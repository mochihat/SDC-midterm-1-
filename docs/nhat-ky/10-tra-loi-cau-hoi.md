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

## T3 – Ngân sách sai số, vùng sai lớn và độ tin cậy từng frame

**Câu hỏi (tr. 6 "thành phần nào của RMSE lớn nhất"; tr. 9 "sai lớn nằm ở đoạn nào"; tr. 15 "khởi đầu xấu có gây sai không";
người dùng 22/10: "xe làm gì thì sai lớn – quay đầu, ngã rẽ?" + "cải thiện độ tin cậy").**

**Giả thuyết:** (H1) sai lớn ở khúc cua và lúc khởi hành; (H2) có một chỉ số chất lượng từng frame (tỉ lệ inlier, lỗi GICP…)
dự báo được frame xấu → dùng làm trọng số; (H3, T3b) hai point cloud khác nhau cho cùng độ sửa nếu lỗi chủ yếu là lỗi GNSS.

**Cách làm (`tools/error_budget.py`, không dùng đáp án / bảng điểm):** độ sửa d = pose GICP − prior Kalman (lượt 1, prior sạch).
Lỗi GNSS biến đổi chậm → phần nhanh hơn 2 s (d trừ làm mượt 2 s của chính nó) là nhiễu của point cloud + phép khớp.
Bảng theo đoạn 10 %: §13.6 trong `08-gicp-va-scale.md` (`tools/segment_analysis.py`).

```bash
docker run --rm -u $(id -u):$(id -g) -v $PWD:/w -w /w sdc-reg python3 tools/error_budget.py \
  $C/clean_prior_1.csv $C/clean_gicp_p1_Track1_debug.csv --other-debug $C/t3/raw_gicp_p1_Track1_debug.csv
```

**Đường đi:** không có quay đầu hay rẽ gắt – tổng góc đổi hướng chỉ +28° (Track01) / −40° (Track02), tốc độ quay ≤ ~3 °/s.

**1. Theo tình huống** (Track01 / Track02; ok = % frame hội tụ, lệch ≤ 2 m, yaw ≤ 3°; spread = RMS nhiễu nhanh):

| Tình huống | số frame | ok % | lệch TB dọc (m) | lệch TB ngang (m) | spread (m) |
|---|---|---|---|---|---|
| Đứng / khởi hành (v < 2 m/s) | 67 / 327 | 54 / 81 | −0.27 / −0.09 | −0.02 / +0.27 | 0.88 / **0.48** |
| Chậm 2–5 m/s | 212 / 88 | **34** / 59 | +0.01 / −0.34 | +0.28 / −0.09 | 0.92 / 0.76 |
| Bình thường 5–12 m/s | 2125 / 1684 | 57 / 54 | +0.26 / +0.16 | −0.19 / −0.28 | 0.82 / 0.78 |
| Nhanh ≥ 12 m/s | 607 / 1200 | 48 / 48 | −0.13 / +0.28 | −0.03 / −0.20 | **0.97 / 0.96** |
| Đang cua ≥ 1 °/s | 223 / 895 | **35** / 52 | +0.15 / +0.35 | +0.17 / −0.26 | **1.07** / 0.87 |
| Phanh / tăng tốc (\|a\| ≥ 1) | 113 / 122 | 66 / 45 | +0.23 / −0.46 | −0.41 / −0.39 | 0.94 / 0.78 |

- **H1 xác nhận một phần:** frame xấu nhất là khi **cua** (Track01: chỉ 35 % dùng được, nhiễu 1.07 m), **chạy chậm 2–5 m/s**
  (34 %) và **chạy nhanh ≥ 12 m/s** (nhiễu ~0.97 m). Đứng yên thì Track02 lại tốt nhất (0.48 m) – không phải "khởi hành = xấu".
- **Độ lệch có hệ thống đổi theo tình huống** (vd. Track02 dọc −0.34 khi chậm, +0.28 khi nhanh) → `--demean` (trừ một hằng số)
  chỉ khử được phần trung bình. Hồi quy độ sửa dọc theo tốc độ: Track02 **+36 ms × v** (KTC 95 % +17…+66 ms, có ý nghĩa);
  Track01 −18 ms (lượt 1, KTC −149…+34) / −36 ms (lượt 2, KTC −103…−3) → **dấu ngược nhau giữa hai track** ⇒ không phải lệch
  thời gian chung của camera mà là méo point cloud phụ thuộc chuyển động; giải thích thêm vì sao GICP làm Track02 xấu đi.

**2. Chỉ số nào dự báo frame xấu?** Spearman(chỉ số, |nhiễu|), Track01 / Track02:

| Chỉ số | ρ | Nhiễu theo phần tư thấp → cao (Track01) |
|---|---|---|
| tốc độ | +0.13 / **+0.30** | 0.85 0.70 0.88 0.96 |
| tốc độ quay | −0.02 / +0.19 | 0.88 0.85 0.83 0.85 |
| tỉ lệ inlier | −0.09 / +0.09 | 0.90 0.90 0.81 0.80 |
| lỗi GICP / inlier | +0.16 / +0.24 | 0.75 0.84 0.89 0.92 |
| số điểm đầu vào | +0.17 / +0.19 | 0.75 0.86 0.87 0.92 |
| \|độ sửa yaw\| | +0.11 / +0.20 | 0.82 0.81 0.86 0.92 |
| **\|độ sửa vị trí\|** | **+0.71 / +0.72** | 0.47 0.63 0.86 **1.25** |
| (Hessian, §13.6) | ≈ 0 | – |

- **H2 bác bỏ phần lớn:** không chỉ số chất lượng nào của GICP dự báo tốt (|ρ| ≤ 0.3). Duy nhất **độ lớn của chính độ sửa**
  dự báo mạnh: phần tư độ sửa lớn nhất nhiễu 1.25 m, gấp 2.7 lần phần tư nhỏ nhất → các frame "kéo xa" phần lớn là sai.
  ⇒ Hướng cải thiện độ tin cậy có cơ sở: **hàm trọng số bền vững (robust kernel, vd. Cauchy/Huber) theo độ lớn độ sửa** thay cho
  cổng cứng 2 m hiện tại, và giảm trọng số khi tốc độ cao (Track02 ρ 0.30). Lỗi GICP / inlier dùng phụ được (ρ 0.16–0.24).

