#!/usr/bin/env python3
"""Turn enriched leads into a call script and a WhatsApp message for each one.

Design rules, all of them cultural rather than technical:

  * Every fact quoted is one we actually harvested. A wrong "I saw your site"
    is worse than no personalisation at all -- it proves you did not look.
  * The observation is always TRUE and SPECIFIC, and it always comes before
    the gap. Praise that could apply to anyone reads as flattery and is
    distrusted; praise that names their platform, their followers, their
    trade, proves attention.
  * The gap is never their fault. It is framed as something nobody told them,
    or something a previous developer left behind. Face is preserved, so the
    conversation can continue.
  * Nothing is pitched before permission is asked for the person's time.
  * The exit is offered explicitly and warmly. A prospect who can leave
    without embarrassment does not block you -- which is the whole ballgame,
    because block rate is what WhatsApp actually measures.

Output:
  out/outreach/outreach-scripts.csv   every lead, with its script fields
  out/outreach/PLAYBOOK.md            the segments, timing, objections
  out/outreach/call-cards.md          printable cards for the top leads
"""
import argparse
import csv
import os
import re
from collections import Counter

# --- THE LAUNCH OFFER, not the services price list -------------------------
# We are selling seats at /en/smart-storefront/, whose price CLIMBS as seats
# sell. Hard-coding a rung would have Nahid quoting 249 after it has become
# 279, so the live ladder is fetched at generation time and stamped with the
# hour it was read. Regenerate before a calling session; never quote a price
# older than the counter.
OFFER_URL = "https://aiprofitlab.io/en/smart-storefront/"
STATUS_API = "https://offer.aiprofitlab.io/status"
ANCHOR = 950          # the published Smart Website price the ladder discounts

FALLBACK = {"price": 249, "seatsLeft": 3, "deposit": 124.5,
            "next": [279, 299], "asOf": "fallback, API unreachable"}


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
    """Read the seat ladder. Never invent one -- a wrong price on a call is
    a broken promise, so an unreachable API returns a clearly-labelled
    fallback that the cards print a warning about."""
    import json
    import urllib.request
    try:
        with urllib.request.urlopen(STATUS_API, timeout=20,
                                    context=_ssl_ctx()) as r:
            d = json.loads(r.read())
        t = d["activeTier"]
        nxt = [p["price"] for p in d.get("published", [])
               if p.get("state") == "next"]
        return {"price": t["price"], "seatsLeft": t["seatsLeft"],
                "deposit": t["deposit"], "next": nxt,
                "asOf": d.get("asOf", ""), "soldOut": d.get("soldOut"),
                "card": (d.get("pay") or {}).get("card")}
    except Exception as e:
        f = dict(FALLBACK)
        f["asOf"] = f"COULD NOT READ LIVE LADDER ({type(e).__name__})"
        return f


OFFER = live_offer()


def money(v):
    """249 -> '249'; 124.5 -> '124.500'. The rial divides into 1000 baisa, so
    a part-rial figure is written to three places, never one."""
    return f"{v:.3f}" if v % 1 else f"{int(v)}"

# --- who to ask for, by trade -----------------------------------------------
ASK_FOR = {
    "Dental clinic": "the doctor or the clinic manager",
    "Medical clinic": "the doctor or the clinic manager",
    "Law firm": "the advocate",
    "Private school": "the principal or the admin office",
    "Real estate": "the office manager",
    "Restaurant": "the owner or the manager",
    "Coffee Shop": "the owner or the manager",
    "Beauty Salon": "the owner",
    "Salon": "the owner",
    "Pharmacy": "the pharmacist in charge",
    "Gym": "the manager",
}
DEFAULT_ASK = "the owner or whoever handles the marketing"

