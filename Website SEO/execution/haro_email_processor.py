#!/usr/bin/env python3
"""
HARO & Media Query Email Processor for AI Profit Lab.
Scans incoming HARO / Connectively / Featured / Qwoted / SourceBottle digests,
extracts relevant queries, evaluates deadlines, generates expert pitches with Gemini,
and saves ready-to-review drafts directly in Gmail.
"""

import os
import re
import sys
import json
import base64
import datetime
from email.mime.text import MIMEText
import urllib.request
import urllib.error

# Google Client Libraries
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
except ImportError as e:
    print(f"Missing Google client libraries: {e}")
    print("Please install via: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    sys.exit(1)

# Scopes needed: Read emails, create drafts, and modify labels (mark as read)
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify'
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_FILE = os.path.join(BASE_DIR, 'credentials.json')
TOKEN_FILE = os.path.join(BASE_DIR, 'token.json')
ENV_FILE = os.path.join(BASE_DIR, '.env')


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
            try:
                print("[*] Refreshing expired Gmail OAuth access token...")
                creds.refresh(Request())
                with open(TOKEN_FILE, 'w', encoding='utf-8') as token:
                    token.write(creds.to_json())
                print("[+] Successfully refreshed and saved token.json.")
            except Exception as e:
                print(f"[!] Failed to refresh token: {e}")
                creds = None

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


def call_gemini(prompt, api_key):
    """Call Google Gemini Flash endpoint via requests with robust retries."""
    import requests
    import time

    # Working and available models
    models = [
        'gemini-flash-latest',
        'gemini-flash-lite-latest',
        'gemini-3-flash-preview',
        'gemini-3.1-flash-lite-preview'
    ]

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 16384,
            "responseMimeType": "application/json"
        }
    }

    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        for attempt in range(3):
            try:
                res = requests.post(url, json=payload, timeout=60)
                if res.status_code == 200:
                    res_data = res.json()
                    parts = res_data.get('candidates', [{}])[0].get('content', {}).get('parts', [])
                    text = "".join([p.get('text', '') for p in parts if 'text' in p]).strip()

                    parsed = safe_parse_json(text)
                    if parsed:
                        return parsed
                    else:
                        print(f"[!] JSON parsing error on {model}")
                        print(f"    Raw preview: {text[:200]} ... {text[-100:]}")
                        return None
                elif res.status_code in [429, 503]:
                    time.sleep(2 * (attempt + 1))
                    continue
                elif res.status_code == 404:
                    # Model not found, advance to next candidate model
                    break
                else:
                    print(f"[!] Gemini Error ({model}): {res.status_code} - {res.text[:200]}")
                    break
            except Exception as e:
                time.sleep(2)
                continue

    return None


def analyze_email_and_draft_pitches(email_body, subject, date_received, api_key):
    """
    Use Gemini to parse HARO digest, filter relevant topics, check deadlines,
    and generate ready-to-use pitch drafts.
    """
    current_time_str = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    # Send up to 80,000 characters to prevent clipping queries in long digests
    trimmed_body = email_body[:80000]

    prompt = f"""
You are an expert PR pitch strategist for Nahid, Founder of AI Profit Lab (International Gulf Lotus SPC, https://aiprofitlab.io).
Current Date/Time: {current_time_str}
Email Subject: {subject}
Email Received: {date_received}

EMAIL CONTENT:
---
{trimmed_body}
---

YOUR TASK:
1. Parse the email digest into individual journalist queries (from HARO, Connectively, Featured, SourceBottle, Qwoted, etc.).
2. For each query:
   - Check deadline: If the deadline has already passed relative to {current_time_str}, mark 'is_expired': true. (If only a date is given without a specific time, assume 23:59 on that day).
   - Check topic relevance to AI Profit Lab:
     * ACCEPT: AI, Machine Learning, Generative AI, LLMs, Automation, RPA, Web Design, UX/UI, Conversion Optimization, SEO, Tech Business, Digital Transformation, Cloud Systems.
     * REJECT: Healthcare/medicine, beauty, fashion, personal investing, crypto trading, real estate, general lifestyles, non-tech topics.
3. For all ACTIVE (not expired) and RELEVANT queries:
   Draft a winning, concise PR pitch tailored to the query adhering strictly to these PR guidelines:
   * Subject Line: "HARO Pitch: [Query Title] — Nahid, AI Profit Lab"
   * Opening: 1 clear sentence with Nahid's title and direct qualifications.
   * Soundbites: 2-3 concise bullet points with concrete, original, actionable insights ready for the journalist to copy-paste.
   * Bio & Signoff:
     Nahid
     Founder, AI Profit Lab (https://aiprofitlab.io)
     A brand of International Gulf Lotus SPC
     Headshot & further insights available upon request.
   * Pitch Draft Formatting:
     At the very top of draft_body, include reference details:
     [OUTLET: <Publication>]
     [QUERY: <Query Title>]
     [DEADLINE: <Deadline>]
     [SUBMIT TO: <Journalist Email or Submission Portal URL>]
     ---

Return JSON in this EXACT schema (do NOT include list of rejected queries):
{{
  "total_queries_found": int,
  "skipped_queries_count": int,
  "relevant_active_queries": [
    {{
      "query_title": "string",
      "publication": "string",
      "journalist_name": "string",
      "journalist_email": "string",
      "submission_url": "string",
      "deadline_str": "string",
      "is_expired": false,
      "is_relevant": true,
      "draft_subject": "string",
      "draft_body": "string"
    }}
  ]
}}
"""
    return call_gemini(prompt, api_key)


