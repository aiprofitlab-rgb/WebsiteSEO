#!/usr/bin/env python3
"""
AI Profit Lab — v4 page kit.

Shared chrome (head, tokens, design system, header, footer, motion) for the
`public_html/en/*-v4.html` set. Pages are emitted SELF-CONTAINED — every byte of
CSS and JS is inlined rather than linked.

Why inline rather than a shared /assets/css file: the host serves /assets/**
with `cache-control: public, max-age=31536000, immutable`, so an edited
stylesheet on a stable filename never reaches a returning visitor without a
filename bump or a CDN purge. HTML is served `max-age=600, must-revalidate`
(x-hcdn-cache-status: DYNAMIC), so an inlined change propagates in ~10 minutes
on its own. During a design review that difference is the whole game.

Palette, type and voice come from brand/docs/02-brand-book.md. Prices come from
en/index-v3.html, which is the page that currently publishes them.
"""

# --------------------------------------------------------------------------
# Design tokens — verbatim from the brand book, plus three working values.
# --------------------------------------------------------------------------
TOKENS = """
:root{
  --teal-950:#072B22; --teal-900:#0A3D30; --teal:#0F6E56; --teal-600:#158268;
  --amber:#BA7517;    --amber-bright:#D89234; --amber-pale:#E8C98F;
  /* Amber for SMALL TEXT on light grounds only. #BA7517 on cream measures
     3.19:1, under the 4.5:1 floor for body-size text; this tint measures
     4.97:1. The brand accent itself is unchanged - shapes, rules, marks and
     large display type all keep --amber. */
  --amber-text:#8F5A11;
  --cream:#F1EFE8;    --panel:#FAF8F2;    --panel-2:#EAE4D5;  --white:#FFFFFF;
  --ink:#232B26;      --muted:#5A665D;    --line:#DED8C8;
  --wa:#1FAF5E;       --alert:#A6431F;
  /* sampled from the hero footage's own background so the stage never seams */
  --taupe:#9F9683;
  /* cream at 62% — the readable tint for hairlines on dark grounds */
  --line-dark:rgba(241,239,232,.16);
  --display:'Marcellus',Georgia,'Times New Roman',serif;
  --sans:'IBM Plex Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
  --mono:'IBM Plex Mono',ui-monospace,SFMono-Regular,Menlo,monospace;
  --ease:cubic-bezier(.22,.7,.25,1);
}
"""

