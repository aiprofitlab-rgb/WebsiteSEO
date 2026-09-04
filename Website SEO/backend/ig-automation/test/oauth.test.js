/**
 * Instagram Business Login.
 *
 * The properties worth holding: the consent screen asks for exactly the three
 * permissions the submission asks for, the short-lived token is always upgraded
 * before it is shown as a success, a cancelled sign-in is not an error page with
 * a 500 on it, and — the one that matters most — completing the flow NEVER
 * writes a token, because a Meta reviewer will complete it with their own
 * account while the service is live.
 */
const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const express = require("express");

const SECRET = "test-app-secret";

const workspace = fs.mkdtempSync(path.join(os.tmpdir(), "ig-oauth-"));
const TOKEN_FILE = path.join(workspace, "token.json");

process.env.META_APP_SECRET = SECRET;
process.env.IG_APP_ID = "1122334455";
process.env.IG_PUBLIC_BASE = "https://hooks.aiprofitlab.io";
process.env.IG_TOKEN_FILE = TOKEN_FILE;
delete process.env.IG_OAUTH_REDIRECT_URI;
delete process.env.IG_APP_SECRET;

const oauth = require("../lib/oauth");
const oauthPage = require("../lib/oauthPage");
const webhook = require("../webhook");

const REDIRECT = "https://hooks.aiprofitlab.io/ig/oauth/callback";

/* ---------------------------------------------------------------------------
 * A fake Meta. Every call it does not recognise is a test bug, not a 404.
 * ------------------------------------------------------------------------- */

function meta({ exchange, exchangeStatus = 200, long, longStatus = 200, whoami, whoamiStatus = 200 } = {}) {
  const calls = [];
  const reply = (body, status) =>
    Promise.resolve({ ok: status < 400, status, json: async () => body });

  const fetchImpl = async (url, options = {}) => {
    const u = String(url);
    calls.push({ url: u, method: options.method || "GET", body: options.body ? String(options.body) : null });

    if (u.startsWith("https://api.instagram.com/oauth/access_token")) {
      return reply(exchange !== undefined ? exchange : { data: [{ access_token: "SHORT", user_id: 178414, permissions: oauth.SCOPES.join(",") }] }, exchangeStatus);
    }
    if (u.includes("/access_token") && u.includes("ig_exchange_token")) {
      return reply(long !== undefined ? long : { access_token: "LONG-LIVED", token_type: "bearer", expires_in: 5183944 }, longStatus);
    }
    if (u.includes("/me?") || /\/me\b/.test(u)) {
      return reply(whoami !== undefined ? whoami : { id: "178414", username: "aiprofitlab" }, whoamiStatus);
    }
    throw new Error(`unexpected call: ${u}`);
  };

  return { fetchImpl, calls };
}

/* ---------------------------------------------------------------------------
 * The authorize URL
 * ------------------------------------------------------------------------- */

test("the consent screen asks for exactly the three reviewed permissions, comma-separated", () => {
  const u = new URL(oauth.authorizeUrl());
  assert.equal(u.origin + u.pathname, "https://www.instagram.com/oauth/authorize");
  assert.equal(u.searchParams.get("client_id"), "1122334455");
  assert.equal(u.searchParams.get("response_type"), "code");
  assert.equal(u.searchParams.get("redirect_uri"), REDIRECT);

  // Comma-separated. A space-separated list is read as one unknown scope and
  // the consent screen silently asks for nothing.
  const scope = u.searchParams.get("scope");
  assert.equal(scope, "instagram_business_basic,instagram_business_manage_comments,instagram_business_manage_messages");
  assert.ok(!scope.includes(" "));
});

test("the redirect URI follows IG_PUBLIC_BASE and can be overridden outright", () => {
  assert.equal(oauth.redirectUri(), REDIRECT);

  process.env.IG_PUBLIC_BASE = "https://hooks.aiprofitlab.io/"; // stray slash
  assert.equal(oauth.redirectUri(), REDIRECT, "a trailing slash must not become a double slash");

  process.env.IG_OAUTH_REDIRECT_URI = "https://elsewhere.example/cb";
  assert.equal(oauth.redirectUri(), "https://elsewhere.example/cb");

  delete process.env.IG_OAUTH_REDIRECT_URI;
  process.env.IG_PUBLIC_BASE = "https://hooks.aiprofitlab.io";
});

