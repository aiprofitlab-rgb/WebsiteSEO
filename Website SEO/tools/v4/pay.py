#!/usr/bin/env python3
"""
The commerce layer for the v4 set.

This module is the ONLY place that knows what is sold, what it costs, which
payment structures exist, and whether the card gateway is switched on. The
checkout page, the order-status page and the honesty of the copy on the
services and contact pages all read from here, and the same table is shipped
to the browser as JSON (CONFIG_JSON) rather than retyped in JavaScript - the
arithmetic exists once, in Python, and is transported.

Two rules this file exists to enforce:

1. MONEY IS INTEGER BAISA, EVERYWHERE. 1 OMR = 1000 baisa. Thawani's
   `unit_amount` is an integer number of baisa and rejects decimals, and float
   arithmetic on prices is how a checkout ends up showing OMR 949.9999998.
   Nothing in this module or the page's script ever holds a price as a float.

2. NOTHING CLAIMS A CARD IS TAKEN UNTIL ONE ACTUALLY CAN BE. `PAY_LIVE` is
   False until Thawani approves the merchant account, and every piece of user
   facing copy that mentions how to pay branches on it. Flipping one boolean
   turns the site from "bank transfer, invoice to follow" to "pay by card now"
   in the checkout, the services page and the contact FAQ at once.

Prices are the ones published on services-v4 and quoted in the contact FAQ.
build_v4.py asserts at build time that every figure below still appears in the
rendered services page, so the two cannot drift apart silently - see
check_services().
"""
import json

# ---------------------------------------------------------------------------
# The switch. Everything downstream branches on these three values.
# ---------------------------------------------------------------------------

# Flip to True on the day the Thawani merchant account is approved AND the
# checkout API is deployed with live keys. Flipping it alone is not enough:
# PAY_API must point at a running service, or the page falls back anyway.
PAY_LIVE = False

# Base URL of the checkout API that creates Thawani sessions - no trailing
# slash. Empty means "not deployed yet", and the checkout uses its offline
# path: it collects the order, shows the reference, and hands it to WhatsApp.
# The contract this URL must satisfy is written down in docs/payments-api.md.
PAY_API = ""

# "uat" while testing against uatcheckout.thawani.om, "live" against
# checkout.thawani.om. The front end never talks to Thawani directly - the
# secret key cannot touch a browser - so this is here for the banner that
# tells a tester which environment they are looking at.
THAWANI_ENV = "uat"

OMR = 1000          # baisa per rial
CURRENCY = "OMR"

# ---------------------------------------------------------------------------
# What is sold.
#
# `price` is the published figure, in baisa - one column, no comparison. `kind`
# separates a one-time build item from a monthly service, because a monthly
# service is NOT charged at checkout: Thawani's e-commerce checkout takes a
# single payment, and recurring billing needs card-on-file, which the
# E-commerce + Payment-link application does not cover. The Growth Desk is
# therefore recorded on the order and invoiced monthly from go-live.
# ---------------------------------------------------------------------------
BASE_ID = "website"