# --------------------------------------------------------------------------
# Base: reset, type scale, layout primitives, surfaces, header, footer,
# buttons, cards, and the motion kit. Shared by all five pages.
# --------------------------------------------------------------------------
BASE_CSS = """
*{box-sizing:border-box}
/* clip, NOT hidden — overflow-x:hidden silently makes this a scroll container
   and position:sticky stops working on every page that uses it. */
html,body{overflow-x:clip}
html{scroll-behavior:smooth;font-size:17px;-webkit-text-size-adjust:100%}
body{
  margin:0;background:var(--cream);color:var(--ink);
  font-family:var(--sans);font-size:19px;line-height:1.7;
  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;
}
img{max-width:100%;height:auto;display:block}
h1,h2,h3,h4{font-family:var(--display);font-weight:400;margin:0;text-wrap:balance;letter-spacing:-.005em}
p{margin:0 0 1.1em}
a{color:var(--teal);text-underline-offset:3px}
::selection{background:var(--amber-pale);color:var(--teal-950)}
:focus-visible{outline:2px solid var(--amber);outline-offset:3px;border-radius:3px}

/* ---------------------------------------------------------------- layout */
.wrap{width:min(1180px,92vw);margin-inline:auto}
.wrap-n{width:min(780px,92vw);margin-inline:auto}
section{position:relative;padding:clamp(74px,9vw,138px) 0}
.pad-s{padding:clamp(48px,6vw,84px) 0}

/* Paper grain. Two-octave fractal noise at 3.5% — visible as texture on a
   large cream field, invisible as pattern. Painted on a pseudo-element so it
   never intercepts a pointer event. */
.grain::before{
  content:"";position:absolute;inset:0;pointer-events:none;z-index:0;opacity:.038;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='2'/%3E%3C/filter%3E%3Crect width='180' height='180' filter='url(%23n)'/%3E%3C/svg%3E");
}
.grain>*{position:relative;z-index:1}

/* ------------------------------------------------------------- surfaces */
.s-cream{background:var(--cream)}
.s-panel{background:var(--panel)}
.s-white{background:var(--white)}
.s-panel2{background:var(--panel-2)}
.s-dark{background:var(--teal-950);color:var(--cream)}
.s-teal{background:var(--teal-900);color:var(--cream)}
.s-dark h1,.s-dark h2,.s-dark h3,.s-teal h1,.s-teal h2,.s-teal h3{color:var(--cream)}
.s-dark .eyebrow,.s-teal .eyebrow{color:var(--amber-pale)}
.s-dark .lede,.s-teal .lede{color:rgba(241,239,232,.76)}
.s-dark a,.s-teal a{color:var(--amber-bright)}
.s-dark .rule,.s-teal .rule{background:var(--line-dark)}

/* ----------------------------------------------------------------- type */
.eyebrow{
  font-family:var(--mono);font-size:.85rem;font-weight:500;letter-spacing:.16em;
  text-transform:uppercase;color:var(--muted);margin:0 0 18px;
  display:flex;align-items:center;gap:10px;
}
.eyebrow .star{color:var(--amber);font-size:1.05em;line-height:1}
.h1{font-size:clamp(2.7rem,6.2vw,5rem);line-height:1.02;color:var(--teal-950)}
.h2{font-size:clamp(2rem,4.4vw,3.4rem);line-height:1.08;color:var(--teal-950);margin:0 0 20px}
.h3{font-size:clamp(1.35rem,2.4vw,1.75rem);line-height:1.2;color:var(--teal-950)}
.lede{font-size:clamp(1.06rem,1.6vw,1.25rem);color:var(--muted);max-width:60ch;line-height:1.65}
.mono{font-family:var(--mono)}
.num{font-family:var(--mono);font-variant-numeric:tabular-nums}
.rule{height:1px;background:var(--line);border:0;margin:0}
.star{color:var(--amber)}
.dot{width:.42em;height:.42em;border-radius:50%;background:var(--amber);display:inline-block;vertical-align:.12em}

/* A section divider that is a mark, not a line: hairline — asterism — hairline */
.asterism{display:flex;align-items:center;gap:18px;color:var(--amber);margin:0 0 clamp(34px,5vw,58px)}
.asterism::before,.asterism::after{content:"";flex:1;height:1px;background:var(--line)}
.s-dark .asterism::before,.s-dark .asterism::after,
.s-teal .asterism::before,.s-teal .asterism::after{background:var(--line-dark)}

/* -------------------------------------------------------------- buttons */
.btn{
  display:inline-flex;align-items:center;justify-content:center;gap:10px;
  font-family:var(--sans);font-size:1.02rem;font-weight:500;text-decoration:none;
  padding:15px 26px;border-radius:99px;border:1px solid transparent;cursor:pointer;
  position:relative;overflow:hidden;
  transition:transform .2s var(--ease),box-shadow .2s var(--ease),background .2s,border-color .2s,color .2s;
}
/* travelling sheen — a single pass on hover, not a loop */
.btn::after{
  content:"";position:absolute;inset:0;pointer-events:none;
  background:linear-gradient(105deg,transparent 38%,rgba(255,255,255,.28) 50%,transparent 62%);
  transform:translateX(-130%);transition:transform .65s var(--ease);
}
.btn:hover::after{transform:translateX(130%)}
.btn:hover{transform:translateY(-2px)}
.btn-teal{background:var(--teal);color:#fff;box-shadow:0 14px 30px -16px rgba(15,110,86,.9)}
.btn-teal:hover{background:var(--teal-600)}
.btn-wa{background:var(--wa);color:#fff;box-shadow:0 14px 30px -16px rgba(31,175,94,.9)}
.btn-amber{background:var(--amber);color:var(--teal-950);font-weight:600;box-shadow:0 14px 30px -16px rgba(186,117,23,.9)}
.btn-ghost{background:transparent;color:var(--teal-900);border-color:rgba(35,43,38,.28)}
.btn-ghost:hover{border-color:var(--teal);background:var(--white)}
.s-dark .btn-ghost,.s-teal .btn-ghost{color:var(--cream);border-color:var(--line-dark)}
.s-dark .btn-ghost:hover,.s-teal .btn-ghost:hover{background:rgba(241,239,232,.08);border-color:var(--amber-bright)}
/* Button text colour has to out-specify `.s-dark a` / `.s-teal a` (0,1,1),
   which otherwise repaints every button label on a dark section amber - and
   an amber label on an amber pill is invisible. A lone `.btn-amber` (0,1,0)
   loses that cascade, so the dark-section variants are restated here. */
.s-dark .btn-amber,.s-teal .btn-amber{color:var(--teal-950)}
.s-dark .btn-teal,.s-teal .btn-teal,
.s-dark .btn-wa,.s-teal .btn-wa{color:#fff}
.btn .wa-icon{width:19px;height:19px}
.wa-icon{width:17px;height:17px;fill:currentColor;flex:none}
.btn-row{display:flex;gap:12px;flex-wrap:wrap;align-items:center}

/* Inline text link that draws its own underline on hover */
.tlink{
  font-family:var(--mono);font-size:.9rem;letter-spacing:.08em;text-transform:uppercase;
  color:var(--teal);text-decoration:none;display:inline-flex;align-items:center;gap:9px;
  padding-bottom:3px;background-image:linear-gradient(var(--amber),var(--amber));
  background-size:0 1px;background-position:0 100%;background-repeat:no-repeat;
  transition:background-size .35s var(--ease),color .2s;
}
.tlink:hover{background-size:100% 1px;color:var(--amber-text)}
.tlink .arw{transition:transform .3s var(--ease)}
.tlink:hover .arw{transform:translateX(4px)}
.s-dark .tlink,.s-teal .tlink{color:var(--amber-pale)}

/* ---------------------------------------------------------------- cards */
.card{
  position:relative;background:var(--panel);border:1px solid var(--line);
  border-radius:16px;padding:clamp(24px,3vw,34px);overflow:hidden;
  transition:transform .35s var(--ease),box-shadow .35s var(--ease),border-color .35s;
}
.card::before{
  content:"";position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,var(--amber),var(--amber-pale));
  transform:scaleX(0);transform-origin:0 50%;transition:transform .5s var(--ease);
}
.card:hover{transform:translateY(-4px);box-shadow:0 26px 50px -34px rgba(7,43,34,.55);border-color:var(--panel-2)}
.card:hover::before{transform:scaleX(1)}
.card .n{font-family:var(--mono);font-size:.9rem;letter-spacing:.14em;color:var(--amber-text);display:block;margin-bottom:14px}
.card h3{margin:0 0 10px}
.card p{color:var(--muted);font-size:1rem;margin:0}
.s-dark .card,.s-teal .card{background:rgba(241,239,232,.045);border-color:var(--line-dark)}
.s-dark .card p,.s-teal .card p{color:rgba(241,239,232,.72)}
.s-dark .card .n,.s-teal .card .n{color:var(--amber-bright)}

.grid{display:grid;gap:clamp(16px,2vw,24px)}
.g2{grid-template-columns:repeat(2,1fr)}
.g3{grid-template-columns:repeat(3,1fr)}
.g4{grid-template-columns:repeat(4,1fr)}

.chip{
  display:inline-flex;align-items:center;gap:8px;font-family:var(--mono);font-size:.82rem;
  letter-spacing:.06em;text-transform:uppercase;color:var(--teal-900);
  background:var(--white);border:1px solid var(--line);border-radius:99px;padding:7px 14px;
}
.chip b{color:var(--amber-text);font-weight:500}
.s-dark .chip,.s-teal .chip{background:rgba(241,239,232,.07);border-color:var(--line-dark);color:var(--cream)}
.s-dark .chip b,.s-teal .chip b{color:var(--amber-bright)}

/* ------------------------------------------------------------ page hero */
.phero{padding:clamp(150px,17vw,220px) 0 clamp(56px,7vw,90px);position:relative;overflow:hidden}
.phero .h1{margin:0 0 22px}
.phero .lede{font-size:clamp(1.12rem,1.9vw,1.4rem);color:var(--muted)}

/* ------------------------------------------------------------ marquee */
.facts{
  border-top:1px solid var(--line);border-bottom:1px solid var(--line);
  background:var(--panel-2);overflow:hidden;padding:15px 0;
}
.facts .track{display:flex;width:max-content;animation:mq 42s linear infinite}
.facts .half{display:flex;gap:0;flex:none}
.facts span{
  font-family:var(--mono);font-size:.86rem;letter-spacing:.12em;text-transform:uppercase;
  color:var(--teal-900);white-space:nowrap;display:inline-flex;align-items:center;gap:12px;padding:0 26px;
}
.facts .star{opacity:.9}
@keyframes mq{to{transform:translateX(-50%)}}
.facts:hover .track{animation-play-state:paused}

/* ------------------------------------------------------------- header */
.top{
  position:fixed;inset:0 0 auto 0;z-index:80;display:flex;align-items:center;
  justify-content:space-between;gap:16px;padding:13px clamp(16px,3vw,30px);
  border-bottom:1px solid transparent;transition:background .3s,border-color .3s,padding .3s;
}
.top.solid{background:rgba(241,239,232,.93);backdrop-filter:blur(12px);border-bottom-color:var(--line);padding-top:9px;padding-bottom:9px}
.top .mark{display:block;width:clamp(128px,15vw,160px);height:auto}
.nav{display:flex;align-items:center;gap:clamp(12px,1.9vw,24px)}
.nav a.lnk{
  position:relative;font-family:var(--mono);font-size:.85rem;letter-spacing:.1em;
  text-transform:uppercase;text-decoration:none;color:var(--teal-900);white-space:nowrap;opacity:.86;
  transition:opacity .2s,color .2s;padding:4px 0;
}
.nav a.lnk::after{
  content:"";position:absolute;left:0;right:0;bottom:0;height:1px;background:var(--amber);
  transform:scaleX(0);transform-origin:0 50%;transition:transform .35s var(--ease);
}
.nav a.lnk:hover{opacity:1;color:var(--teal)}
.nav a.lnk:hover::after,.nav a.lnk[aria-current=page]::after{transform:scaleX(1)}
.nav a.lnk[aria-current=page]{opacity:1;color:var(--teal-950)}
/* The one and only WhatsApp entry point on the page. There used to be two -
   this pill in white up here plus a green float bottom-right - which meant one
   action wearing two different looks, and on a phone the float sat on top of
   the content. The pill is now the green one, the float is gone, and it stays
   on screen at every width, including where the nav links collapse into the
   burger. */
.top-wa{
  display:inline-flex;align-items:center;gap:8px;font-family:var(--mono);font-size:.85rem;
  letter-spacing:.1em;text-transform:uppercase;text-decoration:none;color:#fff;white-space:nowrap;
  border:1px solid transparent;background:var(--wa);
  padding:10px 16px;border-radius:99px;
  box-shadow:0 12px 26px -16px rgba(31,175,94,.9);
  transition:background .2s,transform .2s,box-shadow .2s;
}
.top-wa:hover{background:#199B51;transform:translateY(-1px);box-shadow:0 16px 30px -16px rgba(31,175,94,1)}
.top-wa .wa-icon{width:18px;height:18px}

/* Mobile menu. The v3 header simply hid its links below 1100px, which on a
   phone left the site with no way to reach any other page — the exact
   opposite of what this set is for. */
.burger{
  display:none;width:44px;height:44px;border-radius:50%;border:1px solid rgba(35,43,38,.22);
  background:rgba(250,248,242,.82);cursor:pointer;padding:0;align-items:center;justify-content:center;
}
.burger i{display:block;width:18px;height:1.5px;background:var(--teal-900);position:relative;transition:background .2s}
.burger i::before,.burger i::after{content:"";position:absolute;left:0;width:18px;height:1.5px;background:var(--teal-900);transition:transform .3s var(--ease)}
.burger i::before{top:-6px}.burger i::after{top:6px}
.menu-open .burger i{background:transparent}
.menu-open .burger i::before{transform:translateY(6px) rotate(45deg)}
.menu-open .burger i::after{transform:translateY(-6px) rotate(-45deg)}
.mmenu{
  position:fixed;inset:0;z-index:75;background:var(--teal-950);color:var(--cream);
  display:flex;flex-direction:column;justify-content:center;gap:6px;padding:96px clamp(24px,7vw,64px) 40px;
  opacity:0;visibility:hidden;transform:translateY(-12px);
  transition:opacity .35s var(--ease),transform .35s var(--ease),visibility .35s;
}
.menu-open .mmenu{opacity:1;visibility:visible;transform:none}
.mmenu a{
  font-family:var(--display);font-size:clamp(2rem,8vw,3rem);color:var(--cream);text-decoration:none;
  padding:10px 0;border-bottom:1px solid var(--line-dark);display:flex;align-items:baseline;gap:16px;
}
.mmenu a:hover{color:var(--amber-bright)}
.mmenu a em{font-family:var(--mono);font-size:.8rem;font-style:normal;letter-spacing:.14em;color:var(--amber-bright);opacity:.8}
.mmenu .mfoot{margin-top:28px;font-family:var(--mono);font-size:.85rem;letter-spacing:.08em;color:rgba(241,239,232,.6)}

/* --------------------------------------------------------------- pager */
.pager{border-top:1px solid var(--line);background:var(--panel)}
.pager a{
  display:flex;align-items:center;justify-content:space-between;gap:24px;text-decoration:none;
  padding:clamp(34px,5vw,62px) 0;color:var(--teal-950);
}
.pager .pl{font-family:var(--mono);font-size:.85rem;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);display:block;margin-bottom:10px}
.pager .pt{font-family:var(--display);font-size:clamp(1.7rem,4.4vw,3rem);line-height:1.08;display:block;transition:color .25s}
.pager a:hover .pt{color:var(--teal)}
.pager .parw{font-size:clamp(1.8rem,4vw,2.6rem);color:var(--amber);transition:transform .35s var(--ease);flex:none}
.pager a:hover .parw{transform:translateX(10px)}

/* -------------------------------------------------------------- footer */
.foot{
  position:relative;background:var(--teal-950);color:rgba(241,239,232,.74);
  padding:clamp(58px,7vw,92px) 0 40px;font-size:1rem;
  /* Two soft lights instead of a flat slab: a teal wash rising from the top
     left, an amber one from the right, both well under the text contrast. */
  background-image:
    radial-gradient(980px 400px at 8% -14%, rgba(15,110,86,.50), transparent 62%),
    radial-gradient(720px 360px at 96% 6%, rgba(186,117,23,.13), transparent 66%);
}
/* hairline that fades in from both sides - reads as a seam, not a border */
.foot::before{
  content:"";position:absolute;left:0;right:0;top:0;height:1px;
  background:linear-gradient(90deg,transparent,rgba(186,117,23,.7) 26%,rgba(232,201,143,.35) 64%,transparent);
}
.foot .fmark{width:170px;margin-bottom:clamp(24px,2.6vw,30px)}

/* -------------------------------------------------------- footer signature
   The slogan used to be two flat paragraphs stacked under the wordmark, at
   roughly the weight of a caption - nothing about it said "this is the line
   the whole brand hangs on". It is set as a signature block instead: an amber
   rule in the inline-start gutter to anchor it, the payoff word lifted into
   amber over a brush stroke, and a short beat holding the two languages apart
   in place of 2px of dead margin. Built on logical properties (inset-inline-*,
   not left) so the whole frame mirrors on the Arabic pages, where .slogan
   carries the Arabic and .slogan-ar carries the English echo. */
.fsig{position:relative;margin:0}
/* The rule HANGS in the gutter rather than indenting the text, so the slogan,
   the wordmark above it and the socials below it all share one left edge and
   the mark reads as an annotation instead of a nested quote. Bright at the
   first line and gone by the second: a mark in the margin, not a full-height
   border, which would close the block into a box. */
.fsig::before{
  content:"";position:absolute;inset-block:.16em .5em;inset-inline-start:-18px;
  width:2px;border-radius:2px;
  background:linear-gradient(180deg,var(--amber-bright),rgba(186,117,23,.5) 48%,transparent);
}
.foot .slogan{
  font-family:var(--display);font-size:clamp(1.42rem,2.9vw,2.05rem);
  line-height:1.22;letter-spacing:-.01em;color:var(--cream);margin:0;
  text-wrap:balance;
}
/* The payoff word: amber plus a rule under it. inline-block keeps that rule
   the width of the word rather than of the whole line box, and font-weight
   stays 400 because Marcellus ships one weight - anything heavier is a
   synthesised bold that thickens the serifs unevenly. */
.foot .slogan .ins{
  display:inline-block;position:relative;font-weight:400;
  color:var(--amber-pale);white-space:nowrap;
}
.foot .slogan .ins::after{
  /* Thicker than a text-decoration and rounded at both ends, because at 2px
     square this landed as a link underline in a column full of links that do
     not carry one. It has to read as a brush mark. */
  content:"";position:absolute;left:-.04em;right:-.04em;bottom:-.12em;
  height:4px;border-radius:3px;
  background:linear-gradient(90deg,rgba(216,146,52,.85),rgba(216,146,52,.22));
  transition:background .45s var(--ease);
}
/* Deliberately NOT hung off the .rv reveal. Every other block on the page can
   afford to wait for IntersectionObserver; the one line the brand rests on
   cannot be invisible on any page where the motion script fails to run. The
   movement is on hover instead, where nothing depends on it firing. */
.fsig:hover .slogan .ins::after{background:linear-gradient(90deg,var(--amber-bright),var(--amber-bright))}
/* the beat between the two languages */
.fsig .sig-beat{
  display:block;width:44px;height:1px;
  margin:clamp(13px,1.4vw,17px) 0 clamp(11px,1.2vw,14px);
  background:linear-gradient(90deg,rgba(232,201,143,.6),rgba(232,201,143,0));
}
.foot .slogan-ar{
  /* Marcellus carries no Arabic glyphs, so this line ALWAYS falls back - naming
     the fallback is what makes its size predictable across platforms. Held a
     clear step under the English now rather than matching it, so the pair reads
     as statement and echo instead of two headlines competing; width:fit-content
     pulls the RTL box back to the column's inline-start edge instead of letting
     it drift out to the right of the whole column. */
  font-family:'Noto Naskh Arabic','Geeza Pro','Segoe UI',Tahoma,serif;
  font-size:clamp(1.02rem,2vw,1.3rem);line-height:1.8;color:rgba(232,201,143,.78);
  width:fit-content;margin:0;
}
/* The Arabic echo takes the colour but not the stroke: an underline crosses the
   descenders and the join, which is what makes the word hard to read. */
.foot .slogan-ar .ins{color:var(--amber-pale)}
.foot-grid{display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:clamp(26px,4vw,56px);align-items:stretch}
/* The brand column is the short one. Making it a flex column and pushing the
   socials down on auto margin lands the tiles on the same baseline as the
   longest link column instead of leaving a hole under them. */
.foot-brand{display:flex;flex-direction:column}
.soc-wrap{margin-top:auto;padding-top:34px}
.foot h4{font-family:var(--mono);font-size:.82rem;font-weight:500;letter-spacing:.14em;text-transform:uppercase;color:var(--amber-pale);margin:0 0 16px}
.foot ul{list-style:none;margin:0;padding:0}
.foot li{margin-bottom:11px}
.foot a{color:rgba(241,239,232,.74);text-decoration:none;transition:color .2s}
.foot a:hover{color:var(--amber-bright)}

/* Column links: underline wipes in from the left. Drawn on a pseudo-element
   rather than text-decoration so it animates and costs no layout shift. */
.foot .fcol a{position:relative;display:inline-block}
.foot .fcol a::after{
  content:"";position:absolute;left:0;right:0;bottom:-2px;height:1px;background:currentColor;
  transform:scaleX(0);transform-origin:left;transition:transform .3s var(--ease);
}
.foot .fcol a:hover::after{transform:scaleX(1)}

/* The two direct lines are the ones actually worth a click, so they get size,
   an icon and full-cream contrast while the nav links stay quiet. */
.foot .direct{margin-bottom:20px}
.foot .fcol .direct a{display:inline-flex;align-items:center;gap:10px;color:var(--cream);font-size:1.06rem}
.foot .fcol .direct a:hover{color:var(--amber-bright)}
.foot .direct svg{width:17px;height:17px;flex:none;fill:currentColor;color:var(--amber-pale);transition:transform .25s var(--ease)}
.foot .fcol .direct a:hover svg{transform:translateX(2px)}

/* --------------------------------------------------------------- socials */
.foot .soc-h{margin:0 0 14px}
.socials{display:flex;flex-wrap:wrap;gap:10px}
.socials li{margin:0}
.socials a{
  --sc:var(--teal);
  width:46px;height:46px;border-radius:13px;display:inline-flex;align-items:center;justify-content:center;
  border:1px solid var(--line-dark);background:rgba(241,239,232,.03);color:rgba(241,239,232,.82);
  transition:transform .28s var(--ease),background .28s,border-color .28s,color .28s,box-shadow .28s;
}
.socials svg{width:20px;height:20px;fill:currentColor}
.socials a:hover{
  transform:translateY(-4px);background:var(--sc);border-color:transparent;color:#fff;
  box-shadow:0 14px 26px -12px var(--sc);
}

/* ---------------------------------------------------- google review card */
.review{
  position:relative;overflow:hidden;display:flex;align-items:center;gap:clamp(16px,2.6vw,28px);
  margin-top:clamp(36px,5vw,58px);padding:clamp(20px,2.8vw,26px) clamp(20px,3vw,30px);
  border:1px solid rgba(232,201,143,.26);border-radius:20px;text-decoration:none;
  background:linear-gradient(115deg,rgba(186,117,23,.16),rgba(186,117,23,.05) 52%,rgba(241,239,232,.02));
  transition:transform .3s var(--ease),border-color .3s,box-shadow .3s;
}
/* sheen that sweeps across on hover */
.review::after{
  content:"";position:absolute;inset:0;pointer-events:none;
  background:linear-gradient(105deg,transparent 32%,rgba(241,239,232,.11) 46%,transparent 60%);
  transform:translateX(-110%);transition:transform 1s var(--ease);
}
.review:hover{transform:translateY(-3px);border-color:rgba(232,201,143,.55);box-shadow:0 26px 48px -28px rgba(0,0,0,.9)}
.review:hover::after{transform:translateX(110%)}
.review .gmark{flex:none;width:52px;height:52px;border-radius:50%;background:var(--white);display:flex;align-items:center;justify-content:center}
.review .gmark svg{width:26px;height:26px}
.review .rbody{flex:1 1 auto;min-width:0}
.review .stars{display:flex;gap:3px;margin-bottom:8px}
.review .stars svg{width:16px;height:16px;fill:var(--amber-pale);transition:fill .3s var(--ease),transform .3s var(--ease)}
.review:hover .stars svg{fill:var(--amber-bright);transform:scale(1.18)}
.review:hover .stars svg:nth-child(2){transition-delay:.05s}
.review:hover .stars svg:nth-child(3){transition-delay:.1s}
.review:hover .stars svg:nth-child(4){transition-delay:.15s}
.review:hover .stars svg:nth-child(5){transition-delay:.2s}
.review .rk{display:block;font-family:var(--mono);font-size:.76rem;letter-spacing:.14em;text-transform:uppercase;color:var(--amber-pale)}
.review .rt{display:block;font-family:var(--display);font-size:clamp(1.15rem,2.2vw,1.55rem);line-height:1.2;color:var(--cream);margin-top:5px}
.review .rarw{flex:none;font-size:1.7rem;line-height:1;color:var(--amber-bright);transition:transform .35s var(--ease)}
.review:hover .rarw{transform:translateX(9px)}

.foot .legal a{color:rgba(241,239,232,.82);text-decoration:underline;text-underline-offset:3px}
.foot .legal a:hover{color:var(--amber-bright)}
.foot .legal{
  margin-top:clamp(34px,5vw,58px);padding-top:26px;border-top:1px solid var(--line-dark);
  font-family:var(--mono);font-size:.79rem;letter-spacing:.05em;line-height:2;color:rgba(241,239,232,.5);
}

/* ----------------------------------------------------------- motion kit */
.js .rv{opacity:0;transform:translateY(24px);transition:opacity .8s var(--ease),transform .8s var(--ease);transition-delay:var(--d,0s)}
.js .rv.vis{opacity:1;transform:none}
/* Heading wipe. Done with overflow on the heading and a transform on an inner
   span that the motion script injects - NOT with clip-path:inset(), whose
   negative offsets are dropped by the parser, which left every h2 on the page
   permanently clipped to nothing. The padding-bottom gives descenders room so
   the hidden overflow does not shave a "g" once the wipe has finished. */
.js .rvw{display:block;overflow:hidden;padding-bottom:.14em}
.js .rvw .wi{display:block;transform:translateY(106%);transition:transform 1s var(--ease);transition-delay:var(--d,0s)}
.js .rvw.vis .wi{transform:none}
.js .drawn path,.js .drawn line,.js .drawn polyline,.js .drawn circle,.js .drawn rect.dr{
  stroke-dasharray:var(--len,1000);stroke-dashoffset:var(--len,1000);
  transition:stroke-dashoffset 1.5s var(--ease);transition-delay:var(--d,0s);
}
.js .drawn.vis path,.js .drawn.vis line,.js .drawn.vis polyline,.js .drawn.vis circle,.js .drawn.vis rect.dr{stroke-dashoffset:0}

@media (prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}
  *,*::before,*::after{animation-duration:.001ms!important;animation-iteration-count:1!important;transition-duration:.001ms!important}
  .js .rv{opacity:1;transform:none}
  .js .rvw .wi{transform:none}
  .facts .track{animation:none}
}

/* -------------------------------------------------------- breakpoints */
@media (max-width:1080px){
  .g4{grid-template-columns:repeat(2,1fr)}
  .g3{grid-template-columns:repeat(2,1fr)}
}
@media (max-width:900px){
  .nav a.lnk{display:none}
  /* The WhatsApp button survives the collapse as an icon-only circle: it is
     the primary contact route, and the float that used to carry it here is
     gone. It sits above the open menu (header z-index 80 > mmenu 75), so it
     is reachable whether the menu is open or shut. */
  .top-wa{width:44px;height:44px;padding:0;gap:0;justify-content:center}
  .top-wa span{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap}
  .top-wa .wa-icon{width:20px;height:20px}
  .burger{display:inline-flex}
  .foot-grid{grid-template-columns:1fr 1fr}
  /* brand block goes full width so the two link columns still sit side by side */
  .foot-brand{grid-column:1/-1;margin-bottom:10px}
}
@media (max-width:640px){
  body{font-size:18px}
  /* .wrap leaves ~4vw of gutter here - too little to hang a rule in - and
     indenting the block instead would cost the single left edge the column
     reads on. So the mark turns horizontal and sits above the line. Flat
     amber rather than a gradient: a horizontal fade would have to be flipped
     for Arabic, and at 34px there is nothing to fade. */
  .fsig{padding-inline-start:0;padding-top:15px}
  .fsig::before{
    inset-block:0 auto;inset-inline-start:0;width:34px;height:2px;
    background:var(--amber-bright);
  }
  .foot .slogan{font-size:1.36rem}
  .g2,.g3,.g4{grid-template-columns:1fr}
  .foot-grid{grid-template-columns:1fr}
  .pager .parw{display:none}
  .review .rarw{display:none}
  .review{gap:16px;padding-right:76px}
  .review .rt{font-size:1.12rem}
  .review .gmark{width:44px;height:44px}
  .review .gmark svg{width:22px;height:22px}
}
"""

