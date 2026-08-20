#!/usr/bin/env python3
"""
AI Profit Lab — Google Maps negative-review miner for Oman web/IT agencies.

Finds web-design, web-development and digital agencies across Oman on Google
Maps, pulls the reviews Google exposes for each, and writes out every review at
or below a star threshold together with the agency it belongs to.

Why the Places API rather than reading maps.google.com: the Maps front end is a
JS shell that returns no listing data to a plain fetch (verified — it renders as
an empty page), and bulk-extracting it breaks Google's terms of service. The
Places API serves the same reviews under a licence that permits this use.

COST. Reviews sit in the "Place Details Enterprise + Atmosphere" SKU, $40 per
1,000 calls, with a 1,000-call free allowance per calendar month. Text Search is
an Essentials SKU with a 10,000 allowance. A full sweep of Oman is roughly 20
search calls and 150-250 detail calls, so it lands inside the free tier — but
the key still needs billing enabled on the project, and the allowance resets
monthly, so a repeated sweep in one month can start costing money. Run
--dry-run first; it prints the call count without spending anything.

THE HARD CEILING OF THIS METHOD. Google returns AT MOST 5 reviews per place and
chooses them itself ("most relevant"). A 1-star review from 2023 on an agency
with 200 reviews will usually not be among the 5. So treat this output as a
sample that reliably tells you WHICH agencies are generating unhappy clients —
not as a complete register of every unhappy client. The agency-level ratings in
the companion agencies CSV are complete and are the more trustworthy signal.

Usage:
    export GOOGLE_MAPS_API_KEY='AIza...'
    python3 tools/prospecting/gmaps_review_mining.py --dry-run
    python3 tools/prospecting/gmaps_review_mining.py
    python3 tools/prospecting/gmaps_review_mining.py --max-stars 2 --out-dir out/
"""

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request

API_ROOT = "https://places.googleapis.com/v1"

# Service phrasings crossed with the population centres that actually have
# agencies. Muscat's districts are listed separately because Google treats them
# as distinct localities and each surfaces listings the others miss.
SERVICE_TERMS = [
    "web design company",
    "website development company",
    "web development agency",
    "digital marketing agency",
    "IT solutions company",
]
CITIES = [
    "Muscat, Oman",
    "Al Khuwair, Muscat, Oman",
    "Ruwi, Muscat, Oman",
    "Seeb, Oman",
    "Sohar, Oman",
    "Salalah, Oman",
    "Nizwa, Oman",
]

SEARCH_FIELDS = ",".join(
    "places." + f
    for f in (
        "id",
        "displayName",
        "formattedAddress",
        "rating",
        "userRatingCount",
        "websiteUri",
        "nationalPhoneNumber",
        "googleMapsUri",
    )
)
DETAIL_FIELDS = ",".join(
    (
        "id",
        "displayName",
        "formattedAddress",
        "rating",
        "userRatingCount",
        "websiteUri",
        "nationalPhoneNumber",
        "googleMapsUri",
        "reviews",
    )
)

# Courtesy pause between calls. The API would tolerate far faster, but there is
# no deadline here and nothing is gained by hammering it.
PAUSE_SECONDS = 0.25


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
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:400]
        print(f"  ! HTTP {e.code}: {detail}", file=sys.stderr)
        if e.code in (401, 403):
            print(
                "\n  That is almost always one of: the key is wrong, the Places "
                "API (New) is not enabled on the project, billing is not enabled, "
                "or an HTTP-referrer restriction is set on the key (a server-side "
                "script needs an IP restriction or none).",
                file=sys.stderr,
            )
            sys.exit(1)
        return None
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"  ! network error: {e}", file=sys.stderr)
        return None


