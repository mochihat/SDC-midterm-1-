"""GICP of the LoGeR raw_ply clouds against the 0.3 m map, started at the poses of a trajectory (23/10): one match per
frame, written in the debug-CSV layout of gicp_refine.py (timestamp_ns, accepted, ndt_x, ndt_y, ndt_yaw, inliers) so
that tools/map_yaw_fuse.py can use it as the slow yaw reference. Settings as tools/track_localize.py: scale = 1.646 m /
trailing-median road height, range <= 20 m, 0.5 m source voxels, GICP yaw minus --yaw-offset; z / roll / pitch from the
map ground plane under (x, y) plus the camera mounting (as --level-init).

Usage: python3 tools/raw_gicp_at_poses.py TRACK TRAJ.csv OUT_DEBUG.csv [--threads 8]
"""
import argparse
import os
import sys

import numpy as np
import small_gicp
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gicp_refine import read_pcd_binary, rot_z, yaw_of  # noqa: E402
from t7_pose_source import ground_plane, rpy_matrix  # noqa: E402


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("track", type=int)
    p.add_argument("traj")
    p.add_argument("out")
    p.add_argument("--data", default="/w/data")
    p.add_argument("--cache", default="/w/cache")
    p.add_argument("--yaw-offset", type=float, default=0.66)
    p.add_argument("--mount-pitch", type=float, default=2.4)
    p.add_argument("--max-range", type=float, default=20.0)
    p.add_argument("--threads", type=int, default=8)
    a = p.parse_args()
    tr = np.loadtxt(a.traj, delimiter=",", skiprows=1)
    cdir = os.path.join(a.cache, f"Track{a.track}", "raw_ply")
    cxyz = np.load(os.path.join(cdir, "xyz.npy"), mmap_mode="r")
    cidx = np.load(os.path.join(cdir, "index.npy"))
    ts = np.load(os.path.join(cdir, "ts.npy"))
    if len(cidx) != len(tr):
        sys.exit(f"{len(tr)} trajectory rows, {len(cidx)} raw_ply frames")
    m = read_pcd_binary(os.path.join(a.data, f"Track{a.track}", "map_voxel_0.3m.pcd"))
    origin = np.round(m.mean(axis=0))
    target, tree = small_gicp.preprocess_points(m - origin, downsampling_resolution=0.3, num_neighbors=20,
                                                num_threads=a.threads)
    kd = cKDTree(m[:, :2])
    yoff = np.radians(a.yaw_offset)
    rows = []
    for k in range(len(tr)):
        s = 1.646 / np.median(cidx[max(0, k - 56):k + 1, 3])
        i0, n = int(cidx[k, 0]), int(cidx[k, 1])
        xyz = np.asarray(cxyz[i0:i0 + n], dtype=np.float64)
        xyz = xyz[np.linalg.norm(xyz, axis=1) <= a.max_range / s] * s
        src, _ = small_gicp.preprocess_points(xyz, downsampling_resolution=0.5, num_neighbors=20, num_threads=a.threads)
        x, y, yaw = tr[k, 1], tr[k, 2], tr[k, 3]
        pl = ground_plane(m, kd, x, y, 6.0, 0.4)
        T0 = np.eye(4)
        if pl is None:
            T0[:3, :3] = rot_z(yaw + yoff)
            T0[:3, 3] = (x, y, np.median(m[kd.query_ball_point((x, y), 5.0), 2]) + 1.646)
        else:
            zg, nrm = pl
            c0, s0 = np.cos(yaw), np.sin(yaw)
            pitch = np.arctan2(c0 * nrm[0] + s0 * nrm[1], nrm[2]) + np.radians(a.mount_pitch)
            roll = -np.arctan2(-s0 * nrm[0] + c0 * nrm[1], nrm[2])
            T0[:3, :3] = rpy_matrix(roll, pitch, yaw + yoff)
            T0[:3, 3] = (x, y, zg + 1.646)
        init = T0.copy()
        init[:3, 3] -= origin
        res = small_gicp.align(target, src, tree, init, registration_type="GICP", max_correspondence_distance=1.0,
                               max_iterations=100, num_threads=a.threads)
        T = np.array(res.T_target_source)
        T[:3, 3] += origin
        gy = yaw_of(T) - yoff
        dyaw = np.degrees((gy - yaw + np.pi) % (2 * np.pi) - np.pi)
        ok = res.num_inliers > 50 and np.hypot(T[0, 3] - x, T[1, 3] - y) < 2.0 and abs(dyaw) < 5.0
        rows.append((k, int(ts[k]), int(ok), T[0, 3], T[1, 3], gy, res.num_inliers))
        if k % 500 == 0:
            print(f"  {k}/{len(tr)}", flush=True)
    with open(a.out, "w") as f:
        f.write("idx,timestamp_ns,accepted,ndt_x,ndt_y,ndt_yaw,inliers\n")
        for r in rows:
            f.write(f"{r[0]},{r[1]},{r[2]},{r[3]:.4f},{r[4]:.4f},{r[5]:.6f},{r[6]}\n")
    acc = np.mean([r[2] for r in rows])
    print(f"wrote {a.out}: {acc:.0%} accepted")


if __name__ == "__main__":
    main()
