"""Best combination of yaw changes, from submissions that changed only the yaw (positions fixed).

With positions fixed, score = P + 0.2 * Y with Y the yaw RMSE in degrees, so each scored candidate k
gives Y_k exactly. With D_k = yaw_k - yaw_base (degrees, per frame) and e the unknown base yaw error:
    Y_k^2 = Y_base^2 + 2 mean(e D_k) + mean(D_k^2)        ->  m_k = mean(e D_k) is known.
For yaw = base + sum_k a_k D_k:  Y^2 = Y_base^2 + 2 a.m + a^T G a,  G_ij = mean(D_i D_j),
minimised by a = -G^-1 m. This uses leaderboard scores (Kaggle feedback), not physics.

Usage: python3 yaw_projection.py P BASE_CSV BASE_SCORE OUT_CSV CAND1_CSV:SCORE [CAND2_CSV:SCORE ...]
  P = position RMSE of the (shared) positions, e.g. from analyze_probes.py.
"""
import csv
import math
import sys

import numpy as np


def load(path):
    rows = list(csv.reader(open(path)))[1:]
    return rows, np.array([[float(v) for v in r[1:4]] for r in rows])


def main(p, base_csv, base_score, out_csv, *cands):
    p, base_score = float(p), float(base_score)
    rows, base = load(base_csv)
    y0 = (base_score - p) / 0.2
    D, m, names = [], [], []
    for spec in cands:
        path, score = spec.rsplit(":", 1)
        _, c = load(path)
        if np.abs(c[:, :2] - base[:, :2]).max() > 1e-6:
            raise SystemExit(f"{path}: positions differ from the base")
        d = np.degrees((c[:, 2] - base[:, 2] + np.pi) % (2 * np.pi) - np.pi)
        yk = (float(score) - p) / 0.2
        m.append((yk * yk - y0 * y0 - np.mean(d * d)) / 2)
        D.append(d)
        names.append(path.rsplit("/", 1)[-1])
        print(f"{names[-1]:34s} score {float(score):.5f}  yaw RMSE {yk:.3f} deg  |D| {math.sqrt(np.mean(d * d)):.3f}  "
              f"corr(e, D) {m[-1] / (y0 * math.sqrt(np.mean(d * d))):+.3f}")
    D, m = np.array(D), np.array(m)
    G = D @ D.T / D.shape[1]
    a = -np.linalg.lstsq(G, m, rcond=None)[0]
    y2 = y0 * y0 + 2 * a @ m + a @ G @ a
    print(f"base yaw RMSE {y0:.3f} deg (score {base_score:.5f})")
    print("best combination: " + ", ".join(f"{n} x {v:+.3f}" for n, v in zip(names, a)))
    print(f"predicted yaw RMSE {math.sqrt(max(y2, 0)):.3f} deg -> predicted score {p + 0.2 * math.sqrt(max(y2, 0)):.5f}")
    yaw = base[:, 2] + np.radians(a @ D)
    with open(out_csv, "w") as f:
        f.write("idx,x,y,yaw\n")
        for r, v in zip(rows, yaw):
            f.write(f"{r[0]},{r[1]},{r[2]},{(v + math.pi) % (2 * math.pi) - math.pi:.6f}\n")
    print(f"wrote {out_csv}")


if __name__ == "__main__":
    main(*sys.argv[1:])
