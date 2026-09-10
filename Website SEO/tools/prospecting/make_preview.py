#!/usr/bin/env python3
"""Build ONE free preview page for a prospect, after a call has gone well.

On-demand by design: pages exist only for people who actually said yes, so
nothing is generated for prospects who never asked to see anything.

The page states plainly, at the top and in the footer, that it is a free
mock-up prepared by AI Profit Lab and that nothing is live. It must never read
as the business's own published site.

Usage:
  python3 tools/prospecting/make_preview.py --phone "+96899100161"
  python3 tools/prospecting/make_preview.py --name "Al Basma" --open
"""
import argparse
import csv
import html
import os
import re
import subprocess
import sys
import unicodedata

SRC = "out/outreach/outreach-scripts.csv"
FALLBACK = "out/outreach/master-leads.csv"
OUTROOT = "public_html/preview"
OFFER_URL = "https://aiprofitlab.io/en/smart-storefront/"
STATUS_API = "https://offer.aiprofitlab.io/status"
ANCHOR = 950


def _ssl_ctx():
    """This python.org build ships no CA bundle, so a plain urlopen fails
    verification against a perfectly good certificate. Resolve one the same
    way enrich_leads.py does rather than disabling verification."""
    import os
    import ssl
    for src in (os.environ.get("SSL_CERT_FILE"),
                ssl.get_default_verify_paths().cafile,
                "/etc/ssl/cert.pem"):
        if src and os.path.exists(src):
            return ssl.create_default_context(cafile=src)
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return None


def live_offer():
    """Same live ladder the call scripts quote, so a preview page and the
    phone call can never disagree about the price."""
    import json
    import urllib.request
    try:
        with urllib.request.urlopen(STATUS_API, timeout=20,
                                    context=_ssl_ctx()) as r:
            d = json.loads(r.read())
        t = d["activeTier"]
        return {"price": t["price"], "seatsLeft": t["seatsLeft"],
                "deposit": t["deposit"], "ok": True}
    except Exception:
        return {"price": None, "seatsLeft": None, "deposit": None, "ok": False}
PUBLIC_BASE = "https://aiprofitlab.io/preview"   # .io, not .com

# What each trade's page actually needs. Generic "services / about / contact"
# convinces nobody; an owner recognises their own workflow.
TRADE = {
    "Dental clinic": dict(
        tag="Dental care in {city}",
        blocks=[("Book an appointment", "Pick a time and confirm on WhatsApp — no phone queue."),
                ("Treatments & prices", "Cleaning, whitening, implants, orthodontics, with clear pricing."),
                ("Meet your dentists", "Names, qualifications and languages spoken."),
                ("Before & after", "Real cases, with consent."),
                ("Insurance accepted", "Which providers you work with.")]),
    "Medical clinic": dict(
        tag="Medical care in {city}",
        blocks=[("Book an appointment", "Choose a doctor and a time, confirmed on WhatsApp."),
                ("Departments", "Every speciality you offer, in Arabic and English."),
                ("Our doctors", "Profiles, qualifications and languages."),
                ("Opening hours", "Including which departments run on Fridays."),
                ("Insurance accepted", "Which providers you work with.")]),
    "Law firm": dict(
        tag="Legal practice in {city}",
        blocks=[("Request a consultation", "A private form that reaches you directly."),
                ("Practice areas", "Commercial, labour, family, property — what you actually take."),
                ("The advocates", "Credentials and bar admissions."),
                ("Case outcomes", "What you have achieved, within professional rules."),
                ("Fees explained", "How you charge, so callers arrive informed.")]),
    "Private school": dict(
        tag="Private school in {city}",
        blocks=[("Book a school visit", "Parents choose a slot and confirm."),
                ("Curriculum", "What you teach, at each stage."),
                ("Fees & admissions", "The question every parent asks first."),
                ("Our teachers", "Qualifications and experience."),
                ("Term calendar", "Dates, holidays and events.")]),
    "Real estate": dict(
        tag="Property in {city}",
        blocks=[("Current listings", "Photos, prices, locations — searchable."),
                ("Request a viewing", "Straight to WhatsApp with the property attached."),
                ("List your property", "A form that captures what you need to value it."),
                ("Areas we cover", "Where you actually work."),
                ("Sold recently", "Proof you close deals.")]),
    "Restaurant": dict(
        tag="Restaurant in {city}",
        blocks=[("The menu", "Photos and prices, updating without a developer."),
                ("Order or reserve", "Straight to WhatsApp or your delivery partner."),
                ("Opening hours", "Including Ramadan timings."),
                ("Find us", "Map, parking and directions."),
                ("Private events", "Catering and group bookings.")]),
    "Beauty Salon": dict(
        tag="Salon in {city}",
        blocks=[("Book a slot", "Service, stylist and time — confirmed on WhatsApp."),
                ("Services & prices", "Everything you offer, with real pricing."),
                ("Our work", "A gallery you update from your phone."),
                ("The team", "Who does what."),
                ("Offers", "Packages and seasonal promotions.")]),
    "General Contractor": dict(
        tag="Contracting in {city}",
        blocks=[("Request a quote", "A form that captures scope, size and timeline."),
                ("Completed projects", "Photographs — the only proof that matters."),
                ("What we build", "Villas, fit-outs, maintenance, civil works."),
                ("Licences & registrations", "Proof you are legitimate."),
                ("Our clients", "Who you have worked for.")]),
    "Travel Agency": dict(
        tag="Travel agency in {city}",
        blocks=[("Packages", "Destinations, dates and prices."),
                ("Request a quote", "Straight to WhatsApp with the trip attached."),
                ("Visa services", "What you handle and what it costs."),
                ("Corporate travel", "For business accounts."),
                ("Why book with us", "Licences and partnerships.")]),
}
DEFAULT_TRADE = dict(
    tag="{cat} in {city}",
    blocks=[("What we do", "Your services, clearly, in Arabic and English."),
            ("Get a quote", "A form or WhatsApp button that reaches you instantly."),
            ("Our work", "Photographs of what you have delivered."),
            ("Why us", "What makes you the right choice."),
            ("Find us", "Map, hours and contact.")])


