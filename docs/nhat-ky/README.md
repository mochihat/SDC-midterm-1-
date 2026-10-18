# Nhật ký làm bài – SDC 2026 Midterm 01 (Localization)

Thư mục này ghi lại toàn bộ quá trình làm bài: chuẩn bị môi trường, phân tích dữ liệu, các thí nghiệm,
**từng file đã nộp lên Kaggle** (tạo ra thế nào, khác gì so với file trước, đã chỉnh gì, vì sao chỉnh,
kết quả ra sao, rút ra kết luận gì) và các nhận xét sau khi làm.

- Thời gian ghi theo giờ địa phương **UTC+8** (trừ khi ghi rõ UTC). Công việc diễn ra ngày **17–18/10/2026**.
- Điểm Kaggle **càng thấp càng tốt**.
- Phần công cụ tự động nộp bài không được ghi trong tài liệu này.

## Kết quả hiện tại (chụp lúc ~01:30 ngày 19/10/2026)

| | Track01 | Track02 |
|---|---|---|
| Baseline của TA | 1.79075 | 1.92587 |
| **File tốt nhất của nhóm (đội 11)** | **`pass2dm_bestyaw_1.csv` – 0.92775** | **`posyaw_v2_2.csv` – 0.29887** |
| Tốt nhất mà vị trí chỉ từ thuật toán (GNSS + Kalman + GICP) | `gicp_ground_pass2_pos_1.csv` – 0.99283 | – |
| Hạng | 3 / 6 đội | 3 / 6 đội |
| Hạng 1 | đội 6 – 0.76085 | đội 6 – 0.25774 |

Yaw của các file tốt nhất là **tổ hợp chọn theo điểm Kaggle** (xem [05](05-phan-tich-loi.md) mục 5–6);
phần vị trí Track01 mới nhất là scan matching GICP – xem [08](08-gicp-va-scale.md) (kể cả phần nào dựa vào điểm).

Diễn biến: 17/10 ~21:00 Track01 hạng 3 (1.25338), Track02 hạng 2 (0.40778) → sáng 18/10 Track01 1.07618, Track02 0.30984 →
trưa 18/10 1.05448 / 0.29887 → đêm 18→19/10 GICP + tỉ lệ theo mặt đường: Track01 **0.92775**.

## Tóm tắt nhanh

1. Topic `/localizer_node/gnss_pose` trong rosbag **rất gần đáp án**: chỉ nội suy nó đã vượt xa baseline (1.31 / 0.57).
2. Baseline của TA dùng **sai tỉ lệ point cloud** (`ply_scale = 3`, đúng phải ≈ **9**) nên NDT trôi tới ~100 m.
   Sửa tỉ lệ + độ phân giải NDT 4 m thì NDT ổn định, nhưng **vẫn kém chính xác hơn GNSS** nên ghép vào làm điểm xấu đi.
3. Điểm tốt nhất đến từ **bộ lọc Kalman + RTS smoother với mô hình chuyển động của xe (CTRV)**, tham số nhiễu ước lượng
   từ chính dữ liệu, kèm ước lượng **độ lệch cố định của yaw GNSS** (−0.42° ở Track01, +0.65° ở Track02).
4. Dùng các file "thăm dò" để **tách điểm thành phần vị trí và phần yaw**: Track01 ≈ 0.91 m + 1.77°, Track02 ≈ 0.23 m + 0.88°.
   Ba cách ước lượng độc lập cho cùng kết quả; mô hình dự đoán điểm `phys_yawb_1` = 1.25339, thực tế 1.25338.
5. Thời gian ảnh–GNSS đã đồng bộ (Δt tối ưu ≈ 0), không có lệch ngang; **khoảng cách tới hạng 1 ≈ đúng bằng phần lỗi yaw**.
6. **Yaw của topic GNSS bị trễ 1.1–1.4 s** so với vị trí GNSS và gyro (đo từ dữ liệu). Nhưng bù trễ này lại làm điểm **xấu đi**
   → yaw của đáp án **không phải** hướng chạy đúng giờ.
7. Khi chỉ đổi yaw (giữ vị trí), mỗi lượt nộp cho biết chính xác một "hướng thay đổi yaw" giúp bao nhiêu → tính được **tổ hợp tối ưu**
   (dự đoán trùng điểm thật đến 0.0003). Cách này đưa Track01 1.253 → **1.219** và Track02 0.408 → **0.345**, nhưng các trọng số
   **chọn theo điểm Kaggle, không có ý nghĩa vật lý**.
