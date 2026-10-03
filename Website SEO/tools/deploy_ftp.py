#!/usr/bin/env python3
"""
High-Performance Resilient FTP Deployment Script for AI Profit Lab
------------------------------------------------------------------
Synchronizes public_html directly to Hostinger FTP.
- Uses remote manifest (.deploy_manifest.json) for O(1) change detection
- Computes local MD5 hashes in < 1 second across entire workspace
- Uploads ONLY new/modified files instead of querying 1,300+ files individually
- Automatic retry and socket reconnection on transient network issues
- Fast directory-level fallback scan if remote manifest is missing
"""

import os
import sys
import io
import json
import time
import hashlib
import ftplib
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


def fetch_remote_file_map_fast(ftp, remote_root):
    """Fast fallback: scans remote directory tree via MLSD or NLST (directory-by-directory)."""
    print("[*] Remote manifest not found. Scanning remote directory structure...")
    remote_map = {}

    def scan_dir(path):
        normalized_path = path.rstrip("/")
        try:
            items = list(ftp.mlsd(normalized_path))
            for name, facts in items:
                if name in (".", ".."):
                    continue
                item_path = f"{normalized_path}/{name}".replace("//", "/")
                item_type = facts.get("type")
                if item_type == "dir":
                    scan_dir(item_path)
                elif item_type == "file":
                    rel = os.path.relpath(item_path, remote_root).replace("\\", "/")
                    if rel.startswith("./"):
                        rel = rel[2:]
                    size = int(facts.get("size", -1))
                    remote_map[rel] = {"size": size}
        except Exception:
            # Fallback to NLST
            try:
                entries = ftp.nlst(normalized_path)
                for entry in entries:
                    name = os.path.basename(entry)
                    if name in (".", ".."):
                        continue
                    item_path = f"{normalized_path}/{name}".replace("//", "/")
                    try:
                        sz = ftp.size(item_path)
                        rel = os.path.relpath(item_path, remote_root).replace("\\", "/")
                        if rel.startswith("./"):
                            rel = rel[2:]
                        remote_map[rel] = {"size": sz}
                    except Exception:
                        # Might be a directory
                        scan_dir(item_path)
            except Exception:
                pass

    try:
        scan_dir(remote_root if remote_root else ".")
    except Exception as e:
        print(f"  [!] Directory scan notice: {e}")

    print(f"[+] Remote scan complete: found {len(remote_map)} existing files.")
    return remote_map


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
        if remote_manifest is None:
            remote_manifest = fetch_remote_file_map_fast(ftp, remote_root)

        # Step 3: Determine files requiring upload
        to_upload = []
        for full_path, rel_str, local_size in all_files:
            remote_info = remote_manifest.get(rel_str)
            if not remote_info:
                to_upload.append((full_path, rel_str, local_size, "new file"))
            elif "md5" in remote_info and remote_info["md5"] != local_manifest[rel_str]["md5"]:
                to_upload.append((full_path, rel_str, local_size, "modified content (hash mismatch)"))
            elif "md5" not in remote_info and remote_info.get("size") != local_size:
                to_upload.append((full_path, rel_str, local_size, "size mismatch"))

        skipped_count = len(all_files) - len(to_upload)
        print(f"[*] Sync Plan: {len(to_upload)} files to upload, {skipped_count} files identical/up-to-date.")

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

        # Step 5: Save remote manifest if all or most uploads succeeded
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
    print(f"  • Skipped (Up-to-Date): {skipped_count}")
    print(f"  • Errors:            {error_count}")
    print(f"  • Duration:          {total_time:.2f} seconds")
    print("==================================================")

    if error_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    deploy()
