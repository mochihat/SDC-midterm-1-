"""Chương 3.2 – Pose 6DoF, roll-pitch-yaw, quaternion."""
import os
import sys

import numpy as np
from manim import DOWN, LEFT, RIGHT, UP, Arrow, Dot, FadeIn, Polygon, Rotate, VGroup

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from kit import ScriptScene, default_sfx, lines_of  # noqa: E402
from style import ACCENT, BLUE, FG, RED, T  # noqa: E402


def rpy(scene):
    plane = Polygon([-1.4, -0.3, 0], [1.6, 0, 0], [-1.4, 0.3, 0], color=BLUE, fill_opacity=0.8).shift(LEFT * 3)
    scene.play(FadeIn(plane), run_time=0.3)
    labels = [("ROLL: nghiêng cánh", RIGHT), ("PITCH: chúc đầu", UP), ("YAW: quay trái-phải", np.array([0, 0, 1]))]
    shown = []
    for i, (text, axis) in enumerate(labels):
        lab = T(text, 34, ACCENT if i == 2 else FG, "BOLD" if i == 2 else "NORMAL").move_to(RIGHT * 2.6 + UP * (1 - i))
        scene.play(FadeIn(lab, shift=LEFT * 0.3), run_time=0.3)
        scene.play(Rotate(plane, angle=0.6, axis=axis), run_time=0.45)
        scene.play(Rotate(plane, angle=-0.6, axis=axis), run_time=0.35)
        shown.append(lab)
    return [plane] + shown


def car_yaw(scene):
    car = Dot(radius=0.2, color=RED)
    arrow = Arrow(ORIGIN := np.zeros(3), RIGHT * 1.8, buff=0, color=ACCENT, stroke_width=8)
    lab = T("xe trên mặt đường: x, y, yaw là đủ", 34, FG).to_edge(DOWN, buff=0.7)
    scene.play(FadeIn(car), FadeIn(arrow), run_time=0.4)
    scene.play(Rotate(arrow, angle=1.0, about_point=ORIGIN), run_time=0.7)
    scene.play(FadeIn(lab), run_time=0.3)
    return [car, arrow, lab]


TA_CODE = """def rotation_matrix_to_yaw(pose):
    r11 = pose[0]
    r21 = pose[4]
    return math.atan2(r21, r11)"""

CHAPTER = "c3_02_pose"

BEATS = [
    ("Món thứ hai: pose sáu bậc tự do. Trong không gian ba chiều, một vật có sáu bậc tự do: "
     "ba để dịch – x, y, z – và ba để xoay.",
     [("title", "3.2", "Pose 6DoF · Roll-Pitch-Yaw · Quaternion")]),
    ("Ba góc xoay có tên rất phi công: roll là nghiêng cánh, pitch là chúc đầu, yaw là quay trái phải.",
     [("custom", rpy)]),
    ("Xe chạy trên mặt đường nên quan trọng nhất là x, y và yaw. Kaggle cũng chỉ chấm đúng ba cái đó.",
     [("custom", car_yaw)]),
    ("Còn quaternion là gì? Là cách viết một phép xoay bằng bốn con số: x, y, z, w.",
     [("big", "QUATERNION", "phép xoay = 4 số (x, y, z, w)")]),
    ("Vì sao IMU và ROS thích quaternion? Vì ba góc roll pitch yaw có chỗ bị kẹt, gọi là gimbal lock, "
     "và nội suy giữa hai góc rất xấu. Quaternion thì không bị kẹt, nối mượt.",
     [("caption", "Vì sao dùng quaternion?"),
      ("bullets", ["Góc Euler (roll-pitch-yaw): có thể bị 'kẹt' – gimbal lock",
                   "Nội suy giữa hai góc Euler: xấu", "Quaternion: không kẹt, nội suy mượt"], 36, 1.3,
                  {2: BLUE})]),
    ("Muốn lấy yaw từ quaternion thì dùng công thức này.",
     [("formula", r"\text{yaw}=\operatorname{atan2}\big(2(wz+xy),\;1-2(y^2+z^2)\big)", 50)]),
    ("Còn từ ma trận xoay thì gọn hơn nữa. Code của TA dùng đúng mấy dòng này.",
     [("caption", "Code thật: txt_to_idx_x_y_yaw.py"), ("code", TA_CODE, "python", 28)]),
    ("Lưu ý: file nộp ghi yaw bằng radian, nhưng khi chấm điểm, sai số góc lại tính bằng độ.",
     [("big", "NỘP: RADIAN", "CHẤM ĐIỂM: ĐỘ", RED, 72)]),
]

LINES = lines_of(BEATS)
SFX = default_sfx(BEATS)


class C3_02_Pose(ScriptScene):
    CHAPTER = CHAPTER
    BEATS = BEATS
