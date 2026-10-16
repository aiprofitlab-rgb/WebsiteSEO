#!/usr/bin/env python3
"""
The daily article publisher, run by a Google Antigravity agent on Nahid's Mac.

Antigravity (Gemini on the Google AI Pro plan) does the two jobs that need a model:
it writes the article and it generates the hero image with its own image tool. This
script does everything that must not depend on a model's judgement. It picks the job,
hands the agent a brief, audits each draft against the article-creator skill, checks
every figure against a claims ledger and its sources, checks the image, builds the
pages, commits, pushes (deploy.yml uploads the push) and checks the live pages.

    python3 execution/agent_publish.py next           # this run's job and its brief: start here
    python3 execution/agent_publish.py topics-add     # queue the titles the agent wrote
    python3 execution/agent_publish.py check en       # audit agent_jobs/<slug>/en.json + claims-en.json
    python3 execution/agent_publish.py check ar
    python3 execution/agent_publish.py image PATH     # check and store the generated hero
    python3 execution/agent_publish.py publish        # final checks, build, commit, push, live check
    python3 execution/agent_publish.py fail "why"     # give up on this job for now
    python3 execution/agent_publish.py status
    python3 execution/agent_publish.py trigger [--dry-run]   # the scheduler's entry point

Agent instructions: directives/antigravity_publisher.md. Setup (the clone, the
Antigravity project and the hourly schedule): execution/setup_antigravity_publisher.py.

It runs ONLY in the publisher's own clone (~/Developer/aiprofitlab-publisher), never in
the checkout Nahid works in, because every job starts by resetting the clone to
origin/main. A clone is recognised by `git config apl.publisher true`.

Which job, in order: (1) an article the GitHub fallback published with a placeholder
hero gets its real image; (2) today's new article, started between 06:00 and 19:00
Muscat (GitHub's fallback runs at 20:17 and only if nothing is out); (3) up to two
`Repair` rows a day. Two failed attempts park a job until tomorrow.
"""

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                                   # .../Website SEO
REPO = ROOT.parent


def _ensure_pillow():
    """Antigravity's terminal may find a python3 without Pillow (the build needs it):
    re-run under the first interpreter that has Pillow and certifi."""
    try:
        import PIL  # noqa: F401
        import certifi  # noqa: F401
        return
    except ImportError:
        pass
    if os.environ.get("APL_REEXEC"):
        sys.exit("No python3 with Pillow and certifi found. Install them: python3 -m pip install Pillow certifi")
    cands = sorted(Path("/Library/Frameworks/Python.framework/Versions").glob("3.*/bin/python3"), reverse=True)
    cands += [Path(p) for p in ("/opt/homebrew/bin/python3", "/usr/local/bin/python3", "/usr/bin/python3")]
    for py in cands:
        if py.exists() and subprocess.run([str(py), "-c", "import PIL, certifi, zoneinfo"],
                                          capture_output=True).returncode == 0:
            os.environ["APL_REEXEC"] = "1"
            os.execv(str(py), [str(py), __file__, *sys.argv[1:]])
    sys.exit("No python3 with Pillow and certifi found. Install them: python3 -m pip install Pillow certifi")


_ensure_pillow()

import argparse  # noqa: E402
import html  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
import shutil  # noqa: E402
import time  # noqa: E402
import urllib.error  # noqa: E402
import urllib.request  # noqa: E402
from datetime import datetime, timedelta  # noqa: E402
from html.parser import HTMLParser  # noqa: E402

sys.path.insert(0, str(HERE))
import daily_publish as dp  # noqa: E402
import trend_topics as tt  # noqa: E402

# Not gitignored on purpose: Antigravity's agent cannot open gitignored files.
JOBS = ROOT / "agent_jobs"
STATE = JOBS / "state.json"
LOCK = JOBS / "run.lock"
LOG = JOBS / "log.md"
TOPICS = JOBS / "topics"
DIRECTIVE = "directives/antigravity_publisher.md"
CMD = "python3 execution/agent_publish.py"

NEW_WINDOW = (6, 19)           # Muscat hours in which the Mac may START the day's new article
MAX_REPAIRS_PER_DAY = 2
MAX_FAILS = 2                  # failed attempts per job per day, then it waits for tomorrow
MAX_LAUNCHES = 3               # conversations started for one job per day
LOCK_TTL = 3 * 3600            # a run that has not finished after this is presumed dead
MAX_GENERAL = 8                # "general_knowledge" figures allowed per language
MODEL = os.environ.get("APL_MODEL", "pro")


class Stop(Exception):
    """Nothing to do, or a step the agent has to fix. Printed, exit code 1 unless set."""

    def __init__(self, msg, code=1):
        super().__init__(msg)
        self.code = code


def log(msg=""):
    print(msg, flush=True)


def now_muscat():
    return datetime.now(dp.TZ)


def journal(msg):
    """One line per event in agent_jobs/log.md, for Nahid to read."""
    JOBS.mkdir(parents=True, exist_ok=True)
    if not LOG.exists():
        LOG.write_text("# Antigravity publisher log\n\nNewest last. Muscat time.\n\n", encoding="utf-8")
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"- {now_muscat():%Y-%m-%d %H:%M} {msg}\n")


# ======================================================================
# State
# ======================================================================
def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"job": None, "days": {}}


def save_state(st):
    JOBS.mkdir(parents=True, exist_ok=True)
    keep = sorted(st.get("days", {}))[-14:]
    st["days"] = {k: st["days"][k] for k in keep}
    STATE.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")


def day(st, date=None):
    return st.setdefault("days", {}).setdefault(date or dp.today(), {
        "new": None, "repairs": [], "heroes": [], "fails": {}, "launches": {}})


def job_key(job):
    return f"{job['kind']}:{job.get('slug') or job.get('date')}"


def fail_key(job):
    """Failures of today's article and of the topic research that feeds it count together."""
    return f"new:{job['date']}" if job["kind"] in ("new", "topics") else job_key(job)


def lock_age():
    try:
        return time.time() - float(LOCK.read_text().split()[0])
    except (OSError, ValueError, IndexError):
        return None


def take_lock(label):
    """Exclusive: two Antigravity hosts (the IDE and the app) may both fire the schedule."""
    JOBS.mkdir(parents=True, exist_ok=True)
    age = lock_age()
    if age is not None and age > LOCK_TTL:
        LOCK.unlink(missing_ok=True)
    try:
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False
    with os.fdopen(fd, "w") as f:
        f.write(f"{time.time():.0f} {label}\n")
    return True


def refresh_lock(label):
    """A run started by hand holds the lock too, so the hourly trigger never resets the clone under it."""
    JOBS.mkdir(parents=True, exist_ok=True)
    LOCK.write_text(f"{time.time():.0f} {label}\n")


def release_lock():
    LOCK.unlink(missing_ok=True)


# ======================================================================
# Git: the clone always starts from what is live on GitHub
# ======================================================================
def git(*args, check=True):
    r = subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True)
    if check and r.returncode:
        raise Stop(f"git {' '.join(args)} failed: {(r.stderr or r.stdout).strip()[:400]}")
    return r.stdout.strip()


def assert_clone():
    if git("config", "--get", "apl.publisher", check=False) != "true":
        raise Stop(f"This is not the publisher's clone ({REPO}). agent_publish.py resets its checkout to "
                   f"origin/main, so it refuses to run anywhere else. Set it up with "
                   f"execution/setup_antigravity_publisher.py.")


