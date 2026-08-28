# Renderbolt

Cinematic audio visualizer. Drop in a song and a still, pick a look, and export an MP4 on your machine.

Designed by **JMHBM**. [CC BY 4.0](LICENSE).

**Latest: [1.0.8](https://github.com/JMHBM/Renderbolt/releases/tag/1.0.8)** · Windows installer + Debian / Ubuntu `.deb`

[![check](https://github.com/JMHBM/Renderbolt/actions/workflows/check.yml/badge.svg)](https://github.com/JMHBM/Renderbolt/actions/workflows/check.yml)
[![windows](https://github.com/JMHBM/Renderbolt/actions/workflows/windows.yml/badge.svg)](https://github.com/JMHBM/Renderbolt/actions/workflows/windows.yml)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](LICENSE)

![Renderbolt](docs/banner.jpg)

![Renderbolt studio](docs/studio.png)

## Windows

Download **[Renderbolt-1.0.8-setup.exe](https://github.com/JMHBM/Renderbolt/releases/download/1.0.8/Renderbolt-1.0.8-setup.exe)** from the [1.0.8 release](https://github.com/JMHBM/Renderbolt/releases/tag/1.0.8).

64-bit Windows 10/11. Windows 11 already has WebView2; Windows 10 may need the [Evergreen runtime](https://developer.microsoft.com/microsoft-edge/webview2/). The installer is unsigned, so SmartScreen / Avast may warn on first run.

Hardware encode when the driver is present: **AMD AMF**, **NVIDIA NVENC**, **Intel QSV**. Otherwise CPU (libx264). FFmpeg is bundled.

## Debian / Ubuntu

```bash
sudo apt install ./renderbolt_1.0.8_all.deb
```

Get the file from the [1.0.8 release](https://github.com/JMHBM/Renderbolt/releases/tag/1.0.8). Needs Python 3.10+, Tk, Pillow, NumPy, and FFmpeg. On AMD GPUs, install `mesa-va-drivers`.

Open **Renderbolt** from the app menu, or run `renderbolt`.

## From source

```bash
sudo apt install python3-tk python3-pil python3-pil.imagetk python3-numpy ffmpeg
pip install -r desktop/requirements.txt
python3 desktop/renderbolt
```

Headless (no window):

```bash
python3 desktop/renderbolt render \
  --audio song.mp3 --cover art.jpg --out out.mp4 \
  --look looks/night-drive.json
```

Starter looks live in [`looks/`](looks/README.md). Keys **1–6** load them in the Linux studio.

## What it does

- Background still from disk, with beat bounce and edge fade
- Optional song / artist / album titles
- 2D or 3D: waveform, EQ bars, circular, liquid
- Color presets, custom palette, base → tip gradient
- Place, rotate (0–360°), stretch, and mirror
- 16:9 · 9:16 · 1:1 · 720p / 1080p / 4K · 24 / 30 / 60 fps

### Shortcuts

| Key | Action |
|---|---|
| Space | Play / pause |
| G | Generate MP4 |
| R | Shuffle look |
| 1–6 | Starter looks (Linux studio) |
| S | Save current frame (PNG) |
| F1 | About |
| ← → | Seek 2 seconds |
| Home | Restart |
| Ctrl+O | Open audio |
| Ctrl+I | Open background |

## Wiki

- [Welcome](https://github.com/JMHBM/Renderbolt/wiki/Welcome-to-Renderbolt)
- [Getting started](https://github.com/JMHBM/Renderbolt/wiki/Getting-Started)
- [Studio](https://github.com/JMHBM/Renderbolt/wiki/Studio)
- [Visual engine](https://github.com/JMHBM/Renderbolt/wiki/Visual-Engine)
- [Roadmap](https://github.com/JMHBM/Renderbolt/wiki/Roadmap)

## License

[CC BY 4.0](LICENSE) — credit **JMHBM**.
