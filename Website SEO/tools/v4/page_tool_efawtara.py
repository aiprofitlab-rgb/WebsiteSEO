#!/usr/bin/env python3
"""Free tool 1 - Oman e-invoicing (Fawtara) 2027.

The plain-language layer around Decision 189/2026, not a competitor to the Tax
Authority's own rollout checker. Three things a VAT-registered Omani business
actually wants: how long is left, which of the two dates is mine, and what do I
have to change. Everything else on the page exists to make those three honest.

Design rules this page inherits from the free-tools plan, and must keep:

  * 100% client-side. There is no backend, no form post and no fetch. The
    phase answers and the checklist ticks never leave the browser - the only
    place they are kept is localStorage, which is this browser and nowhere
    else. The page says so, and the claim has to survive DevTools > Network.
  * It is NOT a compliance checker and must never read like one. The OTA
    publishes the authoritative one at OTA_CHECKER; every result on this page
    ends by pointing at it.
  * Nothing here is sold. The one commercial sentence lives in the FAQ, says
    plainly that we are not an accredited e-invoicing provider, and names the
    part of the problem we do solve.

Every dated fact is in FACTS below with a visible LAST_VERIFIED. The OTA has
already moved this timeline once (the pre-Decision-189 dates were different),
so a stale constant here is the page's main failure mode: it goes wrong
silently, with no error anywhere. Re-verify against the sources in SOURCES
before publishing, and again every quarter.
"""
import json

from kit import STAR

# ==========================================================================
# THE FACTS - one block, one date, one place to fix.
#
# Verified 2026-09-10 against the two independent sources in SOURCES, plus a
# live check that OTA_CHECKER answers 200. Phase boundary wording is the
# careful part: both sources say Phase 1 is supplies EXCEEDING OMR 5m and
# Phase 2 is supplies NOT EXCEEDING it, so a business at exactly OMR 5m is
# Phase 2. The page uses "more than" / "OMR 5m or less" for that reason.
# ==========================================================================
LAST_VERIFIED = "10 September 2026"

FACTS = {
    "decision":      "Decision 189/2026",
    "gazette":       "Official Gazette 1660",
    "gazette_date":  "9 August 2026",
    "pilot_when":    "August 2026",
    "pilot_who":     "about 100 large taxpayers, notified directly by the Tax Authority",
    # ISO dates drive the countdown; the human strings are what the page says.
    # Both come from here so a moved deadline is a one-line edit.
    "phase1_iso":    "2027-04-01",
    "phase1_human":  "1 April 2027",
    "phase2_iso":    "2027-10-01",
    "phase2_human":  "1 October 2027",
    # Oman is UTC+4 and does not observe DST, so the deadline is a fixed
    # offset rather than the visitor's midnight - someone reading this in
    # London must see the Muscat deadline, not their own.
    "tz_offset":     "+04:00",
    "big_threshold": "OMR 5 million",
    "vat_mandatory": "OMR 38,500",
    "vat_voluntary": "OMR 19,250",
    "formats":       "UBL 2.1 XML built to the PINT Oman specification, or PDF/A-3",
    "ota_checker":   "https://tms.taxoman.gov.om/portal/rollout-checking",
    "ota_portal":    "https://tms.taxoman.gov.om/portal/",
    "fawtara":       "https://fawtara.taxoman.gov.om/",
}

# Named separately because they are quoted in prose as well as in the JS, and
# a figure typed twice is a figure that will disagree with itself one day.
F = FACTS

SOURCES = [
    ("Decision 189/2026 and the two dates, in law",
     "https://www.e-invoice.app/blog/oman-decision-189-2026-e-invoicing-dates"),
    ("Oman revises its mandatory e-invoicing timeline - Comarch",
     "https://www.comarch.com/trade-and-services/data-management/legal-regulation-changes/"
     "oman-revises-mandatory-e-invoicing-implementation-timeline/"),
    ("E-invoicing in Oman: timeline, requirements, format - ClearTax",
     "https://www.cleartax.com/om/e-invoicing-oman"),
]

# The twelve, in the order a business would actually do them: know your date,
# then get your own house in order, then talk to a vendor. Each is one action
# with an owner, not a topic. Text is duplicated nowhere - the JS reads the
# rendered DOM for the counter, and the print view is the same markup.
CHECKLIST = [
    ("Confirm you are VAT-registered, and have your VAT identification number to hand.",
     "Everything below follows from this one fact. If you are not registered, none of it applies yet."),
    ("Check your phase on the Tax Authority&rsquo;s own rollout checker, and write the date down.",
     "The tool on this page is a plain-language guide. The OTA&rsquo;s checker is the authority."),
    ("Know your annual supplies figure.",
     "That number &mdash; not your headcount, not your capital &mdash; is what decides which of the two dates is yours."),
    ("Name one person who owns e-invoicing in your business.",
     "A date with no owner slips. This does not have to be a finance person; it has to be one person."),
    ("Get every invoice you issue out of one system.",
     "A parallel spreadsheet, or an invoice someone types by hand when the system is awkward, has nowhere to go after your date."),
    ("Make your invoice numbers sequential and unique, with none ever re-used.",
     "A duplicate or a gap you patched later is a validation failure once invoices are machine-checked."),
    ("Collect and verify your customers&rsquo; legal names and VAT numbers now.",
     "They stop being free text on a page and become fields that either validate or fail. Fixing 400 customer records in the week before your date is not a plan."),
    ("Ask your accounting or invoicing software vendor, in writing, what their Oman e-invoicing plan is.",
     "&ldquo;We are working on it&rdquo; in a phone call is not an answer you can hold them to."),
    ("Ask that same vendor who connects you to an accredited service provider &mdash; them, or you.",
     "This is the question most vendors are vaguest about, and the one that decides how much work lands on your desk."),
    ("Confirm with your accountant whether your invoices need Arabic detail as well as English.",
     "Worth settling early: it changes how your invoice template is built, not just how it is sent."),
    ("Decide where invoices are stored and how you would retrieve one.",
     "For the whole retention period the VAT law requires &mdash; confirm that period with your accountant rather than guessing it."),
    ("Put your phase date minus 90 days in the calendar.",
     "That is the day you should be <em>testing</em>, not the day you start. Everything above should be done by then."),
]


