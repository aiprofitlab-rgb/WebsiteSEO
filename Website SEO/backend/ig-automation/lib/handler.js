/**
 * What actually happens when a comment arrives.
 *
 * Everything is injected — ig, store, ledger, alert, clock — so the whole flow
 * is testable without a network, a database file, or a spreadsheet. server.js
 * is the only place that wires the real ones.
 *
 * Order is not arbitrary. The three cheap guards (our own comment, no keyword,
 * already handled) run before anything with a side effect, because the expensive
 * mistakes here are all duplicates.
 */

const rulesLib = require("./rules");

const EMAIL_RE = /[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i;

/** Sheets cells cap out at 50k chars, and a comment that long is not a keyword hit anyway. */
const clip = (s, n = 500) => (String(s || "").length > n ? String(s).slice(0, n - 1) + "…" : String(s || ""));

const iso = (ms) => new Date(ms).toISOString().replace("T", " ").slice(0, 19);

/**
 * One comment event.
 * @returns {{action: string, why?: string, ruleId?: string}} what was decided, for the log
 */
async function handleComment(value, entry, deps) {
  const { ig, store, ledger, rules: cfg, selfId, alert, now = Date.now() } = deps;

  const commentId = value && value.id;
  const from = (value && value.from) || {};
  const media = (value && value.media) || {};
  const text = (value && value.text) || "";
  const accountId = (entry && entry.id) || "";

  if (!commentId) return { action: "drop", why: "no comment id" };

  // Guard 1. Our own public reply is itself a comment, and Meta sends it back to
  // us. Without this the service answers itself, forever.
  if (selfId && String(from.id) === String(selfId)) return { action: "drop", why: "our own comment" };

  // Guard 2. Most comments are not keywords. Costs nothing, so it runs before
  // the write to the dedupe table.
  const matched = rulesLib.match(text, cfg);
  if (!matched) return { action: "drop", why: "no keyword" };
  const { rule, keyword } = matched;

  // Guard 3. Atomic. A Meta retry loses this race and stops here, which is what
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
  const { ig, store, ledger, selfId, now = Date.now() } = deps;

  const msg = (messaging && messaging.message) || {};
  const senderId = (messaging && messaging.sender && messaging.sender.id) || "";

  // Our own outbound DM is echoed back to us. Answering it is an infinite loop.
  if (msg.is_echo) return { action: "drop", why: "echo" };
  if (selfId && String(senderId) === String(selfId)) return { action: "drop", why: "our own message" };
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

module.exports = { handleEvent, handleComment, handleMessage, EMAIL_RE };
