/**
 * rules.json, made writable.
 *
 * Until the admin panel existed, rules were a file you edited over SSH and a
 * restart. Three things change once a web form can write them:
 *
 *   1. WHERE. The file has to move out of the deployed tree. systemd runs this
 *      service with ProtectSystem=strict and ReadWritePaths=/var/lib/ig-automation,
 *      so a write to /opt/ig-automation/rules.json fails outright — and even if
 *      it did not, the rsync in DEPLOY.md would overwrite the live campaign with
 *      whatever is in git on the next deploy. The repo copy is now a SEED,
 *      copied once into the writable location if nothing is there yet.
 *
 *   2. VALIDATION IS A GATE, NOT A LOG LINE. Booting with a bad rule is
 *      survivable; saving one from a form is how the account answered itself
 *      ninety times on 2026-08-30. save() refuses anything with an `error`
 *      finding and hands the findings back to the caller.
 *
 *   3. HOT RELOAD. Nobody is going to SSH in and `systemctl restart` after
 *      changing a word in a DM. The in-process config is replaced atomically on
 *      save, and server.js reads it through a getter so the webhook handler
 *      picks up the new object on the very next comment.
 *
 * Every write leaves the previous version in backups/, because "I broke the
 * campaign and I do not remember what it said" is a likelier emergency than
 * disk pressure.
 */

const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");

const rulesLib = require("./rules");

const SEED_FILE = path.join(__dirname, "..", "rules.json");
const KEEP_BACKUPS = Number(process.env.IG_RULES_BACKUPS || 20);

let cache = null; // { config, etag, mtimeMs }

const file = () => process.env.IG_RULES_FILE || SEED_FILE;
const backupDir = () => path.join(path.dirname(file()), "rules-backups");

/** A cheap version stamp, so two open browser tabs cannot silently overwrite each other. */
const etagFor = (config) => crypto.createHash("sha256").update(JSON.stringify(config)).digest("hex").slice(0, 16);

/**
 * Copy the repo's rules.json into the writable location, once.
 *
 * Only ever creates. A seed that overwrote would turn every deploy into a
 * silent rollback of the live campaign — the exact failure the move to
 * /var/lib is meant to prevent.
 */
function seed() {
  const target = file();
  if (fs.existsSync(target)) return { seeded: false, file: target };
  if (path.resolve(target) === path.resolve(SEED_FILE)) return { seeded: false, file: target };

  fs.mkdirSync(path.dirname(target), { recursive: true });
  const source = fs.existsSync(SEED_FILE) ? fs.readFileSync(SEED_FILE, "utf8") : JSON.stringify({ rules: [] }, null, 2) + "\n";
  fs.writeFileSync(target, source, { mode: 0o640 });
  console.log(`rules seeded into ${target}`);
  return { seeded: true, file: target };
}

/**
 * The config as it is on disk right now.
 *
 * Re-stats on every call and re-parses only when the mtime moved, the same
 * trick tokens.js uses — so a rules file edited by hand over SSH is picked up
 * without a restart too, not only one written through the panel.
 */
function current() {
  const p = file();
  let stat;
  try {
    stat = fs.statSync(p);
  } catch {
    if (cache) return cache.config;
    return { rules: [] };
  }
  if (cache && cache.mtimeMs === stat.mtimeMs) return cache.config;

  try {
    const config = JSON.parse(fs.readFileSync(p, "utf8"));
    if (!config || !Array.isArray(config.rules)) throw new Error("no rules array");
    cache = { config, etag: etagFor(config), mtimeMs: stat.mtimeMs };
    return config;
  } catch (err) {
    // A corrupt file must not take the automation off the air. Keep serving the
    // last good config and say so loudly — this is the one state where what is
    // running and what is on disk genuinely disagree.
    console.error("RULES FILE UNREADABLE, keeping the last good copy in memory:", p, err && err.message);
    return cache ? cache.config : { rules: [] };
  }
}

function etag() {
  current();
  return cache ? cache.etag : etagFor({ rules: [] });
}

/** Newest first. Used by the panel's restore list. */
function backups() {
  const dir = backupDir();
  let names;
  try {
    names = fs.readdirSync(dir);
  } catch {
    return [];
  }
  return names
    .filter((n) => n.startsWith("rules-") && n.endsWith(".json"))
    .sort()
    .reverse()
    .map((name) => {
      const full = path.join(dir, name);
      let size = 0;
      let at = null;
      try {
        const st = fs.statSync(full);
        size = st.size;
        at = new Date(st.mtimeMs).toISOString();
      } catch {
        /* raced with a prune */
      }
      return { name, size, at };
    });
}

function keepBackup(previousText) {
  if (!previousText) return;
  const dir = backupDir();
  fs.mkdirSync(dir, { recursive: true });
  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  fs.writeFileSync(path.join(dir, `rules-${stamp}.json`), previousText, { mode: 0o640 });

  for (const stale of backups().slice(KEEP_BACKUPS)) {
    try {
      fs.unlinkSync(path.join(dir, stale.name));
    } catch {
      /* best effort */
    }
  }
}