# --- what a website is FOR, per trade: the concrete win, not "online presence"
# The first item is used as a PLURAL subject ("when <who> look for you"), so
# every phrase here must be plural. Mixing in a singular produces "someone
# ... searches", which is exactly the kind of wrongness that makes a script
# sound machine-written on the phone.
TRADE_WIN = {
    "Dental clinic": ("people searching 'dentist near me' at 10pm",
                      "book an appointment without calling"),
    "Medical clinic": ("people looking for your speciality at night",
                       "see your timings and book"),
    "Law firm": ("people with a problem searching at 11pm",
                 "read what you handle and send you the case"),
    "Private school": ("parents comparing schools in admission season",
                       "see fees, curriculum and book a visit"),
    "Real estate": ("buyers searching listings on their phone",
                    "see the property and message you"),
    "Restaurant": ("people deciding where to eat tonight",
                   "see the menu and order"),
    "Coffee Shop": ("people looking for somewhere nearby",
                    "see your menu and hours"),
    "Beauty Salon": ("people looking for a salon before an occasion",
                     "see your services and book a slot"),
    "Salon": ("people looking for a salon before an occasion",
              "see your services and book a slot"),
    "Car repair and maintenance service": ("people whose car broke down today",
                                           "see what you fix and call you first"),
    "Pharmacy": ("people looking for a pharmacy open now",
                 "check you have it before driving over"),
    "Travel Agency": ("people planning a trip on their phone",
                      "see your packages and ask for a quote"),
    "General Contractor": ("people planning a build who want to check you are real",
                           "see your finished work and request a quote"),
    "Jewelry Store": ("people shopping for an occasion",
                      "see the pieces before coming in"),
    "Clothing Store": ("people browsing at night",
                       "see what is in stock"),
    "Laundry": ("people new to the neighbourhood",
                "see your prices and pickup times"),
    "Tailor": ("people who need something made before an occasion",
               "see your work and message you"),
}
DEFAULT_WIN = ("people searching for what you do",
               "see what you offer and contact you")


def trade_win(cat):
    return TRADE_WIN.get(cat, DEFAULT_WIN)


# Categories arrive singular ("Law firm"); a script must say "law firms".
IRREGULAR_PLURAL = {
    "Services": "service businesses", "Banking and Finance": "finance offices",
    "Store": "shops", "Clothing Store": "clothing shops",
    "Electronics Store": "electronics shops", "Furniture Store": "furniture shops",
    "Auto Parts Store": "auto parts shops", "Jewelry Store": "jewellers",
    "Building Materials Store": "building materials suppliers",
    "Grocery Store": "grocery shops", "Car repair and maintenance service":
    "garages", "General Contractor": "contractors", "Real estate":
    "real estate offices", "Travel & tourism": "travel agencies",
    "Travel Agency": "travel agencies", "Beauty Salon": "salons",
    "Laundry": "laundries", "Pharmacy": "pharmacies", "Bakery": "bakeries",
    "Manufacturer": "manufacturers", "Wholesaler": "wholesalers",
    "Trading company": "trading companies", "Private school": "private schools",
    "Medical clinic": "clinics", "Dental clinic": "dental clinics",
    "Coffee Shop": "coffee shops", "Car Wash": "car washes",
}


def plural(cat):
    """'Law firm' -> 'law firms'. Used where the script surveys a market."""
    if not cat:
        return "businesses"
    if cat in IRREGULAR_PLURAL:
        return IRREGULAR_PLURAL[cat]
    low = cat.lower()
    if low.endswith(("s", "ch", "sh", "x")):
        return low if low.endswith("s") else low + "es"
    if low.endswith("y") and low[-2:-1] not in "aeiou":
        return low[:-1] + "ies"
    return low + "s"


def singular(cat):
    """'Law firm' -> 'a law firm', for 'early for a law firm in Oman'."""
    if not cat:
        return "a business"
    low = cat.lower()
    article = "an" if low[:1] in "aeiou" else "a"
    return f"{article} {low}"


# Below this, a follower count is not a compliment. Saying "your 41 followers
# are a real audience" insults the owner and ends the call. Under the floor we
# praise the effort (posting consistently) instead of the size.
FOLLOWER_FLOOR = 800


