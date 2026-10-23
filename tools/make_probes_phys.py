"""Leaderboard probes along physically shaped directions (Track01/02 only - probing is allowed there per the TA, 23/10;
never Track03). Round 5 (23/10): after 28 position DCT modes and 4 yaw DCT modes, the remaining error is probed along
directions an actual error source would have:
  yaw0       constant yaw offset                                    D = A
  yawrate    time shift of the yaw (lag)                            D = tau * omega(t)
  gyroscale  gyro scale error seen through the 7 s complementary filter: D = eps * highpass_7s(integrated gyro)
  yawK       cosine mode K over the track (as make_probes.py)      D = A cos(pi K t / T)
  along      constant offset along the body x axis                  D = L * heading
  lateral    constant offset along the body y axis                  D = L * left
  tshift     time shift of the positions                            D = dt * velocity
Amplitudes are only probe sizes (the score is exactly quadratic in D); the combination step rescales them.
Usage: python3 tools/make_probes_phys.py TRACK BASE.csv OUT_DIR TAG [--gyro-bias -0.22] [--kinds yaw0,yawrate,...]
"""
import argparse
import csv
import os
import sys

import numpy as np
from scipy.ndimage import gaussian_filter1d

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yaw_fusion import read_gyro  # noqa: E402

AMP = {"yaw0": 1.5, "yawrate": 1.5, "gyroscale": 0.9, "yawK": 1.5, "along": 0.5, "lateral": 0.5, "tshift": 0.05}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("track", type=int)
    p.add_argument("base")
    p.add_argument("out_dir")
    p.add_argument("tag")
    p.add_argument("--data", default="/w/data")
    p.add_argument("--gyro-bias", type=float, default=-0.22, help="deg/s")
    p.add_argument("--kinds", default="yaw0,yawrate,gyroscale,yaw5,yaw6,yaw7,yaw8,along,lateral,tshift")
    a = p.parse_args()
    track_dir = os.path.join(a.data, f"Track{a.track}")
    with open(os.path.join(track_dir, "3cameras_ply", "index.csv")) as f:
        tns = np.array([int(r["f_ts"]) for r in csv.DictReader(f)], dtype=np.int64)
    t = (tns - tns[0]) / 1e9
    base = np.loadtxt(a.base, delimiter=",", skiprows=1)
    assert len(base) == len(t)
    g_ns, g_w = read_gyro(track_dir, axis="z")
    g_t = (g_ns - tns[0]) / 1e9
    w = g_w - np.radians(a.gyro_bias)
    omega = np.degrees(np.interp(t, g_t, gaussian_filter1d(w, 5)))            # deg/s at the frames
    cum = np.concatenate([[0.0], np.cumsum(0.5 * (w[1:] + w[:-1]) * np.diff(g_t))])
    psi = np.degrees(np.interp(t, g_t, cum))
    fps = 1 / np.median(np.diff(t))
    hp = psi - gaussian_filter1d(psi, 7.0 * fps, mode="nearest")             # what a 7 s complementary filter keeps
    xy = base[:, 1:3]
    vel = np.gradient(gaussian_filter1d(xy, 0.3 * fps, axis=0, mode="nearest"), t, axis=0)
    yaw = base[:, 3]
    head = np.stack([np.cos(yaw), np.sin(yaw)], axis=1)
    left = np.stack([-np.sin(yaw), np.cos(yaw)], axis=1)
    os.makedirs(a.out_dir, exist_ok=True)
    for kind in a.kinds.split(","):
        out = base.copy()
        dyaw = None
        dpos = None
        if kind == "yaw0":
            dyaw = np.full(len(t), AMP["yaw0"])
        elif kind == "yawrate":
            dyaw = AMP["yawrate"] * omega
        elif kind == "gyroscale":
            dyaw = AMP["gyroscale"] * hp
        elif kind.startswith("yaw") and kind[3:].isdigit():
            dyaw = AMP["yawK"] * np.cos(np.pi * int(kind[3:]) * t / t[-1])
        elif kind == "along":
            dpos = AMP["along"] * head
        elif kind == "lateral":
            dpos = AMP["lateral"] * left
        elif kind == "tshift":
            dpos = AMP["tshift"] * vel
        else:
            sys.exit(f"unknown kind {kind}")
        if dyaw is not None:
            out[:, 3] = (out[:, 3] + np.radians(dyaw) + np.pi) % (2 * np.pi) - np.pi
            desc = f"yaw change RMS {np.sqrt(np.mean(dyaw ** 2)):.3f} deg (max {np.abs(dyaw).max():.2f})"
        else:
            out[:, 1:3] += dpos
            desc = f"position change RMS {np.sqrt(np.mean(np.sum(dpos ** 2, axis=1))):.3f} m"
        path = os.path.join(a.out_dir, f"probe_{kind}_{a.tag}.csv")
        with open(path, "w") as f:
            f.write("idx,x,y,yaw\n")
            for r in out:
                f.write(f"{int(r[0])},{r[1]:.6f},{r[2]:.6f},{r[3]:.6f}\n")
        print(f"{path}: {desc}")


if __name__ == "__main__":
    main()
