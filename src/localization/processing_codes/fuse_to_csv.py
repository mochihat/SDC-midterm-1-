"""Fuse the GNSS prior with NDT corrections from a debug CSV and write a Kaggle submission.

The NDT run starts every matched frame from the prior; the correction (ndt - guess) is
gated, median-filtered and Gaussian-smoothed over time, then added back onto the prior
for every frame.

Usage:
  python3 fuse_to_csv.py PRIOR_CSV DEBUG_CSV OUT_CSV [--weight W] [--sigma-s S]
                         [--max-xy M] [--max-yaw-deg D] [--yaw-weight WY] [--demean]

--demean removes the mean along-track / lateral correction (vehicle frame) before smoothing: the prior keeps the
long-run average position, scan matching only adds the local deviations (complementary filter). Use it when the
matcher has a constant offset (e.g. camera mounting) that the prior does not have.
  python3 fuse_to_csv.py PRIOR_CSV DEBUG_CSV --stats     # print correction statistics only
"""
import argparse
import csv

import numpy as np
from scipy.ndimage import gaussian_filter1d, median_filter


def wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


def load_prior(path):
    rows = list(csv.reader(open(path)))[1:]
    return np.array([[float(v) for v in r[1:4]] for r in rows])


def load_debug(path):
    with open(path) as f:
        rows = list(csv.DictReader(f))
    cols = {k: np.array([float(r[k]) for r in rows]) for k in rows[0]}
    cols["idx"] = cols["idx"].astype(int)
    return cols


def corrections(dbg):
    dx = dbg["ndt_x"] - dbg["guess_x"]
    dy = dbg["ndt_y"] - dbg["guess_y"]
    dyaw = wrap(dbg["ndt_yaw"] - dbg["guess_yaw"])
    # Express the translation correction in the vehicle frame (along / lateral) for diagnostics.
    c, s = np.cos(dbg["guess_yaw"]), np.sin(dbg["guess_yaw"])
    return dx, dy, dyaw, dx * c + dy * s, -dx * s + dy * c


def print_stats(dbg):
    dx, dy, dyaw, along, lat = corrections(dbg)
    ok = dbg["converged"] > 0
    r = np.hypot(dx, dy)
    print(f"frames matched {len(r)}, converged {ok.sum()}")
    for name, v in [("|dxy| m", r), ("along m", along), ("lateral m", lat), ("dyaw deg", np.degrees(dyaw))]:
        v = v[ok]
        print(f"  {name:10s} median {np.median(v):+7.3f}  mean {v.mean():+7.3f}  std {v.std():6.3f}  "
              f"p10 {np.percentile(v, 10):+7.3f}  p90 {np.percentile(v, 90):+7.3f}")
    for thr in (0.5, 1, 2, 3, 5):
        print(f"  share |dxy| <= {thr} m: {(r[ok] <= thr).mean():.2%}")
    print(f"  score median {np.median(dbg['score'][ok]):.4f}")


def fuse(prior, dbg, weight, yaw_weight, sigma_s, max_xy, max_yaw_deg, demean=False, need_converged=True):
    dx, dy, dyaw, along, lat = corrections(dbg)
    good = (np.hypot(dx, dy) <= max_xy) & (np.abs(np.degrees(dyaw)) <= max_yaw_deg)
    if need_converged:
        good &= dbg["converged"] > 0
    if demean:
        c, s = np.cos(dbg["guess_yaw"]), np.sin(dbg["guess_yaw"])
        along = along - along[good].mean()
        lat = lat - lat[good].mean()
        dx, dy = along * c - lat * s, along * s + lat * c
        print(f"removed mean correction: along {np.mean(corrections(dbg)[3][good]):+.3f} m, "
              f"lateral {np.mean(corrections(dbg)[4][good]):+.3f} m")
    idx = dbg["idx"][good]
    t = (dbg["timestamp_ns"][good] - dbg["timestamp_ns"][0]) / 1e9
    print(f"using {good.sum()}/{len(good)} matched frames")

    # Frame timestamps for all frames are interpolated from the matched frames' (idx, t) pairs.
    all_idx = np.arange(len(prior))
    all_t = np.interp(all_idx, dbg["idx"], (dbg["timestamp_ns"] - dbg["timestamp_ns"][0]) / 1e9)

    out = prior.copy()
    step = np.median(np.diff(t)) if len(t) > 1 else 1.0
    for col, values, w in ((0, dx, weight), (1, dy, weight), (2, dyaw, yaw_weight)):
        v = values[good]
        v = median_filter(v, size=5, mode="nearest")
        if sigma_s > 0:
            v = gaussian_filter1d(v, sigma_s / step, mode="nearest")
        out[:, col] += w * np.interp(all_t, t, v)
    out[:, 2] = wrap(out[:, 2])
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("prior")
    p.add_argument("debug")
    p.add_argument("out", nargs="?")
    p.add_argument("--stats", action="store_true")
    p.add_argument("--weight", type=float, default=1.0)
    p.add_argument("--yaw-weight", type=float, default=1.0)
    p.add_argument("--sigma-s", type=float, default=2.0)
    p.add_argument("--max-xy", type=float, default=3.0)
    p.add_argument("--max-yaw-deg", type=float, default=5.0)
    p.add_argument("--demean", action="store_true")
    p.add_argument("--any", action="store_true", help="also use frames the matcher did not mark converged")
    a = p.parse_args()

    prior, dbg = load_prior(a.prior), load_debug(a.debug)
    if a.stats or not a.out:
        print_stats(dbg)
        return
    out = fuse(prior, dbg, a.weight, a.yaw_weight, a.sigma_s, a.max_xy, a.max_yaw_deg, a.demean, not a.any)
    with open(a.out, "w") as f:
        f.write("idx,x,y,yaw\n")
        for i, (x, y, yaw) in enumerate(out):
            f.write(f"{i},{x:.6f},{y:.6f},{yaw:.6f}\n")
    d = out - prior
    print(f"wrote {a.out}: shift from prior RMS {np.sqrt((d[:, 0]**2 + d[:, 1]**2).mean()):.3f} m, "
          f"yaw RMS {np.degrees(np.sqrt((wrap(d[:, 2])**2).mean())):.2f} deg")


if __name__ == "__main__":
    main()
