import { clamp, ellipsize, fadeGain, formatTimecode, hueShift, lerp, rgba } from "@/lib/utils";
import type { RenderInput } from "./types";

const EXPORT_W = 1920;
const EXPORT_H = 1080;

export class VisualizerEngine {
  zoom = 1.12;
  peaks = new Float64Array(96);
  waveSmooth = new Float64Array(2048);
  liquidPhase = 0;

  reset() {
    this.zoom = 1.12;
    this.peaks.fill(0);
    this.waveSmooth.fill(0);
    this.liquidPhase = 0;
  }

  render(
    ctx: CanvasRenderingContext2D,
    w: number,
    h: number,
    input: RenderInput,
    dt: number,
  ) {
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = "#0a0a0b";
    ctx.fillRect(0, 0, w, h);

    const pulse = input.analysis.pulse * input.bounce;
    const hueDeg = input.pulseHue * (0.25 + input.analysis.pulse);
    const themed =
      input.pulseHue > 1
        ? {
            ...input.theme,
            primary: hueShift(input.theme.primary, hueDeg),
            secondary: hueShift(input.theme.secondary, hueDeg),
            glow: hueShift(input.theme.glow, hueDeg),
          }
        : input.theme;
    input = { ...input, theme: themed };
    const targetZoom = 1.1 + pulse * 0.16 + input.analysis.bass * 0.04;
    this.zoom = lerp(this.zoom, targetZoom, Math.min(1, dt * 10));
    this.liquidPhase += dt * (0.35 + input.analysis.rms * 1.2);

    this.drawCover(ctx, w, h, input.image, this.zoom, pulse);
    this.drawEdgeFade(ctx, w, h, pulse);
    this.drawScrim(ctx, w, h);

    ctx.save();
    const cx = w * (0.5 + input.visX * 0.45);
    const cy = h * (0.58 - input.visY * 0.4);
    ctx.translate(cx, cy);
    ctx.rotate((input.visRot * Math.PI) / 180);
    ctx.scale(input.visSx * (input.mirror ? -1 : 1), input.visSy);
    ctx.translate(-w * 0.5, -h * 0.58);

    if (input.dim === "2d") {
      this.draw2d(ctx, w, h, input);
    } else {
      switch (input.style) {
        case "waveform":
          this.drawWaveform(ctx, w, h, input);
          break;
        case "eq":
          this.drawEq(ctx, w, h, input, dt);
          break;
        case "circular":
          this.drawCircular(ctx, w, h, input);
          break;
        case "liquid":
          this.drawLiquid(ctx, w, h, input);
          break;
      }
    }
    ctx.restore();

    if (input.glow > 0.02) {
      const gx = w * (0.5 + input.visX * 0.45);
      const gy = h * (0.58 - input.visY * 0.4);
      const rad = Math.min(w, h) * (0.28 + input.glow * 0.12);
      const bloom = ctx.createRadialGradient(gx, gy, 8, gx, gy, rad);
      bloom.addColorStop(0, rgba(input.theme.secondary, input.glow * 0.28));
      bloom.addColorStop(1, rgba(input.theme.secondary, 0));
      ctx.fillStyle = bloom;
      ctx.fillRect(0, 0, w, h);
    }
    this.drawVignette(ctx, w, h, input.vignette);
    this.drawGrain(ctx, w, h, input.grain, input.currentTime);

    if (input.showTitles) {
      this.drawTitles(ctx, w, h, input);
    }
    this.drawProgress(ctx, w, h, input);
    const g = fadeGain(input.currentTime, input.duration, input.fadeIn, input.fadeOut);
    if (g < 0.999) {
      ctx.fillStyle = `rgba(10,10,11,${1 - g})`;
      ctx.fillRect(0, 0, w, h);
    }
  }

