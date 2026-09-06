/**
 * Plan B: what the fallback knows about the blog.
 *
 * `facts` in ai.json is Plan A — eleven hand-written lines naming the core pages.
 * It is right, it is short, and it cannot go stale loudly: when a new article
 * ships, Aiden simply never mentions it and nobody finds out. This module reads
 * the site's own index (https://aiprofitlab.io/aiden-index.json, rebuilt on every
 * website deploy) and offers the model up to three ARTICLES that look like they
 * are about what was asked.
 *
 * FOUR THINGS GOVERN EVERYTHING BELOW.
 *
 * 1. IT CAN ONLY EVER ADD. Every failure — never fetched, fetch failed, bad
 *    JSON, feature off, nothing scored, everything scrubbed — returns an empty
 *    array, and an empty array leaves the prompt byte for byte as it was before
 *    this file existed. Retrieval is not allowed to be the reason a follower
 *    goes unanswered.
 *
 * 2. IT NEVER TOUCHES THE NETWORK ON THE REPLY PATH. lookup() is synchronous, on
 *    purpose: a function that cannot await cannot fetch, so no future edit can
 *    quietly put a 700KB download in front of a reply. refresh() does the
 *    fetching, at boot and on a timer, and the cache is served stale forever
 *    rather than being allowed to fail closed.
 *
 * 3. NO MONEY AND NO STATISTICS GET IN. `headings` — where nearly every figure
 *    on the site lives, including the $126,000 in one article's subhead — is
 *    dropped at load and never enters memory at all. What survives that is run
 *    through the two scrubbers below, also at load, so neither a page carrying
 *    "OMR 50,000" (a PDPL fine, not our price) nor a page merely ABOUT what
 *    things cost is in the haystack to be found.
 *
 *    The second scrubber is not in the original design and is here because the
 *    first one was measurably not enough: "how much does it cost?" retrieved
 *    three cost articles, every one of them figure-free in its title and
 *    description and therefore untouched by a pattern match. ai.json's rule is
 *    that money is a HANDOVER and not an answer — one warm line, then Nahid on
 *    WhatsApp — and putting our own pricing guide in front of the model on that
 *    exact question is the way to lose that argument. This project has already
 *    shipped a model that quoted "around 7,000 OMR" for an OMR 800 package.
 *    Between them the two scrubbers cost 154 of the 322 articles as of
 *    2026-09-06 — 78 to a figure, 76 to the subject — and leave 168, which is
 *    more blog than a one-line Instagram reply will ever need.
 *
 * 4. IT NEVER HANDS THE MODEL A WORD THE MODEL IS BANNED FROM USING. A candidate
 *    whose title or description would trip lib/rules.js on this post is dropped,
 *    because the model parrots what it is shown, vet() then suppresses the whole
 *    reply, and from the outside that looks exactly like Aiden ignoring someone.
 *
 * The core pages are deliberately NOT retrieved. They have to be right, they
 * change rarely, and `facts` already says them better than a description tag
 * would. `types` in the config is what draws that line.
 */

const rulesLib = require("./rules");

/** Hard ceiling on the fetch. The site is behind a CDN; if it is slow it is broken. */
const FETCH_TIMEOUT_MS = Number(process.env.IG_INDEX_TIMEOUT_MS || 8_000);

/** Used only when a tick cannot read a number out of the config at all. */
const DEFAULT_REFRESH_MINUTES = 30;

/** Below this there is no room left for a description worth reading. */
const MIN_DESC = 40;

let cache = null; // { site, generated, fetchedAt, pages: [...], seen, dropped }
let inflight = null; // a boot fetch and a timer tick must not both download 700KB
let timer = null;
let scheduled = false;

/* ---------------------------------------------------------------------------
 * Config
 * ------------------------------------------------------------------------- */

/**
 * The `index` block, defaulted. aiConfig.DEFAULTS is the real source of these —
 * this only exists so lookup() and refresh() survive being handed a config
 * object that predates the feature, which is exactly what a live
 * /var/lib/ig-automation/ai.json is until someone edits it.
 */
function indexConfig(config) {
  const c = (config && config.index) || {};
  return {
    enabled: Boolean(c.enabled),
    url: String(c.url || ""),
    refreshMinutes: Number(c.refreshMinutes) || DEFAULT_REFRESH_MINUTES,
    maxPages: Number.isFinite(Number(c.maxPages)) ? Number(c.maxPages) : 3,
    maxChars: Number.isFinite(Number(c.maxChars)) ? Number(c.maxChars) : 1000,
    types: Array.isArray(c.types) && c.types.length ? c.types.map(String) : ["article"],
    // A word from a title scores 2, a word from the description or the keyword
    // list scores 1. So the default of 2 reads as: one title word, or two words
    // anywhere. Raise it to be stricter; there is no value that makes retrieval
    // unsafe, only values that make it useless.
    minScore: Number.isFinite(Number(c.minScore)) ? Number(c.minScore) : 2,
  };
}

