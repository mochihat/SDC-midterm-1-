# 11 – Đêm 22→23/10: luật 10/22, Track03 (nhân quả, không GNSS) và dò Track01/02

## Luật

- File `SDC 2026 Midterm01 Competition - Localization-3.pdf`, slide "Mid01 Updates Rules 10/22": cấm hậu xử lý / leaderboard-based
  fitting; **chỉ định vị nhân quả** (frame hiện tại và quá khứ, không làm mượt ngược); TA chạy lại code; vi phạm = 0 điểm track đó.
- Người dùng hỏi TA trực tiếp trên lớp (23/10): **Track01/02 chấm public toàn bộ → dò được**, được trình bày chiến thuật trước lớp;
  **Track03 tuyệt đối theo luật 10/22**. Mọi file Track03 dưới đây là output trực tiếp của `tools/track_localize.py` (nhân quả),
  không chỉnh tay, không dò. Tham số chọn bằng so sánh vài cấu hình (chỉnh tham số bình thường).

## Track03

**Dữ liệu** (không tải được từ trang Kaggle vì quá nhiều file → `Track3.zip` trên Google Drive, link trong PDF luật): `map.pcd`
(57 M điểm → 1.55 M voxel 0.3 m), `Track3.db3` (IMU + 3 luồng ảnh, **không GNSS**), `init_guess.txt` (roll / pitch ~15° – nhiễu),
`raw_ply` (LoGeR, camera trước, 3142 frame, đơn vị tuỳ ý, tỉ lệ đo bằng độ cao mặt đường ≈ ×9.2). Không có `3cameras_ply`.

**Thuật toán (`tools/track_localize.py`, nhân quả):** mỗi frame (1) tỉ lệ = 1.646 m / trung vị độ cao mặt đường của 57 frame đã qua;
(2) dự đoán: **odometry scan-to-scan** (GICP point cloud hiện tại với point cloud G frame trước → độ dịch tiến / ngang chia G) +
yaw tích phân gyro (bias −0.26 °/s hiệu chuẩn từ Track01/02); (3) đo: GICP với bản đồ 0.3 m (tầm 20 m), trừ hiệu chuẩn (yaw +0.66°,
dọc `--bias-along`); (4) cập nhật Kalman vị trí (σ 0.7 m, cổng 3σ), yaw kéo về yaw bản đồ với hằng số τ. Khởi đầu: **MHT** – 11 giả
thuyết yaw ±30° quanh `init_guess`, chạy song song, giữ giả thuyết có innovation nhỏ nhất **sau khi xe đi ≥ 25 m**.

**Hiệu chuẩn (từ Track01/02, có GNSS):** GICP `raw_ply` tầm 20 m lệch dọc −0.52 / −0.57 m, ngang +0.18 / +0.08 m, yaw +0.59° / +0.73°.

**Kiểm thử không GNSS trên Track01/02** (so với bài clean, 900 frame): bản vận tốc không đổi trôi tới hàng chục m (along-track không
quan sát được); odometry gap 3 đánh giá thấp tốc độ ~50 % khi chậm; gap 10: Track01 7.4 m RMS (đầu 1.7 m, cuối 1.3 m); MHT theo lỗi
GICP chọn sai ở Track02 (13 s đứng yên) → đổi sang innovation sau 25 m.

**Các lần nộp Track03 (23/10, 15/15; bản 1000 frame + giữ pose cuối cho phần còn lại – điểm public chỉ chấm 10–30 % đầu):**

