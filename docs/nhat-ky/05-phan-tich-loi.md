# 05 – Tách điểm Kaggle thành lỗi vị trí và lỗi yaw

Script: `tools/analyze_probes.py` – kết quả: `data/probe_analysis.txt`.

## 1. Ý tưởng

Điểm = $P + 0.2\,Y$, với $P$ = RMSE vị trí (m), $Y$ = RMSE yaw (độ). Kaggle chỉ cho tổng, không cho biết $P$ và $Y$ riêng.
Một **file thăm dò** = file tốt nhất bị thay đổi theo một cách **biết trước** (dịch thời gian, dời ngang, cộng yaw). Với sai số $e_i$ của từng frame:

$$P(\Delta t)^2 = P^2 + 2\,\Delta t\,\overline{e\cdot v} + \Delta t^2\,\overline{|v|^2}\qquad\text{(dịch thời gian, } v = \text{vận tốc)}$$
$$P(L)^2 = P^2 + 2\,L\,\overline{e\cdot n} + L^2\qquad\text{(dời ngang } L,\ n = \text{pháp tuyến trái)}$$
$$Y(d)^2 = Y^2 + 2\,d\,\overline{e_\theta} + d^2\qquad\text{(cộng yaw } d\text{)}$$

Nộp một cặp $+$/$-$ thì số hạng chéo triệt tiêu khi cộng lại, ví dụ $P(+L)^2 + P(-L)^2 - 2P^2 = 2L^2$.
Phương trình này chỉ còn **một ẩn**: phần điểm của yaw $c = 0.2\,Y$ trong điểm gốc (vì $P = S_0 - c$).
→ **Mỗi nhóm thăm dò cho một ước lượng độc lập của $c$**; hiệu hai phía cho độ lệch tối ưu (thời gian / ngang / yaw).

## 2. Kết quả

### Track01 (file gốc `rts_pos_gnssyaw_1.csv`, điểm 1.25992; tốc độ RMS 10.11 m/s)

| Nhóm thăm dò | $c$ | RMSE vị trí | RMSE yaw | Độ lệch tối ưu |
|---|---|---|---|---|
| Thời gian ±0.1 s | 0.3540 | 0.906 m | 1.77° | Δt = **−3.6 ms** |
| Ngang ±0.5 m | 0.3552 | 0.905 m | 1.78° | **+0.025 m** (sang trái) |
| Yaw ±1° | 0.3553 | 0.905 m | 1.78° | **+0.347°** |

- Ba ước lượng **độc lập** của $c$ nằm trong khoảng 0.3540–0.3553 (chênh 0.0014) → cách tách lỗi rất đáng tin.
- **Kiểm chứng bằng dự đoán:** mô hình dự đoán `phys_yawb_1.csv` (cộng 0.42°) được **1.25339**, Kaggle cho **1.25338**.
- Sau khi bỏ lệch yaw: Track01 ≈ **0.905 m + 1.74°** (= 1.2534).

### Track02 (file gốc `rts_heading_2.csv`, điểm 0.40778; tốc độ RMS 11.29 m/s)

| Nhóm thăm dò | $c$ | RMSE vị trí | RMSE yaw | Độ lệch tối ưu |
|---|---|---|---|---|
| Thời gian ±0.1 s | 0.1756 | 0.232 m | 0.88° | Δt = **−4.7 ms** |

Chỉ có một nhóm thăm dò, và ở Track02 file dịch thời gian dịch cả yaw (yaw đổi ~0.10° RMS, đã bỏ qua) → kém chắc chắn hơn Track01.

## 3. Ý nghĩa

1. **Thời gian ảnh–GNSS đã đồng bộ** (lệch vài ms; 1 ms ở 10 m/s = 1 cm). Không cần chỉnh.
2. **Không có lệch ngang cố định** (0.025 m) → không phải do vị trí lắp ăng-ten.
3. **Có lệch yaw cố định ở Track01 ≈ +0.35°**, khớp với độ lệch b = −0.42° mà bộ lọc Kalman ước lượng từ dữ liệu (không cần Kaggle).
   Dùng 0.42° hay 0.347° cho điểm gần như như nhau (chênh < 0.0002), nên chọn giá trị vật lý.
4. **Track01: lỗi vị trí ~0.9 m** không do thời gian, không do lệch ngang → là sai số **thay đổi chậm theo đoạn đường** của GNSS Track01.
   Làm mượt không khử được (không phải nhiễu trắng); NDT trên ảnh cũng không khử được (mục 03).
5. **So với hạng 1 (đội 12):**

| | Điểm hiện tại | = vị trí + 0.2 × yaw | Hạng 1 | Nếu giữ vị trí, yaw cần |
|---|---|---|---|---|
| Track01 | 1.25338 | 0.905 + 0.2 × 1.74° | 1.00423 | **≈ 0.50°** |
| Track02 | 0.40778 | 0.232 + 0.2 × 0.88° | 0.33283 | **≈ 0.50°** |

Ở **cả hai track**, chỉ cần yaw đạt ~0.5° là bằng hạng 1 với cùng sai số vị trí → **yaw là chỗ đáng cải thiện nhất**.
(Phỏng đoán: đội 12 có thể có vị trí tương tự nhưng yaw tốt hơn.) Để vượt đội 3 ở Track01 (1.22369) chỉ cần bớt 0.03 điểm,
ví dụ yaw từ 1.74° xuống ~1.59°.

## 4. Giả định và giới hạn
- Công thức điểm đúng như slide ($k = 0.2$, yaw tính bằng độ). Các kiểm tra tổng ($2L^2$, $2d^2$) khớp, nên điều này được xác nhận.
- Dịch thời gian 0.1 s được xấp xỉ tuyến tính (vận tốc không đổi trong 0.1 s).
- Các lượt thăm dò **chỉ dùng để đo**, không lấy tham số Kaggle nào đưa vào file cuối (Δt, lệch ngang giữ 0; yaw dùng giá trị vật lý 0.42°).
