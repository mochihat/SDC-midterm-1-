"""Cây hành trình SDC Midterm01 (25/10): gốc = bài toán, nhánh = các con đường đã đi, nhánh dừng = đường đứt,
mũi tên cam = rẽ sang hướng mới, đường tím chấm = liên kết chéo giữa các nhánh. Xuất docs/report/cay_hanh_trinh.pdf.

Chạy trên máy (cần reportlab + font DejaVu): python3 docs/report/make_tree.py
"""
import os

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

F = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("DV", F + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DVB", F + "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DVB", italic="DV", boldItalic="DVB")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cay_hanh_trinh.pdf")

# status: root | group | keep (giữ) | drop (dừng = nhánh đứt) | best (tốt nhất hiện tại) | info (kiểm tra / kết luận)
# edge: 'tree' = nhánh con thường; 'turn' = rẽ hướng mới sau một nhánh dừng (mũi tên cam)
N = [
    ("root", None, "root", "tree", "<b>BÀI TOÁN</b>: với mỗi frame camera, ước lượng pose (x, y, yaw) của xe trên bản đồ LiDAR. "
     "Điểm = RMSE vị trí (m) + 0.2 × RMSE yaw (độ), thấp hơn = tốt hơn. Point cloud dựng từ ảnh bằng AI (LoGeR / MapAnything) bị méo."),

    # ---------------- Track01/02 ----------------
    ("A", "root", "group", "tree", "<b>Track01 / Track02</b> — có GNSS + IMU; TA (23/10) cho phép dò bảng điểm; chấm theo public toàn bộ."),
    ("A1", "A", "drop", "tree", "<b>NDT C++ của TA</b> (bản đồ chia ô Gauss). Sửa <i>ply_scale = 3</i> sai → tỉ lệ theo độ cao mặt đường "
     "(camera cao 1.646 m). Ổn định nhưng kém GNSS → dừng."),
    ("A2", "A1", "keep", "turn", "<b>GNSS → Kalman CTRV + RTS smoother</b> (mô hình tốc độ & tốc độ quay không đổi, làm mượt 2 chiều; "
     "Track01/02 không bắt buộc nhân quả). Nền của mọi bản clean."),
    ("A2y1", "A2", "drop", "tree", "<b>Yaw = hướng chạy GNSS</b>: trễ 1.1–1.4 s, đứng im khi xe dừng → dừng."),
    ("A2y2", "A2y1", "keep", "turn", "<b>Yaw = gyro (nhanh) + hướng GNSS (chậm)</b>, bộ lọc bù τ 7 s (T1) / 15 s (T2)."),
    ("A2g", "A2", "keep", "tree", "<b>GICP 2 lượt</b> (point cloud 3 camera vào bản đồ voxel 0.3 m, lọc ≤2 m/3°, trừ lệch trung bình, "
     "z/roll/pitch từ NDT). T1 clean 0.80."),
    ("A2g1", "A2g", "drop", "tree", "<b>5 lượt GICP</b>: point cloud méo kéo về cực tiểu sai → tệ hơn 2 lượt."),
    ("A2g2", "A2g", "drop", "tree", "<b>Mặt nạ nắp capo, lọc điểm lạc (SOR), raw_ply LoGeR cho GICP</b>: không lợi."),
    ("A2g3", "A2g", "drop", "tree", "<b>Ghép theo Hessian GICP</b> (info_fuse): T1 0.80 → 0.84–0.87, T2 0.28 → 0.30."),
    ("A2g4", "A2g", "keep", "tree", "<b>Tầm point cloud 40 → 20 m</b> (sai độ sâu tăng theo bình phương khoảng cách): T1 0.80 → <b>0.63</b>. "
     "Bỏ GICP khi cua 0.78, z/roll/pitch từ bản đồ 0.81 → dừng."),
    ("A2c", "A2g", "keep", "tree", "<b>CSM quanh quỹ đạo clean</b> (csm_fuse.py, tỉ lệ ×0.9, làm mượt 3 s): T1 0.62 → <b>0.55</b>, "
     "T2 0.28 → <b>0.25</b>."),
    ("A2m", "A2g", "keep", "tree", "<b>Yaw theo bản đồ</b> (map_yaw_fuse.py: gyro nhanh + yaw GICP LoGeR chậm, Gauss 8 s, bỏ xu hướng "
     "tuyến tính trước khi làm mượt): T1 <b>0.51</b>. Trên T2 làm tệ (0.115 → 0.51°) → chỉ dùng T1."),
    ("A2t", "A2g", "keep", "tree", "<b>Bù trễ GNSS −10 ms</b> (time_shift.py) T2: 0.25 → <b>0.24</b>. +20 ms sai dấu (bắt được offline)."),
    ("A3", "A", "drop", "tree", "<b>Dò bảng điểm</b>: m_D = (P_D² − P² − mean|D|²)/2 = mean(e·D) → hình chiếu sai số thật lên hướng D; "
     "ghép bằng ridge. 20/10 TA (forum): \"leaderboard fitting\" → DỪNG."),
    ("A3b", "A3", "keep", "turn", "<b>23/10 TA cho phép dò ở Track01/02</b> → vòng 3–5 (lệch hằng, cosin bậc K, dọc/ngang thân xe): "
     "T1 0.40 → <b>0.36</b> (mode cosin 7), T2 <b>0.11</b> → <b>HẠNG 1 cả hai</b>. Vòng 6 (yaw9/10) chuẩn bị, chưa nộp."),

    # ---------------- Track03 ----------------
    ("B", "root", "group", "tree", "<b>Track03</b> — KHÔNG GNSS, luật 10/22: chỉ nhân quả (frame ≤ k), không sửa tay, TA chạy lại code. "
     "Public = 13 % đầu, private = 87 % (xe đứng chờ đèn frame 950–2150 = 44 % private)."),
    ("B1", "B", "drop", "tree", "<b>Bộ bám v1</b>: GICP + vận tốc không đổi + MHT 9–11 giả thuyết yaw (init lệch ~18°). t3_full_N "
     "public 0.77 nhưng MHT ghi ngược quá khứ = KHÔNG nhân quả → không được làm bài cuối."),
    ("B2", "B1", "drop", "turn", "<b>Sửa thành nhân quả</b> (ghi giả thuyết tốt nhất TẠI frame) + sửa tích phân gyro (mất 14 % góc) + "
     "ZUPT + bias gyro online. Yaw đúng nhưng vị trí trôi 13–30 m từ frame ~500 (odometry LoGeR hụt 40–60 %) → dừng."),
    ("B3", "B2", "keep", "turn", "<b>CSM ±15 m</b> (khớp lưới tương quan trên likelihood field) + GICP tin 0.7 m ngang / 2 m dọc. "
     "t3_A2h public 0.96, chấp nhận 98 %."),
    ("B3a", "B3", "drop", "tree", "<b>Tay đòn CSM −1.0 m + bộ lọc tốc độ IMU</b> (t3_L2): 1.05 — tay đòn −1.0 là hệ quả của sai tỉ lệ "
     "10 % ở T1/T2, T3 chỉ 5–7 %."),
    ("B3b", "B3a", "keep", "turn", "<b>Tay đòn −0.7</b> theo sai tỉ lệ đo trên T3 (t3_L2b): <b>0.84</b>."),
    ("B3c", "B3b", "drop", "tree", "<b>Sửa tỉ lệ point cloud trực tiếp</b> (scale-mult / scale-online): mất bám ở khúc cua → dừng."),
    ("B3d", "B3b", "drop", "tree", "<b>Thử và bỏ</b>: point cloud 3 camera, bước CSM 0.25 m, course-over-ground từ vị trí LoGeR, "
     "quaternion IMU, vạch kẻ từ raw_ply (quá thưa), sàn sd CSM (lạc ở cua)."),
    ("B3e", "B3b", "keep", "tree", "<b>W3h</b>: yaw rate = gyro · hướng thẳng đứng (IMU nghiêng 6°), τ yaw 30 s, phương sai tốc độ vào "
     "nhiễu dọc, giữ vị trí khi đứng. Public 0.89 (tệ hơn) nhưng GIỮ vì nhắm private."),
    ("B3f", "B3b", "keep", "tree", "<b>X3f</b>: hướng trọng lực cố định hiệu chuẩn (ước lượng online lệch 8° ở giây đầu): <b>0.80</b>."),
    ("B3g", "B3b", "keep", "tree", "<b>Z3a</b>: ZUPT cần gia tốc TB ≈ 0 (--zupt-ax 0.3) + loại odometry thấp (--speed-odo-low): "
     "public 0.80, chạy lại sau đèn trễ 2.46 → 0.72 m. = PRIOR của mọi bản vạch sơn."),
    ("B3h", "B3b", "drop", "tree", "<b>Chỉnh tham số theo public</b> (TA cho phép): lưới yaw 2° 0.82, tay đòn −0.9 0.98, −0.5 0.95, "
     "gyro z 0.82, yaw offset 0.81, tay đòn ngang 0.82, κ CSM 25 0.82, τ đầu 20 s 0.80 → không bản nào < 0.80."),
    ("B3i", "B3b", "drop", "tree", "<b>Yaw hội tụ nhanh lúc đầu</b> (--yaw-rls 3: 1.08, --yaw-rls-dist 5: 0.96, 20: 0.85) — tệ đều theo "
     "mức kéo yaw → kết luận: yaw đã đúng, SAI LÀ Ở VỊ TRÍ; trần LoGeR ~0.5–1 m."),

    ("B4", "B3i", "keep", "turn", "<b>KHỚP VẠCH SƠN</b>: ảnh camera trước (h265 trong bag, ảnh từ frame 14) → IPM lên mặt đường (độ cao "
     "theo bản đồ) → vạch sơn (white top-hat 0.7 m + sáng hơn mặt đường nắng) ↔ vạch sơn trong cường độ LiDAR; NCC qua FFT."),
    ("B4a", "B4", "info", "tree", "<b>Hiệu chuẩn camera trên T1/T2</b> (tổng NCC ~300 frame tại pose tham chiếu): pitch <b>1.0°</b>, "
     "yaw <b>−1.5°</b> (cả hai track đồng ý); phép đo T2: ngang ~0.15 m, dọc 0.2–0.6 m."),
    ("B4b", "B4", "drop", "tree", "<b>Bộ lọc v1</b> (hậu nghiệm lưới κ·NCC + prior Gauss): khóa cứng khi xe đứng (một khung cảnh "
     "đếm hàng trăm lần) → tệ hơn prior trên T2."),
    ("B4c", "B4b", "keep", "turn", "<b>κ theo quãng đường + sàn độ bất định</b>: PA1 (tay đòn ngang −0.25) 0.56, PA3 0.55, "
     "<b>PA2 (−0.10) 0.49</b>. 0.80 → 0.49!"),
    ("B4d", "B4c", "keep", "tree", "<b>Tay đòn ngang 0</b> (PB2): <b>0.47</b>."),
    ("B4e", "B4c", "drop", "tree", "<b>Yaw theo vạch sơn</b> (PB3): 0.54 → yaw Z3a tốt hơn."),
    ("B4f", "B4c", "keep", "tree", "<b>Tay đòn dọc +0.15</b> (PD1) 0.44; −0.15 (PD2) 0.55 dừng; <b>κ 40</b> (PD3) 0.43 → gộp (PE1) 0.39."),
    ("B4g", "B4c", "keep", "tree", "<b>κ 80</b> (PE3): <b>0.37</b>. Tay đòn dọc +0.30 (PE2) 0.42 dừng; κ 160 (PF1) 0.38 dừng."),
    ("B4h", "B4c", "drop", "tree", "<b>Bản online</b> (vùng tìm theo dự đoán bộ lọc): lạc 3–4 m ở khúc cua → bỏ."),
    ("B4i", "B4c", "info", "tree", "<b>Nhiều lượt đo, chỉ camera trước</b> (PC3 0.50, PG3 0.38): public ngang bản 1 lượt, khớp ảnh tốt "
     "hơn ở cua → chỉ có giá trị cho private."),
    ("B4j", "B4c", "drop", "tree", "<b>Kiểm tra bằng độ khớp LoGeR</b>: khen Z3a vì Z3a tối ưu đúng phép đo đó → thước đo không độc lập, bỏ."),
    ("B4k", "B4c", "drop", "tree", "<b>Camera bên gộp chung một NCC</b>: T2 tương quan giảm (0.35 → 0.25), nhiễu vùng không vạch làm loãng."),
    ("B4l", "B4k", "best", "turn", "<b>Camera bên là khối NCC riêng</b> (κ_side 40, PF2): <b>0.33 = TỐT NHẤT, HẠNG 2</b> "
     "(camera phải có ảnh từ frame 3, thấy vạch ô đỗ xe cạnh xe). κ_side 80 (PF3) 0.47 dừng."),
    ("B4m", "B4l", "drop", "tree", "<b>3 lượt đo + camera bên</b> (PG4): 0.47 → các lượt trôi, bỏ."),
    ("B4n", "B4l", "info", "tree", "<b>Kiểm tra yaw lúc đứng chờ đèn</b> (hướng chạy của quỹ đạo đã sửa + khớp vạch tĩnh lưới 0.1°): "
     "đúng trong ±0.2° → không sửa."),
    ("B4o", "B4l", "keep", "tree", "<b>PH1 = PF2 + cập nhật lúc đứng yên</b>: public trùng PF2, khác ≤ 0.06 m lúc đứng → ứng viên bài cuối "
     "(chưa nộp). Ước lượng private ~0.35–0.5."),
]
# liên kết chéo (tím, chấm): từ -> tới, nhãn
X = [
    ("A3b", "A2m", "dò chỉ ra mode cosin 7 của yaw → sinh bước yaw theo bản đồ cho clean"),
    ("A3b", "B4a", "quỹ đạo dò (gần đáp án) dùng để hiệu chuẩn camera"),
    ("A2g4", "B3", "bài học tầm ngắn / point cloud méo"),
    ("A2c", "B3", "CSM dùng chung (tracker Track03)"),
    ("B3g", "B4", "Z3a là prior của bộ lọc vạch sơn"),
    ("B3d", "B4", "vạch kẻ từ raw_ply quá thưa → dùng ảnh camera thật"),
    ("B4i", "B4m", "nhiều lượt + camera bên"),
    ("B3e", "B3f", "xây tiếp trên"),
    ("B3f", "B3g", "xây tiếp trên"),
    ("B4d", "B4f", "xây tiếp trên"),
    ("B4f", "B4g", "xây tiếp trên"),
    ("B4g", "B4k", "thêm camera bên vào PE3"),
]

