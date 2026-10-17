"""RMS position / yaw difference between submission CSVs (idx,x,y,yaw), standard library only.

Usage: python3 compare_csv.py SUBMISSIONS_DIR TRACK:FROM:TO [TRACK:FROM:TO ...]
  e.g. python3 compare_csv.py docs/nhat-ky/submissions track1:gnss_1.csv:gnss_smooth_1.csv
Columns: RMS of the position difference [m], RMS and mean of (FROM - TO) yaw [deg].
"""
import csv
import math
import os
import sys


def load(path):
    return [tuple(map(float, r[1:4])) for r in list(csv.reader(open(path)))[1:]]


def diff(a, b):
    A, B = load(a), load(b)
    n = len(A)
    dp = math.sqrt(sum((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 for p, q in zip(A, B)) / n)
    dyaw = [math.degrees((p[2] - q[2] + math.pi) % (2 * math.pi) - math.pi) for p, q in zip(A, B)]
    return dp, math.sqrt(sum(v * v for v in dyaw) / n), sum(dyaw) / n


def main(root, *pairs):
    print(f"{'track':6s} {'from':30s} {'to':32s} {'pos RMS m':>9s} {'yaw RMS deg':>11s} {'mean(from-to) deg':>12s}")
    for spec in pairs:
        track, a, b = spec.split(":")
        dp, dy, my = diff(os.path.join(root, track, a), os.path.join(root, track, b))
        print(f"{track:6s} {a:30s} {b:32s} {dp:9.3f} {dy:11.3f} {my:+12.3f}")


if __name__ == "__main__":
    main(*sys.argv[1:])
