"""Data for the interactive walkthrough docs/report/sim/huong_dan_mo_phong.html (26/10).

Run in sdc-reg:  python3 tools/sim_export.py   -> docs/report/sim/sim_data.js (camera images + map crops = competition data,
NOT committed; the page needs it next to the html). Uses docs/report/fig/explain_data/*.npz (tools/explain_figdata.py).
"""
import base64
import io
import json
import os
import sys

import numpy as np
from scipy import ndimage

sys.path.insert(0, "/w/midterm01/tools")
from paint_bev import Camera, FrameImages, MapPaint, PaintMatcher, bev_grid, load_mask  # noqa: E402
from pc_io import read_pcd_xyz  # noqa: E402

REPO = "/w/midterm01"
R = f"{REPO}/src/localization/result"
EX = f"{REPO}/docs/report/fig/explain_data"
OUT = f"{REPO}/docs/report/sim"
os.makedirs(OUT, exist_ok=True)
L = lambda p: np.loadtxt(p, delimiter=",", skiprows=1)  # noqa: E731
rng = np.random.default_rng(0)
D = {}


def r(a, n=2):
    return np.round(np.asarray(a, dtype=float), n).tolist()


def u8(a, lo=None, hi=None):
    a = np.asarray(a, dtype=float)
    lo = np.nanmin(a) if lo is None else lo
    hi = np.nanmax(a) if hi is None else hi
    q = np.clip((np.nan_to_num(a, nan=lo) - lo) / max(hi - lo, 1e-9) * 255, 0, 255).astype(np.uint8)
    return {"w": int(a.shape[1]), "h": int(a.shape[0]), "lo": float(lo), "hi": float(hi),
            "b64": base64.b64encode(q.tobytes()).decode()}


IMGS = {}


def jpg(gray_or_rgb, width=720):
    """images are encoded on the host (no Pillow in sdc-reg): placeholder now, docs/report/sim/finish_sim.py later"""
    key = f"IMG{len(IMGS)}_{width}"
    IMGS[key] = np.asarray(gray_or_rgb).astype(np.uint8)
    return key


def sub(n, k):
    return np.sort(rng.choice(n, min(n, k), replace=False))


def dist_field(pts, x0, y0, size, res):
    n = int(size / res)
    occ = np.zeros((n, n), bool)
    ix = ((pts[:, 0] - x0) / res).astype(int)
    iy = ((pts[:, 1] - y0) / res).astype(int)
    ok = (ix >= 0) & (ix < n) & (iy >= 0) & (iy < n)
    occ[iy[ok], ix[ok]] = True
    d = ndimage.distance_transform_edt(~occ) * res
    return {"x0": x0, "y0": y0, "res": res, **u8(np.minimum(d, 2.55), 0, 2.55)}


# ---------------------------------------------------------------- 0/1. template drift + scale (Track01 frame 40)
G1 = L(f"{REPO}/docs/nhat-ky/submissions/track1/gnss_1.csv")
G2 = L(f"{REPO}/docs/nhat-ky/submissions/track2/gnss_2.csv")
B1 = np.loadtxt(f"{REPO}/docs/nhat-ky/data/baseline_partial/Track1_result.txt")
B2 = np.loadtxt(f"{REPO}/docs/nhat-ky/data/baseline_partial/Track2_result.txt")
m1 = read_pcd_xyz("/w/data/Track1/map_voxel_0.3m.pcd")
m2 = read_pcd_xyz("/w/data/Track2/map_voxel_0.3m.pcd")
for t, m, G, B in (("1", m1, G1, B1), ("2", m2, G2, B2)):
    lo, hi = G[:, 1:3].min(0) - 60, G[:, 1:3].max(0) + 60
    keep = np.all((m[:, :2] > lo) & (m[:, :2] < hi), 1)
    mm = m[keep]
    pick = sub(len(mm), 60000)
    D[f"map{t}"] = r(mm[pick, :2] - G[0, 1:3], 1)
    D[f"gnss{t}"] = r(G[:, 1:4] - [G[0, 1], G[0, 2], 0], 3)
    D[f"base{t}"] = r(np.stack([B[:, 3] - G[0, 1], B[:, 7] - G[0, 2]], 1), 2)
