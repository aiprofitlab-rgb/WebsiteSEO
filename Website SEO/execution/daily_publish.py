#!/usr/bin/env python3
"""
Daily article publisher: the article-creator skill, run unattended once a day.

    python3 execution/daily_publish.py                  # publish the next queued topic
    python3 execution/daily_publish.py --dry-run        # generate + validate into .tmp/, publish nothing
    python3 execution/daily_publish.py --from-dir DIR   # publish a dry run you already checked (no API spend)
    python3 execution/daily_publish.py --repair SLUG    # regenerate a broken article in place, same URL
    python3 execution/daily_publish.py --verify SLUG    # after deploy: are the EN + AR pages really live?
    python3 execution/daily_publish.py --preflight      # key, models and dependencies only

The rules come from the skill (Website/SKILL_article_creator/SKILL.md): its Step 1
quality criteria are sent to the model verbatim, its local-business JSON-LD block
is copied out of it verbatim, and the source document is written in the marker
contract its Step 5 renderer (tools/reskin_articles.py) parses.

It FAILS CLOSED. The version this replaces published a three-word placeholder
page whenever the Gemini call failed, copied one stock image onto every article,
ignored the exit code of every build step, and marked the topic Published either
way. Here every stage either passes its checks or stops the run with a non-zero
exit, before anything is written into public_html/ or the queue:

  1. the model writes structured JSON (never a whole HTML page), so the markers,
     the schema, the NAP block, the canonical and the legal entity are code, not
     something the model can forget;
  2. the draft is audited against the skill's criteria, measured with the
     renderer's own parser (tools/v4/legacy.py), and sent back for revision with
     the list of failures, up to 3 attempts per language;
  3. every reference URL is fetched; dead ones are unlinked and dropped;
  4. a hero image is generated for THIS article and checked (decodes, wide
     enough, light-mode) under a new filename, so no CDN can serve an old one;
  5. the build steps run with check=True and the rendered pages are verified.

Deploying is the workflow's job (.github/workflows/daily_publish.yml), after the
commit, so the deploy's git diff contains the new files.

Since 2026-10-16 this is the FALLBACK. The daily article is written by a Google
Antigravity agent on Nahid's Mac (execution/agent_publish.py, which reuses this
module's checks, renderer and build). GitHub runs this script in the evening only
when the Mac published nothing that day. It has no image model (the Gemini API free
tier allows 0 images and kie.ai is not used), so it ships a placeholder hero and lists
the article in directives/pending_heroes.json; the next Antigravity run generates the
real hero and swaps it in.
"""

import argparse
import base64
import hashlib
import html
import io
import json
import os
import re
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent            # .../Website SEO
SKILL_FILE = ROOT.parent / "SKILL_article_creator" / "SKILL.md"
QUEUE_FILE = ROOT / "directives" / "article_queue.md"
SNIPPETS_FILE = ROOT / "directives" / "forum_snippets.md"
PUBLIC = ROOT / "public_html"
BLOG = PUBLIC / "blog"
IMAGES = BLOG / "images"
TMP = ROOT / ".tmp" / "daily_publish"
SITE = "https://aiprofitlab.io"
TZ = ZoneInfo("Asia/Muscat")

sys.path.insert(0, str(ROOT / "tools" / "v4"))
import legacy  # noqa: E402  (the renderer's own parser, so we measure what it publishes)

# Models are tried in order; the next one is used when a model is missing,
# retired or overloaded. Override with comma-separated env vars.
# (gemini-2.5-pro still appears in the model list but answers 404 "no longer available to new users".)
TEXT_MODELS = os.environ.get("GEMINI_TEXT_MODELS", "gemini-3.8-flash,gemini-3.6-flash,gemini-3.5-flash").split(",")
IMAGE_MODELS = os.environ.get("GEMINI_IMAGE_MODELS",
                              "gemini-3.1-flash-image,gemini-3.1-flash-lite-image").split(",")
API = "https://generativelanguage.googleapis.com/v1beta"
# Hero images: tried in this order. "placeholder" (the default) ships the brand placeholder
# and queues the article in pending_heroes.json for Antigravity to illustrate. "kie" (Seedream,
# prepaid credit) and "gemini" (needs billing: the free tier allows 0 images) still work.
IMAGE_PROVIDERS = os.environ.get("IMAGE_PROVIDERS", "placeholder").split(",")
PLACEHOLDER_HERO = ROOT / "brand" / "og" / "article-hero-placeholder.png"
PENDING_HEROES = ROOT / "directives" / "pending_heroes.json"
TEMP_IMAGE_STATUS = "Published (temp image)"
KIE_API = "https://api.kie.ai"
KIE_MODEL = os.environ.get("KIE_IMAGE_MODEL", "seedream/5-pro-text-to-image")

ATTEMPTS = 4
WORDS = {"en": (800, 1200), "ar": (650, 1350)}   # skill: 800-1200; Arabic runs ~10% shorter
META_LEN = {"en": (140, 155), "ar": (130, 160)}
MIN_VERIFIED_REFS = 2
SIMILARITY_LIMIT = 0.65
REFILL_BELOW = 2          # queue fewer Pending topics than this -> propose new ones
REFILL_COUNT = 6

CONTACT = {"en": "/en/contact/", "ar": "/contact/"}
SAFE_INTERNAL = {
    "en": {"/en/contact/", "/en/services/", "/en/about/", "/en/process/", "/en/demos/",
           "/en/simulators/", "/en/smart-storefront/", "/en/tools/", "/blog/", "/"},
    "ar": {"/contact/", "/services/", "/about/", "/process/", "/blog-ar/", "/ar/"},
}

# ---- skill criteria that are checked mechanically --------------------------------
SLOP = ["in today's fast-paced", "fast-paced digital world", "delve", "tapestry", "supercharge",
        "game-changer", "game changer", "unleash", "seamless", "amazing", "incredible", "powerful"]
GENERIC_TITLE = ["supercharge your business", "ai for business", "unlock the power of ai",
                 "revolutionize your", "transform your business", "take your business to the next level"]
SELF_PROMO = ["we are", "we provide", "our company", "ai profit lab is", "welcome to", "at ai profit lab"]
META_BAD_START = ("ai profit lab", "learn how", "discover", "supercharge")
TITLE_SPECIFIC = re.compile(r"\d|oman|muscat|gcc|gulf|uae|saudi|sohar|salalah|duqm|how to|why|cost|"
                            r"roi|guide|free|best|top|checklist|vs\b|step", re.I)
GCC_EN = ["muscat", "oman", "omani", "gcc", "gulf", "uae", "dubai", "saudi", "riyadh", "qatar",
          "bahrain", "kuwait", "vision 2040", "pdpl", "sohar", "salalah", "duqm", "nizwa",
          "royal decree", "omantel", "ooredoo", "ma'een", "otech", "mtcit", "omr", "rial", "thawani"]
GCC_AR = ["مسقط", "عمان", "عُمان", "العماني", "العمانية", "الخليج", "الإمارات", "دبي", "السعودية",
          "الرياض", "قطر", "البحرين", "الكويت", "رؤية 2040", "رؤية عمان", "صحار", "صلالة", "الدقم",
          "نزوى", "مرسوم سلطاني", "عمانتل", "ريال", "حماية البيانات الشخصية"]

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def _ssl_context():
    # The python.org macOS build ships without a CA bundle; every HTTPS call
    # failed there with CERTIFICATE_VERIFY_FAILED. certifi fixes that.
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


SSL = _ssl_context()


class PublishError(Exception):
    """A stage failed its checks. The run stops; nothing is published."""


class TransientError(PublishError):
    """Every model was overloaded or unreachable. Worth retrying later today (exit 75)."""


EXIT_TEMPFAIL = 75


def log(msg=""):
    print(msg, flush=True)


def today():
    # The site is read in Muscat, and the date goes into the URL. PUBLISH_DATE_LAG_HOURS
    # lets the evening fallback keep its date when GitHub starts it hours late (runs
    # have started 5 hours after their cron slot), past Muscat midnight.
    lag = float(os.environ.get("PUBLISH_DATE_LAG_HOURS") or 0)
    return (datetime.now(TZ) - timedelta(hours=lag)).strftime("%Y-%m-%d")


# ======================================================================
# Gemini
# ======================================================================
def _api_key():
    k = os.environ.get("GEMINI_API_KEY", "").strip()
    if not k:
        raise PublishError("GEMINI_API_KEY is not set. In GitHub: Settings > Secrets and variables > "
                           "Actions > New repository secret, named GEMINI_API_KEY.")
    return k


def _http_json(url, body=None, timeout=600):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method="POST" if data else "GET",
                                 headers={"Content-Type": "application/json",
                                          "x-goog-api-key": _api_key()})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=SSL) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            msg = json.loads(raw)["error"]["message"]
        except Exception:
            msg = raw[:400]
        raise ApiError(e.code, msg) from None


class ApiError(Exception):
    def __init__(self, code, msg):
        super().__init__(f"HTTP {code}: {msg}")
        self.code = code


USAGE = {"prompt": 0, "output": 0, "thoughts": 0, "images": 0}


_DEAD_MODELS = set()      # retired / not on this plan / out of quota: skipped for the rest of the run
_QUOTA_OUT = set()        # ...of which, out of today's quota only (a later run may have quota again)


