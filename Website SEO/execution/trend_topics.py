#!/usr/bin/env python3
"""
Trend-backed article topics: the searches people in Oman really make, turned into
titles for the daily publisher's queue (directives/article_queue.md).

    python3 execution/trend_topics.py              # research, then top the queue up to 7 Pending topics
    python3 execution/trend_topics.py --dry-run    # research and report only; the queue is untouched
    python3 execution/trend_topics.py --target 10  # top up to 10 Pending topics instead

It costs nothing. The demand data comes from two free Google sources that need no key:
  - Google Trends related queries (top and rising, last 12 months) for each seed
    keyword: the same JSON the Trends Explore page loads. Oman first; a seed with too
    little Oman data is asked again for the UAE, and the report says so.
  - Google autocomplete for each seed (Oman region): what people start typing.
Then ONE Gemini call (free tier) keeps the searches a business owner would make and
writes a title for each. Code, not the model, then checks that every title traces back
to a search that was really collected and carries that search's words, and runs the
publisher's own title rules (banned words, specificity, the skill's 65% overlap check).

daily_publish.py calls top_up() when fewer than 2 topics are Pending, and only asks the
model to invent topics when this finds nothing. The evidence behind every title is
written to directives/trend_report.md.

Trends' JSON is unofficial. Google rate-limits it (HTTP 429), hardest from cloud IPs such
as GitHub's runners. When that happens the run carries on with autocomplete alone, and
the report says Trends was blocked.
"""

import argparse
import http.cookiejar
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                                   # .../Website SEO
REPORT_FILE = ROOT / "directives" / "trend_report.md"
TMP = ROOT / ".tmp" / "trend_topics"

# What AI Profit Lab sells, phrased the way an owner searches for it. Edit freely: each
# seed costs about 2 Trends requests and 4 autocomplete requests.
SEEDS = [
    ("ai for business", "en"),
    ("chatbot", "en"),
    ("whatsapp business", "en"),
    ("ai agent", "en"),
    ("business automation", "en"),
    ("website design", "en"),
    ("e invoicing oman", "en"),
    ("fawtara", "en"),                   # Oman's e-invoicing programme (Oman Tax Authority)
    ("inventory management", "en"),
    ("crm", "en"),
    ("ذكاء اصطناعي", "ar"),
    ("واتساب بزنس", "ar"),
    ("تصميم موقع", "ar"),
    ("الفاتورة الإلكترونية", "ar"),
    ("متجر إلكتروني", "ar"),
]
GEO, FALLBACK_GEO = "OM", "AE"
TZ_OFFSET = "-240"            # Muscat is UTC+4; Trends wants minutes WEST of UTC
MIN_RELATED = 5               # fewer related queries than this in Oman -> ask the UAE as well
FALLBACK_WEIGHT = 0.5         # a UAE signal counts half: the reader is in Oman
TITLE_MAX = 80                # hard limit; the model is asked for 65 or less
TARGET_PENDING = 7
MAX_CANDIDATES = 160          # the strongest searches sent to the model
AC_VARIANTS = {"en": ["{s} ", "{s} for ", "best {s} ", "{s} oman"],
               "ar": ["{s} ", "افضل {s}", "{s} في عمان", "{s} لل"]}

# Navigational and off-topic searches nobody writes a business article for.
JUNK = re.compile(r"\b(log ?in|sign ?in|sign ?up|download|apk|near me|for pc|for windows|for mac|"
                  r"web whatsapp|update|icon|png|wallpaper|movie|movies|anime|games?|crack|mod|"
                  r"porn|sex|nsfw|xxx)\b|تحميل|تنزيل|تسجيل الدخول|تسجيل دخول", re.I)
# Latin or Arabic only: Trends' related queries carry spam in other scripts (Thai casino terms).
# Searches about another country's market or authority (UAE e-invoicing, Dubai web design)
# don't serve an Omani reader, even when the UAE data is what surfaced them.
FOREIGN = re.compile(r"\b(uae|dubai|abu dhabi|sharjah|ajman|saudi|ksa|riyadh|jeddah|qatar|doha|kuwait|"
                     r"bahrain|jordan|egypt|india|pakistan|uk|usa|fta|zatca)\b|الامارات|الإمارات|دبي|"
                     r"السعودية|الرياض|جدة|قطر|الكويت|البحرين|الاردن|الأردن|مصر", re.I)
# The brand's voice rules, on top of the skill's banned words (daily_publish.SLOP).
TITLE_AVOID = ["transform", "revolution", "cutting-edge", "cutting edge", "disrupt", "enterprise-grade",
               "leverage", "10x", "ultimate", "complete guide", "high-converting", "synergy", "growth hack"]
