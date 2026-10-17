# 07 – Tạo lại từng file đã nộp

Mọi lệnh chạy **trong container** (`docker compose exec sdc_ros2_dev bash`), dữ liệu ở `/root/data/Track1`, `/root/data/Track2`,
repo ở `/root/midterm`.

## 1. Tạo lại tất cả và so khớp

```bash
bash /root/midterm/tools/reproduce_submissions.sh /tmp/reproduce
```

Script chạy lại mọi bước theo đúng thứ tự đã làm, rồi so từng file với bản trong `docs/nhat-ky/submissions/`.
Đã kiểm tra ngày 17/10/2026: **19/19 file `identical`** (trùng khớp từng byte), mất ~35 s.
Hai file dùng NDT lấy dữ liệu NDT đã lưu trong `docs/nhat-ky/data/ndt_debug/` (chạy lại NDT mất hàng giờ – xem mục 3).

## 2. Lệnh tạo từng file

Viết tắt: `P=/root/midterm/src/localization/processing_codes`, `T=/root/midterm/tools`, `D=/root/midterm/docs/nhat-ky/data/ndt_debug`.

| File | Lệnh |
|---|---|
| `gnss_N.csv` | `python3 $P/gnss_to_csv.py /root/data/TrackN TrackN gnss_N.csv` |
| `gnss_smooth_N.csv` | `python3 $P/gnss_smooth_to_csv.py /root/data/TrackN TrackN gnss_smooth_N.csv 1.5 gnss` |
| `gnss_heading_N.csv` | `python3 $P/gnss_smooth_to_csv.py /root/data/TrackN TrackN gnss_heading_N.csv 1.5 heading` |
| `fusion_s9r4_headingyaw_2.csv` | `python3 $P/fuse_to_csv.py gnss_heading_2.csv $D/e2s9r4_Track2_debug.csv fusion_s9r4_headingyaw_2.csv --yaw-weight 0 --sigma-s 2 --max-xy 2 --max-yaw-deg 3` |
| `rts_heading_2.csv` | `python3 $T/rts_smoother.py /root/data/Track2 Track2 rts_heading_2.csv --yaw heading` |
| `rts_pos_gnssyaw_1.csv` | `python3 $T/rts_smoother.py /root/data/Track1 Track1 rts_phys_qa1.0_1.csv --yaw gnss --qa 1.0 --qw 0.1` rồi `python3 $T/csv_ops.py merge rts_pos_gnssyaw_1.csv --pos rts_phys_qa1.0_1.csv --yaw gnss_smooth_1.csv` |
| `rts_heading_dt±0.1_2.csv` | như `rts_heading_2` thêm `--time-offset ±0.1` |
| `rts_pos_gnssyaw_dt±0.1_1.csv` | như `rts_pos_gnssyaw_1` nhưng bước smoother thêm `--time-offset ±0.1` (yaw vẫn từ `gnss_smooth_1.csv`) |
| `probe_lat±0.5_1.csv` | `python3 $T/csv_ops.py offset rts_pos_gnssyaw_1.csv probe_lat+0.5_1.csv --lateral 0.5` (hoặc `-0.5`) |
| `probe_yaw±1_1.csv` | `python3 $T/csv_ops.py offset rts_pos_gnssyaw_1.csv probe_yaw+1_1.csv --yaw-deg 1` (hoặc `-1`) |
| `phys_yawb_1.csv` | `python3 $T/csv_ops.py offset rts_pos_gnssyaw_1.csv phys_yawb_1.csv --yaw-deg 0.42` |
| `phys_yawb_ndt_1.csv` | `python3 $P/fuse_to_csv.py phys_yawb_1.csv $D/e2s9r4_Track1_debug.csv phys_yawb_ndt_1.csv --yaw-weight 0 --sigma-s 2 --max-xy 2 --max-yaw-deg 3` |

## 3. Chạy lại các thí nghiệm NDT

