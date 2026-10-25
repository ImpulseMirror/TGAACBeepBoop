#!/bin/sh
# Phoenix Wright trilogy: male and female blips at 15%, typewriter muted.
# Needs ffmpeg on PATH (partial volume). Mute-only does not.
# Optional: path to the install.
#   ./examples/pwaat-quiet.sh
#   ./examples/pwaat-quiet.sh "/path/to/Phoenix Wright Ace Attorney Trilogy"

set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
GAME=${1:-}
set -- --male 15 --female 15 --typewriter 0
if [ -n "$GAME" ]; then
  set -- "$@" --game-dir "$GAME"
fi
exec python3 "$ROOT/PWAAT/set-text-beep-volume.py" "$@"
