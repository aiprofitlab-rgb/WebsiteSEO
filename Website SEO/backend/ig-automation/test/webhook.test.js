/**
 * The transport: the handshake, the signature gate, and the ack-before-work
 * contract Meta actually enforces.
 */
const test = require("node:test");
const assert = require("node:assert");
const express = require("express");

const webhook = require("../webhook");
const signature = require("../lib/signature");

const SECRET = "test-app-secret";
const VERIFY = "test-verify-token";

/** A real listening server, so response timing means something. */
async function serve(deps) {
  process.env.META_APP_SECRET = SECRET;
  process.env.IG_VERIFY_TOKEN = VERIFY;

  const app = express();
  app.use(express.json({ verify: (req, _res, buf) => { req.rawBody = buf; } }));
  app.use("/ig", webhook.create(deps));

  const server = await new Promise((resolve) => {
    const s = app.listen(0, () => resolve(s));
  });
  const base = `http://127.0.0.1:${server.address().port}/ig`;
  return { base, close: () => new Promise((r) => server.close(r)) };
}

const body = () => Buffer.from(JSON.stringify({ object: "instagram", entry: [{ id: "1", changes: [] }] }), "utf8");
const post = (base, buf, header) =>
  fetch(base, {
    method: "POST",
    headers: { "content-type": "application/json", ...(header ? { "x-hub-signature-256": header } : {}) },
    body: buf,
  });

test("the GET handshake echoes the challenge for the right token", async () => {
  const s = await serve({ handleEvent: async () => [] });
  const res = await fetch(`${s.base}?hub.mode=subscribe&hub.verify_token=${VERIFY}&hub.challenge=CHALLENGE_123`);
  assert.equal(res.status, 200);
  assert.equal(await res.text(), "CHALLENGE_123");
  await s.close();
});

test("the handshake refuses a wrong token, and a malformed one", async () => {
  const s = await serve({ handleEvent: async () => [] });
  assert.equal((await fetch(`${s.base}?hub.mode=subscribe&hub.verify_token=wrong&hub.challenge=X`)).status, 403);
  assert.equal((await fetch(`${s.base}?hub.mode=unsubscribe&hub.verify_token=${VERIFY}&hub.challenge=X`)).status, 403);
  assert.equal((await fetch(`${s.base}?hub.challenge=X`)).status, 400);
  await s.close();
});

test("an unsigned POST is refused and never reaches the handler", async () => {
  let called = false;
  const s = await serve({ handleEvent: async () => ((called = true), []) });

  const res = await post(s.base, body(), undefined);
  assert.equal(res.status, 403);
  await new Promise((r) => setTimeout(r, 50));
  assert.equal(called, false, "a forged event must not be processed");
  await s.close();
});

test("a POST signed with the wrong secret is refused", async () => {
  let called = false;
  const s = await serve({ handleEvent: async () => ((called = true), []) });

  const buf = body();
  const res = await post(s.base, buf, signature.sign(buf, "not-the-secret"));
  assert.equal(res.status, 403);
  await new Promise((r) => setTimeout(r, 50));
  assert.equal(called, false);
  await s.close();
});

test("a body altered after signing is refused", async () => {
  const s = await serve({ handleEvent: async () => [] });
  const header = signature.sign(body(), SECRET);
  const altered = Buffer.from(JSON.stringify({ object: "instagram", entry: [{ id: "999", changes: [] }] }), "utf8");
  assert.equal((await post(s.base, altered, header)).status, 403);
  await s.close();
});

test("a correctly signed POST is accepted and processed", async () => {
  let seen = null;
  const s = await serve({ handleEvent: async (b) => ((seen = b), [{ action: "sent", ruleId: "storefront" }]) });

  const buf = body();
  const res = await post(s.base, buf, signature.sign(buf, SECRET));
  assert.equal(res.status, 200);

  await new Promise((r) => setTimeout(r, 50));
  assert.equal(seen.object, "instagram");
  await s.close();
});

test("the 200 comes back before the work is done, not after", async () => {
  // Meta budgets a couple of seconds and disables callbacks that keep missing
  // it. Sending a DM, posting a reply and writing a row cannot fit, so the ack
  // must not wait for them. This handler takes 700ms; the response must not.
  let finished = false;
  const s = await serve({
    handleEvent: async () => {
      await new Promise((r) => setTimeout(r, 700));
      finished = true;
      return [];
    },
  });

  const buf = body();
  const started = Date.now();
  const res = await post(s.base, buf, signature.sign(buf, SECRET));
  const elapsed = Date.now() - started;

  assert.equal(res.status, 200);
  assert.ok(elapsed < 300, `acked in ${elapsed}ms — must not wait for the handler`);
  assert.equal(finished, false, "the work is still running after the ack");

  await new Promise((r) => setTimeout(r, 900));
  assert.equal(finished, true, "and it does still finish");
  await s.close();
});

test("a handler that throws after the ack does not take the process down", async () => {
  const s = await serve({ handleEvent: async () => { throw new Error("downstream exploded"); } });

  const buf = body();
  assert.equal((await post(s.base, buf, signature.sign(buf, SECRET))).status, 200);
  await new Promise((r) => setTimeout(r, 100));

  // Still serving: the rejection was caught rather than becoming fatal.
  const again = body();
  assert.equal((await post(s.base, again, signature.sign(again, SECRET))).status, 200);
  await s.close();
});

test("with no app secret configured, every POST is refused rather than trusted", async () => {
  const s = await serve({ handleEvent: async () => [] });
  const saved = process.env.META_APP_SECRET;
  delete process.env.META_APP_SECRET;

  const buf = body();
  assert.equal((await post(s.base, buf, signature.sign(buf, saved))).status, 403);

  process.env.META_APP_SECRET = saved;
  await s.close();
});

test("with no verify token configured, the handshake fails loudly instead of using a guessable default", async () => {
  const s = await serve({ handleEvent: async () => [] });
  const saved = process.env.IG_VERIFY_TOKEN;
  delete process.env.IG_VERIFY_TOKEN;

  const res = await fetch(`${s.base}?hub.mode=subscribe&hub.verify_token=YOUR_VERIFY_TOKEN&hub.challenge=X`);
  assert.equal(res.status, 500);

  process.env.IG_VERIFY_TOKEN = saved;
  await s.close();
});