CSS = """
/* =========================================================== tool shell */
/* Shared by every page under /en/tools/. Kept in this module for now
   because there is exactly one tool; the day a second one needs it, this
   block moves to a tool_kit.py and both import it rather than copying it. */
.toolbar{
  display:flex;flex-wrap:wrap;gap:10px 22px;align-items:center;
  font-family:var(--mono);font-size:.78rem;letter-spacing:.1em;text-transform:uppercase;
  color:var(--muted);margin:0 0 clamp(20px,3vw,30px);
}
.toolbar span{display:inline-flex;align-items:center;gap:8px}
.toolbar b{font-weight:500;color:var(--teal-950)}
.s-dark .toolbar,.s-teal .toolbar{color:rgba(241,239,232,.6)}
.s-dark .toolbar b,.s-teal .toolbar b{color:var(--cream)}

/* The privacy claim. It is a load-bearing sentence, so it is a component and
   not a paragraph someone can quietly soften. */
.local{
  display:flex;gap:14px;align-items:flex-start;
  border:1px solid var(--line);border-radius:14px;background:var(--white);
  padding:16px 18px;margin:clamp(22px,3vw,32px) 0 0;
}
.local svg{width:22px;height:22px;flex:none;fill:var(--teal);margin-top:2px}
.local p{margin:0;font-size:.94rem;line-height:1.6;color:var(--muted)}
.local b{color:var(--teal-950);font-weight:500}
.s-dark .local{background:rgba(241,239,232,.045);border-color:var(--line-dark)}
.s-dark .local p{color:rgba(241,239,232,.72)}
.s-dark .local b{color:var(--cream)}
.s-dark .local svg{fill:var(--amber-bright)}

/* ============================================================= countdown */
.cd{
  background:rgba(7,43,34,.55);border:1px solid var(--line-dark);border-radius:20px;
  padding:clamp(24px,3.2vw,38px);
}
.cd-cap{
  display:block;font-family:var(--mono);font-size:.76rem;letter-spacing:.15em;text-transform:uppercase;
  color:rgba(241,239,232,.55);margin:0 0 8px;
}
.cd-date{
  display:block;font-family:var(--display);font-size:clamp(1.8rem,4vw,2.8rem);line-height:1.05;
  color:var(--cream);margin:0 0 22px;
}
.cd-date em{font-style:normal;color:var(--amber-bright)}
.cd-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.cd-grid div{
  border:1px solid var(--line-dark);border-radius:14px;padding:14px 6px;text-align:center;
  background:rgba(7,43,34,.5);
}
.cd-grid b{
  display:block;font-family:var(--mono);font-size:clamp(1.5rem,4.4vw,2.35rem);line-height:1.1;
  color:var(--amber-bright);font-variant-numeric:tabular-nums;font-weight:500;
}
.cd-grid span{
  display:block;font-family:var(--mono);font-size:.66rem;letter-spacing:.13em;text-transform:uppercase;
  color:rgba(241,239,232,.5);margin-top:6px;
}
.cd-note{margin:20px 0 0;font-size:.9rem;line-height:1.6;color:rgba(241,239,232,.6)}
.cd-note a{color:var(--amber-bright)}

/* the two-phase strip under the countdown */
.phases{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:22px 0 0}
.phases div{border:1px solid var(--line-dark);border-radius:14px;padding:16px 18px}
.phases div.on{border-color:var(--amber);background:rgba(186,117,23,.1)}
.phases b{
  display:block;font-family:var(--mono);font-size:.72rem;letter-spacing:.13em;text-transform:uppercase;
  color:var(--amber-pale);font-weight:500;margin-bottom:6px;
}
.phases strong{display:block;font-family:var(--display);font-size:1.22rem;color:var(--cream);font-weight:400}
.phases span{display:block;font-size:.86rem;line-height:1.5;color:rgba(241,239,232,.6);margin-top:5px}

/* ============================================================ phase quiz */
.quiz{display:grid;grid-template-columns:1fr 1fr;gap:clamp(20px,3vw,40px);align-items:start}
.qbox,.qout{
  background:rgba(241,239,232,.045);border:1px solid var(--line-dark);border-radius:18px;
  padding:clamp(22px,2.8vw,32px);
}
.qout{background:rgba(7,43,34,.55)}
.qlbl{
  font-family:var(--mono);font-size:.76rem;letter-spacing:.16em;text-transform:uppercase;
  color:var(--amber-bright);margin:0 0 20px;display:flex;align-items:center;gap:9px;
}
fieldset.q{border:0;margin:0 0 26px;padding:0}
fieldset.q:last-of-type{margin-bottom:0}
fieldset.q legend{
  padding:0;margin:0 0 14px;font-size:1.02rem;line-height:1.5;color:var(--cream);
}
fieldset.q legend i{display:block;font-style:normal;font-size:.85rem;color:rgba(241,239,232,.55);margin-top:5px}
.opts{display:flex;flex-wrap:wrap;gap:9px}
.opts label{
  display:inline-flex;align-items:center;gap:9px;cursor:pointer;
  font-family:var(--mono);font-size:.78rem;letter-spacing:.07em;text-transform:uppercase;
  color:rgba(241,239,232,.75);background:transparent;border:1px solid var(--line-dark);
  border-radius:99px;padding:9px 16px;transition:color .2s,border-color .2s,background .2s;
}
.opts label:hover{color:var(--cream);border-color:var(--amber)}
.opts input{position:absolute;opacity:0;width:1px;height:1px}
.opts label:has(input:checked){background:var(--cream);color:var(--teal-950);border-color:var(--cream)}
/* :has() is unsupported on a small tail of browsers, so the script also sets
   this class - the selected state must never depend on one of the two. */
.opts label.sel{background:var(--cream);color:var(--teal-950);border-color:var(--cream)}
.opts input:focus-visible+span{outline:2px solid var(--amber);outline-offset:4px;border-radius:3px}

.qverdict{
  display:block;font-family:var(--mono);font-size:.76rem;letter-spacing:.15em;text-transform:uppercase;
  color:rgba(241,239,232,.55);margin:0 0 6px;
}
.qphase{
  display:block;font-family:var(--display);font-size:clamp(1.7rem,3.6vw,2.4rem);line-height:1.1;
  color:var(--amber-bright);margin:0 0 4px;
}
.qwhen{display:block;font-family:var(--mono);font-size:1.02rem;color:var(--cream);margin:0 0 18px}
.qwhy{margin:0 0 20px;font-size:.98rem;line-height:1.65;color:rgba(241,239,232,.78)}
.qwhy:last-child{margin-bottom:0}

/* ============================================================= checklist */
.ck{list-style:none;margin:0;padding:0;counter-reset:ck}
.ck li{
  position:relative;border-bottom:1px solid var(--line);padding:0;
}
.ck li:first-child{border-top:1px solid var(--line)}
.ck label{
  display:grid;grid-template-columns:auto 1fr;gap:16px;align-items:start;
  padding:18px 4px;cursor:pointer;
}
.ck input{position:absolute;opacity:0;width:1px;height:1px}
.ck .box{
  width:26px;height:26px;border:1.5px solid var(--line);border-radius:7px;flex:none;
  background:var(--white);position:relative;margin-top:2px;transition:border-color .2s,background .2s;
}
.ck .box::after{
  content:"";position:absolute;left:8px;top:5px;width:8px;height:14px;
  border-right:2.5px solid var(--white);border-bottom:2.5px solid var(--white);
  transform:rotate(42deg) scale(.4);opacity:0;transition:opacity .18s,transform .18s var(--ease);
}
.ck label:hover .box{border-color:var(--amber)}
.ck input:checked+.box{background:var(--teal);border-color:var(--teal)}
.ck input:checked+.box::after{opacity:1;transform:rotate(42deg) scale(1)}
.ck input:focus-visible+.box{outline:2px solid var(--amber);outline-offset:3px}
.ck .txt b{
  display:block;font-weight:500;font-size:1.04rem;line-height:1.45;color:var(--teal-950);
}
.ck .txt b::before{
  counter-increment:ck;content:counter(ck,decimal-leading-zero) "  ";
  font-family:var(--mono);font-weight:400;font-size:.8rem;color:var(--amber-text);
  letter-spacing:.1em;
}
.ck .txt span{display:block;font-size:.93rem;line-height:1.6;color:var(--muted);margin-top:6px}
.ck input:checked~.txt b{color:var(--muted);text-decoration:line-through;text-decoration-color:var(--line)}

.ckbar{
  display:flex;flex-wrap:wrap;gap:14px 20px;align-items:center;justify-content:space-between;
  margin:0 0 clamp(18px,2.4vw,26px);
}
.ckcount{font-family:var(--mono);font-size:.86rem;letter-spacing:.08em;color:var(--muted)}
.ckcount b{color:var(--teal-950);font-weight:500}
.ckbtns{display:flex;gap:10px;flex-wrap:wrap}
.ckbtns button{
  font-family:var(--mono);font-size:.74rem;letter-spacing:.09em;text-transform:uppercase;
  color:var(--teal-950);background:transparent;border:1px solid var(--line);border-radius:99px;
  padding:9px 16px;cursor:pointer;transition:color .2s,border-color .2s,background .2s;
}
.ckbtns button:hover{background:var(--teal-950);border-color:var(--teal-950);color:var(--cream)}

/* ========================================================== explanations */
.two{display:grid;grid-template-columns:1fr 1fr;gap:clamp(22px,3vw,44px);align-items:start}
.beforeafter{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:clamp(20px,3vw,30px) 0 0}
.beforeafter div{border:1px solid var(--line);border-radius:16px;padding:20px 22px;background:var(--white)}
.beforeafter div.after{border-color:var(--amber);background:var(--panel)}
.beforeafter h4{
  font-family:var(--mono);font-size:.74rem;font-weight:500;letter-spacing:.14em;text-transform:uppercase;
  color:var(--amber-text);margin:0 0 12px;
}
.beforeafter ul{margin:0;padding-inline-start:20px}
.beforeafter li{font-size:.96rem;line-height:1.6;color:var(--muted);margin-bottom:9px}
.beforeafter li:last-child{margin-bottom:0}
.beforeafter li b{color:var(--teal-950);font-weight:500}

.plainlist{list-style:none;margin:clamp(18px,2.6vw,26px) 0 0;padding:0;display:grid;gap:15px}
.plainlist li{position:relative;padding-inline-start:30px;font-size:1rem;line-height:1.62;color:var(--muted)}
.plainlist li::before{
  content:"";position:absolute;inset-inline-start:3px;top:.62em;width:12px;height:7px;
  border-inline-start:2px solid var(--amber);border-bottom:2px solid var(--amber);transform:rotate(-45deg);
}
.plainlist li b{color:var(--teal-950);font-weight:500}
.s-dark .plainlist li{color:rgba(241,239,232,.76)}
.s-dark .plainlist li b{color:var(--cream)}

.notclaim{
  border-inline-start:3px solid var(--alert);background:var(--white);border-radius:0 14px 14px 0;
  padding:20px 24px;margin:clamp(22px,3vw,32px) 0 0;
}
.notclaim p{margin:0;font-size:1rem;line-height:1.65;color:var(--muted)}
.notclaim p+p{margin-top:.8em}
.notclaim b{color:var(--teal-950);font-weight:500}

/* ------------------------------------------------------------------ faq */
.faq{border-top:1px solid var(--line)}
.faq details{border-bottom:1px solid var(--line)}
.faq summary{
  cursor:pointer;list-style:none;padding:22px 44px 22px 0;position:relative;
  font-family:var(--display);font-size:clamp(1.15rem,2vw,1.45rem);color:var(--teal-950);
}
.faq summary::-webkit-details-marker{display:none}
.faq summary::after{
  content:"";position:absolute;right:8px;top:50%;width:12px;height:12px;margin-top:-8px;
  border-right:1.5px solid var(--amber);border-bottom:1.5px solid var(--amber);
  transform:rotate(45deg);transition:transform .3s var(--ease);
}
.faq details[open] summary::after{transform:rotate(-135deg);margin-top:-3px}
.faq .ans{padding:0 0 24px;color:var(--muted);font-size:1.02rem;max-width:70ch;margin:0}
.faq .ans+.ans{padding-top:0;margin-top:-10px}
.faq summary:hover{color:var(--teal)}

/* --------------------------------------------------------- the fact box */
.facts-box{border:1px solid var(--line-dark);border-radius:18px;padding:clamp(22px,2.8vw,32px)}
.facts-box dl{margin:0;display:grid;grid-template-columns:auto 1fr;gap:12px 22px}
.facts-box dt{
  font-family:var(--mono);font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;
  color:rgba(241,239,232,.5);padding-top:.28em;
}
.facts-box dd{margin:0;font-size:.99rem;line-height:1.55;color:var(--cream)}
.facts-box dd em{font-style:normal;color:var(--amber-bright)}
.srcs{list-style:none;margin:22px 0 0;padding:22px 0 0;border-top:1px solid var(--line-dark);display:grid;gap:9px}
.srcs li{font-size:.9rem;line-height:1.5}
.srcs a{color:var(--amber-bright)}
.verified{
  font-family:var(--mono);font-size:.76rem;letter-spacing:.1em;text-transform:uppercase;
  color:rgba(241,239,232,.55);margin:18px 0 0;
}
.verified b{color:var(--amber-bright);font-weight:500}
.disclaimer{
  margin:clamp(20px,3vw,28px) 0 0;font-size:.93rem;line-height:1.65;color:rgba(241,239,232,.6);
}
.disclaimer a{color:var(--amber-bright)}

/* ---------------------------------------------------------- breakpoints */
@media (max-width:900px){
  .quiz,.two,.beforeafter,.phases{grid-template-columns:1fr}
}
@media (max-width:560px){
  .cd-grid{grid-template-columns:repeat(2,1fr)}
  .facts-box dl{grid-template-columns:1fr;gap:4px 0}
  .facts-box dt{padding-top:14px}
  .ck label{gap:12px}
  .ckbar{justify-content:flex-start}
}

/* ---------------------------------------------------------------- print
   The checklist is meant to be printed and carried into a meeting, so the
   print view is exactly three things: the two dates with yours marked, the
   phase result, and the twelve items. Sections opt IN by carrying .pr -
   opt-out was the first version and it printed six pages of explainer,
   because every section written afterwards has to remember to opt out and
   one of them will not.

   Colour is forced in ONE blanket rule rather than selector by selector.
   The first attempt listed the selectors it knew about and missed four, so
   the countdown label, both phase cards and the OTA disclaimer printed cream
   on white - i.e. invisible, with the disclaimer's link floating alone on the
   page. A dark section printed on white paper has to have every descendant
   re-coloured, so the rule that does it must not be a list. */
@media print{
  main>section{display:none!important}
  main>section.pr{display:block!important}

  /* everything on the paper is ink on white; the exceptions come after */
  main>section.pr,main>section.pr *{
    color:#111!important;background:none!important;background-color:transparent!important;
    border-color:#999!important;box-shadow:none!important;
  }
  main>section.pr{background:#fff!important;padding:10px 0 18px!important;break-inside:auto}
  html,body{background:#fff!important;color:#111!important;font-size:10.5pt}
  .wrap,.wrap-n{width:100%!important}
  .grain::before{display:none!important}
  .top,.mmenu,.foot,.pager,.skip,#aiden-root,.noprint,.btn-row,.ckbtns{display:none!important}

  /* Inside the phase section, only the verdict and the "the OTA is the
     authority" line are worth paper. The questions themselves are not: the
     radio state is a background colour a printer may drop anyway. */
  #phase .eyebrow,#phase .h2,#phase .lede,#phase .qbox{display:none!important}
  #phase .quiz{grid-template-columns:1fr!important;gap:0!important}
  /* "Answer the two questions below" is wrong on paper - they are not on it. */
  #cdNote{display:none!important}

  .cd,.qout,.cd-grid div,.phases div,.facts-box{border:1px solid #999!important;border-radius:8px!important}
  .cd,.qout{padding:14px 16px!important}
  .cd-grid{gap:8px!important}
  .cd-grid b{font-size:20pt!important}
  /* Which phase is yours has to survive the loss of the amber fill. */
  .phases div.on{border:2px solid #111!important}
  .phases div.on b::after{content:" - yours"}

  .ck li{break-inside:avoid}
  .ck .box{border:1.5px solid #111!important;print-color-adjust:exact;-webkit-print-color-adjust:exact}
  .ck input:checked+.box{background:#111!important;background-color:#111!important;border-color:#111!important}
  a{text-decoration:underline}
  .prfoot{display:block!important}
}
.prfoot{display:none}
"""


