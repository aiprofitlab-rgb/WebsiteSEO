#!/usr/bin/env python3
"""Free tool 2 - the Oman VAT tax invoice and quote maker.

Fill your business in once, add line items, print a clean branded document that
carries every field an Omani full tax invoice has to carry. It also writes
quotations, and turns a quotation into an invoice without retyping it.

Four rules this page inherits from the free-tools plan and must keep:

  * 100% CLIENT-SIDE, and here that is not a preference. The data flowing
    through this tool is the USER'S CUSTOMERS' names, addresses and VAT
    numbers - third-party personal data. Sending it anywhere would make this
    site a controller of it under Oman's PDPL, in a stack whose data plane sits
    outside Oman. There is therefore no fetch(), no XHR, no beacon and no image
    ping in the script below, and there must never be one. The page says so in
    a sentence a reader can check in DevTools > Network.

  * NAMING. This tool makes a VAT TAX INVOICE. It never makes an "e-invoice".
    A PDF printed from a browser is not a Fawtara e-invoice and cannot be one -
    that needs UBL 2.1 XML or PDF/A-3 through an OTA-accredited channel. Every
    document this tool prints carries NOT_EFAWTARA below, verbatim, linked to
    the Fawtara page. That honesty is the qualifier and the bridge to the
    consult; softening it would turn the tool into the exact false compliance
    claim the plan says is the highest-consequence naming decision in the set.

  * NUMBERING. The user supplies their own sequence. This tool NEVER mints a
    number, and RESERVED_PREFIXES below exist so it can never even suggest one
    in a namespace that belongs to a live system - LGI- (tools/invoice.py),
    INV- and PF- (the storefront invoicer). See docs/invoicing.md section 1.
    Two real customers holding one invoice number is the failure being
    designed out.

  * MONEY IS INTEGER MINOR UNITS. Baisa for OMR, and the currency's own minor
    unit otherwise. Nothing in the arithmetic is a float that reaches a
    printed page, so no document ever says OMR 949.9999998. The one place a
    float is unavoidable is the foreign-currency conversion, which is a
    division by an exchange rate; it is rounded back to whole baisa
    immediately and that is said out loud in the code.

Three decimals, not two. tools/invoice.py prints AI Profit Lab's own invoices
to two, because the storefront invoicer does and one company must not print
money two ways. This tool prints OTHER companies' VAT documents, where the
rial's third decimal is load-bearing: 5% of OMR 9.990 is OMR 0.500 (baisa), and
rounding that to two decimals is a wrong number on a tax document. The two
rules do not conflict because they govern two different sets of paper. Do not
"unify" them.

Every dated rule is in RULES below with a visible LAST_VERIFIED. A stale rate
or threshold here goes wrong silently, with no error anywhere - re-verify
against SOURCES before publishing and again every quarter.
"""
import json
import re

from kit import STAR
from tool_kit import LOCK_ICON, SHELL_CSS

# The Fawtara dates come from the tool-1 module rather than being typed again.
# The Tax Authority has already moved this timeline once; a second copy of
# "1 October 2027" in this file is a second copy that would be missed.
from page_tool_efawtara import FACTS as EFAWTARA

# ==========================================================================
# THE RULES - one block, one date, one place to fix.
#
# Verified 2026-09-10 against the sources in SOURCES. Two of these are hard
# edges rather than guidance and the code treats them as such:
#   * simplified_max is a THRESHOLD, not a hint. At OMR 500 excluding VAT or
#     above, a simplified invoice is refused - not warned about.
#   * vat_rate_pct drives every computed figure on every document. It is not
#     duplicated anywhere in the JS or the prose; both read it from here.
# ==========================================================================
LAST_VERIFIED = "10 September 2026"

RULES = {
    "vat_rate_pct":         5,
    "vat_rate_label":       "5%",
    # Excluding VAT. "Under OMR 500" - so at exactly 500.000 a simplified
    # invoice is NOT allowed, which is why the comparison in the JS is >= and
    # not >. Held in baisa as well as rials so the check is integer maths.
    "simplified_max":       "OMR 500",
    "simplified_max_baisa": 500000,
    # Days from the triggering event within which the invoice must be issued.
    "issue_within_days":    15,
    "home_currency":        "OMR",
    "minor_per_rial":       1000,
    "vat_mandatory":        "OMR 38,500",
    "vat_voluntary":        "OMR 19,250",
    "ota_site":             "https://taxoman.gov.om/",
    "ota_portal":           "https://tms.taxoman.gov.om/portal/",
    # Read from tool 1 so the two pages cannot disagree about the deadline.
    "fawtara_phase2":       EFAWTARA["phase2_human"],
    "fawtara_url":          "/en/tools/oman-e-invoicing-2027/",
}
R = RULES

# The three prefixes this tool must never produce, in any casing, in any
# suggestion. LGI- is tools/invoice.py counting off invoices/register.json on
# Nahid's Mac; INV- and PF- are the storefront service counting off the
# Seat_Claims sheet from Cloud Run. Neither can see the other, which is why
# they were split in the first place - and why a third generator handing a
# stranger an "INV-2026-0008" is exactly the collision docs/invoicing.md
# section 2 exists to prevent.
RESERVED_PREFIXES = ["LGI", "INV", "PF"]

# The sentence. Printed verbatim on every document this tool produces, with
# the Fawtara page linked behind it. Assembled from the date constant so it
# cannot drift from tool 1, but the wording itself is fixed.
NOT_EFAWTARA = ("Valid as a VAT tax invoice today. Not a Fawtara e-invoice — from %s you will "
                "need an accredited channel." % R["fawtara_phase2"])

# The standing disclaimer, on the page and on the paper.
NOT_ADVICE = ("Produced with a free tool. Not tax advice — verify your obligations with the "
              "Oman Tax Authority.")

# Currencies the document may be issued in, and the number of decimal places
# each one's minor unit carries. A currency's precision is a fact about the
# currency, not a display preference, so it lives here rather than in the JS.
# The list is short on purpose: every entry is one more decimal rule to be
# right about, and an Omani SME invoicing in Norwegian kroner is not the case
# this tool is for. OMR first because it is the default and the fallback.
CURRENCIES = [
    ("OMR", 3, "Omani rial"),
    ("AED", 2, "UAE dirham"),
    ("SAR", 2, "Saudi riyal"),
    ("QAR", 2, "Qatari riyal"),
    ("KWD", 3, "Kuwaiti dinar"),
    ("BHD", 3, "Bahraini dinar"),
    ("USD", 2, "US dollar"),
    ("EUR", 2, "Euro"),
    ("GBP", 2, "Pound sterling"),
    ("INR", 2, "Indian rupee"),
]

# The mandatory content of a FULL tax invoice, as the page states it in prose.
# The live checklist in the tool is generated from the same set in the JS;
# these two lists are the same rules said twice on purpose - one for a reader
# and one for the machine - so if you change a rule, change both.
MANDATORY_FULL = [
    ("The words &ldquo;Tax Invoice&rdquo;",
     "Printed at the top of the document. Not &ldquo;Invoice&rdquo;, not &ldquo;Bill&rdquo;."),
    ("The date it is issued",
     "The day the document is raised."),
    ("The date of supply",
     "The day the goods or services were supplied, which is often not the day you invoice."),
    ("A sequential invoice number",
     "Your own sequence, unique, never re-used. This tool does not issue numbers &mdash; you do."),
    ("Your full name, address and VAT identification number",
     "The legal name the VAT registration is in, not a trading name on its own."),
    ("Your customer&rsquo;s full name, address and VAT identification number",
     "All three. This is the field most hand-made invoices are missing."),
    ("A description of the goods or services",
     "Enough for someone who was not there to know what was bought."),
    ("The quantity, where the supply is goods",
     "This tool asks for a quantity on every line, which satisfies it either way."),
    ("The total consideration excluding VAT",
     "The net figure, before tax."),
    ("The VAT rate applied",
     "%s for a standard-rated supply. Shown per line, so a mixed invoice is still correct."
     % R["vat_rate_label"]),
    ("The taxable value and the VAT due, in OMR",
     "In rials even when the invoice itself is in another currency &mdash; which is why this tool "
     "asks for an exchange rate the moment you pick one."),
]

SOURCES = [
    ("Oman VAT invoice requirements: full, simplified and summary invoices",
     "https://invoicedataextraction.com/blog/oman-vat-invoice-requirements"),
    ("Oman: other taxes, including the 5% VAT rate - PwC Worldwide Tax Summaries",
     "https://taxsummaries.pwc.com/oman/corporate/other-taxes"),
    ("Oman Tax Authority",
     "https://taxoman.gov.om/"),
]

# --------------------------------------------------------------------------
# Optional email capture - BUILT, AND DELIBERATELY OFF.
#
# The plan asks for an optional "save your company profile / get the Fawtara
# readiness checklist" capture. Everything needed for it exists: the form
# markup, the consent row, the submit handler, the generate_lead event, and a
# receiving Apps Script modelled on tools/onboarding/brief-apps-script.gs
# (see tools/tools-lead-apps-script.gs, including the setNumberFormat('@')
# call that stops the sheet's USER_ENTERED mode turning a leading "+" on a
# phone number into #ERROR!).
#
# It ships OFF because turning it on is a PDPL decision, not an engineering
# one. An email plus a name posted to a Google Sheet is a transfer of personal
# data outside Oman. Before "enabled" becomes True:
#
#   1. the privacy policy must describe this capture, the recipient, the
#      purpose, the retention period and the transfer outside Oman;
#   2. the consent line at the point of capture must link to it;
#   3. someone must decide whether the site needs a consent banner at all -
#      there is none today, and this would widen that gap rather than create
#      it.
#
# Shipping it quietly would be the one thing on a page whose whole argument is
# that nothing you type leaves your browser.
# --------------------------------------------------------------------------
LEAD_CAPTURE = {
    "enabled": False,
    # The /exec URL of the Apps Script web app, once deployed. Empty is also a
    # hard stop: the handler refuses to post to an empty endpoint rather than
    # posting to the page's own URL, which is what a bare "" in a form action
    # would do.
    "endpoint": "",
}


