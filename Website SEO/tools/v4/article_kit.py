#!/usr/bin/env python3
"""
AI Profit Lab — v4 article system.

This is a TEMPLATE, not a page. `page_article.py` supplies one article's
content; the same renderer is what the 149 pages under public_html/blog/en/
would be poured into when the set launches.

An article is a dict:

    {"cat", "title", "dek", "date", "updated", "image", "alt", "caption",
     "body": [ (block, ...), ... ], "faq": [(q, a), ...], "refs": [(label, url)],
     "related": [(cat, title, href)]}

`body` is a list of typed blocks rather than a slab of HTML so that the
migration script can map an old article's DOM onto named components once and
get every v4 detail (section numbering, table scroll containers, figure
captions, callout labels) for free. Adding a component means adding one
function here and one key to BLOCKS — no page edits.

Read time and the table of contents are both computed at build time, so the
page is complete and navigable with JavaScript switched off.
"""
import html
import re

from kit import WA, WA_ICON, STAR

# --------------------------------------------------------------------------
# CSS
# --------------------------------------------------------------------------
ARTICLE_CSS = """
/* ---------------------------------------------------------- reading bar */
/* Sits above the fixed header (z-80) so it reads as chrome of the window,
   not of the page. Width is set by JS; with no JS it simply stays at 0. */
.prog{position:fixed;top:0;left:0;height:2px;width:0;z-index:90;background:var(--amber);will-change:width}

/* ---------------------------------------------------------------- hero */
/* Two measures: the headline column is narrow (880) so a long title breaks
   into readable lines; the figure and the body grid use the site's own 1180. */
.artwrap{width:min(1180px,92vw);margin-inline:auto}
.wrap-a{width:min(880px,92vw);margin-inline:auto}
.ahero{padding:clamp(126px,15vw,178px) 0 clamp(26px,3.5vw,40px);background:var(--panel);position:relative;overflow:hidden}
.crumbs{
  font-family:var(--mono);font-size:.76rem;letter-spacing:.12em;text-transform:uppercase;
  color:var(--muted);margin:0 0 20px;display:flex;gap:9px;flex-wrap:wrap;align-items:center;
}
.crumbs a{color:var(--muted);text-decoration:none;transition:color .2s}
.crumbs a:hover{color:var(--amber-text)}
.crumbs i{color:var(--amber);font-style:normal}
.ahero .h1{font-size:clamp(2rem,4.4vw,3.35rem);line-height:1.06;margin:0 0 20px}
.ahero .lede{font-size:clamp(1.1rem,1.8vw,1.32rem);max-width:62ch}

.byline{
  display:flex;align-items:center;gap:15px;flex-wrap:wrap;
  margin-top:clamp(26px,3.5vw,38px);padding-top:20px;border-top:1px solid var(--line);
}
.byline .face{width:46px;height:46px;border-radius:50%;object-fit:cover;flex:none;filter:saturate(.94)}
.byline .who{line-height:1.35}
.byline .who b{display:block;font-weight:500;font-size:1rem;color:var(--teal-950)}
.byline .who span,.byline .stamp{
  font-family:var(--mono);font-size:.76rem;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);
}
.byline .sp{flex:1 1 40px}

/* share — icon buttons, no third-party script and therefore no third-party
   cookie. Each is a plain link except copy, which needs one clipboard call. */
.share{display:flex;gap:9px;align-items:center}
.share a,.share button{
  width:40px;height:40px;border-radius:50%;border:1px solid var(--line);background:var(--white);
  display:inline-flex;align-items:center;justify-content:center;color:var(--teal-900);cursor:pointer;
  padding:0;transition:border-color .2s,color .2s,transform .2s,background .2s;
}
.share a:hover,.share button:hover{border-color:var(--teal);color:var(--teal);transform:translateY(-2px)}
.share svg{width:17px;height:17px;fill:currentColor}
.share .done{border-color:var(--wa);color:var(--wa)}

/* hero figure */
.afig{margin:0;position:relative;background:var(--panel-2);border:1px solid var(--line);
  border-radius:20px;padding:clamp(10px,1.2vw,16px)}
.afig img{width:100%;aspect-ratio:16/7;object-fit:cover;border-radius:12px}
.afig figcaption{
  font-family:var(--mono);font-size:.76rem;letter-spacing:.07em;color:var(--muted);
  margin:12px 4px 4px;padding-left:14px;border-left:2px solid var(--amber);
}

/* ---------------------------------------------------------- body layout */
.artgrid{display:grid;grid-template-columns:206px minmax(0,1fr);gap:clamp(28px,5vw,68px);align-items:start}
.toc{position:sticky;top:106px}
.toc h2{
  font-family:var(--mono);font-size:.74rem;font-weight:500;letter-spacing:.16em;text-transform:uppercase;
  color:var(--muted);margin:0 0 14px;
}
.toc ol{list-style:none;margin:0;padding:0}
.toc a{
  display:block;font-size:.9rem;line-height:1.35;color:var(--muted);text-decoration:none;
  padding:8px 0 8px 15px;border-left:1px solid var(--line);transition:color .25s,border-color .25s;
}
.toc a:hover{color:var(--teal)}
.toc a.on{color:var(--teal-950);border-left-color:var(--amber)}
.toc .back{margin-top:20px}

/* ---------------------------------------------------------------- prose */
.prose{counter-reset:sec;max-width:68ch}
.prose p{font-size:clamp(1.04rem,1.4vw,1.13rem);line-height:1.72;margin:0 0 1.25em;color:var(--ink)}
.prose p.open::first-letter{
  float:left;font-family:var(--display);font-size:3.5em;line-height:.82;padding:.06em .1em 0 0;color:var(--teal);
}
.prose h2{
  font-size:clamp(1.55rem,2.9vw,2.2rem);line-height:1.15;color:var(--teal-950);
  margin:clamp(46px,6vw,74px) 0 18px;scroll-margin-top:104px;
}
/* Section numerals come from a counter, not from markup: the TOC reads
   heading.textContent, and a numeral in the markup would end up in every
   entry. ::before is not a child node, so the motion script's wipe wrapper
   leaves it alone and it holds still while the words rise. */
.prose h2::before{
  content:counter(sec,decimal-leading-zero);counter-increment:sec;display:block;
  font-family:var(--mono);font-size:.76rem;letter-spacing:.18em;color:var(--amber-text);margin-bottom:11px;
}
.prose h3{font-size:clamp(1.18rem,1.9vw,1.4rem);color:var(--teal-950);margin:clamp(30px,3.5vw,44px) 0 12px;scroll-margin-top:104px}
.prose a{color:var(--teal);text-decoration:none;background-image:linear-gradient(var(--amber),var(--amber));
  background-size:100% 1px;background-position:0 100%;background-repeat:no-repeat;padding-bottom:2px;
  transition:color .2s,background-size .3s var(--ease)}
.prose a:hover{color:var(--amber-text)}
/* A button inside the prose is not a prose link. `.prose a` (0,2,0) outranks
   `.btn-wa` (0,1,0), which repainted the pill's own label teal and drew the
   link underline straight through it. */
.prose .btn{background-image:none;padding-bottom:15px}
.prose .btn-wa,.prose .btn-teal{color:#fff}
.prose .btn-amber{color:var(--teal-950)}
.prose .btn-ghost{color:var(--teal-900)}
.icta .btn-ghost{color:var(--cream);border-color:var(--line-dark)}
.prose strong{font-weight:600;color:var(--teal-950)}
.prose em{font-style:italic}
.prose code{
  font-family:var(--mono);font-size:.88em;background:var(--panel-2);border:1px solid var(--line);
  border-radius:5px;padding:1px 6px;color:var(--teal-900);
}
.prose ul,.prose ol{margin:0 0 1.35em;padding-left:0;list-style:none}
.prose li{position:relative;padding-left:30px;margin-bottom:.7em;font-size:clamp(1.02rem,1.35vw,1.1rem);line-height:1.65}
.prose ul>li::before{
  content:"";position:absolute;left:6px;top:.62em;width:7px;height:7px;border-radius:50%;background:var(--amber);
}
.prose ol{counter-reset:li}
.prose ol>li::before{
  counter-increment:li;content:counter(li,decimal-leading-zero);position:absolute;left:0;top:.16em;
  font-family:var(--mono);font-size:.8rem;color:var(--amber-text);
}

/* ------------------------------------------------------------ takeaways */
.keybox{
  background:var(--white);border:1px solid var(--line);border-left:3px solid var(--amber);
  border-radius:0 14px 14px 0;padding:clamp(22px,3vw,30px) clamp(22px,3vw,32px);margin:0 0 clamp(34px,4vw,48px);
}
.keybox h4{
  font-family:var(--mono);font-size:.76rem;font-weight:500;letter-spacing:.16em;text-transform:uppercase;
  color:var(--amber-text);margin:0 0 16px;display:flex;align-items:center;gap:9px;
}
.keybox ul{margin:0;padding:0;list-style:none}
.keybox li{position:relative;padding-left:26px;margin:0 0 .65em;font-size:1.02rem;line-height:1.6;color:var(--ink)}
.keybox li:last-child{margin-bottom:0}
.keybox li::before{content:"\\2727";position:absolute;left:0;top:0;color:var(--amber);font-size:.95em}

/* -------------------------------------------------------------- quotes */
.prose blockquote{
  margin:clamp(34px,4vw,50px) 0;padding:0 0 0 clamp(20px,3vw,30px);border-left:2px solid var(--amber);
}
.prose blockquote p{
  font-family:var(--display);font-size:clamp(1.3rem,2.2vw,1.65rem);line-height:1.35;color:var(--teal-950);margin:0 0 .5em;
}
.prose blockquote cite{
  font-family:var(--mono);font-size:.78rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);font-style:normal;
}
/* A pull quote is a break in the column, not a citation: hairline above and
   below, no rule on the side, so it reads as a held breath. */
.pull{
  margin:clamp(38px,5vw,58px) 0;padding:clamp(24px,3vw,32px) 0;
  border-top:1px solid var(--line);border-bottom:1px solid var(--line);text-align:center;
}
.pull p{font-family:var(--display);font-size:clamp(1.4rem,2.6vw,1.9rem);line-height:1.3;color:var(--teal);margin:0}

/* ------------------------------------------------------------ callouts */
.callout{
  background:var(--panel);border:1px solid var(--line);border-radius:14px;
  padding:clamp(20px,2.6vw,26px) clamp(20px,2.6vw,28px);margin:clamp(30px,3.6vw,42px) 0;position:relative;
}
.callout b{
  display:block;font-family:var(--mono);font-size:.75rem;font-weight:500;letter-spacing:.16em;
  text-transform:uppercase;margin-bottom:10px;color:var(--teal);
}
.callout p{margin:0;font-size:1.02rem;line-height:1.65}
.callout p+p{margin-top:.8em}
.callout.warn{background:rgba(166,67,31,.05);border-color:rgba(166,67,31,.28)}
.callout.warn b{color:var(--alert)}
.callout.tip{background:rgba(186,117,23,.06);border-color:rgba(186,117,23,.3)}
.callout.tip b{color:var(--amber-text)}

/* the arithmetic itself, set as a plate rather than a sentence */
.formula{
  background:var(--teal-950);color:var(--cream);border-radius:14px;
  padding:clamp(22px,3vw,30px);margin:clamp(30px,3.6vw,42px) 0;text-align:center;
}
.formula span{
  font-family:var(--mono);font-size:clamp(.92rem,1.6vw,1.08rem);line-height:1.9;letter-spacing:.02em;
  color:var(--cream);display:block;
}
.formula em{color:var(--amber-bright);font-style:normal}
.formula .lbl{
  font-size:.72rem;letter-spacing:.18em;text-transform:uppercase;color:rgba(241,239,232,.55);margin-bottom:12px;
}

/* ---------------------------------------------------------------- steps */
.steps{margin:clamp(26px,3vw,38px) 0;border-top:1px solid var(--line)}
/* > div, not div: the row holds a second div for its text, and a bare
   descendant selector turned that inner wrapper into a grid too. */
.steps>div{display:grid;grid-template-columns:56px 1fr;gap:clamp(14px,2vw,22px);padding:22px 0;border-bottom:1px solid var(--line)}
.steps b{font-family:var(--mono);font-size:.82rem;letter-spacing:.1em;color:var(--amber-text);padding-top:.32em}
.steps h4{font-family:var(--display);font-size:clamp(1.12rem,1.8vw,1.3rem);font-weight:400;color:var(--teal-950);margin:0 0 7px}
.steps p{margin:0;font-size:1rem;color:var(--muted);line-height:1.62}

/* ---------------------------------------------------------------- table */
/* Wide tables scroll inside their own container - the page body never does. */
.tblwrap{margin:clamp(30px,3.6vw,44px) 0;overflow-x:auto;border:1px solid var(--line);border-radius:14px;background:var(--white)}
.tbl{border-collapse:collapse;width:100%;min-width:520px;font-size:.97rem}
.tbl th{
  text-align:left;font-family:var(--mono);font-size:.74rem;font-weight:500;letter-spacing:.13em;
  text-transform:uppercase;color:var(--muted);background:var(--panel);padding:14px 18px;border-bottom:1px solid var(--line);
}
.tbl td{padding:14px 18px;border-bottom:1px solid var(--line);color:var(--ink);vertical-align:top}
.tbl tr:last-child td{border-bottom:0}
.tbl td.n{font-family:var(--mono);font-variant-numeric:tabular-nums;white-space:nowrap;color:var(--teal-900)}
.tbl tbody tr:hover{background:var(--panel)}
.tblcap{font-family:var(--mono);font-size:.75rem;letter-spacing:.07em;color:var(--muted);margin:-24px 0 34px;padding-left:16px;border-left:2px solid var(--amber)}

/* --------------------------------------------------------------- figure */
.pfig{margin:clamp(30px,3.6vw,44px) 0}
.pfig img{width:100%;border-radius:14px;border:1px solid var(--line)}
.pfig figcaption{font-family:var(--mono);font-size:.75rem;letter-spacing:.07em;color:var(--muted);margin-top:11px;padding-left:16px;border-left:2px solid var(--amber)}

/* ---------------------------------------------------------------- stats */
.pstats{display:grid;grid-template-columns:repeat(3,1fr);gap:clamp(14px,2vw,20px);margin:clamp(30px,3.6vw,44px) 0}
.pstats div{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:22px 20px}
.pstats b{display:block;font-family:var(--mono);font-size:clamp(1.5rem,3vw,2rem);color:var(--teal);line-height:1;margin-bottom:9px;font-weight:500}
.pstats span{font-size:.88rem;color:var(--muted);line-height:1.45;display:block}

/* ------------------------------------------------------------ inline CTA */
.icta{
  background:var(--teal-900);color:var(--cream);border-radius:16px;
  padding:clamp(26px,3.4vw,38px);margin:clamp(38px,4.5vw,56px) 0;position:relative;overflow:hidden;
}
.icta::after{
  content:"";position:absolute;right:-40px;bottom:-40px;width:150px;height:150px;border-radius:50%;
  background:rgba(186,117,23,.16);
}
.icta h3{font-size:clamp(1.25rem,2.2vw,1.6rem);color:var(--cream);margin:0 0 10px;position:relative}
.icta p{color:rgba(241,239,232,.78);font-size:1rem;margin:0 0 20px;max-width:52ch;position:relative}
.icta .btn-row{position:relative}

/* ------------------------------------------------------------------ FAQ */
.faq{border-top:1px solid var(--line)}
.faq details{border-bottom:1px solid var(--line)}
.faq summary{
  cursor:pointer;list-style:none;padding:20px 44px 20px 0;position:relative;
  font-family:var(--display);font-size:clamp(1.05rem,1.7vw,1.24rem);color:var(--teal-950);
  transition:color .2s;
}
.faq summary::-webkit-details-marker{display:none}
.faq summary:hover{color:var(--teal)}
.faq summary::after{
  content:"";position:absolute;right:8px;top:50%;width:13px;height:1.5px;background:var(--amber);
}
.faq summary::before{
  content:"";position:absolute;right:14px;top:50%;width:1.5px;height:13px;margin-top:-6px;background:var(--amber);
  transition:transform .3s var(--ease),opacity .3s;
}
.faq details[open] summary::before{transform:rotate(90deg);opacity:0}
.faq details p{margin:0 0 20px;color:var(--muted);font-size:1.01rem;line-height:1.68;max-width:66ch;padding-right:44px}

/* ------------------------------------------------------------ references */
.refs{margin-top:clamp(34px,4vw,50px);padding-top:26px;border-top:1px solid var(--line)}
.refs h2{font-family:var(--mono);font-size:.75rem;font-weight:500;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin:0 0 14px}
.refs ol{list-style:none;margin:0;padding:0;counter-reset:r}
.refs li{position:relative;padding-left:32px;margin-bottom:.6em;font-size:.94rem;line-height:1.5}
.refs li::before{counter-increment:r;content:counter(r,decimal-leading-zero);position:absolute;left:0;top:.15em;font-family:var(--mono);font-size:.76rem;color:var(--amber-text)}
.refs a{color:var(--teal);text-decoration:none;border-bottom:1px solid var(--line)}
.refs a:hover{color:var(--amber-text);border-bottom-color:var(--amber)}

/* --------------------------------------------------------------- author */
.author{
  display:grid;grid-template-columns:104px 1fr;gap:clamp(18px,3vw,30px);align-items:start;
  background:var(--panel-2);border-radius:16px;padding:clamp(24px,3vw,34px);margin-top:clamp(40px,5vw,60px);
}
.author img{width:104px;height:104px;border-radius:50%;object-fit:cover;filter:saturate(.94)}
.author .rolelbl{font-family:var(--mono);font-size:.74rem;letter-spacing:.16em;text-transform:uppercase;color:var(--amber-text);margin:0 0 8px}
.author h3{font-size:clamp(1.2rem,2vw,1.45rem);margin:0 0 10px}
.author p{font-size:.99rem;color:var(--muted);margin:0 0 16px;line-height:1.62}

/* -------------------------------------------------------------- related */
.related .card h3{font-size:clamp(1.08rem,1.6vw,1.25rem);line-height:1.28}
.related a.card{text-decoration:none;display:block}
.related .card .n{color:var(--amber-text)}
.related .card .rd{font-family:var(--mono);font-size:.74rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-top:16px;display:block}

/* --------------------------------------------------------- breakpoints */
@media (max-width:1080px){
  /* minmax(0,1fr), never 1fr: a grid item's automatic minimum is its
     min-content width, so the 520px min-width on a wide table stretched the
     whole column past the viewport and every line of prose was clipped with
     it. The table still scrolls inside .tblwrap. */
  .artgrid{grid-template-columns:minmax(0,1fr)}
  /* The rail becomes a plate above the article: still one tap to any
     section, but no longer competing with the text for width. */
  .toc{position:static;border:1px solid var(--line);border-radius:14px;padding:22px 24px;background:var(--panel);margin-bottom:34px}
  .toc ol{columns:2;column-gap:26px}
  .toc a{padding:6px 0 6px 13px;break-inside:avoid}
  .toc .back{display:none}
  .prose{max-width:none}
}
@media (max-width:640px){
  .toc ol{columns:1}
  .pstats{grid-template-columns:1fr}
  .author{grid-template-columns:1fr;text-align:left}
  .author img{width:84px;height:84px}
  .steps>div{grid-template-columns:1fr;gap:4px}
  .afig img{aspect-ratio:4/3}
  .byline .sp{display:none}
  .byline .share{width:100%;margin-top:6px}
}
"""

