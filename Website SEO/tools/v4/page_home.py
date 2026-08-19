#!/usr/bin/env python3
"""Homepage body: hero (ported) + six visual sections + an explore rail.

Editorial brief from Nahid: the page must make a visitor want to open other
pages and stay. So every block below is a *thing to look at or touch* with a
door out of it - a slider, a staircase, a clickable demo, an hours grid - and
almost no block runs longer than four lines of prose.
"""
from kit import WA, WA_ICON, STAR

CSS = """
/* ------------------------------------------------------- cost calculator */
.leak-grid{display:grid;grid-template-columns:.85fr 1.15fr;gap:clamp(20px,3vw,40px);align-items:start}
.panelcard{
  background:rgba(241,239,232,.05);border:1px solid var(--line-dark);
  border-radius:16px;padding:clamp(24px,3vw,36px);
}
.panelcard h3{color:var(--cream);margin:0 0 22px;font-size:1.5rem}
/* the evening, as a timeline */
.tl{list-style:none;margin:0;padding:0}
.tl li{position:relative;padding:0 0 22px 26px;border-left:1px solid var(--line-dark)}
.tl li:last-child{padding-bottom:0;border-left-color:transparent}
.tl li::before{
  content:"";position:absolute;left:-4.5px;top:8px;width:8px;height:8px;border-radius:50%;
  background:var(--amber-pale);
}
.tl li.bad::before{background:var(--alert);box-shadow:0 0 0 4px rgba(166,67,31,.18)}
.tl .t{display:block;font-family:var(--mono);font-size:.78rem;letter-spacing:.12em;color:var(--amber-pale);margin-bottom:5px}
.tl .d{display:block;color:rgba(241,239,232,.8);font-size:.98rem;line-height:1.55}
.tl .d b{color:var(--cream)}

.fieldrow{margin-bottom:20px}
.fieldrow label{
  display:flex;justify-content:space-between;align-items:baseline;gap:12px;
  font-size:.95rem;color:rgba(241,239,232,.8);margin-bottom:9px;
}
.fieldrow output{font-family:var(--mono);color:var(--amber-bright);font-size:1rem;white-space:nowrap}
input[type=range]{
  -webkit-appearance:none;appearance:none;width:100%;height:4px;border-radius:99px;
  background:rgba(241,239,232,.16);outline:none;cursor:pointer;
}
input[type=range]::-webkit-slider-thumb{
  -webkit-appearance:none;width:22px;height:22px;border-radius:50%;background:var(--amber-bright);
  border:3px solid var(--teal-950);cursor:grab;transition:transform .15s var(--ease);
}
input[type=range]::-webkit-slider-thumb:hover{transform:scale(1.15)}
input[type=range]::-moz-range-thumb{
  width:18px;height:18px;border-radius:50%;background:var(--amber-bright);
  border:3px solid var(--teal-950);cursor:grab;
}
.bignum-cap{
  display:block;font-family:var(--mono);font-size:.8rem;letter-spacing:.14em;text-transform:uppercase;
  color:rgba(241,239,232,.55);margin:30px 0 4px;
}
.bignum{
  display:block;font-family:var(--display);font-size:clamp(2.6rem,6vw,4.2rem);line-height:1;
  color:var(--amber-bright);font-variant-numeric:tabular-nums;
}
.payback{margin:18px 0 0;color:rgba(241,239,232,.82);font-size:1.02rem}
.payback b{color:var(--cream)}
.assume{margin:14px 0 0;font-size:.88rem;line-height:1.6;color:rgba(241,239,232,.5)}

/* ------------------------------------------------------------- staircase */
.stair{width:100%;height:auto;display:block;margin:clamp(24px,4vw,44px) 0 clamp(28px,4vw,52px);overflow:visible}
.stair .step{opacity:0;transform:translateY(26px);transition:opacity .7s var(--ease),transform .8s var(--ease);transition-delay:var(--d,0s)}
.stair.vis .step{opacity:1;transform:none}
.stair .anno{opacity:0;transition:opacity .6s var(--ease);transition-delay:var(--d,0s)}
.stair.vis .anno{opacity:1}
html:not(.js) .stair .step,html:not(.js) .stair .anno{opacity:1;transform:none}

.sys-card{display:flex;flex-direction:column;gap:14px}
.sys-card .tag{
  font-family:var(--mono);font-size:.85rem;letter-spacing:.06em;color:var(--teal-900);
  background:var(--white);border:1px solid var(--line);border-radius:99px;padding:7px 14px;align-self:flex-start;
}
.sys-card .tag b{color:var(--amber-text)}
.sys-card .tlink{margin-top:auto}

/* ----------------------------------------------------------- proof tiles */
.tiles{display:grid;grid-template-columns:repeat(2,1fr);gap:clamp(16px,2.2vw,26px)}
.tile{
  position:relative;display:block;text-decoration:none;border-radius:16px;overflow:hidden;
  border:1px solid var(--line-dark);background:rgba(241,239,232,.04);
  transition:transform .4s var(--ease),border-color .4s,box-shadow .4s;
}
.tile:hover{transform:translateY(-5px);border-color:var(--amber-bright);box-shadow:0 34px 60px -40px rgba(0,0,0,.85)}
.tile .shot{aspect-ratio:16/10;overflow:hidden;background:var(--teal-900)}
.tile .shot img{width:100%;height:100%;object-fit:cover;object-position:top center;transition:transform .8s var(--ease)}
.tile:hover .shot img{transform:scale(1.045)}
.tile .cap{padding:22px clamp(18px,2vw,26px) 24px}
.tile .cap h3{color:var(--cream);font-size:1.3rem;margin:0 0 7px}
.tile .cap p{color:rgba(241,239,232,.66);font-size:.96rem;margin:0 0 14px}
.tile .live{
  position:absolute;top:14px;left:14px;z-index:2;display:inline-flex;align-items:center;gap:7px;
  font-family:var(--mono);font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;
  background:rgba(7,43,34,.82);color:var(--cream);border:1px solid var(--line-dark);
  padding:6px 11px;border-radius:99px;backdrop-filter:blur(6px);
}
.tile .live i{width:7px;height:7px;border-radius:50%;background:var(--wa);animation:pulse 2.2s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.45;transform:scale(.8)}}
.tile-wide{grid-column:1/-1;display:grid;grid-template-columns:1fr auto;align-items:center;gap:24px;padding:clamp(24px,3vw,36px)}
.tile-wide h3{margin:0 0 8px}
.tile-wide .cap{padding:0}

/* --------------------------------------------------------- hours grid */
.hours-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:clamp(18px,3vw,34px)}
.hcard{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:clamp(22px,3vw,32px)}
.hcard.win{background:var(--teal-950);border-color:var(--teal-900);color:var(--cream)}
.hcard h3{margin:0 0 4px;font-size:1.4rem}
.hcard.win h3{color:var(--cream)}
.hcard .sub{font-family:var(--mono);font-size:.82rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin:0 0 22px}
.hcard.win .sub{color:var(--amber-pale)}
/* 24 columns x 7 rows: one row per day, one cell per hour. Transposed from
   7x24 because 24 narrow columns keep the cells small enough to read as a
   texture; at 7 columns each cell was ~40px and the block ran a metre tall. */
.hgrid{display:grid;grid-template-columns:repeat(24,1fr);gap:2px;margin-bottom:20px}
.hgrid i{aspect-ratio:1;border-radius:1px;background:var(--panel-2);display:block}
.hcard.win .hgrid i{background:rgba(241,239,232,.12)}
.hgrid i.on{background:var(--alert)}
.hcard.win .hgrid i.on{background:var(--wa)}
.hcount{font-family:var(--display);font-size:clamp(1.9rem,4vw,2.7rem);line-height:1;color:var(--teal-950);display:block;margin-bottom:6px}
.hcard.win .hcount{color:var(--amber-bright)}
.hcard .note{font-size:.95rem;color:var(--muted);margin:0}
.hcard.win .note{color:rgba(241,239,232,.72)}
.hlegend{font-family:var(--mono);font-size:.74rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin:0 0 8px}
.hcard.win .hlegend{color:rgba(241,239,232,.55)}

/* -------------------------------------------------------------- promise */
.promise-grid{display:grid;grid-template-columns:auto 1fr;gap:clamp(24px,4vw,52px);align-items:center}
.promise-photo{
  width:clamp(150px,17vw,220px);aspect-ratio:1;border-radius:50%;object-fit:cover;
  border:1px solid var(--line-dark);filter:saturate(.92);
}
.promise q{
  display:block;font-family:var(--display);font-size:clamp(1.5rem,3.2vw,2.4rem);line-height:1.28;
  color:var(--cream);quotes:none;margin:0 0 22px;
}
.promise q::before,.promise q::after{content:""}
.promise .sig{font-family:var(--mono);font-size:.85rem;letter-spacing:.1em;text-transform:uppercase;color:var(--amber-pale);margin:0}

/* -------------------------------------------------------- explore rail */
.rail{display:grid;grid-template-columns:repeat(4,1fr);gap:clamp(14px,1.8vw,22px)}
.rcard{
  position:relative;display:flex;flex-direction:column;justify-content:space-between;gap:34px;
  min-height:230px;text-decoration:none;background:var(--panel);border:1px solid var(--line);
  border-radius:16px;padding:clamp(20px,2.4vw,28px);overflow:hidden;
  transition:background .35s,transform .35s var(--ease),border-color .35s;
}
.rcard::after{
  content:"";position:absolute;inset:auto -30% -60% -30%;height:70%;border-radius:50%;
  background:radial-gradient(closest-side,rgba(186,117,23,.16),transparent);
  opacity:0;transition:opacity .45s var(--ease);
}
.rcard:hover{transform:translateY(-5px);border-color:var(--amber-pale);background:var(--white)}
.rcard:hover::after{opacity:1}
.rcard .rn{font-family:var(--mono);font-size:.8rem;letter-spacing:.16em;color:var(--amber-text)}
.rcard h3{font-size:clamp(1.25rem,2vw,1.55rem);color:var(--teal-950);margin:0 0 8px;position:relative}
.rcard p{font-size:.94rem;color:var(--muted);margin:0;position:relative}
.rcard .go{position:relative;font-family:var(--mono);font-size:.8rem;letter-spacing:.12em;text-transform:uppercase;color:var(--teal);display:inline-flex;align-items:center;gap:8px}
.rcard:hover .go{color:var(--amber-text)}

@media (max-width:760px){ .stair{display:none} }
@media (max-width:960px){
  .leak-grid,.hours-grid,.tiles{grid-template-columns:1fr}
  .rail{grid-template-columns:repeat(2,1fr)}
  .promise-grid{grid-template-columns:1fr;text-align:left}
  .tile-wide{grid-template-columns:1fr}
}
@media (max-width:560px){ .rail{grid-template-columns:1fr} }
"""


