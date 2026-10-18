# Research notes – dữ kiện cho video bài giảng (BƯỚC 0)

Thu thập ngày 18/10/2026 (UTC+8) từ: `git log` / `git diff` của repo `SDC-midterm-1-`, thư mục `docs/nhat-ky/`
(nhật ký chi tiết, số liệu gốc trong `docs/nhat-ky/data/`), và Kaggle API (lịch sử nộp, leaderboard).
Chỗ không có bằng chứng ghi **[CHƯA CÓ DỮ LIỆU]** và video sẽ không nói là "đã làm".

Quyết định từ người học (trả lời ngày 18/10):
- Video chỉ để **tự học** (không dùng thuyết trình) → không có phần dàn ý slide.
- Giọng `vi-VN-HoaiMyNeural`, 30–45 phút, phong cách video giải thích ngắn kiểu mạng xã hội (hook, câu ngắn, chữ nhảy, tóm tắt "nhớ 3 ý").
- Nói rõ việc **dùng AI** và **"chọn theo điểm Kaggle"** (mục 6, 7).
- Hai lượt nộp ngày 16/10 chỉ là nộp thử để làm quen định dạng → không đưa vào timeline.
- Người học làm **một mình** (nhóm 1 người).

---

## 1. Lịch sử commit – mỗi bước thử hướng gì, sửa gì, kết quả

| Commit | Thời gian | Nội dung | Kết quả / ghi chú |
|---|---|---|---|
| `65d10cb` | 17/10 19:10 | Template gốc của TA + `run_baseline.sh` + 2 script GNSS (`gnss_to_csv.py`, `gnss_smooth_to_csv.py` – viết thêm, không có trong template) | Baseline TA chạy trên máy **trôi 91 m (Track01) / 110 m (Track02)** → dừng |
| `cd985a4` | 19:13 | `localization.cpp`: NDT bắt đầu từ prior GNSS, loại kết quả lệch xa prior, `frame_stride`, `max_input_range`, file debug; `fuse_to_csv.py` | Nền cho các thí nghiệm NDT |
| `64fa10c` | 19:27 | Docker (`pandas<2.1` có nháy, đường dẫn, tắt GPU), README | Build được |
| `49de295` | 19:53 | Công cụ phân tích tỉ lệ / hệ trục point cloud (`ground_scale.py`, `check_frame_alignment.py`) | **`ply_scale` đúng ≈ 9, không phải 3** |
| `f66e1c1`, `dcb9f8d` | 20:28–20:32 | Bộ lọc Kalman CTRV + RTS smoother (nhiễu chọn bằng maximum likelihood); tuỳ chọn lệch thời gian | Track02 0.473 → **0.408** |
| `7a1bfda` | 21:14 | Nhật ký, script tái tạo bài nộp, phân tích lỗi bằng file thăm dò | Tách điểm: Track01 = 0.905 m + 1.77°; Track02 = 0.232 m + 0.88° |
| `8b092ce`, `9bccac2` | 21:45–22:23 | Bộ lọc có yaw GNSS trễ + gyro; tổ hợp yaw theo điểm Kaggle; thử NDT chỉ dùng ảnh | Track01 **1.219**, Track02 **0.345** |
| `116f7c0` | 23:56 | Yaw đoạn xe đứng yên dựng lại bằng gyro; tổ hợp vị trí | Track02 **0.335** |
| `77ea2a9` | 18/10 00:08 | Tham số `start_frame`, chạy NDT song song theo đoạn trên 10 lõi | NDT 3 camera chạy xong qua đêm |
| `4346f1e` … `60c6afd` | 08:15–08:36 | Nhật ký: NDT `3cameras_ply`, tổ hợp vị trí | Track01 **1.076**, Track02 **0.310** |
| `383e15f` | ~11:45 | `tools/bump_yaw.py` (dò yaw theo đoạn 15 s) | Track02 **0.29887**, Track01 **1.05448** (lượt nộp 11:40–11:45) |

`map_modified.cpp`, `visualization.cpp`, các file `launch/` và `config/*.rviz`: **không sửa** so với template.

## 2. Code đã sửa so với template (trích `git diff 65d10cb HEAD -- src/localization/src/localization.cpp`)

