"""Merge NDT debug CSVs (whole runs and/or chunks) into one, one row per frame index, sorted.

Usage: python3 merge_debug.py OUT_CSV IN_CSV [IN_CSV ...]   (later files win for duplicate indices)
"""
import csv
import sys


def main(out, *inputs):
    header, rows = None, {}
    for path in inputs:
        with open(path) as f:
            r = csv.reader(f)
            h = next(r)
            header = header or h
            for row in r:
                if row:
                    rows[int(row[0])] = row
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for k in sorted(rows):
            w.writerow(rows[k])
    print(f"{out}: {len(rows)} frames (idx {min(rows)}..{max(rows)})")


if __name__ == "__main__":
    main(*sys.argv[1:])
