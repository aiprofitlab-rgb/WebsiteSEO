#!/usr/bin/env python3
"""Free tool 3 - WhatsApp chat link and branded QR maker.

Two things a small Omani business actually needs and cannot easily get in one
place: a wa.me link with the first message already written, and a QR code that
looks like it belongs to their brand instead of to a barcode scanner.

WHAT MAKES THIS ONE WORTH BUILDING. Every generic QR site renders black
squares. This one renders the brand palette - ink green modules, gold finder
eyes, rounded corners, the mark on a centre plate - by porting the matrix
rules that already exist in tools/build_vcard_qr.py from Pillow to the
browser. The encoder, the reader and the art all live in tools/v4/qr_js.py.

THE RULES THIS PAGE KEEPS, all of them load-bearing:

  * 100% client-side. No backend, no form post, no fetch. The number and the
    message are turned into a link and a code on the visitor's own device.
    The page says so, and the claim has to survive DevTools > Network.

  * NO URL SHORTENER AND NO HOSTED REDIRECT, ever. A redirect on
    aiprofitlab.io would invite phishing use, takedown requests and domain
    blocklisting that would take the site's search and email presence with
    it. The QR encodes the visitor's own wa.me link and we host nothing.
    This is risk 15 in the free-tools plan and it is not a preference.

  * Nothing is offered for download until it has been decoded. The art is
    rendered, read back off the canvas pixel by pixel and run through the
    decoder before the button unlocks - because a logo plate one size too big
    produces a code that looks perfect and does not scan. See DECODE MARGIN
    below.

DECODE MARGIN. Decoding on a clean digital render is not the bar; a phone
scan adds blur, glare and angle. So the logo plate is grown to the largest
size that still leaves MARGIN of the symbol's error-correction budget unspent,
and the page shows that figure rather than a green tick nobody can check.

ARABIC. English page, per the free-tools plan - it is not in MODULES_AR and
must not be added without a native pass. The away-message tab is a different
matter: it WRITES Arabic, because an away message that is not bilingual is
useless to the audience. Those strings are in AWAY_AR and are the one part of
this page that wants Nahid's native review, exactly like the /pay-ar/ strings.
"""
import json

from kit import STAR
from tool_kit import LOCK_ICON, SHELL_CSS
import qr_js

# --------------------------------------------------------------------------
# Dial codes. Oman first and selected by default - this is a tool for Omani
# businesses - with the countries the rest of the audience actually holds
# numbers in. `n` is the national number length, used only to tell someone
# they have typed too few digits; it is never used to reject a number, because
# numbering plans change faster than this file does.
# --------------------------------------------------------------------------
COUNTRIES = [
    ("OM", "Oman", "968", 8, "9924 5250"),
    ("AE", "United Arab Emirates", "971", 9, "50 123 4567"),
    ("SA", "Saudi Arabia", "966", 9, "50 123 4567"),
    ("QA", "Qatar", "974", 8, "3312 3456"),
    ("BH", "Bahrain", "973", 8, "3600 1234"),
    ("KW", "Kuwait", "965", 8, "5001 2345"),
    ("IN", "India", "91", 10, "98200 12345"),
    ("PK", "Pakistan", "92", 10, "301 2345678"),
    ("BD", "Bangladesh", "880", 10, "1712 345678"),
    ("PH", "Philippines", "63", 10, "917 123 4567"),
    ("EG", "Egypt", "20", 10, "100 123 4567"),
    ("JO", "Jordan", "962", 9, "7 9012 3456"),
    ("GB", "United Kingdom", "44", 10, "7400 123456"),
    ("US", "United States / Canada", "1", 10, "202 555 0134"),
]

# The first message, offered both ways round. These are the messages a
# customer sends TO the business, not the other way round - the whole point of
# a prefilled link is that the customer does not have to think of an opener.
PRESETS = [
    ("Order", "Hello, I would like to place an order."),
    ("Price list", "Hello, I saw your flyer. Please send me your price list."),
    ("Booking", "Hello, I would like to book an appointment."),
    ("Delivery", "Hello, do you deliver to Muscat? What is the delivery time?"),
    ("&#1591;&#1604;&#1576;", "&#1605;&#1585;&#1581;&#1576;&#1575;&#1611;&#1548; &#1571;&#1585;&#1610;&#1583; &#1571;&#1606; &#1571;&#1591;&#1604;&#1576;."),
    ("&#1571;&#1587;&#1593;&#1575;&#1585;", "&#1605;&#1585;&#1581;&#1576;&#1575;&#1611;&#1548; &#1588;&#1575;&#1607;&#1583;&#1578; &#1573;&#1593;&#1604;&#1575;&#1606;&#1603;&#1605;. &#1605;&#1606; &#1601;&#1590;&#1604;&#1603; &#1571;&#1585;&#1587;&#1604; &#1604;&#1610; &#1602;&#1575;&#1574;&#1605;&#1577; &#1575;&#1604;&#1571;&#1587;&#1593;&#1575;&#1585;."),
]

# The three palettes, and what each is for. Only these three: each was checked
# by decoding the rendered pixels, and an unchecked palette on a page whose
# whole claim is "we checked it" would be the one thing that cannot ship.
PALETTES = [
    ("cream", "Ink on cream", "The default. Dark modules on a light ground, which every scanner ever "
                              "made reads.", False),
    ("dark", "Cream on ink", "For a dark flyer or a dark social post. This is an <em>inverted</em> "
                             "code &mdash; see the warning under it.", True),
    ("mono", "Pure black", "No mark, no rounding, maximum contrast. For a print vendor who asks for "
                           "plain artwork, or a scanner you do not trust.", False),
]

