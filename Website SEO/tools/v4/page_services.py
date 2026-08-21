#!/usr/bin/env python3
"""Services / What I build.

Every system gets a *picture of itself* rather than a paragraph describing
itself: a phone thread, a dashboard, a follow-up schedule. Prices are published
in full - the whole ladder, founding and standard side by side - because the
page's argument is that you should not need a sales call to learn a number.
Figures are the ones already published on en/index-v3.html.
"""
import pay
from kit import WA, WA_ICON, STAR

CSS = """
/* ---------------------------------------------------------- stat strip */
.stats{display:grid;grid-template-columns:repeat(4,1fr);border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.stats div{padding:clamp(22px,3vw,34px) clamp(14px,2vw,26px);border-right:1px solid var(--line)}
.stats div:last-child{border-right:0}
.stats b{display:block;font-family:var(--display);font-size:clamp(1.9rem,3.6vw,2.9rem);line-height:1;color:var(--teal-950);margin-bottom:8px;font-weight:400}
.stats span{font-family:var(--mono);font-size:.78rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);line-height:1.6;display:block}

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

/* --------------------------------------------------------- order grid */
.ord{display:grid;grid-template-columns:repeat(3,1fr);gap:clamp(14px,1.8vw,22px)}
.ord div{background:var(--white);border:1px solid var(--line);border-radius:14px;padding:22px 24px;transition:border-color .3s,transform .3s var(--ease)}
.ord div:hover{border-color:var(--amber-pale);transform:translateY(-3px)}
.ord h4{font-family:var(--display);font-size:1.2rem;color:var(--teal-950);margin:0 0 7px;font-weight:400}
.ord p{margin:0;font-size:.94rem;color:var(--muted)}

@media (max-width:900px){
  .stats{grid-template-columns:repeat(2,1fr)}
  .stats div:nth-child(2){border-right:0}
  .stats div:nth-child(1),.stats div:nth-child(2){border-bottom:1px solid var(--line)}
  .sysblock{grid-template-columns:1fr}
  .sysblock.flip .art{order:0}
  .pay-grid,.ord{grid-template-columns:1fr}
}
"""


