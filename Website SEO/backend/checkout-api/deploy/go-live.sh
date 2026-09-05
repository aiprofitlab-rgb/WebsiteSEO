#!/usr/bin/env bash
#
# go-live.sh — deploy checkout-api to the VPS and arm both payment paths.
#
# Run it from your Mac. It does everything except the two moments that actually
# start taking money; those stay yours, and they are one command each at the end.
#
#   ./go-live.sh --check     look at everything, change NOTHING. Run this first.
#   ./go-live.sh             do the deployment.
#
# THE DESIGN, in one line: everything is installed and verified with cards
# switched OFF (PAY_ENABLED=0), so "go live" is later, separate, and reversible
# by changing a single character back.
#
# Every file it touches on the server is copied to <file>.bak-<timestamp> first.
# It stops at the first sign of trouble rather than pressing on.

set -euo pipefail

# ---------------------------------------------------------------- constants --
HOST="root@187.127.116.171"
SSH_OPTS=(-o ConnectTimeout=15 -o StrictHostKeyChecking=accept-new)

DOMAIN="checkout.aiprofitlab.io"
BOX_IP="187.127.116.171"
PORT=8093

SVC="checkout-api"
SVC_USER="checkoutbot"
APP_DIR="/opt/checkout-api"
ETC_DIR="/etc/checkout-api"
UNIT="/etc/systemd/system/checkout-api.service"
TRAEFIK="/docker/n8n/traefik-dynamic/checkout.yml"

STOREFRONT_ETC="/etc/storefront-offer-api/.env"
STOREFRONT_SVC="storefront-offer-api"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$(cd "$HERE/.." && pwd)"
ENV_LIVE="$SRC/.env.live"

STAMP="$(date +%Y%m%d-%H%M%S)"
CHECK_ONLY=0
REDEPLOY=0
[[ "${1:-}" == "--check" ]] && CHECK_ONLY=1

# ------------------------------------------------------------------ output --
if [[ -t 1 ]]; then
  R=$'\033[31m'; G=$'\033[32m'; Y=$'\033[33m'; B=$'\033[1m'; D=$'\033[2m'; X=$'\033[0m'
else
  R=""; G=""; Y=""; B=""; D=""; X=""
fi

step()  { printf '\n%s>> %s%s\n' "${B}" "$1" "${X}"; }
ok()    { printf '   %s✓%s %s\n' "${G}" "${X}" "$1"; }
warn()  { printf '   %s!%s %s\n' "${Y}" "${X}" "$1"; }
info()  { printf '   %s%s%s\n' "${D}" "$1" "${X}"; }

