#!/usr/bin/env python3
"""
TGAAC text SFX volume patcher (beep + advance click)

Drop this folder into your TGAAC install (next to TGAAC.exe), then run:
  python set-text-beep-volume.py

Independent controls:
  beep     — dialogue typewriter beeps (message_male / message_female)
  advance  — text-box advance click (chin)

Volumes always re-apply from a one-time backup (not cumulative).
100% = original sample. 0% = mute.
"""

from __future__ import annotations

import argparse
import json
import os
import struct
import sys
import zlib
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

ARC_MAGIC = b"ARC\x00"
ENTRY_STRIDE = 144
PATH_LEN = 0x80
DATA_ALIGN = 0x8000
USIZE_FLAG = 0x40000000

# Independent volume channels → sample stem names inside snd_script_*.arc
CHANNELS: Dict[str, Tuple[str, ...]] = {
    "beep": ("message_male", "message_female"),
    "advance": ("chin",),
}
CHANNEL_LABELS = {
    "beep": "text beep (typewriter)",
    "advance": "text advance click",
}
DEFAULT_SETTINGS: Dict[str, float] = {name: 100.0 for name in CHANNELS}
SETTINGS_FILE = "settings.json"

ADAPTATION = [
    230, 230, 230, 230, 307, 409, 512, 614,
    768, 614, 512, 409, 307, 230, 230, 230,
]


class PatchError(Exception):
    pass


def eprint(*args: object) -> None:
    print(*args, file=sys.stderr)


def script_dir() -> Path:
    return Path(__file__).resolve().parent


def looks_like_tgaac(path: Path) -> bool:
    return (path / "nativeDX11x64" / "archive").is_dir() or (path / "TGAAC.exe").is_file()


# ---------------------------------------------------------------------------
# MS ADPCM
# ---------------------------------------------------------------------------

def _clamp16(v: int) -> int:
    return -32768 if v < -32768 else 32767 if v > 32767 else v


