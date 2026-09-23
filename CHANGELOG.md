# Changelog

## 1.0.11 — 2026-09-23

Linux **AppImage** studio fixes. 1.0.10 still letterboxed a flat sketch and blended dark ink away.

- Preview is the real frame, scaled to cover the stage (no inset, no 560px box)
- Playback redraws that frame, and waveforms use peaks so they actually move
- Black and dark grey stay the color you picked, with a light rim so they show on a dark cover
- Generate never opens GLX on the UI thread. If EGL is missing it draws on the CPU instead of sitting on Starting export

## 1.0.10 — 2026-09-22

Linux **AppImage** studio fixes (Windows / Debian remain 1.0.8).

- Preview fills the stage (cover-crop, no 560px cap)
- Preview is live while playing
- Dark / black vis colors stay readable (lift + halo)
- Export no longer hangs on GPU init — 6s timeout, then CPU compositor
- Status updates while decoding / encoding
- Type-2 AppImage `Renderbolt-1.0.10-x86_64.AppImage`

## 1.0.9 — 2026-09-22

Linux **AppImage** only. Windows installer and Debian `.deb` remain 1.0.8.

Cavasik-inspired visualizers, original Renderbolt code (no GPL source vendored).

- **Levels** — stacked spectrum cells
- **Particles** — one cube per band, riding the amplitude
- **Spine** — growing squares along the midline
- **Radial wave** — filled circular spectrum
- Starter looks: Ladder, Scatter, Vertebra, Orbit
- Type-2 AppImage with static FUSE3 (`Renderbolt-1.0.9-x86_64.AppImage`)

## 1.0.8 — 2026-08-28

Official Windows release. Debian / Ubuntu `.deb` remains supported. Linux **AppImage** for Fedora / Silverblue.

- Type-2 AppImage with static FUSE3 (`Renderbolt-1.0.8-x86_64.AppImage`) — bundled CPython 3.12, Tcl/Tk, FFmpeg
- 2D export uses the same GPU engine as 3D
- Cover art stays upright in the MP4
- Live preview shows the vis, titles, progress bar, and clock
- 2D visualizer sits flush with the bottom of the frame
- Hardware encode: AMD AMF, NVIDIA NVENC, Intel QSV, CPU fallback

## 1.0.7 — 2026-08-28

First official **Windows** release. Debian / Ubuntu `.deb` remains supported.

- Windows studio on Edge WebView2 (not Tk): live canvas preview, UI stays responsive
- Square color pickers, Advanced panel, placement, starter looks, shuffle, save/load look
- Hardware encode: AMD AMF, NVIDIA NVENC, Intel QSV, CPU fallback
- Starter looks: Night Drive, Live Session, Vinyl, After Hours, Neon Rain, Broadcast
- Shareable look JSON in `looks/`
- Headless CLI: `renderbolt render --audio … --out …`
- VA-API on Linux: rank any AMD GPU, `--probe-gpu`
- Windows live preview uses the GPU engine (~12 fps at 960px). UI stays on WebView; GL never runs on the UI thread.

## 1.0.6 — 2026-08-25

First public release. **Debian / Ubuntu `.deb` is the supported package.**

- 16:9, 9:16, and 1:1 output formats
- Fade in / fade out, pulse hue, glow, vignette, grain
- Shuffle look, save / load looks, watermark logo
- Export 720p / 1080p / 4K at 24 / 30 / 60 fps
- Keyboard shortcuts and click-to-seek
- VA-API H.264 on AMD GPUs, with CPU fallback
- Windows, macOS, Fedora, and other distros: coming soon

## 1.0.5

- Scrollable studio sidebar
- 2D and 3D visualizer modes
- Placement, rotation, stretch, mirror
- Saturated color presets, base → tip gradient, square palette

## 1.0.4

- Studio UI matching the web layout
- Live preview

## 1.0.3

- ModernGL 3D pipeline piped into FFmpeg

## 1.0.2

- VA-API H.264 encode on AMD GPUs, software fallback

## 1.0.1

- Debian packages include parent directories as archive members

## 1.0.0

- First Linux release: waveform, EQ, circular, liquid waves, MP4 export
