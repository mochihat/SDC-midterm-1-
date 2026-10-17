# 06 – Nhận xét sau khi làm

## 1. Những điều nhận ra về bài toán

1. **Topic `/localizer_node/gnss_pose` gần như là đáp án.** Chỉ nội suy đã được 1.31 / 0.57 so với baseline 1.79 / 1.93.
   Các đội dẫn đầu cũng ở quanh mức này → ở top, cuộc thi thực chất là **tinh chỉnh pose GNSS**, không phải scan matching.
2. **Baseline của TA dùng sai tỉ lệ point cloud.** Mặt đường trong point cloud LoGeR nằm ổn định ở 0.18 đơn vị dưới camera
   (dao động 5–7 %), camera thật cao ~1.6–1.8 m → tỉ lệ ≈ **9**, không phải 3. Với ×3, NDT trôi tới ~100 m.
3. **Tỉ lệ đúng + độ phân giải NDT 4 m làm NDT ổn định** (Track02: 92 % frame hiệu chỉnh < 1 m, yaw ±2°), nhưng
   **NDT trên ảnh vẫn kém chính xác hơn GNSS** → ghép vào luôn làm điểm xấu đi (+0.06 Track02, +0.025 Track01).
4. **Đáp án dùng yaw = hướng chuyển động thật của xe.** Yaw GNSS có **độ lệch cố định** (−0.42° Track01, +0.65° Track02);
   bỏ độ lệch này giúp điểm, và giá trị ước lượng từ dữ liệu khớp với giá trị đo bằng Kaggle (+0.35°).
5. **Vị trí GNSS gần như không có nhiễu trắng** (bộ lọc Kalman ước lượng σ ≈ mm). Sai số còn lại là **sai số chậm** – làm mượt không xử lý được.
6. **Thời gian ảnh–GNSS đã đồng bộ** (Δt tối ưu −3.6 ms / −4.7 ms), **không có lệch ngang** (0.025 m).
7. **Điểm cực kỳ nhạy với thời gian:** lệch 0.1 s làm điểm tăng 0.4–0.97 → nội suy đúng timestamp từng frame là bắt buộc.
8. **Track01 khó hơn Track02:** GNSS giật gấp 3 lần (0.142 so với 0.052 m), lỗi vị trí 0.9 m so với 0.23 m, lỗi yaw 1.74° so với 0.88°.
9. **Cách cải thiện cho từng track khác nhau:** yaw theo hướng chạy giúp Track02 (−0.105) nhưng hại Track01 (+0.095) –
   một mô hình có tham số ước lượng từ dữ liệu (bộ lọc Kalman) xử lý được cả hai mà không phải chọn tay.
10. **Khoảng cách tới hạng 1 ≈ phần lỗi yaw** ở cả 2 track (cần yaw ~0.5°) → yaw là đòn bẩy lớn nhất còn lại.
11. **IMU có bias gyro z ≈ −0.25…−0.30 °/s** và khớp với GNSS tốt nhất khi lệch ~1.5 s (nghi đồng hồ IMU lệch) – cần hiệu chỉnh trước khi dùng.
12. **`init_guess` có nhiễu lớn** (Track02 lệch yaw 14.85°) – thuật toán chỉ dựa vào nó rất dễ hỏng ngay từ frame đầu.

## 2. Cái gì hiệu quả, cái gì không

| Hiệu quả | Không hiệu quả |
|---|---|
| Dùng GNSS làm nền | NDT ×3 (baseline) – trôi ~100 m |
| Bộ lọc Kalman CTRV, nhiễu chọn bằng maximum likelihood | Ghép hiệu chỉnh NDT ×9 vào GNSS (cả 2 track) |
| Ước lượng và bỏ độ lệch yaw cố định | Làm mượt GNSS khi GNSS đã mượt (Track02) |
| File thăm dò để tách lỗi vị trí / yaw (3 ước lượng độc lập khớp nhau) | Yaw theo hướng chạy khi vị trí bị giật (Track01) |
| Kiểm tra đầu vào (tỉ lệ, hệ trục) bằng mặt đường | Chọn tỉ lệ theo "khoảng cách nhỏ nhất tới bản đồ" (thiên vị tỉ lệ nhỏ) |