def body():
    p1 = f"""<main id="main">

<header class="phero s-cream grain">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> What I build</p>
    <h1 class="h1">You describe the problem.<br>I build the system that removes it.</h1>
    <p class="lede">Three systems, each one a fixed, one-time build. No retainer is required to keep any of
      them running, and every price is on this page.</p>
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
        <div class="pricetag"><b>OMR 950</b><span>One-time &#183; founding price</span></div>
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
"""

    p2 = f"""
<!-- ================================================== THE WHOLE PRICE LIST -->
<section class="s-white" id="price">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> The whole price list</p>
    <h2 class="h2">Every number, on the page, before you talk to me.</h2>
    <p class="lede">Founding Partner pricing applies to the first capped group only. The standard column is
      what gets published once that group closes.</p>

    <div class="tablewrap rv" style="margin-top:clamp(26px,3.5vw,44px)">
      <table class="t">
        <caption>Every rung, and what each one adds</caption>
        <thead>
          <tr><th scope="col">What you get</th><th scope="col" class="n">Founding Partner</th><th scope="col" class="n">Standard</th><th scope="col">Billing</th></tr>
        </thead>
        <tbody>
          <tr>
            <td><b>Silent Buyer Test</b><span class="mini">I message your business as a buyer would, and send you the scorecard</span></td>
            <td class="n">Free</td><td class="n">Free</td><td>&mdash;</td>
          </tr>
          <tr class="hi">
            <td><b>The Smart Website</b><span class="mini">Bilingual site, AI buyer agent, wholesale quote flow, WhatsApp handoff, AI-search visibility, 1 year hosting &amp; care</span></td>
            <td class="n">OMR 950</td><td class="n">OMR 1,450</td><td>One-time</td>
          </tr>
          <tr>
            <td>+ The Live Owner Dashboard<span class="mini">Cash, stock and open-lead dashboard</span></td>
            <td class="n">+OMR 650</td><td class="n">+OMR 950</td><td>One-time</td>
          </tr>
          <tr>
            <td>+ The Full Autopilot<span class="mini">Quote and invoice follow-up, on schedule</span></td>
            <td class="n">+OMR 900</td><td class="n">+OMR 1,300</td><td>One-time</td>
          </tr>
          <tr>
            <td><b>The Operator Stack</b><span class="mini">All three together</span></td>
            <td class="n">OMR 2,200</td><td class="n">OMR 3,400</td><td>One-time</td>
          </tr>
          <tr>
            <td>The Growth Desk<span class="mini">Optional monthly care, new features, reporting review. Never required to keep anything working.</span></td>
            <td class="n">OMR 75/mo</td><td class="n">OMR 95/mo</td><td>Opt-in, cancel anytime</td>
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
        <li>No paid ad management, no ongoing social media, no ongoing content writing beyond your initial site copy.</li>
        <li>No online payment processing or e-commerce checkout. If you need it, it gets scoped and quoted separately.</li>
        <li>Prices above assume one product catalogue and one language pair. Something genuinely bigger gets
          quoted, not squeezed into a package.</li>
      </ul>
    </div>
  </div>
</section>

<!-- ======================================================= BUILT TO ORDER -->
<section class="s-panel">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> Built to order</p>
    <h2 class="h2">And the things that only your business needs.</h2>
    <p class="lede">Scoped and quoted one at a time, usually on top of a system that already exists.</p>

    <div class="ord" style="margin-top:clamp(26px,3.5vw,42px)" data-stagger>
      <div><h4>Arabic content pass</h4><p>Your existing pages rewritten so an Arabic-first buyer takes you seriously.</p></div>
      <div><h4>Google Business Profile</h4><p>Fixed, verified, and pinned to the right place on the map.</p></div>
      <div><h4>Quote-sheet automation</h4><p>Bulk pricing assembled and sent without rebuilding it each time.</p></div>
      <div><h4>Supplier &amp; stock alerts</h4><p>Told before you run out, not after a buyer asks.</p></div>
      <div><h4>Staff training</h4><p>Two hours, in your office, so the team actually uses what was built.</p></div>
      <div><h4>Something else entirely</h4><p>Describe the bottleneck. If I can&#8217;t build it, I will say so.</p></div>
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
    return (p1 + p2).replace("{PAY_HOW}", pay_how).replace("{DEPOSIT}", pay.money(pay.DEPOSIT))


META = dict(
    slug="services",
    title="What I build | AI Profit Lab — three systems, every price published",
    desc=("The Smart Website, the Live Owner Dashboard and the Full Autopilot - what each one does, "
          "what it costs in OMR, and what is deliberately not included."),
    nav="/en/services/",
    next=("Next", "How it works", "/en/process/"),
    schema="""{
  "@context":"https://schema.org",
  "@type":"ItemList",
  "name":"Systems built by AI Profit Lab",
  "itemListElement":[
    {"@type":"Service","position":1,"name":"The Smart Website","description":"A bilingual site with an AI buyer agent that answers in Arabic and English and hands live buyers to WhatsApp.","provider":{"@type":"Organization","name":"AI Profit Lab"},"areaServed":"Oman","offers":{"@type":"Offer","price":"950","priceCurrency":"OMR"}},
    {"@type":"Service","position":2,"name":"The Live Owner Dashboard","description":"Cash position, margin, stock and open leads on one screen, with a recommended action for each.","provider":{"@type":"Organization","name":"AI Profit Lab"},"areaServed":"Oman","offers":{"@type":"Offer","price":"650","priceCurrency":"OMR"}},
    {"@type":"Service","position":3,"name":"The Full Autopilot","description":"Quote and invoice follow-up on a schedule, stopping as soon as the buyer replies or pays.","provider":{"@type":"Organization","name":"AI Profit Lab"},"areaServed":"Oman","offers":{"@type":"Offer","price":"900","priceCurrency":"OMR"}}
  ]
}""",
)
