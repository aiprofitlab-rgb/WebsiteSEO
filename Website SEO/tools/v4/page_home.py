#!/usr/bin/env python3
"""Homepage body: the cinematic hero (ported) plus eight visual sections.

Editorial brief from Nahid, 2026-08-20 - the page is aimed at one state of mind,
not at a feature list. The visitor is a profitable owner who privately thinks:
"I know what I'm doing and I'm making money. But what is this AI everyone talks
about? Does it actually touch my business? Will I fall behind? Can I spend less
and grow with it? I'm afraid of technology and I don't want to learn it - do I
have to?"

So the page answers those questions in that order, and answers them with things
to LOOK AT rather than paragraphs to read:

  S2  the noise, then the five questions      -> names the fear, defuses it
  S3  the reply race                          -> "yes, it touches your business"
  S4  four sliders                            -> "here is what it costs YOU"
  S5  the morning message + three zeros       -> "no, you never learn anything"
  S6  the staircase                           -> what actually gets built
  S7  two live demos                          -> proof he can click
  S8  168 hours + the cost-of-growth chart    -> spend less, serve more
  S9  the named promise                       -> the money is not at risk

Prose budget: no block runs longer than four lines, and every section carries a
diagram, a chart, a control or a screenshot as its centre of gravity.
"""
import json as _json
import re
from kit import WA, WA_ICON, STAR

# --------------------------------------------------------------------------
# S2 - the buzzword cloud. word, left%, top%, rem, opacity, drift seconds.
# Positions deliberately avoid the middle band (roughly 26-74% across, 34-66%
# down) where the answer card sits, so nothing important is ever occluded.
# `s` marks the ones that survive on a phone - the rest are dropped, because at
# 360px the full set collides into an unreadable mat.
# --------------------------------------------------------------------------
BUZZ = [
    # word, left%, top%, rem, opacity, drift seconds, phone position or None
    ("LLM",              11, 13, 1.55, .34, 13, (18,  9)),
    ("prompt engineering", 37, 7, 1.00, .19, 17, None),
    ("RAG",              63, 13, 1.70, .30, 15, (68,  9)),
    ("vector database",  85, 24, 0.95, .18, 19, None),
    ("fine-tuning",       9, 35, 1.15, .25, 16, None),
    ("transformers",     90, 45, 1.20, .22, 14, None),
    ("tokens",           15, 55, 1.45, .28, 18, (72, 91)),
    ("hallucination",    85, 58, 1.05, .20, 15, None),
    ("agents",           11, 76, 1.60, .32, 13, (24, 91)),
    ("embeddings",       41, 90, 1.00, .19, 20, None),
    ("inference",        67, 84, 1.30, .24, 16, (46, 17)),
    ("neural networks",  88, 76, 0.95, .17, 18, None),
    ("chain-of-thought", 27, 24, 0.95, .17, 21, None),
    ("GPU clusters",     80, 20, 1.05, .21, 17, None),
    ("copilots",         20, 88, 1.20, .23, 14, None),
    ("multimodal",       55, 94, 1.00, .18, 19, None),
]

# S2 - number, the question in his own words, the answer in one breath.
QUESTIONS = [
    ("01", "Is this real, or is it hype?",
     "For a trading business it is one thing: a machine that answers buyers in "
     "Arabic and English at two in the morning. <b>That part works today.</b>"),
    ("02", "Will it actually touch my business?",
     "Only through the supplier who replied to your buyer <b>while you were at "
     "dinner</b>. Nothing else about AI needs to concern you this year."),
    ("03", "Do I have to learn it?",
     "No. You never open it, never log in, never type a prompt. "
     "<b>It reports to your WhatsApp in one sentence.</b>"),
    ("04", "Will it break the way I work now?",
     "Nothing about your day changes. It is built <b>beside</b> your business, "
     "not on top of it &mdash; the phone, the prices and the people stay exactly as they are."),
    ("05", "Can it really make me spend less?",
     "It is paid <b>once</b>, not every month. It takes no visa, no leave and no "
     "sick days, and it costs the same whether one buyer writes tonight or forty do."),
]

# S3 - the reply race. who, the time on the clock, bar width, tone, the note.
# Bar length is RANKED, not linear: 40 seconds against 14 hours on a true scale
# is a bar you cannot see. The note under the chart says so.
RACE = [
    ("You, tonight",        "14 h 25 m", 100,  "bad",  "He read your price at 8:12am. He had ordered at 10:03pm.", ""),
    ("The second supplier", "2 h 04 m",   31,  "mid",  "Also too late. He never even got a reply.", ""),
    ("The supplier who won", "4 min",      9,  "good", "Not cheaper. Not better. Awake.", "Got the order"),
    ("You, with the system", "40 sec",   3.5,  "best", "The quote goes out. The lead lands on your phone.", "Answered first"),
]

