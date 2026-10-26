"""Bước kiểm tra 3D (26/10, 3): chạy tools/check3d_shift.py cho nhiều frame đứng đèn đỏ và xem đỉnh δ có ổn định không.
Chạy trong sdc-reg:  python3 tools/check3d_scan.py START END STEP
"""
import subprocess
import sys

import numpy as np

a, b, st = (int(v) for v in sys.argv[1:4])
best = []
for k in range(a, b, st):
    out = subprocess.run(["python3", "tools/check3d_shift.py", str(k)], capture_output=True, text=True).stdout
    line = [l for l in out.splitlines() if "δ tốt nhất" in l]
    if line:
        best.append((k, float(line[0].split("=")[1].split("m")[0])))
d = np.array([v for _, v in best])
print(f"frames {a}-{b}: n={len(d)}, δ trung vị = {np.median(d):+.2f} m, sd = {d.std():.2f} m, "
      f"tỉ lệ đỉnh trong ±0.3 m = {np.mean(np.abs(d) <= 0.3) * 100:.0f} %")
print("  mẫu:", [f"{k}:{v:+.1f}" for k, v in best[::max(1, len(best) // 12)]])
np.save("/w/midterm01/docs/report/fig/check3d/scan_%d_%d.npy" % (a, b), np.array(best))