# --------------------------------------------------------------------------
# JS — progress bar, TOC scrollspy, copy-link
# --------------------------------------------------------------------------
ARTICLE_JS = """
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
"""

# --------------------------------------------------------------------------
# Block renderers
# --------------------------------------------------------------------------
_ID_STRIP = re.compile(r"<[^>]+>|[^a-z0-9\s-]")


def slug(text):
    s = _ID_STRIP.sub("", text.lower().replace("&mdash;", " ").replace("&amp;", " "))
    return re.sub(r"\s+", "-", s.strip())[:60].strip("-")


def _p(text, cls=""):
    c = f' class="{cls}"' if cls else ""
    return f"<p{c}>{text}</p>"


def _h2(text):
    return f'<h2 id="{slug(text)}">{text}</h2>'


def _h3(text):
    return f'<h3 id="{slug(text)}">{text}</h3>'


def _ul(items):
    li = "".join(f"<li>{i}</li>" for i in items)
    return f"<ul>{li}</ul>"


def _ol(items):
    li = "".join(f"<li>{i}</li>" for i in items)
    return f"<ol>{li}</ol>"


def _steps(rows):
    out = ['<div class="steps">']
    for i, (head, text) in enumerate(rows, 1):
        out.append(f'<div><b>{i:02d}</b><div><h4>{head}</h4><p>{text}</p></div></div>')
    out.append("</div>")
    return "".join(out)


