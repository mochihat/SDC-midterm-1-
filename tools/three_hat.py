"""Offline metric 2: error size of each position source without ground truth ("three-cornered hat").

With k >= 3 sources whose errors are independent, the variance of the difference of two sources is the sum of their
error variances: var(i - j) = s_i^2 + s_j^2. All pairs give a small least-squares system for the s_i^2.
Done separately along-track and lateral (vehicle frame from the first source's yaw), after removing each source's
constant offset (the mean of its difference to the first source), on the frames every source has, and for two time
scales: per frame, and low-passed (Gaussian, --sigma seconds) which is what the fusion actually uses.

A negative s^2 means the independence assumption is broken (two sources share an error), e.g. two matchers on the
same point cloud.

Sources: NAME=PATH, PATH is a result CSV (idx,x,y,yaw) or a scan-matching debug CSV (ndt_x, ndt_y; converged
frames within --max-xy of the first source only).

Usage: python3 tools/three_hat.py TRACK A=gnss.csv B=gicp_debug.csv C=raw_gicp_debug.csv [D=...] [--sigma 2]
"""
import argparse
import csv
import os
import sys

import numpy as np
from scipy.ndimage import gaussian_filter1d

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gicp_refine import frame_list  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(path, n):
    """(n, 2) positions, NaN where the source has no valid frame."""
    with open(path) as f:
        rows = list(csv.DictReader(f))
    xy = np.full((n, 2), np.nan)
    if "ndt_x" in rows[0]:
        for r in rows:
            if float(r["converged"]) > 0:
                xy[int(r["idx"])] = float(r["ndt_x"]), float(r["ndt_y"])
    else:
        for r in rows:
            xy[int(r["idx"])] = float(r["x"]), float(r["y"])
    return xy


def lowpass(v, ok, sigma):
    """Gaussian smoothing over the valid frames only (normalised convolution)."""
    w = ok.astype(float)
    num = gaussian_filter1d(np.where(ok, v, 0.0), sigma, mode="nearest")
    den = gaussian_filter1d(w, sigma, mode="nearest")
    return num / np.maximum(den, 1e-9)


def solve(names, diffs):
    """diffs[(i, j)] = variance of source i - source j -> per-source variances (least squares)."""
    k = len(names)
    A, b = [], []
    for (i, j), v in diffs.items():
        row = np.zeros(k)
        row[i] = row[j] = 1
        A.append(row)
        b.append(v)
    return np.linalg.lstsq(np.array(A), np.array(b), rcond=None)[0]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("track", type=int)
    p.add_argument("sources", nargs="+")
    p.add_argument("--data", default=os.path.join(os.path.dirname(ROOT), "data"))
    p.add_argument("--sigma", type=float, default=2.0)
    p.add_argument("--max-xy", type=float, default=2.0)
    a = p.parse_intermixed_args()

    frames = frame_list(os.path.join(a.data, f"Track{a.track}"))
    n = len(frames)
    t = np.array([f[1] for f in frames]) / 1e9
    step = np.median(np.diff(t))
    names, paths = zip(*(s.split("=", 1) for s in a.sources))
    first = np.loadtxt(paths[0], delimiter=",", skiprows=1)
    yaw = first[:, 3]
    fwd, lat = np.c_[np.cos(yaw), np.sin(yaw)], np.c_[-np.sin(yaw), np.cos(yaw)]
    XY = [load(path, n) for path in paths]
    ok = np.ones(n, bool)
    for xy in XY[1:]:
        d = np.linalg.norm(xy - XY[0], axis=1)
        ok &= np.isfinite(d) & (d <= a.max_xy)
    print(f"Track{a.track}: {ok.sum()}/{n} frames where every source is valid; sources: {', '.join(names)}")

    for label, sigma in (("per frame", 0), (f"low-passed {a.sigma:g} s", a.sigma / step)):
        print(f"== {label}")
        for axis_name, axis in (("along", fwd), ("lateral", lat)):
            comp = []
            for xy in XY:
                d = ((xy - XY[0]) * axis).sum(1)  # relative to source 0 (its own column is 0)
                c = d - np.nanmean(d[ok])
                comp.append(lowpass(c, ok, sigma)[ok] if sigma else c[ok])
            diffs = {(i, j): np.var(comp[i] - comp[j]) for i in range(len(XY)) for j in range(i + 1, len(XY))}
            s2 = solve(names, diffs)
            print(f"  {axis_name:8s}" + "  ".join(
                f"{nm} {np.sign(v) * np.sqrt(abs(v)):+.3f} m{' (!)' if v < 0 else ''}" for nm, v in zip(names, s2)))
    print("(!) negative variance: those sources share an error, the independence assumption fails")


if __name__ == "__main__":
    main()
