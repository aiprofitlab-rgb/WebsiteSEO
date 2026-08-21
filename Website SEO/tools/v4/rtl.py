#!/usr/bin/env python3
"""
The Arabic / right-to-left layer for the v4 page set.

Everything here is scoped to `[dir=rtl]` and appended AFTER the page's own CSS,
so it wins on specificity ties without any `!important`. Nothing in this file
is loaded by an English page - `build_v4.render()` only appends it when it is
rendering Arabic - but writing it as an override layer rather than a second
design system is what keeps the two languages on one set of components: an
edit to a card, a button or the footer lands on both pages at once, and only
the handful of declarations that genuinely have a direction are restated.

Three kinds of rule live here, in this order:

  1. TOKENS - the type stack. Latin display faces carry no Arabic glyphs, so
     the whole stack is swapped rather than fallen back on.
  2. TYPE   - line heights, sizes, and the removal of tracking / small-caps.
     Letter-spacing on Arabic breaks the join between letters, which is not a
     stylistic preference: it makes a word unreadable.
  3. MIRROR - the declarations that name a physical side. The kit is written on
     logical properties almost throughout, so this list is short by design; if
     it starts growing, the fix belongs in the component, not here.

RTL_BASE is shared with tools/v4/blog_chrome.py, which serves the same chrome
to 300 migrated articles. Keeping one copy is the point - the article header
and the core-page header are the same markup, and two RTL layers would drift.
"""

# --------------------------------------------------------------------------
# 1 + 2. Type stack and typography.
# --------------------------------------------------------------------------
RTL_BASE = """
/* --------------------------------------------------------------- Arabic */
[dir=rtl]{
  --display:'Markazi Text','Amiri',Georgia,serif;
  --sans:'IBM Plex Sans Arabic','IBM Plex Sans',-apple-system,'Segoe UI',sans-serif;
  --mono:'IBM Plex Mono','IBM Plex Sans Arabic',ui-monospace,SFMono-Regular,Menlo,monospace;
}
/* Naskh needs more leading than Latin at the same size: the descenders and the
   dots below the baseline collide at 1.7. */
[dir=rtl] body{line-height:1.85}
[dir=rtl] h1,[dir=rtl] h2,[dir=rtl] h3,[dir=rtl] h4{letter-spacing:0}
/* Markazi Text runs visibly small against IBM Plex Sans Arabic, so display
   type is bumped a step and given the leading Arabic ascenders need. */
[dir=rtl] .h1{font-size:clamp(2.3rem,5.4vw,4.2rem);line-height:1.24}
[dir=rtl] .h2{font-size:clamp(1.9rem,4.2vw,3.1rem);line-height:1.32}
[dir=rtl] .h3{line-height:1.4}
[dir=rtl] .lede{line-height:1.85}
[dir=rtl] .phero .h1{margin-bottom:26px}

/* Tracking and small-caps are Latin devices. On Arabic, letter-spacing breaks
   the join between letters and text-transform does nothing at all, so both
   come off everywhere the kit sets them. */
[dir=rtl] .eyebrow,[dir=rtl] .chip,[dir=rtl] .btn,[dir=rtl] .tlink,
[dir=rtl] .lnk,[dir=rtl] .top-wa,[dir=rtl] .facts span,[dir=rtl] .card .n,
[dir=rtl] .pager .pl,[dir=rtl] .foot h4,[dir=rtl] .soc-h,[dir=rtl] .rk,
[dir=rtl] .rt,[dir=rtl] .legal,[dir=rtl] .mfoot,[dir=rtl] .mmenu a,
[dir=rtl] .mmenu a em,[dir=rtl] .skip{
  letter-spacing:0;text-transform:none;
}

/* Figures, prices, phone numbers and times stay left-to-right inside Arabic
   running text. Without this, "OMR 1,023" comes out reversed and "9:47" reads
   as "47:9".

   isolate, NOT embed. Under `embed` the Latin run still takes part in the
   surrounding reorder, so a figure at the start of a line gets thrown to the
   far edge of its box and the Arabic closes up behind it - which is exactly
   what happened to the four stats cells on the services page. `isolate`
   treats the run as one neutral object sitting at its logical position. */
[dir=rtl] .num,[dir=rtl] [dir=ltr]{direction:ltr;unicode-bidi:isolate}
/* A figure that is the whole of a display value gets its own line box, so the
   isolation has nothing to fight with; the cell just reads right-to-left. */
[dir=rtl] .stats div b,[dir=rtl] .bignum,[dir=rtl] .hcount{unicode-bidi:isolate}

/* An Arabic page wraps every figure in `.num` so the bidi algorithm cannot
   reorder it. That wrapper is a <span>, and it lands INSIDE components whose
   caption rule is an unscoped descendant selector - `.pricetag span`,
   `.kpi span`, `.mock .mh span`, `.figs span`. Those are (0,1,1) and beat a
   bare `.num`, so a 2.3rem price was rendering its digits at 0.85rem in
   uppercase grey while the currency beside it stayed full size.
   `[dir=rtl] .num` is (0,2,0) and out-specifies all of them. Everything here
   is inherit-or-off: the figure takes the size and colour of whatever it sits
   in, and only keeps the tabular mono face the brand book gives to numerals.
   The English pages are untouched - they write their figures as plain text. */
[dir=rtl] .num{
  display:inline;margin:0;
  font-size:inherit;line-height:inherit;color:inherit;
  letter-spacing:0;text-transform:none;font-weight:inherit;
}
"""