CSS = SHELL_CSS + """
/* A heading the tool section needs for its outline and does not need to
   show - the tabs are the visible label. Same idiom as .top-wa span in kit. */
.vh{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap}

/* ============================================================== the tabs */
.tabs{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 clamp(22px,3vw,32px)}
.tabs button{
  font-family:var(--mono);font-size:.76rem;letter-spacing:.1em;text-transform:uppercase;
  color:var(--muted);background:transparent;border:1px solid var(--line);border-radius:99px;
  padding:11px 20px;cursor:pointer;transition:color .2s,border-color .2s,background .2s;
}
.tabs button:hover{border-color:var(--amber);color:var(--teal-950)}
.tabs button[aria-selected=true]{background:var(--teal-950);border-color:var(--teal-950);color:var(--cream)}
.tabs button:focus-visible{outline:2px solid var(--amber);outline-offset:3px}

/* ============================================================ the layout */
.rig{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,420px);gap:clamp(22px,3vw,40px);align-items:start}
.pane[hidden]{display:none}

fieldset.fset{border:0;margin:0 0 clamp(20px,2.6vw,28px);padding:0;min-width:0}
fieldset.fset legend{
  padding:0;margin:0 0 14px;font-family:var(--mono);font-size:.76rem;letter-spacing:.14em;
  text-transform:uppercase;color:var(--amber-text);
}
.fset .hint{margin:10px 0 0;font-size:.88rem;line-height:1.6;color:var(--muted)}

/* --------------------------------------------------------------- fields
   The same field component as the checkout and the invoice tool, on purpose:
   a visitor who uses two of these should not meet two form designs from one
   company. */
.flds{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:15px}
.fld{display:flex;flex-direction:column;gap:7px;min-width:0}
.fld.full{grid-column:1/-1}
.fld label{
  font-family:var(--mono);font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);
}
.fld label .opt{text-transform:none;letter-spacing:0;font-family:var(--sans);opacity:.75}
.fld input,.fld textarea,.fld select{
  font-family:var(--sans);font-size:1rem;color:var(--ink);background:var(--white);
  border:1px solid var(--line);border-radius:10px;padding:13px 15px;width:100%;min-width:0;
  transition:border-color .2s,box-shadow .2s;
}
.fld textarea{resize:vertical;min-height:96px;line-height:1.55}
.fld input::placeholder,.fld textarea::placeholder{color:rgba(90,102,93,.5)}
.fld input:focus,.fld textarea:focus,.fld select:focus{
  outline:none;border-color:var(--teal);box-shadow:0 0 0 3px rgba(15,110,86,.13);
}
.fld input[aria-invalid=true]{border-color:var(--alert);box-shadow:0 0 0 3px rgba(166,67,31,.13)}
.fld .err{font-size:.84rem;color:var(--alert)}
.fld .err:empty{display:none}
.fld[hidden]{display:none}
.fld select{
  appearance:none;-webkit-appearance:none;cursor:pointer;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 8'%3E%3Cpath fill='none' stroke='%235A665D' stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round' d='M1 1.5 6 6.5l5-5'/%3E%3C/svg%3E");
  background-repeat:no-repeat;background-position:right 15px center;background-size:12px 8px;padding-right:40px;
}
.cnt{font-family:var(--mono);font-size:.74rem;letter-spacing:.06em;color:var(--muted);text-align:right}
.cnt b{color:var(--teal-950);font-weight:500}
.cnt.over b{color:var(--alert)}

/* ------------------------------------------------------------- presets */
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0 0}
.chips button{
  font-family:var(--mono);font-size:.72rem;letter-spacing:.07em;color:var(--teal-950);
  background:var(--white);border:1px solid var(--line);border-radius:99px;padding:8px 14px;cursor:pointer;
  transition:border-color .2s,background .2s;
}
.chips button:hover{border-color:var(--amber);background:var(--panel)}
.chips button[lang=ar]{font-family:var(--sans);font-size:.85rem;letter-spacing:0}

/* ------------------------------------------------------------ palettes */
.pals{display:grid;gap:10px}
.pals label{
  display:grid;grid-template-columns:auto 1fr;gap:14px;align-items:start;cursor:pointer;
  border:1px solid var(--line);border-radius:12px;padding:13px 15px;background:var(--white);
  transition:border-color .2s,background .2s;
}
.pals label:hover{border-color:var(--amber)}
.pals label.sel{border-color:var(--teal);background:var(--panel);box-shadow:0 0 0 1px var(--teal) inset}
.pals input{position:absolute;opacity:0;width:1px;height:1px}
.pals .sw{width:34px;height:34px;border-radius:9px;border:1px solid var(--line);flex:none;position:relative;overflow:hidden}
.pals .sw i{position:absolute;display:block;border-radius:2px}
.pals b{display:block;font-weight:500;font-size:.99rem;color:var(--teal-950);line-height:1.3}
.pals span{display:block;font-size:.84rem;line-height:1.5;color:var(--muted);margin-top:4px}
.pals input:focus-visible + .sw{outline:2px solid var(--amber);outline-offset:3px}

/* ============================================================ the output */
.out{
  position:sticky;top:96px;border:1px solid var(--line);border-radius:20px;background:var(--white);
  padding:clamp(20px,2.4vw,26px);
}
.out h3{
  font-family:var(--mono);font-size:.74rem;letter-spacing:.14em;text-transform:uppercase;
  color:var(--amber-text);margin:0 0 14px;font-weight:400;
}
.link{
  font-family:var(--mono);font-size:.82rem;line-height:1.55;color:var(--teal-950);word-break:break-all;
  background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin:0;
  max-height:7.2em;overflow-y:auto;
}
.link.empty{color:var(--muted)}
.acts{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0 0}
.acts button,.acts a{
  font-family:var(--mono);font-size:.72rem;letter-spacing:.09em;text-transform:uppercase;
  border-radius:99px;padding:9px 15px;cursor:pointer;text-decoration:none;
  border:1px solid var(--line);background:transparent;color:var(--teal-950);
  transition:color .2s,border-color .2s,background .2s;
}
.acts button:hover,.acts a:hover{background:var(--teal-950);border-color:var(--teal-950);color:var(--cream)}
.acts .go{background:var(--wa);border-color:var(--wa);color:#fff}
.acts .go:hover{background:#199e52;border-color:#199e52}
.acts button:disabled{opacity:.4;cursor:not-allowed}
.acts button:disabled:hover{background:transparent;color:var(--teal-950);border-color:var(--line)}

/* -------------------------------------------------------------- the code */
.qrbox{margin:clamp(18px,2.4vw,24px) 0 0;text-align:center}
.qrbox canvas{
  width:100%;max-width:300px;height:auto;border-radius:14px;border:1px solid var(--line);
  image-rendering:-webkit-optimize-contrast;
}
.qrbox canvas[hidden]{display:none}
.qrph{
  max-width:300px;margin:0 auto;aspect-ratio:1;border:1px dashed var(--line);border-radius:14px;
  display:flex;align-items:center;justify-content:center;padding:24px;
  font-size:.9rem;line-height:1.55;color:var(--muted);
}
/* display beats [hidden] every time - the same trap the invoice tool's .fld
   carries a note about, and the reason the placeholder once sat under a
   finished code instead of behind it. */
.qrph[hidden]{display:none}

/* the verification line - the one number on this page worth reading */
.chk{
  display:flex;gap:11px;align-items:flex-start;margin:16px 0 0;text-align:start;
  border-top:1px solid var(--line);padding-top:15px;
}
.chk svg{width:17px;height:17px;flex:none;margin-top:2px;fill:var(--teal)}
.chk p{margin:0;font-size:.86rem;line-height:1.6;color:var(--muted)}
.chk b{color:var(--teal-950);font-weight:500}
.chk[hidden]{display:none}
.chk.warn svg{fill:var(--alert)}
.chk.warn b{color:var(--alert)}
.chk .num{font-family:var(--mono);font-variant-numeric:tabular-nums}

/* ====================================================== the chat preview */
.phone{
  border:1px solid var(--line);border-radius:22px;background:var(--panel);padding:14px;
  margin:clamp(18px,2.4vw,24px) 0 0;
}
.phone .bar{
  display:flex;align-items:center;gap:10px;padding:0 4px 12px;border-bottom:1px solid var(--line);
}
.phone .av{
  width:30px;height:30px;border-radius:50%;background:var(--teal-900);flex:none;
  display:flex;align-items:center;justify-content:center;
}
.phone .av svg{width:17px;height:17px;fill:var(--cream)}
.phone .who{font-size:.9rem;font-weight:500;color:var(--teal-950);line-height:1.2}
.phone .who span{display:block;font-family:var(--mono);font-size:.7rem;color:var(--muted);margin-top:3px}
.phone .thread{padding:16px 4px 6px;min-height:90px;display:flex;flex-direction:column;align-items:flex-end}
.bub{
  background:#DCF8C6;border-radius:14px 14px 4px 14px;padding:10px 13px;max-width:85%;
  font-size:.93rem;line-height:1.5;color:#12261B;white-space:pre-wrap;word-break:break-word;text-align:start;
}
.bub .tx{white-space:pre-wrap}
.bub .tx:empty::before{content:"Your message appears here";color:#5A665D;opacity:.7}
.bub[dir=rtl]{border-radius:14px 14px 14px 4px;text-align:right}
.bub .t{
  display:block;font-family:var(--mono);font-size:.62rem;color:#5A665D;text-align:right;margin-top:5px;
}
.phone .cap{margin:10px 4px 0;font-size:.8rem;line-height:1.5;color:var(--muted)}

/* ======================================================== away messages */
.away{display:grid;gap:14px;margin:clamp(18px,2.4vw,26px) 0 0}
.msg{border:1px solid var(--line);border-radius:16px;background:var(--white);padding:18px 20px}
.msg .top{display:flex;justify-content:space-between;align-items:center;gap:12px;margin:0 0 12px}
.msg .top b{
  font-family:var(--mono);font-size:.72rem;letter-spacing:.13em;text-transform:uppercase;
  color:var(--amber-text);font-weight:400;
}
.msg pre{
  margin:0;font-family:var(--sans);font-size:.96rem;line-height:1.65;color:var(--ink);
  white-space:pre-wrap;word-break:break-word;
}
.msg pre[dir=rtl]{text-align:right}
.msg .cp{
  font-family:var(--mono);font-size:.68rem;letter-spacing:.09em;text-transform:uppercase;
  color:var(--teal-950);background:transparent;border:1px solid var(--line);border-radius:99px;
  padding:7px 13px;cursor:pointer;flex:none;transition:background .2s,color .2s,border-color .2s;
}
.msg .cp:hover{background:var(--teal-950);border-color:var(--teal-950);color:var(--cream)}
.days{display:flex;flex-wrap:wrap;gap:7px}
.days label{
  display:inline-flex;align-items:center;cursor:pointer;font-family:var(--mono);font-size:.72rem;
  letter-spacing:.06em;text-transform:uppercase;color:var(--muted);background:var(--white);
  border:1px solid var(--line);border-radius:99px;padding:8px 13px;transition:all .2s;
}
.days label:hover{border-color:var(--amber);color:var(--teal-950)}
.days label.sel{background:var(--teal-950);border-color:var(--teal-950);color:var(--cream)}
.days input{position:absolute;opacity:0;width:1px;height:1px}
.days input:focus-visible + span{outline:2px solid var(--amber);outline-offset:4px;border-radius:3px}

/* ========================================================= print sizing */
.sizes{width:100%;border-collapse:collapse;margin:clamp(20px,2.6vw,28px) 0 0;font-size:.95rem}
.sizes th,.sizes td{text-align:start;padding:12px 14px;border-bottom:1px solid var(--line)}
.sizes th{
  font-family:var(--mono);font-size:.7rem;letter-spacing:.12em;text-transform:uppercase;
  color:var(--muted);font-weight:400;
}
.sizes td:first-child{color:var(--teal-950);font-weight:500}
.sizes td .num{font-family:var(--mono);font-variant-numeric:tabular-nums}
.tw{overflow-x:auto}

/* ------------------------------------------------------------- rule grid */
.why{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:clamp(16px,2.2vw,26px);margin:clamp(24px,3vw,36px) 0 0}
.why div{border:1px solid var(--line-dark);border-radius:16px;padding:22px 24px}
.why h3{font-size:1.15rem;color:var(--cream);margin:0 0 9px}
.why p{margin:0;font-size:.94rem;line-height:1.62;color:rgba(241,239,232,.72)}
.why p + p{margin-top:10px}

/* ---------------------------------------------------------------- steps */
.steps{list-style:none;margin:clamp(22px,3vw,32px) 0 0;padding:0;counter-reset:s}
.steps li{border-top:1px solid var(--line);padding:20px 0;display:grid;grid-template-columns:auto 1fr;gap:18px}
.steps li:last-child{border-bottom:1px solid var(--line)}
.steps .n{font-family:var(--mono);font-size:.8rem;letter-spacing:.1em;color:var(--amber-text);padding-top:.3em}
.steps b{display:block;font-family:var(--display);font-weight:400;font-size:1.2rem;color:var(--teal-950);margin-bottom:6px}
.steps span{display:block;font-size:.96rem;line-height:1.62;color:var(--muted)}
.steps code{font-family:var(--mono);font-size:.86em;background:var(--panel-2);border-radius:5px;padding:2px 6px}

/* ------------------------------------------------------------------ faq */
.faq{margin:clamp(22px,3vw,32px) 0 0}
.faq details{border-bottom:1px solid var(--line)}
.faq details:first-child{border-top:1px solid var(--line)}
.faq summary{
  cursor:pointer;list-style:none;padding:19px 34px 19px 0;position:relative;
  font-size:1.04rem;line-height:1.5;color:var(--teal-950);font-weight:500;
}
.faq summary::-webkit-details-marker{display:none}
.faq summary::after{
  content:"";position:absolute;right:6px;top:50%;width:9px;height:9px;margin-top:-6px;
  border-right:1.6px solid var(--amber);border-bottom:1.6px solid var(--amber);
  transform:rotate(45deg);transition:transform .22s var(--ease);
}
.faq details[open] summary::after{transform:rotate(-135deg);margin-top:-2px}
.faq summary:focus-visible{outline:2px solid var(--amber);outline-offset:2px;border-radius:4px}
.faq .a{padding:0 0 20px;margin:0;font-size:.98rem;line-height:1.7;color:var(--muted);max-width:74ch}
.faq .a p{margin:0 0 12px}
.faq .a p:last-child{margin:0}
.faq .a a{color:var(--teal)}

@media (max-width:1000px){
  .rig{grid-template-columns:minmax(0,1fr)}
  .out{position:static}
  .qrbox canvas,.qrph{max-width:340px}
}
@media (max-width:760px){
  .why{grid-template-columns:minmax(0,1fr)}
}
@media (max-width:560px){
  .flds{grid-template-columns:minmax(0,1fr)}
  .steps li{grid-template-columns:1fr;gap:6px}
  .tabs button{flex:1 1 auto;text-align:center}
}
"""


