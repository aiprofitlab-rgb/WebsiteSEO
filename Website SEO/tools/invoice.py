#!/usr/bin/env python3
"""Issue one invoice: fill invoices/template.html from a customer JSON, print a PDF.

    python3 tools/invoice.py invoices/customers/acme.json         # issue, PDF only
    python3 tools/invoice.py invoices/customers/acme.json --send  # issue AND email it
    python3 tools/invoice.py invoices/customers/acme.json --dry   # preview, no number burnt
    python3 tools/invoice.py --list                               # what has been issued
    python3 tools/invoice.py --refresh-fonts                      # re-embed the brand faces

SENDING IS OUTWARD-FACING AND CANNOT BE UNDONE. It happens only behind --send, only after
a prompt showing the recipient and the amount, and never twice for the same number without
--resend-email. Mail goes out as hello@aiprofitlab.io through Resend, bcc'd to the same
address so there is always a copy of exactly what the customer received.

WHY A SEPARATE SERIES.  The storefront service issues INV-YYYY-NNNN off the Seat_Claims
sheet, from Cloud Run. This script issues LGI-YYYY-NNNN off a local register. They count
from different places, so sharing one series would eventually hand two customers the same
invoice number. Two clean series is the cheap fix; see docs/invoicing.md.

WHY BAISA.  All money is held as integer baisa (1 OMR = 1000) and only formatted at the
edge. Adding 0.1 + 0.2 in floats and printing the answer on an accounting document is a
bug that shows up as a one-baisa discrepancy months later, in a total the customer has
already paid.

The issuer is the legal entity, Lotus Gulf International, never the brand. No VAT line,
because there is no registration. No bank details on the document — those go by hand.
"""

from __future__ import annotations

import argparse
import base64
import html
import json
import mimetypes
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
INVOICES = ROOT / "invoices"
TEMPLATE = INVOICES / "template.html"
FONTS = INVOICES / "assets" / "fonts.css"
LOGO = ROOT / "brand" / "logo" / "wordmark-primary.png"
REGISTER = INVOICES / "register.json"
OUT = INVOICES / "out"

MUSCAT = ZoneInfo("Asia/Muscat")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

ENV_FILE = INVOICES / ".env"
RESEND_ENDPOINT = "https://api.resend.com/emails"

# The domain is DKIM-verified for Resend (resend._domainkey.aiprofitlab.io), and this is
# already the sender in aiden-backend and storefront-offer-api. One company, one address.
MAIL_FROM = "AI Profit Lab <hello@aiprofitlab.io>"
MAIL_BCC = "hello@aiprofitlab.io"   # our own copy of exactly what the customer got
REPLY_TO = "hello@aiprofitlab.io"

# Two decimals, to match the automatic storefront invoices in
# SmartChatBot/storefront-offer-api/lib/invoice.js. Oman's rial formally carries three
# (1000 baisa), so if you ever want OMR 950.000 on the page, change it in BOTH places —
# one company should not print money two ways.
DECIMALS = 2

GOOGLE_FONTS_URL = (
    "https://fonts.googleapis.com/css2"
    "?family=Marcellus"
    "&family=IBM+Plex+Sans:wght@400;500;600;700"
    "&family=IBM+Plex+Mono:wght@400;500"
    "&display=swap"
)


class Problem(Exception):
    """Something about the invoice is wrong. Printed without a traceback."""


# --------------------------------------------------------------------- money --


def to_baisa(value, field: str) -> int:
    """OMR (as a number or string in the JSON) -> integer baisa."""
    try:
        d = Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise Problem(f"{field}: {value!r} is not an amount")
    baisa = d * 1000
    if baisa != baisa.to_integral_value():
        raise Problem(f"{field}: {value} is finer than one baisa (OMR 0.001)")
    return int(baisa)


