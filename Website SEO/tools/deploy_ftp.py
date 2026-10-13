#!/usr/bin/env python3
"""
High-Performance Resilient FTP Deployment Script for AI Profit Lab
------------------------------------------------------------------
Synchronizes public_html directly to Hostinger FTP.
- Uploads the files changed between the LAST SUCCESSFUL DEPLOY and HEAD. The
  server keeps that commit in /.deployed-commit, written only after a run with
  zero errors, so a failed or skipped deploy is caught up by the next one.
  (Diffing HEAD~1..HEAD, as this used to, silently skipped every commit but the
  last one in a push, and the daily publisher ran it BEFORE committing, so each
  new article reached the server a day late, or never.)
- Bulletproof CWD-based upload preserving directory context for Hostinger
- Automatic retry and socket reconnection on transient network issues

    python3 tools/deploy_ftp.py                  # since the server's marker (else HEAD~1)
    python3 tools/deploy_ftp.py --base <sha>     # fallback base when there is no marker yet
"""

import argparse

import os
import sys
import io
import json
import time
import hashlib
import ftplib
import subprocess
from pathlib import Path

# Files/folders to exclude from FTP upload
EXCLUDE_PATTERNS = {
    ".git",
    ".github",
    ".DS_Store",
    ".ds-store",
    "__pycache__",
    "node_modules",
    ".agent",
    ".agents",
    ".tmp",
    ".impeccable",
    ".vscode",
}

EXCLUDE_EXTENSIONS = {
    ".py",
    ".pyc",
    ".sh",
    ".gs",
    ".env",
    ".log",
}


def should_exclude(rel_path_str):
    parts = rel_path_str.replace("\\", "/").split("/")
    for part in parts:
        if part in EXCLUDE_PATTERNS or part.startswith(".git"):
            return True
    ext = os.path.splitext(rel_path_str)[1].lower()
    if ext in EXCLUDE_EXTENSIONS:
        return True
    return False


def compute_local_manifest(local_dir):
    """Computes sizes and MD5 hashes for all valid local files."""
    manifest = {}
    all_files = []
    for root, dirs, files in os.walk(local_dir):
        for f in files:
            full_path = Path(root) / f
            rel_path = full_path.relative_to(local_dir)
            rel_str = str(rel_path).replace("\\", "/")
            if not should_exclude(rel_str):
                try:
                    size = full_path.stat().st_size
                    h = hashlib.md5()
                    with open(full_path, "rb") as fp:
                        while chunk := fp.read(65536):
                            h.update(chunk)
                    manifest[rel_str] = {
                        "size": size,
                        "md5": h.hexdigest(),
                    }
                    all_files.append((full_path, rel_str, size))
                except Exception as e:
                    print(f"  [!] Warning reading local file {rel_str}: {e}")
    return manifest, all_files


MARKER = ".deployed-commit"
SITE_PREFIX = "Website SEO/public_html/"


def git(repo_root, *args):
    return subprocess.run(["git", *args], cwd=repo_root, capture_output=True, text=True)


def is_commit(repo_root, sha):
    return bool(sha) and set(sha) != {"0"} and git(repo_root, "cat-file", "-e", f"{sha}^{{commit}}").returncode == 0


def read_marker(ftp, initial_cwd):
    buf = io.BytesIO()
    try:
        ftp.cwd(initial_cwd)
        ftp.retrbinary(f"RETR {MARKER}", buf.write)
        return buf.getvalue().decode().strip()
    except Exception:
        return None


def write_marker(ftp, initial_cwd, sha):
    ftp.cwd(initial_cwd)
    ftp.storbinary(f"STOR {MARKER}", io.BytesIO(sha.encode()))


def get_git_diff_files(repo_root, base):
    """public_html-relative paths added or modified between base and HEAD."""
    res = git(repo_root, "-c", "core.quotePath=false", "diff", "--name-only", "--diff-filter=ACMRT", base, "HEAD",
              "--", SITE_PREFIX)
    if res.returncode != 0:
        print(f"  [!] git diff {base[:7]}..HEAD failed: {res.stderr.strip()}")
        return None
    changed = set()
    for line in res.stdout.splitlines():
        line = line.strip().strip('"').replace("\\", "/")
        if line.startswith(SITE_PREFIX):
            rel = line[len(SITE_PREFIX):]
            if not should_exclude(rel):
                changed.add(rel)
    print(f"[+] Git diff {base[:7]}..HEAD: {len(changed)} changed web files.")
    return changed


