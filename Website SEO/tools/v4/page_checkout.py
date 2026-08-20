#!/usr/bin/env python3
"""
Checkout.

The one page on the site that asks for money, so it is built to a different
standard from the pages that ask for attention.

Three properties it has to keep:

1. THE ARITHMETIC EXISTS ONCE. Every price, surcharge and split comes from
   pay.py, serialised into the page as JSON and recomputed in the browser from
   that same table. Nothing is retyped in JavaScript, and money is integer
   baisa from end to end - see the note at the top of pay.py.

2. IT NEVER CLAIMS MORE THAN IT DOES. While pay.PAY_LIVE is False there is no
   card field, no "secure payment" badge and no wording that implies a charge:
   the page collects the order, stamps it with a reference, and hands it over
   on WhatsApp with the balance invoiced. The instant the gateway is approved,
   one boolean turns the same button into a Thawani redirect.

3. THE CARD PAGE IS NEVER OURS. Thawani's secret key creates the session
   server-side and the buyer is redirected to Thawani's own hosted page, so no
   card number is ever typed into aiprofitlab.io. The front end only ever calls
   our own API, whose contract is written down in docs/payments-api.md.

Deep links: /en/checkout-v4/?plan=full&items=dashboard,autopilot preselects a
configuration, which is what the buttons on the services page use.
"""
import pay
from kit import WA, WA_ICON, STAR