CSS = SHELL_CSS + """
/* ======================================================== the builder =====
   Two columns on a desk: the form you fill in, and a sidebar that never
   scrolls away because it holds the two things you need while filling it in -
   what the document is still missing, and the print button.

   minmax(0,1fr) rather than 1fr on BOTH tracks. A bare 1fr resolves to
   min-content, and one long unbroken string in a customer address or a line
   description then widens the whole grid and pushes the page into a
   horizontal scroll on a phone. Same trap as the v4 article blocks.
   ------------------------------------------------------------------------ */
.build{
  display:grid;grid-template-columns:minmax(0,1.6fr) minmax(0,1fr);
  gap:clamp(20px,2.8vw,38px);align-items:start;margin:clamp(26px,3.4vw,40px) 0 0;
}
.side{position:sticky;top:88px;display:grid;gap:16px}

/* --------------------------------------------------------------- panels */
.fset{
  border:1px solid var(--line);border-radius:18px;background:var(--white);
  padding:clamp(20px,2.4vw,28px);margin:0 0 clamp(16px,2vw,22px);
}
.fset:last-child{margin-bottom:0}
.fset > legend, .fset > .lg{
  display:flex;align-items:center;gap:9px;padding:0;margin:0 0 4px;
  font-family:var(--mono);font-size:.76rem;letter-spacing:.15em;text-transform:uppercase;
  color:var(--amber-text);
}
.fset .hint{margin:0 0 18px;font-size:.92rem;line-height:1.6;color:var(--muted)}
.fset .hint a{color:var(--teal)}
fieldset.fset{min-width:0}

/* --------------------------------------------------------------- fields
   The same field component as the checkout, on purpose: a visitor who uses
   the free tool and later buys should not meet two different form designs
   from one company. */
.flds{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:15px}
.fld{display:flex;flex-direction:column;gap:7px;min-width:0}
.fld.full{grid-column:1/-1}
.fld label{
  font-family:var(--mono);font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;
  color:var(--muted);
}
.fld label .req{color:var(--alert);margin-inline-start:4px}
.fld label .opt-tag{text-transform:none;letter-spacing:0;font-family:var(--sans);opacity:.75}
.fld input,.fld textarea,.fld select{
  font-family:var(--sans);font-size:1rem;color:var(--ink);background:var(--white);
  border:1px solid var(--line);border-radius:10px;padding:13px 15px;width:100%;min-width:0;
  transition:border-color .2s,box-shadow .2s;
}
.fld textarea{resize:vertical;min-height:74px;line-height:1.55}
.fld input::placeholder,.fld textarea::placeholder{color:rgba(90,102,93,.5)}
.fld input:focus,.fld textarea:focus,.fld select:focus{
  outline:none;border-color:var(--teal);box-shadow:0 0 0 3px rgba(15,110,86,.13);
}
.fld input[aria-invalid=true]{border-color:var(--alert);box-shadow:0 0 0 3px rgba(166,67,31,.13)}
.fld .err{font-size:.84rem;color:var(--alert)}
.fld .err:empty{display:none}
/* .fld is a flex column and display beats [hidden] every time - the same trap
   that once shipped a storefront row reading "Pledged back to you - -". */
.fld[hidden]{display:none}
.fld select{
  appearance:none;-webkit-appearance:none;cursor:pointer;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 8'%3E%3Cpath fill='none' stroke='%235A665D' stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round' d='M1 1.5 6 6.5l5-5'/%3E%3C/svg%3E");
  background-repeat:no-repeat;background-position:right 15px center;background-size:12px 8px;
  padding-right:40px;
}

/* ------------------------------------------------------- document kind */
.kinds{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin:0 0 18px}
.kinds label{
  display:block;cursor:pointer;border:1px solid var(--line);border-radius:12px;
  padding:13px 14px;background:var(--white);transition:border-color .2s,background .2s;
}
.kinds label:hover{border-color:var(--amber)}
.kinds input{position:absolute;opacity:0;width:1px;height:1px}
.kinds label.sel{border-color:var(--teal);background:var(--panel);box-shadow:0 0 0 1px var(--teal) inset}
.kinds b{display:block;font-weight:500;font-size:.99rem;color:var(--teal-950);line-height:1.3}
.kinds span{display:block;font-size:.82rem;line-height:1.45;color:var(--muted);margin-top:5px}
.kinds label.off{opacity:.45;cursor:not-allowed}
.kinds label.off:hover{border-color:var(--line)}
.kinds input:focus-visible + b{outline:2px solid var(--amber);outline-offset:3px}

/* ------------------------------------------------------------ line items
   A grid, not a <table>: the same six cells reflow to two columns on a phone
   with the header labels re-attached per cell, which a table cannot do. */
.lhead,.lrow{
  display:grid;
  grid-template-columns:minmax(0,1fr) 78px 110px 116px minmax(88px,auto) 32px;
  gap:10px;align-items:center;
}
.lhead{
  padding:0 0 8px;border-bottom:1px solid var(--line);
  font-family:var(--mono);font-size:.68rem;letter-spacing:.13em;text-transform:uppercase;
  color:var(--muted);
}
.lhead span:nth-child(2),.lhead span:nth-child(3),
.lhead span:nth-child(5){text-align:right}
.lrow{padding:12px 0;border-bottom:1px solid var(--line)}
.lrow input,.lrow select{
  font-family:var(--sans);font-size:.97rem;color:var(--ink);background:var(--white);
  border:1px solid var(--line);border-radius:9px;padding:10px 11px;width:100%;min-width:0;
}
.lrow input:focus,.lrow select:focus{
  outline:none;border-color:var(--teal);box-shadow:0 0 0 3px rgba(15,110,86,.13);
}
.lrow input[aria-invalid=true]{border-color:var(--alert);box-shadow:0 0 0 3px rgba(166,67,31,.13)}
.lrow .l-qty,.lrow .l-unit{text-align:right;font-variant-numeric:tabular-nums}
.lrow select{
  appearance:none;-webkit-appearance:none;cursor:pointer;padding-right:30px;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 8'%3E%3Cpath fill='none' stroke='%235A665D' stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round' d='M1 1.5 6 6.5l5-5'/%3E%3C/svg%3E");
  background-repeat:no-repeat;background-position:right 10px center;background-size:11px 7px;
}
.lrow .l-amt{
  text-align:right;font-variant-numeric:tabular-nums;font-size:.97rem;color:var(--teal-950);
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}
.lrow .l-del{
  width:32px;height:32px;border:1px solid var(--line);border-radius:9px;background:transparent;
  color:var(--muted);cursor:pointer;font-size:1.05rem;line-height:1;
  transition:color .2s,border-color .2s,background .2s;
}
.lrow .l-del:hover{background:var(--alert);border-color:var(--alert);color:#fff}
.lrow .l-err{grid-column:1/-1;font-size:.84rem;color:var(--alert);margin:-2px 0 0}
.lrow .l-err:empty{display:none}
.addline{
  margin-top:16px;font-family:var(--mono);font-size:.74rem;letter-spacing:.09em;text-transform:uppercase;
  color:var(--teal-950);background:transparent;border:1px dashed var(--line);border-radius:99px;
  padding:11px 20px;cursor:pointer;transition:color .2s,border-color .2s,background .2s;
}
.addline:hover{background:var(--teal-950);border-color:var(--teal-950);border-style:solid;color:var(--cream)}

/* the running totals under the lines */
.runsum{display:grid;gap:6px;margin:18px 0 0;justify-items:end}
.runsum div{display:flex;gap:22px;font-size:.97rem;color:var(--muted)}
.runsum div b{min-width:9ch;text-align:right;font-variant-numeric:tabular-nums;font-weight:500;color:var(--teal-950)}
.runsum div.big{font-size:1.12rem;color:var(--teal-950)}
.runsum div.big b{font-weight:600}
.runsum .omr{font-family:var(--mono);font-size:.82rem;color:var(--amber-text)}

/* ================================================== sidebar: the cards === */
.sidecard{border:1px solid var(--line);border-radius:18px;background:var(--white);padding:20px 22px}
.sidecard h3{
  display:flex;align-items:center;gap:8px;margin:0 0 14px;
  font-family:var(--mono);font-size:.74rem;font-weight:500;letter-spacing:.14em;text-transform:uppercase;
  color:var(--amber-text);
}
.sidecard p{margin:0;font-size:.9rem;line-height:1.6;color:var(--muted)}

/* what the document is still missing */
.reqs{list-style:none;margin:0;padding:0;display:grid;gap:9px}
.reqs li{
  display:grid;grid-template-columns:18px minmax(0,1fr);gap:10px;align-items:start;
  font-size:.9rem;line-height:1.45;color:var(--muted);
}
.reqs li .m{
  width:18px;height:18px;border-radius:50%;border:1.5px solid var(--line);position:relative;margin-top:1px;
}
.reqs li.ok{color:var(--teal-950)}
.reqs li.ok .m{background:var(--teal);border-color:var(--teal)}
.reqs li.ok .m::after{
  content:"";position:absolute;left:5.5px;top:2.5px;width:5px;height:9px;
  border-right:2px solid #fff;border-bottom:2px solid #fff;transform:rotate(42deg);
}
.reqs li.no .m{border-color:var(--alert);border-style:dashed}
.reqs li i{display:block;font-style:normal;font-size:.82rem;color:var(--muted);opacity:.8;margin-top:2px}
.reqcount{
  font-family:var(--mono);font-size:.82rem;letter-spacing:.06em;color:var(--muted);margin:0 0 13px;
}
.reqcount b{color:var(--teal-950);font-weight:500}
.reqcount.done b{color:var(--teal)}

.printbtn{width:100%;justify-content:center}
.printbtn[disabled]{opacity:.42;cursor:not-allowed;pointer-events:none}
.sidenote{margin:12px 0 0;font-size:.84rem;line-height:1.55;color:var(--muted)}
.sidebtns{display:grid;gap:9px;margin-top:12px}
.minibtn{
  font-family:var(--mono);font-size:.72rem;letter-spacing:.09em;text-transform:uppercase;
  color:var(--teal-950);background:transparent;border:1px solid var(--line);border-radius:99px;
  padding:10px 14px;cursor:pointer;transition:color .2s,border-color .2s,background .2s;
}
.minibtn:hover{background:var(--teal-950);border-color:var(--teal-950);color:var(--cream)}
.minibtn.danger:hover{background:var(--alert);border-color:var(--alert)}

/* a flag that is a fact about the user's situation, not a field error */
.flag{
  display:flex;gap:11px;align-items:flex-start;border-inline-start:3px solid var(--amber);
  background:var(--panel);border-radius:0 12px 12px 0;padding:13px 15px;margin:13px 0 0;
  font-size:.88rem;line-height:1.55;color:var(--muted);
}
.flag.stop{border-inline-start-color:var(--alert)}
.flag b{color:var(--teal-950);font-weight:500}
.flag:empty{display:none}

/* ------------------------------------------------- the VAT add/remove bit */
.vatw .row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:9px;align-items:center}
.vatw input{
  font-family:var(--sans);font-size:1rem;color:var(--ink);background:var(--white);
  border:1px solid var(--line);border-radius:10px;padding:11px 13px;width:100%;min-width:0;
  text-align:right;font-variant-numeric:tabular-nums;
}
.vatw input:focus{outline:none;border-color:var(--teal);box-shadow:0 0 0 3px rgba(15,110,86,.13)}
.vatw .cur{font-family:var(--mono);font-size:.84rem;color:var(--muted)}
.vatw .modes{display:flex;gap:7px;margin:11px 0 0}
.vatw .modes label{
  flex:1 1 0;text-align:center;cursor:pointer;border:1px solid var(--line);border-radius:99px;
  padding:8px 6px;font-family:var(--mono);font-size:.68rem;letter-spacing:.07em;text-transform:uppercase;
  color:var(--muted);transition:color .2s,border-color .2s,background .2s;
}
.vatw .modes input{position:absolute;opacity:0;width:1px;height:1px}
.vatw .modes label.sel{background:var(--teal-950);border-color:var(--teal-950);color:var(--cream)}
.vatw dl{margin:15px 0 0;display:grid;grid-template-columns:auto minmax(0,1fr);gap:7px 14px}
.vatw dt{font-family:var(--mono);font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);padding-top:.25em}
.vatw dd{margin:0;text-align:right;font-variant-numeric:tabular-nums;font-size:1rem;color:var(--teal-950)}
.vatw dd.hi{color:var(--amber-text);font-weight:500}

/* ==================================================== the document =======
   Deliberately the same design as invoices/template.html - the paper AI
   Profit Lab's own invoices are printed on. A prospect who uses the free tool
   and later buys should get documents from one family, and reusing a design
   that has already been through a printer saved a day of drawing one.

   Class names are namespaced p- because the site's own chrome already owns
   .foot, .rule and .total, and a document that inherits the page footer's
   colour is a document nobody can read.

   Geometry is in mm at 210mm wide, exactly as it prints. On screen the whole
   sheet is transform-scaled down to fit its container, which is why the
   preview is a true preview and not an approximation of one. */
.paperwrap{margin:clamp(24px,3.2vw,38px) 0 0}
.paperbox{overflow:hidden;background:var(--panel-2);border-radius:16px;padding:0}
.paper{
  width:210mm;padding:14mm 14mm 12mm;background:#fff;color:#232B26;
  transform-origin:top left;
  font-family:var(--sans);font-size:9.6pt;line-height:1.5;
  display:flex;flex-direction:column;min-height:271mm;
  -webkit-print-color-adjust:exact;print-color-adjust:exact;
}
.paper *{box-sizing:border-box}
.paper a{color:#0F6E56;text-decoration:none}
/* The sheet lives inside a page whose stylesheet styles bare elements, and it
   must not inherit any of that. kit.BASE_CSS gives every <section> 74-138px of
   vertical padding, which is right for a page band and absurd inside a
   document - the parties block was 308px tall instead of 78px, and it looked
   like a bug in the layout rather than a rule leaking in from outside. The
   same goes for the display face on headings and the 1.1em paragraph margin.
   Anything added to the sheet later gets this reset for free. */
.paper section,.paper article,.paper header,.paper footer{padding:0;position:static}
.paper h1,.paper h2,.paper h3,.paper h4{font-family:var(--sans);letter-spacing:normal}
.paper p{margin:0}

.p-head{display:flex;justify-content:space-between;align-items:flex-start;gap:14mm}
.p-logo{max-width:52mm;max-height:22mm;width:auto;height:auto;display:block}
.p-wordmark{
  font-family:var(--display);font-size:15pt;line-height:1.15;color:#0A3D30;
  max-width:92mm;word-break:break-word;
}
.p-doc{text-align:right}
.p-doctype{font-family:var(--display);font-size:15pt;letter-spacing:.04em;color:#0A3D30;line-height:1.1}
.p-doctype.is-quote{color:#BA7517}
.p-docnum{font-family:var(--mono);font-size:10.5pt;margin-top:5px;word-break:break-all}
.p-docdate{font-size:8.8pt;color:#5A665D;margin-top:3px}
.p-rule{border:0;border-top:1px solid #DED8C8;margin:5mm 0}

.p-label{
  font-size:6.9pt;font-weight:600;letter-spacing:.13em;text-transform:uppercase;color:#BA7517;
  margin-bottom:2.5mm;
}
.p-parties{display:flex;gap:10mm}
.p-parties > div{flex:1 1 0;min-width:0}
.p-name{font-family:var(--display);font-size:12pt;color:#0A3D30;line-height:1.25;word-break:break-word}
.p-sub{color:#5A665D;font-size:8.8pt;white-space:pre-line;word-break:break-word}
.p-line{font-size:8.8pt;word-break:break-word}
.p-vatin{font-family:var(--mono);font-size:8.6pt;color:#0A3D30}

.p-strip{
  display:flex;flex-wrap:wrap;justify-content:space-between;gap:3mm 8mm;
  background:#FAF8F2;border:1px solid #DED8C8;padding:2.6mm 4mm;margin-top:6mm;font-size:8.8pt;
}
.p-strip .k{
  font-size:6.9pt;font-weight:600;letter-spacing:.13em;text-transform:uppercase;color:#5A665D;
  margin-right:3mm;
}
.p-strip .v{font-family:var(--mono);color:#0A3D30}

table.p-items{width:100%;border-collapse:collapse;margin-top:7mm;table-layout:fixed}
table.p-items th{
  font-size:6.9pt;font-weight:600;letter-spacing:.13em;text-transform:uppercase;color:#BA7517;
  text-align:left;padding:0 0 1.6mm;border-bottom:1px solid #DED8C8;
}
table.p-items th.num,table.p-items td.num{text-align:right}
/* Figures never wrap. HEADINGS must, or "Amount excl. VAT" runs left out of
   its own column and prints on top of the VAT heading beside it. */
table.p-items td.num{white-space:nowrap}
/* Headings carry their own <br>. Left to wrap on their own they did not - a
   fixed-layout table lets an over-wide cell spill sideways instead - and
   "Amount excl. VAT" printed on top of the VAT heading beside it. A gap on
   the left of every numeric cell keeps the columns apart whatever the
   figures are. */
table.p-items th.num{white-space:normal}
table.p-items th.num,table.p-items td.num{padding-left:3mm}
table.p-items td{padding:3.2mm 0;vertical-align:top;border-bottom:1px solid #DED8C8}
table.p-items td.num{font-variant-numeric:tabular-nums}
table.p-items td.desc{padding-right:4mm;word-break:break-word}
.p-itemtitle{font-size:10.2pt}
table.p-items tr{break-inside:avoid}
.p-col-qty{width:14mm}
.p-col-unit{width:25mm}
.p-col-vat{width:17mm}
.p-col-amt{width:31mm}

.p-sums{margin-top:4mm;margin-left:auto;width:80mm;font-size:9.4pt}
.p-sums .r{display:flex;justify-content:space-between;gap:6mm;padding:1.1mm 0}
.p-sums .r span:last-child{font-variant-numeric:tabular-nums;white-space:nowrap}
.p-sums .r.muted{color:#5A665D;font-size:8.6pt}
.p-total{
  display:flex;justify-content:space-between;align-items:baseline;gap:6mm;
  background:#0A3D30;color:#fff;padding:3.4mm 4mm;margin-top:3mm;break-inside:avoid;
}
.p-total .t-label{font-size:10.5pt;font-weight:600}
/* Sans, not the display face: Marcellus draws a wide circular zero that reads
   as a capital O at this size. Fine in a heading, wrong on the one number the
   customer checks against their bank. Same reasoning as the manual template. */
.p-total .t-amount{
  font-family:var(--sans);font-weight:600;font-size:15.5pt;letter-spacing:.01em;
  font-variant-numeric:tabular-nums;white-space:nowrap;
}

/* the OMR restatement, when the document is in another currency */
.p-omr{
  background:#FAF8F2;border:1px solid #0F6E56;padding:3.4mm 4mm;margin-top:5mm;break-inside:avoid;
}
.p-omr h3{margin:0 0 1.6mm;font-family:var(--sans);font-size:9.6pt;font-weight:600;letter-spacing:.03em;color:#0F6E56}
.p-omr p{margin:0 0 1mm;font-size:9pt}
.p-omr p:last-child{margin-bottom:0}
.p-omr b{font-variant-numeric:tabular-nums}

/* Blocks that must not be cut in half by a page break. A 22-line invoice
   runs to three pages, and the first version split the small print down the
   middle: "Valid as a VAT tax invoice today. Not a Fawtara e-invoice" at the
   foot of page two and the rest of the sentence on page three. The one line
   this tool exists to print honestly is the one line that must never be
   halved. */
.p-notes{margin-top:5mm;font-size:8.8pt;break-inside:avoid}
.p-notes .body{white-space:pre-line;word-break:break-word}
.p-sums{break-inside:avoid}
.p-small{margin-top:6mm;font-size:7.8pt;line-height:1.5;color:#5A665D;break-inside:avoid}
.p-foot{break-inside:avoid}
.p-small p{margin:0 0 1.6mm}
.p-small b{color:#232B26}
.p-small a{color:#0F6E56;text-decoration:underline}
.p-url{display:none;font-family:var(--mono)}
.p-foot{
  margin-top:auto;padding-top:3mm;border-top:1px solid #DED8C8;font-size:7.8pt;color:#5A665D;
  display:flex;justify-content:space-between;gap:6mm;flex-wrap:wrap;
}
.p-foot .made{color:#BA7517}
.p-empty{
  margin:auto 0;text-align:center;color:#5A665D;font-size:11pt;font-family:var(--display);
}

/* -------------------------------------------------------- worked examples */
.vectors{width:100%;border-collapse:collapse;margin:clamp(20px,2.6vw,28px) 0 0;font-size:.94rem}
.vectors th,.vectors td{
  text-align:right;padding:11px 10px;border-bottom:1px solid var(--line);
  font-variant-numeric:tabular-nums;
}
.vectors th{
  font-family:var(--mono);font-size:.68rem;font-weight:500;letter-spacing:.12em;text-transform:uppercase;
  color:var(--amber-text);
}
.vectors th:first-child,.vectors td:first-child{text-align:left;font-variant-numeric:normal}
.vectors td:first-child{color:var(--teal-950)}
.vectors td{color:var(--muted)}
.vscroll{overflow-x:auto;-webkit-overflow-scrolling:touch}

/* --------------------------------------------------------- the fact box */
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
.notclaim a{color:var(--teal);text-underline-offset:3px}
.facts-box{border:1px solid var(--line-dark);border-radius:18px;padding:clamp(22px,2.8vw,32px)}
.facts-box dl{margin:0;display:grid;grid-template-columns:auto minmax(0,1fr);gap:12px 22px}
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
.disclaimer{margin:clamp(20px,3vw,28px) 0 0;font-size:.93rem;line-height:1.65;color:rgba(241,239,232,.6)}
.disclaimer a{color:var(--amber-bright)}

/* ---------------------------------------------------------- breakpoints */
@media (max-width:1040px){
  .build{grid-template-columns:minmax(0,1fr)}
  /* Sticky is worse than useless once the sidebar is a band across the top:
     it pins the checklist over the fields you are trying to fill in. */
  .side{position:static}
}
@media (max-width:720px){
  .kinds{grid-template-columns:minmax(0,1fr)}
  .flds{grid-template-columns:minmax(0,1fr)}
  /* Line rows become two columns with their header labels re-attached to
     each cell. The .lhead strip is meaningless once the cells wrap, so it
     goes; without removing it the labels would be shown twice. */
  .lhead{display:none}
  .lrow{
    grid-template-columns:minmax(0,1fr) minmax(0,1fr);
    gap:12px 10px;padding:16px 0;position:relative;
  }
  .lrow .l-desc-cell{grid-column:1/-1;padding-right:42px}
  .lrow .cell{display:flex;flex-direction:column;gap:5px;min-width:0}
  .lrow .cell::before{
    content:attr(data-lbl);font-family:var(--mono);font-size:.64rem;letter-spacing:.12em;
    text-transform:uppercase;color:var(--muted);
  }
  .lrow .l-amt-cell{align-items:flex-end;text-align:right}
  .lrow .l-del{position:absolute;top:16px;right:0}
}
@media (max-width:420px){
  .vatw .modes{flex-direction:column}
  .runsum div{gap:14px}
}

/* ------------------------------------------------------------------ print
   Sections opt IN by carrying .pr, the same way tool 1 does, because opt-out
   means every section written afterwards has to remember to opt out and one
   of them will not. Exactly one section carries it here, and inside that
   section everything but the sheet is .noprint.

   The transform reset is not cosmetic. The on-screen sheet is scaled to fit
   its container; printing it scaled would put an A4 page inside an A4 page,
   and in Chrome a transformed element also paginates as one unbreakable
   block, so a two-page invoice would lose its second page. */
@media print{
  @page{size:A4;margin:14mm 14mm 12mm}
  html,body{background:#fff!important;color:#111!important}
  .top,.mmenu,.foot,.pager,.skip,#aiden-root,.noprint,.btn-row{display:none!important}
  main>section{display:none!important}
  main>section.pr{display:block!important;padding:0!important;background:#fff!important}
  main>section.pr .wrap,main>section.pr .wrap-n{width:100%!important;margin:0!important}
  .grain::before{display:none!important}
  .paperwrap{margin:0!important}
  .paperbox{overflow:visible!important;height:auto!important;background:none!important;
            border-radius:0!important;padding:0!important}
  .paper{
    transform:none!important;width:auto!important;padding:0!important;margin:0!important;
    box-shadow:none!important;min-height:271mm;
  }
  .p-url{display:inline}
  .p-small a{text-decoration:none;color:#5A665D!important}
}
"""