/* ---------------------------------------------------------------------------
 * Tokens
 * ------------------------------------------------------------------------- */

/**
 * Function words, in both languages the account speaks.
 *
 * Without this the scorer is a popularity contest: the index's `keywords` are
 * simply each page's most frequent terms, so "على" and "tool" are in half of
 * them, and "what do you build?" would score two points against three hundred
 * articles. Only genuinely empty words belong here — every word removed is
 * signal the scorer no longer has, and there is very little of it to start with
 * in a six-word Instagram comment.
 */
const STOPWORDS = [
  // English
  "the", "and", "you", "your", "yours", "our", "ours", "for", "are", "was", "were", "with", "this",
  "that", "these", "those", "what", "how", "why", "who", "whom", "which", "when", "where", "can",
  "could", "would", "should", "will", "shall", "does", "did", "done", "has", "have", "had", "not",
  "but", "its", "from", "into", "than", "then", "there", "here", "any", "all", "some", "each",
  "get", "got", "one", "two", "they", "them", "their", "about", "just", "like", "more", "most",
  "very", "much", "also", "too", "only", "own", "same", "such", "yes", "please", "thanks", "thank",
  "hello", "hey", "sir", "guys", "www", "com", "http", "https",
  // Arabic (written unfolded; the same normalise() the matcher uses is applied below)
  "على", "في", "من", "إلى", "عن", "مع", "هذا", "هذه", "ذلك", "التي", "الذي", "التى", "كيف", "ماذا",
  "لماذا", "هل", "كل", "بعد", "قبل", "بين", "عند", "أو", "ثم", "كان", "يكون", "لكن", "حتى", "أيضا",
  "نحن", "أنا", "أنت", "هو", "هي", "لدي", "عندي", "شكرا", "مرحبا", "السلام", "عليكم", "ممكن", "يا",
];

/**
 * Strip the Arabic definite article off the front of a token.
 *
 * The index's Arabic keyword lists carry it — "الذكاء", "البيانات" — because
 * they are counted straight off the page. A person types "ذكاء". Folding it off
 * both sides is the only way the two ever meet. Same trick lib/rules.js plays in
 * wordRe(), for the same reason. The 3-character lookahead stops it eating words
 * that merely start with those letters ("الى", "ألف").
 */
const fold = (token) =>
  token
    .replace(/^و?ال(?=[؀-ۿ]{3,})/, "")
    // And the English plural off the back. Crude on purpose — "process" becomes
    // "proces" — which does not matter in the slightest, because BOTH sides of
    // the comparison go through this function. It cannot invent a match; all it
    // can do is stop "clinics" and "clinic" being two different words, which on
    // a page of six-word questions is most of the recall there is to win.
    .replace(/(?<=[a-z]{3})s$/, "");

const STOP = new Set(STOPWORDS.map((w) => fold(rulesLib.normalise(w))));

/**
 * A message or a page reduced to the words worth matching on.
 *
 * rulesLib.normalise() is reused rather than reimplemented: it already does NFKC,
 * the Arabic letter folding (أ إ آ -> ا, ى -> ي), diacritic and tatweel removal
 * and lowercasing, and the retrieval side agreeing with the matcher on what a
 * word looks like is worth more than anything a bespoke tokeniser could add.
 */
function tokenise(text) {
  const out = new Set();
  for (const raw of rulesLib.normalise(text).split(/[^\p{L}\p{N}]+/u)) {
    const token = fold(raw);
    // Two-letter words carry no signal in either language and match everywhere.
    if (token.length < 3) continue;
    if (STOP.has(token)) continue;
    out.add(token);
  }
  return out;
}


/* ---------------------------------------------------------------------------
 * The money and statistics scrubber
 * ------------------------------------------------------------------------- */

/**
 * Every way a figure is written on this site, in both languages.
 *
 * Tested against the RAW title and description rather than the normalised form,
 * so the alef variants are spelled out in the classes below instead of being
 * reasoned about second-hand. Arabic-Indic digits (٥٠٠) and the Arabic thousands
 * comma (2،000) both appear in real entries, so both are here.
 *
 * This is deliberately blunt. A false positive costs one article out of 322; a
 * false negative puts a number in front of a model that has already, once, told
 * a customer the wrong price.
 */
