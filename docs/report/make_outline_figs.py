"""Figures for docs/report/presentation_outline.md (English labels) -> docs/report/fig/outline/*.png

Inputs (all local, nothing downloaded):
  ~/kaggle-sdc-bot/bot.log                     every bot submission with its public score ("NOTIFY TrackN: submitted F: score S")
  docs/nhat-ky/04-cac-lan-nop-kaggle.md        the 7 manual submissions of 17/10 18:51-19:00 (before the bot) - typed in EARLY
  src/localization/result/...                  our result CSVs (gitignored, on this machine)
  ~/SDC-midterm01/data/TrackN/map_voxel_0.3m.pcd   map for the trajectory overlays (binary PCD x y z)
  src/localization/result/track3/*_diag.csv    per-frame diagnostics of the Track03 tracker / paint filter
  docs/report/fig/t3_speed.csv                 speed series for the IMU-motion figure
Writes submissions_all.csv next to the figures (our own scores only).

Host: numpy + matplotlib. Usage: python3 docs/report/make_outline_figs.py
"""
import csv
import os
import re
from datetime import datetime

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HOME = os.path.expanduser("~")
OUT = os.path.join(REPO, "docs", "report", "fig", "outline")
RES = os.path.join(REPO, "src", "localization", "result")
T3 = os.path.join(RES, "track3")
DATA = os.path.join(HOME, "SDC-midterm01", "data")
os.makedirs(OUT, exist_ok=True)

# reference categorical palette of the dataviz method (fixed order), text in ink, recessive grid
BLUE, ORANGE, AQUA, YELLOW, VIOLET = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#6250d6"
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e4e0"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "legend.frameon": False})

EARLY = [  # docs/nhat-ky/04 table rows #1-#7 (submitted by hand before the bot log starts) + the two uploads of 16/10
    ("1", "2026-10-16 04:32", "trial.csv", 5822.14965), ("1", "2026-10-16 09:36", "kaggle_track1_result.csv", 602.39927),
    ("1", "2026-10-17 18:51", "gnss_1.csv", 1.31094), ("2", "2026-10-17 18:52", "gnss_2.csv", 0.57111),
    ("1", "2026-10-17 18:57", "gnss_smooth_1.csv", 1.26235), ("1", "2026-10-17 18:58", "gnss_heading_1.csv", 1.35783),
    ("2", "2026-10-17 18:59", "gnss_smooth_2.csv", 0.57811), ("2", "2026-10-17 19:00", "gnss_heading_2.csv", 0.47281)]
LEADER = re.compile(r"^(probe_.*|yawproj_.*|posproj_.*|posyaw_v\d_\d|lb_.*|corr_r\d_\d|bump.*|pp_t\d_r\d|.*bestyaw.*)$")
PIPE = re.compile(r"^(kaggle_track1_result|gnss_.*|rts_.*|phys_yawb.*|lagyaw_.*|yawtau.*|gnssyaw_pos_rts_2|fusion_.*|"
                  r"clean_.*|t6_.*|t2v_.*|if_.*)$")