CATALOG = [
    {
        "id": BASE_ID, "kind": "build", "required": True,
        "name": "The Smart Website",
        "name_ar": "الموقع الذكي",
        "blurb": "Bilingual site, AI buyer agent, wholesale quote flow, WhatsApp handoff, "
                 "AI-search visibility, and the first year of hosting and care.",
        "blurb_ar": "موقع بلغتين، ووكيل مشترٍ بالذكاء الاصطناعي، ومسار عرض سعر بالجملة، وتحويل إلى واتساب، وظهور في بحث الذكاء الاصطناعي، والسنة الأولى من الاستضافة والرعاية.",
        "price": 950 * OMR,
    },
    {
        "id": "dashboard", "kind": "build", "required": False,
        "name": "The Live Owner Dashboard",
        "name_ar": "لوحة متابعة المالك الحيّة",
        "blurb": "Cash position, margin, stock and open leads on one screen, each with the "
                 "action it is asking for.",
        "blurb_ar": "السيولة والهامش والمخزون والطلبات المفتوحة على شاشة واحدة، ومع كل بند الإجراء الذي يطلبه.",
        "price": 650 * OMR,
    },
    {
        "id": "autopilot", "kind": "build", "required": False,
        "name": "The Full Autopilot",
        "name_ar": "الطيار الآلي الكامل",
        "blurb": "Quote and invoice follow-up on a schedule, stopping the moment the buyer "
                 "replies or pays.",
        "blurb_ar": "متابعة عروض الأسعار والفواتير وفق جدول، وتتوقف فور أن يردّ المشتري أو يدفع.",
        "price": 900 * OMR,
    },
    {
        "id": "desk", "kind": "monthly", "required": False,
        "name": "The Growth Desk",
        "name_ar": "مكتب النمو",
        "blurb": "Optional monthly care, new features and a reporting review. Never required "
                 "to keep anything working, and cancellable any month.",
        "blurb_ar": "رعاية شهرية اختيارية، وميزات جديدة، ومراجعة للتقارير. غير مطلوبة أبداً لإبقاء أي شيء يعمل، وتُلغى في أي شهر.",
        "price": 75 * OMR,
    },
    # -----------------------------------------------------------------------
    # The one thing in this table sold at TWO figures, and the only row where
    # the price a page prints is not the price this dict calls `price`.
    #
    #   rack  = 300  the published rate. This is what the services page shows,
    #                what a walk-in pays, and what anyone who declines the
    #                interstitial and asks for it in March pays.
    #   price =  97  the interstitial's offer, available in one window only:
    #                after "pay" is pressed and before the card page, on the
    #                first order. It is what the checkout actually charges.
    #
    # Two flags keep those apart, and they mean different things:
    #
    #   `listed: False`   -> not a checkbox on the checkout. The interstitial
    #                        is the only way to buy it there, at the offer
    #                        price; a checkbox beside it would sell the same
    #                        service twice in one page at two figures.
    #   `published: True` -> IS on the public price list - at `rack`, never at
    #                        `price`. Added 2026-09-01: the interstitial says
    #                        "the published rate for the same work is OMR 300
    #                        a month", and a rate published nowhere is not a
    #                        published rate. Listing it at 300 is what makes
    #                        that sentence true.
    #
    # The line that must never appear on a public page is 97, not 300 -
    # check_services() asserts exactly that, in both directions. If Nahid ever
    # does sell this at 97 to a walk-in, then 300 stops being the real rate
    # and BOTH the services page and the interstitial have to change together.
    #
    # `guarantee_months` drives the guarantee wording on four surfaces now, in
    # both languages: the two checkout interstitials AND the two services
    # pages. Nahid confirmed 2026-09-01 that the guarantee travels with the
    # rack rate - it is not exclusive to the interstitial offer - so the public
    # page states it in full. Every one of those surfaces reads this field
    # rather than typing a number, because a guarantee that says six months in
    # one place and three in another is worse than no guarantee at all.
    #
    # What the promise is, exactly, and what it must never be allowed to imply,
    # is written above UPSELL in page_checkout.py. Read it before editing the
    # wording anywhere: the refund is of THIS SERVICE'S fees, never the build,
    # and "visible" is defined in writing in month one.
    # -----------------------------------------------------------------------
    {
        "id": "visibility", "kind": "monthly", "required": False,
        "listed": False, "published": True,
        "name": "The Visibility Desk",
        "name_ar": "مكتب الظهور",
        "blurb": "The daily work of staying named by Google and by the AI assistants "
                 "buyers now ask first.",
        "blurb_ar": "العمل اليومي لإبقاء اسمك حاضراً في جوجل وفي مساعدي الذكاء الاصطناعي الذين صار المشترون يسألونهم أولاً.",
        "price": 97 * OMR,
        "rack": 300 * OMR,
        "guarantee_months": 6,
    },
]

# The id of the row above. Everything that renders the interstitial asks for it
# by this name rather than by the string, so it can be renamed in one place.
UPSELL_ID = "visibility"


def listed(i):
    """Is this item a line the buyer can tick for himself on the checkout?
    Absent means yes - the exception is the thing that has to be declared, not
    the rule."""
    return i.get("listed", True)


