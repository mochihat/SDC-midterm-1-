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

## 6. 25/10 – camera bên, κ 160, nhiều lượt (người dùng duyệt)

| File | So với | Thay đổi | Public |
|---|---|---|---|
| **`t3_PF2`** | PE3 | camera trước-trái / trước-phải là khối NCC riêng (`--side --separate`, `--kappa-side 40`) | **0.33** |
| `t3_PF1` | PE3 | κ 160 | 0.38 |
| `t3_PF3` | PE3 | `--kappa-side 80` | 0.47 |
| `t3_PG4` | PF2 | 3 lượt đo (cả camera bên) + `--kappa-time 2` | 0.47 → các lượt có camera bên trôi, bỏ |
| `t3_PG3` | PE3 | 3 lượt đo (chỉ camera trước) + `--kappa-time 2` | 0.38 (PE3 0.37) |

`t3_PH1` = PF2 + `--kappa-time 2` (1 lượt): phần public trùng PF2 từng frame (0–408: chênh 0.000 m), chỉ khác lúc đứng
(≤ 0.06 m) và cuối track (≤ 0.22 m) → ứng viên bài cuối (chưa nộp).
Tái lập: `CACHE_ROOT=… PASSES=1 SIDE=1 FUSE="--kappa 80 --kappa-motion 0.3 --sd-floor 0.3,0.15 --lever-along 0.15
--lever-lat 0.0 --kappa-side 40" bash tools/run_track3_paint.sh` = PF2 (trùng từng byte); thêm `FUSE_EXTRA="--kappa-time 2"` = PH1.

## 7. 25/10 tối – phần private: vị trí DỌC rung theo prior → chuyển động theo tốc độ IMU (`--motion imu`)

Người dùng: "còn tối ưu được track 3 không … để private được điểm cao". Không có nhãn cho phần private → chỉ dùng
các kiểm tra không cần bảng điểm.

**7.1 Các bản đã nộp khác nhau ở đâu (so với PF2, RMS vị trí):** đứng yên 950–2150 chỉ 0.01–0.10 m; nhưng lúc xe chạy
(409–950, 2150–2800) tới 0.3–0.9 m (PF1 κ160: 0.88 m ở 409–700). Ảnh NCC theo dọc / ngang: **ngang** có một gờ sáng rõ
(vạch làn) – mọi bản trùng nhau; **dọc** gần như phẳng (vạch song song hướng đi) → vị trí dọc chỉ được chốt ở vạch đứt,
vạch dừng, vạch sang đường; giữa các chỗ đó nó trôi theo prior.

**7.2 Độ trễ camera (bác bỏ):** thời điểm chụp (header) sớm hơn thời điểm frame (tên file raw_ply = thời điểm ghi bag)
trung bình 8.0 ms (sd 0.8) → 0.08 m ở 10 m/s, gần như hằng. Track01/02 (tham chiếu): lệch dọc ở 10–14 m/s +0.07 / +0.13 m
→ tay đòn dọc +0.15 của Track03 là lệch hình học, áp dụng được cả lúc đứng yên. Không đổi.

**7.3 Rung dọc:** tốc độ theo vị trí của Z3a / PF2 nhảy ±3 m/s giữa các frame (PF2: 0.11–1.05 m mỗi frame ở ~10 m/s),
tốc độ IMU (SpeedFilter của Z3a, cột `v_imu` trong `t3_Z3a_diag.csv`, nhân quả) thì mượt. Phần rung < 3 s của vị trí dọc so
với quãng đường tích phân IMU (xe thật không rung như vậy → đó là sai số): PF2 0.28 m (public), **0.51 m (409–950)**, 0.33 m
(khúc cua). Nhưng `v_imu` sai tỉ lệ (dựa vào odometry LoGeR): quãng đường bản đồ / quãng đường IMU theo cửa sổ 100 frame
= 0.82…1.07 lúc chạy thẳng, 1.25…1.47 lúc bò chậm vào cua.

