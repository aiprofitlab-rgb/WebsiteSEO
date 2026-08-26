#!/usr/bin/env python3
"""
AI Profit Lab — visitor journey report from the GA4 BigQuery export.

GA4's own reports answer "how many" well and "in what order" badly. They will
tell you a page had 40 views and a 62% engagement rate; they will not tell you
that eleven of those views were the last thing that happened in the session,
that nine of the eleven left inside five seconds, or that the two who read to
the bottom both opened Aiden on the next page. That ordering is the whole
question this report exists to answer, and the only place it survives intact is
the raw event export.

WHAT THIS IS NOT: a second copy of GA4. Nothing here re-counts users or
sessions for their own sake. Every number is in service of one of five
questions - see the REPORT SECTIONS block below.

MEASURED vs INFERRED - read this before quoting a number at anyone.
The report labels every figure, and the rendered HTML repeats the labels, but
the short version is:

  MEASURED   Anything the browser explicitly sent. dwell_seconds and max_scroll
             from page_exit, percent_scrolled from scroll_depth, the page a
             visitor was on when they opened Aiden, every conversion event, and
             the ORDER of all of it (event_timestamp is microsecond precision).

  INFERRED   Dwell for a page whose page_exit never arrived - reconstructed as
             the gap to the next page_view, which counts background tab time
             the real measurement deliberately excludes. Exit page (the last
             page_view in a session, which is a definition, not an observation:
             a session that resumes after 30 idle minutes becomes two sessions
             and manufactures one extra "exit"). Session-level language and
             device, taken from the session's first event.

  CANNOT     See the "What the data cannot answer" section of the HTML. The
             honest list is there and it is not short.

COST DESIGN - read before changing the SQL.
The export is one table per day, events_YYYYMMDD, and BigQuery bills on bytes
scanned. Two things keep that bounded:

  1. _TABLE_SUFFIX BETWEEN two dates. This is a partition prune - days outside
     the window are never opened. Without it every run scans the entire export
     back to the day it was linked, and that bill grows forever. The filter is
     built in build_sql() and there is no code path that omits it.
     (The BETWEEN also excludes events_intraday_* for free: that table's suffix
     sorts as 'intraday_...', which is above any 'YYYYMMDD' bound. --intraday
     adds it back explicitly when you want today's partial data.)

  2. One query per run, not five. The five report sections are computed in
     Python from a single flat pull of the events they all need. Five separate
     aggregate queries would each re-scan the same days.

Every run prints the dry-run byte estimate BEFORE spending anything and, unless
--yes is passed, waits for you to approve it. The first 1 TiB per month is free
on the BigQuery sandbox and on-demand pricing; a site this size will not come
close, but the estimate is printed so that stays a fact and not an assumption.

CACHING. Results are cached under out/.journey-cache/ keyed by a hash of the
exact SQL. Re-rendering the HTML - which is what you actually do repeatedly
while adjusting thresholds or fixing the layout - reads the cache and bills
nothing. --refresh forces a new query; --render-only refuses to query at all.

PRIVACY. THIS REPO IS PUBLIC. The output contains user_pseudo_ids, full page
sequences and, when the Aiden CSV is supplied, verbatim things visitors typed.
out/journey-*.html and out/.journey-cache/ are gitignored for that reason. Do
not move the output somewhere tracked, and do not commit the Aiden CSV.

REPORT SECTIONS
  1  Session reconstruction   landing page, ordered pages, dwell + scroll each,
                              exit page, total duration
  2  Aiden touchpoints        where they opened it, how many pages first, what
                              they asked (needs --aiden-csv), what followed
  3  Drop-off analysis        ranked exit pages, exit rate, median dwell and
                              scroll before exit, "read fully" vs "bounced"
  4  Content performance      per article: entrances, median dwell, scroll
                              completion, onward clicks, precedes Aiden / lead
  5  Path to conversion       page sequences before generate_lead /
                              begin_checkout / purchase, vs sessions that did
                              not convert

Everything is segmented EN vs AR and mobile vs desktop.

REQUIREMENTS
  gcloud + bq on PATH, authenticated to an account with BigQuery Job User on
  the project. No Python packages beyond the standard library - deliberately,
  so this runs on a fresh machine with nothing but the Google Cloud SDK.

USAGE
    python3 tools/build_journey_report.py --days 28
    python3 tools/build_journey_report.py --days 7 --yes
    python3 tools/build_journey_report.py --render-only        # free, cached
    python3 tools/build_journey_report.py --print-sql          # free, no query
    python3 tools/build_journey_report.py --sample             # free, fake data
    python3 tools/build_journey_report.py --aiden-csv ~/Downloads/Aiden_Chat.csv
"""

import argparse
import csv
import hashlib
import json
import os
import random
import re
import shutil
import statistics
import subprocess
import sys
import urllib.parse
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "out")
CACHE_DIR = os.path.join(OUT_DIR, ".journey-cache")

# The GCP project holding the export. The GA4 property (G-SLR9GD3MJP) is owned
# by ai.profit.lab2026@gmail.com; that account was granted Owner here so the
# GA4 > Admin > BigQuery Links flow can select this project as the destination.
PROJECT = os.environ.get("GA4_BQ_PROJECT", "adroit-minutia-496210-n1")

# The export dataset is named analytics_<numeric GA4 property id> - NOT the
# G-SLR9GD3MJP measurement id, which never appears in BigQuery. Left empty on
# purpose: resolve_dataset() discovers it, so this script did not have to guess
# a number and be wrong about it. Override with --dataset or GA4_DATASET.
DATASET = os.environ.get("GA4_DATASET", "")

SITE_HOST = "aiprofitlab.io"

# ---------------------------------------------------------------------------
# Thresholds. These are judgements, not measurements, so they live in one place
# with the reasoning attached and are all overridable from the command line.
# ---------------------------------------------------------------------------

# "Bounced in five seconds" - the brief's phrase, taken literally. Short enough
# that no one read anything; long enough to clear a mis-click.
BOUNCE_SECONDS = 5

# "Read fully then left". Both halves are required: scroll without time is a
# scrollbar drag to the bottom, time without scroll is an abandoned tab.
READ_SCROLL = 75
READ_SECONDS = 30

# Scroll "completion". Not 100: the last few per cent of a page is footer, and
# holding an article to the standard of the footer being on screen understates
# every long page. 90 is where the article text ends on the v4 skin.
COMPLETE_SCROLL = 90

# A page shorter than the viewport reports max_scroll = 100 without any
# scrolling (see apl-analytics.js scrollPercent). Those views are counted, but
# flagged: they inflate completion on short pages and there is no way to tell
# them apart from a genuine read in the export.

# Events the report reads. Anything not listed is still exported by GA4 and
# still costs nothing extra to scan (BigQuery is columnar - the filter narrows
# rows, and event_params has to be read either way), but naming them keeps the
# pull honest about what the analysis actually uses.
CONVERSION_EVENTS = ("generate_lead", "begin_checkout", "add_payment_info", "purchase")
AIDEN_EVENTS = ("aiden_open", "aiden_first_message", "aiden_message", "aiden_lead_captured")
CLICK_EVENTS = ("cta_click", "outbound_click")
WANTED_EVENTS = (
    ("page_view", "page_exit", "scroll_depth", "session_start", "user_engagement")
    + CONVERSION_EVENTS + AIDEN_EVENTS + CLICK_EVENTS
    + ("demo_scenario", "simulator_preset", "filter_articles")
)


# ===========================================================================
# BigQuery plumbing
#
# Via the bq CLI rather than google-cloud-bigquery: bq ships with the Cloud SDK
# that is already installed and already authenticated, the library is not
# installed and would be this repo's first Python dependency. bq also gives the
# dry-run byte estimate for free, which is the one feature this script cannot
# do without.
# ===========================================================================

class BQError(RuntimeError):
    pass


def bq_path():
    path = shutil.which("bq")
    if not path:
        raise BQError(
            "`bq` is not on PATH. Install the Google Cloud SDK "
            "(https://cloud.google.com/sdk/docs/install), then `gcloud auth login`."
        )
    return path


def bq_run(args, timeout=600):
    """One bq invocation. Returns stdout; raises BQError with bq's own message."""
    cmd = [bq_path(), "--project_id=" + PROJECT, "--headless", "--format=json"] + args
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise BQError("bq timed out after %ds: %s" % (timeout, " ".join(args[:2])))
    if proc.returncode != 0:
        msg = (proc.stderr or proc.stdout or "").strip()
        raise BQError(msg or "bq exited %d with no message" % proc.returncode)
    return proc.stdout


def query(sql, dry_run=False, timeout=600):
    args = ["query", "--use_legacy_sql=false", "--max_rows=1000000"]
    if dry_run:
        args.append("--dry_run")
    args.append(sql)
    out = bq_run(args, timeout=timeout)
    if dry_run:
        return out
    out = out.strip()
    if not out:
        return []
    try:
        return json.loads(out)
    except json.JSONDecodeError as exc:
        raise BQError("could not parse bq output as JSON: %s\n%s" % (exc, out[:400]))


def dry_run_bytes(sql):
    """Bytes this query will scan, without running it. Costs nothing."""
    out = query(sql, dry_run=True)
    # --dry_run + --format=json still answers in prose on some SDK versions,
    # so accept either shape rather than depending on one.
    try:
        data = json.loads(out)
        for key in ("totalBytesProcessed", "estimatedBytesProcessed"):
            if isinstance(data, dict) and key in data:
                return int(data[key])
        if isinstance(data, dict):
            stats = data.get("statistics") or {}
            if "totalBytesProcessed" in stats:
                return int(stats["totalBytesProcessed"])
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    m = re.search(r"process\s+([\d,]+)\s+bytes", out or "", re.I)
    if m:
        return int(m.group(1).replace(",", ""))
    raise BQError("could not read a byte estimate from bq's dry run:\n" + (out or "")[:400])


def human_bytes(n):
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if n < 1024 or unit == "TiB":
            return "%.1f %s" % (n, unit) if unit != "B" else "%d B" % n
        n /= 1024.0