def _quote(text, cite=""):
    c = f"<cite>{cite}</cite>" if cite else ""
    return f"<blockquote><p>{text}</p>{c}</blockquote>"


def _pull(text):
    return f'<div class="pull"><p>{text}</p></div>'


def _callout(kind, label, *paras):
    body = "".join(f"<p>{p}</p>" for p in paras)
    k = f" {kind}" if kind else ""
    return f'<div class="callout{k}"><b>{label}</b>{body}</div>'


def _formula(label, line):
    return f'<div class="formula"><span class="lbl">{label}</span><span>{line}</span></div>'


def _table(head, rows, caption=""):
    th = "".join(f"<th>{h}</th>" for h in head)
    tr = []
    for r in rows:
        tds = []
        for cell in r:
            # a leading "~" marks a numeric cell: mono, tabular, never wrapped
            if isinstance(cell, str) and cell.startswith("~"):
                tds.append(f'<td class="n">{cell[1:]}</td>')
            else:
                tds.append(f"<td>{cell}</td>")
        tr.append("<tr>" + "".join(tds) + "</tr>")
    cap = f'<p class="tblcap">{caption}</p>' if caption else ""
    return ('<div class="tblwrap"><table class="tbl"><thead><tr>' + th + "</tr></thead><tbody>"
            + "".join(tr) + "</tbody></table></div>" + cap)


