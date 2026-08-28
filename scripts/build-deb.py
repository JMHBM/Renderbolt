#!/usr/bin/env python3
"""Build renderbolt_1.0.8_all.deb without requiring dpkg-deb.

dpkg does not mkdir -p while unpacking: every parent directory must be a
real tar member in data.tar.gz, listed before the files it contains.
"""

from __future__ import annotations

import io
import os
import shutil
import stat
import subprocess
import sys
import tarfile
import time
from pathlib import Path

ROOT = Path("/workspace")
STAGE = ROOT / "packaging" / "deb-root"
OUT = ROOT / "public" / "downloads" / "renderbolt_1.0.8_all.deb"

# Directories that must exist as tar members (relative to /).
DATA_DIRS = [
    "opt",
    "opt/renderbolt",
    "opt/renderbolt/share",
    "opt/renderbolt/share/looks",
    "opt/renderbolt/vendor",
    "usr",
    "usr/bin",
    "usr/share",
    "usr/share/applications",
    "usr/share/metainfo",
    "usr/share/doc",
    "usr/share/doc/renderbolt",
    "usr/share/icons",
    "usr/share/icons/hicolor",
    "usr/share/icons/hicolor/256x256",
    "usr/share/icons/hicolor/256x256/apps",
]

CONTROL = """Package: renderbolt
Version: 1.0.8
Section: sound
Priority: optional
Architecture: all
Depends: python3 (>= 3.10), python3-tk, python3-pil, python3-pil.imagetk, python3-numpy, ffmpeg, fonts-dejavu-core
Recommends: mesa-va-drivers
Maintainer: JMHBM <jmhbm@users.noreply.github.com>
Homepage: https://github.com/JMHBM/Renderbolt
Description: Renderbolt cinematic audio visualizer
 Renderbolt turns a song, cover art, and titles into an MP4
 music visualizer with a ModernGL 3D engine (ribbon, bars, halo, terrain).
 VA-API (h264_vaapi) is used on AMD GPUs when available, with CPU fallback.
 Licensed under Creative Commons Attribution 4.0 International.
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

METAINFO = """<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>com.jmhbm.renderbolt</id>
  <name>Renderbolt</name>
  <summary>Offline cinematic audio visualizer</summary>
  <metadata_license>CC-BY-4.0</metadata_license>
  <project_license>CC-BY-4.0</project_license>
  <developer_name>JMHBM</developer_name>
  <url type="homepage">https://github.com/JMHBM/Renderbolt</url>
  <description>
    <p>
      Renderbolt turns a song and a still into a cinematic MP4 on your machine.
      No upload, no account. 2D and 3D visualizers, beat-reactive cover bounce,
      VA-API encode on AMD GPUs with CPU fallback.
    </p>
  </description>
  <launchable type="desktop-id">renderbolt.desktop</launchable>
  <provides>
    <binary>renderbolt</binary>
  </provides>
  <releases>
    <release version="1.0.8" date="2026-08-28"/>
  </releases>
  <categories>
    <category>AudioVideo</category>
    <category>Audio</category>
    <category>Video</category>
  </categories>
</component>
"""

COPYRIGHT = """Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: renderbolt
Upstream-Contact: JMHBM
Source: https://github.com/JMHBM/Renderbolt


Files: *
Copyright: 2026 JMHBM
License: CC-BY-4.0

License: CC-BY-4.0
 This work is licensed under the Creative Commons Attribution 4.0
 International License. To view a copy of this license, visit
 https://creativecommons.org/licenses/by/4.0/
"""

WRAPPER = """#!/bin/sh
export RENDERBOLT_SHARE=/opt/renderbolt/share
export RENDERBOLT_LOOKS=/opt/renderbolt/share/looks
exec python3 /opt/renderbolt/renderbolt "$@"
"""

POSTINST = """#!/bin/sh
set -e
chmod 755 /usr/bin/renderbolt /opt/renderbolt/renderbolt || true
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database -q || true
fi
exit 0
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
    bolt = [
        (156, 28),
        (66, 132),
        (118, 132),
        (84, 228),
        (196, 116),
        (140, 116),
    ]
    d.polygon(bolt, fill=(232, 238, 242, 255))
    im.save(dest, "PNG")


def _dir_info(name: str, mtime: int) -> tarfile.TarInfo:
    info = tarfile.TarInfo(name=name)
    info.type = tarfile.DIRTYPE
    info.mode = 0o755
    info.uid = 0
    info.gid = 0
    info.uname = "root"
    info.gname = "root"
    info.mtime = mtime
    return info


def tar_dir(src: Path, gzip: bool, include_dot: bool = True) -> bytes:
    """Pack src into a tar whose members are rooted at ./ and include dirs."""
    buf = io.BytesIO()
    mode = "w:gz" if gzip else "w"
    mtime = int(time.time())
    with tarfile.open(fileobj=buf, mode=mode, format=tarfile.GNU_FORMAT) as tar:
        if include_dot:
            tar.addfile(_dir_info("./", mtime))

        dirs: set[str] = set()
        files: list[Path] = []
        for path in src.rglob("*"):
            if "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            rel = path.relative_to(src)
            if path.is_dir():
                parts = rel.parts
                for i in range(len(parts)):
                    dirs.add("/".join(parts[: i + 1]))
            else:
                files.append(path)
                if rel.parent != Path("."):
                    parts = rel.parent.parts
                    for i in range(len(parts)):
                        dirs.add("/".join(parts[: i + 1]))

        for rel in sorted(dirs, key=lambda s: (s.count("/"), s)):
            tar.addfile(_dir_info(f"./{rel}/", mtime))

        for path in sorted(files, key=lambda p: str(p.relative_to(src))):
            rel = path.relative_to(src).as_posix()
            info = tar.gettarinfo(str(path), arcname=f"./{rel}")
            info.uid = 0
            info.gid = 0
            info.uname = "root"
            info.gname = "root"
            info.mtime = mtime
            if path.stat().st_mode & stat.S_IXUSR:
                info.mode = 0o755
            else:
                info.mode = 0o644
            with path.open("rb") as fh:
                tar.addfile(info, fh)
    return buf.getvalue()


