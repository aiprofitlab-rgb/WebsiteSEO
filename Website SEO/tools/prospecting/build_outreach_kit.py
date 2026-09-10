#!/usr/bin/env python3
"""Turn broken-site-leads.csv into a ban-safe, outreach-ready working kit.

Input is the POST-RECHECK file (2,083 rows). Do not feed it the 2,398-row
copy in Core4/ColdOutreach -- those extra 312 rows are the macOS resolver
false-positives documented in the prospecting notes; their sites are fine.

Outputs (out/outreach/):
  outreach-master.csv   every usable lead, cleaned, scored, channel-assigned
  call-sheet.csv        phone leads, route-grouped, batched at --per-day
  ig-dm-list.csv        leads whose Google listing points at Instagram
  email-targets.csv     leads with a live site to harvest an address from
  SUMMARY.txt           counts, and the daily plan

Usage:
  python3 tools/prospecting/build_outreach_kit.py \
      --in out/prospecting/broken-site-leads.csv --per-day 40
"""
import argparse
import csv
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict

# --- junk filters -----------------------------------------------------------
# Documented residue in the CSV that was never cleaned automatically.
CHAIN_TOKENS = (
    "anantara", "radisson", "dentons", "dhl", "samsung", "precision tune",
    "kempinski", "sheraton", "crowne plaza", "holiday inn", "intercontinental",
    "hilton", "marriott", "movenpick", "shangri", "grand hyatt", "kfc",
    "mcdonald", "starbucks", "pizza hut", "burger king", "domino", "subway",
    "hertz", "avis", "budget rent", "europcar", "thrifty", "sixt",
)
GOV_HOSTS = (".gov.om", "moh.gov.om", "omanschoolfinder.com")

# --- segmentation -----------------------------------------------------------
# Route groups: what can be walked in one trip from Muscat.
ROUTES = {
    "Muscat, Oman": "R1 Muscat metro",
    "Al Khuwair, Muscat, Oman": "R1 Muscat metro",
    "Al Khuwair": "R1 Muscat metro",
    "Ruwi, Muscat, Oman": "R1 Muscat metro",
    "Ruwi": "R1 Muscat metro",
    "Muscat": "R1 Muscat metro",
    "Seeb, Oman": "R1 Muscat metro",
    "Seeb": "R1 Muscat metro",
    "Barka, Oman": "R2 Batinah day-trip",
    "Barka": "R2 Batinah day-trip",
    "Sohar, Oman": "R2 Batinah day-trip",
    "Sohar": "R2 Batinah day-trip",
    "Nizwa, Oman": "R3 Interior day-trip",
    "Nizwa": "R3 Interior day-trip",
    "Sur, Oman": "R4 Sharqiyah day-trip",
    "Sur": "R4 Sharqiyah day-trip",
    "Salalah, Oman": "R5 Dhofar - remote, phone/IG only",
    "Salalah": "R5 Dhofar - remote, phone/IG only",
}

# Can this category comfortably sign an OMR 800 build?
BUDGET_TIER = {
    "Dental clinic": "A high-ticket",
    "Medical clinic": "A high-ticket",
    "Law firm": "A high-ticket",
    "Private school": "A high-ticket",
    "Real estate": "A high-ticket",
    "Contractor": "B mid",
    "Trading company": "B mid",
    "Travel & tourism": "B mid",
    "Car rental": "B mid",
    "Gym": "C volume",
    "Salon": "C volume",
    "Restaurant": "C volume",
}

# The one line that opens the call. Specific defect, their words, no pitch.
ANGLE = {
    "NO_WEBSITE": "You're on Google Maps with no website link - anyone who "
                  "searches you has nothing to click.",
    "SOCIAL_ONLY": "Your Google listing points to Instagram. Instagram doesn't "
                   "show up in Google search and can't take bookings.",
    "DEAD": "The website link on your Google listing is broken - the domain "
            "doesn't load at all.",
    "STALE": "Your site is still up but hasn't been touched in a long time.",
    "NO_SSL": "Browsers show a 'Not secure' warning on your site - customers "
              "back out when they see it.",
    "NOT_MOBILE": "Your site doesn't fit a phone screen, and most of your "
                  "customers are on phones.",
    "PLACEHOLDER": "Your domain shows a parking page instead of a website.",
}

SCORE_RANK = {"Hot": 0, "Warm": 1, "Cold": 2}
TIER_RANK = {"A high-ticket": 0, "B mid": 1, "C volume": 2, "": 3}


def norm_phone(raw):
    """Return (e164, kind). Omani mobiles are 8 digits starting 7 or 9."""
    digits = re.sub(r"\D", "", raw or "")
    if digits.startswith("00968"):
        digits = digits[5:]
    elif digits.startswith("968") and len(digits) > 8:
        digits = digits[3:]
    if len(digits) != 8:
        return "", "none"
    if digits[0] in "79":
        return "+968" + digits, "mobile"
    if digits[0] == "2":
        return "+968" + digits, "landline"
    return "", "none"


def ig_handle(url):
    m = re.search(r"instagram\.com/([A-Za-z0-9._]+)", url or "", re.I)
    if not m:
        return ""
    h = m.group(1).strip("/.")
    return "" if h.lower() in ("p", "reel", "explore", "accounts") else "@" + h


