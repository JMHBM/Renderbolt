#!/usr/bin/env python3
"""Build Renderbolt-1.0.7-setup.exe. Run on Windows 11 (or windows-latest CI)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
WIN = ROOT / "packaging" / "windows"
DIST = WIN / "dist" / "Renderbolt"
WORK = WIN / "work"
VERSION = "1.0.7"
FFMPEG_ZIP = (
    "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
    "ffmpeg-master-latest-win64-gpl.zip"
)


def run(cmd: list[str], **kw) -> None:
    print("+", " ".join(cmd))
    subprocess.check_call(cmd, **kw)


def download_ffmpeg(dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    if (dest / "ffmpeg.exe").is_file() and (dest / "ffplay.exe").is_file():
        return
    archive = WORK / "ffmpeg.zip"
    archive.parent.mkdir(parents=True, exist_ok=True)
    print("downloading FFmpeg…")
    with urlopen(FFMPEG_ZIP, timeout=120) as src, open(archive, "wb") as out:
        shutil.copyfileobj(src, out)
    extract = WORK / "ffmpeg-src"
    if extract.exists():
        shutil.rmtree(extract)
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(extract)
    bins = next(extract.rglob("ffmpeg.exe"))
    for name in ("ffmpeg.exe", "ffplay.exe", "ffprobe.exe"):
        src = bins.parent / name
        if src.is_file():
            shutil.copy2(src, dest / name)


def freeze() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    entry = WORK / "renderbolt.py"
    shutil.copy2(ROOT / "desktop" / "renderbolt", entry)
    for name in ("engine3d.py", "preview3d.py", "studio_ui.py"):
        shutil.copy2(ROOT / "desktop" / name, WORK / name)
    share = WORK / "share"
    share.mkdir(exist_ok=True)
    cover = None
    for cand in (
        ROOT / "desktop" / "share" / "stage.jpg",
        ROOT / "public" / "samples" / "stage.jpg",
        ROOT / "packaging" / "windows" / "stage.jpg",
    ):
        if cand.is_file():
            cover = cand
            break
    if cover is None:
        from PIL import Image
        img = Image.new("RGB", (1920, 1080), (12, 12, 16))
        img.save(share / "stage.jpg", quality=88)
    else:
        shutil.copy2(cover, share / "stage.jpg")
    looks = WORK / "looks"
    if looks.exists():
        shutil.rmtree(looks)
    shutil.copytree(ROOT / "looks", looks, ignore=shutil.ignore_patterns("README.md"))

    sep = ";" if os.name == "nt" else ":"
    ico = WIN / "renderbolt.ico"
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        "Renderbolt",
        "--distpath",
        str(WIN / "dist"),
        "--workpath",
        str(WORK / "pyi"),
        "--specpath",
        str(WORK),
        "--icon",
        str(ico),
        "--add-data",
        f"{share}{sep}share",
        "--add-data",
        f"{looks}{sep}looks",
        "--hidden-import",
        "engine3d",
        "--hidden-import",
        "preview3d",
        "--hidden-import",
        "studio_ui",
        "--hidden-import",
        "PIL._tkinter_finder",
        "--hidden-import",
        "numpy",
        "--hidden-import",
        "moderngl",
        "--hidden-import",
        "glcontext",
        "--collect-all",
        "moderngl",
        "--collect-all",
        "glcontext",
        str(entry),
    ]
    run(cmd, cwd=str(WORK))
    download_ffmpeg(DIST)
    shutil.copy2(ROOT / "LICENSE", DIST / "LICENSE.txt")


def innosetup() -> Path:
    iscc = shutil.which("iscc") or shutil.which("ISCC")
    if not iscc:
        for cand in (
            Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
            / "Inno Setup 6"
            / "ISCC.exe",
            Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Inno Setup 6" / "ISCC.exe",
        ):
            if cand.is_file():
                iscc = str(cand)
                break
    if not iscc:
        raise SystemExit("Inno Setup 6 is required (choco install innosetup)")
    out_dir = ROOT / "public" / "downloads"
    out_dir.mkdir(parents=True, exist_ok=True)
    run(
        [
            iscc,
            f"/DDistDir={DIST}",
            str(WIN / "renderbolt.iss"),
        ]
    )
    setup = out_dir / f"Renderbolt-{VERSION}-setup.exe"
    if not setup.is_file():
        # Inno may write next to the iss if OutputDir is relative
        alt = WIN / f"Renderbolt-{VERSION}-setup.exe"
        if alt.is_file():
            shutil.move(str(alt), str(setup))
    if not setup.is_file():
        raise SystemExit(f"installer not found: {setup}")
    print("wrote", setup, setup.stat().st_size, "bytes")
    return setup


def main() -> None:
    if os.name != "nt":
        raise SystemExit("build-windows.py must run on Windows (or GitHub windows-latest).")
    run([sys.executable, "-m", "pip", "install", "-U", "pip", "pyinstaller", "pillow", "numpy", "moderngl"])
    freeze()
    innosetup()


if __name__ == "__main__":
    main()
