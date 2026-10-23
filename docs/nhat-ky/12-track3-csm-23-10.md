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
3. **Chỗ dừng cuối Track03** (likelihood phẳng, độ tương phản 0.10–0.15): IMU (tích phân ngược từ lúc dừng, 4 s) 3.86 m từ
   frame 2900. **Sửa lại (cùng ngày):** con số 6.2 m của A2h là *tổng độ dài đường đi* (gồm dao động qua lại); dịch chuyển
   thực là A2h 3.78 m, L2 3.40 m, L2b 3.45 m → cả ba đều khớp IMU, A2h **không** vượt 2–4 m như đã báo. CSM cả lúc đứng yên
   (`--csm-standing`) kéo vị trí đi ~4 m ở chỗ likelihood phẳng → không dùng.

**Ứng viên mới `t3_L2.csv`** (`bash tools/run_track3.sh`, tất định): chấp nhận 99 %, đỉnh likelihood −1.25 m so với tay đòn
−1.0 (sai số ±0.23), so với A2h: +0.5–0.65 m dọc ở 900 frame đầu (tay đòn), +1.5 m ở khúc cua. Không trợ giúp, Track01/02
vẫn lạc (RMSE 31 / 172 m, trước 165 / 393 m) – hai track này odometry hụt 40–60 % và có vùng cây cối, khó hơn Track03.

**Vấn đề còn lại của Track03:** lệch dọc / ngang còn lại ~0.2–0.3 m, yaw ±0.5°; khúc cua (frame 2200–2600) vẫn là chỗ
yếu nhất; pha MHT (chỉ public); không có đáp án → mọi đánh giá dựa trên bản đồ, IMU và Track01/02.

### 6b. Nộp `t3_L2` (người dùng duyệt): public **1.05** (A2h 0.96, N 0.77) – và vì sao tay đòn −1.0 sai cho Track03

Ở ~15 % frame đầu (phần public) L2 chỉ khác A2h ở chỗ dời lên trước ~+0.55 m (tay đòn mới) – yaw như nhau sau frame 75.
Không chỉnh theo bảng điểm; tìm lý do vật lý (`scale_check.py` trong scratchpad, CSM score theo hệ số tỉ lệ × lưới dọc/ngang):

| | hệ số tỉ lệ khớp bản đồ nhất | đỉnh dọc ở tỉ lệ 1.0 | đỉnh dọc ở tỉ lệ 0.9 |
|---|---|---|---|
| Track01 (pose đáp án) | **×0.90** (IQR 0.875–0.95) | −1.25 m | −0.25 m |
| Track02 (pose đáp án) | **×0.90** (IQR 0.875–0.95) | −0.88 m | 0.00 m |
| Track03 (pose A2h) | **×0.95** (IQR 0.925–1.05); ước lượng online ×0.925 | – | – |

→ point cloud LoGeR theo độ cao mặt đường dài hơn thật ~10 % (Track01/02), ~5–7.5 % (Track03); tay đòn −1.0 m chủ yếu là
hệ quả của sai tỉ lệ (tay đòn thật ≈ −0.12 m). Track03 sai tỉ lệ ít hơn → −1.0 sửa quá tay ≈ 0.4 m – khớp với điểm public.
Thử sửa tỉ lệ trực tiếp (`--scale-mult`, `--scale-online`, `--scale-freeze`): Track01/02 có trợ giúp tốt hơn (RMS khi bám
0.95 → 0.78 m, độ lệch ngang 0.50 → 0.31 m) nhưng Track03 mất bám ở khúc cua (chấp nhận 17–58 %) → độ sâu LoGeR sai theo
khoảng cách, một hệ số chung không đủ. Giữ tỉ lệ 1.0 và đặt tay đòn theo sai tỉ lệ đo trên chính Track03: −0.12 −
0.88·(sai tỉ lệ / 10 %) ≈ −0.56…−0.78 → **−0.7 (`t3_L2b.csv`, chấp nhận 99 %)**. τ yaw 30 s: khúc cua tệ hơn → giữ 10 s.

## 7. Tối 23/10 – nộp `t3_L2b`, clean Track01/02 bằng CSM, giới hạn độ chính xác

**Nộp (người dùng duyệt):** `t3_L2b` public **0.84** (A2h 0.96, L2 1.05; N cũ 0.77 vẫn là điểm hiện trên bảng). Yaw ở pha MHT
của L2b không bị "hụt" (A2h hụt −3° ở frame 50–75, L2 ở 25–50) → pha MHT còn phụ thuộc may rủi.

