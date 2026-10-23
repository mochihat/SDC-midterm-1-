"""Causal map-based localization WITHOUT GNSS (Track03; validated on Track01/02 by ignoring their GNSS).

Rule 10/22: only the current and past frames are used. Per frame k, in time order:
  1. scale: road height h in the unscaled cloud (ground_scale.py), trailing median of the last --ground-window frames,
     scale = --ground-height / h (1.646 m: same car / camera as Track01-02)
  2. predict: constant-velocity Kalman filter on (x, y, vx, vy) (process noise --qa m/s^2); yaw integrated from the IMU
     gyro z (bias: mean rate while standing at the start, then a slow PI correction)
  3. measure: GICP of the cloud (range <= --max-range, the pipeline's 20 m) against the 0.3 m LiDAR map, started from
     the prediction (z / roll / pitch: last accepted match); minus the calibrated GICP offset (--bias-along /
     --bias-lat, vehicle frame, measured on Track01/02 against GNSS) and camera yaw offset (--yaw-offset)
  4. update: Kalman update with R = --sigma-match^2 when the match converged and the innovation is < --gate sigma;
     yaw += (1 - exp(-dt / --tau-yaw)) * wrap(match yaw - prediction)
--odometry G: the motion between frames comes from scan-to-scan GICP of the current cloud against the cloud G frames
earlier (forward / lateral displacement, divided by G; yaw stays the gyro's) instead of the constant-velocity model.
Validated on Track01: within ~5 % of the true speed at >= 10 m/s, about half of it below 5 m/s. Process noise then
--odo-noise (fraction of the step) + 0.02 m per frame.
Start: --init (4x4 init_guess.txt, may be noisy: Track02's yaw is ~19 deg off, Track03's roll / pitch ~15 deg).
--level-init keeps x, y, yaw of the init and rebuilds z, roll, pitch from the map ground plane under (x, y) plus the
camera mounting (pitch --mount-pitch, height --ground-height), as in tools/t7_pose_source.py. Multi-hypothesis start (MHT, Thrun ch. 7):
--hyp-yaw yaw offsets around the init are tracked side by side; once every hypothesis has travelled --hyp-distance m
(and at least --hyp-frames frames passed) only the one with the lowest mean capped innovation survives.
Causal output (23/10): every frame writes the pose of the hypothesis that is best AT THAT FRAME (scores of frames <= k);
the survivor's earlier poses are never written back over frames that were already output.
IMU (23/10, all from samples up to the current frame): --zupt-acc: the car stands when the accelerometer std over the
last --zupt-window s is below this -> no odometry step, no yaw change; --bias-online N0: the gyro bias is re-estimated
from the standing samples (prior --gyro-bias with the weight of N0 samples); --yaw-gate: a map match whose yaw differs
from the prediction by more than this is rejected; --turn-rate: above this yaw rate the map yaw does not pull the yaw
(--turn-skip all: the match is not used at all while turning).
--csm-window A (23/10): before the GICP update, correlative scan matching (Olson 2009) on the 2D likelihood field of
the map's above-road structure (mcl_localize.build_field): the above-road points of the cloud, at the predicted yaw,
are scored on an along / lateral grid (+-A m along, clipped to 3 sigma of the prediction, +- --csm-lat m), the grid
score times --csm-kappa plus the Gaussian prior of the prediction gives the posterior on the grid, whose mean and
covariance replace the position estimate (a local histogram filter: it sees the true along-road position as far as A m
away, where GICP only reaches ~1-2 m). The GICP update then runs from there as before.

Usage: python3 tools/track_localize.py TRACK --init INIT.txt --out OUT.csv [--ply 3cameras_ply|raw_ply] [--data /w/data]
         [--cache /w/cache]   (binary raw_ply from tools/cache_ply.py: same clouds and road heights, ~10x faster)
         [--diag DIAG.csv]    (per-frame match details of the output hypothesis)
         [--pose-check REF.csv]   (only for validation on Track01/02: prints the error against a reference)
"""
import argparse
import csv
import os
import sys
import time

import numpy as np
import small_gicp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gicp_refine import frame_list, read_pcd_binary, read_ply_xyz, rot_z, yaw_of  # noqa: E402
from ground_scale import ground_height  # noqa: E402
from yaw_fusion import read_gyro  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


