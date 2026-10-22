"""T11 – why is the GNSS of Track01 more jittery than Track02 (second-difference RMS 0.142 vs 0.052 m)?

For each track, from /localizer_node/gnss_pose (4 Hz):
  jitter_k  = |p_{k+1} - 2 p_k + p_{k-1}|      (second difference: zero for constant velocity, = noise + manoeuvres)
  jitter is split along / across the motion, summarised in 2 s windows, and compared with three explanations:
  (1) occlusion / multipath: share of map points more than 3 m above the road within 25 m sideways of the position
      (buildings, trees) from map_voxel_0.3m.pcd;
  (2) receiver mode changes: discrete jumps (second difference > 5x the median) and their timing;
  (3) driving: speed, turn rate and |acceleration| from the IMU-free GNSS track itself.
Spearman correlations between window jitter and each explanation are printed, plus a figure (--fig).

Usage: python3 tools/gnss_jitter.py [--data /w/data] [--fig docs/nhat-ky/fig/t11_gnss_jitter.png]
"""
import argparse
import csv
import os
import sys
from pathlib import Path

import numpy as np
from rosbags.highlevel import AnyReader
from scipy.spatial import cKDTree
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gicp_refine import read_pcd_binary  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_gnss(track_dir):
    """GNSS (t, x, y) and IMU (t, |gyro z|) - the turn rate must come from the IMU, not from the GNSS track itself
    (heading differentiated from jittery positions would correlate with the jitter by construction)."""
    out, imu = [], []
    with AnyReader([Path(track_dir)]) as r:
        conns = [c for c in r.connections if c.topic in ("/localizer_node/gnss_pose", "/imu/data")]
        if not any(c.topic == "/localizer_node/gnss_pose" for c in conns):
            sys.exit(f"{track_dir}: no /localizer_node/gnss_pose topic")
        for c, ts, raw in r.messages(connections=conns):
            m = r.deserialize(raw, c.msgtype)
            st = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
            if c.topic == "/imu/data":
                imu.append((st, m.angular_velocity.z))
            else:
                out.append((st, m.pose.position.x, m.pose.position.y))
    return np.array(sorted(out)), np.array(sorted(imu))