Build bản đã sửa (tách riêng khỏi bản gốc):
```bash
cd /root/midterm && colcon build --build-base build_dev --install-base install_dev
```
`run_fusion.sh N TAG [tham số ROS]` – prior mặc định `src/localization/result/gnss_smooth_N.csv` (đổi bằng biến môi trường `PRIOR=...`),
ghi `TAG_TrackN_result.txt` và `TAG_TrackN_debug.csv` vào `src/localization/result/`.

| Thí nghiệm | Lệnh |
|---|---|
| Đợt 1 (×2/×3/×4) | `bash /root/midterm/run_fusion.sh 2 e1s3 -p frame_stride:=10 -p ply_scale:=3.0 -p max_correction_xy:=10.0 -p max_correction_yaw_deg:=30.0` |
| Đợt 2 (×9, 4 m) | `bash /root/midterm/run_fusion.sh 2 e2s9r4 -p frame_stride:=20 -p ply_scale:=9.0 -p ndt_resolution:=4.0 -p ndt_max_iterations:=50 -p max_correction_xy:=10.0 -p max_correction_yaw_deg:=30.0 -p submap_half_size:=60.0` |
| Thống kê hiệu chỉnh | `python3 $P/fuse_to_csv.py gnss_smooth_2.csv e2s9r4_Track2_debug.csv --stats` |
| Baseline TA | `bash /root/midterm/run_baseline.sh 1` (hoặc `2`) |

## 4. Chạy lại các phân tích

| Kết quả | Lệnh |
|---|---|
| `data/gnss_imu_analysis.txt` | `python3 $T/analyze_gnss_imu.py /root/data/Track1 Track1` |
| `data/ground_scale.txt` | `python3 $T/ground_scale.py /root/data/Track1 <prior.csv> raw_ply 150` |
| `data/frame_alignment_check.txt` | `python3 $T/check_frame_alignment.py /root/data/Track1 Track1 <prior.csv> raw_ply` (biến `SCALES` để đổi danh sách tỉ lệ) |
| `data/rts_smoother_output.txt` | các lệnh `rts_smoother.py` ở mục 2 (in ra tham số nhiễu ML và độ lệch b) |
| `data/probe_analysis.txt` | `python3 $T/analyze_probes.py docs/nhat-ky/data/kaggle_submissions.csv docs/nhat-ky/submissions /root/data` |
| `data/file_differences.txt` | `python3 $T/compare_csv.py docs/nhat-ky/submissions track1:gnss_1.csv:gnss_smooth_1.csv …` (17 cặp như trong file; đã kiểm tra ra đúng bảng đã lưu) |

## 5. Code đã sửa / thêm

| File | Nội dung |
|---|---|
| `src/localization/src/localization.cpp`, `include/localization/localization.h` | prior GNSS, loại kết quả NDT xa prior, `frame_stride`, `max_input_range`, file debug |
| `src/localization/processing_codes/gnss_to_csv.py` | GNSS nội suy tuyến tính |
| `src/localization/processing_codes/gnss_smooth_to_csv.py` | GNSS làm mượt Gauss + spline, yaw GNSS hoặc hướng chạy |
| `src/localization/processing_codes/fuse_to_csv.py` | ghép hiệu chỉnh NDT vào prior; `--stats` in thống kê |
| `tools/rts_smoother.py` | bộ lọc Kalman CTRV + RTS, nhiễu chọn bằng maximum likelihood, độ lệch yaw b, `--time-offset`, `--qa/--qw` |
| `tools/csv_ops.py` | ghép vị trí/yaw từ 2 file; dời ngang, cộng yaw |
| `tools/compare_csv.py` | chênh lệch vị trí / yaw giữa các file nộp |
| `tools/analyze_probes.py`, `tools/analyze_gnss_imu.py`, `tools/ground_scale.py`, `tools/check_frame_alignment.py`, `tools/pc_io.py` | phân tích |
| `tools/reproduce_submissions.sh` | tạo lại toàn bộ file đã nộp và so khớp |
| `run_baseline.sh`, `run_fusion.sh` | chạy NDT không cần RViz |
| `docker/` | Dockerfile / docker-compose đã sửa |
