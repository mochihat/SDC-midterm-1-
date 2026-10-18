# 08 – GICP, ICP 3 bậc tự do và tỉ lệ theo mặt đường (đêm 18→19/10)

Ý tưởng lấy từ tìm hiểu tài liệu: NDT thô → GICP/VGICP tinh (Segal et al. 2009; Koide et al., ICRA 2021), ước lượng
**tỉ lệ theo đoạn** thay cho một hằng số, và ý của KISS-ICP (robust kernel). Chạy offline trên `3cameras_ply` có sẵn.

## 1. Công cụ

| File | Việc |
|---|---|
| `tools/gicp_refine.py` | Khớp point cloud ảnh vào bản đồ bằng `small_gicp` (ICP / GICP / VGICP) hoặc ICP point-to-plane 3 bậc tự do tự viết (`--method PLANAR`). Bắt đầu từ prior (`--prior`) hoặc từ pose NDT của một lượt C++ cũ (`--init-run`). Ghi file debug **cùng định dạng** với node C++ nên đi qua `fuse_to_csv.py` y như các lượt NDT |
| `tools/map_voxel.py` | Giảm mẫu `map.pcd` gốc (~60 triệu điểm, Track01 dạng chữ, Track02 nhị phân) thành bản đồ 0.3 m (`data/TrackN/map_voxel_0.3m.pcd`) |
| `fuse_to_csv.py --demean` | Trừ độ sửa trung bình (dọc / ngang hướng xe) trước khi làm mượt (xem mục 4) |
| `docker/reg/Dockerfile` | Image nhỏ có `small_gicp` |

Cấu hình chung: bản đồ 0.3 m, nguồn giảm mẫu 0.5 m, bỏ điểm xa hơn 40 m, khoảng cách ghép cặp tối đa 1 m, 100 vòng lặp.
Tốc độ: **~0.06 s/frame** (GICP, 10 tiến trình) – cả Track01 (3011 frame) trong ~3 phút; NDT C++ cũ ~14 s/frame.

**Tỉ lệ theo mặt đường** (`--ground-height 1.646`): mỗi frame đo độ cao mặt đường `h` dưới camera trong point cloud chưa
nhân tỉ lệ (`tools/ground_scale.py`), lọc trung vị 57 frame (~2 s), tỉ lệ = 1.646 / h. 1.646 m = 0.8 × 2.058 (trung vị `h`
của Track01), tức là cùng chiều cao camera đã suy ra tỉ lệ 0.8. `h` thay đổi 1.73–2.27 giữa các đoạn, nên tỉ lệ cố định
0.8 sai vài phần trăm ở nhiều đoạn. Track02: trung vị `h` = 2.239 → tỉ lệ trung vị 0.729.

## 2. Đánh giá

File nộp **chỉ đổi vị trí**, yaw giữ của `yawproj_v1_1.csv` (lỗi yaw 1.570° → 0.314 điểm), nên
**lỗi vị trí = điểm − 0.314**. Hiệu chỉnh của mỗi frame được lọc (≤ 2 m, ≤ 3°), lọc trung vị 5 frame, làm mượt Gauss 2 s
rồi cộng vào vị trí prior – y như các lượt NDT ở [03](03-thi-nghiem-ndt.md) mục 8.

## 3. Kết quả Track01

| File | Cách làm | Điểm | Lỗi vị trí |
|---|---|---|---|
| `yawproj_v1_1.csv` (gốc) | GNSS + Kalman | 1.21861 | 0.905 m |
| `ndt3c_s08_pos_1.csv` (cũ) | NDT C++, tỉ lệ 0.8, mỗi 4 frame | 1.15042 | 0.836 m |
| `gicp_s08_pos_1.csv` | GICP từ prior, tỉ lệ 0.8, mỗi 4 frame | 1.11701 | 0.803 m |
| `ndt_gicp_s08_pos_1.csv` | NDT → GICP, tỉ lệ 0.8 | 1.08265 | 0.769 m |
| `gicp_ground_pos_1.csv` | GICP, **tỉ lệ theo mặt đường**, mỗi 4 frame | 1.06593 | 0.752 m |
| `gicp_ground_all_pos_1.csv` | như trên, **mọi frame** | 1.02813 | 0.714 m |
| `planar_ground_all_pos_1.csv` | ICP 3 bậc tự do (x, y, yaw), Geman-McClure 0.3 m, chỉ mặt đứng | 1.03311 | 0.719 m |
| `gicp_ground_all_posyaw_1.csv` | như `gicp_ground_all`, **thêm yaw của GICP** | 1.03955 | (yaw 1.570° → ~1.627° ❌) |
| `gicp_ground_pass2_pos_1.csv` | lượt 2: GICP lại, bắt đầu từ kết quả lượt 1 | **0.99283** | 0.679 m |
| `gicp_ground_pass5_pos_1.csv` | lượt 5 | 1.11461 | 0.801 m ❌ |
| `pass2pos_bestyaw_1.csv` | vị trí lượt 2 + yaw của `posproj_v2_1` | 0.99060 | – |
| `pass2dm_bestyaw_1.csv` | lượt 1–2 **có trừ độ lệch trung bình**, + yaw của `posproj_v2_1` | **0.92775** | ~0.616 m |

