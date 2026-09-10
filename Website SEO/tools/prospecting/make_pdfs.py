#!/usr/bin/env python3
"""Render the outreach kit to PDFs on the Desktop.

No markdown library is installed on this machine and none is needed: the
documents use a known subset (headings, tables, blockquotes, lists, fences,
checkboxes), so a small converter is more honest than a dependency.

Chrome headless does the printing. Two gotchas it hides from you:
  * without --virtual-time-budget it prints before webfonts and layout settle;
  * its default header/footer stamps a file:// path across every page.

Usage:
  python3 tools/prospecting/make_pdfs.py --leads 1000
"""
import argparse
import csv
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
DESKTOP = os.path.expanduser("~/Desktop")

CSS = """
@page { size: A4; margin: 16mm 14mm; }
@page :first { margin-top: 20mm; }
body { font: 10.5pt/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
       color: #14181d; margin: 0; }
h1 { font-size: 21pt; letter-spacing: -.02em; margin: 0 0 .5rem; }
h2 { font-size: 14pt; margin: 1.5rem 0 .5rem; padding-top: .6rem;
     border-top: 2px solid #0b7a6b; color: #0b5c51; break-after: avoid; }
h3 { font-size: 11.5pt; margin: 1rem 0 .3rem; break-after: avoid; }
p, li { orphans: 3; widows: 3; }
table { border-collapse: collapse; width: 100%; margin: .7rem 0; font-size: 9.5pt;
        break-inside: auto; }
th, td { border: 1px solid #d5dce3; padding: 5px 7px; text-align: left;
         vertical-align: top; }
th { background: #eef4f3; font-weight: 600; }
tr { break-inside: avoid; }
blockquote { margin: .45rem 0; padding: .5rem .8rem; background: #f6f9f8;
             border-left: 3px solid #0b7a6b; break-inside: avoid; }
blockquote p { margin: 0; }
code { background: #eef1f4; padding: 1px 4px; border-radius: 3px; font-size: 9pt; }
pre { background: #14181d; color: #e8eef2; padding: .7rem .9rem; border-radius: 6px;
      font-size: 8.8pt; overflow-wrap: break-word; white-space: pre-wrap;
      break-inside: avoid; }
pre code { background: none; color: inherit; padding: 0; }
hr { border: 0; border-top: 1px solid #d5dce3; margin: 1.1rem 0; }
.card { break-inside: avoid; page-break-inside: avoid; }
.meta { color: #5b6875; font-size: 9pt; }
.warn { background: #fff4e5; border: 1px solid #f0c07a; padding: .6rem .8rem;
        border-radius: 6px; }
a { color: #0b5c51; text-decoration: none; }
"""


def inline(t):
    t = html.escape(t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![*\w])\*([^*\n]+)\*(?!\w)", r"<em>\1</em>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', t)
    t = re.sub(r"&lt;(https?://[^&]+)&gt;", r'<a href="\1">\1</a>', t)
    t = t.replace("- [ ]", "☐").replace("- [x]", "☑")
    return t


def md2html(md, title):
    out, i, lines = [], 0, md.split("\n")
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("```"):
            i += 1
            buf = []
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(html.escape(lines[i]))
                i += 1
            out.append("<pre><code>" + "\n".join(buf) + "</code></pre>")
            i += 1
            continue
        if re.match(r"^\|.*\|\s*$", ln) and i + 1 < len(lines) \
                and re.match(r"^\|[\s:|-]+\|\s*$", lines[i + 1]):
            head = [c.strip() for c in ln.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and re.match(r"^\|.*\|\s*$", lines[i]):
                rows.append([c.strip() for c in
                             lines[i].strip().strip("|").split("|")])
                i += 1
            out.append("<table><thead><tr>"
                       + "".join(f"<th>{inline(c)}</th>" for c in head)
                       + "</tr></thead><tbody>"
                       + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>"
                                                  for c in r) + "</tr>"
                                 for r in rows)
                       + "</tbody></table>")
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", ln)
        if m:
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
            i += 1
            continue
        if ln.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i].lstrip("> ").rstrip())
                i += 1
            cls = ' class="warn"' if any("⚠" in b for b in buf) else ""
            out.append(f"<blockquote{cls}><p>"
                       + "<br>".join(inline(b) for b in buf if b)
                       + "</p></blockquote>")
            continue
        if re.match(r"^\s*[-*]\s+", ln) or re.match(r"^\s*\d+\.\s+", ln):
            ordered = bool(re.match(r"^\s*\d+\.\s+", ln))
            tag = "ol" if ordered else "ul"
            items = []
            while i < len(lines) and (re.match(r"^\s*[-*]\s+", lines[i])
                                      or re.match(r"^\s*\d+\.\s+", lines[i])):
                items.append(inline(re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "",
                                           lines[i])))
                i += 1
            out.append(f"<{tag}>" + "".join(f"<li>{x}</li>" for x in items)
                       + f"</{tag}>")
            continue
        if re.match(r"^---+\s*$", ln):
            out.append("<hr>")
            i += 1
            continue
        if ln.strip():
            buf = []
            while i < len(lines) and lines[i].strip() \
                    and not re.match(r"^(#{1,4}\s|>|```|\||\s*[-*]\s|\s*\d+\.\s|---+\s*$)",
                                     lines[i]):
                buf.append(lines[i].strip())
                i += 1
            out.append("<p>" + inline(" ".join(buf)) + "</p>")
            continue
        i += 1
    return (f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<title>{html.escape(title)}</title><style>{CSS}</style></head>"
            f"<body>{''.join(out)}</body></html>")


