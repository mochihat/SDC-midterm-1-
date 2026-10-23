# 12 – 23/10: Track03 – sửa lỗi gyro, ZUPT, khớp lưới (CSM); dò Track01 vòng 5

Người dùng (23/10): "tối ưu track 1 và track 3 … track 3 có một đoạn private nên hãy cố gắng track 3 nhiều nhất có thể".
Track03 vẫn tuân thủ luật 10/22 (nhân quả, không dò); Track01 dò được (TA cho phép).

## 1. Chẩn đoán Track03 (không có đáp án → dùng bản đồ, IMU, hình học)

Công cụ mới: `tools/cache_ply.py` (raw_ply ASCII → mảng nhị phân, một lần ~15 s/track; bộ bám từ 0.5–1.7 s/frame xuống
0.03 s/frame → một lượt Track03 ~2 phút), `--diag` của `tools/track_localize.py` (mỗi frame: chấp nhận, innovation,
inliers, yaw GICP − yaw bộ bám, odometry, cộng dồn gyro / kéo yaw bản đồ, đứng yên, đang quay).

| Phát hiện | Bằng chứng | Hậu quả với `t3_full_N` |
|---|---|---|
| **MHT không nhân quả**: chọn giả thuyết ở frame ~60–80 rồi ghi lại quỹ đạo quá khứ của nó | đọc code | vi phạm luật cho ~80 frame đầu → **đã sửa**: mỗi frame ghi giả thuyết tốt nhất *tại frame đó* |
| **Lỗi tích phân gyro**: bỏ đoạn từ mẫu IMU cuối tới thời điểm frame (IMU 100 Hz, ảnh 28 Hz) | cộng dồn gyro của bộ bám = 86 % tích phân chuẩn; khúc cua 90° chỉ quay 77° | yaw sau khúc cua lệch −12° → đi lệch khỏi đường 20 m; **đã sửa** |
| Xe đứng yên frame ~1000–2150 (đèn đỏ) và cuối track | độ lệch chuẩn gia tốc 0.02–0.05 m/s² (chạy: 0.3–1.3) | bias gyro đo được −0.278 °/s (hiệu chuẩn −0.26) |
| **Trôi dọc đường 29 m trước chỗ dừng** | (a) "bản đồ độ khớp" dọc đường (tỉ lệ điểm trên mặt đường nằm gần cấu trúc bản đồ, yaw cố định): đỉnh lệch −1 m (frame 300) → −13.5 (600) → −21 (700) → −28.5 (800) → −29 m (dừng); (b) tích phân gia tốc kế ngược từ lúc dừng: từ frame 600 tới chỗ dừng 75 ± 8 m, bộ bám 96 m; (c) sau khúc rẽ trái quỹ đạo song song đường chéo nhưng lệch 20 m về phía tây (vùng không có đường) | toàn bộ phần sau frame ~500 (phần lớn private) sai 13–30 m |
| Odometry scan-to-scan LoGeR không ổn định | Track01/02 (có đáp án): tỉ lệ quãng đường odometry / thật 0.12–1.16 theo đoạn | nguyên nhân gốc của trôi dọc đường |

## 2. Thuật toán mới (đều nhân quả)

1. **ZUPT** (`--zupt-acc 0.1`): đứng yên khi độ lệch chuẩn gia tốc 0.5 s gần nhất < 0.1 m/s² → không dịch chuyển, không đổi yaw;
   **bias gyro online** (`--bias-online 500`): ước lượng lại từ các mẫu lúc đứng yên.
2. **Khớp lưới tương quan (CSM, Olson 2009)** (`--csm-window 15`): trường xác suất 2D (Thrun "likelihood field") của các điểm
   bản đồ cao 0.4–3 m trên mặt đất; điểm của point cloud trong cùng dải cao, ở yaw dự đoán, được chấm trên lưới dọc ±15 m
   (cắt theo 3σ dự đoán) × ngang ±2 m; nhân với prior Gauss của dự đoán → hậu nghiệm trên lưới → trung bình / hiệp phương sai
   thay cho vị trí. GICP chạy tiếp từ đó như cũ. CSM "nhìn thấy" vị trí đúng cách xa tới 15 m, GICP chỉ 1–2 m.

## 3. Kết quả Track03 (không có đáp án – các kiểm tra độc lập)

| Bản | Chấp nhận GICP | Inliers phần cuối | Ghi chú |
|---|---|---|---|
| `N_causal` (= t3_full_N, MHT nhân quả) | 69 % (đoạn 2500–3000: 24 %) | 90–600 | lạc sau frame ~500 |
| `F1` (+ sửa gyro, ZUPT, bias online) | 65 % | 90–600 | yaw đúng nhưng vị trí vẫn trôi |
| **`C3` (+ CSM ±15 m, κ 15)** | **98 %** | **1450–2200** | dừng đúng chỗ đồ thị độ khớp chỉ ra, rẽ trái vào đúng đường chéo, bám đường tới cuối |