def submissions():
    rows = [(t, datetime.strptime(d, "%Y-%m-%d %H:%M"), f, s) for t, d, f, s in EARLY]
    seen = {(t, f) for t, _, f, _ in rows}
    pat = re.compile(r"^(\S+ \S+) NOTIFY Track(\d): submitted (\S+): score ([0-9.]+)")
    for line in open(os.path.join(HOME, "kaggle-sdc-bot", "bot.log")):
        m = pat.match(line)
        if m and (m.group(2), m.group(3)) not in seen:
            seen.add((m.group(2), m.group(3)))
            rows.append((m.group(2), datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S"), m.group(3), float(m.group(4))))
    rows.sort(key=lambda r: (r[0], r[1]))
    out = []
    for t, d, f, s in rows:
        name = f[:-4]
        if t == "3":
            # the first tracker version (23/10 05:11-08:00) rewrote frames 0-80 with the winning start hypothesis
            # (not causal; found and fixed the same day, docs/nhat-ky/12 §1)
            cls = "start not causal" if re.match(r"^t3_(v.*|full_N)$", name) else "causal pipeline"
        elif name == "trial":
            cls = "other"
        elif LEADER.match(name):
            cls = "leaderboard"
        elif PIPE.match(name):
            cls = "pipeline"
        else:
            cls = "hybrid"
        out.append((t, d, name, s, cls))
    with open(os.path.join(OUT, "submissions_all.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["track", "time_utc+8", "file", "public_score", "class"])
        for t, d, f, s, c in out:
            w.writerow([t, d.strftime("%Y-%m-%d %H:%M"), f, s, c])
    return out


def load(path):
    return np.loadtxt(path, delimiter=",", skiprows=1)


def read_pcd_xy(path, step=1):
    with open(path, "rb") as fh:
        head = b""
        while not head.endswith(b"DATA binary\n"):
            head += fh.readline()
        n = int(re.search(rb"POINTS (\d+)", head).group(1))
        pts = np.frombuffer(fh.read(n * 12), np.float32).reshape(n, 3)
    return pts[::step, :2].astype(np.float64)


def map_image(ax, track, traj_xy, pad=40.0, cell=1.0):
    """map points as a density image around the trajectory (grey), returns nothing"""
    xy = read_pcd_xy(os.path.join(DATA, f"Track{track}", "map_voxel_0.3m.pcd"))
    lo, hi = traj_xy.min(axis=0) - pad, traj_xy.max(axis=0) + pad
    keep = np.all((xy >= lo) & (xy <= hi), axis=1)
    h, xe, ye = np.histogram2d(xy[keep, 0], xy[keep, 1], bins=[int((hi[0] - lo[0]) / cell), int((hi[1] - lo[1]) / cell)],
                               range=[[lo[0], hi[0]], [lo[1], hi[1]]])
    ax.imshow(np.log1p(h.T), origin="lower", extent=[xe[0], xe[-1], ye[0], ye[-1]], cmap="Greys", vmax=np.log1p(h).max() * 0.8)
    ax.set_aspect("equal")
    ax.grid(False)


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", name)


# ---------------------------------------------------------------- F03 / F04 score timelines
subs = submissions()
CLS_COL = {"pipeline": BLUE, "hybrid": ORANGE, "leaderboard": AQUA}
fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))
for ax, t, base in zip(axes, ("1", "2"), (1.79075, 1.92587)):
    for cls, col in CLS_COL.items():
        pts = [(d, s) for tt, d, f, s, c in subs if tt == t and c == cls and s < 2.5 and not f.startswith(("probe_", "bump"))]
        if not pts:
            continue
        d, s = zip(*pts)
        ax.scatter(d, s, s=14, color=col, alpha=0.35, linewidths=0)
        best, bx, by = 9e9, [], []
        for di, si in pts:
            best = min(best, si)
            bx.append(di)
            by.append(best)
        ax.step(bx + [datetime(2026, 10, 26)], by + [by[-1]], where="post", color=col, lw=2,
                label=f"{cls} (best {by[-1]:.2f})")
    ax.axhline(base, color=MUTED, ls="--", lw=1)
    ax.text(datetime(2026, 10, 17, 12), base + 0.03, f"TA baseline {base:.2f}", color=MUTED, fontsize=9)
    ax.set_title(f"Track0{t}: public score over time (lower is better)", color=INK, loc="left")
    ax.set_ylim(0, 2.1)
    ax.set_xlim(datetime(2026, 10, 17, 12), datetime(2026, 10, 26))
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d/%m"))
    ax.legend(loc="upper right", fontsize=9)
fig.text(0.01, -0.02, "Probe files (deliberately perturbed) are left out. Classes as in docs/nhat-ky/09: pipeline = algorithm "
         "only; hybrid = algorithm run on a file with a score-fitted part; leaderboard = probes / score-weighted combinations.",
         fontsize=8, color=MUTED)
save(fig, "timeline_t1t2.png")

fig, ax = plt.subplots(figsize=(13, 4.8))
t3 = [(d, f, s, c) for t, d, f, s, c in subs if t == "3"]
d3, f3, s3, c3 = zip(*t3)
TOP = 1.55
sv = np.array(s3)
causal = np.array([c == "causal pipeline" for c in c3])
for msk, col, lab in ((~causal, ORANGE, "first tracker version: start not causal (MHT rewrote frames 0-80; fixed 23/10)"),
                      (causal, BLUE, "causal pipeline")):
    ok = msk & (sv <= TOP)
    ax.scatter(np.flatnonzero(ok), sv[ok], s=22, color=col, alpha=0.6, linewidths=0, zorder=3, label=lab)
    hi = msk & (sv > TOP)
    if hi.any():
        ax.scatter(np.flatnonzero(hi), np.full(hi.sum(), TOP), s=40, marker="^", color=col, zorder=3)
best, by, bx = 9e9, [], []
for i in np.flatnonzero(causal):
    best = min(best, sv[i])
    bx.append(i)
    by.append(best)
ax.step(bx + [len(t3) - 1], by + [by[-1]], where="post", color=BLUE, lw=2, label="best causal so far")
ax.text(len(t3) - 1, TOP + 0.03, "triangles: above 1.55 (v2 3.18, vB 46.67, vL 4.86)", fontsize=8, color=MUTED, ha="right")
marks = {"t3_vN": ("N 0.77 (start\nnot causal)", 0.58), "t3_A2h": ("A2h 0.96: causal MHT,\ngyro fix, CSM", 1.18),
         "t3_L2b": ("L2b 0.84:\nCSM lever", 1.05), "t3_X3f": ("X3f 0.80:\nIMU mounting", 1.30), "t3_Z3a": ("Z3a 0.80:\nrestart fix", 1.12),
         "t3_PA2": ("PA2 0.49:\nroad paint", 0.80), "t3_PE3": ("PE3 0.37:\nkappa, lever", 0.74),
         "t3_PF2": ("PF2 0.33:\nside cams", 0.56), "t3_Q1": ("Q1 0.28:\nIMU motion", 0.52), "t3_Q4": ("Q4 0.28:\nend fix (final)", 0.66)}
for i, f in enumerate(f3):
    if f in marks:
        lab, yt = marks[f]
        ax.annotate(lab, (i, min(s3[i], TOP)), xytext=(i, yt), ha="center", fontsize=8, color=INK,
                    arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6))
ax.axhline(1.40, color=MUTED, ls="--", lw=1)
ax.text(36, 1.42, "private baseline 1.40 (rules)", color=MUTED, fontsize=9)
ax.set_ylim(0, 1.62)
ax.set_xlabel("submission number, in time order (23/10 05:11 -> 25/10 20:55)")
ax.set_ylabel("public score (first ~13 % of frames)")
ax.set_title(f"Track03: all {len(t3)} public scores (pipeline output only, no probing)", loc="left", color=INK)
ax.legend(loc="center right", fontsize=8, bbox_to_anchor=(1.0, 0.66))
save(fig, "timeline_t3.png")

# ---------------------------------------------------------------- F05 Track01 position ablation (log 08 §3, §9.2)
rows = [("GNSS + Kalman (prior)", 0.905), ("NDT 3 cams, scale 1.0", 0.934), ("NDT 3 cams, scale 0.8", 0.836),
        ("GICP, scale 0.8", 0.803), ("NDT -> GICP, scale 0.8", 0.769), ("GICP, ground-height scale (1/4 frames)", 0.752),
        ("GICP, ground scale, every frame", 0.714), ("3-DoF planar ICP", 0.719), ("point-to-plane ICP", 0.681),
        ("GICP pass 2", 0.679), ("GICP pass 5", 0.801), ("+ hood mask + SOR", 0.764), ("GICP 2 passes + de-mean", 0.616)]
fig, ax = plt.subplots(figsize=(8.5, 5.2))
y = np.arange(len(rows))[::-1]
cols = [MUTED] + [ORANGE if v > 0.905 or "pass 5" in n or "SOR" in n else BLUE for n, v in rows[1:]]
cols[-1] = AQUA
ax.barh(y, [v for _, v in rows], color=cols, height=0.62)
for yi, (n, v) in zip(y, rows):
    ax.text(v + 0.005, yi, f"{v:.3f} m", va="center", fontsize=9, color=INK)
ax.set_yticks(y, [n for n, _ in rows])
ax.axvline(0.905, color=MUTED, ls="--", lw=1)
ax.set_xlim(0.5, 1.0)
ax.set_xlabel("Track01 position RMSE (m), from position-only Kaggle submissions (yaw fixed -> error = score - 0.314)")
ax.set_title("Track01: which scan-matching change helped the position", loc="left", color=INK)
ax.grid(axis="y", visible=False)
save(fig, "t1_position_ablation.png")

# ---------------------------------------------------------------- F06 yaw: complementary filter time constant (log 08 §9.1)
fig, axes = plt.subplots(1, 2, figsize=(11, 3.8))
for ax, data, ttl in (
        (axes[0], {"gyro z, no slip": [(7, 0.865), (10, 0.876)], "gravity-projected + slip": [(10, 0.899), (15, 0.952), (30, 1.085)]},
         "Track01"),
        (axes[1], {"gyro z, no slip": [(5, 0.330), (10, 0.264), (15, 0.249), (30, 0.268)],
                   "gravity-projected + slip": [(2, 0.429), (5, 0.393), (15, 0.304)]}, "Track02")):
    for (name, pts), col in zip(data.items(), (BLUE, ORANGE)):
        xs, ys = zip(*pts)
        ax.plot(xs, ys, marker="o", color=col, lw=2, ms=6, label=name)
    ax.set_xlabel("tau (s): smoothing of (course - gyro yaw)")
    ax.set_ylabel("yaw RMSE (deg), from Kaggle")
    ax.set_title(f"{ttl}: yaw = gyro + course over ground", loc="left", color=INK)
    ax.legend(fontsize=9)
axes[0].axhline(1.559, color=MUTED, ls="--", lw=1)
axes[0].text(7, 1.5, "before: score-weighted yaw 1.559 deg", fontsize=8, color=MUTED)
axes[0].set_ylim(0.8, 1.65)
save(fig, "yaw_tau.png")

# ---------------------------------------------------------------- F15 clean Track01 / Track02 chains (Kaggle)
fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))
for ax, chain, ttl in ((axes[0], [("TA baseline", 1.79), ("GNSS", 1.31), ("Kalman + yaw b", 1.25), ("+ GICP 2 passes\n+ gyro yaw", 0.80),
                                   ("range 20 m", 0.63), ("+ no GICP\nin turns", 0.62), ("+ map CSM", 0.55), ("+ map yaw", 0.51)],
                        "Track01 pipeline (no probing)"),
                       (axes[1], [("TA baseline", 1.93), ("GNSS", 0.57), ("heading yaw", 0.47), ("Kalman CTRV", 0.41),
                                  ("+ gyro yaw", 0.28), ("+ map CSM", 0.25), ("GNSS -10 ms", 0.24)], "Track02 pipeline (no probing)")):
    ax.bar(range(len(chain)), [v for _, v in chain], color=[MUTED] + [BLUE] * (len(chain) - 1), width=0.62)
    for i, (_, v) in enumerate(chain):
        ax.text(i, v + 0.03, f"{v:.2f}", ha="center", fontsize=9, color=INK)
    ax.set_xticks(range(len(chain)), [n for n, _ in chain], fontsize=8, rotation=35, ha="right")
    ax.set_title(ttl, loc="left", color=INK)
    ax.set_ylabel("public score")
    ax.grid(axis="x", visible=False)
