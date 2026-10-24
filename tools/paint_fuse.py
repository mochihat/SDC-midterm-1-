"""Causal fusion of the road-paint measurements with a prior trajectory (24/10, Track03 rules).

The prior (tools/track_localize.py, causal) is good to ~0.5-1 m with slowly changing errors; the road-paint match of
frame k (tools/paint_measure.py) gives an NCC volume over yaw x along x lateral offsets around the prior's pose at k.
State: the prior's error e = (dx, dy, dyaw) in the world frame, with covariance P. Per frame, in time order:
  predict   P += Q (body frame: --q-along / --q-lat m and --q-yaw deg per frame, plus --q-dist x the prior's step)
  update    grid posterior (as the correlative scan matching of the tracker): log p(g) = kappa * NCC(g)
            - 0.5 (g - e)' P^-1 (g - e) on the volume's grid g; e, P = posterior mean / covariance
            (--yaw-mode fixed: yaw stays the prior's, the 2-D slice of the volume at the prior yaw is used)
  output    prior + e, minus the camera lever (--lever-along / --lever-lat: the paint pose - reference pose measured
            at the Track01 / Track02 reference poses)
Every output row uses frames <= k only.

Usage: python3 tools/paint_fuse.py PRIOR.csv MEAS.npz OUT.csv [--kappa 40] [--ref REF.csv (validation only)]
"""
import argparse

import numpy as np


def wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("prior")
    p.add_argument("meas")
    p.add_argument("out")
    p.add_argument("--kappa", type=float, default=40.0)
    p.add_argument("--q-along", type=float, default=0.03, help="m per frame")
    p.add_argument("--q-lat", type=float, default=0.02, help="m per frame")
    p.add_argument("--q-yaw", type=float, default=0.02, help="deg per frame")
    p.add_argument("--q-dist", type=float, default=0.02, help="m per m of prior motion (along and lateral)")
    p.add_argument("--p0", default="1.0,1.0,1.0", help="start sd: along m, lateral m, yaw deg")
    p.add_argument("--lever-along", type=float, default=0.0)
    p.add_argument("--lever-lat", type=float, default=0.0)
    p.add_argument("--yaw-mode", default="fixed", choices=["fixed", "paint"])
    p.add_argument("--min-contrast", type=float, default=0.05, help="best NCC - median NCC below this: no update")
    p.add_argument("--kappa-motion", type=float, default=0.0,
                   help="m: kappa x min(1, prior step / this) - frames of one view (standing) are one measurement, "
                        "not hundreds (0 = off)")
    p.add_argument("--sd-floor", default="0,0", help="m: along, lateral sd floor of the posterior")
    p.add_argument("--ref", help="VALIDATION ONLY (Track01/02): reference CSV, prints errors")
    p.add_argument("--diag")
    a = p.parse_args()
    prior = np.loadtxt(a.prior, delimiter=",", skiprows=1)
    z = np.load(a.meas)
    vol, yaws, res, na, nl = z["vol"], np.radians(z["yaws"]), float(z["res"]), int(z["na"]), int(z["nl"])
    if len(vol) != len(prior):
        raise SystemExit(f"{len(prior)} prior rows, {len(vol)} measurement frames")
    da = (np.arange(2 * na + 1) - na) * res
    dl = (np.arange(2 * nl + 1) - nl) * res
    DA, DL = np.meshgrid(da, dl, indexing="ij")
    iy0 = int(np.argmin(np.abs(yaws)))
    sd0 = [float(v) for v in a.p0.split(",")]
    e = np.zeros(3)
    P = None
    out = np.empty_like(prior)
    diag = []
    for k in range(len(prior)):
        x, y, yaw = prior[k, 1:4]
        c, s = np.cos(yaw), np.sin(yaw)
        R = np.array([[c, -s], [s, c]])
        if P is None:
            P = np.zeros((3, 3))
            P[:2, :2] = R @ np.diag([sd0[0] ** 2, sd0[1] ** 2]) @ R.T
            P[2, 2] = np.radians(sd0[2]) ** 2
        else:
            step = np.hypot(*(prior[k, 1:3] - prior[k - 1, 1:3]))
            qa = a.q_along + a.q_dist * step
            ql = a.q_lat + a.q_dist * step
            P[:2, :2] += R @ np.diag([qa ** 2, ql ** 2]) @ R.T
            P[2, 2] += np.radians(a.q_yaw) ** 2
        used, contrast = 0, 0.0
        kap = a.kappa
        if a.kappa_motion > 0:
            st = np.hypot(*(prior[k, 1:3] - prior[k - 1, 1:3])) if k else 0.0
            kap = a.kappa * min(1.0, st / a.kappa_motion)
        v = vol[k].astype(np.float64)
        if v.max() > -0.5:
            contrast = float(v.max() - np.median(v))
        if contrast >= a.min_contrast and kap > 0:
            if a.yaw_mode == "fixed":
                # 2-D posterior on the along / lateral grid at the prior yaw (+ the current yaw error estimate = 0)
                g = np.stack([DA.ravel() * c - DL.ravel() * s, DA.ravel() * s + DL.ravel() * c], axis=1)
                Pi = np.linalg.inv(P[:2, :2])
                d = g - e[:2]
                lp = kap * v[iy0].ravel() - 0.5 * np.einsum("ni,ij,nj->n", d, Pi, d)
                w = np.exp(lp - lp.max())
                w /= w.sum()
                m = w @ g
                dm = g - m
                e[:2] = m
                P[:2, :2] = (dm * w[:, None]).T @ dm + np.eye(2) * (res ** 2 / 12)
            else:
                gs, ls = [], []
                Pi = np.linalg.inv(P)
                for iy_, dyw in enumerate(yaws):
                    cy, sy = np.cos(yaw + dyw), np.sin(yaw + dyw)
                    g = np.stack([DA.ravel() * cy - DL.ravel() * sy, DA.ravel() * sy + DL.ravel() * cy,
                                  np.full(DA.size, dyw)], axis=1)
                    gs.append(g)
                    ls.append(kap * v[iy_].ravel())
                g = np.concatenate(gs)
                d = g - e
                lp = np.concatenate(ls) - 0.5 * np.einsum("ni,ij,nj->n", d, Pi, d)
                w = np.exp(lp - lp.max())
                w /= w.sum()
                m = w @ g
                dm = g - m
                e = m
                P = (dm * w[:, None]).T @ dm + np.diag([res ** 2 / 12, res ** 2 / 12,
                                                         (yaws[1] - yaws[0]) ** 2 / 12])
            used = 1
            fa, fl = (float(v_) for v_ in a.sd_floor.split(","))
            if fa > 0 or fl > 0:
                # sd floor in the body frame: consecutive frames share their errors (scene, calibration)
                Pb = R.T @ P[:2, :2] @ R
                Pb[0, 0] = max(Pb[0, 0], fa ** 2)
                Pb[1, 1] = max(Pb[1, 1], fl ** 2)
                P[:2, :2] = R @ Pb @ R.T
        yo = wrap(yaw + (e[2] if a.yaw_mode == "paint" else 0.0))
        co, so = np.cos(yo), np.sin(yo)
        lev = np.array([a.lever_along * co - a.lever_lat * so, a.lever_along * so + a.lever_lat * co])
        out[k] = (prior[k, 0], x + e[0] - lev[0], y + e[1] - lev[1], yo)
        diag.append((k, used, contrast, e[0] * c + e[1] * s, -e[0] * s + e[1] * c, np.degrees(e[2]),
                     np.sqrt(P[0, 0] + P[1, 1])))
    with open(a.out, "w") as f:
        f.write("idx,x,y,yaw\n")
        for r in out:
            f.write(f"{int(r[0])},{r[1]:.6f},{r[2]:.6f},{r[3]:.6f}\n")
    if a.diag:
        np.savetxt(a.diag, np.array(diag), delimiter=",", fmt="%.4f",
                   header="k,used,contrast,e_along,e_lat,e_yaw_deg,sd_pos", comments="")
    dg = np.array(diag)
    print(f"wrote {a.out}: {dg[:, 1].mean():.0%} of the frames updated, mean |e| {np.hypot(dg[:, 3], dg[:, 4]).mean():.2f} m")
    if a.ref:
        ref = np.loadtxt(a.ref, delimiter=",", skiprows=1)
        for nm, tr in (("prior", prior), ("fused", out)):
            dx, dy = tr[:, 1] - ref[:, 1], tr[:, 2] - ref[:, 2]
            cr, sr = np.cos(ref[:, 3]), np.sin(ref[:, 3])
            al, la = dx * cr + dy * sr, -dx * sr + dy * cr
            ey = np.degrees(wrap(tr[:, 3] - ref[:, 3]))
            P_ = np.sqrt(np.mean(dx ** 2 + dy ** 2))
            Y_ = np.sqrt(np.mean(ey ** 2))
            print(f"  {nm}: pos RMSE {P_:.3f} m (along {np.sqrt(np.mean(al ** 2)):.3f}, lat {np.sqrt(np.mean(la ** 2)):.3f}; "
                  f"mean {al.mean():+.3f} / {la.mean():+.3f}), yaw RMSE {Y_:.3f} deg -> score {P_ + 0.2 * Y_:.3f}")


if __name__ == "__main__":
    main()