def is_junk(row):
    name = (row.get("business") or "").strip()
    stripped = re.sub(r"^\((.*?)\)\s*", "", name).strip()
    # Names that are punctuation or a single character carry no pitchable identity.
    letters = [c for c in stripped if unicodedata.category(c).startswith("L")]
    if len(letters) < 2:
        return "no usable business name"
    low = stripped.lower()
    if any(tok in low for tok in CHAIN_TOKENS):
        return "chain / not an SME prospect"
    site = (row.get("website") or "").lower()
    if any(h in site for h in GOV_HOSTS):
        return "government listing"
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src",
                    default="out/prospecting/broken-site-leads.csv")
    ap.add_argument("--outdir", default="out/outreach")
    ap.add_argument("--per-day", type=int, default=40,
                    help="calls per working day; also the batch size")
    args = ap.parse_args()

    if not os.path.exists(args.src):
        sys.exit(f"input not found: {args.src}")
    rows = list(csv.DictReader(open(args.src, encoding="utf-8")))
    os.makedirs(args.outdir, exist_ok=True)

    dropped = Counter()
    seen_phone, seen_key = {}, set()
    leads = []

    for r in rows:
        reason = is_junk(r)
        if reason:
            dropped[reason] += 1
            continue

        name = re.sub(r"^\((.*?)\)\s*", "", (r["business"] or "").strip())
        key = (name.lower(), r["area"])
        if key in seen_key:
            dropped["duplicate listing"] += 1
            continue
        seen_key.add(key)

        e164, kind = norm_phone(r["phone"])
        # One owner can list several branches; call the best row only once.
        if e164:
            if e164 in seen_phone:
                dropped["same phone as another listing"] += 1
                continue
            seen_phone[e164] = name

        handle = ig_handle(r["website"])
        bucket = r["defect_bucket"]

        if kind in ("mobile", "landline"):
            channel = "CALL"
        elif handle:
            channel = "IG_DM"
        elif r["website"].strip():
            channel = "EMAIL_HARVEST"
        else:
            channel = "NO_ROUTE"
            dropped["no phone, no IG, no site"] += 1
            continue

        tier = BUDGET_TIER.get(r["category"], "")
        leads.append({
            "priority": "",
            "score": r["score"],
            "budget_tier": tier,
            "business": name,
            "category": r["category"],
            "area": r["area"],
            "route": ROUTES.get(r["area"], "R9 unrouted"),
            "channel": channel,
            "phone_e164": e164,
            "phone_kind": kind,
            "ig_handle": handle,
            "website": r["website"],
            "defect": bucket,
            "opening_line": ANGLE.get(bucket, r["evidence"]),
            "maps_url": r["maps_url"],
            # worked by hand from here on
            "batch_day": "",
            "status": "",
            "contacted_on": "",
            "consent_to_whatsapp": "",
            "outcome": "",
            "notes": "",
        })

    # Rank: hottest defect, then who can afford it, then mobile (a mobile
    # number is what turns a call into a permitted WhatsApp thread).
    leads.sort(key=lambda d: (
        SCORE_RANK.get(d["score"], 9),
        TIER_RANK.get(d["budget_tier"], 3),
        0 if d["phone_kind"] == "mobile" else 1,
        d["route"],
        d["business"].lower(),
    ))
    for i, d in enumerate(leads, 1):
        d["priority"] = i

    cols = list(leads[0].keys())
    with open(os.path.join(args.outdir, "outreach-master.csv"), "w",
              newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(leads)

    # --- call sheet: grouped by route so a day of dialling matches a day of
    # driving if a call turns into a visit.
    calls = [d for d in leads if d["channel"] == "CALL"]
    by_route = defaultdict(list)
    for d in calls:
        by_route[d["route"]].append(d)
    ordered, day = [], 1
    for route in sorted(by_route):
        batch = by_route[route]
        for i, d in enumerate(batch):
            d = dict(d)
            d["batch_day"] = f"Day {day + i // args.per_day}"
            ordered.append(d)
        day += (len(batch) + args.per_day - 1) // args.per_day
    with open(os.path.join(args.outdir, "call-sheet.csv"), "w",
              newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(ordered)

    igs = [d for d in leads if d["ig_handle"]]
    with open(os.path.join(args.outdir, "ig-dm-list.csv"), "w",
              newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(igs)

    mails = [d for d in leads
             if d["website"].strip() and not d["ig_handle"]
             and d["defect"] in ("STALE", "NO_SSL", "NOT_MOBILE", "PLACEHOLDER")]
    with open(os.path.join(args.outdir, "email-targets.csv"), "w",
              newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(mails)

    days = (len(calls) + args.per_day - 1) // args.per_day
    lines = [
        "SMART WEBSITE OFFER - OUTREACH KIT",
        f"source: {args.src}",
        "",
        f"usable leads          {len(leads)}",
        f"  callable            {len(calls)}"
        f"   (mobile {sum(1 for d in calls if d['phone_kind']=='mobile')},"
        f" landline {sum(1 for d in calls if d['phone_kind']=='landline')})",
        f"  Instagram handle    {len(igs)}",
        f"  email harvest       {len(mails)}",
        "",
        "dropped:",
    ]
    for reason, n in dropped.most_common():
        lines.append(f"  {n:>5}  {reason}")
    lines += [
        "",
        f"at {args.per_day} calls/day the call sheet is {days} working days"
        f" ({days/5:.1f} weeks).",
        "",
        "by route:",
    ]
    for route in sorted(by_route):
        lines.append(f"  {len(by_route[route]):>5}  {route}")
    lines += ["", "by budget tier:"]
    for tier, n in Counter(d["budget_tier"] for d in leads).most_common():
        lines.append(f"  {n:>5}  {tier or 'unclassified'}")
    lines += [
        "",
        "RULE: never WhatsApp a row whose consent_to_whatsapp is blank.",
        "Fill it 'yes' only when they said yes out loud on the call.",
    ]
    txt = "\n".join(lines)
    open(os.path.join(args.outdir, "SUMMARY.txt"), "w", encoding="utf-8").write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
