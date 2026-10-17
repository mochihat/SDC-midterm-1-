"""Body yaw from motion heading for a reference point ahead of the rear axle.

For a point l metres ahead of the rear axle, the velocity direction leads the body yaw in turns:
    heading = yaw + atan(l * kappa),  kappa = omega / v  (path curvature)
so yaw = heading - atan(l * kappa). kappa is computed from a smooth heading series (SOURCE_CSV) and
the speed of its positions. The output keeps the positions of BASE_CSV and subtracts atan(l * kappa)
from its yaw.

Usage: python3 curvature_yaw.py BASE_CSV SOURCE_CSV PLY_DIR LEVER_M OUT_CSV
"""
import csv
import math
import os
import sys

import numpy as np
from scipy.ndimage import gaussian_filter1d


def load(path):
    rows = list(csv.reader(open(path)))[1:]
    return rows, np.array([[float(v) for v in r[1:4]] for r in rows])


def main(base_csv, source_csv, ply_dir, lever, out_csv):
    lever = float(lever)
    rows, base = load(base_csv)
    _, src = load(source_csv)
    names = sorted(n for n in os.listdir(ply_dir) if n.endswith(".ply"))
    t = np.array([int(n.rsplit("_ts_", 1)[1][:-4]) for n in names]) / 1e9
    heading = np.unwrap(src[:, 2])
    # ~0.25 s smoothing of rates (frames are ~28 Hz).
    omega = gaussian_filter1d(np.gradient(heading, t), 7, mode="nearest")
    v = gaussian_filter1d(np.hypot(np.gradient(src[:, 0], t), np.gradient(src[:, 1], t)), 7, mode="nearest")
    kappa = np.where(v > 2.0, omega / np.maximum(v, 1e-6), 0.0)
    corr = np.arctan(lever * kappa)
    print(f"curvature: RMS {np.sqrt(np.mean(kappa ** 2)):.5f} 1/m, max {np.abs(kappa).max():.4f} 1/m; "
          f"yaw change for l={lever} m: RMS {np.degrees(np.sqrt(np.mean(corr ** 2))):.3f} deg, max {np.degrees(np.abs(corr).max()):.3f} deg")
    yaw = base[:, 2] - corr
    with open(out_csv, "w") as f:
        f.write("idx,x,y,yaw\n")
        for r, a in zip(rows, yaw):
            f.write(f"{r[0]},{r[1]},{r[2]},{(a + math.pi) % (2 * math.pi) - math.pi:.6f}\n")


if __name__ == "__main__":
    main(*sys.argv[1:])
