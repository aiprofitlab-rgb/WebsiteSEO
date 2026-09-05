#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build the Arabic seat-claim page.

    python3 tools/build_pay_ar.py
    python3 tools/build_pay_ar.py --check     # fail if the file on disk is stale

    public_html/en/pay.html   ->   public_html/pay-ar.html
              /en/pay/                      /pay-ar/

WHY THIS IS A SUBSTITUTION AND NOT A REWRITE
--------------------------------------------
Every other Arabic page in this repo is written out whole in Arabic and only
borrows the English page's stylesheet (see build_smart_storefront_ar.py). This
one is not, and the reason is that this page moves money.

Its script opens Thawani sessions, polls a gateway for confirmation, decides
whether to say "paid", and uploads receipts. Two hand-maintained copies of that
logic is two chances to fix a payment bug in one language and not the other -
and the language it would go unfixed in is the one its author cannot read. So
the page's STRUCTURE and its SCRIPT are carried over byte for byte, and only
the strings are swapped.

That trade has a price, and the price is paid here: every English sentence
below has to be found in the source, exactly, or the build stops. A reworded
line in pay.html breaks this script the next time it runs, which is the point -
a reworded English line needs an Arabic decision, and the alternative to a hard
failure is an Arabic page that silently keeps the old sentence.

WHERE THE ARABIC COMES FROM
---------------------------
tools/pay_ar_strings.py, which records the provenance of every string: lifted
from Arabic a native reader has already reviewed, or newly written and awaiting
a pass. Nothing is translated in this file.

THE UPSELL IS NOT TRANSLATED HERE EITHER
----------------------------------------
The Visibility Desk interstitial carries a refund guarantee and a price, and it
belongs to tools/apply_upsell.py, which renders it from tools/v4/pay.py in
either language. The five fenced regions are emptied before substitution and
refilled in Arabic at the end, so no English promise can survive into the
Arabic page and no price can be typed twice.

ORDER OF OPERATIONS. Each step depends on the one before it:

    1. empty the upsell fences        so step 3 never sees English it does not own
    2. head, links, and the script's
       own bilingual seams            code-level edits, asserted one by one
    3. copy substitution              longest English first, so a sentence is
                                      never eaten by its own opening clause
    4. leftover scan                  proves no English sentence survived
    5. refill the fences in Arabic    apply_upsell.apply(html, "ar")
    6. append the RTL layer           last, so it wins on a specificity tie
