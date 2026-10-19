#!/usr/bin/env python3
"""
HARO pitches on Nahid's Mac: Google Antigravity drafts them, Claude checks and humanizes them,
and code decides which go out.

Every 10 minutes Antigravity's scheduler runs `trigger`, outside the agent's sandbox:
  1. HARO digests in Gmail without the "HARO Processed" label are split into queries in code.
     Expired and already-pitched queries are dropped. A job folder with a brief goes into the
     agent's workspace, and an Antigravity conversation starts (Gemini on the Google AI Pro
     plan: no API cost).
  2. The agent screens every query, drafts a reply to each one worth pitching, runs
     `python3 haro.py check` until it passes, and `submit`s.
  3. The next trigger has Claude (Claude Code headless, on Nahid's Claude subscription, never
     an API key) fact-check and humanize each pitch. Code then sends it from
     nahid@aiprofitlab.io, or leaves it in Gmail Drafts with the reasons, and labels the digests.

Sending is OFF until Nahid turns it on. Until then every pitch is a draft whose notes say whether
it would have gone out. Even with sending on, these are never sent: replies to journalists who
reject AI-written pitches (talking points instead), drafts with an [ADD: ...] gap or a "send only
if true" condition, anything Claude holds or flags, a figure the request doesn't explain, fit
under 4 of 5, a reply address code didn't read from a HARO digest, a deadline under 30 minutes
away, and anything past the daily cap (5 in 24 hours).

Three folders under ~/Developer/aiprofitlab-haro (outside Desktop, which Antigravity's background
jobs may not be allowed to read):
  runner/     this code, the Gmail token, and state/ (job state, queries, Claude's reviews, log.md)
  workspace/  the agent's workspace: INSTRUCTIONS.md, haro.py (a copy of this file), briefs, drafts
The agent can read and write only workspace/, so it never sees the token or the reply addresses,
and cannot change what gets sent where.

From the website checkout:
  python3 execution/haro_agent.py setup              # deploy the code here to the runner; Antigravity project + schedule
  python3 execution/haro_agent.py setup --enable     # switch the 10-minute schedule on (--disable: off)
  python3 execution/haro_agent.py setup --sending on # let passing pitches go out by themselves (off: drafts only)
  python3 execution/haro_agent.py setup --dry-run-now | --selftest-now | --cleanup
  python3 execution/haro_agent.py status
In the runner (Antigravity's scheduler, or by hand):
  python3 execution/haro_agent.py trigger [--dry-run] | apply | selftest
The agent, in its workspace:
  python3 haro.py next | check | submit | fail "why"

Agent instructions: directives/antigravity_haro.md (copied to the workspace as INSTRUCTIONS.md).
How the whole HARO pipeline works and what went wrong before: directives/haro_pitch_assistant.md.
After editing this file, haro_rules.py, haro_email_processor.py or the agent directive, run
`setup` again: the runner only has what setup copied there.
"""

import argparse
import base64
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True           # no __pycache__ in the agent's workspace
sys.path.insert(0, str(HERE))
import haro_rules as rules  # noqa: E402

HARO_HOME = Path(os.environ.get("HARO_HOME", str(Path.home() / "Developer" / "aiprofitlab-haro")))
RUNNER = HARO_HOME / "runner"
WS = HERE if HERE.name == "workspace" else HARO_HOME / "workspace"
STATE_DIR = RUNNER / "state"
STATE = STATE_DIR / "state.json"
LOG = STATE_DIR / "log.md"
LOCK = STATE_DIR / "trigger.lock"
CURRENT = WS / "current.json"

CONFIG = Path.home() / ".gemini" / "config"     # Antigravity's projects and sidecars
SIDECAR_ID = "aiprofitlab-haro"
ONE_OFF = {"dry": "aiprofitlab-haro-dryrun", "selftest": "aiprofitlab-haro-selftest"}
GRANTS = ["command(python3 haro.py)"]

# What setup copies from the checkout into the runner, and what the trigger copies from the runner
# into the agent's workspace.
DEPLOY = ["execution/haro_agent.py", "execution/haro_rules.py", "execution/haro_email_processor.py",
          "execution/haro_run.sh", "directives/antigravity_haro.md"]
WS_FILES = {"haro.py": "execution/haro_agent.py", "haro_rules.py": "execution/haro_rules.py",
            "INSTRUCTIONS.md": "directives/antigravity_haro.md"}

DIGEST_DAYS = 7
MAX_QUERIES = 90                 # per job; more than this means a long backlog, earliest deadlines first
AGENT_TIMEOUT = 60 * 60          # an agent that hasn't submitted after this is presumed stuck
MAX_LAUNCHES = 2                 # conversations per job, then its digests go to the Gemini fallback
MAX_LAUNCH_ERRORS = 6            # failed attempts to start a conversation (an hour of 10-minute runs)
MAX_APPLIES = 3
LOCK_TTL = 60 * 60
KEEP_JOBS = 40
SEND_LEAD = datetime.timedelta(minutes=30)
MIN_FIT_TO_SEND = 4
HARO_REPLY = re.compile(r'reply\+[\w.-]+@helpareporter\.com', re.I)
CLAUDE_MODEL = os.environ.get("HARO_CLAUDE_MODEL", "opus")
UTC = datetime.timezone.utc


class Stop(Exception):
    """Tooling trouble or a wrong place to run: printed as STOP."""


def utcnow():
    return datetime.datetime.now(UTC)


def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.rename(path)


# ======================================================================
# Checks shared by the agent's `check` and the trigger's apply step
# ======================================================================
def notes_only(q, d):
    """Talking points instead of a reply: the digest says "No AI Pitches", or the agent saw it in the text."""
    return bool(q.get("no_ai") or d.get("ai_replies_forbidden"))


def decision_problems(q, d):
    qid, out = q["id"], []
    if not isinstance(d.get("eligible"), bool):
        out.append(f"{qid}: eligible must be true or false")
    if not isinstance(d.get("reason"), str) or not d["reason"].strip():
        out.append(f"{qid}: reason is empty")
    fit = d.get("fit")
    fit_ok = isinstance(fit, int) and not isinstance(fit, bool) and 1 <= fit <= 5
    if not fit_ok:
        out.append(f"{qid}: fit must be a whole number from 1 to 5")
    if d.get("decision") not in ("PITCH", "SKIP"):
        out.append(f'{qid}: decision must be "PITCH" or "SKIP"')
    if not isinstance(d.get("ai_replies_forbidden"), bool):
        out.append(f"{qid}: ai_replies_forbidden must be true or false")
    if d.get("decision") == "PITCH" and (d.get("eligible") is not True or (fit_ok and fit < 3)):
        out.append(f"{qid}: PITCH needs eligible=true and fit 3 or more. Make it SKIP, or correct the screening.")
    if q.get("no_ai") and d.get("ai_replies_forbidden") is False:
        out.append(f'{qid}: the request says "No AI Pitches Considered", so ai_replies_forbidden must be true')
    return out


