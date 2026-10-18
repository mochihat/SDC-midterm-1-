"""Chương 5 (phần 1) – Mình đã làm gì: AI, baseline, GNSS, scale, Kalman."""
import os
import sys

from manim import DOWN, LEFT, RIGHT, UP, FadeIn, Line, VGroup

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from kit import ScriptScene, default_sfx, lines_of  # noqa: E402
from style import ACCENT, BLUE, FG, RED, T  # noqa: E402


def two_columns(scene):
    me = VGroup(T("👤 MÌNH", 40, ACCENT, "BOLD"),
                *[T(s, 26, FG) for s in ["tải dữ liệu, tạo token", "tự nộp 6 file GNSS đầu", "quyết định làm một mình",
                                          "cho phép chỉnh theo điểm Kaggle", "chạy hay dừng từng thí nghiệm"]])
    ai = VGroup(T("🤖 AI (Claude Code)", 40, BLUE, "BOLD"),
                *[T(s, 26, FG) for s in ["viết gần như toàn bộ code", "sửa localization.cpp + 20 script", "chạy thí nghiệm",
                                          "đề xuất hướng làm", "nộp phần lớn bài bằng script"]])
    for g in (me, ai):
        g.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
    me.move_to(LEFT * 3.5 + DOWN * 0.3)
    ai.move_to(RIGHT * 3.3 + DOWN * 0.3)
    sep = Line(UP * 2.4, DOWN * 3.0, color=FG, stroke_opacity=0.4)
    scene.play(FadeIn(sep), FadeIn(me[0], shift=DOWN * 0.2), FadeIn(ai[0], shift=DOWN * 0.2), run_time=0.4)
    for row in list(ai[1:]) + list(me[1:]):
        scene.play(FadeIn(row, shift=RIGHT * 0.3), run_time=0.25)
    return [sep, me, ai]


GIT_LOG = """65d10cb Original TA template + baseline/GNSS scripts
cd985a4 Add GNSS-prior guided NDT with gating, debug output, and fusion script
64fa10c Add docker setup and README
49de295 Add point cloud analysis tools (scale/axes), generate_result.py, PRIOR override
f66e1c1 Add CTRV RTS smoother with ML noise estimation
8b092ce Add lag-aware IMU smoother, yaw projection from yaw-only submissions, ...
116f7c0 Add start-segment yaw fix (gyro back-propagation) and position projection tool
77ea2a9 Add start_frame parameter and chunked parallel NDT runs
383e15f Add bump_yaw.py (time-windowed yaw probes)"""

DIFF = """-  Eigen::Matrix4f candidate = pose;
-  const bool converged = AlignNDT(input, submap, pose, candidate, score);
+  const PriorPose* prior = priors_.empty() ? nullptr : &priors_[index];
+  const Eigen::Matrix4f guess = prior ? PriorGuess(*prior, pose) : pose;
+  bool accepted = converged;
+  if (converged && prior) {
+      accepted = std::hypot(dx, dy) <= max_correction_xy_ &&
+                 std::abs(wrapped_dyaw) <= max_correction_yaw_deg_ * M_PI / 180.0;
+  }"""

CHAPTER = "c5a_work"