die() {
  printf '\n%sSTOPPED.%s %s\n' "${R}" "${X}" "$1" >&2
  [[ $# -gt 1 ]] && printf '\n%s\n' "$2" >&2
  printf '\n%sNothing further was changed. Paste this output back to Claude.%s\n' "${D}" "${X}" >&2
  exit 1
}

sshx() { ssh "${SSH_OPTS[@]}" "$HOST" "$@"; }

# Back up a remote file before touching it. Never overwrites an existing backup.
backup_remote() {
  local f="$1"
  sshx "test -f '$f' && cp -n '$f' '$f.bak-$STAMP' || true"
}

# ============================================================================
# PHASE A — look at everything, change nothing
# ============================================================================

printf '%s\n' "${B}"
cat <<'BANNER'
  ┌──────────────────────────────────────────────────────────┐
  │  AI Profit Lab — payment go-live                         │
  │  checkout-api  ->  the Hostinger VPS, port 8093          │
  └──────────────────────────────────────────────────────────┘
BANNER
printf '%s' "${X}"
[[ $CHECK_ONLY -eq 1 ]] && printf '  %sCHECK MODE — nothing will be changed.%s\n' "${Y}" "${X}"

step "1. Can I reach the server?"
sshx "echo ok" >/dev/null 2>&1 \
  || die "Cannot SSH to $HOST." \
"Check you're online, and that this Mac's SSH key is on the box. Test by hand with:
  ssh $HOST"
ok "SSH works"

step "2. Is the DNS name pointing at the box?"
RESOLVED="$(dig +short "$DOMAIN" 2>/dev/null | tail -1 || true)"
if [[ "$RESOLVED" != "$BOX_IP" ]]; then
  die "$DOMAIN does not resolve to $BOX_IP (got: '${RESOLVED:-nothing}')." \
"YOU NEED TO DO THIS BIT IN HOSTINGER — it can't be done from here:

  1. Log in to Hostinger hPanel
  2. Domains -> DNS / Nameservers  (for aiprofitlab.io)
  3. Add an A record:
         Type: A     Name: checkout     Points to: $BOX_IP     TTL: leave default
  4. Wait ~5 minutes, then run this script again.

The certificate is issued on the first request, so the name has to work first."
fi
ok "$DOMAIN -> $BOX_IP"

step "3. Is port $PORT free, and are the neighbours healthy?"
if sshx "ss -ltn | grep -q ':$PORT '"; then
  # Something is listening, which is only a problem if it is not US. After a
  # first successful install our own service holds this port BY DESIGN, and
  # dying here would make the script single-use — every later change would have
  # to be done by hand, which is the thing it exists to avoid.
  if sshx "systemctl is-active --quiet $SVC"; then
    REDEPLOY=1
    ok "port $PORT is $SVC's own — this is a RE-DEPLOY, not a first install"
  else
    die "Something ELSE is already listening on port $PORT." \
"$SVC is not running, so this is not ours.
Find out what with:  ssh $HOST 'ss -ltnp | grep :$PORT'"
  fi
else
  ok "port $PORT is free"
fi

for s in ig-automation aiden-backend "$STOREFRONT_SVC"; do
  if sshx "systemctl is-active --quiet $s"; then
    ok "$s is running (and will not be touched)"
  else
    warn "$s is NOT running — not caused by this script, but worth knowing"
  fi
done

step "4. Is Node installed?"
NODEV="$(sshx "node -v" 2>/dev/null || true)"
[[ -n "$NODEV" ]] || die "node is not on the server's PATH."
ok "node $NODEV"

step "5. Do I have the live Thawani keys locally?"
[[ -f "$ENV_LIVE" ]] || die "Cannot find $ENV_LIVE on this Mac."

get_env() { grep -E "^$1=" "$ENV_LIVE" | head -1 | cut -d= -f2- | tr -d '"'"'"' \r'; }
T_SECRET="$(get_env THAWANI_SECRET_KEY)"
T_PUBLIC="$(get_env THAWANI_PUBLISHABLE_KEY)"
T_BASE="$(get_env THAWANI_BASE)"

[[ -n "$T_SECRET" && -n "$T_PUBLIC" ]] || die "THAWANI keys are missing from $ENV_LIVE."
[[ "$T_SECRET" != "$T_PUBLIC" ]] || die "The two Thawani keys are identical — one of them is wrong."
[[ "$T_BASE" == "https://checkout.thawani.om" ]] \
  || die "THAWANI_BASE in .env.live is '$T_BASE', not the live gateway." \
"It must be https://checkout.thawani.om for real payments."
ok "two distinct keys found, pointed at the LIVE gateway"

step "6. Do those keys actually work?"
# Read-only: ask about a session that cannot exist. Valid key -> 400 "not
# found". Invalid key -> 401. No session is created and no money moves.
CODE="$(curl -s -o /dev/null -w '%{http_code}' -m 20 \
  -H "Thawani-Api-Key: $T_SECRET" \
  "https://checkout.thawani.om/api/v1/checkout/session/probe_does_not_exist" || true)"
case "$CODE" in
  400) ok "Thawani accepted the secret key (merchant account is live)" ;;
  401) die "Thawani rejected the secret key (401 Unauthorized)." \
"The key in .env.live is wrong, or has been rotated in the Thawani portal." ;;
  *)   die "Unexpected reply from Thawani (HTTP $CODE). Try again in a minute." ;;
esac

if [[ $CHECK_ONLY -eq 1 ]]; then
  printf '\n%sAll checks passed.%s Nothing was changed.\n' "${G}" "${X}"
  printf 'When you are ready, run it for real:  %s./go-live.sh%s\n\n' "${B}" "${X}"
  exit 0
fi

# ============================================================================
# PHASE B — the Resend key, for BOTH services
# ============================================================================

step "7. Your Resend API key"
cat <<'EOS'
   This is what sends the buyer their receipt and tells you a payment landed.
   Without it, someone can pay and nobody is told.

   Paste the key you created (it starts with re_). It will not be shown on
   screen, is not saved on this Mac, and never reaches your shell history.
EOS
printf '\n   Resend key: '
read -rs RESEND_KEY
printf '\n'

[[ -n "$RESEND_KEY" ]] || die "No key entered."
[[ "$RESEND_KEY" == re_* ]] || die "That does not look like a Resend key (they start with 're_')."

