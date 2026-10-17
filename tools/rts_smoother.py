"""Kinematic (CTRV) Kalman filter + RTS smoother over the GNSS poses.

State: [x, y, theta, v, omega, b] - position, motion heading, speed, yaw rate and a constant
offset b between the GNSS yaw and the motion heading (antenna/mounting). The vehicle moves
along its heading (no side slip); v and omega follow random walks driven by longitudinal
acceleration noise q_a [m/s^2] and yaw acceleration noise q_w [rad/s^2].
GNSS measures (x, y, theta + b) with noise sigma_p [m] and sigma_yaw [rad].

All noise levels are chosen by maximising the GNSS innovation likelihood on the data itself
(no ground truth / leaderboard involved). The output yaw is the motion heading theta, or
theta + b with --yaw gnss.

Usage (inside container):
  python3 rts_smoother.py TRACK_DIR TRACK_NAME OUT_CSV [--yaw heading|gnss] [--grid small|full]
"""
import argparse
import itertools
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "src", "localization", "processing_codes"))
from gnss_to_csv import frame_timestamps, read_gnss  # noqa: E402

N = 6


def wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


def predict(s, P, dt, q_a, q_w):
    x, y, th, v, w, b = s
    s2 = np.array([x + v * np.cos(th) * dt, y + v * np.sin(th) * dt, th + w * dt, v, w, b])
    F = np.eye(N)
    F[0, 2], F[0, 3] = -v * np.sin(th) * dt, np.cos(th) * dt
    F[1, 2], F[1, 3] = v * np.cos(th) * dt, np.sin(th) * dt
    F[2, 4] = dt
    Q = np.zeros((N, N))
    # Velocity/yaw-rate random walks; their effect on position/heading is second order in dt.
    Q[3, 3] = (q_a * dt) ** 2
    Q[4, 4] = (q_w * dt) ** 2
    Q[0, 0] = Q[1, 1] = (0.5 * q_a * dt * dt) ** 2
    Q[2, 2] = (0.5 * q_w * dt * dt) ** 2
    Q[5, 5] = (1e-5 * dt) ** 2
    return s2, F @ P @ F.T + Q, F


H = np.zeros((3, N))
H[0, 0] = H[1, 1] = 1.0
H[2, 2] = H[2, 5] = 1.0