save(fig, "t1t2_clean_chain.png")

# ---------------------------------------------------------------- F01 final trajectories over the maps
fin = {"1": [(os.path.join(RES, "reg", "clean", "clean_mapyaw_1.csv"), "pipeline clean_mapyaw_1 (0.51)", BLUE),
             (os.path.join(RES, "reg", "lb", "lb_t1_r5.csv"), "probed lb_t1_r5 (0.36)", ORANGE)],
       "2": [(os.path.join(RES, "reg", "t2v", "t2v_tsm10.csv"), "pipeline t2v_tsm10 (0.24)", BLUE),
             (os.path.join(RES, "reg", "lb", "lb_t2_r3.csv"), "probed lb_t2_r3 (0.11)", ORANGE)],
       "3": [(os.path.join(T3, "t3_Q4.csv"), "causal t3_Q4 (public 0.28)", BLUE)]}
for t, items in fin.items():
    trajs = [(load(p), lab, col) for p, lab, col in items]
    fig, ax = plt.subplots(figsize=(9, 6.5))
    map_image(ax, t, trajs[0][0][:, 1:3])
    for X, lab, col in trajs:
        ax.plot(X[:, 1], X[:, 2], color=col, lw=1.8, label=lab)
    X = trajs[0][0]
    ax.plot(X[0, 1], X[0, 2], "o", color=AQUA, ms=8, label="start")
    ax.set_title(f"Track0{t}: final trajectory on the LiDAR map (map points, 1 m density)", loc="left", color=INK)
    ax.set_xlabel("x (m, map frame)")
    ax.set_ylabel("y (m)")
    ax.legend(fontsize=9, loc="best")
    save(fig, f"trajectory_on_map_t{t}.png")

