/**
 * Keyword matching for incoming comments.
 *
 * Real comments are not tidy. They arrive as "STOREFRONT!!", "@aiprofitlab
 * storefront 🔥", "مـتـجـر", or with a zero-width character pasted in from a
 * notes app. Matching raw text against a keyword misses most of those, so
 * every comment is normalised to a comparable form first, and the rule is
 * matched against that.
 *
 * Rules are ordered and the FIRST match wins. Put the specific keyword above
 * the generic one, or the generic one will swallow it.
 *
 * A rule can also be scoped to particular posts (`media.mode: "only"`), which
 * is what lets the same keyword mean different things on different reels. The
 * scope is part of matching, not a filter applied afterwards, because "first
 * match wins" has to mean "first match that could actually fire here".
 */

const fs = require("node:fs");
const path = require("node:path");

// Tashkeel (harakat) and the superscript alef. Decorative in typed Arabic and
// almost never present in the keyword as configured.
const ARABIC_DIACRITICS = /[ً-ٰٟ]/g;
// Tatweel — the kashida stretching character. "مـتـجـر" is the same word as "متجر".
const TATWEEL = /ـ/g;
// Zero-width joiners, marks and the BOM. Invisible, and they break substring matching.
const ZERO_WIDTH = /[​-‏‪-‮⁠﻿]/g;
// Leading @mentions: on a reply the username is part of the comment text, and a
// keyword rule should never fire on somebody's handle.
const LEADING_MENTIONS = /^(?:\s*@[A-Za-z0-9._]+)+/;

/**
 * Lowercase, unicode-normalised, Arabic-folded, mention-stripped.
 * Deliberately does NOT strip punctuation — the matcher handles adjacency.
 */
function normalise(text) {
  return String(text == null ? "" : text)
    .normalize("NFKC")
    .replace(ZERO_WIDTH, "")
    .replace(LEADING_MENTIONS, "")
    .replace(ARABIC_DIACRITICS, "")
    .replace(TATWEEL, "")
    .replace(/[أإآٱ]/g, "ا") // أ إ آ ٱ -> ا
    .replace(/ى/g, "ي") // ى -> ي
    .toLowerCase()
    .replace(/\s+/g, " ")
    .trim();
}

const escapeRe = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

const ARABIC_START = /^[\u0600-\u06FF]/;

/**
 * Whole-word match that also works for Arabic.
 *
 * \b is defined in terms of [A-Za-z0-9_] even with the u flag, so it reports a
 * boundary in the middle of any Arabic word. These lookarounds use the unicode
 * letter and number properties instead, which behave the same way for Latin and
 * correctly for Arabic. Emoji and punctuation are neither, so "متجر🔥" and
 * "storefront!!" both still match.
 *
 * Arabic also glues proclitics onto the front of a word, so a whole-word match
 * for "سعر" would miss "السعر" — which is how someone would actually write it.
 * The definite article ال and a leading و are allowed optionally in front of
 * any Arabic keyword. Other proclitics (بـ، لـ، فـ، كـ) are not, because they
 * shade the meaning more; add those as explicit keywords if a campaign needs
 * them.
 */
function wordRe(keyword) {
  if (!ARABIC_START.test(keyword)) {
    return new RegExp(`(?<![\\p{L}\\p{N}_])${escapeRe(keyword)}(?![\\p{L}\\p{N}_])`, "u");
  }
  const base = keyword.replace(/^و?ال/, "");
  return new RegExp(`(?<![\\p{L}\\p{N}_])و?(?:ال)?${escapeRe(base)}(?![\\p{L}\\p{N}_])`, "u");
}

function hits(normalisedText, keyword, mode) {
  const k = normalise(keyword);
  if (!k) return false;
  if (mode === "exact") return normalisedText === k;
  if (mode === "contains") return normalisedText.includes(k);
  return wordRe(k).test(normalisedText); // "word", the default
}

/* ---------------------------------------------------------------------------
 * Post targeting
 * ------------------------------------------------------------------------- */

/**
 * Which posts a rule is allowed to fire on.
 *
 * "only" with an empty id list is normalised back to "all" rather than to "no
 * posts". A rule that silently matches nothing is the worst of the two failure
 * modes — it looks configured and does nothing — and validate() reports the
 * empty list as an error so it cannot be saved from the panel anyway.
 */
function mediaScope(rule) {
  const m = (rule && rule.media) || {};
  const ids = Array.isArray(m.ids) ? m.ids.map((id) => String(id).trim()).filter(Boolean) : [];
  return m.mode === "only" && ids.length ? { mode: "only", ids } : { mode: "all", ids };
}

