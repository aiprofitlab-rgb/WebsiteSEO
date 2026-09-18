#!/usr/bin/env python3
"""
AI Profit Lab — every business in Oman's free zones and industrial cities, with
its phone, the state of its website, and what we can sell it.

The output matches the "Duqm Factories – Sales Call List" sheet column for
column, so each zone lands as one more tab of that same file and Mohammed calls
from them exactly as he calls from the Duqm tab.

STAGES — each reads the previous stage's files, so a re-run never re-bills:

    plan    the zones, their boxes, and the worst-case billed-call count
    sweep   Places Text Search inside each zone's box  -> <out>/raw/<zone>.json
    audit   website + listing checks, priority, pitch  -> <out>/<zone>.csv

Pushing the CSVs into the Google Sheet is push_zone_tabs.py.

WHERE THE ZONE BOXES COME FROM. Not guessed: each box is the bounding box of the
zone's own polygon in OpenStreetMap (way ids noted per zone), pulled 2026-09-18.
Zones OSM has only as a point (Salalah Free Zone, Al Mazunah, Sur, Samail,
Khazaen) get a box around that point, and the sweep prints what Google itself
returns inside it, so a bad box shows up as an obviously wrong business list.

COST. Same design as broken_site_finder.py — read its COST DESIGN note. One
Text Search Enterprise call returns 20 businesses WITH website + phone; never
loop Place Details. Every call is cached on disk keyed by (term, box, page), so
an interrupted sweep resumes for free, and --max-calls is a hard stop.

A generic term ("company") inside a dense box like Ghala saturates Google's
60-result ceiling. When a (term, box) comes back full, the box is split in four
and that term re-run in each quarter, down to --max-depth. That is the only way
to enumerate a dense area rather than sample it.

Lead data never goes in this repo (it is public). Default output is Core4.

Usage:
    python3 tools/prospecting/zone_sweep.py plan
    python3 tools/prospecting/zone_sweep.py sweep --zones rusayl,sohar-fz --max-calls 300
    python3 tools/prospecting/zone_sweep.py audit
"""

import argparse
import concurrent.futures as cf
import csv
import datetime
import zlib
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import broken_site_finder as bsf          # noqa: E402  TLS, DNS retry, defect checks
from enrich_leads import name_matches_domain   # noqa: E402

OUT_DIR = os.path.expanduser(
    "~/Desktop/Nahid/Core4/ColdOutreach/Leads for website offer/industrial-zones")
FULL_LIST = os.path.expanduser(
    "~/Desktop/AI Profit Lab - Outreach Kit/FULL LEAD LIST (all 20k).csv")

# --------------------------------------------------------------------------
# Zones. Order matters: a business inside two overlapping boxes is filed under
# the FIRST zone listed, so specific zones come before the areas around them.
# Box = (lat_lo, lng_lo, lat_hi, lng_hi).
# --------------------------------------------------------------------------


def around(lat, lng, half_km):
    dlat = half_km / 111.0
    dlng = half_km / (111.0 * math.cos(math.radians(lat)))
    return (round(lat - dlat, 4), round(lng - dlng, 4),
            round(lat + dlat, 4), round(lng + dlng, 4))


ZONES = [
    # --- free zones (Duqm is already its own tab) -------------------------
    {"key": "sohar-fz", "tab": "Sohar Port & Freezone", "short": "Sohar Freezone",
     "kind": "Free zone",
     "boxes": [(24.4498, 56.5394, 24.4811, 56.5683),      # OSM way 326845165 Freezone
               (24.4528, 56.5840, 24.5298, 56.6463)]},    # OSM way 326843841 Sohar Port
    {"key": "salalah-fz", "tab": "Salalah Free Zone", "short": "Salalah Free Zone",
     "kind": "Free zone",
     "boxes": [around(16.9385, 53.9679, 3.5)]},          # OSM way, centre only
    {"key": "mazunah-fz", "tab": "Al Mazunah Free Zone", "short": "Al Mazunah",
     "kind": "Free zone",
     "boxes": [around(17.8326, 52.6174, 2.5)]},          # OSM node, centre only
    # --- Madayn industrial cities ------------------------------------------
    {"key": "rusayl", "tab": "Rusayl Industrial City", "short": "Rusayl",
     "kind": "Madayn industrial city",
     "boxes": [(23.5454, 58.1726, 23.5680, 58.2346)]},    # OSM way 36903705
    {"key": "sohar-ic", "tab": "Sohar Industrial City", "short": "Sohar Industrial City",
     "kind": "Madayn industrial city",
     "boxes": [(24.4057, 56.5377, 24.4505, 56.6081),      # OSM way 181602432 Majan Industrial Area
               (24.3784, 56.4974, 24.4190, 56.5297)]},    # OSM way 565166544 "Phase 7"
    {"key": "raysut", "tab": "Raysut Industrial City", "short": "Raysut",
     "kind": "Madayn industrial city",
     "boxes": [(16.9661, 53.9771, 16.9912, 54.0016)]},    # OSM way 353906507
    {"key": "nizwa", "tab": "Nizwa Industrial City", "short": "Nizwa Industrial Area",
     "kind": "Madayn industrial city",
     "boxes": [(22.8314, 57.4760, 22.8538, 57.4989),      # OSM way 369968250
               (22.8295, 57.5415, 22.8480, 57.5574)]},    # OSM way 265634220 Karsha industrial
    {"key": "buraimi", "tab": "Buraimi Industrial City", "short": "Buraimi Industrial City",
     "kind": "Madayn industrial city",
     "boxes": [(24.2659, 55.8091, 24.3142, 55.8255)]},    # OSM way 367182128
    {"key": "ibri", "tab": "Ibri Industrial City", "short": "Ibri Industrial City",
     "kind": "Madayn industrial city",
     "boxes": [(23.0925, 56.3470, 23.1126, 56.3661)]},    # OSM way 1465668244
    {"key": "sur", "tab": "Sur Industrial City", "short": "Sur Industrial City",
     "kind": "Madayn industrial city",
     "boxes": [around(22.6305, 59.4282, 2.5)]},          # OSM node: Sur Industrial Area admin office
    {"key": "samail", "tab": "Samail Industrial City", "short": "Samail Industrial City",
     "kind": "Madayn industrial city",
     "boxes": [around(23.2654, 58.1566, 2.0)]},          # OSM way: Samail Industrial Area Road
    {"key": "khazaen", "tab": "Khazaen Economic City", "short": "Khazaen",
     "kind": "Economic city",
     "boxes": [(23.5500, 57.7700, 23.6000, 57.8500)]},    # OSM ways: Khazaen Economic City + Dry Port
    # --- Muscat's municipal industrial areas -------------------------------
    {"key": "ghala", "tab": "Ghala Industrial Area", "short": "Ghala Industrial Area",
     "kind": "Industrial area",
     "boxes": [(23.5627, 58.3332, 23.5828, 58.3824)]},    # OSM way 289011558
    {"key": "wadi-kabir", "tab": "Wadi Kabir Industrial Area", "short": "Wadi Kabir",
     "kind": "Industrial area",
     "boxes": [(23.5843, 58.5527, 23.5995, 58.5806)]},    # OSM way 1425796786
    {"key": "mabelah", "tab": "Mabelah Industrial Area", "short": "Mabelah Industrial Area",
     "kind": "Industrial area",
     "boxes": [(23.6323, 58.0898, 23.6623, 58.1092)]},    # OSM way 1381633275
]
ZONE_BY_KEY = {z["key"]: z for z in ZONES}

