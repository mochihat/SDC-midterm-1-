"""Chương 8 – Tổng kết và bảng thuật ngữ."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from kit import ScriptScene, lines_of  # noqa: E402
from style import ACCENT, BLUE  # noqa: E402

GLOSSARY = [
    ("Localization", "định vị – tìm vị trí và hướng của xe"),
    ("Pose / 6DoF", "tư thế – vị trí + hướng / 6 bậc tự do"),
    ("Frame (map, base_link, camera)", "hệ toạ độ gắn với bản đồ / thân xe / camera"),
    ("Rotation, translation", "phép xoay, phép dịch"),
    ("Homogeneous matrix", "ma trận đồng nhất 4×4"),
    ("Roll, pitch, yaw", "nghiêng ngang, chúc đầu, quay trái-phải"),
    ("Quaternion", "biểu diễn phép xoay bằng 4 số"),
    ("Gimbal lock", "hiện tượng \"kẹt\" của góc Euler"),
    ("Point cloud", "đám điểm 3D"),
    ("Voxel grid", "lưới hộp để giảm mẫu"),
    ("Outlier", "điểm lạc loài"),
    ("Scale ambiguity", "không xác định được tỉ lệ"),
    ("Scan matching / registration", "khớp đám điểm"),
    ("ICP (Iterative Closest Point)", "khớp bằng ghép cặp điểm gần nhất, lặp"),
    ("Correspondence", "cặp điểm tương ứng"),
    ("NDT (Normal Distributions Transform)", "khớp bằng các ô phân phối chuẩn"),
    ("Local minimum", "cực tiểu cục bộ"),
    ("Initial guess", "điểm xuất phát"),
    ("Motion model", "mô hình chuyển động"),
    ("GNSS", "hệ thống định vị vệ tinh (GPS là một loại)"),
    ("IMU, gyro", "bộ đo quán tính, con quay hồi chuyển"),
    ("Sensor fusion", "trộn dữ liệu cảm biến"),
    ("Kalman filter / RTS smoother", "bộ lọc Kalman / làm mượt hai chiều"),
    ("Maximum likelihood", "chọn tham số giải thích dữ liệu tốt nhất"),
    ("Node, topic, message, rosbag", "thành phần ROS 2"),
    ("ATE, RMSE", "sai số quỹ đạo tuyệt đối, căn trung bình bình phương"),
    ("Leaderboard", "bảng xếp hạng"),
    ("Overfit", "khớp quá mức vào dữ liệu đã thấy"),
]
PAGE = 6
PAGES = [GLOSSARY[i:i + PAGE] for i in range(0, len(GLOSSARY), PAGE)]
SPOKEN = ["một", "hai", "ba", "bốn", "năm", "sáu"]


def glossary_beat(k, page):
    terms = ", ".join(en.split(" (")[0] for en, _ in page)
    line = f"Bảng thuật ngữ, trang {SPOKEN[k]}: {terms}."
    rows = [["Tiếng Anh", "Tiếng Việt / giải thích"]] + [[en, vi] for en, vi in page]
    return (line, [("caption", f"Thuật ngữ Việt – Anh ({k + 1}/{len(PAGES)})"), ("table", rows, 28)])


CHAPTER = "c8_end"

BEATS = [
    ("Tóm tắt cả video. Localization là tìm pose của xe.",
     [("title", "8", "Tổng kết", "cả video trong 4 dòng")]),
    ("Năm nay dùng ảnh: point cloud từ ảnh có scale sai, nhiễu, méo. "
     "Khớp nó vào bản đồ bằng ICP hoặc NDT, cần điểm xuất phát tốt và scale đúng. "
     "GNSS và bộ lọc Kalman cho nền vững. NDT ba camera sửa được vị trí. "
     "Chọn theo điểm Kaggle đưa điểm xuống thêm, nhưng phải minh bạch.",
     [("caption", "Tóm tắt"),
      ("bullets", ["Localization = tìm pose của xe",
                   "Point cloud từ ảnh: scale sai, nhiễu, méo",
                   "ICP / NDT: cần điểm xuất phát tốt + scale đúng",
                   "GNSS + Kalman · NDT 3 camera · chọn theo điểm (minh bạch)"],
       40, 1.8, {3: BLUE})]),
    *[glossary_beat(k, p) for k, p in enumerate(PAGES)],
    ("Vậy là hết. Nếu bạn hiểu được tại sao nhân ba là sai và nhân chín là đúng, bạn đã hiểu bài này hơn phần lớn mọi người. "
     "Hẹn gặp ở midterm sau.",
     [("big", "×3 ❌ → ×9 ✅", "THE END 🎬", ACCENT, 110)]),
]

LINES = lines_of(BEATS)
SFX = {0: [("whoosh", 0.0)], 1: [("pop", 0.0)], **{2 + k: [("pop", 0.0)] for k in range(len(PAGES))},
       len(BEATS) - 1: [("ding", 0.3), ("whoosh", 3.0)]}


class C8_End(ScriptScene):
    CHAPTER = CHAPTER
    BEATS = BEATS
