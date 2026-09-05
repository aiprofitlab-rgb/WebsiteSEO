#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render the Arabic review page from pay_ar_strings.py.

Generated, never hand-edited, so the page a reviewer reads and the table the
build uses cannot drift apart. Re-run after editing any Arabic.

    python3 tools/build_pay_ar_review.py
"""
import html
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pay_ar_strings as S  # noqa: E402

OUT = HERE.parent / "build" / "pay-ar-review.html"

# Groups a reviewer actually thinks in, rather than "HTML" and "JS".
#
# Keyed off the sections of pay_ar_strings.py rather than off key prefixes. The
# prefix version quietly dropped a sentence out of the review every time a key
# was renamed - the page still built, the reviewer simply never saw the line.
_HTML = {k for k, *_ in S.HTML}
_ERR = {k for k, *_ in S.JS if k.startswith("err_")}
_UPSELL = {k for k, *_ in S.UPSELL}
GROUPS = [
    ("ما يقرأه الزائر على الصفحة", "What the visitor reads on the page",
     lambda k: k in _HTML),
    ("رسائل الخطأ", "Error messages — nobody is blamed, and money is always accounted for",
     lambda k: k in _ERR),
    ("ما تقوله الصفحة أثناء عملها", "What the page says as it works — status, progress, "
     "and the sentences only the script ever shows",
     lambda k: k not in _HTML and k not in _ERR and k not in _UPSELL),
    ("عرض مكتب الظهور", "The Visibility Desk offer, where it touches this page. The "
     "interstitial itself is already-reviewed Arabic and is not repeated here.",
     lambda k: k in _UPSELL),
]

CSS = """
:root{
  --ground:#F6F4EE; --panel:#FFFFFF; --panel-2:#EFEBE0;
  --ink:#1F2A25; --muted:#5E6B62; --faint:#8A9389;
  --line:#DFD9C9; --teal:#0F6E56; --teal-deep:#0A3D30; --amber:#BA7517;
  --shadow:0 1px 2px rgba(10,61,48,.05), 0 8px 24px -16px rgba(10,61,48,.25);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --ground:#0C1512; --panel:#121E1A; --panel-2:#182721;
    --ink:#E8EDE8; --muted:#9AA79E; --faint:#6E7C73;
    --line:#22322B; --teal:#4FBF9B; --teal-deep:#8FD9C0; --amber:#E0A445;
    --shadow:0 1px 2px rgba(0,0,0,.4), 0 8px 24px -16px rgba(0,0,0,.8);
  }
}
:root[data-theme="dark"]{
  --ground:#0C1512; --panel:#121E1A; --panel-2:#182721;
  --ink:#E8EDE8; --muted:#9AA79E; --faint:#6E7C73;
  --line:#22322B; --teal:#4FBF9B; --teal-deep:#8FD9C0; --amber:#E0A445;
  --shadow:0 1px 2px rgba(0,0,0,.4), 0 8px 24px -16px rgba(0,0,0,.8);
}

*{box-sizing:border-box}
body{
  margin:0; background:var(--ground); color:var(--ink);
  font-family:'IBM Plex Sans','IBM Plex Sans Arabic',-apple-system,BlinkMacSystemFont,sans-serif;
  font-size:16px; line-height:1.6;
  -webkit-font-smoothing:antialiased;
}
.wrap{max-width:60rem; margin:0 auto; padding:2.5rem 1.25rem 6rem}

/* ---- header ---- */
header{border-bottom:2px solid var(--line); padding-bottom:1.75rem; margin-bottom:2.5rem}
.eyebrow{
  font-family:'IBM Plex Mono',ui-monospace,monospace;
  font-size:.7rem; letter-spacing:.14em; text-transform:uppercase;
  color:var(--teal); margin:0 0 .75rem;
}
h1{
  font-family:'Markazi Text','IBM Plex Sans Arabic',Georgia,serif;
  font-size:clamp(2.2rem,6vw,3.4rem); line-height:1.1; font-weight:600;
  margin:0 0 .5rem; text-wrap:balance; color:var(--teal-deep);
}
.lede{font-size:1.06rem; color:var(--muted); max-width:34rem; margin:0}

/* ---- counters ---- */
.tally{display:flex; flex-wrap:wrap; gap:.5rem; margin:1.5rem 0 0; padding:0; list-style:none}
.tally li{
  background:var(--panel); border:1px solid var(--line); border-radius:2px;
  padding:.5rem .75rem; font-size:.8rem; color:var(--muted);
  display:flex; gap:.5rem; align-items:baseline;
}
.tally b{
  font-family:'IBM Plex Mono',ui-monospace,monospace; font-size:1rem;
  color:var(--ink); font-variant-numeric:tabular-nums; font-weight:600;
}

