"""Small operations on submission CSVs (idx,x,y,yaw), standard library only.

  python3 csv_ops.py merge OUT --pos A.csv --yaw B.csv
      x, y taken from A and yaw from B, row by row (values copied as text).
  python3 csv_ops.py offset IN OUT [--lateral M] [--yaw-deg D]
      move every pose M metres sideways (positive = to the vehicle's left, using the
      row's yaw) and/or add D degrees to the yaw.
"""
import argparse
import csv
import math

HEADER = "idx,x,y,yaw\n"


def rows(path):
    return list(csv.reader(open(path)))[1:]


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def merge(out, pos, yaw):
    p_rows, y_rows = rows(pos), rows(yaw)
    if len(p_rows) != len(y_rows):
        raise SystemExit(f"row count differs: {len(p_rows)} vs {len(y_rows)}")
    with open(out, "w") as f:
        f.write(HEADER)
        for p, y in zip(p_rows, y_rows):
            f.write(f"{p[0]},{p[1]},{p[2]},{y[3]}\n")


def offset(src, out, lateral, yaw_deg):
    with open(out, "w") as f:
        f.write(HEADER)
        for idx, x, y, yaw in rows(src):
            yaw_f = float(yaw)
            if lateral:
                x = f"{float(x) - lateral * math.sin(yaw_f):.6f}"
                y = f"{float(y) + lateral * math.cos(yaw_f):.6f}"
            f.write(f"{idx},{x},{y},{wrap(yaw_f + math.radians(yaw_deg)):.6f}\n")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("merge")
    m.add_argument("out")
    m.add_argument("--pos", required=True)
    m.add_argument("--yaw", required=True)
    o = sub.add_parser("offset")
    o.add_argument("src")
    o.add_argument("out")
    o.add_argument("--lateral", type=float, default=0.0)
    o.add_argument("--yaw-deg", type=float, default=0.0)
    a = ap.parse_args()
    if a.cmd == "merge":
        merge(a.out, a.pos, a.yaw)
    else:
        offset(a.src, a.out, a.lateral, a.yaw_deg)


if __name__ == "__main__":
    main()
