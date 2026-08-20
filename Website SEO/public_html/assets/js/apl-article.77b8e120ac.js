
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

/* ---------------------------------------------------------------------------
   Article behaviour. The table of contents is rendered server-side and every
   link works without this script; what runs here is only the progress bar,
   the "you are here" highlight, and the copy-link button.
--------------------------------------------------------------------------- */
(function(){
  "use strict";
  var art = document.getElementById("art");
  if (!art) return;

  /* progress ------------------------------------------------------------- */
  var bar = document.getElementById("prog");
  if (bar){
    var tick = function(){
      var box = art.getBoundingClientRect();
      var total = box.height - innerHeight;
      var done = total > 0 ? (-box.top) / total : 1;
      bar.style.width = (Math.min(Math.max(done, 0), 1) * 100).toFixed(2) + "%";
    };
    tick(); addEventListener("scroll", tick, {passive:true}); addEventListener("resize", tick);
  }

  /* scrollspy ------------------------------------------------------------ */
  var links = [].slice.call(document.querySelectorAll(".toc a[href^='#']"));
  var heads = links.map(function(a){ return document.getElementById(a.getAttribute("href").slice(1)); })
                   .filter(Boolean);
  if (heads.length && "IntersectionObserver" in window){
    var seen = {};
    var mark = function(){
      /* The topmost heading that has already crossed the reading line wins;
         intersection alone would light up two entries on a long section. */
      var best = null;
      heads.forEach(function(h){ if (h.getBoundingClientRect().top < 140) best = h; });
      links.forEach(function(a){
        a.classList.toggle("on", !!best && a.getAttribute("href") === "#" + best.id);
      });
    };
    mark(); addEventListener("scroll", mark, {passive:true});
    void seen;
  }

  /* copy link ------------------------------------------------------------ */
  var copy = document.getElementById("copyLink");
  if (copy){
    copy.addEventListener("click", function(){
      var url = location.href.split("#")[0];
      var ok = function(){
        copy.classList.add("done");
        copy.setAttribute("aria-label", "Link copied");
        setTimeout(function(){ copy.classList.remove("done"); copy.setAttribute("aria-label","Copy link"); }, 1800);
      };
      if (navigator.clipboard && navigator.clipboard.writeText){
        navigator.clipboard.writeText(url).then(ok, function(){});
      } else {
        var t = document.createElement("textarea");
        t.value = url; document.body.appendChild(t); t.select();
        try { document.execCommand("copy"); ok(); } catch(e){}
        document.body.removeChild(t);
      }
    });
  }
})();
