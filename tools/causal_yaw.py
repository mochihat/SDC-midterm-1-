"""Causal yaw (rule 10/22: current and past data only): IMU gyro + motion heading in a forward PI complementary filter.

State: yaw and gyro bias b. Between frames the gyro z rate (IMU, 100 Hz) is integrated: yaw += (w - b) dt.
At every frame where the car moves (speed from the past 0.5 s of positions > --min-speed), the error to the motion
heading e = wrap(h - yaw) pulls both:  yaw += Kp e dt,  b -= Ki e dt   (Kp = 2 zeta wn, Ki = wn^2, wn = 1 / --tau).
b starts at the mean gyro rate while the car stands still at the beginning (if it does), else 0.
While the car stands still (no motion heading), --gicp-debug gives an absolute yaw from the map: the yaw of the
converged scan matches so far, minus the camera mounting yaw --gicp-yaw-offset (+1.1 deg, a calibration constant
measured on Track01: GICP yaw - body yaw, mean +1.23 deg; Track02 +1.03 deg), averaged over the standing frames
seen so far. Track02 starts with 13 s standing where the GNSS yaw is stuck ~4.6 deg off.
The heading h comes from a causal source (yaw column of --heading-from, e.g. the forward Kalman filter of
rts_smoother.py --causal --yaw heading). Nothing uses future samples. Writes idx,x,y,yaw with x, y from --positions.

Usage: python3 tools/causal_yaw.py TRACK --positions POS.csv --heading-from KF_HEADING.csv --out OUT.csv
                                   [--tau 7] [--zeta 0.7] [--min-speed 2] [--data /w/data]
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yaw_fusion import frame_times, read_gyro  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("track", type=int)
    p.add_argument("--data", default=os.path.join(os.path.dirname(ROOT), "data"))
    p.add_argument("--positions", required=True)
    p.add_argument("--heading-from", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--tau", type=float, default=7.0, help="s; wn = 1/tau")
    p.add_argument("--zeta", type=float, default=0.7)
    p.add_argument("--min-speed", type=float, default=2.0)
    p.add_argument("--gicp-debug", help="scan-match debug CSV: absolute yaw while standing still")
    p.add_argument("--gicp-yaw-offset", type=float, default=1.1, help="deg, camera mounting yaw (calibration)")
    a = p.parse_args()
    for path in (a.positions, a.heading_from):
        if not os.path.exists(path):
            sys.exit(f"missing input: {path}")
    track_dir = os.path.join(a.data, f"Track{a.track}")
    ft = frame_times(track_dir).astype(np.float64) / 1e9
    pos = np.loadtxt(a.positions, delimiter=",", skiprows=1)
    head = np.loadtxt(a.heading_from, delimiter=",", skiprows=1)[:, 3]
    if len(pos) != len(ft) or len(head) != len(ft):
        sys.exit(f"row counts differ: frames {len(ft)}, positions {len(pos)}, heading {len(head)}")
    gt, gw = read_gyro(track_dir, axis="z")
    gt = gt.astype(np.float64) / 1e9

    # causal speed: displacement over the past 0.5 s
    speed = np.zeros(len(ft))
    j = 0
    for k in range(len(ft)):
        while ft[k] - ft[j] > 0.5:
            j += 1
        if k > j:
            speed[k] = np.hypot(*(pos[k, 1:3] - pos[j, 1:3])) / (ft[k] - ft[j])
    wn = 1.0 / a.tau
    kp, ki = 2 * a.zeta * wn, wn * wn

    # initial bias: mean gyro while standing still at the start (causal: only samples before the car moves)
    move = np.flatnonzero(speed > 0.5)
    t_move = ft[move[0]] if len(move) else ft[-1]
    still = gt < t_move
    b = float(gw[still].mean()) if still.sum() > 100 else 0.0

    gyaw = {}
    if a.gicp_debug:
        import csv
        with open(a.gicp_debug) as f:
            for r in csv.DictReader(f):
                if float(r["converged"]) > 0:
                    gyaw[int(float(r["idx"]))] = float(r["ndt_yaw"]) - np.radians(a.gicp_yaw_offset)
    acc_s = acc_c = 0.0
    n_acc = 0
    yaw = np.zeros(len(ft))
    y = head[0]
    gi = int(np.searchsorted(gt, ft[0]))
    for k in range(len(ft)):
        if k > 0:  # integrate the gyro from the previous frame to this one
            t_prev = ft[k - 1]
            while gi < len(gt) and gt[gi] <= ft[k]:
                dt = gt[gi] - t_prev
                y += (gw[gi] - b) * dt
                t_prev = gt[gi]
                gi += 1
            y += (gw[gi - 1] - b) * (ft[k] - t_prev) if gi > 0 else 0.0
            if speed[k] > a.min_speed:
                e = wrap(head[k] - y)
                dtf = ft[k] - ft[k - 1]
                y += kp * e * dtf
                b -= ki * e * dtf
        standing = speed[k] <= 0.5
        if standing and k > 0 and speed[k - 1] > 0.5:  # a new stop: start a new average
            acc_s = acc_c = 0.0
            n_acc = 0
        if gyaw and standing and k in gyaw and abs(wrap(gyaw[k] - y)) < np.radians(10):
            acc_s += np.sin(gyaw[k])
            acc_c += np.cos(gyaw[k])
            n_acc += 1
            if n_acc >= 30:
                y = np.arctan2(acc_s, acc_c)  # mean map yaw over the standing frames so far
        yaw[k] = wrap(y)
    with open(a.out, "w") as f:
        f.write("idx,x,y,yaw\n")
        for k in range(len(ft)):
            f.write(f"{k},{pos[k, 1]:.6f},{pos[k, 2]:.6f},{yaw[k]:.6f}\n")
    print(f"wrote {a.out}: initial gyro bias {np.degrees(still.sum() > 100 and gw[still].mean() or 0):+.3f} deg/s, "
          f"final {np.degrees(b):+.3f} deg/s, moving frames {np.mean(speed > a.min_speed) * 100:.0f} %, "
          f"standing map-yaw samples {n_acc}")


if __name__ == "__main__":
    main()
