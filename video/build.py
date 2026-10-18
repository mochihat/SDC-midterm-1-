#!/usr/bin/env python3
"""Build the lecture video: TTS -> Manim -> sound effects -> mix with ducked music -> subtitles -> concat.

Run inside the render container (see README.md):
  python3 build.py                         # all chapters, 1080p30 -> out/midterm_localization.mp4
  python3 build.py --preview               # 480p15, much faster
  python3 build.py --chapters c3_06_icp    # only some chapters (each also written as out/<id>.mp4)
  python3 build.py --concat-only           # join already rendered chapters into the final video
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
    {"id": "c0_intro", "file": "scenes/c0_intro.py", "scene": "C0_Intro", "music_volume": 0.26},
    {"id": "c1_big_picture", "file": "scenes/c1_big_picture.py", "scene": "C1_BigPicture", "music_volume": 0.22},
    {"id": "c2_why", "file": "scenes/c2_why.py", "scene": "C2_Why", "music_volume": 0.22},
    {"id": "c3_01_frames", "file": "scenes/c3_01_frames.py", "scene": "C3_01_Frames", "music_volume": 0.18},
    {"id": "c3_02_pose", "file": "scenes/c3_02_pose.py", "scene": "C3_02_Pose", "music_volume": 0.18},
    {"id": "c3_03_pointcloud", "file": "scenes/c3_03_pointcloud.py", "scene": "C3_03_PointCloud", "music_volume": 0.18},
    {"id": "c3_04_scale", "file": "scenes/c3_04_scale.py", "scene": "C3_04_Scale", "music_volume": 0.18},
    {"id": "c3_05_preprocess", "file": "scenes/c3_05_preprocess.py", "scene": "C3_05_Preprocess", "music_volume": 0.18},
    {"id": "c3_06_icp", "file": "scenes/c3_06_icp.py", "scene": "C3_06_ICP", "music_volume": 0.22},
    {"id": "c3_07_ndt", "file": "scenes/c3_07_ndt.py", "scene": "C3_07_NDT", "music_volume": 0.18},
    {"id": "c3_08_tracking", "file": "scenes/c3_08_tracking.py", "scene": "C3_08_Tracking", "music_volume": 0.18},
    {"id": "c3_09_ros", "file": "scenes/c3_09_ros.py", "scene": "C3_09_ROS", "music_volume": 0.18},
    {"id": "c3_10_metric", "file": "scenes/c3_10_metric.py", "scene": "C3_10_Metric", "music_volume": 0.18},
    {"id": "c3_11_kaggle", "file": "scenes/c3_11_kaggle.py", "scene": "C3_11_Kaggle", "music_volume": 0.2},
    {"id": "c4_code", "file": "scenes/c4_code.py", "scene": "C4_Code", "music_volume": 0.18},
    {"id": "c5a_work", "file": "scenes/c5a_work.py", "scene": "C5a_Work", "music_volume": 0.18},
    {"id": "c5b_work", "file": "scenes/c5b_work.py", "scene": "C5b_Work", "music_volume": 0.18},
    {"id": "c6_next", "file": "scenes/c6_next.py", "scene": "C6_Next", "music_volume": 0.2},
    {"id": "c7_checklist", "file": "scenes/c7_checklist.py", "scene": "C7_Checklist", "music_volume": 0.22},
    {"id": "c8_end", "file": "scenes/c8_end.py", "scene": "C8_End", "music_volume": 0.26},
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


def existing_chapter(ch, preview):
    """An already rendered chapter (for --concat-only)."""
    mod = load_module(ch["file"])
    out = os.path.join(OUT, ch["id"] + (".preview" if preview else "") + ".mp4")
    if not os.path.exists(out):
        sys.exit(f"missing {out}: build it first with --chapters {ch['id']}")
    return out, narration(ch["id"], mod.LINES), video_duration(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapters", nargs="*", help="chapter ids (default: all)")
    ap.add_argument("--preview", action="store_true", help="480p15 instead of 1080p30")
    ap.add_argument("--no-music", action="store_true")
    ap.add_argument("--concat-only", action="store_true", help="only join chapters that are already rendered")
    a = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    if not os.path.exists(os.path.join(ROOT, "assets", "music", "upbeat_loop.wav")):
        run([sys.executable, os.path.join(ROOT, "assets", "make_audio.py")])
    chosen = [c for c in CHAPTERS if not a.chapters or c["id"] in a.chapters]
    if a.concat_only:
        built = [existing_chapter(c, a.preview) for c in chosen]
    else:
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
