/**
 * The panel end to end: the real server.js app, a real rules file, a real
 * upload directory.
 *
 * Everything here is a property the panel is only useful if it has — you can
 * sign in, a rule you save is the rule the webhook will use on the next
 * comment, and a rule you cannot save is one that would have broken something.
 */
const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const PASSWORD = "a-properly-long-password";

// Every path and secret has to be in place BEFORE server.js is required: it
// opens the database, seeds the rules file and decides whether to mount the
// panel at all, all at require time.
const workspace = fs.mkdtempSync(path.join(os.tmpdir(), "ig-admin-"));
process.env.IG_RULES_FILE = path.join(workspace, "rules.json");
process.env.IG_DB_FILE = path.join(workspace, "state.sqlite");
process.env.IG_UPLOAD_DIR = path.join(workspace, "uploads");
process.env.IG_PUBLIC_BASE = "https://hooks.aiprofitlab.io";
process.env.META_APP_SECRET = "test-app-secret";
process.env.IG_ADMIN_PASSWORD_HASH = require("../lib/auth").hash(PASSWORD);
process.env.IG_ADMIN_INSECURE_COOKIES = "1";

const { app } = require("../server");
const rulesStore = require("../lib/rulesStore");

let base;
let server;
let cookie = "";

test.before(async () => {
  server = await new Promise((resolve) => {
    const s = app.listen(0, () => resolve(s));
  });
  base = `http://127.0.0.1:${server.address().port}`;
});
test.after(() => server && server.close());

const call = (path, options = {}) =>
  fetch(`${base}${path}`, {
    ...options,
    headers: { ...(cookie ? { cookie } : {}), ...(options.headers || {}) },
    redirect: "manual",
  });

const send = (path, method, body) =>
  call(path, { method, headers: { "content-type": "application/json" }, body: JSON.stringify(body) });

const RULE = {
  id: "storefront",
  name: "Smart Storefront",
  enabled: true,
  keywords: ["storefront"],
  match: "word",
  media: { mode: "all", ids: [] },
  dm: { text: "Here it is", link: "https://aiprofitlab.io/en/smart-storefront/" },
  publicReply: "Sent! Check your DMs 📩",
};

test("every API route is closed until you sign in", async () => {
  for (const [method, route] of [
    ["GET", "/admin/api/state"],
    ["GET", "/admin/api/media"],
    ["GET", "/admin/api/activity"],
    ["PUT", "/admin/api/rules"],
    ["POST", "/admin/api/files"],
  ]) {
    const res = await call(route, { method });
    assert.equal(res.status, 401, `${method} ${route}`);
  }
});

test("the wrong password is refused and the right one issues a session", async () => {
  const bad = await send("/admin/api/login", "POST", { password: "not it" });
  assert.equal(bad.status, 401);
  assert.equal(bad.headers.get("set-cookie"), null, "no cookie on a failed login");

  const ok = await send("/admin/api/login", "POST", { password: PASSWORD });
  assert.equal(ok.status, 200);

  const setCookie = ok.headers.get("set-cookie");
  assert.match(setCookie, /HttpOnly/);
  assert.match(setCookie, /SameSite=Strict/);
  cookie = setCookie.split(";")[0];

  const state = await call("/admin/api/state");
  assert.equal(state.status, 200);
});

test("the state payload reports that the secrets exist without ever containing one", async () => {
  const body = await (await call("/admin/api/state")).json();
  assert.equal(body.account.appSecret, true);
  const text = JSON.stringify(body);
  assert.equal(text.includes(process.env.META_APP_SECRET), false);
  assert.equal(text.includes(process.env.IG_ADMIN_PASSWORD_HASH), false);
  assert.equal(text.includes(PASSWORD), false);
});

test("a saved rule is what the webhook handler reads on the very next comment — no restart", async () => {
  const state = await (await call("/admin/api/state")).json();
  const res = await send("/admin/api/rules", "PUT", {
    rules: [{ ...RULE, dm: { text: "Fresh copy", link: "https://aiprofitlab.io/en/smart-storefront/" } }],
    etag: state.etag,
  });
  assert.equal(res.status, 200);

  // Not the response — the live config object the running service hands the
  // handler. This is the whole point of the hot reload.
  assert.equal(rulesStore.current().rules[0].dm.text, "Fresh copy");
  assert.equal(require("../server").deps.rules.rules[0].dm.text, "Fresh copy");
});

test("a reply loop is refused with a 422 that names the rule and the keyword", async () => {
  const before = rulesStore.current();
  const res = await send("/admin/api/rules", "PUT", {
    rules: [{ ...RULE, publicReply: "Your storefront link is on its way" }],
  });
  assert.equal(res.status, 422);

  const body = await res.json();
  assert.equal(body.problems[0].severity, "error");
  assert.match(body.problems[0].message, /reply loop/);
  assert.deepEqual(rulesStore.current(), before, "nothing was written");
});

