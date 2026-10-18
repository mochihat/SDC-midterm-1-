#!/usr/bin/env python3
"""Build the lecture video: TTS -> Manim -> narration at the real beat times -> sound effects -> mix with ducked
music -> subtitles burned into a band under the picture -> concat.

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
import re
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

SR = tts.SR
OUT = os.path.join(ROOT, "out")
AUDIO = os.path.join(ROOT, "audio")
FINAL = "midterm_localization"
SRT_NAME = "phude_midterm.srt"  # not "<video name>.srt": players would load it on top of the burned-in subtitles

# Subtitle band: the picture is shrunk to 5/6 and placed at the top; subtitles live in the strip below it.
PICTURE = 5 / 6
SUB_SIZE = 38       # font px at 1080p
SUB_CHARS = 84      # max characters per subtitle chunk (wraps to at most two lines)


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


def video_info(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height:format=duration", "-of", "json", path],
                         check=True, capture_output=True, text=True).stdout
    j = json.loads(out)
    return j["streams"][0]["width"], j["streams"][0]["height"], float(j["format"]["duration"])


def narration(ch_id):
    """Place every line at the real start of its beat (beats.json from the scene); return the placed lines."""
    folder = os.path.join(AUDIO, ch_id)
    lines = json.load(open(os.path.join(folder, "timing.json")))["lines"]
    beats = json.load(open(os.path.join(folder, "beats.json")))
    starts = beats["starts"]
    assert len(starts) == len(lines), f"{ch_id}: {len(starts)} beats for {len(lines)} lines"
    total = max(beats["end"], starts[-1] + lines[-1]["dur"] + 0.3)
    track = np.zeros((int(total * SR) + 1, 2), np.float32)
    placed = []
    for i, (t0, line) in enumerate(zip(starts, lines)):
        x = read_wav(os.path.join(folder, line["file"]))
        s = int(round(t0 * SR))
        track[s:s + len(x)] += x[:len(track) - s]
        beat = (starts[i + 1] if i + 1 < len(starts) else total) - t0
        placed.append({"start": t0, "beat": beat, "speech": line["dur"], "text": line["text"]})
    tts.write_wav(os.path.join(folder, "narration.wav"), track)
    json.dump({"total": total, "lines": placed}, open(os.path.join(folder, "placed.json"), "w"),
              ensure_ascii=False, indent=1)
    return placed, total


def sfx_track(ch_id, placed, sfx, total):
    track = np.zeros((int(total * SR) + SR, 2), np.float32)
    bank = {name: read_wav(os.path.join(ROOT, "assets", "sfx", f"{name}.wav"))
            for name in ("whoosh", "pop", "ding")}
    for beat, events in sfx.items():
        if beat >= len(placed):
            continue
        t0, dur = placed[beat]["start"], placed[beat]["beat"]
        for name, off in events:
            at = t0 + (off if off >= 0 else dur + off)
            s = int(at * SR)
            clip = bank[name][: len(track) - s]
            track[s:s + len(clip)] += 0.35 * clip
    path = os.path.join(AUDIO, ch_id, "sfx.wav")
    tts.write_wav(path, track)
    return path


# ---- subtitles --------------------------------------------------------------------------------------------
def chunks(text, limit=SUB_CHARS):
    """Short subtitle pieces: split after punctuation, merge small pieces, cut long ones at a space."""
    pieces = [p for p in re.split(r"(?<=[.,:;?!–])\s+", text.strip()) if p]
    out = []
    for p in pieces:
        while len(p) > limit:
            cut = p.rfind(" ", 0, limit)
            cut = cut if cut > limit // 2 else limit
            out.append(p[:cut].strip())
            p = p[cut:].strip()
        if out and len(out[-1]) + 1 + len(p) <= limit and not out[-1].endswith((".", "?", "!", ":")):
            out[-1] += " " + p
        else:
            out.append(p)
    return out


def cues(placed, offset=0.0):
    """(start, end, text) for every chunk; a line's speech time is shared out by character count."""
    result = []
    for line in placed:
        parts = chunks(line["text"])
        total = sum(len(p) for p in parts)
        t = offset + line["start"]
        for p in parts:
            d = line["speech"] * len(p) / total
            result.append((t, t + d, p))
            t += d
        # keep the last chunk on screen through the pause after the line
        s, e, p = result[-1]
        result[-1] = (s, max(e, offset + line["start"] + min(line["beat"], line["speech"] + 0.6)) - 0.05, p)
    return result