## 3. Sai lầm và bài học

- **Chạy dài trước khi kiểm tra đầu vào.** Đã chạy baseline (~25 phút) và NDT ×2…×4 (~45 phút) trước khi kiểm tra tỉ lệ point cloud.
  Bài học: luôn kiểm tra đơn vị/hệ trục của dữ liệu trước (5 phút) rồi mới chạy thí nghiệm dài.
- **Thước đo bị thiên vị.** Lần kiểm tra tỉ lệ đầu tiên dùng khoảng cách trung bình tới bản đồ → luôn chọn tỉ lệ nhỏ. Bài học: kiểm tra xem thước đo có thiên vị không, và xem tính nhất quán chứ không chỉ giá trị nhỏ nhất.
- **Tải dữ liệu qua API** mất thời gian (giới hạn tốc độ) trong khi có thể tải zip trên trình duyệt.
- **Nộp nhầm track** (`gnss_heading_1.csv` vào Track02) – mất 1 lượt. Bài học: kiểm tra số dòng trước khi nộp.
- **Một số file từng được tạo bằng đoạn lệnh gõ trực tiếp** (không lưu script) → đã bổ sung `tools/csv_ops.py` và `tools/reproduce_submissions.sh`;
  hiện 19/19 file nộp tạo lại được và trùng khớp từng byte.
- **Dùng lượt nộp:** 2 lượt cho ghép NDT (không hiệu quả) và 8 lượt thăm dò. Thăm dò cho thông tin rất giá trị (mục 05) nhưng tốn lượt –
  nên lên kế hoạch thăm dò theo cặp ± ngay từ đầu.

## 4. Rủi ro cho điểm môn học và khuyến nghị

1. **Kết quả tốt nhất không dùng scan matching**, trong khi đề yêu cầu *"Design your own scan matching algorithm"* và báo cáo + thuyết trình
   (50 điểm) chấm vào đóng góp. Nên trình bày đủ: phát hiện tỉ lệ ×9, NDT có prior + loại kết quả xấu, thống kê hiệu chỉnh, lý do NDT không thắng GNSS,
   và bổ sung một kết quả **chỉ dùng ảnh** (NDT ×9, độ phân giải 4 m, chỉ dùng `init_guess`) để so với baseline.
2. **Các lượt thăm dò bằng Kaggle** nên được ghi minh bạch trong báo cáo (đo Δt, lệch ngang, lệch yaw; không đưa tham số Kaggle vào file cuối).
3. **Quy định dùng AI:** phần lớn code được viết với sự hỗ trợ của AI – nên kiểm tra quy định môn học, và cả nhóm cần hiểu pipeline để trình bày/trả lời câu hỏi.
4. **Chọn bài chấm cuối trên Kaggle:** kiểm tra trong tab Submissions rằng `phys_yawb_1.csv` (1.25338) và `rts_heading_2.csv` (0.40778) được dùng.
5. **E3:** `result_1.csv` = `submissions/track1/phys_yawb_1.csv`, `result_2.csv` = `submissions/track2/rts_heading_2.csv` (nếu không có file tốt hơn).

## 5. Hướng tiếp theo (theo thứ tự ưu tiên)

1. **Cải thiện yaw** (lợi nhất cho cả 2 track): ghép gyro IMU (100 Hz, đã biết bias ~−0.27 °/s) với yaw GNSS sau khi xác định chắc độ lệch thời gian của IMU;
   hoặc hướng chạy từ quỹ đạo với giới hạn gia tốc ngang thực tế.
2. **Kết quả chỉ dùng ảnh** (NDT ×9) để đưa vào báo cáo.
3. **Thử `3cameras_ply`** (3 camera, nhìn rộng hơn) cho NDT.
4. **Phân tích lỗi Track01 theo đoạn đường** (đoạn cua, đoạn nhiều nhà cao tầng) để tìm nơi GNSS sai 0.9 m.
