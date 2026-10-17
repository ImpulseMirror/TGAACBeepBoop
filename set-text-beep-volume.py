#!/usr/bin/env python3
"""Universal launcher — works on Windows, macOS, and Linux if Python 3 is installed.

  python set-text-beep-volume.py
  python set-text-beep-volume.py 0
  python3 set-text-beep-volume.py 25
  py -3 set-text-beep-volume.py restore
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

# Prefer the full patcher module next to this file
_HERE = Path(__file__).resolve().parent
_TARGET = _HERE / "tgaac_text_beep_volume.py"

if not _TARGET.is_file():
    sys.stderr.write(f"error: missing {_TARGET.name} next to this launcher\n")
    sys.exit(1)

# Make argv look like the real script was invoked (helps some tooling)
sys.argv[0] = str(_TARGET)
runpy.run_path(str(_TARGET), run_name="__main__")
