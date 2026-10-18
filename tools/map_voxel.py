"""Voxel-downsample a full map.pcd (tens of millions of points, ASCII or binary) into a small binary PCD.

Reads the file in blocks so memory stays low; keeps the centroid of every voxel.
Usage: python3 map_voxel.py MAP_PCD OUT_PCD [LEAF]      (default leaf 0.3 m)
"""
import sys

import numpy as np


def main(src, dst, leaf=0.3):
    leaf = float(leaf)
    acc_keys, acc_sum, acc_cnt = [], [], []
    with open(src, "rb") as f:
        header = {}
        while True:
            key, *vals = f.readline().decode("ascii", "replace").split()
            header[key] = vals
            if key == "DATA":
                break
        fields, kind = header["FIELDS"], header["DATA"][0]
        types = {("F", "4"): "<f4", ("F", "8"): "<f8", ("U", "4"): "<u4", ("I", "4"): "<i4", ("U", "1"): "u1"}
        dtype = np.dtype([(n, types[(t, z)]) for n, t, z in zip(fields, header["TYPE"], header["SIZE"])])
        xyz_cols = [fields.index(c) for c in "xyz"]
        total = 0
        while True:
            if kind == "binary":
                raw = f.read(dtype.itemsize * 5_000_000)
                if not raw:
                    break
                rec = np.frombuffer(raw, dtype=dtype)
                data = np.stack([rec["x"], rec["y"], rec["z"]], axis=1).astype(np.float64)
            else:
                block = f.readlines(80_000_000)
                if not block:
                    break
                data = np.array(b"".join(block).split(), dtype=np.float64).reshape(-1, len(fields))[:, xyz_cols]
            data = data[np.isfinite(data).all(axis=1)]
            total += len(data)
            keys = np.floor(data / leaf).astype(np.int64)
            uniq, inv, cnt = np.unique(keys, axis=0, return_inverse=True, return_counts=True)
            s = np.zeros((len(uniq), 3))
            np.add.at(s, inv.ravel(), data)
            acc_keys.append(uniq)
            acc_sum.append(s)
            acc_cnt.append(cnt)
            print(f"  read {total:,} points", flush=True)
    keys = np.vstack(acc_keys)
    uniq, inv = np.unique(keys, axis=0, return_inverse=True)
    s = np.zeros((len(uniq), 3))
    c = np.zeros(len(uniq))
    np.add.at(s, inv.ravel(), np.vstack(acc_sum))
    np.add.at(c, inv.ravel(), np.concatenate(acc_cnt))
    pts = (s / c[:, None]).astype("<f4")
    with open(dst, "wb") as f:
        f.write((f"# .PCD v0.7 - Point Cloud Data file format\nVERSION 0.7\nFIELDS x y z\nSIZE 4 4 4\nTYPE F F F\n"
                 f"COUNT 1 1 1\nWIDTH {len(pts)}\nHEIGHT 1\nVIEWPOINT 0 0 0 1 0 0 0\nPOINTS {len(pts)}\n"
                 f"DATA binary\n").encode())
        f.write(pts.tobytes())
    print(f"{src}: {total:,} points -> {len(pts):,} voxels of {leaf} m -> {dst}")


if __name__ == "__main__":
    main(*sys.argv[1:])
