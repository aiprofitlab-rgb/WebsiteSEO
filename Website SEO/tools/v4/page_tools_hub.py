#!/usr/bin/env python3
"""The free tools hub - /en/tools/.

The index for a small set of browser tools given away to a specific audience:
VAT-registered Omani businesses with a real deadline. The hub exists so the
tools cluster under one path for search and for analytics, and so a visitor
who lands on one finds the others.

Two rules this page states out loud, because they are the differentiator and
not decoration:

  * every tool runs entirely in the visitor's browser and sends nothing;
  * no tool asks for an email before it works.

LIVE and NEXT below are the only things that change as tools ship. Moving a
tool from NEXT to LIVE is a two-line edit plus its own page module - there is
no second list of tools anywhere else.

Nothing in NEXT carries a date. They are ordered intentions, and a hub full of
dated promises that slip is worse than no hub. See the free-tools plan's kill
rule: a tool that produces nothing in 90 days is removed, not "improved".
"""
import json

from kit import STAR

# (title, one-line what it does, url, the eyebrow tag, who it is for)
LIVE = [
    ("Oman e-invoicing 2027: which date is yours",
     "A live countdown to the Fawtara deadline, two questions that tell you which of the two "
     "mandatory phases applies to your business, and a 12-point readiness checklist you can tick "
     "and print.",
     "/en/tools/oman-e-invoicing-2027/",
     "Tax deadline",
     "Any VAT-registered business in Oman"),

    ("Oman VAT tax invoice &amp; quote maker",
     "Fill your business in once, add your lines, and print a document carrying every field an "
     "Omani tax invoice has to carry &mdash; VAT worked out in whole baisa, the OMR 500 simplified "
     "threshold enforced, and quotations that convert into invoices without retyping.",
     "/en/tools/oman-vat-invoice-generator/",
     "Invoicing",
     "Anyone in Oman who issues invoices or quotes"),

    ("WhatsApp link &amp; branded QR maker",
     "A wa.me link that opens a chat with the first message already written, and a QR code in the "
     "brand palette that is decoded from its own pixels before you are allowed to download it &mdash; "
     "PNG and SVG. Plus a bilingual away message for the hours you are shut.",
     "/en/tools/whatsapp-link-generator/",
     "Getting enquiries",
     "Any business that takes orders on WhatsApp"),
]

# Ordered, undated. The order is the free-tools plan's order: lead intent
# first, build cost second.
NEXT = [
    ("Price list &amp; catalogue builder",
     "Rows, logo, optional product photos, Arabic and English columns, VAT in or out, one A4 PDF to "
     "send on WhatsApp."),
]


CSS = """
/* ------------------------------------------------------------ tool cards */
.tools{display:grid;gap:clamp(18px,2.4vw,26px);margin:clamp(28px,4vw,44px) 0 0}
.tool{
  display:block;text-decoration:none;color:inherit;position:relative;
  border:1px solid var(--line);border-radius:20px;background:var(--white);
  padding:clamp(24px,3vw,36px);
  transition:transform .25s var(--ease),box-shadow .25s var(--ease),border-color .2s;
}
.tool:hover{transform:translateY(-3px);border-color:var(--amber);box-shadow:0 18px 40px -28px rgba(7,43,34,.55)}
.tool .tag{
  display:inline-flex;align-items:center;gap:8px;font-family:var(--mono);font-size:.72rem;
  letter-spacing:.14em;text-transform:uppercase;color:var(--amber-text);margin:0 0 14px;
}
.tool h3{font-size:clamp(1.35rem,2.6vw,1.9rem);line-height:1.16;color:var(--teal-950);margin:0 0 12px}
.tool p{margin:0;color:var(--muted);font-size:1.01rem;line-height:1.62;max-width:62ch}
.tool .who{
  display:block;margin-top:16px;font-family:var(--mono);font-size:.76rem;letter-spacing:.07em;
  color:var(--muted);
}
.tool .who b{color:var(--teal-950);font-weight:500}
.tool .go{
  display:inline-flex;align-items:center;gap:9px;margin-top:18px;
  font-family:var(--mono);font-size:.78rem;letter-spacing:.1em;text-transform:uppercase;color:var(--teal);
}
.tool .go .arw{transition:transform .25s var(--ease)}
.tool:hover .go .arw{transform:translateX(5px)}

/* ------------------------------------------------------------- the rules */
.rules{display:grid;grid-template-columns:repeat(3,1fr);gap:clamp(16px,2vw,24px);margin:clamp(26px,3.6vw,40px) 0 0}
.rules div{border:1px solid var(--line-dark);border-radius:16px;padding:22px 24px}
.rules h3{font-size:1.18rem;color:var(--cream);margin:0 0 9px}
.rules p{margin:0;font-size:.95rem;line-height:1.6;color:rgba(241,239,232,.7)}

/* ----------------------------------------------------------------- next */
.bench{list-style:none;margin:clamp(22px,3vw,32px) 0 0;padding:0;counter-reset:b}
.bench li{border-top:1px solid var(--line);padding:20px 0;display:grid;grid-template-columns:auto 1fr;gap:18px}
.bench li:last-child{border-bottom:1px solid var(--line)}
.bench .n{
  font-family:var(--mono);font-size:.8rem;letter-spacing:.1em;color:var(--amber-text);padding-top:.32em;
}
.bench b{display:block;font-family:var(--display);font-weight:400;font-size:1.2rem;color:var(--teal-950);margin-bottom:6px}
.bench span{display:block;font-size:.96rem;line-height:1.6;color:var(--muted)}

@media (max-width:900px){ .rules{grid-template-columns:1fr} }
@media (max-width:560px){ .bench li{grid-template-columns:1fr;gap:6px} }
"""