**7.4 `tools/paint_fuse.py --motion imu`:** trạng thái (e, s): dự đoán e += s·v_imu·dt·u(yaw) − (bước của prior), s = tỉ lệ
tốc độ (bước ngẫu nhiên `--q-scale`), prior là phép đo yếu e = 0 (`--z-sd`, nhân theo quãng đường như κ – khi đứng yên
prior lặp lại cùng một sai số: bản đầu không nhân → vị trí đứng chờ bị kéo về Z3a, NCC 0.54 → 0.28, đã sửa), cập nhật vạch
sơn như cũ, s đi theo qua hiệp phương sai với e (khớp mômen). Chỉ dùng tốc độ IMU khi nó tốt: `--imu-vmin 4` m/s và tốc độ
quay của prior ≤ `--imu-wmax 3` °/s (bò chậm 2–3 m/s vào cua: tỉ lệ sai 25–37 % → bản không cổng lệch ~1 m ở 2400–2480);
còn lại = bước của prior như PF2. `--kappa-imu K`: κ trên các frame IMU (κ 80 + sàn 0.3 m thì phép đo từng frame vẫn áp đảo
→ còn rung); κ 80 giữ nguyên lúc chậm / đứng (bản κ 40 + sàn 0.1 ở mọi frame làm hỏng vị trí đứng chờ: NCC 0.54 → 0.45).
Kiểm tra: `--imu-vmin 1e9` → trùng từng byte PE3 / PF2.

**7.5 Thước đo không dùng bảng điểm – NCC camera BÊN tại pose đầu ra của bản chỉ dùng camera TRƯỚC** (camera bên nhìn
vùng đường khác, bộ lọc không tối ưu theo nó). Trên 17 bản đã nộp: tương quan với điểm public −0.94 (tất cả) / −0.77
(bản < 0.7) – phân biệt được chênh lớn, không phân biệt được < ~0.05 điểm. Không nhạy với sai số dọc ở đoạn vạch song
song. Phần public (0–409), bản chỉ camera trước:

| | PE3 (đã nộp 0.37) | κ_imu 40 | 20 | 10 | 5 | 2.5 |
|---|---|---|---|---|---|---|
| NCC camera bên 0–409 | 0.122 | 0.125 | 0.128 | **0.132** | **0.134** | 0.129 |
| rung dọc 409–950 (m) | 0.47 | 0.26 | 0.23 | 0.19 | 0.18 | 0.19 |

(tốt nhất trong 17 bản đã nộp: 0.127). Đứng yên / khúc cua / cuối track: như PE3 (cổng tắt IMU ở đó).

**7.6 Yaw khúc cua (24 % frame private):** hướng chạy (COG) − yaw = +5…+7° lúc quay 16–20 °/s. Hai giả thuyết: yaw Z3a
trễ ~0.33 s (sẽ mất ~0.23 điểm private) hoặc điểm tham chiếu đáp án nằm trước trục sau ~1.8 m (góc trượt ω·l/v – khớp
l = 1.6–2.1 m ở 4 thời điểm). Khối NCC có chiều yaw (±1.5°): ở 2450–2550 yaw tốt nhất của camera trước / bên quanh 0
(−0.75…+0.5°, không dồn về mép) → yaw Z3a đúng, COG lệch do góc trượt. Không sửa yaw.

**7.7 Vị trí đứng chờ:** đỉnh NCC tĩnh (trung bình 1100 frame): camera trước dọc +0.595 / ngang −0.412; camera bên
+0.481 / −0.411; PF2 +0.660 / −0.402 → ngang trùng 1 cm, dọc lệch 6.5 cm (hai loại camera lệch nhau 11 cm). Không đổi.

**7.8 Ứng viên (chờ người dùng duyệt nộp)** – đều = PF2 + `--motion imu --imu-vmin 4 --imu-wmax 3`, chỉ khác κ_imu:

| File | κ_imu | khác PF2: public / private (RMS) | rung dọc 409–950 (PF2 0.51) |
|---|---|---|---|
| `t3_Q1` | 20 | 0.13 / 0.24 m | 0.33 |
| `t3_Q2` | 10 | 0.18 / 0.29 m | 0.24 |
| `t3_Q3` | 5 | 0.23 / 0.37 m | 0.17 |

Đứng yên và yaw: trùng PF2 từng byte. Tái lập: `CACHE_ROOT=cache_test PASSES=1 SIDE=1 FUSE="<PF2>"
FUSE_EXTRA="--motion imu --imu-vmin 4 --imu-wmax 3 --kappa-imu 10" bash midterm01/tools/run_track3_paint.sh` = `t3_Q2`
(chạy lại từ ảnh / bản đồ, trùng từng byte).

