"""Causal Monte Carlo localization (particle filter, Thrun et al. "Probabilistic Robotics" ch. 8) without GNSS.

Why (23/10): the Kalman tracker (track_localize.py) drifts along the road: scan-to-scan odometry of the LoGeR clouds is
off by 10-60 % in places, and GICP started from a drifted prediction stays in the wrong basin. On Track03 the
along-road fit profile of the cloud against the map (fraction of points near map structure, attitude fixed) has a sharp
peak that moved 1 m (frame 300) -> 13.5 m (600) -> 29 m (900) behind the tracker. A particle filter weighs many
along-road positions at once, so this information is used instead of one local minimum.

Per frame k (only frames <= k are used; the output row of frame k is written when frame k is processed):
  state of each particle: x, y (camera position on the map), yaw (camera yaw), v (speed along the heading)
  predict: yaw += gyro z increment (bias: --gyro-bias, re-estimated while standing) + noise; v += N(0, --acc-noise dt);
           x, y += v dt (heading); standing (IMU accelerometer std over --zupt-window < --zupt-acc): v = 0, no motion
  weight:  above-road points of the cloud (height --h-lo .. --h-hi above the road, range <= --max-range, scale =
           --ground-height / road height in the cloud, trailing median), projected on the ground plane, scored in a 2D
           likelihood field of the map's structure points (same height band above the map's ground): log(p_hit N(d; 0,
           --sigma) + p_rand) averaged over the points, times --kappa (effective number of independent points)
  resample: systematic, when the effective sample size < N / 2, with a small jitter
  output:  weighted mean of the particles; position of the vehicle reference = camera position - lever (--bias-along /
           --bias-lat, vehicle frame, the GICP calibration of Track01/02), yaw = camera yaw - --yaw-offset

Usage: python3 tools/mcl_localize.py TRACK --init INIT.txt --out OUT.csv [--cache /w/cache] [--pose-check REF.csv]
"""
import argparse
import os
import sys
import time

import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gicp_refine import frame_list, read_pcd_binary, yaw_of  # noqa: E402
from track_localize import read_imu_acc, wrap  # noqa: E402
from yaw_fusion import read_gyro  # noqa: E402


def ground_grid(m, cell):
    """Road height per cell: 10th percentile of the z of the map points in the cell (NaN-free, nearest fill)."""
    x0, y0 = m[:, 0].min(), m[:, 1].min()
    ix = ((m[:, 0] - x0) / cell).astype(np.int64)
    iy = ((m[:, 1] - y0) / cell).astype(np.int64)
    W, H = ix.max() + 1, iy.max() + 1
    lin = iy * W + ix
    order = np.lexsort((m[:, 2], lin))
    lin_s, z_s = lin[order], m[order, 2]
    starts = np.flatnonzero(np.r_[True, lin_s[1:] != lin_s[:-1]])
    counts = np.diff(np.r_[starts, len(lin_s)])
    g = np.full(W * H, np.nan)
    ok = counts >= 3
    g[lin_s[starts[ok]]] = z_s[starts[ok] + (counts[ok] * 0.1).astype(np.int64)]
    g = g.reshape(H, W)
    nan = np.isnan(g)
    if nan.any():
        _, (iy_n, ix_n) = ndimage.distance_transform_edt(nan, return_indices=True)
        g = g[iy_n, ix_n]
    return x0, y0, g


def build_field(m, h_lo, h_hi, res, sigma, p_rand):
    """2D likelihood field of the map points h_lo..h_hi m above the local ground (Thrun's likelihood field model)."""
    gx0, gy0, gz = ground_grid(m, 1.0)
    cx = np.clip(((m[:, 0] - gx0) / 1.0).astype(np.int64), 0, gz.shape[1] - 1)
    cy = np.clip(((m[:, 1] - gy0) / 1.0).astype(np.int64), 0, gz.shape[0] - 1)
    hm = m[:, 2] - gz[cy, cx]
    s_pts = m[(hm > h_lo) & (hm < h_hi)]
    lx0, ly0 = s_pts[:, 0].min() - 30, s_pts[:, 1].min() - 30
    W = int((s_pts[:, 0].max() + 30 - lx0) / res) + 1
    H = int((s_pts[:, 1].max() + 30 - ly0) / res) + 1
    occ = np.zeros((H, W), bool)
    occ[((s_pts[:, 1] - ly0) / res).astype(np.int64), ((s_pts[:, 0] - lx0) / res).astype(np.int64)] = True
    dist = ndimage.distance_transform_edt(~occ) * res
    lf = np.log((1 - p_rand) * np.exp(-0.5 * (dist / sigma) ** 2) + p_rand).astype(np.float32)
    return {"lf": lf, "x0": lx0, "y0": ly0, "res": res, "W": W, "H": H, "lmin": float(np.log(p_rand)),
            "n_struct": len(s_pts)}


