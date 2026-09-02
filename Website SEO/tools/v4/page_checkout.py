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

Deep links: /en/checkout/?plan=full&items=dashboard,autopilot preselects a
configuration, which is what the buttons on the services page use.
"""
import pay
from kit import WA, WA_ICON, STAR, SHIELD

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
/* --------------------------------------------------- the pledge row
   One row on this page is accepted in the buyer's own words rather than
   picked off a shelf, so the sentence is the label and the product name sits
   above it as the header. The statement panel is deliberately symmetric - no
   left border, no directional padding - so it needs nothing from rtl.py and
   cannot mirror wrongly on the Arabic checkout. */
.opt-say .say{
  display:block;margin-top:10px;padding:13px 15px;border-radius:10px;
  background:var(--panel-2);color:var(--teal-950);font-size:1.02rem;line-height:1.6;
}
.opt-say:has(input:checked) .say{background:rgba(15,110,86,.09)}
.opt-say .opt-d{margin-top:10px}

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

/* ==================================================== the upsell interstitial
   Shown once, between "pay" and the card page. A real <dialog> so the browser
   supplies the modal semantics, the focus trap and Escape for free - none of
   which are worth reimplementing badly on the one page that handles money.

   Escape and backdrop-dismiss are NOT blocked. A modal you cannot get out of
   in front of a card page is how a paying buyer becomes an abandoned cart;
   every exit from this thing lands on "continue without it".                */
.up-dlg{
  border:0;padding:0;background:transparent;max-width:min(760px,calc(100vw - 28px));width:100%;
  max-height:calc(100dvh - 28px);overflow:visible;color:var(--ink);
}
.up-dlg::backdrop{background:rgba(7,43,34,.62);backdrop-filter:blur(3px)}
.up-card{
  background:var(--cream);border-radius:18px;overflow:hidden;
  max-height:calc(100dvh - 28px);display:flex;flex-direction:column;
  box-shadow:0 50px 100px -40px rgba(7,43,34,.75);
}
.up-scroll{overflow-y:auto;overscroll-behavior:contain;-webkit-overflow-scrolling:touch}

/* --- the head ---------------------------------------------------------- */
/* position:relative is load-bearing. .up-x is absolute, and with no positioned
   ancestor it anchors to the <dialog> itself - which does not scroll - so the
   close cross hangs in the top corner over whatever text is passing beneath
   it. Anchored here it scrolls away with the header, as it should; the
   sticky footer keeps a way out on screen at all times anyway. */
.up-head{
  position:relative;background:var(--teal-950);color:var(--cream);
  padding:clamp(22px,3.4vw,32px) clamp(20px,3.4vw,36px);
}
/* the eyebrow is the only line long enough to reach the close cross */
.up-head .eyebrow{color:var(--amber-bright);margin:0 0 12px;font-size:.74rem;padding-inline-end:44px}
.up-head h2{
  font-family:var(--display);font-weight:400;color:var(--cream);margin:0;
  font-size:clamp(1.36rem,3.1vw,1.95rem);line-height:1.2;
}
.up-head p{margin:12px 0 0;color:rgba(241,239,232,.82);font-size:1rem;line-height:1.6}

/* --- the body ---------------------------------------------------------- */
.up-body{padding:clamp(20px,3.4vw,34px) clamp(20px,3.4vw,36px) 4px}
.up-body h3{
  font-family:var(--display);font-weight:400;color:var(--teal-950);
  font-size:1.16rem;margin:0 0 6px;line-height:1.3;
}
.up-body p{margin:0 0 15px;font-size:1rem;line-height:1.68;color:var(--ink)}
.up-body p.sub{color:var(--muted);font-size:.95rem}
.up-def{
  border-inline-start:3px solid var(--amber-pale);padding-inline-start:16px;margin:0 0 22px;
}
.up-def:last-of-type{margin-bottom:6px}
.up-rule{height:1px;background:var(--line);margin:22px 0}

/* the "already built in" list */
.up-have{background:var(--panel-2);border-radius:14px;padding:18px 20px;margin:0 0 18px}
.up-have p{margin:0 0 10px;font-size:.95rem}
.up-have ul{margin:0;padding:0;list-style:none;display:grid;gap:7px}
.up-have li{
  position:relative;padding-inline-start:26px;font-size:.93rem;color:var(--muted);line-height:1.5;
}
.up-have li::before{
  content:"";position:absolute;inset-inline-start:2px;top:.52em;
  width:10px;height:6px;border-inline-start:2px solid var(--teal);border-bottom:2px solid var(--teal);
  transform:rotate(-45deg);
}

/* --- the price block --------------------------------------------------- */
.up-offer{
  background:var(--teal-950);color:var(--cream);border-radius:16px;
  padding:clamp(20px,3vw,26px);margin:4px 0 18px;
}
.up-offer .nm{
  font-family:var(--mono);font-size:.7rem;letter-spacing:.15em;text-transform:uppercase;
  color:var(--amber-bright);margin:0 0 10px;display:block;
}
.up-figs{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;margin:0 0 10px}
.up-now{
  font-family:var(--display);font-size:clamp(1.9rem,5vw,2.5rem);line-height:1;color:var(--cream);
}
.up-now .per{font-family:var(--sans);font-size:.94rem;color:rgba(241,239,232,.72)}
.up-was{
  font-family:var(--mono);font-size:1rem;color:rgba(241,239,232,.6);text-decoration:line-through;
  text-decoration-thickness:1.5px;
}
.up-offer .note{margin:0;font-size:.9rem;color:rgba(241,239,232,.75);line-height:1.55}

/* --- the guarantee ----------------------------------------------------- */
.up-gtee{
  border:1.5px solid var(--teal);border-radius:14px;padding:20px;margin:0 0 18px;background:var(--white);
  display:flex;gap:15px;align-items:flex-start;
}
.up-gtee svg{flex:none;width:30px;height:30px;fill:var(--teal);margin-top:1px}
.up-gtee h3{margin:0 0 5px}
.up-gtee p{margin:0;font-size:.95rem;line-height:1.6}
.up-gtee .fine{margin-top:9px;font-size:.85rem;color:var(--muted);line-height:1.55}

/* --- the scarcity line ------------------------------------------------- */
.up-only{
  background:#FBF3E4;border:1px solid #E8CE9C;border-radius:12px;
  padding:15px 18px;margin:0 0 20px;font-size:.96rem;line-height:1.6;color:#6E4E0E;
}
.up-only b{color:#5A3F09}

/* --- the actions ------------------------------------------------------- */
.up-act{
  padding:18px clamp(20px,3.4vw,36px) clamp(20px,3.4vw,26px);
  background:var(--cream);border-top:1px solid var(--line);
  position:sticky;bottom:0;display:grid;gap:11px;
}
.up-act .btn{width:100%}
.up-no{
  background:none;border:0;font-family:var(--sans);font-size:.95rem;color:var(--muted);
  text-decoration:underline;text-underline-offset:3px;cursor:pointer;padding:6px;line-height:1.5;
}
.up-no:hover{color:var(--ink)}
.up-x{
  position:absolute;inset-inline-end:12px;top:12px;width:36px;height:36px;border:0;border-radius:50%;
  background:rgba(241,239,232,.14);color:var(--cream);font-size:1.1rem;line-height:1;cursor:pointer;
  display:grid;place-items:center;
}
.up-x:hover{background:rgba(241,239,232,.26)}

@media (max-width:560px){
  .up-dlg{max-width:100vw;max-height:100dvh;margin:0;height:100dvh}
  .up-card{border-radius:0;max-height:100dvh;height:100dvh}
  .up-gtee{flex-direction:column;gap:10px}
}
@media (prefers-reduced-motion:no-preference){
  .up-dlg[open]{animation:upIn .34s var(--ease)}
  @keyframes upIn{from{opacity:0;transform:translateY(14px) scale(.985)}to{opacity:1;transform:none}}
}
"""

