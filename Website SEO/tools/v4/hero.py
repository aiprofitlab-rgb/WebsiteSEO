#!/usr/bin/env python3
"""
The cinematic hero, ported from en/index-v3.html.

This is the one part of index-v3 Nahid signed off on, so it moves across
unchanged in behaviour: a scroll-scrubbed WebP frame sequence painted to a
canvas (150 frames desktop / 75 mobile, coarse-to-fine fetch, cross-dissolved).
The engine itself is extracted mechanically into _ported_js.py rather than
retyped. Only the copy and the lead CTA are new - the first screen is deliberately
bare: headline, one relief line, one button, everything else left to the scroll.
"""
from kit import WA, WA_ICON

# Layout geometry note (kept from v3, still load-bearing): the copy column has
# to end before x=25% of the frame, which is where the subject's silhouette
# begins at head height in every frame. The outer bands of the footage stay
# light (luminance 148-186), which is why the type over them is dark ink.
HERO_CSS = """
/* Section height IS the playback speed control: travel = height - 100vh
   stage, and the frames are spread across that travel. */
.cine{position:relative;height:500vh;background:var(--cream);padding:0}
.cine-stage{position:sticky;top:0;height:100vh;height:100svh;overflow:hidden;background:var(--cream);display:flex;flex-direction:column}
.cine-media{position:relative;width:100%;height:clamp(240px,46svh,520px);flex:none;background:var(--taupe);overflow:hidden}
.cine-poster,.cine-canvas{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block}
.cine-canvas{z-index:2;opacity:0;transition:opacity .4s ease}
.cine-canvas.ready{opacity:1}
.cine-poster{z-index:1}
.cine-ui{position:relative;flex:1 1 auto;min-height:0}
.cine-ui a{pointer-events:auto}
.lead,.endcard,.beat{
  position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:min(680px,90vw);
  text-align:center;opacity:0;transition:opacity .45s ease;pointer-events:none;
}
.lead.on,.endcard.on,.beat.on{opacity:1;pointer-events:auto}
.lead h1{font-size:clamp(2.6rem,5.6vw,4.5rem);line-height:1.04;color:var(--teal-950);margin:0 0 18px}
/* The relief line. The h1 removes the fear ("you don't have to learn it"); this
   line supplies the reason to keep reading. Kept to one sentence because it is
   read over moving footage. */
.lead .sub{font-size:clamp(1.05rem,2.4vw,1.24rem);line-height:1.5;color:var(--teal-900);margin:0 0 26px;max-width:26ch;margin-inline:auto}
/* A CTA inside the first viewport. v3 learned this the hard way: with the
   only button on the endcard at 86% scroll progress, a visitor who did not
   scroll five screens never saw a call to action at all. */
.lead-cta{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin:0}
.beat{font-family:var(--mono);font-size:clamp(1rem,3.2vw,1.15rem);line-height:1.55;color:var(--teal-900)}
.beat span{display:inline-block;border-top:2px solid var(--amber);padding-top:14px}
.endcard p{font-family:var(--display);font-size:clamp(1.7rem,5vw,2.5rem);color:var(--teal-950);margin:0 0 22px;line-height:1.2}
.cine-progress{position:absolute;left:0;right:0;bottom:0;height:3px;background:rgba(35,43,38,.1);z-index:5}
.cine-progress i{display:block;height:100%;width:100%;background:var(--amber);transform:scaleX(0);transform-origin:0 50%}
.wash-l,.wash-r{display:none;position:absolute;inset:0;z-index:3;pointer-events:none}

@media (min-width:1100px){
  .cine{height:560vh}
  .cine-media{position:absolute;inset:0;height:100%;width:100%}
  .cine-ui{position:absolute;inset:0;z-index:4;flex:none}
  .wash-l{display:block;background:linear-gradient(90deg,rgba(241,239,232,.95) 0%,rgba(241,239,232,.72) 32%,rgba(241,239,232,.18) 52%,rgba(241,239,232,0) 66%)}
  .wash-r{display:block;background:linear-gradient(270deg,rgba(241,239,232,.72) 0%,rgba(241,239,232,.34) 22%,rgba(241,239,232,0) 44%)}
  .lead,.endcard{left:clamp(32px,4.5vw,76px);right:auto;top:46%;transform:translateY(-50%);width:min(470px,34vw);text-align:left}
  .lead h1{font-size:clamp(2.5rem,3.5vw,3.6rem)}
  .lead .sub{margin-inline:0}
  .lead-cta{justify-content:flex-start}
  .beat{left:auto;right:clamp(32px,4.5vw,76px);top:50%;transform:translateY(-50%);width:min(330px,25vw);text-align:left;font-size:1.1rem}
}
@media (max-width:1099px){
  .cine{height:460vh}
  .cine-ui{padding:clamp(18px,4vw,32px) 20px}
  .cine-media{height:clamp(220px,38svh,420px)}
}
@media (max-width:560px){
  .cine{height:420vh}
  .lead h1{font-size:clamp(2.1rem,8.6vw,2.7rem)}
}
"""

HERO_HTML = f"""<section class="cine" id="cine">
  <div class="cine-stage" id="cineStage">
    <div class="cine-media" id="cineMedia">
      <img class="cine-poster" id="cinePoster" src="/assets/cinematic/poster.webp?v=20260817"
        alt="An illustration of the AI assistant: a machine form that becomes a person and begins working."
        width="1440" height="810" fetchpriority="high" decoding="async">
      <canvas class="cine-canvas" id="cineCanvas" aria-hidden="true"></canvas>
      <div class="wash-l"></div><div class="wash-r"></div>
    </div>

    <div class="cine-ui">
      <div class="lead on" id="lead">
        <h1>You don&#8217;t have to learn AI.</h1>
        <p class="sub">You only have to stop losing buyers to the supplier who answers first.</p>
        <div class="lead-cta">
          <a class="btn btn-teal" href="#noise">Show me, in one minute &darr;</a>
        </div>
      </div>

      <p class="beat" data-at="0.16"><span>9:47 PM. A buyer asks if you deliver to Sohar.</span></p>
      <p class="beat" data-at="0.28"><span>Your office closed four hours ago.</span></p>
      <p class="beat" data-at="0.40"><span>Something answers him. In Arabic.</span></p>
      <p class="beat" data-at="0.52"><span>It knows your stock. It knows your delivery days.</span></p>
      <p class="beat" data-at="0.64"><span>It quotes. It books. It logs the lead.</span></p>
      <p class="beat" data-at="0.76"><span>You read about it over coffee. You learned nothing new.</span></p>

      <div class="endcard" id="endcard">
        <p>Every success starts with insight.</p>
        <a class="btn btn-wa" href="{WA}?text=Hello%20Nahid%2C%20I%20want%20to%20ask%20about%20a%20Smart%20Website%20for%20my%20business.">{WA_ICON}Message me on WhatsApp</a>
      </div>

    </div>

    <div class="cine-progress"><i id="cineBar"></i></div>
  </div>
</section>
"""
