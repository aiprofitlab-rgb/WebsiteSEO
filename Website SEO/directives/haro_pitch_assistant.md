# Directive: HARO & Media Pitch Assistant

## Purpose
Automatically scan daily media query digests (HARO, Connectively, Featured.com, SourceBottle, etc.) sent to `ai.profit.lab2026@gmail.com`, filter for relevant expert opportunities in AI, Automation, and Web Design, and reply to them: Google Antigravity drafts, Claude checks and humanizes, and code either sends a pitch or leaves it in Gmail Drafts for Nahid.

## Two drafters (since 2026-10-16)

1. **Main: Antigravity + Claude** (`execution/haro_agent.py`), every 10 minutes while the Mac is on and the Antigravity app is open. No API cost: the drafting runs on Nahid's Google AI Pro plan (Antigravity) and the review on his Claude subscription (Claude Code headless, signed in with claude.ai, never an API key).
2. **Fallback: the Gemini API drafter** (`execution/haro_email_processor.py`, free tier). Since 2026-10-18 it runs on the Mac every 30 minutes while the Mac is awake, with `--defer-to-agent --min-age-hours 3`. While the main pipeline is alive, it takes only the digests that pipeline handed over (`given_up` / `not_ours` in its state). When the pipeline is down (Antigravity closed, schedule off, Gmail failing), it takes digests older than 3 hours. GitHub runs it only by hand. It only ever drafts.

Both read the facts and rules from `execution/haro_rules.py`, so they screen and draft the same way.

---

## Identity & Spokesperson Profile

