#!/usr/bin/env python3
"""
Order status — where the payment provider sends the buyer back to.

One page, three states, chosen from ?status= :

  success  the provider redirected back after the payment sheet
  cancel   the buyer backed out; nothing was charged
  (none)   somebody arrived here on their own

The single most important rule on this page: A URL PARAMETER IS NOT A RECEIPT.
?status=success only means the buyer's browser came back through the success
URL, and anybody can type that. So the page never says "paid" on the strength
of the query string. It says the payment was submitted and is being confirmed,
and it only upgrades that wording - and only then fires the `purchase` analytics
event - once GET {api}/session/{id} has come back from our own server saying
payment_status is "paid".

Which means that until the checkout API is deployed, every successful return
lands on the honest middle state, and that is the correct behaviour, not a
degraded one.
"""
import pay
from kit import WA, WA_ICON, STAR

CSS = """
.ost{padding:clamp(140px,16vw,200px) 0 clamp(50px,6vw,80px)}
.ost .wrap{position:relative}

/* the state mark: a ring that draws itself, then the glyph inside it */
.mark-o{
  width:88px;height:88px;border-radius:50%;display:grid;place-items:center;margin:0 0 28px;
  border:2px solid var(--line-dark);position:relative;
}
.mark-o svg{width:40px;height:40px;fill:none;stroke-width:2.4;stroke-linecap:round;stroke-linejoin:round}
.mark-o.good{border-color:rgba(31,175,94,.5)}
.mark-o.good svg{stroke:var(--wa)}
.mark-o.wait{border-color:rgba(232,201,143,.5)}
.mark-o.wait svg{stroke:var(--amber-bright)}
.mark-o.stop{border-color:rgba(166,67,31,.55)}
.mark-o.stop svg{stroke:#E08461}
.mark-o svg path,.mark-o svg circle,.mark-o svg polyline{
  stroke-dasharray:var(--len,80);stroke-dashoffset:var(--len,80);
  animation:draw .9s var(--ease) forwards;animation-delay:.15s;
}
@keyframes draw{to{stroke-dashoffset:0}}
@media (prefers-reduced-motion:reduce){ .mark-o svg path,.mark-o svg circle,.mark-o svg polyline{animation:none;stroke-dashoffset:0} }

.ost h1{font-size:clamp(2.2rem,5vw,3.6rem);line-height:1.05;margin:0 0 18px}
.ost .lede{max-width:56ch}

.refcard{
  display:inline-flex;flex-wrap:wrap;align-items:center;gap:clamp(16px,3vw,34px);
  background:rgba(241,239,232,.06);border:1px solid var(--line-dark);border-radius:14px;
  padding:18px clamp(20px,2.6vw,28px);margin:clamp(24px,3vw,34px) 0 0;
}
.refcard div{display:flex;flex-direction:column;gap:5px}
.refcard .k{font-family:var(--mono);font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;color:var(--amber-pale)}
.refcard .v{font-family:var(--mono);font-size:1.08rem;color:var(--cream);letter-spacing:.05em;font-variant-numeric:tabular-nums}

/* next steps */
.nxt{list-style:none;margin:clamp(28px,4vw,44px) 0 0;padding:0;display:grid;gap:0;counter-reset:n}
.nxt li{
  position:relative;padding:20px 0 20px 52px;border-top:1px solid var(--line);
  color:var(--muted);font-size:1rem;line-height:1.6;
}
.nxt li:last-child{border-bottom:1px solid var(--line)}
.nxt li::before{
  counter-increment:n;content:"0" counter(n);position:absolute;left:0;top:20px;
  font-family:var(--mono);font-size:.82rem;letter-spacing:.12em;color:var(--amber-text);
}
.nxt b{color:var(--teal-950);font-weight:600;display:block;font-size:1.05rem;margin-bottom:3px;font-family:var(--display)}

.state{display:none}
.state.on{display:block}
"""

CHECK = ('<svg viewBox="0 0 24 24" aria-hidden="true"><polyline points="4,13 9.5,18.5 20,6"/></svg>')
CLOCK = ('<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/>'
         '<polyline points="12,6.5 12,12 16,14.5"/></svg>')
