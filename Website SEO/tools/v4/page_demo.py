#!/usr/bin/env python3
"""Demos.

Two working demonstrations behind one tab strip: the buyer agent answering on
WhatsApp, and the owner dashboard.

The conversations live in SCENARIOS below and are used twice - serialised into
the page as JSON for the player, and rendered as static markup for the default
scenario so that a visitor with no JavaScript still reads the whole exchange
instead of an empty phone. One source, so the two can never drift.

All figures on both demos belong to a fictional distributor. That is stated on
the page rather than implied, because inventing a named client would be the one
thing on this site nobody could check.
"""
import json

from kit import WA, WA_ICON, STAR

# --------------------------------------------------------------------------
# Conversations. who: "in" buyer, "out" agent, "sys" system note, "day" divider.
# rail: what the system did at that point, shown alongside.
# dir/lang: stamped on every speech bubble, so a thread in the other language
# reads correctly whichever page it is embedded in - on the Arabic page it is
# the English scenario that has to opt out of the page direction.
# --------------------------------------------------------------------------
SCENARIOS = [
    {
        "id": "night",
        "tab": "Friday, 21:41",
        "title": "A buyer asks for stock and a price after hours",
        "sub": "Nobody is at the office. The agent answers from your own stock and price list, then hands "
               "over the moment the buyer shows intent.",
        "dir": "ltr", "lang": "en",
        "msgs": [
            {"who": "day", "text": "Friday 21:41"},
            {"who": "in", "t": "21:41",
             "text": "Hi — do you supply 20L drums of hydraulic oil? I need 8 for a site in Sohar.",
             "rail": ["21:41", "Message arrives. The office closed five hours ago."]},
            {"who": "out", "t": "21:41", "typing": 1400,
             "text": "Yes — ISO 68 and ISO 46, both in stock. Eight 20L drums can go out of the Rusayl "
                     "warehouse tomorrow morning.",
             "rail": ["21:41", "Language: English. Intent: stock check, quantity 8."]},
            {"who": "out", "t": "21:41", "typing": 900,
             "text": "ISO 68 is OMR 21.400 a drum at that quantity. Delivery to Sohar before noon.",
             "rail": ["21:41", "Stock: ISO 68 — 41 drums at Rusayl. Price band 8–14 applied."]},
            {"who": "in", "t": "21:43", "text": "And if I take 15?",
             "rail": ["21:43", "Quantity changed. No human has been woken up yet."]},
            {"who": "out", "t": "21:43", "typing": 1200,
             "text": "15 drums brings it to OMR 20.100 each. I can hold that stock against your number "
                     "now — shall I?",
             "rail": ["21:43", "Price band 15+ applied. Stock held, not sold."]},
            {"who": "in", "t": "21:44", "text": "Yes please. And I'll need an invoice for the company.",
             "rail": ["21:44", "Buying signal: invoice requested."]},
            {"who": "out", "t": "21:44", "typing": 1000,
             "text": "Held: 15 × ISO 68 under this number. Nahid has your thread and will confirm the "
                     "invoice details with you — he has everything above, so you will not repeat yourself.",
             "rail": ["21:44", "Handed to a human with the full thread attached."]},
            {"who": "sys", "text": "Three minutes. No one was awake.",
             "rail": ["21:44", "Total time from first message: 3 minutes."]},
        ],
    },
    {
        "id": "arabic",
        "tab": "بالعربية",
        "title": "The same agent, answering in Arabic",
        "sub": "The language is detected from the buyer's first message, not chosen from a menu. A buyer "
               "who writes in Arabic is answered in Arabic, with the same stock and the same prices.",
        "dir": "rtl", "lang": "ar",
        "msgs": [
            {"who": "day", "text": "السبت 20:12"},
            {"who": "in", "t": "20:12", "text": "السلام عليكم، عندكم فلتر زيت لتويوتا هايلكس ٢٠١٩؟",
             "rail": ["20:12", "Language detected: Arabic. Replies switch automatically."]},
            {"who": "out", "t": "20:12", "typing": 1300,
             "text": "وعليكم السلام. نعم متوفر — ١٨ قطعة في مخزن الرسيل.",
             "rail": ["20:12", "Part matched to your catalogue, not to a guess."]},
            {"who": "out", "t": "20:12", "typing": 800,
             "text": "السعر ٤.٥٠٠ ريال عماني للقطعة، ويصبح ٤.١٠٠ عند طلب عشر قطع أو أكثر.",
             "rail": ["20:12", "Your own quantity break, read from the price list."]},
            {"who": "in", "t": "20:14", "text": "أحتاج ٢٠ قطعة. متى يمكن التسليم؟",
             "rail": ["20:14", "Intent: order, quantity 20."]},
            {"who": "out", "t": "20:14", "typing": 1200,
             "text": "التسليم غدًا في مسقط. سأحجز الكمية باسمك الآن، وسيؤكد ناهد الطلب معك مباشرة.",
             "rail": ["20:14", "Stock held. Thread handed to a human, in Arabic."]},
            {"who": "sys", "text": "Two minutes, in the buyer's own language.",
             "rail": ["20:14", "No Arabic-speaking staff member was needed at 8pm on a Saturday."]},
        ],
    },
    {
        "id": "followup",
        "tab": "The quiet buyer",
        "title": "A quote goes out and the buyer goes quiet",
        "sub": "This is the Autopilot, not the receptionist. It chases a quote on a schedule you set, and "
               "stops itself the moment the buyer replies — which is the part most follow-up tools get wrong.",
        "dir": "ltr", "lang": "en",
        "msgs": [
            {"who": "sys", "text": "Quote #1184 sent — OMR 2,340",
             "rail": ["Mon 11:02", "Quote issued. Follow-up scheduled: day 2, day 5, day 9."]},
            {"who": "day", "text": "Two days later"},
            {"who": "out", "t": "11:02", "typing": 900,
             "text": "Morning — just checking quote #1184 for the 15 drums reached you. Happy to hold the "
                     "price until Thursday if that helps.",
             "rail": ["Wed 11:02", "Follow-up 1 of 3. Sent by the system, signed by you."]},
            {"who": "day", "text": "Three days later"},
            {"who": "out", "t": "09:30", "typing": 900,
             "text": "Still holding the 15 drums for you. If the quantity has changed I can re-quote in a "
                     "minute — just say the number.",
             "rail": ["Sat 09:30", "Follow-up 2 of 3."]},
            {"who": "in", "t": "09:52",
             "text": "Sorry — was waiting on my partner. Send the invoice, same quantity.",
             "rail": ["Sat 09:52", "Buyer replied. Follow-up 3 cancelled automatically."]},
            {"who": "sys", "text": "Sequence stopped. Nobody got chased twice.",
             "rail": ["Sat 09:52", "The order that would have quietly died is on your desk instead."]},
        ],
    },
]

