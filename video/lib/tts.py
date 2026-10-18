"""Text-to-speech for one chapter: one wav per narration line, with measured durations.

Every line is read in one go by one Vietnamese voice, so the speech flows without voice changes. English terms are
first rewritten the way Vietnamese engineers say them (PRONOUNCE: "Kaggle" -> "ke gồ", "NDT" -> "en đi ti"), so the
voice does not spell them out with Vietnamese letter names. Subtitles keep the original spelling.

Writes audio/<chapter>/line_XX.wav and audio/<chapter>/timing.json:
    {"voice": ..., "rate": ..., "gap": ..., "lines": [{"text": ..., "spoken": ..., "file": ..., "dur": seconds}]}
"""
import hashlib
import json
import os
import re
import subprocess
import time
import wave

import numpy as np

VOICE = "vi-VN-HoaiMyNeural"
RATE = "+8%"
GAP = 0.25  # silence after each line (seconds)
SR = 44100
VERSION = 4  # bump to re-synthesize everything

# English term = how it is read. Longest match wins; matching ignores case and needs a word boundary on both sides
# (Vietnamese letters count as word characters). Add a line here when a word still sounds wrong.
PRONOUNCE = """
Normal Distributions Transform = no mồ đít tri biu sần tran phom
Iterative Closest Point = i tơ ra típ cờ lâu sợt poi
Problems and Solutions = próp lầm en xơ lu sần
Claude Code = cờ lốt cốt
scan matching = xờ ken mát chinh
point cloud = poi cờ lao
point-to-plane = poi tu pờ lên
point-to-point = poi tu poi
motion model = mâu sần mo đồ
sensor fusion = xen xơ phiu giần
maximum likelihood = mác xi mầm lai cờ li hút
local minimum = lâu cồ mi ni mầm
initial guess = i ni sồ ghét
gimbal lock = gim bồ lóc
homogeneous matrix = hô mô gi ni ợt mây trích
scale ambiguity = xờ kêu em bi ghiu i ti
voxel grid = vóc xồ gờ rít
RTS smoother = a ti ét xờ mu đơ
ros2 launch = rốt tu lăn
ROS 2 = rốt tu
localization.cpp = lô cồ lai dê sần chấm xi pi pi
map_modified.cpp = máp mo đi phai chấm xi pi pi
visualization.cpp = vi giu ồ lai dê sần chấm xi pi pi
txt_to_idx_x_y_yaw.py = tếch tu ai đi ếch ích oai giô chấm pai
init_guess.txt = i nít ghét chấm tếch
launch.py = lăn chấm pai
map.pcd = máp chấm pi xi đi
result_1.csv = ri dôn một chấm xi ét vi
result_2.csv = ri dôn hai chấm xi ét vi
result_1 = ri dôn một
result_2 = ri dôn hai
Track1.db3 = trác một chấm đi bi ba
Track01 = trác không một
Track02 = trác không hai
localizer_node = lô cồ lai dơ nốt
gnss_pose = gi en ét ét pâu
sensor_msgs = xen xơ mét xịch
base_link = bết linh
raw_ply = rô pi eo oai
RunLocalization = răn lô cồ lai dê sần
MapAnything = máp e ni thinh
LoGeR = lô gơ
Dockerfile = đóc cơ phai
Docker = đóc cơ
Kaggle = ke gồ
Kalman = kan mần
leaderboard = li đơ bo
localization = lô cồ lai dê sần
baseline = bết lai
template = tem pờ lết
Gaussian = gao xi ần
quaternion = quơ tơ ni ần
registration = rê gít trây sần
correspondence = co rét pon đần
Contributions = con tri biu sần
Workload = uốc lốt
Pipeline = pai lai
Overfit = âu vơ phít
outlier = ao lai ơ
resolution = rê dồ lu sần
submap = xắp máp
rosbag = rốt béc
colcon = côn con
RViz = a vi
ROS = rốt
GNSS = gi en ét ét
GPS = gi pi ét
IMU = ai em iu
LiDAR = lai đa
Radar = ra đa
ICP = ai xi pi
NDT = en đi ti
RMSE = a em ét i
ATE = ây ti i
PCL = pi xi eo
CSV = xi ét vi
PDF = pi đi ép
README = rít mi
TODO = tu đu
UTC = iu ti xi
AI = ây ai
C++ = xi cộng cộng
Python = pai thần
Ubuntu = u bun tu
terminal = tơ mi nồ
script = xờ cờ ríp
commit = cơ mít
repo = ri pô
token = tâu cần
slide = xờ lai
checklist = chéc lít
midterm = mít thơm
video = vi đi ô
camera = ca mê ra
frame = phờ rêm
pose = pâu
yaw = giô
roll = rôn
pitch = pít
radian = rây đi ần
gyro = giai rô
scale = xờ kêu
prior = prai ơ
voxel = vóc xồ
grid = gờ rít
filter = phin tơ
crop = cờ róp
mask = mát
matching = mát chinh
model = mo đồ
node = nốt
topic = tó pích
message = mét xịch
launch = lăn
build = bin
source = xo
code = cốt
file = phai
test = tét
track = trác
map = máp
point = poi
cloud = cờ lao
delta = đen ta
theta = thê ta
byte = bai
idx = ai đi ếch
ply = pi eo oai
pcd = pi xi đi
txt = tếch
laser = lây dơ
Library = lai bờ ra ri
rotation = rô tây sần
translation = tran xờ lây sần
x, y, z, w = ích, oai, dét, đắp bờ liu
x, y, z = ích, oai, dét
x, y, yaw = ích, oai, giô
x, y = ích, oai
TA = ti ây
E3 = i ba
GB = gi ga bai
DoF = đi âu ép
robot = rô bốt
chat = chát
R = a
t = ti
"""
_say = {}
for row in PRONOUNCE.strip().splitlines():
    term, said = (s.strip() for s in row.split("=", 1))
    _say[term.lower()] = said
