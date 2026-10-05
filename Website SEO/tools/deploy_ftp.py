#!/usr/bin/env python3
"""
High-Performance Resilient FTP Deployment Script for AI Profit Lab
------------------------------------------------------------------
Synchronizes public_html directly to Hostinger FTP.
- Uses remote manifest (.deploy_manifest.json) for O(1) change detection
- Uses Git-diff detection when running in CI/Git to sync ONLY changed files (< 5s)
- Automatic retry and socket reconnection on transient network issues
- Avoids slow sequential 1,300+ file remote scans over high-latency FTP
"""

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


def get_git_diff_files(repo_root, local_dir):
    """Finds files modified in the recent git commits that exist in local_dir."""
    try:
        # Check diff of last commit vs previous
        cmd = ["git", "diff", "--name-only", "HEAD~1", "HEAD"]
        res = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)
        if res.returncode != 0:
            # Fallback to diff of HEAD vs unstaged/staged
            cmd = ["git", "diff", "--name-only", "HEAD"]
            res = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)

        if res.returncode == 0 and res.stdout.strip():
            changed_rel_paths = set()
            for line in res.stdout.strip().splitlines():
                line = line.strip().replace("\\", "/")
                # Check if it targets public_html
                if "public_html/" in line:
                    rel = line.split("public_html/", 1)[1]
                    if not should_exclude(rel):
                        changed_rel_paths.add(rel)
            if changed_rel_paths:
                print(f"[+] Git diff identified {len(changed_rel_paths)} modified web files.")
                return changed_rel_paths
    except Exception as e:
        print(f"  [!] Notice: Git diff check skipped ({e})")
    return None


def connect_ftp(server, user, password, port=21, timeout=60):
    print(f"[*] Connecting to FTP server: {server}:{port} as {user}...")
    ftp = ftplib.FTP(timeout=timeout)
    ftp.connect(server, int(port))
    ftp.login(user, password)
    ftp.set_pasv(True)
    print(f"[+] Connected: {ftp.getwelcome().strip()}")
    return ftp


def fetch_remote_manifest(ftp, remote_root):
    """Attempts to download and parse .deploy_manifest.json from the remote FTP server."""
    manifest_path = f"{remote_root}/.deploy_manifest.json".replace("//", "/")
    buf = io.BytesIO()
    try:
        ftp.retrbinary(f"RETR {manifest_path}", buf.write)
        buf.seek(0)
        data = json.loads(buf.read().decode("utf-8"))
        if isinstance(data, dict):
            print(f"[+] Found remote deployment manifest with {len(data)} tracked files.")
            return data
    except Exception:
        pass
    return None


def ensure_remote_dir(ftp, remote_dir, known_dirs):
    if not remote_dir or remote_dir in (".", "/"):
        return
    clean_dir = remote_dir.replace("\\", "/").strip("/")
    if clean_dir in known_dirs:
        return

    dirs = [d for d in clean_dir.split("/") if d]
    current = ""
    for d in dirs:
        current += "/" + d
        if current not in known_dirs:
            try:
                ftp.cwd(current)
                known_dirs.add(current)
            except ftplib.error_perm:
                try:
                    ftp.mkd(current)
                    known_dirs.add(current)
                    print(f"  [+] Created remote directory: {current}")
                except Exception:
                    known_dirs.add(current)


def save_and_upload_manifest(ftp, remote_root, local_manifest):
    manifest_path = f"{remote_root}/.deploy_manifest.json".replace("//", "/")
    data = json.dumps(local_manifest, indent=2).encode("utf-8")
    buf = io.BytesIO(data)
    try:
        ftp.storbinary(f"STOR {manifest_path}", buf)
        print(f"[+] Uploaded updated deployment manifest ({len(local_manifest)} files tracked).")
    except Exception as e:
        print(f"[!] Warning: Failed to save remote deployment manifest: {e}")


