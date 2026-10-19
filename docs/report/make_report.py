"""Build the personal summary report (PDF, Vietnamese) from the process log and the Kaggle submission history.

Run inside the sdc-video image (matplotlib, Noto fonts) after `pip install reportlab==4.2.5`:
  python3 docs/report/make_report.py
Writes docs/report/bao_cao_tong_hop.pdf and the figures in docs/report/fig/.
"""
import csv
import datetime as dt
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_CENTER  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402
from reportlab.lib.units import cm  # noqa: E402
from reportlab.pdfbase import pdfmetrics  # noqa: E402
from reportlab.pdfbase.ttfonts import TTFont  # noqa: E402
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,  # noqa: E402
                                TableStyle)

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
FIG = os.path.join(HERE, "fig")
VIDEO_FIG = os.path.join(REPO, "video", "assets", "figures")
HISTORY = os.path.join(REPO, "docs", "nhat-ky", "data", "kaggle_submissions.csv")
OUT = os.path.join(HERE, "bao_cao_tong_hop.pdf")

FONT_DIR = "/usr/share/fonts/truetype/noto"
pdfmetrics.registerFont(TTFont("Noto", os.path.join(FONT_DIR, "NotoSans-Regular.ttf")))
pdfmetrics.registerFont(TTFont("Noto-Bold", os.path.join(FONT_DIR, "NotoSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("Noto-Italic", os.path.join(FONT_DIR, "NotoSans-Italic.ttf")))
pdfmetrics.registerFont(TTFont("Noto-BoldItalic", os.path.join(FONT_DIR, "NotoSans-BoldItalic.ttf")))
pdfmetrics.registerFontFamily("Noto", normal="Noto", bold="Noto-Bold", italic="Noto-Italic", boldItalic="Noto-BoldItalic")
pdfmetrics.registerFont(TTFont("DejaVu", os.path.join(matplotlib.get_data_path(), "fonts", "ttf", "DejaVuSans.ttf")))
SYMBOLS = "≈≤≥→−±"  # not in Noto Sans: drawn with DejaVu Sans


def sym(text):
    return "".join(f'<font name="DejaVu">{c}</font>' if c in SYMBOLS else c for c in str(text))
plt.rcParams.update({"font.family": ["Noto Sans", "DejaVu Sans"], "axes.unicode_minus": False, "font.size": 10})

INK, ACCENT, MUTED, OK, BAD = "#1f2a44", "#2f6fb0", "#6b7280", "#2e7d32", "#c62828"
BODY = ParagraphStyle("body", fontName="Noto", fontSize=10, leading=14.5, textColor=colors.HexColor(INK), spaceAfter=5)
SMALL = ParagraphStyle("small", parent=BODY, fontSize=8.5, leading=11.5, spaceAfter=2)
CELL = ParagraphStyle("cell", parent=BODY, fontSize=8.6, leading=11.2, spaceAfter=0)
CELL_B = ParagraphStyle("cellb", parent=CELL, fontName="Noto-Bold")
H1 = ParagraphStyle("h1", parent=BODY, fontName="Noto-Bold", fontSize=15, leading=19, spaceBefore=10, spaceAfter=8,
                    textColor=colors.HexColor(ACCENT), keepWithNext=1)
H2 = ParagraphStyle("h2", parent=BODY, fontName="Noto-Bold", fontSize=11.5, leading=15, spaceBefore=8, spaceAfter=4,
                    keepWithNext=1)
TITLE = ParagraphStyle("title", parent=BODY, fontName="Noto-Bold", fontSize=22, leading=28, alignment=TA_CENTER)
SUB = ParagraphStyle("sub", parent=BODY, fontSize=11.5, leading=16, alignment=TA_CENTER, textColor=colors.HexColor(MUTED))
BULLET = ParagraphStyle("bullet", parent=BODY, leftIndent=12, bulletIndent=2, spaceAfter=3)
CAPTION = ParagraphStyle("cap", parent=SMALL, textColor=colors.HexColor(MUTED), alignment=TA_CENTER, spaceAfter=8)


# ---------------------------------------------------------------------------------------------- figures
def load_history():
    rows = []
    for r in csv.DictReader(open(HISTORY)):
        try:
            score = float(r["public_score"])
        except ValueError:
            continue
        if score > 50:  # the two format trials before the work started
            continue
        rows.append((int(r["track"]), dt.datetime.strptime(r["time_utc+8"], "%Y-%m-%d %H:%M"), score, r["file"]))
    return sorted(rows, key=lambda v: v[1])


def fig_timeline(hist):
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
    leaders = {1: 0.57658, 2: 0.23178}
    baselines = {1: 1.79075, 2: 1.92587}
    for ax, track in zip(axes, (1, 2)):
        pts = [(t, s) for tr, t, s, _ in hist if tr == track]
        best, xs, ys = 9e9, [], []
        for t, s in pts:
            best = min(best, s)
            xs.append(t)
            ys.append(best)
        ax.scatter([t for t, _ in pts], [s for _, s in pts], s=9, color="#b8c2d6", label="từng lượt nộp", zorder=2)
        ax.step(xs, ys, where="post", color=ACCENT, lw=2, label="tốt nhất đến lúc đó", zorder=3)
        ax.axhline(baselines[track], color=MUTED, ls="--", lw=1)
        ax.text(xs[0], baselines[track], " baseline TA", va="bottom", fontsize=8, color=MUTED)
        ax.axhline(leaders[track], color=BAD, ls=":", lw=1.2)
        ax.text(xs[0], leaders[track], " hạng 1 (đội 12, 19/10)", va="top", fontsize=8, color=BAD)
        ax.set_ylim(0, 2.0)
        ax.set_title(f"Track0{track}: điểm (càng thấp càng tốt)")
        ax.set_xlabel("thời gian (17/10 → 19/10)")
        ax.tick_params(axis="x", labelrotation=30, labelsize=8)
        ax.grid(alpha=0.3)
        ax.annotate(f"{ys[-1]:.5f}", (xs[-1], ys[-1]), xytext=(-8, 22), textcoords="offset points", ha="right",
                    fontsize=9, color=ACCENT, fontweight="bold", arrowprops=dict(arrowstyle="-", color=ACCENT, lw=0.8))
    axes[0].legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    path = os.path.join(FIG, "timeline.png")
    fig.savefig(path, dpi=170)
    plt.close(fig)
    return path


def fig_yaw():
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.3))
    t1 = {"gyro chiếu trọng lực + hệ số trượt": ([10, 15, 30], [0.899, 0.953, 1.085]),
          "gyro trục z, không hiệu chỉnh trượt": ([7, 10], [0.866, 0.877])}
    t2 = {"gyro chiếu trọng lực + hệ số trượt": ([2, 5, 15], [0.429, 0.393, 0.303]),
          "gyro trục z, không hiệu chỉnh trượt": ([10, 15, 30], [0.264, 0.249, 0.268])}
    for ax, data, old, name in ((axes[0], t1, 1.559, "Track01"), (axes[1], t2, 0.360, "Track02")):
        for (label, (x, y)), c in zip(data.items(), (MUTED, ACCENT)):
            ax.plot(x, y, "o-", color=c, label=label)
        ax.axhline(old, color=BAD, ls="--", lw=1)
        ax.text(31, old, "yaw cũ (tổ hợp chọn theo điểm) ", va="bottom", ha="right", fontsize=8, color=BAD)
        ax.set_xlabel("τ – độ dài làm mượt phần hướng chạy (giây)")
        ax.set_ylabel("lỗi yaw RMSE (độ)")
        ax.set_title(f"{name}: yaw = gyro + hướng chạy (bộ lọc bù)")
        ax.grid(alpha=0.3)
        ax.set_xlim(0, 32)
        ax.set_ylim(0, max([old] + [v for _, ys in data.values() for v in ys]) * 1.15)
        ax.legend(fontsize=7.5, loc="lower right")
    fig.tight_layout()
    path = os.path.join(FIG, "yaw_tau.png")
    fig.savefig(path, dpi=170)
    plt.close(fig)
    return path


def fig_positions():
    items = [("GNSS + Kalman (nền)", 0.905), ("NDT 3 camera, tỉ lệ 1.0", 0.934), ("NDT 3 camera, tỉ lệ 0.8", 0.836),
             ("GICP, tỉ lệ 0.8", 0.803), ("NDT → GICP, tỉ lệ 0.8", 0.769), ("GICP, tỉ lệ theo mặt đường (1/4 frame)", 0.752),
             ("GICP, tỉ lệ theo mặt đường, mọi frame", 0.714), ("ICP 3 bậc tự do (x, y, yaw)", 0.719),
             ("ICP point-to-plane", 0.681), ("GICP lượt 2", 0.679), ("GICP lượt 2 + trừ độ lệch", 0.616),
             ("GICP lượt 5 (lặp quá nhiều)", 0.801), ("+ nắp capo + lọc điểm lạc", 0.764)]
    fig, ax = plt.subplots(figsize=(9.5, 4.4))
    names = [n for n, _ in items][::-1]
    vals = [v for _, v in items][::-1]
    cols = [OK if v == min(vals) else (BAD if v > 0.9 else ACCENT) for v in vals]
    ax.barh(names, vals, color=cols)
    for i, v in enumerate(vals):
        ax.text(v + 0.005, i, f"{v:.3f} m", va="center", fontsize=8)
    ax.axvline(0.905, color=MUTED, ls="--", lw=1)
    ax.set_xlim(0.5, 1.0)
    ax.set_xlabel("lỗi vị trí RMSE Track01 (m), đo bằng file chỉ đổi vị trí")
    ax.set_title("Track01: các cách sửa vị trí bằng scan matching")
    ax.tick_params(axis="y", labelsize=8)
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    path = os.path.join(FIG, "positions.png")
    fig.savefig(path, dpi=170)
    plt.close(fig)
    return path


def fig_pipeline():
    fig, ax = plt.subplots(figsize=(10, 4.6))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 46)
    ax.axis("off")

    def box(x, y, w, h, text, color=ACCENT, dashed=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2", fc=color + "18",
                                    ec=color, lw=1.4, ls="--" if dashed else "-"))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=8.2, color=INK, wrap=True)

    def arrow(x1, y1, x2, y2):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", color=INK, lw=1.1))

    box(1, 37, 17, 7, "rosbag: GNSS pose\n4 Hz", MUTED)
    box(24, 37, 22, 7, "Kalman CTRV + RTS\n(nhiễu: maximum likelihood)")
    box(1, 22, 17, 9, "3cameras_ply\n(MapAnything)", MUTED)
    box(24, 22, 22, 9, "tỉ lệ từng frame = 1.646 m / h\n(h = độ cao mặt đường)\nlọc ≤ 40 m, voxel 0.5 m")
    box(1, 9, 17, 7, "map.pcd → voxel 0.3 m", MUTED)
    box(52, 28, 22, 12, "GICP (small_gicp)\nlượt 1 → lượt 2\nlọc ≤ 2 m / 3°, làm mượt 2 s,\ntrừ độ lệch trung bình")
    box(1, 0.5, 17, 6, "rosbag: IMU gyro z", MUTED)
    box(24, 0.5, 22, 6, "bộ lọc bù: gyro + hướng chạy\n(Gauss τ: 7 s / 15 s)")
    box(80, 18, 18, 10, "CSV nộp Kaggle\nidx, x, y, yaw", OK)
    box(52, 6, 22, 13, "Phần CHỌN THEO ĐIỂM KAGGLE\n(tổ hợp vị trí / yaw,\nthăm dò, dò lỗi theo\ndao động) – ghi rõ riêng", BAD, dashed=True)
    arrow(18, 40.5, 24, 40.5)
    arrow(18, 26.5, 24, 26.5)
    arrow(46, 40.5, 52, 36)
    arrow(46, 26.5, 52, 31)
    arrow(18, 12.5, 52, 29)
    arrow(74, 34, 80, 25)
    arrow(18, 3.5, 24, 3.5)
    arrow(35, 37, 35, 6.6)
    arrow(46, 3.5, 80, 19)
    arrow(74, 12.5, 80, 20.5)
    ax.text(48, 44.5, "vị trí", fontsize=8, color=MUTED)
    ax.text(48, 1.6, "yaw", fontsize=8, color=MUTED)
    fig.tight_layout()
    path = os.path.join(FIG, "pipeline.png")
    fig.savefig(path, dpi=170)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------------------------- helpers
