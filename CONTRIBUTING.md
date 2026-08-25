# Contributing

Renderbolt is a small studio. Keep changes focused.

1. The supported ship is the Debian package. Do not advertise Fedora, Windows, or macOS until those packages are tested.
2. Desktop app lives in `desktop/`. Match the existing Tk studio look.
3. Packaging must keep parent directories as real archive members in the `.deb`.
4. Credit JMHBM and keep the CC BY 4.0 license.

```bash
python3 -m py_compile desktop/renderbolt desktop/engine3d.py desktop/preview3d.py desktop/studio_ui.py
python3 scripts/build-deb.py
```
