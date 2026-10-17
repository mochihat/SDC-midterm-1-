"""Error of a localization result against a reference trajectory, frame by frame (standard library only).

Both files are Kaggle CSVs (idx,x,y,yaw). The result may be shorter (partial run); only common frames count.
Prints the error every WINDOW frames, the first frames where the error exceeds 1/5/20 m, and
position RMSE + 0.2 * yaw RMSE (deg) - the competition score if the reference were the ground truth.

Usage: python3 track_error.py RESULT_CSV REFERENCE_CSV [WINDOW]
"""
import csv
import math
import sys


def load(path):
    return [tuple(map(float, r[1:4])) for r in list(csv.reader(open(path)))[1:]]


def main(result, reference, window="250"):
    res, ref = load(result), load(reference)
    n = min(len(res), len(ref))
    window = int(window)
    pos, yaw = [], []
    for (x, y, a), (rx, ry, ra) in zip(res[:n], ref[:n]):
        pos.append(math.hypot(x - rx, y - ry))
        yaw.append(math.degrees((a - ra + math.pi) % (2 * math.pi) - math.pi))
    print(f"{n} common frames")
    for start in range(0, n, window):
        p, w = pos[start:start + window], yaw[start:start + window]
        print(f"  frames {start:5d}-{start + len(p) - 1:5d}: position error mean {sum(p) / len(p):7.2f} m, "
              f"max {max(p):7.2f} m; yaw error mean {sum(w) / len(w):+7.2f} deg")
    for thr in (1, 5, 20):
        first = next((i for i, e in enumerate(pos) if e > thr), None)
        print(f"  first frame with position error > {thr:2d} m: {first}")
    p_rmse = math.sqrt(sum(e * e for e in pos) / n)
    y_rmse = math.sqrt(sum(e * e for e in yaw) / n)
    print(f"  position RMSE {p_rmse:.3f} m, yaw RMSE {y_rmse:.2f} deg -> score vs reference {p_rmse + 0.2 * y_rmse:.4f}")


if __name__ == "__main__":
    main(*sys.argv[1:])