def leads_html(path, limit):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))

    def rank(d):
        enriched = 1 if d.get("site_status") or d.get("ig_followers") else 0
        tier = {"Dental clinic": 0, "Medical clinic": 0, "Law firm": 0,
                "Private school": 0, "Real estate": 0}.get(d.get("category"), 1)
        return (-enriched, tier, 0 if d.get("phone_kind") == "mobile" else 1,
                (d.get("business") or "").lower())

    rows.sort(key=rank)
    sel = rows[:limit]
    tr = "".join(
        "<tr>"
        f"<td>{i}</td><td>{html.escape(r['business'][:46])}</td>"
        f"<td>{html.escape((r.get('category') or '')[:20])}</td>"
        f"<td>{html.escape(r.get('city') or '')}</td>"
        f"<td>{html.escape(r.get('phone_e164') or '')}</td>"
        f"<td>{html.escape(r.get('segment') or '')}</td>"
        f"<td>{html.escape((r.get('ig_followers') or '')[:8])}</td>"
        "<td></td><td></td></tr>"
        for i, r in enumerate(sel, 1))
    return (f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<title>Lead list</title><style>{CSS}"
            "@page{size:A4 landscape;margin:12mm}"
            "td,th{font-size:8.4pt;padding:3px 5px}"
            "</style></head><body>"
            f"<h1>Lead list — top {len(sel)}</h1>"
            f"<p class='meta'>Sorted best-first: enriched rows, then "
            f"high-ticket trades, then mobile numbers. The full "
            f"{len(rows):,}-lead file stays as CSV — as a PDF it would run to "
            f"hundreds of pages.</p>"
            "<table><thead><tr><th>#</th><th>Business</th><th>Trade</th>"
            "<th>Town</th><th>Phone</th><th>Sit.</th><th>IG</th>"
            "<th>Called</th><th>Outcome</th></tr></thead>"
            f"<tbody>{tr}</tbody></table></body></html>")


def to_pdf(html_str, out_pdf, tmpdir):
    src = os.path.join(tmpdir, os.path.basename(out_pdf) + ".html")
    open(src, "w", encoding="utf-8").write(html_str)
    r = subprocess.run(
        [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
         "--no-pdf-header-footer", "--virtual-time-budget=12000",
         f"--print-to-pdf={out_pdf}", "file://" + src],
        capture_output=True, text=True, timeout=300)
    if not os.path.exists(out_pdf):
        print(r.stderr[-600:], file=sys.stderr)
        return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=os.path.join(DESKTOP, "AI Profit Lab - Outreach Kit"))
    ap.add_argument("--src", default="out/outreach")
    ap.add_argument("--leads", type=int, default=1000)
    a = ap.parse_args()

    if not os.path.exists(CHROME):
        sys.exit("Google Chrome not found; cannot render PDFs.")
    os.makedirs(a.outdir, exist_ok=True)
    tmp = tempfile.mkdtemp()
    made = []

    docs = [("START-HERE.md", "1 - START HERE - How to use this.pdf", "How to use this kit"),
            ("call-cards.md", "2 - Call cards - your 200 best calls.pdf", "Call cards"),
            ("PLAYBOOK.md", "3 - Playbook - rules, timing, objections.pdf", "Playbook")]
    for fn, out, title in docs:
        p = os.path.join(a.src, fn)
        if not os.path.exists(p):
            print(f"  skip (missing): {fn}")
            continue
        dest = os.path.join(a.outdir, out)
        if to_pdf(md2html(open(p, encoding="utf-8").read(), title), dest, tmp):
            made.append(dest)
            print(f"  ok  {out}")

    lp = os.path.join(a.src, "outreach-scripts.csv")
    if os.path.exists(lp):
        dest = os.path.join(a.outdir, f"4 - Lead list - top {a.leads}.pdf")
        if to_pdf(leads_html(lp, a.leads), dest, tmp):
            made.append(dest)
            print(f"  ok  {os.path.basename(dest)}")
        # The full list travels as CSV: a PDF of 20,000 rows helps nobody.
        shutil.copy(lp, os.path.join(a.outdir, "FULL LEAD LIST (all 20k).csv"))
        print("  ok  FULL LEAD LIST (all 20k).csv")

    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{len(made)} PDFs -> {a.outdir}")
    for m in made:
        print(f"   {os.path.getsize(m)/1024:>7.0f} KB  {os.path.basename(m)}")


if __name__ == "__main__":
    main()