# --------------------------------------------------------------------------
# Shared markup fragments
# --------------------------------------------------------------------------
WA = "https://api.whatsapp.com/send?phone=96899245250"
WA_ICON = (
    '<svg class="wa-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2a10 10 0 0 0-8.6 '
    '15.1L2 22l5-1.3A10 10 0 1 0 12 2zm0 1.8a8.2 8.2 0 1 1-4.2 15.3l-.3-.2-3 .8.8-2.9-.2-.3A8.2 '
    '8.2 0 0 1 12 3.8zm-3.1 4c-.2 0-.5 0-.7.3-.2.3-.9.9-.9 2.1s.9 2.4 1 2.6c.1.2 1.8 2.8 4.4 '
    '3.8 2.2.9 2.6.7 3.1.7.5-.1 1.5-.6 1.7-1.2.2-.6.2-1.1.1-1.2-.1-.1-.2-.2-.5-.3l-1.7-.8c-.2-.1'
    '-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.1-.2 0-.4.1-.5l.5-.6c.2-.2.2-.3.3'
    '-.5.1-.2 0-.4 0-.5L10 8.2c-.2-.4-.4-.4-.6-.4h-.5z"/></svg>'
)
STAR = "&#10038;"

# label, href, mono-index for the mobile menu
# --------------------------------------------------------------------------
# Where each page lands once published: slug -> (path under public_html/,
# public URL). Launched 2026-08-21, taking over the English URLs from the old
# skin; the -v4 preview paths and the older -en paths 301 here (.htaccess
# section 2b). The homepage is the one page that answers on "/" rather than
# under /en/, so its file is written to the document root.
# --------------------------------------------------------------------------
# Third field is the Arabic twin, or None where the page is English-only. The
# Arabic pages already declare the English side of each pair; without this the
# pairing is one-directional and Google ignores it.
PAGES = {
    "index":      ("index.html",          "/",               "/ar/"),
    "services":   ("en/services.html",    "/en/services/",   "/services/"),
    "process":    ("en/process.html",     "/en/process/",    "/process/"),
    "about":      ("en/about.html",       "/en/about/",      "/about/"),
    "contact":    ("en/contact.html",     "/en/contact/",    "/contact/"),
    "simulators": ("en/simulators.html",  "/en/simulators/", "/simulators-ar/"),
    "demos":      ("en/demos.html",       "/en/demos/",      "/demos-ar/"),
    "checkout":   ("en/checkout.html",    "/en/checkout/",   "/checkout-ar/"),
    "order":      ("en/order.html",       "/en/order/",      "/order-ar/"),
}

