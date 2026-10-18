# 03 – Baseline và các thí nghiệm NDT

Số liệu gốc: `data/baseline_partial/`, `data/ndt_debug/*.csv`, `data/ndt_correction_stats.txt`.

## 1. Baseline của TA chạy trên máy (không sửa gì)

Cấu hình mặc định (`localization.h`): `ply_scale = 3`, voxel đầu vào 0.3 m, bản đồ voxel 1 m, vùng bản đồ ±100 m,
NDT `resolution = 8 m`, `step = 0.8`, `epsilon = 0.05`, tối đa 30 vòng lặp. Điểm khởi đầu của mỗi frame = pose frame trước
(frame đầu dùng `init_guess.txt`). Không dùng GNSS/IMU.

Chạy song song 2 track (~3.5 s/frame Track01, ~1.5 s/frame Track02), so với quỹ đạo GNSS:

| | Bắt đầu lệch > 5 m | Lệch > 20 m | Lúc dừng |
|---|---|---|---|
| Track01 | frame 17 | frame 238 | frame 504: lệch **91.2 m**, yaw lệch **+113.5°** |
| Track02 | ngay frame 0 (5.7 m) | frame 505 | frame 782: lệch **110.0 m**, yaw lệch **−80.6°** |

→ NDT bị kéo vào điểm khớp sai từ sớm rồi kéo sai luôn các frame sau. Chạy tiếp là vô ích nên đã dừng
(điểm của baseline đã biết từ leaderboard: 1.79 / 1.93; có lẽ cấu hình TA dùng để nộp khác cấu hình mặc định trong code).

## 2. Sửa `localization.cpp`

Thêm vào node (tham số mới, mặc định giữ nguyên hành vi cũ):

| Tham số | Ý nghĩa |
|---|---|
| `prior_file` | CSV `idx,x,y,yaw` cho mỗi frame (GNSS đã làm mượt). NDT bắt đầu từ **x, y, yaw của prior**, giữ z/roll/pitch của frame trước |
| `max_correction_xy`, `max_correction_yaw_deg` | Nếu NDT kéo xa prior hơn ngưỡng thì **loại** kết quả, dùng prior |
| `frame_stride` | Chỉ chạy NDT mỗi N frame (các frame khác lấy prior) để thí nghiệm nhanh |
| `max_input_range` | Bỏ điểm ở xa camera (độ sâu từ ảnh càng xa càng sai) |
| `debug_file` | Ghi mỗi frame: prior, điểm khởi đầu, kết quả NDT, score, số điểm |

Script chạy: `run_fusion.sh` (không RViz). Bản build riêng `build_dev/install_dev` để không đụng bản gốc.

"**Hiệu chỉnh NDT**" dưới đây = (pose NDT − pose khởi đầu từ prior GNSS), tách thành dọc hướng chạy (along) và ngang (lateral).
Nếu NDT thật sự chính xác hơn GNSS, hiệu chỉnh phải **nhỏ, ổn định**, và cộng vào thì điểm phải tốt lên.

## 3. Thí nghiệm đợt 1 – tỉ lệ nhỏ (×2, ×3, ×4), NDT mặc định

`frame_stride = 10`, ngưỡng loại nới rộng 10 m / 30° (để thấy hiệu chỉnh "thật" của NDT).

| Thí nghiệm | Số frame NDT | Hiệu chỉnh vị trí (trung vị) | ≤ 1 m | Yaw: độ lệch chuẩn |
|---|---|---|---|---|
| Track02 ×2 | 330 (đủ) | 2.68 m | 23 % | **33.4°** |
| Track02 ×3 | 241 (dừng sớm) | 4.00 m | 21 % | 32.4° |
| Track02 ×4 | 144 (dừng sớm) | 3.49 m | 26 % | 24.0° |
| Track01 ×3 | 194 (dừng sớm) | 4.32 m | 16 % | **47.4°** |

→ Dù bắt đầu từ GNSS, NDT vẫn kéo đi 3–4 m và quay yaw ±30–47°: hoàn toàn không dùng được.
Frame đầu Track01 ở ×3 bị kéo về đúng chỗ baseline đã khớp sai (lệch ~4.5 m, +24°) → baseline sai vì **dữ liệu đầu vào sai tỉ lệ**,
không phải vì thiếu điểm khởi đầu tốt. Đây là lý do phải đi phân tích tỉ lệ (xem 02).

## 4. Thí nghiệm đợt 2 – tỉ lệ đúng (×9, ×10), NDT 4 m / 8 m