def _generate(models, body, what, rounds=5):
    """POST generateContent. Cycles through the models in rounds, backing off between
    rounds, because "high demand" 503s come in bursts that pass within minutes.
    Returns (response, model)."""
    last = None
    for rnd in range(rounds):
        live = [m.strip() for m in models if m.strip() not in _DEAD_MODELS]
        if not live:
            break
        for model in live:
            try:
                res = _http_json(f"{API}/models/{model}:generateContent", body)
                u = res.get("usageMetadata", {})
                USAGE["prompt"] += u.get("promptTokenCount", 0)
                USAGE["output"] += u.get("candidatesTokenCount", 0)
                USAGE["thoughts"] += u.get("thoughtsTokenCount", 0)
                return res, model
            except ApiError as e:
                last = e
                log(f"    ! {what} via {model}: {str(e)[:160]}")
                if e.code in (401, 403):
                    raise PublishError(f"Gemini rejected the API key ({e}). Check the GEMINI_API_KEY "
                                       "secret and that billing is enabled for its project.")
                if e.code == 404 or (e.code == 429 and _hard_quota(str(e))):
                    _DEAD_MODELS.add(model)      # will not come back during this run
                    if e.code == 429 and not re.search(r"limit: 0\b", str(e)):
                        _QUOTA_OUT.add(model)
                elif e.code == 400:
                    break                        # the request itself is wrong; no model will take it
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                last = e
                log(f"    ! {what} via {model}: network error {e}")
        if rnd < rounds - 1 and any(m.strip() not in _DEAD_MODELS for m in models):
            wait = 30 * 2 ** rnd                 # 30, 60, 120, 240 s
            log(f"    waiting {wait}s before trying again")
            time.sleep(wait)
    transient = (isinstance(last, ApiError) and last.code in (429, 500, 502, 503, 504)) or \
        isinstance(last, (urllib.error.URLError, TimeoutError, ConnectionError))
    if any(m.strip() in _QUOTA_OUT for m in models) and all(m.strip() in _DEAD_MODELS for m in models):
        raise TransientError(f"{what}: today's free-tier quota is used up on "
                             f"{', '.join(sorted(_QUOTA_OUT))}. Enabling billing on the key's Google "
                             f"project removes this limit. Last error: {last}")
    if transient and any(m.strip() not in _DEAD_MODELS for m in models):
        raise TransientError(f"{what}: every model stayed overloaded or unreachable. Last error: {last}")
    raise PublishError(f"{what} failed on every model ({', '.join(models)}). Last error: {last}")


def _hard_quota(msg):
    """True for a 429 that waiting will not fix inside this run: a free-tier limit of 0
    (the model needs billing) or a daily quota with hours to go."""
    if re.search(r"limit: 0\b", msg):
        return True
    m = re.search(r"retry in (?:(\d+)h)?(?:(\d+)m)?([\d.]+)s", msg)
    if m:
        secs = int(m.group(1) or 0) * 3600 + int(m.group(2) or 0) * 60 + float(m.group(3))
        return secs > 120
    return "PerDay" in msg or "per day" in msg.lower()


def gemini_json(system, prompt, schema, what):
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "responseSchema": schema,
                             "maxOutputTokens": 60000},
    }
    res, model = _generate(TEXT_MODELS, body, what)
    cand = (res.get("candidates") or [{}])[0]
    reason = cand.get("finishReason", "")
    text = "".join(p.get("text", "") for p in cand.get("content", {}).get("parts", [])
                   if not p.get("thought"))
    if reason not in ("STOP", "") or not text.strip():
        block = res.get("promptFeedback", {}).get("blockReason")
        raise PublishError(f"{what}: model {model} stopped with {reason or block or 'no output'}")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            return json.loads(m.group(0))
        raise PublishError(f"{what}: model {model} returned invalid JSON")


def kie_image(prompt):
    """Seedream on kie.ai: create a task, poll it, download the result."""
    key = os.environ.get("KIE_AI_API_KEY", "").strip()
    if not key:
        raise PublishError("KIE_AI_API_KEY is not set")
    h = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}

    def call(url, body=None):
        req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None, headers=h,
                                     method="POST" if body else "GET")
        with urllib.request.urlopen(req, timeout=60, context=SSL) as r:
            return json.load(r)

    j = call(f"{KIE_API}/api/v1/jobs/createTask", {"model": KIE_MODEL, "input": {
        "prompt": prompt, "aspect_ratio": "16:9", "quality": "high", "output_format": "png",
        "nsfw_checker": False}})
    if j.get("code") != 200 or not (j.get("data") or {}).get("taskId"):
        raise PublishError(f"kie.ai createTask: {json.dumps(j)[:300]}")
    tid, t0, delay = j["data"]["taskId"], time.time(), 4
    while time.time() - t0 < 600:
        time.sleep(delay)
        delay = min(delay * 1.25, 15)
        d = (call(f"{KIE_API}/api/v1/jobs/recordInfo?taskId={tid}").get("data") or {})
        state = d.get("state") or d.get("status")
        if state == "success":
            out = d.get("resultJson")
            out = json.loads(out) if isinstance(out, str) else (out or {})
            urls = out.get("resultUrls") or out.get("result_urls") or []
            if not urls:
                raise PublishError("kie.ai: task succeeded with no result URL")
            with urllib.request.urlopen(urllib.request.Request(urls[0], headers={"User-Agent": UA}),
                                        timeout=120, context=SSL) as r:
                USAGE["images"] += 1
                return r.read(), f"kie:{KIE_MODEL}"
        if state in ("fail", "failed"):
            raise PublishError(f"kie.ai task failed: {d.get('failMsg') or d.get('failCode')}")
    raise PublishError("kie.ai: no image after 10 minutes")


def kie_credit():
    key = os.environ.get("KIE_AI_API_KEY", "").strip()
    if not key:
        return None
    req = urllib.request.Request(f"{KIE_API}/api/v1/chat/credit", headers={"Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=30, context=SSL) as r:
        return json.load(r).get("data")


def generate_image(prompt):
    """First provider that returns an image wins."""
    errors = []
    for prov in (p.strip() for p in IMAGE_PROVIDERS):
        try:
            if prov == "kie":
                return kie_image(prompt)
            if prov == "gemini":
                return gemini_image(prompt)
        except (PublishError, urllib.error.URLError, TimeoutError, ValueError) as e:
            log(f"    ! image via {prov}: {e}")
            errors.append(f"{prov}: {e}")
    raise PublishError("No image provider worked. " + " | ".join(errors) + ". Fix: add the KIE_AI_API_KEY "
                       "secret, or enable billing for the Gemini key's Google project.")


def gemini_image(prompt):
    """Return PNG bytes, or raise. Tries smaller config variants when a model rejects one."""
    configs = [{"aspectRatio": "16:9", "imageSize": "1K"}, {"aspectRatio": "16:9"}, None]
    last = None
    for model in IMAGE_MODELS:
        for cfg in configs:
            gen = {"responseModalities": ["IMAGE"]}
            if cfg:
                gen["imageConfig"] = cfg
            body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}], "generationConfig": gen}
            try:
                res, _ = _generate([model], body, "hero image", rounds=2)
            except PublishError as e:
                last = e
                if re.search(r"limit: 0|quota", str(e)):
                    break            # a config change will not fix a quota
                continue
            for p in (res.get("candidates") or [{}])[0].get("content", {}).get("parts", []):
                d = p.get("inlineData") or p.get("inline_data")
                if d and d.get("data"):
                    USAGE["images"] += 1
                    return base64.b64decode(d["data"]), model
            last = PublishError(f"{model} returned no image")
    raise PublishError(f"Image generation failed on every model. Last error: {last}")


# ======================================================================
# Queue (directives/article_queue.md)
# ======================================================================
def read_queue():
    lines = QUEUE_FILE.read_text(encoding="utf-8").splitlines(keepends=True)
    rows = []
    for i, line in enumerate(lines):
        s = line.strip()
        if not s.startswith("|") or s.startswith("|---") or s.startswith("| #"):
            continue
        parts = [p.strip() for p in s.strip("|").split("|")]
        if len(parts) < 7:
            continue
        rows.append({"idx": i, "num": parts[0], "cluster": parts[1], "en_title": parts[2],
                     "ar_title": parts[3], "status": parts[4], "date": parts[5], "url": parts[6]})
    return lines, rows


def _row_line(r):
    return "| " + " | ".join([r["num"], r["cluster"], r["en_title"], r["ar_title"],
                              r["status"], r["date"], r["url"]]) + " |\n"


def update_queue_row(row):
    lines, _ = read_queue()
    lines[row["idx"]] = _row_line(row)
    QUEUE_FILE.write_text("".join(lines), encoding="utf-8")


def append_queue_rows(new_rows):
    lines, rows = read_queue()
    last = max(r["idx"] for r in rows) if rows else len(lines) - 1
    lines[last + 1:last + 1] = [_row_line(r) for r in new_rows]
    QUEUE_FILE.write_text("".join(lines), encoding="utf-8")


# ======================================================================
# Corpus: what is already published (similarity check + internal links)
# ======================================================================
def corpus():
    out = {"en": {}, "ar": {}}
    for lang in ("en", "ar"):
        for f in sorted((BLOG / lang).glob("*.html")):
            head = f.read_text(encoding="utf-8", errors="ignore")[:8000]
            m = re.search(r"<title>(.*?)</title>", head, re.S)
            t = html.unescape(m.group(1)).strip() if m else f.stem
            out[lang][f.stem] = re.sub(r"\s*\|\s*AI Profit Lab\s*$", "", t).strip()
    return out


_STOP = set("a an and are as at be by can do for from how in into is it its of on or the to vs what "
            "when where which who why with your you our their this that".split())


