"""Hình minh hoạ (nhãn tiếng Việt) cho bộ slide đầy đủ: mỗi bước của pipeline nhìn thấy gì, trên frame thật.

Dữ liệu: docs/report/fig/explain_data/*.npz (tools/explain_figdata.py trong sdc-reg) + ảnh / bản đồ trên máy.
Ra: docs/report/fig/explain/*.png. Chạy trên máy (numpy + matplotlib + Pillow): python3 docs/report/make_explain_figs.py
"""
import csv
import os
import re

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HOME = os.path.expanduser("~")
DATA = os.path.join(HOME, "SDC-midterm01", "data")
IN = os.path.join(REPO, "docs", "report", "fig", "explain_data")
OUT = os.path.join(REPO, "docs", "report", "fig", "explain")
# EN=1: same figures with English labels, saved to fig/explain_en/ (the Vietnamese set is not touched).
if os.environ.get("EN") == "1":
    OUT = os.path.join(REPO, "docs", "report", "fig", "explain_en")
    import matplotlib.text as _mt
    _TR = [('+ lỗi giả lập: gốc camera lệch 0.3 m lên trước', '+ simulated error: camera origin 0.3 m forward'), ('+ lỗi giả lập: gốc camera lệch 0.3 m sang trái', '+ simulated error: camera origin 0.3 m left'), ('+ lỗi giả lập: méo độ sâu +0.2 %/m (5 % ở 25 m)', '+ simulated error: depth distortion +0.2 %/m (5 % at 25 m)'), ('+ lỗi giả lập: ', '+ simulated error: '), ('11 giả thuyết (−30…+30°) chạy song song; mỗi frame chỉ xuất giả thuyết tốt nhất tại chính frame đó', '11 yaw hypotheses (−30…+30°) run in parallel; each frame outputs only the best one at that frame'), ('① Ảnh camera trước (đã cắt hàng 420–799)', '① Front camera image (rows 420–799 cropped)'), ('② Chiếu ngược xuống mặt đường (IPM)', '② Projected down onto the road (IPM)'), ('③ Vạch sơn camera: chỉ giữ cấu trúc sáng, hẹp < 0.7 m', '③ Camera paint: keep only thin bright structures, < 0.7 m'), ('④ Cường độ LiDAR của bản đồ (cùng ô)', '④ Map LiDAR intensity (same cells)'), ('⑤ Vạch sơn bản đồ (white top-hat 0.7 m)', '⑤ Map paint (white top-hat 0.7 m)'), ('⑥ So ③ với ⑤ ở mọi độ dời (NCC qua FFT)', '⑥ ③ vs ⑤ at every shift (NCC via FFT)'), ('250 frame đầu của kết quả cuối', 'first 250 frames of the final result'), ('3cameras_ply (MapAnything, 3 camera): gần đúng mét', '3cameras_ply (MapAnything, 3 cameras): nearly metric'), ('~330 nghìn điểm, nhìn được cả hai bên xe', '~330k points, sees both sides of the car'), ('3 lần nộp thật (Track01, 17/10)', '3 real submissions (Track01, 17/10)'), ('bản đồ LiDAR (vật cao 0.4–3 m)', 'LiDAR map (tall objects 0.4–3 m)'), ('bản đồ LiDAR', 'LiDAR map'), ('Camera trước-phải', 'Front-right camera'), ('Camera trước-trái', 'Front-left camera'), ('Camera trước', 'Front camera'), ('camera trước-phải', 'front-right camera'), ('camera trước-trái', 'front-left camera'), ('camera trước', 'front camera'), ('camera bên', 'side camera'), ('camera hai bên', 'side cameras'), ('Code mẫu (×3, mỗi frame bắt đầu từ frame trước):', 'Sample code (×3, each frame starts from the previous frame):'), ('sai số cộng dồn tới 91 m / 110 m', 'errors accumulate to 91 m / 110 m'), ('cùng các điểm đó tại đỉnh CSM', 'same points at the CSM peak'), ('điểm của point cloud tại vị trí bộ bám cũ (N)', 'points of the point cloud at the old tracker pose (N)'), ('điểm Kaggle', 'Kaggle score'), ('điểm khớp (log-likelihood trung bình)', 'match score (mean log-likelihood)'), ('Điểm khớp trên lưới ±15 m × ±3 m', 'Match score on the ±15 m × ±3 m grid'), ('điều kiện mới loại các frame này', 'the new condition rejects these frames'), ('đỉnh của điểm khớp', 'peak of the match'), ('đỉnh NCC', 'NCC peak'), ('độ cao (m)', 'height (m)'), ('độ cao z', 'height z'), ('dời dọc đường so với bộ bám (m)', 'along-road shift vs. tracker (m)'), ('dời dọc đường (m)', 'along-road shift (m)'), ('dời dọc (m)', 'along shift (m)'), ('dời mọi pose sang ngang L (m)', 'shift all poses sideways by L (m)'), ('dời ngang (m)', 'lateral shift (m)'), ('độ lệch chuẩn gia tốc', 'accel. standard deviation'), ('trong 0.5 s (m/s²)', 'over 0.5 s (m/s²)'), ('được chiếu vào ảnh fisheye bằng thông số camera; vùng tô vàng = nắp capo (bị che, không dùng)', 'projected into the fisheye image with camera parameters; yellow area = hood (occluded, not used)'), ('frame 1100: đèn đỏ, ô chờ → đỉnh rõ', 'frame 1100: red light, waiting box → clear peak'), ('frame 3050: dừng cuối, không vạch → phẳng', 'frame 3050: final stop, no markings → flat'), ('frame 390: chỉ có vạch dọc → gần phẳng', 'frame 390: only longitudinal lines → nearly flat'), ('% frame GICP hợp lệ', '% valid GICP frames'), ('gần vạch dừng → đỉnh rõ', 'frame {kb}: near stop line → clear peak'), ('gia tốc tiến TB', 'mean forward accel.'), ('(trừ lúc đứng, m/s²)', '(excluding standstill, m/s²)'), ('– GICP chỉ nhìn được 1–2 m', '– GICP only sees 1–2 m'), ('GICP gần như không sai trên point cloud hoàn hảo; sai số đến từ point cloud do AI dựng', 'GICP is almost exact on a perfect point cloud; the errors come from the AI-built point cloud'), ('gốc camera lệch', 'camera origin offset'), ('point cloud hoàn hảo (lấy từ bản đồ),', 'perfect point cloud (from the map),'), ('khởi đầu lệch', 'starts offset'), ('point cloud hoàn hảo', 'perfect point cloud'), ('khởi đầu đúng', 'starts correct'), ('point cloud THẬT (3cameras_ply, lượt 1)', 'REAL point cloud (3cameras_ply, pass 1)'), ('point cloud × 3 (code mẫu)', 'point cloud × 3 (sample code)'), ('(do theo mặt đường)', 'point cloud × {s9:.2f} (measured from road)'), ('hướng chạy tính từ vị trí GNSS (chỉ có khi xe chạy)', 'heading from GNSS positions (only while moving)'), ('init_guess (có nhiễu)', 'init_guess (noisy)'), ('kết quả cuối Q4', 'final Q4 result'), ('kết quả Q4', 'Q4 result'), ('khoảng cách từ điểm của point cloud ảnh tới bản đồ (m)', 'distance from image-cloud points to the map (m)'), ('khoảng cách phía trước (m)', 'distance ahead (m)'), ('khoảng cách tới bản đồ: trung vị', 'distance to map: median'), ('% điểm < 0.5 m', '% of points < 0.5 m'), ('khoảng cách', 'distance'), ('lệch so với GNSS (m)', 'offset from GNSS (m)'), ('mặt đường: z = −h, h =', 'road: z = −h, h ='), ('đơn vị', 'units'), ('méo theo khoảng cách', 'distortion with distance'), ('Một cặp ±L tách được lỗi vị trí P =', 'A ±L pair separates the position error P ='), ('và phần yaw 0.2·Y =', 'and the yaw part 0.2·Y ='), ('ngang (đơn vị point cloud)', 'lateral (point-cloud units)'), ('phía trước (đơn vị point cloud)', 'ahead (point-cloud units)'), ('ngang (m), dương = bên trái xe', "lateral (m), + = car's left"), ('ngưỡng 0.1 m/s²', 'threshold 0.1 m/s²'), ('ngưỡng mới', 'new threshold'), ('nhiễu của độ sửa GICP (m)', 'noise of the GICP correction (m)'), ('nhiễu dọc', 'along noise'), ('nhiễu ngang', 'lateral noise'), ('nhiễu độ sâu', 'depth noise'), ('GICP dời vị trí', 'GICP moved the position by'), ('° để hai đám điểm trùng nhau', '° so the two point groups overlap'), ('và quay', 'and rotated'), ('phía trước', 'ahead'), ('sang trái', 'to the left'), ('Quét offline Track01 (GICP lượt 1, mỗi lần đổi 1 tham số): tầm 20 m ổn định nhất; voxel gần như không ảnh hưởng', 'Offline sweep on Track01 (GICP pass 1, one parameter changed each time): 20 m range is most stable; voxel size barely matters'), ('raw_ply (LoGeR, 1 camera): nhìn từ trên', 'raw_ply (LoGeR, 1 camera): top view'), ('đơn vị tuỳ ý – cả cảnh chỉ rộng vài đơn vị', 'arbitrary units – the whole scene is only a few units wide'), ('raw_ply nhìn ngang (dải giữa xe)', 'raw_ply side view (strip in the middle of the car)'), ('tỉ lệ = 1.646 m / h ≈ ', 'scale = 1.646 m / h ≈ '), ('sai số vị trí mỗi frame sau GICP (m, RMS)', 'position error per frame after GICP (m, RMS)'), ('tầm 20 m', 'range 20 m'), ('tầm 30 m', 'range 30 m'), ('tham chiếu', 'reference'), ('thời gian từ đầu Track02 (s)', 'time since start of Track02 (s)'), ('tỉ lệ ×', 'scale ×'), ('ba ảnh fisheye 1440×928 của cùng một thời điểm', 'Track01, frame {K1}: three fisheye images (1440×928) at the same moment'), ('Track02: 13 s đầu yaw GNSS giữ −15.2° trong khi yaw thật ≈ −19.8°', 'Track02: first 13 s GNSS yaw stays at −15.2° while the true yaw ≈ −19.8°'), ('đặt tại vị trí GNSS: ở ×3 cả khung cảnh co lại', 'Track01 frame {K} placed at GNSS pose: at ×3 the whole scene shrinks'), ('chỉ còn bán kính ~13 m – không có chỗ nào khớp đúng', 'only a ~13 m radius left – nothing matches'), ('Track03 frame 1100 (đèn đỏ): camera hai bên nhìn mặt đường ngay cạnh xe (dưới 5 m), nơi camera trước không thấy', 'Track03 frame 1100 (red light): side cameras see the road right beside the car (under 5 m), where the front camera cannot'), ('khớp lưới (CSM) nhìn thấy vị trí đúng cách', 'grid matching (CSM) sees the correct position'), ('m dọc đường ', 'm along the road '), ('từ ảnh camera tới phép đo vị trí, từng bước', 'Track03 frame {k}: from camera image to position measurement, step by step'), ('Track03 lúc chạy lại: vùng hồng = ZUPT cũ tưởng xe đứng yên (gia tốc ít dao động) dù xe đang tăng tốc đều;', 'Track03 restart: pink = old ZUPT thought the car was standing still (little accel. variation) while it was accelerating steadily;'), ('Track03 lúc khởi đầu: init_guess chỉ hướng', 'Track03 start: init_guess points'), ('(đen), nhưng xe thật đi theo giả thuyết +18° (xanh)', '(black), but the true car follows hypothesis +18° (blue)'), ('Trước: point cloud đặt tại vị trí GNSS + Kalman', 'Before: point cloud placed at GNSS + Kalman pose'), ('Sau GICP: point cloud khớp với tường / cây của bản đồ', 'After GICP: point cloud matches walls / trees of the map'), ('Sau GICP', 'After GICP'), ('Trường xác suất của bản đồ (đen = gần cột / tường / cây)', 'Map likelihood field (black = near poles / walls / trees)'), ('điểm trong ô 50×50 m', 'points in a 50×50 m cell'), ('Vạch làn chốt vị trí ngang ở mọi frame; vị trí dọc chỉ được chốt khi có vạch cắt ngang hướng đi', 'Lane lines fix the lateral position in every frame; the along position is fixed only where a line crosses the path'), ('vị trí bộ bám Z3a', 'tracker Z3a position'), ('vị trí của bộ bám mới (A2h)', 'new tracker position (A2h)'), ('vị trí dự đoán (N)', 'predicted position (N)'), ('voxel 0.2 m (thử: chậm hơn 3×)', 'voxel 0.2 m (test: 3× slower)'), ('voxel 0.3 m (pipeline của nhóm)', 'voxel 0.3 m (team pipeline)'), ('voxel 1 m (code mẫu)', 'voxel 1 m (sample code)'), ('xe đạt 4 m/s', 'car reaches 4 m/s'), ('yaw của topic GNSS (bậc thang, đứng im khi xe dừng)', 'GNSS topic yaw (steps, frozen while stopped)'), ('yaw dựng lại bằng gyro (trừ bias −0.293°/s)', 'yaw rebuilt from gyro (bias −0.293°/s removed)'), ('Bản đồ LiDAR Track01 quanh frame 752 (màu = độ cao)', 'LiDAR map of Track01 around frame 752 (colour = height)'), ('Sau', 'After'), ('Trước', 'Before')]
    _TR.append(('(do theo mặt đường)', '(measured from road)'))
    _TR += [("(đo theo mặt đường)", "(measured from road)"), ("mỗi chấm = một điểm trên mặt đường của bản đồ", "each dot = one point on the map road surface"),
            ("(lưới 1 m,", "(grid 1 m,"), ("±6 m ngang)", "±6 m lateral)"), ("điểm = 0.2·Y", "score = 0.2·Y")]
    _TR.sort(key=lambda kv: -len(kv[0]))
    _orig_set_text = _mt.Text.set_text
    def _set_text_en(self, s):
        s = "" if s is None else str(s)
        for vi, en in _TR:
            s = s.replace(vi, en)
        _orig_set_text(self, s)
    _mt.Text.set_text = _set_text_en
