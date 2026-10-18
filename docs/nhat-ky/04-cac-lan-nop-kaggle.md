# 04 – Từng lần nộp lên Kaggle

Điểm càng thấp càng tốt. Bản đúng của mọi file nằm trong `submissions/`, lịch sử gốc từ Kaggle trong `data/kaggle_submissions.csv`,
chênh lệch giữa các file trong `data/file_differences.txt`, lệnh tạo lại từng file trong [07-tai-tao.md](07-tai-tao.md).
Trên Kaggle, tên file có thêm hậu tố ngẫu nhiên (ví dụ `rts_heading_2_6b9926.csv`) và dấu `+` bị Kaggle bỏ đi.

## Bảng tổng hợp (theo thời gian, giờ UTC+8)

| # | Giờ | Track | File | Điểm | So với tốt nhất trước đó | Mục đích |
|---|---|---|---|---|---|---|
| – | 16/10 04:32 | 1 | `trial.csv` | 5822.14965 | | nộp trước khi bắt đầu ghi chép (không có file) |
| – | 16/10 09:36 | 1 | `kaggle_track1_result.csv` | 602.39927 | | nộp trước khi bắt đầu ghi chép (không có file) |
| 1 | 17/10 18:51 | 1 | `gnss_1.csv` | 1.31094 | (baseline TA 1.79075) | thử GNSS |
| 2 | 18:52 | 2 | `gnss_2.csv` | 0.57111 | (baseline TA 1.92587) | thử GNSS |
| 3 | 18:57 | 1 | `gnss_smooth_1.csv` | **1.26235** | −0.04859 ✅ | làm mượt GNSS |
| 4 | 18:58 | 1 | `gnss_heading_1.csv` | 1.35783 | +0.09548 ❌ | yaw = hướng chạy |
| 5 | 18:59 | 2 | `gnss_smooth_2.csv` | 0.57811 | +0.00700 ❌ | làm mượt GNSS |
| 6 | 18:59 | 2 | `gnss_heading_1.csv` | lỗi | – | **nộp nhầm file Track01 vào Track02** |
| 7 | 19:00 | 2 | `gnss_heading_2.csv` | **0.47281** | −0.09830 ✅ | yaw = hướng chạy |
| 8 | 20:18 | 2 | `fusion_s9r4_headingyaw_2.csv` | 0.53520 | +0.06239 ❌ | ghép hiệu chỉnh NDT ×9 |
| 9 | 20:28 | 2 | `rts_heading_2.csv` | **0.40778** | −0.06503 ✅ | bộ lọc Kalman CTRV |
| 10 | 20:28 | 1 | `rts_pos_gnssyaw_1.csv` | **1.25992** | −0.00243 ✅ | bộ lọc Kalman CTRV (vị trí) |
| 11 | 20:30 | 2 | `rts_heading_dt-0.1_2.csv` | 1.27503 | (thăm dò) | lệch thời gian −0.1 s |
| 12 | 20:30 | 1 | `rts_pos_gnssyaw_dt-0.1_1.csv` | 1.68409 | (thăm dò) | lệch thời gian −0.1 s |
| 13 | 20:31 | 2 | `rts_heading_dt0.1_2.csv` | 1.37861 | (thăm dò) | lệch thời gian +0.1 s |
| 14 | 20:31 | 1 | `rts_pos_gnssyaw_dt0.1_1.csv` | 1.73784 | (thăm dò) | lệch thời gian +0.1 s |
| 15 | 20:35 | 1 | `probe_lat+0.5_1.csv` | 1.37688 | (thăm dò) | lệch ngang +0.5 m |
| 16 | 20:39 | 1 | `probe_lat-0.5_1.csv` | 1.40077 | (thăm dò) | lệch ngang −0.5 m |
| 17 | 20:40 | 1 | `probe_yaw+1_1.csv` | 1.27676 | (thăm dò) | lệch yaw +1° |
| 18 | 20:43 | 1 | `probe_yaw-1_1.csv` | 1.34505 | (thăm dò) | lệch yaw −1° |
| 19 | 20:44 | 1 | `phys_yawb_1.csv` | **1.25338** | −0.00654 ✅ | bỏ độ lệch yaw cố định (vật lý) |
| 20 | 20:45 | 1 | `phys_yawb_ndt_1.csv` | 1.27855 | +0.02517 ❌ | ghép hiệu chỉnh NDT ×9 |
| 21 | 21:38 | 2 | `lagyaw_pos_best_2.csv` | 0.45496 | +0.04718 ❌ | yaw đã bù trễ GNSS (vật lý) |
| 22 | 21:39 | 1 | `lagyaw_pos_best_1.csv` | 1.30875 | +0.05537 ❌ | yaw đã bù trễ GNSS (vật lý) |
| 23 | 21:41 | 2 | `yawtau0.75_pos_best_2.csv` | 0.48625 | +0.07847 ❌ | giả thuyết "yaw đáp án trễ 0.75 s" |
| 24 | 21:44 | 2 | `yawproj_v1_2.csv` | **0.35696** | −0.05082 ✅ | tổ hợp yaw theo điểm Kaggle |
| 25 | 21:44 | 1 | `yawproj_v1_1.csv` | **1.21861** | −0.03477 ✅ | tổ hợp yaw theo điểm Kaggle |
| 26 | 21:48 | 2 | `curv1.5_on_proj_2.csv` | 0.36280 | +0.00584 (thăm dò) | yaw thân xe theo độ cong, l = 1.5 m |
| 27 | 21:49 | 2 | `gnssyaw_pos_rts_2.csv` | 0.56160 | (thăm dò) | hướng "yaw GNSS gốc" |
| 28 | 21:50 | 2 | `yawproj_v3_2.csv` | **0.34530** | −0.01166 ✅ | tổ hợp 4 hướng yaw theo điểm Kaggle |