def _tok(t):
    return {w for w in re.findall(r"[a-z0-9]+", t.lower()) if w not in _STOP and len(w) > 1}


def _grams(t, n=3):
    t = re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()
    return {t[i:i + n] for i in range(len(t) - n + 1)}


def similarity(a, b):
    """The skill's Step 0 measure: the worse of token Jaccard and character-trigram Jaccard."""
    ta, tb, ga, gb = _tok(a), _tok(b), _grams(a), _grams(b)
    j = len(ta & tb) / len(ta | tb) if ta | tb else 0
    c = len(ga & gb) / len(ga | gb) if ga | gb else 0
    return max(j, c)


def closest(title, titles, exclude=()):
    best = (0.0, None)
    for slug, t in titles.items():
        if slug in exclude:
            continue
        s = similarity(title, t)
        if s > best[0]:
            best = (s, slug)
    return best


def link_candidates(topic, corp, exclude, n=14):
    scored = sorted(((len(_tok(topic) & _tok(t)), slug) for slug, t in corp["en"].items()
                     if slug not in exclude and slug in corp["ar"]), reverse=True)
    return [s for score, s in scored[:n] if score > 0] or [s for _, s in scored[:n]]


# ======================================================================
# Prompts
# ======================================================================
def skill_text():
    if not SKILL_FILE.exists():
        raise PublishError(f"Skill file not found: {SKILL_FILE}")
    return SKILL_FILE.read_text(encoding="utf-8")


def skill_criteria():
    s = skill_text()
    m = re.search(r"## Step 1: Research and Outline(.*?)## Step 2:", s, re.S)
    if not m:
        raise PublishError("Could not find 'Step 1' in SKILL.md; its headings changed.")
    return m.group(1).strip()


def nap_block():
    """The ProfessionalService JSON-LD, verbatim from the skill (never retyped)."""
    m = re.search(r'<script type="application/ld\+json">\s*(\{\s*"@context": "https://schema.org",\s*'
                  r'"@type": "ProfessionalService".*?\})\s*</script>', skill_text(), re.S)
    if not m:
        raise PublishError("Could not find the ProfessionalService block in SKILL.md.")
    node = json.loads(m.group(1))
    return node


AUTOMATION_RULES = """
RULES FOR THIS UNATTENDED RUN (they add to the skill criteria above; where they are stricter, they win):

Facts. This page is published under a real company's name with no human review.
- Never invent client names, case studies, testimonials, survey results, market statistics, or quotes.
- Never quote or attribute Reddit threads, usernames or forum posts. You may describe, in general terms,
  the questions business owners commonly raise.
- Every number must be one of: (a) a figure from a source you cite inline, (b) worked arithmetic that is
  clearly illustrative ("Say your team answers 300 WhatsApp messages a week at 4 minutes each..."),
  or (c) public list pricing of a named third-party tool you are certain of.
- Do not state AI Profit Lab prices, clients, results or years of experience, and never write "we found",
  "our data", "our clients" or "in our experience". Never attribute a figure to a source unless that
  source states it.
- A threshold or target you recommend is phrased as a recommendation ("aim for a first reply under
  2 seconds"), never as an industry fact or an observed average.
- These rules apply to every field: title, meta description, dek, body, FAQs and the forum snippet.
- State Omani/GCC legal or regulatory specifics (decree numbers, dates, fines) only if you are certain;
  otherwise describe them generally.

Structure (the renderer builds the page; you only write content):
- 4 to 6 sections. Each heading is a question. "answer" is the ~40-word direct answer under it, in an
  "X is Y" / "To do X, you need Y" form. "body_html" is the rest of the section.
- intro_html + every answer + every body_html together: 900 to 1100 words. Count carefully.
- At least one section's body_html contains a real <table> with <thead> and <tbody>.
- Allowed tags in intro_html/body_html: p, h3, ul, ol, li, strong, em, a, table, thead, tbody, tr, th,
  td, blockquote. No h1/h2, no div, no class or style attributes, no images.
- Exactly 10 FAQs, each answer 30 to 80 words.
- References: 4 to 6 real, stable, high-authority URLs (vendor documentation, government or regulator
  portals, major publishers). Prefer a well-known page you are sure exists over a deep link you are not.
  Every reference must also be linked inline in the body with <a href>. Every URL is fetched before
  publishing; dead ones are deleted along with their links.
- Internal links: 2 or 3 contextual links to the existing articles listed below, using exactly the
  URLs given. No other internal blog URLs.
- No call-to-action block in the body; the page adds its own.
- image_concept: one paragraph describing the hero photograph for criterion 16: bright light-mode
  editorial scene, cream/off-white background, deep teal and subtle amber accents, realistic people or
  objects relevant to the topic in a GCC business setting. No text, letters, logos, screens with
  readable text, or watermarks.
- forum_snippet: per Step 8 of the skill, 60 to 90 words, problem first, one concrete number from the
  piece, ending with the article URL given below.
"""

SECTION = {"type": "OBJECT", "properties": {
    "heading": {"type": "STRING"}, "answer": {"type": "STRING"}, "body_html": {"type": "STRING"}},
    "required": ["heading", "answer", "body_html"]}
ARTICLE_SCHEMA = {"type": "OBJECT", "properties": {
    "title": {"type": "STRING"},
    "meta_description": {"type": "STRING"},
    "keywords": {"type": "STRING"},
    "category": {"type": "STRING"},
    "dek": {"type": "STRING"},
    "intro_html": {"type": "STRING"},
    "sections": {"type": "ARRAY", "items": SECTION},
    "faqs": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
        "q": {"type": "STRING"}, "a": {"type": "STRING"}}, "required": ["q", "a"]}},
    "references": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
        "label": {"type": "STRING"}, "url": {"type": "STRING"}}, "required": ["label", "url"]}},
    "image_concept": {"type": "STRING"},
    "forum_snippet": {"type": "STRING"},
}, "required": ["title", "meta_description", "keywords", "category", "dek", "intro_html", "sections",
                "faqs", "references", "image_concept", "forum_snippet"]}


def system_prompt():
    return ("You write for the AI Profit Lab blog (aiprofitlab.io), an AI-automation consultancy in "
            "Muscat, Oman, read by owners and managers of small and mid-sized GCC businesses. You are "
            "running the article-creator skill. Its quality criteria follow, verbatim. Meet every one."
            "\n\n=== SKILL: QUALITY CRITERIA ===\n" + skill_criteria() + "\n=== END SKILL ===\n"
            + AUTOMATION_RULES)


def en_prompt(topic, slug, date, corp, links):
    lst = "\n".join(f"- {corp['en'][s]} -> /blog/en/{s}/" for s in links)
    return (f"Write the ENGLISH article.\n\nTopic / working title: {topic['en_title']}\n"
            f"Cluster: {topic['cluster']}\nPublication date: {date}\n"
            f"Article URL: {SITE}/blog/en/{slug}/\n\n"
            f"Keep the title close to the working title (the URL slug is fixed), but fix it if it breaks "
            f"criterion 1 or uses a banned word.\n\nExisting articles you may link to:\n{lst}\n")


def ar_prompt(topic, slug, date, corp, links, en):
    lst = "\n".join(f"- {corp['ar'][s]} -> /blog/ar/{s}/" for s in links)
    return (f"Write the ARABIC edition of the article below for Omani and GCC business readers, in "
            f"professional Modern Standard Arabic. Adapt, do not translate word for word, but keep the "
            f"same facts, numbers, table data and reference URLs (reference labels in Arabic). Same rules "
            f"as the English: section headings end in '؟', exactly 10 FAQs, 800 to 1100 words in "
            f"intro_html + answers + body_html. The meta description must start with a regional pain "
            f"point (for example 'هل تعاني من...') and be 140 to 155 characters.\n\n"
            f"Working Arabic title: {topic['ar_title']}\nPublication date: {date}\n"
            f"Article URL: {SITE}/blog/ar/{slug}/\n\n"
            f"Internal links must use these Arabic URLs only:\n{lst}\n\n"
            f"ENGLISH ARTICLE (JSON):\n{json.dumps(en, ensure_ascii=False)}\n")


def revise_prompt(original_prompt, draft, problems):
    return (original_prompt + "\n\nYour previous draft (JSON below) failed these checks:\n- "
            + "\n- ".join(problems)
            + "\n\nReturn the complete corrected article JSON. Fix every failure listed; keep what passed."
            + "\n\nPREVIOUS DRAFT:\n" + json.dumps(draft, ensure_ascii=False))


# ======================================================================
# HTML: sanitise the model's fragments, render the skill's source template
# ======================================================================
ALLOWED = {"p", "h3", "ul", "ol", "li", "strong", "em", "b", "i", "a", "table", "thead", "tbody",
           "tr", "th", "td", "blockquote", "br", "code"}
DROP_CONTENT = {"script", "style", "iframe", "object", "svg", "form", "button", "img"}
DEMOTE = {"h1", "h2", "h4", "h5", "h6"}      # sections own the <h2>s; anything else becomes <h3>