def run(times, meas, is_meas, params, smooth=True):
    """times: sorted seconds; meas: (n,3) GNSS rows (ignored where is_meas is False)."""
    sigma_p, sigma_yaw, q_a, q_w = params
    R = np.diag([sigma_p ** 2, sigma_p ** 2, sigma_yaw ** 2])
    first = np.argmax(is_meas)
    s = np.array([meas[first, 0], meas[first, 1], meas[first, 2], 0.0, 0.0, 0.0])
    P = np.diag([1.0, 1.0, 0.1, 25.0, 0.1, 0.01])
    n = len(times)
    xs_f, Ps_f, xs_p, Ps_p, Fs = (np.zeros((n, N)), np.zeros((n, N, N)), np.zeros((n, N)),
                                  np.zeros((n, N, N)), np.zeros((n, N, N)))
    loglik = 0.0
    prev_t = times[0]
    for i, t in enumerate(times):
        s, P, F = predict(s, P, t - prev_t, q_a, q_w)
        prev_t = t
        xs_p[i], Ps_p[i], Fs[i] = s, P, F
        if is_meas[i]:
            innov = meas[i] - H @ s
            innov[2] = wrap(innov[2])
            S = H @ P @ H.T + R
            Sinv = np.linalg.inv(S)
            K = P @ H.T @ Sinv
            s = s + K @ innov
            P = (np.eye(N) - K @ H) @ P
            loglik += -0.5 * (innov @ Sinv @ innov + np.log(np.linalg.det(S)) + 3 * np.log(2 * np.pi))
        xs_f[i], Ps_f[i] = s, P
    if not smooth:
        return loglik, xs_f
    xs = xs_f.copy()
    Ps = Ps_f.copy()
    for i in range(n - 2, -1, -1):
        C = Ps_f[i] @ Fs[i + 1].T @ np.linalg.inv(Ps_p[i + 1])
        d = xs[i + 1] - xs_p[i + 1]
        d[2] = wrap(d[2])
        xs[i] = xs_f[i] + C @ d
        Ps[i] = Ps_f[i] + C @ (Ps[i + 1] - Ps_p[i + 1]) @ C.T
    return loglik, xs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("track_dir")
    ap.add_argument("track_name")
    ap.add_argument("out_csv")
    ap.add_argument("--yaw", default="heading", choices=["heading", "gnss"])
    ap.add_argument("--grid", default="full", choices=["small", "full"])
    ap.add_argument("--qa", type=float, help="fix longitudinal acceleration noise [m/s^2] (physical prior)")
    ap.add_argument("--qw", type=float, help="fix yaw acceleration noise [rad/s^2] (physical prior)")
    a = ap.parse_args()

    g_t, g_x, g_y, g_yaw = read_gnss(os.path.join(a.track_dir, f"{a.track_name}.db3"))
    f_t = frame_timestamps(os.path.join(a.track_dir, "raw_ply"))
    t0 = min(g_t[0], f_t[0])
    gs, fs = (g_t - t0) / 1e9, (f_t - t0) / 1e9
    gnss = np.stack([g_x, g_y, g_yaw], axis=1)

    # Likelihood is evaluated on GNSS epochs only (frame epochs carry no information).
    if a.grid == "small":
        grid = itertools.product([0.03, 0.1], [np.radians(0.5), np.radians(2)], [1.0], [0.3])
    else:
        grid = itertools.product([0.003, 0.006, 0.01, 0.02, 0.05, 0.1, 0.2],
                                 np.radians([0.2, 0.5, 1.0, 2.0, 4.0]),
                                 [0.3, 1.0, 3.0, 6.0, 10.0],
                                 [0.03, 0.1, 0.3, 1.0])
    scored = []
    if a.qa is not None or a.qw is not None:
        grid = [p for p in grid if (a.qa is None or p[2] == a.qa) and (a.qw is None or p[3] == a.qw)]
        if not grid:
            grid = itertools.product([0.003, 0.006, 0.01, 0.02, 0.05, 0.1, 0.2, 0.4],
                                     np.radians([0.2, 0.5, 1.0, 2.0, 4.0]), [a.qa], [a.qw])
    for params in grid:
        ll, _ = run(gs, gnss, np.ones(len(gs), bool), params, smooth=False)
        scored.append((ll, params))
    scored.sort(key=lambda r: -r[0])
    ll, best = scored[0]
    print(f"ML noise: sigma_p {best[0]:.3f} m, sigma_yaw {np.degrees(best[1]):.2f} deg, "
          f"q_a {best[2]} m/s^2, q_w {best[3]} rad/s^2 (loglik {ll:.1f})")
    for ll2, p in scored[1:4]:
        print(f"   next: sp {p[0]:.3f} syaw {np.degrees(p[1]):.2f} qa {p[2]} qw {p[3]} loglik {ll2:.1f}")

    # Smooth over the merged GNSS + frame timeline and read out the frame epochs.
    times = np.concatenate([gs, fs])
    order = np.argsort(times, kind="stable")
    is_meas = np.concatenate([np.ones(len(gs), bool), np.zeros(len(fs), bool)])[order]
    meas = np.concatenate([gnss, np.zeros((len(fs), 3))])[order]
    _, xs = run(times[order], meas, is_meas, best, smooth=True)
    frame_rows = np.empty(len(fs), int)
    frame_rows[order[order >= len(gs)] - len(gs)] = np.nonzero(order >= len(gs))[0]
    out = xs[frame_rows]
    yaw = out[:, 2] + (out[:, 5] if a.yaw == "gnss" else 0.0)
    print(f"estimated GNSS yaw offset b: mean {np.degrees(out[:, 5]).mean():+.3f} deg; "
          f"speed median {np.median(out[:, 3]):.2f} m/s")

    with open(a.out_csv, "w") as f:
        f.write("idx,x,y,yaw\n")
        for i, (x, y, th) in enumerate(zip(out[:, 0], out[:, 1], wrap(yaw))):
            f.write(f"{i},{x:.6f},{y:.6f},{th:.6f}\n")
    print(f"wrote {a.out_csv}")


if __name__ == "__main__":
    main()
