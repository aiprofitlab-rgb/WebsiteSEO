#!/usr/bin/env python3
"""Services / What I build.

Every system gets a *picture of itself* rather than a paragraph describing
itself: a phone thread, a dashboard, a follow-up schedule. Prices are published
in full - the whole ladder, one price per rung - because the page's argument
is that you should not need a sales call to learn a number.
Figures are the ones already published on en/index-v3.html.
"""
import pay
from kit import WA, WA_ICON, STAR, SHIELD

CSS = """
/* ---------------------------------------------------------- stat strip */
.stats{display:grid;grid-template-columns:repeat(4,1fr);border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.stats div{padding:clamp(22px,3vw,34px) clamp(14px,2vw,26px);border-right:1px solid var(--line)}
.stats div:last-child{border-right:0}
.stats b{display:block;font-family:var(--display);font-size:clamp(1.9rem,3.6vw,2.9rem);line-height:1;color:var(--teal-950);margin-bottom:8px;font-weight:400}
/* `> span`, not `span`: the first cell's figure is a <span data-count> nested
   inside the <b> so the motion kit can count it up, and an unscoped `.stats
   span` caught it too - which rendered "168" as an 0.78rem mono label beside
   three 2.9rem display figures. */
.stats div>span{font-family:var(--mono);font-size:.78rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);line-height:1.6;display:block}

/* ------------------------------------------------------ system blocks */
.sysblock{display:grid;grid-template-columns:1fr 1fr;gap:clamp(28px,5vw,72px);align-items:center}
.sysblock.flip .art{order:-1}
.sysblock+.sysblock{margin-top:clamp(64px,9vw,130px)}
.sysblock .kicker{font-family:var(--mono);font-size:.85rem;letter-spacing:.16em;color:var(--amber-text);display:block;margin-bottom:14px}
.sysblock h3{font-size:clamp(1.8rem,3.4vw,2.6rem);line-height:1.12;margin:0 0 16px}
.sysblock p{color:var(--muted);font-size:1.06rem}
.s-dark .sysblock p{color:rgba(241,239,232,.75)}
.deliver{list-style:none;margin:22px 0;padding:0;display:grid;gap:11px}
.deliver li{position:relative;padding-left:28px;font-size:1rem;line-height:1.5}
.deliver li::before{
  content:"";position:absolute;left:0;top:.52em;width:11px;height:11px;border-radius:50%;
  border:2px solid var(--amber);
}
.pricetag{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin:24px 0 20px}
.s-dark .sysblock .kicker{color:var(--amber-bright)}
.pricetag b{font-family:var(--display);font-size:clamp(1.7rem,3vw,2.3rem);color:var(--teal-950);font-weight:400}
.s-dark .pricetag b{color:var(--cream)}
.pricetag span{font-family:var(--mono);font-size:.85rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.s-dark .pricetag span{color:rgba(241,239,232,.6)}

/* --------------------------------------------------------- phone mock */
.phone{
  width:min(320px,86%);margin-inline:auto;border-radius:34px;background:var(--teal-950);
  padding:11px;box-shadow:0 44px 80px -46px rgba(7,43,34,.75);border:1px solid rgba(35,43,38,.2);
}
.phone .screen{border-radius:25px;overflow:hidden;background:#E9E2D6}
.phone .bar{background:var(--teal-900);color:var(--cream);padding:13px 15px;display:flex;align-items:center;gap:11px}
.phone .bar .av{width:32px;height:32px;border-radius:50%;background:var(--teal);display:grid;place-items:center;font-family:var(--mono);font-size:.72rem;color:var(--cream);flex:none}
.phone .bar b{display:block;font-weight:500;font-size:.92rem;font-family:var(--sans)}
.phone .bar em{display:block;font-style:normal;font-family:var(--mono);font-size:.66rem;letter-spacing:.08em;color:var(--amber-pale)}
.thread{padding:16px 13px 18px;display:flex;flex-direction:column;gap:9px;min-height:330px}
.msg{max-width:83%;padding:9px 13px;border-radius:14px;font-size:.86rem;line-height:1.45;position:relative}
.msg.them{background:var(--white);color:var(--ink);align-self:flex-start;border-bottom-left-radius:4px}
.msg.us{background:#D6F2DF;color:#123A25;align-self:flex-end;border-bottom-right-radius:4px}
.msg time{display:block;font-family:var(--mono);font-size:.6rem;color:rgba(35,43,38,.45);margin-top:4px}
.msg.ar{direction:rtl;text-align:right;font-size:.92rem}
.typing{align-self:flex-start;background:var(--white);border-radius:14px;padding:11px 14px;display:flex;gap:4px}
.typing i{width:6px;height:6px;border-radius:50%;background:var(--muted);animation:blink 1.4s infinite}
.typing i:nth-child(2){animation-delay:.2s}.typing i:nth-child(3){animation-delay:.4s}
@keyframes blink{0%,60%,100%{opacity:.3}30%{opacity:1}}

/* ------------------------------------------------------ dashboard mock */
.dash{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:clamp(16px,2vw,22px);box-shadow:0 40px 70px -50px rgba(7,43,34,.6)}
.dash .dhead{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:14px}
.dash .dhead b{font-family:var(--display);font-size:1.15rem;color:var(--teal-950);font-weight:400}
.dash .dhead span{font-family:var(--mono);font-size:.66rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:9px;margin-bottom:12px}
.kpi{background:var(--white);border:1px solid var(--line);border-radius:10px;padding:11px 12px}
.kpi span{display:block;font-family:var(--mono);font-size:.6rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-bottom:5px}
.kpi b{font-family:var(--display);font-size:1.25rem;color:var(--teal-950);font-weight:400;display:block;line-height:1}
.kpi i{font-style:normal;font-family:var(--mono);font-size:.62rem;color:var(--wa)}
.kpi i.dn{color:var(--alert)}
.alertrow{background:var(--white);border:1px solid var(--line);border-left:3px solid var(--alert);border-radius:8px;padding:11px 13px;margin-bottom:8px}
.alertrow em{font-style:normal;font-family:var(--mono);font-size:.6rem;letter-spacing:.1em;text-transform:uppercase;color:var(--alert);display:block;margin-bottom:4px}
.alertrow p{margin:0;font-size:.84rem;color:var(--ink);line-height:1.4}
.alertrow.ok{border-left-color:var(--wa)}
.alertrow.ok em{color:var(--wa)}

/* ------------------------------------------------------- autopilot rail */
.rail-svg{width:100%;height:auto;display:block}

/* -------------------------------------------------------------- table */
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:16px;background:var(--white)}
table.t{width:100%;border-collapse:collapse;min-width:660px}
table.t caption{text-align:left;padding:20px clamp(16px,2vw,24px) 0;font-family:var(--mono);font-size:.78rem;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
table.t th,table.t td{padding:17px clamp(14px,1.8vw,22px);text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
table.t thead th{font-family:var(--mono);font-size:.76rem;font-weight:500;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);background:var(--panel)}
table.t td.n,table.t th.n{text-align:right;font-family:var(--mono);white-space:nowrap;font-variant-numeric:tabular-nums}
table.t tbody tr:last-child td{border-bottom:0}
table.t tr.hi{background:rgba(186,117,23,.055)}
table.t tr.hi td:first-child{box-shadow:inset 3px 0 0 var(--amber)}
table.t td b{font-weight:600;color:var(--teal-950)}
table.t .mini{display:block;font-size:.86rem;color:var(--muted);margin-top:5px;line-height:1.45;font-weight:400}

/* ---------------------------------------------------------- pay cards */
.pay-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:clamp(16px,2vw,24px)}
.pay{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:clamp(22px,2.6vw,32px);display:flex;flex-direction:column}
.pay.hero-pay{background:var(--teal-950);border-color:var(--teal-900);color:var(--cream)}
.pay.hero-pay h3,.pay.hero-pay .price{color:var(--cream)}
.pay.hero-pay p{color:rgba(241,239,232,.76)}
.pay .badge{font-family:var(--mono);font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;color:var(--amber-text);margin-bottom:14px;display:block}
.pay.hero-pay .badge{color:var(--amber-bright)}
.pay h3{font-size:1.45rem;margin:0 0 6px}
.pay .price{display:block;font-family:var(--display);font-size:clamp(1.9rem,3.4vw,2.5rem);color:var(--teal-950);margin-bottom:14px;line-height:1}
.pay p{font-size:.97rem;color:var(--muted);flex:1}
.pay .btn,.pay .tlink{margin-top:16px;align-self:flex-start}

/* ----------------------------------------------------- not-included */
.nolog{background:var(--panel-2);border:1px solid var(--line);border-radius:16px;padding:clamp(24px,3vw,38px)}
.nolog ul{list-style:none;margin:18px 0 0;padding:0;display:grid;gap:14px}
.nolog li{position:relative;padding-left:34px;font-size:1rem;line-height:1.55;color:var(--ink)}
.nolog li::before{
  content:"";position:absolute;left:0;top:.42em;width:16px;height:16px;border-radius:50%;
  border:1.5px solid var(--alert);
}
.nolog li::after{content:"";position:absolute;left:4px;top:1.06em;width:8px;height:1.5px;background:var(--alert)}

/* ------------------------------------------------ the visibility desk
   The one monthly service on the page, so it gets its own furniture rather
   than a fourth .sysblock: the argument it has to make is "why does this
   repeat", which is prose, not a product shot.

   Direction-sensitive rules here use LOGICAL properties (border-inline-start)
   rather than border-left plus a [dir=rtl] override in rtl.py. The block is
   pure prose with no mirrored artwork, so the automatic flip is correct in
   both languages and there is nothing for the Arabic layer to remember. */
.vis-defs{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:clamp(16px,2vw,24px);margin:clamp(26px,3.4vw,42px) 0}
.vis-def{background:var(--white);border:1px solid var(--line);border-radius:16px;padding:clamp(20px,2.4vw,30px)}
.vis-def h3{font-size:clamp(1.08rem,1.9vw,1.3rem);line-height:1.28;color:var(--teal-950);margin:0 0 12px}
.vis-def p{margin:0;font-size:1rem;line-height:1.62;color:var(--muted)}
.vis-def b,.vis-why b,.vis-split b{color:var(--teal-950);font-weight:600}
.vis-why{background:var(--white);border:1px solid var(--line);border-inline-start:3px solid var(--amber);border-radius:16px;padding:clamp(22px,2.8vw,34px)}
.vis-why h3{margin:0 0 14px}
.vis-why p{color:var(--muted);font-size:1.04rem;line-height:1.66;margin:0 0 14px}
.vis-why p:last-child{margin-bottom:0}
.vis-split{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:clamp(26px,4vw,60px);margin-top:clamp(30px,4vw,52px)}
.vis-split h3{margin:0}
.vis-split p{color:var(--muted);font-size:1rem;line-height:1.62;margin:0}
.vis-gtee{background:var(--white);border:1.5px solid var(--teal);border-radius:16px;
  padding:clamp(20px,2.6vw,30px);margin-top:clamp(30px,4vw,50px);
  display:flex;gap:clamp(14px,2vw,20px);align-items:flex-start}
.vis-gtee svg{flex:none;width:34px;height:34px;fill:var(--teal);margin-top:2px}
.vis-gtee h3{margin:0 0 8px}
.vis-gtee p{margin:0;font-size:1.02rem;line-height:1.62;color:var(--ink)}
.vis-gtee .fine{margin-top:12px;font-size:.9rem;color:var(--muted);line-height:1.58}
.vis-gtee b{color:var(--teal-950);font-weight:600}
.vis-foot{display:flex;align-items:center;justify-content:space-between;gap:clamp(16px,3vw,40px);flex-wrap:wrap;
  margin-top:clamp(30px,4vw,50px);padding-top:clamp(24px,3vw,36px);border-top:1px solid var(--line)}
.vis-foot .pricetag{margin:0}

@media (max-width:900px){
  .stats{grid-template-columns:repeat(2,1fr)}
  .stats div:nth-child(2){border-right:0}
  .stats div:nth-child(1),.stats div:nth-child(2){border-bottom:1px solid var(--line)}
  .sysblock{grid-template-columns:1fr}
  .sysblock.flip .art{order:0}
  .vis-defs,.vis-split{grid-template-columns:minmax(0,1fr)}
  .vis-gtee{flex-direction:column;gap:12px}
  .pay-grid{grid-template-columns:1fr}
}
"""


