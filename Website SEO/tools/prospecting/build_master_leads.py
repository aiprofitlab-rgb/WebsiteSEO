#!/usr/bin/env python3
"""Merge every lead source into one deduped, Oman-verified master.

Sources (all outside the public repo, in Core4/ColdOutreach):
  mostashari-phase1-extract/google-places.csv   21,930  Places API, Jul 2026
  mostashari-phase1-extract/openstreetmap.csv      795  Overpass, ODbL
  mostashari-phase1-extract/directory-pull.csv     618  Oman Yellow Pages
  broken-site-leads 2.csv                        2,083  the POST-recheck file

Do NOT ingest the 2,398-row broken-site copies: their extra 312 rows are
macOS-resolver false-positives whose domains resolve fine.

Writes out/outreach/master-leads.csv -- one row per business, phone-deduped,
with the defect signal carried over from the broken-site sweep where known.
"""
import argparse
import csv
import os
import re
import sys
import unicodedata
from collections import Counter

CORE4 = os.path.expanduser(
    "~/Desktop/Nahid/Core4/ColdOutreach/Leads for website offer")

# Oman is +968, 8 national digits. Mobile 7/9, landline 2.
def norm_phone(raw):
    d = re.sub(r"\D", "", raw or "")
    if d.startswith("00968"):
        d = d[5:]
    elif d.startswith("968") and len(d) > 8:
        d = d[3:]
    if len(d) != 8:
        return "", "invalid"
    if d[0] in "79":
        return "+968" + d, "mobile"
    if d[0] == "2":
        return "+968" + d, "landline"
    return "", "invalid"

# The "Adam" query dragged in ADAM-named businesses worldwide.
FOREIGN = ("india", "myanmar", "burma", "pakistan", "bangladesh", "yangon",
           "kerala", "mumbai", "delhi", "chennai", "bengaluru", "hyderabad",
           "karachi", "lahore", "dhaka", "nepal", "sri lanka", "philippines",
           "egypt", "jordan", "dubai", "abu dhabi", "sharjah", "qatar", "doha",
           "kuwait", "bahrain", "saudi", "riyadh", "jeddah", "turkey", "canada",
           "edmonton", "indonesia", "malaysia", "thailand", "vietnam", "china",
           "tamil", "punjab", "gujarat", "assam", "guwahati")

CHAIN_TOKENS = (
    "anantara", "radisson", "dentons", "dhl", "samsung", "precision tune",
    "kempinski", "sheraton", "crowne plaza", "holiday inn", "intercontinental",
    "hilton", "marriott", "movenpick", "shangri", "grand hyatt", "kfc",
    "mcdonald", "starbucks", "pizza hut", "burger king", "domino", "subway",
    "hertz", "avis", "budget rent", "europcar", "thrifty", "sixt", "lulu ",
    "carrefour", "nesto", "vodafone", "ooredoo", "omantel", "bank muscat",
    "hsbc", "standard chartered", "aramex", "fedex", "western union",
)
GOV_HOSTS = (".gov.om", "omanschoolfinder.com")


def foreign(addr):
    low = (addr or "").lower()
    return next((k for k in FOREIGN if k in low), "")


def junk_reason(name, addr, website):
    stripped = re.sub(r"^\((.*?)\)\s*", "", (name or "")).strip()
    letters = [c for c in stripped if unicodedata.category(c).startswith("L")]
    if len(letters) < 2:
        return "no usable business name"
    low = stripped.lower()
    if any(t in low for t in CHAIN_TOKENS):
        return "chain / not an SME"
    if any(h in (website or "").lower() for h in GOV_HOSTS):
        return "government listing"
    k = foreign(addr)
    if k:
        return f"outside Oman ({k})"
    return ""


def clean_name(n):
    return re.sub(r"^\((.*?)\)\s*", "", (n or "").strip()).strip()