"""
import hashlib
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "v4"))

import pay_ar_strings as S      # noqa: E402
import apply_upsell             # noqa: E402
import aiden_version            # noqa: E402

SRC = ROOT / "public_html" / "en" / "pay.html"
OUT = ROOT / "public_html" / "pay-ar.html"


# ═══════════════════════════════════════════════════════════════════════════
# 1. The seams. Code, not copy - so none of it comes from the strings table.
#
# Every pair is asserted to appear exactly once. That is what makes this file
# safe to leave alone for six months: it cannot half-apply.
# ═══════════════════════════════════════════════════════════════════════════
def seams():
    d = dict(S.ALL_BY_KEY)

    def split(key, *marks):
        """An Arabic string written with {placeholders}, cut at them.

        The English page builds these by concatenation - "Pay " + money() +
        " by card" - so the Arabic has to be cut the same way rather than
        formatted, and the cut has to survive Arabic putting the pieces in a
        different order than English does."""
        ar = d[key]
        for m in marks:
            if "{" + m + "}" not in ar:
                raise SystemExit(f"{key}: Arabic is missing the {{{m}}} placeholder")
        pattern = "|".join(re.escape("{" + m + "}") for m in marks)
        return re.split(pattern, ar)

    def concat(head, expr, tail, isolate=False):
        """head + expr + tail, as JavaScript, with the empty pieces left out.

        Arabic often ends on the value where English carries on past it, and
        `"..." + x + ""` in generated code is the kind of dangling artefact
        that gets "tidied up" by hand six months later, at which point the file
        is no longer generated."""
        if isolate:
            head, tail = head + "\\u2066", "\\u2069" + tail
        parts = [f'"{head}"' if head else None, expr, f'"{tail}"' if tail else None]
        return " + ".join(x for x in parts if x)

    pay_a, pay_z = split("pay_by_card", "amount")
    inv_a, inv_z = split("invoice_no", "no")
    wa_seat_a, wa_seat_z = split("wa_about_seat", "ref")
    wa_paid_a, wa_paid_z = split("wa_paid_unconfirmed", "ref")

    return [
        # ---- the document, and which way it reads --------------------------
        ('<html lang="en" dir="ltr">',
         '<html dir="rtl" lang="ar">'),

        # Markazi Text and IBM Plex Sans Arabic join the request rather than
        # replacing the Latin faces: the wordmark, the reference code and every
        # figure on the page are still Latin and still want IBM Plex Mono.
        ("family=Marcellus&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500",
         "family=Markazi+Text:wght@400;500;600&family=IBM+Plex+Sans+Arabic:wght@400;500;600"
         "&family=IBM+Plex+Mono:wght@400;500"),

        # ---- where the page points ----------------------------------------
        ('<a class="brand" href="/en/smart-storefront/">',
         '<a class="brand" href="/smart-storefront-ar/">'),
        ('<a href="/en/smart-storefront/">', '<a href="/smart-storefront-ar/">'),
        ('<a href="/terms/">', '<a href="/terms-ar/">'),
        ('<a href="/refund-policy/">', '<a href="/refund-policy-ar/">'),
        ('<a href="/privacy/">', '<a href="/privacy-ar/">'),

        # ---- money, inside an RTL paragraph -------------------------------
        # money() writes straight into textContent, so there is no <span> to
        # hang `dir="ltr"` on the way pay.money_ar() does in rendered markup.
        # U+2066 LEFT-TO-RIGHT ISOLATE and U+2069 POP DIRECTIONAL ISOLATE do
        # the same job in a bare string: without them "950.00 ر.ع." is
        # reordered by the bidi algorithm and the buyer is shown a price with
        # its parts in the wrong places.
        ('  var money = function(n){ return n == null ? "—" : "OMR " + Number(n).toFixed(2); };',
         '  /* U+2066/U+2069 isolate the figure so Arabic running text cannot\n'
         '     reorder it. Same reading order as pay.money_ar() renders in\n'
         '     markup: the number first, then the currency after it. */\n'
         '  var money = function(n){ return n == null ? "—" : '
         '"\\u2066" + Number(n).toFixed(2) + "\\u2069 ر.ع."; };'),

        ('$("rebate").textContent = money(data.rebate) + " (" + data.pledgePct + "%)";',
         '$("rebate").textContent = money(data.rebate) + " (\\u2066" + data.pledgePct + "%\\u2069)";'),

        # ---- strings the script builds by concatenation --------------------
        ('$("payBtn").textContent = "Pay " + money(data.deposit) + " by card";',
         '$("payBtn").textContent = '
         + concat(pay_a, 'money(data.deposit)', pay_z) + ';'),

        # The invoice number is Latin and sits at the end of an Arabic line,
        # so it gets the same isolate pair the figures get. `js()` below drops
        # the trailing concatenation when the Arabic ends on the placeholder.
        ('$("doneInv").textContent = "Invoice " + data.invoiceNo;',
         '$("doneInv").textContent = '
         + concat(inv_a, 'data.invoiceNo', inv_z, isolate=True) + ';'),

        ('encodeURIComponent("Hello — about my Smart Website seat, reference " + data.ref + ".")',
         'encodeURIComponent(' + concat(wa_seat_a, 'data.ref', wa_seat_z) + ')'),

        ('encodeURIComponent("Hello — I paid for seat " + ref + " but the page hasn\'t confirmed it.")',
         'encodeURIComponent(' + concat(wa_paid_a, 'ref', wa_paid_z) + ')'),

        ('>message me</a> and I\\\'ll sort it in minutes.',
         f'>{d["unconfirmed_link"]}</a>{d["unconfirmed_tail"]}'),
    ]


# ═══════════════════════════════════════════════════════════════════════════
# 2. Copy. Everything that is a whole English string in the source and a whole
#    Arabic string in the table.
#
# The keys below are handled by seams() instead - as fragments of a
# concatenation, or by apply_upsell in its own language.
# ═══════════════════════════════════════════════════════════════════════════
BY_SEAM = {
    "pay_by_card", "invoice_no", "wa_about_seat", "wa_paid_unconfirmed",
    "unconfirmed_link", "unconfirmed_tail",
}
BY_UPSELL = {k for k, _, _, _ in S.UPSELL} | {"wa_upsell_booked"}

# Source spellings. The page writes some of these with entities or with a
# non-breaking space, and the table stores the sentence a reader reads. The
# difference is typography, not copy, so it is reconciled here rather than by
# putting markup into a translation table.
AS_WRITTEN = {
    "Up to 5 MB.": "Up to 5&nbsp;MB.",
}


def copy_pairs():
    pairs = []
    seen = set()
    for k, en, ar, _src in S.ALL:
        if k in BY_SEAM or k in BY_UPSELL:
            continue
        en = AS_WRITTEN.get(en, en)
        for frag, repl in AS_WRITTEN.items():          # entities inside a longer line
            en = en.replace(frag, repl) if frag in en else en
        if en in seen:
            continue
        seen.add(en)
        if '"' in ar:
            raise SystemExit(f"{k}: the Arabic contains a double quote, which would "
                             f"close a JavaScript string literal in the page")
        pairs.append((en, ar))
    # Longest first. "Your invoice is in your inbox" is the opening clause of
    # two other sentences on this page; replaced first it would eat both.
    pairs.sort(key=lambda p: -len(p[0]))
    return pairs


# ═══════════════════════════════════════════════════════════════════════════
# 3. The RTL layer, appended after everything the English page and the upsell
#    tool have already written, so it wins on a specificity tie.
#
#    Short by design. The upsell's own stylesheet is already written in logical
#    properties (inset-inline-start, padding-inline-end, border-inline-start),
#    so it needs no mirroring at all - only the seat page's own four physical
#    declarations do.
# ═══════════════════════════════════════════════════════════════════════════
RTL_CSS = r"""
/* ══════════════════════ Arabic ══════════════════════ */
/* Appended by tools/build_pay_ar.py. Everything above this line is the English
   page's stylesheet, carried over unchanged - so a design change lands on both
   languages and only the declarations that name a physical side are restated.

   1. TYPE  2. BIDI  3. MIRROR, in that order. */

