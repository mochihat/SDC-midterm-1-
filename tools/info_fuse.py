"""Fuse the GNSS/Kalman prior with scan-matching poses as one least-squares problem over the whole trajectory,
trusting each scan match only in the directions it actually constrains.

Unknown: the position correction c_i (2D) of every frame i, added to the prior p_i. Cost:

  sum_i  |c_i|^2 / sigma_prior^2                                    prior: GNSS error is bounded
+ sum_i  |c_{i+1} - c_i|^2 / (q * dt_i)                             GNSS error drifts slowly (random walk, q m^2/s)
+ sum_{i matched}  (c_i - d_i)^T W_i (c_i - d_i)                    scan match d_i = matched pose - prior

W_i comes from the GICP Hessian reduced to x, y (gicp_refine.py columns info_xx/xy/yy): its eigenvectors give the
well / badly constrained directions (on a straight road: lateral well, along-track badly). The absolute scale of
the Hessian is not trustworthy (image point clouds are distorted, so errors are correlated across points), so W_i
keeps the Hessian's shape and is normalised: eigenvalues l1 >= l2 become w * (1, (l2 / l1)^gamma) / sigma_match^2.
gamma = 0 is the isotropic case (every direction trusted alike, like the Gaussian smoothing in fuse_to_csv.py).

--demean removes the mean along / lateral scan-match offset (vehicle frame) first, as in fuse_to_csv.py.
Gating: |d_i| <= --max-xy and |dyaw| <= --max-yaw-deg, converged frames only, median filter over 5 matched frames.

Usage: python3 tools/info_fuse.py PRIOR_CSV DEBUG_CSV OUT_CSV [--sigma-prior 1.0] [--q 0.02] [--sigma-match 0.5]
                                  [--gamma 1.0] [--demean]
Output keeps the prior yaw.
"""
import argparse
import csv

import numpy as np
from scipy.ndimage import median_filter
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve


def wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


def load_debug(path):
    with open(path) as f:
        rows = list(csv.DictReader(f))
    return {k: np.array([float(r[k]) for r in rows]) for k in rows[0]}


def weights(dbg, good, gamma, sigma_match):
    W = np.zeros((len(good), 2, 2))
    has_info = "info_xx" in dbg
    ratios = np.ones(len(good))
    for k in np.flatnonzero(good):
        S = np.array([[dbg["info_xx"][k], dbg["info_xy"][k]], [dbg["info_xy"][k], dbg["info_yy"][k]]]) \
            if has_info else np.full((2, 2), np.nan)
        if gamma > 0 and np.isfinite(S).all() and S[0, 0] + S[1, 1] > 0:
            lam, U = np.linalg.eigh(S)  # ascending
            r = max(lam[0], 0) / max(lam[1], 1e-12)
            ratios[k] = r
            W[k] = U @ np.diag([r ** gamma, 1.0]) @ U.T / sigma_match ** 2
        else:
            W[k] = np.eye(2) / sigma_match ** 2
    return W, ratios