# ---------------------------------------------------------------- F07 Track03: tracker N vs causal C3-type (A2h)
N, A = load(os.path.join(T3, "t3_full_N.csv")), load(os.path.join(T3, "t3_A2h.csv"))
fig, axes = plt.subplots(1, 2, figsize=(15, 6.2), gridspec_kw={"width_ratios": [1.7, 1]})
map_image(axes[0], "3", np.vstack([N[:, 1:3], A[:, 1:3]]))
axes[0].plot(N[:, 1], N[:, 2], color=ORANGE, lw=1.6, label="t3_full_N (odometry + GICP, no CSM)")
axes[0].plot(A[:, 1], A[:, 2], color=BLUE, lw=1.6, label="t3_A2h (+ gyro fix, ZUPT, CSM +-15 m)")
for k in (500, 950, 2150, 2500):
    axes[0].annotate(str(k), A[k, 1:3], fontsize=8, color=INK)
axes[0].legend(fontsize=8, loc="best")
axes[0].set_title("Track03: the first tracker drifts off the road", loc="left", color=INK)
d = np.hypot(*(N[:, 1:3] - A[:, 1:3]).T)
axes[1].plot(d, color=VIOLET, lw=1.8)
axes[1].axvspan(0, 409, color=GRID, alpha=0.8)
axes[1].text(20, d.max() * 0.92, "public part", fontsize=9, color=MUTED)
axes[1].set_xlabel("frame")
axes[1].set_ylabel("distance between the two tracks (m)")
axes[1].set_title("gap: ~30 m from frame ~800, ~50 m at the end", loc="left", color=INK)
save(fig, "t3_drift_N_vs_A2h.png")

