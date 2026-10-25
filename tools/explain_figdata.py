"""Arrays for docs/report/make_explain_figs.py: what each step of the pipeline sees, on real frames (25/10).

Run in sdc-reg (needs scipy / rosbags):  python3 tools/explain_figdata.py
Writes docs/report/fig/explain_data/*.npz (camera images, map crops = competition data: NOT committed).
"""
import os
import sys

import numpy as np

sys.path.insert(0, "/w/midterm01/tools")
sys.path.insert(0, "/w/midterm01/src/localization/processing_codes")
from mcl_localize import above_road, build_field, field_score, ground_grid  # noqa: E402
from paint_bev import (Camera, FrameImages, MapPaint, PaintMatcher, SideCamera, bev, bev_grid, ground_frame,  # noqa: E402
                       load_mask, read_extrinsics)
from pc_io import read_ply_xyz, read_pcd_xyz  # noqa: E402

OUT = "/w/midterm01/docs/report/fig/explain_data"
R = "/w/midterm01/src/localization/result"
os.makedirs(OUT, exist_ok=True)
L = lambda p: np.loadtxt(p, delimiter=",", skiprows=1)  # noqa: E731


def save(name, **kw):
    np.savez_compressed(os.path.join(OUT, name), **kw)
    print("wrote", name, flush=True)


# ------------------------------------------------ 1. Track01 frame: two image clouds, GICP before / after on the map
K1 = 752
dbg = np.genfromtxt(f"{R}/reg/gicp_ground_Track1_debug.csv", delimiter=",", names=True)
row = dbg[dbg["idx"] == K1][0]
ci = np.load("/w/cache/Track1/raw_ply/index.npy")
cx = np.load("/w/cache/Track1/raw_ply/xyz.npy", mmap_mode="r")
crgb = np.load("/w/cache/Track1/raw_ply/rgb.npy", mmap_mode="r")
i0, n = int(ci[K1, 0]), int(ci[K1, 1])
raw = np.asarray(cx[i0:i0 + n], np.float32)
raw_rgb = np.asarray(crgb[i0:i0 + n])
names = sorted(os.listdir("/w/data/Track1/3cameras_ply/ply"))
c3 = read_ply_xyz(os.path.join("/w/data/Track1/3cameras_ply/ply", names[K1]))
m1 = read_pcd_xyz("/w/data/Track1/map_voxel_0.3m.pcd")
g = np.array([row["guess_x"], row["guess_y"]])
sel = np.hypot(m1[:, 0] - g[0], m1[:, 1] - g[1]) < 50
mm = m1[sel]
gx0, gy0, gz = ground_grid(mm, 1.0)
gi = np.clip(((mm[:, 0] - gx0)).astype(int), 0, gz.shape[1] - 1)
gj = np.clip(((mm[:, 1] - gy0)).astype(int), 0, gz.shape[0] - 1)
mh = mm[:, 2] - gz[gj, gi]
save("t1_clouds.npz", raw=raw, raw_rgb=raw_rgb, raw_h=ci[K1, 3], c3=c3[::3], scale=row["scale"], ground_h=row["ground_h"],
     guess=np.array([row["guess_x"], row["guess_y"], row["guess_yaw"]]),
     gicp=np.array([row["ndt_x"], row["ndt_y"], row["ndt_yaw"]]), map_xy=mm[:, :2], map_h=mh, k=K1)