Template – mỗi frame NDT bắt đầu từ pose của frame trước:
```cpp
-        Eigen::Matrix4f candidate = pose;
-        const bool converged = AlignNDT(input, submap, pose, candidate, score);
-        if (converged) {
```
Bản sửa – bắt đầu từ prior (GNSS đã làm mượt), loại kết quả lệch xa prior:
```cpp
+        const PriorPose* prior = priors_.empty() ? nullptr : &priors_[index];
+        const Eigen::Matrix4f guess = prior ? PriorGuess(*prior, pose) : pose;
 ...
+        bool accepted = converged;
+        if (converged && prior) {
+            ...
+            accepted = std::hypot(dx, dy) <= max_correction_xy_ &&
+                       std::abs(wrapped_dyaw) <= max_correction_yaw_deg_ * M_PI / 180.0;
+        }
```
Lọc điểm xa (độ sâu từ ảnh càng xa càng sai):
```cpp
+        if (max_input_range_ > 0.0 && point.getVector3fMap().squaredNorm() > max_range_sq) continue;
```
Hàm NDT gốc của template (dùng nguyên, không sửa):
```cpp
    pcl::NormalDistributionsTransform<pcl::PointXYZ, pcl::PointXYZ> ndt;
    ndt.setResolution(ndt_resolution_);
    ndt.setStepSize(ndt_step_size_);
    ndt.setTransformationEpsilon(ndt_transformation_epsilon_);
    ndt.setMaximumIterations(ndt_max_iterations_);
    ndt.setInputSource(source);
    ndt.setInputTarget(target);
    ndt.align(aligned, initial_guess);
```
Tổng: `localization.cpp` +132 dòng, `localization.h` +26; thêm `run_fusion.sh`, `run_image_only.sh`, `run_chunk.sh`, `fuse_to_csv.py`, 20 script trong `tools/`.
**Các file nộp tốt nhất được tạo bằng Python ngoài ROS** (`tools/rts_smoother.py`, `tools/*_projection.py`…); phần C++ NDT dùng để sinh "hiệu chỉnh vị trí".

## 3. Tham số

Mặc định trong `localization.h` (template):

| Tham số | Giá trị | Ý nghĩa |
|---|---|---|
| `map_voxel_leaf_size` | 1.0 m | voxel giảm mẫu bản đồ (Track01: 59 531 846 → 496 909 điểm) |
| `input_voxel_leaf_size` | 0.3 m | voxel giảm mẫu point cloud từ ảnh |
| `submap_half_size` / `submap_half_height` | 100 m / 30 m | vùng bản đồ cắt quanh xe |
| `ndt_resolution` | 8.0 m | kích thước ô NDT |
| `ndt_step_size` | 0.8 | bước tối ưu |
| `ndt_transformation_epsilon` | 0.05 | điều kiện dừng |
| `ndt_max_iterations` | 30 | số vòng lặp tối đa |
| `ply_scale` | **3.0** (sai; đúng ≈ 9 cho `raw_ply`) | nhân tỉ lệ point cloud |
| `max_correction_xy` / `max_correction_yaw_deg` (thêm mới) | 3 m / 5° | ngưỡng loại kết quả NDT |

Cấu hình các thí nghiệm (`docs/nhat-ky/03`):

| Thí nghiệm | ply_scale | NDT res | iter | input voxel | max range | submap | stride | Kết quả |
|---|---|---|---|---|---|---|---|---|
| Baseline TA | 3 | 8 m | 30 | 0.3 | – | 100 | 1 | trôi ~100 m |
| e1 (`raw_ply`) | 2/3/4 | 8 m | 30 | 0.3 | – | 100 | 10 | hiệu chỉnh 3–4 m, yaw ±24–47° |
| e2 (`raw_ply`) | **9** / 10 | **4** / 8 m | 50 | 0.3 | – | 60 | 20 | ×9 + 4 m: 92 % frame < 1 m (Track02) |
| NDT chỉ ảnh (thử 150 frame) | 9 | 4 m | 30 | 1.0 | 40 m | 60 | 1 | trôi 9 m |
| `3cameras_ply` | **0.8** / 0.85 / 1.0 | 4 m | 50 | 0.5 | 40 m | 60 | 2–4 | Track01 ×0.8: vị trí 0.905 → 0.836 m; ×1.0 xấu đi; Track02: không giúp khi dùng riêng |

**ICP: [CHƯA CÓ DỮ LIỆU]** – chưa thử (repo không có code ICP). Video dạy ICP như kiến thức nền, không nói "đã dùng".

## 4. Timeline nộp Kaggle (từng lượt: `docs/nhat-ky/04-cac-lan-nop-kaggle.md`)

(Trước đó có 2 lượt nộp thử ngày 16/10 để làm quen định dạng – không tính.)

