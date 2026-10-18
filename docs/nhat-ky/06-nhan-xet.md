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
10. **Khoảng cách tới hạng 1 ≈ phần lỗi yaw** ở cả 2 track (cần yaw ~0.5°) → yaw là đòn bẩy lớn nhất còn lại
    (đúng lúc ~21:00; sau khi đội 13 đạt 0.913 ở Track01 thì Track01 cần giảm cả lỗi vị trí).
11. **IMU đúng giờ, gyro z có bias ≈ −0.25…−0.30 °/s.** (Lúc đầu tưởng đồng hồ IMU lệch 1.5 s – sai; xem ý 13.)
12. **`init_guess` có nhiễu lớn** (Track02 lệch yaw 14.85°) – thuật toán chỉ dựa vào nó rất dễ hỏng ngay từ frame đầu.
13. **Yaw của topic GNSS trễ 1.1–1.4 s** so với vị trí GNSS và gyro. "Độ lệch yaw cố định" tìm được trước đó (−0.42° / +0.65°)
    phần lớn chỉ là hệ quả của độ trễ trên quãng đường rẽ một chiều.
14. **Yaw của đáp án không trùng với nguồn yaw "vật lý" nào ta có:** hướng chạy đúng giờ (lỗi 2.02° / 1.11°), hướng chạy trễ 0.75 s (1.27°),
    yaw GNSS gốc (1.65°) đều kém hơn tổ hợp. Cách đáp án được tạo ra vẫn chưa rõ.
15. **Giữ vị trí cố định thì mỗi lượt nộp đo được chính xác một "hướng" yaw**, và tổ hợp tối ưu dự đoán đúng điểm tới 0.0003 –
    nhưng trọng số thu được (vd. −4.58) **không có ý nghĩa vật lý**.
16. **`3cameras_ply` gần đúng đơn vị mét** (mặt đường 2.06 m dưới camera), nhìn xa 30–70 m – nguồn tiềm năng để sửa vị trí Track01.
17. **Đội 13 cải thiện rất nhanh** (Track01 1.118 → 0.913 trong ~20 phút) – có lẽ cũng đang dò bằng bảng điểm.
18. **Yaw GNSS thực chất là hướng dịch chuyển của vị trí GNSS** (cửa sổ 1 s, cập nhật ~1.25 s/lần) – không có thông tin mới; "trễ 1.1–1.4 s"
    là hệ quả của cách tính này.
19. **Khi xe đứng yên yaw GNSS đóng băng** (Track02: 13 s đầu, sai ~4.6°). Gyro (bias đo lúc đứng yên) dựng lại được yaw thật → Track02 −0.010.
20. **NDT `3cameras_ply` ở tỉ lệ 0.8 sửa được vị trí GNSS** (Track01 0.905 → 0.836 m) – lần đầu scan matching thắng GNSS; tỉ lệ 1.0 thì không.
    Tỉ lệ 0.8 ứng với camera cao ~1.65 m, khớp tỉ lệ ×9 của `raw_ply` – hai cách đo độc lập cho cùng độ cao camera.
21. **Chạy song song theo đoạn** (frame độc lập khi có prior) tăng tốc ~2.5× trên 10 lõi.
22. Các đội khác cải thiện liên tục qua đêm (đội 12: Track02 0.333 → 0.283; Track01 1.004 → 0.937) – bảng xếp hạng thay đổi nhanh.

## 2. Cái gì hiệu quả, cái gì không

