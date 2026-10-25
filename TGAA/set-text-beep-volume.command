#!/usr/bin/env sh
# macOS double-click launcher (same as .sh, pauses so the window stays open)
DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$DIR"
chmod +x "$DIR/set-text-beep-volume.sh" 2>/dev/null || true
"$DIR/set-text-beep-volume.sh" "$@"
status=$?
echo
echo "Press Enter to close..."
# shellcheck disable=SC2034
read -r _
exit "$status"
