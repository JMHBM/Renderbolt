# Testing

The box that matters is **Zorin OS 18.1** (Ubuntu 24.04 family, `apt`). Fedora Silverblue is out of the loop on purpose — immutable hosts made the RPM path a fight we do not need while the `.deb` is still the product.

Public package: [renderbolt_1.0.6_all.deb](https://github.com/JMHBM/Renderbolt/releases/download/1.0.6/renderbolt_1.0.6_all.deb)

## First boot on Zorin

```bash
sudo apt update
sudo apt install ./renderbolt_1.0.6_all.deb
# AMD Radeon (RX 6600M and friends):
sudo apt install mesa-va-drivers
vainfo || true
renderbolt
```

`vainfo` should list a VAProfile for H.264 encode if GPU export will kick in. If it does not, Renderbolt still finishes on CPU.

## What to poke

- Audio + still from disk, not the demo beat
- 2D and 3D, all four styles
- Color presets (Rose should not come out white)
- Generate a 16:9 1080p MP4, then a 9:16
- Progress bar and titles on the export
- VA-API vs CPU: the status line says which encoder won

## 1.0.7 from source (optional)

Do not treat this as the release. `main` is ahead of 1.0.6.

```bash
sudo apt install python3-tk python3-pil python3-pil.imagetk python3-numpy ffmpeg
pip install -r desktop/requirements.txt
python3 desktop/renderbolt
```

Starter looks, `S` for PNG, and `renderbolt render --audio … --out …` live here.

## Later, not now

| When | What |
|---|---|
| `.deb` signed off | Windows 11 installer |
| After Windows, in a VM | macOS |
| Last | RPM / Fedora / dnf |

If a test fails, open a [bug](https://github.com/JMHBM/Renderbolt/issues/new?template=bug.yml) and say Zorin 18.1.

## GPU encode (VA-API)

From `main` / 1.0.7 source:

```bash
sudo apt install mesa-va-drivers vainfo ffmpeg
# not the snap — /usr/bin/ffmpeg
python3 desktop/renderbolt --probe-gpu
```

It walks every `/dev/dri/renderD*`, prefers AMD (highest VRAM = the discrete card on laptops), and writes `~/.config/renderbolt/vaapi.log`. F1 / About in the studio shows the pick.

Override if needed: `RENDERBOLT_VAAPI_DEVICE=/dev/dri/renderD129`
