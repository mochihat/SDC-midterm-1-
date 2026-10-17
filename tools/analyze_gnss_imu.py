"""Statistics of the GNSS pose topic, init_guess and IMU in a track bag (run inside the container).

Usage: python3 analyze_gnss_imu.py TRACK_DIR TRACK_NAME
"""
import math
import os
import sys
from pathlib import Path

import numpy as np
from rosbags.highlevel import AnyReader
from scipy.ndimage import gaussian_filter1d


def yaw_of(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


def wrap_deg(a):
    return (a + 180.0) % 360.0 - 180.0


def main(track_dir, track):
    gnss, imu = [], []
    with AnyReader([Path(os.path.join(track_dir, f"{track}.db3"))]) as r:
        for con, ts, raw in r.messages(connections=[c for c in r.connections if c.topic == "/localizer_node/gnss_pose"]):
            m = r.deserialize(raw, con.msgtype)
            hs = m.header.stamp.sec * 10**9 + m.header.stamp.nanosec
            gnss.append((ts, hs, m.pose.position.x, m.pose.position.y, m.pose.position.z, yaw_of(m.pose.orientation)))
        for con, ts, raw in r.messages(connections=[c for c in r.connections if c.topic == "/imu/data"]):
            m = r.deserialize(raw, con.msgtype)
            a, w = m.linear_acceleration, m.angular_velocity
            imu.append((ts, a.x, a.y, a.z, w.x, w.y, w.z, yaw_of(m.orientation)))
            frame_id = m.header.frame_id
    g = np.array(gnss, dtype=float)
    bt, hs, x, y, z, yaw = g.T
    t = (bt - bt[0]) / 1e9
    print(f"== {track}: GNSS /localizer_node/gnss_pose")
    print(f"  messages {len(g)}, duration {t[-1]:.1f} s, dt mean {np.diff(t).mean():.3f} s max {np.diff(t).max():.3f} s")
    print(f"  header stamp - bag time: mean {((hs - bt) / 1e6).mean():.1f} ms (min {((hs - bt) / 1e6).min():.1f}, max {((hs - bt) / 1e6).max():.1f})")
    print(f"  z: min {z.min():.3f} max {z.max():.3f} (constant -> planar pose)")
    step = np.hypot(np.diff(x), np.diff(y))
    print(f"  path length {step.sum():.1f} m, mean speed {step.sum() / t[-1]:.2f} m/s, max step {step.max():.2f} m, "
          f"repeated positions {(step < 1e-4).sum()}")
    acc = np.diff(np.stack([x, y]), 2, axis=1)
    print(f"  position second difference RMS {np.sqrt((acc ** 2).sum(0).mean()):.3f} m (jitter indicator)")
    moving = step > 0.3
    heading = np.degrees(np.arctan2(np.diff(y), np.diff(x)))
    d = wrap_deg(heading - np.degrees(yaw[:-1]))[moving]
    print(f"  motion heading - GNSS yaw (moving): mean {d.mean():+.2f} deg, std {d.std():.2f} deg")

    ig = np.loadtxt(os.path.join(track_dir, "init_guess.txt"), delimiter=",")
    ig_yaw = math.degrees(math.atan2(ig[1, 0], ig[0, 0]))
    print(f"  init_guess vs first GNSS: position diff {math.hypot(ig[0, 3] - x[0], ig[1, 3] - y[0]):.2f} m, "
          f"yaw diff {wrap_deg(ig_yaw - math.degrees(yaw[0])):+.2f} deg, z diff {ig[2, 3] - z[0]:+.2f} m")

    i = np.array(imu, dtype=float)
    ti = (i[:, 0] - bt[0]) / 1e9
    print(f"== {track}: IMU /imu/data (frame {frame_id})")
    print(f"  messages {len(i)}, rate {len(i) / (ti[-1] - ti[0]):.0f} Hz, accel mean {np.round(i[:, 1:4].mean(0), 2)}, "
          f"gyro std {np.round(i[:, 4:7].std(0), 4)} rad/s")
    gy = np.unwrap(yaw)
    qy = np.unwrap(i[:, 7])
    dq = wrap_deg(np.degrees(np.interp(t, ti, qy) - gy))
    print(f"  IMU orientation yaw - GNSS yaw: mean {dq.mean():+.2f} deg, std {dq.std():.2f} deg")
    cum = np.concatenate([[0.0], np.cumsum(i[1:, 6] * np.diff(ti))])
    print(f"  total yaw change: GNSS {np.degrees(gy[-1] - gy[0]):+.1f} deg, IMU orientation {np.degrees(qy[-1] - qy[0]):+.1f} deg, "
          f"integrated gyro z {np.degrees(cum[-1]):+.1f} deg")

    rate = np.gradient(gaussian_filter1d(gy, 2), t)
    gz_s = gaussian_filter1d(i[:, 6], 50)
    corr = [(np.corrcoef(rate, np.interp(t + lag, ti, gz_s))[0, 1], lag) for lag in np.arange(-3, 3.001, 0.05)]
    c0 = np.corrcoef(rate, np.interp(t, ti, gz_s))[0, 1]
    cb = max(corr)
    print(f"  corr(GNSS yaw rate, gyro z): {c0:.3f} at lag 0, best {cb[0]:.3f} at lag {cb[1]:+.2f} s")

    k = 8  # 2 s windows
    best = None
    for lag in np.arange(-3, 3.001, 0.05):
        ci = np.interp(t + lag, ti, cum)
        dy, dc, dt = gy[k:] - gy[:-k], ci[k:] - ci[:-k], t[k:] - t[:-k]
        b = np.sum((dc - dy) * dt) / np.sum(dt * dt)
        res = np.degrees(np.sqrt(np.mean((dy - (dc - b * dt)) ** 2)))
        if lag == 0 or abs(lag) < 1e-9:
            at0 = (b, res)
        if best is None or res < best[0]:
            best = (res, lag, b)
    print(f"  gyro z bias fit (2 s yaw changes): lag 0 -> bias {math.degrees(at0[0]):+.3f} deg/s, residual {at0[1]:.3f} deg; "
          f"best lag {best[1]:+.2f} s -> bias {math.degrees(best[2]):+.3f} deg/s, residual {best[0]:.3f} deg")


if __name__ == "__main__":
    main(*sys.argv[1:3])
