# Trạng thái dự án – đọc file này trước (cập nhật 23/10/2026 05:30)

File này dành cho bất kỳ phiên Claude nào (hoặc người) tiếp nhận dự án: đọc xong là biết đang ở đâu, luật là gì,
làm gì tiếp. Chi tiết từng thí nghiệm: `docs/nhat-ky/` (tiếng Việt). Cách chạy: `docs/HUONG-DAN-CHAY.md`.

## 1. Dự án

- Môn **Self-Driving Cars (SDC) 2026, NYCU – Midterm01: Localization**. Sinh viên làm **một mình**, đội Kaggle tên **"11"**.
- Bài toán: ước lượng x, y, yaw của xe cho từng frame camera bằng cách khớp point cloud (dựng từ ảnh camera) vào bản đồ
  LiDAR có sẵn. Được dùng thêm GNSS và IMU (Track01, Track02).
- Kaggle: Track01 `sdc-2026-midterm-01-track-01` (3011 frame), Track02 `sdc-2026-localization-track-02` (3299 frame).
- Điểm = RMSE vị trí (m) + 0.2 × RMSE yaw (độ). Thấp hơn = tốt hơn. Baseline TA: 1.79075 / 1.92587.
- Chấm môn: xếp hạng mỗi track (hạng 1/2/3 = 56/52/48 × r, top 50 % = 42r, top 75 % = 36r, trên baseline = 30r,
  r = 0.3 cho Track01/02), báo cáo 30 điểm (Pipeline, Contributions, Problems and Solutions, Workload Distribution),
  thuyết trình 20 điểm (4–6 phút, 29/10).
- **Hạn:** Kaggle đóng **29/10 09:00**; nộp E3 (code không kèm dữ liệu, `result_1.csv`, `result_2.csv`, báo cáo PDF,
  README) trước **05/11 23:59**.

## 2. Luật bắt buộc (đừng vi phạm)

**Cập nhật 23/10 (người dùng hỏi TA trực tiếp trên lớp):** Track01 và Track02 chấm theo điểm public toàn bộ → **dò bảng điểm được
phép** để lên hạng, và người dùng được trình bày chiến thuật dò trước lớp. **Track03 tuyệt đối tuân thủ luật 10/22** (slide
"Mid01 Updates Rules 10/22" trong `SDC 2026 Midterm01 Competition - Localization-3.pdf`): không hậu xử lý / không dò bảng điểm,
**chỉ định vị nhân quả** (frame hiện tại và quá khứ, không làm mượt ngược / phi nhân quả), TA chạy lại code, vi phạm = 0 điểm track.
(Văn bản 10/22 ghi chung cho Midterm01 – nên giữ bằng chứng lời cho phép của TA cho Track01/02.)

1. Track03: chỉ thuật toán nhân quả (`tools/track_localize.py`, `tools/run_causal_pipeline.sh`), không dò, không chỉnh tay.
2. Track01/02: dò được (`tools/lb_combine.py`, `tools/make_probes.py`); vẫn giữ bản pipeline (clean) để báo cáo.
3. Mỗi thí nghiệm đổi một thứ, ghi giả thuyết trước; mọi việc commit + push (`mochihat/SDC-midterm-1-`, private).
4. Không commit token Kaggle / dữ liệu; không ghi tên thành viên đội khác; không dùng nhiều tài khoản.
5. Trả lời tiếng Việt; báo cáo / slide nộp thật bằng tiếng Anh.

## 3. Kết quả hiện tại (23/10 13:30)

| | Track01 | Track02 | Track03 |
|---|---|---|---|
| Bảng điểm (tốt nhất) | **0.40** (`lb_t1_r4`, dò – bằng hạng 1 đội 12) | **0.11** (`lb_t2_r3`, dò – hạng 1; đội 12 0.17) | **0.77** (`t3_vN`, nhân quả – hạng 2; dẫn đầu 0.51) |
| Clean (pipeline, không dò) | 0.62 (`t6_range20_turn0_1`: GICP tầm 20 m, bỏ khi cua) | 0.28 (`clean_cfz2_tau15`) | = cột trên (Track03 luôn clean) |
| Ứng viên chờ người dùng duyệt nộp | vòng 5: 9 file dò `result/reg/probes/r5/` (yaw0, yawrate, gyroscale, yaw5–8, along, lateral) → ghép bằng `tools/lb_combine2.py` | – | **`t3_A2h.csv`** (`tools/run_track3.sh`): bám đường suốt track, sửa trôi 29 m của bản N |

