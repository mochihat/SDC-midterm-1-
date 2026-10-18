"""Offline scan matching of the image point clouds against the LiDAR map with small_gicp (ICP / GICP / VGICP).

Two ways to start each frame:
  --init-run TAG    start from the NDT pose of an earlier C++ run (NDT -> GICP/VGICP refinement); only the frames
                    that run matched are processed. Needs src/localization/result/TAG_TrackN_{debug.csv,result.txt}.
  --prior CSV       start from the prior x, y, yaw (z / roll / pitch taken from --pose-source, a C++ result.txt).

The output is a debug CSV in the same format as the C++ node (guess = prior-based start, ndt_* = refined pose),
so it goes through processing_codes/fuse_to_csv.py exactly like the NDT runs. Extra columns: init_* (the start
pose actually used), error, inliers, inlier_ratio, scale, ground_h.

--method PLANAR is a robust point-to-plane ICP that only moves x, y and yaw (z, roll, pitch stay at the start pose):
only map points on vertical surfaces (walls, poles, trunks: horizontal normal) are used, since the road gives no
x / y information, and a Geman-McClure kernel (--kernel) down-weights the badly estimated image points.

--ground-height H replaces the fixed --scale by a per-frame scale H / h, where h is the road height below the camera
measured in the unscaled cloud (tools/ground_scale.py) and median-filtered over --ground-window processed frames.

Run inside the sdc-reg image (docker/reg/Dockerfile), e.g.
  python3 tools/gicp_refine.py 1 --init-run c3s08 --scale 0.8 --method VGICP --out result/vgicp_s08_Track1_debug.csv
"""
import argparse
import csv
import os
import time
from multiprocessing import Pool

import numpy as np
import small_gicp
from scipy.ndimage import median_filter

from ground_scale import ground_height

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULT = os.path.join(ROOT, "src", "localization", "result")

G = {}  # per-process state (map, frames), filled before forking


def read_pcd_binary(path):
    with open(path, "rb") as f:
        header = {}
        while True:
            key, *vals = f.readline().decode().split()
            header[key] = vals
            if key == "DATA":
                break
        assert header["DATA"][0] == "binary" and header["FIELDS"] == ["x", "y", "z"], header
        n = int(header["POINTS"][0])
        return np.frombuffer(f.read(n * 12), dtype="<f4").reshape(n, 3).astype(np.float64)


def read_ply_xyz(path):
    with open(path, "rb") as f:
        count, props = 0, []
        while True:
            line = f.readline().decode("ascii", "replace").strip()
            if line.startswith("element vertex"):
                count = int(line.split()[-1])
            elif line.startswith("property"):
                props.append(line.split())
            elif line == "end_header":
                break
        types = {"float": "<f4", "double": "<f8", "uchar": "u1"}
        dtype = np.dtype([(p[2], types[p[1]]) for p in props])
        rec = np.frombuffer(f.read(count * dtype.itemsize), dtype=dtype, count=count)
    xyz = np.stack([rec["x"], rec["y"], rec["z"]], axis=1).astype(np.float64)
    return xyz[np.isfinite(xyz).all(axis=1)]


def yaw_of(T):
    return float(np.arctan2(T[1, 0], T[0, 0]))


def rot_z(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])


def prior_guess(prior_xyyaw, reference):
    """Same as LocalizationApp::PriorGuess: x, y, yaw from the prior; z, roll, pitch from `reference`."""
    T = reference.copy()
    T[:3, :3] = rot_z(prior_xyyaw[2] - yaw_of(reference)) @ reference[:3, :3]
    T[0, 3], T[1, 3] = prior_xyyaw[0], prior_xyyaw[1]
    return T


def load_result_txt(path):
    rows = np.loadtxt(path).reshape(-1, 3, 4)
    T = np.tile(np.eye(4), (len(rows), 1, 1))
    T[:, :3, :] = rows
    return T


def load_run_poses(tag, track):
    """4x4 pose per frame of a C++ run: the main result file plus chunk files (rows of chunk START are frames
    START, START+1, ...; later chunks win)."""
    import glob
    poses = {}
    main_file = os.path.join(RESULT, f"{tag}_Track{track}_result.txt")
    if os.path.exists(main_file):
        poses.update(enumerate(load_result_txt(main_file)))
    for path in sorted(glob.glob(os.path.join(RESULT, "chunks", f"{tag}_*_result.txt"))):
        start = int(os.path.basename(path)[len(tag) + 1:].split("_")[0])
        poses.update((start + k, T) for k, T in enumerate(load_result_txt(path)))
    return poses