def money(baisa: int) -> str:
    """Integer baisa -> the string printed on the document."""
    step = 10 ** (3 - DECIMALS)
    if baisa % step:
        raise Problem(
            f"OMR {Decimal(baisa) / 1000} cannot be shown to {DECIMALS} decimals "
            f"without rounding. Round the amount, or raise DECIMALS to 3."
        )
    whole, frac = divmod(abs(baisa), 1000)
    body = f"{whole:,}"
    if DECIMALS:
        body += "." + f"{frac:03d}"[:DECIMALS]
    return f"{'−' if baisa < 0 else ''}OMR {body}"


# ------------------------------------------------------------------- dates --


def parse_date(value, field: str) -> datetime:
    if isinstance(value, str):
        try:
            return datetime.strptime(value.strip(), "%Y-%m-%d").replace(tzinfo=MUSCAT)
        except ValueError:
            raise Problem(f"{field}: {value!r} is not a date — use YYYY-MM-DD")
    raise Problem(f"{field}: expected a YYYY-MM-DD string")


def today() -> datetime:
    return datetime.now(MUSCAT)


def long_date(d: datetime) -> str:
    """`25 Aug 2026` — how a date is read in Oman, on Muscat's clock."""
    return f"{d.day:02d} {d:%b} {d.year}"


# ----------------------------------------------------------------- register --


def load_register() -> dict:
    if not REGISTER.exists():
        return {"note": "Every manual invoice ever issued. Do not delete lines.", "issued": []}
    return json.loads(REGISTER.read_text())


def save_register(reg: dict) -> None:
    REGISTER.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n")


def next_number(reg: dict, kind: str, when: datetime) -> str:
    """Next in series, read off what has already been issued.

    The register on disk is the counter, so the sequence survives a machine rebuild in a
    way an in-memory one would not. Series restart at 0001 each year — that is what the
    year in the number is for.
    """
    head = f"LGI-{'PF-' if kind == 'proforma' else ''}{when.year}-"
    highest = 0
    for row in reg["issued"]:
        num = str(row.get("number", ""))
        if not num.startswith(head):
            continue
        tail = num[len(head):]
        if tail.isdigit():
            highest = max(highest, int(tail))
    return f"{head}{highest + 1:04d}"


# ----------------------------------------------------------------- template --


# Matches the innermost IF block only — its body may not contain another IF opener. The
# caller loops, so nesting resolves from the inside out.
IF_BLOCK = re.compile(r"<!--IF:(\w+)-->(?P<body>(?:(?!<!--IF:).)*?)<!--ENDIF:\1-->", re.S)
ROWS_BLOCK = re.compile(r"<!--ROWS-->(?P<body>.*?)<!--ENDROWS-->", re.S)
PLACEHOLDER = re.compile(r"\{\{(\w+)\}\}")
ROWS_SENTINEL = "@@RENDERED_ROWS@@"


def resolve_ifs(text: str, flags: set[str]) -> str:
    while True:
        text, n = IF_BLOCK.subn(lambda m: m.group("body") if m.group(1) in flags else "", text)
        if not n:
            return text


def fill(text: str, values: dict[str, str]) -> str:
    def swap(m):
        key = m.group(1)
        if key not in values:
            raise Problem(f"template asks for {{{{{key}}}}} and nothing supplies it")
        return values[key]

    return PLACEHOLDER.sub(swap, text)


def esc(value) -> str:
    return html.escape(str(value), quote=True)


# --------------------------------------------------------------------- build --


