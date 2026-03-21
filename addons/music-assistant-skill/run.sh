#!/usr/bin/env bash
set -euo pipefail

OPTIONS_FILE="/data/options.json"

if [ -f "$OPTIONS_FILE" ]; then
  # Export allowed options as environment variables unless already set.
  eval "$(python - <<'PY'
import json
import os
import shlex

allowed = {
    "MA_HOSTNAME",
    "STREAM_HOSTNAME",
    "APP_USERNAME",
    "APP_PASSWORD",
    "PORT",
    "DEBUG_PORT",
    "AWS_DEFAULT_REGION",
    "SKILL_HOSTNAME",
    "LOCALE",
}

try:
    with open("/data/options.json", "r", encoding="utf-8") as fh:
        data = json.load(fh)
except FileNotFoundError:
    data = {}

for key in sorted(allowed):
    if key in os.environ and os.environ.get(key) not in (None, ""):
        continue
    if key not in data:
        continue
    val = data.get(key)
    if val is None:
        continue
    if isinstance(val, bool):
        val = "true" if val else "false"
    export_line = f"export {key}={shlex.quote(str(val))}"
    print(export_line)
PY
)"
fi

PORT="${PORT:-5000}"
DEBUG_PORT="${DEBUG_PORT:-0}"

if [ -n "$DEBUG_PORT" ] && [ "$DEBUG_PORT" != "0" ]; then
  exec python -m debugpy --listen 0.0.0.0:"$DEBUG_PORT" app/app.py
else
  exec python app/app.py
fi