def write_srt(cue_list, path):
    def fmt(t):
        ms = int(round(t * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    with open(path, "w") as f:
        for i, (s, e, text) in enumerate(cue_list, 1):
            f.write(f"{i}\n{fmt(s)} --> {fmt(e)}\n{text}\n\n")


def write_ass(cue_list, path, width, height):
    def fmt(t):
        cs = int(round(t * 100))
        return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"
    k = height / 1080
    margin_x = int(width * (1 - PICTURE) / 2) + int(20 * k)
    head = (
        "[Script Info]\nScriptType: v4.00+\n"
        f"PlayResX: {width}\nPlayResY: {height}\nWrapStyle: 0\nScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
        "MarginR, MarginV, Encoding\n"
        f"Style: Default,Noto Sans,{round(SUB_SIZE * k)},&H00F5F5F5,&H00F5F5F5,&H00000000,&H00000000,0,0,0,0,"
        f"100,100,0,0,1,0,0,2,{margin_x},{margin_x},{round(36 * k)},1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    with open(path, "w") as f:
        f.write(head)
        for s, e, text in cue_list:
            f.write(f"Dialogue: 0,{fmt(s)},{fmt(e)},Default,,0,0,0,,{text}\n")


def layout_filter(width, height, ass_path, pad_end):
    """Shrink the picture, put it at the top on the background colour, burn the subtitles into the band below."""
    w, h = int(width * PICTURE) // 2 * 2, int(height * PICTURE) // 2 * 2
    x, y = (width - w) // 2, int(height * 0.012) // 2 * 2
    tail = f",tpad=stop_mode=clone:stop_duration={pad_end:.3f}" if pad_end > 0 else ""
    return (f"[0:v]scale={w}:{h}:flags=lanczos,pad={width}:{height}:{x}:{y}:color=0x101321,"
            f"ass={ass_path}{tail}[v]")


def music_file():
    custom = sorted(glob.glob(os.path.join(ROOT, "assets", "music", "custom.*")))
    return custom[0] if custom else os.path.join(ROOT, "assets", "music", "upbeat_loop.wav")


def chapter_out(ch, preview):
    return os.path.join(OUT, ch["id"] + (".preview" if preview else "") + ".mp4")


def build_chapter(ch, preview, music_on):
    mod = load_module(ch["file"])
    tts.synthesize(ch["id"], mod.LINES, AUDIO)

    quality = ["-ql"] if preview else ["--resolution", "1920,1080", "--frame_rate", "30"]
    env = dict(os.environ, VIDEO_ROOT=ROOT)
    run(["manim", "render", *quality, "--disable_caching", "--media_dir", os.path.join(OUT, "media"),
         "-o", ch["id"], os.path.join(ROOT, ch["file"]), ch["scene"]], env=env, cwd=ROOT)
    silent = glob.glob(os.path.join(OUT, "media", "videos", "*", "*", ch["id"] + ".mp4"))
    silent = max(silent, key=os.path.getmtime)
    width, height, vdur = video_info(silent)

    placed, total = narration(ch["id"])
    dur = max(vdur, total)
    sfx = sfx_track(ch["id"], placed, getattr(mod, "SFX", {}), dur)
    ass = os.path.join(AUDIO, ch["id"], "subs.ass")
    write_ass(cues(placed), ass, width, height)

    vol = ch.get("music_volume", 0.2) if music_on else 0.0
    out = chapter_out(ch, preview)
    voice = os.path.join(AUDIO, ch["id"], "narration.wav")
    fmt = "aformat=sample_rates=44100:channel_layouts=stereo"
    graph = (layout_filter(width, height, ass, dur - vdur) + ";"
             f"[1:a]{fmt},apad,asplit=2[vo][sc];"
             f"[2:a]{fmt},volume={vol},afade=t=in:d=1,afade=t=out:st={max(dur - 1.5, 0):.2f}:d=1.5[mu];"
             f"[mu][sc]sidechaincompress=threshold=0.02:ratio=12:attack=15:release=350[duck];"
             f"[3:a]{fmt}[fx];"
             f"[duck][vo][fx]amix=inputs=3:duration=longest:normalize=0,alimiter=limit=0.95[a]")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", voice, "-stream_loop", "-1", "-i", music_file(),
         "-i", sfx, "-filter_complex", graph, "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-t", f"{dur:.3f}", out])
    return out, placed, dur


def existing_chapter(ch, preview):
    """An already rendered chapter (for --concat-only)."""
    out = chapter_out(ch, preview)
    placed_path = os.path.join(AUDIO, ch["id"], "placed.json")
    if not (os.path.exists(out) and os.path.exists(placed_path)):
        sys.exit(f"missing {out}: build it first with --chapters {ch['id']}")
    return out, json.load(open(placed_path))["lines"], video_info(out)[2]


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
        final = os.path.join(OUT, FINAL + (".preview" if a.preview else "") + ".mp4")
        run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", final])
        offset, all_cues = 0.0, []
        for _, placed, dur in built:
            all_cues += cues(placed, offset)
            offset += dur
        write_srt(all_cues, os.path.join(OUT, ("preview_" if a.preview else "") + SRT_NAME))
        print("final:", final)
    else:
        print("chapter:", built[0][0])


if __name__ == "__main__":
    main()