def field_score(field, wx, wy):
    """Mean log likelihood over the last axis of world points wx, wy."""
    ix = ((wx - field["x0"]) / field["res"]).astype(np.int64)
    iy = ((wy - field["y0"]) / field["res"]).astype(np.int64)
    inside = (ix >= 0) & (ix < field["W"]) & (iy >= 0) & (iy < field["H"])
    v = np.full(ix.shape, field["lmin"], np.float32)
    v[inside] = field["lf"][iy[inside], ix[inside]]
    return v.mean(axis=-1)


def above_road(xyz, mount_pitch, ground_height, h_lo, h_hi, min_range, max_range):
    """Scaled camera-frame cloud -> (x, y) of the points h_lo..h_hi m above the road, in the level camera frame."""
    cp, sp = np.cos(np.radians(mount_pitch)), np.sin(np.radians(mount_pitch))
    xl = cp * xyz[:, 0] + sp * xyz[:, 2]
    zl = -sp * xyz[:, 0] + cp * xyz[:, 2]
    yl = xyz[:, 1]
    rr = np.hypot(xl, yl)
    hh = zl + ground_height
    sel = (rr <= max_range) & (rr >= min_range) & (hh > h_lo) & (hh < h_hi)
    return xl[sel], yl[sel]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("track", type=int)
    p.add_argument("--data", default="/w/data")
    p.add_argument("--cache", default="/w/cache")
    p.add_argument("--init", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--map", default="map_voxel_0.3m.pcd")
    p.add_argument("--particles", type=int, default=3000)
    p.add_argument("--init-pos", type=float, default=2.0, help="m, sigma of the start position")
    p.add_argument("--init-yaw", type=float, default=30.0, help="deg, start yaw uniform within +-this of the init")
    p.add_argument("--init-v", default="0,15", help="m/s, start speed uniform range")
    p.add_argument("--ground-height", type=float, default=1.646)
    p.add_argument("--ground-window", type=int, default=57)
    p.add_argument("--mount-pitch", type=float, default=2.4)
    p.add_argument("--max-range", type=float, default=20.0)
    p.add_argument("--min-range", type=float, default=1.0)
    p.add_argument("--h-lo", type=float, default=0.4)
    p.add_argument("--h-hi", type=float, default=3.0)
    p.add_argument("--points", type=int, default=400, help="source points per frame (random subset)")
    p.add_argument("--res", type=float, default=0.2, help="m, likelihood grid")
    p.add_argument("--sigma", type=float, default=0.4)
    p.add_argument("--p-rand", type=float, default=0.1)
    p.add_argument("--kappa", type=float, default=8.0)
    p.add_argument("--every", type=int, default=1, help="weight every N-th frame")
    p.add_argument("--acc-noise", type=float, default=2.0, help="m/s^2, speed random walk")
    p.add_argument("--yaw-noise", type=float, default=0.3, help="deg/sqrt(s), yaw random walk")
    p.add_argument("--lat-noise", type=float, default=0.05, help="m/sqrt(s), sideways random walk")
    p.add_argument("--gyro-bias", type=float, default=-0.26)
    p.add_argument("--bias-online", type=float, default=500.0)
    p.add_argument("--zupt-acc", type=float, default=0.1)
    p.add_argument("--zupt-window", type=float, default=0.5)
    p.add_argument("--yaw-offset", type=float, default=0.66)
    p.add_argument("--bias-along", type=float, default=-0.52)
    p.add_argument("--bias-lat", type=float, default=0.0)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--count", type=int, default=0)
    p.add_argument("--diag")
    p.add_argument("--pose-check")
    a = p.parse_args()
    rng = np.random.default_rng(a.seed)

    track_dir = os.path.join(a.data, f"Track{a.track}")
    frames = frame_list(track_dir, "raw_ply")
    if a.count:
        frames = frames[:a.count]
    ft = np.array([f[1] for f in frames], dtype=np.float64) / 1e9
    cdir = os.path.join(a.cache, f"Track{a.track}", "raw_ply")
    cxyz = np.load(os.path.join(cdir, "xyz.npy"), mmap_mode="r")
    cidx = np.load(os.path.join(cdir, "index.npy"))
    cts = np.load(os.path.join(cdir, "ts.npy"))
    if len(cts) < len(frames) or np.any(cts[:len(frames)] != np.array([f[1] for f in frames], dtype=np.int64)):
        sys.exit(f"{cdir}: cache does not match the frames")
    T0 = np.loadtxt(a.init, delimiter=",") if "," in open(a.init).read() else np.loadtxt(a.init)
    T0 = T0.reshape(4, 4)
    gt, gw = read_gyro(track_dir, axis="z")
    gt = gt.astype(np.float64) / 1e9
    it, iacc = read_imu_acc(track_dir)

    # ---- likelihood field of the map's structure (2D)
    t_build = time.time()
    m = read_pcd_binary(os.path.join(track_dir, a.map))
    field = build_field(m, a.h_lo, a.h_hi, a.res, a.sigma, a.p_rand)
    print(f"Track{a.track}: {len(frames)} frames; map {len(m)} pts, structure {field['n_struct']} pts "
          f"({a.h_lo}..{a.h_hi} m above ground), field {field['W']}x{field['H']} at {a.res} m "
          f"({time.time() - t_build:.0f} s)", flush=True)

    def loglik(px, py, pyaw, sx, sy):
        c, s = np.cos(pyaw)[:, None], np.sin(pyaw)[:, None]
        return field_score(field, px[:, None] + c * sx[None, :] - s * sy[None, :],
                           py[:, None] + s * sx[None, :] + c * sy[None, :])

    # ---- particles
    N = a.particles
    yaw0 = yaw_of(T0) + np.radians(a.yaw_offset)
    px = T0[0, 3] + rng.normal(0, a.init_pos, N)
    py = T0[1, 3] + rng.normal(0, a.init_pos, N)
    pyaw = yaw0 + np.radians(rng.uniform(-a.init_yaw, a.init_yaw, N))
    v_lo, v_hi = (float(v) for v in a.init_v.split(","))
    pv = rng.uniform(v_lo, v_hi, N)
    logw = np.zeros(N)

    bias0 = np.radians(a.gyro_bias)
    bias, b_sum, b_n = bias0, 0.0, 0
    gi = int(np.searchsorted(gt, ft[0], side="right"))
    t_int = ft[0]
    hist_h = []
    rows = []
    n_resample = 0
    t_start = time.time()
    for k in range(len(frames)):
        i0, n_ = int(cidx[k, 0]), int(cidx[k, 1])
        hist_h.append(cidx[k, 3])
        s = a.ground_height / np.median(hist_h[-a.ground_window:])
        dt = ft[k] - ft[k - 1] if k else 0.0
        # standstill and gyro (samples up to ft[k])
        j0, j1 = np.searchsorted(it, ft[k] - a.zupt_window), np.searchsorted(it, ft[k], side="right")
        standing = j1 - j0 >= 5 and float(np.linalg.norm(iacc[j0:j1].std(axis=0))) < a.zupt_acc
        dyaw = 0.0
        if k:
            g_first = gi
            while gi < len(gt) and gt[gi] <= ft[k]:
                dyaw += (gw[gi] - bias) * (gt[gi] - t_int)
                t_int = gt[gi]
                gi += 1
            if gi > 0:
                dyaw += (gw[gi - 1] - bias) * (ft[k] - t_int)
            t_int = ft[k]
            if standing and a.bias_online > 0 and gi > g_first:
                b_sum += float(gw[g_first:gi].sum())
                b_n += gi - g_first
                bias = (a.bias_online * bias0 + b_sum) / (a.bias_online + b_n)
        # predict
        if k:
            if standing:
                pv[:] = 0.0
            else:
                pyaw = pyaw + dyaw + rng.normal(0, np.radians(a.yaw_noise) * np.sqrt(dt), N)
                pv = np.abs(pv + rng.normal(0, a.acc_noise * dt, N))
                c, s_ = np.cos(pyaw), np.sin(pyaw)
                lat = rng.normal(0, a.lat_noise * np.sqrt(dt), N)
                px = px + pv * dt * c - lat * s_
                py = py + pv * dt * s_ + lat * c
        # weight
        if k % a.every == 0:
            sx, sy = above_road(np.asarray(cxyz[i0:i0 + n_], dtype=np.float64) * s, a.mount_pitch, a.ground_height,
                                a.h_lo, a.h_hi, a.min_range, a.max_range)
            if len(sx) > a.points:
                pick = rng.choice(len(sx), a.points, replace=False)
                sx, sy = sx[pick], sy[pick]
            if len(sx) >= 30:
                ll = loglik(px, py, pyaw, sx, sy)
                logw = logw + a.kappa * (ll - ll.max())
        w = np.exp(logw - logw.max())
        w /= w.sum()
        ess = 1.0 / np.sum(w * w)
        # output (weighted mean) before resampling: the estimate of frame k
        mx, my = float(np.sum(w * px)), float(np.sum(w * py))
        myaw = float(np.arctan2(np.sum(w * np.sin(pyaw)), np.sum(w * np.cos(pyaw))))
        mv = float(np.sum(w * pv))
        spread = float(np.sqrt(np.sum(w * ((px - mx) ** 2 + (py - my) ** 2))))
        byaw = myaw - np.radians(a.yaw_offset)
        cb, sb = np.cos(byaw), np.sin(byaw)
        ox = mx - (a.bias_along * cb - a.bias_lat * sb)
        oy = my - (a.bias_along * sb + a.bias_lat * cb)
        rows.append((k, ox, oy, wrap(byaw), mv, spread, ess, int(standing)))
        if ess < 0.5 * N:
            u = (rng.random() + np.arange(N)) / N
            idx = np.minimum(np.searchsorted(np.cumsum(w), u), N - 1)
            px = px[idx] + rng.normal(0, 0.05, N)
            py = py[idx] + rng.normal(0, 0.05, N)
            pyaw = pyaw[idx] + rng.normal(0, np.radians(0.1), N)
            pv = np.abs(pv[idx] + rng.normal(0, 0.05, N))
            logw = np.zeros(N)
            n_resample += 1
        if (k + 1) % 500 == 0:
            print(f"  {k + 1}/{len(frames)}  {(time.time() - t_start) / (k + 1):.3f} s/frame, spread {spread:.2f} m, "
                  f"v {mv:.1f} m/s, resampled {n_resample}x", flush=True)
    with open(a.out, "w") as f:
        f.write("idx,x,y,yaw\n")
        for r in rows:
            f.write(f"{r[0]},{r[1]:.6f},{r[2]:.6f},{r[3]:.6f}\n")
    print(f"wrote {a.out}; gyro bias {np.degrees(bias):+.3f} deg/s", flush=True)
    if a.diag:
        with open(a.diag, "w") as f:
            f.write("idx,x,y,yaw,v,spread,ess,standing\n")
            for r in rows:
                f.write(f"{r[0]},{r[1]:.4f},{r[2]:.4f},{r[3]:.6f},{r[4]:.3f},{r[5]:.3f},{r[6]:.1f},{r[7]}\n")
    if a.pose_check:
        ref = np.loadtxt(a.pose_check, delimiter=",", skiprows=1)
        out = np.array([[r[1], r[2], r[3]] for r in rows])
        n = min(len(out), len(ref))
        d = out[:n, :2] - ref[:n, 1:3]
        e = np.linalg.norm(d, axis=1)
        ey = np.degrees(wrap(out[:n, 2] - ref[:n, 3]))
        hy = ref[:n, 3]
        along = d[:, 0] * np.cos(hy) + d[:, 1] * np.sin(hy)
        latr = -d[:, 0] * np.sin(hy) + d[:, 1] * np.cos(hy)
        print(f"vs {os.path.basename(a.pose_check)}: position RMSE {np.sqrt((e ** 2).mean()):.3f} m (max {e.max():.2f}), "
              f"yaw RMSE {np.sqrt((ey ** 2).mean()):.2f} deg -> 'score' "
              f"{np.sqrt((e ** 2).mean()) + 0.2 * np.sqrt((ey ** 2).mean()):.3f}; mean along {along.mean():+.2f} "
              f"lat {latr.mean():+.2f} m, yaw {ey.mean():+.2f} deg")
        for q_ in range(10):
            sl = slice(q_ * n // 10, (q_ + 1) * n // 10)
            print(f"    segment {q_ + 1}: pos RMSE {np.sqrt((e[sl] ** 2).mean()):6.2f} m (along {along[sl].mean():+6.2f}, "
                  f"lat {latr[sl].mean():+5.2f}), yaw RMSE {np.sqrt((ey[sl] ** 2).mean()):5.2f}", flush=True)


if __name__ == "__main__":
    main()
