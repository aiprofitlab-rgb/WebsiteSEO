#!/usr/bin/env python3
"""Contact.

The form composes a WhatsApp message rather than posting to a backend - the
same pattern index-v3 and contact-new.html use - so nothing leaves the browser
until the visitor presses send inside WhatsApp, which is exactly what the note
under the button promises.

Copy here is deliberately short: this page exists to be acted on, not read.
"""
import pay
from kit import WA, WA_ICON, STAR

CSS = """
/* ------------------------------------------------------------- channels */
.chan{display:grid;grid-template-columns:repeat(3,1fr);gap:clamp(16px,2vw,24px)}
.chan a{
  position:relative;display:flex;flex-direction:column;gap:12px;text-decoration:none;overflow:hidden;
  background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:clamp(22px,2.6vw,32px);
  transition:transform .35s var(--ease),border-color .35s,background .35s,box-shadow .35s;
}
.chan a:hover{transform:translateY(-5px);border-color:var(--amber-pale);background:var(--white);box-shadow:0 30px 54px -40px rgba(7,43,34,.5)}
.chan a.primary{background:var(--teal-950);border-color:var(--teal-900)}
.chan a.primary:hover{background:var(--teal-900);border-color:var(--amber-bright)}
.chan .ic{width:44px;height:44px;border-radius:50%;display:grid;place-items:center;background:var(--white);border:1px solid var(--line);color:var(--teal)}
.chan a.primary .ic{background:var(--wa);border-color:var(--wa);color:#fff}
.chan .ic svg{width:21px;height:21px;fill:currentColor}
.chan h3{font-size:1.35rem;color:var(--teal-950);margin:0}
.chan a.primary h3{color:var(--cream)}
.chan .val{font-family:var(--mono);font-size:.95rem;color:var(--teal);word-break:break-word}
.chan a.primary .val{color:var(--amber-bright)}
.chan .when{
  font-family:var(--mono);font-size:.7rem;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);
  margin-top:auto;padding-top:10px;display:flex;align-items:center;gap:8px;
}
.chan a.primary .when{color:var(--amber-pale)}
.chan .when i{width:7px;height:7px;border-radius:50%;background:var(--wa);flex:none}

/* --------------------------------------------------------- section plate
   Same background image and opacity the live contact page uses, with the
   section colour faded back in top and bottom so the form stays readable. */
.plate{position:absolute;inset:0;z-index:0;overflow:hidden;pointer-events:none}
.plate img{width:100%;height:100%;object-fit:cover;opacity:.2}
.plate::after{
  content:"";position:absolute;inset:0;
  background:linear-gradient(180deg,var(--teal-950),rgba(7,43,34,.45) 45%,var(--teal-950));
}
#test .wrap{position:relative;z-index:1}

/* ----------------------------------------------------------------- form */
.capture-grid{display:grid;grid-template-columns:.95fr 1.05fr;gap:clamp(28px,5vw,64px);align-items:start}
/* five lines of display type in the narrow column read as a wall */
.capture-grid .h2{font-size:clamp(1.75rem,3.1vw,2.5rem)}
.form-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}
.field{display:flex;flex-direction:column;gap:8px}
.field.full{grid-column:1/-1}
.field label{font-family:var(--mono);font-size:.74rem;letter-spacing:.12em;text-transform:uppercase;color:rgba(241,239,232,.68)}
.field input{
  font-family:var(--sans);font-size:1rem;color:var(--cream);background:rgba(7,43,34,.55);
  border:1px solid var(--line-dark);border-radius:10px;padding:14px 16px;transition:border-color .2s,background .2s;
}
.field input::placeholder{color:rgba(241,239,232,.34)}
.field input:focus{outline:none;border-color:var(--amber-bright);background:rgba(7,43,34,.75)}
.formnote{font-size:.88rem;color:rgba(241,239,232,.55);margin:12px 0 0;line-height:1.55}
.getlist{list-style:none;margin:22px 0 0;padding:0;display:grid;gap:13px}
.getlist li{position:relative;padding-left:30px;font-size:1rem;color:rgba(241,239,232,.82);line-height:1.5}
.getlist li::before{
  content:"";position:absolute;left:3px;top:.5em;width:13px;height:7px;
  border-left:2px solid var(--amber-bright);border-bottom:2px solid var(--amber-bright);transform:rotate(-45deg);
}

/* ------------------------------------------------------------------ faq */
.faq{border-top:1px solid var(--line)}
.faq details{border-bottom:1px solid var(--line)}
.faq summary{
  cursor:pointer;list-style:none;padding:22px 44px 22px 0;position:relative;
  font-family:var(--display);font-size:clamp(1.15rem,2vw,1.45rem);color:var(--teal-950);
}
.faq summary::-webkit-details-marker{display:none}
.faq summary::after{
  content:"";position:absolute;right:8px;top:50%;width:12px;height:12px;margin-top:-8px;
  border-right:1.5px solid var(--amber);border-bottom:1.5px solid var(--amber);
  transform:rotate(45deg);transition:transform .3s var(--ease);
}
.faq details[open] summary::after{transform:rotate(-135deg);margin-top:-3px}
.faq .ans{padding:0 0 24px;color:var(--muted);font-size:1.02rem;max-width:70ch;margin:0}
.faq summary:hover{color:var(--teal)}

@media (max-width:900px){ .chan,.capture-grid{grid-template-columns:1fr} }
@media (max-width:560px){ .form-grid{grid-template-columns:1fr} }
"""

