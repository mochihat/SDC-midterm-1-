# 02 – Phân tích dữ liệu

Số liệu gốc: `data/gnss_imu_analysis.txt`, `data/ground_scale.txt`, `data/frame_alignment_check.txt`.

## 1. GNSS – topic `/localizer_node/gnss_pose`

| | Track01 | Track02 |
|---|---|---|
| Số message, tần số | 440, 4 Hz (dt trung bình 0.250 s) | 475, 4 Hz |
| Thời lượng / quãng đường | 109.7 s / 1052.9 m | 118.5 s / 1247.4 m |
| Tốc độ trung bình | 9.60 m/s | 10.53 m/s |
| `z` | luôn = 110.132 | luôn = 17.344 |
| Lệch header stamp so với thời gian bag | −1.2 ms | −1.2 ms |
| Độ giật vị trí (RMS sai phân bậc 2, mỗi 0.25 s) | **0.142 m** | 0.052 m |
| Hướng chạy − yaw GNSS (lúc xe chạy) | +0.44° ± 3.91° | −0.66° ± 1.66° |

Nhận xét:
- `z` không đổi → đây là **pose phẳng (x, y, yaw)**, nhiều khả năng là đầu ra của một hệ định vị (tên topic là `localizer_node`), không phải GNSS thô.
- Cùng hệ toạ độ với bản đồ: `z` GNSS cao hơn mặt đường trên bản đồ phần lớn ~1.4–2.4 m (Track01: 110.13 so với 107.7–108.7; Track02: 17.34 so với 15.0–16.1, trừ đoạn đầu Track02 nơi mặt đất đo được 16.4–16.8; số liệu dưới vị trí GNSS trong `data/ground_scale.txt`), cỡ độ cao cảm biến trên nóc xe.
- **GNSS Track01 giật gấp ~3 lần Track02** (0.142 so với 0.052 m) → dự đoán Track01 khó hơn (đúng như điểm Kaggle sau này).
- Yaw GNSS lệch có hệ thống so với hướng chạy (khác dấu giữa 2 track) → gợi ý yaw GNSS có **độ lệch cố định** (sau này bộ lọc Kalman ước lượng được: −0.42° ở Track01, +0.65° ở Track02).

## 2. `init_guess.txt` (pose ban đầu có nhiễu)

| | lệch vị trí so với GNSS đầu tiên | lệch yaw | lệch z |
|---|---|---|---|
| Track01 | 0.55 m | +2.00° | −0.20 m |
| Track02 | 0.65 m | **+14.85°** | −0.18 m |

Track02 lệch yaw gần 15° → nếu chỉ dựa vào `init_guess` (như baseline) thì NDT dễ khớp sai ngay từ đầu.

## 3. Point cloud từ ảnh – hệ trục và tỉ lệ

### Định dạng
- `raw_ply/` (LoGeR, camera trước): PLY **ASCII**, ~20–41 nghìn điểm/frame, có màu RGB.
- `3cameras_ply/` (MapAnything): PLY nhị phân, ~330 nghìn điểm/frame, header ghi rõ `coordinate_frame=front_camera_FLU_x_front_y_left_z_up`.

### Point cloud rất "nhỏ"
Frame 0 Track01 (phân vị 1 %–99 %): x từ 0.37 đến 3.26, y từ −1.36 đến 2.97, z từ −0.21 đến 0.96; khoảng cách tới camera tối đa ~4.3 đơn vị.
Một camera thật trên xe phải nhìn xa hàng chục mét → point cloud đang ở **đơn vị tuỳ ý (không phải mét)**.

### Đo tỉ lệ bằng mặt đường (`tools/ground_scale.py`)
Mặt đường là mặt phẳng z = −h trong point cloud (h = độ cao camera tính bằng đơn vị của point cloud).
Đo h trên 21 (Track01) và 22 (Track02) frame, cứ 150 frame một lần, trải đều cả quãng đường:

| | h trung vị | min – max | độ dao động |
|---|---|---|---|
| Track01 | 0.1795 | 0.1656 – 0.1982 | 5.0 % |
| Track02 | 0.1798 | 0.1602 – 0.1996 | 6.9 % |

→ h gần như **không đổi** giữa các frame và giữa 2 track ⇒ một tỉ lệ cố định là dùng được.
Camera cao ~1.5–1.8 m ⇒ **tỉ lệ = 1.5…1.8 / 0.18 ≈ 8.4…10**. Baseline dùng **3** → cảnh bị thu nhỏ 3 lần
(camera như chỉ cao 0.54 m, tầm nhìn ~9 m thay vì ~27 m).

