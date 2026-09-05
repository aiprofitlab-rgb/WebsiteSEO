/**
 * "How did you hear about us?" — the self-reported half of attribution.
 *
 * The automatic layer (utm tags, click ids, the first/last touch apl-analytics.js
 * keeps in localStorage) can only ever see what arrived through a link. It is
 * blind to a flyer somebody was handed, a name passed on in a meeting, a
 * WhatsApp forward that stripped the query string, and to anyone who heard the
 * brand out loud and then searched for it — which GA4 files, correctly and
 * uselessly, as organic search. This one answer is what catches those.
 *
 * The page posts an ID, never a label, and the mapping back to English lives
 * here rather than in the browser for two reasons:
 *
 *   1. The Arabic checkout posts the same ids as the English one, so both
 *      languages land in one bucket in Nahid's sheet and one channel can be
 *      counted with one filter.
 *   2. A label can then be reworded on the page without splitting last month's
 *      count in two.
 *
 * The list must stay in step with HEARD in tools/v4/page_checkout.py, which is
 * what renders the options. It does not have to be complete: an id this table
 * has never seen is written through as itself rather than dropped, because an
 * answer nobody can read beats an answer nobody has.
 */

const LABELS = {
  flyer: "A printed flyer",
  google: "Google search",
  ai: "ChatGPT or another AI assistant",
  instagram: "Instagram",
  linkedin: "LinkedIn",
  whatsapp: "A WhatsApp message from Nahid",
  referral: "Someone recommended you",
  inperson: "Met in person",
  other: "Somewhere else",
};

// Every answer is written into the Notes column behind this, so the cell can be
// filtered on it and — since it is the first thing in the cell — Sheets can
// never read the buyer's own text as a formula. See the USER_ENTERED trap in
// lib/ledger.js.
const PREFIX = "Heard about us: ";

/** Newlines would break the one-line shape the Notes cell is read in. */
const clean = (v, max) =>
  String(v == null ? "" : v)
    .replace(/[\r\n\t]+/g, " ")
    .trim()
    .slice(0, max);

/**
 * One line for the ledger, or "" if they were not asked (an older cached page,
 * or a POST that never came from our form). Never throws, never returns a bare
 * prefix with nothing after it.
 */
function line(id, detail) {
  const key = clean(id, 40);
  if (!key) return "";
  const label = LABELS[key] || key;
  const extra = clean(detail, 200);
  return PREFIX + label + (extra ? ` — ${extra}` : "");
}

/**
 * The answer above whatever the buyer wrote themselves, one blank line apart.
 *
 * Two separate things share this cell and the order is deliberate: the heard-of
 * line is the one being counted, so it goes where it can be read off a column
 * without opening the row.
 */
function prepend(notes, id, detail) {
  // Their own prose keeps its line breaks — only the heard-of line has to stay
  // on one. It arrives already length-capped by str() in the route.
  const own = String(notes == null ? "" : notes).trim();
  return [line(id, detail), own].filter(Boolean).join("\n\n");
}

module.exports = { LABELS, PREFIX, line, prepend };