# Words every title here shares. Two titles whose OTHER words mostly match are one article
# ("Website Design Oman: Cost Guide" vs "Website Design for Oman Businesses"), which the
# skill's 65% similarity measure misses because the filler differs.
FILLER = set("guide guides oman omani muscat sohar salalah gcc gulf sme smes business businesses small mid "
             "sized company companies team teams practical simple setup cost costs best top owners owner "
             "managers manager service trade retail ai".split())
SAME_TOPIC = 0.5
ALLOWED = re.compile(r"[A-Za-z0-9؀-ۿ\s'’&.,+/?#%:()\-]+")
AR_CHARS = re.compile(r"[؀-ۿ]")
AR_STOP = set("في من على الى إلى عن مع او أو ما ماذا كيف هل".split())


def _ar_norm(s):
    s = re.sub(r"[ً-ْـ]", "", s)          # harakat and tatweel
    return re.sub("[أإآ]", "ا", s).replace("ة", "ه").replace("ى", "ي")


def _norm(q):
    return re.sub(r"\s+", " ", _ar_norm((q or "").lower())).strip()


# ======================================================================
# Demand: Google Trends + autocomplete
# ======================================================================
class Trends:
    """Google Trends' Explore JSON. Stops asking for the rest of the run after repeated 429s."""
    HOME = "https://trends.google.com/trends/explore?geo=OM"
    API = "https://trends.google.com/trends/api"

    def __init__(self, dp):
        self.dp = dp
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
            urllib.request.HTTPSHandler(context=dp.SSL))
        self.opener.addheaders = [("User-Agent", dp.UA), ("Accept-Language", "en-US,en;q=0.9")]
        self.blocked = None
        try:
            self.opener.open(self.HOME, timeout=30).read()
        except Exception:
            pass                  # this page usually answers 429, but it still sets the NID cookie

    def _json(self, url):
        last = None
        for wait in (0, 20, 60):
            if wait:
                time.sleep(wait)
            try:
                with self.opener.open(url, timeout=30) as r:
                    body = r.read().decode("utf-8", "replace")
                return json.loads(body[body.find("{"):])      # strips the )]}' guard prefix
            except urllib.error.HTTPError as e:
                last = f"HTTP {e.code}"
                if e.code != 429:
                    return None   # this request is bad; the next seed may be fine
            except (urllib.error.URLError, TimeoutError, ConnectionError, ValueError) as e:
                last = str(e)
        self.blocked = last
        return None

    def related(self, kw, geo):
        """[{query, kind: top|rising, value, label}] for one keyword in one country."""
        if self.blocked:
            return []
        q = {"hl": "en-US", "tz": TZ_OFFSET}
        req = {"comparisonItem": [{"keyword": kw, "geo": geo, "time": "today 12-m"}],
               "category": 0, "property": ""}
        ex = self._json(f"{self.API}/explore?" + urllib.parse.urlencode({**q, "req": json.dumps(req)}))
        w = next((w for w in (ex or {}).get("widgets", []) if w.get("id") == "RELATED_QUERIES"), None)
        if not w:
            return []
        time.sleep(1.5)
        d = self._json(f"{self.API}/widgetdata/relatedsearches?" + urllib.parse.urlencode(
            {**q, "req": json.dumps(w["request"]), "token": w["token"]}))
        out = []
        # rankedList[0] is "Top", rankedList[1] is "Rising" (what pytrends reads too)
        for i, lst in enumerate((d or {}).get("default", {}).get("rankedList", [])[:2]):
            for k in lst.get("rankedKeyword", []):
                out.append({"query": k.get("query", ""), "kind": "top" if i == 0 else "rising",
                            "value": k.get("value", 0) or 0, "label": k.get("formattedValue", "")})
        return out


def autocomplete(dp, q, lang):
    url = "https://suggestqueries.google.com/complete/search?" + urllib.parse.urlencode(
        {"client": "firefox", "hl": lang, "gl": "om", "q": q})
    req = urllib.request.Request(url, headers={"User-Agent": dp.UA})
    try:
        with urllib.request.urlopen(req, timeout=20, context=dp.SSL) as r:
            return json.loads(r.read().decode("utf-8", "replace"))[1]
    except (urllib.error.URLError, TimeoutError, ConnectionError, ValueError, IndexError):
        return []