_TERM_RE = re.compile(r"(?<![\w.])(" + "|".join(re.escape(t) for t in sorted(_say, key=len, reverse=True))
                      + r")(?!\w)", re.IGNORECASE)


def spoken(text):
    """The line as it is sent to the voice."""
    return _TERM_RE.sub(lambda m: _say[m.group(0).lower()], text)


def _edge_tts(text, path):
    for attempt in range(6):
        try:  # edge-tts can hang forever on a stalled connection
            proc = subprocess.run(["edge-tts", "--voice", VOICE, f"--rate={RATE}", "--text", text,
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


def _trim(x, thresh=0.01, keep=0.05):
    loud = np.flatnonzero(np.abs(x).max(axis=1) > thresh)
    if len(loud) == 0:
        return x
    k = int(keep * SR)
    return x[max(loud[0] - k, 0):loud[-1] + k]


def write_wav(path, x):
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


def synthesize(chapter, lines, audio_root):
    folder = os.path.join(audio_root, chapter)
    cache = os.path.join(audio_root, "_cache")
    os.makedirs(folder, exist_ok=True)
    os.makedirs(cache, exist_ok=True)
    timing_path = os.path.join(folder, "timing.json")
    settings = {"version": VERSION, "voice": VOICE, "rate": RATE}
    old = {}
    if os.path.exists(timing_path):
        prev = json.load(open(timing_path))
        if all(prev.get(k) == v for k, v in settings.items()):
            old = {(l["spoken"], l["file"]): l for l in prev["lines"]}
    result = []
    for i, text in enumerate(lines):
        say = spoken(text)
        name = f"line_{i:02d}.wav"
        path = os.path.join(folder, name)
        cached = old.get((say, name))
        if cached is None or not os.path.exists(path):
            key = hashlib.sha1(f"{VOICE}|{RATE}|{say}".encode()).hexdigest()[:16]
            mp3 = os.path.join(cache, key + ".mp3")
            if not os.path.exists(mp3):
                _edge_tts(say, mp3 + ".tmp.mp3")
                os.replace(mp3 + ".tmp.mp3", mp3)
            x = _trim(_decode(mp3))
            write_wav(path, x)
            cached = {"text": text, "spoken": say, "file": name, "dur": len(x) / SR}
        cached["text"] = text
        result.append(cached)
    json.dump({**settings, "gap": GAP, "lines": result}, open(timing_path, "w"), ensure_ascii=False, indent=1)
    return result