CSS = """
/* ------------------------------------------------------------------ tabs */
.dtabs{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:clamp(22px,3vw,34px)}
.dtabs button{
  display:inline-flex;align-items:center;gap:11px;font-family:var(--mono);font-size:.82rem;
  letter-spacing:.1em;text-transform:uppercase;color:rgba(241,239,232,.72);background:transparent;
  border:1px solid var(--line-dark);border-radius:99px;padding:12px 22px;cursor:pointer;
  transition:color .2s,border-color .2s,background .2s,transform .2s;
}
.dtabs button em{font-style:normal;color:var(--amber-bright);opacity:.75}
/* the scenario strip sits inside a panel the demo tabs already chose - lighter
   weight, so the hierarchy between the two rows is legible at a glance */
.dtabs.sub button{font-size:.75rem;padding:9px 16px;letter-spacing:.08em}
.dtabs.sub button[aria-selected=true]{
  background:transparent;color:var(--amber-bright);border-color:var(--amber);
}
.dtabs.sub button[aria-selected=true] em{color:var(--amber-bright)}
.dtabs button:hover{color:var(--cream);border-color:var(--amber);transform:translateY(-1px)}
.dtabs button[aria-selected=true]{background:var(--cream);color:var(--teal-950);border-color:var(--cream)}
.dtabs button[aria-selected=true] em{color:var(--amber-text);opacity:1}

/* ---------------------------------------------------------------- stage */
.stage{display:grid;grid-template-columns:378px minmax(0,1fr);gap:clamp(26px,4vw,60px);align-items:start}
.stage[hidden]{display:none}

/* phone ----------------------------------------------------------------- */
.phone{
  width:100%;max-width:378px;border-radius:34px;background:#0A1A14;
  border:1px solid rgba(241,239,232,.14);box-shadow:0 40px 80px -50px rgba(0,0,0,.9);
  overflow:hidden;position:relative;
}
.phone .bar{
  display:flex;align-items:center;gap:11px;padding:14px 16px;background:#10261E;
  border-bottom:1px solid rgba(241,239,232,.08);
}
/* .phone .bar .av, not .phone .av: the status line's `.phone .bar span` rule
   (0,3,0 with the element) outranked a two-class selector and repainted the
   avatar's glyph at .7rem in WhatsApp green, top-left of its own circle. */
.phone .bar .av{
  width:36px;height:36px;border-radius:50%;background:var(--teal);flex:none;display:grid;place-items:center;
  color:var(--amber-pale);font-size:1.15rem;line-height:1;
}
.phone .bar b{display:block;font-size:.95rem;font-weight:500;color:var(--cream);line-height:1.2}
.phone .bar span{
  font-family:var(--mono);font-size:.7rem;letter-spacing:.08em;text-transform:uppercase;color:var(--wa);
  display:flex;align-items:center;gap:6px;margin-top:3px;
}
.phone .bar span i{width:6px;height:6px;border-radius:50%;background:var(--wa);display:inline-block;animation:blip 2.4s infinite}
@keyframes blip{0%,100%{opacity:1}50%{opacity:.35}}
.thread{
  height:498px;overflow-y:auto;padding:18px 14px 22px;display:flex;flex-direction:column;gap:9px;
  background:#0A1A14;scroll-behavior:smooth;
}
.thread::-webkit-scrollbar{width:5px}
.thread::-webkit-scrollbar-thumb{background:rgba(241,239,232,.14);border-radius:9px}
.bub{
  max-width:84%;padding:9px 12px;border-radius:13px;font-size:.9rem;line-height:1.5;
  color:#EDEAE1;position:relative;animation:pop .35s var(--ease) both;
}
@keyframes pop{from{opacity:0;transform:translateY(9px) scale(.98)}to{opacity:1;transform:none}}
.bub.in{background:#1E2F27;align-self:flex-start;border-bottom-left-radius:4px}
.bub.out{background:#0F5F49;align-self:flex-end;border-bottom-right-radius:4px}
.bub .t{
  display:block;font-family:var(--mono);font-size:.63rem;letter-spacing:.06em;
  color:rgba(237,234,225,.5);margin-top:5px;text-align:right;
}
.bub.out .t::after{content:" \\2713\\2713";color:#7FD4FF}
.bub[dir=rtl]{text-align:right;font-size:.95rem;line-height:1.75}
.bub[dir=rtl] .t{text-align:left}
.daysep{
  align-self:center;font-family:var(--mono);font-size:.66rem;letter-spacing:.12em;text-transform:uppercase;
  color:rgba(237,234,225,.45);background:rgba(241,239,232,.06);padding:5px 13px;border-radius:99px;margin:5px 0;
}
.sysmsg{
  align-self:center;text-align:center;font-family:var(--mono);font-size:.7rem;letter-spacing:.07em;
  color:var(--amber-bright);background:rgba(186,117,23,.12);border:1px solid rgba(186,117,23,.3);
  padding:8px 14px;border-radius:10px;margin:6px 0;max-width:92%;
}
.typing{align-self:flex-end;background:#0F5F49;border-radius:13px;padding:11px 14px;display:flex;gap:4px}
.typing i{width:6px;height:6px;border-radius:50%;background:rgba(237,234,225,.75);animation:dot 1.1s infinite}
.typing i:nth-child(2){animation-delay:.16s}
.typing i:nth-child(3){animation-delay:.32s}
@keyframes dot{0%,60%,100%{opacity:.3;transform:translateY(0)}30%{opacity:1;transform:translateY(-3px)}}

.replay{
  display:flex;align-items:center;gap:10px;margin-top:16px;font-family:var(--mono);font-size:.76rem;
  letter-spacing:.09em;text-transform:uppercase;color:rgba(241,239,232,.6);
}
.replay button{
  font:inherit;color:var(--cream);background:transparent;border:1px solid var(--line-dark);
  border-radius:99px;padding:9px 16px;cursor:pointer;white-space:nowrap;flex:none;
  transition:border-color .2s,color .2s;
}
.replay span{line-height:1.5}
.replay button:hover{border-color:var(--amber);color:var(--amber-bright)}

/* rail ------------------------------------------------------------------ */
.rail h3{font-size:clamp(1.3rem,2.4vw,1.85rem);color:var(--cream);margin:0 0 12px}
.rail .sub{color:rgba(241,239,232,.72);font-size:1.02rem;margin:0 0 clamp(22px,3vw,32px);max-width:56ch}
.rail .lbl{
  font-family:var(--mono);font-size:.74rem;letter-spacing:.16em;text-transform:uppercase;
  color:var(--amber-bright);margin:0 0 16px;display:flex;align-items:center;gap:9px;
}
.steps2{list-style:none;margin:0;padding:0;position:relative}
.steps2::before{content:"";position:absolute;left:6px;top:6px;bottom:6px;width:1px;background:var(--line-dark)}
.steps2 li{
  position:relative;padding:0 0 18px 30px;opacity:.25;transition:opacity .45s var(--ease);
}
.steps2 li.on{opacity:1}
.steps2 li::before{
  content:"";position:absolute;left:0;top:7px;width:13px;height:13px;border-radius:50%;
  background:var(--teal-950);border:1.5px solid var(--line-dark);transition:border-color .45s,background .45s;
}
.steps2 li.on::before{background:var(--amber);border-color:var(--amber)}
.steps2 b{
  display:block;font-family:var(--mono);font-size:.72rem;letter-spacing:.12em;color:var(--amber-bright);
  margin-bottom:4px;font-weight:400;
}
.steps2 span{color:rgba(241,239,232,.8);font-size:.98rem;line-height:1.5}
html:not(.js) .steps2 li{opacity:1}
html:not(.js) .steps2 li::before{background:var(--amber);border-color:var(--amber)}

/* --------------------------------------------------------------- dashboard */
.dash{
  background:#08201A;border:1px solid var(--line-dark);border-radius:18px;overflow:hidden;
}
.dash .head{
  display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;
  padding:18px clamp(18px,2.4vw,28px);border-bottom:1px solid var(--line-dark);background:rgba(241,239,232,.03);
}
.dash .head b{font-family:var(--display);font-size:1.2rem;color:var(--cream);font-weight:400}
.dash .head .live{
  font-family:var(--mono);font-size:.7rem;letter-spacing:.12em;text-transform:uppercase;color:var(--wa);
  display:inline-flex;align-items:center;gap:7px;
}
.dash .head .live i{width:7px;height:7px;border-radius:50%;background:var(--wa);animation:blip 2.4s infinite}
.dash .body{padding:clamp(18px,2.4vw,28px);display:grid;grid-template-columns:1.25fr .75fr;gap:clamp(18px,2.4vw,26px)}
.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px}
.kpi{background:rgba(241,239,232,.05);border:1px solid var(--line-dark);border-radius:12px;padding:15px 16px}
.kpi span{
  display:block;font-family:var(--mono);font-size:.68rem;letter-spacing:.12em;text-transform:uppercase;
  color:rgba(241,239,232,.5);margin-bottom:8px;
}
.kpi b{display:block;font-family:var(--mono);font-size:clamp(1.1rem,1.9vw,1.42rem);color:var(--cream);font-weight:500;font-variant-numeric:tabular-nums}
.kpi i{font-style:normal;font-family:var(--mono);font-size:.74rem;color:var(--wa);display:block;margin-top:5px}
.kpi i.down{color:var(--alert)}
.dchart{background:rgba(241,239,232,.04);border:1px solid var(--line-dark);border-radius:12px;padding:16px}
.dchart h4,.alerts h4{
  font-family:var(--mono);font-size:.7rem;font-weight:500;letter-spacing:.13em;text-transform:uppercase;
  color:rgba(241,239,232,.5);margin:0 0 14px;
}
.alerts{display:flex;flex-direction:column;gap:12px}
.alert{
  background:rgba(241,239,232,.05);border:1px solid var(--line-dark);border-left:2px solid var(--amber);
  border-radius:10px;padding:14px 16px;
}
.alert.red{border-left-color:var(--alert)}
.alert.green{border-left-color:var(--wa)}
.alert b{display:block;font-family:var(--mono);font-size:.68rem;letter-spacing:.12em;text-transform:uppercase;color:var(--amber-bright);margin-bottom:7px}
.alert.red b{color:#E08262}
.alert.green b{color:var(--wa)}
.alert p{margin:0;font-size:.93rem;line-height:1.55;color:rgba(241,239,232,.82)}
.alert em{display:block;font-style:normal;margin-top:9px;font-size:.85rem;color:rgba(241,239,232,.55)}
.mini{width:100%;border-collapse:collapse;font-size:.9rem}
.mini td{padding:9px 0;border-bottom:1px solid var(--line-dark);color:rgba(241,239,232,.8)}
.mini tr:last-child td{border-bottom:0;color:rgba(241,239,232,.55)}
.mini td:nth-child(2){font-family:var(--mono);font-size:.8rem;color:rgba(241,239,232,.5);white-space:nowrap;padding-left:12px}
.mini td.r{text-align:right;font-family:var(--mono);font-variant-numeric:tabular-nums;color:var(--cream);white-space:nowrap}
.dnote{
  font-family:var(--mono);font-size:.75rem;letter-spacing:.06em;color:rgba(241,239,232,.45);
  margin:16px 0 0;padding-left:14px;border-left:2px solid var(--amber);line-height:1.7;
}

@media (max-width:1080px){
  .stage{grid-template-columns:minmax(0,1fr)}
  .phone{margin-inline:auto}
  .dash .body{grid-template-columns:minmax(0,1fr)}
}
@media (max-width:640px){
  .kpis{grid-template-columns:1fr}
  .dtabs button{flex:1 1 100%;justify-content:center}
  .thread{height:430px}
}
"""

