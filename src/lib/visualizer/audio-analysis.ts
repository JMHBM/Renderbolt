import { clamp } from "@/lib/utils";
import type { FrameAnalysis } from "./types";

export const FFT_SIZE = 2048;
export const BAND_COUNT = 64;

export class BeatDetector {
  avg = 0.1;
  pulse = 0;
  hold = 0;

  reset() {
    this.avg = 0.1;
    this.pulse = 0;
    this.hold = 0;
  }

  push(bass: number, dt: number, sensitivity = 1): number {
    const s = Math.max(0.25, Math.min(2.5, sensitivity));
    const attack = Math.min(1, dt * 3);
    this.avg += (bass - this.avg) * attack * 0.35;
    const onset = bass - this.avg;
    if (onset > 0.07 / s && bass > 0.12 / s && this.hold <= 0) {
      this.pulse = clamp((0.5 + onset * 2.4) * s);
      this.hold = 0.11;
    }
    this.hold = Math.max(0, this.hold - dt);
    this.pulse *= Math.pow(0.08, dt);
    if (this.pulse < 0.002) this.pulse = 0;
    return this.pulse;
  }
}

export type AnalysisScratch = {
  re: Float32Array;
  im: Float32Array;
  timeDomain: Float32Array;
  mag: Float32Array;
  bands: Float32Array;
  window: Float32Array;
};

export function createScratch(): AnalysisScratch {
  const window = new Float32Array(FFT_SIZE);
  for (let i = 0; i < FFT_SIZE; i++) {
    window[i] = 0.5 * (1 - Math.cos((2 * Math.PI * i) / (FFT_SIZE - 1)));
  }
  return {
    re: new Float32Array(FFT_SIZE),
    im: new Float32Array(FFT_SIZE),
    timeDomain: new Float32Array(FFT_SIZE),
    mag: new Float32Array(FFT_SIZE / 2),
    bands: new Float32Array(BAND_COUNT),
    window,
  };
}

function fftRadix2(re: Float32Array, im: Float32Array) {
  const n = re.length;
  for (let i = 1, j = 0; i < n; i++) {
    let bit = n >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) {
      const tr = re[i];
      re[i] = re[j]!;
      re[j] = tr!;
      const ti = im[i];
      im[i] = im[j]!;
      im[j] = ti!;
    }
  }
  for (let len = 2; len <= n; len <<= 1) {
    const ang = (-2 * Math.PI) / len;
    const wlenRe = Math.cos(ang);
    const wlenIm = Math.sin(ang);
    const half = len >> 1;
    for (let i = 0; i < n; i += len) {
      let wRe = 1;
      let wIm = 0;
      for (let j = 0; j < half; j++) {
        const i0 = i + j;
        const i1 = i0 + half;
        const vr = re[i1]! * wRe - im[i1]! * wIm;
        const vi = re[i1]! * wIm + im[i1]! * wRe;
        re[i1] = re[i0]! - vr;
        im[i1] = im[i0]! - vi;
        re[i0] += vr;
        im[i0] += vi;
        const nWRe = wRe * wlenRe - wIm * wlenIm;
        wIm = wRe * wlenIm + wIm * wlenRe;
        wRe = nWRe;
      }
    }
  }
}

function toLogBands(
  mag: Float32Array,
  bands: Float32Array,
  sampleRate: number,
) {
  const n = mag.length;
  const fMin = 30;
  const fMax = Math.min(16000, sampleRate / 2);
  const nyquist = sampleRate / 2;
  for (let b = 0; b < bands.length; b++) {
    const t0 = b / bands.length;
    const t1 = (b + 1) / bands.length;
    const hz0 = fMin * Math.pow(fMax / fMin, t0);
    const hz1 = fMin * Math.pow(fMax / fMin, t1);
    const i0 = Math.max(0, Math.floor((hz0 / nyquist) * n));
    const i1 = Math.min(n, Math.ceil((hz1 / nyquist) * n));
    let sum = 0;
    let count = 0;
    for (let i = i0; i < Math.max(i0 + 1, i1); i++) {
      sum += mag[i]!;
      count++;
    }
    const raw = count ? sum / count : 0;
    // Perceptual boost for highs, compress dynamic range
    const boosted = Math.pow(raw, 0.62) * (0.75 + t0 * 0.7);
    bands[b] = clamp(boosted);
  }
}