def body():
    p1 = f"""<main id="main">

<header class="phero s-cream grain">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> What I build</p>
    <h1 class="h1">You describe the problem.<br>I build the system that removes it.</h1>
    <p class="lede">Three systems, each one a fixed, one-time build &mdash; plus one monthly desk, for the
      single job that genuinely never finishes. No retainer is required to keep anything running, and
      every price is on this page.</p>
    <div class="btn-row" style="margin-top:30px">
      <a class="btn btn-teal" href="#price">Jump to the price list</a>
      <a class="tlink" href="/en/process/">How a build actually runs <span class="arw">&rarr;</span></a>
    </div>
  </div>
</header>

<div class="stats" aria-label="At a glance">
  <div><b><span data-count="168">168</span></b><span>Hours covered per week,<br>including Fridays</span></div>
  <div><b>~1 week</b><span>From kickoff<br>to going live</span></div>
  <div><b>2</b><span>Languages, both<br>first-class</span></div>
  <div><b>OMR 0</b><span>Required monthly<br>to keep it running</span></div>
</div>

<!-- ==================================================== 01 - THE SMART WEBSITE -->
<section class="s-cream grain" id="smart-website">
  <div class="wrap">
    <div class="sysblock">
      <div>
        <span class="kicker">01 &#183; The flagship</span>
        <h3>The Smart Website</h3>
        <p>A bilingual site with a buyer agent inside it. It answers in Arabic or English, knows your
          catalogue and your delivery terms, and hands the serious ones to your WhatsApp.</p>
        <ul class="deliver">
          <li>An employee who never sleeps &mdash; 4am, Friday, Eid</li>
          <li>Hot leads pushed straight to your phone</li>
          <li>A wholesale quote flow, not a retail &ldquo;contact us&rdquo; box</li>
          <li>A short note on who visited and what they were after</li>
          <li>Found by Google <em>and</em> by ChatGPT</li>
          <li>A year of hosting, security and care included</li>
        </ul>
        <div class="pricetag"><b>OMR 950</b><span>One-time</span></div>
        <a class="btn btn-wa" href="{WA}&text=Hello%20Nahid%2C%20I%20want%20to%20ask%20about%20the%20Smart%20Website.">{WA_ICON}Ask about a build slot</a>
      </div>
      <div class="art rv">
        <div class="phone">
          <div class="screen">
            <div class="bar"><span class="av">AI</span><span><b>Gulf Lotus Trading</b><em>Typically replies instantly</em></span></div>
            <div class="thread">
              <div class="msg them ar" lang="ar" dir="rtl">&#1607;&#1604; &#1578;&#1608;&#1589;&#1604;&#1608;&#1606; &#1573;&#1604;&#1609; &#1589;&#1581;&#1575;&#1585;&#1567; &#1608;&#1603;&#1605; &#1587;&#1593;&#1585; &#1575;&#1604;&#1580;&#1605;&#1604;&#1577;&#1567;<time>21:47</time></div>
              <div class="msg us ar" lang="ar" dir="rtl">&#1606;&#1593;&#1605;&#1548; &#1606;&#1608;&#1589;&#1604; &#1573;&#1604;&#1609; &#1589;&#1581;&#1575;&#1585; &#1582;&#1604;&#1575;&#1604; 48 &#1587;&#1575;&#1593;&#1577;. &#1603;&#1605; &#1603;&#1585;&#1578;&#1608;&#1606; &#1578;&#1581;&#1578;&#1575;&#1580;&#1567;<time>21:47</time></div>
              <div class="msg them">Around 40 cartons. Do you deliver to Sohar too?<time>21:48</time></div>
              <div class="msg us">Yes &mdash; Sohar is a next-day route. For 40 cartons you are in the bulk tier, so I can send you the wholesale sheet now.<time>21:48</time></div>
              <div class="msg us">Can I take a name and a company so Nahid can confirm stock in the morning?<time>21:48</time></div>
              <div class="typing" aria-label="The buyer is typing"><i></i><i></i><i></i></div>
            </div>
          </div>
        </div>
        <p class="lede" style="text-align:center;font-size:.9rem;margin:18px auto 0;max-width:34ch">Illustration of the buyer agent. Your catalogue, your terms, your tone.</p>
      </div>
    </div>
  </div>
</section>

<!-- ===================================================== 02 - THE DASHBOARD -->
<section class="s-panel" id="dashboard">
  <div class="wrap">
    <div class="sysblock flip">
      <div>
        <span class="kicker">02 &#183; The add-on</span>
        <h3>The Live Owner Dashboard</h3>
        <p>Once buyers are arriving, the next question is whether you know your own position when one of
          them calls. This answers it without you phoning three people first.</p>
        <ul class="deliver">
          <li>Cash position, margin and stock on one screen</li>
          <li>Dead stock and losing lines, named</li>
          <li>What to do about each one, in a plain sentence</li>
          <li>Reads the systems you already use</li>
        </ul>
        <div class="pricetag"><b>+OMR 650</b><span>One-time &#183; added to the Smart Website</span></div>
        <div class="btn-row">
          <a class="btn btn-teal" href="/en/demos/#dash">Open the live demo</a>
          <a class="tlink" href="#price">See it in the price list <span class="arw">&rarr;</span></a>
        </div>
      </div>
      <div class="art rv">
        <div class="dash">
          <div class="dhead"><b>Executive summary</b><span>Live &#183; synced</span></div>
          <div class="kpis">
            <div class="kpi"><span>Revenue MTD</span><b>OMR 109K</b><i>&uarr; 12%</i></div>
            <div class="kpi"><span>Gross profit</span><b>OMR 41.9K</b><i>38.4% margin</i></div>
            <div class="kpi"><span>Below floor</span><b>16 / 47</b><i class="dn">urgent</i></div>
          </div>
          <div class="alertrow"><em>Critical &mdash; act today</em><p>Heavy equipment is dragging total margin down by 4.2 points. Freight is the cause.</p></div>
          <div class="alertrow"><em>Opportunity &mdash; this week</em><p>OMR 6,900 of cash is sitting in 4 dead-stock SKUs, costing OMR 350/month in warehouse fees.</p></div>
          <div class="alertrow ok"><em>Good news &mdash; double down</em><p>Shaker bottles and resistance bands are your highest-margin lines, and stock is running low.</p></div>
        </div>
        <p class="lede" style="text-align:center;font-size:.9rem;margin:18px auto 0;max-width:34ch">Demo figures. The live version reads your own numbers.</p>
      </div>
    </div>
  </div>
</section>

<!-- ===================================================== 03 - THE AUTOPILOT -->
<section class="s-dark" id="autopilot">
  <div class="wrap">
    <div class="sysblock">
      <div>
        <span class="kicker">03 &#183; The add-on</span>
        <h3>The Full Autopilot</h3>
        <p>Quotes and invoices do not chase themselves, and nobody in a busy office remembers all of them.
          This does, on a schedule, in your name.</p>
        <ul class="deliver">
          <li>Quote follow-up, spaced and polite</li>
          <li>Invoice reminders before and after the due date</li>
          <li>Stops the moment the buyer replies or pays</li>
          <li>Every message logged where you can read it</li>
        </ul>
        <div class="pricetag"><b>+OMR 900</b><span>One-time &#183; added to the Smart Website</span></div>
        <a class="btn btn-ghost" href="#price">See it in the price list</a>
      </div>
      <div class="art rv">
        <svg class="rail-svg drawn" viewBox="0 0 460 300" role="img" aria-labelledby="railT railD">
          <title id="railT">The follow-up schedule</title>
          <desc id="railD">A quote is sent on day zero. A first nudge goes on day two, a second on day five,
            and an invoice reminder on day nine. The sequence stops as soon as the buyer replies or pays.</desc>
          <line x1="34" y1="30" x2="34" y2="262" stroke="#1E5344" stroke-width="2"/>
          <g font-family="IBM Plex Mono, monospace" font-size="13" fill="#E8C98F">
            <circle cx="34" cy="34" r="7" fill="#D89234" stroke="none"/>
            <text x="58" y="30">DAY 0</text>
            <text x="58" y="50" font-family="IBM Plex Sans, sans-serif" font-size="15" fill="#F1EFE8">Quote sent</text>
            <circle cx="34" cy="110" r="7" fill="#0F6E56" stroke="none"/>
            <text x="58" y="106">DAY 2</text>
            <text x="58" y="126" font-family="IBM Plex Sans, sans-serif" font-size="15" fill="#F1EFE8">&#8220;Did that price work for you?&#8221;</text>
            <circle cx="34" cy="186" r="7" fill="#0F6E56" stroke="none"/>
            <text x="58" y="182">DAY 5</text>
            <text x="58" y="202" font-family="IBM Plex Sans, sans-serif" font-size="15" fill="#F1EFE8">&#8220;Shall I hold the stock?&#8221;</text>
            <circle cx="34" cy="258" r="7" fill="#1FAF5E" stroke="none"/>
            <text x="58" y="254">DAY 9</text>
            <text x="58" y="274" font-family="IBM Plex Sans, sans-serif" font-size="15" fill="#F1EFE8">Invoice reminder</text>
          </g>
        </svg>
        <p class="lede" style="text-align:center;font-size:.9rem;margin:14px auto 0;max-width:36ch">One reply from the buyer and the whole sequence stops.</p>
      </div>
    </div>
  </div>
</section>

<!-- =============================================== 04 - THE VISIBILITY DESK -->
<section class="s-panel2 grain" id="visibility">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> 04 &#183; The monthly one</p>
    <h2 class="h2">A website makes you findable.<br>Being <em>found</em> is a different job.</h2>
    <p class="lede">Everything above is built once and then it is yours. This one is not, and I would
      rather explain why in plain words now than have you feel surprised by an invoice later.</p>

    <div class="vis-defs rv">
      <div class="vis-def">
        <h3>SEO &mdash; how Google decides who to show</h3>
        <p>Picture a library with ten million books and one librarian. Somebody walks in and asks for
          &#8220;the best water pump supplier in Muscat.&#8221; She does not read ten million books. She
          reaches for the few she already knows, already trusts, and has watched people come back to
          happy. <b>SEO is the work of becoming a book she reaches for.</b></p>
      </div>
      <div class="vis-def">
        <h3>GEO &mdash; the same thing, for the AI</h3>
        <p>Your buyer now asks ChatGPT &#8220;who should I buy from in Oman?&#8221; ChatGPT does not go
          and read the internet on the spot &mdash; it answers out of what it has already read and
          already trusts. <b>GEO is the work of being inside what it read</b>, so your name is in the
          answer itself, not on page four of something nobody opens.</p>
      </div>
    </div>

    <div class="vis-why rv">
      <h3 class="h3">Why this one repeats every month</h3>
      <p>Your competitors do not stop. Google changes its mind about who it trusts almost daily. And the
        AI models are retrained and re-read the web on their own schedule &mdash; every time they do, the
        answer to &#8220;who should I buy from in Oman?&#8221; is written again from nothing. What it said
        about you last year counts for nothing this year.</p>
      <p><b>So being found is not a wall you build once. It is a garden.</b> Stop watering it and it does
        not stay the way you left it. It goes back to weeds &mdash; because the man next door kept
        watering his.</p>
      <p>That is the entire reason this is a monthly fee and not a one-time one. You are not buying an
        object that gets delivered and then sits there working. <b>You are paying for somebody to keep
        showing up.</b> The month the work stops is the month you start slipping back down the list, and
        climbing back is slower and dearer than staying put. If that is not worth OMR 300 a month to you,
        do not buy it &mdash; nothing else on this page needs it to work.</p>
    </div>

    <div class="vis-split">
      <div>
        <h3 class="h3">What your build already gives you, free, for ever</h3>
        <ul class="deliver">
          <li>A structure Google can read cleanly, on a site that loads fast</li>
          <li>Markup that tells an AI what your business is and what it sells</li>
          <li>Arabic and English done properly, not run through a translator</li>
          <li>A content structure built to be quoted by an answer engine</li>
        </ul>
        <p>That part is real, it is done, and you keep it whether you ever pay me another rial or not.
          <b>But infrastructure is a road, not a car driving down it.</b> The road is finished the day I
          hand it over. Somebody still has to drive it &mdash; and not once. Every week.</p>
      </div>
      <div>
        <h3 class="h3">What the Visibility Desk does, every month</h3>
        <ul class="deliver">
          <li>Watches what your buyers actually type and ask</li>
          <li>Writes the answers they are searching for</li>
          <li>Gets your name onto the pages, directories and sources the models read</li>
          <li>Keeps your Google Business Profile alive and correct</li>
          <li>Fixes what breaks before it costs you a position</li>
          <li>Tests whether ChatGPT, Gemini, Google&#8217;s AI answers and ordinary Google search name
            you &mdash; and sends you the screenshots either way, good month or bad</li>
        </ul>
      </div>
    </div>

    <div class="vis-gtee rv">
      {SHIELD}
      <div>
        <h3 class="h3">The {{GMONTHS}}-month guarantee</h3>
        <p>{{GMONTHS}} months after the work starts &mdash; that is the day your site goes live if I am
          building it, or the day we begin if your site is already up &mdash; if you are not visible,
          not named by Google and not named by ChatGPT, <b>I refund every rial you have paid for the
          Visibility Desk, and I carry on working, free, until you are.</b></p>
        <p class="fine">In plain terms: the refund covers this service&#8217;s fees, <b>not your
          build</b> &mdash; if you bought a website from me, that stays bought and is not touched by
          this. And &#8220;visible&#8221; is not left vague: in your first month we write down the
          actual buying questions your customers ask, and those are what we test against, every
          month, in front of you. You can still cancel any month &mdash; the guarantee simply needs
          its {{GMONTHS}} months to run.</p>
      </div>
    </div>

    <div class="vis-foot">
      <div class="pricetag"><b>OMR 300</b><span>Per month &#183; cancel any month &#183; {{GMONTHS}}-month guarantee</span></div>
      <div class="btn-row">
        <a class="btn btn-wa" href="{WA}&amp;text=Hello%20Nahid%2C%20I%20want%20to%20ask%20about%20the%20Visibility%20Desk%20at%20OMR%20300%20a%20month.">{WA_ICON}Ask about the Visibility Desk</a>
        <a class="tlink" href="#price">See it in the price list <span class="arw">&rarr;</span></a>
      </div>
    </div>
  </div>
</section>
"""

    p2 = f"""
<!-- ================================================== THE WHOLE PRICE LIST -->
<section class="s-white" id="price">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> The whole price list</p>
    <h2 class="h2">Every number, on the page, before you talk to me.</h2>
    <p class="lede">One price per rung, all of it below. No tiers to decode, and nothing that only
      appears once you are on a call.</p>

    <div class="tablewrap rv" style="margin-top:clamp(26px,3.5vw,44px)">
      <table class="t">
        <caption>Every rung, and what each one adds</caption>
        <thead>
          <tr><th scope="col">What you get</th><th scope="col" class="n">Price</th><th scope="col">Billing</th></tr>
        </thead>
        <tbody>
          <tr>
            <td><b>Silent Buyer Test</b><span class="mini">I message your business as a buyer would, and send you the scorecard</span></td>
            <td class="n">Free</td><td>&mdash;</td>
          </tr>
          <tr class="hi">
            <td><b>The Smart Website</b><span class="mini">Bilingual site, AI buyer agent, wholesale quote flow, WhatsApp handoff, AI-search visibility, 1 year hosting &amp; care</span></td>
            <td class="n">OMR 950</td><td>One-time</td>
          </tr>
          <tr>
            <td>+ The Live Owner Dashboard<span class="mini">Cash, stock and open-lead dashboard</span></td>
            <td class="n">+OMR 650</td><td>One-time</td>
          </tr>
          <tr>
            <td>+ The Full Autopilot<span class="mini">Quote and invoice follow-up, on schedule</span></td>
            <td class="n">+OMR 900</td><td>One-time</td>
          </tr>
          <tr>
            <td><b>The Operator Stack</b><span class="mini">All three together</span></td>
            <td class="n">OMR 2,200</td><td>One-time</td>
          </tr>
          <tr>
            <td>The Growth Desk<span class="mini">Optional monthly care, new features, reporting review. Never required to keep anything working.</span></td>
            <td class="n">OMR 75/mo</td><td>Opt-in, cancel anytime</td>
          </tr>
          <tr>
            <td>The Visibility Desk<span class="mini">The ongoing SEO and GEO work &mdash; staying named by Google and by the AI assistants buyers ask first. Carries a {{GMONTHS}}-month refund guarantee. <a href="#visibility">What that means, in plain words</a>.</span></td>
            <td class="n">OMR 300/mo</td><td>Opt-in, cancel any month</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</section>

<!-- ==================================================== THREE WAYS TO PAY -->
<section class="s-cream grain">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> Three ways to pay for it</p>
    <h2 class="h2">Same build. Pick whichever one you are comfortable with.</h2>

    <div class="pay-grid" style="margin-top:clamp(26px,3.5vw,44px)" data-stagger>
      <div class="pay hero-pay">
        <span class="badge">Most owners start here</span>
        <h3>Pay on Proof</h3>
        <span class="price">OMR 1,150</span>
        <p>Nothing today. Nothing when it goes live. I invoice you only after your smart website has produced its
          first real, verifiable buyer inquiry. If it never does, you never pay.</p>
        <div class="btn-row"><a class="btn btn-amber" href="/en/checkout/?plan=proof">Start this order</a><a class="btn btn-ghost" href="{WA}&text=Hello%20Nahid%2C%20I%20want%20the%20Smart%20Website%20on%20Pay%20on%20Proof%20terms.">{WA_ICON}Ask first</a></div>
      </div>
      <div class="pay">
        <span class="badge">Cheapest</span>
        <h3>Pay on Start</h3>
        <span class="price">OMR 950</span>
        <p>Paid up front {{PAY_HOW}}. Saves you OMR 200 against Pay on Proof, and includes the Arabic
          content pass, the Google Business Profile fix, and one staff training session at no charge.</p>
        <div class="btn-row"><a class="btn btn-ghost" href="/en/checkout/?plan=full">Start this order</a><a class="btn btn-ghost" href="{WA}&text=Hello%20Nahid%2C%20I%20want%20the%20Smart%20Website%20paid%20up%20front%20at%20OMR%20950.">{WA_ICON}Ask first</a></div>
      </div>
      <div class="pay">
        <span class="badge">Spread it out</span>
        <h3>Three payments</h3>
        <span class="price">3 &times; OMR 340</span>
        <p>On signing, on go-live, and thirty days later. Less than one month of an administrator&#8217;s salary
          in total &mdash; and it keeps working after the three months are done.</p>
        <div class="btn-row"><a class="btn btn-ghost" href="/en/checkout/?plan=three">Start this order</a><a class="btn btn-ghost" href="{WA}&text=Hello%20Nahid%2C%20I%20want%20the%20Smart%20Website%20on%20the%20three-payment%20plan.">{WA_ICON}Ask first</a></div>
      </div>
    </div>

    <p class="lede" style="margin:clamp(20px,2.6vw,30px) auto 0;max-width:66ch">
      Not ready to commit the whole figure today? <a href="/en/checkout/">Reserve a build slot for
      {{DEPOSIT}}</a> instead &mdash; it holds your place in the queue, comes off your price in full, and is
      refundable until the day building starts.
    </p>

    <!-- The exclusions sit immediately beside the price. That placement is the
         point: it is where honesty does the most work. -->
    <div class="nolog rv" style="margin-top:clamp(34px,4.5vw,60px)">
      <h3 class="h3">What&#8217;s not included &mdash; before any money changes hands</h3>
      <ul>
        <li>This is <b>not an ERP</b>. If you need multi-branch inventory and finance in one system, that is a
          different weight class and I will say so on the call.</li>
        <li>It <b>does not replace your accountant</b>. It shows you what is happening now; they still close your books.</li>
        <li>No paid ad management and no ongoing social media. A build also carries no ongoing content
          writing beyond your initial site copy &mdash; that is <a href="#visibility">the Visibility
          Desk</a>, priced separately above, and nothing here needs it to work.</li>
        <li>No online payment processing or e-commerce checkout. If you need it, it gets scoped and quoted separately.</li>
        <li>Prices above assume one product catalogue and one language pair. Something genuinely bigger gets
          quoted, not squeezed into a package.</li>
      </ul>
    </div>
  </div>
</section>

<!-- ================================================================ CTA -->
<section class="s-dark pad-s">
  <div class="wrap">
    <div style="display:flex;gap:clamp(20px,4vw,50px);align-items:center;justify-content:space-between;flex-wrap:wrap">
      <div style="flex:1 1 380px">
        <h2 class="h2" style="margin-bottom:12px">Not sure which one you need?</h2>
        <p class="lede" style="margin:0">Then start with the free one. I&#8217;ll message your business as a buyer would
          and send you the scorecard &mdash; no obligation, and you keep it either way.</p>
      </div>
      <div class="btn-row">
        <a class="btn btn-amber" href="/en/contact/#test">Get the Silent Buyer Test</a>
        <a class="btn btn-ghost" href="/en/checkout/">Or start an order</a>
        <a class="btn btn-ghost" href="/en/process/">See how a build runs</a>
      </div>
    </div>
  </div>
</section>

</main>
"""
    # PAY_HOW follows tools/v4/pay.py: the page must not offer a card until
    # one can actually be taken. DEPOSIT comes from the same table as the
    # checkout, so the two can never quote different deposits.
    pay_how = "by card or bank transfer" if pay.PAY_LIVE else "by bank transfer"
    # The guarantee length is read from the catalog rather than typed, because
    # the same promise is made on the checkout interstitial from the same
    # field. Two hand-written copies of "6 months" is how a guarantee ends up
    # meaning two different lengths on two pages.
    gmonths = str(pay.item(pay.UPSELL_ID)["guarantee_months"])
    return ((p1 + p2).replace("{PAY_HOW}", pay_how)
            .replace("{DEPOSIT}", pay.money(pay.DEPOSIT))
            .replace("{GMONTHS}", gmonths))


