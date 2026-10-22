"""T3 – error budget of the scan-match corrections and which per-frame signal predicts an unreliable frame.

No ground truth and no leaderboard. The scan-match correction of frame i is d_i = matched pose - GNSS/Kalman prior.
GNSS error is slow, so the part of d_i faster than ~2 s (d_i minus its own Gaussian smooth) is matcher + point-cloud
noise. For every candidate reliability signal (speed, turn rate, acceleration, inlier ratio, GICP error per inlier,
input points, scale deviation, yaw correction, ...) the script reports the rank correlation with |noise|, and the
noise RMS per quartile of the signal -> a signal with a strong, monotone relation can weight or reject frames.
Also: a situation table (standing / slow / cruise / fast / turning) and the bias + spread of the corrections per
situation, and, with --other-debug, a comparison with another point cloud source on the same frames (T3b).

Usage: python3 tools/error_budget.py PRIOR.csv DEBUG.csv [--other-debug DEBUG2.csv] [--label 3cameras_ply]
                                     [--other-label raw_ply] [--max-xy 2] [--out-csv docs/nhat-ky/data/t3_x.csv]
"""
import argparse
import csv
import os
import sys

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.stats import spearmanr


def load_debug(path):
    if not os.path.exists(path):
        sys.exit(f"missing debug CSV: {path}")
    with open(path) as f:
        rows = list(csv.DictReader(f))
    need = {"idx", "timestamp_ns", "converged", "ndt_x", "ndt_y", "ndt_yaw", "guess_yaw"}
    if not need <= set(rows[0]):
        sys.exit(f"{path}: not a scan-match debug CSV (needs {sorted(need)})")
    return {k: np.array([float(r[k]) if r[k] not in ("", "nan") else np.nan for r in rows]) for k in rows[0]}


def corrections(prior, D, max_xy):
    i = D["idx"].astype(int)
    yaw = prior[i, 2]
    d = np.c_[D["ndt_x"], D["ndt_y"]] - prior[i, :2]
    al = d[:, 0] * np.cos(yaw) + d[:, 1] * np.sin(yaw)
    la = -d[:, 0] * np.sin(yaw) + d[:, 1] * np.cos(yaw)
    dy = np.degrees((D["ndt_yaw"] - D["guess_yaw"] + np.pi) % (2 * np.pi) - np.pi)
    ok = (D["converged"] > 0) & (np.hypot(al, la) <= max_xy) & (np.abs(dy) <= 3)
    return i, al, la, dy, ok