def solve(n, dt, idx, d, W, sigma_prior, q):
    """Sparse normal equations for c (2n unknowns, x and y interleaved)."""
    rows, cols, vals = [], [], []
    b = np.zeros(2 * n)

    def add(i, j, v):
        rows.append(i)
        cols.append(j)
        vals.append(v)

    for i in range(2 * n):
        add(i, i, 1.0 / sigma_prior ** 2)
    for i in range(n - 1):
        w = 1.0 / (q * max(dt[i], 1e-3))
        for a in range(2):
            u, v = 2 * i + a, 2 * (i + 1) + a
            add(u, u, w)
            add(v, v, w)
            add(u, v, -w)
            add(v, u, -w)
    for k, i in enumerate(idx):
        Wk = W[k]
        for a in range(2):
            for c in range(2):
                add(2 * i + a, 2 * i + c, Wk[a, c])
        b[2 * i:2 * i + 2] += Wk @ d[k]
    A = coo_matrix((vals, (rows, cols)), shape=(2 * n, 2 * n)).tocsc()
    return spsolve(A, b).reshape(n, 2)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("prior")
    p.add_argument("debug")
    p.add_argument("out")
    p.add_argument("--sigma-prior", type=float, default=1.0, help="m, size of the GNSS error")
    p.add_argument("--q", type=float, default=0.02, help="m^2/s, random-walk rate of the GNSS error")
    p.add_argument("--sigma-match", type=float, default=0.5, help="m, scan-match noise in its best direction")
    p.add_argument("--gamma", type=float, default=1.0, help="0 = isotropic, 1 = follow the Hessian shape")
    p.add_argument("--max-xy", type=float, default=2.0)
    p.add_argument("--max-yaw-deg", type=float, default=3.0)
    p.add_argument("--demean", action="store_true")
    a = p.parse_args()

    prior_rows = list(csv.reader(open(a.prior)))[1:]
    prior = np.array([[float(v) for v in r[1:4]] for r in prior_rows])
    n = len(prior)
    dbg = load_debug(a.debug)
    idx_all = dbg["idx"].astype(int)
    t_all = (dbg["timestamp_ns"] - dbg["timestamp_ns"][0]) / 1e9
    t = np.interp(np.arange(n), idx_all, t_all)
    dt = np.diff(t)

    # Scan-match correction against the prior positions (the debug run may have started from another prior).
    d = np.c_[dbg["ndt_x"], dbg["ndt_y"]] - prior[idx_all, :2]
    dyaw = wrap(dbg["ndt_yaw"] - dbg["guess_yaw"])
    good = (np.hypot(d[:, 0], d[:, 1]) <= a.max_xy) & (np.abs(np.degrees(dyaw)) <= a.max_yaw_deg) & \
           (dbg["converged"] > 0)
    yaw = prior[idx_all, 2]
    fwd, lat = np.c_[np.cos(yaw), np.sin(yaw)], np.c_[-np.sin(yaw), np.cos(yaw)]
    along_d, lat_d = (d * fwd).sum(1), (d * lat).sum(1)
    if a.demean:
        ma, ml = along_d[good].mean(), lat_d[good].mean()
        along_d, lat_d = along_d - ma, lat_d - ml
        print(f"removed mean scan-match offset: along {ma:+.3f} m, lateral {ml:+.3f} m")
    along_d[good] = median_filter(along_d[good], size=5, mode="nearest")
    lat_d[good] = median_filter(lat_d[good], size=5, mode="nearest")
    d = along_d[:, None] * fwd + lat_d[:, None] * lat

    W, ratios = weights(dbg, good, a.gamma, a.sigma_match)
    sel = np.flatnonzero(good)
    # Direction of the weak axis relative to the vehicle, for the log.
    print(f"using {len(sel)}/{len(good)} matched frames; information ratio weak/strong median "
          f"{np.median(ratios[sel]):.3f} (p10 {np.percentile(ratios[sel], 10):.3f})")
    c = solve(n, dt, idx_all[sel], d[sel], W[sel], a.sigma_prior, a.q)

    out = prior.copy()
    out[:, :2] += c
    with open(a.out, "w") as f:
        f.write("idx,x,y,yaw\n")
        for i, (x, y, yw) in enumerate(out):
            f.write(f"{i},{x:.6f},{y:.6f},{yw:.6f}\n")
    ca = (c * np.c_[np.cos(prior[:, 2]), np.sin(prior[:, 2])]).sum(1)
    cl = (c * np.c_[-np.sin(prior[:, 2]), np.cos(prior[:, 2])]).sum(1)
    print(f"wrote {a.out}: correction RMS {np.sqrt((c ** 2).sum(1).mean()):.3f} m "
          f"(along {np.sqrt((ca ** 2).mean()):.3f}, lateral {np.sqrt((cl ** 2).mean()):.3f})")


if __name__ == "__main__":
    main()