RES = os.path.join(REPO, "src", "localization", "result")
os.makedirs(OUT, exist_ok=True)
BLUE, ORANGE, AQUA, YELLOW, VIOLET = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#6250d6"
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e4e0"
MAPC = np.array([0x3F, 0xB8, 0xC8]) / 255
CAMC = np.array([0xF2, 0xA2, 0x3A]) / 255
BG = np.array([0x14, 0x24, 0x2E]) / 255
plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.color": GRID, "grid.linewidth": 0.6, "legend.frameon": False})


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", name)


def clean(ax):
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)


def read_pcd_xyz(path):
    with open(path, "rb") as fh:
        head = b""
        while not head.endswith(b"DATA binary\n"):
            head += fh.readline()
        n = int(re.search(rb"POINTS (\d+)", head).group(1))
        return np.frombuffer(fh.read(n * 12), np.float32).reshape(n, 3)


def rot(xy, yaw):
    c, s = np.cos(yaw), np.sin(yaw)
    return np.stack([c * xy[:, 0] - s * xy[:, 1], s * xy[:, 0] + c * xy[:, 1]], 1)


# =========================================================== 1. Track01: ba camera
z1 = np.load(os.path.join(IN, "t1_clouds.npz"))
K1 = int(z1["k"])
fig, axes = plt.subplots(1, 3, figsize=(15, 3.4))
for ax, cam, ttl in zip(axes, ("fl", "f", "fr"), ("Camera trước-trái", "Camera trước", "Camera trước-phải")):
    d_ = os.path.join(DATA, "Track1", "Track1_images", f"Track1_{cam}_images")
    ax.imshow(plt.imread(os.path.join(d_, sorted(os.listdir(d_))[K1])))
    ax.set_title(ttl, loc="left", fontsize=10)
    clean(ax)