CSS = """
/* ------------------------------------------------------------ the frame */
.co-grid{
  display:grid;grid-template-columns:minmax(0,1.14fr) minmax(0,.86fr);
  gap:clamp(26px,4vw,58px);align-items:start;
}
/* minmax(0,…) rather than 1fr on both tracks: a 1fr track takes its automatic
   minimum from its widest content, and the summary holds tabular numbers that
   will not wrap. Without this the right column pushes the grid past the
   viewport and html{overflow-x:clip} hides the evidence. */
.sum-wrap{position:sticky;top:96px}

/* ------------------------------------------------------------- the steps */
.step{border-top:1px solid var(--line);padding:clamp(26px,3.4vw,40px) 0}
.step:first-child{border-top:0;padding-top:0}
.step-h{display:flex;align-items:baseline;gap:14px;margin:0 0 6px}
.step-h .sn{
  font-family:var(--mono);font-size:.82rem;letter-spacing:.14em;color:var(--amber-text);flex:none;
}
.step-h h2{font-size:clamp(1.4rem,2.5vw,1.9rem);margin:0}
.step .hint{color:var(--muted);font-size:.98rem;margin:0 0 20px;max-width:56ch}

/* ------------------------------------------------- selectable option card
   A real <input> inside the <label>, moved off-screen rather than
   display:none - a hidden input is not focusable, and this whole page has to
   be operable from the keyboard. The card paints its own state from :checked
   and its own focus ring from :has(). */
.opts{display:grid;gap:12px}
.opt{
  position:relative;display:flex;gap:15px;align-items:flex-start;cursor:pointer;
  background:var(--panel);border:1px solid var(--line);border-radius:14px;
  padding:clamp(16px,2vw,20px) clamp(16px,2vw,22px);
  transition:border-color .25s var(--ease),background .25s,box-shadow .25s,transform .25s var(--ease);
}
.opt:hover{border-color:var(--amber-pale);background:var(--white)}
.opt input{position:absolute;opacity:0;width:1px;height:1px;margin:0;pointer-events:none}
.opt:has(input:checked){border-color:var(--teal);background:var(--white);box-shadow:0 18px 40px -30px rgba(15,110,86,.75)}
.opt:has(input:focus-visible){outline:2px solid var(--amber);outline-offset:3px}
.opt .tick{
  flex:none;width:23px;height:23px;margin-top:2px;border-radius:6px;
  border:1.5px solid rgba(35,43,38,.3);background:var(--white);
  display:grid;place-items:center;transition:background .2s,border-color .2s;
}
.opt input[type=radio]~.tick{border-radius:50%}
.opt .tick::after{
  content:"";width:11px;height:6px;border-left:2px solid var(--white);border-bottom:2px solid var(--white);
  transform:rotate(-45deg) scale(.4);opacity:0;transition:opacity .2s,transform .25s var(--ease);
  margin-top:-2px;
}
.opt input[type=radio]~.tick::after{
  width:9px;height:9px;border:0;border-radius:50%;background:var(--white);margin:0;transform:scale(.3);
}
.opt:has(input:checked) .tick{background:var(--teal);border-color:var(--teal)}
.opt:has(input:checked) .tick::after{opacity:1;transform:rotate(-45deg) scale(1)}
.opt:has(input[type=radio]:checked) .tick::after{transform:scale(1)}
.opt-b{flex:1 1 auto;min-width:0}
.opt-h{display:flex;justify-content:space-between;align-items:baseline;gap:14px;flex-wrap:wrap}
.opt-h b{font-family:var(--display);font-weight:400;font-size:1.14rem;color:var(--teal-950);line-height:1.25}
.opt-p{font-family:var(--mono);font-variant-numeric:tabular-nums;font-size:1rem;color:var(--teal);white-space:nowrap}
.opt-d{display:block;color:var(--muted);font-size:.95rem;line-height:1.55;margin-top:7px}
.opt .flag{
  display:inline-block;font-family:var(--mono);font-size:.66rem;letter-spacing:.12em;text-transform:uppercase;
  color:var(--amber-text);background:var(--panel-2);border-radius:99px;padding:3px 9px;margin-left:9px;
  vertical-align:.14em;
}
.opt.locked{cursor:default;background:var(--panel-2);border-style:dashed}
.opt.locked:hover{border-color:var(--line);background:var(--panel-2)}
.opt.locked .tick{background:var(--teal);border-color:var(--teal)}
.opt.locked .tick::after{opacity:1;transform:rotate(-45deg) scale(1)}

/* the bundle note, revealed only when both add-ons are on */
.bundle{
  display:none;align-items:flex-start;gap:12px;margin-top:12px;
  background:var(--teal-950);color:var(--cream);border-radius:14px;padding:16px 20px;font-size:.96rem;
}
.bundle.on{display:flex}
.bundle .star{flex:none;font-size:1.1rem;line-height:1.5}
.bundle b{color:var(--amber-bright);font-weight:600}

/* ------------------------------------------------------------ the fields */
.flds{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:15px}
.fld{display:flex;flex-direction:column;gap:7px}
.fld.full{grid-column:1/-1}
.fld label{font-family:var(--mono);font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.fld label .opt-tag{text-transform:none;letter-spacing:0;font-family:var(--sans);opacity:.75}
.fld input,.fld textarea{
  font-family:var(--sans);font-size:1rem;color:var(--ink);background:var(--white);
  border:1px solid var(--line);border-radius:10px;padding:13px 15px;width:100%;
  transition:border-color .2s,box-shadow .2s;
}
.fld textarea{resize:vertical;min-height:88px;line-height:1.55}
.fld input::placeholder,.fld textarea::placeholder{color:rgba(90,102,93,.5)}
.fld input:focus,.fld textarea:focus{outline:none;border-color:var(--teal);box-shadow:0 0 0 3px rgba(15,110,86,.13)}
.fld input[aria-invalid=true]{border-color:var(--alert);box-shadow:0 0 0 3px rgba(166,67,31,.13)}
.fld .err{font-size:.84rem;color:var(--alert);min-height:0}

/* consent row */
.consent{display:flex;gap:13px;align-items:flex-start;margin:4px 0 0;font-size:.97rem;color:var(--muted);line-height:1.55}
.consent input{
  flex:none;width:21px;height:21px;margin:2px 0 0;accent-color:var(--teal);cursor:pointer;
}
.consent a{color:var(--teal);text-underline-offset:3px}

/* ----------------------------------------------------------- the summary */
.sum{
  background:var(--teal-950);color:var(--cream);border-radius:18px;
  padding:clamp(22px,2.7vw,30px);position:relative;overflow:hidden;
  box-shadow:0 40px 80px -56px rgba(7,43,34,.9);
}
.sum::before{
  content:"";position:absolute;inset:0 0 auto 0;height:2px;
  background:linear-gradient(90deg,var(--amber),var(--amber-pale),transparent);
}
.sum-t{
  font-family:var(--mono);font-size:.78rem;font-weight:500;letter-spacing:.16em;text-transform:uppercase;
  color:var(--amber-pale);margin:0 0 18px;
  display:flex;justify-content:space-between;gap:8px 18px;align-items:baseline;flex-wrap:wrap;
}
.sum-t .ref{color:rgba(241,239,232,.5);letter-spacing:.05em;font-size:.74rem}
.sum-lines{list-style:none;margin:0;padding:0}
.sum-lines li{
  display:flex;justify-content:space-between;gap:16px;align-items:baseline;
  padding:11px 0;border-bottom:1px solid var(--line-dark);font-size:.98rem;
}
.sum-lines li:first-child{padding-top:0}
/* .sum-due draws its own top rule, so the last row must not draw one too */
.sum-lines li:last-child{border-bottom:0;padding-bottom:0}
.sum-lines .nm{color:rgba(241,239,232,.88);min-width:0}
.sum-lines .nm small{display:block;font-size:.8rem;color:rgba(241,239,232,.5);margin-top:3px;line-height:1.4}
.sum-lines .amt{font-family:var(--mono);font-variant-numeric:tabular-nums;white-space:nowrap;color:var(--cream)}
.sum-lines li.save .nm,.sum-lines li.save .amt{color:var(--amber-bright)}
.sum-lines li.total{border-bottom-color:rgba(241,239,232,.34)}
.sum-lines li.total .nm{
  font-family:var(--mono);font-size:.78rem;letter-spacing:.14em;text-transform:uppercase;
  color:var(--amber-pale);
}
.sum-lines li.total .amt{font-size:1.1rem}
.sum-lines li.later .amt,.sum-lines li.later .nm{color:rgba(241,239,232,.6)}
.sum-due{
  display:flex;justify-content:space-between;align-items:baseline;gap:16px;
  margin-top:18px;padding-top:18px;border-top:1px solid var(--line-dark);
}
.sum-due .k{font-family:var(--mono);font-size:.8rem;letter-spacing:.12em;text-transform:uppercase;color:var(--amber-pale)}
.sum-due .v{
  font-family:var(--display);font-weight:400;font-size:clamp(1.9rem,3.4vw,2.5rem);
  line-height:1;color:var(--cream);font-variant-numeric:tabular-nums;white-space:nowrap;
}
.sum-then{font-size:.9rem;color:rgba(241,239,232,.62);margin:12px 0 0;line-height:1.55}
.sum-note{
  font-size:.82rem;color:rgba(241,239,232,.5);margin:16px 0 0;padding-top:15px;
  border-top:1px solid var(--line-dark);line-height:1.6;
}
.sum-note b{color:rgba(241,239,232,.75);font-weight:500}

/* ------------------------------------------------------------- the action */
.act{margin-top:clamp(20px,2.4vw,28px)}
.act .btn{width:100%}
.act .undertext{font-size:.88rem;color:var(--muted);margin:12px 0 0;line-height:1.55;text-align:center}
.act .formerr{
  display:none;background:rgba(166,67,31,.09);border:1px solid rgba(166,67,31,.35);color:var(--alert);
  border-radius:10px;padding:12px 15px;font-size:.92rem;margin:0 0 14px;
}
.act .formerr.on{display:block}
.btn[aria-busy=true]{opacity:.72;pointer-events:none}

/* --------------------------------------------------------- trust strip */
.trust{display:grid;gap:11px;margin-top:clamp(20px,2.4vw,26px)}
.trust li{
  display:flex;gap:11px;align-items:flex-start;list-style:none;
  font-size:.9rem;color:var(--muted);line-height:1.5;
}
.trust svg{flex:none;width:17px;height:17px;fill:var(--teal);margin-top:2px}

/* ---------------------------------------------------- offline order panel */
.offline{
  display:none;margin-top:22px;background:var(--white);border:1px solid var(--line);
  border-left:3px solid var(--amber);border-radius:14px;padding:clamp(20px,2.6vw,26px);
}
.offline.on{display:block}
.offline h3{font-size:1.3rem;margin:0 0 10px}
.offline p{color:var(--muted);font-size:.98rem}
.offline .refbox{
  display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap;
  background:var(--panel);border:1px dashed var(--line);border-radius:10px;padding:13px 16px;margin:16px 0;
}
.offline .refbox b{font-family:var(--mono);font-size:1.05rem;color:var(--teal-950);letter-spacing:.06em}
.offline .refbox span{font-family:var(--mono);font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}

/* -------------------------------------------------------- mobile pay bar */
.paybar{
  position:fixed;left:0;right:0;bottom:0;z-index:70;display:none;
  align-items:center;justify-content:space-between;gap:14px;
  background:rgba(7,43,34,.97);backdrop-filter:blur(10px);color:var(--cream);
  padding:12px clamp(14px,4vw,20px);border-top:1px solid var(--line-dark);
  padding-bottom:calc(12px + env(safe-area-inset-bottom));
  transform:translateY(110%);transition:transform .35s var(--ease);
}
.paybar.up{transform:none}
.paybar .pb-k{font-family:var(--mono);font-size:.68rem;letter-spacing:.12em;text-transform:uppercase;color:var(--amber-pale);display:block}
.paybar .pb-v{font-family:var(--display);font-size:1.5rem;line-height:1.1;font-variant-numeric:tabular-nums}
.paybar .btn{padding:12px 20px;font-size:.95rem}

/* ------------------------------------------------------------ after-strip */
.after{counter-reset:a;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:clamp(16px,2vw,24px)}
.after div{position:relative;padding-top:44px}
.after div::before{
  counter-increment:a;content:"0" counter(a);position:absolute;top:0;left:0;
  font-family:var(--mono);font-size:.82rem;letter-spacing:.14em;color:var(--amber-text);
}
.after div::after{content:"";position:absolute;top:9px;left:34px;right:0;height:1px;background:var(--line)}
.after h3{font-size:1.14rem;margin:0 0 7px}
.after p{color:var(--muted);font-size:.95rem;margin:0;line-height:1.55}

/* ------------------------------------------------------------- env banner */
.envbar{
  background:var(--amber);color:var(--teal-950);font-family:var(--mono);font-size:.78rem;
  letter-spacing:.08em;text-align:center;padding:9px 16px;position:relative;z-index:81;
}

/* The Aiden launcher pins itself bottom-right and, when it looks for
   something to stack above, skips anything wider than 340px as "a bar, not a
   button" (avoidCorner in js/aiden-chat.js). A full-width pay bar is exactly
   that, so the launcher lands on top of the button. The bar lifts it instead
   of reserving a hole in itself - !important because avoidCorner writes
   --bottom as an inline style on every resize. */
html:has(.paybar.up) #aiden-root{--bottom:96px!important}

@media (max-width:960px){
  .co-grid{grid-template-columns:minmax(0,1fr)}
  .sum-wrap{position:static}
  .after{grid-template-columns:repeat(2,minmax(0,1fr))}
  .paybar{display:flex}
  /* the bar covers the last inch of the page, so give the footer room */
  body{padding-bottom:76px}
}
@media (max-width:560px){
  .flds{grid-template-columns:minmax(0,1fr)}
  .after{grid-template-columns:minmax(0,1fr)}
  .paybar .pb-v{font-size:1.25rem}
}
"""