| Đợt | Khi nào | Làm gì | Track01 | Track02 | Rút ra |
|---|---|---|---|---|---|
| 1 | 17/10 18:51–19:00 | GNSS nội suy / làm mượt / yaw theo hướng chạy | 1.311 → 1.262 | 0.571 → 0.473 | GNSS rất gần đáp án; mỗi track cần cách khác |
| 2 | 20:18 | ghép NDT `raw_ply` ×9 | – | 0.535 ❌ | NDT kém hơn GNSS |
| 3 | 20:28 | Kalman CTRV + maximum likelihood | 1.260 | **0.408** | mô hình vật lý tốt hơn làm mượt tuỳ ý |
| 4–5 | 20:30–20:43 | 8 file thăm dò (thời gian ±0.1 s, ngang ±0.5 m, yaw ±1°) | 1.28–1.74 | 1.28–1.38 | Δt ≈ 0, không lệch ngang; tách lỗi vị trí / yaw |
| 6 | 20:44 | bỏ lệch yaw cố định 0.42° (từ dữ liệu) | **1.253** | – | dự đoán 1.25339, thực tế 1.25338 |
| 7 | 21:38–21:41 | bù độ trễ yaw GNSS; yaw trễ 0.75 s | 1.309 ❌ | 0.455 / 0.486 ❌ | đáp án không dùng hướng chạy đúng giờ |
| 8–9 | 21:44–21:50 | tổ hợp yaw theo điểm Kaggle | **1.219** | **0.345** | trọng số không có ý nghĩa vật lý |
| 10 | 23:54 | yaw đoạn xe đứng yên từ gyro | 1.219 | **0.335** | yaw GNSS đóng băng khi xe dừng |
| 11 | 18/10 08:07–08:31 | NDT `3cameras_ply` + tổ hợp vị trí | **1.076** | **0.310** | NDT 3 camera ×0.8 sửa được vị trí lần đầu |
| 12 | 10:24–10:37 | 9 file dò yaw theo đoạn 15 s (Track02) | – | 0.322–0.342 | lỗi yaw còn lại thay đổi nhanh |
| 13 | 11:37–11:45 | NDT 3 camera ×0.8 (T2), ×0.85 (T1) + tổ hợp vị trí & yaw | **1.054** | **0.299** | Track02 lên hạng 2 |

Leaderboard ~11:45 18/10: Track01 – đội 13 0.85886, đội 12 0.93699, **bạn 1.05448 (hạng 3)**, đội 3 1.15275, đội 6 1.62239, baseline 1.79075.
Track02 – đội 12 0.28263, **bạn 0.29887 (hạng 2)**, đội 3 0.30576, đội 13 0.35142, đội 6 0.56911, baseline 1.92587.
File tốt nhất **chỉ dùng tham số vật lý**: Track01 1.25338, Track02 0.40778 (vẫn vượt xa baseline).

## 5. Phát hiện chính (số liệu thật, dùng cho chương "mình đã làm gì")

1. `ply_scale` của template sai: mặt đường 0.18 đơn vị dưới camera, camera cao ~1.6 m → tỉ lệ ≈ 9 (`data/ground_scale.txt`).
2. Topic `/localizer_node/gnss_pose`: 4 Hz, `z` hằng số; yaw **tính từ dịch chuyển vị trí trong 1 s, cập nhật ~1.25 s/lần**, **đóng băng khi xe dừng**
   (Track02 13 s đầu: −15.2°, yaw thật ≈ −19.8°).
3. Gyro z có bias ≈ −0.25…−0.30 °/s; IMU đúng giờ.
4. `init_guess` có nhiễu: Track02 lệch yaw 14.85°.
5. Lỗi Track01 chủ yếu là vị trí (0.905 m) → NDT `3cameras_ply` ×0.8 (camera ~1.65 m, khớp ×9 của `raw_ply`) giảm còn 0.836 m.

## 6. Dùng AI như thế nào (có dẫn chứng)

- **Công cụ:** Claude Code (trợ lý AI chạy trong terminal Ubuntu), một phiên làm việc liên tục từ 17/10 đến 18/10.
- **Đưa vào gì:** link cuộc thi Kaggle, ảnh chụp màn hình (token API, lỗi terminal, leaderboard), slide đề bài (link Google Slides),
  file zip dữ liệu và code mẫu đã tải, và các yêu cầu bằng lời ("chạy NDT", "lên top 1", "ghi nhật ký"…).