CSS = """
/* The word cloud is decorative markup that carries real meaning, so the meaning
   is repeated once in text for anyone who cannot see it. */
.sr-only{
  position:absolute;width:1px;height:1px;margin:-1px;padding:0;overflow:hidden;
  clip:rect(0 0 0 0);clip-path:inset(50%);white-space:nowrap;border:0;
}

/* ==================================================== S2 - the noise cloud */
.buzz{
  position:relative;overflow:hidden;border-radius:20px;border:1px solid var(--line-dark);
  height:clamp(360px,44vw,480px);margin:clamp(26px,4vw,44px) 0 0;
  background:radial-gradient(120% 90% at 50% 50%,rgba(15,110,86,.30),transparent 68%);
}
.buzz b{
  position:absolute;font-family:var(--mono);font-weight:400;white-space:nowrap;color:var(--cream);
  left:var(--x);top:var(--y);font-size:var(--s);opacity:var(--o);
  /* the centring translate lives INSIDE the keyframes, or the animation would
     overwrite it on the first frame and every word would jump down-right */
  transform:translate(-50%,-50%);
  animation:drift var(--t) ease-in-out infinite alternate;animation-delay:var(--dl);
}
@keyframes drift{from{transform:translate(-50%,-50%)}to{transform:translate(-50%,calc(-50% - 20px))}}
.buzz-card{
  position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:min(580px,84%);
  text-align:center;border:1px solid rgba(232,201,143,.5);border-radius:18px;
  padding:clamp(26px,3.6vw,40px);backdrop-filter:blur(10px);
  /* a shade lighter than the section it sits on, so it reads as a card lying
     over the noise rather than as a hole cut out of it */
  background:linear-gradient(180deg,rgba(12,66,52,.97),rgba(7,43,34,.98));
  box-shadow:0 44px 90px -44px #000;
}
.buzz-card .k{
  font-family:var(--mono);font-size:.8rem;letter-spacing:.16em;text-transform:uppercase;
  color:var(--amber-pale);margin:0 0 14px;
}
.buzz-card p.q{
  font-family:var(--display);font-size:clamp(1.4rem,3.2vw,2.15rem);line-height:1.25;
  color:var(--cream);margin:0;
}
.buzz-card p.q em{font-style:normal;color:var(--amber-bright)}

/* ============================================== S2 - the five real questions */
.qa{border-top:1px solid var(--line-dark);margin-top:clamp(30px,4vw,50px)}
.qa-row{
  display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.02fr);align-items:center;
  gap:clamp(14px,3vw,52px);padding:clamp(22px,3vw,32px) 0;border-bottom:1px solid var(--line-dark);
  transition:background .35s var(--ease);
}
.qa-row:hover{background:rgba(241,239,232,.03)}
.qa-q{display:flex;align-items:baseline;gap:clamp(12px,1.6vw,20px)}
.qa-n{font-family:var(--mono);font-size:.78rem;letter-spacing:.14em;color:var(--amber-bright);flex:none}
.qa-q p{
  font-family:var(--display);font-size:clamp(1.28rem,2.4vw,1.9rem);line-height:1.24;
  color:var(--cream);margin:0;
}
.qa-a{
  margin:0;padding-left:clamp(15px,2vw,24px);border-left:2px solid var(--amber);
  color:rgba(241,239,232,.78);font-size:1rem;line-height:1.62;
}
.qa-a b{color:var(--cream);font-weight:500}

/* ======================================================= S3 - the reply race */
.race{margin-top:clamp(28px,4vw,48px);display:grid;gap:clamp(20px,2.6vw,30px)}
.lane-head{display:flex;align-items:baseline;justify-content:space-between;gap:14px;margin-bottom:9px}
/* .lane-who is itself a flex row so that on a narrow screen the "got the order"
   chip wraps under the supplier name instead of pushing the time onto its own
   line, where space-between would strand it against the left edge. */
.lane-who{display:flex;flex-wrap:wrap;align-items:center;gap:10px;min-width:0;font-size:1.04rem;color:var(--teal-950)}
.lane-when{font-family:var(--mono);font-variant-numeric:tabular-nums;font-size:1rem;color:var(--muted);white-space:nowrap}
.lane-track{height:14px;border-radius:99px;background:var(--panel-2);overflow:hidden}
.lane-track i{
  display:block;height:100%;width:var(--w);border-radius:99px;background:var(--tone);
  transform:scaleX(0);transform-origin:0 50%;transition:transform 1.1s var(--ease);
  transition-delay:var(--d,0s);
}
.rv.vis .lane-track i,html:not(.js) .lane-track i{transform:none}
.lane-note{margin:9px 0 0;font-size:.95rem;color:var(--muted)}
.lane.bad{--tone:var(--alert)}
.lane.mid{--tone:#B9AE93}
.lane.good{--tone:var(--teal)}
.lane.best{--tone:var(--wa)}
.lane.best .lane-who,.lane.best .lane-when{color:var(--teal-950);font-weight:500}
.lane.best .lane-track{background:rgba(31,175,94,.16)}
.lane-flag{
  display:inline-flex;align-items:center;gap:7px;font-family:var(--mono);
  font-size:.7rem;letter-spacing:.12em;text-transform:uppercase;color:var(--teal-950);
  background:var(--amber-pale);border-radius:99px;padding:4px 10px;white-space:nowrap;
}
.lane.best .lane-flag{background:var(--wa);color:#fff}
.race-foot{
  display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:14px;
  margin-top:clamp(24px,3vw,36px);padding-top:20px;border-top:1px solid var(--line);
}
.race-kick{font-family:var(--display);font-size:clamp(1.2rem,2.4vw,1.7rem);color:var(--teal-950);margin:0}
.race-note{font-family:var(--mono);font-size:.76rem;letter-spacing:.06em;color:var(--muted);margin:0;max-width:38ch}

/* ================================================== S4 - the four sliders */
.leak-grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:clamp(20px,3vw,40px);align-items:stretch}
.panelcard{
  background:rgba(241,239,232,.05);border:1px solid var(--line-dark);
  border-radius:16px;padding:clamp(24px,3vw,36px);
}
.panelcard h3{color:var(--cream);margin:0 0 22px;font-size:1.4rem}
.fieldrow{margin-bottom:22px}
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
  color:rgba(241,239,232,.55);margin:0 0 4px;
}
.bignum{
  display:block;font-family:var(--display);font-size:clamp(2.8rem,6.4vw,4.4rem);line-height:1;
  color:var(--amber-bright);font-variant-numeric:tabular-nums;
}
.payback{margin:20px 0 0;color:rgba(241,239,232,.82);font-size:1.02rem}
.payback b{color:var(--cream)}
.assume{margin:14px 0 0;font-size:.86rem;line-height:1.6;color:rgba(241,239,232,.5)}

/* ============================== S5 - the morning message and the three zeros */
.touch-grid{display:grid;grid-template-columns:minmax(0,.9fr) minmax(0,1.1fr);gap:clamp(30px,5vw,68px);align-items:center}
.phone{
  width:min(320px,100%);margin-inline:auto;padding:9px;border-radius:36px;
  background:var(--teal-950);border:1px solid var(--teal-900);
  box-shadow:0 46px 80px -46px rgba(7,43,34,.75);
}
.phone-in{border-radius:28px;overflow:hidden;background:#E9E3D6}
.phone-bar{display:flex;align-items:center;gap:11px;background:var(--teal-900);padding:13px 15px}
.phone-av{
  width:34px;height:34px;border-radius:50%;flex:none;background:var(--amber);color:var(--teal-950);
  display:grid;place-items:center;font-family:var(--mono);font-size:.76rem;font-weight:500;
}
.phone-nm{font-size:.92rem;color:var(--cream);line-height:1.25}
.phone-nm span{
  display:block;font-family:var(--mono);font-size:.64rem;letter-spacing:.12em;
  text-transform:uppercase;color:var(--amber-pale);
}
.phone-body{padding:18px 15px 24px}
.bub{
  background:#fff;border-radius:3px 15px 15px 15px;padding:15px 16px;
  box-shadow:0 3px 10px -4px rgba(7,43,34,.35);font-size:.92rem;line-height:1.6;color:var(--ink);
}
.bub p{margin:0 0 10px}
.bub ul{list-style:none;margin:0 0 10px;padding:0}
.bub li{position:relative;padding-left:18px;margin-bottom:5px}
.bub li::before{content:"";position:absolute;left:2px;top:.62em;width:6px;height:6px;border-radius:50%;background:var(--teal)}
.bub li.act::before{background:var(--alert)}
.bub b{color:var(--teal-950);font-weight:600}
.bub .act-l{color:var(--alert);font-weight:600}
.bub .tme{display:block;text-align:right;font-family:var(--mono);font-size:.62rem;color:var(--muted);margin-top:2px}
.phone-cap{
  text-align:center;font-family:var(--mono);font-size:.72rem;letter-spacing:.1em;text-transform:uppercase;
  color:var(--muted);margin:16px 0 0;
}
.zeros{list-style:none;margin:0;padding:0;display:grid;gap:clamp(12px,1.8vw,18px)}
.zeros li{
  display:flex;align-items:center;gap:clamp(16px,2.4vw,28px);
  border-bottom:1px solid var(--line);padding-bottom:clamp(12px,1.8vw,18px);
}
.zeros li:last-child{border-bottom:0;padding-bottom:0}
/* Mono, not the display serif: Marcellus's zero is a wide open oval that at
   5rem reads as a ring or a bullet, not as the number nought - which is the
   entire point of the row. Plex Mono's zero is unmistakable. */
.zeros .z{
  font-family:var(--mono);font-weight:500;font-size:clamp(2.9rem,6.6vw,4.4rem);
  line-height:.9;color:var(--amber);flex:none;min-width:1.1em;text-align:center;
}
.zeros .zt{margin:0;font-size:clamp(1.05rem,1.8vw,1.28rem);color:var(--teal-950);line-height:1.3}
.zeros .zt small{display:block;font-size:.88rem;color:var(--muted);margin-top:3px;line-height:1.5}
.touch-kick{
  margin:clamp(28px,4vw,46px) 0 0;font-family:var(--display);
  font-size:clamp(1.35rem,3vw,2.1rem);line-height:1.3;color:var(--teal-950);text-align:center;
}
.touch-kick em{font-style:normal;color:var(--amber-text)}

/* ----------------------------------------------------------- S6 staircase */
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

/* --------------------------------------------------------- S7 proof tiles */
.tiles{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:clamp(16px,2.2vw,26px)}
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
.tile-wide{grid-column:1/-1;display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:center;gap:24px;padding:clamp(24px,3vw,36px)}
.tile-wide h3{margin:0 0 8px}
.tile-wide .cap{padding:0}

/* ------------------------------------------------- S8 hours + growth chart */
.hours-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:clamp(18px,3vw,34px)}
.hcard{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:clamp(22px,3vw,32px)}
.hcard.win{background:var(--teal-950);border-color:var(--teal-900);color:var(--cream)}
.hcard h3{margin:0 0 4px;font-size:1.4rem}
.hcard.win h3{color:var(--cream)}
.hcard .sub{font-family:var(--mono);font-size:.82rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin:0 0 22px}
.hcard.win .sub{color:var(--amber-pale)}
/* 24 columns x 7 rows: one row per day, one cell per hour. Transposed from
   7x24 because 24 narrow columns keep the cells small enough to read as a
   texture; at 7 columns each cell was ~40px and the block ran a metre tall. */
.hgrid{display:grid;grid-template-columns:repeat(24,minmax(0,1fr));gap:2px;margin-bottom:20px}
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
.growth{
  margin-top:clamp(18px,3vw,34px);background:var(--white);border:1px solid var(--line);border-radius:16px;
  padding:clamp(22px,3vw,34px);display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr);
  gap:clamp(20px,3.4vw,46px);align-items:center;
}
.growth svg{width:100%;height:auto;display:block}
.growth h3{margin:0 0 10px;font-size:clamp(1.3rem,2.4vw,1.75rem)}
.growth p{margin:0;color:var(--muted);font-size:1rem}

/* ------------------------------------------------------------- S9 promise */
.promise-grid{display:grid;grid-template-columns:auto minmax(0,1fr);gap:clamp(24px,4vw,52px);align-items:center}
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

/* ---------------------------------------------------------- S10 explore rail */
.rail{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:clamp(14px,1.8vw,22px)}
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

/* ------------------------------------------------------------ breakpoints */
@media (max-width:960px){
  .leak-grid,.hours-grid,.tiles,.touch-grid,.growth{grid-template-columns:minmax(0,1fr)}
  .rail{grid-template-columns:repeat(2,minmax(0,1fr))}
  .promise-grid{grid-template-columns:minmax(0,1fr);text-align:left}
  .tile-wide{grid-template-columns:minmax(0,1fr)}
  .qa-row{grid-template-columns:minmax(0,1fr);gap:14px}
  .qa-a{margin-left:calc(2ch + 20px)}
}
@media (max-width:760px){
  .stair{display:none}
  .buzz{height:clamp(330px,74vw,400px)}
  .buzz b.o{display:none}
  .buzz b{left:var(--xs);top:var(--ys);font-size:calc(var(--s) * .78)}
}
@media (max-width:560px){
  .rail{grid-template-columns:minmax(0,1fr)}
  .qa-a{margin-left:0}
}
"""