fig.suptitle(f"Track01, frame {K1}: ba ảnh fisheye 1440×928 của cùng một thời điểm", x=0.01, ha="left", fontsize=11)
save(fig, "x01_t1_cameras.png")

# =========================================================== 2. hai loại point cloud + đo tỉ lệ bằng mặt đường
raw, rgb, h = z1["raw"], z1["raw_rgb"], float(z1["raw_h"])
c3 = z1["c3"]
fig, axes = plt.subplots(1, 3, figsize=(16, 5), gridspec_kw={"width_ratios": [1, 1, 1.25]})
col = rgb / 255.0 if rgb.max() > 1.5 else rgb
ax = axes[0]
ax.scatter(-raw[:, 1], raw[:, 0], s=0.3, c=col, linewidths=0)
ax.set_aspect("equal")
ax.set_title("raw_ply (LoGeR, 1 camera): nhìn từ trên\nđơn vị tuỳ ý – cả cảnh chỉ rộng vài đơn vị", loc="left", fontsize=10)
ax.set_xlabel("ngang (đơn vị point cloud)")
ax.set_ylabel("phía trước (đơn vị point cloud)")
ax = axes[1]
near = (raw[:, 0] > 0.2) & (raw[:, 0] < 3) & (np.abs(raw[:, 1]) < 0.6)
ax.scatter(raw[near, 0], raw[near, 2], s=0.5, c=col[near], linewidths=0)
ax.axhline(-h, color=ORANGE, lw=2)
ax.text(0.25, -h + 0.03, f"mặt đường: z = −h, h = {h:.3f} đơn vị", color=ORANGE, fontsize=9)
ax.plot(0, 0, marker="o", color=INK)
ax.text(0.05, 0.03, "camera", fontsize=9)
ax.set_title("raw_ply nhìn ngang (dải giữa xe)\ntỉ lệ = 1.646 m / h ≈ " + f"{1.646 / h:.1f}", loc="left", fontsize=10)
ax.set_xlabel("phía trước")
ax.set_ylabel("độ cao z")
ax = axes[2]
r = np.hypot(c3[:, 0], c3[:, 1])
sel = r < 45
sc = ax.scatter(-c3[sel, 1], c3[sel, 0], s=0.2, c=c3[sel, 2], cmap="viridis", vmin=-2.5, vmax=4, linewidths=0)
ax.set_aspect("equal")
ax.set_title("3cameras_ply (MapAnything, 3 camera): gần đúng mét\n~330 nghìn điểm, nhìn được cả hai bên xe", loc="left", fontsize=10)
ax.set_xlabel("ngang (m)")
ax.set_ylabel("phía trước (m)")
fig.colorbar(sc, ax=ax, label="độ cao (m)", shrink=0.8)
save(fig, "x02_t1_clouds.png")