- **AI đã làm (bằng chứng):**
  - Viết/sửa **toàn bộ code trong các commit** ở mục 1 (`localization.cpp`/`.h`, các script `run_*.sh`, 20 file trong `tools/`,
    `processing_codes/gnss_*.py`, `fuse_to_csv.py`), sửa Dockerfile, chạy thí nghiệm, phân tích số liệu, viết `docs/nhat-ky/`.
  - **Đề xuất hướng:** dùng GNSS làm prior, kiểm tra tỉ lệ point cloud (tìm ra ×9), bộ lọc Kalman, file thăm dò để tách lỗi,
    phương pháp tổ hợp theo điểm Kaggle, sửa yaw lúc xe đứng yên, NDT 3 camera.
  - Nộp phần lớn bài lên Kaggle bằng script (tên file trên Kaggle có hậu tố ngẫu nhiên như `_6b9926`).
  - Commit không có dòng ghi tên AI; mọi commit trong repo sau `8d5f06a` đều do AI tạo trong phiên này.
- **Người học đã làm / quyết định:** tải dữ liệu bằng trình duyệt; tạo token Kaggle và đăng nhập GitHub; **tự nộp 6 file GNSS đầu tiên**
  (tên không có hậu tố); quyết định làm một mình; cho phép chỉnh theo điểm Kaggle ("thầy không cấm thì cứ làm"); quyết định dùng thêm lõi CPU,
  dừng/tiếp tục các thí nghiệm; yêu cầu ghi nhật ký minh bạch.
- **Đã kiểm tra:** mọi file nộp được tạo lại từ dữ liệu gốc và so khớp từng byte (`tools/reproduce_submissions.sh`, 34/34 file đến sáng 18/10);
  dự đoán điểm được đối chiếu với điểm Kaggle thật.
- **[CHƯA CÓ DỮ LIỆU]** việc người học tự đọc/kiểm tra lại từng dòng code – video không khẳng định điều này.

## 7. "Chọn theo điểm Kaggle" nghĩa là gì

- **Quy trình:** tạo nhiều phiên bản kết quả (khác tham số hoặc khác cách tính) → nộp lên Kaggle → xem điểm → giữ cái tốt hơn.
  Bản nâng cao đã dùng: giữ nguyên vị trí, chỉ đổi yaw (hoặc ngược lại) → mỗi lượt nộp cho biết chính xác một "hướng thay đổi" tốt hay xấu bao nhiêu
  → giải phương trình bậc 2 để ra tổ hợp tối ưu (`tools/yaw_projection.py`, `tools/pos_projection.py`); dự đoán khớp điểm thật tới ~0.001.
- **Ưu điểm:** cải thiện điểm nhanh mà không cần hiểu đáp án được tạo thế nào; đo được những thứ dữ liệu không cho biết
  (ví dụ: tách điểm thành lỗi vị trí và lỗi yaw).
- **Rủi ro:**
  - **Overfit vào leaderboard:** ở cuộc thi này leaderboard tính trên **toàn bộ** dữ liệu test (không có private leaderboard) –
    chỉnh theo điểm là khớp trực tiếp với đáp án, không phải thuật toán tốt hơn; trọng số tìm được thường **không có ý nghĩa vật lý** (vd. −4.58).
  - **Tốn lượt:** mỗi hướng tốn 1 lượt; 15 lượt/ngày/track; dò sai lãng phí cả ngày.
  - **Rủi ro học thuật:** báo cáo chấm "đóng góp gốc"; phải nói rõ phần nào chọn theo điểm.

## 8. Những gì KHÔNG có – [CHƯA CÓ DỮ LIỆU]

- ICP: chưa thử. `map_modified.cpp`: chưa dùng. `visualization.cpp` / RViz: chưa chạy (chỉ chạy không giao diện).
- Code LoGeR: chưa chạy; MapAnything: chỉ dùng file `3cameras_ply` có sẵn.
- Report PDF: chưa có.
- Ảnh chụp RViz: chưa có → hình quỹ đạo trong video sẽ vẽ bằng matplotlib từ CSV trong `docs/nhat-ky/submissions` và bản đồ `map_downsampled_1m.pcd`.
- Đề ghi `process/txt_to_idx_x_y_yaw.py`; repo thực tế là `src/localization/processing_codes/txt_to_idx_x_y_yaw.py`.

## 9. Nhạc / hiệu ứng âm thanh

Không tải nhạc tự động từ Pixabay/YouTube (cần trình duyệt + đăng nhập, khó xác minh license tự động).
Phương án: **tự tổng hợp nhạc nền và SFX bằng code** (numpy → WAV, bản quyền thuộc về người tạo, ghi CC0 trong `assets/CREDITS.md`).
Nếu muốn nhạc "viral" thật hơn: tải tay một bài từ Pixabay Music (license Pixabay), đặt vào `video/assets/music/` và ghi nguồn vào `CREDITS.md`
– `build.py` sẽ ưu tiên file đó.
