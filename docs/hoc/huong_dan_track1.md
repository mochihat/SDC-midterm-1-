# Từ code mẫu của TA đến kết quả Track 01 – đổi gì và vì sao

Tài liệu học, viết cho người mới. Mỗi bước ghi: **đổi gì**, **vì sao đổi**, **điểm Kaggle** trước/sau (điểm thấp hơn = tốt hơn).
Bản sao học nằm trong `hoc/ws/` (code C++ của TA, commit `65d10cb`). Kết quả cuối là **pipeline sạch** của nhóm.

> **Quan trọng, đọc trước:** chỉ hai bước đầu (tỉ lệ và ô NDT) là sửa C++. Phần lớn điểm đến từ các công cụ Python
> trong `tools/`, chạy ngoài container bằng Docker. Và pipeline cuối **không hoàn toàn nhân quả**: dùng bộ làm mượt
> hai chiều (RTS). Track 01 cho phép điều này, nhưng Track 03 thì không.

---

## Bảng tổng quan

| # | Bước | Đổi gì | Điểm sau bước | Loại |
|---|---|---|---|---|
| 0 | Code mẫu | – | **602.39** (chạy mặc định, trôi) | – |
| 1 | Tỉ lệ point cloud | `ply_scale_` 3 → 9 | (chưa nộp riêng) | C++ |
| 2 | Ô NDT | `ndt_resolution_` 8 → 4 m | (chưa nộp riêng) | C++ |
| 3 | Điểm xuất phát | mỗi frame bắt đầu từ GNSS, không từ frame trước | (thử nghiệm) | C++ |
| 4 | Chỉ GNSS | nội suy GNSS cho từng frame | **1.31** | Python |
| 5 | Làm mượt GNSS | Kalman CTRV + RTS | **1.25** | Python |
| 6 | Yaw từ gyro | bộ lọc bù gyro + hướng chạy (τ 7 s) | **0.79** | Python |
| 7 | GICP | khớp point cloud 3 camera vào bản đồ, 2 lượt | **≈ 0.93 → 0.79** | Python |
| 8 | Tầm 20 m | bỏ điểm xa hơn 20 m | **0.63** | Python |
| 9 | Khớp bản đồ (CSM) | sửa vị trí dọc đường | **0.55** | Python |
| 10 | Yaw theo bản đồ | yaw từ GICP cho phần chậm | **0.51** (**kết quả cuối**) | Python |

---

## Bước 0 – Code mẫu chạy mặc định

- **Làm gì:** chạy `run_baseline.sh` hoặc `hoc/ws` như hướng dẫn.
- **Vì sao trôi:** `ply_scale_ = 3`, ô NDT 8 m, và mỗi frame bắt đầu từ pose **frame trước**. Sai số cộng dồn.
- **Kết quả:** nộp được 602.39 (quỹ đạo lệch hàng trăm mét).

## Bước 1 – Sửa tỉ lệ point cloud (C++)

- **Đổi:** `include/localization/localization.h`, dòng `ply_scale_ = 3.0` → `9.0`.
- **Vì sao:** point cloud LoGeR không có đơn vị. Mặt đường nằm 0.18 đơn vị dưới camera, mà camera thật cao 1.646 m, nên tỉ lệ đúng ≈ 1.646 / 0.18 ≈ 9. Với ×3, cả cảnh co lại và NDT bám vào cấu trúc sai.
- **Kiểm chứng:** nhật ký `docs/nhat-ky/02` mục 3 (đo độ cao mặt đường trên 21 frame).

## Bước 2 – Ô NDT 8 m → 4 m (C++)

- **Đổi:** `ndt_resolution_ = 8.0` → `4.0`.
- **Vì sao:** point cloud ×9 chỉ phủ ~27 m, nên ô 8 m quá to: mặt đường, tường và cây gộp chung một ô, không còn chi tiết để phân biệt vị trí. Ô 4 m giữ được hình dạng.
- **Kiểm chứng:** nhật ký `docs/nhat-ky/03` mục 4 (độ sửa trung vị 1.55 m → 0.23 m, Track 02).

## Bước 3 – Mỗi frame bắt đầu từ GNSS (C++)

- **Đổi:** thay `pose` (frame trước) bằng GNSS của frame hiện tại: thêm `LoadGnssPoses` / `GnssPoseAt` và dùng biến `start` thay cho `pose` ở `CropSubmap`, `candidate` và `AlignNDT` (đã hướng dẫn từng dòng trong phần trò chuyện).
- **Vì sao:** sai số của frame trước không cộng dồn được vào frame sau.
- **Lưu ý:** đây là bước học. Pipeline cuối **không** dùng NDT từng frame; nó dùng GICP và các công cụ ở bước 4–10.

## Bước 4 – Chỉ dùng GNSS (Python)

- **Làm gì:** `processing_codes/gnss_to_csv.py` nội suy tuyến tính GNSS (4 Hz) tới thời điểm từng frame.
- **Vì sao:** GNSS cùng hệ tọa độ với bản đồ và đã gần đáp án. Nộp thử để đo: **1.31** (baseline 1.79).
- **Kết quả nhóm:** `docs/nhat-ky/submissions/track1/gnss_1.csv`.

