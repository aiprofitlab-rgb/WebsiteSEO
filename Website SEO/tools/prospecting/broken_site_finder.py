#!/usr/bin/env python3
"""
AI Profit Lab — finds Omani SMEs whose website is absent, dead or visibly broken.

The premise, and why this beats mining negative reviews: a bad review is
anonymous, uncontactable, and about something that happened years ago. A broken
website is the opposite. The business is on Google Maps with its phone number
in plain sight, the defect is provable in one screenshot, and the fix is the
OMR 800 "Website with built-in AI" product. Nothing here is speculative — every
row is a business that today either has no site or has one that fails.

COST DESIGN — read before changing the field mask.
Google's Text Search returns up to 20 businesses per billed call, and the
FieldMask decides both what comes back AND which SKU the call bills at. Asking
for websiteUri + nationalPhoneNumber in the SEARCH mask promotes the call to
Text Search Enterprise ($40/1,000, 1,000 calls free per calendar month) but
gets the website for all 20 businesses in that one call. The naive shape —
Text Search, then one Place Details per business — would cost hundreds of
metered Details calls for the same data. So: one Enterprise search call per
20 businesses, roughly 20,000 businesses inside the free allowance. Do not add
a Place Details loop to this script.

Each nextPageToken page is a SEPARATE billed call, so --max-pages is the cost
dial. A full sweep at the default of 2 pages is ~216 calls, about a fifth of
the monthly free allowance. --max-pages 1 halves that.

This Enterprise allowance is a different pool from the Essentials Text Search
and Place Details allowances used by gmaps_review_mining.py, so the two scripts
do not eat each other's free tier.

The health-check phase is free of Google charges but it touches prospects'
servers. One HEAD and one small GET per site, a courtesy pause between, an
honest User-Agent, and never more than the homepage.

Usage:
    python3 tools/prospecting/broken_site_finder.py --dry-run
    python3 tools/prospecting/broken_site_finder.py
    python3 tools/prospecting/broken_site_finder.py --max-pages 1 --limit 200
"""

import argparse
import csv
import datetime
import json
import os
import re
import socket
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API_ROOT = "https://places.googleapis.com/v1"
KEY_FILE = os.path.expanduser("~/.config/aiprofitlab/gmaps.key")

# Identify ourselves honestly. A webmaster reading their logs should be able to
# tell who probed them and why.
USER_AGENT = "AIProfitLab-SiteCheck/1.0 (+https://aiprofitlab.io; site availability check)"

# SME categories that live or die on having a working website — a customer who
# cannot find the menu, the price list or the booking form goes to a competitor.
CATEGORIES = {
    "Restaurant":       "restaurant",
    "Medical clinic":   "medical clinic",
    "Dental clinic":    "dental clinic",
    "Gym":              "gym fitness center",
    "Salon":            "beauty salon",
    "Law firm":         "law firm",
    "Real estate":      "real estate agency",
    "Car rental":       "car rental company",
    "Travel & tourism": "travel agency tour operator",
    "Contractor":       "contracting company",
    "Private school":   "private school",
    "Trading company":  "trading company",
}

# Muscat's districts are listed separately because Google treats them as
# distinct localities and each surfaces listings the others miss.
AREAS = [
    "Muscat, Oman",
    "Al Khuwair, Muscat, Oman",
    "Ruwi, Muscat, Oman",
    "Seeb, Oman",
    "Sohar, Oman",
    "Salalah, Oman",
    "Nizwa, Oman",
    "Sur, Oman",
    "Barka, Oman",
]

# websiteUri and nationalPhoneNumber are the Enterprise-tier fields that make
# this whole approach work. See the COST DESIGN note above before editing.
SEARCH_FIELDS = ",".join(
    "places." + f
    for f in (
        "id",
        "displayName",
        "formattedAddress",
        "websiteUri",
        "nationalPhoneNumber",
        "googleMapsUri",
    )
)

PAUSE_SECONDS = 0.25          # between Google API calls
MAX_READ = 80_000             # bytes of HTML we read per site — enough for <head> + footer