/**
 * Can this rule fire on this post?
 *
 * An unknown mediaId ("" or null — a comment event that arrived without one)
 * counts as "not one of the chosen posts". Scoping is an explicit narrowing by
 * the person who wrote the rule, so an ambiguous case resolves to not firing.
 */
function appliesToMedia(rule, mediaId) {
  const scope = mediaScope(rule);
  if (scope.mode === "all") return true;
  const id = String(mediaId == null ? "" : mediaId);
  return id !== "" && scope.ids.includes(id);
}

/** Could these two rules ever be in play under the same post? */
function scopesOverlap(a, b) {
  const sa = mediaScope(a);
  const sb = mediaScope(b);
  if (sa.mode === "all" || sb.mode === "all") return true;
  return sa.ids.some((id) => sb.ids.includes(id));
}

/**
 * @param {string} text comment body
 * @param {object} config the rules config
 * @param {{mediaId?: string}} [opts] pass mediaId to honour post targeting.
 *   OMITTING the key means "no post context" and every rule is considered —
 *   that is what validate() wants, and what the old two-argument callers get.
 * @returns {{rule: object, keyword: string}|null} first matching rule, or null
 */
function match(text, config, opts) {
  const norm = normalise(text);
  if (!norm) return null;
  const scoped = Boolean(opts && Object.prototype.hasOwnProperty.call(opts, "mediaId"));

  for (const rule of (config && config.rules) || []) {
    if (rule.enabled === false) continue;
    if (scoped && !appliesToMedia(rule, opts.mediaId)) continue;
    const mode = rule.match || "word";
    for (const keyword of rule.keywords || []) {
      if (hits(norm, keyword, mode)) return { rule, keyword };
    }
  }
  return null;
}

/**
 * Is this text one of our own public replies, handed back to us?
 *
 * Meta does not label a comment as ours in any way we can rely on — `from.id` is
 * scoped per app and is not always the id in IG_USER_ID — so identity alone is
 * not enough to recognise ourselves. The text is. Every public reply is a fixed
 * string out of this config; seeing one arrive as a new comment can only mean
 * the loop has already started, whoever Meta says wrote it.
 *
 * Equality on the normalised form, not a substring: a follower quoting us back
 * word for word is not a lead, and anything looser would start swallowing real
 * comments. Post targeting is deliberately ignored here — our own words are our
 * own words wherever they turn up.
 */
function isOwnReplyText(text, config) {
  const norm = normalise(text);
  if (!norm) return false;
  return ((config && config.rules) || []).some((rule) => rule.publicReply && normalise(rule.publicReply) === norm);
}

/**
 * The DM body.
 *
 * Meta allows exactly ONE private reply per comment, ever, so the text, the
 * link and any attached file have to travel together in a single message. The
 * file is a URL and not a real attachment for the same reason: an attachment
 * would have to be a second message, and there is no second message.
 *
 * @param {object} rule
 * @param {{fileUrl?: string}} [opts] resolved public URL of rule.dm.fileId
 */
function dmText(rule, opts = {}) {
  const dm = (rule && rule.dm) || {};
  const parts = [dm.text, dm.link, opts.fileUrl].filter(Boolean);
  return parts.join("\n\n").trim();
}

/** Does this rule send anything at all? A file counts, even before it resolves. */
function hasPayload(rule) {
  const dm = (rule && rule.dm) || {};
  return Boolean((dm.text && String(dm.text).trim()) || dm.link || dm.fileId);
}

const HTTP_URL = /^https?:\/\/[^\s]+$/i;

/**
 * Everything wrong with a config, as structured findings.
 *
 * Two severities, and the difference decides whether the admin panel will save:
 *
 *   error — the rule cannot work, or will hurt. A reply loop, a rule with no
 *           payload, a scoped rule with no posts chosen. Refused on save.
 *   warn  — the rule works but probably not as intended. A keyword an earlier
 *           rule already claims, a one-character keyword. Shown, not blocking.
 *
 * @returns {Array<{severity: string, ruleIndex: number|null, ruleId: string|null,
 *                  field: string|null, message: string}>}
 */
