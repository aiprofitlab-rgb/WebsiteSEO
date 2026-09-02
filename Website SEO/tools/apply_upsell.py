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
     Shown once, between "pay the deposit" and Thawani's card page. It only
     ever DELAYS the payment - every exit from it calls startPayment(). */
  var UP_ID = {pay.UPSELL_ID!r}, UP_PRICE = {pay.price(u) // pay.OMR},
      UP_KEY = "apl.upsell." + ref;
  var upDlg = document.getElementById("upDlg"), upDecided = false;

  function upsellDue(){{
    if (upDecided || !upDlg || !upDlg.showModal) return false;
    /* Never interrupt a buyer who has already taken it on a previous visit. */
    try {{ if (localStorage.getItem(UP_KEY) === "1") return false; }} catch(e){{}}
    return true;
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
    startPayment();
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

  document.getElementById("payBtn").addEventListener("click", function(){{
    if (upsellDue()){{
      upDlg.showModal();
      track("view_promotion", {{ promotion_id: UP_ID, ref: ref }});
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
    html = fence("css", CSS_A, CSS_Z, css() + BOOKED_CSS, html, "</style>")
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
    html = fence("js", JS_A, JS_Z, js(), html, "  /* ─────────── the transfer receipt ─────────── */")

    # The one invariant that cannot be left to a comment: the markup must be
    # parsed before the script that binds to it. This is the exact bug that
    # shipped a silently disabled upsell the first time round, and it is
    # invisible from the outside - the page works perfectly, it just never
    # makes the offer. Assert the order rather than trusting the anchors.
    if html.index(DLG_A) > html.index(JS_A):
        raise SystemExit(
            "dialog is injected AFTER the page script that binds to it - the gate "
            "would find no #upDlg and every buyer would skip the offer silently")
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