# Generic enough to enumerate an industrial box, specific enough that Google
# ranks businesses (not roads) first. Arabic terms surface the listings whose
# only name is Arabic, which the English terms rank last or miss.
TERMS = ["company", "factory", "trading", "engineering", "industries", "logistics",
         "workshop", "supplier", "contracting", "LLC", "شركة", "مصنع"]

SEARCH_FIELDS = ",".join("places." + f for f in (
    "id", "displayName", "formattedAddress", "location", "websiteUri",
    "nationalPhoneNumber", "internationalPhoneNumber", "googleMapsUri",
    "rating", "userRatingCount", "primaryType", "primaryTypeDisplayName",
    "types", "businessStatus", "photos", "regularOpeningHours",
)) + ",nextPageToken"

PAGES = 3                    # Google's ceiling: 3 pages x 20 = 60 per query
MIN_SPLIT_KM = 0.6           # never split a box smaller than this on a side

# --------------------------------------------------------------------------
# Who is NOT a prospect. Industrial areas are full of cafeterias, mosques,
# ATMs and labour camps; the 20k consumer list already covers shops and clinics.
# Everything dropped is counted in SUMMARY.txt, so nothing disappears silently.
# --------------------------------------------------------------------------
EXCLUDE_TYPES = {
    "mosque": "worship", "place_of_worship": "worship", "church": "worship",
    "hindu_temple": "worship",
    "atm": "bank/ATM", "bank": "bank/ATM",
    "gas_station": "fuel station",
    "restaurant": "food service", "cafe": "food service", "coffee_shop": "food service",
    "fast_food_restaurant": "food service", "meal_takeaway": "food service",
    "meal_delivery": "food service", "indian_restaurant": "food service",
    "cafeteria": "food service", "tea_house": "food service",
    "supermarket": "grocery/retail", "grocery_store": "grocery/retail",
    "convenience_store": "grocery/retail", "hypermarket": "grocery/retail",
    "barber_shop": "personal care", "beauty_salon": "personal care",
    "hair_salon": "personal care", "laundry": "personal care",
    "police": "government", "local_government_office": "government",
    "government_office": "government", "city_hall": "government",
    "courthouse": "government", "embassy": "government", "post_office": "government",
    "school": "education", "primary_school": "education",
    "secondary_school": "education", "university": "education",
    "hospital": "health", "pharmacy": "health", "doctor": "health",
    "dentist": "health", "medical_clinic": "health", "drugstore": "health",
    "bus_stop": "transit/parking", "bus_station": "transit/parking",
    "transit_station": "transit/parking", "parking": "transit/parking",
    "park": "not a business", "tourist_attraction": "not a business",
    "lodging": "lodging/camp", "hotel": "lodging/camp",
    "route": "not a business", "locality": "not a business",
    "sublocality": "not a business", "neighborhood": "not a business",
    "political": "not a business", "premise": "not a business",
    "street_address": "not a business", "apartment_building": "not a business",
}
EXCLUDE_NAME_RX = re.compile(
    r"\b(gate|roundabout|bus stop|labou?r camp|camp|accommodation|mess|masjid|"
    r"mosque|cafeteria|restaurant|coffee shop|atm|madayn|public authority|ministry)\b"
    r"|مسجد|جامع|بوابة|دوار|مقهى|مطعم|كافتيريا|سكن العمال",
    re.I)

# Backstop on Google's category text, for places whose primaryType is missing.
EXCLUDE_CAT_RX = re.compile(
    r"pharmacy|clinic|hospital|medical cent|dentist|doctor|restaurant|caf[eé]|coffee|"
    r"cafeteria|bakery shop|grocery|supermarket|hypermarket|convenience|salon|barber|"
    r"\bspa\b|gym|fitness|school|institute|college|university|kindergarten|nursery|"
    r"mosque|hotel|apartment|hostel|bank|atm|government|police|embassy|park\b|"
    r"gas station|petrol|bus stop|parking",
    re.I)

# Large groups and multinationals: reachable only through head office, bought
# by tender. Rated C (low chance) like Port of Duqm and Jindal in the Duqm tab.
BIG_RX = re.compile(
    r"\b(oq8?|orpic|omifco|pdo|petroleum development|oman oil|oman lng|vale|jindal|"
    r"sohar aluminium|oman cement|raysut cement|oman flour mills|asyad|port of|"
    r"oman cables|voltamp|jazeera steel|sabic|dhl|aramex|fedex|oman post|omantel|"
    r"ooredoo|vodafone|nama (water|dhofar|electricity|power)|shell|nestl[eé]|pepsi|coca[- ]cola|unilever|siemens|"
    r"schlumberger|halliburton|baker hughes|weatherford|suhail bahwan|bahwan|"
    r"zubair (corporation|automotive)|towell|khimji|galfar|al tasnim|assarain|al hassan engineering|"
    r"mazoon (dairy|electricity)|a'saffa|areej vegetable|oman refreshment|national mineral water|lulu|carrefour|"
    r"sohar international|bank muscat|national bank of oman|hsbc|oman arab bank|"
    r"ahli bank|oman oil marketing|al maha petroleum|octal|oman india fertili[sz]er|"
    r"sohar power|phoenix power|oman chlorine|al anwar ceramic|oman ceramic|"
    r"sembcorp|acwa|engie|oman electricity|oman broadband|salalah port|"
    r"salalah methanol|oman methanol|dhofar cattle|oman fisheries)\b",
    re.I)
BIG_REVIEW_COUNT = 100       # an industrial listing this reviewed is a big employer

