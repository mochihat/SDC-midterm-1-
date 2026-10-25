"""Presentation figure: Track03 road-paint matching at one frame (camera paint vs LiDAR-map paint, before / after).

Data: docs/report/fig/paint_figdata.npz, written by tools/paint_figdata.py in the sdc-reg container (camera paint on the
vehicle-frame road grid, map paint sampled on the same grid at the Z3a pose and at the t3_Q4 pose). Host: numpy + matplotlib.
Usage: python3 docs/report/make_paint_figure.py FRAME
"""
import os
import sys

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

D = os.path.dirname(os.path.abspath(__file__))
k = int(sys.argv[1]) if len(sys.argv) > 1 else 1100
z = np.load(os.path.join(D, "fig", "paint_figdata.npz"))
MAPC = np.array([0x3F, 0xB8, 0xC8]) / 255      # map paint
CAMC = np.array([0xF2, 0xA2, 0x3A]) / 255      # camera paint (overlap -> near white)
BG = np.array([0x14, 0x24, 0x2E]) / 255
INK, MUTED = "#1E2A32", "#5F6F7A"
A, L = z["A"], z["L"]
keep_a = (A[:, 0] >= 0.0) & (A[:, 0] <= 16.0)
keep_l = (L[0] >= -7.0) & (L[0] <= 7.0)


def overlay(cam, mp, seen):
    m = np.clip((np.nan_to_num(mp) - 0.2) / 0.5, 0, 1)
    c = np.clip((cam / max(np.percentile(cam[seen], 99.5), 1e-6) - 0.15) / 0.5, 0, 1)
    rgb = BG + m[..., None] * MAPC + c[..., None] * CAMC
    rgb[~seen] = BG + 0.55 * (rgb[~seen] - BG)
    rgb = np.clip(rgb, 0, 1)[keep_a][:, keep_l]
    return rgb[::-1, ::-1]          # along up, the car's left on the left


if os.environ.get("VI") == "1":
    import matplotlib.text as _mt
    _o = _mt.Text.set_text
    _TR = [("Front camera (one of three)", "Camera trước (một trong ba camera)"), ("Before: LiDAR-map tracker", "Trước: bộ bám bản đồ LiDAR"),
           ("m off)", "m lệch)"), ("After: road-paint matching", "Sau: khớp vạch sơn"),
           ("paint in the LiDAR map", "vạch sơn trong bản đồ LiDAR"), ("paint seen by the cameras", "vạch sơn camera thấy"),
           ("both (aligned)", "cả hai (trùng khít)")]

    def _st(self, s):
        s = "" if s is None else str(s)
        for e_, v_ in _TR:
            s = s.replace(e_, v_)
        _o(self, s)
    _mt.Text.set_text = _st
fig = plt.figure(figsize=(6.6, 5.4), dpi=220)
gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 2.55], hspace=0.16, wspace=0.06)
ax0 = fig.add_subplot(gs[0, :])
ax0.imshow(z[f"img{k}"], cmap="gray", aspect="auto")
ax0.set_title("Front camera (one of three)", fontsize=9, color=INK, loc="left")
off = z[f"off{k}"]
for j, (key, ttl) in enumerate([("mapZ", f"Before: LiDAR-map tracker ({abs(off[0]):.2f} m / {abs(off[1]):.2f} m off)"),
                                ("mapQ", "After: road-paint matching")]):
    ax = fig.add_subplot(gs[1, j])
    ax.imshow(overlay(z[f"cam{k}"], z[f"{key}{k}"], z[f"seen{k}"]), extent=[-7, 7, 0, 16], interpolation="nearest")
    ax.set_title(ttl, fontsize=8.5, color=INK, loc="left")
    ax.plot([4.3, 6.3], [0.7, 0.7], color="white", lw=1.5)
    ax.text(5.3, 1.0, "2 m", color="white", fontsize=7, ha="center", va="bottom")
    ax.plot(0, 0.35, marker="^", color="white", ms=5)
for ax in fig.axes:
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)
fig.legend(handles=[Patch(color=MAPC, label="paint in the LiDAR map"), Patch(color=CAMC, label="paint seen by the cameras"),
                    Patch(facecolor="white", edgecolor=MUTED, label="both (aligned)")],
           loc="lower center", ncol=3, fontsize=8, frameon=False, bbox_to_anchor=(0.5, 0.0))
fig.subplots_adjust(left=0.01, right=0.99, top=0.95, bottom=0.07)
out = os.path.join(D, "fig", "paint_matching_vi.png" if os.environ.get("VI") == "1" else "paint_matching.png")
fig.savefig(out, facecolor="white")
print("wrote", out)
