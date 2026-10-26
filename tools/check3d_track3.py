"""Kiểm tra 3D (26/10): có vật cao trong bản đồ (cột, mép lề, tường) chiếu được vào ảnh camera trước ở chỗ không có vạch sơn
không, và chúng có nằm ở nhiều độ dời dọc đường để chốt vị trí dọc không?

Chạy trong sdc-reg:  python3 tools/check3d_track3.py FRAME
Ra: docs/report/fig/check3d/ (npz + png). Chỉ dùng pose của bộ bám Z3a (nhân quả) tại FRAME.
"""
import os
import sys

import numpy as np

sys.path.insert(0, "/w/midterm01/tools")
from paint_bev import Camera, FrameImages, load_mask  # noqa: E402
from pc_io import read_pcd_xyz  # noqa: E402

K = int(sys.argv[1]) if len(sys.argv) > 1 else 1100
R = "/w/midterm01/src/localization/result/track3"
C = "/w/cache_test"
OUT = "/w/midterm01/docs/report/fig/check3d"
os.makedirs(OUT, exist_ok=True)

Z = np.loadtxt(f"{R}/t3_Z3a.csv", delimiter=",", skiprows=1)
px, py, yaw = Z[K, 1:4]
c, s = np.cos(yaw), np.sin(yaw)
m = read_pcd_xyz("/w/data/Track3/map_voxel_0.3m.pcd")
d = m[:, :2] - [px, py]
near = m[np.hypot(d[:, 0], d[:, 1]) < 30]

# đất quanh xe: phân vị 5 % độ cao trong bán kính 6 m (cùng ý với t7_pose_source.py)
g = near[np.hypot(near[:, 0] - px, near[:, 1] - py) < 6]
z_road = float(np.percentile(g[:, 2], 5))
# vật cao = 0.4–3 m trên đường (trừ cột / tường / mép; mặt đường đã loại)
a = (near[:, 0] - px) * c + (near[:, 1] - py) * s
l = -(near[:, 0] - px) * s + (near[:, 1] - py) * c
zr = near[:, 2] - z_road
sel = (a > 5) & (a < 18) & (np.abs(l) < 7) & (zr > 0.4) & (zr < 3.0)
P = np.stack([a[sel], l[sel], zr[sel]], 1)
print(f"frame {K}: vật cao 0.4–3 m trong 5–18 m phía trước, |ngang|<7 m: {len(P)} điểm; mặt đường z = {z_road:.2f}")

# chiếu vào ảnh camera trước (cùng mô hình với bộ đo vạch sơn)
fi = FrameImages(C, 3)
cam = Camera(3, data="/w/data", row0=fi.row0, rows=fi.rows, mask=load_mask(C, 3), pitch=1.0, height=1.646, yaw=-1.5)
u, v, ok = cam.project(P)
print(f"  trong khung ảnh camera trước: {ok.sum()} điểm")

# đa dạng theo phương dọc: đếm điểm theo ô 1 m (cần ít nhất vài ô khác nhau để chốt vị trí dọc)
bins = np.arange(5, 18.01, 1.0)
cnt, _ = np.histogram(P[ok, 0], bins=bins)
print("  số điểm theo dời dọc (m):", dict(zip(bins[:-1].astype(int).tolist(), cnt.tolist())))
np.savez_compressed(f"{OUT}/check3d_{K}.npz", P=P, u=u[ok], v=v[ok], ok=ok, img=fi.get(K), z_road=z_road,
                    pose=np.array([px, py, yaw]))
print("wrote", f"{OUT}/check3d_{K}.npz")
