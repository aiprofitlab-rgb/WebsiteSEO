/**
 * The writable half of rules.json.
 *
 * The gate is the point of this file. Everything else — seeding, backups,
 * etags — is bookkeeping around one guarantee: a config that would make the
 * account answer itself cannot be written through the panel.
 */
const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const rulesStore = require("../lib/rulesStore");

function workspace() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "ig-rules-"));
  process.env.IG_RULES_FILE = path.join(dir, "rules.json");
  rulesStore._reset();
  return dir;
}

const rule = (over = {}) => ({
  id: "storefront",
  name: "Storefront",
  keywords: ["storefront"],
  dm: { text: "Here it is", link: "https://aiprofitlab.io/en/smart-storefront/" },
  publicReply: "Sent! Check your DMs 📩",
  ...over,
});

test("seed copies the repo's rules.json in, once, and never overwrites after that", () => {
  const dir = workspace();
  const first = rulesStore.seed();
  assert.equal(first.seeded, true);
  assert.ok(fs.existsSync(path.join(dir, "rules.json")));

  rulesStore.save({ rules: [rule()] });
  const second = rulesStore.seed();
  assert.equal(second.seeded, false, "a second boot must not roll the live campaign back to the repo copy");
  assert.equal(rulesStore.current().rules.length, 1);
});

test("a publicReply that trips its own keyword is refused, not saved with a warning", () => {
  workspace();
  rulesStore.seed();
  const before = JSON.stringify(rulesStore.current());

  assert.throws(
    () => rulesStore.save({ rules: [rule({ publicReply: "Demos sent — comment storefront for more" })] }),
    (err) => {
      assert.equal(err.name, "RulesRejected");
      assert.match(err.problems[0].message, /reply loop/);
      return true;
    }
  );
  assert.equal(JSON.stringify(rulesStore.current()), before, "the file on disk is untouched by a refused save");
});

test("a rule scoped to specific posts with none chosen is refused — it could never fire", () => {
  workspace();
  assert.throws(
    () => rulesStore.save({ rules: [rule({ media: { mode: "only", ids: [] } })] }),
    /no posts are selected/
  );
});

test("a saved rule is normalised: unknown keys dropped, ids derived, duplicates de-duplicated", () => {
  workspace();
  const { config } = rulesStore.save({
    rules: [
      { name: "Pricing questions", keywords: [" price ", "price", "cost"], dm: { text: "hi" }, sneaky: "dropped" },
      { name: "Pricing questions", keywords: ["quote"], dm: { link: "https://x.test" } },
    ],
  });

  assert.equal(config.rules[0].id, "pricing-questions");
  assert.equal(config.rules[1].id, "pricing-questions-2", "a clashing derived id is made unique rather than silently merged");
  assert.deepEqual(config.rules[0].keywords, ["price", "cost"]);
  assert.equal(config.rules[0].sneaky, undefined);
  assert.deepEqual(config.rules[0].media, { mode: "all", ids: [] });
});

test("every save leaves the previous version behind, and it can be restored", () => {
  workspace();
  rulesStore.save({ rules: [rule({ dm: { text: "version one" } })] });
  rulesStore.save({ rules: [rule({ dm: { text: "version two" } })] });

  const list = rulesStore.backups();
  assert.ok(list.length >= 1, "the first version was kept");
  const old = rulesStore.readBackup(list[list.length - 1].name);
  assert.equal(old.rules[0].dm.text, "version one");
});

test("a backup name from a browser cannot walk out of the backup directory", () => {
  workspace();
  rulesStore.save({ rules: [rule()] });
  assert.equal(rulesStore.readBackup("../../../etc/passwd"), null);
  assert.equal(rulesStore.readBackup("rules-x.json/../../token.json"), null);
});

test("a stale tab loses the race instead of silently overwriting the other tab's save", () => {
  workspace();
  const first = rulesStore.save({ rules: [rule()] });
  rulesStore.save({ rules: [rule({ dm: { text: "someone else got here first" } })] });

  assert.throws(
    () => rulesStore.save({ rules: [rule({ dm: { text: "stale" } })] }, { ifMatch: first.etag }),
    (err) => err.name === "RulesConflict"
  );
});

test("current() re-reads a file changed underneath it — the panel and a hand edit both go live without a restart", () => {
  const dir = workspace();
  rulesStore.save({ rules: [rule()] });
  assert.equal(rulesStore.current().rules[0].dm.text, "Here it is");

  const p = path.join(dir, "rules.json");
  const edited = JSON.parse(fs.readFileSync(p, "utf8"));
  edited.rules[0].dm.text = "edited over ssh";
  // mtime resolution is coarse enough that a same-millisecond write can look
  // unchanged; the future stamp is what a real edit seconds later would have.
  fs.writeFileSync(p, JSON.stringify(edited));
  fs.utimesSync(p, new Date(Date.now() + 2000), new Date(Date.now() + 2000));

  assert.equal(rulesStore.current().rules[0].dm.text, "edited over ssh");
});

test("a corrupt rules file keeps the last good config serving instead of taking the automation off the air", () => {
  const dir = workspace();
  rulesStore.save({ rules: [rule()] });
  const p = path.join(dir, "rules.json");
  fs.writeFileSync(p, "{ this is not json");
  fs.utimesSync(p, new Date(Date.now() + 2000), new Date(Date.now() + 2000));

  assert.equal(rulesStore.current().rules[0].id, "storefront");
});