Kiểm tra độc lập của C3: quãng đường frame 600 → dừng 72 m (IMU 75 ± 8 m); chạy lại / đổi số luồng: trùng 100 % (tất định).

### 3b. Độ vững: GICP trượt dọc đường → nhiễu đo bất đẳng hướng

Đổi một tham số nhỏ (bias dọc −0.52 thay −0.27, hoặc σ đo 0.5) làm C3 lạc ở frame ~470–1000 (lệch 22–30 m, chấp nhận
còn 40 %). Nguyên nhân (đọc `--diag`): odometry vẫn đúng (0.38–0.44 m/frame) nhưng mỗi frame GICP hội tụ trước dự đoán
~1.1 m, vẫn qua cổng → 11 m sau 12 frame. **Sửa:** `--sigma-match-along 2` – GICP chỉ tin 0.7 m theo phương ngang, 2 m theo
phương dọc (dọc đường do CSM lo). Sau đó mọi biến thể (bias −0.27 / −0.52, σ 0.5 / 0.7, σ dọc 2 / 4) đều bám 96–99 % và
khớp nhau ±0.5 m (chỗ bắt đầu rẽ ±1–3 m, lúc dừng cuối ±1–2 m).

`--hold-yaw-standing`: khi đứng yên không kéo yaw về yaw GICP (các phép đo của cùng một khung cảnh có chung sai số):
yaw − gyro giữ −0.9° suốt 45 s dừng (trước: trôi tới −2.4°).

**Ứng viên Track03: `t3_A2h.csv`** = `bash tools/run_track3.sh` (bộ đệm + bộ bám; chạy lại / đổi số luồng: trùng 100 %),
chấp nhận 99 %, yaw 100 frame đầu 2.1° RMS so với yaw gyro truy ngược (bản "trung bình hậu nghiệm" 3.0°).

### 3c. Nộp `t3_A2h` (người dùng duyệt, 23/10 ~12:45): public **0.96** (bản N: 0.77)

So từng frame với N: frame 0–450 hai bản lệch nhau < 1 m (không có hướng hệ thống); từ 450 A2h lùi 6 → 30 m (phần sửa trôi).
Vì N lệch 6–30 m sau frame ~470 mà vẫn được 0.77, phần public chỉ có thể nằm trong ~15 % frame đầu (A2h cũng chỉ 0.96).
Chênh 0.19 khớp với ~25 frame (50–75) của pha MHT: bản nhân quả xuất giả thuyết +12° (đang tốt nhất lúc đó), lệch ~5° so
với N – N "đẹp" ở đây chính vì ghi ngược kết quả của giả thuyết thắng (không hợp lệ). Đoạn này không thuộc private.
Thử τ yaw nhanh trong pha MHT (`--tau-yaw-start 1/3`, lưới 3°): không rõ tốt hơn (yaw sau đó lệch −1.4…−2.6°) → giữ A2h;
không dùng thêm lượt nộp để chỉnh pha đầu theo bảng điểm (sẽ là leaderboard fitting).
**Phải chọn tay `t3_A2h` làm "Use for Final Score"** – nếu để Kaggle tự chọn theo public, nó lấy N (private rất tệ).

## 4. Kiểm thử không GNSS trên Track01/02 (so với bài tốt nhất)

| Bản | Track01 đoạn 1–4 / 5–10 | Track02 |
|---|---|---|
| F1 | 4.3–23 m / 35–223 m | lạc từ đoạn 2 |
| C3 | **1.3–4.3 m** / 41–300 m | MHT chọn sai yaw đầu (xe đứng 13 s lúc đầu) |
| C3 bắt đầu từ pose đáp án (chỉ để đo sai lệch) | 2.6 / 9.6 / 2.9 / 2.6 m, rồi lạc | lạc từ đoạn 2 (odometry chỉ 55 %) |

Track01/02 khó hơn Track03 (odometry hụt 40–60 % trong vùng cây, đồ thị độ khớp phẳng): ở đó tỉ lệ chấp nhận rơi 14–35 %,
còn Track03 giữ 96–99 % → tỉ lệ chấp nhận là chỉ báo bám / lạc dùng được. Đã thử và **bỏ** (kém hơn trên Track01/02):
`--odo-filter` (tốc độ là trạng thái Kalman), `--csm-mode kalman`, `--mht-score csm`; bộ lọc hạt `tools/mcl_localize.py`
(tốc độ sụp về 0 ở vùng đồ thị độ khớp phẳng). Đoạn đã bám của Track01: lệch dọc −1.0 m, ngang +0.4 m, yaw −0.6°
(một track, chưa đủ để hiệu chuẩn lại Track03).