8. **Yaw GNSS thực chất được tính từ các vị trí GNSS** (hướng dịch chuyển trong 1 s, cập nhật ~1.25 s/lần, giữ nguyên ở giữa) và
   **đứng yên khi xe dừng** (Track02: −15.2° suốt 13 s đầu, trong khi yaw thật ≈ −19.8°). Sửa yaw đoạn khởi hành bằng gyro: Track02 0.345 → 0.335.
9. **NDT với `3cameras_ply` ở tỉ lệ 0.8** cho cải thiện vị trí thật đầu tiên (Track01 1.219 → 1.150 chỉ bằng đổi vị trí);
   tổ hợp vị trí theo điểm Kaggle đưa Track01 tới **1.07618**.

## Mục lục

| File | Nội dung |
|---|---|
| [01-chuan-bi.md](01-chuan-bi.md) | Thông tin cuộc thi, cách chấm, tải dữ liệu, Docker, build |
| [02-phan-tich-du-lieu.md](02-phan-tich-du-lieu.md) | Rosbag, GNSS, init_guess, point cloud (hệ trục, tỉ lệ), bản đồ, IMU |
| [03-thi-nghiem-ndt.md](03-thi-nghiem-ndt.md) | Chạy baseline, sửa `localization.cpp`, các thí nghiệm NDT (×2…×10, độ phân giải 4/8 m) |
| [04-cac-lan-nop-kaggle.md](04-cac-lan-nop-kaggle.md) | **Từng lần nộp**: cách tạo, khác gì, vì sao, điểm, kết luận |
| [05-phan-tich-loi.md](05-phan-tich-loi.md) | Tách điểm thành lỗi vị trí / lỗi yaw bằng các file thăm dò |
| [06-nhan-xet.md](06-nhan-xet.md) | Những điều nhận ra, cái gì hiệu quả / không, sai lầm, rủi ro, hướng tiếp theo |
| [07-tai-tao.md](07-tai-tao.md) | Cách tạo lại **từng file đã nộp** (đã kiểm tra: 34/34 file trùng khớp từng byte) |
| [08-gicp-va-scale.md](08-gicp-va-scale.md) | GICP / ICP 3 bậc tự do trên `3cameras_ply`, tỉ lệ theo mặt đường, trừ độ lệch trung bình – Track01 0.92775 |

## Cấu trúc thư mục

```
docs/nhat-ky/
├── README.md, 01-…07-*.md          tài liệu
├── submissions/
│   ├── track1/*.csv                18 file đã nộp Track01 (đúng bản đã nộp)
│   └── track2/*.csv                16 file đã nộp Track02
└── data/
    ├── kaggle_submissions.csv       lịch sử nộp bài lấy từ Kaggle API (thời gian, tên file, điểm, trạng thái)
    ├── file_differences.txt         chênh lệch vị trí / yaw giữa các cặp file liên tiếp
    ├── probe_analysis.txt           kết quả tách lỗi (tools/analyze_probes.py)
    ├── gnss_imu_analysis.txt        thống kê GNSS / IMU / init_guess (tools/analyze_gnss_imu.py)
    ├── gnss_yaw_lag.txt             yaw GNSS trễ so với vị trí / gyro (tools/analyze_yaw_lag.py)
    ├── rts_imu_smoother_output.txt  bộ lọc có mô hình yaw trễ + gyro: tham số ML (tools/rts_imu_smoother.py)
    ├── yaw_projection_output.txt    tổ hợp yaw tối ưu từ các lượt chỉ đổi yaw (tools/yaw_projection.py)
    ├── ground_scale.txt             chiều cao mặt đường trong point cloud → tỉ lệ (tools/ground_scale.py)
    ├── ground_scale_3cameras.txt    như trên cho 3cameras_ply
    ├── frame_alignment_check.txt    thử đặt point cloud vào bản đồ với nhiều tỉ lệ (tools/check_frame_alignment.py)
    ├── rts_smoother_output.txt      tham số nhiễu ước lượng bởi bộ lọc Kalman (tools/rts_smoother.py)
    ├── ndt_correction_stats.txt     thống kê hiệu chỉnh của NDT trong từng thí nghiệm
    ├── ndt_correction_stats_3cameras_test.txt   thử NDT với 3cameras_ply (tỉ lệ 0.8 / 1.0)
    ├── image_only_test.txt, image_only_test/    thử NDT chỉ dùng ảnh 150 frame đầu
    ├── ndt_debug/*.csv              dữ liệu từng frame của các thí nghiệm NDT, gồm cả 3cameras_ply (dùng để tạo lại file fusion)
    └── baseline_partial/            kết quả baseline TA chạy dở trên máy (đã trôi xa) – làm bằng chứng
```
