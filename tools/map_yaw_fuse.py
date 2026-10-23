"""Clean Track01/02 yaw from the map (23/10): gyro for the fast part, the GICP yaw of the clean pipeline's scan matching
for the slow part, instead of the GNSS motion heading.

Leaderboard probes of Track01 (docs/nhat-ky/12 section 9) showed that the clean yaw carries slow errors (cosine modes 2, 4
and 7 of the track, periods ~107 / 53 / 30 s, 0.3-0.7 deg) that come with the slow reference, the GNSS motion heading
(tools/yaw_fusion.py). Here the slow reference is the map instead: per frame the GICP yaw g_k of gicp_refine.py
(column ndt_yaw of its debug CSV, accepted matches only), the gyro yaw G(t) integrated at the frame times, and
  yaw(t) = G(t) + S_sigma[g - G](t) - c
with S_sigma a weighted Gaussian smoothing in time (both directions - Track01/02 need not be causal) and c the circular
mean of the difference to the prior's yaw (--demean: the GNSS mean heading is kept, the map only corrects how the yaw
error changes along the track). Positions are copied from the prior. Uses no leaderboard information.

Usage: python3 tools/map_yaw_fuse.py TRACK PRIOR.csv GICP_DEBUG.csv OUT.csv [--sigma-t 15] [--gyro-axis gravity]
         [--demean] [--weight-prior W]
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yaw_fusion import read_gyro  # noqa: E402


def wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


def wsmooth(x, w, t, sigma):
    """Weighted Gaussian smoothing in time of x (n,) with weights w (n,)."""
    out = np.empty_like(x)
    for i in range(len(t)):
        g = w * np.exp(-0.5 * ((t - t[i]) / sigma) ** 2)
        out[i] = np.sum(g * x) / max(g.sum(), 1e-12)
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("track", type=int)
    p.add_argument("prior")
    p.add_argument("gicp")
    p.add_argument("out")
    p.add_argument("--data", default="/w/data")
    p.add_argument("--sigma-t", type=float, default=15.0, help="s, smoothing of the map - gyro yaw difference")
    p.add_argument("--gyro-axis", default="gravity", choices=["gravity", "z"])
    p.add_argument("--max-dev", type=float, default=5.0, help="deg, GICP yaws further than this from the prior are skipped")
    p.add_argument("--demean", action="store_true")
    a = p.parse_args()
    prior = np.loadtxt(a.prior, delimiter=",", skiprows=1)
    gi = np.genfromtxt(a.gicp, delimiter=",", names=True)
    if len(gi) != len(prior):
        sys.exit(f"{len(prior)} prior rows, {len(gi)} GICP rows")
    t = gi["timestamp_ns"].astype(np.int64)
    g_ns, g_w = read_gyro(os.path.join(a.data, f"Track{a.track}"), a.gyro_axis)
    gt = (g_ns - t[0]) / 1e9
    tt = (t - t[0]) / 1e9
    G_imu = np.concatenate([[0.0], np.cumsum(0.5 * (g_w[1:] + g_w[:-1]) * np.diff(gt))])
    G = np.interp(tt, gt, G_imu)                       # raw gyro angle (bias included: absorbed by the smoothing)
    g = gi["ndt_yaw"]
    ok = (gi["accepted"] > 0) & (np.abs(np.degrees(wrap(g - prior[:, 3]))) < a.max_dev)
    d = np.unwrap(wrap(g - G))
    w = ok.astype(float)
    # gyro bias: the linear trend of the difference (weighted fit), removed before the smoothing (the Gaussian window is
    # truncated at the track ends, where a 0.26 deg/s drift would otherwise bend the result by degrees)
    A = np.stack([np.ones_like(tt), tt], axis=1)
    coef = np.linalg.lstsq(A * w[:, None], d * w, rcond=None)[0]
    trend = A @ coef
    o = trend + wsmooth(d - trend, w, tt, a.sigma_t)
    yaw = wrap(G + o)
    if a.demean:
        c = np.angle(np.mean(np.exp(1j * (yaw - prior[:, 3]))))
        yaw = wrap(yaw - c)
    out = prior.copy()
    out[:, 3] = yaw
    with open(a.out, "w") as f:
        f.write("idx,x,y,yaw\n")
        for r in out:
            f.write(f"{int(r[0])},{r[1]:.6f},{r[2]:.6f},{r[3]:.6f}\n")
    dy = np.degrees(wrap(yaw - prior[:, 3]))
    print(f"wrote {a.out}: {ok.mean():.0%} of the GICP yaws used, gyro bias {-np.degrees(coef[1]):+.3f} deg/s, "
          f"yaw change vs prior RMS {np.sqrt(np.mean(dy ** 2)):.3f} "
          f"deg (mean {dy.mean():+.3f}, max {np.abs(dy).max():.2f})")


if __name__ == "__main__":
    main()