def draft_problems(jd, q, d):
    qid = q["id"]
    path = jd / "drafts" / f"{qid}.json"
    if not path.exists():
        return [f"{qid} is PITCH but drafts/{qid}.json does not exist yet"]
    dr = read_json(path)
    if not isinstance(dr, dict):
        return [f"drafts/{qid}.json is not valid JSON in the brief's shape (use \\n for line breaks inside text)"]
    out = [f'drafts/{qid}.json: "{k}" must be a string' + (' (an empty one if nothing)' if k == "only_if_true" else "")
           for k in ("fit_note", "only_if_true", "text") if not isinstance(dr.get(k), str)]
    if out:
        return out
    if not dr["fit_note"].strip():
        out.append(f"drafts/{qid}.json: fit_note is empty")
    out += [f"drafts/{qid}.json: {p}" for p in rules.text_problems(dr["text"], q["query"], notes_only(q, d))]
    return out


def check_job(jd, queries):
    """Every problem with the agent's screening and drafts, each as an instruction it can act on."""
    path = jd / "screening.json"
    if not path.exists():
        return ["screening.json does not exist yet"]
    scr = read_json(path)
    decisions = scr.get("decisions") if isinstance(scr, dict) else None
    if not isinstance(decisions, list):
        return ['screening.json is not valid JSON of the form {"decisions": [...]}, one decision per request']
    problems, by_id = [], {}
    for d in decisions:
        if not isinstance(d, dict) or not d.get("id"):
            problems.append(f"a decision without an id: {str(d)[:80]}")
            continue
        if d["id"] in by_id:
            problems.append(f"{d['id']}: two decisions; keep one")
        by_id[d["id"]] = d
    ids = [q["id"] for q in queries]
    for extra in sorted(set(by_id) - set(ids)):
        problems.append(f"{extra}: not a request in this job (its ids run from {ids[0]} to {ids[-1]})")
    for q in queries:
        d = by_id.get(q["id"])
        if d is None:
            problems.append(f"{q['id']}: no decision. Every request needs one, SKIP included.")
            continue
        dp = decision_problems(q, d)
        problems += dp
        if d.get("decision") == "PITCH" and not dp:
            problems += draft_problems(jd, q, d)
    return problems


# ======================================================================
# The agent's commands (run in the workspace, inside Antigravity's sandbox: stdlib only)
# ======================================================================
def open_job():
    cur = read_json(CURRENT, {}) or {}
    if cur.get("status") != "open" or not cur.get("id"):
        return None, None
    return cur, WS / "jobs" / cur["id"]


def report(problems):
    if not problems:
        print("PASS: the screening and every draft are in order.")
        return 0
    print(f"FAIL: {len(problems)} problem(s) in your files. Fix each one, then run the same command again:")
    for i, p in enumerate(problems[:40], 1):
        print(f" {i:2d}. {p}")
    if len(problems) > 40:
        print(f"  ... and {len(problems) - 40} more")
    return 1


def cmd_next(a):
    cur, jd = open_job()
    if not cur:
        print("NOTHING TO DO: no HARO job is open for you. Stop here.")
        return 0
    print(f"JOB {cur['id']}: {cur['count']} journalist requests"
          + (" · DRY RUN: nothing is sent" if cur.get("dry_run") else ""))
    print(f"Read the brief now, all of it: jobs/{cur['id']}/brief.md")
    if cur.get("last_problems"):
        print("Your last submission was sent back. Fix these first:")
        for i, p in enumerate(cur["last_problems"], 1):
            print(f" {i:2d}. {p}")
    done = sorted(p.relative_to(jd).as_posix() for p in jd.rglob("*.json") if p.name != "queries.json")
    if done:
        print(f"Files from an earlier attempt: {', '.join(done)}. Check them and continue from where they stop.")
    return 0


def cmd_check(a):
    cur, jd = open_job()
    if not cur:
        print("STOP: no HARO job is open.")
        return 1
    return report(check_job(jd, read_json(jd / "queries.json", [])))


def cmd_submit(a):
    cur, jd = open_job()
    if not cur:
        print("STOP: no HARO job is open.")
        return 1
    queries = read_json(jd / "queries.json", [])
    problems = check_job(jd, queries)
    if problems:
        return report(problems)
    decisions = read_json(jd / "screening.json")["decisions"]
    pitched = sum(d["decision"] == "PITCH" for d in decisions)
    (jd / "SUBMITTED").write_text(utcnow().isoformat() + "\n", encoding="utf-8")
    cur["status"] = "submitted"
    write_json(CURRENT, cur)
    print(f"SUBMITTED: {len(queries)} requests screened, {pitched} drafted. Claude reviews the pitches within "
          f"about 10 minutes. You are done: reply with your one-line summary and stop.")
    return 0


def cmd_fail(a):
    cur, jd = open_job()
    if cur:
        (jd / "FAILED").write_text(a.reason.strip() + "\n", encoding="utf-8")
        cur["status"] = "failed"
        write_json(CURRENT, cur)
    print("Recorded. Stop here; the schedule tries again later.")
    return 0


