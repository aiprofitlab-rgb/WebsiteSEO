#!/usr/bin/env python3
"""Simulators.

Two tools on one page, sharing one shell: the cost of silence (unanswered
buyer inquiries) and the cost of re-typing (manual data entry). Both follow the
same rule as the home page calculator - every term is a number the visitor
sets, so the output is arithmetic on their own figures and never a claim of
ours. Nothing is posted anywhere; the only thing that leaves the page is the
WhatsApp message the visitor chooses to send, with their inputs in it.

Adding a third tool: add a tab button, a .simgrid panel with the same field
markup, and one entry in TOOLS inside SIM_JS. The chart, the currency
formatting and the WhatsApp handoff are shared.
"""
from kit import WA, WA_ICON, STAR

SMART_SITE = 950     # one-time, must match the services page ladder
AUTOPILOT = 900      # one-time, added to the Smart Website

CSS = """
/* ------------------------------------------------------------------ tabs */
.tabs{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:clamp(24px,3vw,36px)}
.tabs button{
  display:inline-flex;align-items:center;gap:12px;font-family:var(--mono);font-size:.82rem;
  letter-spacing:.1em;text-transform:uppercase;color:rgba(241,239,232,.72);
  background:transparent;border:1px solid var(--line-dark);border-radius:99px;padding:12px 22px;
  cursor:pointer;transition:color .2s,border-color .2s,background .2s,transform .2s;
}
.tabs button em{font-style:normal;color:var(--amber-bright);opacity:.75}
.tabs button:hover{color:var(--cream);border-color:var(--amber);transform:translateY(-1px)}
.tabs button[aria-selected=true]{background:var(--cream);color:var(--teal-950);border-color:var(--cream)}
.tabs button[aria-selected=true] em{color:var(--amber-text);opacity:1}

/* ------------------------------------------------------------ simulator */
.simgrid{display:grid;grid-template-columns:.92fr 1.08fr;gap:clamp(22px,3vw,44px);align-items:start}
.simgrid[hidden]{display:none}
.simin,.simout{
  background:rgba(241,239,232,.045);border:1px solid var(--line-dark);border-radius:18px;
  padding:clamp(24px,2.8vw,34px);
}
.simout{background:rgba(7,43,34,.55)}
.simlbl{
  font-family:var(--mono);font-size:.76rem;letter-spacing:.16em;text-transform:uppercase;
  color:var(--amber-bright);margin:0 0 18px;display:flex;align-items:center;gap:9px;
}
.presets{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:24px}
.presets button{
  font-family:var(--mono);font-size:.74rem;letter-spacing:.08em;text-transform:uppercase;
  color:rgba(241,239,232,.75);background:transparent;border:1px solid var(--line-dark);
  border-radius:99px;padding:7px 13px;cursor:pointer;transition:color .2s,border-color .2s,background .2s;
}
.presets button:hover{color:var(--teal-950);background:var(--amber-pale);border-color:var(--amber-pale)}

.fieldrow{margin-bottom:22px}
.fieldrow label{
  display:flex;justify-content:space-between;align-items:baseline;gap:12px;
  font-size:.95rem;color:rgba(241,239,232,.82);margin-bottom:10px;
}
.fieldrow output{font-family:var(--mono);color:var(--amber-bright);font-size:1.02rem;white-space:nowrap}
.simin input[type=range]{
  -webkit-appearance:none;appearance:none;width:100%;height:4px;border-radius:99px;
  background:rgba(241,239,232,.16);outline:none;cursor:pointer;
}
.simin input[type=range]::-webkit-slider-thumb{
  -webkit-appearance:none;width:22px;height:22px;border-radius:50%;background:var(--amber-bright);
  border:3px solid var(--teal-950);cursor:grab;transition:transform .15s var(--ease);
}
.simin input[type=range]::-webkit-slider-thumb:hover{transform:scale(1.15)}
.simin input[type=range]::-moz-range-thumb{
  width:18px;height:18px;border-radius:50%;background:var(--amber-bright);border:3px solid var(--teal-950);cursor:grab;
}
.micro{font-size:.84rem;line-height:1.6;color:rgba(241,239,232,.5);margin:22px 0 0}

/* ----------------------------------------------------------------- out */
.bignum-cap{
  display:block;font-family:var(--mono);font-size:.78rem;letter-spacing:.15em;text-transform:uppercase;
  color:rgba(241,239,232,.55);margin:0 0 6px;
}
.bignum{
  display:block;font-family:var(--display);font-size:clamp(2.5rem,5.6vw,4rem);line-height:1;
  color:var(--amber-bright);font-variant-numeric:tabular-nums;
}
/* the arithmetic, shown rather than hidden - the whole argument is that the
   visitor can check every term against their own phone */
.chain{
  display:flex;flex-wrap:wrap;align-items:center;gap:7px 10px;margin:22px 0 0;
  padding:16px 0;border-top:1px solid var(--line-dark);border-bottom:1px solid var(--line-dark);
}
.chain span{font-family:var(--mono);font-size:.82rem;color:var(--cream);white-space:nowrap}
.chain i{font-style:normal;color:var(--amber-bright);opacity:.7}
.chain b{font-weight:400;color:rgba(241,239,232,.5);font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;display:block}

.figs{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:22px 0 0}
.figs div{border:1px solid var(--line-dark);border-radius:12px;padding:15px 16px}
.figs b{display:block;font-family:var(--mono);font-size:1.12rem;color:var(--cream);margin-bottom:5px;font-weight:500;font-variant-numeric:tabular-nums}
.figs span{font-size:.78rem;line-height:1.4;color:rgba(241,239,232,.55);display:block}

.chartwrap{margin:26px 0 0}
.chartwrap h4{
  font-family:var(--mono);font-size:.74rem;font-weight:500;letter-spacing:.14em;text-transform:uppercase;
  color:rgba(241,239,232,.55);margin:0 0 14px;
}
.chart{width:100%;height:auto;display:block;overflow:visible}
.legend{display:flex;gap:18px;flex-wrap:wrap;margin-top:14px;font-family:var(--mono);font-size:.74rem;letter-spacing:.06em;color:rgba(241,239,232,.6)}
.legend i{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:7px;vertical-align:-1px}
.legend i.dash{width:16px;height:0;border-radius:0;border-top:1.5px dashed var(--wa);vertical-align:4px}
.assume{margin:20px 0 0;font-size:.86rem;line-height:1.62;color:rgba(241,239,232,.5)}
.simout .btn-row{margin-top:24px}

/* --------------------------------------------------------------- method */
.method{display:grid;grid-template-columns:repeat(3,1fr);gap:clamp(16px,2vw,24px)}
.method .card p{font-size:.97rem}
.fixes .tblwrap{border:1px solid var(--line);border-radius:14px;overflow-x:auto;background:var(--white)}

@media (max-width:980px){
  .simgrid{grid-template-columns:minmax(0,1fr)}
  .figs{grid-template-columns:repeat(3,1fr)}
  .method{grid-template-columns:1fr}
}
@media (max-width:640px){
  .figs{grid-template-columns:1fr}
  /* The multiplication signs only read as operators on one line. Once the
     chain wraps, a two-column list of labelled terms is clearer than an
     equation broken in the middle. */
  .chain{display:grid;grid-template-columns:1fr 1fr;gap:14px 16px}
  .chain i{display:none}
  .tabs button{flex:1 1 100%;justify-content:center}
}
"""

