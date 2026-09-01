/**
 * What actually happens when a comment arrives.
 *
 * Everything is injected — ig, store, ledger, alert, clock — so the whole flow
 * is testable without a network, a database file, or a spreadsheet. server.js
 * is the only place that wires the real ones.
 *
 * Order is not arbitrary. The cheap guards (our own comment, our own words, no
 * keyword, already handled, too many already) run before anything with a side
 * effect, because the expensive mistakes here are all duplicates.
 *
 * Two different duplicates, and they need different guards. A REDELIVERY is the
 * same comment id arriving twice; the dedupe table stops it. A LOOP is our own
 * public reply coming back as a brand new comment with a brand new id, which the
 * dedupe table cannot see at all — it has never been asked about that id before.
 * Everything named "loop" below exists for the second kind.
 */

const rulesLib = require("./rules");

const EMAIL_RE = /[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i;

/**
 * The circuit breaker's defaults. Not a rate limit — a loop detector. A real post
 * that genuinely draws more than this many keyword comments in an hour is a good
 * problem, and it is still better handled by hand than by a service that cannot
 * tell the difference between a viral reel and itself.
 */
const DEFAULT_LIMITS = { perMediaPerHour: 12, perAccountPerHour: 40, windowMs: 60 * 60 * 1000 };

/**
 * When we last mailed about a runaway post. A tripped breaker drops every
 * further comment on that post for the rest of the window, and one email per
 * dropped comment would turn one incident into a hundred notifications — the
 * exact shape of the problem being reported. In memory on purpose: a restart
 * re-alerting is the right behaviour, since a restart is someone intervening.
 */
const alerted = new Map();

/**
 * Is this comment ours?
 *
 * Four answers because no single one is dependable. `selfId` may be unset (the
 * boot lookup is allowed to fail) and, worse, may simply not be the id Meta puts
 * in `from.id` — that id is scoped, and the scope is not always the one the
 * token belongs to. `entry.id` is the account the webhook was raised for, which
 * is us by definition, and it is in every payload.
 */
function isSelf(from, accountId, selfId, selfUsername) {
  const id = String((from && from.id) || "");
  const username = String((from && from.username) || "").toLowerCase();
  if (id && selfId && id === String(selfId)) return true;
  if (id && accountId && id === String(accountId)) return true;
  if (username && selfUsername && username === String(selfUsername).toLowerCase()) return true;
  return false;
}

/** Sheets cells cap out at 50k chars, and a comment that long is not a keyword hit anyway. */
const clip = (s, n = 500) => (String(s || "").length > n ? String(s).slice(0, n - 1) + "…" : String(s || ""));

const iso = (ms) => new Date(ms).toISOString().replace("T", " ").slice(0, 19);

/**
 * One comment event.
 * @returns {{action: string, why?: string, ruleId?: string}} what was decided, for the log
 */
async function handleComment(value, entry, deps) {
  const { ig, store, ledger, rules: cfg, selfId, selfUsername, alert, limits, now = Date.now() } = deps;
  const caps = { ...DEFAULT_LIMITS, ...(limits || {}) };

  const commentId = value && value.id;
  const from = (value && value.from) || {};
  const media = (value && value.media) || {};
  const text = (value && value.text) || "";
  const accountId = (entry && entry.id) || "";

  if (!commentId) return { action: "drop", why: "no comment id" };

  // Guard 1. Our own public reply is itself a comment, and Meta sends it back to
  // us. Without this the service answers itself, forever.
  if (isSelf(from, accountId, selfId, selfUsername)) return { action: "drop", why: "our own comment" };

  // Guard 2. Our own words, no matter who Meta says posted them. This is the one
  // that holds when guard 1 does not, and guard 1 not holding is not theoretical:
  // it is one unset env var, or one id Meta scoped differently than we expected.
  if (rulesLib.isOwnReplyText(text, cfg)) return { action: "drop", why: "our own reply text" };

  // Guard 3. Most comments are not keywords. Costs nothing, so it runs before
  // the write to the dedupe table.
  const matched = rulesLib.match(text, cfg);
  if (!matched) return { action: "drop", why: "no keyword" };
  const { rule, keyword } = matched;

  // Guard 4. The circuit breaker. Every guard above is a statement about one
  // comment; this one is a statement about the account, and it is the only guard
  // that still works against a loop nobody predicted. Whatever goes wrong, the
  // damage stops at a dozen replies under one post instead of a hundred.
  const since = now - caps.windowMs;
  const perMedia = media.id ? store.recentReplies({ mediaId: media.id, since }) : 0;
  const perAccount = store.recentReplies({ since });
  if (perMedia >= caps.perMediaPerHour || perAccount >= caps.perAccountPerHour) {
    const why = perMedia >= caps.perMediaPerHour ? `${perMedia} replies on this post in the last hour` : `${perAccount} replies in the last hour`;
    console.error("LOOP BREAKER TRIPPED:", why, "— dropping", commentId, "on media", media.id);

    const key = String(media.id || "account");
    if (alert && alert.loopSuspected && !((alerted.get(key) || 0) > since)) {
      alerted.set(key, now);
      if (alerted.size > 500) alerted.clear();
      await alert.loopSuspected({ mediaId: media.id, commentId, perMedia, perAccount, caps, text }).catch(() => {});
    }
    return { action: "throttled", why, ruleId: rule.id };
  }

  // Guard 5. Atomic. A Meta retry loses this race and stops here, which is what
  // protects the one-shot private reply.
  const won = store.claim(
    commentId,
    { accountId, mediaId: media.id, commenterId: from.id, username: from.username, ruleId: rule.id },
    now
  );
  if (!won) return { action: "drop", why: "already handled", ruleId: rule.id };

  const record = {
    Timestamp: iso(now),
    Account: accountId,
    Username: from.username || "",
    "Commenter ID": from.id || "",
    "Comment ID": commentId,
    "Media ID": media.id || "",
    Permalink: "",
    "Comment text": clip(text),
    Keyword: keyword,
    Rule: rule.id,
    DM: "",
    "Public reply": "",
    Email: "",
    Status: "",
    Notes: "",
  };

  // The DM. This is the deliverable; everything after it is bookkeeping.
  let dmOk = false;
  try {
    await ig.privateReply({ commentId, text: rulesLib.dmText(rule) });
    dmOk = true;
    record.DM = "sent";
  } catch (err) {
    record.DM = "failed";
    record.Status = ledger.STATUS.FAILED;
    record.Notes = clip(err.message, 300);
    console.error("PRIVATE REPLY FAILED:", commentId, err.code, err.message);
    if (err.tokenProblem && alert) {
      await alert.tokenRejected({ where: "privateReply", message: err.message, code: err.code }).catch(() => {});
    }
  }

  // Only if the DM landed. "Sent! Check your DMs" under a comment that got no
  // DM is worse than staying quiet.
  if (dmOk && rule.publicReply) {
    try {
      await ig.publicReply({ commentId, message: rule.publicReply });
      record["Public reply"] = "posted";
    } catch (err) {
      record["Public reply"] = "failed";
      console.error("PUBLIC REPLY FAILED:", commentId, err.code, err.message);
    }
  }

  // Nice for the CRM row, worthless if it costs us the lead. Best-effort only.
  if (media.id) {
    try {
      const m = await ig.media(media.id);
      record.Permalink = (m && m.permalink) || "";
    } catch {
      /* ignore */
    }
  }

  if (dmOk) {
    record.Status = rule.askEmail ? ledger.STATUS.AWAITING_EMAIL : ledger.STATUS.SENT;
  }

  await ledger.append(record);

  // Arm the reply handler. Only meaningful if they actually got the DM.
  if (dmOk && rule.askEmail && from.id) {
    store.setState(from.id, { accountId, state: "awaiting_email", ruleId: rule.id, commentId, username: from.username }, now);
  }

  store.finish(commentId, dmOk ? "sent" : "failed", record.Notes, now);
  return { action: dmOk ? "sent" : "failed", ruleId: rule.id, keyword };
}

/**
 * One message event — the second half of email capture.
 * Only acts on people we are already expecting to hear from.
 */
async function handleMessage(messaging, entry, deps) {
  const { ig, store, ledger, selfId, selfUsername, now = Date.now() } = deps;

  const msg = (messaging && messaging.message) || {};
  const senderId = (messaging && messaging.sender && messaging.sender.id) || "";

  // Our own outbound DM is echoed back to us. Answering it is an infinite loop.
  if (msg.is_echo) return { action: "drop", why: "echo" };
  if (isSelf({ id: senderId }, (entry && entry.id) || "", selfId, selfUsername)) return { action: "drop", why: "our own message" };
  if (!senderId || !msg.text) return { action: "drop", why: "no text" };

  const state = store.getState(senderId, now);
  if (!state || state.state !== "awaiting_email") return { action: "drop", why: "not awaiting email" };

  const found = EMAIL_RE.exec(msg.text);
  if (!found) {
    // No nagging. One clarification, then leave them alone — the state stays
    // armed until the 24h window closes on its own.
    try {
      await ig.sendText({ igsid: senderId, text: "That doesn't look like an email — send it as name@example.com and I'll get the PDF over to you." });
    } catch (err) {
      console.error("CLARIFY FAILED:", senderId, err.code, err.message);
    }
    return { action: "clarify", why: "no email in text" };
  }

  const email = found[0].toLowerCase();
  await ledger.update(state.comment_id, { Email: email, Status: ledger.STATUS.EMAIL_CAPTURED });

  try {
    await ig.sendText({ igsid: senderId, text: `Got it — sending it to ${email}. Anything you want me to look at on your side, just reply here.` });
  } catch (err) {
    console.error("CONFIRM FAILED:", senderId, err.code, err.message);
  }

  store.clearState(senderId);
  return { action: "email_captured", email, ruleId: state.rule_id };
}

/**
 * Walk a whole webhook body. Meta batches, so one POST can carry several events
 * across several entries, and one bad event must not abandon the rest.
 */
async function handleEvent(body, deps) {
  const results = [];
  if (!body || body.object !== "instagram") return results;

  for (const entry of body.entry || []) {
    for (const change of entry.changes || []) {
      if (change.field !== "comments") {
        results.push({ action: "drop", why: `field ${change.field}` });
        continue;
      }
      try {
        results.push(await handleComment(change.value || {}, entry, deps));
      } catch (err) {
        console.error("COMMENT HANDLER THREW:", err && err.stack);
        results.push({ action: "error", why: err && err.message });
      }
    }

    for (const messaging of entry.messaging || []) {
      try {
        results.push(await handleMessage(messaging, entry, deps));
      } catch (err) {
        console.error("MESSAGE HANDLER THREW:", err && err.stack);
        results.push({ action: "error", why: err && err.message });
      }
    }
  }
  return results;
}

module.exports = { handleEvent, handleComment, handleMessage, isSelf, EMAIL_RE, DEFAULT_LIMITS };