# ======================================================================
# The runner: state, log, lock
# ======================================================================
def journal(msg):
    """One line per event in runner/state/log.md, for Nahid to read."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if not LOG.exists():
        LOG.write_text("# HARO pipeline log\n\nNewest last. Muscat time.\n\n", encoding="utf-8")
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"- {datetime.datetime.now(ZoneInfo('Asia/Muscat')):%Y-%m-%d %H:%M} {msg}\n")
    print(msg, flush=True)


def load_state():
    st = read_json(STATE, {}) or {}
    st.setdefault("job", None)
    st.setdefault("given_up", {})      # digest message ids left to the Gemini fallback
    st.setdefault("not_ours", {})      # digests in another format: the Gemini fallback lists their queries
    return st


def save_state(st):
    cutoff = (utcnow() - datetime.timedelta(days=10)).isoformat()
    for k in ("given_up", "not_ours"):
        st[k] = {i: t for i, t in st[k].items() if t > cutoff}
    write_json(STATE, st)


def take_lock():
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        if time.time() - LOCK.stat().st_mtime > LOCK_TTL:
            LOCK.unlink()
    except OSError:
        pass
    try:
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False
    os.write(fd, f"{time.time():.0f} {os.getpid()}\n".encode())
    os.close(fd)
    return True


def release_lock():
    try:
        LOCK.unlink()
    except OSError:
        pass


def require_runner():
    if HERE != (RUNNER / "execution").resolve():
        raise Stop(f"this command runs in the runner ({RUNNER}/execution), which holds the Gmail token and the "
                   f"pipeline's state. From the website checkout, run `setup` first; then use "
                   f"python3 {RUNNER}/execution/haro_agent.py {sys.argv[1] if len(sys.argv) > 1 else ''}")


def require_checkout():
    if HERE in ((RUNNER / "execution").resolve(), WS.resolve()) or not (HERE.parent / "directives").is_dir():
        raise Stop("run setup from the website checkout (Website SEO/execution/haro_agent.py), whose code it deploys")


def hep():
    """The Gemini drafter's module: Gmail access, digest parsing, deadlines, draft layout."""
    import haro_email_processor
    return haro_email_processor


def sidecar_env():
    return (read_json(CONFIG / "sidecars" / SIDECAR_ID / "sidecar.json", {}) or {}).get("env", {})


def settings():
    """(sending on?, daily cap). The switch lives in the sidecar's config, outside the agent's reach."""
    env = sidecar_env()
    send = env.get("HARO_SEND", os.environ.get("HARO_SEND", "off")) == "on"
    cap = int(env.get("HARO_DAILY_CAP", os.environ.get("HARO_DAILY_CAP", "5")))
    return send, cap


def project_id():
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"aiprofitlab-haro:{WS}"))


def sync_workspace():
    """Keep the agent's copies of its command, the rules and its instructions current."""
    (WS / "jobs").mkdir(parents=True, exist_ok=True)
    for name, rel in WS_FILES.items():
        data = (RUNNER / rel).read_bytes()
        dst = WS / name
        if not dst.exists() or dst.read_bytes() != data:
            dst.write_bytes(data)


def write_current(job):
    if not job:
        write_json(CURRENT, {"status": "idle"})
        return
    write_json(CURRENT, {k: job.get(k) for k in ("id", "status", "count", "dry_run", "last_problems")})


def marker(job):
    jd = WS / "jobs" / job["id"]
    if (jd / "SUBMITTED").exists():
        return "submitted", ""
    if (jd / "FAILED").exists():
        return "failed", (jd / "FAILED").read_text(encoding="utf-8").strip()
    return None, ""


# ======================================================================
# Preparing a job
# ======================================================================
def find_digests(service, h, st, dry_run):
    """Digest emails no run has handled, grouped by subject (HARO sends each to both addresses)."""
    label_id = h.get_processed_label_id(service)
    query = h.digest_search_query(DIGEST_DAYS, include_processed=dry_run)
    msgs = service.users().messages().list(userId="me", q=query, maxResults=40).execute(num_retries=5).get("messages", [])
    groups = {}
    for m in msgs:
        if not dry_run and (m["id"] in st["given_up"] or m["id"] in st["not_ours"]):
            continue
        data = service.users().messages().get(userId="me", id=m["id"], format="full").execute(num_retries=5)
        if not dry_run and label_id in data.get("labelIds", []):
            continue
        headers = {x["name"].lower(): x["value"] for x in data.get("payload", {}).get("headers", [])}
        if "github.com" in headers.get("from", "").lower() or "run failed" in headers.get("subject", "").lower():
            continue
        groups.setdefault(headers.get("subject", "(no subject)"), []).append(data)
    if dry_run:                                   # newest first: the latest editions, labelled or not
        groups = dict(list(groups.items())[:int(os.environ.get("HARO_DRY_DIGESTS", "2"))])
    return groups, label_id


def make_job(service, h, st, groups, label_id, dry_run):
    now = utcnow()
    pitched_a, pitched_t = (set(), set()) if dry_run else h.already_pitched(service)
    digests, queries, seen = [], [], set()
    expired = already = 0
    for subject, copies in groups.items():
        data = copies[0]
        body = h.extract_message_body(data.get("payload", {}))
        received = datetime.datetime.fromtimestamp(int(data.get("internalDate", 0)) / 1000, UTC)
        ids = [c["id"] for c in copies]
        qs = h.parse_haro_digest(body)
        if not qs:
            if len(body) >= 100:
                for i in ids:
                    st["not_ours"][i] = now.isoformat()
                journal(f"left '{subject}' to the Gemini fallback: it isn't in HARO's format")
            elif not dry_run:
                for i in ids:
                    h.mark_digest_processed(service, i, label_id)
            continue
        digests.append({"subject": subject, "ids": ids, "received": received.isoformat()})
        for q in qs:
            dl = h.parse_deadline(q["deadline_raw"], received)
            if dl is not None and dl <= now + h.MIN_LEAD:
                expired += 1
                continue
            if q["id"] in seen:
                continue
            seen.add(q["id"])
            if q["email"].lower() in pitched_a or h.pitch_title_key(q["title"]) in pitched_t:
                already += 1
                continue
            q.update(ref=q["id"], deadline_utc=dl.isoformat() if dl else None, digest=subject)
            queries.append(q)
    if not digests:
        return None
    jid = now.strftime("%Y%m%d-%H%M") + ("-dry" if dry_run else "")
    job = {"id": jid, "status": "open", "digests": digests, "count": len(queries), "created": now.isoformat(),
           "launches": 0, "launch_errors": 0, "applies": 0, "dry_run": dry_run, "last_problems": []}
    subjects = ", ".join(f"'{d['subject']}'" for d in digests)
    if not queries:
        if not dry_run:
            label_digests(service, h, job, label_id)
        journal(f"{subjects}: nothing to pitch ({expired} past their deadline, {already} already drafted or sent)")
        return None
    if len(queries) > MAX_QUERIES:
        queries.sort(key=lambda q: q["deadline_utc"] or "9999")
        journal(f"{len(queries) - MAX_QUERIES} requests over the {MAX_QUERIES}-per-job limit were left out "
                f"(latest deadlines)")
        queries = queries[:MAX_QUERIES]
        job["count"] = len(queries)
    for i, q in enumerate(queries, 1):
        q["id"] = f"q{i}"
    write_json(STATE_DIR / "jobs" / jid / "queries.json", queries)
    jd = WS / "jobs" / jid
    (jd / "drafts").mkdir(parents=True, exist_ok=True)
    # The agent's copy leaves out the reply addresses: it never needs them.
    agent_keys = ("id", "title", "outlet", "journalist", "category", "deadline_raw", "deadline_utc", "no_ai", "query")
    write_json(jd / "queries.json", [{k: q.get(k) for k in agent_keys} for q in queries])
    (jd / "brief.md").write_text(brief(job, queries), encoding="utf-8")
    journal(f"prepared job {jid}" + (" (dry run)" if dry_run else "") + f": {len(queries)} requests from {subjects} "
            f"({expired} past their deadline, {already} already drafted or sent)")
    return job