**Clean Track01/02 – `tools/csm_fuse.py`** (không dùng thông tin bảng điểm): quanh quỹ đạo clean, CSM (tỉ lệ ×0.9, tay đòn
−0.12 / +0.12, prior 0.5 m) cho độ lệch theo bản đồ mỗi frame; làm mượt có trọng số (độ tương phản) 3 s, bỏ trung bình.
Tham số đặt trước (không chọn theo bản dò; quét 1.5 / 3 / 6 s và prior 0.5 / 1.0 cho kết quả gần nhau).

| | trước | sau CSM (nộp) | dự đoán từ hiệu với bản dò | bản dò |
|---|---|---|---|---|
| Track01 `clean_csm_1` | 0.62 | **0.55** | 0.56 | 0.40 |
| Track02 `clean_csm_2` | 0.28 | **0.25** | 0.26 | 0.11 |

**Giới hạn độ chính xác của bộ bám không GNSS** (Track01/02 có trợ giúp, frame đang bám): RMS vị trí 0.90–1.06 m với mọi
thiết lập nhiễu (`--odo-noise 0.05`, `--sigma-match 1.0`, `--csm-kappa 30`) → giới hạn là hình học point cloud LoGeR, không
phải bộ lọc. Mô hình sai độ sâu theo khoảng cách p' = p(1 + 4c)/(1 + c r): c tốt nhất 0.008 / 0.004 / 0.004 (Track01/02/03),
tay đòn tại c = 0.004 vẫn khác 0.5 m giữa Track01 và Track02 → hiệu chuẩn dọc chỉ tới ±0.3 m. Point cloud 3 camera của
Track01/02 là MapAnything (~330 nghìn điểm / frame) – không chạy lại được cho Track03 trên GPU 6 GB của máy này.
Đầu Track03 (frame 0–150): đỉnh CSM −0.25…−1.0 m dọc (kỳ vọng −0.7), ngang 0…−0.25 m → không có lỗi lớn riêng ở đầu track.

## 8. Chiều 23/10 (16:40–17:40) – cấu hình W3h: yaw theo phương thẳng đứng, τ 30 s, giữ vị trí khi đứng yên

Luật Track03 (slide 10/20, đọc lại): "Public Score: Evaluates only the first 5–40% of the trajectory", **private (phần còn lại)
dùng để chấm và xếp hạng**, cần ≤ 1.40. Được phép "explore multi-camera images" (bag Track03 có 3 luồng ảnh h265).
Phần private của Track03: xe **đứng yên frame ~950–2150 = 45 % số frame private** → vị trí và yaw lúc đứng yên quyết định
phần lớn điểm private. Mọi so sánh dưới đây không dùng bảng điểm.

### 8.1 Những hướng đã kiểm tra và bỏ

| Hướng | Kiểm tra | Kết quả |
|---|---|---|
| Point cloud 3 camera (MapAnything, chỉ Track01/02) | `cache_ply.py --ply 3cameras_ply`, Track02 có trợ giúp | RMS vị trí khi bám 0.95 m (LoGeR 0.91) – chỉ ít lạc hơn (14 / 34 lần đặt lại) → nguồn point cloud không phải nút thắt |
| Bước lưới CSM 0.25 m / 1500 điểm CSM / `--odo-noise 0.08` | Track02 có trợ giúp | 0.90 / 0.92 / 0.92 m – không lợi |
| Course over ground của quỹ đạo bám làm mốc yaw | so với yaw tham chiếu Track01/02 | 1.0–2.2° RMS, kém yaw hiện tại (0.56–0.88°) |
| Quaternion hướng của IMU | so với yaw tham chiếu | trôi ~4° trên Track02 → không tuyệt đối |
| Vạch kẻ đường | `map.pcd` có intensity (vạch thấy rõ, `cache/Track3/map_corridor.npy`) | raw_ply quá thưa trên mặt đường, không thấy vạch → cần giải mã ảnh h265 (chưa làm) |
| CSM một frame lúc đứng yên (yaw × tỉ lệ × dọc × ngang) | 5 frame cùng khung cảnh | cực đại nhảy ±3°, ±1.5 m → không dùng để chốt vị trí đứng yên |
| Sàn độ lệch chuẩn dọc 0.7 m sau CSM | Track03 | lạc ở khúc cua → bỏ |

