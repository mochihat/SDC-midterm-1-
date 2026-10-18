"""Chương 0 – Mở đầu."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from kit import ScriptScene, default_sfx, lines_of  # noqa: E402
from style import BLUE, RED  # noqa: E402

CHAPTER = "c0_intro"

BEATS = [
    ("Một chiếc xe. Ba cái camera. Một tấm bản đồ ba chiều to bằng cả khu phố.",
     [("image", "map_top_track1.png", 5.6)]),
    ("Câu hỏi: xe đang ở đâu? Chính xác tới từng chục xăng-ti-mét.",
     [("big", "XE ĐANG Ở ĐÂU?", "chính xác tới từng chục cm")]),
    ("Nghe dễ? Bài baseline của đề chạy xong… lạc mất gần một trăm mét.",
     [("image", "baseline_vs_gnss.png", 5.4)]),
    ("Video này giải thích từ con số không: bài toán là gì, cần kiến thức gì, "
     "và mình đã làm gì để điểm từ 1.79 xuống 1.05.",
     [("big", "1.79 → 1.05", "điểm Track01: baseline → bài của mình", BLUE)]),
    ("Mình chia làm tám chương: bức tranh lớn, vì sao đề ra như vậy, kiến thức nền – phần dài nhất, "
     "code của đề, mình đã làm gì kể cả chỗ dùng AI, hướng cải thiện, checklist nộp bài, và bảng thuật ngữ.",
     [("caption", "LỘ TRÌNH"),
      ("bullets", ["1. Bức tranh lớn", "2. Vì sao đề ra như vậy", "3. Kiến thức nền (dài nhất)",
                   "4. Code của đề", "5. Mình đã làm gì (kể cả dùng AI)", "6. Hướng cải thiện",
                   "7. Checklist nộp bài", "8. Tổng kết + thuật ngữ"], 32, 2.4, {4: RED})]),
]

LINES = lines_of(BEATS)
SFX = default_sfx(BEATS)


class C0_Intro(ScriptScene):
    CHAPTER = CHAPTER
    BEATS = BEATS