def highpass(v, ok, sigma):
    w = ok.astype(float)
    lo = gaussian_filter1d(np.where(ok, v, 0.0), sigma, mode="nearest") / \
        np.maximum(gaussian_filter1d(w, sigma, mode="nearest"), 1e-9)
    return v - lo


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("prior")
    p.add_argument("debug")
    p.add_argument("--other-debug")
    p.add_argument("--label", default="3cameras_ply")
    p.add_argument("--other-label", default="raw_ply")
    p.add_argument("--max-xy", type=float, default=2.0)
    p.add_argument("--out-csv")
    a = p.parse_args()
    if not os.path.exists(a.prior):
        sys.exit(f"missing prior CSV: {a.prior}")
    prior = np.loadtxt(a.prior, delimiter=",", skiprows=1)[:, 1:4]
    D = load_debug(a.debug)
    i, al, la, dy, ok = corrections(prior, D, a.max_xy)
    t = (D["timestamp_ns"] - D["timestamp_ns"][0]) / 1e9
    step = np.median(np.diff(t))
    sig = 2.0 / step
    na, nl = highpass(al, ok, sig), highpass(la, ok, sig)
    noise = np.hypot(na, nl)

    xy = gaussian_filter1d(prior[:, :2], 0.5 / step, axis=0)
    v_all = np.linalg.norm(np.gradient(xy, axis=0), axis=1) / step
    acc_all = np.abs(np.gradient(gaussian_filter1d(v_all, 0.5 / step))) / step
    w_all = np.degrees(np.abs(np.gradient(gaussian_filter1d(np.unwrap(prior[:, 2]), 0.5 / step)))) / step
    v, acc, w = v_all[i], acc_all[i], w_all[i]
    scale_dev = np.abs(D["scale"] / np.nanmedian(D["scale"]) - 1) if "scale" in D else np.zeros(len(i))
    signals = {
        "speed (m/s)": v, "turn rate (deg/s)": w, "|accel| (m/s2)": acc,
        "inlier ratio": D.get("inlier_ratio"), "GICP error / inlier": D.get("score"),
        "input points": D.get("input_points"), "|scale - median| / median": scale_dev,
        "|yaw correction| (deg)": np.abs(dy), "|correction| (m)": np.hypot(al, la),
    }
    m = ok
    print(f"frames {len(i)}, valid (converged, |d| <= {a.max_xy} m, |dyaw| <= 3 deg): {m.sum()} ({100 * m.mean():.0f} %)")
    print(f"noise (correction minus 2 s smooth) RMS: along {np.sqrt((na[m]**2).mean()):.3f} m, "
          f"lateral {np.sqrt((nl[m]**2).mean()):.3f} m")
    print("== which per-frame signal predicts the noise?  Spearman(signal, |noise|) and noise RMS per signal quartile")
    rows = []
    for name, s in signals.items():
        if s is None:
            continue
        g = m & np.isfinite(s)
        rho = spearmanr(s[g], noise[g]).correlation
        q = np.quantile(s[g], [0, .25, .5, .75, 1])
        qs = [np.sqrt((noise[g & (s >= q[k]) & (s <= q[k + 1])] ** 2).mean()) for k in range(4)]
        rows.append((name, rho, *qs))
        print(f"  {name:28s} rho {rho:+.3f}   quartiles low->high: " + " ".join(f"{x:.3f}" for x in qs))

    print("== situations (bias = mean correction, spread = noise RMS, ok = valid share)")
    sit = [("standing / starting (v < 2)", v < 2), ("slow (2-5 m/s)", (v >= 2) & (v < 5)),
           ("cruise (5-12 m/s)", (v >= 5) & (v < 12)), ("fast (>= 12 m/s)", v >= 12),
           ("turning (>= 1 deg/s)", w >= 1), ("braking / accel. (|a| >= 1)", acc >= 1)]
    for name, s in sit:
        if s.sum() < 20:
            print(f"  {name:30s} {s.sum():5d} frames – too few")
            continue
        g = s & m
        print(f"  {name:30s} {s.sum():5d} frames  ok {100 * g.sum() / s.sum():5.1f} %  bias along {al[g].mean():+.3f} "
              f"lat {la[g].mean():+.3f}  spread {np.sqrt((noise[g] ** 2).mean()):.3f} m  yaw corr RMS "
              f"{np.sqrt((dy[g] ** 2).mean()):.2f} deg")

    if a.other_debug:
        D2 = load_debug(a.other_debug)
        i2, al2, la2, dy2, ok2 = corrections(prior, D2, a.max_xy)
        common = np.intersect1d(i[ok], i2[ok2])
        p1 = {k: n for n, k in enumerate(i)}
        p2 = {k: n for n, k in enumerate(i2)}
        A = np.array([[al[p1[k]], la[p1[k]]] for k in common])
        B = np.array([[al2[p2[k]], la2[p2[k]]] for k in common])
        A0, B0 = A - A.mean(0), B - B.mean(0)
        print(f"== T3b: {a.label} vs {a.other_label}, same prior, same GICP, {len(common)} common valid frames")
        print(f"  valid share: {a.label} {100 * ok.mean():.0f} %, {a.other_label} {100 * ok2.mean():.0f} %")
        print(f"  mean correction along / lateral: {a.label} {A[:, 0].mean():+.3f} / {A[:, 1].mean():+.3f}, "
              f"{a.other_label} {B[:, 0].mean():+.3f} / {B[:, 1].mean():+.3f}")
        for k, nm in enumerate(("along", "lateral")):
            r_raw = np.corrcoef(A0[:, k], B0[:, k])[0, 1]
            sm = lambda x: gaussian_filter1d(x, 60, mode="nearest")  # ~2 s at 30 frames/s
            r_slow = np.corrcoef(sm(A0[:, k]), sm(B0[:, k]))[0, 1]
            print(f"  {nm:8s} corr per frame {r_raw:+.3f}, corr of 2 s-smoothed {r_slow:+.3f};  RMS "
                  f"{a.label} {np.sqrt((A0[:, k] ** 2).mean()):.3f}, {a.other_label} {np.sqrt((B0[:, k] ** 2).mean()):.3f}")
        print("  If both clouds gave the true correction (GNSS error) plus independent cloud errors, the smoothed")
        print("  corrections would correlate strongly; a low correlation means each cloud's own distortion dominates.")

    if a.out_csv:
        with open(a.out_csv, "w", newline="") as f:
            wr = csv.writer(f)
            wr.writerow(["signal", "spearman_vs_noise", "q1_noise", "q2_noise", "q3_noise", "q4_noise"])
            wr.writerows(rows)
        print(f"wrote {a.out_csv}")


if __name__ == "__main__":
    main()
