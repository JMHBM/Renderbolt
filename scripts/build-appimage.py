#!/usr/bin/env python3
"""Build Renderbolt-1.0.8-x86_64.AppImage (type-2, static FUSE3 runtime).

Bundles CPython 3.12 + Tcl/Tk, Pillow, NumPy, ModernGL, and a static FFmpeg.
Host only needs libGL / libX11 (already on Fedora and Silverblue).
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
import tarfile
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "packaging" / "linux" / "cache"
STAGE = ROOT / "packaging" / "linux" / "AppDir"
OUT = ROOT / "public" / "downloads" / "Renderbolt-1.0.8-x86_64.AppImage"
VERSION = "1.0.8"

PYTHON_URL = (
    "https://github.com/astral-sh/python-build-standalone/releases/download/"
    "20260901/cpython-3.12.14+20260901-x86_64-unknown-linux-gnu-install_only.tar.gz"
)
FFMPEG_URL = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
APPIMAGETOOL_URL = (
    "https://github.com/AppImage/appimagetool/releases/download/continuous/"
    "appimagetool-x86_64.AppImage"
)
RUNTIME_URL = (
    "https://github.com/AppImage/type2-runtime/releases/download/continuous/"
    "runtime-x86_64"
)

DESKTOP = """[Desktop Entry]
Type=Application
Name=Renderbolt
Comment=Cinematic audio visualizer
Exec=renderbolt
Icon=renderbolt
Terminal=false
Categories=AudioVideo;Audio;Video;
StartupNotify=true
StartupWMClass=Renderbolt
X-AppImage-Version=1.0.8
"""

APPRUN = """#!/bin/sh
set -e
HERE="$(dirname "$(readlink -f "$0")")"
export PATH="$HERE/usr/bin:$HERE/python/bin:$PATH"
export LD_LIBRARY_PATH="$HERE/python/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export TCL_LIBRARY="$HERE/python/lib/tcl9.0"
export TK_LIBRARY="$HERE/python/lib/tk9.0"
export PYTHONHOME="$HERE/python"
export PYTHONNOUSERSITE=1
export RENDERBOLT_SHARE="$HERE/opt/renderbolt/share"
export RENDERBOLT_LOOKS="$HERE/opt/renderbolt/share/looks"
# Prefer the bundled encoder; VA-API / NVENC still use host drivers.
export SSL_CERT_FILE="${SSL_CERT_FILE:-$HERE/python/lib/python3.12/site-packages/certifi/cacert.pem}"
exec "$HERE/python/bin/python3" "$HERE/opt/renderbolt/renderbolt" "$@"
"""

WRAPPER = """#!/bin/sh
exec "$(dirname "$(readlink -f "$0")")/../AppRun" "$@"
"""


def run(cmd: list[str], **kw) -> None:
    print("+", " ".join(cmd))
    subprocess.check_call(cmd, **kw)


def download(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size > 1024:
        return dest
    print(f"downloading {url}")
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urlopen(url, timeout=180) as src, open(tmp, "wb") as out:
        shutil.copyfileobj(src, out)
    tmp.replace(dest)
    return dest


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
    bolt = [(156, 28), (66, 132), (118, 132), (84, 228), (196, 116), (140, 116)]
    d.polygon(bolt, fill=(232, 238, 242, 255))
    im.save(dest, "PNG")


def extract_python(archive: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    with tarfile.open(archive) as tar:
        tar.extractall(dest)
    # tarball root is "python/"
    inner = dest / "python"
    if not (inner / "bin" / "python3").is_file():
        raise SystemExit(f"python tarball missing bin/python3 under {dest}")


def install_ffmpeg(appdir: Path) -> None:
    bin_dir = appdir / "usr" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    host = Path("/usr/local/bin/ffmpeg")
    if host.is_file():
        shutil.copy2(host, bin_dir / "ffmpeg")
        os.chmod(bin_dir / "ffmpeg", 0o755)
        return
    archive = download(FFMPEG_URL, CACHE / "ffmpeg-release-amd64-static.tar.xz")
    extract = CACHE / "ffmpeg-src"
    if extract.exists():
        shutil.rmtree(extract)
    extract.mkdir()
    run(["tar", "-xJf", str(archive), "-C", str(extract), "--strip-components=1"])
    src = extract / "ffmpeg"
    if not src.is_file():
        matches = list(extract.rglob("ffmpeg"))
        if not matches:
            raise SystemExit("static ffmpeg binary not found")
        src = matches[0]
    shutil.copy2(src, bin_dir / "ffmpeg")
    os.chmod(bin_dir / "ffmpeg", 0o755)


def stage_app(appdir: Path) -> None:
    opt = appdir / "opt" / "renderbolt"
    share = opt / "share"
    looks = share / "looks"
    looks.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "desktop" / "renderbolt", opt / "renderbolt")
    os.chmod(opt / "renderbolt", 0o755)
    shutil.copy2(ROOT / "desktop" / "engine3d.py", opt / "engine3d.py")
    shutil.copy2(ROOT / "desktop" / "studio_ui.py", opt / "studio_ui.py")
    shutil.copy2(ROOT / "desktop" / "preview3d.py", opt / "preview3d.py")
    stage_jpg = ROOT / "desktop" / "share" / "stage.jpg"
    if not stage_jpg.is_file():
        stage_jpg = ROOT / "public" / "samples" / "stage.jpg"
    shutil.copy2(stage_jpg, share / "stage.jpg")
    for look in sorted((ROOT / "looks").glob("*.json")):
        shutil.copy2(look, looks / look.name)
    doc = appdir / "usr" / "share" / "doc" / "renderbolt"
    doc.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "LICENSE", doc / "LICENSE")
    write(appdir / "renderbolt.desktop", DESKTOP)
    write(appdir / "AppRun", APPRUN, 0o755)
    write(appdir / "usr" / "bin" / "renderbolt", WRAPPER, 0o755)
    draw_icon(appdir / "renderbolt.png")
    shutil.copy2(appdir / "renderbolt.png", appdir / ".DirIcon")


def pip_install(python: Path) -> None:
    run([str(python), "-m", "pip", "install", "-q", "--upgrade", "pip"])
    run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "-q",
            "Pillow>=10.0",
            "numpy>=1.24",
            "moderngl>=5.10",
            "certifi",
        ]
    )


def wrap_appimage(appdir: Path) -> None:
    tool = download(APPIMAGETOOL_URL, CACHE / "appimagetool-x86_64.AppImage")
    runtime = download(RUNTIME_URL, CACHE / "runtime-x86_64")
    os.chmod(tool, tool.stat().st_mode | stat.S_IXUSR)
    os.chmod(runtime, runtime.stat().st_mode | stat.S_IXUSR)
    extracted = CACHE / "appimagetool-extracted"
    if not (extracted / "AppRun").is_file():
        if extracted.exists():
            shutil.rmtree(extracted)
        cwd = Path.cwd()
        os.chdir(CACHE)
        run([str(tool), "--appimage-extract"])
        os.chdir(cwd)
        squash = CACHE / "squashfs-root"
        if squash.exists():
            squash.rename(extracted)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        OUT.unlink()
    env = os.environ.copy()
    env["ARCH"] = "x86_64"
    env["VERSION"] = VERSION
    run(
        [
            str(extracted / "AppRun"),
            "-n",
            "--runtime-file",
            str(runtime),
            str(appdir),
            str(OUT),
        ],
        env=env,
    )
    os.chmod(OUT, 0o755)


def verify(python: Path) -> None:
    run(
        [
            str(python),
            "-c",
            "import tkinter, PIL, numpy, moderngl; print('imports-ok', tkinter.TkVersion)",
        ]
    )
    run([str(STAGE / "usr" / "bin" / "ffmpeg"), "-version"])
    payload = STAGE / "opt" / "renderbolt" / "renderbolt"
    run(
        [
            str(python),
            str(payload),
            "--help",
        ]
    )


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)

    py_tar = download(PYTHON_URL, CACHE / Path(PYTHON_URL).name)
    extract_python(py_tar, STAGE)
    python = STAGE / "python" / "bin" / "python3"
    pip_install(python)
    install_ffmpeg(STAGE)
    stage_app(STAGE)
    verify(python)
    wrap_appimage(STAGE)
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)
