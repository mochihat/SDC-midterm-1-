"""Chương 2 – Vì sao đề lại ra như vậy."""
import os
import sys

import numpy as np
from manim import DOWN, LEFT, RIGHT, UP, Dot, FadeIn, Group, ImageMobject, Line, Polygon, Rectangle, VGroup

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from kit import FIG, ScriptScene, default_sfx, lines_of  # noqa: E402
from style import ACCENT, BLUE, FG, RED, T  # noqa: E402


def three_cameras(scene):
    imgs = Group()
    for name, label in (("cam_fl.jpg", "trước-trái"), ("cam_f.jpg", "trước"), ("cam_fr.jpg", "trước-phải")):
        img = ImageMobject(os.path.join(FIG, name))
        img.width = 4.2
        cap = T(label, 26, ACCENT).next_to(img, DOWN, buff=0.15)
        imgs.add(Group(img, cap))
    imgs.arrange(RIGHT, buff=0.25).move_to(DOWN * 0.2)
    for g in imgs:
        g[0].set_opacity(0)
        scene.add(g[0])
        scene.play(scene.image_fade(g[0], True), FadeIn(g[1]), run_time=0.5)
    note = T("ảnh thật Track01, frame 1500", 24, FG).to_edge(DOWN, buff=0.3)
    scene.play(FadeIn(note), run_time=0.3)
    return [g[0] for g in imgs] + [g[1] for g in imgs] + [note]


def depth_ambiguity(scene):
    eye = Dot(LEFT * 5.5, radius=0.12, color=FG)
    screen = Line(LEFT * 3.5 + UP * 1.6, LEFT * 3.5 + DOWN * 1.6, color=ACCENT, stroke_width=6)
    near = Rectangle(width=0.6, height=0.35, color=BLUE, fill_opacity=1).move_to(LEFT * 2.3 + UP * 0.1)
    far = Rectangle(width=2.4, height=1.4, color=RED, fill_opacity=1).move_to(RIGHT * 4.0 + UP * 0.4)
    rays = VGroup(*[Line(eye.get_center(), far.get_corner(c), color=FG, stroke_opacity=0.35)
                    for c in (UP + LEFT, DOWN + LEFT)])
    l1 = T("xe đồ chơi – gần", 24, BLUE).next_to(near, DOWN, buff=0.2)
    l2 = T("xe thật – xa", 24, RED).next_to(far, DOWN, buff=0.2)
    l3 = T("ảnh", 24, ACCENT).next_to(screen, UP, buff=0.15)
    scene.play(FadeIn(eye), FadeIn(screen), FadeIn(l3), run_time=0.4)
    scene.play(FadeIn(far), FadeIn(l2), FadeIn(rays), run_time=0.5)
    scene.play(FadeIn(near), FadeIn(l1), run_time=0.5)
    same = T("trên ảnh: TRÔNG Y HỆT", 36, ACCENT, "BOLD").to_edge(DOWN, buff=0.5)
    scene.play(FadeIn(same, scale=1.2), run_time=0.4)
    return [eye, screen, near, far, rays, l1, l2, l3, same]


def three_problems(scene):
    rng = np.random.default_rng(3)
    base = np.array([[x, 0.6 * np.sin(x)] for x in np.linspace(-2, 2, 25)])
    panels = VGroup()
    for k, (cx, name) in enumerate(((-4.3, "1. SCALE ?"), (0, "2. NHIỄU"), (4.3, "3. MÉO"))):
        pts = base.copy()
        if k == 0:
            pts *= 0.45
        elif k == 1:
            pts = pts + rng.normal(0, 0.18, pts.shape)
        else:
            pts = np.c_[pts[:, 0], pts[:, 1] + 0.25 * pts[:, 0] ** 2]
        d = VGroup(*[Dot([cx + 0.8 * x, y, 0], radius=0.05, color=RED) for x, y in pts])
        ref = VGroup(*[Dot([cx + 0.8 * x, y, 0], radius=0.03, color=BLUE) for x, y in base])
        lab = T(name, 32, ACCENT, "BOLD").move_to([cx, 2.3, 0])
        panels.add(VGroup(ref, d, lab))
    for p in panels:
        scene.play(FadeIn(p, shift=UP * 0.2), run_time=0.5)
    note = T("xanh = thật · đỏ = đoán từ ảnh", 26, FG).to_edge(DOWN, buff=0.5)
    scene.play(FadeIn(note), run_time=0.3)
    return [panels, note]


