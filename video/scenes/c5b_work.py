"""Chương 5 (phần 2) – File thăm dò, yaw GNSS, chọn theo điểm Kaggle, NDT 3 camera, bài học."""
import os
import sys

import numpy as np
from manim import DOWN, LEFT, RIGHT, UP, Arc, Arrow, FadeIn, Rectangle, RoundedRectangle, SurroundingRectangle, VGroup

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from kit import ScriptScene, default_sfx, lines_of  # noqa: E402
from style import ACCENT, BLUE, FG, RED, T  # noqa: E402


def loop(scene):
    steps = ["THỬ", "NỘP", "XEM ĐIỂM", "GIỮ CÁI TỐT"]
    colors = [BLUE, ACCENT, RED, BLUE]
    R = 2.2
    nodes = []
    for k, (s, c) in enumerate(zip(steps, colors)):
        ang = np.pi / 2 - k * np.pi / 2
        pos = np.array([R * 1.4 * np.cos(ang), R * np.sin(ang) - 0.3, 0])
        r = RoundedRectangle(corner_radius=0.2, width=3.2, height=0.9, color=c, fill_opacity=0.15).move_to(pos)
        nodes.append(VGroup(r, T(s, 32, c, "BOLD").move_to(r)))
    arcs = []
    for k in range(4):
        a, b = nodes[k], nodes[(k + 1) % 4]
        arcs.append(Arrow(a.get_center(), b.get_center(), buff=0.75, color=FG, stroke_width=3,
                          path_arc=-np.pi / 3))
    for n, a in zip(nodes, arcs):
        scene.play(FadeIn(n, scale=0.8), run_time=0.3)
        scene.play(FadeIn(a), run_time=0.2)
    return nodes + arcs


def weights(scene):
    rows = [["Hướng (Track02, yawproj_v3_2)", "Trọng số"],
            ["#21 − base", "−4.581"], ["#23 − base", "−0.205"], ["#26 − base", "−1.119"], ["#27 − base", "+0.499"]]
    group = scene.el_table(rows, 34)[0]
    cell = group[1 * 2 + 1]
    cell.set_color(RED)
    ring = SurroundingRectangle(cell, color=RED, buff=0.15, corner_radius=0.1)
    scene.play(FadeIn(ring, scale=1.3), run_time=0.3)
    lab = T("không có ý nghĩa vật lý – thuần khớp theo đáp án", 28, RED).to_edge(DOWN, buff=0.6)
    scene.play(FadeIn(lab), run_time=0.3)
    return [group, ring, lab]


CHAPTER = "c5b_work"