  private drawCover(
    ctx: CanvasRenderingContext2D,
    w: number,
    h: number,
    image: CanvasImageSource | null,
    zoom: number,
    pulse: number,
  ) {
    if (!image) return;
    const iw =
      "naturalWidth" in image && (image as HTMLImageElement).naturalWidth
        ? (image as HTMLImageElement).naturalWidth
        : "width" in image
          ? Number((image as { width: number }).width)
          : w;
    const ih =
      "naturalHeight" in image && (image as HTMLImageElement).naturalHeight
        ? (image as HTMLImageElement).naturalHeight
        : "height" in image
          ? Number((image as { height: number }).height)
          : h;
    if (!iw || !ih) return;

    const scale = Math.max(w / iw, h / ih) * zoom;
    const dw = iw * scale;
    const dh = ih * scale;
    const dx = (w - dw) / 2;
    const dy = (h - dh) / 2 + pulse * h * -0.008;

    ctx.save();
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = "high";
    ctx.drawImage(image, dx, dy, dw, dh);
    ctx.restore();
  }

  private drawEdgeFade(
    ctx: CanvasRenderingContext2D,
    w: number,
    h: number,
    pulse: number,
  ) {
    const inner = 0.22 - pulse * 0.08;
    const outerA = 0.55 + pulse * 0.4;
    const g = ctx.createRadialGradient(
      w / 2,
      h / 2,
      Math.min(w, h) * inner,
      w / 2,
      h / 2,
      Math.max(w, h) * 0.72,
    );
    g.addColorStop(0, "rgba(10,10,11,0)");
    g.addColorStop(0.55, `rgba(10,10,11,${0.18 + pulse * 0.12})`);
    g.addColorStop(1, `rgba(10,10,11,${outerA})`);
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);

