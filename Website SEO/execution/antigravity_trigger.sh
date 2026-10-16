#!/bin/sh
# Antigravity's scheduler runs this every hour (see execution/setup_antigravity_publisher.py).
# It hands over to agent_publish.py at once, which starts a conversation only when there is
# work. Python reads its whole script before running, so the clone can be updated under it.
cd "$(dirname "$0")/.." || exit 1
for py in /Library/Frameworks/Python.framework/Versions/3.*/bin/python3 \
          /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3 python3; do
  if "$py" -c 'import PIL, certifi, zoneinfo' >/dev/null 2>&1; then
    exec "$py" execution/agent_publish.py trigger "$@"
  fi
done
echo "No python3 with Pillow and certifi; run: python3 -m pip install Pillow certifi" >&2
exit 1
