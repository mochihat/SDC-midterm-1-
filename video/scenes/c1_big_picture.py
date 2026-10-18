"""Chương 1 – Bức tranh lớn."""
import os
import sys

import numpy as np
from manim import DOWN, LEFT, RIGHT, UP, Arrow, Circle, Dot, FadeIn, Line, Rectangle, VGroup

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from kit import ScriptScene, default_sfx, lines_of  # noqa: E402
from style import ACCENT, BLUE, FG, RED, T  # noqa: E402


def pose_arrow(scene):
    car = Dot(radius=0.18, color=RED)
    arrow = Arrow(car.get_center(), car.get_center() + RIGHT * 1.6, buff=0, color=ACCENT, stroke_width=8)
    label = T("pose = (x, y, hướng)", 34, FG).next_to(car, DOWN, buff=0.8)
    scene.play(FadeIn(car, scale=2), run_time=0.4)
    scene.play(FadeIn(arrow), run_time=0.3)
    for ang in (np.pi / 3, -np.pi / 2, np.pi / 6):
        scene.play(arrow.animate.rotate(ang, about_point=car.get_center()), run_time=0.45)
    scene.play(FadeIn(label, shift=UP * 0.2), run_time=0.3)
    return [car, arrow, label]


def lanes(scene):
    road = VGroup(*[Line(LEFT * 6 + UP * y, RIGHT * 6 + UP * y, color=FG, stroke_width=3 if abs(y) == 1.75 else 2,
                         stroke_opacity=1 if abs(y) == 1.75 else 0.5) for y in (-1.75, 0, 1.75)])
    car = Rectangle(width=1.2, height=0.6, color=BLUE, fill_opacity=1).move_to(UP * 0.9 + LEFT * 2)
    gps = VGroup(Dot(color=RED, radius=0.12), Circle(radius=1.0, color=RED, stroke_opacity=0.6)).move_to(car)
    width = T("làn ~3.5 m", 28, FG).next_to(road, RIGHT, buff=0.2).shift(LEFT * 1.6 + UP * 1.2)
    scene.play(FadeIn(road), FadeIn(car), FadeIn(width), run_time=0.6)
    scene.play(FadeIn(gps), run_time=0.3)
    for off in (DOWN * 1.9 + RIGHT * 0.6, UP * 0.4 + RIGHT * 1.2, DOWN * 1.6 + RIGHT * 2.0):
        scene.play(gps.animate.move_to(car.get_center() + off), run_time=0.5)
    wrong = T("GPS sai 2 m → sang làn bên cạnh!", 32, RED).to_edge(DOWN, buff=0.5)
    scene.play(FadeIn(wrong, shift=UP * 0.2), run_time=0.3)
    return [road, car, gps, width, wrong]


def matching(scene):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from c3_06_icp import run_icp, rot, street, dots, move_dots
    target = street()
    source = (target @ rot(np.radians(-12)).T + np.array([0.5, -0.3]))[::2]
    states, _, _ = run_icp(source, target, 10)
    tgt = dots(target, BLUE)
    src = dots(states[0], RED, radius=0.07)
    legend = VGroup(T("● bản đồ", 26, BLUE), T("● cảm biến nhìn thấy", 26, RED)).arrange(RIGHT, buff=0.6)
    legend.to_edge(DOWN, buff=0.35)
    scene.play(FadeIn(tgt), FadeIn(src), FadeIn(legend), run_time=0.6)
    for k in range(1, len(states), 2):
        scene.play(*move_dots(src, states[k]), run_time=0.35)
    hit = T("KHỚP → biết xe ở đâu", 34, ACCENT, "BOLD").to_edge(UP, buff=0.4)
    scene.play(FadeIn(hit, scale=1.3), run_time=0.4)
    return [tgt, src, legend, hit]


CHAPTER = "c1_big_picture"

BEATS = [
    ("Điện thoại bạn có GPS. Vậy sao xe tự lái không dùng luôn GPS cho xong?",
     [("title", "CHƯƠNG 1", "Bức tranh lớn", "Có GPS rồi… cần gì nữa?")]),
    ("Xe tự hành phải trả lời ba câu hỏi. Mình đang ở đâu. Xung quanh có gì. Và đi tiếp thế nào.",
     [("caption", "3 câu hỏi của xe tự hành"),
      ("bullets", ["1. Ở ĐÂU?  →  Localization (định vị)", "2. CÓ GÌ?  →  Perception (nhận thức)",
                   "3. ĐI SAO?  →  Planning (lập kế hoạch)"], 40, 1.4)]),
    ("Câu đầu tiên tên là localization – định vị. Đó là chủ đề của cả midterm này.",
     [("big", "LOCALIZATION", "định vị – chủ đề của midterm")]),
    ("Định vị không chỉ là toạ độ. Còn phải biết xe đang quay mặt về hướng nào. "
     "Vị trí cộng hướng gọi là pose – tư thế.",
     [("caption", "POSE = VỊ TRÍ + HƯỚNG"), ("custom", pose_arrow)]),
    ("GPS thường sai vài mét. Giữa nhà cao tầng, tín hiệu dội qua dội lại, sai còn nhiều hơn. Vào hầm thì mất luôn. "
     "Một làn đường rộng chừng ba mét rưỡi. Sai hai mét là xe đã nằm ở làn bên cạnh.",
     [("custom", lanes)]),
    ("Cách của xe tự hành: mang theo một bản đồ ba chiều rất chi tiết. Cảm biến trên xe nhìn thấy gì, đem so với bản đồ. "
     "Khớp ở đâu thì xe ở đó.",
     [("custom", matching)]),
    ("Giống như bạn bị bịt mắt thả vào một con phố quen. Mở mắt ra nhìn quanh là biết mình đang đứng trước quán nào.",
     [("big", "NHÌN QUANH → SO BẢN ĐỒ", "→ biết mình đang ở đâu", BLUE, 64)]),
    ("Nhớ ba ý này. Một: localization là tìm pose – vị trí và hướng – của xe. Hai: GPS sai vài mét, không đủ cho xe tự hành. "
     "Ba: cách chính là so cái cảm biến nhìn thấy với bản đồ ba chiều.",
     [("summary", ["Localization = tìm pose (vị trí + hướng) của xe",
                   "GPS sai vài mét → không đủ cho xe tự hành",
                   "Cách chính: so cái cảm biến thấy với bản đồ 3D"])]),
]

LINES = lines_of(BEATS)
SFX = default_sfx(BEATS)


class C1_BigPicture(ScriptScene):
    CHAPTER = CHAPTER
    BEATS = BEATS