def deploy():
    start_time = time.time()
    server = os.environ.get("FTP_SERVER")
    user = os.environ.get("FTP_USERNAME")
    password = os.environ.get("FTP_PASSWORD")
    port = int(os.environ.get("FTP_PORT", 21))
    remote_root = os.environ.get("FTP_REMOTE_ROOT", "./").rstrip("/")

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
    print(f"[*] Target remote directory: {remote_root}")

    # Step 1: Compute local manifest
    print("[*] Indexing and hashing local files...")
    local_manifest, all_files = compute_local_manifest(local_dir)
    print(f"[+] Local files indexed: {len(local_manifest)} files in {time.time() - start_time:.2f}s")

    ftp = None
    known_dirs = set()
    try:
        ftp = connect_ftp(server, user, password, port)

        # Step 2: Fetch remote state
        remote_manifest = fetch_remote_manifest(ftp, remote_root)

        # Step 3: Determine files requiring upload
        to_upload = []

        if remote_manifest is not None:
            # We have a valid remote manifest -> exact diff
            for full_path, rel_str, local_size in all_files:
                remote_info = remote_manifest.get(rel_str)
                if not remote_info:
                    to_upload.append((full_path, rel_str, local_size, "new file"))
                elif "md5" in remote_info and remote_info["md5"] != local_manifest[rel_str]["md5"]:
                    to_upload.append((full_path, rel_str, local_size, "modified content (hash mismatch)"))
                elif "md5" not in remote_info and remote_info.get("size") != local_size:
                    to_upload.append((full_path, rel_str, local_size, "size mismatch"))
        else:
            # Remote manifest not found -> Check Git diff to avoid 38-minute sequential FTP scan
            git_changed = get_git_diff_files(repo_root, local_dir)
            if git_changed:
                print(f"[*] Deploying {len(git_changed)} files changed in recent Git commits...")
                for full_path, rel_str, local_size in all_files:
                    if rel_str in git_changed:
                        to_upload.append((full_path, rel_str, local_size, "git commit diff"))
            else:
                # Fallback: Sync all critical HTML/sitemap/images modified in last 7 days or everything
                print("[*] Syncing recent modified files...")
                now = time.time()
                for full_path, rel_str, local_size in all_files:
                    mtime = full_path.stat().st_mtime
                    if (now - mtime) < (7 * 86400) or rel_str in ("sitemap.xml", "blog/index.html", "blog-ar/index.html"):
                        to_upload.append((full_path, rel_str, local_size, "recently modified"))

        skipped_count = len(all_files) - len(to_upload)
        print(f"[*] Sync Plan: {len(to_upload)} files to upload, {skipped_count} files untouched.")

        # Step 4: Upload changed files
        uploaded_count = 0
        error_count = 0

        for idx, (full_path, rel_str, local_size, reason) in enumerate(to_upload, 1):
            remote_file_path = f"{remote_root}/{rel_str}".replace("//", "/")
            remote_dir = os.path.dirname(remote_file_path)

            success = False
            for attempt in range(1, 4):
                try:
                    ensure_remote_dir(ftp, remote_dir, known_dirs)
                    with open(full_path, "rb") as fp:
                        ftp.storbinary(f"STOR {remote_file_path}", fp)
                    print(f"  [{idx}/{len(to_upload)}] Uploaded: {rel_str} ({local_size:,} bytes) [{reason}]")
                    uploaded_count += 1
                    success = True
                    break
                except (ftplib.error_temp, ftplib.error_proto, EOFError, TimeoutError, ConnectionResetError, BrokenPipeError) as e:
                    print(f"  [!] Socket error on '{rel_str}' (attempt {attempt}/3): {e}")
                    time.sleep(2 * attempt)
                    try:
                        if ftp:
                            ftp.close()
                    except Exception:
                        pass
                    try:
                        ftp = connect_ftp(server, user, password, port)
                    except Exception as reconnect_err:
                        print(f"  [!] Reconnect failed: {reconnect_err}")
                except Exception as e:
                    print(f"  [!] Permanent error uploading '{rel_str}': {e}")
                    break

            if not success:
                print(f"  [ERROR] Failed to upload: {rel_str}")
                error_count += 1

        # Step 5: Save remote manifest so subsequent deploys are instant
        if error_count == 0 or uploaded_count > 0:
            save_and_upload_manifest(ftp, remote_root, local_manifest)

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
    deploy()