def sync():
    """Fetch and move to origin/main. A commit that never reached GitHub is pushed first."""
    if os.environ.get("APL_NO_SYNC"):
        return
    git("fetch", "--quiet", "origin", "main")
    if git("rev-parse", "--abbrev-ref", "HEAD") != "main":
        git("checkout", "--quiet", "main")
    if int(git("rev-list", "--count", "origin/main..HEAD") or 0):
        r = subprocess.run(["git", "rebase", "origin/main"], cwd=REPO, capture_output=True, text=True)
        if r.returncode:
            git("rebase", "--abort", check=False)
            raise Stop("A publish commit from an earlier run conflicts with GitHub's main. Nahid has to "
                       f"resolve it in {REPO}.", code=1)
        git("push", "--quiet", "origin", "HEAD:main")
        journal("pushed a commit an earlier run had left behind")
    git("reset", "--quiet", "--hard", "origin/main")
    # Files an interrupted build left behind would otherwise ride along in the next commit.
    git("clean", "-fdq", "--", "Website SEO/public_html", "Website SEO/directives")


def freshen_derivatives():
    """A checkout gives every file an arbitrary mtime, and tools/build_image_derivatives.py trusts
    mtimes: in a fresh clone it rebuilt 510 thumbnails and changed the bytes of a dozen, which
    would ride along in every publish commit. Existing derivatives count as current; only missing
    ones (the new hero's) get built."""
    sys.path.insert(0, str(ROOT / "tools"))
    import build_image_derivatives as bid
    now = time.time()
    for p in dp.IMAGES.iterdir():
        if bid.is_derivative(p):
            os.utime(p, (now, now))


def commit_and_push(message, paths=("Website SEO/public_html", "Website SEO/directives")):
    if os.environ.get("APL_NO_SYNC"):
        log("  (APL_NO_SYNC: not committing)")
        return None
    git("add", "-A", *paths)
    if not git("status", "--porcelain", "--", *paths):
        raise Stop("The build changed nothing to commit.")
    git("commit", "--quiet", "-m", message)
    for attempt in range(3):
        r = subprocess.run(["git", "push", "--quiet", "origin", "HEAD:main"], cwd=REPO,
                           capture_output=True, text=True)
        if not r.returncode:
            return git("rev-parse", "--short", "HEAD")
        git("pull", "--quiet", "--rebase", "origin", "main", check=False)
        time.sleep(5)
    raise Stop(f"git push failed: {(r.stderr or r.stdout).strip()[:300]}. The commit is kept and the "
               f"next run pushes it.")


# ======================================================================
# Choosing the job
# ======================================================================
def pending_heroes():
    if not dp.PENDING_HEROES.exists():
        return {}
    return json.loads(dp.PENDING_HEROES.read_text(encoding="utf-8"))


def repair_rows():
    _, rows = dp.read_queue()
    out = []
    for r in rows:
        m = re.search(r"\[(\d{4}-\d{2}-\d{2}-[a-z0-9-]+)\]", r["url"])
        if r["status"].lower() == "repair" and m and (dp.BLOG / "en" / f"{m.group(1)}.html").exists():
            out.append((r, m.group(1)))
    return out


def due(st):
    """What this run should do, or None. Never writes anything."""
    today = dp.today()
    d = day(st, today)
    if st.get("job"):
        if st["job"].get("defer_until", "") > today:
            return None              # a finished draft waiting for tomorrow holds the slot
        return f"resume {st['job']['kind']}"
    for slug in pending_heroes():
        if d["fails"].get(f"hero:{slug}", 0) < MAX_FAILS:
            return "hero"
    hour = now_muscat().hour
    if not dp.already_published(today) and NEW_WINDOW[0] <= hour < NEW_WINDOW[1] \
            and d["fails"].get(f"new:{today}", 0) < MAX_FAILS:
        return "new"
    if len(d["repairs"]) < MAX_REPAIRS_PER_DAY:
        for _, slug in repair_rows():
            if d["fails"].get(f"repair:{slug}", 0) < MAX_FAILS:
                return "repair"
    return None


def new_job(st, kind):
    today = dp.today()
    d = day(st, today)
    base = {"kind": kind, "started": time.time(), "dry_run": bool(st.pop("dry_run_next", False)),
            "status": "open"}
    if kind == "hero":
        slug, h = next((s, h) for s, h in pending_heroes().items()
                       if d["fails"].get(f"hero:{s}", 0) < MAX_FAILS)
        return dict(base, slug=slug, date=h["date"], title=h["title"], concept=h["concept"],
                    old_image=h["image_name"])
    if kind == "repair":
        row, slug = next((r, s) for r, s in repair_rows() if d["fails"].get(f"repair:{s}", 0) < MAX_FAILS)
        return dict(base, slug=slug, date=slug[:10], modified=today, row_num=row["num"],
                    en_title=row["en_title"], ar_title=row["ar_title"], cluster=row["cluster"])
    # new: topics first if the queue has run dry
    _, rows = dp.read_queue()
    if sum(r["status"].lower() == "pending" for r in rows) < dp.REFILL_BELOW:
        return dict(base, kind="topics", date=today)
    corp = dp.corpus()
    try:
        row = dp.next_topic(corp)
    except dp.PublishError:
        return dict(base, kind="topics", date=today)
    slug = f"{today}-{dp.slugify(row['en_title'])}"
    return dict(base, slug=slug, date=today, modified=None, row_num=row["num"], en_title=row["en_title"],
                ar_title=row["ar_title"], cluster=row["cluster"])


def folder(job):
    return JOBS / (job["slug"] + ("-hero" if job["kind"] == "hero" else "")) if job.get("slug") else TOPICS


# ======================================================================
# Briefs: everything the agent needs, in one file
# ======================================================================
JSON_SHAPE = """{
  "title": "the H1. Keep it close to the working title; fix it only if it breaks criterion 1",
  "meta_description": "140-155 characters (Arabic 130-160), names Oman or the GCC, does not start with 'Learn how', 'Discover' or 'AI Profit Lab'",
  "keywords": "5 to 8 comma-separated search phrases",
  "category": "a short category label",
  "dek": "one full sentence under the title, 40+ characters",
  "intro_html": "<p>...</p><p>...</p>",
  "sections": [
    {"heading": "A question ending in ?",
     "answer": "the ~40-word direct answer under that heading, in an 'X is Y' form",
     "body_html": "<p>...</p><ul><li>...</li></ul><table><thead><tr><th>...</th></tr></thead><tbody><tr><td>...</td></tr></tbody></table>"}
  ],
  "faqs": [{"q": "A question?", "a": "30 to 80 words"}],
  "references": [{"label": "Publisher: page title", "url": "https://..."}],
  "image_concept": "one paragraph describing the hero photograph (see Hero image below)",
  "forum_snippet": "60-90 words, problem first, one concrete number from the article, ends with the article URL"
}"""

