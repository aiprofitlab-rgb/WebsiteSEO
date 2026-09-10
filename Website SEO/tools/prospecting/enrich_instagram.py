#!/usr/bin/env python3
"""Read public Instagram profiles for the highest-value leads, carefully.

Nahid runs live IG business automation from this network and has a Meta App
Review pending, so this script is built to give up early rather than push:

  * single worker, ~1.4 requests/second, jittered;
  * a rolling health check -- N consecutive failures, any 429, or a redirect to
    the login wall aborts the whole run and writes what it already has;
  * a hard cap on how many profiles it will ever touch.

It reads only the og:description meta of a public profile page with a Googlebot
user-agent. Nothing logs in and nothing touches the Graph API.

Usage:
  python3 tools/prospecting/enrich_instagram.py --cap 500 --delay 0.7
"""
import argparse
import csv
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
import html as _html

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from enrich_leads import (resolve_ca_bundle, make_ctx, tls_selftest, fetch,
                          meta, IG_META_RX, UA_BOT, IG_BAD_PATH)

# High-ticket trades first: a follower count is worth most where the build is
# most affordable to the buyer.
TIER = {"Dental clinic": 0, "Medical clinic": 0, "Law firm": 0,
        "Private school": 0, "Real estate": 0, "Jewelry Store": 1,
        "Travel Agency": 1, "General Contractor": 1, "Trading company": 1,
        "Gym": 1, "Beauty Salon": 2, "Salon": 2, "Restaurant": 2,
        "Coffee Shop": 2, "Florist": 2}


def parse_count(s):
    """'18K' -> 18000, '2,712' -> 2712. Thresholding needs a real number."""
    s = (s or "").strip().replace(",", "")
    if not s:
        return 0
    mult = {"k": 1_000, "m": 1_000_000}.get(s[-1].lower(), 1)
    try:
        return int(float(s[:-1] if mult > 1 else s) * mult)
    except ValueError:
        return 0


def handle_of(row):
    for field in ("ig_handle", "site_ig", "website"):
        v = (row.get(field) or "")
        m = re.search(r"(?:instagram\.com/|@)([A-Za-z0-9._]+)", v, re.I)
        if m:
            h = m.group(1).strip("/.")
            if h.lower() not in IG_BAD_PATH and "." not in h and len(h) >= 3:
                return h
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", default="out/outreach/master-leads.csv")
    ap.add_argument("--out", default="out/outreach/instagram.csv")
    ap.add_argument("--cap", type=int, default=500)
    ap.add_argument("--delay", type=float, default=0.7)
    ap.add_argument("--abort-after", type=int, default=8,
                    help="consecutive failures that end the run")
    args = ap.parse_args()

    ctx = make_ctx(resolve_ca_bundle())
    if not tls_selftest(ctx):
        sys.exit("TLS verification not working; refusing to run.")

    rows = list(csv.DictReader(open(args.src, encoding="utf-8")))
    cands = []
    for r in rows:
        h = handle_of(r)
        if h:
            cands.append((TIER.get(r.get("category", ""), 3), h, r))
    cands.sort(key=lambda t: t[0])
    seen, targets = set(), []
    for tier, h, r in cands:
        if h.lower() in seen:
            continue
        seen.add(h.lower())
        targets.append((h, r))
        if len(targets) >= args.cap:
            break

    print(f"{len(cands)} leads carry a handle; {len(seen)} unique; "
          f"taking the top {len(targets)} by trade value.")
    print(f"pace: ~{1/args.delay:.1f} req/sec, aborting after "
          f"{args.abort_after} consecutive failures.\n")

    out, consecutive, aborted = [], 0, ""
    for i, (h, r) in enumerate(targets, 1):
        time.sleep(args.delay + random.uniform(0, 0.4))
        rec = dict(r)
        rec["ig_handle"] = "@" + h
        for k in ("ig_followers", "ig_following", "ig_posts", "ig_name",
                  "ig_followers_n", "ig_note"):
            rec[k] = ""
        try:
            res = fetch(f"https://www.instagram.com/{h}/", ctx, ua=UA_BOT, timeout=20)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                aborted = "HTTP 429 -- Instagram is rate-limiting this IP"
                break
            rec["ig_note"] = f"HTTP {e.code}"
            consecutive += 1
        except Exception as e:
            rec["ig_note"] = type(e).__name__
            consecutive += 1
        else:
            final = res.get("final_url", "")
            if "/accounts/login" in final:
                aborted = "redirected to the login wall -- IG stopped serving us"
                break
            desc = meta(res["html"], "og:description")
            if not desc:
                rec["ig_note"] = "no og:description (private, renamed, or gone)"
                consecutive += 1
            else:
                m = IG_META_RX.search(desc)
                if m:
                    (rec["ig_followers"], rec["ig_following"],
                     rec["ig_posts"]) = m.groups()
                    consecutive = 0
                else:
                    rec["ig_note"] = "counts not in meta"
                    consecutive += 1
                # og:description is boilerplate ("See Instagram photos and
                # videos from NAME (@handle)"). The only useful part is the
                # display name, which confirms the account really is theirs.
                dm = re.search(r"videos from\s+(.*?)\s*\(@", _html.unescape(desc))
                rec["ig_name"] = re.sub(r"\s+", " ", dm.group(1)).strip()[:80] if dm else ""
                rec["ig_followers_n"] = str(parse_count(rec["ig_followers"]))
        out.append(rec)
        if consecutive >= args.abort_after:
            aborted = f"{consecutive} failures in a row -- backing off"
            break
        if i % 25 == 0:
            got = sum(1 for r in out if r["ig_followers"])
            print(f"  {i}/{len(targets)}  followers read: {got}")

    if aborted:
        print(f"\n!! STOPPED EARLY: {aborted}")
        print("   Nothing is broken; this is the guard doing its job.")
        print("   Wait a few hours before another run.")

    if out:
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        with open(args.out, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
            w.writeheader()
            w.writerows(out)
        got = sum(1 for r in out if r["ig_followers"])
        print(f"\nwrote {len(out)} rows ({got} with follower counts) -> {args.out}")


if __name__ == "__main__":
    main()
