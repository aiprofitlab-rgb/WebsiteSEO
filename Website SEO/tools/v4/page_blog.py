#!/usr/bin/env python3
"""Articles hub.

Every entry below is a real published article: title, description and image
are read off the file in public_html/blog/en/, and the reading time is counted
from that file's own words at build time rather than guessed. Only the first
card points at the v4 skin - the rest still open in the old one, which is what
a staged migration looks like from the outside.

Categories are a filter, not a taxonomy the writer has to maintain: each post
carries one key, the chip row is derived from the keys in use, and filtering
happens in the page with no reload and no second request.
"""
import pathlib
import re

from kit import WA, WA_ICON, STAR

BLOG_DIR = pathlib.Path(__file__).resolve().parents[2] / "public_html" / "blog" / "en"

CATS = [
    ("all", "Everything"),
    ("silence", "Silence &amp; speed"),
    ("money", "Money &amp; ROI"),
    ("law", "Data &amp; the law"),
    ("systems", "Systems &amp; tools"),
]

# cat, title, dek, date, iso, image, href, source file (for the word count)
POSTS = [
    ("silence",
     "What silence costs: putting a number on the messages you never answered",
     "Twelve unread messages on a Sunday morning is not a service problem. It is a number, and this is "
     "the arithmetic that produces it.",
     "25 June 2026", "2026-06-25",
     "/blog/images/whatsapp_missed_inquiries_cost_oman.png",
     "/en/article-v4/", None, 6),
    ("money",
     "How much a WhatsApp AI receptionist costs in Oman",
     "What the setup actually involves, what Meta charges on top, and how to tell a real quote from a "
     "subscription trap.",
     "16 June 2026", "2026-06-16",
     "/blog/images/whatsapp-ai-receptionist-pricing-oman.png",
     "/blog/en/2026-06-16-whatsapp-ai-receptionist-cost-oman-2026.html",
     "2026-06-16-whatsapp-ai-receptionist-cost-oman-2026", None),
    ("systems",
     "WhatsApp Business API vs the Business app",
     "The five-device ceiling is where most Omani teams hit the wall. What migrating to the API changes, "
     "and what it costs you in flexibility.",
     "17 June 2026", "2026-06-17",
     "/blog/images/whatsapp-api-vs-app-oman-guide.png",
     "/blog/en/2026-06-17-whatsapp-business-api-vs-app-oman-guide.html",
     "2026-06-17-whatsapp-business-api-vs-app-oman-guide", None),
    ("law",
     "Oman's PDPL, explained for anyone using WhatsApp or AI",
     "Royal Decree 6/2022 in plain language: what counts as personal data, what consent has to look like, "
     "and where the line actually sits.",
     "27 July 2026", "2026-07-27",
     "/blog/images/oman-pdpl-explained-whatsapp-ai-2026.png",
     "/blog/en/2026-07-27-oman-pdpl-explained-whatsapp-ai-2026.html",
     "2026-07-27-oman-pdpl-explained-whatsapp-ai-2026", None),
    ("law",
     "The cost of non-compliance: penalties under the PDPL",
     "The fines are not theoretical and they are not small. What triggers them, and the cheapest way to "
     "stay on the right side of them.",
     "31 July 2026", "2026-07-31",
     "/blog/images/oman_pdpl_penalties.png",
     "/blog/en/2026-07-31-cost-of-non-compliance-oman-pdpl.html",
     "2026-07-31-cost-of-non-compliance-oman-pdpl", None),
    ("systems",
     "The copilot at the helm: what a 2026 CEO dashboard is for",
     "A monthly report tells you what already happened. This is the argument for a screen that tells you "
     "what is happening while you can still act on it.",
     "28 March 2026", "2026-03-28",
     "/blog/images/ceo-dashboard-story-1774720867978.png",
     "/blog/en/2026-03-28-ceo-dashboard.html",
     "2026-03-28-ceo-dashboard", None),
    ("money",
     "The engineering behind the receptionist and the dashboard",
     "The technical brief the press feature did not have room for: the two-stage pipeline, the handover "
     "rule, and the measured outcomes.",
     "8 July 2026", "2026-07-08",
     "/blog/images/boss_today_enterprise_ai_smb.png",
     "/blog/en/2026-07-08-enterprise-ai-smb-whatsapp-receptionist-ceo-dashboard.html",
     "2026-07-08-enterprise-ai-smb-whatsapp-receptionist-ceo-dashboard", None),
    ("silence",
     "Never missing a property inquiry again",
     "Real estate is the clearest case of the leak: high order value, impatient buyers, and every viewing "
     "request arriving after six.",
     "17 June 2026", "2026-06-17",
     "/blog/images/whatsapp_ai_real_estate_oman.png",
     "/blog/en/2026-06-17-whatsapp-ai-real-estate-oman-guide.html",
     "2026-06-17-whatsapp-ai-real-estate-oman-guide", None),
    ("systems",
     "Replacing manual data entry inside an Omani enterprise",
     "The work nobody bills for: re-typing the same figures between a supplier's sheet, the ERP, and the "
     "invoice. What it costs and how it goes away.",
     "12 August 2026", "2026-08-12",
     "/blog/images/automating-internal-operations-oman.png",
     "/blog/en/2026-08-12-automating-internal-operations-replacing-manual-data-entry-omani-enterprises.html",
     "2026-08-12-automating-internal-operations-replacing-manual-data-entry-omani-enterprises", None),
    ("law",
     "How company data leaks through AI &mdash; and how to stop it",
     "Your staff are already pasting your pricing into public chatbots. The fix is a policy and a boundary, "
     "not a ban nobody follows.",
     "1 April 2026", "2026-04-01",
     "/blog/images/ai-data-leak-companies.png",
     "/blog/en/2026-04-01-how-companies-data-leaks-through-ai.html",
     "2026-04-01-how-companies-data-leaks-through-ai", None),
    ("systems",
     "n8n vs Make: which one survives scale",
     "Both are fine at ten runs a day. The bill and the data-control question are what separate them at "
     "ten thousand.",
     "23 April 2026", "2026-04-23",
     "/blog/images/n8n-vs-make-automation.png",
     "/blog/en/2026-04-23-n8n-vs-make-automation-scaling.html",
     "2026-04-23-n8n-vs-make-automation-scaling", None),
    ("systems",
     "Putting AI into an Omani retail POS, step by step",
     "Stockouts at the till are a data problem before they are a buying problem. How the predictive layer "
     "attaches to a POS you already run.",
     "13 June 2026", "2026-06-13",
     "/blog/images/ai-pos-integration.png",
     "/blog/en/2026-06-13-integrate-ai-omani-retail-pos.html",
     "2026-06-13-integrate-ai-omani-retail-pos", None),
]