def list_price(i):
    """What the public price list shows for this item, in baisa, or None if it
    is not on the list at all.

    For every row but one this is simply `price`. The Visibility Desk is
    published at its rack rate and sold on the checkout interstitial at a
    lower one, so `rack` wins wherever it exists - the page prints the rate
    anyone can buy at, never the rate that is only reachable through the
    interstitial. `published` defaults to `listed`, because for everything
    else the two questions have the same answer."""
    if not i.get("published", listed(i)):
        return None
    return i.get("rack") or price(i)

# All three build items together are sold as one thing at a lower price than
# the sum of its parts. `saving` is not stored - it is derived, so it cannot
# disagree with the numbers above.
BUNDLE = {
    "id": "stack",
    "name": "The Operator Stack",
    "name_ar": "حزمة المشغّل",
    "requires": ["dashboard", "autopilot"],
    "price": 2200 * OMR,
}

# ---------------------------------------------------------------------------
# How it can be paid for.
#
# `surcharge` and `due` are what turn the published headline figures into
# arithmetic that generalises past the Smart Website on its own:
#
#   full     950            -> the published "Pay on Start" price
#   three    950 + 70 = 1020 -> the published "3 x OMR 340"
#   proof    950 + 200 = 1150 -> the published "Pay on Proof" price
#
# The two surcharges are flat, not percentages, because a flat figure is the
# only reading that reproduces all three published numbers exactly. On a
# larger order a flat surcharge is the generous reading, deliberately.
# ASSUMPTION, FLAGGED TO NAHID: the services page only ever published these
# three structures against the Smart Website alone. If he wants the premium
# to scale with the order instead, it changes here and nowhere else.
# ---------------------------------------------------------------------------
PLANS = [
    {
        "id": "deposit", "card": True, "recommended": True,
        "label": "Reserve a build slot",
        "label_ar": "احجز موعد بناء",
        "badge": "Most owners start here",
        "badge_ar": "أكثر ما يبدأ به أصحاب الأعمال",
        "due": "deposit", "surcharge": 0, "split": 1,
        "blurb": "OMR 100 today holds your slot in the build queue and comes straight off "
                 "your price. The balance is invoiced once your brief is confirmed.",
        "blurb_ar": "‏100 ر.ع. اليوم تحفظ لك مكانك في دور البناء وتُخصم مباشرةً من سعرك. والمتبقي يُفوتر بعد تأكيد ملخّص طلبك.",
    },
    {
        "id": "full", "card": True, "recommended": False,
        "label": "Pay in full",
        "label_ar": "ادفع المبلغ كاملاً",
        "badge": "Three extras included",
        "badge_ar": "ثلاث إضافات مشمولة",
        "due": "total", "surcharge": 0, "split": 1,
        "blurb": "The whole build paid now. This is the Pay on Start price, and it carries "
                 "the Arabic content pass, the Google Business Profile fix and one staff "
                 "training session at no charge.",
        "blurb_ar": "البناء كاملاً مدفوعاً الآن. هذا هو سعر الدفع عند البدء، ويشمل مجاناً تحرير المحتوى العربي، وضبط ملفّك في نشاطي التجاري على جوجل، وجلسة تدريب واحدة للفريق.",
    },
    {
        "id": "three", "card": True, "recommended": False,
        "label": "Three payments",
        "label_ar": "ثلاث دفعات",
        "badge": "Spread it out",
        "badge_ar": "وزّعها على مراحل",
        "due": "first", "surcharge": 70 * OMR, "split": 3,
        "blurb": "On signing, on go-live, and thirty days later. Paying in three adds "
                 "OMR 70 to the total.",
        "blurb_ar": "عند التوقيع، وعند الإطلاق، وبعد ثلاثين يوماً. والدفع على ثلاث دفعات يضيف 70 ر.ع. إلى الإجمالي.",
    },
    {
        "id": "proof", "card": False, "recommended": False,
        "label": "Pay on Proof",
        "label_ar": "ادفع عند الإثبات",
        "badge": "Nothing until it works",
        "badge_ar": "لا شيء حتى ينجح",
        "due": "zero", "surcharge": 200 * OMR, "split": 1,
        "blurb": "Nothing today, and nothing when it goes live. You are invoiced only after "
                 "your site has produced its first real, verifiable buyer inquiry. If it "
                 "never does, you never pay. Pay on Proof adds OMR 200 to the total.",
        "blurb_ar": "لا شيء اليوم، ولا شيء عند الإطلاق. تُفوتر فقط بعد أن ينتج موقعك أول استفسار حقيقي وقابل للتحقق من مشترٍ. وإن لم ينتجه أبداً، فلن تدفع أبداً. والدفع عند الإثبات يضيف 200 ر.ع. إلى الإجمالي.",
    },
]