# --------------------------------------------------------------------------
# JS. Plain string, not an f-string: the constants are injected by .replace()
# so the CSS-like braces in the script never have to be doubled. Everything
# below runs on the visitor's device and nothing in it opens a connection -
# that is the page's central claim, so no fetch(), no XHR, no beacon, and no
# image ping may ever be added here.
# --------------------------------------------------------------------------
JS_TPL = r"""
(function(){
  "use strict";
  var F = __FACTS__;

  /* -------------------------------------------------------- countdown --
     One Date per phase, built from the ISO constants plus Oman's fixed
     +04:00 offset. A reader in London must see the Muscat deadline, not
     their own midnight, and Oman has no daylight saving to complicate it. */
  function omanDate(iso){ return new Date(iso + "T00:00:00" + F.tz_offset); }
  var TARGETS = { p1: omanDate(F.phase1_iso), p2: omanDate(F.phase2_iso) };
  var LABELS  = { p1: F.phase1_human, p2: F.phase2_human };

  var cdDate = document.getElementById("cdDate");
  var cdNote = document.getElementById("cdNote");
  var cells  = ["cdD","cdH","cdM","cdS"].map(function(id){ return document.getElementById(id); });
  var current = "p2";           /* the default: the date that catches everyone */
  var chosen  = false;          /* true once the quiz has picked the phase */
  var tick = null;

  /* The note has three states, and paint() has to write it in EVERY branch.
     The first version wrote it only when the date had passed, so a reader in
     mid-2027 who switched from Phase 1 (passed) back to Phase 2 (live) got a
     correct 152-day countdown under the words "This date has passed". A
     conditional that only ever sets text one way leaves the other way stale. */
  var NOTE_DEFAULT = cdNote ? cdNote.innerHTML : "";
  var NOTE_PASSED  = "This date has passed. If it is your phase, the obligation is already live " +
                     "&mdash; check your standing with the Tax Authority.";

  function pad(n){ return n < 10 ? "0" + n : String(n); }

  function paint(){
    var t = TARGETS[current], ms = t - new Date();
    var n = current === "p1" ? "1" : "2";
    if (cdDate) cdDate.innerHTML = "Phase " + n + " &middot; <em>" + LABELS[current] + "</em>";
    if (ms <= 0){
      /* The page outlives the deadline. Say so rather than counting up, and
         stop the timer so a passed date is not re-rendered every second. */
      cells.forEach(function(c){ if (c) c.textContent = "00"; });
      if (cdNote) cdNote.innerHTML = NOTE_PASSED;
      if (tick){ clearInterval(tick); tick = null; }
      return;
    }
    if (cdNote) cdNote.innerHTML = chosen
      ? "Counting to midnight in Muscat on " + LABELS[current] + ", when Phase " + n + " begins."
      : NOTE_DEFAULT;
    var s = Math.floor(ms / 1000);
    var d = Math.floor(s / 86400);
    cells[0] && (cells[0].textContent = String(d));
    cells[1] && (cells[1].textContent = pad(Math.floor(s % 86400 / 3600)));
    cells[2] && (cells[2].textContent = pad(Math.floor(s % 3600 / 60)));
    cells[3] && (cells[3].textContent = pad(s % 60));
  }

  function setPhase(which, fromQuiz){
    current = which;
    if (fromQuiz) chosen = true;
    ["p1","p2"].forEach(function(k){
      var el = document.getElementById("ph_" + k);
      if (el) el.classList.toggle("on", k === which);
    });
    paint();
    /* Restarted deliberately: paint() stops the timer when the date it was
       showing has passed, and switching to a date that has NOT passed has to
       start it again. */
    if (!tick) tick = setInterval(paint, 1000);
  }
  if (cells[0]) setPhase("p2", false);

  /* ------------------------------------------------------ the phase quiz --
     Two questions, six answers, four outcomes. Every outcome ends at the
     OTA's own checker: this is the plain-language layer, not the authority. */
  var CHECKER = '<a href="' + F.ota_checker + '" target="_blank" rel="noopener">the Tax Authority&rsquo;s ' +
                'rollout checker</a>';

  var OUTCOMES = {
    "no": {
      phase: "Not yet",
      when:  "No date applies to you today",
      cls:   "p2",
      why:   ["Decision 189/2026 obliges <b>VAT-registered</b> businesses. A business that is not " +
              "registered has nothing to do on either date.",
              "The thing to watch is the registration threshold, not the e-invoicing one. VAT " +
              "registration is mandatory once your taxable supplies pass <b>" + F.vat_mandatory +
              "</b> over a rolling twelve months, and voluntary from <b>" + F.vat_voluntary + "</b>. " +
              "Cross it and you register &mdash; and e-invoicing arrives with the registration, on " +
              "the <b>" + F.phase2_human + "</b> timetable."]
    },
    "yes-big": {
      phase: "Phase 1",
      when:  F.phase1_human,
      cls:   "p1",
      why:   ["Annual supplies of more than " + F.big_threshold + " puts you in the first mandatory " +
              "wave, six months ahead of everyone else.",
              "Confirm it against " + CHECKER + " before you plan around it. That checker reads your " +
              "actual VATIN; this page reads two answers you typed."]
    },
    "yes-small": {
      phase: "Phase 2",
      when:  F.phase2_human,
      cls:   "p2",
      why:   ["Annual supplies of " + F.big_threshold + " or less puts you in the second wave &mdash; " +
              "which is every remaining VAT-registered business in Oman. There is no turnover floor " +
              "below which this stops applying.",
              "Confirm it against " + CHECKER + " before you plan around it. That checker reads your " +
              "actual VATIN; this page reads two answers you typed."]
    },
    "yes-unsure": {
      phase: "Phase 1 or 2",
      when:  F.phase1_human + " or " + F.phase2_human,
      cls:   "p2",
      why:   ["You are VAT-registered, so one of the two dates is yours. Which one depends on a single " +
              "figure: whether your annual supplies are more than " + F.big_threshold + ".",
              "Your accountant can tell you in a minute, and " + CHECKER + " will tell you from your " +
              "VATIN. Until then, plan for <b>" + F.phase2_human + "</b> &mdash; the later of the two &mdash; " +
              "but do not assume it."]
    },
    "unsure": {
      phase: "Check first",
      when:  "Start with your VAT registration",
      cls:   "p2",
      why:   ["Whether you are registered for VAT is the question that decides everything else, and it " +
              "is not one to guess at. Your accountant knows, and it is on any tax invoice you have " +
              "ever issued.",
              "Once you know, come back &mdash; or go straight to " + CHECKER + ", which answers both " +
              "questions at once from your VATIN."]
    }
  };

  var q1 = null, q2 = null;
  var out = document.getElementById("qOut");

  function outcomeKey(){
    if (q1 === "no")     return "no";
    if (q1 === "unsure") return "unsure";
    if (q1 !== "yes")    return null;
    if (q2 === "yes")    return "yes-big";
    if (q2 === "no")     return "yes-small";
    if (q2 === "unsure") return "yes-unsure";
    return null;
  }

  function render(){
    if (!out) return;
    var key = outcomeKey();
    if (!key){
      out.innerHTML = '<span class="qverdict">Your date</span>' +
        '<span class="qphase">&mdash;</span>' +
        '<span class="qwhen">Answer both questions</span>' +
        '<p class="qwhy">Two questions, and the answer is one of two dates. Nothing you pick here is ' +
        'sent anywhere &mdash; there is no server behind this page to send it to.</p>';
      return;
    }
    var o = OUTCOMES[key];
    out.innerHTML = '<span class="qverdict">Your date</span>' +
      '<span class="qphase">' + o.phase + '</span>' +
      '<span class="qwhen">' + o.when + '</span>' +
      o.why.map(function(p){ return '<p class="qwhy">' + p + '</p>'; }).join("");
    setPhase(o.cls, true);
    /* The one measurement this page takes, and it carries no answer with it -
       only that the tool was used. gtag is defined by the shared head. */
    if (!render.sent && typeof gtag === "function"){
      render.sent = true;
      gtag("event", "tool_used", {tool_name: "oman-e-invoicing-2027", tool_step: "phase_answered"});
    }
  }

  Array.prototype.forEach.call(document.querySelectorAll(".opts input"), function(inp){
    inp.addEventListener("change", function(){
      Array.prototype.forEach.call(
        inp.form ? inp.form.querySelectorAll('.opts input[name="' + inp.name + '"]')
                 : document.querySelectorAll('.opts input[name="' + inp.name + '"]'),
        function(sib){ sib.closest("label").classList.toggle("sel", sib.checked); });
      if (inp.name === "q1") q1 = inp.value; else q2 = inp.value;
      render();
    });
  });
  render();

  /* -------------------------------------------------------- checklist --
     Ticks live in localStorage and nowhere else: this browser, this device,
     never a server. Wrapped in try/catch because a private window or a
     browser set to block site data throws on the accessor itself, and a
     checklist that cannot remember must still be a checklist that works. */
  var KEY = "apl.efawtara.checklist.v1";
  var boxes = Array.prototype.slice.call(document.querySelectorAll(".ck input"));
  var counter = document.getElementById("ckCount");

  function load(){
    try {
      var raw = localStorage.getItem(KEY);
      if (!raw) return;
      var on = JSON.parse(raw);
      if (Object.prototype.toString.call(on) !== "[object Array]") return;
      boxes.forEach(function(b, i){ b.checked = on.indexOf(i) > -1; });
    } catch(e){}
  }
  function save(){
    try {
      var on = [];
      boxes.forEach(function(b, i){ if (b.checked) on.push(i); });
      localStorage.setItem(KEY, JSON.stringify(on));
    } catch(e){}
  }
  function count(){
    var n = boxes.filter(function(b){ return b.checked; }).length;
    if (counter) counter.innerHTML = "<b>" + n + "</b> of <b>" + boxes.length + "</b> done";
  }
  load(); count();
  boxes.forEach(function(b){ b.addEventListener("change", function(){ save(); count(); }); });

  var reset = document.getElementById("ckReset");
  if (reset) reset.addEventListener("click", function(){
    boxes.forEach(function(b){ b.checked = false; });
    save(); count();
  });
  var printBtn = document.getElementById("ckPrint");
  if (printBtn) printBtn.addEventListener("click", function(){
    if (typeof gtag === "function"){
      gtag("event", "tool_output_saved", {tool_name: "oman-e-invoicing-2027", output_format: "print"});
    }
    window.print();
  });
})();
"""