# ---------------------------------------------------------------- F08 Track03 restart after the red light: X3f vs Z3a
Xf, Z = load(os.path.join(T3, "t3_X3f.csv")), load(os.path.join(T3, "t3_Z3a.csv"))
Zd = np.genfromtxt(os.path.join(T3, "t3_Z3a_diag.csv"), delimiter=",", names=True)
th = np.loadtxt(os.path.join(HOME, "SDC-midterm01", "cache_test", "Track3", "img", "f.h265.ts"), delimiter=",",
                dtype=np.int64)[:, 1] * 1e-9
sl = slice(2120, 2360)
c, s = np.cos(Z[:, 3]), np.sin(Z[:, 3])
dz = (Xf[:, 1] - Z[:, 1]) * c + (Xf[:, 2] - Z[:, 2]) * s
fig, axes = plt.subplots(1, 2, figsize=(12, 3.8))
fr = np.arange(len(Z))[sl]
axes[0].plot(fr, dz[sl], color=ORANGE, lw=2)
axes[0].set_xlabel("frame")
axes[0].set_ylabel("X3f minus Z3a, along the road (m)")
axes[0].set_title(f"before the fix: up to {abs(dz[sl].min()):.1f} m behind Z3a", loc="left", color=INK)
sp = lambda X: np.r_[np.nan, np.hypot(*np.diff(X[:, 1:3], axis=0).T) / np.diff(th)]  # noqa: E731
kern = np.ones(9) / 9
for X, lab, col in ((Xf, "X3f (before)", ORANGE), (Z, "Z3a (after: odometry gate + ZUPT needs |a| small)", BLUE)):
    v = np.convolve(np.nan_to_num(sp(X)), kern, "same")
    axes[1].plot(fr, v[sl], color=col, lw=1.8, label=lab)
axes[1].plot(fr, Zd["v_imu"][sl], color=MUTED, ls="--", lw=1.4, label="IMU speed filter")
axes[1].set_xlabel("frame")
axes[1].set_ylabel("speed (m/s), 9-frame mean")
axes[1].set_title("restart after the 43 s red light", loc="left", color=INK)
axes[1].legend(fontsize=8)
save(fig, "t3_restart_fix.png")

