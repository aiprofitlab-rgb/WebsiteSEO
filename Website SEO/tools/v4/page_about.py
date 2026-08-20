#!/usr/bin/env python3
"""About.

Written entirely in the first person, and deliberately with no third-person
pronouns for Nahid anywhere on the page. The founder story follows the approved
wording in brand/docs/01-persona-and-avatar.md section 5: an engineer who has
built and run a real distribution business - never implying Omani roots, a
local trade network, or that the distribution experience was built in-market.
"""
from kit import WA, WA_ICON, STAR

CSS = """
/* ----------------------------------------------------------- hero split */
.about-hero{display:grid;grid-template-columns:1.25fr .75fr;gap:clamp(28px,5vw,64px);align-items:center}
.about-hero .h1{font-size:clamp(2.2rem,4.3vw,3.5rem)}
.portrait{position:relative}
.portrait img{width:100%;border-radius:18px;object-fit:cover;aspect-ratio:4/5;filter:saturate(.94)}
/* the brand's single mark, echoed at photo scale */
.portrait::after{
  content:"";position:absolute;right:-14px;bottom:-14px;width:64px;height:64px;border-radius:50%;
  background:var(--amber);z-index:2;
}
.portrait figcaption{
  position:absolute;left:0;right:0;bottom:0;padding:26px 22px 18px;border-radius:0 0 18px 18px;
  background:linear-gradient(transparent,rgba(7,43,34,.86));
  font-family:var(--mono);font-size:.76rem;letter-spacing:.1em;text-transform:uppercase;color:var(--cream);
}

/* ------------------------------------------------------------- the path */
.path{display:grid;grid-template-columns:repeat(4,1fr);gap:0;margin-top:clamp(28px,4vw,48px)}
.path div{position:relative;padding:clamp(22px,2.6vw,32px) clamp(16px,2vw,26px) clamp(22px,2.6vw,32px) 0}
.path div+div{padding-left:clamp(16px,2vw,26px);border-left:1px solid var(--line)}
.s-dark .path div+div{border-left-color:var(--line-dark)}
.path b{display:block;font-family:var(--mono);font-size:.76rem;letter-spacing:.14em;color:var(--amber-text);margin-bottom:12px}
.path h3{font-size:clamp(1.15rem,1.9vw,1.45rem);margin:0 0 8px}
.path p{margin:0;font-size:.95rem;color:var(--muted)}
.s-dark .path p{color:rgba(241,239,232,.7)}
.s-dark .path b{color:var(--amber-bright)}

/* ---------------------------------------------------------- prose block */
.prose p{font-size:clamp(1.1rem,1.7vw,1.3rem);line-height:1.65;color:var(--ink);max-width:60ch;margin:0 0 1.1em}
.prose p.open::first-letter{
  float:left;font-family:var(--display);font-size:3.6em;line-height:.82;padding:.06em .1em 0 0;color:var(--teal);
}
.sigline{display:flex;align-items:center;gap:14px;margin-top:34px}
.sigline span{font-family:var(--mono);font-size:.82rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.sigline .mk{width:34px;height:1px;background:var(--amber)}

/* ------------------------------------------------------------ say no to */
.nope{display:grid;grid-template-columns:repeat(2,1fr);gap:clamp(14px,2vw,22px)}
.nope div{background:rgba(241,239,232,.045);border:1px solid var(--line-dark);border-radius:14px;padding:22px 24px}
.nope b{display:block;font-family:var(--display);font-size:1.2rem;color:var(--cream);font-weight:400;margin-bottom:7px;text-decoration:line-through;text-decoration-color:rgba(166,67,31,.75);text-decoration-thickness:2px}
.nope p{margin:0;font-size:.95rem;color:rgba(241,239,232,.7)}

/* ---------------------------------------------------------- facts sheet */
.facts-sheet{border-top:1px solid var(--line)}
.facts-sheet div{display:grid;grid-template-columns:minmax(150px,.32fr) 1fr;gap:clamp(14px,3vw,40px);padding:17px 0;border-bottom:1px solid var(--line);align-items:baseline}
.facts-sheet dt{font-family:var(--mono);font-size:.78rem;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.facts-sheet dd{margin:0;font-size:1.02rem;color:var(--ink)}

@media (max-width:900px){
  .about-hero{grid-template-columns:1fr}
  .portrait{max-width:400px}
  .path{grid-template-columns:repeat(2,1fr)}
  .path div:nth-child(3){border-left:0;padding-left:0}
  .path div:nth-child(3),.path div:nth-child(4){border-top:1px solid var(--line)}
  .nope{grid-template-columns:1fr}
  .facts-sheet div{grid-template-columns:1fr;gap:4px}
}
"""


