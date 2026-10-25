#!/usr/bin/env python3
"""
Phoenix Wright: Ace Attorney Trilogy dialogue-blip volume.

The trilogy does not use TGAAC's Capcom .arc archives. Sound effects are
Rijndael-wrapped UnityFS bundles of FMOD FSB5 Vorbis clips. MessageSystem
plays only three blips while text scrolls:

  message_se == 0  ->  se003  (male / default)
  message_se == 1  ->  se004  (female)
  message_se == 2  ->  se01a  (typewriter)

There is no separate text-advance sample.

Volumes re-apply from a one-time backup. 100 = original file. 0 = silence
(no ffmpeg). 1-99 scales the waveform and needs ffmpeg on PATH.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

# FMOD Vorbis setup packet for setup id 0xD6E0BBD4 (shared by the three blips).
_CODEBOOK = zlib.decompress(base64.b64decode(
    "eNqVV39Q01cSfyhCApFGCDTU2EmQFL6R3BkEa7hzDqJU8oWofCEooVxrICoEqCSEO+dKByVwgBAx"
    "RA5D7PAjQRMJVQpUuGlrxQQEjIAStLaj1goq3vWutrU3/eNuvwFbrr0Z577z8ma/b9/bfbv72f1u"
    "VpS+pZLnqTHRlgwvREEICVLYjvKJBilCdITeDMcCGveKMYuhLfJgsyGJpBzra5oNNQ5mTp3A+Wxix"
    "+QGI+SNyiOpuo5Zcb5LuI8ZoVO1CvO2bzrF9q1NvSOkXvz2lZyizt5OZZEL41JWZq5AaBmKT+JUMg"
    "hykldzqpgw/ZmlGuGcMqn8eKdbD/tFj7ArUqIfmhu3xz083aGLexTZOyHy5/dO4SmC6Yyc7g99st9"
    "Wu4RzpsWJ6rGDDXcR+YTm0kUUUnw11tmsAlELZrFROZiJth1jiM8xxs6xrkyG7/g6KjUodnJDYlq6"
    "RAqPJntXqWKmVDNTWpbZXJl1vizzfGXWjcrsp5V7mFWL4/uy20/J4TGd7YVa1wqb7mHtYS+1fyFs"
    "X66t6lqGckmXsKn6MEzfIe7cm9+d19K//0x/4VhP1FgPzbMFecEW8mnNM3b+YuzNbFI8f8TvH+Ghe"
    "PDlcDFruDg8kQgfVkX5ejw8giCm8USUQxWzTR0zrP4tjG0lWy8bUq58k/LCsyBQPDeIF7AcxazL4A2"
    "Cf00Vu0u9eUYtmQFXSJ/7HPI4FgzhnNzblF9O2dCwx+MW0tHMNsoW2oIm2FDd9iXbOGF8ckUYYLzf"
    "amW0XPukJr0lYsDa3OKJYIEr9B6EERs94Wg9MWFUu8Q0o2WBOhjY4mu3TgEVOmcKcIbugX15U0Zf68"
    "3dcDZzwjh7eoABVI2hJaJvIL1lKSysvze5PhHeBarm0xblADUbqH/lmv5+hXrX9Ev4xMNV99xgOk8e"
    "ZpfpfOQMTien8eWSowGNrYIRzPxyve413FqxkwiNsJQcXoQU0tKJH6EMkwfKCyg262t5o5Hvj0ePRZ"
    "FT15Arbv7sEH0LTQAojooFFNf3zb6r7hYmKS19btk6i4HAMctCRkFQ2bkNCT6hC0KbVaPYKciKpYH7"
    "R/jVVWsml4yr/2SlBnJhTEbz0zZslqZLd5UWZv5Fc+uDyuwbmtszZbdn6t94sernMPoxcxAkjdZjiE"
    "FeJxg2VWwXUQ/9V+YUM4aPsS4fC0/uCZdMRV35OmbHk5jJoMTUGElacPZksOZaiCJtY/a1WMU1qWK6"
    "VHGzX5H1QVlm/2LCLI4ZzZLMIVMkTKi7l6T3/ilzWiN1X2zSrRXrwzP1rxxs2ldjtJ5496G13e9nmb"
    "O/9lRz7anq2rlqXWRNU16N0TbQXjDaPT/43PFj5mxThcOAzElUhS/JnAsC1hbIpp4oyZMFGzdPgkNL"
    "El/878y50EBL9tSRVII/TcROE3xp+ubnJs10jORaDDj2OEKhCK2FIGvptaoGUdHm3RTBbPiKNqFP2y"
    "Wm9hR9A024MqykISFi83m9cIj25A4RGbw1paKe+6qOvfJi5+vi+5soEDxvlIpQuWBEcImpcokvt251"
    "CagnDSPCCEvjlBjjNzE3YNzOwJx7po4p8WWzgZlce9IcmFNjh0PIF37+bRMNwV7xDITkNMIPqzQQLm"
    "y2gRgV3GcRuPCUKc0lpKzRjgp8TlbQMQsrzYUNs7TjCfdNFRMJkQCOC4CeC6LImNxERI9Adw6EX22M"
    "SWZwk4MSrzIUM0GSmeMxV2JiU9OlY0HS6XTprRCJtJ8rCZJIvkmXBiVKg6XXmiTSvsKrMYqb6dLPQ6"
    "TT/YpbIe/satLc3iDJhFc3cDUzTWVvuAuzmxdFSRgeURulM/2xqSXSVKkiM12aWarIfCrd5S5LBm6a"
    "5GawVNovvfltobSp7G6JNHuX4uZTaWbIO1kzlXe/K7vLJCXPTGuAu8et2POB5nZknjEvv/20zRhps1"
    "lt/YW2bntW+wNbu220Z5+tu2u0570z3QXzwO0+beuJstmizvR0/WCLmu8/bRu0j/acbek+M9//lf9Q"
    "1PzgAVt395mexyR30D7vLJ4fXP92JzbWeebRoHVwsGh+sHi8v5DVYXv0EW/s4tnRnq/mB3/dq+GkSj"
    "WfG7Lv7QI7Ct/4w7tZTyt7Cn/zsf2HURAw9b3w6lusATj2ftFqWHM+Wfe7PZt0ln1GuKnN3mI7M99Tt"
    "G6oa16UKi3LPq64/Wp25otFt1/VZc3Ut9seDfLGPgJFgs+cb7H+up6VfWsjME722P3LckaeUq8qbzmL"
    "f4i7952m4z0adfgoYMOLxEbQaHwbZ92y8k1eyIczx0ij8xzsEjrxiG1OF/hw1NtxB8uwE8/nGK7znOx"
    "0nXjE1BiI78cMU4Rvm2UnrmwzuAnluc7r8r+xzSF4Ht8wJcu3Oq/L6lbl0KPnzLkuMdXSSzJA1FyrOU"
    "CEW8yMZJyfMQ5A7phKSLKaA9PE1j4QZTGHJOOCfkZWkcDNghPmwCwx5mSkFfKdxrVONoi6TCr36Ljfb"
    "ABRJyr0OG4/rifGTY2kqAodLsb69XgK3ArHz1USsgKB20QUxMIJEKXHC/hOWVZKn4Yu8/fcyt6Xocy3"
    "O0E518JMxs/1hSiLBLMvAYNUbnWEZOlAeZoyttOdTzKyCje7jWrc7r5O1AMjp/DDaeOfvnpmuTyf73T"
    "L7aRy3rnjelA++6msTggMEKUn6uBEVsFAZ1M+MIzEkb7ZT9UFsd9dl3WROpLhC6E+OvBtBlSd8uUovp"
    "yqaCVLCJm2CdWES5xHV40LeVTRuDDCqkoRYZh0PIHC7XMJMczhFlK4lpBkHt+RocQwsIIP1dOTtj6S"
    "GoeX38pMKtoKr0421B2fUAuzYoJpZuTQwyxMiIuFkQO+ZaoDRLzQHFdCJKbdifOwSjou5lqgHPuxoCA"
    "WTBh2s1qf1ZE3aXKaoIpdkh7NW6VNwSOsh8Cjdg1AweIYl+Xbe2/EU+yV7uhkLkBhr/1Ss2wdQo/hQ"
    "o89dYSLGnxRPLMD9Ar30eXjwgesGKiMLG0Az2mqCBBRguEa8K0aF8JEFwED+r22CpgshimSQeAP2bC"
    "GWUpIhoHwQ4h3AOr62dRc9eFjrVAzl6GDZM3Ehb5thtcwJ9ugJ0AdmGRV0cB3jgySYZA9ZgM0CmJL6"
    "RBAp2wLbnfsVnZzLG55V+wMgLhv1qjEgaG8MoDQZyt80dnlqxM3RjCpvEUjytngxjpBFUNeK5gzbaF"
    "gjmbocTqZZNcBH1my9agTeJoQZzO5xlpoR3Q/NSZLWpT/YYQVPkKrMuRkL76astCVvxboec0pWGzSm"
    "+VL2vX/Y8pS2gFySycU/7GfL/q37+qMbZuwl/yjSBvpAdDoDTXDjX3WaKuwB2YthKdtCy6M5AJKMAz"
    "gAxltkOEn1ATB41qayNJxXYbzQaIv1+Im8kF2HMXSe53UciMhCbO4ZUf4kHI4vMrrYqsI2OK4Ie8Sm"
    "KcIyE9mThckkEwJN1TysT63vK4P/A8Vwi0/EuuW+aM7RQdQedLZ4qrj5vcvTt7xuIkDLYPI423yjwE"
    "BsWgl0cLZigOqSIxwtHXP1rQNP67R4+YWoAWAmltYM+wUeaDlWcPWABXpobhAURcauAVuIFAGDyLJN"
    "UMgedZDESQid3oo3ANVD0XlaBfXMM7CWZIBEF1OVuG1D8I7RsMKYu5eXL5z/wiOymkIFd/In8fcI2y"
    "HSduUrG1Q0eW/WkXUCredUySFOpjTBoGFkUYoH5jkdak7TubggqEuQwYeeezwlKqrr3TcC77bFLSez"
    "tlwKN6LwRwBRVpvDLWevTAheN3b+8vAaD+a37BWPZW3HNG1I7Rj1btpgUG2Q+3yOLT79TdHfMtp9fW"
    "9R/wfRF9Ykf2Zhq1le3OqHV6MhvKKoKI/frFyx/lPqHGJloBlnj7JC72MkH4lOyzMKNQFHH2hgX5sl"
    "T6wMcjg4aJl5S+g8vAV1dXVe3UdQ/eWh2/N1ZovfenNRc8eCmWh4fL20P8BBK7vOA=="
))

# message_se value -> clip stem under StreamingAssets/Sound/se/
CHANNELS: Dict[str, Tuple[str, ...]] = {
    "male": ("se003",),
    "female": ("se004",),
    "typewriter": ("se01a",),
}
CHANNEL_LABELS = {
    "male": "male / default blip (se003)",
    "female": "female blip (se004)",
    "typewriter": "typewriter blip (se01a)",
}
DEFAULT_SETTINGS: Dict[str, float] = {name: 100.0 for name in CHANNELS}
SETTINGS_FILE = "settings.json"
GAME_FOLDER = "Phoenix Wright Ace Attorney Trilogy"
_RATES = [4000, 8000, 11000, 11025, 16000, 22050, 24000, 32000, 44100, 48000, 96000]

_SBOX = bytes.fromhex(
    "637c777bf26b6fc53001672bfed7ab76ca82c97dfa5947f0add4a2af9ca472c0"
    "b7fd9326363ff7cc34a5e5f171d8311504c723c31896059a071280e2eb27b275"
    "09832c1a1b6e5aa0523bd6b329e32f8453d100ed20fcb15b6acbbe394a4c58cf"
    "d0efaafb434d338545f9027f503c9fa851a3408f929d38f5bcb6da2110fff3d2"
    "cd0c13ec5f974417c4a77e3d645d197360814fdc222a908846eeb814de5e0bdb"
    "e0323a0a4906245cc2d3ac629195e479e7c8376d8dd54ea96c56f4ea657aae08b"
    "a78252e1ca6b4c6e8dd741f4bbd8b8a703eb5664803f60e613557b986c11d9ee"
    "1f8981169d98e949b1e87e9ce5528df8ca1890dbfe6426841992d0fb054bb16"
)
_INV_SBOX = bytearray(256)
for _i, _v in enumerate(_SBOX):
    _INV_SBOX[_v] = _i
_INV_SBOX = bytes(_INV_SBOX)
_RCON = (0x00, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1B, 0x36)


class PatchError(Exception):
    pass


def eprint(*args: object) -> None:
    print(*args, file=sys.stderr)


def script_dir() -> Path:
    return Path(__file__).resolve().parent


def _walk_up(start: Path, levels: int) -> List[Path]:
    out = [start]
    cur = start
    for _ in range(levels):
        if cur.parent == cur:
            break
        cur = cur.parent
        out.append(cur)
    return out


# ---------------------------------------------------------------------------
# AES-128-CBC (game wrapper: PBKDF2-HMAC-SHA1, password u8DurGE2)
# ---------------------------------------------------------------------------

def _xtime(a: int) -> int:
    return ((a << 1) ^ 0x1B) & 0xFF if a & 0x80 else (a << 1) & 0xFF


def _mul(a: int, b: int) -> int:
    p = 0
    for _ in range(8):
        if b & 1:
            p ^= a
        hi = a & 0x80
        a = (a << 1) & 0xFF
        if hi:
            a ^= 0x1B
        b >>= 1
    return p


def _expand_key(key: bytes) -> List[int]:
    words = [list(key[i : i + 4]) for i in range(0, 16, 4)]
    rcon_i = 1
    while len(words) < 44:
        temp = words[-1][:]
        if len(words) % 4 == 0:
            temp = temp[1:] + temp[:1]
            temp = [_SBOX[b] for b in temp]
            temp[0] ^= _RCON[rcon_i]
            rcon_i += 1
        prev = words[-4]
        words.append([prev[j] ^ temp[j] for j in range(4)])
    return [b for word in words for b in word]


def _add_round(state: List[int], w: Sequence[int], rnd: int) -> None:
    off = rnd * 16
    for i in range(16):
        state[i] ^= w[off + i]


def _mix_columns(state: List[int]) -> None:
    for c in range(4):
        i = c * 4
        a, b, c1, d = state[i : i + 4]
        state[i] = _xtime(a) ^ _xtime(b) ^ b ^ c1 ^ d
        state[i + 1] = a ^ _xtime(b) ^ _xtime(c1) ^ c1 ^ d
        state[i + 2] = a ^ b ^ _xtime(c1) ^ _xtime(d) ^ d
        state[i + 3] = _xtime(a) ^ a ^ b ^ c1 ^ _xtime(d)


def _inv_mix_columns(state: List[int]) -> None:
    for c in range(4):
        i = c * 4
        a, b, c1, d = state[i : i + 4]
        state[i] = _mul(a, 14) ^ _mul(b, 11) ^ _mul(c1, 13) ^ _mul(d, 9)
        state[i + 1] = _mul(a, 9) ^ _mul(b, 14) ^ _mul(c1, 11) ^ _mul(d, 13)
        state[i + 2] = _mul(a, 13) ^ _mul(b, 9) ^ _mul(c1, 14) ^ _mul(d, 11)
        state[i + 3] = _mul(a, 11) ^ _mul(b, 13) ^ _mul(c1, 9) ^ _mul(d, 14)


def _encrypt_block(block: bytes, w: Sequence[int]) -> bytes:
    s = list(block)
    _add_round(s, w, 0)
    for rnd in range(1, 10):
        for i in range(16):
            s[i] = _SBOX[s[i]]
        s[1], s[5], s[9], s[13] = s[5], s[9], s[13], s[1]
        s[2], s[6], s[10], s[14] = s[10], s[14], s[2], s[6]
        s[3], s[7], s[11], s[15] = s[15], s[3], s[7], s[11]
        _mix_columns(s)
        _add_round(s, w, rnd)
    for i in range(16):
        s[i] = _SBOX[s[i]]
    s[1], s[5], s[9], s[13] = s[5], s[9], s[13], s[1]
    s[2], s[6], s[10], s[14] = s[10], s[14], s[2], s[6]
    s[3], s[7], s[11], s[15] = s[15], s[3], s[7], s[11]
    _add_round(s, w, 10)
    return bytes(s)


def _decrypt_block(block: bytes, w: Sequence[int]) -> bytes:
    s = list(block)
    _add_round(s, w, 10)
    s[1], s[5], s[9], s[13] = s[13], s[1], s[5], s[9]
    s[2], s[6], s[10], s[14] = s[10], s[14], s[2], s[6]
    s[3], s[7], s[11], s[15] = s[7], s[11], s[15], s[3]
    for i in range(16):
        s[i] = _INV_SBOX[s[i]]
    for rnd in range(9, 0, -1):
        _add_round(s, w, rnd)
        _inv_mix_columns(s)
        s[1], s[5], s[9], s[13] = s[13], s[1], s[5], s[9]
        s[2], s[6], s[10], s[14] = s[10], s[14], s[2], s[6]
        s[3], s[7], s[11], s[15] = s[7], s[11], s[15], s[3]
        for i in range(16):
            s[i] = _INV_SBOX[s[i]]
    _add_round(s, w, 0)
    return bytes(s)


def _xor16(a: bytes, b: bytes) -> bytes:
    return bytes(x ^ y for x, y in zip(a, b))


def aes_cbc_encrypt(data: bytes, key: bytes, iv: bytes) -> bytes:
    pad = 16 - (len(data) % 16)
    raw = data + bytes([pad]) * pad
    w = _expand_key(key)
    out = bytearray()
    prev = iv
    for i in range(0, len(raw), 16):
        prev = _encrypt_block(_xor16(raw[i : i + 16], prev), w)
        out += prev
    return bytes(out)


def aes_cbc_decrypt(data: bytes, key: bytes, iv: bytes) -> bytes:
    if len(data) == 0 or len(data) % 16:
        raise PatchError("encrypted bundle length is not a multiple of 16")
    w = _expand_key(key)
    out = bytearray()
    prev = iv
    for i in range(0, len(data), 16):
        block = data[i : i + 16]
        plain = _xor16(_decrypt_block(block, w), prev)
        out += plain
        prev = block
    pad = out[-1]
    if pad < 1 or pad > 16 or out[-pad:] != bytes([pad]) * pad:
        raise PatchError("bad Rijndael padding (not a trilogy bundle?)")
    return bytes(out[:-pad])


def game_key_iv() -> Tuple[bytes, bytes]:
    # Rfc2898DeriveBytes defaults: HMAC-SHA1, 1000 iterations.
    material = hashlib.pbkdf2_hmac("sha1", b"u8DurGE2", b"6BBGizHE", 1000, 32)
    return material[:16], material[16:]


# ---------------------------------------------------------------------------
# UnityFS (uncompressed block info + uncompressed storage on write)
# ---------------------------------------------------------------------------

def _lz4_decompress(src: bytes, usize: int) -> bytes:
    dst = bytearray()
    i = 0
    n = len(src)
    while len(dst) < usize:
        if i >= n:
            raise PatchError("truncated LZ4 block")
        token = src[i]
        i += 1
        lit = token >> 4
        if lit == 15:
            while True:
                b = src[i]
                i += 1
                lit += b
                if b != 255:
                    break
        if lit:
            dst += src[i : i + lit]
            i += lit
        if len(dst) >= usize:
            break
        offset = src[i] | (src[i + 1] << 8)
        i += 2
        if offset == 0 or offset > len(dst):
            raise PatchError("bad LZ4 offset")
        match = (token & 0xF) + 4
        if (token & 0xF) == 15:
            while True:
                b = src[i]
                i += 1
                match += b
                if b != 255:
                    break
        start = len(dst) - offset
        for k in range(match):
            dst.append(dst[start + k])
    return bytes(dst[:usize])


def _cstring(data: bytes, offset: int) -> Tuple[str, int]:
    end = data.index(b"\x00", offset)
    return data[offset:end].decode("utf-8", "replace"), end + 1


def parse_unityfs(data: bytes) -> dict:
    if data[:7] != b"UnityFS":
        raise PatchError("decrypted file is not UnityFS")
    o = 8
    version = struct.unpack_from(">I", data, o)[0]
    o += 4
    player, o = _cstring(data, o)
    engine, o = _cstring(data, o)
    o += 8  # file size
    cib = struct.unpack_from(">I", data, o)[0]
    o += 4
    uib = struct.unpack_from(">I", data, o)[0]
    o += 4
    flags = struct.unpack_from(">I", data, o)[0]
    o += 4
    comp = flags & 0x3F
    info = data[o : o + cib]
    if comp == 0:
        raw = info
    elif comp in (2, 3):
        raw = _lz4_decompress(info, uib)
    else:
        raise PatchError(f"unsupported UnityFS compression {comp}")
    p = 16  # data hash
    block_count = struct.unpack_from(">I", raw, p)[0]
    p += 4
    blocks = []
    for _ in range(block_count):
        usize, csize, bflags = struct.unpack_from(">IIH", raw, p)
        p += 10
        blocks.append((usize, csize, bflags))
    node_count = struct.unpack_from(">I", raw, p)[0]
    p += 4
    nodes_meta = []
    for _ in range(node_count):
        off, size = struct.unpack_from(">QQ", raw, p)
        p += 16
        nflags = struct.unpack_from(">I", raw, p)[0]
        p += 4
        name, p = _cstring(raw, p)
        nodes_meta.append((off, size, nflags, name))
    storage = bytearray()
    bo = o + cib
    for usize, csize, bflags in blocks:
        chunk = data[bo : bo + csize]
        bo += csize
        bcomp = bflags & 0x3F
        if bcomp == 0:
            storage += chunk
        elif bcomp in (2, 3):
            storage += _lz4_decompress(chunk, usize)
        else:
            raise PatchError(f"unsupported block compression {bcomp}")
    nodes = []
    for off, size, nflags, name in nodes_meta:
        nodes.append((name, nflags, bytes(storage[off : off + size])))
    return {"version": version, "player": player, "engine": engine, "nodes": nodes}


def build_unityfs(player: str, engine: str, nodes: Sequence[Tuple[str, int, bytes]]) -> bytes:
    storage = bytearray()
    directory = []
    for name, nflags, blob in nodes:
        directory.append((len(storage), len(blob), nflags, name))
        storage += blob
    info = bytearray(16)  # hash unused by the player
    info += struct.pack(">I", 1)
    info += struct.pack(">IIH", len(storage), len(storage), 0)
    info += struct.pack(">I", len(directory))
    for off, size, nflags, name in directory:
        info += struct.pack(">QQI", off, size, nflags)
        info += name.encode("utf-8") + b"\x00"
    flags = 0x40  # blocks + directory combined, uncompressed
    prefix = bytearray()
    prefix += b"UnityFS\x00"
    prefix += struct.pack(">I", 6)
    prefix += player.encode("utf-8") + b"\x00"
    prefix += engine.encode("utf-8") + b"\x00"
    # file size filled after we know the total
    head_rest = struct.pack(">III", len(info), len(info), flags)
    total = len(prefix) + 8 + len(head_rest) + len(info) + len(storage)
    return bytes(prefix) + struct.pack(">Q", total) + head_rest + bytes(info) + bytes(storage)


# ---------------------------------------------------------------------------
# FSB5 Vorbis -> PCM16
# ---------------------------------------------------------------------------

def _ogg_crc(data: bytes) -> int:
    crc = 0
    for byte in data:
        crc ^= byte << 24
        for _ in range(8):
            if crc & 0x80000000:
                crc = ((crc << 1) ^ 0x04C11DB7) & 0xFFFFFFFF
            else:
                crc = (crc << 1) & 0xFFFFFFFF
    return crc


def _ogg_page(packets: Sequence[bytes], seq: int, bos: bool = False, eos: bool = False, granule: int = 0) -> bytes:
    segs = bytearray()
    body = bytearray()
    for pkt in packets:
        n = len(pkt)
        body += pkt
        while n >= 255:
            segs.append(255)
            n -= 255
        segs.append(n)
    header = bytearray(27)
    header[0:4] = b"OggS"
    flags = (2 if bos else 0) | (4 if eos else 0)
    header[5] = flags
    struct.pack_into("<Q", header, 6, granule)
    struct.pack_into("<I", header, 14, 1)
    struct.pack_into("<I", header, 18, seq)
    header[26] = len(segs)
    page = bytes(header) + bytes(segs) + bytes(body)
    crc = _ogg_crc(page)
    return page[:22] + struct.pack("<I", crc) + page[26:]


def fsb_meta(blob: bytes) -> dict:
    if blob[:4] != b"FSB5":
        raise PatchError("sound resource is not FSB5")
    version, _ns, sample_header, name_table, data_size, codec = struct.unpack_from("<6I", blob, 4)
    if version != 1:
        raise PatchError(f"FSB5 version {version} is not supported")
    base = 0x3C
    mode = struct.unpack_from("<Q", blob, base)[0]
    samples = (mode >> 34) & 0x3FFFFFFF
    channels = {0: 1, 1: 2}.get((mode >> 5) & 3)
    if channels is None:
        raise PatchError("unsupported channel count in FSB5")
    rate_i = (mode >> 1) & 0xF
    if rate_i >= len(_RATES):
        raise PatchError("unsupported sample rate in FSB5")
    data_off = base + sample_header + name_table
    return {
        "codec": codec,
        "samples": samples,
        "channels": channels,
        "rate": _RATES[rate_i],
        "data": blob[data_off : data_off + data_size],
    }


def _vorbis_packets(data: bytes) -> List[bytes]:
    packets: List[bytes] = []
    i = 0
    while i + 2 <= len(data):
        size = struct.unpack_from("<H", data, i)[0]
        i += 2
        if size == 0 or size == 0xFFFF:
            break
        if i + size > len(data):
            raise PatchError("truncated FSB Vorbis packet")
        packets.append(data[i : i + size])
        i += size
    if not packets:
        raise PatchError("FSB Vorbis stream has no packets")
    return packets


def _ident_packet(channels: int, rate: int) -> bytes:
    # FMOD uses blocksize nibbles (2048 << 4) | 256. ffmpeg accepts this.
    buf = bytearray(0x1E)
    buf[0] = 1
    buf[1:7] = b"vorbis"
    buf[0x0B] = channels
    struct.pack_into("<I", buf, 0x0C, rate)
    buf[0x1C] = (11 << 4) | 8
    buf[0x1D] = 1
    return bytes(buf)


def _comment_packet() -> bytes:
    buf = bytearray(0x19)
    buf[0] = 3
    buf[1:7] = b"vorbis"
    struct.pack_into("<I", buf, 7, 9)
    buf[0x0B:0x14] = b"vgmstream"
    buf[0x18] = 1
    return bytes(buf)


def _wrap_ogg(meta: dict) -> bytes:
    if meta["codec"] != 0x0F:
        raise PatchError(f"expected Vorbis FSB (codec 15), got {meta['codec']}")
    packets = _vorbis_packets(meta["data"])
    pages = [
        _ogg_page([_ident_packet(meta["channels"], meta["rate"])], 0, bos=True),
        _ogg_page([_comment_packet()], 1),
        _ogg_page([_CODEBOOK], 2),
    ]
    for i, pkt in enumerate(packets):
        last = i == len(packets) - 1
        pages.append(_ogg_page([pkt], 3 + i, eos=last, granule=meta["samples"] if last else 0))
    return b"".join(pages)


def decode_pcm(meta: dict) -> bytes:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise PatchError(
            "ffmpeg is required to set a volume other than 0 or 100.\n"
            "Install ffmpeg and retry, or pass 0 to mute without it."
        )
    ogg = _wrap_ogg(meta)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "blip.ogg"
        src.write_bytes(ogg)
        proc = subprocess.run(
            [ffmpeg, "-hide_banner", "-loglevel", "error", "-i", str(src),
             "-f", "s16le", "-ac", str(meta["channels"]), "-ar", str(meta["rate"]), "pipe:1"],
            capture_output=True,
        )
    if proc.returncode != 0 or not proc.stdout:
        tail = proc.stderr.decode("utf-8", "replace").strip().splitlines()
        detail = tail[-1] if tail else "no output"
        raise PatchError(f"ffmpeg could not decode the blip ({detail})")
    if len(proc.stdout) % (2 * meta["channels"]):
        raise PatchError("ffmpeg returned a partial PCM frame")
    return proc.stdout


def scale_pcm(pcm: bytes, volume_pct: float) -> bytes:
    if volume_pct <= 0:
        return b"\x00" * len(pcm)
    if volume_pct >= 100:
        return pcm
    gain = volume_pct / 100.0
    samples = struct.unpack("<" + str(len(pcm) // 2) + "h", pcm)
    scaled = []
    for sample in samples:
        value = int(round(sample * gain))
        if value < -32768:
            value = -32768
        elif value > 32767:
            value = 32767
        scaled.append(value)
    return struct.pack("<" + str(len(scaled)) + "h", *scaled)


def build_pcm_fsb(pcm: bytes, rate: int, channels: int) -> bytes:
    if channels not in (1, 2):
        raise PatchError("PCM rebuild only supports mono or stereo")
    if len(pcm) % (2 * channels):
        raise PatchError("PCM length is not a whole frame")
    samples = len(pcm) // (2 * channels)
    try:
        rate_i = _RATES.index(rate)
    except ValueError as exc:
        raise PatchError(f"cannot store sample rate {rate}") from exc
    mode = (samples & 0x3FFFFFFF) << 34
    mode |= (0 if channels == 1 else 1) << 5
    mode |= rate_i << 1
    header = bytearray()
    header += b"FSB5"
    header += struct.pack("<6I", 1, 1, 8, 0, len(pcm), 2)  # PCM16
    header += struct.pack("<I", 1)  # field at 0x1C, same as the stock banks
    header += struct.pack("<I", 0)  # flags: little-endian PCM16
    header += b"\x00" * 16
    header += b"\x00" * 8
    header += struct.pack("<Q", mode)
    if len(header) != 68:
        raise PatchError("internal FSB header size mismatch")
    return bytes(header) + pcm


def patch_audioclip(assets: bytes, old_fsb_len: int, new_fsb_len: int, new_samples: int, rate: int) -> bytes:
    data = bytearray(assets)
    needle = struct.pack("<Q", old_fsb_len)
    idx = data.rfind(needle)
    if idx < 0 or idx + 12 > len(data):
        raise PatchError("AudioClip resource size field not found")
    struct.pack_into("<Q", data, idx, new_fsb_len)
    fmt = struct.unpack_from("<I", data, idx + 8)[0]
    if fmt not in (0, 1):
        raise PatchError(f"unexpected AudioClip compression format {fmt}")
    struct.pack_into("<I", data, idx + 8, 0)  # PCM
    freq = struct.pack("<I", rate)
    pos = 0
    while True:
        j = data.find(freq, pos)
        if j < 0 or j + 12 > len(data):
            raise PatchError("AudioClip length field not found")
        bits = struct.unpack_from("<I", data, j + 4)[0]
        length = struct.unpack_from("<f", data, j + 8)[0]
        if bits == 16 and 0 < length < 30:
            struct.pack_into("<f", data, j + 8, new_samples / float(rate))
            return bytes(data)
        pos = j + 4


def rebuild_bundle(bundle: dict, volume_pct: float) -> bytes:
    nodes = list(bundle["nodes"])
    resource_i = next(i for i, (name, _f, blob) in enumerate(nodes) if name.endswith(".resource") or blob[:4] == b"FSB5")
    assets_i = next(i for i, (name, _f, blob) in enumerate(nodes) if b"AudioClip" in blob or b"m_Frequency" in blob)
    name, flags, fsb = nodes[resource_i]
    meta = fsb_meta(fsb)
    if volume_pct <= 0:
        pcm = b"\x00" * (meta["samples"] * meta["channels"] * 2)
    else:
        pcm = scale_pcm(decode_pcm(meta), volume_pct)
    new_fsb = build_pcm_fsb(pcm, meta["rate"], meta["channels"])
    new_samples = len(pcm) // (2 * meta["channels"])
    aname, aflags, assets = nodes[assets_i]
    nodes[assets_i] = (aname, aflags, patch_audioclip(assets, len(fsb), len(new_fsb), new_samples, meta["rate"]))
    nodes[resource_i] = (name, flags, new_fsb)
    return build_unityfs(bundle["player"], bundle["engine"], nodes)


# ---------------------------------------------------------------------------
# Game discovery / settings
# ---------------------------------------------------------------------------

def looks_like_pwaat(path: Path) -> bool:
    return (path / "PWAAT.exe").is_file() or (path / "PWAAT_Data" / "StreamingAssets" / "Sound").is_dir()


def candidate_game_dirs() -> List[Path]:
    home = Path.home()
    cands: List[Path] = []
    env = os.environ.get("PWAAT_DIR")
    if env:
        cands.append(Path(env))
    cands.extend(_walk_up(script_dir(), 4))
    cands.extend(_walk_up(Path.cwd(), 4))
    roots = [
        home / ".steam/steam/steamapps/common" / GAME_FOLDER,
        home / ".local/share/Steam/steamapps/common" / GAME_FOLDER,
        home / ".var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/common" / GAME_FOLDER,
        home / "Library/Application Support/Steam/steamapps/common" / GAME_FOLDER,
    ]
    for drive in "CDEFGH":
        roots.append(Path(f"{drive}:/Program Files (x86)/Steam/steamapps/common") / GAME_FOLDER)
        roots.append(Path(f"{drive}:/Program Files/Steam/steamapps/common") / GAME_FOLDER)
        roots.append(Path(f"{drive}:/SteamLibrary/steamapps/common") / GAME_FOLDER)
    cands.extend(roots)
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
            if '"path"' not in line:
                continue
            parts = line.split('"')
            if len(parts) >= 4:
                cands.append(Path(parts[3].replace("\\\\", "\\")) / "steamapps/common" / GAME_FOLDER)
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
        if not looks_like_pwaat(p):
            raise PatchError(f"--game-dir does not look like the Phoenix Wright trilogy: {p}")
        return p
    for cand in _walk_up(script_dir(), 4):
        if looks_like_pwaat(cand):
            return cand.resolve()
    for cand in candidate_game_dirs():
        if looks_like_pwaat(cand):
            return cand.resolve()
    raise PatchError(
        "Could not find Phoenix Wright: Ace Attorney Trilogy.\n"
        "Drop this repo into the install (next to PWAAT.exe) and run again,\n"
        "or pass --game-dir pointing at that folder."
    )


def target_files(game_dir: Path) -> List[Tuple[str, Path]]:
    root = game_dir / "PWAAT_Data" / "StreamingAssets" / "Sound" / "se"
    found: List[Tuple[str, Path]] = []
    for channel, names in CHANNELS.items():
        for name in names:
            hits = sorted(root.rglob(name + ".unity3d")) if root.is_dir() else []
            if not hits:
                raise PatchError(f"missing {name}.unity3d under {root}")
            for hit in hits:
                found.append((channel, hit))
    return found


def backup_dir_for(game_dir: Path) -> Path:
    return game_dir / "PWAAT_Data" / "StreamingAssets" / "Sound" / ".pwaat_text_beep_backup"


def backup_name(path: Path, sound_root: Path) -> str:
    rel = path.relative_to(sound_root)
    return str(rel).replace("\\", "/").replace("/", "__")


def load_settings(bdir: Path) -> Dict[str, float]:
    settings = dict(DEFAULT_SETTINGS)
    path = bdir / SETTINGS_FILE
    if not path.is_file():
        return settings
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return settings
    for key in CHANNELS:
        if key not in data:
            continue
        try:
            val = float(data[key])
        except (TypeError, ValueError):
            continue
        if 0.0 <= val <= 100.0:
            settings[key] = val
    return settings


def save_settings(bdir: Path, settings: Dict[str, float], dry_run: bool) -> None:
    if dry_run:
        return
    bdir.mkdir(parents=True, exist_ok=True)
    payload = {k: float(settings[k]) for k in CHANNELS}
    (bdir / SETTINGS_FILE).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def ensure_backups(files: Sequence[Tuple[str, Path]], bdir: Path, sound_root: Path, dry_run: bool) -> None:
    if dry_run:
        return
    bdir.mkdir(parents=True, exist_ok=True)
    for _channel, path in files:
        dest = bdir / backup_name(path, sound_root)
        if dest.is_file():
            continue
        dest.write_bytes(path.read_bytes())
        print(f"backup: {path.relative_to(sound_root)}")


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
    print("Phoenix Wright trilogy dialogue blips (independent)")
    print("  male        = default text blip")
    print("  female      = higher text blip")
    print("  typewriter  = typewriter text blip")
    print("  100 = original, 0 = mute, blank = keep current")
    print("  'restore' at the first prompt = reset all to 100")
    print()
    try:
        first = input(f"Male blip % [{current['male']:g}] (or 'restore' / Enter): ").strip().lower()
    except EOFError:
        raise PatchError("no volume provided") from None
    if first in ("restore", "r", "undo"):
        return "restore", dict(DEFAULT_SETTINGS)
    settings = dict(current)
    if first != "":
        try:
            settings["male"] = _parse_pct(first)
        except ValueError as exc:
            raise PatchError("invalid male volume") from exc
    settings["female"] = prompt_pct("Female blip %", settings["female"])
    settings["typewriter"] = prompt_pct("Typewriter blip %", settings["typewriter"])
    return "apply", settings


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Set Phoenix Wright trilogy dialogue-blip volumes (0–100%).")
    p.add_argument("positional", nargs="?", default=None, help="'restore' to undo")
    p.add_argument("--male", type=float, metavar="PCT", help="default/male blip volume 0-100")
    p.add_argument("--female", type=float, metavar="PCT", help="female blip volume 0-100")
    p.add_argument("--typewriter", type=float, metavar="PCT", help="typewriter blip volume 0-100")
    p.add_argument("--restore", action="store_true", help="restore originals from backup")
    p.add_argument("--game-dir", type=Path, default=None, help="trilogy install folder")
    p.add_argument("--dry-run", action="store_true", help="do not write files")
    p.add_argument("--show", action="store_true", help="print saved volumes and exit")
    return p.parse_args(argv)


def resolve_settings(args: argparse.Namespace, current: Dict[str, float]) -> Tuple[str, Dict[str, float]]:
    if args.show:
        return "show", current
    if args.restore:
        return "restore", dict(DEFAULT_SETTINGS)
    updates: Dict[str, float] = {}
    for key in CHANNELS:
        val = getattr(args, key)
        if val is not None:
            updates[key] = float(val)
    if args.positional is not None:
        if str(args.positional).lower() in ("restore", "r", "undo"):
            return "restore", dict(DEFAULT_SETTINGS)
        raise PatchError(
            f"unknown argument {args.positional!r}. "
            "Use --male/--female/--typewriter, or 'restore'."
        )
    if updates:
        settings = dict(current)
        for key, val in updates.items():
            if not (0.0 <= val <= 100.0):
                raise PatchError(f"{key} volume must be between 0 and 100")
            settings[key] = val
        return "apply", settings
    return prompt_settings(current)


def apply_one(path: Path, backup: Path, volume: float, dry_run: bool) -> None:
    if volume >= 100.0:
        print(f"  restore original {path.name}")
        if not dry_run:
            path.write_bytes(backup.read_bytes())
        return
    key, iv = game_key_iv()
    plain = aes_cbc_decrypt(backup.read_bytes(), key, iv)
    bundle = parse_unityfs(plain)
    rebuilt = rebuild_bundle(bundle, volume)
    # round-trip check: the player must be able to read what we wrote
    parse_unityfs(rebuilt)
    enc = aes_cbc_encrypt(rebuilt, key, iv)
    print(f"  {path.parent.name}/{path.name} -> {volume:g}%")
    if dry_run:
        return
    path.write_bytes(enc)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        game = find_game_dir(args.game_dir)
        files = target_files(game)
        sound_root = game / "PWAAT_Data" / "StreamingAssets" / "Sound"
        bdir = backup_dir_for(game)
        current = load_settings(bdir)
        action, settings = resolve_settings(args, current)
        shown = current if action == "show" else settings
        print(f"game: {game}")
        print(f"clips: {len(files)}")
        print("volumes: " + ", ".join(f"{CHANNEL_LABELS[k]}={shown[k]:g}%" for k in CHANNELS))
        if action == "show":
            return 0
        if action == "restore":
            settings = dict(DEFAULT_SETTINGS)
        ensure_backups(files, bdir, sound_root, args.dry_run)
        for channel, path in files:
            bak = bdir / backup_name(path, sound_root)
            if args.dry_run and not bak.is_file():
                bak = path
            elif not bak.is_file():
                raise PatchError(f"missing backup {bak}")
            apply_one(path, bak, settings[channel], args.dry_run)
        save_settings(bdir, settings, args.dry_run)
        print("done (" + ", ".join(f"{k}={settings[k]:g}%" for k in CHANNELS) + ").")
        return 0
    except PatchError as exc:
        eprint(f"error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