LEDGER = """Every sentence, list item, table row, FAQ or field that contains a number (a figure, percentage,
price, count, duration, date or year) needs an entry in `claims-<lang>.json`. `check` lists any it
cannot find, quoting the exact text to copy. Format:

```json
{"claims": [
  {"quote": "exact text copied from the article that contains the number", "kind": "sourced",
   "source_url": "https://... (must be one of the article's references)",
   "evidence": "the sentence on that page that states the number, copied from the page"},
  {"quote": "Say your team answers 300 WhatsApp messages a week at 4 minutes each", "kind": "illustrative"},
  {"quote": "aim for a first reply in under 2 minutes", "kind": "recommendation"},
  {"quote": "Oman's Personal Data Protection Law (Royal Decree 6/2022)", "kind": "general_knowledge"}
]}
```

Kinds, and what `check` verifies mechanically:
- `sourced`: `check` downloads `source_url` and every number in your quote must appear on that page.
  Anything phrased "according to", "a study/survey/report by...", "research shows", or "X% of
  businesses/customers/..." MUST be sourced.
- `illustrative`: worked arithmetic or a scenario. The sentence (or the one before it, or for a
  table the paragraph before the table) must frame it: "say", "suppose", "for example", "imagine", "if".
- `recommendation`: a target you advise ("aim for", "keep it under", "budget", "start with", "should").
- `calculated`: worked out from sourced numbers, such as a percentage change. Add
  `"formula": "(37.57 - 30.97) / 30.97 * 100"`. `check` recomputes it, and every input must
  appear in a `sourced` entry of the same ledger.
- `general_knowledge`: a stable fact you are certain of (a law's decree number, a product's name and
  version). At most 8 per language, and never a percentage or a price.
Never invent a statistic, a client, a result, a quote or a price. If you cannot source a number,
delete it or rewrite it as clearly illustrative arithmetic. In the Arabic edition write numbers
as Western digits (0-9), like the English, so they can be matched against the sources."""


def links_block(job, corp):
    links = dp.link_candidates(job["en_title"] + " " + job.get("cluster", ""), corp, {job["slug"]})
    en = "\n".join(f"- {corp['en'][s]} -> /blog/en/{s}/" for s in links)
    ar = "\n".join(f"- {corp['ar'][s]} -> /blog/ar/{s}/" for s in links if s in corp["ar"])
    return en, ar


def article_brief(job, corp):
    en_links, ar_links = links_block(job, corp)
    slug, f = job["slug"], folder(job)
    rel = f.relative_to(ROOT)
    if job["kind"] == "repair":
        what = (f"REPAIR. The article at this URL is broken (too short, a placeholder, or missing). Write a "
                f"complete new article on its topic. The URL and the publication date ({job['date']}) stay.")
    else:
        what = "NEW ARTICLE for today."
    publish = (f"`{CMD} publish --dry-run`  (THIS IS A DRY RUN: never run plain `publish`)"
               if job.get("dry_run") else f"`{CMD} publish`")
    return f"""# Brief: {job['en_title']}

{what}

- Slug: `{slug}`  ·  publication date: {job['date']}
- English URL: {dp.SITE}/blog/en/{slug}/
- Arabic URL: {dp.SITE}/blog/ar/{slug}/
- Working titles: EN "{job['en_title']}"  ·  AR "{job['ar_title']}"
- Cluster: {job.get('cluster') or '-'}
- Your folder: `{rel}/` (write every file there)

## Steps

1. Research the topic with web search. Collect 4 to 6 real, stable sources you have opened
   yourself: vendor documentation, government or regulator portals (Oman first), major
   publishers. Note the exact sentence behind every number you plan to use.
2. Write `{rel}/en.json` in the JSON format below, then `{rel}/claims-en.json`.
3. Run `{CMD} check en`. Fix every problem it lists and run it again until it prints PASS.
4. Write `{rel}/ar.json` and `{rel}/claims-ar.json` (see Arabic edition). Run `{CMD} check ar`
   until PASS.
5. Generate the hero image with your image generation tool, aspect ratio 16:9 (see Hero image).
   Then run `{CMD} image "<full path of the generated image>"`. If it is rejected, generate a
   new one that fixes what it says.
6. Run {publish}. It rebuilds the site, commits, pushes and checks the live pages.
7. Reply with a 3-line summary: title, live URL, anything that went wrong.

If a step still fails after 5 rounds of fixes, or a tool you need is missing, run
`{CMD} fail "<what blocked you>"` and stop.

## The rules: the article-creator skill, verbatim

{dp.system_prompt()}

## JSON format (en.json and ar.json)

```json
{JSON_SHAPE}
```

Use only these HTML tags inside intro_html and body_html: p, h3, ul, ol, li, strong, em, a,
table, thead, tbody, tr, th, td, blockquote. Every reference must also be linked inline with
<a href> where you use it. The page adds its own call to action, hero, table of contents and
schema: do not write them.

## Internal links (use 2 or 3, exactly these URLs)

English:
{en_links}

Arabic (for ar.json):
{ar_links}

## Arabic edition

Write the Arabic edition for Omani and GCC business readers in professional Modern Standard
Arabic. Adapt, do not translate word for word, but keep the same facts, numbers, table data
and reference URLs (reference labels in Arabic). Section headings end in '؟'. Exactly 10 FAQs.
650 to 1350 words in intro_html + answers + body_html. The meta description starts with a
regional pain point (for example 'هل تعاني من...') and is 130 to 160 characters. Internal
links use the Arabic URLs above. Working Arabic title: {job['ar_title']}

## Claims ledger

{LEDGER}

## Hero image

Write `image_concept` in en.json first, then generate with this prompt (style + your scene):

{dp.IMAGE_STYLE}

Article: <the English title>
Scene: <your image_concept>

`image` rejects anything under 1000px wide, not landscape, or too dark for the light brand.
"""


def hero_brief(job):
    f = folder(job).relative_to(ROOT)
    publish = f"`{CMD} publish --dry-run`" if job.get("dry_run") else f"`{CMD} publish`"
    return f"""# Brief: hero image for "{job['title']}"

The article {dp.SITE}/blog/en/{job['slug']}/ went live with a placeholder image (it was
published by the GitHub fallback, which has no image model). Give it its real hero.

1. Generate the image with your image generation tool, aspect ratio 16:9, using this prompt:

{dp.IMAGE_STYLE}

Article: {job['title']}
Scene: {job['concept']}

2. Run `{CMD} image "<full path of the generated image>"`. If it is rejected, generate a new
   one that fixes what it says.
3. Run {publish}. It swaps the image in, rebuilds the blog hubs, commits, pushes and checks
   the live page.
4. Reply with one line: the article URL and whether the new hero is live.

Your folder: `{f}/`. If it still fails after 4 images, run `{CMD} fail "<why>"` and stop.
"""


def topics_brief(job):
    research = json.loads((TOPICS / "research.json").read_text(encoding="utf-8"))
    cands = research["cands"]
    corp = dp.corpus()
    _, rows = dp.read_queue()
    n = research["n"]
    if cands:
        task = tt.pick_prompt(dp, cands, corp, rows, n)
        shape = ('{"topics": [{"query": "the search, copied exactly", "cluster": "...", "en_title": "...", '
                 '"ar_title": "...", "intent": "who searches this and what they need"}]}')
    else:
        clusters = sorted({r["cluster"] for r in rows if r["cluster"]})
        task = (f"Google's search data could not be collected today. Propose {n * 2} article topics for "
                f"the AI Profit Lab blog, each serving an owner or manager of a small or mid-sized business "
                f"in Oman or the GCC with a clear search intent, following criterion 1 of the skill (a "
                f"specific number, location or outcome; nothing generic). Clusters (use the names exactly): "
                f"{'; '.join(clusters)}. They must not overlap a published article:\n"
                + "\n".join(f"- {t}" for t in corp["en"].values()))
        shape = '{"topics": [{"cluster": "...", "en_title": "...", "ar_title": "..."}]}'
    return f"""# Brief: new topics for the article queue

The queue has run out of topics. Pick today's from what people in Oman really search.

1. Read the task below and write your answer to `{(TOPICS / 'topics.json').relative_to(ROOT)}`
   in this shape:

```json
{shape}
```

2. Run `{CMD} topics-add`. It checks every title (it must carry its search's words, follow the
   skill's title rules and not overlap a published article) and queues the good ones. If it
   queues none, fix what it lists and run it again.
3. Then run `{CMD} next` again: it hands you today's article.

## Task

{task}
"""


