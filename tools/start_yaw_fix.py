"""Yaw while the vehicle is (almost) standing still, from the gyro instead of the GNSS.

The GNSS pose yaw is computed from GNSS position displacements (updated every ~1.25 s) and is meaningless
at low speed: on Track02 it stays frozen for the first 13 s. Here the yaw before the vehicle first exceeds
SPEED_MPS is rebuilt as
    yaw(t) = heading(t_s) - integral_t^{t_s} (gyro_z - bias) dt
with t_s the first time above SPEED_MPS, heading(t_s) the on-time motion heading from HEADING_CSV, and the
gyro bias averaged over the standstill (true yaw rate = 0). After t_s the yaw of BASE_CSV is kept, with a
linear blend over BLEND_S seconds. Positions of BASE_CSV are kept.

Usage (inside container):
  python3 start_yaw_fix.py TRACK_DIR TRACK_NAME BASE_CSV HEADING_CSV OUT_CSV [SPEED_MPS] [BLEND_S]
"""
import csv
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "src", "localization", "processing_codes"))
from gnss_to_csv import frame_timestamps, read_gnss  # noqa: E402
from rts_imu_smoother import read_gyro  # noqa: E402


def load(path):
    rows = list(csv.reader(open(path)))[1:]
    return rows, np.array([[float(v) for v in r[1:4]] for r in rows])


def main(track_dir, track, base_csv, heading_csv, out_csv, speed="4.0", blend="1.0"):
    speed, blend = float(speed), float(blend)
    bag = os.path.join(track_dir, f"{track}.db3")
    g_t, gx, gy, _ = read_gnss(bag)
    w_t, w_v = read_gyro(bag)
    f_t = frame_timestamps(os.path.join(track_dir, "raw_ply"))
    t0 = g_t[0]
    tg, tw, tf = (g_t - t0) / 1e9, (w_t - t0) / 1e9, (f_t - t0) / 1e9

    v = np.r_[0.0, np.hypot(np.diff(gx), np.diff(gy)) / np.diff(tg)]
    t_s = tg[np.argmax(v > speed)]
    still = tg[(v < 0.1) & (tg < t_s)]
    if len(still) >= 2:
        mask = (tw >= still.min()) & (tw <= still.max())
        bias = w_v[mask].mean()
    else:
        bias = 0.0

    rows, base = load(base_csv)
    _, head = load(heading_csv)
    base_yaw = np.unwrap(base[:, 2])
    head_u = np.unwrap(head[:, 2])
    i_s = int(np.argmin(np.abs(tf - t_s)))
    cum = np.concatenate([[0.0], np.cumsum((w_v[1:] - bias) * np.diff(tw))])
    cum_f = np.interp(tf, tw, cum)
    start = head_u[i_s] - (cum_f[i_s] - cum_f)
    # Same 2*pi branch as the base around t_s.
    start += 2 * np.pi * np.round((base_yaw[i_s] - start[i_s]) / (2 * np.pi))

    w = np.clip((tf - t_s) / blend, 0.0, 1.0) if blend > 0 else (tf > t_s).astype(float)
    # Before t_s: rebuilt yaw; blend window: from the rebuilt value at t_s (held, plus gyro) towards the base.
    hold = start[i_s] + (cum_f - cum_f[i_s])
    rebuilt = np.where(tf <= t_s, start, hold)
    yaw = (1 - w) * rebuilt + w * base_yaw
    n_changed = int(np.sum(w < 1))
    print(f"{track}: speed > {speed} m/s at t_s = {t_s:.2f} s; gyro bias (standstill) {np.degrees(bias):+.3f} deg/s; "
          f"start yaw {np.degrees(start[0]):.3f} deg; base yaw at t=0 {np.degrees(base_yaw[0]):.3f} deg; "
          f"{n_changed} frames changed, RMS change {np.degrees(np.sqrt(np.mean((yaw - base_yaw) ** 2))):.3f} deg")
    with open(out_csv, "w") as f:
        f.write("idx,x,y,yaw\n")
        for r, a in zip(rows, yaw):
            f.write(f"{r[0]},{r[1]},{r[2]},{(a + math.pi) % (2 * math.pi) - math.pi:.6f}\n")


if __name__ == "__main__":
    main(*sys.argv[1:])