def slugify(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return (s or "preview")[:60]


def load(phone, name):
    src = SRC if os.path.exists(SRC) else FALLBACK
    if not os.path.exists(src):
        sys.exit(f"no lead file at {SRC} or {FALLBACK}")
    want = re.sub(r"\D", "", phone or "")
    for r in csv.DictReader(open(src, encoding="utf-8")):
        if want and re.sub(r"\D", "", r.get("phone_e164", "")).endswith(want[-8:]):
            return r
        if name and name.lower() in (r.get("business") or "").lower():
            return r
    sys.exit("no matching lead found")


def build_html(r, offer):
    biz = html.escape(r["business"])
    cat = r.get("category") or "Business"
    city = html.escape(r.get("city") or "Oman")
    phone = r.get("phone_e164") or ""
    wa = re.sub(r"\D", "", phone)
    t = TRADE.get(cat, DEFAULT_TRADE)
    tag = html.escape(t["tag"].format(cat=cat, city=city))
    if offer["ok"]:
        offer_block = (
            f'<p style="border:1px solid var(--line);border-radius:10px;'
            f'padding:1rem;background:var(--soft)"><b>The launch:</b> this '
            f'build is normally OMR {ANCHOR}. During the launch it is '
            f'<b>OMR {offer["price"]}</b>, with <b>{offer["seatsLeft"]} '
            f'seats left</b> at that price — the counter is live, so you can '
            f'check it yourself. A seat is held with half, '
            f'OMR {offer["deposit"]:.3f}, and the rest when your site is '
            f'built. <a href="{OFFER_URL}">See the live counter →</a></p>')
    else:
        offer_block = (f'<p><a href="{OFFER_URL}">See the current launch '
                       f'offer and the live seat counter →</a></p>')
    blocks = "\n".join(
        f'<article class="b"><h3>{html.escape(h)}</h3><p>{html.escape(p)}</p></article>'
        for h, p in t["blocks"])
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Preview — {biz}</title>
<style>
:root{{--ink:#12181f;--mut:#5b6875;--line:#e3e8ee;--bg:#fff;--accent:#0b7a6b;--soft:#f5f8f7}}
@media(prefers-color-scheme:dark){{:root{{--ink:#eef3f8;--mut:#9fb0c0;--line:#26313d;--bg:#0e1419;--soft:#141c23}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);
font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}}
.note{{background:#12181f;color:#fff;padding:.7rem 1rem;font-size:.82rem;text-align:center}}
.note b{{color:#7fe3d2}}
.wrap{{max-width:1000px;margin:0 auto;padding:0 1.25rem}}
header{{padding:3.5rem 0 2.5rem;border-bottom:1px solid var(--line)}}
h1{{font-size:clamp(1.9rem,5vw,3rem);line-height:1.15;margin:.2rem 0 .6rem;letter-spacing:-.02em}}
.tag{{color:var(--accent);font-weight:600;text-transform:uppercase;letter-spacing:.08em;font-size:.78rem}}
.lede{{color:var(--mut);font-size:1.08rem;max-width:56ch}}
.cta{{display:flex;gap:.7rem;flex-wrap:wrap;margin-top:1.6rem}}
.btn{{display:inline-block;padding:.8rem 1.4rem;border-radius:9px;text-decoration:none;font-weight:600}}
.p{{background:var(--accent);color:#fff}}.s{{border:1px solid var(--line);color:var(--ink)}}
.grid{{display:grid;gap:1rem;grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr));padding:2.5rem 0}}
.b{{border:1px solid var(--line);border-radius:12px;padding:1.2rem;background:var(--soft)}}
.b h3{{margin:0 0 .4rem;font-size:1.02rem}}.b p{{margin:0;color:var(--mut);font-size:.93rem}}
.ai{{border:1px solid var(--line);border-radius:12px;padding:1.5rem;margin-bottom:2.5rem;background:var(--soft)}}
.bub{{background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:.7rem .9rem;margin:.5rem 0;font-size:.93rem}}
footer{{border-top:1px solid var(--line);padding:2rem 0 3rem;color:var(--mut);font-size:.88rem}}
</style></head><body>
<div class="note">This is a <b>free preview</b> prepared by AI Profit Lab for {biz}. Nothing here is live yet, and no information has been published.</div>
<div class="wrap">
<header>
  <div class="tag">{tag}</div>
  <h1>{biz}</h1>
  <p class="lede">This is what someone searching for you on Google would find — instead of a phone number and nothing to open.</p>
  <div class="cta">
    <a class="btn p" href="https://wa.me/{wa}">WhatsApp us</a>
    <a class="btn s" href="tel:{phone}">{html.escape(phone)}</a>
  </div>
</header>
<div class="grid">{blocks}</div>
<div class="ai">
  <h3 style="margin:0 0 .3rem">Your AI assistant, answering at 2am</h3>
  <p style="color:var(--mut);margin:.2rem 0 .9rem;font-size:.93rem">In Arabic and English, from your real information — and it hands the serious ones straight to your WhatsApp.</p>
  <div class="bub"><b>Customer:</b> هل عندكم موعد بكرة؟</div>
  <div class="bub"><b>{biz}:</b> نعم، عندنا مواعيد متاحة غداً. أي وقت يناسبك؟</div>
</div>
<footer>
  <p><b>Prepared for {biz} by AI Profit Lab</b> — a free preview, built from public information on your Google listing. Nothing is published and nothing is charged.</p>
  {offer_block}
  <p>AI Profit Lab · Lotus Gulf International · CR 1570092 · aiprofitlab.io</p>
</footer>
</div></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phone")
    ap.add_argument("--name")
    ap.add_argument("--outroot", default=OUTROOT)
    ap.add_argument("--open", action="store_true", help="open it in the browser")
    a = ap.parse_args()
    if not (a.phone or a.name):
        sys.exit("give --phone or --name")

    r = load(a.phone, a.name)
    slug = slugify(r["business"])
    d = os.path.join(a.outroot, slug)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "index.html")
    offer = live_offer()
    if not offer["ok"]:
        print("!! could not read the live seat ladder; the page links to the "
              "offer page instead of quoting a price. That is safe.")
    open(path, "w", encoding="utf-8").write(build_html(r, offer))

    url = f"{PUBLIC_BASE}/{slug}/"
    print(f"lead    : {r['business']}  ({r.get('category')}, {r.get('city')})")
    print(f"file    : {path}")
    print(f"url     : {url}   (after you deploy public_html/)")
    print("\n--- WhatsApp message, ready to paste ---\n")
    msg = (r.get("whatsapp_en") or "").replace("[PREVIEW LINK]", url)
    print(msg or f"Preview: {url}")
    if a.open:
        subprocess.run(["open", path], check=False)


if __name__ == "__main__":
    main()
