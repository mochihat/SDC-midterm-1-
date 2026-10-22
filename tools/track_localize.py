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
--hyp-yaw yaw offsets around the init are tracked side by side for the first --hyp-frames frames; the hypothesis with
the lowest mean GICP error per inlier survives (a decision that uses past frames only).

Usage: python3 tools/track_localize.py TRACK --init INIT.txt --out OUT.csv [--ply 3cameras_ply|raw_ply] [--data /w/data]
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
    a = p.parse_args()

    track_dir = os.path.join(a.data, f"Track{a.track}")
    for path in (a.init, os.path.join(track_dir, a.map)):
        if not os.path.exists(path):
            sys.exit(f"missing input: {path}")
    frames = frame_list(track_dir, a.ply)
    if a.count:
        frames = frames[:a.count]
    ft = np.array([f[1] for f in frames], dtype=np.float64) / 1e9
    T0 = np.loadtxt(a.init, delimiter=",") if "," in open(a.init).read() else np.loadtxt(a.init)
    T0 = T0.reshape(4, 4)
    gt, gw = read_gyro(track_dir, axis="z")
    gt = gt.astype(np.float64) / 1e9

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
    yaw_off = np.radians(a.yaw_offset)
    t_start = time.time()
    gi = int(np.searchsorted(gt, ft[0]))
    for k, (_, ts, path) in enumerate(frames):
        xyz = read_ply_xyz(path)
        hist_h.append(ground_height(xyz))
        h = np.median(hist_h[-a.ground_window:])
        s = a.ground_height / h
        xyz = xyz[np.linalg.norm(xyz, axis=1) <= a.max_range / s] * s
        src, _ = small_gicp.preprocess_points(xyz, downsampling_resolution=0.5, num_neighbors=20, num_threads=a.threads)
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
                
        # gyro increment since the previous frame (shared by all hypotheses)
        dyaw = 0.0
        if k:
            t_prev = ft[k - 1]
            while gi < len(gt) and gt[gi] <= ft[k]:
                dyaw += (gw[gi] - bias) * (gt[gi] - t_prev)
                t_prev = gt[gi]
                gi += 1
        F = np.array([[1, 0, dt, 0], [0, 1, 0, dt], [0, 0, 1, 0], [0, 0, 0, 1]])
        q = a.qa ** 2
        Q = q * np.array([[dt ** 4 / 4, 0, dt ** 3 / 2, 0], [0, dt ** 4 / 4, 0, dt ** 3 / 2],
                          [dt ** 3 / 2, 0, dt ** 2, 0], [0, dt ** 3 / 2, 0, dt ** 2]])
        H = np.array([[1, 0, 0, 0], [0, 1, 0, 0]])
        R = np.eye(2) * a.sigma_match ** 2
        for hy in hyps:
            if a.odometry:
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
            S = H @ hy.P @ H.T + R
            d = float(np.sqrt(innov @ np.linalg.solve(S, innov)))
            # the converged flag is rarely set on these clouds; the innovation gate decides
            ok = res.num_inliers > 50 and d < a.gate and abs(wrap(gy - hy.yaw)) < np.radians(10)
            if ok:
                K = hy.P @ H.T @ np.linalg.inv(S)
                hy.x = hy.x + K @ innov
                hy.P = (np.eye(4) - K @ H) @ hy.P
                hy.yaw = wrap(hy.yaw + (1 - np.exp(-dt / a.tau_yaw)) * wrap(gy - hy.yaw)) if dt else hy.yaw
                hy.T[:3, :3] = T[:3, :3]
                hy.T[2, 3] = T[2, 3]
            if a.debug and len(hyps) == 1 and k % a.debug == 0:
                print(f"  k {k}: conv {int(res.converged)} inl {res.num_inliers} d {d:.1f} dxy "
                      f"{np.hypot(*(meas - hy.x[:2] if not ok else innov)):.2f} dyaw {np.degrees(wrap(gy - hy.yaw)):+.1f} "
                      f"v {np.hypot(hy.x[2], hy.x[3]):.1f} ok {int(ok)}", flush=True)
            # MHT score: capped squared innovation (a wrong start yaw sends the prediction off once the car moves)
            hy.score.append(min(d, 2 * a.gate) ** 2)
            hy.dist += np.hypot(*(hy.x[2:] * dt))
            hy.rows.append((k, hy.x[0], hy.x[1], hy.yaw, int(ok)))
        if len(hyps) > 1 and k + 1 >= a.hyp_frames and min(h_.dist for h_ in hyps) >= a.hyp_distance:
            best = min(hyps, key=lambda h_: np.mean(h_.score))
            print(f"MHT at frame {k}: kept yaw offset {np.degrees(wrap(best.yaw - yaw_of(T0))):+.1f} deg "
                  f"(mean capped innovation^2 {np.mean(best.score):.2f}; all "
                  + ", ".join(f"{np.mean(h_.score):.4f}" for h_ in hyps) + ")", flush=True)
            hyps = [best]
        if (k + 1) % 500 == 0:
            acc = np.mean([r[4] for r in hyps[0].rows[-500:]])
            print(f"  {k + 1}/{len(frames)}  {(time.time() - t_start) / (k + 1):.2f} s/frame, accepted {acc:.0%}", flush=True)
    rows = hyps[0].rows
    with open(a.out, "w") as f:
        f.write("idx,x,y,yaw\n")
        for k, x, y, yw, _ in rows:
            f.write(f"{k},{x:.6f},{y:.6f},{yw:.6f}\n")
    print(f"wrote {a.out}: accepted {np.mean([r[4] for r in rows]):.0%} of frames", flush=True)
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