def create_gmail_draft(service, to_email, subject, body_text):
    """Create a draft email in Gmail."""
    message = MIMEText(body_text, 'plain', 'utf-8')
    if to_email and '@' in to_email and ' ' not in to_email and not to_email.startswith('http'):
        message['to'] = to_email
    message['from'] = 'ai.profit.lab2026@gmail.com'
    message['subject'] = subject

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    draft_body = {
        'message': {
            'raw': raw_message
        }
    }

    draft = service.users().drafts().create(userId='me', body=draft_body).execute()
    return draft


def mark_email_as_read(service, msg_id):
    """Mark the email as read in Gmail by removing the UNREAD label."""
    try:
        service.users().messages().modify(
            userId='me',
            id=msg_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        print("     [+] Marked digest email as READ in inbox.")
    except Exception as e:
        print(f"     [!] Could not mark email as read: {e}")


def run_haro_processor(query_days=7):
    """Main execution function."""
    print("=" * 60)
    print("AI PROFIT LAB — AUTOMATED HARO & MEDIA PITCH ASSISTANT")
    print(f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    api_key = get_gemini_api_key()
    if not api_key:
        print("[ERROR] GEMINI_API_KEY is required. Please add it to .env or environment.")
        return

    service = get_gmail_service()
    print("[+] Successfully connected to Gmail API.")

    # Search for unread HARO / media digest emails strictly in inbox, filtering out GitHub alerts
    query = (
        'is:unread in:inbox -from:me -from:notifications@github.com -subject:"Run failed" -subject:"[aiprofitlab-rgb" '
        '(from:haro OR from:connectively OR from:featured.com OR from:sourcebottle OR from:qwoted OR from:helpareporter '
        f'OR subject:HARO OR subject:Connectively OR subject:Featured OR subject:SourceBottle OR subject:Qwoted) newer_than:{query_days}d'
    )
    print(f"[*] Searching inbox with query: '{query}'...")

    results = service.users().messages().list(userId='me', q=query, maxResults=20).execute()
    messages = results.get('messages', [])

    if not messages:
        print(f"[-] No unread media digest emails found in the last {query_days} days.")
        return

    print(f"[+] Found {len(messages)} unread media digest email(s). Processing...")

    # Fetch existing drafts to avoid duplicating pitches
    existing_draft_subjects = set()
    try:
        drafts_list = service.users().drafts().list(userId='me', maxResults=50).execute()
        for d in drafts_list.get('drafts', []):
            d_data = service.users().drafts().get(userId='me', id=d['id'], format='metadata').execute()
            d_headers = d_data.get('message', {}).get('payload', {}).get('headers', [])
            d_subj = next((h['value'] for h in d_headers if h['name'].lower() == 'subject'), '')
            if d_subj:
                existing_draft_subjects.add(d_subj.strip().lower())
    except Exception as e:
        print(f"[*] Note: Could not fetch existing drafts list ({e})")

    total_drafts_created = 0

    for msg_meta in messages:
        msg_id = msg_meta['id']
        msg_data = service.users().messages().get(userId='me', id=msg_id, format='full').execute()

        headers = msg_data.get('payload', {}).get('headers', [])
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '(No Subject)')
        date_header = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
        sender_header = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')

        # Safeguard: Skip any obvious GitHub notification that slipped through
        if 'github.com' in sender_header.lower() or 'run failed' in subject.lower():
            print(f"     [SKIP] Skipping non-digest message: '{subject}'")
            continue

        print(f"\n---> Processing Digest: '{subject}' ({date_header})")
        body_text = extract_message_body(msg_data.get('payload', {}))

        if not body_text or len(body_text) < 100:
            print("     [!] Email body is empty or too short. Skipping.")
            mark_email_as_read(service, msg_id)
            continue

        print(f"     [*] Analyzing queries with Gemini (Length: {len(body_text)} chars)...")
        analysis = analyze_email_and_draft_pitches(body_text, subject, date_header, api_key)

        if not analysis:
            print("     [!] Could not parse email analysis from Gemini.")
            continue

        found = analysis.get('total_queries_found', 0)
        active_relevant = analysis.get('relevant_active_queries', [])
        skipped = analysis.get('skipped_queries_count', 0)

        print(f"     [+] Queries Found: {found} | Relevant & Active: {len(active_relevant)} | Skipped: {skipped}")

        for item in active_relevant:
            q_title = item.get('query_title', 'Inquiry')
            to_addr = item.get('journalist_email') or ''
            sub_url = item.get('submission_url') or ''
            pub = item.get('publication', 'Media Outlet')
            draft_sub = item.get('draft_subject', f"HARO Pitch: {q_title} — Nahid, AI Profit Lab")
            draft_body = item.get('draft_body', '')

            # Check if this exact pitch subject is already in drafts
            if draft_sub.strip().lower() in existing_draft_subjects:
                print(f"     [SKIP] Draft already exists for: '{draft_sub}'")
                continue

            print(f"\n     [+] DRAFTING PITCH:")
            print(f"         • Title: {q_title}")
            print(f"         • Publication: {pub}")
            print(f"         • Target: {to_addr or sub_url or 'Portal Submission'}")
            print(f"         • Subject: {draft_sub}")

            try:
                draft_res = create_gmail_draft(service, to_addr, draft_sub, draft_body)
                draft_id = draft_res.get('id')
                print(f"         [SUCCESS] Created Gmail Draft (ID: {draft_id})")
                existing_draft_subjects.add(draft_sub.strip().lower())
                total_drafts_created += 1
            except Exception as e:
                print(f"         [ERROR] Failed to create draft: {e}")

        # Mark this email as read now that it has been fully processed
        mark_email_as_read(service, msg_id)

    print("\n" + "=" * 60)
    print(f"[SUMMARY] Routine complete. Total new pitches drafted: {total_drafts_created}")
    print("=" * 60)


if __name__ == '__main__':
    days = 7
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        days = int(sys.argv[1])
    run_haro_processor(query_days=days)
