"""Chương 6 – Hướng cải thiện tiếp."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from kit import ScriptScene, default_sfx, lines_of  # noqa: E402
from style import BLUE  # noqa: E402

CHAPTER = "c6_next"

BEATS = [
    ("Còn cách hạng nhất. Vậy đào ở đâu tiếp?",
     [("title", "6", "Hướng cải thiện tiếp", "đào ở đâu tiếp? ⛏️")]),
    ("Một: NDT chỉ dùng ảnh còn trôi chín mét sau một trăm năm mươi frame, vì thiếu motion model và hướng ban đầu sai mười lăm độ. "
     "Thêm dự đoán vận tốc và thử nhiều góc ở frame đầu.",
     [("caption", "1. NDT chỉ dùng ảnh: trôi 9 m sau 150 frame"),
      ("big", "MOTION MODEL + THỬ NHIỀU GÓC", "hướng ban đầu sai 15°", BLUE, 64)]),
    ("Hai: chưa thử ICP, nhất là point-to-plane.",
     [("big", "2. ICP point-to-plane", "chưa thử", None, 76)]),
    ("Ba: tỉ lệ ba camera mới thử 0.8, 0.85 và 1.0. Còn thử được 0.7, 0.75, và ô NDT hai mét.",
     [("caption", "3. Tỉ lệ & độ phân giải"),
      ("bullets", ["Đã thử: 0.8 · 0.85 · 1.0", "Chưa thử: 0.7 · 0.75 · ô NDT 2 m"], 46, 1.0, {1: BLUE})]),
    ("Bốn: lỗi yaw còn lại thay đổi nhanh, dò theo đoạn mười lăm giây không bắt được. Có thể dùng gyro tốt hơn.",
     [("big", "4. YAW TẦN SỐ CAO ← GYRO", "dò theo đoạn 15 s không bắt được", None, 64)]),
    ("Năm: lọc outlier, bỏ mặt đường, mask nắp capo. Đề có gợi ý, nhưng mình chưa làm.",
     [("caption", "5. Tiền xử lý đề gợi ý (chưa làm)"),
      ("bullets", ["Lọc outlier", "Bỏ mặt đường", "Mask nắp capo"], 46, 1.3)]),
    ("Nhớ ba ý. Một: thuật toán chỉ dùng ảnh cần motion model. "
     "Hai: hướng sửa vị trí có hy vọng nhất là NDT ba camera với tỉ lệ và độ phân giải khác. "
     "Ba: các bước tiền xử lý đề gợi ý chưa được thử.",
     [("summary", ["Chỉ dùng ảnh → cần motion model",
                   "Có hy vọng nhất: NDT 3 camera, tỉ lệ/độ phân giải khác",
                   "Tiền xử lý đề gợi ý: chưa thử"])]),
]

LINES = lines_of(BEATS)
SFX = default_sfx(BEATS)


class C6_Next(ScriptScene):
    CHAPTER = CHAPTER
    BEATS = BEATS