BEATS = [
    ("Bước năm: file thăm dò. Một mẹo hay: cố tình nộp file sai có chủ đích. "
     "Dịch thời gian cộng trừ 0.1 giây. Dời ngang cộng trừ nửa mét. Xoay yaw cộng trừ một độ.",
     [("caption", "Bước 5 – Nộp sai có chủ đích 🎯"),
      ("bullets", ["⏱️ dịch thời gian ±0.1 s", "↔️ dời ngang ±0.5 m", "🔄 xoay yaw ±1°"], 44, 1.3)]),
    ("Xem điểm thay đổi bao nhiêu, giải ngược ra: Track01 sai vị trí 0.905 mét, sai góc 1.77 độ.",
     [("big", "T1 = 0.905 m + 1.77°", "giải ngược từ điểm số", ACCENT, 84)]),
    ("Ba nhóm thăm dò cho cùng một đáp số. Và công thức dự đoán điểm của bài tiếp theo là 1.25339. Thực tế: 1.25338.",
     [("caption", "Kiểm chứng"),
      ("bullets", ["Dự đoán: 1.25339", "Thực tế: 1.25338 🤯"], 60, 1.2, {0: FG, 1: BLUE})]),
    ("Bước sáu: bí mật của yaw GNSS. Soi kỹ thì lộ ra: góc yaw chỉ thay đổi khoảng 1.25 giây một lần. "
     "Và nó được tính từ chính vị trí GNSS trong một giây trước đó. Nên nó trễ.",
     [("caption", "Bước 6 – yaw GNSS: 1.25 s mới đổi 1 lần ⏱️"), ("image", "gnss_yaw_staircase_t2.png", 5.2)]),
    ("Tệ nhất: khi xe đứng yên, nó đóng băng. Track02 mười ba giây đầu: GNSS báo âm mười lăm độ, góc thật khoảng âm hai mươi độ.",
     [("big", "ĐỨNG YÊN → ĐÓNG BĂNG ❄️", "T2, 13 s đầu: GNSS −15° · thật ≈ −20°", RED, 72)]),
    ("Mình dựng lại góc lúc đứng yên bằng con quay hồi chuyển, gyro, trong IMU. Track02 xuống 0.335.",
     [("big", "GYRO CỨU: T2 0.335 ✅", "dựng lại yaw đoạn đứng yên", BLUE, 80)]),
    ("Nhưng có một cú lừa: bù độ trễ cho đúng vật lý lại làm điểm tệ đi. Đáp án không dùng hướng chạy đúng giờ. "
     "Đúng với dữ liệu chưa chắc đúng với đáp án.",
     [("big", "BÙ TRỄ 'ĐÚNG VẬT LÝ' → TỆ HƠN ❌", "đúng với dữ liệu ≠ đúng với đáp án", RED, 60)]),
    ("Tới phần nhạy cảm. Chọn theo điểm Kaggle nghĩa là: làm nhiều phiên bản, nộp lên, xem điểm, giữ cái tốt hơn.",
     [("caption", "\"Chọn theo điểm Kaggle\" là gì?"), ("custom", loop)]),
    ("Bản nâng cao mình dùng: giữ nguyên vị trí, chỉ đổi yaw. Khi đó mỗi lượt nộp cho biết chính xác cái thay đổi đó tốt hay xấu bao nhiêu. "
     "Có vài lượt như vậy là giải được phương trình, ra tổ hợp tốt nhất, không cần nộp thử thêm. "
     "Dự đoán khớp điểm thật tới khoảng một phần nghìn.",
     [("caption", "Bản nâng cao: giữ vị trí, chỉ đổi yaw"),
      ("bullets", ["Mỗi lượt nộp = 1 phương trình", "Vài lượt → giải ra tổ hợp tốt nhất",
                   "Dự đoán khớp điểm thật ~0.001"], 40, 1.3, {2: BLUE})]),
    ("Ưu điểm: điểm lên nhanh, đo được những thứ dữ liệu không nói.",
     [("big", "✅ NHANH", "đo được những thứ dữ liệu không nói", BLUE, 90)]),
    ("Rủi ro thì phải nói thẳng. Một: leaderboard ở đây chấm trên toàn bộ dữ liệu test, không có bảng điểm ẩn. "
     "Chỉnh theo điểm là khớp thẳng vào đáp án, không phải thuật toán giỏi hơn.",
     [("big", "⚠️ KHỚP ĐÁP ÁN", "không phải thuật toán giỏi hơn", RED, 84)]),
    ("Trọng số tìm được nhiều khi vô nghĩa về vật lý, ví dụ âm bốn phẩy năm tám.",
     [("custom", weights)]),
    ("Hai: tốn lượt, mỗi hướng một lượt, mười lăm lượt mỗi ngày. Ba: báo cáo chấm đóng góp gốc, nên phải ghi rõ phần nào chọn theo điểm.",
     [("caption", "Rủi ro (tiếp)", RED),
      ("bullets", ["⚠️ tốn lượt: 1 hướng = 1 lượt, 15 lượt/ngày", "⚠️ báo cáo chấm đóng góp gốc → ghi rõ phần chọn theo điểm"],
       38, 0.9)]),
    ("Bước bảy: NDT ba camera, lần đầu thắng GNSS. Track01 sai chủ yếu ở vị trí, chín mươi phân. Cần nguồn vị trí mới. "
     "Thử NDT với point cloud ba camera. Tỉ lệ 1.0: tệ đi. Tỉ lệ 0.8: lỗi vị trí từ 0.905 xuống 0.836 mét.",
     [("caption", "Bước 7 – NDT 3 camera"),
      ("bullets", ["scale ×1.0 → tệ đi ❌", "scale ×0.8 → 0.905 → 0.836 m ✅"], 50, 1.0, {0: RED, 1: BLUE})]),
    ("Tỉ lệ 0.8 ứng với camera cao khoảng một mét sáu lăm, khớp với tỉ lệ chín của LoGeR. Hai nguồn độc lập cho cùng một chiều cao camera. "
     "Đây là lần đầu scan matching thật sự sửa được GNSS.",
     [("big", "camera ≈ 1.65 m ✔︎", "khớp với ×9 của LoGeR – hai nguồn độc lập", ACCENT, 80)]),
    ("Kết hợp các hướng theo điểm Kaggle: Track01 xuống 1.054, Track02 xuống 0.299, hạng hai. Đây là toàn bộ hành trình điểm số.",
     [("caption", "T1: 1.054 · T2: 0.299 (hạng 2) 🥈"), ("image", "score_timeline.png", 5.4)]),
    ("Bài học. Kiểm tra dữ liệu đầu vào trước khi chạy thí nghiệm dài, bài này mất cả tiếng vì tỉ lệ sai. "
     "Một thước đo có thể thiên vị, lần đầu đo tỉ lệ, mình đo sai vì thế. "
     "Giả thuyết đẹp chưa chắc đúng với đáp án, chỉ một lượt nộp mới trả lời được. Và ghi lại mọi thứ để tạo lại được từng file.",
     [("caption", "Bài học"),
      ("bullets", ["1. Kiểm tra input trước 🔍", "2. Thước đo có thể lừa 🎭", "3. Giả thuyết đẹp ≠ đúng",
                   "4. Ghi lại mọi thứ 📒"], 42, 1.6)]),
    ("Nhớ ba ý. Một: lỗi lớn nhất của template là scale nhân ba, đúng phải khoảng chín cho LoGeR, khoảng 0.8 cho ba camera. "
     "Hai: GNSS cộng Kalman mạnh nhất, NDT ba camera tỉ lệ 0.8 là lần đầu scan matching thắng GNSS. "
     "Ba: phần lớn điểm cuối đến từ chọn theo điểm Kaggle, hiệu quả, nhưng phải ghi rõ, và không phải thuật toán giỏi hơn.",
     [("summary", ["Lỗi lớn nhất: scale ×3 (đúng ≈ 9 LoGeR, ≈ 0.8 3 camera)",
                   "GNSS + Kalman mạnh nhất; NDT 3 camera ×0.8 thắng GNSS",
                   "Điểm cuối nhờ chọn theo điểm Kaggle → phải ghi rõ"])]),
]

LINES = lines_of(BEATS)
SFX = default_sfx(BEATS)


class C5b_Work(ScriptScene):
    CHAPTER = CHAPTER
    BEATS = BEATS
