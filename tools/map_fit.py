"""Offline metric 1: how well a result file puts the image point clouds onto the LiDAR map (no ground truth).

For every --stride-th frame, the 3cameras_ply cloud (per-frame road-height scale, read from a GICP debug CSV) is
placed at the result's x, y, yaw (z / roll / pitch from a C++ run, as in gicp_refine.py) and every point's distance
to the nearest map point (0.3 m voxel map) is measured. Only points more than 0.3 m above the road are scored:
the road surface fits at any x, y and would hide position errors. Reported per file:
  med    median point-to-map distance (m, capped at 2 m)       lower = better
  in30   share of points within 0.3 m of the map               higher = better

--validate compares the metric with the Kaggle scores of earlier pipeline submissions
(docs/nhat-ky/data/submission_stats.csv, classes pipeline / mixed, 5-decimal scores) by Spearman rank correlation:
near +1 for `med` (or -1 for `in30`) means the metric orders files like Kaggle does.

Usage: python3 tools/map_fit.py TRACK FILE.csv [FILE.csv ...] [--stride 10]
       python3 tools/map_fit.py TRACK --validate
"""
import argparse
import csv
import glob
import os
import sys

import numpy as np
import small_gicp
from scipy.spatial import cKDTree
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gicp_refine import (RESULT, frame_list, load_run_poses, prior_guess, read_pcd_binary,  # noqa: E402
                         read_ply_xyz)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSE_SOURCE = {1: "c3s08", 2: "c3s10T2"}
SCALE_FROM = {1: "reg/clean/clean_gicp_p1_Track1_debug.csv", 2: "reg/clean/clean_gicp_p1_Track2_debug.csv"}
GROUND = 1.646


def load_clouds(track, data, stride, max_range=40.0, voxel=0.5):
    frames = frame_list(os.path.join(data, f"Track{track}"))
    with open(os.path.join(RESULT, SCALE_FROM[track])) as f:
        scale = {int(r["idx"]): float(r["scale"]) for r in csv.DictReader(f)}
    poses = load_run_poses(POSE_SOURCE[track], track)
    keys = np.array(sorted(poses))
    clouds = []
    for i in range(0, len(frames), stride):
        s = scale[i]
        xyz = read_ply_xyz(frames[i][2])
        xyz = xyz[np.linalg.norm(xyz, axis=1) <= max_range / s] * s
        xyz = xyz[xyz[:, 2] > -GROUND + 0.3]  # above the road
        xyz = np.asarray(small_gicp.voxelgrid_sampling(xyz, voxel).points())[:, :3]
        ref = poses[int(keys[np.argmin(np.abs(keys - i))])]
        clouds.append((i, xyz, ref))
    return clouds


def score(result, clouds, tree, cap=2.0):
    d_all = []
    for i, xyz, ref in clouds:
        T = prior_guess(result[i], ref)
        pts = xyz @ T[:3, :3].T + T[:3, 3]
        d, _ = tree.query(pts, distance_upper_bound=cap)
        d_all.append(np.minimum(d, cap))
    d = np.concatenate(d_all)
    return float(np.median(d)), float((d < 0.3).mean())


def main():
    p = argparse.ArgumentParser()
    p.add_argument("track", type=int)
    p.add_argument("files", nargs="*")
    p.add_argument("--data", default=os.path.join(os.path.dirname(ROOT), "data"))
    p.add_argument("--stride", type=int, default=10)
    p.add_argument("--validate", action="store_true")
    a = p.parse_intermixed_args()

    clouds = load_clouds(a.track, a.data, a.stride)
    m = read_pcd_binary(os.path.join(a.data, f"Track{a.track}", "map_voxel_0.3m.pcd"))
    tree = cKDTree(m)
    print(f"Track{a.track}: {len(clouds)} frames, {sum(len(c[1]) for c in clouds)} points above the road, "
          f"map {len(m)} points", flush=True)

    files = [(f, None) for f in a.files]
    if a.validate:
        sub_dir = os.path.join(ROOT, "docs", "nhat-ky", "submissions", f"track{a.track}")
        with open(os.path.join(ROOT, "docs", "nhat-ky", "data", "submission_stats.csv")) as f:
            for r in csv.DictReader(f):
                path = os.path.join(sub_dir, r["file"] + ".csv")
                if (r["track"] == str(a.track) and r["class"] in ("pipeline", "mixed") and r["score_exact"] == "1"
                        and float(r["score"]) < 3 and os.path.exists(path)):
                    files.append((path, float(r["score"])))
    rows = []
    for path, kaggle in files:
        res = np.loadtxt(path, delimiter=",", skiprows=1)[:, 1:4]
        med, in30 = score(res, clouds, tree)
        rows.append((os.path.basename(path), kaggle, med, in30))
        print(f"  {os.path.basename(path):40s} med {med:.4f} m  in30 {in30:6.2%}"
              + (f"  kaggle {kaggle:.5f}" if kaggle is not None else ""), flush=True)
    scored = [r for r in rows if r[1] is not None]
    if a.validate and len(scored) > 3:
        k = np.array([r[1] for r in scored])
        for j, name in ((2, "med"), (3, "in30")):
            rho = spearmanr(k, [r[j] for r in scored]).correlation
            print(f"Spearman(kaggle, {name}) = {rho:+.3f} over {len(scored)} files")


if __name__ == "__main__":
    main()