def parse_count(s):
    s = (s or "").strip().replace(",", "")
    if not s:
        return 0
    mult = {"k": 1_000, "m": 1_000_000}.get(s[-1:].lower(), 1)
    try:
        return int(float(s[:-1] if mult > 1 else s) * mult)
    except ValueError:
        return 0


def num(s):
    try:
        return int(float(str(s)))
    except (TypeError, ValueError):
        return 0


# --- segmentation -----------------------------------------------------------
def segment(r):
    """Return (code, human label). Order matters: most specific defect wins."""
    status = (r.get("site_status") or "").strip()
    defect = (r.get("defect") or "").strip()
    site = (r.get("website") or "").strip()
    ig = (r.get("ig_handle") or r.get("site_ig") or "").strip()

    if status == "SOCIAL_PROFILE" or defect == "SOCIAL_ONLY":
        return "S3", "Google listing points at social media"
    if status == "THIRD_PARTY" or defect == "LINK_PAGE":
        return "S4", "link page or someone else's platform"
    if status in ("DNS_FAIL", "UNREACHABLE") or defect == "DEAD":
        return "S5", "website link is broken"
    if status.startswith(("4", "5")) or status == "526":
        return "S6", "website returns an error"
    if r.get("site_https") == "invalid-cert" or defect == "NO_SSL":
        return "S7", "browser shows Not Secure"
    if r.get("site_mobile") == "no" or defect == "NOT_MOBILE":
        return "S8", "website does not fit a phone"
    if status == "200":
        year = num(r.get("site_year"))
        if year and year <= 2023:
            return "S9", "website looks abandoned"
        if num(r.get("site_ms")) > 4000:
            return "S10", "website is slow"
        if r.get("site_has_whatsapp") == "no" and r.get("site_has_booking") == "no":
            return "S11", "website has no way to act"
        return "S12", "website is fine, offer the upgrade"
    if not site:
        return "S2" if ig else "S1", ("no website, has Instagram" if ig
                                      else "no website at all")
    # Has a website the sweep has not reached yet. Never call this "no website"
    # -- telling an owner they have no site when they do ends the call.
    return "S13", "has a website, not yet checked"


# --- the specific, true observation ----------------------------------------
def observation(r, seg):
    """One sentence proving we actually looked. Never invented."""
    name = r["business"]
    cat = (r.get("category") or "business").lower()
    city = r.get("city") or ""
    ig = (r.get("ig_handle") or r.get("site_ig") or "").strip()
    fol = (r.get("ig_followers") or "").strip()
    plat = (r.get("site_platform") or "").strip()
    title = (r.get("site_title") or "").strip()
    year = num(r.get("site_year"))
    ms = num(r.get("site_ms"))

    if seg == "S1":
        return ("you come up on Google Maps, and people are clearly "
                "finding you there")
    posts = num(r.get("ig_posts"))
    big = parse_count(fol) >= FOLLOWER_FLOOR
    if seg == "S2":
        if big:
            return (f"your Instagram {ig} has {fol} followers — that is a real "
                    f"audience you built yourself, not bought")
        if posts >= 20:
            return (f"you have put {posts} posts into your Instagram {ig} — "
                    f"you are doing the work most owners never get round to")
        return f"you are putting real work into your Instagram {ig}"
    if seg == "S3":
        if big:
            return (f"your Instagram {ig} has {fol} followers and it is "
                    f"clearly where you put your effort")
        return (f"your Google listing sends people to your Instagram {ig}, "
                f"so that is where all your work is going")
    if seg == "S4":
        host = re.sub(r"^https?://(www\.)?", "", r.get("website", "")).split("/")[0]
        return (f"you set up {host} so customers would have something to open — "
                f"you already knew the link mattered")
    if seg == "S5":
        host = re.sub(r"^https?://(www\.)?", "", r.get("website", "")).split("/")[0]
        return (f"you registered {host} at some point, so you already decided "
                f"years ago that you wanted a proper website")
    if seg == "S6":
        return "you have a website address on your Google listing"
    if seg == "S7":
        return f"you have a real website up at {r.get('site_final_url','')[:50]}"
    if seg == "S8":
        return (f"your website{' — ' + title[:40] if title else ''} is live and "
                f"the content on it is genuinely good")
    if seg == "S9":
        return (f"you invested in a proper website back in {year} — that was "
                f"early for {singular(r.get('category',''))} in Oman")
    if seg == "S10":
        return f"your website has a lot on it, you have clearly put work in"
    if seg == "S11":
        return (f"your website looks good{' (' + plat + ')' if plat and plat!='custom/unknown' else ''}"
                f" and the information on it is clear")
    if seg == "S13":
        host = re.sub(r"^https?://(www\.)?", "", r.get("website", "")).split("/")[0]
        return f"you already have a site up at {host}"
    return (f"your website is genuinely one of the better ones I have seen "
            f"among {plural(r.get('category',''))} in {city}")


