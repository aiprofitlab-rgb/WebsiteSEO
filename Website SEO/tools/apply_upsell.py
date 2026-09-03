#!/usr/bin/env python3
"""
Put the checkout's upsell interstitial onto the storefront seat page.

WHY THIS IS A TOOL AND NOT A PASTE
----------------------------------
public_html/en/pay.html is hand-written and outside build_v4.py, so the obvious
move is to paste the dialog into it. Do not. The block contains a REFUND
GUARANTEE and a price, and two hand-maintained copies of a guarantee is how the
same promise ends up meaning two different things on two pages - the version
Nahid remembers and the version the buyer screenshotted.

So the markup, the CSS and the numbers are all rendered from
tools/v4/page_checkout.py, which renders them from tools/v4/pay.py. Edit the
copy or the price there, re-run this, and both checkouts say the same sentence.

TWO ROUTES, TWO TRIGGERS
------------------------
The seat page takes money two ways and only one of them has a button. When the
card gateway is off, render() sets #payBtn to display:none - and #payBtn is
what the gate binds to, so hanging the offer there alone means a bank-transfer
buyer is never shown it at all. Nothing looks broken; the offer simply never
happens. So the transfer route gets its own trigger: a standing band inside the
pay box, plus one auto-open on the first visit to that seat. The offer is
BOOKED and not charged, which is what makes it safe to make away from the
payment button.

IDEMPOTENT. Every injected region is fenced by a matched pair of marker
comments; a re-run replaces what is between the fences rather than adding a
second copy. Running it twice leaves the file byte-identical - which is the
property the repo checks by hashing twice, and which this file's own
--check mode asserts.

    python3 tools/apply_upsell.py            # write
    python3 tools/apply_upsell.py --check    # verify it is applied and current
"""
import hashlib
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE / "v4"))

import pay              # noqa: E402
import page_checkout    # noqa: E402

TARGET = ROOT / "public_html" / "en" / "pay.html"

# Every region this tool owns, as (name, opening fence, closing fence).
CSS_A, CSS_Z = "/* >>> APL upsell css >>> */", "/* <<< APL upsell css <<< */"
DLG_A, DLG_Z = "<!-- >>> APL upsell dialog >>> -->", "<!-- <<< APL upsell dialog <<< -->"
BAND_A, BAND_Z = "<!-- >>> APL upsell band >>> -->", "<!-- <<< APL upsell band <<< -->"
JS_A, JS_Z = "/* >>> APL upsell js >>> */", "/* <<< APL upsell js <<< */"


# ---------------------------------------------------------------------------
# The three payloads
# ---------------------------------------------------------------------------
def css():
    """The interstitial's stylesheet, lifted whole out of the checkout's CSS.

    Two tokens the checkout's kit defines and this page does not (--teal-950,
    --ease) are declared on .up-dlg itself, so they cascade to everything
    inside the dialog and nothing outside it. Same for .btn-teal: the seat page
    calls its primary button .btn-primary, and the shared markup asks for
    .btn-teal."""
    whole = page_checkout.CSS
    start = whole.index("/* ==================================================== the upsell")
    shim = (
        "/* tokens this page does not define, scoped to the dialog that needs them */\n"
        ".up-dlg{--teal-950:#072B22;--ease:cubic-bezier(.22,.7,.25,1)}\n"
        ".up-dlg .btn-teal{background:var(--teal);color:#fff}\n"
    )
    return shim + whole[start:]


def dialog():
    """The markup, English only - the seat page has no Arabic twin."""
    return page_checkout.upsell_dialog("en").strip()