# A "website" that is really just a social profile. The business has no asset it
# owns, no booking, no menu, no search presence.
SOCIAL_HOSTS = (
    "facebook.com", "fb.com", "fb.me", "instagram.com", "linkedin.com",
    "twitter.com", "x.com", "tiktok.com", "youtube.com", "snapchat.com",
    "wa.me", "api.whatsapp.com", "linktr.ee", "t.me",
    # Google's free "business.site" builder was shut down in 2024; these are dead
    # storefronts that now bounce back to the Maps listing.
    "business.site", "sites.google.com",
)

PARKING_HOSTS = (
    "sedoparking.com", "parkingcrew.net", "above.com", "hugedomains.com",
    "afternic.com", "dan.com", "bodis.com", "undeveloped.com", "sedo.com",
)

PLACEHOLDER_TEXT = (
    "coming soon", "under construction", "site is under construction",
    "this domain is for sale", "buy this domain", "domain is parked",
    "parked domain", "domain for sale", "future home of",
    "welcome to nginx", "apache2 ubuntu default page", "apache2 debian default page",
    "default web page", "it works!", "iis windows server", "index of /",
    "your new website is ready", "web hosting default page",
)

COPYRIGHT_RE = re.compile(
    r"(?:©|&copy;|&#169;|copyright)[^0-9]{0,20}((?:19|20)\d{2})"
    r"(?:\s*[-–—/]\s*((?:19|20)\d{2}))?",
    re.I,
)
VIEWPORT_RE = re.compile(r"""<meta[^>]+name\s*=\s*['"]?viewport""", re.I)
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)

# Worst-first. A site can fail several ways; this decides which one names the row.
BUCKET_ORDER = ["NO_WEBSITE", "DEAD", "SOCIAL_ONLY", "NO_SSL", "PLACEHOLDER",
                "NOT_MOBILE", "STALE", "OK"]


# --------------------------------------------------------------------------
# Google Places
# --------------------------------------------------------------------------

def _request(url, api_key, field_mask, body=None):
    """One Places API call. Returns parsed JSON, or None on a handled error."""
    headers = {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": field_mask,
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30,
                                    context=SSL_CONTEXT) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:400]
        print(f"  ! HTTP {e.code}: {detail}", file=sys.stderr)
        if e.code in (401, 403):
            print(
                "\n  That is almost always one of: the key is wrong, Places API "
                "(New) is not enabled on the project, billing is not enabled, or "
                "the key has an HTTP-referrer restriction (a server-side script "
                "needs an IP restriction or none).",
                file=sys.stderr,
            )
            sys.exit(1)
        return None
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"  ! network error: {e}", file=sys.stderr)
        return None


def text_search(query, api_key, max_pages):
    """Text Search across Oman. Returns (places, billed_call_count)."""
    found, page_token, calls = [], None, 0
    for _ in range(max_pages):
        body = {"textQuery": query, "regionCode": "OM", "pageSize": 20}
        if page_token:
            body["pageToken"] = page_token
        payload = _request(
            f"{API_ROOT}/places:searchText", api_key,
            SEARCH_FIELDS + ",nextPageToken", body,
        )
        calls += 1
        time.sleep(PAUSE_SECONDS)
        if not payload:
            break
        found.extend(payload.get("places", []))
        page_token = payload.get("nextPageToken")
        if not page_token:
            break
    return found, calls


# Requiring the word "Oman" in the address does NOT work here. Google returns
# short-form addresses for these categories — "Bousher, Muscat", "H9VC+GGG,
# Muscat", "مسقط 133" — and a require-Oman filter throws away ~19 of every 20
# genuine results. So invert it: regionCode=OM plus a city-named query already
# pins us to Oman, and we only need to drop the occasional cross-border leak.
NON_OMAN_ASCII = (
    "united arab emirates", "dubai", "abu dhabi", "sharjah", "ajman",
    "fujairah", "ras al khaimah", "umm al quwain", "uae",
    "saudi arabia", "riyadh", "jeddah", "dammam", "makkah", "mecca",
    "medina", "khobar", "qatar", "doha", "kuwait", "bahrain", "manama",
    "yemen", "sanaa", "india", "pakistan", "iran", "egypt", "jordan",
    "lebanon", "turkey", "united kingdom", "london",
)
NON_OMAN_ARABIC = (
    "الإمارات", "دبي", "أبوظبي", "الشارقة", "السعودية", "الرياض", "جدة",
    "قطر", "الدوحة", "الكويت", "البحرين", "المنامة", "اليمن",
)
_NON_OMAN_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(t) for t in NON_OMAN_ASCII) + r")\b", re.I
)


