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
--motion imu (25/10): the prior's frame-to-frame steps jitter (Track03: its speed swings +-3 m/s between frames, the
car's does not), and with e a random walk the output inherits that jitter (0.3-0.5 m along). Instead the pose moves
with the IMU speed of the prior's SpeedFilter (v_imu in PRIOR_diag.csv, causal; its LoGeR odometry scale is off by
-15..+30 %, slowly varying -> a scale state s): state (e, s), predict e += s v_imu dt u(yaw) - (prior step),
the prior itself as a weak measurement e = 0 (--z-sd per frame), the paint posterior as above (s follows through its
covariance with e, moment matching).
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
    p.add_argument("--kappa-side", type=float, default=0.0,
                   help="weight of the side-camera volume (vol_side of paint_measure.py --side --separate; 0 = unused)")
    p.add_argument("--meas-side", help="file with vol_side (default: MEAS); its search grid must be MEAS's")
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
    p.add_argument("--kappa-time", type=float, default=0.0,
                   help="s: with --kappa-motion, a frame weighs at least frame time / this (standing: a static view "
                        "still pulls the pose to it, slowly; 0 = off)")
    p.add_argument("--time-contrast", type=float, default=0.2,
                   help="--kappa-time applies only when the contrast is at least this")
    p.add_argument("--center", help="poses the volumes were computed around (default: the prior; a causal earlier pass "
                                    "re-centres the search windows on a better estimate of frame k)")
    p.add_argument("--online", type=int, default=0,
                   help="TRACK: compute each frame's volume here, around the filter's prediction prior + e (MEAS is "
                        "then ignored; matcher settings as tools/paint_measure.py defaults / --m-* options)")
    p.add_argument("--data", default="/w/data")
    p.add_argument("--cache", default="/w/cache")
    p.add_argument("--m-pitch", type=float, default=1.0)
    p.add_argument("--m-camyaw", type=float, default=-1.5)
    p.add_argument("--m-sa", type=float, default=2.0)
    p.add_argument("--m-sl", type=float, default=1.5)
    p.add_argument("--m-yaws", default="-1.5,1.5,0.25")
    p.add_argument("--m-pitches", default="-0.5,0.5,0.25")
    p.add_argument("--m-along", default="5,18")
    p.add_argument("--m-lat", default="-7,7")
    p.add_argument("--motion", default="prior", choices=["prior", "imu"],
                   help="prediction: the prior's steps (e a random walk) or the IMU speed x a scale state")
    p.add_argument("--speed", help="--motion imu: CSV with a v_imu column, one row per frame (default PRIOR_diag.csv)")
    p.add_argument("--times", help="--motion imu: camera .ts file (bag_h265.py; column 2 = capture time, ns); "
                                   "default 1/27.8 s per frame")
    p.add_argument("--s0", default="1.0,0.1", help="--motion imu: start scale, its sd")
    p.add_argument("--q-scale", type=float, default=0.005, help="--motion imu: scale random walk per frame")
    p.add_argument("--q-imu", default="0.01,0.01", help="--motion imu: process noise along, lateral m per frame on the "
                                                       "IMU-predicted frames (else --q-along / --q-lat)")
    p.add_argument("--kappa-imu", type=float, default=0.0, help="--motion imu: kappa on the IMU-predicted frames (0 = "
                                                                  "--kappa)")
    p.add_argument("--kappa-imu-vmin", type=float, default=0.0, help="--kappa-imu only at IMU speeds >= this (m/s)")
    p.add_argument("--imu-lat-full", action="store_true", help="--motion imu with --kappa-imu: the lateral of the "
                                                                    "IMU-predicted frames still with --kappa")
    p.add_argument("--imu-vmin", type=float, default=0.0, help="--motion imu: m/s, IMU speed below this -> prior step")
    p.add_argument("--imu-vstay", type=float, default=0.0, help="--motion imu: m/s, once moving with the IMU speed, "
                                                                 "keep it down to this speed (0 = --imu-vmin)")
    p.add_argument("--imu-stay-sd", type=float, default=1e9, help="--motion imu: --imu-vstay only if the scale sd was "
                                                                   "<= this on the last frame at >= --imu-vmin")
    p.add_argument("--imu-wmax", type=float, default=1e9, help="--motion imu: deg/s, prior yaw rate above -> prior step")
    p.add_argument("--q-turn", type=float, default=0.0, help="--motion imu: along / lateral m per rad of prior yaw change")
    p.add_argument("--z-sd", default="3,1.5", help="--motion imu: the prior as a measurement of the pose, sd per "
                                                   "frame along, lateral (m; 0 = unused)")
    p.add_argument("--ref", help="VALIDATION ONLY (Track01/02): reference CSV, prints errors")
    p.add_argument("--diag")
    a = p.parse_args()
    prior = np.loadtxt(a.prior, delimiter=",", skiprows=1)
    pm = fi = None
    vol_side = None
    if a.online:
        import os
        import sys
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from paint_bev import Camera, FrameImages, MapPaint, PaintMatcher, load_mask
        from paint_measure import rng
        mp = MapPaint.load(os.path.join(a.cache, f"Track{a.online}", "paint_map.npz"))
        paint = np.load(os.path.join(a.cache, f"Track{a.online}", "paint_th.npy"))
        fi = FrameImages(a.cache, a.online)
        cam = Camera(a.online, data=a.data, row0=fi.row0, rows=fi.rows, mask=load_mask(a.cache, a.online),
                     pitch=a.m_pitch, yaw=a.m_camyaw)
        pm = PaintMatcher(mp, paint, cam, along=tuple(float(v) for v in a.m_along.split(",")),
                          lat=tuple(float(v) for v in a.m_lat.split(",")), s_along=a.m_sa, s_lat=a.m_sl,
                          yaws=rng(a.m_yaws), pitches=rng(a.m_pitches))
        vol, yaws, res, na, nl = None, np.radians(pm.yaws), pm.res, pm.na, pm.nl
    else:
        z = np.load(a.meas)
        vol, yaws, res, na, nl = z["vol"], np.radians(z["yaws"]), float(z["res"]), int(z["na"]), int(z["nl"])
        zs = np.load(a.meas_side) if a.meas_side else z
        vol_side = zs["vol_side"] if ("vol_side" in zs.files and a.kappa_side > 0) else None
        if vol_side is not None and (vol_side.shape != vol.shape or not np.allclose(zs["prior"], z["prior"])):
            raise SystemExit("side volumes: other search grid or other window centres than MEAS")
        if len(vol) != len(prior):
            raise SystemExit(f"{len(prior)} prior rows, {len(vol)} measurement frames")
    da = (np.arange(2 * na + 1) - na) * res
    dl = (np.arange(2 * nl + 1) - nl) * res
    DA, DL = np.meshgrid(da, dl, indexing="ij")
    iy0 = int(np.argmin(np.abs(yaws)))
    center = np.loadtxt(a.center, delimiter=",", skiprows=1) if a.center else prior.copy()
    sd0 = [float(v) for v in a.p0.split(",")]
    e = np.zeros(3)
    P = None
    imu = a.motion == "imu"
    if imu:
        if a.yaw_mode != "fixed" or a.online:
            raise SystemExit("--motion imu: only with --yaw-mode fixed and precomputed volumes")
        sp = np.genfromtxt(a.speed or a.prior.replace(".csv", "_diag.csv"), delimiter=",", names=True)["v_imu"]
        th = (np.loadtxt(a.times, delimiter=",", dtype=np.int64)[:, 1] * 1e-9 if a.times
              else np.arange(len(prior)) / 27.8)
        if len(sp) != len(prior) or len(th) != len(prior):
            raise SystemExit("--motion imu: speed / times rows != prior rows")
        s_init, s_sd = (float(v) for v in a.s0.split(","))
        sc = s_init
        zsa, zsl = (float(v) for v in a.z_sd.split(","))
        qi_a, qi_l = (float(v) for v in a.q_imu.split(","))
        n_imu = 0
        moved_imu = stay_ok = False
        C3 = None                                        # covariance of (e_x, e_y, s)
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
            if imu:
                C3 = np.zeros((3, 3))
                C3[:2, :2] = P[:2, :2]
                C3[2, 2] = s_sd ** 2
        elif imu:
            # pose moves with s x the IMU speed along the prior's heading (e = pose - prior absorbs the prior's step)
            # where that speed is good: moving (>= --imu-vmin) and not turning (prior yaw rate over the last 10 frames
            # <= --imu-wmax); else with the prior's step as --motion prior
            dpsi = wrap(prior[k, 3] - prior[k - 1, 3])
            k0 = max(k - 10, 0)
            w_ = abs(np.degrees(wrap(prior[k, 3] - prior[k0, 3]))) / max(th[k] - th[k0], 1e-6)
            # hysteresis: enter at >= --imu-vmin (the scale is learnt there), stay down to --imu-vstay (slowing to a stop)
            # if the scale was known (sd <= --imu-stay-sd) on the last fast frame - not after a restart, say
            if w_ <= a.imu_wmax and sp[k] >= a.imu_vmin:
                moved_imu = True
                stay_ok = np.sqrt(C3[2, 2]) <= a.imu_stay_sd
            else:
                moved_imu = moved_imu and stay_ok and a.imu_vstay > 0 and w_ <= a.imu_wmax and sp[k] >= a.imu_vstay
            if moved_imu:
                psi = prior[k - 1, 3] + 0.5 * dpsi
                m = 0.5 * (sp[k] + sp[k - 1]) * (th[k] - th[k - 1]) * np.array([np.cos(psi), np.sin(psi)])
                e[:2] += sc * m - (prior[k, 1:3] - prior[k - 1, 1:3])
                F = np.eye(3)
                F[:2, 2] = m
                C3 = F @ C3 @ F.T
                st = np.hypot(*m)
                qa = qi_a + a.q_dist * st + a.q_turn * abs(dpsi)
                ql = qi_l + a.q_dist * st + a.q_turn * abs(dpsi)
                C3[:2, :2] += R @ np.diag([qa ** 2, ql ** 2]) @ R.T
                C3[2, 2] += a.q_scale ** 2
                wz = min(1.0, st / a.kappa_motion) if a.kappa_motion > 0 else 1.0
                if zsa > 0 and zsl > 0 and wz > 0:
                    # the prior as a weak measurement of the pose: e = 0 (weighted by motion as kappa: standing, the
                    # prior repeats one error)
                    Rz = R @ np.diag([zsa ** 2, zsl ** 2]) @ R.T / wz
                    K = C3[:, :2] @ np.linalg.inv(C3[:2, :2] + Rz)
                    ez = np.r_[e[:2], sc] - K @ e[:2]
                    e[:2], sc = ez[:2], ez[2]
                    C3 = C3 - K @ C3[:2, :]
                n_imu += 1
            else:
                step = np.hypot(*(prior[k, 1:3] - prior[k - 1, 1:3]))
                qa = a.q_along + a.q_dist * step
                ql = a.q_lat + a.q_dist * step
                C3[:2, :2] += R @ np.diag([qa ** 2, ql ** 2]) @ R.T
                C3[2, 2] += a.q_scale ** 2
            P[:2, :2] = C3[:2, :2]
        else:
            step = np.hypot(*(prior[k, 1:3] - prior[k - 1, 1:3]))
            qa = a.q_along + a.q_dist * step
            ql = a.q_lat + a.q_dist * step
            P[:2, :2] += R @ np.diag([qa ** 2, ql ** 2]) @ R.T
            P[2, 2] += np.radians(a.q_yaw) ** 2
        used, contrast = 0, 0.0
        low_k = imu and k and moved_imu and a.kappa_imu > 0 and sp[k] >= a.kappa_imu_vmin
        kap = a.kappa_imu if low_k else a.kappa
        kap_lat = a.kappa if (low_k and a.imu_lat_full) else 0.0
        if a.kappa_motion > 0:
            st = np.hypot(*(prior[k, 1:3] - prior[k - 1, 1:3])) if k else 0.0
            kap = kap * min(1.0, st / a.kappa_motion)
            kap_lat = kap_lat * min(1.0, st / a.kappa_motion)
            kap_t = a.kappa * (1 / 27.8) / a.kappa_time if a.kappa_time > 0 else 0.0
        if pm is not None:
            # online: the search window around the filter's prediction (causal: e holds frames < k)
            center[k, 1:4] = (x + e[0], y + e[1], wrap(yaw + (e[2] if a.yaw_mode == "paint" else 0.0)))
            img = fi.get(k)
            v = (pm.ncc_volume(img, *center[k, 1:4]).max(axis=0) if img is not None
                 else np.full((len(yaws), 2 * na + 1, 2 * nl + 1), -1.0))
        else:
            v = vol[k].astype(np.float64)
        vs = vol_side[k].astype(np.float64) if vol_side is not None else None
        ws = 0.0
        if vs is not None and vs.max() > -0.5 and float(vs.max() - np.median(vs)) >= a.min_contrast:
            ws = a.kappa_side / max(a.kappa, 1e-9)       # side-camera evidence, in units of the front kappa
        if v.max() > -0.5:
            contrast = float(v.max() - np.median(v))
        if vs is not None and ws > 0:
            # front + side evidence as one log-likelihood in units of kappa: v <- v_front + ws * v_side
            if v.max() > -0.5 and contrast >= a.min_contrast:
                v = v + ws * vs
            else:
                v = ws * vs
            contrast = max(contrast, float(v.max() - np.median(v)))
        if a.kappa_motion > 0 and a.kappa_time > 0 and contrast >= a.time_contrast:
            kap = max(kap, kap_t)
        if contrast >= a.min_contrast and kap > 0:
            if a.yaw_mode == "fixed":
                # 2-D posterior on the along / lateral grid at the prior yaw (+ the current yaw error estimate = 0)
                xc, yc, ywc = center[k, 1:4]
                cc_, sc_ = np.cos(ywc), np.sin(ywc)
                g = np.stack([xc - x + DA.ravel() * cc_ - DL.ravel() * sc_, yc - y + DA.ravel() * sc_ + DL.ravel() * cc_],
                             axis=1)
                Pi = np.linalg.inv(P[:2, :2])
                d = g - e[:2]
                lp = kap * v[iy0].ravel() - 0.5 * np.einsum("ni,ij,nj->n", d, Pi, d)
                w = np.exp(lp - lp.max())
                w /= w.sum()
                m = w @ g
                dm = g - m
                e_pr = e[:2].copy()
                e[:2] = m
                P[:2, :2] = (dm * w[:, None]).T @ dm + np.eye(2) * (res ** 2 / 12)
                if kap_lat > 0:
                    # lateral (body frame) from the posterior with kappa_lat, along from the one above: lane lines fix
                    # the lateral every frame, the along evidence (dashes, stop lines) is sparse and ambiguous
                    lp2 = kap_lat * v[iy0].ravel() - 0.5 * np.einsum("ni,ij,nj->n", d, Pi, d)
                    w2 = np.exp(lp2 - lp2.max())
                    w2 /= w2.sum()
                    m2 = w2 @ g
                    dm2 = g - m2
                    C1b = R.T @ P[:2, :2] @ R
                    C2b = R.T @ ((dm2 * w2[:, None]).T @ dm2 + np.eye(2) * (res ** 2 / 12)) @ R
                    mb = np.array([(R.T @ m)[0], (R.T @ m2)[1]])
                    m = R @ mb
                    e[:2] = m
                    P[:2, :2] = R @ np.diag([C1b[0, 0], C2b[1, 1]]) @ R.T
                if imu:
                    # s | e is Gaussian (linear regression on e): moment matching of the grid posterior
                    Ks = C3[2, :2] @ np.linalg.inv(C3[:2, :2])
                    sc += Ks @ (m - e_pr)
                    vs_ = C3[2, 2] - Ks @ C3[:2, 2]
                    C3[:2, :2] = P[:2, :2]
                    C3[2, :2] = C3[:2, 2] = Ks @ P[:2, :2]
                    C3[2, 2] = vs_ + Ks @ P[:2, :2] @ Ks
            else:
                gs, ls = [], []
                Pi = np.linalg.inv(P)
                xc, yc, ywc = center[k, 1:4]
                for iy_, dyw in enumerate(yaws):
                    cy, sy = np.cos(ywc + dyw), np.sin(ywc + dyw)
                    g = np.stack([xc - x + DA.ravel() * cy - DL.ravel() * sy, yc - y + DA.ravel() * sy + DL.ravel() * cy,
                                  np.full(DA.size, wrap(ywc - yaw) + dyw)], axis=1)
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
                if imu:
                    C3[:2, :2] = P[:2, :2]
        yo = wrap(yaw + (e[2] if a.yaw_mode == "paint" else 0.0))
        co, so = np.cos(yo), np.sin(yo)
        lev = np.array([a.lever_along * co - a.lever_lat * so, a.lever_along * so + a.lever_lat * co])
        out[k] = (prior[k, 0], x + e[0] - lev[0], y + e[1] - lev[1], yo)
        diag.append((k, used, contrast, e[0] * c + e[1] * s, -e[0] * s + e[1] * c, np.degrees(e[2]),
                     np.sqrt(P[0, 0] + P[1, 1])) + ((sc, np.sqrt(C3[2, 2]), float(moved_imu)) if imu else ()))
    with open(a.out, "w") as f:
        f.write("idx,x,y,yaw\n")
        for r in out:
            f.write(f"{int(r[0])},{r[1]:.6f},{r[2]:.6f},{r[3]:.6f}\n")
    if a.diag:
        np.savetxt(a.diag, np.array(diag), delimiter=",", fmt="%.4f",
                   header="k,used,contrast,e_along,e_lat,e_yaw_deg,sd_pos" + (",scale,scale_sd,imu" if imu else ""), comments="")
    dg = np.array(diag)
    print(f"wrote {a.out}: {dg[:, 1].mean():.0%} of the frames updated, mean |e| {np.hypot(dg[:, 3], dg[:, 4]).mean():.2f} m"
          + (f", {n_imu} frames moved with the IMU speed" if imu else ""))
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
