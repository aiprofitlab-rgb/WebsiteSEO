#!/usr/bin/env python3
"""
Set up (or repair) the Antigravity daily publisher on this Mac. Safe to re-run.

    python3 execution/setup_antigravity_publisher.py                # clone + project + schedule (paused)
    python3 execution/setup_antigravity_publisher.py --enable       # ...and switch the hourly schedule on
    python3 execution/setup_antigravity_publisher.py --disable      # pause the hourly schedule
    python3 execution/setup_antigravity_publisher.py --dry-run-now  # start ONE dry run right away
    python3 execution/setup_antigravity_publisher.py --cleanup-dry-run

What it creates:
  1. A slim clone of the website repo at ~/Developer/aiprofitlab-publisher (only
     `Website SEO/` and the article skill, ~200 MB), marked `apl.publisher=true`. The
     publisher resets it to GitHub's main before every job, so it never runs in the
     checkout Nahid works in.
  2. An Antigravity project, "AI Profit Lab Publisher", whose workspace is that clone's
     `Website SEO/` folder, pre-approved to run `python3 execution/agent_publish.py` and to
     read web pages (for source research), so an unattended run never waits for a click.
  3. A scheduled sidecar (~/.gemini/config/sidecars/aiprofitlab-publisher) that runs
     execution/antigravity_trigger.sh at minute 17 of every hour. It starts a conversation
     only when today's article, a hero swap or a repair is due.

Antigravity must be open (the app or the IDE) for the schedule to fire. When the Mac is
off all day, GitHub's evening fallback publishes instead (daily_publish.yml).
"""

import argparse
import json
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path
from urllib.parse import quote

HOME = Path.home()
CONFIG = HOME / ".gemini" / "config"
SIDECAR_ID = "aiprofitlab-publisher"
DRY_ID = "aiprofitlab-publisher-dryrun"
DEFAULT_CLONE = HOME / "Developer" / "aiprofitlab-publisher"
REMOTE = "https://github.com/aiprofitlab-rgb/WebsiteSEO"
GRANTS = ["command(python3 execution/agent_publish.py)", "read_url(*)"]


def sh(*cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"{' '.join(cmd)} failed:\n{r.stderr or r.stdout}")
    return r.stdout.strip()


def ensure_clone(path):
    if not (path / ".git").exists():
        print(f"Cloning into {path} (only Website SEO/ and the skill)...")
        path.parent.mkdir(parents=True, exist_ok=True)
        # --no-cone: cone mode always checks out root-level files, and the repo root holds
        # ~300 MB of tracked backup zips. Blobless + no checkout until the patterns are set,
        # so those zips are never downloaded at all.
        sh("git", "clone", "--quiet", "--filter=blob:none", "--no-checkout", REMOTE, str(path))
        sh("git", "sparse-checkout", "set", "--no-cone", "/Website SEO/", "/SKILL_article_creator/",
           "/AGENTS.md", "/.gitignore", cwd=path)
        sh("git", "checkout", "--quiet", "main", cwd=path)
    sh("git", "config", "apl.publisher", "true", cwd=path)
    sh("git", "config", "user.name", "AI Profit Lab publisher (Antigravity)", cwd=path)
    sh("git", "config", "user.email", "bot@aiprofitlab.io", cwd=path)
    (path / "Website SEO" / "agent_jobs").mkdir(parents=True, exist_ok=True)
    print(f"  clone ready: {path}")


def ensure_project(clone):
    pid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"aiprofitlab-publisher:{clone}"))
    f = CONFIG / "projects" / f"{pid}.json"
    data = json.loads(f.read_text()) if f.exists() else {}
    data.update({
        "id": pid,
        "name": quote("AI Profit Lab Publisher"),
        "projectResources": {"resources": [{"gitFolder": {
            "folderUri": "file://" + quote(str(clone / "Website SEO")),
            "defaultBranch": "main", "allowWrite": True}}]},
        "permissionGrants": {"allow": sorted(set(data.get("permissionGrants", {}).get("allow", [])) | set(GRANTS))},
        "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%S.000000Z", time.gmtime()),
    })
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(data, indent=2))
    sh("git", "config", "apl.projectId", pid, cwd=clone)
    print(f"  Antigravity project: {f}")
    return pid


def write_sidecar(sid, cfg):
    d = CONFIG / "sidecars" / sid
    d.mkdir(parents=True, exist_ok=True)
    (d / "sidecar.json").write_text(json.dumps(cfg, indent=2))
    print(f"  sidecar: {d / 'sidecar.json'}")


def enable_in_config(sid, pid, enabled=True):
    f = CONFIG / "config.json"
    data = json.loads(f.read_text()) if f.exists() else {}
    if f.exists():
        shutil.copy2(f, f.with_name(f"config.json.bak-{time.strftime('%Y%m%d-%H%M%S')}"))
    data.setdefault("sidecars", {})[sid] = {"enabled": enabled, "projectId": pid}
    f.write_text(json.dumps(data, indent=2))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--clone-dir", default=str(DEFAULT_CLONE))
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--enable", action="store_true", help="switch the hourly schedule on")
    g.add_argument("--disable", action="store_true", help="pause the hourly schedule")
    ap.add_argument("--dry-run-now", action="store_true", help="start one dry run right away")
    ap.add_argument("--cleanup-dry-run", action="store_true", help="remove the one-off dry-run sidecar")
    a = ap.parse_args()

    clone = Path(a.clone_dir).expanduser()
    ensure_clone(clone)
    pid = ensure_project(clone)
    trigger = str(clone / "Website SEO" / "execution" / "antigravity_trigger.sh")
    sc = CONFIG / "sidecars" / SIDECAR_ID / "sidecar.json"
    was_disabled = json.loads(sc.read_text()).get("disabled", True) if sc.exists() else True
    disabled = False if a.enable else True if a.disable else was_disabled
    write_sidecar(SIDECAR_ID, {
        "builtin": "schedule",
        "args": ["17 * * * *", "/bin/sh", trigger],
        "restart_policy": "always",
        "display_name": "AI Profit Lab publisher",
        "description": ("Every hour at :17. If today's blog article, a hero-image swap or a repair is due, "
                        "starts an Antigravity conversation that writes, illustrates and publishes it "
                        "(Website SEO/execution/agent_publish.py)."),
        "env": {"ANTIGRAVITY_PROJECT_ID": pid},
        "disabled": disabled,
    })
    enable_in_config(SIDECAR_ID, pid, not disabled)
    if a.dry_run_now:
        write_sidecar(DRY_ID, {
            "command": "/bin/sh", "args": [trigger, "--dry-run"], "restart_policy": "never",
            "display_name": "AI Profit Lab publisher: one dry run",
            "description": "Runs once: a full article run that publishes nothing (agent_publish.py --dry-run).",
            "env": {"ANTIGRAVITY_PROJECT_ID": pid},
        })
        enable_in_config(DRY_ID, pid, True)
    if a.cleanup_dry_run:
        shutil.rmtree(CONFIG / "sidecars" / DRY_ID, ignore_errors=True)
        f = CONFIG / "config.json"
        data = json.loads(f.read_text())
        data.get("sidecars", {}).pop(DRY_ID, None)
        f.write_text(json.dumps(data, indent=2))
        print("  dry-run sidecar removed")
    print(f"\nHourly schedule: {'PAUSED' if disabled else 'ON'}. Antigravity must be open for it to fire.")
    print(f"Run log: {clone / 'Website SEO' / 'agent_jobs' / 'log.md'}")


if __name__ == "__main__":
    main()