def _hours_grid(on_test):
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


def _buzz():
    """The cloud of words he keeps hearing and does not want to learn.

    Two position sets, not one. On a phone the answer card is 84% of the box,
    so the only clear ground is a thin band above it and another below - words
    left on their desktop coordinates get bisected by the card edge or clipped
    by the box, which reads as a broken layout rather than as noise.
    """
    out = []
    for i, (word, x, y, size, op, dur, phone) in enumerate(BUZZ):
        cls = "" if phone else ' class="o"'
        pos = f"--xs:{phone[0]}%;--ys:{phone[1]}%;" if phone else ""
        out.append(
            f'    <b{cls} style="--x:{x}%;--y:{y}%;{pos}--s:{size}rem;--o:{op};'
            f'--t:{dur}s;--dl:-{i * 1.7:.1f}s">{word}</b>'
        )
    return "\n".join(out)


PAGE_URL = 'https://aiprofitlab.io/'
LANG = 'en'
def _faq_schema():
    """FAQPage built from the five questions the page already shows.

    The block was on the page as visible copy and nowhere in the markup, so
    the one section written to be quoted was the one an answer engine could
    not read as an answer. Built from QUESTIONS so the two cannot drift.
    """
    import html as _h
    strip = lambda t: _h.unescape(re.sub(r"<[^>]+>", "", t)).strip()
    rows = ",".join(
        '{"@type":"Question","name":%s,"acceptedAnswer":{"@type":"Answer","text":%s}}'
        % (_json.dumps(strip(q), ensure_ascii=False), _json.dumps(strip(a), ensure_ascii=False))
        for _, q, a in QUESTIONS)
    return ('{"@type":"FAQPage","@id":"%s#faq","inLanguage":"%s",'
            '"isPartOf":{"@id":"https://aiprofitlab.io/#website"},'
            '"mainEntity":[%s]}' % (PAGE_URL, LANG, rows))