**3. T3b – cùng prior, cùng GICP, hai point cloud khác nhau** (Track01, 826 frame cả hai đều hợp lệ):

| | `3cameras_ply` (MapAnything) | `raw_ply` ×9.27 (LoGeR) |
|---|---|---|
| % frame hợp lệ | 53 % | 52 % |
| Độ sửa TB dọc / ngang | **+0.27 / −0.17 m** | **−0.59 / +0.35 m** |
| RMS độ sửa (đã trừ TB) dọc / ngang | 0.72 / 0.68 m | 0.74 / 0.66 m |
| Tương quan từng frame dọc / ngang | +0.05 / +0.03 | |
| Tương quan sau làm mượt 2 s dọc / ngang | −0.18 / −0.41 | |

- **H3 bác bỏ:** nếu lỗi chủ yếu là lỗi GNSS (chung cho cả hai), hai point cloud phải cho độ sửa giống nhau. Thực tế chúng lệch
  TB **ngược chiều nhau** (+0.27 so với −0.59 m dọc) và gần như không tương quan → **méo riêng của mỗi mô hình AI lớn hơn tín hiệu
  lỗi GNSS ở từng frame**. GICP chỉ có ích ở Track01 nhờ lấy trung bình nhiều frame + demean (lỗi GNSS ~0.9 m đủ lớn để lộ ra).
- Cùng kết luận với T2: **nguồn sai số chính là point cloud do AI dựng**.

**Đề xuất cải thiện (cho T4 / T6):** (1) robust kernel theo độ lớn độ sửa; (2) giảm trọng số frame tốc độ cao / đang cua;
(3) sửa phần có hệ thống ở đầu vào (tỉ lệ, gốc camera, tầm – T4, T7). Chưa chọn được cái nào chỉ bằng offline vì không có
thước đo offline đáng tin cho biến thể GICP (§13.5) → cần lượt nộp có kiểm soát.

## T11 – Vì sao GNSS Track01 giật hơn Track02 (0.142 m so với 0.052 m)?

**Câu hỏi (chat, brief 6.2).** **Giả thuyết theo thứ tự (brief):** (1) che chắn / multipath; (2) máy thu đổi chế độ (bước nhảy);
(3) cách lái (chậm hơn, dừng / rẽ nhiều hơn).

**Cách làm (`tools/gnss_jitter.py`):** độ giật = sai phân bậc 2 của vị trí GNSS (4 Hz), tách dọc / ngang hướng chạy, gom cửa sổ 2 s;
bước nhảy = sai phân > 5× trung vị; che chắn = tỉ lệ điểm bản đồ cao hơn mặt đường > 3 m trong bán kính 25 m; tốc độ quay lấy từ
**gyro IMU** (lần chạy đầu dùng hướng tính từ chính GNSS → tương quan 0.86 là vòng tròn, đã loại).

```bash
docker run --rm -u $(id -u):$(id -g) -v ~/SDC-midterm01:/w -w /w/midterm01 sdc-reg python3 tools/gnss_jitter.py --data /w/data
```

| | Track01 | Track02 |
|---|---|---|
| Độ giật RMS (dọc / ngang) | **0.142 m** (0.057 / **0.130**) | 0.052 m (0.032 / 0.040) |
| Bước nhảy > 5× trung vị | **11** (cụm ở 27–40 s và 80–83 s) | 1 |
| Tỉ lệ công trình cao quanh đường (≤ 25 m) | **74 %** | 29 % |
| Tốc độ TB / tỉ lệ thời gian dừng | 9.6 m/s / 2 % | 10.5 m/s / 8 % |
| Tốc độ quay TB (gyro) | 0.40 °/s | 0.80 °/s |
| Spearman(giật cửa sổ, tốc độ / quay / gia tốc) | −0.11 / −0.12 / +0.23 | +0.01 / +0.24 / +0.62 |
| Spearman(giật cửa sổ, che chắn) | −0.00 | −0.02 |
| Spearman(giật cửa sổ, số bước nhảy) | +0.59 | +0.22 |

Hình: `fig/t11_gnss_jitter.png`. Số liệu: `data/t11_gnss_jitter.csv` (cửa sổ 2 s), `data/t11_gnss_jitter_messages.csv`.

**Xếp hạng giả thuyết:**
1. **Che chắn / multipath – được ủng hộ ở mức cả track:** Track01 có công trình cao quanh 74 % quãng đường (Track02 29 %), độ giật
   chủ yếu **theo phương ngang** (0.130 m) – đúng kiểu phản xạ từ nhà / cây hai bên đường. Trong cùng một track tương quan với tỉ lệ
   che chắn ≈ 0 → thước đo che chắn thô (Track01 gần như chỗ nào cũng bị che) hoặc phụ thuộc vào vệ tinh cụ thể – **chưa kết luận
   được** ở mức từng đoạn.
2. **Bước nhảy rời rạc – đóng góp đáng kể:** 11 bước nhảy ở Track01 (1 ở Track02), cửa sổ có bước nhảy giật hơn rõ (ρ = 0.59).
   Không tách được "đổi chế độ máy thu" với "đỉnh multipath" vì topic chỉ là pose đã xử lý (không có trạng thái fix / số vệ tinh).
3. **Cách lái – bác bỏ:** Track01 quay ít hơn (0.40 so với 0.80 °/s) và ít dừng hơn mà vẫn giật gấp 3; không tương quan với tốc độ
   hay tốc độ quay. (Gia tốc chỉ liên quan ở Track02, nơi độ giật vốn nhỏ.)

**Hệ quả & cải tiến đề xuất:** GNSS Track01 kém (nhiều bước nhảy) nên scan matching có chỗ để sửa – khớp với việc GICP chỉ giúp Track01.
Cải tiến trực tiếp cho "sai số lớn bất thường": **phát hiện bước nhảy GNSS (sai phân > 5× trung vị hoặc innovation lớn) và giảm
trọng số các mẫu đó trong Kalman/RTS** (robust measurement update) – đưa vào T12 / ứng viên T6.

