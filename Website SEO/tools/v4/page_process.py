#!/usr/bin/env python3
"""How it works.

The page is a timeline you watch fill in, not a list of steps you read. Each
step carries a small mock of the artefact it actually produces - a scorecard, a
call agenda, a build board, a launch checklist - so the reader sees what they
will be handed rather than being told about it.
"""
from kit import WA, WA_ICON, STAR

CSS = """
/* --------------------------------------------------------- the week bar */
.weekbar{margin-top:clamp(26px,3.5vw,44px)}
.wb{display:grid;grid-template-columns:1fr 2fr 3fr 1fr 1fr;gap:4px;margin-bottom:12px}
.wb i{
  display:block;height:16px;border-radius:4px;background:var(--teal);
  transform-origin:0 50%;transform:scaleX(0);transition:transform .8s var(--ease);transition-delay:var(--d,0s);
}
.weekbar.vis .wb i{transform:none}
html:not(.js) .wb i{transform:none}
.wb i:nth-child(1){background:var(--amber)}
.wb i:nth-child(2){background:var(--teal-600)}
.wb i:nth-child(3){background:var(--teal)}
.wb i:nth-child(4){background:var(--teal-900)}
.wb i:nth-child(5){background:var(--wa)}
.wbl{display:grid;grid-template-columns:1fr 2fr 3fr 1fr 1fr;gap:4px}
.wbl span{font-family:var(--mono);font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);line-height:1.5}
.wbl b{display:block;color:var(--teal-950);font-weight:500}
.wb{min-height:16px}

/* ------------------------------------------------------------- the steps */
.steps{margin-top:clamp(40px,6vw,80px)}
.step-row{display:grid;grid-template-columns:88px 1fr 1fr;gap:clamp(18px,3vw,46px);align-items:start;position:relative;padding-bottom:clamp(46px,6vw,84px)}
.step-row:last-child{padding-bottom:0}
.step-rail{position:relative;display:flex;flex-direction:column;align-items:center;align-self:stretch}
.step-rail .dotn{
  width:56px;height:56px;border-radius:50%;border:1px solid var(--line);background:var(--white);
  display:grid;place-items:center;font-family:var(--mono);font-size:.92rem;color:var(--muted);
  flex:none;z-index:2;transition:background .5s,color .5s,border-color .5s,transform .5s var(--ease);
}
.step-row.vis .dotn{background:var(--teal-950);color:var(--amber-bright);border-color:var(--teal-950);transform:scale(1.04)}
.step-rail .ln{flex:1;width:1px;background:var(--line);margin-top:10px;transform:scaleY(0);transform-origin:50% 0;transition:transform .9s var(--ease) .15s}
.step-row.vis .ln{transform:none}
.step-row:last-child .ln{display:none}
html:not(.js) .step-rail .ln{transform:none}
.step-body h3{font-size:clamp(1.4rem,2.6vw,2rem);margin:6px 0 12px}
.step-body p{color:var(--muted);font-size:1.02rem;margin:0 0 14px}
.step-when{font-family:var(--mono);font-size:.78rem;letter-spacing:.12em;text-transform:uppercase;color:var(--amber-text);display:block;margin-bottom:2px}

/* ----------------------------------------------------------- mock cards */
.mock{background:var(--white);border:1px solid var(--line);border-radius:14px;padding:20px 22px;box-shadow:0 30px 56px -44px rgba(7,43,34,.55)}
.mock .mh{display:flex;justify-content:space-between;align-items:baseline;border-bottom:1px solid var(--line);padding-bottom:11px;margin-bottom:14px}
.mock .mh b{font-family:var(--display);font-size:1.1rem;color:var(--teal-950);font-weight:400}
.mock .mh span{font-family:var(--mono);font-size:.66rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.scorerow{display:flex;justify-content:space-between;align-items:center;gap:14px;padding:9px 0;border-bottom:1px dotted var(--line);font-size:.92rem}
.scorerow:last-child{border-bottom:0}
.scorerow em{font-style:normal;color:var(--muted)}
.grade{font-family:var(--mono);font-size:.78rem;letter-spacing:.06em;padding:3px 10px;border-radius:99px;white-space:nowrap}
.grade.bad{background:rgba(166,67,31,.12);color:var(--alert)}
.grade.mid{background:rgba(186,117,23,.14);color:var(--amber)}
.grade.good{background:rgba(31,175,94,.14);color:#127A41}
.checks{list-style:none;margin:0;padding:0}
.checks li{position:relative;padding:8px 0 8px 28px;font-size:.94rem;border-bottom:1px dotted var(--line)}
.checks li:last-child{border-bottom:0}
.checks li::before{
  content:"";position:absolute;left:2px;top:1.15em;width:13px;height:7px;border-left:2px solid var(--wa);
  border-bottom:2px solid var(--wa);transform:rotate(-45deg);
}
.board{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px}
.board .col{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:10px}
.board .col b{display:block;font-family:var(--mono);font-size:.6rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-bottom:8px}
.board .t{background:var(--white);border:1px solid var(--line);border-radius:6px;padding:7px 8px;font-size:.74rem;line-height:1.35;margin-bottom:6px;color:var(--ink)}
.board .t:last-child{margin-bottom:0}
.board .col.done .t{color:var(--muted);text-decoration:line-through;text-decoration-color:var(--line)}

/* ------------------------------------------------------------ you-give */
.give{display:grid;grid-template-columns:repeat(3,1fr);gap:clamp(14px,2vw,22px)}
.give div{border:1px solid var(--line-dark);border-radius:14px;padding:24px 26px;background:rgba(241,239,232,.045)}
.give b{display:block;font-family:var(--display);font-size:1.3rem;color:var(--cream);font-weight:400;margin-bottom:7px}
.give p{margin:0;font-size:.96rem;color:rgba(241,239,232,.7)}
.give .t{font-family:var(--mono);font-size:.7rem;letter-spacing:.12em;text-transform:uppercase;color:var(--amber-bright);display:block;margin-bottom:12px}

@media (max-width:900px){
  /* minmax(0,1fr): the automatic minimum of a plain 1fr track is the widest
     thing inside it, so the 3-column .board held this row at ~430px and the
     right edge of every step was clipped on a phone. */
  .step-row{grid-template-columns:56px minmax(0,1fr)}
  .step-row .art{grid-column:2}
  .wb,.wbl{grid-template-columns:1fr 1fr}
  .wbl span:nth-child(n+3){margin-top:6px}
  .give{grid-template-columns:1fr}
  .step-rail .dotn{width:44px;height:44px;font-size:.8rem}
}
"""