def ar_member(name: str, data: bytes) -> bytes:
    header = (
        f"{name:<16}{0:<12}{0:<6}{0:<6}{0o100644:<8}{len(data):<10}`\n"
    ).encode("ascii")
    if len(header) != 60:
        raise RuntimeError(f"bad ar header length {len(header)}")
    if len(data) % 2 == 1:
        data = data + b"\n"
    return header + data


def main() -> None:
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)

    debian = STAGE / "DEBIAN"
    data = STAGE / "data"

    # Explicit directory tree so the tar has real directory members.
    for rel in DATA_DIRS:
        (data / rel).mkdir(parents=True, exist_ok=True)
    debian.mkdir(parents=True, exist_ok=True)

    write(debian / "control", CONTROL)
    write(debian / "postinst", POSTINST, 0o755)

    write(data / "usr/bin/renderbolt", WRAPPER, 0o755)
    dest_app = data / "opt/renderbolt/renderbolt"
    shutil.copy2(ROOT / "desktop/renderbolt", dest_app)
    os.chmod(dest_app, 0o755)
    shutil.copy2(ROOT / "desktop/engine3d.py", data / "opt/renderbolt/engine3d.py")
    shutil.copy2(ROOT / "desktop/studio_ui.py", data / "opt/renderbolt/studio_ui.py")
    shutil.copy2(ROOT / "desktop/preview3d.py", data / "opt/renderbolt/preview3d.py")
    vendor = data / "opt/renderbolt/vendor"
    vendor.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--target",
            str(vendor),
            "--upgrade",
            "moderngl",
            "-q",
        ]
    )
    for junk in vendor.rglob("__pycache__"):
        shutil.rmtree(junk, ignore_errors=True)
    shutil.copy2(ROOT / "public/samples/stage.jpg", data / "opt/renderbolt/share/stage.jpg")
    looks_src = ROOT / "looks"
    if looks_src.is_dir():
        for look in sorted(looks_src.glob("*.json")):
            shutil.copy2(look, data / "opt/renderbolt/share/looks" / look.name)
    write(data / "usr/share/doc/renderbolt/copyright", COPYRIGHT)
    write(data / "usr/share/doc/renderbolt/LICENSE", (ROOT / "LICENSE").read_text())
    write(data / "usr/share/applications/renderbolt.desktop", DESKTOP)
    write(data / "usr/share/metainfo/com.jmhbm.renderbolt.metainfo.xml", METAINFO)
    draw_icon(data / "usr/share/icons/hicolor/256x256/apps/renderbolt.png")

    control_tar = tar_dir(debian, gzip=True)
    data_tar = tar_dir(data, gzip=True)

    deb = b"!<arch>\n"
    deb += ar_member("debian-binary", b"2.0\n")
    deb += ar_member("control.tar.gz", control_tar)
    deb += ar_member("data.tar.gz", data_tar)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(deb)

    verify(data_tar)
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


def verify(data_tar: bytes) -> None:
    with tarfile.open(fileobj=io.BytesIO(data_tar), mode="r:gz") as tar:
        infos = tar.getmembers()
    names = [i.name for i in infos]
    print("data.tar members:")
    for info in infos:
        kind = "dir " if info.isdir() else "file"
        print(f"  {kind} {info.name}")
    required_dirs = [
        ".",
        "./opt",
        "./opt/renderbolt",
        "./opt/renderbolt/share",
        "./usr",
        "./usr/bin",
        "./usr/share",
        "./usr/share/doc",
        "./usr/share/doc/renderbolt",
        "./usr/share/applications",
        "./usr/share/icons/hicolor/256x256/apps",
    ]
    required_files = [
        "./opt/renderbolt/renderbolt",
        "./opt/renderbolt/engine3d.py",
        "./opt/renderbolt/studio_ui.py",
        "./opt/renderbolt/preview3d.py",
        "./opt/renderbolt/share/stage.jpg",
        "./usr/bin/renderbolt",
        "./usr/share/doc/renderbolt/LICENSE",
        "./usr/share/doc/renderbolt/copyright",
        "./usr/share/applications/renderbolt.desktop",
        "./usr/share/icons/hicolor/256x256/apps/renderbolt.png",
    ]
    by_name = {i.name: i for i in infos}
    missing = [n for n in required_dirs + required_files if n not in by_name]
    if missing:
        raise SystemExit(f"data.tar missing members: {missing}")
    for n in required_dirs:
        if not by_name[n].isdir():
            raise SystemExit(f"{n} is not a directory member")
    for f in required_files:
        parent = f.rsplit("/", 1)[0]
        if names.index(parent) > names.index(f):
            raise SystemExit(f"{parent} listed after {f}")
    print("deb data.tar directory layout ok")


if __name__ == "__main__":
    main()