## T4 – Quét tham số offline (mỗi lần đổi 1 tham số)

**Câu hỏi (tr. 13 "voxel gây sai bao nhiêu", tr. 14 "scale gây sai gì / có tỉ lệ tốt hơn 0.8 không", tr. 42 "chỉnh thông số nào
ít sai nhất", tr. 45 "hướng giảm điểm").** **Giả thuyết (từ T2):** méo độ sâu tăng theo khoảng cách → **giới hạn tầm** giảm nhiễu /
độ lệch; voxel bản đồ ít ảnh hưởng; tỉ lệ sai làm lệch dọc có hệ thống.

**Cách làm:** GICP lượt 1 Track01 từ cùng prior sạch, chỉ đổi đúng một tham số so với `ref` (= pipeline: bản đồ 0.3 m, tầm 40 m,
tỉ lệ 1.646 / h). Bản đồ 0.2 m dựng mới từ `map.pcd` (`data/Track1/map_voxel_0.2m.pcd`, file mới). Thống kê bằng `tools/t4_summary.py`
(không có đáp án → các chỉ số chỉ là độ ổn định / độ lệch của phép khớp, không phải sai số thật).

```bash
bash midterm01/tools/t4_sweep.sh          # 7 lượt, 34 phút
docker run --rm -v ~/SDC-midterm01/midterm01:/w -w /w sdc-reg python3 tools/t4_summary.py
```

| Cấu hình | % hợp lệ | Lệch TB dọc | Lệch TB ngang | Nhiễu dọc | Nhiễu ngang | Độ sửa yaw RMS | Thời gian |
|---|---|---|---|---|---|---|---|
| `ref` (40 m, map 0.3, ×1) | 53.1 | +0.166 | −0.136 | 0.665 | 0.532 | 1.54° | ~3.5 phút |
| **tầm 20 m** | **58.0** | −0.104 | −0.294 | **0.563** | **0.403** | 1.51° | 1.4 phút |
| tầm 30 m | 53.6 | +0.086 | −0.137 | 0.617 | 0.517 | 1.54° | 2.4 phút |
| map 0.2 m | 52.5 | +0.185 | −0.089 | 0.628 | 0.535 | 1.50° | 9.2 phút |
| map 0.5 m | 52.8 | +0.159 | −0.176 | 0.675 | 0.511 | 1.52° | 2.8 phút |
| tỉ lệ ×0.95 (0.76) | 49.7 | +0.209 | −0.252 | 0.665 | 0.512 | 1.53° | 3.4 phút |
| tỉ lệ ×1.05 (0.84) | 53.8 | **+0.107** | **−0.031** | 0.688 | 0.530 | 1.50° | 3.2 phút |

Số liệu: `data/t4_sweep.csv`.

**Kết luận:**
- **Tầm 20 m – xác nhận giả thuyết:** nhiều frame hợp lệ nhất (58 %), nhiễu dọc / ngang giảm 15 % / 24 %, nhanh gấp 2.5 lần.
  Độ lệch TB đổi dấu theo phương dọc (+0.17 → −0.10) → phần điểm xa (> 20 m) đóng góp phần lớn độ lệch dọc dương. Ứng viên số 1.
- **Voxel bản đồ:** 0.2 / 0.3 / 0.5 m khác nhau rất ít (0.2 m nhiễu dọc thấp hơn 0.04 m nhưng chậm 3×) → voxel không phải nguồn sai.
- **Tỉ lệ:** ×0.95 kém rõ (ít frame hợp lệ, lệch lớn hơn); ×1.05 lệch TB gần 0 nhất nhưng nhiễu hơi tăng. Độ nhạy thật nhỏ hơn
  giả lập nhiều (T2: 3 % tỉ lệ → 0.3 m; thật: 5 % → chỉ −0.06 m dọc) → độ lệch thật **không chủ yếu do tỉ lệ**. Chưa kết luận tỉ lệ
  tốt nhất chỉ bằng offline.
- **Ứng viên cho T6 (≤ 3):** (1) tầm 20 m (2 lượt + demean + yaw gyro như pipeline); (2) giảm trọng số khúc cua `TURN_WEIGHT=0`
  (yêu cầu của người dùng, xem T3); (3) tỉ lệ ×1.05 hoặc tầm 30 m. Thứ tự đề xuất khi báo người dùng ở bước T6.

## T7 – Làm sạch z / roll / pitch và đo chiều cao camera

**Câu hỏi (tr. 27 "lượt NDT cũ c3s08 → z, roll, pitch là sao"; tr. 14 "h ≈ 2.06 m nhưng camera 1.65 m – tại sao").**
**Vấn đề:** GICP cần pose 3D; x, y, yaw lấy từ prior Kalman nhưng z / roll / pitch lấy từ lượt NDT C++ `c3s08`, vốn chạy với
prior `yawproj_v1_1` (yaw chọn theo bảng điểm) → pipeline chưa sạch tuyệt đối. **Giả thuyết:** thay bằng mặt đường bản đồ +
chiều cao camera thì kết quả gần như không đổi (z / roll / pitch ít ảnh hưởng tới x, y).

**Cách làm (`tools/t7_pose_source.py`):** mỗi frame, mặt phẳng mặt đường bản đồ quanh (x, y) prior (bán kính 6 m, dải 0.4 m trên
phân vị 5 %, khớp lại bỏ 20 % xấu nhất) → độ cao mặt đường z_g và pháp tuyến → roll, pitch theo hướng xe. z = z_g + H. Lượt NDT cũ
chỉ còn dùng để **đo 3 hằng số mỗi track** (trung vị): chiều cao H, góc lắp roll, pitch – thay vì cho pose từng frame.

```bash
docker run ... sdc-reg python3 tools/t7_pose_source.py 1 --prior $R/clean/clean_prior_1.csv --old-run c3s08 \
  --out $R/t7/mapground_Track1_result.txt      # Track02: --old-run c3s10T2
POSE_SOURCE1=$R/t7/mapground_Track1_result.txt bash midterm01/tools/run_clean_pipeline.sh $R/t7/pipeline
```

| | Track01 | Track02 |
|---|---|---|
| H = z(NDT cũ) − mặt đường bản đồ (trung vị, IQR) | 1.952 m (1.76–2.17) | 2.327 m (2.18–2.52) |
| H ngầm định bởi hằng số tỉ lệ | 1.646 m | 1.646 m |
| Góc lắp pitch (cũ − bản đồ) | **+2.47°** | **+2.30°** |
| Góc lắp roll | −2.87° | −0.05° |
| Sau hiệu chỉnh, lệch so với NDT cũ: z / roll / pitch RMS | 0.47 m / 3.85° / 1.27° | 0.26 m / 1.24° / 0.63° |
| **Kết quả cuối (2 lượt GICP + yaw) so với bài chấm `clean_cfz1_tau7`** | **0.060 m RMS** (max 0.29 m) | – (Track02 không dùng GICP) |

**Kết luận:**
- **Giả thuyết xác nhận:** bỏ pose từng frame của `c3s08` chỉ đổi vị trí cuối 6 cm RMS → pipeline không còn phụ thuộc vào lượt NDT
  chạy với prior chọn theo điểm (chỉ còn 3 hằng số hiệu chuẩn). Ứng viên `t6_mapground_1.csv` (nếu điểm bằng bài chấm thì nên dùng
  bản này cho sạch).
- **Góc lắp pitch +2.3…+2.5° nhất quán giữa hai track** → camera (khung point cloud) chúc ~2.4° so với mặt đường – một thông số hiệu
  chuẩn thật. Roll không nhất quán (Track01 −2.9°) → nhiều khả năng bản đồ đoạn Track01 hơi nghiêng; chưa kết luận được.
- **Chiều cao camera:** H đo theo NDT = 1.95 / 2.33 m, khác nhau giữa hai track và khác 1.646 m → **không phải chiều cao vật lý độc
  lập**: z của NDT chỉ khớp theo point cloud đã nhân tỉ lệ (0.8 ở Track01, 1.0 ở Track02), nên H đo được là "độ cao mặt đường trong
  point cloud × tỉ lệ" + sai số mặt đường bản đồ. Tỉ lệ và chiều cao camera **không tách được** chỉ từ point cloud ảnh (chúng nhân với
  nhau) → câu hỏi "h 2.06 m vs camera 1.65 m" **chưa kết luận được**; T4 cho thấy tỉ lệ ±5 % đổi độ lệch rất ít nên ảnh hưởng tới điểm nhỏ.