const DIGIT = "[0-9\\u0660-\\u0669\\u06F0-\\u06F9]";
const AMOUNT = `${DIGIT}(?:[.,،٬٫]?${DIGIT})*`;
const SCALE = "(?:k|m|bn|thousand|million|billion|[أا]لف|[آا]لاف|مليون|مليار)";
const CURRENCY =
  "(?:OMR|USD|AED|SAR|QAR|KWD|BHD|EGP|EUR|GBP|\\$|€|£|ر\\.?\\s?ع\\.?|ريالا?|درهما?|دولارا?|يورو|جنيه)";

const MONEY = new RegExp(`(?:${CURRENCY}\\s*${AMOUNT})|(?:${AMOUNT}\\s*${SCALE}?\\s*${CURRENCY})`, "iu");
const PERCENT = new RegExp(`(?:${AMOUNT}\\s*[%٪])|(?:[%٪]\\s*${AMOUNT})|(?:${AMOUNT}\\s*(?:percent|بالما?ئة|في الما?ئة))`, "iu");
/** "10x ROI", "3 أضعاف" — a multiplier is a statistic wearing a different hat. */
const MULTIPLIER = new RegExp(`(?<![\\p{L}\\p{N}])${AMOUNT}\\s*(?:x|×|[أا]ضعاف|ضعف)(?![\\p{L}\\p{N}])`, "iu");
/** A thousands separator is never a date and never a version — it is always a claim. */
const BIG_NUMBER = new RegExp(`${DIGIT}[.,،]${DIGIT}{3}(?![\\p{L}\\p{N}])`, "u");

function carriesAFigure(text) {
  const s = String(text || "");
  return MONEY.test(s) || PERCENT.test(s) || MULTIPLIER.test(s) || BIG_NUMBER.test(s);
}

/**
 * Money as a SUBJECT, with or without a number attached.
 *
 * "How Much Does AI Automation Cost for B2B Companies in the GCC?" has no figure
 * anywhere in its title or description, sails through carriesAFigure(), and is
 * the single worst thing that could be sitting in the prompt when somebody asks
 * what we charge. The rule in ai.json is that the handover IS the answer; a
 * model holding our own pricing guide will link it instead, and be pleased with
 * itself for staying off the number.
 *
 * Blunter than the figure scrubber and deliberately so — it drops articles that
 * only mention cost in passing. Losing an article we could have linked costs a
 * click. Losing control of the money conversation costs the deal, and this
 * account has an eleven-line rule about it.
 */
const MONEY_TOPIC =
  /(?<![\p{L}])(cost|costs|costing|price|prices|pricing|priced|fee|fees|budget|budgets|cheap|cheaper|affordable|expensive|discount|discounts|roi|invoice|invoices|salary|salaries|payroll)(?![\p{L}])|تكلفة|تكاليف|كلفة|سعر|اسعار|أسعار|تسعير|ميزانية|رخيص|خصم|فاتورة|راتب|عائد الاستثمار/iu;

const talksAboutMoney = (text) => MONEY_TOPIC.test(String(text || ""));

/**
 * The one gate everything passes through on the way into memory.
 * @returns {string} "" when the entry is safe, otherwise why it was dropped.
 */
function unsafeToInject(text) {
  if (carriesAFigure(text)) return "figure";
  if (talksAboutMoney(text)) return "money";
  return "";
}

/* ---------------------------------------------------------------------------
 * Loading
 * ------------------------------------------------------------------------- */