- **Spokesperson Name**: Nahid Abyari (journalists need the full name to quote him)
- **Title**: Founder, AI Profit Lab
- **Brand**: **AI Profit Lab**
- **Legal Entity**: **Lotus Gulf International** (CR 1570092), per the `aiprofitlab-brand` skill and the live About page. (The older name "International Gulf Lotus SPC" is wrong; the website's AGENTS.md still carries it.)
- **Website**: [https://aiprofitlab.io](https://aiprofitlab.io)
- **The facts a pitch may state** live in `SPOKESPERSON_FACTS` in `execution/haro_rules.py` (shared by both drafters and by Claude's review), sourced from the live About page: an engineer who built and ran a real distribution business (never name the country), the response-time lesson, what AI Profit Lab builds, his working rules, and who he turns away. Add a fact there only once Nahid confirms it. Never add a client name, a result, a percentage or a count of years.
- **Core Expertise** (topics he can give an opinion on, not facts to claim):
  - Practical AI implementation for businesses & enterprise workflows.
  - Autonomous AI agents & multi-agent systems.
  - Business process automation (reducing operational waste, CRM/ERP integrations).
  - Modern web architecture, conversion-focused web design, and high-performance SEO.
  - Data privacy, compliance (PDPL / GDPR), and secure AI deployment.

---

## Qualification Criteria

### Target Topics (ACCEPT)
1. **Artificial Intelligence & LLMs**: Real-world business applications, generative AI adoption, agentic systems, AI prompt engineering, AI ethics/regulations.
2. **Business Automation**: Automating repetitive tasks, workflow optimization, robotic process automation (RPA), AI tooling for SMBs/enterprises.
3. **Web Design & Development**: Modern UX/UI principles, speed optimization, SEO architecture, converting visitors into leads, web design trends.
4. **Technology Entrepreneurship**: Running AI-first businesses, digital transformation in emerging markets (GCC / Middle East / Global).

### Disqualification Criteria (REJECT)
1. **Expired Deadlines**: Any query whose submission deadline has already passed, or is less than an hour away (no time to review). Checked in code, not by Gemini.
2. **Not eligible**: The journalist asks for a role, credential, company size, location or personal experience Nahid doesn't have: CIO/CTO/CISO of a larger firm, nonprofit leader, MD, licensed advisor, "US-based", "e-commerce store owners", parents, homeowners. This was the old agent's biggest miss: it matched on topic alone. (On 2026-10-16 it drafted a reply to Fortune's request for a *nonprofit* CIO/CTO.)
3. **Irrelevant Topics**: Healthcare/medical advice, personal finance/stocks, real estate, diet/fitness, beauty/fashion, travel, relationships, or unrelated niches.
4. **Pay-to-play**: Sponsored placements, paid awards or listings ("TechRound's PR54 Is Open For Entries"), product samples, gift guides.

### Journalists who reject AI-written replies
About 45% of HARO queries carry the line **"No AI Pitches Considered"**, and some say "written in your own words". For these the agent still drafts, but writes **talking points** rather than a pitch. The subject is tagged `[WRITE IT YOURSELF]` and the notes explain why. Nahid writes the reply himself from those points and removes the tag before sending. Never send AI-written text to these journalists.

---

## Winning Pitch Guidelines for Journalists

HARO journalists review dozens of pitches. Our drafted responses must adhere to strict PR best practices:

1. **Subject Line**:
   `HARO Pitch: [Query Title] — Nahid Abyari, AI Profit Lab` (with `[WRITE IT YOURSELF] ` in front for the no-AI queries above).
2. **From / To**: From `nahid@aiprofitlab.io`, the address the HARO account is registered to (a verified send-as alias in this Gmail). To: the query's `reply+…@helpareporter.com` address, copied from the digest by code and never typed by Gemini.
3. **Opening (1 sentence)**:
   Who Nahid is and why he can answer *this* query.
4. **Answers (2–4 short paragraphs or bullets, 120–250 words)**:
   - Answer the journalist's questions directly, in the order asked, and include every item they list.
   - A concrete opinion, a practical tip or how something works in practice, ready to quote.
   - Plain brand voice: no hype words (the brand's banned list is in the prompt and in `BANNED_WORDS`).
5. **No invented facts**: Never invent clients, results, percentages, years of experience or world statistics, and never claim Nahid did, built, switched or measured anything the facts don't say. When the query needs first-hand experience, those parts become `[ADD: …]` placeholders (at most 3). A placeholder says what to add and never suggests an answer. The notes add a **"Send only if true:"** line naming the experience the reply depends on. Code flags any figure the query doesn't explain, any banned word, and any placeholder that suggests a number, on the notes' `Check:` line.
6. **Notes block**: Each draft opens with a notes block for Nahid (outlet, journalist, deadline in ET, Muscat time and UTC, why it fits, placeholders to fill, claims to check, and the full query). It ends at a dashed line, and **must be deleted before sending**.
7. **Signature** (the brand signature, verbatim, from the `aiprofitlab-brand` skill):
   Nahid Abyari · Founder, AI Profit Lab · hello@aiprofitlab.io · +968 9924 5250 · aiprofitlab.io · LinkedIn https://www.linkedin.com/in/nahid-aby · headshot on request.
5. **Safety & Inbox Rules**:
   - **SENDING**: Only `haro_agent.py` ever sends, and only when Nahid has switched sending on (`python3 execution/haro_agent.py setup --sending on`). It was built on 2026-10-16 with sending OFF for a review week: every pitch is a draft whose notes say whether it would have gone out. Even with sending on, a pitch goes out only when ALL of these hold, and otherwise stays a draft that says why:
     - the journalist accepts AI-written replies (talking points for the rest are never sent);
     - Claude's verdict is "send", with nothing left in "remaining", eligible and answers_request both true;
     - no `[ADD: ...]` placeholder and no "send only if true" condition;
     - the final text passes `haro_rules.text_problems` (length, no greeting/sign-off/markdown, no banned words, no country, no figure the request doesn't explain), and Claude's rewrite adds no figure the draft didn't have;
     - fit is 4 or 5;
     - the reply address is a `reply+…@helpareporter.com` address code read from the digest;
     - the deadline is readable and more than 30 minutes away;
     - fewer than 5 HARO pitches have gone out in the last 24 hours (`--daily-cap`).
   - The Gemini fallback never sends anything.
   - **LABEL AS PROCESSED**: Once a digest email has been fully processed (its queries analyzed and qualifying drafts created), add the Gmail label `HARO Processed` to it (and mark it read). The label, not read status, is what prevents duplicate work, so a digest Nahid has already opened still gets pitched. A digest whose Gemini analysis fails stays unlabelled and is retried on the next run.

---

## Execution Tools & Architecture

### Main pipeline: `execution/haro_agent.py` (Antigravity drafts, Claude reviews)
- **Where it runs**: `~/Developer/aiprofitlab-haro/`, kept off the Desktop because Antigravity's background jobs may not be allowed to read it. `runner/` holds a copy of the code, the Gmail token (its own copy, refreshed independently) and `state/` (job state, the authoritative queries with reply addresses, Claude's raw reviews, `sent.jsonl`, and **`log.md`, the place to look first**). `workspace/` is the Antigravity agent's whole world: `INSTRUCTIONS.md` (from `directives/antigravity_haro.md`), `haro.py` + `haro_rules.py` (copies), and `jobs/<id>/` with the brief, a queries copy *without* reply addresses, the agent's `screening.json` and `drafts/`. The agent can't see the token or the addresses, and can't change where anything is sent.
- **Deploying**: the runner only has what `setup` copied. After editing `haro_agent.py`, `haro_rules.py`, `haro_email_processor.py`, `haro_run.sh` or `directives/antigravity_haro.md`, run `python3 execution/haro_agent.py setup` from the checkout. `status` says when the runner is out of date.
- **Antigravity**: project "AI Profit Lab HARO" (workspace = `workspace/`, grant `command(python3 haro.py)`), and the scheduled sidecar `aiprofitlab-haro` running `runner/execution/haro_run.sh trigger` every 10 minutes. The send switch (`HARO_SEND`) and cap (`HARO_DAILY_CAP`) live in that sidecar's env in `~/.gemini/config/sidecars/aiprofitlab-haro/sidecar.json`, outside the agent's reach. Its output: `~/.gemini/antigravity/sidecar_data/aiprofitlab-haro/logs/sidecar.log`.
- **A run**: unlabelled HARO-format digests → queries split and deadlines read in code → expired and already-pitched dropped → job + brief → `agentapi new-conversation --model=pro`. The agent screens every query, drafts each PITCH, loops `python3 haro.py check` until PASS, then `submit`. The next trigger re-checks against the runner's queries, runs Claude on each pitch (`claude -p --safe-mode --tools "" --json-schema …`, prompt in `haro_rules.REVIEW_TASK`), applies the send gates above, sends or drafts, and labels the digests `HARO Processed`.
- **When things fail**: an agent that hasn't submitted after 60 minutes gets a second conversation; after 2 the job is given up, and its digests stay unlabelled for the Gemini fallback. Files that fail the re-check go back to the agent with the problems listed. A Claude error (usage limit, timeout) means that pitch is drafted, never sent. Apply errors are retried on the next run, up to 3 times; the Drafts/Sent dedupe stops anything being created twice.
- **Commands**: `setup [--enable|--disable] [--sending on|off] [--daily-cap N] [--dry-run-now] [--selftest-now] [--cleanup]` and `status` from the checkout; `trigger [--dry-run]`, `apply`, `selftest` in the runner (`python3 ~/Developer/aiprofitlab-haro/runner/execution/haro_agent.py …`). A dry run takes the newest digests (2, or `--dry-run-digests N`), labelled or not, and writes would-be emails to `runner/state/jobs/<id>-dry/out/` without touching Gmail.

### Fallback: `execution/haro_email_processor.py` (Gemini API)

- **Main Processor**: [`execution/haro_email_processor.py`](file:///Users/nahid/Desktop/Nahid/AI%20Profit%20Lab/Website/Website%20SEO/execution/haro_email_processor.py)
  - Connects to Gmail API via OAuth.
  - Queries digest emails without the `HARO Processed` label (`-label:haro-processed`, `newer_than:7d` across HARO, Connectively, Featured, SourceBottle, Qwoted), read or unread. Creates the label on first use.
  - **Splits each HARO digest into queries in code** (`parse_haro_digest`): title, journalist, outlet, reply address, deadline, the "No AI Pitches" flag, and the full query text. On 2026-10-16 it was tested on 75 digests: 1,564 queries, none miscounted, no fields missing. Gemini only lists queries for digests in another format (Connectively, Qwoted, …).
  - **Reads deadlines in code** (`parse_deadline`, ET → UTC, with year rollover) and drops expired queries before Gemini sees them.
  - **Gemini models** (`HARO_MODELS`, override with the `HARO_GEMINI_MODELS` env var): 3.7 Flash → 3 Flash Preview → 3.5 Flash → flash-latest (3.8) → 3.6 Flash. On this key's free tier, **Gemini Pro has no quota at all**, and each Flash model allows about **20 requests a day**. The article publisher (`daily_publish.py`) uses 3.8 → 3.6 → 3.5 on the same key, so HARO starts with models the publisher doesn't use. A 429 for a spent daily quota moves straight to the next model rather than retrying. A day of HARO costs roughly one call per digest plus one per pitch. **Testing burns the same quota**: run evaluations with `HARO_GEMINI_MODELS` set to models the publisher doesn't use.
  - **Screens every query with Gemini** (`screen_queries`). The output is held to a schema: for each query, eligible or not, a one-line reason, a fit score from 1–5, PITCH/SKIP, and whether it forbids AI replies. A pitch needs PITCH and fit ≥ 3. Every decision is printed to the log, so a missed query can be traced.
  - **Drafts each chosen query separately** (`write_pitch`), using only `SPOKESPERSON_FACTS`. Code adds the notes block, greeting, signature and subject.
  - **Avoids duplicates by reply address** (exact; the two digest copies share it), plus the query title, across Drafts and the last 60 days of Sent. Each digest is read once even though it arrives twice, and both copies get the label.
  - `--dry-run` writes the drafts it would create to `.tmp/haro_dryrun/<timestamp>/` and changes nothing in Gmail (it also reads already-labelled digests, for testing).
  - `--delete-expired` lists HARO drafts whose deadline has passed, and `--apply` deletes them. Each one is first saved to `.tmp/haro_deleted_drafts.jsonl`, because the Gmail API deletes drafts permanently. A draft with no readable deadline is kept.
- **Interactive Authenticator**: [`tools/authenticate_gmail.py`](file:///Users/nahid/Desktop/Nahid/AI%20Profit%20Lab/Website/Website%20SEO/tools/authenticate_gmail.py)
  - Run interactively (`python3 tools/authenticate_gmail.py`) whenever OAuth credentials need initialization or renewal.
  - It only renews the checkout's `token.json`. The runner keeps its own copy, and plain `setup` leaves that copy alone, so follow it with `python3 execution/haro_agent.py setup --copy-token`. The GitHub fallback needs the same file in its `GMAIL_TOKEN_JSON` secret.
- **Mac LaunchAgent**: [`tools/setup_mac_schedule.sh`](file:///Users/nahid/Desktop/Nahid/AI%20Profit%20Lab/Website/Website%20SEO/tools/setup_mac_schedule.sh)
  - Runs every 30 minutes (`StartInterval 1800`) via `~/Library/LaunchAgents/com.aiprofitlab.haro.plist`, with `--defer-to-agent --min-age-hours 3`. launchd catches up after sleep. A shut-down Mac runs nothing.
  - `--defer-to-agent` decides from the main pipeline's footprints. It counts that pipeline as alive when `runner/state/state.json` or the sidecar's `sidecar.log` was written in the last 20 minutes and `gmail_down` isn't set. It never touches the digests of an open job. It also stays idle for the first 20 minutes after a boot or wake (`sysctl kern.waketime`), because at wake both drafters fire at once and would draft the same digest twice. An idle run writes one `fallback idle: …` line to `.tmp/haro_stdout.log`.
  - Logs are persisted in `.tmp/haro_stdout.log` and `.tmp/haro_stderr.log`.

---

## Google Cloud OAuth Token Permanence (Self-Annealing Note)

- **Issue**: By default, Google Cloud OAuth projects set to "Testing" status issue refresh tokens that expire after **7 days**. When expired, background cron/launchd jobs fail with `invalid_grant: Token has been expired or revoked`.
- **Permanent Solution**:
  1. Open [Google Cloud Console](https://console.cloud.google.com/) for project `ai-profit-lab-assistant`.
  2. Navigate to **APIs & Services** > **OAuth consent screen**.
  3. Under **Publishing status**, click **PUBLISH APP** (transitioning from "Testing" to "In Production").
  4. In Production status, refresh tokens do not expire after 7 days and remain valid indefinitely until manually revoked.
- **Done 2026-10-17 (Mac time)**: Nahid published the app; it had been in Testing until then. The new token was issued after publishing. The Audience page now shows "Your app requires verification": ignore it. An unverified app may keep restricted scopes such as `gmail.modify` for up to 100 users, and the only cost is the "Google hasn't verified this app" screen at sign-in (Advanced → Go to AI Profit Lab Assistant).
- **GitHub Actions Secret**: the cloud workflow is manual-only since 2026-10-18. Before running it by hand, set the repository secret `GMAIL_TOKEN_JSON` to the contents of `token.json`, and update it after every `tools/authenticate_gmail.py`.

---

## Known Failure Modes (Self-Annealing Log)

- **Cloud fallback failed on every run, 2026-10-03 to 10-15** (13 runs, all at "Set up Python"). `cache: 'pip'` in `setup-python` needs a `requirements.txt` or `pyproject.toml`, and the repo has neither. Removed on 2026-10-16. Don't add it back without adding one of those files. The workflow now also stops with a named `::error::` if `GEMINI_API_KEY` or `GMAIL_TOKEN_JSON` is missing.
- **"Expired token" that wasn't (2026-10-13)**: launchd runs a job missed during sleep as soon as the Mac wakes, often before Wi-Fi is back. The DNS failure was reported as an expired token. The processor now retries a network error 6 times over 2.5 minutes, and says "No network" if it still can't connect. Re-authenticate only when the log shows `invalid_grant` / "expired or invalid".
- **Digests you opened yourself were never pitched (fixed 2026-10-16)**: the search used to find only `is:unread` mail, so a digest opened on the phone before the run was skipped for good. The 2026-10-16 Morning Edition was opened that way within an hour of arriving. The search now uses the `HARO Processed` label instead. On switching, the 21 digests that earlier runs had already processed (per `.tmp/haro_stdout.log`) were labelled by hand, so they weren't pitched again. Not every run writes to that log: drafts made 2026-10-10 06:08–06:21 UTC came from a manual run.
- **Every digest arrives twice**: HARO sends one copy to `nahid@aiprofitlab.io` and one to `ai.profit.lab2026@gmail.com` (two subscriptions). Both copies have the same queries and the same reply addresses. Since 2026-10-16 the processor reads one copy and labels both. Before that, Gemini read each copy separately and picked a *different* "relevant" query from each identical copy (Oct 9 Evening). That inconsistency is what prompted the rewrite.
- **The old all-in-one Gemini step invented details (before 2026-10-16)**: it shortened titles, and once made up a reply address (`reply+nix-data-ai@helpareporter.com`; the real one was `reply+5c58d9e2-…`). It drafted for requests Nahid wasn't eligible for: Fortune wanted a nonprofit CIO/CTO, TechTarget wanted CISOs and excluded vendors, Industry Dive wanted bank IT leaders. It also drafted for off-topic ones (romantic relationships, a holiday gift guide). Its sign-off named the wrong legal entity. All of it was replaced by the code parser, the per-query screening and the fixed facts list.
- **Screening blind spots, fixed in the prompt (2026-10-16)**: Gemini skipped a query about "Gemini 4 Argon" because it didn't recognise the model, which was newer than its training data. It also read a "city and state you work from" attribution field as a US-only requirement. The prompt now says to take the journalist's description as true, and that an attribution field isn't a location requirement.
- **Drafts invent first-hand experience unless told not to (2026-10-16)**: for Techopedia's "companies that switched to smaller models", the first draft said Nahid had "moved our core workflows" and that it "worked as planned". Its placeholders also suggested numbers ("e.g., 7 seconds to under 2"). The old agent's open drafts had the same fault: "In our client audits, consolidating 35,000+ thin facet URLs…", "drops unit operational costs by 60% to 85%". The prompt now forbids claimed experience, and `only_if_true` plus the `Check:` line put whatever is left in front of Nahid.
- **Expired drafts pile up**: run `--delete-expired` (then `--apply`) now and then. On 2026-10-16 it removed 25 of 37 HARO drafts; their copies are in `.tmp/haro_deleted_drafts.jsonl`.
- **One dead token stopped all three drafters (2026-10-17)**: the refresh token last worked at 05:20 UTC and was refused with `invalid_grant` from 06:10 UTC on. The cause was the 7-day expiry for an app in "Testing": the app was still in Testing, and was published that day (see the section above). The runner, the Mac LaunchAgent and the checkout all held the same refresh token, so the main pipeline and the Mac fallback died together. The GitHub fallback had never run at all, because its `GMAIL_TOKEN_JSON` secret was never set. The outage went unnoticed for 24 hours: `get_gmail_service` exits before anything is journaled, so `log.md` and `status` both looked healthy while `sidecar.log` filled with 70+ failures. Since then, `trigger` writes one line to `log.md` after 30 minutes of failed logins, and another when login works again, and `status` prints `Gmail: login FAILING since …`.
- **The Mac clock is on America/Los_Angeles**, not Muscat. The LaunchAgent's 22:00 is 05:00 UTC (09:00 Muscat), which conveniently falls after all three of the previous day's HARO editions. The cloud run is scheduled for 18:00 UTC but GitHub starts it 3–5 hours late.
- **"Run failed" emails every night (until 2026-10-18)**: the GitHub fallback's `GMAIL_TOKEN_JSON` secret was never set, so every scheduled run stopped at "Restore credentials", and each failure emailed the inbox. The main pipeline was fine throughout. HARO sends nothing on Saturday or Sunday, so a weekend of `nothing new` is normal. The nightly cron was removed in favour of the Mac's 30-minute fallback. Without `gh`, read a run's failed step from the public API: `api.github.com/repos/aiprofitlab-rgb/WebsiteSEO/check-runs/<job id>/annotations`.
