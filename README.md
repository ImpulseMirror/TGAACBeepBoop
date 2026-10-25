# TGAACBeepBoop

Turn down (or mute) a few dialogue sounds in two Capcom Ace Attorney PC ports
**without** muting the rest of the sound effects.

| Game | What you can change |
|------|---------------------|
| [The Great Ace Attorney Chronicles](https://store.steampowered.com/app/1158850) | Typewriter beeps, and the click that advances the text box |
| [Phoenix Wright: Ace Attorney Trilogy](https://store.steampowered.com/app/787480) | The three dialogue blips (male, female, typewriter) |

| Volume | Result |
|--------|--------|
| `100` | Original |
| `1`–`99` | Quieter |
| `0` | Mute that sound only |
| `restore` | Undo from the backup this tool made |

The stock games only have a global SFX slider. These tools edit the sound
files the games actually play. Steam **Verify integrity of game files** puts
the originals back.

## Requirements

- Your own Steam copy of the game
- [Python 3](https://www.python.org/downloads/) on your PATH (no pip packages)
- Phoenix Wright partial volume (`1`–`99`) also needs [ffmpeg](https://ffmpeg.org/) on your PATH. Mute (`0`) and restore do not.

## The Great Ace Attorney Chronicles

Scripts live in [`TGAA/`](TGAA/). The game plays these from packed `.arc`
archives (deleting loose files does nothing):

| Option | What it changes | Samples |
|--------|-----------------|---------|
| **beep** | Typewriter beeps while text appears | `message_male`, `message_female` |
| **advance** | Click when you advance the text box | `page` |

Put this repo inside the install, next to `TGAAC.exe`:

```text
TGAAC/
  TGAAC.exe
  nativeDX11x64/
  TGAACBeepBoop/
    TGAA/set-text-beep-volume.py
```

Steam folder examples:

- Windows: `C:\Program Files (x86)\Steam\steamapps\common\TGAAC\`
- macOS: `~/Library/Application Support/Steam/steamapps/common/TGAAC/`
- Linux: `~/.local/share/Steam/steamapps/common/TGAAC/`

Close the game first.

```bash
python TGAA/set-text-beep-volume.py
```

Blank at a prompt keeps the last saved value. `python3` and `py -3` work too.

```bash
python TGAA/set-text-beep-volume.py --beep 0 --advance 0
python TGAA/set-text-beep-volume.py --beep 10 --advance 0
python TGAA/set-text-beep-volume.py --advance 0
python TGAA/set-text-beep-volume.py 0          # legacy: beep only
python TGAA/set-text-beep-volume.py restore
python TGAA/set-text-beep-volume.py --show
python TGAA/set-text-beep-volume.py --game-dir "/path/to/TGAAC"
```

| OS | Helper |
|----|--------|
| Windows | Double-click `TGAA/set-text-beep-volume.bat` |
| Linux | `chmod +x TGAA/set-text-beep-volume.sh && ./TGAA/set-text-beep-volume.sh` |
| macOS | Double-click `TGAA/set-text-beep-volume.command`, or run the `.sh` |

Or, from a clone that is **not** inside the install:

```bash
./examples/tgaa-mute.sh "/path/to/TGAAC"         # both off
./examples/tgaa-quiet-beep.sh "/path/to/TGAAC"   # beep 10%, advance off
```

Saved volumes:

`nativeDX11x64/archive/.tgaac_text_beep_backup/settings.json`

Files touched (when present):

- `nativeDX11x64/archive/BB/snd_script_eng.arc` (+ `_jpn`)
- `nativeDX11x64/archive/GO/snd_script_eng.arc` (+ `_jpn`)

The first run copies originals to `nativeDX11x64/archive/.tgaac_text_beep_backup/`.
Later runs always start from that backup.

`TGAAC_DIR` is another way to point at the install.

## Phoenix Wright: Ace Attorney Trilogy

Scripts live in [`PWAAT/`](PWAAT/). This port is a different engine (Unity).
Dialogue blips are three short clips. `MessageSystem` picks one from the
speaker's `message_se` value. There is no separate "advance click" sample;
menu confirms are shared with the rest of the UI and this tool leaves them alone.

| Option | `message_se` | File |
|--------|--------------|------|
| **male** | 0 (default) | `Sound/se/wsd/se003.unity3d` |
| **female** | 1 | `Sound/se/wsd/se004.unity3d` |
| **typewriter** | 2 | `Sound/se/wsd/se01a.unity3d` |

Put this repo inside the install, next to `PWAAT.exe`:

```text
Phoenix Wright Ace Attorney Trilogy/
  PWAAT.exe
  PWAAT_Data/
  TGAACBeepBoop/
    PWAAT/set-text-beep-volume.py
```

Steam folder name: `Phoenix Wright Ace Attorney Trilogy`.

Close the game first.

```bash
python PWAAT/set-text-beep-volume.py
python PWAAT/set-text-beep-volume.py --male 0 --female 0 --typewriter 0
python PWAAT/set-text-beep-volume.py --male 15 --female 15 --typewriter 0
python PWAAT/set-text-beep-volume.py --typewriter 0
python PWAAT/set-text-beep-volume.py restore
python PWAAT/set-text-beep-volume.py --show
python PWAAT/set-text-beep-volume.py --game-dir "/path/to/Phoenix Wright Ace Attorney Trilogy"
```

| OS | Helper |
|----|--------|
| Windows | Double-click `PWAAT/set-text-beep-volume.bat` |
| Linux | `chmod +x PWAAT/set-text-beep-volume.sh && ./PWAAT/set-text-beep-volume.sh` |
| macOS | Double-click `PWAAT/set-text-beep-volume.command`, or run the `.sh` |

```bash
./examples/pwaat-mute.sh "/path/to/Phoenix Wright Ace Attorney Trilogy"
./examples/pwaat-quiet.sh "/path/to/Phoenix Wright Ace Attorney Trilogy"
```

`0` rewrites the clip as silence and does not need ffmpeg. `1`–`99` decodes
the original with ffmpeg, scales it, and writes it back. `100` puts the
backup bytes back.

Saved volumes:

`PWAAT_Data/StreamingAssets/Sound/.pwaat_text_beep_backup/settings.json`

`PWAAT_DIR` is another way to point at the install.

## Examples

| Script | Effect |
|--------|--------|
| [`examples/tgaa-mute.sh`](examples/tgaa-mute.sh) | TGAAC beep and advance at 0 |
| [`examples/tgaa-quiet-beep.sh`](examples/tgaa-quiet-beep.sh) | TGAAC beep at 10, advance at 0 |
| [`examples/pwaat-mute.sh`](examples/pwaat-mute.sh) | All three trilogy blips at 0 |
| [`examples/pwaat-quiet.sh`](examples/pwaat-quiet.sh) | Trilogy male/female at 15, typewriter at 0 |

Each takes an optional install path as its first argument.

## Sharing / legal

Share **this tool**, not Capcom’s game files. You need your own Steam copy.
Unofficial fan utility; not affiliated with Capcom.

## License

MIT — see [LICENSE](LICENSE).
