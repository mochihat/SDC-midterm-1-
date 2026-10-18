"""Text-to-speech for one chapter: one wav per narration line, with measured durations.

Vietnamese text is read by a Vietnamese voice; English terms (see TERMS) by an English voice, so words like
"Kaggle", "point cloud" or "localization.cpp" are pronounced in English instead of with Vietnamese phonetics.
Each line is cut into segments, every segment is synthesized once (cached in audio/_cache), silence at the
segment edges is trimmed and the segments are joined with short pauses that follow the punctuation.

Writes audio/<chapter>/line_XX.wav and audio/<chapter>/timing.json:
    {"voices": ..., "rate": ..., "gap": ..., "lines": [{"text": ..., "file": ..., "dur": seconds}, ...]}
"""
import hashlib
import json
import os
import re
import subprocess
import time
import wave

import numpy as np

VOICE_VI = "vi-VN-HoaiMyNeural"
VOICE_EN = "en-US-JennyNeural"
RATE = "+8%"
GAP = 0.25  # silence after each line (seconds)
SR = 44100
VERSION = 3  # bump to re-synthesize everything

# English words and phrases in the narration, read by the English voice. Longest match wins; matching ignores case
# and requires a word boundary on both sides (Vietnamese letters count as word characters).
TERMS = """
Normal Distributions Transform; Iterative Closest Point; Problems and Solutions; Claude Code; scan matching;
point cloud; point-to-plane; point-to-point; motion model; sensor fusion; maximum likelihood; local minimum;
initial guess; gimbal lock; homogeneous matrix; scale ambiguity; voxel grid; RTS smoother; ros2 launch; ROS 2;
localization.cpp; map_modified.cpp; visualization.cpp; txt_to_idx_x_y_yaw.py; init_guess.txt; launch.py; map.pcd;
result_1.csv; result_2.csv; result_1; result_2; Track1.db3; Track01; Track02; localizer_node; gnss_pose;
sensor_msgs; base_link; raw_ply; RunLocalization; MapAnything; LoGeR; Dockerfile; Docker; Kaggle; Kalman;
leaderboard; localization; baseline; template; Gaussian; quaternion; registration; correspondence; Contributions;
Workload; Pipeline; Overfit; outlier; resolution; submap; rosbag; colcon; RViz; ROS; GNSS; GPS; IMU; LiDAR; Radar;
ICP; NDT; RMSE; ATE; PCL; CSV; PDF; README; TODO; UTC; AI; C++; Python; Ubuntu; terminal; script; commit; repo;
token; slide; checklist; midterm; video; camera; frame; pose; yaw; roll; pitch; radian; gyro; scale; prior;
voxel; grid; filter; crop; mask; matching; model; node; topic; message; launch; build; source; code; file;
test; track; map; point; cloud; delta; theta; byte; idx; ply; pcd; txt; laser; Library; rotation; translation;
x, y, z, w; x, y, z; x, y, yaw; x, y; R; t
"""
_terms = sorted({t.strip() for t in TERMS.replace("\n", " ").split(";") if t.strip()}, key=len, reverse=True)
_TERM_RE = re.compile(r"(?<![\w.])(" + "|".join(re.escape(t) for t in _terms) + r")(?![\w])", re.IGNORECASE)
# English terms separated only by spaces/commas/slashes ("x, y, yaw") are read as one English segment.
_JOIN_RE = re.compile(r"^[\s,/+&-]*$")


def segments(text):
    """[(lang, text)] with lang 'vi' or 'en', in reading order."""
    out, pos = [], 0
    for m in _TERM_RE.finditer(text):
        if m.start() > pos:
            out.append(["vi", text[pos:m.start()]])
        if out and out[-1][0] == "vi" and _JOIN_RE.match(out[-1][1]) and len(out) >= 2 and out[-2][0] == "en":
            joiner = out.pop()[1]
            out[-1][1] += joiner + m.group(0)
        else:
            out.append(["en", m.group(0)])
        pos = m.end()
    if pos < len(text):
        out.append(["vi", text[pos:]])
    return [(lang, s) for lang, s in out if re.search(r"\w", s)] or [("vi", text)]


