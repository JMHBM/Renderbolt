export const VIS_STYLES = ["waveform", "eq", "circular", "liquid"] as const;
export type VisStyle = (typeof VIS_STYLES)[number];

export const THEME_IDS = [
  "ice",
  "ember",
  "forest",
  "midnight",
  "mono",
  "rose",
  "violet",
  "gold",
  "cyan",
  "crimson",
  "ocean",
  "sunset",
] as const;
export type ThemeId = (typeof THEME_IDS)[number];

export type VisTheme = {
  id: ThemeId;
  label: string;
  primary: string;
  secondary: string;
  glow: string;
};

export type FrameAnalysis = {
  timeDomain: Float32Array;
  bands: Float32Array;
  bass: number;
  mid: number;
  treble: number;
  rms: number;
  pulse: number;
};

export type RenderInput = {
  image: CanvasImageSource | null;
  analysis: FrameAnalysis;
  currentTime: number;
  duration: number;
  style: VisStyle;
  theme: VisTheme;
  song: string;
  artist: string;
  album: string;
  bounce: number;
  visAlpha: number;
  tilt: number;
  dim: "2d" | "3d";
  visX: number;
  visY: number;
  visRot: number;
  visSx: number;
  visSy: number;
  mirror: boolean;
  showTitles: boolean;
  glow: number;
  vignette: number;
  grain: number;
  titleScale: number;
  titlePos: "top" | "bottom";
  fadeIn: number;
  fadeOut: number;
  pulseHue: number;
};

export const STYLE_META: Record<VisStyle, { label: string; blurb: string }> = {
  waveform: { label: "Waveform", blurb: "Amplitude ribbon" },
  eq: { label: "EQ bars", blurb: "Log-spaced spectrum" },
  circular: { label: "Circular", blurb: "Radial ring" },
  liquid: { label: "Liquid", blurb: "Layered fluid" },
};