def brief(job, queries):
    jid = job["id"]
    subjects = "; ".join(d["subject"] for d in job["digests"])
    reqs = []
    for q in queries:
        reqs += [f"### {q['id']} · {q['title']}",
                 f"Outlet: {q['outlet'] or '-'} · Journalist: {q['journalist'] or '-'} · Category: {q['category'] or '-'}",
                 f"Deadline: {q['deadline_raw'] or 'not stated'} · No AI pitches: {'YES' if q['no_ai'] else 'no'}",
                 "", q["query"], ""]
    return f"""# HARO job {jid}{' (DRY RUN: nothing is sent)' if job.get('dry_run') else ''}

{len(queries)} journalist requests from: {subjects}.
Decide for every one whether Nahid Abyari should reply, and draft the reply to each one he should.
Your drafts are not sent as you write them: Claude checks each pitch against the facts below and edits
it, and code decides whether it goes out or waits for Nahid. Write each one as if it were going
straight to the journalist.

Your folder is jobs/{jid}/. Write screening.json and drafts/<id>.json there, and nothing else.

## Facts about Nahid: the only things you may state about him or AI Profit Lab

{rules.SPOKESPERSON_FACTS}

## Step 1: screen every request into jobs/{jid}/screening.json

{rules.SCREENING_RULES}

Give one decision for every request below ({queries[0]['id']} to {queries[-1]['id']}), SKIP included, and keep
each reason to one sentence. A request marked "No AI pitches: YES" gets ai_replies_forbidden=true.

```json
{{"decisions": [
  {{"id": "q1", "eligible": true, "reason": "One sentence.", "fit": 4, "decision": "PITCH", "ai_replies_forbidden": false}},
  {{"id": "q2", "eligible": false, "reason": "One sentence.", "fit": 1, "decision": "SKIP", "ai_replies_forbidden": true}}
]}}
```

## Step 2: draft each PITCH into jobs/{jid}/drafts/<id>.json (for example drafts/q1.json)

For a request whose journalist accepts any reply:

{rules.PITCH_TASK}

For a request with ai_replies_forbidden=true:

{rules.NOTES_TASK}

{rules.DRAFT_RULES}

Each file:

```json
{{"fit_note": "One sentence for Nahid.", "only_if_true": "", "text": "The reply, or the talking points. Plain text, with \\n for each line break."}}
```

## Step 3: check, then submit

    python3 haro.py check     # PASS, or a numbered list of problems: fix them all and run it again
    python3 haro.py submit    # then reply with one line (requests, PITCH count, anything that went wrong) and stop

## The requests

""" + "\n".join(reqs)


# ======================================================================
# Antigravity conversations
# ======================================================================
def agentapi():
    """Antigravity's agent API. Inside a sidecar the app sets ANTIGRAVITY_AGENTAPI_EXE to its
    language-server binary, whose `agentapi` SUBCOMMAND this is (see agent_publish.py)."""
    exe = os.environ.get("ANTIGRAVITY_AGENTAPI_EXE")
    if exe and Path(exe).exists():
        return [exe, "agentapi"]
    for c in (shutil.which("agentapi"), str(Path.home() / ".gemini/antigravity/bin/agentapi")):
        if c and Path(c).exists():
            return [c]
    raise Stop("agentapi not found: is Antigravity installed?")


def launch(st, job):
    """Start a conversation for the job. False if Antigravity couldn't start one (tried again next run)."""
    job.update(status="open", launched=time.time())
    write_current(job)               # before the conversation starts, so its `next` finds the job
    title = f"AI Profit Lab HARO · {job['id']}" + (" · dry run" if job.get("dry_run") else "")
    prompt = ("You are AI Profit Lab's HARO pitch drafter. Read `INSTRUCTIONS.md` in this workspace and follow "
              "it exactly. Then run `python3 haro.py next` in the workspace root and do what the brief it "
              "names says." + (" This is a DRY RUN: nothing is sent." if job.get("dry_run") else ""))
    env = dict(os.environ)
    env.setdefault("ANTIGRAVITY_PROJECT_ID", project_id())
    try:
        r = subprocess.run([*agentapi(), "new-conversation", "--model=pro", f"--title={title}", prompt],
                           env=env, capture_output=True, text=True, timeout=180)
        out, rc = (r.stdout + r.stderr).strip(), r.returncode
    except (Stop, OSError, subprocess.TimeoutExpired) as e:
        out, rc = str(e), 1
    if rc:
        job["launch_errors"] = job.get("launch_errors", 0) + 1
        journal(f"could not start a conversation for job {job['id']}: {out[:200]}")
        return False
    job["launches"] = job.get("launches", 0) + 1
    try:
        job["conversation"] = json.loads(out)["response"]["newConversation"]["conversationId"]
    except (ValueError, KeyError, TypeError):
        pass
    journal(f"started conversation {job['launches']} for job {job['id']}")
    return True


def finish(st, job):
    st["job"] = None
    write_current(None)
    for base in (WS / "jobs", STATE_DIR / "jobs"):
        if base.is_dir():
            for old in sorted(p for p in base.iterdir() if p.is_dir())[:-KEEP_JOBS]:
                shutil.rmtree(old, ignore_errors=True)


def give_up(st, job, why):
    if not job.get("dry_run"):
        for d in job["digests"]:
            for i in d["ids"]:
                st["given_up"][i] = utcnow().isoformat()
    journal(f"gave up on job {job['id']} ({why}). Its digests stay unlabelled for the Gemini fallback "
            f"(the Mac's 22:00 run, then GitHub's).")
    finish(st, job)