## 5. Track01 vòng 5 (dò, đã chuẩn bị – chờ người dùng duyệt nộp)

`tools/make_probes_phys.py`: hướng có hình dạng vật lý trên gốc `lb_t1_r4` (0.40): yaw lệch hằng, yaw trễ (τ·ω), sai tỉ lệ gyro
(phần cao tần 7 s của góc tích phân), yaw cosin bậc 5–8, vị trí lệch dọc / ngang thân xe (bỏ "trễ thời gian vị trí": tương quan
0.96 với lệch dọc). Ghép: `tools/lb_combine2.py` (ridge, chọn λ theo Monte Carlo với nhiễu cắt 2 chữ số và sai số P₀).

## 6. Chiều 23/10 – chẩn đoán clean Track01/02 và Track03 vòng 2 (cấu hình L2)

### Clean Track01/02 khác bản dò ở đâu (bản dò gần đáp án hơn → hiệu = lỗi của bản clean, chỉ để chẩn đoán)

| | Track01 clean 0.62 vs `lb_t1_r4` 0.40 | Track02 clean 0.28 vs `lb_t2_r3` 0.11 |
|---|---|---|
| Ước lượng lỗi bản clean | P ≈ 0.48 m, Y ≈ 0.83° | P ≈ 0.24 m, Y ≈ 0.19° |
| Hiệu vị trí | 0.40 m RMS; phần nhanh (< 10 s) lớn hơn phần chậm (ngang 0.27 / 0.10 m) | 0.22 m; dọc đường tỉ lệ tốc độ (+0.020 s ≈ GNSS lệch thời gian 20 ms) và 0.42 m lúc đứng yên đầu track |
| Hiệu yaw | 0.40° (chậm 0.28°); 1/10 cuối 0.91° | 0.12° |
| Ghi chú | bản dò cũng chứa nhiễu nhanh (ghép 9 file pipeline hệ số ±4.6) → phần nhanh chưa chắc là lỗi clean | GICP (camera) không đủ chính xác để đo 20 ms (lệch theo vị trí, ngược dấu giữa 2 track) |

### Track03 vòng 2

1. **Hiệu chuẩn tay đòn camera của CSM** (`--csm-bias-along -1.0 --csm-bias-lat 0.12`): đỉnh likelihood tại pose đáp án nằm
   **−1.00 m** dọc (trung vị) trên **cả Track01 và Track02** (bộ bám giả định −0.27) ↔ chạy "có trợ giúp" (`--reset-ref`,
   chỉ Track01/02: lạc > 3 m thì đặt lại về đáp án, đo lệch khi đang bám): dọc −0.67 / −0.70 m → sau hiệu chuẩn −0.30 / −0.06 m.
2. **Bộ lọc tốc độ IMU** (`--speed-filter`, class `SpeedFilter`): trạng thái [v, b]; dự đoán bằng gia tốc dọc; đo: ZUPT,
   tốc độ hướng tâm a_y/ω khi quay > 5°/s, odometry có cổng 3σ. Lý do: trong khúc cua Track03 odometry nhảy 2 ↔ 11 m/s giữa
   các frame, còn a_y/ω mượt (2.2 → 5.9 → 7.3 m/s). Track01/02 có trợ giúp: số lần lạc 49 → 9 / 80 → 33, frame bám 52 → 77 %
   / 38 → 59 %; sai số tốc độ Track01 5.55 → 1.27 m/s RMS.
3. **Chỗ dừng cuối Track03**: A2h đi 6.2 m từ frame 2900, IMU (tích phân ngược từ lúc dừng, 4 s) chỉ 3.9 m → vượt 2–4 m
   (likelihood phẳng, độ tương phản 0.10–0.15). L2: dịch chuyển thực 3.40 m (IMU 3.86) từ 2900, 0.54 m (IMU 0.69) từ 2950.
   CSM cả lúc đứng yên (`--csm-standing`) làm tệ hơn ở chỗ likelihood phẳng → không dùng.

**Ứng viên mới `t3_L2.csv`** (`bash tools/run_track3.sh`, tất định): chấp nhận 99 %, đỉnh likelihood −1.25 m so với tay đòn
−1.0 (sai số ±0.23), so với A2h: +0.5–0.65 m dọc ở 900 frame đầu (tay đòn), +1.5 m ở khúc cua. Không trợ giúp, Track01/02
vẫn lạc (RMSE 31 / 172 m, trước 165 / 393 m) – hai track này odometry hụt 40–60 % và có vùng cây cối, khó hơn Track03.

**Vấn đề còn lại của Track03:** lệch dọc / ngang còn lại ~0.2–0.3 m, yaw ±0.5°; khúc cua (frame 2200–2600) vẫn là chỗ
yếu nhất; pha MHT (chỉ public); không có đáp án → mọi đánh giá dựa trên bản đồ, IMU và Track01/02.