JS = r"""
/* ---------------------------------------------------------------------------
   Two simulators, one engine.

   Each tool declares its fields, how to format them, the arithmetic, and the
   one-time cost it is being compared against. Everything below - the chart,
   the payback line, the WhatsApp handoff - is shared, so a third tool is a
   data entry rather than a new script.

   No input leaves the page. The WhatsApp button composes a message and hands
   it to WhatsApp; nothing is sent until the visitor presses send there.
--------------------------------------------------------------------------- */
(function(){
  "use strict";
  var WEEKS = 4.33;
  var omr = function(n){ return "OMR " + Math.round(n).toLocaleString("en-US"); };
  var pct = function(n){ return n + "%"; };

  var TOOLS = {
    A: {
      cost: 950,
      costLabel: "Smart Website, once",
      fields: {
        a1: {fmt: String},
        a2: {fmt: pct},
        a3: {fmt: pct},
        a4: {fmt: omr}
      },
      /* inquiries a week -> a month -> the after-hours slice -> the share of
         those you would have won -> the order they were worth */
      calc: function(v){ return v.a1 * WEEKS * (v.a2/100) * (v.a3/100) * v.a4; },
      chain: function(v){ return [
        [v.a1 + " a week", "inquiries"],
        [WEEKS.toFixed(2), "weeks/month"],
        [pct(v.a2), "after hours"],
        [pct(v.a3), "you win"],
        [omr(v.a4), "per order"]
      ]; },
      wa: function(v, out){
        return "Hello Nahid — I ran the silence simulator.\n\n" +
          "Inquiries a week: " + v.a1 + "\n" +
          "Arriving after hours: " + pct(v.a2) + "\n" +
          "Win rate when answered: " + pct(v.a3) + "\n" +
          "Average order: " + omr(v.a4) + "\n\n" +
          "It puts " + omr(out.monthly) + " a month at stake" +
          (out.days ? ", and payback at " + out.days + " days." : ".") +
          "\n\nCan we talk about it?";
      }
    },
    B: {
      cost: 900,
      costLabel: "Full Autopilot, once",
      fields: {
        b1: {fmt: String},
        b2: {fmt: function(n){ return n + " h"; }},
        b3: {fmt: function(n){ return "OMR " + n; }},
        b4: {fmt: pct}
      },
      calc: function(v){ return v.b1 * v.b2 * WEEKS * v.b3 * (v.b4/100); },
      chain: function(v){ return [
        [v.b1 + (v.b1 === 1 ? " person" : " people"), "re-typing"],
        [v.b2 + " h a week", "each"],
        [WEEKS.toFixed(2), "weeks/month"],
        ["OMR " + v.b3, "an hour"],
        [pct(v.b4), "automatable"]
      ]; },
      wa: function(v, out){
        return "Hello Nahid — I ran the re-typing simulator.\n\n" +
          "People doing it: " + v.b1 + "\n" +
          "Hours each a week: " + v.b2 + "\n" +
          "Loaded cost an hour: OMR " + v.b3 + "\n" +
          "Share that is mechanical: " + pct(v.b4) + "\n\n" +
          "It puts " + omr(out.monthly) + " a month into work nobody bills for" +
          (out.days ? ", with payback at " + out.days + " days." : ".") +
          "\n\nCan we talk about it?";
      }
    }
  };

  var SVGNS = "http://www.w3.org/2000/svg";
  function el(name, attrs){
    var n = document.createElementNS(SVGNS, name);
    for (var k in attrs) n.setAttribute(k, attrs[k]);
    return n;
  }

  /* Twelve months of cumulative loss against one one-time cost. The month the
     bars cross the cost line is the whole point of the picture, so that bar is
     the only one painted amber and the only extra label drawn.

     The cost line carries no text of its own: at a realistic leak the line
     sits near the floor, and any label on it landed on top of the first bars.
     It is named in the legend underneath instead, where nothing can cover it. */
  function chart(svg, monthly, cost, costLabel, legendEl){
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var W = 620, H = 210, padB = 26, padT = 14;
    var total = monthly * 12;
    var max = Math.max(total, cost * 1.15) || 1;
    var bw = W / 12, gap = 5;
    var crossed = -1;
    var marks = [];

    for (var i = 0; i < 12; i++){
      var cum = monthly * (i + 1);
      var was = crossed;
      if (crossed < 0 && cum >= cost && cost > 0) crossed = i;
      var hit = (was < 0 && crossed === i);
      var h = Math.max(1, (cum / max) * (H - padB - padT));
      var x = i * bw, y = H - padB - h;
      svg.appendChild(el("rect", {
        x: x + gap/2, y: y, width: bw - gap, height: h, rx: 4,
        fill: hit ? "#D89234" : (crossed >= 0 ? "rgba(241,239,232,.22)" : "rgba(241,239,232,.13)")
      }));
      if (hit) marks.push([i, "#D89234"]);
      else if (i === 0 || i === 5 || i === 11) marks.push([i, "rgba(241,239,232,.5)"]);
    }

    if (cost > 0 && cost <= max){
      var ly = H - padB - (cost / max) * (H - padB - padT);
      svg.appendChild(el("line", {x1: 0, y1: ly, x2: W, y2: ly,
        stroke: "#1FAF5E", "stroke-width": 1.5, "stroke-dasharray": "5 4"}));
    }

    /* month labels last, so nothing paints over them */
    var seen = {};
    marks.forEach(function(m){
      if (seen[m[0]] && m[1] !== "#D89234") return;
      seen[m[0]] = 1;
      var t = el("text", {x: m[0] * bw + bw/2, y: H - 9, "text-anchor": "middle",
        fill: m[1], "font-family": "IBM Plex Mono, monospace", "font-size": "11"});
      t.textContent = "M" + (m[0] + 1);
      svg.appendChild(t);
    });

    if (legendEl) legendEl.textContent = costLabel + " \u00b7 " + omr(cost);
    return crossed;
  }

  function wire(key){
    var tool = TOOLS[key];
    var panel = document.getElementById("panel" + key);
    if (!panel) return null;
    var ids = Object.keys(tool.fields);
    var inputs = ids.map(function(id){ return document.getElementById(id); });
    if (inputs.some(function(x){ return !x; })) return null;

    var out = {
      monthly: document.getElementById(key + "Monthly"),
      chain:   document.getElementById(key + "Chain"),
      annual:  document.getElementById(key + "Annual"),
      daily:   document.getElementById(key + "Daily"),
      payback: document.getElementById(key + "Payback"),
      svg:     document.getElementById(key + "Chart"),
      wa:      document.getElementById(key + "Wa"),
      legend:  document.getElementById(key + "Cost")
    };

    function read(){
      var v = {};
      ids.forEach(function(id){ v[id] = +document.getElementById(id).value; });
      return v;
    }

    function render(){
      var v = read();
      ids.forEach(function(id){
        var o = document.getElementById(id + "o");
        if (o) o.textContent = tool.fields[id].fmt(v[id]);
      });

      var monthly = tool.calc(v);
      var perDay = monthly / 30;
      var days = perDay > 0 ? Math.ceil(tool.cost / perDay) : 0;

      out.monthly.textContent = omr(monthly);
      out.annual.textContent = omr(monthly * 12);
      out.daily.textContent = omr(perDay);
      out.payback.textContent = !days ? "—"
        : days <= 1 ? "1 day" : days < 400 ? days + " days" : "over a year";

      out.chain.innerHTML = "";
      tool.chain(v).forEach(function(pair, i){
        if (i){
          var x = document.createElement("i");
          x.textContent = "×";
          out.chain.appendChild(x);
        }
        var s = document.createElement("span");
        var b = document.createElement("b");
        b.textContent = pair[1];
        s.appendChild(b);
        s.appendChild(document.createTextNode(pair[0]));
        out.chain.appendChild(s);
      });

      chart(out.svg, monthly, tool.cost, tool.costLabel, out.legend);

      out.wa.setAttribute("href", "https://wa.me/96899245250?text=" +
        encodeURIComponent(tool.wa(v, {monthly: monthly, days: days < 400 ? days : 0})));
    }

    inputs.forEach(function(i){ i.addEventListener("input", render); });
    panel.addEventListener("click", function(e){
      var b = e.target.closest("[data-preset]"); if (!b) return;
      b.getAttribute("data-preset").split(",").forEach(function(pair){
        var kv = pair.split(":"), f = document.getElementById(kv[0]);
        if (f) f.value = kv[1];
      });
      render();
      if (typeof gtag === "function") gtag("event","simulator_preset",{tool:key});
    });
    if (out.wa) out.wa.addEventListener("click", function(){
      if (typeof gtag === "function") gtag("event","generate_lead",{method:"simulator_" + key});
    });
    render();
    return render;
  }

  wire("A"); wire("B");

  /* tabs ------------------------------------------------------------------ */
  var bar = document.getElementById("simtabs");
  if (bar) bar.addEventListener("click", function(e){
    var b = e.target.closest("button[role=tab]"); if (!b) return;
    [].forEach.call(bar.querySelectorAll("button[role=tab]"), function(t){
      var on = t === b;
      t.setAttribute("aria-selected", on ? "true" : "false");
      t.setAttribute("tabindex", on ? "0" : "-1");
      document.getElementById(t.getAttribute("aria-controls")).hidden = !on;
    });
    if (typeof gtag === "function") gtag("event","simulator_tab",{tool:b.id});
  });
})();
"""