### 8.2 Bốn thay đổi giữ lại (mỗi cái thử riêng, trên Track01/02 có trợ giúp và trên Track03)

1. **Yaw rate theo phương thẳng đứng** (`--gyro-axis up`, `read_gyro_up`): trọng lực trong hệ IMU lúc đứng yên
   (−0.095, 0.041, 0.995) / (−0.098, −0.004, 0.995) / (−0.103, 0.019, 0.994) → IMU nghiêng ~6°; trục z chỉ thấy cos 6° của
   góc quay quanh phương thẳng đứng và trộn bias trục x / y. Yaw rate = véc-tơ gyro · hướng trọng lực (trung bình gia tốc kế
   của các mẫu đã qua – nhân quả). Bias prior −0.24 °/s (khớp theo hướng đi: Track01 −0.227, Track02 −0.250; trục z cũ
   −0.26 với tản mát −0.26…−0.30).
2. **τ yaw 30 s** (10 s trong 10 s đầu: các giả thuyết yaw đầu cách nhau 6° → sai số đầu tới ±3°): yaw GICP có sai số
   theo cảnh tương quan 2–15 s; τ dài lấy trung bình nhiều cảnh hơn.
3. **Phương sai tốc độ vào nhiễu dọc** (`--along-speed-noise 28`): CSM thay hiệp phương sai bằng độ rộng đỉnh cục bộ → trong
   khúc cua độ lệch chuẩn dọc co còn 0.39 m trong khi sai số thật ~2–3 m, prior chặn mất mode đúng (frame 2646: L2b nhảy
   −2.3 m về vị trí khớp bản đồ tốt hơn, bản gyro chiếu không nhảy → lệch 3 m trong 100 frame).
4. **Không cập nhật GICP khi đứng yên** (`--hold-position-standing`, giống `--hold-yaw-standing`): Track02 khởi đầu đúng
   vị trí tham chiếu, 230 frame đứng yên GICP kéo lệch −1.0 m dọc / +1.9 m ngang; Track03 kéo vị trí đứng yên lùi 0.3–0.5 m.

| Track01/02 có trợ giúp (frame đang bám) | RMS vị trí | RMS yaw |
|---|---|---|
| Track02 – L2b | 0.913 m | 0.88° |
| Track02 – τ 30 | 0.905 | 0.45 |
| Track02 – τ 30 + gyro chiếu | 0.886 | **0.40** |
| Track02 – W3h (cả 4) | 0.94 (cùng frame: 230–500 1.49 → 1.48, đứng yên 1.95 → 1.56) | 0.47 |
| Track01 – L2b | 1.019 | 0.64 |
| Track01 – τ 30 + gyro chiếu | 1.016 | **0.55** |
| Track01 – W3h | **1.003** | 0.67 (khác biệt ở frame 1200–1800 do lần đặt lại về tham chiếu khác nhau, không phải do cấu hình) |

### 8.3 Track03 – kiểm tra không có đáp án

Độ khớp bản đồ tại chính pose của quỹ đạo (`fit_at_pose.py` trong scratchpad: điểm trên mặt đường 0.4–3 m, tỉ lệ ×0.95,
tay đòn −0.4 m, không tìm kiếm; càng gần 0 càng tốt):

| Đoạn | L2b (đã nộp) | W3h |
|---|---|---|
| 0–157 | **−0.161** | −0.166 |
| 157–470 | −0.262 | **−0.244** |
| 470–950 | −0.220 | **−0.207** |
| 950–2150 (đứng yên) | −0.156 | **−0.138** |
| 2150–2300 (chạy lại) | −0.158 | **−0.145** |
| 2300–2450 | −0.553 | **−0.545** |
| 2450–2650 | −0.364 | **−0.331** |
| 2650–2850 | −0.047 | −0.047 |
| 3000–3142 (dừng cuối) | **−0.116** | −0.117 |

Nhất quán động học qua khúc rẽ trái 88°: yaw đứng yên + góc gyro = yaw bản đồ sau khúc cua → L2b cần bản đồ bù +1.43°
(yaw đứng yên thấp ~1°), bản τ 30 + gyro chiếu chỉ −0.02°. Course over ground trước khi dừng (frame 500–850): yaw đứng yên
≈ 159.15 ± 0.3° (L2b 158.80, W3h 159.47). Chạy lại với 6 / 10 luồng: trùng 100 %.

