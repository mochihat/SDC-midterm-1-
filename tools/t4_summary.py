"""T4 summary: per sweep run, statistics of the GICP pass-1 corrections (no ground truth, no leaderboard).

For src/localization/result/reg/t4/<name>_Track1_debug.csv against the clean prior:
  ok %        converged, |correction| <= 2 m, |yaw correction| <= 3 deg (what the fusion keeps)
  bias        mean along / lateral correction (removed by --demean; a smaller bias = less systematic distortion)
  noise       RMS of the correction minus its 2 s smooth (matcher + point-cloud noise; lower = steadier)
  fused       RMS of the fused position change (prior -> <name>_pos_1.csv)
Ranking needs care: none of these is the true error (T2/T3: the GNSS error is in every correction).

Usage: python3 tools/t4_summary.py [--dir src/localization/result/reg/t4] [--prior .../clean_prior_1.csv]
"""
import argparse
import csv
import glob
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from error_budget import corrections, highpass, load_debug  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dir", default=os.path.join(ROOT, "src/localization/result/reg/t4"))
    p.add_argument("--prior", default=os.path.join(ROOT, "src/localization/result/reg/clean/clean_prior_1.csv"))
    p.add_argument("--out-csv", default=os.path.join(ROOT, "docs/nhat-ky/data/t4_sweep.csv"))
    a = p.parse_args()
    runs = sorted(glob.glob(os.path.join(a.dir, "*_Track1_debug.csv")))
    if not runs:
        sys.exit(f"no *_Track1_debug.csv in {a.dir}")
    prior = np.loadtxt(a.prior, delimiter=",", skiprows=1)[:, 1:4]
    rows = []
    for path in runs:
        name = os.path.basename(path).replace("_Track1_debug.csv", "")
        D = load_debug(path)
        i, al, la, dy, ok = corrections(prior, D, 2.0)
        t = (D["timestamp_ns"] - D["timestamp_ns"][0]) / 1e9
        sig = 2.0 / np.median(np.diff(t))
        na, nl = highpass(al, ok, sig), highpass(la, ok, sig)
        pos = os.path.join(a.dir, f"{name}_pos_1.csv")
        fused = np.nan
        if os.path.exists(pos):
            f = np.loadtxt(pos, delimiter=",", skiprows=1)[:, 1:3]
            fused = np.sqrt(((f - prior[:, :2]) ** 2).sum(1).mean())
        rows.append(dict(run=name, ok_pct=100 * ok.mean(), bias_along=al[ok].mean(), bias_lat=la[ok].mean(),
                         noise_along=np.sqrt((na[ok] ** 2).mean()), noise_lat=np.sqrt((nl[ok] ** 2).mean()),
                         yaw_corr_rms=np.sqrt((dy[ok] ** 2).mean()), fused_shift=fused))
    print(f"{'run':10s} {'ok%':>6s} {'bias al':>8s} {'bias lat':>8s} {'noise al':>8s} {'noise lat':>9s} {'yaw rms':>7s} {'fused':>6s}")
    for r in rows:
        print(f"{r['run']:10s} {r['ok_pct']:6.1f} {r['bias_along']:+8.3f} {r['bias_lat']:+8.3f} {r['noise_along']:8.3f} "
              f"{r['noise_lat']:9.3f} {r['yaw_corr_rms']:7.2f} {r['fused_shift']:6.3f}")
    with open(a.out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {a.out_csv}")


if __name__ == "__main__":
    main()