# --------------------------------------------------------------------------
# JS. A plain string, not an f-string: the constants arrive through .replace()
# so none of the braces below has to be doubled.
#
# EVERYTHING IN HERE RUNS ON THE VISITOR'S DEVICE AND NOTHING IN IT OPENS A
# CONNECTION. No fetch, no XHR, no sendBeacon, no new Image().src. What flows
# through this script is a third party's name, address and VAT number - the
# visitor's customer, who never agreed to anything with us. That is the whole
# reason the architecture is what it is; adding one network call to this file
# would make the sentence printed on the page false and this site a controller
# of personal data it has no lawful basis to hold.
# --------------------------------------------------------------------------
JS_TPL = r"""
(function(){
  "use strict";
  var C = __CFG__;

  /* ===================================================== small helpers === */
  function $(id){ return document.getElementById(id); }
  var ENT = {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"};
  function esc(s){
    return String(s == null ? "" : s).replace(/[&<>"']/g, function(c){ return ENT[c]; });
  }
  /* Round half away from zero. Math.round() rounds -0.5 to -0 (i.e. towards
     +Infinity), which would make a credit line disagree with the same line
     entered positive. A tax document must not have a sign-dependent rounding
     rule. */
  function rhu(x){ return x < 0 ? -Math.floor(-x + 0.5) : Math.floor(x + 0.5); }

  function decimals(cur){ return C.currencies[cur] === undefined ? 2 : C.currencies[cur]; }

  /* Text -> integer minor units. Returns {ok:true,v:int} or {ok:false,...}.
     It REFUSES to round rather than quietly accepting a fourth decimal: on a
     tax document an amount that needs a place the currency does not have is a
     mistake, not something to silently truncate. tools/invoice.py takes the
     same line. */
  function parseMoney(txt, d, allowNeg){
    /* Strip grouping before parsing: \s (which covers the non-breaking
       space), the Latin comma, and U+066C, the Arabic thousands separator a
       phone set to Arabic numerals pastes in. */
    var s = String(txt == null ? "" : txt).replace(/[\s,\u066C]/g, "");
    if (s === "") return {ok:false, empty:true};
    if (!/^-?(\d+(\.\d*)?|\.\d+)$/.test(s)) return {ok:false, why:"not a number"};
    var neg = s.charAt(0) === "-";
    if (neg){
      if (!allowNeg) return {ok:false, why:"cannot be negative"};
      s = s.slice(1);
    }
    var parts = s.split(".");
    var whole = parts[0] === "" ? "0" : parts[0];
    var frac  = parts.length > 1 ? parts[1] : "";
    if (frac.length > d){
      return {ok:false, why: d === 0 ? "must be a whole number"
                                     : "more than " + d + " decimal places"};
    }
    while (frac.length < d) frac += "0";
    var v = Number(whole) * Math.pow(10, d) + (frac === "" ? 0 : Number(frac));
    if (!isFinite(v) || v > C.maxMinor) return {ok:false, why:"too large"};
    return {ok:true, v: neg ? -v : v};
  }

  /* Integer minor units -> "1,234.567". Built by slicing the digit string
     rather than dividing, so nothing ever passes through a float on its way
     to a printed page. */
  function fmt(minor, d){
    var neg = minor < 0, n = Math.abs(minor), s = String(n);
    while (s.length <= d) s = "0" + s;
    var whole = d ? s.slice(0, s.length - d) : s;
    var frac  = d ? s.slice(s.length - d) : "";
    whole = whole.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    return (neg ? "−" : "") + whole + (d ? "." + frac : "");
  }
  /* The gap between the code and the number is a NON-BREAKING space, written
     as an escape rather than typed so it is visible to whoever reads this
     next. "OMR" and the figure it qualifies must never be split across a line
     break: a stray "OMR" at the end of one line and "105.000" at the start of
     the next is the kind of thing a customer queries. Anything comparing
     these strings has to expect \u00a0. */
  function money(minor, cur){ return cur + "\u00a0" + fmt(minor, decimals(cur)); }
  function omr(baisa){ return "OMR\u00a0" + fmt(baisa, 3); }

  /* Quantity carries three decimals too - 2.5 hours, 0.75 kg - and is held as
     integer thousandths for the same reason the money is. */
  function parseQty(txt){ return parseMoney(txt, 3, false); }

  /* -------------------------------------------------------------- dates -- */
  var MONTHS = ["January","February","March","April","May","June",
                "July","August","September","October","November","December"];
  function todayISO(){
    var d = new Date();
    return d.getFullYear() + "-" + pad2(d.getMonth() + 1) + "-" + pad2(d.getDate());
  }
  function pad2(n){ return n < 10 ? "0" + n : String(n); }
  function parseISO(iso){
    var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(iso || ""));
    if (!m) return null;
    /* Constructed from local parts, never Date.parse("2026-09-10"), which the
       spec reads as UTC midnight - west of Greenwich that is the day before,
       and an invoice dated one day early is a real problem. */
    var d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
    return isNaN(d.getTime()) ? null : d;
  }
  function fmtDate(iso){
    var d = parseISO(iso);
    return d ? d.getDate() + " " + MONTHS[d.getMonth()] + " " + d.getFullYear() : "";
  }
  function addDays(iso, n){
    var d = parseISO(iso);
    if (!d) return null;
    d.setDate(d.getDate() + n);
    return d.getFullYear() + "-" + pad2(d.getMonth() + 1) + "-" + pad2(d.getDate());
  }
  function daysBetween(aIso, bIso){
    var a = parseISO(aIso), b = parseISO(bIso);
    if (!a || !b) return null;
    return Math.round((b - a) / 86400000);
  }

  /* ================================================= state and storage ===
     Two keys, both in localStorage and nowhere else: this browser, this
     device, never a server. Every access is wrapped, because a private window
     or a browser set to block site data throws on the accessor itself - and a
     tool that cannot remember must still be a tool that works. */
  var K_PROFILE = "apl.vatinv.profile.v1";
  var K_DRAFT   = "apl.vatinv.draft.v1";
  var K_LAST    = "apl.vatinv.lastnumber.v1";   /* {invoice:"...", quote:"..."} */

  function lsGet(k){
    try { var raw = localStorage.getItem(k); return raw ? JSON.parse(raw) : null; }
    catch(e){ return null; }
  }
  function lsSet(k, v){
    try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch(e){ return false; }
  }
  function lsDel(k){ try { localStorage.removeItem(k); } catch(e){} }

  var S = {
    kind: "invoice",
    logo: "",
    profile:  {name:"", address:"", vatin:"", cr:"", email:"", phone:""},
    customer: {name:"", address:"", vatin:""},
    doc: {number:"", issue:"", supply:"", currency:"OMR", fx:"",
          reference:"", terms:"", valid:"", notes:""}
  };

  /* ---------------------------------------------------------- the lines --
     The DOM is the source of truth for line items, and S is read out of it.
     Keeping a parallel array in sync with the inputs was the first design and
     it needed an index on every row; a row deleted from the middle then left
     every index after it pointing one row along. Reading the rows in document
     order cannot go wrong that way. */
  var rowsEl = $("lines");

  function rowHTML(L){
    return '' +
      '<div class="l-desc-cell cell" data-lbl="Description">' +
        '<input class="l-desc" type="text" value="' + esc(L.desc || "") +
        '" placeholder="Description of the goods or services" aria-label="Description">' +
      '</div>' +
      '<div class="cell" data-lbl="Qty">' +
        '<input class="l-qty" type="text" inputmode="decimal" value="' + esc(L.qty || "") +
        '" placeholder="1" aria-label="Quantity">' +
      '</div>' +
      '<div class="cell" data-lbl="Unit price">' +
        '<input class="l-unit" type="text" inputmode="decimal" value="' + esc(L.unit || "") +
        '" placeholder="0.000" aria-label="Unit price excluding VAT">' +
      '</div>' +
      '<div class="cell" data-lbl="VAT">' +
        '<select class="l-rate" aria-label="VAT treatment">' +
          '<option value="S">' + C.vatRateLabel + '</option>' +
          '<option value="Z">0% zero-rated</option>' +
          '<option value="E">Exempt</option>' +
        '</select>' +
      '</div>' +
      '<div class="cell l-amt-cell" data-lbl="Amount excl. VAT"><span class="l-amt">&mdash;</span></div>' +
      '<button type="button" class="l-del" aria-label="Remove this line">&times;</button>' +
      '<p class="l-err" role="alert"></p>';
  }

  function addRow(L, focus){
    L = L || {};
    var div = document.createElement("div");
    div.className = "lrow";
    div.innerHTML = rowHTML(L);
    div.querySelector(".l-rate").value = (L.rate === "Z" || L.rate === "E") ? L.rate : "S";
    rowsEl.appendChild(div);
    if (focus) div.querySelector(".l-desc").focus();
    return div;
  }

  function readLines(){
    var out = [];
    Array.prototype.forEach.call(rowsEl.children, function(row){
      out.push({
        desc: row.querySelector(".l-desc").value,
        qty:  row.querySelector(".l-qty").value,
        unit: row.querySelector(".l-unit").value,
        rate: row.querySelector(".l-rate").value
      });
    });
    return out;
  }

  function setLines(arr){
    rowsEl.innerHTML = "";
    if (!arr || !arr.length){ addRow({qty:"1", rate:"S"}, false); return; }
    arr.forEach(function(L){ addRow(L, false); });
  }

  /* ==================================================== the arithmetic ===
     Every figure below is an integer in the document currency's minor unit -
     baisa for OMR. The only division that leaves integer space is the foreign
     exchange one at the bottom, and it is rounded straight back to whole
     baisa. */
  function compute(){
    var lines = readLines();
    var cur = S.doc.currency, d = decimals(cur);
    var T = {cur:cur, d:d, rows:[], net:0, vat:0, gross:0,
             byRate:{S:{net:0,vat:0,n:0}, Z:{net:0,vat:0,n:0}, E:{net:0,vat:0,n:0}},
             allValid:true, anyLine:false, tooBig:false};

    lines.forEach(function(L){
      var hasAnything = (L.desc || "").trim() !== "" || (L.qty || "").trim() !== ""
                        || (L.unit || "").trim() !== "";
      var q = parseQty(L.qty);
      var u = parseMoney(L.unit, d, true);
      var r = {desc:(L.desc || "").trim(), rate:L.rate, q:q, u:u,
               used:hasAnything, net:null, vat:null, err:""};

      if (hasAnything){
        T.anyLine = true;
        if (!r.desc) r.err = "This line needs a description.";
        else if (!q.ok) r.err = "Quantity: " + (q.empty ? "required" : q.why) + ".";
        else if (!u.ok) r.err = "Unit price: " + (u.empty ? "required" : u.why) + ".";
      }

      if (q.ok && u.ok){
        /* qty is thousandths, so divide it back down before multiplying. Both
           operands are small on any real invoice and the product is exact
           well below the 2^53 integer ceiling; the maxMinor guard below
           catches the case where it is not. */
        r.net = rhu(q.v / 1000 * u.v);
        if (Math.abs(r.net) > C.maxMinor){ r.err = "That line comes to more than this tool will total."; T.tooBig = true; }
        r.vat = r.rate === "S" ? rhu(r.net * C.vatRatePct / 100) : 0;
      }
      if (r.err) T.allValid = false;

      if (!r.err && r.net !== null && hasAnything){
        T.net += r.net;
        T.vat += r.vat;
        var b = T.byRate[r.rate] || T.byRate.S;
        b.net += r.net; b.vat += r.vat; b.n += 1;
      }
      T.rows.push(r);
    });

    T.gross = T.net + T.vat;
    if (Math.abs(T.gross) > C.maxMinor) T.tooBig = true;

    /* ------------------------------------------------------ the OMR view --
       "The VAT amount must be shown in OMR even where the invoice is in
       another currency." When the document IS in rials that is the same
       number; when it is not, it is this conversion, and the rate the user
       typed is printed beside it so the customer can check the arithmetic. */
    var fx = parseMoney(S.doc.fx, 6, false);
    T.fxOk = cur === "OMR" ? true : (fx.ok && fx.v > 0);
    T.fxMicro = fx.ok ? fx.v : 0;
    if (cur === "OMR"){
      T.netOmr = T.net; T.vatOmr = T.vat; T.grossOmr = T.gross;
    } else if (T.fxOk){
      T.netOmr   = toOmr(T.net, d, T.fxMicro);
      T.vatOmr   = toOmr(T.vat, d, T.fxMicro);
      T.grossOmr = toOmr(T.gross, d, T.fxMicro);
    } else {
      T.netOmr = T.vatOmr = T.grossOmr = null;
    }
    return T;
  }

  /* Minor units of `cur` -> whole baisa. This is the one place a float is
     unavoidable: an exchange rate is a division, and no integer holds the
     result. It is rounded to whole baisa immediately and the rate used is
     printed on the document, so the number on the page is exact even though
     the step that produced it was not. */
  function toOmr(minor, d, rateMicro){
    return rhu((minor / Math.pow(10, d)) * (rateMicro / 1000000) * 1000);
  }

  /* =============================================== the mandatory fields ===
     Generated, not typed - the same set the prose on this page lists, in the
     same order. A document cannot be printed until every gating row passes,
     which is what "required inputs, not optional" means in practice. */
  function requirements(T){
    var k = S.kind, p = S.profile, c = S.customer, dd = S.doc, out = [];
    function add(label, ok, hint){ out.push({label:label, ok:!!ok, hint:hint || ""}); }

    var descOk = T.anyLine && T.allValid && T.rows.some(function(r){ return r.used; });
    var qtyOk  = descOk;
    var amountsOk = descOk && !T.tooBig;

    if (k === "quote"){
      add("A quotation number", dd.number.trim(), "Your own reference for this quote.");
      add("The date", dd.issue, "");
      add("Valid until", dd.valid, "A quote with no expiry is a price you are still held to next year.");
      add("Your full name and address", p.name.trim() && p.address.trim(), "");
      add("Your customer&rsquo;s name", c.name.trim(), "");
      add("A description of each item", descOk, "");
      add("A quantity on each line", qtyOk, "");
      add("The total excluding VAT", amountsOk, "");
    } else {
      var simple = k === "simplified";
      add("The words &ldquo;Tax Invoice&rdquo;", true, "Printed at the top by this tool.");
      add("The date it is issued", dd.issue, "");
      add("The date of supply", dd.supply, "Often not the same day you invoice.");
      add("A sequential invoice number", dd.number.trim(),
          "Your own sequence. This tool does not issue numbers.");
      add("Your full name", p.name.trim(), "The legal name on the VAT registration.");
      add("Your address", p.address.trim(), "");
      add("Your VAT identification number", p.vatin.trim(), "");
      add("Your customer&rsquo;s full name", c.name.trim(), "");
      if (!simple){
        add("Your customer&rsquo;s address", c.address.trim(), "");
        add("Your customer&rsquo;s VAT identification number", c.vatin.trim(),
            "The field most hand-made invoices are missing.");
      }
      add("A description of each item", descOk, "");
      add("A quantity on each line", qtyOk, "");
      add("The total excluding VAT", amountsOk, "");
      add("The VAT rate applied", amountsOk, "Shown per line, so a mixed invoice is still correct.");
      add("The taxable value and VAT due in OMR",
          amountsOk && T.netOmr !== null,
          T.cur === "OMR" ? "" : "Needs the exchange rate above.");
      if (simple){
        add("The supply is under " + C.simplifiedMax + " excluding VAT",
            T.netOmr !== null && T.netOmr < C.simplifiedMaxBaisa,
            "A simplified invoice is only allowed below that figure.");
      }
    }
    return out;
  }

  /* ================================================== reading the form === */
  var FIELD_MAP = [
    ["pf-name", "profile", "name"], ["pf-address", "profile", "address"],
    ["pf-vatin", "profile", "vatin"], ["pf-cr", "profile", "cr"],
    ["pf-email", "profile", "email"], ["pf-phone", "profile", "phone"],
    ["c-name", "customer", "name"], ["c-address", "customer", "address"],
    ["c-vatin", "customer", "vatin"],
    ["d-number", "doc", "number"], ["d-issue", "doc", "issue"], ["d-supply", "doc", "supply"],
    ["d-currency", "doc", "currency"], ["d-fx", "doc", "fx"],
    ["d-reference", "doc", "reference"], ["d-terms", "doc", "terms"],
    ["d-valid", "doc", "valid"], ["d-notes", "doc", "notes"]
  ];

  function readForm(){
    FIELD_MAP.forEach(function(f){
      var el = $(f[0]);
      if (el) S[f[1]][f[2]] = el.value;
    });
    var checked = document.querySelector('input[name="kind"]:checked');
    S.kind = checked ? checked.value : "invoice";
  }
  function writeForm(){
    FIELD_MAP.forEach(function(f){
      var el = $(f[0]);
      if (el) el.value = S[f[1]][f[2]] || "";
    });
    var r = document.querySelector('input[name="kind"][value="' + S.kind + '"]');
    if (r) r.checked = true;
    paintKinds();
  }

  function paintKinds(){
    Array.prototype.forEach.call(document.querySelectorAll('.kinds label'), function(lb){
      var inp = lb.querySelector("input");
      lb.classList.toggle("sel", !!(inp && inp.checked));
    });
  }

  /* ======================================================== persistence === */
  var saveTimer = null;
  function saveSoon(){
    if (saveTimer) clearTimeout(saveTimer);
    saveTimer = setTimeout(save, 400);
  }
  function save(){
    var p = {};
    for (var k in S.profile) if (Object.prototype.hasOwnProperty.call(S.profile, k)) p[k] = S.profile[k];
    p.logo = S.logo;
    var okP = lsSet(K_PROFILE, p);
    var okD = lsSet(K_DRAFT, {kind:S.kind, doc:S.doc, customer:S.customer, lines:readLines()});
    var el = $("saveState");
    if (el){
      /* Three states, and the first one matters: saying "Saved in this
         browser" to somebody who has typed nothing is a claim about their
         data made before they have given you any, on the one card whose job
         is to be believed. */
      var anything = S.profile.name || S.profile.address || S.profile.vatin
                  || S.customer.name || S.doc.number
                  || readLines().some(function(L){ return L.desc || L.unit; });
      el.textContent = !(okP && okD)
        ? "This browser will not let the page remember anything — everything still works, "
          + "but nothing is kept when you close the tab."
        : anything
          ? "Saved in this browser"
          : "Nothing saved yet. What you type is kept in this browser only.";
    }
  }
  function restore(){
    var p = lsGet(K_PROFILE);
    if (p){
      ["name","address","vatin","cr","email","phone"].forEach(function(k){
        if (typeof p[k] === "string") S.profile[k] = p[k];
      });
      /* Sanitised at the door as well as at every use: a stored value that is
         not an inline image is dropped here rather than carried around. */
      if (typeof p.logo === "string" && /^data:image\//i.test(p.logo)) S.logo = p.logo;
    }
    var dft = lsGet(K_DRAFT);
    if (dft){
      if (dft.kind === "invoice" || dft.kind === "simplified" || dft.kind === "quote") S.kind = dft.kind;
      if (dft.doc) for (var k1 in S.doc)
        if (typeof dft.doc[k1] === "string") S.doc[k1] = dft.doc[k1];
      if (dft.customer) for (var k2 in S.customer)
        if (typeof dft.customer[k2] === "string") S.customer[k2] = dft.customer[k2];
      setLines(dft.lines);
    } else {
      setLines(null);
    }
    if (!S.doc.issue) S.doc.issue = todayISO();
    if (!S.doc.currency) S.doc.currency = "OMR";
    writeForm();
    paintLogo();
  }

  /* ========================================================== the logo ===
     Read with FileReader into a data URI and kept in localStorage. It is
     never uploaded, because there is nowhere to upload it to. Capped because
     localStorage is a handful of megabytes and a 4 MB photograph of a logo
     would silently blow the quota and take the saved profile with it. */
  /* The ONLY value this page will ever put in an <img src>, and the reason it
     is a function rather than a plain read of S.logo.

     S.logo comes from FileReader, so in the normal path it is always a data:
     URI and nothing could be safer. But it is also restored from
     localStorage, which is a store the user - or anything else that ever runs
     on this origin - can write. A logo of "https://somewhere/x.png" would
     make the browser fetch it, and the one claim this whole page rests on
     would be false the moment the profile loaded. Refusing anything that is
     not an inline image keeps "nothing leaves your browser" a property of the
     code rather than of where the value happened to come from. */
  function logoSrc(){ return /^data:image\//i.test(S.logo || "") ? S.logo : ""; }

  function paintLogo(){
    var img = $("logoPrev"), clear = $("logoClear"), src = logoSrc();
    if (!img) return;
    if (src){ img.src = src; img.hidden = false; if (clear) clear.hidden = false; }
    else { img.removeAttribute("src"); img.hidden = true; if (clear) clear.hidden = true; }
  }

  var logoIn = $("pf-logo");
  if (logoIn) logoIn.addEventListener("change", function(){
    var err = $("logoErr");
    if (err) err.textContent = "";
    var f = logoIn.files && logoIn.files[0];
    if (!f) return;
    if (!/^image\/(png|jpeg|webp|svg\+xml|gif)$/.test(f.type)){
      if (err) err.textContent = "That is not an image file.";
      logoIn.value = ""; return;
    }
    if (f.size > C.maxLogoBytes){
      if (err) err.textContent = "That image is " + Math.round(f.size / 1024) + " KB. Keep it under "
        + Math.round(C.maxLogoBytes / 1024) + " KB so it fits in this browser's storage.";
      logoIn.value = ""; return;
    }
    var fr = new FileReader();
    fr.onload = function(){
      S.logo = String(fr.result || "");
      paintLogo(); save(); render();
    };
    fr.onerror = function(){ if (err) err.textContent = "That file could not be read."; };
    fr.readAsDataURL(f);
  });

  var logoClear = $("logoClear");
  if (logoClear) logoClear.addEventListener("click", function(){
    S.logo = ""; if (logoIn) logoIn.value = "";
    paintLogo(); save(); render();
  });

  /* ================================================ numbering discipline ==
     This tool never mints a number. The one convenience it offers is
     incrementing the LAST number you yourself used, and even that stops dead
     at the three prefixes below: LGI- is tools/invoice.py counting off a
     register on one Mac, INV- and PF- are the storefront service counting off
     a Google Sheet from Cloud Run, and neither can see the other. A third
     generator handing out numbers in either namespace is how two real
     customers end up holding one invoice number. */
  var RESERVED_RE = new RegExp("^\\s*(" + C.reserved.join("|") + ")\\s*[-‐-―_ ]", "i");

  function lastNumbers(){ return lsGet(K_LAST) || {}; }
  function seriesKey(){ return S.kind === "quote" ? "quote" : "invoice"; }

  function nextNumber(prev){
    if (!prev || RESERVED_RE.test(prev)) return "";
    var m = /^([\s\S]*?)(\d+)(\D*)$/.exec(prev);
    if (!m) return "";
    var digits = m[2], n = String(Number(digits) + 1);
    while (n.length < digits.length) n = "0" + n;
    return m[1] + n + m[3];
  }

  function paintNextBtn(){
    var b = $("nextNum");
    if (!b) return;
    var prev = lastNumbers()[seriesKey()] || "";
    var nxt = nextNumber(prev);
    b.disabled = !nxt;
    b.textContent = nxt ? ("Next: " + nxt) : "No previous number yet";
    b.setAttribute("data-next", nxt);
  }
  var nextBtn = $("nextNum");
  if (nextBtn) nextBtn.addEventListener("click", function(){
    var nxt = nextBtn.getAttribute("data-next");
    if (!nxt) return;
    $("d-number").value = nxt;
    onInput();
  });

  /* =========================================================== rendering == */
  function rateCell(rate){
    return rate === "S" ? C.vatRateLabel : (rate === "Z" ? "0%" : "Exempt");
  }

  function render(){
    var T = compute();

    /* per-line amounts and errors */
    Array.prototype.forEach.call(rowsEl.children, function(row, i){
      var r = T.rows[i];
      if (!r) return;
      row.querySelector(".l-amt").textContent =
        (r.net === null || r.err) ? "—" : fmt(r.net, T.d);
      row.querySelector(".l-err").textContent = r.err;
      row.querySelector(".l-qty").setAttribute("aria-invalid", (r.used && !r.q.ok) ? "true" : "false");
      row.querySelector(".l-unit").setAttribute("aria-invalid", (r.used && !r.u.ok) ? "true" : "false");
    });

    /* the running totals under the lines */
    var rs = $("runsum");
    if (rs){
      var bits = '<div><span>Total excluding VAT</span><b>' + money(T.net, T.cur) + '</b></div>';
      bits += '<div><span>VAT</span><b>' + money(T.vat, T.cur) + '</b></div>';
      bits += '<div class="big"><span>Total including VAT</span><b>' + money(T.gross, T.cur) + '</b></div>';
      if (T.cur !== "OMR"){
        bits += T.netOmr === null
          ? '<div class="omr">VAT in OMR: add the exchange rate above</div>'
          : '<div class="omr">VAT in rials: ' + omr(T.vatOmr) + '</div>';
      }
      rs.innerHTML = bits;
    }

    /* the mandatory-field checklist */
    var reqs = requirements(T);
    var done = 0;
    var html = "";
    reqs.forEach(function(q){
      if (q.ok) done++;
      html += '<li class="' + (q.ok ? "ok" : "no") + '"><span class="m" aria-hidden="true"></span>' +
              '<span>' + q.label + (q.hint ? '<i>' + q.hint + '</i>' : '') + '</span></li>';
    });
    var list = $("reqList"); if (list) list.innerHTML = html;
    var cnt = $("reqCount");
    if (cnt){
      cnt.innerHTML = "<b>" + done + "</b> of <b>" + reqs.length + "</b> present";
      cnt.classList.toggle("done", done === reqs.length);
    }
    var ready = done === reqs.length && !T.tooBig;
    var pb = $("printBtn");
    if (pb){
      pb.disabled = !ready;
      pb.textContent = ready ? ("Print / save " + (S.kind === "quote" ? "the quote" : "the invoice") + " as PDF")
                             : "Fill in what is missing first";
    }

    renderFlags(T);
    renderPaper(T);
    paintNextBtn();

    if (!render.counted && T.anyLine && T.allValid && T.net !== 0 && typeof gtag === "function"){
      render.counted = true;
      /* THAT the tool was used, never WHAT was typed into it. */
      gtag("event", "tool_used", {tool_name:"oman-vat-invoice-generator", tool_step:"first_line"});
    }
  }

  /* Facts about the user's situation, as opposed to fields they have not
     filled in. These never block printing - a late invoice is still an
     invoice, and telling someone they cannot print the document they are
     legally required to issue would be absurd. */
  function renderFlags(T){
    var el = $("flags");
    if (!el) return;
    var out = "";

    if (S.kind !== "quote" && S.doc.supply && S.doc.issue){
      var gap = daysBetween(S.doc.supply, S.doc.issue);
      var due = addDays(S.doc.supply, C.issueWithinDays);
      if (gap !== null && gap > C.issueWithinDays){
        out += '<div class="flag stop"><span><b>This is ' + gap + ' days after the supply.</b> ' +
               'An invoice has to be issued within ' + C.issueWithinDays + ' days of the event that ' +
               'triggered it — for this supply that was ' + esc(fmtDate(due)) + '. Issue it anyway; ' +
               'raise the timing with your accountant.</span></div>';
      } else if (gap !== null && gap >= 0){
        out += '<div class="flag"><span><b>Issue by ' + esc(fmtDate(due)) + '.</b> ' +
               C.issueWithinDays + ' days from the supply on ' + esc(fmtDate(S.doc.supply)) + '.</span></div>';
      } else if (gap !== null && gap < 0){
        out += '<div class="flag"><span><b>Dated before the supply.</b> The supply date is after the ' +
               'issue date, which is usually a typo in one of the two.</span></div>';
      }
    }

    if (S.doc.number && RESERVED_RE.test(S.doc.number)){
      out += '<div class="flag"><span><b>That prefix is already in use.</b> ' +
             C.reserved.join("-, ") + '- are the prefixes AI Profit Lab&rsquo;s own invoicing ' +
             'systems count off. Nothing stops you using it, but this tool will not suggest a next ' +
             'number inside one — pick a prefix of your own and two documents can never end up ' +
             'sharing a number.</span></div>';
    }

    if (S.kind === "simplified" && T.netOmr !== null && T.netOmr >= C.simplifiedMaxBaisa){
      out += '<div class="flag stop"><span><b>Too large for a simplified invoice.</b> This supply is ' +
             omr(T.netOmr) + ' excluding VAT, and a simplified invoice is only allowed below ' +
             C.simplifiedMax + '. Switch to a full tax invoice and add your customer&rsquo;s address ' +
             'and VAT number.</span></div>';
    }

    if (T.cur !== "OMR" && !T.fxOk){
      out += '<div class="flag stop"><span><b>The rate to rials is missing.</b> The VAT has to be shown ' +
             'in OMR even when the invoice is in ' + esc(T.cur) + '.</span></div>';
    }
    el.innerHTML = out;
  }

  /* ----------------------------------------------------------- the paper -- */
  var TITLES = {invoice:"Tax Invoice", simplified:"Simplified Tax Invoice", quote:"Quotation"};

  function partyBlock(label, name, address, vatin, extra){
    var h = '<div><div class="p-label">' + label + '</div>';
    h += '<div class="p-name">' + (name ? esc(name) : "&mdash;") + '</div>';
    if (address) h += '<div class="p-sub">' + esc(address) + '</div>';
    if (vatin)   h += '<div class="p-vatin">VATIN ' + esc(vatin) + '</div>';
    if (extra)   h += extra;
    return h + '</div>';
  }

  function renderPaper(T){
    var paper = $("paper");
    if (!paper) return;
    var p = S.profile, c = S.customer, dd = S.doc, k = S.kind;
    var isQuote = k === "quote";

    var h = '';

    /* header ------------------------------------------------------------- */
    h += '<header class="p-head">';
    var lsrc = logoSrc();
    h += lsrc
      ? '<img class="p-logo" src="' + esc(lsrc) + '" alt="">'
      : '<div class="p-wordmark">' + (p.name ? esc(p.name) : "Your business") + '</div>';
    h += '<div class="p-doc">';
    h += '<div class="p-doctype' + (isQuote ? " is-quote" : "") + '">' + TITLES[k] + '</div>';
    h += '<div class="p-docnum">' + (dd.number ? esc(dd.number) : "&mdash;") + '</div>';
    if (dd.issue)  h += '<div class="p-docdate">Issued ' + esc(fmtDate(dd.issue)) + '</div>';
    if (!isQuote && dd.supply)
      h += '<div class="p-docdate">Date of supply ' + esc(fmtDate(dd.supply)) + '</div>';
    h += '</div></header><hr class="p-rule">';

    /* parties ------------------------------------------------------------ */
    var fromExtra = "";
    if (p.cr)    fromExtra += '<div class="p-line">CR ' + esc(p.cr) + '</div>';
    if (p.email) fromExtra += '<div class="p-sub">' + esc(p.email) + '</div>';
    if (p.phone) fromExtra += '<div class="p-sub">' + esc(p.phone) + '</div>';
    h += '<div class="p-parties">';
    h += partyBlock("From", p.name, p.address, p.vatin, fromExtra);
    h += partyBlock(isQuote ? "Quotation for" : "Billed to", c.name, c.address, c.vatin, "");
    h += '</div>';

    /* reference strip ---------------------------------------------------- */
    var strip = "";
    if (dd.reference) strip += '<div><span class="k">Reference</span><span class="v">' + esc(dd.reference) + '</span></div>';
    if (isQuote && dd.valid) strip += '<div><span class="k">Valid until</span><span class="v">' + esc(fmtDate(dd.valid)) + '</span></div>';
    if (dd.terms) strip += '<div><span class="k">' + (isQuote ? "Terms" : "Payment") + '</span><span class="v">' + esc(dd.terms) + '</span></div>';
    if (strip) h += '<div class="p-strip">' + strip + '</div>';

    /* items -------------------------------------------------------------- */
    var used = T.rows.filter(function(r){ return r.used && !r.err && r.net !== null; });
    if (!used.length){
      h += '<div class="p-empty">Add a line item and this becomes a document.</div>';
    } else {
      h += '<table class="p-items"><thead><tr>' +
           '<th>Description</th>' +
           '<th class="num p-col-qty">Qty</th>' +
           '<th class="num p-col-unit">Unit price</th>' +
           '<th class="num p-col-vat">VAT<br>rate</th>' +
           '<th class="num p-col-amt">Amount<br>excl. VAT</th>' +
           '</tr></thead><tbody>';
      used.forEach(function(r){
        h += '<tr><td class="desc"><div class="p-itemtitle">' + esc(r.desc) + '</div></td>' +
             '<td class="num">' + trimQty(r.q.v) + '</td>' +
             '<td class="num">' + fmt(r.u.v, T.d) + '</td>' +
             '<td class="num">' + rateCell(r.rate) + '</td>' +
             '<td class="num">' + fmt(r.net, T.d) + '</td></tr>';
      });
      h += '</tbody></table>';

      /* sums ------------------------------------------------------------- */
      h += '<div class="p-sums">';
      h += '<div class="r"><span>Total excluding VAT</span><span>' + money(T.net, T.cur) + '</span></div>';
      var mixed = (T.byRate.S.n ? 1 : 0) + (T.byRate.Z.n ? 1 : 0) + (T.byRate.E.n ? 1 : 0) > 1;
      if (mixed){
        if (T.byRate.S.n) h += '<div class="r muted"><span>Standard-rated at ' + C.vatRateLabel + '</span><span>' + money(T.byRate.S.net, T.cur) + '</span></div>';
        if (T.byRate.Z.n) h += '<div class="r muted"><span>Zero-rated at 0%</span><span>' + money(T.byRate.Z.net, T.cur) + '</span></div>';
        if (T.byRate.E.n) h += '<div class="r muted"><span>Exempt</span><span>' + money(T.byRate.E.net, T.cur) + '</span></div>';
      }
      h += '<div class="r"><span>VAT at ' + C.vatRateLabel + '</span><span>' + money(T.vat, T.cur) + '</span></div>';
      h += '</div>';
      h += '<div class="p-total"><span class="t-label">' +
           (isQuote ? "Quotation total" : "Total including VAT") +
           '</span><span class="t-amount">' + money(T.gross, T.cur) + '</span></div>';

      /* the rial restatement --------------------------------------------- */
      if (T.cur !== "OMR" && T.netOmr !== null){
        h += '<div class="p-omr"><h3>VAT in Omani rials</h3>' +
             '<p>Taxable value <b>' + omr(T.netOmr) + '</b> &middot; VAT due <b>' + omr(T.vatOmr) +
             '</b> &middot; total <b>' + omr(T.grossOmr) + '</b>.</p>' +
             '<p>Converted at 1 ' + esc(T.cur) + ' = ' + fmt(T.fxMicro, 6) + ' OMR.</p></div>';
      }
    }

    /* notes and small print ---------------------------------------------- */
    if (dd.notes)
      h += '<div class="p-notes"><div class="p-label">Notes</div><div class="body">' + esc(dd.notes) + '</div></div>';

    h += '<div class="p-small">';
    if (isQuote){
      h += '<p><b>This is a quotation, not a tax invoice.</b> No VAT is due on this document; the ' +
           'figures show what the VAT would be if it is accepted and invoiced.</p>';
    }
    h += '<p>' + C.notEfawtaraHTML + '</p>';
    h += '<p>' + C.notAdvice + '</p>';
    h += '</div>';

    h += '<footer class="p-foot"><div>' + (p.name ? esc(p.name) : "") +
         (p.vatin ? ' &middot; VATIN ' + esc(p.vatin) : "") + '</div>' +
         '<div class="made">Made with the free VAT invoice maker &middot; aiprofitlab.io</div></footer>';

    paper.innerHTML = h;
    fit();
  }

  /* A quantity of 1 should read "1", not "1.000"; 2.5 should read "2.5". */
  function trimQty(milli){
    var s = fmt(milli, 3);
    return s.indexOf(".") === -1 ? s : s.replace(/\.?0+$/, "");
  }

  /* ------------------------------------------------------- fit the sheet --
     The sheet is 210 mm wide because that is what it prints as. On screen it
     is scaled down to whatever room the container has, so the preview is the
     document rather than a drawing of it. The box's height is set to the
     scaled height, because a transform does not change layout size and the
     unscaled sheet would otherwise leave a metre of empty page below it. */
  function fit(){
    var box = $("paperBox"), paper = $("paper");
    if (!box || !paper) return;
    var w = paper.offsetWidth;
    if (!w) return;
    var s = Math.min(1, box.clientWidth / w);
    paper.style.transform = s < 1 ? "scale(" + s + ")" : "none";
    box.style.height = Math.ceil(paper.offsetHeight * s) + "px";
  }
  var fitTimer = null;
  window.addEventListener("resize", function(){
    if (fitTimer) clearTimeout(fitTimer);
    fitTimer = setTimeout(fit, 120);
  });
  /* A logo arriving late changes the header's height after the fit has run. */
  document.addEventListener("load", function(e){
    if (e.target && e.target.id === "logoPrev") fit();
    if (e.target && e.target.className === "p-logo") fit();
  }, true);

  /* ========================================================= interaction == */
  function onInput(){
    readForm();
    syncCurrency();
    render();
    saveSoon();
  }

  function syncCurrency(){
    var foreign = S.doc.currency !== "OMR";
    var fxFld = $("fx-field");
    if (fxFld) fxFld.hidden = !foreign;
    var lbl = $("fxLabel");
    if (lbl && foreign) lbl.textContent = "1 " + S.doc.currency + " in OMR";
    var vq = $("vw-cur");
    if (vq) vq.textContent = "OMR";
    /* Amounts are held in the currency's own minor unit, so changing the
       currency changes how the same digits are read. Say so rather than
       silently reinterpreting OMR 1.500 as USD 1.50. */
    var note = $("curNote");
    if (note){
      note.textContent = foreign
        ? ("Amounts below are in " + S.doc.currency + ", to " + decimals(S.doc.currency) +
           " decimal places. The VAT is restated in rials on the document.")
        : "Amounts are in rials, to three decimal places — 1 rial is 1,000 baisa.";
    }
    var cv = $("convertBtn");
    if (cv) cv.hidden = S.kind !== "quote";
    /* Fields that only belong to one kind. */
    var vf = $("valid-field");
    if (vf) vf.hidden = S.kind !== "quote";
    var sf = $("supply-field");
    if (sf) sf.hidden = S.kind === "quote";
  }

  document.addEventListener("input", function(e){
    if (e.target && e.target.closest && e.target.closest("#toolForm")) onInput();
  });
  document.addEventListener("change", function(e){
    if (!e.target || !e.target.closest) return;
    if (e.target.name === "kind"){ paintKinds(); onInput(); return; }
    if (e.target.closest("#toolForm")) onInput();
  });

  rowsEl.addEventListener("click", function(e){
    var btn = e.target.closest && e.target.closest(".l-del");
    if (!btn) return;
    if (rowsEl.children.length === 1){
      /* Never leave the tool with no row at all - an empty list reads as
         broken. Emptying the last row is what "delete" means there. */
      var row = rowsEl.children[0];
      row.querySelector(".l-desc").value = "";
      row.querySelector(".l-qty").value = "";
      row.querySelector(".l-unit").value = "";
      row.querySelector(".l-rate").value = "S";
    } else {
      btn.closest(".lrow").remove();
    }
    render(); saveSoon();
  });

  var addBtn = $("addLine");
  if (addBtn) addBtn.addEventListener("click", function(){
    addRow({qty:"1", rate:"S"}, true);
    render(); saveSoon();
  });

  /* ------------------------------------------------- quote -> invoice ----
     The whole point of writing the quote in this tool: accepting it should
     not mean retyping it. Everything that describes the work carries over.
     Everything that identifies the DOCUMENT does not - a tax invoice needs
     its own number from your own sequence, and inheriting the quote's number
     would put two different documents on one reference. */
  var convertBtn = $("convertBtn");
  if (convertBtn) convertBtn.addEventListener("click", function(){
    var oldNum = S.doc.number.trim();
    S.kind = "invoice";
    S.doc.reference = oldNum ? ("Quotation " + oldNum) : S.doc.reference;
    S.doc.number = "";
    S.doc.issue = todayISO();
    if (!S.doc.supply) S.doc.supply = todayISO();
    S.doc.valid = "";
    writeForm();
    syncCurrency();
    render();
    save();
    var n = $("d-number");
    if (n){ n.focus(); }
    var el = $("flags");
    if (el) el.insertAdjacentHTML("afterbegin",
      '<div class="flag"><span><b>Converted to a tax invoice.</b> The lines, the customer and the ' +
      'prices carried over. Give it a number from your own invoice sequence — it must not ' +
      'reuse the quotation&rsquo;s.</span></div>');
    if (typeof gtag === "function")
      gtag("event", "tool_used", {tool_name:"oman-vat-invoice-generator", tool_step:"quote_converted"});
  });

  /* --------------------------------------------------------- erase all --- */
  var wipeBtn = $("wipeBtn");
  if (wipeBtn) wipeBtn.addEventListener("click", function(){
    if (!window.confirm("Erase the saved business profile, this draft and the logo from this browser?"))
      return;
    lsDel(K_PROFILE); lsDel(K_DRAFT); lsDel(K_LAST);
    S.logo = "";
    S.profile = {name:"", address:"", vatin:"", cr:"", email:"", phone:""};
    S.customer = {name:"", address:"", vatin:""};
    S.doc = {number:"", issue:todayISO(), supply:"", currency:"OMR", fx:"",
             reference:"", terms:"", valid:"", notes:""};
    S.kind = "invoice";
    if (logoIn) logoIn.value = "";
    setLines(null);
    writeForm(); paintLogo(); syncCurrency(); render();
    var el = $("saveState");
    if (el) el.textContent = "Erased. Nothing about you is left in this browser.";
  });

  /* ------------------------------------------------------------- print --- */
  var printBtn = $("printBtn");
  if (printBtn) printBtn.addEventListener("click", function(){
    if (printBtn.disabled) return;
    /* Remembered so the next document can offer the next number in YOUR
       sequence. Stored per series, so quotes and invoices count separately. */
    var last = lastNumbers();
    last[seriesKey()] = S.doc.number.trim();
    lsSet(K_LAST, last);
    if (typeof gtag === "function"){
      gtag("event", "tool_output_saved",
           {tool_name:"oman-vat-invoice-generator", output_format:"print", document_type:S.kind});
    }
    window.print();
  });
  /* A print started from Cmd-P rather than the button must not print a sheet
     still scaled to the screen. */
  window.addEventListener("beforeprint", function(){
    var paper = $("paper"), box = $("paperBox");
    if (paper) paper.style.transform = "none";
    if (box) box.style.height = "auto";
  });
  window.addEventListener("afterprint", fit);

  /* ============================================ the VAT add/remove widget ==
     Always in rials: it is the Oman VAT widget, not a general converter, and
     a currency selector on it would only invite the question of which VAT. */
  var vwAmt = $("vw-amt");
  function vatWidget(){
    if (!vwAmt) return;
    var mode = document.querySelector('input[name="vwmode"]:checked');
    mode = mode ? mode.value : "excl";
    Array.prototype.forEach.call(document.querySelectorAll('.vatw .modes label'), function(lb){
      var i = lb.querySelector("input");
      lb.classList.toggle("sel", !!(i && i.checked));
    });
    var a = parseMoney(vwAmt.value, 3, false);
    var net, vat, gross;
    if (!a.ok){ net = vat = gross = null; }
    else if (mode === "incl"){
      gross = a.v;
      /* net = gross x 100/105, in one integer step: x20/21. */
      net = rhu(gross * 100 / (100 + C.vatRatePct));
      vat = gross - net;
    } else {
      net = a.v;
      vat = rhu(net * C.vatRatePct / 100);
      gross = net + vat;
    }
    $("vw-net").textContent   = net === null ? "—" : fmt(net, 3);
    $("vw-vat").textContent   = vat === null ? "—" : fmt(vat, 3);
    $("vw-gross").textContent = gross === null ? "—" : fmt(gross, 3);
  }
  if (vwAmt){
    vwAmt.addEventListener("input", vatWidget);
    Array.prototype.forEach.call(document.querySelectorAll('input[name="vwmode"]'), function(i){
      i.addEventListener("change", vatWidget);
    });
  }

  /* ============================================================== boot === */
  restore();
  syncCurrency();
  render();
  vatWidget();
  save();
  __LEADJS__
})();
"""

