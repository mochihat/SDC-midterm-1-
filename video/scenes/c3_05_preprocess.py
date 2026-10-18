"""Chương 3.5 – Tiền xử lý: voxel grid, crop, outlier, mặt đất, mask."""
import os
import sys

import numpy as np
from manim import DOWN, LEFT, RIGHT, UP, Dot, FadeIn, FadeOut, Line, VGroup

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from kit import ScriptScene, default_sfx, lines_of  # noqa: E402
from style import ACCENT, BLUE, FG, RED, T  # noqa: E402


def voxel(scene):
    rng = np.random.default_rng(5)
    pts = np.vstack([rng.normal([-2, 0.5], [0.9, 0.6], (120, 2)), rng.normal([2, -0.5], [1.0, 0.5], (120, 2))])
    pts = pts[(np.abs(pts[:, 0]) < 4.4) & (np.abs(pts[:, 1]) < 2.2)]
    cloud = VGroup(*[Dot([x, y - 0.3, 0], radius=0.04, color=FG) for x, y in pts])
    count = T(f"{len(pts)} điểm", 32, ACCENT).to_corner(UP + RIGHT, buff=0.5).shift(DOWN * 0.8)
    scene.play(FadeIn(cloud, lag_ratio=0.01), FadeIn(count), run_time=0.8)
    size = 0.8
    grid = VGroup(*[Line([x, -2.6, 0], [x, 2.0, 0], color=BLUE, stroke_opacity=0.5) for x in np.arange(-4.4, 4.5, size)],
                  *[Line([-4.4, y, 0], [4.4, y, 0], color=BLUE, stroke_opacity=0.5) for y in np.arange(-2.6, 2.1, size)])
    scene.play(FadeIn(grid), run_time=0.5)
    keys = np.floor((pts - np.array([-4.4, -2.3])) / size).astype(int)
    reps = {}
    for p, k in zip(pts, map(tuple, keys)):
        reps.setdefault(k, []).append(p)
    centers = np.array([np.mean(v, axis=0) for v in reps.values()])
    voxels = VGroup(*[Dot([x, y - 0.3, 0], radius=0.09, color=RED) for x, y in centers])
    count2 = T(f"{len(centers)} điểm", 32, ACCENT).move_to(count)
    scene.play(FadeOut(cloud), FadeIn(voxels, scale=1.5), FadeOut(count), FadeIn(count2), run_time=0.8)
    note = T("mỗi ô giữ 1 điểm đại diện", 28, FG).to_edge(DOWN, buff=0.35)
    scene.play(FadeIn(note), run_time=0.3)
    return [grid, voxels, count2, note]


CHAPTER = "c3_05_preprocess"

BEATS = [
    ("Món thứ năm: tiền xử lý. Point cloud thô vừa nhiều vừa bẩn. Trước khi khớp phải dọn dẹp.",
     [("title", "3.5", "Tiền xử lý", "dọn dẹp trước khi khớp")]),
    ("Một: voxel grid. Chia không gian thành các hộp nhỏ, mỗi hộp chỉ giữ một điểm đại diện.",
     [("caption", "1. VOXEL GRID"), ("custom", voxel)]),
    ("Đề dùng hộp một mét cho bản đồ, 0.3 mét cho point cloud từ ảnh. Bản đồ gần sáu mươi triệu điểm còn khoảng năm trăm nghìn.",
     [("big", "59.5 triệu → 497 nghìn", "voxel 1 m (bản đồ) · 0.3 m (point cloud)", ACCENT, 64)]),
    ("Hai: crop, chỉ cắt lấy phần bản đồ quanh xe, ở đây là cộng trừ một trăm mét. "
     "Ba: lọc điểm lạc loài, outlier, bằng thống kê hoặc bán kính. Bốn: bỏ mặt đường nếu nó gây nhiễu. "
     "Năm: che phần nắp capo xe bằng mask mà đề cho sẵn.",
     [("caption", "Các bước khác"),
      ("bullets", ["2. CROP: chỉ lấy bản đồ ±100 m quanh xe", "3. OUTLIER: lọc điểm lạc loài (thống kê / bán kính)",
                   "4. BỎ MẶT ĐẤT nếu gây nhiễu", "5. MASK nắp capo (đề cho sẵn)"], 36, 1.6)]),
    ("Nói thật: mình mới dùng một và hai, cộng thêm bỏ điểm xa hơn bốn mươi mét. Ba bước còn lại đề có gợi ý nhưng mình chưa thử.",
     [("caption", "Bài của mình"),
      ("bullets", ["Đã dùng: voxel grid, crop, bỏ điểm xa > 40 m", "Chưa thử: outlier, bỏ mặt đất, mask capo"], 38, 0.9,
                   {0: BLUE, 1: RED})]),
]

LINES = lines_of(BEATS)
SFX = default_sfx(BEATS)


class C3_05_Preprocess(ScriptScene):
    CHAPTER = CHAPTER
    BEATS = BEATS