**7.9 Kết quả nộp (người dùng duyệt, 25/10 19:38):** `t3_Q1` / `t3_Q2` / `t3_Q3` (κ_imu 20 / 10 / 5) = **0.28 / 0.28 / 0.28**
(PF2 0.33) → giảm rung dọc là thật; hạng 2 (đội 12: 0.24). Kaggle cắt 2 chữ số → không phân biệt được κ_imu 5–20.

**7.10 Đoạn cuối (2850–3142, ~9 % frame private): trượt dọc lúc giảm tốc.** Đường NCC dọc ở đoạn đứng yên cuối PHẲNG
(camera trước 0.17–0.23, camera bên 0.28–0.39 trên ±2 m) → không có vạch chốt dọc. PF2 / Q2 trượt lùi từ +0.1 (frame 2900,
mọi bản trùng) xuống −1.57 m so với Z3a lúc xe giảm tốc 3 → 0 m/s (κ 80 cộng dồn một độ dốc NCC rất nhẹ: camera trước
dốc về −, camera bên dốc về + → không đáng tin). Quãng đường 2900 → 3020: IMU × tỉ lệ đã học (0.905, sd 0.05) 3.27 m,
Z3a 4.25 m, PF2 2.57 m → IMU dự đoán −0.87 m, Z3a 0. Sửa: trễ (hysteresis) – đã chạy theo IMU (vào ở ≥ 4 m/s) thì ở lại
tới 0.5 m/s (`--imu-vstay 0.5`) nếu độ lệch chuẩn tỉ lệ lúc còn nhanh ≤ 0.08 (`--imu-stay-sd`; sau lúc đứng chờ 43 s nó là
0.19 → đoạn khởi động lại / bò vào cua giữ như Q2, ở đó cả hai camera ủng hộ Q2: NCC 0.36 / 0.25 so với 0.28 / 0.15 nếu
chạy theo IMU). Kết quả `t3_Q4`: trùng Q2 ở mọi nơi trừ đoạn cuối (vị trí đứng yên cuối −0.72 m thay vì −1.57 so với Z3a);
ngưỡng 0.06 / 0.08 / 0.1 cho cùng kết quả.

**7.11 Ứng viên đợt 2:** `t3_Q4` (bản cuối đề xuất; public = Q2), `t3_Q5` = Q4 + tay đòn dọc +0.25 (đang +0.15),
`t3_Q6` = Q4 + tay đòn ngang +0.10 (đang 0; PA1 −0.25 0.56 → PA2 −0.10 0.49 → PB2 0 0.47: chưa thử phía +). Tay đòn áp
dụng cả lúc đứng chờ đèn (44 % private) → chỉnh theo public có ích cho private.

**7.12 Kết quả đợt 2 (người dùng duyệt, 25/10 20:44):**

| File | So với Q4 | Public |
|---|---|---|
| **`t3_Q4`** | – (Q2 + trễ IMU ở đoạn cuối) | **0.28** (= Q2, như dự đoán: phần public trùng từng frame) |
| `t3_Q5` | tay đòn dọc +0.25 (đang +0.15) | 0.32 |
| `t3_Q6` | tay đòn ngang +0.10 (đang 0) | 0.29 |

Tay đòn là một dời hằng trong hệ xe (Q5 / Q6 lệch Q4 đúng 0.100 m ở MỌI frame, yaw trùng) → điểm đổi theo
RMSE² = σ² + (b + δ)², với b là sai lệch trung bình còn lại. Giả sử phần yaw ≈ 0.06 (vị trí ≈ 0.22): Q5 +0.03…+0.05 →
b_dọc ≈ 0…+0.1 → tay đòn dọc tối ưu ≈ +0.05…+0.15; Q6 +0.00…+0.02 → tay đòn ngang tối ưu ≈ 0…+0.05. Lợi ích còn lại
≤ ~0.01 (dưới mức Kaggle cắt 2 chữ số). Ứng viên tinh chỉnh (chưa nộp): `t3_Q7` = Q4 + dọc +0.10, `t3_Q8` = Q4 + ngang
+0.05 (`t3_Q9` = ngang −0.05: dự đoán xấu hơn, không đề xuất). **Bản cuối đề xuất hiện tại: `t3_Q4`.**

**7.13 Tinh chỉnh tay đòn (người dùng duyệt, 25/10 20:55):** `t3_Q7` (dọc +0.10) = 0.28, `t3_Q8` (ngang +0.05) = 0.28 →
không phân biệt được với Q4 sau khi Kaggle cắt 2 chữ số (đúng dự đoán ≤ 0.01). Giữ tay đòn +0.15 / 0 → **bản cuối đề xuất
vẫn là `t3_Q4`**. Đã dùng 13 / 15 lượt Track03 ngày 25/10.

