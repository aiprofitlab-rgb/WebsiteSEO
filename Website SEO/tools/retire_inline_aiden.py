#!/usr/bin/env python3
"""
Retire the hand-written Aiden markup from the ten pages that still ship it.

Home / services / process / about / contact (EN + AR) each carry a copy of the
2026 chat widget in their own HTML, plus a loader that only fetches
/js/aiden-chat.js on click or after a ten-second timer. The consequence was a
visible seam: the old blue launcher sat in the corner for up to ten seconds,
then aiden-chat.js replaced it with the current one.

This removes the inline block and lets the widget mount itself like it does on
every other page. What is removed:

  * <div class="fixed bottom-8 …-8 z-[10005]"> … </div>  - launcher + panel
  * let chatLoading / window.toggleChat / window.handleSend lazy-load plumbing
  * the 10-second setTimeout that loaded the script

What replaces it: a plain deferred <script> tag, and two one-line shims for
toggleChat / handleSend so any stray caller keeps working.

The dead `#aiden-ui` CSS rules are deliberately left alone: nothing in the
document carries that id any more, so they are inert, and editing ten differently
formatted <style> blocks buys nothing.

    python3 tools/retire_inline_aiden.py --dry-run
    python3 tools/retire_inline_aiden.py
"""
import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC = os.path.join(ROOT, "public_html")

PAGES = [
    "index.html", "en/index.html",
    "services.html", "services-en.html",
    "process.html", "process-en.html",
    "about.html", "about-en.html",
    "contact.html", "contact-en.html",
]

WIDGET_OPEN = re.compile(r'<!--[^\n]*Chatbot Widget[^\n]*-->\s*\n?\s*'
                         r'(?P<div><div class="fixed bottom-8 (?:left|right)-8 z-\[10005\]">)'
                         r'|(?P<bare><div class="fixed bottom-8 (?:left|right)-8 z-\[10005\]">)')

TAG = '<script defer src="/js/aiden-chat.js"></script>'

SHIMS = """        // Aiden mounts itself from /js/aiden-chat.js, loaded at the end of this
        // page. These shims remain only so any stray caller keeps working.
        window.toggleChat = function () { if (window.aidenChat) window.aidenChat.toggle(); };
        window.handleSend = function () { if (window.aidenChat) window.aidenChat.send(); };
"""


def match_block(html, start, open_tag, close_tag):
    """End index of the tag opened at `start`, counting nested opens."""
    depth = 0
    i = start
    while i < len(html):
        if html.startswith(open_tag, i):
            depth += 1
            i += len(open_tag)
        elif html.startswith(close_tag, i):
            depth -= 1
            i += len(close_tag)
            if depth == 0:
                return i
        else:
            i += 1
    return -1


def match_parens(html, start):
    """End index (past the closing paren) of the call opened at or after `start`."""
    open_at = html.find("(", start)
    if open_at < 0:
        return -1
    depth = 0
    for i in range(open_at, len(html)):
        if html[i] == "(":
            depth += 1
        elif html[i] == ")":
            depth -= 1
            if depth == 0:
                return i + 1
    return -1


def match_braces(html, start):
    """End index (past the closing brace) of the first {...} at or after `start`."""
    open_at = html.find("{", start)
    if open_at < 0:
        return -1
    depth = 0
    for i in range(open_at, len(html)):
        if html[i] == "{":
            depth += 1
        elif html[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
    return -1


def drop_statement(html, needle):
    """Remove `needle … { … };` including a trailing semicolon and blank line."""
    start = html.find(needle)
    if start < 0:
        return html, False
    end = match_braces(html, start)
    if end < 0:
        return html, False
    while end < len(html) and html[end] in ");":
        end += 1
    # take the whole line, indentation included
    line_start = html.rfind("\n", 0, start) + 1
    if end < len(html) and html[end] == "\n":
        end += 1
    return html[:line_start] + html[end:], True


def strip_widget_markup(html):
    m = WIDGET_OPEN.search(html)
    if not m:
        return html, False
    div_start = m.start("div") if m.group("div") else m.start("bare")
    end = match_block(html, div_start, "<div", "</div>")
    if end < 0:
        return html, False
    if end < len(html) and html[end] == "\n":
        end += 1
    return html[:m.start()] + html[end:], True


def convert(html):
    notes = []

    html, ok = strip_widget_markup(html)
    notes.append("markup" if ok else "MARKUP NOT FOUND")

    html, ok = drop_statement(html, "window.toggleChat = function")
    notes.append("toggleChat" if ok else "toggleChat NOT FOUND")

    html, ok = drop_statement(html, "window.handleSend = function")
    notes.append("handleSend" if ok else "handleSend NOT FOUND")

    # The 10-second lazy loader, identified by its own call rather than by the
    # comment above it, which is not present on every page.
    idx = html.find("if (!chatLoading && !window.aidenChat)")
    if idx >= 0:
        start = html.rfind("setTimeout(", 0, idx)
        if start >= 0:
            line_start = html.rfind("\n", 0, start) + 1
            # a comment line directly above belongs to the block
            prev_start = html.rfind("\n", 0, line_start - 1) + 1
            if html[prev_start:line_start].strip().startswith("//"):
                line_start = prev_start
            end = match_parens(html, start)
            if end < 0:
                notes.append("timer UNBALANCED - NOT FOUND")
                end = None
            else:
                while end < len(html) and html[end] == ";":
                    end += 1
                if end < len(html) and html[end] == "\n":
                    end += 1
                html = html[:line_start] + html[end:]
                notes.append("timer")
    else:
        notes.append("timer NOT FOUND")

    html = re.sub(r"[ \t]*let chatLoading = false;\n", "", html)

    # Shims go where the removed functions were: at the top of the same loader
    # block, right after the loadScript helper the other lazy loads still use.
    anchor = html.find("        let formLoading = false;")
    if anchor >= 0:
        html = html[:anchor] + SHIMS + html[anchor:]
        notes.append("shims")
    else:
        notes.append("SHIM ANCHOR NOT FOUND")

    # Look for the tag, not the bare path: the shim comment above mentions the
    # file by name and would otherwise read as "already linked".
    if 'src="/js/aiden-chat.js"' not in html:
        head, sep, tail = html.rpartition("</body>")
        html = head + "    " + TAG + "\n" + sep + tail
        notes.append("script tag")
    else:
        notes.append("SCRIPT TAG ALREADY PRESENT")

    return html, notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    failed = False
    for rel in PAGES:
        full = os.path.join(PUBLIC, rel)
        html = open(full, encoding="utf-8").read()
        if 'id="aiden-ui"' not in html:
            print(f"  -- {rel}: already retired")
            continue
        out, notes = convert(html)
        bad = [n for n in notes if "NOT FOUND" in n or "ALREADY" in n]
        if bad:
            failed = True
        print(f"  {'!!' if bad else 'ok'} {rel}: {', '.join(notes)}")
        if not args.dry_run and not bad:
            with open(full, "w", encoding="utf-8") as fh:
                fh.write(out)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