info "testing it against Resend..."
# Probe POST /emails with a deliberately incomplete body. It SENDS NOTHING, and
# it separates the two failures cleanly:
#
#   422 "Missing `to` field"  -> authenticated. The key works for sending.
#   401 / 403                 -> the key is dead or revoked.
#
# Do NOT test with GET /domains. That needs a FULL-ACCESS key, so a correct
# key made with 'Sending access' — which is what we tell you to create three
# lines above, and all this service needs — comes back 401 and gets rejected
# as dead. Verified 2026-09-05 against a real sending-only key: /domains says
# 401 while /emails says 422.
RCODE="$(curl -s -o /dev/null -w '%{http_code}' -m 20 \
  -X POST -H "Authorization: Bearer $RESEND_KEY" -H 'Content-Type: application/json' \
  -d '{}' https://api.resend.com/emails || true)"
[[ "$RCODE" == "422" ]] \
  || die "Resend rejected that key (HTTP $RCODE)." \
"This is exactly the failure that has bitten this setup before, so it is worth
getting right. Make a fresh key at resend.com -> API Keys -> Create API Key,
with 'Sending access', and run this again."
ok "Resend accepted the key (sending access confirmed)"

step "8. Arming the storefront service — email ON, cards still OFF"
backup_remote "$STOREFRONT_ETC"

# All four values in ONE write, and PAY_ENABLED=0 goes in with them. The order
# matters: this file's two Thawani keys ARE the campaign's card switch, so
# writing them without disarming first would start taking cards mid-script.
# Values arrive on stdin so no secret is ever an argument in a process list.
printf '%s\n%s\n%s\n' "$RESEND_KEY" "$T_SECRET" "$T_PUBLIC" | sshx "
  set -e
  read -r resend; read -r tsecret; read -r tpublic
  f='$STOREFRONT_ETC'

  setkey() {
    if grep -q \"^\$1=\" \"\$f\"; then
      awk -v k=\"\$1\" -v v=\"\$2\" 'BEGIN{FS=OFS=\"=\"} \$1==k{print k \"=\" v; next} {print}' \"\$f\" > \"\$f.tmp\"
      mv \"\$f.tmp\" \"\$f\"
    else
      printf '%s=%s\n' \"\$1\" \"\$2\" >> \"\$f\"
    fi
  }

  setkey PAY_ENABLED 0
  setkey RESEND_API_KEY \"\$resend\"
  setkey THAWANI_SECRET_KEY \"\$tsecret\"
  setkey THAWANI_PUBLISHABLE_KEY \"\$tpublic\"
  setkey THAWANI_BASE https://checkout.thawani.om
  chmod 600 \"\$f\"
"
sshx "systemctl restart $STOREFRONT_SVC"
sleep 3
sshx "systemctl is-active --quiet $STOREFRONT_SVC" \
  || die "$STOREFRONT_SVC did not come back up." \
"Put it back exactly as it was and restart:
  ssh $HOST 'cp $STOREFRONT_ETC.bak-$STAMP $STOREFRONT_ETC && systemctl restart $STOREFRONT_SVC'"

# Prove the campaign is still on bank transfer. If this says true, the kill
# switch did not take and we must not leave the script thinking it is armed.
PAYCARD="$(curl -s -m 15 https://offer.aiprofitlab.io/status | grep -o '"card":[a-z]*' || true)"
[[ "$PAYCARD" == '"card":false' ]] \
  || die "The campaign page is reporting card payments as ON ($PAYCARD)." \
"That is not what this script intended. Disarm it now:
  ssh $HOST 'cp $STOREFRONT_ETC.bak-$STAMP $STOREFRONT_ETC && systemctl restart $STOREFRONT_SVC'"
ok "email on, keys loaded, cards still OFF (backup: $STOREFRONT_ETC.bak-$STAMP)"

# ============================================================================
# PHASE C — deploy checkout-api, with cards OFF
# ============================================================================

step "9. Creating the service account and directory"
sshx "
  set -e
  id -u $SVC_USER >/dev/null 2>&1 || useradd --system --shell /usr/sbin/nologin --home $APP_DIR $SVC_USER
  install -d -o $SVC_USER -g $SVC_USER $APP_DIR
  install -d -m 750 -o root -g $SVC_USER $ETC_DIR
"
ok "$SVC_USER exists, $APP_DIR ready"