`frame_stride = 20`, `ndt_max_iterations = 50`, vùng bản đồ ±60 m, ngưỡng loại 10 m / 30°. Tất cả chạy đủ.

| Thí nghiệm | Số frame NDT | Hiệu chỉnh vị trí (trung vị) | ≤ 1 m | Along (trung vị) | Lateral (trung vị) | Yaw: trung vị / độ lệch chuẩn |
|---|---|---|---|---|---|---|
| Track02 ×9, NDT 8 m | 165 | 1.55 m | 35 % | −0.01 m | +0.54 m | −1.0° / 9.3° |
| **Track02 ×9, NDT 4 m** | 165 | **0.23 m** | **92 %** | −0.04 m | +0.07 m | **−0.07° / 2.1°** |
| Track02 ×10, NDT 4 m | 165 | 0.46 m | 81 % | −0.17 m | −0.04 m | +0.32° / 3.0° |
| **Track01 ×9, NDT 4 m** | 151 | **0.70 m** | 68 % | −0.29 m | +0.31 m | +0.01° / 2.0° |

Nhận xét:
- Sửa tỉ lệ từ 3 → 9 và độ phân giải 8 → 4 m: hiệu chỉnh giảm từ ~4 m xuống **0.2–0.7 m**, yaw từ ±30–47° xuống **±2°**. NDT đã **ổn định**.
- ×9 tốt hơn ×10; độ phân giải 4 m tốt hơn 8 m (point cloud ×9 phủ ~27 m, ô NDT 8 m quá thô).
- Ở Track01 hiệu chỉnh lớn hơn (trung vị 0.70 m, along −0.29 m) – phù hợp với việc GNSS Track01 kém hơn.

## 5. Ghép NDT vào GNSS – kết quả trên Kaggle

Cách ghép (`processing_codes/fuse_to_csv.py`): lấy hiệu chỉnh của các frame NDT hội tụ và nằm trong 2 m / 3°,
lọc trung vị (5 frame), làm mượt Gauss σ = 2 s, nội suy cho mọi frame rồi cộng vào vị trí của prior (yaw giữ nguyên).

| File | Dùng | Dịch so với prior | Điểm | So với prior |
|---|---|---|---|---|
| `fusion_s9r4_headingyaw_2.csv` (Track02) | 139/165 frame | 0.197 m RMS | 0.53520 | **xấu hơn** 0.062 (prior 0.47281) |
| `phys_yawb_ndt_1.csv` (Track01) | 118/151 frame | 0.471 m RMS | 1.27855 | **xấu hơn** 0.025 (prior 1.25338) |

**Kết luận:** NDT trên point cloud LoGeR (×9) ổn định nhưng **sai lệch của nó vẫn lớn hơn sai lệch của GNSS** so với đáp án,
nên ghép vào làm điểm xấu đi ở cả 2 track. Nguyên nhân có thể: độ sâu ước lượng từ một camera bị méo, tỉ lệ thay đổi ~5–7 % giữa các frame,
bản đồ giảm mẫu 1 m, và đáp án nhiều khả năng sinh ra từ chính hệ định vị đã tạo topic GNSS.
(File `fusion_s9r4_ndtyaw_2.csv` – cùng hiệu chỉnh vị trí, thêm hiệu chỉnh yaw của NDT – đã tạo nhưng **không nộp** vì chắc chắn cũng xấu hơn.)

## 6. NDT chỉ dùng ảnh (không GNSS) – thử 150 frame đầu

Mục đích: có một kết quả **scan matching thuần** (đúng yêu cầu đề) để so với baseline TA trong báo cáo.
Script `run_image_only.sh`: như baseline (bắt đầu từ `init_guess`, mỗi frame bắt đầu từ pose frame trước) nhưng `ply_scale = 9`,
NDT 4 m, voxel đầu vào 1 m, bỏ điểm xa hơn 40 m, tối đa 30 vòng lặp. Tốc độ: ~1.3 s/frame (Track01), ~0.8 s/frame (Track02).
So với quỹ đạo GNSS tốt nhất (`tools/track_error.py`, `data/image_only_test.txt`):

| | Lỗi vị trí trung bình theo từng 25 frame | Lỗi yaw |
|---|---|---|
| Track01 | 1.5 → 2.8 → 5.1 → 7.2 → 8.2 → **9.1 m** (tăng đều) | ±1–5° |
| Track02 | 3.6 → 6.0 → 8.4 → 9.6 → 9.3 → 8.9 m | **+29…+40°** |

