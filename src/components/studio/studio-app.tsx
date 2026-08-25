import { useCallback, useEffect, useRef, useState } from "react";
import {
  Download,
  Loader2,
  Pause,
  Play,
  FileVideo,
} from "lucide-react";
import { toast, Toaster } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Progress } from "@/components/ui/progress";
import { ControlPanel } from "@/components/studio/control-panel";
import { Wordmark } from "@/components/studio/logo";
import { useStudio } from "@/lib/store";
import { formatTimecode, frameSize } from "@/lib/utils";
import {
  BeatDetector,
  analyzeBufferAt,
  createScratch,
  idleAnalysis,
} from "@/lib/visualizer/audio-analysis";
import { createDemoBuffer } from "@/lib/visualizer/demo-audio";
import { exportVisualizerMp4 } from "@/lib/visualizer/export-mp4";
import { VisualizerEngine } from "@/lib/visualizer/renderer";
import { THEMES } from "@/lib/visualizer/themes";

const DEFAULT_COVER = "/samples/stage.jpg";
const RPM_HREF = "/downloads/renderbolt-1.0.6-1.fc44.noarch.rpm";
const DEB_HREF = "/downloads/renderbolt_1.0.6_all.deb";

function loadImage(url: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error("Could not load image"));
    img.src = url;
  });
}

function slugify(name: string): string {
  const s = name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
  return s || "renderbolt";
}