# --------------------------------------------------------------------------
# 3. Mirroring for the shared chrome: header, menu, footer, pager, buttons.
# --------------------------------------------------------------------------
RTL_CHROME = """
/* ---------------------------------------------------------- skip link */
[dir=rtl] .skip{left:auto;right:-9999px;border-radius:0 0 0 8px}
[dir=rtl] .skip:focus{left:auto;right:0}

/* --------------------------------------------------------- the marquee */
/* The track is a flex row of two identical halves scrolled by half its own
   width. Under dir=rtl the row is laid out right-to-left, so the same
   -50% walks it the wrong way and the strip empties out from the right. */
[dir=rtl] .facts .track{animation-name:mq-rtl}
@keyframes mq-rtl{to{transform:translateX(50%)}}

/* ------------------------------------------------ underlines and sheens */
/* transform-origin:0 50% means "grow from the left". Every one of these wants
   to grow from the reader's starting edge, which is the right one here. */
[dir=rtl] .nav a.lnk::after,[dir=rtl] .card::before,
[dir=rtl] .foot .fcol a::after,[dir=rtl] .lane-track i,
[dir=rtl] .cine-progress i{transform-origin:100% 50%}
[dir=rtl] .btn::after{transform:translateX(130%)}
[dir=rtl] .btn:hover::after{transform:translateX(-130%)}
[dir=rtl] .review::after{transform:translateX(110%)}
[dir=rtl] .review:hover::after{transform:translateX(-110%)}

/* --------------------------------------------------- arrows that travel */
/* The glyph itself is flipped in the markup (&larr; not &rarr;), so only the
   direction of travel is restated here. */
[dir=rtl] .tlink:hover .arw{transform:translateX(-4px)}
[dir=rtl] .pager a:hover .parw{transform:translateX(-10px)}
[dir=rtl] .review:hover .rarw{transform:translateX(-9px)}
[dir=rtl] .foot .fcol .direct a:hover svg{transform:translateX(-2px)}
/* .tlink draws its own underline from a background-position; 0 is the left. */
[dir=rtl] .tlink{background-position:100% 100%}

/* ---------------------------------------------- footer signature, mirrored */
/* On an Arabic page the two lines swap roles: .slogan carries the Arabic and
   .slogan-ar carries the English echo. The amber stroke follows the Latin word
   rather than staying on .slogan, because under Arabic it cuts through the
   descenders and the join. .fsig itself is built on logical properties and
   mirrors on its own. */
[dir=rtl] .foot .slogan .ins::after{content:none}
/* .slogan-ar carries Latin here, so it drops the Naskh fallback stack and
   takes Marcellus - which the page already loads for the wordmark - instead of
   rendering the English echo in an Arabic face. */
[dir=rtl] .foot .slogan-ar{font-family:'Marcellus',Georgia,'Times New Roman',serif}
[dir=rtl] .foot .slogan-ar .ins{display:inline-block;position:relative;white-space:nowrap}
[dir=rtl] .foot .slogan-ar .ins::after{
  content:"";position:absolute;left:-.04em;right:-.04em;bottom:-.12em;
  height:4px;border-radius:3px;
  background:linear-gradient(90deg,rgba(216,146,52,.85),rgba(216,146,52,.22));
  transition:background .45s var(--ease);
}
[dir=rtl] .fsig:hover .slogan-ar .ins::after{background:linear-gradient(90deg,var(--amber-bright),var(--amber-bright))}
/* the beat fades away from the inline-start edge, which is the right one here */
[dir=rtl] .fsig .sig-beat{background:linear-gradient(270deg,rgba(232,201,143,.6),rgba(232,201,143,0))}

@media (max-width:640px){
  /* the arrow is hidden at this width and the padding reserves its gutter */
  [dir=rtl] .review{padding-right:clamp(20px,3vw,30px);padding-left:76px}
}
"""

