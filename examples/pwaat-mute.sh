#!/bin/sh
# Mute Phoenix Wright trilogy dialogue blips (male, female, typewriter).
# Mute does not need ffmpeg. Partial volume does.
# Optional: path to the install (the folder that contains PWAAT.exe).
#   ./examples/pwaat-mute.sh
#   ./examples/pwaat-mute.sh "$HOME/.local/share/Steam/steamapps/common/Phoenix Wright Ace Attorney Trilogy"

set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
GAME=${1:-}
set -- --male 0 --female 0 --typewriter 0
if [ -n "$GAME" ]; then
  set -- "$@" --game-dir "$GAME"
fi
exec python3 "$ROOT/PWAAT/set-text-beep-volume.py" "$@"