def P(text, style=BODY):
    return Paragraph(sym(text), style)


def bullets(items):
    return [Paragraph(sym(t), BULLET, bulletText="•") for t in items]


def table(rows, widths, header=True, zebra=True):
    data = [[Paragraph(sym(c), CELL_B if (header and i == 0) else CELL) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=[w * cm for w in widths], repeatRows=1 if header else 0)
    style = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c9d1e0")),
             ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
             ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e7eef8")))
    if zebra:
        for i in range(1 if header else 0, len(rows)):
            if i % 2 == 0:
                style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f7f9fc")))
    t.setStyle(TableStyle(style))
    return t


def image(path, width_cm, caption=None):
    from reportlab.lib.utils import ImageReader
    w, h = ImageReader(path).getSize()
    out = [Image(path, width=width_cm * cm, height=width_cm * cm * h / w)]
    if caption:
        out.append(Paragraph(sym(caption), CAPTION))
    return KeepTogether(out)


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Noto", 7.5)
    canvas.setFillColor(colors.HexColor(MUTED))
    canvas.drawString(2 * cm, 1.2 * cm, "SDC 2026 Midterm01 – Localization · tổng hợp công việc (đội 11) · tài liệu nội bộ")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"trang {doc.page}")
    canvas.restoreState()


# ---------------------------------------------------------------------------------------------- content
def build():
    os.makedirs(FIG, exist_ok=True)
    hist = load_history()
    f_tl, f_yaw, f_pos, f_pipe = fig_timeline(hist), fig_yaw(), fig_positions(), fig_pipeline()
    n1 = sum(1 for h in hist if h[0] == 1)
    n2 = sum(1 for h in hist if h[0] == 2)
    s = []

    # ---- cover + summary
    s += [Spacer(1, 2.2 * cm), P("SDC 2026 Midterm 01 – Localization", TITLE),
          P("Tổng hợp toàn bộ công việc để viết báo cáo cho TA", SUB), Spacer(1, 0.3 * cm),
          P("Đội 11 (một thành viên) · Kaggle: thuhangcs013 · GitHub: mochihat/SDC-midterm-1- · cập nhật 19/10/2026", SUB),
          Spacer(1, 0.9 * cm)]
    s.append(table([
        ["", "Track01 (3011 frame)", "Track02 (3299 frame)"],
        ["Baseline của TA", "1.79075", "1.92587"],
        ["Điểm tốt nhất hiện tại", "<b>0.78914</b> (hạng 3)", "<b>0.26849</b> (hạng 3)"],
        ["= lỗi vị trí + 0.2 × lỗi yaw", "0.616 m + 0.2 × 0.866°", "0.219 m + 0.2 × 0.249°"],
        ["Tốt nhất không dùng tổ hợp trọng số chọn theo điểm", "0.78914", "0.27654"],
        ["Hạng 1 lúc 19/10 14:00 (đội 12)", "0.57658", "0.23178"],
        ["Số lượt đã nộp có điểm (17–19/10)", str(n1), str(n2)],
    ], [6.2, 5.2, 5.2]))
    s += [Spacer(1, 0.6 * cm),
          P("<b>Tài liệu này là gì.</b> Bản tổng hợp do trợ lý AI (Claude Code) soạn từ nhật ký trong repo "
            "(<font face='Noto-Italic'>docs/nhat-ky/</font>) và lịch sử nộp bài lấy từ Kaggle API, để bạn nắm hết những gì đã "
            "làm trước khi tự viết báo cáo cho TA. Mọi con số đều lấy từ điểm Kaggle thật hoặc từ dữ liệu; chỗ nào là ước "
            "lượng sẽ ghi rõ. Phần nào <b>dựa vào điểm Kaggle</b> (không phải thuật toán) được tách riêng ở mục 6."),
          PageBreak()]

    s += [P("1. Tóm tắt nhanh", H1)]
    s += bullets([
        "Baseline của TA trôi tới ~100 m vì <b>tỉ lệ point cloud sai</b>: <font face='Noto-Italic'>ply_scale = 3</font>, "
        "đúng phải ≈ 9 (raw_ply) hoặc ≈ 0.8 (3cameras_ply) – tìm ra bằng cách đo độ cao mặt đường dưới camera.",
        "Topic <font face='Noto-Italic'>/localizer_node/gnss_pose</font> trong rosbag rất gần đáp án; "
        "<b>bộ lọc Kalman CTRV + RTS</b> (nhiễu chọn bằng maximum likelihood) làm nền vị trí.",
        "<b>Scan matching thật sự sửa được GNSS ở Track01</b>: GICP trên point cloud 3 camera với <b>tỉ lệ ước lượng "
        "theo từng frame</b>, chạy 2 lượt và <b>trừ độ lệch cố định</b> của phép khớp: lỗi vị trí 0.905 → 0.616 m.",
        "<b>Yaw của đáp án là yaw thân xe</b>: bộ lọc bù gyro (phần nhanh) + hướng chạy (phần chậm) giảm lỗi yaw "
        "Track01 1.56° → 0.87°, Track02 0.36° → 0.25° – bước tiến lớn nhất (Track01 0.928 → 0.789).",
        "Ở Track02, GNSS đã tốt (~0.23 m) và mọi phép khớp từ ảnh đều sai có hệ thống ~1 m → không sửa được vị trí bằng scan matching.",
        "Nhiều điểm cuối dùng <b>kỹ thuật chọn theo điểm Kaggle</b> (tổ hợp tuyến tính, file thăm dò). "
        "Từ 19/10, theo đồng ý của bạn sau khi hỏi TA, bắt đầu <b>dò lỗi qua bảng điểm</b> – phải khai báo rõ (mục 6).",
    ])
    s += [P("2. Bài toán và dữ liệu", H1),
          P("Ước lượng pose (x, y, yaw) của xe cho từng ảnh bằng cách khớp point cloud tạo từ ảnh vào bản đồ LiDAR. "
            "Dữ liệu mỗi track: <font face='Noto-Italic'>raw_ply</font> (LoGeR, camera trước), "
            "<font face='Noto-Italic'>3cameras_ply</font> (MapAnything, 3 camera), ảnh, bản đồ "
            "<font face='Noto-Italic'>map.pcd</font> (~50–60 triệu điểm), rosbag (IMU 100 Hz, GNSS pose 4 Hz), "
            "<font face='Noto-Italic'>init_guess.txt</font>, <font face='Noto-Italic'>camera_info</font> "
            "(thông số 3 camera fisheye + mặt nạ nắp capo)."),
          P("Điểm = RMSE vị trí (m) + 0.2 × RMSE yaw (độ), càng thấp càng tốt; leaderboard tính trên toàn bộ dữ liệu test. "
            "Mỗi track 15 lượt nộp/ngày; Kaggle đóng 29/10 09:00.")]

    s += [P("3. Pipeline hiện tại", H1), image(f_pipe, 16.5, "Hình 1 – Luồng xử lý. Khung đỏ nét đứt: phần dựa vào điểm "
                                                       "Kaggle, tách khỏi phần thuật toán.")]
    s += bullets([
        "<b>Vị trí:</b> GNSS → Kalman CTRV + RTS → prior. Mỗi frame: point cloud 3 camera nhân tỉ lệ 1.646 m / h "
        "(h = độ cao mặt đường đo trong point cloud, lọc trung vị ~2 s), bỏ điểm xa hơn 40 m, voxel 0.5 m; khớp GICP "
        "(small_gicp) vào bản đồ voxel 0.3 m, bắt đầu từ prior. Độ sửa của từng frame được lọc (≤ 2 m, ≤ 3°), lọc trung vị, "
        "làm mượt Gauss 2 s, <b>trừ độ lệch trung bình</b> rồi cộng vào prior; chạy lại GICP một lượt nữa từ kết quả.",
        "<b>Yaw:</b> tích phân gyro z (bias ước lượng bằng bình phương tối thiểu theo hướng chạy) + làm mượt Gauss τ của "
        "(hướng chạy − yaw gyro). τ = 7 s (Track01), 15 s (Track02).",
        "Công cụ chính: <font face='Noto-Italic'>tools/gicp_refine.py</font>, <font face='Noto-Italic'>tools/yaw_fusion.py</font>, "
        "<font face='Noto-Italic'>tools/rts_smoother.py</font>, <font face='Noto-Italic'>processing_codes/fuse_to_csv.py</font>.",
    ])

    # ---- contributions
    s += [P("4. Đóng góp (Contributions) – phần thuật toán", H1),
          P("Các ý tưởng dưới đây có cơ sở vật lý / dữ liệu; kết quả đo bằng điểm Kaggle (đánh giá).", SMALL)]
    s.append(table([
        ["Ý tưởng", "Bằng chứng / cách làm", "Kết quả"],
        ["Phát hiện tỉ lệ point cloud sai", "Mặt đường cách camera 0.18 đơn vị (raw_ply) → ×9 (camera ~1.62 m); 3cameras_ply → ×0.8",
         "NDT hết trôi (hiệu chỉnh 4 m → 0.2–0.7 m)"],
        ["Kalman CTRV + RTS smoother", "Mô hình xe: chạy theo hướng mũi; nhiễu chọn bằng maximum likelihood", "Track02 0.473 → 0.408"],
        ["Phân tích yaw GNSS", "Yaw GNSS = hướng dịch chuyển 1 s, cập nhật 1.25 s/lần, đóng băng khi dừng; dựng lại bằng gyro",
         "Track02 0.345 → 0.335"],
        ["NDT 3 camera tỉ lệ 0.8", "NDT C++ (PCL) bắt đầu từ prior GNSS, loại kết quả lệch xa", "lỗi vị trí 0.905 → 0.836 m"],
        ["GICP + tỉ lệ theo từng frame", "Tỉ lệ = 1.646 m / độ cao mặt đường đo được; GICP nhanh hơn NDT ~200 lần",
         "0.836 → 0.714 m (mọi frame)"],
        ["Lặp 2 lượt + trừ độ lệch trung bình", "GICP lệch cố định ~0.28 m so với GNSS (GNSS không lệch, đo bằng thăm dò) → "
         "bộ lọc bù: GNSS giữ trung bình, GICP thêm phần cục bộ", "0.714 → <b>0.616 m</b>"],
        ["Yaw bằng bộ lọc bù gyro", "Gyro cho phần nhanh, hướng chạy cho phần chậm; không trễ thời gian; trục z", "Track01 yaw 1.56° → <b>0.87°</b>; "
         "Track02 0.36° → <b>0.25°</b>"],
    ], [4.0, 8.0, 4.6]))
    s.append(Spacer(1, 0.3 * cm))
    s.append(image(f_pos, 15.5, "Hình 2 – Lỗi vị trí Track01 theo từng cách (file chỉ đổi vị trí, yaw giữ nguyên nên "
                                "lỗi vị trí = điểm − 0.314)."))
    s.append(image(f_yaw, 16.5, "Hình 3 – Lỗi yaw theo τ (vị trí giữ nguyên nên lỗi yaw = (điểm − lỗi vị trí) / 0.2). "
                                "τ, trục gyro và việc bỏ hiệu chỉnh trượt được chọn theo điểm."))

    # ---- problems
    s += [P("5. Vấn đề và cách giải quyết (Problems and Solutions)", H1)]
    s.append(table([
        ["Vấn đề", "Nguyên nhân tìm ra", "Cách xử lý"],
        ["Baseline trôi 91 m / 110 m", "ply_scale = 3 sai (phải ≈ 9)", "Đo độ cao mặt đường → sửa tỉ lệ; NDT 4 m"],
        ["NDT ổn định nhưng làm điểm xấu đi", "Sai số NDT trên ảnh lớn hơn sai số GNSS", "Dùng GNSS + Kalman làm nền, NDT/GICP chỉ sửa phần cục bộ"],
        ["Yaw GNSS trễ, đóng băng khi xe dừng", "Yaw tính từ vị trí GNSS, 1.25 s/lần", "Dựng lại yaw đoạn đứng yên bằng gyro; sau đó bộ lọc bù gyro"],
        ["Bù trễ 'đúng vật lý' làm điểm xấu", "Đáp án không dùng hướng chạy đúng giờ; yaw đáp án = yaw thân xe", "Dùng gyro làm phần chính của yaw"],
        ["GICP chạy lặp thì xấu đi (lượt 5)", "Point cloud ảnh méo → cực tiểu GICP lệch khỏi vị trí thật", "Dừng ở lượt 2"],
        ["GICP lệch cố định ~0.28 m", "Vị trí camera trong point cloud MapAnything (GNSS không lệch)", "Trừ độ lệch trung bình (bộ lọc bù)"],
        ["Tỉ lệ thay đổi giữa các frame (±5–11 %)", "MapAnything ước lượng tỉ lệ từng frame", "Tỉ lệ theo độ cao mặt đường từng frame"],
        ["Track02: scan matching làm hỏng vị trí", "GNSS Track02 ~0.23 m, phép khớp sai ~1 m có hệ thống", "Không dùng scan matching cho vị trí Track02"],
        ["Không có đáp án offline", "Chỉ có điểm Kaggle", "File 'chỉ đổi vị trí' / 'chỉ đổi yaw' để đo riêng từng phần"],
    ], [4.4, 6.0, 6.2]))

    s += [P("Những gì đã thử nhưng không hiệu quả", H2)]
    s.append(table([
        ["Thử", "Kết quả"],
        ["Gợi ý TA: mặt nạ nắp capo (camera_info)", "Chỉ 0.5–2 % điểm rơi vào vùng nắp capo (MapAnything đã tự bỏ); gần như không đổi"],
        ["Gợi ý TA: lọc điểm lạc (xử lý nhiễu)", "Lỗi vị trí 0.714 → 0.764 m (xấu đi)"],
        ["Gợi ý TA: bỏ mặt đường", "GICP mất ràng buộc z/roll/pitch (30 % hội tụ); với ICP 3 bậc tự do: không đổi"],
        ["raw_ply (LoGeR) + GICP", "Lệch dọc đường −0.79 m; không tương quan với 3 camera → bỏ"],
        ["VGICP, ICP 3 bậc tự do, point-to-plane lượt 2", "Không tốt hơn GICP lượt 2"],
        ["Yaw từ NDT / GICP", "Xấu hơn yaw hiện có"],
        ["Yaw GNSS gốc, bù trễ yaw, hiệu chỉnh trượt tự ước lượng", "Xấu đi"],
    ], [6.0, 10.6]))

    # ---- kaggle feedback
    s += [P("6. Phần dựa vào điểm Kaggle – cần khai báo rõ", H1),
          P("Leaderboard tính trên toàn bộ dữ liệu test (không có bảng điểm ẩn), nên mọi lựa chọn dựa vào điểm là khớp trực "
            "tiếp vào đáp án, không phải thuật toán. Danh sách đầy đủ để bạn ghi trong báo cáo:")]
    s.append(table([
        ["Kỹ thuật", "Dùng ở đâu", "Mức độ"],
        ["File thăm dò (lệch thời gian, dời ngang, cộng yaw ±)", "Tách điểm thành lỗi vị trí / yaw; đo độ lệch cố định", "Đo lường (nhẹ)"],
        ["Chọn tham số theo điểm (τ, trục gyro, số lượt GICP, tỉ lệ 0.8)", "Yaw và vị trí hiện tại", "1 tham số mỗi thứ (nhẹ)"],
        ["Trừ độ lệch trung bình", "Có cơ sở vật lý, nhưng dựa vào kết quả thăm dò 'GNSS không lệch ngang'", "Nhẹ"],
        ["Tổ hợp tuyến tính theo điểm (yaw_projection / pos_projection)", "yawproj_*, posproj_*, posyaw_v2_2, "
         "posproj_t2_v1_2 (Track02 0.26849); trọng số như −4.58, +7.5 không có ý nghĩa vật lý", "Mạnh"],
        ["Dò yaw theo đoạn 15 s (bump9, 18/10)", "Track02", "Mạnh"],
        ["Dò lỗi vị trí theo dao động thời gian (từ 20/10)", "Cả hai track; đã xếp hàng nộp đợt đầu", "Rất mạnh – gần như đọc đáp án"],
    ], [6.3, 7.3, 3.0]))
    s += [Spacer(1, 0.25 * cm),
          P("<b>Gợi ý:</b> trong báo cáo, tách rõ (1) kết quả thuật toán – Track01 0.78914 (vị trí GICP + yaw gyro, chỉ có vài tham "
            "số chọn theo điểm) và Track02 0.27654; (2) phần cải thiện thêm nhờ chọn theo điểm. Khi chọn bài nộp cuối trên Kaggle, "
            "bạn có thể chọn bài thuần thuật toán nếu TA yêu cầu.", BODY)]

    s += [P("7. Diễn biến điểm", H1), image(f_tl, 16.5, "Hình 4 – Mỗi chấm là một lượt nộp; đường xanh là điểm tốt nhất "
                                                       "đến lúc đó (lấy từ Kaggle API).")]
    s.append(table([
        ["Thời điểm", "Bước", "Track01", "Track02"],
        ["17/10 tối", "GNSS → làm mượt → Kalman; yaw theo hướng chạy", "1.26235", "0.40778"],
        ["17/10 khuya", "Tổ hợp yaw theo điểm; yaw đoạn khởi hành bằng gyro", "1.21861", "0.33504"],
        ["18/10 sáng", "NDT 3 camera tỉ lệ 0.8; tổ hợp vị trí", "1.07618", "0.30984"],
        ["18/10 trưa", "Dò yaw theo đoạn; tổ hợp", "1.05448", "0.29887"],
        ["19/10 00:45–01:30", "GICP + tỉ lệ theo mặt đường + 2 lượt + trừ độ lệch", "0.92775", "–"],
        ["19/10 02:00", "Bộ lọc bù gyro (Track02)", "–", "0.29268"],
        ["19/10 10:00–13:00", "Yaw dựa vào gyro (τ 7 / 15 s), tổ hợp vị trí Track02", "<b>0.78914</b>", "<b>0.26849</b>"],
    ], [3.2, 8.4, 2.5, 2.5]))

    # ---- workload / AI
    s.append(KeepTogether([P("8. Phân công và việc dùng AI (Workload)", H1),
          P("Bạn làm một mình. Đề không cấm và không bắt khai báo AI, nhưng phần Contributions chấm theo tính độc đáo, "
            "nên khai báo rõ là an toàn nhất. Tóm tắt trung thực:"), table([
        ["", "Chi tiết"],
        ["Công cụ AI", "Claude Code (trợ lý AI chạy trong terminal Ubuntu), làm việc liên tục 17–19/10"],
        ["AI đã làm", "Viết gần như toàn bộ code trong repo sau commit 8d5f06a (sửa localization.cpp/.h, các script run_*.sh, "
         "tools/*.py, processing_codes/*.py, Docker), chạy thí nghiệm, phân tích số liệu, đề xuất hướng làm, "
         "nộp phần lớn bài bằng script (bot), viết docs/nhat-ky và video bài giảng"],
        ["Bạn đã làm / quyết định", "Tải dữ liệu, tạo token Kaggle, kết nối GitHub, tự nộp 6 file GNSS đầu tiên; quyết định làm một "
         "mình; cho phép chỉnh theo điểm Kaggle và (19/10, sau khi hỏi TA) dò lỗi qua bảng điểm; quyết định chạy/dừng thí nghiệm"],
        ["Kiểm chứng", "Mọi file nộp đến sáng 18/10 được tạo lại từ dữ liệu gốc, trùng khớp từng byte (34/34); các file sau đó lưu "
         "trong docs/nhat-ky/submissions; dự đoán điểm của các tổ hợp khớp điểm thật tới ~0.0003"],
    ], [3.6, 13.0])]))
    s += [Spacer(1, 0.2 * cm),
          P("Nên tự đọc lại các phần code chính (tools/gicp_refine.py, tools/yaw_fusion.py, rts_smoother.py) để trình bày "
            "và trả lời câu hỏi khi thuyết trình.", SMALL)]

    s += [P("9. Mã nguồn và nhật ký", H1)]
    s.append(table([
        ["File / thư mục", "Nội dung"],
        ["src/localization/src/localization.cpp", "Node ROS 2: NDT bắt đầu từ prior GNSS, loại kết quả lệch xa, debug, chạy theo đoạn"],
        ["tools/rts_smoother.py", "Kalman CTRV + RTS smoother, nhiễu bằng maximum likelihood"],
        ["tools/gicp_refine.py", "GICP / VGICP / ICP 3 bậc tự do / point-to-plane trên point cloud ảnh; tỉ lệ theo mặt đường; "
         "nắp capo, lọc điểm lạc, bỏ mặt đường"],
        ["processing_codes/fuse_to_csv.py", "Ghép độ sửa scan matching vào prior (lọc, làm mượt, trừ độ lệch)"],
        ["tools/yaw_fusion.py", "Yaw bằng bộ lọc bù gyro + hướng chạy"],
        ["tools/map_voxel.py", "Giảm mẫu map.pcd 60 triệu điểm thành bản đồ 0.3 m"],
        ["tools/yaw_projection.py, pos_projection.py, make_probes.py", "Các công cụ chọn theo điểm Kaggle (mục 6)"],
        ["docs/nhat-ky/01–08", "Nhật ký chi tiết: phân tích dữ liệu, thí nghiệm, từng lượt nộp, nhận xét, cách tạo lại"],
        ["docs/nhat-ky/submissions/", "Bản sao mọi file đã nộp"],
    ], [5.8, 10.8]))

    s += [P("10. Việc còn lại và checklist", H1)]
    s += bullets([
        "<b>Kaggle đóng 29/10 09:00</b>: chọn bài nộp cuối (nếu TA không chấp nhận phần chọn theo điểm, chọn bài thuần thuật toán).",
        "<b>Thuyết trình 29/10 trên lớp (4–6 phút)</b>; gửi slide hoặc link slide tới email TA trước <b>29/10 09:00</b>.",
        "<b>E3 hạn 05/11 23:59</b>: file zip gồm thư mục localization/ (không kèm dữ liệu), code đã viết, result_1.csv, result_2.csv "
        "(bài tốt nhất), báo cáo PDF tên localization_report_&lt;MSSV&gt;.pdf, README cách chạy. Làm một mình: hỏi TA cách đặt tên.",
        "Báo cáo 30 điểm: Pipeline · Contributions · Problems and Solutions · Workload Distribution · Others – các mục 3–8 "
        "của tài liệu này đi theo đúng khung đó.",
    ])
    appendix = [P("Phụ lục – một số hình từ dữ liệu", H1)]
    for name, cap in (("baseline_vs_gnss.png", "Baseline TA (tỉ lệ ×3) trôi khỏi quỹ đạo GNSS sau vài trăm frame."),
                      ("ply_side_scale.png", "Point cloud LoGeR nhìn ngang: mặt đường ở 0.18 đơn vị dưới camera → tỉ lệ ×9."),
                      ("gnss_yaw_staircase_t2.png", "Yaw GNSS Track02 dạng bậc thang, đóng băng 13 s đầu khi xe đứng yên.")):
        p = os.path.join(VIDEO_FIG, name)
        if os.path.exists(p):
            appendix.append(image(p, 13.5, cap))
    s.append(KeepTogether(appendix[:2]))
    s += appendix[2:]

    doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm,
                            bottomMargin=1.8 * cm, title="SDC 2026 Midterm01 – tổng hợp công việc (đội 11)",
                            author="Claude Code cho đội 11")
    doc.build(s, onFirstPage=on_page, onLaterPages=on_page)
    print("wrote", OUT)


if __name__ == "__main__":
    build()
