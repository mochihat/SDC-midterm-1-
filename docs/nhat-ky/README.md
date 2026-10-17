# Nhật ký làm bài – SDC 2026 Midterm 01 (Localization)

Thư mục này ghi lại toàn bộ quá trình làm bài: chuẩn bị môi trường, phân tích dữ liệu, các thí nghiệm,
**từng file đã nộp lên Kaggle** (tạo ra thế nào, khác gì so với file trước, đã chỉnh gì, vì sao chỉnh,
kết quả ra sao, rút ra kết luận gì) và các nhận xét sau khi làm.

- Thời gian ghi theo giờ địa phương **UTC+8** (trừ khi ghi rõ UTC). Toàn bộ công việc diễn ra ngày **17/10/2026**.
- Điểm Kaggle **càng thấp càng tốt**.
- Phần công cụ tự động nộp bài không được ghi trong tài liệu này.

## Kết quả hiện tại (chụp lúc ~21:00 ngày 17/10/2026)

| | Track01 | Track02 |
|---|---|---|
| Baseline của TA | 1.79075 | 1.92587 |
| **File tốt nhất của nhóm (đội 11)** | **`phys_yawb_1.csv` – 1.25338** | **`rts_heading_2.csv` – 0.40778** |
| Hạng | 3 / 5 đội | 2 / 4 đội |
| Hạng 1 (đội 12) | 1.00423 | 0.33283 |

Leaderboard lúc đó:
- Track01: đội 12 – 1.00423, đội 3 – 1.22369, **đội 11 – 1.25338**, đội 13 – 1.32030, đội 6 – 1.64067, baseline – 1.79075
- Track02: đội 12 – 0.33283, **đội 11 – 0.40778**, đội 13 – 0.53064, đội 3 – 0.56063, baseline – 1.92587

## Tóm tắt nhanh

1. Topic `/localizer_node/gnss_pose` trong rosbag **rất gần đáp án**: chỉ nội suy nó đã vượt xa baseline (1.31 / 0.57).
2. Baseline của TA dùng **sai tỉ lệ point cloud** (`ply_scale = 3`, đúng phải ≈ **9**) nên NDT trôi tới ~100 m.
   Sửa tỉ lệ + độ phân giải NDT 4 m thì NDT ổn định, nhưng **vẫn kém chính xác hơn GNSS** nên ghép vào làm điểm xấu đi.
3. Điểm tốt nhất đến từ **bộ lọc Kalman + RTS smoother với mô hình chuyển động của xe (CTRV)**, tham số nhiễu ước lượng
   từ chính dữ liệu, kèm ước lượng **độ lệch cố định của yaw GNSS** (−0.42° ở Track01, +0.65° ở Track02).
4. Dùng các file "thăm dò" để **tách điểm thành phần vị trí và phần yaw**: Track01 ≈ 0.91 m + 1.77°, Track02 ≈ 0.23 m + 0.88°.
   Ba cách ước lượng độc lập cho cùng kết quả; mô hình dự đoán điểm `phys_yawb_1` = 1.25339, thực tế 1.25338.
5. Thời gian ảnh–GNSS đã đồng bộ (Δt tối ưu ≈ 0), không có lệch ngang; **khoảng cách tới hạng 1 ≈ đúng bằng phần lỗi yaw**.

## Mục lục

| File | Nội dung |
|---|---|
| [01-chuan-bi.md](01-chuan-bi.md) | Thông tin cuộc thi, cách chấm, tải dữ liệu, Docker, build |
| [02-phan-tich-du-lieu.md](02-phan-tich-du-lieu.md) | Rosbag, GNSS, init_guess, point cloud (hệ trục, tỉ lệ), bản đồ, IMU |
| [03-thi-nghiem-ndt.md](03-thi-nghiem-ndt.md) | Chạy baseline, sửa `localization.cpp`, các thí nghiệm NDT (×2…×10, độ phân giải 4/8 m) |
| [04-cac-lan-nop-kaggle.md](04-cac-lan-nop-kaggle.md) | **Từng lần nộp**: cách tạo, khác gì, vì sao, điểm, kết luận |
| [05-phan-tich-loi.md](05-phan-tich-loi.md) | Tách điểm thành lỗi vị trí / lỗi yaw bằng các file thăm dò |
| [06-nhan-xet.md](06-nhan-xet.md) | Những điều nhận ra, cái gì hiệu quả / không, sai lầm, rủi ro, hướng tiếp theo |
| [07-tai-tao.md](07-tai-tao.md) | Cách tạo lại **từng file đã nộp** (đã kiểm tra: 19/19 file trùng khớp từng byte) |

## Cấu trúc thư mục

```
docs/nhat-ky/
├── README.md, 01-…07-*.md          tài liệu
├── submissions/
│   ├── track1/*.csv                12 file đã nộp Track01 (đúng bản đã nộp)
│   └── track2/*.csv                 7 file đã nộp Track02
└── data/
    ├── kaggle_submissions.csv       lịch sử nộp bài lấy từ Kaggle API (thời gian, tên file, điểm, trạng thái)
    ├── file_differences.txt         chênh lệch vị trí / yaw giữa các cặp file liên tiếp
    ├── probe_analysis.txt           kết quả tách lỗi (tools/analyze_probes.py)
    ├── gnss_imu_analysis.txt        thống kê GNSS / IMU / init_guess (tools/analyze_gnss_imu.py)
    ├── ground_scale.txt             chiều cao mặt đường trong point cloud → tỉ lệ (tools/ground_scale.py)
    ├── frame_alignment_check.txt    thử đặt point cloud vào bản đồ với nhiều tỉ lệ (tools/check_frame_alignment.py)
    ├── rts_smoother_output.txt      tham số nhiễu ước lượng bởi bộ lọc Kalman (tools/rts_smoother.py)
    ├── ndt_correction_stats.txt     thống kê hiệu chỉnh của NDT trong từng thí nghiệm
    ├── ndt_debug/*.csv              dữ liệu từng frame của các thí nghiệm NDT (dùng để tạo lại file fusion)
    └── baseline_partial/            kết quả baseline TA chạy dở trên máy (đã trôi xa) – làm bằng chứng
```
