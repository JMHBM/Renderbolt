# Looks

JSON look files Renderbolt can load in the studio (**Load look…**) or from the CLI.

| File | Vibe |
|---|---|
| [night-drive.json](night-drive.json) | 3D waveform, midnight, 16:9 |
| [live-session.json](live-session.json) | 2D EQ, ember, live-mix bottom bars |
| [vinyl.json](vinyl.json) | 3D circular, gold, square, film grain |
| [after-hours.json](after-hours.json) | 3D liquid, violet |
| [neon-rain.json](neon-rain.json) | 3D EQ, cyan, 9:16 |
| [broadcast.json](broadcast.json) | 2D waveform, mono, titles + progress |

From source:

```bash
python3 desktop/renderbolt render \
  --audio song.mp3 --cover art.jpg --out out.mp4 \
  --look looks/night-drive.json
```

These ship with 1.0.7 (unreleased). The GitHub Release `.deb` is still 1.0.6.