| File | So với bản trước | Điểm public |
|---|---|---|
| `t3_v2` (đủ 3142 frame) | vận tốc từ odometry gap 10, bias gyro hiệu chuẩn, MHT theo lỗi GICP | 3.18 |
| `t3_vA` | MHT theo innovation sau 25 m | 1.30 |
| `t3_vB` | A + σ đo 0.4 | 46.67 (MHT sai, mất bám) |
| `t3_vC` | A, giữ roll / pitch của init | 1.30 |
| `t3_vD` | A, quét yaw mịn +6…+24° | 1.48 |
| `t3_vE` | A + σ đo 1.0 | 1.50 |
| `t3_vF` | A + τ yaw 10 s | 1.29 |
| `t3_vG` | F + tầm 30 m | 1.37 |
| `t3_vH` | F + odometry gap 8 | 0.97 |
| `t3_vI` | F + bias dọc −0.27 | 1.13 |
| `t3_vJ` | F + gap 6 | 0.82 |
| `t3_vK` | gap 8 + bias −0.27 | 0.88 |
| `t3_vL` | gap 8 + bias −0.54 | 4.86 |
| `t3_vM` | F + gap 4 | 0.83 |
| **`t3_vN`** | **gap 6 + bias −0.27** | **0.77** (hạng 2; dẫn đầu 0.51) |

Bản đủ 3142 frame của cấu hình N: `src/localization/result/track3/t3_full_N.csv` (nộp 23/10 08:00: public **0.77**, như `t3_vN`; phần private 70–90 % chỉ biết điểm khi cuộc thi đóng).
Nhận xét: gap odometry ngắn hơn tốt hơn tới 6 (gap 4 ngang); bù đủ độ lệch dọc làm hỏng (bộ bám "trượt" dọc đường → bù cộng dồn).

## Track01 / Track02 – dò (được phép, 23/10)

| Lượt | Track | Cách | Dự đoán | Kaggle |
|---|---|---|---|---|
| `corr_r2_2` | 02 | sửa từ dao động 0–13 (đã có từ 21/10) | 0.153 | **0.15** (hạng 1) |
| `lb_t1_r3` | 01 | `tools/lb_combine.py`: 28 dao động + corr_r1 + 9 file pipeline mới, ridge λ 3e-4 | 0.33 | 0.42 |
| `probe_yaw1..4_1` | 01 | dao động cosin yaw bậc 1–4, biên độ 1.5° | – | 0.53 0.54 0.51 0.58 |
| `lb_t1_r4` | 01 | tổ hợp yaw 4 dao động (bậc 4 lớn nhất, a = −0.37) | 0.40 | **0.40** (bằng hạng 1) |
| `probe_x/y14..18_2` | 02 | dao động vị trí bậc 14–18 | – | 0.42–0.49 |
| `lb_t2_r3` | 02 | tổ hợp 41 hướng, ridge λ 1e-4 | 0.11 | **0.11** (hạng 1; nộp 23/10 08:00) |

Bài học: (1) nhiều hướng gần trùng (9 file pipeline) + điểm bị cắt 2 chữ số → hệ số ±4.6 khuếch đại sai số → dự đoán 0.33 thành 0.42;
mô phỏng Monte Carlo chỉ bắt được nhiễu độc lập. (2) hai file cùng vị trí (`posproj_t2_v1_2`, `lb_posyaw_v1_2`) làm G suy biến, hệ số
10¹⁴ → bộ giải giờ bỏ nghiệm có |a| > 20. (3) Track02 dự đoán khớp tốt (0.109 → 0.10–0.11) vì ít hướng gần trùng.

## Pipeline nhân quả cho Track01/02 (`tools/run_causal_pipeline.sh`) – chưa nộp

Kalman chỉ chạy tiến (`rts_smoother.py --causal`), yaw PI nhân quả (`tools/causal_yaw.py`, yaw bản đồ khi đứng yên), ghép GICP nhân quả
(`fuse_to_csv.py --causal`: trung vị 5 frame trước, trung bình chạy dần, EMA một phía), tỉ lệ trung vị trượt (`--ground-causal`).
So với bản clean: Track01 vị trí lệch 0.55 m, yaw 0.82°; Track02 vị trí 0.05 m, yaw 0.71° (đầu track vẫn 1.8°) → nếu luật nhân quả áp
dụng cho Track01/02 thì phải cải thiện tiếp; theo lời TA (23/10) chỉ Track03 bắt buộc.
