
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
   Archive controls: topic filter, text search and progressive reveal, over one
   server-rendered list. There is no second copy of the data and no fetch - the
   cards are the index - so with the script absent the page is still the whole
   archive, newest first.
--------------------------------------------------------------------------- */
(function(){
  "use strict";
  var grid = document.getElementById("posts");
  if (!grid) return;

  var bar    = document.getElementById("filters");
  var input  = document.getElementById("q");
  var wrap   = document.getElementById("searchbox");
  var clear  = document.getElementById("qclear");
  var count  = document.getElementById("fcount");
  var empty  = document.getElementById("empty");
  var more   = document.getElementById("more");
  var feat   = document.getElementById("featured");
  var PAGE   = parseInt(grid.getAttribute("data-page") || "24", 10);
  var ONE    = grid.getAttribute("data-one");
  var MANY   = grid.getAttribute("data-many");

  /* Arabic is written with optional vowel marks, four spellings of alef and a
     taa marbuta that readers type as either ة or ه. Folding both the haystack
     and the needle through the same normaliser is what makes "اتمتة" find an
     article filed under "أتمتة". Harmless on Latin text, so it runs on both. */
  function norm(s){
    return (s || "").toLowerCase()
      .replace(/[ً-ْٰـ]/g, "")
      .replace(/[آأإٱ]/g, "ا")
      .replace(/ى/g, "ي")
      .replace(/ة/g, "ه")
      .replace(/\s+/g, " ")
      .trim();
  }

  /* The searchable string is normalised once per card, not once per keystroke. */
  var cards = [].slice.call(grid.querySelectorAll(".post")).map(function(el){
    return {el: el, cat: el.getAttribute("data-cat"), feat: el.hasAttribute("data-feat"),
            s: norm(el.getAttribute("data-s"))};
  });

  /* `q` is always an array of normalised terms - never a string, never null.
     One shape means matches() has no type test to get wrong, and an empty
     array is the honest representation of "nothing typed". */
  var cat = "all", q = [], shown = PAGE;

  function matches(c){
    if (cat !== "all" && c.cat !== cat) return false;
    for (var i = 0; i < q.length; i++){ if (c.s.indexOf(q[i]) === -1) return false; }
    return true;
  }

  function apply(){
    /* The featured panel is the unfiltered, unsearched view only: with a
       filter or a query active it would sit above the results contradicting
       them. While it shows, it stands in for its own card in the grid. */
    var featOn = (cat === "all" && q.length === 0);
    if (feat) feat.hidden = !featOn;

    var hits = 0, painted = 0;
    for (var i = 0; i < cards.length; i++){
      var c = cards[i];
      var vis;
      if (c.feat && featOn){
        vis = false;                       /* the panel is showing it instead */
      } else {
        var on = matches(c);
        if (on) hits++;
        /* Two reasons a card can be out: it did not match, or it matched but
           sits past the reveal line. Only the first is "no results", which is
           why hits is counted before this test. */
        vis = on && painted < shown;
        if (vis) painted++;
      }
      if (c.el.hidden === vis) c.el.hidden = !vis;
    }

    /* The panel is one of the articles on show, so it counts as one. */
    var total = hits + (featOn ? 1 : 0);
    if (count) count.textContent = total === 1 ? ONE : MANY.replace("%d", total);
    if (empty) empty.hidden = total > 0;
    if (more)  more.hidden  = hits <= painted;
    if (wrap)  wrap.classList.toggle("has-q", !!(input && input.value));
  }

  if (bar) bar.addEventListener("click", function(e){
    var b = e.target.closest("button");
    if (!b) return;
    cat = b.getAttribute("data-cat");
    shown = PAGE;
    [].forEach.call(bar.querySelectorAll("button"), function(x){
      x.setAttribute("aria-pressed", x === b ? "true" : "false");
    });
    apply();
    if (typeof gtag === "function") gtag("event", "filter_articles", {category: cat});
  });

  if (input){
    var timer;
    input.addEventListener("input", function(){
      /* Split on whitespace so the terms can appear in any order and in any
         of the fields folded into data-s. */
      q = norm(input.value).split(" ").filter(Boolean);
      shown = PAGE;
      apply();
      clearTimeout(timer);
      timer = setTimeout(function(){
        if (q.length && typeof gtag === "function")
          gtag("event", "search_articles", {search_term: input.value.trim()});
      }, 900);
    });
    input.addEventListener("keydown", function(e){ if (e.key === "Escape") reset(); });
  }

  function reset(){
    if (input) input.value = "";
    q = []; shown = PAGE; apply(); if (input) input.focus();
  }
  if (clear) clear.addEventListener("click", reset);

  if (more) more.addEventListener("click", function(){
    /* The first card of the batch about to appear, captured before it does.
       Once the button hides itself on the last batch it can no longer hold
       focus, and a keyboard user would be dropped back to the top of the
       document with no indication anything happened. */
    var first = grid.querySelectorAll(".post:not([hidden])").length;
    shown += PAGE;
    apply();
    if (more.hidden){
      var visible = grid.querySelectorAll(".post:not([hidden])");
      /* Each card is an <a href>, so it is already focusable - no tabindex
         needed, and adding one would pull it out of the tab order. */
      var target = visible[first] || visible[visible.length - 1];
      if (target) target.focus();
    }
  });

  apply();
})();
