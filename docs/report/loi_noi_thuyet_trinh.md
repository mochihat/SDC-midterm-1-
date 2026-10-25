# Lời nói thuyết trình Midterm01 (29/10, 4–6 phút)

Slide: `docs/report/presentation_midterm01.pptx` (8 trang, tạo lại bằng `python3 docs/report/make_presentation.py`).
Lời tiếng Anh dưới đây cũng nằm trong phần **Notes** của từng slide trong PowerPoint (bật Presenter View để vừa nhìn
slide vừa đọc). Tổng khoảng 780 từ, tức khoảng 5,5 phút nếu nói 140 từ/phút. Nếu bị giới hạn 4 phút, rút gọn slide 3 và 4 trước.

| Slide | Nội dung | Thời gian |
|---|---|---|
| 1 | Tiêu đề | 0:20 |
| 2 | Bài toán, công thức điểm | 0:30 |
| 3 | Pipeline Track 01/02 | 0:45 |
| 4 | Dò bảng điểm (TA cho phép ở Track 01/02) | 0:40 |
| 5 | Track 03: ba tầng | 0:40 |
| 6 | Tầng 2: khớp vạch sơn | 0:45 |
| 7 | Tầng 3: IMU cho vị trí dọc | 0:45 |
| 8 | Kết quả, bài học | 0:30 |

Số cần nhớ: Track01 0.36 (hạng 1, pipeline 0.51), Track02 0.11 (hạng 1, pipeline 0.24), Track03 0.28 (hạng 2 public).
Track03: 0.80 (bộ bám bản đồ LiDAR) → 0.33 (vạch sơn) → 0.28 (IMU).

---

## Slide 1 – Tiêu đề

**EN:** Hello, I'm team 11 and I worked alone, with an AI coding assistant. The task is to estimate the car's x, y and yaw
for every camera frame against a pre-built LiDAR map. I'll show the pipeline for Tracks 01 and 02 and how I used the
leaderboard there; most of the time goes to Track 03, which has no GNSS.

**VI:** Xin chào, em là đội 11, làm một mình, có dùng trợ lý lập trình AI. Bài toán là ước lượng x, y và góc yaw của xe
cho từng frame camera, so với một bản đồ LiDAR có sẵn. Em sẽ trình bày pipeline của Track 01 và 02, cách em dùng bảng
điểm ở hai track đó; phần lớn thời gian dành cho Track 03, track không có GNSS.

## Slide 2 – Bài toán và điểm

**EN:** There are three tracks. Tracks 01 and 02 have GNSS and IMU. Track 03 has no GNSS, the localization must be causal,
and it is graded on a hidden private part, about 87 percent of the frames. The score adds position RMSE in metres and 0.2
times yaw RMSE in degrees, so one degree of yaw costs as much as 20 centimetres.

**VI:** Có ba track. Track 01 và 02 có GNSS và IMU. Track 03 không có GNSS, phải định vị nhân quả (chỉ dùng frame hiện tại
và quá khứ), và được chấm trên phần private bị ẩn, khoảng 87% số frame. Điểm bằng RMSE vị trí (mét) cộng 0,2 lần RMSE
yaw (độ), nên lệch 1 độ yaw bị phạt bằng lệch 20 cm vị trí.

## Slide 3 – Pipeline Track 01/02

**EN:** For Tracks 01 and 02 the first finding was the scale: the baseline scaled the point clouds by 3, but the camera
height above the road says about 9, so every frame is rescaled by the road height. Then GNSS goes through a Kalman filter
and RTS smoother; GICP against the map refines the position, only within 20 metres because image depth gets worse with
range; correlative map matching fixes the along-road position; and the yaw comes from the gyro, with the slow part from
the map. Track 01 went from 1.79 to 0.51, Track 02 from 1.93 to 0.24.