def _figure(src, alt, caption=""):
    cap = f"<figcaption>{caption}</figcaption>" if caption else ""
    return (f'<figure class="pfig"><img src="{src}" alt="{html.escape(alt, quote=True)}" '
            f'loading="lazy" decoding="async">{cap}</figure>')


def _stats(items):
    out = ['<div class="pstats" data-stagger>']
    for value, label in items:
        out.append(f"<div><b>{value}</b><span>{label}</span></div>")
    out.append("</div>")
    return "".join(out)


def _cta(heading, text, label, wa_text):
    return (f'<div class="icta"><h3>{heading}</h3><p>{text}</p><div class="btn-row">'
            f'<a class="btn btn-wa" href="{WA}&text={wa_text}">{WA_ICON}<span>{label}</span></a>'
            f'</div></div>')


BLOCKS = {
    "p": lambda t: _p(t),
    "open": lambda t: _p(t, "open"),
    "h2": _h2,
    "h3": _h3,
    "ul": _ul,
    "ol": _ol,
    "steps": _steps,
    "quote": _quote,
    "pull": _pull,
    "callout": _callout,
    "formula": _formula,
    "table": _table,
    "figure": _figure,
    "stats": _stats,
    "cta": _cta,
}


def _blocks_html(body):
    return "\n".join(BLOCKS[b[0]](*b[1:]) for b in body)


