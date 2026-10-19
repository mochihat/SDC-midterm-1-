"""Probe files for measuring the error field through the leaderboard (Kaggle feedback, not physics).

Each probe = base file + a known smooth change: a cosine in time (DCT mode k over the whole track) added to x, to y
or to the yaw. With the rest of the file unchanged, score = P + 0.2 Y gives one number mean(e . D) per probe
(see pos_projection.py / yaw_projection.py), i.e. the projection of the unknown per-frame error e on that mode.
Low modes first: the GNSS error changes slowly, so a few dozen modes hold most of it. All scored probes are then
combined with pos_projection.py / yaw_projection.py into the best correction inside their span.

Usage: python3 make_probes.py TRACK_DIR BASE_CSV OUT_DIR TAG --axis x|y|yaw --modes 0-6 [--amp 0.5]
  amp in metres for x / y, in degrees for yaw. Output: OUT_DIR/probe_<axis><k>_<TAG>.csv
"""
import argparse
import csv
import os

import numpy as np


def frame_times(track_dir):
    with open(os.path.join(track_dir, "3cameras_ply", "index.csv")) as f:
        t = np.array([int(r["f_ts"]) for r in csv.DictReader(f)], dtype=np.int64)
    return (t - t[0]) / 1e9


def main():
    p = argparse.ArgumentParser()
    p.add_argument("track_dir")
    p.add_argument("base")
    p.add_argument("out_dir")
    p.add_argument("tag")
    p.add_argument("--axis", required=True, choices=["x", "y", "yaw"])
    p.add_argument("--modes", required=True, help="e.g. 0-6 or 3,5,8")
    p.add_argument("--amp", type=float, default=0.5)
    a = p.parse_args()

    t = frame_times(a.track_dir)
    base = np.loadtxt(a.base, delimiter=",", skiprows=1)
    assert len(base) == len(t)
    if "-" in a.modes:
        lo, hi = (int(v) for v in a.modes.split("-"))
        modes = range(lo, hi + 1)
    else:
        modes = [int(v) for v in a.modes.split(",")]
    col = {"x": 1, "y": 2, "yaw": 3}[a.axis]
    os.makedirs(a.out_dir, exist_ok=True)
    for k in modes:
        phi = np.cos(np.pi * k * t / t[-1])
        out = base.copy()
        out[:, col] += (np.radians(a.amp) if a.axis == "yaw" else a.amp) * phi
        if a.axis == "yaw":
            out[:, 3] = (out[:, 3] + np.pi) % (2 * np.pi) - np.pi
        path = os.path.join(a.out_dir, f"probe_{a.axis}{k}_{a.tag}.csv")
        with open(path, "w") as f:
            f.write("idx,x,y,yaw\n")
            for r in out:
                f.write(f"{int(r[0])},{r[1]:.6f},{r[2]:.6f},{r[3]:.6f}\n")
        print(path)


if __name__ == "__main__":
    main()
