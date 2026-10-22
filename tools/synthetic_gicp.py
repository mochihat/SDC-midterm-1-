"""T2 – "perfect point cloud" test: is the remaining error from the AI-built point clouds or from the matcher?

For N frames spread over a track, a synthetic source cloud is cut from the LiDAR map itself around a known pose
(the prior pose = "truth" for this test): points in the 3-camera field of view (azimuth --fov-min..--fov-max in the
vehicle frame, range <= --max-range), a simple visibility test (per 1 x 1 degree azimuth/elevation cell keep only points
within 1 m of the nearest one), then resampled so its range histogram matches the real 3cameras_ply cloud of that frame.
It is brought into the vehicle frame and registered with exactly the pipeline's GICP set-up (map voxel 0.3 m,
source voxel 0.5 m, 20 neighbours, max correspondence 1 m, 100 iterations).

(a) matcher only: start offset by (--init-along, --init-lateral, --init-yaw) from the truth -> residual pose error.
(b) simulated input errors, started from the truth: global scale (x1.03, x1.05, x0.97), depth noise sigma = k*d,
    range-dependent depth bias d' = d (1 + beta d), camera origin offset 0.3 m -> the bias they create.
(c) the real 3cameras_ply clouds of the same frames (pass 1 of the pipeline, from the debug CSV) for comparison.
Reported in the vehicle frame: mean (bias) and RMS of the along-track / lateral error, yaw error, % converged.

Usage: python3 tools/synthetic_gicp.py TRACK --prior PRIOR.csv --pose-source c3s08 --real-debug DEBUG.csv
                                      [--frames 200] [--workers 10] [--out-csv docs/nhat-ky/data/t2_synthetic.csv]
"""
import argparse
import csv
import os
import sys
from multiprocessing import Pool

import numpy as np
import small_gicp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gicp_refine import (build_target, frame_list, load_run_poses, prior_guess, read_pcd_binary,  # noqa: E402
                         read_ply_xyz, rot_z, yaw_of)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = {}

CASES = [  # name, kind, value
    ("a: matcher only, offset start", "init", None),
    ("b: scale x1.03", "scale", 1.03),
    ("b: scale x1.05", "scale", 1.05),
    ("b: scale x0.97", "scale", 0.97),
    ("b: depth noise 2% of range", "noise", 0.02),
    ("b: depth noise 5% of range", "noise", 0.05),
    ("b: depth bias +0.2%/m (5% at 25 m)", "beta", 0.002),
    ("b: camera origin 0.3 m forward", "origin_x", 0.3),
    ("b: camera origin 0.3 m left", "origin_y", 0.3),
    ("0: perfect cloud, true start", "none", None),
]


def visible(local, cell_deg=1.0, slack=1.0):
    """Keep, per azimuth/elevation cell, the points within `slack` m of the nearest one (crude occlusion)."""
    r = np.linalg.norm(local, axis=1)
    az = np.floor(np.degrees(np.arctan2(local[:, 1], local[:, 0])) / cell_deg).astype(np.int64)
    el = np.floor(np.degrees(np.arcsin(np.clip(local[:, 2] / np.maximum(r, 1e-6), -1, 1))) / cell_deg).astype(np.int64)
    key = (az + 1000) * 4000 + (el + 2000)
    order = np.lexsort((r, key))
    k, rr = key[order], r[order]
    first = np.r_[True, k[1:] != k[:-1]]
    rmin = np.maximum.accumulate(np.where(first, rr, -np.inf))  # nearest range of each cell, carried along the run
    keep = np.zeros(len(r), bool)
    keep[order] = rr <= rmin + slack
    return keep


