/**
 * Durable state: the dedupe set, the email-capture conversation, the AI's
 * short-term memory, and the record of what the AI has already said.
 *
 * None of it can live in a Map, because all of it has to survive a restart.
 *
 *   Dedupe — Meta retries a webhook it thinks failed, and a private reply is
 *   one-shot per comment FOREVER. A retry that got through twice would burn the
 *   single reply on a duplicate and post a second public comment. claim() is
 *   the guard: it is an atomic INSERT that only one caller can win.
 *
 *   Conversation — "reply with your email" only works if the service still
 *   remembers, minutes or hours later, which rule that person was answering.
 *
 *   Transcript — the AI fallback answers a DM in context, so it has to be able
 *   to read back the last few turns. Trimmed hard: this is a lead-capture bot,
 *   not a therapist, and an unbounded transcript is an unbounded prompt bill.
 *
 *   Said — every sentence the AI has posted publicly, recently, as a hash.
 *   rules.isOwnReplyText() recognises our own words by comparing them against
 *   the fixed publicReply strings in the config. The AI has no fixed strings,
 *   so that guard cannot see its output at all — and an AI that answers every
 *   comment, then meets its own answer coming back as a new comment, is the
 *   2026-08-30 reply loop with a language model attached. This table is how the
 *   same guard is made to work on text nobody wrote in advance.
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
// How long the AI remembers a DM thread. Matches the 24h window it can reply in:
// past that, the next message starts a conversation we could not have continued.
const TRANSCRIPT_TTL_MS = 24 * 60 * 60 * 1000;
// How long our own public sentences stay recognisable. A loop closes in seconds,
// not days, and keeping these forever would eventually start silencing followers
// who happen to phrase something the way we once did.
const SAID_TTL_MS = 6 * 60 * 60 * 1000;
// Turns of DM history handed to the model. Six is three exchanges — enough to
// not re-ask a question already answered, small enough to stay cheap.
const TRANSCRIPT_TURNS = 6;

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

    -- The AI's short-term memory of one DM thread. role is 'user' or 'assistant',
    -- named to match what the model expects so nothing has to be translated on
    -- the way out.
    CREATE TABLE IF NOT EXISTS transcript (
      id      INTEGER PRIMARY KEY AUTOINCREMENT,
      igsid   TEXT NOT NULL,
      role    TEXT NOT NULL,
      text    TEXT NOT NULL,
      at      INTEGER NOT NULL
    );
    CREATE INDEX IF NOT EXISTS transcript_thread ON transcript (igsid, id);
    CREATE INDEX IF NOT EXISTS transcript_age ON transcript (at);

    -- What we have said out loud, by hash. Read on every incoming comment, so it
    -- is a primary-key lookup and never a scan.
    CREATE TABLE IF NOT EXISTS said (
      hash TEXT PRIMARY KEY,
      at   INTEGER NOT NULL
    );
    CREATE INDEX IF NOT EXISTS said_age ON said (at);
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

    // Same question as above, narrowed to one rule and to claims that actually
    // ended in something being posted. The AI needs this shape and the keyword
    // path must not: a keyword comment we claimed and then failed to DM is still
    // evidence of a loop, whereas an AI comment we claimed and then declined to
    // answer is evidence of the guards working. Counting declines against the
    // AI's own cap would let a wave of spam silence it for the rest of the hour.
    sentByMediaRule: db.prepare(
      `SELECT COUNT(*) AS n FROM handled WHERE media_id = ? AND rule_id = ? AND status = 'sent' AND claimed_at >= ?`
    ),
    sentByRule: db.prepare(`SELECT COUNT(*) AS n FROM handled WHERE rule_id = ? AND status = 'sent' AND claimed_at >= ?`),

    addTurn: db.prepare(`INSERT INTO transcript (igsid, role, text, at) VALUES (?, ?, ?, ?)`),
    // Newest first here, reversed by the caller. Taking the tail in SQL means the
    // index does the work; ordering it back to oldest-first is free in JS.
    lastTurns: db.prepare(`SELECT role, text FROM transcript WHERE igsid = ? AND at > ? ORDER BY id DESC LIMIT ?`),
    dropTurns: db.prepare(`DELETE FROM transcript WHERE igsid = ?`),

    remember: db.prepare(`INSERT OR REPLACE INTO said (hash, at) VALUES (?, ?)`),
    recall: db.prepare(`SELECT at FROM said WHERE hash = ?`),

    sweepTurns: db.prepare(`DELETE FROM transcript WHERE at <= ?`),
    sweepSaid: db.prepare(`DELETE FROM said WHERE at <= ?`),
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
     * How many replies under one rule actually went out recently. The AI's own
     * cap; see the statement above for why it is not just recentReplies().
     */
    recentSent({ mediaId, ruleId, since } = {}) {
      const from = Number(since) || 0;
      const rule = String(ruleId || "");
      const row = mediaId ? stmts.sentByMediaRule.get(String(mediaId), rule, from) : stmts.sentByRule.get(rule, from);
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

    /**
     * Append one turn of a DM thread.
     *
     * Called for the follower's message AND for our own answer, because a model
     * that cannot see what it already said will greet the same person four times
     * in a row. Text is clipped: a pasted wall of text is not worth the tokens,
     * and the interesting part of a long message is at the front.
     */
    addTurn(igsid, role, text, now = Date.now()) {
      if (!igsid || !text) return;
      stmts.addTurn.run(String(igsid), role === "assistant" ? "assistant" : "user", String(text).slice(0, 1000), now);
    },

    /**
     * The last few turns, oldest first — the order a chat model wants them in.
     * Anything older than the 24h window is excluded rather than deleted; the
     * sweep does the deleting, and a read must never depend on it having run.
     */
    transcript(igsid, { turns = TRANSCRIPT_TURNS, now = Date.now() } = {}) {
      if (!igsid) return [];
      const n = Math.min(Math.max(Number(turns) || TRANSCRIPT_TURNS, 1), 40);
      return stmts.lastTurns.all(String(igsid), now - TRANSCRIPT_TTL_MS, n).reverse();
    },

    forget: (igsid) => stmts.dropTurns.run(String(igsid)),

    /**
     * Record that we said this, and ask whether we recently did.
     *
     * The hash is of the caller's normalised form (lib/rules.normalise), so
     * casing, diacritics and a leading @mention do not defeat it — a follower
     * quoting us back with an @ in front is exactly the shape a loop takes.
     */
    remember(hash, now = Date.now()) {
      if (!hash) return;
      stmts.remember.run(String(hash), now);
    },

    saidRecently(hash, now = Date.now()) {
      if (!hash) return false;
      const row = stmts.recall.get(String(hash));
      return Boolean(row && row.at > now - SAID_TTL_MS);
    },

    /** Housekeeping. Cheap enough to run on an interval from server.js. */
    sweep(now = Date.now()) {
      const states = stmts.sweepStates.run(now).changes;
      const old = stmts.sweepHandled.run(now - HANDLED_TTL_MS).changes;
      const turns = stmts.sweepTurns.run(now - TRANSCRIPT_TTL_MS).changes;
      const said = stmts.sweepSaid.run(now - SAID_TTL_MS).changes;
      return { states, handled: old, turns, said };
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

module.exports = { open, STATE_TTL_MS, HANDLED_TTL_MS, TRANSCRIPT_TTL_MS, SAID_TTL_MS, TRANSCRIPT_TURNS };