/* ---- how-to ---- */
.howto{
  background:var(--panel); border:1px solid var(--line); border-inline-start:3px solid var(--teal);
  padding:1.25rem 1.4rem; margin:2rem 0 0; border-radius:2px; box-shadow:var(--shadow);
}
.howto h2{font-size:.95rem; margin:0 0 .6rem; letter-spacing:.01em}
.howto p{margin:0 0 .5rem; color:var(--muted); font-size:.94rem}
.howto p:last-child{margin-bottom:0}

/* ---- decisions ---- */
.decisions{margin:2.5rem 0 0}
.decisions h2{
  font-family:'Markazi Text',Georgia,serif; font-size:1.7rem; font-weight:600;
  color:var(--teal-deep); margin:0 0 .25rem;
}
.decisions > p{color:var(--muted); font-size:.94rem; margin:0 0 1rem}
.decision{
  background:var(--panel); border:1px solid var(--line);
  border-inline-start:3px solid var(--amber);
  padding:1.1rem 1.3rem; border-radius:2px; margin-bottom:.75rem; box-shadow:var(--shadow);
}
.decision p{margin:0; font-size:.94rem}
.decision .q{
  font-family:'IBM Plex Mono',ui-monospace,monospace; font-size:.68rem;
  letter-spacing:.12em; text-transform:uppercase; color:var(--amber);
  display:block; margin-bottom:.4rem;
}

/* ---- tone reference ---- */
.tone{margin:3rem 0 0}
.tone h2{
  font-family:'Markazi Text',Georgia,serif; font-size:1.7rem; font-weight:600;
  color:var(--teal-deep); margin:0 0 .25rem;
}
.tone > p{color:var(--muted); font-size:.94rem; margin:0 0 1rem; max-width:38rem}
.ref{
  display:grid; gap:.4rem 1.5rem; padding:.85rem 0;
  border-bottom:1px dashed var(--line);
}
.ref:last-child{border-bottom:0}
.ref .ar{
  font-family:'IBM Plex Sans Arabic','Noto Naskh Arabic',sans-serif;
  direction:rtl; text-align:right; unicode-bidi:isolate;
  font-size:1.06rem; color:var(--ink);
}
.ref .en{font-size:.82rem; color:var(--faint); direction:ltr; text-align:left; unicode-bidi:isolate}

/* ---- the pairs ---- */
section.group{margin:3.5rem 0 0}
section.group > h2{
  font-family:'Markazi Text','IBM Plex Sans Arabic',Georgia,serif;
  direction:rtl; text-align:right; unicode-bidi:isolate;
  font-size:2rem; font-weight:600; color:var(--teal-deep);
  margin:0 0 .2rem; padding-bottom:.5rem; border-bottom:2px solid var(--line);
}
section.group > p.sub{
  font-size:.85rem; color:var(--faint); margin:.5rem 0 1.5rem;
  direction:ltr; text-align:left;
}

.item{
  display:grid; grid-template-columns:2.5rem 1fr; gap:.15rem 1rem;
  background:var(--panel); border:1px solid var(--line); border-radius:2px;
  padding:1.1rem 1.25rem; margin-bottom:.6rem; box-shadow:var(--shadow);
}
.item .n{
  grid-row:1 / span 3;
  font-family:'IBM Plex Mono',ui-monospace,monospace;
  font-size:.95rem; font-variant-numeric:tabular-nums;
  color:var(--amber); font-weight:600; padding-top:.15rem;
}
.item .key{
  font-family:'IBM Plex Mono',ui-monospace,monospace; font-size:.66rem;
  letter-spacing:.06em; color:var(--faint); direction:ltr; text-align:left;
  unicode-bidi:isolate;
}
.item .en{
  font-size:.88rem; color:var(--muted); direction:ltr; text-align:left;
  unicode-bidi:isolate; margin:.15rem 0 .5rem;
}
.item .ar{
  font-family:'IBM Plex Sans Arabic','Noto Naskh Arabic',sans-serif;
  direction:rtl; text-align:right; unicode-bidi:isolate;
  font-size:1.22rem; line-height:1.85; color:var(--ink);
  padding-top:.5rem; border-top:1px solid var(--line);
}