class _Sanitiser(HTMLParser):
    def __init__(self, lang, corp, links):
        super().__init__(convert_charrefs=True)
        self.lang, self.corp, self.out, self.stack, self.skip = lang, corp, [], [], 0
        self.links = links          # collects external hrefs

    def _href(self, href):
        href = (href or "").strip()
        if href.startswith(SITE):
            href = href[len(SITE):] or "/"
        if re.match(r"https?://", href):
            self.links.add(href)
            return href
        m = re.match(r"/blog/(en|ar)/([^/?#]+?)(?:\.html)?/?(#.*)?$", href)
        if m:
            lang, slug, frag = m.group(1), m.group(2), m.group(3) or ""
            if lang == self.lang and slug in self.corp[lang]:
                return f"/blog/{lang}/{slug}/{frag}"
            return None
        path = href.split("#")[0]
        if path and not path.endswith("/"):
            path += "/"
        return href if path in SAFE_INTERNAL[self.lang] else None

    def handle_starttag(self, tag, attrs):
        tag = "h3" if tag in DEMOTE else tag
        if self.skip or tag in DROP_CONTENT:
            self.skip += tag in DROP_CONTENT and tag not in ("img", "br")
            return
        if tag not in ALLOWED:
            return
        a = dict(attrs)
        if tag == "a":
            h = self._href(a.get("href"))
            if not h:
                self.stack.append("a#unwrapped")
                return
            self.out.append(f'<a href="{html.escape(h, quote=True)}">')
        elif tag in ("th", "td") and (a.get("colspan") or a.get("rowspan")):
            extra = "".join(f' {k}="{int(v)}"' for k, v in a.items()
                            if k in ("colspan", "rowspan") and str(v).isdigit())
            self.out.append(f"<{tag}{extra}>")
        else:
            self.out.append("<br>" if tag == "br" else f"<{tag}>")
        if tag != "br":
            self.stack.append(tag)

    def handle_endtag(self, tag):
        tag = "h3" if tag in DEMOTE else tag
        if tag in DROP_CONTENT:
            if tag not in ("img", "br") and self.skip:
                self.skip -= 1
            return
        if self.skip or tag not in ALLOWED or tag == "br":
            return
        names = [t.split("#")[0] for t in self.stack]
        if tag not in names:
            return
        while self.stack:
            t = self.stack.pop()
            if t != "a#unwrapped":
                self.out.append(f"</{t}>")
            if t.split("#")[0] == tag:
                break

    def handle_data(self, data):
        if not self.skip:
            self.out.append(html.escape(data, quote=False))

    def result(self):
        while self.stack:
            t = self.stack.pop()
            if t != "a#unwrapped":
                self.out.append(f"</{t}>")
        return "".join(self.out).strip()


def sanitise(fragment, lang, corp, links):
    s = _Sanitiser(lang, corp, links)
    s.feed(fragment or "")
    s.close()
    out = s.result()
    if out and not out.lstrip().startswith("<"):
        out = f"<p>{out}</p>"
    return out


def unlink(fragment, dead):
    """Remove <a> tags pointing at dead URLs, keeping their text."""
    for url in dead:
        fragment = re.sub(r'<a href="%s">(.*?)</a>' % re.escape(html.escape(url, quote=True)),
                          r"\1", fragment, flags=re.S)
    return fragment


def _e(s):
    return html.escape(str(s or "").strip(), quote=True)


def _plain(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def _ld(obj):
    return json.dumps(obj, ensure_ascii=False, indent=2).replace("</", "<\\/")


def render_source(lang, d, slug, date, image_name, nap, modified=None):
    """The skill's source template, with its marker contract (SKILL.md 'Marker contract')."""
    en = lang == "en"
    canon = f"{SITE}/blog/{lang}/{slug}/"
    img_url = f"/blog/images/{image_name}.png"
    article = {"@type": "Article", "headline": d["title"], "description": d["meta_description"],
               "image": SITE + img_url, "author": {"@type": "Organization", "name": "AI Profit Lab"},
               "publisher": {"@id": f"{SITE}/#organization"}, "datePublished": date,
               "inLanguage": lang, "mainEntityOfPage": canon}
    if modified and modified != date:
        article["dateModified"] = modified
    graph = {"@context": "https://schema.org", "@graph": [
        {"@type": "Organization", "@id": f"{SITE}/#organization", "name": "AI Profit Lab",
         "legalName": nap["legalName"], "url": f"{SITE}/",
         "logo": {"@type": "ImageObject", "url": f"{SITE}/favicon.svg"}},
        article,
        {"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}}
            for f in d["faqs"]]},
    ]}
    nums = "١٢٣٤٥٦٧٨٩" if not en else "123456789"
    toc = "\n".join(
        f'                    <li><a href="#section-{i}"><span>{nums[i - 1] if i <= 9 else i}.</span> '
        f'{_e(s["heading"])}</a></li>' for i, s in enumerate(d["sections"], 1))
    faq_label = "Frequently Asked Questions" if en else "الأسئلة الشائعة"
    prose = [d["intro_html"]]
    for i, s in enumerate(d["sections"], 1):
        prose.append(f'<h2 id="section-{i}">{_e(s["heading"])}</h2>\n<p>{_e(s["answer"])}</p>\n{s["body_html"]}')
    faqs = "\n".join(
        f'                    <div class="glass-card rounded-2xl p-6">\n'
        f'                        <h3 class="text-lg font-bold text-white mb-2">{_e(f["q"])}</h3>\n'
        f'                        <p class="text-gray-400 mb-0">{_e(f["a"])}</p>\n'
        f'                    </div>' for f in d["faqs"])
    refs = "\n".join(f'                    <li><a href="{_e(r["url"])}" target="_blank" rel="noopener">'
                     f'{_e(r["label"])}</a></li>' for r in d["references"])
    if en:
        alt = f"{image_name} - Empowering AI Solutions by AI Profit Lab to scale your business operations."
        cta = ("Ready to Automate Your Business Operations?",
               "AI Profit Lab helps non-technical managers in Oman and the GCC deploy custom AI solutions, "
               "automated customer service systems, and real-time dashboards to slash overhead costs and "
               "eliminate manual busywork.", "Book a Free 30-Minute AI Consultation")
        toc_title, refs_title, back = "Table of Contents", "References", ("/blog/", "Back to Hub")
        footer = "© 2025 AI Profit Lab — a brand of Lotus Gulf International • All Rights Reserved"
    else:
        alt = f"{image_name} - حلول الذكاء الاصطناعي المبتكرة من AI Profit Lab لتطوير أعمالك."
        cta = ("هل أنت مستعد لأتمتة عمليات شركتك؟",
               "تساعد AI Profit Lab المديرين غير التقنيين في عُمان ودول الخليج على نشر حلول الذكاء الاصطناعي "
               "المخصصة، وأنظمة خدمة العملاء المؤتمتة، ولوحات المعلومات الفورية لتقليل النفقات العامة "
               "والتخلص من المهام اليدوية المكررة.", "احجز استشارة مجانية في الذكاء الاصطناعي لمدة 30 دقيقة")
        toc_title, refs_title, back = "جدول المحتويات", "المراجع", ("/blog-ar/", "العودة إلى المدونة")
        footer = "© ٢٠٢٥ AI Profit Lab — علامة تجارية تابعة لشركة Lotus Gulf International • جميع الحقوق محفوظة"
    body = "\n\n".join(prose)
    return f"""<!DOCTYPE html>
<html lang="{lang}" dir="{'ltr' if en else 'rtl'}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="category" content="{_e(d['category'])}">
    <title>{_e(d['title'])} | AI Profit Lab</title>
    <meta name="description" content="{_e(d['meta_description'])}">
    <meta name="keywords" content="{_e(d['keywords'])}">
    <link rel="canonical" href="{canon}">
    <link rel="icon" href="/favicon.ico" sizes="32x32">
    <link rel="icon" type="image/svg+xml" href="/favicon.svg?v=20260822">
    <link rel="apple-touch-icon" href="/apple-touch-icon.png?v=20260822">
    <link rel="manifest" href="/site.webmanifest?v=20260822">

    <!-- JSON-LD Schema Markup -->
    <script type="application/ld+json">
{_ld(graph)}
    </script>

    <!-- Local Business Schema (NAP) - copied verbatim from SKILL.md -->
    <script type="application/ld+json">
{_ld(nap)}
    </script>

    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="antialiased">
    <nav class="flex justify-between items-center px-6 py-8 w-full glass" id="header">
        <a href="{'/' if not en else '/en/'}">AI Profit Lab</a>
        <a href="{back[0]}">{back[1]}</a>
    </nav>

    <main class="max-w-4xl mx-auto px-6 py-16">
        <article>
            <div class="mb-12 text-center">
                <span class="bg-blue-500/10 text-blue-400 text-sm font-bold px-4 py-2 rounded-full">{_e(d['category'])}</span>
                <h1 class="text-4xl md:text-6xl font-extrabold mb-6 leading-tight">{_e(d['title'])}</h1>
                <p class="text-xl text-gray-400 max-w-2xl mx-auto">{_e(d['dek'])}</p>
            </div>

            <img src="{img_url}" alt="{_e(alt)}" class="w-full rounded-3xl mb-16 object-cover h-[500px]">

            <nav class="glass-card rounded-2xl p-6 mb-12 border border-blue-500/20" id="table-of-contents">
                <h2 class="text-xl font-bold text-white mb-4 mt-0">{toc_title}</h2>
                <ul class="space-y-2 text-gray-300 text-sm">
{toc}
                    <li><a href="#faq">{faq_label}</a></li>
                </ul>
            </nav>

            <div class="prose max-w-none">
{body}
            </div>

            <div class="glass-card rounded-2xl p-8 mt-12 mb-8 text-center border-blue-500/30 border">
                <h3 class="text-2xl font-bold text-white mb-4">{cta[0]}</h3>
                <p class="text-gray-300 mb-6">{cta[1]}</p>
                <a class="inline-block bg-blue-600 text-white font-bold py-3 px-8 rounded-full" href="{CONTACT[lang]}">{cta[2]}</a>
            </div>

            <section class="mt-16 pt-8 border-t border-white/10" id="faq">
                <h2 class="text-3xl font-extrabold mb-8">{faq_label}</h2>
                <div class="space-y-6">
{faqs}
                </div>
            </section>

            <hr class="border-gray-800 my-10">

            <div class="mt-8">
                <h3 class="text-xl font-bold mb-4 text-white">{refs_title}</h3>
                <ul class="list-disc list-inside text-gray-500 space-y-2 text-sm">
{refs}
                </ul>
            </div>
        </article>
    </main>

    <footer class="border-t border-white/10 bg-black py-8 text-center text-gray-500 text-sm">
        <p>{footer}</p>
    </footer>
</body>
</html>
"""


