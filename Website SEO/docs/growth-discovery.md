# Growth discovery questionnaire

A client intake for growth work: about 15 minutes, 7 parts, 24 short screens, in English,
Persian and Arabic. As the client answers, a **Growth X-ray** builds beside the questions. It
follows the customer's path in four steps: **Seen** (new people see you), **Trusted** (they
check you before they message), **Booked** (they message and book) and **Back again** (they
come back and send friends).

After Send, the client sees, in this order:

1. how many gaps their answers revealed;
2. what **one more booking a week** is worth to them a month and a year, from their own
   typical booking (typical booking × 52 ÷ 12);
3. what the unanswered messages cost (low end: "a few" counts as 2 a week, "quite a lot" as 6,
   and only 1 in 4 would have booked), with their own "if nothing changes" and "this would
   mean it's working" answers quoted back;
4. what we already run for them (with `built=`);
5. one line on why content alone isn't enough ("more reels bring more messages…");
6. the three plans, **Digital Partner first**, each smaller plan showing how many gaps it
   leaves open and in which steps of the path;
7. the gaps step by step, each tagged with the smallest plan that closes it;
8. the first month with Digital Partner (from the proposal's timeline).

Beside it (on phones, straight after the plans), the client picks the plan to talk about.
Each button opens WhatsApp with that plan already named, and the choice reaches the sheet.
No prices are shown.

Built 2026-11-01, first for Mazloumi Rent Car. Reworked 2026-11-02 after an audit against
the ACQ Offers, Money Models and Leads material, so that the form sells the partnership, not
content alone (see "Why it is built this way").

## URLs

| Language | URL | File |
|---|---|---|
| English | https://aiprofitlab.io/en/growth-discovery/ | `public_html/en/growth-discovery.html` |
| Persian | https://aiprofitlab.io/fa/growth-discovery/ | `public_html/fa/growth-discovery/index.html` |
| Arabic | https://aiprofitlab.io/ar/growth-discovery/ | `public_html/ar/growth-discovery/index.html` |

All three are `noindex`, in no sitemap and in no nav. Clarity is off. The client can switch
language on the page.

## Personal links

Add these to any of the three URLs. `b`, `ig` and `n` fill an empty draft only, so a client
who has started is never overwritten.

| Parameter | Does | Example |
|---|---|---|
| `b` | Business name ("Prepared for …", the X-ray title, the phone in the hero) | `b=Mazloumi%20Rent%20Car` |
| `ig` | Instagram handles, comma separated, pre-added as accounts | `ig=oman_rentcar,mazloumi.rentcar` |
| `n` | Contact name | `n=…` |
| `plans=off` | Hides plan names everywhere, for a client on a different offer | `plans=off` |
| `built` | "Already working for you": what we already run for this client. Any of `platform`, `website`, `leads` (WhatsApp enquiry counter), `alerts` (phone alerts), `chat` (AI chat on the website). List only what is really live. | `built=platform,website,leads` |
| `until` | The real expiry of the proposal they were sent. Hidden once the date has passed. | `until=2026-11-07` |
| `pp` | Digital Partner's monthly price in OMR. Never shown; only used for "it pays for itself with N extra bookings a month". Take it from the proposal they hold. | `pp=220` |

`built`, `until` and `pp` are for a client who already has our proposal.

Mazloumi's link (Persian):

    https://aiprofitlab.io/fa/growth-discovery/?b=Mazloumi%20Rent%20Car&ig=oman_rentcar,mazloumi.rentcar&built=platform,website,leads&until=2026-11-07&pp=220

Add `alerts` once his iPhone receives the WhatsApp push alerts, and `chat` once the website
chat has its AI key on the VPS. `until=2026-11-07` and `pp=220` are from the 24 Oct proposal.

## Editing

Edit only `tools/growth-discovery/growth-discovery.src.html`, then run:

    python3 tools/growth-discovery/build_growth_discovery.py

- **Questions:** `STEPS`. The English label is also the sheet column, so changing it starts a
  new column. The step with `after:1` (`plan`, "Your first month") is not part of the
  diagnosis: it is offered on the results page, optional, and sent separately.
- **Screens:** `SCREEN_DEF`. Every key appears exactly once; the page logs an error if not.
- **Gaps:** `GAPS`. Each has `layer` (seen, trust, book, back), `tier` (the smallest plan that
  closes it), `w` (weight), `ask` (was the question answered), `on` (do the answers show the
  gap), the text, and the fix. Weight: 3 = the customer was ready to book or had already
  bought (5 AM message, missed messages, "price?" comments, no return visits, no referrals);
  2 = they were deciding; 1 = reach and polish.
- **Plans:** `PLANS` and `coverage()`. The best fit is the smallest plan that leaves no
  weight-3 gap open and closes at least 80% of the weight. So a plan that leaves ready
  customers leaking is never recommended, and a business whose only gaps are content still
  gets Social.
- **Money:** `gainOf`, `leakOf`, `paybackOf` and `MISSED`. They read only the client's own
  answers (Persian and Arabic digits too).

Checked on 2026-11-02 with sample answers: every gap present → Digital Partner; Mazloumi-like
answers → Digital Partner; only content weak → Social; content and search weak, inbox and
after-sale fine → Growth.

The Persian was written for this form; read it before sending. The Arabic is new and not yet
native-reviewed, so the page says so, as brand discovery does.

## Why it is built this way

From the 2026-11-02 audit (ACQ Offers, Money Models, Leads):

- **It's a "reveal a problem" lead magnet.** The X-ray must reveal the *next* problem, the
  one Digital Partner solves, so it shows the whole path and says plainly that more content
  sends more people into a leaking inbox.
- **The pain is priced in their numbers.** One more booking a week, the cost of unanswered
  messages, and their own words about doing nothing. Estimates are labelled and use the low end.
- **Anchor and decoy.** Digital Partner is shown first and complete; the smaller plans show
  what they leave open.
- **The choice comes after the X-ray.** Asking "which do you need?" before it made people
  commit to the smallest answer. Now the plan choice is the call to action.
- **No content-agency intake before the sale.** Filming, tone, stories and dates moved to the
  optional first-month step after the X-ray, like the Storefront onboarding brief.
- **Gaps only a partner closes:** referrals, other businesses that send customers, a reason to
  book now (a named offer with an end date), and planned slow months. These are in the Digital
  Partner tier, so the Partner plan must really include them: a referral voucher system,
  partner links, a monthly named offer and slow-month campaigns.

## Backend

The page posts `text/plain` JSON to a Google Apps Script web app, as brand discovery does.
Set up on 2026-11-02 with clasp, in ai.profit.lab2026@gmail.com's Drive:

| | |
|---|---|
| Sheet | "Growth discovery briefs", id `1C2kyj45drK7DQVM2Oel5L9t8H34jptGMrOEbU4L4wcY` |
| Script | id `14tEldSGkuPG3zAEMyjyof178CtS_VABhwM4DMhflFAri9Uv-oj9ZkGXq`, bound to the sheet; source of record `tools/growth-discovery/growth-discovery-apps-script.gs` |
| Deployment | `AKfycbzn4LyTKthGixrAi1G-2PCrtvf17PBo1jtTtIMiM7bKoJ9r45xzJa3c2S8CBckyu3_aKQ` (= `BRIEF_ENDPOINT` in the page), Execute as Me, access Anyone |

**The owner must authorise it once:** open the sheet, Extensions > Apps Script, pick `setup`
in the function list, Run, and allow the permissions (sheet, Drive, mail). Until then the
`/exec` URL answers 403 and Send lands on the X-ray with the download, copy, email and
WhatsApp options, and never claims it sent. Optional after that: run `selfTest`; it writes a
"TEST - delete me" row and a Drive folder.

Script edits: put the `.gs` (as `Code.js`) in a folder with a `.clasp.json` holding the script
id, plus an `appsscript.json` with `"timeZone": "Asia/Muscat"` and
`"webapp": {"executeAs": "USER_DEPLOYING", "access": "ANYONE_ANONYMOUS"}`, then
`npx @google/clasp@2.4.2 push -f`, `version`, and `deploy -i <deployment id> -V <n>`.
Redeploying the same id keeps the URL; a new deployment would change it.

Each brief arrives as:
- one Sheet row, with fixed columns (contact, accounts, gaps, best fit, chose, one more booking
  a week, voice notes, first-month notes, session) and then one column per question;
- a Drive folder of voice answers, with each `[voice:FILE]` in the answers replaced by its link;
- an email with the brief attached as `growth-discovery-<business>.md`.

After the brief, the results page can send two more things, both written onto the same row
(found by the session id):
- **the plan they tapped** ("Chose"), with an email to you: "<business> wants to talk about
  Digital Partner". WhatsApp opens on their phone at the same moment, with a message to you;
- **the first-month notes**, as their own columns at the end of the row, with an email and a
  `first-month-<business>.md` attachment.

A "Not sent yet" tab and email cover clients who reach the review screen and never press Send.
A sent brief stays on the client's device, so reopening the link shows their X-ray again
("Start a new form" clears it).

## Turning a brief into a plan

Download the voice notes from the Drive folder and transcribe them, for example with
Recordly's `whisper-cli`. Then give Claude the `.md` brief, the first-month notes if they
sent them, and the transcripts, with this prompt:

> Here is a growth discovery brief for <client>. Using it, write: (1) one content strategy per
> Instagram account: audience, language, three to five content pillars built from "What do
> customers ask you most", "What worries them" and "Your hidden advantage", and the tone from
> the sliders; (2) a 30-day calendar per account with N reels, N carousels and daily stories,
> using their dates and offers; (3) ten reel hooks and scripts, using the virality skill, from
> their questions and stories; (4) the first fixes for each gap in the X-ray, in order, starting
> with the Booked and Back again steps. Respect their red lines and the "show prices" answer.
> Don't invent facts about the business; list what's missing as questions for the kickoff call.