def _questions():
    rows = []
    for n, q, a in QUESTIONS:
        rows.append(f"""      <div class="qa-row rv">
        <div class="qa-q"><span class="qa-n">{n}</span><p>&#8220;{q}&#8221;</p></div>
        <p class="qa-a">{a}</p>
      </div>""")
    return "\n".join(rows)


def _race():
    lanes = []
    for who, when, width, tone, note, flag in RACE:
        chip = f'<span class="lane-flag">{flag}</span>' if flag else ""
        lanes.append(f"""      <div class="lane {tone}">
        <div class="lane-head">
          <span class="lane-who">{who}{chip}</span>
          <span class="lane-when">{when}</span>
        </div>
        <div class="lane-track"><i style="--w:{width}%"></i></div>
        <p class="lane-note">{note}</p>
      </div>""")
    return "\n".join(lanes)


FACTS = [
    "Nothing new to learn", "You keep using WhatsApp", "One-time fee", "No monthly lock-in",
    "Arabic &#43; English", "Live in about a week", "Built in Muscat", "You own what I build",
]


def _facts():
    half = "".join(f'<span><span class="star">{STAR}</span>{f}</span>' for f in FACTS)
    return f"""<div class="facts" aria-label="Key facts">
  <div class="track">
    <div class="half">{half}</div>
    <div class="half" aria-hidden="true">{half}</div>
  </div>
</div>"""