# The lead-capture handler, spliced into the script above only when
# LEAD_CAPTURE["enabled"] is true. It is written out in full so that turning it
# on is a one-line change once the privacy work is done - and so that anyone
# reading this file can see exactly what would be sent, which is the point.
LEAD_JS = r"""
  /* ================================================ optional email capture ==
     OFF unless LEAD_CAPTURE["enabled"] is set in the page module. Read the
     block above it there before turning it on: this is the one thing on the
     page that sends anything anywhere, and it is a cross-border transfer of
     personal data under the PDPL.

     Note what it does NOT send. No customer name, no customer VAT number, no
     line item, no amount. The document never leaves the browser; only the
     person asking for the checklist does, and only with the box ticked. */
  (function(){
    var form = document.getElementById("leadForm");
    if (!form) return;
    var msg = document.getElementById("leadMsg");
    var btn = document.getElementById("leadBtn");

    form.addEventListener("submit", function(e){
      e.preventDefault();
      var email = (document.getElementById("lead-email").value || "").trim();
      var name  = (document.getElementById("lead-name").value || "").trim();
      var consent = document.getElementById("lead-consent").checked;
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/.test(email)){
        msg.textContent = "That does not look like an email address."; return;
      }
      if (!consent){
        msg.textContent = "Tick the box first — I need your permission to hold your address."; return;
      }
      btn.disabled = true;
      msg.textContent = "Sending…";

      var attr = (window.APLPage && window.APLPage.attributionFields)
                 ? window.APLPage.attributionFields() : {};
      var rows = [
        {q:"Email",   v:email},
        {q:"Name",    v:name},
        {q:"Wants",   v:"Fawtara readiness checklist"},
        {q:"Consent", v:"Yes — ticked at " + new Date().toISOString()}
      ];
      for (var k in attr) if (Object.prototype.hasOwnProperty.call(attr, k))
        rows.push({q:k, v:String(attr[k] == null ? "" : attr[k])});

      /* text/plain, deliberately, and the same shape the project brief on
         /en/onboarding/ already posts: it is a CORS "simple" request, so the
         browser sends no preflight - which an Apps Script web app cannot
         answer. The script reads e.postData.contents either way, and its
         /exec redirect does return CORS headers, so the reply IS readable and
         a failure is a failure rather than a silent success. */
      fetch(C.leadEndpoint, {
        method: "POST",
        headers: {"Content-Type": "text/plain;charset=utf-8"},
        body: JSON.stringify({source:"oman-vat-invoice-generator", rows:rows})
      }).then(function(r){ return r.json(); }).then(function(res){
        if (!res || !res.ok) throw new Error(res && res.error ? res.error : "refused");
        msg.textContent = "Sent. The checklist is on its way.";
        form.reset();
        if (typeof gtag === "function")
          gtag("event", "generate_lead", {tool_name:"oman-vat-invoice-generator",
                                          lead_source:"fawtara_checklist"});
      }).catch(function(){
        btn.disabled = false;
        msg.textContent = "That did not send. Email hello@aiprofitlab.io instead.";
      });
    });
  })();
"""