export function analyzeBufferAt(
  buffer: AudioBuffer,
  timeSec: number,
  scratch: AnalysisScratch,
  detector: BeatDetector,
  dt: number,
  sensitivity = 1,
): FrameAnalysis {
  const ch = buffer.getChannelData(0);
  const sr = buffer.sampleRate;
  const center = Math.floor(timeSec * sr);
  const half = FFT_SIZE >> 1;
  const { re, im, timeDomain, mag, bands, window } = scratch;

  let sumSq = 0;
  for (let i = 0; i < FFT_SIZE; i++) {
    const idx = center - half + i;
    const s = idx >= 0 && idx < ch.length ? ch[idx]! : 0;
    timeDomain[i] = s;
    const w = s * window[i]!;
    re[i] = w;
    im[i] = 0;
    sumSq += s * s;
  }

  fftRadix2(re, im);

  const inv = 1 / FFT_SIZE;
  for (let i = 0; i < mag.length; i++) {
    const a = re[i]!;
    const b = im[i]!;
    mag[i] = Math.sqrt(a * a + b * b) * inv * 8;
  }

  toLogBands(mag, bands, sr);

  const bassN = Math.max(1, Math.floor(bands.length * 0.14));
  const midN = Math.max(1, Math.floor(bands.length * 0.5));
  let bass = 0;
  let mid = 0;
  let treble = 0;
  for (let i = 0; i < bands.length; i++) {
    const v = bands[i]!;
    if (i < bassN) bass += v;
    else if (i < midN) mid += v;
    else treble += v;
  }
  bass = clamp(bass / bassN);
  mid = clamp(mid / Math.max(1, midN - bassN));
  treble = clamp(treble / Math.max(1, bands.length - midN));
  const rms = clamp(Math.sqrt(sumSq / FFT_SIZE) * 2.4);
  const pulse = detector.push(bass * 0.7 + rms * 0.3, dt, sensitivity);

  return { timeDomain, bands, bass, mid, treble, rms, pulse };
}

export function idleAnalysis(
  scratch: AnalysisScratch,
  detector: BeatDetector,
  nowSec: number,
  sensitivity = 1,
): FrameAnalysis {
  const t = nowSec;
  // Silent idle motion so the stage never looks frozen
  const kick = Math.pow(Math.max(0, Math.sin(t * Math.PI * 2 * 2)), 10);
  const hat = Math.pow(Math.max(0, Math.sin(t * Math.PI * 2 * 8)), 4) * 0.25;
  for (let i = 0; i < scratch.timeDomain.length; i++) {
    const x = i / scratch.timeDomain.length;
    scratch.timeDomain[i] =
      Math.sin(x * Math.PI * 6 + t * 2.2) * (0.12 + kick * 0.55) +
      Math.sin(x * Math.PI * 18 + t * 4) * 0.04;
  }
  for (let i = 0; i < scratch.bands.length; i++) {
    const n = i / scratch.bands.length;
    scratch.bands[i] = clamp(
      (1 - n) * (0.12 + kick * 0.7) + n * hat + Math.sin(t * 1.4 + n * 8) * 0.05,
    );
  }
  const bass = 0.1 + kick * 0.75;
  const pulse = detector.push(bass, 1 / 60, sensitivity);
  return {
    timeDomain: scratch.timeDomain,
    bands: scratch.bands,
    bass,
    mid: 0.15 + hat,
    treble: 0.08 + hat * 0.6,
    rms: 0.1 + kick * 0.4,
    pulse,
  };
}
