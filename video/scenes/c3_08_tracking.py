"""Chương 3.8 – Theo thời gian: motion model, GNSS, IMU, Kalman."""
import os
import sys

import numpy as np
from manim import DOWN, LEFT, RIGHT, UP, Circle, DashedLine, Dot, FadeIn, VGroup

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from kit import ScriptScene, default_sfx, lines_of  # noqa: E402
from style import ACCENT, BLUE, FG, RED, T  # noqa: E402


def lag_demo(scene):
    road = DashedLine(LEFT * 6, RIGHT * 6, color=FG, stroke_opacity=0.4)
    true_pos = [LEFT * 4 + RIGHT * 1.6 * k for k in range(5)]
    car = Dot(true_pos[0], radius=0.18, color=BLUE)
    guess = Dot(true_pos[0], radius=0.12, color=RED)
    lab1 = T("xe thật", 26, BLUE).next_to(car, UP, buff=0.3)
    lab2 = T("điểm xuất phát (pose frame trước)", 26, RED).to_edge(DOWN, buff=0.8)
    scene.play(FadeIn(road), FadeIn(car), FadeIn(guess), FadeIn(lab1), FadeIn(lab2), run_time=0.5)
    for k in range(1, 5):
        scene.play(car.animate.move_to(true_pos[k]), lab1.animate.next_to(true_pos[k], UP, buff=0.3), run_time=0.35)
        scene.play(guess.animate.move_to(true_pos[k - 1] + RIGHT * 0.9), run_time=0.3)
    lag = T("luôn bị TRỄ một đoạn", 34, ACCENT, "BOLD").to_edge(UP, buff=0.5)
    scene.play(FadeIn(lag, scale=1.2), run_time=0.3)
    return [road, car, guess, lab1, lab2, lag]


def kalman(scene):
    path = [np.array([-5 + 2.0 * k, 0.6 * np.sin(k), 0]) for k in range(6)]
    car = Dot(path[0], radius=0.14, color=BLUE)
    cloud = Circle(radius=0.3, color=ACCENT, fill_opacity=0.15).move_to(path[0])
    pred = T("DỰ ĐOÁN: vòng bất định phình ra", 28, ACCENT).to_edge(UP, buff=0.5)
    upd = T("CẬP NHẬT (có GNSS): co lại", 28, BLUE).next_to(pred, DOWN, buff=0.25)
    scene.play(FadeIn(car), FadeIn(cloud), run_time=0.4)
    shown_label = None
    for k in range(1, 6):
        scene.play(car.animate.move_to(path[k]), cloud.animate.move_to(path[k]).scale(1.6),
                   *([FadeIn(pred)] if shown_label is None else []), run_time=0.45)
        shown_label = pred
        meas = Dot(path[k] + np.array([0.25, -0.2, 0]), radius=0.08, color=RED)
        scene.play(FadeIn(meas, scale=2), run_time=0.15)
        scene.play(cloud.animate.scale(1 / 1.6), FadeIn(upd) if k == 1 else meas.animate.set_opacity(0.4), run_time=0.35)
    legend = VGroup(T("● xe (ước lượng)", 24, BLUE), T("● số đo GNSS", 24, RED)).arrange(RIGHT, buff=0.6).to_edge(DOWN, buff=0.4)
    scene.play(FadeIn(legend), run_time=0.3)
    return [car, cloud, pred, upd, legend]


CHAPTER = "c3_08_tracking"

BEATS = [
    ("Món thứ tám: theo dõi theo thời gian. Xe chạy liên tục, mỗi giây khoảng hai mươi tám khung hình.",
     [("title", "3.8", "Theo thời gian", "motion model · GNSS · IMU · Kalman")]),
    ("Cách đơn giản: lấy pose của frame trước làm điểm xuất phát cho frame sau. Template làm đúng như vậy. "
     "Vấn đề: xe đã đi tiếp ba mươi phân, điểm xuất phát luôn bị trễ.",
     [("custom", lag_demo)]),
    ("Cách tốt hơn: motion model, dự đoán bằng vận tốc. Đi đều thì frame sau ở xa thêm đúng bằng chừng đó.",
     [("big", "MOTION MODEL", "dự đoán bằng vận tốc")]),
    ("Rồi còn các cảm biến khác. GNSS cho vị trí tuyệt đối nhưng thô. IMU đo gia tốc và tốc độ quay, rất nhanh nhưng cộng dồn là trôi.",
     [("caption", "Cảm biến khác"),
      ("bullets", ["GNSS: vị trí tuyệt đối, nhưng thô", "IMU: đo gia tốc + tốc độ quay, nhanh, nhưng cộng dồn là trôi"],
       38, 0.9, {0: RED, 1: BLUE})]),
    ("Trộn chúng lại một cách thông minh gọi là sensor fusion. Công cụ kinh điển là bộ lọc Kalman. "
     "Kalman làm hai bước, lặp mãi: dự đoán theo mô hình chuyển động, rồi cập nhật khi có số đo, "
     "tin số đo nhiều hay ít tuỳ nó nhiễu cỡ nào.",
     [("custom", kalman)]),
    ("Ví dụ đời thường: bạn đi trong bóng tối đếm bước chân, đó là dự đoán. Thỉnh thoảng thấy cột đèn quen, đó là cập nhật.",
     [("big", "ĐẾM BƯỚC + NHÌN CỘT ĐÈN", "dự đoán + cập nhật = Kalman", BLUE, 60)]),
]

LINES = lines_of(BEATS)
SFX = default_sfx(BEATS)


class C3_08_Tracking(ScriptScene):
    CHAPTER = CHAPTER
    BEATS = BEATS