# ======================================================================
# References: fetch every URL before it ships
# ======================================================================
_URL_CACHE = {}


# Browser-like headers: developers.facebook.com answers 400 to anything else, for
# real pages and fake ones alike; with these it returns 200 vs 404 correctly.
BROWSER = {"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
           "Accept-Language": "en-US,en;q=0.9", "Sec-Fetch-Mode": "navigate", "Sec-Fetch-Dest": "document",
           "Sec-Fetch-Site": "none", "Upgrade-Insecure-Requests": "1"}
# Existence check only (the page is never trusted): oman2040.om serves an
# incomplete certificate chain that browsers repair and Python does not.
LOOSE_SSL = ssl.create_default_context()
LOOSE_SSL.check_hostname = False
LOOSE_SSL.verify_mode = ssl.CERT_NONE


def url_alive(url):
    if url in _URL_CACHE:
        return _URL_CACHE[url]
    ok, ctx = False, SSL
    for attempt in range(3):
        req = urllib.request.Request(url, headers=BROWSER)
        try:
            with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
                ok = r.status < 400
                break
        except urllib.error.HTTPError as e:
            # 404/410 = the page does not exist. 401/403/429 = it exists and refuses bots.
            ok = e.code in (401, 403, 429, 999)
            if e.code < 500:
                break
        except urllib.error.URLError as e:
            if isinstance(e.reason, ssl.SSLCertVerificationError) and ctx is SSL:
                ctx = LOOSE_SSL
                continue
            if attempt:
                break                       # DNS failure or timeout twice: dead
        except Exception:
            if attempt:
                break
    _URL_CACHE[url] = ok
    return ok


# ======================================================================
# Draft -> cleaned draft + rendered source + list of problems
# ======================================================================
def prepare(lang, raw, slug, date, image_name, corp, nap, modified=None):
    """Sanitise the model's JSON, verify its links, render it, audit it. Returns (d, src, problems)."""
    d = json.loads(json.dumps(raw))           # deep copy
    for k in ("title", "meta_description", "keywords", "category", "dek", "image_concept", "forum_snippet"):
        d[k] = _plain(d.get(k, ""))
    d["title"] = re.sub(r"\s*\|\s*AI Profit Lab\s*$", "", d["title"])
    links = set()
    d["intro_html"] = sanitise(d.get("intro_html"), lang, corp, links)
    secs = []
    for s in d.get("sections") or []:
        secs.append({"heading": _plain(s.get("heading")), "answer": _plain(s.get("answer")),
                     "body_html": sanitise(s.get("body_html"), lang, corp, links)})
    d["sections"] = secs
    d["faqs"] = [{"q": _plain(f.get("q")), "a": _plain(f.get("a"))} for f in d.get("faqs") or []
                 if _plain(f.get("q")) and _plain(f.get("a"))]

    # references: real URLs only, deduplicated; inline sources join the list (skill criterion 15)
    refs, seen = [], set()
    for r in d.get("references") or []:
        u = (r.get("url") or "").strip()
        if re.match(r"https?://", u) and u not in seen and not u.startswith(SITE):
            refs.append({"label": _plain(r.get("label")) or u, "url": u})
            seen.add(u)
    for u in sorted(links - seen):
        refs.append({"label": re.sub(r"^https?://(www\.)?", "", u).split("/")[0], "url": u})
    dead = [r["url"] for r in refs if not url_alive(r["url"])]
    if dead:
        log(f"    {lang}: dropping {len(dead)} dead reference(s): {', '.join(dead)}")
        d["intro_html"] = unlink(d["intro_html"], dead)
        for s in d["sections"]:
            s["body_html"] = unlink(s["body_html"], dead)
    d["references"] = [r for r in refs if r["url"] not in dead]

    src = render_source(lang, d, slug, date, image_name, nap, modified)
    return d, src, audit(lang, d, src)


def audit(lang, d, src):
    """The skill's criteria, checked on what the renderer will actually read."""
    p = []
    tmp = TMP / f"audit-{lang}.html"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(src, encoding="utf-8")
    doc = legacy.read(str(tmp))
    body_text = _plain(doc["body"])
    low = body_text.lower()

    lo, hi = WORDS[lang]
    if not lo <= doc["words"] <= hi:
        p.append(f"Body length is {doc['words']} words; it must be {lo}-{hi} (intro + answers + section "
                 f"bodies, not counting FAQs). {'Expand' if doc['words'] < lo else 'Tighten'} the sections.")
    if len(doc.get("faq") or []) != 10:
        p.append(f"There are {len(doc.get('faq') or [])} FAQs; there must be exactly 10.")
    if len(d["sections"]) < 3:
        p.append(f"Only {len(d['sections'])} sections; write 4 to 6.")
    qmark = "?" if lang == "en" else "؟"
    questions = sum(1 for s in d["sections"] if s["heading"].rstrip().endswith((qmark, "?")))
    if questions < 3:
        p.append(f"Only {questions} section headings are questions; at least 3 must end with '{qmark}'.")
    for s in d["sections"]:
        n = len(s["answer"].split())
        if not 15 <= n <= 80:
            p.append(f"The direct answer under '{s['heading'][:60]}' is {n} words; make it about 40.")
    if "<table" not in doc["body"]:
        p.append("No <table> in the body; add a comparison, ROI or before/after table.")
    if len(d["references"]) < MIN_VERIFIED_REFS:
        p.append(f"Only {len(d['references'])} references survived URL checking; cite at least 4 real, "
                 f"stable URLs (official docs, government portals, major publishers) and link each inline.")
    if not doc.get("hero", {}).get("src"):
        p.append("[renderer] hero image not found")
    if not doc.get("cta"):
        p.append("[renderer] CTA not found")

    t = d["title"]
    if len(t) <= 20:
        p.append("Title is too short (must be over 20 characters).")
    if lang == "en" and not TITLE_SPECIFIC.search(t):
        p.append("Title needs a specific number, location (Oman, Muscat, GCC...) or outcome (how to, cost, ROI, guide).")
    md = d["meta_description"]
    mlo, mhi = META_LEN[lang]
    if not mlo <= len(md) <= mhi:
        p.append(f"Meta description is {len(md)} characters; it must be {mlo}-{mhi}. Current: \"{md}\"")
    if md.lower().startswith(META_BAD_START):
        p.append("Meta description must not start with 'AI Profit Lab', 'Learn how', 'Discover' or 'Supercharge'.")

    if len(d["dek"]) < 40:
        p.append("The dek (subtitle under the title) must be one full sentence, 40+ characters.")
    if any(w in t.lower() for w in GENERIC_TITLE):
        p.append("Title uses a generic pattern banned by criterion 1; make it specific.")
    if lang == "en":
        for w in SLOP:
            for field, txt in (("title", t.lower()), ("body", low), ("dek", d["dek"].lower())):
                if re.search(r"\b" + re.escape(w), txt):
                    p.append(f"Banned phrase '{w}' in the {field}; rewrite it plainly.")
        first100 = " ".join(_plain(d["intro_html"]).lower().split()[:100])
        for w in SELF_PROMO:
            if re.search(r"\b" + re.escape(w) + r"\b", first100):
                p.append(f"The opening is self-promotional ('{w}'); open on the reader's problem.")
        gcc = {w for w in GCC_EN if re.search(r"\b" + re.escape(w) + r"\b", low)}
        if not any(w in md.lower() for w in GCC_EN):
            p.append("Meta description needs an Oman or GCC reference.")
    else:
        gcc = {w for w in GCC_AR if w in body_text}
        letters = re.findall(r"[A-Za-z؀-ۿ]", body_text)
        arabic = sum(1 for c in letters if "؀" <= c <= "ۿ")
        if letters and arabic / len(letters) < 0.75:
            p.append("The Arabic edition is not mostly Arabic text.")
    if len(gcc) < 3:
        p.append(f"Only {len(gcc)} distinct Oman/GCC references in the body ({', '.join(sorted(gcc)) or 'none'}); "
                 f"weave in at least 3 (e.g. Muscat, Vision 2040, PDPL, Sohar, OMR).")
    internal = re.findall(r'href="/blog/%s/' % lang, doc["body"])
    if not internal:
        p.append("No internal links to existing articles; add 2-3 from the list, exact URLs.")
    return sorted(set(p), key=p.index)


FACT_SYSTEM = """You are the fact-check editor of a company blog that is published with no human review,
under a real company's name. Your job is to stop invented facts.

List every claim in the article JSON that contains a number, percentage, statistic, rate, benchmark,
survey result, price, legal or regulatory reference, or a statement about what companies, engineers,
customers or markets "typically", "often" or "routinely" see. Classify each one:
- sourced: the article cites, inline, a reference that would plausibly state exactly this.
- illustrative: worked arithmetic or a scenario clearly framed as an example ("say you get 300 messages").
- recommendation: a target or threshold the article recommends, phrased as advice.
- general_knowledge: a stable fact you are certain is correct (e.g. a well-known law's decree number).
- unsupported: anything else: an empirical figure or observed trend with no real source, a figure pinned
  on a source that would not contain it, a claim about AI Profit Lab's own findings, clients or results,
  or a legal/regulatory specific you are not certain is correct.
Be strict. When unsure between unsupported and another kind, choose unsupported.
Quote each claim exactly as it appears. field = title, meta_description, dek, intro, section N, faq N or
forum_snippet."""

