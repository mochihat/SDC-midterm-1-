"""Where does GICP help, and does its Hessian predict its own noise? (no ground truth, no leaderboard)

1. Hessian check. The GICP Hessian H (reduced to x, y: info_xx/xy/yy) predicts a per-frame noise sigma in every
   direction (sigma^2 = u^T S^-1 u). The actual frame-to-frame noise of the scan-match correction is measurable
   without ground truth: correction minus its own 2 s Gaussian smooth (the GNSS error is slow, so what is left is
   matcher noise). If the Hessian is informative, (a) the along / lateral noise ratio follows the predicted ratio and
   (b) frames with a larger predicted sigma show a larger residual (rank correlation, per direction).
2. Per-segment table (10 % of the drive each): speed, curvature, road height and scale stability, points, information
   ratio along/lateral, correction size, measured along / lateral noise.

Usage: python3 tools/segment_analysis.py PRIOR_CSV GICP_DEBUG_CSV [--segments 10]
"""
import argparse
import csv

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.stats import spearmanr


def main():
    p = argparse.ArgumentParser()
    p.add_argument("prior")
    p.add_argument("debug")
    p.add_argument("--segments", type=int, default=10)
    p.add_argument("--max-xy", type=float, default=2.0)
    a = p.parse_args()

    prior = np.loadtxt(a.prior, delimiter=",", skiprows=1)[:, 1:4]  # x, y, yaw
    with open(a.debug) as f:
        rows = list(csv.DictReader(f))
    D = {k: np.array([float(r[k]) for r in rows]) for k in rows[0]}
    idx = D["idx"].astype(int)
    n = len(prior)
    t = (D["timestamp_ns"] - D["timestamp_ns"][0]) / 1e9
    step = np.median(np.diff(t))
    yaw = prior[idx, 2]
    fwd, lat = np.c_[np.cos(yaw), np.sin(yaw)], np.c_[-np.sin(yaw), np.cos(yaw)]
    d = np.c_[D["ndt_x"], D["ndt_y"]] - prior[idx, :2]
    ok = (D["converged"] > 0) & (np.linalg.norm(d, axis=1) <= a.max_xy) & np.isfinite(D["info_xx"]) & (D["info_xx"] > 0)
    ca, cl = (d * fwd).sum(1), (d * lat).sum(1)

    # measured matcher noise = correction - its own slow part (normalised Gaussian over valid frames)
    def hp(v):
        w = ok.astype(float)
        lo = gaussian_filter1d(np.where(ok, v, 0), 2 / step, mode="nearest") / \
            np.maximum(gaussian_filter1d(w, 2 / step, mode="nearest"), 1e-9)
        return v - lo
    ra, rl = hp(ca), hp(cl)

    # Hessian-predicted sigma along / lateral
    sa, sl = np.full(len(idx), np.nan), np.full(len(idx), np.nan)
    for k in np.flatnonzero(ok):
        S = np.array([[D["info_xx"][k], D["info_xy"][k]], [D["info_xy"][k], D["info_yy"][k]]])
        C = np.linalg.pinv(S)
        sa[k], sl[k] = np.sqrt(fwd[k] @ C @ fwd[k]), np.sqrt(lat[k] @ C @ lat[k])

    m = ok
    print(f"frames used {m.sum()}/{len(idx)}")
    print("== 1. Does the Hessian predict the matcher noise?")
    print(f"  measured noise RMS: along {np.sqrt((ra[m]**2).mean()):.3f} m, lateral {np.sqrt((rl[m]**2).mean()):.3f} m"
          f"  -> ratio along/lateral {np.sqrt((ra[m]**2).mean() / (rl[m]**2).mean()):.2f}")
    print(f"  Hessian-predicted sigma (median): along {np.median(sa[m]):.4f}, lateral {np.median(sl[m]):.4f}"
          f"  -> ratio {np.median(sa[m] / sl[m]):.2f}   (absolute scale is meaningless, only ratios)")
    for name, s, r in (("along", sa, ra), ("lateral", sl, rl)):
        rho = spearmanr(s[m], np.abs(r[m])).correlation
        q = np.quantile(s[m], [0, 0.25, 0.5, 0.75, 1])
        bins = [np.sqrt((r[m][(s[m] >= q[i]) & (s[m] <= q[i + 1])] ** 2).mean()) for i in range(4)]
        print(f"  {name:8s} Spearman(predicted sigma, |noise|) {rho:+.3f}; noise RMS by predicted-sigma quartile "
              + " ".join(f"{b:.3f}" for b in bins))
    rho = spearmanr((sa / sl)[m], (np.abs(ra) / np.maximum(np.abs(rl), 1e-6))[m]).correlation
    print(f"  per-frame anisotropy: Spearman(predicted along/lat, measured |along|/|lat|) {rho:+.3f}")

    print(f"== 2. Per segment ({a.segments} x {100 // a.segments} %)")
    xy = prior[:, :2]
    v = np.linalg.norm(np.gradient(xy, axis=0), axis=1) / step
    w = np.abs(np.gradient(np.unwrap(prior[:, 2]))) / step
    head = ("seg", "speed", "turn", "scale", "scale_sd", "pts", "ok%", "info_al/lat", "|corr|", "corr_al", "corr_lat",
            "noise_al", "noise_lat")
    print("  " + " ".join(f"{h:>10s}" for h in head))
    for s in range(a.segments):
        fr = (idx >= s * n // a.segments) & (idx < (s + 1) * n // a.segments)
        g = fr & m
        Ia = np.array([fwd[k] @ np.array([[D["info_xx"][k], D["info_xy"][k]], [D["info_xy"][k], D["info_yy"][k]]]) @ fwd[k]
                       for k in np.flatnonzero(g)])
        Il = np.array([lat[k] @ np.array([[D["info_xx"][k], D["info_xy"][k]], [D["info_xy"][k], D["info_yy"][k]]]) @ lat[k]
                       for k in np.flatnonzero(g)])
        pf = idx[fr]
        vals = (s + 1, v[pf].mean(), np.degrees(w[pf]).mean(), D["scale"][fr].mean(), D["scale"][fr].std(),
                D["input_points"][fr].mean(), 100 * g.sum() / max(fr.sum(), 1), np.median(Ia / Il),
                np.sqrt((d[g] ** 2).sum(1).mean()), np.sqrt((ca[g] ** 2).mean()), np.sqrt((cl[g] ** 2).mean()),
                np.sqrt((ra[g] ** 2).mean()), np.sqrt((rl[g] ** 2).mean()))
        print("  " + " ".join(f"{x:10.0f}" if i in (0, 5, 6) else f"{x:10.3f}" for i, x in enumerate(vals)))
    print("  speed m/s, turn deg/s, scale = 1.646 / road height, pts = points per frame before downsampling,")
    print("  ok% = converged and within 2 m, corr = GICP correction (m), noise = correction minus its 2 s smooth (m)")


if __name__ == "__main__":
    main()
