#!/usr/bin/env python3
"""Build renderbolt-1.0.6-1.fc44.noarch.rpm without rpmbuild.

Fedora 44 / rpm 4.20 layout: zstd cpio, SHA256HEADER tag 273 in the
signature header (not legacy 1018), HEADERI18NTABLE, payload digest alt.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import stat
import struct
import time
from pathlib import Path

import zstandard

ROOT = Path("/workspace")
STAGE = ROOT / "packaging" / "rpm-root"
OUT = ROOT / "public" / "downloads" / "renderbolt-1.0.6-1.fc44.noarch.rpm"

NAME = "renderbolt"
VERSION = "1.0.6"
RELEASE = "1.fc44"
ARCH = "noarch"
NVR = f"{NAME}-{VERSION}-{RELEASE}"

NULL, CHAR, INT8, INT16, INT32, INT64, STRING, BIN, STRING_ARRAY, I18NSTRING = range(10)
ALIGN = {NULL: 1, CHAR: 1, INT8: 1, INT16: 2, INT32: 4, INT64: 8, STRING: 1, BIN: 1, STRING_ARRAY: 1, I18NSTRING: 1}

RPMSENSE_LESS = 1 << 1
RPMSENSE_GREATER = 1 << 2
RPMSENSE_EQUAL = 1 << 3
RPMSENSE_RPMLIB = 1 << 24

HEADER_MAGIC = b"\x8e\xad\xe8\x01\x00\x00\x00\x00"
HEADER_SIGNATURES = 62
HEADER_IMMUTABLE = 63
HEADERI18NTABLE = 100

# Fedora 44 writes these tag numbers into the signature header (not 1010/1018).
SIG_SHA1HEADER = 269
SIG_SHA256HEADER = 273
SIG_SIZE = 1000
SIG_MD5 = 1004
SIG_PAYLOADSIZE = 1007

TAG = {
    "NAME": 1000,
    "VERSION": 1001,
    "RELEASE": 1002,
    "SUMMARY": 1004,
    "DESCRIPTION": 1005,
    "BUILDTIME": 1006,
    "BUILDHOST": 1007,
    "SIZE": 1009,
    "LICENSE": 1014,
    "PACKAGER": 1015,
    "GROUP": 1016,
    "URL": 1020,
    "OS": 1021,
    "ARCH": 1022,
    "FILESIZES": 1028,
    "FILEMODES": 1030,
    "FILERDEVS": 1033,
    "FILEMTIMES": 1034,
    "FILEDIGESTS": 1035,
    "FILELINKTOS": 1036,
    "FILEFLAGS": 1037,
    "FILEUSERNAME": 1039,
    "FILEGROUPNAME": 1040,
    "SOURCERPM": 1044,
    "FILEVERIFYFLAGS": 1045,
    "ARCHIVESIZE": 1046,
    "PROVIDENAME": 1047,
    "REQUIREFLAGS": 1048,
    "REQUIRENAME": 1049,
    "REQUIREVERSION": 1050,
    "RPMVERSION": 1064,
    "CHANGELOGTIME": 1080,
    "CHANGELOGNAME": 1081,
    "CHANGELOGTEXT": 1082,
    "FILEDEVICES": 1095,
    "FILEINODES": 1096,
    "FILELANGS": 1097,
    "PROVIDEFLAGS": 1112,
    "PROVIDEVERSION": 1113,
    "DIRINDEXES": 1116,
    "BASENAMES": 1117,
    "DIRNAMES": 1118,
    "PAYLOADFORMAT": 1124,
    "PAYLOADCOMPRESSOR": 1125,
    "PAYLOADFLAGS": 1126,
    "FILEDIGESTALGO": 5011,
    "ENCODING": 5062,
    "PAYLOADDIGEST": 5092,
    "PAYLOADDIGESTALGO": 5093,
    "PAYLOADDIGESTALT": 5097,
}

FILEFLAG_DOC = 1 << 1
FILEFLAG_LICENSE = 1 << 7
VERIFY_ALL = 0xFFFFFFFF
SHA256_ALGO = 8

WRAPPER = """#!/bin/sh
export RENDERBOLT_SHARE=/opt/renderbolt/share
exec python3 /opt/renderbolt/renderbolt "$@"
"""

DESKTOP = """[Desktop Entry]
Type=Application
Name=Renderbolt
Comment=Cinematic audio visualizer
Exec=/usr/bin/renderbolt
Icon=renderbolt
Terminal=false
Categories=AudioVideo;Audio;Video;
StartupNotify=true
"""

README = """Renderbolt 1.0.6
Cinematic audio visualizer
Copyright 2026 JMHBM
License: Creative Commons Attribution 4.0 International
https://creativecommons.org/licenses/by/4.0/