# --------------------------------------------------------------------------
# Sectors decide the pitch. Checked in order; first match wins. Name, Google
# category and site title are searched, never the address ("Industrial Area"
# in an address would otherwise make every business a manufacturer).
# --------------------------------------------------------------------------
SECTORS = [
    ("construction", "contractors", r"concrete|ready ?-?mix|\bblock|interlock|cement|asphalt|quarr|crush|aggregate|precast|kerb|gravel|خرسان|طابوق|اسمنت|إسمنت|كسار|اسفلت|أسفلت|بلوك|خرسانة"),
    ("food", "shops and distributors", r"\bfood|water|dairy|milk|bakery|bread|flour|juice|\bice\b|beverage|sweets|halwa|\bdates\b|fish|seafood|meat|poultry|chicken|spice|\brice\b|coffee|\btea\b|مياه|غذائ|ألبان|البان|مخبز|حلوى|حلويات|تمور|أسماك|اسماك|لحوم|دواجن|ثلج|عصير|قهوة"),
    ("automotive", "customers", r"\bcars?\b|\bauto|garage|tyre|tire|spare parts?|motors?\b|vehicle|mechanic|body shop|radiator|سيارات|قطع غيار|إطارات|اطارات|كراج"),
    ("fabrication", "clients", r"steel|fabricat|engineering|mechanical|electro|welding|scaffold|metal|alumin|glass|workshop|machin|cnc|hydraulic|حديد|هندس|ورشة|ألمنيوم|المنيوم|زجاج|لحام|معادن"),
    ("manufacturing", "buyers", r"plastic|polymer|chemical|paint|pipe|cable|wire|paper|packag|carton|print|textile|garment|pharma|fertili|detergent|soap|cosmetic|furniture|wood|foam|rubber|battery|lubricant|oxygen|factory|industr|manufactur|mill\b|مصنع|صناع|بلاستيك|كيماو|دهان|أنابيب|انابيب|كابلات|ورق|تغليف|طباعة|أثاث|اثاث|خشب"),
    ("logistics", "customers", r"logistic|transport|shipping|freight|cargo|forward|clearing|warehous|storage|courier|movers|haulage|نقل|شحن|لوجست|مخازن|تخزين|تخليص"),
    ("rental", "customers", r"rental|\brent|hire|crane|heavy equipment|equipment|تأجير|معدات|رافعات"),
    ("trading", "buyers", r"trading|\btrade|import|export|distribut|wholesale|supplier|supplies|تجارة|تجاري|توزيع|استيراد|موزع|توريد"),
    ("services", "clients", r"cleaning|security|manpower|facility|pest|maintenance|contracting|contractor|construction|building|مقاولات|تنظيف|صيانة|خدمات"),
]
SECTOR_LABEL = {
    "construction": "Construction materials", "food": "Food & water production",
    "automotive": "Automotive services / parts", "fabrication": "Engineering & fabrication",
    "manufacturing": "Manufacturer", "logistics": "Logistics & warehousing",
    "rental": "Equipment rental", "trading": "Trading & distribution",
    "services": "Contracting & services", "general": "Industrial business",
}

HEADER = [
    "Priority (A = call first, B = good lead, C = big company / low chance, Skip = no phone)",
    "Company", "What they do", "Phone to call (Oman)", "Other contacts",
    "Website status", "Google Maps rating", "Weaknesses we can fix", "What to offer",
    "Call opener (what to say first)", "Google Maps link", "Source", "Call status",
    "Follow-up date", "Notes",
]

# ==========================================================================
# plan / sweep
# ==========================================================================


def box_km(box):
    lat_lo, lng_lo, lat_hi, lng_hi = box
    h = (lat_hi - lat_lo) * 111.0
    w = (lng_hi - lng_lo) * 111.0 * math.cos(math.radians(lat_lo))
    return w, h


def split4(box):
    lat_lo, lng_lo, lat_hi, lng_hi = box
    lat_m, lng_m = (lat_lo + lat_hi) / 2, (lng_lo + lng_hi) / 2
    r = lambda b: tuple(round(v, 5) for v in b)            # noqa: E731
    return [r((lat_lo, lng_lo, lat_m, lng_m)), r((lat_lo, lng_m, lat_m, lng_hi)),
            r((lat_m, lng_lo, lat_hi, lng_m)), r((lat_m, lng_m, lat_hi, lng_hi))]


def cmd_plan(args):
    zones = pick_zones(args.zones)
    base = sum(len(z["boxes"]) for z in zones) * len(TERMS)
    print(f"{len(zones)} zones, {len(TERMS)} search terms each.\n")
    for z in zones:
        area = sum(w * h for w, h in map(box_km, z["boxes"]))
        print(f"  {z['key']:12} {z['tab']:30} {len(z['boxes'])} box(es), {area:6.1f} km2")
    print(f"\nBilled Text Search Enterprise calls:\n"
          f"  floor   ~{base}  (every term fits on one page)\n"
          f"  typical ~{base * 2}  (most terms 1-2 pages, a few dense boxes split)\n"
          f"  ceiling  --max-calls {args.max_calls} (hard stop; re-run resumes from cache)\n"
          f"1,000 calls are free per calendar month, then ~$40 per 1,000.\n"
          f"Terms: {', '.join(TERMS)}")


def pick_zones(spec):
    if not spec or spec == "all":
        return ZONES
    keys = [k.strip() for k in spec.split(",") if k.strip()]
    bad = [k for k in keys if k not in ZONE_BY_KEY]
    if bad:
        sys.exit(f"Unknown zone(s): {bad}. Known: {', '.join(ZONE_BY_KEY)}")
    return [ZONE_BY_KEY[k] for k in keys]


class Sweeper:
    def __init__(self, api_key, cache_path, max_calls, max_depth):
        self.key = api_key
        self.cache_path = cache_path
        self.cache = json.load(open(cache_path)) if os.path.exists(cache_path) else {}
        self.calls = 0
        self.max_calls = max_calls
        self.max_depth = max_depth
        self.stopped = False

    def save(self):
        tmp = self.cache_path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.cache, f, ensure_ascii=False)
        os.replace(tmp, self.cache_path)

    def page(self, term, box, page_no, token):
        ck = f"{term}|{','.join(map(str, box))}|{page_no}"
        if ck in self.cache:
            return self.cache[ck]
        if self.calls >= self.max_calls:
            self.stopped = True
            return None
        body = {"textQuery": term, "pageSize": 20, "languageCode": "en",
                "locationRestriction": {"rectangle": {
                    "low": {"latitude": box[0], "longitude": box[1]},
                    "high": {"latitude": box[2], "longitude": box[3]}}}}
        if token:
            body["pageToken"] = token
        payload = bsf._request(f"{bsf.API_ROOT}/places:searchText", self.key,
                               SEARCH_FIELDS, body)
        self.calls += 1
        time.sleep(bsf.PAUSE_SECONDS)
        if payload is None:
            return None                    # transient error: not cached, retried next run
        self.cache[ck] = payload
        if self.calls % 10 == 0:
            self.save()
        return payload

    def search(self, term, box):
        found, token = [], None
        for page_no in range(PAGES):
            payload = self.page(term, box, page_no, token)
            if not payload:
                break
            found.extend(payload.get("places", []))
            token = payload.get("nextPageToken")
            if not token:
                break
        return found

    def sweep_box(self, term, box, depth=0):
        found = self.search(term, box)
        w, h = box_km(box)
        saturated = len(found) >= PAGES * 20
        if saturated and depth < self.max_depth and min(w, h) / 2 >= MIN_SPLIT_KM:
            for sub in split4(box):
                if self.stopped:
                    break
                found.extend(self.sweep_box(term, sub, depth + 1))
        return found


