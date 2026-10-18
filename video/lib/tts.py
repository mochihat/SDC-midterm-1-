"""Text-to-speech for one chapter: one mp3 per narration line, with measured durations.

Writes audio/<chapter>/line_XX.mp3 and audio/<chapter>/timing.json:
    {"voice": ..., "rate": ..., "gap": ..., "lines": [{"text": ..., "file": ..., "dur": seconds}, ...]}
Lines whose text, voice and rate are unchanged are not re-synthesized.
"""
import json
import os
import subprocess

VOICE = "vi-VN-HoaiMyNeural"
RATE = "+8%"
GAP = 0.25  # silence after each line (seconds)


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=noprint_wrappers=1:nokey=1", path],
                         check=True, capture_output=True, text=True).stdout
    return float(out.strip())


def synthesize(chapter, lines, audio_root, voice=VOICE, rate=RATE):
    folder = os.path.join(audio_root, chapter)
    os.makedirs(folder, exist_ok=True)
    timing_path = os.path.join(folder, "timing.json")
    old = {}
    if os.path.exists(timing_path):
        prev = json.load(open(timing_path))
        if prev.get("voice") == voice and prev.get("rate") == rate:
            old = {(l["text"], l["file"]): l for l in prev["lines"]}
    result = []
    for i, text in enumerate(lines):
        name = f"line_{i:02d}.mp3"
        path = os.path.join(folder, name)
        cached = old.get((text, name))
        if cached is None or not os.path.exists(path):
            for attempt in range(4):
                proc = subprocess.run(["edge-tts", "--voice", voice, f"--rate={rate}", "--text", text,
                                       "--write-media", path], capture_output=True, text=True)
                if proc.returncode == 0 and os.path.exists(path) and os.path.getsize(path) > 0:
                    break
            else:
                raise RuntimeError(f"edge-tts failed for line {i}: {proc.stderr[-300:]}")
            cached = {"text": text, "file": name, "dur": duration(path)}
        result.append(cached)
    json.dump({"voice": voice, "rate": rate, "gap": GAP, "lines": result},
              open(timing_path, "w"), ensure_ascii=False, indent=1)
    return result