def csm_update(field, field_score, x, P, yaw, yaw_off, sx, sy, a):
    """Correlative scan matching on an along / lateral grid around the prediction; returns the posterior (x, P)."""
    c, s = np.cos(yaw), np.sin(yaw)
    Rh = np.array([[c, -s], [s, c]])                       # heading frame -> world
    Pr = Rh.T @ P[:2, :2] @ Rh                             # prior covariance, along / lateral
    A = float(np.clip(3 * np.sqrt(max(Pr[0, 0], 1e-6)), a.csm_min_window, a.csm_window))
    L = float(np.clip(3 * np.sqrt(max(Pr[1, 1], 1e-6)), 1.0, a.csm_lat))
    da = np.arange(-A, A + 1e-9, a.csm_step)
    dl = np.arange(-L, L + 1e-9, a.csm_step)
    ga, gl = np.meshgrid(da, dl, indexing="ij")
    ga, gl = ga.ravel(), gl.ravel()
    # camera position for each grid offset (reference + lever), cloud rotated by the camera yaw
    lever = np.array([a.bias_along * c - a.bias_lat * s, a.bias_along * s + a.bias_lat * c])
    cam = x[:2] + lever
    cy_, sy_ = np.cos(yaw + yaw_off), np.sin(yaw + yaw_off)
    wx0 = cy_ * sx - sy_ * sy
    wy0 = sy_ * sx + cy_ * sy
    ox = cam[0] + ga * c - gl * s
    oy = cam[1] + ga * s + gl * c
    sc = field_score(field, ox[:, None] + wx0[None, :], oy[:, None] + wy0[None, :])
    Pi = np.linalg.inv(Pr + np.eye(2) * 1e-6)
    lp = a.csm_kappa * sc - 0.5 * (Pi[0, 0] * ga * ga + 2 * Pi[0, 1] * ga * gl + Pi[1, 1] * gl * gl)
    w = np.exp(lp - lp.max())
    w /= w.sum()
    mu = np.array([np.sum(w * ga), np.sum(w * gl)])
    C = np.array([[np.sum(w * (ga - mu[0]) ** 2), np.sum(w * (ga - mu[0]) * (gl - mu[1]))],
                  [np.sum(w * (ga - mu[0]) * (gl - mu[1])), np.sum(w * (gl - mu[1]) ** 2)]])
    C += np.eye(2) * a.csm_step ** 2 / 12
    contrast = float(sc.max() - np.median(sc))
    info = (float(mu[0]), float(np.sqrt(C[0, 0])), contrast, float(sc.max()))
    if a.csm_mode == "kalman":
        # likelihood-only fit on the grid -> measurement (z, R) of the position, Kalman update of the whole state
        wl = np.exp(a.csm_kappa * (sc - sc.max()))
        wl /= wl.sum()
        ml = np.array([np.sum(wl * ga), np.sum(wl * gl)])
        Cl = np.array([[np.sum(wl * (ga - ml[0]) ** 2), np.sum(wl * (ga - ml[0]) * (gl - ml[1]))],
                       [np.sum(wl * (ga - ml[0]) * (gl - ml[1])), np.sum(wl * (gl - ml[1]) ** 2)]])
        Cl = a.csm_inflate * (Cl + np.eye(2) * a.csm_step ** 2 / 12)
        z = x[:2] + Rh @ ml
        Rw = Rh @ Cl @ Rh.T
        H = np.zeros((2, len(x)))
        H[0, 0] = H[1, 1] = 1.0
        S = H @ P @ H.T + Rw
        inn = z - x[:2]
        if float(np.sqrt(inn @ np.linalg.solve(S, inn))) > a.csm_gate:
            return x, P, info
        K = P @ H.T @ np.linalg.inv(S)
        return x + K @ inn, (np.eye(len(x)) - K @ H) @ P, info
    x = x.copy()
    x[:2] = x[:2] + Rh @ mu
    P = P.copy()
    P[:2, :2] = Rh @ C @ Rh.T
    return x, P, info


