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
from paint_bev import Camera, FrameImages, MapPaint, PaintMatcher, load_mask  # noqa: E402

G = {}


def rng(s):
    lo, hi, st = (float(v) for v in s.split(","))
    return np.arange(lo, hi + 1e-6, st)


def work(k):
    pm, fi, prior = G["pm"], G["fi"], G["prior"]
    img = fi.get(k)
    if img is None:
        return k, None, -1
    vol = pm.ncc_volume(img, *prior[k, 1:4])
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
    p.add_argument("--procs", type=int, default=10)
    a = p.parse_args()
    t0 = time.time()
    prior = np.loadtxt(a.prior, delimiter=",", skiprows=1)
    mp = MapPaint.load(os.path.join(a.cache, f"Track{a.track}", "paint_map.npz"))
    paint = np.load(os.path.join(a.cache, f"Track{a.track}", "paint_th.npy"))
    fi = FrameImages(a.cache, a.track)
    cam = Camera(a.track, data=a.data, row0=fi.row0, rows=fi.rows, mask=load_mask(a.cache, a.track), pitch=a.pitch,
                 height=a.height, roll=a.roll, yaw=a.camyaw)
    pm = PaintMatcher(mp, paint, cam, along=tuple(float(v) for v in a.along.split(",")),
                      lat=tuple(float(v) for v in a.lat.split(",")), s_along=a.sa, s_lat=a.sl, yaws=rng(a.yaws),
                      pitches=rng(a.pitches), q_level=a.q_level)
    G.update(pm=pm, fi=fi, prior=prior)
    with multiprocessing.Pool(a.procs) as pool:       # fork: the rasters are shared, results are per frame
        res = pool.map(work, range(len(prior)), chunksize=8)
    shape = (len(pm.yaws), 2 * pm.na + 1, 2 * pm.nl + 1)
    vol = np.full((len(prior),) + shape, -1.0, np.float16)
    pitch_i = np.full(len(prior), -1, np.int16)
    for k, v, ip in res:
        if v is not None:
            vol[k], pitch_i[k] = v, ip
    np.savez(a.out, vol=vol, pitch_i=pitch_i, yaws=pm.yaws, pitches=pm.pitches + a.pitch, res=pm.res, na=pm.na,
             nl=pm.nl, prior=prior, camyaw=a.camyaw, height=a.height)
    best = vol.reshape(len(prior), -1).max(axis=1).astype(float)
    print(f"wrote {a.out}: {np.sum(pitch_i >= 0)} frames with an image, median best NCC "
          f"{np.median(best[pitch_i >= 0]):.3f} ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