def js():
    """The gate.

    Mirrors the checkout's, with one difference that matters: the storefront
    ledger is a SEPARATE service that is not in this repo, so an accepted offer
    cannot be added to the order the way the checkout adds a line item. It is
    recorded three ways instead, none of which can block the payment:

      1. a GA4 event, which is what Nahid can actually report on;
      2. a fire-and-forget POST to /pay/upsell - harmless 404 today, and it
         starts working by itself the day that route exists;
      3. localStorage, which is what puts the confirmation block in front of
         the buyer when they come back from the gateway having paid.

    (3) is the one that guarantees Nahid finds out: it hands the buyer a
    prefilled WhatsApp message on the confirmed screen. Until the ledger knows
    this offer exists, that message IS the booking record."""
    u = pay.item(pay.UPSELL_ID)
    return f"""
  /* ---------------------------------------------------- the upsell gate ---
     Shown once, before the buyer pays. There are two ways to pay here and so
     there are two ways in:

       CARD      the gate sits between the pay button and Thawani's page. It
                 only ever DELAYS the payment - every exit calls startPayment().
       TRANSFER  there is no pay button at all (render() hides it), so the gate
                 is hung on the page instead: a standing band in the pay box,
                 plus one auto-open on the first visit. Nothing here can touch
                 the payment, because in this mode the page does not take it.

     Both are safe because the offer is BOOKED, not charged. */
  var UP_ID = {pay.UPSELL_ID!r}, UP_PRICE = {pay.price(u) // pay.OMR},
      UP_KEY = "apl.upsell." + ref, UP_SEEN = "apl.upsell.seen." + ref;
  var upDlg  = document.getElementById("upDlg"),
      upBand = document.getElementById("upBand"),
      upDecided = false, upOffline = false;

  /* Taken on a previous visit. Read through a helper because three different
     callers need it and localStorage is allowed to throw in every one. */
  function upsellTaken(){{
    try {{ return localStorage.getItem(UP_KEY) === "1"; }} catch(e){{ return false; }}
  }}

  function upsellDue(){{
    if (upDecided || !upDlg || !upDlg.showModal) return false;
    /* Never interrupt a buyer who has already taken it on a previous visit. */
    return !upsellTaken();
  }}

  function upsellShow(){{
    upDecided = false;          /* re-opening it by hand is not a decision */
    try {{ upDlg.showModal(); }} catch(e){{ return; }}
    track("view_promotion", {{ promotion_id: UP_ID, ref: ref }});
  }}

  function upsellRecord(){{
    try {{ localStorage.setItem(UP_KEY, "1"); }} catch(e){{}}
    /* Best effort, never awaited, and wrapped so that a service worker or a
       blocked request cannot throw into the payment path. keepalive lets it
       survive the redirect that is about to happen. */
    try {{
      fetch(API + "/pay/upsell", {{
        method: "POST", keepalive: true,
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify({{ ref: ref, offer: UP_ID, price: UP_PRICE, currency: "OMR" }})
      }}).catch(function(){{}});
    }} catch(e){{}}
  }}

  function upsellClose(taken){{
    upDecided = true;
    try {{ upDlg.close(); }} catch(e){{}}
    track(taken ? "add_to_cart" : "upsell_declined",
          {{ item_id: UP_ID, value: UP_PRICE, currency: "OMR", ref: ref }});
    if (taken) {{ upsellRecord(); upsellBanner(); }}
    if (upOffline) return upsellSettled(taken);
    startPayment();
  }}

  /* Where a transfer buyer lands after deciding. There is no payment to start,
     so the page just resolves: taken swaps the band for the booked block and
     puts it in front of them; declined leaves the band as the way back in. */
  function upsellSettled(taken){{
    if (upBand) upBand.hidden = taken;
    if (!taken) return;
    var box = document.getElementById("upBooked");
    if (box && box.scrollIntoView) box.scrollIntoView({{ behavior: "smooth", block: "center" }});
  }}

  /* Called by render() on the no-gateway branch - see rewire() in
     tools/apply_upsell.py. Without it the gate has nothing to hang on: the
     button it binds to is display:none in that mode, and the offer is never
     made to a single transfer buyer. */
  function upsellOffline(){{
    upOffline = true;
    if (!upBand || !upsellDue()) return;
    upBand.hidden = false;

    /* The auto-open happens once ever, per seat. The band is permanent, so a
       buyer who closes it still has a way back and is not asked again on every
       reload. If localStorage cannot be read we assume it HAS been seen -
       failing towards the quieter page rather than towards nagging. */
    var seen = true;
    try {{ seen = localStorage.getItem(UP_SEEN) === "1"; }} catch(e){{}}
    if (seen) return;
    try {{ localStorage.setItem(UP_SEEN, "1"); }} catch(e){{}}
    /* Let the seat card paint first: a dialog that arrives with the page reads
       as an ad and gets dismissed before it is read. */
    setTimeout(function(){{ if (upsellDue()) upsellShow(); }}, 900);
  }}

  /* The confirmation the buyer sees on the paid screen, and the thing that
     actually tells Nahid a booking happened. Drawn from localStorage, so it
     survives the round trip through the gateway. */
  function upsellBanner(){{
    var taken = false;
    try {{ taken = localStorage.getItem(UP_KEY) === "1"; }} catch(e){{}}
    var box = document.getElementById("upBooked");
    if (!box) return;
    box.hidden = !taken;
    if (!taken) return;
    var msg = "Hello Nahid - seat " + ref + ". I added the {pay.t(u, 'name')} at "
            + "OMR " + UP_PRICE + "/month on the payment page. Please confirm it.";
    var a = document.getElementById("upBookedWa");
    if (a) a.href = WA + "&text=" + encodeURIComponent(msg);
  }}

  if (upDlg){{
    document.getElementById("upYes").addEventListener("click", function(){{ upsellClose(true); }});
    document.getElementById("upNo").addEventListener("click", function(){{ upsellClose(false); }});
    document.getElementById("upX").addEventListener("click", function(){{ upsellClose(false); }});
    upDlg.addEventListener("cancel", function(e){{ e.preventDefault(); upsellClose(false); }});
  }}

  /* The band's own button ignores upDecided: a buyer who declined and then
     went looking for the offer again is asking for it, not being interrupted
     by it. Only actually owning it takes the button away. */
  if (upBand){{
    document.getElementById("upBandBtn").addEventListener("click", function(){{
      if (upDlg && upDlg.showModal && !upsellTaken()) upsellShow();
    }});
  }}

  document.getElementById("payBtn").addEventListener("click", function(){{
    if (upsellDue()){{
      upsellShow();
      return;
    }}
    startPayment();
  }});

  /* A buyer returning from a successful payment never passes through the
     dialog, so the banner is drawn on load too. */
  upsellBanner();
"""