def _hours_grid(on_test, win):
    """168 cells, one per hour of the week. Sunday first (Oman work week).

    `on_test(day, hour)` decides which cells are lit. The grid is decorative
    relative to the number stated beside it, so it carries aria-hidden and the
    count is written out in text.
    """
    cells = []
    for day in range(7):
        for hour in range(24):
            cells.append('<i class="on"></i>' if on_test(day, hour) else "<i></i>")
    return f'<div class="hgrid" aria-hidden="true">{"".join(cells)}</div>'


def body():
    from hero import HERO_HTML

    # Sun-Thu (cols 0-4), 08:00-15:59 -> exactly 40 of 168 hours, which is the
    # figure in brand/docs/03-money-model.md section 5.
    office = _hours_grid(lambda d, h: d <= 4 and 8 <= h <= 15, False)
    always = _hours_grid(lambda d, h: True, True)

    p1 = f"""<main id="main">

{HERO_HTML}

<div class="facts" aria-label="Key facts">
  <div class="track">
    <div class="half">
      <span><span class="star">{STAR}</span>One-time fee</span>
      <span><span class="star">{STAR}</span>No monthly lock-in</span>
      <span><span class="star">{STAR}</span>Priced in OMR</span>
      <span><span class="star">{STAR}</span>English + &#1575;&#1604;&#1593;&#1585;&#1576;&#1610;&#1577;</span>
      <span><span class="star">{STAR}</span>Built in Muscat</span>
      <span><span class="star">{STAR}</span>Live in about a week</span>
      <span><span class="star">{STAR}</span>You keep what I build</span>
    </div>
    <div class="half" aria-hidden="true">
      <span><span class="star">{STAR}</span>One-time fee</span>
      <span><span class="star">{STAR}</span>No monthly lock-in</span>
      <span><span class="star">{STAR}</span>Priced in OMR</span>
      <span><span class="star">{STAR}</span>English + &#1575;&#1604;&#1593;&#1585;&#1576;&#1610;&#1577;</span>
      <span><span class="star">{STAR}</span>Built in Muscat</span>
      <span><span class="star">{STAR}</span>Live in about a week</span>
      <span><span class="star">{STAR}</span>You keep what I build</span>
    </div>
  </div>
</div>

<!-- ============================================ S2 - THE LEAK, IN YOUR NUMBERS -->
<section class="s-dark" id="leak">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> The cost of silence</p>
    <h2 class="h2">Move four sliders. See your own number.</h2>
    <p class="lede">Nothing here is assumed. Every figure is one you set yourself.</p>

    <div class="leak-grid" style="margin-top:clamp(30px,4vw,52px)">
      <div class="panelcard rv">
        <h3>One buyer. One evening.</h3>
        <ol class="tl">
          <li class="bad"><span class="t">21:47 THU</span><span class="d">A buyer asks if you deliver to Sohar, and what the bulk price is.</span></li>
          <li class="bad"><span class="t">21:47 &rarr; 08:12</span><span class="d">Nothing. Your office closed at 5pm. The message sits <b>14 hours</b>.</span></li>
          <li class="bad"><span class="t">22:10 THU</span><span class="d">He messages two more suppliers. One replies in four minutes.</span></li>
          <li><span class="t">08:12 FRI</span><span class="d">You reply, politely, with a good price.</span></li>
          <li class="bad"><span class="t">08:14 FRI</span><span class="d">Silence. You never got to compete.</span></li>
        </ol>
      </div>

      <div class="panelcard rv" style="--d:.12s">
        <h3>What that costs you every month</h3>

        <div class="fieldrow">
          <label for="q1">Buyer inquiries you get in a week <output id="o1">25</output></label>
          <input type="range" id="q1" min="5" max="150" step="5" value="25">
        </div>
        <div class="fieldrow">
          <label for="q2">Share arriving outside working hours <output id="o2">40%</output></label>
          <input type="range" id="q2" min="5" max="80" step="5" value="40">
        </div>
        <div class="fieldrow">
          <label for="q3">Your average order value <output id="o3">OMR 180</output></label>
          <input type="range" id="q3" min="20" max="2000" step="20" value="180">
        </div>
        <div class="fieldrow">
          <label for="q4">Share of answered inquiries you win <output id="o4">20%</output></label>
          <input type="range" id="q4" min="5" max="60" step="5" value="20">
        </div>

        <span class="bignum-cap">Revenue walking away, per month</span>
        <span class="bignum" id="leak">OMR 1,559</span>

        <!-- Two bars, one scale: the monthly leak against the one-time cost of
             fixing it. The comparison is the whole argument. -->
        <svg id="bars" viewBox="0 0 420 132" role="img" style="width:100%;height:auto;margin-top:22px" aria-labelledby="barsTitle">
          <title id="barsTitle">Monthly revenue lost to silence, compared with the one-time cost of the Smart Storefront</title>
          <text x="0" y="14" fill="#A8BCB1" font-family="IBM Plex Mono, monospace" font-size="15">Lost each month</text>
          <rect x="0" y="22" width="420" height="26" rx="5" fill="rgba(241,239,232,.10)"/>
          <rect id="barLeak" x="0" y="22" width="420" height="26" rx="5" fill="#D89234"/>
          <text id="barLeakT" x="410" y="40" fill="#072B22" font-family="IBM Plex Mono, monospace" font-size="15" font-weight="500" text-anchor="end">OMR 1,559</text>
          <text x="0" y="82" fill="#A8BCB1" font-family="IBM Plex Mono, monospace" font-size="15">Smart Storefront, once</text>
          <rect x="0" y="90" width="420" height="26" rx="5" fill="rgba(241,239,232,.10)"/>
          <rect id="barCost" x="0" y="90" width="256" height="26" rx="5" fill="#1FAF5E"/>
          <text x="10" y="108" fill="#072B22" font-family="IBM Plex Mono, monospace" font-size="15" font-weight="500">OMR 950</text>
        </svg>

        <p class="payback">At that rate the build pays for itself in <b id="days">19 days</b>.</p>
        <p class="assume">After-hours inquiries per month &times; your win rate &times; your average order.
          It shows what is <em>at stake</em> in those messages &mdash; not a promise of recovery.</p>
      </div>
    </div>
  </div>
</section>
"""

    # ------------------------------------------------------------------
    # S3 - the ladder. The staircase is hidden below 760px, where a 1000-unit
    # viewBox would render its 26px labels at under 9 real pixels; the three
    # cards underneath carry the same content at any width.
    # ------------------------------------------------------------------
    p2 = f"""
<section class="s-cream grain" id="build">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> What gets built</p>
    <h2 class="h2">Three systems. Each one solves the problem the last one creates.</h2>
    <p class="lede">Start where the pain is. Nothing is a bundle you must buy at once, and nothing
      needs a monthly fee to keep working.</p>

    <svg class="stair rv" viewBox="0 0 1000 400" role="img" aria-labelledby="stairT stairD">
      <title id="stairT">The three systems as a staircase</title>
      <desc id="stairD">Step one, the Smart Storefront at OMR 950, makes buyers arrive. That creates the next
        question, answered by step two, the Live Owner Dashboard at plus OMR 650. That creates the next question,
        answered by step three, the Full Autopilot at plus OMR 900.</desc>

      <g class="step" style="--d:0s">
        <rect x="30" y="270" width="280" height="90" rx="12" fill="#0F6E56"/>
        <text x="54" y="308" fill="#F1EFE8" font-family="Marcellus, Georgia, serif" font-size="26">The Smart Storefront</text>
        <text x="54" y="336" fill="#BFE3D5" font-family="IBM Plex Mono, monospace" font-size="17">01 &#183; OMR 950</text>
      </g>

      <g class="anno" style="--d:.55s">
        <path d="M352 146 l-12 -7 v14 z" fill="#BA7517"/>
        <text x="374" y="151" fill="#8F5A11" font-family="IBM Plex Mono, monospace" font-size="16">buyers start arriving</text>
        <text x="352" y="177" fill="#232B26" font-family="IBM Plex Sans, sans-serif" font-size="18">&#8220;what&#8217;s my cash and stock?&#8221;</text>
      </g>

      <g class="step" style="--d:.18s">
        <rect x="350" y="190" width="280" height="170" rx="12" fill="#0A3D30"/>
        <text x="374" y="228" fill="#F1EFE8" font-family="Marcellus, Georgia, serif" font-size="26">The Live Owner</text>
        <text x="374" y="256" fill="#F1EFE8" font-family="Marcellus, Georgia, serif" font-size="26">Dashboard</text>
        <text x="374" y="284" fill="#BFE3D5" font-family="IBM Plex Mono, monospace" font-size="17">02 &#183; +OMR 650</text>
      </g>

      <g class="anno" style="--d:.75s">
        <path d="M672 66 l-12 -7 v14 z" fill="#BA7517"/>
        <text x="694" y="71" fill="#8F5A11" font-family="IBM Plex Mono, monospace" font-size="16">quotes pile up</text>
        <text x="672" y="97" fill="#232B26" font-family="IBM Plex Sans, sans-serif" font-size="18">&#8220;who chases the invoice?&#8221;</text>
      </g>

      <g class="step" style="--d:.36s">
        <rect x="670" y="110" width="300" height="250" rx="12" fill="#072B22"/>
        <text x="694" y="148" fill="#F1EFE8" font-family="Marcellus, Georgia, serif" font-size="26">The Full Autopilot</text>
        <text x="694" y="176" fill="#BFE3D5" font-family="IBM Plex Mono, monospace" font-size="17">03 &#183; +OMR 900</text>
      </g>

      <line x1="30" y1="372" x2="970" y2="372" stroke="#DED8C8" stroke-width="2"/>
    </svg>

    <div class="grid g3" data-stagger>
      <article class="card sys-card">
        <span class="n">01</span>
        <h3>The Smart Storefront</h3>
        <p>A bilingual site that answers buyers in Arabic and English, records who they are, and hands the live ones to your WhatsApp.</p>
        <span class="tag">One-time &#183; <b>OMR 950</b></span>
        <a class="tlink" href="/en/services-v4/#storefront">See what&#8217;s inside <span class="arw">&rarr;</span></a>
      </article>
      <article class="card sys-card">
        <span class="n">02</span>
        <h3>The Live Owner Dashboard</h3>
        <p>Your cash position, stock and open leads on one screen &mdash; without phoning three people to assemble it.</p>
        <span class="tag">Add-on &#183; <b>+OMR 650</b></span>
        <a class="tlink" href="/customized-ceo-dashboard-demo/">Open the live demo <span class="arw">&rarr;</span></a>
      </article>
      <article class="card sys-card">
        <span class="n">03</span>
        <h3>The Full Autopilot</h3>
        <p>Something has to chase the quotes and the invoices. This does it, on schedule, without anyone remembering to.</p>
        <span class="tag">Add-on &#183; <b>+OMR 900</b></span>
        <a class="tlink" href="/en/services-v4/#autopilot">See what&#8217;s inside <span class="arw">&rarr;</span></a>
      </article>
    </div>
  </div>
</section>

<!-- ================================================= S4 - PROOF YOU CAN CLICK -->
<section class="s-dark" id="proof">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> Proof, not testimonials</p>
    <h2 class="h2">I have no client logos yet. So open the systems instead.</h2>
    <p class="lede">These are the real builds, running on real demo data. Click into them &mdash; that is
      a better test than a quote from someone you&#8217;ve never met.</p>

    <div class="tiles" style="margin-top:clamp(28px,4vw,48px)" data-stagger>
      <a class="tile" href="/customized-ceo-dashboard-demo/">
        <span class="live"><i></i>Live demo</span>
        <span class="shot"><img src="/assets/v4/demo-dashboard-960.webp" alt="The CEO dashboard demo: revenue, gross profit and margin cards above a list of ranked actions." width="960" height="600" loading="lazy" decoding="async"></span>
        <span class="cap">
          <h3>The Live Owner Dashboard</h3>
          <p>Cash, margin, dead stock and what to do about it &mdash; ranked, in plain sentences.</p>
          <span class="tlink">Open it <span class="arw">&rarr;</span></span>
        </span>
      </a>

      <a class="tile" href="/whatsapp-receptionist-demo/">
        <span class="live"><i></i>Live demo</span>
        <span class="shot"><img src="/assets/v4/demo-whatsapp-960.webp" alt="The WhatsApp receptionist demo: a lead list beside a full buyer conversation handled by the AI agent." width="960" height="600" loading="lazy" decoding="async"></span>
        <span class="cap">
          <h3>The buyer agent, mid-conversation</h3>
          <p>Watch it qualify a buyer, hold the thread, and book the appointment.</p>
          <span class="tlink">Open it <span class="arw">&rarr;</span></span>
        </span>
      </a>

      <a class="tile tile-wide" href="/en/contact-v4/#test">
        <span class="cap">
          <h3>Or point it at your own business: the Silent Buyer Test</h3>
          <p>I message your business the way a buyer would, then send you the scorecard &mdash; how long you took,
            what was missed, what it cost. Free, and you owe me nothing afterwards.</p>
        </span>
        <span class="chip">Free &#183; <b>5 a week</b></span>
      </a>
    </div>
  </div>
</section>

<!-- ============================================ S5 - THE HONEST COMPARISON -->
<section class="s-panel">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> Against the real alternative</p>
    <h2 class="h2">A week has 168 hours. An administrator covers 40 of them.</h2>
    <p class="lede">Each square is one hour of your week. This is not a claim about quality &mdash; a good
      administrator does things no system can. It is only about coverage.</p>

    <div class="hours-grid" style="margin-top:clamp(28px,4vw,48px)" data-stagger>
      <div class="hcard">
        <h3>Hiring an administrator</h3>
        <p class="sub">OMR 350&ndash;500 / month, every month</p>
        <p class="hlegend">Rows: Sun &rarr; Sat &#183; columns: 00:00 &rarr; 23:00</p>
        {office}
        <span class="hcount"><span data-count="40">40</span> of 168 hours</span>
        <p class="note">Plus visa, insurance, paid leave and sick days &mdash; and the cover stops when they do.</p>
      </div>

      <div class="hcard win">
        <h3>The Smart Storefront</h3>
        <p class="sub">OMR 950, once</p>
        <p class="hlegend">Rows: Sun &rarr; Sat &#183; columns: 00:00 &rarr; 23:00</p>
        {always}
        <span class="hcount"><span data-count="168">168</span> of 168 hours</span>
        <p class="note">It does not replace her. It covers the 128 hours she was never there for.</p>
      </div>
    </div>

    <div class="btn-row" style="margin-top:clamp(26px,3vw,40px)">
      <a class="btn btn-teal" href="/en/services-v4/#price">See the whole price list</a>
      <a class="tlink" href="/en/services-v4/">Every system, in detail <span class="arw">&rarr;</span></a>
    </div>
  </div>
</section>

<!-- ================================================== S6 - THE NAMED PROMISE -->
<section class="s-teal promise">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> The First Inquiry Promise</p>
    <div class="promise-grid" style="margin-top:14px">
      <img class="promise-photo" src="/nahid-founder-2026.webp" alt="Nahid Abyari, founder of AI Profit Lab" width="220" height="220" loading="lazy" decoding="async">
      <div>
        <q>No real buyer inquiry within 30 days of going live? I rebuild it free until you get one.
          If you still don&#8217;t, you get your money back.</q>
        <p class="sig">Nahid Abyari &#183; Founder, AI Profit Lab</p>
      </div>
    </div>
  </div>
</section>

<!-- ===================================================== S7 - EXPLORE RAIL -->
<section class="s-cream grain">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> Keep going</p>
    <h2 class="h2">Four places worth your next five minutes.</h2>

    <div class="rail" style="margin-top:clamp(26px,3.5vw,44px)" data-stagger>
      <a class="rcard" href="/en/services-v4/">
        <span class="rn">01</span>
        <span><h3>What I build</h3><p>Three systems, every price, and what is deliberately not included.</p></span>
        <span class="go">Open <span aria-hidden="true">&rarr;</span></span>
      </a>
      <a class="rcard" href="/en/process-v4/">
        <span class="rn">02</span>
        <span><h3>How it works</h3><p>First message to live system, step by step, with the dates.</p></span>
        <span class="go">Open <span aria-hidden="true">&rarr;</span></span>
      </a>
      <a class="rcard" href="/en/about-v4/">
        <span class="rn">03</span>
        <span><h3>Who builds it</h3><p>One operator, not an agency. Including who I turn away.</p></span>
        <span class="go">Open <span aria-hidden="true">&rarr;</span></span>
      </a>
      <a class="rcard" href="/en/blog/">
        <span class="rn">04</span>
        <span><h3>Articles</h3><p>Plain-language writing on AI for Omani and GCC trading businesses.</p></span>
        <span class="go">Open <span aria-hidden="true">&rarr;</span></span>
      </a>
    </div>
  </div>
</section>

</main>
"""
    return p1 + p2


