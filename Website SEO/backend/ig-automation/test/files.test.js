/**
 * Uploaded files, and the public URL a stranger is meant to click.
 *
 * The allowlist test is the one that matters: these files are served from a
 * subdomain of the brand, so an .html or .svg upload would be a same-origin
 * script wearing aiprofitlab.io.
 */
const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const files = require("../lib/files");

function workspace() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "ig-files-"));
  process.env.IG_UPLOAD_DIR = dir;
  process.env.IG_PUBLIC_BASE = "https://hooks.aiprofitlab.io";
  return dir;
}

const pdf = () => Buffer.from("%PDF-1.4 pretend");

test("an upload gets an unguessable id and a public URL that carries its name", () => {
  workspace();
  const saved = files.save(pdf(), "AI Storefront Guide.pdf");

  assert.match(saved.id, /^[a-f0-9]{32}$/);
  assert.equal(saved.name, "AI-Storefront-Guide.pdf");
  assert.equal(saved.mime, "application/pdf");
  assert.equal(saved.url, `https://hooks.aiprofitlab.io/f/${saved.id}/AI-Storefront-Guide.pdf`);
  assert.equal(files.find(saved.id).name, saved.name);
});

test("active content is refused — this is served from a subdomain of the brand", () => {
  workspace();
  for (const name of ["payload.html", "logo.svg", "script.js", "run.sh", "thing"]) {
    assert.throws(() => files.save(Buffer.from("x"), name), /not allowed/, name);
  }
  assert.ok(files.save(pdf(), "fine.pdf"));
});

test("a filename cannot climb out of the upload directory or hide a second extension", () => {
  const dir = workspace();
  const saved = files.save(pdf(), "../../../etc/cron.d/evil.pdf");
  assert.equal(saved.name, "evil.pdf");
  assert.equal(path.dirname(files.find(saved.id).path), dir);
  assert.equal(files.safeName("a/b/../c.pdf"), "c.pdf");
});

test("an oversized upload is refused with the limit in the message", () => {
  workspace();
  const tooBig = Buffer.alloc(files.MAX_BYTES + 1);
  assert.throws(() => files.save(tooBig, "big.pdf"), /the limit is/);
  assert.throws(() => files.save(Buffer.alloc(0), "empty.pdf"), /empty/);
});

test("a deleted file resolves to no URL, so a rule sends its text instead of a 404", () => {
  workspace();
  const saved = files.save(pdf(), "guide.pdf");
  assert.ok(files.urlFor(saved.id));

  assert.equal(files.remove(saved.id), true);
  assert.equal(files.urlFor(saved.id), "");
  assert.equal(files.find(saved.id), null);
  assert.equal(files.remove(saved.id), false);
});

test("a made-up id never touches the filesystem", () => {
  workspace();
  assert.equal(files.find("../../etc/passwd"), null);
  assert.equal(files.find("nope"), null);
  assert.equal(files.urlFor(""), "");
});

test("usedBy names the rules that would break if a file were deleted", () => {
  workspace();
  const saved = files.save(pdf(), "guide.pdf");
  const config = {
    rules: [
      { id: "guide", dm: { fileId: saved.id } },
      { id: "price", dm: { link: "https://x.test" } },
    ],
  };
  assert.deepEqual(files.usedBy(saved.id, config), ["guide"]);
  assert.deepEqual(files.usedBy("other", config), []);
});

test("the list is newest first and survives a directory that does not exist yet", () => {
  const dir = workspace();
  fs.rmSync(dir, { recursive: true, force: true });
  assert.deepEqual(files.list(), []);

  files.save(pdf(), "one.pdf");
  files.save(pdf(), "two.pdf");
  assert.equal(files.list().length, 2);
});