def js():
    return JS_TPL.replace("__FACTS__", json.dumps(FACTS, ensure_ascii=False))


LOCK_ICON = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 1a5 5 0 0 0-5 5v3H6a2 2 0 0 0-2 '
             '2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V11a2 2 0 0 0-2-2h-1V6a5 5 0 0 0-5-5zm0 2a3 3 0 0 1 3 '
             '3v3H9V6a3 3 0 0 1 3-3zm0 11a2 2 0 0 1 1 3.7V20h-2v-2.3A2 2 0 0 1 12 14z"/></svg>')

FAQ = [
    ("Is a PDF invoice enough?",
     "No &mdash; not once your phase starts. A PDF you typed in Word, Excel or a design tool and then "
     "emailed or sent on WhatsApp is a picture of an invoice. A compliant e-invoice is a structured "
     "data file (%s), given a unique number and passed through a service provider accredited by the "
     "Tax Authority. Your customer can still be sent something readable; that readable copy just stops "
     "being the invoice." % F["formats"]),
    ("Do I have to do anything before %s?" % F["phase1_human"],
     "If you are in Phase 1, yes &mdash; that date is when you must already be issuing e-invoices, not "
     "when you start looking into it. If you are in Phase 2 your date is %s, but almost every item on "
     "the checklist above is work inside your own business: one invoicing system, clean numbering, "
     "verified customer VAT numbers. None of it depends on choosing a provider, and all of it takes "
     "longer than people expect." % F["phase2_human"]),
    ("I am not registered for VAT. Does this apply to me?",
     "Not today. The obligation follows VAT registration, and registration is mandatory once your "
     "taxable supplies pass %s over a rolling twelve months (voluntary from %s). If you cross that "
     "line you register for VAT, and e-invoicing comes with it."
     % (F["vat_mandatory"], F["vat_voluntary"])),
    ("Is there a size below which I am exempt?",
     "There is no turnover floor that exempts a VAT-registered business permanently. Phase 2 on %s is "
     "defined as everyone whose annual supplies are %s or less &mdash; which is the rest of the "
     "register. The law does let the Chairman of the Tax Authority grant a time-limited exemption on "
     "application, with documents and a clean filing record; that is a discretionary deferral for a "
     "set period, not a permanent carve-out, and it is not something to plan around."
     % (F["phase2_human"], F["big_threshold"])),
    ("What is Fawtara?",
     "Fawtara is the Tax Authority&rsquo;s e-invoicing platform &mdash; the system your invoices are "
     "validated and exchanged through, via an accredited service provider. It is the plumbing, not a "
     "product you buy off a shelf."),
    ("Which software should I buy?",
     "Nothing, yet. As at %s the Tax Authority had not published the list of accredited service "
     "providers, so anyone selling you an &ldquo;OTA-approved&rdquo; e-invoicing product today is "
     "ahead of the announcement. Spend the waiting time on the checklist instead: a business with one "
     "invoicing system, clean sequential numbering and verified customer VAT numbers can connect to a "
     "provider in weeks. A business running on spreadsheets cannot." % LAST_VERIFIED),
    ("Does AI Profit Lab sell an e-invoicing system?",
     "No. We are not an accredited service provider and this page is not selling one &mdash; if it "
     "were, the honest answer above would be a different answer. What we do build is the layer "
     "underneath: getting quotes, orders and invoices out of spreadsheets and WhatsApp threads and "
     "into one system, which is items 5 to 7 on the checklist and the part that takes months rather "
     "than weeks. If that is your problem, the price list is published."),
]


