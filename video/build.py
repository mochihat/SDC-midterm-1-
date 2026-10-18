#!/usr/bin/env python3
"""Build the lecture video: TTS -> Manim -> sound effects -> mix with ducked music -> subtitles -> concat.

Run inside the render container (see README.md):
  python3 build.py                         # all chapters, 1080p30 -> out/midterm_localization.mp4
  python3 build.py --preview               # 480p15, much faster
  python3 build.py --chapters c3_06_icp    # only some chapters (each also written as out/<id>.mp4)
  python3 build.py --no-music              # voice + sound effects only
"""
import argparse
import glob
import importlib.util
import json
import os
import subprocess
import sys
import wave

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "lib"))
import tts  # noqa: E402

# One entry per chapter, in video order. music_volume: background music level before ducking (0 = off).
CHAPTERS = [
    {"id": "c3_06_icp", "file": "scenes/c3_06_icp.py", "scene": "C3_06_ICP", "music_volume": 0.22},
]

SR = 44100
OUT = os.path.join(ROOT, "out")
AUDIO = os.path.join(ROOT, "audio")


def run(cmd, **kw):
    print("+", " ".join(cmd[:6]), "..." if len(cmd) > 6 else "", flush=True)
    subprocess.run(cmd, check=True, **kw)


def load_module(path):
    spec = importlib.util.spec_from_file_location(os.path.basename(path)[:-3], os.path.join(ROOT, path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_wav(path):
    with wave.open(path) as w:
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        return data.reshape(-1, w.getnchannels())


def write_wav(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def decode(src, dst):
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-ar", str(SR), "-ac", "2", dst])


def narration(ch_id, lines):
    """Concatenate the line mp3s with the same gaps the scene uses; return beat start times."""
    folder = os.path.join(AUDIO, ch_id)
    data = json.load(open(os.path.join(folder, "timing.json")))
    parts, starts, t = [], [], 0.0
    for line in data["lines"]:
        wav = os.path.join(folder, line["file"][:-4] + ".wav")
        decode(os.path.join(folder, line["file"]), wav)
        x = read_wav(wav)
        beat = line["dur"] + data["gap"]
        n = int(round(beat * SR))
        pad = np.zeros((max(n, len(x)), 2), np.float32)
        pad[:len(x)] = x
        parts.append(pad[:n])
        starts.append((t, beat, line["text"]))
        t += beat
    write_wav(os.path.join(folder, "narration.wav"), np.vstack(parts))
    return starts


def sfx_track(ch_id, starts, sfx, total):
    track = np.zeros((int(total * SR) + SR, 2), np.float32)
    bank = {name: read_wav(os.path.join(ROOT, "assets", "sfx", f"{name}.wav"))
            for name in ("whoosh", "pop", "ding")}
    for beat, events in sfx.items():
        if beat >= len(starts):
            continue
        t0, dur, _ = starts[beat]
        for name, off in events:
            at = t0 + (off if off >= 0 else dur + off)
            s = int(at * SR)
            clip = bank[name][: len(track) - s]
            track[s:s + len(clip)] += 0.35 * clip
    path = os.path.join(AUDIO, ch_id, "sfx.wav")
    write_wav(path, track)
    return path


def srt(starts, path, offset=0.0):
    def fmt(t):
        ms = int(round(t * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    with open(path, "w") as f:
        for i, (t0, dur, text) in enumerate(starts, 1):
            f.write(f"{i}\n{fmt(offset + t0)} --> {fmt(offset + t0 + dur - 0.05)}\n{text}\n\n")


def video_duration(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                 "default=noprint_wrappers=1:nokey=1", path],
                                check=True, capture_output=True, text=True).stdout)


def music_file():
    custom = sorted(glob.glob(os.path.join(ROOT, "assets", "music", "custom.*")))
    return custom[0] if custom else os.path.join(ROOT, "assets", "music", "upbeat_loop.wav")


def build_chapter(ch, preview, music_on):
    mod = load_module(ch["file"])
    tts.synthesize(ch["id"], mod.LINES, AUDIO)
    starts = narration(ch["id"], mod.LINES)

    quality = ["-ql"] if preview else ["--resolution", "1920,1080", "--frame_rate", "30"]
    env = dict(os.environ, VIDEO_ROOT=ROOT)
    run(["manim", "render", *quality, "--disable_caching", "--media_dir", os.path.join(OUT, "media"),
         "-o", ch["id"], os.path.join(ROOT, ch["file"]), ch["scene"]], env=env, cwd=ROOT)
    silent = glob.glob(os.path.join(OUT, "media", "videos", "*", "*", ch["id"] + ".mp4"))
    silent = max(silent, key=os.path.getmtime)
    dur = video_duration(silent)

    sfx = sfx_track(ch["id"], starts, getattr(mod, "SFX", {}), dur)
    vol = ch.get("music_volume", 0.2) if music_on else 0.0
    out = os.path.join(OUT, ch["id"] + (".preview" if preview else "") + ".mp4")
    voice = os.path.join(AUDIO, ch["id"], "narration.wav")
    fmt = "aformat=sample_rates=44100:channel_layouts=stereo"
    graph = (f"[1:a]{fmt},apad,asplit=2[vo][sc];"
             f"[2:a]{fmt},volume={vol},afade=t=in:d=1,afade=t=out:st={max(dur - 1.5, 0):.2f}:d=1.5[mu];"
             f"[mu][sc]sidechaincompress=threshold=0.02:ratio=12:attack=15:release=350[duck];"
             f"[3:a]{fmt}[fx];"
             f"[duck][vo][fx]amix=inputs=3:duration=longest:normalize=0,alimiter=limit=0.95[a]")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", voice, "-stream_loop", "-1", "-i", music_file(),
         "-i", sfx, "-filter_complex", graph, "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac",
         "-b:a", "192k", "-t", f"{dur:.3f}", out])
    srt(starts, out[:-4] + ".srt")
    return out, starts, dur


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapters", nargs="*", help="chapter ids (default: all)")
    ap.add_argument("--preview", action="store_true", help="480p15 instead of 1080p30")
    ap.add_argument("--no-music", action="store_true")
    a = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    if not os.path.exists(os.path.join(ROOT, "assets", "music", "upbeat_loop.wav")):
        run([sys.executable, os.path.join(ROOT, "assets", "make_audio.py")])
    chosen = [c for c in CHAPTERS if not a.chapters or c["id"] in a.chapters]
    built = [build_chapter(c, a.preview, not a.no_music) for c in chosen]

    if len(built) > 1:
        lst = os.path.join(OUT, "concat.txt")
        with open(lst, "w") as f:
            f.writelines(f"file '{p}'\n" for p, _, _ in built)
        final = os.path.join(OUT, "midterm_localization" + (".preview" if a.preview else "") + ".mp4")
        run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", final])
        offset, all_starts = 0.0, []
        for _, starts, dur in built:
            all_starts += [(t + offset, d, txt) for t, d, txt in starts]
            offset += dur
        srt(all_starts, final[:-4] + ".srt")
        print("final:", final)
    else:
        print("chapter:", built[0][0])


if __name__ == "__main__":
    main()