# The block that shows on the confirmed screen. Injected next to the dialog.
def booked_box():
    u = pay.item(pay.UPSELL_ID)
    return f"""<div class="up-booked" id="upBooked" hidden>
  <h3>{pay.t(u, 'name')} &mdash; booked at OMR {pay.price(u) // pay.OMR}/month</h3>
  <p>Locked at the price you were shown, and <b>not charged today</b>. It begins the month
    after your site goes live. Send me one message so it is on your file in writing &mdash;
    that message is your record of the price and the
    {u['guarantee_months']}-month guarantee.</p>
  <a class="btn btn-wa" id="upBookedWa" href="#" target="_blank" rel="noopener">Confirm it on WhatsApp</a>
</div>"""


def band():
    """The standing offer, for the route that has no pay button.

    Short on purpose, and carrying NO guarantee wording: a guarantee is a
    promise and it lives in exactly one place, the dialog. The headline and
    both figures are the dialog's own values, read from the same tables, so
    the band cannot drift away from what the buyer reads when they open it."""
    u = pay.item(pay.UPSELL_ID)
    w = page_checkout.UPSELL["en"]
    now, rack = pay.money(pay.price(u)), pay.money(u["rack"])
    return f"""      <div class="up-band" id="upBand" hidden>
        <p class="eyebrow">Before you transfer &#183; ninety seconds</p>
        <h3>{w['h']}</h3>
        <p>{pay.t(u, 'name')} is the monthly work that puts your name inside Google's answers
          and ChatGPT's. Booked from this page it is <b>{now} a month</b> instead of {rack}
          &mdash; and <b>nothing is charged today</b>.</p>
        <button type="button" class="btn btn-block" id="upBandBtn">Read it &mdash; {now} a month</button>
      </div>"""


