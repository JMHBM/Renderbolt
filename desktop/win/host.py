#!/usr/bin/env python3
"""Renderbolt for Windows — Edge WebView2 studio (not Tk).

Copyright (c) 2026 JMHBM
Licensed under Creative Commons Attribution 4.0 International
"""

from __future__ import annotations

import base64
import json
import os
import sys
import threading
import traceback
from pathlib import Path

VERSION = "1.0.7"
APP_NAME = "Renderbolt"

if getattr(sys, "frozen", False):
    HERE = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    APP_DIR = Path(sys.executable).resolve().parent
else:
    HERE = Path(__file__).resolve().parent
    APP_DIR = HERE
    sys.path.insert(0, str(HERE.parent))

os.environ.setdefault("RENDERBOLT_SHARE", str(HERE / "share"))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

LOG = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming") / "Renderbolt" / "win.log"


def _log(msg: str) -> None:
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(msg.rstrip() + "\n")
    except OSError:
        pass


def _mime(path: str) -> str:
    ext = Path(path).suffix.lower()
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".flac": "audio/flac",
        ".ogg": "audio/ogg",
        ".m4a": "audio/mp4",
        ".aac": "audio/aac",
    }.get(ext, "application/octet-stream")


class Api:
    def __init__(self) -> None:
        self.window = None
        self.audio_path = ""
        self.image_path = ""
        self._busy = False

    def _win(self):
        import webview

        if self.window is not None:
            return self.window
        return webview.windows[0] if webview.windows else None

    def version(self) -> str:
        return VERSION

    def default_cover(self) -> str:
        p = HERE / "share" / "stage.jpg"
        return self.file_data_url(str(p)) if p.is_file() else ""

    def pick_audio(self) -> str:
        import webview

        w = self._win()
        if not w:
            return ""
        result = w.create_file_dialog(
            webview.OPEN_DIALOG,
            file_types=("Audio (*.mp3;*.wav;*.flac;*.ogg;*.m4a;*.aac)", "All files (*.*)"),
        )
        if not result:
            return ""
        self.audio_path = result[0]
        return self.audio_path

    def pick_image(self) -> str:
        import webview

        w = self._win()
        if not w:
            return ""
        result = w.create_file_dialog(
            webview.OPEN_DIALOG,
            file_types=("Images (*.jpg;*.jpeg;*.png;*.webp)", "All files (*.*)"),
        )
        if not result:
            return ""
        self.image_path = result[0]
        return self.image_path

    def pick_save(self, name: str = "renderbolt.mp4") -> str:
        import webview

        w = self._win()
        if not w:
            return ""
        result = w.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename=name or "renderbolt.mp4",
            file_types=("MP4 video (*.mp4)",),
        )
        if not result:
            return ""
        path = result if isinstance(result, str) else result[0]
        if path and not path.lower().endswith(".mp4"):
            path = path + ".mp4"
        return path

    def pick_logo(self) -> str:
        import webview

        w = self._win()
        if not w:
            return ""
        result = w.create_file_dialog(
            webview.OPEN_DIALOG,
            file_types=("Images (*.png;*.webp;*.jpg;*.jpeg)", "All files (*.*)"),
        )
        return result[0] if result else ""

    def pick_look_save(self, name: str = "renderbolt-look.json") -> str:
        import webview

        w = self._win()
        if not w:
            return ""
        result = w.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename=name,
            file_types=("Renderbolt look (*.json)",),
        )
        if not result:
            return ""
        path = result if isinstance(result, str) else result[0]
        if path and not path.lower().endswith(".json"):
            path += ".json"
        return path

    def pick_look_load(self) -> str:
        import webview

        w = self._win()
        if not w:
            return ""
        result = w.create_file_dialog(
            webview.OPEN_DIALOG,
            file_types=("Renderbolt look (*.json)", "All files (*.*)"),
        )
        return result[0] if result else ""

    def write_text(self, path: str, text: str) -> bool:
        Path(path).write_text(text, encoding="utf-8")
        return True

    def read_text(self, path: str) -> str:
        return Path(path).read_text(encoding="utf-8")

    def pick_png_save(self, name: str = "renderbolt-frame.png") -> str:
        import webview

        w = self._win()
        if not w:
            return ""
        result = w.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename=name,
            file_types=("PNG image (*.png)",),
        )
        if not result:
            return ""
        path = result if isinstance(result, str) else result[0]
        if path and not path.lower().endswith(".png"):
            path += ".png"
        return path

    def save_data_url(self, path: str, data_url: str) -> bool:
        raw = data_url.split(",", 1)[-1]
        Path(path).write_bytes(base64.b64decode(raw))
        return True

    def file_data_url(self, path: str, max_bytes: int = 12_000_000) -> str:
        if not path or not os.path.isfile(path):
            return ""
        data = Path(path).read_bytes()
        if len(data) > max_bytes:
            if _mime(path).startswith("image/"):
                try:
                    from PIL import Image
                    from io import BytesIO

                    im = Image.open(path).convert("RGB")
                    im.thumbnail((1280, 1280))
                    buf = BytesIO()
                    im.save(buf, format="JPEG", quality=86)
                    data = buf.getvalue()
                    return "data:image/jpeg;base64," + base64.b64encode(data).decode("ascii")
                except Exception:
                    return ""
            return ""
        return f"data:{_mime(path)};base64," + base64.b64encode(data).decode("ascii")

    def generate(self, opts: dict) -> str:
        if self._busy:
            return "busy"
        self._busy = True
        threading.Thread(target=self._generate, args=(opts,), daemon=True, name="renderbolt-export").start()
        return "ok"

    def _js(self, fn: str, *args) -> None:
        w = self._win()
        if not w:
            return
        payload = ", ".join(json.dumps(a) for a in args)
        try:
            w.evaluate_js(f"window.{fn} && window.{fn}({payload})")
        except Exception as exc:
            _log(f"evaluate_js {fn}: {exc}")

    def _generate(self, opts: dict) -> None:
        try:
            from PIL import Image

            try:
                import renderbolt as rb
            except ImportError:
                import importlib.util

                cand = HERE / "renderbolt.py"
                if not cand.is_file():
                    cand = HERE.parent / "renderbolt"
                spec = importlib.util.spec_from_file_location("renderbolt", cand)
                rb = importlib.util.module_from_spec(spec)
                assert spec.loader
                spec.loader.exec_module(rb)

            audio = opts.get("audio") or self.audio_path
            cover_path = opts.get("cover") or self.image_path
            dest = opts.get("out") or ""
            if not audio or not os.path.isfile(audio):
                raise RuntimeError("Choose an audio file first.")
            if not dest:
                raise RuntimeError("Choose where to save the MP4.")
            if cover_path and os.path.isfile(cover_path):
                cover = Image.open(cover_path).convert("RGB")
            else:
                fallback = HERE / "share" / "stage.jpg"
                cover = (
                    Image.open(fallback).convert("RGB")
                    if fallback.is_file()
                    else Image.new("RGB", (1920, 1080), (12, 12, 16))
                )
            look = dict(opts.get("look") or {})
            logo = None
            logo_path = opts.get("logo") or ""
            if logo_path and os.path.isfile(logo_path):
                logo = Image.open(logo_path).convert("RGBA")

            def progress(msg: str, pct: float) -> None:
                self._js("__rbProgress", str(msg), float(pct or 0))

            label = rb.run_export(
                audio,
                dest,
                cover,
                look,
                opts.get("title") or "",
                opts.get("artist") or "",
                opts.get("album") or "",
                logo,
                progress,
            )
            self._js("__rbDone", dest, label)
        except Exception as exc:
            _log(traceback.format_exc())
            self._js("__rbFail", str(exc))
        finally:
            self._busy = False


def main() -> None:
    try:
        import webview
    except ImportError as exc:
        raise SystemExit(
            "Renderbolt for Windows needs pywebview (Edge WebView2).\n"
            "pip install pywebview"
        ) from exc

    ui = HERE / "ui" / "index.html"
    if not ui.is_file():
        ui = HERE / "index.html"
    if not ui.is_file():
        raise SystemExit(f"missing studio UI: {ui}")

    api = Api()
    window = webview.create_window(
        f"{APP_NAME} {VERSION}",
        url=str(ui),
        js_api=api,
        width=1280,
        height=800,
        min_size=(1000, 640),
        background_color="#0a0a0b",
    )
    api.window = window
    webview.start(debug=False)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        _log(traceback.format_exc())
        raise
