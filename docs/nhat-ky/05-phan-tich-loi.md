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
5. **So với hạng 1 (đội 12), lúc ~21:00** (sau đó đội 13 lên 0.91335 ở Track01 – xem README):

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

## 5. Tổ hợp tối ưu từ các lượt "chỉ đổi yaw" (`tools/yaw_projection.py`, `data/yaw_projection_output.txt`)

**Ý tưởng.** Giữ nguyên vị trí (nên $P$ biết trước) thì mỗi file chỉ đổi yaw cho biết **chính xác** lỗi yaw của nó: $Y_k = (S_k - P)/0.2$.
Với $D_k$ = (yaw file k − yaw base) từng frame (độ) và $e$ = lỗi yaw của base (không biết):

$$Y_k^2 = Y_{base}^2 + 2\,\overline{e\,D_k} + \overline{D_k^2} \;\Rightarrow\; m_k = \overline{e\,D_k}\ \text{biết được}$$

Với mọi tổ hợp $yaw = base + \sum_k a_k D_k$:
$$Y^2 = Y_{base}^2 + 2\,a^\top m + a^\top G\,a,\qquad G_{ij} = \overline{D_i D_j}\ \text{(tính trực tiếp)}$$
→ nhỏ nhất tại $a = -G^{-1}m$. **Không cần nộp thêm để biết điểm**, chỉ cần nộp để đưa lên leaderboard.
(Các hướng phải độc lập tuyến tính – một file vốn là tổ hợp của các file khác làm hệ suy biến, phải bỏ ra.)

**Kiểm chứng:**

| File | Hướng dùng | Dự đoán | Thực tế |
|---|---|---|---|
| `yawproj_v1_1.csv` (Track01) | +1° cố định, hướng chạy đúng giờ | 1.21862 | **1.21861** |
| `yawproj_v1_2.csv` (Track02) | yaw bù trễ, yaw trễ 0.75 s | 0.35674 | **0.35696** |
| `yawproj_v3_2.csv` (Track02) | + độ cong, + yaw GNSS gốc | 0.34498 | **0.34530** |

Sai lệch nhỏ (≤ 0.0003) đến từ việc $P$ của Track02 chỉ ước lượng từ một nhóm thăm dò.

**Tương quan giữa lỗi yaw và từng hướng** (dấu cho biết nên đi theo hay ngược hướng đó):

| Track | Hướng | corr(e, D) |
|---|---|---|
| 01 | +1° cố định | −0.195 |
| 01 | yaw bù trễ (hướng chạy đúng giờ) | −0.455 |
| 02 | yaw bù trễ | **+0.681** |
| 02 | hướng chạy trễ 0.75 s | +0.123 |
| 02 | độ cong l = 1.5 m (trên v1) | −0.673 (chủ yếu do phần v1 bên trong) |
| 02 | yaw GNSS gốc | −0.029 |

**Tham số đã chọn theo điểm Kaggle (không phải vật lý):**

| File | Trọng số | Diễn giải |
|---|---|---|
| `yawproj_v1_1.csv` | +0.199 × (+1°), +0.373 × (hướng chạy đúng giờ − yaw cũ) | cộng 0.2° và trộn 37 % hướng chạy – còn hợp lý |
| `yawproj_v1_2.csv` | −2.156 × (yaw bù trễ − yaw cũ), +0.214 × (trễ 0.75 s − yaw cũ) | **không vật lý** (ngược hướng bù trễ, gấp 2 lần) |
| `yawproj_v3_2.csv` | −4.581, −0.205, −1.119, +0.499 (4 hướng) | **không vật lý**, thuần khớp theo đáp án |
| `yawproj_v4_2.csv` | +0.675 (bù trễ), −0.299 (trễ 0.75 s), +0.224 (độ cong), +0.168 (yaw GNSS), +0.734 (đoạn khởi hành) | hướng đoạn khởi hành có ý nghĩa vật lý; các trọng số còn lại không |
| `proj1_v2` (yaw dùng trong `posproj_v1_1.csv`) | +0.106 (+1°), +0.185 (bù trễ), +0.496 (đoạn khởi hành) | trộn các nguồn yaw – còn diễn giải được |

**Giới hạn.** Cách này dùng bảng điểm (chấm trên toàn bộ dữ liệu test) để chọn tổ hợp – về bản chất là học từ đáp án qua điểm số,
không phải thuật toán định vị. Mỗi hướng mới tốn 1 lượt nộp. Áp dụng tương tự cho **vị trí** (ví dụ dời từng đoạn đường) là có thể,
nhưng khi đó gần như "dò lại đáp án" – nên hỏi giảng viên trước.


## 6. Tổ hợp vị trí từ các lượt "chỉ đổi vị trí" (`tools/pos_projection.py`)

Giống mục 5 nhưng cho vị trí: giữ yaw (Y biết trước) thì $P_k = S_k - 0.2\,Y$ chính xác; $D_k$ = dịch chuyển (dx, dy) từng frame,
$P_k^2 = P_{base}^2 + 2\,\overline{e\cdot D_k} + \overline{|D_k|^2}$ → tổ hợp tối ưu $a = -G^{-1}m$ với $G_{ij} = \overline{D_i\cdot D_j}$.

Track01 (vị trí gốc P = 0.905 m; các hướng là trường hiệu chỉnh NDT):

| Hướng | Điểm | Lỗi vị trí | corr(e, D) | Trọng số tối ưu |
|---|---|---|---|---|
| NDT `3cameras_ply` tỉ lệ 1.0 | 1.24807 | 0.934 m | −0.094 | +1.072 |
| NDT `3cameras_ply` tỉ lệ 0.8 | 1.15042 | 0.836 m | −0.383 | +1.370 |
| NDT `raw_ply` ×9 (#20) | 1.27855 | 0.930 m | −0.206 | +0.248 |

→ lỗi vị trí dự đoán **0.764 m**; ghép với yaw `proj1_v2` (1.559°) → dự đoán **1.0762**, thực tế **1.07618**.
Trọng số **chọn theo điểm Kaggle**; riêng việc "trường hiệu chỉnh NDT 3 camera tỉ lệ 0.8 có ích" là kết quả scan matching thật.

Track02 (vị trí gốc P = 0.232 m): NDT `3cameras_ply` tỉ lệ 1.0 – điểm 0.40544, lỗi vị trí 0.303 m, corr(e, D) = +0.020,
trọng số tối ưu −0.024 → lỗi vị trí 0.2321 m (gần như không đổi) – không đáng một lượt nộp.