# --------------------------------------------------------------------------
# The Arabic twin of the same table, added 2026-08-21 when the Arabic set was
# rebuilt on this skin. Same shape: (file under public_html/, public URL,
# the OTHER language's URL).
#
# The five core pages keep the root URLs they have been indexed on for months
# - only the skin under them changes, so nothing 301s and no equity moves. The
# four pages that are new in Arabic take the site's existing `-ar` suffix
# convention (/blog-ar/, /refund-policy-ar/), which .htaccess rule 5 already
# maps to a root file: no new rewrite rule is needed to serve them.
# --------------------------------------------------------------------------
PAGES_AR = {
    "index":      ("ar/index.html",       "/ar/",            "/"),
    "services":   ("services.html",       "/services/",      "/en/services/"),
    "process":    ("process.html",        "/process/",       "/en/process/"),
    "about":      ("about.html",          "/about/",         "/en/about/"),
    "contact":    ("contact.html",        "/contact/",       "/en/contact/"),
    "simulators": ("simulators-ar.html",  "/simulators-ar/", "/en/simulators/"),
    "demos":      ("demos-ar.html",       "/demos-ar/",      "/en/demos/"),
    "checkout":   ("checkout-ar.html",    "/checkout-ar/",   "/en/checkout/"),
    "order":      ("order-ar.html",       "/order-ar/",      "/en/order/"),
}


