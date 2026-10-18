"""Chương 3.4 – Chiều sâu từ ảnh và chuyện scale."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from kit import ScriptScene, default_sfx, lines_of  # noqa: E402
from style import BLUE, RED  # noqa: E402

CHAPTER = "c3_04_scale"

BEATS = [
    ("Món thứ tư: chuyện tỉ lệ, scale. LoGeR nhận ảnh camera trước, đoán chiều sâu, dựng thành point cloud.",
     [("title", "3.4", "Chiều sâu từ ảnh & SCALE")]),
    ("Nhưng một camera thì không biết tỉ lệ thật. Mô hình có thể dựng đúng hình dạng nhưng sai kích thước cả mấy lần.",
     [("big", "1 CAMERA", "→ đúng hình dạng, SAI kích thước")]),
    ("Ví dụ thật trong bài. Trong point cloud của LoGeR, mặt đường nằm thấp hơn camera đúng 0.18 đơn vị. "
     "Ngoài đời, camera cao khoảng một mét sáu.",
     [("image", "ply_side_scale.png", 5.0)]),
    ("Vậy phải nhân cả đám điểm lên khoảng chín lần mới đúng kích thước thật. Code mẫu của đề lại nhân ba lần.",
     [("big", "×9  (template: ×3)", "1.6 m ÷ 0.18 ≈ 9", RED, 80)]),
    ("MapAnything dùng ba camera nên gần đúng mét hơn: mặt đường cách camera khoảng hai mét. "
     "Nhưng thử thực tế, nhân 0.8 mới khớp tốt nhất.",
     [("caption", "Hai nguồn point cloud"),
      ("bullets", ["raw_ply (LoGeR): mặt đường 0.18 đơn vị → scale ≈ 9",
                   "3cameras_ply (MapAnything): ~2 m → scale tốt nhất ≈ 0.8",
                   "Cả hai cùng ra camera cao ~1.6 m"], 36, 1.2, {0: BLUE, 1: RED})]),
]

LINES = lines_of(BEATS)
SFX = default_sfx(BEATS)


class C3_04_Scale(ScriptScene):
    CHAPTER = CHAPTER
    BEATS = BEATS