def load(path, mapping, source, rows_out, dropped, seen_phone, seen_name):
    if not os.path.exists(path):
        print(f"  !! missing, skipped: {path}", file=sys.stderr)
        return 0
    n = 0
    with open(path, encoding="utf-8", errors="replace") as fh:
        for r in csv.DictReader(fh):
            rec = {k: (r.get(v) or "").strip() for k, v in mapping.items()}
            name = clean_name(rec["business"])
            reason = junk_reason(name, rec.get("address", ""), rec.get("website", ""))
            if reason:
                dropped[reason] += 1
                continue
            e164, kind = norm_phone(rec.get("phone", ""))
            if rec.get("phone", "").strip() and kind == "invalid":
                dropped["phone not Omani-shaped"] += 1
                continue
            if e164:
                if e164 in seen_phone:
                    dropped["duplicate phone"] += 1
                    continue
                seen_phone.add(e164)
            else:
                key = (name.lower(), rec.get("city", "").lower())
                if key in seen_name:
                    dropped["duplicate name+city, no phone"] += 1
                    continue
                seen_name.add(key)
                if not rec.get("website"):
                    dropped["no phone and no website"] += 1
                    continue
            rec.update(business=name, phone_e164=e164, phone_kind=kind,
                       source=source)
            rows_out.append(rec)
            n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--core4", default=CORE4)
    ap.add_argument("--out", default="out/outreach/master-leads.csv")
    args = ap.parse_args()

    rows, dropped = [], Counter()
    seen_phone, seen_name = set(), set()
    ex = os.path.join(args.core4, "mostashari-phase1-extract")

    # Order matters: the broken-site sweep is loaded FIRST so its verified
    # defect signal wins the phone-dedupe against a bare directory row.
    print("loading broken-site sweep (has defect signal)...")
    n = load(os.path.join(args.core4, "broken-site-leads 2.csv"),
             {"business": "business", "category": "category", "city": "area",
              "phone": "phone", "website": "website", "address": "area",
              "defect": "defect_bucket", "evidence": "evidence",
              "maps_url": "maps_url", "score": "score", "email": ""},
             "gmaps-sweep", rows, dropped, seen_phone, seen_name)
    print(f"  kept {n}")

    for fn, src in (("google-places.csv", "places-jul26"),
                    ("openstreetmap.csv", "osm"),
                    ("directory-pull.csv", "yellowpages")):
        path = os.path.join(ex, fn)
        if fn == "directory-pull.csv":
            m = {"business": "Company / Business", "category": "Listed Category",
                 "city": "City", "phone": "Phone", "website": "",
                 "address": "Area", "email": "Email", "defect": "",
                 "evidence": "", "maps_url": "", "score": ""}
        else:
            m = {"business": "Name", "category": "Type", "city": "City",
                 "phone": "Phone", "website": "Website", "address": "Address",
                 "email": "Email", "defect": "", "evidence": "",
                 "maps_url": "", "score": ""}
        print(f"loading {fn}...")
        n = load(path, m, src, rows, dropped, seen_phone, seen_name)
        print(f"  kept {n}")

    # Fill the defect signal for rows the sweep never tested.
    for r in rows:
        if not r["defect"]:
            w = r["website"].lower()
            if not w:
                r["defect"] = "NO_WEBSITE"
                r["evidence"] = "no website on the listing"
            elif "instagram.com" in w or "facebook.com" in w:
                r["defect"] = "SOCIAL_ONLY"
                r["evidence"] = "listing points at social media, not a site"
            elif "linktr.ee" in w or "linktree" in w or ".my.canva.site" in w \
                    or "sites.google.com" in w or "wa.me" in w:
                r["defect"] = "LINK_PAGE"
                r["evidence"] = "listing points at a link page, not a site"
            else:
                r["defect"] = "UNTESTED"
                r["evidence"] = "site not yet checked"

    cols = ["business", "category", "city", "phone_e164", "phone_kind",
            "email", "website", "defect", "evidence", "score", "maps_url",
            "address", "source"]
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    print(f"\nMASTER: {len(rows)} leads -> {args.out}")
    print(f"  mobile   {sum(1 for r in rows if r['phone_kind']=='mobile')}")
    print(f"  landline {sum(1 for r in rows if r['phone_kind']=='landline')}")
    print(f"  no phone {sum(1 for r in rows if not r['phone_e164'])}")
    print(f"  website  {sum(1 for r in rows if r['website'])}")
    print(f"  email    {sum(1 for r in rows if r['email'])}")
    print("\n  by defect:")
    for k, v in Counter(r["defect"] for r in rows).most_common():
        print(f"    {v:>6}  {k}")
    print("\n  by source:")
    for k, v in Counter(r["source"] for r in rows).most_common():
        print(f"    {v:>6}  {k}")
    print("\n  dropped:")
    for k, v in dropped.most_common():
        print(f"    {v:>6}  {k}")


if __name__ == "__main__":
    main()