    const side = ctx.createLinearGradient(0, 0, w, 0);
    const edge = 0.12 + pulse * 0.1;
    side.addColorStop(0, `rgba(10,10,11,${edge + 0.25})`);
    side.addColorStop(0.12, "rgba(10,10,11,0)");
    side.addColorStop(0.88, "rgba(10,10,11,0)");
    side.addColorStop(1, `rgba(10,10,11,${edge + 0.25})`);
    ctx.fillStyle = side;
    ctx.fillRect(0, 0, w, h);
  }

  private drawVignette(ctx: CanvasRenderingContext2D, w: number, h: number, amount: number) {
    if (amount <= 0.01) return;
    const g = ctx.createRadialGradient(
      w / 2,
      h / 2,
      Math.min(w, h) * 0.25,
      w / 2,
      h / 2,
      Math.min(w, h) * 0.78,
    );
    g.addColorStop(0, "rgba(0,0,0,0)");
    g.addColorStop(1, `rgba(0,0,0,${0.72 * amount})`);
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);
  }

  private grainCanvas: HTMLCanvasElement | null = null;
  private drawGrain(
    ctx: CanvasRenderingContext2D,
    w: number,
    h: number,
    amount: number,
    t: number,
  ) {
    if (amount <= 0.01) return;
    if (!this.grainCanvas) {
      const c = document.createElement("canvas");
      c.width = 128;
      c.height = 128;
      const gctx = c.getContext("2d");
      if (gctx) {
        const img = gctx.createImageData(128, 128);
        for (let i = 0; i < img.data.length; i += 4) {
          const n = 128 + Math.random() * 80;
          img.data[i] = n;
          img.data[i + 1] = n;
          img.data[i + 2] = n;
          img.data[i + 3] = 255;
        }
        gctx.putImageData(img, 0, 0);
      }
      this.grainCanvas = c;
    }
    ctx.save();
    ctx.globalAlpha = amount * 0.22;
    ctx.globalCompositeOperation = "overlay";
    const ox = Math.floor((t * 30) % 40);
    ctx.drawImage(this.grainCanvas, -ox, -ox, w + 80, h + 80);
    ctx.restore();
  }

  private drawScrim(ctx: CanvasRenderingContext2D, w: number, h: number) {
    const g = ctx.createLinearGradient(0, h * 0.45, 0, h);
    g.addColorStop(0, "rgba(10,10,11,0)");
    g.addColorStop(0.45, "rgba(10,10,11,0.25)");
    g.addColorStop(1, "rgba(10,10,11,0.78)");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);
  }

  private draw2d(
    ctx: CanvasRenderingContext2D,
    w: number,
    h: number,
    input: RenderInput,
  ) {
    const a = input.analysis;
    const theme = input.theme;
    ctx.save();
    ctx.globalAlpha = input.visAlpha;
    if (input.style === "eq") {
      const bars = 56;
      const padX = w * 0.08;
      const avail = w - padX * 2;
      const gap = avail * 0.006;
      const bw = (avail - gap * (bars - 1)) / bars;
      const baseY = h * 0.74;
      const maxH = h * 0.38;
      for (let i = 0; i < bars; i++) {
        const v = a.bands[Math.floor((i / (bars - 1)) * (a.bands.length - 1))] ?? 0;
        const bh = Math.max(4, v * maxH);
        const x = padX + i * (bw + gap);
        const g = ctx.createLinearGradient(x, baseY, x, baseY - bh);
        g.addColorStop(0, theme.primary);
        g.addColorStop(1, theme.secondary);
        ctx.fillStyle = g;
        ctx.fillRect(x, baseY - bh, bw, bh);
      }
    } else if (input.style === "circular") {
      const cx = w * 0.5;
      const cy = h * 0.46;
      const inner = Math.min(w, h) * (0.16 + a.pulse * 0.02);
      const maxLen = Math.min(w, h) * 0.2;
      const n = 96;
      ctx.beginPath();
      ctx.arc(cx, cy, inner, 0, Math.PI * 2);
      ctx.strokeStyle = theme.secondary;
      ctx.lineWidth = 3;
      ctx.stroke();
      for (let i = 0; i < n; i++) {
        const v = a.bands[Math.floor((i / n) * a.bands.length) % a.bands.length] ?? 0;
        const ang = (i / n) * Math.PI * 2 - Math.PI / 2;
        const len = inner + Math.max(8, v * maxLen);
        ctx.strokeStyle = theme.secondary;
        ctx.globalAlpha = input.visAlpha * (0.45 + v * 0.55);
        ctx.beginPath();
        ctx.moveTo(cx + Math.cos(ang) * inner, cy + Math.sin(ang) * inner);
        ctx.lineTo(cx + Math.cos(ang) * len, cy + Math.sin(ang) * len);
        ctx.stroke();
      }
    } else if (input.style === "liquid") {
      const pts = 48;
      const layers = [
        { amp: 0.09 + a.bass * 0.08, y: 0.7, alpha: 0.35, color: theme.primary },
        { amp: 0.07, y: 0.76, alpha: 0.48, color: theme.glow },
        { amp: 0.05, y: 0.82, alpha: 0.7, color: theme.secondary },
      ];
      for (const layer of layers) {
        ctx.beginPath();
        ctx.moveTo(0, h);
        for (let i = 0; i <= pts; i++) {
          const t = i / pts;
          const band = a.bands[Math.floor(t * (a.bands.length - 1))] ?? 0;
          const y =
            h * layer.y -
            Math.sin(t * Math.PI * 3 + this.liquidPhase * (0.6 + layer.alpha)) * h * layer.amp -
            band * h * 0.05;
          ctx.lineTo(t * w, y);
        }
        ctx.lineTo(w, h);
        ctx.closePath();
        ctx.fillStyle = layer.color;
        ctx.globalAlpha = input.visAlpha * layer.alpha;
        ctx.fill();
      }
    } else {
      const td = a.timeDomain;
      const step = Math.max(1, Math.floor(td.length / 480));
      const count = Math.floor(td.length / step);
      const padX = w * 0.07;
      const midY = h * 0.58;
      const amp = h * (0.14 + a.bass * 0.08);
      ctx.beginPath();
      for (let i = 0; i < count; i++) {
        let s = 0;
        for (let k = 0; k < step; k++) s += td[i * step + k] ?? 0;
        const x = padX + (i / Math.max(1, count - 1)) * (w - padX * 2);
        const y = midY - (s / step) * amp;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      for (let i = count - 1; i >= 0; i--) {
        let s = 0;
        for (let k = 0; k < step; k++) s += td[i * step + k] ?? 0;
        const x = padX + (i / Math.max(1, count - 1)) * (w - padX * 2);
        ctx.lineTo(x, midY + (s / step) * amp * 0.92);
      }
      ctx.closePath();
      ctx.fillStyle = theme.primary;
      ctx.globalAlpha = input.visAlpha * 0.55;
      ctx.fill();
      ctx.globalAlpha = input.visAlpha;
      ctx.strokeStyle = theme.secondary;
      ctx.lineWidth = 3;
      ctx.stroke();
    }
    ctx.restore();
  }

  private project(
    x: number,
    y: number,
    z: number,
    w: number,
    h: number,
    tiltDeg: number,
  ): [number, number] {
    const tilt = (tiltDeg * Math.PI) / 180;
    const yaw = 0.48;
    const cy = Math.cos(yaw);
    const sy = Math.sin(yaw);
    const x1 = x * cy + z * sy;
    const z1 = -x * sy + z * cy;
    const ct = Math.cos(tilt);
    const st = Math.sin(tilt);
    const y2 = y * ct - z1 * st;
    const z2 = y * st + z1 * ct;
    const f = 7.2 / (7.2 + z2);
    const scale = Math.min(w, h) * 0.092;
    return [w * 0.5 + x1 * scale * f, h * 0.62 - y2 * scale * f];
  }

  private fillTri(
    ctx: CanvasRenderingContext2D,
    pts: [number, number][],
    color: string,
  ) {
    ctx.beginPath();
    ctx.moveTo(pts[0]![0], pts[0]![1]);
    ctx.lineTo(pts[1]![0], pts[1]![1]);
    ctx.lineTo(pts[2]![0], pts[2]![1]);
    ctx.closePath();
    ctx.fillStyle = color;
    ctx.fill();
  }

  private drawPrism(
    ctx: CanvasRenderingContext2D,
    ox: number,
    hgt: number,
    oz: number,
    bw: number,
    bd: number,
    w: number,
    h: number,
    tilt: number,
    top: string,
    side: string,
    face: string,
  ) {
    const p = (x: number, y: number, z: number) => this.project(x, y, z, w, h, tilt);
    const a = p(ox, 0, oz);
    const b = p(ox + bw, 0, oz);
    const c = p(ox + bw, 0, oz + bd);
    const e = p(ox, hgt, oz);
    const f = p(ox + bw, hgt, oz);
    const g = p(ox + bw, hgt, oz + bd);
    const hh = p(ox, hgt, oz + bd);
    this.fillTri(ctx, [b, c, g], side);
    this.fillTri(ctx, [b, g, f], side);
    this.fillTri(ctx, [a, b, f], face);
    this.fillTri(ctx, [a, f, e], face);
    this.fillTri(ctx, [e, f, g], top);
    this.fillTri(ctx, [e, g, hh], top);
  }

  private drawWaveform(
    ctx: CanvasRenderingContext2D,
    w: number,
    h: number,
    input: RenderInput,
  ) {
    const td = input.analysis.timeDomain;
    const n = td.length;
    const samples = 96;
    const step = Math.max(1, Math.floor(n / samples));
    if (this.waveSmooth.length < samples) this.waveSmooth = new Float64Array(samples);
    for (let i = 0; i < samples; i++) {
      let sum = 0;
      const base = i * step;
      for (let k = 0; k < step; k++) sum += td[base + k] ?? 0;
      this.waveSmooth[i] = lerp(this.waveSmooth[i] ?? 0, sum / step, 0.4);
    }
    ctx.save();
    ctx.globalAlpha = input.visAlpha;
    for (let i = samples - 2; i >= 0; i--) {
      const t0 = i / (samples - 1);
      const t1 = (i + 1) / (samples - 1);
      const x0 = -5.2 + t0 * 10.4;
      const x1 = -5.2 + t1 * 10.4;
      const y0 = (this.waveSmooth[i] ?? 0) * 2.6;
      const y1 = (this.waveSmooth[i + 1] ?? 0) * 2.6;
      const p = (x: number, y: number, z: number) => this.project(x, y, z, w, h, input.tilt);
      const a = p(x0, y0, -0.7);
      const b = p(x1, y1, -0.7);
      const c = p(x1, y1, 0.7);
      const d = p(x0, y0, 0.7);
      this.fillTri(ctx, [a, b, c], rgba(input.theme.secondary, 0.55));
      this.fillTri(ctx, [a, c, d], rgba(input.theme.primary, 0.7));
    }
    ctx.restore();
  }

  private drawEq(
    ctx: CanvasRenderingContext2D,
    w: number,
    h: number,
    input: RenderInput,
    dt: number,
  ) {
    const bars = 36;
    if (this.peaks.length < bars) this.peaks = new Float64Array(bars);
    const a = input.analysis;
    ctx.save();
    ctx.globalAlpha = input.visAlpha;
    for (let i = bars - 1; i >= 0; i--) {
      const t = i / (bars - 1);
      const src = a.bands[Math.floor(t * (a.bands.length - 1))] ?? 0;
      this.peaks[i] = Math.max(src, (this.peaks[i] ?? 0) - dt * 0.55);
      const hgt = 0.18 + src * 3.6;
      const x = -5.1 + t * 10.2;
      this.drawPrism(
        ctx,
        x,
        hgt,
        -0.35,
        0.2,
        0.7,
        w,
        h,
        input.tilt,
        rgba(input.theme.primary, 0.95),
        rgba(input.theme.secondary, 0.55),
        rgba(input.theme.glow, 0.8),
      );
    }
    ctx.restore();
  }

  private drawCircular(
    ctx: CanvasRenderingContext2D,
    w: number,
    h: number,
    input: RenderInput,
  ) {
    const bars = 48;
    const a = input.analysis;
    const radius = 2.4 + a.pulse * 0.12;
    ctx.save();
    ctx.globalAlpha = input.visAlpha;
    for (let i = 0; i < bars; i++) {
      const t = i / bars;
      const ang = t * Math.PI * 2 - Math.PI / 2;
      const v = a.bands[Math.floor(t * a.bands.length) % a.bands.length] ?? 0;
      const x = Math.cos(ang) * radius;
      const z = Math.sin(ang) * radius;
      this.drawPrism(
        ctx,
        x - 0.08,
        0.25 + v * 2.8,
        z - 0.08,
        0.16,
        0.16,
        w,
        h,
        input.tilt,
        rgba(input.theme.primary, 0.92),
        rgba(input.theme.secondary, 0.5),
        rgba(input.theme.glow, 0.75),
      );
    }
    ctx.restore();
  }

  private drawLiquid(
    ctx: CanvasRenderingContext2D,
    w: number,
    h: number,
    input: RenderInput,
  ) {
    const nx = 22;
    const nz = 12;
    const a = input.analysis;
    const heightAt = (xi: number, zi: number) => {
      const band = a.bands[Math.floor((xi / (nx - 1)) * (a.bands.length - 1))] ?? 0;
      return (
        Math.sin(xi * 0.55 + this.liquidPhase + zi * 0.4) * 0.22 +
        Math.sin(xi * 0.2 + this.liquidPhase * 0.6) * 0.12 +
        band * 1.15
      );
    };
    ctx.save();
    ctx.globalAlpha = input.visAlpha;
    for (let zi = nz - 2; zi >= 0; zi--) {
      for (let xi = 0; xi < nx - 1; xi++) {
        const x0 = -5 + (xi / (nx - 1)) * 10;
        const x1 = -5 + ((xi + 1) / (nx - 1)) * 10;
        const z0 = -2.2 + (zi / (nz - 1)) * 4.4;
        const z1 = -2.2 + ((zi + 1) / (nz - 1)) * 4.4;
        const p = (x: number, y: number, z: number) => this.project(x, y, z, w, h, input.tilt);
        const a0 = p(x0, heightAt(xi, zi), z0);
        const a1 = p(x1, heightAt(xi + 1, zi), z0);
        const a2 = p(x1, heightAt(xi + 1, zi + 1), z1);
        const a3 = p(x0, heightAt(xi, zi + 1), z1);
        const shade = 0.35 + 0.65 * ((heightAt(xi, zi) + 0.3) / 2);
        this.fillTri(ctx, [a0, a1, a2], rgba(input.theme.primary, 0.25 + shade * 0.5));
        this.fillTri(ctx, [a0, a2, a3], rgba(input.theme.secondary, 0.2 + shade * 0.45));
      }
    }
    ctx.restore();
  }

  private drawTitles(
    ctx: CanvasRenderingContext2D,
    w: number,
    h: number,
    input: RenderInput,
  ) {
    const padX = w * 0.06;
    const top = input.titlePos === "top";
    const baseY = top ? Math.max(72, h * 0.12) : h - Math.max(72, h * 0.12);
    const song = input.song.trim();
    const meta = [input.artist.trim(), input.album.trim()].filter(Boolean).join("  ·  ");
    if (!song && !meta) return;

    ctx.save();
    ctx.textAlign = "left";
    ctx.textBaseline = "alphabetic";

    const barH = Math.max(18, h * 0.028);
    ctx.fillStyle = rgba(input.theme.primary, 0.9);
    ctx.fillRect(padX, baseY - barH - 10, Math.max(3, w * 0.003), barH + 8);

    const titleSize = Math.max(28, Math.round(h * 0.042 * (input.titleScale || 1)));
    ctx.font = `500 ${titleSize}px Oswald, Impact, sans-serif`;
    ctx.fillStyle = "#f4f0ea";
    const title = ellipsize(ctx, song.toUpperCase(), w * 0.7);
    ctx.fillText(title, padX + w * 0.014, baseY);

    if (meta) {
      const metaSize = Math.max(14, Math.round(h * 0.018));
      ctx.font = `500 ${metaSize}px Figtree, system-ui, sans-serif`;
      ctx.fillStyle = "rgba(244,240,234,0.62)";
      ctx.fillText(ellipsize(ctx, meta.toUpperCase(), w * 0.62), padX + w * 0.014, baseY + metaSize + 10);
    }
    ctx.restore();
  }

  private drawProgress(
    ctx: CanvasRenderingContext2D,
    w: number,
    h: number,
    input: RenderInput,
  ) {
    const padX = w * 0.06;
    const y = h - Math.max(28, h * 0.036);
    const trackW = w - padX * 2;
    const th = Math.max(3, h * 0.004);
    const p = input.duration > 0 ? clamp(input.currentTime / input.duration) : 0;

    ctx.save();
    ctx.fillStyle = "rgba(244,240,234,0.16)";
    roundRect(ctx, padX, y, trackW, th, th / 2);
    ctx.fill();

    ctx.fillStyle = input.theme.primary;
    roundRect(ctx, padX, y, Math.max(th, trackW * p), th, th / 2);
    ctx.fill();

    const hx = padX + trackW * p;
    ctx.beginPath();
    ctx.arc(hx, y + th / 2, th * 1.6, 0, Math.PI * 2);
    ctx.fillStyle = "#f4f0ea";
    ctx.fill();

    const tSize = Math.max(11, Math.round(h * 0.014));
    ctx.font = `500 ${tSize}px Figtree, system-ui, sans-serif`;
    ctx.fillStyle = "rgba(244,240,234,0.55)";
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    ctx.fillText(
      `${formatTimecode(input.currentTime)}  /  ${formatTimecode(input.duration)}`,
      w - padX,
      y - tSize - 4,
    );
    ctx.restore();
  }
}

function roundRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number,
) {
  const rr = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + rr, y);
  ctx.arcTo(x + w, y, x + w, y + h, rr);
  ctx.arcTo(x + w, y + h, x, y + h, rr);
  ctx.arcTo(x, y + h, x, y, rr);
  ctx.arcTo(x, y, x + w, y, rr);
  ctx.closePath();
}

export const FRAME_SIZE = { w: EXPORT_W, h: EXPORT_H };
