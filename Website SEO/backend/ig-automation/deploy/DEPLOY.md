# Deploying ig-automation to the Hostinger VPS

Everything else AI Profit Lab runs is Cloud Run. This one is on the VPS, which
means it is a real server you now own: OS patches, a TLS certificate, a process
supervisor, a firewall. The units in this folder exist so none of that has to be
remembered a second time.

The service is deliberately free of VPS-specific assumptions — the port comes
from `PORT`, every path comes from an env var — so if the box ever becomes a
chore, the same code deploys to Cloud Run unchanged.

> **Node 22 or newer is required.** State is stored with `node:sqlite`, built
> into Node since 22.5. The usual choice, `better-sqlite3`, is a native module
> and would drag a C++ toolchain onto the VPS just to install the service.

---

## 1. DNS

An `A` record for `hooks.aiprofitlab.io` pointing at the VPS IP.

Keep it off the apex. `aiprofitlab.io` serves the static site from Hostinger's
web root, and the GitHub Action that FTPs the site has no idea this exists.

Confirm it resolves before touching Caddy — Caddy cannot get a certificate for a
name that does not point at it yet:

```bash
dig +short hooks.aiprofitlab.io
```

## 2. Node, Caddy, a user

```bash
# Node 22 LTS
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs
node -v                       # must be >= 22.5.0

# Caddy
sudo apt-get install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt-get update && sudo apt-get install -y caddy

# A user that owns nothing else and cannot log in
sudo useradd --system --shell /usr/sbin/nologin --home /opt/ig-automation igbot
```

## 3. The code

```bash
sudo mkdir -p /opt/ig-automation
sudo chown igbot:igbot /opt/ig-automation

# From your Mac, from the repo root:
rsync -av --exclude node_modules --exclude .env --exclude '*.sqlite*' --exclude token.json \
  "backend/ig-automation/" root@YOUR_VPS_IP:/opt/ig-automation/

# On the VPS:
cd /opt/ig-automation
sudo -u igbot npm ci --omit=dev
```

`npm ci --omit=dev` and not `npm install`: the lockfile is what was tested.

## 4. The directories that are not the repo

Two things get written at runtime, and neither may live in the deployed tree —
a redeploy would wipe the token and the dedupe table with it.

```bash
# Rotating token, SQLite state, the rules the admin panel writes, and uploads.
sudo mkdir -p /var/lib/ig-automation/uploads
sudo chown -R igbot:igbot /var/lib/ig-automation
sudo chmod 750 /var/lib/ig-automation

# Secrets. Read by systemd as root, before dropping to igbot.
sudo mkdir -p /etc/ig-automation
sudo chmod 700 /etc/ig-automation
```

## 5. Secrets

```bash
sudo cp /opt/ig-automation/.env.example /etc/ig-automation/.env
sudo nano /etc/ig-automation/.env
sudo chmod 600 /etc/ig-automation/.env
```

Set at minimum:

```ini
IG_VERIFY_TOKEN=<openssl rand -hex 32>
META_APP_SECRET=<App Dashboard -> Settings -> Basic -> App Secret>
IG_USER_ID=<your Instagram professional account id>
IG_TOKEN_FILE=/var/lib/ig-automation/token.json
IG_DB_FILE=/var/lib/ig-automation/state.sqlite

# NOT /opt. The admin panel writes this file, and systemd's ProtectSystem=strict
# only allows writes under /var/lib/ig-automation — a rules file in the deployed
# tree could not be saved to, and the next rsync would revert it anyway. The
# repo's rules.json is a seed, copied here once if nothing exists.
IG_RULES_FILE=/var/lib/ig-automation/rules.json
IG_UPLOAD_DIR=/var/lib/ig-automation/uploads

# The origin written into every DM that carries a file. Must be the public name.
IG_PUBLIC_BASE=https://hooks.aiprofitlab.io

# The admin panel. Omit it and the panel is not mounted at all.
#   node scripts/set-admin-password.js
IG_ADMIN_PASSWORD_HASH=<paste the scrypt$... line>

PORT=8090
```

**Upgrading an install that predates the panel.** The rules file moves; nothing
else does:

```bash
sudo -u igbot cp /opt/ig-automation/rules.json /var/lib/ig-automation/rules.json
sudo nano /etc/ig-automation/.env      # point IG_RULES_FILE at the new path
sudo systemctl restart ig-automation
curl -s localhost:8090/health | python3 -c 'import sys,json;print(json.load(sys.stdin)["rules"])'
```

`IG_VERIFY_TOKEN` is a nonce you invent and paste into the Meta dashboard. It is
not a credential. `META_APP_SECRET` is a credential, and it is the only thing
standing between a public URL and a stranger posting forged comment events.

Seed the access token once, then let the timer own it:

```bash
sudo -u igbot tee /var/lib/ig-automation/token.json >/dev/null <<'JSON'
{ "access_token": "PASTE_LONG_LIVED_TOKEN", "expires_in": 5184000, "obtained_at": "2026-08-27T00:00:00.000Z" }
JSON
sudo chmod 600 /var/lib/ig-automation/token.json
```

For the CRM sheet, put the service-account key at `/etc/ig-automation/sa.json`
(`chmod 600`, owned by `igbot`), point `GOOGLE_APPLICATION_CREDENTIALS` at it,
and share the spreadsheet with that service account's email as an **Editor**.
Without this the automation still works and every lead lands in the journal.

## 6. Services

```bash
sudo cp /opt/ig-automation/deploy/ig-automation.service /etc/systemd/system/
sudo cp /opt/ig-automation/deploy/ig-token-refresh.service /etc/systemd/system/
sudo cp /opt/ig-automation/deploy/ig-token-refresh.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ig-automation
sudo systemctl enable --now ig-token-refresh.timer

sudo journalctl -u ig-automation -n 50 --no-pager
curl -s localhost:8090/health | python3 -m json.tool
```