def retry(st, job, why):
    """Another conversation for the job, or give up after MAX_LAUNCHES."""
    if why:
        journal(f"job {job['id']}: {why}")
    if job.get("launches", 0) >= MAX_LAUNCHES:
        give_up(st, job, f"{job['launches']} conversations did not finish it")
        return
    if job.get("launch_errors", 0) >= MAX_LAUNCH_ERRORS:
        give_up(st, job, f"Antigravity would not start a conversation {job['launch_errors']} times")
        return
    for m in ("SUBMITTED", "FAILED"):
        try:
            (WS / "jobs" / job["id"] / m).unlink()
        except OSError:
            pass
    launch(st, job)


# ======================================================================
# Applying a submitted job: Claude's review, then send or draft
# ======================================================================
def claude_bin():
    for c in (shutil.which("claude"), str(Path.home() / ".local/bin/claude"), "/opt/homebrew/bin/claude",
              "/usr/local/bin/claude"):
        if c and Path(c).exists():
            return c
    return None


def run_claude(prompt, schema, system, log_path=None, timeout=600):
    """Claude Code headless, on the Claude subscription it is signed in with. Returns (answer, error).

    ANTHROPIC_API_KEY is removed from its environment so it can never bill the API. --safe-mode
    skips CLAUDE.md, skills, hooks, plugins and MCP servers; --tools "" gives it no tools.
    """
    exe = claude_bin()
    if not exe:
        return None, "the claude command is not installed"
    env = {k: v for k, v in os.environ.items()
           if k not in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDECODE")}
    cmd = [exe, "-p", "--safe-mode", "--tools", "", "--no-session-persistence", "--model", CLAUDE_MODEL,
           "--output-format", "json", "--json-schema", json.dumps(schema), "--system-prompt", system]
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=timeout, env=env,
                           cwd=str(STATE_DIR))
    except subprocess.TimeoutExpired:
        return None, f"no answer within {timeout // 60} minutes"
    if log_path:
        write_json(log_path, {"prompt": prompt, "rc": r.returncode, "stdout": r.stdout[-20000:], "stderr": r.stderr[-4000:]})
    try:
        out = json.loads(r.stdout)
    except ValueError:
        return None, f"exit {r.returncode}: {(r.stderr or r.stdout).strip()[:200]}"
    if out.get("is_error") or out.get("subtype") != "success":
        return None, str(out.get("result") or out.get("subtype") or "error")[:200]
    answer = out.get("structured_output")
    if not isinstance(answer, dict):
        return None, "its answer was not in the expected shape"
    return answer, None


def claude_review(q, draft, pd):
    deadline = q.get("deadline_raw") or "not stated"
    prompt = f"""THE JOURNALIST'S REQUEST
Title: {q['title']}
Outlet: {q['outlet'] or '-'} · Journalist: {q['journalist'] or '-'}
Deadline: {deadline}
{q['query']}

FACTS ABOUT NAHID: the only things a pitch may state about him or AI Profit Lab
{rules.SPOKESPERSON_FACTS}

THE DRAFT
{draft['text'].strip()}

The drafter's notes. Why it fits: {draft.get('fit_note', '').strip() or '-'} Send only if true: {draft.get('only_if_true', '').strip() or '(nothing)'}

{rules.REVIEW_TASK}
"""
    review, err = run_claude(prompt, rules.REVIEW_SCHEMA, rules.REVIEW_SYSTEM, pd / "review" / f"{q['id']}.json")
    if review and (review.get("verdict") not in ("send", "hold") or not isinstance(review.get("text"), str)):
        return None, "its answer was missing the verdict or the text"
    return review, err


def send_blockers(q, d, draft, review, err, final, sent_24h, cap, now):
    """Why this pitch may not go out by itself. Empty means it may."""
    if review is None:
        return [f"Claude's review didn't run ({err}), and nothing goes out unreviewed"]
    b = []
    if review["verdict"] != "send":
        b.append("Claude says hold: " + (review.get("hold_reason") or "no reason given"))
    remaining = ["Claude: " + x for x in review.get("remaining") or [] if x.strip()]
    b += remaining
    # The generic reasons only when Claude's own list doesn't already spell them out.
    if not review.get("eligible") and not remaining:
        b.append("Claude: Nahid may not be who the journalist asked for")
    if not review.get("answers_request") and not remaining:
        b.append("Claude: it doesn't answer everything the journalist asked")
    if rules.PLACEHOLDER.search(final) and not remaining:
        b.append("fill in the [ADD: ...] gap(s)")
    if (draft.get("only_if_true") or "").strip():
        b.append("send only if true: " + draft["only_if_true"].strip())
    b += rules.text_problems(final, q["query"], False)
    new = (rules.figures(final) - rules.figures(draft["text"]) - rules.figures(q["query"])
           - rules.figures(rules.SPOKESPERSON_FACTS))
    if new:
        b.append("Claude's rewrite has figures the draft didn't: " + ", ".join(sorted(new)))
    if int(d.get("fit") or 0) < MIN_FIT_TO_SEND:
        b.append(f"fit {d.get('fit')} of 5: only {MIN_FIT_TO_SEND}+ goes out by itself")
    if not HARO_REPLY.fullmatch(q.get("email") or ""):
        b.append("the reply address wasn't read from a HARO digest by code")
    deadline = q.get("deadline_utc")
    if deadline is None:
        b.append("the deadline couldn't be read")
    elif deadline <= now + SEND_LEAD:
        b.append("the deadline is less than 30 minutes away")
    if sent_24h >= cap:
        b.append(f"{cap} pitches have gone out in the last 24 hours (the daily cap)")
    return list(dict.fromkeys(b))


