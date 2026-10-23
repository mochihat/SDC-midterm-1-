"""GNSS latency compensation of a trajectory (23/10): positions p'(t) = p(t + dt) by linear interpolation in time (yaw kept).
Track02's clean positions lag a speed-proportional ~20 ms behind (docs/nhat-ky/12 section 6); dt is a pipeline parameter.
Usage: python3 tools/time_shift.py TRACK IN.csv OUT.csv --dt 0.02 [--cache /w/cache]"""
import argparse
import os

import numpy as np

p = argparse.ArgumentParser()
p.add_argument("track", type=int)
p.add_argument("inp")
p.add_argument("out")
p.add_argument("--dt", type=float, required=True, help="s (positive: the positions are moved forward in time)")
p.add_argument("--cache", default="/w/cache")
a = p.parse_args()
tr = np.loadtxt(a.inp, delimiter=",", skiprows=1)
t = np.load(os.path.join(a.cache, f"Track{a.track}", "raw_ply", "ts.npy"))[:len(tr)] / 1e9
out = tr.copy()
out[:, 1] = np.interp(t + a.dt, t, tr[:, 1])
out[:, 2] = np.interp(t + a.dt, t, tr[:, 2])
with open(a.out, "w") as f:
    f.write("idx,x,y,yaw\n")
    for r in out:
        f.write(f"{int(r[0])},{r[1]:.6f},{r[2]:.6f},{r[3]:.6f}\n")
d = np.hypot(*(out[:, 1:3] - tr[:, 1:3]).T)
print(f"wrote {a.out}: dt {a.dt:+.3f} s, position change mean {d.mean():.3f} m (max {d.max():.3f})")
