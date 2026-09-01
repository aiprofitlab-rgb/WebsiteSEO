# ig-automation

A follower comments a keyword on a post or reel. They get a DM with the link, a
public "check your DMs" reply appears under their comment, and the lead lands in
a Google Sheet. ManyChat's core behaviour, self-hosted, with no monthly fee.

Runs on the Hostinger VPS. Everything else at AI Profit Lab is Cloud Run, so the
service is written to be portable — port from `PORT`, every path from an env var
— and could move to Cloud Run unchanged if the VPS becomes a chore.

```
comment webhook
  → verify X-Hub-Signature-256   (fails closed; an unsigned POST is refused)
  → ack 200                      (before any work — Meta's budget is ~2s)
  → our own comment?             drop, or the public reply answers itself forever
  → keyword match on THIS post?  a rule can be scoped to particular posts
  → claim comment_id             atomic; a Meta retry loses this race
  → private reply  POST /<IG_ID>/messages  { recipient: { comment_id }, ... }
  → public reply   POST /<COMMENT_ID>/replies
  → append lead row to the sheet
  → arm email capture if the rule asks for it

message webhook
  → skip echoes of our own DMs
  → is this person in 'awaiting_email'?
  → extract the email → backfill the CRM row → confirm
```

## Read first

**Meta's `comments` webhook needs Advanced Access, and Advanced Access needs
Business Verification plus App Review — around 20 days.** It does not work in
Development mode, not even on your own account. Everything else here is testable
today. See [META-SETUP.md](META-SETUP.md); that is the critical path, not this code.

Three Meta constraints shape the design and are worth knowing before you write
campaign copy:

- **One private reply per comment, ever.** So `dm.text` and `dm.link` are sent as
  a single message. There is no "hi!" followed by the link.
- **7 days** to privately reply to a comment. Old comments cannot be back-filled.
- **24 hours** to keep replying after they message you. Email capture lives inside
  that window.

## The admin panel

Everything a campaign needs changed — keywords, DM copy, which post a rule fires
on, the file it sends — is a browser form at `/admin/`, not an SSH session:

```
Rules     one card per rule: keywords, match mode, the posts it fires on,
          the DM, the link, the attached file, the public reply, email capture
Files     drag a PDF in; it gets an unguessable public link a rule can attach
Activity  the last comments the service acted on, and what happened to each
```

Three properties, each of which is the reason something in `lib/` looks the way
it does:

- **A save is live on the next comment.** No restart. `lib/rulesStore.js` writes
  atomically and the service reads the config through a getter.
- **A reply loop cannot be saved.** The panel runs the same validator the service
  boots with, and an `error` finding blocks the write. This is the guard for the
  failure that produced ninety identical replies on 2026-08-30.
- **The panel does not exist without a password.** `IG_ADMIN_PASSWORD_HASH` unset
  means the routes are never mounted.

A file is delivered as a link inside the DM rather than as an attachment, and
that is forced by the first constraint above: with one message to work with,
an attachment would arrive *instead of* the message.

```bash
node scripts/set-admin-password.js     # prints the line for .env
```

## Layout

| File | What it is |
|---|---|
| `server.js` | Wiring, `/health`, rate limit, boot checks |
| `webhook.js` | The GET handshake and the POST that acks before it works |
| `rules.json` | Keyword → action config. The SEED; the live copy is writable and lives outside the tree |
| `admin/` | The panel: the API in `router.js`, the page in `public/` |
| `lib/signature.js` | `X-Hub-Signature-256` and `appsecret_proof` |
| `lib/rules.js` | Matching, post targeting, Arabic normalisation, and the validator |
| `lib/rulesStore.js` | The writable rules file: validate, back up, write, hot-reload |
| `lib/auth.js` | The panel's password, session cookie and lockout |
| `lib/files.js` | Uploads, and the public URL a DM links to |
| `lib/ig.js` | Graph client |
| `lib/tokens.js` | The token file and its 60-day refresh |
| `lib/store.js` | SQLite: the dedupe set and conversation state |
| `lib/ledger.js` | The Google Sheet, and the stdout journal behind it |
| `lib/handler.js` | The flow above. Every dependency injected, so it is testable |
| `lib/mail.js` | The one alert worth sending: the token stopped refreshing |
| `scripts/graph-stub.js` | A fake graph.instagram.com for testing before approval |
| `scripts/replay.js` | Send a correctly signed webhook at a running instance |
| `scripts/refresh-token.js` | The daily cron |
| `scripts/verify-sheet.js` | Proves a 17-digit id survives the real spreadsheet |
| `scripts/set-admin-password.js` | Prints the `IG_ADMIN_PASSWORD_HASH` line for `.env` |
| `deploy/` | Caddyfile, systemd units, and [DEPLOY.md](deploy/DEPLOY.md) |

Requires **Node 22.5+** — state uses the built-in `node:sqlite`, deliberately
instead of `better-sqlite3`, so the VPS never needs a C++ toolchain.

## Local development

```bash
npm ci
cp .env.example .env          # invent a verify token and an app secret
npm test                      # 139 tests, no network needed

# Terminal 1 — a fake Instagram
node scripts/graph-stub.js

# Terminal 2 — the service pointed at it
IG_GRAPH_BASE=http://127.0.0.1:9099 npm run dev

# Terminal 3
node scripts/replay.js "storefront"
node scripts/replay.js --email "sure, it's me@example.com"
```

The panel needs a password and, over plain http, a cookie it is allowed to set:

```bash
IG_GRAPH_BASE=http://127.0.0.1:9099 \
IG_ADMIN_PASSWORD=local-dev-password IG_ADMIN_INSECURE_COOKIES=1 \
IG_PUBLIC_BASE=http://127.0.0.1:8090 npm run dev
# then http://127.0.0.1:8090/admin/
```

The stub serves three fake posts, so the post picker, the targeting and the
"not in recent list" tile are all exercisable before Meta approves anything.


The stub prints every call the service would have made to Meta, and enforces the
one-private-reply-per-comment rule, so the dedupe is proven rather than assumed.

## Editing keywords

`rules.json`. Ordered; **first match wins**, so put specific keywords above
generic ones. `npm test` fails if a rule is unreachable, and the service prints
`RULES PROBLEMS:` on boot.

```json
{
  "id": "storefront",
  "keywords": ["storefront", "store", "متجر"],
  "match": "word",
  "dm": { "text": "Here's the breakdown 👇", "link": "https://aiprofitlab.io/en/smart-storefront/" },
  "publicReply": "Sent! Check your DMs 📩",
  "askEmail": false
}
```

`match` is `word` (default, whole word), `contains` (substring), or `exact`
(the whole comment). Matching is case-insensitive, survives punctuation, emoji
and zero-width characters, ignores leading `@mentions`, and for Arabic handles
tatweel, diacritics, alef/yeh variants and a leading `ال` — so `سعر` matches
`السعر`. It will not match a keyword inside a longer word: `store` does not fire
on `restore`.

### The one rule about `publicReply`

**A public reply must never contain any rule's keyword.** We post it, Meta hands
it straight back as a new comment with a *new id*, it matches the rule again, and
the account answers itself until Instagram throttles it. The dedupe table cannot
help: every step of the loop is an id it has never seen.

`"Demos sent 📩"` under a rule keyed on `demos` is a loop. So is
`"Just sent you the pricing 📩"` under `pricing`. Both shipped, and both are why
`validate()` now refuses to stay quiet about it:

```
rules[2] (demo): publicReply "Demos sent 📩" contains the keyword "demos"
and would retrigger rule "demo" — that is a reply loop, change the wording
```

Three further guards stand behind that check, because config is only one of the
ways a loop starts:

| Guard | Catches |
| --- | --- |
| `from.id` vs `selfId`, `entry.id`, and `selfUsername` | our own comment, however Meta scoped the id |
| comment text equals any configured `publicReply` | our own words, whoever Meta says wrote them |
| `IG_MAX_REPLIES_PER_MEDIA_PER_HOUR` (12), `IG_MAX_REPLIES_PER_HOUR` (40) | anything else — bounds the damage and sends mail |

The breaker counts claims, not successes, and the window rolls forward on its
own, so a throttled post recovers an hour later without a restart.

## Verification

### Before Advanced Access — everything except the live trigger

1. `npm test` — 139 tests: signature (valid, tampered, wrong secret, missing,
   unconfigured), rules matching and post targeting, the self-comment guard,
   dedupe across a restart, token rotation, the ledger's ID-precision guard,
   and the panel end to end (sign-in, the loop the save gate refuses, an upload
   that reaches a DM, a stale tab that loses the race).
2. `node scripts/replay.js "storefront"` against a running instance. Expect a
   **200 in well under two seconds** and the DM, reply and ledger lines in the
   log. Replay the same payload three times and confirm exactly one DM.
3. `node --env-file=.env scripts/verify-sheet.js` — writes a 17-digit ID to the
   real sheet and reads it back. This is the only check that can catch
   `USER_ENTERED` rounding, which produces no error.
4. Point the Meta webhook at `https://hooks.aiprofitlab.io/ig` and confirm it
   verifies green in the App Dashboard. **This works before Advanced Access.**
5. `npm run refresh-token`, then hit `/health` on the still-running service and
   confirm it picked up the new token without a restart.

### After Advanced Access

6. Comment the keyword from a second Instagram account on a real post. Expect a
   DM, a public reply, and one row in the sheet.
7. Comment the same keyword again on the same post — expect no second DM.
8. Reply to the DM with an email; confirm it lands in the row's Email column.
9. A week later, `journalctl -u ig-token-refresh` should show a daily success.

## Operating it

`/health` reports the account, Graph version, days left on the token, whether the
verify token and app secret are set, the loaded rule ids, whether the ledger is
writing to a sheet or the logs, and the store's counters.

Every lead is printed to stdout as one line of JSON **before** the sheet is
touched, so a spreadsheet outage degrades to the journal instead of losing a lead:

```bash
sudo journalctl -u ig-automation | grep '"ledger":"lead"'
```

If the account ever starts repeating itself under a post, that is a reply loop.
Stop it first, diagnose second:

```bash
sudo systemctl stop ig-automation          # the replies stop immediately
sudo journalctl -u ig-automation | grep -E 'LOOP BREAKER|"webhook":"sent"' | tail -40
```

Then delete the runaway comments in the Instagram app, fix the `publicReply` the
breaker names, and start the service again. `IG_MAX_REPLIES_PER_MEDIA_PER_HOUR=0`
is the mute switch if you want the service up — answering Meta, keeping the
handshake and the callbacks alive — while it replies to nobody.

The failure that matters most is the quiet one: the token stops refreshing, every
Graph call starts returning 190, and the automation is off for eight weeks before
anyone notices. Set `RESEND_API_KEY` so that failure sends mail.

## Not in scope

Multi-tenant onboarding, OAuth for third-party accounts, a rules dashboard. The
CRM row carries an `Account` column so a second account could be added later
without a rewrite, but none of it is built.
