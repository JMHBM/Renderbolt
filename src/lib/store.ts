import { create } from "zustand";
import type { ThemeId, VisStyle } from "@/lib/visualizer/types";
import { THEME_IDS, VIS_STYLES } from "@/lib/visualizer/types";
import { THEMES } from "@/lib/visualizer/themes";
import type { AspectId, ResId } from "@/lib/utils";

export type StudioState = {
  song: string;
  artist: string;
  album: string;
  style: VisStyle;
  themeId: ThemeId;
  baseColor: string;
  tipColor: string;
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
  sensitivity: number;
  glow: number;
  vignette: number;
  grain: number;
  titleScale: number;
  titlePos: "top" | "bottom";
  aspect: AspectId;
  res: ResId;
  fadeIn: number;
  fadeOut: number;
  pulseHue: number;
  audioLabel: string;
  imageLabel: string;
  usingDemo: boolean;
  usingDefaultImage: boolean;
  setField: <K extends keyof StudioState>(key: K, value: StudioState[K]) => void;
  setTheme: (id: ThemeId) => void;
  shuffleLook: () => void;
};

export const useStudio = create<StudioState>((set) => ({
  song: "",
  artist: "",
  album: "",
  style: "waveform",
  themeId: "ice",
  baseColor: THEMES.ice.primary,
  tipColor: THEMES.ice.secondary,
  bounce: 1,
  visAlpha: 0.78,
  tilt: 42,
  dim: "3d",
  visX: 0,
  visY: 0,
  visRot: 0,
  visSx: 1,
  visSy: 1,
  mirror: false,
  showTitles: true,
  sensitivity: 1,
  glow: 0.4,
  vignette: 0.55,
  grain: 0.1,
  titleScale: 1,
  titlePos: "bottom",
  aspect: "16:9",
  res: "1080p",
  fadeIn: 0.6,
  fadeOut: 1.2,
  pulseHue: 0,
  audioLabel: "Demo beat",
  imageLabel: "Stage (default)",
  usingDemo: true,
  usingDefaultImage: true,
  setField: (key, value) => set({ [key]: value } as Partial<StudioState>),
  setTheme: (id) =>
    set({
      themeId: id,
      baseColor: THEMES[id].primary,
      tipColor: THEMES[id].secondary,
    }),
  shuffleLook: () =>
    set(() => {
      const id = THEME_IDS[Math.floor(Math.random() * THEME_IDS.length)]!;
      const style = VIS_STYLES[Math.floor(Math.random() * VIS_STYLES.length)]!;
      const bounce = [0.45, 1, 1.45][Math.floor(Math.random() * 3)]!;
      const aspects: AspectId[] = ["16:9", "16:9", "9:16", "1:1"];
      return {
        dim: Math.random() > 0.4 ? "3d" : "2d",
        style,
        themeId: id,
        baseColor: THEMES[id].primary,
        tipColor: THEMES[id].secondary,
        bounce,
        visX: (Math.random() - 0.5) * 0.5,
        visY: (Math.random() - 0.5) * 0.4,
        visRot: [0, 0, 0, 12, 348, 180][Math.floor(Math.random() * 6)]!,
        visSx: 0.85 + Math.random() * 0.4,
        visSy: 0.85 + Math.random() * 0.35,
        glow: 0.2 + Math.random() * 0.5,
        grain: 0.04 + Math.random() * 0.14,
        pulseHue: [0, 0, 24, 48, 90][Math.floor(Math.random() * 5)]!,
        aspect: aspects[Math.floor(Math.random() * aspects.length)]!,
      };
    }),
}));
