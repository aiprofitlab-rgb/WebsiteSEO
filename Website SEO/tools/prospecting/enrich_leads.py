#!/usr/bin/env python3
"""Harvest real, quotable facts about each lead so outreach can be specific.

One fetch per site yields everything the scripts need: what they built it on,
whether it works on a phone, how old it looks, whether a customer can actually
book or message from it, and an email address if one is published.

Instagram is read the cheap way -- a plain GET with a Googlebot UA returns the
og:description meta, which carries follower/post counts without login. That is
the ONLY IG method used here; nothing logs in, nothing touches the graph API.

Environment traps this machine has bitten us with before, both guarded below:
  - this python.org build ships no CA bundle, so TLS "failures" are meaningless
    until a bundle is resolved and self-tested against a known-good host;
  - the macOS resolver returns spurious NXDOMAIN under bulk lookups, so a single
    resolution failure never condemns a domain.

Usage:
  python3 tools/prospecting/enrich_leads.py --in out/outreach/master-leads.csv \
      --out out/outreach/enriched.csv --workers 8 --limit 200
  python3 tools/prospecting/enrich_leads.py ... --instagram   # opt in to IG
"""
import argparse
import concurrent.futures as cf
import csv
import gzip
import io
import os
import re
import socket
import ssl
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import Counter

UA_BROWSER = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")
UA_BOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
CONTROL_HOST = "www.google.com"

PLATFORMS = (
    ("Wix", ("wix.com", "wixstatic", "_wixCssImports")),
    ("Squarespace", ("squarespace.com", "static1.squarespace")),
    ("Shopify", ("cdn.shopify.com", "shopify.theme")),
    ("WordPress", ("wp-content", "wp-includes", "wp-json")),
    ("Canva site", (".my.canva.site", "canva.com/design")),
    ("Google Sites", ("sites.google.com", "gstatic.com/sites")),
    ("Linktree", ("linktr.ee",)),
    ("Blogger", ("blogspot.", "blogger.com")),
    ("Webflow", ("webflow.io", "assets.website-files")),
    ("GoDaddy builder", ("godaddysites.com", "img1.wsimg.com")),
    ("Weebly", ("weebly.com", "editmysite.com")),
)
# A listing pointing here is a social profile or someone else's platform --
# never the business's own site. Quoting one of these as "your website" is the
# fastest way to sound like you never actually looked.
SOCIAL_HOSTS = ("instagram.com", "facebook.com", "m.facebook.com", "fb.com",
                "twitter.com", "x.com", "linkedin.com", "youtube.com",
                "tiktok.com", "snapchat.com", "wa.me", "api.whatsapp.com",
                "t.me", "pinterest.com")
THIRD_PARTY_HOSTS = ("linktr.ee", "linktree.com", "menuu.at", "zomato.com",
                     "talabat.com", "deliveroo.", "opentable.", "sites.google.com",
                     "my.canva.site", "google.com", "goo.gl", "bit.ly",
                     "blogspot.", "wordpress.com", "wixsite.com", "business.site")

# Anchored so nav chrome and cookie banners cannot fake a booking flow.
BOOKING_RX = re.compile(
    r"\b(book\s+(now|online|an?\s+appointment|a\s+table)|make\s+an?\s+appointment"
    r"|request\s+an?\s+appointment|schedule\s+an?\s+appointment|reserve\s+a\s+table"
    r"|احجز\s*(الآن|موعد)|حجز\s*موعد)", re.I)
PRICE_RX = re.compile(r"(\bOMR\s?\d|\bRO\.?\s?\d|ر\.ع\.?\s?\d|\d+\s?ريال)", re.I)
IG_BAD_PATH = ("p", "reel", "reels", "explore", "accounts", "static", "rsrc.php",
               "developer", "about", "legal", "privacy", "directory", "web")