DEPOSIT = 100 * OMR

# Thawani truncates a product name at 40 characters. Building the line items
# server-side does not remove the constraint - the names come from CATALOG, so
# they are checked here, at build time, where a rename is caught immediately.
THAWANI_NAME_MAX = 40


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def price(item):
    """The published price of a catalog item or the bundle, in baisa."""
    return item["price"]


def omr(baisa):
    """Format baisa as an OMR figure. Whole rials stay whole; a remainder gets
    three decimals, because baisa are thousandths and 0.5 OMR is 0.500."""
    whole, rem = divmod(int(baisa), OMR)
    s = f"{whole:,}"
    if rem:
        s += f".{rem:03d}"
    return s


def money(baisa):
    return f"{CURRENCY} {omr(baisa)}"


# The Arabic pages never hand-type a figure: they call this, so the price table
# and the checkout cannot drift the way the English table can. The numeral is
# wrapped and forced LTR because an Arabic paragraph otherwise renders
# "1,450" with the comma group reversed.
CURRENCY_AR = "ر.ع."
MONTHLY_AR = "شهرياً"


def money_ar(baisa):
    return f'<span class="num" dir="ltr">{omr(baisa)}</span> {CURRENCY_AR}'


def bundle_saving():
    """What the Operator Stack saves against buying the three separately."""
    parts = sum(price(i) for i in CATALOG
                if i["kind"] == "build" and (i["id"] == BASE_ID or i["id"] in BUNDLE["requires"]))
    return parts - price(BUNDLE)


def item(item_id):
    for i in CATALOG:
        if i["id"] == item_id:
            return i
    raise KeyError(item_id)


def plan(plan_id):
    for p in PLANS:
        if p["id"] == plan_id:
            return p
    raise KeyError(plan_id)


# ---------------------------------------------------------------------------
# What the browser gets.
#
# The page's script recomputes totals live as the buyer toggles things, so it
# needs the same table. It is serialised rather than restated: a price edited
# above changes the rendered markup AND the script in the same build.
# ---------------------------------------------------------------------------
def t(entry, field, lang="en"):
    """A catalogue string in one language. Arabic falls back to the English if
    a translation has not been written yet, which is what keeps a newly added
    product from rendering as an empty label on the Arabic checkout."""
    if lang == "ar":
        return entry.get(field + "_ar") or entry[field]
    return entry[field]


def config(lang="en"):
    return {
        "currency": CURRENCY,
        "baisa": OMR,
        "live": PAY_LIVE,
        "api": PAY_API,
        "env": THAWANI_ENV,
        "deposit": DEPOSIT,
        "base": BASE_ID,
        "items": [
            {"id": i["id"], "kind": i["kind"], "name": t(i, "name", lang),
             "required": i["required"], "price": price(i)}
            for i in CATALOG
        ],
        "bundle": {"id": BUNDLE["id"], "name": t(BUNDLE, "name", lang),
                   "requires": BUNDLE["requires"],
                   "price": price(BUNDLE), "saving": bundle_saving()},
        # The upsell is already in `items` above - the server prices it from
        # there like any other monthly line. This block is the extra it needs
        # to be SOLD: the struck-through rate and the length of the guarantee,
        # which no other item has. Shipped separately so `items` keeps one
        # shape for every row.
        "upsell": {
            "id": UPSELL_ID,
            "name": t(item(UPSELL_ID), "name", lang),
            "price": price(item(UPSELL_ID)),
            "rack": item(UPSELL_ID)["rack"],
            "months": item(UPSELL_ID)["guarantee_months"],
            # The row the interstitial stands down for. A buyer who already
            # took monthly care is not asked to buy a second monthly plan in
            # the same breath.
            "skip_if": "desk",
        },
        "plans": [
            {"id": p["id"], "label": t(p, "label", lang), "card": p["card"], "due": p["due"],
             "surcharge": p["surcharge"], "split": p["split"]}
            for p in PLANS
        ],
    }