def cmd_sweep(args):
    zones = pick_zones(args.zones)
    os.makedirs(os.path.join(args.out, "raw"), exist_ok=True)
    sw = Sweeper(bsf.load_api_key(), os.path.join(args.out, "raw", "_search-cache.json"),
                 args.max_calls, args.max_depth)
    print(f"Sweeping {len(zones)} zone(s); hard stop at {args.max_calls} billed calls. "
          f"Cached pages are free.\n")
    try:
        sweep_zones(zones, sw, args)
    finally:
        sw.save()                  # a 403 mid-run exits; never lose paid-for pages
    print(f"\nBilled calls this run: {sw.calls}.")


def sweep_zones(zones, sw, args):
    for z in zones:
        places = {}
        for box in z["boxes"]:
            for term in TERMS:
                if sw.stopped:
                    break
                for p in sw.sweep_box(term, box):
                    if p.get("id"):
                        places.setdefault(p["id"], p)
        path = os.path.join(args.out, "raw", f"{z['key']}.json")
        with open(path, "w") as f:
            json.dump(list(places.values()), f, ensure_ascii=False)
        sample = ", ".join(p.get("displayName", {}).get("text", "?")
                           for p in list(places.values())[:4])
        print(f"  {z['tab']:30} {len(places):4} places   e.g. {sample[:90]}")
        if sw.stopped:
            print(f"\n--max-calls {args.max_calls} reached. Progress is cached; "
                  "re-run the same command to continue.")
            break

# ==========================================================================
# audit — website
# ==========================================================================


UA_BROWSER = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
THIRD_PARTY_HOSTS = ("linktr.ee", "sites.google.com", "business.site", "my.canva.site",
                     "wixsite.com", "blogspot.", "wordpress.com", "google.com",
                     "goo.gl", "yellowpages", "omanyp", "dnb.com",
                     "indiamart", "alibaba.com", "tradeindia", "kompass")
PLATFORMS = (("GoDaddy builder", ("img1.wsimg.com", "godaddysites.com")),
             ("Wix", ("wixstatic", "wix.com")), ("WordPress", ("wp-content", "wp-includes")),
             ("Shopify", ("cdn.shopify.com",)), ("Squarespace", ("squarespace",)),
             ("Webflow", ("website-files.com", "webflow")), ("Google Sites", ("sites.google.com",)))
EMAIL_RX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
FREEMAIL_RX = re.compile(r"@(gmail|hotmail|yahoo|outlook|live|icloud)\.", re.I)
ARABIC_RX = re.compile(r"[؀-ۿ]")
WA_RX = re.compile(r"(?:wa\.me/|api\.whatsapp\.com/send\?phone=|whatsapp\.com/send\?phone=)\+?(\d{8,15})", re.I)
TEL_RX = re.compile(r"tel:|(?:\+|00)?968[\s-]?\d{4}[\s-]?\d{4}|\b[279]\d{3}[\s-]?\d{4}\b")
FORM_RX = re.compile(r"<textarea|type=[\"']?(email|tel)|wpcf7|wpforms|gform_|elementor-form|"
                     r"formspree|hs-form|ninja-forms|fluentform", re.I)
QUOTE_RX = re.compile(r"request (a |for )?quot|get (a )?quot|rfq|enquir|inquir|طلب عرض سعر|استفسار", re.I)