LOCK = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2a5 5 0 0 0-5 5v3H6a2 2 0 0 0-2 2v8a2 '
        '2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8a2 2 0 0 0-2-2h-1V7a5 5 0 0 0-5-5zm0 2a3 3 0 0 1 3 3v3H9V7a3 3 0 '
        '0 1 3-3zm0 10a1.8 1.8 0 0 1 1 3.3V19a1 1 0 0 1-2 0v-1.7a1.8 1.8 0 0 1 1-3.3z"/></svg>')
DOC = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 2h8l6 6v14a0 0 0 0 1 0 0H6a2 2 0 0 '
       '1-2-2V4a2 2 0 0 1 2-2zm7 2v5h5l-5-5zM8 13h8v2H8v-2zm0 4h8v2H8v-2z"/></svg>')
BACK = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5V1L7 6l5 5V7a6 6 0 1 1-6 6H4a8 8 0 1 0 8-8z"/></svg>')


# ===========================================================================
# The upsell interstitial.
#
# One function, both languages, both checkouts' wording - because this is the
# single most consequential piece of copy on the site and two drifting copies
# of it is how a guarantee ends up meaning two different things in two places.
#
# Every figure is interpolated from pay.py. Nothing here types a price.
#
# WHAT IT PROMISES, EXACTLY - read this before editing a word of it:
#
#   * It is NOT charged today. Thawani's e-commerce checkout takes a single
#     payment and recurring billing needs card-on-file (see SUBSCRIPTIONS.md),
#     so this is recorded on the order and invoiced monthly from go-live -
#     identical treatment to the Growth Desk. The copy says so plainly.
#   * The refund is of THIS SERVICE'S fees only, never the build. Refunding a
#     OMR 950 website because a visibility retainer underperformed is not what
#     is being offered and the wording must never be allowed to imply it.
#   * "Visible" is defined, in writing, in month one. An undefined guarantee
#     is unenforceable for Nahid and untrustworthy for the buyer; the same
#     sentence protects both of them.
# ===========================================================================
UPSELL = {
    "en": {
        "eyebrow": "One page only &#183; you will not see this offer again",
        "h": "Your website will be ready to be found.<br>Being found is a different job.",
        "sub": "Ninety seconds, then you can pay. This is the one thing people come back "
               "and ask me for six months late, so I would rather you heard it now.",
        "seo_h": "SEO &mdash; how Google decides who to show",
        "seo_p": "Picture a library with ten million books and one librarian. Somebody walks in "
                 "and asks for &#8220;the best water pump supplier in Muscat.&#8221; She does not "
                 "read ten million books. She reaches for the few she already knows, already "
                 "trusts, and has watched people come back to happy. <b>SEO is the work of "
                 "becoming a book she reaches for.</b>",
        "geo_h": "GEO &mdash; the same thing, for AI",
        "geo_p": "When your buyer asks ChatGPT &#8220;who should I buy from in Oman?&#8221;, "
                 "ChatGPT does not go and read the internet on the spot. It answers out of what "
                 "it has already read and already trusts. <b>GEO is the work of being inside what "
                 "it read</b> &mdash; so your name is in the answer itself, not on page four of "
                 "something nobody opens.",
        "why_h": "And here is the part nobody tells you: it never finishes",
        "why_p": "Your competitors do not stop. Google changes its mind about who to trust almost "
                 "daily. And the AI models are retrained and re-read the web on their own "
                 "schedule &mdash; every time they do, the answer is written again from nothing.",
        "why_p2": "So visibility is not a wall you build once. <b>It is a garden.</b> Stop watering "
                  "it and it does not stay the way you left it. It goes back to weeds, because the "
                  "person next door kept watering theirs.",
        "have_h": "What you are already paying for &mdash; and where it stops",
        "have_p": "Everything I build for you already carries the full visibility skeleton:",
        "have": [
            "A structure Google can read cleanly, on a site that loads fast",
            "Schema markup that tells an AI what your business is and what it sells",
            "Arabic and English done properly, not run through a translator",
            "An <code>llms.txt</code> and a content structure built to be quoted by an answer engine",
        ],
        "have_after": "That part is real, it is done, and it is yours for ever. <b>But "
                      "infrastructure is a road, not a car driving down it.</b> The road will be "
                      "finished on the day I hand it over. Somebody still has to drive it &mdash; "
                      "and not once. Every day.",
        "do_h": "What driving it actually looks like",
        "do_p": "Watching what your buyers really type and ask. Writing the answers they are "
                "searching for. Getting your name onto the pages, directories and sources the "
                "models actually read. Keeping your Google Business Profile alive. Fixing what "
                "breaks. And testing every month whether ChatGPT, Gemini, Google&#8217;s AI "
                "answers and ordinary Google search name you &mdash; and showing you the "
                "screenshots either way.",
        "do_p2": "That is daily work. It is a job, and it is the job I do.",
        "offer_nm": "Book it now",
        "per": "/month",
        "was": "#/month",
        "offer_note": "<b>Nothing is charged today.</b> It starts the month after your site goes "
                      "live and is invoiced monthly. Cancel any month &mdash; though the "
                      "guarantee below needs #MO months to run.",
        "g_h": "The #MO-month guarantee",
        "g_p": "#MO months after your site goes live, if you are not visible &mdash; not named "
               "by Google, not named by ChatGPT &mdash; <b>I refund every rial you have paid "
               "for #NM, and I carry on working, free, until you are.</b>",
        "g_fine": "In plain terms: the refund covers this service&#8217;s fees, not your build. "
                  "And &#8220;visible&#8221; is not left vague &mdash; in your first month we "
                  "write down the actual buying questions your customers ask, and those are what "
                  "we test against, every month, in front of you.",
        "only_h": "This price lives on this page and nowhere else.",
        "only_p": "The published rate for the same work is <b>#RACK a month</b>. #NOW is what it "
                  "costs if you book it in this window, before you pay for your build &mdash; "
                  "because doing this from day one is far cheaper for me than rescuing it a year "
                  "in. <b>Leave this page and the price is #RACK.</b> I do not re-open it later, "
                  "and asking me nicely in March will not work.",
        "yes": "Add it &mdash; #NOW a month",
        "no": "No thanks &mdash; continue to payment at #RACK later",
        "close": "Close and continue without it",
    },
    "ar": {
        "eyebrow": "هذه الصفحة فقط &#183; لن يظهر هذا العرض مرة أخرى",
        "h": "موقعك سيكون جاهزاً لأن يُعثر عليه.<br>أما أن يُعثر عليه فعلاً، فتلك مهمة أخرى.",
        "sub": "تسعون ثانية، ثم تستطيع الدفع. هذا هو الشيء الذي يعود الناس ليطلبوه مني بعد ستة "
               "أشهر، ولذلك أفضّل أن تسمعه الآن.",
        "seo_h": "‏SEO — كيف يقرّر جوجل من يعرض",
        "seo_p": "تخيّل مكتبة فيها عشرة ملايين كتاب وأمين مكتبة واحد. يدخل شخص ويسأل عن "
                 "«أفضل مورّد مضخات مياه في مسقط». هو لا يقرأ عشرة ملايين كتاب، بل يمدّ يده إلى "
                 "الكتب القليلة التي يعرفها ويثق بها ورأى الناس يعودون إليها راضين. "
                 "<b>‏SEO هو العمل الذي يجعلك أحد الكتب التي تمتدّ إليها يده.</b>",
        "geo_h": "‏GEO — الشيء نفسه، لكن للذكاء الاصطناعي",
        "geo_p": "حين يسأل مشتريك ChatGPT: «ممن أشتري في عُمان؟»، فهو لا يذهب ليقرأ الإنترنت في "
                 "تلك اللحظة، بل يجيب مما قرأه سابقاً ووثق به. <b>‏GEO هو العمل الذي يجعلك داخل "
                 "ما قرأه</b> — ليكون اسمك في الإجابة نفسها، لا في صفحة رابعة لا يفتحها أحد.",
        "why_h": "وهنا الجزء الذي لا يخبرك به أحد: هذا العمل لا ينتهي",
        "why_p": "منافسوك لا يتوقفون. وجوجل يغيّر رأيه فيمن يثق به كل يوم تقريباً. ونماذج الذكاء "
                 "الاصطناعي يُعاد تدريبها وتقرأ الويب من جديد وفق جدولها الخاص — وفي كل مرة "
                 "تُكتب الإجابة من الصفر.",
        "why_p2": "فالظهور ليس جداراً تبنيه مرة واحدة. <b>إنه حديقة.</b> توقّف عن سقايتها فلن تبقى "
                  "كما تركتها، بل تعود إلى العشب البري — لأن جارك واصل سقاية حديقته.",
        "have_h": "ما تدفع مقابله بالفعل — وأين يتوقف",
        "have_p": "كل ما أبنيه لك يحمل أصلاً هيكل الظهور كاملاً:",
        "have": [
            "بنية يقرأها جوجل بوضوح، على موقع سريع التحميل",
            "ترميز Schema يخبر الذكاء الاصطناعي ما هو نشاطك وما الذي تبيعه",
            "عربية وإنجليزية مكتوبتان كما ينبغي، لا مارّتان عبر مترجم آلي",
            "ملف <code>llms.txt</code> وبنية محتوى مصمّمة ليقتبسها محرك الإجابات",
        ],
        "have_after": "هذا الجزء حقيقي، ومنجز، وهو ملكك إلى الأبد. <b>لكن البنية التحتية طريق، لا "
                      "سيارة تسير عليه.</b> الطريق سيكتمل يوم أسلّمه لك، ويبقى على أحدهم أن "
                      "يقودها — لا مرة واحدة، بل كل يوم.",
        "do_h": "وكيف تبدو القيادة عملياً",
        "do_p": "متابعة ما يكتبه ويسأله مشتروك فعلاً. وكتابة الإجابات التي يبحثون عنها. وإيصال "
                "اسمك إلى الصفحات والأدلة والمصادر التي تقرأها النماذج فعلاً. وإبقاء ملفّك في "
                "«نشاطي التجاري على جوجل» حيّاً. وإصلاح ما يتعطّل. واختبار شهري لما إذا كان "
                "ChatGPT وGemini وإجابات جوجل الذكية وبحث جوجل العادي يذكرون اسمك — مع عرض "
                "لقطات الشاشة عليك في الحالتين.",
        "do_p2": "هذا عمل يومي. إنه وظيفة، وهي الوظيفة التي أؤدّيها.",
        "offer_nm": "احجزه الآن",
        "per": "شهرياً",
        "was": "# شهرياً",
        "offer_note": "<b>لا يُحتسب شيء اليوم.</b> يبدأ في الشهر التالي لإطلاق موقعك ويُفوتر شهرياً. "
                      "وتستطيع الإلغاء في أي شهر — مع أن الضمان أدناه يحتاج #MO أشهر ليكتمل.",
        "g_h": "ضمان الـ#MO أشهر",
        "g_p": "بعد #MO أشهر من إطلاق موقعك، إن لم تكن ظاهراً — لا جوجل يذكرك ولا ChatGPT — "
               "<b>أعيد لك كل ريال دفعته مقابل #NM، وأواصل العمل مجاناً حتى تظهر.</b>",
        "g_fine": "بعبارة صريحة: الاسترداد يشمل رسوم هذه الخدمة، لا تكلفة بناء موقعك. و«الظهور» "
                  "ليس مصطلحاً غامضاً — ففي شهرك الأول نكتب معاً أسئلة الشراء الحقيقية التي "
                  "يسألها عملاؤك، وهي ما نختبر عليه، كل شهر، أمامك.",
        "only_h": "هذا السعر موجود في هذه الصفحة، ولا مكان غيرها.",
        "only_p": "السعر المعلن للعمل نفسه هو <b>#RACK شهرياً</b>. و#NOW هو ما يكلّفه إن حجزته في "
                  "هذه اللحظة، قبل أن تدفع مقابل البناء — لأن القيام بهذا من اليوم الأول أرخص "
                  "عليّ بكثير من إنقاذه بعد عام. <b>غادر هذه الصفحة وسيعود السعر إلى #RACK</b> "
                  "أنا لا أعيد فتحه لاحقاً، ولن ينفع الطلب اللطيف في مارس.",
        "yes": "أضِفه — #NOW شهرياً",
        "no": "لا، شكراً — أكمل الدفع وسعره لاحقاً #RACK",
        "close": "إغلاق والمتابعة بدونه",
    },
}


