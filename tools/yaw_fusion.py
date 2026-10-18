"""Yaw from a complementary filter: IMU gyro for the fast part, motion heading of the trajectory for the slow part.

  yaw = psi_g + G_tau * (h_body - psi_g)

psi_g    integral of the yaw rate = gyro vector projected on the measured gravity direction (the IMU is tilted
         ~5 deg; --gyro-axis z uses the raw z axis) (bias removed: least-squares fit of a constant rate offset so that psi_g follows
         the motion heading on moving frames; no leaderboard involved), sampled at the image timestamps
h_body   motion heading of the given trajectory (Gaussian-smoothed positions, sigma --heading-sigma s), minus the
         lever-arm slip atan(d * omega / v) of a point d metres ahead of the rear axle (--lever d, 0 = none;
         --auto-lever fits d by regressing the high-passed heading - gyro yaw on the curvature omega / v)
G_tau    zero-phase Gaussian smoothing with sigma tau seconds, weighted by "moving" (speed > --min-speed), so the
         gyro carries everything faster than ~tau and the heading fixes the gyro drift

Writes idx,x,y,yaw with x, y copied from --positions.

Usage (sdc-reg image):
  python3 tools/yaw_fusion.py 1 --positions POS.csv --out OUT.csv [--tau 5] [--lever 0] [--heading-sigma 0.5]
"""
import argparse
import csv
import os
from pathlib import Path

import numpy as np
from rosbags.highlevel import AnyReader
from scipy.ndimage import gaussian_filter1d

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


def frame_times(track_dir):
    with open(os.path.join(track_dir, "3cameras_ply", "index.csv")) as f:
        return np.array([int(r["f_ts"]) for r in csv.DictReader(f)], dtype=np.int64)


def read_gyro(bag_path, axis="gravity"):
    """IMU timestamps and yaw rate: the gyro vector projected on the mean accelerometer direction (vertical)."""
    with AnyReader([Path(bag_path)]) as r:
        conns = [c for c in r.connections if c.topic == "/imu/data"]
        rows = []
        for c, ts, raw in r.messages(connections=conns):
            m = r.deserialize(raw, c.msgtype)
            w, acc = m.angular_velocity, m.linear_acceleration
            rows.append((ts, w.x, w.y, w.z, acc.x, acc.y, acc.z))
    rows.sort()
    a = np.array(rows, dtype=np.float64)
    if axis == "z":
        return a[:, 0].astype(np.int64), a[:, 3]
    up = a[:, 4:7].mean(axis=0)
    up /= np.linalg.norm(up)
    return a[:, 0].astype(np.int64), a[:, 1:4] @ up