def _mins(stem, override):
    """Reading time counted from the published file, not estimated."""
    if override:
        return override
    f = BLOG_DIR / (stem + ".html")
    if not f.exists():
        return None
    text = f.read_text(encoding="utf-8", errors="ignore")
    body = re.search(r"<article.*?</article>", text, re.S)
    text = body.group(0) if body else text
    text = re.sub(r"<(script|style).*?</\1>", " ", text, flags=re.S)
    words = len(re.sub(r"<[^>]+>", " ", text).split())
    return max(1, round(words / 225))


CSS = """
/* --------------------------------------------------------------- filter */
.filters{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:clamp(24px,3vw,34px)}
.filters button{
  font-family:var(--mono);font-size:.8rem;letter-spacing:.09em;text-transform:uppercase;
  color:var(--teal-900);background:var(--white);border:1px solid var(--line);border-radius:99px;
  padding:9px 17px;cursor:pointer;transition:border-color .2s,background .2s,color .2s,transform .2s;
}
.filters button:hover{border-color:var(--teal);transform:translateY(-1px)}
.filters button[aria-pressed=true]{background:var(--teal-950);border-color:var(--teal-950);color:var(--cream)}
.filters .count{font-family:var(--mono);font-size:.78rem;letter-spacing:.08em;color:var(--muted);margin-left:auto}

/* ------------------------------------------------------------- featured */
.feat{
  display:grid;grid-template-columns:1.05fr .95fr;gap:0;background:var(--white);
  border:1px solid var(--line);border-radius:18px;overflow:hidden;text-decoration:none;
  transition:transform .4s var(--ease),box-shadow .4s var(--ease);
}
.feat:hover{transform:translateY(-4px);box-shadow:0 30px 60px -40px rgba(7,43,34,.6)}
.feat .shot{position:relative;background:var(--panel-2);min-height:340px}
.feat .shot img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.feat .txt{padding:clamp(26px,3.4vw,44px);display:flex;flex-direction:column;justify-content:center}
.feat .tagline{
  font-family:var(--mono);font-size:.74rem;letter-spacing:.16em;text-transform:uppercase;
  color:var(--amber-text);margin:0 0 14px;display:flex;align-items:center;gap:9px;
}
.feat h3{font-size:clamp(1.4rem,2.6vw,2.05rem);line-height:1.14;color:var(--teal-950);margin:0 0 14px}
.feat p{color:var(--muted);font-size:1.02rem;margin:0 0 20px}
.feat .stamp{font-family:var(--mono);font-size:.76rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}

/* ---------------------------------------------------------------- cards */
.posts{display:grid;grid-template-columns:repeat(3,1fr);gap:clamp(18px,2.4vw,28px)}
.post{
  display:flex;flex-direction:column;background:var(--panel);border:1px solid var(--line);
  border-radius:16px;overflow:hidden;text-decoration:none;
  transition:transform .35s var(--ease),box-shadow .35s var(--ease),border-color .35s;
}
.post:hover{transform:translateY(-4px);box-shadow:0 26px 50px -34px rgba(7,43,34,.5);border-color:var(--panel-2)}
.post .shot{aspect-ratio:16/9;background:var(--panel-2);overflow:hidden}
.post .shot img{width:100%;height:100%;object-fit:cover;transition:transform .6s var(--ease)}
.post:hover .shot img{transform:scale(1.04)}
.post .txt{padding:clamp(20px,2.2vw,26px);display:flex;flex-direction:column;flex:1}
.post .kicker{font-family:var(--mono);font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;color:var(--amber-text);margin:0 0 11px}
.post h3{font-size:clamp(1.06rem,1.5vw,1.22rem);line-height:1.26;color:var(--teal-950);margin:0 0 10px}
.post p{color:var(--muted);font-size:.95rem;line-height:1.55;margin:0 0 18px}
.post .stamp{
  margin-top:auto;padding-top:14px;border-top:1px solid var(--line);
  font-family:var(--mono);font-size:.73rem;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);
  display:flex;justify-content:space-between;gap:10px;
}
.post .stamp .old{color:var(--taupe)}
.post[hidden]{display:none}
.empty{
  border:1px dashed var(--line);border-radius:16px;padding:clamp(30px,5vw,60px);text-align:center;color:var(--muted);
}
.empty b{display:block;font-family:var(--display);font-size:1.3rem;color:var(--teal-950);font-weight:400;margin-bottom:8px}

@media (max-width:1080px){
  /* minmax(0,…) everywhere: a card's <img> carries a width attribute, so the
     automatic minimum of a plain 1fr track is that image's own width and the
     grid quietly grows past a phone viewport. */
  .posts{grid-template-columns:repeat(2,minmax(0,1fr))}
  .feat{grid-template-columns:minmax(0,1fr)}
  /* min-height with aspect-ratio sets an automatic minimum in the INLINE
     axis too (220 x 16/8 = 440px), which overrode the grid track and
     pushed the card off a phone screen. The ratio alone sizes it. */
  .feat .shot{min-height:0;aspect-ratio:16/8}
}
@media (max-width:640px){
  .posts{grid-template-columns:minmax(0,1fr)}
  .filters .count{width:100%;margin:4px 0 0}
}
"""

