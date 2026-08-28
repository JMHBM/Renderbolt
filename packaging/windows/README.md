# Windows installer

The Windows app is a **WebView2 studio** (`desktop/win/`), not a port of the Linux Tk window.

- Preview: HTML + canvas (the cover always shows)
- Export: the same FFmpeg path as Linux (`h264_amf` / `nvenc` / `qsv`, CPU fallback)
- Linux `.deb` is unchanged

Build on Windows 11 or `windows-latest`:

```
python scripts/build-windows.py
```

Output: `public/downloads/Renderbolt-1.0.7-setup.exe`