**Ứng viên `t3_W3h.csv`** (`bash tools/run_track3.sh`): chấp nhận 98 % frame đang chạy. Người dùng duyệt nộp (23/10 19:10):
**public 0.89** (L2b 0.84, A2h 0.96, L2 1.05, N 0.77). Ở phần public (đoạn đầu) W3h khác L2b chủ yếu ở yaw frame 0–157
(thấp hơn 0.31°) và dọc 0.14–0.24 m RMS; độ khớp bản đồ offline dự đoán hai bản gần bằng nhau ở đoạn này → thước đo khớp bản
đồ không phân biệt được chênh lệch cỡ 0.05 điểm. Các thay đổi của W3h nhắm phần private (đứng yên, khúc cua); điểm public
không đo được phần đó. Không chỉnh tiếp theo điểm public (luật 10/22).

**Còn mở:** khi xe chạy lại sau đứng yên (frame 2200–2306) vị trí dọc trễ ~3 m rồi CSM sửa ở 2306–2318 (cả L2b và W3h);
khúc cua vẫn là đoạn khớp kém nhất (−0.55); pha đầu (yaw MHT +0.8…1.2° so với yaw hội tụ).

## 9. Tối 23/10 (19:45–20:00) – nộp theo lời người dùng: Track01 vòng 5, ba biến thể Track03

Người dùng (23/10 tối): TA chỉ cấm sửa trực tiếp file kết quả mà không qua thuật toán; **chỉnh tham số / thuật toán Track03
theo điểm public là được**. Người dùng duyệt nộp các file đã nêu.

### 9.1 Track01 vòng 5 (dò – TA cho phép ở Track01/02)

| File dò (trên `lb_t1_r4`, 0.40) | Điểm | m = mean(e·D) | Ghi chú |
|---|---|---|---|
| yaw0 (lệch hằng 1.5°) | 0.61 | +0.193 | |
| yawrate (trễ τ·ω) | 0.50 | −0.023 | |
| gyroscale | 0.52 | +0.076 | |
| yaw5 / yaw6 / yaw7 / yaw8 (cosin bậc K) | 0.50 / 0.52 / **0.42** / 0.51 | −0.073 / +0.055 / **−0.485** / −0.010 | mode 7 chứa phần lớn sai số yaw còn lại |
| along / lateral (0.5 m) | 0.71 / 0.71 | +0.003 / +0.003 | vị trí: không còn lệch hằng theo thân xe |
| csm (`lb_t1_r4` + hiệu chỉnh `csm_fuse.py`) | 0.43 | −0.001 | khớp bản đồ không cải thiện được bản dò |

Ghép (`tools/lb_combine2.py`, P0 0.259): yaw 0.73° → 0.545° (hệ số lớn nhất 0.45 ở mode 7), vị trí giữ nguyên →
dự đoán 0.368 → **`lb_t1_r5` = 0.36** (đội 12: 0.40) → Track01 hạng 1. Vòng 6 đã tạo (chưa nộp): yaw9, yaw10 trên `lb_t1_r5`.

### 9.2 Track03 – lý do W3h kém L2b ở đoạn đầu, và ba biến thể (mỗi bản đổi 1 tham số so với W3h)

Hướng thẳng đứng tính nhân quả (trung bình gia tốc kế) lệch **8°** ở giây đầu Track03 (xe tăng tốc và rẽ ngay từ frame 0),
3.9° sau 2 s, 1.9° sau 5 s → bias trục gyro x (−0.45 °/s) rò vào yaw rate ~0.06 °/s → yaw đoạn đầu hụt 0.3°.

| Bản | Thay đổi so với W3h | Yaw 0–157 so với L2b | Public |
|---|---|---|---|
| **`t3_X3f`** | `--gyro-up=-0.0985,-0.0036,0.9951` (trọng lực lúc đứng yên Track02 – hiệu chuẩn hướng lắp IMU) | +0.11° | **0.80** |
| `t3_X3z` | `--gyro-axis z --gyro-bias -0.26` | +0.08° | 0.82 |
| `t3_X3l` | `--csm-bias-along -0.5` (dọc −0.2 m) | −0.80° | 0.95 |
| (W3h) | | −0.31° | 0.89 |
| (L2b) | | 0 | 0.84 |

Track01/02 có trợ giúp với hướng cố định: yaw Track01 0.665 → 0.608°, Track02 0.470 → 0.614° (Track02 đổi độ dốc dọc
đường; hướng cố định không theo); bias dạng véc-tơ (`--gyro-bias3`): Track01 0.512°, Track02 0.639°. Điểm public chọn X3f.