def build_html(spec: dict, number: str, template: str) -> str:
    kind = spec.get("kind", "invoice")
    if kind not in ("invoice", "proforma"):
        raise Problem(f"kind: {kind!r} — expected \"invoice\" or \"proforma\"")

    buyer = spec.get("buyer") or {}
    if not buyer.get("name"):
        raise Problem("buyer.name is required — an invoice has to be addressed to somebody")

    items = spec.get("items") or []
    if not items:
        raise Problem("items: an invoice with no line items is not an invoice")

    issued = parse_date(spec["date"], "date") if spec.get("date") else today()

    # ---- line items -------------------------------------------------------
    has_qty = any(item.get("qty") is not None for item in items)
    rows, subtotal = [], 0
    for i, item in enumerate(items):
        where = f"items[{i}]"
        if not item.get("title"):
            raise Problem(f"{where}.title is required")

        qty = item.get("qty")
        if item.get("unit") is not None:
            if qty is None:
                raise Problem(f"{where}: has a unit price but no qty")
            unit = to_baisa(item["unit"], f"{where}.unit")
            if int(qty) != qty:
                raise Problem(f"{where}.qty: {qty} — use whole units, or price the line directly")
            amount = unit * int(qty)
            if item.get("amount") is not None and to_baisa(item["amount"], f"{where}.amount") != amount:
                raise Problem(
                    f"{where}: amount {item['amount']} does not equal qty × unit "
                    f"({qty} × {item['unit']}). Drop amount and let it be computed."
                )
        elif item.get("amount") is not None:
            # A qty with no unit price would print "2 × OMR 100.00 = OMR 100.00" — the
            # row would contradict its own arithmetic in front of the customer.
            if qty is not None:
                raise Problem(f"{where}: has a qty and an amount but no unit price")
            amount = to_baisa(item["amount"], f"{where}.amount")
            unit = amount
        else:
            raise Problem(f"{where}: needs either an amount, or a qty and a unit price")

        subtotal += amount
        rows.append(
            {
                "flags": {"HASQTY"} if has_qty else set(),
                "values": {
                    "ROW_TITLE": esc(item["title"]),
                    "ROW_NOTE": esc(item.get("note", "")),
                    "ROW_QTY": esc(qty if qty is not None else ""),
                    "ROW_UNIT": esc(money(unit) if qty is not None else ""),
                    "ROW_AMOUNT": esc(money(amount)),
                },
                "note": bool(item.get("note")),
            }
        )

    # ---- what is owed -----------------------------------------------------
    total = subtotal
    deductions = []
    for key, default_label in (("discount", "Discount"), ("already_paid", "Already paid")):
        block = spec.get(key)
        if not block:
            deductions.append((key, None, None))
            continue
        amount = to_baisa(block.get("amount"), f"{key}.amount")
        if amount <= 0:
            raise Problem(f"{key}.amount must be positive — it is subtracted, not added")
        total -= amount
        deductions.append((key, block.get("label", default_label), amount))

    if total < 0:
        raise Problem(
            f"the deductions come to more than the line items "
            f"(subtotal {money(subtotal)}, total {money(total)})"
        )

    # ---- paid, or due -----------------------------------------------------
    paid = spec.get("paid")
    paid_values = {
        "PAID_AMOUNT": "",
        "PAID_DATE": "",
        "PAID_METHOD_PHRASE": "",
        "PAID_REF": "",
        "PAID_CLOSING": "",
    }
    if paid:
        got = to_baisa(paid.get("amount", total), "paid.amount")
        if got < total:
            raise Problem(
                f"paid.amount {money(got)} is less than the total {money(total)}. A part "
                f"payment belongs in \"already_paid\", which is subtracted before the "
                f"total, so the document still adds up."
            )
        if got > total:
            raise Problem(f"paid.amount {money(got)} is more than the total {money(total)}")
        when = parse_date(paid["date"], "paid.date") if paid.get("date") else issued
        method = paid.get("method", "")
        paid_values = {
            "PAID_AMOUNT": esc(money(got)),
            "PAID_DATE": esc(long_date(when)),
            "PAID_METHOD_PHRASE": esc(f" by {method}") if method else "",
            "PAID_REF": esc(paid.get("reference", "")),
            "PAID_CLOSING": "This invoice is settled in full. No further action is needed.",
        }
        if kind == "proforma":
            raise Problem("a proforma cannot carry a payment — issue it as kind \"invoice\"")

    # ---- flags ------------------------------------------------------------
    reference = spec.get("reference", "")
    terms = spec.get("terms", "") or ("" if paid else "Due on receipt")
    pay_url = spec.get("pay_url", "")

    flags = set()
    if has_qty:
        flags.add("HASQTY")
    if reference:
        flags.add("REFERENCE")
    if terms:
        flags.add("TERMS")
    if reference or terms:
        flags.add("STRIP")
    if len(items) > 1 or any(d[2] for d in deductions):
        flags.add("SHOWSUBTOTAL")
    for key, _, amount in deductions:
        if amount:
            flags.add("DISCOUNT" if key == "discount" else "ALREADYPAID")
    if paid:
        flags.add("PAID")
        if paid_values["PAID_REF"]:
            flags.add("PAID_REF")
    else:
        flags.add("UNPAID")
        flags.add("PAY_URL" if pay_url else "NO_PAY_URL")
    if spec.get("notes"):
        flags.add("NOTES")
    if kind == "proforma":
        flags.add("PROFORMA")
    for key in buyer:
        if buyer.get(key) and key != "name":
            flags.add(f"BUYER_{key.upper()}")

    discount_label = next((lbl for k, lbl, a in deductions if k == "discount" and a), "")
    discount_amount = next((a for k, _, a in deductions if k == "discount" and a), 0)
    prepaid_label = next((lbl for k, lbl, a in deductions if k == "already_paid" and a), "")
    prepaid_amount = next((a for k, _, a in deductions if k == "already_paid" and a), 0)

    values = {
        "DOCTYPE": "PROFORMA INVOICE" if kind == "proforma" else "INVOICE",
        "DOCTYPE_CLASS": " is-proforma" if kind == "proforma" else "",
        "NUMBER": esc(number),
        "DATE": esc(long_date(issued)),
        "BUYER_NAME": esc(buyer["name"]),
        "BUYER_ATTN": esc(buyer.get("attn", "")),
        "BUYER_CR": esc(buyer.get("cr", "")),
        "BUYER_ADDRESS": esc(buyer.get("address", "")),
        "BUYER_EMAIL": esc(buyer.get("email", "")),
        "BUYER_PHONE": esc(buyer.get("phone", "")),
        "REFERENCE": esc(reference),
        "TERMS_LABEL": "Paid" if paid else "Terms",
        "TERMS": esc(terms),
        "SUBTOTAL": esc(money(subtotal)),
        "DISCOUNT_LABEL": esc(discount_label),
        "DISCOUNT": esc(money(discount_amount)) if discount_amount else "",
        "ALREADYPAID_LABEL": esc(prepaid_label),
        "ALREADYPAID": esc(money(prepaid_amount)) if prepaid_amount else "",
        "TOTAL_LABEL": "Paid" if paid else "Total due",
        "TOTAL": esc(money(total)),
        "PAY_URL": esc(pay_url),
        "NOTES": esc(spec.get("notes", "")),
        **paid_values,
    }

    # ---- render -----------------------------------------------------------
    row_match = ROWS_BLOCK.search(template)
    if not row_match:
        raise Problem("template.html has lost its <!--ROWS--> block")
    row_template = row_match.group("body")

    rendered_rows = []
    for row in rows:
        row_flags = set(row["flags"])
        if row["note"]:
            row_flags.add("ROW_NOTE")
        rendered_rows.append(fill(resolve_ifs(row_template, row_flags), row["values"]))

    doc = ROWS_BLOCK.sub(ROWS_SENTINEL, template)
    doc = fill(resolve_ifs(doc, flags), values)
    doc = doc.replace(ROWS_SENTINEL, "".join(rendered_rows))
    return inline_assets(doc), total