def pause_after(piece):
    """Pause (s) after a segment, from the punctuation at its end."""
    tail = piece.rstrip()
    if tail.endswith((".", "!", "?", ":")):
        return 0.30
    if tail.endswith((",", ";", "–", "-")):
        return 0.15
    return 0.04


def _edge_tts(text, voice, rate, path):
    for attempt in range(6):
        try:  # edge-tts can hang forever on a stalled connection
            proc = subprocess.run(["edge-tts", "--voice", voice, f"--rate={rate}", "--text", text,
                                   "--write-media", path], capture_output=True, text=True, timeout=90)
        except subprocess.TimeoutExpired as e:
            proc = subprocess.CompletedProcess(e.cmd, 1, "", "timeout")
        if proc.returncode == 0 and os.path.exists(path) and os.path.getsize(path) > 0:
            return
        time.sleep(5 * (attempt + 1))  # network hiccups and "NoAudioReceived": back off before retrying
    raise RuntimeError(f"edge-tts failed for {text!r}: {proc.stderr[-300:]}")


def _decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "s16le", "-ac", "2", "-ar", str(SR), "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32).reshape(-1, 2) / 32768


def _trim(x, thresh=0.01, keep=0.03):
    loud = np.flatnonzero(np.abs(x).max(axis=1) > thresh)
    if len(loud) == 0:
        return x[:0]
    k = int(keep * SR)
    return x[max(loud[0] - k, 0):loud[-1] + k]


def _level(x, target_db=-20.0):
    """Same loudness for both voices (the English voice is a few dB quieter)."""
    if len(x) == 0:
        return x
    rms = np.sqrt((x ** 2).mean())
    return x * min(10 ** (target_db / 20) / max(rms, 1e-6), 4.0)


def segment_audio(lang, text, rate, cache):
    voice = VOICE_EN if lang == "en" else VOICE_VI
    seg_rate = "+0%" if lang == "en" else rate  # isolated English words sound rushed when sped up
    key = hashlib.sha1(f"{voice}|{seg_rate}|{text.strip()}".encode()).hexdigest()[:16]
    path = os.path.join(cache, key + ".mp3")
    if not os.path.exists(path):
        _edge_tts(text.strip(), voice, seg_rate, path + ".tmp.mp3")
        os.replace(path + ".tmp.mp3", path)
    return _level(_trim(_decode(path)))


def write_wav(path, x):
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


def synthesize(chapter, lines, audio_root, rate=RATE):
    folder = os.path.join(audio_root, chapter)
    cache = os.path.join(audio_root, "_cache")
    os.makedirs(folder, exist_ok=True)
    os.makedirs(cache, exist_ok=True)
    timing_path = os.path.join(folder, "timing.json")
    settings = {"version": VERSION, "voices": [VOICE_VI, VOICE_EN], "rate": rate}
    old = {}
    if os.path.exists(timing_path):
        prev = json.load(open(timing_path))
        if all(prev.get(k) == v for k, v in settings.items()):
            old = {(l["text"], l["file"]): l for l in prev["lines"]}
    result = []
    for i, text in enumerate(lines):
        name = f"line_{i:02d}.wav"
        path = os.path.join(folder, name)
        cached = old.get((text, name))
        if cached is None or not os.path.exists(path):
            parts = []
            for lang, piece in segments(text):
                parts.append(segment_audio(lang, piece, rate, cache))
                parts.append(np.zeros((int(pause_after(piece) * SR), 2), np.float32))
            x = np.vstack(parts[:-1]) if len(parts) > 1 else np.zeros((SR // 2, 2), np.float32)
            write_wav(path, x)
            cached = {"text": text, "file": name, "dur": len(x) / SR}
        result.append(cached)
    json.dump({**settings, "gap": GAP, "lines": result}, open(timing_path, "w"), ensure_ascii=False, indent=1)
    return result