def _faq_html():
    out = []
    for q, a in FAQ:
        out.append(f"""      <details>
        <summary>{q}</summary>
        <p class="ans">{a}</p>
      </details>""")
    return "\n".join(out)


def _faq_schema():
    """FAQPage from the same seven questions the page renders, so the two can
    never disagree. Tags are stripped rather than re-typed for the same
    reason: a hand-written second copy of an answer is a second answer."""
    import re
    items = []
    for q, a in FAQ:
        plain = re.sub(r"<[^>]+>", "", a)
        items.append('{"@type":"Question","name":%s,"acceptedAnswer":{"@type":"Answer","text":%s}}'
                     % (json.dumps(_txt(q)), json.dumps(_txt(plain))))
    return ('{"@type":"FAQPage","@id":"https://aiprofitlab.io/en/tools/oman-e-invoicing-2027/#faq",'
            '"inLanguage":"en","mainEntity":[' + ",".join(items) + "]}")


def _txt(s):
    """HTML entities back to characters, for JSON-LD - schema wants text, and
    a literal &mdash; in a JSON string is what a parser would read."""
    import html
    return html.unescape(s)


def _checklist_html():
    rows = []
    for i, (title, note) in enumerate(CHECKLIST):
        rows.append(f"""    <li>
      <label>
        <input type="checkbox" id="ck{i}">
        <span class="box" aria-hidden="true"></span>
        <span class="txt"><b>{title}</b><span>{note}</span></span>
      </label>
    </li>""")
    return "\n".join(rows)