def upsell_dialog(lang="en"):
    """The interstitial, rendered server-side into both checkouts.

    Deliberately markup and not a JavaScript template. It is long-form
    persuasion with two languages of hand-written prose in it, and prose
    belongs in prose files - building it by string-concatenation in the page
    script would make it unreadable and unreviewable, which is the last thing
    a guarantee should be.

    The <dialog> ships closed. Nothing shows it but the submit handler."""
    w = UPSELL[lang]
    u = pay.item(pay.UPSELL_ID)
    fmt = pay.money_ar if lang == "ar" else pay.money
    now, rack = fmt(pay.price(u)), fmt(u["rack"])
    months = str(u["guarantee_months"])
    nm = pay.t(u, "name", lang)

    def s(key):
        """One string with every token filled.

        Every token is NAMED - #NOW, #RACK, #NM, #MO - and that is not a
        style choice. WORDS elsewhere in this file uses a bare "#" as its
        placeholder, but these strings are HTML and HTML is full of numeric
        entities: a bare "#" replacement rewrites &#8217; into &68217; and
        prints a literal "&68217;s" on the one page that has to look
        trustworthy. Named tokens only, here."""
        return (w[key].replace("#NOW", now).replace("#RACK", rack)
                .replace("#NM", nm).replace("#MO", months))

    haves = "\n".join(f"            <li>{h}</li>" for h in w["have"])

    return f"""
<dialog class="up-dlg" id="upDlg" aria-labelledby="upTitle">
  <div class="up-card">
    <div class="up-scroll">

      <div class="up-head">
        <button type="button" class="up-x" id="upX" aria-label="{w['close']}">&#10005;</button>
        <p class="eyebrow">{w['eyebrow']}</p>
        <h2 id="upTitle">{w['h']}</h2>
        <p>{w['sub']}</p>
      </div>

      <div class="up-body">

        <div class="up-def">
          <h3>{w['seo_h']}</h3>
          <p>{w['seo_p']}</p>
        </div>

        <div class="up-def">
          <h3>{w['geo_h']}</h3>
          <p>{w['geo_p']}</p>
        </div>

        <div class="up-rule"></div>

        <h3>{w['why_h']}</h3>
        <p>{w['why_p']}</p>
        <p>{w['why_p2']}</p>

        <div class="up-rule"></div>

        <h3>{w['have_h']}</h3>
        <div class="up-have">
          <p>{w['have_p']}</p>
          <ul>
{haves}
          </ul>
        </div>
        <p>{w['have_after']}</p>

        <h3>{w['do_h']}</h3>
        <p>{w['do_p']}</p>
        <p class="sub">{w['do_p2']}</p>

        <div class="up-rule"></div>

        <div class="up-offer">
          <span class="nm">{w['offer_nm']} &#183; {nm}</span>
          <p class="up-figs">
            <span class="up-now">{now}<span class="per">{w['per']}</span></span>
            <span class="up-was">{w['was'].replace('#', rack)}</span>
          </p>
          <p class="note">{s('offer_note')}</p>
        </div>

        <div class="up-gtee">
          {SHIELD}
          <div>
            <h3>{s('g_h')}</h3>
            <p>{s('g_p')}</p>
            <p class="fine">{s('g_fine')}</p>
          </div>
        </div>

        <div class="up-only">
          <b>{w['only_h']}</b><br>{s('only_p')}
        </div>

      </div>
    </div>

    <div class="up-act">
      <button type="button" class="btn btn-teal" id="upYes">{s('yes')}</button>
      <button type="button" class="up-no" id="upNo">{s('no')}</button>
    </div>
  </div>
</dialog>

"""