FACT_SCHEMA = {"type": "OBJECT", "properties": {"claims": {"type": "ARRAY", "items": {
    "type": "OBJECT", "properties": {
        "field": {"type": "STRING"}, "quote": {"type": "STRING"},
        "kind": {"type": "STRING", "enum": ["sourced", "illustrative", "recommendation",
                                            "general_knowledge", "unsupported"]},
        "why": {"type": "STRING"}},
    "required": ["field", "quote", "kind", "why"]}}}, "required": ["claims"]}


def fact_check(lang, d):
    """A second, adversarial pass: every unsupported figure becomes a revision problem."""
    keys = ("title", "meta_description", "dek", "intro_html", "sections", "faqs", "references",
            "forum_snippet")
    res = gemini_json(FACT_SYSTEM, json.dumps({k: d[k] for k in keys}, ensure_ascii=False),
                      FACT_SCHEMA, f"{lang} fact-check")
    claims = res.get("claims") or []
    bad = [c for c in claims if c.get("kind") == "unsupported"]
    log(f"    fact-check: {len(claims)} claims, {len(bad)} unsupported")
    return [f'Unsupported claim in {c.get("field", "?")}: "{_plain(c.get("quote", ""))[:220]}" ({_plain(c.get("why", ""))[:200]}). '
            "Delete it, cite a reference that really states it, or rewrite it as clearly illustrative "
            "arithmetic or as a recommendation." for c in bad]


def write_language(lang, prompt, slug, date, image_name, corp, nap, modified=None):
    """Generate -> audit -> fact-check -> revise, up to ATTEMPTS. Returns (d, src) or raises.

    The latest model reply is kept in .tmp/daily_publish/<slug>/cache/<lang>.raw.json, so a
    run stopped by an outage resumes from it instead of paying for the draft again."""
    system = system_prompt()
    raw_file = TMP / slug / "cache" / f"{lang}.raw.json"
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    if raw_file.exists():
        raw = json.loads(raw_file.read_text(encoding="utf-8"))
        log(f"  {lang}: resuming from the last draft in {raw_file.parent}")
    else:
        raw = gemini_json(system, prompt, ARTICLE_SCHEMA, f"{lang} draft 1")
        raw_file.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    for attempt in range(1, ATTEMPTS + 1):
        d, src, problems = prepare(lang, raw, slug, date, image_name, corp, nap, modified)
        doc_words = legacy.read(str(TMP / f"audit-{lang}.html"))["words"]
        log(f"  {lang} attempt {attempt}: {doc_words} words, {len(d['faqs'])} FAQs, "
            f"{len(d['references'])} refs, {len(problems)} problem(s)")
        if not problems:
            problems = fact_check(lang, d)
        if not problems:
            return d, src
        for x in problems:
            log(f"      - {x}")
        if any(x.startswith("[renderer]") for x in problems):
            raise PublishError(f"{lang}: the source template no longer matches the renderer: {problems}")
        if attempt == ATTEMPTS:
            break
        raw = gemini_json(system, revise_prompt(prompt, raw, problems), ARTICLE_SCHEMA,
                          f"{lang} revision {attempt}")
        raw_file.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    raw_file.unlink()                      # it failed for real; the next run starts fresh
    raise PublishError(f"{lang} draft still fails after {ATTEMPTS} attempts: " + " | ".join(problems))


# ======================================================================
# Hero image
# ======================================================================
IMAGE_STYLE = """Editorial hero photograph for a business article. 16:9, landscape.
Style: bright light-mode editorial photography, soft directional daylight, clean and expensive feel,
semi-realistic. Background: clean light cream / off-white (#F1EFE8, #FAF8F2) filling the frame.
Palette: cream, off-white, deep teal (#0F6E56) accents, subtle amber (#BA7517) highlights.
Strictly avoid: dark mode, dark or black backgrounds, neon, glowing eyes, sci-fi or cyberpunk clutter,
generic stock-photo look, any text, letters, numbers, logos, watermarks, or screens with readable text."""


def vet_image(data):
    """(PNG bytes ready to publish or None, problems, 'WxH, luminance N'). The same bar for
    every source: this script's image models and Antigravity's image tool."""
    try:
        from PIL import Image, ImageStat
    except ImportError:
        raise PublishError("Pillow is required: python3 -m pip install Pillow")
    try:
        im = Image.open(io.BytesIO(data))
        im.load()
    except Exception as e:
        return None, [f"not a decodable image ({e})"], "unreadable"
    rgb = im.convert("RGB")
    lum = ImageStat.Stat(rgb.convert("L")).mean[0]
    info = f"{rgb.width}x{rgb.height}, luminance {lum:.0f}"
    problems = []
    if rgb.width < 1000:
        problems.append(f"only {rgb.width}px wide (needs 1000+)")
    if rgb.width < rgb.height * 1.3:
        problems.append("not a wide landscape frame (use 16:9)")
    if lum < 120:
        problems.append(f"too dark for the light-mode brand (mean luminance {lum:.0f}/255, needs 120+)")
    if problems:
        return None, problems, info
    if rgb.width > 1600:                       # the largest rung served is 1200px
        rgb = rgb.resize((1600, round(rgb.height * 1600 / rgb.width)), Image.LANCZOS)
    out = io.BytesIO()
    rgb.save(out, "PNG", optimize=True)
    return out.getvalue(), [], info


def make_image(concept, title):
    problems = []
    for attempt in range(1, ATTEMPTS + 1):
        prompt = f"{IMAGE_STYLE}\n\nArticle: {title}\nScene: {concept}"
        if problems:
            prompt += "\n\nThe previous image was rejected: " + "; ".join(problems)
        data, model = generate_image(prompt)
        png, problems, info = vet_image(data)
        log(f"  image attempt {attempt} ({model}): {info}"
            + (f" -> rejected: {'; '.join(problems)}" if problems else " -> ok"))
        if png:
            return png
    raise PublishError(f"No acceptable hero image after {ATTEMPTS} attempts: {'; '.join(problems)}")


def add_pending_hero(g):
    """Queue a placeholder-hero article for Antigravity (agent_publish.py swaps the real one in)."""
    data = json.loads(PENDING_HEROES.read_text(encoding="utf-8")) if PENDING_HEROES.exists() else {}
    data[g["slug"]] = {"date": g["date"], "image_name": g["image_name"], "title": g["en"]["title"],
                       "concept": g["en"]["image_concept"]}
    PENDING_HEROES.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                              encoding="utf-8")


def image_name_for(slug, png):
    # A new image always gets a new URL: /blog/images/ is served as immutable
    # for a year, so overwriting a file in place never reaches visitors.
    short = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", slug)
    if len(short) > 48:
        short = short[:48].rsplit("-", 1)[0]          # whole words only
    return f"{short}-{hashlib.sha256(png).hexdigest()[:6]}"


# ======================================================================
# Build: the skill's Steps 5-7 with exit codes enforced
# ======================================================================
def run(cmd, cwd=ROOT):
    log(f"  $ {' '.join(str(c) for c in cmd)}")
    r = subprocess.run([str(c) for c in cmd], cwd=cwd, capture_output=True, text=True)
    tail = (r.stdout + r.stderr).strip().splitlines()[-6:]
    for line in tail:
        log(f"      {line}")
    if r.returncode != 0:
        raise PublishError(f"{' '.join(str(c) for c in cmd[1:2])} exited {r.returncode}")
    return r.stdout


def build(slug):
    py = sys.executable
    run([py, "tools/build_image_derivatives.py"])
    run([py, "tools/reskin_articles.py", "--only", slug])
    for lang in ("en", "ar"):
        s = (BLOG / lang / f"{slug}.html").read_text(encoding="utf-8")
        checks = {"tailwind": s.count("cdn.tailwindcss.com") == 0, "brand css": "apl-article" in s,
                  "hero figure": s.count('class="afig"') == 1, "hreflang pair": 'hreflang="ar"' in s
                  and 'hreflang="en"' in s, "derivative hero": "-1200.webp" in s}
        bad = [k for k, ok in checks.items() if not ok]
        if bad:
            raise PublishError(f"Rendered {lang} page failed: {', '.join(bad)}")
    run([py, "tools/reskin_blog_hubs.py"])
    run([py, "run_sitemap.py"])
    run([py, "tools/build_aiden_index.py"])
    for hub, lang in (("blog/index.html", "en"), ("blog-ar/index.html", "ar")):
        if slug not in (PUBLIC / hub).read_text(encoding="utf-8"):
            raise PublishError(f"{hub} does not list {slug}")
    if f"/blog/en/{slug}/" not in (PUBLIC / "sitemap.xml").read_text(encoding="utf-8"):
        raise PublishError(f"sitemap.xml does not list {slug}")


# ======================================================================
# Topics: pick the next one, refill the queue when it runs dry
# ======================================================================
TOPIC_SCHEMA = {"type": "OBJECT", "properties": {"topics": {"type": "ARRAY", "items": {
    "type": "OBJECT", "properties": {"cluster": {"type": "STRING"}, "en_title": {"type": "STRING"},
                                     "ar_title": {"type": "STRING"}},
    "required": ["cluster", "en_title", "ar_title"]}}}, "required": ["topics"]}


