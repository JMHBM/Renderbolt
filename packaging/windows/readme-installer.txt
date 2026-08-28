Renderbolt 1.0.8 for Windows
Copyright (c) 2026 JMHBM, Grok (xAI), and Jan-4B-Base-Instruct (Menlo Labs Research)
Equal copyright · Creative Commons Attribution 4.0 International

This is a native Windows studio (Edge WebView2), not the Linux Tk app.
Windows 11 includes WebView2. On Windows 10, install the Evergreen runtime
from Microsoft if the window is blank.

This build bundles FFmpeg.

Hardware encode (when the driver is present):
  AMD     h264_amf
  NVIDIA  h264_nvenc
  Intel   h264_qsv
Otherwise it falls back to CPU (libx264).

The live preview is the picture on screen. Generate writes the MP4.

Your files stay on this machine. No account, no upload.