META = dict(
    slug="index-v4",
    title="AI Profit Lab | Never lose a buyer to silence again — Muscat, Oman",
    desc=("A bilingual storefront with an AI buyer agent that answers your buyers in Arabic and "
          "English while you sleep. One-time fee, no monthly lock-in, built by an operator in Muscat."),
    nav="/en/index-v4/",
    hero=True,
    calc=True,
    next=("Next", "What I build", "/en/services-v4/"),
    schema="""{
  "@context":"https://schema.org",
  "@type":"ProfessionalService",
  "name":"AI Profit Lab",
  "description":"Done-for-you AI automation for trading and distribution SMEs in Oman and the GCC.",
  "url":"https://aiprofitlab.io/en/index-v4/",
  "email":"hello@aiprofitlab.io",
  "telephone":"+968 9924 5250",
  "slogan":"Every success starts with insight",
  "areaServed":[{"@type":"Country","name":"Oman"}],
  "address":{"@type":"PostalAddress","addressLocality":"Bousher","addressRegion":"Muscat","addressCountry":"OM","streetAddress":"South Al Khuwair"},
  "parentOrganization":{"@type":"Organization","name":"Lotus Gulf International","identifier":"CR 1570092"},
  "founder":{"@type":"Person","name":"Nahid Abyari"},
  "priceRange":"OMR 950 - OMR 2200"
}""",
)