/* ─────────── 1. TYPE ─────────── */
/* Fallback metrics measured out of the font files in tools/v4/rtl.py. Without
   them the page reflows on font swap: Markazi Text's x-height is 36.4% of its
   em against Geeza Pro's 49.1%, so every Arabic heading paints a third too
   large in the fallback and snaps down when the webfont lands. */
@font-face{
  font-family:'Markazi Fallback';src:local('Geeza Pro');
  size-adjust:74.2%;ascent-override:113.1%;descent-override:48.7%;line-gap-override:0%;
}
@font-face{
  font-family:'Markazi Fallback 2';src:local('Tahoma'),local('Segoe UI');
  size-adjust:66.8%;ascent-override:125.6%;descent-override:54.1%;line-gap-override:0%;
}
@font-face{
  font-family:'Plex Arabic Fallback';src:local('Geeza Pro');
  size-adjust:105.1%;ascent-override:103.2%;descent-override:39.5%;line-gap-override:0%;
}
@font-face{
  font-family:'Plex Arabic Fallback 2';src:local('Tahoma'),local('Segoe UI');
  size-adjust:94.6%;ascent-override:114.7%;descent-override:43.9%;line-gap-override:0%;
}

[dir=rtl]{
  --display:'Markazi Text','Markazi Fallback','Markazi Fallback 2','Amiri',Georgia,serif;
  --sans:'IBM Plex Sans Arabic','Plex Arabic Fallback','Plex Arabic Fallback 2',-apple-system,'Segoe UI',sans-serif;
  /* The mono face keeps its Latin stack. Everything this page sets in mono is
     Latin: the reference code, the figures, and the eyebrow. */
}
/* Naskh needs more leading than Latin at the same size - the dots below the
   baseline collide at 1.65. */
