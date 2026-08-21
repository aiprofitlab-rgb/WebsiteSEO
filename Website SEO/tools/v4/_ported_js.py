"""Verbatim ports from en/index-v3.html (lines 2527-2748 and 2751-2813).
Extracted mechanically, not retyped. Do not hand-edit - re-extract instead."""

CINE_JS = r'''
/* --------------------------------------------------------------------------
   Scroll-scrubbed image sequence.

   Canvas rather than <video>: no +faststart, no every-frame keyframe encode,
   no Baseline re-encode for iOS, and none of the iOS Safari blanking that
   happens when currentTime is set repeatedly on a paused <video>. Scrubs the
   same on desktop, tablet and iPhone.

   Canvas rather than swapping <img> src: no decode flash between frames.

   Payload: 3.2 MB desktop / 0.9 MB mobile, versus 15.5 MB for the source mp4.
-------------------------------------------------------------------------- */
(function () {
  "use strict";

  /* Must match tools/build_cinematic_frames.py. That script prints replacement
     values if you rebuild with a different --frames. */
  const FRAMES_DESKTOP = 150;
  const FRAMES_MOBILE = 75;

  /* Cache-busting token for the frame set. MUST be bumped whenever the
     frames are rebuilt — build_cinematic_frames.py stamps it automatically.
     The host serves these immutable with positional filenames, so without a
     version token edge nodes can mix two builds of the same sequence. */
  const ASSET_V = "20260817";

  const sect = document.getElementById("cine");
  const stage = document.getElementById("cineStage");
  const media = document.getElementById("cineMedia");
  const canvas = document.getElementById("cineCanvas");
  const poster = document.getElementById("cinePoster");
  const bar = document.getElementById("cineBar");
  const lead = document.getElementById("lead");
  const endcard = document.getElementById("endcard");
  const beats = [].slice.call(document.querySelectorAll(".beat"));
  const topbar = document.getElementById("top");

  const clamp = (v, a, b) => (v < a ? a : v > b ? b : v);

  const onTopbar = () => topbar.classList.toggle("solid", window.scrollY > 40);
  onTopbar();
  addEventListener("scroll", onTopbar, { passive: true });

  if (!sect || !canvas) return;

  /* Reduced motion: never fetch the sequence. Swap in the closing still, since
     one image has to carry the whole story, and reveal all copy statically. */
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) {
    poster.src = "/assets/cinematic/still.webp?v=" + ASSET_V;
    lead.classList.add("on");
    endcard.classList.add("on");
    beats.forEach(b => b.classList.add("on"));
    return;
  }

  const isMobile = matchMedia("(max-width: 768px)").matches;
  const DIR = isMobile ? "mobile" : "desktop";
  const N = isMobile ? FRAMES_MOBILE : FRAMES_DESKTOP;

  const ctx = canvas.getContext("2d", { alpha: false });
  const imgs = new Array(N);
  let current = 0;
  let inView = false;
  let painted = false;
  let started = false;

  function resize() {
    const dpr = Math.min(devicePixelRatio || 1, 2);   // capping at 2 matters
    const w = media.clientWidth;
    const h = media.clientHeight;
    if (!w || !h) return;
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    canvas.style.width = w + "px";
    canvas.style.height = h + "px";
    ctx.fillStyle = "#9F9683";      // sampled from the footage
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    paint(true);
  }

  /* Frames arrive coarse-to-fine, so the array has holes. Fall back to the
     closest frame that has arrived rather than refusing to paint. */
  function nearest(idx) {
    if (imgs[idx]) return imgs[idx];
    for (let d = 1; d < N; d++) {
      if (imgs[idx - d]) return imgs[idx - d];
      if (imgs[idx + d]) return imgs[idx + d];
    }
    return null;
  }

  /* cover, never contain — contain letterboxes a 16:9 source in a tall box */
  function draw(im, alpha) {
    const cw = canvas.width, ch = canvas.height;
    const s = Math.max(cw / im.naturalWidth, ch / im.naturalHeight);
    const w = im.naturalWidth * s, h = im.naturalHeight * s;
    ctx.globalAlpha = alpha;
    ctx.drawImage(im, (cw - w) / 2, (ch - h) / 2, w, h);
    ctx.globalAlpha = 1;
  }

  /* Cross-dissolve the two frames `current` sits between rather than snapping
     to Math.round — the sequence samples a 14.5s source at ~10 fps, so a hard
     cut steps visibly. Only blends when BOTH neighbours have arrived; during
     the coarse-to-fine load, dissolving frame 0 into frame 8 would ghost. */
  function paint(force) {
    const pos = clamp(current, 0, N - 1);
    const i0 = Math.floor(pos);
    const f = pos - i0;
    const a = imgs[i0], b = imgs[i0 + 1];

    if (a && b && f > 0.001) {
      draw(a, 1);
      draw(b, f);
    } else {
      const im = nearest(Math.round(pos));
      if (!im) return;
      draw(im, 1);
    }
    if (!painted || force) { painted = true; canvas.classList.add("ready"); }
  }

  /* Coarse-to-fine fetch order. Passing over the range at stride 8, then 4, 2,
     1 makes the entire scrub usable after ~19 frames (~420 KB). */
  function fetchOrder(n) {
    const seen = new Set(), out = [];
    for (const stride of [8, 4, 2, 1]) {
      for (let i = 0; i < n; i += stride) {
        if (!seen.has(i)) { seen.add(i); out.push(i); }
      }
    }
    if (!seen.has(n - 1)) out.push(n - 1);
    return out;
  }

  const order = fetchOrder(N);
  let qi = 0;
  function loadNext() {
    if (qi >= order.length) return;
    const i = order[qi++];
    const im = new Image();
    im.decoding = "async";
    // keep frames behind fonts, poster and document in the network queue
    if ("fetchPriority" in im) im.fetchPriority = "low";
    im.onload = () => { imgs[i] = im; paint(!painted); loadNext(); };
    im.onerror = loadNext;            // a gap must not stall the chain
    im.src = "/assets/cinematic/" + DIR + "/f-" + String(i).padStart(3, "0")
      + ".webp?v=" + ASSET_V;
  }

  /* Deferred start. The hero is the first section, so the observer fires
     instantly and the sequence would otherwise compete with the fonts and the
     LCP poster for bandwidth on the very first paint. */
  function startLoading() {
    if (started) return;
    started = true;
    const go = () => { for (let k = 0; k < 4; k++) loadNext(); };   // 4 in flight
    const idle = fn => (window.requestIdleCallback
      ? requestIdleCallback(fn, { timeout: 1200 }) : setTimeout(fn, 300));
    if (document.readyState === "complete") idle(go);
    else addEventListener("load", () => idle(go), { once: true });
  }

  function progress() {
    const travel = sect.offsetHeight - stage.offsetHeight;
    if (travel <= 0) return 0;
    return clamp(-sect.getBoundingClientRect().top / travel, 0, 1);
  }

  function overlays(p) {
    bar.style.transform = "scaleX(" + p + ")";
    lead.classList.toggle("on", p < 0.12);
    endcard.classList.toggle("on", p > 0.86);
    for (let i = 0; i < beats.length; i++) {
      const at = parseFloat(beats[i].dataset.at);
      beats[i].classList.toggle("on", p > at - 0.055 && p < at + 0.075);
    }
  }

  /* Frame-rate independent smoothing. TAU is a time constant in ms: the canvas
     closes ~63% of the remaining distance to the scroll position every TAU,
     whatever the refresh rate. A fixed per-frame lerp converged twice as fast
     on a 120 Hz display as on a 60 Hz one. */
  const TAU = 190;
  let last = 0;

  function tick(now) {
    const dt = last ? Math.min(now - last, 64) : 16;   // cap across tab switches
    last = now;
    const p = progress();
    const target = p * (N - 1);
    current += (target - current) * (1 - Math.exp(-dt / TAU));
    if (Math.abs(target - current) < 0.004) current = target;
    paint(false);
    overlays(p);
    if (inView) requestAnimationFrame(tick);
  }

  /* Fires well before the section arrives so frames are in place on entry. */
  new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        startLoading();
        /* last=0 so the first tick after a long absence uses the nominal
           16ms step instead of a huge dt that would snap the scrub. */
        if (!inView) { inView = true; last = 0; requestAnimationFrame(tick); }
      } else {
        inView = false;
      }
    });
  }, { rootMargin: "200% 0px 200% 0px" }).observe(sect);

  let rt = 0;
  addEventListener("resize", () => { clearTimeout(rt); rt = setTimeout(resize, 150); });
  addEventListener("orientationchange", () => setTimeout(resize, 250));

  resize();
  overlays(0);
})();
'''

