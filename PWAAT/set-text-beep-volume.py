#!/usr/bin/env python3
"""Universal launcher — Windows, macOS, and Linux if Python 3 is installed.

  python set-text-beep-volume.py
  python set-text-beep-volume.py --male 0 --female 0 --typewriter 0
  python set-text-beep-volume.py restore
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_TARGET = _HERE / "pwaat_text_beep_volume.py"

if not _TARGET.is_file():
    sys.stderr.write(f"error: missing {_TARGET.name} next to this launcher\n")
    sys.exit(1)

sys.argv[0] = str(_TARGET)
runpy.run_path(str(_TARGET), run_name="__main__")