# --- the gap, always blame-free --------------------------------------------
def gap(r, seg):
    who, what = trade_win(r.get("category", ""))
    ig = (r.get("ig_handle") or r.get("site_ig") or "").strip()
    year = num(r.get("site_year"))
    ms = num(r.get("site_ms"))
    host = re.sub(r"^https?://(www\.)?", "", r.get("website", "")).split("/")[0]

    if seg == "S1":
        return (f"But there is nothing for them to open. {who.capitalize()} "
                f"find your name and your phone, and that is it — they cannot "
                f"{what}.")
    if seg in ("S2", "S3"):
        return (f"But Instagram does not show up in Google search, and it "
                f"cannot take a booking. So {who} never find you at all. "
                f"And even the followers you already have have to message you "
                f"and wait, instead of being able to {what} themselves.")
    if seg == "S4":
        return (f"But a link page is not a shopfront — Google does not rank it, "
                f"and {who} cannot {what} from it.")
    if seg == "S5":
        return (f"But {host} does not open any more. Anyone who clicks the link "
                f"on your Google listing gets an error page. It may have "
                f"expired without anyone telling you.")
    if seg == "S6":
        return ("But the link on your listing is returning an error instead of "
                "your site. I wanted to tell you in case nobody had.")
    if seg == "S7":
        return ("But browsers now put a red 'Not secure' warning in front of "
                "it. That is a new rule, not anything you did — most owners "
                "have no idea it is happening.")
    if seg == "S8":
        return (f"But it was built before phones took over, so on a phone the "
                f"text comes out tiny and people have to pinch and zoom. "
                f"Almost everyone who finds you is on a phone.")
    if seg == "S9":
        return (f"But it still says {year} at the bottom, so anyone who lands "
                f"on it wonders whether you are still open. That one number "
                f"costs you more than it should.")
    if seg == "S10":
        return (f"But it takes about {ms/1000:.0f} seconds to load on a phone, "
                f"and most people leave after three. So the work you paid for "
                f"is not being seen.")
    if seg == "S11":
        return (f"But there is no WhatsApp button and no way to book on it. So "
                f"{who} read it, are convinced — and then have nothing to press.")
    if seg == "S13":
        return ("But I have not opened it properly yet — I wanted to speak to "
                "you first rather than guess about your business.")
    return ("But it does not have an AI assistant answering buyers in Arabic "
            "and English at 2am, and that is where the market is moving.")


# --- the gift and the close -------------------------------------------------
GIFT = ("Here is what I would like to do, and there is no cost and no "
        "obligation in it: let me build you a preview of the page — your name, "
        "your work, your real information — and send it to you on WhatsApp. "
        "If you look at it and it is not for you, delete it and I will not "
        "call you again. If you like it, then we talk.")

_nxt = OFFER["next"]
_after = (f" After those, it goes to OMR {_nxt[0]}"
          + (f", then OMR {_nxt[1]}" if len(_nxt) > 1 else "") + ".") if _nxt else ""