# ------------------------------------------------ 2. Track03 CSM: likelihood field, cloud points, score along the road
m3 = np.load("/w/cache/Track3/map_corridor.npy")[:, :3].astype(np.float64)
field = build_field(m3, 0.4, 3.0, 0.2, 0.4, 0.1)
N, A2 = L(f"{R}/track3/t3_full_N.csv"), L(f"{R}/track3/t3_A2h.csv")
d = np.hypot(*(N[:, 1:3] - A2[:, 1:3]).T)
K3 = int(450 + np.argmin(np.abs(d[450:700] - 9.0)))
ti = np.load("/w/cache/Track3/raw_ply/index.npy")
tx = np.load("/w/cache/Track3/raw_ply/xyz.npy", mmap_mode="r")
h = np.median(ti[max(0, K3 - 56):K3 + 1, 3])
s = 1.646 / h
j0, nn = int(ti[K3, 0]), int(ti[K3, 1])
full = np.asarray(tx[j0:j0 + nn], np.float64) * s
csx, csy = above_road(full, 2.4, 1.646, 0.4, 3.0, 1.0, 20.0)
x0, y0, yaw = N[K3, 1], N[K3, 2], N[K3, 3]
yo = yaw + np.radians(0.66)
c, sn = np.cos(yaw), np.sin(yaw)
lever = np.array([-0.7 * c - 0.12 * sn, -0.7 * sn + 0.12 * c])
cy_, sy_ = np.cos(yo), np.sin(yo)
wx0, wy0 = cy_ * csx - sy_ * csy, sy_ * csx + cy_ * csy
da, dl = np.arange(-15, 15.01, 0.25), np.arange(-3, 3.01, 0.25)
GA, GL = np.meshgrid(da, dl, indexing="ij")
ox = x0 + lever[0] + GA.ravel() * c - GL.ravel() * sn
oy = y0 + lever[1] + GA.ravel() * sn + GL.ravel() * c
score = field_score(field, ox[:, None] + wx0[None, :], oy[:, None] + wy0[None, :]).reshape(GA.shape)
ib = np.unravel_index(np.argmax(score), score.shape)
best = np.array([ox.reshape(GA.shape)[ib], oy.reshape(GA.shape)[ib]])
rel = A2[K3, 1:3] - N[K3, 1:3]
pad = 35
xs0, ys0 = int((x0 - pad - field["x0"]) / 0.2), int((y0 - pad - field["y0"]) / 0.2)
crop = field["lf"][ys0:ys0 + int(2 * pad / 0.2), xs0:xs0 + int(2 * pad / 0.2)]
save("t3_csm.npz", lf=crop, extent=np.array([field["x0"] + xs0 * 0.2, field["x0"] + (xs0 + crop.shape[1]) * 0.2,
                                               field["y0"] + ys0 * 0.2, field["y0"] + (ys0 + crop.shape[0]) * 0.2]),
     pose=np.array([x0, y0, yaw]), pts_at_N=np.stack([x0 + lever[0] + wx0, y0 + lever[1] + wy0], 1),
     pts_at_best=np.stack([best[0] + wx0, best[1] + wy0], 1), score=score, da=da, dl=dl, best=best,
     a2h=A2[K3, 1:3], rel_along=np.array([rel @ [c, sn], rel @ [-sn, c]]), k=K3, scale=s)

# ------------------------------------------------ 3. Track03 paint matching, step by step (front camera) + IPM grid
C = "/w/cache_test"
mp = MapPaint.load(f"{C}/Track3/paint_map.npz")
paint = np.load(f"{C}/Track3/paint_th.npy")
fi = FrameImages(C, 3)
cam = Camera(3, data="/w/data", row0=fi.row0, rows=fi.rows, mask=load_mask(C, 3), pitch=1.0, height=1.646, yaw=-1.5)
Z = L(f"{R}/track3/t3_Z3a.csv")
Q = L(f"{R}/track3/t3_Q4.csv")
M = np.load(f"{C}/Track3/paint/meas_pass1.npz")
Ms = np.load(f"{C}/Track3/paint/meas_side_pass1.npz")
out = {}
for k in (390, 1100):
    x, y, yw = Z[k, 1:4]
    A_, L_ = bev_grid((5.0, 18.0), (-7.0, 7.0), 0.1)
    img = fi.get(k)
    ip = int(M["pitch_i"][k])
    pm = PaintMatcher(mp, paint, cam, along=(5.0, 18.0), lat=(-7.0, 7.0), s_along=0.1, s_lat=0.1, yaws=[0.0],
                      pitches=[M["pitches"][ip] - 1.0])
    cam.set_mount(cam.lx, cam.ly, cam.height, M["pitches"][ip], cam.roll, cam.yaw)
    grey, _ = bev(img, cam, mp, x, y, yw, A_, L_)
    cam.set_mount(cam.lx, cam.ly, cam.height, 1.0, cam.roll, cam.yaw)
    th, seen = pm.camera_paint(img, x, y, yw)[0]
    qx, qy, qyw = Q[k, 1] + 0.15 * np.cos(Q[k, 3]), Q[k, 2] + 0.15 * np.sin(Q[k, 3]), Q[k, 3]
    cw, sw = np.cos(yw), np.sin(yw)
    W = lambda px, py, pyw: (px + A_ * np.cos(pyw) - L_ * np.sin(pyw), py + A_ * np.sin(pyw) + L_ * np.cos(pyw))  # noqa: E731
    inten = mp.sample(*W(x, y, yw))
    mpaint = mp.sample(*W(x, y, yw), paint)
    iy0 = int(np.argmin(np.abs(M["yaws"])))
    vol = M["vol"][k][iy0].astype(np.float32)
    vols = Ms["vol_side"][k][iy0].astype(np.float32)
    # IPM grid: road points every 1 m (5..18 m ahead, +-6 m), projected into the image
    ga, gl = np.meshgrid(np.arange(5, 18.1, 1.0), np.arange(-6, 6.1, 1.0), indexing="ij")
    Pv = np.stack([ga.ravel(), gl.ravel(), np.zeros(ga.size)], 1)
    u, v, ok = cam.project(Pv)
    dqa = (qx - x) * cw + (qy - y) * sw
    dql = -(qx - x) * sw + (qy - y) * cw
    out.update({f"img{k}": img.astype(np.uint8), f"grey{k}": grey, f"th{k}": th, f"seen{k}": seen, f"inten{k}": inten,
                f"mpaint{k}": mpaint, f"vol{k}": vol, f"vols{k}": vols, f"u{k}": u, f"v{k}": v, f"ok{k}": ok,
                f"ga{k}": ga.ravel(), f"gl{k}": gl.ravel(), f"q{k}": np.array([dqa, dql])})