def analyse(track, data):
    track_dir = os.path.join(data, f"Track{track}")
    g, imu = read_gnss(track_dir)
    t, p = g[:, 0] - g[0, 0], g[:, 1:3]
    v = np.gradient(p, t, axis=0)
    speed = np.linalg.norm(v, axis=1)
    from scipy.ndimage import gaussian_filter1d
    wz = gaussian_filter1d(imu[:, 1], 25)  # 0.25 s at 100 Hz
    turn = np.degrees(np.abs(np.interp(g[:, 0], imu[:, 0], wz)))  # gyro bias ~0.3 deg/s left in: fine for ranking
    acc = np.abs(np.gradient(speed, t))
    dd = np.zeros_like(p)
    dd[1:-1] = p[2:] - 2 * p[1:-1] + p[:-2]
    fwd = v / np.maximum(speed[:, None], 1e-6)
    j_al = np.abs((dd * fwd).sum(1))
    j_lat = np.abs(dd[:, 0] * -fwd[:, 1] + dd[:, 1] * fwd[:, 0])
    jit = np.linalg.norm(dd, axis=1)
    jumps = jit > 5 * np.median(jit[1:-1])

    m = read_pcd_binary(os.path.join(track_dir, "map_voxel_0.3m.pcd"))
    tree = cKDTree(m[:, :2])
    occl = np.zeros(len(p))
    for k, (x, y) in enumerate(p):
        near = m[tree.query_ball_point((x, y), 25.0)]
        if len(near) == 0:
            continue
        ground = np.percentile(near[:, 2], 5)
        occl[k] = np.mean(near[:, 2] > ground + 3.0)

    win = (t // 2).astype(int)
    W = []
    for w in np.unique(win):
        s = (win == w) & (np.arange(len(t)) > 0) & (np.arange(len(t)) < len(t) - 1)
        if s.sum() < 4:
            continue
        W.append((w * 2, np.sqrt((jit[s] ** 2).mean()), np.sqrt((j_al[s] ** 2).mean()), np.sqrt((j_lat[s] ** 2).mean()),
                  speed[s].mean(), turn[s].mean(), acc[s].mean(), occl[s].mean(), jumps[s].sum()))
    W = np.array(W)
    print(f"== Track{track}: {len(t)} GNSS messages over {t[-1]:.1f} s")
    print(f"  second-difference RMS {np.sqrt((jit[1:-1] ** 2).mean()):.3f} m (along {np.sqrt((j_al[1:-1] ** 2).mean()):.3f},"
          f" lateral {np.sqrt((j_lat[1:-1] ** 2).mean()):.3f}); jumps > 5x median: {jumps.sum()}")
    print(f"  speed mean {speed.mean():.1f} m/s, stopped share {100 * (speed < 1).mean():.0f} %, turn mean "
          f"{turn.mean():.2f} deg/s, |acc| mean {acc.mean():.2f} m/s2, tall-structure share {100 * occl.mean():.1f} %")
    for name, col in (("speed", 4), ("turn rate", 5), ("|acceleration|", 6), ("tall structures (occlusion)", 7),
                      ("jumps in window", 8)):
        rho = spearmanr(W[:, 1], W[:, col]).correlation
        print(f"  Spearman(window jitter, {name:28s}) {rho:+.3f}")
    return dict(t=t, jit=jit, occl=occl, speed=speed, W=W, jumps=jumps)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", default=os.path.join(os.path.dirname(ROOT), "data"))
    p.add_argument("--fig")
    p.add_argument("--out-csv", default=os.path.join(ROOT, "docs", "nhat-ky", "data", "t11_gnss_jitter.csv"))
    a = p.parse_args()
    res = {tr: analyse(tr, a.data) for tr in (1, 2)}
    with open(a.out_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["track", "t_start_s", "jitter_rms_m", "jitter_along_m", "jitter_lat_m", "speed", "turn_deg_s",
                    "acc", "tall_structure_share", "jumps"])
        for tr, r in res.items():
            for row in r["W"]:
                w.writerow([tr, *np.round(row, 4)])
    print(f"wrote {a.out_csv}")
    with open(a.out_csv.replace(".csv", "_messages.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["track", "t_s", "second_diff_m", "tall_structure_share", "speed", "jump"])
        for tr, r in res.items():
            for k in range(1, len(r["t"]) - 1):
                w.writerow([tr, round(r["t"][k], 3), round(r["jit"][k], 4), round(r["occl"][k], 4),
                            round(r["speed"][k], 3), int(r["jumps"][k])])
    if a.fig:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(2, 1, figsize=(10, 5.5), dpi=150, sharex=True)
        for ax, (tr, r) in zip(axes, res.items()):
            ax.plot(r["t"][1:-1], r["jit"][1:-1], color="#2a78d6", lw=0.8, label="GNSS second difference (m)")
            ax.scatter(r["t"][r["jumps"]], r["jit"][r["jumps"]], s=10, color="#eb6834", label="jump > 5x median", zorder=3)
            ax2 = ax.twinx()
            ax2.plot(r["t"], 100 * r["occl"], color="#888888", lw=1, ls="--", label="tall structures within 25 m (%)")
            ax2.set_ylabel("tall structures %", fontsize=8, color="#666666")
            ax.set_ylabel("m", fontsize=8)
            ax.set_title(f"Track0{tr}", fontsize=9, loc="left")
            ax.grid(axis="y", color="#eeeeee")
        axes[0].legend(fontsize=7, frameon=False, loc="upper right")
        axes[-1].set_xlabel("time (s)")
        fig.tight_layout()
        fig.savefig(a.fig)
        print(f"wrote {a.fig}")


if __name__ == "__main__":
    main()
