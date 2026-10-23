"""Clean Track01/02: correct a GNSS-based trajectory with correlative scan matching on the LiDAR map (23/10).

Per frame: the above-road points of the LoGeR cloud (raw_ply cache, road-height scale x --scale; Track01/02 clouds are
~10 % too large: best map fit x0.90 at the true poses) are scored on an along / lateral grid around the prior pose in
the 2D likelihood field of the map's structure (mcl_localize.build_field, the field of track_localize.py --csm); with
a Gaussian prior (--sigma-prior) the grid posterior gives the map's opinion d_k of the position, and its contrast
(peak - median score) a confidence w_k. The correction is the weighted Gaussian smoothing (--sigma-t seconds, both
directions - Track01/02 need not be causal) of d_k; --demean removes its weighted mean (the GNSS mean is trusted, the
map only corrects how the GNSS error changes along the track). Yaw is kept from the prior.
Uses no leaderboard information: inputs are the prior CSV, the raw_ply cache and the map.

Usage: python3 tools/csm_fuse.py TRACK PRIOR.csv OUT.csv [--scale 0.9] [--sigma-t 3] [--demean] [--debug D.csv]
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gicp_refine import read_pcd_binary  # noqa: E402
from mcl_localize import above_road, build_field, field_score  # noqa: E402


def wsmooth(x, w, t, sigma):
    """Weighted Gaussian smoothing in time (x: n x d)."""
    out = np.empty_like(x)
    for i in range(len(t)):
        g = w * np.exp(-0.5 * ((t - t[i]) / sigma) ** 2)
        sel = g > 1e-6 * g.max() if g.max() > 0 else slice(None)
        out[i] = np.sum(g[sel, None] * x[sel], axis=0) / max(g[sel].sum(), 1e-12)
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("track", type=int)
    p.add_argument("prior")
    p.add_argument("out")
    p.add_argument("--data", default="/w/data")
    p.add_argument("--cache", default="/w/cache")
    p.add_argument("--scale", type=float, default=0.9)
    p.add_argument("--lever-along", type=float, default=-0.12, help="m, camera behind the reference (at --scale)")
    p.add_argument("--lever-lat", type=float, default=0.12)
    p.add_argument("--yaw-offset", type=float, default=0.66)
    p.add_argument("--sigma-prior", type=float, default=0.5)
    p.add_argument("--kappa", type=float, default=15.0)
    p.add_argument("--span", type=float, default=2.0)
    p.add_argument("--lat-span", type=float, default=1.5)
    p.add_argument("--step", type=float, default=0.25)
    p.add_argument("--points", type=int, default=800)
    p.add_argument("--sigma-t", type=float, default=3.0)
    p.add_argument("--min-contrast", type=float, default=0.15)
    p.add_argument("--demean", action="store_true")
    p.add_argument("--debug")
    a = p.parse_args()
    prior = np.loadtxt(a.prior, delimiter=",", skiprows=1)
    cdir = os.path.join(a.cache, f"Track{a.track}", "raw_ply")
    cxyz = np.load(os.path.join(cdir, "xyz.npy"), mmap_mode="r")
    cidx = np.load(os.path.join(cdir, "index.npy"))
    t = np.load(os.path.join(cdir, "ts.npy")) / 1e9
    if len(cidx) != len(prior):
        sys.exit(f"{len(prior)} prior rows, {len(cidx)} raw_ply frames")
    field = build_field(read_pcd_binary(os.path.join(a.data, f"Track{a.track}", "map_voxel_0.3m.pcd")),
                        0.4, 3.0, 0.2, 0.4, 0.1)
    da = np.arange(-a.span, a.span + 1e-9, a.step)
    dl = np.arange(-a.lat_span, a.lat_span + 1e-9, a.step)
    ga, gl = [g.ravel() for g in np.meshgrid(da, dl, indexing="ij")]
    lp_prior = -0.5 * (ga ** 2 + gl ** 2) / a.sigma_prior ** 2
    rng = np.random.default_rng(0)
    d = np.zeros((len(prior), 2))
    w = np.zeros(len(prior))
    rows = []
    for k in range(len(prior)):
        s = 1.646 / np.median(cidx[max(0, k - 56):k + 1, 3]) * a.scale
        i0, n = int(cidx[k, 0]), int(cidx[k, 1])
        sx, sy = above_road(np.asarray(cxyz[i0:i0 + n], dtype=np.float64) * s, 2.4, 1.646 * a.scale, 0.4, 3.0, 1.0,
                            20.0)
        if len(sx) < 30:
            rows.append((k, 0.0, 0.0, 0.0))
            continue
        if len(sx) > a.points:
            pick = rng.choice(len(sx), a.points, replace=False)
            sx, sy = sx[pick], sy[pick]
        yaw = prior[k, 3]
        c, sn = np.cos(yaw), np.sin(yaw)
        cy, sy_ = np.cos(yaw + np.radians(a.yaw_offset)), np.sin(yaw + np.radians(a.yaw_offset))
        ox = prior[k, 1] + (a.lever_along + ga) * c - (a.lever_lat + gl) * sn
        oy = prior[k, 2] + (a.lever_along + ga) * sn + (a.lever_lat + gl) * c
        sc = field_score(field, ox[:, None] + (cy * sx - sy_ * sy)[None, :], oy[:, None] + (sy_ * sx + cy * sy)[None, :])
        lp = a.kappa * sc + lp_prior
        wg = np.exp(lp - lp.max())
        wg /= wg.sum()
        ma, ml = float(np.sum(wg * ga)), float(np.sum(wg * gl))
        contrast = float(sc.max() - np.median(sc))
        d[k] = (ma * c - ml * sn, ma * sn + ml * c)
        w[k] = contrast if contrast >= a.min_contrast else 0.0
        rows.append((k, ma, ml, contrast))
    corr = wsmooth(d, w, t - t[0], a.sigma_t)
    if a.demean:
        corr = corr - np.sum(w[:, None] * d, axis=0) / max(w.sum(), 1e-12)
    out = prior.copy()
    out[:, 1:3] += corr
    with open(a.out, "w") as f:
        f.write("idx,x,y,yaw\n")
        for r in out:
            f.write(f"{int(r[0])},{r[1]:.6f},{r[2]:.6f},{r[3]:.6f}\n")
    used = w > 0
    print(f"wrote {a.out}: {used.mean():.0%} of frames informative (contrast >= {a.min_contrast}); raw map offset "
          f"along {np.median(np.array(rows)[used, 1]):+.2f} m, lateral {np.median(np.array(rows)[used, 2]):+.2f} m "
          f"(median); correction RMS {np.sqrt(np.mean(np.sum(corr ** 2, axis=1))):.3f} m")
    if a.debug:
        np.savetxt(a.debug, np.array(rows), delimiter=",", header="idx,along,lateral,contrast", comments="", fmt="%.4f")


if __name__ == "__main__":
    main()