def _live_html():
    out = []
    for title, what, href, tag, who in LIVE:
        out.append(f"""      <a class="tool" href="{href}">
        <p class="tag"><span class="star">{STAR}</span>{tag}</p>
        <h3>{title}</h3>
        <p>{what}</p>
        <span class="who">For: <b>{who}</b></span>
        <span class="go">Open the tool <span class="arw" aria-hidden="true">&rarr;</span></span>
      </a>""")
    return "\n".join(out)


def _next_html():
    return "\n".join(
        f"""      <li>
        <span class="n">{i + 1:02d}</span>
        <span><b>{title}</b><span>{what}</span></span>
      </li>"""
        for i, (title, what) in enumerate(NEXT))


def body():
    return f"""<main id="main">

<section class="phero s-panel grain">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span>Free tools</p>
    <h1 class="h1">Tools I built because I needed them</h1>
    <p class="lede">Small, specific tools for running a business in Oman. Free, no sign-up, no email
      before they work &mdash; and every one of them runs entirely inside your own browser. They are
      here because a working tool is a better argument than a page of claims.</p>
  </div>
</section>

<section class="s-cream grain" id="live">
  <div class="wrap-n">
    <p class="eyebrow"><span class="star">{STAR}</span>Open now</p>
    <h2 class="h2">Available today</h2>
    <div class="tools">
{_live_html()}
    </div>
  </div>
</section>

<section class="s-dark grain">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span>The rules these follow</p>
    <h2 class="h2">Three promises, and why they are keepable</h2>
    <div class="rules">
      <div>
        <h3>Nothing leaves your browser</h3>
        <p>There is no server behind any of these. What you type is worked out on your own device and
          never sent anywhere &mdash; which is not a policy we are asking you to trust, but an
          architecture you can check in DevTools. The pages count that a tool was used, the way every
          page here is counted. They never send what you typed into it.</p>
      </div>
      <div>
        <h3>No email to get in</h3>
        <p>The tool works before you have told me anything. If it turns out to be useful you know
          where to find me, and if it does not, you owe me nothing for finding out.</p>
      </div>
      <div>
        <h3>Dated facts, reviewed</h3>
        <p>Where a tool depends on a rate, a threshold or a deadline, that figure sits in one place on
          the page with the date it was last verified &mdash; so you can see how fresh it is instead of
          guessing.</p>
      </div>
    </div>
  </div>
</section>

<section class="s-cream grain">
  <div class="wrap-n">
    <div class="asterism"><span>{STAR}</span></div>
    <p class="eyebrow"><span class="star">{STAR}</span>On the bench</p>
    <h2 class="h2">Being built next</h2>
    <p class="lede">In this order, and without dates &mdash; a list of promised dates that slip is worse
      than no list. Each one ships when it is good enough to be a fair sample of the work.</p>
    <ul class="bench">
{_next_html()}
    </ul>
    <p style="margin-top:26px;color:var(--muted);font-size:.97rem">Want one of them sooner, or want
      something else entirely? <a href="/en/contact/">Tell me which</a> &mdash; the order is not
      fixed.</p>
  </div>
</section>

<section class="s-panel grain pad-s">
  <div class="wrap-n">
    <p class="eyebrow"><span class="star">{STAR}</span>Why these are free</p>
    <h2 class="h2">Because I sell the thing they are made of</h2>
    <p>These tools are a sample. They are built the way I build the paid work &mdash; fast, in two
      languages, on your own numbers, and with nothing hidden behind a form. If a free tool is useful
      enough to keep open in a tab, the case for the paid one makes itself.</p>
    <div class="btn-row" style="margin-top:22px">
      <a class="btn btn-teal" href="/en/services/#price">What I build, and what it costs</a>
      <a class="btn btn-ghost" href="/en/simulators/">Run your own numbers</a>
    </div>
  </div>
</section>

</main>
"""


def _itemlist():
    """The ItemList node, generated from LIVE.

    Typed out by hand it was a second copy of the same list - including a
    numberOfItems that a future tool would have left wrong with no error
    anywhere. Built here, adding a tool to LIVE updates the markup and the
    structured data together or not at all."""
    items = ",".join(
        '{"@type":"ListItem","position":%d,"url":"https://aiprofitlab.io%s","name":%s}'
        % (i + 1, href, json.dumps(title))
        for i, (title, _what, href, _tag, _who) in enumerate(LIVE))
    return ('{"@type":"ItemList","itemListOrder":"https://schema.org/ItemListOrderAscending",'
            '"numberOfItems":%d,"itemListElement":[%s]}' % (len(LIVE), items))


META = dict(
    slug="tools",
    title="Free tools for running a business in Oman | AI Profit Lab",
    desc=("Free browser tools for Omani businesses: a VAT tax invoice and quote maker, the Fawtara "
          "e-invoicing deadline checker with its readiness checklist, and a WhatsApp chat link and "
          "branded QR code maker. No sign-up, no email, and nothing you type is ever sent anywhere."),
    nav="/en/tools/",
    next=("Next", "What I build, and what it costs", "/en/services/"),
    schema="""{
  "@type":"CollectionPage",
  "@id":"https://aiprofitlab.io/en/tools/#collection",
  "name":"Free tools for running a business in Oman",
  "url":"https://aiprofitlab.io/en/tools/",
  "inLanguage":"en",
  "isPartOf":{"@id":"https://aiprofitlab.io/#website"},
  "about":{"@id":"https://aiprofitlab.io/#organization"},
  "mainEntity":__ITEMLIST__
}""".replace("__ITEMLIST__", _itemlist()),
)
