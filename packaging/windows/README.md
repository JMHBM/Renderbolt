# Windows installer

Inno Setup `.exe`. Build **on Windows 11** (or GitHub Actions `windows-latest`).

```powershell
python scripts\build-windows.py
```

Writes `public\downloads\Renderbolt-1.0.7-setup.exe`.

Needs:

- Python 3.10+ with pip
- [Inno Setup 6](https://jrsoftware.org/isinfo.php) (`iscc` on PATH, or Chocolatey `innosetup`)

The script downloads a Windows FFmpeg build, freezes the studio with PyInstaller, and wraps it. GPU encode on Windows is AMF (AMD), NVENC (NVIDIA), or QSV (Intel).