**VI:** Với Track 01 và 02, phát hiện đầu tiên là tỉ lệ: baseline nhân point cloud với 3, nhưng độ cao camera so với mặt
đường cho thấy phải khoảng 9, nên mỗi frame được chỉnh tỉ lệ theo độ cao mặt đường. Sau đó GNSS đi qua bộ lọc Kalman và
bộ làm mượt RTS; GICP với bản đồ tinh chỉnh vị trí, chỉ trong phạm vi 20 m vì độ sâu từ ảnh kém dần theo khoảng cách;
khớp bản đồ kiểu tương quan (correlative) sửa vị trí dọc đường; còn yaw lấy từ con quay hồi chuyển (gyro), phần thay đổi
chậm lấy từ bản đồ. Track 01 từ 1,79 xuống 0,51; Track 02 từ 1,93 xuống 0,24.

## Slide 4 – Bảng điểm như một phép đo

**EN:** The TA allowed using the leaderboard on Tracks 01 and 02. Because the score is an RMSE, adding a known change to a
file and reading the new score measures how the hidden error projects onto that change. That showed that yaw was the
larger error and that the pipeline yaw had a slow 30-second error, which I then fixed in the pipeline with map yaw. With
probing, both tracks rank first, 0.36 and 0.11; the pipeline alone gives 0.51 and 0.24, and the report keeps the two
apart; the one pipeline constant chosen against a probed file, the map-yaw time constant, is labelled too. I never did
this on Track 03.

**VI:** TA cho phép dùng bảng điểm ở Track 01 và 02. Vì điểm là RMSE, nên khi cộng một thay đổi đã biết vào file rồi đọc
điểm mới, ta đo được hình chiếu của sai số ẩn lên thay đổi đó. Cách này cho thấy yaw là sai số lớn hơn, và yaw của
pipeline có một sai số chậm chu kỳ khoảng 30 giây; em đã sửa nó ngay trong pipeline bằng yaw theo bản đồ. Có dò bảng
điểm, cả hai track đều hạng 1, 0,36 và 0,11; riêng pipeline được 0,51 và 0,24, và báo cáo tách riêng hai loại này; hằng
số duy nhất của pipeline được chọn theo file dò (hằng số thời gian của yaw theo bản đồ) cũng được ghi rõ. Em không làm
việc này ở Track 03.

## Slide 5 – Track 03: ba tầng

**EN:** Track 03 is built in three layers, and every output uses only the current and past frames. First, a LiDAR-map
tracker: several yaw hypotheses at the start, an IMU speed filter, the gyro projected on gravity because the IMU is tilted
6 degrees, and scan matching on the map. Debugging it with physics instead of ground truth brought the public score to
0.80. The two layers on top use the cameras and took it to 0.28. Their constants were tuned on the public score, which the
TA allows; the output files are never edited.

**VI:** Track 03 gồm ba tầng, và mọi kết quả chỉ dùng frame hiện tại và quá khứ. Tầng một là bộ bám theo bản đồ LiDAR:
nhiều giả thuyết yaw lúc khởi đầu, bộ lọc tốc độ từ IMU, gyro chiếu lên phương trọng lực vì IMU lắp nghiêng 6 độ, và khớp
quét (scan matching) với bản đồ. Gỡ lỗi bằng vật lý thay vì đáp án đưa điểm public về 0,80. Hai tầng phía trên dùng camera
và đưa điểm xuống 0,28. Các hằng số của chúng được chỉnh theo điểm public, việc TA cho phép; file kết quả không bao giờ
bị sửa tay.

## Slide 6 – Tầng 2: khớp vạch sơn

**EN:** The LiDAR map also stores intensity, and road paint is bright in it: lane lines, stop lines, crosswalks, accurate to
a few centimetres. The bag contains three camera videos. For every frame I project the map's road surface into each
fisheye image, keep only thin bright structures, and correlate this camera paint with the map paint over shifts of plus or
minus 2 metres. That gives a likelihood for the car's position, which a causal error-state filter combines with the
tracker. Here, at a red light, the tracker was 0.66 metres off; after matching, the waiting box lines up. Public score
0.80 to 0.33.