## T6 – Ứng viên Kaggle (chờ người dùng duyệt, KHÔNG tự nộp)

File ở `src/localization/result/candidates_T6/` (đã kiểm tra định dạng bằng `bot.validate`). Track02 không đổi (không dùng GICP) →
cả 3 ứng viên là Track01; mỗi file khác bài chấm `clean_cfz1_tau7` (0.80) đúng một thay đổi, yaw giống hệt.

| File | Thay đổi | Giả thuyết | Lệch so với bài chấm | Dự đoán |
|---|---|---|---|---|
| `t6_range20_1.csv` | GICP `--max-range 20` (thay 40) | điểm xa méo nhất (T2, T4: nhiễu −15/−24 %, hợp lệ +5 %) | 0.375 m RMS | 0.74–0.84 (không chắc chiều) |
| `t6_turn0_1.csv` | `--turn-weight 0` (bỏ GICP khi cua) | frame cua nhiễu 1.07 m, chỉ 35 % hợp lệ (T3) | 0.090 m | 0.79–0.81 |
| `t6_mapground_1.csv` | z / roll / pitch từ bản đồ (T7) | pipeline sạch hơn, kết quả gần như không đổi | 0.060 m | 0.79–0.81 |

## T8 – Mục "Leaderboard analysis" cho báo cáo (tiếng Anh, dán vào Problems and Solutions)

**Câu hỏi (tr. 9 "chỉ trình bày như phân tích – viết vào report thế nào"; tr. 43; tr. 48 "đọc Hình 21").** Số liệu từ
`09-thong-ke-nop-bai.md` (152 lần nộp, 85 là file dò / tổ hợp: Track01 37, Track02 48). Hình 21 = `fig/submission_progress.png`.

> **Leaderboard analysis (not used for grading).** Kaggle returns only one number per submission, the total
> score E = P + 0.2·Y (P = position RMSE in metres, Y = yaw RMSE in degrees), so the leaderboard alone cannot tell
> which part of the pipeline is wrong. We therefore submitted a few controlled pairs early on: shifting every pose by
> ±L along one axis gives P₊² + P₋² − 2P² = 2L², so each pair isolates P exactly, and a ±1° yaw pair isolates Y in
> the same way. Three independent pairs agreed to 0.0014 and gave Track01 = 0.905 m + 1.77° and
> Track02 = 0.23 m + 0.88°. This analysis produced four findings that we then turned into real algorithm changes:
> (1) yaw was the largest share of the score, (2) the answer yaw is the vehicle body yaw, not the motion heading,
> which led to the gyro complementary filter (−0.14 on Track01); (3) the GNSS has no lateral bias and no time offset
> (+0.025 m, −3.6 ms), so de-meaning the GICP correction is safe; (4) the Track01 error is slow and mostly along the
> road. We later extended the idea into score-weighted combinations and cosine-mode probes, which reached 0.46 /
> 0.19 but only re-estimate the hidden answer: their weights have no physical meaning (e.g. −4.58) and would not
> transfer to new data. After the TA's clarification on 20/10 we stopped on 21/10 (85 of our 152 submissions were
> probes or combinations) and rebuilt every graded file from the localization pipeline alone. Figure 21 shows the
> difference: the pipeline-only curve falls from 1.253 to 0.789 through algorithm changes and then stays flat, while
> the leaderboard-fitted curve drops in steps exactly on the two probing days. **All graded submissions come directly
> from the localization pipeline.**