# --------------------------------------------------------------------------
# 3b. Mirroring for the page-level components, in page order.
# --------------------------------------------------------------------------
RTL_PAGES = """
/* ================================================================== hero */
/* The copy column deliberately does NOT mirror. The frame sequence puts the
   subject's silhouette from x=25% rightwards, and the light band the dark type
   is legible on is the left one - flipping the block would set Arabic over the
   subject's head. Only the alignment inside the box changes, so the text still
   starts at the reader's own edge. */
[dir=rtl] .lead,[dir=rtl] .endcard,[dir=rtl] .beat{text-align:right}
@media (min-width:1100px){
  [dir=rtl] .lead .sub{margin-inline:0 auto}
  [dir=rtl] .lead-cta{justify-content:flex-end}
}

/* ============================================================ home / S2 */
[dir=rtl] .qa-a{
  padding-left:0;padding-right:clamp(15px,2vw,24px);
  border-left:0;border-right:2px solid var(--amber);
}

/* ============================================================ home / S5 */
[dir=rtl] .bub li{padding-left:0;padding-right:18px}
[dir=rtl] .bub li::before{left:auto;right:2px}
[dir=rtl] .bub .tme{text-align:left}

/* ============================================================ home / S7 */
[dir=rtl] .tile .live{left:auto;right:14px}

@media (max-width:960px){
  [dir=rtl] .promise-grid{text-align:right}
  [dir=rtl] .qa-a{margin-left:0;margin-right:calc(2ch + 20px)}
}
@media (max-width:560px){
  [dir=rtl] .qa-a{margin-right:0}
}

/* ============================================================== services */
[dir=rtl] .stats div{border-right:0;border-left:1px solid var(--line)}
[dir=rtl] .stats div:last-child{border-left:0}
/* The tick keeps its shape - a check mark mirrored is a backwards check mark.
   Only where it sits changes. Same rule for .checks and .getlist below. */
[dir=rtl] .deliver li{padding-left:0;padding-right:28px}
[dir=rtl] .deliver li::before{left:auto;right:0}
/* The buyer-agent mock is a WhatsApp thread carrying BOTH languages, because
   answering an Arabic buyer and an English one in the same thread is the whole
   point of the illustration. Bubbles are marked with dir in the markup; the
   thread itself flips its speaker sides so the visitor's own side is right. */
[dir=rtl] .msg[dir=ltr]{text-align:left}
[dir=rtl] .msg.them{border-bottom-left-radius:14px;border-bottom-right-radius:4px}
[dir=rtl] .msg.us{border-bottom-right-radius:14px;border-bottom-left-radius:4px}
[dir=rtl] .alertrow{border-left:1px solid var(--line);border-right:3px solid var(--alert)}
[dir=rtl] .alertrow.ok{border-left-color:var(--line);border-right-color:var(--wa)}
[dir=rtl] table.t caption{text-align:right}
[dir=rtl] table.t th,[dir=rtl] table.t td{text-align:right}
[dir=rtl] table.t td.n,[dir=rtl] table.t th.n{text-align:left}
/* The highlight rule on the flagship row is an inset shadow on the row's
   first cell, which in RTL is its right edge - the shadow has to move with it
   or the mark lands in the middle of the table. */
[dir=rtl] table.t tr.hi td:first-child{box-shadow:inset -3px 0 0 var(--amber)}
[dir=rtl] .nolog li{padding-left:0;padding-right:34px}
[dir=rtl] .nolog li::before{left:auto;right:0}
[dir=rtl] .nolog li::after{left:auto;right:4px}
@media (max-width:760px){
  [dir=rtl] .stats div:nth-child(2){border-left:0}
}

/* =============================================================== process */
[dir=rtl] .checks li{padding-left:0;padding-right:28px}
[dir=rtl] .checks li::before{left:auto;right:2px}

/* ================================================================= about */
[dir=rtl] .portrait::after{right:auto;left:-14px}
[dir=rtl] .path div{padding:clamp(22px,2.6vw,32px) 0 clamp(22px,2.6vw,32px) clamp(16px,2vw,26px)}
[dir=rtl] .path div+div{
  padding-left:0;padding-right:clamp(16px,2vw,26px);
  border-left:0;border-right:1px solid var(--line);
}
[dir=rtl] .s-dark .path div+div{border-right-color:var(--line-dark)}
/* A drop cap on Naskh collides with the letters that join it and with the dots
   below the baseline. The opening paragraph takes size and colour instead. */
[dir=rtl] .prose p.open::first-letter{float:none;font-size:inherit;padding:0;color:inherit}
[dir=rtl] .prose p.open{font-size:clamp(1.24rem,2.1vw,1.5rem);color:var(--teal-950)}
@media (max-width:900px){
  [dir=rtl] .path div:nth-child(3){border-right:0;padding-right:0}
}

/* =============================================================== contact */
[dir=rtl] .getlist li{padding-left:0;padding-right:30px}
[dir=rtl] .getlist li::before{left:auto;right:3px}
[dir=rtl] .faq summary{padding:22px 0 22px 44px}
[dir=rtl] .faq summary::after{right:auto;left:8px}

/* ============================================================ simulators */
[dir=rtl] .legend i{margin-right:0;margin-left:7px}

/* ================================================================= demos */
[dir=rtl] .steps2::before{left:auto;right:6px}
[dir=rtl] .steps2 li{padding:0 30px 18px 0}
[dir=rtl] .steps2 li::before{left:auto;right:0}
[dir=rtl] .alert{border-left:1px solid var(--line-dark);border-right:2px solid var(--amber)}
[dir=rtl] .alert.red{border-left-color:var(--line-dark);border-right-color:var(--alert)}
[dir=rtl] .alert.green{border-left-color:var(--line-dark);border-right-color:var(--wa)}
[dir=rtl] .mini td:nth-child(2){padding-left:0;padding-right:12px}
[dir=rtl] .mini td.r{text-align:left}
[dir=rtl] .dnote{padding-left:0;padding-right:14px;border-left:0;border-right:2px solid var(--amber)}
/* Bubbles in the player carry their own dir, set per message from SCENARIOS. */
[dir=rtl] .bub[dir=ltr]{text-align:left}
[dir=rtl] .bub .t{text-align:left}

/* ============================================================== checkout */
[dir=rtl] .opt .flag{margin-left:0;margin-right:9px}
[dir=rtl] .sum::before{background:linear-gradient(270deg,var(--amber),var(--amber-pale),transparent)}
[dir=rtl] .offline{border-left:1px solid var(--line);border-right:3px solid var(--amber)}
[dir=rtl] .after div{padding-left:0;padding-right:0}
[dir=rtl] .after div::before{left:auto;right:0}
[dir=rtl] .after div::after{left:0;right:34px}

/* ================================================================= order */
[dir=rtl] .nxt li{padding:20px 52px 20px 0}
[dir=rtl] .nxt li::before{left:auto;right:0}
"""

CORE_RTL_CSS = RTL_BASE + RTL_CHROME + RTL_PAGES