def refill_queue(rows, corp):
    # Searches people in Oman really make come first (execution/trend_topics.py). Topics the
    # model invents are only the fallback, for a run where that research comes back empty.
    try:
        import trend_topics
        new = trend_topics.top_up(sys.modules[__name__], corp, rows, REFILL_COUNT)
        if new:
            return new
        log("  trend research found no usable topic; asking the model to propose some")
    except TransientError:
        raise
    except Exception as e:
        log(f"  trend research failed ({e}); asking the model to propose topics")
    clusters = sorted({r["cluster"] for r in rows if r["cluster"]})
    titles = "\n".join(f"- {t}" for t in corp["en"].values())
    prompt = (f"Propose {REFILL_COUNT * 2} new article topics for the AI Profit Lab blog. Each must serve "
              f"an Omani/GCC small or mid-sized business owner, have clear search intent, and follow "
              f"criterion 1 of the skill (specific number, location or outcome; no generic phrasing; no "
              f"banned words). Spread them over these clusters (use the names exactly): "
              f"{'; '.join(clusters)}.\nEach needs an English title and a natural Arabic title.\n"
              f"They must NOT overlap any published article:\n{titles}\n")
    res = gemini_json(system_prompt(), prompt, TOPIC_SCHEMA, "topic refill")
    taken = list(corp["en"].values()) + [r["en_title"] for r in rows]
    nums = [int(r["num"]) for r in rows if r["num"].isdigit()]
    nxt, new = (max(nums) + 1 if nums else 1), []
    for t in res.get("topics", []):
        en, ar, cl = _plain(t.get("en_title")), _plain(t.get("ar_title")), _plain(t.get("cluster"))
        if not en or not ar or "|" in en + ar + cl or not TITLE_SPECIFIC.search(en):
            continue
        if any(re.search(r"\b" + re.escape(w), en.lower()) for w in SLOP + GENERIC_TITLE):
            continue
        if max((similarity(en, x) for x in taken), default=0) > SIMILARITY_LIMIT:
            continue
        new.append({"num": str(nxt), "cluster": cl or clusters[0], "en_title": en, "ar_title": ar,
                    "status": "Pending", "date": "-", "url": "-"})
        taken.append(en)
        nxt += 1
        if len(new) == REFILL_COUNT:
            break
    if new:
        append_queue_rows(new)
        log(f"  queue refilled with {len(new)} topic(s): " + "; ".join(r["en_title"] for r in new))
    return new


def next_topic(corp):
    """First Pending row that passes the skill's Step 0 similarity pre-check."""
    _, rows = read_queue()
    if sum(r["status"].lower() == "pending" for r in rows) < REFILL_BELOW:
        refill_queue(rows, corp)
        _, rows = read_queue()
    for r in rows:
        if r["status"].lower() != "pending":
            continue
        score, slug = closest(r["en_title"], corp["en"])
        if score > SIMILARITY_LIMIT:
            log(f"  pushback (Step 0): '{r['en_title']}' is {score:.0%} similar to {slug}; skipping it")
            r.update(status="Skipped", url=f"duplicate of {slug} ({score:.0%})")
            update_queue_row(r)
            continue
        return r
    raise PublishError("No publishable topic in directives/article_queue.md (and the refill found none).")


def slugify(title, limit=60):
    s = re.sub(r"[^a-z0-9\s-]", "", title.lower())
    s = re.sub(r"[\s-]+", "-", s).strip("-")
    if len(s) > limit:
        s = s[:limit].rsplit("-", 1)[0]       # whole words only
    return s


# ======================================================================
# Publish
# ======================================================================
def generate(topic, slug, date, corp, modified=None):
    """Both languages + image, into memory. Nothing is written to public_html here."""
    nap = nap_block()
    exclude = {slug}
    links = link_candidates(topic["en_title"] + " " + topic["cluster"], corp, exclude)
    placeholder = "pending-image"
    # Each stage is cached as soon as it passes, so a run that fails later (the
    # image, the build) does not pay for the text again when it is re-run.
    cache = TMP / slug / "cache"
    cache.mkdir(parents=True, exist_ok=True)

    def cached(lang):
        f = cache / f"{lang}.json"
        if not f.exists():
            return None
        d, _, problems = prepare(lang, json.loads(f.read_text(encoding="utf-8")), slug, date,
                                 placeholder, corp, nap, modified)
        if problems:
            return None
        log(f"  {lang}: reusing the validated draft cached in {f.parent}")
        return d

    log(f"\n[1/3] English draft  ({', '.join(TEXT_MODELS)})")
    en_d = cached("en")
    if not en_d:
        en_p = en_prompt(topic, slug, date, corp, links)
        en_d, _ = write_language("en", en_p, slug, date, placeholder, corp, nap, modified)
        (cache / "en.json").write_text(json.dumps(en_d, ensure_ascii=False), encoding="utf-8")
    log("\n[2/3] Arabic edition")
    ar_d = cached("ar")
    if not ar_d:
        ar_p = ar_prompt(topic, slug, date, corp, links, en_d)
        ar_d, _ = write_language("ar", ar_p, slug, date, placeholder, corp, nap, modified)
        (cache / "ar.json").write_text(json.dumps(ar_d, ensure_ascii=False), encoding="utf-8")
    log(f"\n[3/3] Hero image  ({', '.join(IMAGE_PROVIDERS)})")
    temp = IMAGE_PROVIDERS[0].strip() == "placeholder"
    if temp:
        png = PLACEHOLDER_HERO.read_bytes()
        log("  placeholder hero; the article goes into pending_heroes.json for Antigravity to illustrate")
    elif (cache / "hero.png").exists():
        png = (cache / "hero.png").read_bytes()
        log(f"  reusing the checked image cached in {cache}")
    else:
        png = make_image(en_d["image_concept"], en_d["title"])
        (cache / "hero.png").write_bytes(png)
    name = image_name_for(slug, png)
    srcs = {lang: render_source(lang, d, slug, date, name, nap, modified)
            for lang, d in (("en", en_d), ("ar", ar_d))}
    return {"slug": slug, "date": date, "image_name": name, "png": png, "en": en_d, "ar": ar_d,
            "src": srcs, "temp_image": temp}