def _field(fid, label, mn, mx, step, val, out):
    return f"""<div class="fieldrow">
          <label for="{fid}">{label} <output id="{fid}o" for="{fid}">{out}</output></label>
          <input type="range" id="{fid}" min="{mn}" max="{mx}" step="{step}" value="{val}">
        </div>"""


def body():
    presets = [
        ("Auto workshop", "a1:30,a2:35,a3:25,a4:90"),
        ("Trading &amp; distribution", "a1:22,a2:45,a3:15,a4:420"),
        ("Real estate", "a1:18,a2:50,a3:10,a4:800"),
        ("Clinic", "a1:45,a2:40,a3:30,a4:35"),
    ]
    preset_html = "".join(
        f'<button type="button" data-preset="{v}">{n}</button>' for n, v in presets)

    return f"""<main id="main">

<section class="phero s-panel grain">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span>Simulators</p>
    <h1 class="h1">Run your own numbers</h1>
    <p class="lede">Two calculators for the two leaks I am asked about most: the buyers who message
      when nobody is there, and the hours your staff spend re-typing what a machine already knows.
      Every term is a figure you set. Nothing is stored, nothing is submitted, and no result is a promise.</p>
    <div class="btn-row" style="margin-top:26px">
      <a class="btn btn-teal" href="#tools">Open the simulators</a>
      <a class="tlink" href="/en/article-v4/">Read the method first <span class="arw">&rarr;</span></a>
    </div>
  </div>
</section>

<section class="s-dark grain" id="tools">
  <div class="wrap">
    <div class="tabs" id="simtabs" role="tablist" aria-label="Choose a simulator">
      <button type="button" role="tab" id="tabA" aria-controls="panelA" aria-selected="true" tabindex="0"><em>01</em>The cost of silence</button>
      <button type="button" role="tab" id="tabB" aria-controls="panelB" aria-selected="false" tabindex="-1"><em>02</em>The cost of re-typing</button>
    </div>

    <!-- ------------------------------------------------ tool A: silence -->
    <div class="simgrid" id="panelA" role="tabpanel" aria-labelledby="tabA">
      <div class="simin">
        <p class="simlbl"><span class="star">{STAR}</span>Your numbers</p>
        <div class="presets">{preset_html}</div>
        {_field("a1", "Buyer inquiries in a normal week", 5, 150, 1, 30, "30")}
        {_field("a2", "Share arriving outside working hours", 5, 80, 5, 35, "35%")}
        {_field("a3", "Share of answered inquiries you win", 5, 60, 5, 25, "25%")}
        {_field("a4", "Your average order value", 20, 2000, 10, 90, "OMR 90")}
        <p class="micro">Count people, not messages, and use a normal week rather than your best one.
          Round every figure down &mdash; the argument is stronger when it is conservative.</p>
      </div>
      <div class="simout">
        <span class="bignum-cap">Revenue at stake, per month</span>
        <span class="bignum" id="AMonthly">OMR 1,023</span>
        <div class="chain" id="AChain"></div>
        <div class="figs">
          <div><b id="AAnnual">OMR 12,276</b><span>Over twelve months</span></div>
          <div><b id="ADaily">OMR 34</b><span>Every day it stays open</span></div>
          <div><b id="APayback">28 days</b><span>To cover OMR {SMART_SITE} once</span></div>
        </div>
        <div class="chartwrap">
          <h4>Cumulative, against the one-time cost of closing it</h4>
          <svg class="chart" id="AChart" viewBox="0 0 620 210" role="img"
               aria-label="Cumulative revenue at stake over twelve months, compared with the one-time cost of the Smart Website"></svg>
          <p class="legend"><span><i style="background:#D89234"></i>The month it has paid for itself</span>
            <span><i style="background:rgba(241,239,232,.22)"></i>Cumulative at stake</span>
            <span><i class="dash"></i><span id="ACost">Smart Website, once &middot; OMR 950</span></span></p>
        </div>
        <div class="btn-row">
          <a class="btn btn-wa" id="AWa" href="{WA}">{WA_ICON}<span>Send me these numbers</span></a>
          <a class="btn btn-ghost" href="/en/services-v4/#price">See what closes it</a>
        </div>
        <p class="assume">This is what is <em>at stake</em> in the messages nobody answered &mdash; not revenue
          you are guaranteed to recover. I deliberately do not multiply it by a recovery rate, because I
          would be inventing that rate and you would have no way to check it.</p>
      </div>
    </div>

    <!-- ----------------------------------------------- tool B: re-typing -->
    <div class="simgrid" id="panelB" role="tabpanel" aria-labelledby="tabB" hidden>
      <div class="simin">
        <p class="simlbl"><span class="star">{STAR}</span>Your numbers</p>
        {_field("b1", "People re-keying data between systems", 1, 20, 1, 3, "3")}
        {_field("b2", "Hours each spends on it per week", 1, 30, 1, 6, "6 h")}
        {_field("b3", "Loaded cost of an hour of their time", 1, 15, 1, 4, "OMR 4")}
        {_field("b4", "Share of it that is purely mechanical", 10, 90, 5, 70, "70%")}
        <p class="micro">Loaded cost means salary plus everything that comes with it, divided by the hours
          actually worked &mdash; not the hourly rate on the contract. The mechanical share is the part with
          no judgement in it: copying, re-formatting, checking one screen against another.</p>
      </div>
      <div class="simout">
        <span class="bignum-cap">Paid for work nobody bills for, per month</span>
        <span class="bignum" id="BMonthly">OMR 218</span>
        <div class="chain" id="BChain"></div>
        <div class="figs">
          <div><b id="BAnnual">OMR 2,619</b><span>Over twelve months</span></div>
          <div><b id="BDaily">OMR 7</b><span>Every day it stays manual</span></div>
          <div><b id="BPayback">124 days</b><span>To cover OMR {AUTOPILOT} once</span></div>
        </div>
        <div class="chartwrap">
          <h4>Cumulative, against the one-time cost of automating it</h4>
          <svg class="chart" id="BChart" viewBox="0 0 620 210" role="img"
               aria-label="Cumulative cost of manual re-keying over twelve months, compared with the one-time cost of the Full Autopilot"></svg>
          <p class="legend"><span><i style="background:#D89234"></i>The month it has paid for itself</span>
            <span><i style="background:rgba(241,239,232,.22)"></i>Cumulative cost</span>
            <span><i class="dash"></i><span id="BCost">Full Autopilot, once &middot; OMR 900</span></span></p>
        </div>
        <div class="btn-row">
          <a class="btn btn-wa" id="BWa" href="{WA}">{WA_ICON}<span>Send me these numbers</span></a>
          <a class="btn btn-ghost" href="/en/services-v4/#price">See what closes it</a>
        </div>
        <p class="assume">This one is a real cost, not an opportunity cost: you are already paying it every
          month in salary. What it does not include is the error rate &mdash; the wrong figure typed once and
          then trusted by everyone downstream.</p>
      </div>
    </div>
  </div>
</section>

<section class="s-cream grain">
  <div class="wrap">
    <div class="asterism"><span>{STAR}</span></div>
    <p class="eyebrow"><span class="star">{STAR}</span>How to read the result</p>
    <h2 class="h2">Three rules, so the number stays honest</h2>
    <div class="method grid" data-stagger style="margin-top:clamp(28px,4vw,44px)">
      <div class="card">
        <span class="n">01</span>
        <h3>Every term is yours</h3>
        <p>There is not one industry average anywhere in this page. If the output looks wrong, one of your
          four inputs is wrong &mdash; and you are the only person who can correct it.</p>
      </div>
      <div class="card">
        <span class="n">02</span>
        <h3>At stake, not recovered</h3>
        <p>Tool 01 prices what was in the messages, not what any system would win back. Anyone quoting you
          a fixed recovery percentage has invented it.</p>
      </div>
      <div class="card">
        <span class="n">03</span>
        <h3>One-time against monthly</h3>
        <p>The comparison that matters is a recurring leak against a cost you pay once. That is the only
          reason the payback line is on the chart at all.</p>
      </div>
    </div>
  </div>
</section>

<section class="s-panel grain fixes">
  <div class="wrap-n">
    <p class="eyebrow"><span class="star">{STAR}</span>What the money buys</p>
    <h2 class="h2">The published prices these charts compare against</h2>
    <p class="lede">No quote-on-request, no discovery call before you are told a number.</p>
    <div class="tblwrap" style="margin-top:clamp(24px,3vw,34px)">
      <table class="tbl">
        <thead><tr><th>What it is</th><th>One-time</th><th>Required monthly</th></tr></thead>
        <tbody>
          <tr><td>The Smart Website &mdash; a site with a buyer agent that answers in Arabic and English</td>
              <td class="n">OMR {SMART_SITE}</td><td class="n">OMR 0</td></tr>
          <tr><td>The Live Owner Dashboard &mdash; cash, margin, stock and open leads on one screen</td>
              <td class="n">+OMR 650</td><td class="n">OMR 0</td></tr>
          <tr><td>The Full Autopilot &mdash; quote and invoice follow-up that stops when the buyer replies</td>
              <td class="n">+OMR {AUTOPILOT}</td><td class="n">OMR 0</td></tr>
          <tr><td>Care &mdash; optional, cancellable, never required to keep the system running</td>
              <td class="n">&mdash;</td><td class="n">OMR 75/mo</td></tr>
        </tbody>
      </table>
    </div>
    <div class="btn-row" style="margin-top:26px">
      <a class="btn btn-teal" href="/en/services-v4/#price">The full price page</a>
      <a class="btn btn-ghost" href="/en/demo-v4/">Watch it answer a buyer</a>
    </div>
  </div>
</section>

</main>
"""


META = dict(
    slug="simulator-v4",
    title="Simulators | What silence and re-typing cost your business — AI Profit Lab",
    desc=("Two calculators on your own figures: what unanswered buyer inquiries put at stake each month, "
          "and what manual data entry costs you. Nothing stored, nothing submitted."),
    nav="/en/simulator-v4/",
    next=("Next", "Watch it answer a buyer", "/en/demo-v4/"),
    schema="""{
  "@context":"https://schema.org",
  "@type":"WebApplication",
  "name":"AI Profit Lab Revenue Leak Simulators",
  "applicationCategory":"BusinessApplication",
  "operatingSystem":"Any",
  "url":"https://aiprofitlab.io/en/simulator-v4/",
  "offers":{"@type":"Offer","price":"0","priceCurrency":"OMR"},
  "publisher":{"@type":"Organization","name":"AI Profit Lab","legalName":"Lotus Gulf International"}
}""",
)
