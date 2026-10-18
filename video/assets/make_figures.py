"""Figures from the real data and logs (matplotlib, dark theme) -> assets/figures/*.png.

Needs the repository at /repo and the dataset at /data (see README.md for the docker command).
Usage: python3 assets/make_figures.py
"""
import csv
import os
import shutil
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

REPO = os.environ.get("REPO", "/repo")
DATA = os.environ.get("DATA", "/data")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")
SUB = os.path.join(REPO, "docs", "nhat-ky", "submissions")
sys.path.insert(0, os.path.join(REPO, "tools"))
from pc_io import read_pcd_xyz, read_ply_xyz  # noqa: E402

BG, FG, BLUE, RED, ACCENT = "#101321", "#F5F5F5", "#3BCEAC", "#EE4266", "#FFD23F"
plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": BG, "axes.edgecolor": FG, "axes.labelcolor": FG,
                     "xtick.color": FG, "ytick.color": FG, "text.color": FG, "font.size": 16,
                     "font.family": "Noto Sans", "axes.unicode_minus": False, "legend.facecolor": BG, "legend.edgecolor": "#555"})


def load_csv(path):
    return np.array([[float(v) for v in r[1:4]] for r in list(csv.reader(open(path)))[1:]])


def frame_times(track):
    names = sorted(n for n in os.listdir(os.path.join(DATA, f"Track{track}", "raw_ply")) if n.endswith(".ply"))
    t = np.array([int(n.rsplit("_ts_", 1)[1][:-4]) for n in names]) / 1e9
    return t - t[0], names


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=120, bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)


def map_top():
    m = read_pcd_xyz(os.path.join(DATA, "Track1", "map_downsampled_1m.pcd"))
    gnss = load_csv(os.path.join(SUB, "track1", "gnss_1.csv"))
    c = gnss[:, :2].mean(0)
    keep = (np.abs(m[:, 0] - c[0]) < 650) & (np.abs(m[:, 1] - c[1]) < 450)
    m = m[keep]
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.scatter(m[:, 0], m[:, 1], s=0.15, c=m[:, 2], cmap="viridis", vmin=np.percentile(m[:, 2], 5),
               vmax=np.percentile(m[:, 2], 95), linewidths=0)
    ax.plot(gnss[:, 0], gnss[:, 1], color=RED, lw=3, label="quỹ đạo xe (GNSS) – Track01")
    ax.set_aspect("equal")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.legend(loc="upper right")
    save(fig, "map_top_track1.png")


def ply_side():
    _, names = frame_times(1)
    p = read_ply_xyz(os.path.join(DATA, "Track1", "raw_ply", names[0]))
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for ax, scale, title in ((axes[0], 1.0, "point cloud LoGeR gốc"), (axes[1], 9.0, "nhân ×9")):
        q = p * scale
        ax.scatter(q[:, 0], q[:, 2], s=0.5, c=BLUE, linewidths=0)
        ax.axhline(-0.18 * scale, color=ACCENT, lw=2, ls="--")
        ax.text(q[:, 0].max() * 0.55, -0.18 * scale + 0.08 * scale, f"mặt đường: z = {-0.18 * scale:.2f}",
                color=ACCENT)
        ax.scatter([0], [0], s=120, c=RED, marker="^", zorder=5)
        ax.set_title(title)
        ax.set_xlabel("x – phía trước")
        ax.set_ylabel("z – độ cao")
    save(fig, "ply_side_scale.png")


def baseline_vs_gnss():
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    for ax, n in zip(axes, (1, 2)):
        gnss = load_csv(os.path.join(SUB, f"track{n}", f"gnss_{n}.csv"))
        rows = [list(map(float, l.split())) for l in open(os.path.join(REPO, "docs", "nhat-ky", "data",
                                                                       "baseline_partial", f"Track{n}_result.txt"))]
        b = np.array([[r[3], r[7]] for r in rows])
        k = len(b)
        ax.plot(gnss[:k, 0], gnss[:k, 1], color=BLUE, lw=3, label="GNSS (gần đáp án)")
        ax.plot(b[:, 0], b[:, 1], color=RED, lw=2, label="baseline TA")
        ax.scatter(*b[-1], c=RED, s=60, zorder=5)
        err = np.hypot(*(b[-1] - gnss[k - 1, :2]))
        ax.set_title(f"Track0{n}: sau {k} frame lệch {err:.0f} m")
        ax.set_aspect("equal")
        ax.legend(loc="best", fontsize=12)
    save(fig, "baseline_vs_gnss.png")