MAIL_ICON = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 5.5A1.5 1.5 0 0 1 3.5 4h17A1.5 1.5 0 0 1 22 '
             '5.5v13a1.5 1.5 0 0 1-1.5 1.5h-17A1.5 1.5 0 0 1 2 18.5v-13zm2.2.5 7.8 5.9L19.8 6H4.2zM20 7.9l-7.4 '
             '5.6a1 1 0 0 1-1.2 0L4 7.9V18h16V7.9z"/></svg>')
PHONE_ICON = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.6 2h3.1l1.6 4-2.1 1.5a12.6 12.6 0 0 0 5.9 '
              '5.9L16.6 11l4 1.6v3.1a2.3 2.3 0 0 1-2.5 2.3A16.4 16.4 0 0 1 4.3 4.5 2.3 2.3 0 0 1 6.6 2z"/></svg>')


def _body():
    return f"""<main id="main">

<header class="phero s-cream grain">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> Talk to me</p>
    <h1 class="h1">You will be talking to<br>the person who builds it.</h1>
    <p class="lede">No sales team, no ticket queue. Every route below reaches the same phone.</p>
  </div>
</header>

<section class="s-cream grain" style="padding-top:0">
  <div class="wrap">
    <div class="chan" data-stagger>
      <a class="primary" href="{WA}&text=Hello%20Nahid%2C%20I%20have%20a%20question%20about%20my%20business.">
        <span class="ic">{WA_ICON}</span>
        <h3>WhatsApp</h3>
        <span class="val" dir="ltr">+968 9924 5250</span>
        <span class="when"><i></i>Usually same day</span>
      </a>
      <a href="mailto:hello@aiprofitlab.io">
        <span class="ic">{MAIL_ICON}</span>
        <h3>Email</h3>
        <span class="val">hello@aiprofitlab.io</span>
        <span class="when"><i></i>Within one business day</span>
      </a>
      <a href="tel:+96899245250">
        <span class="ic">{PHONE_ICON}</span>
        <h3>Phone</h3>
        <span class="val" dir="ltr">+968 9924 5250</span>
        <span class="when"><i></i>9am &ndash; 6pm Muscat</span>
      </a>
    </div>
  </div>
</section>

<!-- ================================================== SILENT BUYER TEST -->
<section class="s-dark" id="test">
  <span class="plate" aria-hidden="true">
    <img src="/audit-bg.webp" alt="" width="1000" height="667" loading="lazy" decoding="async">
  </span>
  <div class="wrap">
    <div class="capture-grid">
      <div>
        <p class="eyebrow"><span class="star">{STAR}</span> Free &#183; five a week</p>
        <h2 class="h2">Before you buy, see what a buyer sees.</h2>
        <p class="lede">I contact your business the way a real buyer would &mdash; WhatsApp, form, email, phone.</p>
        <ul class="getlist">
          <li>How fast each channel answered &mdash; measured, not guessed</li>
          <li>What a buyer saw, including in Arabic</li>
          <li>Where that buyer would have gone instead</li>
          <li>No pitch attached</li>
        </ul>
      </div>

      <form id="sbtForm" class="form-grid" novalidate>
        <div class="field">
          <label for="f-name">Your name</label>
          <input id="f-name" name="name" type="text" required placeholder="Your name">
        </div>
        <div class="field">
          <label for="f-biz">Business name</label>
          <input id="f-biz" name="business" type="text" required placeholder="Gulf Lotus Trading">
        </div>
        <div class="field">
          <label for="f-wa">WhatsApp number</label>
          <input id="f-wa" name="whatsapp" type="tel" required placeholder="+968 &hellip;" inputmode="tel">
        </div>
        <div class="field">
          <label for="f-sell">What do you sell?</label>
          <input id="f-sell" name="sells" type="text" required placeholder="Medical consumables, wholesale">
        </div>
        <div class="field full">
          <button class="btn btn-wa" type="submit" style="width:100%">{WA_ICON}Send my details on WhatsApp</button>
          <p class="formnote">Nothing is sent until you press send inside WhatsApp.</p>
        </div>
      </form>
    </div>
  </div>
</section>

<!-- ================================================================ FAQ -->
<section class="s-cream grain">
  <div class="wrap-n">
    <p class="eyebrow"><span class="star">{STAR}</span> The awkward questions</p>
    <h2 class="h2">Asked and answered.</h2>

    <div class="faq" style="margin-top:clamp(22px,3vw,38px)">
      <details>
        <summary>How much does it cost?</summary>
        <p class="ans">Smart Website: OMR 950 one-time. Dashboard +650, autopilot +900, all
          three 2,200. Every number is on <a href="/en/services/#price">the price list</a>.</p>
      </details>
      <details>
        <summary>Is there a monthly fee?</summary>
        <p class="ans">Not to keep anything working. The first year of hosting and care is in the build price.
          The Growth Desk at OMR 75/month is optional.</p>
      </details>
      <details>
        <summary>Do you have clients I can speak to?</summary>
        <p class="ans">Not yet, and I won&#8217;t pretend otherwise. That is why the guarantee is named and both
          demos are open to click: the <a href="/en/demos/#dash">dashboard</a> and the
          <a href="/en/demos/">buyer agent</a>.</p>
      </details>
      <details>
        <summary>What if it doesn&#8217;t work?</summary>
        <p class="ans">The First Inquiry Promise: no real buyer inquiry within 30 days of going live and I rebuild
          it free. If you still don&#8217;t get one, you get your money back.</p>
      </details>
      <details>
        <summary>Do you work in Arabic?</summary>
        <p class="ans">Yes &mdash; both languages first-class, with Arabic checked by a native reader before it ships.</p>
      </details>
      <details>
        <summary>Who am I actually contracting with?</summary>
        <p class="ans">Lotus Gulf International, CR <span dir="ltr">1570092</span>, Bousher, Muscat. AI Profit Lab is
          the brand. Not VAT registered, so invoices carry no VAT line.</p>
      </details>
      <details>
        <summary>How do I pay?</summary>
        <p class="ans">{{PAY_ANSWER}}</p>
      </details>
    </div>
  </div>
</section>

</main>
"""


