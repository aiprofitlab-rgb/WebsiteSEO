# Directive: HARO & Media Pitch Assistant

## Purpose
Automatically scan daily media query digests (HARO, Connectively, Featured.com, SourceBottle, etc.) sent to `ai.profit.lab2026@gmail.com`, filter for relevant expert opportunities in AI, Automation, and Web Design, and create ready-to-send draft responses directly in Gmail.

---

## Identity & Spokesperson Profile

- **Spokesperson Name**: Nahid
- **Title**: Founder & Lead AI Systems Architect
- **Brand**: **AI Profit Lab**
- **Parent Legal Entity**: **International Gulf Lotus SPC**
- **Website**: [https://aiprofitlab.io](https://aiprofitlab.io)
- **Core Expertise**:
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
1. **Expired Deadlines**: Any query whose submission deadline has already passed.
2. **Irrelevant Topics**: Healthcare/medical advice, personal finance/stocks, real estate, diet/fitness, beauty/fashion, or unrelated niches.
3. **Consumer Complaints / Paid Sponsorship Solicitations**: Direct advertorial pitches or pay-to-play link schemes.

---

## Winning Pitch Guidelines for Journalists

HARO journalists review dozens of pitches. Our drafted responses must adhere to strict PR best practices:

1. **Subject Line**:
   `HARO Pitch: [Query Title] — [Spokesperson Name], AI Profit Lab`
2. **Opening (1 sentence)**:
   Acknowledge the question and state our direct qualification in 1 sentence.
3. **Direct Soundbites / Insights (2-3 bullet points)**:
   - Provide concrete, original, and actionable answers to their specific questions.
   - Avoid fluff, generic AI jargon, or marketing buzzwords.
   - Give concise, ready-to-quote statements that a reporter can copy-paste directly into their article.
4. **Spokesperson Bio & Attribution**:
   - Name: Nahid
   - Role: Founder, AI Profit Lab ([https://aiprofitlab.io](https://aiprofitlab.io))
   - Headshot / LinkedIn available upon request.
5. **Safety & Inbox Rules**:
   - **ALWAYS SAVE AS DRAFT**: Never send emails automatically. Drafts must remain in the Gmail `Drafts` folder for human review and final approval.
   - **LABEL AS PROCESSED**: Once a digest email has been fully processed (its queries analyzed and qualifying drafts created), add the Gmail label `HARO Processed` to it (and mark it read). The label, not read status, is what prevents duplicate work, so a digest Nahid has already opened still gets pitched. A digest whose Gemini analysis fails stays unlabelled and is retried on the next run.

---

## Execution Tools & Architecture

- **Main Processor**: [`execution/haro_email_processor.py`](file:///Users/nahid/Desktop/Nahid/AI%20Profit%20Lab/Website/Website%20SEO/execution/haro_email_processor.py)
  - Connects to Gmail API via OAuth.
  - Queries digest emails without the `HARO Processed` label (`-label:haro-processed`, `newer_than:7d` across HARO, Connectively, Featured, SourceBottle, Qwoted), read or unread. Creates the label on first use.
  - Uses `gemini-flash-latest` (with fallback to `gemini-flash-lite-latest`) with schema-constrained extraction.
  - Avoids duplicate pitches by inspecting existing draft subjects before creation.
  - Formats drafts with journalist submission link/email and spokesperson credentials.
- **Interactive Authenticator**: [`tools/authenticate_gmail.py`](file:///Users/nahid/Desktop/Nahid/AI%20Profit%20Lab/Website/Website%20SEO/tools/authenticate_gmail.py)
  - Run interactively (`python3 tools/authenticate_gmail.py`) whenever OAuth credentials need initialization or renewal.
- **Mac LaunchAgent**: [`tools/setup_mac_schedule.sh`](file:///Users/nahid/Desktop/Nahid/AI%20Profit%20Lab/Website/Website%20SEO/tools/setup_mac_schedule.sh)
  - Schedules daily execution at 22:00 local time via `~/Library/LaunchAgents/com.aiprofitlab.haro.plist`.
  - Logs are persisted in `.tmp/haro_stdout.log` and `.tmp/haro_stderr.log`.

---

## Google Cloud OAuth Token Permanence (Self-Annealing Note)

- **Issue**: By default, Google Cloud OAuth projects set to "Testing" status issue refresh tokens that expire after **7 days**. When expired, background cron/launchd jobs fail with `invalid_grant: Token has been expired or revoked`.
- **Permanent Solution**:
  1. Open [Google Cloud Console](https://console.cloud.google.com/) for project `ai-profit-lab-assistant`.
  2. Navigate to **APIs & Services** > **OAuth consent screen**.
  3. Under **Publishing status**, click **PUBLISH APP** (transitioning from "Testing" to "In Production").
  4. In Production status, refresh tokens do not expire after 7 days and remain valid indefinitely until manually revoked.
- **GitHub Actions Secret**: If using GitHub Actions cloud fallback, update repository secret `GMAIL_TOKEN_JSON` with the contents of `token.json` after running `tools/authenticate_gmail.py`.

---

## Known Failure Modes (Self-Annealing Log)

- **Cloud fallback failed on every run, 2026-10-03 to 10-15** (13 runs, all at "Set up Python"). `cache: 'pip'` in `setup-python` needs a `requirements.txt` or `pyproject.toml`, and the repo has neither. Removed on 2026-10-16. Don't add it back without adding one of those files. The workflow now also stops with a named `::error::` if `GEMINI_API_KEY` or `GMAIL_TOKEN_JSON` is missing.
- **"Expired token" that wasn't (2026-10-13)**: launchd runs a job missed during sleep as soon as the Mac wakes, often before Wi-Fi is back. The DNS failure was reported as an expired token. The processor now retries a network error 6 times over 2.5 minutes, and says "No network" if it still can't connect. Re-authenticate only when the log shows `invalid_grant` / "expired or invalid".
- **Digests you opened yourself were never pitched (fixed 2026-10-16)**: the search used to find only `is:unread` mail, so a digest opened on the phone before the run was skipped for good. The 2026-10-16 Morning Edition was opened that way within an hour of arriving. The search now uses the `HARO Processed` label instead. On switching, the 21 digests that earlier runs had already processed (per `.tmp/haro_stdout.log`) were labelled by hand, so they weren't pitched again. Not every run writes to that log: drafts made 2026-10-10 06:08–06:21 UTC came from a manual run.
- **Every digest arrives twice**: HARO sends one copy to `nahid@aiprofitlab.io` and one to `ai.profit.lab2026@gmail.com` (two subscriptions). Each copy costs a Gemini call. The duplicate draft is skipped only when Gemini writes the same subject line for both copies.
- **The Mac clock is on America/Los_Angeles**, not Muscat. The LaunchAgent's 22:00 is 05:00 UTC (09:00 Muscat), which conveniently falls after all three of the previous day's HARO editions. The cloud run is scheduled for 18:00 UTC but GitHub starts it 3–5 hours late.