def _step(n, when, title, para, art, last=False):
    return f"""<div class="step-row rv">
  <div class="step-rail"><span class="dotn">{n}</span><span class="ln"></span></div>
  <div class="step-body">
    <span class="step-when">{when}</span>
    <h3>{title}</h3>
    <p>{para}</p>
  </div>
  <div class="art">{art}</div>
</div>"""


def body():
    scorecard = """<div class="mock">
  <div class="mh"><b>Silent Buyer Test</b><span>Your scorecard</span></div>
  <div class="scorerow"><em>Reply to a WhatsApp message at 9pm</em><span class="grade bad">No reply</span></div>
  <div class="scorerow"><em>Reply to the same message next morning</em><span class="grade mid">14h 25m</span></div>
  <div class="scorerow"><em>Answered in Arabic</em><span class="grade bad">No</span></div>
  <div class="scorerow"><em>Bulk pricing offered</em><span class="grade bad">No</span></div>
  <div class="scorerow"><em>Website found on Google</em><span class="grade good">Page 1</span></div>
  <div class="scorerow"><em>Business named by ChatGPT</em><span class="grade bad">Not mentioned</span></div>
</div>
<p class="lede" style="font-size:.86rem;margin:14px 0 0">Illustration of the format. Yours is filled in with what actually happened.</p>"""

    agenda = """<div class="mock">
  <div class="mh"><b>The call</b><span>30 minutes</span></div>
  <ul class="checks">
    <li>Where the money is leaking, in your words</li>
    <li>What your buyers actually ask, and in which language</li>
    <li>Which of the three systems fixes it &mdash; often only one</li>
    <li>The number, and how you would rather pay it</li>
    <li>What I will <em>not</em> be doing for you</li>
  </ul>
</div>
<p class="lede" style="font-size:.86rem;margin:14px 0 0">No slides. No proposal to sit through. If it isn&#8217;t a fit I will say so on the call.</p>"""

    board = """<div class="mock">
  <div class="mh"><b>Your build</b><span>Day 3 of 7</span></div>
  <div class="board">
    <div class="col done"><b>Done</b>
      <div class="t">Catalogue &amp; terms captured</div>
      <div class="t">EN + AR copy drafted</div>
      <div class="t">Structure signed off</div>
    </div>
    <div class="col"><b>Building</b>
      <div class="t">Buyer agent trained on your stock</div>
      <div class="t">WhatsApp handoff wired</div>
      <div class="t">Quote flow</div>
    </div>
    <div class="col"><b>Next</b>
      <div class="t">Search &amp; AI-answer setup</div>
      <div class="t">Your review pass</div>
      <div class="t">Go live</div>
    </div>
  </div>
</div>"""

    launch = """<div class="mock">
  <div class="mh"><b>Go-live checklist</b><span>Before I hand it over</span></div>
  <ul class="checks">
    <li>Tested from a real phone, on a real network</li>
    <li>Arabic and English both answered correctly</li>
    <li>A test buyer routed to your WhatsApp</li>
    <li>Google Business Profile pointing at the right place</li>
    <li>Your team shown how it works, once, live</li>
    <li>Hosting, security and care running for a year</li>
  </ul>
</div>"""

    promise = """<div class="mock" style="background:var(--teal-950);border-color:var(--teal-900)">
  <div class="mh" style="border-bottom-color:rgba(241,239,232,.16)">
    <b style="color:var(--cream)">The First Inquiry Promise</b><span style="color:var(--amber-pale)">30 days</span>
  </div>
  <p style="font-family:var(--display);font-size:1.25rem;line-height:1.35;color:var(--cream);margin:0 0 14px">
    No real buyer inquiry within 30 days of going live? I rebuild it free until you get one.
    If you still don&#8217;t, you get your money back.</p>
  <p style="font-family:var(--mono);font-size:.76rem;letter-spacing:.1em;text-transform:uppercase;color:var(--amber-pale);margin:0">
    Nahid Abyari &#183; Founder</p>
</div>"""

    steps = "\n".join([
        _step("01", "Day 0 &#183; free", "The Silent Buyer Test",
              "I message your business the way a buyer would &mdash; in Arabic, after hours &mdash; and send you a "
              "scorecard of what happened. You owe me nothing, and most people stop here having learned something.",
              scorecard),
        _step("02", "Day 0 &#183; 30 minutes", "One honest conversation",
              "We look at the scorecard together and I tell you which system fixes it, what it costs, and "
              "whether it is worth doing at all.",
              agenda),
        _step("03", "Days 1&ndash;6", "The build",
              "I build it. You get a link on day three to look at real progress, not a status email. "
              "One round of changes is expected, not charged for.",
              board),
        _step("04", "Day 7", "Go live",
              "Tested from a real phone before anyone else sees it. Your team gets shown how it works, live, "
              "in one sitting.",
              launch),
        _step("05", "Days 7&ndash;37", "The 30-day promise",
              "The clock starts the day it goes live. If it produces no real buyer inquiry in thirty days, "
              "I rebuild it free &mdash; and if that still fails, you get your money back.",
              promise),
    ])

    return f"""<main id="main">

<header class="phero s-cream grain">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> How it works</p>
    <h1 class="h1">First message to live system,<br>in about a week.</h1>
    <p class="lede">Five steps. The first one is free, the second one is a conversation, and you can stop
      after either without owing anything.</p>

    <div class="weekbar rv">
      <div class="wb"><i style="--d:0s"></i><i style="--d:.1s"></i><i style="--d:.2s"></i><i style="--d:.3s"></i><i style="--d:.4s"></i></div>
      <div class="wbl">
        <span><b>Day 0</b>Test &amp; call</span>
        <span><b>Days 1&ndash;2</b>Copy &amp; structure</span>
        <span><b>Days 3&ndash;5</b>Build</span>
        <span><b>Day 6</b>Your review</span>
        <span><b>Day 7</b>Live</span>
      </div>
    </div>
  </div>
</header>

<section class="s-panel">
  <div class="wrap">
    <div class="steps">
      {steps}
    </div>
  </div>
</section>

<!-- ======================================================== WHAT I NEED -->
<section class="s-dark">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> What I need from you</p>
    <h2 class="h2">Three things. That is the whole ask.</h2>
    <p class="lede">You are not going to be managing this build. If you are, I have done it wrong.</p>

    <div class="give" style="margin-top:clamp(26px,3.5vw,44px)" data-stagger>
      <div><span class="t">About an hour</span><b>Your catalogue and terms</b><p>What you sell, at what tiers, delivered where, in how long.</p></div>
      <div><span class="t">About 30 minutes</span><b>One review pass</b><p>You read it, mark what is wrong, I fix it. One round is expected.</p></div>
      <div><span class="t">Five minutes</span><b>Access, not passwords</b><p>The WhatsApp number the leads should land on. Nothing sensitive by message.</p></div>
    </div>
  </div>
</section>

<!-- ==================================================== WHAT CAN GO WRONG -->
<section class="s-cream grain">
  <div class="wrap-n">
    <p class="eyebrow"><span class="star">{STAR}</span> Being straight with you</p>
    <h2 class="h2">Where this goes wrong.</h2>
    <div class="grid" style="margin-top:26px" data-stagger>
      <article class="card"><span class="n">01</span><h3>You never send the catalogue</h3><p>The single most common way a build stalls. The agent is only as good as what it knows about your stock and your terms.</p></article>
      <article class="card"><span class="n">02</span><h3>Nobody watches the WhatsApp</h3><p>It hands you live buyers. If the phone goes unread for two days, you have moved the silence, not removed it.</p></article>
      <article class="card"><span class="n">03</span><h3>You needed an ERP</h3><p>If the real problem is multi-branch inventory and finance in one system, this is the wrong tool and I will tell you on the call.</p></article>
    </div>
  </div>
</section>

<!-- ================================================================ CTA -->
<section class="s-teal pad-s">
  <div class="wrap">
    <div style="display:flex;gap:clamp(20px,4vw,50px);align-items:center;justify-content:space-between;flex-wrap:wrap">
      <div style="flex:1 1 380px">
        <h2 class="h2" style="margin-bottom:12px">Step one costs nothing.</h2>
        <p class="lede" style="margin:0">Let me message your business as a buyer would, and send you the scorecard.</p>
      </div>
      <div class="btn-row">
        <a class="btn btn-amber" href="/en/contact/#test">Get the Silent Buyer Test</a>
        <a class="btn btn-ghost" href="{WA}&text=Hello%20Nahid%2C%20I%20read%20how%20it%20works%20and%20I%20have%20a%20question.">{WA_ICON}Just ask me something</a>
      </div>
    </div>
  </div>
</section>

</main>
"""


