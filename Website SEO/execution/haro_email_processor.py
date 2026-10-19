#!/usr/bin/env python3
"""
HARO & Media Query Email Processor for AI Profit Lab.
Scans incoming HARO / Connectively / Featured / Qwoted / SourceBottle digests, splits them into
queries and reads each deadline in code, has Gemini screen every query (PITCH or SKIP, with a
reason), drafts one reply per chosen query from a fixed set of facts about Nahid, and saves the
drafts in Gmail for review. Never sends anything.

Since 2026-10-16 this is the fallback. The main drafter is haro_agent.py (Antigravity drafts,
Claude reviews), which runs every 10 minutes while the Mac is on. Since 2026-10-18 the Mac runs
this every 30 minutes with --defer-to-agent --min-age-hours 3: while that pipeline is alive it
takes only the digests handed over to it, and when it is down, digests older than 3 hours.
GitHub no longer runs it on a schedule. The facts and rules live in haro_rules.py, shared with it.

  python3 execution/haro_email_processor.py                 # every unprocessed digest, now
  python3 execution/haro_email_processor.py --defer-to-agent --min-age-hours 3   # the Mac's scheduled run
  python3 execution/haro_email_processor.py --dry-run       # write drafts to .tmp/haro_dryrun/ instead
  python3 execution/haro_email_processor.py --delete-expired [--apply]
"""

import os
import re
import sys
import json
import base64
import calendar
import datetime
import email.utils
import time
from email.mime.text import MIMEText
from zoneinfo import ZoneInfo
import urllib.request
import urllib.error

# Google Client Libraries
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.auth.exceptions import TransportError
    from googleapiclient.discovery import build