def save_draft(g, folder):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "hero.png").write_bytes(g["png"])
    for lang in ("en", "ar"):
        (folder / f"{lang}.html").write_text(g["src"][lang], encoding="utf-8")
        (folder / f"{lang}.json").write_text(json.dumps(g[lang], ensure_ascii=False, indent=2),
                                             encoding="utf-8")
    meta = {k: g.get(k) for k in ("slug", "date", "image_name", "row_num", "temp_image")}
    (folder / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


def load_draft(folder):
    meta = json.loads((folder / "meta.json").read_text())
    g = dict(meta, png=(folder / "hero.png").read_bytes(),
             src={l: (folder / f"{l}.html").read_text(encoding="utf-8") for l in ("en", "ar")})
    for lang in ("en", "ar"):
        g[lang] = json.loads((folder / f"{lang}.json").read_text(encoding="utf-8"))
    return g


def install(g):
    """Write the article into public_html/ and build. Rolled back if any step fails."""
    slug = g["slug"]
    targets = [BLOG / "en" / f"{slug}.html", BLOG / "ar" / f"{slug}.html"]
    backup = {t: t.read_bytes() for t in targets if t.exists()}
    img = IMAGES / f"{g['image_name']}.png"
    try:
        img.write_bytes(g["png"])
        for lang, t in zip(("en", "ar"), targets):
            t.write_text(g["src"][lang], encoding="utf-8")
        build(slug)
    except Exception:
        log("  build failed; restoring the previous article files")
        for f in IMAGES.glob(f"{g['image_name']}*"):
            f.unlink()
        for t in targets:
            if t in backup:
                t.write_bytes(backup[t])
            elif t.exists():
                t.unlink()
        raise


def record(g, row, repair_row=None):
    for lang in ("en", "ar"):
        url = f"{SITE}/blog/{lang}/{g['slug']}/"
        if url not in g[lang]["forum_snippet"]:
            g[lang]["forum_snippet"] = g[lang]["forum_snippet"].rstrip() + " " + url
    snippet = (f"\n## {g['date']} — {g['en']['title']}\n\n**EN:** {g['en']['forum_snippet']}\n\n"
               f"**AR:** {g['ar']['forum_snippet']}\n")
    if not SNIPPETS_FILE.exists():
        SNIPPETS_FILE.write_text("# Forum snippets\n\nOne per published article (skill Step 8), newest last. "
                                 "Paste into GCC business forums, LinkedIn groups or WhatsApp communities.\n",
                                 encoding="utf-8")
    with SNIPPETS_FILE.open("a", encoding="utf-8") as f:
        f.write(snippet)
    if g.get("temp_image"):
        add_pending_hero(g)
    if row:
        row.update(status=TEMP_IMAGE_STATUS if g.get("temp_image") else "Published", date=g["date"],
                   url=f"[{g['slug']}]({SITE}/blog/en/{g['slug']}/)")
        update_queue_row(row)
    if repair_row:
        repair_row.update(status=f"Published (rebuilt {today()})")
        update_queue_row(repair_row)


def outputs(**kv):
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a") as f:
            for k, v in kv.items():
                f.write(f"{k}={v}\n")


def summary(g, extra=""):
    lines = [f"### {g['en']['title']}", "",
             f"- EN: {SITE}/blog/en/{g['slug']}/", f"- AR: {SITE}/blog/ar/{g['slug']}/",
             f"- Hero: /blog/images/{g['image_name']}.png",
             f"- FAQs: {len(g['en']['faqs'])} / {len(g['ar']['faqs'])}, references: "
             f"{len(g['en']['references'])} / {len(g['ar']['references'])}",
             f"- Tokens: {USAGE['prompt']:,} in, {USAGE['output']:,} out, {USAGE['thoughts']:,} thinking; "
             f"images: {USAGE['images']}", "", "**Forum snippet (EN):** " + g["en"]["forum_snippet"], extra]
    text = "\n".join(lines)
    log("\n" + text)
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(text + "\n")


def already_published(date):
    return sorted(p.stem for p in (BLOG / "en").glob(f"{date}-*.html"))


def find_row_for(slug):
    _, rows = read_queue()
    return next((r for r in rows if slug in r["url"]), None)


def next_repair_row():
    """First row marked `Repair`: an already-published article to rebuild in place."""
    _, rows = read_queue()
    for r in rows:
        m = re.search(r"\[(\d{4}-\d{2}-\d{2}-[a-z0-9-]+)\]", r["url"])
        if r["status"].lower() == "repair" and m and (BLOG / "en" / f"{m.group(1)}.html").exists():
            return r, m.group(1)
    return None, None


def cmd_publish(a):
    date = today()
    corp = corpus()
    row = repair_row = None
    if not a.repair and not a.from_dir and already_published(date) and not a.force:
        if a.no_repair:
            # The evening fallback: Antigravity already published today, and repairs are its job.
            log(f"Already published today ({date}): {already_published(date)[0]}. Nothing to do.")
            outputs(published="false")
            return
        # Today's article is out. The day's later slots rebuild one `Repair` row each.
        repair_row, a.repair = next_repair_row()
        if not a.repair:
            log(f"Already published today ({date}): {already_published(date)[0]}. No `Repair` rows "
                f"queued. Nothing to do. (--force publishes another article.)")
            outputs(published="false")
            return
    if a.repair:
        slug = a.repair.strip().strip("/").split("/")[-1].removesuffix(".html")
        if not (BLOG / "en" / f"{slug}.html").exists():
            raise PublishError(f"--repair: no article named {slug}")
        row = find_row_for(slug)
        if row and row["status"].lower() == "repair":
            repair_row = row                     # a manual run clears the queued rebuild too
        topic = ({"en_title": row["en_title"], "ar_title": row["ar_title"], "cluster": row["cluster"]}
                 if row else {"en_title": corp["en"][slug], "ar_title": corp["ar"].get(slug, ""),
                              "cluster": ""})
        pub_date, modified, row = slug[:10], date, None      # keep the URL and the original date
        log(f"Repairing {slug} ({topic['en_title']})")
    else:
        done = already_published(date)
        if done and not a.force:
            log(f"Already published today ({date}): {done[0]}. Nothing to do. (--force overrides.)")
            outputs(published="false")
            return
        row = None if a.from_dir else next_topic(corp)
        topic = row
        slug, pub_date, modified = (f"{date}-{slugify(row['en_title'])}" if row else None), date, None
        if row:
            log(f"Topic #{row['num']}: {row['en_title']}\nSlug: {slug}")

    if a.from_dir:
        g = load_draft(Path(a.from_dir))
        if a.repair and g["slug"] != slug:
            raise PublishError(f"{a.from_dir} holds {g['slug']}, not {slug}")
        if not a.repair:
            _, rows = read_queue()
            row = next((r for r in rows if r["num"] == str(g.get("row_num"))), None)
            if not row or row["status"].lower() != "pending":
                raise PublishError(f"{a.from_dir}: its queue row #{g.get('row_num')} is not Pending")
        log(f"Using the reviewed draft in {a.from_dir} (no API calls)")
    else:
        g = generate(topic, slug, pub_date, corp, modified)
        g["row_num"] = row["num"] if row else None

    folder = TMP / g["slug"]
    if not a.from_dir:
        save_draft(g, folder)
    if a.dry_run:
        summary(g, f"\nDry run: nothing published. Review {folder}/ then publish it with:\n"
                   f"  python3 execution/daily_publish.py --from-dir \"{folder}\""
                   + (f" --repair {slug}" if a.repair else ""))
        outputs(published="false")
        return

    log("\nBuilding (skill Steps 5-7)")
    install(g)
    record(g, row, repair_row)
    summary(g)
    outputs(published="true", slug=g["slug"], kind="Repair" if a.repair else "Publish")


def cmd_verify(slug, wait=600):
    """Poll the live site until both pages and the hero answer correctly."""
    deadline = time.time() + wait
    while True:
        problems = []
        for lang in ("en", "ar"):
            url = f"{SITE}/blog/{lang}/{slug}/?cb={int(time.time())}"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=30, context=SSL) as r:
                    page = r.read().decode("utf-8", "replace")
            except Exception as e:
                problems.append(f"{lang}: {e}")
                continue
            if "apl-article" not in page:
                problems.append(f"{lang}: page is not on the brand skin")
            m = re.search(r'<img[^>]+src="(/blog/images/[^"]+-1200\.webp)"', page)
            if not m:
                problems.append(f"{lang}: no hero image in the page")
            elif lang == "en":
                try:
                    req = urllib.request.Request(SITE + m.group(1), method="HEAD", headers={"User-Agent": UA})
                    with urllib.request.urlopen(req, timeout=30, context=SSL) as r:
                        if not r.headers.get("Content-Type", "").startswith("image/"):
                            problems.append("hero URL is not an image")
                except Exception as e:
                    problems.append(f"hero image: {e}")
            words = len(_plain(re.search(r'<article class="prose".*?</article>', page, re.S).group(0)).split()) \
                if 'class="prose"' in page else 0
            if words < WORDS[lang][0]:
                problems.append(f"{lang}: only {words} words live")
        if not problems:
            log(f"Live and correct: {SITE}/blog/en/{slug}/ and /blog/ar/{slug}/")
            return
        if time.time() > deadline:
            raise PublishError("Live check failed: " + "; ".join(problems))
        log("  not live yet: " + "; ".join(problems) + " (retrying in 30s)")
        time.sleep(30)


def cmd_preflight():
    try:
        import PIL  # noqa: F401
    except ImportError:
        raise PublishError("Pillow is missing: python3 -m pip install Pillow")
    nap_block(), skill_criteria()
    providers = [p.strip() for p in IMAGE_PROVIDERS]
    res = _http_json(f"{API}/models?pageSize=1000", timeout=60)
    have = {m["name"].split("/", 1)[1] for m in res.get("models", [])}
    for kind, models in (("text", TEXT_MODELS), ("image", IMAGE_MODELS)):
        if kind == "image" and "gemini" not in providers:
            continue
        ok = [m for m in models if m.strip() in have]
        if not ok:
            raise PublishError(f"None of the {kind} models are available to this key: {models}")
        log(f"  {kind} models available: {', '.join(ok)}")
    if providers[0] == "placeholder":
        if not PLACEHOLDER_HERO.exists():
            raise PublishError(f"The placeholder hero is missing: {PLACEHOLDER_HERO}")
        log("  images: placeholder hero; Antigravity swaps in the real one (pending_heroes.json)")
        log("Preflight OK: key accepted, skill readable, Pillow installed.")
        return
    if providers[0] == "kie" and not os.environ.get("KIE_AI_API_KEY", "").strip():
        # Fail here, before the text quota is spent: Gemini's image models are 0/day on the
        # free tier, so without kie.ai the run would die at the image step.
        raise PublishError("KIE_AI_API_KEY is not set. Add it as a repository secret (Settings > "
                           "Secrets and variables > Actions), or enable Gemini billing and set "
                           "IMAGE_PROVIDERS=gemini.")
    credit = None
    try:
        credit = kie_credit()
    except Exception as e:
        log(f"  kie.ai credit check failed: {e}")
    if "kie" in IMAGE_PROVIDERS and credit is not None:
        log(f"  kie.ai credit: {credit}")
        if credit < 50 and "gemini" not in IMAGE_PROVIDERS:
            raise PublishError(f"kie.ai credit is down to {credit}; top up at kie.ai.")
    elif "gemini" in IMAGE_PROVIDERS:
        log("  images: Gemini only (no KIE_AI_API_KEY). Gemini image models need billing enabled.")
    log("Preflight OK: key accepted, skill readable, Pillow installed.")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dry-run", action="store_true", help="generate and validate into .tmp/ only")
    ap.add_argument("--from-dir", help="publish a reviewed dry-run folder without calling the API")
    ap.add_argument("--repair", metavar="SLUG", help="regenerate an existing article at the same URL")
    ap.add_argument("--force", action="store_true", help="publish even if today already has an article")
    ap.add_argument("--no-repair", action="store_true",
                    help="if today already has an article, stop instead of rebuilding a Repair row")
    ap.add_argument("--verify", metavar="SLUG", help="check the live pages after a deploy")
    ap.add_argument("--preflight", action="store_true")
    a = ap.parse_args()
    try:
        if a.preflight:
            cmd_preflight()
        elif a.verify:
            cmd_verify(a.verify)
        else:
            cmd_publish(a)
    except TransientError as e:
        log(f"\nPOSTPONED: {e}\nNothing was published; a later run today resumes from the cache.")
        sys.exit(EXIT_TEMPFAIL)
    except PublishError as e:
        log(f"\nFAILED: {e}\nNothing was published and the queue is unchanged.")
        sys.exit(1)


if __name__ == "__main__":
    main()