CHAPTER = "c2_why"

BEATS = [
    ("Năm 2021 đề dùng LiDAR. 2023 dùng Radar. Năm nay… dùng camera. Tại sao càng ngày càng nghèo đi?",
     [("title", "CHƯƠNG 2", "Vì sao đề ra như vậy?", "2021–22 LiDAR → 2023–25 Radar → 2026 Camera")]),
    ("LiDAR bắn tia laser, đo khoảng cách cực chuẩn, nhưng đắt. Radar rẻ hơn, xuyên mưa sương tốt, nhưng điểm thưa và nhiễu. "
     "Camera rẻ nhất, ảnh rất nhiều chi tiết. Nhưng có một điểm yếu chết người.",
     [("caption", "3 loại cảm biến"),
      ("bullets", ["LiDAR: đo chuẩn, đắt", "Radar: rẻ hơn, xuyên mưa sương, nhưng thưa và nhiễu",
                   "Camera: rẻ nhất, nhiều chi tiết… nhưng?"], 38, 1.3)]),
    ("Đây là ảnh thật từ ba camera của xe trong đề: trước-trái, trước, trước-phải.",
     [("custom", three_cameras)]),
    ("Ảnh là hai chiều. Một chiếc xe đồ chơi đặt sát ống kính và một chiếc xe thật ở xa có thể trông y hệt nhau. "
     "Ảnh không cho biết vật cách bao xa.",
     [("custom", depth_ambiguity)]),
    ("Nên người ta dùng mô hình học sâu để đoán chiều sâu, rồi dựng ảnh thành đám điểm ba chiều. Đề cho sẵn hai loại. "
     "LoGeR dựng từ camera trước. MapAnything dựng từ cả ba camera.",
     [("caption", "ẢNH → MÔ HÌNH HỌC SÂU → POINT CLOUD 3D"),
      ("bullets", ["raw_ply  =  LoGeR, chỉ camera trước", "3cameras_ply  =  MapAnything, 3 camera"], 40, 0.9,
                   {0: BLUE, 1: RED})]),
    ("Đám điểm đoán ra có ba cái bệnh. Một: không biết tỉ lệ, to nhỏ sai cả mấy lần, gọi là scale ambiguity. "
     "Hai: nhiễu, càng xa càng sai. Ba: méo, lệch so với thực tế.",
     [("custom", three_problems)]),
    ("Đem một đám điểm méo như vậy đi khớp với bản đồ LiDAR chuẩn – đó chính là thử thách năm nay.",
     [("big", "ĐIỂM TỪ ẢNH  ⟷  BẢN ĐỒ LiDAR", "thử thách của midterm năm nay", ACCENT, 56)]),
    ("Đề cho hai đoạn đường: Track01 có 3011 khung hình, Track02 có 3299. Với mỗi khung hình phải nộp vị trí x, y và góc yaw. "
     "Muốn có điểm thì phải tốt hơn baseline của TA. Ngoài ảnh, đề còn cho IMU và GNSS, và cho phép dùng.",
     [("caption", "ĐỀ YÊU CẦU"),
      ("bullets", ["Track01: 3011 frame  ·  Track02: 3299 frame", "Mỗi frame nộp: x, y, yaw",
                   "Phải tốt hơn baseline của TA", "Được dùng thêm: 3 camera, IMU, GNSS"], 38, 1.5)]),
    ("Nhớ ba ý này. Một: camera rẻ nhưng không đo được chiều sâu. Hai: point cloud đoán từ ảnh có scale sai, nhiễu và méo. "
     "Ba: nhiệm vụ là khớp nó vào bản đồ LiDAR để ra pose từng frame.",
     [("summary", ["Camera rẻ nhưng không đo được chiều sâu", "Point cloud từ ảnh: scale sai, nhiễu, méo",
                   "Nhiệm vụ: khớp vào bản đồ LiDAR → pose từng frame"])]),
]

LINES = lines_of(BEATS)
SFX = default_sfx(BEATS)


class C2_Why(ScriptScene):
    CHAPTER = CHAPTER
    BEATS = BEATS
