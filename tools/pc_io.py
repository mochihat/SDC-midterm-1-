"""Minimal PLY / PCD readers (numpy only) for offline analysis."""
import numpy as np


def read_ply_xyz(path):
    with open(path, "rb") as f:
        fmt, count, props = None, 0, []
        while True:
            line = f.readline().decode("ascii", "replace").strip()
            if line.startswith("format"):
                fmt = line.split()[1]
            elif line.startswith("element vertex"):
                count = int(line.split()[-1])
            elif line.startswith("property"):
                props.append(line.split())
            elif line == "end_header":
                break
        if fmt == "ascii":
            data = np.loadtxt(f, max_rows=count, usecols=(0, 1, 2), dtype=np.float32)
        else:
            types = {"float": "<f4", "double": "<f8", "uchar": "u1", "uint8": "u1", "int": "<i4"}
            dtype = np.dtype([(p[2], types[p[1]]) for p in props])
            rec = np.frombuffer(f.read(count * dtype.itemsize), dtype=dtype, count=count)
            data = np.stack([rec["x"], rec["y"], rec["z"]], axis=1).astype(np.float32)
    return data[np.isfinite(data).all(axis=1)]


def read_pcd_xyz(path):
    with open(path, "rb") as f:
        header = {}
        while True:
            line = f.readline().decode("ascii", "replace").strip()
            if line.startswith("#") or not line:
                continue
            key, *vals = line.split()
            header[key] = vals
            if key == "DATA":
                break
        fields = header["FIELDS"]
        n = int(header["POINTS"][0])
        if header["DATA"][0] == "ascii":
            data = np.loadtxt(f, max_rows=n, dtype=np.float32)
        else:
            sizes = [int(s) for s in header["SIZE"]]
            counts = [int(c) for c in header.get("COUNT", ["1"] * len(fields))]
            dtype = np.dtype([(fld if fld != "_" else f"_pad{i}", f"<f{s}" if t == "F" else f"V{s}", (c,) if c > 1 else ())
                              for i, (fld, s, t, c) in enumerate(zip(fields, sizes, header["TYPE"], counts))])
            rec = np.frombuffer(f.read(n * dtype.itemsize), dtype=dtype, count=n)
            data = np.stack([rec["x"], rec["y"], rec["z"]], axis=1).astype(np.float32)
    idx = [fields.index(c) for c in ("x", "y", "z")] if data.shape[1] > 3 else [0, 1, 2]
    return data[:, idx]
