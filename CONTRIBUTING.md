# Contributing

Renderbolt is a small studio. Keep changes focused.

1. The public GitHub Release is **1.0.8** (Windows installer + Debian `.deb`). Fedora / RPM last. macOS later.
2. Windows studio lives in `desktop/win/` (WebView2). Linux studio lives in `desktop/renderbolt` (Tk).
3. Packaging must keep parent directories as real archive members in the `.deb`.
4. Credit **JMHBM**, **Grok (xAI)**, and **Jan-4B-Base-Instruct (Menlo Labs Research)**. Copyright is equally shared. Keep the CC BY 4.0 license.

```bash
python3 -m py_compile desktop/renderbolt desktop/engine3d.py desktop/preview3d.py desktop/studio_ui.py
python3 scripts/build-deb.py
```

```powershell
python scripts\build-windows.py
```