**7.14 Còn gì để giảm sai số? (25/10 tối, không dùng bảng điểm)**
- Yaw: hướng NCC theo trục yaw ở vị trí Q4 (camera trước / bên, từng đoạn 100–600 frame) dao động ±0.5° giữa các cách đo
  và giữa hai nửa đoạn → không đủ tin để sửa yaw Z3a (đúng như PB3). Hướng chạy − yaw trên đoạn thẳng: public −0.13…+0.22°,
  private +0.01…+0.14°, sau khúc cua (2500–2850) +0.5…+0.6° (≈ 0.01 điểm private nếu là lỗi yaw).
- Camera trước ↔ camera bên: đỉnh NCC chênh dọc +0.06…+0.11 m, ngang +0.01…+0.05 m ở mọi đoạn → không có lỗi hiệu
  chuẩn giữa các camera để sửa.
- Rung còn lại của Q4 (lệch khỏi trung bình trượt 0.75 s): dọc 0.11 m public, 0.08 m 409–950; yaw 0.04° → nhiễu đã
  lọc gần hết; sai số còn lại là lệch chậm mà vạch sơn không thấy.
- Đầu track: camera trước không có ảnh ở frame 0–13 (h265 bắt đầu giữa GOP), camera bên từ frame 4; xe đang cua nhẹ
  ~4°/s nên chế độ IMU (ngưỡng 3°/s) chỉ bật từ frame 21, trong khi bước của Z3a ở frame 1–9 chập chờn (5–17 m/s).
  `--imu-wmax 5` (= `t3_R1`, chưa nộp): frame 6–81 đi theo tốc độ IMU, vị trí dọc frame 14–18 bớt kéo theo các ảnh
  trước đầu tiên (−0.67…−0.48 thay vì −0.44…−0.34 so với Z3a; IMU và camera trước ở frame 20–40 cùng chỉ ≈ −0.85);
  public lệch Q4 0.037 m RMS, private 0.011 m. Thước đo camera bên không phân biệt được → lợi dự kiến ≤ 0.01.
- Kết luận: các nút chỉnh còn lại đều ≤ 0.01; muốn giảm thêm ~0.05 (bằng đội 12) cần nguồn thông tin mới cho vị trí dọc
  (vd. cấu trúc 3D của bản đồ – cột, mép lề, tường – chiếu vào ảnh camera).

## 8. 26/10 – Thử cấu trúc 3D của bản đồ để chốt vị trí dọc (bác bỏ)

Ý tưởng: vật cao trong bản đồ (0.4–3 m trên mặt đường: cột, cây, tường, xe đỗ) chiếu vào ảnh camera trước; dời chúng theo
phương dọc (−3…+3 m) và chọn độ dời làm độ mạnh cạnh của ảnh tại các điểm chiếu lớn nhất (`tools/check3d_track3.py`,
`check3d_shift.py`, `check3d_scan.py`, `check3d_validate.py`).
- Track03 frame 1100: 1318 điểm vật cao trong khung ảnh, trải 5–17 m (hình `docs/report/fig/check3d/check3d_1100.png`);
  đỉnh ở +0.6 m, đường cong gợn (7.3–9.5), độ nổi ~10 %.
- Track03 60 frame đèn đỏ (960–2150): đỉnh ổn định +0.60 m (sd 0.28) – nhất quán nhưng chưa biết có đúng.
- **Kiểm chứng trên Track01** (pose = GNSS nội suy, thước = `lb_t1_r5`, chỉ để kiểm tra phép đo): 120 frame, tương quan
  giữa δ đo được và sai số dọc thật **−0.08**, |δ − thật| trung vị **2.93 m** (sai số GNSS chỉ 0.68 m), lệch TB +2.46 m;
  chọn frame có đỉnh rõ cũng không khá hơn. → thước đo "cạnh ảnh tại điểm chiếu" bị chi phối bởi vị trí điểm rơi trong
  ảnh (càng xa càng gần đường chân trời nhiều cạnh), không phải bởi việc khớp; đỉnh +0.6 m ở Track03 cũng là lệch kiểu này.
  **Bỏ hướng này** (không đủ thời gian làm thước đo tốt hơn trước 29/10). Bài cuối Track03 vẫn là `t3_Q4`.