# --------------------------------------------------------------------------
# Cost-of-silence calculator. One template, two languages.
#
# The arithmetic, the ids and the bar geometry are shared; what varies is the
# currency format, the payback wording, and whether the two bars grow from the
# left or the right. Mirroring is done in the script rather than with a CSS
# transform because a flipped <g> would mirror the label text with it.
# --------------------------------------------------------------------------
_CALC_TPL = r"""
/* --------------------------------------------------------------------------
   Cost-of-silence calculator.

   Deliberately assumption-free: every term is a slider the visitor sets, so
   the output is arithmetic on their own inputs rather than a claim of ours.
   That matters — the site has a standing rule against unsourced statistics.
-------------------------------------------------------------------------- */
(function () {
  "use strict";
  const $ = id => document.getElementById(id);
  const q1 = $("q1"), q2 = $("q2"), q3 = $("q3"), q4 = $("q4");
  if (!q1) return;

  const WEEKS_PER_MONTH = 4.33;
  const SMART_SITE = 950;          // must match the price ladder above
  const RTL = __RTL__;
  const fmt = n => __FMT__;

  function render() {
    const perWeek = +q1.value, pct = +q2.value, order = +q3.value, win = +q4.value;

    $("o1").textContent = perWeek;
    $("o2").textContent = pct + "%";
    $("o3").textContent = fmt(order);
    $("o4").textContent = win + "%";

    const leak = perWeek * WEEKS_PER_MONTH * (pct / 100) * (win / 100) * order;
    $("leakNum").textContent = fmt(leak);

    /* Both bars share one scale so the comparison is honest. The leak bar is
       full width whenever it exceeds the build cost, and the cost bar shrinks
       against it; below that the roles swap. */
    const max = Math.max(leak, SMART_SITE) || 1;
    const W = 420;
    const leakW = Math.max(4, (leak / max) * W);
    const costW = Math.max(4, (SMART_SITE / max) * W);
    $("barLeak").setAttribute("width", leakW.toFixed(1));
    $("barCost").setAttribute("width", costW.toFixed(1));
    /* On an Arabic page both bars are anchored to the right edge of the track
       and grow leftwards, so a bar still starts where the reader starts. */
    if (RTL) {
      $("barLeak").setAttribute("x", (W - leakW).toFixed(1));
      $("barCost").setAttribute("x", (W - costW).toFixed(1));
    }

    /* Keep the leak label inside its own bar; when the bar is short the label
       would otherwise overhang the track and collide with the background. */
    const lt = $("barLeakT");
    lt.textContent = fmt(leak);
    if (leakW > 120) {
      lt.setAttribute("x", (RTL ? W - leakW + 10 : leakW - 10).toFixed(1));
      lt.setAttribute("text-anchor", RTL ? "start" : "end");
      lt.setAttribute("fill", "#072B22");
    } else {
      lt.setAttribute("x", (RTL ? W - leakW - 10 : leakW + 10).toFixed(1));
      lt.setAttribute("text-anchor", RTL ? "end" : "start");
      lt.setAttribute("fill", "#F1EFE8");
    }

    const perDay = leak / 30;
    const days = perDay > 0 ? Math.ceil(SMART_SITE / perDay) : Infinity;
    $("days").textContent = !isFinite(days) ? "—"
      : days <= 1 ? __DAY1__
        : days < 400 ? __DAYS__
          : __YEAR__;
  }

  [q1, q2, q3, q4].forEach(el => el.addEventListener("input", render));
  render();
})();
"""

_CALC_WORDS = {
    "en": {
        "__RTL__": "false",
        "__FMT__": '"OMR " + Math.round(n).toLocaleString("en-US")',
        "__DAY1__": '"a single day"',
        "__DAYS__": 'days + " days"',
        "__YEAR__": '"over a year"',
    },
    "ar": {
        "__RTL__": "true",
        # Latin figures with an Arabic currency word: Omani prices are written
        # in Latin numerals everywhere, including on invoices. The element that
        # receives this carries dir="ltr" so the group separators survive.
        "__FMT__": 'Math.round(n).toLocaleString("en-US") + " ر.ع."',
        "__DAY1__": '"يوم واحد"',
        "__DAYS__": 'days + " يوماً"',
        "__YEAR__": '"أكثر من سنة"',
    },
}


def calc_js(lang="en"):
    out = _CALC_TPL
    for k, v in _CALC_WORDS[lang].items():
        out = out.replace(k, v)
    return out


CALC_JS = calc_js("en")
CALC_JS_AR = calc_js("ar")
