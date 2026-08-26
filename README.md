# Renderbolt

Cinematic audio visualizer. Drop in a song and a still, pick a look, and export an MP4.

Designed by **JMHBM**. Licensed under [Creative Commons Attribution 4.0 International](LICENSE).

**Debian / Ubuntu is available now.** Current release is **1.0.6**. Windows, macOS, Fedora, and other Linux distros are coming soon.

`main` is 1.0.7 in progress — starter looks, session memory, PNG frames, and a headless CLI. That is not on Releases yet.

![Renderbolt studio](docs/studio.png)

## Install

### Debian / Ubuntu (current)

Download [`renderbolt_1.0.6_all.deb`](https://github.com/JMHBM/Renderbolt/releases/download/1.0.6/renderbolt_1.0.6_all.deb) from the [v1.0.6 release](https://github.com/JMHBM/Renderbolt/releases/tag/1.0.6), then:

```bash
sudo apt install ./renderbolt_1.0.6_all.deb
```

Needs Python 3.10+, Tk, Pillow, NumPy, and FFmpeg. On AMD GPUs, install `mesa-va-drivers` for hardware encode.

Open **Renderbolt** from the app menu, or run `renderbolt`.

### Coming soon

- Windows
- macOS
- Fedora / other Linux distros

### From source (Linux)

```bash
sudo apt install python3-tk python3-pil python3-pil.imagetk python3-numpy ffmpeg
pip install -r desktop/requirements.txt
python3 desktop/renderbolt
```

From `main` (1.0.7, unreleased) you can also render with no window:

```bash
python3 desktop/renderbolt render --audio song.mp3 --cover art.jpg --out out.mp4 --preset "Night Drive"
```

## What it does

- Background image from disk, with beat bounce and edge fade
- Song / artist / album titles (optional)
- 2D or 3D: waveform, EQ bars, circular, liquid
- Color presets, custom palette, base → tip gradient
- Place, rotate (0–360°), stretch, and mirror the visualizer
- Live preview, then GPU-accelerated H.264 when VA-API is present
- Formats: 16:9, 9:16, 1:1 · 720p / 1080p / 4K · 24 / 30 / 60 fps

### Shortcuts

| Key | Action |
|---|---|
| Space | Play / pause |
| G | Generate MP4 |
| R | Shuffle look |
| ← → | Seek 2 seconds |
| Home | Restart |
| Ctrl+O | Open audio |
| Ctrl+I | Open background |

## License

[CC BY 4.0](LICENSE) — credit **JMHBM**.
