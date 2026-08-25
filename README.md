# Renderbolt

Cinematic audio visualizer for Linux. Drop in a song and a still, pick a look, and export an MP4.

Designed by **JMHBM**. Licensed under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).

![Renderbolt studio](docs/studio.png)

## Install

### Debian / Ubuntu

```bash
sudo apt install ./renderbolt_1.0.6_all.deb
```

Packages live in [`public/downloads/`](public/downloads/). Needs Python 3.10+, Tk, Pillow, NumPy, and FFmpeg. On AMD GPUs, install `mesa-va-drivers` for hardware encode.

### Fedora / Silverblue 44 (Coming Soon)

```bash
# Workstation
sudo dnf install ./renderbolt-1.0.6-1.fc44.noarch.rpm

# Silverblue
rpm-ostree install ./renderbolt-1.0.6-1.fc44.noarch.rpm
systemctl reboot
```

Then open **Renderbolt** from the app menu, or run `renderbolt`.

### From source

```bash
sudo apt install python3-tk python3-pil python3-pil.imagetk python3-numpy ffmpeg
# Fedora: python3-tkinter python3-pillow python3-pillow-tk python3-numpy ffmpeg
pip install -r desktop/requirements.txt
python3 desktop/renderbolt
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

## Build packages

```bash
python3 scripts/build-deb.py
python3 scripts/build-rpm.py
```

Outputs:

- `public/downloads/renderbolt_1.0.6_all.deb`
- `public/downloads/renderbolt-1.0.6-1.fc44.noarch.rpm`

## Browser studio

`src/` is an in-browser preview of the same studio (Web Audio + canvas). The installable Linux app in `desktop/` is the product.

```bash
npm install
npm run dev
```

## License

[CC BY 4.0](LICENSE) — credit **JMHBM**.