def body():
    """The one answer on this page that changes the day the gateway is
    approved. Gated on tools/v4/pay.py rather than edited by hand, so the FAQ
    cannot go on saying "no payment is taken on this site" after one is."""
    if pay.PAY_LIVE:
        answer = ('By card on <a href="/en/checkout/">the checkout page</a>, or by bank transfer in '
                  'OMR &mdash; on start, in three payments, or only once it has produced a real inquiry. '
                  'Every structure is set out on <a href="/en/services/#price">the services page</a>.')
    else:
        answer = ('Bank transfer in OMR &mdash; on start, in three payments, or only once it has produced '
                  'a real inquiry. Set out on <a href="/en/services/#price">the services page</a>. You '
                  'can put the order together on <a href="/en/checkout/">the checkout page</a> and I '
                  'send the invoice; card payment on the site is being switched on now.')
    return _body().replace("{PAY_ANSWER}", answer)


JS = """
/* ---------------------------------------------------------------------------
   Silent Buyer Test capture.

   Composes a WhatsApp message rather than posting to a backend, so nothing is
   transmitted until the visitor presses send inside WhatsApp - which is what
   the note under the button promises. Same pattern as en/index-v3.html.
--------------------------------------------------------------------------- */
(function(){
  "use strict";
  var form = document.getElementById("sbtForm");
  if (!form) return;

  form.addEventListener("submit", function(e){
    e.preventDefault();
    var get = function(n){ return (form.elements[n].value || "").trim(); };
    var required = ["name","business","whatsapp","sells"];
    for (var i = 0; i < required.length; i++){
      var n = required[i];
      if (!get(n)){
        form.elements[n].focus();
        if (form.elements[n].reportValidity) form.elements[n].reportValidity();
        return;
      }
    }
    var msg = "Hello Nahid \\u2014 I'd like the free Silent Buyer Test.\\n\\n" +
      "Name: " + get("name") + "\\n" +
      "Business: " + get("business") + "\\n" +
      "WhatsApp: " + get("whatsapp") + "\\n" +
      "We sell: " + get("sells");
    if (typeof gtag === "function") gtag("event","generate_lead",{method:"silent_buyer_test"});
    window.open("https://api.whatsapp.com/send?phone=96899245250&text=" + encodeURIComponent(msg), "_blank", "noopener");
  });
})();
"""