def collect(dp, seeds=SEEDS):
    """Every search found for the seeds, keyed by normalised text, with its evidence."""
    cands = {}
    stats = {"seeds": len(seeds), "trends": 0, "fallback": [], "autocomplete": 0, "blocked": None}

    def add(q, evidence, weight):
        q = " ".join((q or "").split())
        k = _norm(q)
        if not k or JUNK.search(q) or FOREIGN.search(q) or not ALLOWED.fullmatch(q):
            return
        c = cands.setdefault(k, {"query": q, "lang": "ar" if AR_CHARS.search(q) else "en",
                                 "evidence": [], "score": 0.0})
        if evidence not in c["evidence"]:
            c["evidence"].append(evidence)
            c["score"] += weight

    tr = Trends(dp)
    for kw, lang in seeds:
        dp.log(f"  searching: {kw}")
        for geo in (GEO, FALLBACK_GEO):
            rel = tr.related(kw, geo)
            k = 1 if geo == GEO else FALLBACK_WEIGHT
            for r in rel:
                if r["kind"] == "rising":
                    weight = 3 if r["label"] == "Breakout" else 2 if r["value"] >= 100 else 1
                    add(r["query"], f"Trends {geo}: rising {r['label']}", weight * k)
                else:
                    add(r["query"], f"Trends {geo}: top {r['label']}/100", (1 + r["value"] / 100) * k)
            stats["trends"] += len(rel)
            if len(rel) >= MIN_RELATED or tr.blocked or geo == FALLBACK_GEO:
                break
            stats["fallback"].append(kw)
            time.sleep(random.uniform(2, 4))
        for v in AC_VARIANTS[lang]:
            got = autocomplete(dp, v.format(s=kw), lang)
            stats["autocomplete"] += len(got)
            for s in got:
                add(s, "Autocomplete (Oman)", 0.5)
            time.sleep(0.4)
        time.sleep(random.uniform(3, 6))      # Trends throttles fast callers
    stats["blocked"] = tr.blocked
    if tr.blocked:
        dp.log(f"  ! Google Trends stopped answering ({tr.blocked}); the rest is autocomplete only")
    return cands, stats


# ======================================================================
# Titles: one Gemini call, then code checks every one
# ======================================================================
PICK_SCHEMA = {"type": "OBJECT", "properties": {"topics": {"type": "ARRAY", "items": {
    "type": "OBJECT", "properties": {"query": {"type": "STRING"}, "cluster": {"type": "STRING"},
                                     "en_title": {"type": "STRING"}, "ar_title": {"type": "STRING"},
                                     "intent": {"type": "STRING"}},
    "required": ["query", "cluster", "en_title", "ar_title", "intent"]}}}, "required": ["topics"]}


def _words(s, stop):
    return [w for w in re.findall(r"[a-z0-9]+|[ء-ي]+", _norm(s)) if w not in stop]


def grounded(query, title, stop):
    """Does the title carry at least two thirds of the search's own words? A longer word may sit
    inside a title word, so plurals and Arabic affixes count (مجاني in المجانية)."""
    q, t = _words(query, stop), set(_words(title, stop))
    if not q:
        return False
    hit = sum(any(w == x or (len(w) > 3 and w in x) for x in t) for w in q)
    return hit * 3 >= len(q) * 2


def _topic_words(dp, title):
    return {w for w in dp._tok(title) if w not in FILLER and not w.isdigit()}


def same_topic(dp, a, b):
    ta, tb = _topic_words(dp, a), _topic_words(dp, b)
    return len(ta & tb) / len(ta | tb) if ta | tb else 0


def pick(dp, cands, corp, rows, n):
    """(valid picks in the model's order, rejected picks with the reason)."""
    res = dp.gemini_json(dp.system_prompt(), pick_prompt(dp, cands, corp, rows, n), PICK_SCHEMA,
                         "trend topics")
    return validate_picks(dp, res.get("topics", []), cands, corp, rows)