# --------------------------------------------------------------------------
# Print sizing. Two independent rules of thumb, both widely used and both
# stated as rules of thumb on the page rather than as standards, because they
# are not standards:
#   * the code should be about a tenth of the distance it is read from;
#   * a printed module should not fall below ~0.5 mm on ordinary presses.
# The page shows BOTH for the code actually on screen, and takes the larger.
# --------------------------------------------------------------------------
DISTANCES = [
    ("In the hand", "A business card, a receipt, a product label", "25 cm", 2.5),
    ("On a counter", "A table talker or a till-side sticker", "50 cm", 5.0),
    ("On a wall", "A shop window or a door", "1.5 m", 15.0),
    ("Across a room", "A pull-up banner or a wall poster", "4 m", 40.0),
]

FAQ = [
    ("Does anything I type get sent to you?",
     "<p>No. The link and the code are both built by JavaScript running on your own device. There is "
     "no server behind this page, no form submission and no upload.</p>"
     "<p>Check it rather than believe it: open your browser's developer tools, watch the Network tab "
     "and use the whole tool. The page's own files load at the start, and after that the only thing "
     "that leaves is the same anonymous visit counting that runs on every page of this site, plus one "
     "ping saying a code was made and which palette it used. Your number and your message are in "
     "neither, because nothing in this tool ever hands them to anything that could send them.</p>"),
    ("Is the QR code linked to your website in any way?",
     "<p>No, and deliberately so. The code contains your <code>wa.me</code> link and nothing else. We "
     "do not run a redirect, a short link or a tracking hop, so there is nothing of ours between your "
     "customer and your chat &mdash; nothing that can break, expire, start counting your scans, or "
     "stop working if this website ever disappears.</p>"),
    ("Will the code still work if I change my mind about the message?",
     "<p>No &mdash; and this is the one thing to get right before you print. The message is baked into "
     "the code, so a new message means a new code. The phone number is baked in too. Print a code "
     "with a message you are happy to keep, or leave the message empty so the code just opens a "
     "blank chat with you.</p>"),
    ("Why does the code get bigger when I write a longer message?",
     "<p>Because the message is stored inside the code itself, not fetched from anywhere. More text "
     "means more modules &mdash; the little squares &mdash; which means the code has to be printed "
     "larger to stay scannable. The page tells you the module count and the minimum print size as you "
     "type. If the code is getting dense, shorten the message: the customer can always type the rest "
     "themselves.</p>"),
    ("What does the &ldquo;checked&rdquo; line under the code mean?",
     "<p>That the code you are looking at was decoded before the download was unlocked. The page "
     "renders the artwork, reads the pixels back the way a scanner would, and runs a decoder over "
     "them. Putting a logo in the middle of a QR code destroys some of it &mdash; that is fine, because "
     "QR codes carry error correction, but only up to a point. The percentage is how much of that "
     "error-correction budget is still unspent after the logo. We keep most of it in reserve, because "
     "a real scan adds blur, glare and angle that a clean render does not.</p>"),
    ("Can I use my own colours or my own logo?",
     "<p>Not on this page. The three palettes here are the ones that were checked by actually decoding "
     "them, and the mark in the middle is ours. Arbitrary colours are how branded QR codes stop "
     "scanning &mdash; a mid-tone on a mid-tone reads as neither dark nor light. Your own mark, in your "
     "own colours, checked the same way, is part of what we build.</p>"),
    ("Do I need WhatsApp Business for this?",
     "<p>Not for the link or the code &mdash; they work with any WhatsApp account. The away message in "
     "the second tab does need WhatsApp Business, which is free: it is under Settings, Business tools, "
     "Away message. The greeting message and quick replies live in the same place.</p>"),
    ("Is this an official WhatsApp tool?",
     "<p>No. WhatsApp is a Meta product and we are not affiliated with them. <code>wa.me</code> is "
     "WhatsApp's own public link format, documented by them, and this page just assembles one "
     "correctly &mdash; including getting the percent-encoding right for Arabic, which is where "
     "hand-made links usually break.</p>"),
]