META = dict(
    slug="contact",
    title="Contact | AI Profit Lab — talk to the person who builds it",
    desc=("WhatsApp, email or phone - all reaching the same person in Muscat. Or start with the free "
          "Silent Buyer Test and see what a buyer sees when they message your business."),
    nav="/en/contact/",
    next=("Back to the start", "Never lose a buyer to silence again", "/"),
    schema="""{
  "@context":"https://schema.org",
  "@type":"FAQPage",
  "mainEntity":[
    {"@type":"Question","name":"How much does it cost?","acceptedAnswer":{"@type":"Answer","text":"The Smart Website is OMR 950 one-time. The dashboard adds OMR 650, the autopilot adds OMR 900, and all three together are OMR 2,200."}},
    {"@type":"Question","name":"Is there a monthly fee?","acceptedAnswer":{"@type":"Answer","text":"Not to keep anything working. The first year of hosting, security and care is included in the build price. The Growth Desk at OMR 75 a month is optional and never required."}},
    {"@type":"Question","name":"Do you have clients I can speak to?","acceptedAnswer":{"@type":"Answer","text":"Not yet. That is why there is a named guarantee and why the dashboard and buyer-agent demos are open to click without asking for anything."}},
    {"@type":"Question","name":"What if it doesn't work?","acceptedAnswer":{"@type":"Answer","text":"The First Inquiry Promise: no real buyer inquiry within 30 days of going live and it gets rebuilt free until you get one. If you still don't, you get your money back."}},
    {"@type":"Question","name":"Do you work in Arabic?","acceptedAnswer":{"@type":"Answer","text":"Yes. Both English and Arabic are treated as first-class, and Arabic copy is checked by a native reader before it ships."}},
    {"@type":"Question","name":"Who am I actually contracting with?","acceptedAnswer":{"@type":"Answer","text":"Lotus Gulf International, CR 1570092, South Al Khuwair, Bousher, Muscat. AI Profit Lab is the brand. Not VAT registered, so invoices carry no VAT line."}}
  ]
}
$$SPLIT$$
{"@type":"ContactPage","@id":"https://aiprofitlab.io/en/contact/#contactpage","url":"https://aiprofitlab.io/en/contact/","inLanguage":"en","isPartOf":{"@id":"https://aiprofitlab.io/#website"},"about":{"@id":"https://aiprofitlab.io/#organization"}}""",
)