def synthetic_cloud(job):
    i, T, real_path = job
    a = G["args"]
    m = G["map"]
    near = m[np.linalg.norm(m[:, :2] - T[:2, 3], axis=1) <= a.max_range + 5]
    local = (near - T[:3, 3]) @ T[:3, :3]
    r = np.linalg.norm(local, axis=1)
    az = np.degrees(np.arctan2(local[:, 1], local[:, 0]))
    sel = (r <= a.max_range) & (az >= a.fov_min) & (az <= a.fov_max) & (r > 1.0)
    local = local[sel]
    local = local[visible(local)]
    # match the range histogram of the real cloud of this frame
    real = read_ply_xyz(real_path) * G["scale"].get(i, 0.8)
    real = real[np.linalg.norm(real, axis=1) <= a.max_range]
    bins = np.arange(0, a.max_range + 2, 2.0)
    h_real, _ = np.histogram(np.linalg.norm(real, axis=1), bins)
    rl = np.linalg.norm(local, axis=1)
    h_syn, _ = np.histogram(rl, bins)
    want = h_real / max(h_real.sum(), 1)
    have = h_syn / max(h_syn.sum(), 1)
    w = np.where(have > 0, want / np.maximum(have, 1e-12), 0)[np.clip(np.digitize(rl, bins) - 1, 0, len(bins) - 2)]
    rng = np.random.default_rng(i)
    n = min(len(local), 60000)
    if w.sum() > 0 and len(local) > 0:
        local = local[rng.choice(len(local), n, replace=True, p=w / w.sum())]
    return local


def run_case(job):
    i, T, local, name, kind, value = job
    a = G["args"]
    rng = np.random.default_rng(1000 + i)
    pts = local.copy()
    r = np.linalg.norm(pts, axis=1, keepdims=True)
    if kind == "scale":
        pts = pts * value
    elif kind == "noise":
        pts = pts * (1 + rng.normal(0, value, (len(pts), 1)))
    elif kind == "beta":
        pts = pts * (1 + value * r)
    elif kind == "origin_x":
        pts = pts + np.array([value, 0, 0])
    elif kind == "origin_y":
        pts = pts + np.array([0, value, 0])
    src, _ = small_gicp.preprocess_points(pts, downsampling_resolution=0.5, num_neighbors=20, num_threads=1)
    init = T.copy()
    if kind == "init":
        init[:3, :3] = rot_z(np.radians(a.init_yaw)) @ T[:3, :3]
        init[:3, 3] = T[:3, 3] + T[:3, :3] @ np.array([a.init_along, a.init_lateral, 0])
    init[:3, 3] -= G["origin"]
    res = small_gicp.align(G["target"], src, G["tree"], init, registration_type="GICP",
                           max_correspondence_distance=1.0, max_iterations=100, num_threads=1)
    E = np.array(res.T_target_source)
    E[:3, 3] += G["origin"]
    d = E[:2, 3] - T[:2, 3]
    yaw = yaw_of(T)
    along = d[0] * np.cos(yaw) + d[1] * np.sin(yaw)
    lat = -d[0] * np.sin(yaw) + d[1] * np.cos(yaw)
    dyaw = np.degrees((yaw_of(E) - yaw + np.pi) % (2 * np.pi) - np.pi)
    return name, i, int(res.converged), along, lat, dyaw