LOCK = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2a5 5 0 0 0-5 5v3H6a2 2 0 0 0-2 2v8a2 '
        '2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8a2 2 0 0 0-2-2h-1V7a5 5 0 0 0-5-5zm0 2a3 3 0 0 1 3 3v3H9V7a3 3 0 '
        '0 1 3-3zm0 10a1.8 1.8 0 0 1 1 3.3V19a1 1 0 0 1-2 0v-1.7a1.8 1.8 0 0 1 1-3.3z"/></svg>')
DOC = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 2h8l6 6v14a0 0 0 0 1 0 0H6a2 2 0 0 '
       '1-2-2V4a2 2 0 0 1 2-2zm7 2v5h5l-5-5zM8 13h8v2H8v-2zm0 4h8v2H8v-2z"/></svg>')
SHIELD = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2l8 3v6c0 5-3.4 9.4-8 11-4.6-1.6-8-6-8-11V5l8-3zm'
          '-1.2 13.4 5.7-5.7-1.4-1.4-4.3 4.3-2-2-1.4 1.4 3.4 3.4z"/></svg>')
BACK = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5V1L7 6l5 5V7a6 6 0 1 1-6 6H4a8 8 0 1 0 8-8z"/></svg>')


# ---------------------------------------------------------------------------
# Markup helpers. Every card is generated from pay.CATALOG / pay.PLANS, so a
# new item or a new payment structure appears here without touching markup.
# ---------------------------------------------------------------------------
def _addon(i):
    """A toggleable build item."""
    return f"""      <label class="opt" data-kind="item">
        <input type="checkbox" name="item" value="{i['id']}">
        <span class="tick" aria-hidden="true"></span>
        <span class="opt-b">
          <span class="opt-h"><b>{i['name']}</b><span class="opt-p">+{pay.money(pay.price(i))}</span></span>
          <span class="opt-d">{i['blurb']}</span>
        </span>
      </label>"""


def _monthly(i):
    return f"""      <label class="opt" data-kind="item">
        <input type="checkbox" name="item" value="{i['id']}">
        <span class="tick" aria-hidden="true"></span>
        <span class="opt-b">
          <span class="opt-h"><b>{i['name']}</b><span class="opt-p">{pay.money(pay.price(i))}/month</span></span>
          <span class="opt-d">{i['blurb']} <b>Not charged today</b> &mdash; it starts the month after
            your site goes live, and is invoiced monthly.</span>
        </span>
      </label>"""


def _plan_card(p):
    """A payment structure. The figure on the right is what is due TODAY for
    the default configuration; the script rewrites it as items are toggled."""
    q = pay.quote([pay.BASE_ID], p["id"])
    if p["due"] == "zero":
        fig = "Nothing today"
    elif p["split"] > 1:
        fig = f"{pay.money(q['due'])} today"
    else:
        fig = f"{pay.money(q['due'])} today"
    flag = f'<span class="flag">{p["badge"]}</span>' if p.get("badge") else ""
    checked = " checked" if p.get("recommended") else ""
    return f"""      <label class="opt" data-kind="plan" data-plan="{p['id']}">
        <input type="radio" name="plan" value="{p['id']}"{checked}>
        <span class="tick" aria-hidden="true"></span>
        <span class="opt-b">
          <span class="opt-h"><b>{p['label']}{flag}</b><span class="opt-p" data-planfig="{p['id']}">{fig}</span></span>
          <span class="opt-d">{p['blurb']}</span>
        </span>
      </label>"""


def _default_summary():
    """The server-rendered order summary: the default configuration, correct
    with JavaScript switched off. The script replaces the whole list on its
    first run, so this markup is never the thing a scripted visitor sees - it
    is the floor under them, not the target."""
    q = pay.quote([pay.BASE_ID], "deposit")
    base = pay.item(pay.BASE_ID)
    return f"""        <li><span class="nm">{base['name']}</span><span class="amt">{pay.money(pay.price(base))}</span></li>
        <li class="later"><span class="nm">Balance after the deposit<small>Invoiced once your brief is confirmed</small></span><span class="amt">{pay.money(q['balance'])}</span></li>"""