def list_datasets():
    """Every dataset in PROJECT, including hidden ones.

    `bq ls` alone hides the anonymous query-cache datasets, which is fine, but
    it has also been seen to print nothing at all where the REST endpoint
    answers correctly - so go to the API and be sure.
    """
    try:
        out = bq_run(["ls", "--datasets", "--max_results=1000"])
        names = [d["datasetReference"]["datasetId"] for d in json.loads(out or "[]")]
        if names:
            return names
    except (BQError, json.JSONDecodeError, KeyError, TypeError):
        pass
    try:
        token = subprocess.run(
            ["gcloud", "auth", "print-access-token"],
            capture_output=True, text=True, timeout=60,
        ).stdout.strip()
        if not token:
            return []
        import urllib.request
        req = urllib.request.Request(
            "https://bigquery.googleapis.com/bigquery/v2/projects/%s/datasets?all=true"
            % urllib.parse.quote(PROJECT),
            headers={"Authorization": "Bearer " + token},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.load(resp)
        return [d["datasetReference"]["datasetId"] for d in data.get("datasets", [])]
    except Exception:
        return []


NO_EXPORT_HELP = """
No GA4 export dataset (analytics_<property id>) exists in project %s.

As of the last check this is the expected state - the GA4 property is owned by
ai.profit.lab2026@gmail.com, that account has Owner on this project, but the
BigQuery link itself has not been created. To create it, signed in to GA4 as
ai.profit.lab2026@gmail.com:

  1. GA4 > Admin > Product links > BigQuery links > Link
  2. Choose project %s
  3. Data location: pick one and keep it - it cannot be changed later
  4. Data streams: include the web stream (G-SLR9GD3MJP)
  5. Frequency: tick Daily. Streaming is per-GB-billed and this report does
     not need it; Daily is free.

Then wait. The first events_YYYYMMDD table lands within about 24 hours, and
THE EXPORT IS NOT RETROACTIVE - day one of the data is the day you link it, so
nothing before that will ever be queryable here. That is a good reason to link
it today even if you do not run this report for a month.

Meanwhile, to see and review the report's layout with synthetic data:
    python3 tools/build_journey_report.py --sample
""".strip()


def resolve_dataset(explicit):
    """--dataset > GA4_DATASET > the single analytics_* dataset in the project."""
    if explicit:
        return explicit
    if DATASET:
        return DATASET
    names = list_datasets()
    exports = sorted(n for n in names if n.startswith("analytics_"))
    if len(exports) == 1:
        print("  dataset:  %s (discovered)" % exports[0])
        return exports[0]
    if len(exports) > 1:
        raise BQError(
            "project %s holds %d GA4 export datasets: %s\nPass --dataset to say which."
            % (PROJECT, len(exports), ", ".join(exports))
        )
    raise BQError(NO_EXPORT_HELP % (PROJECT, PROJECT))


# ===========================================================================
# The query
#
# One pull, flat, one row per event. Every section of the report is computed
# from this in Python. See COST DESIGN in the module docstring for why it is
# one query and not five.
# ===========================================================================

# Custom params are read as STRING regardless of how gtag typed them. This is
# not laziness: gtag decides int vs string vs double per value at send time, so
# `dwell_seconds` can arrive as an int on one hit and a double on the next, and
# a query that assumes int silently returns NULL for the others. Coalescing to
# text and parsing in Python cannot be wrong that way. The cast is free - the
# whole event_params column is read either way.
PARAM_SQL = """    (SELECT COALESCE(p.value.string_value,
                     CAST(p.value.int_value AS STRING),
                     CAST(p.value.double_value AS STRING),
                     CAST(p.value.float_value AS STRING))
     FROM UNNEST(event_params) p WHERE p.key = '{key}' LIMIT 1) AS {alias},"""

# key -> column alias. Grouped by which part of the site sends them.
PARAMS = [
    # GA4 built-ins
    ("ga_session_id", "ga_session_id"),
    ("page_location", "page_location"),
    ("page_referrer", "page_referrer"),
    ("page_title", "page_title"),
    ("engagement_time_msec", "engagement_time_msec"),
    ("session_engaged", "session_engaged"),
    # apl-analytics.js event-scoped custom dimensions, set on EVERY event
    ("page_type", "page_type"),
    ("content_language", "content_language"),
    ("article_slug", "article_slug"),
    ("page_path", "page_path"),
    # page_exit
    ("dwell_seconds", "dwell_seconds"),
    ("max_scroll", "max_scroll"),
    ("exit_intent", "exit_intent"),
    # scroll_depth
    ("percent_scrolled", "percent_scrolled"),
    # cta_click / outbound_click
    ("cta_type", "cta_type"),
    ("cta_location", "cta_location"),
    ("link_url", "link_url"),
    ("link_domain", "link_domain"),
    ("link_text", "link_text"),
    # aiden_*
    ("message_count", "message_count"),
    ("returning", "aiden_returning"),
    # conversions
    ("method", "lead_method"),
    ("value", "event_value"),
    ("currency", "currency"),
    ("transaction_id", "transaction_id"),
    ("payment_type", "payment_type"),
    # demos, simulators, blog hubs
    ("scenario", "scenario"),
    ("tool", "tool"),
    ("category", "category"),
]

DATE_RE = re.compile(r"^\d{8}$")


def build_sql(dataset, start, end, intraday=False, max_rows=500000):
    """The one query. `start` and `end` are YYYYMMDD strings.

    They are interpolated rather than passed as query parameters because bq's
    parameter syntax cannot reach _TABLE_SUFFIX in a way that still prunes
    partitions on every SDK version, and a filter that silently stops pruning
    is exactly the failure this script exists to prevent. They are generated
    from datetime and re-validated here, so nothing user-typed reaches the SQL.
    """
    for label, value in (("start", start), ("end", end)):
        if not DATE_RE.match(value or ""):
            raise ValueError("%s date must be YYYYMMDD, got %r" % (label, value))
    if not re.match(r"^[A-Za-z0-9_]+$", dataset or ""):
        raise ValueError("suspicious dataset name: %r" % dataset)
    if start > end:
        raise ValueError("start %s is after end %s" % (start, end))

    # The partition prune. Days outside the window are never opened.
    #
    # This also excludes events_intraday_* without naming it: that table's
    # _TABLE_SUFFIX is 'intraday_YYYYMMDD', and 'i' sorts above '9', so it
    # falls outside any BETWEEN of two 8-digit dates. --intraday adds it back.
    suffix = "_TABLE_SUFFIX BETWEEN '%s' AND '%s'" % (start, end)
    if intraday:
        suffix = "(%s OR _TABLE_SUFFIX LIKE 'intraday_%%')" % suffix

    params = "\n".join(
        PARAM_SQL.format(key=key, alias=alias) for key, alias in PARAMS
    )
    events = ", ".join("'%s'" % e for e in WANTED_EVENTS)

    return """-- AI Profit Lab visitor journey pull
-- Generated by tools/build_journey_report.py. Do not edit by hand; edit the
-- builder, which keeps the _TABLE_SUFFIX prune and the column list together.
SELECT
    event_date,
    event_timestamp,
    event_name,
    user_pseudo_id,
    device.category            AS device_category,
    device.operating_system    AS device_os,
    device.web_info.browser    AS browser,
    geo.country                AS country,
    traffic_source.source      AS source,
    traffic_source.medium      AS medium,
    traffic_source.name        AS campaign,
{params}
    _TABLE_SUFFIX              AS table_suffix
FROM `{project}.{dataset}.events_*`
WHERE {suffix}
  AND event_name IN ({events})
ORDER BY user_pseudo_id, event_timestamp
LIMIT {max_rows}
""".format(
        params=params,
        project=PROJECT,
        dataset=dataset,
        suffix=suffix,
        events=events,
        max_rows=int(max_rows),
    )


# ===========================================================================
# Cache
#
# Keyed on a hash of the exact SQL, so any change to the window, the dataset or
# the column list is a different key and cannot silently serve stale rows.
# ===========================================================================

def cache_path(sql):
    digest = hashlib.sha256(sql.encode("utf-8")).hexdigest()[:16]
    return os.path.join(CACHE_DIR, "events-%s.json" % digest)


def load_cache(sql):
    path = cache_path(sql)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            blob = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None
    return blob


def save_cache(sql, rows, meta):
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = cache_path(sql)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"meta": meta, "rows": rows}, fh)
    return path