test("state round-trips, and a forged or stale one does not", () => {
  const state = oauth.signState();
  assert.ok(oauth.checkState(state));

  assert.ok(!oauth.checkState(""));
  assert.ok(!oauth.checkState("garbage"));
  assert.ok(!oauth.checkState(state.replace(/.$/, "x")), "a tampered signature must fail");

  const old = oauth.signState(Date.now() - 2 * 3600_000);
  assert.ok(!oauth.checkState(old), "an hour-old state is stale");
});

/* ---------------------------------------------------------------------------
 * The exchange
 * ------------------------------------------------------------------------- */

test("the code is exchanged, then upgraded to a long-lived token", async () => {
  const m = meta();
  const result = await oauth.connect("AQBcode", { fetchImpl: m.fetchImpl });

  assert.equal(result.account.username, "aiprofitlab");
  assert.equal(result.account.id, "178414");
  assert.deepEqual(result.permissions, oauth.SCOPES);
  assert.equal(result.expiresInDays, 60);

  const [exchange, upgrade] = m.calls;
  assert.equal(exchange.method, "POST", "the code exchange is a POST, so the code never lands in a log line");
  assert.match(exchange.body, /grant_type=authorization_code/);
  assert.match(exchange.body, /client_secret=test-app-secret/);
  assert.match(exchange.body, /code=AQBcode/);
  assert.match(exchange.body, /redirect_uri=https%3A%2F%2Fhooks\.aiprofitlab\.io%2Fig%2Foauth%2Fcallback/);

  assert.match(upgrade.url, /ig_exchange_token/);
  assert.match(upgrade.url, /access_token=SHORT/, "the SHORT token is what gets upgraded");
});

test("the trailing #_ Instagram appends to the redirect is stripped from the code", async () => {
  const m = meta();
  await oauth.connect("AQBcode#_", { fetchImpl: m.fetchImpl });
  assert.match(m.calls[0].body, /code=AQBcode(&|$)/);
});

test("the older flat token response is read as well as the current wrapped one", async () => {
  const m = meta({ exchange: { access_token: "SHORT", user_id: 178414 } });
  const result = await oauth.connect("AQBcode", { fetchImpl: m.fetchImpl });
  assert.equal(result.account.id, "178414");
  // No `permissions` came back, so the page falls back to what was requested.
  assert.deepEqual(result.permissions, oauth.SCOPES);
});

test("permissions actually granted win over the ones requested", async () => {
  const m = meta({
    exchange: { data: [{ access_token: "SHORT", user_id: 178414, permissions: "instagram_business_basic" }] },
  });
  const result = await oauth.connect("AQBcode", { fetchImpl: m.fetchImpl });
  assert.deepEqual(result.permissions, ["instagram_business_basic"], "an unticked scope has to be visible on the page");
});

test("a rejected exchange surfaces Meta's own wording, not a generic failure", async () => {
  const m = meta({ exchange: { error_message: "Invalid platform app" }, exchangeStatus: 400 });
  await assert.rejects(
    () => oauth.connect("AQBcode", { fetchImpl: m.fetchImpl }),
    (err) => err.name === "OAuthError" && err.step === "exchange" && /Invalid platform app/.test(err.message)
  );
});

test("a failed long-lived upgrade is an error, never a success page with a 1-hour token behind it", async () => {
  const m = meta({ long: { error: { message: "Invalid client secret" } }, longStatus: 400 });
  await assert.rejects(
    () => oauth.connect("AQBcode", { fetchImpl: m.fetchImpl }),
    (err) => err.step === "long-lived" && /Invalid client secret/.test(err.message)
  );
});

test("a failed whoami still yields a success page — the token is the claim, the username is decoration", async () => {
  const m = meta({ whoami: { error: { message: "nope" } }, whoamiStatus: 400 });
  const result = await oauth.connect("AQBcode", { fetchImpl: m.fetchImpl });
  assert.equal(result.account.id, "178414", "the id from the exchange stands in");
  assert.equal(result.account.username, "");
});

test("isConfiguredAccount tells our own account from a reviewer's", async () => {
  process.env.IG_USER_ID = "178414";
  assert.equal((await oauth.connect("c", { fetchImpl: meta().fetchImpl })).isConfiguredAccount, true);

  process.env.IG_USER_ID = "999999";
  assert.equal((await oauth.connect("c", { fetchImpl: meta().fetchImpl })).isConfiguredAccount, false);

  delete process.env.IG_USER_ID;
  assert.equal((await oauth.connect("c", { fetchImpl: meta().fetchImpl })).isConfiguredAccount, false);
});

