#!/usr/bin/env python3
"""
Ship the price table to the checkout server.

pay.py is the one place that knows what is sold and what it costs, and it
already serialises that table to the browser rather than letting JavaScript
restate it (see pay.CONFIG_JSON). The server that creates Thawani sessions has
to re-price every order from its own copy - it must never charge the number the
browser sent - so it needs the same table, and the same reasoning applies: the
arithmetic is ported, the numbers are transported.

Output is deterministic. No timestamp, no build id: catalog.json only changes
when a price changes, so a diff on it always means something.

Run by build_v4.py; also runnable on its own:

    python3 tools/v4/export_catalog.py
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))

import pay  # noqa: E402

DEST = ROOT / "backend" / "checkout-api" / "catalog.json"


def catalog():
    """The English config, minus the two fields that are about the browser.

    `live` and `api` tell the PAGE whether to offer a card and where to post;
    the server is the thing being pointed at, and reads its own environment.
    Shipping them would invite someone to branch on them server-side."""
    c = pay.config("en")
    for browser_only in ("live", "api", "env"):
        c.pop(browser_only, None)
    # Thawani truncates a product name at 40 characters. The check lives in
    # pay.py at build time; the server needs the number to build the composed
    # line items ("First of 3 payments") that no build-time check ever sees.
    c["name_max"] = pay.THAWANI_NAME_MAX
    return c


def write():
    text = json.dumps(catalog(), indent=2, ensure_ascii=False) + "\n"
    before = DEST.read_text(encoding="utf-8") if DEST.exists() else None
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(text, encoding="utf-8")
    return DEST, before != text


if __name__ == "__main__":
    dest, changed = write()
    rel = dest.relative_to(ROOT)
    print(f"  {'ok ' if not changed else 'NEW'} {rel}"
          + ("" if not changed else "  (prices changed - redeploy checkout-api)"))
