"""Offline scan matching of the image point clouds against the LiDAR map with small_gicp (ICP / GICP / VGICP).

Two ways to start each frame:
  --init-run TAG    start from the NDT pose of an earlier C++ run (NDT -> GICP/VGICP refinement); only the frames
                    that run matched are processed. Needs src/localization/result/TAG_TrackN_{debug.csv,result.txt}.
  --prior CSV       start from the prior x, y, yaw (z / roll / pitch taken from --pose-source, a C++ result.txt).

The output is a debug CSV in the same format as the C++ node (guess = prior-based start, ndt_* = refined pose),
so it goes through processing_codes/fuse_to_csv.py exactly like the NDT runs. Extra columns: init_* (the start
pose actually used), error, inliers, inlier_ratio, scale, ground_h, and info_xx / info_xy / info_yy: the GICP
Hessian reduced to the world x, y position (Schur complement over rotation and z), i.e. how firmly the scan pins
the position in each direction (a long straight road gives little along-track information).

--method PLANAR is a robust point-to-plane ICP that only moves x, y and yaw (z, roll, pitch stay at the start pose):
only map points on vertical surfaces (walls, poles, trunks: horizontal normal) are used, since the road gives no
x / y information, and a Geman-McClure kernel (--kernel) down-weights the badly estimated image points.

Point cloud preprocessing (TA suggestions: noise handling, front-hood mask):
  --hood-mask      drop points that project into the front-hood mask of the front camera (fisheye model, camera_info)
  --sor K,STD      statistical outlier removal: drop points whose mean distance to their K neighbours is more than
                   STD standard deviations above the average (as PCL StatisticalOutlierRemoval), on a 0.2 m voxel cloud
  --no-ground M    drop points within M metres of the road plane (measured per frame)

--ground-height H replaces the fixed --scale by a per-frame scale H / h, where h is the road height below the camera
measured in the unscaled cloud (tools/ground_scale.py) and median-filtered over --ground-window processed frames.

Run inside the sdc-reg image (docker/reg/Dockerfile), e.g.
  python3 tools/gicp_refine.py 1 --init-run c3s08 --scale 0.8 --method VGICP --out result/vgicp_s08_Track1_debug.csv
"""
import argparse
import csv
import os
import sys
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
        count, props, fmt = 0, [], "binary_little_endian"
        while True:
            line = f.readline().decode("ascii", "replace").strip()
            if line.startswith("format"):
                fmt = line.split()[1]
            elif line.startswith("element vertex"):
                count = int(line.split()[-1])
            elif line.startswith("property"):
                props.append(line.split())
            elif line == "end_header":
                break
        if fmt == "ascii":  # raw_ply (LoGeR)
            xyz = np.loadtxt(f, max_rows=count, usecols=(0, 1, 2), dtype=np.float64)
            return xyz[np.isfinite(xyz).all(axis=1)]
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


def frame_list(track_dir, ply="3cameras_ply"):
    if ply == "raw_ply":  # files named <timestamp_ns>.ply, one per frame in time order
        names = sorted(f for f in os.listdir(os.path.join(track_dir, "raw_ply")) if f.endswith(".ply"))
        return [(i, int(n.split(".")[0].split("_")[-1]), os.path.join(track_dir, "raw_ply", n))
                for i, n in enumerate(names)]
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


def read_yaml_list(path, key):
    """`data: [...]` list that follows `key:` in a camera_info yaml (no yaml dependency)."""
    lines = open(path).read().splitlines()
    k = next(i for i, l in enumerate(lines) if l.startswith(key + ":"))
    row = next(l for l in lines[k:] if "data:" in l)
    return np.array([float(v) for v in row.split("[")[1].split("]")[0].split(",")])


def load_hood(track_dir, track):
    cam = os.path.join(track_dir, f"Track{track}_images", "camera_info")
    K = read_yaml_list(os.path.join(cam, "gige_100_f_hdr_camera_info.yaml"), "camera_matrix")
    D = read_yaml_list(os.path.join(cam, "gige_100_f_hdr_camera_info.yaml"), "distortion_coefficients")
    return np.load(os.path.join(cam, "hood_mask.npy")), (K[0], K[4], K[2], K[5]), D


def in_hood(xyz, hood):
    """Points (front camera FLU) whose fisheye projection falls in the white (hood) part of the mask."""
    mask, (fx, fy, cx, cy), D = hood
    X, Y, Z = -xyz[:, 1], -xyz[:, 2], xyz[:, 0]
    front = Z > 1e-3
    a = np.where(front, X / np.where(front, Z, 1), 0)
    b = np.where(front, Y / np.where(front, Z, 1), 0)
    r = np.hypot(a, b)
    th = np.arctan(r)
    thd = th * (1 + D[0] * th ** 2 + D[1] * th ** 4 + D[2] * th ** 6 + D[3] * th ** 8)
    k = np.where(r > 1e-9, thd / np.maximum(r, 1e-9), 1.0)
    u, v = fx * k * a + cx, fy * k * b + cy
    h, w = mask.shape
    ok = front & (u >= 0) & (u < w) & (v >= 0) & (v < h)
    out = np.zeros(len(xyz), bool)
    out[ok] = mask[v[ok].astype(int), u[ok].astype(int)]
    return out


def statistical_outliers(xyz, k, std):
    from scipy.spatial import cKDTree
    d, _ = cKDTree(xyz).query(xyz, k=k + 1)
    mean_d = d[:, 1:].mean(axis=1)
    return mean_d > mean_d.mean() + std * mean_d.std()


