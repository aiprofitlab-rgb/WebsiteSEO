#!/bin/sh
# Antigravity's scheduler runs this every 10 minutes from the HARO runner
# (~/Developer/aiprofitlab-haro/runner; see `haro_agent.py setup`). It finds a python3 with the
# Gmail client libraries and hands over to haro_agent.py with the given command (trigger, selftest).
cd "$(dirname "$0")/.." || exit 1
for py in /Library/Frameworks/Python.framework/Versions/3.*/bin/python3 \
          /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3 python3; do
  if "$py" -c 'import googleapiclient, google_auth_oauthlib, requests' >/dev/null 2>&1; then
    exec "$py" execution/haro_agent.py "$@"
  fi
done
echo "No python3 with the Gmail client libraries; run: python3 -m pip install google-api-python-client google-auth-oauthlib requests" >&2
exit 1
