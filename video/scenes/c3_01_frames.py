"""Chương 3.1 – Hệ toạ độ và phép biến đổi."""
import os
import sys

import numpy as np
from manim import (DOWN, LEFT, RIGHT, UP, Arrow, Dot, DashedLine, FadeIn, MathTex, Rectangle, VGroup)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from kit import ScriptScene, default_sfx, lines_of  # noqa: E402
from style import ACCENT, BLUE, FG, PURPLE, RED, T  # noqa: E402


def axes(origin, angle, color, name, length=1.4):
    d1 = np.array([np.cos(angle), np.sin(angle), 0])
    d2 = np.array([-np.sin(angle), np.cos(angle), 0])
    ax = VGroup(Arrow(origin, origin + d1 * length, buff=0, color=color, stroke_width=5),
                Arrow(origin, origin + d2 * length, buff=0, color=color, stroke_width=5))
    lab = T(name, 26, color).next_to(origin, DOWN + LEFT, buff=0.1)
    return VGroup(ax, lab)


def frames(scene):
    map_ax = axes(np.array([-5.5, -2.8, 0]), 0, BLUE, "map", 2.0)
    car_origin = np.array([-1.0, -0.6, 0])
    car = Rectangle(width=1.6, height=0.8, color=FG).rotate(0.5).move_to(car_origin)
    base = axes(car_origin, 0.5, RED, "base_link", 1.2)
    cam_origin = car_origin + 0.55 * np.array([np.cos(0.5), np.sin(0.5), 0])
    cam = axes(cam_origin, 0.5, ACCENT, "camera", 0.8)
    scene.play(FadeIn(map_ax), run_time=0.4)
    scene.play(FadeIn(car), FadeIn(base), run_time=0.5)
    scene.play(FadeIn(cam), run_time=0.4)
    legend = VGroup(T("map: gắn bản đồ, đứng yên", 26, BLUE), T("base_link: gắn thân xe", 26, RED),
                    T("camera: gắn với camera", 26, ACCENT)).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
    legend.to_corner(UP + RIGHT, buff=0.5).shift(DOWN * 0.8)
    scene.play(FadeIn(legend, shift=LEFT * 0.3), run_time=0.5)
    return [map_ax, car, base, cam, legend]


def transform_point(scene):
    origin_map = np.array([-5.0, -2.6, 0])
    map_ax = axes(origin_map, 0, BLUE, "map", 2.0)
    cam_o = np.array([0.5, -0.5, 0])
    ang = 0.6
    cam_ax = axes(cam_o, ang, ACCENT, "camera", 1.4)
    p_cam = np.array([1.6, 0.7, 0])
    R = np.array([[np.cos(ang), -np.sin(ang), 0], [np.sin(ang), np.cos(ang), 0], [0, 0, 1]])
    p_world = cam_o + R @ p_cam
    dot = Dot(origin_map + p_cam, color=RED, radius=0.12)
    lab = T("p (toạ độ camera)", 24, RED).next_to(dot, UP, buff=0.15)
    scene.play(FadeIn(map_ax), FadeIn(cam_ax), run_time=0.5)
    scene.play(FadeIn(dot, scale=2), FadeIn(lab), run_time=0.4)
    step1 = T("xoay R", 30, ACCENT, "BOLD").to_edge(DOWN, buff=0.6)
    scene.play(FadeIn(step1), dot.animate.move_to(origin_map + R @ p_cam), lab.animate.next_to(origin_map + R @ p_cam, UP),
               run_time=0.9)
    step2 = T("dịch t", 30, ACCENT, "BOLD").to_edge(DOWN, buff=0.6)
    trail = DashedLine(origin_map + R @ p_cam, p_world, color=PURPLE)
    scene.play(FadeIn(step2), FadeIn(trail), step1.animate.set_opacity(0), dot.animate.move_to(p_world),
               lab.animate.next_to(p_world, UP), run_time=0.9)
    done = T("→ p trên bản đồ", 24, BLUE).next_to(dot, RIGHT, buff=0.2)
    scene.play(FadeIn(done), run_time=0.3)
    return [map_ax, cam_ax, dot, lab, step1, step2, trail, done]


CODE = """T = np.eye(4)
T[:3, :3] = R          # phép xoay
T[:3, 3] = t           # phép dịch
p_map = (T @ np.append(p_cam, 1))[:3]"""

CHAPTER = "c3_01_frames"

BEATS = [
    ("Phần ba: kiến thức nền. Phần này dài nhất, nhưng hiểu xong là bạn đọc được code của đề như đọc truyện. "
     "Món đầu tiên: hệ toạ độ.",
     [("title", "CHƯƠNG 3", "Kiến thức nền", "3.1 Hệ toạ độ & phép biến đổi")]),
    ("Muốn nói xe ở đâu thì phải nói so với cái gì. Cái mốc đó gọi là hệ toạ độ, hay frame.",
     [("big", "FRAME", "= cái mốc để đo toạ độ")]),
    ("Bài này có ba frame chính. Map gắn với bản đồ, đứng yên. Base_link gắn với thân xe, chạy theo xe. "
     "Camera gắn với cái camera.",
     [("custom", frames)]),
    ("Một điểm thấy trong frame camera, muốn đặt lên bản đồ thì phải xoay rồi dịch. "
     "Xoay gọi là rotation, ký hiệu R. Dịch gọi là translation, ký hiệu t.",
     [("caption", "camera → map: xoay R rồi dịch t"), ("custom", transform_point)]),
    ("Hai cái gộp lại thành một ma trận bốn nhân bốn, gọi là ma trận đồng nhất, homogeneous matrix. "
     "Nhân ma trận này với điểm là xong cả xoay lẫn dịch.",
     [("caption", "MA TRẬN ĐỒNG NHẤT 4×4"),
      ("formula", r"T=\begin{bmatrix}R & t\\ 0 & 1\end{bmatrix},\qquad "
                  r"\begin{bmatrix}p_{map}\\ 1\end{bmatrix}=T\begin{bmatrix}p_{cam}\\ 1\end{bmatrix}", 52)]),
    ("Viết bằng Python thì chỉ vài dòng thế này.",
     [("code", CODE, "python", 26)]),
    ("Trong đề, mỗi dòng kết quả chính là ma trận này của từng frame. "
     "Và file pose ban đầu init_guess.txt cũng là một ma trận bốn nhân bốn, có cộng thêm nhiễu.",
     [("caption", "Trong đề"),
      ("bullets", ["result.txt: mỗi frame 1 ma trận 4×4 (12 số)", "init_guess.txt: ma trận 4×4 ban đầu + nhiễu"],
       36, 1.2)]),
]

LINES = lines_of(BEATS)
SFX = default_sfx(BEATS)


class C3_01_Frames(ScriptScene):
    CHAPTER = CHAPTER
    BEATS = BEATS