def pages(lang):
    return PAGES_AR if lang == "ar" else PAGES


def url(slug, lang="en"):
    """The public URL of one v4 page in one language. Every cross-page link in
    the page modules goes through this, so a URL change is a one-line edit in
    the table above rather than a grep across nine files in two languages."""
    return pages(lang)[slug][1]


ROBOTS_INDEX = ('<meta name="robots" content="index, follow, '
                'max-image-preview:large, max-snippet:-1">')
ROBOTS_NONE = '<meta name="robots" content="noindex, follow">'


def alternates(path, other, lang="en"):
    """hreflang block for one page. `path` is this page, `other` is its twin in
    the other language (or None where the page exists in one language only).

    x-default is the English side throughout: the Arabic pages already nominate
    it, and this is a Muscat business whose English pages are the ones written
    for a first-time visitor. Which of the two URLs is English therefore
    depends on which language is being rendered, hence the swap below."""
    en, ar = (other, path) if lang == "ar" else (path, other)
    out = []
    if en:
        out.append(f'<link rel="alternate" hreflang="en" href="https://aiprofitlab.io{en}">')
    if ar:
        out.append(f'<link rel="alternate" hreflang="ar" href="https://aiprofitlab.io{ar}">')
    out.append(f'<link rel="alternate" hreflang="x-default" href="https://aiprofitlab.io{en or path}">')
    return "\n".join(out)

NAV = [
    ("Home",         "/",    "01"),
    ("What I Build", "/en/services/", "02"),
    ("How It Works", "/en/process/",  "03"),
    ("About",        "/en/about/",    "04"),
    ("Contact",      "/en/contact/",  "05"),
]

# The Arabic nav, in the same order and carrying the same meanings. The labels
# are first-person singular ("ما أبنيه", "من أنا") rather than the corporate
# plural the old Arabic site used, because the whole proposition of the about
# page is that this is one operator and not an agency - "نحن" would contradict
# the page it links to. tools/v4/blog_chrome.py carries the same six labels so
# an article and a core page do not disagree in the header.
NAV_AR = [
    ("الرئيسية",     "/ar/",       "٠١"),
    ("ما أبنيه",      "/services/", "٠٢"),
    ("طريقة العمل",   "/process/",  "٠٣"),
    ("من أنا",       "/about/",    "٠٤"),
    ("تواصل معي",    "/contact/",  "٠٥"),
]

