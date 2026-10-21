# Hướng dẫn chạy: từ code tới file kết quả (Track01, Track02)

Pipeline sạch (không có phần chọn theo leaderboard): **GNSS → Kalman/RTS → GICP (Track01) → ghép độ sửa → yaw từ gyro**.
Có 2 môi trường Docker:

| Image | Dùng cho | Mở bằng |
|---|---|---|
| `sdc_ros2_dev` (ROS 2 Humble, code mẫu TA) | build node C++, NDT, RViz, bộ lọc Kalman | `docker compose` (bước 1) |
| `sdc-reg` (Python + small_gicp) | GICP, ghép, yaw gyro | `docker run` (bước 3–6, script có sẵn) |

Thư mục: `~/SDC-midterm01/` chứa `data/` (dữ liệu), `midterm01/` (repo này), `docker-compose.yml`.
Trong container ROS: repo ở `/root/midterm`, dữ liệu ở `/root/data`.

---

## Bước 0 – Chuẩn bị một lần

```bash
cd ~/SDC-midterm01
docker compose build                                   # image sdc_ros2_dev (~1 phút)
docker build -t sdc-reg midterm01/docker/reg           # image Python + small_gicp
```

## Bước 1 – Mở container ROS (có hiện cửa sổ RViz)

```bash
xhost +local:                                          # cho Docker mở cửa sổ trên màn hình
cd ~/SDC-midterm01
docker compose up -d                                   # chạy container ở nền
docker compose exec sdc_ros2_dev bash                  # vào trong container
```

Trong container, build code C++ (lần đầu hoặc sau khi sửa `localization.cpp`):

```bash
cd /root/midterm
source /opt/ros/humble/setup.bash
colcon build --build-base build_dev --install-base install_dev
source install_dev/setup.bash
```

## Bước 2 (tuỳ chọn) – Xem bằng RViz

Chạy node NDT của TA cùng RViz, 100 frame đầu Track01, tỉ lệ point cloud đã sửa (9 thay cho 3):

```bash
ros2 launch localization localization.launch.py data_path:=/root/data/Track1 \
  ply_scale:=9.0 ndt_resolution:=4.0 max_frames:=100 save_file:=rviz_test_Track1_result.txt
```

RViz hiện bản đồ LiDAR, point cloud của frame hiện tại và quỹ đạo. Dùng để **nhìn** và **chụp ảnh cho báo cáo**;
không cần cho kết quả. Thử `ply_scale:=3.0` (giá trị gốc của TA) để thấy point cloud bé hơn bản đồ và NDT trôi.

## Bước 3 – GNSS + bộ lọc Kalman (trong container ROS)

```bash
O=/root/midterm/src/localization/result
cd /root/midterm/src/localization/processing_codes
# GNSS làm mượt (lấy yaw GNSS cho Track01)
python3 gnss_smooth_to_csv.py /root/data/Track1 Track1 $O/gnss_smooth_1.csv 1.5 gnss
cd /root/midterm/tools
# Kalman CTRV + RTS smoother
python3 rts_smoother.py /root/data/Track1 Track1 $O/rts_phys_qa1.0_1.csv --yaw gnss --qa 1.0 --qw 0.1
python3 csv_ops.py merge $O/rts_pos_gnssyaw_1.csv --pos $O/rts_phys_qa1.0_1.csv --yaw $O/gnss_smooth_1.csv
python3 csv_ops.py offset $O/rts_pos_gnssyaw_1.csv $O/phys_yawb_1.csv --yaw-deg 0.42   # bỏ lệch yaw GNSS
python3 rts_smoother.py /root/data/Track2 Track2 $O/rts_heading_2.csv --yaw heading       # Track02
```

Kết quả: `src/localization/result/phys_yawb_1.csv` (Track01, điểm Kaggle 1.25338) và `rts_heading_2.csv` (Track02, 0.40778).

## Bước 4 – Chuẩn bị cho GICP (đã có sẵn, chỉ làm lại khi cần)

- **Bản đồ 0.3 m** (trên máy, không cần container):
  ```bash
  cd ~/SDC-midterm01
  docker run --rm -u $(id -u):$(id -g) -v $PWD:/w -w /w/midterm01 sdc-reg \
    python3 tools/map_voxel.py /w/data/Track1/map.pcd /w/data/Track1/map_voxel_0.3m.pcd 0.3
  ```
  (tương tự Track2)
- **Độ cao z, góc lăn / chúi mỗi frame** lấy từ một lượt NDT C++ trên `3cameras_ply` (`c3s08` cho Track01,
  `c3s10T2` cho Track02 – file `*_result.txt` trong `src/localization/result/` và `result/chunks/`). Lượt này rất chậm
  (~14 s/frame, chạy chia khúc bằng `run_chunk.sh`), nên giữ file có sẵn, không cần chạy lại.

## Bước 5 – Chạy pipeline sạch: một lệnh (trên máy, ngoài container)

```bash
cd ~/SDC-midterm01
bash midterm01/tools/run_clean_pipeline.sh
```

Script làm lần lượt (~10 phút):

| # | Track | Việc | Công cụ |
|---|---|---|---|
| 1 | 01 | yaw tạm từ gyro (τ 7 s) cho vị trí Kalman | `tools/yaw_fusion.py` |
| 2 | 01 | GICP lượt 1: khớp point cloud 3 camera vào bản đồ, tỉ lệ = 1.646 m / độ cao mặt đường | `tools/gicp_refine.py` |
| 3 | 01 | ghép độ sửa: lọc ≤ 2 m / 3°, trừ độ lệch trung bình, làm mượt 2 s | `fuse_to_csv.py --demean` |
| 4 | 01 | GICP lượt 2 + ghép lần 2 | như 2–3 |
| 5 | 01 | yaw cuối: gyro (nhanh) + hướng chạy của quỹ đạo Kalman (chậm) | `tools/yaw_fusion.py` |
| 6 | 02 | vị trí Kalman + yaw gyro (τ 15 s); không dùng scan matching | `tools/yaw_fusion.py` |

Kết quả: `midterm01/src/localization/result/reg/rerun/result_1.csv` và `result_2.csv`
(dạng `idx,x,y,yaw`, đúng định dạng Kaggle).

## Bước 6 – Kiểm tra và nộp

```bash
cd ~/kaggle-sdc-bot
python3 -I -c "import sys; sys.path.insert(0,'.'); import bot; \
print(bot.validate('1','$HOME/SDC-midterm01/midterm01/src/localization/result/reg/rerun/result_1.csv'))"
```

- Kiểm tra offline (không tốn lượt nộp, chỉ để loại cấu hình hỏng):
  `docker run --rm -v ~/SDC-midterm01:/w -w /w/midterm01 sdc-reg python3 tools/map_fit.py 1 --data /w/data <file.csv>`
- Nộp: chép file vào `~/kaggle-sdc-bot/queue/track1/` (bot tự nộp lúc 8:00) hoặc nộp tay trên trang Kaggle.
- Cuối cùng: trên Kaggle, tab Submissions, chọn file pipeline làm **Use for Final Score**.
- Nộp E3: đổi tên thành `result_1.csv`, `result_2.csv`, kèm code (không kèm `data/`), báo cáo PDF, README.

## Sơ đồ

```
data/TrackN ──► (3) GNSS + Kalman/RTS ──► phys_yawb_1 / rts_heading_2
                                               │
         Track01 ──► (5.1) yaw gyro ──► (5.2–5.4) GICP ×2 + ghép ──► (5.5) yaw gyro ──► result_1.csv
         Track02 ─────────────────────────────────────────────────► (5.6) yaw gyro ──► result_2.csv
```