footer{
  margin-top:4rem; padding-top:1.5rem; border-top:2px solid var(--line);
  font-size:.82rem; color:var(--faint);
}
footer .ltr{direction:ltr; unicode-bidi:isolate; display:inline-block}

@media (max-width:34rem){
  .wrap{padding:1.75rem 1rem 4rem}
  .item{grid-template-columns:2rem 1fr; padding:1rem}
  .item .ar{font-size:1.14rem}
}
@media (prefers-reduced-motion:no-preference){
  .item{transition:border-color .15s ease}
}
.item:hover{border-color:var(--teal)}
"""


def esc(t):
    return html.escape(t, quote=False)


def build():
    new = S.review_list()
    st = S.stats()
    keyed = {k: (en, ar) for k, en, ar in new}

    parts = []
    n = 0
    used = set()
    for ar_title, en_title, belongs in GROUPS:
        rows = [(k, en, ar) for k, en, ar in new if belongs(k) and k not in used]
        if not rows:
            continue
        used.update(k for k, _, _ in rows)
        parts.append('<section class="group">')
        parts.append(f"  <h2>{esc(ar_title)}</h2>")
        parts.append(f'  <p class="sub">{esc(en_title)}</p>')
        for k, en, ar in rows:
            n += 1
            parts.append(
                '  <div class="item">'
                f'<div class="n">{n:02d}</div>'
                f'<div class="key">{esc(k)}</div>'
                f'<div class="en">{esc(en)}</div>'
                f'<div class="ar">{esc(ar)}</div>'
                "</div>"
            )
        parts.append("</section>")

    leftover = [(k, en, ar) for k, en, ar in new if k not in used]
    if leftover:
        parts.append('<section class="group"><h2>أخرى</h2><p class="sub">Uncategorised</p>')
        for k, en, ar in leftover:
            n += 1
            parts.append(
                '  <div class="item">'
                f'<div class="n">{n:02d}</div>'
                f'<div class="key">{esc(k)}</div>'
                f'<div class="en">{esc(en)}</div>'
                f'<div class="ar">{esc(ar)}</div>'
                "</div>"
            )
        parts.append("</section>")

    tone = "\n".join(
        f'    <div class="ref"><div class="ar">{esc(ar)}</div>'
        f'<div class="en">{esc(en)}</div></div>'
        for k, en, ar, src in S.harvested()[:6]
    )

    decisions = "\n".join(
        f'    <div class="decision"><span class="q">Decision {i}</span><p>{esc(q)}</p></div>'
        for i, q in enumerate(S.OPEN_QUESTIONS, 1)
    )

    return f"""<title>Seat Page Arabic Review</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Markazi+Text:wght@500;600&family=IBM+Plex+Sans+Arabic:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>{CSS}</style>

<div class="wrap">
<header>
  <p class="eyebrow">AI Profit Lab · صفحة حجز المقعد</p>
  <h1>مراجعة النصوص العربية</h1>
  <p class="lede">These {st['new']} sentences are new. Nobody has read them but the machine that wrote them.</p>
  <ul class="tally">
    <li><b>{st['new']}</b> new, need you</li>
    <li><b>{st['harvested']}</b> already yours</li>
    <li><b>{st['total']}</b> strings on the page in total</li>
  </ul>
</header>

<div class="howto">
  <h2>What to do</h2>
  <p>Read the Arabic. Where it is wrong, stiff, or not how a person would say it, write the better version and quote the number beside it — “item 14 should be …”. That is all that is needed; nothing has to be edited in place.</p>
  <p>The English above each line is what the sentence has to mean, not a text to translate literally. If natural Arabic says it differently, natural Arabic wins.</p>
</div>

<div class="decisions">
  <h2>ثلاثة قرارات</h2>
  <p>Three things deliberately left open, because they are judgement calls rather than mistakes.</p>
{decisions}
</div>

<div class="tone">
  <h2>النبرة المعتمدة</h2>
  <p>Your own reviewed lines, already live on the site. The new sentences were written to sit beside these — if any of them reads in a different voice, that is the bug.</p>
{tone}
</div>

{chr(10).join(parts)}

<footer>
  <p>Generated from <span class="ltr">tools/pay_ar_strings.py</span> · the seat-claim page at <span class="ltr">/pay-ar/</span> · first person singular throughout, never the corporate plural.</p>
</footer>
</div>
"""


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    page = build()
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT}  ({len(page):,} bytes, {S.stats()['new']} items)")
