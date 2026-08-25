# Studio

The studio is a single window: controls on the left, live preview on the right, transport along the bottom.

## Modes and styles

Toggle **2D** or **3D**, then pick a look:

| Style | 2D | 3D |
|---|---|---|
| Waveform | Flat ribbon of the time-domain signal | Connected mesh with depth |
| EQ | Vertical bars | Prism bars receding in Z |
| Circular | Polar ring | Halo / orbit |
| Liquid | Flowing waves | Terrain that rolls with the bass |

## Color

Presets (Rose, Ice, Ember, and the rest) are saturated on purpose so they survive lighting. You can also:

- Pick a custom color from the square palette
- Set a **base → tip** gradient (dark blue into light pink, etc.)
- Pulse hue with the beat

If a color looks washed out in the preview, check that you actually selected the chip — the engine uses the base/tip pair, not a leftover white default.

## Placement

The visualizer is not glued to the bottom of the frame.

- **X / Y** — put it anywhere on the canvas
- **Rotation** — full 360°
- **Stretch** — longer/shorter, taller/thinner
- **Mirror** — flip the geometry

Camera tilt (3D) is separate from that placement. Tilt is the isometric angle of the virtual camera.

## Frame

| Control | Options |
|---|---|
| Aspect | 16:9 · 9:16 · 1:1 |
| Resolution | 720p · 1080p · 4K |
| Frame rate | 24 · 30 · 60 |
| Titles | Top or bottom, optional scale |
| Fade | In / out, in seconds |
| Look | Glow, vignette, grain, sensitivity |

The background still **bounces** on the beat, with the edges fading as it moves toward or away from the camera.

## Shortcuts

| Key | Action |
|---|---|
| Space | Play / pause |
| G | Generate MP4 |
| R | Shuffle look |
| ← → | Seek 2 seconds |
| Home | Restart |
| Ctrl+O | Open audio |
| Ctrl+I | Open background |

Looks can be saved and reloaded. Shuffle is the fastest way to find a starting point you did not know you wanted.