def review_notes(no_ai, review, err, blockers, send_on, draft, final):
    """Lines for the draft's notes block: what Claude did and why it wasn't sent."""
    if no_ai:
        return ["Drafted by: Antigravity. Talking points are never sent and Claude doesn't edit them."], []
    extra = []
    if review is None:
        extra.append(f"Claude:      the review didn't run ({err})")
    else:
        verdict = review["verdict"].upper()
        if review["verdict"] == "hold" and review.get("hold_reason"):
            verdict += f": {review['hold_reason']}"
        extra.append(f"Claude:      {verdict}")
        if review.get("fixed"):
            extra.append("Claude fixed: " + "; ".join(x.strip().rstrip(".") for x in review["fixed"]))
        if review.get("changes"):
            extra.append("Voice edit:  " + review["changes"])
    if not blockers:
        extra.append("REVIEW MODE: this passed every check, so with sending on it would have gone out by itself.")
    else:
        extra.append(("REVIEW MODE: with sending on, this would still wait for you, because:" if not send_on
                      else "NOT SENT, because:"))
        extra += [f"  - {x}" for x in blockers]
    appendix = []
    if review is not None and final.strip() != draft["text"].strip():
        appendix = ["", "Antigravity's draft, before Claude's edit:", draft["text"].strip()]
    return extra, appendix


def count_sent_24h(service):
    res = service.users().messages().list(userId="me", q='in:sent newer_than:1d "HARO Pitch"',
                                          maxResults=50).execute(num_retries=5)
    return len(res.get("messages", []))


def send_pitch(service, h, q, text):
    from email.mime.text import MIMEText
    msg = MIMEText(h.pitch_body(q, text), "plain", "utf-8")
    msg["to"] = q["email"]
    msg["from"] = h.PITCH_FROM
    msg["subject"] = h.pitch_subject(q)
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    # No retries: a retry after a lost response could send it twice. A failure leaves the job
    # submitted; the next run finds the pitch in Sent if it did go, and skips it.
    res = service.users().messages().send(userId="me", body={"raw": raw}).execute()
    with (STATE_DIR / "sent.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"at": utcnow().isoformat(), "to": q["email"], "title": q["title"],
                            "outlet": q["outlet"], "id": res.get("id")}) + "\n")
    return res


def label_digests(service, h, job, label_id=None):
    label_id = label_id or h.get_processed_label_id(service)
    for d in job["digests"]:
        for i in d["ids"]:
            h.mark_digest_processed(service, i, label_id)


def apply_job(st, job):
    jid, dry = job["id"], job.get("dry_run")
    jd, pd = WS / "jobs" / jid, STATE_DIR / "jobs" / jid
    queries = read_json(pd / "queries.json", [])
    problems = check_job(jd, queries)        # against the runner's copy of the queries, not the agent's
    if problems:
        job["last_problems"] = problems[:30]
        retry(st, job, f"the submitted files failed the check ({len(problems)} problems); sent back to the agent")
        return
    job["applies"] = job.get("applies", 0) + 1
    save_state(st)
    if job["applies"] > MAX_APPLIES:
        give_up(st, job, f"applying it failed {MAX_APPLIES} times")
        return
    send_on, cap = settings()
    h = hep()
    service = h.get_gmail_service()
    decisions = {d["id"]: d for d in read_json(jd / "screening.json")["decisions"]}
    pitched_a, pitched_t = (set(), set()) if dry else h.already_pitched(service)
    sent_24h = 0 if dry else count_sent_24h(service)
    now = utcnow()
    chosen = [q for q in queries if decisions[q["id"]]["decision"] == "PITCH"]
    for q in chosen:
        q["deadline_utc"] = datetime.datetime.fromisoformat(q["deadline_utc"]) if q.get("deadline_utc") else None
    outcomes = []
    for q in sorted(chosen, key=lambda x: x["deadline_utc"] or now + datetime.timedelta(days=365)):
        d = decisions[q["id"]]
        draft = read_json(jd / "drafts" / f"{q['id']}.json")
        o = {"id": q["id"], "title": q["title"], "outlet": q["outlet"], "fit": d["fit"]}
        outcomes.append(o)
        if q["deadline_utc"] and q["deadline_utc"] <= now + SEND_LEAD:
            o["action"] = "expired"
            continue
        if not dry and (q["email"].lower() in pitched_a or h.pitch_title_key(q["title"]) in pitched_t):
            o["action"] = "already drafted or sent"
            continue
        no_ai = notes_only(q, d)
        review, err = (None, None) if no_ai else claude_review(q, draft, pd)
        final = ((review or {}).get("text") or "").strip() or draft["text"].strip()
        blockers = [] if no_ai else send_blockers(q, d, draft, review, err, final, sent_24h, cap, now)
        o.update(talking_points=no_ai, claude=(review or {}).get("verdict") or (None if no_ai else f"error: {err}"),
                 blockers=blockers, would_send=not no_ai and not blockers)
        if o["would_send"] and send_on and not dry:
            send_pitch(service, h, q, final)
            sent_24h += 1
            o["action"] = "sent"
        else:
            extra, appendix = review_notes(no_ai, review, err, blockers, send_on, draft, final)
            result = {"text": final, "fit_note": draft["fit_note"], "only_if_true": draft["only_if_true"]}
            subject, body = h.build_draft(q, result, no_ai, extra, appendix)
            if dry:
                (pd / "out").mkdir(parents=True, exist_ok=True)
                (pd / "out" / f"{q['id']}.txt").write_text(
                    f"To: {q['email']}\nFrom: {h.PITCH_FROM}\nSubject: {subject}\n\n{body}", encoding="utf-8")
                o["action"] = "would send" if o["would_send"] else "would draft"
            else:
                h.create_gmail_draft(service, q["email"], subject, body)
                o["action"] = "draft"
        pitched_a.add(q["email"].lower())
        pitched_t.add(h.pitch_title_key(q["title"]))
        write_json(pd / "outcome.json", outcomes)
    write_json(pd / "outcome.json", outcomes)
    if not dry:
        label_digests(service, h, job)
    count = lambda *acts: sum(o.get("action") in acts for o in outcomes)  # noqa: E731
    journal(f"job {jid} done" + (" (dry run, see runner/state/jobs/%s/out)" % jid if dry else "") + ": "
            f"{len(queries)} screened, {len(chosen)} to pitch. Sent {count('sent')}, "
            f"drafts {count('draft', 'would draft', 'would send')} "
            f"({sum(o.get('would_send', False) for o in outcomes)} passed every check, "
            f"{sum(o.get('talking_points', False) for o in outcomes)} are talking points), "
            f"skipped {count('expired', 'already drafted or sent')}.")
    finish(st, job)


