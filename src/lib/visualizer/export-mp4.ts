import {
  AudioBufferSource,
  BufferTarget,
  CanvasSource,
  Mp4OutputFormat,
  Output,
  Quality,
  getFirstEncodableAudioCodec,
  getFirstEncodableVideoCodec,
} from "mediabunny";
import type { VideoCodec, AudioCodec } from "mediabunny";

export const EXPORT_WIDTH = 1920;
export const EXPORT_HEIGHT = 1080;
export const EXPORT_FPS = 30;

export type ExportOptions = {
  canvas: HTMLCanvasElement;
  duration: number;
  audioBuffer: AudioBuffer;
  drawFrame: (time: number) => void;
  onProgress?: (progress: number, label: string) => void;
  signal?: AbortSignal;
};

export class ExportError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ExportError";
  }
}

function throwIfAborted(signal?: AbortSignal) {
  if (signal?.aborted) {
    const err = new DOMException("Export cancelled", "AbortError");
    throw err;
  }
}

export async function exportVisualizerMp4(opts: ExportOptions): Promise<Blob> {
  const { canvas, duration, audioBuffer, drawFrame, onProgress, signal } = opts;
  const width = canvas.width || EXPORT_WIDTH;
  const height = canvas.height || EXPORT_HEIGHT;
  const frames = Math.max(1, Math.round(duration * EXPORT_FPS));
  const frameDur = 1 / EXPORT_FPS;

  onProgress?.(0.02, "Preparing encoder");

  const quality = new Quality("high");
  const videoCodec: VideoCodec | null = await getFirstEncodableVideoCodec(
    ["avc", "hevc", "vp9", "av1"],
    { width, height, quality },
  );
  if (!videoCodec) {
    throw new ExportError(
      "This browser cannot encode video. Try Chrome or Edge, then generate again.",
    );
  }

  const audioCodec: AudioCodec | null = await getFirstEncodableAudioCodec(
    ["aac", "opus", "mp3"],
    {
      numberOfChannels: Math.min(2, audioBuffer.numberOfChannels),
      sampleRate: audioBuffer.sampleRate,
      quality,
    },
  );

  const target = new BufferTarget();
  const output = new Output({
    format: new Mp4OutputFormat({ fastStart: "in-memory" }),
    target,
  });

  const videoSource = new CanvasSource(canvas, {
    codec: videoCodec,
    quality,
    keyFrameInterval: 2,
  });
  output.addVideoTrack(videoSource, { frameRate: EXPORT_FPS });

  let audioSource: AudioBufferSource | null = null;
  if (audioCodec) {
    audioSource = new AudioBufferSource({
      codec: audioCodec,
      quality,
    });
    output.addAudioTrack(audioSource);
  }

  await output.start();
  throwIfAborted(signal);

  if (audioSource) {
    onProgress?.(0.06, "Writing audio");
    await audioSource.add(audioBuffer);
  }

  onProgress?.(0.1, "Rendering frames");

  for (let i = 0; i < frames; i++) {
    throwIfAborted(signal);
    const t = Math.min(duration, i * frameDur);
    drawFrame(t);
    await videoSource.add(t, frameDur);
    if (i % 8 === 0 || i === frames - 1) {
      onProgress?.(0.1 + (0.85 * (i + 1)) / frames, "Rendering frames");
      // Yield so the progress dialog can paint
      await new Promise((r) => setTimeout(r, 0));
    }
  }

  onProgress?.(0.96, "Finalizing MP4");
  await output.finalize();

  const buf = target.buffer;
  if (!buf) {
    throw new ExportError("Encoder produced an empty file.");
  }
  onProgress?.(1, "Done");
  return new Blob([new Uint8Array(buf)], { type: "video/mp4" });
}