def CONFIG_JSON(lang="en"):
    return json.dumps(config(lang), separators=(",", ":"))


# ---------------------------------------------------------------------------
# Anti-drift check, run from build_v4.py after services-v4.html is written.
#
# The services page holds its price table as hand-written markup. That is fine
# - it is a page of prose, not a spreadsheet - but it means two copies of every
# figure exist. Rather than rewrite that page, the build asserts the copies
# agree: every live price in this module must still appear, formatted, in the
# rendered services page. Change a price here and forget the table, and the
# build fails with the figure that no longer matches.
# ---------------------------------------------------------------------------
def check_services(html, lang="en"):
    """Return a list of human-readable problems; empty means consistent.

    `lang` picks how a figure is written on the page under test. English writes
    "OMR 950" as literal text in a hand-authored table; Arabic writes the
    fragment money_ar() emits. Both are checked the same way, so an Arabic
    price cannot quietly fall behind a change in this module either."""
    ar = lang == "ar"
    fmt = money_ar if ar else money
    monthly_suffix = f"/{MONTHLY_AR}" if ar else "/mo"
    page = "services-ar" if ar else "services-v4"
    problems = []

    for i in CATALOG:
        # An unpublished item is deliberately absent from the price table -
        # see the note on `published` in CATALOG. Asserting it were present
        # would force a private figure onto the public page.
        shown = list_price(i)
        if shown is None:
            continue
        # `list_price`, not `price`: the Visibility Desk publishes its rack
        # rate. Checking `price` here would demand the offer figure appear on
        # the page, which is the exact thing the loop below forbids.
        #
        # The table writes add-ons as "+OMR 650" and the base as "OMR 950";
        # both contain "OMR 650" / "OMR 950", so one needle covers both.
        needle = fmt(shown)
        if i["kind"] == "monthly":
            needle += monthly_suffix
        if needle not in html:
            problems.append(f"{i['name']}: {page} does not contain {needle!r}")

    if fmt(price(BUNDLE)) not in html:
        problems.append(f"{BUNDLE['name']}: {page} does not contain "
                        f"{fmt(price(BUNDLE))!r}")

    # The three published payment structures, as the page writes them.
    base = price(item(BASE_ID))
    for pid, shown in (("full", fmt(base)),
                       ("proof", fmt(base + plan("proof")["surcharge"]))):
        if shown not in html:
            problems.append(f"payment structure {pid!r}: {page} does not contain {shown!r}")

    three = base + plan("three")["surcharge"]
    per = three // 3
    if per * 3 != three:
        problems.append(f"three-payment total {omr(three)} does not divide into 3 whole payments")
    elif fmt(per) not in html:
        problems.append(f"payment structure 'three': {page} does not contain "
                        f"{fmt(per)!r} (3 x)")

    # ...and the inverse. A private price appearing on the public page is a
    # worse failure than a published one going missing: it does not break a
    # build or look wrong, it just quietly turns "only on this page" into a
    # false statement while every test still passes.
    #
    # The needle is the OFFER figure - the price a page is not allowed to
    # print - and it is checked for every row whose published figure differs
    # from it, which today means the Visibility Desk (97 forbidden, 300
    # required above) and would also catch any future unpublished row.
    #
    # `rack` itself is never asserted absent: the bundle saving is also
    # OMR 300 and legitimately appears in that table, so that check would fail
    # on a page that is perfectly correct.
    for i in CATALOG:
        if list_price(i) == price(i):
            continue
        leaked = fmt(price(i))
        if leaked in html:
            problems.append(
                f"{i['name']}: {leaked!r} is the checkout-interstitial price and it "
                f"appears on {page}, which publishes {fmt(list_price(i))!r} if anything. "
                f"Printing it there contradicts the 'only on this page' claim.")

    for i in CATALOG:
        if len(i["name"]) > THAWANI_NAME_MAX:
            problems.append(f"{i['name']!r} is {len(i['name'])} chars; Thawani truncates a "
                            f"product name at {THAWANI_NAME_MAX}")

    return problems