[dir=rtl] body{line-height:1.85}
[dir=rtl] h1,[dir=rtl] h2,[dir=rtl] h3{letter-spacing:0;line-height:1.32}
[dir=rtl] h1{font-size:clamp(2rem,5.2vw,2.9rem)}
[dir=rtl] h2{font-size:1.6rem}
/* Markazi sets visibly smaller than Marcellus at the same px, and the price is
   the one figure on this page a buyer checks twice. */
[dir=rtl] .row b{font-size:1.3rem}
[dir=rtl] .row.due b{font-size:1.6rem}
[dir=rtl] .done-box h3{font-size:1.45rem}

/* Tracking and small-caps are Latin devices: letter-spacing breaks the join
   between Arabic letters, and text-transform does nothing at all. Both come
   off wherever the English sheet sets them on a string that is now Arabic.
   .ref is deliberately absent - a reference code is still Latin. */
[dir=rtl] .eyebrow,[dir=rtl] .pill{letter-spacing:0;text-transform:none}

/* ─────────── 2. BIDI ─────────── */
/* A Latin run inside Arabic is reordered unless it is isolated. Prices go
   through money(), which carries its own U+2066/U+2069 pair; these are the
   runs that arrive as bare text from the ledger or from the markup.

   isolate, NOT embed: under `embed` the Latin run still takes part in the
   surrounding reorder and a code at the start of a line gets thrown to the far
   edge of its box. */
[dir=rtl] .ref{direction:ltr;unicode-bidi:isolate;text-align:right}
/* The business name is whatever the buyer typed - Arabic, Latin, or both.
   plaintext lets each one set its own direction from its first strong
   character instead of being forced either way. */
[dir=rtl] #business{unicode-bidi:plaintext}
[dir=rtl] .invno{direction:rtl;unicode-bidi:isolate}