def in_oman(place):
    """Drop the occasional cross-border leak; keep everything else."""
    addr = place.get("formattedAddress") or ""
    if _NON_OMAN_RE.search(addr):
        return False
    return not any(t in addr for t in NON_OMAN_ARABIC)


# --------------------------------------------------------------------------
# Site health check
# --------------------------------------------------------------------------

# This machine's Python may ship without a CA bundle (the python.org macOS build
# is the usual culprit). If that happens every https site verifies as "invalid
# certificate", NO_SSL false-positives across the board, and every other defect
# is masked behind it — a silently worthless lead list. So resolve a bundle
# explicitly and prove it works before trusting a single TLS verdict.
def _ca_bundle():
    for path in (os.environ.get("SSL_CERT_FILE"),
                 ssl.get_default_verify_paths().openssl_cafile):
        if path and os.path.exists(path):
            return path
    try:
        import certifi
        return certifi.where()
    except ImportError:
        pass
    for path in ("/etc/ssl/cert.pem", "/usr/local/etc/openssl/cert.pem",
                 "/opt/homebrew/etc/ca-certificates/cert.pem"):
        if os.path.exists(path):
            return path
    return None


def _make_ssl_context():
    ctx = ssl.create_default_context()
    if not ctx.get_ca_certs():
        bundle = _ca_bundle()
        if bundle:
            ctx.load_verify_locations(cafile=bundle)
    return ctx


SSL_CONTEXT = _make_ssl_context()


def tls_self_test():
    """Verify our TLS trust store works before we judge anyone else's cert."""
    try:
        req = urllib.request.Request("https://www.google.com",
                                     method="HEAD",
                                     headers={"User-Agent": USER_AGENT})
        urllib.request.urlopen(req, timeout=15, context=SSL_CONTEXT)
        return True, _ca_bundle() or "system default"
    except Exception as e:                                  # noqa: BLE001
        return False, str(getattr(e, "reason", e))


class Fetch:
    """Result of one HTTP attempt: either a status+body, or a classified failure."""

    def __init__(self, status=None, final_url=None, body="", bucket=None,
                 evidence=None, kind=None):
        self.status = status
        self.final_url = final_url
        self.body = body
        self.bucket = bucket        # set only on failure
        self.evidence = evidence
        self.kind = kind            # dns | refused | reset | timeout | tls | other


def _classify(exc):
    """Map a network exception onto a defect bucket."""
    reason = getattr(exc, "reason", exc)
    if isinstance(reason, ssl.SSLCertVerificationError):
        msg = getattr(reason, "verify_message", None) or str(reason)
        return "NO_SSL", f"invalid certificate: {msg}", "tls"
    if isinstance(reason, ssl.SSLError):
        return "NO_SSL", f"TLS handshake failed: {reason}", "tls"
    if isinstance(reason, socket.gaierror):
        return "DEAD", "DNS does not resolve", "dns"
    if isinstance(reason, ConnectionRefusedError):
        return "DEAD", "connection refused", "refused"
    if isinstance(reason, ConnectionResetError):
        return "DEAD", "connection reset by server", "reset"
    if isinstance(reason, (TimeoutError, socket.timeout)):
        return "DEAD", "no response (timeout)", "timeout"
    return "DEAD", f"unreachable: {reason}", "other"


