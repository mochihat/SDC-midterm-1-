"""Convert a track's raw_ply (LoGeR, ASCII, ~34k points per frame) into binary arrays once, so runs of
track_localize.py do not re-parse 3000 text files (np.loadtxt was most of the time per frame).

Writes CACHE/Track<N>/raw_ply/{xyz.npy (float32, all frames stacked), rgb.npy (uint8), index.npy, ts.npy}:
index rows = (first point, point count, timestamp ns, road height in cloud units from ground_scale.ground_height);
ts.npy = the exact int64 timestamps (float64 in index.npy loses the last digits).
The cache holds competition data: it lives outside the repo (default ~/SDC-midterm01/cache) and is never committed.

Usage: python3 tools/cache_ply.py TRACK [--data /w/data] [--cache /w/cache] [--workers 10]
"""
import argparse
import os
import sys
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gicp_refine import frame_list  # noqa: E402
from ground_scale import ground_height  # noqa: E402


def read_ascii_ply(path):
    with open(path, "rb") as f:
        count = 0
        while True:
            line = f.readline().decode("ascii", "replace").strip()
            if line.startswith("element vertex"):
                count = int(line.split()[-1])
            elif line == "end_header":
                break
        v = np.fromstring(f.read().decode("ascii"), dtype=np.float64, sep=" ")
    v = v[:count * 6].reshape(-1, 6)
    v = v[np.isfinite(v[:, :3]).all(axis=1)]
    return v[:, :3], v[:, 3:].astype(np.uint8)


def work(item):
    _, ts, path = item
    xyz, rgb = read_ascii_ply(path)
    return ts, xyz.astype(np.float32), rgb, ground_height(xyz)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("track", type=int)
    p.add_argument("--data", default="/w/data")
    p.add_argument("--cache", default="/w/cache")
    p.add_argument("--workers", type=int, default=10)
    a = p.parse_args()
    frames = frame_list(os.path.join(a.data, f"Track{a.track}"), "raw_ply")
    out = os.path.join(a.cache, f"Track{a.track}", "raw_ply")
    os.makedirs(out, exist_ok=True)
    with Pool(a.workers) as pool:
        res = pool.map(work, frames, chunksize=8)
    counts = np.array([len(r[1]) for r in res])
    first = np.concatenate([[0], np.cumsum(counts)[:-1]])
    index = np.array([(f, c, r[0], r[3]) for f, c, r in zip(first, counts, res)], dtype=np.float64)
    np.save(os.path.join(out, "xyz.npy"), np.concatenate([r[1] for r in res]))
    np.save(os.path.join(out, "rgb.npy"), np.concatenate([r[2] for r in res]))
    np.save(os.path.join(out, "index.npy"), index)
    np.save(os.path.join(out, "ts.npy"), np.array([r[0] for r in res], dtype=np.int64))
    print(f"Track{a.track}: {len(res)} frames, {counts.sum()} points ({counts.min()}..{counts.max()} per frame), "
          f"road height median {np.median(index[:, 3]):.4f} -> {out}")


if __name__ == "__main__":
    main()