# Everything in the chrome that is a word rather than a URL. Anything a page
# module needs in both languages belongs here, not in an `if lang == "ar"`.
CHROME = {
    "en": {
        "nav": NAV, "blog": "/blog/", "blog_label": "Articles",
        "other_url": "/ar/", "other_label": "&#1593;&#1585;&#1576;&#1610;", "other_lang": "ar",
        "skip": "Skip to content", "menu": "Open menu", "whatsapp": "WhatsApp",
        "home_aria": "AI Profit Lab home", "primary": "Primary",
        "wa_intro": "Hello%20Nahid%2C%20I%20have%20a%20question%20about%20my%20business.",
        "wa_short": "Hello%20Nahid",
        "wa_aria": "Chat with Nahid on WhatsApp",
        "mfoot": "Muscat, Oman",
        "arrow": "&rarr;",
        "f_work": "The work", "f_talk": "Talk to me",
        "f_links": [("What I build", "/en/services/"), ("How it works", "/en/process/"),
                    ("Prices", "/en/services/#price"), ("Start an order", "/en/checkout/"),
                    ("Revenue leak simulator", "/en/simulators/"),
                    ("Dashboard demo", "/en/demos/#dash"), ("WhatsApp demo", "/en/demos/")],
        "f_direct": [("Contact page", "/en/contact/"), ("About Nahid", "/en/about/"),
                     ("Articles", "/blog/")],
        "follow": "Follow the work",
        "review_k": "Worked with me?", "review_t": "Leave a review on Google Maps",
        "slogan": 'Every success starts with <span class="ins">insight</span>.',
        "slogan_other": ('<p class="slogan-ar" lang="ar" dir="rtl">&#1603;&#1604; &#1606;&#1580;&#1575;&#1581; '
                         '&#1610;&#1576;&#1583;&#1571; <span class="ins">&#1576;&#1585;&#1572;&#1610;&#1577;</span></p>'),
        "legal": ('&copy; 2026 AI Profit Lab &mdash; a brand of Lotus Gulf International '
                  '(CR <span dir="ltr">1570092</span>)<br>\n      South Al Khuwair, Bousher, Muscat, '
                  'Oman &middot; Not VAT registered (TIN <span dir="ltr">2317725</span>)<br>\n      '
                  '<a href="/terms/">Terms of Service</a> &middot; '
                  '<a href="/refund-policy/">Refunds &amp; cancellation</a>\n      '
                  '&middot; <a href="/privacy/">Privacy</a>'),
        "locale": "en_OM", "dir": "ltr", "htmllang": "en",
    },
    "ar": {
        "nav": NAV_AR, "blog": "/blog-ar/", "blog_label": "المقالات",
        "other_url": "/", "other_label": "English", "other_lang": "en",
        "skip": "تخطَّ إلى المحتوى", "menu": "فتح القائمة", "whatsapp": "واتساب",
        "home_aria": "AI Profit Lab — الصفحة الرئيسية", "primary": "الرئيسية",
        # "مرحباً، لدي سؤال عن عملي."
        "wa_intro": "%D9%85%D8%B1%D8%AD%D8%A8%D8%A7%D9%8B%D8%8C%20%D9%84%D8%AF%D9%8A%20"
                    "%D8%B3%D8%A4%D8%A7%D9%84%20%D8%B9%D9%86%20%D8%B9%D9%85%D9%84%D9%8A.",
        # "مرحباً ناهد"
        "wa_short": "%D9%85%D8%B1%D8%AD%D8%A8%D8%A7%D9%8B%20%D9%86%D8%A7%D9%87%D8%AF",
        "wa_aria": "راسل ناهد على واتساب",
        "mfoot": "مسقط، سلطنة عُمان",
        "arrow": "&larr;",
        "f_work": "ما أقدّمه", "f_talk": "تواصل معي",
        "f_links": [("ما أبنيه", "/services/"), ("طريقة العمل", "/process/"),
                    ("الأسعار", "/services/#price"), ("ابدأ طلبك", "/checkout-ar/"),
                    ("حاسبة الإيرادات الضائعة", "/simulators-ar/"),
                    ("تجربة لوحة المتابعة", "/demos-ar/#dash"), ("تجربة واتساب", "/demos-ar/")],
        "f_direct": [("صفحة التواصل", "/contact/"), ("عن ناهد", "/about/"),
                     ("المقالات", "/blog-ar/")],
        "follow": "تابع العمل",
        "review_k": "تعاملت معي؟", "review_t": "اترك تقييماً على خرائط جوجل",
        "slogan": 'كل نجاح يبدأ <span class="ins">برؤية</span>',
        "slogan_other": ('<p class="slogan-ar" lang="en" dir="ltr">Every success starts with '
                         '<span class="ins">insight</span>.</p>'),
        "legal": ('&copy; 2026 AI Profit Lab &mdash; علامة تجارية تابعة لشركة Lotus Gulf International '
                  '(س.ت <span dir="ltr">1570092</span>)<br>\n      الخوير الجنوبية، بوشر، مسقط، '
                  'سلطنة عُمان &middot; غير مسجّلة في ضريبة القيمة المضافة '
                  '(الرقم الضريبي <span dir="ltr">2317725</span>)<br>\n      '
                  '<a href="/terms/">شروط الخدمة</a> &middot; '
                  '<a href="/refund-policy-ar/">الاسترداد والإلغاء</a>\n      '
                  '&middot; <a href="/privacy/">الخصوصية</a>'),
        "locale": "ar_OM", "dir": "rtl", "htmllang": "ar",
    },
}

FONTS_EN = ("https://fonts.googleapis.com/css2?family=Marcellus&family=IBM+Plex+Sans:wght@400;500;600;700"
            "&family=IBM+Plex+Mono:wght@400;500&display=swap")
# Marcellus is kept on the Arabic pages: it has no Arabic glyphs, but it is
# what the wordmark and every Latin figure caption are set in, and dropping it
# would leave those falling back to a system serif mid-page.
FONTS_AR = ("https://fonts.googleapis.com/css2?family=Marcellus&family=Markazi+Text:wght@400;500;600"
            "&family=IBM+Plex+Sans+Arabic:wght@400;500;600"
            "&family=IBM+Plex+Mono:wght@400;500&display=swap")

def head_html(lang="en"):
    """The <head> template for one language. Everything language-dependent is
    a lookup rather than a branch: direction, html lang, og:locale, the font
    stylesheet and the skip link. The placeholders build_v4.render() fills in
    are identical in both, so nothing downstream has to know the language."""
    c = CHROME[lang]
    fonts = FONTS_AR if lang == "ar" else FONTS_EN
    return """<!DOCTYPE html>
<html dir="%(dir)s" lang="%(htmllang)s">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
{{ROBOTS}}
{{ALTERNATES}}
<title>{{TITLE}}</title>
<meta name="description" content="{{DESC}}">
<link rel="canonical" href="https://aiprofitlab.io{{PATH}}">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">

<meta property="og:type" content="website">
<meta property="og:title" content="{{TITLE}}">
<meta property="og:description" content="{{DESC}}">
<meta property="og:url" content="https://aiprofitlab.io{{PATH}}">
<meta property="og:image" content="https://aiprofitlab.io/og-aiprofitlab-2026.jpg">
<meta property="og:locale" content="%(locale)s">
<meta name="twitter:card" content="summary_large_image">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<!-- Non-blocking font load: a plain stylesheet link costs a render-blocking
     round trip to fonts.googleapis.com. display=swap paints fallback text
     immediately and swaps when the webfont lands. -->
<link rel="preload" as="style" href="%(fonts)s">
<link rel="stylesheet" media="print" onload="this.media='all'" href="%(fonts)s">
<noscript><link rel="stylesheet" href="%(fonts)s"></noscript>
{{HEADEXTRA}}
<!-- Sets .js before first paint so the reveal styles apply only when there is
     JS to un-apply them. Without it, a no-JS visitor gets a blank page. -->
<script>document.documentElement.className+=" js"</script>

<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-SLR9GD3MJP"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments)}gtag('js',new Date());gtag('config','G-SLR9GD3MJP');</script>

<style>{{CSS}}</style>
{{SCHEMA}}
</head>
<body>
<a class="skip" href="#main">%(skip)s</a>
""" % dict(c, fonts=fonts)


# Kept as a module constant because it is what the English build has always
# read. It is now one call of the function above rather than a second copy.
HEAD = head_html("en")


def header(active_href, lang="en"):
    """Fixed header + the full-screen mobile menu."""
    c = CHROME[lang]
    nav = c["nav"]
    links = []
    for label, href, _ in nav[1:]:
        cur = ' aria-current="page"' if href == active_href else ""
        links.append(f'<a class="lnk" href="{href}"{cur}>{label}</a>')
    cur = ' aria-current="page"' if active_href == c["blog"] else ""
    links.append(f'<a class="lnk" href="{c["blog"]}"{cur}>{c["blog_label"]}</a>')
    links.append(f'<a class="lnk" href="{c["other_url"]}" lang="{c["other_lang"]}">{c["other_label"]}</a>')

    m = []
    for label, href, n in nav:
        mcur = ' aria-current="page"' if href == active_href else ""
        m.append(f'<a href="{href}"{mcur}><em>{n}</em>{label}</a>')
    m.append(f'<a href="{c["blog"]}"{cur}><em>{"٠٦" if lang == "ar" else "06"}</em>{c["blog_label"]}</a>')

    return f"""<header class="top" id="top">
  <a href="{nav[0][1]}" aria-label="{c["home_aria"]}">
    <img class="mark" src="/assets/brand/wordmark-primary.svg" alt="AI Profit Lab" width="160" height="28">
  </a>
  <nav class="nav" aria-label="{c["primary"]}">
    {chr(10).join('    ' + l for l in links)}
    <a class="top-wa" href="{WA}&text={c["wa_intro"]}" target="_blank" rel="noopener" aria-label="{c["wa_aria"]}">{WA_ICON}<span>{c["whatsapp"]}</span></a>
    <button class="burger" id="burger" aria-label="{c["menu"]}" aria-expanded="false" aria-controls="mmenu"><i></i></button>
  </nav>
</header>
<div class="mmenu" id="mmenu" aria-hidden="true">
  {chr(10).join('  ' + l for l in m)}
  <p class="mfoot">hello@aiprofitlab.io &middot; <span dir="ltr">+968 9924 5250</span><br>{c["mfoot"]}</p>
</div>
"""