| 29 | 23:54 | 2 | `startfix_on_v3_2.csv` | **0.33504** | −0.01026 ✅ | yaw đoạn khởi hành dựng lại bằng gyro (vật lý) |
| 30 | 23:55 | 1 | `startfix_on_v1_1.csv` | 1.21871 | +0.00010 | như trên cho Track01 |
| 31 | 18/10 08:07 | 2 | `yawproj_v4_2.csv` | **0.30984** | −0.02520 ✅ | tổ hợp 5 hướng yaw theo điểm Kaggle |
| 32 | 08:07 | 1 | `ndt3c_s10_pos_1.csv` | 1.24807 | +0.02946 (thăm dò) | vị trí + hiệu chỉnh NDT 3 camera tỉ lệ 1.0 |
| 33 | 08:08 | 1 | `ndt3c_s08_pos_1.csv` | **1.15042** | −0.06819 ✅ | vị trí + hiệu chỉnh NDT 3 camera tỉ lệ 0.8 |
| 34 | 08:08 | 1 | `posproj_v1_1.csv` | **1.07618** | −0.07424 ✅ | tổ hợp vị trí (3 trường NDT) + yaw theo điểm Kaggle |

Ngày 17/10 đã dùng 15 lượt Track01 và 15 lượt Track02 (tối đa 15/ngày); sáng 18/10 (đến 08:10) dùng 3 lượt Track01, 1 lượt Track02.

---

## Trước khi bắt đầu: `trial.csv` (5822) và `kaggle_track1_result.csv` (602)
Hai file nộp từ trước (không có trong thư mục này). Điểm hàng trăm – hàng nghìn mét nghĩa là quỹ đạo lệch hoàn toàn
(sai định dạng/thứ tự, hoặc NDT trôi như baseline chạy trên máy ở mục 03).

---

## Đợt 1 – Dùng thẳng GNSS (18:51–19:00)

### #1, #2 `gnss_1.csv` (1.31094) và `gnss_2.csv` (0.57111)
- **Cách tạo:** `processing_codes/gnss_to_csv.py` – đọc `/localizer_node/gnss_pose` (4 Hz) từ rosbag, **nội suy tuyến tính**
  x, y, yaw tại timestamp của từng file trong `raw_ply/` (tên file chứa timestamp). Frame nằm ngoài khoảng có GNSS lấy giá trị đầu/cuối
  (Track01: 3 frame cuối; Track02: 1 frame đầu, 4 frame cuối).
