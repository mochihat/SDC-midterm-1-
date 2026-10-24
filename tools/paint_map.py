"""Road-paint rasters of the LiDAR map (24/10), for tools/paint_bev.py / tools/track_localize.py --paint.

Streams the ASCII map.pcd (x y z intensity), keeps the points within --radius m of a trajectory (any CSV idx,x,y,yaw:
the corridor the car can be in; Track03: the tracker's own output, +-30 m covers its errors), and saves
  ground  (0.5 m cells: 10th percentile of z, cars / walls removed)  and
  inten   (0.1 m cells: mean intensity of the points within 0.12 m of the ground)
to OUT.npz, and the map paint (tools/paint_bev.paint_raster: white top-hat of the intensity) to paint_th.npy in the
same directory. Deterministic; ~1-2 min per track.

Usage: python3 tools/paint_map.py TRACK TRAJ.csv OUT.npz [--data /w/data] [--radius 30]
"""
import argparse
import os
import sys
import time
import warnings

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paint_bev import MapPaint, paint_raster  # noqa: E402


def read_pcd_ascii_corridor(path, keep, chunk=1 << 26):
    """x y z intensity rows of an ASCII PCD, filtered chunk by chunk with keep(xyzi) -> bool mask"""
    out = []
    with open(path, "rb") as f:
        header = {}
        while True:
            line = f.readline()
            key, *vals = line.decode().split()
            header[key] = vals
            if key == "DATA":
                break
        if header["DATA"][0] == "binary":
            # e.g. Track02: FIELDS tl th x y z intensity, SIZE 4 x 6, TYPE U U F F F F
            kinds = {"F": "f", "U": "u", "I": "i"}
            dt = np.dtype([(n, f"<{kinds[t]}{sz}") for n, sz, t in zip(header["FIELDS"], header["SIZE"],
                                                                        header["TYPE"])])
            n_left = int(header["POINTS"][0])
            per = max(1, chunk // dt.itemsize)
            while n_left > 0:
                rec = np.frombuffer(f.read(min(per, n_left) * dt.itemsize), dtype=dt)
                n_left -= len(rec)
                v = np.stack([rec["x"], rec["y"], rec["z"], rec["intensity"]], axis=1).astype(np.float32)
                out.append(v[keep(v)])
            return np.concatenate(out)
        rest = b""
        while True:
            buf = f.read(chunk)
            if not buf:
                break
            buf = rest + buf
            cut = buf.rfind(b"\n")
            rest = buf[cut + 1:]
            v = parse(buf[:cut])
            out.append(v[keep(v)])
        if rest.strip():
            v = parse(rest)
            out.append(v[keep(v)])
    return np.concatenate(out)


def parse(b):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")      # np.fromstring(sep=" ") is deprecated but 2.5x faster than split()
        return np.fromstring(b.decode(), dtype=np.float32, sep=" ").reshape(-1, 4)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("track", type=int)
    p.add_argument("traj")
    p.add_argument("out")
    p.add_argument("--data", default="/w/data")
    p.add_argument("--radius", type=float, default=30.0)
    p.add_argument("--corridor-cache", help="optional .npy of the corridor points (re-used if it exists)")
    a = p.parse_args()
    t0 = time.time()
    if a.corridor_cache and os.path.exists(a.corridor_cache):
        pts = np.load(a.corridor_cache)
    else:
        tr = np.loadtxt(a.traj, delimiter=",", skiprows=1)
        xy = tr[:, 1:3]
        keep_i = [0]
        for i in range(1, len(xy)):
            if np.hypot(*(xy[i] - xy[keep_i[-1]])) > 1.0:
                keep_i.append(i)
        tree = cKDTree(xy[keep_i])
        pts = read_pcd_ascii_corridor(os.path.join(a.data, f"Track{a.track}", "map.pcd"),
                                      lambda v: tree.query(v[:, :2], distance_upper_bound=a.radius)[0] <= a.radius)
        if a.corridor_cache:
            np.save(a.corridor_cache, pts)
    print(f"{len(pts)} corridor points ({time.time() - t0:.0f} s)", flush=True)
    mp = MapPaint(pts)
    np.savez_compressed(a.out, x0=mp.x0, y0=mp.y0, res=mp.res, gcell=mp.gcell, ground=mp.ground, inten=mp.inten,
                        count=mp.count.astype(np.int32))
    paint = os.path.join(os.path.dirname(a.out), "paint_th.npy")
    np.save(paint, paint_raster(mp))
    print(f"wrote {a.out} + {paint}: paint raster {mp.inten.shape}, ground {mp.ground.shape} ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
