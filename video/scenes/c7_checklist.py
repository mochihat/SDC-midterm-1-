"""Chương 7 – Checklist nộp bài và dàn ý báo cáo."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from kit import ScriptScene, default_sfx, lines_of  # noqa: E402
from style import ACCENT, BLUE, RED  # noqa: E402

CHAPTER = "c7_checklist"

BEATS = [
    ("Làm hay mà nộp thiếu file thì cũng như không.",
     [("title", "7", "Checklist nộp bài", "nộp thiếu file = như không 📦")]),
    ("Kaggle đóng lúc chín giờ sáng ngày hai mươi chín tháng mười. Nhớ kiểm tra bài nào được chọn để chấm. "
     "E3 hạn mười một giờ năm mươi chín tối ngày năm tháng mười một.",
     [("caption", "Hạn chót ⏰"),
      ("table", [["", "Hạn"], ["Kaggle", "29/10 09:00"], ["E3", "05/11 23:59"]], 48)]),
    ("File zip gồm thư mục localization không kèm dữ liệu, result_1.csv, result_2.csv, báo cáo PDF và README cách chạy.",
     [("caption", "File zip nộp E3"),
      ("bullets", ["📁 localization/ (không kèm dữ liệu)", "📄 result_1.csv · result_2.csv", "📕 report.pdf",
                   "📘 README (cách chạy)"], 42, 1.6)]),
    ("Làm một mình thì tên file chỉ có một mã số sinh viên, nên hỏi TA cho chắc.",
     [("big", "1 người → hỏi TA cách đặt tên", None, ACCENT, 66)]),
    ("Báo cáo ba mươi điểm, có bốn phần. Pipeline: chương trình chạy thế nào. "
     "Contributions: đóng góp của bạn, như phát hiện scale, NDT có prior, Kalman, NDT ba camera.",
     [("caption", "Báo cáo (30 điểm)"),
      ("bullets", ["Pipeline – chương trình chạy thế nào",
                   "Contributions – scale, NDT có prior, Kalman, NDT 3 camera"], 38, 1.6)]),
    ("Problems and Solutions: baseline lạc, yaw GNSS trễ, xe đứng yên. "
     "Workload: làm một mình, và ghi rõ phần nào AI hỗ trợ, phần nào chọn theo điểm Kaggle.",
     [("caption", "Báo cáo (tiếp)"),
      ("bullets", ["Problems & Solutions – baseline lạc, yaw trễ, xe đứng yên",
                   "Workload – một mình; ghi rõ AI + chọn theo điểm Kaggle"], 38, 1.6, {1: BLUE})]),
    ("Nhớ: dùng mã nguồn mở mà không sửa gì đáng kể thì phần đóng góp bằng không.",
     [("big", "⚠️ OPEN-SOURCE KHÔNG SỬA", "= 0 điểm đóng góp", RED, 70)]),
    ("Nhớ ba ý. Một: Kaggle đóng chín giờ sáng hai mươi chín tháng mười, E3 hạn mười một giờ năm mươi chín tối năm tháng mười một. "
     "Hai: file zip gồm code không kèm dữ liệu, result_1, result_2, PDF và README. "
     "Ba: báo cáo ghi rõ phần AI và phần chọn theo điểm Kaggle.",
     [("summary", ["Kaggle 29/10 09:00 · E3 05/11 23:59",
                   "Zip: code (không data) + result_1/2.csv + PDF + README",
                   "Báo cáo ghi rõ AI + chọn theo điểm Kaggle"])]),
]

LINES = lines_of(BEATS)
SFX = default_sfx(BEATS)


class C7_Checklist(ScriptScene):
    CHAPTER = CHAPTER
    BEATS = BEATS