def load_debug(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def frame_list(track_dir):
    with open(os.path.join(track_dir, "3cameras_ply", "index.csv")) as f:
        rows = list(csv.DictReader(f))
    return [(int(r["index"]), int(r["f_ts"]), os.path.join(track_dir, "3cameras_ply", r["ply"])) for r in rows]


def build_target(map_xyz, method, resolution, threads):
    pts, tree = small_gicp.preprocess_points(map_xyz, downsampling_resolution=resolution, num_neighbors=20,
                                             num_threads=threads)
    if method == "PLANAR":
        from scipy.spatial import cKDTree
        xyz = np.asarray(pts.points())[:, :3].copy()
        normals = np.asarray(pts.normals())[:, :3].copy()
        vertical = np.abs(normals[:, 2]) < 0.5  # surface normal close to horizontal = wall / pole
        return (xyz[vertical], normals[vertical], cKDTree(xyz[vertical])), None, None
    if method == "VGICP":
        vmap = small_gicp.GaussianVoxelMap(resolution * 2)
        vmap.insert(pts)
        return pts, tree, vmap
    return pts, tree, None


def source_cloud(path, scale, max_range, voxel):
    xyz = read_ply_xyz(path)
    xyz = xyz[np.linalg.norm(xyz, axis=1) <= max_range / scale] * scale
    pts, _ = small_gicp.preprocess_points(xyz, downsampling_resolution=voxel, num_neighbors=20, num_threads=1)
    return pts


def measure_ground(path):
    return ground_height(read_ply_xyz(path))


def planar_icp(target, src_xyz, T, max_corr, kernel, iterations):
    """Robust point-to-plane ICP over x, y, yaw only. Returns (T, converged, error, inliers)."""
    xyz, normals, kd = target
    T = T.copy()
    p_cam = src_xyz @ T[:3, :3].T + T[:3, 3]
    converged, err, n_in = False, 0.0, 0
    for _ in range(iterations):
        dist, j = kd.query(p_cam, distance_upper_bound=max_corr)
        ok = np.isfinite(dist)
        n_in = int(ok.sum())
        if n_in < 30:
            break
        p, q, n = p_cam[ok], xyz[j[ok]], normals[j[ok]]
        r = np.einsum("ij,ij->i", n, p - q)
        c = T[:3, 3]
        J = np.stack([n[:, 0], n[:, 1], -n[:, 0] * (p[:, 1] - c[1]) + n[:, 1] * (p[:, 0] - c[0])], axis=1)
        w = 1.0 / (1.0 + (r / kernel) ** 2) ** 2  # Geman-McClure
        H = (J * w[:, None]).T @ J + np.eye(3) * 1e-6
        dx, dy, dth = -np.linalg.solve(H, (J * w[:, None]).T @ r)
        cs, sn = np.cos(dth), np.sin(dth)
        Rz = np.array([[cs, -sn, 0], [sn, cs, 0], [0, 0, 1.0]])
        p_cam = (p_cam - c) @ Rz.T + c + np.array([dx, dy, 0])
        T[:3, :3] = Rz @ T[:3, :3]
        T[:3, 3] = c + np.array([dx, dy, 0])
        err = float(np.sum(w * r ** 2))
        if np.hypot(dx, dy) < 1e-3 and abs(dth) < 1e-4:
            converged = True
            break
    return T, converged, err, n_in


def register(job):
    idx, ts, path, init_T, guess_T, prior, scale, ground_h = job
    a = G["args"]
    o = G["origin"]
    src = source_cloud(path, scale, a.max_range, a.voxel)
    init_local = init_T.copy()
    init_local[:3, 3] -= o
    if a.method == "PLANAR":
        src_xyz = np.asarray(src.points())[:, :3]
        T, conv, err, n_in = planar_icp(G["target"], src_xyz, init_local, a.max_corr, a.kernel, a.iterations)

        class _R:  # same fields as small_gicp.RegistrationResult
            pass
        res = _R()
        res.T_target_source, res.converged, res.error, res.num_inliers = T, conv, err, n_in
    elif a.method == "VGICP":
        res = small_gicp.align(G["vmap"], src, init_local, max_correspondence_distance=a.max_corr,
                               max_iterations=a.iterations, num_threads=1)
    else:
        res = small_gicp.align(G["target"], src, G["tree"], init_local, registration_type=a.method,
                               max_correspondence_distance=a.max_corr, max_iterations=a.iterations, num_threads=1)
    T = np.array(res.T_target_source)
    T[:3, 3] += o
    n = src.size()
    return {
        "idx": idx, "timestamp_ns": ts, "converged": int(res.converged), "accepted": 1,
        "score": res.error / max(res.num_inliers, 1), "input_points": n,
        "prior_x": prior[0], "prior_y": prior[1], "prior_yaw": prior[2],
        "guess_x": guess_T[0, 3], "guess_y": guess_T[1, 3], "guess_z": guess_T[2, 3], "guess_yaw": yaw_of(guess_T),
        "ndt_x": T[0, 3], "ndt_y": T[1, 3], "ndt_z": T[2, 3], "ndt_yaw": yaw_of(T),
        "init_x": init_T[0, 3], "init_y": init_T[1, 3], "init_yaw": yaw_of(init_T),
        "error": res.error, "inliers": res.num_inliers, "inlier_ratio": res.num_inliers / max(n, 1),
        "scale": scale, "ground_h": ground_h,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("track", type=int)
    p.add_argument("--data", default=os.path.join(os.path.dirname(ROOT), "data"))
    p.add_argument("--init-run", help="C++ run tag whose NDT poses are the start (e.g. c3s08)")
    p.add_argument("--prior", help="prior CSV idx,x,y,yaw (start from it instead of NDT)")
    p.add_argument("--pose-source", help="C++ result.txt or run tag giving z / roll / pitch when starting from --prior")
    p.add_argument("--stride", type=int, default=4)
    p.add_argument("--start", type=int, default=0)
    p.add_argument("--count", type=int, default=0)
    p.add_argument("--scale", type=float, default=0.8)
    p.add_argument("--ground-height", type=float, help="per-frame scale = H / measured road height (see above)")
    p.add_argument("--ground-window", type=int, default=15)
    p.add_argument("--method", default="VGICP", choices=["ICP", "PLANE_ICP", "GICP", "VGICP", "PLANAR"])
    p.add_argument("--kernel", type=float, default=0.3, help="Geman-McClure scale (m) for --method PLANAR")
    p.add_argument("--map", default="map_downsampled_1m.pcd")
    p.add_argument("--map-res", type=float, default=0.5, help="target downsampling (VGICP voxel = 2x)")
    p.add_argument("--voxel", type=float, default=0.5, help="source downsampling")
    p.add_argument("--max-range", type=float, default=40.0)
    p.add_argument("--max-corr", type=float, default=1.0)
    p.add_argument("--iterations", type=int, default=100)
    p.add_argument("--workers", type=int, default=10)
    p.add_argument("--out", required=True)
    a = p.parse_args()

    track_dir = os.path.join(a.data, f"Track{a.track}")
    frames = frame_list(track_dir)
    jobs = []
    if a.init_run:
        dbg = load_debug(os.path.join(RESULT, f"{a.init_run}_Track{a.track}_debug.csv"))
        poses = load_run_poses(a.init_run, a.track)
        for r in dbg:
            i = int(r["idx"])
            guess = prior_guess([float(r["guess_x"]), float(r["guess_y"]), float(r["guess_yaw"])], poses[i])
            guess[2, 3] = float(r["guess_z"])
            jobs.append((i, frames[i][1], frames[i][2], poses[i], guess,
                         (float(r["prior_x"]), float(r["prior_y"]), float(r["prior_yaw"]))))
    else:
        prior = np.loadtxt(a.prior, delimiter=",", skiprows=1)[:, 1:4]
        ref = load_result_txt(a.pose_source) if a.pose_source.endswith(".txt") else load_run_poses(a.pose_source, a.track)
        keys = np.array(sorted(ref.keys())) if isinstance(ref, dict) else np.arange(len(ref))
        for i in range(a.start, len(frames), a.stride):
            near = int(keys[np.argmin(np.abs(keys - i))])  # a frame missing from the run: nearest one with a pose
            guess = prior_guess(prior[i], ref[near])
            jobs.append((i, frames[i][1], frames[i][2], guess, guess, tuple(prior[i])))
    if a.count:
        jobs = jobs[:a.count]

    if a.ground_height:
        with Pool(a.workers) as pool:
            h = np.array(pool.map(measure_ground, [j[2] for j in jobs], chunksize=8))
        hs = median_filter(h, size=a.ground_window, mode="nearest")
        scales = a.ground_height / hs
        print(f"ground h median {np.median(h):.3f} (smoothed range {hs.min():.3f}..{hs.max():.3f}); "
              f"scale median {np.median(scales):.3f} range {scales.min():.3f}..{scales.max():.3f}", flush=True)
        jobs = [j + (float(sc), float(hh)) for j, sc, hh in zip(jobs, scales, h)]
    else:
        jobs = [j + (a.scale, float("nan")) for j in jobs]

    t0 = time.time()
    map_xyz = read_pcd_binary(os.path.join(track_dir, a.map))
    origin = np.round(map_xyz.mean(axis=0))
    target, tree, vmap = build_target(map_xyz - origin, a.method, a.map_res, a.workers)
    G.update(args=a, origin=origin, target=target, tree=tree, vmap=vmap)
    n_target = len(target[0]) if isinstance(target, tuple) else target.size()
    print(f"map {len(map_xyz)} pts -> {n_target} (res {a.map_res}) in {time.time() - t0:.1f} s; "
          f"{len(jobs)} frames, {a.method}, scale {'ground' if a.ground_height else a.scale}", flush=True)

    t0 = time.time()
    with Pool(a.workers) as pool:
        rows = []
        for k, row in enumerate(pool.imap(register, jobs, chunksize=4)):
            rows.append(row)
            if (k + 1) % 100 == 0:
                print(f"  {k + 1}/{len(jobs)}  {(time.time() - t0) / (k + 1):.2f} s/frame", flush=True)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {a.out}: {len(rows)} frames in {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    main()