def _get(url, timeout, ua):
    """GET with a chosen UA, gzip aware. Returns bsf.Fetch."""
    req = urllib.request.Request(url, headers={
        "User-Agent": ua, "Accept": "text/html,application/xhtml+xml,*/*",
        "Accept-Language": "en,ar;q=0.8", "Accept-Encoding": "gzip"})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=bsf.SSL_CONTEXT) as r:
            raw = r.read(bsf.MAX_READ * 4)
            if r.headers.get("Content-Encoding") == "gzip":
                # decompressobj tolerates the truncated stream a capped read leaves;
                # GzipFile raises EOFError, which would misreport a live site as dead
                try:
                    raw = zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(raw)
                except zlib.error:
                    pass
            return bsf.Fetch(status=r.status, final_url=r.geturl(),
                             body=raw.decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        return bsf.Fetch(status=e.code, final_url=e.geturl())
    except Exception as e:                                  # noqa: BLE001
        bucket, evidence, kind = bsf._classify(e)
        return bsf.Fetch(bucket=bucket, evidence=evidence, kind=kind)


_DOH_CACHE = {}


def doh_exists(host):
    """Ask Cloudflare (by IP, so local DNS is never consulted) whether a domain
    exists. True / False, or None when Cloudflare cannot be reached."""
    if host in _DOH_CACHE:
        return _DOH_CACHE[host]
    ans = None
    for attempt in range(2):
        try:
            req = urllib.request.Request(
                f"https://1.1.1.1/dns-query?name={urllib.parse.quote(host)}&type=A",
                headers={"accept": "application/dns-json", "User-Agent": bsf.USER_AGENT})
            with urllib.request.urlopen(req, timeout=10, context=bsf.SSL_CONTEXT) as r:
                d = json.loads(r.read().decode())
            status = d.get("Status")
            if status == 3:                       # NXDOMAIN: genuinely not there
                ans = False
            elif status == 0:
                ans = bool(d.get("Answer")) or bool(d.get("Authority"))
            break
        except Exception:                          # noqa: BLE001
            time.sleep(1 + attempt)
    _DOH_CACHE[host] = ans
    return ans


def domain_is_theirs(name, url):
    """name_matches_domain, plus initials: owg.om IS One Worldwide Group's."""
    if name_matches_domain(name, url):
        return True
    base = re.sub(r"^www\.", "", bsf._host_of(url)).split(".")[0]
    words = [w for w in re.findall(r"[A-Za-z]+", name or "")
             if w.lower() not in ("the", "and", "of", "for", "llc", "l", "co", "spc", "saoc", "saog")]
    initials = "".join(w[0] for w in words).lower()
    return len(initials) >= 2 and base.startswith(initials[:3])


def visible_text(html):
    t = re.sub(r"<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def audit_site(raw_url, name, timeout=12):
    """One business's website. Never condemns a site on one failure.

    status: NONE | SOCIAL | THIRD_PARTY | DEAD | UNSURE | PLACEHOLDER | OK
    UNSURE means the server refused an automated check (Cloudflare and friends);
    such a row must never be told its site is broken.
    """
    a = {"status": "NONE", "evidence": "", "url": raw_url or "", "final": "",
         "host": "", "issues": [], "emails": [], "wa": "", "platform": "",
         "title": "", "desc": "", "theirs": True, "year": 0, "site_phone": ""}
    if not raw_url:
        return a
    url = raw_url.strip()
    if not re.match(r"^https?://", url, re.I):
        url = "http://" + url
    host = bsf._host_of(url)
    a["host"] = re.sub(r"^www\.", "", host)
    if bsf.is_social(url):
        a.update(status="SOCIAL", evidence=a["host"])
        return a
    if any(h in host for h in THIRD_PARTY_HOSTS):
        a.update(status="THIRD_PARTY", evidence=a["host"])
        return a
    ok, why = bsf.resolve(host)
    if not ok:
        # This network's resolver (the router, 192.168.100.1) answers NXDOMAIN for
        # some domains that exist - tinyurl.com among them, verified 2026-09-18.
        # Only Cloudflare's own answer may declare a domain gone.
        exists = doh_exists(host)
        if exists is None:
            a.update(status="UNSURE", evidence="DNS lookup failed here and could not be double-checked")
        elif exists:
            a.update(status="UNSURE", evidence="the domain exists but this network's DNS blocks it")
        else:
            a.update(status="DEAD", evidence="no longer exists (the domain is not registered or has no DNS)")
        return a

    parts = urllib.parse.urlsplit(url)
    https_url = urllib.parse.urlunsplit(("https",) + tuple(parts)[1:])
    http_url = urllib.parse.urlunsplit(("http",) + tuple(parts)[1:])

    got = _get(https_url, timeout, bsf.USER_AGENT)
    if got.bucket == "DEAD" and got.kind == "timeout":
        time.sleep(1)
        got = _get(https_url, timeout, bsf.USER_AGENT)
    https_ok = got.bucket is None and got.status and got.status < 400
    if not https_ok:
        # Blocked or erroring for our honest UA? Ask again as a browser before judging.
        if got.bucket is None and got.status:
            again = _get(https_url, timeout, UA_BROWSER)
            if again.bucket is None and again.status and again.status < 400:
                got, https_ok = again, True
    if not https_ok:
        plain = _get(http_url, timeout, UA_BROWSER)
        if plain.bucket is None and plain.status and plain.status < 400:
            if not (plain.final_url or "").startswith("https"):
                a["issues"].append(("NO_SSL", "no secure (https) version: browsers show 'Not secure'"))
            got = plain
        else:
            codes = {s for s in (got.status, plain.status) if s}
            if codes & {401, 403, 429, 503} or (got.kind == "tls" and not plain.status):
                a.update(status="UNSURE", evidence=(
                    "the server refused an automated check (HTTP "
                    + "/".join(map(str, sorted(codes))) + ")" if codes
                    else f"TLS problem: {got.evidence}"))
                return a
            # The listing may point at a deep page that was deleted while the
            # homepage lives on. That is a broken Maps link, not a dead company site.
            if codes and parts.path not in ("", "/"):
                root = urllib.parse.urlunsplit(("https", parts.netloc, "/", "", ""))
                home = _get(root, timeout, UA_BROWSER)
                if home.bucket is None and home.status and home.status < 400:
                    a["issues"].append(("BAD_LINK", f"the Google Maps link points to a page that no "
                                        f"longer exists (HTTP {min(codes)}); the homepage works"))
                    got = home
            if not (got.bucket is None and got.status and got.status < 400):
                code = min(codes) if codes else 0
                if code in (404, 410):
                    ev = f"shows 'page not found' (HTTP {code})"
                elif code >= 500:
                    ev = f"shows a server error (HTTP {code})"
                elif code:
                    ev = f"returns an error (HTTP {code})"
                elif "timeout" in (got.kind or "", plain.kind or ""):
                    ev = "does not load (no response)"
                else:
                    ev = "does not load (" + (plain.evidence or got.evidence or "unreachable") + ")"
                a.update(status="DEAD", evidence=ev)
                return a

    html = got.body or ""
    a["final"] = got.final_url or https_url
    a["status"] = "OK"
    for bucket, ev in bsf.inspect_html(html, a["final"]):
        if bucket == "PLACEHOLDER":
            a.update(status="PLACEHOLDER", evidence=ev)
        elif bucket == "NOT_MOBILE":
            a["issues"].append(("NOT_MOBILE", "does not fit a phone screen (no mobile layout)"))
        elif bucket == "STALE":
            yr = re.search(r"(\d{4})", ev)
            a["year"] = int(yr.group(1)) if yr else 0
            a["issues"].append(("STALE", f"footer still says © {a['year']}"))
    if a["status"] == "PLACEHOLDER":
        return a

    low = html.lower()
    text = visible_text(html)
    t = bsf.TITLE_RE.search(html)
    a["title"] = re.sub(r"\s+", " ", t.group(1)).strip()[:120] if t else ""
    m = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']{15,220})', html, re.I)
    a["desc"] = m.group(1).strip() if m else ""
    for label, needles in PLATFORMS:
        if any(n in low for n in needles):
            a["platform"] = label
            break
    a["theirs"] = domain_is_theirs(name, a["final"])

    if len(text) < 250 and re.search(r'id=["\'](root|app|__next|__nuxt)["\']|ng-version', html, re.I):
        a["issues"].append(("JS_ONLY", "text loads only through JavaScript, so Google and AI tools see almost nothing"))
    has_form = bool(FORM_RX.search(html))
    has_quote = bool(QUOTE_RX.search(text))
    wa = WA_RX.search(html)
    if wa:
        a["wa"] = wa.group(1)
    if not has_form and not has_quote:
        a["issues"].append(("NO_FORM", "no quote or inquiry form on the homepage"))
    if not wa and "whatsapp" not in low:
        a["issues"].append(("NO_WA", "no WhatsApp button"))
    for m in re.finditer(r"tel:\s*(?:\+|00)?(?:968)?[\s-]*([279]\d{3})[\s-]*(\d{4})|"
                         r"(?:\+|00)968[\s-]*([279]\d{3})[\s-]*(\d{4})", html):
        g = [x for x in m.groups() if x]
        a["site_phone"] = f"{g[0]} {g[1]}"
        break
    if not TEL_RX.search(html):
        a["issues"].append(("NO_TEL", "no phone number on the homepage"))
    if text and not ARABIC_RX.search(text):
        a["issues"].append(("EN_ONLY", "English only, no Arabic"))
    emails = []
    for e in EMAIL_RX.findall(html):
        e = e.strip(".").lower()
        if e.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")) or any(
                x in e for x in ("example", "sentry", "wixpress", "domain.com", "email.com",
                                 "yourdomain", "@2x", "godaddy", "schema.org")):
            continue
        if e not in emails:
            emails.append(e)
    a["emails"] = emails[:3]
    if any(FREEMAIL_RX.search(e) for e in emails):
        a["issues"].append(("FREEMAIL", "uses a Gmail/Hotmail address, which looks weak to big buyers and in tenders"))
    return a

# ==========================================================================
# audit — listing, priority, pitch
# ==========================================================================


def sector_of(p, site):
    blob = " ".join([p.get("displayName", {}).get("text", ""),
                     p.get("primaryTypeDisplayName", {}).get("text", ""),
                     site.get("title", "") if site.get("theirs") else ""])
    for key, _, rx in SECTORS:
        if re.search(rx, blob, re.I):
            return key
    return "general"


def buyers_of(sector):
    return next((b for k, b, _ in SECTORS if k == sector), "customers")