JS = """
/* ---------------------------------------------------------------------------
   Category filter. Server-rendered cards, hidden and shown in place - there is
   no second list and no fetch, so the page works identically with the filter
   never touched.
--------------------------------------------------------------------------- */
(function(){
  "use strict";
  var bar = document.getElementById("filters");
  if (!bar) return;
  var cards = [].slice.call(document.querySelectorAll(".post"));
  var count = document.getElementById("fcount");
  var empty = document.getElementById("empty");

  bar.addEventListener("click", function(e){
    var b = e.target.closest("button"); if (!b) return;
    var key = b.getAttribute("data-cat");
    [].forEach.call(bar.querySelectorAll("button"), function(x){
      x.setAttribute("aria-pressed", x === b ? "true" : "false");
    });
    var shown = 0;
    cards.forEach(function(c){
      var on = key === "all" || c.getAttribute("data-cat") === key;
      c.hidden = !on; if (on) shown++;
    });
    if (count) count.textContent = shown + (shown === 1 ? " article" : " articles");
    if (empty) empty.hidden = shown > 0;
    if (typeof gtag === "function") gtag("event","filter_articles",{category:key});
  });
})();
"""


def _card(p):
    cat, title, dek, date, iso, img, href, stem, override = p
    mins = _mins(stem, override)
    read = f"{mins} min" if mins else ""
    old = "" if href.startswith("/en/") else '<span class="old">Older skin</span>'
    return f"""<a class="post" href="{href}" data-cat="{cat}">
      <div class="shot"><img src="{img}" alt="" loading="lazy" decoding="async" width="420" height="236"></div>
      <div class="txt">
        <p class="kicker">{dict(CATS)[cat]}</p>
        <h3>{title}</h3>
        <p>{dek}</p>
        <span class="stamp"><time datetime="{iso}">{date}</time><span>{old}{" &middot; " if old and read else ""}{read}</span></span>
      </div>
    </a>"""