### Kiểm tra hệ trục bằng cách đặt point cloud vào bản đồ (`tools/check_frame_alignment.py`)
Đặt point cloud tại pose GNSS (x, y, yaw), mặt đường point cloud trùng mặt đường bản đồ, rồi dò lưới
tỉ lệ × độ lệch yaw (−30…+30°) × dịch chuyển (±4 m), tính khoảng cách trung bình tới bản đồ (chỉ dùng điểm phía trên mặt đường).

Độ lệch yaw tốt nhất tìm được tại mỗi frame (lưới 3°, dịch ±4 m bước 1 m):

| Frame | tỉ lệ 3 | tỉ lệ 9 |
|---|---|---|
| Track01 #0 / #752 / #1505 / #2258 | −30° / −3° / −9° / −24° | −3° / +6° / +3° / 0° |
| Track02 #0 / #824 / #1649 / #2474 | +27° / 0° / 0° / −24° | +24° / 0° / 0° / −3° |

- Ở tỉ lệ **3**: 4/8 frame cần quay 24–30° mới "khớp" → không có cách khớp thật, chỉ là cực tiểu ngẫu nhiên.
- Ở tỉ lệ **9**: 7/8 frame khớp tốt nhất khi quay ≤ 6° (ngoại lệ: frame đầu Track02, +24°). Ở Track02 frame #824 và #2474,
  tỉ lệ 9 còn cho khoảng cách nhỏ nhất trong mọi tỉ lệ.
- ⇒ **Hệ trục FLU đúng** (trục x của point cloud trùng hướng mũi xe) và tỉ lệ ≈ 9 khớp nhất quán. Bằng chứng mạnh hơn đến từ
  thí nghiệm NDT (mục 03): ở ×9 hiệu chỉnh yaw của NDT có trung vị ~0° và độ lệch chuẩn ~2°, so với ±24–47° ở ×2…×4.
- Lưu ý: chính thước đo "khoảng cách trung bình" lại **thiên vị tỉ lệ nhỏ** (point cloud nhỏ dồn sát mặt đường nên luôn gần bản đồ),
  vì vậy giá trị nhỏ nhất của nó rơi vào tỉ lệ 3 – không được đọc kết quả theo giá trị nhỏ nhất mà phải xem **tính nhất quán của độ lệch yaw**.
  Lần chạy đầu tiên (chỉ thử tỉ lệ 1–6, dùng cả điểm mặt đường) bị đúng lỗi này và chỉ ra tỉ lệ 1 – đã được sửa.

## 4. Bản đồ

- Track01: 59 531 846 điểm → voxel 1 m còn 496 909 điểm. Track02: 50 881 350 → 297 890 điểm.
- Đọc bản đồ ASCII 2.7 GB mất ~1 phút → code lưu bản đã giảm mẫu thành `map_downsampled_1m.pcd` để các lần sau đọc trong vài giây.

## 5. IMU – topic `/imu/data`

| | Track01 | Track02 |
|---|---|---|
| Tần số | 100 Hz (frame `imu_link`, covariance = 0) | 100 Hz |
| Gia tốc trung bình | [−0.91, 0.40, 9.74] m/s² | [−0.78, 0.02, 9.76] m/s² |
| Yaw (orientation IMU) − yaw GNSS | −2.95° ± 2.15° | −2.83° ± 2.14° |
| Tổng góc quay: GNSS / orientation IMU / tích phân gyro z | +28.0° / +24.3° / −4.1° | −40.1° / −33.3° / −71.2° |
| Tương quan tốc độ quay GNSS – gyro z | 0.19 (trễ 0) → 0.37 (trễ −1.70 s) | 0.69 (trễ 0) → **0.91 (trễ −1.45 s)** |
| Bias gyro z (khớp thay đổi yaw trong 2 s) | −0.296 °/s | −0.25 °/s |

Nhận xét:
- Gyro z có **bias ≈ −0.25…−0.30 °/s**, giống nhau ở 2 track → tích phân trực tiếp sẽ sai nhiều.
- Gyro khớp với GNSS nhất khi **lệch ~1.5 s** ở cả 2 track. Nếu GNSS trễ 1.5 s thì vị trí sai ~15 m – trái với điểm Kaggle (~0.4–1.3) –
  nên nhiều khả năng là **đồng hồ của IMU lệch**. Chưa kiểm chứng thêm; IMU **chưa được dùng** trong bất kỳ file nộp nào.
- Orientation của IMU lệch ~−2.9° so với GNSS và bị trôi (tổng góc quay thiếu 4–7°).

## 6. Kết luận phần phân tích

1. GNSS là nguồn thông tin mạnh nhất: cùng hệ toạ độ bản đồ, mượt, 4 Hz.
2. Point cloud từ ảnh cần **tỉ lệ ≈ 9** (không phải 3) và hệ trục FLU là đúng.
3. `init_guess` có nhiễu lớn (Track02 lệch 15° yaw).
4. IMU cần hiệu chỉnh bias và thời gian trước khi dùng được.