step "10. Copying the code up"
# .env* is excluded deliberately: .env.live holds the live secret key and must
# never land in a directory the deploy rsyncs over.
rsync -a --delete \
  --exclude node_modules --exclude '.env' --exclude '.env.*' \
  --exclude sa.json --exclude '.DS_Store' --exclude 'test' \
  -e "ssh ${SSH_OPTS[*]}" \
  "$SRC/" "$HOST:$APP_DIR/"
sshx "chown -R $SVC_USER:$SVC_USER $APP_DIR"
ok "code copied (no secrets included)"

step "11. Installing dependencies"
sshx "cd $APP_DIR && sudo -u $SVC_USER npm ci --omit=dev --no-audit --no-fund" >/dev/null 2>&1 \
  || die "npm ci failed." "See what happened:  ssh $HOST 'cd $APP_DIR && npm ci --omit=dev'"
ok "dependencies installed"

step "12. Writing the environment file — WITH CARDS SWITCHED OFF"
# The Google key: reuse the storefront's, which is already a writer on the
# ledger sheets. Optional — without it orders go to the journal instead.
SA_NOTE="no ledger sheet (orders go to the log)"
if sshx "test -f /etc/storefront-offer-api/sa.json"; then
  sshx "cp -n /etc/storefront-offer-api/sa.json $ETC_DIR/sa.json \
        && chown root:$SVC_USER $ETC_DIR/sa.json && chmod 640 $ETC_DIR/sa.json" || true
  SA_NOTE="Google key in place (add CHECKOUT_SHEET_ID later to use a sheet)"
fi

backup_remote "$ETC_DIR/.env"

# Carry forward anything a human set by hand after an earlier run. This file is
# REWRITTEN whole, so a value not read back here is a value silently destroyed:
# blanking CHECKOUT_SHEET_ID moves every future order out of the Google Sheet
# and into a log file nobody reads, and /health still cheerfully says "ok":true.
# Found the hard way on 2026-09-05, when a re-run would have done exactly that.
KEEP_SHEET="$(sshx "grep -m1 '^CHECKOUT_SHEET_ID=' $ETC_DIR/.env 2>/dev/null | cut -d= -f2-" 2>/dev/null || true)"
KEEP_CRON="$(sshx "grep -m1 '^CRON_KEY=' $ETC_DIR/.env 2>/dev/null | cut -d= -f2-" 2>/dev/null || true)"
[[ -n "$KEEP_SHEET" ]] && ok "keeping the CHECKOUT_SHEET_ID already on the box" || warn "no CHECKOUT_SHEET_ID set — orders will go to the log, not the sheet"
[[ -n "$KEEP_CRON" ]] && ok "keeping the CRON_KEY already on the box" || true

printf '%s\n%s\n%s\n%s\n%s\n' "$T_SECRET" "$T_PUBLIC" "$RESEND_KEY" "$KEEP_SHEET" "$KEEP_CRON" | sshx "
  set -e
  read -r secret; read -r public; read -r resend; read -r sheet; read -r cron
  cat > $ETC_DIR/.env <<EOF
THAWANI_SECRET_KEY=\$secret
THAWANI_PUBLISHABLE_KEY=\$public
THAWANI_BASE=https://checkout.thawani.om

# THE SWITCH. 0 = every card is refused and the checkout hands the buyer to
# WhatsApp, truthfully saying nothing was charged. Set to 1 to go live.
PAY_ENABLED=0

SITE_ORIGIN=https://aiprofitlab.io
ORDER_PATH=/en/order-v4/
ALLOWED_ORIGINS=https://aiprofitlab.io,https://www.aiprofitlab.io

CHECKOUT_SHEET_ID=\$sheet
CHECKOUT_SHEET_TAB=Checkout_Orders
GOOGLE_APPLICATION_CREDENTIALS=$ETC_DIR/sa.json

RESEND_API_KEY=\$resend
OWNER_EMAIL=hello@aiprofitlab.io

CRON_KEY=\$cron
PORT=$PORT
EOF
  chown root:$SVC_USER $ETC_DIR/.env && chmod 640 $ETC_DIR/.env
"
ok "environment written, PAY_ENABLED=0"
info "$SA_NOTE"

step "13. Installing the service"
sshx "
  set -e
  cp $APP_DIR/deploy/checkout-api.service $UNIT
  systemctl daemon-reload
  systemctl enable $SVC >/dev/null 2>&1
  systemctl restart $SVC
"
sleep 4
sshx "systemctl is-active --quiet $SVC" \
  || die "$SVC did not start." "Read the log:  ssh $HOST 'journalctl -u $SVC -n 40 --no-pager'"