def js():
    cfg = {
        "vatRatePct":         R["vat_rate_pct"],
        "vatRateLabel":       R["vat_rate_label"],
        "simplifiedMax":      R["simplified_max"],
        "simplifiedMaxBaisa": R["simplified_max_baisa"],
        "issueWithinDays":    R["issue_within_days"],
        "currencies":         {code: dec for code, dec, _n in CURRENCIES},
        "reserved":           RESERVED_PREFIXES,
        # OMR 1,000,000,000.000 in baisa. Well above any real invoice and well
        # below the point where an integer stops being exact in a double, so
        # an amount that trips it is a typo rather than a transaction.
        "maxMinor":           10 ** 12,
        "maxLogoBytes":       260 * 1024,
        "notEfawtaraHTML":    _not_efawtara_html(),
        "notAdvice":          NOT_ADVICE,
        "leadEndpoint":       LEAD_CAPTURE["endpoint"],
    }
    return (JS_TPL
            .replace("__CFG__", json.dumps(cfg, ensure_ascii=False))
            .replace("__LEADJS__", LEAD_JS if LEAD_CAPTURE["enabled"] else ""))


# ==========================================================================
# Worked examples, computed here rather than typed.
#
# The free-tools plan's first risk is that wrong VAT arithmetic costs a
# business a penalty and they blame the tool. Its mitigation is published
# worked examples - which are only worth anything if they are the SAME
# arithmetic the tool runs. These figures come out of the functions below,
# which mirror the JS line for line, so a table that disagreed with the tool
# would be a table this file could not produce.
#
# selftest() at the bottom of the module asserts the expected column. Run it
# with:  python3 tools/v4/page_tool_invoice.py
# ==========================================================================
def _rhu(x):
    """Round half away from zero - the JS rhu(), in Python."""
    import math
    return -math.floor(-x + 0.5) if x < 0 else math.floor(x + 0.5)