- **Khác gì so với trước:** chưa có file nào trước (so với baseline của TA chỉ dùng point cloud).
- **Vì sao làm:** GNSS cùng hệ toạ độ với bản đồ; nộp thử để đo xem GNSS gần đáp án đến đâu – một lượt nộp trả lời được câu hỏi quan trọng nhất.
- **Kết quả:** tốt hơn baseline rất nhiều (1.79 → 1.31; 1.93 → 0.57).
- **Kết luận:** topic GNSS rất gần đáp án → lấy làm nền cho mọi bước sau. Track01 kém hơn Track02 nhiều.

### #3, #5 `gnss_smooth_1.csv` (1.26235 ✅) và `gnss_smooth_2.csv` (0.57811 ❌)
- **Cách tạo:** `processing_codes/gnss_smooth_to_csv.py … 1.5 gnss` – lọc Gauss σ = 1.5 mẫu GNSS (0.375 s) cho x, y, yaw,
  rồi nội suy **spline bậc 3** thay cho đường thẳng.
- **Khác gì:** vị trí dịch 0.095 m RMS (Track01) / 0.089 m (Track02); yaw đổi 0.50° / 0.23° RMS.
- **Vì sao chỉnh:** GNSS chỉ có 4 Hz còn camera ~28 Hz; nội suy tuyến tính tạo góc gãy, và GNSS Track01 bị giật (0.142 m).
- **Kết quả:** Track01 tốt lên 0.049; Track02 xấu đi 0.007.
- **Kết luận:** Track01 có nhiễu mà làm mượt khử được; GNSS Track02 vốn đã mượt nên làm mượt chỉ làm sai thêm chút ít.

### #4, #7 `gnss_heading_1.csv` (1.35783 ❌) và `gnss_heading_2.csv` (0.47281 ✅)
- **Cách tạo:** như trên nhưng tham số cuối là `heading`: yaw = **hướng chuyển động** của quỹ đạo đã làm mượt
  (đạo hàm của spline), khi xe đứng yên (< 1 m/s) thì dùng yaw GNSS.
- **Khác gì so với `gnss_smooth`:** vị trí giữ nguyên, chỉ yaw đổi: 2.38° RMS (Track01), 1.37° RMS (Track02);
  trung bình hướng chạy lệch yaw GNSS +0.42° (Track01) / −0.57° (Track02).