# ===========================================================================
# The pledge row.
#
# The Assigned Admin is not offered the way the other options are. It is a
# commitment about how the two teams will work every day, so the buyer accepts
# it by ticking a sentence written in his own voice - the wording Nahid asked
# for, verbatim but for the brand name and the figure.
#
# Both languages live here for the same reason the upsell's do: one sentence
# that says what somebody is agreeing to must not exist in two drifting copies.
# The rate is interpolated from pay.py (#FEE), never typed, so a price change
# rewrites the sentence a buyer signs. Named token, not a bare "#", because
# these strings are HTML and a bare "#" replacement would rewrite &#8217;.
#
# What it must keep saying, whatever else is edited:
#   * it is NOT charged today - it starts the month after go-live and is
#     invoiced monthly, exactly like the Growth Desk (see SUBSCRIPTIONS.md);
#   * the figure in the sentence is the figure on the invoice;
#   * it is cancellable any month, and nothing else on the order depends on it.
# ===========================================================================
PLEDGE = {
    "en": {
        "price": "#FEE/month",
        "say": "I want AI Profit Lab to assign an admin for our website to update our "
               "products/services and be in daily touch with our team. I accept a monthly "
               "payment of #FEE for it.",
        "note": "<b>Not charged today.</b> It starts the month after your site goes live and is "
                "invoiced monthly with everything else &mdash; cancel any month.",
    },
    "ar": {
        "price": "#FEE/شهرياً",
        "say": "أريد من AI Profit Lab أن يخصّص مشرفاً لموقعنا يحدّث منتجاتنا وخدماتنا ويكون على "
               "تواصل يومي مع فريقنا. وأوافق على دفع #FEE شهرياً مقابل ذلك.",
        "note": "<b>غير محتسب اليوم.</b> يبدأ في الشهر التالي لإطلاق موقعك ويُفوتر شهرياً مع بقية "
                "البنود &mdash; ويمكن إلغاؤه في أي شهر.",
    },
}