def ms_adpcm_decode(fmt: bytes, data: bytes) -> Tuple[List[int], dict]:
    if len(fmt) < 50:
        raise PatchError("unexpected fmt chunk size for MS ADPCM")
    tag, channels, rate, _br, block_align, bps = struct.unpack_from("<HHIIHH", fmt, 0)
    if tag != 2:
        raise PatchError(f"expected MS ADPCM (tag=2), got {tag}")
    if channels != 1:
        raise PatchError(f"expected mono, got {channels} channels")
    _cb_size, samples_per_block, n_coefs = struct.unpack_from("<HHH", fmt, 16)
    if n_coefs < 1:
        raise PatchError("MS ADPCM nCoeffs < 1")
    coefs = [
        struct.unpack_from("<hh", fmt, 22 + i * 4)
        for i in range(n_coefs)
    ]
    if block_align <= 0 or len(data) % block_align != 0:
        raise PatchError(f"data length {len(data)} not multiple of block align {block_align}")

    pcm: List[int] = []
    for off in range(0, len(data), block_align):
        block = data[off : off + block_align]
        predictor = block[0]
        if predictor >= len(coefs):
            raise PatchError(f"bad predictor index {predictor}")
        delta = struct.unpack_from("<h", block, 1)[0]
        sample1 = struct.unpack_from("<h", block, 3)[0]
        sample2 = struct.unpack_from("<h", block, 5)[0]
        coef1, coef2 = coefs[predictor]
        pcm.append(sample2)
        pcm.append(sample1)
        s1, s2 = sample1, sample2
        nibble_bytes = block[7:]
        produced = 2
        for byte in nibble_bytes:
            for nibble in ((byte >> 4) & 0xF, byte & 0xF):
                if produced >= samples_per_block:
                    break
                signed = nibble - 16 if nibble & 0x8 else nibble
                pred = ((s1 * coef1) + (s2 * coef2)) // 256
                sample = _clamp16(pred + signed * delta)
                pcm.append(sample)
                delta = max(16, (delta * ADAPTATION[nibble]) // 256)
                s2, s1 = s1, sample
                produced += 1
            if produced >= samples_per_block:
                break
    meta = {
        "channels": channels,
        "rate": rate,
        "bps": bps,
        "block_align": block_align,
        "samples_per_block": samples_per_block,
        "coefs": coefs,
        "fmt": fmt,
    }
    return pcm, meta


def ms_adpcm_encode(pcm: Sequence[int], meta: dict) -> bytes:
    channels = meta["channels"]
    block_align = meta["block_align"]
    samples_per_block = meta["samples_per_block"]
    coefs: Sequence[Tuple[int, int]] = meta["coefs"]
    if channels != 1:
        raise PatchError("encode only supports mono")

    samples = list(pcm)
    rem = len(samples) % samples_per_block
    if rem:
        samples.extend([0] * (samples_per_block - rem))

    out = bytearray()
    for i in range(0, len(samples), samples_per_block):
        block_samples = samples[i : i + samples_per_block]
        predictor = 0
        coef1, coef2 = coefs[predictor]
        sample2 = _clamp16(block_samples[0])
        sample1 = _clamp16(block_samples[1])
        delta = 16
        for a, b in zip(block_samples, block_samples[1:]):
            delta = max(delta, abs(a - b) * 2)
        delta = min(delta, 32767)

        block = bytearray(block_align)
        block[0] = predictor
        struct.pack_into("<h", block, 1, delta)
        struct.pack_into("<h", block, 3, sample1)
        struct.pack_into("<h", block, 5, sample2)

        s1, s2 = sample1, sample2
        nibbles: List[int] = []
        for sample in block_samples[2:]:
            pred = ((s1 * coef1) + (s2 * coef2)) // 256
            if delta <= 0:
                delta = 16
            diff = sample - pred
            nibble = int(round(diff / delta))
            nibble = -8 if nibble < -8 else 7 if nibble > 7 else nibble
            unsigned = nibble & 0xF
            decoded = _clamp16(pred + nibble * delta)
            delta = max(16, (delta * ADAPTATION[unsigned]) // 256)
            s2, s1 = s1, decoded
            nibbles.append(unsigned)

        for bi, n_off in enumerate(range(0, len(nibbles), 2)):
            hi = nibbles[n_off]
            lo = nibbles[n_off + 1] if n_off + 1 < len(nibbles) else 0
            block[7 + bi] = ((hi & 0xF) << 4) | (lo & 0xF)
        out.extend(block)
    return bytes(out)


def scale_pcm(pcm: Sequence[int], volume_pct: float) -> List[int]:
    if volume_pct <= 0:
        return [0] * len(pcm)
    if volume_pct >= 100:
        return list(pcm)
    gain = volume_pct / 100.0
    return [_clamp16(int(round(s * gain))) for s in pcm]


def parse_wave(blob: bytes) -> Tuple[bytes, bytes, List[Tuple[bytes, bytes]]]:
    if blob[:4] != b"RIFF" or blob[8:12] != b"WAVE":
        raise PatchError("not a RIFF WAVE")
    pos = 12
    fmt = data = None
    extras: List[Tuple[bytes, bytes]] = []
    while pos + 8 <= len(blob):
        chunk = blob[pos : pos + 4]
        size = struct.unpack_from("<I", blob, pos + 4)[0]
        payload = blob[pos + 8 : pos + 8 + size]
        if chunk == b"fmt ":
            fmt = payload
        elif chunk == b"data":
            data = payload
        else:
            extras.append((chunk, payload))
        pos += 8 + size + (size & 1)
    if fmt is None or data is None:
        raise PatchError("WAVE missing fmt/data")
    return fmt, data, extras


def build_wave(fmt: bytes, data: bytes, extras: Sequence[Tuple[bytes, bytes]]) -> bytes:
    parts = [b"WAVE", b"fmt ", struct.pack("<I", len(fmt)), fmt]
    if len(fmt) & 1:
        parts.append(b"\x00")
    parts += [b"data", struct.pack("<I", len(data)), data]
    if len(data) & 1:
        parts.append(b"\x00")
    for chunk, payload in extras:
        parts += [chunk, struct.pack("<I", len(payload)), payload]
        if len(payload) & 1:
            parts.append(b"\x00")
    body = b"".join(parts)
    return b"RIFF" + struct.pack("<I", len(body)) + body


def adjust_wave_volume(blob: bytes, volume_pct: float) -> bytes:
    fmt, data, extras = parse_wave(blob)
    if volume_pct >= 100:
        return blob
    pcm, meta = ms_adpcm_decode(fmt, data)
    pcm = scale_pcm(pcm, volume_pct)
    new_data = ms_adpcm_encode(pcm, meta)
    return build_wave(fmt, new_data, extras)


# ---------------------------------------------------------------------------
# Capcom ARC
# ---------------------------------------------------------------------------

class ArcEntry:
    __slots__ = ("path", "hash", "csize", "usize_field", "offset", "blob")

    def __init__(
        self,
        path: str,
        hash_: int,
        csize: int,
        usize_field: int,
        offset: int,
        blob: bytes,
    ) -> None:
        self.path = path
        self.hash = hash_
        self.csize = csize
        self.usize_field = usize_field
        self.offset = offset
        self.blob = blob

    @property
    def name(self) -> str:
        return Path(self.path.replace("\\", "/")).stem

    @property
    def usize(self) -> int:
        return self.usize_field & 0x00FFFFFF


def read_arc(path: Path) -> Tuple[bytes, int, List[ArcEntry]]:
    data = path.read_bytes()
    if data[:4] != ARC_MAGIC:
        raise PatchError(f"{path}: not an ARC file")
    version = struct.unpack_from("<H", data, 4)[0]
    count = struct.unpack_from("<H", data, 6)[0]
    entries: List[ArcEntry] = []
    for i in range(count):
        eoff = 8 + i * ENTRY_STRIDE
        raw_path = data[eoff : eoff + PATH_LEN].split(b"\x00", 1)[0]
        path_s = raw_path.decode("ascii", "ignore")
        hash_, csize, usize_field, offset = struct.unpack_from("<IIII", data, eoff + PATH_LEN)
        blob = data[offset : offset + csize]
        try:
            zlib.decompress(blob)
        except zlib.error as exc:
            raise PatchError(f"{path}: entry {path_s!r} zlib error: {exc}") from exc
        entries.append(ArcEntry(path_s, hash_, csize, usize_field, offset, blob))
    return data[:8], version, entries


def build_arc(header8: bytes, entries: Sequence[ArcEntry]) -> bytes:
    count = len(entries)
    header = bytearray(header8)
    struct.pack_into("<H", header, 6, count)

    offset = DATA_ALIGN
    placed: List[Tuple[ArcEntry, int, bytes]] = []
    for ent in entries:
        placed.append((ent, offset, ent.blob))
        offset += len(ent.blob)

    toc_size = 8 + count * ENTRY_STRIDE
    if toc_size > DATA_ALIGN:
        raise PatchError(f"TOC too large ({toc_size} > {DATA_ALIGN})")

    out = bytearray(b"\x00" * offset)
    out[:8] = header
    for i, (ent, off, blob) in enumerate(placed):
        eoff = 8 + i * ENTRY_STRIDE
        path_bytes = ent.path.encode("ascii")
        if len(path_bytes) >= PATH_LEN:
            raise PatchError(f"path too long: {ent.path}")
        out[eoff : eoff + len(path_bytes)] = path_bytes
        flag = ent.usize_field & 0xFF000000
        if flag == 0:
            flag = USIZE_FLAG
        usize_field = flag | (ent.usize & 0x00FFFFFF)
        struct.pack_into(
            "<IIII",
            out,
            eoff + PATH_LEN,
            ent.hash,
            len(blob),
            usize_field,
            off,
        )
        out[off : off + len(blob)] = blob
    return bytes(out)


# ---------------------------------------------------------------------------
# Game discovery / backups / settings
# ---------------------------------------------------------------------------

def candidate_game_dirs() -> List[Path]:
    home = Path.home()
    cands: List[Path] = []
    env = os.environ.get("TGAAC_DIR")
    if env:
        cands.append(Path(env))

    here = script_dir()
    cands.extend([here, here.parent, Path.cwd(), Path.cwd().parent])

    steam_roots = [
        home / ".steam/steam/steamapps/common/TGAAC",
        home / ".local/share/Steam/steamapps/common/TGAAC",
        home / ".var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/common/TGAAC",
        home / "Library/Application Support/Steam/steamapps/common/TGAAC",
    ]
    for drive in "CDEFGH":
        steam_roots.append(Path(f"{drive}:/Program Files (x86)/Steam/steamapps/common/TGAAC"))
        steam_roots.append(Path(f"{drive}:/Program Files/Steam/steamapps/common/TGAAC"))
        steam_roots.append(Path(f"{drive}:/SteamLibrary/steamapps/common/TGAAC"))
    cands.extend(steam_roots)

    vdfs = [
        home / ".steam/steam/steamapps/libraryfolders.vdf",
        home / ".local/share/Steam/steamapps/libraryfolders.vdf",
        home / "Library/Application Support/Steam/steamapps/libraryfolders.vdf",
    ]
    for drive in "CDEFGH":
        vdfs.append(Path(f"{drive}:/Program Files (x86)/Steam/steamapps/libraryfolders.vdf"))
    for vdf in vdfs:
        if not vdf.is_file():
            continue
        text = vdf.read_text(errors="ignore")
        for line in text.splitlines():
            line = line.strip()
            if '"path"' not in line:
                continue
            parts = line.split('"')
            if len(parts) >= 4:
                cands.append(Path(parts[3].replace("\\\\", "\\")) / "steamapps/common/TGAAC")

    out: List[Path] = []
    seen = set()
    for p in cands:
        try:
            rp = p.resolve()
        except OSError:
            rp = p
        if rp in seen:
            continue
        seen.add(rp)
        out.append(p)
    return out


def find_game_dir(explicit: Optional[Path]) -> Path:
    if explicit:
        p = explicit.expanduser().resolve()
        if not looks_like_tgaac(p):
            raise PatchError(f"--game-dir does not look like TGAAC: {p}")
        return p

    here = script_dir()
    for cand in (here, here.parent):
        if looks_like_tgaac(cand):
            return cand.resolve()

    for c in candidate_game_dirs():
        if looks_like_tgaac(c):
            return c.resolve()
    raise PatchError(
        "Could not find TGAAC.\n"
        "Drop this patcher folder into your TGAAC install (next to TGAAC.exe) and run again,\n"
        "or pass --game-dir pointing at that folder."
    )


def target_arcs(game_dir: Path) -> List[Path]:
    archive = game_dir / "nativeDX11x64" / "archive"
    patterns = [
        "BB/snd_script_eng.arc",
        "BB/snd_script_jpn.arc",
        "GO/snd_script_eng.arc",
        "GO/snd_script_jpn.arc",
    ]
    found = [archive / rel for rel in patterns if (archive / rel).is_file()]
    if not found:
        raise PatchError(f"no snd_script_*.arc under {archive}")
    return found


def backup_dir_for(game_dir: Path) -> Path:
    return game_dir / "nativeDX11x64" / "archive" / ".tgaac_text_beep_backup"


def settings_path(bdir: Path) -> Path:
    return bdir / SETTINGS_FILE


def load_settings(bdir: Path) -> Dict[str, float]:
    path = settings_path(bdir)
    settings = dict(DEFAULT_SETTINGS)
    if not path.is_file():
        return settings
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return settings
    for key in CHANNELS:
        if key in data:
            try:
                val = float(data[key])
            except (TypeError, ValueError):
                continue
            if 0.0 <= val <= 100.0:
                settings[key] = val
    # migrate legacy single-volume key
    if "volume" in data and "beep" not in data:
        try:
            val = float(data["volume"])
            if 0.0 <= val <= 100.0:
                settings["beep"] = val
        except (TypeError, ValueError):
            pass
    return settings


def save_settings(bdir: Path, settings: Dict[str, float], dry_run: bool) -> None:
    if dry_run:
        return
    bdir.mkdir(parents=True, exist_ok=True)
    payload = {k: float(settings[k]) for k in CHANNELS}
    settings_path(bdir).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def ensure_backups(arcs: Sequence[Path], bdir: Path, dry_run: bool) -> None:
    if dry_run:
        return
    bdir.mkdir(parents=True, exist_ok=True)
    for arc in arcs:
        dest = bdir / f"{arc.parent.name}__{arc.name}"
        if dest.is_file():
            continue
        dest.write_bytes(arc.read_bytes())
        print(f"backup: {arc.name} ({arc.parent.name})")


def restore_from_backup(arcs: Sequence[Path], bdir: Path, dry_run: bool) -> None:
    for arc in arcs:
        src = bdir / f"{arc.parent.name}__{arc.name}"
        if not src.is_file():
            raise PatchError(f"missing backup: {src}")
        print(f"restore: {arc.parent.name}/{arc.name}")
        if not dry_run:
            arc.write_bytes(src.read_bytes())


def channel_for_sample(name: str) -> Optional[str]:
    for channel, names in CHANNELS.items():
        if name in names:
            return channel
    return None


def patch_one_from_backup(
    arc: Path,
    backup: Path,
    settings: Dict[str, float],
    dry_run: bool,
) -> None:
    header8, _version, entries = read_arc(backup)
    hits = {channel: 0 for channel in CHANNELS}
    for ent in entries:
        channel = channel_for_sample(ent.name)
        if channel is None:
            continue
        vol = settings[channel]
        raw = zlib.decompress(ent.blob)
        patched = adjust_wave_volume(raw, vol)
        new_blob = zlib.compress(patched, 9)
        flag = ent.usize_field & 0xFF000000 or USIZE_FLAG
        ent.blob = new_blob
        ent.csize = len(new_blob)
        ent.usize_field = flag | (len(patched) & 0x00FFFFFF)
        hits[channel] += 1
        print(
            f"  {arc.parent.name}/{arc.name}: {ent.name} "
            f"[{channel}] -> {vol:g}%"
        )

    for channel, names in CHANNELS.items():
        expected = len(names)
        if hits[channel] != expected:
            raise PatchError(
                f"{backup}: expected {expected} {channel} sample(s) "
                f"{names}, found {hits[channel]}"
            )

    # All default → write exact backup bytes
    if all(settings[c] >= 100.0 for c in CHANNELS):
        if dry_run:
            print(f"  dry-run: would restore original {arc.name}")
            return
        arc.write_bytes(backup.read_bytes())
        print(f"  restored original {arc.parent.name}/{arc.name}")
        return

    out = build_arc(header8, entries)
    if dry_run:
        print(f"  dry-run: would write {len(out)} bytes")
        return
    arc.write_bytes(out)
    print(f"  wrote {arc.parent.name}/{arc.name}")


def _parse_pct(raw: str) -> float:
    val = float(str(raw).rstrip("%"))
    if not (0.0 <= val <= 100.0):
        raise ValueError("out of range")
    return val


def prompt_pct(label: str, current: float) -> float:
    while True:
        try:
            raw = input(f"{label} [{current:g}]: ").strip().lower()
        except EOFError:
            raise PatchError("no volume provided") from None
        if raw == "":
            return current
        if raw in ("restore", "r", "undo"):
            return 100.0
        try:
            return _parse_pct(raw)
        except ValueError:
            print("  enter a number 0-100 (blank keeps current)")


def prompt_settings(current: Dict[str, float]) -> Tuple[str, Dict[str, float]]:
    print()
    print("TGAAC text SFX volumes (independent)")
    print("  beep     = typewriter beeps while text appears")
    print("  advance  = click when advancing the text box")
    print("  100 = default, 0 = mute, blank = keep current")
    print("  'restore' at any prompt = reset both to 100")
    print()
    try:
        first = input(
            f"Text beep % [{current['beep']:g}] (or 'restore' / Enter): "
        ).strip().lower()
    except EOFError:
        raise PatchError("no volume provided") from None
    if first in ("restore", "r", "undo"):
        return "restore", dict(DEFAULT_SETTINGS)
    settings = dict(current)
    if first != "":
        try:
            settings["beep"] = _parse_pct(first)
        except ValueError as exc:
            raise PatchError("invalid beep volume") from exc
    settings["advance"] = prompt_pct(
        f"Text advance click %", settings["advance"]
    )
    return "apply", settings


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Set TGAAC text-beep and text-advance volumes independently (0–100%)."
    )
    p.add_argument(
        "volume_positional",
        nargs="?",
        default=None,
        help="legacy: set beep volume 0-100, or 'restore'",
    )
    p.add_argument(
        "--beep",
        type=float,
        metavar="PCT",
        help="typewriter beep volume 0-100",
    )
    p.add_argument(
        "--advance",
        type=float,
        metavar="PCT",
        help="text-box advance click volume 0-100",
    )
    p.add_argument(
        "--volume",
        type=float,
        metavar="PCT",
        help="alias for --beep (backward compatible)",
    )
    p.add_argument("--restore", action="store_true", help="restore originals from backup")
    p.add_argument("--game-dir", type=Path, default=None, help="TGAAC install folder")
    p.add_argument("--dry-run", action="store_true", help="do not write files")
    p.add_argument(
        "--show",
        action="store_true",
        help="print saved volumes and exit",
    )
    return p.parse_args(argv)


def resolve_settings(
    args: argparse.Namespace, current: Dict[str, float]
) -> Tuple[str, Dict[str, float]]:
    """Return ('restore'|'apply'|'show', settings)."""
    if args.show:
        return "show", current
    if args.restore:
        return "restore", dict(DEFAULT_SETTINGS)

    updates: Dict[str, float] = {}
    if args.beep is not None:
        updates["beep"] = float(args.beep)
    if args.volume is not None:
        updates["beep"] = float(args.volume)
    if args.advance is not None:
        updates["advance"] = float(args.advance)

    pos = args.volume_positional
    if pos is not None:
        if str(pos).lower() in ("restore", "r", "undo"):
            return "restore", dict(DEFAULT_SETTINGS)
        try:
            updates["beep"] = _parse_pct(str(pos))
        except ValueError as exc:
            raise PatchError(f"invalid volume: {pos!r}") from exc

    if updates:
        settings = dict(current)
        for key, val in updates.items():
            if not (0.0 <= val <= 100.0):
                raise PatchError(f"{key} volume must be between 0 and 100")
            settings[key] = val
        return "apply", settings

    # Interactive
    return prompt_settings(current)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        game = find_game_dir(args.game_dir)
        arcs = target_arcs(game)
        bdir = backup_dir_for(game)
        current = load_settings(bdir)
        action, settings = resolve_settings(args, current)

        print(f"game: {game}")
        print(f"arcs: {len(arcs)} file(s)")
        print(
            "volumes: "
            + ", ".join(
                f"{CHANNEL_LABELS[k]}={settings[k]:g}%"
                if action != "show"
                else f"{CHANNEL_LABELS[k]}={current[k]:g}%"
                for k in CHANNELS
            )
        )

        if action == "show":
            return 0

        if action == "restore" or all(settings[c] >= 100.0 for c in CHANNELS):
            ensure_backups(arcs, bdir, args.dry_run)
            restore_from_backup(arcs, bdir, args.dry_run)
            save_settings(bdir, dict(DEFAULT_SETTINGS), args.dry_run)
            print("done (restored to defaults / 100%).")
            return 0

        ensure_backups(arcs, bdir, args.dry_run)
        for arc in arcs:
            bak = bdir / f"{arc.parent.name}__{arc.name}"
            if args.dry_run and not bak.is_file():
                bak = arc
            elif not bak.is_file():
                raise PatchError(f"missing backup {bak}")
            print(f"patching {arc.parent.name}/{arc.name} ...")
            patch_one_from_backup(arc, bak, settings, args.dry_run)
        save_settings(bdir, settings, args.dry_run)
        print(
            "done ("
            + ", ".join(f"{k}={settings[k]:g}%" for k in CHANNELS)
            + ")."
        )
        return 0
    except PatchError as exc:
        eprint(f"error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