# The band's stylesheet. It sits inside .pay, which already styles h3, so these
# rules have to come after that one - they do, because the whole injected block
# is written in at the end of <style> where equal specificity resolves by order.
BAND_CSS = """
.up-band{
  background:linear-gradient(168deg,#FCF8F0,#F5EFE1);
  border:1.5px solid var(--amber-bright);border-radius:12px;
  padding:20px 18px;margin:18px 0 0;
}
.up-band .eyebrow{color:var(--amber);margin:0 0 8px}
.up-band h3{font-family:var(--display);font-weight:400;font-size:1.12rem;line-height:1.35;
  color:var(--teal-900);margin:0 0 8px}
.up-band p{font-size:.92rem;color:var(--muted);margin:0 0 16px}
.up-band b{color:var(--ink)}
.up-band .btn{background:var(--teal);color:#fff}
"""


BOOKED_CSS = """
.up-booked{
  background:var(--white);border:1.5px solid var(--teal);border-radius:12px;
  padding:20px 18px;margin-top:18px;
}
.up-booked h3{font-family:var(--display);font-weight:400;font-size:1.1rem;color:var(--teal-900);margin:0 0 6px}
.up-booked p{font-size:.93rem;color:var(--muted);margin:0 0 14px}
.up-booked b{color:var(--ink)}
"""


# ---------------------------------------------------------------------------
# Injection
# ---------------------------------------------------------------------------
def fence(name, a, z, payload, html, anchor):
    """Replace the region between the fences, or create it at `anchor`.

    `anchor` is a literal string already in the file; the fenced block is
    inserted immediately BEFORE it on first run. On every later run the anchor
    is irrelevant, because the fences are found instead - which is what keeps
    a re-run from stacking a second copy."""
    block = f"{a}\n{payload}\n{z}\n"
    if a in html:
        if z not in html:
            raise SystemExit(f"{name}: opening fence present but closing fence missing - "
                             f"{TARGET.name} has been hand-edited inside a generated region")
        pattern = re.compile(re.escape(a) + r".*?" + re.escape(z) + r"\n?", re.S)
        return pattern.sub(lambda _: block, html, count=1)
    if html.count(anchor) != 1:
        raise SystemExit(f"{name}: anchor {anchor!r} appears {html.count(anchor)}x, need exactly 1")
    return html.replace(anchor, block + anchor, 1)


def rewire(html):
    """The two edits this tool makes to hand-written code it does not own.

    Both are surgical line rewrites rather than re-emitted blocks, and both
    carry their own independent guard: the file in the repo has already had
    the first one applied, so a shared early return would silently skip the
    second one for ever."""
    return rewire_offline(rewire_paybtn(html))


# The end of render()'s no-gateway branch. The band reveal goes AFTER it, not
# before: those lines restyle the pay box for the transfer route, and the band
# belongs to the box they leave behind.
OFFLINE_ANCHOR = '      $("altBox").querySelector("p").style.display = "none";\n'
OFFLINE_ADD = (
    '      /* Added by tools/apply_upsell.py. This branch hides #payBtn, which is\n'
    '         what the upsell gate binds to - so the gate is handed its own way in\n'
    '         rather than being silently disabled for every transfer buyer. */\n'
    '      upsellOffline();\n')


def rewire_offline(html):
    """Give the gate a trigger on the branch that has no pay button."""
    if OFFLINE_ADD in html or "upsellOffline();" in html:
        return html                       # already rewired
    if html.count(OFFLINE_ANCHOR) != 1:
        raise SystemExit(f"rewire: the last line of render()'s no-gateway branch appears "
                         f"{html.count(OFFLINE_ANCHOR)}x, need exactly 1 - pay.html has "
                         f"changed shape")
    return html.replace(OFFLINE_ANCHOR, OFFLINE_ANCHOR + OFFLINE_ADD, 1)