def read_imu_acc(track_dir):
    """IMU timestamps (s) and accelerometer vectors, for the standstill test."""
    from pathlib import Path
    from rosbags.highlevel import AnyReader
    rows = []
    with AnyReader([Path(track_dir)]) as r:
        conns = [c for c in r.connections if c.topic == "/imu/data"]
        for c, ts, raw in r.messages(connections=conns):
            acc = r.deserialize(raw, c.msgtype).linear_acceleration
            rows.append((ts, acc.x, acc.y, acc.z))
    rows.sort()
    a = np.array(rows, dtype=np.float64)
    return a[:, 0] / 1e9, a[:, 1:4]


class Hypothesis:
    def __init__(self, T0, yaw_off):
        self.T = T0.copy()
        self.T[:3, :3] = rot_z(yaw_off) @ T0[:3, :3]
        self.x = np.array([self.T[0, 3], self.T[1, 3], 0.0, 0.0])
        self.P = np.diag([1.0, 1.0, 4.0, 4.0])
        self.yaw = yaw_of(self.T)
        self.score = []
        self.rows = []
        self.dist = 0.0
        self.pull = 0.0      # accumulated map-yaw correction (diagnostics)
        self.offset = yaw_off


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("track", type=int)
    p.add_argument("--data", default=os.path.join(os.path.dirname(ROOT), "data"))
    p.add_argument("--init", required=True, help="4x4 initial pose (init_guess.txt)")
    p.add_argument("--out", required=True)
    p.add_argument("--ply", default="3cameras_ply")
    p.add_argument("--map", default="map_voxel_0.3m.pcd")
    p.add_argument("--ground-height", type=float, default=1.646)
    p.add_argument("--ground-window", type=int, default=57)
    p.add_argument("--max-range", type=float, default=20.0)
    p.add_argument("--qa", type=float, default=1.0)
    p.add_argument("--sigma-match", type=float, default=0.7)
    p.add_argument("--gate", type=float, default=3.0)
    p.add_argument("--tau-yaw", type=float, default=5.0)
    p.add_argument("--bias-along", type=float, default=-0.10)
    p.add_argument("--bias-lat", type=float, default=-0.29)
    p.add_argument("--yaw-offset", type=float, default=1.1, help="deg, GICP yaw - body yaw (calibration)")
    p.add_argument("--hyp-yaw", default="-24,-18,-12,-6,0,6,12,18,24", help="deg offsets around the init yaw")
    p.add_argument("--hyp-frames", type=int, default=60)
    p.add_argument("--hyp-distance", type=float, default=25.0, help="m travelled before the hypotheses are pruned")
    p.add_argument("--threads", type=int, default=8)
    p.add_argument("--iterations", type=int, default=100)
    p.add_argument("--pose-check", help="reference CSV (validation only)")
    p.add_argument("--count", type=int, default=0)
    p.add_argument("--level-init", action="store_true")
    p.add_argument("--debug", type=int, default=0, help="print match details every N frames (0 = off)")
    p.add_argument("--odometry", type=int, default=0, help="scan-to-scan odometry gap in frames (0 = constant velocity)")
    p.add_argument("--odo-noise", type=float, default=0.15)
    p.add_argument("--gyro-bias", type=float, default=-0.26, help="deg/s, IMU z-gyro bias (calibration)")
    p.add_argument("--odo-target", type=float, default=0.0,
                   help="m; if > 0 the gap adapts so the displacement is about this (gap between 6 and --odometry)")
    p.add_argument("--mount-pitch", type=float, default=2.4, help="deg (T7: +2.47 Track01, +2.30 Track02)")
    p.add_argument("--cache", help="directory of tools/cache_ply.py (raw_ply only)")
    p.add_argument("--diag", help="per-frame diagnostics CSV")
    p.add_argument("--zupt-acc", type=float, default=0.0, help="m/s^2, standstill threshold (0 = off)")
    p.add_argument("--zupt-window", type=float, default=0.5, help="s")
    p.add_argument("--bias-online", type=float, default=0.0, help="prior weight in samples (0 = fixed bias)")
    p.add_argument("--yaw-gate", type=float, default=10.0, help="deg")
    p.add_argument("--turn-rate", type=float, default=0.0, help="deg/s (0 = off)")
    p.add_argument("--turn-skip", default="yaw", choices=["yaw", "all"])
    p.add_argument("--csm-window", type=float, default=0.0, help="m, max along-road search (0 = off)")
    p.add_argument("--csm-min-window", type=float, default=4.0)
    p.add_argument("--csm-lat", type=float, default=2.0)
    p.add_argument("--csm-step", type=float, default=0.5)
    p.add_argument("--csm-kappa", type=float, default=30.0)
    p.add_argument("--csm-sigma", type=float, default=0.4, help="m, likelihood field")
    p.add_argument("--csm-points", type=int, default=600)
    p.add_argument("--csm-range", type=float, default=20.0)
    p.add_argument("--csm-h", default="0.4,3.0", help="m above the road (source and map)")
    p.add_argument("--no-gicp", action="store_true", help="CSM only (no GICP position / yaw update)")
    p.add_argument("--csm-mode", default="posterior", choices=["posterior", "kalman"],
                   help="posterior: the grid posterior replaces x, y; kalman: likelihood-only fit as a measurement")
    p.add_argument("--csm-inflate", type=float, default=2.0, help="kalman mode: R factor (correlated frames)")
    p.add_argument("--csm-gate", type=float, default=5.0)
    p.add_argument("--odo-filter", action="store_true",
                   help="velocity is a Kalman state (constant velocity, --qa) measured by the odometry, instead of "
                        "being overwritten by it; the map corrections then also correct the speed")
    p.add_argument("--odo-sigma", default="0.15,0.3", help="odo-filter: velocity noise = a * speed + b (m/s)")
    p.add_argument("--mht-score", default="innovation", choices=["innovation", "csm"])
    p.add_argument("--tau-yaw-start", type=float, default=0.0,
                   help="s, map-yaw pull while several start hypotheses are alive (0 = --tau-yaw)")
    p.add_argument("--hold-yaw-standing", action="store_true",
                   help="no map-yaw pull while standing (the matches of one view share their error)")
    p.add_argument("--sigma-match-along", type=float, default=0.0,
                   help="m, GICP noise along the heading (0 = --sigma-match): LoGeR GICP slides along the road")
    p.add_argument("--mht-output", default="best", choices=["best", "mean"],
                   help="before the hypotheses are pruned: the best one, or the posterior mean (prior --hyp-prior)")
    p.add_argument("--hyp-prior", type=float, default=15.0, help="deg, sigma of the start-yaw error prior")
    a = p.parse_args()

    track_dir = os.path.join(a.data, f"Track{a.track}")
    for path in (a.init, os.path.join(track_dir, a.map)):
        if not os.path.exists(path):
            sys.exit(f"missing input: {path}")
    frames = frame_list(track_dir, a.ply)
    if a.count:
        frames = frames[:a.count]
    ft = np.array([f[1] for f in frames], dtype=np.float64) / 1e9
    cache = None
    if a.cache:
        cdir = os.path.join(a.cache, f"Track{a.track}", a.ply)
        cache = (np.load(os.path.join(cdir, "xyz.npy"), mmap_mode="r"), np.load(os.path.join(cdir, "index.npy")))
        cts = np.load(os.path.join(cdir, "ts.npy"))
        if len(cts) < len(frames) or np.any(cts[:len(frames)] != np.array([f[1] for f in frames], dtype=np.int64)):
            sys.exit(f"{cdir}: cache does not match the frames of {a.ply}")
    T0 = np.loadtxt(a.init, delimiter=",") if "," in open(a.init).read() else np.loadtxt(a.init)
    T0 = T0.reshape(4, 4)
    gt, gw = read_gyro(track_dir, axis="z")
    gt = gt.astype(np.float64) / 1e9
    if a.zupt_acc > 0 or a.turn_rate > 0:
        it, iacc = read_imu_acc(track_dir)

    m = read_pcd_binary(os.path.join(track_dir, a.map))
    if a.level_init:
        from scipy.spatial import cKDTree
        from t7_pose_source import ground_plane, rpy_matrix
        pl = ground_plane(m, cKDTree(m[:, :2]), T0[0, 3], T0[1, 3], 6.0, 0.4)
        if pl is None:
            sys.exit("--level-init: no map ground around the init position")
        zg, nrm = pl
        yaw0 = yaw_of(T0)
        c0, s0 = np.cos(yaw0), np.sin(yaw0)
        pitch = np.arctan2(c0 * nrm[0] + s0 * nrm[1], nrm[2]) + np.radians(a.mount_pitch)
        roll = -np.arctan2(-s0 * nrm[0] + c0 * nrm[1], nrm[2])
        T0 = T0.copy()
        T0[:3, :3] = rpy_matrix(roll, pitch, yaw0)
        print(f"level init: z {T0[2, 3]:.2f} -> {zg + a.ground_height:.2f} m, roll {np.degrees(roll):+.1f}, "
              f"pitch {np.degrees(pitch):+.1f}, yaw {np.degrees(yaw0):+.1f} deg", flush=True)
        T0[2, 3] = zg + a.ground_height
    field = None
    if a.csm_window > 0:
        from mcl_localize import above_road, build_field, field_score
        h_lo, h_hi = (float(v) for v in a.csm_h.split(","))
        field = build_field(m, h_lo, h_hi, 0.2, a.csm_sigma, 0.1)
        csm_rng = np.random.default_rng(0)
    origin = np.round(m.mean(axis=0))
    target, tree = small_gicp.preprocess_points(m - origin, downsampling_resolution=0.3, num_neighbors=20,
                                                num_threads=a.threads)
    print(f"Track{a.track}: {len(frames)} frames ({a.ply}), map {len(m)} pts", flush=True)

    hyps = [Hypothesis(T0, np.radians(float(v))) for v in a.hyp_yaw.split(",")]
    clouds = []          # recent preprocessed clouds for the odometry
    odo_step = np.zeros(2)
    hist_h = []
    # gyro bias: a calibration constant of this IMU (same car on every track: -0.22 deg/s on Track01, -0.30 on
    # Track02, measured while standing / fitted to the heading); the first second is NOT assumed to be standing
    bias = np.radians(a.gyro_bias)
    bias_sum, bias_n = 0.0, 0
    gyro_sum = 0.0
    n_standing = 0
    yaw_off = np.radians(a.yaw_offset)
    t_start = time.time()
    gi = int(np.searchsorted(gt, ft[0], side="right"))
    t_int = ft[0]
    out_rows = []        # causal output: one row per frame, written when the frame is processed
    for k, (_, ts, path) in enumerate(frames):
        if cache is not None:
            i0, n_ = int(cache[1][k, 0]), int(cache[1][k, 1])
            xyz = np.asarray(cache[0][i0:i0 + n_], dtype=np.float64)
            hist_h.append(cache[1][k, 3])
        else:
            xyz = read_ply_xyz(path)
            hist_h.append(ground_height(xyz))
        h = np.median(hist_h[-a.ground_window:])
        s = a.ground_height / h
        xyz = xyz[np.linalg.norm(xyz, axis=1) <= a.max_range / s] * s
        src, _ = small_gicp.preprocess_points(xyz, downsampling_resolution=0.5, num_neighbors=20, num_threads=a.threads)
        if field is not None:
            full = (np.asarray(cache[0][i0:i0 + n_], dtype=np.float64) if cache is not None else read_ply_xyz(path)) * s
            csx, csy = above_road(full, a.mount_pitch, a.ground_height, h_lo, h_hi, 1.0, a.csm_range)
            if len(csx) > a.csm_points:
                pick = csm_rng.choice(len(csx), a.csm_points, replace=False)
                csx, csy = csx[pick], csy[pick]
        dt = ft[k] - ft[k - 1] if k else 0.0
        if a.odometry:
            clouds.append((src, _))
            if len(clouds) > a.odometry + 1:
                clouds.pop(0)
            gap = a.odometry
            if a.odo_target > 0:
                gap = int(np.clip(round(a.odo_target / max(abs(odo_step[0]), 1e-3)), 6, a.odometry))
            if len(clouds) >= gap + 1:
                tgt, ttree = clouds[-1 - gap]
                g0 = np.eye(4)
                g0[0, 3] = odo_step[0] * gap
                r = small_gicp.align(tgt, src, ttree, g0, registration_type="GICP", max_correspondence_distance=1.0,
                                     max_iterations=30, num_threads=a.threads)
                Tr = np.array(r.T_target_source)
                if r.num_inliers > 50 and abs(Tr[0, 3]) < 2.0 * gap:
                    odo_step = Tr[:2, 3] / gap   # forward / left per frame, cloud frame
                
        standing = False
        if a.zupt_acc > 0:
            j0, j1 = np.searchsorted(it, ft[k] - a.zupt_window), np.searchsorted(it, ft[k], side="right")
            standing = j1 - j0 >= 5 and float(np.linalg.norm(iacc[j0:j1].std(axis=0))) < a.zupt_acc
            n_standing += standing
        # gyro increment since the previous frame (shared by all hypotheses)
        # (fixed 23/10: the stretch between the last IMU sample and the frame time was dropped every frame, ~14 % of
        # every rotation at 100 Hz IMU / 28 Hz frames; it is now integrated with the latest sample's rate)
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
                bias_sum += float(gw[g_first:gi].sum())
                bias_n += gi - g_first
                bias = (a.bias_online * np.radians(a.gyro_bias) + bias_sum) / (a.bias_online + bias_n)
            if standing:
                dyaw = 0.0
                odo_step = np.zeros(2)
        gyro_sum += dyaw
        turning = False
        if a.turn_rate > 0:
            j0, j1 = np.searchsorted(gt, ft[k] - 0.3), np.searchsorted(gt, ft[k], side="right")
            turning = j1 > j0 and abs(np.degrees(gw[j0:j1].mean() - bias)) > a.turn_rate
        F = np.array([[1, 0, dt, 0], [0, 1, 0, dt], [0, 0, 1, 0], [0, 0, 0, 1]])
        q = a.qa ** 2
        Q = q * np.array([[dt ** 4 / 4, 0, dt ** 3 / 2, 0], [0, dt ** 4 / 4, 0, dt ** 3 / 2],
                          [dt ** 3 / 2, 0, dt ** 2, 0], [0, dt ** 3 / 2, 0, dt ** 2]])
        H = np.array([[1, 0, 0, 0], [0, 1, 0, 0]])
        R = np.eye(2) * a.sigma_match ** 2
        for hy in hyps:
            if a.odometry and standing:
                hy.x = hy.x.copy()
                hy.x[2:] = 0.0
            elif a.odometry and a.odo_filter:
                hy.x = F @ hy.x
                hy.P = F @ hy.P @ F.T + Q
                c_, s2 = np.cos(hy.yaw), np.sin(hy.yaw)
                zv = np.array([odo_step[0] * c_ - odo_step[1] * s2, odo_step[0] * s2 + odo_step[1] * c_]) / max(dt, 1e-3)
                if dt and np.any(odo_step):
                    oa, ob = (float(v) for v in a.odo_sigma.split(","))
                    Rv = np.eye(2) * (oa * np.hypot(*zv) + ob) ** 2
                    Hv = np.array([[0, 0, 1, 0], [0, 0, 0, 1]])
                    Sv = Hv @ hy.P @ Hv.T + Rv
                    iv = zv - hy.x[2:]
                    if float(np.sqrt(iv @ np.linalg.solve(Sv, iv))) < 3.0:
                        Kv = hy.P @ Hv.T @ np.linalg.inv(Sv)
                        hy.x = hy.x + Kv @ iv
                        hy.P = (np.eye(4) - Kv @ Hv) @ hy.P
            elif a.odometry:
                c_, s2 = np.cos(hy.yaw), np.sin(hy.yaw)
                step = np.array([odo_step[0] * c_ - odo_step[1] * s2, odo_step[0] * s2 + odo_step[1] * c_])
                hy.x = hy.x.copy()
                hy.x[:2] += step
                hy.x[2:] = step / max(dt, 1e-3)
                qn = (a.odo_noise * np.hypot(*step) + 0.02) ** 2
                hy.P = hy.P.copy()
                hy.P[:2, :2] += np.eye(2) * qn
            else:
                hy.x = F @ hy.x
                hy.P = F @ hy.P @ F.T + Q
            hy.yaw = wrap(hy.yaw + dyaw)
            csm_info = (0.0, 0.0, 0.0, 0.0)
            if field is not None and len(csx) >= 30:
                # standing: the score still ranks the MHT hypotheses (yaw), but the state is not updated
                xu, Pu, csm_info = csm_update(field, field_score, hy.x, hy.P, hy.yaw, yaw_off, csx, csy, a)
                if not standing:
                    hy.x, hy.P = xu, Pu
            Tp = hy.T.copy()
            Tp[:3, :3] = rot_z(hy.yaw - yaw_of(hy.T)) @ hy.T[:3, :3]
            Tp[0, 3], Tp[1, 3] = hy.x[0], hy.x[1]
            init = Tp.copy()
            init[:3, 3] -= origin
            res = small_gicp.align(target, src, tree, init, registration_type="GICP", max_correspondence_distance=1.0,
                                   max_iterations=a.iterations, num_threads=a.threads)
            T = np.array(res.T_target_source)
            T[:3, 3] += origin
            gy = yaw_of(T) - yaw_off
            c, s_ = np.cos(gy), np.sin(gy)
            meas = T[:2, 3] - np.array([a.bias_along * c - a.bias_lat * s_, a.bias_along * s_ + a.bias_lat * c])
            innov = meas - H @ hy.x
            if a.sigma_match_along > 0:
                ch, sh = np.cos(hy.yaw), np.sin(hy.yaw)
                Rh = np.array([[ch, -sh], [sh, ch]])
                R = Rh @ np.diag([a.sigma_match_along ** 2, a.sigma_match ** 2]) @ Rh.T
            S = H @ hy.P @ H.T + R
            d = float(np.sqrt(innov @ np.linalg.solve(S, innov)))
            # the converged flag is rarely set on these clouds; the innovation gate decides
            ok = res.num_inliers > 50 and d < a.gate and abs(wrap(gy - hy.yaw)) < np.radians(a.yaw_gate)
            if (turning and a.turn_skip == "all") or a.no_gicp:
                ok = False
            if ok:
                K = hy.P @ H.T @ np.linalg.inv(S)
                hy.x = hy.x + K @ innov
                hy.P = (np.eye(4) - K @ H) @ hy.P
                if dt and not turning and not (standing and a.hold_yaw_standing):
                    tau = a.tau_yaw_start if (a.tau_yaw_start > 0 and len(hyps) > 1) else a.tau_yaw
                    corr = (1 - np.exp(-dt / tau)) * wrap(gy - hy.yaw)
                    hy.yaw = wrap(hy.yaw + corr)
                    hy.pull += corr
                hy.T[:3, :3] = T[:3, :3]
                hy.T[2, 3] = T[2, 3]
            if a.debug and len(hyps) == 1 and k % a.debug == 0:
                print(f"  k {k}: conv {int(res.converged)} inl {res.num_inliers} d {d:.1f} dxy "
                      f"{np.hypot(*(meas - hy.x[:2] if not ok else innov)):.2f} dyaw {np.degrees(wrap(gy - hy.yaw)):+.1f} "
                      f"v {np.hypot(hy.x[2], hy.x[3]):.1f} ok {int(ok)}", flush=True)
            # MHT score: capped squared innovation (a wrong start yaw sends the prediction off once the car moves)
            hy.score.append(-csm_info[3] if a.mht_score == "csm" and field is not None else min(d, 2 * a.gate) ** 2)
            hy.dist += np.hypot(*(hy.x[2:] * dt))
            hy.rows.append((k, hy.x[0], hy.x[1], hy.yaw, int(ok), d, res.num_inliers,
                            res.error / max(res.num_inliers, 1), float(np.hypot(*innov)),
                            float(np.degrees(wrap(gy - hy.yaw))), odo_step[0], odo_step[1], len(hyps),
                            float(np.degrees(gyro_sum)), float(np.degrees(hy.pull)), int(standing), int(turning),
                            csm_info[0], csm_info[1], csm_info[2]))
        cur = min(hyps, key=lambda h_: np.mean(h_.score))
        if a.mht_output == "mean" and len(hyps) > 1:
            # posterior over the hypotheses: prior on the start-yaw error x likelihood exp(-sum of capped innovation^2 / 2)
            lw = np.array([-0.5 * np.sum(h_.score) - 0.5 * (np.degrees(h_.offset) / a.hyp_prior) ** 2 for h_ in hyps])
            w = np.exp(lw - lw.max())
            w /= w.sum()
            r0 = list(cur.rows[-1])
            r0[1] = float(sum(w_ * h_.x[0] for w_, h_ in zip(w, hyps)))
            r0[2] = float(sum(w_ * h_.x[1] for w_, h_ in zip(w, hyps)))
            r0[3] = float(np.arctan2(sum(w_ * np.sin(h_.yaw) for w_, h_ in zip(w, hyps)),
                                     sum(w_ * np.cos(h_.yaw) for w_, h_ in zip(w, hyps))))
            out_rows.append(tuple(r0))
        else:
            out_rows.append(cur.rows[-1])
        if len(hyps) > 1 and k + 1 >= a.hyp_frames and min(h_.dist for h_ in hyps) >= a.hyp_distance:
            best = min(hyps, key=lambda h_: np.mean(h_.score))
            print(f"MHT at frame {k}: kept yaw offset {np.degrees(wrap(best.yaw - yaw_of(T0))):+.1f} deg "
                  f"(mean capped innovation^2 {np.mean(best.score):.2f}; all "
                  + ", ".join(f"{np.mean(h_.score):.4f}" for h_ in hyps) + ")", flush=True)
            hyps = [best]
        if (k + 1) % 500 == 0:
            acc = np.mean([r[4] for r in out_rows[-500:]])
            print(f"  {k + 1}/{len(frames)}  {(time.time() - t_start) / (k + 1):.2f} s/frame, accepted {acc:.0%}", flush=True)
    rows = out_rows
    with open(a.out, "w") as f:
        f.write("idx,x,y,yaw\n")
        for r in rows:
            f.write(f"{r[0]},{r[1]:.6f},{r[2]:.6f},{r[3]:.6f}\n")
    print(f"wrote {a.out}: accepted {np.mean([r[4] for r in rows]):.0%} of frames"
          + (f", standing {n_standing} frames, gyro bias {np.degrees(bias):+.3f} deg/s" if a.zupt_acc > 0 else ""),
          flush=True)
    if a.diag:
        with open(a.diag, "w") as f:
            f.write("idx,x,y,yaw,ok,d,inliers,err_per_inlier,innov_m,dyaw_deg,odo_fwd,odo_lat,hyps,gyro_sum_deg,"
                    "pull_deg,standing,turning,csm_shift_along,csm_sd_along,csm_contrast\n")
            for r in rows:
                f.write(f"{r[0]},{r[1]:.4f},{r[2]:.4f},{r[3]:.6f},{r[4]},{r[5]:.3f},{r[6]},{r[7]:.5f},{r[8]:.3f},"
                        f"{r[9]:.2f},{r[10]:.4f},{r[11]:.4f},{r[12]},{r[13]:.3f},{r[14]:.3f},{r[15]},{r[16]},"
                        f"{r[17]:.3f},{r[18]:.3f},{r[19]:.3f}\n")
    if a.pose_check:
        ref = np.loadtxt(a.pose_check, delimiter=",", skiprows=1)
        out = np.array([[r[1], r[2], r[3]] for r in rows])
        n = min(len(out), len(ref))
        e = np.linalg.norm(out[:n, :2] - ref[:n, 1:3], axis=1)
        ey = np.degrees(wrap(out[:n, 2] - ref[:n, 3]))
        print(f"vs {os.path.basename(a.pose_check)}: position RMSE {np.sqrt((e ** 2).mean()):.3f} m (max {e.max():.2f}), "
              f"yaw RMSE {np.sqrt((ey ** 2).mean()):.2f} deg -> 'score' {np.sqrt((e ** 2).mean()) + 0.2 * np.sqrt((ey ** 2).mean()):.3f}")
        for q_ in range(10):
            sl = slice(q_ * n // 10, (q_ + 1) * n // 10)
            print(f"    segment {q_ + 1}: pos RMSE {np.sqrt((e[sl] ** 2).mean()):.2f} m", flush=True)


if __name__ == "__main__":
    main()
