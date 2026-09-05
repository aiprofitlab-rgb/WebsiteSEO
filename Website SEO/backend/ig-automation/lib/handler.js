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
 *
 * THE AI FALLBACK. Where this file used to drop an event it did not want — a
 * comment matching no keyword, a DM from someone the email capture was not
 * waiting on — it now offers that event to `deps.ai` instead. Keywords always
 * win: the fallback only ever sees what the rules declined, and it cannot send
 * a DM off a comment, so it can never burn the one-shot private reply a keyword
 * rule might still need. With `deps.ai` absent, every path below behaves exactly
 * as it did before the fallback existed, which is what keeps the original tests
 * honest.
 *
 * The fallback is the most dangerous feature in this service, because a reply
 * nobody wrote in advance defeats the guard that caught the 2026-08-30 loop:
 * rules.isOwnReplyText() recognises our own words by comparing them to the fixed
 * strings in the config, and generated text has no fixed string to compare to.
 * `store.remember`/`saidRecently` is the replacement — we hash every sentence we
 * post and refuse to answer it if it comes back. See lib/ai.js for the other
 * half, which is that generated text is re-run through rules.match() before it
 * is allowed out, so it can never contain a word that would trigger us.
 */

const crypto = require("node:crypto");

const rulesLib = require("./rules");

/**
 * The AI's rows in the `handled` table wear these instead of a real rule id, so
 * its own caps can be counted separately from the keyword rules' and so a glance
 * at the admin panel's recent-activity list says which brain answered.
 */
const AI_COMMENT_RULE = "ai:comment";
const AI_DM_RULE = "ai:dm";

/**
 * A stable fingerprint of what we said, on the normalised form — so casing, an
 * added @mention, Arabic diacritics or a zero-width character cannot smuggle our
 * own sentence back past us. Truncated: 128 bits is far past collision risk for
 * a table that holds a few hundred rows for six hours.
 */
