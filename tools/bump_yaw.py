"""Add a smooth bump to the yaw over one time window (probe direction for yaw_projection.py).

The track time span is split into K overlapping cos^2 windows (they sum to 1); window k gets AMP_DEG added
to the yaw. Positions are kept.

Usage: python3 bump_yaw.py BASE_CSV PLY_DIR K k AMP_DEG OUT_CSV
"""
import csv
import math
import os
import sys


def main(base_csv, ply_dir, K, k, amp, out_csv):
    K, k, amp = int(K), int(k), math.radians(float(amp))
    rows = list(csv.reader(open(base_csv)))[1:]
    names = sorted(n for n in os.listdir(ply_dir) if n.endswith(".ply"))
    t = [int(n.rsplit("_ts_", 1)[1][:-4]) / 1e9 for n in names]
    t0, t1 = t[0], t[-1]
    step = (t1 - t0) / (K - 1)
    with open(out_csv, "w") as f:
        f.write("idx,x,y,yaw\n")
        for r, ti in zip(rows, t):
            u = (ti - t0) / step - k          # window centre at u = 0, neighbours at +-1
            w = math.cos(math.pi * u / 2) ** 2 if abs(u) < 1 else 0.0
            yaw = float(r[3]) + amp * w
            f.write(f"{r[0]},{r[1]},{r[2]},{(yaw + math.pi) % (2 * math.pi) - math.pi:.6f}\n")


if __name__ == "__main__":
    main(*sys.argv[1:])
