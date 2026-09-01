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
 * the generic one in rules.json, or the generic one will swallow it.
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

/**
 * @returns {{rule: object, keyword: string}|null} first matching rule, or null
 */
function match(text, config) {
  const norm = normalise(text);
  if (!norm) return null;

  for (const rule of (config && config.rules) || []) {
    if (rule.enabled === false) continue;
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
 * comments.
 */
function isOwnReplyText(text, config) {
  const norm = normalise(text);
  if (!norm) return false;
  return ((config && config.rules) || []).some((rule) => rule.publicReply && normalise(rule.publicReply) === norm);
}

/** The DM body: the payload text with the link appended, since we only get one shot. */
function dmText(rule) {
  const dm = (rule && rule.dm) || {};
  const parts = [dm.text, dm.link].filter(Boolean);
  return parts.join("\n\n").trim();
}

function validate(config) {
  const problems = [];
  const rules = (config && config.rules) || [];
  if (!Array.isArray(rules) || rules.length === 0) problems.push("no rules defined");

  const seenIds = new Set();
  rules.forEach((rule, i) => {
    const where = `rules[${i}]${rule.id ? ` (${rule.id})` : ""}`;
    if (!rule.id) problems.push(`${where}: missing id`);
    else if (seenIds.has(rule.id)) problems.push(`${where}: duplicate id`);
    else seenIds.add(rule.id);

    if (!Array.isArray(rule.keywords) || rule.keywords.length === 0) problems.push(`${where}: no keywords`);
    if (rule.match && !["word", "contains", "exact"].includes(rule.match)) {
      problems.push(`${where}: unknown match mode "${rule.match}"`);
    }
    if (!dmText(rule)) problems.push(`${where}: dm.text and dm.link are both empty — nothing to send`);
  });

  // A keyword that an earlier rule already claims can never fire. Silent dead
  // config is the kind of thing you only notice during a campaign.
  for (let i = 0; i < rules.length; i++) {
    for (const keyword of rules[i].keywords || []) {
      const earlier = match(keyword, { rules: rules.slice(0, i) });
      if (earlier) {
        problems.push(`rules[${i}] keyword "${keyword}" is shadowed by earlier rule "${earlier.rule.id}"`);
      }
    }
  }
  // A public reply that trips one of our own keywords is an infinite loop, and it
  // is invisible on the page: "Demos sent" contains "demos", "Just sent you the
  // pricing" contains "pricing". We post it, Meta hands it back as a new comment
  // with a NEW id — so the dedupe table, which is keyed on comment id, cannot see
  // anything wrong — and we answer ourselves until Instagram rate limits the
  // account. This check is the reason that can never ship again.
  rules.forEach((rule, i) => {
    if (!rule.publicReply) return;
    const trips = match(rule.publicReply, config);
    if (trips) {
      problems.push(
        `rules[${i}]${rule.id ? ` (${rule.id})` : ""}: publicReply "${rule.publicReply}" contains the keyword "${trips.keyword}" ` +
          `and would retrigger rule "${trips.rule.id}" — that is a reply loop, change the wording`
      );
    }
  });

  return problems;
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

module.exports = { normalise, match, dmText, isOwnReplyText, validate, load };