JS_HEAD = """
/* ---------------------------------------------------------------------------
   Conversation player.

   The default scenario is already in the page as markup; this replaces it with
   a timed replay of the same data. Under prefers-reduced-motion the thread and
   the rail are painted complete, with no typing indicators and no waiting.
--------------------------------------------------------------------------- */
(function(){
  "use strict";
  var DATA = """

JS_TAIL = r""";
  var reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  var thread = document.getElementById("thread");
  var rail = document.getElementById("rail");
  var title = document.getElementById("scTitle");
  var sub = document.getElementById("scSub");
  var tabs = document.getElementById("sctabs");
  if (!thread || !rail) return;

  var timers = [], current = 0, playing = false;
  function clearTimers(){ timers.forEach(clearTimeout); timers = []; }
  function after(ms, fn){ timers.push(setTimeout(fn, ms)); }

  function bubble(m){
    if (m.who === "day"){
      var d = document.createElement("div");
      d.className = "daysep"; d.textContent = m.text; return d;
    }
    if (m.who === "sys"){
      var s = document.createElement("div");
      s.className = "sysmsg"; s.textContent = m.text; return s;
    }
    var b = document.createElement("div");
    b.className = "bub " + m.who;
    if (m.dir){ b.setAttribute("dir", m.dir); b.setAttribute("lang", m.lang); }
    b.appendChild(document.createTextNode(m.text));
    if (m.t){
      var t = document.createElement("span");
      t.className = "t"; t.textContent = m.t; b.appendChild(t);
    }
    return b;
  }

  function railItem(m, live){
    var li = document.createElement("li");
    if (!live) li.className = "on";
    var b = document.createElement("b"); b.textContent = m.rail[0];
    var s = document.createElement("span"); s.textContent = m.rail[1];
    li.appendChild(b); li.appendChild(s);
    return li;
  }

  function toBottom(){ thread.scrollTop = thread.scrollHeight; }

  function paint(sc){
    thread.innerHTML = ""; rail.innerHTML = "";
    sc.msgs.forEach(function(m){
      m.dir = sc.dir; m.lang = sc.lang;
      thread.appendChild(bubble(m));
      if (m.rail) rail.appendChild(railItem(m, false));
    });
    toBottom();
  }

  function play(i){
    var sc = DATA[i];
    clearTimers();
    title.textContent = sc.title;
    sub.textContent = sc.sub;
    if (reduce){ paint(sc); playing = false; return; }

    thread.innerHTML = ""; rail.innerHTML = "";
    var railEls = [];
    sc.msgs.forEach(function(m){
      if (m.rail){ var li = railItem(m, true); rail.appendChild(li); railEls.push(li); }
      else railEls.push(null);
    });

    playing = true;
    var clock = 260;
    sc.msgs.forEach(function(m, n){
      var wait = m.typing || 0;
      if (wait){
        clock += 300;
        (function(at){
          after(at, function(){
            var tp = document.createElement("div");
            tp.className = "typing"; tp.id = "tp";
            tp.innerHTML = "<i></i><i></i><i></i>";
            thread.appendChild(tp); toBottom();
          });
        })(clock);
        clock += wait;
      } else {
        clock += (n === 0 ? 0 : 620);
      }
      (function(at, msg, li){
        after(at, function(){
          var tp = document.getElementById("tp");
          if (tp) tp.remove();
          msg.dir = sc.dir; msg.lang = sc.lang;
          thread.appendChild(bubble(msg));
          if (li) li.classList.add("on");
          toBottom();
          if (msg === sc.msgs[sc.msgs.length - 1]) playing = false;
        });
      })(clock, m, railEls[n]);
    });
  }

  /* start when the phone is actually on screen, not on page load */
  var started = false;
  if ("IntersectionObserver" in window && !reduce){
    var io = new IntersectionObserver(function(en){
      if (en[0].isIntersecting && !started){ started = true; play(current); io.disconnect(); }
    }, {threshold:.35});
    io.observe(thread);
  } else { paint(DATA[0]); }

  if (tabs) tabs.addEventListener("click", function(e){
    var b = e.target.closest("button[role=tab]"); if (!b) return;
    [].forEach.call(tabs.querySelectorAll("button[role=tab]"), function(t){
      t.setAttribute("aria-selected", t === b ? "true" : "false");
      t.setAttribute("tabindex", t === b ? "0" : "-1");
    });
    current = +b.getAttribute("data-i");
    started = true;
    play(current);
    if (typeof gtag === "function") gtag("event","demo_scenario",{scenario:DATA[current].id});
  });

  var again = document.getElementById("again");
  if (again) again.addEventListener("click", function(){ started = true; play(current); });

  /* demo tabs (conversation / dashboard) --------------------------------- */
  var dt = document.getElementById("dtabs");
  function selectDemo(b){
    if (!dt || !b) return;
    [].forEach.call(dt.querySelectorAll("button[role=tab]"), function(t){
      var on = t === b;
      t.setAttribute("aria-selected", on ? "true" : "false");
      t.setAttribute("tabindex", on ? "0" : "-1");
      document.getElementById(t.getAttribute("aria-controls")).hidden = !on;
    });
    if (b.id === "dtab1" && !playing) play(current);
  }
  if (dt) dt.addEventListener("click", function(e){
    var b = e.target.closest("button[role=tab]"); if (!b) return;
    selectDemo(b);
    if (typeof gtag === "function") gtag("event","demo_tab",{demo:b.id});
  });

  /* Deep links. The site nav points every page at /en/demo/#dash, but the
     dashboard is a tab panel that starts hidden - a bare fragment would land
     on the conversation demo with nothing to show. Map the friendly names
     onto their tab buttons and scroll the section into view ourselves. */
  var HASHTAB = {"#dash":"dtab2","#dashboard":"dtab2","#demo2":"dtab2",
                 "#agent":"dtab1","#demo1":"dtab1"};
  function fromHash(smooth){
    var id = HASHTAB[location.hash]; if (!id) return;
    selectDemo(document.getElementById(id));
    var s = document.getElementById("demos");
    if (s) s.scrollIntoView({block:"start", behavior: smooth ? "smooth" : "auto"});
  }
  fromHash(false);
  addEventListener("hashchange", function(){ fromHash(true); });
})();
"""