def _country_opts():
    return "\n".join(
        '        <option value="%s" data-dial="%s" data-n="%d" data-eg="%s"%s>%s (+%s)</option>'
        % (iso, dial, n, eg, ' selected' if iso == "OM" else '', name, dial)
        for iso, name, dial, n, eg in COUNTRIES)


def _preset_chips():
    return "\n".join(
        '        <button type="button" data-msg="%s"%s>%s</button>'
        % (msg.replace('"', "&quot;"), ' lang="ar" dir="rtl"' if "&#1" in label else "", label)
        for label, msg in PRESETS)


def _palette_opts():
    sw = {"cream": ('<i style="inset:0;background:#F1EFE8"></i>'
                    '<i style="left:6px;top:6px;width:9px;height:9px;background:#BA7517"></i>'
                    '<i style="right:6px;bottom:6px;width:14px;height:9px;background:#0A3D30"></i>'),
          "dark": ('<i style="inset:0;background:#0A1A14"></i>'
                   '<i style="left:6px;top:6px;width:9px;height:9px;background:#E8C98F"></i>'
                   '<i style="right:6px;bottom:6px;width:14px;height:9px;background:#F1EFE8"></i>'),
          "mono": ('<i style="inset:0;background:#FFFFFF"></i>'
                   '<i style="left:6px;top:6px;width:9px;height:9px;background:#000"></i>'
                   '<i style="right:6px;bottom:6px;width:14px;height:9px;background:#000"></i>')}
    return "\n".join(
        """        <label data-pal="%s"%s>
          <input type="radio" name="pal" value="%s"%s>
          <span class="sw">%s</span>
          <span><b>%s</b><span>%s</span></span>
        </label>""" % (key, ' class="sel"' if key == "cream" else "", key,
                       ' checked' if key == "cream" else "", sw[key], name, what)
        for key, name, what, _inv in PALETTES)


def _sizes_rows():
    return "\n".join(
        """        <tr><td>%s</td><td>%s</td><td><span class="num">%s</span></td>
          <td><span class="num" data-dist="%s">&mdash;</span></td></tr>""" % (where, eg, dist, cm)
        for where, eg, dist, cm in DISTANCES)


def _faq_html():
    return "\n".join(
        """      <details%s>
        <summary>%s</summary>
        <div class="a">%s</div>
      </details>""" % (" open" if i == 0 else "", q, a) for i, (q, a) in enumerate(FAQ))


def _day_boxes():
    days = [("Sun", 0), ("Mon", 1), ("Tue", 2), ("Wed", 3), ("Thu", 4), ("Fri", 5), ("Sat", 6)]
    # Sunday to Thursday preselected: that is the Omani working week.
    return "\n".join(
        '          <label%s><input type="checkbox" data-day="%d"%s><span>%s</span></label>'
        % (' class="sel"' if i <= 4 else "", i, " checked" if i <= 4 else "", lbl)
        for lbl, i in days)