/* ---------------------------------------------------------------------------
 * The routes
 * ------------------------------------------------------------------------- */

async function serve() {
  const app = express();
  app.use("/ig", webhook.create({ handleEvent: async () => [] }));
  const server = await new Promise((resolve) => {
    const s = app.listen(0, () => resolve(s));
  });
  return { base: `http://127.0.0.1:${server.address().port}/ig`, close: () => new Promise((r) => server.close(r)) };
}

test("/oauth/start redirects to the consent screen", async () => {
  const s = await serve();
  const res = await fetch(`${s.base}/oauth/start`, { redirect: "manual" });
  assert.equal(res.status, 302);
  const to = new URL(res.headers.get("location"));
  assert.equal(to.host, "www.instagram.com");
  assert.ok(oauth.checkState(to.searchParams.get("state")), "start must issue a state the callback will accept");
  await s.close();
});

test("cancelling on the consent screen is a readable page, not a 500", async () => {
  const s = await serve();
  const res = await fetch(`${s.base}/oauth/callback?error=access_denied&error_description=User+denied`);
  assert.equal(res.status, 400);
  const html = await res.text();
  assert.match(html, /Sign-in cancelled/);
  assert.match(html, /User denied/);
  await s.close();
});

test("a callback with no code does not reach Meta", async () => {
  const s = await serve();
  const res = await fetch(`${s.base}/oauth/callback`);
  assert.equal(res.status, 400);
  assert.match(await res.text(), /Missing authorization code/);
  await s.close();
});

test("the routes are not mounted at all without an app id", async () => {
  const saved = process.env.IG_APP_ID;
  delete process.env.IG_APP_ID;

  const app = express();
  app.use("/ig", webhook.create({ handleEvent: async () => [] }));
  app.use((req, res) => res.status(404).json({ message: "Not found." }));
  const server = await new Promise((resolve) => {
    const s = app.listen(0, () => resolve(s));
  });
  const base = `http://127.0.0.1:${server.address().port}/ig`;

  assert.equal((await fetch(`${base}/oauth/start`, { redirect: "manual" })).status, 404);
  assert.equal((await fetch(`${base}/oauth/callback?code=x`)).status, 404);

  await new Promise((r) => server.close(r));
  process.env.IG_APP_ID = saved;
});

/* ---------------------------------------------------------------------------
 * The decision this whole module rests on
 * ------------------------------------------------------------------------- */

test("completing the flow writes NO token file — a reviewer's login cannot replace ours", async () => {
  const before = fs.existsSync(TOKEN_FILE);

  const m = meta({ whoami: { id: "555000", username: "meta_reviewer" } });
  const result = await oauth.connect("AQBcode", { fetchImpl: m.fetchImpl });

  assert.equal(result.account.username, "meta_reviewer");
  assert.equal(fs.existsSync(TOKEN_FILE), before, "the callback must never touch token.json");

  // And the token is not handed back to the caller either, so no route can
  // store it by accident later.
  assert.ok(!JSON.stringify(result).includes("LONG-LIVED"));
});

/* ---------------------------------------------------------------------------
 * The page
 * ------------------------------------------------------------------------- */

test("the success page names the account, lists the permissions, and leaks no token", () => {
  const html = oauthPage.success({
    account: { id: "178414", username: "aiprofitlab" },
    permissions: oauth.SCOPES,
    expiresInDays: 60,
    isConfiguredAccount: true,
  });

  assert.match(html, /Connected as @aiprofitlab/);
  assert.match(html, /60 days/);
  for (const scope of oauth.SCOPES) assert.ok(html.includes(scope), `${scope} must be visible on camera`);
  assert.match(html, /token was not saved/i);
  assert.ok(!/LONG-LIVED|access_token/.test(html));
});

test("a stranger's account gets the 'nothing was stored' wording", () => {
  const html = oauthPage.success({
    account: { id: "555000", username: "meta_reviewer" },
    permissions: oauth.SCOPES,
    expiresInDays: 60,
    isConfiguredAccount: false,
  });
  assert.match(html, /Nothing was stored/);
  assert.match(html, /@meta_reviewer/);
});

test("a username is escaped, not injected", () => {
  const html = oauthPage.success({
    account: { id: "1", username: `<script>alert(1)</script>` },
    permissions: [],
    expiresInDays: null,
    isConfiguredAccount: false,
  });
  assert.ok(!html.includes("<script>alert"));
  assert.match(html, /&lt;script&gt;/);
});
