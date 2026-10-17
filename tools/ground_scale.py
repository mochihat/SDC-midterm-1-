"""Per-frame ground height of image point clouds, to recover their metric scale.

The clouds are in a camera-centred FLU frame with arbitrary scale. The road plane sits at
z = -h (h = camera height in cloud units), so scale = real_camera_height / h. Also reports
the map ground under the GNSS position, for comparison with the GNSS z.

Usage (inside container):
  python3 ground_scale.py TRACK_DIR PRIOR_CSV PLY_SUBDIR STEP
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from pc_io import read_pcd_xyz, read_ply_xyz  # noqa: E402


def ground_height(pts):
    """Camera height above the road in cloud units: fit z = c over the near, low points."""
    near = pts[(pts[:, 0] > 0) & (np.hypot(pts[:, 0], pts[:, 1]) < np.percentile(np.hypot(pts[:, 0], pts[:, 1]), 60))]
    z = near[:, 2]
    low = z[z < np.percentile(z, 30)]
    hist, edges = np.histogram(low, bins=60)
    k = np.argmax(hist)
    return -(edges[k] + edges[k + 1]) / 2


def main(track_dir, prior_csv, ply_subdir, step):
    prior = np.loadtxt(prior_csv, delimiter=",", skiprows=1)
    names = sorted(n for n in os.listdir(os.path.join(track_dir, ply_subdir)) if n.endswith(".ply"))
    full_map = read_pcd_xyz(os.path.join(track_dir, "map_downsampled_1m.pcd"))
    rows = []
    for fi in range(0, len(names), int(step)):
        pts = read_ply_xyz(os.path.join(track_dir, ply_subdir, names[fi]))
        h = ground_height(pts)
        reach = np.percentile(pts[:, 0], 95)
        x0, y0 = prior[fi, 1:3]
        near = full_map[np.hypot(full_map[:, 0] - x0, full_map[:, 1] - y0) < 3]
        mg = np.percentile(near[:, 2], 20) if len(near) else np.nan
        rows.append((fi, h, reach, mg))
        print(f"frame {fi:5d}: ground h {h:.4f}  x95 {reach:.3f}  x95/h {reach / h:6.1f}  map ground z {mg:.2f}")
    h = np.array([r[1] for r in rows])
    print(f"\nh: median {np.median(h):.4f}  min {h.min():.4f}  max {h.max():.4f}  rel.std {h.std() / h.mean():.2%}")
    for cam_h in (1.5, 1.8, 2.0, 2.2):
        print(f"  if camera height {cam_h} m -> scale median {cam_h / np.median(h):.2f}")


if __name__ == "__main__":
    main(*sys.argv[1:])