def _sources_html():
    return "\n".join(
        f'      <li><a href="{u}" target="_blank" rel="noopener nofollow">{t}</a></li>'
        for t, u in SOURCES)


def body():
    return f"""<main id="main">

<section class="phero s-panel grain">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span>Free tool &middot; No sign-up</p>
    <h1 class="h1">Oman e&#8209;invoicing: which date is yours</h1>
    <p class="lede">Every VAT-registered business in Oman has to issue structured electronic invoices
      by {F["phase2_human"]}. Two questions below tell you which of the two dates applies to you, how
      long is left, and the twelve things to have done before it arrives. Written in plain English,
      because the vendor blogs are not.</p>
    <div class="btn-row" style="margin-top:26px">
      <a class="btn btn-teal" href="#phase">Find my date</a>
      <a class="tlink" href="#checklist">Skip to the checklist <span class="arw">&rarr;</span></a>
    </div>
    <div class="local">
      {LOCK_ICON}
      <p><b>Nothing you type here leaves your browser.</b> There is no form, no sign-up and no server
        behind this tool &mdash; your answers and your ticks are worked out on your own device and
        never sent anywhere. Ticks are remembered in this browser only, so we cannot see them and
        neither can anyone else. The page counts <em>that</em> the tool was used, the way every page
        on this site is counted; it never sends <em>what</em> you picked. Open DevTools &rarr; Network
        and check.</p>
    </div>
  </div>
</section>

<!-- ------------------------------------------------------------ countdown -->
<section class="s-dark grain pad-s pr" id="countdown">
  <div class="wrap-n">
    <div class="cd">
      <span class="cd-cap">Time left until</span>
      <span class="cd-date" id="cdDate">Phase 2 &middot; <em>{F["phase2_human"]}</em></span>
      <div class="cd-grid">
        <div><b id="cdD">&ndash;&ndash;</b><span>Days</span></div>
        <div><b id="cdH">&ndash;&ndash;</b><span>Hours</span></div>
        <div><b id="cdM">&ndash;&ndash;</b><span>Minutes</span></div>
        <div><b id="cdS">&ndash;&ndash;</b><span>Seconds</span></div>
      </div>
      <p class="cd-note" id="cdNote">Counting to midnight in Muscat. Answer the two questions below and
        this switches to your phase.</p>
      <div class="phases">
        <div id="ph_p1">
          <b>Phase 1</b>
          <strong>{F["phase1_human"]}</strong>
          <span>Annual supplies of more than {F["big_threshold"]}.</span>
        </div>
        <div id="ph_p2">
          <b>Phase 2</b>
          <strong>{F["phase2_human"]}</strong>
          <span>{F["big_threshold"]} or less &mdash; every remaining VAT-registered business.</span>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- ----------------------------------------------------------- phase quiz -->
<section class="s-dark grain pr" id="phase">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span>Which phase am I in?</p>
    <h2 class="h2">Two questions</h2>
    <p class="lede">There are only two mandatory dates, and one figure decides which is yours.</p>

    <div class="quiz" style="margin-top:clamp(26px,3.4vw,40px)">
      <form class="qbox" id="qForm" onsubmit="return false">
        <p class="qlbl"><span class="star">{STAR}</span>Your answers</p>

        <fieldset class="q">
          <legend>Is your business registered for VAT in Oman?
            <i>Registration is mandatory above {F["vat_mandatory"]} of taxable supplies in a rolling
              twelve months.</i></legend>
          <div class="opts">
            <label><input type="radio" name="q1" value="yes"><span>Yes</span></label>
            <label><input type="radio" name="q1" value="no"><span>No</span></label>
            <label><input type="radio" name="q1" value="unsure"><span>Not sure</span></label>
          </div>
        </fieldset>

        <fieldset class="q">
          <legend>Are your annual supplies more than {F["big_threshold"]}?
            <i>Supplies, not profit &mdash; the total value of what you sell in a year.</i></legend>
          <div class="opts">
            <label><input type="radio" name="q2" value="yes"><span>Yes</span></label>
            <label><input type="radio" name="q2" value="no"><span>No</span></label>
            <label><input type="radio" name="q2" value="unsure"><span>Not sure</span></label>
          </div>
        </fieldset>
      </form>

      <div class="qout" id="qOut" aria-live="polite">
        <span class="qverdict">Your date</span>
        <span class="qphase">&mdash;</span>
        <span class="qwhen">Answer both questions</span>
        <p class="qwhy">Two questions, and the answer is one of two dates. Nothing you pick here is
          sent anywhere &mdash; there is no server behind this page to send it to.</p>
      </div>
    </div>

    <p class="disclaimer">This tool is a plain-language guide and deliberately not a compliance
      checker &mdash; the Tax Authority publishes the authoritative one, which reads your real VAT
      identification number rather than two answers you typed:
      <a href="{F["ota_checker"]}" target="_blank" rel="noopener">check your rollout phase on the OTA
      portal</a>. Where the two disagree, the OTA is right.</p>
  </div>
</section>

<!-- ------------------------------------------------------- what it means -->
<section class="s-cream grain">
  <div class="wrap-n">
    <div class="asterism"><span>{STAR}</span></div>
    <p class="eyebrow"><span class="star">{STAR}</span>In plain English</p>
    <h2 class="h2">What a compliant e&#8209;invoice actually is</h2>
    <p>An e-invoice is not a nicer PDF. It is a <b>structured data file</b> &mdash; {F["formats"]}
      &mdash; that a machine reads as data rather than as a picture of a page. It carries a unique
      invoice number, and it reaches your customer through a service provider accredited by the Tax
      Authority rather than straight out of your outbox.</p>
    <p>Your customer can still receive something they can read. That readable copy is now a by-product.
      The file the Tax Authority recognises is the invoice.</p>

    <div class="notclaim">
      <p><b>So a hand-made PDF is not compliant.</b> An invoice typed in Word, built in Excel, drawn in
        a design tool or photographed off a printed pad stops being a valid tax invoice on your phase
        date, no matter how correct the numbers on it are.</p>
      <p>That is worth saying plainly, because you will be sold tools between now and 2027 that produce
        a PDF and call it an e-invoice. The test is not what the document looks like. It is whether it
        went through an accredited channel in an approved format.</p>
    </div>
  </div>
</section>

<section class="s-panel grain">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span>What changes</p>
    <h2 class="h2">How you send an invoice, before and after</h2>
    <p class="lede">The arithmetic on your invoice does not change. The route it travels does.</p>
    <div class="beforeafter">
      <div>
        <h4>Today</h4>
        <ul>
          <li>You raise an invoice in whatever you use &mdash; software, a spreadsheet, a printed pad.</li>
          <li>You send it: <b>email, WhatsApp, print, hand it over.</b></li>
          <li>Your copy is your record. Nobody validates it as it goes.</li>
          <li>A mistake is fixed by re-issuing and telling the customer.</li>
        </ul>
      </div>
      <div class="after">
        <h4>From your phase date</h4>
        <ul>
          <li>Your system produces a <b>structured file</b> with a unique number.</li>
          <li>It goes out through an <b>accredited service provider</b> and the Fawtara platform.</li>
          <li>It is <b>validated as it goes</b> &mdash; a bad VAT number fails rather than looking untidy.</li>
          <li>Corrections and credit notes travel the same road, not around it.</li>
        </ul>
      </div>
    </div>
  </div>
</section>

<section class="s-cream grain">
  <div class="wrap-n">
    <p class="eyebrow"><span class="star">{STAR}</span>What happens to your process</p>
    <h2 class="h2">The five things that actually break</h2>
    <ul class="plainlist">
      <li><b>The second system.</b> The spreadsheet someone keeps &ldquo;because the software is
        awkward&rdquo;, or the invoice typed by hand for one difficult customer. Both have nowhere to go.</li>
      <li><b>Invoice numbering.</b> Sequential, unique, never re-used. Gaps you patched later and numbers
        borrowed from a different pad become validation failures instead of untidiness.</li>
      <li><b>Customer records.</b> Legal names and VAT numbers stop being free text and become fields
        that either pass or fail. Cleaning four hundred customer records the week before your date is
        not a plan.</li>
      <li><b>Who types invoices.</b> Whoever raises them needs to know the date their part of the job
        changes, and needs the new route to be the easy one. If the old way is quicker they will use it.</li>
      <li><b>Storage and retrieval.</b> You have to be able to produce a specific invoice on request,
        for the full retention period the VAT law requires. A folder of emailed PDFs is not that.</li>
    </ul>
    <div class="notclaim">
      <p><b>The one thing not to rush: buying something.</b> As at {LAST_VERIFIED} the Tax Authority had
        not yet published which service providers are accredited. Everything in the list above is work
        inside your own business, and none of it depends on that announcement &mdash; which is exactly
        why it is the work to do now.</p>
    </div>
  </div>
</section>

<!-- ------------------------------------------------------------ checklist -->
<section class="s-panel grain pr" id="checklist">
  <div class="wrap-n">
    <p class="prfoot mono" style="margin:0 0 14px;font-size:.8rem">Oman e&#8209;invoicing readiness
      &middot; prepared from aiprofitlab.io &middot; not tax advice</p>
    <p class="eyebrow"><span class="star">{STAR}</span>Readiness checklist</p>
    <h2 class="h2">Twelve things to have done</h2>
    <p class="lede noprint">Tick them off as you go. Print it, or save it as a PDF, and take it into the
      conversation with your accountant or your software vendor.</p>
    <div class="ckbar">
      <p class="ckcount" id="ckCount"><b>0</b> of <b>{len(CHECKLIST)}</b> done</p>
      <div class="ckbtns">
        <button type="button" id="ckPrint">Print / save as PDF</button>
        <button type="button" id="ckReset">Clear ticks</button>
      </div>
    </div>
    <ul class="ck">
{_checklist_html()}
    </ul>
    <p class="prfoot mono" style="margin-top:22px;font-size:.8rem">
      Oman e-invoicing readiness checklist &middot; aiprofitlab.io/en/tools/oman-e-invoicing-2027/
      &middot; facts verified {LAST_VERIFIED} &middot; not tax advice</p>
    <p class="cd-note noprint" style="color:var(--muted);margin-top:22px">Your ticks are saved in this
      browser only. Clearing your browser data clears them, and opening the page on another device
      starts fresh &mdash; there is nowhere else they are kept.</p>
  </div>
</section>

<!-- ------------------------------------------------------------------ faq -->
<section class="s-cream grain noprint">
  <div class="wrap-n">
    <div class="asterism"><span>{STAR}</span></div>
    <p class="eyebrow"><span class="star">{STAR}</span>The questions people actually ask</p>
    <h2 class="h2">Straight answers</h2>
    <div class="faq" style="margin-top:clamp(22px,3vw,38px)">
{_faq_html()}
    </div>
  </div>
</section>

<!-- ------------------------------------------------------------ the facts -->
<section class="s-dark grain noprint" id="facts">
  <div class="wrap-n">
    <p class="eyebrow"><span class="star">{STAR}</span>Where these dates come from</p>
    <h2 class="h2">The facts on this page</h2>
    <p class="lede">Every figure above is one of these. If the Tax Authority moves a date, this is the
      block that changes.</p>
    <div class="facts-box" style="margin-top:clamp(24px,3vw,34px)">
      <dl>
        <dt>Instrument</dt>
        <dd>{F["decision"]}, {F["gazette"]}, {F["gazette_date"]}</dd>
        <dt>Pilot</dt>
        <dd>{F["pilot_when"]} &mdash; {F["pilot_who"]}</dd>
        <dt>Phase 1</dt>
        <dd><em>{F["phase1_human"]}</em> &mdash; annual supplies of more than {F["big_threshold"]}</dd>
        <dt>Phase 2</dt>
        <dd><em>{F["phase2_human"]}</em> &mdash; annual supplies of {F["big_threshold"]} or less, i.e.
          every remaining VAT-registered business</dd>
        <dt>Exemption</dt>
        <dd>No permanent turnover exemption. A time-limited exemption may be granted on application, at
          the Tax Authority&rsquo;s discretion</dd>
        <dt>Format</dt>
        <dd>{F["formats"]}, exchanged through an OTA-accredited service provider</dd>
        <dt>VAT threshold</dt>
        <dd>{F["vat_mandatory"]} mandatory registration, {F["vat_voluntary"]} voluntary</dd>
      </dl>
      <ul class="srcs">
{_sources_html()}
      </ul>
      <p class="verified">Facts verified <b>{LAST_VERIFIED}</b> &middot; reviewed quarterly, and again
        after any OTA decision that moves a date</p>
    </div>
    <p class="disclaimer">This page is a plain-language summary, not tax advice, and it is not a
      substitute for your accountant. The Oman Tax Authority is the only authority on what you owe and
      when &mdash; verify anything here against
      <a href="{F["ota_portal"]}" target="_blank" rel="noopener">the OTA tax portal</a> and
      <a href="{F["ota_checker"]}" target="_blank" rel="noopener">its rollout checker</a> before you
      act on it. AI Profit Lab is not an accredited e-invoicing service provider.</p>
  </div>
</section>

<!-- ------------------------------------------------------------------ cta -->
<section class="s-panel grain pad-s noprint">
  <div class="wrap-n">
    <p class="eyebrow"><span class="star">{STAR}</span>If items 5 to 7 are your problem</p>
    <h2 class="h2">One system, before the deadline makes it urgent</h2>
    <p>The parts of this that take months rather than weeks are the ones with nothing to do with the
      Tax Authority: getting quotes, orders and invoices out of spreadsheets and WhatsApp threads and
      into one place, with customer records clean enough to validate. That is what we build, at
      published prices.</p>
    <div class="btn-row" style="margin-top:22px">
      <a class="btn btn-teal" href="/en/services/#price">What I build, and what it costs</a>
      <a class="btn btn-ghost" href="/en/tools/">The other free tools</a>
    </div>
  </div>
</section>

</main>
"""