def _fetch(url, timeout, method="GET"):
    req = urllib.request.Request(
        url, method=method,
        headers={"User-Agent": USER_AGENT, "Accept": "*/*",
                 "Accept-Language": "en,ar"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout,
                                    context=SSL_CONTEXT) as r:
            body = ""
            if method == "GET":
                body = r.read(MAX_READ).decode("utf-8", errors="replace")
            return Fetch(status=r.status, final_url=r.geturl(), body=body)
    except urllib.error.HTTPError as e:
        # A 4xx/5xx is a real answer from a real server, not a transport failure.
        return Fetch(status=e.code, final_url=e.geturl())
    except Exception as e:                                  # noqa: BLE001
        bucket, evidence, kind = _classify(e)
        return Fetch(bucket=bucket, evidence=evidence, kind=kind)


def _host_of(url):
    try:
        return (urllib.parse.urlsplit(url).hostname or "").lower()
    except ValueError:
        return ""


def is_social(url):
    host = _host_of(url)
    return any(host == h or host.endswith("." + h) for h in SOCIAL_HOSTS)


def inspect_html(html, final_url):
    """Content-level defects. Returns a list of (bucket, evidence)."""
    defects = []
    low = html.lower()

    host = _host_of(final_url)
    parked = next((h for h in PARKING_HOSTS
                   if host == h or host.endswith("." + h)), None)
    if parked:
        defects.append(("PLACEHOLDER", f"redirects to parking host {parked}"))
    else:
        hit = next((p for p in PLACEHOLDER_TEXT if p in low), None)
        if hit:
            title = TITLE_RE.search(html)
            title = re.sub(r"\s+", " ", title.group(1)).strip()[:60] if title else ""
            ev = f'placeholder page: "{hit}"'
            if title:
                ev += f' (title: "{title}")'
            defects.append(("PLACEHOLDER", ev))

    if not VIEWPORT_RE.search(html):
        defects.append(("NOT_MOBILE", "no viewport meta tag — will not scale on a phone"))

    years = []
    for m in COPYRIGHT_RE.finditer(html):
        years += [int(g) for g in m.groups() if g]
    if years:
        newest = max(years)
        cutoff = datetime.date.today().year - 2
        if newest <= cutoff:
            defects.append(("STALE", f"copyright reads {newest}"))

    return defects


_DNS_CACHE = {}


def resolve(host, attempts=3):
    """Resolve a hostname, retrying before declaring it dead.

    A single getaddrinfo failure is NOT proof a domain is gone. A sweep of this
    size issues thousands of lookups, and a busy or rate-limited resolver starts
    returning spurious NXDOMAIN — which would silently fill the lead list with
    live businesses wrongly marked DEAD. (This is not hypothetical: the first
    full run flagged 526 domains as dead and 28 of 30 sampled resolved fine
    minutes later, including moh.gov.om.)

    So on failure we retry with backoff, and we ask a known-good control domain
    whether the resolver itself is the thing that is broken. If the control also
    fails, we back off hard rather than blame the prospect.
    """
    if host in _DNS_CACHE:
        return _DNS_CACHE[host]

    result = (False, "")
    for i in range(attempts):
        try:
            socket.getaddrinfo(host, None)
            result = (True, "")
            break
        except socket.gaierror:
            if i == attempts - 1:
                result = (False, "")
                break
            time.sleep(1.0 * (i + 1))
            try:
                socket.getaddrinfo("cloudflare.com", None)
            except socket.gaierror:
                # Our resolver is the problem, not theirs. Wait it out.
                time.sleep(15)
        except Exception as e:                              # noqa: BLE001
            result = (False, f" [lookup error: {e}]")
            break

    _DNS_CACHE[host] = result
    return result


def check_site(raw_url, timeout, pause):
    """Health-check one site. Returns (list_of_defects, final_url)."""
    url = (raw_url or "").strip()
    if not re.match(r"^https?://", url, re.I):
        url = "http://" + url

    parts = urllib.parse.urlsplit(url)
    host = parts.hostname
    if not host:
        return [("DEAD", f"unusable URL on the listing: {raw_url}")], url

    # DNS first — cheapest possible answer, and the commonest failure by far.
    ok, why = resolve(host)
    if not ok:
        return [("DEAD", f"DNS does not resolve ({host}){why}")], url

    pre = []
    # Listed as http://. Only a genuine defect if https is unavailable — plenty
    # of listings are stale text pointing at a site that does serve TLS.
    if parts.scheme.lower() == "http":
        https_url = urllib.parse.urlunsplit(("https",) + tuple(parts)[1:])
        probe = _fetch(https_url, timeout, "HEAD")
        time.sleep(pause)
        if probe.bucket is None and probe.status and probe.status < 400:
            url = https_url                      # judge the working https version
        else:
            why = probe.evidence or f"HTTP {probe.status}"
            pre.append(("NO_SSL", f"listed as http:// and https fails ({why})"))

    head = _fetch(url, timeout, "HEAD")
    # A hard transport failure needs no confirming GET.
    if head.bucket and head.kind in ("dns", "refused", "reset", "tls"):
        return pre + [(head.bucket, head.evidence)], url
    time.sleep(pause)

    got = _fetch(url, timeout, "GET")
    if got.bucket and got.kind == "timeout":
        # One retry — a single slow response is not proof a business is offline.
        time.sleep(pause * 2)
        got = _fetch(url, timeout, "GET")
    if got.bucket:
        ev = got.evidence
        if got.kind == "timeout":
            ev += f" after {timeout}s, twice"
        return pre + [(got.bucket, ev)], url

    if got.status and got.status >= 400:
        return pre + [("DEAD", f"HTTP {got.status}")], url

    return pre + inspect_html(got.body, got.final_url or url), (got.final_url or url)


# --------------------------------------------------------------------------

def score_for(bucket, phone):
    """Hot = provably no working site AND reachable by phone."""
    if bucket in ("NO_WEBSITE", "DEAD"):
        # Without a phone we cannot act on it today, so it drops a rung.
        return "Hot" if phone else "Warm"
    if bucket in ("SOCIAL_ONLY", "PLACEHOLDER", "NO_SSL"):
        return "Warm"
    return "Cold"


def load_api_key():
    key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if key:
        return key.strip()
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, encoding="utf-8") as f:
            key = f.read().strip()
        if key:
            return key
    sys.exit(
        "No API key found.\n"
        "  1. console.cloud.google.com -> create/pick a project\n"
        "  2. enable 'Places API (New)' and enable billing\n"
        "  3. Credentials -> Create API key, restrict it to Places API (New)\n"
        f"  4. export GOOGLE_MAPS_API_KEY='AIza...'   (or write it to {KEY_FILE})"
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", default="out/prospecting",
                    help="directory for the CSV output")
    ap.add_argument("--dry-run", action="store_true",
                    help="show the search plan and call estimate, spend nothing")
    ap.add_argument("--max-pages", type=int, default=2,
                    help="result pages per query; each page is a billed call (default 2)")
    ap.add_argument("--limit", type=int, default=0,
                    help="cap how many websites get health-checked")
    ap.add_argument("--timeout", type=int, default=8,
                    help="per-request timeout in seconds (default 8)")
    ap.add_argument("--pause", type=float, default=0.5,
                    help="courtesy pause between requests to a prospect (default 0.5s)")
    ap.add_argument("--recheck", metavar="CSV",
                    help="re-verify the DEAD/NO_SSL rows of an existing CSV "
                         "in place; costs no API calls")
    ap.add_argument("--yes", action="store_true",
                    help="skip both confirmation prompts")
    args = ap.parse_args()

    if args.recheck:
        recheck_mode(args.recheck, args.timeout, args.pause)
        return

    queries = [(label, f"{term} in {area}", area)
               for area in AREAS for label, term in CATEGORIES.items()]
    max_calls = len(queries) * args.max_pages

    if args.dry_run:
        print(f"{len(queries)} search queries planned "
              f"({len(CATEGORIES)} categories x {len(AREAS)} areas):\n")
        for _, q, _ in queries:
            print(f"  - {q}")
        print(
            f"\nMetered phase: up to {max_calls} Text Search calls at "
            f"--max-pages {args.max_pages}\n"
            f"  SKU: Text Search Enterprise (websiteUri + nationalPhoneNumber in the\n"
            f"       field mask), 1,000 calls free per calendar month, then $40/1,000.\n"
            f"  Inside a fresh allowance: $0.00. That is {max_calls / 10:.0f}% of the month.\n"
            f"  Returns up to {max_calls * 20} business records for those calls.\n"
            f"\nFree phase: HEAD + GET per business that has a website, "
            f"{args.pause}s apart.\n"
            f"Drop --dry-run to run it."
        )
        return

    ok, detail = tls_self_test()
    if not ok:
        sys.exit(
            f"TLS self-test failed before spending anything: {detail}\n"
            "This Python cannot verify ANY certificate, so every https site would\n"
            "be mis-bucketed as NO_SSL and the lead list would be worthless.\n"
            "Fix with one of:\n"
            "  /Applications/Python\\ 3.11/Install\\ Certificates.command\n"
            "  python3 -m pip install --upgrade certifi\n"
            "  export SSL_CERT_FILE=/etc/ssl/cert.pem"
        )
    print(f"TLS trust store OK ({detail}).")

    api_key = load_api_key()

    print(f"Metered phase: up to {max_calls} Text Search Enterprise calls "
          f"({len(queries)} queries x {args.max_pages} pages).")
    print(f"  1,000 free per calendar month, then $40/1,000. This run uses up to "
          f"{max_calls / 10:.0f}% of the allowance.")
    if not args.yes:
        if input("Proceed? [y/N] ").strip().lower() not in ("y", "yes"):
            sys.exit("Stopped. Nothing spent.")

    # ---- discovery -------------------------------------------------------
    places, search_calls = {}, 0
    for i, (label, q, area) in enumerate(queries, 1):
        results, calls = text_search(q, api_key, args.max_pages)
        search_calls += calls
        kept = 0
        for p in results:
            pid = p.get("id")
            if not pid or not in_oman(p):
                continue
            if pid not in places:
                p["_category"], p["_area"] = label, area.split(",")[0]
                places[pid] = p
                kept += 1
        print(f"  [{i}/{len(queries)}] {q}: +{kept} new ({len(places)} unique)")

    print(f"\nDiscovery done: {len(places)} unique businesses, "
          f"{search_calls} billed search calls.")
    if not places:
        sys.exit("No businesses found — check the key and that Places API (New) is enabled.")

    # ---- triage ----------------------------------------------------------
    rows, today = [], datetime.date.today().isoformat()
    no_site, to_check = [], []
    for p in places.values():
        (to_check if p.get("websiteUri") else no_site).append(p)

    for p in no_site:
        rows.append(build_row(p, "NO_WEBSITE",
                              "no website on the Google listing", "", today))

    social = [p for p in to_check if is_social(p["websiteUri"])]
    live = [p for p in to_check if not is_social(p["websiteUri"])]
    for p in social:
        rows.append(build_row(p, "SOCIAL_ONLY",
                              f"social profile only ({_host_of(p['websiteUri'])})",
                              p["websiteUri"], today))

    if args.limit:
        live = live[: args.limit]

    est = len(live) * (2 * args.pause + 1.5) / 60
    print(f"\nTriage: {len(no_site)} with no website, {len(social)} social-only, "
          f"{len(live)} to health-check.")
    print(f"  Health-checking is free of Google charges. It sends one HEAD and one "
          f"GET\n  to each prospect's own server, {args.pause}s apart. "
          f"Rough time: {est:.0f} min.")
    if live and not args.yes:
        if input("Proceed? [y/N] ").strip().lower() not in ("y", "yes"):
            print("Stopped before health-checking; writing what we have.")
            live = []

    checked_ok = 0
    for i, p in enumerate(live, 1):
        defects, final = check_site(p["websiteUri"], args.timeout, args.pause)
        if not defects:
            checked_ok += 1
        else:
            defects.sort(key=lambda d: BUCKET_ORDER.index(d[0]))
            primary, evidence = defects[0]
            if len(defects) > 1:
                evidence += "; also: " + "; ".join(e for _, e in defects[1:])
            rows.append(build_row(p, primary, evidence, p["websiteUri"], today))
        time.sleep(args.pause)
        if i % 25 == 0 or i == len(live):
            print(f"  ...checked {i}/{len(live)}")

    # ---- output ----------------------------------------------------------
    score_rank = {"Hot": 0, "Warm": 1, "Cold": 2}
    rows.sort(key=lambda r: (score_rank[r["score"]],
                             BUCKET_ORDER.index(r["defect_bucket"]),
                             r["business"].lower()))

    os.makedirs(args.out_dir, exist_ok=True)
    path = os.path.join(args.out_dir, "broken-site-leads.csv")
    fields = ["score", "business", "category", "area", "defect_bucket",
              "evidence", "website", "phone", "maps_url", "verified_date"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    # ---- summary ---------------------------------------------------------
    print(f"\n{'=' * 60}\n{len(rows)} leads -> {path}\n{'=' * 60}")
    print(f"Businesses seen:      {len(places)}")
    print(f"Health-checked:       {len(live)}")
    print(f"Passed (excluded):    {checked_ok}")
    print(f"Billed search calls:  {search_calls}\n")

    print("By bucket:")
    for b in BUCKET_ORDER[:-1]:
        n = sum(1 for r in rows if r["defect_bucket"] == b)
        print(f"  {b:<12} {n:>5}" + ("   (none)" if n == 0 else ""))
    print("\nBy score:")
    for s in ("Hot", "Warm", "Cold"):
        n = sum(1 for r in rows if r["score"] == s)
        print(f"  {s:<12} {n:>5}" + ("   (none)" if n == 0 else ""))

    timeouts = sum(1 for r in rows if "timeout" in r["evidence"])
    if timeouts:
        print(f"\nNote: {timeouts} row(s) are DEAD on a timeout rather than a hard "
              f"refusal.\nThat is the least certain signal here — open those in a "
              f"browser before calling.")


# Buckets derived from the network transport, and therefore vulnerable to a
# flaky resolver or a blip on our side rather than a real defect at theirs.
# The content buckets (PLACEHOLDER/NOT_MOBILE/STALE) came from a page we
# successfully fetched and parsed, so they need no re-verification.
RECHECKABLE = {"DEAD", "NO_SSL"}


def recheck_mode(path, timeout, pause):
    """Re-verify the transport-derived rows of an existing CSV. Costs no API calls."""
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit(f"{path} is empty.")

    todo = [r for r in rows if r["defect_bucket"] in RECHECKABLE and r["website"]]
    keep = [r for r in rows if r not in todo]
    print(f"{len(rows)} rows in {path}")
    print(f"  {len(todo)} in {sorted(RECHECKABLE)} to re-verify, "
          f"{len(keep)} passed through unchanged.")

    ok, detail = tls_self_test()
    if not ok:
        sys.exit(f"TLS self-test failed: {detail}")
    print(f"TLS trust store OK ({detail}).\n")

    today = datetime.date.today().isoformat()
    fixed, changed, cleared = [], 0, 0
    for i, r in enumerate(todo, 1):
        defects, _ = check_site(r["website"], timeout, pause)
        if not defects:
            cleared += 1                      # site is fine — drop from the list
        else:
            defects.sort(key=lambda d: BUCKET_ORDER.index(d[0]))
            primary, evidence = defects[0]
            if len(defects) > 1:
                evidence += "; also: " + "; ".join(e for _, e in defects[1:])
            if primary != r["defect_bucket"]:
                changed += 1
            r = dict(r)
            r["defect_bucket"] = primary
            r["evidence"] = evidence
            r["score"] = score_for(primary, r["phone"])
            r["verified_date"] = today
            fixed.append(r)
        time.sleep(pause)
        if i % 50 == 0 or i == len(todo):
            print(f"  ...re-checked {i}/{len(todo)}  "
                  f"(cleared {cleared}, re-bucketed {changed})")

    out = keep + fixed
    score_rank = {"Hot": 0, "Warm": 1, "Cold": 2}
    out.sort(key=lambda r: (score_rank[r["score"]],
                            BUCKET_ORDER.index(r["defect_bucket"]),
                            r["business"].lower()))
    fields = ["score", "business", "category", "area", "defect_bucket",
              "evidence", "website", "phone", "maps_url", "verified_date"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(out)

    print(f"\n{'=' * 60}")
    print(f"Re-verified. {cleared} row(s) were false positives and have been "
          f"dropped.\n{changed} row(s) moved to a different bucket.")
    print(f"{len(rows)} -> {len(out)} leads in {path}\n{'=' * 60}")
    for b in BUCKET_ORDER[:-1]:
        n = sum(1 for r in out if r["defect_bucket"] == b)
        print(f"  {b:<12} {n:>5}" + ("   (none)" if n == 0 else ""))
    print()
    for sc in ("Hot", "Warm", "Cold"):
        n = sum(1 for r in out if r["score"] == sc)
        print(f"  {sc:<12} {n:>5}" + ("   (none)" if n == 0 else ""))


def build_row(place, bucket, evidence, website, today):
    phone = place.get("nationalPhoneNumber", "")
    return {
        "score": score_for(bucket, phone),
        "business": (place.get("displayName") or {}).get("text", ""),
        "category": place.get("_category", ""),
        "area": place.get("_area", ""),
        "defect_bucket": bucket,
        "evidence": evidence,
        "website": website,
        "phone": phone,
        "maps_url": place.get("googleMapsUri", ""),
        "verified_date": today,
    }


if __name__ == "__main__":
    main()