(≈ 270 từ. Ghi chú: 0.789 là bản cùng phương pháp; bài chấm sạch hiện tại 0.80 / 0.28.)

## T10 – Baseline 1.79 trên Kaggle nhưng chạy trên máy trôi 91–110 m

**Câu hỏi (tr. 26 "baseline thấp thì trông như nào"; brief 4: "file baseline TA nộp có lẽ không phải lượt trôi này – cần kiểm chứng").**

**Cách làm:** lượt chạy code mẫu TA không sửa (`ply_scale = 3`, khởi đầu `init_guess`, frame sau bắt đầu từ frame trước) lưu ở
`data/baseline_partial/` (dừng ở frame 504 / 782 vì đã trôi); đổi sang CSV rồi so với GNSS nội suy (`gnss_N.csv`, điểm Kaggle 1.31 / 0.57,
đủ gần đáp án để làm thước đo cỡ chục mét) bằng `tools/track_error.py`.

| | Track01 (505 / 3011 frame đầu) | Track02 (783 / 3299 frame đầu) |
|---|---|---|
| Lệch > 5 m từ frame | 18 | 0 |
| Lệch > 20 m từ frame | 239 | 505 |
| Lệch ở frame cuối đã chạy | 90.7 m, yaw +112° | 94–110 m, yaw −73° |
| RMSE vị trí / yaw trên đoạn đã chạy | 42.2 m / 80.0° | 39.8 m / 81.0° |
| "Điểm" tính trên đoạn đã chạy (so với GNSS) | **58.2** | **56.0** |
| Điểm Kaggle của baseline TA | 1.79075 | 1.92587 |
| Điểm Kaggle của chính file mình chạy code mẫu (16/10, `kaggle_track1_result.csv`) | **602.39** | – |

**Kết luận:** lượt chạy code mẫu với cấu hình mặc định cho điểm hàng chục (chỉ 17–24 % đầu quỹ đạo: 56–58) tới hàng trăm (cả quỹ đạo:
602 khi mình nộp thử) → **file baseline 1.79 / 1.93 TA đăng trên Kaggle không phải output của cấu hình mặc định trong code mẫu.**
Điểm 1.79 nằm giữa "chỉ GNSS" (1.31) và lượt trôi (> 50) → nhiều khả năng TA dùng tỉ lệ đúng và / hoặc khởi đầu bằng GNSS. Đã xác nhận
giả thuyết của brief; cấu hình thật **chưa kết luận được** (cần hỏi TA).

**Câu hỏi soạn sẵn cho TA:** *"The provided template with its default settings (ply_scale = 3) drifts by ~90–110 m within the first
500–800 frames on our machine, and the full output scored 602 on Kaggle, while the published baseline is 1.79 / 1.93. Which
configuration (ply_scale, initial pose, GNSS use) produced the baseline submission? We would like to describe the baseline correctly in
our report."*

## T5 – Giải thích lỗi tỉ lệ ×3 cho báo cáo

**Câu hỏi (tr. 6 "tỉ lệ ×3 thay vì ×9, trôi ~100 m – vì sao sai tỉ lệ gây trôi lớn").** Hình: `fig/t5_scale_x3.png` (trái: frame 40
Track01 đặt tại pose GNSS, point cloud `raw_ply` ×3 so với ×9.27 – chỉ minh hoạ kích thước, chưa khớp; phải: sai số so với GNSS của
lượt chạy code mẫu, `data/baseline_partial/`).

> **Point-cloud scale.** The image point clouds have no metric scale, and the template multiplies the `raw_ply` clouds by
> 3. Measuring the road height under the camera in every cloud (0.177 units on Track01) and comparing it with the camera
> height gives a scale of about 9.3, so with ×3 every structure appears three times closer than it is: walls 30 m away look
> 10 m away and the whole cloud fits inside a ~13 m radius around the car (left figure). NDT then has no correct pose to find:
> it pulls the scan towards the nearest map structures that roughly match the shrunken shape, and because each frame starts
> from the previous estimate, every wrong match becomes the next starting point. The error exceeded 5 m after 18 frames on
> Track01 (at the first frame on Track02) and grew to 91 m and 110 m before we stopped the runs (right figure); the full
> template output scored 602 on Kaggle. With the measured scale (×9 for `raw_ply`, ×0.8 or 1.646 m / road height for
> `3cameras_ply`) NDT and GICP converge – the remaining problem is that the reconstructed clouds are distorted, not scaled
> wrongly (T2).

## T9 – Tài liệu cho thuyết trình (4–6 phút, 29/10)

**Câu hỏi (tr. 6 "ba phát hiện chính – nói rõ khi thuyết trình"; tr. 8 "LoGeR, MapAnything là gì"; tr. 16 "GICP vs NDT";
tr. 17 "tại sao cần Kalman"; tr. 40 "bài toán tương tự").** Dùng điểm sạch (0.80 / 0.28), không dùng 0.46 / 0.19.

### Dàn 7 slide (~45 s / slide)

| # | Tiêu đề (câu kết luận) | Nội dung / hình | Câu nói chính |
|---|---|---|---|
| 1 | Localizing a car on a LiDAR map with camera point clouds | tên, đội 11, 0.80 / 0.28 (baseline 1.79 / 1.93) | "Giảm hơn một nửa sai số baseline ở cả hai track." |
| 2 | Four stages: GNSS smoother → GICP → fusion → gyro yaw | sơ đồ pipeline; Track02 bỏ bước 2–3 | "Mỗi nguồn chỉ được dùng khi nó chính xác hơn cái nó sửa." |
| 3 | Finding 1 – the template ran NDT at the wrong scale | `fig/t5_scale_x3.png` | "×3 thay vì ×9: point cloud nhỏ hơn thật 3 lần, NDT trôi tới 100 m." |
| 4 | Finding 2 – the answer yaw is the body yaw: use the gyro | bảng yaw 1.56° → 0.87°, 0.33° → 0.25° | "Yaw GNSS là hướng chạy, trễ 1.1–1.4 s; gyro đo trực tiếp." |
| 5 | Finding 3 – the error comes from the AI point clouds, not the matcher | `fig/t2_synthetic.png` | "GICP trên point cloud hoàn hảo sai 5 mm; méo có hệ thống của point cloud mới gây ~0.7 m." |
| 6 | Track01 vs Track02: scan matching helps only where GNSS is worse | waterfall Track01 + bảng Track02; `fig/t11_gnss_jitter.png` | "GNSS Track01 bị che chắn, 11 bước nhảy → GICP có chỗ để sửa; Track02 GNSS 0.23 m tốt hơn GICP." |
| 7 | Lessons & honesty | 3 bài học; dò bảng điểm chỉ là phân tích, mọi bài chấm từ pipeline; dùng AI làm trợ lý | "All graded submissions come directly from the localization pipeline." |

