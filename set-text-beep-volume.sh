#!/usr/bin/env sh
# TGAAC text-beep volume — Linux / macOS / Git Bash
# Drop the text-beep-patcher folder into your TGAAC install, then:
#   ./set-text-beep-volume.sh          # interactive
#   ./set-text-beep-volume.sh 0        # mute
#   ./set-text-beep-volume.sh 25       # 25%
#   ./set-text-beep-volume.sh 100      # default
#   ./set-text-beep-volume.sh restore  # undo

set -eu
DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$DIR"

pick_python() {
  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return
  fi
  if command -v python >/dev/null 2>&1; then
    # Ensure it's Python 3
    if python -c 'import sys; raise SystemExit(0 if sys.version_info[0] >= 3 else 1)' 2>/dev/null; then
      command -v python
      return
    fi
  fi
  return 1
}

if ! PY=$(pick_python); then
  echo "error: Python 3 is required." >&2
  echo "  macOS:  brew install python   (or install from python.org)" >&2
  echo "  Linux:  sudo apt install python3   (or your distro equivalent)" >&2
  exit 1
fi

exec "$PY" "$DIR/set-text-beep-volume.py" "$@"