## 10. Tối 23/10 (20:00–20:25) – clean Track01: yaw theo bản đồ; Track03 đợt 3

**Chẩn đoán từ vòng dò 5:** bản clean Track01 mang nguyên sai số yaw chậm mode 7 (−0.71°, chu kỳ ~30 s) và mode 2 / 4
(+0.27 / +0.41°) – phần chậm của yaw lấy từ hướng GNSS. Bước mới (không dùng thông tin bảng điểm trong file):
`tools/raw_gicp_at_poses.py` (GICP point cloud LoGeR tại pose clean, như bộ bám Track03) + `tools/map_yaw_fuse.py`
(gyro cho phần nhanh, yaw GICP cho phần chậm, làm mượt Gauss có trọng số 8 s, bỏ xu hướng tuyến tính = bias gyro trước
khi làm mượt, giữ trung bình hướng GNSS).

| Track01, yaw so với `lb_t1_r5` (bản dò tốt nhất) | RMS | mode 2 / 4 / 7 |
|---|---|---|
| clean `clean_csm_1` (hướng GNSS, τ 7 s) | 0.672° | +0.27 / +0.41 / −0.71 |
| yaw GICP 3 camera, σ 8 s | 0.637° | +0.51 / +0.15 / −0.60 |
| **yaw GICP LoGeR, σ 8 s (`clean_mapyaw_1`)** | **0.485°** | +0.26 / +0.08 / −0.53 |
| yaw GICP LoGeR, σ 15 / 30 s | 0.66 / 0.87° | (yaw GICP có sai số chậm riêng) |

σ 8 s **chọn bằng cách so với bản dò** (ghi rõ trong báo cáo). Track02: cùng bước làm yaw kém đi (0.115 → 0.51°) – hướng
GNSS Track02 đã rất tốt → giữ nguyên. **Nộp: `clean_mapyaw_1` = 0.51** (clean Track01 trước: 0.55).

**Track03 đợt 3:** `t3_Y3a` (X3f + lưới giả thuyết yaw 2°; chỉ đổi frame 0–83: yaw thấp hơn 1.4° do giả thuyết +14…+16°
tạm dẫn đầu) = **0.82**; `t3_Y3c` (X3f + tay đòn −0.9; pha MHT cũng đổi: yaw frame 0–84 lệch RMS 2.7°) = **0.98**.
→ X3f (0.80) vẫn tốt nhất; điểm public rất nhạy với 84 frame đầu (pha MHT).

## 11. Tối 23/10 (20:30–21:00) – phần private Track03: hai lỗi của bộ lọc tốc độ / ZUPT (`t3_Z3a`)

Người dùng hỏi phần private có được cải thiện không → làm lỗi private lớn nhất còn mở: vị trí dọc trễ ~3–4 m khi xe chạy
lại sau 40 s đứng yên (frame 2200–2306). Chẩn đoán trên Track02 (cũng bắt đầu bằng đứng yên, có tham chiếu) và Track03:

1. **Odometry hỏng kéo tốc độ về 0** (Track02 frame 450–530: thật 5.7–6.5 m/s, bộ lọc 0.04–2.5 m/s): odometry LoGeR đọc
   0.05–0.3 m/s ở vùng cây, mà nhiễu đo đặt tỉ lệ với số đọc (0.25·v_odo + 0.3) → số đọc hỏng trông "chính xác" và qua
   cổng 3σ. Sửa `--speed-odo-low 0.5`: nhiễu theo max(số đọc, dự đoán), loại số đọc < 50 % tốc độ dự đoán (khi > 1.5 m/s).
   Track02 có trợ giúp: số lần lạc 32 → **15**, frame bám 62 → 72 %, RMS vị trí 0.951 → 0.905 m; Track01: 11 → 7 lần.
