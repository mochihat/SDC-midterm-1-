"""Interpolate GNSS poses from the track bag to every PLY frame timestamp
and write a Kaggle submission (idx, x, y, yaw).

Usage (inside container):
  python3 gnss_to_csv.py /root/data/Track1 Track1 out.csv
"""
import math
import os
import sys
from pathlib import Path

import numpy as np
from rosbags.highlevel import AnyReader


def read_gnss(bag_path):
    ts, xs, ys, yaws = [], [], [], []
    with AnyReader([Path(bag_path)]) as reader:
        conns = [c for c in reader.connections if c.topic == "/localizer_node/gnss_pose"]
        for conn, t, raw in reader.messages(connections=conns):
            msg = reader.deserialize(raw, conn.msgtype)
            p, q = msg.pose.position, msg.pose.orientation
            ts.append(t)
            xs.append(p.x)
            ys.append(p.y)
            yaws.append(math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z)))
    return np.array(ts, dtype=np.int64), np.array(xs), np.array(ys), np.unwrap(np.array(yaws))


def frame_timestamps(ply_dir):
    names = sorted(n for n in os.listdir(ply_dir) if n.endswith(".ply"))
    return np.array([int(n.rsplit("_ts_", 1)[1][:-4]) for n in names], dtype=np.int64)


def main(track_dir, track_name, output_csv):
    g_t, g_x, g_y, g_yaw = read_gnss(os.path.join(track_dir, f"{track_name}.db3"))
    f_t = frame_timestamps(os.path.join(track_dir, "raw_ply"))
    # Interpolate in seconds relative to the first GNSS sample; np.interp clamps at both ends.
    g_s = (g_t - g_t[0]) / 1e9
    f_s = (f_t - g_t[0]) / 1e9
    x = np.interp(f_s, g_s, g_x)
    y = np.interp(f_s, g_s, g_y)
    yaw = np.interp(f_s, g_s, g_yaw)
    yaw = (yaw + np.pi) % (2 * np.pi) - np.pi

    with open(output_csv, "w") as out:
        out.write("idx,x,y,yaw\n")
        for i in range(len(f_t)):
            out.write(f"{i},{x[i]:.6f},{y[i]:.6f},{yaw[i]:.6f}\n")
    print(f"{track_name}: {len(f_t)} frames, GNSS {len(g_t)} msgs, "
          f"frames outside GNSS span: {(f_s < 0).sum()} before / {(f_s > g_s[-1]).sum()} after -> {output_csv}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