def body():
    cfg = pay.CONFIG_JSON()
    base = pay.item(pay.BASE_ID)
    addons = [i for i in pay.CATALOG if i["kind"] == "build" and not i["required"]]
    monthlies = [i for i in pay.CATALOG if i["kind"] == "monthly"]
    q0 = pay.quote([pay.BASE_ID], "deposit")

    # The wording of the action changes entirely with the gateway switch, and
    # nothing about it is left to a CSS class - a disabled-looking button that
    # still says "Pay now" is exactly the lie this page must not tell.
    if pay.PAY_LIVE:
        btn_label = f"Pay {pay.money(q0['due'])} securely"
        under = ("You will finish on Thawani&#8217;s own secure page. Your card details are entered "
                 "there and never reach this site.")
    else:
        btn_label = "Reserve my slot"
        under = ("Card payments are being switched on. Until then your order is confirmed on "
                 "WhatsApp and the invoice follows &mdash; nothing is charged here.")

    envbar = ""
    if pay.PAY_LIVE and pay.THAWANI_ENV != "live":
        envbar = ('<div class="envbar">TEST MODE &mdash; payments run against Thawani UAT. '
                  'No real money moves.</div>')

    founding_note = ("Founding Partner pricing, held for the first capped group."
                     if pay.FOUNDING_OPEN else "Standard pricing.")

    return f"""<main id="main">
{envbar}
<header class="phero s-cream grain">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> Checkout &#183; {founding_note}</p>
    <h1 class="h1">Build it exactly<br>the way you need it.</h1>
    <p class="lede">Pick what you want built, choose how you want to pay for it, and the total on the
      right updates as you go. No hidden line appears at the end &mdash; what you see is the invoice.</p>
  </div>
</header>

<section class="s-cream grain" style="padding-top:0">
  <div class="wrap">
    <form id="coForm" class="co-grid" novalidate>

      <!-- ================================================= LEFT: the order -->
      <div>

        <div class="step">
          <p class="step-h"><span class="sn">01</span></p>
          <h2 class="h3" style="margin:0 0 6px">What you&#8217;re having built</h2>
          <p class="hint">The Smart Website is the foundation &mdash; the other two are built on top of it,
            and can be added later at the same price you see now.</p>

          <div class="opts">
            <span class="opt locked" data-kind="locked">
              <span class="tick" aria-hidden="true"></span>
              <span class="opt-b">
                <span class="opt-h"><b>{base['name']}<span class="flag">Included</span></b><span class="opt-p">{pay.money(pay.price(base))}</span></span>
                <span class="opt-d">{base['blurb']}</span>
              </span>
            </span>
{chr(10).join(_addon(i) for i in addons)}
          </div>

          <div class="bundle" id="bundleNote">
            <span class="star" aria-hidden="true">{STAR}</span>
            <span>All three together is <b>{pay.BUNDLE['name']}</b>, which is priced as one build rather
              than three &mdash; that is <b>{pay.money(pay.bundle_saving())} off</b> the parts, and it is
              already in the total on the right.</span>
          </div>

          <p class="hint" style="margin:26px 0 12px">And one optional thing that is <b>not</b> charged today:</p>
          <div class="opts">
{chr(10).join(_monthly(i) for i in monthlies)}
          </div>
        </div>

        <div class="step">
          <p class="step-h"><span class="sn">02</span></p>
          <h2 class="h3" style="margin:0 0 6px">How you&#8217;d like to pay for it</h2>
          <p class="hint">Same build in every row. The only difference is when the money moves.</p>
          <div class="opts">
{chr(10).join(_plan_card(p) for p in pay.PLANS)}
          </div>
        </div>

        <div class="step">
          <p class="step-h"><span class="sn">03</span></p>
          <h2 class="h3" style="margin:0 0 6px">Who I&#8217;m building it for</h2>
          <p class="hint">Enough to raise the invoice and start the brief. Nothing here is used for marketing.</p>

          <div class="flds">
            <div class="fld">
              <label for="f-name">Your name</label>
              <input id="f-name" name="name" type="text" autocomplete="name" required placeholder="Your name">
              <span class="err" data-for="name"></span>
            </div>
            <div class="fld">
              <label for="f-biz">Business name</label>
              <input id="f-biz" name="business" type="text" autocomplete="organization" required placeholder="Gulf Lotus Trading LLC">
              <span class="err" data-for="business"></span>
            </div>
            <div class="fld">
              <label for="f-email">Email <span class="opt-tag">&mdash; your receipt goes here</span></label>
              <input id="f-email" name="email" type="email" autocomplete="email" required placeholder="you@company.om" inputmode="email">
              <span class="err" data-for="email"></span>
            </div>
            <div class="fld">
              <label for="f-wa">WhatsApp number</label>
              <input id="f-wa" name="whatsapp" type="tel" autocomplete="tel" required placeholder="+968 &hellip;" inputmode="tel">
              <span class="err" data-for="whatsapp"></span>
            </div>
            <div class="fld">
              <label for="f-cr">CR number <span class="opt-tag">&mdash; optional, for the invoice</span></label>
              <input id="f-cr" name="cr" type="text" placeholder="1234567" inputmode="numeric">
            </div>
            <div class="fld">
              <label for="f-city">City</label>
              <input id="f-city" name="city" type="text" autocomplete="address-level2" placeholder="Muscat">
            </div>
            <div class="fld full">
              <label for="f-notes">Anything I should know before the brief call <span class="opt-tag">&mdash; optional</span></label>
              <textarea id="f-notes" name="notes" placeholder="What you sell, how buyers reach you today, and the one thing that is costing you money."></textarea>
            </div>
          </div>
        </div>

        <div class="step">
          <p class="step-h"><span class="sn">04</span></p>
          <h2 class="h3" style="margin:0 0 14px">Confirm and send</h2>

          <label class="consent">
            <input type="checkbox" name="agree" id="f-agree" required>
            <span>I have read the <a href="/terms/" target="_blank" rel="noopener">Terms of Service</a> and the
              <a href="/refund-policy/" target="_blank" rel="noopener">Refund &amp; Cancellation Policy</a>, and I
              understand what is included in this build and what is not.</span>
          </label>

          <div class="act">
            <p class="formerr" id="formErr" role="alert"></p>
            <button class="btn btn-teal" type="submit" id="payBtn">{LOCK}<span id="payLabel">{btn_label}</span></button>
            <p class="undertext" id="payUnder">{under}</p>
          </div>

          <div class="offline" id="offlinePanel" role="status" aria-live="polite">
            <h3>Your order is ready to send.</h3>
            <p id="offlineWhy">Card payments are being switched on, so this last step happens on WhatsApp:
              press the button and the whole order below goes to me in one message. I confirm it, send the
              invoice and the transfer details, and your slot is held from that moment.</p>
            <div class="refbox">
              <span>Your reference</span>
              <b id="offlineRef">&mdash;</b>
            </div>
            <div class="btn-row">
              <a class="btn btn-wa" id="offlineWa" href="{WA}" target="_blank" rel="noopener">{WA_ICON}Send my order on WhatsApp</a>
              <a class="btn btn-ghost" id="offlineMail" href="mailto:hello@aiprofitlab.io">Email it instead</a>
            </div>
          </div>

          <noscript>
            <div class="offline on" style="margin-top:20px">
              <h3>Order without JavaScript</h3>
              <p>This page adds up your order in the browser, which needs JavaScript. Message
                <a href="{WA}">+968 9924 5250</a> on WhatsApp or email
                <a href="mailto:hello@aiprofitlab.io">hello@aiprofitlab.io</a> with what you want built and
                I will send you the invoice by return. The prices on the right are the real ones either way.</p>
            </div>
          </noscript>
        </div>

      </div>

      <!-- ============================================== RIGHT: the summary -->
      <div class="sum-wrap">
        <aside class="sum" aria-label="Order summary">
          <!-- Deliberately NOT an <h2>. The shared motion script wraps the
               children of every `section h2` in one .wi span to run its reveal
               wipe, which turns this flex row into a single flex child and
               glues "Your order" onto the reference. role=heading keeps the
               semantics without matching that selector. -->
          <p class="sum-t" role="heading" aria-level="2"><span>Your order</span><span class="ref" id="refTag"></span></p>

          <ul class="sum-lines" id="sumLines">
{_default_summary()}
          </ul>

          <div class="sum-due">
            <span class="k" id="dueKey">Due today</span>
            <b class="v" id="dueVal">{pay.money(q0['due'])}</b>
          </div>
          <p class="sum-then" id="sumThen">The remaining {pay.money(q0['balance'])} is invoiced once your
            brief is confirmed, and comes off nothing you have already paid.</p>

          <p class="sum-note">
            <b>No VAT is added.</b> Lotus Gulf International is below Oman&#8217;s registration threshold,
            so the figure above is the figure on the invoice.<br>
            Charged in Omani Rial by <b>Lotus Gulf International</b>, CR <span dir="ltr">1570092</span>,
            trading as AI Profit Lab.
          </p>
        </aside>

        <ul class="trust">
          <li>{LOCK}<span>Your card details are entered on the payment provider&#8217;s own page. They are never
            typed into, sent to, or stored by this site.</span></li>
          <li>{BACK}<span>Cancel before I start building and you get everything back &mdash;
            <a href="/refund-policy/">the refund policy</a> says exactly when and how much.</span></li>
          <li>{SHIELD}<span>The First Inquiry Promise: no real buyer inquiry within 30 days of going live
            and I rebuild it free. Still nothing, and you get your money back.</span></li>
          <li>{DOC}<span>An itemised invoice from a registered Omani company, not a payment link from
            a stranger.</span></li>
        </ul>
      </div>

    </form>
  </div>
</section>

<!-- ==================================================== WHAT HAPPENS NEXT -->
<section class="s-panel">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> After you press the button</p>
    <h2 class="h2">Four things happen, in this order.</h2>

    <div class="after" style="margin-top:clamp(26px,3.5vw,44px)" data-stagger>
      <div>
        <h3>You get a receipt</h3>
        <p>Emailed within minutes, with your reference and an itemised invoice from Lotus Gulf International.</p>
      </div>
      <div>
        <h3>I call you</h3>
        <p>Within one business day, to take the brief properly. Nothing is built off a form alone.</p>
      </div>
      <div>
        <h3>You watch it get built</h3>
        <p>A working link from the first week, updated as it goes. You are never shown a finished thing you
          have not already seen.</p>
      </div>
      <div>
        <h3>It goes live</h3>
        <p>And the 30-day First Inquiry Promise starts counting from that day, not from the day you paid.</p>
      </div>
    </div>
  </div>
</section>

<!-- ============================================================ QUESTIONS -->
<section class="s-dark pad-s">
  <div class="wrap">
    <div style="display:flex;gap:clamp(20px,4vw,50px);align-items:center;justify-content:space-between;flex-wrap:wrap">
      <div style="flex:1 1 400px">
        <h2 class="h2" style="margin-bottom:12px">Not ready to pay for anything yet?</h2>
        <p class="lede" style="margin:0">Reasonable. Start with the free one instead: I message your business
          the way a buyer would and send you the scorecard. You keep it either way, and there is no pitch attached.</p>
      </div>
      <div class="btn-row">
        <a class="btn btn-amber" href="/en/contact-v4/#test">Get the Silent Buyer Test</a>
        <a class="btn btn-ghost" href="/en/services-v4/#price">See the full price list</a>
      </div>
    </div>
  </div>
</section>

<div class="paybar" id="payBar" aria-hidden="true">
  <span><span class="pb-k" id="barKey">Due today</span><span class="pb-v" id="barVal">{pay.money(q0['due'])}</span></span>
  <button class="btn btn-teal" type="submit" form="coForm" id="barBtn">Reserve</button>
</div>

<script type="application/json" id="payCfg">{cfg}</script>
</main>
"""


