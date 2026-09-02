#!/usr/bin/env python3
"""
Shared Arabic vocabulary and helpers for the Arabic v4 pages.

Two jobs:

  * ONE name per thing. A product called "الموقع الذكي" on the home page and
    "موقع ذكي" on the services page is two products as far as a reader is
    concerned, and the price table stops matching the cards. Every page imports
    the names from here rather than typing them, so a rename is one edit.

  * ONE way to write a WhatsApp link. The prefilled text has to be
    percent-encoded, and hand-encoded Arabic is where this kind of page rots
    first - a single unencoded character silently truncates the message.

Naming decisions worth keeping: the systems keep an Arabic name rather than a
transliteration, because the whole point of the voice is that nothing on the
page is in software vocabulary. "AI Profit Lab" itself stays Latin - it is the
registered brand and the wordmark is Latin.
"""
import urllib.parse

from kit import WA

# --------------------------------------------------------------------------
# Product and offer names. Also used by the schema blocks, so a rename here
# reaches the structured data too.
# --------------------------------------------------------------------------
SITE = "الموقع الذكي"
DASH = "لوحة متابعة المالك الحيّة"
AUTO = "الطيار الآلي الكامل"
STACK = "حزمة المشغّل"
DESK = "مكتب النمو"
VIS = "مكتب الظهور"
TEST = "اختبار المشتري الصامت"
PROMISE = "وعد أول استفسار"

PLAN_PROOF = "ادفع عند الإثبات"
PLAN_FULL = "ادفع عند البدء"
PLAN_THREE = "ثلاث دفعات"

FOUNDER = "ناهد آبياري"
ROLE = "المؤسس"
CITY = "مسقط، سلطنة عُمان"

# Recurring phrases that must read identically wherever they appear.
ONE_TIME = "دفعة واحدة"
ADDON = "إضافة"
FREE = "مجاناً"


def wa(text):
    """A WhatsApp deep link with an Arabic prefilled message, encoded once.

    `safe=""` matters: urlencode's default leaves "/" alone, and a slash inside
    the text argument ends the message early on some WhatsApp clients."""
    return f"{WA}&text={urllib.parse.quote(text, safe='')}"


def num(s):
    """Wrap a Latin figure so it survives inside an Arabic paragraph.

    Arabic is RTL, so an unmarked "OMR 1,450" or "9:47 PM" has its parts
    reordered by the bidi algorithm and comes out backwards. Everything that is
    a figure, a time, a phone number or a code goes through here."""
    return f'<span class="num" dir="ltr">{s}</span>'


# --------------------------------------------------------------------------
# Prices. Every figure an Arabic page shows is derived from tools/v4/pay.py
# through these, never typed. The English services page still hand-writes its
# table (and is checked against pay.py at build time); the Arabic side skips
# that risk entirely by computing the markup.
# --------------------------------------------------------------------------
import pay  # noqa: E402


def price_ar(item_id):
    """The formatted figure this item is PUBLISHED at.

    pay.list_price(), never pay.price(): the Visibility Desk is published at
    its rack rate and sold on the checkout interstitial at a lower one, so the
    two are genuinely different numbers and an Arabic page must print the
    published one. An item with no published figure raises instead of falling
    back - a page asking for a price it is not allowed to show is a bug, and
    silently printing the private figure is the exact failure the build's
    leak check exists to catch."""
    shown = pay.list_price(pay.item(item_id))
    if shown is None:
        raise ValueError(f"{item_id!r} has no published price and must not be "
                         f"printed on a page")
    return pay.money_ar(shown)


def bundle_ar():
    return pay.money_ar(pay.price(pay.BUNDLE))


def plan_total_ar(plan_id):
    """The published headline for one payment structure, against the base build
    on its own - which is the only basis the three figures were ever quoted
    on. See the note above PLANS in pay.py."""
    base = pay.price(pay.item(pay.BASE_ID))
    return pay.money_ar(base + pay.plan(plan_id)["surcharge"])


def plan_instalment_ar(plan_id):
    base = pay.price(pay.item(pay.BASE_ID))
    p = pay.plan(plan_id)
    return pay.money_ar((base + p["surcharge"]) // p["split"])