def text_search(query, api_key, max_pages=2):
    """Text Search across Oman. Returns a list of place dicts."""
    found, page_token, calls = [], None, 0
    for _ in range(max_pages):
        body = {"textQuery": query, "regionCode": "OM", "pageSize": 20}
        if page_token:
            body["pageToken"] = page_token
        payload = _request(
            f"{API_ROOT}/places:searchText", api_key, SEARCH_FIELDS + ",nextPageToken", body
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


def place_details(place_id, api_key):
    """Place Details including up to 5 reviews."""
    payload = _request(f"{API_ROOT}/places/{place_id}", api_key, DETAIL_FIELDS)
    time.sleep(PAUSE_SECONDS)
    return payload


def in_oman(place):
    """Text Search leaks neighbouring countries; drop anything not in Oman."""
    return "oman" in (place.get("formattedAddress") or "").lower()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-stars", type=int, default=3,
                    help="keep reviews at or below this rating (default 3)")
    ap.add_argument("--out-dir", default="out/prospecting",
                    help="directory for the CSV output")
    ap.add_argument("--dry-run", action="store_true",
                    help="show the search plan and call estimate, spend nothing")
    ap.add_argument("--limit", type=int, default=0,
                    help="cap how many businesses get a (metered) details call")
    ap.add_argument("--yes", action="store_true",
                    help="skip the confirmation before the metered details phase")
    args = ap.parse_args()

    queries = [f"{term} in {city}" for city in CITIES for term in SERVICE_TERMS]

    if args.dry_run:
        print(f"{len(queries)} search queries planned:\n")
        for q in queries:
            print(f"  - {q}")
        print(
            f"\nEstimated calls: ~{len(queries) * 2} Text Search (Essentials, "
            f"10,000/mo free)\n"
            f"                 ~150-250 Place Details w/ reviews "
            f"(Enterprise+Atmosphere, 1,000/mo free)\n"
            f"Estimated cost inside a fresh monthly allowance: $0.00\n"
            f"Drop --dry-run to run it."
        )
        return

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        sys.exit(
            "Set GOOGLE_MAPS_API_KEY first.\n"
            "  1. console.cloud.google.com -> create/pick a project\n"
            "  2. enable 'Places API (New)' and enable billing\n"
            "  3. Credentials -> Create API key\n"
            "  4. export GOOGLE_MAPS_API_KEY='AIza...'"
        )

    # ---- discovery -------------------------------------------------------
    places, search_calls = {}, 0
    for q in queries:
        results, calls = text_search(q, api_key)
        search_calls += calls
        kept = 0
        for p in results:
            if p.get("id") and in_oman(p):
                places.setdefault(p["id"], p)
                kept += 1
        print(f"  {q}: {kept} in Oman ({len(places)} unique so far)")

    print(f"\nDiscovery done: {len(places)} unique businesses, {search_calls} search calls.")
    if not places:
        sys.exit("No businesses found — check the key and that Places API (New) is enabled.")

    # ---- reviews ---------------------------------------------------------
    # This is the phase that spends the metered SKU, and the count is only known
    # now, after discovery. Show it and get a yes before spending.
    if args.limit:
        places = dict(list(places.items())[: args.limit])
    n = len(places)
    free_left = max(0, 1000 - n)
    over = max(0, n - 1000)
    print(
        f"\nNext step calls Place Details once per business: {n} calls against the\n"
        f"Enterprise+Atmosphere SKU (1,000 free per calendar month, then $40/1,000).\n"
        f"  within a fresh allowance: {min(n, 1000)} free, {over} billable "
        f"(~${over * 0.04:.2f})\n"
        f"  NOTE: the allowance is shared with anything else on this key this month."
    )
    if not args.yes:
        if input("Proceed? [y/N] ").strip().lower() not in ("y", "yes"):
            sys.exit("Stopped. Nothing beyond the search calls was spent.")

    print(f"Pulling reviews for {n} businesses...")
    agencies, negatives = [], []
    for i, pid in enumerate(places, 1):
        d = place_details(pid, api_key)
        if not d:
            continue
        name = (d.get("displayName") or {}).get("text", "")
        rating = d.get("rating")
        count = d.get("userRatingCount", 0)
        reviews = d.get("reviews", []) or []
        low = [r for r in reviews if (r.get("rating") or 5) <= args.max_stars]

        agencies.append({
            "agency": name,
            "rating": rating if rating is not None else "",
            "review_count": count,
            "negatives_visible": len(low),
            "website": d.get("websiteUri", ""),
            "phone": d.get("nationalPhoneNumber", ""),
            "address": d.get("formattedAddress", ""),
            "maps_url": d.get("googleMapsUri", ""),
        })

        for r in low:
            author = (r.get("authorAttribution") or {})
            negatives.append({
                "agency": name,
                "agency_rating": rating if rating is not None else "",
                "agency_review_count": count,
                "stars": r.get("rating", ""),
                "when": r.get("relativePublishTimeDescription", ""),
                "published": (r.get("publishTime") or "")[:10],
                "reviewer": author.get("displayName", ""),
                "reviewer_profile": author.get("uri", ""),
                "review_text": ((r.get("originalText") or r.get("text") or {}).get("text", "")
                                .replace("\n", " ").strip()),
                "agency_maps_url": d.get("googleMapsUri", ""),
                "agency_website": d.get("websiteUri", ""),
            })

        if i % 25 == 0:
            print(f"  ...{i}/{len(places)}")

    # ---- output ----------------------------------------------------------
    os.makedirs(args.out_dir, exist_ok=True)
    agencies.sort(key=lambda a: (a["rating"] if a["rating"] != "" else 9,
                                 -int(a["review_count"] or 0)))
    negatives.sort(key=lambda r: (r["stars"] if r["stars"] != "" else 9))

    a_path = os.path.join(args.out_dir, "oman-web-agencies.csv")
    n_path = os.path.join(args.out_dir, "oman-negative-reviews.csv")

    with open(a_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(agencies[0].keys()))
        w.writeheader()
        w.writerows(agencies)

    if negatives:
        with open(n_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(negatives[0].keys()))
            w.writeheader()
            w.writerows(negatives)

    print(f"\n{len(agencies)} agencies -> {a_path}")
    print(f"{len(negatives)} reviews at <={args.max_stars} stars -> "
          f"{n_path if negatives else '(none found)'}")

    rated = [a for a in agencies if a["rating"] != ""]
    weak = [a for a in rated if float(a["rating"]) < 4.0 and int(a["review_count"] or 0) >= 5]
    if weak:
        print(f"\nWeakest agencies (rating < 4.0, >=5 reviews) — check their client "
              f"portfolios, that is where the reachable leads are:")
        for a in weak[:15]:
            print(f"  {a['rating']}* ({a['review_count']:>4} reviews)  "
                  f"{a['agency'][:45]:<45} {a['website'][:40]}")


if __name__ == "__main__":
    main()
