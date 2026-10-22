"""Leaderboard-feedback combination (Track01/02 only – allowed there per the TA, 23/10; never for Track03).

Same algebra as pos_projection.py: with a base file of known position RMSE P0 and position changes D_k whose scores
S_k (same yaw Y_k) are known, m_k = mean(e . D_k) = (P_k^2 - P0^2 - mean|D_k|^2) / 2, P_k = S_k - 0.2 Y_k, and the
combination base + sum a_k D_k has P^2 = P0^2 + 2 a.m + a^T G a.
New here: Kaggle shows scores truncated to 2 decimals since 21/10 -> a spec ending in ":t" is a truncated score
(the true score is in [S, S + 0.01): use S + 0.005 and noise sd 0.01/sqrt(12) in the score). The solution is
ridge-regularised, a = -(G + lam I)^-1 m, and lam is chosen by Monte Carlo: draw the measurement noise, solve with the
noisy m, evaluate the achieved P^2 with the unperturbed m; keep the lam with the lowest mean achieved P^2.

Spec: PATH:SCORE:Y[:t]   (Y = yaw RMSE in deg of the yaw that file carries; P0 given directly)
Usage: python3 tools/lb_combine.py P0 BASE.csv OUT.csv SPEC [SPEC ...] [--yaw-from YAW.csv] [--draws 300]
"""
import argparse
import sys

import numpy as np


def load(path):
    return np.loadtxt(path, delimiter=",", skiprows=1)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("p0", type=float)
    p.add_argument("base")
    p.add_argument("out")
    p.add_argument("specs", nargs="+")
    p.add_argument("--yaw-from", help="CSV whose yaw column goes into the output (default: base yaw)")
    p.add_argument("--draws", type=int, default=300)
    p.add_argument("--lam", type=float, help="use this ridge value instead of the Monte Carlo choice")
    a = p.parse_args()
    base = load(a.base)
    D, m, sd, names = [], [], [], []
    for spec in a.specs:
        parts = spec.split(":")
        trunc = parts[-1] == "t"
        if trunc:
            parts = parts[:-1]
        path, s, y = parts[0], float(parts[1]), float(parts[2])
        c = load(path)
        if len(c) != len(base):
            sys.exit(f"{path}: {len(c)} rows, base has {len(base)}")
        d = c[:, 1:3] - base[:, 1:3]
        s_mid = s + 0.005 if trunc else s
        pk = s_mid - 0.2 * y
        dd = np.mean(np.sum(d * d, axis=1))
        m.append((pk * pk - a.p0 ** 2 - dd) / 2)
        sd.append(pk * 0.01 / np.sqrt(12) if trunc else 0.0)  # d(P^2)/2 = P dP
        D.append(d)
        names.append(path.rsplit("/", 1)[-1])
    m, sd = np.array(m), np.array(sd)
    G = np.array([[np.mean(np.sum(x * z, axis=1)) for z in D] for x in D])
    ev = np.linalg.eigvalsh(G)
    print(f"{len(D)} directions, G eigenvalues {ev.min():.2e} .. {ev.max():.2e}")
    rng = np.random.default_rng(0)
    best = None
    for lam in ([a.lam] if a.lam is not None else [0, 1e-6, 1e-5, 1e-4, 3e-4, 1e-3, 3e-3, 1e-2]):
        A = G + lam * np.eye(len(m))
        a0 = -np.linalg.solve(A, m)
        p2_nom = a.p0 ** 2 + 2 * a0 @ m + a0 @ G @ a0
        ach = []
        for _ in range(a.draws):
            an = -np.linalg.solve(A, m + rng.normal(0, 1, len(m)) * sd)
            ach.append(a.p0 ** 2 + 2 * an @ m + an @ G @ an)
        ach = np.array(ach)
        print(f"  lam {lam:7.0e}: nominal P {np.sqrt(max(p2_nom, 0)):.4f} m, achieved mean P {np.sqrt(max(ach.mean(), 0)):.4f} "
              f"(p90 {np.sqrt(max(np.percentile(ach, 90), 0)):.4f}), max |a| {np.abs(a0).max():.2f}")
        if np.abs(a0).max() > 20:  # (near-)duplicate directions: the solution explodes, never trust it
            continue
        if best is None or ach.mean() < best[1]:
            best = (lam, ach.mean(), a0)
    lam, p2, coef = best
    print(f"chosen lam {lam:.0e}: expected position RMSE {np.sqrt(max(p2, 0)):.4f} m")
    for n_, c_ in sorted(zip(names, coef), key=lambda r: -abs(r[1]))[:12]:
        print(f"    {n_:34s} {c_:+.3f}")
    xy = base[:, 1:3] + sum(c_ * d for c_, d in zip(coef, D))
    yaw = load(a.yaw_from)[:, 3] if a.yaw_from else base[:, 3]
    with open(a.out, "w") as f:
        f.write("idx,x,y,yaw\n")
        for i, ((x, y), yw) in enumerate(zip(xy, yaw)):
            f.write(f"{int(base[i, 0])},{x:.6f},{y:.6f},{yw:.6f}\n")
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
