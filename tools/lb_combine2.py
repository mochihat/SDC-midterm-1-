"""Combine leaderboard probes that change EITHER the yaw OR the positions of one base file (Track01/02 only - probing is
allowed there per the TA, 23/10; never Track03).

Score S = P + 0.2 Y. A yaw probe keeps the positions, so Y_k = (S_k - P0) / 0.2; a position probe keeps the yaw, so
P_k = S_k - 0.2 Y0. For a change D_k: m_k = mean(e . D_k) = (E_k^2 - E0^2 - mean|D_k|^2) / 2 (E = Y or P), and the best
combination inside the probes' span is a = -(G + lam I)^-1 m (ridge), separately for the yaw and the positions.
Kaggle shows truncated 2-decimal scores (true score in [S, S + 0.01)): the midpoint is used, and lam is chosen by
Monte Carlo over that noise and over P0 (the base's position RMSE, known only to +- --p0-sd).

Usage: python3 tools/lb_combine2.py BASE.csv S0 P0 OUT.csv PROBE.csv:S [...] [--p0-sd 0.005] [--max-coef 3]
"""
import argparse

import numpy as np


def load(path):
    return np.loadtxt(path, delimiter=",", skiprows=1)


def wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


def solve(G, m, lam):
    return -np.linalg.solve(G + lam * np.eye(len(m)), m)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("base")
    p.add_argument("s0", type=float, help="displayed (truncated) score of the base")
    p.add_argument("p0", type=float, help="position RMSE of the base (m)")
    p.add_argument("out")
    p.add_argument("probes", nargs="+")
    p.add_argument("--p0-sd", type=float, default=0.005)
    p.add_argument("--draws", type=int, default=2000)
    p.add_argument("--max-coef", type=float, default=3.0, help="reject solutions with a larger |coefficient|")
    p.add_argument("--only", choices=["yaw", "pos"], help="combine only this kind")
    a = p.parse_args()
    base = load(a.base)
    sd_t = 0.01 / np.sqrt(12)
    kinds = {"yaw": [], "pos": []}
    for spec in a.probes:
        path, s = spec.rsplit(":", 1)
        c = load(path)
        dpos = c[:, 1:3] - base[:, 1:3]
        dyaw = np.degrees(wrap(c[:, 3] - base[:, 3]))
        if np.abs(dpos).max() < 1e-5:
            kinds["yaw"].append((path, float(s), dyaw))
        elif np.abs(dyaw).max() < 1e-4:
            kinds["pos"].append((path, float(s), dpos))
        else:
            raise SystemExit(f"{path}: changes both yaw and positions")
    rng = np.random.default_rng(0)
    s0 = a.s0 + 0.005
    out = base.copy()
    total = {}
    for kind, probes in kinds.items():
        if not probes or (a.only and a.only != kind):
            continue
        D = [pr[2] for pr in probes]
        if kind == "yaw":
            G = np.array([[np.mean(x * z) for z in D] for x in D])
            dd = np.diag(G)
        else:
            G = np.array([[np.mean(np.sum(x * z, axis=1)) for z in D] for x in D])
            dd = np.diag(G)
        S = np.array([pr[1] + 0.005 for pr in probes])

        def m_of(s_probe, s_base, p0):
            y0 = (s_base - p0) / 0.2
            if kind == "yaw":
                yk = (s_probe - p0) / 0.2
                return (yk ** 2 - y0 ** 2 - dd) / 2, y0
            pk = s_probe - 0.2 * y0
            return (pk ** 2 - p0 ** 2 - dd) / 2, p0

        m, e0 = m_of(S, s0, a.p0)
        ev = np.linalg.eigvalsh(G)
        print(f"== {kind}: {len(D)} probes, base {'Y' if kind == 'yaw' else 'P'} = {e0:.4f}, "
              f"G eigenvalues {ev.min():.3g}..{ev.max():.3g}")
        for (path, s, _), mk, g in zip(probes, m, dd):
            print(f"   {path.rsplit('/', 1)[-1]:28s} S {s:.2f}  m {mk:+.4f}  |D|^2 {g:.3f}  -> alone a {-mk / g:+.3f}, "
                  f"gain {mk * mk / g:.4f}")
        best = None
        for lam in [0, 1e-3, 3e-3, 1e-2, 3e-2, 0.1, 0.3]:
            a0 = solve(G, m, lam)
            nom = e0 ** 2 + 2 * a0 @ m + a0 @ G @ a0
            ach = []
            for _ in range(a.draws):
                p0n = a.p0 + rng.normal(0, a.p0_sd)
                sb = a.s0 + rng.uniform(0, 0.01)
                sk = np.array([pr[1] for pr in probes]) + rng.uniform(0, 0.01, len(probes))
                # truth drawn: (sk, sb, p0n); estimate uses the midpoints and the nominal P0
                m_true, e_true = m_of(sk, sb, p0n)
                ach.append(e_true ** 2 + 2 * a0 @ m_true + a0 @ G @ a0 - e_true ** 2)
            ach = np.array(ach)
            print(f"   lam {lam:6.3f}: coef max {np.abs(a0).max():.2f}, nominal {np.sqrt(max(nom, 0)):.4f}, "
                  f"change in E^2 mean {ach.mean():+.4f} (p90 {np.percentile(ach, 90):+.4f})")
            if np.abs(a0).max() > a.max_coef:
                continue
            if best is None or np.percentile(ach, 90) < best[1]:
                best = (lam, np.percentile(ach, 90), a0, nom)
        lam, p90, coef, nom = best
        print(f"   chosen lam {lam}: expected {'Y' if kind == 'yaw' else 'P'} {np.sqrt(max(nom, 0)):.4f} "
              f"(p90 of the E^2 change {p90:+.4f})")
        for (path, _, _), c in zip(probes, coef):
            print(f"      {path.rsplit('/', 1)[-1]:28s} {c:+.3f}")
        if kind == "yaw":
            out[:, 3] = wrap(base[:, 3] + np.radians(sum(c * d for c, d in zip(coef, D))))
        else:
            out[:, 1:3] = base[:, 1:3] + sum(c * d for c, d in zip(coef, D))
        total[kind] = np.sqrt(max(nom, 0))
    y0 = (s0 - a.p0) / 0.2
    pred = total.get("pos", a.p0) + 0.2 * total.get("yaw", y0)
    print(f"predicted score {pred:.4f} (base midpoint {s0:.3f}; P {total.get('pos', a.p0):.4f}, Y {total.get('yaw', y0):.4f})")
    with open(a.out, "w") as f:
        f.write("idx,x,y,yaw\n")
        for r in out:
            f.write(f"{int(r[0])},{r[1]:.6f},{r[2]:.6f},{r[3]:.6f}\n")
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
