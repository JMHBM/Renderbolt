import { AudioWaveform, BarChart3, ChevronDown, Circle, Dices, ImageIcon, Music, Waves } from "lucide-react";
import { FileDrop } from "@/components/studio/file-drop";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { cn } from "@/lib/utils";
import { useStudio } from "@/lib/store";
import { THEME_LIST } from "@/lib/visualizer/themes";
import { STYLE_META, VIS_STYLES, type VisStyle } from "@/lib/visualizer/types";

const STYLE_ICONS: Record<VisStyle, typeof AudioWaveform> = {
  waveform: AudioWaveform,
  eq: BarChart3,
  circular: Circle,
  liquid: Waves,
};

const BOUNCE_PRESETS = [
  { label: "Soft", value: 0.45 },
  { label: "Medium", value: 1 },
  { label: "Hard", value: 1.45 },
] as const;

type ControlPanelProps = {
  imagePreview: string | null;
  onAudioFile: (file: File) => void;
  onImageFile: (file: File) => void;
};

export function ControlPanel({
  imagePreview,
  onAudioFile,
  onImageFile,
}: ControlPanelProps) {
  const studio = useStudio();

  return (
    <div className="flex flex-col gap-5">
      <FileDrop
        accept="audio/*,.mp3,.wav,.flac,.ogg,.m4a,.aac"
        label="Audio"
        hint="MP3, WAV, FLAC, OGG"
        icon={Music}
        fileName={studio.audioLabel}
        onFile={onAudioFile}
      />
      <FileDrop
        accept="image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp"
        label="Background"
        hint="JPG, PNG, WebP"
        icon={ImageIcon}
        fileName={studio.imageLabel}
        previewUrl={imagePreview}
        onFile={onImageFile}
      />

      <Separator />

      <div className="grid gap-3">
        <Field
          id="song"
          label="Song"
          value={studio.song}
          onChange={(v) => studio.setField("song", v)}
          placeholder="Song title"
        />
        <Field
          id="artist"
          label="Artist"
          value={studio.artist}
          onChange={(v) => studio.setField("artist", v)}
          placeholder="Artist name"
        />
        <Field
          id="album"
          label="Album"
          value={studio.album}
          onChange={(v) => studio.setField("album", v)}
          placeholder="Album name"
        />
      </div>

      <Separator />

      <div>
        <p className="mb-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">
          Mode
        </p>
        <div className="grid grid-cols-2 gap-1 rounded-lg bg-muted p-1">
          {(["2d", "3d"] as const).map((d) => (
            <button
              key={d}
              type="button"
              onClick={() => studio.setField("dim", d)}
              className={cn(
                "h-9 rounded-md text-xs font-medium uppercase transition-colors duration-150",
                studio.dim === d ? "bg-secondary text-foreground" : "text-muted-foreground hover:text-foreground",
              )}
            >
              {d}
            </button>
          ))}
        </div>
      </div>

      <div>
        <p className="mb-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">
          Format
        </p>
        <div className="grid grid-cols-3 gap-1 rounded-lg bg-muted p-1">
          {(["16:9", "9:16", "1:1"] as const).map((a) => (
            <button
              key={a}
              type="button"
              onClick={() => studio.setField("aspect", a)}
              className={cn(
                "h-9 rounded-md text-xs font-medium transition-colors duration-150",
                studio.aspect === a ? "bg-secondary text-foreground" : "text-muted-foreground hover:text-foreground",
              )}
            >
              {a}
            </button>
          ))}
        </div>
      </div>

      <div>
        <p className="mb-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">
          Visualizer
        </p>
        <div className="grid grid-cols-2 gap-2">
          {VIS_STYLES.map((id) => {
            const Icon = STYLE_ICONS[id];
            const active = studio.style === id;
            return (
              <button
                key={id}
                type="button"
                onClick={() => studio.setField("style", id)}
                className={cn(
                  "flex min-h-11 flex-col items-start gap-1 rounded-lg border px-3 py-2.5 text-left transition-[border-color,background-color] duration-150",
                  active
                    ? "border-ring bg-muted"
                    : "border-border bg-transparent hover:border-ring/40",
                )}
              >
                <span className="flex items-center gap-2 text-sm font-medium text-foreground">
                  <Icon className="size-4 text-ice" />
                  {STYLE_META[id].label}
                </span>
                <span className="text-xs leading-snug text-muted-foreground">
                  {STYLE_META[id].blurb}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      <button
        type="button"
        onClick={() => studio.shuffleLook()}
        className="flex h-11 w-full items-center justify-center gap-2 rounded-lg border border-border bg-muted text-sm font-medium text-foreground hover:border-ring/40"
      >
        <Dices className="size-4 text-ice" />
        Shuffle look
      </button>

      <Collapsible>
        <CollapsibleTrigger className="group flex h-11 w-full items-center justify-between rounded-md px-1 text-sm font-medium text-foreground hover:bg-muted">
          Advanced
          <ChevronDown className="size-4 text-muted-foreground transition-transform duration-200 group-data-[state=open]:rotate-180" />
        </CollapsibleTrigger>
        <CollapsibleContent className="flex flex-col gap-4 pt-2">
          <div>
            <p className="mb-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">
              Color theme
            </p>
            <div className="flex flex-wrap gap-2">
              {THEME_LIST.map((theme) => {
                const active = studio.themeId === theme.id;
                return (
                  <button
                    key={theme.id}
                    type="button"
                    title={theme.label}
                    onClick={() => studio.setTheme(theme.id)}
                    className={cn(
                      "flex h-11 items-center gap-2 rounded-full border px-3 transition-[border-color] duration-150",
                      active ? "border-ring" : "border-border hover:border-ring/40",
                    )}
                  >
                    <span
                      className="size-3.5 rounded-full"
                      style={{
                        background: `linear-gradient(135deg, ${theme.primary}, ${theme.secondary})`,
                      }}
                    />
                    <span className="text-xs font-medium">{theme.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <p className="mb-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">
              Gradient · base → tips
            </p>
            <div className="grid grid-cols-2 gap-2">
              <label className="flex h-11 items-center gap-2 rounded-lg border border-border px-2">
                <input
                  type="color"
                  value={studio.baseColor}
                  onChange={(e) => studio.setField("baseColor", e.target.value)}
                  className="size-7 cursor-pointer rounded border-0 bg-transparent"
                  aria-label="Base color"
                />
                <span className="text-xs">Base</span>
              </label>
              <label className="flex h-11 items-center gap-2 rounded-lg border border-border px-2">
                <input
                  type="color"
                  value={studio.tipColor}
                  onChange={(e) => studio.setField("tipColor", e.target.value)}
                  className="size-7 cursor-pointer rounded border-0 bg-transparent"
                  aria-label="Tip color"
                />
                <span className="text-xs">Tips</span>
              </label>
            </div>
          </div>

          <div>
            <p className="mb-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">
              Beat bounce
            </p>
            <div className="grid grid-cols-3 gap-1 rounded-lg bg-muted p-1">
              {BOUNCE_PRESETS.map((p) => (
                <button
                  key={p.label}
                  type="button"
                  onClick={() => studio.setField("bounce", p.value)}
                  className={cn(
                    "h-9 rounded-md text-xs font-medium transition-colors duration-150",
                    studio.bounce === p.value
                      ? "bg-secondary text-foreground"
                      : "text-muted-foreground hover:text-foreground",
                  )}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <p className="mb-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">
              Camera tilt
            </p>
            <input
              type="range"
              min={22}
              max={62}
              step={1}
              value={studio.tilt}
              onChange={(e) => studio.setField("tilt", Number(e.target.value))}
              className="h-11 w-full accent-ice"
              aria-label="Camera tilt"
            />
            <p className="mt-1 text-xs text-muted-foreground">{Math.round(studio.tilt)}° isometric</p>
          </div>

          <div>
            <p className="mb-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">
              Glass
            </p>
            <input
              type="range"
              min={0.25}
              max={1}
              step={0.01}
              value={studio.visAlpha}
              onChange={(e) => studio.setField("visAlpha", Number(e.target.value))}
              className="h-11 w-full accent-ice"
              aria-label="Waveform transparency"
            />
            <p className="mt-1 text-xs text-muted-foreground">
              {Math.round(studio.visAlpha * 100)}% solid — cover bleeds through
            </p>
          </div>

          {(["visX", "visY", "visRot", "visSx", "visSy"] as const).map((key) => {
            const meta = {
              visX: { label: "X axis", min: -1, max: 1, step: 0.01, fmt: (v: number) => v.toFixed(2) },
              visY: { label: "Y axis", min: -1, max: 1, step: 0.01, fmt: (v: number) => v.toFixed(2) },
              visRot: { label: "Rotation", min: 0, max: 360, step: 1, fmt: (v: number) => `${Math.round(v)}°` },
              visSx: { label: "Width", min: 0.35, max: 2.2, step: 0.01, fmt: (v: number) => `${v.toFixed(2)}×` },
              visSy: { label: "Height", min: 0.35, max: 2.2, step: 0.01, fmt: (v: number) => `${v.toFixed(2)}×` },
            }[key];
            return (
              <div key={key}>
                <p className="mb-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">
                  {meta.label}
                </p>
                <input
                  type="range"
                  min={meta.min}
                  max={meta.max}
                  step={meta.step}
                  value={studio[key]}
                  onChange={(e) => studio.setField(key, Number(e.target.value))}
                  className="h-11 w-full accent-ice"
                  aria-label={meta.label}
                />
                <p className="mt-1 text-xs text-muted-foreground">{meta.fmt(studio[key])}</p>
              </div>
            );
          })}

          <label className="flex h-11 items-center justify-between gap-3 rounded-md px-1">
            <span className="text-sm">Mirror</span>
            <button
              type="button"
              role="switch"
              aria-checked={studio.mirror}
              onClick={() => studio.setField("mirror", !studio.mirror)}
              className={cn(
                "relative h-6 w-10 rounded-full transition-colors duration-150",
                studio.mirror ? "bg-primary" : "bg-border",
              )}
            >
              <span
                className={cn(
                  "absolute top-0.5 left-0.5 size-5 rounded-full bg-background transition-transform duration-150",
                  studio.mirror && "translate-x-4",
                )}
              />
            </button>
          </label>

          <label className="flex h-11 items-center justify-between gap-3 rounded-md px-1">
            <span className="text-sm">Show titles on video</span>
            <button
              type="button"
              role="switch"
              aria-checked={studio.showTitles}
              onClick={() => studio.setField("showTitles", !studio.showTitles)}
              className={cn(
                "relative h-6 w-10 rounded-full transition-colors duration-150",
                studio.showTitles ? "bg-primary" : "bg-border",
              )}
            >
              <span
                className={cn(
                  "absolute top-0.5 left-0.5 size-5 rounded-full bg-background transition-transform duration-150",
                  studio.showTitles && "translate-x-4",
                )}
              />
            </button>
          </label>

          {([
            ["sensitivity", "Beat sensitivity", 0.4, 2.2, 0.01, (v: number) => `${v.toFixed(2)}×`],
            ["glow", "Glow", 0, 1, 0.01, (v: number) => `${Math.round(v * 100)}%`],
            ["vignette", "Vignette", 0, 1, 0.01, (v: number) => `${Math.round(v * 100)}%`],
            ["grain", "Film grain", 0, 0.45, 0.01, (v: number) => `${Math.round(v * 100)}%`],
            ["titleScale", "Title size", 0.6, 1.8, 0.01, (v: number) => `${v.toFixed(2)}×`],
            ["pulseHue", "Pulse hue", 0, 180, 1, (v: number) => `${Math.round(v)}°`],
            ["fadeIn", "Fade in", 0, 4, 0.1, (v: number) => `${v.toFixed(1)}s`],
            ["fadeOut", "Fade out", 0, 6, 0.1, (v: number) => `${v.toFixed(1)}s`],
          ] as const).map(([key, label, min, max, step, fmt]) => (
            <div key={key}>
              <p className="mb-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">{label}</p>
              <input
                type="range"
                min={min}
                max={max}
                step={step}
                value={studio[key]}
                onChange={(e) => studio.setField(key, Number(e.target.value))}
                className="h-11 w-full accent-ice"
                aria-label={label}
              />
              <p className="mt-1 text-xs text-muted-foreground">{fmt(studio[key])}</p>
            </div>
          ))}

          <div>
            <p className="mb-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">
              Title position
            </p>
            <div className="grid grid-cols-2 gap-1 rounded-lg bg-muted p-1">
              {(["bottom", "top"] as const).map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => studio.setField("titlePos", p)}
                  className={cn(
                    "h-9 rounded-md text-xs font-medium capitalize transition-colors duration-150",
                    studio.titlePos === p ? "bg-secondary text-foreground" : "text-muted-foreground hover:text-foreground",
                  )}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          <div>
            <p className="mb-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">
              Export quality
            </p>
            <div className="grid grid-cols-3 gap-1 rounded-lg bg-muted p-1">
              {(["720p", "1080p", "4K"] as const).map((r) => (
                <button
                  key={r}
                  type="button"
                  onClick={() => studio.setField("res", r)}
                  className={cn(
                    "h-9 rounded-md text-xs font-medium transition-colors duration-150",
                    studio.res === r ? "bg-secondary text-foreground" : "text-muted-foreground hover:text-foreground",
                  )}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>
        </CollapsibleContent>
      </Collapsible>
    </div>
  );
}

function Field({
  id,
  label,
  value,
  onChange,
  placeholder,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder: string;
}) {
  return (
    <div className="grid gap-1.5">
      <Label htmlFor={id}>{label}</Label>
      <Input
        id={id}
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        autoComplete="off"
      />
    </div>
  );
}