# ======================================================================
# Claims ledger: every figure is sourced, illustrative, advice, or known
# ======================================================================
DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
# A number the reader would take as a figure: "300", "1,200", "4.5", "30%", "10k", "5x". Not part
# of a name or code ("GPT-4o", "5G", "B2B", "3PL").
FIG = re.compile(r"(?<![A-Za-z؀-ۿ\d.])(?<![A-Za-z]-)\d[\d,.]*(?:k|m|bn|x|h|hrs|mins?)?(?![A-Za-z\d])",
                 re.I)
EXEMPT = re.compile(r"https?://\S+|(oman\s+)?vision\s+2040|رؤية\s+(عمان\s+)?2040|24/7", re.I)
ATTRIBUTION = re.compile(
    r"according to|\b(study|studies|survey|surveys|poll|polls)\b|"
    r"\b(report|research|data|statistics|figures|analysis)\s+(by|from|shows?|showed|found|finds|suggests?|"
    r"indicates?)\b|researchers|found that|\bestimates?\s+(by|from)\b|gartner|mckinsey|statista|forrester|"
    r"\bidc\b|deloitte|\bpwc\b|world bank|\bimf\b|وفق[اًا]?\s*ل|بحسب|دراسة|استطلاع|تشير\s+(البيانات|"
    r"الإحصاءات|الدراسات|التقارير)|إحصاءات|إحصائيات", re.I)
POPULATION = re.compile(
    r"\d[\d.,]*\s*(%|percent|per cent)\s+of\s+(the\s+|all\s+)?(\w+\s+){0,2}(businesses|companies|firms|smes|"
    r"customers|consumers|shoppers|buyers|users|people|respondents|organi[sz]ations|employees|retailers|"
    r"owners|leaders|executives|ceos|managers|enterprises|omanis|residents|households|merchants)|"
    r"\d[\d.,]*\s*[%٪]\s*من\s+(ال)?(شركات|عملاء|مستهلكين|متسوقين|مستخدمين|مؤسسات|موظفين|أصحاب|مديرين|"
    r"مشترين|أسر|عمانيين|تجار|مشاركين)", re.I)
ILLUSTRATIVE = re.compile(
    r"\b(say|suppose|supposing|imagine|for example|for instance|e\.g\.|example|assume|assuming|if|"
    r"hypothetical|illustrative|illustration|picture|scenario|let's|lets)\b|مثلا|مثلاً|لنفترض|افترض|نفترض|"
    r"على سبيل المثال|تخيل|لو\s|إذا|اذا|فرضا|فرضاً|لنقل|مثال|توضيحي|سيناريو", re.I)
ADVICE = re.compile(
    r"\b(aim|target|recommend|should|try|keep|budget|plan|start|set|allow|allocate|limit|cap|choose|pick|"
    r"expect|ensure|make sure|rule of thumb|no more than|at least|at most|up to|under|within|consider)\b|"
    r"ننصح|يُنصح|ينصح|استهدف|اجعل|ينبغي|يجب|حاول|ابدأ|خطط|احرص|لا تتجاوز|على الأقل|حد أقصى|خصص", re.I)
MONEY = re.compile(r"%|٪|percent|\bomr\b|\bro\b|\busd\b|\$|ريال|دولار|\baed\b|\bsar\b|درهم", re.I)


def _n(s):
    s = html.unescape(s or "").translate(DIGITS)
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"[‐‑‒–—−]", "-", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def _figs(s):
    s = EXEMPT.sub(" ", _n(s))
    year = now_muscat().year
    out = []
    for m in FIG.finditer(s):
        tok = m.group(0).rstrip(".,")
        if tok in (str(year), str(year + 1)):
            continue               # "in 2026" / "your 2027 budget" needs no source
        out.append(tok)
    return out


def _num(tok):
    return re.sub(r"[a-z]+$", "", tok.lower().replace(",", "")).rstrip(".")