`/health` is the fastest way to catch a configuration mistake — it reports
whether the verify token and app secret are set, how many days the token has
left, and whether the ledger is writing to a sheet or to the logs.

## 6b. The admin panel

Keywords, DM copy, which posts a rule fires on, and file uploads — from a
browser, without SSH.

```bash
cd /opt/ig-automation
sudo -u igbot node scripts/set-admin-password.js     # prints the env line
sudo nano /etc/ig-automation/.env                    # paste IG_ADMIN_PASSWORD_HASH
sudo systemctl restart ig-automation
```

Then `https://hooks.aiprofitlab.io/admin/`.

Three things worth knowing before you use it:

- **No password, no panel.** The routes are not mounted when
  `IG_ADMIN_PASSWORD_HASH` is unset, so a half-finished install is a 404 rather
  than an open door. `/health` reports `admin.configured`.
- **Saves are live immediately.** No restart. The running service re-reads the
  rules file when its mtime changes, so an edit made over SSH takes effect the
  same way.
- **It refuses to save a reply loop.** A public reply containing one of your own
  keywords is what made the account answer itself ninety times on 2026-08-30.
  The panel runs the same validator the service boots with and blocks the save,
  naming the rule and the keyword.

Uploaded files are served from `https://hooks.aiprofitlab.io/f/<id>/<name>` —
public, unguessable, and linked from inside the DM. That is not a shortcut:
Meta allows exactly one private reply per comment, so an attachment would have
to be sent *instead of* your message.

## 7. TLS

```bash
sudo cp /opt/ig-automation/deploy/Caddyfile /etc/caddy/Caddyfile
sudo systemctl reload caddy
curl -sI https://hooks.aiprofitlab.io/ig | head -1
```

Meta requires a valid public certificate on the callback URL and rejects a
self-signed one, so this must be working before the webhook is registered.

## 8. Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

Port 8090 is deliberately absent. Node listens on localhost and only Caddy
reaches it; opening 8090 would expose an endpoint with no TLS in front of it.

## 9. Register the webhook

In the Meta App Dashboard → your app → Instagram → Webhooks:

- **Callback URL:** `https://hooks.aiprofitlab.io/ig`
- **Verify token:** the exact `IG_VERIFY_TOKEN` value
- Subscribe to **`comments`** and **`messages`**

The handshake works before Advanced Access is granted, so verify it now. Watch
it land:

```bash
sudo journalctl -u ig-automation -f     # expect: WEBHOOK_VERIFIED
```

Meta will not *deliver* `comments` events until the app has Advanced Access and
is set to Live. See `../META-SETUP.md`.

---

## Redeploying

```bash
rsync -av --exclude node_modules --exclude .env --exclude '*.sqlite*' --exclude token.json \
  "backend/ig-automation/" root@YOUR_VPS_IP:/opt/ig-automation/
ssh root@YOUR_VPS_IP 'cd /opt/ig-automation && sudo -u igbot npm ci --omit=dev && systemctl restart ig-automation'
```

Those excludes are not optional. `--exclude token.json` and `--exclude '*.sqlite*'`
are what stop a redeploy from overwriting the live token with a stale one, or
wiping the dedupe table — which would let Meta's retries re-send DMs for comments
that were already answered.

Changing keyword rules is not a redeploy, and no longer needs SSH at all —
use `https://hooks.aiprofitlab.io/admin/`. Over SSH it is still just the file,
and still needs no restart:

```bash
sudo -u igbot nano /var/lib/ig-automation/rules.json
```

Note the path: `/var/lib`, not `/opt`. The copy in the deployed tree is only the
seed used on a fresh box; editing it changes nothing on a running install.

## When something is wrong

| Symptom | Cause | Check |
|---|---|---|
| Dashboard will not verify the callback | verify token mismatch, or TLS not up | `journalctl -u ig-automation -f`, `curl -sI https://hooks.aiprofitlab.io/ig` |
| Every POST logs `SIGNATURE REJECTED` | `META_APP_SECRET` wrong or unset | `/health` → `webhook.appSecret` |
| Webhook verifies, no events ever arrive | app is not Live, or lacks Advanced Access | App Dashboard → App Review |
| DMs stopped, comments still arriving | token expired | `/health` → `token.daysLeft`, `journalctl -u ig-token-refresh` |
| A comment got two DMs | dedupe table was wiped by a redeploy | confirm `IG_DB_FILE` is under `/var/lib`, not `/opt` |
| Leads missing from the sheet | service account lacks access | `grep '"ledger":"lead"' <(journalctl -u ig-automation)` — they are still in the journal |
| Service answers its own comments | own IG id unknown | `/health` → `account.id`; set `IG_USER_ID` |
| `/admin/` is a 404 | no password configured | `/health` → `admin.configured`; run `scripts/set-admin-password.js` |
| Panel loads, saving 500s | `IG_RULES_FILE` is under `/opt` | systemd's `ProtectSystem=strict` blocks it; move it to `/var/lib/ig-automation/rules.json` |
| A rule's file link 404s in the DM | uploads dir was wiped by a redeploy | confirm `IG_UPLOAD_DIR` is under `/var/lib`, re-upload, re-attach |
| Panel shows no posts to pick | the Graph call failed | ids already in rules still work; check `/health` → `token.daysLeft` |
| Signed out constantly | the password hash changed | the cookie key is derived from it; sign in again |

Every lead is printed to the journal as one line of JSON before the sheet is
touched, so nothing is ever lost to a spreadsheet problem:

```bash
sudo journalctl -u ig-automation | grep '"ledger":"lead"' | tail -20
```