def pager(label, title, href, lang="en"):
    c = CHROME[lang]
    aria = "الصفحة التالية" if lang == "ar" else "Next page"
    return f"""<nav class="pager" aria-label="{aria}">
  <div class="wrap"><a href="{href}">
    <span><span class="pl">{label}</span><span class="pt">{title}</span></span>
    <span class="parw" aria-hidden="true">{c["arrow"]}</span>
  </a></div>
</nav>
"""


# --------------------------------------------------------------------------
# Footer marks. Every glyph is an inline 24x24 path on fill:currentColor so the
# tile can recolour it on hover; the Google G is the one exception and keeps its
# official four colours, which is also the only reason it reads as Google at
# 26px on a dark ground.
# --------------------------------------------------------------------------
GOOGLE_G = (
    '<svg viewBox="0 0 48 48" aria-hidden="true">'
    '<path fill="#4285F4" d="M45.12 24.5c0-1.56-.14-3.06-.4-4.5H24v8.51h11.84c-.51 2.75-2.06 '
    '5.08-4.39 6.64v5.52h7.11c4.16-3.83 6.56-9.47 6.56-16.17z"/>'
    '<path fill="#34A853" d="M24 46c5.94 0 10.92-1.97 14.56-5.33l-7.11-5.52c-1.97 1.32-4.49 '
    '2.1-7.45 2.1-5.73 0-10.58-3.87-12.31-9.07H4.34v5.7C7.96 41.07 15.4 46 24 46z"/>'
    '<path fill="#FBBC05" d="M11.69 28.18C11.25 26.86 11 25.45 11 24s.25-2.86.69-4.18v-5.7H4.34C2.85 '
    '17.09 2 20.45 2 24s.85 6.91 2.34 9.88l7.35-5.7z"/>'
    '<path fill="#EA4335" d="M24 10.75c3.23 0 6.13 1.11 8.41 3.29l6.31-6.31C34.91 4.18 29.93 2 24 '
    '2 15.4 2 7.96 6.93 4.34 14.12l7.35 5.7c1.73-5.2 6.58-9.07 12.31-9.07z"/></svg>'
)

STAR_SVG = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 17.3l-6.18 3.75 1.64-7.03L2 '
            '9.24l7.19-.61L12 2l2.81 6.63 7.19.61-5.46 4.78 1.64 7.03z"/></svg>')

MAIL_ICON = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 '
             '18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg>')

_WA_PATH = ('M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm0 1.8a8.2 8.2 0 1 1-4.2 '
            '15.3l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 0 1 12 3.8zm-3.1 4c-.2 0-.5 0-.7.3-.2.3-.9.9-.9 '
            '2.1s.9 2.4 1 2.6c.1.2 1.8 2.8 4.4 3.8 2.2.9 2.6.7 3.1.7.5-.1 1.5-.6 1.7-1.2.2-.6.2-1.1'
            '.1-1.2-.1-.1-.2-.2-.5-.3l-1.7-.8c-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1a6.7 6.7 0 0 '
            '1-3.3-2.9c-.1-.2 0-.4.1-.5l.5-.6c.2-.2.2-.3.3-.5.1-.2 0-.4 0-.5L10 8.2c-.2-.4-.4-.4-.6'
            '-.4h-.5z')

WA_SMALL = f'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="{_WA_PATH}"/></svg>'

# label, href, brand colour used for the hover fill, glyph path
SOCIALS = [
    ("WhatsApp", WA + "&text=Hello%20Nahid", "#1FAF5E", _WA_PATH),
    ("LinkedIn", "https://www.linkedin.com/in/nahid-aby", "#0A66C2",
     "M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238"
     "-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75"
     ".79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3"
     "v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"),
    ("YouTube", "https://www.youtube.com/@AI_for_Managers", "#FF0000",
     "M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 "
     "8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484"
     "-8.549-4.385-8.816zm-10.615 12.816v-8l8 3.993-8 4.007z"),
    ("Facebook", "https://www.facebook.com/profile.php?id=61584870364473", "#1877F2",
     "M9 8h-3v4h3v12h5v-12h3.642l.358-4h-4v-1.667c0-.955.192-1.333 1.115-1.333h2.885v-5h-3.808c-3.596"
     " 0-5.192 1.583-5.192 4.615v3.385z"),
]

GOOGLE_REVIEW = "https://g.page/r/CYPlrz58-k0DEAI/review"


# --------------------------------------------------------------------------
# Entity graph
# --------------------------------------------------------------------------
# One Organization node, given a stable @id and emitted on every page, with
# every other node on the page referencing it. This is how a search engine
# consolidates twenty-two URLs into one entity, and it matters more here than
# it usually would: "AI Profit Lab" collides with an automated-trading brand,
# and `sameAs` is the only thing on the page that says which one this is.
#
# The v4 rebuild had dropped all of it - `grep sameAs tools/v4/` returned
# nothing, while 187 retired pages still carried the profiles.
SITE = "https://aiprofitlab.io"
ORG_ID = SITE + "/#organization"
SITE_ID = SITE + "/#website"

# openingHours is deliberately absent: there are no published business hours
# to state, and inventing them would be worse than omitting the property.
ORG_NODE = """{
    "@type":"ProfessionalService",
    "@id":"%(org)s",
    "name":"AI Profit Lab",
    "description":"Done-for-you AI automation for trading and distribution SMEs in Oman and the GCC.",
    "url":"%(site)s/",
    "email":"hello@aiprofitlab.io",
    "telephone":"+968 9924 5250",
    "slogan":"Every success starts with insight",
    "logo":{"@type":"ImageObject","url":"%(site)s/assets/brand/wordmark-primary.svg","width":1600,"height":274},
    "image":"%(site)s/og-aiprofitlab-2026.jpg",
    "areaServed":[{"@type":"Country","name":"Oman"}],
    "address":{"@type":"PostalAddress","addressLocality":"Bousher","addressRegion":"Muscat","addressCountry":"OM","streetAddress":"South Al Khuwair"},
    "geo":{"@type":"GeoCoordinates","latitude":23.5803,"longitude":58.4310},
    "parentOrganization":{"@type":"Organization","name":"Lotus Gulf International","identifier":"CR 1570092"},
    "founder":{"@type":"Person","name":"Nahid Abyari"},
    "priceRange":"OMR 950 - OMR 2200",
    "sameAs":["https://www.linkedin.com/in/nahid-aby","https://www.youtube.com/@AI_for_Managers","https://www.facebook.com/profile.php?id=61584870364473"]
  }""" % {"org": ORG_ID, "site": SITE}

WEBSITE_NODE = """{
    "@type":"WebSite",
    "@id":"%(site_id)s",
    "url":"%(site)s/",
    "name":"AI Profit Lab",
    "inLanguage":["en","ar"],
    "publisher":{"@id":"%(org)s"}
  }""" % {"site_id": SITE_ID, "site": SITE, "org": ORG_ID}


NODE_SEP = "$$SPLIT$$"


def graph(nodes):
    """One @graph per page: the shared Organization plus the page's own nodes.

    Page modules keep authoring a single self-contained node with its own
    @context; that context is stripped on the way in, because a graph carries
    exactly one at the top.
    """
    import re as _re
    flat = []
    for n in nodes:
        # A page with more than one node of its own separates them with this
        # marker rather than hand-assembling a graph it cannot see the rest of.
        flat.extend((n or "").split(NODE_SEP))
    out = []
    for n in flat:
        n = (n or "").strip()
        if not n:
            continue
        n = _re.sub(r'"@context"\s*:\s*"https://schema\.org"\s*,?\s*', "", n, count=1)
        out.append(n.strip())
    return ('{\n  "@context":"https://schema.org",\n  "@graph":[\n  '
            + ",\n  ".join(out) + "\n  ]\n}")


def _socials():
    li = []
    for label, href, colour, path in SOCIALS:
        li.append(
            f'    <li><a href="{href}" style="--sc:{colour}" target="_blank" rel="noopener" '
            f'aria-label="AI Profit Lab on {label}"><svg viewBox="0 0 24 24" aria-hidden="true">'
            f'<path d="{path}"/></svg></a></li>'
        )
    return "\n".join(li)