def phone_of(p):
    n = (p.get("nationalPhoneNumber") or "").strip()
    if not n and p.get("internationalPhoneNumber"):
        n = re.sub(r"^\+968\s*", "", p["internationalPhoneNumber"])
    return n


def digits8(s):
    d = re.sub(r"\D", "", s or "")
    return d[-8:] if len(d) >= 8 else ""


def is_mobile(num):
    d = digits8(num)
    return bool(d) and d[0] in "79"


def rating_text(p):
    r, n = p.get("rating"), p.get("userRatingCount") or 0
    photos = len(p.get("photos") or [])
    ph = "no photos" if not photos else ("10+ photos" if photos >= 10 else
                                         f"{photos} photo{'s' if photos > 1 else ''}")
    if r:
        return f"★{r:.1f} ({n} review{'s' if n != 1 else ''}) · {ph}"
    return f"No rating · {ph}"


def excluded_reason(p):
    name = p.get("displayName", {}).get("text", "")
    if p.get("businessStatus") == "CLOSED_PERMANENTLY":
        return "permanently closed"
    types = p.get("types") or []
    # A factory Google also tags "store" is still a factory, so only the primary
    # type (or the first specific one when Google gives none) decides, plus a few
    # secondary types that are never a prospect whatever else the place is.
    prim = p.get("primaryType") or next(
        (t for t in types if t not in ("point_of_interest", "establishment")), None)
    if prim in EXCLUDE_TYPES:
        return EXCLUDE_TYPES[prim]
    for t in types:
        if t in ("mosque", "place_of_worship", "atm", "gas_station", "police"):
            return EXCLUDE_TYPES[t]
    if EXCLUDE_NAME_RX.search(name):
        return "not a business (name)"
    cat = p.get("primaryTypeDisplayName", {}).get("text", "")
    m = EXCLUDE_CAT_RX.search(cat)
    if m:
        return "consumer/other category (" + m.group(0).lower() + ")"
    return ""


def is_big(p, domain_counts, site):
    name = p.get("displayName", {}).get("text", "")
    if BIG_RX.search(name):
        return "large group / multinational"
    if (p.get("userRatingCount") or 0) >= BIG_REVIEW_COUNT:
        return f"{p['userRatingCount']} Google reviews, a big employer"
    if site.get("host") and domain_counts.get(site["host"], 0) >= 3:
        return f"branch of a group ({domain_counts[site['host']]} listings share {site['host']})"
    return ""


def website_status_text(site, name):
    s, h = site["status"], site["host"]
    if s == "NONE":
        return "NONE: no website on their Google Maps listing"
    if s == "SOCIAL":
        return f"SOCIAL ONLY: the Website button on Google Maps opens a social page ({h}), not a website"
    if s == "THIRD_PARTY":
        return f"NO OWN SITE: the Google Maps link goes to {h}, someone else's platform"
    if s == "DEAD":
        return f"BROKEN: the Website button on Google Maps opens {h}, which {site['evidence']}"
    if s == "PLACEHOLDER":
        return f"BROKEN: {h} opens a placeholder page, not a real site ({site['evidence']})"
    if s == "UNSURE":
        return f"CHECK BY HAND: {h} blocked our automatic check ({site['evidence']}). Open it yourself before calling"
    strong = [ev for k, ev in site["issues"]
              if k in ("BAD_LINK", "NO_SSL", "NOT_MOBILE", "STALE", "JS_ONLY")]
    gaps = [ev for k, ev in site["issues"] if k in ("NO_FORM", "NO_WA", "EN_ONLY")]
    owner = "" if site["theirs"] else " (domain may belong to a parent company or partner; confirm)"
    plat = f" ({site['platform']})" if site["platform"] else ""
    if strong:
        return f"WEAK: {h}{plat} works but {strong[0]}{owner}"
    if gaps:
        return f"OK: {h}{plat} works, but {'; '.join(gaps[:2])}{owner}"
    return f"OK: {h}{plat} is a working site{owner}"


def weaknesses(p, site, dup_links):
    w = []
    s = site["status"]
    if s == "NONE":
        w.append("No website on the Google Maps listing, so buyers who find them there have nowhere to see products or ask for a quote")
    elif s == "SOCIAL":
        w.append(f"No website of their own: the Maps Website button opens a social page ({site['host']})")
    elif s == "THIRD_PARTY":
        w.append(f"No website of their own: the Maps link goes to {site['host']}")
    elif s in ("DEAD", "PLACEHOLDER"):
        w.append("Customers who tap Website on Google Maps land on a broken or empty page")
    elif s == "UNSURE":
        w.append("Website could not be checked automatically; open it by hand before calling")
    for k, ev in site["issues"]:
        if k in ("BAD_LINK", "NO_SSL", "NOT_MOBILE", "STALE", "JS_ONLY", "NO_FORM", "FREEMAIL"):
            w.append(ev[0].upper() + ev[1:])
    if s == "OK" and any(k == "NO_WA" for k, _ in site["issues"]):
        w.append("No WhatsApp button on the website")
    if s == "OK" and any(k == "EN_ONLY" for k, _ in site["issues"]):
        w.append("Website is English only, no Arabic")
    photos = len(p.get("photos") or [])
    listing = []
    if not photos:
        listing.append("no photos")
    if not p.get("regularOpeningHours"):
        listing.append("no opening hours")
    if not (p.get("userRatingCount") or 0):
        listing.append("no reviews")
    if listing:
        w.append("Google Maps listing has " + ", ".join(listing))
    r, n = p.get("rating"), p.get("userRatingCount") or 0
    if r and r < 4.0 and n >= 3:
        w.append(f"Low Google rating ({r:.1f} from {n} reviews)")
    elif 0 < n < 5 and photos:
        w.append(f"Very few Google reviews ({n})")
    if dup_links:
        w.append("Duplicate Google Maps listings for the same business")
    w = w[:4]
    return " ".join(f"{i}) {x}." for i, x in enumerate(w, 1)).replace(".. ", ". ") if w else ""


OFFER_CORE = {
    "construction": ("Smart Website with product list (sizes, grades) and quote form",
                     "WhatsApp order bot: material, quantity and site location in one message, plus a daily dispatch list for the trucks"),
    "food": ("Smart Website with product range and price list",
             "WhatsApp ordering for shops and distributors, with one-tap reorder and refill reminders"),
    "automotive": ("Smart Website with services and prices",
                   "WhatsApp booking and service reminders; spare-part requests by photo or part number"),
    "fabrication": ("Smart Website with project gallery and an RFQ form where clients upload drawings",
                    "WhatsApp quote assistant that collects job details and follows up"),
    "manufacturing": ("Smart Website with product catalogue, spec sheets and RFQ form, in English and Arabic",
                      "AI buyer assistant that answers spec questions 24/7 and collects orders"),
    "logistics": ("Smart Website with services and an instant quote request (route, weight, dates)",
                  "WhatsApp assistant that answers rate questions and gives shipment updates"),
    "rental": ("Smart Website with equipment list and rates",
               "WhatsApp booking bot showing availability, with booking reminders"),
    "trading": ("Smart Website with online catalogue and wholesale quote requests handed to WhatsApp",
                "Full Autopilot: automatic follow-up on quotes and unpaid invoices"),
    "services": ("Smart Website with services, past projects and a request form",
                 "WhatsApp assistant that answers enquiries and books site visits"),
    "general": ("Smart Website with products or services and an inquiry form, in English and Arabic",
                "WhatsApp assistant that answers enquiries and collects leads"),
}


