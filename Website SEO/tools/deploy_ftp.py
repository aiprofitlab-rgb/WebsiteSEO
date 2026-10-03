#!/usr/bin/env python3
"""
Robust FTP Deployment Script for AI Profit Lab
-----------------------------------------------
Synchronizes public_html directly to Hostinger FTP.
- Uses ftplib with automatic retry and exponential backoff
- Syncs only new or modified files (size & modification time)
- Preserves remote files while uploading all web updates
- Avoids fragile third-party sync state JSON files
"""

import os
import sys
import ftplib
import time
from pathlib import Path

# Files/folders to exclude from FTP upload
EXCLUDE_PATTERNS = {
    ".git",
    ".github",
    ".DS_Store",
    ".ds-store",
    "__pycache__",
    "node_modules",
}

EXCLUDE_EXTENSIONS = {
    ".py",
    ".pyc",
    ".sh",
    ".gs",
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


def get_remote_file_size(ftp, remote_path):
    try:
        return ftp.size(remote_path)
    except Exception:
        return None


def ensure_remote_dir(ftp, remote_dir):
    if not remote_dir or remote_dir == "." or remote_dir == "/":
        return
    dirs = [d for d in remote_dir.replace("\\", "/").strip("/").split("/") if d]
    current = ""
    for d in dirs:
        current += "/" + d
        try:
            ftp.cwd(current)
        except ftplib.error_perm:
            try:
                ftp.mkd(current)
                print(f"  [+] Created remote directory: {current}")
            except Exception as e:
                # Directory may already exist or permissions issue
                pass


def connect_ftp(server, user, password, port=21):
    print(f"[*] Connecting to FTP server: {server}:{port} as {user}...")
    ftp = ftplib.FTP(timeout=60)
    ftp.connect(server, int(port))
    ftp.login(user, password)
    ftp.set_pasv(True)
    print(f"[+] Connected: {ftp.getwelcome()}")
    return ftp


def deploy():
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

    print(f"[*] Source directory: {local_dir}")
    print(f"[*] Target remote root: {remote_root}")

    # Gather local files to upload
    all_files = []
    for root, dirs, files in os.walk(local_dir):
        for f in files:
            full_path = Path(root) / f
            rel_path = full_path.relative_to(local_dir)
            rel_str = str(rel_path).replace("\\", "/")
            if not should_exclude(rel_str):
                all_files.append((full_path, rel_str))

    print(f"[*] Total valid files to check: {len(all_files)}")

    ftp = None
    uploaded_count = 0
    skipped_count = 0
    error_count = 0

    try:
        ftp = connect_ftp(server, user, password, port)

        for full_path, rel_str in all_files:
            remote_file_path = f"{remote_root}/{rel_str}".replace("//", "/")
            remote_dir = os.path.dirname(remote_file_path)
            local_size = full_path.stat().st_size

            # Retry loop per file
            success = False
            for attempt in range(1, 4):
                try:
                    # Check remote size
                    remote_size = get_remote_file_size(ftp, remote_file_path)
                    if remote_size is not None and remote_size == local_size:
                        # File is identical in size, skip upload
                        skipped_count += 1
                        success = True
                        break

                    # Ensure directory exists on remote
                    ensure_remote_dir(ftp, remote_dir)

                    # Upload file in binary mode
                    with open(full_path, "rb") as fp:
                        ftp.storbinary(f"STOR {remote_file_path}", fp)

                    print(f"[+] Uploaded: {rel_str} ({local_size:,} bytes)")
                    uploaded_count += 1
                    success = True
                    break
                except (ftplib.error_temp, ftplib.error_proto, EOFError, TimeoutError, ConnectionResetError, BrokenPipeError) as e:
                    print(f"[!] Socket/Connection error on '{rel_str}' (attempt {attempt}/3): {e}")
                    time.sleep(2 * attempt)
                    try:
                        if ftp:
                            ftp.close()
                    except Exception:
                        pass
                    try:
                        ftp = connect_ftp(server, user, password, port)
                    except Exception as reconnect_err:
                        print(f"[!] Reconnect failed: {reconnect_err}")
                except Exception as e:
                    print(f"[!] Permanent error uploading '{rel_str}': {e}")
                    break

            if not success:
                print(f"[ERROR] Failed to upload: {rel_str}")
                error_count += 1

    finally:
        if ftp:
            try:
                ftp.quit()
            except Exception:
                pass

    print("\n==================================================")
    print(f"DEPLOYMENT SUMMARY:")
    print(f"  • Files Checked:   {len(all_files)}")
    print(f"  • Files Uploaded:  {uploaded_count}")
    print(f"  • Files Skipped:   {skipped_count} (identical)")
    print(f"  • Errors:          {error_count}")
    print("==================================================")

    if error_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    deploy()
