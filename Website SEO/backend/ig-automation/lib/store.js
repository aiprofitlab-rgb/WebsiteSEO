/**
 * Durable state: the dedupe set, and the email-capture conversation.
 *
 * Both have to survive a restart, so neither can live in a Map.
 *
 *   Dedupe — Meta retries a webhook it thinks failed, and a private reply is
 *   one-shot per comment FOREVER. A retry that got through twice would burn the
 *   single reply on a duplicate and post a second public comment. claim() is
 *   the guard: it is an atomic INSERT that only one caller can win.
 *
 *   Conversation — "reply with your email" only works if the service still
 *   remembers, minutes or hours later, which rule that person was answering.
 *
 * Storage is node:sqlite, built into Node 22.5+. Deliberately NOT better-sqlite3:
 * that is a native module, and needing a C++ toolchain on the VPS just to install
 * the service is a bad trade for a table with two columns.
 */

const fs = require("node:fs");
const path = require("node:path");
const { DatabaseSync } = require("node:sqlite");

const DEFAULT_FILE = path.join(__dirname, "..", "ig-automation.sqlite");

// Meta's rule: after a user messages us, we may reply for 24 hours. A capture
// state that outlives the window is a state we could not act on anyway.
const STATE_TTL_MS = 24 * 60 * 60 * 1000;
// Long enough that no plausible Meta retry lands after it. Keeps the table small.
const HANDLED_TTL_MS = 60 * 24 * 60 * 60 * 1000;

