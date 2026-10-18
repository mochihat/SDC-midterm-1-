"""Chương 3.7 – NDT (Normal Distributions Transform)."""
import os
import sys

import numpy as np
from manim import DOWN, LEFT, RIGHT, UP, Dot, Ellipse, FadeIn, Line, VGroup

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from kit import ScriptScene, default_sfx, lines_of  # noqa: E402
from style import ACCENT, BLUE, FG, RED, T  # noqa: E402


def ndt_cells(scene):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from c3_06_icp import rot, street
    target = street()
    S, O = 1.0, LEFT * 0.4 + DOWN * 0.4
    pts = VGroup(*[Dot(O + S * np.array([x, y, 0]), radius=0.04, color=BLUE) for x, y in target])
    scene.play(FadeIn(pts, lag_ratio=0.01), run_time=0.6)
    size = 1.0
    xs, ys = np.arange(-3.5, 3.6, size), np.arange(-2.5, 2.6, size)
    grid = VGroup(*[Line(O + [x, ys[0], 0], O + [x, ys[-1], 0], color=FG, stroke_opacity=0.25) for x in xs],
                  *[Line(O + [xs[0], y, 0], O + [xs[-1], y, 0], color=FG, stroke_opacity=0.25) for y in ys])
    scene.play(FadeIn(grid), run_time=0.4)
    ells = VGroup()
    for x0 in xs[:-1]:
        for y0 in ys[:-1]:
            inside = target[(target[:, 0] >= x0) & (target[:, 0] < x0 + size) & (target[:, 1] >= y0) & (target[:, 1] < y0 + size)]
            if len(inside) < 3:
                continue
            mu = inside.mean(0)
            cov = np.cov(inside.T) + np.eye(2) * 0.004
            w, v = np.linalg.eigh(cov)
            e = Ellipse(width=4 * np.sqrt(w[1]) + 0.08, height=4 * np.sqrt(w[0]) + 0.08, color=ACCENT,
                        fill_opacity=0.35, stroke_width=2)
            e.rotate(np.arctan2(v[1, 1], v[0, 1])).move_to(O + S * np.array([mu[0], mu[1], 0]))
            ells.add(e)
    scene.play(FadeIn(ells, lag_ratio=0.05), pts.animate.set_opacity(0.3), run_time=1.0)
    src_pts = target[::2] @ rot(np.radians(-10)).T + np.array([0.4, -0.25])
    src = VGroup(*[Dot(O + S * np.array([x, y, 0]), radius=0.05, color=RED) for x, y in src_pts])
    scene.play(FadeIn(src), run_time=0.4)
    final = target[::2]
    scene.play(*[d.animate.move_to(O + S * np.array([x, y, 0])) for d, (x, y) in zip(src, final)], run_time=1.2)
    lab = T("điểm đỏ rơi vào chỗ 'đậm' của các ô", 28, ACCENT).to_edge(DOWN, buff=0.3)
    scene.play(FadeIn(lab), run_time=0.3)
    return [pts, grid, ells, src, lab]


NDT_CODE = """pcl::NormalDistributionsTransform<pcl::PointXYZ, pcl::PointXYZ> ndt;
ndt.setResolution(ndt_resolution_);
ndt.setStepSize(ndt_step_size_);
ndt.setTransformationEpsilon(ndt_transformation_epsilon_);
ndt.setMaximumIterations(ndt_max_iterations_);
ndt.setInputSource(source);
ndt.setInputTarget(target);
ndt.align(aligned, initial_guess);"""

CHAPTER = "c3_07_ndt"

BEATS = [
    ("Món thứ bảy, cũng là món mình dùng thật: NDT, Normal Distributions Transform.",
     [("title", "3.7", "NDT", "Normal Distributions Transform")]),
    ("Thay vì giữ từng điểm của bản đồ, NDT chia bản đồ thành các ô. Mỗi ô tóm lại bằng một hình bầu dục xác suất, "
     "một phân phối chuẩn, Gaussian. Rồi nó xoay, dịch đám điểm từ ảnh sao cho các điểm rơi vào vùng đậm nhất của các hình bầu dục.",
     [("custom", ndt_cells)]),
    ("Ưu điểm: không cần ghép cặp từng điểm, mượt hơn, thường nhanh hơn ICP.",
     [("big", "KHÔNG cần ghép cặp", "mượt hơn · thường nhanh hơn ICP", BLUE, 72)]),
    ("Tham số quan trọng nhất là độ lớn ô, resolution. Ô to thì dễ hội tụ nhưng thô. Ô nhỏ thì chi tiết nhưng dễ lạc. "
     "Template dùng ô tám mét. Với tỉ lệ đúng, mình thấy ô bốn mét tốt hơn hẳn.",
     [("caption", "RESOLUTION = độ lớn ô"),
      ("bullets", ["Ô to: dễ hội tụ, nhưng thô", "Ô nhỏ: chi tiết, nhưng dễ lạc",
                   "Template: 8 m  →  bài mình: 4 m (với scale đúng)"], 38, 1.3, {2: ACCENT})]),
    ("Đây là hàm NDT thật trong code của đề, dùng thư viện PCL. Mình giữ nguyên hàm này.",
     [("caption", "Code thật: AlignNDT() trong localization.cpp"), ("code", NDT_CODE, "cpp", 20)]),
    ("So nhanh hai thuật toán. ICP ghép cặp từng điểm, rất nhạy với điểm xuất phát, tham số chính là khoảng cách ghép cặp. "
     "NDT không ghép cặp, đỡ nhạy hơn một chút, tham số chính là resolution.",
     [("table", [["", "ICP", "NDT"], ["Ghép cặp từng điểm", "có", "không"], ["Nhạy điểm xuất phát", "cao", "vừa"],
                 ["Tham số chính", "khoảng cách ghép cặp", "resolution (độ lớn ô)"]], 32)]),
]

LINES = lines_of(BEATS)
SFX = default_sfx(BEATS)


class C3_07_NDT(ScriptScene):
    CHAPTER = CHAPTER
    BEATS = BEATS