/* ─────────── 3. MIRROR ─────────── */
/* The whole of it. Four declarations name a physical side on this page. */
[dir=rtl] .steps li{padding:0 42px 20px 0}
[dir=rtl] .steps li::before{left:auto;right:0}
"""

# Selectors the mirror layer overrides. Rename one in the English page and the
# Arabic silently loses the rule - it still renders, it just renders wrong, in
# a language its author cannot read. So the build asserts they are still there.
HOOKS = [".eyebrow{", ".pill{", ".ref{", ".steps li{", ".steps li::before{",
         ".row b{", ".row.due b{", ".done-box h3{", ".invno{"]


# ═══════════════════════════════════════════════════════════════════════════
# Build
# ═══════════════════════════════════════════════════════════════════════════
def empty_fences(html):
    """Take the English upsell out before anything else touches the page.

    Not cosmetic. The dialog contains the sentence "Keeping your Google
    Business Profile alive", and the copy pass is about to replace the word
    "Business" wherever it appears. Emptying the regions first means the
    substitution never sees a word it does not own, and apply_upsell puts the
    Arabic back at the end."""
    for a, z in ((apply_upsell.CSS_A, apply_upsell.CSS_Z),
                 (apply_upsell.DLG_A, apply_upsell.DLG_Z),
                 (apply_upsell.BAND_A, apply_upsell.BAND_Z),
                 (apply_upsell.JS_A, apply_upsell.JS_Z),
                 ("<!-- >>> APL upsell booked >>> -->", "<!-- <<< APL upsell booked <<< -->")):
        if a not in html:
            raise SystemExit(f"{SRC.name} has no {a!r} fence - run "
                             f"`python3 tools/apply_upsell.py` on the English page first")
        html = re.sub(re.escape(a) + r".*?" + re.escape(z), a + "\n" + z, html, count=1, flags=re.S)
    return html


def build():
    src = SRC.read_text(encoding="utf-8")

    css = re.search(r"<style>\n(.*?)\n\s*</style>", src, re.S)
    if not css:
        raise SystemExit(f"no <style> block in {SRC} - has the page been restructured?")
    missing = [h for h in HOOKS
               if not re.search(re.escape(h[:-1].rstrip()) + r"\s*\{", css.group(1))]
    if missing:
        raise SystemExit("the English stylesheet no longer carries: " + ", ".join(missing)
                         + "\nUpdate the MIRROR section of RTL_CSS before rebuilding.")

    html = empty_fences(src)

    # --- the seams -------------------------------------------------------
    for en, ar in seams():
        n = html.count(en)
        if n != 1:
            raise SystemExit(f"seam appears {n}x, need exactly 1:\n    {en[:110]}\n"
                             f"pay.html has changed shape - fix seams() in {pathlib.Path(__file__).name}")
        html = html.replace(en, ar, 1)

    # --- the copy --------------------------------------------------------
    misses = []
    for en, ar in copy_pairs():
        if en not in html:
            misses.append(en)
            continue
        html = html.replace(en, ar)
    if misses:
        raise SystemExit(
            "these sentences are in tools/pay_ar_strings.py but no longer in pay.html:\n"
            + "\n".join(f"    · {m}" for m in misses)
            + "\n\nEnglish was reworded without the Arabic being revisited. Update the\n"
              "table, re-run tools/build_pay_ar_review.py, and get the new lines read.")

    # --- proof that no English survived ----------------------------------
    # A sentence the table forgot leaves an English word on an Arabic page and
    # nothing else goes wrong, so it has to be looked for rather than noticed.
    leaked = [w for w in ("deposit", "seat", "invoice", "receipt", "transfer",
                          "payment", "Business", "reference", "WhatsApp")
              if re.search(r"(?<![\w-])" + w + r"(?![\w-])", visible(html))]
    if leaked:
        raise SystemExit("English is still visible on the Arabic page: "
                         + ", ".join(leaked)
                         + "\nA string the table does not carry. Add it and rebuild.")

    # --- the upsell, in Arabic -------------------------------------------
    html = apply_upsell.apply(html, "ar")

    # --- the RTL layer, last ---------------------------------------------
    if html.count("</style>") != 1:
        raise SystemExit("expected exactly one </style>")
    html = html.replace("</style>", RTL_CSS + "</style>", 1)

    return html.replace('<script defer src="/js/aiden-chat.js?v=8002bc67"></script>',
                        aiden_version.tag())


def visible(html):
    """Roughly, the text a reader sees - markup, script and comment stripped.

    Rough is the right amount of precision here: this feeds a leak check whose
    job is to be noisy, and the cost of a false positive is one line added to
    a table."""
    body = html.split("<body>", 1)[-1]
    body = re.sub(r"<script.*?</script>", " ", body, flags=re.S)
    body = re.sub(r"<!--.*?-->", " ", body, flags=re.S)
    body = re.sub(r"<[^>]+>", " ", body)
    return body


def main():
    check = "--check" in sys.argv
    out = build()

    before = OUT.read_text(encoding="utf-8") if OUT.exists() else None
    rel = OUT.relative_to(ROOT)

    if check:
        if before is None:
            print(f"  BAD {rel}  (missing - run without --check)")
            return 1
        same = hashlib.sha256(before.encode()).hexdigest() == hashlib.sha256(out.encode()).hexdigest()
        print(f"  {'ok ' if same else 'BAD'} {rel}  ({'current' if same else 'STALE - run without --check'})")
        return 0 if same else 1

    OUT.write_text(out, encoding="utf-8")
    st = S.stats()
    print(f"wrote {rel}  ({len(out):,} bytes)")
    print(f"  {st['total']} strings · {st['harvested']} already reviewed · "
          f"{st['new']} awaiting a native pass (tools/build_pay_ar_review.py)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
