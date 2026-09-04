# Deploying checkout-api to the Hostinger VPS

The v4 checkout's payment service. Twin of `storefront-offer-api`, which moved
to the same box on 2026-09-02 — that service's `deploy/DEPLOY.md` is the worked
example and every trap it documents applies here too.

**Host:** `187.127.116.171` · **Port:** `8093` · **Public name:**
`checkout.aiprofitlab.io`

| Port | Service |
|---|---|
| 8090 | ig-automation |
| 8091 | aiden-backend |
| 8092 | storefront-offer-api |
| **8093** | **checkout-api ← this document** |

Traefik (from the n8n compose stack in `/docker/n8n`) owns :80 and :443. There
is no Caddy on this box — it is installed but `disabled` and `failed`, and
`/etc/caddy` is empty. Traefik cannot see a host service through its docker
provider, so host services are published with **file-provider YAML** in
`/docker/n8n/traefik-dynamic/`.

`172.16.1.1` is the `n8n_default` bridge gateway: how a container reaches a port
on the host. It is why Node must keep binding `0.0.0.0` and must **not** be
"hardened" onto `127.0.0.1` — that would make it unreachable from Traefik and
yield a 502. What keeps 8093 off the internet is ufw, scoped to the bridge
subnet.

---

## 1. DNS — do this first

An `A` record for `checkout.aiprofitlab.io` → `187.127.116.171`, in Hostinger
hPanel under Domains → DNS/Nameservers (DNS is Hostinger's own,
`ns1/ns2.dns-parking.com`).

```bash
dig +short checkout.aiprofitlab.io      # must return 187.127.116.171
```

Subdomain only. The apex `aiprofitlab.io` resolves to Hostinger's *web hosting*,
not to this box, and the GitHub Action that FTPs the site knows nothing about
any of this.

Traefik gets its certificate through the TLS-ALPN challenge on first request, so
**the name must resolve before the route file goes in**, or the first hit fails
and the failure is cached for a few minutes.

## 2. A user, and the code

Node 22 is already installed. There are no native modules.

```bash
sudo useradd --system --shell /usr/sbin/nologin --home /opt/checkout-api checkoutbot
sudo install -d -o checkoutbot -g checkoutbot /opt/checkout-api
```

From the Mac, in `Website/Website SEO/backend/checkout-api`:

```bash
rsync -av --delete \
  --exclude node_modules --exclude '.env' --exclude '.env.*' \
  --exclude sa.json --exclude '.DS_Store' \
  ./ root@187.127.116.171:/opt/checkout-api/

ssh root@187.127.116.171 \
  'cd /opt/checkout-api && sudo -u checkoutbot npm ci --omit=dev'
```

`--exclude '.env.*'` is not optional: `.env.live` holds the live Thawani secret
key and must never land inside a directory the deploy rsyncs over. Secrets live
in `/etc/checkout-api/.env`, which nothing rsyncs.

## 3. The environment file

```bash
sudo install -d -m 700 /etc/checkout-api
sudo install -m 600 /dev/null /etc/checkout-api/.env
sudo nano /etc/checkout-api/.env
```

Fill it from `deploy/.env.example` in this directory. The Thawani values come
from `backend/checkout-api/.env.live` on the Mac.

**systemd's EnvironmentFile is not a shell.** One value per line, no surrounding
quotes, no `export`.

Three of these decide whether the launch is real:

- `THAWANI_BASE=https://checkout.thawani.om` — this string is the live/test
  switch. `lib/thawani.js` derives `live` from it and `/health` reports it.
- `RESEND_API_KEY` — **without it nobody is told a payment landed and the buyer
  gets no receipt.** A working key is on this same box at
  `/etc/aiden-backend/.env`. Do not reuse the storefront's old Cloud Run key:
  it is invalid, Resend rejects it with HTTP 400.
- `CHECKOUT_SHEET_ID` — optional, and the service runs without it (orders go to
  the journal as one JSON line). Set it anyway, or Nahid cannot see orders where
  he actually works.