JS = JS_HEAD + json.dumps(SCENARIOS, ensure_ascii=False) + JS_TAIL


def _static_thread(sc):
    """Scenario one, rendered as markup, for the no-JS case."""
    out = []
    for m in sc["msgs"]:
        if m["who"] == "day":
            out.append(f'<div class="daysep">{m["text"]}</div>')
        elif m["who"] == "sys":
            out.append(f'<div class="sysmsg">{m["text"]}</div>')
        else:
            rtl = f' dir="{sc["dir"]}" lang="{sc["lang"]}"' 
            t = f'<span class="t">{m["t"]}</span>' if m.get("t") else ""
            out.append(f'<div class="bub {m["who"]}"{rtl}>{m["text"]}{t}</div>')
    return "\n        ".join(out)


def _static_rail(sc):
    return "\n        ".join(
        f'<li><b>{m["rail"][0]}</b><span>{m["rail"][1]}</span></li>'
        for m in sc["msgs"] if m.get("rail"))


def body():
    first = SCENARIOS[0]
    sctabs = "".join(
        f'<button type="button" role="tab" data-i="{i}" '
        f'aria-selected="{"true" if i == 0 else "false"}" tabindex="{0 if i == 0 else -1}">'
        f'<em>{i+1:02d}</em>{s["tab"]}</button>'
        for i, s in enumerate(SCENARIOS))

    return f"""<main id="main">

<section class="phero s-panel grain">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span>Demos</p>
    <h1 class="h1">Watch it answer a buyer</h1>
    <p class="lede">Not a video and not a slide deck. This is the same conversation logic and the same
      screen an owner gets, running here in the page. The company is fictional and so are its numbers &mdash;
      everything else is the real behaviour.</p>
  </div>
</section>

<section class="s-dark grain" id="demos">
  <div class="wrap">
    <div class="dtabs" id="dtabs" role="tablist" aria-label="Choose a demo">
      <button type="button" role="tab" id="dtab1" aria-controls="demo1" aria-selected="true" tabindex="0"><em>01</em>The buyer agent</button>
      <button type="button" role="tab" id="dtab2" aria-controls="demo2" aria-selected="false" tabindex="-1"><em>02</em>The owner dashboard</button>
    </div>

    <!-- ------------------------------------------------ demo 1: the agent -->
    <div class="stage" id="demo1" role="tabpanel" aria-labelledby="dtab1">
      <div>
        <div class="phone">
          <div class="bar">
            <span class="av" aria-hidden="true">&#10038;</span>
            <div>
              <b>Gulf Lubricants &amp; Parts</b>
              <span><i></i>Answers in seconds</span>
            </div>
          </div>
          <div class="thread" id="thread" aria-live="polite" aria-label="Demo conversation">
        {_static_thread(first)}
          </div>
        </div>
        <div class="replay">
          <button type="button" id="again">Play again</button>
          <span>Fictional company, real behaviour</span>
        </div>
      </div>

      <div class="rail">
        <div class="dtabs sub" id="sctabs" role="tablist" aria-label="Choose a conversation" style="margin-bottom:26px">
          {sctabs}
        </div>
        <h3 id="scTitle">{first["title"]}</h3>
        <p class="sub" id="scSub">{first["sub"]}</p>
        <p class="lbl"><span class="star">{STAR}</span>What the system did</p>
        <ul class="steps2" id="rail">
        {_static_rail(first)}
        </ul>
        <div class="btn-row" style="margin-top:30px">
          <a class="btn btn-wa" href="{WA}&text=Hello%20Nahid%2C%20I%20watched%20the%20buyer%20agent%20demo%20-%20can%20it%20answer%20from%20my%20stock%20list%3F">{WA_ICON}<span>Ask it about my stock</span></a>
          <a class="btn btn-ghost" href="/en/services/#price">What it costs</a>
        </div>
      </div>
    </div>

    <!-- -------------------------------------------- demo 2: the dashboard -->
    <div class="stage" id="demo2" role="tabpanel" aria-labelledby="dtab2" hidden
         style="grid-template-columns:minmax(0,1fr)">
      <div>
        <div class="dash">
          <div class="head">
            <b>Gulf Lubricants &amp; Parts &mdash; this month</b>
            <span class="live"><i></i>Updated 4 minutes ago</span>
          </div>
          <div class="body">
            <div>
              <div class="kpis">
                <div class="kpi"><span>Revenue MTD</span>
                  <b><span data-count="109400" data-pre="OMR "></span></b><i>&uarr; 12% on last month</i></div>
                <div class="kpi"><span>Gross profit</span>
                  <b><span data-count="41900" data-pre="OMR "></span></b><i>38.3% margin</i></div>
                <div class="kpi"><span>Cash collected</span>
                  <b><span data-count="72150" data-pre="OMR "></span></b><i class="down">OMR 37,250 overdue</i></div>
              </div>
              <div class="dchart">
                <h4>Gross profit by week &mdash; OMR</h4>
                <svg viewBox="0 0 560 170" style="width:100%;height:auto;display:block" role="img"
                     aria-label="Gross profit by week: 8,200, 9,400, 7,100, 11,300, 9,900, 12,400, 10,800, 13,200">
                  <g fill="rgba(241,239,232,.18)">
                    <rect x="4"   y="86"  width="58" height="60" rx="4"/>
                    <rect x="74"  y="70"  width="58" height="76" rx="4"/>
                    <rect x="144" y="100" width="58" height="46" rx="4"/>
                    <rect x="214" y="46"  width="58" height="100" rx="4"/>
                    <rect x="284" y="63"  width="58" height="83" rx="4"/>
                    <rect x="354" y="32"  width="58" height="114" rx="4"/>
                    <rect x="424" y="53"  width="58" height="93" rx="4"/>
                  </g>
                  <rect x="494" y="22" width="58" height="124" rx="4" fill="#D89234"/>
                  <line x1="0" y1="146" x2="560" y2="146" stroke="rgba(241,239,232,.16)" stroke-width="1"/>
                  <text x="4" y="164" fill="rgba(241,239,232,.45)" font-family="IBM Plex Mono, monospace" font-size="11">W1</text>
                  <text x="523" y="164" fill="#D89234" font-family="IBM Plex Mono, monospace" font-size="11" text-anchor="middle">This week</text>
                </svg>
              </div>
              <div class="dchart" style="margin-top:18px">
                <h4>Oldest unpaid &mdash; who to call first</h4>
                <table class="mini">
                  <tr><td>Al Batinah Contracting</td><td>112 days</td><td class="r">OMR 14,800</td></tr>
                  <tr><td>Sohar Marine Services</td><td>96 days</td><td class="r">OMR 9,250</td></tr>
                  <tr><td>Muscat Fleet Care</td><td>61 days</td><td class="r">OMR 6,400</td></tr>
                  <tr><td>Three others under 45 days</td><td>&mdash;</td><td class="r">OMR 6,800</td></tr>
                </table>
              </div>
              <p class="dnote">Sample data from a fictional distributor. On a real build these read from
                the systems you already run &mdash; the accounting file, the stock sheet, the WhatsApp thread.</p>
            </div>

            <div class="alerts">
              <h4>What needs you today</h4>
              <div class="alert red">
                <b>Cash &mdash; act this week</b>
                <p>OMR 37,250 is overdue across 6 invoices. Two of them are past 90 days and both are with
                  the same customer.</p>
                <em>Suggested: hold new credit orders for that account until one clears.</em>
              </div>
              <div class="alert">
                <b>Stock &mdash; money asleep</b>
                <p>OMR 6,900 sits in 4 SKUs that have not moved in 90 days, costing about OMR 350 a month
                  in warehouse space.</p>
                <em>Suggested: clear at cost. The space is worth more than the margin.</em>
              </div>
              <div class="alert green">
                <b>Leads &mdash; answered without you</b>
                <p>18 buyer inquiries arrived after hours this month. All 18 were answered; 5 became
                  quotes and 2 have already paid.</p>
                <em>Nothing to do. This is the part that used to be silence.</em>
              </div>
            </div>
          </div>
        </div>
        <div class="btn-row" style="margin-top:28px">
          <a class="btn btn-wa" href="{WA}&text=Hello%20Nahid%2C%20I%20want%20a%20dashboard%20like%20the%20demo%20-%20built%20on%20my%20own%20numbers.">{WA_ICON}<span>Build this on my numbers</span></a>
          <a class="btn btn-ghost" href="/en/simulators/">Run my numbers first</a>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="s-cream grain">
  <div class="wrap">
    <div class="asterism"><span>{STAR}</span></div>
    <p class="eyebrow"><span class="star">{STAR}</span>What a demo cannot show you</p>
    <h2 class="h2">Three things I would rather say here than in a sales call</h2>
    <div class="grid g3" data-stagger style="margin-top:clamp(28px,4vw,44px)">
      <div class="card">
        <span class="n">01</span>
        <h3>It answers from your data or not at all</h3>
        <p>Every price and every stock figure above came from a list. The agent is not inventing an
          answer &mdash; when it has no source for one, it says so and hands the buyer to you.</p>
      </div>
      <div class="card">
        <span class="n">02</span>
        <h3>The handover is a rule, not a mood</h3>
        <p>Invoice, negotiation, complaint, anything it is unsure of &mdash; those are routed to a human by
          a rule you set. That boundary is the difference between a system and a gamble.</p>
      </div>
      <div class="card">
        <span class="n">03</span>
        <h3>Your buyers' data stays accountable</h3>
        <p>Under Oman's PDPL a conversation like this is personal data. Consent, purpose and storage are
          designed in at the start, not bolted on after someone asks.</p>
      </div>
    </div>
  </div>
</section>

</main>
"""


META = dict(
    slug="demos",
    title="Demos | Watch the buyer agent answer — AI Profit Lab",
    desc=("A live demo of the WhatsApp buyer agent answering in English and Arabic after hours, and of "
          "the owner dashboard. Fictional company, real behaviour."),
    nav="/en/demos/",
    next=("Next", "Talk to me", "/en/contact/"),
    schema="""{
  "@context":"https://schema.org",
  "@type":"WebPage",
  "name":"AI Profit Lab — product demos",
  "url":"https://aiprofitlab.io/en/demos/",
  "description":"Interactive demonstrations of the WhatsApp buyer agent and the live owner dashboard.",
  "inLanguage":"en",
  "publisher":{"@type":"Organization","name":"AI Profit Lab","legalName":"Lotus Gulf International"}
}""",
)