def source_cloud(path, scale, max_range, voxel, opts=None):
    xyz = read_ply_xyz(path)
    opts = opts or {}
    if opts.get("hood") is not None:
        xyz = xyz[~in_hood(xyz, opts["hood"])]
    xyz = xyz[np.linalg.norm(xyz, axis=1) <= max_range / scale] * scale
    if opts.get("sor"):
        k, std = opts["sor"]
        xyz = np.asarray(small_gicp.voxelgrid_sampling(xyz, 0.2).points())[:, :3]
        xyz = xyz[~statistical_outliers(xyz, int(k), std)]
    if opts.get("no_ground"):
        xyz = xyz[xyz[:, 2] > -ground_height(xyz) + opts["no_ground"]]
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


def xy_information(H, R):
    """small_gicp Hessian (perturbation [rot, trans] on the right, i.e. in the source frame) -> 2x2 information of
    the world x, y position, with rotation and z marginalised out. Returns (xx, xy, yy)."""
    J = np.zeros((6, 6))  # world translation delta = R @ local translation delta
    J[:3, :3] = np.eye(3)
    J[3:, 3:] = R.T
    Hw = J.T @ H @ J  # Hessian in [rot, world trans]
    keep, rest = [3, 4], [0, 1, 2, 5]
    S = Hw[np.ix_(keep, keep)] - Hw[np.ix_(keep, rest)] @ np.linalg.pinv(Hw[np.ix_(rest, rest)]) @ Hw[np.ix_(rest, keep)]
    return S[0, 0], S[0, 1], S[1, 1]


def register(job):
    idx, ts, path, init_T, guess_T, prior, scale, ground_h = job
    a = G["args"]
    o = G["origin"]
    src = source_cloud(path, scale, a.max_range, a.voxel, G["opts"])
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
    info = xy_information(np.array(res.H), T[:3, :3]) if hasattr(res, "H") else np.full(3, np.nan)
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
        "info_xx": info[0], "info_xy": info[1], "info_yy": info[2],
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
    p.add_argument("--ground-causal", action="store_true", help="trailing (causal) median of the road height")
    p.add_argument("--hood-mask", action="store_true")
    p.add_argument("--sor", help="K,STD statistical outlier removal")
    p.add_argument("--no-ground", type=float, default=0.0)
    p.add_argument("--ply", default="3cameras_ply", help="3cameras_ply (MapAnything) or raw_ply (LoGeR)")
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
    frames = frame_list(track_dir, a.ply)
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
        if not a.prior or not os.path.exists(a.prior):
            sys.exit(f"--prior missing or not found: {a.prior}")
        if not a.pose_source:
            sys.exit("--pose-source is required with --prior (C++ run tag such as c3s08 / c3s10T2, or a *_result.txt)")
        prior = np.loadtxt(a.prior, delimiter=",", skiprows=1)[:, 1:4]
        if len(prior) != len(frames):
            sys.exit(f"--prior has {len(prior)} rows but Track{a.track} has {len(frames)} frames (wrong track?)")
        if a.pose_source.endswith(".txt"):
            if not os.path.exists(a.pose_source):
                sys.exit(f"--pose-source file not found: {a.pose_source}")
            ref = load_result_txt(a.pose_source)
        else:
            ref = load_run_poses(a.pose_source, a.track)
            if not ref:
                sys.exit(f"--pose-source {a.pose_source}: no {a.pose_source}_Track{a.track}_result.txt or chunks in {RESULT}")
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
        if a.ground_causal:  # rule 10/22: trailing median over the current and past frames only
            hs = np.array([np.median(h[max(0, k - a.ground_window + 1):k + 1]) for k in range(len(h))])
        else:
            hs = median_filter(h, size=a.ground_window, mode="nearest")
        scales = a.ground_height / hs
        print(f"ground h median {np.median(h):.3f} (smoothed range {hs.min():.3f}..{hs.max():.3f}); "
              f"scale median {np.median(scales):.3f} range {scales.min():.3f}..{scales.max():.3f}", flush=True)
        jobs = [j + (float(sc), float(hh)) for j, sc, hh in zip(jobs, scales, h)]
    else:
        jobs = [j + (a.scale, float("nan")) for j in jobs]

    t0 = time.time()
    map_path = os.path.join(track_dir, a.map)
    if not os.path.exists(map_path):
        sys.exit(f"map not found: {map_path} (build it with tools/map_voxel.py)")
    map_xyz = read_pcd_binary(map_path)
    # The start height must lie near this map's ground: a pose source of the other track (e.g. c3s10 instead of
    # c3s10T2 on Track02) gives a z ~90 m off and GICP then silently returns the prior unchanged.
    z0 = jobs[0][4][2, 3]
    near = map_xyz[np.linalg.norm(map_xyz[:, :2] - jobs[0][4][:2, 3], axis=1) < 30]
    if len(near) and abs(z0 - np.median(near[:, 2])) > 20:
        sys.exit(f"start height z = {z0:.1f} m but the map around the first pose is at ~{np.median(near[:, 2]):.1f} m: "
                 f"the pose source belongs to another track?")
    origin = np.round(map_xyz.mean(axis=0))
    target, tree, vmap = build_target(map_xyz - origin, a.method, a.map_res, a.workers)
    opts = {"hood": load_hood(track_dir, a.track) if a.hood_mask else None,
            "sor": tuple(float(v) for v in a.sor.split(",")) if a.sor else None,
            "no_ground": a.no_ground}
    G.update(args=a, origin=origin, target=target, tree=tree, vmap=vmap, opts=opts)
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
