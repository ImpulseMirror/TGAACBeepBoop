#!/bin/sh
# TGAAC: typewriter beeps at 10%, advance click muted.
# Optional: path to the TGAAC install.
#   ./examples/tgaa-quiet-beep.sh
#   ./examples/tgaa-quiet-beep.sh /path/to/TGAAC

set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
GAME=${1:-}
set -- --beep 10 --advance 0
if [ -n "$GAME" ]; then
  set -- "$@" --game-dir "$GAME"
fi
exec python3 "$ROOT/TGAA/set-text-beep-volume.py" "$@"
