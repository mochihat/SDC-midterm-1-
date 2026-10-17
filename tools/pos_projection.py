"""Best combination of position changes, from submissions that changed only the positions.

Same idea as yaw_projection.py, for positions: score = P + 0.2 * Y, and when a candidate keeps a yaw whose
RMSE Y is known, its position RMSE P_k = S_k - 0.2 * Y follows exactly. With D_k the per-frame (dx, dy)
change against the base positions and e the unknown base position error:
    P_k^2 = P_base^2 + 2 mean(e . D_k) + mean |D_k|^2     ->  m_k = mean(e . D_k) is known,
and positions = base + sum_k a_k D_k has P^2 = P_base^2 + 2 a.m + a^T G a, minimised by a = -G^-1 m.
This uses leaderboard scores (Kaggle feedback), not physics.

Usage: python3 pos_projection.py P_BASE BASE_CSV OUT_CSV CAND_CSV:SCORE:Y [CAND_CSV:SCORE:Y ...]
  P_BASE  position RMSE of the base positions; Y = yaw RMSE (deg) of the yaw used in that candidate.
  The output keeps the base yaw.
"""
import csv
import math
import sys

import numpy as np


def load(path):
    rows = list(csv.reader(open(path)))[1:]
    return rows, np.array([[float(v) for v in r[1:4]] for r in rows])


def main(p0, base_csv, out_csv, *cands):
    p0 = float(p0)
    rows, base = load(base_csv)
    D, m, names = [], [], []
    for spec in cands:
        path, score, y = spec.rsplit(":", 2)
        _, c = load(path)
        d = c[:, :2] - base[:, :2]
        pk = float(score) - 0.2 * float(y)
        dd = np.mean(np.sum(d * d, axis=1))
        m.append((pk * pk - p0 * p0 - dd) / 2)
        D.append(d)
        names.append(path.rsplit("/", 1)[-1])
        print(f"{names[-1]:34s} score {float(score):.5f}  position RMSE {pk:.4f} m  |D| {math.sqrt(dd):.3f} m  "
              f"corr(e, D) {m[-1] / (p0 * math.sqrt(dd)):+.3f}")
    G = np.array([[np.mean(np.sum(a * b, axis=1)) for b in D] for a in D])
    m = np.array(m)
    a = -np.linalg.lstsq(G, m, rcond=None)[0]
    p2 = p0 * p0 + 2 * a @ m + a @ G @ a
    print(f"base position RMSE {p0:.4f} m")
    print("best combination: " + ", ".join(f"{n} x {v:+.3f}" for n, v in zip(names, a)))
    print(f"predicted position RMSE {math.sqrt(max(p2, 0)):.4f} m")
    xy = base[:, :2] + sum(ak * dk for ak, dk in zip(a, D))
    with open(out_csv, "w") as f:
        f.write("idx,x,y,yaw\n")
        for r, (x, y) in zip(rows, xy):
            f.write(f"{r[0]},{x:.6f},{y:.6f},{r[3]}\n")
    print(f"wrote {out_csv}")


if __name__ == "__main__":
    main(*sys.argv[1:])
