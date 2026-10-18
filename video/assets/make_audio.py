"""Synthesize the background music loop and sound effects (no third-party audio, so no licence issues).

Writes assets/music/upbeat_loop.wav (32 bars at 120 BPM, loops cleanly) and assets/sfx/{whoosh,pop,ding}.wav.
Usage: python3 assets/make_audio.py
"""
import os
import wave

import numpy as np

SR = 44100
HERE = os.path.dirname(os.path.abspath(__file__))


def write(path, x):
    x = np.clip(x, -1, 1)
    data = (x * 32767).astype(np.int16)
    if data.ndim == 1:
        data = np.stack([data, data], axis=1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


def env(n, attack, release):
    e = np.ones(n)
    a = max(1, int(attack * SR))
    e[:a] = np.linspace(0, 1, a)
    e *= np.exp(-np.arange(n) / (release * SR))
    return e


def lowpass(x, alpha):
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += alpha * (v - acc)
        y[i] = acc
    return y


def music(bpm=120, bars=32):
    beat = 60 / bpm
    n = int(bars * 4 * beat * SR)
    out = np.zeros(n)
    rng = np.random.default_rng(1)
    t_beat = np.arange(int(beat * SR)) / SR
    # Chords: Am - F - C - G (root frequencies in Hz), one per bar.
    roots = [220.0, 174.61, 261.63, 196.0]
    triads = {220.0: [1, 1.189, 1.498], 174.61: [1, 1.26, 1.498], 261.63: [1, 1.26, 1.498], 196.0: [1, 1.26, 1.498]}
    for bar in range(bars):
        root = roots[bar % 4]
        start = int(bar * 4 * beat * SR)
        length = int(4 * beat * SR)
        tt = np.arange(length) / SR
        pad = sum(np.sin(2 * np.pi * root * r * tt) + 0.3 * np.sin(4 * np.pi * root * r * tt) for r in triads[root])
        out[start:start + length] += 0.05 * pad * (0.6 + 0.4 * np.sin(2 * np.pi * tt / (4 * beat)) ** 2)
        for b in range(4):
            s = start + int(b * beat * SR)
            kick = np.sin(2 * np.pi * (45 + 90 * np.exp(-t_beat * 30)) * t_beat) * np.exp(-t_beat * 9)
            out[s:s + len(kick)] += 0.55 * kick[: n - s]
            # Bass on eighth notes.
            for half in range(2):
                hs = s + int(half * beat / 2 * SR)
                tb = np.arange(int(beat / 2 * SR)) / SR
                bass = np.sign(np.sin(2 * np.pi * root / 2 * tb)) * np.exp(-tb * 6)
                out[hs:hs + len(tb)] += 0.09 * bass[: n - hs]
                hat = rng.standard_normal(int(0.04 * SR)) * np.exp(-np.arange(int(0.04 * SR)) / (0.008 * SR))
                hat = hat - lowpass(hat, 0.3)
                out[hs:hs + len(hat)] += 0.07 * hat[: n - hs]
            if b in (1, 3):
                sn = rng.standard_normal(int(0.18 * SR)) * np.exp(-np.arange(int(0.18 * SR)) / (0.04 * SR))
                out[s:s + len(sn)] += 0.18 * sn[: n - s]
    return out / np.max(np.abs(out)) * 0.8


def whoosh():
    n = int(0.45 * SR)
    rng = np.random.default_rng(2)
    noise = rng.standard_normal(n)
    alpha = np.linspace(0.02, 0.4, n)
    y = np.empty(n)
    acc = 0.0
    for i in range(n):
        acc += alpha[i] * (noise[i] - acc)
        y[i] = acc
    shape = np.sin(np.linspace(0, np.pi, n)) ** 2
    return 0.9 * y / np.max(np.abs(y)) * shape


def pop():
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    f = 1100 * np.exp(-t * 18) + 350
    return 0.7 * np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 0.025)


def ding():
    n = int(1.2 * SR)
    t = np.arange(n) / SR
    y = sum(a * np.sin(2 * np.pi * f * t) for f, a in ((1318.5, 1), (2637, 0.4), (3955, 0.15)))
    return 0.5 * y * env(n, 0.003, 0.35)


def main():
    os.makedirs(os.path.join(HERE, "music"), exist_ok=True)
    os.makedirs(os.path.join(HERE, "sfx"), exist_ok=True)
    write(os.path.join(HERE, "music", "upbeat_loop.wav"), music())
    for name, fn in (("whoosh", whoosh), ("pop", pop), ("ding", ding)):
        write(os.path.join(HERE, "sfx", f"{name}.wav"), fn())
    print("wrote music/upbeat_loop.wav and sfx/{whoosh,pop,ding}.wav")


if __name__ == "__main__":
    main()