Chẩn đoán (chưa sửa):
1. **Không có mô hình chuyển động** – mỗi frame bắt đầu từ vị trí cũ trong khi xe đã đi tiếp ~0.36 m; NDT chỉ kéo về một phần → kết quả trễ dần.
   Cách sửa: dự đoán bằng vận tốc frame trước (constant velocity).
2. **Hướng ban đầu sai**: `init_guess` Track02 lệch yaw ~15°, NDT không tự sửa được. Cách sửa: thử nhiều góc ở frame đầu, chọn góc khớp nhất.

## 7. NDT với `3cameras_ply` (3 camera, MapAnything) – Track01

Mục đích: tìm nguồn thông tin vị trí mới cho Track01 (lỗi vị trí GNSS ~0.9 m mà NDT trên `raw_ply` không sửa được).
Prior = file tốt nhất Track01 (`yawproj_v1_1.csv`), NDT 4 m, voxel đầu vào 0.5 m, bỏ điểm xa hơn 40 m, tối đa 50 vòng lặp, vùng bản đồ ±60 m.
~7–9 nghìn điểm/frame sau lọc, ~14 s/frame NDT.

Thử nhanh tỉ lệ (cứ 100 frame một lần, dừng sớm; `data/ndt_correction_stats_3cameras_test.txt`):

| Tỉ lệ | Số frame | Hiệu chỉnh vị trí (trung vị) | ≤ 0.5 m | Along (trung vị) | Yaw: trung vị / độ lệch chuẩn |
|---|---|---|---|---|---|
| 0.8 | 15 | 0.58 m | 47 % | +0.04 m | +0.15° / 1.25° |
| **1.0** | 14 | **0.18 m** | **71 %** | 0.00 m | −0.02° / 1.64° |

Chạy đầy đủ qua đêm 17→18/10: tỉ lệ 1.0 cứ 2 frame (`c3s10`, 1506 frame), tỉ lệ 0.8 cứ 4 frame (`c3s08`, 753 frame).
Ban đầu mỗi lượt 1 lõi (~12–25 s/frame); từ 00:07 chia phần còn lại thành **10 đoạn chạy song song** (`run_chunk.sh`, tham số mới
`start_frame`, ghép bằng `tools/merge_debug.py`) → ~20 frame/phút, xong lúc 01:26.

## 8. Kết quả NDT `3cameras_ply` và đánh giá trên Kaggle

| Lượt chạy | Hiệu chỉnh (trung vị) | ≤ 0.5 m | ≤ 1 m | Yaw (trung vị / độ lệch chuẩn) |
|---|---|---|---|---|
| Track01 tỉ lệ 1.0 (`c3s10`) | 0.43 m | 52 % | 67 % | +0.12° / 1.82° |
| Track01 tỉ lệ 0.8 (`c3s08`) | 0.47 m | 52 % | 71 % | +0.66° / 1.89° |
| Track02 tỉ lệ 1.0 (`c3s10T2`, 10 lõi, xong 02:26) | 0.40 m | 56 % | 67 % | −0.28° / 2.85° |

Đánh giá Track01 bằng lượt nộp **chỉ đổi vị trí** (hiệu chỉnh lọc ≤ 2 m / 3°, làm mượt 2 s, cộng vào vị trí của `yawproj_v1_1`):

| File | Dịch vị trí | Điểm | Lỗi vị trí (từ điểm) |
|---|---|---|---|
| (gốc) `yawproj_v1_1.csv` | – | 1.21861 | 0.905 m |
| `ndt3c_s10_pos_1.csv` (tỉ lệ 1.0) | 0.333 m RMS | 1.24807 | 0.934 m ❌ |
| `ndt3c_s08_pos_1.csv` (tỉ lệ 0.8) | 0.384 m RMS | **1.15042** | **0.836 m** ✅ |

→ **Tỉ lệ 0.8 là lần đầu scan matching sửa được lỗi vị trí GNSS** (0.905 → 0.836 m). Tỉ lệ 0.8 ứng với camera cao ~1.65 m,
khớp với tỉ lệ ×9 của `raw_ply` (camera ~1.62 m) – hai nguồn point cloud cho cùng một độ cao camera.
Tỉ lệ 1.0 (tin MapAnything) lại làm xấu đi. Tổ hợp 3 trường hiệu chỉnh (×1.0, ×0.8, raw ×9) theo điểm Kaggle: xem 04 #34, 05 mục 6.
