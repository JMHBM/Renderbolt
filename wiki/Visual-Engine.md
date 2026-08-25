# Visual Engine

Renderbolt is not a screen recorder. It synthesizes every frame, then hands the pixels to FFmpeg.

## Preview

The live preview is a lightweight path (PIL / canvas projection) so the UI stays responsive. It is meant to match the export look — same placement math, same gradients, same bounce — at a capped size.

## Export

1. Decode audio and analyze spectrum / transients.
2. For each frame, draw the cover, titles, and visualizer.
3. **3D** goes through ModernGL: real meshes (prisms, ribbon, terrain, halo), a perspective camera, Phong lighting, alpha so the still shows through.
4. Frames leave as raw RGB on stdout.
5. FFmpeg reads stdin and writes H.264 + AAC into an MP4.

## GPU encode (Linux)

On AMD (tested path: Radeon RX 6600M) export prefers VA-API:

- Device: `/dev/dri/renderD128`
- Encoder: `h264_vaapi`
- Filtergraph ends in `format=nv12,hwupload`

If the VA-API device is missing, it falls back to `libx264` on the CPU. That fallback is deliberate — a laptop without drivers should still finish a video.

NVIDIA NVENC and Intel QSV are on the [Roadmap](Roadmap). They are not in 1.0.6.

## Why local

The whole point is that the song never leaves the machine. No cloud queue, no watermark tax, no “processing” spinner on someone else’s GPU. Your files, your FFmpeg, your disk.