The Google service account key goes to `/etc/checkout-api/sa.json`, chmod 600.
It must be **`offer-api@aiprofitlab-offer.iam.gserviceaccount.com`** — the
identity already shared as a writer on the ledger sheets. A different account
authenticates perfectly and then fails every write with a 403, which reads as
"the sheet is broken" rather than "the key is wrong". Share the
`Checkout_Orders` spreadsheet with that address as an Editor before first boot.

## 4. systemd

```bash
sudo cp /opt/checkout-api/deploy/checkout-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now checkout-api
sudo systemctl status checkout-api
sudo journalctl -u checkout-api -n 50
```

A clean start logs the base URL and whether it is LIVE, then either
`ledger tab ready` or `ledger: no CHECKOUT_SHEET_ID, orders go to logs`.

`!! THAWANI keys are not set` means every `/session` call will fail — stop and
fix the env file.

## 5. ufw

```bash
sudo ufw allow from 172.16.1.0/24 to any port 8093 proto tcp
sudo ufw status numbered | grep 8093
```

Same shape as 8090/8091/8092. This is what keeps the port off the internet while
Node still binds `0.0.0.0` for Traefik.

## 6. Traefik

```bash
sudo cp /opt/checkout-api/deploy/traefik-checkout.yml \
        /docker/n8n/traefik-dynamic/checkout.yml
```

Traefik runs with `--providers.file.watch=true`, so **saving the file is the
deployment**. Nothing restarts, and n8n, ig-automation, aiden and the storefront
API are untouched. A malformed file is logged and ignored rather than breaking
live routes.

## 7. Verify before pointing the site at it

```bash
# On the box — /health is deliberately NOT publicly routed.
curl -s localhost:8093/health

# From anywhere.
curl -s https://checkout.aiprofitlab.io/session/nonexistent
```

`/health` must report `"env":"live"` and `"keys":true`. If it says `uat`, the
`THAWANI_BASE` line is wrong and no real money will move.

CORS, both directions:

```bash
curl -si -X POST https://checkout.aiprofitlab.io/session \
  -H 'Origin: https://aiprofitlab.io' -H 'Content-Type: application/json' \
  -d '{}' | grep -i access-control-allow-origin      # present

curl -si -X POST https://checkout.aiprofitlab.io/session \
  -H 'Origin: https://evil.example' -H 'Content-Type: application/json' \
  -d '{}' | grep -i access-control-allow-origin      # ABSENT
```

## 8. Point the site at it — the actual go-live

Only after step 7 passes. In `tools/v4/pay.py`:

```python
PAY_LIVE = True
PAY_API  = "https://checkout.aiprofitlab.io"
THAWANI_ENV = "live"
```

Then rebuild and deploy the site. That one edit switches the checkout button,
the note under it, the services page and the contact FAQ **together**, in both
languages, so none can be left saying the old thing.

`THAWANI_ENV` only drives the "TEST MODE" banner. Leaving it `"uat"` while
`PAY_LIVE` is True puts a banner saying no real money moves on a page that is
taking real money — check it.

## 9. Switching payments off in a hurry

In order of speed:

1. **Kill the route.** `sudo rm /docker/n8n/traefik-dynamic/checkout.yml` —
   takes effect immediately, no restart. The checkout page's own timeout then
   hands every buyer to the WhatsApp fallback and tells them nothing was
   charged, which is true.
2. **Stop the service.** `sudo systemctl stop checkout-api`. Same buyer-facing
   result.
3. **Rebuild with `PAY_LIVE = False`.** The honest, permanent one — the copy
   stops promising a card at all. Slowest, because it needs a site deploy.

Unlike the storefront, this service has **no `PAY_ENABLED` kill switch**. If
that matters, it is a small addition to `lib/thawani.js` mirroring
`storefront-offer-api`'s `config().enabled`.

## 10. Retiring nothing

The GCP project `aiprofitlab-offer` and the `offer-api@` service account **must
stay** — that account is the writer on the ledger sheets. Deleting the project
kills both ledgers. "Off Google Cloud" means nothing *runs* there; the ledgers
are still Google Sheets.