def body():
    return f"""<main id="main">

<header class="phero s-cream grain">
  <div class="wrap">
    <div class="about-hero">
      <div>
        <p class="eyebrow"><span class="star">{STAR}</span> Who builds it</p>
        <h1 class="h1">Not an agency.<br>One operator who has run a distribution business.</h1>
        <p class="lede">Which is the only reason I know what a missed 9pm message actually costs, and why
          nothing on this site is written in software vocabulary.</p>
        <div class="btn-row" style="margin-top:30px">
          <a class="btn btn-wa" href="{WA}&text=Hello%20Nahid%2C%20I%20read%20your%20about%20page.">{WA_ICON}Message me directly</a>
          <a class="tlink" href="/en/services-v4/">See what I build <span class="arw">&rarr;</span></a>
        </div>
      </div>
      <figure class="portrait rv" style="margin:0">
        <img src="/nahid-founder-seated-2026.webp" alt="Nahid Abyari, founder of AI Profit Lab, in Muscat" width="600" height="705" loading="eager" decoding="async">
        <figcaption>Nahid Abyari &#183; Founder &#183; Muscat, Oman</figcaption>
      </figure>
    </div>
  </div>
</header>

<!-- ================================================================ STORY -->
<section class="s-panel">
  <div class="wrap-n prose">
    <p class="eyebrow"><span class="star">{STAR}</span> The short version</p>
    <p class="open">I am an engineer who has built and run a real distribution business &mdash; importing, stocking,
      quoting, chasing. Not a consultant who read about it.</p>
    <p>The problem I kept hitting was never strategy. It was a message that arrived at 9pm and got answered
      at 8 the next morning, by which time the buyer had already ordered somewhere else. Multiply that by a
      year and it is not a small number.</p>
    <p>So I started building the thing I wanted: something that answers in both languages, knows the stock
      and the terms, and hands me only the buyers worth my time. AI Profit Lab is that, built for other
      owners in the same position.</p>
    <div class="sigline"><span class="mk"></span><span>Nahid Abyari &#183; Founder</span></div>
  </div>
</section>

<!-- ================================================================= PATH -->
<section class="s-dark">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> How I got here</p>
    <h2 class="h2">Four steps, in order.</h2>

    <div class="path" data-stagger>
      <div><b>01</b><h3>Engineering</h3><p>Trained to take a system apart, find the constraint, and fix that one thing.</p></div>
      <div><b>02</b><h3>Distribution</h3><p>Ran a real trading operation. Catalogues, tiers, freight, invoices, and the follow-up nobody has time for.</p></div>
      <div><b>03</b><h3>The bottleneck</h3><p>Discovered the constraint was not price or product. It was response time.</p></div>
      <div><b>04</b><h3>AI Profit Lab</h3><p>Now I build that fix for other owners &mdash; done for them, in plain language, priced in OMR.</p></div>
    </div>
  </div>
</section>

<!-- =========================================================== PRINCIPLES -->
<section class="s-cream grain">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> How I work</p>
    <h2 class="h2">Four rules I do not bend.</h2>

    <div class="grid g4" style="margin-top:clamp(26px,3.5vw,44px)" data-stagger>
      <article class="card"><span class="n">01</span><h3>Plain language</h3><p>If a sentence needs software vocabulary to work, the sentence is wrong.</p></article>
      <article class="card"><span class="n">02</span><h3>Prices in public</h3><p>Every number is on the site. You should never sit through a call to learn what something costs.</p></article>
      <article class="card"><span class="n">03</span><h3>What&#8217;s not included, first</h3><p>Stated as clearly as what is &mdash; before any money moves.</p></article>
      <article class="card"><span class="n">04</span><h3>No invented numbers</h3><p>If a figure can&#8217;t be sourced, it doesn&#8217;t go on the page. That is why you see no statistics here.</p></article>
    </div>
  </div>
</section>

<!-- =========================================================== SAY NO TO -->
<section class="s-teal">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> Being useful about fit</p>
    <h2 class="h2">Who I turn away.</h2>
    <p class="lede">Saying this on a public page costs me enquiries. It also saves us both a wasted month.</p>

    <div class="nope" style="margin-top:clamp(26px,3.5vw,44px)" data-stagger>
      <div><b>Enterprise and ERP-scale buyers</b><p>Different weight class, long procurement. You want a systems integrator, and you should have one.</p></div>
      <div><b>Anyone shopping purely on price</b><p>I am not the cheapest option in Oman and will not pretend to be. I compete on the work being done for you.</p></div>
      <div><b>Businesses with nothing digital yet</b><p>If there is no WhatsApp presence and no buyer flow at all, there is nothing here to automate yet.</p></div>
      <div><b>&ldquo;Make us go viral&rdquo;</b><p>Wrong problem and wrong measure. I build systems that answer buyers, not campaigns that chase attention.</p></div>
    </div>
  </div>
</section>

<!-- ============================================================== FACTS -->
<section class="s-panel">
  <div class="wrap-n">
    <p class="eyebrow"><span class="star">{STAR}</span> The unglamorous facts</p>
    <h2 class="h2">Who you are actually dealing with.</h2>
    <dl class="facts-sheet" style="margin-top:clamp(24px,3vw,38px)">
      <div><dt>Brand</dt><dd>AI Profit Lab</dd></div>
      <div><dt>Legal entity</dt><dd>Lotus Gulf International <span lang="ar" dir="rtl">&#1604;&#1608;&#1578;&#1587; &#1575;&#1604;&#1582;&#1604;&#1610;&#1580; &#1575;&#1604;&#1593;&#1575;&#1604;&#1605;&#1610;&#1577; &#1588; &#1588; &#1608;</span> &mdash; CR <span dir="ltr">1570092</span></dd></div>
      <div><dt>VAT</dt><dd>Not VAT registered (TIN <span dir="ltr">2317725</span>). Invoices carry no VAT line.</dd></div>
      <div><dt>Where</dt><dd>South Al Khuwair, Bousher, Muscat, Sultanate of Oman</dd></div>
      <div><dt>Languages</dt><dd>English and Arabic, both delivered as first-class</dd></div>
      <div><dt>Who does the work</dt><dd>Me. You will not be handed to an account manager.</dd></div>
      <div><dt>Reach me</dt><dd><a href="{WA}&text=Hello%20Nahid">WhatsApp <span dir="ltr">+968 9924 5250</span></a> &#183; <a href="mailto:hello@aiprofitlab.io">hello@aiprofitlab.io</a></dd></div>
    </dl>
  </div>
</section>

<!-- ================================================================ CTA -->
<section class="s-dark pad-s">
  <div class="wrap">
    <div style="display:flex;gap:clamp(20px,4vw,50px);align-items:center;justify-content:space-between;flex-wrap:wrap">
      <div style="flex:1 1 380px">
        <h2 class="h2" style="margin-bottom:12px">Still reading? Then let&#8217;s test your business.</h2>
        <p class="lede" style="margin:0">Free, takes me about forty minutes, and you keep the scorecard whatever you decide.</p>
      </div>
      <div class="btn-row">
        <a class="btn btn-amber" href="/en/contact-v4/#test">Get the Silent Buyer Test</a>
        <a class="btn btn-ghost" href="/en/services-v4/#price">See the prices</a>
      </div>
    </div>
  </div>
</section>

</main>
"""


META = dict(
    slug="about-v4",
    title="About | AI Profit Lab — one operator, not an agency",
    desc=("An engineer who has built and run a real distribution business, now building AI systems for "
          "trading and distribution owners in Oman. Including who I turn away."),
    nav="/en/about-v4/",
    next=("Next", "Talk to me", "/en/contact-v4/"),
    schema="""{
  "@context":"https://schema.org",
  "@type":"AboutPage",
  "mainEntity":{
    "@type":"Person",
    "name":"Nahid Abyari",
    "jobTitle":"Founder",
    "email":"hello@aiprofitlab.io",
    "telephone":"+968 9924 5250",
    "worksFor":{"@type":"Organization","name":"AI Profit Lab","parentOrganization":{"@type":"Organization","name":"Lotus Gulf International","identifier":"CR 1570092"}},
    "address":{"@type":"PostalAddress","addressLocality":"Bousher","addressRegion":"Muscat","addressCountry":"OM"}
  }
}""",
)
