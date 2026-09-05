/**
 * ai.json, hot-reloaded.
 *
 * The same shape as lib/rulesStore.js — seed once into a writable location,
 * re-stat on read, re-parse only when the mtime moved — but deliberately its
 * own file rather than a key inside rules.json. The admin panel rebuilds the
 * whole rules object from its form on every save, so any key it does not know
 * about is dropped: an `ai` block in there would survive exactly until the next
 * keyword edit. See the _comment at the top of ai.json.
 *
 * There is no save() here on purpose. Nothing writes this file but a person, so
 * it needs no etag, no backups and no validation gate — a broken edit falls back
 * to the last good parse and says so in the log, which is the right failure for
 * a fallback feature: the keyword rules keep working regardless.
 */

const fs = require("node:fs");
const path = require("node:path");

const SEED_FILE = path.join(__dirname, "..", "ai.json");

/**
 * What the service assumes when the file is missing, unreadable or half-filled.
 * `enabled: false` is the important one: an install that has not been configured
 * for AI behaves exactly like the install before this feature existed.
 */
const DEFAULTS = {
  enabled: false,
  comments: { enabled: true, topLevelOnly: true, maxPerMediaPerHour: 8, maxPerHour: 25, maxChars: 280 },
  dms: { enabled: true, maxPerHour: 60, maxChars: 700 },
  model: "gpt-4o-mini",
  temperature: 0.6,
  persona: "",
  facts: [],
  rules: [],
};

let cache = null; // { config, mtimeMs }

const file = () => process.env.IG_AI_FILE || SEED_FILE;

/** Copy the repo seed into the writable location, once. Only ever creates. */
function seed() {
  const target = file();
  if (fs.existsSync(target)) return { seeded: false, file: target };
  if (path.resolve(target) === path.resolve(SEED_FILE)) return { seeded: false, file: target };
  try {
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.writeFileSync(target, fs.readFileSync(SEED_FILE, "utf8"), { mode: 0o640 });
    console.log(`ai config seeded into ${target}`);
    return { seeded: true, file: target };
  } catch (err) {
    // Not fatal. Without a config the AI is simply off, and the keyword rules
    // — the part that earns money — do not care.
    console.error("!! could not seed ai config:", err && err.message);
    return { seeded: false, file: target, error: err && err.message };
  }
}

/** Shallow-merge one level deep, so a file that sets only `persona` still gets every cap. */
function withDefaults(raw) {
  const c = raw && typeof raw === "object" ? raw : {};
  return {
    ...DEFAULTS,
    ...c,
    comments: { ...DEFAULTS.comments, ...(c.comments || {}) },
    dms: { ...DEFAULTS.dms, ...(c.dms || {}) },
    facts: Array.isArray(c.facts) ? c.facts : DEFAULTS.facts,
    rules: Array.isArray(c.rules) ? c.rules : DEFAULTS.rules,
  };
}

function current() {
  const p = file();
  let stat;
  try {
    stat = fs.statSync(p);
  } catch {
    return cache ? cache.config : withDefaults(null);
  }
  if (cache && cache.mtimeMs === stat.mtimeMs) return cache.config;

  try {
    const config = withDefaults(JSON.parse(fs.readFileSync(p, "utf8")));
    cache = { config, mtimeMs: stat.mtimeMs };
    return config;
  } catch (err) {
    console.error("!! ai config is not valid JSON, keeping the last good copy:", err && err.message);
    return cache ? cache.config : withDefaults(null);
  }
}

module.exports = { current, seed, file, withDefaults, DEFAULTS };