# ======================================================================
# Runner commands
# ======================================================================
def cmd_trigger(a):
    """Every 10 minutes from Antigravity's scheduler. Applies submitted work, restarts a stuck
    job, or starts a job for new digests."""
    require_runner()
    if not take_lock():
        print("busy: another run holds the lock")
        return 0
    try:
        sync_workspace()
        st = load_state()
        job = st.get("job")
        if job:
            state, why = marker(job)
            if state == "submitted":
                try:
                    apply_job(st, job)
                except (Exception, SystemExit) as e:   # get_gmail_service exits on a bad token
                    save_state(st)
                    journal(f"applying job {job['id']} failed ({type(e).__name__}: {str(e)[:200]}); "
                            f"the next run tries again")
                    return 1
            elif state == "failed":
                retry(st, job, f"the agent gave up: {why[:200]}")
            elif not job.get("launches"):
                retry(st, job, None)                       # the last attempt to start a conversation failed
            elif time.time() - job.get("launched", 0) > AGENT_TIMEOUT:
                retry(st, job, f"no submission within {AGENT_TIMEOUT // 60} minutes")
            else:
                print(f"agent at work on job {job['id']} ({(time.time() - job['launched']) / 60:.0f} min)")
                return 0
            save_state(st)
            if st.get("job"):
                return 0
        h = hep()
        try:
            service = h.get_gmail_service()
        except SystemExit:
            # A dead token stops every run before anything reaches log.md (2026-10-17: 24 silent hours),
            # so after half an hour of failures say so there, once. A short Wi-Fi gap stays out of it.
            down = st.setdefault("gmail_down", {"since": time.time()})
            if not down.get("logged") and time.time() - down["since"] > 1800:
                down["logged"] = True
                journal("Gmail login is failing, so no digest is being read (the reason is in sidecar.log). If it "
                        "says invalid_grant: run `python3 tools/authenticate_gmail.py`, then "
                        "`python3 execution/haro_agent.py setup --copy-token`, from Website SEO")
            save_state(st)
            raise
        if st.pop("gmail_down", {}).get("logged"):
            journal("Gmail login works again")
        groups, label_id = find_digests(service, h, st, a.dry_run)
        if not groups:
            save_state(st)
            print("nothing new")
            return 0
        job = make_job(service, h, st, groups, label_id, a.dry_run)
        if job:
            st["job"] = job
            launch(st, job)
        save_state(st)
        return 0
    finally:
        release_lock()


def cmd_apply(a):
    """Review and send/draft a submitted job now, without waiting for the schedule."""
    require_runner()
    if not take_lock():
        print("busy: another run holds the lock")
        return 1
    try:
        st = load_state()
        job = st.get("job")
        if not job or marker(job)[0] != "submitted":
            print(f"nothing submitted (job: {job['id'] + ' ' + str(marker(job)[0]) if job else 'none'})")
            return 0
        apply_job(st, job)
        save_state(st)
        return 0
    finally:
        release_lock()


def cmd_selftest(a):
    """Checks what an unattended run needs, from wherever it runs (the sidecar runs it too)."""
    require_runner()
    ok = True
    h = hep()
    try:
        service = h.get_gmail_service()
        email = service.users().getProfile(userId="me").execute()["emailAddress"]
        aliases = service.users().settings().sendAs().list(userId="me").execute().get("sendAs", [])
        alias = next((s for s in aliases if s["sendAsEmail"].lower() == h.PITCH_FROM), None)
        status = "missing" if not alias else (alias.get("verificationStatus") or "accepted (primary)")
        good = alias is not None and status in ("accepted", "accepted (primary)")
        ok &= good
        print(f"gmail: {'ok' if good else 'PROBLEM'} (signed in as {email}; {h.PITCH_FROM} send-as: {status})")
    except BaseException as e:  # noqa: B902 (get_gmail_service exits on a bad token)
        ok = False
        print(f"gmail: PROBLEM ({type(e).__name__}: {e})")
    answer, err = run_claude("Reply with ok=true.", {"type": "object", "properties": {"ok": {"type": "boolean"}},
                                                     "required": ["ok"]}, "Answer in the requested shape.", timeout=180)
    ok &= bool(answer and answer.get("ok"))
    print(f"claude: {'ok' if answer and answer.get('ok') else 'PROBLEM'} ({err or CLAUDE_MODEL + ' on the subscription'})")
    in_sidecar = bool(os.environ.get("ANTIGRAVITY_AGENTAPI_EXE"))
    print(f"antigravity: {'inside a sidecar, can start conversations' if in_sidecar else 'not in a sidecar (fine for a manual run)'}")
    send_on, cap = settings()
    print(f"sending: {'ON' if send_on else 'off (review mode)'}, cap {cap} per 24 hours")
    journal(f"selftest {'passed' if ok else 'FAILED'}" + (" (in the sidecar)" if in_sidecar else ""))
    return 0 if ok else 1


# ======================================================================
# Setup and status (from the website checkout)
# ======================================================================
def deploy(copy_token):
    """Copy the code and the Gmail credentials from this checkout into the runner."""
    src_root = HERE.parent
    for rel in DEPLOY:
        dst = RUNNER / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_root / rel, dst)
    for name in ("credentials.json", "token.json"):
        src, dst = src_root / name, RUNNER / name
        if src.exists() and (name != "token.json" or copy_token or not dst.exists()):
            shutil.copy2(src, dst)
            os.chmod(dst, 0o600)
    (WS / "jobs").mkdir(parents=True, exist_ok=True)
    sync_workspace()
    if not CURRENT.exists():
        write_current(None)
    print(f"  deployed to {RUNNER} (workspace {WS})")


def ensure_project():
    pid = project_id()
    f = CONFIG / "projects" / f"{pid}.json"
    data = read_json(f, {}) or {}
    data.update({
        "id": pid,
        "name": quote("AI Profit Lab HARO"),
        "projectResources": {"resources": [{"gitFolder": {"folderUri": "file://" + quote(str(WS)), "allowWrite": True}}]},
        "permissionGrants": {"allow": sorted(set((data.get("permissionGrants") or {}).get("allow", [])) | set(GRANTS))},
        "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%S.000000Z", time.gmtime()),
    })
    write_json(f, data)
    print(f"  Antigravity project: {f}")
    return pid