def pick_prompt(dp, cands, corp, rows, n):
    """The title-writing task. Sent to Gemini's API here, or handed to the Antigravity agent
    by agent_publish.py; either way validate_picks() checks the answer."""
    clusters = sorted({r["cluster"] for r in rows if r["cluster"]})
    best = sorted(cands.values(), key=lambda c: -c["score"])[:MAX_CANDIDATES]
    lines = "\n".join(f"- {c['query']}  [{'; '.join(c['evidence'])}]" for c in best)
    published = "\n".join(f"- {t}" for t in corp["en"].values())
    prompt = (
        f"These are real Google searches from Oman (from the UAE where Oman's data was too thin; those "
        f"carry 'Trends AE'), collected "
        f"today from Google Trends related queries and Google autocomplete. Each line is one search, then "
        f"the evidence for it.\n\n{lines}\n\n"
        f"Pick the {n * 2} searches most likely typed by this blog's reader: the owner or manager of a "
        f"small or mid-sized trading, distribution or service business in Oman or the GCC, trying to "
        f"solve a business problem (sales inquiries, customer messages on WhatsApp, invoices and "
        f"e-invoicing, stock, their website, follow-up, reporting, using AI tools at work). Reject "
        f"consumer AI toys and image or video generators, homework tools (humanizers, AI detectors), app "
        f"logins and downloads, news and celebrities, searches for another company's product with no "
        f"business how-to angle, searches for another company's prices (they change, and every number "
        f"in an article needs a live source), and anything the blog could not answer honestly. One "
        f"search per topic: the same need in English and Arabic is one pick.\n\n"
        f"For each pick, write the title of an article that answers that search:\n"
        f"- query: copy the search exactly as it appears in the list above.\n"
        f"- en_title: must contain the search's words (an Arabic search: its natural English wording), "
        f"and follow criterion 1 of the skill. 65 characters or fewer, as close to the search as reads "
        f"naturally. Plain words, the way an owner would say it over coffee: no 'complete' or 'ultimate' "
        f"guides, no 'high-converting', 'enterprise', 'transform' or 'leverage'.\n"
        f"- ar_title: natural Arabic for Gulf readers. For an Arabic search it must contain the search's "
        f"words.\n"
        f"- No prices, percentages or statistics in either title: nothing in a title may need a source. "
        f"A year is fine.\n"
        f"- cluster: one of these, exactly: {'; '.join(clusters)}\n"
        f"- intent: one line on who types this and what they need from the article.\n"
        f"Order the list best first: clearest business need first, then strongest demand. Oman evidence "
        f"(Trends OM, autocomplete) outranks UAE evidence. Oman-specific angles beat generic GCC ones. "
        f"Do not overlap these published articles:\n{published}\n")
    return prompt


def validate_picks(dp, topics, cands, corp, rows):
    """Code, not the model, decides: every title must trace back to a collected search."""
    clusters = sorted({r["cluster"] for r in rows if r["cluster"]})
    taken = list(corp["en"].values()) + [r["en_title"] for r in rows]
    used, picks, rejected = set(), [], []
    for t in topics:
        k = _norm(t.get("query"))
        c = cands.get(k)
        en, ar, cl = dp._plain(t.get("en_title")), dp._plain(t.get("ar_title")), dp._plain(t.get("cluster"))
        score, like = max(((dp.similarity(en, x), x) for x in taken), default=(0, ""))
        twin = next((x for x in taken if same_topic(dp, en, x) >= SAME_TOPIC), None)
        bad = next((w for w in dp.SLOP + dp.GENERIC_TITLE + TITLE_AVOID
                    if re.search(r"\b" + re.escape(w), en.lower())), None)
        why = (
            "not one of the collected searches" if not c else
            "same search as an earlier pick" if k in used else
            "missing a title" if not en or not ar or "|" in en + ar + cl else
            "title drops the search's words" if not grounded(
                c["query"], ar if c["lang"] == "ar" else en, AR_STOP | dp._STOP) else
            "not specific enough (skill criterion 1)" if not dp.TITLE_SPECIFIC.search(en) else
            f"uses \"{bad}\"" if bad else
            f"title is {len(en)} characters (limit {TITLE_MAX})" if len(en) > TITLE_MAX else
            f"{score:.0%} like \"{like}\"" if score > dp.SIMILARITY_LIMIT else
            f"same topic as \"{twin}\"" if twin else "")
        if why:
            rejected.append({**t, "why": why})
            continue
        used.add(k)
        taken.append(en)
        picks.append({"query": c["query"], "evidence": c["evidence"], "intent": dp._plain(t.get("intent")),
                      "cluster": cl if cl in clusters else (clusters[0] if clusters else cl),
                      "en_title": en, "ar_title": ar})
    return picks, rejected


# ======================================================================
# Report + queue
# ======================================================================
def _cell(s):
    return str(s).replace("|", "/").replace("\n", " ")