# --------------------------------------------------------------------------
# Read time + table of contents, both derived from the block list
# --------------------------------------------------------------------------
def read_time(body):
    words = 0
    for b in body:
        for part in b[1:]:
            if isinstance(part, str):
                words += len(re.sub(r"<[^>]+>", " ", part).split())
            elif isinstance(part, (list, tuple)):
                for row in part:
                    row = row if isinstance(row, (list, tuple)) else [row]
                    for cell in row:
                        if isinstance(cell, str):
                            words += len(re.sub(r"<[^>]+>", " ", cell).split())
    return max(1, round(words / 225))


def toc(body):
    return [(t[1], slug(t[1])) for t in body if t[0] == "h2"]


# --------------------------------------------------------------------------
# Page composition
# --------------------------------------------------------------------------
LI_ICON = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 '
           '0-5zM3 9h4v12H3zM9 9h3.8v1.7h.05c.53-.95 1.83-1.95 3.77-1.95 4.03 0 4.78 2.5 4.78 5.76V21h-4v-5.6c0'
           '-1.34-.03-3.06-1.9-3.06-1.9 0-2.2 1.45-2.2 2.96V21H9z"/></svg>')
LINK_ICON = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10.6 13.4a1 1 0 0 1 0-1.4l1.4-1.4a1 1 0 0 '
             '1 1.4 1.4l-1.4 1.4a1 1 0 0 1-1.4 0zm-3 4.4a3.5 3.5 0 0 1 0-5l2.2-2.1 1.4 1.4-2.2 2.1a1.5 1.5 0 0 '
             '0 2.2 2.2l2.1-2.2 1.4 1.4-2.1 2.2a3.5 3.5 0 0 1-5 0zm9-9a3.5 3.5 0 0 0-5 0l-2.1 2.2 1.4 1.4 2.1'
             '-2.2a1.5 1.5 0 0 1 2.2 2.2l-2.2 2.1 1.4 1.4 2.2-2.1a3.5 3.5 0 0 0 0-5z"/></svg>')

