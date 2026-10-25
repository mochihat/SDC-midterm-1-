# 13 – 24/10: Track03 – khớp vạch sơn mặt đường (camera ↔ cường độ bản đồ LiDAR)

Người dùng (24/10 tối): "tập trung vào track 3 … public lên top 2, private cũng phải lên top 2". Luật Track03 (10/22):
nhân quả, không sửa tay file; người dùng báo TA cho chỉnh tham số / thuật toán theo điểm public.

## 1. Yaw đoạn đầu (bác bỏ)

Chạy cấu hình Track03 trên Track01 (có quỹ đạo gần đáp án `lb_t1_r5`, bắt đầu từ `init_guess.txt`): pha MHT chọn sai
giả thuyết (+21°) và sau đó yaw hội tụ chậm (τ 30 s) → −2…−3° trong ~200 frame. Thêm `--yaw-rls N0` (độ lợi yaw ít nhất
1/(n + N0) sau n lần khớp) và `--yaw-rls-dist D0` (trung bình theo quãng đường) vào `tools/track_localize.py`.
Track01 tốt hơn, Track02 xấu đi (lúc đứng / bò chậm các khung GICP cùng sai số). Track03 (người dùng duyệt nộp):

| File | Thay đổi so với `t3_Z3a` | Yaw đoạn đầu so với Z3a | Public |
|---|---|---|---|
| `t3_R4d20` | `--yaw-rls-dist 20` | −0.3…−0.65° | 0.85 |
| `t3_R4d5` | `--yaw-rls-dist 5` | −1.1…−1.3° | 0.96 |
| `t3_R4r3` | `--yaw-rls 3` | −1.8…−3.0° | 1.08 |
| (`t3_Z3a`) | | 0 | 0.80 |

→ điểm tăng đều theo độ kéo yaw xuống: yaw trung bình của Z3a ở phần public đã gần đúng; sai số chính là **vị trí**.

## 2. Vạch sơn: camera trước ↔ cường độ LiDAR của bản đồ

Bản đồ `map.pcd` có cường độ: vạch kẻ, vạch đứt, chữ trên đường, vạch dừng, vạch sang đường, ô chờ xe máy hiện rõ.
Camera trước (bag Track03 có 3 luồng h265) nhìn thấy đúng những vạch đó ở 5–18 m phía trước. Point cloud LoGeR sai
độ sâu theo khoảng cách (giới hạn ~0.5–1 m), còn vạch sơn trên bản đồ chính xác vài cm.

Công cụ mới (đều chạy trong `sdc-reg`, chỉ numpy / scipy; ffmpeg trên máy để giải mã h265):

| Công cụ | Việc |
|---|---|
| `tools/bag_h265.py` | luồng h265 camera trước → file `.h265` (Track03: khung khóa đầu tiên ở message 14 → frame 0–13 không có ảnh) |
| `tools/paint_map.py` | `map.pcd` (ASCII / nhị phân) → độ cao mặt đường (ô 0.5 m, phân vị 10 %) + cường độ mặt đường (ô 0.1 m) + vạch sơn bản đồ (white top-hat 0.7 m) |
| `tools/paint_bev.py` | mô hình fisheye (camera_info), chiếu lưới mặt đường (độ cao theo bản đồ) vào ảnh (IPM); vạch sơn camera = sáng hơn cả grey opening 0.7 m lẫn mức "mặt đường nắng" cục bộ (phân vị 70 %) → loại xe, vỉa hè, khe nắng giữa bóng cây; NCC có mặt nạ, trừ trung bình, qua FFT trên lưới dọc × ngang × yaw × pitch |
| `tools/paint_measure.py` | mỗi frame k: ảnh k so với vạch bản đồ quanh pose của quỹ đạo prior tại k (dọc ±2 m, ngang ±1.5 m, yaw ±1.5°, pitch ±0.5°) |
| `tools/paint_fuse.py` | Kalman trên sai số của prior: dự đoán (nhiễu quá trình), cập nhật = hậu nghiệm trên lưới (κ·NCC + prior Gauss, như CSM); κ nhân min(1, bước/0.3 m) (khi đứng yên cùng một khung cảnh = một phép đo, không phải hàng trăm); sàn độ lệch chuẩn; trừ tay đòn camera |
| `tools/run_track3_paint.sh` | cả chuỗi (Z3a → ảnh → bản đồ vạch → đo → lọc); chạy lại từ bộ đệm trống: **trùng 100 %** với `t3_PA2` |

Nhân quả: hàng k của file nộp chỉ dùng ảnh k, pose prior tại k (Z3a, nhân quả) và các phép đo ≤ k. Bản đồ cắt hành lang
30 m quanh prior chỉ để đọc nhanh: frame k chỉ dùng bản đồ trong ~25 m quanh pose prior tại k (nằm trong hành lang).

**Hiệu chuẩn camera (cùng xe, cùng mặt nạ nắp capo trên 3 track):** tổng NCC trên ~300 frame tại pose tham chiếu:
pitch **1.0°** (cả Track01 và Track02), yaw **−1.5°** (Track02 −1.5…−1.75, Track01 −1.0…−1.5). Độ lệch phép đo so với
tham chiếu (NCC ≥ 0.3): Track02 dọc ≈ 0 (độ phân tán 0.2 m), ngang −0.10 m (0.15 m); Track01 dọc +0.08, ngang −0.30…−0.46.