ci1 = np.load("/w/cache/Track1/raw_ply/index.npy")
cx1 = np.load("/w/cache/Track1/raw_ply/xyz.npy", mmap_mode="r")
K = 40
c40 = np.asarray(cx1[int(ci1[K, 0]):int(ci1[K, 0]) + int(ci1[K, 1])], np.float64)
h40 = float(np.median(ci1[max(0, K - 56):K + 1, 3]))
pk = sub(len(c40), 4000)
px, py, pyaw = G1[K, 1:4]
near = m1[np.hypot(m1[:, 0] - px, m1[:, 1] - py) < 60]
gx0, gy0 = px - 60, py - 60
D["scale"] = {"cloud": r(c40[pk], 4), "h": h40, "pose": r([px - G1[0, 1], py - G1[0, 2], pyaw], 4),
              "df": dist_field(near, gx0, gy0, 120, 0.25), "dfx0": gx0 - G1[0, 1], "dfy0": gy0 - G1[0, 2]}
D["scale"]["df"]["x0"] = gx0 - G1[0, 1]
D["scale"]["df"]["y0"] = gy0 - G1[0, 2]

# ---------------------------------------------------------------- NDT experiments: corrections at scale 3 vs 9, cell 8 vs 4 m
ndt = {}
for name, lab in (("e1s3_Track1", "Track01, tỉ lệ ×3, ô 8 m"), ("e1s3_Track2", "Track02, tỉ lệ ×3, ô 8 m"),
                  ("e2s9r8_Track2", "Track02, tỉ lệ ×9, ô 8 m"), ("e2s9r4_Track2", "Track02, tỉ lệ ×9, ô 4 m"),
                  ("e2s9r4_Track1", "Track01, tỉ lệ ×9, ô 4 m")):
    d = np.genfromtxt(f"{REPO}/docs/nhat-ky/data/ndt_debug/{name}_debug.csv", delimiter=",", names=True)
    d = d[d["converged"] > 0]
    dx, dy = d["ndt_x"] - d["guess_x"], d["ndt_y"] - d["guess_y"]
    c, s = np.cos(d["guess_yaw"]), np.sin(d["guess_yaw"])
    dyaw = np.degrees((d["ndt_yaw"] - d["guess_yaw"] + np.pi) % (2 * np.pi) - np.pi)
    ndt[name] = {"label": lab, "along": r(dx * c + dy * s), "lat": r(-dx * s + dy * c), "yaw": r(dyaw, 1)}
D["ndt"] = ndt
for t in ("1", "2"):
    I = L(f"{REPO}/docs/nhat-ky/data/image_only_test/imgtest_Track{t}.csv")
    G = G1 if t == "1" else G2
    D[f"imgonly{t}"] = r(I[:, 1:3] - G[0, 1:3], 2)

# ---------------------------------------------------------------- yaw GNSS Track02 start
g = np.load(f"{EX}/t2_gnss.npz")
gt = (g["gt"] - g["gt"][0]) * 1e-9
gxx, gyy, gyaw = g["gx"], g["gy"], np.degrees(g["gyaw"])
sp = np.r_[0, np.hypot(np.diff(gxx), np.diff(gyy)) / np.diff(gt)]
crs = np.full(len(gt), np.nan)
for i in range(4, len(gt)):
    dx, dy = gxx[i] - gxx[i - 4], gyy[i] - gyy[i - 4]
    if np.hypot(dx, dy) > 1.0:
        crs[i] = np.degrees(np.arctan2(dy, dx))
i4 = int(np.argmax(sp > 4.0))
it = (g["it"] - g["gt"][0]) * 1e-9
w = g["wz"] - np.radians(-0.293)
yg = np.degrees(np.cumsum(np.r_[0, w[1:] * np.diff(it)]))
yg += crs[i4 + 2] - np.interp(gt[i4 + 2], it, yg)
sel = gt < 40
tt = np.arange(0, 40, 0.1)
D["yawg"] = {"t": r(tt, 1), "gnss": r(np.interp(tt, gt, np.where(np.isfinite(gyaw), gyaw, 0)), 2),
             "gnss_step": r([gyaw[np.searchsorted(gt, x, side="right") - 1] for x in tt], 2),
             "course": [None if not np.isfinite(v) else round(float(v), 2) for v in np.interp(tt, gt[np.isfinite(crs)], crs[np.isfinite(crs)], left=np.nan)],
             "gyro": r(np.interp(tt, it, yg), 2), "x": r(np.interp(tt, gt, gxx - gxx[0]), 2), "y": r(np.interp(tt, gt, gyy - gyy[0]), 2),
             "v": r(np.interp(tt, gt, sp), 2), "t4": float(gt[i4])}