YEAR_RX = re.compile(r"(?:©|&copy;|copyright)\s*(?:\d{4}\s*[-–]\s*)?(20\d{2})", re.I)
EMAIL_RX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
ARABIC_RX = re.compile(r"[؀-ۿ]")
IG_META_RX = re.compile(
    r"([\d,.KMkm]+)\s+Followers?,\s*([\d,.KMkm]+)\s+Following,\s*([\d,.KMkm]+)\s+Posts?")

_print_lock = threading.Lock()


def resolve_ca_bundle():
    for src in (os.environ.get("SSL_CERT_FILE"),
                ssl.get_default_verify_paths().cafile,
                "/etc/ssl/cert.pem"):
        if src and os.path.exists(src):
            return src
    try:
        import certifi
        return certifi.where()
    except ImportError:
        return None


def make_ctx(bundle):
    if not bundle:
        return None
    ctx = ssl.create_default_context(cafile=bundle)
    return ctx


def tls_selftest(ctx):
    """Refuse to report TLS verdicts until verification demonstrably works."""
    try:
        req = urllib.request.Request("https://" + CONTROL_HOST, headers={"User-Agent": UA_BROWSER})
        urllib.request.urlopen(req, timeout=15, context=ctx).read(64)
        return True
    except Exception as exc:
        print(f"TLS self-test FAILED against {CONTROL_HOST}: {exc}", file=sys.stderr)
        return False


def resolver_ok():
    try:
        socket.getaddrinfo(CONTROL_HOST, 443)
        return True
    except OSError:
        return False


def fetch(url, ctx, ua=UA_BROWSER, timeout=20, maxbytes=400_000):
    req = urllib.request.Request(url, headers={
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en,ar;q=0.8",
        "Accept-Encoding": "gzip",
    })
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        raw = resp.read(maxbytes)
        if resp.headers.get("Content-Encoding") == "gzip":
            try:
                raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
            except OSError:
                pass
        return {
            "status": resp.status,
            "final_url": resp.geturl(),
            "ms": int((time.time() - t0) * 1000),
            "bytes": len(raw),
            "html": raw.decode("utf-8", errors="replace"),
        }