def rewire_paybtn(html):
    """Turn the existing click handler into startPayment().

    The upsell has to run BEFORE the body of that handler, and the handler is
    hand-written code this tool does not own. Rather than re-emit it, the two
    lines that open and close it are rewritten in place, once - after which the
    marker in the opening line makes the change self-evidently idempotent."""
    OPEN_WAS = '  $("payBtn").addEventListener("click", function(){\n'
    OPEN_NOW = ('  /* Wrapped by tools/apply_upsell.py: the upsell gate below calls this. */\n'
                '  function startPayment(){\n')
    CLOSE_WAS = '      .catch(function(){ payFailed("offline"); });\n  });\n'
    CLOSE_NOW = '      .catch(function(){ payFailed("offline"); });\n  }\n'

    if "function startPayment(){" in html:
        return html                       # already rewired
    for was, n in ((OPEN_WAS, "opening"), (CLOSE_WAS, "closing")):
        if html.count(was) != 1:
            raise SystemExit(f"rewire: {n} line of the payBtn handler appears "
                             f"{html.count(was)}x, need exactly 1 - pay.html has changed shape")
    return html.replace(OPEN_WAS, OPEN_NOW, 1).replace(CLOSE_WAS, CLOSE_NOW, 1)


def apply(html):
    html = rewire(html)
    html = fence("css", CSS_A, CSS_Z, css() + BOOKED_CSS + BAND_CSS, html, "</style>")
    # BEFORE <footer>, and that is not cosmetic. The page's script is a plain
    # IIFE at the end of <body>, not deferred, so it runs the instant it is
    # parsed. A dialog injected after it does not exist yet when the gate looks
    # it up - getElementById returns null, `if (upDlg)` quietly skips, and the
    # buyer goes straight to the card page having never seen the offer. No
    # error, no clue. The ordering assertion below is what keeps it that way.
    html = fence("dialog", DLG_A, DLG_Z, dialog(), html, "<footer>")
    # The confirmed-screen block belongs inside the card, under the done box.
    html = fence("booked", "<!-- >>> APL upsell booked >>> -->",
                 "<!-- <<< APL upsell booked <<< -->", booked_box(), html,
                 '    <!-- returning from the payment page -->')
    # The band lives INSIDE the pay box, above the error line, so that on the
    # transfer route it reads as part of paying rather than as an ad bolted to
    # the page. Same parse-order requirement as the dialog: it is bound by id
    # at script-parse time and must already exist.
    html = fence("band", BAND_A, BAND_Z, band(), html,
                 '      <div class="msg err" id="payErr"></div>')
    html = fence("js", JS_A, JS_Z, js(), html, "  /* ─────────── the transfer receipt ─────────── */")

    # The one invariant that cannot be left to a comment: the markup must be
    # parsed before the script that binds to it. This is the exact bug that
    # shipped a silently disabled upsell the first time round, and it is
    # invisible from the outside - the page works perfectly, it just never
    # makes the offer. Assert the order rather than trusting the anchors.
    for name, marker, node in (("dialog", DLG_A, "#upDlg"), ("band", BAND_A, "#upBand")):
        if html.index(marker) > html.index(JS_A):
            raise SystemExit(
                f"{name} is injected AFTER the page script that binds to it - the gate "
                f"would find no {node} and every buyer would skip the offer silently")
    return html


def main():
    check = "--check" in sys.argv
    before = TARGET.read_text(encoding="utf-8")
    after = apply(before)

    # Prove idempotency rather than asserting it: apply twice, compare.
    twice = apply(after)
    if hashlib.sha256(after.encode()).hexdigest() != hashlib.sha256(twice.encode()).hexdigest():
        raise SystemExit("NOT IDEMPOTENT - a second run changes the file again")

    rel = TARGET.relative_to(ROOT)
    if check:
        state = "current" if after == before else "STALE - run without --check"
        print(f"  {'ok ' if after == before else 'BAD'} {rel}  ({state})")
        return 0 if after == before else 1
    TARGET.write_text(after, encoding="utf-8")
    print(f"  {'ok ' if after == before else 'NEW'} {rel}"
          + ("  (already current)" if after == before else "  (upsell applied, idempotency verified)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