def body():
    from hero import HERO_HTML

    # Sun-Thu (cols 0-4), 08:00-15:59 -> exactly 40 of 168 hours, which is the
    # figure in brand/docs/03-money-model.md section 5.
    office = _hours_grid(lambda d, h: d <= 4 and 8 <= h <= 15)
    always = _hours_grid(lambda d, h: True)

    p1 = f"""<main id="main">

{HERO_HTML}

{_facts()}

<!-- ================================= S2 - THE NOISE, THEN THE REAL QUESTIONS -->
<section class="s-dark" id="noise">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> Start here</p>
    <h2 class="h2">Everyone is talking about AI. Almost none of it is your job.</h2>

    <div class="buzz rv" aria-hidden="true">
{_buzz()}
      <div class="buzz-card">
        <p class="k">Your job is one question</p>
        <p class="q">Did that buyer get an answer, <em>or did he go somewhere else?</em></p>
      </div>
    </div>
    <p class="sr-only">A cloud of AI jargon &mdash; LLM, RAG, fine-tuning, agents, embeddings, inference
      and the rest &mdash; with one sentence over it: your job is one question. Did that buyer get an
      answer, or did he go somewhere else?</p>

    <div class="asterism" style="margin-top:clamp(38px,5vw,64px)" aria-hidden="true">{STAR}</div>

    <p class="eyebrow"><span class="star">{STAR}</span> The five you don&#8217;t ask out loud</p>
    <div class="qa">
{_questions()}
    </div>
  </div>
</section>

<!-- ======================================================= S3 - THE REPLY RACE -->
<section class="s-cream grain">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> What has actually changed</p>
    <h2 class="h2">Your buyer stopped waiting. That is the whole change.</h2>
    <p class="lede">One evening. One buyer. The same question sent to three suppliers at 9:47 PM.</p>

    <div class="race rv" data-stagger>
{_race()}
    </div>

    <div class="race-foot">
      <p class="race-kick">Three suppliers got the message. One got the order.</p>
      <p class="race-note">An evening of the kind you have had, not a statistic.
        Bar length is ranked, not to scale.</p>
    </div>
  </div>
</section>

<!-- ========================================== S4 - YOUR OWN NUMBER, NOT MINE -->
<section class="s-dark" id="leak">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> Your own numbers</p>
    <h2 class="h2">Four sliders. Nothing assumed. Your number.</h2>
    <p class="lede">I have no figures about your business, so every one below is yours to set.</p>

    <div class="leak-grid" style="margin-top:clamp(30px,4vw,52px)">
      <div class="panelcard rv">
        <h3>Your business, in four numbers</h3>

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
        <div class="fieldrow" style="margin-bottom:0">
          <label for="q4">Share of answered inquiries you win <output id="o4">20%</output></label>
          <input type="range" id="q4" min="5" max="60" step="5" value="20">
        </div>
      </div>

      <div class="panelcard rv" style="--d:.12s">
        <span class="bignum-cap">Revenue walking away, per month</span>
        <span class="bignum" id="leakNum">OMR 1,559</span>

        <!-- Two bars, one scale: the monthly leak against the one-time cost of
             fixing it. The comparison is the whole argument. -->
        <svg id="bars" viewBox="0 0 420 132" role="img" style="width:100%;height:auto;margin-top:26px" aria-labelledby="barsTitle">
          <title id="barsTitle">Monthly revenue lost to silence, compared with the one-time cost of the Smart Website</title>
          <text x="0" y="14" fill="#A8BCB1" font-family="IBM Plex Mono, monospace" font-size="15">Lost each month</text>
          <rect x="0" y="22" width="420" height="26" rx="5" fill="rgba(241,239,232,.10)"/>
          <rect id="barLeak" x="0" y="22" width="420" height="26" rx="5" fill="#D89234"/>
          <text id="barLeakT" x="410" y="40" fill="#072B22" font-family="IBM Plex Mono, monospace" font-size="15" font-weight="500" text-anchor="end">OMR 1,559</text>
          <text x="0" y="82" fill="#A8BCB1" font-family="IBM Plex Mono, monospace" font-size="15">Smart Website, once</text>
          <rect x="0" y="90" width="420" height="26" rx="5" fill="rgba(241,239,232,.10)"/>
          <rect id="barCost" x="0" y="90" width="256" height="26" rx="5" fill="#1FAF5E"/>
          <text x="10" y="108" fill="#072B22" font-family="IBM Plex Mono, monospace" font-size="15" font-weight="500">OMR 950</text>
        </svg>

        <p class="payback">At that rate it pays for itself in <b id="days">19 days</b>.</p>
        <p class="assume">After-hours inquiries per month &times; your win rate &times; your average order.
          It shows what is <em>at stake</em> in those messages &mdash; not a promise of recovery.</p>
      </div>
    </div>
  </div>
</section>

<!-- ============================== S5 - THE PART HE IS ACTUALLY AFRAID OF -->
<section class="s-panel">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> The part that worries you</p>
    <h2 class="h2">There is nothing here for you to learn.</h2>
    <p class="lede">No app to install. No screen to check. One message arrives every morning,
      in the place you already look first.</p>

    <div class="touch-grid" style="margin-top:clamp(30px,4vw,52px)">
      <div class="rv">
        <div class="phone">
          <div class="phone-in">
            <div class="phone-bar">
              <span class="phone-av" aria-hidden="true">AI</span>
              <span class="phone-nm">AI Profit Lab<span>online</span></span>
            </div>
            <div class="phone-body">
              <div class="bub">
                <p><b>Good morning.</b> Overnight, while you slept:</p>
                <ul>
                  <li>6 buyers asked about stock and delivery</li>
                  <li>4 got prices and dates &mdash; closed</li>
                  <li class="act"><span class="act-l">Needs you:</span> 200 cartons to Sohar</li>
                  <li class="act"><span class="act-l">Needs you:</span> a request for 60-day credit</li>
                </ul>
                <p style="margin:0">Both numbers are saved in your phone.</p>
                <span class="tme">07:02 &#10003;&#10003;</span>
              </div>
            </div>
          </div>
        </div>
        <p class="phone-cap">An example of the daily message</p>
      </div>

      <ul class="zeros rv" style="--d:.12s">
        <li>
          <span class="z" aria-hidden="true">0</span>
          <p class="zt">apps to install
            <small>Your phone stays exactly as it is today.</small></p>
        </li>
        <li>
          <span class="z" aria-hidden="true">0</span>
          <p class="zt">passwords to remember
            <small>There is no login for you, so there is nothing to forget.</small></p>
        </li>
        <li>
          <span class="z" aria-hidden="true">0</span>
          <p class="zt">screens you must check
            <small>It writes to you. You never go looking for it.</small></p>
        </li>
      </ul>
    </div>

    <p class="touch-kick">If you can read a WhatsApp message, <em>you can run this.</em></p>
  </div>
</section>
"""

    # ------------------------------------------------------------------
    # S6 - the ladder. The staircase is hidden below 760px, where a 1000-unit
    # viewBox would render its 26px labels at under 9 real pixels; the three
    # cards underneath carry the same content at any width.
    # ------------------------------------------------------------------
    p2 = f"""
<section class="s-cream grain" id="build">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> What gets built</p>
    <h2 class="h2">Three systems. Start with the one that hurts.</h2>
    <p class="lede">Nothing is a bundle you must buy at once. Nothing needs a monthly fee to keep working.</p>

    <svg class="stair rv" viewBox="0 0 1000 400" role="img" aria-labelledby="stairT stairD">
      <title id="stairT">The three systems as a staircase</title>
      <desc id="stairD">Step one, the Smart Website at OMR 950, makes buyers arrive. That creates the next
        question, answered by step two, the Live Owner Dashboard at plus OMR 650. That creates the next question,
        answered by step three, the Full Autopilot at plus OMR 900.</desc>

      <g class="step" style="--d:0s">
        <rect x="30" y="270" width="280" height="90" rx="12" fill="#0F6E56"/>
        <text x="54" y="308" fill="#F1EFE8" font-family="Marcellus, Georgia, serif" font-size="26">The Smart Website</text>
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
        <h3>The Smart Website</h3>
        <p>Answers buyers in Arabic and English, records who they are, and hands the live ones to your WhatsApp.</p>
        <span class="tag">One-time &#183; <b>OMR 950</b></span>
        <a class="tlink" href="/en/services/#smart-website">See what&#8217;s inside <span class="arw">&rarr;</span></a>
      </article>
      <article class="card sys-card">
        <span class="n">02</span>
        <h3>The Live Owner Dashboard</h3>
        <p>Cash, stock and open leads on one screen &mdash; without phoning three people to assemble it.</p>
        <span class="tag">Add-on &#183; <b>+OMR 650</b></span>
        <a class="tlink" href="/en/demos/#dash">Open the live demo <span class="arw">&rarr;</span></a>
      </article>
      <article class="card sys-card">
        <span class="n">03</span>
        <h3>The Full Autopilot</h3>
        <p>Something has to chase the quotes and the invoices. This does, on schedule, without being reminded.</p>
        <span class="tag">Add-on &#183; <b>+OMR 900</b></span>
        <a class="tlink" href="/en/services/#autopilot">See what&#8217;s inside <span class="arw">&rarr;</span></a>
      </article>
    </div>
  </div>
</section>

<!-- ================================================= S7 - PROOF YOU CAN CLICK -->
<section class="s-dark" id="proof">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> Proof, not testimonials</p>
    <h2 class="h2">Don&#8217;t take my word. Open the machines.</h2>
    <p class="lede">Real builds, running on demo data. Clicking one is a better test than a quote
      from someone you have never met.</p>

    <div class="tiles" style="margin-top:clamp(28px,4vw,48px)" data-stagger>
      <a class="tile" href="/en/demos/#dash">
        <span class="live"><i></i>Live demo</span>
        <span class="shot"><img src="/assets/v4/demo-dashboard-960.webp" alt="The CEO dashboard demo: revenue, gross profit and margin cards above a list of ranked actions." width="960" height="600" loading="lazy" decoding="async"></span>
        <span class="cap">
          <h3>Your business on one screen</h3>
          <p>Cash, margin, dead stock and what to do about it &mdash; ranked, in plain sentences.</p>
          <span class="tlink">Open it <span class="arw">&rarr;</span></span>
        </span>
      </a>

      <a class="tile" href="/en/demos/">
        <span class="live"><i></i>Live demo</span>
        <span class="shot"><img src="/assets/v4/demo-whatsapp-960.webp" alt="The WhatsApp receptionist demo: a lead list beside a full buyer conversation handled by the AI agent." width="960" height="600" loading="lazy" decoding="async"></span>
        <span class="cap">
          <h3>The buyer agent, mid-conversation</h3>
          <p>Watch it qualify a buyer, hold the thread, and book the appointment.</p>
          <span class="tlink">Open it <span class="arw">&rarr;</span></span>
        </span>
      </a>

      <a class="tile tile-wide" href="/en/contact/#test">
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

<!-- ================================== S8 - SPEND LESS, SERVE MORE -->
<section class="s-panel">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> Spend less. Serve more.</p>
    <h2 class="h2">A week has 168 hours. An administrator covers 40.</h2>
    <p class="lede">Each square is one hour of your week. This is about coverage, not quality &mdash;
      a good administrator does things no system can.</p>

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
        <h3>The Smart Website</h3>
        <p class="sub">OMR 950, once</p>
        <p class="hlegend">Rows: Sun &rarr; Sat &#183; columns: 00:00 &rarr; 23:00</p>
        {always}
        <span class="hcount"><span data-count="168">168</span> of 168 hours</span>
        <p class="note">It does not replace her. It covers the 128 hours she was never there for.</p>
      </div>
    </div>

    <div class="growth rv">
      <svg class="drawn" viewBox="0 0 640 284" role="img" aria-labelledby="grT grD">
        <title id="grT">Monthly cost as the number of buyers grows</title>
        <desc id="grD">Staff cost climbs in steps: every increase in inquiry volume eventually needs another
          salary. The system's line is flat &mdash; it is paid once and does not rise with the number of buyers.</desc>
        <line x1="48" y1="246" x2="612" y2="246" stroke="#DED8C8" stroke-width="2"/>
        <line x1="48" y1="22" x2="48" y2="246" stroke="#DED8C8" stroke-width="2"/>
        <polyline points="48,180 190,180 190,140 332,140 332,98 474,98 474,50 612,50"
          fill="none" stroke="#A6431F" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>
        <polyline points="48,224 612,224" fill="none" stroke="#1FAF5E" stroke-width="3" stroke-linecap="round"/>
        <text x="58" y="168" fill="#A6431F" font-family="IBM Plex Mono, monospace" font-size="15">More staff</text>
        <text x="58" y="212" fill="#178A4B" font-family="IBM Plex Mono, monospace" font-size="15">The system</text>
        <text x="48" y="272" fill="#5A665D" font-family="IBM Plex Mono, monospace" font-size="13">buyers per month &#8594;</text>
        <text x="20" y="134" fill="#5A665D" font-family="IBM Plex Mono, monospace" font-size="13"
          text-anchor="middle" transform="rotate(-90 20 134)">monthly cost</text>
      </svg>
      <div>
        <h3>Ten buyers at once cost the same as one.</h3>
        <p>Every step up in volume eventually costs another salary, every month. The system is paid
          once and does not notice how many people wrote tonight.</p>
      </div>
    </div>

    <div class="btn-row" style="margin-top:clamp(26px,3vw,40px)">
      <a class="btn btn-teal" href="/en/services/#price">See the whole price list</a>
      <a class="tlink" href="/en/services/">Every system, in detail <span class="arw">&rarr;</span></a>
    </div>
  </div>
</section>

<!-- ================================================== S9 - THE NAMED PROMISE -->
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

<!-- ===================================================== S10 - EXPLORE RAIL -->
<section class="s-cream grain">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> Keep going</p>
    <h2 class="h2">Four places worth your next five minutes.</h2>

    <div class="rail" style="margin-top:clamp(26px,3.5vw,44px)" data-stagger>
      <a class="rcard" href="/en/services/">
        <span class="rn">01</span>
        <span><h3>What I build</h3><p>Three systems, every price, and what is deliberately not included.</p></span>
        <span class="go">Open <span aria-hidden="true">&rarr;</span></span>
      </a>
      <a class="rcard" href="/en/process/">
        <span class="rn">02</span>
        <span><h3>How it works</h3><p>First message to live system, step by step, with the dates.</p></span>
        <span class="go">Open <span aria-hidden="true">&rarr;</span></span>
      </a>
      <a class="rcard" href="/en/about/">
        <span class="rn">03</span>
        <span><h3>Who builds it</h3><p>One operator, not an agency. Including who I turn away.</p></span>
        <span class="go">Open <span aria-hidden="true">&rarr;</span></span>
      </a>
      <a class="rcard" href="/blog/">
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
    slug="index",
    title="AI Profit Lab | You don't have to learn AI — Muscat, Oman",
    desc=("You never open it, never log in, never type a prompt. A bilingual smart website answers "
          "your buyers in Arabic and English at 2am and reports to your WhatsApp in one sentence. "
          "One-time fee, no monthly lock-in, built by an operator in Muscat."),
    nav="/",
    hero=True,
    calc=True,
    next=("Next", "What I build", "/en/services/"),
    schema=_faq_schema(),
)
