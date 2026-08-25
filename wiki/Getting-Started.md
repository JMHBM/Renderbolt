# Getting Started

Renderbolt 1.0.6 is a Linux desktop app. The supported package is Debian / Ubuntu.

## Install (Debian / Ubuntu)

1. Download [`renderbolt_1.0.6_all.deb`](https://github.com/JMHBM/Renderbolt/releases/download/1.0.6/renderbolt_1.0.6_all.deb) from the [v1.0.6 release](https://github.com/JMHBM/Renderbolt/releases/tag/1.0.6).
2. Install it:

```bash
sudo apt install ./renderbolt_1.0.6_all.deb
```

3. Open **Renderbolt** from the app menu, or run `renderbolt`.

### Dependencies

`apt` pulls these in. If you build from source, you want:

- Python 3.10+
- Tk (`python3-tk`)
- Pillow + ImageTk
- NumPy
- FFmpeg

On AMD GPUs, install `mesa-va-drivers` so export can use VA-API instead of the CPU.

### From source

```bash
sudo apt install python3-tk python3-pil python3-pil.imagetk python3-numpy ffmpeg
pip install -r desktop/requirements.txt
python3 desktop/renderbolt
```

## First render

1. Drop in an audio file (MP3, WAV, FLAC, OGG…).
2. Choose a background image.
3. Optionally fill song / artist / album.
4. Pick **2D** or **3D**, then a style.
5. Hit **Generate**.

The live preview is a working sketch of the final frame. Export writes a real MP4 through FFmpeg.

Windows, macOS, Fedora, and other distros are not supported yet. See [Roadmap](Roadmap.md).
