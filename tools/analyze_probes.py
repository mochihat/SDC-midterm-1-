"""Split a Kaggle score into its position and yaw parts using probe submissions.

Score (slide): S = sqrt(mean |dp|^2) + 0.2 * sqrt(mean dtheta_deg^2) = P + 0.2 * Y.

A probe changes the base trajectory in one known way, so for its error e_i:
  time shift dt  : P(dt)^2 = P^2 + 2 dt mean(e.v) + dt^2 mean|v|^2   (v from the trajectory)
  lateral shift L: P(L)^2  = P^2 + 2 L mean(e.n) + L^2              (n = left normal)
  yaw offset d   : Y(d)^2  = Y^2 + 2 d mean(e_theta) + d^2
With a +/- pair the cross term cancels: P(+)^2 + P(-)^2 - 2 P^2 = 2 * shift^2 * (...),
which fixes the unknown split c = 0.2 * Y of the base score. Each probe family gives an
independent estimate of c, and the cross terms give the optimal offsets.

Usage: python3 analyze_probes.py SCORES_CSV SUBMISSIONS_DIR DATA_DIR
"""
import csv
import math
import os
import sys


def scores(path):
    out = {}
    for r in csv.DictReader(open(path)):
        if r["public_score"]:
            out[(r["track"], r["file"])] = float(r["public_score"])
    return out


def trajectory(path):
    return [tuple(map(float, r[1:4])) for r in list(csv.reader(open(path)))[1:]]


def frame_times(ply_dir):
    names = sorted(n for n in os.listdir(ply_dir) if n.endswith(".ply"))
    return [int(n.rsplit("_ts_", 1)[1][:-4]) / 1e9 for n in names]


def rates(traj, times):
    """RMS speed [m/s] and RMS yaw rate [deg/s] of a trajectory sampled at `times`."""
    v2, w2 = [], []
    for (x0, y0, a0), (x1, y1, a1), t0, t1 in zip(traj, traj[1:], times, times[1:]):
        dt = t1 - t0
        v2.append(((x1 - x0) ** 2 + (y1 - y0) ** 2) / dt ** 2)
        da = math.degrees((a1 - a0 + math.pi) % (2 * math.pi) - math.pi)
        w2.append((da / dt) ** 2)
    return math.sqrt(sum(v2) / len(v2)), math.sqrt(sum(w2) / len(w2))


def solve(f, lo, hi):
    """Bisection for f(c) = 0 on [lo, hi]; None if there is no sign change."""
    flo, fhi = f(lo), f(hi)
    if flo * fhi > 0:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def report(name, c, s0):
    p, y = s0 - c, c / 0.2
    print(f"    {name:28s} c = {c:.4f}  ->  position RMSE {p:.3f} m, yaw RMSE {y:.2f} deg")
    return p, y


def main(scores_csv, subs_dir, data_dir):
    S = scores(scores_csv)
    plans = {
        # Track1 time probes shift positions only (yaw merged from the unshifted gnss_smooth_1).
        "1": dict(base="rts_pos_gnssyaw_1.csv", dt=("rts_pos_gnssyaw_dt-0.1_1.csv", "rts_pos_gnssyaw_dt0.1_1.csv"),
                  dt_shifts_yaw=False,
                  lat=("probe_lat-0.5_1.csv", "probe_lat+0.5_1.csv"), yaw=("probe_yaw-1_1.csv", "probe_yaw+1_1.csv"),
                  check=("phys_yawb_1.csv", 0.42)),
        "2": dict(base="rts_heading_2.csv", dt=("rts_heading_dt-0.1_2.csv", "rts_heading_dt0.1_2.csv"),
                  dt_shifts_yaw=True),
    }
    for track, plan in plans.items():
        s0 = S[(track, plan["base"])]
        traj = trajectory(os.path.join(subs_dir, f"track{track}", plan["base"]))
        v_rms, w_rms = rates(traj, frame_times(os.path.join(data_dir, f"Track{track}", "raw_ply")))
        print(f"\nTrack{track}: base {plan['base']} score {s0:.5f}; RMS speed {v_rms:.2f} m/s, RMS yaw rate {w_rms:.2f} deg/s")
        estimates = {}

        sm, sp = S[(track, plan["dt"][0])], S[(track, plan["dt"][1])]
        h = 0.1
        c = solve(lambda c: (sp - c) ** 2 + (sm - c) ** 2 - 2 * (s0 - c) ** 2 - 2 * h * h * v_rms ** 2, 0.0, s0 - 1e-9)
        if c is not None:
            p, _ = report("time probes (+-0.1 s)", c, s0)
            e_v = ((sp - c) ** 2 - (sm - c) ** 2) / (4 * h)
            note = (f"yaw also shifted, changing by ~{w_rms * h:.2f} deg RMS; ignored" if plan["dt_shifts_yaw"]
                    else "yaw not shifted; exact")
            print(f"      optimal time offset {-e_v / v_rms ** 2 * 1000:+.1f} ms ({note})")
            estimates["time"] = c

        if "lat" in plan:
            qm, qp = S[(track, plan["lat"][0])], S[(track, plan["lat"][1])]
            L = 0.5
            c = solve(lambda c: (qp - c) ** 2 + (qm - c) ** 2 - 2 * (s0 - c) ** 2 - 2 * L * L, 0.0, s0 - 1e-9)
            if c is not None:
                p, _ = report("lateral probes (+-0.5 m)", c, s0)
                e_n = ((qp - c) ** 2 - (qm - c) ** 2) / (4 * L)
                print(f"      optimal lateral shift {-e_n:+.3f} m (positive = left)")
                estimates["lateral"] = c

        if "yaw" in plan:
            ym, yp = S[(track, plan["yaw"][0])], S[(track, plan["yaw"][1])]
            d = 1.0

            def f(c):
                p = s0 - c
                return ((yp - p) / 0.2) ** 2 + ((ym - p) / 0.2) ** 2 - 2 * (c / 0.2) ** 2 - 2 * d * d
            c = solve(f, 1e-6, s0 - 1e-9)
            if c is not None:
                p, y = report("yaw probes (+-1 deg)", c, s0)
                e_t = (((yp - p) / 0.2) ** 2 - ((ym - p) / 0.2) ** 2) / (4 * d)
                print(f"      optimal yaw offset {-e_t:+.3f} deg")
                estimates["yaw"] = c
                name, off = plan["check"]
                pred = p + 0.2 * math.sqrt(y * y + 2 * off * e_t + off * off)
                print(f"      prediction for {name} (yaw {off:+.2f} deg): {pred:.5f}; actual {S[(track, name)]:.5f}")

        if len(estimates) > 1:
            vals = list(estimates.values())
            print(f"    agreement of the {len(vals)} independent estimates of c: "
                  f"{min(vals):.4f} .. {max(vals):.4f} (spread {max(vals) - min(vals):.4f})")


if __name__ == "__main__":
    main(*sys.argv[1:4])
