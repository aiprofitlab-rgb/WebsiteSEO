#!/bin/sh
# Antigravity keeps this running while the app is open (see setup_antigravity_publisher.py).
# It runs the agent's link checks, source checks and image reads outside the terminal
# sandbox, which has no internet and cannot read the image tool's output folder.
cd "$(dirname "$0")/.." || exit 1
for py in /Library/Frameworks/Python.framework/Versions/3.*/bin/python3 \
          /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3 python3; do
  if "$py" -c 'import PIL, certifi, zoneinfo' >/dev/null 2>&1; then
    exec "$py" execution/agent_publish.py serve
  fi
done
echo "No python3 with Pillow and certifi; run: python3 -m pip install Pillow certifi" >&2
exit 1
