# Trạng thái dự án – đọc file này trước (cập nhật 23/10/2026 17:40)

File này dành cho bất kỳ phiên Claude nào (hoặc người) tiếp nhận dự án: đọc xong là biết đang ở đâu, luật là gì,
làm gì tiếp. Chi tiết từng thí nghiệm: `docs/nhat-ky/` (tiếng Việt). Cách chạy: `docs/HUONG-DAN-CHAY.md`.

## 0. Bàn giao nhanh (25/10/2026 20:50) – phiên mới đọc mục này trước

- Bảng điểm: Track01 **hạng 1** 0.36 (`lb_t1_r5`, dò), Track02 **hạng 1** 0.11 (`lb_t2_r3`, dò), Track03 **hạng 2 public 0.28**
  (`t3_Q4`, nhân quả; đội 12: 0.24). Clean: Track01 0.51 (`clean_mapyaw_1`), Track02 0.24 (`reg/t2v/t2v_tsm10`).
- **Track03 mới (24/10): khớp vạch sơn** camera trước ↔ cường độ bản đồ LiDAR (`docs/nhat-ky/13-track3-vach-son-24-10.md`):
  `tools/run_track3_paint.sh` = Z3a (`tools/run_track3.sh`) → ảnh h265 (`tools/bag_h265.py` + ffmpeg trên máy) →
  `tools/paint_map.py` → `tools/paint_measure.py` → `tools/paint_fuse.py`. Public 0.80 (Z3a) → 0.49 (PA2) → **0.37 (PE3:
  κ 80, tay đòn dọc +0.15, ngang 0)**. Script hiện mặc định tham số PA2 – đổi `FUSE` cho bản cuối. Bộ đệm ảnh / bản đồ:
  `~/SDC-midterm01/cache/Track{1,2,3}` (+ `cache_test` khi chạy lại từ đầu), không commit.
- Hướng tiếp: κ 160+, sàn độ lệch chuẩn, nhiễu quá trình; bản cuối cho private = thông số tốt nhất + `PASSES=3` +
  `--kappa-time 2` (PC3: public 0.50 so với PA2 0.49, khớp tốt hơn ở khúc cua / cuối / lúc đứng chờ đèn). Bản cuối phải
  được NỘP lên Kaggle thì mới chọn được làm bài chấm (người dùng tự chọn).
- **25/10:** PF2 (+ camera trước-trái/phải, khối NCC riêng, κ_side 40) = public **0.33** (hạng 2). Phần private: vị trí DỌC
  rung theo Z3a (0.5 m ở 409–950) → `paint_fuse.py --motion imu` (đi theo tốc độ IMU × tỉ lệ khi ≥ 4 m/s và gần thẳng,
  `--kappa-imu`): `t3_Q1/Q2/Q3` (κ_imu 20/10/5) = **0.28**. Đoạn cuối trượt dọc −1.57 m → trễ IMU (`--imu-vstay 0.5
  --imu-stay-sd 0.08`) = **`t3_Q4` 0.28 = bản cuối đề xuất** (đã nộp). Tay đòn: dọc +0.25 → 0.32, ngang +0.10 → 0.29 (giữ
  +0.15 / 0); tinh chỉnh `t3_Q7` (dọc +0.10) / `t3_Q8` (ngang +0.05) chưa nộp, lợi ≤ 0.01 – nhật ký 13 §7.9–7.12.
- Toàn bộ quá trình trước 24/10: `docs/report/bao_cao_trung_thuc.pdf`; chi tiết `docs/nhat-ky/12-*.md`, `13-*.md`.
- Quy tắc làm việc với người dùng: **mỗi đợt nộp Kaggle phải được người dùng duyệt rõ ràng ("cho phép nộp" + danh sách file)**,
  tối đa 3 file / đợt, mỗi file đổi 1 tham số; 8 giờ sáng (reset lượt) **đừng nộp vội**. Không nhắc "Use for Final Score"
  nhiều lần. Trả lời tiếng Việt.
- Kiểm tra bảng điểm (cron trong phiên cũ – phiên mới phải tạo lại nếu muốn): `python3 -I ~/kaggle-sdc-bot/bot.py status`
  và `tail -5 ~/kaggle-sdc-bot/bot.log`; báo khi đội 11 tụt hạng / đội khác tăng điểm. Nộp: `python3 -I bot.py submit 3 FILE`.
- Track03 theo luật 10/22 (nhân quả, không sửa tay file); người dùng báo TA cho chỉnh tham số theo điểm public.

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

## 3. Kết quả hiện tại (23/10 13:50)

| | Track01 | Track02 | Track03 |
|---|---|---|---|
| Bảng điểm (tốt nhất) | **0.36** (`lb_t1_r5`, dò vòng 5, 23/10 19:56 – hạng 1; đội 12 0.40) | **0.11** (`lb_t2_r3`, dò – hạng 1; đội 12 0.17) | **0.77** (`t3_vN`, nhân quả – hạng 2; dẫn đầu 0.51) |
| Clean (pipeline, không dò) | **0.51** (`clean_mapyaw_1` = `clean_csm_1` + yaw theo bản đồ `tools/map_yaw_fuse.py`, σ 8 s chọn theo bản dò; trước 0.55 / 0.62) | **0.24** (`t2v_tsm10` = `clean_csm_2` + bù trễ GNSS −10 ms `tools/time_shift.py`, chọn theo bảng điểm; trước 0.25 / 0.28) | = cột trên (Track03 luôn clean) |
| Ứng viên / trạng thái | vòng 5 dò: 9 file `result/reg/probes/r5/` – người dùng chưa duyệt (họ muốn ưu tiên cải thiện clean) | – | đã nộp `t3_A2h` 0.96, `t3_L2` 1.05, **`t3_L2b` 0.84** (public = ~15 % frame đầu, không phản ánh private); `t3_W3h` 0.89, **`t3_X3f` 0.80** (= W3h + `--gyro-up` hướng lắp IMU hiệu chuẩn; tốt nhất nhân quả), X3z 0.82, X3l 0.95, Y3a 0.82, Y3c 0.98 (nhật ký 12 §8–10); **`t3_Z3a`** (= X3f + sửa ZUPT / odometry, phần private, ước lượng −0.13…−0.21 điểm private; `tools/run_track3.sh`, §11) public 0.80, nộp 21:01 |

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
