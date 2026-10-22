# TGAACBeepBoop

Turn down (or mute) dialogue text sounds in
[*The Great Ace Attorney Chronicles*](https://store.steampowered.com/app/1158850)
**without** muting the rest of the sound effects.

Two independent controls:

| Option | What it changes | Samples |
|--------|-----------------|---------|
| **beep** | Typewriter beeps while text appears | `message_male`, `message_female` |
| **advance** | Click when you advance the text box | `page` |

| Volume | Result |
|--------|--------|
| `100` | Default (original) |
| `1`–`99` | Quieter |
| `0` | Mute that sound only |
| `restore` | Undo everything from backup |

The stock game only has a global SFX slider. Deleting the loose `.xsew` files
does **nothing** — the game plays these from packed Capcom `.arc` archives.
This patcher edits those archives in place.

## Requirements

- A legal Steam copy of TGAAC
- [Python 3](https://www.python.org/downloads/) on your PATH (no pip packages)

## Install

1. Download a [release](https://github.com/ImpulseMirror/TGAACBeepBoop/releases) zip, **or** clone this repo.
2. Put the folder inside your TGAAC install (next to `TGAAC.exe`):

```text
TGAAC/
  TGAAC.exe
  nativeDX11x64/
  TGAACBeepBoop/          <-- this project
    set-text-beep-volume.py
    ...
```

Steam folder examples:

- Windows: `C:\Program Files (x86)\Steam\steamapps\common\TGAAC\`
- macOS: `~/Library/Application Support/Steam/steamapps/common/TGAAC/`
- Linux: `~/.local/share/Steam/steamapps/common/TGAAC/`

Close the game before patching. Steam **Verify integrity of game files** will
undo the patch.

## How to run

### All platforms (recommended)

```bash
python set-text-beep-volume.py
```

Interactive: asks for **beep** and **advance** separately (blank keeps the
last saved value).

```bash
# Mute both
python set-text-beep-volume.py --beep 0 --advance 0

# Quiet typewriter, mute advance click
python set-text-beep-volume.py --beep 10 --advance 0

# Only change advance click (beep stays at last saved value)
python set-text-beep-volume.py --advance 0

# Legacy: bare number still sets beep only
python set-text-beep-volume.py 0

# Restore originals
python set-text-beep-volume.py restore
# or
python set-text-beep-volume.py --restore

# Show saved volumes
python set-text-beep-volume.py --show
```

`python3` or `py -3` also work.

Settings are remembered in:

`nativeDX11x64/archive/.tgaac_text_beep_backup/settings.json`

So changing one option does not reset the other.

### Optional OS helpers

| OS | Helper |
|----|--------|
| Windows | Double-click `set-text-beep-volume.bat` |
| Linux | `chmod +x set-text-beep-volume.sh && ./set-text-beep-volume.sh` |
| macOS | Double-click `set-text-beep-volume.command`, or run the `.sh` |

Windows cannot run `.sh`. macOS/Linux cannot run `.bat`. The `.py` entry works
everywhere Python is installed.

## Releases

| Asset | Contents |
|-------|----------|
| `TGAACBeepBoop-full-*.zip` | Everything (clone equivalent) |
| `TGAACBeepBoop-windows-*.zip` | `.bat` + Python scripts + README |
| `TGAACBeepBoop-unix-*.zip` | `.sh` + `.command` + Python scripts + README |

```bash
git clone https://github.com/ImpulseMirror/TGAACBeepBoop.git
```

## What files get changed

Only these (when present):

- `nativeDX11x64/archive/BB/snd_script_eng.arc` (+ `_jpn` if installed)
- `nativeDX11x64/archive/GO/snd_script_eng.arc` (+ `_jpn` if installed)

First run copies originals to:

`nativeDX11x64/archive/.tgaac_text_beep_backup/`

Later changes always re-apply from that backup (not cumulative).

## Sharing / legal

Share **this tool**, not Capcom’s `.arc` files. You need your own Steam copy
of the game. This is an unofficial fan utility; not affiliated with Capcom.

## License

MIT — see [LICENSE](LICENSE).