def newest_cache():
    """Most recent cached pull, for --render-only after the window has moved."""
    if not os.path.isdir(CACHE_DIR):
        return None
    files = [os.path.join(CACHE_DIR, f) for f in os.listdir(CACHE_DIR)
             if f.startswith("events-") and f.endswith(".json")]
    if not files:
        return None
    newest = max(files, key=os.path.getmtime)
    try:
        with open(newest, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None


def fetch_events(sql, refresh=False, assume_yes=False, render_only=False):
    """Cached rows, or a fresh query after showing what it will cost."""
    if not refresh:
        blob = load_cache(sql)
        if blob:
            meta = blob.get("meta", {})
            print("  cache:    hit (%s rows, pulled %s) - this run bills nothing"
                  % (len(blob.get("rows", [])), meta.get("fetched_at", "?")))
            return blob["rows"], meta

    if render_only:
        blob = newest_cache()
        if blob:
            meta = blob.get("meta", {})
            print("  cache:    no entry for this window; rendering the most recent "
                  "cached pull instead (%s)" % meta.get("fetched_at", "?"))
            return blob["rows"], meta
        raise BQError(
            "--render-only was passed but there is nothing cached in %s.\n"
            "Run once without it to pull the data, or use --sample to see the "
            "report shape with synthetic events." % CACHE_DIR
        )

    est = dry_run_bytes(sql)
    # On-demand pricing, first 1 TiB per month free. Printed so the number is
    # a fact you approved rather than one you discovered on a bill.
    tib = est / float(1024 ** 4)
    print("  estimate: %s to scan (%.6f TiB, ~$%.4f at $6.25/TiB beyond the "
          "free 1 TiB/month)" % (human_bytes(est), tib, tib * 6.25))

    if not assume_yes:
        try:
            answer = input("  run it? [y/N] ").strip().lower()
        except EOFError:
            answer = ""
        if answer not in ("y", "yes"):
            raise SystemExit("  aborted - nothing was queried, nothing was billed.")

    started = datetime.now(timezone.utc)
    rows = query(sql)
    meta = {
        "fetched_at": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "bytes_estimated": est,
        "row_count": len(rows),
        "project": PROJECT,
    }
    path = save_cache(sql, rows, meta)
    print("  fetched:  %d rows, cached to %s" % (len(rows), os.path.relpath(path, ROOT)))
    return rows, meta


# ===========================================================================
# Normalisation
# ===========================================================================

def to_int(value, default=None):
    """int() first, float() only as a fallback.

    event_timestamp is a 16-digit microsecond epoch. int(float(x)) is exact
    below 2**53 and this is comfortably under, but routing timestamps through
    a float to parse them is the kind of thing that stays correct until it
    silently is not - and the whole report is built on their ordering.
    """
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        pass
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def to_bool(value):
    return str(value).strip().lower() in ("true", "1", "yes")


def norm_path(row):
    """One canonical path per page.

    Articles are served BOTH as /blog/en/<slug>.html and /blog/en/<slug>/ - the
    .htaccess pretty-URL rewrite means the same article appears under two
    page_locations, and left alone every article would split into two rows in
    the drop-off and content tables and look half as read as it is. Query
    strings go too, except that /en/checkout/?plan=... is genuinely three
    different pages, so `plan` is kept.
    """
    location = row.get("page_location") or ""
    raw = row.get("page_path") or location
    if not raw:
        return ""
    if "://" in raw:
        parsed = urllib.parse.urlsplit(raw)
        path, qs = parsed.path, parsed.query
    else:
        path, _, qs = raw.partition("?")
    # page_path comes from location.pathname, which never carries a query, so
    # the plan has to come from page_location or it is lost on every hit.
    if not qs and location:
        qs = urllib.parse.urlsplit(location).query
    path = re.sub(r"/index\.html$", "/", path)
    path = re.sub(r"\.html$", "", path)
    if len(path) > 1:
        path = path.rstrip("/")
    path = path or "/"
    plan = ""
    if qs:
        for key, values in urllib.parse.parse_qs(qs).items():
            if key.lower() == "plan" and values:
                plan = "?plan=" + values[0]
    return path + plan


def page_label(path):
    return path if path else "(unknown)"


# ---------------------------------------------------------------------------
# Classification fallbacks
#
# page_type, content_language and article_slug are event-scoped custom
# dimensions set by apl-analytics.js. THAT FILE IS NOT ON THE LIVE SERVER YET
# (/js/apl-analytics.js 404s as of 2026-08-25 - it is part of the un-deployed
# Clarity + analytics rollout), so every event currently arriving carries them
# empty. Without a fallback, section 4 filters on page_type == "article" and
# matches nothing, and the report looks broken when it is the deploy that is
# incomplete.
#
# These are a deliberate port of the same three functions in
# apl-analytics.js - keep them in step. Values derived here are INFERRED from
# the URL, and the report says so wherever they are used.
# ---------------------------------------------------------------------------

TYPE_PATTERNS = [
    (re.compile(r"/blog/(en|ar)/"), "article"),
    (re.compile(r"/academy/(en|ar)/"), "guide"),
    (re.compile(r"^/(blog|blog-ar)/?(index\.html)?$"), "blog-hub"),
    (re.compile(r"^/(academy|academy-ar)/?(index\.html)?$"), "academy-hub"),
    (re.compile(r"privacy|terms|legal|refund"), "legal"),
    (re.compile(r"service|package"), "services"),
    (re.compile(r"process"), "process"),
    (re.compile(r"about"), "about"),
    (re.compile(r"contact"), "contact"),
    (re.compile(r"simulator|calculator"), "tool"),
    (re.compile(r"demo"), "demo"),
    (re.compile(r"offer|storefront|claim"), "offer"),
    # norm_path() has already stripped the trailing slash, so /ar/ arrives as
    # /ar - which the anchored en/|ar/ form does not match, and the Arabic
    # home fell through to the generic "page".
    (re.compile(r"^/(en|ar)?$"), "home"),
    (re.compile(r"^/(en/|ar/)?(index[\w-]*\.html)?$"), "home"),
]


def bare(path):
    """Path without the query norm_path() preserves.

    apl-analytics.js classifies on location.pathname, which has no query at
    all. Leaving it on makes /en/checkout?plan=storefront match the `storefront`
    branch and come back as an offer page, where the live classifier says
    "page" - two different answers for one page view.
    """
    return (path or "").split("?", 1)[0]


def type_from_path(path):
    path = bare(path)
    for pattern, kind in TYPE_PATTERNS:
        if pattern.search(path):
            return kind
    return "page"


# The URL map, not a guess. This site does NOT mark Arabic with a suffix:
# English lives under /en/ (plus the apex and the /blog/, /academy/ and trust
# pages), and Arabic holds the bare root paths - /services, /process, /about,
# /contact and /smart-website-offer are all Arabic. Defaulting to English
# would put most of the Arabic site in the English segment.
#
# Source of truth for this map is run_sitemap.py; build_aiden_index.py's
# detect_lang() reaches the same conclusion ("site default is Arabic at the
# root"). If the URL map changes, all three change together.
EN_PATH = re.compile(
    r"^/en(/|$)"                       # /en/services, /en/checkout, ...
    r"|/blog/en/|/academy/en/"         # English articles and guides
    # The hubs THEMSELVES, anchored - an unanchored /blog also swallows
    # /blog/ar/<slug> and files every Arabic article under English.
    r"|^/(blog|academy)/?$"            # the English hubs (Arabic: -ar)
    r"|^/(privacy|terms|refund-policy)/?$"     # trust pages (Arabic: -ar)
)


def lang_from_path(path):
    """Inferred from the URL. Only used when content_language is absent."""
    path = bare(path)
    if path in ("", "/"):
        return "en"                    # the apex is the English home
    return "en" if EN_PATH.search(path) else "ar"


def slug_from_path(path):
    path = bare(path)
    if not re.search(r"/blog/(en|ar)/", path):
        return ""
    return path.rstrip("/").split("/")[-1].replace(".html", "")


# ===========================================================================
# Aiden transcripts
#
# The sheet is written by the Aiden backend, which lives in a different repo -
# there is no Sheet id here to read from, and putting a service-account key in
# this repo to fetch one would be worse than the small manual step. So: export
# the tab (File > Download > CSV) and point --aiden-csv at it.
#
# The join is exact, not fuzzy. aiden-chat.js reads GA4's own client_id and
# session_id via gtag('get') and sends them with every message, and GA4's
# client_id IS user_pseudo_id in the export while its session_id IS the
# ga_session_id param. Same two values on both sides.
#
# What the join CANNOT reach: any message sent before gtag answered - the
# widget sends whatever ids have arrived, and an empty pair is a row that will
# never match - and every row written before those columns were added.
# ===========================================================================

def _pick(fieldnames, *candidates):
    """First header matching any candidate, compared loosely (Client ID == client_id)."""
    def key(s):
        return re.sub(r"[^a-z0-9]", "", (s or "").lower())
    index = {key(f): f for f in fieldnames or []}
    for cand in candidates:
        if key(cand) in index:
            return index[key(cand)]
    for cand in candidates:
        ck = key(cand)
        for k, original in index.items():
            if ck and ck in k:
                return original
    return None


def load_aiden_csv(path):
    """(messages_by_session, diagnostics). Never raises on a shape surprise."""
    diag = {"path": path, "rows": 0, "joinable": 0, "columns": {}, "note": ""}
    if not path:
        diag["note"] = ("no --aiden-csv given, so section 2 shows where and when "
                        "Aiden was opened but not what was said")
        return {}, diag
    if not os.path.isfile(path):
        diag["note"] = "file not found: %s" % path
        return {}, diag

    by_session = defaultdict(list)
    try:
        with open(path, encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            fields = reader.fieldnames or []
            col = {
                "client": _pick(fields, "client_id", "ga_client_id", "clientId", "client"),
                "session": _pick(fields, "session_id", "ga_session_id", "sessionId", "session"),
                "message": _pick(fields, "message", "text", "question", "user_message", "content"),
                "reply": _pick(fields, "reply", "answer", "response", "bot_reply"),
                "time": _pick(fields, "timestamp", "time", "date", "created"),
                "role": _pick(fields, "role", "direction", "sender"),
            }
            diag["columns"] = {k: v for k, v in col.items() if v}
            if not col["client"] or not col["session"]:
                diag["note"] = (
                    "the CSV has no client_id/session_id columns (headers seen: %s), "
                    "so transcripts cannot be joined to sessions. Re-export the tab "
                    "after the Aiden backend has written those columns."
                    % (", ".join(fields[:12]) or "none")
                )
                return {}, diag
            for row in reader:
                diag["rows"] += 1
                client = (row.get(col["client"]) or "").strip()
                session = (row.get(col["session"]) or "").strip()
                if not client or not session:
                    continue
                diag["joinable"] += 1
                by_session[(client, session)].append({
                    "text": (row.get(col["message"]) if col["message"] else "") or "",
                    "reply": (row.get(col["reply"]) if col["reply"] else "") or "",
                    "time": (row.get(col["time"]) if col["time"] else "") or "",
                    "role": (row.get(col["role"]) if col["role"] else "") or "",
                })
    except (OSError, csv.Error, UnicodeDecodeError) as exc:
        diag["note"] = "could not read the CSV: %s" % exc
        return {}, diag

    unjoinable = diag["rows"] - diag["joinable"]
    if unjoinable:
        diag["note"] = ("%d of %d rows carry no GA4 ids and cannot be joined - "
                        "expected for rows written before the ids were added, or "
                        "where gtag had not answered when the message was sent"
                        % (unjoinable, diag["rows"]))
    return dict(by_session), diag


# ===========================================================================
# Session reconstruction  (report section 1)
# ===========================================================================

class Step:
    """One page view, and everything that happened while it was on screen."""

    __slots__ = ("path", "url", "title", "page_type", "slug", "lang", "ts",
                 "dwell", "dwell_measured", "scroll", "scroll_measured",
                 "exit_intent", "events", "is_exit", "referrer", "type_derived")

    def __init__(self, row, ts):
        self.path = norm_path(row)
        self.url = row.get("page_location") or ""
        self.title = row.get("page_title") or ""
        # The param when it is there, the URL when it is not. See the
        # Classification fallbacks block: today it is always not.
        self.page_type = row.get("page_type") or ""
        self.type_derived = not self.page_type
        if self.type_derived:
            self.page_type = type_from_path(self.path)
        self.slug = row.get("article_slug") or slug_from_path(self.path)
        self.lang = row.get("content_language") or lang_from_path(self.path)
        self.referrer = row.get("page_referrer") or ""
        self.ts = ts
        self.dwell = None
        self.dwell_measured = False
        self.scroll = None
        self.scroll_measured = False
        self.exit_intent = False
        self.events = []          # non-page_view events that happened here
        self.is_exit = False

    def names(self):
        return [e["event_name"] for e in self.events]


class Session:
    __slots__ = ("user", "sid", "rows", "steps", "start_ts", "end_ts",
                 "lang", "device", "country", "source", "medium", "campaign",
                 "conversions", "aiden_opens", "pre_page_events")

    def __init__(self, user, sid):
        self.user = user
        self.sid = sid
        self.rows = []
        self.steps = []
        self.pre_page_events = []   # events that arrived before any page_view
        self.start_ts = 0
        self.end_ts = 0
        self.lang = ""
        self.device = ""
        self.country = ""
        self.source = ""
        self.medium = ""
        self.campaign = ""
        self.conversions = []
        self.aiden_opens = []

    @property
    def key(self):
        return (self.user, self.sid)

    @property
    def landing(self):
        return self.steps[0].path if self.steps else ""

    @property
    def exit_page(self):
        return self.steps[-1].path if self.steps else ""

    @property
    def duration(self):
        """Seconds from first to last event. See INFERRED in the docstring."""
        return max(0.0, (self.end_ts - self.start_ts) / 1e6)

    @property
    def path_sequence(self):
        return [s.path for s in self.steps]

    @property
    def converted(self):
        return bool(self.conversions)


def build_sessions(rows):
    """Group the flat event pull into ordered sessions of ordered pages."""
    grouped = defaultdict(list)
    for row in rows:
        user = row.get("user_pseudo_id") or ""
        sid = row.get("ga_session_id") or ""
        if not user or not sid:
            continue          # cannot be placed in a session; see CANNOT ANSWER
        grouped[(user, sid)].append(row)

    sessions = []
    for (user, sid), evs in grouped.items():
        evs.sort(key=lambda r: to_int(r.get("event_timestamp"), 0))
        sess = Session(user, sid)
        sess.rows = evs
        sess.start_ts = to_int(evs[0].get("event_timestamp"), 0)
        sess.end_ts = to_int(evs[-1].get("event_timestamp"), 0)

        current = None
        for row in evs:
            ts = to_int(row.get("event_timestamp"), 0)
            name = row.get("event_name") or ""

            # Session-level attributes: first non-empty wins. A session cannot
            # honestly have two languages or two devices, and the first event
            # is the one closest to how it actually started.
            for attr, field in (("lang", "content_language"), ("device", "device_category"),
                                ("country", "country"), ("source", "source"),
                                ("medium", "medium"), ("campaign", "campaign")):
                if not getattr(sess, attr) and row.get(field):
                    setattr(sess, attr, row[field])

            if name == "page_view":
                current = Step(row, ts)
                sess.steps.append(current)
                continue

            target = current
            if target is None:
                sess.pre_page_events.append(row)
            else:
                target.events.append(row)

            if name == "page_exit":
                dwell = to_int(row.get("dwell_seconds"))
                scroll = to_int(row.get("max_scroll"))
                if target is not None:
                    if dwell is not None and not target.dwell_measured:
                        target.dwell, target.dwell_measured = dwell, True
                    if scroll is not None and not target.scroll_measured:
                        target.scroll, target.scroll_measured = scroll, True
                    if to_bool(row.get("exit_intent")):
                        target.exit_intent = True
            elif name == "scroll_depth" and target is not None and not target.scroll_measured:
                pct = to_int(row.get("percent_scrolled"))
                if pct is not None:
                    target.scroll = max(target.scroll or 0, pct)
            elif name in CONVERSION_EVENTS:
                sess.conversions.append({
                    "name": name, "ts": ts, "path": norm_path(row),
                    "method": row.get("lead_method") or "",
                    "value": row.get("event_value") or "",
                    "currency": row.get("currency") or "",
                    "pages_before": len(sess.steps),
                })
            elif name == "aiden_open":
                sess.aiden_opens.append({
                    "ts": ts, "path": norm_path(row),
                    "pages_before": max(0, len(sess.steps) - 1),
                    "returning": to_bool(row.get("aiden_returning")),
                    "step_index": len(sess.steps) - 1,
                })

        # Dwell for pages whose page_exit never arrived: the gap to the next
        # page_view. INFERRED, and weaker than the measurement it stands in for
        # - it counts time in a background tab, which page_exit excludes.
        for i, step in enumerate(sess.steps):
            if step.dwell is None:
                nxt = sess.steps[i + 1].ts if i + 1 < len(sess.steps) else sess.end_ts
                step.dwell = max(0, int(round((nxt - step.ts) / 1e6)))
                step.dwell_measured = False
        if sess.steps:
            sess.steps[-1].is_exit = True

        # A session whose events never carried content_language - i.e. every
        # session, until apl-analytics.js ships - still has to land in the
        # EN or AR segment, or both are empty and the split is useless.
        if not sess.lang and sess.steps:
            sess.lang = sess.steps[0].lang

        sessions.append(sess)

    sessions.sort(key=lambda s: s.start_ts)
    return sessions


# ===========================================================================
# Analysis
#
# Every function here takes an already-filtered list of sessions, so the
# segment split (EN/AR, mobile/desktop) is applied once, outside, and no
# function needs to know it exists.
# ===========================================================================

def median(values):
    vals = [v for v in values if v is not None]
    return round(statistics.median(vals), 1) if vals else None


def pct(part, whole):
    return round(100.0 * part / whole, 1) if whole else None


SEGMENTS = [
    ("all",     "All sessions",  lambda s: True),
    ("en",      "English",       lambda s: s.lang == "en"),
    ("ar",      "Arabic",        lambda s: s.lang == "ar"),
    ("mobile",  "Mobile",        lambda s: s.device == "mobile"),
    ("desktop", "Desktop",       lambda s: s.device == "desktop"),
]


def analyse_overview(sessions):
    durations = [s.duration for s in sessions]
    depths = [len(s.steps) for s in sessions]
    single = sum(1 for s in sessions if len(s.steps) == 1)
    measured, total = 0, 0
    for s in sessions:
        for step in s.steps:
            total += 1
            if step.dwell_measured:
                measured += 1
    return {
        "sessions": len(sessions),
        "visitors": len({s.user for s in sessions}),
        "pageviews": total,
        "median_duration": median(durations),
        "median_depth": median(depths),
        "single_page_pct": pct(single, len(sessions)),
        "dwell_coverage_pct": pct(measured, total),
        "converting": sum(1 for s in sessions if s.converted),
        "with_aiden": sum(1 for s in sessions if s.aiden_opens),
        "languages": Counter(s.lang or "(unset)" for s in sessions).most_common(),
        "devices": Counter(s.device or "(unset)" for s in sessions).most_common(),
        "countries": Counter(s.country or "(unset)" for s in sessions).most_common(8),
        "sources": Counter(
            "%s / %s" % (s.source or "(direct)", s.medium or "(none)") for s in sessions
        ).most_common(8),
    }


def analyse_journeys(sessions, limit=60):
    """Section 1: the literal reconstruction, richest sessions first.

    Ranked by pages then duration rather than by recency: a report you read
    once a week should open on the sessions that had something in them.
    """
    ranked = sorted(sessions, key=lambda s: (len(s.steps), s.duration), reverse=True)
    out = []
    for s in ranked[:limit]:
        out.append({
            "user": s.user,
            "sid": s.sid,
            "started": datetime.fromtimestamp(s.start_ts / 1e6, timezone.utc)
                               .strftime("%Y-%m-%d %H:%M UTC") if s.start_ts else "",
            "lang": s.lang, "device": s.device, "country": s.country,
            "source": "%s / %s" % (s.source or "(direct)", s.medium or "(none)"),
            "duration": round(s.duration, 1),
            "landing": s.landing,
            "exit": s.exit_page,
            "converted": [c["name"] for c in s.conversions],
            "aiden": len(s.aiden_opens),
            "steps": [{
                "path": st.path,
                "type": st.page_type,
                "dwell": st.dwell,
                "dwell_measured": st.dwell_measured,
                "scroll": st.scroll,
                "scroll_measured": st.scroll_measured,
                "exit_intent": st.exit_intent,
                "events": [e for e in st.names() if e not in ("page_exit", "scroll_depth")],
            } for st in s.steps],
        })
    return out


def analyse_aiden(sessions, transcripts, limit=40):
    """Section 2: where Aiden gets opened, after what, and what follows."""
    opens, by_page, pages_before, after_counter = [], Counter(), [], Counter()
    outcome = Counter()
    joined = 0

    for s in sessions:
        for op in s.aiden_opens:
            by_page[op["path"]] += 1
            pages_before.append(op["pages_before"])

            # Everything the session did after the open, in order. This is the
            # "and then what" the brief asks for, and it is measured: these are
            # real events with timestamps after the open.
            after = []
            for st in s.steps:
                if st.ts > op["ts"]:
                    after.append({"kind": "page", "name": st.path})
                for ev in st.events:
                    ets = to_int(ev.get("event_timestamp"), 0)
                    name = ev.get("event_name") or ""
                    if ets > op["ts"] and name not in ("page_exit", "scroll_depth", "user_engagement"):
                        after.append({"kind": "event", "name": name})
            for item in after:
                after_counter[item["name"]] += 1

            msgs = transcripts.get((s.user, s.sid), [])
            if msgs:
                joined += 1
            if any(c["name"] == "generate_lead" for c in s.conversions):
                outcome["led to generate_lead"] += 1
            elif any(c["name"] in ("begin_checkout", "purchase") for c in s.conversions):
                outcome["reached checkout"] += 1
            elif any(n == "aiden_lead_captured" for st in s.steps for n in st.names()):
                outcome["gave contact details in chat"] += 1
            elif any(x["kind"] == "page" for x in after):
                outcome["kept browsing"] += 1
            else:
                outcome["left after the chat"] += 1

            opens.append({
                "user": s.user, "sid": s.sid,
                "path": op["path"],
                "pages_before": op["pages_before"],
                "journey_before": [st.path for st in s.steps if st.ts <= op["ts"]],
                "returning": op["returning"],
                "lang": s.lang, "device": s.device,
                "messages": [m["text"][:400] for m in msgs if (m.get("text") or "").strip()][:10],
                "message_events": sum(
                    1 for st in s.steps for n in st.names() if n == "aiden_message"),
                "after": [x["name"] for x in after][:12],
                "converted": [c["name"] for c in s.conversions],
            })

    opens.sort(key=lambda o: (bool(o["messages"]), o["pages_before"]), reverse=True)
    return {
        "total_opens": len(opens),
        "sessions_with_aiden": sum(1 for s in sessions if s.aiden_opens),
        "open_rate_pct": pct(sum(1 for s in sessions if s.aiden_opens), len(sessions)),
        "joined_transcripts": joined,
        "median_pages_before": median(pages_before),
        "by_page": by_page.most_common(20),
        "after": after_counter.most_common(15),
        "outcome": outcome.most_common(),
        "opens": opens[:limit],
    }


def analyse_dropoff(sessions, bounce_seconds, read_scroll, read_seconds):
    """Section 3: ranked exit pages, split by HOW they were left."""
    views, exits = Counter(), Counter()
    dwell_on_exit, scroll_on_exit = defaultdict(list), defaultdict(list)
    classified = defaultdict(Counter)
    unmeasured = Counter()
    types = {}

    for s in sessions:
        for st in s.steps:
            views[st.path] += 1
            types.setdefault(st.path, st.page_type)
            if not st.is_exit:
                continue
            exits[st.path] += 1
            if st.scroll is not None:
                scroll_on_exit[st.path].append(st.scroll)
            if not st.dwell_measured:
                # An inferred dwell on the LAST page of a session is the gap to
                # nothing at all - it cannot separate a five-second bounce from
                # a ten-minute read, so it is excluded from the split rather
                # than allowed to invent one.
                unmeasured[st.path] += 1
                continue
            dwell_on_exit[st.path].append(st.dwell)
            if st.dwell <= bounce_seconds:
                classified[st.path]["bounced"] += 1
            elif st.dwell >= read_seconds and (st.scroll or 0) >= read_scroll:
                classified[st.path]["read_fully"] += 1
            else:
                classified[st.path]["partial"] += 1

    rows = []
    for path, n_exits in exits.most_common():
        c = classified[path]
        measured = sum(c.values())
        rows.append({
            "path": path,
            "type": types.get(path, ""),
            "views": views[path],
            "exits": n_exits,
            "exit_rate": pct(n_exits, views[path]),
            "median_dwell": median(dwell_on_exit[path]),
            "median_scroll": median(scroll_on_exit[path]),
            "bounced": c["bounced"],
            "read_fully": c["read_fully"],
            "partial": c["partial"],
            "bounced_pct": pct(c["bounced"], measured),
            "read_fully_pct": pct(c["read_fully"], measured),
            "measured": measured,
            "unmeasured": unmeasured[path],
        })
    totals = {
        "bounced": sum(r["bounced"] for r in rows),
        "read_fully": sum(r["read_fully"] for r in rows),
        "partial": sum(r["partial"] for r in rows),
        "unmeasured": sum(r["unmeasured"] for r in rows),
    }
    return {"rows": rows, "totals": totals,
            "thresholds": {"bounce_seconds": bounce_seconds,
                           "read_scroll": read_scroll, "read_seconds": read_seconds}}


def analyse_content(sessions, complete_scroll):
    """Section 4: per article. Keyed on the normalised path, not the slug -
    a page with no article_slug (a guide, a service page) still belongs here."""
    stat = defaultdict(lambda: {
        "views": 0, "entrances": 0, "dwells": [], "measured_dwells": 0,
        "scrolls": [], "complete": 0, "onward": 0, "clicks": 0,
        "precedes_aiden": 0, "precedes_lead": 0, "title": "", "slug": "", "type": "",
    })

    for s in sessions:
        first_aiden = min((o["ts"] for o in s.aiden_opens), default=None)
        first_lead = min((c["ts"] for c in s.conversions
                          if c["name"] == "generate_lead"), default=None)
        for i, st in enumerate(s.steps):
            if st.page_type not in ("article", "guide"):
                continue
            d = stat[st.path]
            d["views"] += 1
            d["title"] = d["title"] or st.title
            d["slug"] = d["slug"] or st.slug
            d["type"] = st.page_type
            if i == 0:
                d["entrances"] += 1
            if st.dwell is not None:
                d["dwells"].append(st.dwell)
                if st.dwell_measured:
                    d["measured_dwells"] += 1
            if st.scroll is not None:
                d["scrolls"].append(st.scroll)
                if st.scroll >= complete_scroll:
                    d["complete"] += 1
            clicked = any(n in CLICK_EVENTS for n in st.names())
            if clicked:
                d["clicks"] += 1
            # Onward = the visit continued, by either route: another page on
            # the site, or a click off it (WhatsApp is a click off it, and on
            # this site it is the most valuable one there is).
            if i + 1 < len(s.steps) or clicked:
                d["onward"] += 1
            if first_aiden is not None and first_aiden > st.ts:
                d["precedes_aiden"] += 1
            if first_lead is not None and first_lead > st.ts:
                d["precedes_lead"] += 1

    rows = []
    for path, d in stat.items():
        rows.append({
            "path": path, "title": d["title"], "slug": d["slug"], "type": d["type"],
            "views": d["views"], "entrances": d["entrances"],
            "median_dwell": median(d["dwells"]),
            "dwell_coverage_pct": pct(d["measured_dwells"], d["views"]),
            "median_scroll": median(d["scrolls"]),
            "completion_pct": pct(d["complete"], len(d["scrolls"])),
            "onward_pct": pct(d["onward"], d["views"]),
            "clicks": d["clicks"],
            "precedes_aiden": d["precedes_aiden"],
            "precedes_aiden_pct": pct(d["precedes_aiden"], d["views"]),
            "precedes_lead": d["precedes_lead"],
            "precedes_lead_pct": pct(d["precedes_lead"], d["views"]),
        })
    rows.sort(key=lambda r: (-r["views"], r["path"]))
    return rows


def analyse_paths(sessions, top=15):
    """Section 5: what converting sessions did, and how it differed."""
    converting = [s for s in sessions if s.converted]
    other = [s for s in sessions if not s.converted]

    seqs, entries, by_event = Counter(), Counter(), Counter()
    for s in converting:
        first = min(c["ts"] for c in s.conversions)
        before = [st.path for st in s.steps if st.ts <= first] or [s.landing]
        seqs[tuple(before)] += 1
        entries[before[0]] += 1
        for c in s.conversions:
            by_event[c["name"] + (" / " + c["method"] if c["method"] else "")] += 1

    def profile(group):
        if not group:
            return {"n": 0}
        return {
            "n": len(group),
            "median_pages": median([len(s.steps) for s in group]),
            "median_duration": median([s.duration for s in group]),
            "aiden_pct": pct(sum(1 for s in group if s.aiden_opens), len(group)),
            "article_pct": pct(sum(1 for s in group
                                   if any(st.page_type in ("article", "guide")
                                          for st in s.steps)), len(group)),
            "single_page_pct": pct(sum(1 for s in group if len(s.steps) == 1), len(group)),
            "top_landing": Counter(s.landing for s in group).most_common(6),
            "top_source": Counter("%s / %s" % (s.source or "(direct)", s.medium or "(none)")
                                  for s in group).most_common(5),
        }

    return {
        "converting": profile(converting),
        "non_converting": profile(other),
        "conversion_rate_pct": pct(len(converting), len(sessions)),
        "by_event": by_event.most_common(),
        "entry_pages": entries.most_common(10),
        "sequences": [{"path": list(seq), "n": n} for seq, n in seqs.most_common(top)],
    }


def analyse(sessions, transcripts, opts):
    """The whole report, computed once per segment."""
    out = {}
    for key, label, pred in SEGMENTS:
        subset = [s for s in sessions if pred(s)]
        out[key] = {
            "label": label,
            "overview": analyse_overview(subset),
            "journeys": analyse_journeys(subset),
            "aiden": analyse_aiden(subset, transcripts),
            "dropoff": analyse_dropoff(subset, opts.bounce_seconds,
                                       opts.read_scroll, opts.read_seconds),
            "content": analyse_content(subset, opts.complete_scroll),
            "paths": analyse_paths(subset),
        }
    return out


# ===========================================================================
# HTML rendering
#
# Self-contained on purpose: one file, no CDN, no network at all. It gets
# opened from disk, mailed, and read on a plane. Charts are inline SVG for the
# same reason - a charting library would be a script tag pointing at a CDN.
#
# Colours are the validated data-viz palette. The exit-reason split is a
# DIVERGING scale, not a traffic light: "read fully" and "bounced" are opposite
# poles with "partial" as the neutral middle. Green/red was tried first and is
# wrong - red vs green measures CVD delta-E 4.1, i.e. indistinguishable to a
# deuteranope, which is exactly the readership a drop-off report must not lose.
# Blue <-> red with a grey middle measures 23.8 and passes every check in both
# light and dark mode.
# ===========================================================================

CSS = """
:root {
  color-scheme: light;
  --plane:#f9f9f7; --surface:#fcfcfb; --ink:#0b0b0b; --ink-2:#52514e;
  --muted:#898781; --grid:#e1e0d9; --axis:#c3c2b7; --ring:rgba(11,11,11,0.10);
  --read:#2a78d6; --partial:#c3c2b7; --bounce:#d03b3b; --bar:#2a78d6;
  --good:#006300;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --plane:#0d0d0d; --surface:#1a1a19; --ink:#ffffff; --ink-2:#c3c2b7;
    --muted:#898781; --grid:#2c2c2a; --axis:#383835; --ring:rgba(255,255,255,0.10);
    --read:#3987e5; --partial:#4a4a46; --bounce:#d03b3b; --bar:#3987e5;
    --good:#0ca30c;
  }
}
* { box-sizing:border-box; }
body {
  margin:0; background:var(--plane); color:var(--ink);
  font:14px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;
  -webkit-font-smoothing:antialiased;
}
.wrap { max-width:1180px; margin:0 auto; padding:28px 20px 80px; }
h1 { font-size:26px; margin:0 0 4px; letter-spacing:-0.01em; }
h2 { font-size:18px; margin:0 0 2px; letter-spacing:-0.01em; }
h3 { font-size:14px; margin:22px 0 8px; color:var(--ink-2); font-weight:600; }
p  { margin:0 0 10px; }
a  { color:var(--read); }
.sub { color:var(--ink-2); font-size:13px; }
.tiny { color:var(--muted); font-size:12px; }
code { font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:12px;
       background:var(--surface); border:1px solid var(--ring); border-radius:4px;
       padding:1px 5px; }

.card { background:var(--surface); border:1px solid var(--ring); border-radius:10px;
        padding:18px 20px; margin:0 0 18px; }
.sec  { scroll-margin-top:16px; }
.sec > header { margin-bottom:14px; }

.badge { display:inline-block; font-size:11px; font-weight:600; letter-spacing:.03em;
         text-transform:uppercase; padding:2px 7px; border-radius:999px;
         border:1px solid var(--ring); color:var(--ink-2); background:var(--plane); }
.badge.m { color:var(--read); border-color:var(--read); }
.badge.i { color:var(--muted); }

.tiles { display:grid; grid-template-columns:repeat(auto-fit,minmax(132px,1fr)); gap:10px; }
.tile { background:var(--plane); border:1px solid var(--ring); border-radius:8px; padding:11px 13px; }
.tile b { display:block; font-size:23px; font-weight:600; line-height:1.15; }
.tile span { display:block; font-size:11.5px; color:var(--ink-2); margin-top:2px; }

table { width:100%; border-collapse:collapse; font-size:13px; }
.scroller { overflow-x:auto; }
th, td { text-align:left; padding:7px 9px; border-bottom:1px solid var(--grid); vertical-align:top; }
th { font-size:11px; text-transform:uppercase; letter-spacing:.04em; color:var(--muted);
     font-weight:600; white-space:nowrap; border-bottom:1px solid var(--axis); }
td.n, th.n { text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }
tbody tr:hover { background:var(--plane); }
.path { font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:12px; word-break:break-all; }

.tabs { display:flex; flex-wrap:wrap; gap:6px; margin:0 0 18px; }
.tabs button { font:inherit; font-size:13px; padding:6px 13px; border-radius:999px; cursor:pointer;
               border:1px solid var(--ring); background:var(--surface); color:var(--ink-2); }
.tabs button[aria-selected="true"] { background:var(--read); border-color:var(--read); color:#fff; }
.seg[hidden] { display:none; }

.legend { display:flex; flex-wrap:wrap; gap:14px; margin:0 0 10px; font-size:12px; color:var(--ink-2); }
.legend i { display:inline-block; width:11px; height:11px; border-radius:3px; margin-right:5px;
            vertical-align:-1px; }

.chart { width:100%; height:auto; display:block; }
.chart text { font:11px system-ui,-apple-system,sans-serif; fill:var(--muted); }
.chart text.val { fill:var(--ink-2); font-variant-numeric:tabular-nums; }
/* Labels printed INSIDE a stacked segment. The colour is picked per fill by
   measured contrast, not by taste: near-black on blue (4.46:1) and on the
   light grey (11:1), white on red (4.80:1) and on the dark grey (8.90:1).
   These must not inherit --ink-2, which sits at ~1.9:1 on the blue. */
.chart text.val.on-read    { fill:#0b0b0b; }
.chart text.val.on-partial { fill:#0b0b0b; }
.chart text.val.on-bounce  { fill:#ffffff; }
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) .chart text.val.on-partial { fill:#ffffff; }
}
.chart rect { shape-rendering:crispEdges; }

.trail { display:flex; flex-wrap:wrap; align-items:center; gap:5px; }
.hop { display:inline-flex; align-items:center; gap:5px; background:var(--plane);
       border:1px solid var(--ring); border-radius:6px; padding:3px 7px;
       font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:11.5px; }
.hop .d { color:var(--muted); font-family:system-ui,sans-serif; }
.arrow { color:var(--muted); }
.ev { display:inline-block; background:var(--read); color:#fff; border-radius:4px;
      padding:1px 6px; font-size:11px; font-family:system-ui,sans-serif; }
.ev.x { background:var(--bounce); }
.quote { border-left:2px solid var(--read); padding:2px 0 2px 10px; margin:4px 0;
         color:var(--ink-2); font-size:12.5px; }

.note { background:var(--plane); border:1px solid var(--ring); border-left:3px solid var(--muted);
        border-radius:6px; padding:11px 14px; margin:12px 0; font-size:13px; color:var(--ink-2); }
.note.warn { border-left-color:var(--bounce); }
.note b { color:var(--ink); }
ul.tight { margin:6px 0; padding-left:20px; }
ul.tight li { margin:4px 0; color:var(--ink-2); }

#tip { position:fixed; z-index:9; pointer-events:none; opacity:0; transition:opacity .1s;
       background:var(--ink); color:var(--surface); font-size:12px; padding:5px 8px;
       border-radius:5px; max-width:280px; }
#tip.on { opacity:1; }
@media print { .tabs { display:none; } .seg[hidden] { display:block; } }
"""

TIP_JS = """
(function(){
  var tip = document.getElementById('tip');
  document.addEventListener('mouseover', function(e){
    var t = e.target.closest('[data-tip]');
    if (!t) return;
    tip.textContent = t.getAttribute('data-tip');
    tip.classList.add('on');
  });
  document.addEventListener('mousemove', function(e){
    if (!tip.classList.contains('on')) return;
    var x = Math.min(e.clientX + 14, window.innerWidth - tip.offsetWidth - 8);
    tip.style.left = x + 'px';
    tip.style.top = (e.clientY + 16) + 'px';
  });
  document.addEventListener('mouseout', function(e){
    if (e.target.closest('[data-tip]')) tip.classList.remove('on');
  });
  var tabs = document.querySelectorAll('.tabs button');
  tabs.forEach(function(btn){
    btn.addEventListener('click', function(){
      tabs.forEach(function(b){ b.setAttribute('aria-selected', b === btn); });
      document.querySelectorAll('.seg').forEach(function(s){
        s.hidden = (s.dataset.seg !== btn.dataset.seg);
      });
      window.scrollTo({top:0, behavior:'smooth'});
    });
  });
})();
"""


def esc(value):
    return (str(value if value is not None else "")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def num(value, suffix="", dash="—"):
    return dash if value is None else "%s%s" % (value, suffix)


def secs(value):
    """Seconds as something a person reads without doing arithmetic."""
    if value is None:
        return "—"
    value = float(value)
    if value < 60:
        return "%gs" % round(value, 1)
    return "%dm %02ds" % (int(value // 60), int(round(value % 60)))


# --- charts ----------------------------------------------------------------

def plural(value, unit):
    """'1 session', not '1 sessions'. Word units only; '%' and '×' pass through."""
    if value == 1 and unit.startswith(" ") and unit.endswith("s"):
        return unit[:-1]
    return unit


def bar_chart(rows, value_key, label_key, unit="", height_per=22, max_rows=12):
    """Horizontal bars, one series. No legend - the heading names the series.

    4px rounded ends on the data side only, bars anchored to a shared baseline,
    values direct-labelled outside the bar so nothing depends on reading a
    length against a gridline.
    """
    rows = rows[:max_rows]
    if not rows:
        return '<p class="tiny">No rows in this segment.</p>'
    top = max((r[value_key] or 0) for r in rows) or 1
    # Wide enough for a full article path (/blog/ar/<10-char date>-<slug>),
    # because the label IS the identity here - truncating the slug turns two
    # different articles into the same-looking row.
    label_w, gap, val_w = 300, 8, 62
    plot_w = 560
    height = height_per * len(rows) + 6
    total_w = label_w + gap + plot_w + gap + val_w

    parts = ['<svg class="chart" viewBox="0 0 %d %d" role="img" '
             'preserveAspectRatio="xMinYMin meet">' % (total_w, height)]
    for i, row in enumerate(rows):
        value = row[value_key] or 0
        y = i * height_per + 3
        bar_h = height_per - 9
        width = max(2.0, plot_w * value / top)
        label = str(row[label_key])
        shown = label if len(label) <= 48 else "…" + label[-47:]
        tip = "%s — %s%s" % (label, value, plural(value, unit))
        parts.append(
            '<text x="%d" y="%.1f" text-anchor="end">%s</text>'
            % (label_w, y + bar_h * 0.78, esc(shown)))
        parts.append(
            '<rect x="%d" y="%.1f" width="%.1f" height="%d" rx="4" fill="var(--bar)" '
            'data-tip="%s"><title>%s</title></rect>'
            % (label_w + gap, y, width, bar_h, esc(tip), esc(tip)))
        parts.append(
            '<text class="val" x="%.1f" y="%.1f">%s%s</text>'
            % (label_w + gap + width + 6, y + bar_h * 0.78, esc(value),
               esc(plural(value, unit))))
    parts.append("</svg>")
    return "".join(parts)


EXIT_LEGEND = (
    '<div class="legend">'
    '<span><i style="background:var(--read)"></i>Read fully, then left</span>'
    '<span><i style="background:var(--partial)"></i>Partial</span>'
    '<span><i style="background:var(--bounce)"></i>Bounced</span>'
    '</div>'
)


def exit_split_chart(rows, thresholds, max_rows=12):
    """Stacked diverging bars: read-fully <- partial -> bounced, per exit page.

    A 2px surface gap between segments so two adjacent fills never read as one,
    and each segment carries its own count as a direct label wherever it fits.
    Only exit views with a MEASURED dwell are in here; the count that had none
    is stated beside the chart rather than silently folded into a bucket.
    """
    rows = [r for r in rows if r["measured"]][:max_rows]
    if not rows:
        return ('<p class="tiny">No exits in this segment carry a measured dwell, '
                'so there is nothing to split. See the note below.</p>')
    top = max(r["measured"] for r in rows) or 1
    label_w, gap, val_w, plot_w, height_per = 300, 8, 74, 500, 24
    height = height_per * len(rows) + 6
    total_w = label_w + gap + plot_w + gap + val_w

    parts = [EXIT_LEGEND,
             '<svg class="chart" viewBox="0 0 %d %d" role="img" '
             'preserveAspectRatio="xMinYMin meet">' % (total_w, height)]
    order = (("read_fully", "var(--read)", "read fully", "on-read"),
             ("partial", "var(--partial)", "partial", "on-partial"),
             ("bounced", "var(--bounce)", "bounced", "on-bounce"))
    for i, row in enumerate(rows):
        y = i * height_per + 3
        bar_h = height_per - 9
        x = float(label_w + gap)
        label = row["path"]
        shown = label if len(label) <= 48 else "…" + label[-47:]
        parts.append('<text x="%d" y="%.1f" text-anchor="end">%s</text>'
                     % (label_w, y + bar_h * 0.78, esc(shown)))
        # Only the segments that actually have a count, so the rounded data
        # end lands on the last VISIBLE segment. Rounding by position in the
        # full order puts a square edge at the end of any bar whose last
        # bucket happens to be empty.
        present = [(k, f, w, c) for k, f, w, c in order if row[k]]
        for j, (key, fill, word, ink) in enumerate(present):
            count = row[key]
            width = plot_w * count / top
            # Data end only. The baseline end stays square - it is anchored to
            # the axis, and a rounded corner there reads as a gap.
            radius = ' rx="4"' if j == len(present) - 1 else ""
            tip = "%s — %d of %d measured exits %s (%s)" % (
                label, count, row["measured"], word,
                "dwell <= %ds" % thresholds["bounce_seconds"] if key == "bounced"
                else ("scroll >= %d%% and dwell >= %ds" % (thresholds["read_scroll"],
                                                           thresholds["read_seconds"])
                      if key == "read_fully" else "in between"))
            parts.append(
                '<rect x="%.1f" y="%.1f" width="%.1f" height="%d"%s fill="%s" '
                'data-tip="%s"><title>%s</title></rect>'
                % (x, y, max(1.0, width - 2), bar_h, radius, fill, esc(tip), esc(tip)))
            if width >= 26:
                parts.append('<text class="val %s" x="%.1f" y="%.1f" '
                             'text-anchor="middle">%d</text>'
                             % (ink, x + width / 2 - 1, y + bar_h * 0.74, count))
            x += width
        parts.append('<text class="val" x="%.1f" y="%.1f">%s exits</text>'
                     % (label_w + gap + plot_w + 6, y + bar_h * 0.78, row["exits"]))
    parts.append("</svg>")
    return "".join(parts)


# --- section renderers -----------------------------------------------------

MEAS = '<span class="badge m">measured</span>'
INF = '<span class="badge i">inferred</span>'


def render_overview(seg, key):
    o = seg["overview"]
    tiles = [
        ("Sessions", o["sessions"]), ("Visitors", o["visitors"]),
        ("Page views", o["pageviews"]),
        ("Median duration", secs(o["median_duration"])),
        ("Median pages / session", num(o["median_depth"])),
        ("Single-page sessions", num(o["single_page_pct"], "%")),
        ("Sessions that converted", o["converting"]),
        ("Sessions that opened Aiden", o["with_aiden"]),
    ]
    html = ['<section class="card sec" id="%s-glance">' % key,
            '<header><h2>At a glance</h2>'
            '<p class="sub">%s. "Visitors" counts browsers, not people — see '
            '<a href="#cannot">what the data cannot answer</a>.</p></header>'
            '<div class="tiles">' % MEAS]
    for label, value in tiles:
        html.append('<div class="tile"><b>%s</b><span>%s</span></div>'
                    % (esc(value), esc(label)))
    html.append('</div>')
    html.append(
        '<p class="tiny" style="margin-top:12px">Dwell is a real measurement on '
        '<b>%s%%</b> of page views (a <code>page_exit</code> arrived); the rest is '
        'inferred from the gap to the next page view.</p>'
        % num(o["dwell_coverage_pct"], ""))

    def mini(title, pairs):
        # One <div> per block, not a bare h3 + table: these sit in a CSS grid,
        # and loose siblings get placed in separate cells - which put every
        # heading in one column and its own table in the next.
        if not pairs:
            return ""
        total = sum(n for _, n in pairs) or 1
        out = ['<div><h3>%s</h3><table><tbody>' % esc(title)]
        for name, n in pairs:
            out.append('<tr><td>%s</td><td class="n">%d</td><td class="n">%s%%</td></tr>'
                       % (esc(name), n, round(100.0 * n / total, 1)))
        return "".join(out) + '</tbody></table></div>'

    html.append('<div style="display:grid;grid-template-columns:repeat(auto-fit,'
                'minmax(230px,1fr));gap:0 26px">')
    html.append(mini("Language", o["languages"]))
    html.append(mini("Device", o["devices"]))
    html.append(mini("Country", o["countries"]))
    html.append(mini("Source / medium", o["sources"]))
    html.append('</div></section>')
    return "".join(html)


def render_journeys(seg, key):
    rows = seg["journeys"]
    html = ['<section class="card sec" id="%s-journeys"><header>' % key,
            '<h2>1 &middot; Session reconstruction</h2>'
            '<p class="sub">Every page in the order it was seen, with the dwell and '
            'scroll depth reached on each. Deepest sessions first. Order is %s; a dwell '
            'marked <span class="badge i">inf</span> had no <code>page_exit</code> and is '
            'the gap to the next page view instead.</p></header>' % MEAS]
    if not rows:
        html.append('<p class="tiny">No sessions in this segment.</p></section>')
        return "".join(html)
    html.append('<div class="scroller"><table><thead><tr>'
                '<th>Session</th><th class="n">Dur.</th><th>Journey — page · dwell · scroll</th>'
                '</tr></thead><tbody>')
    for s in rows:
        badges = ""
        if s["converted"]:
            badges += " ".join('<span class="ev">%s</span>' % esc(c) for c in s["converted"])
        if s["aiden"]:
            badges += ' <span class="ev">aiden ×%d</span>' % s["aiden"]
        hops = []
        for i, st in enumerate(s["steps"]):
            if i:
                hops.append('<span class="arrow">&rsaquo;</span>')
            mark = "" if st["dwell_measured"] else '<span class="badge i">inf</span>'
            scroll = ("%d%%" % st["scroll"]) if st["scroll"] is not None else "—"
            extra = "".join(' <span class="ev">%s</span>' % esc(e) for e in st["events"])
            hops.append(
                '<span class="hop" data-tip="%s">%s<span class="d">%s%s · %s</span>%s</span>'
                % (esc("%s — %s, scrolled %s%s" % (
                       st["path"], secs(st["dwell"]), scroll,
                       "" if st["dwell_measured"] else " (inferred)")),
                   esc(st["path"] if len(st["path"]) <= 44 else "…" + st["path"][-43:]),
                   secs(st["dwell"]), mark, scroll, extra))
        html.append(
            '<tr><td><span class="tiny">%s<br>%s · %s · %s<br>%s</span></td>'
            '<td class="n">%s</td><td><div class="trail">%s</div>%s</td></tr>'
            % (esc(s["started"]), esc(s["lang"] or "?"), esc(s["device"] or "?"),
               esc(s["country"] or "?"), esc(s["source"]),
               secs(s["duration"]), "".join(hops),
               ('<div style="margin-top:5px">%s</div>' % badges) if badges else ""))
    html.append('</tbody></table></div>'
                '<p class="tiny">Showing the %d deepest of %d sessions. '
                'Visitor ids are omitted here on purpose — the row is the journey, '
                'not the person.</p></section>'
                % (len(rows), seg["overview"]["sessions"]))
    return "".join(html)


def render_aiden(seg, key, aiden_diag):
    a = seg["aiden"]
    html = ['<section class="card sec" id="%s-aiden"><header>' % key,
            '<h2>2 &middot; Aiden touchpoints</h2>'
            '<p class="sub">Where the chat was opened, how much of the site came first, '
            'and what happened next. The page and the ordering are %s; the questions come '
            'from the Aiden_Chat sheet, joined on GA4 <code>client_id</code> + '
            '<code>session_id</code>.</p></header>' % MEAS]
    html.append('<div class="tiles">')
    for label, value in (("Opens", a["total_opens"]),
                         ("Sessions with an open", a["sessions_with_aiden"]),
                         ("Open rate", num(a["open_rate_pct"], "%")),
                         ("Median pages before opening", num(a["median_pages_before"])),
                         ("Opens with a joined transcript", a["joined_transcripts"])):
        html.append('<div class="tile"><b>%s</b><span>%s</span></div>' % (esc(value), esc(label)))
    html.append('</div>')

    if aiden_diag.get("note"):
        html.append('<div class="note"><b>Transcripts:</b> %s</div>' % esc(aiden_diag["note"]))

    if a["by_page"]:
        html.append('<h3>Where Aiden gets opened</h3>')
        html.append(bar_chart([{"p": p, "n": n} for p, n in a["by_page"]], "n", "p", " opens"))
    if a["after"]:
        html.append('<h3>What happened after the open, ranked</h3>')
        html.append(bar_chart([{"p": p, "n": n} for p, n in a["after"]], "n", "p", "×"))
    if a["outcome"]:
        html.append('<h3>How the session ended</h3><table><tbody>')
        for name, n in a["outcome"]:
            html.append('<tr><td>%s</td><td class="n">%d</td></tr>' % (esc(name), n))
        html.append('</tbody></table>')

    if a["opens"]:
        html.append('<h3>Individual touchpoints</h3><div class="scroller"><table><thead><tr>'
                    '<th>Opened on</th><th class="n">Pages first</th>'
                    '<th>Journey before the open</th><th>Asked</th><th>Then</th>'
                    '</tr></thead><tbody>')
        for o in a["opens"]:
            before = " &rsaquo; ".join(
                '<span class="hop">%s</span>' % esc(p if len(p) <= 30 else "…" + p[-29:])
                for p in o["journey_before"]) or '<span class="tiny">—</span>'
            if o["messages"]:
                asked = "".join('<div class="quote">%s</div>' % esc(m) for m in o["messages"])
            elif o["message_events"]:
                asked = ('<span class="tiny">%d message(s) sent, but no matching sheet '
                         'row — see the note above</span>' % o["message_events"])
            else:
                asked = '<span class="tiny">opened, never typed</span>'
            # A path is a page they moved to, anything else is an event they
            # fired; the two read differently and must not share a chip style.
            chips = []
            for n in o["after"]:
                if n.startswith("/"):
                    chips.append('<span class="hop">%s</span>' % esc(n))
                else:
                    chips.append('<span class="ev%s">%s</span>'
                                 % (" x" if n in CONVERSION_EVENTS else "", esc(n)))
            after = " ".join(chips) or '<span class="tiny">nothing</span>'
            html.append('<tr><td class="path">%s<br><span class="tiny">%s · %s%s</span></td>'
                        '<td class="n">%d</td><td>%s</td><td>%s</td><td>%s</td></tr>'
                        % (esc(o["path"]), esc(o["lang"] or "?"), esc(o["device"] or "?"),
                           " · returning" if o["returning"] else "",
                           o["pages_before"], before, asked, after))
        html.append('</tbody></table></div>')
    html.append('</section>')
    return "".join(html)


def render_dropoff(seg, key):
    d = seg["dropoff"]
    t = d["thresholds"]
    html = ['<section class="card sec" id="%s-dropoff"><header>' % key,
            '<h2>3 &middot; Drop-off analysis</h2>'
            '<p class="sub">Exit pages ranked by how often a session ended there. The split '
            'is the point: <b>read fully then left</b> (scroll &ge; %d%% and dwell &ge; %ds) '
            'and <b>bounced</b> (dwell &le; %ds) are opposite findings on the same page — one '
            'says the page worked and had no next step, the other says it never landed.</p>'
            '</header>' % (t["read_scroll"], t["read_seconds"], t["bounce_seconds"])]
    tot = d["totals"]
    html.append('<div class="tiles">')
    for label, value in (("Read fully, then left", tot["read_fully"]),
                         ("Partial", tot["partial"]),
                         ("Bounced (&le;%ds)" % t["bounce_seconds"], tot["bounced"]),
                         ("Exits with no measured dwell", tot["unmeasured"])):
        html.append('<div class="tile"><b>%s</b><span>%s</span></div>' % (esc(value), label))
    html.append('</div>')
    if tot["unmeasured"]:
        html.append(
            '<div class="note"><b>%d exits could not be classified.</b> No '
            '<code>page_exit</code> arrived for them, and an inferred dwell on the last '
            'page of a session is the gap to nothing at all — it cannot tell a '
            'five-second bounce from a ten-minute read. They are counted in the exit '
            'totals and excluded from the split, so the bounce figure is a <b>floor</b>, '
            'not a total.</div>' % tot["unmeasured"])

    html.append('<h3>How each exit page was left</h3>')
    html.append(exit_split_chart(d["rows"], t))
    html.append('<h3>Every exit page</h3><div class="scroller"><table><thead><tr>'
                '<th>Page</th><th>Type</th><th class="n">Views</th><th class="n">Exits</th>'
                '<th class="n">Exit rate</th><th class="n">Median dwell</th>'
                '<th class="n">Median scroll</th><th class="n">Read fully</th>'
                '<th class="n">Bounced</th></tr></thead><tbody>')
    for r in d["rows"]:
        html.append(
            '<tr><td class="path">%s</td><td class="tiny">%s</td><td class="n">%d</td>'
            '<td class="n">%d</td><td class="n">%s</td><td class="n">%s</td>'
            '<td class="n">%s</td><td class="n">%s</td><td class="n">%s</td></tr>'
            % (esc(r["path"]), esc(r["type"] or "—"), r["views"], r["exits"],
               num(r["exit_rate"], "%"), secs(r["median_dwell"]),
               num(r["median_scroll"], "%"),
               "%d (%s)" % (r["read_fully"], num(r["read_fully_pct"], "%")),
               "%d (%s)" % (r["bounced"], num(r["bounced_pct"], "%"))))
    html.append('</tbody></table></div>'
                '<p class="tiny">Exit rate = exits &divide; views of that page. Read-fully '
                'and bounced percentages are of the <b>measured</b> exits on that page, not '
                'of all of them.</p></section>')
    return "".join(html)


def render_content(seg, key):
    rows = seg["content"]
    html = ['<section class="card sec" id="%s-content"><header>' % key,
            '<h2>4 &middot; Content performance</h2>'
            '<p class="sub">Articles and guides only. "Precedes Aiden" and "precedes a lead" '
            'are ordering facts — the event happened later in the same session — and %s. '
            'They are <b>not</b> a claim that the article caused it.</p></header>' % MEAS]
    if not rows:
        html.append('<p class="tiny">No article or guide views in this segment.</p></section>')
        return "".join(html)
    html.append('<h3>Most-read</h3>')
    html.append(bar_chart([{"p": r["path"], "n": r["views"]} for r in rows], "n", "p", " views"))
    html.append('<div class="scroller"><table><thead><tr>'
                '<th>Article</th><th class="n">Views</th><th class="n">Entrances</th>'
                '<th class="n">Median dwell</th><th class="n">Median scroll</th>'
                '<th class="n">Completed</th><th class="n">Onward</th>'
                '<th class="n">Precedes Aiden</th><th class="n">Precedes lead</th>'
                '</tr></thead><tbody>')
    for r in rows:
        title = r["title"] or r["path"]
        html.append(
            '<tr><td><span class="path">%s</span>%s</td><td class="n">%d</td>'
            '<td class="n">%d</td><td class="n">%s<br><span class="tiny">%s meas.</span></td>'
            '<td class="n">%s</td><td class="n">%s</td><td class="n">%s</td>'
            '<td class="n">%s</td><td class="n">%s</td></tr>'
            % (esc(r["path"]),
               ('<br><span class="tiny">%s</span>' % esc(title[:80])) if r["title"] else "",
               r["views"], r["entrances"], secs(r["median_dwell"]),
               num(r["dwell_coverage_pct"], "%"), num(r["median_scroll"], "%"),
               num(r["completion_pct"], "%"), num(r["onward_pct"], "%"),
               "%d (%s)" % (r["precedes_aiden"], num(r["precedes_aiden_pct"], "%")),
               "%d (%s)" % (r["precedes_lead"], num(r["precedes_lead_pct"], "%"))))
    html.append('</tbody></table></div>')
    html.append(
        '<p class="tiny"><b>Completed</b> = share of views whose max scroll reached %d%%. '
        'Beware short pages: a page shorter than the viewport reports 100%% without anyone '
        'scrolling, and the export cannot tell that apart from a real read. '
        '<b>Onward</b> = the visit continued, either to another page on the site or via a '
        'CTA / outbound click off it.</p></section>' % COMPLETE_SCROLL)
    return "".join(html)


def render_paths(seg, key):
    p = seg["paths"]
    c, n = p["converting"], p["non_converting"]
    html = ['<section class="card sec" id="%s-paths"><header>' % key,
            '<h2>5 &middot; Path to conversion</h2>'
            '<p class="sub">The page sequence up to the first conversion event in each '
            'converting session, and how those sessions differ from the rest. Sequences and '
            'events are %s. The difference is a <b>correlation across a small number of '
            'sessions</b> — read it as a lead to test, never as a cause.</p></header>' % MEAS]
    html.append('<div class="tiles">'
                '<div class="tile"><b>%s</b><span>Converting sessions</span></div>'
                '<div class="tile"><b>%s</b><span>Conversion rate</span></div>'
                '</div>' % (c["n"], num(p["conversion_rate_pct"], "%")))
    if not c["n"]:
        html.append('<p class="tiny">No conversion events in this segment, so there is no '
                    'path to describe.</p></section>')
        return "".join(html)

    html.append('<h3>Converting vs everything else</h3><div class="scroller"><table><thead><tr>'
                '<th></th><th class="n">Sessions</th><th class="n">Median pages</th>'
                '<th class="n">Median duration</th><th class="n">Single-page</th>'
                '<th class="n">Opened Aiden</th><th class="n">Read an article</th>'
                '</tr></thead><tbody>')
    for label, g in (("Converted", c), ("Did not convert", n)):
        if not g.get("n"):
            continue
        html.append('<tr><td><b>%s</b></td><td class="n">%d</td><td class="n">%s</td>'
                    '<td class="n">%s</td><td class="n">%s</td><td class="n">%s</td>'
                    '<td class="n">%s</td></tr>'
                    % (label, g["n"], num(g["median_pages"]), secs(g["median_duration"]),
                       num(g["single_page_pct"], "%"), num(g["aiden_pct"], "%"),
                       num(g["article_pct"], "%")))
    html.append('</tbody></table></div>')

    if p["by_event"]:
        html.append('<h3>Which conversions fired</h3>')
        html.append(bar_chart([{"p": k, "n": v} for k, v in p["by_event"]], "n", "p", "×"))

    html.append('<h3>The sequences that preceded a conversion</h3>'
                '<div class="scroller"><table><thead><tr><th class="n">×</th>'
                '<th>Page sequence, in order</th></tr></thead><tbody>')
    for seq in p["sequences"]:
        hops = " &rsaquo; ".join('<span class="hop">%s</span>' % esc(step)
                                 for step in seq["path"])
        html.append('<tr><td class="n">%d</td><td><div class="trail">%s</div></td></tr>'
                    % (seq["n"], hops))
    html.append('</tbody></table></div>')

    if p["entry_pages"]:
        html.append('<h3>Where converting sessions started</h3>')
        html.append(bar_chart([{"p": k, "n": v} for k, v in p["entry_pages"]],
                              "n", "p", " sessions"))
    html.append('</section>')
    return "".join(html)


# --- provenance ------------------------------------------------------------

PROVENANCE = [
    ("Order of pages within a session", "measured",
     "event_timestamp is microsecond precision. Two events one second apart are "
     "reliably in the right order."),
    ("Dwell per page", "measured, partially",
     "dwell_seconds from page_exit is accumulated VISIBLE time, so a tab left open "
     "in the background does not inflate it. Where no page_exit arrived, the figure "
     "is inferred from the gap to the next page view and is marked as such in every "
     "table. The coverage percentage is in the At a glance panel."),
    ("Scroll depth per page", "measured",
     "max_scroll from page_exit, falling back to the highest scroll_depth milestone. "
     "One caveat, in Content performance: a page shorter than the viewport reports "
     "100% without anyone scrolling."),
    ("Landing page", "measured", "The first page_view of the session."),
    ("Exit page", "inferred by definition",
     "The last page_view of the session. That is a definition, not an observation: "
     "GA4 ends a session after 30 idle minutes, so a visitor who resumes after lunch "
     "produces a second session and one extra 'exit' that nobody actually made."),
    ("Total session duration", "measured",
     "Last event timestamp minus first. Time after the final event is invisible "
     "unless a page_exit closed it out."),
    ("The page Aiden was opened on, and how many pages preceded it", "measured",
     "aiden_open carries page_path, and the page views before it are counted from "
     "the same session."),
    ("What the visitor asked Aiden", "measured where joined",
     "From the Aiden_Chat sheet, joined exactly on GA4 client_id + session_id — the "
     "same two values the export calls user_pseudo_id and the ga_session_id param. "
     "Rows without those ids cannot be joined and are reported as a count, not "
     "guessed at."),
    ("Exit rate per page", "measured", "Exits divided by views of that page."),
    ("'Read fully' vs 'bounced'", "measured behaviour, chosen thresholds",
     "The dwell and scroll are measurements; where the lines fall between them is a "
     "judgement, set by --read-scroll / --read-seconds / --bounce-seconds and stated "
     "on the section. Exits with no measured dwell are excluded rather than "
     "assigned, so the bounce count is a floor."),
    ("'Precedes an Aiden open' / 'precedes a lead'", "measured ordering, not causation",
     "The article was viewed and the later event happened in the same session. "
     "Nothing here establishes that the article caused it."),
    ("Session language and device", "inferred",
     "Taken from the session's first event. A session cannot honestly have two."),
    ("Conversion events", "measured",
     "generate_lead, begin_checkout, add_payment_info and purchase are fired by the "
     "pages themselves. purchase fires on the order page after the gateway confirms, "
     "so it is a real payment, not an intent."),
]

CANNOT = [
    ("One person across two devices",
     "user_pseudo_id is per browser. The same buyer researching on a phone and "
     "purchasing on a laptop is two visitors here, and their journey is cut in half. "
     "Only a login could fix it, and the site has none."),
    ("A journey that spans a break",
     "GA4 closes a session after 30 minutes idle. Read an article at 9am, come back "
     "at noon and buy, and the report shows a stranger arriving directly at checkout. "
     "This is the single biggest distortion in section 5."),
    ("Everyone who blocked the tag",
     "No gtag, no events, no row — they are not undercounted, they are absent. Every "
     "denominator in this report is 'sessions we could see', and there is no way to "
     "measure the size of what we could not."),
    ("Total time on a page",
     "page_exit fires ONCE, on the first transition to hidden (apl-analytics.js says "
     "so explicitly, and deliberately does not re-arm). Time after a visitor comes "
     "back to the tab is not counted anywhere. Dwell means 'attention before it first "
     "left', which is the more useful number but is not the same number."),
    ("A close so fast the beacon died",
     "If the browser tears the page down before sendBeacon flushes, no page_exit "
     "arrives at all. Those exits land in the unclassified pile. The fastest bounces "
     "are therefore the ones most likely to be missing from the bounce count."),
    ("Whether a short page was actually read",
     "A page shorter than the viewport reports max_scroll = 100 the moment it paints. "
     "In the export that is identical to a full read."),
    ("What they searched for",
     "Google strips the query from the referrer. page_referrer gives the last hop and "
     "nothing else. Search Console is the only place that answer exists, and it does "
     "not join to a session."),
    ("Whether Aiden's answer was any good",
     "Nothing measures satisfaction. A long conversation is as easily frustration as "
     "engagement, and the report cannot tell you which."),
    ("What happened in WhatsApp",
     "A cta_click to wa.me is the last thing measurable. The click that became a "
     "paying customer and the click that was ignored are the same row. This is the "
     "biggest measurement gap on this site, because WhatsApp is where the business "
     "actually closes."),
    ("Why anyone did anything",
     "Every label in this report classifies behaviour. None of them is a reason. "
     "'Read fully then left' does not say whether they were satisfied or looking for "
     "something that was not there."),
    ("Anything before the export was linked",
     "The GA4 BigQuery export is not retroactive. Its first day is the day the link "
     "was created; nothing earlier will ever be queryable here, whatever GA4's own "
     "reports show."),
]


# Events this report needs that only apl-analytics.js sends. If none of them
# arrive, the cause is almost never the query - it is that the file is not on
# the server. Verified 404 on 2026-08-25.
ANALYTICS_JS_EVENTS = ("page_exit", "scroll_depth", "cta_click", "outbound_click")


def coverage(rows, sessions):
    """What actually arrived, so an empty section can be told from a missing tag."""
    names = Counter(r.get("event_name") or "?" for r in rows)
    typed = sum(1 for s in sessions for st in s.steps if not st.type_derived)
    steps = sum(len(s.steps) for s in sessions) or 1
    return {
        "names": names.most_common(),
        "missing": [e for e in ANALYTICS_JS_EVENTS if not names.get(e)],
        "page_type_param_pct": pct(typed, steps),
    }


def render_coverage(cov, sample=False):
    """A standing answer to 'why is this section empty?'."""
    html = ['<section class="card sec" id="coverage"><header>'
            '<h2>What arrived</h2><p class="sub">Every event in the pull, counted. '
            'Read this first when a section looks emptier than it should.</p></header>']
    if cov["missing"] and not sample:
        html.append(
            '<div class="note warn"><b>%s never arrived in this window.</b> '
            'Those events come from <code>/js/apl-analytics.js</code>, and as of '
            '2026-08-25 that file returns <b>404 on the live site</b> — it is part of '
            'an un-deployed rollout, so no page loads it and nothing fires it. Until it '
            'ships: <b>dwell is inferred on every page</b> (never measured), '
            '<b>scroll depth does not exist at all</b>, the read-fully / bounced split in '
            'section 3 cannot be computed, and the CTA half of "onward" in section 4 is '
            'blind. Sections 2 and 5 are unaffected — Aiden and the conversion events are '
            'fired by the widget and the page builders, and those are live.</div>'
            % ", ".join("<code>%s</code>" % esc(e) for e in cov["missing"]))
    if cov["page_type_param_pct"] is not None and cov["page_type_param_pct"] < 99:
        html.append(
            '<div class="note"><b>page_type arrived on only %s%% of page views.</b> '
            'It is one of the four event-scoped custom dimensions set by the same '
            'un-deployed file. For the rest, the report classifies the page '
            '<b>from its URL</b> using a port of that file\'s own rules — so section 4 '
            'still finds the articles, but the page type is <span class="badge i">'
            'inferred</span>, not reported by the browser.</div>'
            % num(cov["page_type_param_pct"], ""))
    html.append('<table><thead><tr><th>Event</th><th class="n">Rows</th></tr></thead><tbody>')
    for name, n in cov["names"]:
        html.append('<tr><td><code>%s</code></td><td class="n">%d</td></tr>' % (esc(name), n))
    html.append('</tbody></table></section>')
    return "".join(html)


def render_provenance():
    html = ['<section class="card sec" id="cannot"><header>'
            '<h2>Provenance &mdash; what is measured, what is inferred</h2>'
            '<p class="sub">Read this before quoting a number at anyone.</p></header>'
            '<div class="scroller"><table><thead><tr><th>Figure</th><th>Status</th>'
            '<th>How it is arrived at</th></tr></thead><tbody>']
    for label, status, why in PROVENANCE:
        cls = "m" if status.startswith("measured") else "i"
        html.append('<tr><td><b>%s</b></td><td><span class="badge %s">%s</span></td>'
                    '<td class="sub">%s</td></tr>' % (esc(label), cls, esc(status), esc(why)))
    html.append('</tbody></table></div>')
    html.append('<h3>What the data genuinely cannot answer</h3>'
                '<div class="note warn">These are not gaps to be filled by a better query. '
                'They are limits of what the site can observe.</div><ul class="tight">')
    for label, why in CANNOT:
        html.append('<li><b>%s.</b> %s</li>' % (esc(label), esc(why)))
    html.append('</ul></section>')
    return "".join(html)


def render_html(analysis, meta, aiden_diag, opts, cov):
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    head = [
        '<!doctype html><html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>Visitor journeys — aiprofitlab.io</title>',
        '<style>%s</style></head><body><div id="tip"></div><div class="wrap">' % CSS,
    ]
    html = list(head)
    html.append('<h1>Visitor journeys — aiprofitlab.io</h1>')
    html.append(
        '<p class="sub">%s &nbsp;·&nbsp; window <b>%s → %s</b> &nbsp;·&nbsp; '
        'generated %s &nbsp;·&nbsp; data pulled %s &nbsp;·&nbsp; %s rows</p>'
        % (esc(meta.get("source_label", "GA4 BigQuery export")),
           esc(meta.get("start", "?")), esc(meta.get("end", "?")), esc(generated),
           esc(meta.get("fetched_at", "—")), esc(meta.get("row_count", "?"))))
    if meta.get("sample"):
        html.append(
            '<div class="note warn"><b>SYNTHETIC DATA.</b> This was built with '
            '<code>--sample</code>, which invents sessions so the report can be reviewed '
            'before the BigQuery export exists. Every number on this page is made up. '
            'Do not act on any of it.</div>')

    html.append(render_coverage(cov, sample=bool(meta.get("sample"))))
    html.append('<div class="tabs" role="tablist">')
    for i, (key, label, _) in enumerate(SEGMENTS):
        n = analysis[key]["overview"]["sessions"]
        html.append('<button role="tab" data-seg="%s" aria-selected="%s">%s '
                    '<span class="tiny">%d</span></button>'
                    % (key, "true" if i == 0 else "false", esc(label), n))
    html.append('</div>')

    for i, (key, _label, _) in enumerate(SEGMENTS):
        seg = analysis[key]
        html.append('<div class="seg" data-seg="%s"%s>' % (key, "" if i == 0 else " hidden"))
        html.append(render_overview(seg, key))
        html.append(render_journeys(seg, key))
        html.append(render_aiden(seg, key, aiden_diag))
        html.append(render_dropoff(seg, key))
        html.append(render_content(seg, key))
        html.append(render_paths(seg, key))
        html.append('</div>')

    html.append(render_provenance())
    html.append('<p class="tiny">Built by <code>tools/build_journey_report.py</code>. '
                'This file contains visitor identifiers and, where the Aiden CSV was '
                'supplied, things visitors typed — it is gitignored, and this repository '
                'is public. Keep it that way.</p>')
    html.append('</div><script>%s</script></body></html>' % TIP_JS)
    return "".join(html)


# ===========================================================================
# Sample data
#
# --sample exists because the export does not, yet. It invents plausible
# sessions so the report's shape, thresholds and layout can be reviewed and
# argued with today rather than after the first BigQuery bill. It is loudly
# labelled in the output and shares no code path with the real query.
# ===========================================================================

SAMPLE_PAGES = [
    ("/", "home", "en"), ("/en/services", "services", "en"),
    ("/en/process", "process", "en"), ("/en/contact", "contact", "en"),
    ("/en/checkout?plan=storefront", "offer", "en"),
    ("/blog/en/2026-04-19-b2b-ai-automation-cost-roi", "article", "en"),
    ("/blog/en/2026-04-19-stop-losing-leads-whatsapp-ai", "article", "en"),
    ("/blog/en/2026-04-06-ai-admin-automation", "article", "en"),
    ("/ar/", "home", "ar"), ("/services", "services", "ar"), ("/contact", "contact", "ar"),
    ("/blog/ar/2026-04-19-b2b-ai-automation-cost-roi", "article", "ar"),
    ("/blog/ar/2026-04-06-gcc-ai-search-trends", "article", "ar"),
]


def sample_rows(n_sessions=140, seed=7):
    rng = random.Random(seed)
    rows = []
    base = int((datetime.now(timezone.utc) - timedelta(days=14)).timestamp() * 1e6)

    def emit(user, sid, ts, name, page, extra=None):
        path, ptype, lang = page
        row = {
            "event_date": datetime.fromtimestamp(ts / 1e6, timezone.utc).strftime("%Y%m%d"),
            "event_timestamp": str(ts), "event_name": name, "user_pseudo_id": user,
            "ga_session_id": sid, "page_location": "https://%s%s" % (SITE_HOST, path),
            "page_path": path.split("?")[0], "page_type": ptype,
            "content_language": lang,
            "article_slug": path.rsplit("/", 1)[-1] if ptype == "article" else "",
            "page_title": path.strip("/").replace("-", " ")[:60],
            "device_category": None, "country": "Oman",
        }
        row.update(extra or {})
        rows.append(row)

    for i in range(n_sessions):
        user = "u%04d" % rng.randint(1, int(n_sessions * 0.8))
        sid = str(1700000000 + i)
        device = rng.choices(["mobile", "desktop", "tablet"], [0.68, 0.29, 0.03])[0]
        lang = rng.choices(["ar", "en"], [0.6, 0.4])[0]
        pool = [p for p in SAMPLE_PAGES if p[2] == lang]
        depth = rng.choices([1, 2, 3, 4, 5], [0.52, 0.2, 0.13, 0.09, 0.06])[0]
        ts = base + rng.randint(0, 14 * 86400) * 1000000
        journey = [rng.choice(pool)]
        for _ in range(depth - 1):
            journey.append(rng.choice(pool))
        src = rng.choices([("google", "organic"), ("(direct)", "(none)"),
                           ("instagram", "social")], [0.55, 0.3, 0.15])[0]
        common = {"device_category": device, "source": src[0], "medium": src[1]}

        opened_aiden = False
        for j, page in enumerate(journey):
            emit(user, sid, ts, "page_view", page, common)
            # Bimodal on purpose. Real page dwell is not one lognormal hump:
            # a large share leave in seconds and a smaller share genuinely read,
            # and a sample that produced only the first half would render a
            # drop-off chart in which "read fully" never appears - hiding the
            # one distinction section 3 exists to draw.
            if page[1] == "article" and rng.random() < 0.38:
                dwell = int(rng.triangular(45, 420, 130))          # a real read
                scroll = min(100, int(rng.triangular(70, 100, 92)))
            else:
                dwell = max(1, int(rng.lognormvariate(2.2, 1.2)))
                scroll = min(100, int(rng.triangular(8, 100, 38)))
            for m in (25, 50, 75, 100):
                if scroll >= m:
                    emit(user, sid, ts + m * 1000, "scroll_depth", page,
                         dict(common, percent_scrolled=str(m)))
            if rng.random() < 0.82:      # page_exit does not always arrive
                emit(user, sid, ts + dwell * 1000000, "page_exit", page,
                     dict(common, dwell_seconds=str(dwell), max_scroll=str(scroll),
                          exit_intent="true" if rng.random() < 0.15 else "false"))
            if page[1] == "article" and rng.random() < 0.12:
                emit(user, sid, ts + dwell * 500000, "cta_click", page,
                     dict(common, cta_type="whatsapp", cta_location="fab"))
            if not opened_aiden and j >= 1 and rng.random() < 0.14:
                opened_aiden = True
                emit(user, sid, ts + dwell * 400000, "aiden_open", page,
                     dict(common, aiden_returning="false"))
                for k in range(rng.randint(1, 3)):
                    emit(user, sid, ts + dwell * 400000 + (k + 1) * 20000000,
                         "aiden_message", page, dict(common, message_count=str(k + 1)))
            ts += (dwell + rng.randint(1, 6)) * 1000000
        if rng.random() < 0.06:
            last = journey[-1]
            emit(user, sid, ts, "generate_lead", last,
                 dict(common, lead_method=rng.choice(["simulator_roi", "checkout_offline",
                                                      "silent_buyer_test"])))
            if rng.random() < 0.4:
                emit(user, sid, ts + 30000000, "begin_checkout", last,
                     dict(common, currency="OMR"))
                if rng.random() < 0.5:
                    emit(user, sid, ts + 90000000, "purchase", last,
                         dict(common, currency="OMR", event_value="800",
                              transaction_id="INV-%04d" % i))
    rows.sort(key=lambda r: (r["user_pseudo_id"], int(r["event_timestamp"])))
    return rows


# ===========================================================================
# CLI
# ===========================================================================

def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Visitor journey report for aiprofitlab.io, from the GA4 "
                    "BigQuery export.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Every run prints the bytes-scanned estimate before spending "
               "anything. --render-only and --sample never query at all.")
    p.add_argument("--days", type=int, default=28,
                   help="days back from today, inclusive (default 28)")
    p.add_argument("--start", help="window start, YYYY-MM-DD (overrides --days)")
    p.add_argument("--end", help="window end, YYYY-MM-DD (default: yesterday)")
    p.add_argument("--dataset", help="GA4 export dataset; discovered if omitted")
    p.add_argument("--project", default=PROJECT, help="GCP project (default %s)" % PROJECT)
    p.add_argument("--intraday", action="store_true",
                   help="include events_intraday_* (today, partial and subject to change)")
    p.add_argument("--aiden-csv", help="Aiden_Chat sheet exported as CSV, for transcripts")
    p.add_argument("--out", help="output HTML path (default out/journey-<start>-<end>.html)")
    p.add_argument("--max-rows", type=int, default=500000, help="LIMIT on the pull")
    p.add_argument("--refresh", action="store_true", help="re-query even if cached")
    p.add_argument("--render-only", action="store_true",
                   help="render from cache; never query, never bill")
    p.add_argument("--print-sql", action="store_true", help="print the SQL and exit")
    p.add_argument("--estimate-only", action="store_true",
                   help="print the bytes-scanned estimate and exit")
    p.add_argument("--sample", action="store_true",
                   help="render with synthetic data - no BigQuery, loudly labelled")
    p.add_argument("--yes", "-y", action="store_true", help="do not ask before querying")
    p.add_argument("--bounce-seconds", type=int, default=BOUNCE_SECONDS,
                   help="dwell at or below this is a bounce (default %d)" % BOUNCE_SECONDS)
    p.add_argument("--read-scroll", type=int, default=READ_SCROLL,
                   help="scroll%%%% needed to count as read (default %d)" % READ_SCROLL)
    p.add_argument("--read-seconds", type=int, default=READ_SECONDS,
                   help="dwell needed to count as read (default %d)" % READ_SECONDS)
    p.add_argument("--complete-scroll", type=int, default=COMPLETE_SCROLL,
                   help="scroll%%%% counted as completing an article (default %d)"
                        % COMPLETE_SCROLL)
    return p.parse_args(argv)


def window(opts):
    """(start, end) as YYYYMMDD.

    Ends yesterday by default: today's table is events_intraday_*, which is
    partial and rewritten, so including it silently by default would make two
    runs on the same day disagree for no reason the reader could see.
    """
    fmt = "%Y%m%d"
    if opts.end:
        end = datetime.strptime(opts.end, "%Y-%m-%d")
    else:
        end = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)
    if opts.start:
        start = datetime.strptime(opts.start, "%Y-%m-%d")
    else:
        start = end - timedelta(days=max(0, opts.days - 1))
    return start.strftime(fmt), end.strftime(fmt)


def main(argv=None):
    global PROJECT
    opts = parse_args(argv)
    PROJECT = opts.project
    start, end = window(opts)
    print("AI Profit Lab — visitor journey report")
    print("  window:   %s → %s (%d days)"
          % (start, end, (datetime.strptime(end, "%Y%m%d")
                          - datetime.strptime(start, "%Y%m%d")).days + 1))

    transcripts, aiden_diag = load_aiden_csv(opts.aiden_csv)
    if opts.aiden_csv:
        print("  aiden:    %d rows, %d joinable (%s)"
              % (aiden_diag["rows"], aiden_diag["joinable"], opts.aiden_csv))

    if opts.sample:
        rows = sample_rows()
        meta = {"fetched_at": "n/a (synthetic)", "row_count": len(rows), "sample": True,
                "source_label": "SYNTHETIC SAMPLE — not real data",
                "start": start, "end": end}
        print("  source:   synthetic sample (%d events, no BigQuery)" % len(rows))
    else:
        print("  project:  %s" % PROJECT)
        # --print-sql is a review aid and must not depend on the export
        # existing yet: show the shape of the query against a placeholder
        # rather than refusing to answer a question that costs nothing.
        try:
            dataset = resolve_dataset(opts.dataset)
        except BQError:
            # --print-sql and --render-only both promise to cost nothing, so
            # neither may be blocked by the export not existing yet: one is
            # only showing the query's shape, the other only reads the cache.
            if not (opts.print_sql or opts.render_only):
                raise
            dataset = "analytics_PROPERTYID"
            print("  dataset:  none found - %s"
                  % ("printing SQL against a placeholder" if opts.print_sql
                     else "falling back to the most recent cached pull"))
        sql = build_sql(dataset, start, end, intraday=opts.intraday,
                        max_rows=opts.max_rows)
        if opts.print_sql:
            print("\n" + sql)
            return 0
        if opts.estimate_only:
            est = dry_run_bytes(sql)
            tib = est / float(1024 ** 4)
            print("  estimate: %s (%.6f TiB, ~$%.4f beyond the free 1 TiB/month)"
                  % (human_bytes(est), tib, tib * 6.25))
            return 0
        rows, meta = fetch_events(sql, refresh=opts.refresh, assume_yes=opts.yes,
                                  render_only=opts.render_only)
        meta = dict(meta, start=start, end=end,
                    source_label="GA4 export · %s.%s" % (PROJECT, dataset))

    sessions = build_sessions(rows)
    print("  sessions: %d reconstructed from %d events" % (len(sessions), len(rows)))
    if not sessions:
        print("  ! no sessions in this window. If the export was linked recently, "
              "remember it is not retroactive - try a narrower, more recent window.")

    analysis = analyse(sessions, transcripts, opts)
    cov = coverage(rows, sessions)
    if cov["missing"] and not opts.sample:
        print("  ! missing: %s - /js/apl-analytics.js is not deployed, so dwell is "
              "inferred everywhere and scroll depth does not exist"
              % ", ".join(cov["missing"]))
    html = render_html(analysis, meta, aiden_diag, opts, cov)

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = opts.out or os.path.join(
        OUT_DIR, "journey-%s%s-%s.html" % ("sample-" if opts.sample else "", start, end))
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(html)
    print("  wrote:    %s (%.0f KB)" % (os.path.relpath(out_path, ROOT),
                                        os.path.getsize(out_path) / 1024))
    for key, label, _ in SEGMENTS:
        o = analysis[key]["overview"]
        print("    %-9s %4d sessions · %4d views · %3d converting · %3d opened Aiden"
              % (label + ":", o["sessions"], o["pageviews"], o["converting"], o["with_aiden"]))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BQError as exc:
        print("\n" + str(exc), file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
