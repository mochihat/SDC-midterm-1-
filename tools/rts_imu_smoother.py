"""CTRV Kalman filter + RTS smoother over GNSS poses, aided by the IMU gyro (yaw rate).

Extends rts_smoother.py with a gyro measurement and a delayed GNSS yaw. State: [x, y, theta, v, omega, b, bg]
  theta  motion heading, omega yaw rate, b constant GNSS-yaw offset, bg gyro z bias (random walk).
Measurements: GNSS position (x, y) at 4 Hz; GNSS yaw = theta(t - yaw_lag) + b, i.e. the yaw of the
pose message lags the position by yaw_lag seconds (found in the data: ~1.2-1.4 s); gyro z = omega + bg,
averaged into 20 Hz bins, with its clock shifted by `shift` seconds. yaw_lag, shift, the gyro noise and
all other noise levels are chosen by maximising the likelihood of the GNSS measurements (no ground
truth / leaderboard involved).

Usage (inside container):
  python3 rts_imu_smoother.py TRACK_DIR TRACK_NAME OUT_CSV [--yaw heading|gnss] [--no-imu]
"""
import argparse
import os
import sys
from pathlib import Path

import numpy as np
from rosbags.highlevel import AnyReader

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "src", "localization", "processing_codes"))
from gnss_to_csv import frame_timestamps, read_gnss  # noqa: E402

N = 7
GNSS_POS, GYRO, FRAME, GNSS_YAW = 0, 1, 2, 3

H_P = np.zeros((2, N))
H_P[0, 0] = H_P[1, 1] = 1.0
H_Y = np.zeros((1, N))
H_Y[0, 2] = H_Y[0, 5] = 1.0
H_W = np.zeros((1, N))
H_W[0, 4] = H_W[0, 6] = 1.0


def wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


def read_gyro(bag_path, bin_s=0.05):
    with AnyReader([Path(bag_path)]) as r:
        conns = [c for c in r.connections if c.topic == "/imu/data"]
        rows = [(ts, r.deserialize(raw, c.msgtype).angular_velocity.z) for c, ts, raw in r.messages(connections=conns)]
    t = np.array([v[0] for v in rows], dtype=np.int64)
    w = np.array([v[1] for v in rows])
    # Average into fixed bins: lower measurement noise and far fewer filter steps.
    edges = np.arange(t[0], t[-1] + 1, int(bin_s * 1e9))
    idx = np.digitize(t, edges)
    keep = [k for k in np.unique(idx) if np.sum(idx == k) >= 2]
    tb = np.array([t[idx == k].mean() for k in keep])
    wb = np.array([w[idx == k].mean() for k in keep])
    return tb, wb


def predict(s, P, dt, p):
    x, y, th, v, w, b, bg = s
    s2 = np.array([x + v * np.cos(th) * dt, y + v * np.sin(th) * dt, th + w * dt, v, w, b, bg])
    F = np.eye(N)
    F[0, 2], F[0, 3] = -v * np.sin(th) * dt, np.cos(th) * dt
    F[1, 2], F[1, 3] = v * np.cos(th) * dt, np.sin(th) * dt
    F[2, 4] = dt
    Q = np.zeros((N, N))
    Q[3, 3] = (p["q_a"] * dt) ** 2
    Q[4, 4] = (p["q_w"] * dt) ** 2
    Q[0, 0] = Q[1, 1] = (0.5 * p["q_a"] * dt * dt) ** 2
    Q[2, 2] = (0.5 * p["q_w"] * dt * dt) ** 2
    Q[5, 5] = (1e-5 * dt) ** 2
    Q[6, 6] = (p["q_bg"] * dt) ** 2
    return s2, F @ P @ F.T + Q, F


def update(s, P, z, H, R):
    """Kalman update; returns state, covariance and the innovation log-likelihood."""
    innov = z - H @ s
    S = H @ P @ H.T + R
    Sinv = np.linalg.inv(S)
    K = P @ H.T @ Sinv
    ll = -0.5 * (innov @ Sinv @ innov + np.log(np.linalg.det(S)) + len(z) * np.log(2 * np.pi))
    return s + K @ innov, (np.eye(N) - K @ H) @ P, ll