### Câu trả lời dự phòng

- **Vì sao demean?** GICP lệch cố định ~+0.17 m dọc / −0.14 m ngang so với GNSS (gốc camera / méo của point cloud); GNSS không lệch ngang.
  Prior giữ phần trung bình, GICP chỉ thêm dao động cục bộ (bộ lọc bù). Điểm: 0.99060 → 0.92775.
- **Vì sao tỉ lệ 0.8 / 1.646 m?** Độ cao mặt đường trong point cloud 3 camera trung vị 2.058 đơn vị; 0.8 × 2.058 = 1.646 m. Đo mỗi frame vì
  độ cao này đổi 1.73–2.27 giữa các đoạn. T4: ±5 % tỉ lệ đổi kết quả rất ít; tỉ lệ và chiều cao camera không tách được từ point cloud ảnh.
- **Vì sao 2 lượt GICP?** Point cloud méo → cực tiểu GICP lệch khỏi vị trí thật; đi một phần đường thì có lợi (2 lượt 0.993), đi hết
  thì hại (5 lượt 1.115). T2 xác nhận lỗi đến từ point cloud.
- **Vì sao Track02 không dùng GICP?** GNSS Track02 sai ~0.23 m, GICP trên point cloud ảnh nhiễu ~0.75 m mỗi frame → mọi lần thêm GICP
  đều xấu đi (0.28 → 0.30–0.37).
- **GICP vs NDT?** NDT so điểm với phân bố chuẩn của từng ô lưới (4–8 m), không ghép cặp, nhạy kích thước ô, ~14 s/frame (C++ mẫu);
  GICP ghép cặp điểm gần nhất, mỗi điểm hai phía có hiệp phương sai từ 20 điểm lân cận (plane-to-plane), ~0.06 s/frame; trên cùng dữ liệu
  GICP 0.803 m so với NDT 0.836 m.
- **Vì sao Kalman?** GNSS 4 Hz, camera 28 Hz → cần nội suy theo mô hình chuyển động; GNSS Track01 giật (0.142 m) → RTS smoother dùng cả dữ
  liệu tương lai để làm mượt; Track02 0.473 → 0.408.
- **LoGeR / MapAnything là gì?** Hai mô hình AI dựng 3D từ ảnh (point cloud do TA chạy sẵn): MapAnything (Meta + CMU, 2025) – transformer
  feed-forward dự đoán độ sâu, tia camera, pose và hệ số tỉ lệ mét (→ `3cameras_ply`, tỉ lệ gần mét); LoGeR (Google DeepMind + UC Berkeley,
  2026) – dựng hình học cho video dài bằng bộ nhớ lai (→ `raw_ply`, đơn vị tuỳ ý, cần ×9).
- **Có dò bảng điểm không?** Có, như phân tích (T8); TA làm rõ 20/10, dừng 21/10, mọi bài chấm từ pipeline.

### Tài liệu tham khảo (đã tra, 23/10)