**VI:** Bản đồ LiDAR còn lưu cường độ phản xạ, và vạch sơn trên đường hiện rất sáng trong đó: vạch làn, vạch dừng, vạch
sang đường, chính xác tới vài cm. File bag có video của ba camera. Với mỗi frame, em chiếu mặt đường của bản đồ vào từng
ảnh fisheye, chỉ giữ các cấu trúc sáng và mảnh, rồi tính tương quan giữa vạch sơn thấy qua camera với vạch sơn trong bản
đồ, trên các độ dời ±2 m. Kết quả là một hàm khả năng (likelihood) cho vị trí xe; một bộ lọc sai số trạng thái
(error-state filter) nhân quả kết hợp nó với bộ bám. Ở hình này, xe đang dừng đèn đỏ, bộ bám lệch 0,66 m; sau khi khớp,
ô chờ xe máy trùng khít. Điểm public từ 0,80 xuống 0,33.

## Slide 7 – Tầng 3: IMU cho vị trí dọc

**EN:** One problem remained. Lane lines fix the lateral position in every frame, but the along-road position is only fixed
at dashes, stop lines and crosswalks. In between, the estimate followed the tracker's jitter: the implied speed jumped
between 0 and 29 metres per second while the car drove a steady 9.5. So between markings the pose now moves with the IMU
speed times a scale that the filter learns, because the odometry is 10 to 15 percent off. It is used only when the car is
fast and nearly straight, and it stays on while braking to a stop. The speed is now smooth, and the public score went from
0.33 to 0.28.

**VI:** Còn một vấn đề. Vạch làn cố định vị trí ngang ở mọi frame, nhưng vị trí dọc đường chỉ được cố định ở vạch đứt,
vạch dừng và vạch sang đường. Ở giữa, ước lượng bị rung theo bộ bám: tốc độ suy ra nhảy từ 0 đến 29 m/s, trong khi xe
chạy đều khoảng 9,5 m/s. Vì vậy giữa các vạch, vị trí giờ di chuyển theo tốc độ IMU nhân với một hệ số tỉ lệ mà bộ lọc tự
học, vì odometry sai 10–15%. Chỉ dùng khi xe chạy nhanh và gần như thẳng, và vẫn giữ khi xe phanh tới lúc dừng. Tốc độ
giờ mượt, và điểm public từ 0,33 xuống 0,28.

## Slide 8 – Kết quả

**EN:** Results: Track 01 0.36 and Track 02 0.11, both first, with the pipeline alone at 0.51 and 0.24. Track 03 is second on
the public part with 0.28, from a purely causal pipeline. What worked was physics: the right scale, short-range matching,
the IMU mounting, and road paint as a landmark. Next I would use the map's 3D structure, like poles and curbs, for the
along position. Thank you.

**VI:** Kết quả: Track 01 được 0,36 và Track 02 được 0,11, cả hai hạng nhất; riêng pipeline được 0,51 và 0,24. Track 03
hạng hai ở phần public với 0,28, từ một pipeline hoàn toàn nhân quả. Điều hiệu quả là vật lý: đúng tỉ lệ, khớp ở tầm
gần, hướng lắp IMU, và vạch sơn làm mốc. Bước tiếp theo em sẽ dùng cấu trúc 3D của bản đồ, như cột và mép lề, cho vị trí
dọc. Em cảm ơn.

---

## Câu hỏi có thể gặp (gợi ý trả lời)

- **"Track 03 có dùng frame tương lai không?"** – No. Every row k uses frames ≤ k; the TA can rerun
  `tools/run_track3_paint.sh` (with the final filter flags) from the raw bag and get the same file byte for byte.
  (Không. Hàng k chỉ dùng frame ≤ k; TA chạy lại script là ra đúng file.)
- **"Why is probing allowed?"** – The TA allowed it for Tracks 01/02 in class on 23/10; the report labels the probed files
  and gives the pipeline scores separately. (TA cho phép trên lớp ngày 23/10; báo cáo ghi rõ.)
- **"What does the AI assistant do?"** – It wrote and ran code and analyses under my instructions; every experiment and
  decision is logged in the repository. (AI viết và chạy code theo yêu cầu của em; mọi thí nghiệm đều có nhật ký.)
- **"Private score of Track 03?"** – Unknown until the competition closes; our estimate is about 0.3–0.4 because the
  standstill (44 % of the private frames) is well locked by a crosswalk, while the turn and the final stop are harder.
  (Chưa biết; ước tính 0,3–0,4.)
