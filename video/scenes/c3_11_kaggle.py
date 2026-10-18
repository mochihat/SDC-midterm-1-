"""Chương 3.11 – Kaggle, và tóm tắt chương 3."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from kit import ScriptScene, default_sfx, lines_of  # noqa: E402

CSV_EXAMPLE = """idx,x,y,yaw
0,-4800.720977,2274.626087,2.323874
1,-4800.725199,2274.632284,2.323874
2,-4800.729455,2274.638531,2.323874"""

CHAPTER = "c3_11_kaggle"

BEATS = [
    ("Món cuối của phần nền: Kaggle. Bài được nộp lên Kaggle bằng một file CSV bốn cột: idx, x, y, yaw – "
     "yaw bằng radian, mỗi frame một dòng.",
     [("title", "3.11", "Kaggle"), ("keep",)]),
    ("Đây là vài dòng đầu của một file mình đã nộp.",
     [("caption", "File nộp (CSV)"), ("code", CSV_EXAMPLE, "text", 28)]),
    ("Thiếu dòng là bị lỗi. Mình từng nộp nhầm file Track01 vào Track02 và bị báo lỗi đúng như vậy: "
     "file có 3011 dòng nhưng cần 3299.",
     [("big", "3011 dòng ≠ 3299 dòng", "nộp nhầm track → lỗi"),]),
    ("Mỗi track tối đa mười lăm lượt mỗi ngày. Ngày mới tính theo giờ quốc tế UTC, tức tám giờ sáng ở Đài Loan, bảy giờ sáng ở Việt Nam.",
     [("caption", "Luật nộp"),
      ("bullets", ["15 lượt / ngày / track", "Ngày mới: 00:00 UTC = 08:00 Đài Loan = 07:00 Việt Nam"], 38, 0.9)]),
    ("Leaderboard cuộc thi này chấm trên toàn bộ dữ liệu test. Nhớ chi tiết này, chương năm sẽ cần.",
     [("big", "LEADERBOARD = TOÀN BỘ TEST", "nhớ chi tiết này cho chương 5", None, 60)]),
    ("Tóm tắt phần kiến thức nền, nhớ ba ý. Một: pose là ma trận bốn nhân bốn, gồm xoay R và dịch t, nhưng Kaggle chỉ chấm x, y, yaw. "
     "Hai: scan matching như ICP hay NDT khớp point cloud vào bản đồ, nhưng cần điểm xuất phát tốt và scale đúng. "
     "Ba: điểm bằng RMSE vị trí cộng 0.2 lần RMSE góc tính bằng độ, càng thấp càng tốt.",
     [("summary", ["Pose = ma trận 4×4 (R, t); Kaggle chấm x, y, yaw",
                   "ICP/NDT cần điểm xuất phát tốt + scale đúng",
                   "Điểm = RMSE vị trí + 0.2 × RMSE góc (độ)"])]),
]

LINES = lines_of(BEATS)
SFX = default_sfx(BEATS)


class C3_11_Kaggle(ScriptScene):
    CHAPTER = CHAPTER
    BEATS = BEATS