function readBackup(name) {
  // Path traversal on a filename that arrives from a browser. The name is
  // rebuilt from a basename rather than trusted, and then still has to match
  // the pattern the writer uses.
  const safe = path.basename(String(name || ""));
  if (!/^rules-[0-9TZ.:-]+\.json$/.test(safe)) return null;
  try {
    return JSON.parse(fs.readFileSync(path.join(backupDir(), safe), "utf8"));
  } catch {
    return null;
  }
}

class RulesRejected extends Error {
  constructor(problems) {
    super("rules rejected: " + problems.map((p) => p.message).join("; "));
    this.name = "RulesRejected";
    this.problems = problems;
  }
}

class RulesConflict extends Error {
  constructor(expected, actual) {
    super("the rules changed in another tab since this page was loaded");
    this.name = "RulesConflict";
    this.expected = expected;
    this.actual = actual;
  }
}

const slug = (s) =>
  String(s || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 40);

/**
 * Normalise whatever the form sent into the shape the matcher expects.
 *
 * The panel is not the only possible caller and a hand-written PUT is a fair
 * thing to do, so nothing here assumes well-formed input: unknown keys are
 * dropped, types are coerced, and an id is derived from the name if one is
 * missing. Dropping unknown keys is on purpose — it stops a stale browser tab
 * from resurrecting a field that was removed from the schema.
 */
function normaliseConfig(input) {
  const raw = (input && Array.isArray(input.rules) ? input.rules : []).filter(Boolean);
  const seen = new Set();

  const rules = raw.map((r, i) => {
    const name = String(r.name || "").trim();
    let id = String(r.id || "").trim() || slug(name) || `rule-${i + 1}`;
    while (seen.has(id)) id = `${id}-2`;
    seen.add(id);

    const ids = Array.isArray(r.media && r.media.ids) ? r.media.ids.map((x) => String(x).trim()).filter(Boolean) : [];
    const mode = r.media && r.media.mode === "only" ? "only" : "all";

    const out = {
      id,
      name: name || id,
      enabled: r.enabled !== false,
      keywords: [...new Set((Array.isArray(r.keywords) ? r.keywords : []).map((k) => String(k).trim()).filter(Boolean))],
      match: ["word", "contains", "exact"].includes(r.match) ? r.match : "word",
      media: { mode, ids: [...new Set(ids)] },
      dm: {
        text: String((r.dm && r.dm.text) || "").trim(),
        link: String((r.dm && r.dm.link) || "").trim(),
        fileId: String((r.dm && r.dm.fileId) || "").trim(),
      },
      publicReply: String(r.publicReply || "").trim(),
      askEmail: Boolean(r.askEmail),
      tag: String(r.tag || "").trim() || id,
    };
    if (!out.dm.fileId) delete out.dm.fileId;
    return out;
  });

  return { version: 2, rules, updatedAt: new Date().toISOString() };
}

/**
 * Validate, back up, write atomically, publish in-process.
 *
 * @param {object} input     the config as the panel posted it
 * @param {{ifMatch?: string, actor?: string}} [opts]
 *   ifMatch — the etag the browser loaded. Mismatch means someone else saved in
 *   between, and the write is refused rather than silently winning.
 * @returns {{config: object, etag: string, problems: Array}}
 * @throws {RulesRejected|RulesConflict}
 */
function save(input, opts = {}) {
  const config = normaliseConfig(input);
  const problems = rulesLib.inspect(config);
  const blocking = problems.filter((p) => p.severity === "error");
  if (blocking.length) throw new RulesRejected(blocking);

  const p = file();
  const live = etag();
  if (opts.ifMatch && opts.ifMatch !== live) throw new RulesConflict(opts.ifMatch, live);

  let previous = null;
  try {
    previous = fs.readFileSync(p, "utf8");
  } catch {
    /* first write */
  }

  fs.mkdirSync(path.dirname(p), { recursive: true });
  const text = JSON.stringify(config, null, 2) + "\n";
  // Same atomic dance as tokens.js: a half-written rules file read by the
  // webhook mid-save would drop every rule on the floor.
  const tmp = `${p}.${process.pid}.tmp`;
  fs.writeFileSync(tmp, text, { mode: 0o640 });
  fs.renameSync(tmp, p);

  keepBackup(previous);
  cache = null; // force a re-stat; current() republishes to the running handler

  console.log(
    JSON.stringify({
      event: "rules_saved",
      by: opts.actor || "admin",
      rules: config.rules.length,
      enabled: config.rules.filter((r) => r.enabled).length,
      warnings: problems.length,
    })
  );

  const saved = current();
  return { config: saved, etag: etag(), problems };
}

module.exports = {
  file,
  seed,
  current,
  etag,
  save,
  normaliseConfig,
  backups,
  readBackup,
  RulesRejected,
  RulesConflict,
  SEED_FILE,
  _reset: () => {
    cache = null;
  },
};