Track03 23/10 (`docs/nhat-ky/12-track3-csm-23-10.md`): MHT cũ ghi ngược quỹ đạo (không nhân quả) → đã sửa; lỗi tích phân gyro
(mất 14 % góc quay) → đã sửa; bản N trôi 13–30 m từ frame ~500 (phần lớn private) → CSM + nhiễu GICP dọc 2 m. Bộ đệm
`~/SDC-midterm01/cache` (không commit). Phần public Track03 chỉ là đoạn đầu → điểm public gần như không phản ánh sửa đổi.
Kaggle chỉ hiện 2 chữ số **cắt bớt**. Điểm 5 chữ số cũ: `docs/nhat-ky/data/kaggle_submissions.csv`.

## 4. Pipeline (bài chấm)

```
GNSS /localizer_node/gnss_pose ─► Kalman CTRV + RTS smoother ─► phys_yawb_1 / rts_heading_2
Track01: yaw gyro (τ 7 s) ─► GICP lượt 1 ─► ghép (lọc ≤2 m/3°, trừ lệch TB, mượt 2 s) ─► GICP lượt 2 ─► ghép ─► yaw gyro ─► result_1
Track02: vị trí Kalman ─► yaw gyro (τ 15 s) ─► result_2   (scan matching luôn làm Track02 kém đi)
```

- GICP: `small_gicp`, point cloud `3cameras_ply`, tỉ lệ mỗi frame = 1.646 m / độ cao mặt đường đo được (trung vị 57 frame),
  bản đồ voxel 0.3 m, nguồn 0.5 m, tầm ≤ 40 m. z / roll / pitch lấy từ lượt NDT C++ `c3s08` (Track01) / `c3s10T2` (Track02).
- Yaw: gyro trục z (bias khớp theo hướng chạy) cho phần nhanh + hướng chạy của quỹ đạo Kalman cho phần chậm.
- Chạy lại toàn bộ bằng một lệnh (trên máy, ngoài container): `cd ~/SDC-midterm01 && bash midterm01/tools/run_clean_pipeline.sh`
  → `src/localization/result/reg/rerun/result_{1,2}.csv` (đã kiểm tra: trùng 100 % với file `clean_*`).

## 5. Đang chờ / việc tiếp theo

**Kết quả 22/10 (§13.7):** Track01 `clean_cfz1_tau7` 0.80, `if_iso_1` 0.84, `if_aniso_1` 0.87; Track02 `clean_cfz2_tau15` 0.28,
`if_iso_2` 0.30, `if_aniso_2` 0.30 → bộ ghép mới (`info_fuse.py`) KÉM hơn; giữ pipeline cũ (2 lượt GICP, làm mượt 2 s).
Hàng đợi bot trống (23/10 08:40); `lb_t2_r3` và `t3_full_N` đã nộp lúc 23/10 08:00.

**Brief 22/10 (`docs/brief_claude_code.pdf`) – kết quả ở `docs/nhat-ky/10-tra-loi-cau-hoi.md`:**
- Xong: T0 (sao lưu `~/SDC-midterm01/backup/2026-10-22`), T1, T2 (lỗi do point cloud AI, GICP ~5 mm trên point cloud hoàn hảo),
  T3, T11, T4 (tầm 20 m ổn định nhất), T7 (z/roll/pitch từ bản đồ, đổi 6 cm), T8, T10, T5, T9, T12 (robust GNSS: chỉ 1.9 cm), T13.
- T6 đợt 1 ĐÃ NỘP (người dùng duyệt 23/10): range20 **0.63**, turn0 0.78, mapground 0.81. Đợt 2 (chờ duyệt): tầm 15 m, tầm 20 + bỏ cua,
  Track02 GICP tầm 20 m (`tools/run_track2_gicp.sh`). File ở `src/localization/result/candidates_T6/`:
  `t6_range20_1.csv` (tầm 20 m, dự đoán 0.74–0.84), `t6_turn0_1.csv` (bỏ GICP khi cua, 0.79–0.81),
  `t6_mapground_1.csv` (z/roll/pitch từ bản đồ, 0.79–0.81). Track02 giữ `clean_cfz2_tau15` (không dùng GICP).
- Công tắc thí nghiệm của `tools/run_clean_pipeline.sh`: `TURN_WEIGHT`, `MAX_RANGE`, `GROUND_H`, `POSE_SOURCE1` (mặc định = pipeline).

