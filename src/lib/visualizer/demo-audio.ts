/** 16s, 124 BPM stereo demo so the stage is alive before a file is chosen. */
export async function createDemoBuffer(): Promise<AudioBuffer> {
  const sr = 44100;
  const duration = 16;
  const ctx = new OfflineAudioContext(2, Math.floor(sr * duration), sr);
  const bpm = 124;
  const beat = 60 / bpm;
  const now = ctx.currentTime;

  const master = ctx.createGain();
  master.gain.value = 0.85;
  master.connect(ctx.destination);

  const kick = ctx.createGain();
  kick.connect(master);
  const snare = ctx.createGain();
  snare.connect(master);
  const hat = ctx.createGain();
  hat.connect(master);
  const bass = ctx.createGain();
  bass.gain.value = 0.22;
  bass.connect(master);
  const pad = ctx.createGain();
  pad.gain.value = 0.08;
  pad.connect(master);

  const noiseBuf = ctx.createBuffer(1, sr, sr);
  const nch = noiseBuf.getChannelData(0);
  for (let i = 0; i < nch.length; i++) nch[i] = Math.random() * 2 - 1;

  function makeKick(time: number) {
    const o = ctx.createOscillator();
    o.type = "sine";
    const g = ctx.createGain();
    o.connect(g);
    g.connect(kick);
    o.frequency.setValueAtTime(140, time);
    o.frequency.exponentialRampToValueAtTime(42, time + 0.12);
    g.gain.setValueAtTime(1, time);
    g.gain.exponentialRampToValueAtTime(0.001, time + 0.32);
    o.start(time);
    o.stop(time + 0.34);
  }

  function makeSnare(time: number) {
    const src = ctx.createBufferSource();
    src.buffer = noiseBuf;
    const bp = ctx.createBiquadFilter();
    bp.type = "bandpass";
    bp.frequency.value = 1800;
    bp.Q.value = 0.9;
    const g = ctx.createGain();
    src.connect(bp);
    bp.connect(g);
    g.connect(snare);
    g.gain.setValueAtTime(0.55, time);
    g.gain.exponentialRampToValueAtTime(0.001, time + 0.18);
    src.start(time);
    src.stop(time + 0.2);

    const tone = ctx.createOscillator();
    tone.type = "triangle";
    const tg = ctx.createGain();
    tone.connect(tg);
    tg.connect(snare);
    tone.frequency.value = 180;
    tg.gain.setValueAtTime(0.25, time);
    tg.gain.exponentialRampToValueAtTime(0.001, time + 0.12);
    tone.start(time);
    tone.stop(time + 0.14);
  }

  function makeHat(time: number, open = false) {
    const src = ctx.createBufferSource();
    src.buffer = noiseBuf;
    const hp = ctx.createBiquadFilter();
    hp.type = "highpass";
    hp.frequency.value = 7000;
    const g = ctx.createGain();
    src.connect(hp);
    hp.connect(g);
    g.connect(hat);
    g.gain.setValueAtTime(open ? 0.22 : 0.1, time);
    g.gain.exponentialRampToValueAtTime(0.001, time + (open ? 0.18 : 0.05));
    src.start(time);
    src.stop(time + 0.2);
  }

  const notes = [41, 41, 44, 36, 41, 48, 44, 36];
  function makeBass(time: number, midi: number, len: number) {
    const o = ctx.createOscillator();
    o.type = "sawtooth";
    const f = ctx.createBiquadFilter();
    f.type = "lowpass";
    f.frequency.setValueAtTime(280, time);
    f.frequency.exponentialRampToValueAtTime(120, time + len);
    const g = ctx.createGain();
    o.connect(f);
    f.connect(g);
    g.connect(bass);
    o.frequency.value = 440 * Math.pow(2, (midi - 69) / 12);
    g.gain.setValueAtTime(0.0001, time);
    g.gain.exponentialRampToValueAtTime(0.9, time + 0.02);
    g.gain.exponentialRampToValueAtTime(0.0001, time + len);
    o.start(time);
    o.stop(time + len + 0.02);
  }

  const padNotes = [53, 56, 60];
  for (const midi of padNotes) {
    const o = ctx.createOscillator();
    o.type = "triangle";
    const f = ctx.createBiquadFilter();
    f.type = "lowpass";
    f.frequency.value = 900;
    o.connect(f);
    f.connect(pad);
    o.frequency.value = 440 * Math.pow(2, (midi - 69) / 12);
    o.start(now);
    o.stop(now + duration);
  }

  const beats = Math.floor(duration / beat);
  for (let i = 0; i < beats; i++) {
    const t = now + i * beat;
    makeKick(t);
    if (i % 2 === 1) makeSnare(t);
    makeHat(t, false);
    makeHat(t + beat * 0.5, i % 4 === 3);
    const n = notes[i % notes.length]!;
    makeBass(t, n, beat * 0.92);
  }

  return ctx.startRendering();
}