# ---------------------------------------------------------------- GICP Track01 frame 752
z1 = np.load(f"{EX}/t1_clouds.npz")
s = float(z1["scale"])
pts = z1["c3"] * s
keep = (np.hypot(pts[:, 0], pts[:, 1]) < 40) & (pts[:, 2] > -float(z1["ground_h"]) * s + 0.4)
P = pts[keep]
pk = sub(len(P), 7000)
mxy, mh = z1["map_xy"], z1["map_h"]
st = mxy[(mh > 0.4) & (mh < 3.0)]
gx, gy = z1["guess"][:2]
D["gicp"] = {"cloud": r(P[pk, :2], 2), "range": r(np.hypot(P[pk, 0], P[pk, 1]), 1), "guess": r(z1["guess"], 4),
             "gicp": r(z1["gicp"], 4), "map": r(st[sub(len(st), 30000)] - [gx, gy], 2),
             "df": dist_field(st - [gx, gy], -50.0, -50.0, 100, 0.2), "k": int(z1["k"])}

# ---------------------------------------------------------------- Track03 trajectories, segments, CSM
m3 = np.load("/w/cache/Track3/map_corridor.npy")
Q4, Z3a, N, A2h, PF2, X3f = (L(f"{R}/track3/{n}.csv") for n in ("t3_Q4", "t3_Z3a", "t3_full_N", "t3_A2h", "t3_PF2", "t3_X3f"))
o3 = Q4[0, 1:3]
D["map3"] = r(m3[sub(len(m3), 70000), :2] - o3, 1)
D["map3i"] = np.clip(m3[sub(len(m3), 70000)][:, 3], 0, 255).astype(int).tolist()[:0]
for n, X in (("Q4", Q4), ("Z3a", Z3a), ("N", N), ("A2h", A2h)):
    D[f"t3_{n}"] = r(X[::2, 1:4] - [o3[0], o3[1], 0], 2)
Zd = np.genfromtxt(f"{R}/track3/t3_Z3a_diag.csv", delimiter=",", names=True)
D["v3"] = r(Zd["v_imu"][::2], 2)
cz = np.load(f"{EX}/t3_csm.npz")
pose = cz["pose"]
c_, s_ = np.cos(pose[2]), np.sin(pose[2])
rel = cz["pts_at_N"] - pose[:2]
D["csm"] = {"lf": u8(np.exp(cz["lf"]), 0, 1), "ext": r(np.array(cz["extent"]) - [o3[0], o3[0], o3[1], o3[1]], 2),
            "pose": r([pose[0] - o3[0], pose[1] - o3[1], pose[2]], 4),
            "pts_body": r(np.stack([rel[:, 0] * c_ + rel[:, 1] * s_, -rel[:, 0] * s_ + rel[:, 1] * c_], 1), 2),
            "score": r(cz["score"], 3), "da": r(cz["da"]), "dl": r(cz["dl"]), "a2h_rel": r(cz["rel_along"]), "k": int(cz["k"])}

# ---------------------------------------------------------------- ZUPT at the restart
im = np.load(f"{EX}/t3_imu.npz")
t, acc, ft = im["t"], im["acc"], im["ft"]
b = acc[(t > ft[1500]) & (t < ft[2100]), 0].mean()
ks = np.arange(2120, 2340)
sd, mx = [], []
for k in ks:
    j0, j1 = np.searchsorted(t, ft[k] - 0.5), np.searchsorted(t, ft[k], side="right")
    sd.append(float(np.linalg.norm(acc[j0:j1].std(axis=0))))
    mx.append(float(acc[j0:j1, 0].mean() - b))
spd = lambda X: np.r_[0, np.hypot(*np.diff(X[:, 1:3], axis=0).T) / np.diff(ft)]  # noqa: E731
kern = np.ones(9) / 9
c3, s3 = np.cos(Z3a[:, 3]), np.sin(Z3a[:, 3])
gap = (X3f[:, 1] - Z3a[:, 1]) * c3 + (X3f[:, 2] - Z3a[:, 2]) * s3
D["zupt"] = {"k": ks.tolist(), "sd": r(sd, 3), "mx": r(mx, 3), "vx": r(np.convolve(spd(X3f), kern, "same")[ks], 2),
             "vz": r(np.convolve(spd(Z3a), kern, "same")[ks], 2), "vimu": r(Zd["v_imu"][ks], 2), "gap": r(gap[ks], 2),
             "x3f": r(X3f[ks, 1:3] - o3, 2), "z3a": r(Z3a[ks, 1:3] - o3, 2)}

