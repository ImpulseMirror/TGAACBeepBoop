#!/bin/sh
# Mute TGAAC typewriter beeps and the text-advance click.
# Optional: path to the TGAAC install (the folder that contains TGAAC.exe).
#   ./examples/tgaa-mute.sh
#   ./examples/tgaa-mute.sh "$HOME/.local/share/Steam/steamapps/common/TGAAC"

set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
GAME=${1:-}
set -- --beep 0 --advance 0
if [ -n "$GAME" ]; then
  set -- "$@" --game-dir "$GAME"
fi
exec python3 "$ROOT/TGAA/set-text-beep-volume.py" "$@"