def meta(html, prop):
    m = re.search(
        r'<meta[^>]+(?:property|name)=["\']%s["\'][^>]+content=["\']([^"\']*)' % prop,
        html, re.I)
    if m:
        return m.group(1)
    m = re.search(
        r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+(?:property|name)=["\']%s["\']' % prop,
        html, re.I)
    return m.group(1) if m else ""


def host_of(url):
    return re.sub(r"^https?://", "", url or "").split("/")[0].lower()


def name_matches_domain(name, url):
    """Cheap sanity check: does the domain plausibly belong to this business?

    Guards against quoting a shared platform (a QR-menu host, a marketplace)
    back to an owner as though it were their own site.
    """
    host = host_of(url)
    base = re.sub(r"^www\.", "", host).split(".")[0]
    if not base:
        return False
    words = [w for w in re.findall(r"[A-Za-z]{3,}", name or "") if w.lower() not in
             ("the", "and", "llc", "for", "company", "trading", "oman", "muscat",
              "center", "centre", "store", "shop", "group", "services", "est")]
    if not words:
        return True          # Arabic-only name: cannot judge, do not accuse
    b = base.replace("-", "")
    return any(w.lower()[:5] in b or b[:5] in w.lower() for w in words)


def enrich_site(url, ctx):
    out = {k: "" for k in (
        "site_status", "site_final_url", "site_ms", "site_kb", "site_title",
        "site_desc", "site_platform", "site_mobile", "site_https",
        "site_year", "site_lang", "site_has_whatsapp", "site_has_tel",
        "site_has_booking", "site_has_price", "site_email", "site_ig",
        "site_fb", "site_note", "site_is_theirs")}
    if not url:
        return out
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    host = host_of(url)
    if any(h in host for h in SOCIAL_HOSTS):
        out["site_status"] = "SOCIAL_PROFILE"
        out["site_note"] = "listing points at a social profile, not a website"
        return out
    if any(h in host for h in THIRD_PARTY_HOSTS):
        out["site_status"] = "THIRD_PARTY"
        out["site_note"] = f"hosted on someone else's platform ({host})"
        return out

    # Never condemn a domain on one resolver hiccup.
    resolved = False
    for attempt in range(3):
        try:
            socket.getaddrinfo(host, None)
            resolved = True
            break
        except OSError:
            if not resolver_ok():
                out["site_note"] = "resolver unhealthy, retry later"
                return out
            time.sleep(0.6 * (attempt + 1))
    if not resolved:
        out["site_status"] = "DNS_FAIL"
        out["site_note"] = "domain does not resolve after 3 tries"
        return out

    https_url = "https://" + url.split("://", 1)[1]
    r, err = None, ""
    for candidate in (https_url, url):
        try:
            r = fetch(candidate, ctx)
            out["site_https"] = "yes" if candidate.startswith("https") else "no"
            break
        except urllib.error.HTTPError as e:
            out["site_status"] = str(e.code)
            err = f"HTTP {e.code}"
        except ssl.SSLCertVerificationError as e:
            err = f"bad certificate: {e.verify_message}"
            out["site_https"] = "invalid-cert"
        except Exception as e:
            err = type(e).__name__
    if r is None:
        out["site_status"] = out["site_status"] or "UNREACHABLE"
        out["site_note"] = err
        return out

    html = r["html"]
    low = html.lower()
    out["site_status"] = str(r["status"])
    out["site_final_url"] = r["final_url"]
    out["site_ms"] = r["ms"]
    out["site_kb"] = round(r["bytes"] / 1024)
    t = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    out["site_title"] = re.sub(r"\s+", " ", t.group(1)).strip()[:160] if t else ""
    out["site_desc"] = meta(html, "description")[:200]
    out["site_mobile"] = "yes" if re.search(
        r'<meta[^>]+name=["\']viewport["\']', html, re.I) else "no"
    lang = re.search(r'<html[^>]+lang=["\']([^"\']+)', html, re.I)
    out["site_lang"] = lang.group(1) if lang else ""
    if ARABIC_RX.search(html):
        out["site_lang"] = (out["site_lang"] + "+ar").strip("+")
    for label, needles in PLATFORMS:
        if any(n.lower() in low for n in needles):
            out["site_platform"] = label
            break
    else:
        out["site_platform"] = "custom/unknown"
    years = YEAR_RX.findall(html)
    if years:
        out["site_year"] = max(years)
    out["site_has_whatsapp"] = "yes" if ("wa.me" in low or "api.whatsapp" in low) else "no"
    out["site_has_tel"] = "yes" if "tel:" in low else "no"
    out["site_has_booking"] = "yes" if BOOKING_RX.search(html) else "no"
    out["site_has_price"] = "yes" if PRICE_RX.search(html) else "no"
    emails = [e for e in EMAIL_RX.findall(html)
              if not e.lower().endswith((".png", ".jpg", ".gif", ".webp", ".svg"))
              and "example.com" not in e.lower() and "sentry" not in e.lower()]
    out["site_email"] = emails[0] if emails else ""
    # If the final domain is unrelated to the name, no script may cite it.
    out["site_is_theirs"] = "yes" if name_matches_domain(
        out.get("_business", ""), r["final_url"]) else "unsure"
    for cand in re.findall(r"instagram\.com/([A-Za-z0-9._]+)", html, re.I):
        c = cand.strip("/.")
        if c.lower() in IG_BAD_PATH or "." in c or len(c) < 3:
            continue
        out["site_ig"] = "@" + c
        break
    fb = re.search(r"facebook\.com/([A-Za-z0-9._-]+)", html, re.I)
    if fb and fb.group(1).lower() not in ("sharer", "tr", "plugins", "dialog"):
        out["site_fb"] = fb.group(1).strip("/.")
    return out


def enrich_ig(handle, ctx):
    out = {k: "" for k in ("ig_followers", "ig_following", "ig_posts",
                           "ig_bio", "ig_note")}
    if not handle:
        return out
    h = handle.lstrip("@")
    try:
        r = fetch(f"https://www.instagram.com/{h}/", ctx, ua=UA_BOT, timeout=20)
    except Exception as e:
        out["ig_note"] = f"unreachable: {type(e).__name__}"
        return out
    desc = meta(r["html"], "og:description")
    if not desc:
        out["ig_note"] = "no og:description (private, gone, or IG blocked us)"
        return out
    m = IG_META_RX.search(desc)
    if m:
        out["ig_followers"], out["ig_following"], out["ig_posts"] = m.groups()
    tail = desc.split(" - ", 1)[-1] if " - " in desc else ""
    out["ig_bio"] = re.sub(r"\s+", " ", tail).strip()[:200]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", default="out/outreach/master-leads.csv")
    ap.add_argument("--out", default="out/outreach/enriched.csv")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0, help="0 = all")
    ap.add_argument("--instagram", action="store_true",
                    help="also read public IG profiles (see IP-rate-limit note)")
    ap.add_argument("--delay", type=float, default=0.25,
                    help="per-worker politeness delay in seconds")
    args = ap.parse_args()

    bundle = resolve_ca_bundle()
    ctx = make_ctx(bundle)
    print(f"CA bundle: {bundle or 'NONE FOUND'}")
    if not tls_selftest(ctx):
        sys.exit("Refusing to run: TLS verification is not working on this "
                 "machine, so every https verdict would be noise. Fix with "
                 "'/Applications/Python 3.11/Install Certificates.command' "
                 "or pip install certifi.")
    print("TLS self-test OK")
    if not resolver_ok():
        sys.exit("Refusing to run: DNS resolver is not answering.")

    rows = list(csv.DictReader(open(args.src, encoding="utf-8")))
    targets = [r for r in rows if r["website"].strip()]
    if args.limit:
        targets = targets[:args.limit]
    print(f"{len(targets)} leads with a website to check "
          f"({'with' if args.instagram else 'without'} Instagram)\n")

    done = Counter()
    results = []

    def work(row):
        time.sleep(args.delay)
        site = enrich_site(row["website"], ctx)
        if site.get("site_final_url"):
            site["site_is_theirs"] = "yes" if name_matches_domain(
                row["business"], site["site_final_url"]) else "unsure"
        ig = {k: "" for k in ("ig_followers", "ig_following", "ig_posts",
                              "ig_bio", "ig_note")}
        handle = ""
        w = row["website"].lower()
        m = re.search(r"instagram\.com/([A-Za-z0-9._]+)", w)
        if m and m.group(1).lower() not in IG_BAD_PATH:
            handle = m.group(1)
        elif site.get("site_ig"):
            handle = site["site_ig"].lstrip("@")
        if args.instagram and handle:
            time.sleep(args.delay)
            ig = enrich_ig(handle, ctx)
        out = dict(row)
        out.update(site)
        out.update(ig)
        out["ig_handle"] = "@" + handle if handle else ""
        with _print_lock:
            done[site.get("site_status", "?")] += 1
            n = sum(done.values())
            if n % 25 == 0:
                print(f"  {n}/{len(targets)}  {dict(done.most_common(5))}")
        return out

    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for res in pool.map(work, targets):
            results.append(res)

    cols = list(results[0].keys())
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(results)
    print(f"\nwrote {len(results)} -> {args.out}")
    print("status:", dict(done.most_common()))
    print("platforms:", dict(Counter(r["site_platform"] for r in results).most_common(8)))
    print("not mobile:", sum(1 for r in results if r["site_mobile"] == "no"))
    print("emails found:", sum(1 for r in results if r["site_email"]))


if __name__ == "__main__":
    main()