def body():
    feat = POSTS[0]
    rest = POSTS[1:]
    chips = "".join(
        f'<button type="button" data-cat="{k}" aria-pressed="{"true" if k == "all" else "false"}">{lbl}</button>'
        for k, lbl in CATS)
    cards = "\n".join(_card(p) for p in rest)

    return f"""<main id="main">

<section class="phero s-panel grain">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span>Articles</p>
    <h1 class="h1">Notes from the work</h1>
    <p class="lede">Everything here comes out of a system I actually built for someone in Oman. No trend
      pieces, no borrowed statistics &mdash; if a number appears, you can see where it came from or how to
      produce it yourself.</p>
    <div class="filters" id="filters">
      {chips}
      <span class="count" id="fcount">{len(rest)} articles</span>
    </div>
  </div>
</section>

<section class="s-cream pad-s">
  <div class="wrap">
    <a class="feat rv" href="{feat[6]}">
      <div class="shot"><img src="{feat[5]}" alt="" width="620" height="420" fetchpriority="high"></div>
      <div class="txt">
        <p class="tagline"><span class="star">{STAR}</span>Start here</p>
        <h3>{feat[1]}</h3>
        <p>{feat[2]}</p>
        <span class="stamp">{feat[3]} &middot; {feat[8]} min read</span>
      </div>
    </a>
  </div>
</section>

<section class="s-cream" style="padding-top:0">
  <div class="wrap">
    <div class="asterism"><span>{STAR}</span></div>
    <div class="posts" data-stagger>
{cards}
    </div>
    <div class="empty" id="empty" hidden style="margin-top:24px">
      <b>Nothing filed under that yet.</b>
      <p style="margin:0">Ask me the question directly and I will answer it &mdash; and probably write it up afterwards.</p>
    </div>
  </div>
</section>

<section class="s-dark grain">
  <div class="wrap-n" style="text-align:center">
    <p class="eyebrow" style="justify-content:center"><span class="star">{STAR}</span>Not covered here</p>
    <h2 class="h2">Ask the question you actually have</h2>
    <p class="lede" style="margin-inline:auto">The articles answer what people ask most often. Yours is
      probably more specific than that &mdash; send it and you get an answer from the person who builds the
      thing, not a form reply.</p>
    <div class="btn-row" style="justify-content:center;margin-top:26px">
      <a class="btn btn-wa" href="{WA}&text=Hello%20Nahid%2C%20I%20have%20a%20question%20I%20did%20not%20find%20an%20article%20about.">{WA_ICON}<span>Ask on WhatsApp</span></a>
      <a class="btn btn-ghost" href="/en/simulator-v4/">Run the numbers instead</a>
    </div>
  </div>
</section>

</main>
"""


META = dict(
    slug="blog-v4",
    title="Articles | AI Profit Lab — notes from the work in Oman",
    desc=("Practical writing on WhatsApp response gaps, owner dashboards, automation cost and Oman's PDPL "
          "- from the operator who builds the systems, not a content team."),
    nav="/en/blog-v4/",
    next=("Start here", "What silence costs", "/en/article-v4/"),
    schema="""{
  "@context":"https://schema.org",
  "@type":"Blog",
  "name":"AI Profit Lab — Articles",
  "url":"https://aiprofitlab.io/en/blog-v4/",
  "inLanguage":"en",
  "publisher":{"@type":"Organization","name":"AI Profit Lab","legalName":"Lotus Gulf International"}
}""",
)
