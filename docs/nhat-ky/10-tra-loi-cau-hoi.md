# 10 – Trả lời câu hỏi trong brief (22/10 → 29/10)

Theo `docs/brief_claude_code.pdf` (7 trang đầu = brief, mục 3 = bảng câu hỏi, mục 7 = nhiệm vụ T0–T13).
Luật: không dò bảng điểm; file nộp = output trực tiếp của pipeline; mỗi thí nghiệm đổi đúng 1 tham số, ghi giả thuyết trước;
không tự nộp Kaggle (đề xuất ≤ 3 file / đợt). Python chạy trong Docker `sdc-reg`. Mỗi nhiệm vụ: câu hỏi → cách làm → lệnh →
số liệu → kết luận (giả thuyết nào xác nhận / bác bỏ). Số liệu thô: `data/`, hình: `fig/`.

Yêu cầu thêm của người dùng (22/10): tìm cách xử lý các tình huống có sai số lớn bất thường (xe chậm / khởi hành, xe nhanh
> 12 m/s, khúc cua – xem mục "Tình huống sai số lớn" ở T3) và cải thiện độ tin cậy của phép khớp.

## T0 – Sao lưu file ngoài git

**Câu hỏi (brief tr. 27, "vai trò lượt NDT cũ"):** file nào pipeline cần mà không có trong git, mất thì sao?

**Cách làm:** chép vào `~/SDC-midterm01/backup/2026-10-22/` (ngoài repo) kèm `SHA256SUMS`, kiểm tra lại bằng `sha256sum -c`.

```bash
B=backup/2026-10-22; R=midterm01/src/localization/result
cp -a $R/c3s08_* $R/phys_yawb_1.csv $R/rts_heading_2.csv $B/result/; cp -a $R/chunks $B/result/
cp -a data/Track{1,2}/map_voxel_0.3m.pcd → $B/maps/Track{1,2}_map_voxel_0.3m.pcd
(cd $B && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS && sha256sum -c SHA256SUMS)
```

| Nhóm | Nội dung | Ghi chú |
|---|---|---|
| `result/c3s08_Track1_*` (6 file) | lượt NDT C++ trên `3cameras_ply`, tỉ lệ 0.8 | z / roll / pitch cho GICP Track01 |
| `result/chunks/` (60 file) | `c3s08` (6), `c3s085` (8), `c3s08T2` (12), `c3s10` (14), `c3s10T2` (20) | `c3s10T2` chỉ có dạng chunk (không có file gộp) – z / roll / pitch Track02 |
| `phys_yawb_1.csv`, `rts_heading_2.csv` | prior GNSS + Kalman/RTS | đầu vào pipeline sạch |
| `maps/Track{1,2}_map_voxel_0.3m.pcd` | bản đồ voxel 0.3 m | dựng lại được bằng `tools/map_voxel.py` |

Tổng 69 file, 87 MB, kiểm tra checksum: **OK**. Danh sách + checksum: `data/backup_2026-10-22_SHA256SUMS.txt`.
**Thiếu:** không có file nào thiếu. Brief chép vào `docs/brief_claude_code.pdf`.
**Rủi ro còn lại:** `c3s08` chạy với prior `yawproj_v1_1.csv` (yaw là tổ hợp chọn theo bảng điểm) → z/roll/pitch có phụ thuộc
gián tiếp; T7 sẽ thay bằng nguồn sạch.

## T1 – Điểm file sạch: dự đoán và thực tế

**Câu hỏi (tr. 41, "tự tính lại kết quả, so với Kaggle"):** không có đáp án thì dự đoán điểm thế nào, và có khớp không?

**Cách làm:** khi hai file có cùng yaw, theo bất đẳng thức tam giác điểm chênh nhau không quá RMS độ lệch vị trí giữa chúng:
|S_mới − S_cũ| ≤ RMS(Δp) + 0.2 · RMS(Δyaw). Lấy file đã có điểm 5 chữ số cùng phương pháp làm mốc (`cfz1_tau7` 0.78914,
`cfz2_tau15` 0.27654). Cận này chỉ dùng hiệu giữa hai file của chính pipeline, không dùng bảng điểm để suy đáp án.
Thêm khoảng dự đoán "kinh nghiệm" đã ghi ngày 21/10 (CLAUDE.md).