def write_report(path, date, stats, ncands, queued, spare, rejected):
    tr = (f"blocked ({stats['blocked']}), so autocomplete carried this run" if stats["blocked"] else
          f"{stats['trends']} related queries")
    fb = (f" The UAE was asked too for: {', '.join(stats['fallback'])} (too little Oman data)."
          if stats["fallback"] else "")
    out = [
        "# Trend-backed article topics\n\n",
        f"Generated by `execution/trend_topics.py` on {date}. This file is rewritten on every run, so "
        "edit topics in `article_queue.md`, not here.\n\n",
        f"**Sources:** {stats['seeds']} seed keywords. Google Trends: {tr}.{fb} Google autocomplete: "
        f"{stats['autocomplete']} suggestions. {ncands} distinct searches went to the model.\n\n",
        "Arabic titles are AI-drafted and not yet reviewed by a native speaker.\n\n",
    ]

    def table(title, rows, head, cols):
        out.append(f"## {title}\n\n")
        if not rows:
            out.append("None.\n\n")
            return
        out.append("| " + " | ".join(head) + " |\n|" + "---|" * len(head) + "\n")
        for r in rows:
            out.append("| " + " | ".join(_cell(c(r)) for c in cols) + " |\n")
        out.append("\n")

    topic_cols = [lambda r: r.get("num", "-"), lambda r: r["en_title"], lambda r: r["ar_title"],
                  lambda r: r["query"], lambda r: "; ".join(r["evidence"]), lambda r: r["intent"]]
    head = ["#", "English title", "Arabic title", "Search behind it", "Evidence", "Who searches it"]
    table("Added to the queue", queued, head, topic_cols)
    table("Also suggested (not queued; copy one into the queue to use it)", spare, head, topic_cols)
    table("Rejected by the checks", rejected, ["Search", "Proposed title", "Why"],
          [lambda r: r.get("query", ""), lambda r: r.get("en_title", ""), lambda r: r["why"]])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(out), encoding="utf-8")


def top_up(dp, corp, rows, n, write=True):
    """Research, pick and (if write) append up to n trend-backed topics. Returns the new queue rows."""
    dp.log(f"Trend research: {len(SEEDS)} seeds, {GEO} first")
    cands, stats = collect(dp)
    dp.log(f"  {len(cands)} distinct searches collected")
    if not cands:
        return []
    picks, rejected = pick(dp, cands, corp, rows, n)
    return queue_picks(dp, picks, rejected, rows, n, stats, min(len(cands), MAX_CANDIDATES), write)


def queue_picks(dp, picks, rejected, rows, n, stats, ncands, write=True):
    """Append the first n picks to the queue and write the evidence report. Returns the new rows."""
    nums = [int(r["num"]) for r in rows if r["num"].isdigit()]
    nxt = max(nums) + 1 if nums else 1
    queued, spare = picks[:n], picks[n:]
    new = []
    for i, p in enumerate(queued):
        p["num"] = str(nxt + i)
        new.append({"num": p["num"], "cluster": p["cluster"], "en_title": p["en_title"],
                    "ar_title": p["ar_title"], "status": "Pending", "date": "-", "url": "-"})
    date = dp.today()
    report = REPORT_FILE if write else TMP / f"{date}.md"
    write_report(report, date, stats, ncands, queued, spare, rejected)
    if write and new:
        dp.append_queue_rows(new)
    for p in queued:
        dp.log(f"  {'queued' if write else 'would queue'}: {p['en_title']}   <- \"{p['query']}\"")
    dp.log(f"  report: {report.relative_to(ROOT)}")
    return new


def load_env():
    """KEY=value lines from .env, for local runs (GitHub passes the secrets as env vars)."""
    for p in (ROOT / ".env", ROOT.parent / ".env"):
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                m = re.match(r"\s*([A-Z_][A-Z0-9_]*)\s*=\s*(.*)", line)
                if m and not os.environ.get(m.group(1)):
                    os.environ[m.group(1)] = m.group(2).strip().strip("'\"")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dry-run", action="store_true", help="report only; leave the queue alone")
    ap.add_argument("--target", type=int, default=TARGET_PENDING,
                    help=f"top the queue up to this many Pending topics (default {TARGET_PENDING})")
    a = ap.parse_args()
    load_env()
    sys.path.insert(0, str(HERE))
    import daily_publish as dp
    corp = dp.corpus()
    _, rows = dp.read_queue()
    pending = sum(r["status"].lower() == "pending" for r in rows)
    n = a.target if a.dry_run else a.target - pending
    if n <= 0:
        dp.log(f"The queue already has {pending} Pending topics (target {a.target}). Nothing to add.")
        return
    try:
        top_up(dp, corp, rows, n, write=not a.dry_run)
    except dp.TransientError as e:
        dp.log(f"\nPOSTPONED: {e}")
        sys.exit(dp.EXIT_TEMPFAIL)
    except dp.PublishError as e:
        dp.log(f"\nFAILED: {e}\nThe queue is unchanged.")
        sys.exit(1)


if __name__ == "__main__":
    main()