def body():
    return f"""<main id="main">

<section class="phero s-panel grain">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span>Free tool</p>
    <h1 class="h1">WhatsApp link and branded QR maker</h1>
    <p class="lede">Turn your number into a link that opens a chat with the first message already
      written &mdash; and into a QR code in your own colours that a phone can still read. Both are
      built here, in this browser, on your device. Nothing you type is sent anywhere, because there is
      nowhere for it to be sent.</p>
    <p class="toolbar" style="margin-top:26px">
      <span><b>Free</b></span>
      <span><b>No sign-up</b></span>
      <span><b>Nothing leaves your browser</b></span>
      <span><b>PNG and SVG</b></span>
    </p>
  </div>
</section>

<section class="s-cream grain" id="tool">
  <div class="wrap-n">
    <h2 class="vh">The tool</h2>

    <div class="tabs" role="tablist" aria-label="What to make">
      <button type="button" role="tab" id="tab-link" aria-controls="pane-link" aria-selected="true">Chat link &amp; QR</button>
      <button type="button" role="tab" id="tab-away" aria-controls="pane-away" aria-selected="false" tabindex="-1">Away message</button>
    </div>

    <!-- ============================================ tab 1: link and code -->
    <div class="pane" id="pane-link" role="tabpanel" aria-labelledby="tab-link">
    <div class="rig">
      <div>
        <fieldset class="fset">
          <legend>Your WhatsApp number</legend>
          <div class="flds">
            <div class="fld">
              <label for="cc">Country</label>
              <select id="cc">
{_country_opts()}
              </select>
            </div>
            <div class="fld">
              <label for="num">Number</label>
              <input id="num" type="tel" inputmode="tel" autocomplete="tel-national" placeholder="9924 5250">
              <p class="err" id="numErr"></p>
            </div>
          </div>
          <p class="hint">Type it however you like &mdash; <span class="num" dir="ltr">+968 9924 5250</span>,
            <span class="num" dir="ltr">00968 99245250</span> or just <span class="num" dir="ltr">99245250</span>.
            Paste a number with its country code and the country above follows it. WhatsApp wants digits
            with no plus and no spaces, and that is what goes into the link.</p>
        </fieldset>

        <fieldset class="fset">
          <legend>The first message</legend>
          <div class="flds">
            <div class="fld full">
              <label for="msg">What the customer's message should already say <span class="opt">(optional)</span></label>
              <textarea id="msg" rows="4" placeholder="Hello, I would like to place an order."></textarea>
              <p class="cnt" id="msgCnt"><b>0</b> characters</p>
            </div>
          </div>
          <div class="chips" id="chips">
{_preset_chips()}
          </div>
          <p class="hint">This is what <em>your customer</em> sends to <em>you</em>, already typed, so
            they only have to press send. Leave it empty for a plain chat. Arabic is fine &mdash; it is
            encoded properly here, which is where hand-written links usually break.</p>
        </fieldset>

        <fieldset class="fset">
          <legend>Code style</legend>
          <div class="pals" id="pals">
{_palette_opts()}
          </div>
        </fieldset>
      </div>

      <div class="out">
        <h3>Your link</h3>
        <p class="link empty" id="link">Enter a number to build your link.</p>
        <div class="acts">
          <button type="button" id="copyLink" disabled>Copy link</button>
          <a class="go" id="openLink" href="#" target="_blank" rel="noopener" hidden>Test it</a>
        </div>

        <div class="qrbox">
          <canvas id="qr" hidden width="300" height="300" aria-label="Your WhatsApp QR code"></canvas>
          <div class="qrph" id="qrPh">Your code appears here once there is a number to put in it.</div>
        </div>

        <div class="chk" id="chk" hidden>
          {LOCK_ICON}
          <p id="chkText"></p>
        </div>

        <div class="acts" style="margin-top:14px">
          <button type="button" id="dlPng" disabled>Download PNG</button>
          <button type="button" id="dlSvg" disabled>Download SVG</button>
        </div>
        <div class="flds" style="margin-top:12px">
          <div class="fld full">
            <label for="px">PNG size</label>
            <select id="px">
              <option value="1000">1000 px &mdash; screens and social</option>
              <option value="2000" selected>2000 px &mdash; flyers and stickers</option>
              <option value="4000">4000 px &mdash; posters and banners</option>
            </select>
          </div>
        </div>

        <div class="phone">
          <div class="bar">
            <span class="av"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2a10 10 0 0 0-8.7 14.9L2 22l5.3-1.4A10 10 0 1 0 12 2zm0 2a8 8 0 1 1-4.1 14.9l-.4-.2-3 .8.8-2.9-.2-.4A8 8 0 0 1 12 4z"/></svg></span>
            <span class="who">Your business<span id="waNum">&mdash;</span></span>
          </div>
          <div class="thread"><span class="bub" id="bub"><span class="tx" id="bubTx"></span><span class="t">now</span></span></div>
          <p class="cap">What your customer sees when they tap the link or scan the code. They press
            send; you get the message.</p>
        </div>
      </div>
    </div>
    </div>

    <!-- ============================================== tab 2: away message -->
    <div class="pane" id="pane-away" role="tabpanel" aria-labelledby="tab-away" hidden>
    <div class="rig">
      <div>
        <fieldset class="fset">
          <legend>Your business</legend>
          <div class="flds">
            <div class="fld">
              <label for="bizEn">Name in English</label>
              <input id="bizEn" type="text" placeholder="Al Noor Trading">
            </div>
            <div class="fld">
              <label for="bizAr">Name in Arabic <span class="opt">(optional)</span></label>
              <input id="bizAr" type="text" lang="ar" dir="rtl" placeholder="&#1575;&#1604;&#1606;&#1608;&#1585; &#1604;&#1604;&#1578;&#1580;&#1575;&#1585;&#1577;">
            </div>
          </div>
          <p class="hint">Leave the Arabic name empty and the Arabic message will use the English one
            &mdash; which is right if your name is a Latin brand.</p>
        </fieldset>

        <fieldset class="fset">
          <legend>When you are open</legend>
          <div class="days" id="days">
{_day_boxes()}
          </div>
          <div class="flds" style="margin-top:15px">
            <div class="fld">
              <label for="opens">Opens</label>
              <input id="opens" type="time" value="08:00">
            </div>
            <div class="fld">
              <label for="closes">Closes</label>
              <input id="closes" type="time" value="18:00">
            </div>
          </div>
          <p class="hint">Sunday to Thursday is filled in because that is the Omani working week.
            Change it to whatever yours actually is &mdash; a wrong away message is worse than none.</p>
        </fieldset>

        <fieldset class="fset">
          <legend>What to promise</legend>
          <div class="flds">
            <div class="fld">
              <label for="reply">You will reply</label>
              <select id="reply">
                <option value="hour">Within an hour of opening</option>
                <option value="day" selected>The same working day</option>
                <option value="next">On the next working day</option>
              </select>
            </div>
            <div class="fld">
              <label for="urgent">Urgent number <span class="opt">(optional)</span></label>
              <input id="urgent" type="tel" inputmode="tel" placeholder="+968 9924 5250">
            </div>
          </div>
          <p class="hint">Promise the one you will actually keep. An away message that says
            &ldquo;within an hour&rdquo; and takes two days costs you more than silence would.</p>
        </fieldset>
      </div>

      <div class="out">
        <h3>Paste these into WhatsApp Business</h3>
        <div class="away">
          <div class="msg">
            <div class="top"><b>English</b><button type="button" class="cp" data-copy="awayEn">Copy</button></div>
            <pre id="awayEn"></pre>
          </div>
          <div class="msg">
            <div class="top"><b>&#1575;&#1604;&#1593;&#1585;&#1576;&#1610;&#1577;</b><button type="button" class="cp" data-copy="awayAr">Copy</button></div>
            <pre id="awayAr" lang="ar" dir="rtl"></pre>
          </div>
          <div class="msg">
            <div class="top"><b>Both, one message</b><button type="button" class="cp" data-copy="awayBoth">Copy</button></div>
            <pre id="awayBoth"></pre>
          </div>
        </div>
        <p class="hint" style="margin-top:16px">In WhatsApp Business: <b>Settings &rarr; Business tools
          &rarr; Away message</b>. Turn it on, paste, and set the schedule to
          &ldquo;Outside of business hours&rdquo; so it only fires when you are actually shut.</p>
      </div>
    </div>
    </div>

    <div class="local">
      {LOCK_ICON}
      <p><b>Nothing you type here is sent anywhere.</b> Your number, your message and your opening
        hours are turned into a link, a code and some text by scripts running on your own device, and
        there is no server behind this tool to receive them. The page counts that a code was made, the
        way every page here counts a visit &mdash; it never sends what you put in it. Open the Network
        tab in your browser's developer tools and watch.</p>
    </div>

  </div>
</section>

<section class="s-panel grain">
  <div class="wrap-n">
    <p class="eyebrow"><span class="star">{STAR}</span>What to do with it</p>
    <h2 class="h2">Three places this earns its keep</h2>
    <ol class="steps">
      <li><span class="n">01</span><span><b>The link goes where people already look</b>
        <span>Your Instagram bio, your Google Business Profile, the signature on your quotes, the
          footer of your invoices. Anywhere a customer might be holding a phone and thinking about
          buying. The message being pre-written is the whole trick: it removes the sentence they would
          otherwise have to compose, and that sentence is where most enquiries die.</span></span></li>
      <li><span class="n">02</span><span><b>The code goes on the things you print</b>
        <span>The counter, the shop window, the van, the delivery note, the product itself. Pick a
          palette, download the PNG for anything digital and the SVG for anything a printer is going to
          handle &mdash; SVG has no resolution to run out of, so it stays sharp at any size.</span></span></li>
      <li><span class="n">03</span><span><b>The away message answers when you cannot</b>
        <span>A message that arrives at 9pm on a Thursday and gets nothing back until Sunday is a
          customer deciding you are not interested. Two lines saying when you open and when you will
          reply keeps them. In both languages, because your customers are not all reading the
          same one.</span></span></li>
    </ol>
  </div>
</section>

<section class="s-cream grain" id="print">
  <div class="wrap-n">
    <p class="eyebrow"><span class="star">{STAR}</span>Before you print it</p>
    <h2 class="h2">How big the code has to be</h2>
    <p class="lede">A QR code that is too small does not scan, and you find out after the flyers are
      printed. Two rules of thumb, and the tool applies both to the code you have actually made.</p>
    <p style="color:var(--muted);line-height:1.7;max-width:74ch">The first: <b>a code should be about a
      tenth as wide as the distance it is read from.</b> The second: <b>a printed module &mdash; one of
      the little squares &mdash; should not fall below about half a millimetre</b> on ordinary printing.
      Take whichever is larger. The last column updates as you build your code, because the answer
      depends on how much you put in it.</p>
    <div class="tw">
      <table class="sizes">
        <thead><tr><th>Where it goes</th><th>For example</th><th>Read from</th><th>Print it at least</th></tr></thead>
        <tbody>
{_sizes_rows()}
        </tbody>
      </table>
    </div>
    <p style="margin-top:18px;color:var(--muted);font-size:.93rem;line-height:1.65">Add the quiet
      margin &mdash; the empty border around the code &mdash; to those numbers, or rather, do not remove
      it: it is already in every file this page gives you, and a designer cropping it off is the single
      most common way a working code stops working.</p>
  </div>
</section>

<section class="s-dark grain">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span>Why it looks like that</p>
    <h2 class="h2">A brand asset, not a barcode &mdash; and still readable</h2>
    <div class="why">
      <div>
        <h3>The mark is sized by measurement, not taste</h3>
        <p>Putting a logo in the middle of a QR code destroys part of it. That is survivable, because
          QR codes carry error correction, but only up to a point &mdash; and past that point the code
          looks perfect and does not scan.</p>
        <p>So the plate is not a fixed size. The page grows it, renders the artwork, reads the pixels
          back the way a scanner would and decodes them, then keeps the largest mark that still leaves
          most of the error-correction budget unspent. That reserve is what a real scan spends on blur,
          glare and angle.</p>
      </div>
      <div>
        <h3>The corners round, the eyes do not</h3>
        <p>The modules are rounded because it softens the field without losing any dark area. The three
          big squares in the corners are left alone on purpose.</p>
        <p>A scanner finds a code by hunting a 1:1:3:1:1 run of dark and light across those corners.
          Rounding them skews that ratio on every scan line that does not cross dead centre. Tested,
          and even a slight radius stopped the code decoding &mdash; so the brand lives in the colour of
          the eyes, not their shape.</p>
      </div>
      <div>
        <h3>Gold, but only where gold still reads as dark</h3>
        <p>A scanner does not see colour. It turns the picture into black and white on a threshold, so
          every coloured part has to land on the correct side of that threshold.</p>
        <p>Our gold is dark enough to pass for a dark module on cream. On the dark palette it is not,
          which is why that one uses a pale gold instead. A mid-tone on a mid-tone reads as neither, and
          that is how most &ldquo;branded&rdquo; QR codes quietly stop working.</p>
      </div>
      <div>
        <h3>Inverted codes are a real risk, so we say so</h3>
        <p>The <b>Cream on ink</b> palette is an inverted code: light modules on a dark ground. Modern
          phone cameras generally read them. Plenty of ordinary barcode apps cannot &mdash; we tested it
          against OpenCV, which many of them are built on, and it failed on every inverted code while
          reading the same code perfectly the moment the image was flipped.</p>
        <p>So it is offered, because a dark flyer wants a dark code, and it is labelled. If the public
          is going to scan it, use <b>Ink on cream</b>.</p>
      </div>
    </div>
  </div>
</section>

<section class="s-cream grain">
  <div class="wrap-n">
    <div class="asterism"><span>{STAR}</span></div>
    <p class="eyebrow"><span class="star">{STAR}</span>One thing this will never do</p>
    <h2 class="h2">There is no short link, and there never will be</h2>
    <p style="color:var(--muted);line-height:1.75;max-width:74ch">Most QR generators hand you a code
      that points at <em>their</em> domain, which then redirects to yours. It is a good business for
      them: they see every scan, and they can charge you later for a code you have already printed on
      two thousand flyers.</p>
    <p style="color:var(--muted);line-height:1.75;max-width:74ch">It is a bad deal for you and a worse
      one for us. For you, because your code now depends on somebody else's company still existing and
      still being free. For us, because a redirect service on this domain would be found and used for
      phishing within weeks, and the blocklisting that followed would take our search results and our
      email with it.</p>
    <p style="color:var(--muted);line-height:1.75;max-width:74ch">So the code contains your link.
      Not ours. Nothing of ours sits between your customer and your chat, this page could vanish
      tomorrow, and every code it ever made would carry on working.</p>
  </div>
</section>

<section class="s-cream grain" id="faq" style="padding-top:0">
  <div class="wrap-n">
    <p class="eyebrow"><span class="star">{STAR}</span>Questions</p>
    <h2 class="h2">The ones worth answering</h2>
    <div class="faq">
{_faq_html()}
    </div>
  </div>
</section>

<section class="s-panel grain pad-s">
  <div class="wrap-n">
    <p class="eyebrow"><span class="star">{STAR}</span>Where this came from</p>
    <h2 class="h2">This is one button of the thing I actually build</h2>
    <p style="color:var(--muted);line-height:1.75;max-width:74ch">A link that opens a chat with the
      message already written is a small piece of a larger idea: that the distance between someone
      being interested and someone being in touch with you should be as close to nothing as it can be.
      The Smart Website is that idea applied to the whole path &mdash; the pages, the enquiry, the
      follow-up, and the part where the message gets answered rather than just received.</p>
    <p style="color:var(--muted);line-height:1.75;max-width:74ch">This page is free and stays free.
      It is also a fair sample: it was built the way the paid work is built, and it is doing the same
      job &mdash; getting the customer to the message.</p>
    <div class="btn-row" style="margin-top:24px">
      <a class="btn btn-teal" href="/en/services/#price">What I build, and what it costs</a>
      <a class="btn btn-ghost" href="/en/tools/">The other free tools</a>
    </div>
  </div>
</section>

</main>
"""