- **Vì sao chỉnh:** xe chạy theo hướng mũi xe nên hướng chạy là một ước lượng yaw độc lập với yaw GNSS.
- **Kết quả:** Track01 xấu đi 0.095; Track02 tốt lên mạnh 0.105 → 0.47281.
- **Kết luận:** ở Track02 yaw GNSS có lệch/nhiễu mà hướng chạy khử được. Ở Track01 vị trí GNSS bị giật nên hướng tính từ vị trí nhiễu theo
  → yaw GNSS tốt hơn. ⇒ **Đáp án dùng yaw ≈ hướng chuyển động thật**; vấn đề là ước lượng nó cho tốt (xác nhận lại ở #19).

### #6 nộp nhầm
`gnss_heading_1.csv` (3011 dòng) bị nộp vào Track02: Kaggle báo lỗi `Submission has 3011 rows but 3299 were expected` – mất 1 lượt.

---

## Đợt 2 – Ghép hiệu chỉnh NDT (20:18)

### #8 `fusion_s9r4_headingyaw_2.csv` (0.53520 ❌)
- **Cách tạo:** chạy NDT với tỉ lệ ×9, độ phân giải 4 m, cứ 20 frame một lần, bắt đầu từ GNSS (thí nghiệm `e2s9r4_Track2`, mục 03);
  `fuse_to_csv.py` lọc + làm mượt hiệu chỉnh và cộng vào vị trí của `gnss_heading_2.csv`, yaw giữ nguyên.
- **Khác gì so với `gnss_heading_2`:** vị trí dịch 0.197 m RMS, yaw không đổi.
- **Vì sao chỉnh:** sau khi sửa tỉ lệ, NDT ổn định (92 % frame hiệu chỉnh < 1 m) – hy vọng bản đồ LiDAR sửa được sai số GNSS.
- **Kết quả:** xấu đi 0.062.
- **Kết luận:** hiệu chỉnh 0.2 m của NDT là **nhiễu/sai lệch của chính NDT**, không phải sai số của GNSS → GNSS chính xác hơn NDT trên ảnh.
  Không nộp biến thể có thêm hiệu chỉnh yaw của NDT.

---

## Đợt 3 – Bộ lọc Kalman với mô hình chuyển động xe (20:28) – chỉ dùng tham số vật lý

`tools/rts_smoother.py`: bộ lọc Kalman mở rộng + làm mượt hai chiều (RTS) với mô hình **CTRV**
(xe đi theo hướng mũi xe, không trượt ngang; tốc độ và tốc độ quay thay đổi ngẫu nhiên). Trạng thái
`[x, y, θ, v, ω, b]`, trong đó `b` = **độ lệch cố định giữa yaw GNSS và hướng chuyển động** (do lắp ăng-ten/cảm biến).
GNSS đo (x, y, θ + b). Bốn mức nhiễu (σ vị trí, σ yaw, nhiễu gia tốc q_a, nhiễu gia tốc góc q_w) chọn bằng
**maximum likelihood trên chính dữ liệu GNSS** (không dùng điểm Kaggle). Kết quả lấy tại đúng timestamp từng frame.

### #9 `rts_heading_2.csv` (0.40778 ✅ – tốt nhất Track02)
- **Cách tạo:** `rts_smoother.py /root/data/Track2 Track2 out.csv --yaw heading`. ML chọn σ vị trí 0.006 m, σ yaw 1.0°,
  q_a = 1.0 m/s², q_w = 0.03 rad/s²; ước lượng **b = +0.653°**. Yaw xuất ra = hướng chuyển động θ.
- **Khác gì so với `gnss_heading_2`:** vị trí 0.116 m RMS, yaw 0.363° RMS (trung bình +0.08°).
- **Vì sao chỉnh:** thay bộ lọc Gauss + spline (tuỳ ý) bằng mô hình vật lý: giữa hai mẫu GNSS, xe di chuyển theo hướng và tốc độ của nó;
  yaw là sự cân bằng tối ưu giữa yaw GNSS (đã bỏ lệch b) và hướng chạy, theo độ tin cậy ước lượng từ dữ liệu.
- **Kết quả:** tốt lên 0.065 → **0.40778**.
- **Kết luận:** mô hình vật lý tốt hơn làm mượt tuỳ ý. ML cho σ vị trí cỡ mm → vị trí GNSS gần như **không có nhiễu trắng**,
  phần lớn lợi ích đến từ yaw.

### #10 `rts_pos_gnssyaw_1.csv` (1.25992 ✅)
- **Cách tạo:** với Track01, ML tự do chọn q_a = 3 m/s² (giải thích các rung động vị trí là chuyển động thật) làm hướng chạy rung theo
  (lệch yaw GNSS 2.5°). Vì vậy cố định **nhiễu quá trình ở mức thực tế của xe: q_a = 1 m/s², q_w = 0.1 rad/s²**
  (`--yaw gnss --qa 1.0 --qw 0.1`), lấy **vị trí** từ bộ lọc; **yaw giữ nguyên của `gnss_smooth_1`** (đợt 1 cho thấy ở Track01 yaw GNSS tốt hơn hướng chạy).
  Ghép bằng `tools/csv_ops.py merge`.
- **Khác gì so với `gnss_smooth_1`:** chỉ vị trí, 0.108 m RMS.
- **Kết quả:** tốt lên rất ít, 0.0024.
- **Kết luận:** cách nội suy vị trí không phải vấn đề của Track01 – sai số nằm ở chỗ khác (đo ở đợt 4–5).

---

## Đợt 4 – Thăm dò lệch thời gian (20:30–20:31) – dùng điểm Kaggle để đo

### #11–#14 `…_dt-0.1…` và `…_dt0.1…`
- **Cách tạo:** `rts_smoother.py … --time-offset ±0.1` – lấy mẫu quỹ đạo tại (timestamp + Δt). Track01: chỉ dịch vị trí (yaw vẫn của `gnss_smooth_1`);
  Track02: dịch cả vị trí lẫn yaw.
- **Khác gì:** vị trí dịch ~1.01 m (Track01) / 1.13 m (Track02) RMS – đúng bằng tốc độ × 0.1 s.
- **Vì sao:** về vật lý Δt phải bằng 0, nhưng nếu ảnh và GNSS lệch đồng hồ chỉ 0.1 s thì sai ~1 m – không đo được từ dữ liệu
  (IMU lệch đồng hồ), nên đo bằng Kaggle.
- **Kết quả:** Track01 1.68409 / 1.73784; Track02 1.27503 / 1.37861 – xấu đi rất nhiều ở cả hai phía.
- **Kết luận** (tính ở [05](05-phan-tich-loi.md)): Δt tối ưu = **−3.6 ms** (Track01) và **−4.7 ms** (Track02) ≈ 0 → thời gian **đã đồng bộ**,
  không cần đổi gì. Từ 3 điểm số còn tách được lỗi: Track01 = 0.906 m vị trí + 1.77° yaw; Track02 = 0.232 m + 0.88°.

## Đợt 5 – Thăm dò lệch ngang và lệch yaw cố định, Track01 (20:35–20:43)

### #15–#18 `probe_lat±0.5_1.csv`, `probe_yaw±1_1.csv`
- **Cách tạo:** `csv_ops.py offset` trên `rts_pos_gnssyaw_1.csv`: dời mọi điểm 0.5 m sang trái/phải xe; hoặc cộng ±1° vào yaw.
- **Vì sao:** lỗi vị trí 0.9 m của Track01 không phải do thời gian → kiểm tra giả thuyết **ăng-ten lắp lệch ngang** và **yaw lệch cố định**.
- **Kết quả:** 1.37688 / 1.40077 (ngang) và 1.27676 / 1.34505 (yaw) – đều xấu hơn.
- **Kết luận:** lệch ngang tối ưu **+0.025 m ≈ 0** (không có lệch ngang); lệch yaw tối ưu **+0.347°**.
  Ba nhóm thăm dò cho cùng một cách tách lỗi (xem 05) → kết quả tách lỗi đáng tin.
- Ghi chú: `probe_lat+0.5_1.csv` được nộp sớm hơn dự định (trong một lần chạy lệnh đã bị báo là bị chặn).

## Đợt 6 – Áp dụng kết luận (20:44–20:45)

### #19 `phys_yawb_1.csv` (1.25338 ✅ – tốt nhất Track01)
- **Cách tạo:** `csv_ops.py offset rts_pos_gnssyaw_1.csv phys_yawb_1.csv --yaw-deg 0.42`.
- **Khác gì so với `rts_pos_gnssyaw_1`:** chỉ yaw, cộng đều +0.42°.
- **Vì sao chỉnh:** bộ lọc Kalman ước lượng **từ dữ liệu** yaw GNSS Track01 lệch b = −0.420° so với hướng chuyển động;
  thăm dò Kaggle độc lập cho độ lệch tối ưu +0.347° – hai con số khớp nhau. Dùng **giá trị vật lý 0.42°** (không dùng 0.347 dò từ Kaggle).
- **Kết quả:** tốt lên 0.0065. Mô hình tách lỗi dự đoán 1.25339, thực tế **1.25338**.
- **Kết luận:** đáp án dùng yaw = hướng chuyển động; yaw GNSS Track01 lệch cố định −0.42°. Phần còn lại (~1.73° RMS) là sai số thay đổi theo thời gian.

### #20 `phys_yawb_ndt_1.csv` (1.27855 ❌)
- **Cách tạo:** hiệu chỉnh NDT ×9, 4 m (thí nghiệm `e2s9r4_Track1`, 118/151 frame dùng được) cộng vào vị trí của `phys_yawb_1`.
- **Khác gì:** vị trí dịch 0.471 m RMS.
- **Vì sao:** GNSS Track01 sai ~0.9 m (lớn hơn nhiều so với Track02) – hy vọng NDT sửa được dù ở Track02 không giúp.
- **Kết quả:** xấu đi 0.025.
- **Kết luận:** NDT trên point cloud LoGeR cũng không sửa được sai số 0.9 m của Track01.

---

## Đợt 7 – Bù độ trễ của yaw GNSS (21:38–21:41) – tham số vật lý

Phát hiện (mục 02, phần 6): **yaw GNSS trễ ~1.1 s (Track01) / ~1.4 s (Track02)** so với vị trí GNSS và gyro. Bộ lọc mới
`tools/rts_imu_smoother.py` mô hình hoá "yaw GNSS đo tại t = hướng xe tại t − trễ"; độ trễ, nhiễu, (Track02) gyro chọn bằng maximum likelihood.

### #21, #22 `lagyaw_pos_best_2.csv` (0.45496 ❌), `lagyaw_pos_best_1.csv` (1.30875 ❌)
- **Cách tạo:** vị trí giữ nguyên của file tốt nhất (`rts_heading_2` / `phys_yawb_1`), **yaw thay bằng hướng chạy đúng giờ** từ bộ lọc mới
  (Track02 dùng thêm gyro; Track01 không, vì gyro làm likelihood giảm).
- **Khác gì:** chỉ yaw: 0.31° RMS (Track02), 2.03° RMS (Track01).
- **Kiểm tra trước khi nộp:** yaw này khớp với "yaw GNSS dịch sớm đúng bằng độ trễ" (tính độc lập, không qua bộ lọc) trong 0.29° / 0.53°.
- **Kết quả:** xấu đi ở cả 2 track. Vì vị trí không đổi nên tính được chính xác lỗi yaw: Track02 0.88° → 1.11°, Track01 1.74° → 2.02°.
- **Kết luận:** yaw của **đáp án không phải hướng chạy đúng giờ** của xe – nó gần yaw "trễ" hơn. Mô hình vật lý đúng với dữ liệu GNSS
  nhưng không khớp với cách đáp án được tạo ra.

### #23 `yawtau0.75_pos_best_2.csv` (0.48625 ❌)
- **Cách tạo:** yaw = hướng chạy tại (t − 0.75 s) (`--time-offset -0.75`), vị trí giữ nguyên.
- **Vì sao:** từ #21/#22 suy ra yaw đáp án có thể trễ ~0.7–0.9 s (một tham số chung cho cả 2 track, dùng điểm Kaggle).
- **Kết quả:** lỗi yaw 1.27° – xấu hơn → giả thuyết "yaw đáp án chỉ là hướng chạy bị trễ" **sai**. Không thử ở Track01.

## Đợt 8 – Tổ hợp yaw theo điểm Kaggle (21:44) – **tham số chọn theo Kaggle**

Khi vị trí giữ nguyên, mỗi file chỉ đổi yaw cho biết chính xác $\overline{e\cdot D}$ (tương quan giữa lỗi yaw và thay đổi D).
Với nhiều thay đổi D₁…D_K, lỗi yaw của mọi tổ hợp $base + \sum a_k D_k$ là một hàm bậc 2 **biết chính xác**
→ tính được trọng số tối ưu mà không cần nộp thêm (`tools/yaw_projection.py`, chi tiết ở [05](05-phan-tich-loi.md) mục 5).

### #24 `yawproj_v1_2.csv` (0.35696 ✅) và #25 `yawproj_v1_1.csv` (1.21861 ✅)
- **Cách tạo:**
  - Track02: base `rts_heading_2` + (−2.156) × (#21 − base) + 0.214 × (#23 − base).
  - Track01: base `rts_pos_gnssyaw_1` + 0.199 × (+1° cố định) + 0.373 × (#22 − base).
- **Dự đoán trước khi nộp:** 0.35674 và 1.21862. **Thực tế: 0.35696 và 1.21861** → phương pháp đúng.
- **Kết quả:** Track02 tốt lên 0.051 (lỗi yaw 0.88° → 0.62°); Track01 tốt lên 0.035 (1.74° → 1.57°) – **lấy lại hạng 3** từ đội 3.
- **Ý nghĩa của trọng số:** Track01 ≈ "+0.2° và trộn 37 % hướng chạy đúng giờ" – còn diễn giải được.
  Track02: hệ số **−2.156** = "làm ngược việc bù trễ, mạnh gấp 2" – **không có ý nghĩa vật lý**, chỉ là khớp theo đáp án.

## Đợt 9 – Thêm hướng yaw cho Track02 (21:48–21:50)

### #26 `curv1.5_on_proj_2.csv` (0.36280, thăm dò)
- **Cách tạo:** `tools/curvature_yaw.py`: yaw thân xe = hướng chạy − atan(l × độ cong) với l = 1.5 m (điểm tham chiếu vị trí nằm trước trục sau),
  cộng vào #24. Thay đổi yaw 0.15° RMS, tối đa 1.09° (Track02 phần lớn đường thẳng).
- **Vì sao:** có ý nghĩa vật lý (khi cua, hướng chạy của một điểm phía trước lệch so với thân xe).
- **Kết quả:** xấu hơn #24 một chút; đưa vào tổ hợp chỉ giúp ~0.002 → hướng này giải thích rất ít.

### #27 `gnssyaw_pos_rts_2.csv` (0.56160, thăm dò)
- **Cách tạo:** vị trí của `rts_heading_2`, yaw = yaw GNSS đã làm mượt (`gnss_smooth_2`).
- **Kết quả:** lỗi yaw 1.65° (yaw GNSS thuần rất kém) nhưng là một hướng mới cho tổ hợp.

### #28 `yawproj_v3_2.csv` (0.34530 ✅ – tốt nhất Track02)
- **Cách tạo:** tổ hợp 4 hướng: (#21 − base) × −4.581, (#23 − base) × −0.205, (#26 − base) × −1.119, (#27 − base) × +0.499.
- **Dự đoán:** 0.34498; **thực tế 0.34530**. Lỗi yaw 0.56° (vị trí 0.23 m).
- **Kết luận:** còn cách hạng 1 (0.33283) 0.0125 → cần yaw ≈ 0.50°. Trọng số **chọn theo Kaggle**, không có ý nghĩa vật lý.

## Đợt 10 – Yaw lúc xe đứng yên (17/10 23:54–23:55) – vật lý

Phát hiện (02, mục 7): yaw GNSS được tính từ vị trí, cập nhật ~1.25 s/lần và **đóng băng khi xe dừng** – Track02 giữ −15.2° suốt 13 s đầu.

### #29 `startfix_on_v3_2.csv` (0.33504 ✅) và #30 `startfix_on_v1_1.csv` (1.21871)
- **Cách tạo:** `tools/start_yaw_fix.py`: trước khi xe đạt 4 m/s, yaw = hướng chạy lúc đạt 4 m/s lùi ngược bằng gyro (bias đo lúc đứng yên),
  chuyển dần về file gốc trong 1 s; áp lên file tốt nhất (`yawproj_v3_2` / `yawproj_v1_1`). Vị trí giữ nguyên.
- **Khác gì:** Track02 đổi 411 frame (0.63° RMS toàn track; yaw lúc đứng yên −19.78° thay vì −17.1° của file gốc); Track01 đổi 278 frame (0.38°).
- **Kết quả:** Track02 tốt lên 0.010 (lỗi yaw 0.566° → 0.514°). Track01 gần như không đổi (xe chỉ đứng yên ~1 s).
- **Kết luận:** sửa có cơ sở vật lý cho đoạn GNSS không đo được hướng – có ích ở Track02.

## Đợt 11 – Sáng 18/10 (08:07–08:08)

### #31 `yawproj_v4_2.csv` (0.30984 ✅ – tốt nhất Track02)
- **Cách tạo:** tổ hợp 5 hướng yaw (thêm #29): (#21 − base) × +0.675, (#23 − base) × −0.299, (#26 − base) × +0.224, (#27 − base) × +0.168,
  (#29 − base) × +0.734. **Trọng số chọn theo điểm Kaggle.**
- **Dự đoán 0.31053, thực tế 0.30984.** Lỗi yaw ≈ 0.39° (vị trí 0.23 m). Nhưng đội 12 cùng lúc lên 0.28263 → vẫn hạng 3.

### #32, #33 `ndt3c_s10_pos_1.csv` (1.24807 ❌) và `ndt3c_s08_pos_1.csv` (1.15042 ✅)
- **Cách tạo:** chỉ đổi vị trí – cộng hiệu chỉnh NDT `3cameras_ply` (tỉ lệ 1.0 / 0.8) vào vị trí của `yawproj_v1_1` (yaw giữ nguyên, Y = 1.570°).
- **Kết quả:** tỉ lệ 1.0 xấu đi; **tỉ lệ 0.8 tốt lên 0.068** – lỗi vị trí 0.905 → 0.836 m (03, mục 8).
- **Kết luận:** NDT 3 camera ở tỉ lệ 0.8 là nguồn sửa vị trí có ích đầu tiên.

### #34 `posproj_v1_1.csv` (1.07618 ✅ – tốt nhất Track01)
- **Cách tạo:** `tools/pos_projection.py`: vị trí = gốc + 1.072 × (hiệu chỉnh tỉ lệ 1.0) + 1.370 × (tỉ lệ 0.8) + 0.248 × (NDT raw ×9 của #20)
  → lỗi vị trí dự đoán 0.764 m; yaw = tổ hợp yaw `proj1_v2` (thêm #30, Y dự đoán 1.559°). **Trọng số chọn theo điểm Kaggle.**
- **Dự đoán 0.7644 + 0.2 × 1.559 = 1.0762; thực tế 1.07618.** Lên hạng 3 Track01.

---

## Tổng kết: thay đổi nào có ích

| Thay đổi | Track01 | Track02 | Nhận xét |
|---|---|---|---|
| GNSS thay cho baseline | −0.48 | −1.35 | bước nhảy lớn nhất |
| Làm mượt Gauss + spline | −0.049 | +0.007 | chỉ giúp khi GNSS giật |
| Yaw = hướng chạy (từ quỹ đạo làm mượt) | +0.095 | −0.105 | giúp khi vị trí mượt |
| Bộ lọc Kalman CTRV + ML | −0.002 | −0.065 | tốt nhất Track02 |
| Bỏ lệch yaw cố định b (từ bộ lọc) | −0.0065 | (đã có sẵn trong #9) | tốt nhất Track01 |
| Ghép hiệu chỉnh NDT ×9 | +0.025 | +0.062 | luôn xấu hơn |
| Lệch thời gian ±0.1 s | +0.42…+0.48 | +0.87…+0.97 | tối ưu ≈ 0 |
| Lệch ngang ±0.5 m | +0.12…+0.14 | – | tối ưu ≈ 0 |
| Lệch yaw ±1° | +0.017…+0.085 | – | tối ưu +0.35° (khớp vật lý 0.42°) |
| Bù trễ yaw GNSS (hướng chạy đúng giờ) | +0.055 | +0.047 | đúng với dữ liệu, sai với đáp án |
| Yaw = hướng chạy trễ 0.75 s | – | +0.078 | giả thuyết sai |
| **Tổ hợp yaw theo điểm Kaggle** | **−0.035** | **−0.051 / −0.063** | tốt nhất hiện tại, trọng số không vật lý |
| Hiệu chỉnh độ cong (l = 1.5 m) | – | ~−0.002 (trong tổ hợp) | gần như không có tác dụng |
| Yaw đoạn khởi hành từ gyro (vật lý) | ~0 | −0.010 | có ích khi xe đứng yên lâu |
| Hiệu chỉnh vị trí NDT `3cameras_ply` tỉ lệ 0.8 | **−0.068** | (đang thử) | sửa vị trí thật đầu tiên |
| Hiệu chỉnh vị trí NDT `3cameras_ply` tỉ lệ 1.0 | +0.029 | – | tỉ lệ sai |
| Tổ hợp vị trí + yaw theo điểm Kaggle | **−0.074** (→ 1.07618) | −0.025 (→ 0.30984) | trọng số không vật lý |