def run(times, kinds, values, p, smooth=False):
    """kinds per epoch: GNSS_POS (values x,y), GNSS_YAW (values[0] = yaw), GYRO (values[0]), FRAME."""
    R_p = np.diag([p["sigma_p"] ** 2, p["sigma_p"] ** 2])
    R_y = np.array([[p["sigma_yaw"] ** 2]])
    R_w = np.array([[p["sigma_g"] ** 2]])
    first = np.argmax(kinds == GNSS_POS)
    first_yaw = np.argmax(kinds == GNSS_YAW)
    s = np.array([values[first, 0], values[first, 1], values[first_yaw, 0], 0.0, 0.0, 0.0, 0.0])
    P = np.diag([1.0, 1.0, 0.1, 25.0, 0.1, 0.01, 0.01 ** 2])
    n = len(times)
    keep = smooth
    if keep:
        xs_f, Ps_f, xs_p, Ps_p, Fs = (np.zeros((n, N)), np.zeros((n, N, N)), np.zeros((n, N)),
                                      np.zeros((n, N, N)), np.zeros((n, N, N)))
    loglik, prev = 0.0, times[0]
    for i in range(n):
        s, P, F = predict(s, P, times[i] - prev, p)
        prev = times[i]
        if keep:
            xs_p[i], Ps_p[i], Fs[i] = s, P, F
        k = kinds[i]
        if k == GNSS_POS:
            s, P, ll = update(s, P, values[i, :2], H_P, R_p)
            loglik += ll
        elif k == GNSS_YAW:
            # Keep the measured yaw on the same 2*pi branch as the prediction.
            z = values[i, :1].copy()
            z[0] = (H_Y @ s)[0] + wrap(z[0] - (H_Y @ s)[0])
            s, P, ll = update(s, P, z, H_Y, R_y)
            loglik += ll
        elif k == GYRO and p["use_imu"]:
            s, P, _ = update(s, P, values[i, :1], H_W, R_w)
        if keep:
            xs_f[i], Ps_f[i] = s, P
    if not smooth:
        return loglik, None
    xs = xs_f.copy()
    for i in range(n - 2, -1, -1):
        C = Ps_f[i] @ Fs[i + 1].T @ np.linalg.inv(Ps_p[i + 1])
        d = xs[i + 1] - xs_p[i + 1]
        d[2] = wrap(d[2])
        xs[i] = xs_f[i] + C @ d
    return loglik, xs