**Hướng tiếp theo đã có cơ sở (§13.6):** lỗi còn lại là **độ lệch có hệ thống** của GICP do point cloud ảnh bị méo, không phải
nhiễu (Hessian không dự báo được nhiễu từng frame; nhiễu sau lọc gần đẳng hướng 0.505 / 0.494 m). Đề xuất kế tiếp:
**giới hạn tầm point cloud 20 / 30 / 40 m** (độ sâu từ ảnh sai tăng theo bình phương khoảng cách) – 3 file, chỉ đổi `--max-range`
của `gicp_refine.py`. Sau đó: Kalman kết hợp GICP + IMU thay cho làm mượt 2 s.

**Trước 29/10:** nộp bài chấm sạch tốt nhất và **chọn "Use for Final Score"** trên Kaggle cho từng track (người dùng tự làm).

## 6. Những điều đã biết (đừng thử lại)

- `ply_scale = 3` của TA sai (đúng ≈ 9 cho `raw_ply`, ≈ 0.8 cho `3cameras_ply`); NDT ổn định nhưng kém GNSS.
- GICP: 2 lượt tốt nhất, 5 lượt xấu (point cloud méo → cực tiểu lệch); phải `--demean`; yaw của GICP làm xấu yaw.
- Không có ích: hood mask, lọc điểm lạc (SOR), `raw_ply` (LoGeR), hiệu chỉnh trượt (lever) cho hướng chạy, bù trễ yaw GNSS.
- GNSS yaw = hướng chạy từ vị trí GNSS, trễ 1.1–1.4 s, đứng yên khi xe dừng → dùng gyro.
- Đo lệch thời gian GNSS–IMU từ gia tốc kế: không được (±75–220 ms) – `tools/time_offset.py`.
- Thước đo offline `tools/map_fit.py` (độ khớp bản đồ): tương quan hạng với Kaggle 0.92 / 0.67 nhưng **bị GICP đánh lừa** →
  chỉ dùng để loại cấu hình hỏng. `tools/three_hat.py`: không dùng được (các nguồn đều kế thừa lỗi GNSS).

## 7. Môi trường, lệnh hay dùng, bẫy

- Thư mục: `~/SDC-midterm01/{data, midterm01 (repo này), docker-compose.yml}`. Trong container ROS: `/root/midterm`, `/root/data`.
- Docker: `sdc_ros2_dev` (ROS 2 Humble, `docker compose up -d && docker compose exec sdc_ros2_dev bash`), `sdc-reg`
  (Python + small_gicp; mọi công cụ `tools/*.py` chạy bằng
  `docker run --rm -u $(id -u):$(id -g) -v ~/SDC-midterm01:/w -w /w/midterm01 sdc-reg python3 tools/...`).
  **Máy host không có numpy** → luôn chạy Python qua `sdc-reg`.
- Bẫy: Track02 GICP phải dùng `--pose-source c3s10T2` (`c3s10` lấy nhầm độ cao z của Track01 → GICP không chạy).
- Bot Kaggle (không nằm trong repo): `~/kaggle-sdc-bot`. `python3 -I bot.py status` (bảng xếp hạng + lượt đã dùng),
  hàng đợi `queue/track1`, `queue/track2`, file tạm giữ `held/`, `config.json` (`max_submissions_per_run` = 3, budget 15/ngày),
  cron mỗi 30 phút (`run.sh`), log `bot.log`. 15 lượt/ngày/track, reset 08:00 giờ máy (00:00 UTC). Máy phải bật lúc 08:00.
- Kiểm tra file trước khi nộp: `cd ~/kaggle-sdc-bot && python3 -I -c "import sys; sys.path.insert(0,'.'); import bot; print(bot.validate('1','FILE.csv'))"`.

## 8. Tài liệu khác

- Báo cáo (tiếng Anh, bản nháp "như nộp thật"): https://claude.ai/artifact/Kwr2eFuztKcaopy3q2pvc6 – cần sắp lại theo 4 mục TA yêu cầu.
- Slide (13 trang, cần rút còn 6–8 trang cho 4–6 phút): https://claude.ai/artifact/HtWevyxNDjiZXwFW6LJnqt
- Báo cáo PDF tiếng Việt cho người dùng tự đọc: `docs/report/bao_cao_tong_hop.pdf` (cũ, trước 21/10).
- Nhật ký: `docs/nhat-ky/README.md` (mục lục), `08-gicp-va-scale.md` (GICP, yaw, dò điểm, §12 luật TA, §13 hướng mới).
