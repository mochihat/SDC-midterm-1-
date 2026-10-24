"""Road-paint measurements around a prior trajectory (24/10, Track03 rules: causal).

Frame k: the grey front image k (tools/paint_images.sh) is mapped onto the road around the prior's pose at frame k
(tools/paint_bev.py: IPM with the map's road heights, camera paint = bright structures narrower than 0.7 m and brighter
than the local sunlit road) and correlated with the LiDAR map's paint (masked zero-mean NCC) over
  along x lateral shifts (--sa / --sl m, 0.1 m steps)  x  yaw offsets (--yaws)  x  camera pitch offsets (--pitches)
around that pose. Saved per frame: the NCC volume over (yaw, along, lateral), maximised over the pitch candidates
(float16), for tools/paint_fuse.py. Only image k and the prior's pose at k are used -> causal if the prior is.

Camera mounting (same car on all tracks; calibrated 24/10 on Track01 and Track02 at the reference poses, total NCC
over ~300 frames each): pitch 1.0 deg down (both tracks), yaw -1.5 deg (Track02 -1.5..-1.75, Track01 -1.0..-1.5),
height 1.646 m (the LoGeR road height used everywhere else).

Usage: python3 tools/paint_measure.py TRACK PRIOR.csv OUT.npz [--procs 10]
"""
import argparse
import multiprocessing
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paint_bev import (Camera, FrameImages, MapPaint, PaintMatcher, SideCamera, load_mask,  # noqa: E402
                       read_extrinsics)

G = {}


def rng(s):
    lo, hi, st = (float(v) for v in s.split(","))
    return np.arange(lo, hi + 1e-6, st)


def work(k):
    pm, fis, prior = G["pm"], G["fis"], G["prior"]
    imgs = [f.get(k) for f in fis]
    if imgs[0] is None and all(v is None for v in imgs):
        return k, None, -1
    if G["separate"]:
        vf, vs = pm.ncc_volume(imgs, *prior[k, 1:4], groups=[[0], list(range(1, len(imgs)))])
        ip = int(np.unravel_index(np.argmax(vf), vf.shape)[0])
        return k, np.stack([vf.max(axis=0), vs.max(axis=0)]).astype(np.float16), ip
    vol = pm.ncc_volume(imgs if len(imgs) > 1 else imgs[0], *prior[k, 1:4])
    ip = int(np.unravel_index(np.argmax(vol), vol.shape)[0])
    return k, vol.max(axis=0).astype(np.float16), ip


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("track", type=int)
    p.add_argument("prior")
    p.add_argument("out")
    p.add_argument("--data", default="/w/data")
    p.add_argument("--cache", default="/w/cache")
    p.add_argument("--pitch", type=float, default=1.0)
    p.add_argument("--camyaw", type=float, default=-1.5)
    p.add_argument("--height", type=float, default=1.646)
    p.add_argument("--roll", type=float, default=0.0)
    p.add_argument("--sa", type=float, default=2.0)
    p.add_argument("--sl", type=float, default=1.5)
    p.add_argument("--yaws", default="-1.5,1.5,0.25")
    p.add_argument("--pitches", default="-0.5,0.5,0.25")
    p.add_argument("--along", default="5,18")
    p.add_argument("--lat", default="-7,7")
    p.add_argument("--q-level", type=float, default=70.0)
    p.add_argument("--side", action="store_true",
                   help="also the front-left / front-right cameras for the road beside the car (along < --front-min "
                        "m, |lateral| >= 1.5 m; extrinsics of camera_info/lucid_camera_extrinsics.yaml)")
    p.add_argument("--front-min", type=float, default=5.0, help="m: with --side, the front camera's nearest along")
    p.add_argument("--separate", action="store_true",
                   help="with --side: front and side cameras as two NCC volumes (vol, vol_side) instead of one")
    p.add_argument("--norm", type=float, default=0.0, help="grey levels: fixed paint scale (0 = per-camera 99.5 %%)")
    p.add_argument("--procs", type=int, default=10)
    a = p.parse_args()
    t0 = time.time()
    prior = np.loadtxt(a.prior, delimiter=",", skiprows=1)
    mp = MapPaint.load(os.path.join(a.cache, f"Track{a.track}", "paint_map.npz"))
    paint = np.load(os.path.join(a.cache, f"Track{a.track}", "paint_th.npy"))
    fi = FrameImages(a.cache, a.track)
    cam = Camera(a.track, data=a.data, row0=fi.row0, rows=fi.rows, mask=load_mask(a.cache, a.track), pitch=a.pitch,
                 height=a.height, roll=a.roll, yaw=a.camyaw)
    along = tuple(float(v) for v in a.along.split(","))
    lat = tuple(float(v) for v in a.lat.split(","))
    fis, extra, fmin = [fi], [], None
    if a.side:
        from paint_bev import bev_grid
        A, L = bev_grid(along, lat, 0.1)
        ex = read_extrinsics(a.track, a.data)
        for c, reg in (("fl", (A < a.front_min) & (L >= 1.5)), ("fr", (A < a.front_min) & (L <= -1.5))):
            f = FrameImages(a.cache, a.track, c)
            fis.append(f)
            extra.append((SideCamera(a.track, cam, ex[c], f"gige_100_{c}_hdr", data=a.data, row0=f.row0, rows=f.rows,
                                     scale=f.scale), reg))
        fmin = a.front_min
    pm = PaintMatcher(mp, paint, cam, along=along, lat=lat, s_along=a.sa, s_lat=a.sl, yaws=rng(a.yaws),
                      pitches=rng(a.pitches), q_level=a.q_level, extra=extra, front_min_along=fmin,
                      norm=a.norm)
    G.update(pm=pm, fis=fis, prior=prior, separate=a.side and a.separate)
    with multiprocessing.Pool(a.procs) as pool:       # fork: the rasters are shared, results are per frame
        res = pool.map(work, range(len(prior)), chunksize=8)
    shape = (len(pm.yaws), 2 * pm.na + 1, 2 * pm.nl + 1)
    sep = G["separate"]
    vol = np.full((len(prior),) + shape, -1.0, np.float16)
    vol_side = np.full((len(prior),) + shape, -1.0, np.float16) if sep else None
    pitch_i = np.full(len(prior), -1, np.int16)
    for k, v, ip in res:
        if v is not None:
            if sep:
                vol[k], vol_side[k] = v[0], v[1]
            else:
                vol[k] = v
            pitch_i[k] = ip
    extra_arrays = {"vol_side": vol_side} if sep else {}
    np.savez(a.out, vol=vol, pitch_i=pitch_i, yaws=pm.yaws, pitches=pm.pitches + a.pitch, res=pm.res, na=pm.na,
             nl=pm.nl, prior=prior, camyaw=a.camyaw, height=a.height, **extra_arrays)
    best = vol.reshape(len(prior), -1).max(axis=1).astype(float)
    print(f"wrote {a.out}: {np.sum(pitch_i >= 0)} frames with an image, median best NCC "
          f"{np.median(best[pitch_i >= 0]):.3f} ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
