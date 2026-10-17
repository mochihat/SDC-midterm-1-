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