test("a save from a stale tab is refused rather than allowed to overwrite", async () => {
  const res = await send("/admin/api/rules", "PUT", { rules: [RULE], etag: "0000000000000000" });
  assert.equal(res.status, 409);
  assert.ok((await res.json()).etag, "the current etag comes back so the page can recover");
});

test("post targeting decides which rule fires, and the dry run proves it before you save", async () => {
  await send("/admin/api/rules", "PUT", {
    rules: [
      { ...RULE, id: "reel-only", name: "Reel only", media: { mode: "only", ids: ["17900000000000001"] }, dm: { text: "Reel answer" }, publicReply: "On its way 📩" },
      { ...RULE, id: "everywhere", name: "Everywhere", dm: { text: "Default answer" }, publicReply: "Sent! Check your DMs 📩" },
    ],
  });

  const ask = async (mediaId) =>
    (await send("/admin/api/rules/preview", "POST", { text: "storefront please", mediaId })).json();

  assert.equal((await ask("17900000000000001")).ruleId, "reel-only", "the targeted rule wins on its own post");
  assert.equal((await ask("17900000000000009")).ruleId, "everywhere", "and is invisible everywhere else");
  assert.equal((await ask("")).ruleId, "everywhere");

  const own = await (await send("/admin/api/rules/preview", "POST", { text: "Sent! Check your DMs 📩" })).json();
  assert.equal(own.outcome, "dropped", "our own public reply is recognised, not answered");
});

test("the dry run answers for unsaved edits, so the button means what it says", async () => {
  const draft = [{ ...RULE, id: "draft", keywords: ["unsaved"], dm: { text: "Only in the browser" }, publicReply: "" }];
  const body = await (await send("/admin/api/rules/preview", "POST", { text: "unsaved", rules: draft })).json();
  assert.equal(body.dm, "Only in the browser");
  assert.equal(rulesStore.current().rules.some((r) => r.id === "draft"), false, "and it is still only in the browser");
});

test("an uploaded file gets a link, the link serves the bytes, and the DM carries it", async () => {
  const pdf = Buffer.from("%PDF-1.4 the guide");
  const upload = await call("/admin/api/files", {
    method: "POST",
    headers: { "content-type": "application/pdf", "x-filename": "Storefront Guide.pdf" },
    body: pdf,
  });
  assert.equal(upload.status, 201);
  const { file } = await upload.json();
  assert.equal(file.name, "Storefront-Guide.pdf");

  // The public download. No cookie — this is the URL a follower opens.
  const download = await fetch(`${base}/f/${file.id}/${file.name}`);
  assert.equal(download.status, 200);
  assert.equal(download.headers.get("content-type"), "application/pdf");
  assert.equal(download.headers.get("x-content-type-options"), "nosniff");
  assert.equal(Buffer.from(await download.arrayBuffer()).toString(), pdf.toString());

  await send("/admin/api/rules", "PUT", {
    rules: [{ ...RULE, dm: { text: "Here is the guide", link: "", fileId: file.id } }],
  });
  const preview = await (await send("/admin/api/rules/preview", "POST", { text: "storefront" })).json();
  assert.equal(preview.dm, `Here is the guide\n\n${file.url}`);
});

test("a file still attached to a rule is not deleted by accident", async () => {
  const fileId = rulesStore.current().rules[0].dm.fileId;
  const refused = await call(`/admin/api/files/${fileId}`, { method: "DELETE" });
  assert.equal(refused.status, 409);
  assert.deepEqual((await refused.json()).inUse, ["storefront"]);

  const forced = await call(`/admin/api/files/${fileId}?force=1`, { method: "DELETE" });
  assert.equal(forced.status, 200);
});

test("an unreadable file type is refused at the door", async () => {
  const res = await call("/admin/api/files", {
    method: "POST",
    headers: { "content-type": "text/html", "x-filename": "payload.html" },
    body: Buffer.from("<script>alert(1)</script>"),
  });
  assert.equal(res.status, 400);
  assert.match((await res.json()).message, /not allowed/);
});

test("a cross-origin write is refused even with a valid cookie", async () => {
  const res = await call("/admin/api/rules", {
    method: "PUT",
    headers: { "content-type": "application/json", origin: "https://evil.test" },
    body: JSON.stringify({ rules: [RULE] }),
  });
  assert.equal(res.status, 403);
});

test("signing out invalidates the cookie that was just used", async () => {
  assert.equal((await call("/admin/api/logout", { method: "POST" })).status, 200);
  cookie = "ig_admin=nonsense";
  assert.equal((await call("/admin/api/state")).status, 401);
});