## Bước 5 – Làm mượt GNSS bằng Kalman CTRV + RTS (Python)

- **Làm gì:** `tools/rts_smoother.py`. Mô hình xe đi theo hướng mũi xe (CTRV). Bốn tham số nhiễu chọn bằng **maximum likelihood trên chính dữ liệu GNSS** (không dùng điểm Kaggle).
- **Vì sao:** GNSS Track 01 giật (0.142 m); mô hình chuyển động loại bỏ nhiễu tốt hơn lọc Gauss.
- **Điểm:** 1.25 (vị trí chỉ đổi 0.1 m).
- **Lưu ý nhân quả:** RTS dùng cả frame tương lai (làm mượt hai chiều). Chấp nhận được cho Track 01, không cho Track 03.

## Bước 6 – Yaw từ gyro (Python)

- **Làm gì:** `tools/yaw_fusion.py --gyro-axis z --tau 7`. Gyro cho phần thay đổi nhanh, hướng chạy cho phần trung bình.
- **Vì sao:** yaw của đáp án là **yaw thân xe**, không phải hướng chuyển động. Gyro đo đúng điều đó. Thử bù trễ hướng chạy thì điểm lại xấu đi.
- **Điểm:** 0.93 → **0.79** (yaw 1.56° → 0.87°). τ = 7 s chọn theo điểm (ghi rõ trong báo cáo).

## Bước 7 – GICP với point cloud 3 camera (Python)

- **Làm gì:** `tools/gicp_refine.py` (GICP của `small_gicp`), bản đồ voxel 0.3 m, tỉ lệ theo mặt đường (1.646 m / độ cao đo được, trung vị 57 frame), **2 lượt**, sau đó `fuse_to_csv.py --demean`.
- **Vì sao:** NDT chậm hơn ~200 lần và kém chính xác hơn GICP trên cùng dữ liệu (0.836 so với 0.803 m).
  - **2 lượt, không hơn:** lượt 5 xấu (0.80 m) vì point cloud méo làm cực tiểu của GICP lệch khỏi vị trí thật.
  - **De-mean:** GICP có lệch cố định (+0.17 m dọc, −0.14 m ngang). Chỉ lấy phần dao động, còn phần trung bình giữ theo GNSS.
- **Điểm:** ≈ 0.93 sau 2 lượt và de-mean; với yaw gyro ở bước 6 là **0.79**.

## Bước 8 – Tầm 20 m (Python)

- **Làm gì:** `gicp_refine.py --max-range 20` (thay vì 40).
- **Vì sao:** độ sâu từ ảnh méo tăng theo khoảng cách. Bỏ điểm xa làm GICP sửa đúng hơn (nhật ký `docs/nhat-ky/10` T4: nhiễu dọc 0.67 → 0.56 m, nhiều frame hợp lệ hơn).
- **Điểm:** 0.80 → **0.63**. Đây là bước có lợi nhất sau GNSS.

## Bước 9 – Khớp bản đồ CSM (Python)

- **Làm gì:** `tools/csm_fuse.py`, khớp lưới tương quan với bản đồ quanh quỹ đạo, rồi làm mượt có trọng số.
- **Vì sao:** GICP chỉ nhìn được 1–2 m; khớp lưới nhìn được xa hơn và sửa vị trí dọc đường.
- **Điểm:** 0.62 → **0.55**.

## Bước 10 – Yaw theo bản đồ (Python)

- **Làm gì:** `tools/raw_gicp_at_poses.py` (GICP của point cloud LoGeR tại các pose) + `tools/map_yaw_fuse.py` (gyro cho phần nhanh, yaw GICP cho phần chậm, làm mượt Gauss 8 s).
- **Vì sao:** phần chậm của yaw gyro còn sai khoảng 0.7°; yaw từ bản đồ bù phần đó.
- **Lưu ý trung thực:** σ = 8 s được chọn **sau khi so với một file dò bảng điểm** (nhật ký `docs/nhat-ky/12` §10). Phải ghi rõ trong báo cáo.
- **Điểm:** 0.55 → **0.51**. Đây là bài chấm sạch tốt nhất của Track 01.

---

## Cách chạy lại (không cần làm từng bước)

Trên máy, ngoài container, từ `~/SDC-midterm01`:

```bash
bash midterm01/tools/run_clean_pipeline.sh      # bước 5–7 + yaw: tạo clean_cfz1_tau7 (điểm ~0.80)
```
Script này cần sẵn `phys_yawb_1.csv` (bước 5) và file NDT C++ `c3s08` (bước 1–2). Các bước 8–10 là các lệnh riêng,
xem `docs/nhat-ky/12-track3-csm-23-10.md` §7 và §10 (`csm_fuse.py`, `map_yaw_fuse.py`).

## Những gì phải nói thật khi nộp báo cáo

- Tham số τ, trục gyro, số lượt GICP, σ yaw bản đồ đều **chọn theo điểm Kaggle** (chỉnh tham số bình thường, TA cho phép).
- Pipeline dùng **RTS** (làm mượt hai chiều): không nhân quả. Chỉ Track 03 bắt buộc nhân quả.
- Bài chấm cuối phải được chọn bằng tay trên Kaggle ("Use for Final Score"), vì Kaggle mặc định chọn theo điểm public.