| Hiệu quả | Không hiệu quả |
|---|---|
| Dùng GNSS làm nền | NDT ×3 (baseline) – trôi ~100 m |
| Bộ lọc Kalman CTRV, nhiễu chọn bằng maximum likelihood | Ghép hiệu chỉnh NDT ×9 vào GNSS (cả 2 track) |
| Ước lượng và bỏ độ lệch yaw cố định | Làm mượt GNSS khi GNSS đã mượt (Track02) |
| File thăm dò để tách lỗi vị trí / yaw (3 ước lượng độc lập khớp nhau) | Yaw theo hướng chạy khi vị trí bị giật (Track01) |
| Kiểm tra đầu vào (tỉ lệ, hệ trục) bằng mặt đường | Chọn tỉ lệ theo "khoảng cách nhỏ nhất tới bản đồ" (thiên vị tỉ lệ nhỏ) |
| Tổ hợp yaw từ các lượt chỉ đổi yaw (điểm Kaggle) | Bù trễ yaw GNSS / yaw trễ 0.75 s / hiệu chỉnh độ cong |
| Kiểm tra giả thuyết bằng likelihood của bộ lọc (phát hiện cách hiểu sai về IMU) | NDT chỉ dùng ảnh khi chưa có mô hình chuyển động (trôi 9 m sau 150 frame) |

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
- **Hiểu sai một phép tương quan.** Tương quan gyro – yaw GNSS cao nhất ở độ trễ 1.45 s được hiểu thành "đồng hồ IMU lệch";
  likelihood của bộ lọc Kalman cho thấy ngược lại (IMU đúng giờ, yaw GNSS trễ). Bài học: kiểm tra giả thuyết bằng mô hình đầy đủ, không chỉ tương quan.
- **Hướng phụ thuộc tuyến tính** khi tính tổ hợp (đưa cả file vốn là tổ hợp của file khác) làm phương trình suy biến, ra hệ số hàng triệu – phải loại ra.
- **Giả thuyết đẹp chưa chắc đúng với đáp án:** bù trễ yaw đúng về vật lý nhưng sai với cách đáp án được tạo – chỉ một lượt nộp mới trả lời được.

## 4. Rủi ro cho điểm môn học và khuyến nghị

1. **Kết quả tốt nhất không dùng scan matching**, trong khi đề yêu cầu *"Design your own scan matching algorithm"* và báo cáo + thuyết trình
   (50 điểm) chấm vào đóng góp. Nên trình bày đủ: phát hiện tỉ lệ ×9, NDT có prior + loại kết quả xấu, thống kê hiệu chỉnh, lý do NDT không thắng GNSS,
   và bổ sung một kết quả **chỉ dùng ảnh** (NDT ×9, độ phân giải 4 m, chỉ dùng `init_guess`) để so với baseline.
2. **Các lượt thăm dò bằng Kaggle** nên được ghi minh bạch trong báo cáo (đo Δt, lệch ngang, lệch yaw; không đưa tham số Kaggle vào file cuối).
3. **Dùng AI:** môn học không cấm; phần lớn code được viết với sự hỗ trợ của AI – nên ghi rõ trong báo cáo, và cần tự hiểu pipeline để trình bày/trả lời câu hỏi.
4. **Chọn bài chấm cuối trên Kaggle:** kiểm tra trong tab Submissions rằng `phys_yawb_1.csv` (1.25338) và `rts_heading_2.csv` (0.40778) được dùng.
5. **E3:** file nộp tốt nhất hiện tại là `submissions/track1/yawproj_v1_1.csv` và `submissions/track2/yawproj_v3_2.csv` (trọng số theo Kaggle);
   file tốt nhất chỉ dùng tham số vật lý là `phys_yawb_1.csv` và `rts_heading_2.csv`. Nên trình bày cả hai và nói rõ phần nào chọn theo Kaggle.
6. **Trọng số chọn theo Kaggle của Track02 (−2.16, −4.58…) không có ý nghĩa vật lý** – nếu muốn chắc chắn hợp lệ, hỏi giảng viên.
7. Làm **một mình** (nhóm 1 người): Workload Distribution = 100 %; nếu có dùng AI hỗ trợ thì ghi rõ.

## 5. Hướng tiếp theo (cập nhật tối 17/10)

1. **Track02 (sáng 18/10: 0.30984, hạng 1 là 0.28263):** thêm hướng vị trí từ NDT 3 camera (đã chạy xong) và các hướng yaw mới.
2. **Track01 (sáng 18/10: 1.07618, hạng 1 là 0.89331):** NDT 3 camera tỉ lệ 0.8 có ích → thử các tỉ lệ / độ phân giải khác (0.7, 0.85, NDT 2 m)
   làm thêm hướng vị trí; người dùng đã cho phép tiếp tục chọn trọng số theo điểm Kaggle (dò theo từng đoạn đường nếu cần).
3. **Kết quả chỉ dùng ảnh** cho báo cáo: thêm mô hình chuyển động + thử nhiều góc ban đầu vào NDT ×9.