def pledge_card(lang="en"):
    """The Assigned Admin, as a checkbox whose label is the sentence.

    An ordinary `name="item"` checkbox, so it travels the machinery that was
    already there: selected() finds it, render() re-totals from it, the summary
    prints it as a monthly line, summaryText() puts it in the WhatsApp order,
    order() ships its id, and the server prices it from its own copy of the
    table. Nothing about the pledge is special once it is ticked - only the way
    it is asked."""
    i = pay.item(pay.ADMIN_ID)
    w = PLEDGE[lang]
    fee = (pay.money_ar if lang == "ar" else pay.money)(pay.price(i))
    f = lambda key: w[key].replace("#FEE", fee)  # noqa: E731
    return f"""      <label class="opt opt-say" data-kind="item">
        <input type="checkbox" name="item" value="{i['id']}">
        <span class="tick" aria-hidden="true"></span>
        <span class="opt-b">
          <span class="opt-h"><b>{pay.t(i, 'name', lang)}</b><span class="opt-p">{f('price')}</span></span>
          <span class="say">{f('say')}</span>
          <span class="opt-d">{f('note')}</span>
        </span>
      </label>"""


def upsell_field():
    """The upsell's only state, and it has to sit INSIDE #coForm.

    A real checkbox named "item", so the existing selected() finds it,
    render() re-totals from it, the summary lists it and order() ships it:
    the interstitial adds a line item through the machinery that was already
    there rather than around it, and the server prices it like any other
    monthly row.

    It cannot be attached with a `form="coForm"` attribute from outside,
    because selected() reads `form.querySelectorAll(...)` - a DOM-descendant
    query that a form-associated control living elsewhere would silently fail.
    That failure would be invisible: the buyer accepts, the dialog closes,
    payment proceeds, and the item is simply not on the order."""
    return (f'          <input type="checkbox" name="item" value="{pay.UPSELL_ID}" '
            f'id="upItem" hidden>\n')


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
    # pay.listed() is what keeps the upsell OFF this list. It is a monthly
    # item like the Growth Desk, but it is sold only by the interstitial - if
    # it rendered as an ordinary checkbox here, "only on this page" would be
    # false the moment the page loaded.
    # ...and pay.ADMIN_ID is off it for a different reason: it IS listed, but
    # it is asked as a sentence, so pledge_card() renders it below rather than
    # _monthly() rendering it as a card like the others.
    monthlies = [i for i in pay.CATALOG if i["kind"] == "monthly"
                 and pay.listed(i) and i["id"] != pay.ADMIN_ID]
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

    return f"""<main id="main">
{envbar}
<header class="phero s-cream grain">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> Checkout &#183; the published price, nothing added at the end</p>
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

          <p class="hint" style="margin:26px 0 12px">And the optional monthly work &mdash; <b>none</b> of it
            charged today, and none of it needed to keep your site running:</p>
          <div class="opts">
{chr(10).join(_monthly(i) for i in monthlies)}
{pledge_card("en")}
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

{upsell_field()}    </form>
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
        <a class="btn btn-amber" href="/en/contact/#test">Get the Silent Buyer Test</a>
        <a class="btn btn-ghost" href="/en/services/#price">See the full price list</a>
      </div>
    </div>
  </div>
</section>

<div class="paybar" id="payBar" aria-hidden="true">
  <span><span class="pb-k" id="barKey">Due today</span><span class="pb-v" id="barVal">{pay.money(q0['due'])}</span></span>
  <button class="btn btn-teal" type="submit" form="coForm" id="barBtn">Reserve</button>
</div>

{upsell_dialog("en")}
<script type="application/json" id="payCfg">{cfg}</script>
</main>
"""


