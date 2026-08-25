# Contributing

Renderbolt is a small studio. Keep changes focused.

1. Desktop app lives in `desktop/`. Match the existing Tk studio look.
2. Packaging must keep parent directories as real archive members in the `.deb`.
3. Fedora RPMs need SHA256 header digest tag 273 so `rpm-ostree` verifies them.
4. Credit JMHBM and keep the CC BY 4.0 license.

```bash
python3 -m py_compile desktop/renderbolt desktop/engine3d.py desktop/preview3d.py desktop/studio_ui.py
python3 scripts/build-deb.py
python3 scripts/build-rpm.py
```