def connect_ftp(server, user, password, port=21, timeout=60):
    print(f"[*] Connecting to FTP server: {server}:{port} as {user}...")
    ftp = ftplib.FTP(timeout=timeout)
    ftp.connect(server, int(port))
    ftp.login(user, password)
    ftp.set_pasv(True)
    welcome = ftp.getwelcome().strip().replace("\n", " ")
    print(f"[+] Connected: {welcome}")
    return ftp


def ensure_remote_dir_hierarchy(ftp, initial_cwd, target_dir_rel, known_dirs):
    """Creates nested directory hierarchy relative to initial_cwd and caches it."""
    if not target_dir_rel or target_dir_rel in (".", "/"):
        return
    clean_dir = target_dir_rel.replace("\\", "/").strip("/")
    if clean_dir in known_dirs:
        return

    ftp.cwd(initial_cwd)
    parts = [p for p in clean_dir.split("/") if p and p != "."]
    curr = ""
    for part in parts:
        curr = f"{curr}/{part}" if curr else part
        if curr not in known_dirs:
            try:
                ftp.cwd(curr)
                known_dirs.add(curr)
                ftp.cwd(initial_cwd)
            except ftplib.error_perm:
                try:
                    ftp.mkd(curr)
                    known_dirs.add(curr)
                    print(f"  [+] Created remote directory: {curr}")
                except Exception:
                    known_dirs.add(curr)
                finally:
                    ftp.cwd(initial_cwd)


