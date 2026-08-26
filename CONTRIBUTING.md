# Contributing

Renderbolt is a small studio. Keep changes focused.

1. The public GitHub Release is **1.0.6**. `main` may already contain 1.0.7 work. Do not cut a 1.0.7 release or retarget README download links until we agree it is ready.
2. The supported ship is the Debian package. Do not advertise Fedora, Windows, or macOS until those packages are tested.
3. Desktop app lives in `desktop/`. Match the existing Tk studio look.
4. Packaging must keep parent directories as real archive members in the `.deb`.
5. Credit JMHBM and keep the CC BY 4.0 license.

```bash
python3 -m py_compile desktop/renderbolt desktop/engine3d.py desktop/preview3d.py desktop/studio_ui.py
python3 scripts/build-deb.py
```