# =========================================================== 3. GICP: point cloud trên bản đồ, trước / sau
mxy, mh = z1["map_xy"], z1["map_h"]
st = (mh > 0.4) & (mh < 3.0)
s = float(z1["scale"])
pts = c3 * s
keep = (np.hypot(pts[:, 0], pts[:, 1]) < 40) & (pts[:, 2] > -float(z1["ground_h"]) * s + 0.4)
fig, axes = plt.subplots(1, 2, figsize=(14, 6.4))
P2 = pts[keep][::3, :2]
Mst = mxy[st]
for ax, key, ttl in ((axes[0], "guess", "Trước: point cloud đặt tại vị trí GNSS + Kalman"),
                     (axes[1], "gicp", "Sau GICP")):
    px, py, pyaw = z1[key]
    w = rot(P2, pyaw) + [px, py]
    near = Mst[np.all(np.abs(Mst - [px, py]) < 45, axis=1)][::2]
    dist = np.concatenate([np.sqrt(((c_[:, None, :] - near[None]) ** 2).sum(-1)).min(1) for c_ in np.array_split(w, 20)])
    ax.scatter(Mst[:, 0], Mst[:, 1], s=1.2, c="#9a9a96", linewidths=0, label="bản đồ LiDAR (vật cao 0.4–3 m)")
    sc = ax.scatter(w[:, 0], w[:, 1], s=1.5, c=np.minimum(dist, 1.0), cmap="RdYlGn_r", vmin=0, vmax=1, linewidths=0)
    ax.plot(px, py, marker="^", color=INK, ms=9)
    ax.set_xlim(px - 22, px + 22)
    ax.set_ylim(py - 18, py + 18)
    ax.set_aspect("equal")
    ax.set_title(f"{ttl}\nkhoảng cách tới bản đồ: trung vị {np.median(dist):.2f} m, {100 * np.mean(dist < 0.5):.0f} % điểm < 0.5 m",
                 loc="left", fontsize=10)
    ax.legend(loc="lower left", fontsize=8, markerscale=8)
fig.colorbar(sc, ax=axes, label="khoảng cách từ điểm của point cloud ảnh tới bản đồ (m)", shrink=0.8)
gx, gy = z1["gicp"][:2] - z1["guess"][:2]
fig.suptitle(f"Track01 frame {K1}: GICP dời vị trí {np.hypot(gx, gy):.2f} m và quay "
             f"{np.degrees(z1['gicp'][2] - z1['guess'][2]):+.1f}° để hai đám điểm trùng nhau", x=0.01, ha="left", fontsize=11)
save(fig, "x03_t1_gicp.png")

# =========================================================== 4. Track03 CSM
z = np.load(os.path.join(IN, "t3_csm.npz"))
fig, axes = plt.subplots(1, 2, figsize=(15, 6.2), gridspec_kw={"width_ratios": [1.15, 1]})
ax = axes[0]
ax.imshow(np.exp(z["lf"]), origin="lower", extent=z["extent"], cmap="Greys", vmin=0, vmax=1)
ax.scatter(z["pts_at_N"][:, 0], z["pts_at_N"][:, 1], s=4, c=ORANGE, label="điểm của point cloud tại vị trí bộ bám cũ (N)")
ax.scatter(z["pts_at_best"][:, 0], z["pts_at_best"][:, 1], s=4, c=BLUE, label="cùng các điểm đó tại đỉnh CSM")
ax.plot(*z["pose"][:2], marker="^", color=ORANGE, ms=10)
ax.plot(*z["a2h"], marker="*", color=AQUA, ms=12, label="vị trí của bộ bám mới (A2h)")
ax.set_aspect("equal")
e = z["extent"]
ax.set_xlim(e[0], e[1])
ax.set_ylim(e[2], e[3])
ax.legend(loc="upper right", fontsize=8, framealpha=0.9, frameon=True)
ax.set_title("Trường xác suất của bản đồ (đen = gần cột / tường / cây)", loc="left", fontsize=10)
ax = axes[1]
im = ax.imshow(z["score"].T, origin="lower", aspect="auto", extent=[z["da"][0], z["da"][-1], z["dl"][0], z["dl"][-1]],
               cmap="viridis")
ib = np.unravel_index(np.argmax(z["score"]), z["score"].shape)
ax.plot(z["da"][ib[0]], z["dl"][ib[1]], marker="+", color="white", ms=16, mew=2.5, label="đỉnh của điểm khớp")
ax.plot(*z["rel_along"], marker="*", color=AQUA, ms=14, label="A2h")
ax.plot(0, 0, marker="^", color=ORANGE, ms=10, label="vị trí dự đoán (N)")
ax.set_xlabel("dời dọc đường (m)")
ax.set_ylabel("dời ngang (m)")
ax.legend(loc="upper left", fontsize=8)
fig.colorbar(im, ax=ax, label="điểm khớp (log-likelihood trung bình)")
ax.set_title("Điểm khớp trên lưới ±15 m × ±3 m", loc="left", fontsize=10)
fig.suptitle(f"Track03 frame {int(z['k'])}: khớp lưới (CSM) nhìn thấy vị trí đúng cách {abs(z['rel_along'][0]):.1f} m dọc đường "
             "– GICP chỉ nhìn được 1–2 m", x=0.01, ha="left", fontsize=11)
