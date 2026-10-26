"""Bước kiểm tra 3D (26/10, 2): vật cao trong bản đồ có chốt được vị trí dọc đường không?

Dịch cụm điểm vật cao theo phương dọc đường (δ từ −3 đến +3 m), chiếu vào ảnh camera trước, và đo độ mạnh cạnh của ảnh
tại các điểm chiếu (cạnh = đạo hàm độ sáng). Nếu δ tốt nhất gần 0 và có đỉnh rõ thì cụm này chốt được vị trí dọc.
Bỏ dải gần ngang 0 (|ngang| < 1 m: nhiễu mặt đường, chưa chắc là vật cao).

Chạy trong sdc-reg:  python3 tools/check3d_shift.py FRAME
"""
import sys

import numpy as np

sys.path.insert(0, "/w/midterm01/tools")
from paint_bev import Camera, FrameImages, load_mask  # noqa: E402
from pc_io import read_pcd_xyz  # noqa: E402

K = int(sys.argv[1]) if len(sys.argv) > 1 else 1100
R = "/w/midterm01/src/localization/result/track3"
C = "/w/cache_test"
Z = np.loadtxt(f"{R}/t3_Z3a.csv", delimiter=",", skiprows=1)
px, py, yaw = Z[K, 1:4]
c, s = np.cos(yaw), np.sin(yaw)
m = read_pcd_xyz("/w/data/Track3/map_voxel_0.3m.pcd")
near = m[np.hypot(m[:, 0] - px, m[:, 1] - py) < 30]
g = near[np.hypot(near[:, 0] - px, near[:, 1] - py) < 6]
z_road = float(np.percentile(g[:, 2], 5))
a = (near[:, 0] - px) * c + (near[:, 1] - py) * s
l = -(near[:, 0] - px) * s + (near[:, 1] - py) * c
zr = near[:, 2] - z_road
sel = (a > 5) & (a < 18) & (np.abs(l) < 7) & (zr > 0.4) & (zr < 3.0) & (np.abs(l) > 1.0)
A, L, ZR = a[sel], l[sel], zr[sel]
print(f"frame {K}: {len(A)} điểm vật cao (đã bỏ |ngang| < 1 m)")

fi = FrameImages(C, 3)
img = fi.get(K)
gy, gx = np.gradient(img)
edge = np.hypot(gx, gy)
cam = Camera(3, data="/w/data", row0=fi.row0, rows=fi.rows, mask=load_mask(C, 3), pitch=1.0, height=1.646, yaw=-1.5)

shifts = np.arange(-3.0, 3.01, 0.1)
score = []
for d in shifts:
    P = np.stack([A + d, L, ZR], 1)  # cùng cụm, dời δ theo phương dọc đường
    u, v, ok = cam.project(P)
    if ok.sum() < 50:
        score.append(np.nan)
        continue
    ui = np.clip(np.round(u[ok]).astype(int), 0, edge.shape[1] - 1)
    vi = np.clip(np.round(v[ok]).astype(int), 0, edge.shape[0] - 1)
    score.append(float(edge[vi, ui].mean()))
score = np.array(score)
best = shifts[np.nanargmax(score)]
print(f"  δ tốt nhất = {best:+.1f} m (0 = bộ bám Z3a); cạnh TB tại δ=0: {score[np.argmin(np.abs(shifts)) ]:.2f}, "
      f"cực đại: {np.nanmax(score):.2f}")
print("  đường cong (δ, cạnh TB):")
for d, sc in zip(shifts[::5], score[::5]):
    print(f"   {d:+.1f}  {sc:.2f}")
np.savez_compressed("/w/midterm01/docs/report/fig/check3d/shift_%d.npz" % K, shifts=shifts, score=score, best=best)