def offer(p, site, sector, big, dup_links):
    if big:
        return ("Only through head office: AI assistant for buyer or supplier inquiries, "
                "or vendor-registration automation. Ask which department buys digital services.")
    site_part, auto = OFFER_CORE[sector]
    s = site["status"]
    if s in ("DEAD", "PLACEHOLDER"):
        first = f"Rebuild the website: {site_part}. Fix the link on Google Maps"
    elif s in ("SOCIAL", "THIRD_PARTY"):
        first = f"A {site_part}, with their social pages linked to it"
    elif s == "UNSURE":
        first = f"Open their site first. If it is weak: {site_part}"
    elif s == "OK":
        fixes = []
        if any(k == "BAD_LINK" for k, _ in site["issues"]):
            fixes.append("fix the broken Google Maps link")
        keys = {k for k, _ in site["issues"]}
        if "NO_FORM" in keys:
            fixes.append("RFQ/quote form")
        if "NO_WA" in keys:
            fixes.append("WhatsApp button")
        if "EN_ONLY" in keys:
            fixes.append("Arabic version")
        if "NOT_MOBILE" in keys:
            fixes.append("mobile layout")
        if "NO_SSL" in keys:
            fixes.append("secure https")
        if "JS_ONLY" in keys:
            fixes.append("search-friendly rebuild")
        if "STALE" in keys:
            fixes.append("fresh content")
        first = ("Website upgrade: " + ", ".join(fixes[:4])) if fixes else \
            "Their site is fine; lead with automation"
    else:
        first = site_part[0].upper() + site_part[1:]
    extra = []
    photos = len(p.get("photos") or [])
    if s != "OK" or not photos or not p.get("regularOpeningHours"):
        extra.append("Complete the Google Maps listing (photos, hours, website link)")
    if dup_links:
        extra.append("Merge the duplicate Google listings")
    if any(k == "FREEMAIL" for k, _ in site["issues"]):
        extra.append("Company email on their own domain")
    if (p.get("userRatingCount") or 0) < 5:
        extra.append("Automatic review requests after each order or job")
    parts = [first, auto[0].upper() + auto[1:]] + extra[:2]
    return ". ".join(parts) + "."


def spoken_name(name):
    """'Falcon Freight Connect فالكون للشحن' -> 'Falcon Freight Connect' for the call."""
    if re.search(r"[A-Za-z]{3,}", name) and ARABIC_RX.search(name):
        latin = re.sub(r"[\u0600-\u06FF]+", " ", name)
        latin = re.sub(r"\s*[|/\-–(),]+\s*$", "", re.sub(r"\s+", " ", latin)).strip(" |/-–")
        return latin or name
    return name


def opener(p, site, sector, big, zone):
    name = p.get("displayName", {}).get("text", "")
    buyers = buyers_of(sector)
    place = zone["short"]
    if big:
        return (f"Hi, we build AI assistants that answer buyer and supplier inquiries 24/7 for "
                f"companies in {place}. Could you connect me with whoever handles digital "
                f"projects or procurement?")
    r, n = p.get("rating"), p.get("userRatingCount") or 0
    photos = len(p.get("photos") or [])
    praise = ""
    if r and r >= 4.5 and n >= 5:
        praise = f"You have a strong {r:.1f} rating on Google Maps, "
    elif photos >= 10:
        praise = "Your Google Maps photos show real work, "
    greet = f"Hi, is this {spoken_name(name)}? "
    s, h = site["status"], site["host"]
    ask = "Who is the right person to talk to?"
    if s == "NONE":
        body = (f"{praise}{'but ' if praise else 'I found you on Google Maps in ' + place + ', but '}"
                f"your listing has no website, so {buyers} who find you there can't see what you "
                f"offer or ask for a quote. We build websites with WhatsApp quote requests for "
                f"companies in {place}.")
    elif s in ("DEAD", "PLACEHOLDER"):
        if "does not resolve" in site["evidence"]:
            what = f"opens {h}, which no longer exists"
        elif s == "DEAD":
            what = f"opens {h}, and it shows an error"
        else:
            what = f"opens {h}, and it's an empty placeholder page"
        body = (f"The Website button on your Google Maps listing {what}, so {buyers} who tap it "
                f"leave. We fix and rebuild websites for companies in {place}.")
        ask = "Can I speak to whoever handles sales or marketing?"
    elif s == "SOCIAL":
        body = (f"{praise}{'but ' if praise else ''}the Website button on your Google Maps listing "
                f"opens a social page, not a website, so {buyers} can't see products or send a "
                f"quote request. We build proper websites with WhatsApp quote requests.")
    elif s == "THIRD_PARTY":
        body = (f"The link on your Google Maps listing goes to {h}, not to a website of your own. "
                f"We build websites with quote requests and WhatsApp for companies in {place}.")
    elif s == "UNSURE":
        return (f"{greet}We build websites and WhatsApp quote systems for companies in {place}, "
                f"so {buyers} can send a quote request any time. Who looks after your website?")
    else:
        keys = [k for k, _ in site["issues"]]
        subject = "your website" if site["theirs"] else "the website on your Google listing"
        if "BAD_LINK" in keys:
            gap = (f"the Website button on your Google Maps listing opens a page that no longer "
                   f"exists, so {buyers} who tap it get an error")
        elif "NO_SSL" in keys:
            gap = f"{subject} shows a 'Not secure' warning in the browser"
        elif "NOT_MOBILE" in keys:
            gap = f"{subject} doesn't fit a phone screen, and most {buyers} look on their phones"
        elif "STALE" in keys:
            gap = f"{subject} still shows {site['year']}"
        elif "NO_FORM" in keys and "NO_WA" in keys:
            gap = f"{subject} has no quote form or WhatsApp button, so {buyers} have to call or email"
        elif "NO_FORM" in keys:
            gap = f"{subject} has no quote or inquiry form"
        elif "NO_WA" in keys:
            gap = f"{buyers} can't reach you on WhatsApp from {subject}"
        elif "EN_ONLY" in keys:
            gap = f"{subject} is English only"
        else:
            gap = ""
        if not gap:
            return (f"{greet}We help companies in {place} answer buyer inquiries 24/7 on WhatsApp "
                    f"and follow up every quote automatically. Who handles sales?")
        body =(f"{praise}{'but ' if praise else 'I was looking at your company, and '}{gap}. We fix that and add "
                f"automatic quote follow-up for companies in {place}.")
        ask = "Who looks after your website?"
    return greet + body[0].upper() + body[1:] + " " + ask