PORTRAIT = "/nahid-founder-2026.webp"


def share_row(title, url):
    t = title.replace('"', "&quot;")
    from urllib.parse import quote
    q = quote(f"{title} — {url}")
    return f"""<div class="share">
      <a href="https://api.whatsapp.com/send?text={q}" target="_blank" rel="noopener" aria-label="Share on WhatsApp" title="Share on WhatsApp">{WA_ICON}</a>
      <a href="https://www.linkedin.com/sharing/share-offsite/?url={quote(url)}" target="_blank" rel="noopener" aria-label="Share on LinkedIn" title="Share on LinkedIn">{LI_ICON}</a>
      <button type="button" id="copyLink" aria-label="Copy link" title="Copy link">{LINK_ICON}</button>
    </div><!-- {t} -->"""


def render(art):
    """Compose one article page body (everything between header and pager)."""
    url = "https://aiprofitlab.io" + art["path"]
    mins = read_time(art["body"])
    entries = toc(art["body"])

    toc_html = "".join(f'<li><a href="#{i}">{t}</a></li>' for t, i in entries)
    if art.get("faq"):
        toc_html += '<li><a href="#questions">Questions people ask</a></li>'

    keybox = ""
    if art.get("takeaways"):
        li = "".join(f"<li>{t}</li>" for t in art["takeaways"])
        keybox = (f'<div class="keybox"><h4><span class="star">{STAR}</span>The short version</h4>'
                  f"<ul>{li}</ul></div>")

    faq = ""
    if art.get("faq"):
        rows = "".join(
            f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in art["faq"])
        faq = (f'<section class="faq" id="questions" style="margin-top:clamp(48px,6vw,74px)">'
               f'<h2 style="scroll-margin-top:104px">Questions people ask</h2>{rows}</section>')

    refs = ""
    if art.get("refs"):
        li = "".join(f'<li><a href="{u}" target="_blank" rel="noopener nofollow">{l}</a></li>'
                     for l, u in art["refs"])
        refs = f'<div class="refs"><h4>Sources</h4><ol>{li}</ol></div>'

    related = ""
    if art.get("related"):
        cards = "".join(
            f'<a class="card" href="{href}"><span class="n">{cat}</span><h3>{title}</h3>'
            f'<span class="rd">Read &rarr;</span></a>'
            for cat, title, href in art["related"])
        related = f"""
<section class="s-panel related grain">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span>Keep reading</p>
    <div class="grid g3" data-stagger>{cards}</div>
  </div>
</section>"""

    stamp = art["date"]
    if art.get("updated"):
        stamp += f' &middot; updated {art["updated"]}'

    return f"""<div class="prog" id="prog" aria-hidden="true"></div>
<main id="main">

<section class="ahero grain">
  <div class="wrap-a">
    <p class="crumbs">
      <a href="/">Home</a><i>{STAR}</i><a href="/blog/">Articles</a><i>{STAR}</i>
      <span>{art["cat"]}</span>
    </p>
    <h1 class="h1">{art["title"]}</h1>
    <p class="lede">{art["dek"]}</p>
    <div class="byline">
      <img class="face" src="{PORTRAIT}" alt="Nahid Abyari" width="46" height="46" loading="lazy">
      <div class="who"><b>Nahid Abyari</b><span>Founder &middot; writes every word</span></div>
      <span class="sp"></span>
      <span class="stamp">{stamp} &middot; {mins} min read</span>
      {share_row(art["title"], url)}
    </div>
  </div>
  <div class="artwrap" style="margin-top:clamp(32px,4.5vw,58px)">
    <figure class="afig">
      <img src="{art["image"]}" alt="{html.escape(art["alt"], quote=True)}" width="1180" height="516" fetchpriority="high">
      <figcaption>{art["caption"]}</figcaption>
    </figure>
  </div>
</section>

<section class="s-cream">
  <div class="artwrap">
    <div class="artgrid">
      <nav class="toc" aria-label="On this page">
        <h4>On this page</h4>
        <ol>{toc_html}</ol>
        <p class="back"><a class="tlink" href="/blog/"><span class="arw">&larr;</span><span>All articles</span></a></p>
      </nav>
      <div id="art">
        {keybox}
        <article class="prose">
{_blocks_html(art["body"])}
        </article>
        {faq}
        {refs}
        <div class="author">
          <img src="{PORTRAIT}" alt="Nahid Abyari" width="104" height="104" loading="lazy">
          <div>
            <p class="rolelbl">Who wrote this</p>
            <h3>Nahid Abyari</h3>
            <p>I build the systems I write about — one operator in Muscat, not an agency. Everything
              here comes out of work done for trading and distribution owners in Oman. If a number in
              this article does not match your business, send me yours and I will run it with you.</p>
            <div class="btn-row">
              <a class="btn btn-wa" href="{WA}&text=Hello%20Nahid%2C%20I%20read%20your%20article%20and%20have%20a%20question.">{WA_ICON}<span>Ask me directly</span></a>
              <a class="tlink" href="/en/about/">More about me <span class="arw">&rarr;</span></a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>
{related}
</main>
"""