JS_TPL = r"""
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

  /* Every user-visible string, so one engine serves both languages. "#" is
     the slot a value drops into: Arabic puts the currency after the figure
     and English before it, and none of these sentences survive being glued
     together in a fixed order. */
  var T = __WORDS__;

  var $ = function(id){ return document.getElementById(id); };

  /* ------------------------------------------------------------- money --- */
  function omr(b){
    var w = Math.floor(b / CFG.baisa), r = b % CFG.baisa;
    var s = w.toLocaleString("en-US");
    if (r) s += "." + ("00" + r).slice(-3);
    return s;
  }
  function money(b){ return T.cur.replace("#", omr(b)); }

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
      lines.appendChild(li(T.bundleLine.replace("#", CFG.bundle.name), "−" + money(q.saving), "save"));
    }
    if (q.surcharge > 0){
      lines.appendChild(li(
        q.plan.id === "three" ? T.payThree : T.payProof,
        "+" + money(q.surcharge)));
    }
    lines.appendChild(li(T.total, money(q.total), "total"));
    for (i = 0; i < q.monthly.length; i++){
      lines.appendChild(li(q.monthly[i].name, T.perMonth.replace("#", money(q.monthly[i].price)), "later",
        T.monthlyNote));
    }

    /* ---- the number that matters ---- */
    dueVal.textContent = money(q.due);
    if (barVal) barVal.textContent = money(q.due);
    var key = T.dueToday;
    dueKey.textContent = key;
    if (barKey) barKey.textContent = key;

    /* ---- and what happens to the rest of it ---- */
    var then;
    if (q.plan.due === "zero"){
      then = T.thenZero.replace("#", money(q.total));
    } else if (q.plan.split > 1){
      then = T.thenSplit.replace("#1", money(q.later)).replace("#2", money(q.later))
                        .replace("#3", money(q.total));
    } else if (q.balance > 0){
      then = T.thenBalance.replace("#1", money(q.balance)).replace("#2", money(q.due));
    } else {
      then = T.thenWhole;
    }
    /* Every monthly line, not just the first. Two of them can now be on one
       order (the Growth Desk and the Assigned Admin), and naming one while
       silently invoicing two is the kind of small dishonesty this page is
       built to avoid. */
    if (q.monthly.length){
      var mnames = [];
      for (i = 0; i < q.monthly.length; i++) mnames.push(q.monthly[i].name);
      then += " " + (q.monthly.length > 1 ? T.monthlyStartsMany : T.monthlyStarts)
                      .replace("#", mnames.join(T.and));
    }
    thenP.textContent = then;

    /* ---- each payment structure's own headline ---- */
    for (i = 0; i < CFG.plans.length; i++){
      var p = CFG.plans[i], tag = form.querySelector('[data-planfig="' + p.id + '"]');
      if (!tag) continue;
      var pq = quote(sel, p.id);
      tag.textContent = p.due === "zero" ? T.nothingToday : T.todayFig.replace("#", money(pq.due));
    }

    if (bundleNote) bundleNote.classList.toggle("on", q.bundled);

    /* ---- the button says what will actually happen ---- */
    var canCard = CFG.live && CFG.api && q.plan.card;
    if (canCard){
      payLabel.textContent = T.payNow.replace("#", money(q.due));
      if (barBtn) barBtn.textContent = T.payNowShort.replace("#", money(q.due));
    } else if (CFG.live && !q.plan.card){
      payLabel.textContent = T.sendOrder;
      if (barBtn) barBtn.textContent = T.sendOrderShort;
      payUnder.innerHTML = T.proofUnder;
    } else {
      payLabel.textContent = T.reserve;
      if (barBtn) barBtn.textContent = T.reserveShort;
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
      var msg = v ? "" : T.errRequired;
      if (!msg && nm === "email" && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v)){
        msg = T.errEmail;
      }
      if (!msg && nm === "whatsapp" && v.replace(/[^\d]/g, "").length < 8){
        msg = T.errPhone;
      }
      if (msg){ ok = false; first = first || form.elements[nm]; }
      fieldErr(nm, msg);
    }
    var box = $("formErr");
    if (!form.elements.agree.checked){
      ok = false;
      box.textContent = T.errAgree;
      box.classList.add("on");
      first = first || form.elements.agree;
    } else if (ok){
      box.classList.remove("on");
    } else {
      box.textContent = T.errSome;
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
    var out = [T.waHead, "", T.waRef + reference(), ""];
    for (var i = 0; i < q.build.length; i++){
      out.push("• " + q.build[i].name + " — " + money(q.build[i].price));
    }
    if (q.saving > 0) out.push("• " + CFG.bundle.name + " — " + T.waSaving.replace("#", money(q.saving)));
    if (q.surcharge > 0) out.push("• " + q.plan.label + " — " + T.waAdds.replace("#", money(q.surcharge)));
    for (i = 0; i < q.monthly.length; i++){
      out.push("• " + q.monthly[i].name + " — " + T.waMonthly.replace("#", money(q.monthly[i].price)));
    }
    out.push("", T.waTotal + money(q.total));
    out.push(q.plan.due === "zero" ? T.waTerms + q.plan.label + T.waNothingDue
                                   : T.waDueNow + money(q.due) + " (" + q.plan.label + ")");
    var g = function(n){ return (form.elements[n].value || "").trim(); };
    out.push("", T.waName + g("name"), T.waBusiness + g("business"), T.waEmail + g("email"),
             T.waWhatsapp + g("whatsapp"));
    if (g("cr")) out.push(T.waCr + g("cr"));
    if (g("city")) out.push(T.waCity + g("city"));
    if (g("notes")) out.push("", T.waNotes + g("notes"));
    return out.join("\n");
  }

  /* --------------------------------------------------- offline handover --- */
  function offline(q, why){
    var panel = $("offlinePanel");
    $("offlineRef").textContent = reference();
    if (why) $("offlineWhy").textContent = why;
    var text = summaryText(q);
    $("offlineWa").href = "https://api.whatsapp.com/send?phone=96899245250&text=" + encodeURIComponent(text);
    $("offlineMail").href = "mailto:hello@aiprofitlab.io?subject=" + encodeURIComponent(T.mailSubject + reference())
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

  /* ------------------------------------------------ the upsell gate ---
     Runs once, between "pay" and the card page, and only ever DELAYS the
     submission - never cancels it. Every exit from the dialog calls pay()
     with the buyer's answer already recorded on #upItem.

     Three reasons it stands down, all of them deliberate:
       * decided        - it has already been answered this page-load. A
                          buyer whose card was refused and who presses pay
                          again is not asked to re-decide an upsell.
       * skip_if        - they already bought the monthly plan it overlaps
                          with (the Growth Desk). Nobody is asked to take
                          two monthly retainers in the same breath.
       * already ticked - deep link or a browser restoring form state.
     If the markup is missing for any reason, it stands down too: the
     absence of an upsell must never be able to block a payment.            */
  var upDlg = $("upDlg"), upItem = $("upItem"), upDecided = false;

  function upsellDue(){
    if (upDecided || !upDlg || !upItem || !upDlg.showModal) return false;
    if (upItem.checked) return false;
    var cfg = CFG.upsell;
    if (!cfg) return false;
    if (cfg.skip_if && selected().indexOf(cfg.skip_if) >= 0) return false;
    return true;
  }

  function upsellClose(taken){
    upDecided = true;
    upItem.checked = Boolean(taken);
    render();                       /* re-total, so the summary shows the line */
    try { upDlg.close(); } catch(err){}
    if (typeof gtag === "function"){
      gtag("event", taken ? "add_to_cart" : "upsell_declined", {
        item_id: CFG.upsell.id, item_name: CFG.upsell.name,
        value: CFG.upsell.price / CFG.baisa, currency: CFG.currency
      });
    }
    pay();
  }

  if (upDlg && upItem){
    $("upYes").addEventListener("click", function(){ upsellClose(true); });
    $("upNo").addEventListener("click", function(){ upsellClose(false); });
    $("upX").addEventListener("click", function(){ upsellClose(false); });
    /* Escape and backdrop both fire `cancel`/`close`. Whichever way the buyer
       leaves, they leave INTO the payment they asked for - a dialog that
       swallowed the click on the one page that takes money would be the
       worst bug on the site. */
    upDlg.addEventListener("cancel", function(e){ e.preventDefault(); upsellClose(false); });
  }

  form.addEventListener("submit", function(e){
    e.preventDefault();
    if (!validate()) return;
    if (upsellDue()){
      upDlg.showModal();
      if (typeof gtag === "function"){
        gtag("event", "view_promotion", {promotion_id: CFG.upsell.id,
                                         promotion_name: CFG.upsell.name});
      }
      return;
    }
    pay();
  });

  function pay(){
    var q = render();
    var canCard = CFG.live && CFG.api && q.plan.card;

    if (!canCard){ offline(q, null); return; }

    btn.setAttribute("aria-busy", "true");
    $("payLabel").textContent = T.opening;

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
      offline(q, T.abandon.replace("#", why));
    }

    var give_up = setTimeout(function(){
      if (!settle()) return;
      abandon(T.errTimeout);
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
      abandon((res.body && res.body.message) || T.errRefused);
    }).catch(function(err){
      if (!settle()) return;
      abandon(err && err.message ? err.message : T.errUnknown);
    });
  }

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


# --------------------------------------------------------------------------
# Every user-visible string in the checkout engine, both languages.
# "#" (or #1/#2/#3) marks where a formatted figure drops in.
# --------------------------------------------------------------------------
WORDS = {
    "en": {
        "cur": "OMR #",
        "bundleLine": "# — priced as one build",
        "payThree": "Paying in three", "payProof": "Paying only on proof",
        "total": "Total", "perMonth": "#/mo",
        "monthlyNote": "From the month after go-live. Not charged today, cancel any month.",
        "dueToday": "Due today",
        "thenZero": ("Nothing is charged now. The full # is invoiced only after your site has produced "
                     "its first real, verifiable buyer inquiry — and if it never does, it is never invoiced."),
        "thenSplit": "Then #1 when it goes live, and #2 thirty days after that. #3 in total, and nothing after it.",
        "thenBalance": ("The remaining #1 is invoiced once your brief is confirmed. "
                        "Your #2 comes off it — it is a deposit, not a fee."),
        "thenWhole": "That is the whole build, paid once. No monthly fee is required to keep any of it running.",
        "monthlyStarts": "# starts separately, the month after go-live.",
        "monthlyStartsMany": "# start separately, the month after go-live.",
        "and": " and ",
        "nothingToday": "Nothing today", "todayFig": "# today",
        "payNow": "Pay # securely", "payNowShort": "Pay #",
        "sendOrder": "Send my order", "sendOrderShort": "Send order",
        "proofUnder": ("Nothing is charged on Pay on Proof terms. I confirm the order and the agreement "
                       "follows — the invoice only comes after your first real inquiry."),
        "reserve": "Reserve my slot", "reserveShort": "Reserve",
        "errRequired": "I need this one.",
        "errEmail": "That address does not look complete.",
        "errPhone": "A number I can actually reach you on, please.",
        "errAgree": ("Please confirm you have read the terms and the refund policy — it is the "
                     "one box I cannot tick for you."),
        "errSome": "A few details are missing below.",
        "waHead": "Hello Nahid — here is my order.", "waRef": "Reference: ",
        "waSaving": "# off the parts", "waAdds": "adds #", "waMonthly": "#/month from go-live",
        "waTotal": "Total: ", "waTerms": "Terms: ", "waNothingDue": ", nothing due now",
        "waDueNow": "Due now: ", "waName": "Name: ", "waBusiness": "Business: ",
        "waEmail": "Email: ", "waWhatsapp": "WhatsApp: ", "waCr": "CR: ",
        "waCity": "City: ", "waNotes": "Notes: ",
        "mailSubject": "Order ", "opening": "Opening secure payment…",
        "abandon": ("The card payment could not be started (#), so nothing was charged. "
                    "Send the order across instead and I will follow it up with a payment link."),
        "errTimeout": "the gateway did not answer in time",
        "errRefused": "the gateway refused the order",
        "errUnknown": "unknown error",
    },
    "ar": {
        "cur": "# ر.ع.",
        "bundleLine": "# — بسعر بناء واحد",
        "payThree": "الدفع على ثلاث دفعات", "payProof": "الدفع عند الإثبات فقط",
        "total": "الإجمالي", "perMonth": "#/شهرياً",
        "monthlyNote": "يبدأ من الشهر التالي للإطلاق. غير محتسب اليوم، ويُلغى في أي شهر.",
        "dueToday": "المستحق اليوم",
        "thenZero": ("لا يُحتسب شيء الآن. المبلغ كاملاً # يُفوتر فقط بعد أن ينتج موقعك أول استفسار "
                     "حقيقي وقابل للتحقق من مشترٍ — وإن لم ينتجه أبداً، فلن يُفوتر أبداً."),
        "thenSplit": "ثم #1 عند الإطلاق، و#2 بعد ثلاثين يوماً من ذلك. #3 إجمالاً، ولا شيء بعدها.",
        "thenBalance": ("المتبقي #1 يُفوتر بعد تأكيد ملخّص طلبك. "
                        "و#2 التي دفعتها تُخصم منه — فهي عربون لا رسم."),
        "thenWhole": "هذا هو البناء كاملاً، مدفوعاً مرة واحدة. ولا رسم شهري مطلوب لإبقاء أي منه يعمل.",
        "monthlyStarts": "# يبدأ على حدة، في الشهر التالي للإطلاق.",
        "monthlyStartsMany": "# تبدأ على حدة، في الشهر التالي للإطلاق.",
        # No space after the waw: Arabic joins it to the following word, so
        # " و" + "المشرف" reads "والمشرف" and " و " would not.
        "and": " و",
        "nothingToday": "لا شيء اليوم", "todayFig": "# اليوم",
        "payNow": "ادفع # بأمان", "payNowShort": "ادفع #",
        "sendOrder": "أرسل طلبي", "sendOrderShort": "أرسل الطلب",
        "proofUnder": ("لا يُحتسب شيء بصيغة الدفع عند الإثبات. أؤكّد الطلب ويتبعه الاتفاق — "
                       "والفاتورة لا تأتي إلا بعد أول استفسار حقيقي يصلك."),
        "reserve": "احجز موعدي", "reserveShort": "احجز",
        "errRequired": "أحتاج هذه الخانة.",
        "errEmail": "هذا العنوان لا يبدو مكتملاً.",
        "errPhone": "رقم أستطيع الوصول إليك عليه فعلاً، من فضلك.",
        "errAgree": ("يرجى تأكيد اطّلاعك على الشروط وسياسة الاسترداد — وهي الخانة الوحيدة "
                     "التي لا أستطيع تعليمها نيابةً عنك."),
        "errSome": "بعض البيانات ناقصة في الأسفل.",
        "waHead": "مرحباً ناهد — هذا طلبي.", "waRef": "الرقم المرجعي: ",
        "waSaving": "# خصماً عن مجموع الأجزاء", "waAdds": "يضيف #",
        "waMonthly": "#/شهرياً من تاريخ الإطلاق",
        "waTotal": "الإجمالي: ", "waTerms": "الصيغة: ", "waNothingDue": "، لا مستحق الآن",
        "waDueNow": "المستحق الآن: ", "waName": "الاسم: ", "waBusiness": "النشاط: ",
        "waEmail": "البريد: ", "waWhatsapp": "واتساب: ", "waCr": "س.ت: ",
        "waCity": "المدينة: ", "waNotes": "ملاحظات: ",
        "mailSubject": "طلب ", "opening": "جارٍ فتح صفحة الدفع الآمن…",
        "abandon": ("تعذّر بدء الدفع بالبطاقة (#)، فلم يُحتسب شيء. "
                    "أرسل الطلب بدلاً من ذلك وسأتابعه معك برابط دفع."),
        "errTimeout": "لم تستجب بوابة الدفع في الوقت المحدد",
        "errRefused": "رفضت بوابة الدفع الطلب",
        "errUnknown": "خطأ غير معروف",
    },
}


def js(lang="en"):
    import json
    return JS_TPL.replace("__WORDS__", json.dumps(WORDS[lang], ensure_ascii=False))


JS = js("en")


META = dict(
    slug="checkout",
    title="Checkout | AI Profit Lab — build it the way you need it",
    desc=("Choose what gets built, choose how you pay for it, and see the total before you commit. "
          "Priced in OMR by Lotus Gulf International, CR 1570092, Muscat."),
    nav="/en/services/",
    next=("Any last questions?", "Talk to the person who builds it", "/en/contact/"),
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