/** Absolute, because a bare "/blog/en/..." in a prompt is a link nobody can tap. */
function absolute(site, url) {
  const u = String(url || "");
  if (/^https?:\/\//i.test(u)) return u;
  return `${String(site || "").replace(/\/+$/, "")}${u.startsWith("/") ? "" : "/"}${u}`;
}

function originOf(url) {
  try {
    return new URL(url).origin;
  } catch {
    return "";
  }
}

/**
 * Turn a fetched index into the slim thing lookup() reads.
 *
 * Exported because it is also how the tests load a fixture — there is no network
 * anywhere in this module's test file, and there should not be.
 *
 * Everything expensive happens here, once per refresh, rather than once per
 * reply: the tokenising, and both scrubs. Note what does NOT survive — `headings`
 * is read and thrown away, and a page whose title or description carries a figure
 * or is about money is not stored at all. A page that is not in memory cannot be
 * retrieved by a future edit that forgets why.
 */
function load(payload, { url = "" } = {}) {
  if (!payload || !Array.isArray(payload.pages)) {
    console.error("!! site index is not the shape we expect (no `pages` array) — keeping the last good copy");
    return { ok: false, why: "bad shape" };
  }

  const site = String(payload.site || originOf(url) || "").trim();
  const pages = [];
  const dropped = { figure: 0, money: 0 };

  for (const p of payload.pages) {
    if (!p || !p.url || !p.title) continue;

    const title = String(p.title).trim();
    const desc = String(p.desc || "").trim();
    const href = absolute(site, p.url);

    // The url is scrubbed too: a slug like "...-receptionist-2000-worth-it" is
    // injected text like any other, and a model will read a number out of it.
    const why = unsafeToInject(`${title} ${desc} ${href}`);
    if (why) {
      dropped[why]++;
      continue;
    }

    pages.push({
      url: href,
      lang: String(p.lang || "en"),
      type: String(p.type || ""),
      title,
      desc,
      // Scored across title + desc + keywords. `headings` is deliberately not
      // among them and is not stored — see the header.
      tokens: tokenise(`${title} ${desc} ${(p.keywords || []).join(" ")}`),
      titleTokens: tokenise(title),
    });
  }

  cache = {
    site,
    generated: String(payload.generated || ""),
    fetchedAt: Date.now(),
    seen: payload.pages.length,
    dropped,
    pages,
  };
  return { ok: true, pages: pages.length, seen: payload.pages.length, dropped };
}

/**
 * Fetch the index and swap it in. Never throws, never leaves a worse cache than
 * it found.
 */
async function refresh(config, { fetchImpl = fetch } = {}) {
  const cfg = indexConfig(config);
  if (!cfg.enabled || !cfg.url) return { ok: false, why: "disabled" };

  // A boot fetch and the first timer tick can overlap on a slow box. One
  // download, two callers.
  if (inflight) return inflight;

  inflight = (async () => {
    let payload;
    try {
      const res = await fetchImpl(cfg.url, {
        headers: { accept: "application/json" },
        signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      payload = await res.json();
    } catch (err) {
      // One line, and it says what the consequence is — "failed" on its own
      // would leave someone wondering whether replies had stopped.
      console.error(
        `!! site index refresh failed (${cfg.url}): ${err && err.message}` +
          (cache
            ? ` — still serving the ${cache.pages.length}-page copy from ${cache.generated || "an earlier fetch"}`
            : " — retrieval stays off until a fetch succeeds; the prompt is unchanged")
      );
      return { ok: false, why: err && err.message };
    }
    return load(payload, { url: cfg.url });
  })();

  try {
    return await inflight;
  } finally {
    inflight = null;
  }
}

/**
 * Refresh now, then every refreshMinutes, forever.
 *
 * The config is read on every tick rather than captured once, so both
 * `refreshMinutes` and `enabled` are live: turning the feature on in
 * /var/lib/ig-automation/ai.json starts it working within one interval, with no
 * restart, exactly like every other setting in this service.
 *
 * @returns {Promise} the first refresh, so boot can log what happened.
 */
function schedule(getConfig, { fetchImpl } = {}) {
  if (scheduled) return Promise.resolve({ ok: false, why: "already scheduled" });
  scheduled = true;

  const tick = async () => {
    let minutes = DEFAULT_REFRESH_MINUTES;
    try {
      const config = getConfig();
      minutes = indexConfig(config).refreshMinutes;
      return await refresh(config, { fetchImpl });
    } catch (err) {
      console.error("!! site index tick failed:", err && err.message);
      return { ok: false, why: err && err.message };
    } finally {
      // unref'd, like the sweep timer: this must never be the reason the process
      // refuses to exit.
      timer = setTimeout(tick, Math.max(1, minutes) * 60_000);
      timer.unref();
    }
  };

  return tick();
}

/** Tests and shutdown. Leaves the cache alone — only the clock stops. */
function stop() {
  if (timer) clearTimeout(timer);
  timer = null;
  scheduled = false;
}

/** Tests only: back to the state a fresh process starts in. */
function reset() {
  stop();
  cache = null;
  inflight = null;
}

/* ---------------------------------------------------------------------------
 * Retrieval
 * ------------------------------------------------------------------------- */

/**
 * Would this entry's own words trip the matcher on this post?
 *
 * Not "does it contain a forbidden string" — the real matcher, with the same
 * media id vet() will use, so the prompt and the post-check cannot drift apart.
 * Showing the model a title containing a live keyword is how a perfectly good
 * reply gets silently suppressed on its way out.
 */
function collides(page, rulesConfig, mediaId) {
  if (!rulesConfig) return false;
  return Boolean(rulesLib.match(`${page.title} ${page.desc}`, rulesConfig, { mediaId: String(mediaId == null ? "" : mediaId) }));
}

/** Cut to fit, at a word boundary, counting the ellipsis rather than adding it after. */
function clip(text, max) {
  if (text.length <= max) return text;
  const cut = text.slice(0, max - 1);
  const space = cut.lastIndexOf(" ");
  return `${(space > max * 0.5 ? cut.slice(0, space) : cut).trimEnd()}…`;
}

function render(page, budget) {
  const head = `- ${page.title} — ${page.url}`;
  if (head.length > budget) return "";
  const room = budget - head.length - 3; // " — "
  if (!page.desc || room < MIN_DESC) return head;
  return `${head} — ${clip(page.desc, room)}`;
}

/**
 * Up to maxPages lines of reference material for this message, or nothing.
 *
 * SYNCHRONOUS AND CACHE-ONLY — see the header. Silent, too: this runs once per
 * reply, so a log line here would be a log line per comment forever.
 *
 * @param {string} text the incoming comment or DM
 * @param {{config: object, lang: string, rulesConfig: object, mediaId: string}} opts
 * @returns {string[]} lines to inject, empty when there is nothing good enough
 */
function lookup(text, { config, lang, rulesConfig, mediaId } = {}) {
  const cfg = indexConfig(config);
  if (!cfg.enabled) return [];
  if (!cache || !cache.pages.length) return [];
  if (cfg.maxPages < 1 || cfg.maxChars < 1) return [];

  const query = tokenise(text);
  if (!query.size) return [];

  const types = new Set(cfg.types);
  // Anything that is not Arabic is answered in English, which is the same call
  // languageInstruction() makes — the caller passes its answer in rather than
  // this file guessing again.
  const wanted = lang === "ar" ? "ar" : "en";

  const scored = [];
  for (const page of cache.pages) {
    if (!types.has(page.type)) continue;
    if (page.lang !== wanted) continue;

    let score = 0;
    let titleHits = 0;
    for (const token of query) {
      if (!page.tokens.has(token)) continue;
      // A word in a sixty-character title is not a coincidence; the same word
      // somewhere in a keyword list very often is. So a title hit is worth two,
      // which at the default minScore of 2 makes the rule legible: ONE word from
      // a title, or TWO words from anywhere.
      //
      // That second half matters more than it looks. Half the questions this
      // account gets are one strong noun and nothing else — "what's an ai
      // receptionist?" is three stopwords, a two-letter word this tokeniser
      // drops, and the only term that means anything.
      if (page.titleTokens.has(token)) {
        score += 2;
        titleHits++;
      } else {
        score += 1;
      }
    }
    // The threshold is the whole defence against a weak match. Instagram gives
    // no page context and a comment is six words, so a single passing mention is
    // noise — and injecting noise is worse than injecting nothing.
    if (score < cfg.minScore) continue;
    scored.push({ page, score, titleHits });
  }
  if (!scored.length) return [];

  // Title hits break the tie because a word in a 60-character title means more
  // than the same word buried in a keyword list. The url is the last tiebreak
  // purely so the same question always produces the same block.
  scored.sort((a, b) => b.score - a.score || b.titleHits - a.titleHits || (a.page.url < b.page.url ? -1 : 1));

  const lines = [];
  let used = 0;
  for (const { page } of scored) {
    if (lines.length >= cfg.maxPages) break;
    if (collides(page, rulesConfig, mediaId)) continue;
    // The newline systemPrompt() will join these with is paid for out of the
    // same budget, so the cap holds on the block as the model actually sees it.
    const newline = lines.length ? 1 : 0;
    const line = render(page, cfg.maxChars - used - newline);
    // Out of room. The list is in score order, so what is left is worth less
    // than what we already have — stopping beats squeezing in a weaker line.
    if (!line) break;
    lines.push(line);
    used += newline + line.length;
  }
  return lines;
}

/** For /health. The two questions worth asking are "how old" and "how many". */
function stats() {
  if (!cache) return { loaded: false, pages: 0 };
  return {
    loaded: true,
    pages: cache.pages.length,
    seen: cache.seen,
    // Two numbers rather than one, because they mean different things: a jump in
    // `figure` means the blog started publishing numbers, a jump in `money`
    // means it started publishing about price.
    dropped: cache.dropped,
    generated: cache.generated || null,
    ageMinutes: Math.round((Date.now() - cache.fetchedAt) / 60_000),
  };
}

module.exports = {
  lookup,
  refresh,
  schedule,
  load,
  stats,
  stop,
  reset,
  // Exported for the tests and for anyone auditing the scrubber, which is the
  // part of this file most worth reading twice.
  carriesAFigure,
  talksAboutMoney,
  unsafeToInject,
  tokenise,
  indexConfig,
};