JS = qr_js.CODEC_JS + qr_js.ART_JS + """
/* ======================================================================== */
/*  The page. Everything below runs on the visitor's device and sends
    nothing - see the note at the top of tools/v4/page_tool_whatsapp.py.    */
/* ======================================================================== */
(function(){
  "use strict";
  var $ = function(id){ return document.getElementById(id); };
  var LOGO = "__LOGO_PATH__";

  /* ------------------------------------------------------------- tabs --- */
  var TABS = [["tab-link","pane-link"],["tab-away","pane-away"]];
  function showTab(i){
    TABS.forEach(function(t, j){
      var b = $(t[0]), p = $(t[1]);
      b.setAttribute("aria-selected", i === j ? "true" : "false");
      b.tabIndex = i === j ? 0 : -1;
      p.hidden = i !== j;
    });
  }
  TABS.forEach(function(t, i){
    $(t[0]).addEventListener("click", function(){ showTab(i); });
    $(t[0]).addEventListener("keydown", function(e){
      if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
      e.preventDefault();
      var n = (i + (e.key === "ArrowRight" ? 1 : TABS.length - 1)) % TABS.length;
      showTab(n); $(TABS[n][0]).focus();
    });
  });

  /* ------------------------------------------------------ the encoding ---
     The same rule as wa() in tools/v4/ar/ar_common.py: encode everything,
     leave nothing safe. encodeURIComponent alone leaves !'()* raw, so those
     are finished off by hand - which makes this byte-for-byte what Python's
     quote(text, safe="") produces, and keeps a slash in the message from
     ending it early on some WhatsApp clients. */
  function enc(s){
    return encodeURIComponent(s).replace(/[!'()*]/g, function(c){
      return "%" + c.charCodeAt(0).toString(16).toUpperCase();
    });
  }

  /* ------------------------------------------------- the phone number --- */
  var cc = $("cc"), num = $("num"), numErr = $("numErr");
  function dial(){ return cc.options[cc.selectedIndex].getAttribute("data-dial"); }
  function natLen(){ return parseInt(cc.options[cc.selectedIndex].getAttribute("data-n"), 10); }
  function digitsOf(s){ return (s || "").replace(/[^0-9]/g, ""); }

  /* Longest dial code first, so +971 is not read as +97. */
  var DIALS = [];
  for (var i = 0; i < cc.options.length; i++)
    DIALS.push([cc.options[i].getAttribute("data-dial"), cc.options[i].value]);
  DIALS.sort(function(a, b){ return b[0].length - a[0].length; });

  function normalise(){
    var raw = num.value.trim(), d = digitsOf(raw);
    if (!d) return "";
    /* An explicit + or 00 means the country code is already in there. */
    var intl = raw.charAt(0) === "+" || raw.slice(0, 2) === "00";
    if (intl){
      if (raw.slice(0, 2) === "00") d = d.replace(/^00/, "");
      for (var k = 0; k < DIALS.length; k++)
        if (d.indexOf(DIALS[k][0]) === 0 && cc.value !== DIALS[k][1]){ cc.value = DIALS[k][1]; break; }
      return d;
    }
    /* No plus. Digits that both START with the dial code and are longer than a
       local number are an international number typed without one - 96899245250.
       A bare 8-digit Omani number that happens to begin 968 is not. */
    var dl = dial();
    if (d.indexOf(dl) === 0 && d.length > natLen()) return d;
    return dl + d;
  }

  function numberProblem(full){
    if (!full) return "";
    var dl = dial(), nat = full.slice(dl.length), want = natLen();
    if (nat.length < want)
      return "That is " + nat.length + " digit" + (nat.length === 1 ? "" : "s") + " after +" + dl +
             ". " + cc.options[cc.selectedIndex].text.split(" (")[0] + " numbers normally have " +
             want + ".";
    if (nat.length > want + 1) return "That is more digits than a normal number for this country.";
    if (dl === "968" && nat.charAt(0) === "2")
      return "Omani numbers starting 2 are landlines, which usually have no WhatsApp account.";
    return "";
  }

  function pretty(full){
    if (!full) return "\\u2014";
    var dl = dial(), nat = full.slice(dl.length);
    return "+" + dl + " " + (nat.length > 4 ? nat.slice(0, nat.length - 4) + " " + nat.slice(-4) : nat);
  }

  /* --------------------------------------------------------- the link --- */
  var msg = $("msg");
  function chatLink(){
    var full = normalise();
    if (!full || full.length < 8) return "";
    var t = msg.value.trim();
    /* wa.me, not api.whatsapp.com: same destination, 25 fewer bytes in the
       code, which is one version smaller on a long Arabic message. */
    return "https://wa.me/" + full + (t ? "?text=" + enc(t) : "");
  }

  /* --------------------------------------------------------- the code --- */
  var work = document.createElement("canvas");   /* offscreen, for fitting */
  var dlcv = document.createElement("canvas");   /* offscreen, for saving  */
  var view = $("qr"), ph = $("qrPh"), chk = $("chk"), chkText = $("chkText");
  var dlPng = $("dlPng"), dlSvg = $("dlSvg"), copyLink = $("copyLink"), openLink = $("openLink");
  var cur = null, counted = false;

  function palette(){
    var r = document.querySelector('input[name=pal]:checked');
    return r ? r.value : "cream";
  }

  function clearCode(msgText){
    cur = null;
    view.hidden = true; ph.hidden = false; chk.hidden = true;
    ph.textContent = msgText || "Your code appears here once there is a number to put in it.";
    dlPng.disabled = dlSvg.disabled = true;
  }

  function build(){
    var url = chatLink();
    var full = normalise();

    /* the link box, the copy button and the preview all follow the link */
    var box = $("link");
    if (url){
      box.textContent = url; box.classList.remove("empty");
      copyLink.disabled = false;
      openLink.hidden = false; openLink.href = url;
    } else {
      box.textContent = "Enter a number to build your link."; box.classList.add("empty");
      copyLink.disabled = true; openLink.hidden = true;
    }
    $("waNum").textContent = pretty(full);
    var t = msg.value.trim();
    /* into the message span, never into the bubble: setting textContent on
       the bubble would delete the timestamp span with it. */
    $("bubTx").textContent = t;
    $("bub").setAttribute("dir", /[\\u0600-\\u06FF]/.test(t) ? "rtl" : "ltr");
    var c = $("msgCnt");
    c.innerHTML = "<b>" + msg.value.length + "</b> character" + (msg.value.length === 1 ? "" : "s");

    var problem = numberProblem(full);
    numErr.textContent = problem;
    num.setAttribute("aria-invalid", problem ? "true" : "false");

    if (!url){ clearCode(); sizes(0); return; }

    var sym = ART.symbolFor(url);
    if (!sym){
      clearCode("That message is too long to fit in a QR code at all. Shorten it - your customer can "
                + "always type the rest.");
      sizes(0);
      return;
    }

    var pal = palette();
    var fit = ART.fit(work, sym, pal, LOGO);
    if (!fit.check.ok){
      /* Should not happen - fit falls back to no mark at all - but if it ever
         does, say so and keep the download locked rather than hand over a
         code that does not read. */
      clearCode("This code did not pass its own decode check, so it is not being offered. Try a "
                + "shorter message.");
      sizes(0);
      return;
    }

    /* Draw it big enough that the on-screen code is crisp on a retina screen,
       then let CSS size it down. */
    var S = Math.max(4, Math.round(760 / (sym.size + 2 * ART.QUIET)));
    ART.canvas(view, sym, pal, fit.plate, LOGO, S);
    view.hidden = false; ph.hidden = true;

    cur = { sym: sym, plate: fit.plate, pal: pal, check: fit.check, url: url };
    paintCheck();
    sizes(sym.size);
    dlPng.disabled = dlSvg.disabled = false;

    if (!counted && typeof gtag === "function"){
      counted = true;
      gtag("event", "tool_used", {tool_name:"whatsapp-link-generator", tool_step:"first_code"});
    }
  }

  /* The verification line. A percentage nobody can check is worth less than a
     number they can - so it says how much of the error-correction budget the
     mark spent, not just that it passed. */
  function paintCheck(){
    var v = cur.check, inv = !!ART.SCHEMES[cur.pal].inverted;
    var pct = Math.round(v.headroom * 100);
    var html = "<b>Checked.</b> This exact image was decoded after it was drawn" +
               (cur.plate ? ", with the mark in place" : "") + " &mdash; <span class=\\"num\\">" + pct +
               "%</span> of its error-correction budget is still unspent, so it has room for a " +
               "real-world scan.";
    if (inv)
      html += " <b>But this is an inverted code</b> (light on dark): modern phone cameras read these, " +
              "plenty of ordinary barcode apps do not. For anything the public will scan, use Ink on cream.";
    chk.className = "chk" + (inv ? " warn" : "");
    chkText.innerHTML = html;
    chk.hidden = false;
  }

  /* Print sizing: the larger of "a tenth of the reading distance" and "half a
     millimetre per module". Both include the quiet margin, because that is
     what the downloaded file contains. */
  function minCm(N, distCm){
    if (!N) return 0;
    var byDistance = distCm / 10;
    var byModule = (N + 2 * ART.QUIET) * 0.05;
    return Math.ceil(Math.max(byDistance, byModule) * 2) / 2;
  }
  function sizes(N){
    var cells = document.querySelectorAll("[data-dist]");
    for (var i = 0; i < cells.length; i++){
      var d = parseFloat(cells[i].getAttribute("data-dist"));
      cells[i].textContent = N ? minCm(N, d).toFixed(1) + " cm" : "\\u2014";
    }
  }

  /* ------------------------------------------------------- the saving --- */
  function fileStem(){
    return "whatsapp-qr-" + (normalise() || "code") + "-" + cur.pal;
  }
  function save(blob, name){
    var u = URL.createObjectURL(blob), a = document.createElement("a");
    a.href = u; a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function(){ URL.revokeObjectURL(u); }, 4000);
    if (typeof gtag === "function")
      gtag("event", "tool_output_saved",
           {tool_name:"whatsapp-link-generator", output_format:name.split(".").pop(), palette:cur.pal});
  }

  dlPng.addEventListener("click", function(){
    if (!cur) return;
    var px = parseInt($("px").value, 10);
    var S = Math.max(2, Math.round(px / (cur.sym.size + 2 * ART.QUIET)));
    ART.canvas(dlcv, cur.sym, cur.pal, cur.plate, LOGO, S);
    /* Decode the file we are about to hand over, not a proxy for it. */
    var v = ART.verify(dlcv, cur.sym, !!ART.SCHEMES[cur.pal].inverted);
    if (!v.ok){
      chk.className = "chk warn";
      chkText.innerHTML = "<b>Not offered.</b> That size did not decode when it was checked. Pick a " +
                          "different size or a shorter message.";
      return;
    }
    dlcv.toBlob(function(b){ save(b, fileStem() + "-" + dlcv.width + "px.png"); }, "image/png");
  });

  dlSvg.addEventListener("click", function(){
    if (!cur) return;
    /* The SVG is drawn from the same path data the canvas was painted from,
       so the decode check above covers this file too. */
    var s = ART.svg(cur.sym, cur.pal, cur.plate, LOGO);
    save(new Blob([s], {type:"image/svg+xml;charset=utf-8"}), fileStem() + ".svg");
  });

  function flash(btn, word){
    var was = btn.textContent;
    btn.textContent = word;
    setTimeout(function(){ btn.textContent = was; }, 1600);
  }
  function copy(text, btn){
    if (navigator.clipboard && navigator.clipboard.writeText){
      navigator.clipboard.writeText(text).then(function(){ flash(btn, "Copied"); },
                                               function(){ flash(btn, "Press Ctrl+C"); });
      return;
    }
    var ta = document.createElement("textarea");
    ta.value = text; ta.setAttribute("readonly", "");
    ta.style.position = "fixed"; ta.style.top = "-1000px";
    document.body.appendChild(ta); ta.select();
    try { document.execCommand("copy"); flash(btn, "Copied"); }
    catch (e) { flash(btn, "Press Ctrl+C"); }
    ta.remove();
  }
  copyLink.addEventListener("click", function(){ if (cur) copy(cur.url, copyLink); });

  /* ------------------------------------------------------------ wiring --- */
  var timer = null;
  function later(){ clearTimeout(timer); timer = setTimeout(build, 220); }
  num.addEventListener("input", later);
  msg.addEventListener("input", later);
  cc.addEventListener("change", function(){
    num.placeholder = cc.options[cc.selectedIndex].getAttribute("data-eg");
    build();
  });
  $("chips").addEventListener("click", function(e){
    var b = e.target.closest("button[data-msg]");
    if (!b) return;
    msg.value = b.getAttribute("data-msg");
    msg.focus();
    build();
  });
  $("pals").addEventListener("change", function(){
    var labels = $("pals").querySelectorAll("label");
    for (var i = 0; i < labels.length; i++)
      labels[i].classList.toggle("sel", labels[i].querySelector("input").checked);
    build();
  });

  /* ================================================== the away message === */
  var DAY_EN = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"];
  /* Arabic day names and the four sentences below are the one part of this
     page written in Arabic. They want a native pass before they are called
     finished - the same debt the /pay-ar/ strings carry. */
  var DAY_AR = ["الأحد","الاثنين","الثلاثاء","الأربعاء","الخميس","الجمعة","السبت"];
  var REPLY_EN = {hour:"within an hour of opening", day:"on the same working day",
                  next:"on the next working day"};
  var REPLY_AR = {hour:"خلال ساعة من بداية الدوام", day:"خلال يوم العمل نفسه",
                  next:"في أول يوم عمل قادم"};

  /* A Latin run inside Arabic text gets reordered by the bidi algorithm: a
     phone number typed +968 9924 5250 comes out of WhatsApp reading
     5250 9924 968+, which is worse than useless on an away message. U+200E
     (LEFT-TO-RIGHT MARK) on both sides pins it. LRM rather than the U+2066
     isolate pair on purpose - it is invisible in every client old enough to
     matter, where an unsupported isolate can show up as a box. This is the
     plain-text cousin of num() in tools/v4/ar/ar_common.py. */
  var LRM = "\u200E";
  function ltr(s){ return /[A-Za-z0-9+]/.test(s) ? LRM + s + LRM : s; }

  function chosenDays(){
    var out = [], b = document.querySelectorAll("#days input");
    for (var i = 0; i < b.length; i++) if (b[i].checked) out.push(parseInt(b[i].getAttribute("data-day"), 10));
    return out;
  }
  /* "Sunday to Thursday" when the days run without a gap, otherwise the list.
     Wrapping is handled too, so Saturday-to-Wednesday reads as a range. */
  function dayPhrase(days, names, to, sep){
    if (!days.length) return "";
    if (days.length === 7) return names[0] + " " + to + " " + names[6];
    var sorted = days.slice().sort(function(a, b){ return a - b; });
    for (var start = 0; start < sorted.length; start++){
      var ok = true;
      for (var k = 1; k < sorted.length; k++)
        if (sorted[(start + k) % sorted.length] !== (sorted[(start + k - 1) % sorted.length] + 1) % 7){ ok = false; break; }
      if (ok && sorted.length > 2)
        return names[sorted[start]] + " " + to + " " + names[sorted[(start + sorted.length - 1) % sorted.length]];
    }
    return sorted.map(function(d){ return names[d]; }).join(sep);
  }
  function clock(v, ar){
    var p = (v || "").split(":");
    if (p.length !== 2) return "";
    var h = parseInt(p[0], 10), m = p[1];
    var pm = h >= 12, h12 = h % 12 === 0 ? 12 : h % 12;
    return h12 + ":" + m + " " + (ar ? (pm ? "م" : "ص") : (pm ? "PM" : "AM"));
  }

  function away(){
    var days = chosenDays();
    var en = $("bizEn").value.trim(), ar = $("bizAr").value.trim() || en;
    var o = clock($("opens").value, false), c = clock($("closes").value, false);
    var oa = clock($("opens").value, true), ca = clock($("closes").value, true);
    var r = $("reply").value, u = $("urgent").value.trim();

    var L = [];
    L.push("Thanks for your message" + (en ? " to " + en : "") + ". We are closed right now.");
    if (days.length && o && c)
      L.push("We are open " + dayPhrase(days, DAY_EN, "to", ", ") + ", " + o + " to " + c + ".");
    L.push("We will reply " + REPLY_EN[r] + ".");
    if (u) L.push("If it is urgent, call " + u + ".");
    var textEn = L.join("\\n");

    var A = [];
    A.push("شكراً لتواصلك" + (ar ? " مع " + ltr(ar) : "") + ". نحن خارج أوقات العمل حالياً.");
    if (days.length && oa && ca)
      A.push("أوقات العمل: من " + dayPhrase(days, DAY_AR, "إلى", "، ") + "، من " + oa + " إلى " + ca + ".");
    A.push("سنرد عليك " + REPLY_AR[r] + ".");
    if (u) A.push("للحالات العاجلة، اتصل على " + ltr(u) + ".");
    var textAr = A.join("\\n");

    $("awayEn").textContent = textEn;
    $("awayAr").textContent = textAr;
    $("awayBoth").textContent = textEn + "\\n\\n" + textAr;
  }

  $("days").addEventListener("change", function(e){
    var l = e.target.closest("label");
    if (l) l.classList.toggle("sel", e.target.checked);
    away();
  });
  ["bizEn","bizAr","opens","closes","reply","urgent"].forEach(function(id){
    $(id).addEventListener("input", away);
    $(id).addEventListener("change", away);
  });
  document.querySelectorAll(".cp").forEach(function(b){
    b.addEventListener("click", function(){ copy($(b.getAttribute("data-copy")).textContent, b); });
  });

  /* ------------------------------------------------------------- start --- */
  build();
  away();
})();
""".replace("__LOGO_PATH__", qr_js.LOGO_PATH)