def inline_assets(doc: str) -> str:
    """Make the built page standalone: fonts and logo carried inside it.

    The template points at ../brand/logo and assets/fonts.css so it still renders when
    opened by hand from invoices/. The built copy lives in out/ and gets emailed and
    archived, so it must not depend on either path still being there.
    """
    if not FONTS.exists():
        raise Problem(f"{FONTS.relative_to(ROOT)} is missing — run --refresh-fonts")
    doc = doc.replace(
        '<link rel="stylesheet" href="assets/fonts.css">',
        f"<style>\n{FONTS.read_text()}</style>",
    )
    mime = mimetypes.guess_type(LOGO.name)[0] or "image/png"
    b64 = base64.b64encode(LOGO.read_bytes()).decode()
    return doc.replace('src="../brand/logo/wordmark-primary.png"', f'src="data:{mime};base64,{b64}"')


def print_pdf(html_path: Path, pdf_path: Path, timeout: int = 60) -> None:
    """Render the page to PDF with headless Chrome.

    Chrome writes the PDF and then, on this Mac, sometimes does not exit — it sits there
    until it is killed. So the file on disk is the success signal, not the exit code: wait
    a bounded time, kill it either way, then look for a non-empty PDF. Waiting on Chrome
    to exit hangs the script forever on an invoice that in fact rendered fine.
    """
    if not Path(CHROME).exists():
        raise Problem(f"Chrome is not at {CHROME} — it is what turns the page into a PDF")

    if pdf_path.exists():
        pdf_path.unlink()  # never mistake a previous run's PDF for this one's

    with tempfile.TemporaryDirectory() as profile:
        proc = subprocess.Popen(
            [
                CHROME,
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                f"--user-data-dir={profile}",
                "--no-pdf-header-footer",
                "--virtual-time-budget=4000",
                f"--print-to-pdf={pdf_path}",
                html_path.as_uri(),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        # Poll for the file rather than for the process. As soon as the PDF has appeared
        # and stopped growing, Chrome has done its job and can go.
        deadline, size = time.monotonic() + timeout, -1
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                break
            now = pdf_path.stat().st_size if pdf_path.exists() else -1
            if now > 0 and now == size:
                proc.kill()
                break
            size = now
            time.sleep(0.25)
        else:
            proc.kill()
        _, stderr = proc.communicate()

    if not pdf_path.exists() or pdf_path.stat().st_size == 0:
        raise Problem(f"Chrome produced no PDF:\n{(stderr or '').strip()}")


# ------------------------------------------------------------------- fonts --


def refresh_fonts() -> None:
    """Re-download the brand faces and embed them as base64.

    curl, not urllib: TLS verification fails for Python on this Mac. Latin subsets only —
    an English invoice never prints a Cyrillic glyph, and carrying them triples the file.
    """
    css = subprocess.run(
        ["curl", "-sS", "-A", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/126.0", GOOGLE_FONTS_URL],
        capture_output=True, text=True, check=True,
    ).stdout
    blocks = re.findall(r"/\*\s*([\w-]+)\s*\*/\s*(@font-face\s*\{.*?\})", css, re.S)
    kept = []
    for subset, block in blocks:
        if subset != "latin":
            continue
        url = re.search(r"url\((https://[^)]+\.woff2)\)", block).group(1)
        data = subprocess.run(["curl", "-sS", url], capture_output=True, check=True).stdout
        block = re.sub(
            r"url\(https://[^)]+\.woff2\)",
            f"url(data:font/woff2;base64,{base64.b64encode(data).decode()})",
            block,
        )
        kept.append(re.sub(r"\s*unicode-range:[^;]+;", "", block))
    if not kept:
        raise Problem("Google Fonts returned no latin faces — check the network")
    FONTS.parent.mkdir(parents=True, exist_ok=True)
    FONTS.write_text(
        "/* Brand faces, base64-embedded so an invoice renders identically offline.\n"
        "   Regenerate with: python3 tools/invoice.py --refresh-fonts */\n" + "\n".join(kept) + "\n"
    )
    print(f"{len(kept)} faces embedded -> {FONTS.relative_to(ROOT)} ({FONTS.stat().st_size / 1024:.0f} KB)")



# ---------------------------------------------------------------------- mail --


def load_env() -> None:
    """Read invoices/.env into the environment. Gitignored — this repo is public."""
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def resend_key() -> str:
    load_env()
    key = os.environ.get("RESEND_API_KEY", "").strip()
    if not key:
        raise Problem(
            "no RESEND_API_KEY. Create one at https://resend.com/api-keys and put it in\n"
            f"  {ENV_FILE.relative_to(ROOT)}   as   RESEND_API_KEY=re_...\n"
            "That file is gitignored; this repo is public."
        )
    if not key.startswith("re_"):
        raise Problem("RESEND_API_KEY does not look like a Resend key (they start with re_)")
    return key


def covering_email(spec: dict, number: str, total: int, kind: str) -> tuple[str, str, str]:
    """Subject, HTML and plain-text bodies for the invoice email.

    NO BANK DETAILS, deliberately, exactly as on the PDF. If the customer wants to
    transfer, they reply and Nahid answers a person he has spoken to.
    """
    buyer = spec.get("buyer") or {}
    greeting = buyer.get("attn") or buyer.get("name")
    paid = bool(spec.get("paid"))
    doc = "Proforma invoice" if kind == "proforma" else "Invoice"
    amount = money(total)

    if paid:
        standing = f"{amount}, paid in full. This is your receipt."
    else:
        terms = spec.get("terms") or "due on receipt"
        standing = f"{amount}, {terms[0].lower() + terms[1:]}."

    pay_url = spec.get("pay_url", "")
    if paid:
        action = "Nothing is owed on it. Keep it for your records."
    elif pay_url:
        action = f'You can pay by card here: <a href="{esc(pay_url)}" style="color:#0F6E56">{esc(pay_url)}</a>'
    else:
        action = "To pay by transfer, just reply to this email and I will send you the details."

    action_text = re.sub(r"<[^>]+>", "", action)

    subject = f"{doc} {number} — AI Profit Lab"

    html = f"""<div style="font-family:-apple-system,Segoe UI,sans-serif;font-size:15px;line-height:1.6;color:#232B26;background:#F1EFE8;padding:28px">
<div style="max-width:560px;margin:0 auto;background:#FAF8F2;border:1px solid #DAD4C4;border-radius:12px;padding:28px">
<p style="margin:0 0 16px">Hi {esc(greeting)},</p>
<p style="margin:0 0 16px">Your {doc.lower()} is attached &mdash; <b>{esc(standing)}</b></p>
<p style="margin:0 0 16px">{action}</p>
<p style="margin:0 0 16px">If anything on it does not look right, tell me and I will reissue it.</p>
<p style="margin:24px 0 0">Nahid Abyari<br>
<span style="color:#5C6259">Founder, AI Profit Lab</span></p>
<p style="margin:20px 0 0;padding-top:14px;border-top:1px solid #DAD4C4;font-size:12px;color:#5C6259">
AI Profit Lab &mdash; a brand of Lotus Gulf International &middot; CR 1570092 &middot; aiprofitlab.io<br>
<span style="color:#BA7517">Every success starts with insight.</span></p>
</div></div>"""

    text = (
        f"Hi {greeting},\n\n"
        f"Your {doc.lower()} is attached - {standing}\n\n"
        f"{action_text}\n\n"
        "If anything on it does not look right, tell me and I will reissue it.\n\n"
        "Nahid Abyari\n"
        "Founder, AI Profit Lab\n\n"
        "AI Profit Lab - a brand of Lotus Gulf International - CR 1570092 - aiprofitlab.io\n"
    )
    return subject, html, text


def send_email(to: str, subject: str, html: str, text: str, pdf: Path) -> str:
    """POST the message to Resend. Returns the message id.

    curl, not urllib: Python's TLS verification fails on this Mac. The payload carries a
    base64 PDF and is far too big for a command line, so it goes through a temp file.
    """
    key = resend_key()
    payload = {
        "from": MAIL_FROM,
        "to": [to],
        "bcc": [MAIL_BCC],
        "reply_to": REPLY_TO,
        "subject": subject,
        "html": html,
        "text": text,
        "attachments": [
            {"filename": pdf.name, "content": base64.b64encode(pdf.read_bytes()).decode()}
        ],
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        json.dump(payload, fh)
        body_file = fh.name
    try:
        result = subprocess.run(
            ["curl", "-sS", "-X", "POST", RESEND_ENDPOINT,
             "-H", f"Authorization: Bearer {key}",
             "-H", "Content-Type: application/json",
             "--data-binary", f"@{body_file}"],
            capture_output=True, text=True,
        )
    finally:
        Path(body_file).unlink(missing_ok=True)

    if result.returncode != 0:
        raise Problem(f"could not reach Resend: {result.stderr.strip()}")
    try:
        reply = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise Problem(f"Resend returned something unreadable: {result.stdout[:400]}")
    if "id" not in reply:
        # Surface Resend's own words — "domain not verified" and "invalid key" are
        # different problems and the fix is different.
        raise Problem(f"Resend refused the message: {json.dumps(reply)[:400]}")
    return reply["id"]


def confirm(number: str, amount: str, to: str) -> bool:
    """Outward-facing and irreversible, so it is asked for out loud."""
    print(f"\n  {number}   {amount}")
    print(f"  to:  {to}")
    print(f"  bcc: {MAIL_BCC}")
    if not sys.stdin.isatty():
        print("  not a terminal — pass --yes to send without being asked")
        return False
    return input("  Send? [y/N] ").strip().lower() in ("y", "yes")


# --------------------------------------------------------------------- main --


def check_mail() -> None:
    """Answer "did I put the key in the right place?" without emailing anybody.

    It cannot prove the key still works — only a real send does that — so it says so
    rather than implying a green light it has not earned.
    """
    print(f"env file : {ENV_FILE}")
    if not ENV_FILE.exists():
        raise Problem(
            f"not found. Create it:\n"
            f"  cp invoices/.env.example invoices/.env\n"
            f"then put your key in it as   RESEND_API_KEY=re_..."
        )
    key = resend_key()  # raises with instructions if missing or malformed
    print(f"key      : {key[:6]}{'…' * 1}{key[-4:]}  ({len(key)} chars)")
    print(f"from     : {MAIL_FROM}")
    print(f"bcc      : {MAIL_BCC}")
    tracked = subprocess.run(["git", "check-ignore", "-q", str(ENV_FILE)], cwd=ROOT).returncode != 0
    print(f"gitignored: {'NO — DO NOT COMMIT' if tracked else 'yes'}")
    print("\nThe key is readable and well-formed. Whether Resend accepts it is only proven")
    print("by a real send — try one to your own address first.")


def show_register() -> None:
    reg = load_register()
    if not reg["issued"]:
        print("Nothing issued yet.")
        return
    print(f"{'NUMBER':<18} {'DATE':<12} {'TOTAL':>14}  BILLED TO")
    for row in reg["issued"]:
        print(f"{row['number']:<18} {row['date']:<12} {row['total']:>14}  {row['to']}")
    print(f"\n{len(reg['issued'])} issued.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", nargs="?", help="the customer JSON, e.g. invoices/customers/acme.json")
    ap.add_argument("--dry", action="store_true", help="render without allocating a number or writing the register")
    ap.add_argument("--list", action="store_true", help="show everything issued so far")
    ap.add_argument("--refresh-fonts", action="store_true", help="re-download and re-embed the brand faces")
    ap.add_argument("--send", action="store_true", help="email the invoice to the customer, bcc hello@aiprofitlab.io")
    ap.add_argument("--yes", action="store_true", help="with --send, skip the confirmation prompt")
    ap.add_argument("--resend-email", action="store_true", help="send again an invoice already recorded as sent")
    ap.add_argument("--check-mail", action="store_true", help="confirm the Resend key is found, without sending anything")
    args = ap.parse_args()

    if args.dry and args.send:
        raise Problem("--dry and --send contradict each other: a dry run must not reach a customer")

    if args.refresh_fonts:
        refresh_fonts()
        return 0
    if args.list:
        show_register()
        return 0
    if args.check_mail:
        check_mail()
        return 0
    if not args.spec:
        ap.print_help()
        return 2

    spec_path = Path(args.spec)
    if not spec_path.is_absolute():
        spec_path = (Path.cwd() / spec_path).resolve()
    if not spec_path.exists():
        raise Problem(f"{args.spec} does not exist")
    spec = json.loads(spec_path.read_text())

    reg = load_register()
    kind = spec.get("kind", "invoice")
    when = parse_date(spec["date"], "date") if spec.get("date") else today()

    # A number already on the spec is reused, so re-running to fix a typo regenerates the
    # same invoice instead of burning the next number in the series.
    reissue = bool(spec.get("number"))
    number = spec["number"] if reissue else ("LGI-DRAFT" if args.dry else next_number(reg, kind, when))

    doc, total = build_html(spec, number, TEMPLATE.read_text())

    OUT.mkdir(parents=True, exist_ok=True)
    html_path = OUT / f"{number}.html"
    pdf_path = OUT / f"{number}.pdf"
    html_path.write_text(doc)
    print_pdf(html_path, pdf_path)

    if args.dry:
        print(f"DRY RUN — no number allocated, nothing written to the register.")
        print(f"  {pdf_path.relative_to(ROOT)}")
        return 0

    if not reissue:
        # Write the number back so the next run reissues rather than reallocates.
        spec["number"] = number
        spec_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n")
        reg["issued"].append(
            {
                "number": number,
                "kind": kind,
                "date": when.strftime("%Y-%m-%d"),
                "to": (spec.get("buyer") or {}).get("name", ""),
                "total": money(total),
                "total_baisa": total,
                "spec": str(spec_path.relative_to(ROOT)) if spec_path.is_relative_to(ROOT) else str(spec_path),
            }
        )
        save_register(reg)

    print(f"{'Reissued' if reissue else 'Issued'} {number} — {money(total)} — {(spec.get('buyer') or {}).get('name','')}")
    print(f"  {pdf_path.relative_to(ROOT)}")
    if not reissue:
        print(f"  number written back to {spec_path.name}; re-running regenerates it rather than taking a new one")

    if not args.send:
        return 0

    # ---- email ------------------------------------------------------------
    row = next((r for r in reg["issued"] if r["number"] == number), None)
    if row and row.get("sent") and not args.resend_email:
        raise Problem(
            f"{number} was already emailed to {row['sent']['to']} on {row['sent']['at'][:10]}.\n"
            "Pass --resend-email to send it a second time."
        )

    to = (spec.get("buyer") or {}).get("email", "").strip()
    if not to:
        raise Problem("buyer.email is missing — there is nowhere to send it")
    if "@" not in to or " " in to:
        raise Problem(f"buyer.email {to!r} is not an address")

    subject, body_html, body_text = covering_email(spec, number, total, kind)
    resend_key()  # fail on a missing key BEFORE asking whether to send

    if not (args.yes or confirm(number, money(total), to)):
        print("  not sent.")
        return 0

    message_id = send_email(to, subject, body_html, body_text, pdf_path)
    print(f"  sent to {to} (bcc {MAIL_BCC}) — {message_id}")

    if row is not None:
        row["sent"] = {"to": to, "at": datetime.now(MUSCAT).isoformat(timespec="seconds"), "id": message_id}
        save_register(reg)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Problem as err:
        print(f"invoice: {err}", file=sys.stderr)
        sys.exit(1)