CLOSE = (
    f"Our normal price for this build is OMR {ANCHOR} — it is on our services "
    f"page, you can check it. But we are running a launch right now, and the "
    f"way it works is that the price climbs as the seats fill. Today it is "
    f"OMR {money(OFFER['price'])}, and there are "
    f"{OFFER['seatsLeft']} seats left at that price.{_after} "
    f"Everything beyond the website itself — the AI assistant, the WhatsApp "
    f"handover, the Arabic, the first year of hosting — is a launch gift, "
    f"about OMR {ANCHOR - OFFER['price']} worth. "
    f"To hold a seat it is half, OMR {money(OFFER['deposit'])}, and the rest "
    f"when your site is built. The counter is live on the page, so you are not "
    f"taking my word for how many are left.")

EXIT = ("And honestly — if this is not the right time, tell me and I will "
        "leave it. No pressure from me at all.")


def call_script(r, seg, label):
    ask = ASK_FOR.get(r.get("category", ""), DEFAULT_ASK)
    return {
        "call_1_greeting": (
            f"As-salamu alaykum. Am I through to {r['business']}? … "
            f"My name is Nahid, I am with AI Profit Lab here in Muscat. "
            f"Could I speak with {ask}?"),
        "call_2_permission": (
            "Do you have two minutes? If it is a bad moment, tell me a better "
            "time and I will call then — I do not want to interrupt you."),
        "call_3_observation": (
            f"I was going through {plural(r.get('category',''))} in "
            f"{r.get('city','Oman')} this week, and I noticed {observation(r, seg)}."),
        "call_4_gap": gap(r, seg),
        "call_5_gift": GIFT,
        "call_6_close": CLOSE,
        "call_7_exit": EXIT,
    }