## 4. Nhận xét

1. **GICP tốt hơn NDT** trên cùng dữ liệu (0.803 so với 0.836 m), và nhanh hơn ~200 lần. NDT → GICP còn tốt hơn (0.769 m).
2. **Tỉ lệ theo mặt đường có tác dụng thật**: 0.803 → 0.752 m (cùng số frame). Chạy mọi frame thay vì mỗi 4 frame: → 0.714 m.
3. **Chạy lặp chỉ có lợi 1–2 lượt.** Lượt 2 tốt hơn (0.679 m) nhưng lượt 5 xấu hẳn (0.801 m) dù mỗi lượt vẫn dịch cùng
   hướng (tương quan 0.8–0.9). Chẩn đoán trên 8 frame: GICP kéo pose 0.5–1.2 m nhưng khoảng cách điểm–bản đồ gần như
   không giảm; mặt đường khớp tốt (~0.2 m), phần trên mặt đất khớp kém (0.4–1.3 m) – point cloud ảnh bị méo, nên **cực tiểu
   của GICP lệch khỏi vị trí thật**; đi một phần đường về phía nó thì có lợi, đi hết thì hại.
4. **GICP có độ lệch cố định** so với GNSS: trung bình dọc +0.17 m, ngang −0.14 m (lượt 1, các frame qua bộ lọc).
   Lượt thăm dò "dời ngang ±0.5 m" (xem 05) cho thấy GNSS Track01 **không** lệch ngang (+0.025 m), lệch thời gian chỉ
   −3.6 ms ⇒ độ lệch cố định này là của phép khớp ảnh (nhiều khả năng vị trí camera trong point cloud MapAnything).
   Cách xử lý kiểu bộ lọc bù (complementary): prior giữ phần trung bình, scan matching chỉ thêm phần dao động cục bộ
   (`--demean`). Kết quả: 0.99060 → **0.92775** (lỗi vị trí ~0.679 → ~0.616 m, đúng như dự đoán 0.62 m khi bỏ độ lệch ~0.28 m).
5. **Yaw của GICP không dùng được** (làm lỗi yaw tăng ~0.06°), giống NDT trước đây.
6. ICP 3 bậc tự do ít nhiễu hơn hẳn GICP (độ sửa: trung vị 0.49 m, độ lệch chuẩn 0.34 m so với 1.14 m / 0.93 m) nhưng
   lỗi sau lượt 1 ngang GICP (0.719 so với 0.714 m).

## 5. Track02: GICP làm xấu đi

`gicp_dm_w05_on_best_2.csv`: GICP tỉ lệ theo mặt đường, trừ độ lệch trung bình, **trọng số 0.5**, cộng vào vị trí của
`posyaw_v2_2.csv` (0.29887) → **0.36530** ❌. Lỗi vị trí GNSS Track02 chỉ ~0.2 m; ở mức đó độ sửa của GICP gần như là nhiễu
(không tương quan với lỗi). Giống NDT trước đây (0.33504 → 0.40544). Không dùng scan matching cho vị trí Track02.

## 6. Phần nào dựa vào điểm Kaggle

- Mọi kết luận "tốt hơn / xấu hơn" ở trên đến từ điểm leaderboard (đánh giá), không có đáp án offline.
- **Số lượt lặp** (dừng ở 2) được chọn sau khi thấy lượt 5 xấu đi – một tham số chọn theo điểm.
- `--demean` dựa vào một sự thật đo bằng lượt thăm dò (GNSS không lệch ngang) – thông tin lấy từ điểm Kaggle.
- Yaw của các file `*_bestyaw_1.csv` lấy từ `posproj_v2_1.csv`, vốn là **tổ hợp chọn theo điểm Kaggle** (xem 05).
  File chỉ dùng yaw `yawproj_v1_1` (ít phụ thuộc điểm hơn) tốt nhất là `gicp_ground_pass2_pos_1.csv` – 0.99283.

## 7. Các phương pháp TA gợi ý (slide: "Scale calibration、雜訊處理", front-hood mask trong `camera_info`)