function inspect(config) {
  const found = [];
  const rules = (config && config.rules) || [];
  const add = (severity, i, field, message) =>
    found.push({
      severity,
      ruleIndex: i,
      ruleId: i == null ? null : (rules[i] && rules[i].id) || null,
      field,
      message,
    });

  if (!Array.isArray(rules) || rules.length === 0) {
    add("error", null, null, "no rules defined");
    return found;
  }

  const seenIds = new Set();
  rules.forEach((rule, i) => {
    const where = `rules[${i}]${rule.id ? ` (${rule.id})` : ""}`;

    if (!rule.id) add("error", i, "id", `${where}: missing id`);
    else if (seenIds.has(rule.id)) add("error", i, "id", `${where}: duplicate id`);
    else seenIds.add(rule.id);

    if (!Array.isArray(rule.keywords) || rule.keywords.length === 0) {
      add("error", i, "keywords", `${where}: no keywords`);
    }
    for (const keyword of rule.keywords || []) {
      if (normalise(keyword).length === 1) {
        add("warn", i, "keywords", `${where}: keyword "${keyword}" is a single character — it will fire on almost anything`);
      }
    }

    if (rule.match && !["word", "contains", "exact"].includes(rule.match)) {
      add("error", i, "match", `${where}: unknown match mode "${rule.match}"`);
    }

    if (!hasPayload(rule)) add("error", i, "dm", `${where}: dm.text, dm.link and dm.fileId are all empty — nothing to send`);

    if (rule.dm && rule.dm.link && !HTTP_URL.test(String(rule.dm.link).trim())) {
      add("error", i, "dm.link", `${where}: link "${rule.dm.link}" is not an http(s) URL`);
    }

    const body = String((rule.dm && rule.dm.text) || "");
    if (body.length > 900) {
      add("warn", i, "dm.text", `${where}: the DM text is ${body.length} characters — long messages risk being rejected, keep the pitch short and let the link do the work`);
    }

    // "Only these posts" with nothing chosen is a rule that can never fire, and
    // it looks fully configured on the page. Error, not warning.
    const scope = (rule.media && rule.media.mode) || "all";
    if (scope === "only" && mediaScope(rule).mode === "all") {
      add("error", i, "media", `${where}: set to specific posts but no posts are selected — it would never fire`);
    }
  });

  // A keyword that an earlier rule already claims, ON A POST THEY SHARE, can
  // never fire. Silent dead config is the kind of thing you only notice during
  // a campaign. Rules targeting different posts do not shadow each other, which
  // is the whole point of post targeting.
  for (let i = 0; i < rules.length; i++) {
    const earlierOverlapping = rules.slice(0, i).filter((r) => scopesOverlap(r, rules[i]));
    if (!earlierOverlapping.length) continue;
    for (const keyword of rules[i].keywords || []) {
      const earlier = match(keyword, { rules: earlierOverlapping });
      if (earlier) {
        add("warn", i, "keywords", `rules[${i}] keyword "${keyword}" is shadowed by earlier rule "${earlier.rule.id}"`);
      }
    }
  }

  // A public reply that trips one of our own keywords is an infinite loop, and it
  // is invisible on the page: "Demos sent" contains "demos", "Just sent you the
  // pricing" contains "pricing". We post it, Meta hands it back as a new comment
  // with a NEW id — so the dedupe table, which is keyed on comment id, cannot see
  // anything wrong — and we answer ourselves until Instagram rate limits the
  // account. This check is the reason that can never ship again.
  //
  // Scope matters here too, but only in one direction: the reply is posted under
  // the post the rule fired on, so the rules that can catch it are the ones that
  // also run there.
  rules.forEach((rule, i) => {
    if (!rule.publicReply) return;
    const reachable = rules.filter((r) => scopesOverlap(r, rule));
    const trips = match(rule.publicReply, { rules: reachable });
    if (trips) {
      add(
        "error",
        i,
        "publicReply",
        `rules[${i}]${rule.id ? ` (${rule.id})` : ""}: publicReply "${rule.publicReply}" contains the keyword "${trips.keyword}" ` +
          `and would retrigger rule "${trips.rule.id}" — that is a reply loop, change the wording`
      );
    }
  });

  return found;
}

/**
 * The old string-array shape, kept because server.js, the boot log and the
 * tests all read it. `inspect()` is what the admin panel uses.
 */
function validate(config) {
  return inspect(config).map((p) => p.message);
}

/** True if nothing found would stop this config from being saved. */
function isSafeToSave(config) {
  return !inspect(config).some((p) => p.severity === "error");
}

function load(file) {
  const p = file || process.env.IG_RULES_FILE || path.join(__dirname, "..", "rules.json");
  const config = JSON.parse(fs.readFileSync(p, "utf8"));
  const problems = validate(config);
  // Loud, but not fatal: a shadowed keyword should not stop the service booting
  // and drop every other rule on the floor.
  if (problems.length) console.error("RULES PROBLEMS:\n  " + problems.join("\n  "));
  return config;
}

module.exports = {
  normalise,
  match,
  dmText,
  hasPayload,
  isOwnReplyText,
  mediaScope,
  appliesToMedia,
  scopesOverlap,
  inspect,
  validate,
  isSafeToSave,
  load,
};
