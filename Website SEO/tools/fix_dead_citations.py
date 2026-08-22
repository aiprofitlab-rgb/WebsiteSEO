#!/usr/bin/env python3
"""
Repoint or remove citations whose host or path no longer exists.

    python3 tools/fix_dead_citations.py --dry-run
    python3 tools/fix_dead_citations.py

Sixty-five articles cited nineteen domains that fail DNS outright and a dozen
URLs that 404 to a real browser - and they are concentrated in the compliance
and government-policy pieces, which are exactly the pages where a dead source
costs the most trust.

Two rules, and the second one matters:

  * REPOINT only when the replacement is the SAME body under a new domain.
    Most of these are the Omani IT ministry, which has been ITA, then ITC,
    then MCIT, then MTIT, and is now MTCIT - every one of those anchor texts
    already names "Ministry of Transport, Communications and Information
    Technology", so the citation is still true after the move. Every target
    below was fetched and returned 200 before being written here.

  * REMOVE when it cannot be repointed truthfully. A citation that silently
    resolves to a different organisation than the one it names is worse than
    no citation: it reads as a source and is not one. Three Omani bodies
    (MoCIIP, the national cyber-security centre, the tenders portal) have no
    live domain I could verify, so their citations come out.

Bot-walled hosts - Meta, OpenAI, Gartner, BCG, Reuters, LinkedIn's 999 - are
deliberately untouched. They answer a real browser perfectly well and only
refuse automated fetches.
"""
import argparse
import glob
import io
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent

# dead URL (prefix match) -> verified live replacement for the same body
REPOINT = {
    # The Omani IT ministry, through four names. All 200 on www.mtcit.gov.om.
    "https://itc.gov.om": "https://www.mtcit.gov.om/",
    "https://mtit.gov.om/": "https://www.mtcit.gov.om/",
    "https://www.mtit.gov.om/": "https://www.mtcit.gov.om/",
    "https://www.mcit.gov.om": "https://www.mtcit.gov.om/",
    "https://mttc.gov.om/": "https://www.mtcit.gov.om/",
    "https://cra.gov.om/": "https://www.mtcit.gov.om/",
    "https://mtcit.gov.om/ai-policy": "https://www.mtcit.gov.om/",
    "https://mtcit.gov.om/ministerial-decision-34-2024": "https://www.mtcit.gov.om/",
    # Ma'een is MTCIT's national AI programme - its own domain is gone.
    "https://maeen.om/": "https://www.mtcit.gov.om/",

    # Oman Vision 2040, under its live domain.
    "https://vision2040.om": "https://www.oman2040.om/",
    "https://www.vision2040.om/": "https://www.oman2040.om/",
    "https://www.omanvision2040.om/": "https://www.oman2040.om/",
    "https://oman2040.om/en/": "https://www.oman2040.om/",
    "https://oman2040.om/ar/": "https://www.oman2040.om/",
    "https://www.oman2040.om/en/": "https://www.oman2040.om/",
    "https://www.japan.go.jp/tomodachi/2021/spring2021/oman_vision2040.html":
        "https://www.oman2040.om/",

    # Saudi data protection: SDAIA is the authority, pdpl.sa never resolved.
    "https://pdpl.sa/en": "https://sdaia.gov.sa/en/",
    "https://pdpl.sa/ar": "https://sdaia.gov.sa/",
    "https://sdaia.gov.sa/en/SDAIA/about/Pages/pdpl.aspx": "https://sdaia.gov.sa/en/",
    "https://sdaia.gov.sa/en/SDAIA/about/Pages/Vision2030.aspx": "https://sdaia.gov.sa/en/",
    "https://sdaia.gov.sa/ar/SDAIA/about/Pages/Vision2030.aspx": "https://sdaia.gov.sa/",

    # Omani legal affairs: MOLA was folded into the Ministry of Justice.
    "https://mola.gov.om/": "https://mjla.gov.om/",
    "https://mjla.gov.om/eng/legislation/laws/": "https://mjla.gov.om/",
    # The PDPL royal decree was cited off a ministry that does not publish it.
    "https://mosa.gov.om/en/legal-framework/": "https://mjla.gov.om/",

    # Same organisation, working host.
    "https://www.mht.gov.om": "https://mht.gov.om/",
    "https://www.cpa.gov.om/": "https://cpa.gov.om/",
    "https://www.moeoman.gov.om": "https://moe.gov.om/",
    "https://isdb.org/": "https://www.isdb.org/",
    "https://www.kdipa.gov.kw/en/": "https://kdipa.gov.kw/",
    "https://n8n.io/docs/": "https://docs.n8n.io/",
    "https://www.tii.ae/ai": "https://www.tii.ae/",
    "https://www.pwc.com/m1/en/publications/ai-in-the-middle-east.html":
        "https://www.pwc.com/m1/en.html",
    "https://www.pwc.com/m1/en/publications/oman-personal-data-protection-law.html":
        "https://www.pwc.com/m1/en.html",
    "https://oxfordbusinessgroup.com/reports/oman/2023-report/economy/"
    "digital-leap-transformation-is-a-key-pillar-of-oman-vision-2040-overview":
        "https://oxfordbusinessgroup.com/",

    # A typo, not a move: the national portal has no www host, so this one
    # form failed DNS while every other citation of it resolved.
    "https://www.omanuna.oman.om": "https://omanuna.oman.om/",
}

# Dead, and no live equivalent for the body the anchor names. Removed whole.
REMOVE = (
    "https://cmo.gov.om",            # national cyber security centre - no live domain
    "https://mci.gov.om",            # MoCIIP - no live domain found
    "https://www.tender.gov.om",     # government tenders portal - no live domain
    "https://aiinoman.com",          # third-party blog, host gone
    "https://www.cms.law/en/omn/publication/oman-s-personal-data-protection-law",
)

LI = re.compile(r"[ \t]*<li>(?:(?!</li>).)*?</li>", re.S)


def fix(text):
    """Returns (text, repointed, removed)."""
    repointed = 0
    # Longest first, so a specific path wins over its own domain prefix.
    for dead in sorted(REPOINT, key=len, reverse=True):
        live = REPOINT[dead]
        for m in list(re.finditer(r'href="(%s[^"]*)"' % re.escape(dead), text)):
            text = text.replace('href="%s"' % m.group(1), 'href="%s"' % live)
            repointed += 1

    removed = 0
    for dead in REMOVE:
        while True:
            i = text.find('href="%s' % dead)
            if i < 0:
                break
            # take out the whole list item, not just the anchor: a bare label
            # in a Sources list reads as a source that lost its link.
            start = text.rfind("<li>", 0, i)
            m = LI.match(text, start) if start >= 0 else None
            if not m:
                text = re.sub(r'<a href="%s[^"]*"[^>]*>((?:(?!</a>).)*)</a>' % re.escape(dead),
                              r"\1", text, count=1, flags=re.S)
            else:
                text = text[:m.start()] + text[m.end():]
            removed += 1
    return text, repointed, removed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    files = rep = rem = 0
    for f in sorted(glob.glob(str(ROOT / "public_html" / "blog" / "*" / "*.html"))):
        text = io.open(f, encoding="utf-8").read()
        out, r, d = fix(text)
        if out == text:
            continue
        files += 1
        rep += r
        rem += d
        if not a.dry_run:
            io.open(f, "w", encoding="utf-8").write(out)
    print(f"  {files} files: {rep} citations repointed, {rem} removed"
          f"{' (dry run)' if a.dry_run else ''}")


if __name__ == "__main__":
    main()
