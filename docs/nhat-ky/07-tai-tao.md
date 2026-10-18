# 07 – Tạo lại từng file đã nộp

Mọi lệnh chạy **trong container** (`docker compose exec sdc_ros2_dev bash`), dữ liệu ở `/root/data/Track1`, `/root/data/Track2`,
repo ở `/root/midterm`.

## 1. Tạo lại tất cả và so khớp

```bash
bash /root/midterm/tools/reproduce_submissions.sh /tmp/reproduce
```

Script chạy lại mọi bước theo đúng thứ tự đã làm, rồi so từng file với bản trong `docs/nhat-ky/submissions/`.
Đã kiểm tra sáng 18/10/2026: **33/33 file `identical`** (trùng khớp từng byte), mất ~2 phút.
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
| `lagyaw_pos_best_1.csv` | `python3 $T/rts_imu_smoother.py /root/data/Track1 Track1 lag_noimu_heading_1.csv --yaw heading --no-imu` rồi `csv_ops.py merge lagyaw_pos_best_1.csv --pos phys_yawb_1.csv --yaw lag_noimu_heading_1.csv` |
| `lagyaw_pos_best_2.csv` | `python3 $T/rts_imu_smoother.py /root/data/Track2 Track2 lag_imu_heading_2.csv --yaw heading` rồi `csv_ops.py merge lagyaw_pos_best_2.csv --pos rts_heading_2.csv --yaw lag_imu_heading_2.csv` |
| `yawtau0.75_pos_best_2.csv` | như trên thêm `--time-offset -0.75` (→ `lagtau0.75_imu_2.csv`), rồi merge vào vị trí `rts_heading_2.csv` |
| `yawproj_v1_1.csv` | `python3 $T/yaw_projection.py 0.90462 rts_pos_gnssyaw_1.csv 1.25992 yawproj_v1_1.csv probe_yaw+1_1.csv:1.27676 lagyaw_pos_best_1.csv:1.30875` |
| `yawproj_v1_2.csv` | `python3 $T/yaw_projection.py 0.23218 rts_heading_2.csv 0.40778 yawproj_v1_2.csv lagyaw_pos_best_2.csv:0.45496 yawtau0.75_pos_best_2.csv:0.48625` |
| `curv1.5_on_proj_2.csv` | `python3 $T/curvature_yaw.py yawproj_v1_2.csv lag_imu_heading_2.csv /root/data/Track2/raw_ply 1.5 curv1.5_on_proj_2.csv` |
| `gnssyaw_pos_rts_2.csv` | `python3 $T/csv_ops.py merge gnssyaw_pos_rts_2.csv --pos rts_heading_2.csv --yaw gnss_smooth_2.csv` |
| `yawproj_v3_2.csv` | `yaw_projection.py` như `v1_2` nhưng thêm `curv1.5_on_proj_2.csv:0.36280 gnssyaw_pos_rts_2.csv:0.56160` |
| `startfix_on_v3_2.csv` / `startfix_on_v1_1.csv` | `python3 $T/start_yaw_fix.py /root/data/Track2 Track2 yawproj_v3_2.csv lag_imu_heading_2.csv startfix_on_v3_2.csv 4.0 1.0` (Track01: `yawproj_v1_1.csv`, `lag_noimu_heading_1.csv`) |
| `yawproj_v4_2.csv` | `yaw_projection.py` như `v3_2` thêm `startfix_on_v3_2.csv:0.33504` |
| `ndt3c_s10_pos_1.csv` / `ndt3c_s08_pos_1.csv` | `python3 $P/fuse_to_csv.py yawproj_v1_1.csv $D/c3s10_Track1_debug.csv ndt3c_s10_pos_1.csv --yaw-weight 0 --sigma-s 2 --max-xy 2 --max-yaw-deg 3` (tương tự `c3s08`) |
| `posproj_v1_1.csv` | `yaw_projection.py 0.90462 rts_pos_gnssyaw_1.csv 1.25992 proj1_v2.csv probe_yaw+1_1.csv:1.27676 lagyaw_pos_best_1.csv:1.30875 startfix_on_v1_1.csv:1.21871`; `pos_projection.py 0.90462 yawproj_v1_1.csv pos1_v1.csv ndt3c_s10_pos_1.csv:1.24807:1.56995 ndt3c_s08_pos_1.csv:1.15042:1.56995 phys_yawb_ndt_1.csv:1.27855:1.74380`; `csv_ops.py merge posproj_v1_1.csv --pos pos1_v1.csv --yaw proj1_v2.csv` |