def deploy(base_arg=None):
    start_time = time.time()
    server = os.environ.get("FTP_SERVER")
    user = os.environ.get("FTP_USERNAME")
    password = os.environ.get("FTP_PASSWORD")
    port = int(os.environ.get("FTP_PORT", 21))

    if not all([server, user, password]):
        print("[!] Error: FTP_SERVER, FTP_USERNAME, or FTP_PASSWORD environment variables are missing.")
        sys.exit(1)

    # Determine local public_html directory
    script_dir = Path(__file__).resolve().parent
    local_dir = script_dir.parent / "public_html"
    if not local_dir.exists():
        local_dir = Path("Website SEO/public_html").resolve()
    if not local_dir.exists():
        local_dir = Path("public_html").resolve()

    if not local_dir.exists():
        print(f"[!] Error: Local directory '{local_dir}' does not exist.")
        sys.exit(1)

    repo_root = local_dir.parent
    if not (repo_root / ".git").exists() and (repo_root.parent / ".git").exists():
        repo_root = repo_root.parent

    print(f"[*] Local source directory: {local_dir}")

    # Step 1: Compute local manifest
    print("[*] Indexing local files...")
    local_manifest, all_files = compute_local_manifest(local_dir)
    print(f"[+] Local files indexed: {len(local_manifest)} files in {time.time() - start_time:.2f}s")

    # Step 2: pick the diff base: the server's marker, else --base, else HEAD~1
    head = git(repo_root, "rev-parse", "HEAD").stdout.strip()
    ftp = connect_ftp(server, user, password, port)
    initial_cwd = ftp.pwd()
    marker = read_marker(ftp, initial_cwd)
    if is_commit(repo_root, marker) and marker != head and \
            git(repo_root, "merge-base", "--is-ancestor", "HEAD", marker).returncode == 0:
        # Re-running an old workflow run is how the site was once rolled back
        # four commits (see the deploy-failure notes). Refuse instead.
        ftp.quit()
        print(f"[!] Refusing to deploy {head[:7]}: the server already has the newer {marker[:7]}. "
              "Deploy the tip of main (Run workflow), never re-run an old run.")
        sys.exit(1)
    if is_commit(repo_root, marker):
        base, why = marker, "last successful deploy (server marker)"
    elif is_commit(repo_root, base_arg):
        base, why = base_arg, "--base (no usable server marker)"
    elif is_commit(repo_root, "HEAD~1"):
        base, why = git(repo_root, "rev-parse", "HEAD~1").stdout.strip(), "HEAD~1 (no marker, no --base)"
    else:
        base, why = None, "no git history"
    print(f"[*] Deploying {head[:7] or '?'}; diff base {base[:7] if base else '-'} = {why}")

    git_changed = get_git_diff_files(repo_root, base) if base else None
    to_upload = []

    if git_changed is not None:
        for full_path, rel_str, local_size in all_files:
            if rel_str in git_changed:
                to_upload.append((full_path, rel_str, local_size, "git diff"))
    else:
        # Upload all files modified in the last 7 days + core index files
        now = time.time()
        for full_path, rel_str, local_size in all_files:
            mtime = full_path.stat().st_mtime
            if (now - mtime) < (7 * 86400) or rel_str in ("sitemap.xml", "blog/index.html", "blog-ar/index.html"):
                to_upload.append((full_path, rel_str, local_size, "recent modification"))

    skipped_count = len(all_files) - len(to_upload)
    print(f"[*] Sync Plan: {len(to_upload)} files to upload, {skipped_count} files untouched.")

    known_dirs = set()
    uploaded_count = 0
    error_count = 0
    try:
        print(f"[*] Initial FTP directory: {initial_cwd}")

        uploaded_count = 0
        error_count = 0

        for idx, (full_path, rel_str, local_size, reason) in enumerate(to_upload, 1):
            clean_rel = rel_str.replace("\\", "/").lstrip("/")
            rel_dir = os.path.dirname(clean_rel)
            file_name = os.path.basename(clean_rel)

            success = False
            for attempt in range(1, 4):
                try:
                    # Navigate and upload safely
                    if rel_dir:
                        ensure_remote_dir_hierarchy(ftp, initial_cwd, rel_dir, known_dirs)
                        ftp.cwd(f"{initial_cwd}/{rel_dir}".replace("//", "/"))
                    else:
                        ftp.cwd(initial_cwd)

                    with open(full_path, "rb") as fp:
                        ftp.storbinary(f"STOR {file_name}", fp)

                    ftp.cwd(initial_cwd)
                    print(f"  [{idx}/{len(to_upload)}] Uploaded: {clean_rel} ({local_size:,} bytes)")
                    uploaded_count += 1
                    success = True
                    break
                except (ftplib.error_temp, ftplib.error_proto, EOFError, TimeoutError, ConnectionResetError, BrokenPipeError) as e:
                    print(f"  [!] Socket error on '{clean_rel}' (attempt {attempt}/3): {e}")
                    time.sleep(2 * attempt)
                    try:
                        if ftp:
                            ftp.close()
                    except Exception:
                        pass
                    try:
                        ftp = connect_ftp(server, user, password, port)
                        initial_cwd = ftp.pwd()
                    except Exception as reconnect_err:
                        print(f"  [!] Reconnect failed: {reconnect_err}")
                except Exception as e:
                    print(f"  [!] Error uploading '{clean_rel}': {e}")
                    try:
                        ftp.cwd(initial_cwd)
                    except Exception:
                        pass
                    break

            if not success:
                print(f"  [ERROR] Failed to upload: {clean_rel}")
                error_count += 1

        # Only a clean run moves the marker; otherwise the next deploy retries
        # everything since the last good one.
        if error_count == 0 and head:
            write_marker(ftp, initial_cwd, head)
            print(f"[+] Server marker now {head[:7]}")

    finally:
        if ftp:
            try:
                ftp.quit()
            except Exception:
                pass

    total_time = time.time() - start_time
    print("\n==================================================")
    print("DEPLOYMENT SUMMARY:")
    print(f"  • Total Local Files: {len(all_files)}")
    print(f"  • Uploaded Files:    {uploaded_count}")
    print(f"  • Skipped:           {skipped_count}")
    print(f"  • Errors:            {error_count}")
    print(f"  • Duration:          {total_time:.2f} seconds")
    print("==================================================")

    if error_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", help="diff base to use when the server has no deploy marker yet")
    deploy(ap.parse_args().base)