except ImportError as e:
    print(f"Missing Google client libraries: {e}")
    print("Please install via: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    sys.exit(1)

from haro_rules import (SPOKESPERSON_FACTS, WRITE_YOURSELF, SCREENING_RULES,
                        PITCH_TASK, NOTES_TASK, DRAFT_RULES, claims_to_check)

# Scopes needed: Read emails, create drafts, and modify labels (mark as read)
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify'
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_FILE = os.path.join(BASE_DIR, 'credentials.json')
TOKEN_FILE = os.path.join(BASE_DIR, 'token.json')
ENV_FILE = os.path.join(BASE_DIR, '.env')

# Gmail label put on every digest once it has been analysed. Gmail search spells a
# label name in lowercase with hyphens for spaces.
PROCESSED_LABEL = 'HARO Processed'
PROCESSED_LABEL_SEARCH = PROCESSED_LABEL.lower().replace(' ', '-')


def load_env():
    """Load simple key=value pairs from .env into os.environ."""
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    os.environ[key.strip()] = val.strip().strip('"').strip("'")


def get_gemini_api_key():
    """Retrieve Gemini API key from environment."""
    load_env()
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("[!] GEMINI_API_KEY is not set in .env or environment.")
    return api_key


def get_gmail_service():
    """Authenticate and return the Gmail API service."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            if not creds.has_scopes(SCOPES):
                print("[*] Stored token is missing required scopes. Re-authentication required.")
                creds = None
        except Exception as e:
            print(f"[!] Error loading token.json: {e}")
            creds = None

    # Handle expired credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # launchd runs a job missed during sleep the moment the Mac wakes, often before
            # Wi-Fi is back (2026-10-13: DNS failure reported as an expired token). A network
            # error is retried; only a refusal from Google means the token itself is bad.
            for attempt in range(6):
                try:
                    print("[*] Refreshing expired Gmail OAuth access token...")
                    creds.refresh(Request())
                    with open(TOKEN_FILE, 'w', encoding='utf-8') as token:
                        token.write(creds.to_json())
                    print("[+] Successfully refreshed and saved token.json.")
                    break
                except TransportError as e:
                    if attempt == 5:
                        print(f"[FATAL] No network after 6 tries over 2.5 minutes, so Google could not be reached: {e}")
                        print("        token.json is probably fine; the next scheduled run will retry.")
                        sys.exit(1)
                    print(f"[!] Network not reachable yet ({e}). Retrying in 30s...")
                    time.sleep(30)
                except Exception as e:
                    print(f"[!] Failed to refresh token: {e}")
                    creds = None
                    break

        if not creds:
            # Check if running interactively or headless (launchd / cron / CI)
            is_interactive = sys.stdin.isatty() and not os.environ.get('CI')
            if not is_interactive:
                print("\n" + "!" * 60)
                print("[FATAL] Gmail credentials in token.json are expired or invalid,")
                print("        and this process is running in a non-interactive environment.")
                print("        Please run: python3 tools/authenticate_gmail.py")
                print("!" * 60 + "\n")
                sys.exit(1)

            if not os.path.exists(CREDENTIALS_FILE):
                print(f"\n[ERROR] Missing '{CREDENTIALS_FILE}'!")
                print("Please download credentials.json from Google Cloud Console and place it in the project root folder.")
                sys.exit(1)

            print("[*] Launching browser for Google authentication...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=8080)

            with open(TOKEN_FILE, 'w', encoding='utf-8') as token:
                token.write(creds.to_json())
                print(f"[+] Saved authentication token to '{TOKEN_FILE}'")

    return build('gmail', 'v1', credentials=creds)


def clean_html_to_text(html_content):
    """Strip basic HTML tags to produce readable plain text for parsing."""
    text = re.sub(r'<(br|p|div|tr|li)[^>]*>', '\n', html_content, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    return text.strip()


def extract_message_body(payload):
    """Extract plain text or HTML body from a Gmail message payload."""
    body_text = ""

    if 'parts' in payload:
        for part in payload['parts']:
            mime_type = part.get('mimeType', '')
            data = part.get('body', {}).get('data', '')
            if data:
                decoded = base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8', errors='ignore')
                if mime_type == 'text/plain':
                    return decoded
                elif mime_type == 'text/html' and not body_text:
                    body_text = clean_html_to_text(decoded)
            if 'parts' in part:
                nested = extract_message_body(part)
                if nested:
                    return nested
    else:
        data = payload.get('body', {}).get('data', '')
        if data:
            decoded = base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8', errors='ignore')
            if payload.get('mimeType') == 'text/html':
                return clean_html_to_text(decoded)
            return decoded

    return body_text


def safe_parse_json(text):
    """Robustly parse JSON output from LLMs, handling unescaped newlines/quotes."""
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith('```'):
        cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
        cleaned = re.sub(r'\s*```$', '', cleaned)
        cleaned = cleaned.strip()

    if not cleaned.startswith('{'):
        m = re.search(r'(\{[\s\S]*\})', cleaned)
        if m:
            cleaned = m.group(1)

    # 1. First attempt: standard loads with strict=False (handles unescaped control characters)
    try:
        return json.loads(cleaned, strict=False)
    except Exception:
        pass

    # 2. Second attempt: escape literal unescaped newlines inside string literals
    try:
        in_str = False
        esc = False
        res = []
        for ch in cleaned:
            if ch == '\\' and not esc:
                esc = True
                res.append(ch)
                continue
            if ch == '"' and not esc:
                in_str = not in_str
            elif ch == '\n' and in_str:
                res.append('\\n')
                esc = False
                continue
            res.append(ch)
            esc = False
        return json.loads("".join(res), strict=False)
    except Exception:
        pass

    # 3. Third attempt: try repairing truncated JSON endings
    try:
        trimmed = cleaned.rstrip()
        if not trimmed.endswith('}'):
            quotes = trimmed.count('"') - trimmed.count('\\"')
            if quotes % 2 != 0:
                trimmed += '"'
            if ']' in trimmed and trimmed.rfind(']') < trimmed.rfind('['):
                trimmed += ']'
            if trimmed.count('{') > trimmed.count('}'):
                trimmed += '}' * (trimmed.count('{') - trimmed.count('}'))
            return json.loads(trimmed, strict=False)
    except Exception:
        pass

    return None


# Tried in order. On the free tier (2026-10-16) Gemini Pro has no quota at all, and each Flash
# model has its own allowance of about 20 requests a day. The article publisher
# (daily_publish.py) uses 3.8 -> 3.6 -> 3.5 Flash on the same key, so HARO starts with models it
# doesn't use and only falls back to those. A day of HARO costs about one call per digest plus
# one per pitch. Override with a comma-separated HARO_GEMINI_MODELS.
HARO_MODELS = os.environ.get(
    'HARO_GEMINI_MODELS',
    'gemini-3.7-flash,gemini-3-flash-preview,gemini-3.5-flash,gemini-flash-latest,gemini-3.6-flash').split(',')


def _daily_quota_spent(res):
    """True for a 429 that waiting won't fix within this run: a per-day limit, or a limit of 0."""
    try:
        details = res.json().get('error', {}).get('details', [])
    except ValueError:
        return False
    return any('PerDay' in v.get('quotaId', '') or str(v.get('quotaValue')) in ('0', 'None')
               for d in details for v in d.get('violations', []))


def call_gemini(prompt, api_key, schema=None, models=None, temperature=0.2):
    """Call Gemini and return the parsed JSON reply, trying each model in turn.

    With `schema`, Gemini is held to that response shape (structured output).
    """
    import requests

    models = models or HARO_MODELS
    config = {
        "temperature": temperature,
        "maxOutputTokens": 32768,
        "responseMimeType": "application/json",
    }
    if schema:
        config["responseSchema"] = schema
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": config}

    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        for attempt in range(3):
            try:
                res = requests.post(url, json=payload, timeout=180)
            except Exception as e:
                print(f"     [!] Gemini {model} attempt {attempt + 1}: {type(e).__name__}")
                time.sleep(5)
                continue
            if res.status_code == 200:
                parts = res.json().get('candidates', [{}])[0].get('content', {}).get('parts', [])
                text = "".join(p.get('text', '') for p in parts if 'text' in p).strip()
                parsed = safe_parse_json(text)
                if parsed:
                    if model != models[0]:
                        print(f"     [*] Answered by {model}.")
                    return parsed
                print(f"[!] JSON parsing error on {model}. Raw preview: {text[:200]} ... {text[-100:]}")
                break
            if res.status_code == 429 and _daily_quota_spent(res):
                print(f"     [!] Gemini {model}: no free quota left today. Trying the next model.")
                break
            if res.status_code in (429, 500, 503):
                print(f"     [!] Gemini {model} attempt {attempt + 1}: HTTP {res.status_code} {res.text[:120]!r}")
                time.sleep(10 * (attempt + 1))
                continue
            if res.status_code != 404:
                print(f"[!] Gemini Error ({model}): {res.status_code} - {res.text[:200]}")
            break
    return None


PITCH_FROM = 'nahid@aiprofitlab.io'   # the address the HARO account is registered to; a verified send-as alias

# The brand signature (aiprofitlab-brand skill, section 9), one item per line.
SIGNATURE = (
    "Nahid Abyari\n"
    "Founder, AI Profit Lab\n"
    "hello@aiprofitlab.io · +968 9924 5250 · aiprofitlab.io\n"
    "LinkedIn: https://www.linkedin.com/in/nahid-aby · headshot on request"
)

NOTES_START = "=== NOTES FOR NAHID: delete from here down to the dashed line before sending ==="
NOTES_END = "-" * 84

MIN_LEAD = datetime.timedelta(hours=1)   # a deadline closer than this leaves no time to review a draft
EASTERN = ZoneInfo('America/New_York')   # HARO deadlines are in ET
MUSCAT = ZoneInfo('Asia/Muscat')

MONTHS = {name.lower(): i for i, name in enumerate(calendar.month_name) if name}
MONTHS.update({name.lower(): i for i, name in enumerate(calendar.month_abbr) if name})
MONTHS['sept'] = 9
_MONTH_RE = '|'.join(sorted(MONTHS, key=len, reverse=True))


def parse_deadline(raw, reference):
    """Turn a HARO deadline into an aware UTC datetime, or None if it can't be read.

    Handles "6:00 PM ET - 20 October", "October 15, 2026, at 5 p.m. Eastern" and
    "9 October 2026, 4:56 PM ET". `reference` (an aware datetime, e.g. when the digest
    arrived) supplies a missing year. A date with no time counts as 23:59 that day.
    """
    if not raw:
        return None
    text = raw.lower()
    d = re.search(rf'\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({_MONTH_RE})\b', text)
    if d:
        day, month = int(d.group(1)), MONTHS[d.group(2)]
    else:
        d = re.search(rf'\b({_MONTH_RE})\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?\b', text)
        if not d:
            return None
        month, day = MONTHS[d.group(1)], int(d.group(2))
    y = re.search(r'\b(20\d{2})\b', text)
    year = int(y.group(1)) if y else reference.year
    if not y and month < reference.month - 6:
        year += 1   # a December digest with a January deadline
    hour, minute = 23, 59
    t = re.search(r'\b(\d{1,2})(?::(\d{2}))?\s*([ap])\.?\s*m\b', text)
    if t:
        hour = int(t.group(1)) % 12 + (12 if t.group(3) == 'p' else 0)
        minute = int(t.group(2) or 0)
    try:
        return datetime.datetime(year, month, day, hour, minute, tzinfo=EASTERN).astimezone(datetime.timezone.utc)
    except ValueError:
        return None


def _unwrap(text):
    """Join the digest's hard-wrapped lines back into paragraphs."""
    paras = [re.sub(r'\s+', ' ', p).strip() for p in re.split(r'\n\s*\n', text)]
    return '\n\n'.join(p for p in paras if p)


def _field(header, label):
    m = re.search(rf'^{label}:[ \t]*(.*)$', header, re.M)
    return m.group(1).strip() if m else ''


def parse_haro_digest(text):
    """Split a HARO digest into its queries, without an LLM. Returns [] for any other format.

    Each query is keyed by its reply+ address, which HARO gives every query and repeats
    unchanged in the copies sent to both subscribed addresses.
    """
    starts = list(re.finditer(r'^(\d{1,3})\) Summary:\s*', text, re.M))
    queries = []
    for i, m in enumerate(starts):
        end = starts[i + 1].start() if i + 1 < len(starts) else len(text)
        block = text[m.end():end].split('\nBack to Top')[0]
        head, found, body = block.partition('\nQuery:')
        if not found:
            continue
        title, _, fields = head.partition('\nName:')
        fields = 'Name:' + fields
        addr = re.search(r'[\w.+-]+@[\w-]+(?:\.[\w-]+)+', _field(fields, 'Email'))
        outlet = _field(fields, 'Media Outlet')
        outlet_m = re.match(r'(.*?)\s*\((https?://[^)\s]+)\)\s*$', outlet)
        profile = re.search(r'HARO Journalist Profile URL:\s*(https?://\S+)', fields)
        queries.append({
            'id': addr.group(0).lower() if addr else f"query-{m.group(1)}",
            'title': _unwrap(title),
            'journalist': _field(fields, 'Name'),
            'category': _field(fields, 'Category'),
            'email': addr.group(0) if addr else '',
            'profile_url': profile.group(1) if profile else '',
            'outlet': outlet_m.group(1) if outlet_m else outlet,
            'outlet_url': outlet_m.group(2) if outlet_m else '',
            'deadline_raw': _field(fields, 'Deadline'),
            'no_ai': 'no ai pitches considered' in fields.lower(),
            'query': _unwrap(body),
        })
    return queries


EXTRACT_SCHEMA = {
    "type": "OBJECT",
    "properties": {"queries": {"type": "ARRAY", "items": {
        "type": "OBJECT",
        "properties": {
            "title": {"type": "STRING"}, "journalist": {"type": "STRING"}, "outlet": {"type": "STRING"},
            "email": {"type": "STRING"}, "submission_url": {"type": "STRING"},
            "deadline_raw": {"type": "STRING"}, "query": {"type": "STRING"},
        },
        "required": ["title", "outlet", "email", "deadline_raw", "query"],
    }}},
    "required": ["queries"],
}


def extract_queries_with_gemini(text, api_key):
    """For a digest that isn't in HARO's format (Connectively, Qwoted, ...): list its queries with Gemini."""
    prompt = (
        "This email is a digest of journalist requests for expert sources. List every request in it. "
        "Copy each field from the email; do not summarise or invent. Use an empty string for a field the email "
        "doesn't give. 'email' is where a reply goes; 'query' is the full request text.\n\nEMAIL:\n---\n"
        f"{text[:80000]}\n---"
    )
    result = call_gemini(prompt, api_key, schema=EXTRACT_SCHEMA, temperature=0)
    queries = []
    for i, q in enumerate((result or {}).get('queries', [])):
        addr = (q.get('email') or '').strip()
        queries.append({
            'id': addr.lower() if '@' in addr else f"query-{i + 1}-{q.get('title', '')[:40].lower()}",
            'title': q.get('title', '').strip(), 'journalist': q.get('journalist', '').strip(),
            'category': '', 'email': addr if '@' in addr else '',
            'profile_url': q.get('submission_url', ''), 'outlet': q.get('outlet', '').strip(), 'outlet_url': '',
            'deadline_raw': q.get('deadline_raw', '').strip(),
            'no_ai': 'no ai pitch' in q.get('query', '').lower(), 'query': q.get('query', '').strip(),
        })
    return queries


SCREEN_SCHEMA = {
    "type": "OBJECT",
    "properties": {"decisions": {"type": "ARRAY", "items": {
        "type": "OBJECT",
        "properties": {
            "id": {"type": "STRING"},
            "eligible": {"type": "BOOLEAN"},
            "reason": {"type": "STRING"},
            "fit": {"type": "INTEGER"},
            "decision": {"type": "STRING", "enum": ["PITCH", "SKIP"]},
            "ai_replies_forbidden": {"type": "BOOLEAN"},
        },
        "required": ["id", "eligible", "reason", "fit", "decision", "ai_replies_forbidden"],
        "propertyOrdering": ["id", "eligible", "reason", "fit", "decision", "ai_replies_forbidden"],
    }}},
    "required": ["decisions"],
}


def screen_queries(queries, api_key):
    """Ask Gemini for a PITCH/SKIP decision, with a reason, on every query. None if it fails."""
    if not queries:
        return {}
    listing = "\n\n".join(
        f"[q{i}] {q['title']}\nOutlet: {q['outlet']} | Category: {q['category'] or '-'}\n{q['query']}"
        for i, q in enumerate(queries)
    )
    prompt = f"""You screen journalist requests for one expert source and decide, for EVERY request,
whether he should reply.

THE SOURCE
{SPOKESPERSON_FACTS}

{SCREENING_RULES}
Give one decision for every id below, in order. Keep each reason to one sentence.

REQUESTS
{listing}
"""
    result = call_gemini(prompt, api_key, schema=SCREEN_SCHEMA, temperature=0)
    if not result:
        return None
    by_id = {d.get('id'): d for d in result.get('decisions', [])}
    decisions = {}
    for i, q in enumerate(queries):
        d = by_id.get(f"q{i}")
        if d is None:
            print(f"     [!] Screening returned no decision for '{q['title']}'. Treating it as SKIP.")
            d = {'decision': 'SKIP', 'fit': 0, 'eligible': False, 'reason': 'no decision returned',
                 'ai_replies_forbidden': False}
        decisions[q['id']] = d
    return decisions


DRAFT_SCHEMA = {
    "type": "OBJECT",
    "properties": {"fit_note": {"type": "STRING"}, "only_if_true": {"type": "STRING"}, "text": {"type": "STRING"}},
    "required": ["fit_note", "only_if_true", "text"],
    "propertyOrdering": ["fit_note", "only_if_true", "text"],
}


def write_pitch(q, api_key, notes_only):
    """Draft the reply to one query, or talking points when the journalist rejects AI-written replies."""
    task = NOTES_TASK if notes_only else PITCH_TASK

    prompt = f"""You draft replies to journalist requests for Nahid Abyari.

THE REQUEST
Title: {q['title']}
Outlet: {q['outlet']}
Journalist: {q['journalist']}
{q['query']}

FACTS ABOUT NAHID: the only things you may state about him or AI Profit Lab
{SPOKESPERSON_FACTS}

{task}

{DRAFT_RULES}
"""
    result = call_gemini(prompt, api_key, schema=DRAFT_SCHEMA, temperature=0.4)
    if not result or not (result.get('text') or '').strip():
        return None
    return result


def greeting(q):
    """The greeting: "Hi <first name>,", or "Hello," when the query names a desk or the outlet ("Featured News")."""
    name = q['journalist'].strip()
    is_person = name and name.lower() != q['outlet'].strip().lower() and not re.search(
        r'\b(news|team|editors?|desk|staff|magazine|media|newsroom|podcast)\b', name, re.I)
    return f"Hi {name.split()[0]}," if is_person else "Hello,"


def pitch_subject(q, notes_only=False):
    subject = f"HARO Pitch: {q['title']} — Nahid Abyari, AI Profit Lab"
    return WRITE_YOURSELF + subject if notes_only else subject


def pitch_body(q, text):
    """The email the journalist receives: greeting, reply, brand signature."""
    return f"{greeting(q)}\n\n{text.strip()}\n\n{SIGNATURE}\n"


def build_draft(q, result, notes_only, extra_notes=(), appendix=()):
    """Assemble the subject and body of a pitch draft. Everything above NOTES_END is for Nahid only.

    extra_notes: lines added after the standard notes (haro_agent.py puts Claude's review there).
    appendix: lines added after the journalist's request, still inside the notes.
    """
    deadline = q.get('deadline_utc')
    if deadline:
        when = (f"{q['deadline_raw']}  =  {deadline.astimezone(MUSCAT):%a %d %b, %H:%M} Muscat  "
                f"({deadline:%Y-%m-%d %H:%M} UTC)")
    else:
        when = f"{q['deadline_raw'] or 'not stated'}  (couldn't read it: check the request)"
    text = result['text'].strip()
    notes = [
        NOTES_START,
        f"Outlet:      {q['outlet']}" + (f" ({q['outlet_url']})" if q['outlet_url'] else ''),
        f"Journalist:  {q['journalist']}" + (f" · {q['profile_url']}" if q['profile_url'] else ''),
        f"Deadline:    {when}",
        f"Why pitch:   {result.get('fit_note', '').strip()}",
    ]
    condition = (result.get('only_if_true') or '').strip()
    if condition:
        notes.append(f"Send only if true: {condition}")
    placeholders = re.findall(r'\[ADD:[^\]]*\]', text)
    if placeholders:
        notes.append(f"Fill in:     {len(placeholders)} [ADD: ...] placeholder(s) below")
    flags = claims_to_check(re.sub(r'\[ADD:[^\]]*\]', '', text), q['query'])
    flags += [f"placeholder suggests an answer: {p}" for p in placeholders if re.search(r'\d|e\.g\.', p)]
    if flags:
        notes.append("Check:       " + "; ".join(flags))
    if notes_only:
        notes += ["!! NO AI-WRITTEN PITCHES: this journalist rejects AI-written replies, so below are",
                  "   talking points, not a pitch. Write the reply in your own words, then remove the",
                  f"   {WRITE_YOURSELF.strip()} tag from the subject."]
    notes += list(extra_notes)
    notes += ["", f"Their request: {q['title']}", q['query'], *appendix, NOTES_END]
    body = "\n".join(notes) + "\n\n" + pitch_body(q, text)
    return pitch_subject(q, notes_only), body


def pitch_title_key(subject):
    """The query title inside a pitch subject, so old and new subject formats compare equal."""
    s = subject.replace(WRITE_YOURSELF, '')
    s = re.sub(r'^\s*(re|fwd?):\s*', '', s, flags=re.I)
    s = re.sub(r'^HARO Pitch:\s*', '', s)
    s = re.split(r'\s+—\s+Nahid', s)[0]
    return re.sub(r'\W+', ' ', s).strip().lower()


def already_pitched(service):
    """Reply addresses and title keys of HARO pitches already in Drafts or sent in the last 60 days."""
    addresses, titles = set(), set()

    def note(headers):
        h = {x['name'].lower(): x['value'] for x in headers}
        if 'HARO Pitch' not in h.get('subject', ''):
            return
        titles.add(pitch_title_key(h['subject']))
        for addr in re.findall(r'[\w.+-]+@[\w-]+(?:\.[\w-]+)+', h.get('to', '')):
            addresses.add(addr.lower())

    token = None
    while True:
        page = service.users().drafts().list(userId='me', maxResults=100, pageToken=token).execute(num_retries=5)
        for d in page.get('drafts', []):
            msg = service.users().drafts().get(userId='me', id=d['id'], format='metadata').execute(num_retries=5)
            note(msg.get('message', {}).get('payload', {}).get('headers', []))
        token = page.get('nextPageToken')
        if not token:
            break
    sent = service.users().messages().list(
        userId='me', q='in:sent newer_than:60d "HARO Pitch"', maxResults=200).execute(num_retries=5)
    for s in sent.get('messages', []):
        msg = service.users().messages().get(userId='me', id=s['id'], format='metadata',
                                             metadataHeaders=['To', 'Subject']).execute(num_retries=5)
        note(msg.get('payload', {}).get('headers', []))
    return addresses, titles


def create_gmail_draft(service, to_email, subject, body_text):
    """Create a draft email in Gmail, sent from the address the HARO account uses."""
    message = MIMEText(body_text, 'plain', 'utf-8')
    if to_email and '@' in to_email and ' ' not in to_email and not to_email.startswith('http'):
        message['to'] = to_email
    message['from'] = PITCH_FROM
    message['subject'] = subject

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    draft_body = {
        'message': {
            'raw': raw_message
        }
    }

    draft = service.users().drafts().create(userId='me', body=draft_body).execute(num_retries=5)
    return draft


def get_processed_label_id(service):
    """Return the id of the Gmail label that marks a digest as done, creating it on first use."""
    for label in service.users().labels().list(userId='me').execute(num_retries=5).get('labels', []):
        if label['name'] == PROCESSED_LABEL:
            return label['id']
    created = service.users().labels().create(userId='me', body={
        'name': PROCESSED_LABEL,
        'labelListVisibility': 'labelShow',
        'messageListVisibility': 'show',
    }).execute(num_retries=5)
    print(f"[+] Created Gmail label '{PROCESSED_LABEL}'.")
    return created['id']


def mark_digest_processed(service, msg_id, label_id):
    """Label the digest as processed and mark it read.

    The label, not read status, is what stops a digest being pitched twice, so a digest
    opened on the phone before the run still gets pitched (2026-10-16's Morning Edition was
    opened before the run that would have pitched it).
    """
    try:
        service.users().messages().modify(
            userId='me',
            id=msg_id,
            body={'addLabelIds': [label_id], 'removeLabelIds': ['UNREAD']}
        ).execute(num_retries=5)
        print(f"     [+] Labelled digest '{PROCESSED_LABEL}' and marked it read.")
    except Exception as e:
        print(f"     [!] Could not label digest as processed: {e}")


def digest_search_query(query_days, include_processed=False):
    """Gmail search for HARO / media digests in the inbox, filtering out GitHub alerts."""
    label_filter = '' if include_processed else f'-label:{PROCESSED_LABEL_SEARCH} '
    return (
        f'{label_filter}in:inbox -from:me -from:notifications@github.com -subject:"Run failed" -subject:"[aiprofitlab-rgb" '
        '(from:haro OR from:connectively OR from:featured.com OR from:sourcebottle OR from:qwoted OR from:helpareporter '
        f'OR subject:HARO OR subject:Connectively OR subject:Featured OR subject:SourceBottle OR subject:Qwoted) newer_than:{query_days}d'
    )


# haro_agent.py's footprints. Its sidecar logs every 10-minute fire and the trigger rewrites the state
# file, so their age says whether that pipeline is alive; the state names what it handed over.
AGENT_STATE = os.path.expanduser('~/Developer/aiprofitlab-haro/runner/state/state.json')
AGENT_SIDECAR_LOG = os.path.expanduser('~/.gemini/antigravity/sidecar_data/aiprofitlab-haro/logs/sidecar.log')
AGENT_ALIVE_SECS = 20 * 60
WAKE_GRACE_SECS = 20 * 60


def awake_seconds():
    """Seconds since the Mac last booted or woke, or None when that can't be read (e.g. on GitHub)."""
    if sys.platform != 'darwin':
        return None
    import subprocess
    latest = 0
    for key in ('kern.boottime', 'kern.waketime'):
        try:
            out = subprocess.run(['sysctl', '-n', key], capture_output=True, text=True, timeout=5).stdout
        except (OSError, subprocess.SubprocessError):
            continue
        m = re.search(r'sec = (\d+)', out)
        if m:
            latest = max(latest, int(m.group(1)))
    return time.time() - latest if latest else None


def agent_handoff():
    """What haro_agent.py leaves to this fallback: (reason to skip this run, handed_over, in_job).

    handed_over is None when that pipeline is down, so every digest old enough is ours; while it is
    alive, only the digests it gave up on or couldn't parse are. in_job: digests of its open job.
    """
    try:
        with open(AGENT_STATE, encoding='utf-8') as f:
            st = json.load(f) or {}
    except (OSError, ValueError):
        st = {}
    in_job = {i for d in (st.get('job') or {}).get('digests', []) for i in d.get('ids', [])}
    beats = [os.path.getmtime(p) for p in (AGENT_STATE, AGENT_SIDECAR_LOG) if os.path.exists(p)]
    if beats and time.time() - max(beats) < AGENT_ALIVE_SECS and not st.get('gmail_down'):
        handed = (set(st.get('given_up') or {}) | set(st.get('not_ours') or {})) - in_job
        return ('' if handed else 'the Antigravity pipeline is running and has handed nothing over'), handed, in_job
    # Down, or not started yet: at login or wake both run at once, so give it its first runs.
    awake = awake_seconds()
    if awake is not None and awake < WAKE_GRACE_SECS:
        return f'the Mac woke {awake / 60:.0f} min ago; the Antigravity pipeline goes first', None, in_job
    return '', None, in_job


def run_haro_processor(query_days=7, dry_run=False, min_age_hours=0, defer_to_agent=False):
    """Main execution function.

    dry_run: also reads digests already labelled as processed, and writes the drafts it would
    create to .tmp/haro_dryrun/ instead of Gmail. Nothing in Gmail changes.
    min_age_hours: leave digests younger than this alone. The scheduled runs pass 3, because
    haro_agent.py (Antigravity + Claude) takes a new digest within about 10 minutes when the
    Mac is on; what it hasn't labelled by then, this fallback drafts.
    defer_to_agent: the Mac's 30-minute run. While haro_agent.py is alive, take only the digests
    it handed over (no age wait); never touch its open job; skip the first minutes after a wake.
    """
    handed, in_job = None, set()
    if defer_to_agent and not dry_run:
        reason, handed, in_job = agent_handoff()
        if reason:
            print(f"{datetime.datetime.now():%Y-%m-%d %H:%M} fallback idle: {reason}")
            return

    print("=" * 60)
    print("AI PROFIT LAB — AUTOMATED HARO & MEDIA PITCH ASSISTANT" + ("  [DRY RUN]" if dry_run else ""))
    print(f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    api_key = get_gemini_api_key()
    if not api_key:
        print("[ERROR] GEMINI_API_KEY is required. Please add it to .env or environment.")
        sys.exit(1)

    service = get_gmail_service()
    print("[+] Successfully connected to Gmail API.")
    processed_label_id = get_processed_label_id(service)

    query = digest_search_query(query_days, include_processed=dry_run)
    print(f"[*] Searching inbox with query: '{query}'...")
    messages = service.users().messages().list(userId='me', q=query, maxResults=40).execute(num_retries=5).get('messages', [])
    if not messages:
        print(f"[-] No unprocessed media digest emails found in the last {query_days} days.")
        return

    # HARO sends the same digest to both subscribed addresses; read one copy, label both.
    groups = {}
    young = agents = 0
    for msg_meta in messages:
        if msg_meta['id'] in in_job or (handed is not None and msg_meta['id'] not in handed):
            agents += 1
            continue  # haro_agent.py has it, or is alive and will take it
        msg_data = service.users().messages().get(userId='me', id=msg_meta['id'], format='full').execute(num_retries=5)
        if not dry_run and processed_label_id in msg_data.get('labelIds', []):
            continue  # labelled since the search ran (e.g. by an overlapping run)
        if handed is None and min_age_hours and time.time() - int(msg_data.get('internalDate', 0)) / 1000 < min_age_hours * 3600:
            young += 1
            continue  # haro_agent.py's to take
        headers = {h['name'].lower(): h['value'] for h in msg_data.get('payload', {}).get('headers', [])}
        if 'github.com' in headers.get('from', '').lower() or 'run failed' in headers.get('subject', '').lower():
            continue
        groups.setdefault(headers.get('subject', '(No Subject)'), []).append((msg_data, headers))
    print(f"[+] Found {len(messages)} unprocessed media digest email(s): {len(groups)} distinct digest(s)."
          + (f" Left {young} younger than {min_age_hours}h to the Antigravity pipeline." if young else "")
          + (f" Left {agents} the Antigravity pipeline is handling." if agents else ""))

    pitched_addresses, pitched_titles = already_pitched(service)
    now = datetime.datetime.now(datetime.timezone.utc)
    out_dir = os.path.join(BASE_DIR, '.tmp', 'haro_dryrun', now.strftime('%Y%m%d-%H%M%S'))
    total_drafts_created = 0

    for subject, copies in groups.items():
        msg_data, headers = copies[0]
        print(f"\n---> Processing Digest: '{subject}' ({headers.get('date', '')}) x{len(copies)}")
        body_text = extract_message_body(msg_data.get('payload', {}))
        try:
            received = email.utils.parsedate_to_datetime(headers.get('date', ''))
        except (TypeError, ValueError):
            received = now

        queries = parse_haro_digest(body_text)
        if not queries and len(body_text) >= 100:
            print("     [*] Not in HARO's format; listing its queries with Gemini...")
            queries = extract_queries_with_gemini(body_text, api_key)
        if not queries:
            print("     [-] No journalist queries found in this email.")
            if not dry_run:
                for c, _ in copies:
                    mark_digest_processed(service, c['id'], processed_label_id)
            continue

        for q in queries:
            q['deadline_utc'] = parse_deadline(q['deadline_raw'], received)
        active = [q for q in queries if q['deadline_utc'] is None or q['deadline_utc'] > now + MIN_LEAD]
        print(f"     [*] {len(queries)} queries, {len(queries) - len(active)} past their deadline. "
              f"Screening {len(active)} with Gemini...")
        decisions = screen_queries(active, api_key)
        if decisions is None:
            print("     [!] Gemini screening failed. Leaving this digest for the next run.")
            continue

        chosen = []
        for q in active:
            d = decisions[q['id']]
            pitch = d.get('decision') == 'PITCH' and int(d.get('fit') or 0) >= 3
            print(f"       {'PITCH' if pitch else 'skip '} fit {d.get('fit')}  {q['title'][:70]}  ({q['outlet']})"
                  f"\n                    {d.get('reason', '')}")
            if pitch:
                q['notes_only'] = q['no_ai'] or bool(d.get('ai_replies_forbidden'))
                chosen.append(q)
        print(f"     [+] Queries Found: {len(queries)} | To pitch: {len(chosen)}")

        all_ok = True
        for q in sorted(chosen, key=lambda x: x['deadline_utc'] or now + datetime.timedelta(days=365)):
            if q['email'].lower() in pitched_addresses or pitch_title_key(q['title']) in pitched_titles:
                print(f"     [SKIP] Already drafted or sent: '{q['title']}'")
                continue
            result = write_pitch(q, api_key, q['notes_only'])
            if not result:
                print(f"     [!] Gemini could not draft '{q['title']}'. The digest stays unprocessed for a retry.")
                all_ok = False
                continue
            draft_subject, draft_body = build_draft(q, result, q['notes_only'])
            print(f"\n     [+] DRAFTING {'TALKING POINTS' if q['notes_only'] else 'PITCH'}:")
            print(f"         • Title: {q['title']}")
            print(f"         • Publication: {q['outlet']}")
            print(f"         • Target: {q['email'] or q['profile_url'] or 'Portal Submission'}")
            print(f"         • Subject: {draft_subject}")
            if dry_run:
                os.makedirs(out_dir, exist_ok=True)
                name = re.sub(r'[^a-z0-9]+', '-', q['title'].lower())[:60].strip('-')
                with open(os.path.join(out_dir, f"{name}.txt"), 'w', encoding='utf-8') as f:
                    f.write(f"To: {q['email']}\nFrom: {PITCH_FROM}\nSubject: {draft_subject}\n\n{draft_body}")
                print(f"         [DRY RUN] Written to {out_dir}/{name}.txt")
            else:
                try:
                    draft_res = create_gmail_draft(service, q['email'], draft_subject, draft_body)
                    print(f"         [SUCCESS] Created Gmail Draft (ID: {draft_res.get('id')})")
                except Exception as e:
                    print(f"         [ERROR] Failed to create draft: {e}")
                    all_ok = False
                    continue
            pitched_addresses.add(q['email'].lower())
            pitched_titles.add(pitch_title_key(q['title']))
            total_drafts_created += 1

        # Label every copy of this digest as processed now that its pitches are drafted
        if all_ok and not dry_run:
            for c, _ in copies:
                mark_digest_processed(service, c['id'], processed_label_id)

    print("\n" + "=" * 60)
    print(f"[SUMMARY] Routine complete. Total new pitches drafted: {total_drafts_created}"
          + (f" (dry run, see {out_dir})" if dry_run and total_drafts_created else ""))
    print("=" * 60)


def build_deadline_index(service, days=45):
    """Map each reply address, and each title key, seen in the last `days` of HARO digests to its
    deadline (UTC). Titles cover drafts with no address, or with one the old all-in-one Gemini
    step made up (2026-10-03: reply+nix-data-ai@..., where the query said pr@n-ix.com)."""
    index = {}
    msgs = service.users().messages().list(
        userId='me', q=f'from:haro@helpareporter.com newer_than:{days}d', maxResults=500).execute(num_retries=5).get('messages', [])
    seen_subjects = set()
    for meta in msgs:
        msg = service.users().messages().get(userId='me', id=meta['id'], format='full').execute(num_retries=5)
        headers = {h['name'].lower(): h['value'] for h in msg['payload']['headers']}
        if headers.get('subject') in seen_subjects:
            continue
        seen_subjects.add(headers.get('subject'))
        received = email.utils.parsedate_to_datetime(headers['date'])
        for q in parse_haro_digest(extract_message_body(msg['payload'])):
            deadline = parse_deadline(q['deadline_raw'], received)
            if q['email']:
                index[q['email'].lower()] = deadline
            index[pitch_title_key(q['title'])] = deadline
    return index


def delete_expired_drafts(apply=False):
    """Delete HARO pitch drafts whose deadline has passed; with apply=False only list them.

    The deadline comes from the draft's own notes (the "(... UTC)" stamp, or the older
    "[DEADLINE: ...]" line). When neither is readable it is looked up by the draft's reply
    address in the last 45 days of digests. A draft whose deadline can't be found is kept.
    Each deleted draft is saved first to .tmp/haro_deleted_drafts.jsonl, because the Gmail
    API deletes drafts permanently rather than moving them to Trash.
    """
    service = get_gmail_service()
    now = datetime.datetime.now(datetime.timezone.utc)
    drafts, token = [], None
    while True:
        page = service.users().drafts().list(userId='me', maxResults=100, pageToken=token).execute(num_retries=5)
        drafts += page.get('drafts', [])
        token = page.get('nextPageToken')
        if not token:
            break

    rows, index = [], None
    for d in drafts:
        full = service.users().drafts().get(userId='me', id=d['id'], format='full').execute(num_retries=5)
        msg = full.get('message', {})
        headers = {h['name'].lower(): h['value'] for h in msg.get('payload', {}).get('headers', [])}
        subject = headers.get('subject', '')
        if 'HARO Pitch' not in subject:
            continue
        body = extract_message_body(msg.get('payload', {}))
        created = datetime.datetime.fromtimestamp(int(msg.get('internalDate', 0)) / 1000, datetime.timezone.utc)
        deadline = None
        stamp = re.search(r'\((\d{4}-\d{2}-\d{2} \d{2}:\d{2}) UTC\)', body)
        if stamp:
            deadline = datetime.datetime.strptime(stamp.group(1), '%Y-%m-%d %H:%M').replace(tzinfo=datetime.timezone.utc)
        if deadline is None:
            old = re.search(r'\[DEADLINE:\s*([^\]]+)\]', body)
            deadline = parse_deadline(old.group(1), created) if old else None
        to = (re.findall(r'[\w.+-]+@[\w-]+(?:\.[\w-]+)+', headers.get('to', '')) or [''])[0].lower()
        if deadline is None:
            if index is None:
                print("[*] Looking up deadlines in the last 45 days of HARO digests...")
                index = build_deadline_index(service)
            deadline = index.get(to) or index.get(pitch_title_key(subject))
        state = 'unknown' if deadline is None else ('expired' if deadline <= now else 'active')
        rows.append((state, deadline, subject, d['id'], full))

    for state, deadline, subject, _, _ in sorted(rows, key=lambda r: (r[0], r[1] or now)):
        when = f"{deadline:%Y-%m-%d %H:%M} UTC" if deadline else "deadline not found"
        print(f"  {state:8} {when:22} {subject[:90]}")
    expired = [r for r in rows if r[0] == 'expired']
    print(f"[*] {len(rows)} HARO drafts: {len(expired)} expired, "
          f"{sum(r[0] == 'active' for r in rows)} still open, {sum(r[0] == 'unknown' for r in rows)} unknown (kept).")
    if not apply:
        print("[*] Nothing deleted. Run again with --apply to delete the expired drafts.")
        return
    backup = os.path.join(BASE_DIR, '.tmp', 'haro_deleted_drafts.jsonl')
    os.makedirs(os.path.dirname(backup), exist_ok=True)
    with open(backup, 'a', encoding='utf-8') as f:
        for _, deadline, subject, draft_id, full in expired:
            f.write(json.dumps({'deleted_at': now.isoformat(), 'deadline': deadline.isoformat(),
                                'subject': subject, 'draft': full}) + "\n")
    for _, _, subject, draft_id, _ in expired:
        service.users().drafts().delete(userId='me', id=draft_id).execute(num_retries=5)
    print(f"[+] Deleted {len(expired)} expired drafts. Copies saved to {backup}")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('days', nargs='?', type=int, default=7, help='how many days of digests to read (default 7)')
    parser.add_argument('--dry-run', action='store_true',
                        help='write would-be drafts to .tmp/haro_dryrun/ and change nothing in Gmail')
    parser.add_argument('--delete-expired', action='store_true',
                        help='list HARO drafts whose deadline has passed (add --apply to delete them)')
    parser.add_argument('--apply', action='store_true', help='with --delete-expired: actually delete')
    parser.add_argument('--min-age-hours', type=float, default=0,
                        help='skip digests younger than this (the scheduled fallback runs pass 3)')
    parser.add_argument('--defer-to-agent', action='store_true',
                        help="the Mac's 30-minute run: take only what haro_agent.py leaves, and nothing right after a wake")
    args = parser.parse_args()
    if args.delete_expired:
        delete_expired_drafts(apply=args.apply)
    else:
        run_haro_processor(query_days=args.days, dry_run=args.dry_run, min_age_hours=args.min_age_hours,
                           defer_to_agent=args.defer_to_agent)