mask = load_mask(C, 3)
out["mask"] = mask[fi.row0:fi.row0 + fi.rows]
out["na"], out["nl"], out["res"] = int(M["na"]), int(M["nl"]), float(M["res"])
# side cameras at frame 1100
ex = read_extrinsics(3, "/w/data")
for cn in ("fl", "fr"):
    f = FrameImages(C, 3, cn)
    out[f"img_{cn}"] = f.get(1100).astype(np.uint8)
save("t3_paint_steps.npz", **out)

# ------------------------------------------------ 4. along NCC profiles: a dash, the red light, the flat final stop
prof = {}
iy0 = int(np.argmin(np.abs(M["yaws"])))
pr = M["prior"]


def lat_index(k):
    qx, qy = Q[k, 1] + 0.15 * np.cos(Q[k, 3]), Q[k, 2] + 0.15 * np.sin(Q[k, 3])
    cw, sw = np.cos(pr[k, 3]), np.sin(pr[k, 3])
    return int(np.clip(round((-(qx - pr[k, 1]) * sw + (qy - pr[k, 2]) * cw) / 0.1) + int(M["nl"]), 0, 2 * int(M["nl"])))


con = np.full(len(Q), -1.0)
for k in range(20, 940):
    if M["vol"][k].max() > -0.5:
        pf = M["vol"][k][iy0][:, lat_index(k)].astype(np.float32)
        con[k] = float(pf.max() - np.median(pf))
kbest = int(np.argmax(con))
prof["kbest"] = np.array([kbest])
print("sharpest along profile while driving: frame", kbest, con[kbest])
for k in (kbest, 390, 1100, 3050):
    qx, qy = Q[k, 1] + 0.15 * np.cos(Q[k, 3]), Q[k, 2] + 0.15 * np.sin(Q[k, 3])
    pr = M["prior"]
    cw, sw = np.cos(pr[k, 3]), np.sin(pr[k, 3])
    il = int(round((-(qx - pr[k, 1]) * sw + (qy - pr[k, 2]) * cw) / 0.1)) + int(M["nl"])
    iy0 = int(np.argmin(np.abs(M["yaws"])))
    prof[f"f{k}"] = M["vol"][k][iy0][:, il].astype(np.float32)
    prof[f"s{k}"] = Ms["vol_side"][k][iy0][:, il].astype(np.float32)
    prof[f"q{k}"] = np.array([((qx - pr[k, 1]) * cw + (qy - pr[k, 2]) * sw)])
save("t3_profiles.npz", **prof)

# ------------------------------------------------ 5. IMU: standstill test at the restart; GNSS yaw at the Track02 start
sys.path.insert(0, "/w/midterm01/tools")
from track_localize import read_imu_acc, read_gyro_up  # noqa: E402
it, acc = read_imu_acc("/w/data/Track3")
ft = np.loadtxt(f"{C}/Track3/img/f.h265.ts", delimiter=",", dtype=np.int64)[:, 1] * 1e-9
save("t3_imu.npz", t=it, acc=acc, ft=ft)
from gnss_to_csv import read_gnss  # noqa: E402
gt, gxx, gyy, gyaw = read_gnss("/w/data/Track2/Track2.db3")
t2, w2 = read_gyro_up("/w/data/Track2", up_fixed=(0, 0, 1))
t2i, acc2 = read_imu_acc("/w/data/Track2")
save("t2_gnss.npz", gt=gt, gx=gxx, gy=gyy, gyaw=gyaw, it=t2, wz=w2)
print("done")