Fedora Silverblue 44
  rpm-ostree install renderbolt-1.0.6-1.fc44.noarch.rpm
  systemctl reboot

Fedora Workstation
  sudo dnf install ./renderbolt-1.0.6-1.fc44.noarch.rpm
"""


def write(path: Path, text: str, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    os.chmod(path, mode)


def draw_icon(dest: Path) -> None:
    from PIL import Image, ImageDraw

    dest.parent.mkdir(parents=True, exist_ok=True)
    im = Image.new("RGBA", (256, 256), (10, 10, 11, 255))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([8, 8, 247, 247], radius=48, fill=(10, 10, 11, 255))
    d.polygon(
        [(156, 28), (66, 132), (118, 132), (84, 228), (196, 116), (140, 116)],
        fill=(232, 238, 242, 255),
    )
    im.save(dest, "PNG")


def align(buf: bytearray, alignment: int) -> None:
    while len(buf) % alignment:
        buf.append(0)


def pack_value(typ: int, value) -> bytes:
    if typ == INT16:
        vals = value if isinstance(value, (list, tuple)) else [value]
        return struct.pack("!" + "H" * len(vals), *[int(v) & 0xFFFF for v in vals])
    if typ == INT32:
        vals = value if isinstance(value, (list, tuple)) else [value]
        return struct.pack("!" + "I" * len(vals), *[int(v) & 0xFFFFFFFF for v in vals])
    if typ == INT64:
        vals = value if isinstance(value, (list, tuple)) else [value]
        return struct.pack("!" + "Q" * len(vals), *[int(v) for v in vals])
    if typ == STRING:
        return value.encode("utf-8") + b"\x00"
    if typ in (STRING_ARRAY, I18NSTRING):
        return b"".join(s.encode("utf-8") + b"\x00" for s in value)
    if typ == BIN:
        return bytes(value)
    raise ValueError(f"unsupported type {typ}")


def value_count(typ: int, value) -> int:
    if typ in (INT16, INT32, INT64):
        return len(value) if isinstance(value, (list, tuple)) else 1
    if typ in (STRING_ARRAY, I18NSTRING):
        return len(value)
    if typ == BIN:
        return len(value)
    return 1


def build_header(tags: list[tuple[int, int, object]], region_tag: int) -> bytes:
    # Keep tags sorted (region is inserted first). Required by headerCheck.
    tags = sorted(tags, key=lambda t: t[0])
    store = bytearray()
    index: list[tuple[int, int, int, int]] = []
    for tag, typ, value in tags:
        align(store, ALIGN[typ])
        offset = len(store)
        packed = pack_value(typ, value)
        store += packed
        index.append((tag, typ, offset, value_count(typ, value)))

    nindex = len(index) + 1
    trailer = struct.pack("!IIiI", region_tag, BIN, -(nindex * 16), 16)
    region_offset = len(store)
    store += trailer
    index = [(region_tag, BIN, region_offset, 16)] + index

    out = HEADER_MAGIC + struct.pack("!II", len(index), len(store))
    for tag, typ, offset, count in index:
        out += struct.pack("!IIiI", tag, typ, offset, count)
    out += bytes(store)
    return out


def cpio_entry(name: str, data: bytes, mode: int, mtime: int, inode: int) -> bytes:
    name_b = name.encode("utf-8") + b"\x00"
    fields = (
        f"{inode:08x}{mode:08x}{0:08x}{0:08x}{1:08x}{mtime:08x}"
        f"{len(data):08x}{0:08x}{0:08x}{0:08x}{0:08x}"
        f"{len(name_b):08x}{0:08x}"
    )
    hdr = b"070701" + fields.encode("ascii")
    chunk = hdr + name_b
    if len(chunk) % 4:
        chunk += b"\x00" * (4 - len(chunk) % 4)
    chunk += data
    if len(chunk) % 4:
        chunk += b"\x00" * (4 - len(chunk) % 4)
    return chunk


def build_cpio(files: list[tuple[str, bytes, int, int]]) -> bytes:
    parts = []
    for i, (name, data, mode, mtime) in enumerate(files, start=1):
        parts.append(cpio_entry(name, data, mode, mtime, i))
    parts.append(cpio_entry("TRAILER!!!", b"", 0, 0, 0))
    return b"".join(parts)


def lead(name: str) -> bytes:
    n = name.encode("ascii")[:65].ljust(66, b"\x00")
    # Fedora 44 noarch packages use archnum 0 in the lead (the lead is ignored
    # by modern rpm; the header ARCH tag is what matters).
    return struct.pack(
        "!4sBBHH66sHH16s",
        b"\xed\xab\xee\xdb",
        3,
        0,
        0,
        0,
        n,
        1,
        5,
        b"\x00" * 16,
    )


def stage_files() -> Path:
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)

    write(STAGE / "usr/bin/renderbolt", WRAPPER, 0o755)
    dest = STAGE / "opt/renderbolt/renderbolt"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "desktop/renderbolt", dest)
    os.chmod(dest, 0o755)
    for name in ("engine3d.py", "studio_ui.py", "preview3d.py"):
        shutil.copy2(ROOT / "desktop" / name, STAGE / "opt/renderbolt" / name)
    vendor = STAGE / "opt/renderbolt/vendor"
    vendor.mkdir(parents=True, exist_ok=True)
    import subprocess
    import sys

    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "--target", str(vendor), "--upgrade", "moderngl", "-q"]
    )
    for junk in vendor.rglob("__pycache__"):
        shutil.rmtree(junk, ignore_errors=True)
    share = STAGE / "opt/renderbolt/share"
    share.mkdir(parents=True)
    shutil.copy2(ROOT / "public/samples/stage.jpg", share / "stage.jpg")
    write(STAGE / "usr/share/applications/renderbolt.desktop", DESKTOP)
    draw_icon(STAGE / "usr/share/icons/hicolor/256x256/apps/renderbolt.png")
    write(STAGE / "usr/share/licenses/renderbolt/LICENSE", (ROOT / "LICENSE").read_text())
    write(STAGE / "usr/share/doc/renderbolt/README", README)
    return STAGE


def collect_files(root: Path) -> list[dict]:
    records = []
    mtime = int(time.time())
    for path in sorted(root.rglob("*")):
        if path.is_dir():
            continue
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        rel = "/" + str(path.relative_to(root)).replace("\\", "/")
        data = path.read_bytes()
        mode = 0o100755 if path.stat().st_mode & stat.S_IXUSR else 0o100644
        flags = 0
        if "/licenses/" in rel:
            flags = FILEFLAG_LICENSE | FILEFLAG_DOC
        elif "/doc/" in rel:
            flags = FILEFLAG_DOC
        records.append(
            {
                "path": rel,
                "data": data,
                "mode": mode,
                "mtime": mtime,
                "digest": hashlib.sha256(data).hexdigest(),
                "flags": flags,
            }
        )
    return records


def zstd_compress(data: bytes) -> bytes:
    cctx = zstandard.ZstdCompressor(level=19)
    return cctx.compress(data)


def main() -> None:
    root = stage_files()
    records = collect_files(root)
    mtime = records[0]["mtime"] if records else int(time.time())

    dirs: list[str] = []
    dir_indexes = []
    basenames = []
    for rec in records:
        dirname = rec["path"].rsplit("/", 1)[0] + "/"
        if dirname not in dirs:
            dirs.append(dirname)
        dir_indexes.append(dirs.index(dirname))
        basenames.append(rec["path"].rsplit("/", 1)[1])

    cpio_files = [
        ("." + rec["path"], rec["data"], rec["mode"], rec["mtime"]) for rec in records
    ]
    payload_raw = build_cpio(cpio_files)
    payload = zstd_compress(payload_raw)

    requires = [
        ("rpmlib(CompressedFileNames)", "3.0.4-1", RPMSENSE_LESS | RPMSENSE_EQUAL | RPMSENSE_RPMLIB),
        ("rpmlib(FileDigests)", "4.6.0-1", RPMSENSE_LESS | RPMSENSE_EQUAL | RPMSENSE_RPMLIB),
        ("rpmlib(PayloadFilesHavePrefix)", "4.0-1", RPMSENSE_LESS | RPMSENSE_EQUAL | RPMSENSE_RPMLIB),
        ("rpmlib(PayloadIsZstd)", "5.4.18-1", RPMSENSE_LESS | RPMSENSE_EQUAL | RPMSENSE_RPMLIB),
        ("python3", "3.10", RPMSENSE_GREATER | RPMSENSE_EQUAL),
        ("python3-tkinter", "", 0),
        ("python3-pillow", "", 0),
        ("python3-pillow-tk", "", 0),
        ("python3-numpy", "", 0),
        ("/usr/bin/ffmpeg", "", 0),
        ("dejavu-sans-fonts", "", 0),
    ]

    summary = "Cinematic audio visualizer"
    description = (
        "Renderbolt turns a song, cover art, and titles into an MP4 "
        "music visualizer with 2D and 3D styles, VA-API encoding on AMD "
        "GPUs, and CPU fallback.\n\n"
        "Licensed under Creative Commons Attribution 4.0 International."
    )

    tags: list[tuple[int, int, object]] = [
        (HEADERI18NTABLE, STRING_ARRAY, ["C"]),
        (TAG["NAME"], STRING, NAME),
        (TAG["VERSION"], STRING, VERSION),
        (TAG["RELEASE"], STRING, RELEASE),
        (TAG["SUMMARY"], I18NSTRING, [summary]),
        (TAG["DESCRIPTION"], I18NSTRING, [description]),
        (TAG["BUILDTIME"], INT32, mtime),
        (TAG["BUILDHOST"], STRING, "renderbolt"),
        (TAG["SIZE"], INT32, sum(len(r["data"]) for r in records)),
        (TAG["LICENSE"], STRING, "CC-BY-4.0"),
        (TAG["PACKAGER"], STRING, "JMHBM"),
        (TAG["GROUP"], STRING, "Applications/Multimedia"),
        (TAG["URL"], STRING, "https://creativecommons.org/licenses/by/4.0/"),
        (TAG["OS"], STRING, "linux"),
        (TAG["ARCH"], STRING, ARCH),
        (TAG["FILESIZES"], INT32, [len(r["data"]) for r in records]),
        (TAG["FILEMODES"], INT16, [r["mode"] for r in records]),
        (TAG["FILERDEVS"], INT16, [0] * len(records)),
        (TAG["FILEMTIMES"], INT32, [r["mtime"] for r in records]),
        (TAG["FILEDIGESTS"], STRING_ARRAY, [r["digest"] for r in records]),
        (TAG["FILELINKTOS"], STRING_ARRAY, [""] * len(records)),
        (TAG["FILEFLAGS"], INT32, [r["flags"] for r in records]),
        (TAG["FILEUSERNAME"], STRING_ARRAY, ["root"] * len(records)),
        (TAG["FILEGROUPNAME"], STRING_ARRAY, ["root"] * len(records)),
        (TAG["SOURCERPM"], STRING, f"{NVR}.src.rpm"),
        (TAG["FILEVERIFYFLAGS"], INT32, [VERIFY_ALL] * len(records)),
        (TAG["ARCHIVESIZE"], INT32, len(payload_raw)),
        (TAG["PROVIDENAME"], STRING_ARRAY, [NAME]),
        (TAG["REQUIREFLAGS"], INT32, [r[2] for r in requires]),
        (TAG["REQUIRENAME"], STRING_ARRAY, [r[0] for r in requires]),
        (TAG["REQUIREVERSION"], STRING_ARRAY, [r[1] for r in requires]),
        (TAG["RPMVERSION"], STRING, "4.20.1"),
        (TAG["CHANGELOGTIME"], INT32, [mtime]),
        (TAG["CHANGELOGNAME"], STRING_ARRAY, ["JMHBM <jmhbm@users.noreply.github.com> - 1.0.6-1"]),
        (TAG["CHANGELOGTEXT"], STRING_ARRAY, ["Release 1.0.6: 3D engine, VA-API, studio UI, formats."]),
        (TAG["FILEDEVICES"], INT32, [1] * len(records)),
        (TAG["FILEINODES"], INT32, list(range(1, len(records) + 1))),
        (TAG["FILELANGS"], STRING_ARRAY, [""] * len(records)),
        (TAG["PROVIDEFLAGS"], INT32, [RPMSENSE_EQUAL]),
        (TAG["PROVIDEVERSION"], STRING_ARRAY, [f"{VERSION}-{RELEASE}"]),
        (TAG["DIRINDEXES"], INT32, dir_indexes),
        (TAG["BASENAMES"], STRING_ARRAY, basenames),
        (TAG["DIRNAMES"], STRING_ARRAY, dirs),
        (TAG["PAYLOADFORMAT"], STRING, "cpio"),
        (TAG["PAYLOADCOMPRESSOR"], STRING, "zstd"),
        (TAG["PAYLOADFLAGS"], STRING, "19"),
        (TAG["FILEDIGESTALGO"], INT32, SHA256_ALGO),
        (TAG["ENCODING"], STRING, "utf-8"),
        (TAG["PAYLOADDIGEST"], STRING_ARRAY, [hashlib.sha256(payload).hexdigest()]),
        (TAG["PAYLOADDIGESTALGO"], INT32, SHA256_ALGO),
        (TAG["PAYLOADDIGESTALT"], STRING_ARRAY, [hashlib.sha256(payload_raw).hexdigest()]),
    ]

    header = build_header(tags, HEADER_IMMUTABLE)
    # Sorted: 269, 273, 1000, 1004, 1007 — matches Fedora 44 unsigned-digest layout.
    sig_tags: list[tuple[int, int, object]] = [
        (SIG_SHA1HEADER, STRING, hashlib.sha1(header).hexdigest()),
        (SIG_SHA256HEADER, STRING, hashlib.sha256(header).hexdigest()),
        (SIG_SIZE, INT32, len(header) + len(payload)),
        (SIG_MD5, BIN, hashlib.md5(header + payload).digest()),
        (SIG_PAYLOADSIZE, INT32, len(payload_raw)),
    ]
    sig = build_header(sig_tags, HEADER_SIGNATURES)
    if len(sig) % 8:
        sig += b"\x00" * (8 - len(sig) % 8)

    rpm = lead(NVR) + sig + header + payload
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(rpm)

    verify(rpm, records)
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes, {len(records)} files)")


def verify(rpm: bytes, records: list[dict]) -> None:
    assert rpm[:4] == b"\xed\xab\xee\xdb", "bad lead magic"
    rest = rpm[96:]
    assert rest[:8] == HEADER_MAGIC, "bad signature magic"
    nindex, hsize = struct.unpack("!II", rest[8:16])
    sig_len = 16 + nindex * 16 + hsize
    sig_len_padded = (sig_len + 7) & ~7
    idx = rest[16 : 16 + nindex * 16]
    store = rest[16 + nindex * 16 : 16 + nindex * 16 + hsize]
    sig_tags = [struct.unpack("!IIiI", idx[i * 16 : (i + 1) * 16])[0] for i in range(nindex)]
    assert SIG_SHA256HEADER in sig_tags, f"missing SHA256HEADER, have {sig_tags}"
    assert SIG_SHA1HEADER in sig_tags, f"missing SHA1HEADER, have {sig_tags}"
    body = rest[sig_len_padded:]
    assert body[:8] == HEADER_MAGIC, "bad header magic"
    n2, h2 = struct.unpack("!II", body[8:16])
    hdr_len = 16 + n2 * 16 + h2
    header = body[:hdr_len]
    payload = body[hdr_len:]
    # Confirm stored SHA256 matches full header bytes.
    sha_off = None
    for i in range(nindex):
        tag, typ, off, cnt = struct.unpack("!IIiI", idx[i * 16 : (i + 1) * 16])
        if tag == SIG_SHA256HEADER:
            stored = store[off:].split(b"\x00", 1)[0].decode()
            actual = hashlib.sha256(header).hexdigest()
            assert stored == actual, f"sha256 mismatch {stored} != {actual}"
            sha_off = off
    assert sha_off is not None
    raw = zstandard.ZstdDecompressor().decompress(payload)
    for rec in records:
        assert rec["path"].encode() in raw, f"missing {rec['path']}"
    print("rpm verify ok", "sig tags", sig_tags)


if __name__ == "__main__":
    main()