STYLE = {
    "root": (colors.HexColor("#1f2937"), colors.HexColor("#e5e7eb"), 2.0, None),
    "group": (colors.HexColor("#374151"), colors.HexColor("#f3f4f6"), 1.6, None),
    "keep": (colors.HexColor("#15803d"), colors.HexColor("#ecfdf3"), 1.2, None),
    "best": (colors.HexColor("#1d4ed8"), colors.HexColor("#dbeafe"), 2.6, None),
    "drop": (colors.HexColor("#b91c1c"), colors.HexColor("#fef2f2"), 1.2, (4, 3)),
    "info": (colors.HexColor("#6b7280"), colors.HexColor("#f9fafb"), 1.0, (1, 2)),
}
BW, COLW, GAP, M = 260, 315, 12, 40
ps = ParagraphStyle("b", fontName="DV", fontSize=8.2, leading=10.4)


def main():
    nodes = {n[0]: dict(id=n[0], parent=n[1], st=n[2], edge=n[3], text=n[4], kids=[]) for n in N}
    for n in N:
        if n[1]:
            nodes[n[1]]["kids"].append(n[0])
    for v in nodes.values():
        v["p"] = Paragraph(v["text"], ps)
        _, h = v["p"].wrap(BW - 12, 1000)
        v["h"] = h + 12

    def depth(i):
        return 0 if nodes[i]["parent"] is None else depth(nodes[i]["parent"]) + 1
    cursor = [M + 40]

    def place(i):                      # tidy tree: leaves stacked top-down, parents centred on their children
        v = nodes[i]
        v["x"] = M + depth(i) * COLW
        if not v["kids"]:
            v["y"] = cursor[0]
            cursor[0] += v["h"] + GAP
        else:
            start = cursor[0]
            for k in v["kids"]:
                place(k)
            if cursor[0] - start < v["h"] + GAP:      # a tall parent over a short child span: keep its rows free
                cursor[0] = start + v["h"] + GAP
            ys = [nodes[k]["y"] + nodes[k]["h"] / 2 for k in v["kids"]]
            v["y"] = min(max((min(ys) + max(ys)) / 2 - v["h"] / 2, start), cursor[0] - GAP - v["h"])

    place("root")
    W = M * 2 + (max(depth(i) for i in nodes) + 1) * COLW
    H = cursor[0] + 140
    c = canvas.Canvas(OUT, pagesize=(W, H))
    c.setTitle("Cây hành trình SDC Midterm01 – Localization")
    Y = lambda y: H - y                # top-down coordinates

    c.setFont("DVB", 20)
    c.drawString(M, Y(M - 5), "Cây hành trình SDC Midterm01 – Localization (đến 25/10/2026)")
    c.setFont("DV", 10)
    c.drawString(M, Y(M + 14), "Các nhánh anh em xếp theo thời gian từ trên xuống. Gốc = bài toán · nhánh = con đường đã đi · đỏ đứt = đã dừng (✂) · mũi tên cam = rẽ hướng mới · "
                 "xanh = giữ · xanh đậm = tốt nhất · xám chấm = kiểm tra/kết luận · tím chấm = liên kết chéo")

    # edges
    for v in nodes.values():
        if not v["parent"]:
            continue
        p = nodes[v["parent"]]
        x0, y0 = p["x"] + BW, p["y"] + p["h"] / 2
        x1, y1 = v["x"], v["y"] + v["h"] / 2
        xm = (x0 + x1) / 2
        if v["edge"] == "turn":
            c.setStrokeColor(colors.HexColor("#ea580c")); c.setLineWidth(2.0); c.setDash()
        elif v["st"] == "drop":
            c.setStrokeColor(colors.HexColor("#b91c1c")); c.setLineWidth(1.2); c.setDash(5, 4)
        else:
            c.setStrokeColor(colors.HexColor("#4b5563")); c.setLineWidth(1.2); c.setDash()
        pth = c.beginPath(); pth.moveTo(x0, Y(y0)); pth.curveTo(xm, Y(y0), xm, Y(y1), x1, Y(y1))
        c.drawPath(pth, stroke=1, fill=0)
        c.setDash()
        if v["edge"] == "turn":       # arrow head + label
            c.setFillColor(colors.HexColor("#ea580c"))
            a = c.beginPath(); a.moveTo(x1, Y(y1)); a.lineTo(x1 - 8, Y(y1) + 4); a.lineTo(x1 - 8, Y(y1) - 4); a.close()
            c.drawPath(a, stroke=0, fill=1)
            c.setFont("DVB", 7); c.drawString(xm - 22, Y((y0 + y1) / 2) + 3, "rẽ hướng")
        if v["st"] == "drop":         # cut mark at the end of a stopped branch
            c.setFillColor(colors.HexColor("#b91c1c")); c.setFont("DVB", 11)
            c.drawString(v["x"] + BW + 4, Y(v["y"] + v["h"] / 2) - 4, "✂")
    # cross links
    for a_, b_, lab in X:
        a, b = nodes[a_], nodes[b_]
        x0, y0 = a["x"] + BW / 2, a["y"] + (a["h"] if b["y"] > a["y"] else 0)
        x1, y1 = b["x"] + BW / 2, b["y"] + (0 if b["y"] > a["y"] else b["h"])
        c.setStrokeColor(colors.HexColor("#7c3aed")); c.setLineWidth(1.3); c.setDash(1, 3)
        bend = 160 if x1 >= x0 else -160
        pth = c.beginPath(); pth.moveTo(x0, Y(y0)); pth.curveTo(x0 + bend, Y(y0), x1 - bend, Y(y1), x1, Y(y1))
        c.drawPath(pth, stroke=1, fill=0); c.setDash()
        c.setFillColor(colors.HexColor("#7c3aed"))
        ar = c.beginPath(); ar.circle(x1, Y(y1), 3); c.drawPath(ar, stroke=0, fill=1)
        c.setFont("DV", 7); c.drawString((x0 + x1) / 2 + 4, Y((y0 + y1) / 2), lab)
    # boxes
    for v in nodes.values():
        sc, bg, lw, dash = STYLE[v["st"]]
        c.setStrokeColor(sc); c.setFillColor(bg); c.setLineWidth(lw)
        if dash:
            c.setDash(*dash)
        c.roundRect(v["x"], Y(v["y"] + v["h"]), BW, v["h"], 5, stroke=1, fill=1)
        c.setDash()
        v["p"].drawOn(c, v["x"] + 6, Y(v["y"] + v["h"]) + 6)
    c.setFont("DV", 8); c.setFillColor(colors.HexColor("#4b5563"))
    c.drawString(M, 30, "Số liệu: điểm Kaggle public (bot.log), nhật ký docs/nhat-ky/08–13. Track03 'public' = 13 % frame đầu; "
                 "private không đo được. Mọi file Track03 là output trực tiếp của tools/run_track3.sh / run_track3_paint.sh.")
    c.showPage()

    # page 2: concepts
    c.setPageSize((W, H))
    items = [
        ("Pose", "vị trí (x, y) và hướng yaw của xe trong hệ toạ độ bản đồ."),
        ("RMSE", "căn trung bình bình phương sai số; phạt nặng sai số lớn."),
        ("Point cloud LoGeR / MapAnything", "đám điểm 3D do mạng AI dựng từ ảnh (1 camera / 3 camera); méo, sai độ sâu tăng theo khoảng cách, sai tỉ lệ 5–10 %."),
        ("Bản đồ LiDAR + cường độ", "đám điểm laser chính xác vài cm; cường độ = độ phản xạ, vạch sơn phản xạ mạnh."),
        ("GNSS / IMU / gyro / bias", "GPS vệ tinh; cảm biến quán tính (gia tốc kế + con quay); bias = độ lệch cố định của số đọc (−0.24°/s ở xe này)."),
        ("Nhân quả (causal)", "kết quả frame k chỉ dùng dữ liệu frame ≤ k; không làm mượt ngược. Luật bắt buộc của Track03."),
        ("Kalman filter / EKF", "dự đoán trạng thái + độ bất định, gặp phép đo thì trộn theo mức tin cậy; EKF = tuyến tính hoá cho mô hình phi tuyến."),
        ("CTRV", "mô hình chuyển động tốc độ và tốc độ quay không đổi."),
        ("RTS smoother", "Kalman xuôi rồi ngược để làm mượt (phi nhân quả)."),
        ("Bộ lọc bù (complementary), τ", "trộn nguồn nhanh mà trôi (gyro) với nguồn chậm mà tuyệt đối; τ = thời gian kéo về nguồn chậm."),
        ("NDT", "Normal Distributions Transform: bản đồ chia ô, mỗi ô một phân bố Gauss; tối ưu pose để điểm rơi vào vùng đậm."),
        ("ICP / GICP", "lặp: ghép điểm gần nhất rồi giải phép biến đổi; GICP thêm hiệp phương sai bề mặt cục bộ mỗi điểm."),
        ("CSM (correlative scan matching)", "thử mọi vị trí trên lưới, chấm điểm theo likelihood field, lấy phân bố hậu nghiệm; nhìn xa ±15 m, không kẹt cực tiểu cục bộ."),
        ("Likelihood field", "ảnh 2D 'xác suất có cấu trúc' làm mờ từ các điểm bản đồ cao 0.4–3 m trên mặt đường."),
        ("MHT", "nhiều giả thuyết (ở đây: 11 yaw ban đầu) chạy song song, giữ cái ít sai nhất."),
        ("ZUPT", "zero-velocity update: xe đứng yên → ép tốc độ = 0 và không đổi yaw."),
        ("Odometry", "chuyển động giữa hai frame liên tiếp (GICP cloud với cloud 6 frame trước)."),
        ("Tay đòn (lever)", "độ lệch cố định giữa điểm đo (camera / tâm cloud) và điểm tham chiếu của đáp án, trong hệ xe (dọc / ngang)."),
        ("IPM", "inverse perspective mapping: chiếu lưới điểm mặt đường vào ảnh để có ảnh nhìn từ trên xuống."),
        ("Fisheye OpenCV", "mô hình ống kính góc rộng: θd = θ(1 + k1θ² + k2θ⁴ + k3θ⁶ + k4θ⁸)."),
        ("Nội tại / ngoại tại", "tiêu cự, tâm ảnh, méo / vị trí-hướng lắp camera (pitch 1.0°, yaw −1.5°; camera bên theo lucid_camera_extrinsics.yaml)."),
        ("White top-hat, grey opening", "giá trị trừ phép mở hình thái (min rồi max trong ô 0.7 m): chỉ còn cấu trúc sáng mảnh hơn 0.7 m = vạch sơn."),
        ("NCC (có mặt nạ, trừ trung bình)", "tương quan chuẩn hoá −1…1: hai ảnh giống nhau bao nhiêu, không phụ thuộc độ sáng; chỉ tính trên ô camera thấy."),
        ("FFT", "tính tương quan cho mọi dịch chuyển cùng lúc (0.07 s/frame cho 13 yaw × 5 pitch × 41 × 31 dịch)."),
        ("Hậu nghiệm trên lưới, κ", "log p = κ·NCC − ½(g−e)ᵀP⁻¹(g−e); κ lớn = tin phép đo vạch sơn hơn (tốt nhất 80)."),
        ("κ theo quãng đường / thời gian", "khung cảnh đứng yên lặp lại không phải phép đo mới → trọng số theo mét đã đi; khi đứng chỉ kéo chậm."),
        ("Dò bảng điểm (probing)", "m_D = (P_D² − P² − mean|D|²)/2 = mean(e·D): mỗi lần nộp cho biết hình chiếu sai số lên một hướng D; ghép bằng ridge."),
        ("Ridge", "hồi quy có phạt λ‖a‖² để nghiệm ổn định khi điểm số bị cắt 2 chữ số."),
        ("GOP / khung khoá (IDR)", "nhóm ảnh nén h265; chỉ giải mã được từ khung khoá: camera trước frame 14, phải 3, trái 35."),
        ("Public / private", "phần điểm thấy ngay (Track03: 13 % đầu) / phần ẩn quyết định hạng (87 %); Kaggle chỉ tính private cho bài được chọn."),
    ]
    c.setFont("DVB", 18); c.setFillColor(colors.black)
    c.drawString(M, H - M, "Khái niệm dùng trong cây (đầy đủ, không lược bớt)")
    y = H - M - 30
    pk = ParagraphStyle("k", fontName="DV", fontSize=11, leading=14)
    for k, d in items:
        p = Paragraph(f"<b>{k}</b>: {d}", pk)
        _, h = p.wrap(W - 2 * M, 200)
        p.drawOn(c, M, y - h)
        y -= h + 8
    c.showPage()
    c.save()
    print("wrote", OUT, f"{W:.0f} x {H:.0f} pt")


if __name__ == "__main__":
    main()