META = dict(
    slug="services",
    title="What I build | AI Profit Lab — three systems, SEO/GEO, prices published",
    desc=("The Smart Website, the Live Owner Dashboard, the Full Autopilot and the monthly "
          "Visibility Desk (SEO and GEO) - what each one does, what it costs in OMR, and what is "
          "deliberately not included."),
    nav="/en/services/",
    next=("Next", "How it works", "/en/process/"),
    schema="""{
  "@context":"https://schema.org",
  "@type":"ItemList",
  "name":"Systems built by AI Profit Lab",
  "itemListElement":[
    {"@type":"Service","position":1,"name":"The Smart Website","description":"A bilingual site with an AI buyer agent that answers in Arabic and English and hands live buyers to WhatsApp.","provider":{"@id":"https://aiprofitlab.io/#organization"},"areaServed":"Oman","offers":{"@type":"Offer","price":"950","priceCurrency":"OMR","availability":"https://schema.org/InStock","url":"https://aiprofitlab.io/en/checkout/?plan=website","priceValidUntil":"2026-12-31"}},
    {"@type":"Service","position":2,"name":"The Live Owner Dashboard","description":"Cash position, margin, stock and open leads on one screen, with a recommended action for each.","provider":{"@id":"https://aiprofitlab.io/#organization"},"areaServed":"Oman","offers":{"@type":"Offer","price":"650","priceCurrency":"OMR","availability":"https://schema.org/InStock","url":"https://aiprofitlab.io/en/checkout/?plan=dashboard","priceValidUntil":"2026-12-31"}},
    {"@type":"Service","position":3,"name":"The Full Autopilot","description":"Quote and invoice follow-up on a schedule, stopping as soon as the buyer replies or pays.","provider":{"@id":"https://aiprofitlab.io/#organization"},"areaServed":"Oman","offers":{"@type":"Offer","price":"900","priceCurrency":"OMR","availability":"https://schema.org/InStock","url":"https://aiprofitlab.io/en/checkout/?plan=autopilot","priceValidUntil":"2026-12-31"}},
    {"@type":"Service","position":4,"name":"The Visibility Desk","serviceType":"Search engine and AI answer-engine visibility (SEO and GEO)","description":"Ongoing monthly SEO and GEO work: staying named by Google and by the AI assistants buyers ask first, with a monthly test showing whether ChatGPT, Gemini, Google AI answers and Google search name the business.","provider":{"@id":"https://aiprofitlab.io/#organization"},"areaServed":"Oman","offers":{"@type":"Offer","priceCurrency":"OMR","availability":"https://schema.org/InStock","url":"https://aiprofitlab.io/en/services/#visibility","priceValidUntil":"2026-12-31","priceSpecification":{"@type":"UnitPriceSpecification","price":"300","priceCurrency":"OMR","unitCode":"MON","unitText":"month"}}}
  ]
}""",
)