META = dict(
    slug="process",
    title="How it works | AI Profit Lab — from first message to live in about a week",
    desc=("Five steps: a free Silent Buyer Test, one honest conversation, the build, go-live, and a "
          "30-day promise. What I need from you, and where it goes wrong."),
    nav="/en/process/",
    next=("Next", "Who builds it", "/en/about/"),
    schema="""{
  "@context":"https://schema.org",
  "@type":"HowTo",
  "name":"How an AI Profit Lab build runs",
  "totalTime":"P7D",
  "step":[
    {"@type":"HowToStep","position":1,"name":"The Silent Buyer Test","text":"I message your business the way a buyer would and send you a scorecard of what happened. Free."},
    {"@type":"HowToStep","position":2,"name":"One honest conversation","text":"Thirty minutes on which system fixes the leak, what it costs, and whether it is worth doing."},
    {"@type":"HowToStep","position":3,"name":"The build","text":"Days one to six, with a live link on day three and one round of changes included."},
    {"@type":"HowToStep","position":4,"name":"Go live","text":"Tested from a real phone, with your team shown how it works in one sitting."},
    {"@type":"HowToStep","position":5,"name":"The 30-day promise","text":"No real buyer inquiry within 30 days? It gets rebuilt free, or your money back."}
  ]
}""",
)
