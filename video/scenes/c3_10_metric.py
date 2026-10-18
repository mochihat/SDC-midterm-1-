"""Chương 3.10 – Thước đo: RMSE của ATE."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from kit import ScriptScene, default_sfx, lines_of  # noqa: E402
from style import BLUE, FG  # noqa: E402

CHAPTER = "c3_10_metric"

BEATS = [
    ("Món thứ mười: chấm điểm thế nào?",
     [("title", "3.10", "Thước đo: RMSE của ATE")]),
    ("Với mỗi frame, lấy vị trí bạn nộp trừ vị trí đáp án, được sai số delta p, tính bằng mét. "
     "Lấy góc bạn nộp trừ góc đáp án, được delta theta, tính bằng độ.",
     [("caption", "Sai số từng frame"),
      ("formula", r"\Delta p_i = \hat p_i - p_i^{*}\ (\text{m}),\qquad "
                  r"\Delta\theta_i = \hat\theta_i - \theta_i^{*}\ (^\circ)", 52),
      ("note", "dấu ^ = giá trị bạn nộp  ·  dấu * = đáp án", FG, 32)]),
    ("Bình phương, lấy trung bình, rồi căn bậc hai, đó là RMSE. Điểm bằng RMSE vị trí cộng 0.2 lần RMSE góc. Càng thấp càng tốt.",
     [("caption", "ĐIỂM (càng thấp càng tốt)"),
      ("formula", r"E=\sqrt{\tfrac1n\sum_i\lVert\Delta p_i\rVert^2}\;+\;0.2\,\sqrt{\tfrac1n\sum_i\Delta\theta_i^2}", 52)]),
    ("Nghĩa là sai một độ thì bị cộng 0.2 điểm, tương đương sai hai mươi phân vị trí.",
     [("big", "1° = 0.2 điểm = 20 cm", None, BLUE, 80)]),
    ("Ví dụ thật: một bài nộp của mình sai vị trí 0.905 mét, sai góc 1.57 độ. Điểm bằng 0.905 cộng 0.2 nhân 1.57, khoảng 1.22.",
     [("caption", "Ví dụ thật (Track01)"),
      ("formula", r"0.905 + 0.2\times 1.57 \approx 1.22", 64)]),
]

LINES = lines_of(BEATS)
SFX = default_sfx(BEATS)


class C3_10_Metric(ScriptScene):
    CHAPTER = CHAPTER
    BEATS = BEATS
