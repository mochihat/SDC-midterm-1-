# 01 – Chuẩn bị: cuộc thi, dữ liệu, môi trường

## 1. Thông tin cuộc thi

| | Track01 | Track02 |
|---|---|---|
| Kaggle | `sdc-2026-midterm-01-track-01` | `sdc-2026-localization-track-02` |
| Số frame cần nộp | 3011 | 3299 |
| Baseline TA trên leaderboard | 1.79075 | 1.92587 |

- Đề: định vị xe (localization) bằng cách khớp point cloud dựng từ ảnh camera với bản đồ LiDAR dựng sẵn.
- Hạn Kaggle: **29/10/2026 09:00** (01:00 UTC). Nộp muộn đến 05/11 23:59 (được 11 điểm/track).
- Tối đa **15 lần nộp/ngày** mỗi track (ngày tính theo UTC, tức đổi ngày lúc 08:00 giờ địa phương), đội tối đa 2 người. Tên đội trên Kaggle: **11**.
- Nộp file CSV `idx,x,y,yaw`, mỗi frame một dòng, `yaw` tính bằng **radian**
  (script của TA `processing_codes/txt_to_idx_x_y_yaw.py`: `yaw = atan2(r21, r11)` từ ma trận pose).

### Cách chấm điểm (theo slide)

$$E = \sqrt{\frac{1}{n}\sum_i \lVert\Delta \mathbf p_i\rVert^2} \;+\; k\cdot\sqrt{\frac{1}{n}\sum_i \lVert\Delta\theta_i\rVert^2},\qquad k = 0.2$$

`Δp` = sai số vị trí (mét), `Δθ` = sai số góc (**độ**). Nghĩa là **1° sai yaw = 0.2 điểm**, tương đương 0.2 m sai vị trí.

### Thang điểm môn học (theo slide)
- Xếp hạng Kaggle tối đa 56 điểm = tổng 2 track; mỗi track: hạng 1: 28, hạng 2: 26, hạng 3: 24, top 50%: 21, top 75%: 18,
  vượt baseline: 15, nộp muộn: 11, dưới baseline: 0.
- Báo cáo 30 điểm (Pipeline, Contributions, Problems and Solutions, Workload Distribution), thuyết trình 20 điểm (4–6 phút, ngày 29/10).
- Nộp E3 trước 05/11 23:59: code (không kèm dữ liệu), `result_1.csv`, `result_2.csv` (bài nộp tốt nhất), báo cáo PDF, README.
- Slide ghi: baseline của TA chỉ dùng point cloud từ camera trước; sinh viên **được phép dùng thêm ảnh các camera khác, IMU và GNSS**.

## 2. Dữ liệu

Mỗi track gồm:

| Thành phần | Track01 | Track02 | Ghi chú |
|---|---|---|---|
| `map.pcd` | 2.70 GB | 1.22 GB | bản đồ LiDAR, PCD ASCII, trường `x y z intensity`; Track01 có 59 531 846 điểm |
| `TrackN.db3` + `metadata.yaml` | 250 MB | 270 MB | rosbag2: `/imu/data`, 3 topic ảnh h265, `/localizer_node/gnss_pose` |
| `raw_ply/` | 3011 file, 5.09 GB | 3299 file, 3.12 GB | point cloud dựng từ **ảnh camera trước** bằng LoGeR, tên file chứa timestamp |
| `3cameras_ply/` | 3011 file, 14.75 GB | 3299 file, 12.21 GB | point cloud dựng từ **3 camera** bằng MapAnything |
| `TrackN_images/` | 3 × 3011 ảnh | 3 × 3299 ảnh | front / front-left / front-right, fisheye 1440×928 |
| `camera_info/` | | | intrinsic (mô hình fisheye), extrinsic giữa 3 camera, mặt nạ nắp capo |
| `init_guess.txt` | | | ma trận 4×4 pose ban đầu **có cộng nhiễu** |

Rosbag Track01 (`metadata.yaml`): dài 110.0 s, 20 608 message: `/imu/data` 10 999, mỗi camera ~3 056, `/localizer_node/gnss_pose` 440.

## 3. Tải dữ liệu – những gì đã xảy ra

1. Trang Kaggle render bằng JavaScript nên không đọc trực tiếp được; dùng **Kaggle API** (token của tài khoản) để đọc thông tin cuộc thi và danh sách file (15 066 file, 25.4 GB cho Track01).
2. Endpoint tải trọn gói `download-all` trả về `404 "no gcs url"` → Kaggle **không có file zip gộp** cho cuộc thi này (có lẽ do dữ liệu quá lớn).
3. Tải từng file qua API: được ~3 GB (gồm `map.pcd`, `Track1.db3`) thì bị Kaggle trả `429 Too Many Requests` liên tục → dừng.
4. Bạn tải các file zip trực tiếp trên trình duyệt (`Track1.zip`, `3cameras_ply.zip`, `Track2.zip`, `sdc-2026-localization-track-02.zip`).
   Kiểm tra: số file và dung lượng khớp danh sách Kaggle; `Track2.zip` giống hệt phần Track2 trong zip của Kaggle (so CRC 13 205 file).
5. Giải nén thành:

```
~/SDC-midterm01/data/            (trong Docker: /root/data/)
├── Track1/  map.pcd  Track1.db3  metadata.yaml  init_guess.txt  raw_ply/  3cameras_ply/  Track1_images/
└── Track2/  map.pcd  Track2.db3  metadata.yaml  init_guess.txt  raw_ply/  3cameras_ply/  Track2_images/
```

Code mẫu của TA (`SDC-midterm01.zip`) giải nén ra `~/SDC-midterm01/` (thư mục `midterm01/` = repo này).

## 4. Môi trường Docker

Ba chỗ phải sửa trong cấu hình của TA:

| File | Sửa | Lý do |
|---|---|---|
| `docker-compose.yml` | `/{USER-PATH}/…` → `/home/thuhang/…` | đường dẫn mẫu chưa điền |
| `Dockerfile` | `pandas<2.1` → `"pandas<2.1"` | không có nháy, shell hiểu `<` là chuyển hướng đọc file `2.1` → build lỗi |
| `docker-compose.yml` | comment khối `deploy:` (GPU) | máy chưa cài `nvidia-container-toolkit`; NDT của PCL chạy CPU nên không cần GPU |

Bạn tự làm: thêm tài khoản vào nhóm `docker` (`sudo usermod -aG docker $USER`, rồi đăng nhập lại), `xhost +local:` cho RViz.
Image `sdc_ros2_dev` (ROS 2 Humble) build ~66 s; `colcon build` thành công (chỉ có cảnh báo).
Bản sao cấu hình đã sửa nằm ở `docker/` trong repo.

**Chạy thử 5 frame Track01 (không RViz):** đọc `map.pcd` mất ~58 s, giảm mẫu voxel 1 m còn 496 909 điểm
(Track02: 50 881 350 → 297 890 điểm) và lưu cache `map_downsampled_1m.pcd`; NDT hội tụ cả 5 frame,
frame 1 ở (−4796.851, 2277.024, 111.162). Mỗi frame ~3 s.

## 5. Quản lý code

Repo git ở `~/SDC-midterm01/midterm01` (GitHub: `mochihat/SDC-midterm-1-`, private). Commit đầu tiên là **bản gốc của TA**
để luôn so được phần đã sửa. Thư mục `build/`, `install/`, `log/`, `src/localization/result/` không đưa lên git.