class _Blocks(HTMLParser):
    """Text blocks of an HTML fragment: paragraphs, list items, headings, and table rows."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks, self.cur, self.row, self.cell = [], [], None, None
        self.table_ctx, self.header = "", ""

    def handle_starttag(self, tag, attrs):
        if tag in ("p", "li", "h3", "blockquote"):
            self._flush()
        elif tag == "table":
            self._flush()
            self.table_ctx = self.blocks[-1]["text"] if self.blocks else ""
            self.header = ""
        elif tag == "tr":
            self.row = []
        elif tag in ("td", "th"):
            self.cell = []

    def handle_endtag(self, tag):
        if tag in ("p", "li", "h3", "blockquote"):
            self._flush()
        elif tag in ("td", "th") and self.cell is not None and self.row is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            text = " | ".join(c for c in self.row if c)
            if text and not self.header:
                self.header = text
            elif text:
                self.blocks.append({"text": text, "row": True,
                                    "context": self.table_ctx + " " + self.header})
            self.row = None

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)
        elif self.row is None:
            self.cur.append(data)

    def _flush(self):
        text = " ".join("".join(self.cur).split())
        if text:
            self.blocks.append({"text": text, "row": False, "context": ""})
        self.cur = []

    def close(self):
        super().close()
        self._flush()


SENT = re.compile(r"(?<=[.!?؟])\s+")


def units(d):
    """(where, text, context) for every sentence, row and field the reader sees."""
    out = []

    def add_text(where, text):
        prev = ""
        for s in SENT.split(" ".join((text or "").split())):
            if s:
                out.append((where, s, prev))
                prev = s

    def add_html(where, frag):
        p = _Blocks()
        p.feed(frag or "")
        p.close()
        prev = ""
        for b in p.blocks:
            if b["row"]:
                out.append((where + " (table)", b["text"], b["context"]))
            else:
                for s in SENT.split(b["text"]):
                    if s:
                        out.append((where, s, prev))
                        prev = s

    for k in ("title", "meta_description", "dek"):
        add_text(k, d.get(k))
    add_html("intro", d.get("intro_html"))
    for i, s in enumerate(d.get("sections") or [], 1):
        add_text(f"section {i} heading", s.get("heading"))
        add_text(f"section {i} answer", s.get("answer"))
        add_html(f"section {i}", s.get("body_html"))
    for i, f in enumerate(d.get("faqs") or [], 1):
        add_text(f"faq {i}", f"{f.get('q', '')} {f.get('a', '')}")
    add_text("forum_snippet", d.get("forum_snippet"))
    return out


_PAGES = {}
CHALLENGE = re.compile(r"checking your browser|verify you are (a )?human|are you a robot|captcha|"
                       r"enable javascript and cookies|access denied|request unsuccessful|just a moment")


def numbers_missing(url, q):
    """The quote's numbers the page does not state. A page that just served a bot check is
    fetched once more before anything is declared missing."""
    for attempt in range(2):
        page = page_text(url)
        if page is None:
            return None
        toks = {_num(t) for t in re.findall(r"\d[\d,.]*", page)}
        vals = {v for v in (_value(t) for t in toks) if v is not None}
        missing = [t for t in _figs(q) if not number_on_page(t, vals, toks)]
        if not missing or attempt:
            return missing
        _PAGES.pop(url, None)
        time.sleep(4)
    return missing


def page_text(url):
    """The visible text of a source page, or None if it cannot be read."""
    if url in _PAGES:
        return _PAGES[url]
    text = None
    for ctx in (dp.SSL, dp.LOOSE_SSL):
        try:
            req = urllib.request.Request(url, headers=dp.BROWSER)
            with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
                if "pdf" in r.headers.get("Content-Type", "").lower() or url.lower().endswith(".pdf"):
                    text = _pdf_text(r.read(25_000_000))
                    break
                raw = r.read(6_000_000).decode(r.headers.get_content_charset() or "utf-8", "replace")
            raw = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", raw)
            text = _n(re.sub(r"<[^>]+>", " ", raw))
            if len(text) < 1500 or CHALLENGE.search(text[:3000]):
                text = None              # a bot check or an empty shell, not the article
            break
        except urllib.error.URLError as e:
            if isinstance(getattr(e, "reason", None), dp.ssl.SSLCertVerificationError):
                continue
            break
        except Exception:
            break
    _PAGES[url] = text
    return text


def _pdf_text(data):
    """Government and research reports are often PDFs. Text of the first 80 pages, or None."""
    try:
        import io
        from pypdf import PdfReader
        pages = PdfReader(io.BytesIO(data)).pages[:80]
        return _n(" ".join(p.extract_text() or "" for p in pages)) or None
    except Exception:
        return None


def _value(tok):
    try:
        return float(_num(tok))
    except ValueError:
        return None


def number_on_page(tok, page_vals, page_toks):
    """True if the page states this number, allowing for rounding (the page's 21.3 supports
    the article's 21, its 3.36 supports 3.4) but nothing looser."""
    if _num(tok) in page_toks:
        return True
    v = _value(tok)
    if v is None:
        return False
    dec = len(_num(tok).split(".")[1]) if "." in _num(tok) else 0
    half = 0.5 * 10 ** -dec
    return any(abs(p - v) <= half + 1e-9 for p in page_vals)


def check_formula(label, c, q, verified):
    """A figure worked out from sourced ones ("+21.3%" from 30.97 kg -> 37.57 kg): the script
    recomputes it, and every input must be a number a sourced entry has verified."""
    formula = (c.get("formula") or "").replace("×", "*").replace("÷", "/")
    if not re.fullmatch(r"[\d.\s+\-*/()]+", formula or "x"):
        return [f"{label}: a calculated entry needs \"formula\" using only numbers and + - * / ( ), "
                f"e.g. \"(37.57 - 30.97) / 30.97 * 100\"."]
    try:
        result = eval(formula, {"__builtins__": {}}, {})       # digits and operators only (checked above)
    except Exception:
        return [f"{label}: the formula {formula} does not compute."]
    inputs = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", formula)]
    unsourced = [x for x in inputs if x not in (100, 1000) and not any(abs(x - v) < 1e-9 for v in verified)]
    if unsourced:
        return [f"{label}: the formula uses {', '.join(f'{x:g}' for x in unsourced)}, which no verified "
                f"`sourced` entry states. Source those inputs first."]
    if not any(number_on_page(t, {abs(result), result}, set()) for t in _figs(q)):
        return [f"{label}: the formula gives {result:.4g}, which is not the number in the quote."]
    return []


def load_ledger(path):
    if not path.exists():
        return None, [f"{path.name} is missing. Write the claims ledger (see the brief)."]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return None, [f"{path.name} is not valid JSON: {e}"]
    claims = data.get("claims") if isinstance(data, dict) else data
    if not isinstance(claims, list):
        return None, [f'{path.name} must be {{"claims": [...]}}.']
    return [c for c in claims if isinstance(c, dict)], []


def check_claims(lang, d, path):
    claims, problems = load_ledger(path)
    if problems:
        return problems, 0, 0
    refs = {r["url"].rstrip("/") for r in d["references"]}
    us = units(d)
    figured = [(w, t, c) for w, t, c in us if _figs(t)]
    entries = []
    for i, c in enumerate(claims, 1):
        q = _n(c.get("quote"))
        kind = (c.get("kind") or "").strip().lower()
        if len(q) < 4 or not _figs(q):
            problems.append(f"Ledger entry {i}: the quote must be copied text containing its number "
                            f"(got \"{c.get('quote', '')[:80]}\").")
            continue
        homes = [(w, t, ctx) for w, t, ctx in figured if q in _n(t) or _n(t) in q]
        if not homes:
            problems.append(f"Ledger entry {i}: \"{c.get('quote', '')[:100]}\" is not in the article. Copy "
                            f"the text exactly as it appears.")
            continue
        entries.append((i, c, q, kind, homes))

    general, verified, calculated = 0, set(), []
    for i, c, q, kind, homes in entries:
        text = " ".join(_n(t) for _, t, _ in homes)
        ctx = " ".join(_n(x) for _, _, x in homes)
        label = f"\"{c.get('quote', '')[:90]}\""
        if kind not in ("sourced", "calculated", "illustrative", "recommendation", "general_knowledge"):
            problems.append(f"{label}: kind must be sourced, calculated, illustrative, recommendation or "
                            f"general_knowledge (got \"{kind}\").")
            continue
        if kind not in ("sourced", "calculated") and (ATTRIBUTION.search(text) or POPULATION.search(text)):
            problems.append(f"{label}: it reads as a statistic from a study or about a population, so it "
                            f"must be `sourced` with a page that states it, or be deleted.")
            continue
        if kind == "sourced":
            url = (c.get("source_url") or "").strip()
            if url.rstrip("/") not in refs:
                problems.append(f"{label}: source_url {url or '(empty)'} is not one of this article's "
                                f"references that passed the link check.")
                continue
            missing = numbers_missing(url, q)
            if missing is None:
                problems.append(f"{label}: {url} could not be read (blocked, a bot check, a scanned PDF or "
                                f"a page built by script). Cite a page that can be fetched, or rewrite the "
                                f"sentence without the number.")
                continue
            if missing:
                problems.append(f"{label}: {', '.join(missing)} does not appear on {url}. The source does not "
                                f"state it: fix the number, cite the page that does, or delete the claim.")
            else:
                verified |= {_value(t) for t in _figs(q)} - {None}
        elif kind == "calculated":
            calculated.append((label, c, q))
        elif kind == "illustrative":
            if not ILLUSTRATIVE.search(text + " " + ctx):
                problems.append(f"{label}: marked illustrative but not framed as an example. Add 'say', "
                                f"'for example' or 'if' to the sentence (or to the one before it).")
        elif kind == "recommendation":
            if not ADVICE.search(text):
                problems.append(f"{label}: marked recommendation but not phrased as advice ('aim for', "
                                f"'keep it under', 'budget', 'start with'...).")
        else:
            general += 1
            if MONEY.search(q):
                problems.append(f"{label}: a percentage or a price cannot be general_knowledge. Source it, "
                                f"make it illustrative, or delete it.")

    for label, c, q in calculated:
        problems += check_formula(label, c, q, verified)

    if general > MAX_GENERAL:
        problems.append(f"{general} general_knowledge entries; at most {MAX_GENERAL}. Source the others.")

    covered = {}
    for _, _, q, _, homes in entries:
        for w, t, _ in homes:
            covered.setdefault((w, t), set()).update(_num(x) for x in _figs(q))
    missing_units = []
    for w, t, _ in figured:
        need = {_num(x) for x in _figs(t)}
        if not need <= covered.get((w, t), set()):
            missing_units.append(f"No ledger entry for ({w}): \"{t[:220]}\"")
    problems += missing_units[:25]
    if len(missing_units) > 25:
        problems.append(f"...and {len(missing_units) - 25} more sentences with numbers have no ledger entry.")
    return problems, len(figured), len(claims)


# ======================================================================
# Drafts
# ======================================================================
REQUIRED = {"title": str, "meta_description": str, "keywords": str, "category": str, "dek": str,
            "intro_html": str, "sections": list, "faqs": list, "references": list,
            "image_concept": str, "forum_snippet": str}


def load_draft(job, lang):
    path = folder(job) / f"{lang}.json"
    if not path.exists():
        raise Stop(f"{path.relative_to(ROOT)} does not exist yet.")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise Stop(f"{path.relative_to(ROOT)} is not valid JSON: {e}")
    bad = [k for k, t in REQUIRED.items() if not isinstance(raw.get(k), t)]
    bad += [f"sections[{i}]" for i, s in enumerate(raw.get("sections") or [])
            if not (isinstance(s, dict) and all(isinstance(s.get(k), str) for k in ("heading", "answer", "body_html")))]
    bad += [f"faqs[{i}]" for i, f in enumerate(raw.get("faqs") or [])
            if not (isinstance(f, dict) and isinstance(f.get("q"), str) and isinstance(f.get("a"), str))]
    bad += [f"references[{i}]" for i, r in enumerate(raw.get("references") or [])
            if not (isinstance(r, dict) and isinstance(r.get("url"), str))]
    if bad:
        raise Stop(f"{path.relative_to(ROOT)}: missing or wrong type: {', '.join(bad)}. See the JSON format "
                   f"in the brief.")
    return raw


def audit_lang(job, lang, quiet=False):
    """(cleaned draft, problems). The skill audit, the dead-link sweep and the claims ledger."""
    raw = load_draft(job, lang)
    corp = dp.corpus()
    d, _, problems = dp.prepare(lang, raw, job["slug"], job["date"], "pending-image", corp, dp.nap_block(),
                                job.get("modified"))
    problems = [p for p in problems if not p.startswith("[renderer] hero")]
    dropped = sorted({r["url"] for r in raw.get("references") or [] if isinstance(r, dict)}
                     - {r["url"] for r in d["references"]})
    lp, nfig, nclaims = check_claims(lang, d, folder(job) / f"claims-{lang}.json")
    problems += lp
    if not quiet:
        words = dp.legacy.read(str(dp.TMP / f"audit-{lang}.html"))["words"]
        log(f"{lang.upper()}: {words} body words, {len(d['faqs'])} FAQs, {len(d['references'])} working "
            f"references, {nfig} sentences with numbers, {nclaims} ledger entries")
        if dropped:
            log("  dead links removed (and unlinked in the text): " + ", ".join(dropped))
    return d, problems


def report(problems, what):
    if not problems:
        log(f"PASS: {what}")
        return True
    log(f"FAIL: {len(problems)} problem(s) in {what}. Fix them all, then run the check again.")
    for i, p in enumerate(problems, 1):
        log(f" {i:2d}. {p}")
    return False


# ======================================================================
# Commands
# ======================================================================
def active(st, kinds=None):
    job = st.get("job")
    if not job:
        raise Stop(f"No job is open. Run `{CMD} next` first.")
    if kinds and job["kind"] not in kinds:
        raise Stop(f"The open job is a {job['kind']} job; this command does not apply to it.")
    return job


def cmd_next(a):
    assert_clone()
    refresh_lock("next")
    st = load_state()
    job = st.get("job")
    if job and job.get("defer_until", "") > dp.today():
        release_lock()
        log(f"NOTHING TO DO: the open draft ({job['slug']}) waits for {job['defer_until']}. Stop here.")
        return 0
    if not job:
        sync()
        label = due(st)
        if not label:
            save_state(st)
            release_lock()
            log("NOTHING TO DO: today's article is out, no hero swap or repair is due. Stop here.")
            return 0
        if label == "new":
            shutil.rmtree(TOPICS, ignore_errors=True)      # research from an earlier day is stale
        job = new_job(st, label)
        st["job"] = job
        d = day(st)
        d["launches"].setdefault(job_key(job), 0)
        save_state(st)
        journal(f"start {job_key(job)}" + (" (dry run)" if job.get("dry_run") else ""))
    f = folder(job)
    f.mkdir(parents=True, exist_ok=True)
    if job["kind"] == "topics":
        if not (TOPICS / "research.json").exists():
            corp = dp.corpus()
            _, rows = dp.read_queue()
            n = max(tt.TARGET_PENDING - sum(r["status"].lower() == "pending" for r in rows), 1)
            log("Researching what people in Oman search (Google Trends + autocomplete, ~3 minutes)...")
            try:
                cands, stats = tt.collect(dp)
            except Exception as e:
                log(f"  search research failed ({e}); you will propose topics without it")
                cands, stats = {}, {"seeds": len(tt.SEEDS), "trends": 0, "fallback": [], "autocomplete": 0,
                                    "blocked": str(e)[:80]}
            best = dict(sorted(cands.items(), key=lambda kv: -kv[1]["score"])[:tt.MAX_CANDIDATES])
            (TOPICS / "research.json").write_text(json.dumps(
                {"cands": best, "stats": stats, "n": n}, ensure_ascii=False, indent=1), encoding="utf-8")
        brief = topics_brief(job)
    elif job["kind"] == "hero":
        brief = hero_brief(job)
    else:
        brief = article_brief(job, dp.corpus())
    (f / "brief.md").write_text(brief, encoding="utf-8")
    log(f"JOB: {job['kind']}" + (f" · {job['slug']}" if job.get("slug") else "")
        + (" · DRY RUN" if job.get("dry_run") else ""))
    if job.get("status") == "ready":
        log(f"This draft already passed every check (dry run). Run `{CMD} publish` now.")
    else:
        log(f"Read the brief now: {(f / 'brief.md').relative_to(ROOT)}  (it has every step and rule)")
        done = [p.name for p in sorted(f.glob("*")) if p.name != "brief.md"]
        if done:
            log(f"Files already in the folder from an earlier attempt: {', '.join(done)}. Check them and "
                f"continue from where they stop.")
    return 0


def cmd_topics_add(a):
    st = load_state()
    job = active(st, ("topics",))
    research = json.loads((TOPICS / "research.json").read_text(encoding="utf-8"))
    path = TOPICS / "topics.json"
    if not path.exists():
        raise Stop(f"{path.relative_to(ROOT)} does not exist yet.")
    try:
        topics = json.loads(path.read_text(encoding="utf-8")).get("topics") or []
    except (json.JSONDecodeError, AttributeError) as e:
        raise Stop(f"{path.relative_to(ROOT)} is not valid JSON in the shape the brief shows: {e}")
    corp = dp.corpus()
    _, rows = dp.read_queue()
    cands, n = research["cands"], research["n"]
    if cands:
        picks, rejected = tt.validate_picks(dp, topics, cands, corp, rows)
    else:
        picks, rejected = invented_picks(topics, corp, rows)
    for r in rejected:
        log(f"  rejected: {r.get('en_title', '?')}  ({r['why']})")
    if not picks:
        raise Stop("No title passed. Fix the reasons above and run topics-add again.")
    new = tt.queue_picks(dp, picks, rejected, rows, n, research["stats"], len(cands))
    st["job"] = None
    save_state(st)
    journal(f"queued {len(new)} topic(s): " + "; ".join(r["en_title"] for r in new))
    if not os.environ.get("APL_NO_SYNC"):
        commit_and_push(f"queue: {len(new)} trend-backed topic(s) from Antigravity",
                        ("Website SEO/directives",))
    log(f"Queued {len(new)} topic(s). Now run `{CMD} next` for today's article.")
    return 0


def invented_picks(topics, corp, rows):
    """No search data today: the refill rules of daily_publish.refill_queue, applied to the agent's ideas."""
    clusters = sorted({r["cluster"] for r in rows if r["cluster"]})
    taken = list(corp["en"].values()) + [r["en_title"] for r in rows]
    picks, rejected = [], []
    for t in topics:
        en, ar, cl = dp._plain(t.get("en_title")), dp._plain(t.get("ar_title")), dp._plain(t.get("cluster"))
        why = ("missing a title" if not en or not ar or "|" in en + ar + cl else
               "not specific enough (skill criterion 1)" if not dp.TITLE_SPECIFIC.search(en) else
               "banned wording" if any(re.search(r"\b" + re.escape(w), en.lower())
                                       for w in dp.SLOP + dp.GENERIC_TITLE + tt.TITLE_AVOID) else
               "too close to a published or queued title"
               if max((dp.similarity(en, x) for x in taken), default=0) > dp.SIMILARITY_LIMIT else "")
        if why:
            rejected.append({**t, "why": why})
            continue
        taken.append(en)
        picks.append({"query": "(no search data)", "evidence": ["proposed by the agent"], "intent": "",
                      "cluster": cl if cl in clusters else (clusters[0] if clusters else cl),
                      "en_title": en, "ar_title": ar})
    return picks, rejected


def cmd_check(a):
    refresh_lock("check")
    st = load_state()
    job = active(st, ("new", "repair"))
    if a.lang == "ar" and not (folder(job) / "en.json").exists():
        raise Stop("Write and check the English edition first.")
    _, problems = audit_lang(job, a.lang)
    ok = report(problems, f"the {a.lang.upper()} draft")
    journal(f"check {a.lang} {job['slug']}: {'PASS' if ok else f'{len(problems)} problem(s)'}")
    return 0 if ok else 1


def cmd_image(a):
    refresh_lock("image")
    st = load_state()
    job = active(st, ("new", "repair", "hero"))
    src = Path(a.path).expanduser()
    if not src.is_file():
        raise Stop(f"No file at {src}. Give the full path of the image your tool saved.")
    png, problems, info = dp.vet_image(src.read_bytes())
    if not png:
        log(f"REJECTED ({info}): " + "; ".join(problems) + ". Generate a new image that fixes this.")
        journal(f"image rejected for {job['slug']}: {'; '.join(problems)}")
        return 1
    (folder(job) / "hero.png").write_bytes(png)
    log(f"PASS: hero image stored ({info}) as {(folder(job) / 'hero.png').relative_to(ROOT)}")
    journal(f"image ok for {job['slug']} ({info})")
    return 0


def hero_png(job):
    p = folder(job) / "hero.png"
    if not p.exists():
        raise Stop(f"No hero image yet. Generate it, then run `{CMD} image <path>`.")
    png, problems, _ = dp.vet_image(p.read_bytes())
    if not png:
        raise Stop("The stored hero no longer passes: " + "; ".join(problems))
    return png


def copy_preview(slug, image_name):
    out = JOBS / slug / "preview"
    out.mkdir(parents=True, exist_ok=True)
    for lang in ("en", "ar"):
        shutil.copy2(dp.BLOG / lang / f"{slug}.html", out / f"{lang}.html")
    for f in dp.IMAGES.glob(f"{image_name}*"):
        shutil.copy2(f, out / f.name)
    return out


def revert_tree():
    """Undo a dry run's build in the clone (tracked edits and new files)."""
    if os.environ.get("APL_NO_SYNC"):
        log("  (APL_NO_SYNC: leaving the build in place)")
        return
    git("checkout", "--quiet", "--", "Website SEO/public_html", "Website SEO/directives")
    git("clean", "-fdq", "--", "Website SEO/public_html", "Website SEO/directives")


def cmd_publish(a):
    assert_clone()
    refresh_lock("publish")
    st = load_state()
    job = active(st, ("new", "repair", "hero"))
    dry = a.dry_run or job.get("dry_run")
    if job["kind"] == "hero":
        return publish_hero(st, job, dry)
    hero = hero_png(job)
    sync()
    freshen_derivatives()
    today = dp.today()
    _, rows = dp.read_queue()
    row = next((r for r in rows if r["num"] == str(job.get("row_num"))), None)
    if not dry and row and (row["status"].startswith("Published") and job["slug"] in row["url"]):
        # An earlier run's push failed and sync() has just pushed it: the job is already done.
        return finish(st, job, "already pushed by sync")
    if job["kind"] == "new":
        if job["date"] != today and not dry:       # a draft carried over a day publishes as today's
            old = folder(job)
            job["slug"] = today + job["slug"][10:]
            job["date"] = today
            if old.exists() and not folder(job).exists():
                old.rename(folder(job))
            save_state(st)
        other = [s for s in dp.already_published(today) if s != job["slug"]]
        if other:
            # GitHub's fallback (or a person) published while this draft was being written.
            job["defer_until"] = (datetime.strptime(today, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
            save_state(st)
            release_lock()
            journal(f"deferred {job['slug']} to {job['defer_until']}: {other[0]} went out today")
            log(f"DEFERRED: another article went out today ({other[0]}). This draft is kept and publishes "
                f"on {job['defer_until']}. Stop here.")
            return 0
        if not row or row["status"].lower() != "pending":
            raise Stop(f"Queue row #{job.get('row_num')} is no longer Pending; someone changed the queue.")

    drafts, problems = {}, []
    for lang in ("en", "ar"):
        d, p = audit_lang(job, lang, quiet=True)
        drafts[lang] = d
        problems += [f"[{lang}] {x}" for x in p]
    if not report(problems, "the final check of both editions"):
        return 1

    slug, date = job["slug"], job["date"]
    nap = dp.nap_block()
    name = dp.image_name_for(slug, hero)
    g = {"slug": slug, "date": date, "image_name": name, "png": hero, "en": drafts["en"], "ar": drafts["ar"],
         "src": {lang: dp.render_source(lang, drafts[lang], slug, date, name, nap, job.get("modified"))
                 for lang in ("en", "ar")}}
    log("Building (render, image derivatives, reskin, hubs, sitemap, Aiden index)...")
    dp.install(g)
    if job["kind"] == "new":
        dp.record(g, row, None)
    else:
        dp.record(g, None, row if row and row["status"].lower() == "repair" else None)

    if dry:
        out = copy_preview(slug, name)
        revert_tree()
        job.update(status="ready", dry_run=False, preview=str(out))
        save_state(st)
        release_lock()
        journal(f"dry run passed for {slug}; preview in {out.relative_to(ROOT)}")
        log(f"DRY RUN PASSED. Nothing was committed or pushed. Preview: {out.relative_to(ROOT)}/en.html "
            f"and ar.html. The next real run publishes this draft as is.")
        return 0

    kind = "Repair" if job["kind"] == "repair" else "Publish"
    sha = commit_and_push(f"{kind} article: {slug}\n\nWritten and illustrated by Google Antigravity; "
                          f"checked and built by execution/agent_publish.py.")
    return finish(st, job, f"{kind.lower()}, commit {sha}")


def finish(st, job, how):
    slug = job["slug"]
    d = day(st)
    if job["kind"] == "new":
        d["new"] = slug
    else:
        d["repairs"].append(slug)
    st["job"] = None
    save_state(st)
    release_lock()
    journal(f"published {slug} ({how})")
    log(f"PUSHED ({how}). GitHub's deploy workflow is uploading it; checking the live pages (up to 10 min)...")
    return verify(slug)


def verify(slug):
    if os.environ.get("APL_NO_SYNC"):
        return 0
    try:
        dp.cmd_verify(slug, wait=600)
    except dp.PublishError as e:
        journal(f"live check failed for {slug}: {e}")
        log(f"PUSHED BUT NOT LIVE YET: {e}. Check the 'Deploy to Hostinger' run on GitHub.")
        return 2
    journal(f"live: {dp.SITE}/blog/en/{slug}/")
    return 0


def publish_hero(st, job, dry):
    png = hero_png(job)
    sync()
    freshen_derivatives()
    slug, old = job["slug"], job["old_image"]
    heroes = pending_heroes()
    if slug not in heroes:
        st["job"] = None
        save_state(st)
        release_lock()
        log("This article no longer needs a hero (someone already swapped it). Nothing to do.")
        return 0
    new = dp.image_name_for(slug, png)
    (dp.IMAGES / f"{new}.png").write_bytes(png)
    for lang in ("en", "ar"):
        page = dp.BLOG / lang / f"{slug}.html"
        s = page.read_text(encoding="utf-8")
        if old not in s:
            raise Stop(f"{page.name} ({lang}) does not reference the placeholder {old}; swap it by hand.")
        page.write_text(s.replace(old, new), encoding="utf-8")
    py = sys.executable
    dp.run([py, "tools/build_image_derivatives.py"])
    dp.run([py, "tools/reskin_blog_hubs.py"])
    for lang in ("en", "ar"):
        if f"{new}-1200.webp" not in (dp.BLOG / lang / f"{slug}.html").read_text(encoding="utf-8"):
            raise Stop(f"The {lang} page does not serve the new hero's -1200.webp.")
    for f in dp.IMAGES.glob(f"{old}*"):
        f.unlink()
    heroes.pop(slug)
    dp.PENDING_HEROES.write_text(json.dumps(heroes, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                                 encoding="utf-8")
    _, rows = dp.read_queue()
    for r in rows:
        if slug in r["url"] and r["status"] == dp.TEMP_IMAGE_STATUS:
            r["status"] = "Published"
            dp.update_queue_row(r)
    if dry:
        out = copy_preview(slug, new)
        revert_tree()
        job.update(status="ready", dry_run=False)
        save_state(st)
        release_lock()
        log(f"DRY RUN PASSED. Preview: {out.relative_to(ROOT)}")
        return 0
    sha = commit_and_push(f"Real hero image for {slug}\n\nGenerated by Google Antigravity; it replaces the "
                          f"placeholder the GitHub fallback shipped.")
    day(st)["heroes"].append(slug)
    st["job"] = None
    save_state(st)
    release_lock()
    journal(f"hero swapped for {slug} (commit {sha})")
    log(f"PUSHED {sha}. Checking the live page...")
    return verify(slug)


def cmd_fail(a):
    st = load_state()
    job = st.get("job")
    if job:
        d = day(st)
        k = fail_key(job)
        d["fails"][k] = d["fails"].get(k, 0) + 1
        journal(f"FAILED {job_key(job)}: {a.reason}")
        if d["fails"][k] >= MAX_FAILS or job["kind"] == "topics":
            st["job"] = None       # parked; its folder stays, and `next` resumes it tomorrow if it is due
    save_state(st)
    release_lock()
    log("Recorded. Stop here; the schedule tries again later.")
    return 0


def cmd_status(a):
    st = load_state()
    today = dp.today()
    log(f"Today (Muscat): {today}. Published today: {', '.join(dp.already_published(today)) or 'nothing'}")
    log(f"Open job: {json.dumps(st.get('job'), ensure_ascii=False) if st.get('job') else 'none'}")
    log(f"Today: {json.dumps(day(st, today), ensure_ascii=False)}")
    log(f"Pending heroes: {', '.join(pending_heroes()) or 'none'}")
    log(f"Repair rows: {', '.join(s for _, s in repair_rows()) or 'none'}")
    age = lock_age()
    log(f"Run lock: {'held for %d min' % (age // 60) if age is not None else 'free'}")
    log(f"Would do now: {due(st) or 'nothing'}")
    return 0


# ======================================================================
# The scheduler's entry point
# ======================================================================
def agentapi():
    for c in (os.environ.get("ANTIGRAVITY_AGENTAPI_EXE"), shutil.which("agentapi"),
              str(Path.home() / ".gemini/antigravity/bin/agentapi"),
              str(Path.home() / ".gemini/antigravity-ide/bin/agentapi")):
        if c and Path(c).exists():
            return c
    raise Stop("agentapi not found: is Antigravity installed?")


def cmd_trigger(a):
    """Runs hourly from Antigravity's scheduler. Starts a conversation only when there is work."""
    assert_clone()
    # The lock comes first: the IDE and the app may both fire this, and a run in progress
    # must never have its clone reset under it.
    age = lock_age()
    if not take_lock("trigger"):
        log(f"busy: a run holds the lock ({(age or 0) / 60:.0f} min old)")
        return 0
    try:
        sync()
        st = load_state()
        if a.dry_run:
            st["dry_run_next"] = True
            if st.get("job"):
                st["job"]["dry_run"] = True      # an open job must not publish for real either
        label = due(st)
        if st.get("job"):
            d = day(st)
            k = job_key(st["job"])
            d["launches"][k] = d["launches"].get(k, 0) + 1
            if d["launches"][k] > MAX_LAUNCHES:
                d["fails"][fail_key(st["job"])] = MAX_FAILS
                journal(f"parked {k} for today: {MAX_LAUNCHES} conversations did not finish it")
                st["job"] = None
                label = due(st)
        if not label:
            st.pop("dry_run_next", None)
            save_state(st)
            release_lock()
            log("nothing to do")
            return 0
        save_state(st)
    except BaseException:
        release_lock()
        raise
    today = dp.today()
    title = f"AI Profit Lab publisher · {label} · {today}" + (" · dry run" if a.dry_run else "")
    prompt = (f"You are the AI Profit Lab blog publisher. Open `{DIRECTIVE}` in this workspace and follow "
              f"it exactly. Start by running `{CMD} next` in the workspace root, then do what it says."
              + (" This is a DRY RUN: finish with `publish --dry-run`, never plain `publish`."
                 if a.dry_run else ""))
    env = dict(os.environ)
    pid = git("config", "--get", "apl.projectId", check=False)
    if pid and not env.get("ANTIGRAVITY_PROJECT_ID"):
        env["ANTIGRAVITY_PROJECT_ID"] = pid
    cmd = [agentapi(), "new-conversation", f"--model={MODEL}", f"--title={title}", prompt]
    r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=180)
    out = (r.stdout + r.stderr).strip()
    log(out[:800])
    if r.returncode:
        release_lock()
        journal(f"trigger could not start a conversation ({label}): {out[:200]}")
        return r.returncode
    journal(f"started a conversation: {label}" + (" (dry run)" if a.dry_run else ""))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("next")
    sub.add_parser("topics-add")
    p = sub.add_parser("check")
    p.add_argument("lang", choices=["en", "ar"])
    p = sub.add_parser("image")
    p.add_argument("path")
    p = sub.add_parser("publish")
    p.add_argument("--dry-run", action="store_true")
    p = sub.add_parser("fail")
    p.add_argument("reason")
    sub.add_parser("status")
    p = sub.add_parser("trigger")
    p.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    fn = {"next": cmd_next, "topics-add": cmd_topics_add, "check": cmd_check, "image": cmd_image,
          "publish": cmd_publish, "fail": cmd_fail, "status": cmd_status, "trigger": cmd_trigger}[a.cmd]
    try:
        if a.cmd != "status":
            assert_clone()           # state and drafts live in the publisher's clone only
        sys.exit(fn(a) or 0)
    except Stop as e:
        log(f"STOP: {e}")
        sys.exit(e.code)
    except dp.PublishError as e:
        log(f"FAILED: {e}")
        journal(f"{a.cmd} failed: {str(e)[:200]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