2. **ZUPT nhận nhầm tăng tốc đều là đứng yên**: điều kiện chỉ là độ lệch chuẩn gia tốc 0.5 s < 0.1, mà tăng tốc đều có độ
   lệch chuẩn nhỏ. Track03: tích phân gia tốc kế từ chỗ đứng yên (b = trung bình a_x lúc đứng yên) → xe tăng tốc đều
   ~1.2 m/s² từ frame 2175, đi 9.98 m tới frame 2300; ZUPT báo đứng yên ở frame 2220–2240 (xe đang 1.2 → 2.2 m/s) → tốc độ
   về 0 → bộ bám mới đi 5.95 m (trễ 4 m, CSM chỉ sửa được ở 2306–2318). Track02: xe bò 0.3–0.7 m/s ở frame 200–235 cũng bị
   coi là đứng yên. Sửa `--zupt-ax 0.3`: đứng yên còn cần |trung bình a_x − b| < 0.3 m/s² (b = trạng thái trọng lực / bias
   của bộ lọc tốc độ). Sau sửa: tốc độ bộ bám ở Track03 bám tích phân gia tốc kế (1.08 / 1.62 / 2.20 m/s so với
   1.19 / 1.67 / 2.20), quãng đường tới frame 2260 lệch < 0.4 m. Track01 RMS vị trí 0.996 → **0.964 m**, Track02 0.905 → 0.902.
   (Hạ ngưỡng ZUPT 0.1 → 0.06 thay vì sửa logic: trái chiều trên Track01/02 → bỏ.)

`t3_Z3a` (`bash tools/run_track3.sh`, = X3f + hai sửa đổi; tất định với 4 / 10 luồng): frame 0–2150 trùng X3f (phần public
giữ ~0.80), khác ở 2150–2650 (chạy lại + khúc cua). Độ khớp bản đồ: 2150–2300 −0.183 (X3f −0.149; độ tương phản CSM ở
đoạn này chỉ 0.10–0.15 → dọc đường gần như không đo được), 2300–2450 **−0.480** (X3f −0.555), 2850–3142 tốt hơn nhẹ.
Chưa nộp – chờ người dùng.

**Ước lượng lợi ích private của `t3_Z3a`** (frame 2175–2300, mốc = tích phân gia tốc kế từ chỗ đứng yên; `private_gain.py`
trong scratchpad): sai số dọc X3f RMS 2.46 m (trễ tới 4.23 m), Z3a 0.72 m → phần vị trí của điểm private giảm ~0.13–0.21
(giả định sai số vị trí ở các đoạn khác 0.5–0.8 m, 2670–2985 frame private). Không tính khúc cua 2300–2650 (không có mốc).
Các thay đổi private trước đó (W3h) không quy ra điểm được – chỉ có độ khớp bản đồ / tính nhất quán / Track01/02.
**Nộp (người dùng duyệt, 23/10 21:01): `t3_Z3a` public 0.80** (= X3f, như dự kiến – phần public trùng X3f).

## 12. Đêm 23/10 (23:45) – nộp nốt lượt trong ngày (người dùng duyệt)

**Track02 clean – 13 biến thể của `clean_csm_2` (0.25), mỗi bản 1 tham số** (dự đoán offline = so với `lb_t2_r3`):

| Biến thể | Kaggle | Offline (vị trí, m) |
|---|---|---|
| **trễ GNSS −10 ms (`tools/time_shift.py --dt -0.01`)** | **0.24** | 0.192 (clean 0.201) |
| τ yaw 10 s | 0.25 | – |
| tay đòn CSM 0 / không bỏ trung bình / τ yaw 25 s / gyro chiếu trọng lực | 0.26 | 0.205 / 0.204 / – / – |
| σ CSM 6 / 1.5 s, κ 30, tỉ lệ 0.85 | 0.27 | 0.212 / 0.223 / 0.218 / 0.218 |
| prior CSM 1.0 m | 0.28 | 0.232 |
| trễ GNSS −20 ms | 0.29 | 0.242 |
| tỉ lệ 0.95 | 0.33 | 0.275 |

Thứ tự Kaggle khớp thứ tự offline. **Clean Track02 tốt nhất: `t2v_tsm10` = 0.24.** (Lưu ý: +20 / +40 ms làm kém
hẳn offline – đã sửa dấu trước khi nộp.)

**Track01 clean:** yaw theo bản đồ σ 6 s và σ 4 s: cả hai 0.51 (= σ 8 s) – không phân biệt được ở 2 chữ số.

**Track03:** trên `t3_Z3a` (0.80): yaw offset 0.36° → 0.81; tay đòn ngang −0.08 m → 0.82 → giữ 0.66° / +0.12 m (tay
đòn dọc: −0.5 → 0.95, −0.9 → 0.98 → giữ −0.7). Các biến thể tăng yaw offset / tay đòn ngang làm pha MHT đổi giả thuyết
(yaw 84 frame đầu lệch RMS 2.4–5°) → không nộp (điểm sẽ phản ánh pha MHT, không phản ánh tham số). Còn 2 lượt Track03 để trống.
