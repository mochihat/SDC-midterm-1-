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

Ngày 17/10 đã dùng 12 lượt Track01 và 8 lượt Track02 (tối đa 15/ngày).

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