def timeline(gs, gnss, fs, ws, wv, yaw_lag):
    """GNSS position at its stamp, GNSS yaw at (stamp - yaw_lag), frames, gyro bins."""
    times = np.concatenate([gs, gs - yaw_lag, fs, ws])
    kinds = np.concatenate([np.full(len(gs), GNSS_POS), np.full(len(gs), GNSS_YAW),
                            np.full(len(fs), FRAME), np.full(len(ws), GYRO)])
    values = np.zeros((len(times), 2))
    values[:len(gs)] = gnss[:, :2]
    values[len(gs):2 * len(gs), 0] = gnss[:, 2]
    values[2 * len(gs) + len(fs):, 0] = wv
    order = np.argsort(times, kind="stable")
    return times[order], kinds[order], values[order], order


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("track_dir")
    ap.add_argument("track_name")
    ap.add_argument("out_csv")
    ap.add_argument("--yaw", default="heading", choices=["heading", "gnss"])
    ap.add_argument("--no-imu", action="store_true")
    ap.add_argument("--time-offset", type=float, default=0.0,
                    help="seconds added to frame timestamps before sampling (e.g. -0.75 -> state at t - 0.75 s)")
    a = ap.parse_args()

    bag = os.path.join(a.track_dir, f"{a.track_name}.db3")
    g_t, g_x, g_y, g_yaw = read_gnss(bag)
    f_t = frame_timestamps(os.path.join(a.track_dir, "raw_ply"))
    w_t, w_v = read_gyro(bag)
    t0 = min(g_t[0], f_t[0])
    gs, fs, ws0 = (g_t - t0) / 1e9, (f_t - t0) / 1e9 + a.time_offset, (w_t - t0) / 1e9
    gnss = np.stack([g_x, g_y, g_yaw], axis=1)
    no_frames = np.array([])

    def loglik(p):
        shifted = ws0 + p["shift"]
        inside = (shifted > gs[0] - 1) & (shifted < gs[-1] + 1)
        t, k, v, _ = timeline(gs, gnss, no_frames, shifted[inside], w_v[inside], p["yaw_lag"])
        return run(t, k, v, p)[0]

    def scan(p, name, coarse, step):
        best_ll, best_v = max((loglik(dict(p, **{name: v})), v) for v in coarse)
        return max((loglik(dict(p, **{name: v})), v) for v in np.arange(best_v - step, best_v + step + 1e-9, step / 10))

    p = dict(sigma_p=0.02, sigma_yaw=np.radians(1.0), q_a=1.0, q_w=0.1, sigma_g=0.003, q_bg=1e-4,
             shift=0.0, yaw_lag=0.0, use_imu=not a.no_imu)
    print(f"loglik, start parameters, no yaw lag, no IMU: {loglik(dict(p, use_imu=False)):.1f}")
    # 1) Delay of the GNSS yaw relative to the GNSS position.
    ll, p["yaw_lag"] = scan(dict(p, use_imu=False), "yaw_lag", np.arange(-1.0, 3.001, 0.1), 0.1)
    print(f"GNSS yaw lag: {p['yaw_lag']:+.2f} s (loglik without IMU {ll:.1f})")
    if p["use_imu"]:
        # 2) IMU clock shift.
        ll, p["shift"] = scan(p, "shift", np.arange(-1.0, 1.001, 0.1), 0.1)
        print(f"IMU clock shift: {p['shift']:+.2f} s (loglik {ll:.1f})")
    # 2) Coordinate ascent over the noise levels.
    grids = dict(sigma_p=[0.003, 0.006, 0.01, 0.02, 0.05, 0.1, 0.2],
                 sigma_yaw=list(np.radians([0.2, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0])),
                 q_a=[0.3, 1.0, 2.0, 3.0, 6.0],
                 q_w=[0.01, 0.03, 0.1, 0.3, 1.0],
                 sigma_g=[0.0005, 0.001, 0.002, 0.005, 0.01, 0.03],
                 q_bg=[1e-5, 1e-4, 1e-3])
    if not p["use_imu"]:
        grids.pop("sigma_g")
        grids.pop("q_bg")
    current = loglik(p)
    for _ in range(3):
        changed = False
        for name, values in grids.items():
            scored = [(loglik(dict(p, **{name: v})), v) for v in values]
            ll, v = max(scored)
            if ll > current + 1e-6 and v != p[name]:
                p[name], current, changed = v, ll, True
        if not changed:
            break
    current, p["yaw_lag"] = max((loglik(dict(p, yaw_lag=v)), v)
                                for v in np.arange(p["yaw_lag"] - 0.1, p["yaw_lag"] + 0.101, 0.01))
    if p["use_imu"]:
        current, p["shift"] = max((loglik(dict(p, shift=v)), v)
                                  for v in np.arange(p["shift"] - 0.1, p["shift"] + 0.101, 0.01))
    print("ML parameters: " + ", ".join(
        f"{k}={np.degrees(v):.2f}deg" if k == "sigma_yaw" else f"{k}={v}" for k, v in p.items()) + f" (loglik {current:.1f})")

    shifted = ws0 + p["shift"]
    inside = (shifted > min(gs[0], fs[0]) - 1) & (shifted < max(gs[-1], fs[-1]) + 1)
    t, k, v, order = timeline(gs, gnss, fs, shifted[inside], w_v[inside], p["yaw_lag"])
    _, xs = run(t, k, v, p, smooth=True)
    out = xs[k == FRAME]
    # FRAME epochs come out in time order; frame timestamps are already sorted.
    yaw = out[:, 2] + (out[:, 5] if a.yaw == "gnss" else 0.0)
    print(f"GNSS yaw offset b {np.degrees(out[:, 5]).mean():+.3f} deg, gyro bias {np.degrees(out[:, 6]).mean():+.3f} deg/s, "
          f"speed median {np.median(out[:, 3]):.2f} m/s")
    with open(a.out_csv, "w") as f:
        f.write("idx,x,y,yaw\n")
        for i, (x, y, th) in enumerate(zip(out[:, 0], out[:, 1], wrap(yaw))):
            f.write(f"{i},{x:.6f},{y:.6f},{th:.6f}\n")
    print(f"wrote {a.out_csv}")


if __name__ == "__main__":
    main()