function open(file) {
  const target = file || process.env.IG_DB_FILE || DEFAULT_FILE;
  fs.mkdirSync(path.dirname(target), { recursive: true });

  const db = new DatabaseSync(target);
  // WAL survives an abrupt kill without corrupting; NORMAL is the right sync
  // level with WAL and avoids an fsync on every single comment.
  db.exec("PRAGMA journal_mode = WAL");
  db.exec("PRAGMA synchronous = NORMAL");
  db.exec("PRAGMA busy_timeout = 5000");

  db.exec(`
    CREATE TABLE IF NOT EXISTS handled (
      comment_id   TEXT PRIMARY KEY,
      account_id   TEXT,
      media_id     TEXT,
      commenter_id TEXT,
      username     TEXT,
      rule_id      TEXT,
      status       TEXT NOT NULL DEFAULT 'processing',
      notes        TEXT,
      claimed_at   INTEGER NOT NULL,
      finished_at  INTEGER
    );
    CREATE INDEX IF NOT EXISTS handled_claimed ON handled (claimed_at);
    -- The circuit breaker asks "how many did we answer under this post lately",
    -- on every keyword comment. Without this it is a table scan each time.
    CREATE INDEX IF NOT EXISTS handled_media ON handled (media_id, claimed_at);

    CREATE TABLE IF NOT EXISTS conversations (
      igsid      TEXT PRIMARY KEY,
      account_id TEXT,
      state      TEXT NOT NULL,
      rule_id    TEXT,
      comment_id TEXT,
      username   TEXT,
      updated_at INTEGER NOT NULL,
      expires_at INTEGER NOT NULL
    );
    CREATE INDEX IF NOT EXISTS conversations_expiry ON conversations (expires_at);
  `);

  const stmts = {
    claim: db.prepare(
      `INSERT OR IGNORE INTO handled
         (comment_id, account_id, media_id, commenter_id, username, rule_id, status, claimed_at)
       VALUES (?, ?, ?, ?, ?, ?, 'processing', ?)`
    ),
    finish: db.prepare(`UPDATE handled SET status = ?, notes = ?, finished_at = ? WHERE comment_id = ?`),
    getHandled: db.prepare(`SELECT * FROM handled WHERE comment_id = ?`),
    dropHandled: db.prepare(`DELETE FROM handled WHERE comment_id = ?`),
    stuck: db.prepare(`SELECT * FROM handled WHERE status = 'processing' AND claimed_at < ? ORDER BY claimed_at`),
    countHandled: db.prepare(`SELECT COUNT(*) AS n FROM handled`),
    recentHandled: db.prepare(`SELECT * FROM handled ORDER BY claimed_at DESC LIMIT ?`),

    setState: db.prepare(
      `INSERT INTO conversations (igsid, account_id, state, rule_id, comment_id, username, updated_at, expires_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)
       ON CONFLICT(igsid) DO UPDATE SET
         account_id = excluded.account_id,
         state      = excluded.state,
         rule_id    = excluded.rule_id,
         comment_id = excluded.comment_id,
         username   = excluded.username,
         updated_at = excluded.updated_at,
         expires_at = excluded.expires_at`
    ),
    getState: db.prepare(`SELECT * FROM conversations WHERE igsid = ?`),
    clearState: db.prepare(`DELETE FROM conversations WHERE igsid = ?`),
    countStates: db.prepare(`SELECT COUNT(*) AS n FROM conversations WHERE expires_at > ?`),

    recentByMedia: db.prepare(`SELECT COUNT(*) AS n FROM handled WHERE media_id = ? AND claimed_at >= ?`),
    recentAll: db.prepare(`SELECT COUNT(*) AS n FROM handled WHERE claimed_at >= ?`),

    sweepStates: db.prepare(`DELETE FROM conversations WHERE expires_at <= ?`),
    sweepHandled: db.prepare(`DELETE FROM handled WHERE claimed_at < ?`),
  };

  return {
    file: target,

    /**
     * Take exclusive ownership of a comment.
     * @returns {boolean} true if this caller won and should do the work.
     *   false means a retry, or a concurrent delivery, already has it.
     */
    claim(commentId, meta = {}, now = Date.now()) {
      if (!commentId) return false;
      const res = stmts.claim.run(
        String(commentId),
        meta.accountId || null,
        meta.mediaId || null,
        meta.commenterId || null,
        meta.username || null,
        meta.ruleId || null,
        now
      );
      return res.changes === 1;
    },

    /** Record the outcome. Failures stay visible instead of looking like successes. */
    finish(commentId, status, notes = "", now = Date.now()) {
      stmts.finish.run(String(status), notes ? String(notes) : null, now, String(commentId));
    },

    /**
     * Give a claim back. Only for the case where the work never started — a
     * genuine crash before the first API call. Never call this after a private
     * reply attempt: a second attempt cannot succeed and would re-post the
     * public reply and re-log the lead.
     */
    release(commentId) {
      stmts.dropHandled.run(String(commentId));
    },

    handled: (commentId) => stmts.getHandled.get(String(commentId)) || null,

    /**
     * How many comments we have taken on recently — under one post, or across the
     * whole account. This is what the loop breaker in handler.js reads.
     *
     * It counts claims, not successes, deliberately: a loop that is failing every
     * DM is still a loop, and it is still hammering Graph.
     */
    recentReplies({ mediaId, since } = {}) {
      const from = Number(since) || 0;
      const row = mediaId ? stmts.recentByMedia.get(String(mediaId), from) : stmts.recentAll.get(from);
      return (row && row.n) || 0;
    },

    /**
     * The last N comments taken on, newest first. Read-only, and the only thing
     * the admin panel needs from this table: "did my new rule actually fire?"
     * is otherwise a journalctl session over SSH.
     */
    recent(limit = 40) {
      const n = Math.min(Math.max(Number(limit) || 40, 1), 500);
      return stmts.recentHandled.all(n);
    },

    /** Claims that never reported an outcome — a crash mid-flight. For /health and ops. */
    stuck(olderThanMs = 10 * 60_000, now = Date.now()) {
      return stmts.stuck.all(now - olderThanMs);
    },

    setState(igsid, patch = {}, now = Date.now()) {
      stmts.setState.run(
        String(igsid),
        patch.accountId || null,
        String(patch.state || "awaiting_email"),
        patch.ruleId || null,
        patch.commentId || null,
        patch.username || null,
        now,
        now + (patch.ttlMs || STATE_TTL_MS)
      );
    },

    /** null once the 24h messaging window has closed, even though the row lingers. */
    getState(igsid, now = Date.now()) {
      const row = stmts.getState.get(String(igsid));
      if (!row) return null;
      if (row.expires_at <= now) return null;
      return row;
    },

    clearState: (igsid) => stmts.clearState.run(String(igsid)),

    /** Housekeeping. Cheap enough to run on an interval from server.js. */
    sweep(now = Date.now()) {
      const states = stmts.sweepStates.run(now).changes;
      const old = stmts.sweepHandled.run(now - HANDLED_TTL_MS).changes;
      return { states, handled: old };
    },

    stats(now = Date.now()) {
      return {
        handled: stmts.countHandled.get().n,
        openConversations: stmts.countStates.get(now).n,
        stuck: stmts.stuck.all(now - 10 * 60_000).length,
      };
    },

    close: () => db.close(),
  };
}

module.exports = { open, STATE_TTL_MS, HANDLED_TTL_MS };
