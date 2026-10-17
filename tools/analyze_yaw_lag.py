"""Is the GNSS yaw delayed with respect to the GNSS positions and the gyro? (run inside the container)

Compares the yaw of /localizer_node/gnss_pose with the motion heading of its own (smoothed) positions
for lags of -3..3 s, and correlates the gyro z rate with both heading rates.

Usage: python3 analyze_yaw_lag.py TRACK_DIR TRACK_NAME
"""
import os
import sys

import numpy as np
from scipy.interpolate import CubicSpline
from scipy.ndimage import gaussian_filter1d

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "src", "localization", "processing_codes"))
from gnss_to_csv import read_gnss  # noqa: E402
from rts_imu_smoother import read_gyro  # noqa: E402


def main(track_dir, track):
    bag = os.path.join(track_dir, f"{track}.db3")
    g_t, x, y, yaw = read_gnss(bag)
    t = (g_t - g_t[0]) / 1e9
    sx = CubicSpline(t, gaussian_filter1d(x, 2, mode="nearest"))
    sy = CubicSpline(t, gaussian_filter1d(y, 2, mode="nearest"))
    tf = np.arange(t[0] + 4, t[-1] - 4, 0.05)
    vx, vy = sx(tf, 1), sy(tf, 1)
    moving = np.hypot(vx, vy) > 3.0
    head = np.unwrap(np.arctan2(vy, vx))
    gy = np.interp(tf, t, yaw)
    lags = np.arange(-3.0, 3.001, 0.05)

    res = []
    for lag in lags:
        d = np.degrees(gy - np.interp(tf - lag, tf, head))[moving]
        d = d - np.median(d)
        res.append((np.sqrt(np.mean(d ** 2)), lag))
    best, at0 = min(res), [r for r in res if abs(r[1]) < 1e-9][0]
    print(f"{track}: GNSS yaw vs path heading of the GNSS positions: lag 0 -> RMS {at0[0]:.2f} deg; "
          f"best lag {best[1]:+.2f} s -> RMS {best[0]:.2f} deg  (positive = GNSS yaw is late)")

    w_t, w_v = read_gyro(bag)
    gz = np.interp(tf, (w_t - g_t[0]) / 1e9, gaussian_filter1d(w_v, 10))
    for name, rate in (("path-heading rate", np.gradient(head, tf)),
                       ("GNSS-yaw rate", np.gradient(gaussian_filter1d(gy, 10), tf))):
        cc = [(np.corrcoef(rate[moving], np.interp(tf - lag, tf, gz)[moving])[0, 1], lag) for lag in lags]
        c0 = [c for c in cc if abs(c[1]) < 1e-9][0][0]
        cb = max(cc)
        print(f"   gyro z vs {name:18s}: corr {c0:.3f} at lag 0, best {cb[0]:.3f} at lag {cb[1]:+.2f} s")


if __name__ == "__main__":
    main(*sys.argv[1:3])