function fingerprint(text) {
  const norm = rulesLib.normalise(text);
  return norm ? crypto.createHash("sha256").update(norm).digest("hex").slice(0, 32) : "";
}

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

  // Guard 2b. The same idea, for words that were never in the config. Guard 2
  // can only recognise the fixed publicReply strings; once a language model is
  // writing the replies there is no fixed string, so every sentence we post is
  // fingerprinted on the way out and looked up again here on the way back in.
  // Without this the fallback would answer itself, exactly as the account did on
  // 2026-08-30, and no amount of prompt wording would stop it.
  if (store.saidRecently && store.saidRecently(fingerprint(text), now)) {
    return { action: "drop", why: "our own generated reply" };
  }

  // Guard 3. Most comments are not keywords.
  //
  // The media id is part of the question, not a filter applied to the answer: a
  // rule can be scoped to particular posts, and "first match wins" has to mean
  // the first rule that could actually fire under THIS post. Passing the key at
  // all is what turns targeting on, so an event that somehow arrives without a
  // media id still matches every untargeted rule and none of the targeted ones.
  const matched = rulesLib.match(text, cfg, { mediaId: media.id || "" });
  if (!matched) {
    // Nothing the rules wanted. Before the fallback existed this was the end of
    // the line, and with no `ai` wired in it still is.
    return deps.ai ? aiAnswerComment(value, entry, deps) : { action: "drop", why: "no keyword" };
  }
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
  //
  // An attached file travels as a URL inside this one message, because there is
  // no second message: Meta allows exactly one private reply per comment, ever.
  // A file that has been deleted since the rule was written resolves to "" and
  // the DM goes out with its text and link — a lead with a slightly thinner
  // message beats a lead with a 404 in it.
  const fileUrl = deps.files && rule.dm && rule.dm.fileId ? deps.files.urlFor(rule.dm.fileId) : "";
  if (rule.dm && rule.dm.fileId && !fileUrl) {
    console.error("ATTACHED FILE IS MISSING:", rule.dm.fileId, "for rule", rule.id, "— sending the DM without it");
  }

  let dmOk = false;
  try {
    await ig.privateReply({ commentId, text: rulesLib.dmText(rule, { fileUrl }) });
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
 * A comment no keyword wanted, answered in public by the model.
 *
 * PUBLIC REPLY ONLY, and that is a deliberate limit rather than a missing
 * feature. Meta allows exactly ONE private reply per comment, ever; if the
 * fallback spent it on small talk, the keyword rule that person triggers on
 * their next comment would have nothing left to send. The whole point of the
 * fallback is to be the cheap half of the funnel, so it takes the surface that
 * is free and leaves the scarce one alone.
 *
 * @returns {{action: string, why?: string, ruleId?: string}}
 */
async function aiAnswerComment(value, entry, deps) {
  const { ig, store, ai, rules: cfg, aiConfig, alert, limits, now = Date.now() } = deps;
  const caps = { ...DEFAULT_LIMITS, ...(limits || {}) };

  const ac = aiConfig || {};
  if (!ac.enabled) return { action: "drop", why: "no keyword" };
  const cc = ac.comments || {};
  if (!cc.enabled) return { action: "drop", why: "ai comments off" };
  if (!ai.configured || !ai.configured()) return { action: "drop", why: "ai not configured" };

  const commentId = value.id;
  const from = value.from || {};
  const media = value.media || {};
  const text = value.text || "";

  if (!String(text).trim()) return { action: "drop", why: "empty comment" };

  /**
   * Only top-level comments, by default.
   *
   * A reply to a comment carries parent_id. Answering those turns one comment
   * into a thread the account is obliged to keep up with — and a thread is the
   * shape a loop takes once the other participant is also automated. The rules
   * still fire on replies exactly as before; this limit is the fallback's alone.
   */
  if (cc.topLevelOnly !== false && value.parent_id) {
    return { action: "drop", why: "reply to a comment, not a top-level one" };
  }

  // The shared circuit breaker, unchanged. It bounds everything this service
  // says under one post, whichever brain said it.
  const since = now - caps.windowMs;
  const perMedia = media.id ? store.recentReplies({ mediaId: media.id, since }) : 0;
  const perAccount = store.recentReplies({ since });
  if (perMedia >= caps.perMediaPerHour || perAccount >= caps.perAccountPerHour) {
    return { action: "throttled", why: "loop breaker", ruleId: AI_COMMENT_RULE };
  }

  // And the fallback's own, tighter caps. These count only replies that actually
  // went out, so a run of spam the model declines to answer does not use them up.
  const aiPerMedia = media.id ? store.recentSent({ mediaId: media.id, ruleId: AI_COMMENT_RULE, since }) : 0;
  const aiPerAccount = store.recentSent({ ruleId: AI_COMMENT_RULE, since });
  const aiMediaCap = Number(cc.maxPerMediaPerHour);
  const aiAccountCap = Number(cc.maxPerHour);
  if ((Number.isFinite(aiMediaCap) && aiPerMedia >= aiMediaCap) || (Number.isFinite(aiAccountCap) && aiPerAccount >= aiAccountCap)) {
    const why = aiPerMedia >= aiMediaCap ? `${aiPerMedia} ai replies on this post in the last hour` : `${aiPerAccount} ai replies in the last hour`;
    console.warn("AI COMMENT CAP REACHED:", why, "— staying quiet on", commentId);
    return { action: "throttled", why, ruleId: AI_COMMENT_RULE };
  }

  // Same atomic claim the keyword path uses, so a Meta retry cannot produce a
  // second public reply. Taken BEFORE the model call: paying for a completion
  // twice is cheaper than posting twice, and only one of the two is visible to
  // followers.
  if (!store.claim(commentId, { accountId: entry.id || "", mediaId: media.id, commenterId: from.id, username: from.username, ruleId: AI_COMMENT_RULE }, now)) {
    return { action: "drop", why: "already handled", ruleId: AI_COMMENT_RULE };
  }

  let reply = null;
  try {
    reply = await ai.replyToComment({ text, username: from.username, config: ac, rulesConfig: cfg, mediaId: media.id || "" });
  } catch (err) {
    console.error("AI COMMENT FAILED:", commentId, err && err.code, err && err.message);
    store.finish(commentId, "ai_failed", clip(err && err.message, 300), now);
    if (err && err.code === "NO_KEY" && alert && alert.tokenRejected) {
      await alert.tokenRejected({ where: "ai", message: "OPENAI_API_KEY is missing", code: "NO_KEY" }).catch(() => {});
    }
    return { action: "error", why: err && err.message, ruleId: AI_COMMENT_RULE };
  }

  // The model declined, or its answer tripped a guard in lib/ai.js. Silence is a
  // correct outcome here, not a failure — most comments deserve no reply.
  if (!reply) {
    store.finish(commentId, "skipped", "nothing to say", now);
    return { action: "skipped", why: "no reply generated", ruleId: AI_COMMENT_RULE };
  }

  // Remember it BEFORE it exists anywhere Meta can hand it back. Doing this after
  // the post would leave a window — small, but exactly the width of a webhook
  // round trip — in which our own sentence arrives and is not yet recognised.
  store.remember(fingerprint(reply), now);

  try {
    await ig.publicReply({ commentId, message: reply });
  } catch (err) {
    console.error("AI PUBLIC REPLY FAILED:", commentId, err.code, err.message);
    store.finish(commentId, "failed", clip(err.message, 300), now);
    if (err.tokenProblem && alert) {
      await alert.tokenRejected({ where: "aiPublicReply", message: err.message, code: err.code }).catch(() => {});
    }
    return { action: "failed", why: err.message, ruleId: AI_COMMENT_RULE };
  }

  store.finish(commentId, "sent", "", now);
  return { action: "ai_replied", ruleId: AI_COMMENT_RULE, surface: "comment", username: from.username || "", reply };
}

/**
 * One message event.
 *
 * Two jobs, in this order. First the email capture, which is a specific person
 * we are specifically waiting on and must not be interrupted — a follower typing
 * their address is answering a question we asked, and handing that to a chatbot
 * instead would lose the lead. Everything else goes to the fallback.
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
  if (!state || state.state !== "awaiting_email") {
    return deps.ai ? aiAnswerDm(messaging, entry, deps) : { action: "drop", why: "not awaiting email" };
  }

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

  // The capture flow and the fallback share one thread. Recording this exchange
  // means that when the same person says "so how does it work?" thirty seconds
  // later, the model can see it already has their email and does not ask again.
  if (store.addTurn) {
    store.addTurn(senderId, "user", msg.text, now);
    store.addTurn(senderId, "assistant", `Got their email: ${email}`, now);
  }

  try {
    await ig.sendText({ igsid: senderId, text: `Got it — sending it to ${email}. Anything you want me to look at on your side, just reply here.` });
  } catch (err) {
    console.error("CONFIRM FAILED:", senderId, err.code, err.message);
  }

  store.clearState(senderId);
  return { action: "email_captured", email, ruleId: state.rule_id };
}

/**
 * A DM the email capture was not waiting for — the ordinary case, and until now
 * the one this service threw away without so much as a log line.
 *
 * Meta only allows a reply within 24 hours of the person's last message, which
 * happens to be exactly the right policy for a fallback anyway: if someone wrote
 * yesterday and nobody answered, an automated reply arriving now is worse than
 * none. A send outside the window fails at Graph and is logged, not retried.
 *
 * @returns {{action: string, why?: string, ruleId?: string}}
 */
async function aiAnswerDm(messaging, entry, deps) {
  const { ig, store, ai, rules: cfg, aiConfig, alert, now = Date.now() } = deps;

  const ac = aiConfig || {};
  if (!ac.enabled) return { action: "drop", why: "not awaiting email" };
  const dc = ac.dms || {};
  if (!dc.enabled) return { action: "drop", why: "ai dms off" };
  if (!ai.configured || !ai.configured()) return { action: "drop", why: "ai not configured" };

  const msg = messaging.message || {};
  const senderId = messaging.sender.id;
  const text = String(msg.text || "");
  const username = (messaging.sender && messaging.sender.username) || "";
  const since = now - DEFAULT_LIMITS.windowMs;

  const cap = Number(dc.maxPerHour);
  if (Number.isFinite(cap) && store.recentSent({ ruleId: AI_DM_RULE, since }) >= cap) {
    console.warn("AI DM CAP REACHED:", cap, "in the last hour — staying quiet");
    return { action: "throttled", why: "ai dm cap", ruleId: AI_DM_RULE };
  }

  /**
   * Dedupe on Meta's message id.
   *
   * A DM has no comment id, but `mid` is unique per message and Meta retries a
   * delivery it thinks failed just as it does for comments. Reusing the same
   * table is deliberate: one place to look when asking "did we answer this", and
   * the caps above read the same rows.
   *
   * A message with no mid is not dropped. Meta has always sent one, but a missing
   * id is a reason to lose dedupe for that one message, not a reason to ignore a
   * follower — so it falls back to a synthetic key that is stable for a minute,
   * which is long enough to swallow a retry burst and short enough to never
   * silence a real second message.
   */
  const mid = msg.mid || `nomid:${senderId}:${fingerprint(text)}:${Math.floor(now / 60_000)}`;
  if (!store.claim(mid, { accountId: entry.id || "", commenterId: senderId, username, ruleId: AI_DM_RULE }, now)) {
    return { action: "drop", why: "already handled", ruleId: AI_DM_RULE };
  }

  // Read the thread BEFORE adding this message, because lib/ai.js appends it as
  // the final user turn itself — adding it here too would show the model the
  // same sentence twice and invite it to answer the echo.
  const history = store.transcript ? store.transcript(senderId, { now }) : [];
  if (store.addTurn) store.addTurn(senderId, "user", text, now);

  let reply = null;
  try {
    reply = await ai.replyToDm({ text, username, history, config: ac, rulesConfig: cfg });
  } catch (err) {
    console.error("AI DM FAILED:", senderId, err && err.code, err && err.message);
    store.finish(mid, "ai_failed", clip(err && err.message, 300), now);
    if (err && err.code === "NO_KEY" && alert && alert.tokenRejected) {
      await alert.tokenRejected({ where: "ai", message: "OPENAI_API_KEY is missing", code: "NO_KEY" }).catch(() => {});
    }
    return { action: "error", why: err && err.message, ruleId: AI_DM_RULE };
  }

  if (!reply) {
    store.finish(mid, "skipped", "nothing to say", now);
    return { action: "skipped", why: "no reply generated", ruleId: AI_DM_RULE };
  }

  try {
    await ig.sendText({ igsid: senderId, text: reply });
  } catch (err) {
    // The overwhelmingly likely cause is the 24h window having closed, which is
    // Meta enforcing its own policy and not a fault of ours.
    console.error("AI DM SEND FAILED:", senderId, err.code, err.message);
    store.finish(mid, "failed", clip(err.message, 300), now);
    if (err.tokenProblem && alert) {
      await alert.tokenRejected({ where: "aiDm", message: err.message, code: err.code }).catch(() => {});
    }
    return { action: "failed", why: err.message, ruleId: AI_DM_RULE };
  }

  if (store.addTurn) store.addTurn(senderId, "assistant", reply, now);
  store.finish(mid, "sent", "", now);
  return { action: "ai_replied", ruleId: AI_DM_RULE, surface: "dm", username, reply };
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

module.exports = {
  handleEvent,
  handleComment,
  handleMessage,
  aiAnswerComment,
  aiAnswerDm,
  isSelf,
  fingerprint,
  EMAIL_RE,
  DEFAULT_LIMITS,
  AI_COMMENT_RULE,
  AI_DM_RULE,
};