def _line(qty_milli, unit_minor, rate):
    net = _rhu(qty_milli / 1000 * unit_minor)
    vat = _rhu(net * R["vat_rate_pct"] / 100) if rate == "S" else 0
    return net, vat


def _doc(lines):
    net = vat = 0
    for q, u, r in lines:
        n, v = _line(q, u, r)
        net += n
        vat += v
    return net, vat, net + vat


def _b(baisa):
    """Baisa -> '1,234.567'."""
    neg, n = baisa < 0, abs(baisa)
    s = str(n).rjust(4, "0")
    out = "{:,}".format(int(s[:-3])) + "." + s[-3:]
    return ("&minus;" if neg else "") + out


def _q(milli):
    s = ("%d.%03d" % (milli // 1000, milli % 1000)).rstrip("0").rstrip(".")
    return s or "0"


# (case, lines[(qty_milli, unit_baisa, rate)], note, expected(net, vat, gross))
VECTORS = [
    ("One line, a round hundred",
     [(1000, 100000, "S")],
     "The ordinary case.",
     (100000, 5000, 105000)),
    ("Three decimals, rounded up",
     [(3000, 9995, "S")],
     "3 &times; 9.995 is 29.985. Five per cent of that is 1.49925 &mdash; half a baisa is rounded "
     "away from zero, so 1.499.",
     (29985, 1499, 31484)),
    ("The smallest supply there is",
     [(1000, 10, "S")],
     "One baisa of VAT on ten. Exactly half a baisa, and it rounds up rather than disappearing.",
     (10, 1, 11)),
    ("Just under the simplified threshold",
     [(1000, 499999, "S")],
     "A simplified invoice is allowed here &mdash; by one baisa.",
     (499999, 25000, 524999)),
    ("Exactly OMR 500 excluding VAT",
     [(1000, 500000, "S")],
     "A simplified invoice is <b>not</b> allowed. The threshold is under 500, so 500.000 is over it.",
     (500000, 25000, 525000)),
    ("A zero-rated line",
     [(1000, 250000, "Z")],
     "Zero-rated is a rate of 0%, not an absence of VAT. It belongs on the invoice, showing zero.",
     (250000, 0, 250000)),
    ("Standard and zero-rated on one invoice",
     [(2000, 75500, "S"), (1000, 40000, "Z")],
     "VAT is worked out per line and then added up, so a mixed invoice is right on both lines.",
     (191000, 7550, 198550)),
    ("A credit line",
     [(1000, 120000, "S"), (1000, -20000, "S")],
     "A discount entered as a negative line carries its own negative VAT, so the invoice still adds up.",
     (100000, 5000, 105000)),
]


def _vectors_html():
    rows = []
    for case, lines, note, _exp in VECTORS:
        net, vat, gross = _doc(lines)
        qty = " + ".join("%s &times; %s" % (_q(q), _b(u)) for q, u, _r in lines)
        rows.append(
            "        <tr><td>%s<i style=\"display:block;font-style:normal;font-size:.84rem;"
            "color:var(--muted);margin-top:4px\">%s</i></td>"
            "<td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
            % (case, note, qty, _b(net), _b(vat), _b(gross)))
    return "\n".join(rows)


def selftest():
    """Assert every published figure. Not wired into the build - a page module
    that ran assertions on import would fail the whole site build over a test
    fixture - but one command away, and the numbers it checks are the numbers
    the page prints."""
    bad = 0
    for case, lines, _note, exp in VECTORS:
        got = _doc(lines)
        flag = "ok " if got == exp else "FAIL"
        if got != exp:
            bad += 1
        print("  %s %-42s net=%s vat=%s gross=%s" % (flag, case, _b(got[0]), _b(got[1]), _b(got[2])))
    # The threshold itself, since it is the one edge that is a legal rule
    # rather than arithmetic.
    for net, allowed in ((499999, True), (500000, False), (500001, False)):
        got = net < R["simplified_max_baisa"]
        if got != allowed:
            bad += 1
        print("  %s simplified allowed at net %s -> %s"
              % ("ok " if got == allowed else "FAIL", _b(net), got))
    print("  %d failure(s)" % bad)
    return bad


# ==========================================================================
# Page copy
# ==========================================================================
def _not_efawtara_html():
    """The standing sentence, with the Fawtara page linked behind it and the
    URL in a span that only appears in print - a hyperlink on paper is just
    underlined text, and the reader has no way to follow it."""
    linked = NOT_EFAWTARA.replace(
        "Not a Fawtara e-invoice",
        '<a href="%s">Not a Fawtara e-invoice</a>' % R["fawtara_url"])
    return (linked.replace("—", "&mdash;")
            + ' <span class="p-url">aiprofitlab.io%s</span>' % R["fawtara_url"])


FAQ = [
    ("Is this an e-invoice?",
     "No, and it is important that it is not sold as one. This tool makes a <b>VAT tax invoice</b> "
     "&mdash; a document that carries every field Oman requires today. A Fawtara e-invoice is a "
     "different thing entirely: a structured data file passed through a service provider accredited "
     "by the Tax Authority. A PDF printed from a browser cannot be that, no matter how correct the "
     "numbers on it are. From %s you will need an accredited channel as well, which is what the "
     "<a href=\"%s\">e-invoicing page</a> is about."
     % (R["fawtara_phase2"], R["fawtara_url"])),
    ("Can I send these to real customers?",
     "Yes. A tax invoice is defined by the information it carries, not by the software that printed "
     "it, and this tool refuses to print until every mandatory field is filled in. What it cannot do "
     "is keep your accounts, chase the payment, or file your return &mdash; and after your Fawtara "
     "date it stops being enough on its own."),
    ("Does anything I type here reach you?",
     "No. There is no server behind this tool: your business details, your customers&rsquo; names and "
     "VAT numbers, your prices and your logo are worked out and drawn on your own device. They are "
     "remembered in this browser&rsquo;s local storage so you do not retype them, which is a place "
     "only this browser can read &mdash; not us, not another device of yours. Open DevTools &rarr; "
     "Network and use the whole tool: you will see the page&rsquo;s own files load and nothing else "
     "go out. That is deliberate. Your customers never agreed to anything with us, and their details "
     "are not ours to hold."),
    ("What invoice number should I use?",
     "Your own, in one unbroken sequence, never re-used. This tool <b>does not issue numbers</b> "
     "&mdash; it asks for yours, and once you have printed one it offers to add one to it next time. "
     "It will not do that inside the prefixes %s, because those are the sequences AI Profit "
     "Lab&rsquo;s own invoicing systems count off and no tool should be handing out numbers in a "
     "series somebody else is already using."
     % ", ".join(p + "-" for p in RESERVED_PREFIXES)),
    ("When am I allowed to issue a simplified invoice?",
     "When the supply is under %s excluding VAT. That is a threshold, not a guideline: at 500.000 "
     "exactly you are over it, and this tool switches you back to a full tax invoice rather than "
     "printing something that is not valid. A full tax invoice is always acceptable, so if you are "
     "unsure, issue one." % R["simplified_max"]),
    ("How long do I have to issue it?",
     "%d days from the event that triggered it. This tool works the date out from the supply date you "
     "enter and shows it beside the document, and says so plainly if the invoice you are building is "
     "already later than that &mdash; it still prints, because a late invoice is better than no "
     "invoice." % R["issue_within_days"]),
    ("What if I invoice in dollars or dirhams?",
     "You can, and the VAT still has to be shown in Omani rials. Pick the currency, give the tool "
     "your rate, and the document carries a rial restatement of the taxable value and the VAT due "
     "with the rate printed underneath it, so your customer and your accountant can both check the "
     "conversion. The rate is yours to choose and to defend &mdash; this tool does not fetch one, "
     "because fetching one would mean talking to a server."),
    ("Do I need an Arabic version?",
     "The Tax Authority can ask you for one. This tool is English for now; an Arabic twin is coming "
     "and will not be machine-translated, because a machine-translated tax document is the worst "
     "possible thing to hand a business. If you have been asked for Arabic today, your accountant is "
     "the right person to ask what form it has to take."),
    ("Does it check that a VAT number is real?",
     "No, and it says so rather than pretending. It checks that the field is filled in. Whether a "
     "VAT identification number belongs to the business printed beside it is a question only the Tax "
     "Authority can answer, and a tool that green-ticked a number it had not actually verified would "
     "be worse than one that stayed quiet."),
    ("Is any of this tax advice?",
     "No. It is a document generator built from published rules, with the date those rules were last "
     "checked printed on the page. Your accountant and the Oman Tax Authority are the authorities on "
     "what you owe and what your invoices must say."),
]


def _txt(s):
    import html
    return html.unescape(re.sub(r"<[^>]+>", "", s))


def _faq_html():
    return "\n".join(
        f"""      <details>
        <summary>{q}</summary>
        <p class="ans">{a}</p>
      </details>"""
        for q, a in FAQ)


def _faq_schema():
    """FAQPage generated from the same list the page renders, so a hand-typed
    second copy of an answer cannot become a second answer."""
    items = ",".join(
        '{"@type":"Question","name":%s,"acceptedAnswer":{"@type":"Answer","text":%s}}'
        % (json.dumps(_txt(q)), json.dumps(_txt(a)))
        for q, a in FAQ)
    return ('{"@type":"FAQPage","@id":"https://aiprofitlab.io/en/tools/'
            'oman-vat-invoice-generator/#faq","inLanguage":"en","mainEntity":[' + items + "]}")


def _mandatory_html():
    return "\n".join(
        f"      <li><b>{title}</b> &mdash; {why}</li>"
        for title, why in MANDATORY_FULL)


def _sources_html():
    return "\n".join(
        f'      <li><a href="{u}" target="_blank" rel="noopener nofollow">{t}</a></li>'
        for t, u in SOURCES)


def _currency_options():
    return "\n".join(
        f'            <option value="{code}">{code} &mdash; {name}</option>'
        for code, _dec, name in CURRENCIES)


def _lead_html():
    """The email capture. Rendered only when LEAD_CAPTURE['enabled'] is true -
    see the block beside that constant for what has to be true first."""
    if not LEAD_CAPTURE["enabled"]:
        return ""
    return f"""
<section class="s-panel grain pad-s noprint" id="checklist">
  <div class="wrap-n">
    <p class="eyebrow"><span class="star">{STAR}</span>Optional, and only if you want it</p>
    <h2 class="h2">The Fawtara readiness checklist, by email</h2>
    <p>The tool above needs nothing from you. This is separate: twelve things to have done before
      your e-invoicing date, sent once to an address you give me.</p>
    <form id="leadForm" class="fset" style="margin-top:22px">
      <div class="flds">
        <div class="fld"><label for="lead-email">Email<span class="req">*</span></label>
          <input id="lead-email" type="email" autocomplete="email" required></div>
        <div class="fld"><label for="lead-name">Name <span class="opt-tag">(optional)</span></label>
          <input id="lead-name" type="text" autocomplete="name"></div>
        <div class="fld full">
          <label class="consent" style="text-transform:none;letter-spacing:0;font-family:var(--sans)">
            <input id="lead-consent" type="checkbox">
            <span>Send me the checklist and occasional email about running a business in Oman. Your
              address is stored in a Google spreadsheet, which means <b>outside Oman</b>, and is used
              for nothing else. Unsubscribe by replying. See the
              <a href="/en/privacy/">privacy policy</a>.</span>
          </label>
        </div>
      </div>
      <div class="btn-row" style="margin-top:18px">
        <button class="btn btn-teal" id="leadBtn" type="submit">Send it to me</button>
      </div>
      <p class="sidenote" id="leadMsg" role="status"></p>
    </form>
    <p class="sidenote">Nothing you typed into the invoice tool is attached to this. Not your
      customer, not your prices, not your VAT number.</p>
  </div>
</section>
"""


def body():
    return f"""<main id="main">

<section class="phero s-panel grain noprint">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span>Free tool &middot; No sign-up</p>
    <h1 class="h1">Oman VAT tax invoice &amp; quote maker</h1>
    <p class="lede">Fill your business in once. Add your lines. Print a document that carries every
      field an Omani tax invoice has to carry, in a layout that does not look like a spreadsheet.
      It writes quotations too, and turns an accepted quotation into an invoice without retyping it.</p>
    <div class="btn-row" style="margin-top:26px">
      <a class="btn btn-teal" href="#tool">Make an invoice</a>
      <a class="tlink" href="#must">What Oman requires on one <span class="arw">&rarr;</span></a>
    </div>
    <div class="local">
      {LOCK_ICON}
      <p><b>Your customers&rsquo; details never leave your browser.</b> There is no server behind this
        tool and no account to make. Their names, addresses and VAT numbers are worked out and drawn
        on your own device, and remembered only in this browser&rsquo;s own storage so you do not
        retype them &mdash; a place we cannot read. That matters more here than on most pages: the
        data flowing through this tool belongs to <em>your</em> customers, who never agreed to
        anything with us. Open DevTools &rarr; Network and watch it stay quiet.</p>
    </div>
  </div>
</section>

<!-- ----------------------------------------------------------------- tool -->
<section class="s-cream grain noprint" id="tool">
  <div class="wrap">
    <p class="toolbar">
      <span><span class="star">{STAR}</span><b>VAT {R["vat_rate_label"]}</b></span>
      <span>Simplified under <b>{R["simplified_max"]}</b></span>
      <span>Issue within <b>{R["issue_within_days"]} days</b></span>
      <span>Rules verified <b>{LAST_VERIFIED}</b></span>
    </p>

    <!-- data-clarity-mask is the SECOND line of defence. The first is that
         META carries clarity=False, so no recorder loads here at all. This
         attribute is what still protects the customer's details if somebody
         removes that flag without reading why it is there. -->
    <div class="build" data-clarity-mask="true">
      <form id="toolForm" onsubmit="return false">

        <fieldset class="fset">
          <legend><span class="star">{STAR}</span>What are you making?</legend>
          <div class="kinds">
            <label data-kind="invoice">
              <input type="radio" name="kind" value="invoice" checked>
              <b>Tax invoice</b>
              <span>The full one. Every mandatory field, any amount.</span>
            </label>
            <label data-kind="simplified">
              <input type="radio" name="kind" value="simplified">
              <b>Simplified</b>
              <span>Only under {R["simplified_max"]} excluding VAT.</span>
            </label>
            <label data-kind="quote">
              <input type="radio" name="kind" value="quote">
              <b>Quotation</b>
              <span>A price, not a tax document. Converts later.</span>
            </label>
          </div>
          <p class="hint" id="curNote">Amounts are in rials, to three decimal places &mdash; 1 rial is
            1,000 baisa.</p>
        </fieldset>

        <fieldset class="fset">
          <legend><span class="star">{STAR}</span>Your business</legend>
          <p class="hint">Typed once. This browser remembers it for next time, and nowhere else does.</p>
          <div class="flds">
            <div class="fld full">
              <label for="pf-name">Legal name<span class="req" aria-hidden="true">*</span></label>
              <input id="pf-name" type="text" autocomplete="organization"
                     placeholder="The name your VAT registration is in">
            </div>
            <div class="fld full">
              <label for="pf-address">Address<span class="req" aria-hidden="true">*</span></label>
              <textarea id="pf-address" autocomplete="street-address"
                        placeholder="Street, area, town&#10;P.O. Box, postal code, Sultanate of Oman"></textarea>
            </div>
            <div class="fld">
              <label for="pf-vatin">VAT identification number<span class="req" aria-hidden="true">*</span></label>
              <input id="pf-vatin" type="text" placeholder="As it appears on your VAT certificate">
            </div>
            <div class="fld">
              <label for="pf-cr">CR number <span class="opt-tag">(optional)</span></label>
              <input id="pf-cr" type="text" placeholder="1234567">
            </div>
            <div class="fld">
              <label for="pf-email">Email <span class="opt-tag">(optional)</span></label>
              <input id="pf-email" type="email" autocomplete="email">
            </div>
            <div class="fld">
              <label for="pf-phone">Phone <span class="opt-tag">(optional)</span></label>
              <input id="pf-phone" type="tel" autocomplete="tel" placeholder="+968 …">
            </div>
            <div class="fld full">
              <label for="pf-logo">Your logo <span class="opt-tag">(optional, stays on this device)</span></label>
              <input id="pf-logo" type="file" accept="image/png,image/jpeg,image/webp,image/svg+xml">
              <p class="err" id="logoErr" role="alert"></p>
              <img id="logoPrev" alt="" hidden
                   style="max-width:180px;max-height:70px;width:auto;margin-top:4px">
              <button type="button" class="minibtn" id="logoClear" hidden
                      style="justify-self:start;margin-top:8px">Remove the logo</button>
            </div>
          </div>
        </fieldset>

        <fieldset class="fset">
          <legend><span class="star">{STAR}</span>This document</legend>
          <div class="flds">
            <div class="fld">
              <label for="d-number">Number<span class="req" aria-hidden="true">*</span></label>
              <input id="d-number" type="text" placeholder="Your own sequence, e.g. 2026-014">
              <button type="button" class="minibtn" id="nextNum"
                      style="justify-self:start;margin-top:2px">No previous number yet</button>
            </div>
            <div class="fld">
              <label for="d-issue">Date issued<span class="req" aria-hidden="true">*</span></label>
              <input id="d-issue" type="date">
            </div>
            <div class="fld" id="supply-field">
              <label for="d-supply">Date of supply<span class="req" aria-hidden="true">*</span></label>
              <input id="d-supply" type="date">
            </div>
            <div class="fld" id="valid-field" hidden>
              <label for="d-valid">Valid until<span class="req" aria-hidden="true">*</span></label>
              <input id="d-valid" type="date">
            </div>
            <div class="fld">
              <label for="d-currency">Currency</label>
              <select id="d-currency">
{_currency_options()}
              </select>
            </div>
            <div class="fld" id="fx-field" hidden>
              <label for="d-fx"><span id="fxLabel">Rate to OMR</span><span class="req" aria-hidden="true">*</span></label>
              <input id="d-fx" type="text" inputmode="decimal" placeholder="0.384500">
            </div>
            <div class="fld">
              <label for="d-reference">Your reference <span class="opt-tag">(optional)</span></label>
              <input id="d-reference" type="text" placeholder="PO number, job number">
            </div>
            <div class="fld">
              <label for="d-terms">Payment terms <span class="opt-tag">(optional)</span></label>
              <input id="d-terms" type="text" placeholder="Due within 30 days">
            </div>
            <div class="fld full">
              <label for="d-notes">Notes on the document <span class="opt-tag">(optional)</span></label>
              <textarea id="d-notes" placeholder="Anything the customer should read. Line breaks survive."></textarea>
            </div>
          </div>
        </fieldset>

        <fieldset class="fset">
          <legend><span class="star">{STAR}</span>Your customer</legend>
          <p class="hint">Name, address and VAT number are all three mandatory on a full tax invoice.
            The VAT number is the field hand-made invoices miss most often.</p>
          <div class="flds">
            <div class="fld full">
              <label for="c-name">Name<span class="req" aria-hidden="true">*</span></label>
              <input id="c-name" type="text" placeholder="Their full legal name">
            </div>
            <div class="fld full">
              <label for="c-address">Address<span class="req" aria-hidden="true">*</span></label>
              <textarea id="c-address" placeholder="Street, area, town&#10;P.O. Box, postal code"></textarea>
            </div>
            <div class="fld full">
              <label for="c-vatin">Their VAT identification number<span class="req" aria-hidden="true">*</span></label>
              <input id="c-vatin" type="text" placeholder="Ask them for it &mdash; it is on any invoice they issue">
            </div>
          </div>
        </fieldset>

        <fieldset class="fset">
          <legend><span class="star">{STAR}</span>What you supplied</legend>
          <p class="hint">Unit prices exclude VAT. A discount is a line with a negative unit price &mdash;
            it carries its own negative VAT, so the invoice still adds up.</p>
          <div class="lhead" aria-hidden="true">
            <span>Description</span><span>Qty</span><span>Unit price</span>
            <span>VAT</span><span>Amount</span><span></span>
          </div>
          <div id="lines"></div>
          <button type="button" class="addline" id="addLine">+ Add a line</button>
          <div class="runsum" id="runsum"></div>
        </fieldset>
      </form>

      <aside class="side">
        <div class="sidecard">
          <h3><span class="star">{STAR}</span>What this document needs</h3>
          <p class="reqcount" id="reqCount"><b>0</b> of <b>0</b> present</p>
          <ul class="reqs" id="reqList" aria-live="polite"></ul>
          <div id="flags"></div>
          <div class="btn-row" style="margin-top:16px">
            <button type="button" class="btn btn-teal printbtn" id="printBtn" disabled>Fill in what is missing first</button>
          </div>
          <p class="sidenote">Printing opens your browser&rsquo;s own print dialog. Choose
            <b>Save as PDF</b> as the destination and you have the file.</p>
        </div>

        <div class="sidecard">
          <h3><span class="star">{STAR}</span>This browser</h3>
          <p class="sidenote" id="saveState" role="status" style="margin-top:0">Nothing saved yet. What you
            type is kept in this browser only.</p>
          <div class="sidebtns">
            <button type="button" class="minibtn" id="convertBtn" hidden>Turn this quote into an invoice</button>
            <button type="button" class="minibtn danger" id="wipeBtn">Erase everything stored here</button>
          </div>
        </div>

        <div class="sidecard vatw">
          <h3><span class="star">{STAR}</span>Add or remove VAT</h3>
          <div class="row">
            <input id="vw-amt" type="text" inputmode="decimal" placeholder="0.000" aria-label="Amount in rials">
            <span class="cur" id="vw-cur">OMR</span>
          </div>
          <div class="modes">
            <label class="sel"><input type="radio" name="vwmode" value="excl" checked><span>Excludes VAT</span></label>
            <label><input type="radio" name="vwmode" value="incl"><span>Includes VAT</span></label>
          </div>
          <dl>
            <dt>Net</dt><dd id="vw-net">&mdash;</dd>
            <dt>VAT {R["vat_rate_label"]}</dt><dd class="hi" id="vw-vat">&mdash;</dd>
            <dt>Gross</dt><dd id="vw-gross">&mdash;</dd>
          </dl>
        </div>
      </aside>
    </div>
  </div>
</section>

<!-- -------------------------------------------------------------- preview -->
<section class="s-white grain pr" id="preview">
  <div class="wrap">
    <p class="eyebrow noprint"><span class="star">{STAR}</span>What prints</p>
    <h2 class="h2 noprint">The document</h2>
    <p class="lede noprint">This is the sheet itself, scaled to fit the screen &mdash; not a drawing of
      it. What you see is what comes out of the printer, and out of &ldquo;Save as PDF&rdquo;.</p>
    <div class="paperwrap" data-clarity-mask="true">
      <div class="paperbox" id="paperBox">
        <article class="paper" id="paper"></article>
      </div>
    </div>
  </div>
</section>

<!-- ---------------------------------------------------------- what it needs -->
<section class="s-panel grain noprint" id="must">
  <div class="wrap-n">
    <div class="asterism"><span>{STAR}</span></div>
    <p class="eyebrow"><span class="star">{STAR}</span>The rules this tool enforces</p>
    <h2 class="h2">What a full Omani tax invoice must carry</h2>
    <p class="lede">Eleven requirements, and the tool will not print until every one of them is
      answered. They are inputs, not options &mdash; a missing field is the difference between a tax
      document and a piece of paper.</p>
    <ul class="plainlist">
{_mandatory_html()}
    </ul>
  </div>
</section>

<section class="s-cream grain noprint">
  <div class="wrap-n">
    <p class="eyebrow"><span class="star">{STAR}</span>Two hard edges</p>
    <h2 class="h2">The {R["simplified_max"]} line, and the {R["issue_within_days"]} days</h2>
    <p><b>A simplified invoice is only allowed when the supply is under {R["simplified_max"]}
      excluding VAT.</b> It is a threshold and not a guideline: at 500.000 exactly you are over it.
      That is why this tool refuses rather than warns &mdash; a simplified invoice above the line is
      not a slightly worse invoice, it is not a valid one. A full tax invoice is always acceptable,
      so when in doubt, issue one.</p>
    <p style="margin-top:1em"><b>An invoice must be issued within {R["issue_within_days"]} days of the
      event that triggered it.</b> Enter the date of supply and the tool shows you the date it has to
      be out by, and says so if the document you are building is already past it. It still prints: a
      late invoice is better than no invoice, and the timing is a conversation with your accountant
      rather than a reason to stop you.</p>
    <p style="margin-top:1em">One more that catches exporters: <b>the VAT has to be shown in Omani
      rials even when the invoice is in another currency.</b> Pick a currency other than OMR and the
      tool asks for your rate, then prints the taxable value and the VAT due in rials with the rate
      underneath, so the conversion can be checked rather than taken on trust.</p>
  </div>
</section>

<!-- ------------------------------------------------------ the honest bit -->
<section class="s-panel grain noprint" id="notefawtara">
  <div class="wrap-n">
    <p class="eyebrow"><span class="star">{STAR}</span>What this is not</p>
    <h2 class="h2">This is a tax invoice. It is not an e&#8209;invoice.</h2>
    <p>Those two words get used as if they meant the same thing, and they do not. A <b>VAT tax
      invoice</b> is a document carrying the information Oman requires &mdash; which is what this tool
      makes, and what your customer and your accountant need today. A <b>Fawtara e-invoice</b> is a
      structured data file, in UBL 2.1 XML or PDF/A-3, passed through a service provider accredited by
      the Tax Authority.</p>
    <div class="notclaim">
      <p><b>A PDF printed from a browser cannot be a Fawtara e-invoice.</b> Not this one, and not any
        other &mdash; the format and the channel are the whole definition, and a printed page has
        neither. Every document this tool produces says so on its face, in one line:</p>
      <p style="font-style:italic">&ldquo;{NOT_EFAWTARA}&rdquo;</p>
      <p>We would rather write that on the paper than have you find out from the Tax Authority. If you
        want to know which date is yours and what to have done before it,
        <a href="{R["fawtara_url"]}">the e-invoicing page</a> is two questions and a checklist.</p>
    </div>
  </div>
</section>

<!-- ------------------------------------------------------ worked examples -->
<section class="s-cream grain noprint" id="maths">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span>Check the arithmetic</p>
    <h2 class="h2">Worked examples, including the awkward ones</h2>
    <p class="lede">Every figure below comes out of the same code the tool runs, so the table cannot
      quietly disagree with the page. Money is held as whole baisa from the first keystroke to the
      printed page &mdash; there is no point at which a total becomes 949.9999998.</p>
    <div class="vscroll">
      <table class="vectors">
        <thead>
          <tr><th>Case</th><th>Lines</th><th>Excl. VAT</th><th>VAT {R["vat_rate_label"]}</th><th>Total</th></tr>
        </thead>
        <tbody>
{_vectors_html()}
        </tbody>
      </table>
    </div>
    <p style="margin-top:20px;color:var(--muted);font-size:.95rem">VAT is calculated per line and
      then added up, rather than taken on the invoice total. That is why a mixed standard and
      zero-rated invoice comes out right on both lines, and it is the same order of operations
      accounting software uses. Halves round away from zero, so half a baisa becomes a baisa rather
      than disappearing.</p>
  </div>
</section>

<!-- ------------------------------------------------------------------ faq -->
<section class="s-panel grain noprint">
  <div class="wrap-n">
    <div class="asterism"><span>{STAR}</span></div>
    <p class="eyebrow"><span class="star">{STAR}</span>The questions people actually ask</p>
    <h2 class="h2">Straight answers</h2>
    <div class="faq" style="margin-top:clamp(22px,3vw,38px)">
{_faq_html()}
    </div>
  </div>
</section>
{_lead_html()}
<!-- ------------------------------------------------------------ the facts -->
<section class="s-dark grain noprint" id="facts">
  <div class="wrap-n">
    <p class="eyebrow"><span class="star">{STAR}</span>Where these rules come from</p>
    <h2 class="h2">The rules on this page</h2>
    <p class="lede">Every rate, threshold and deadline the tool enforces is one of these. If the Tax
      Authority moves one, this is the block that changes.</p>
    <div class="facts-box" style="margin-top:clamp(24px,3vw,34px)">
      <dl>
        <dt>VAT rate</dt>
        <dd><em>{R["vat_rate_label"]}</em> standard rate. Zero-rated and exempt supplies exist and are
          selectable per line</dd>
        <dt>Simplified</dt>
        <dd>Allowed only <em>under {R["simplified_max"]}</em> excluding VAT. A hard threshold</dd>
        <dt>Issue window</dt>
        <dd><em>{R["issue_within_days"]} days</em> from the triggering event</dd>
        <dt>Currency</dt>
        <dd>The VAT must be shown in <em>OMR</em> even where the invoice is in another currency</dd>
        <dt>Arabic</dt>
        <dd>The Tax Authority can request an Arabic version of an invoice</dd>
        <dt>VAT registration</dt>
        <dd>{R["vat_mandatory"]} mandatory, {R["vat_voluntary"]} voluntary</dd>
        <dt>E-invoicing</dt>
        <dd>A document from this tool is <em>not</em> a Fawtara e-invoice. Phase 2 lands
          {R["fawtara_phase2"]} &mdash; <a href="{R["fawtara_url"]}">which date is yours</a></dd>
      </dl>
      <ul class="srcs">
{_sources_html()}
      </ul>
      <p class="verified">Rules verified <b>{LAST_VERIFIED}</b> &middot; reviewed quarterly, and again
        after any Tax Authority decision that moves a rate or a threshold</p>
    </div>
    <p class="disclaimer">{NOT_ADVICE} This page is a plain-language summary and not a substitute for
      your accountant. Verify anything here against
      <a href="{R["ota_site"]}" target="_blank" rel="noopener">taxoman.gov.om</a> before you act on
      it. AI Profit Lab is not an accredited e-invoicing service provider, and does not check whether
      a VAT number you type is real &mdash; only the Tax Authority can do that.</p>
  </div>
</section>

<!-- ------------------------------------------------------------------ cta -->
<section class="s-panel grain pad-s noprint">
  <div class="wrap-n">
    <p class="eyebrow"><span class="star">{STAR}</span>If you are typing these one at a time</p>
    <h2 class="h2">The version that remembers your customers</h2>
    <p>This tool is deliberately one document at a time, with nothing kept anywhere we can see. That
      is the right trade for something free. What it is not is a system: no customer list, no
      numbering that cannot be skipped, no record of what has been paid, and nothing that will connect
      to an accredited channel when your Fawtara date arrives. Building that &mdash; quotes, orders and
      invoices in one place, with customer records clean enough to validate &mdash; is the work we sell,
      at published prices.</p>
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
    slug="vatinvoice",
    title="Free Oman VAT tax invoice & quote maker | AI Profit Lab",
    desc=("Make a valid Omani VAT tax invoice or quotation in your browser: every mandatory field "
          "enforced, %s VAT worked out in whole baisa, simplified invoices held to the %s threshold, "
          "and a branded PDF. No sign-up, and nothing you type is ever sent anywhere."
          % (R["vat_rate_label"], R["simplified_max"])),
    nav="/en/tools/oman-vat-invoice-generator/",
    # NO SESSION RECORDER ON THIS PAGE. See kit.head_html(): Clarity rebuilds
    # the DOM, and this page's DOM contains a live preview of the visitor's
    # invoice - their customer's name, address and VAT number, rendered as
    # text. That was measured going out in a POST to e.clarity.ms/collect
    # before this line existed. The page promises those details never leave
    # the browser; this is what makes the promise true rather than aspirational.
    clarity=False,
    next=("Next", "Which e-invoicing date is yours", R["fawtara_url"]),
    schema=_faq_schema() + "$$SPLIT$$" + """{
  "@type":"WebApplication",
  "@id":"https://aiprofitlab.io/en/tools/oman-vat-invoice-generator/#tool",
  "name":"Oman VAT tax invoice and quotation maker",
  "applicationCategory":"FinanceApplication",
  "operatingSystem":"Any",
  "browserRequirements":"Runs entirely in the browser. No account, and no data leaves the device.",
  "url":"https://aiprofitlab.io/en/tools/oman-vat-invoice-generator/",
  "inLanguage":"en",
  "isAccessibleForFree":true,
  "featureList":"Full Oman VAT tax invoice with every mandatory field enforced; simplified tax invoice below OMR 500 excluding VAT; quotations, and conversion of a quotation into an invoice; VAT restated in OMR for invoices in another currency; VAT add and remove calculator",
  "offers":{"@type":"Offer","price":"0","priceCurrency":"OMR"},
  "publisher":{"@id":"https://aiprofitlab.io/#organization"}
}""",
)


if __name__ == "__main__":
    print("Oman VAT invoice tool - arithmetic self test")
    raise SystemExit(1 if selftest() else 0)