# ---------------------------------------------------------------- F09 Track03 end of track: PF2 slides on a flat ridge, Q4 holds
P, Q = load(os.path.join(T3, "t3_PF2.csv")), load(os.path.join(T3, "t3_Q4.csv"))
Qd = np.genfromtxt(os.path.join(T3, "t3_Q4_diag.csv"), delimiter=",", names=True)
sl = slice(2800, len(Z))
fr = np.arange(len(Z))[sl]
fig, ax = plt.subplots(figsize=(9, 3.8))
for X, lab, col in ((P, "PF2 (paint only)", ORANGE), (Q, "Q4 (IMU motion kept while braking)", BLUE)):
    a = (X[:, 1] - Z[:, 1]) * c + (X[:, 2] - Z[:, 2]) * s
    ax.plot(fr, a[sl], color=col, lw=2, label=lab)
ax2 = ax.twinx()
ax2.plot(fr, Zd["v_imu"][sl], color=MUTED, ls="--", lw=1.2)
ax2.set_ylabel("speed (m/s, dashed)", color=MUTED)
ax2.grid(False)
ax2.spines["right"].set_visible(True)
ax.set_xlabel("frame")
ax.set_ylabel("along offset from the tracker Z3a (m)")
ax.set_title("End of Track03: no paint pins the along position while the car stops", loc="left", color=INK)
ax.legend(fontsize=8, loc="lower left")
save(fig, "t3_end_slide.png")

# ---------------------------------------------------------------- F10 speed jitter (fig/t3_speed.csv)
r = np.genfromtxt(os.path.join(REPO, "docs", "report", "fig", "t3_speed.csv"), delimiter=",", names=True, skip_header=1)
fig, ax = plt.subplots(figsize=(9, 3.6))
ax.plot(r["t_s"], r["paint_only"], color=ORANGE, lw=1, label="paint only (PF2)")
ax.plot(r["t_s"], r["paint_imu"], color=BLUE, lw=2, label="paint + IMU motion (Q4)")
ax.plot(r["t_s"], r["imu_scaled"], color=MUTED, lw=1.4, ls="--", label="IMU speed x learnt scale")
ax.set_xlabel("time (s), Track03 frames 450-730")
ax.set_ylabel("speed implied by the output (m/s)")
ax.set_ylim(0, 30)
ax.legend(fontsize=8, ncol=3, loc="upper center")
ax.set_title("Lane lines fix the lateral position; between markings the along position jittered", loc="left", color=INK)
save(fig, "t3_speed_jitter.png")

# ---------------------------------------------------------------- F14 Track03 segments (public / private, standstill, turn)
fig, ax = plt.subplots(figsize=(12, 3.2))
ax.plot(Zd["v_imu"], color=BLUE, lw=1.5)
for (a, b, lab, col) in ((0, 409, "public ~13 %", YELLOW), (950, 2150, "red light: 44 % of private", AQUA),
                         (2150, 2650, "restart + 88 deg left turn", ORANGE), (2850, 3142, "final stop", VIOLET)):
    ax.axvspan(a, b, color=col, alpha=0.18, lw=0)
    ax.text((a + b) / 2, 12.3, lab, ha="center", fontsize=8, color=INK)
ax.set_ylim(0, 13.5)
ax.set_xlim(0, len(Zd))
ax.set_xlabel("frame")
ax.set_ylabel("IMU speed (m/s)")
ax.set_title("Track03: what the private part (frames 409-3141) contains", loc="left", color=INK)
save(fig, "t3_segments.png")

# ---------------------------------------------------------------- F11 Track03 layers (public score)
layers = [("first causal\n(A2h)", 0.96), ("tracker fixes\n(X3f / Z3a)", 0.80), ("+ paint,\nfront cam (PA2)", 0.49),
          ("kappa 80 +\nlever (PE3)", 0.37), ("+ side cams\n(PF2)", 0.33), ("+ IMU motion\n(Q1-Q4)", 0.28)]
fig, ax = plt.subplots(figsize=(8.5, 3.8))
ax.bar(range(len(layers)), [v for _, v in layers], color=[MUTED, MUTED, BLUE, BLUE, BLUE, AQUA], width=0.6)
for i, (_, v) in enumerate(layers):
    ax.text(i, v + 0.02, f"{v:.2f}", ha="center", fontsize=10, color=INK)
ax.set_xticks(range(len(layers)), [n for n, _ in layers], fontsize=8)
ax.set_ylabel("public score")
ax.set_title("Track03: public score after each layer", loc="left", color=INK)
ax.grid(axis="x", visible=False)
save(fig, "t3_layers.png")