CROSS = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12"/><path d="M18 6L6 18"/></svg>')


def _state(sid, mark, glyph, h1, lede, extra=""):
    return f"""  <div class="state" id="st-{sid}">
    <span class="mark-o {mark}" aria-hidden="true">{glyph}</span>
    <h1 class="h1">{h1}</h1>
    <p class="lede">{lede}</p>
{extra}
  </div>"""


def body():
    cfg = pay.CONFIG_JSON()

    # Python 3.11 cannot nest a triple-quoted f-string inside another one, so
    # the shared blocks are built first and passed in as plain strings.
    contact = f"""    <div class="btn-row" style="margin-top:clamp(26px,3.4vw,38px)">
      <a class="btn btn-wa" href="{WA}&text=Hello%20Nahid%2C%20about%20my%20order%20">{WA_ICON}Ask me about it</a>
      <a class="btn btn-ghost" href="/">Back to the site</a>
    </div>"""

    retry = f"""    <div class="btn-row" style="margin-top:clamp(26px,3.4vw,38px)">
      <a class="btn btn-amber" href="/en/checkout/?restore=1">Pick up where I left off</a>
      <a class="btn btn-ghost" href="{WA}&text=Hello%20Nahid%2C%20I%20had%20trouble%20paying%20on%20the%20site.">Something went wrong &mdash; tell me</a>
    </div>"""

    ref_status = """    <div class="refcard">
      <div><span class="k">Your reference</span><span class="v" data-ref>&mdash;</span></div>
      <div><span class="k">Status</span><span class="v" data-status>Confirming</span></div>
    </div>
""" + contact

    ref_paid = """    <div class="refcard">
      <div><span class="k">Your reference</span><span class="v" data-ref>&mdash;</span></div>
      <div><span class="k">Paid</span><span class="v" data-paid>&mdash;</span></div>
    </div>
""" + contact

    states = "\n\n".join([
        _state("wait", "wait", CLOCK,
               "Thank you &mdash; I&#8217;m confirming your payment.",
               "Your order has come through. I check every payment by hand against the provider "
               "before I call anything confirmed, so your receipt follows by email shortly &mdash; "
               "usually within minutes, and always within one business day.",
               ref_status),
        _state("paid", "good", CHECK,
               "Payment received. Your slot is held.",
               "That is the money side finished. Everything from here is me and you: I will be in "
               "touch within one business day to take the brief properly, and nothing gets built "
               "off a form alone.",
               ref_paid),
        _state("cancel", "stop", CROSS,
               "Nothing was charged.",
               "You backed out of the payment page, which is entirely your right &mdash; no money "
               "moved and no order was created. Your configuration is still saved in this browser, "
               "so you can walk straight back into it, or ask me the question that stopped you.",
               retry),
        _state("fail", "stop", CROSS,
               "That payment didn&#8217;t go through.",
               "The provider tells me the payment was not completed, so nothing has been charged. "
               "This is usually a bank declining an online transaction rather than anything wrong "
               "with the card &mdash; a call to them, or a different card, normally settles it.",
               retry),
        _state("none", "wait", CLOCK,
               "Looking for an order?",
               "There is nothing to show on this page unless you have just come back from a "
               "payment. If you have an order reference and want to know where it stands, send it "
               "to me and I will tell you in plain terms.",
               contact),
    ])

    return f"""<main id="main">

<header class="ost s-dark grain">
  <div class="wrap">

{states}

  </div>
</header>

<section class="s-cream grain pad-s">
  <div class="wrap-n">
    <p class="eyebrow"><span class="star">{STAR}</span> What happens now</p>
    <h2 class="h2">The next four things, in order.</h2>
    <ol class="nxt">
      <li><b>Your receipt and invoice</b>Emailed to the address on your order, itemised, from Lotus Gulf
        International (CR <span dir="ltr">1570092</span>). No VAT line, because the company is below the
        registration threshold.</li>
      <li><b>The brief call</b>Within one business day. Half an hour, on the phone or WhatsApp, about your
        business rather than about websites.</li>
      <li><b>A link in the first week</b>You watch it get built. You are never handed a finished thing you
        have not already seen and commented on.</li>
      <li><b>Go-live, and the promise starts</b>The 30-day First Inquiry Promise counts from the day it goes
        live, not the day you paid.</li>
    </ol>

    <p style="margin-top:clamp(26px,3.4vw,38px);color:var(--muted);font-size:.96rem">
      Changed your mind? The <a href="/refund-policy/">Refund &amp; Cancellation Policy</a> sets out exactly
      what comes back and when &mdash; in short, everything, until the day building starts.
    </p>
  </div>
</section>

<script type="application/json" id="payCfg">{cfg}</script>
</main>
"""