def _strip(html):
    """FAQ answers are markup on the page and plain text in the structured
    data - Google wants the answer, not the tags."""
    import re
    t = re.sub(r"<[^>]+>", "", html)
    return re.sub(r"\s+", " ", t).strip()


def _faq_schema():
    items = ",".join(
        '{"@type":"Question","name":%s,"acceptedAnswer":{"@type":"Answer","text":%s}}'
        % (json.dumps(_strip(q)), json.dumps(_strip(a))) for q, a in FAQ)
    return ('{"@type":"FAQPage",'
            '"@id":"https://aiprofitlab.io/en/tools/whatsapp-link-generator/#faq",'
            '"inLanguage":"en","mainEntity":[%s]}' % items)


META = dict(
    slug="waqr",
    title="WhatsApp link and branded QR code maker | AI Profit Lab",
    desc=("Free tool: turn an Oman phone number into a wa.me chat link with the first message already "
          "written, and into a branded QR code that is decoded before you download it. PNG and SVG, "
          "Arabic and English, no sign-up. Runs entirely in your browser."),
    nav="/en/tools/whatsapp-link-generator/",
    # Same reason as the other two tools: this page says nothing you type is
    # sent anywhere, and a session recorder rebuilds the DOM - which here
    # means the visitor's phone number and their customers' message. One
    # sentence cannot be true on one tool and false on the next.
    clarity=False,
    next=("Next", "The other free tools", "/en/tools/"),
    schema=_faq_schema() + "$$SPLIT$$" + """{
  "@type":"WebApplication",
  "@id":"https://aiprofitlab.io/en/tools/whatsapp-link-generator/#tool",
  "name":"WhatsApp link and branded QR code maker",
  "description":"Builds a wa.me chat link with a prefilled message in Arabic or English, and renders it as a brand-coloured QR code that is decoded from its own pixels before download. PNG and SVG. Runs entirely in the browser with no account and no data submission.",
  "applicationCategory":"BusinessApplication",
  "applicationSubCategory":"QR code generator",
  "operatingSystem":"Any",
  "browserRequirements":"Runs entirely in the browser. No account and no data submission.",
  "url":"https://aiprofitlab.io/en/tools/whatsapp-link-generator/",
  "inLanguage":"en",
  "isAccessibleForFree":true,
  "offers":{"@type":"Offer","price":"0","priceCurrency":"OMR"},
  "featureList":[
    "wa.me chat link with a prefilled first message",
    "Correct percent-encoding for Arabic message text",
    "Oman number normalisation from +968, 968, 00968 or a local 8-digit number",
    "Brand-coloured QR code with rounded modules and a centre mark",
    "Every code decoded from its rendered pixels before the download unlocks",
    "PNG at print resolution and resolution-independent SVG",
    "Bilingual English and Arabic business-hours away message"
  ],
  "publisher":{"@id":"https://aiprofitlab.io/#organization"}
}""",
)