BEATS = [
    ("Bốn mươi bốn lượt nộp. Có lượt điểm tăng, có lượt tụt thê thảm. Đây là toàn bộ câu chuyện, kể cả chỗ dùng AI. "
     "Trước đó có hai lượt nộp thử chỉ để làm quen định dạng.",
     [("title", "5", "Mình đã làm gì", "44 lượt nộp 📈📉")]),
    ("Nói trước cho minh bạch. Mình làm bài với một trợ lý AI tên là Claude Code, chạy trong terminal Ubuntu. "
     "Mình đưa cho nó: link cuộc thi, slide đề, ảnh chụp màn hình lỗi, dữ liệu đã tải, và các yêu cầu bằng lời.",
     [("big", "🤖 Claude Code", "trợ lý AI chạy trong terminal Ubuntu", BLUE, 80),
      ("note", "input: link cuộc thi · slide đề · ảnh lỗi · dữ liệu · yêu cầu bằng lời", FG, 28)]),
    ("AI viết gần như toàn bộ code trong repo, từ sửa localization.cpp tới hai mươi script phân tích, chạy thí nghiệm, "
     "đề xuất hướng làm, và nộp phần lớn bài lên Kaggle bằng script. Phần mình: tải dữ liệu, tạo token, "
     "tự nộp sáu file GNSS đầu tiên, quyết định làm một mình, cho phép chỉnh theo điểm Kaggle, và quyết định chạy hay dừng từng thí nghiệm.",
     [("custom", two_columns)]),
    ("Đây là lịch sử commit thật. Mỗi commit là một bước thử.",
     [("caption", "git log --oneline (repo thật)"), ("code", GIT_LOG, "text", 18)]),
    ("Cách kiểm tra: mọi file đã nộp đều được tạo lại từ dữ liệu gốc bằng một script và so khớp từng byte. Ba mươi tư trên ba mươi tư file khớp.",
     [("big", "TẠO LẠI 34/34 FILE ✅", "so khớp từng byte với file đã nộp", BLUE, 76)]),
    ("Bước một: chạy baseline của TA. Kết quả: Track01 lệch chín mươi mốt mét, yaw lệch một trăm mười ba độ. "
     "Track02 lệch một trăm mười mét. Tức là xe quay ngược đầu và đi lạc sang khu khác.",
     [("caption", "Bước 1 – Baseline: lệch 91 m / 110 m 💀", RED), ("image", "baseline_vs_gnss.png", 5.4)]),
    ("Bước hai: GNSS, phao cứu sinh. Trong rosbag có một topic tên là localizer_node gnss_pose, cập nhật bốn lần mỗi giây. "
     "Thử nộp thẳng nó: Track01 được 1.31, Track02 được 0.57. Baseline là 1.79 và 1.93.",
     [("caption", "Bước 2 – GNSS: phao cứu sinh"),
      ("table", [["", "Track01", "Track02"], ["Baseline TA", "1.79", "1.93"], ["GNSS nộp thẳng", "1.31", "0.57"]], 40)]),
    ("Làm mượt thêm một chút: Track01 xuống 1.26. Thử lấy hướng chạy làm yaw: Track02 xuống 0.47, nhưng Track01 lại tệ đi. Mỗi track mỗi tính.",
     [("caption", "Thử thêm"),
      ("bullets", ["Làm mượt → T1: 1.26 ✅", "yaw = hướng chạy → T2: 0.47 ✅", "… nhưng T1 tệ đi ❌  (mỗi track mỗi tính)"],
       40, 1.3, {2: RED})]),
    ("Bước ba: phát hiện scale sai. Tại sao NDT lạc? Mình đo point cloud: mặt đường cách camera 0.18 đơn vị, ổn định trên cả hai track. "
     "Camera thật cao một mét sáu. Tỉ lệ đúng phải khoảng chín. Template để ba.",
     [("caption", "Bước 3 – Scale sai!"), ("image", "ply_side_scale.png", 4.6)]),
    ("Một mét sáu chia 0.18, xấp xỉ chín.",
     [("keep",), ("note", "1.6 m ÷ 0.18 ≈ 9   →   scale ×9 (template: ×3)", ACCENT, 40, DOWN * 3.3)]),
    ("Sửa thành chín, ô NDT bốn mét: chín mươi hai phần trăm khung hình Track02 chỉ lệch dưới một mét so với GNSS. "
     "Nhưng ghép vào GNSS thì điểm lại tệ hơn, 0.535. NDT ổn định rồi, nhưng chưa chính xác bằng GNSS.",
     [("caption", "Sửa scale ×9, ô NDT 4 m"), ("image", "ndt_corrections_hist.png", 4.4),
      ("note", "92 % frame < 1 m so với GNSS ✅   ·   ghép vào GNSS: 0.535 ❌", FG, 30)]),
    ("Đây là phần mình sửa trong localization.cpp: NDT bắt đầu từ GNSS đã làm mượt, và loại kết quả nếu lệch quá xa GNSS.",
     [("caption", "Code thật (git diff) – localization.cpp"), ("code", DIFF, "diff", 18)]),
    ("Bước bốn: bộ lọc Kalman. Thay vì làm mượt kiểu tuỳ ý, mình dùng bộ lọc Kalman với mô hình xe: "
     "xe chạy theo hướng mũi, tốc độ và tốc độ quay thay đổi từ từ.",
     [("big", "KALMAN + MÔ HÌNH XE", "CTRV: tốc độ & tốc độ quay đổi từ từ", ACCENT, 72)]),
    ("Độ nhiễu không đoán bừa, mà chọn sao cho mô hình giải thích dữ liệu GNSS tốt nhất, gọi là maximum likelihood. "
     "Kết quả: Track02 từ 0.47 xuống 0.408.",
     [("caption", "Độ nhiễu: maximum likelihood"), ("big", "T2: 0.47 → 0.408 ✅", None, BLUE, 84)]),
]

LINES = lines_of(BEATS)
SFX = default_sfx(BEATS)


class C5a_Work(ScriptScene):
    CHAPTER = CHAPTER
    BEATS = BEATS