def summarise(name, rows):
    rows = [r for r in rows if r[0] == name]
    ok = [r for r in rows if r[2] and abs(r[3]) < 2 and abs(r[4]) < 2]
    al = np.array([r[3] for r in ok])
    la = np.array([r[4] for r in ok])
    yw = np.array([r[5] for r in ok])
    return {"case": name, "frames": len(rows), "ok_pct": 100 * len(ok) / max(len(rows), 1),
            "along_mean": al.mean(), "along_rms": np.sqrt((al ** 2).mean()),
            "lat_mean": la.mean(), "lat_rms": np.sqrt((la ** 2).mean()),
            "yaw_mean": yw.mean(), "yaw_rms": np.sqrt((yw ** 2).mean())}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("track", type=int, choices=[1, 2])
    p.add_argument("--data", default=os.path.join(os.path.dirname(ROOT), "data"))
    p.add_argument("--prior", required=True, help="CSV idx,x,y,yaw used as the true pose")
    p.add_argument("--pose-source", required=True, help="C++ run tag giving z / roll / pitch (c3s08, c3s10T2)")
    p.add_argument("--real-debug", required=True, help="GICP debug CSV of the real clouds (pipeline pass 1)")
    p.add_argument("--frames", type=int, default=200)
    p.add_argument("--max-range", type=float, default=40.0)
    p.add_argument("--fov-min", type=float, default=-116.0)
    p.add_argument("--fov-max", type=float, default=97.0)
    p.add_argument("--init-along", type=float, default=0.5)
    p.add_argument("--init-lateral", type=float, default=0.3)
    p.add_argument("--init-yaw", type=float, default=2.0)
    p.add_argument("--workers", type=int, default=10)
    p.add_argument("--out-csv", default=os.path.join(ROOT, "docs", "nhat-ky", "data", "t2_synthetic.csv"))
    a = p.parse_args()
    for path in (a.prior, a.real_debug, os.path.join(a.data, f"Track{a.track}", "map_voxel_0.3m.pcd")):
        if not os.path.exists(path):
            sys.exit(f"missing input: {path}")

    track_dir = os.path.join(a.data, f"Track{a.track}")
    frames = frame_list(track_dir)
    prior = np.loadtxt(a.prior, delimiter=",", skiprows=1)[:, 1:4]
    poses = load_run_poses(a.pose_source, a.track)
    if not poses:
        sys.exit(f"no poses for run {a.pose_source} on Track{a.track}")
    keys = np.array(sorted(poses))
    with open(a.real_debug) as f:
        dbg = {int(r["idx"]): r for r in csv.DictReader(f)}
    sel = np.linspace(0, len(frames) - 1, a.frames).astype(int)
    truth = {i: prior_guess(prior[i], poses[int(keys[np.argmin(np.abs(keys - i))])]) for i in sel}

    m = read_pcd_binary(os.path.join(track_dir, "map_voxel_0.3m.pcd"))
    origin = np.round(m.mean(axis=0))
    target, tree, _ = build_target(m - origin, "GICP", 0.3, a.workers)
    G.update(args=a, map=m, origin=origin, target=target, tree=tree,
             scale={i: float(dbg[i]["scale"]) for i in sel if i in dbg})
    print(f"Track{a.track}: {len(sel)} frames, map {len(m)} points", flush=True)

    with Pool(a.workers) as pool:
        clouds = pool.map(synthetic_cloud, [(i, truth[i], frames[i][2]) for i in sel])
        print(f"synthetic clouds: median {int(np.median([len(c) for c in clouds]))} points", flush=True)
        jobs = [(i, truth[i], c, name, kind, val) for i, c in zip(sel, clouds) if len(c) > 100
                for name, kind, val in CASES]
        rows = pool.map(run_case, jobs, chunksize=4)

    out = [summarise(name, rows) for name, _, _ in CASES]
    # (c) real clouds, pass 1 of the pipeline, same frames: correction relative to the prior
    re = []
    for i in sel:
        r = dbg.get(i)
        if r is None:
            continue
        d = np.array([float(r["ndt_x"]) - prior[i, 0], float(r["ndt_y"]) - prior[i, 1]])
        y = prior[i, 2]
        al, la = d[0] * np.cos(y) + d[1] * np.sin(y), -d[0] * np.sin(y) + d[1] * np.cos(y)
        dy = np.degrees((float(r["ndt_yaw"]) - y + np.pi) % (2 * np.pi) - np.pi)
        re.append(("c: real 3cameras_ply (pass 1)", i, int(float(r["converged"])), al, la, dy))
    out.append(summarise("c: real 3cameras_ply (pass 1)", re))

    print(f"{'case':38s} {'ok%':>6s} {'along mean':>10s} {'along rms':>9s} {'lat mean':>9s} {'lat rms':>8s} "
          f"{'yaw mean':>8s} {'yaw rms':>8s}")
    for o in out:
        print(f"{o['case']:38s} {o['ok_pct']:6.1f} {o['along_mean']:+10.3f} {o['along_rms']:9.3f} {o['lat_mean']:+9.3f} "
              f"{o['lat_rms']:8.3f} {o['yaw_mean']:+8.2f} {o['yaw_rms']:8.2f}")
    print("(c) is the real correction against the GNSS prior: it contains the GNSS error as well as the matcher error.")
    os.makedirs(os.path.dirname(a.out_csv), exist_ok=True)
    with open(a.out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    with open(a.out_csv.replace(".csv", "_frames.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["case", "idx", "converged", "along", "lateral", "dyaw_deg"])
        w.writerows(rows + re)
    print(f"wrote {a.out_csv}")


if __name__ == "__main__":
    main()
