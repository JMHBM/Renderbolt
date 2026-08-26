# Roadmap

This is a living list, not a contract. GitHub Release is **1.0.6**. **1.0.7** stays on `main` until we cut it. Nothing else ships until it is actually tested.

## Order of operations

1. **Debian-family `.deb`** — Ubuntu, Debian, Zorin OS. This is the test bed. JMHBM is moving off Fedora Silverblue onto Zorin OS 18.1 so packaging is not fighting an immutable host.
2. **Windows 11** — after the `.deb` is signed off. Native installer, NVENC / QSV, same studio.
3. **macOS** — no Mac on the desk, so this is a VM (and later a real Mac if one shows up). VideoToolbox. No download until a VM run has actually exported a file.
4. **RPM / Fedora / other distros last.** An RPM was built once. It stays off Releases until someone installs it on a mutable Fedora and says it works.

## Now — 1.0.6 on Releases

- Debian / Ubuntu / Zorin `.deb`
- 2D + 3D studio
- Live preview
- VA-API on AMD, software fallback
- 16:9 / 9:16 / 1:1 · 720p–4K
- Beat bounce, placement, rotation, stretch, gradients

## Unreleased on `main` — 1.0.7

- Starter looks, session memory, PNG frame export
- Headless CLI (`renderbolt render`)
- AppStream metainfo
- Keys 1–6, About

## Engine, later

- NVIDIA NVENC / Intel QSV (Linux)
- More 3D looks (particles, tunnels, spectrum cities)
- Preset packs people can share
- Optional lyrics / timed text
- Batch render from a folder of tracks

## What we will not do

- Require an account
- Upload your audio to a server to “process” it
- Ship a package we have not installed ourselves
- Lead with RPM because the first box was Silverblue

Watch [Releases](https://github.com/JMHBM/Renderbolt/releases). The Debian build is the one we stand behind today.