save(fig, "x04_t3_csm.png")

# =========================================================== 5–7. vạch sơn: IPM, từng bước, camera bên
p = np.load(os.path.join(IN, "t3_paint_steps.npz"))
for k in (390, 1100):
    img = p[f"img{k}"]
    fig, ax = plt.subplots(figsize=(13, 3.8))
    ax.imshow(img, cmap="gray")
    ax.imshow(np.where(p["mask"], np.nan, 1.0), cmap="autumn", alpha=0.35, vmin=0, vmax=1)
    ok = p[f"ok{k}"]
    sc = ax.scatter(p[f"u{k}"][ok], p[f"v{k}"][ok], c=p[f"ga{k}"][ok], cmap="plasma", s=12)
    fig.colorbar(sc, ax=ax, label="khoảng cách phía trước (m)", pad=0.01)
    ax.set_title(f"IPM, frame {k}: mỗi chấm = một điểm trên mặt đường của bản đồ (lưới 1 m, 5–18 m phía trước, ±6 m ngang)\n"
                 "được chiếu vào ảnh fisheye bằng thông số camera; vùng tô vàng = nắp capo (bị che, không dùng)", loc="left", fontsize=10)
    clean(ax)
    save(fig, f"x05_t3_ipm_{k}.png")

    fig, axes = plt.subplots(2, 3, figsize=(15, 9.5))
    ext = [7, -7, 5, 18]

    def bevshow(ax, a, ttl, cmap="gray", vmax=None):
        ax.imshow(a[::-1, ::-1] if a.ndim == 2 else a, cmap=cmap, extent=[7, -7, 5, 18], vmax=vmax, aspect="equal")
        ax.set_title(ttl, loc="left", fontsize=10)
        ax.set_xlabel("ngang (m), dương = bên trái xe")
        ax.set_ylabel("phía trước (m)")
        ax.grid(False)
    axes[0, 0].imshow(img, cmap="gray", aspect="auto")
    axes[0, 0].set_title("① Ảnh camera trước (đã cắt hàng 420–799)", loc="left", fontsize=10)
    clean(axes[0, 0])
    bevshow(axes[0, 1], np.nan_to_num(p[f"grey{k}"], nan=0), "② Chiếu ngược xuống mặt đường (IPM)")
    bevshow(axes[0, 2], p[f"th{k}"], "③ Vạch sơn camera: chỉ giữ cấu trúc sáng, hẹp < 0.7 m", cmap="magma")
    bevshow(axes[1, 0], np.nan_to_num(p[f"inten{k}"], nan=0), "④ Cường độ LiDAR của bản đồ (cùng ô)", vmax=np.nanpercentile(p[f"inten{k}"], 99))
    bevshow(axes[1, 1], np.nan_to_num(p[f"mpaint{k}"], nan=0), "⑤ Vạch sơn bản đồ (white top-hat 0.7 m)", cmap="magma")
    ax = axes[1, 2]
    vol = p[f"vol{k}"]
    na, nl, res = int(p["na"]), int(p["nl"]), float(p["res"])
    im = ax.imshow(vol.T, origin="lower", extent=[-na * res, na * res, -nl * res, nl * res], cmap="viridis", aspect="auto")
    ib = np.unravel_index(np.argmax(vol), vol.shape)
    ax.plot((ib[0] - na) * res, (ib[1] - nl) * res, "+", color="white", ms=16, mew=2.5, label=f"đỉnh NCC {vol.max():.2f}")
    ax.plot(*p[f"q{k}"], "*", color=AQUA, ms=13, label="kết quả cuối Q4")
    ax.plot(0, 0, "^", color=ORANGE, ms=9, label="vị trí bộ bám Z3a")
    ax.set_xlabel("dời dọc (m)")
    ax.set_ylabel("dời ngang (m)")
    ax.legend(fontsize=8, loc="upper left")
    ax.set_title("⑥ So ③ với ⑤ ở mọi độ dời (NCC qua FFT)", loc="left", fontsize=10)
    fig.colorbar(im, ax=ax, shrink=0.8)
    fig.suptitle(f"Track03 frame {k}: từ ảnh camera tới phép đo vị trí, từng bước", x=0.01, ha="left", fontsize=12)
    save(fig, f"x06_t3_paint_steps_{k}.png")

fig, axes = plt.subplots(1, 3, figsize=(15, 3.2), gridspec_kw={"width_ratios": [1, 1.4, 1]})
for ax, key, ttl in zip(axes, ("img_fl", "img1100", "img_fr"), ("Camera trước-trái", "Camera trước", "Camera trước-phải")):
    ax.imshow(p[key], cmap="gray", aspect="auto")
    ax.set_title(ttl, loc="left", fontsize=10)
    clean(ax)
fig.suptitle("Track03 frame 1100 (đèn đỏ): camera hai bên nhìn mặt đường ngay cạnh xe (dưới 5 m), nơi camera trước không thấy",
             x=0.01, ha="left", fontsize=11)
save(fig, "x07_t3_side_cams.png")