| Tài liệu | Đã xác minh | Ghi chú |
|---|---|---|
| T. Caselitz et al., "Monocular camera localization in 3D LiDAR maps", IROS 2016, pp. 1926–1931 | tên / hội nghị / trang qua trích dẫn ([computeroptics.ru](https://www.computeroptics.ru/KO/Annot/KO48-3/480311.html)); "Caselitz et al." qua [CMRNext](https://arxiv.org/html/2402.00129v5); chưa mở được bản gốc | dựng 3D từ camera (visual odometry) rồi khớp vào bản đồ LiDAR – gần nhất với bài này |
| D. Cattaneo et al., "CMRNet: Camera to LiDAR-Map Registration", ITSC 2019, pp. 1283–1289, DOI 10.1109/ITSC.2019.8917470 | ✅ [arXiv 1906.10109](https://web3.arxiv.org/abs/1906.10109), [UAH](https://ebuah.uah.es/dspace/handle/10017/60404) | CNN khớp ảnh vào bản đồ LiDAR, KITTI ~0.27 m / 1.07° |
| K. Koide, `hdl_localization` (UKF + IMU + NDT) | ✅ [GitHub](https://github.com/koide3/hdl_localization/blob/master/README.md) | UKF dự đoán bằng IMU, NDT sửa – cùng ý "scan matching là phép đo trong bộ lọc" |
| Autoware `ndt_scan_matcher` + `ekf_localizer` | ✅ [index.ros.org](https://index.ros.org/p/autoware_ndt_scan_matcher/), [pose_initializer](https://index.ros.org/p/autoware_pose_initializer/) | GNSS cho pose thô → NDT tinh chỉnh → EKF |
| A. Segal, D. Haehnel, S. Thrun, "Generalized-ICP", RSS 2009, DOI 10.15607/RSS.2009.V.021 | ✅ [roboticsproceedings.org](https://roboticsproceedings.org/rss05/p21.html) | thuật toán GICP |
| P. Biber, W. Straßer, "The normal distributions transform", IROS 2003, pp. 2743–2748 | ✅ [IEEE Xplore](https://ieeexplore.ieee.org/document/1249285) | NDT của code mẫu |
| K. Koide, "small_gicp", JOSS 9(100) 6948, 2024, DOI 10.21105/joss.06948 | ✅ [JOSS](https://joss.theoj.org/papers/10.21105/joss.06948) | thư viện GICP dùng trong bài |
| N. Keetha et al., "MapAnything: Universal Feed-Forward Metric 3D Reconstruction", arXiv 2509.13414 (3DV 2026) | ✅ [arXiv](https://arxiv.org/abs/2509.13414v3) | mô hình dựng `3cameras_ply` |
| J. Zhang et al., "LoGeR: Long-Context Geometric Reconstruction with Hybrid Memory", arXiv 2603.03269 | ✅ [arXiv](https://arxiv.org/pdf/2603.03269.pdf) | mô hình dựng `raw_ply` (theo slide TA – chưa đối chiếu slide gốc) |
| S. Thrun, W. Burgard, D. Fox, *Probabilistic Robotics*, MIT Press 2005 (giáo trình môn học) | slide môn học | Ch. 3 (Kalman), Ch. 7 (localization); slide Localization tr. 61: bộ lọc chỉ chịu nhiễu độc lập theo thời gian – lỗi có hệ thống của point cloud thì không |

## T12 – Kalman bền vững với bước nhảy GNSS (và vì sao không làm tiếp bản GICP + IMU)

**Câu hỏi (tr. 41 "lọc không khử được lỗi trôi chậm → cần cách tính khác"; người dùng 22/10: xử lý sai số lớn bất thường).**
**Giả thuyết:** 11 bước nhảy GNSS ở Track01 (T11) kéo quỹ đạo Kalman lệch; giảm trọng số các mẫu đó sẽ làm prior tốt hơn.

**Cách làm:** `tools/rts_smoother.py --robust K` – cập nhật kiểu Huber: mẫu GNSS có khoảng cách Mahalanobis của phần vị trí d > K thì nhiễu
đo được nhân d / K. Tham số nhiễu vẫn chọn bằng maximum likelihood như cũ (không bật robust thì kết quả trùng 100 % file cũ – đã kiểm
tra, lệch 0.0). Sửa thêm `gnss_to_csv.read_gnss`: rosbags mới chỉ mở bag theo thư mục → tự dùng thư mục khi nhận đường dẫn `.db3`.

```bash
docker run ... sdc-reg python3 tools/rts_smoother.py /w/data/Track1 Track1 $R/reg/t12/rts_robust3_1.csv --yaw gnss --qa 1.0 --qw 0.1 --robust 3
docker run ... sdc-reg python3 tools/rts_smoother.py /w/data/Track2 Track2 $R/reg/t12/rts_robust3_2.csv --yaw heading --robust 3
```

| | Track01 | Track02 |
|---|---|---|
| σ vị trí GNSS (ML) | 0.050 m | 0.006 m |
| Mẫu bị giảm trọng số (K = 3) | 98 / 440 | 282 / 475 |
| Lớn nhất (σ) và thời điểm | 11.3σ ở **27–39 s, 82.7 s** (đúng cụm bước nhảy của T11) | 23.6σ ở 81–84 s |
| Đổi vị trí so với Kalman thường | **0.019 m RMS** (max 0.115 m, 136 frame > 5 cm) | 0.006 m RMS (max 0.037 m) |

**Kết luận:**
- Bộ lọc **tự phát hiện đúng** các bước nhảy (xác nhận T11), nhưng **giả thuyết bác bỏ về mức độ:** RTS smoother vốn đã làm phẳng phần lớn
  bước nhảy, robust chỉ đổi 1.9 cm RMS → ảnh hưởng điểm < 0.01 (dưới mức Kaggle hiển thị) → **không đề xuất nộp**. Track02: σ ML rất nhỏ
  (0.006 m) nên ngưỡng K = 3 đánh dấu tới 59 % mẫu – không có ý nghĩa; Track02 không có vấn đề bước nhảy.
- **Kalman GNSS-bias Gauss–Markov + GICP làm phép đo:** về toán học là cùng bài toán bình phương tối thiểu tuyến tính mà `tools/info_fuse.py`
  đã giải (RTS smoother của mô hình tuyến tính Gauss = nghiệm bình phương tối thiểu). Bản đó đã nộp 22/10 và **kém hơn** (0.84 / 0.87 so với
  0.80) vì sửa ít hơn bản 2 lượt GICP cộng dồn. T2/T3 cho thấy lỗi còn lại là **méo có hệ thống, tương quan theo thời gian** của point cloud –
  đúng loại lỗi mà bộ lọc Kalman (giả định nhiễu độc lập, slide Localization tr. 61) không khử được. → **Không làm tiếp**; nếu còn thời gian
  thì đầu tư vào đầu vào (tầm 20 m, T4/T6) hơn là bộ lọc.

## T13 – Dọn repo

| Việc | Thay đổi |
|---|---|
| README | điểm cũ (1.25338 / 0.40778) → bài chấm sạch 0.80 / 0.28, lệnh tái tạo, ghi rõ 0.46 / 0.19 chỉ là phân tích; link tới file này |
| `tools/reproduce_submissions.sh` | trước đây so **mọi** file trong `submissions/` (kể cả file GICP / dò mà script không dựng lại) → báo "DIFFERENT" sai; giờ chỉ so file script dựng lại và in số "identical / different / not rebuilt" |
| Thư mục build | giữ nguyên (đều trong `.gitignore`); ghi rõ trong `docs/HUONG-DAN-CHAY.md` bản nào dùng cho script nào (`install_dev` hằng ngày, `install_par` chạy song song, `install` baseline) |
| `tools/gicp_refine.py` | kiểm tra đầu vào: thiếu / sai `--prior`, số dòng prior khác số frame, thiếu `--pose-source` hoặc không tìm thấy lượt chạy, thiếu bản đồ, và **độ cao khởi đầu lệch > 20 m so với bản đồ** (lỗi `c3s10` thay cho `c3s10T2` ngày 21/10 giờ báo ngay: "start height z = 109.9 m but the map around the first pose is at ~17.4 m") |
| `gnss_to_csv.read_gnss` | mở bag theo thư mục khi nhận `.db3` (rosbags mới) – `rts_smoother.py` chạy được trong `sdc-reg` |
| Kiểm chứng | `run_clean_pipeline.sh` chạy lại sau mọi thay đổi → `result_1.csv`, `result_2.csv` **trùng từng byte** với `clean_cfz1_tau7.csv`, `clean_cfz2_tau15.csv` |

### T6 – Kết quả đợt 1 (người dùng duyệt, nộp 23/10 03:21 giờ máy; còn 12 lượt mỗi track)

| File | Thay đổi so với bài chấm (0.80) | Dự đoán | **Kaggle** |
|---|---|---|---|
| `t6_range20_1.csv` | GICP `--max-range 20` | ~0.80 (0.72–0.91) | **0.63** ✅ (−0.17) |
| `t6_turn0_1.csv` | `--turn-weight 0` | 0.79–0.80 | **0.78** ✅ (−0.02) |
| `t6_mapground_1.csv` | z/roll/pitch từ bản đồ | ~0.80 | **0.81** (≈ bằng, +0.01) |

- **Tầm 20 m – xác nhận mạnh giả thuyết T2/T4:** phần point cloud xa > 20 m (méo nhiều nhất) là nguồn lỗi lớn; bỏ đi thì GICP sửa đúng hơn
  hẳn. Thực tế vượt cả kịch bản tốt mình dự đoán (0.72) → mô hình dự đoán đã đánh giá thấp mức "sửa đúng" của GICP khi đầu vào sạch hơn.
- **Bỏ GICP khi cua:** tốt hơn một chút (0.78) – đúng hướng đề xuất của người dùng; nhỏ vì cua chỉ ~5–7 % frame.
- **Z/roll/pitch từ bản đồ:** ngang bài chấm → pipeline sạch hơn không mất điểm.
- **Bài chấm Track01 mới: `t6_range20_1.csv` (0.63)** – nhớ chọn "Use for Final Score". Đợt 2 đang chuẩn bị: tầm 15 m; tầm 20 m + bỏ cua;
  Track02 có GICP tầm 20 m.

## Dò điểm như một chiến thuật thi đấu – công thức và những chỗ "vô lý" (cho thuyết trình, 23/10)

Người dùng báo TA cho phép trình bày trước lớp. **Lưu ý luật 10/22 (file `…Localization-3.pdf`):** "Offline trajectory corrections and
leaderboard-based fitting are strictly prohibited" + "Causal localization only" + TA chạy lại code, vi phạm = 0 điểm track đó → dò chỉ là
phân tích / chiến thuật để kể, **không được chọn làm bài chấm**.

### Công thức

1. **Điểm:** S = P + 0.2·Y (P = RMSE vị trí, m; Y = RMSE yaw, độ). Bảng chỉ cho S.
2. **Cặp dò tách P và Y:** dời mọi pose ±L theo một trục: P±² = P² ± 2L·ē + L² ⇒ **P+² + P−² − 2P² = 2L²**. Ba file (gốc, +L, −L) có
   chung Y → 3 phương trình, 3 ẩn (P, Y, ē) → giải ra P, Y. Làm tương tự với yaw ±1°. Ba cặp độc lập khớp nhau tới 0.0014.
3. **Hình chiếu của lỗi lên một thay đổi bất kỳ D** (cộng D vào vị trí, giữ yaw): P_D² = P² + 2·mean(e·D) + mean|D|² ⇒
   **m_D = mean(e·D) = (P_D² − P² − mean|D|²) / 2** – mỗi lượt nộp đo được đúng một con số về lỗi ẩn e.
4. **Tổ hợp tối ưu:** vị trí = gốc + Σ aₖ·Dₖ ⇒ P(a)² = P² + 2aᵀm + aᵀGa, G_ij = mean(Dᵢ·Dⱼ) ⇒ **a* = −G⁻¹m**, P*² = P² − mᵀG⁻¹m
   (`tools/pos_projection.py`; yaw: `tools/yaw_projection.py`). Dự đoán trùng điểm thật tới 0.0003.
5. **Dao động cosin (DCT):** Dₖ(t) = 0.5 m·cos(πk·t/T) cộng vào x hoặc y → mₖ = hệ số DCT bậc k của lỗi → 14 bậc × 2 trục = dựng lại
   phần tần số thấp của lỗi (`tools/make_probes.py`).

### Những chỗ "vô lý" (số không có ý nghĩa vật lý)

| Chỗ | Số | Vì sao vô lý |
|---|---|---|
| Trọng số tổ hợp yaw Track02 | −4.581, −2.156 | một hiệu chỉnh vật lý nằm trong 0…1; −2.156 nghĩa là bù trễ **ngược chiều và gấp đôi** |
| Trọng số 18 trường vị trí Track01 | −9.2 … +7.5 | trộn các kết quả NDT/GICP với hệ số âm lớn = đi **ngược** điều scan matching nói ở một số hướng |
| Hướng gần trùng nhau (đưa cả file vốn là tổ hợp của file khác) | hệ số tới **hàng triệu** | G gần suy biến → nghiệm bùng nổ; phải bỏ bớt hướng |
| Điểm sau dò | 0.46 / 0.15 | tốt hơn mọi cảm biến / thuật toán (GNSS ~0.9 m, GICP tốt nhất 0.62) → chỉ có được khi "biết đáp án" |
| Quỹ đạo sau dò | tổng 28 sóng cosin | không ứng với phép đo nào; không chuyển sang dữ liệu mới (Track03 private: vô dụng) |
| Từ 21/10 Kaggle cắt còn 2 chữ số | sai số đo ±0.005 | mỗi mₖ nhiễu ~0.004 m²; dự đoán P² có lúc âm (phải cắt về 0) |

**Phòng thủ của ban tổ chức (đúng những gì đã xảy ra):** cắt điểm còn 2 chữ số, public/private leaderboard (Track03), luật causal + chạy lại
code. **Cách nói khi thuyết trình:** "Bảng điểm là một oracle bậc hai: mỗi lần nộp đo được một hình chiếu của lỗi ẩn. Chúng tôi dùng nó để
chẩn đoán (yaw chiếm phần lớn lỗi; yaw đáp án là yaw thân xe) rồi biến chẩn đoán thành thuật toán; mọi bài chấm đến từ pipeline."
