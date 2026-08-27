/**
 * The access token, and keeping it alive.
 *
 * Instagram long-lived tokens last 60 days. There is no warning when one dies:
 * the webhook keeps arriving, every Graph call starts returning 190, and the
 * automation is silently off until somebody notices the DMs stopped. So the
 * refresh is unattended, and a FAILED refresh is treated as an incident and
 * emailed — a failure that only logs is a failure nobody sees for eight weeks.
 *
 * The token lives in a file, not an env var, because refreshing rewrites it.
 * An env var would mean editing a systemd unit every 60 days, which is exactly
 * the manual step this is meant to remove. server.js re-reads the file when its
 * mtime changes, so the cron can rotate the token under a running process
 * without a restart.
 */

const fs = require("node:fs");
const path = require("node:path");

const { appsecretProof } = require("./signature");

const GRAPH = process.env.IG_GRAPH_BASE || "https://graph.instagram.com";
const DEFAULT_FILE = path.join(__dirname, "..", "token.json");
const DAY_MS = 24 * 60 * 60 * 1000;

const file = () => process.env.IG_TOKEN_FILE || DEFAULT_FILE;

let cache = null; // { record, mtimeMs }

function readFile() {
  const p = file();
  let stat;
  try {
    stat = fs.statSync(p);
  } catch {
    return null;
  }
  if (cache && cache.mtimeMs === stat.mtimeMs) return cache.record;
  try {
    const record = JSON.parse(fs.readFileSync(p, "utf8"));
    cache = { record, mtimeMs: stat.mtimeMs };
    return record;
  } catch (err) {
    console.error("TOKEN FILE UNREADABLE:", p, err && err.message);
    return null;
  }
}

/**
 * Atomic write. A half-written token file read by the server mid-refresh would
 * take the automation down, so the new content lands under a temp name and is
 * renamed into place, which is atomic on the same filesystem.
 */
function write(record) {
  const p = file();
  fs.mkdirSync(path.dirname(p), { recursive: true });
  const tmp = `${p}.${process.pid}.tmp`;
  fs.writeFileSync(tmp, JSON.stringify(record, null, 2) + "\n", { mode: 0o600 });
  fs.renameSync(tmp, p);
  cache = null; // force a re-stat on next read
  return record;
}

/**
 * The token to call Graph with.
 * Falls back to IG_ACCESS_TOKEN so a fresh box works before the first refresh.
 */
function current() {
  const record = readFile();
  if (record && record.access_token) return record.access_token;
  return process.env.IG_ACCESS_TOKEN || "";
}

/** Write the env-var token into the file once, so refreshes have something to rotate. */
function seed(token = process.env.IG_ACCESS_TOKEN, now = Date.now()) {
  if (!token) return null;
  if (readFile()) return null; // never clobber a refreshed token with a stale env var
  return write({
    access_token: token,
    expires_in: 60 * 24 * 3600,
    obtained_at: new Date(now).toISOString(),
    source: "IG_ACCESS_TOKEN (seed)",
  });
}

/**
 * Whole days before this token stops working. Negative means it already has.
 *
 * Rounds UP, so a token with any part of its last day remaining reads as 1
 * rather than 0. Flooring looks more conservative but is worse here: a freshly
 * refreshed 60-day token would read as 59 one millisecond later, so the number
 * in /health and in the alert email would disagree with the refresh that just
 * ran. Rounding up holds "60" steady for the whole first day and still reaches
 * 0 exactly at expiry.
 */
function daysLeft(now = Date.now()) {
  const record = readFile();
  if (!record) return null;
  const from = Date.parse(record.refreshed_at || record.obtained_at || "");
  if (!Number.isFinite(from) || !record.expires_in) return null;
  return Math.ceil((from + record.expires_in * 1000 - now) / DAY_MS);
}

/**
 * Exchange the current long-lived token for a fresh 60-day one.
 * Meta refuses this for a token less than 24h old — that is a normal answer on
 * a freshly seeded box, not an incident, so it is reported distinctly.
 */
async function refresh({ fetchImpl = fetch, now = Date.now() } = {}) {
  const token = current();
  if (!token) return { ok: false, reason: "no-token", message: "No token in file or IG_ACCESS_TOKEN." };

  const url = new URL(`${GRAPH}/refresh_access_token`);
  url.searchParams.set("grant_type", "ig_refresh_token");
  url.searchParams.set("access_token", token);
  // Not required by the endpoint's own documentation, but an app with "require
  // app secret for server API calls" switched on rejects EVERY Graph call
  // without it — including this one. Sending it when we have it costs nothing
  // and removes a failure that would only appear 60 days after that setting
  // was changed.
  const proof = appsecretProof(token, process.env.META_APP_SECRET);
  if (proof) url.searchParams.set("appsecret_proof", proof);

  let res, body;
  try {
    res = await fetchImpl(url, { method: "GET", signal: AbortSignal.timeout(15_000) });
    body = await res.json().catch(() => ({}));
  } catch (err) {
    return { ok: false, reason: "network", message: err && err.message };
  }

  if (!res.ok || !body.access_token) {
    const meta = body && body.error;
    const message = (meta && meta.message) || `HTTP ${res.status}`;
    // Meta's wording for "not old enough yet". Benign; the next daily run works.
    const tooSoon = /less than 24 hours|24 hours old/i.test(message);
    return { ok: false, reason: tooSoon ? "too-soon" : "rejected", message, status: res.status };
  }

  const record = write({
    access_token: body.access_token,
    expires_in: body.expires_in || 60 * 24 * 3600,
    obtained_at: (readFile() || {}).obtained_at || new Date(now).toISOString(),
    refreshed_at: new Date(now).toISOString(),
    source: "refresh_access_token",
  });

  // Reported by the same function /health uses, so the two never disagree.
  return { ok: true, daysLeft: daysLeft(), record };
}

module.exports = { current, seed, refresh, daysLeft, file, _write: write, _read: readFile };
