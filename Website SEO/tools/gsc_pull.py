#!/usr/bin/env python3
"""Pull Google Search Console data for aiprofitlab.io into .tmp/gsc/<date>/.

Read-only. Auth is the gcloud application-default login of the account that
owns the Search Console property (ai.profit.lab2026@gmail.com), made once with:

    gcloud auth application-default login --scopes=https://www.googleapis.com/auth/webmasters.readonly,https://www.googleapis.com/auth/cloud-platform

The access token stays inside this process: it is never printed or written.
Requests are counted against the GCP project below (the Search Console API is
free; the project only needs the API enabled and the account granted
roles/serviceusage.serviceUsageConsumer on it).

Usage:
    python3 tools/gsc_pull.py                 # 16 months + last 28 days
    python3 tools/gsc_pull.py --inspect 20    # also URL-inspect the top 20 pages
"""

import argparse
import datetime as dt
import json
import pathlib
import sys

import google.auth
from google.auth.transport.requests import AuthorizedSession

QUOTA_PROJECT = "adroit-minutia-496210-n1"
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
API = "https://searchconsole.googleapis.com/webmasters/v3"
INSPECT_API = "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect"
# The domain property covers www + apex + http; fall back to the URL-prefix one.
PREFERRED_SITES = ["sc-domain:aiprofitlab.io", "https://aiprofitlab.io/"]
ROW_LIMIT = 25000  # API maximum per request

ROOT = pathlib.Path(__file__).resolve().parent.parent


def session():
    creds, _ = google.auth.default(scopes=SCOPES, quota_project_id=QUOTA_PROJECT)
    return AuthorizedSession(creds)


def check(resp):
    if resp.status_code != 200:
        # Error bodies never contain the token, only Google's message.
        sys.exit(f"Search Console API error {resp.status_code}: {resp.text[:800]}")
    return resp.json()


def pick_site(s, override):
    sites = check(s.get(f"{API}/sites")).get("siteEntry", [])
    usable = {e["siteUrl"]: e["permissionLevel"] for e in sites
              if e["permissionLevel"] != "siteUnverifiedUser"}
    if override:
        if override not in usable:
            sys.exit(f"{override} not accessible. Available: {sorted(usable)}")
        return override, sites
    for site in PREFERRED_SITES:
        if site in usable:
            return site, sites
    sys.exit(f"No aiprofitlab.io property found. Available: {sorted(usable)}")


def query(s, site, start, end, dimensions, search_type="web"):
    """Page through searchAnalytics until the API returns a short page."""
    url = f"{API}/sites/{requests_quote(site)}/searchAnalytics/query"
    rows, offset = [], 0
    while True:
        body = {"startDate": str(start), "endDate": str(end),
                "dimensions": dimensions, "type": search_type,
                "rowLimit": ROW_LIMIT, "startRow": offset, "dataState": "all"}
        page = check(s.post(url, json=body)).get("rows", [])
        rows += page
        if len(page) < ROW_LIMIT:
            return rows
        offset += ROW_LIMIT


def requests_quote(site):
    from urllib.parse import quote
    return quote(site, safe="")


def inspect(s, site, urls):
    out = []
    for u in urls:
        r = s.post(INSPECT_API, json={"inspectionUrl": u, "siteUrl": site})
        out.append({"url": u, "status": r.status_code,
                    "result": r.json().get("inspectionResult") if r.ok else r.text[:300]})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", help="override the property, e.g. https://aiprofitlab.io/")
    ap.add_argument("--inspect", type=int, default=0,
                    help="URL-inspect the top N pages by impressions (quota 2000/day)")
    args = ap.parse_args()

    s = session()
    site, all_sites = pick_site(s, args.site)

    today = dt.date.today()
    end = today - dt.timedelta(days=1)            # dataState=all includes fresh data
    start_16m = end - dt.timedelta(days=16 * 30)  # API keeps ~16 months
    start_28d = end - dt.timedelta(days=27)

    outdir = ROOT / ".tmp" / "gsc" / str(today)
    outdir.mkdir(parents=True, exist_ok=True)

    pulls = {
        "daily_16m": (start_16m, ["date"]),
        "queries_16m": (start_16m, ["query"]),
        "pages_16m": (start_16m, ["page"]),
        "query_page_16m": (start_16m, ["query", "page"]),
        "country_16m": (start_16m, ["country"]),
        "device_16m": (start_16m, ["device"]),
        "appearance_16m": (start_16m, ["searchAppearance"]),
        "queries_28d": (start_28d, ["query"]),
        "pages_28d": (start_28d, ["page"]),
        "query_page_28d": (start_28d, ["query", "page"]),
    }
    summary = {"site": site, "accessible_sites": all_sites,
               "range_16m": [str(start_16m), str(end)],
               "range_28d": [str(start_28d), str(end)], "files": {}}

    for name, (start, dims) in pulls.items():
        rows = query(s, site, start, end, dims)
        (outdir / f"{name}.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
        summary["files"][name] = len(rows)
        print(f"{name:18} {len(rows):6} rows")

    sitemaps = check(s.get(f"{API}/sites/{requests_quote(site)}/sitemaps"))
    (outdir / "sitemaps.json").write_text(json.dumps(sitemaps, indent=1))
    print(f"{'sitemaps':18} {len(sitemaps.get('sitemap', [])):6} entries")

    if args.inspect:
        pages = json.loads((outdir / "pages_16m.json").read_text())
        top = [r["keys"][0] for r in sorted(pages, key=lambda r: -r["impressions"])[:args.inspect]]
        # URL inspection wants URLs inside the property; fine for both property types.
        result = inspect(s, site, top)
        (outdir / "inspection.json").write_text(json.dumps(result, ensure_ascii=False, indent=1))
        print(f"{'inspection':18} {len(result):6} urls")

    (outdir / "summary.json").write_text(json.dumps(summary, indent=1))
    print(f"\nProperty: {site}\nSaved to {outdir.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
