import type { ThemeId, VisTheme } from "./types";

export const THEMES: Record<ThemeId, VisTheme> = {
  ice: { id: "ice", label: "Ice", primary: "#156a96", secondary: "#b8ecff", glow: "#5ad0ff" },
  ember: { id: "ember", label: "Ember", primary: "#8a2208", secondary: "#ffb070", glow: "#ff6a1a" },
  forest: { id: "forest", label: "Forest", primary: "#0d5c38", secondary: "#9ef0c0", glow: "#22c47a" },
  midnight: { id: "midnight", label: "Midnight", primary: "#1e2a8a", secondary: "#b8c4ff", glow: "#6a78ff" },
  mono: { id: "mono", label: "Mono", primary: "#2a2a2c", secondary: "#f0ece4", glow: "#c8c4bc" },
  rose: { id: "rose", label: "Rose", primary: "#8a1848", secondary: "#ff9ec0", glow: "#ff4d6d" },
  violet: { id: "violet", label: "Violet", primary: "#4a148c", secondary: "#e0b0ff", glow: "#a855f0" },
  gold: { id: "gold", label: "Gold", primary: "#8a5a00", secondary: "#ffe08a", glow: "#ffc400" },
  cyan: { id: "cyan", label: "Cyan", primary: "#046060", secondary: "#7dfff0", glow: "#12d0c8" },
  crimson: { id: "crimson", label: "Crimson", primary: "#7a1020", secondary: "#ff6a7a", glow: "#ff4d6d" },
  ocean: { id: "ocean", label: "Ocean", primary: "#023e6b", secondary: "#5ad0ff", glow: "#1e90d0" },
  sunset: { id: "sunset", label: "Sunset", primary: "#c43c08", secondary: "#ffd0a0", glow: "#ff6a1a" },
};

export const THEME_LIST: VisTheme[] = Object.values(THEMES);