GENERIC_CATS = {"corporate office", "store", "company", "point of interest",
                "establishment", "business", "office"}


def what_they_do(p, site, sector, zone):
    cat = p.get("primaryTypeDisplayName", {}).get("text", "")
    base = cat if cat and cat.lower() not in GENERIC_CATS else SECTOR_LABEL[sector]
    desc = ""
    if site.get("status") == "OK" and site.get("theirs"):
        d = site.get("desc") or ""
        if (len(d) >= 40 and len(d.split()) >= 6
                and not re.search(r"lorem|just another|welcome to|description|theme|template|"
                                  r"demo|default|sample|coming soon|under construction", d, re.I)):
            desc = d if len(d) <= 110 else d[:107].rsplit(" ", 1)[0] + "..."
    s = base + (f": {desc}" if desc else "")
    return f"{s} ({zone['short']})"


def load_known_phones():
    known = set()
    if os.path.exists(FULL_LIST):
        with open(FULL_LIST, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                d = digits8(r.get("phone_e164"))
                if d:
                    known.add(d)
    return known


def cmd_audit(args):
    zones = pick_zones(args.zones)
    ok, detail = bsf.tls_self_test()
    if not ok:
        sys.exit(f"TLS self-test failed ({detail}); every https verdict would be wrong. "
                 "Fix the CA bundle first (see broken_site_finder.py).")
    print(f"TLS trust store OK ({detail}).")
    known = load_known_phones()
    today = datetime.date.today().isoformat()
    seen_ids, summary = set(), []

    for z in zones:
        path = os.path.join(args.out, "raw", f"{z['key']}.json")
        if not os.path.exists(path):
            print(f"  {z['tab']}: no sweep file yet, skipped")
            continue
        places = json.load(open(path))
        dropped, keep = {}, []
        for p in places:
            if p["id"] in seen_ids:
                dropped["filed under an earlier zone"] = dropped.get("filed under an earlier zone", 0) + 1
                continue
            seen_ids.add(p["id"])
            why = excluded_reason(p)
            if why:
                dropped[why] = dropped.get(why, 0) + 1
                continue
            keep.append(p)

        # Same phone twice in one zone = duplicate listings of one business.
        by_phone, rows_src = {}, []
        for p in sorted(keep, key=lambda p: -(p.get("userRatingCount") or 0)):
            d = digits8(phone_of(p))
            if d and d in by_phone:
                by_phone[d]["_dups"].append(p.get("googleMapsUri", ""))
                continue
            p["_dups"] = []
            if d:
                by_phone[d] = p
            rows_src.append(p)

        with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
            sites = list(ex.map(
                lambda p: audit_site(p.get("websiteUri"), p.get("displayName", {}).get("text", "")),
                rows_src))

        domain_counts = {}
        for s in sites:
            if s["host"] and s["status"] not in ("SOCIAL", "THIRD_PARTY"):
                domain_counts[s["host"]] = domain_counts.get(s["host"], 0) + 1

        rows = []
        for p, site in zip(rows_src, sites):
            name = p.get("displayName", {}).get("text", "")
            phone = phone_of(p)
            phone_from_site = False
            if not phone and site["site_phone"] and site["theirs"]:
                phone, phone_from_site = site["site_phone"], True
            sector = sector_of(p, site)
            big = is_big(p, domain_counts, site)
            dups = p["_dups"]
            if not phone:
                prio = "Skip"
            elif big:
                prio = "C"
            elif site["status"] in ("NONE", "DEAD", "PLACEHOLDER", "SOCIAL", "THIRD_PARTY"):
                prio = "A"
            elif site["status"] == "UNSURE" or site["issues"]:
                prio = "B"
            else:
                prio = "C"
            other = []
            if site["wa"] and digits8(site["wa"]) != digits8(phone):
                other.append(f"WhatsApp on website: {digits8(site['wa'])[:4]} {digits8(site['wa'])[4:]}")
            if site["emails"]:
                other.append(" · ".join(site["emails"]))
            notes = []
            if phone:
                notes.append("Mobile number: likely reaches the owner or a manager directly"
                             if is_mobile(phone) else "Landline: ask reception for sales or marketing")
            if big:
                notes.append(f"Big company: {big}")
            if p.get("businessStatus") == "CLOSED_TEMPORARILY":
                notes.append("Google marks this place TEMPORARILY CLOSED")
            if digits8(phone) in known:
                notes.append("Also in the 20k outreach list; may already have been called")
            if dups:
                notes.append("Other listing: " + " · ".join(dups[:2]))
            if phone_from_site:
                notes.append("No phone on Google Maps; this number is from their website")
            if not phone:
                notes.append("No phone on Google Maps or their website: find one another way or visit")
            rows.append({
                "_prio": prio, "_mobile": is_mobile(phone), "_n": p.get("userRatingCount") or 0,
                "row": [
                    prio, name, what_they_do(p, site, sector, z), phone, "; ".join(other),
                    website_status_text(site, name), rating_text(p),
                    weaknesses(p, site, dups), offer(p, site, sector, big, dups),
                    opener(p, site, sector, big, z) if phone else "Find a phone first.",
                    p.get("googleMapsUri", ""), f"Google Maps sweep ({today})",
                    "Not called", "", ". ".join(notes),
                ]})
        order = {"A": 0, "B": 1, "C": 2, "Skip": 3}
        rows.sort(key=lambda r: (order[r["_prio"]], not r["_mobile"], -r["_n"]))
        out_csv = os.path.join(args.out, f"{z['key']}.csv")
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(HEADER)
            for r in rows:
                w.writerow(r["row"])
        counts = {k: sum(1 for r in rows if r["_prio"] == k) for k in order}
        line = (f"{z['tab']:30} {len(rows):4} rows  A {counts['A']:3}  B {counts['B']:3}  "
                f"C {counts['C']:3}  Skip {counts['Skip']:3}   dropped {sum(dropped.values())}: "
                + ", ".join(f"{k} {v}" for k, v in sorted(dropped.items(), key=lambda kv: -kv[1])))
        print("  " + line)
        summary.append(line)

    with open(os.path.join(args.out, "SUMMARY.txt"), "w") as f:
        f.write(f"zone_sweep.py audit, {today}\n\n" + "\n".join(summary) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=["plan", "sweep", "audit"])
    ap.add_argument("--zones", default="all", help="comma-separated zone keys (default all)")
    ap.add_argument("--out", default=OUT_DIR)
    ap.add_argument("--max-calls", type=int, default=900,
                    help="hard stop on billed Text Search calls this run (default 900)")
    ap.add_argument("--max-depth", type=int, default=3,
                    help="how many times a saturated box may be split in four")
    ap.add_argument("--workers", type=int, default=8, help="parallel website checks")
    args = ap.parse_args()
    {"plan": cmd_plan, "sweep": cmd_sweep, "audit": cmd_audit}[args.stage](args)


if __name__ == "__main__":
    main()
