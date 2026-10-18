"""Chương 3.9 – ROS 2 và Docker."""
import os
import sys

from manim import DOWN, LEFT, RIGHT, UP, Arrow, FadeIn, RoundedRectangle, VGroup

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from kit import ScriptScene, default_sfx, lines_of  # noqa: E402
from style import ACCENT, BLUE, FG, RED, T  # noqa: E402


def box(text, color, pos, w=3.6):
    r = RoundedRectangle(corner_radius=0.2, width=w, height=1.0, color=color, fill_opacity=0.15).move_to(pos)
    t = T(text, 26, color)
    if t.width > w - 0.3:
        t.scale_to_fit_width(w - 0.3)
    return VGroup(r, t.move_to(r))


def ros_graph(scene):
    bag = box("rosbag Track1.db3", FG, LEFT * 4.6 + UP * 1.2)
    imu = box("/imu/data", RED, LEFT * 0.2 + UP * 2.0, 3.2)
    gnss = box("/localizer_node/gnss_pose", RED, LEFT * 0.2 + UP * 0.4, 4.4)
    node = box("node: localization", BLUE, RIGHT * 4.4 + UP * 1.2)
    rviz = box("RViz (xem 3D)", ACCENT, RIGHT * 4.4 + DOWN * 1.6)
    arrows = VGroup(Arrow(bag.get_right(), imu.get_left(), color=FG), Arrow(bag.get_right(), gnss.get_left(), color=FG),
                    Arrow(imu.get_right(), node.get_left(), color=FG), Arrow(gnss.get_right(), node.get_left(), color=FG),
                    Arrow(node.get_bottom(), rviz.get_top(), color=FG))
    for g in (bag, imu, gnss, node, rviz):
        scene.play(FadeIn(g, shift=UP * 0.2), run_time=0.3)
    scene.play(FadeIn(arrows), run_time=0.5)
    note = T("topic = kênh chat · message = tin nhắn có kiểu (vd. sensor_msgs/Imu)", 26, FG).to_edge(DOWN, buff=0.4)
    scene.play(FadeIn(note), run_time=0.3)
    return [bag, imu, gnss, node, rviz, arrows, note]


CHAPTER = "c3_09_ros"

BEATS = [
    ("Món thứ chín: ROS 2 và Docker. Code của đề chạy trên ROS 2, bộ khung phần mềm cho robot.",
     [("title", "3.9", "ROS 2 & Docker")]),
    ("Mỗi chương trình nhỏ là một node. Các node nói chuyện qua topic, như kênh chat. "
     "Mỗi tin nhắn có kiểu rõ ràng, ví dụ sensor_msgs Imu cho IMU. Dữ liệu ghi lại được lưu trong rosbag, ở đây là file Track1.db3.",
     [("custom", ros_graph)]),
    ("File launch.py khởi động nhiều node cùng lúc. RViz để xem ba chiều. colcon để build.",
     [("caption", "Công cụ ROS 2"),
      ("bullets", ["launch.py: khởi động nhiều node cùng lúc", "RViz: xem dữ liệu 3D", "colcon: build code"], 38, 1.2)]),
    ("Còn Docker là cái hộp đóng gói sẵn hệ điều hành và thư viện, máy ai chạy cũng giống nhau. Đề cho sẵn Dockerfile.",
     [("big", "DOCKER", "hộp đóng gói sẵn hệ điều hành + thư viện", BLUE)]),
]

LINES = lines_of(BEATS)
SFX = default_sfx(BEATS)


class C3_09_ROS(ScriptScene):
    CHAPTER = CHAPTER
    BEATS = BEATS