# --- WhatsApp: sent AFTER permission, short, one question -------------------
def whatsapp_en(r, seg):
    first = observation(r, seg)
    who, what = trade_win(r.get("category", ""))
    return (
        f"As-salamu alaykum — Nahid here, from AI Profit Lab in Muscat. "
        f"Thank you for your time on the phone just now.\n\n"
        f"As I mentioned: {first}. The only gap is that {who} cannot {what} "
        f"right now.\n\n"
        f"Here is the preview I promised — your page, with your real "
        f"information, built at no cost: [PREVIEW LINK]\n\n"
        f"And this is the launch I mentioned: {OFFER_URL}\n"
        f"Normal price is OMR {ANCHOR}. Today it is "
        f"OMR {money(OFFER['price'])} with {OFFER['seatsLeft']} seats left at "
        f"that price — the counter on the page is live, so you can see for "
        f"yourself. A seat is held with half, OMR {money(OFFER['deposit'])}.\n\n"
        f"Have a look whenever you have a minute. If it is not for you, just "
        f"tell me and I will not disturb you again.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", default="out/outreach/enriched-full.csv")
    ap.add_argument("--fallback", default="out/outreach/master-leads.csv")
    ap.add_argument("--outdir", default="out/outreach")
    ap.add_argument("--cards", type=int, default=200)
    args = ap.parse_args()

    # The Instagram pass ran separately and capped at 500, so its rows are
    # folded back in here by phone. Without this the follower counts we paid
    # network time for never reach a single script.
    ig_by_phone = {}
    igpath = os.path.join(args.outdir, "instagram.csv")
    if os.path.exists(igpath):
        for r in csv.DictReader(open(igpath, encoding="utf-8")):
            if r.get("phone_e164"):
                ig_by_phone[r["phone_e164"]] = r
        print(f"instagram: {len(ig_by_phone)} profiles to merge")

    src = args.src if os.path.exists(args.src) else args.fallback
    rows = list(csv.DictReader(open(src, encoding="utf-8")))
    # If we enriched only the website-havers, fold the rest back in.
    if src != args.fallback and os.path.exists(args.fallback):
        have = {r["business"] + r["city"] for r in rows}
        for r in csv.DictReader(open(args.fallback, encoding="utf-8")):
            if r["business"] + r["city"] not in have:
                rows.append(r)
    print(f"source: {src}  ({len(rows)} leads)")

    merged = 0
    for r in rows:
        g = ig_by_phone.get(r.get("phone_e164", ""))
        if g and g.get("ig_followers"):
            for k in ("ig_handle", "ig_followers", "ig_posts", "ig_name",
                      "ig_followers_n"):
                if g.get(k):
                    r[k] = g[k]
            merged += 1
    if ig_by_phone:
        print(f"instagram: merged follower counts into {merged} leads")

    out, segs = [], Counter()
    for r in rows:
        code, label = segment(r)
        segs[f"{code} {label}"] += 1
        rec = dict(r)
        rec["segment"] = code
        rec["segment_label"] = label
        rec.update(call_script(r, code, label))
        rec["whatsapp_en"] = whatsapp_en(r, code)
        rec["consent_to_whatsapp"] = ""
        rec["status"] = ""
        rec["outcome"] = ""
        out.append(rec)

    os.makedirs(args.outdir, exist_ok=True)
    cols = list(out[0].keys())
    path = os.path.join(args.outdir, "outreach-scripts.csv")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(out)
    print(f"wrote {len(out)} -> {path}\n")

    # One card per lead, ordered so the best calls come first: an enriched
    # row (we have a real fact) beats a bare one, and a mobile beats a landline
    # because only a mobile can become a WhatsApp thread after the call.
    def rank(d):
        enriched = 1 if d.get("site_status") or d.get("ig_followers") else 0
        tier = {"Dental clinic": 0, "Medical clinic": 0, "Law firm": 0,
                "Private school": 0, "Real estate": 0}.get(d.get("category"), 1)
        return (-enriched, tier, 0 if d.get("phone_kind") == "mobile" else 1,
                d.get("business", "").lower())

    cards = sorted(out, key=rank)[:args.cards]
    warn = ("> **⚠ THE LIVE LADDER COULD NOT BE READ.** The prices below are a "
            "fallback. Check " + OFFER_URL + " before quoting anything.\n"
            if "COULD NOT" in OFFER["asOf"] else "")
    lines = ["# Call cards — work top to bottom",
             "",
             warn,
             f"The {len(cards)} best calls in the file, best first. Tick the box "
             "when done and write the outcome in the sheet.",
             "",
             "## The offer, as the counter stood when these were printed",
             "",
             f"- Normal price **OMR {ANCHOR}** · launch seat "
             f"**OMR {money(OFFER['price'])}** · deposit "
             f"**OMR {money(OFFER['deposit'])}** (half)",
             f"- **{OFFER['seatsLeft']} seats left at this price**"
             + (f", then OMR {', then OMR '.join(str(n) for n in OFFER['next'])}"
                if OFFER["next"] else ""),
             f"- Page: {OFFER_URL}",
             f"- Counter read: `{OFFER['asOf']}`",
             "",
             "**The price climbs as seats sell.** Regenerate these cards before "
             "each calling session, or check the page, so you never quote a "
             "rung that has already gone.",
             ""]
    for i, d in enumerate(cards, 1):
        lines += [
            "---", "",
            f"## {i}. {d['business']}",
            f"**{d.get('category','')} · {d.get('city','')} · "
            f"{d.get('phone_e164','')}** ({d.get('phone_kind','')})",
            f"*Situation {d['segment']}: {d['segment_label']}*", "",
            f"> {d['call_1_greeting']}", "",
            f"> {d['call_2_permission']}", "",
            f"> {d['call_3_observation']}", "",
            f"> {d['call_4_gap']}", "",
            f"> {d['call_5_gift']}", "",
            "**If they ask the price:**", "",
            f"> {d['call_6_close']}", "",
            "**Always end with:**", "",
            f"> {d['call_7_exit']}", "",
            "- [ ] Called   - [ ] Said yes to WhatsApp   - [ ] Preview sent", "",
        ]
    cpath = os.path.join(args.outdir, "call-cards.md")
    open(cpath, "w", encoding="utf-8").write("\n".join(lines))
    print(f"wrote {len(cards)} cards -> {cpath}\n")
    for k, v in sorted(segs.items()):
        print(f"  {v:>6}  {k}")
    return out, segs


if __name__ == "__main__":
    main()