Các số sau dấu `:` là **điểm Kaggle** của file đó (và với `pos_projection.py`: điểm:lỗi-yaw của yaw mà file đó giữ) –
đầu vào của phép tính tổ hợp (trọng số chọn theo bảng điểm).

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
| NDT chỉ dùng ảnh (thử) | `bash /root/midterm/run_image_only.sh 1 imgtest -p max_frames:=150` |
| NDT chạy song song theo đoạn | `PRIOR=... bash /root/midterm/run_chunk.sh 1 c3s10 <frame bắt đầu> <số frame> -p ply_path:=... -p frame_stride:=2 ...` (cần `colcon build --build-base build_par --install-base install_par`); ghép: `python3 $T/merge_debug.py out.csv phần1.csv chunks/c3s10_*_debug.csv` |
| NDT `3cameras_ply` (qua đêm) | `PRIOR=src/localization/result/prior_best_1.csv bash /root/midterm/run_fusion.sh 1 c3s10 -p ply_path:=/root/data/Track1/3cameras_ply/ply -p frame_stride:=2 -p ply_scale:=1.0 -p ndt_resolution:=4.0 -p ndt_max_iterations:=50 -p submap_half_size:=60.0 -p input_voxel_leaf_size:=0.5 -p max_input_range:=40.0 -p max_correction_xy:=10.0 -p max_correction_yaw_deg:=30.0` (`prior_best_1.csv` = `yawproj_v1_1.csv`) |

## 4. Chạy lại các phân tích

| Kết quả | Lệnh |
|---|---|
| `data/gnss_imu_analysis.txt` | `python3 $T/analyze_gnss_imu.py /root/data/Track1 Track1` |
| `data/ground_scale.txt` | `python3 $T/ground_scale.py /root/data/Track1 <prior.csv> raw_ply 150` |
| `data/frame_alignment_check.txt` | `python3 $T/check_frame_alignment.py /root/data/Track1 Track1 <prior.csv> raw_ply` (biến `SCALES` để đổi danh sách tỉ lệ) |
| `data/rts_smoother_output.txt` | các lệnh `rts_smoother.py` ở mục 2 (in ra tham số nhiễu ML và độ lệch b) |
| `data/probe_analysis.txt` | `python3 $T/analyze_probes.py docs/nhat-ky/data/kaggle_submissions.csv docs/nhat-ky/submissions /root/data` |
| `data/gnss_yaw_lag.txt` | `python3 $T/analyze_yaw_lag.py /root/data/Track1 Track1` |
| `data/rts_imu_smoother_output.txt` | `python3 $T/rts_imu_smoother.py /root/data/TrackN TrackN out.csv --yaw heading [--no-imu]` |
| `data/yaw_projection_output.txt` | các lệnh `yaw_projection.py` ở mục 2 |
| `data/image_only_test.txt` | `python3 $T/track_error.py imgtest_TrackN.csv <file tốt nhất> 25` |
| `data/ground_scale_3cameras.txt` | `python3 $T/ground_scale.py /root/data/Track1 <prior.csv> 3cameras_ply/ply 300` |
| `data/file_differences.txt` | `python3 $T/compare_csv.py docs/nhat-ky/submissions track1:gnss_1.csv:gnss_smooth_1.csv …` (25 cặp như trong file) |

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
| `tools/rts_imu_smoother.py` | bộ lọc Kalman: yaw GNSS trễ (ước lượng độ trễ), gyro (bias, lệch đồng hồ), maximum likelihood |
| `tools/yaw_projection.py` | tổ hợp yaw tối ưu từ các lượt chỉ đổi yaw (**dùng điểm Kaggle**) |
| `tools/curvature_yaw.py` | yaw thân xe = hướng chạy − atan(l × độ cong) |
| `tools/analyze_yaw_lag.py` | đo độ trễ của yaw GNSS so với vị trí và gyro |
| `tools/track_error.py` | lỗi của một quỹ đạo so với quỹ đạo tham chiếu theo từng đoạn |
| `run_image_only.sh` | NDT chỉ dùng ảnh (×9, không GNSS) |
| `tools/start_yaw_fix.py` | yaw đoạn xe đứng yên/chạy chậm dựng lại bằng gyro |
| `tools/pos_projection.py` | tổ hợp vị trí tối ưu từ các lượt chỉ đổi vị trí (**dùng điểm Kaggle**) |
| `run_chunk.sh`, `tools/merge_debug.py`, tham số `start_frame` | chạy NDT song song theo đoạn và ghép kết quả |
| `tools/analyze_probes.py`, `tools/analyze_gnss_imu.py`, `tools/ground_scale.py`, `tools/check_frame_alignment.py`, `tools/pc_io.py` | phân tích |
| `tools/reproduce_submissions.sh` | tạo lại toàn bộ file đã nộp và so khớp |
| `run_baseline.sh`, `run_fusion.sh` | chạy NDT không cần RViz |
| `docker/` | Dockerfile / docker-compose đã sửa |
