"""Smooth GNSS poses, interpolate them to every PLY frame and write a Kaggle CSV.

Usage (inside container):
  python3 gnss_smooth_to_csv.py /root/data/Track1 Track1 out.csv SIGMA YAW_MODE
    SIGMA     Gaussian smoothing std in GNSS samples (GNSS is 4 Hz; 0 disables)
    YAW_MODE  "gnss"    - smoothed GNSS yaw
              "heading" - direction of motion of the smoothed path (GNSS yaw while stopped)
"""
import os
import sys

import numpy as np
from scipy.interpolate import CubicSpline
from scipy.ndimage import gaussian_filter1d

from gnss_to_csv import frame_timestamps, read_gnss


def main(track_dir, track_name, output_csv, sigma, yaw_mode):
    sigma = float(sigma)
    g_t, g_x, g_y, g_yaw = read_gnss(os.path.join(track_dir, f"{track_name}.db3"))
    f_t = frame_timestamps(os.path.join(track_dir, "raw_ply"))
    g_s = (g_t - g_t[0]) / 1e9
    f_s = np.clip((f_t - g_t[0]) / 1e9, g_s[0], g_s[-1])

    if sigma > 0:
        g_x, g_y, g_yaw = (gaussian_filter1d(v, sigma, mode="nearest") for v in (g_x, g_y, g_yaw))

    sx, sy, syaw = CubicSpline(g_s, g_x), CubicSpline(g_s, g_y), CubicSpline(g_s, g_yaw)
    x, y, yaw = sx(f_s), sy(f_s), syaw(f_s)

    if yaw_mode == "heading":
        vx, vy = sx(f_s, 1), sy(f_s, 1)
        moving = np.hypot(vx, vy) > 1.0
        heading = np.arctan2(vy, vx)
        # Bring heading onto the same unwrapped branch as the GNSS yaw before mixing.
        heading = yaw + ((heading - yaw + np.pi) % (2 * np.pi) - np.pi)
        yaw = np.where(moving, heading, yaw)
    elif yaw_mode != "gnss":
        raise ValueError(f"unknown YAW_MODE {yaw_mode}")

    yaw = (yaw + np.pi) % (2 * np.pi) - np.pi
    with open(output_csv, "w") as out:
        out.write("idx,x,y,yaw\n")
        for i in range(len(f_t)):
            out.write(f"{i},{x[i]:.6f},{y[i]:.6f},{yaw[i]:.6f}\n")
    print(f"{track_name}: sigma={sigma} yaw={yaw_mode} -> {output_csv}")


if __name__ == "__main__":
    main(*sys.argv[1:6])
