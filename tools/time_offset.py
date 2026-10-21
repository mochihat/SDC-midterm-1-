"""Time offset between the GNSS positions and the IMU, measured from the data (no leaderboard).

The along-track acceleration seen by the GNSS (second derivative of the speed along the GNSS track) must match the
forward acceleration of the IMU. Both are smoothed alike (Gaussian, --sigma s) and cross-correlated over lags;
the peak (parabolic fit) is the GNSS delay. A delay tau shifts every GNSS position by ~ -v * tau along the track,
i.e. 0.2 m at 10 m/s for 20 ms. The IMU forward axis is found from the data: the horizontal accelerometer
direction (gravity removed by the mean) that best correlates with the GNSS acceleration.

Usage: python3 tools/time_offset.py TRACK [--sigma 0.5] [--max-lag 0.5]
  positive result = GNSS positions lag the IMU (the GNSS reports where the car was tau seconds earlier)
"""
import argparse
import os
from pathlib import Path

import numpy as np
from rosbags.highlevel import AnyReader
from scipy.ndimage import gaussian_filter1d

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def stamp(h):
    return h.stamp.sec + h.stamp.nanosec * 1e-9


def read(bag):
    imu, gnss = [], []
    with AnyReader([Path(bag)]) as r:
        conns = [c for c in r.connections if c.topic in ("/imu/data", "/localizer_node/gnss_pose")]
        for c, ts, raw in r.messages(connections=conns):
            m = r.deserialize(raw, c.msgtype)
            if c.topic == "/imu/data":
                a = m.linear_acceleration
                imu.append((stamp(m.header), a.x, a.y, a.z))
            else:
                p = m.pose.position
                gnss.append((stamp(m.header), p.x, p.y))
    return np.array(sorted(imu)), np.array(sorted(gnss))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("track", type=int)
    ap.add_argument("--data", default=os.path.join(os.path.dirname(ROOT), "data"))
    ap.add_argument("--sigma", type=float, default=0.5)
    ap.add_argument("--max-lag", type=float, default=0.5)
    a = ap.parse_args()
    imu, gnss = read(os.path.join(a.data, f"Track{a.track}"))
    t0 = gnss[0, 0]
    dt = 0.01
    t = np.arange(0, gnss[-1, 0] - t0, dt)
    # GNSS: positions -> 100 Hz (linear), smoothed, then velocity / along-track acceleration.
    x = np.interp(t, gnss[:, 0] - t0, gnss[:, 1])
    y = np.interp(t, gnss[:, 0] - t0, gnss[:, 2])
    s = a.sigma / dt
    vx, vy = np.gradient(gaussian_filter1d(x, s), dt), np.gradient(gaussian_filter1d(y, s), dt)
    v = np.hypot(vx, vy)
    acc_g = np.gradient(gaussian_filter1d(v, s), dt)
    # IMU: horizontal accelerometer components, gravity (mean) removed, same smoothing.
    ai = np.stack([np.interp(t, imu[:, 0] - t0, imu[:, k]) for k in (1, 2, 3)], 1)
    ai -= ai.mean(0)
    # GNSS acceleration went through two Gaussian passes (positions, speed); zero-phase, so no lag, but match the width.
    ai = gaussian_filter1d(ai, s * np.sqrt(2), axis=0)
    moving = v > 2
    # Forward axis: least squares of acc_g on the three IMU axes.
    coef = np.linalg.lstsq(ai[moving], acc_g[moving], rcond=None)[0]
    acc_i = ai @ coef
    print(f"Track{a.track}: IMU forward-axis fit {np.round(coef, 3)}, corr at lag 0 "
          f"{np.corrcoef(acc_i[moving], acc_g[moving])[0, 1]:.3f}")
    lags = np.arange(-a.max_lag, a.max_lag + 1e-9, dt)
    cc = []
    m = moving.copy()
    edge = int(a.max_lag / dt) + 1
    m[:edge] = m[-edge:] = False
    for L in lags:
        k = int(round(L / dt))
        cc.append(np.corrcoef(acc_g[m], np.roll(acc_i, k)[m])[0, 1])
    cc = np.array(cc)
    j = int(np.argmax(cc))
    if 0 < j < len(cc) - 1:
        den = cc[j - 1] - 2 * cc[j] + cc[j + 1]
        off = 0.5 * (cc[j - 1] - cc[j + 1]) / den if den != 0 else 0.0
    else:
        off = 0.0
    tau = lags[j] + off * dt
    print(f"  peak corr {cc[j]:.3f} at GNSS delay {tau * 1000:+.1f} ms  (corr at 0: {cc[len(cc) // 2]:.3f})")
    # Bootstrap over 10 s blocks for an uncertainty.
    rng = np.random.default_rng(0)
    blocks = np.array_split(np.flatnonzero(m), max(int((m.sum() * dt) / 10), 2))
    est = []
    for _ in range(200):
        pick = np.concatenate([blocks[i] for i in rng.integers(0, len(blocks), len(blocks))])
        c2 = [np.corrcoef(acc_g[pick], np.roll(acc_i, int(round(L / dt)))[pick])[0, 1] for L in lags]
        est.append(lags[int(np.argmax(c2))])
    print(f"  bootstrap (10 s blocks): {np.mean(est) * 1000:+.0f} ms +- {np.std(est) * 1000:.0f} ms")


if __name__ == "__main__":
    main()