def footer(lang="en"):
    """Site footer. Same four blocks in both languages; every word and every
    href comes out of CHROME, so an Arabic footer cannot quietly keep an
    English link the way a hand-translated copy would."""
    c = CHROME[lang]
    work = "\n          ".join('<li><a href="%s">%s</a></li>' % (href, label)
                               for label, href in c["f_links"])
    direct = "\n          ".join('<li><a href="%s">%s</a></li>' % (href, label)
                                 for label, href in c["f_direct"])
    return f"""<footer class="foot">
  <div class="wrap">
    <div class="foot-grid">

      <div class="foot-brand">
        <img class="fmark" src="/assets/brand/wordmark-reversed.svg" alt="AI Profit Lab" width="170" height="29">
        <div class="fsig">
          <p class="slogan">{c["slogan"]}</p>
          <span class="sig-beat" aria-hidden="true"></span>
          {c["slogan_other"]}
        </div>
        <div class="soc-wrap">
          <h4 class="soc-h">{c["follow"]}</h4>
          <ul class="socials">
{_socials()}
          </ul>
        </div>
      </div>

      <nav class="fcol" aria-label="{c["f_work"]}">
        <h4>{c["f_work"]}</h4>
        <ul>
          {work}
        </ul>
      </nav>

      <nav class="fcol" aria-label="{c["f_talk"]}">
        <h4>{c["f_talk"]}</h4>
        <ul class="direct">
          <li><a href="{WA}&text={c["wa_short"]}">{WA_SMALL}<span dir="ltr">+968 9924 5250</span></a></li>
          <li><a href="mailto:hello@aiprofitlab.io">{MAIL_ICON}hello@aiprofitlab.io</a></li>
        </ul>
        <ul>
          {direct}
        </ul>
      </nav>

    </div>

    <a class="review" href="{GOOGLE_REVIEW}" target="_blank" rel="noopener">
      <span class="gmark" aria-hidden="true">{GOOGLE_G}</span>
      <span class="rbody">
        <span class="stars" aria-hidden="true">{STAR_SVG * 5}</span>
        <span class="rk">{c["review_k"]}</span>
        <span class="rt">{c["review_t"]}</span>
      </span>
      <span class="rarw" aria-hidden="true">{c["arrow"]}</span>
    </a>

    <p class="legal">
      {c["legal"]}
    </p>
  </div>
</footer>
"""


FOOTER = footer("en")

# --------------------------------------------------------------------------
# Motion kit — one IIFE, shared by every page.
# --------------------------------------------------------------------------
MOTION_JS = """
/* ---------------------------------------------------------------------------
   Shared page behaviour: sticky header state, mobile menu, scroll reveals,
   SVG draw-in, and count-up numbers. Everything degrades to "visible and
   static" when JS or IntersectionObserver is missing, and is skipped wholesale
   under prefers-reduced-motion.
--------------------------------------------------------------------------- */
(function(){
  "use strict";
  var root = document.documentElement;
  var reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* header ---------------------------------------------------------------- */
  var top = document.getElementById("top");
  function onScroll(){ top.classList.toggle("solid", scrollY > 40); }
  onScroll(); addEventListener("scroll", onScroll, {passive:true});

  /* mobile menu ----------------------------------------------------------- */
  var burger = document.getElementById("burger"), mm = document.getElementById("mmenu");
  if (burger && mm){
    var setMenu = function(open){
      root.classList.toggle("menu-open", open);
      burger.setAttribute("aria-expanded", open ? "true" : "false");
      mm.setAttribute("aria-hidden", open ? "false" : "true");
      document.body.style.overflow = open ? "hidden" : "";
    };
    burger.addEventListener("click", function(){ setMenu(!root.classList.contains("menu-open")); });
    mm.addEventListener("click", function(e){ if (e.target.tagName === "A") setMenu(false); });
    addEventListener("keydown", function(e){ if (e.key === "Escape") setMenu(false); });
  }

  /* auto-tag the standard blocks so pages don't have to repeat class="rv" --- */
  document.querySelectorAll("section:not(.cine) .eyebrow, section:not(.cine) .lede").forEach(function(el){ el.classList.add("rv"); });
  /* The wipe needs an inner block to move inside the heading's own overflow,
     so the script supplies one rather than every page repeating it. */
  document.querySelectorAll("section:not(.cine) h2, section:not(.cine) .h1").forEach(function(el){
    var inner = document.createElement("span");
    inner.className = "wi";
    while (el.firstChild) inner.appendChild(el.firstChild);
    el.appendChild(inner);
    el.classList.add("rvw");
  });
  /* [data-stagger] children reveal in sequence, capped so a long grid does not
     end up waiting a second and a half for its last card. */
  document.querySelectorAll("[data-stagger]").forEach(function(g){
    Array.prototype.forEach.call(g.children, function(c,i){
      c.classList.add("rv"); c.style.setProperty("--d", Math.min(i*0.075, 0.45) + "s");
    });
  });

  /* SVG draw-in: measure each stroked path so the dash length is its own
     length, not a guessed constant that under- or over-shoots. */
  document.querySelectorAll(".drawn").forEach(function(svg){
    svg.querySelectorAll("path,line,polyline,circle,rect.dr").forEach(function(p,i){
      var len = 1000;
      try { if (p.getTotalLength) len = Math.ceil(p.getTotalLength()) || 1000; } catch(e){}
      p.style.setProperty("--len", len);
      p.style.setProperty("--d", Math.min(i*0.09, 0.7) + "s");
    });
  });

  var els = document.querySelectorAll(".rv,.rvw,.drawn,[data-count]");
  function showAll(){ els.forEach(function(e){ e.classList.add("vis"); countUp(e, true); }); }
  if (reduce || !("IntersectionObserver" in window)){ showAll(); return; }

  /* count-up -------------------------------------------------------------- */
  function countUp(el, instant){
    var raw = el.getAttribute("data-count"); if (raw === null || el.dataset.counted) return;
    el.dataset.counted = "1";
    var to = parseFloat(raw), pre = el.getAttribute("data-pre") || "", post = el.getAttribute("data-post") || "";
    var dp = parseInt(el.getAttribute("data-dp") || "0", 10);
    if (instant){ el.textContent = pre + to.toFixed(dp) + post; return; }
    var t0 = 0, dur = 1250;
    (function step(now){
      if (!t0) t0 = now;
      var k = Math.min((now - t0)/dur, 1);
      var e = 1 - Math.pow(1 - k, 3);                       /* easeOutCubic */
      var v = to * e;
      el.textContent = pre + (dp ? v.toFixed(dp) : Math.round(v).toLocaleString("en-US")) + post;
      if (k < 1) requestAnimationFrame(step);
    })(0);
  }

  var io = new IntersectionObserver(function(entries){
    entries.forEach(function(en){
      if (!en.isIntersecting) return;
      en.target.classList.add("vis"); countUp(en.target, false); io.unobserve(en.target);
    });
  }, {threshold:0.12, rootMargin:"0px 0px -60px 0px"});
  els.forEach(function(e){ io.observe(e); });
})();
"""

# {{AIDEN}} is the Aiden chat widget tag, filled in by build_v4.render(). It is
# a placeholder rather than a fixed line because article pages do not carry the
# widget - see AIDEN_TAG and META["aiden"].
TAIL = """<script>{{JS}}</script>
{{AIDEN}}</body>
</html>
"""

# {{VER}} is the widget's content hash, filled in by build_v4.render() from
# tools/aiden_version.py. Without it an edited widget never reaches a returning
# visitor: .htaccess serves .js as immutable for a year on a stable filename.
AIDEN_TAG = '<script defer src="/js/aiden-chat.js?v={{VER}}"></script>\n'

SKIP_CSS = """
.skip{position:absolute;left:-9999px;top:0;z-index:200;background:var(--teal-950);color:var(--cream);
  padding:12px 20px;border-radius:0 0 8px 0;font-family:var(--mono);font-size:.85rem;text-decoration:none}
.skip:focus{left:0}
"""
