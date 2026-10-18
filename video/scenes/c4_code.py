"""Chương 4 – Code của đề chạy thế nào."""
import os
import sys

from manim import DOWN, LEFT, RIGHT, UP, Arrow, FadeIn, GrowArrow, RoundedRectangle, VGroup

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from kit import ScriptScene, default_sfx, lines_of  # noqa: E402
from style import ACCENT, BLUE, FG, PURPLE, RED, T  # noqa: E402


def card(title, desc, color, pos, w=6.2):
    r = RoundedRectangle(corner_radius=0.2, width=w, height=1.5, color=color, fill_opacity=0.12).move_to(pos)
    t = T(title, 30, color, "BOLD").move_to(r.get_center() + UP * 0.3)
    d = T(desc, 22, FG).move_to(r.get_center() + DOWN * 0.3)
    if d.width > w - 0.3:
        d.scale_to_fit_width(w - 0.3)
    return VGroup(r, t, d)


def files(scene):
    cards = [card("localization.cpp", "trái tim: đọc map, từng point cloud, NDT, ghi kết quả", ACCENT, LEFT * 3.3 + UP * 1.3),
             card("map_modified.cpp", "tuỳ chọn: lọc, giảm mẫu bản đồ (mình chưa dùng)", FG, RIGHT * 3.3 + UP * 1.3),
             card("visualization.cpp", "vẽ kết quả lên RViz", BLUE, LEFT * 3.3 + DOWN * 0.6),
             card("txt_to_idx_x_y_yaw.py", "đổi kết quả sang định dạng Kaggle", PURPLE, RIGHT * 3.3 + DOWN * 0.6)]
    for c in cards:
        scene.play(FadeIn(c, shift=UP * 0.3), run_time=0.35)
        scene.wait(1.6)
    note = T("đề ghi process/…  ·  repo thật: src/localization/processing_codes/", 24, FG).to_edge(DOWN, buff=0.5)
    scene.play(FadeIn(note), run_time=0.3)
    return cards + [note]


def box(text, color, pos, w=2.6):
    r = RoundedRectangle(corner_radius=0.15, width=w, height=0.8, color=color, fill_opacity=0.15).move_to(pos)
    t = T(text, 22, color)
    if t.width > w - 0.2:
        t.scale_to_fit_width(w - 0.2)
    return VGroup(r, t.move_to(r))


def dataflow(scene):
    y1, y2, y3 = UP * 2.0, UP * 0.2, DOWN * 1.7
    row1 = [box("map.pcd", FG, LEFT * 5 + y1), box("voxel 1 m", BLUE, LEFT * 1.8 + y1), box("cache (lần sau vài giây)", BLUE, RIGHT * 1.9 + y1, 3.6)]
    init = box("init_guess.txt", FG, LEFT * 5.4 + y2, 2.6)
    row3 = [box("*.ply", FG, LEFT * 5.6 + y3, 1.6), box("× scale", RED, LEFT * 3.5 + y3, 1.8), box("voxel", BLUE, LEFT * 1.5 + y3, 1.6),
            box("NDT", ACCENT, RIGHT * 0.7 + y3, 1.8), box("result.txt", FG, RIGHT * 3.1 + y3, 2.2), box("CSV", PURPLE, RIGHT * 5.4 + y3, 1.6)]
    submap = box("submap quanh xe", BLUE, RIGHT * 2.4 + y2, 2.8)
    pose = box("pose frame trước", ACCENT, LEFT * 2.0 + y2, 2.8)

    def chain(items):
        arrows = []
        for a, b in zip(items, items[1:]):
            ar = Arrow(a.get_right(), b.get_left(), buff=0.05, color=FG, stroke_width=3, max_tip_length_to_length_ratio=0.3)
            scene.play(FadeIn(b, shift=RIGHT * 0.2), GrowArrow(ar), run_time=0.35)
            arrows.append(ar)
        return arrows

    scene.play(FadeIn(row1[0]), run_time=0.3)
    a1 = chain(row1)
    a2 = [Arrow(row1[1].get_bottom(), submap.get_top(), buff=0.05, color=FG, stroke_width=3)]
    scene.play(FadeIn(submap), GrowArrow(a2[0]), run_time=0.4)
    scene.play(FadeIn(init), run_time=0.3)
    a3 = [Arrow(init.get_right(), pose.get_left(), buff=0.05, color=FG, stroke_width=3)]
    scene.play(FadeIn(pose), GrowArrow(a3[0]), run_time=0.4)
    scene.play(FadeIn(row3[0]), run_time=0.3)
    a4 = chain(row3)
    a5 = [Arrow(submap.get_bottom(), row3[3].get_top(), buff=0.05, color=FG, stroke_width=3),
          Arrow(pose.get_bottom(), row3[3].get_top() + LEFT * 0.3, buff=0.05, color=ACCENT, stroke_width=3)]
    scene.play(*[GrowArrow(a) for a in a5], run_time=0.4)
    # the result feeds the next frame's start pose
    back = Arrow(row3[3].get_left() + UP * 0.25, pose.get_bottom() + LEFT * 0.4, buff=0.05, color=ACCENT, stroke_width=2)
    scene.play(GrowArrow(back), run_time=0.3)
    return row1 + [init, submap, pose] + row3 + a1 + a2 + a3 + a4 + a5 + [back]