def cmd_setup(a):
    require_checkout()
    import setup_antigravity_publisher as sap
    deploy(a.copy_token)
    pid = ensure_project()
    run_sh = str(RUNNER / "execution" / "haro_run.sh")
    old = read_json(CONFIG / "sidecars" / SIDECAR_ID / "sidecar.json", {}) or {}
    disabled = False if a.enable else True if a.disable else old.get("disabled", True)
    env = dict(old.get("env") or {})
    env.update(ANTIGRAVITY_PROJECT_ID=pid)
    env.setdefault("HARO_SEND", "off")
    env.setdefault("HARO_DAILY_CAP", "5")
    if a.sending:
        env["HARO_SEND"] = a.sending
    if a.daily_cap:
        env["HARO_DAILY_CAP"] = str(a.daily_cap)
    sap.write_sidecar(SIDECAR_ID, {
        "builtin": "schedule",
        "args": ["*/10 * * * *", "/bin/sh", run_sh, "trigger"],
        "restart_policy": "always",
        "display_name": "AI Profit Lab HARO",
        "description": ("Every 10 minutes: new HARO digests become a job that an Antigravity conversation "
                        "screens and drafts; Claude then checks and humanizes each pitch, and code sends it "
                        "or leaves it in Gmail Drafts (Website SEO/execution/haro_agent.py)."),
        "env": env,
        "disabled": disabled,
    })
    sap.enable_in_config(SIDECAR_ID, pid, not disabled)
    for kind, flag in (("dry", a.dry_run_now), ("selftest", a.selftest_now)):
        if flag:
            sap.write_sidecar(ONE_OFF[kind], {
                "command": "/bin/sh",
                "args": [run_sh, "trigger", "--dry-run"] if kind == "dry" else [run_sh, "selftest"],
                "restart_policy": "never",
                "display_name": "AI Profit Lab HARO: " + ("one dry run" if kind == "dry" else "self-test"),
                "description": ("Runs once: a HARO job from the latest digests that sends nothing and changes "
                                "nothing in Gmail." if kind == "dry" else
                                "Runs once: checks Gmail, Claude and Antigravity from inside a sidecar."),
                # A new value each time: Antigravity reruns a sidecar only when its file changes.
                "env": {**env, "APL_REQUESTED": time.strftime("%Y-%m-%dT%H:%M:%S"),
                        "HARO_DRY_DIGESTS": str(a.dry_run_digests)},
            })
            sap.enable_in_config(ONE_OFF[kind], pid, True)
    if a.cleanup:
        data = read_json(CONFIG / "config.json", {}) or {}
        for sid in ONE_OFF.values():
            shutil.rmtree(CONFIG / "sidecars" / sid, ignore_errors=True)
            data.get("sidecars", {}).pop(sid, None)
        write_json(CONFIG / "config.json", data)
        print("  one-off sidecars removed")
    print(f"\nSchedule (every 10 minutes): {'PAUSED' if disabled else 'ON'}. Antigravity must be open for it to fire.")
    print(f"Sending: {'ON' if env['HARO_SEND'] == 'on' else 'OFF (review mode: every pitch is a Gmail draft)'}, "
          f"cap {env['HARO_DAILY_CAP']} per 24 hours.")
    print(f"Log: {LOG}")
    return 0


def cmd_status(a):
    sc = read_json(CONFIG / "sidecars" / SIDECAR_ID / "sidecar.json", {}) or {}
    send_on, cap = settings()
    print(f"Schedule: {'ON' if sc and not sc.get('disabled', True) else 'PAUSED' if sc else 'not set up'}"
          f" · Sending: {'ON' if send_on else 'off (review mode)'} · cap {cap}/24h")
    if HERE.parent.joinpath("directives").is_dir() and HERE != (RUNNER / "execution").resolve():
        stale = [rel for rel in DEPLOY if not (RUNNER / rel).exists()
                 or (RUNNER / rel).read_bytes() != (HERE.parent / rel).read_bytes()]
        if stale:
            print(f"Runner is out of date ({', '.join(stale)}): run `python3 execution/haro_agent.py setup`.")
    st = load_state()
    job = st.get("job")
    if job:
        print(f"Job: {job['id']} · {job['count']} requests · {marker(job)[0] or 'agent at work'}"
              f" · conversations {job.get('launches', 0)}" + (" · dry run" if job.get("dry_run") else ""))
    else:
        print("Job: none open")
    if st.get("gmail_down"):
        since = datetime.datetime.fromtimestamp(st["gmail_down"]["since"], ZoneInfo("Asia/Muscat"))
        print(f"Gmail: login FAILING since {since:%Y-%m-%d %H:%M} Muscat (the reason is in sidecar.log; if it says "
              f"invalid_grant, run tools/authenticate_gmail.py, then setup --copy-token)")
    if st["given_up"]:
        print(f"Left to the Gemini fallback: {len(st['given_up'])} digest email(s)")
    if LOG.exists():
        print("\nLast log lines:")
        print("".join(LOG.read_text(encoding="utf-8").splitlines(True)[-12:]), end="")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("next")
    sub.add_parser("check")
    sub.add_parser("submit")
    p = sub.add_parser("fail")
    p.add_argument("reason")
    p = sub.add_parser("trigger")
    p.add_argument("--dry-run", action="store_true",
                   help="a job from the latest digests (HARO_DRY_DIGESTS, default 2); nothing sent or labelled")
    sub.add_parser("apply")
    sub.add_parser("selftest")
    sub.add_parser("status")
    p = sub.add_parser("setup")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--enable", action="store_true", help="switch the 10-minute schedule on")
    g.add_argument("--disable", action="store_true", help="pause the schedule")
    p.add_argument("--sending", choices=["on", "off"], help="on: pitches that pass every check go out by themselves")
    p.add_argument("--daily-cap", type=int, help="most pitches sent in 24 hours (default 5)")
    p.add_argument("--copy-token", action="store_true", help="replace the runner's Gmail token with this checkout's")
    p.add_argument("--dry-run-now", action="store_true", help="start one dry run in Antigravity right away")
    p.add_argument("--dry-run-digests", type=int, default=2, help="how many of the latest digests the dry run takes")
    p.add_argument("--selftest-now", action="store_true", help="check Gmail, Claude and Antigravity from a sidecar")
    p.add_argument("--cleanup", action="store_true", help="remove the one-off dry-run and self-test sidecars")
    a = ap.parse_args()
    fn = {"next": cmd_next, "check": cmd_check, "submit": cmd_submit, "fail": cmd_fail, "trigger": cmd_trigger,
          "apply": cmd_apply, "selftest": cmd_selftest, "status": cmd_status, "setup": cmd_setup}[a.cmd]
    try:
        sys.exit(fn(a) or 0)
    except Stop as e:
        print(f"STOP: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
