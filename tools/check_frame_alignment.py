"""Check axis convention and scale of image point clouds against the LiDAR map.

For a few frames, the cloud is placed at the GNSS pose (x, y, yaw) on the map ground and a
brute-force search over scale, yaw offset and planar offset reports which combination puts
the most points close to the map.

Usage (inside container):
  python3 check_frame_alignment.py TRACK_DIR TRACK_NAME PRIOR_CSV PLY_SUBDIR [frame ...]
"""
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(__file__))
from pc_io import read_pcd_xyz, read_ply_xyz  # noqa: E402


def rot_z(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def describe(pts):
    r = np.linalg.norm(pts, axis=1)
    q = lambda v: " ".join(f"{p:+.2f}" for p in np.percentile(v, [1, 10, 50, 90, 99]))
    print(f"  points {len(pts)}; percentiles 1/10/50/90/99")
    print(f"    x {q(pts[:, 0])}\n    y {q(pts[:, 1])}\n    z {q(pts[:, 2])}\n    range {q(r)}")


def main(track_dir, track, prior_csv, ply_subdir, *frames):
    scales = [float(v) for v in os.environ.get("SCALES", "3,6,8,9,10,11,12,14").split(",")]
    prior = np.loadtxt(prior_csv, delimiter=",", skiprows=1)
    names = sorted(n for n in os.listdir(os.path.join(track_dir, ply_subdir)) if n.endswith(".ply"))
    frames = [int(f) for f in frames] or [0, len(names) // 4, len(names) // 2, 3 * len(names) // 4]
    full_map = read_pcd_xyz(os.path.join(track_dir, "map_downsampled_1m.pcd"))
    print(f"map points {len(full_map)}")

    yaw_offsets = np.radians(np.arange(-30, 31, 3))
    shifts = np.arange(-4, 4.01, 1.0)
    summary = []
    for fi in frames:
        x0, y0, yaw0 = prior[fi, 1:4]
        pts = read_ply_xyz(os.path.join(track_dir, ply_subdir, names[fi]))
        print(f"\n== frame {fi} ({names[fi]}) GNSS x={x0:.2f} y={y0:.2f} yaw={np.degrees(yaw0):.1f} deg")
        describe(pts)

        local = full_map[(np.abs(full_map[:, 0] - x0) < 120) & (np.abs(full_map[:, 1] - y0) < 120)]
        near = local[np.hypot(local[:, 0] - x0, local[:, 1] - y0) < 4]
        ground = np.percentile(near[:, 2], 10) if len(near) else np.median(local[:, 2])
        tree = cKDTree(local)
        # Score only above-ground structure; the road plane matches at any scale.
        h = -np.percentile(pts[:, 2], 5)
        structure = pts[pts[:, 2] > -0.5 * h]
        sample = structure[np.random.default_rng(0).choice(len(structure), min(3000, len(structure)), replace=False)]

        best = []
        for s in scales:
            p = sample * s
            # Put the cloud's ground (low z percentile) on the map ground.
            dz = ground + h * s
            top = (np.inf, None)
            for dyaw in yaw_offsets:
                w = p @ rot_z(yaw0 + dyaw).T
                for dx in shifts:
                    for dy in shifts:
                        d, _ = tree.query(w + [x0 + dx, y0 + dy, dz], distance_upper_bound=2.0)
                        cost = np.mean(np.minimum(d, 2.0))
                        if cost < top[0]:
                            top = (cost, (np.degrees(dyaw), dx, dy))
            inlier = top[0]
            best.append((inlier, s, *top[1]))
            print(f"  scale {s:3.1f}: mean clipped NN dist {top[0]:.3f} m at dyaw {top[1][0]:+5.1f} deg, "
                  f"dx {top[1][1]:+.1f}, dy {top[1][2]:+.1f}")
        best.sort()
        summary.append((fi, best[0]))
    print("\nbest per frame (cost, scale, dyaw_deg, dx, dy):")
    for fi, b in summary:
        print(f"  frame {fi}: {b[0]:.3f} scale {b[1]} dyaw {b[2]:+.1f} dx {b[3]:+.1f} dy {b[4]:+.1f}")


if __name__ == "__main__":
    main(*sys.argv[1:])