# =========================================================== 8. đường NCC theo phương dọc
pr = np.load(os.path.join(IN, "t3_profiles.npz"))
da = (np.arange(len(pr["f390"])) - len(pr["f390"]) // 2) * 0.1
kb = int(pr["kbest"][0])
fig, axes = plt.subplots(1, 4, figsize=(18, 3.9), sharey=True)
for ax, k, ttl in zip(axes, (kb, 390, 1100, 3050), (f"frame {kb}: gần vạch dừng → đỉnh rõ", "frame 390: chỉ có vạch dọc → gần phẳng",
                                                   "frame 1100: đèn đỏ, ô chờ → đỉnh rõ", "frame 3050: dừng cuối, không vạch → phẳng")):
    ax.plot(da, pr[f"f{k}"], color=BLUE, lw=2, label="camera trước")
    ax.plot(da, pr[f"s{k}"], color=ORANGE, lw=2, label="camera bên")
    ax.axvline(pr[f"q{k}"][0], color=AQUA, ls="--", lw=1.5, label="kết quả Q4")
    ax.set_title(ttl, loc="left", fontsize=10)
    ax.set_xlabel("dời dọc đường so với bộ bám (m)")
axes[0].set_ylabel("NCC")
axes[0].legend(fontsize=8)
fig.suptitle("Vạch làn chốt vị trí ngang ở mọi frame; vị trí dọc chỉ được chốt khi có vạch cắt ngang hướng đi", x=0.01,
             ha="left", fontsize=11)
save(fig, "x08_t3_ncc_profiles.png")

# =========================================================== 9. ZUPT lúc xe chạy lại
im_ = np.load(os.path.join(IN, "t3_imu.npz"))
t, acc, ft = im_["t"], im_["acc"], im_["ft"]
b = acc[(t > ft[1500]) & (t < ft[2100]), 0].mean()
ks = np.arange(2120, 2330)
sd, mx = [], []
for k in ks:
    j0, j1 = np.searchsorted(t, ft[k] - 0.5), np.searchsorted(t, ft[k], side="right")
    sd.append(float(np.linalg.norm(acc[j0:j1].std(axis=0))))
    mx.append(float(acc[j0:j1, 0].mean() - b))
sd, mx = np.array(sd), np.array(mx)
old = sd < 0.1
new = old & (np.abs(mx) < 0.3)
fig, axes = plt.subplots(2, 1, figsize=(12, 5.6), sharex=True)
axes[0].plot(ks, sd, color=BLUE, lw=2)
axes[0].axhline(0.1, color=MUTED, ls="--")
axes[0].text(ks[0], 0.115, "ngưỡng 0.1 m/s²", fontsize=8, color=MUTED)
axes[0].set_ylabel("độ lệch chuẩn gia tốc\ntrong 0.5 s (m/s²)")
axes[1].plot(ks, mx, color=ORANGE, lw=2)
axes[1].axhline(0.3, color=MUTED, ls="--")
axes[1].text(ks[0], 0.33, "ngưỡng mới |a_x − b| < 0.3", fontsize=8, color=MUTED)
axes[1].set_ylabel("gia tốc tiến TB\n(trừ lúc đứng, m/s²)")
for ax in axes:
    for k, o, n_ in zip(ks, old, new):
        if o and not n_:
            ax.axvspan(k - 0.5, k + 0.5, color="#f6c7b6", lw=0)
axes[1].set_xlabel("frame")
fig.suptitle("Track03 lúc chạy lại: vùng hồng = ZUPT cũ tưởng xe đứng yên (gia tốc ít dao động) dù xe đang tăng tốc đều;"
             " điều kiện mới loại các frame này", x=0.01, ha="left", fontsize=10)
save(fig, "x09_t3_zupt.png")

# =========================================================== 10. yaw GNSS bậc thang ở đầu Track02
g = np.load(os.path.join(IN, "t2_gnss.npz"))
gt = (g["gt"] - g["gt"][0]) * 1e-9
gx, gy, gyaw = g["gx"], g["gy"], np.degrees(g["gyaw"])
sp = np.r_[0, np.hypot(np.diff(gx), np.diff(gy)) / np.diff(gt)]
crs = np.full(len(gt), np.nan)
for i in range(4, len(gt)):
    dx, dy = gx[i] - gx[i - 4], gy[i] - gy[i - 4]
    if np.hypot(dx, dy) > 1.0:
        crs[i] = np.degrees(np.arctan2(dy, dx))
t4 = gt[np.argmax(sp > 4.0)]
i4 = np.argmax(sp > 4.0)
it = (g["it"] - g["gt"][0]) * 1e-9
w = g["wz"] - np.radians(-0.293)
yaw_g = np.degrees(np.cumsum(np.r_[0, w[1:] * np.diff(it)]))
yaw_g += crs[i4 + 2] - np.interp(gt[i4 + 2], it, yaw_g)
fig, ax = plt.subplots(figsize=(12, 4.2))
ax.step(gt, gyaw, where="post", color=ORANGE, lw=2, label="yaw của topic GNSS (bậc thang, đứng im khi xe dừng)")
ax.plot(gt, crs, color=BLUE, lw=1.5, label="hướng chạy tính từ vị trí GNSS (chỉ có khi xe chạy)")
ax.plot(it, yaw_g, color=AQUA, lw=2, label="yaw dựng lại bằng gyro (trừ bias −0.293°/s)")
ax.axvline(t4, color=MUTED, ls=":")
ax.text(t4 + 0.3, ax.get_ylim()[0] + 1, "xe đạt 4 m/s", fontsize=8, color=MUTED)
ax.set_xlim(0, 30)
ax.set_ylim(-24, -12)
ax.set_xlabel("thời gian từ đầu Track02 (s)")
ax.set_ylabel("yaw (°)")
ax.legend(fontsize=8, loc="best")
ax.set_title("Track02: 13 s đầu yaw GNSS giữ −15.2° trong khi yaw thật ≈ −19.8°", loc="left", fontsize=11)
save(fig, "x10_t2_gnss_yaw.png")

# =========================================================== 11. dò bảng điểm: cặp ±L
S0, Sp, Sm, cyaw, L = 1.25992, 1.37688, 1.40077, 0.3552, 0.5
P = S0 - cyaw
e = ((Sp - cyaw) ** 2 - (Sm - cyaw) ** 2) / (4 * L)
xs = np.linspace(-0.8, 0.8, 200)
fig, ax = plt.subplots(figsize=(8, 4.4))
ax.plot(xs, cyaw + np.sqrt(P ** 2 + 2 * xs * e + xs ** 2), color=BLUE, lw=2, label="điểm = 0.2·Y + √(P² + 2Lē + L²)")
ax.plot([-L, 0, L], [Sm, S0, Sp], "o", color=ORANGE, ms=9, label="3 lần nộp thật (Track01, 17/10)")
for xv, yv in ((-L, Sm), (0, S0), (L, Sp)):
    ax.text(xv, yv + 0.012, f"{yv:.5f}", ha="center", fontsize=9)
ax.set_xlabel("dời mọi pose sang ngang L (m)")
ax.set_ylabel("điểm Kaggle")
ax.set_title(f"Một cặp ±L tách được lỗi vị trí P = {P:.3f} m và phần yaw 0.2·Y = {cyaw:.3f}", loc="left", fontsize=11)
ax.legend(fontsize=8)
save(fig, "x11_probe_parabola.png")

# =========================================================== 12. giả thuyết yaw lúc khởi đầu Track03
T0 = np.loadtxt(os.path.join(DATA, "Track3", "init_guess.txt"), delimiter="," if "," in open(os.path.join(DATA, "Track3", "init_guess.txt")).read() else None)
yaw0 = np.arctan2(T0[1, 0], T0[0, 0])
Q = np.loadtxt(os.path.join(RES, "track3", "t3_Q4.csv"), delimiter=",", skiprows=1)
m3 = read_pcd_xyz(os.path.join(DATA, "Track3", "map_voxel_0.3m.pcd"))
x0, y0 = T0[0, 3], T0[1, 3]
sel = (np.abs(m3[:, 0] - x0) < 70) & (np.abs(m3[:, 1] - y0) < 60)
fig, ax = plt.subplots(figsize=(10, 7))
ax.scatter(m3[sel, 0], m3[sel, 1], s=0.2, c="#a9a9a5", linewidths=0)
for off in range(-30, 31, 6):
    a_ = yaw0 + np.radians(off)
    ax.plot([x0, x0 + 30 * np.cos(a_)], [y0, y0 + 30 * np.sin(a_)], color=AQUA if off == 18 else (INK if off == 0 else ORANGE),
            lw=3 if off == 18 else 1.4)
    ax.text(x0 + 32 * np.cos(a_), y0 + 32 * np.sin(a_), f"{off:+d}°", fontsize=8, ha="center")
ax.plot(Q[:250, 1], Q[:250, 2], color=BLUE, lw=2.5, label="250 frame đầu của kết quả cuối")
ax.plot(x0, y0, "o", color=AQUA, ms=9, label="init_guess (có nhiễu)")
ax.set_aspect("equal")
ax.set_xlim(x0 - 70, x0 + 20)
ax.set_ylim(y0 - 45, y0 + 45)
ax.legend(fontsize=9, loc="lower right")
ax.set_title(f"Track03 lúc khởi đầu: init_guess chỉ hướng {np.degrees(yaw0):.1f}° (đen), nhưng xe thật đi theo giả thuyết +18° (xanh)\n"
             "11 giả thuyết (−30…+30°) chạy song song; mỗi frame chỉ xuất giả thuyết tốt nhất tại chính frame đó", loc="left", fontsize=10)
save(fig, "x12_t3_mht.png")

# =========================================================== 13. bản đồ ở các cỡ voxel
gx_, gy_ = z1["guess"][:2]
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
for ax, f, ttl in zip(axes, ("map_downsampled_1m.pcd", "map_voxel_0.3m.pcd", "map_voxel_0.2m.pcd"),
                      ("voxel 1 m (code mẫu)", "voxel 0.3 m (pipeline của nhóm)", "voxel 0.2 m (thử: chậm hơn 3×)")):
    m = read_pcd_xyz(os.path.join(DATA, "Track1", f))
    sel = (np.abs(m[:, 0] - gx_) < 25) & (np.abs(m[:, 1] - gy_) < 25)
    ax.scatter(m[sel, 0], m[sel, 1], s=0.3 if "1m" not in f else 3, c=m[sel, 2], cmap="viridis", linewidths=0)
    ax.set_aspect("equal")
    ax.set_title(f"{ttl}\n{sel.sum():,} điểm trong ô 50×50 m".replace(",", " "), loc="left", fontsize=10)
    clean(ax)
fig.suptitle("Bản đồ LiDAR Track01 quanh frame 752 (màu = độ cao)", x=0.01, ha="left", fontsize=11)
save(fig, "x13_map_voxel.png")

# =========================================================== 14. quét tham số T4 (offline)
rows = list(csv.DictReader(open(os.path.join(REPO, "docs", "nhat-ky", "data", "t4_sweep.csv"))))
lab = {"ref": "tham chiếu\n(40 m, map 0.3, ×1)", "range20": "tầm 20 m", "range30": "tầm 30 m", "res0.2": "map 0.2 m",
       "res0.5": "map 0.5 m", "scale0.95": "tỉ lệ ×0.95", "scale1.05": "tỉ lệ ×1.05"}
names = [r["run"] for r in rows]
fig, axes = plt.subplots(1, 2, figsize=(14, 4.2))
xx = np.arange(len(rows))
axes[0].bar(xx, [float(r["ok_pct"]) for r in rows], color=[AQUA if n == "range20" else BLUE for n in names], width=0.6)
axes[0].set_ylabel("% frame GICP hợp lệ")
axes[0].set_ylim(40, 62)
axes[1].bar(xx - 0.17, [float(r["noise_along"]) for r in rows], 0.34, color=BLUE, label="nhiễu dọc")
axes[1].bar(xx + 0.17, [float(r["noise_lat"]) for r in rows], 0.34, color=ORANGE, label="nhiễu ngang")
axes[1].set_ylabel("nhiễu của độ sửa GICP (m)")
axes[1].legend(fontsize=8)
for ax in axes:
    ax.set_xticks(xx, [lab.get(n, n) for n in names], fontsize=8, rotation=25, ha="right")
    ax.grid(axis="x", visible=False)
fig.suptitle("Quét offline Track01 (GICP lượt 1, mỗi lần đổi 1 tham số): tầm 20 m ổn định nhất; voxel gần như không ảnh hưởng",
             x=0.01, ha="left", fontsize=11)
save(fig, "x14_t4_sweep.png")

# =========================================================== 15. tỉ lệ ×3 (code mẫu) và ×9 + trôi của code mẫu
K = 40
ci1 = np.load(os.path.join(HOME, "SDC-midterm01", "cache", "Track1", "raw_ply", "index.npy"))
cx1 = np.load(os.path.join(HOME, "SDC-midterm01", "cache", "Track1", "raw_ply", "xyz.npy"), mmap_mode="r")
c40 = np.asarray(cx1[int(ci1[K, 0]):int(ci1[K, 0]) + int(ci1[K, 1])], np.float64)
gn1 = np.loadtxt(os.path.join(REPO, "docs", "nhat-ky", "submissions", "track1", "gnss_1.csv"), delimiter=",", skiprows=1)
m1 = read_pcd_xyz(os.path.join(DATA, "Track1", "map_voxel_0.3m.pcd"))
px, py, pyaw = gn1[K, 1:4]
sel = (np.abs(m1[:, 0] - px) < 45) & (np.abs(m1[:, 1] - py) < 45)
s9 = 1.646 / float(np.median(ci1[max(0, K - 56):K + 1, 3]))
fig, axes = plt.subplots(1, 2, figsize=(15, 6))
ax = axes[0]
ax.scatter(m1[sel, 0], m1[sel, 1], s=0.3, c="#b0b0ac", linewidths=0, label="bản đồ LiDAR")
for sc_, col_, lab in ((3.0, ORANGE, "point cloud × 3 (code mẫu)"), (s9, BLUE, f"point cloud × {s9:.2f} (đo theo mặt đường)")):
    w = rot(c40[:, :2] * sc_, pyaw) + [px, py]
    ax.scatter(w[::2, 0], w[::2, 1], s=0.6, c=col_, linewidths=0, alpha=0.7, label=lab)
ax.plot(px, py, "^", color=INK, ms=9)
ax.set_xlim(px - 40, px + 40)
ax.set_ylim(py - 40, py + 40)
ax.set_aspect("equal")
ax.legend(fontsize=8, markerscale=10, loc="lower left")
ax.set_title(f"Track01 frame {K} đặt tại vị trí GNSS: ở ×3 cả khung cảnh co lại\nchỉ còn bán kính ~13 m – không có chỗ nào khớp đúng",
             loc="left", fontsize=10)
ax = axes[1]
for t, col_ in (("1", BLUE), ("2", ORANGE)):
    B = np.loadtxt(os.path.join(REPO, "docs", "nhat-ky", "data", "baseline_partial", f"Track{t}_result.txt"))
    G = np.loadtxt(os.path.join(REPO, "docs", "nhat-ky", "submissions", f"track{t}", f"gnss_{t}.csv"), delimiter=",", skiprows=1)
    e = np.hypot(B[:, 3] - G[:len(B), 1], B[:, 7] - G[:len(B), 2])
    ax.plot(e, color=col_, lw=2, label=f"Track0{t}")
ax.set_xlabel("frame")
ax.set_ylabel("lệch so với GNSS (m)")
ax.legend()
ax.set_title("Code mẫu (×3, mỗi frame bắt đầu từ frame trước):\nsai số cộng dồn tới 91 m / 110 m", loc="left", fontsize=10)
save(fig, "x15_scale_x3.png")

# =========================================================== 16. point cloud "hoàn hảo": lỗi nằm ở đâu
VN = {"a: matcher only, offset start": "point cloud hoàn hảo (lấy từ bản đồ),\nkhởi đầu lệch 0.5 m / 2°"}
fig, ax = plt.subplots(figsize=(11, 5.4))
for t, col_, off in (("1", BLUE, -0.2), ("2", ORANGE, 0.2)):
    rows = list(csv.DictReader(open(os.path.join(REPO, "docs", "nhat-ky", "data", f"t2_synthetic_track{t}.csv"))))
    v = [np.hypot(float(r["along_rms"]), float(r["lat_rms"])) for r in rows]
    yy = np.arange(len(rows))[::-1]
    ax.barh(yy + off, v, 0.38, color=col_, label=f"Track0{t}")
    if t == "1":
        names = [r["case"] for r in rows]
for i, n in enumerate(names):
    pass
lab = {"a: matcher only, offset start": "point cloud hoàn hảo, khởi đầu lệch 0.5 m / 2°",
       "0: perfect cloud, true start": "point cloud hoàn hảo, khởi đầu đúng",
       "c: real 3cameras_ply (pass 1)": "point cloud THẬT (3cameras_ply, lượt 1)",
       "b: depth bias +0.2%/m (5% at 25 m)": "+ lỗi giả lập: méo độ sâu +0.2 %/m (5 % ở 25 m)",
       "b: camera origin 0.3 m forward": "+ lỗi giả lập: gốc camera lệch 0.3 m lên trước",
       "b: camera origin 0.3 m left": "+ lỗi giả lập: gốc camera lệch 0.3 m sang trái"}


def vn(n):
    if n in lab:
        return lab[n]
    n = n.replace("b: ", "+ lỗi giả lập: ").replace("scale x", "tỉ lệ ×").replace("depth noise", "nhiễu độ sâu").replace("of range", "khoảng cách")
    n = n.replace("range", "méo theo khoảng cách").replace("camera origin", "gốc camera lệch").replace("left", "sang trái")
    return n


ax.set_yticks(np.arange(len(names))[::-1], [vn(n) for n in names], fontsize=9)
ax.set_xlabel("sai số vị trí mỗi frame sau GICP (m, RMS)")
ax.legend()
ax.grid(axis="y", visible=False)
ax.set_title("GICP gần như không sai trên point cloud hoàn hảo; sai số đến từ point cloud do AI dựng", loc="left", fontsize=11)
save(fig, "x16_synthetic_gicp.png")
