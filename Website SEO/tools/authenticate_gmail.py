#!/usr/bin/env python3
"""
Gmail Authentication Helper for AI Profit Lab.
Performs interactive OAuth authentication to generate or renew token.json.
Uses port 8080 or dynamic port and opens the authorization URL in your browser.
"""

import os
import sys
import json
import webbrowser

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify'
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_FILE = os.path.join(BASE_DIR, 'credentials.json')
TOKEN_FILE = os.path.join(BASE_DIR, 'token.json')


def authenticate():
    print("=" * 60)
    print("AI PROFIT LAB — GMAIL OAUTH AUTHENTICATION HELPER")
    print("=" * 60)

    if not os.path.exists(CREDENTIALS_FILE):
        print(f"[ERROR] Missing credentials file: {CREDENTIALS_FILE}")
        print("Please place credentials.json in the project root.")
        sys.exit(1)

    print(f"[*] Reading client secrets from: {CREDENTIALS_FILE}")
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)

    print("[*] Starting local OAuth server...")
    print("[*] A browser window should open automatically.")
    print("    If it does not, copy and paste the URL displayed into your browser.")
    print("-" * 60)

    try:
        # Try port 8080 first, fallback to dynamic port
        creds = flow.run_local_server(port=8080, prompt='consent', access_type='offline')
    except Exception as e:
        print(f"[*] Port 8080 unavailable ({e}), trying dynamic port...")
        creds = flow.run_local_server(port=0, prompt='consent', access_type='offline')

    # Save credentials to token.json
    with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
        f.write(creds.to_json())

    print("-" * 60)
    print(f"[+] Successfully authenticated and saved token to: {TOKEN_FILE}")

    # Verify connection and scopes
    try:
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        email_addr = profile.get('emailAddress', 'unknown')
        print(f"[+] Connected to Gmail as: {email_addr}")
        print(f"[+] Total messages in account: {profile.get('messagesTotal', 'N/A')}")
    except Exception as e:
        print(f"[!] Warning: Could not verify Gmail profile: {e}")

    print("=" * 60)
    print("OAuth setup complete! The HARO processor can now access Gmail.")
    print("=" * 60)


if __name__ == '__main__':
    authenticate()
