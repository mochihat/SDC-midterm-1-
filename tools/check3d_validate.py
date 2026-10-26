"""Bước kiểm tra 3D (26/10, 4): phép đo "vật cao trong bản đồ ↔ cạnh trong ảnh" có đo đúng sai số dọc đường không?

Trên Track01 (có quỹ đạo gần đáp án): đặt pose = GNSS nội suy (gnss_1.csv, sai ~0.9 m), tìm độ dời dọc δ làm điểm khớp
cạnh lớn nhất (như tools/check3d_shift.py), rồi so với sai số dọc thật của GNSS, ước lượng bằng lb_t1_r5.csv
(file tốt nhất, điểm 0.36; chỉ dùng làm thước để KIỂM TRA phép đo, không dùng cho bài nộp).
Nếu δ ≈ sai số thật thì phép đo 3D đáng tin.

Chạy trong sdc-reg:  python3 tools/check3d_validate.py [STEP]
"""
import sys

import numpy as np

sys.path.insert(0, "/w/midterm01/tools")
from paint_bev import Camera, FrameImages, load_mask  # noqa: E402
from pc_io import read_pcd_xyz  # noqa: E402

STEP = int(sys.argv[1]) if len(sys.argv) > 1 else 25
G = np.loadtxt("/w/midterm01/docs/nhat-ky/submissions/track1/gnss_1.csv", delimiter=",", skiprows=1)
REF = np.loadtxt("/w/midterm01/src/localization/result/reg/lb/lb_t1_r5.csv", delimiter=",", skiprows=1)
m = read_pcd_xyz("/w/data/Track1/map_voxel_0.3m.pcd")
fi = FrameImages("/w/cache", 1)
cam = Camera(1, data="/w/data", row0=fi.row0, rows=fi.rows, mask=load_mask("/w/cache", 1), pitch=1.0, height=1.646, yaw=-1.5)
shifts = np.arange(-3.0, 3.01, 0.1)
rows = []
for k in range(30, len(G) - 5, STEP):
    px, py, yaw = G[k, 1:4]
    c, s = np.cos(yaw), np.sin(yaw)
    near = m[(np.abs(m[:, 0] - px) < 30) & (np.abs(m[:, 1] - py) < 30)]
    g = near[np.hypot(near[:, 0] - px, near[:, 1] - py) < 6]
    if len(g) < 20:
        continue
    z_road = float(np.percentile(g[:, 2], 5))
    a = (near[:, 0] - px) * c + (near[:, 1] - py) * s
    l = -(near[:, 0] - px) * s + (near[:, 1] - py) * c
    zr = near[:, 2] - z_road
    sel = (a > 5) & (a < 18) & (np.abs(l) < 7) & (np.abs(l) > 1.0) & (zr > 0.4) & (zr < 3.0)
    if sel.sum() < 100:
        continue
    img = fi.get(k)
    if img is None:
        continue
    gy, gx = np.gradient(img)
    edge = np.hypot(gx, gy)
    sc = []
    for d in shifts:
        u, v, ok = cam.project(np.stack([a[sel] + d, l[sel], zr[sel]], 1))
        if ok.sum() < 50:
            sc.append(np.nan)
            continue
        ui = np.clip(np.round(u[ok]).astype(int), 0, edge.shape[1] - 1)
        vi = np.clip(np.round(v[ok]).astype(int), 0, edge.shape[0] - 1)
        sc.append(float(edge[vi, ui].mean()))
    sc = np.array(sc)
    if np.all(np.isnan(sc)):
        continue
    best = float(shifts[np.nanargmax(sc)])
    # sai số dọc thật của GNSS (dời cần thiết để tới REF, theo hướng xe)
    true = float((REF[k, 1] - px) * c + (REF[k, 2] - py) * s)
    contrast = float(np.nanmax(sc) - np.nanmedian(sc))
    rows.append((k, best, true, contrast))
r = np.array(rows)
d = r[:, 1] - r[:, 2]
print(f"Track01: {len(r)} frame. δ đo được so với sai số dọc thật:")
print(f"  tương quan = {np.corrcoef(r[:, 1], r[:, 2])[0, 1]:+.2f}")
print(f"  |δ − thật| trung vị = {np.median(np.abs(d)):.2f} m; lệch TB = {d.mean():+.2f} m")
print(f"  sai số dọc thật của GNSS: trung vị |.| = {np.median(np.abs(r[:, 2])):.2f} m (để so: dùng 3D phải nhỏ hơn con số này)")
for q in (0.25, 0.5, 0.75):
    thr = np.quantile(r[:, 3], q)
    s_ = r[:, 3] >= thr
    print(f"  chỉ frame có đỉnh rõ (độ nổi ≥ phân vị {int(q * 100)}): n={s_.sum()}, "
          f"|δ − thật| trung vị = {np.median(np.abs(d[s_])):.2f} m, tương quan = {np.corrcoef(r[s_, 1], r[s_, 2])[0, 1]:+.2f}")
np.save("/w/midterm01/docs/report/fig/check3d/validate_t1.npy", r)