TA_CODE = """const auto input = FilterInputCloud(ScalePlyPointCloud(raw_cloud, ply_scale_));
const auto submap = CropSubmap(pose);
// ================= TODO: Localization =================
const bool converged =
    AlignNDT(input, submap, pose, candidate, score);"""

RUN_CODE = """colcon build
source install/setup.bash
ros2 launch localization localization.launch.py"""

CHAPTER = "c4_code"

BEATS = [
    ("Một lệnh ros2 launch. Đằng sau nó, dữ liệu đi qua những đâu?",
     [("title", "4", "Code của đề chạy thế nào", "một lệnh ros2 launch → bên trong có gì?")]),
    ("Có bốn file chính. localization.cpp là trái tim: đọc bản đồ, đọc từng point cloud, chạy NDT, ghi kết quả. "
     "map_modified.cpp là tuỳ chọn, để lọc và giảm mẫu bản đồ trước, mình chưa dùng. "
     "visualization.cpp vẽ kết quả lên RViz. Và txt_to_idx_x_y_yaw.py đổi file kết quả sang định dạng Kaggle.",
     [("custom", files)]),
    ("Dòng chảy dữ liệu thế này. Đầu tiên đọc map.pcd, giảm mẫu một mét, lưu lại bản nhỏ để lần sau đọc trong vài giây. "
     "Đọc pose ban đầu từ init_guess.txt. Với mỗi file ply: nhân tỉ lệ, giảm mẫu, cắt phần bản đồ quanh xe, "
     "chạy NDT bắt đầu từ pose frame trước, ghi ma trận ra file. Cuối cùng đổi sang CSV để nộp.",
     [("custom", dataflow)]),
    ("Đây là đúng chỗ TA để chữ TODO trong hàm RunLocalization: nhân tỉ lệ, lọc, cắt submap, rồi gọi NDT.",
     [("caption", "Code thật: TODO của TA trong RunLocalization()"), ("code", TA_CODE, "cpp", 20)]),
    ("Chạy trong Docker: build bằng colcon, source môi trường, rồi ros2 launch. Sửa code thì phải build lại.",
     [("caption", "Chạy (trong Docker)"), ("code", RUN_CODE, "bash", 26)]),
    ("Bản đồ đọc lần đầu mất khoảng một phút. Mỗi frame NDT vài giây. Chạy hết một track mất cỡ một, hai tiếng.",
     [("caption", "Mất bao lâu?"),
      ("bullets", ["Đọc bản đồ lần đầu: ~1 phút", "Mỗi frame NDT: vài giây", "Cả một track: ~1–2 tiếng ⏳"], 40, 1.3)]),
    ("Nhớ ba ý. Một: localization.cpp đọc bản đồ, rồi với từng frame thì nhân tỉ lệ, lọc, cắt submap, chạy NDT, ghi pose. "
     "Hai: điểm xuất phát mỗi frame là pose của frame trước. Ba: kết quả dạng ma trận trong file txt, "
     "đổi bằng txt_to_idx_x_y_yaw.py thành CSV để nộp Kaggle.",
     [("summary", ["localization.cpp: scale → lọc → submap → NDT → ghi pose",
                   "Điểm xuất phát = pose frame trước (template)",
                   ".txt (ma trận) → txt_to_idx_x_y_yaw.py → CSV"])]),
]

LINES = lines_of(BEATS)
SFX = default_sfx(BEATS)


class C4_Code(ScriptScene):
    CHAPTER = CHAPTER
    BEATS = BEATS
