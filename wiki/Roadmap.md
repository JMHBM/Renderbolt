# Roadmap

This is a living list, not a contract. 1.0.6 is Debian. Everything else ships when it is actually tested.

## Now — 1.0.6

- Debian / Ubuntu `.deb`
- 2D + 3D studio
- Live preview
- VA-API on AMD, software fallback
- 16:9 / 9:16 / 1:1 · 720p–4K
- Beat bounce, placement, rotation, stretch, gradients

## Next — other Linux

| Target | Status | Notes |
|---|---|---|
| Fedora / Silverblue RPM | Built, **untested** | Will not be on the release page until JMHBM signs off |
| AppImage / Flatpak | Planned | One file that runs on more distros without a package manager fight |
| NVIDIA NVENC / Intel QSV | Planned | Same pipe as VA-API, different encoder |

## Then — Windows

A real Windows build is the commercial-shaped release: installer, hardware encode (NVENC / QSV), the same studio. Not a Python zip with a README. When it exists, it will have its own tested artifact on GitHub Releases.

## Then — macOS

VideoToolbox encode, native windowing, signed app if we can do it cleanly. Same rule: no download until it has been used on a Mac, not just cross-compiled.

## Engine, later

Ideas we want, in no sacred order:

- More 3D looks (particles, tunnels, spectrum cities)
- Preset packs / look files people can share
- Template aspect presets for YouTube, Shorts, square
- Optional lyrics / timed text
- Batch render from a folder of tracks
- A small library of motion (slow dolly, orbit) that does not fight the beat bounce

## What we will not do

- Require an account
- Upload your audio to a server to “process” it
- Ship a package we have not installed ourselves

If you are waiting on Fedora, Windows, or macOS: that is fair. Watch [Releases](https://github.com/JMHBM/Renderbolt/releases). The Debian build is the one we stand behind today.