ok "$SVC is running and will start on boot"

step "14. Opening the port to Traefik only"
sshx "ufw allow from 172.16.1.0/24 to any port $PORT proto tcp" >/dev/null 2>&1 || true
ok "port $PORT reachable from the bridge, closed to the internet"

step "15. Publishing the route"
sshx "cp $APP_DIR/deploy/traefik-checkout.yml $TRAEFIK"
ok "route file saved (Traefik picks it up on its own, nothing restarts)"

# ============================================================================
# PHASE D — prove it
# ============================================================================

step "16. Checking the service from inside the box"
HEALTH="$(sshx "curl -s -m 10 localhost:$PORT/health" || true)"
grep -q '"ok":true' <<<"$HEALTH" || die "The service is not answering." "Got: $HEALTH"
grep -q '"env":"live"' <<<"$HEALTH" || die "The service is NOT pointed at the live gateway." "Got: $HEALTH"
grep -q '"keys":true' <<<"$HEALTH" || die "The Thawani keys did not load." "Got: $HEALTH"
grep -q '"accepting_cards":false' <<<"$HEALTH" || warn "accepting_cards is not false — check the env file"
ok "live gateway, keys loaded, cards correctly OFF"

step "17. Checking it from the outside"
info "waiting for the certificate to be issued (up to 60s on first request)..."
EXT=""
for i in $(seq 1 12); do
  EXT="$(curl -s -m 10 "https://$DOMAIN/session/probe" 2>/dev/null || true)"
  [[ -n "$EXT" ]] && break
  sleep 5
done
[[ -n "$EXT" ]] \
  || die "$DOMAIN is not answering from the internet yet." \
"Usually DNS or the certificate needing another minute. Try by hand:
  curl -v https://$DOMAIN/session/probe"
ok "$DOMAIN is live and serving over HTTPS"

step "18. Checking that strangers are refused"
STRANGER="$(curl -si -m 10 -X POST "https://$DOMAIN/session" \
  -H 'Origin: https://evil.example' -H 'Content-Type: application/json' \
  -d '{}' 2>/dev/null | grep -ci 'access-control-allow-origin' || true)"
[[ "$STRANGER" == "0" ]] \
  && ok "a stranger's website cannot use your payment endpoint" \
  || warn "CORS allowed an unexpected origin — tell Claude before going live"

# ============================================================================
# DONE — and deliberately stopping here
# ============================================================================

cat <<EOF

${G}┌────────────────────────────────────────────────────────────┐
│  Deployed. Nothing is taking cards yet — by design.        │
└────────────────────────────────────────────────────────────┘${X}

  Everything is installed, verified, and switched OFF. Email is fixed on
  both services. The two commands below are the only irreversible steps,
  and they are yours.

${B}  A. Turn on the v4 checkout${X}

     ssh $HOST "sed -i 's/^PAY_ENABLED=0/PAY_ENABLED=1/' $ETC_DIR/.env && systemctl restart $SVC"
     ssh $HOST "curl -s localhost:$PORT/health"   # want: "accepting_cards":true
     #   /health is deliberately NOT routed publicly — ask the box, not the internet.

     Then, on this Mac, in tools/v4/pay.py:
         PAY_LIVE    = True
         PAY_API     = "https://$DOMAIN"
         THAWANI_ENV = "live"
     ...rebuild, and push to deploy the site.

${B}  B. Turn on the campaign page${X}

     ssh $HOST "sed -i 's/^PAY_ENABLED=0/PAY_ENABLED=1/' $STOREFRONT_ETC && systemctl restart $STOREFRONT_SVC"
     curl -s https://offer.aiprofitlab.io/status | grep -o '"pay":{[^}]*}'

     Want: {"card":true}. No site rebuild needed — the campaign pages read
     that flag from the service, so the card button appears on its own.

${B}  If anything goes wrong, at any time${X}

     ssh $HOST "sed -i 's/^PAY_ENABLED=1/PAY_ENABLED=0/' $ETC_DIR/.env && systemctl restart $SVC"
     ssh $HOST "sed -i 's/^PAY_ENABLED=1/PAY_ENABLED=0/' $STOREFRONT_ETC && systemctl restart $STOREFRONT_SVC"

     Cards stop instantly on that path. Buyers get the offline handover and
     are told, truthfully, that nothing was charged.

  Backups taken this run are named *.bak-$STAMP

EOF
