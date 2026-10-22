"""T7 – z / roll / pitch for GICP without the old NDT run (c3s08 / c3s10T2), and an independent camera height.

GICP needs a full 3D start pose; x, y, yaw come from the GNSS/Kalman prior, but z, roll and pitch were taken from the
old C++ NDT run (c3s08 for Track01 – itself started from a leaderboard-fitted prior). Here they come from the map:
  ground   robust plane through the map points around (x, y) (radius --radius, lowest --band m above the 5th
           percentile height): ground height z_g and normal n
  roll, pitch  from n expressed in the vehicle heading frame
  z        = z_g + camera height H
H is measured, not assumed: H = z(old NDT pose) - z_g(map) on the frames the old run matched (median), and compared
with the 1.646 m implied by the scale constant (0.8 x median road height in the clouds). Likewise one constant roll and
one constant pitch offset (camera mounting: the cloud frame is tilted against the ground) = median(old - map).
So the old run only calibrates three numbers per track instead of giving every frame's pose.
Writes a 3x4-per-row pose file usable as --pose-source FILE.txt of gicp_refine.py (one row per frame, in order).

Usage: python3 tools/t7_pose_source.py TRACK --prior PRIOR.csv --old-run c3s08 --out OUT_result.txt
                                       [--height auto|<metres>] [--radius 6] [--band 0.4]
"""
import argparse
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gicp_refine import load_run_poses, read_pcd_binary, yaw_of  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ground_plane(m, tree, x, y, radius, band):
    idx = tree.query_ball_point((x, y), radius)
    if len(idx) < 30:
        return None
    pts = m[idx]
    z5 = np.percentile(pts[:, 2], 5)
    g = pts[pts[:, 2] <= z5 + band]
    if len(g) < 20:
        return None
    A = np.c_[g[:, 0] - x, g[:, 1] - y, np.ones(len(g))]
    for _ in range(3):  # plane z = a dx + b dy + c, re-fit without the worst 20 %
        coef = np.linalg.lstsq(A, g[:, 2], rcond=None)[0]
        r = np.abs(A @ coef - g[:, 2])
        keep = r <= np.percentile(r, 80)
        A, g = A[keep], g[keep]
    a, b, c = coef
    n = np.array([-a, -b, 1.0])
    return c, n / np.linalg.norm(n)


def rpy_matrix(roll, pitch, yaw):
    cr, sr, cp, sp, cy, sy = np.cos(roll), np.sin(roll), np.cos(pitch), np.sin(pitch), np.cos(yaw), np.sin(yaw)
    return np.array([[cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
                     [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
                     [-sp, cp * sr, cp * cr]])


def rpy_of(R):
    return np.arctan2(R[2, 1], R[2, 2]), -np.arcsin(np.clip(R[2, 0], -1, 1))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("track", type=int, choices=[1, 2])
    p.add_argument("--data", default=os.path.join(os.path.dirname(ROOT), "data"))
    p.add_argument("--prior", required=True)
    p.add_argument("--old-run", required=True, help="old C++ run tag, only to MEASURE the camera height and compare")
    p.add_argument("--out", required=True)
    p.add_argument("--height", default="auto")
    p.add_argument("--radius", type=float, default=6.0)
    p.add_argument("--band", type=float, default=0.4)
    a = p.parse_args()
    mp = os.path.join(a.data, f"Track{a.track}", "map_voxel_0.3m.pcd")
    for path in (a.prior, mp):
        if not os.path.exists(path):
            sys.exit(f"missing input: {path}")
    prior = np.loadtxt(a.prior, delimiter=",", skiprows=1)[:, 1:4]
    m = read_pcd_binary(mp)
    tree = cKDTree(m[:, :2])
    old = load_run_poses(a.old_run, a.track)
    if not old:
        sys.exit(f"no poses for run {a.old_run}")

    planes = [ground_plane(m, tree, x, y, a.radius, a.band) for x, y, _ in prior]
    miss = sum(pl is None for pl in planes)
    # camera height from the old run (measurement only)
    hs, dr, dp = [], [], []
    for k, T in old.items():
        if k >= len(prior) or planes[k] is None:
            continue
        hs.append(T[2, 3] - planes[k][0])
    hs = np.array(hs)
    print(f"Track{a.track}: {len(prior)} frames, ground plane missing on {miss}")
    print(f"camera height = z(old {a.old_run}) - map ground: median {np.median(hs):.3f} m, IQR "
          f"{np.percentile(hs, 25):.3f}..{np.percentile(hs, 75):.3f} m (n={len(hs)}); scale constant implies 1.646 m")
    H = float(np.median(hs)) if a.height == "auto" else float(a.height)
    d_roll, d_pitch = [], []
    for k, T in old.items():
        if k >= len(prior) or planes[k] is None:
            continue
        n = planes[k][1]
        c, s = np.cos(prior[k, 2]), np.sin(prior[k, 2])
        pr = np.arctan2(c * n[0] + s * n[1], n[2])
        rr = -np.arctan2(-s * n[0] + c * n[1], n[2])
        r0, p0 = rpy_of(T[:3, :3])
        d_roll.append(r0 - rr)
        d_pitch.append(p0 - pr)
    mount_roll, mount_pitch = float(np.median(d_roll)), float(np.median(d_pitch))
    print(f"mounting offsets (median old - map): roll {np.degrees(mount_roll):+.2f} deg, pitch {np.degrees(mount_pitch):+.2f} deg")

    rows, cmp = [], []
    last = None
    for k, (x, y, yaw) in enumerate(prior):
        pl = planes[k] or last
        last = pl
        zg, n = pl
        # roll / pitch: the ground normal seen in the heading frame
        c, s = np.cos(yaw), np.sin(yaw)
        nf = c * n[0] + s * n[1]         # component along heading
        nl = -s * n[0] + c * n[1]        # component to the left
        pitch = np.arctan2(nf, n[2])     # nose down on a downhill slope -> positive pitch in this convention
        roll = -np.arctan2(nl, n[2])
        roll, pitch = roll + mount_roll, pitch + mount_pitch
        R = rpy_matrix(roll, pitch, yaw)
        rows.append(np.c_[R, [x, y, zg + H]].reshape(-1))
        if k in old:
            r0, p0 = rpy_of(old[k][:3, :3])
            cmp.append((zg + H - old[k][2, 3], np.degrees(roll - r0), np.degrees(pitch - p0)))
    cmp = np.array(cmp)
    print(f"vs old run on {len(cmp)} frames: z diff RMS {np.sqrt((cmp[:, 0] ** 2).mean()):.3f} m (mean {cmp[:, 0].mean():+.3f}), "
          f"roll diff RMS {np.sqrt((cmp[:, 1] ** 2).mean()):.2f} deg (mean {cmp[:, 1].mean():+.2f}), "
          f"pitch diff RMS {np.sqrt((cmp[:, 2] ** 2).mean()):.2f} deg (mean {cmp[:, 2].mean():+.2f})")
    np.savetxt(a.out, np.array(rows), fmt="%.6f")
    print(f"wrote {a.out} (camera height {H:.3f} m)")


if __name__ == "__main__":
    main()