JS = r"""
/* ---------------------------------------------------------------------------
   Order status.

   ?status=success is a claim made by a URL, not proof of payment. This script
   therefore starts every successful return in the "confirming" state and only
   upgrades it - and only then reports a purchase to analytics - after our own
   API confirms payment_status === "paid" for the session. With no API deployed
   the page simply stays in the honest state, which is why it is the default.
--------------------------------------------------------------------------- */
(function(){
  "use strict";
  var cfgEl = document.getElementById("payCfg");
  var CFG = {};
  try { CFG = JSON.parse(cfgEl.textContent); } catch(e){}

  var qs = new URLSearchParams(location.search);
  var status = (qs.get("status") || "").toLowerCase();
  var session = qs.get("session") || qs.get("session_id") || "";
  var ref = qs.get("ref") || "";

  var saved = null;
  try { saved = JSON.parse(localStorage.getItem("apl_order") || "null"); } catch(e){}
  if (!ref && saved) ref = saved.ref || "";
  if (!session && saved) session = saved.session || "";

  function show(id){
    document.querySelectorAll(".state").forEach(function(el){ el.classList.remove("on"); });
    var el = document.getElementById("st-" + id);
    if (el) el.classList.add("on");
    /* The heading in a hidden state was wrapped for the reveal animation by the
       shared motion script and left un-revealed; force the visible one open. */
    if (el) el.querySelectorAll(".rv,.rvw").forEach(function(n){ n.classList.add("vis"); });
  }
  function fill(sel, text){
    document.querySelectorAll(sel).forEach(function(el){ el.textContent = text; });
  }

  var first = status === "cancel" ? "cancel"
            : status === "success" ? "wait"
            : status === "fail" ? "fail"
            : status ? "wait" : "none";
  show(first);
  if (ref) fill("[data-ref]", ref);

  if (first !== "wait" || !CFG.api || !session) return;

  /* Confirm it properly. A failure here is not an error state for the buyer -
     it only means the page keeps saying "confirming", which is true. */
  fetch(CFG.api + "/session/" + encodeURIComponent(session), {headers: {"Accept": "application/json"}})
    .then(function(r){ return r.json(); })
    .then(function(d){
      if (!d) return;
      if (d.payment_status === "paid"){
        show("paid");
        if (d.reference || ref) fill("[data-ref]", d.reference || ref);
        fill("[data-paid]", d.amount_display || "Confirmed");
        try { localStorage.removeItem("apl_order"); } catch(e){}
        if (typeof gtag === "function"){
          gtag("event", "purchase", {
            transaction_id: d.reference || ref || session,
            value: typeof d.amount === "number" ? d.amount / (CFG.baisa || 1000) : undefined,
            currency: CFG.currency || "OMR"
          });
        }
      } else if (d.payment_status === "cancelled" || d.payment_status === "unpaid"){
        show("fail");
        if (ref) fill("[data-ref]", ref);
      }
    })
    .catch(function(){ /* stay in "confirming" - it is the truthful state */ });
})();
"""


META = dict(
    noindex=True,
    slug="order",
    title="Your order | AI Profit Lab",
    desc="Where your AI Profit Lab order stands, and what happens next.",
    nav="/en/services/",
    next=("Back to the start", "You don't have to learn AI", "/"),
)