def weighted_smooth(values, weights, sigma):
    if sigma <= 0:
        return values
    num = gaussian_filter1d(values * weights, sigma, mode="nearest")
    den = gaussian_filter1d(weights.astype(float), sigma, mode="nearest")
    return num / np.maximum(den, 1e-9)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("track", type=int)
    p.add_argument("--data", default=os.path.join(os.path.dirname(ROOT), "data"))
    p.add_argument("--positions", required=True, help="CSV idx,x,y,yaw whose x, y are written to the output")
    p.add_argument("--heading-from", help="CSV whose x, y give the motion heading (default: --positions)")
    p.add_argument("--out", required=True)
    p.add_argument("--tau", type=float, default=5.0, help="complementary crossover (Gaussian sigma, s)")
    p.add_argument("--lever", type=float, default=0.0, help="slip correction: point d m ahead of the rear axle")
    p.add_argument("--heading-sigma", type=float, default=0.5, help="position smoothing for the heading (s)")
    p.add_argument("--min-speed", type=float, default=2.0)
    p.add_argument("--gyro-shift", type=float, default=0.0, help="add this many seconds to the IMU clock")
    p.add_argument("--gyro-axis", default="gravity", choices=["gravity", "z"])
    p.add_argument("--auto-lever", action="store_true")
    p.add_argument("--lf-from-debug", help="scan-matching debug CSV: use its yaw (ndt_yaw, gated <= 2 m / 3 deg) "
                                          "instead of the motion heading as the slow reference")
    a = p.parse_args()

    track_dir = os.path.join(a.data, f"Track{a.track}")
    t_ns = frame_times(track_dir)
    t = (t_ns - t_ns[0]) / 1e9
    pos = np.loadtxt(a.positions, delimiter=",", skiprows=1)
    assert len(pos) == len(t), (len(pos), len(t))
    fps = (len(t) - 1) / (t[-1] - t[0])

    # Motion heading from the smoothed trajectory.
    src = np.loadtxt(a.heading_from, delimiter=",", skiprows=1) if a.heading_from else pos
    xs = gaussian_filter1d(src[:, 1], a.heading_sigma * fps, mode="nearest")
    ys = gaussian_filter1d(src[:, 2], a.heading_sigma * fps, mode="nearest")
    vx, vy = np.gradient(xs, t), np.gradient(ys, t)
    speed = np.hypot(vx, vy)
    heading = np.unwrap(np.arctan2(vy, vx))
    moving = speed > a.min_speed

    # Gyro integral at the image times.
    g_ns, g_w = read_gyro(track_dir, a.gyro_axis)  # ROS 2 bag directory (metadata.yaml + .db3)
    g_t = (g_ns - t_ns[0]) / 1e9 + a.gyro_shift
    cum = np.concatenate([[0.0], np.cumsum(0.5 * (g_w[1:] + g_w[:-1]) * np.diff(g_t))])
    psi_raw = np.interp(t, g_t, cum)
    omega = np.interp(t, g_t, g_w)

    # Bias: fit heading - psi_raw = c + b * t on moving frames (robust: two passes with a 3-sigma cut).
    d = np.unwrap(heading - psi_raw)
    keep = moving.copy()
    for _ in range(2):
        A = np.stack([np.ones(keep.sum()), t[keep]], axis=1)
        c, b = np.linalg.lstsq(A, d[keep], rcond=None)[0]
        res = d - (c + b * t)
        keep = moving & (np.abs(res) < 3 * res[moving].std())
    psi_g = psi_raw + c + b * t
    omega_c = omega + b

    # Lever-arm slip: velocity direction of a point d ahead of the rear axle = body yaw + atan(d * omega / v).
    lever = a.lever
    if a.auto_lever:
        sig = a.heading_sigma * fps
        r = np.unwrap(heading - gaussian_filter1d(psi_g, sig, mode="nearest"))
        r -= gaussian_filter1d(r, 10 * fps, mode="nearest")
        kap = gaussian_filter1d(omega_c, sig, mode="nearest") / np.maximum(speed, 0.5)
        kap -= gaussian_filter1d(kap, 10 * fps, mode="nearest")
        m = speed > 3
        lever = float(np.sum(kap[m] * r[m]) / np.sum(kap[m] ** 2))
        print(f"auto lever d = {lever:+.2f} m")
    h_body = heading - (np.arctan2(lever * omega_c, np.maximum(speed, 0.5)) if lever else 0.0)

    ref, w_ref = h_body, moving.astype(float)
    if a.lf_from_debug:
        with open(a.lf_from_debug) as f:
            rows = list(csv.DictReader(f))
        idx = np.array([int(r["idx"]) for r in rows])
        col = lambda k: np.array([float(r[k]) for r in rows])
        dyaw = wrap(col("ndt_yaw") - col("guess_yaw"))
        good = (np.hypot(col("ndt_x") - col("guess_x"), col("ndt_y") - col("guess_y")) <= 2) & (np.abs(np.degrees(dyaw)) <= 3)
        ref = np.zeros(len(t))
        w_ref = np.zeros(len(t))
        ref[idx[good]] = col("ndt_yaw")[good]
        w_ref[idx[good]] = 1.0
        ref = psi_g + wrap(ref - psi_g)  # same branch as psi_g
        print(f"slow reference: scan-matching yaw on {int(w_ref.sum())} frames")
    corr = weighted_smooth(np.unwrap(ref - psi_g), w_ref, a.tau * fps)
    yaw = wrap(psi_g + corr)

    with open(a.out, "w") as f:
        f.write("idx,x,y,yaw\n")
        for i in range(len(t)):
            f.write(f"{int(pos[i, 0])},{pos[i, 1]:.6f},{pos[i, 2]:.6f},{yaw[i]:.6f}\n")

    hr = np.gradient(heading, t)
    lag_corr = {lag: np.corrcoef(np.interp(t[moving] + lag, g_t, g_w), hr[moving])[0, 1] for lag in (-0.2, 0.0, 0.2)}
    print(f"gyro bias {np.degrees(-b):+.3f} deg/s (fit), moving frames {moving.mean():.0%}; "
          f"corr(heading rate, gyro) at lag -0.2/0/+0.2 s: " + " ".join(f"{v:.3f}" for v in lag_corr.values()))
    print(f"heading - gyro yaw: residual std {np.degrees(res[moving].std()):.2f} deg; "
          f"correction applied RMS {np.degrees(np.sqrt(((corr - corr.mean()) ** 2).mean())):.2f} deg")
    print(f"wrote {a.out}: yaw change vs input yaw RMS {np.degrees(np.sqrt((wrap(yaw - pos[:, 3]) ** 2).mean())):.2f} deg")


if __name__ == "__main__":
    main()