# ---------------------------------------------------------------- paint: camera paint vs map paint, live NCC
C = "/w/cache_test"
mp = MapPaint.load(f"{C}/Track3/paint_map.npz")
paint = np.load(f"{C}/Track3/paint_th.npy")
fi = FrameImages(C, 3)
cam = Camera(3, data="/w/data", row0=fi.row0, rows=fi.rows, mask=load_mask(C, 3), pitch=1.0, height=1.646, yaw=-1.5)
M = np.load(f"{C}/Track3/paint/meas_pass1.npz")
pz = np.load(f"{EX}/t3_paint_steps.npz")
paintd = {}
for k in (390, 1100):
    x, y, yw = Z3a[k, 1:4]
    pm = PaintMatcher(mp, paint, cam, along=(5.0, 18.0), lat=(-7.0, 7.0), s_along=0.1, s_lat=0.1, yaws=[0.0],
                      pitches=[M["pitches"][int(M["pitch_i"][k])] - 1.0])
    th, seen = pm.camera_paint(fi.get(k), x, y, yw)[0]
    Ae, Le = bev_grid((3.0, 20.0), (-8.5, 8.5), 0.1)
    cw, sw = np.cos(yw), np.sin(yw)
    mpe = mp.sample(x + Ae * cw - Le * sw, y + Ae * sw + Le * cw, paint)
    th = np.where(seen, th / max(np.percentile(th[seen], 99.5), 1e-6), np.nan)
    paintd[str(k)] = {"cam": u8(np.clip(np.nan_to_num(th, nan=0), 0, 1), 0, 1), "seen": u8(seen.astype(float), 0, 1),
                      "map": u8(np.clip(np.nan_to_num(mpe), 0, 1), 0, 1), "vol": r(pz[f"vol{k}"], 3), "q": r(pz[f"q{k}"]),
                      "img": jpg(pz[f"img{k}"]), "u": r(pz[f"u{k}"][pz[f"ok{k}"]], 0), "v": r(pz[f"v{k}"][pz[f"ok{k}"]], 0),
                      "ga": r(pz[f"ga{k}"][pz[f"ok{k}"]], 0)}
paintd["fl"] = jpg(pz["img_fl"])
paintd["fr"] = jpg(pz["img_fr"])
D["paint"] = paintd

# ---------------------------------------------------------------- along NCC profiles per frame + positions
Ms = np.load(f"{C}/Track3/paint/meas_side_pass1.npz")
pr = M["prior"]
iy0 = int(np.argmin(np.abs(M["yaws"])))
nl = int(M["nl"])
prof = {"k": [], "f": [], "s": [], "q": [], "p": []}
for k in list(range(300, 951, 2)) + list(range(2800, 3142, 2)):
    cw, sw = np.cos(pr[k, 3]), np.sin(pr[k, 3])
    qx, qy = Q4[k, 1] + 0.15 * np.cos(Q4[k, 3]), Q4[k, 2] + 0.15 * np.sin(Q4[k, 3])
    fx, fy = PF2[k, 1] + 0.15 * np.cos(PF2[k, 3]), PF2[k, 2] + 0.15 * np.sin(PF2[k, 3])
    il = int(np.clip(round((-(qx - pr[k, 1]) * sw + (qy - pr[k, 2]) * cw) / 0.1) + nl, 0, 2 * nl))
    prof["k"].append(k)
    prof["f"].append(r(M["vol"][k][iy0][:, il], 2))
    prof["s"].append(r(Ms["vol_side"][k][iy0][:, il], 2))
    prof["q"].append(round(float((qx - pr[k, 1]) * cw + (qy - pr[k, 2]) * sw), 2))
    prof["p"].append(round(float((fx - pr[k, 1]) * cw + (fy - pr[k, 2]) * sw), 2))
D["prof"] = prof
spdf = np.genfromtxt(f"{REPO}/docs/report/fig/t3_speed.csv", delimiter=",", names=True, skip_header=1)
D["jit"] = {"t": r(spdf["t_s"], 2), "pf2": r(spdf["paint_only"], 1), "q4": r(spdf["paint_imu"], 1), "imu": r(spdf["imu_scaled"], 1)}

# ---------------------------------------------------------------- Track01 camera images
d1 = "/w/data/Track1/Track1_images"
D["cams1"] = {c: "FILE:" + os.path.join(d1, f"Track1_{c}_images", sorted(os.listdir(os.path.join(d1, f"Track1_{c}_images")))[752])
               for c in ("fl", "f", "fr")}
np.savez_compressed(f"{OUT}/sim_imgs.npz", **IMGS)

with open(f"{OUT}/sim_data.js", "w") as f:
    f.write("window.SIM=")
    json.dump(D, f, separators=(",", ":"))
    f.write(";\n")
print("wrote sim_data.js", os.path.getsize(f"{OUT}/sim_data.js") / 1e6, "MB")