def schema(art):
    """Article + FAQPage + BreadcrumbList, as one @graph."""
    url = "https://aiprofitlab.io" + art["path"]
    faq = ""
    if art.get("faq"):
        items = ",".join(
            '{"@type":"Question","name":%s,"acceptedAnswer":{"@type":"Answer","text":%s}}'
            % (_json(q), _json(a)) for q, a in art["faq"])
        faq = ',{"@type":"FAQPage","mainEntity":[%s]}' % items
    return """{
  "@context":"https://schema.org",
  "@graph":[
    {"@type":"Article",
     "headline":%s,
     "description":%s,
     "image":"https://aiprofitlab.io%s",
     "datePublished":"%s","dateModified":"%s",
     "author":{"@type":"Person","name":"Nahid Abyari","url":"https://aiprofitlab.io/en/about/"},
     "publisher":{"@type":"Organization","name":"AI Profit Lab","legalName":"Lotus Gulf International"},
     "mainEntityOfPage":{"@type":"WebPage","@id":"%s"},
     "articleSection":%s,
     "inLanguage":"en"},
    {"@type":"BreadcrumbList","itemListElement":[
      {"@type":"ListItem","position":1,"name":"Home","item":"https://aiprofitlab.io/"},
      {"@type":"ListItem","position":2,"name":"Articles","item":"https://aiprofitlab.io/blog/"},
      {"@type":"ListItem","position":3,"name":%s,"item":"%s"}
    ]}%s
  ]
}""" % (_json(art["title"]), _json(art["dek"]), art["image"], art["iso"],
        art.get("iso_updated", art["iso"]), url, _json(art["cat"]),
        _json(art["title"]), url, faq)


def _json(s):
    """Strip markup and quote a string for embedding in JSON-LD."""
    s = re.sub(r"<[^>]+>", "", s)
    s = (s.replace("&mdash;", "\u2014").replace("&amp;", "&").replace("&middot;", "\u00b7")
          .replace("&rarr;", "\u2192").replace("&times;", "\u00d7").replace("&nbsp;", " "))
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"'
