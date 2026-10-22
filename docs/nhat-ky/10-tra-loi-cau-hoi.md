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
