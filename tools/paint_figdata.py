"""Arrays for docs/report/make_paint_figure.py (Track03 road-paint figure): camera paint vs map paint at the Z3a prior pose and
at the t3_Q4 pose. Run in sdc-reg: python3 tools/paint_figdata.py FRAME [FRAME ...]"""
import sys, numpy as np
sys.path.insert(0, '/w/midterm01/tools')
from paint_bev import (Camera, FrameImages, MapPaint, PaintMatcher, SideCamera, load_mask, read_extrinsics, bev_grid)
from paint_measure import rng
C = '/w/cache_test'; T = 3
R = '/w/midterm01/src/localization/result/track3/'
Z = np.loadtxt(R + 't3_Z3a.csv', delimiter=',', skiprows=1)
Q = np.loadtxt(R + 't3_Q4.csv', delimiter=',', skiprows=1)
M = np.load(C + '/Track3/paint/meas_side_pass1.npz')
mp = MapPaint.load(C + '/Track3/paint_map.npz'); paint = np.load(C + '/Track3/paint_th.npy')
fi = FrameImages(C, T)
cam = Camera(T, data='/w/data', row0=fi.row0, rows=fi.rows, mask=load_mask(C, T), pitch=1.0, height=1.646, yaw=-1.5)
along, lat = (-4.0, 18.0), (-9.0, 9.0)
A, L = bev_grid(along, lat, 0.1)
ex = read_extrinsics(T, '/w/data'); fis = [fi]; extra = []
for c, reg in (('fl', (A < 5) & (L >= 1.5)), ('fr', (A < 5) & (L <= -1.5))):
    f = FrameImages(C, T, c); fis.append(f)
    extra.append((SideCamera(T, cam, ex[c], f'gige_100_{c}_hdr', data='/w/data', row0=f.row0, rows=f.rows, scale=f.scale), reg))
out = {}
for k in [int(v) for v in sys.argv[1:]]:
    ip = int(M['pitch_i'][k]); pitches = M['pitches']
    pm = PaintMatcher(mp, paint, cam, along=along, lat=lat, s_along=0.1, s_lat=0.1, yaws=[0.0],
                      pitches=[pitches[ip] - 1.0], extra=extra, front_min_along=5.0, norm=30)
    imgs = [f.get(k) for f in fis]
    x, y, yaw = Z[k, 1:4]
    th, seen = pm.camera_paint(imgs, x, y, yaw)[0]
    def mapgrid(px, py, pyaw):
        c, s = np.cos(pyaw), np.sin(pyaw)
        return mp.sample(px + A * c - L * s, py + A * s + L * c, paint)
    la = 0.15
    qx, qy, qyaw = Q[k, 1] + la * np.cos(Q[k, 3]), Q[k, 2] + la * np.sin(Q[k, 3]), Q[k, 3]
    out[f'img{k}'] = imgs[0].astype(np.uint8); out[f'cam{k}'] = th.astype(np.float32); out[f'seen{k}'] = seen
    out[f'mapZ{k}'] = mapgrid(x, y, yaw); out[f'mapQ{k}'] = mapgrid(qx, qy, qyaw)
    d = np.array([qx - x, qy - y]); out[f'off{k}'] = np.array([d @ [np.cos(yaw), np.sin(yaw)], d @ [-np.sin(yaw), np.cos(yaw)]])
    print(k, 'offset Q4-Z3a (along, lat)', out[f'off{k}'], 'seen', seen.sum())
out['A'] = A; out['L'] = L
np.savez_compressed('/w/midterm01/docs/report/fig/paint_figdata.npz', **out)