JS = js()


META = dict(
    slug="efawtara",
    title="Oman e-invoicing 2027 (Fawtara): which phase am I in? | AI Profit Lab",
    desc=("Free tool: a live countdown to Oman's %s e-invoicing deadline, two questions that tell you "
          "which phase applies to your business, and a 12-point readiness checklist you can print. "
          "Runs entirely in your browser." % F["phase2_human"]),
    nav="/en/tools/oman-e-invoicing-2027/",
    next=("Next", "The other free tools", "/en/tools/"),
    schema=_faq_schema() + "$$SPLIT$$" + """{
  "@type":"WebApplication",
  "@id":"https://aiprofitlab.io/en/tools/oman-e-invoicing-2027/#tool",
  "name":"Oman e-invoicing (Fawtara) 2027 phase checker and readiness checklist",
  "applicationCategory":"BusinessApplication",
  "operatingSystem":"Any",
  "browserRequirements":"Runs entirely in the browser. No account and no data submission.",
  "url":"https://aiprofitlab.io/en/tools/oman-e-invoicing-2027/",
  "inLanguage":"en",
  "isAccessibleForFree":true,
  "offers":{"@type":"Offer","price":"0","priceCurrency":"OMR"},
  "publisher":{"@id":"https://aiprofitlab.io/#organization"}
}""",
)
