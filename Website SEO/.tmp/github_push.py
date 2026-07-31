#!/usr/bin/env python3
"""
Push index-new.html to a new GitHub repo and enable GitHub Pages.
"""
import urllib.request
import urllib.error
import json
import base64
import sys
import os

TOKEN = "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"
REPO_NAME = "apl-preview"
FILE_PATH = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/en/index-new.html"
BRANCH = "main"

headers = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "Content-Type": "application/json",
    "User-Agent": "python3"
}

def gh_request(method, url, data=None):
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code

# Step 1: Get username
print("Step 1: Getting GitHub username...")
user, status = gh_request("GET", "https://api.github.com/user")
if status != 200:
    print(f"ERROR: Could not authenticate. Status {status}: {user}")
    sys.exit(1)
username = user["login"]
print(f"  Username: {username}")

# Step 2: Check if repo already exists, delete if so
print(f"Step 2: Checking if repo '{REPO_NAME}' exists...")
existing, status = gh_request("GET", f"https://api.github.com/repos/{username}/{REPO_NAME}")
if status == 200:
    print(f"  Repo already exists, deleting it first...")
    _, del_status = gh_request("DELETE", f"https://api.github.com/repos/{username}/{REPO_NAME}")
    print(f"  Deleted. Status: {del_status}")

# Step 3: Create new public repo
print(f"Step 3: Creating new public repo '{REPO_NAME}'...")
repo_data = {
    "name": REPO_NAME,
    "description": "AI Profit Lab - Homepage Preview",
    "private": False,
    "auto_init": True
}
repo, status = gh_request("POST", "https://api.github.com/user/repos", repo_data)
if status not in (201, 200):
    print(f"ERROR: Could not create repo. Status {status}: {repo}")
    sys.exit(1)
print(f"  Repo created: {repo['html_url']}")

# Step 4: Read and encode the HTML file
print("Step 4: Reading index-new.html...")
with open(FILE_PATH, "rb") as f:
    content = base64.b64encode(f.read()).decode()
print(f"  File read successfully ({len(content)} chars encoded)")

# Step 5: Push the file as index.html (GitHub Pages serves index.html)
import time
time.sleep(2)  # wait for repo to initialize

print("Step 5: Pushing file as index.html...")
file_data = {
    "message": "Add homepage preview",
    "content": content,
    "branch": BRANCH
}
result, status = gh_request("PUT", f"https://api.github.com/repos/{username}/{REPO_NAME}/contents/index.html", file_data)
if status not in (201, 200):
    print(f"ERROR: Could not push file. Status {status}: {result}")
    sys.exit(1)
print(f"  File pushed successfully!")

# Step 6: Enable GitHub Pages
print("Step 6: Enabling GitHub Pages...")
pages_data = {
    "source": {
        "branch": BRANCH,
        "path": "/"
    }
}
pages, status = gh_request("POST", f"https://api.github.com/repos/{username}/{REPO_NAME}/pages", pages_data)
if status not in (201, 200, 409):
    print(f"  Warning: Could not enable GitHub Pages. Status {status}: {pages}")
else:
    print(f"  GitHub Pages enabled!")

# Final: Print the URLs
print("\n" + "="*60)
print(f"✅ DONE!")
print(f"GitHub Repo:   https://github.com/{username}/{REPO_NAME}")
print(f"Live Preview:  https://{username}.github.io/{REPO_NAME}/")
print("="*60)
print("\nNote: GitHub Pages takes 1-3 minutes to go live after first deploy.")