JS = r"""
/* ---------------------------------------------------------------------------
   Checkout engine.

   The pricing table arrives as JSON in #payCfg, generated from tools/v4/pay.py.
   quote() below is a direct port of pay.quote() - if one changes, change both;
   `python3 tools/v4/pay.py` re-checks every published figure against the Python
   side, and tools/build_v4.py re-checks them against the services page.

   MONEY IS INTEGER BAISA. 1 OMR = 1000 baisa. Nothing here divides into a
   float and formats it later: instalments are floored to whole rials and the
   remainder is carried by the first payment, so the parts always sum to the
   total exactly. A checkout that is one baisa out is a checkout nobody trusts.
--------------------------------------------------------------------------- */
(function(){
  "use strict";
  var cfgEl = document.getElementById("payCfg");
  var form  = document.getElementById("coForm");
  if (!cfgEl || !form) return;

  var CFG;
  try { CFG = JSON.parse(cfgEl.textContent); } catch(e){ return; }

  var $ = function(id){ return document.getElementById(id); };

  /* ------------------------------------------------------------- money --- */
  function omr(b){
    var w = Math.floor(b / CFG.baisa), r = b % CFG.baisa;
    var s = w.toLocaleString("en-US");
    if (r) s += "." + ("00" + r).slice(-3);
    return s;
  }
  function money(b){ return CFG.currency + " " + omr(b); }

  function planById(id){
    for (var i = 0; i < CFG.plans.length; i++) if (CFG.plans[i].id === id) return CFG.plans[i];
    return CFG.plans[0];
  }

  /* -------------------------------------------------------- the quote ---
     Port of pay.quote(). Keep the branch names identical to the Python so the
     two read as the same function.                                          */
  function quote(sel, planId){
    var plan = planById(planId), build = [], monthly = [], i;
    for (i = 0; i < CFG.items.length; i++){
      var it = CFG.items[i], on = it.required || sel.indexOf(it.id) >= 0;
      if (!on) continue;
      (it.kind === "build" ? build : monthly).push(it);
    }
    var parts = 0, ids = [];
    for (i = 0; i < build.length; i++){ parts += build[i].price; ids.push(build[i].id); }

    var bundled = true;
    for (i = 0; i < CFG.bundle.requires.length; i++){
      if (ids.indexOf(CFG.bundle.requires[i]) < 0) bundled = false;
    }
    var subtotal = bundled ? CFG.bundle.price : parts;
    var total = subtotal + plan.surcharge, due;

    if (plan.due === "deposit")   due = Math.min(CFG.deposit, total);
    else if (plan.due === "total") due = total;
    else if (plan.due === "first"){
      var per = Math.floor(Math.floor(total / plan.split) / CFG.baisa) * CFG.baisa;
      due = total - per * (plan.split - 1);
    }
    else due = 0;

    return {
      build: build, monthly: monthly, bundled: bundled,
      parts: parts, subtotal: subtotal, saving: parts - subtotal,
      surcharge: plan.surcharge, total: total,
      due: due, balance: total - due,
      later: plan.split > 1 ? (total - due) / (plan.split - 1) : 0,
      plan: plan
    };
  }

  /* -------------------------------------------------------- reference ---
     A human-readable handle the buyer can quote back on WhatsApp. The server
     issues the authoritative one once the gateway is live; this is what holds
     the order together until then, and what a cancelled payment comes back to.
     Ambiguous glyphs (0/O, 1/I) are left out of the alphabet on purpose - this
     gets read down a phone line.                                             */
  function newRef(){
    var d = new Date(), p = function(n){ return ("0" + n).slice(-2); };
    var stamp = String(d.getFullYear()).slice(2) + p(d.getMonth() + 1) + p(d.getDate());
    var abc = "ACDEFGHJKLMNPQRTUVWXY2346789", out = "";
    var rnd = new Uint8Array(4);
    if (window.crypto && crypto.getRandomValues) crypto.getRandomValues(rnd);
    else for (var i = 0; i < 4; i++) rnd[i] = Math.floor(Math.random() * 256);
    for (var j = 0; j < 4; j++) out += abc.charAt(rnd[j] % abc.length);
    return "APL-" + stamp + "-" + out;
  }

  var STORE = "apl_order";
  var ref = null;
  function reference(){
    if (!ref) ref = newRef();
    return ref;
  }

  /* ------------------------------------------------------------ state --- */
  function selected(){
    var out = [];
    form.querySelectorAll("input[name=item]:checked").forEach(function(el){ out.push(el.value); });
    return out;
  }
  function currentPlan(){
    var el = form.querySelector("input[name=plan]:checked");
    return el ? el.value : CFG.plans[0].id;
  }

  /* ----------------------------------------------------------- render --- */
  var lines = $("sumLines"), dueVal = $("dueVal"), dueKey = $("dueKey"), thenP = $("sumThen");
  var barVal = $("barVal"), barKey = $("barKey"), barBtn = $("barBtn");
  var payLabel = $("payLabel"), payUnder = $("payUnder"), bundleNote = $("bundleNote");

  function li(name, amount, cls, sub){
    var l = document.createElement("li");
    if (cls) l.className = cls;
    var n = document.createElement("span"); n.className = "nm"; n.appendChild(document.createTextNode(name));
    if (sub){ var s = document.createElement("small"); s.textContent = sub; n.appendChild(s); }
    var a = document.createElement("span"); a.className = "amt"; a.textContent = amount;
    l.appendChild(n); l.appendChild(a);
    return l;
  }

  function render(){
    var sel = selected(), q = quote(sel, currentPlan()), i;

    /* ---- the itemised list ---- */
    lines.textContent = "";
    for (i = 0; i < q.build.length; i++){
      lines.appendChild(li((i ? "+ " : "") + q.build[i].name, money(q.build[i].price)));
    }
    if (q.saving > 0){
      lines.appendChild(li(CFG.bundle.name + " — priced as one build", "−" + money(q.saving), "save"));
    }
    if (q.surcharge > 0){
      lines.appendChild(li(
        q.plan.id === "three" ? "Paying in three" : "Paying only on proof",
        "+" + money(q.surcharge)));
    }
    lines.appendChild(li("Total", money(q.total), "total"));
    for (i = 0; i < q.monthly.length; i++){
      lines.appendChild(li(q.monthly[i].name, money(q.monthly[i].price) + "/mo", "later",
        "From the month after go-live. Not charged today, cancel any month."));
    }

    /* ---- the number that matters ---- */
    dueVal.textContent = money(q.due);
    if (barVal) barVal.textContent = money(q.due);
    var key = q.plan.due === "zero" ? "Due today" : "Due today";
    dueKey.textContent = key;
    if (barKey) barKey.textContent = key;

    /* ---- and what happens to the rest of it ---- */
    var then;
    if (q.plan.due === "zero"){
      then = "Nothing is charged now. The full " + money(q.total) + " is invoiced only after your site "
           + "has produced its first real, verifiable buyer inquiry — and if it never does, it is "
           + "never invoiced.";
    } else if (q.plan.split > 1){
      then = "Then " + money(q.later) + " when it goes live, and " + money(q.later)
           + " thirty days after that. " + money(q.total) + " in total, and nothing after it.";
    } else if (q.balance > 0){
      then = "The remaining " + money(q.balance) + " is invoiced once your brief is confirmed. Your "
           + money(q.due) + " comes off it — it is a deposit, not a fee.";
    } else {
      then = "That is the whole build, paid once. No monthly fee is required to keep any of it running.";
    }
    if (q.monthly.length){
      then += " " + q.monthly[0].name + " starts separately, the month after go-live.";
    }
    thenP.textContent = then;

    /* ---- each payment structure's own headline ---- */
    for (i = 0; i < CFG.plans.length; i++){
      var p = CFG.plans[i], tag = form.querySelector('[data-planfig="' + p.id + '"]');
      if (!tag) continue;
      var pq = quote(sel, p.id);
      tag.textContent = p.due === "zero" ? "Nothing today" : money(pq.due) + " today";
    }

    if (bundleNote) bundleNote.classList.toggle("on", q.bundled);

    /* ---- the button says what will actually happen ---- */
    var canCard = CFG.live && CFG.api && q.plan.card;
    if (canCard){
      payLabel.textContent = "Pay " + money(q.due) + " securely";
      if (barBtn) barBtn.textContent = "Pay " + money(q.due);
    } else if (CFG.live && !q.plan.card){
      payLabel.textContent = "Send my order";
      if (barBtn) barBtn.textContent = "Send order";
      payUnder.innerHTML = "Nothing is charged on Pay on Proof terms. I confirm the order and the "
        + "agreement follows — the invoice only comes after your first real inquiry.";
    } else {
      payLabel.textContent = "Reserve my slot";
      if (barBtn) barBtn.textContent = "Reserve";
    }

    save(sel, q);
    return q;
  }

  /* Kept so a cancelled or abandoned payment can be walked back into. */
  function save(sel, q){
    try {
      localStorage.setItem(STORE, JSON.stringify({
        ref: reference(), items: sel, plan: currentPlan(), due: q.due, total: q.total,
        at: Date.now()
      }));
    } catch(e){}
  }

  /* -------------------------------------------------- restore / deeplink ---
     ?plan=full&items=dashboard,autopilot preselects a configuration - the
     price-list buttons on the services page use it. ?restore=1 comes back from
     a cancelled payment and reinstates whatever was on screen.               */
  (function preset(){
    var qs = new URLSearchParams(location.search), items = null, planId = null;
    if (qs.get("restore")){
      try {
        var saved = JSON.parse(localStorage.getItem(STORE) || "null");
        if (saved){ items = saved.items || []; planId = saved.plan; ref = saved.ref || null; }
      } catch(e){}
    }
    if (qs.get("items") !== null) items = qs.get("items").split(",");
    if (qs.get("plan")) planId = qs.get("plan");

    if (items){
      form.querySelectorAll("input[name=item]").forEach(function(el){
        el.checked = items.indexOf(el.value) >= 0;
      });
    }
    if (planId){
      var el = form.querySelector('input[name=plan][value="' + planId.replace(/"/g, "") + '"]');
      if (el) el.checked = true;
    }
  })();

  var refTag = $("refTag");
  if (refTag) refTag.textContent = reference();

  /* ------------------------------------------------------ interaction --- */
  var started = false;
  form.addEventListener("change", function(e){
    if (!started && typeof gtag === "function"){
      started = true;
      gtag("event", "begin_checkout", {currency: CFG.currency});
    }
    render();
    if (e.target.name === "plan" && typeof gtag === "function"){
      gtag("event", "add_payment_info", {payment_type: e.target.value});
    }
  });

  /* ------------------------------------------------------- validation --- */
  var REQUIRED = ["name", "business", "email", "whatsapp"];
  function fieldErr(nm, msg){
    var el = form.elements[nm];
    var slot = form.querySelector('.err[data-for="' + nm + '"]');
    if (el) el.setAttribute("aria-invalid", msg ? "true" : "false");
    if (slot) slot.textContent = msg || "";
    return !msg;
  }
  function validate(){
    var ok = true, first = null, i;
    for (i = 0; i < REQUIRED.length; i++){
      var nm = REQUIRED[i], v = (form.elements[nm].value || "").trim();
      var msg = v ? "" : "I need this one.";
      if (!msg && nm === "email" && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v)){
        msg = "That address does not look complete.";
      }
      if (!msg && nm === "whatsapp" && v.replace(/[^\d]/g, "").length < 8){
        msg = "A number I can actually reach you on, please.";
      }
      if (msg){ ok = false; first = first || form.elements[nm]; }
      fieldErr(nm, msg);
    }
    var box = $("formErr");
    if (!form.elements.agree.checked){
      ok = false;
      box.textContent = "Please confirm you have read the terms and the refund policy — it is the "
                      + "one box I cannot tick for you.";
      box.classList.add("on");
      first = first || form.elements.agree;
    } else if (ok){
      box.classList.remove("on");
    } else {
      box.textContent = "A few details are missing below.";
      box.classList.add("on");
    }
    if (first){
      first.focus();
      first.scrollIntoView({block: "center", behavior: "smooth"});
    }
    return ok;
  }
  form.addEventListener("input", function(e){
    if (REQUIRED.indexOf(e.target.name) >= 0 && e.target.getAttribute("aria-invalid") === "true"){
      fieldErr(e.target.name, "");
    }
  });

  /* ------------------------------------------------------ the payload ---
     One shape, whether it goes to the gateway API or into a WhatsApp message.
     Documented in docs/payments-api.md - the server re-prices it from its own
     copy of the table and NEVER trusts the amounts in here.                  */
  function order(q){
    var g = function(n){ return (form.elements[n].value || "").trim(); };
    return {
      reference: reference(),
      items: selected(),
      plan: currentPlan(),
      founding: CFG.founding,
      currency: CFG.currency,
      /* quoted_* is what the buyer was shown. The server recomputes and, if it
         disagrees, refuses the session rather than quietly charging its own
         number - a mismatch is a bug worth stopping for. */
      quoted_due: q.due,
      quoted_total: q.total,
      customer: {
        name: g("name"), business: g("business"), email: g("email"),
        whatsapp: g("whatsapp"), cr: g("cr"), city: g("city"), notes: g("notes")
      },
      page: location.pathname + location.search
    };
  }

  function summaryText(q){
    var out = ["Hello Nahid — here is my order.", "", "Reference: " + reference(), ""];
    for (var i = 0; i < q.build.length; i++){
      out.push("• " + q.build[i].name + " — " + money(q.build[i].price));
    }
    if (q.saving > 0) out.push("• " + CFG.bundle.name + " — " + money(q.saving) + " off the parts");
    if (q.surcharge > 0) out.push("• " + q.plan.label + " — adds " + money(q.surcharge));
    for (i = 0; i < q.monthly.length; i++){
      out.push("• " + q.monthly[i].name + " — " + money(q.monthly[i].price) + "/month from go-live");
    }
    out.push("", "Total: " + money(q.total));
    out.push(q.plan.due === "zero" ? "Terms: " + q.plan.label + ", nothing due now"
                                   : "Due now: " + money(q.due) + " (" + q.plan.label + ")");
    var g = function(n){ return (form.elements[n].value || "").trim(); };
    out.push("", "Name: " + g("name"), "Business: " + g("business"), "Email: " + g("email"),
             "WhatsApp: " + g("whatsapp"));
    if (g("cr")) out.push("CR: " + g("cr"));
    if (g("city")) out.push("City: " + g("city"));
    if (g("notes")) out.push("", "Notes: " + g("notes"));
    return out.join("\n");
  }

  /* --------------------------------------------------- offline handover --- */
  function offline(q, why){
    var panel = $("offlinePanel");
    $("offlineRef").textContent = reference();
    if (why) $("offlineWhy").textContent = why;
    var text = summaryText(q);
    $("offlineWa").href = "https://api.whatsapp.com/send?phone=96899245250&text=" + encodeURIComponent(text);
    $("offlineMail").href = "mailto:hello@aiprofitlab.io?subject=" + encodeURIComponent("Order " + reference())
                          + "&body=" + encodeURIComponent(text);
    panel.classList.add("on");
    panel.scrollIntoView({block: "nearest", behavior: "smooth"});
    if (typeof gtag === "function"){
      gtag("event", "generate_lead", {method: "checkout_offline", value: q.due / CFG.baisa,
                                      currency: CFG.currency});
    }
  }

  /* -------------------------------------------------------- submission --- */
  var btn = $("payBtn");
  form.addEventListener("submit", function(e){
    e.preventDefault();
    if (!validate()) return;
    var q = render();
    var canCard = CFG.live && CFG.api && q.plan.card;

    if (!canCard){ offline(q, null); return; }

    btn.setAttribute("aria-busy", "true");
    $("payLabel").textContent = "Opening secure payment…";

    /* One attempt, settled exactly once - by the response, by a refusal, or by
       the timeout, whichever gets there first.

       An earlier version raised the "settled" flag BEFORE throwing on a refused
       order, which meant the catch that was supposed to handle the refusal saw
       the attempt as already handled and returned. A 502 from the gateway left
       the button spinning "Opening secure payment…" for ever, with no way
       forward and nothing said. Settle in one place, and only in one place. */
    var settled = false;
    function settle(){
      if (settled) return false;
      settled = true;
      clearTimeout(give_up);
      return true;
    }
    function abandon(why){
      btn.removeAttribute("aria-busy");
      render();
      offline(q, "The card payment could not be started (" + why + "), so nothing was charged. "
               + "Send the order across instead and I will follow it up with a payment link.");
    }

    var give_up = setTimeout(function(){
      if (!settle()) return;
      abandon("the gateway did not answer in time");
    }, 15000);

    fetch(CFG.api + "/session", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(order(q))
    }).then(function(r){
      return r.json().then(function(d){ return {ok: r.ok, body: d}; },
                          function(){ return {ok: false, body: null}; });
    }).then(function(res){
      if (!settle()) return;
      if (res.ok && res.body && res.body.redirect_url){
        try { localStorage.setItem(STORE, JSON.stringify({
          ref: res.body.reference || reference(), items: selected(), plan: currentPlan(),
          due: q.due, total: q.total, session: res.body.session_id || null, at: Date.now()
        })); } catch(err){}
        location.href = res.body.redirect_url;
        return;
      }
      abandon((res.body && res.body.message) || "the gateway refused the order");
    }).catch(function(err){
      if (!settle()) return;
      abandon(err && err.message ? err.message : "unknown error");
    });
  });

  /* ---------------------------------------------------- mobile pay bar ---
     On a phone the summary is not a sidebar - the single-column stack puts it
     BELOW the four steps, so for the whole time the buyer is filling the form
     the running total is off-screen underneath them. The bar is that total,
     brought back: it rises while the form is in view and stands down again the
     moment the real summary is on screen, so the two never show at once.

     An early version watched only the summary and asked whether it had scrolled
     off the TOP - true for a sticky sidebar, never true for a stack where the
     summary is the last thing on the page, so the bar never appeared at all. */
  var bar = $("payBar"), sum = document.querySelector(".sum");
  if (bar){
    var setBar = function(up){
      bar.classList.toggle("up", up);
      bar.setAttribute("aria-hidden", up ? "false" : "true");
      if (up) bar.removeAttribute("inert"); else bar.setAttribute("inert", "");
    };
    setBar(false);
    if ("IntersectionObserver" in window && sum){
      var formIn = false, sumIn = false;
      var watch = function(el, set){
        new IntersectionObserver(function(en){
          set(en[0].isIntersecting);
          setBar(formIn && !sumIn);
        }, {threshold: 0}).observe(el);
      };
      watch(form, function(v){ formIn = v; });
      watch(sum,  function(v){ sumIn = v; });
    }
  }

  render();
})();
"""


META = dict(
    slug="checkout-v4",
    title="Checkout | AI Profit Lab — build it the way you need it",
    desc=("Choose what gets built, choose how you pay for it, and see the total before you commit. "
          "Priced in OMR by Lotus Gulf International, CR 1570092, Muscat."),
    nav="/en/services-v4/",
    next=("Any last questions?", "Talk to the person who builds it", "/en/contact-v4/"),
    schema="""{
  "@context":"https://schema.org",
  "@type":"CheckoutPage",
  "name":"AI Profit Lab checkout",
  "provider":{
    "@type":"Organization",
    "name":"AI Profit Lab",
    "legalName":"Lotus Gulf International",
    "identifier":"CR 1570092",
    "address":{"@type":"PostalAddress","addressLocality":"Bousher","addressRegion":"Muscat","addressCountry":"OM"},
    "email":"hello@aiprofitlab.io",
    "telephone":"+968-9924-5250"
  }
}""",
)