def gnss_yaw_staircase():
    t, _ = frame_times(2)
    raw = load_csv(os.path.join(SUB, "track2", "gnss_2.csv"))
    fix = load_csv(os.path.join(SUB, "track2", "startfix_on_v3_2.csv"))
    sel = t < 30
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(t[sel], np.degrees(np.unwrap(raw[sel, 2])), color=RED, lw=2.5, label="yaw GNSS (nội suy)")
    ax.plot(t[sel], np.degrees(np.unwrap(fix[sel, 2])), color=BLUE, lw=2.5, label="yaw đã sửa (gyro + hướng chạy)")
    ax.axvspan(0, 13.25, color=ACCENT, alpha=0.12)
    ax.text(0.5, -17.0, "GNSS đóng băng 13 s đầu\n(xe đứng yên / chạy chậm)", color=ACCENT)
    ax.set_xlabel("thời gian (s)")
    ax.set_ylabel("yaw (độ)")
    ax.legend(loc="lower right")
    save(fig, "gnss_yaw_staircase_t2.png")


def score_timeline():
    rows = list(csv.DictReader(open(os.path.join(REPO, "docs", "nhat-ky", "data", "kaggle_submissions.csv"))))
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    for ax, n, base in zip(axes, ("1", "2"), (1.79075, 1.92587)):
        r = [x for x in rows if x["track"] == n and x["public_score"] and x["file"] not in
             ("trial.csv", "kaggle_track1_result.csv")]
        s = np.array([float(x["public_score"]) for x in r])
        best = np.minimum.accumulate(s)
        ax.scatter(range(1, len(s) + 1), s, c=[BLUE if v <= b + 1e-9 else "#777" for v, b in zip(s, best)], s=40)
        ax.step(range(1, len(s) + 1), best, where="post", color=ACCENT, lw=2.5, label="tốt nhất tới lúc đó")
        ax.axhline(base, color=RED, ls="--", lw=2, label=f"baseline TA {base}")
        ax.set_ylim(0, max(2.0, base + 0.1))
        ax.set_title(f"Track0{n}: tốt nhất {best[-1]:.4f}")
        ax.set_xlabel("lượt nộp")
        ax.set_ylabel("điểm (thấp = tốt)")
        ax.legend(fontsize=12)
    save(fig, "score_timeline.png")


def cameras():
    t, names = frame_times(1)
    idx = 1500
    stem = names[idx][:-4]  # 001500_ts_...
    img_dir = os.path.join(DATA, "Track1", "Track1_images")
    out = []
    for cam in ("fl", "f", "fr"):
        folder = os.path.join(img_dir, f"Track1_{cam}_images")
        pre = stem.split("_ts_")[0] + "_"
        match = sorted(n for n in os.listdir(folder) if n.startswith(pre))
        if match:
            dst = os.path.join(OUT, f"cam_{cam}.jpg")
            shutil.copy(os.path.join(folder, match[0]), dst)
            out.append(dst)
    print("cameras:", out)


def ndt_hist():
    def corr(name):
        rows = list(csv.DictReader(open(os.path.join(REPO, "docs", "nhat-ky", "data", "ndt_debug", name))))
        return np.array([np.hypot(float(r["ndt_x"]) - float(r["guess_x"]), float(r["ndt_y"]) - float(r["guess_y"]))
                         for r in rows])
    fig, ax = plt.subplots(figsize=(14, 6))
    bins = np.linspace(0, 8, 41)
    ax.hist(corr("e1s3_Track2_debug.csv"), bins=bins, color=RED, alpha=0.7, label="scale ×3, ô NDT 8 m")
    ax.hist(corr("e2s9r4_Track2_debug.csv"), bins=bins, color=BLUE, alpha=0.7, label="scale ×9, ô NDT 4 m")
    ax.set_xlabel("NDT kéo lệch khỏi GNSS (m)")
    ax.set_ylabel("số frame")
    ax.set_title("Track02: sửa scale làm NDT ổn định")
    ax.legend()
    save(fig, "ndt_corrections_hist.png")


def main():
    os.makedirs(OUT, exist_ok=True)
    for fn in (map_top, ply_side, baseline_vs_gnss, gnss_yaw_staircase, score_timeline, cameras, ndt_hist):
        fn()


if __name__ == "__main__":
    main()