| Track | File | Lệch so với mốc (vị trí / yaw) | Cận chắc chắn | Dự đoán 21/10 | Thực tế (Kaggle cắt 2 chữ số) |
|---|---|---|---|---|---|
| 01 | `clean_cfz1_tau7` | 0.101 m / 0.000° | 0.688–0.891 | 0.78–0.80 | **0.80** (0.800–0.809) ✅ |
| 01 | `if_iso_1` | 0.286 m / 0.000° | 0.503–1.075 | 0.79–0.82 | 0.84 ❌ (kém hơn dự đoán) |
| 01 | `if_aniso_1` | 0.321 m / 0.000° | 0.468–1.110 | 0.80–0.83 | 0.87 ❌ (kém hơn dự đoán) |
| 02 | `clean_cfz2_tau15` | 0.054 m / 0.015° | 0.219–0.334 | ~0.28 | **0.28** ✅ |
| 02 | `if_iso_2` | 0.103 m / 0.015° | 0.171–0.382 | 0.28–0.30 | 0.30 ✅ |
| 02 | `if_aniso_2` | 0.088 m / 0.015° | 0.186–0.368 | 0.28–0.30 | 0.30 ✅ |

**Kết luận:**
- Mọi điểm thật nằm trong cận chắc chắn, nhưng cận quá rộng (±0.1–0.3) để chọn file → chỉ dùng để loại file chắc chắn tệ.
- Dự đoán kinh nghiệm đúng thứ tự (đối chứng < iso < aniso) và đúng Track02; sai mức độ ở Track01: bộ ghép mới kém hơn mình nghĩ
  0.02–0.04 → đánh giá quá cao lợi ích của việc "làm mượt toàn cục" (giả thuyết của §13.2 bị bác bỏ).
- **Bài chấm hiện tại:** Track01 `clean_cfz1_tau7` (0.80), Track02 `clean_cfz2_tau15` (0.28). **Người dùng cần vào Kaggle →
  Submissions → tick "Use for Final Score" cho 2 file này** (làm tay trên web; đổi lại nếu T6 có file tốt hơn).

## T2 – "Point cloud hoàn hảo": sai số do AI dựng 3D hay do thuật toán khớp?

**Câu hỏi (chat; tr. 14 "scale gây sai số gì / bao nhiêu"; tr. 42 "tại sao lệch nhiều"):** tách sai số đầu vào (point cloud do
mô hình AI dựng) khỏi sai số thuật toán (GICP).

**Giả thuyết trước khi chạy (brief 6.1):** (H1) GICP trên point cloud hoàn hảo gần như không sai; (H2) nhiễu ngẫu nhiên theo độ
sâu ít hại, lỗi **có hệ thống** (tỉ lệ, méo theo khoảng cách, gốc camera) mới tạo độ lệch cỡ thật; (H3) lỗi tỉ lệ / gốc camera tái
tạo được độ lệch trung bình đo thật (+0.17 m dọc, −0.14 m ngang).

**Cách làm (`tools/synthetic_gicp.py`):** 200 frame rải đều mỗi track. Point cloud tổng hợp = điểm của chính bản đồ LiDAR quanh
pose "thật" (prior Kalman + z/roll/pitch của lượt NDT), trong vùng nhìn của 3 camera (góc −116°…+97° đo từ `3cameras_ply`,
tầm ≤ 40 m), lọc che khuất thô (mỗi ô 1°×1° giữ điểm gần nhất ± 1 m), lấy mẫu lại cho khớp phân bố khoảng cách của point cloud
thật cùng frame (trung vị 7.5 m). Khớp bằng đúng cấu hình GICP của pipeline. (a) khởi đầu lệch 0.5 m dọc / 0.3 m ngang / 2°;
(b) thêm lỗi giả lập, khởi đầu đúng; (c) point cloud thật (lượt 1 của pipeline, cùng frame – có lẫn lỗi GNSS).

```bash
docker run --rm -u $(id -u):$(id -g) -v ~/SDC-midterm01:/w -w /w/midterm01 sdc-reg python3 tools/synthetic_gicp.py 1 \
  --data /w/data --prior $R/clean_prior_1.csv --pose-source c3s08 --real-debug $R/clean_gicp_p1_Track1_debug.csv
# Track02: --prior $R/clean_cfz2_tau15.csv --pose-source c3s10T2 --real-debug $R/clean_gicp_p1_Track2_debug.csv
```

Sai số theo hệ xe (m, độ); "mean" = độ lệch có hệ thống, "rms" = tổng. Track01 / Track02:

| Trường hợp | hội tụ % | dọc mean | dọc rms | ngang mean | ngang rms | yaw rms |
|---|---|---|---|---|---|---|
| Point cloud hoàn hảo, khởi đầu đúng | 100 / 100 | +0.002 / +0.001 | 0.004 / 0.007 | −0.003 / −0.005 | 0.004 / 0.008 | 0.01 / 0.02 |
| (a) hoàn hảo, khởi đầu lệch 0.5/0.3 m, 2° | 100 / 100 | +0.003 / +0.002 | 0.005 / 0.007 | −0.003 / −0.005 | 0.004 / 0.008 | 0.01 / 0.02 |
| (b) nhiễu độ sâu ngẫu nhiên 2 % | 100 / 99 | +0.006 / +0.010 | 0.014 / 0.026 | +0.006 / −0.002 | 0.020 / 0.029 | 0.05 / 0.08 |
| (b) nhiễu độ sâu ngẫu nhiên 5 % | 97 / 94 | +0.003 / +0.011 | 0.028 / 0.051 | +0.016 / +0.010 | 0.043 / 0.075 | 0.10 / 0.18 |
| (b) tỉ lệ ×0.97 | 99.5 / 94.5 | **+0.331 / +0.288** | 0.357 / 0.338 | +0.080 / −0.149 | 0.236 / 0.243 | 0.26 / 0.42 |
| (b) tỉ lệ ×1.03 | 98.5 / 96 | **−0.309 / −0.255** | 0.336 / 0.314 | −0.053 / +0.146 | 0.239 / 0.242 | 0.23 / 0.42 |
| (b) tỉ lệ ×1.05 | 97.5 / 93 | −0.475 / −0.371 | 0.525 / 0.482 | −0.078 / +0.351 | 0.561 / 0.479 | 0.45 / 0.58 |
| (b) méo độ sâu +0.2 %/m (5 % ở 25 m) | 97.5 / 94.5 | −0.336 / −0.238 | 0.404 / 0.347 | −0.109 / +0.243 | 0.431 / 0.367 | 0.58 / 0.62 |
| (b) gốc camera lệch 0.3 m tới trước | 100 / 100 | −0.297 / −0.298 | 0.297 / 0.298 | 0.00 / 0.00 | 0.005 / 0.008 | 0.01 / 0.02 |
| (b) gốc camera lệch 0.3 m sang trái | 100 / 100 | 0.00 / 0.00 | 0.007 / 0.007 | −0.297 / −0.303 | 0.297 / 0.304 | 0.01 / 0.02 |
| (c) point cloud thật `3cameras_ply` | 76 / 71.5 | **+0.245 / +0.253** | 0.871 / 0.787 | **−0.196 / −0.283** | 0.810 / 0.763 | 2.74 / 2.87 |

Hình: `fig/t2_synthetic.png`. Số liệu: `data/t2_synthetic_track{1,2}.csv` (+ `_frames.csv` từng frame).

**Kết luận:**
- **H1 xác nhận.** Trên point cloud hoàn hảo GICP sai ~**5–8 mm**, hội tụ 100 % kể cả khi khởi đầu lệch 0.5 m / 2° → **sai số của
  thuật toán khớp gần như bằng 0**; khởi đầu từ prior (~0.9 / 0.23 m) không phải vấn đề.
- **H2 xác nhận.** Nhiễu ngẫu nhiên 5 % độ sâu chỉ gây 0.03–0.08 m. Lỗi **có hệ thống** mới gây sai số cỡ thật: tỉ lệ sai 3 % →
  ~0.3 m lệch dọc; méo độ sâu theo khoảng cách → 0.35–0.43 m.
- **H3 xác nhận một phần.** Độ lệch trung bình thật (+0.25 m dọc, −0.20 / −0.28 m ngang) tái tạo được bằng tỉ lệ nhỏ hơn thật
  ~2–3 % (dấu dọc khớp: tỉ lệ < 1 → lệch dọc dương) **hoặc** gốc camera của point cloud lệch ~0.25 m về sau và ~0.2–0.3 m sang
  phải so với điểm tham chiếu của xe. Hai giả thuyết này chưa tách được (T7 đo chiều cao camera độc lập sẽ giúp).
- **Point cloud thật sai hơn hẳn mọi lỗi giả lập đơn lẻ:** ở Track02 (lỗi GNSS chỉ ~0.23 m) độ sửa từng frame vẫn 0.79 / 0.76 m
  và yaw 2.9° → ~0.75 m mỗi frame là do point cloud. Yaw thật sai 2.7–2.9° trong khi mọi lỗi giả lập ≤ 0.6° → point cloud ảnh bị
  méo hình dạng thay đổi theo frame, không chỉ sai tỉ lệ.
- **Trả lời câu hỏi 6.1:** sai số còn lại **đến từ point cloud do AI dựng (đầu vào), không phải từ thuật toán khớp** (thuật toán
  đóng góp < 1 %). Thay thuật toán khớp (NDT / GICP / point-to-plane) không thể cải thiện nhiều; cần (1) sửa phần **có hệ thống**
  của point cloud (tỉ lệ, gốc camera → T4, T7) và (2) giảm trọng số các frame / vùng méo nặng (độ tin cậy → T3).
- Giới hạn: point cloud tổng hợp lấy từ bản đồ LiDAR (có thể có điểm camera không thấy, che khuất xử lý thô), "sự thật" là prior
  Kalman – đủ cho câu hỏi tách nguồn, không dùng để đánh giá vị trí tuyệt đối.
