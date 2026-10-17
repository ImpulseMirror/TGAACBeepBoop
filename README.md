# TGAACBeepBoop

Turn down (or mute) the dialogue **typewriter beep** in
[*The Great Ace Attorney Chronicles*](https://store.steampowered.com/app/1158850)
without muting the rest of the sound effects.

The stock game only has a global SFX slider. Deleting the loose
`message_male.xsew` / `message_female.xsew` files does **nothing** — the game
plays those samples from packed Capcom `.arc` archives. This patcher edits
those archives in place.

| Volume | Result |
|--------|--------|
| `100` | Default (original beeps) |
| `1`–`99` | Quieter beeps |
| `0` | Mute beeps only |
| `restore` | Undo from backup |

Other SFX (desk slam, objection, UI clicks, etc.) are left alone.

## Requirements

- A legal Steam copy of TGAAC
- [Python 3](https://www.python.org/downloads/) on your PATH (no pip packages)

## Install

1. Download a release asset below, **or** clone this repo.
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

`python3` or `py -3` also work. No arguments → interactive prompt.

```bash
python set-text-beep-volume.py 0        # mute
python set-text-beep-volume.py 25       # quiet
python set-text-beep-volume.py 100      # default
python set-text-beep-volume.py restore  # undo
```

### Optional OS helpers

| OS | Helper |
|----|--------|
| Windows | Double-click `set-text-beep-volume.bat` |
| Linux | `chmod +x set-text-beep-volume.sh && ./set-text-beep-volume.sh` |
| macOS | Double-click `set-text-beep-volume.command`, or run the `.sh` |

Windows cannot run `.sh`. macOS/Linux cannot run `.bat`. The `.py` entry works
everywhere Python is installed.

## Releases

Each GitHub Release attaches zip downloads:

| Asset | Contents |
|-------|----------|
| `TGAACBeepBoop-full-*.zip` | Everything (clone equivalent) |
| `TGAACBeepBoop-windows-*.zip` | `.bat` + Python scripts + README |
| `TGAACBeepBoop-unix-*.zip` | `.sh` + `.command` + Python scripts + README |

Or clone the whole repo:

```bash
git clone https://github.com/ImpulseMirror/TGAACBeepBoop.git
```

## What files get changed

Only these (when present):

- `nativeDX11x64/archive/BB/snd_script_eng.arc` (+ `_jpn` if installed)
- `nativeDX11x64/archive/GO/snd_script_eng.arc` (+ `_jpn` if installed)

First run copies originals to:

`nativeDX11x64/archive/.tgaac_text_beep_backup/`

Later volume changes always re-apply from that backup (not cumulative).

## Sharing / legal

Share **this tool**, not Capcom’s `.arc` files. You need your own Steam copy
of the game. This is an unofficial fan utility; not affiliated with Capcom.

## License

MIT — see [LICENSE](LICENSE).