export function StudioApp() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const engineRef = useRef(new VisualizerEngine());
  const scratchRef = useRef(createScratch());
  const detectorRef = useRef(new BeatDetector());
  const imageRef = useRef<HTMLImageElement | null>(null);
  const bufferRef = useRef<AudioBuffer | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const sourceRef = useRef<AudioBufferSourceNode | null>(null);
  const playingRef = useRef(false);
  const pausePosRef = useRef(0);
  const startedAtRef = useRef(0);
  const rafRef = useRef(0);
  const lastTsRef = useRef(0);
  const objectUrlsRef = useRef<string[]>([]);
  const abortRef = useRef<AbortController | null>(null);
  const exportingRef = useRef(false);

  const [ready, setReady] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(16);
  const [imagePreview, setImagePreview] = useState(DEFAULT_COVER);
  const [exportOpen, setExportOpen] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState(0);
  const [exportLabel, setExportLabel] = useState("Preparing");
  const [resultUrl, setResultUrl] = useState<string | null>(null);
  const [resultName, setResultName] = useState("renderbolt.mp4");
  const [licenseOpen, setLicenseOpen] = useState(false);
  const [rpmOpen, setRpmOpen] = useState(false);

  const setField = useStudio((s) => s.setField);

  const getCtx = useCallback(() => {
    if (!audioCtxRef.current) {
      audioCtxRef.current = new AudioContext();
    }
    return audioCtxRef.current;
  }, []);

  const stopSource = useCallback(() => {
    const src = sourceRef.current;
    sourceRef.current = null;
    if (src) {
      try {
        src.onended = null;
        src.stop();
      } catch {
        /* already stopped */
      }
    }
  }, []);

  const drawFrame = useCallback((time: number, dt: number, useIdle: boolean) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const state = useStudio.getState();
    const buffer = bufferRef.current;
    const analysis =
      buffer && !useIdle
        ? analyzeBufferAt(
            buffer,
            Math.min(time, buffer.duration),
            scratchRef.current,
            detectorRef.current,
            dt,
            state.sensitivity,
          )
        : idleAnalysis(scratchRef.current, detectorRef.current, time, state.sensitivity);

    engineRef.current.render(
      ctx,
      canvas.width,
      canvas.height,
      {
        image: imageRef.current,
        analysis,
        currentTime: buffer ? Math.min(time, buffer.duration) : 0,
        duration: buffer?.duration ?? 0,
        style: state.style,
        theme: {
          ...THEMES[state.themeId],
          primary: state.baseColor,
          secondary: state.tipColor,
        },
        song: state.song,
        artist: state.artist,
        album: state.album,
        bounce: state.bounce,
        visAlpha: state.visAlpha,
        tilt: state.tilt,
        dim: state.dim,
        visX: state.visX,
        visY: state.visY,
        visRot: state.visRot,
        visSx: state.visSx,
        visSy: state.visSy,
        mirror: state.mirror,
        showTitles: state.showTitles,
        glow: state.glow,
        vignette: state.vignette,
        grain: state.grain,
        titleScale: state.titleScale,
        titlePos: state.titlePos,
        fadeIn: state.fadeIn,
        fadeOut: state.fadeOut,
        pulseHue: state.pulseHue,
      },
      dt,
    );
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [img, buffer] = await Promise.all([
          loadImage(DEFAULT_COVER),
          createDemoBuffer(),
        ]);
        if (cancelled) return;
        imageRef.current = img;
        bufferRef.current = buffer;
        setDuration(buffer.duration);
        setReady(true);
      } catch (err) {
        console.error(err);
        toast.error("Could not start the studio.");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const aspect = useStudio((s) => s.aspect);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const preview = frameSize(aspect, "720p");
    canvas.width = preview.w;
    canvas.height = preview.h;

    const tick = (now: number) => {
      if (exportingRef.current) {
        rafRef.current = requestAnimationFrame(tick);
        return;
      }
      const last = lastTsRef.current || now;
      const dt = Math.min(0.05, (now - last) / 1000);
      lastTsRef.current = now;

      const buffer = bufferRef.current;
      let t = pausePosRef.current;
      if (playingRef.current && audioCtxRef.current) {
        t = pausePosRef.current + (audioCtxRef.current.currentTime - startedAtRef.current);
        if (buffer && t >= buffer.duration) {
          t = buffer.duration;
          playingRef.current = false;
          setPlaying(false);
          stopSource();
          pausePosRef.current = 0;
        }
      }
      setCurrentTime(t);
      const idle = !buffer || (!playingRef.current && pausePosRef.current === 0 && t === 0);
      drawFrame(idle ? now / 1000 : t, dt, idle);
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [drawFrame, stopSource, aspect]);

  const play = useCallback(async () => {
    const buffer = bufferRef.current;
    if (!buffer) return;
    const ctx = getCtx();
    if (ctx.state === "suspended") await ctx.resume();
    stopSource();
    if (pausePosRef.current >= buffer.duration - 0.05) {
      pausePosRef.current = 0;
    }
    const src = ctx.createBufferSource();
    src.buffer = buffer;
    src.connect(ctx.destination);
    src.onended = () => {
      if (sourceRef.current !== src) return;
      sourceRef.current = null;
      playingRef.current = false;
      setPlaying(false);
      pausePosRef.current = 0;
      setCurrentTime(0);
    };
    src.start(0, pausePosRef.current);
    sourceRef.current = src;
    startedAtRef.current = ctx.currentTime;
    playingRef.current = true;
    setPlaying(true);
  }, [getCtx, stopSource]);

  const pause = useCallback(() => {
    if (playingRef.current && audioCtxRef.current) {
      pausePosRef.current += audioCtxRef.current.currentTime - startedAtRef.current;
    }
    playingRef.current = false;
    setPlaying(false);
    stopSource();
  }, [stopSource]);

  const togglePlay = useCallback(() => {
    if (playingRef.current) pause();
    else void play();
  }, [pause, play]);

  const seekTo = useCallback(
    (t: number) => {
      const buf = bufferRef.current;
      if (!buf) return;
      const next = Math.max(0, Math.min(buf.duration - 0.01, t));
      pausePosRef.current = next;
      setCurrentTime(next);
      if (playingRef.current) void play();
    },
    [play],
  );

  const seekBy = useCallback((dt: number) => seekTo(pausePosRef.current + dt), [seekTo]);

  const onAudioFile = useCallback(
    async (file: File) => {
      try {
        pause();
        const ctx = getCtx();
        const copy = await file.arrayBuffer();
        const decoded = await ctx.decodeAudioData(copy);
        bufferRef.current = decoded;
        pausePosRef.current = 0;
        setCurrentTime(0);
        setDuration(decoded.duration);
        detectorRef.current.reset();
        const wasDemo = useStudio.getState().usingDemo;
        setField("audioLabel", file.name);
        setField("usingDemo", false);
        toast.success("Audio loaded");
      } catch (err) {
        console.error(err);
        toast.error("Could not read that audio file.");
      }
    },
    [getCtx, pause, setField],
  );

  const onImageFile = useCallback(
    async (file: File) => {
      try {
        const url = URL.createObjectURL(file);
        objectUrlsRef.current.push(url);
        const img = await loadImage(url);
        imageRef.current = img;
        setImagePreview(url);
        setField("imageLabel", file.name);
        setField("usingDefaultImage", false);
        toast.success("Background loaded");
      } catch (err) {
        console.error(err);
        toast.error("Could not read that image.");
      }
    },
    [setField],
  );

  const generate = useCallback(async () => {
    const canvas = canvasRef.current;
    const buffer = bufferRef.current;
    if (!canvas || !buffer) return;
    pause();
    abortRef.current?.abort();
    const ac = new AbortController();
    abortRef.current = ac;
    exportingRef.current = true;
    setResultUrl(null);
    setExportOpen(true);
    setExporting(true);
    setExportProgress(0);
    setExportLabel("Preparing encoder");

    const exportEngine = new VisualizerEngine();
    const exportDetector = new BeatDetector();
    const exportScratch = createScratch();
    const state = useStudio.getState();
    const name = `${slugify(state.song)}.mp4`;
    setResultName(name);

    const size = frameSize(state.aspect, state.res);
    const prevW = canvas.width;
    const prevH = canvas.height;
    canvas.width = size.w;
    canvas.height = size.h;

    try {
      const blob = await exportVisualizerMp4({
        canvas,
        duration: buffer.duration,
        audioBuffer: buffer,
        signal: ac.signal,
        onProgress: (p, label) => {
          setExportProgress(Math.round(p * 100));
          setExportLabel(label);
        },
        drawFrame: (time) => {
          const ctx = canvas.getContext("2d");
          if (!ctx) return;
          const analysis = analyzeBufferAt(
            buffer,
            time,
            exportScratch,
            exportDetector,
            1 / 30,
            state.sensitivity,
          );
          exportEngine.render(
            ctx,
            canvas.width,
            canvas.height,
            {
              image: imageRef.current,
              analysis,
              currentTime: time,
              duration: buffer.duration,
              style: state.style,
              theme: {
                ...THEMES[state.themeId],
                primary: state.baseColor,
                secondary: state.tipColor,
              },
              song: state.song,
              artist: state.artist,
              album: state.album,
              bounce: state.bounce,
              visAlpha: state.visAlpha,
              tilt: state.tilt,
              dim: state.dim,
              visX: state.visX,
              visY: state.visY,
              visRot: state.visRot,
              visSx: state.visSx,
              visSy: state.visSy,
              mirror: state.mirror,
              showTitles: state.showTitles,
              glow: state.glow,
              vignette: state.vignette,
              grain: state.grain,
              titleScale: state.titleScale,
              titlePos: state.titlePos,
              fadeIn: state.fadeIn,
              fadeOut: state.fadeOut,
              pulseHue: state.pulseHue,
            },
            1 / 30,
          );
        },
      });
      const url = URL.createObjectURL(blob);
      objectUrlsRef.current.push(url);
      setResultUrl(url);
      const a = document.createElement("a");
      a.href = url;
      a.download = name;
      a.click();
      toast.success("MP4 ready");
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      console.error(err);
      toast.error(err instanceof Error ? err.message : "Export failed");
      setExportOpen(false);
    } finally {
      canvas.width = prevW;
      canvas.height = prevH;
      exportingRef.current = false;
      setExporting(false);
      engineRef.current.reset();
      detectorRef.current.reset();
    }
  }, [pause]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const tag = (e.target as HTMLElement | null)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA") return;
      if (e.code === "Space") {
        e.preventDefault();
        togglePlay();
        return;
      }
      if (e.key === "g" || e.key === "G") {
        e.preventDefault();
        void generate();
        return;
      }
      if (e.key === "r" || e.key === "R") {
        e.preventDefault();
        useStudio.getState().shuffleLook();
      }
      if (e.code === "ArrowLeft") {
        e.preventDefault();
        seekBy(-2);
      }
      if (e.code === "ArrowRight") {
        e.preventDefault();
        seekBy(2);
      }
      if (e.code === "Home") {
        e.preventDefault();
        seekTo(0);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [togglePlay, generate, seekBy, seekTo]);

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
      stopSource();
      objectUrlsRef.current.forEach((u) => URL.revokeObjectURL(u));
      void audioCtxRef.current?.close();
    };
  }, [stopSource]);

  return (
    <div className="flex min-h-dvh flex-col bg-background">
      <Toaster theme="dark" position="bottom-right" richColors={false} />
      <header className="flex h-16 shrink-0 items-center justify-between gap-3 border-b border-border px-4 sm:px-6">
        <Wordmark />
        <div className="flex items-center gap-1 sm:gap-2">
          <Button variant="ghost" size="sm" asChild>
            <a
              href={RPM_HREF}
              download
              onClick={() => setRpmOpen(true)}
            >
              <Download />
              <span className="hidden sm:inline">Fedora RPM</span>
              <span className="sm:hidden">RPM</span>
            </a>
          </Button>
          <Button variant="ghost" size="sm" asChild>
            <a href={DEB_HREF} download>
              <span className="hidden md:inline">Debian .deb</span>
            </a>
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setLicenseOpen(true)}>
            CC BY 4.0
          </Button>
        </div>
      </header>

      <main className="mx-auto grid w-full max-w-7xl flex-1 grid-cols-1 gap-6 p-4 sm:p-6 lg:grid-cols-[20rem_minmax(0,1fr)] lg:gap-8">
        <aside className="rounded-xl border border-border bg-card p-4 sm:p-5">
          <p className="font-display mb-4 text-sm tracking-[0.16em] text-muted-foreground">
            STUDIO
          </p>
          <ControlPanel
            imagePreview={imagePreview}
            onAudioFile={onAudioFile}
            onImageFile={onImageFile}
          />
        </aside>

        <section className="flex min-w-0 flex-col gap-4">
          <div className="overflow-hidden rounded-xl border border-border bg-card p-2 sm:p-3">
            <div
              className={
                aspect === "9:16"
                  ? "relative mx-auto aspect-[9/16] max-h-[72vh] w-auto overflow-hidden rounded-lg bg-background"
                  : aspect === "1:1"
                    ? "relative mx-auto aspect-square max-h-[72vh] w-full max-w-[72vh] overflow-hidden rounded-lg bg-background"
                    : "relative aspect-video overflow-hidden rounded-lg bg-background"
              }
            >
              <canvas
                ref={canvasRef}
                className="h-full w-full object-contain"
                aria-label="Visualizer preview"
              />
              {!ready && (
                <div className="absolute inset-0 flex items-center justify-center text-sm text-muted-foreground">
                  Loading stage
                </div>
              )}
            </div>
          </div>

          <div className="flex flex-col gap-3 rounded-xl border border-border bg-card p-3 sm:flex-row sm:items-center sm:p-4">
            <div className="flex flex-1 items-center gap-3">
              <Button
                type="button"
                variant="secondary"
                size="icon"
                onClick={togglePlay}
                disabled={!ready || exporting}
                aria-label={playing ? "Pause" : "Play"}
              >
                {playing ? <Pause /> : <Play className="ml-0.5" />}
              </Button>
              <div className="min-w-0 flex-1">
                <div
                  className="h-1.5 cursor-pointer overflow-hidden rounded-full bg-muted"
                  onClick={(e) => {
                    const r = e.currentTarget.getBoundingClientRect();
                    const p = (e.clientX - r.left) / Math.max(1, r.width);
                    seekTo(p * duration);
                  }}
                >
                  <div
                    className="h-full bg-primary"
                    style={{
                      width: `${duration > 0 ? (currentTime / duration) * 100 : 0}%`,
                    }}
                  />
                </div>
                <p className="mt-1.5 font-mono text-xs tabular-nums text-muted-foreground">
                  {formatTimecode(currentTime)} / {formatTimecode(duration)}
                </p>
              </div>
            </div>
            <Button
              type="button"
              size="lg"
              className="w-full sm:w-auto"
              onClick={() => void generate()}
              disabled={!ready || exporting}
            >
              {exporting ? <Loader2 className="animate-spin" /> : <FileVideo />}
              Generate MP4
            </Button>
          </div>
        </section>
      </main>

      <footer className="mt-auto border-t border-border px-4 py-4 sm:px-6">
        <p className="text-xs text-muted-foreground">
          Renderbolt · Designed by JMHBM · Licensed under{" "}
          <button
            type="button"
            className="underline decoration-border underline-offset-2 hover:text-foreground"
            onClick={() => setLicenseOpen(true)}
          >
            Creative Commons Attribution 4.0 International
          </button>
        </p>
      </footer>

      <Dialog
        open={exportOpen}
        onOpenChange={(open) => {
          if (!open && exporting) abortRef.current?.abort();
          setExportOpen(open);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{resultUrl ? "Your video" : "Generating"}</DialogTitle>
            <DialogDescription>
              {resultUrl
                ? "1080p MP4 with burned-in progress bar. The file also downloaded to your device."
                : exportLabel}
            </DialogDescription>
          </DialogHeader>
          {exporting && (
            <div className="grid gap-2">
              <Progress value={exportProgress} />
              <p className="text-xs tabular-nums text-muted-foreground">
                {exportProgress}%
              </p>
            </div>
          )}
          {resultUrl && (
            <div className="grid gap-3">
              <video
                src={resultUrl}
                controls
                playsInline
                className="w-full rounded-lg bg-background"
              />
              <Button asChild>
                <a href={resultUrl} download={resultName}>
                  <Download />
                  Download {resultName}
                </a>
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={rpmOpen} onOpenChange={setRpmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Install on Fedora Silverblue</DialogTitle>
            <DialogDescription>
              Re-download this build (1.0.0-2). The first RPM used header tags Fedora 44
              rejects, which is why rpm-ostree said verification failed.
            </DialogDescription>
          </DialogHeader>
          <ol className="list-decimal space-y-2 pl-4 text-sm text-muted-foreground">
            <li>Save the new file. It is named renderbolt-1.0.0-2.fc44.noarch.rpm.</li>
            <li>
              Layer it with{" "}
              <code className="text-foreground">rpm-ostree install</code> pointing at that
              file, then reboot.
            </li>
            <li>
              Workstation Fedora can{" "}
              <code className="text-foreground">dnf install</code> the same file.
            </li>
          </ol>
          <p className="text-sm text-muted-foreground">
            Dependencies (Python, Tkinter, Pillow, NumPy, ffmpeg-free) are pulled in
            automatically. On Workstation, that is enough. On Silverblue they layer with the
            package.
          </p>
          <Button asChild>
            <a href={RPM_HREF} download>
              <Download />
              Download RPM again
            </a>
          </Button>
        </DialogContent>
      </Dialog>

      <Dialog open={licenseOpen} onOpenChange={setLicenseOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Creative Commons 4.0</DialogTitle>
            <DialogDescription>
              Renderbolt is licensed under CC BY 4.0. Credit JMHBM when you share or adapt it.
            </DialogDescription>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">
            You are free to share and adapt this work for any purpose, even commercially, as
            long as you give appropriate credit, provide a link to the license, and indicate
            if changes were made.
          </p>
          <a
            className="text-sm text-ice underline underline-offset-2"
            href="https://creativecommons.org/licenses/by/4.0/"
            target="_blank"
            rel="noreferrer"
          >
            Read the full license
          </a>
        </DialogContent>
      </Dialog>
    </div>
  );
}