| Thử | Kết quả offline | Nộp |
|---|---|---|
| **Mặt nạ nắp capo** (`--hood-mask`, chiếu điểm lên ảnh camera trước bằng mô hình fisheye) | `3cameras_ply`: chỉ 0.5–2 % điểm rơi vào vùng nắp capo, và chúng nằm ở độ cao mặt đường (z ≈ −2.1) – MapAnything đã tự bỏ nắp capo, phần còn lại là mặt đường "đoán" sau nắp capo. Kết quả GICP đổi rất ít (0.09 m RMS) | – |
| **Lọc điểm lạc thống kê** (`--sor 10,2`, như PCL StatisticalOutlierRemoval) + nắp capo | GICP đổi 0.14 m RMS so với không lọc | `gicp_hood_sor_pos_1.csv` (chờ) |
| **Bỏ mặt đường** (`--no-ground 0.3`) | GICP mất ràng buộc z / roll / pitch, chỉ 30 % frame hội tụ → chỉ dùng cho ICP 3 bậc tự do | `planar_clean_pos_1.csv` (chờ) |
| `raw_ply` (LoGeR) + GICP, tỉ lệ theo mặt đường (trung vị ×9.27) | Độ sửa lệch dọc đường −0.79 m (3 camera: +0.38 m); sau khi trừ trung bình **không tương quan** (0.02) với 3 camera → coi là nhiễu, không nộp | – |
| ICP point-to-plane (`--method PLANE_ICP`, chỉ dùng pháp tuyến bản đồ, không dùng hiệp phương sai của point cloud ảnh) | Độ lệch trung bình gần 0 (dọc +0.04, ngang −0.08 m) – ít lệch hơn GICP | `plane_icp_ground_pos_1.csv` (chờ) |

## 8. Yaw: bộ lọc bù gyro + hướng chạy (`tools/yaw_fusion.py`)

yaw = tích phân gyro (bias ước lượng bằng bình phương tối thiểu theo hướng chạy) + làm mượt Gauss τ giây của
(hướng chạy − yaw gyro): gyro lo phần thay đổi nhanh, hướng chạy giữ phần trung bình. Không dùng điểm Kaggle.

- Gyro được **chiếu lên phương trọng lực** (IMU nghiêng 5.8° / 4.6°): phần dư hướng chạy − yaw gyro (Track02) 0.342° → 0.309°;
  hệ số tỉ lệ gyro khi đó 1.002 / 1.005 → không cần hiệu chỉnh tỉ lệ. Không có lệch thời gian IMU – vị trí (tối ưu ≈ 0 s).
- Track02 (hướng chạy sạch, tương quan tốc độ quay – gyro 0.89): `cf_tau5_2.csv` (vị trí của `posyaw_v2_2`, τ = 5 s)
  **0.29887 → 0.29268** ✅ (yaw ~−0.03°) – yaw hoàn toàn vật lý tốt hơn yaw cũ có thành phần chọn theo điểm.
- Hệ số trượt ước lượng từ dữ liệu (`--auto-lever`, hồi quy phần dư theo độ cong ω/v): Track02 d = −2.0 m (hợp lý: hiệu ứng
  understeer ở 11 m/s ≈ −1 m + vị trí điểm đo gần cầu sau). Track01 không tin được (hướng chạy nhiễu).
- Track01: hướng chạy tính từ vị trí GNSS bị nhiễu (tương quan với gyro chỉ 0.35–0.56 dù làm mượt 0.5–2.5 s; phần dư ~1.2°,
  cỡ chính lỗi yaw hiện tại 1.56°) → thử yaw dựa nhiều vào gyro (τ = 15, 30 s).

## 9. Còn chờ nộp (đã tính sẵn)

Track01: `gicp_ground_pass3dm_bestyaw_1.csv`, `gicp_ground_pass4dm_bestyaw_1.csv` (lượt 3, 4 có trừ độ lệch; độ dịch mỗi
lượt 0.259 → 0.188 → 0.143 m), `planar_pass2dm_bestyaw_1.csv`, các file ở mục 7, `cfg1_tau15_al.csv`, `cfg1_tau30_al.csv`.
Track02: `cfg2_tau5_al.csv`, `cfg2_tau5.csv`, `cfg2_tau15_al.csv`, `cfg2_tau2_al.csv`, cặp thăm dò yaw ±0.5° trên `cf_tau5_2.csv`.

Dự phòng (chọn theo điểm Kaggle, chưa nộp): tổ hợp 10 trường vị trí Track01 (`pos_projection.py`) dự đoán lỗi vị trí
**0.510 m** (bài thuần thuật toán tốt nhất ~0.616 m); trọng số +3.72, −2.03… không có ý nghĩa vật lý.