**Kiểm định Track01/02:** (a) prior giả = tham chiếu + sai số đã biết (dọc 0.6, ngang 0.3 m): phép đo bám đúng sai số
(ngang 0.13–0.2 m, dọc 0.2–0.7 m tùy NCC) – bản lọc đầu tiên khóa sai khi xe đứng yên (cùng một khung cảnh lặp lại) → thêm
κ theo quãng đường + sàn độ lệch chuẩn. (b) prior = bộ bám thật không GNSS (có đặt lại khi lệch > 3 m): vị trí 1.17 → 1.01 m
(Track01), 1.32 → 1.16 m (Track02). Hai track này nhiều cây, vạch mờ (NCC trung vị 0.19–0.22); Track03: 0.49.

## 3. Track03 – nộp (người dùng duyệt, 24/10 20:47)

| File | Tham số (prior `t3_Z3a`) | Public |
|---|---|---|
| `t3_PA1` | κ 20, κ theo bước 0.3 m, sàn 0.3 / 0.15 m, tay đòn ngang −0.25 | 0.56 |
| **`t3_PA2`** | như PA1, tay đòn ngang **−0.10** (Track02) | **0.49** |
| `t3_PA3` | như PA1, sàn 0.5 / 0.25 m | 0.55 |
| (`t3_Z3a`) | | 0.80 |

→ **0.80 → 0.49** (đội 8: 0.65; đội 12: 0.24). Hiệu chỉnh của PA2 so với Z3a: phần public 0.5–1.1 m RMS; lúc đứng yên ở
đèn đỏ (frame 950–2150, 45 % frame private) dời +0.6 m dọc (vạch dừng + vạch sang đường + ô chờ xe máy: NCC 0.58).
Phần private không đo được trên bảng điểm; phép đo vạch sơn ở đó còn rõ hơn phần public.

## 4. Tối 24/10 (21:29–21:44) – chỉnh tham số theo điểm public (người dùng duyệt từng đợt; mỗi bản đổi 1 tham số)

| File | So với | Thay đổi | Public |
|---|---|---|---|
| `t3_PC3` | PA2 | 3 lượt đo (cửa sổ tìm quanh lượt trước) + `--kappa-time 2` (đứng yên vẫn kéo dần về phép đo tĩnh) | 0.50 |
| **`t3_PB2`** | PA2 | tay đòn ngang 0 (PA2 −0.10, PA1 −0.25) | **0.47** |
| `t3_PB3` | PA2 | yaw theo vạch sơn (`--yaw-mode paint`) | 0.54 → yaw Z3a tốt hơn |
| `t3_PD1` | PB2 | tay đòn dọc +0.15 | 0.44 |
| `t3_PD2` | PB2 | tay đòn dọc −0.15 | 0.55 |
| **`t3_PD3`** | PB2 | κ 40 | **0.43** |
| `t3_PE1` | PB2 | κ 40 + tay đòn dọc +0.15 (gộp hai thay đổi đã thắng) | 0.39 |
| `t3_PE2` | PE1 | tay đòn dọc +0.30 | 0.42 |
| **`t3_PE3`** | PE1 | κ 80 | **0.37** |

Tay đòn (vị trí theo vạch sơn − điểm tham chiếu, hệ xe): dọc tối ưu ≈ +0.15 m, ngang ≈ 0…+0.05 m (Track02 đo −0.10,
Track01 −0.3 – Track03 lệch khác; một hiệu chỉnh hằng 0.1–0.2 m không đo được trên Track01/02). κ càng lớn càng tốt
(20 / 40 / 80 → 0.44 / 0.39 / 0.37). Bảng xếp hạng Track03 public: **hạng 2** (đội 12: 0.24; đội 8: 0.65).
Phần private: không đo được; ảnh chồng (camera / bản đồ) ở khúc cua, cuối track và lúc đứng chờ đèn cho thấy bản 3 lượt
khớp tốt hơn bản 1 lượt (bản cửa sổ tìm theo dự đoán của bộ lọc – `--online` – bị lạc ở khúc cua → không dùng).

## 5. 25/10 – yaw lúc đứng chờ đèn (44 % frame private) có cần sửa không?

Hai kiểm tra độc lập, đều không dùng bảng điểm: (a) hướng chạy (course over ground, mốc 5 m, chỉ đoạn thẳng) của quỹ đạo đã
hiệu chỉnh vạch sơn (`t3_PG3`) so với yaw xuất ra: frame 700–945 −0.14° (sd 0.35), 870–945 +0.15° (trên Track02 tham
chiếu, cùng phép đo: −0.3…+0.24°); (b) khớp vạch sơn tĩnh với lưới yaw 0.1° tại frame 1100 / 1600 / 2100: +0.1° (vùng
phẳng −0.4…+0.5°). → yaw đứng yên 159.68° đúng trong ~±0.2°; con số 159.15° của nhật ký 12 §8.3 (tính từ vị trí LoGeR) bị
thay thế. Không sửa yaw.