# ---------------------------------------------------------------------------
# The quote.
#
# This is the arithmetic the checkout runs. It lives here so that the page can
# render a CORRECT static default for a visitor with no JavaScript, and so the
# published figures can be asserted at build time. The page's script is a
# direct port of this function - if you change a rule here, change it there
# too, and `python3 tools/v4/pay.py` will tell you if the published numbers
# stopped coming out.
# ---------------------------------------------------------------------------
def quote(item_ids, plan_id):
    p = plan(plan_id)
    chosen = [i for i in CATALOG if i["id"] in item_ids or i["required"]]
    build = [i for i in chosen if i["kind"] == "build"]
    monthly = [i for i in chosen if i["kind"] == "monthly"]

    parts = sum(price(i) for i in build)
    bundled = all(r in {i["id"] for i in build} for r in BUNDLE["requires"])
    subtotal = price(BUNDLE) if bundled else parts
    saving = parts - subtotal

    total = subtotal + p["surcharge"]

    if p["due"] == "deposit":
        due = min(DEPOSIT, total)
    elif p["due"] == "total":
        due = total
    elif p["due"] == "first":
        # Whole-rial instalments, with the rounding remainder carried by the
        # FIRST payment. Paying the odd baisa up front means the two later
        # invoices are identical, which is the pair the buyer has to remember.
        per = (total // p["split"]) // OMR * OMR
        due = total - per * (p["split"] - 1)
    else:
        due = 0

    return {
        "items": build, "monthly": monthly, "bundled": bundled,
        "parts": parts, "subtotal": subtotal, "saving": saving,
        "surcharge": p["surcharge"], "total": total,
        "due": due, "balance": total - due,
        "later": (total - due) // (p["split"] - 1) if p["split"] > 1 else 0,
        "plan": p,
    }


if __name__ == "__main__":
    # Every figure the services page publishes, recomputed from the table
    # above. Run this after touching a price.
    base = [BASE_ID]
    checks = [
        ("Smart Website, paid in full", quote(base, "full")["total"], 950 * OMR),
        ("Smart Website, pay on proof", quote(base, "proof")["total"], 1150 * OMR),
        ("Smart Website, three payments", quote(base, "three")["total"], 1020 * OMR),
        ("  ... first payment", quote(base, "three")["due"], 340 * OMR),
        ("  ... each later payment", quote(base, "three")["later"], 340 * OMR),
        ("Smart Website, deposit today", quote(base, "deposit")["due"], 100 * OMR),
        ("  ... balance", quote(base, "deposit")["balance"], 850 * OMR),
        ("Operator Stack, paid in full", quote([BASE_ID, "dashboard", "autopilot"], "full")["total"],
         2200 * OMR),
        ("  ... saving against the parts",
         quote([BASE_ID, "dashboard", "autopilot"], "full")["saving"], 300 * OMR),
    ]
    bad = 0
    for label, got, want in checks:
        ok = got == want
        bad += not ok
        print(f"  {'ok ' if ok else 'BAD'} {label:38s} {money(got):>12s}"
              + ("" if ok else f"   expected {money(want)}"))
    stack3 = quote([BASE_ID, "dashboard", "autopilot"], "three")
    print(f"\n  Operator Stack in three: {money(stack3['due'])} today, "
          f"then 2 x {money(stack3['later'])}  (total {money(stack3['total'])})")
    assert stack3["due"] + stack3["later"] * 2 == stack3["total"], "instalments do not sum to the total"
    raise SystemExit(bad)
