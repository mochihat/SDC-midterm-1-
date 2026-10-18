# Kịch bản video: "SDC 2026 Midterm 01 – Localization, giải thích từ con số 0"

Giọng đọc: `vi-VN-HoaiMyNeural` (nữ), nhịp nhanh. Tổng dự kiến ~38 phút. Xưng hô: "mình" (người kể, cũng là người đã làm bài) – "bạn" (người xem).
Ký hiệu mỗi cảnh:
- **Lời:** câu đọc (mỗi câu một dòng → mỗi câu là một "nhịp" chữ nhảy).
- **Chữ:** từ khoá hiện to trên màn hình (kinetic typography).
- **Hình:** mô tả animation / ảnh.
- **SFX:** hiệu ứng âm thanh (whoosh = chuyển cảnh, pop = chữ hiện, ding = ý quan trọng / kết quả).

Mọi con số lấy từ `video/research_notes.md` (nguồn: git, `docs/nhat-ky`, Kaggle). Chỗ chưa làm thì nói rõ là chưa làm.

---

## Chương 0 – Mở đầu (~1 phút)

### 0.1 Hook
- **Lời:**
  Một chiếc xe. Ba cái camera. Một tấm bản đồ ba chiều to bằng cả khu phố.
  Câu hỏi: xe đang ở đâu? Chính xác tới từng chục xăng-ti-mét.
  Nghe dễ? Bài baseline của đề chạy xong… lạc mất một trăm mét.
  Video này giải thích từ con số không: bài toán là gì, kiến thức nào cần, và mình đã làm gì để điểm từ 1.79 xuống 1.05.
- **Chữ:** "XE ĐANG Ở ĐÂU?" → "lạc 100 m 😱" → "1.79 → 1.05"
- **Hình:** icon xe 🚗 chạy trên bản đồ điểm (point cloud vẽ từ `map_downsampled_1m.pcd`, nhìn từ trên xuống); một chấm đỏ (baseline) trôi xa khỏi đường.
- **SFX:** whoosh mở đầu, pop từng chữ, ding ở "1.05".

### 0.2 Lộ trình
- **Lời:**
  Mình chia làm tám chương.
  Bức tranh lớn. Vì sao đề ra như vậy. Kiến thức nền – phần dài nhất.
  Code của đề. Mình đã làm gì, kể cả chỗ dùng AI. Hướng cải thiện. Checklist nộp bài. Và bảng thuật ngữ.
- **Chữ:** danh sách 8 chương hiện lần lượt.
- **SFX:** pop × 8.

---

## Chương 1 – Bức tranh lớn (~3 phút)

### 1.1 Hook
- **Lời:** Điện thoại bạn có GPS. Vậy sao xe tự lái không dùng luôn GPS cho xong?
- **Chữ:** "Có GPS rồi… cần gì nữa? 🤔"

### 1.2 Xe tự hành cần biết gì
- **Lời:**
  Xe tự hành phải trả lời ba câu hỏi.
  Mình đang ở đâu. Xung quanh có gì. Và đi tiếp thế nào.
  Câu đầu tiên tên là localization – định vị.
- **Chữ:** "1. Ở ĐÂU? → Localization" · "2. CÓ GÌ? → Perception" · "3. ĐI SAO? → Planning"
- **Hình:** 3 thẻ bài lật ra, thẻ 1 phóng to.

### 1.3 Pose
- **Lời:**
  Định vị không chỉ là toạ độ.
  Còn phải biết xe đang quay mặt về hướng nào.
  Vị trí cộng hướng gọi là pose – tư thế.
- **Chữ:** "POSE = VỊ TRÍ + HƯỚNG"
- **Hình:** mũi tên trên chấm xe, xoay quanh.

### 1.4 Vì sao GPS chưa đủ
- **Lời:**
  GPS thường sai vài mét.
  Vào giữa nhà cao tầng, tín hiệu dội qua dội lại, sai còn nhiều hơn.
  Vào hầm thì mất luôn.
  Một làn đường rộng chừng ba mét rưỡi. Sai hai mét là xe đã nằm ở làn bên cạnh.
- **Chữ:** "GPS: sai vài mét" · "nhà cao tầng 🏢 → dội sóng" · "hầm 🚇 → mất tín hiệu" · "làn đường ~3.5 m"
- **Hình:** xe vẽ đúng làn; chấm GPS nhảy lung tung sang làn bên cạnh.

### 1.5 Ý tưởng: so với bản đồ
- **Lời:**
  Cách của xe tự hành: mang theo một bản đồ 3D rất chi tiết.
  Cảm biến trên xe nhìn thấy gì, đem so với bản đồ.
  Khớp ở đâu thì xe ở đó.
  Giống như bạn bị bịt mắt thả vào một con phố quen, mở mắt ra nhìn quanh là biết mình đang đứng trước quán nào.
- **Chữ:** "NHÌN XUNG QUANH → SO VỚI BẢN ĐỒ → BIẾT MÌNH Ở ĐÂU"
- **Hình:** cụm điểm nhỏ (cái xe nhìn thấy) trượt trên bản đồ lớn rồi "khớp" vào đúng chỗ, sáng lên.
- **SFX:** ding khi khớp.

### 1.6 Nhớ 3 ý
- **Chữ (thẻ tóm tắt):**
  1. Localization = tìm **pose** (vị trí + hướng) của xe.
  2. GPS sai vài mét → không đủ cho xe tự hành.
  3. Cách chính: **so cái cảm biến thấy với bản đồ 3D**.
- **SFX:** pop × 3.

---

## Chương 2 – Vì sao đề lại ra như vậy (~3 phút)

### 2.1 Hook
- **Lời:** Năm 2021 đề dùng LiDAR. 2023 dùng Radar. Năm nay… dùng camera. Tại sao càng ngày càng "nghèo" đi?
- **Chữ:** "2021–22 LiDAR → 2023–25 Radar → 2026 CAMERA 📷"

### 2.2 Ba loại cảm biến
- **Lời:**
  LiDAR bắn tia laser, đo khoảng cách cực chuẩn. Nhưng đắt.
  Radar rẻ hơn, xuyên mưa sương tốt, nhưng điểm thưa và nhiễu.
  Camera rẻ nhất, ảnh rất nhiều chi tiết. Nhưng có một điểm yếu chết người.
- **Chữ:** "LiDAR: chuẩn 🎯, đắt 💰" · "Radar: rẻ hơn, thưa" · "Camera: rẻ, chi tiết… nhưng?"

### 2.3 Ảnh không có chiều sâu
- **Lời:**
  Ảnh là hai chiều.
  Một chiếc xe đồ chơi đặt sát ống kính và một chiếc xe thật ở xa có thể trông y hệt nhau.
  Ảnh không cho biết vật cách bao xa.
- **Chữ:** "ẢNH = 2D" · "gần & nhỏ = xa & to ??"
- **Hình:** xe đồ chơi gần và xe thật xa cùng hiện thành một hình giống nhau trên khung ảnh.

### 2.4 Mô hình học sâu đoán chiều sâu
- **Lời:**
  Nên người ta dùng mô hình học sâu để đoán chiều sâu, rồi dựng ảnh thành đám điểm 3D.
  Đề cho sẵn hai loại.
  LoGeR dựng từ camera trước. MapAnything dựng từ ba camera: trước, trước-trái, trước-phải.
- **Chữ:** "ẢNH → MÔ HÌNH → POINT CLOUD 3D" · "raw_ply = LoGeR (1 camera)" · "3cameras_ply = MapAnything (3 camera)"

### 2.5 Vì sao khó
- **Lời:**
  Đám điểm đoán ra có ba cái bệnh.
  Một: không biết tỉ lệ – to nhỏ sai cả mấy lần. Gọi là scale ambiguity.
  Hai: nhiễu, càng xa càng sai.
  Ba: méo, lệch so với thực tế.
  Đem một bản đồ "méo" như vậy đi khớp với bản đồ LiDAR chuẩn – đó chính là thử thách năm nay.
- **Chữ:** "1. SCALE ❓" · "2. NHIỄU 〰️" · "3. MÉO 🌀"
- **Hình:** đám điểm phóng to/thu nhỏ, rung, méo.

### 2.6 Đề yêu cầu gì
- **Lời:**
  Đề cho hai đoạn đường: Track01 có 3011 khung hình, Track02 có 3299.
  Với mỗi khung hình phải nộp vị trí x, y và góc yaw.
  Muốn có điểm thì phải tốt hơn baseline của TA.
  Ngoài ảnh, đề còn cho IMU và GNSS – và cho phép dùng.
- **Chữ:** "Track01: 3011 frame" · "Track02: 3299 frame" · "nộp: x, y, yaw" · "phải > baseline"

### 2.7 Nhớ 3 ý
1. Camera rẻ nhưng **không đo được chiều sâu**.
2. Mô hình học sâu đoán ra point cloud có **scale sai, nhiễu, méo**.
3. Nhiệm vụ: khớp point cloud đó vào **bản đồ LiDAR** để ra pose từng frame.

---

## Chương 3 – Kiến thức nền (~15 phút)

### 3.0 Hook
- **Lời:** Phần này dài nhất. Nhưng hiểu xong là bạn đọc được code của đề như đọc truyện.
- **Chữ:** "KIẾN THỨC NỀN 📚 – 11 món"

### 3.1 Hệ toạ độ và phép biến đổi
- **Lời:**
  Muốn nói "xe ở đâu" thì phải nói so với cái gì.
  Cái mốc đó gọi là hệ toạ độ, hay frame.
  Bài này có ba frame chính.
  Map – gắn với bản đồ, đứng yên.
  Base_link – gắn với thân xe, chạy theo xe.
  Camera – gắn với cái camera.
  Một điểm thấy trong frame camera, muốn đặt lên bản đồ thì phải xoay và dịch.
  Xoay gọi là rotation, ký hiệu R. Dịch gọi là translation, ký hiệu t.
  Hai cái gộp lại thành một ma trận bốn nhân bốn, gọi là ma trận đồng nhất – homogeneous matrix.
  Nhân ma trận này với điểm là xong cả xoay lẫn dịch.
- **Chữ:** "FRAME = mốc toạ độ" · "map 🗺️ / base_link 🚗 / camera 📷" · "p_map = R · p_cam + t"
- **Hình:** 3 hệ trục; điểm đỏ trong frame camera được xoay + dịch sang frame map. Công thức LaTeX:
  $T=\begin{bmatrix}R & t\\ 0 & 1\end{bmatrix}$, $\begin{bmatrix}p_{map}\\1\end{bmatrix} = T\begin{bmatrix}p_{cam}\\1\end{bmatrix}$
- **Code minh hoạ (Python, ngắn):**
  ```python
  T = np.eye(4); T[:3, :3] = R; T[:3, 3] = t
  p_map = (T @ np.append(p_cam, 1))[:3]
  ```
- **Lời (tiếp):**
  Trong đề, mỗi dòng kết quả chính là ma trận này của từng frame.
  Và file ma trận ban đầu init_guess.txt cũng là một ma trận bốn nhân bốn – có cộng thêm nhiễu.

### 3.2 Pose 6 bậc tự do, roll-pitch-yaw, quaternion
- **Lời:**
  Trong không gian 3D, một vật có sáu bậc tự do: ba để dịch – x, y, z – và ba để xoay.
  Ba góc xoay có tên rất "phi công": roll – nghiêng cánh, pitch – chúc đầu, yaw – quay trái phải.
  Xe chạy trên mặt đường nên quan trọng nhất là x, y và yaw.
  Kaggle cũng chỉ chấm đúng ba cái đó.
- **Chữ:** "6DoF = x y z + roll pitch yaw" · "Kaggle chấm: x, y, yaw"
- **Hình:** máy bay giấy ✈️ xoay theo 3 trục, rồi chuyển thành xe nhìn từ trên xuống, chỉ còn yaw.
- **Lời:**
  Còn quaternion là gì?
  Là cách viết một phép xoay bằng bốn con số: x, y, z, w.
  Vì sao IMU và ROS thích quaternion? Vì ba góc roll-pitch-yaw có chỗ bị "kẹt" – gọi là gimbal lock – và nội suy giữa hai góc rất xấu.
  Quaternion thì không bị kẹt, nối mượt.
  Muốn lấy yaw từ quaternion thì dùng công thức này.
- **Chữ:** "QUATERNION = 4 số (x, y, z, w)" · "không gimbal lock 🔒❌"
- **Công thức:** $\text{yaw} = \operatorname{atan2}\big(2(wz + xy),\ 1 - 2(y^2 + z^2)\big)$
- **Lời:**
  Còn từ ma trận xoay thì gọn hơn nữa – code của TA dùng đúng dòng này.
- **Code thật** (`processing_codes/txt_to_idx_x_y_yaw.py`):
  ```python
  def rotation_matrix_to_yaw(pose):
      r11 = pose[0]
      r21 = pose[4]
      return math.atan2(r21, r11)
  ```
- **Lời:** Lưu ý: file nộp ghi yaw bằng radian, nhưng khi chấm điểm sai số góc tính bằng độ.

### 3.3 Point cloud, file .ply, .pcd, bản đồ LiDAR
- **Lời:**
  Point cloud là một đống điểm 3D, mỗi điểm có x, y, z – có khi có thêm màu.
  File .ply là định dạng phổ biến, mỗi dòng một điểm. raw_ply của đề là dạng chữ, đọc được bằng mắt.
  File .pcd là định dạng của thư viện PCL – Point Cloud Library – thư viện C++ mà code của đề dùng.
  Bản đồ map.pcd của Track01 có gần sáu mươi triệu điểm, nặng 2.7 GB.
  Nó được dựng bằng cách cho xe có LiDAR chạy nhiều vòng, rồi ghép tất cả các lần quét lại với nhau.
- **Chữ:** "POINT CLOUD = đống điểm (x, y, z)" · ".ply / .pcd" · "PCL = Point Cloud Library" · "map.pcd: 59.5 triệu điểm 🤯"
- **Hình:** vài dòng text của file .ply thật (5 dòng đầu raw_ply frame 0), rồi zoom ra thành đám mây điểm; bản đồ Track01 thật (matplotlib, nhìn từ trên).

### 3.4 Chiều sâu từ ảnh và chuyện "scale"
- **Lời:**
  LoGeR nhận ảnh camera trước, đoán chiều sâu, dựng thành point cloud.
  Nhưng một camera thì không biết tỉ lệ thật.
  Ví dụ thật trong bài: trong point cloud của LoGeR, mặt đường nằm thấp hơn camera đúng 0.18 đơn vị.
  Ngoài đời camera cao khoảng một mét sáu.
  Vậy phải nhân cả đám điểm lên khoảng chín lần mới đúng kích thước thật.
  Code mẫu của đề lại nhân… ba lần.
  MapAnything dùng ba camera nên gần đúng mét hơn: mặt đường cách camera khoảng hai mét. Nhưng thử thực tế, nhân 0.8 mới khớp tốt nhất.
- **Chữ:** "mặt đường: 0.18 đơn vị" · "camera thật: ~1.6 m" · "→ scale ≈ 9 (template: 3 ❌)" · "3 camera: scale ≈ 0.8"
- **Hình:** point cloud LoGeR thật (frame 0) nhìn ngang, đường ngang ở z = −0.18; thanh trượt scale 3 → 9, đám điểm phóng to cho đến khi camera ở độ cao 1.6 m.
- **SFX:** ding ở "≈ 9".

### 3.5 Tiền xử lý
- **Lời:**
  Point cloud thô vừa nhiều vừa bẩn. Trước khi khớp phải dọn dẹp.
  Một: voxel grid – chia không gian thành các hộp nhỏ, mỗi hộp chỉ giữ một điểm đại diện. Đề dùng hộp một mét cho bản đồ, 0.3 mét cho point cloud từ ảnh. Bản đồ sáu mươi triệu điểm còn khoảng năm trăm nghìn.
  Hai: crop – chỉ cắt lấy phần bản đồ quanh xe, ở đây là cộng trừ một trăm mét.
  Ba: lọc điểm lạc loài – outlier – bằng thống kê hoặc bán kính. Bốn: bỏ mặt đường nếu nó gây nhiễu. Năm: che phần nắp capo xe bằng mask mà đề cho sẵn.
  Nói thật: mình mới dùng một và hai, cộng thêm bỏ điểm xa hơn bốn mươi mét. Ba cái còn lại đề có gợi ý nhưng mình chưa thử.
- **Chữ:** "1. VOXEL GRID 🧊" · "2. CROP ✂️" · "3. OUTLIER" · "4. BỎ MẶT ĐẤT" · "5. MASK CAPO" · "đã dùng: 1, 2 (+ bỏ điểm > 40 m)"
- **Hình:** animation voxel: lưới ô vuông phủ lên đám điểm 2D, mỗi ô co lại thành 1 điểm; số điểm đếm giảm.

### 3.6 ICP
- **Lời:**
  Giờ tới món chính: scan matching – khớp hai đám điểm.
  Thuật toán kinh điển nhất là ICP, Iterative Closest Point.
  Tưởng tượng hai tấm bản đồ in trên giấy kính, đặt chồng lên nhau, lệch một chút.
  Bước một: với mỗi điểm trên tấm trên, tìm điểm gần nhất trên tấm dưới. Gọi là ghép cặp – correspondence.
  Bước hai: tính phép xoay và dịch làm các cặp đó sát nhau nhất.
  Bước ba: dời tấm trên theo phép đó. Lặp lại tới khi không nhúc nhích nữa.
- **Chữ:** "ICP = ghép 2 tấm giấy kính 🗺️🗺️" · "1. tìm điểm gần nhất" · "2. tính R, t" · "3. dời & lặp 🔁"
- **Hình:** animation ICP 2D thật sự (tính bằng numpy): đám điểm đỏ, đám điểm xanh; vạch nối cặp gần nhất; đám đỏ xoay/dịch qua 5–6 vòng lặp cho tới khớp.
- **Lời:**
  Có hai kiểu: point-to-point – kéo điểm về điểm; và point-to-plane – kéo điểm về mặt phẳng gần nhất, thường hội tụ nhanh hơn trên tường và mặt đường.
  Điểm yếu: ICP chỉ tìm được cực tiểu gần nhất. Đặt lệch quá xa ban đầu là nó khớp sai, và rất tự tin là mình đúng.
  Vì vậy điểm xuất phát – initial guess – cực kỳ quan trọng.
  Lưu ý: bài của mình chưa dùng ICP. Mình dùng NDT – món tiếp theo.
- **Chữ:** "point-to-point vs point-to-plane" · "⚠️ cực tiểu cục bộ" · "initial guess quyết định" · "(bài mình: chưa dùng ICP)"
- **Hình:** ví dụ ICP bắt đầu lệch 60° → hội tụ sai, kèm dấu ❌.

### 3.7 NDT
- **Lời:**
  NDT – Normal Distributions Transform.
  Thay vì giữ từng điểm của bản đồ, NDT chia bản đồ thành các ô, mỗi ô tóm lại bằng một hình bầu dục xác suất – một phân phối chuẩn, Gaussian.
  Rồi nó xoay, dịch đám điểm từ ảnh sao cho các điểm rơi vào vùng "đậm" nhất của các hình bầu dục.
  Ưu điểm: không cần ghép cặp từng điểm, mượt hơn, thường nhanh hơn ICP.
  Tham số quan trọng nhất là độ lớn ô – resolution. Ô to thì dễ hội tụ nhưng thô. Ô nhỏ thì chi tiết nhưng dễ lạc.
  Template dùng ô tám mét. Với tỉ lệ đúng, mình thấy ô bốn mét tốt hơn hẳn.
- **Chữ:** "NDT = bản đồ → các ô Gaussian 🥚" · "tối ưu: điểm rơi vào chỗ đậm" · "resolution: 8 m → 4 m ✅"
- **Hình:** lưới ô trên bản đồ 2D; mỗi ô có ellipse màu đậm nhạt; đám điểm trượt vào; heatmap.
- **Code thật** (`localization.cpp`, hàm `AlignNDT` của template):
  ```cpp
  pcl::NormalDistributionsTransform<pcl::PointXYZ, pcl::PointXYZ> ndt;
  ndt.setResolution(ndt_resolution_);
  ndt.setStepSize(ndt_step_size_);
  ndt.setTransformationEpsilon(ndt_transformation_epsilon_);
  ndt.setMaximumIterations(ndt_max_iterations_);
  ndt.setInputSource(source);
  ndt.setInputTarget(target);
  ndt.align(aligned, initial_guess);
  ```
- **Chữ (so sánh):** bảng ICP vs NDT – ghép cặp từng điểm / không; nhạy điểm đầu: cao / vừa; tham số chính: khoảng cách ghép cặp / resolution.

### 3.8 Theo thời gian: motion model, GNSS, IMU, Kalman
- **Lời:**
  Xe chạy liên tục, mỗi giây khoảng hai mươi tám khung hình.
  Cách đơn giản: lấy pose của frame trước làm điểm xuất phát cho frame sau. Template làm đúng như vậy.
  Vấn đề: xe đã đi tiếp ba mươi phân, điểm xuất phát luôn bị "trễ".
  Cách tốt hơn: motion model – dự đoán bằng vận tốc. Đi đều thì frame sau ở xa thêm đúng bằng chừng đó.
  Rồi còn các cảm biến khác: GNSS cho vị trí tuyệt đối nhưng thô; IMU đo gia tốc và tốc độ quay, rất nhanh nhưng cộng dồn là trôi.
  Trộn chúng lại một cách thông minh là sensor fusion. Công cụ kinh điển là bộ lọc Kalman.
  Kalman làm hai bước, lặp mãi: dự đoán theo mô hình chuyển động; rồi cập nhật khi có số đo, tin số đo nhiều hay ít tuỳ nó nhiễu cỡ nào.
  Ví dụ đời thường: bạn đi trong bóng tối đếm bước chân – đó là dự đoán. Thỉnh thoảng thấy cột đèn quen – đó là cập nhật.
- **Chữ:** "frame trước → frame sau (trễ!)" · "MOTION MODEL 🏃" · "GNSS: tuyệt đối, thô" · "IMU: nhanh, trôi" · "KALMAN = DỰ ĐOÁN 🔮 + CẬP NHẬT 📏"
- **Hình:** chấm xe; vòng tròn bất định phình ra khi dự đoán, co lại khi có số đo GNSS.

### 3.9 ROS 2 và Docker
- **Lời:**
  Code của đề chạy trên ROS 2 – bộ khung phần mềm cho robot.
  Mỗi chương trình nhỏ là một node. Các node nói chuyện qua topic – như kênh chat. Mỗi tin nhắn có kiểu rõ ràng, ví dụ sensor_msgs/Imu cho IMU.
  Dữ liệu ghi lại được lưu trong rosbag – ở đây là file Track1.db3.
  File launch.py khởi động nhiều node cùng lúc. RViz để xem 3D. colcon để build.
  Còn Docker là cái hộp đóng gói sẵn hệ điều hành và thư viện, máy ai chạy cũng giống nhau. Đề cho sẵn Dockerfile.
- **Chữ:** "NODE 🧩 · TOPIC 📡 · MESSAGE ✉️" · "rosbag .db3" · "launch.py · RViz · colcon" · "DOCKER 📦"
- **Hình:** sơ đồ: node localization ↔ topic /imu/data, /localizer_node/gnss_pose ↔ RViz.

### 3.10 Thước đo: RMSE của ATE
- **Lời:**
  Chấm điểm thế nào?
  Với mỗi frame, lấy vị trí bạn nộp trừ vị trí đáp án – được sai số Δp, tính bằng mét.
  Lấy góc bạn nộp trừ góc đáp án – được Δθ, tính bằng độ.
  Bình phương, lấy trung bình, rồi căn bậc hai – đó là RMSE.
  Điểm bằng RMSE vị trí cộng 0.2 lần RMSE góc. Càng thấp càng tốt.
  Nghĩa là sai một độ thì bị cộng 0.2 điểm, tương đương sai hai mươi phân vị trí.
  Ví dụ thật: một bài nộp của mình sai vị trí 0.905 mét, sai góc 1.57 độ. Điểm bằng 0.905 cộng 0.2 nhân 1.57, khoảng 1.22.
- **Công thức:** $E=\sqrt{\tfrac1n\sum\lVert\Delta p_i\rVert^2}+0.2\sqrt{\tfrac1n\sum\Delta\theta_i^2}$
- **Chữ:** "càng THẤP càng tốt ⬇️" · "1° = 0.2 điểm = 20 cm" · "0.905 + 0.2×1.57 ≈ 1.22"

### 3.11 Kaggle
- **Lời:**
  Bài được nộp lên Kaggle.
  File CSV bốn cột: idx, x, y, yaw – yaw bằng radian. Mỗi frame một dòng. Thiếu dòng là bị lỗi – mình từng nộp nhầm file Track01 vào Track02 và bị báo lỗi đúng như vậy.
  Mỗi track tối đa mười lăm lượt mỗi ngày. Ngày mới tính theo giờ quốc tế UTC – tức tám giờ sáng ở Đài Loan, bảy giờ sáng ở Việt Nam.
  Leaderboard cuộc thi này chấm trên toàn bộ dữ liệu test. Nhớ chi tiết này – chương năm sẽ cần.
- **Chữ:** "CSV: idx, x, y, yaw(rad)" · "15 lượt/ngày/track" · "reset 00:00 UTC = 08:00 Đài Loan" · "leaderboard = toàn bộ test"

### 3.12 Nhớ 3 ý
1. **Pose** = ma trận 4×4 (xoay R + dịch t); Kaggle chỉ chấm x, y, yaw.
2. **Scan matching** (ICP/NDT) khớp point cloud vào bản đồ, nhưng **cần điểm xuất phát tốt** và **scale đúng**.
3. Điểm = RMSE vị trí + **0.2 × RMSE góc (độ)** – càng thấp càng tốt.

---

## Chương 4 – Code của đề chạy thế nào (~3 phút)

### 4.1 Hook
- **Lời:** Một lệnh ros2 launch. Đằng sau nó dữ liệu đi qua những đâu?

### 4.2 Các file
- **Lời:**
  localization.cpp – trái tim. Đọc bản đồ, đọc từng point cloud, chạy NDT, ghi kết quả.
  map_modified.cpp – tuỳ chọn, để lọc và giảm mẫu bản đồ trước. Mình chưa dùng.
  visualization.cpp – vẽ kết quả lên RViz.
  txt_to_idx_x_y_yaw.py – đổi file kết quả sang định dạng Kaggle.
- **Chữ:** 4 thẻ file. Ghi chú: "đề ghi process/…; repo thật: src/localization/processing_codes/".

### 4.3 Dòng chảy dữ liệu
- **Lời:**
  Đầu tiên đọc map.pcd, giảm mẫu một mét, lưu lại bản nhỏ để lần sau đọc trong vài giây.
  Đọc pose ban đầu từ init_guess.txt.
  Với mỗi file ply: nhân tỉ lệ, giảm mẫu, cắt phần bản đồ quanh xe, chạy NDT bắt đầu từ pose frame trước, ghi ma trận ra file.
  Cuối cùng đổi sang CSV để nộp.
- **Hình:** sơ đồ khối animate: map.pcd → voxel 1 m → cache; init_guess → pose; *.ply → ×scale → voxel → NDT ← submap; → result.txt → CSV.
- **Code thật** (TODO của TA trong `RunLocalization`):
  ```cpp
  const auto input = FilterInputCloud(ScalePlyPointCloud(raw_cloud, ply_scale_));
  const auto submap = CropSubmap(pose);
  // ================= TODO：Localization =================
  const bool converged = AlignNDT(input, submap, pose, candidate, score);
  ```

### 4.4 Chạy
- **Lời:**
  Chạy trong Docker: build bằng colcon, source môi trường, rồi ros2 launch.
  Sửa code thì phải build lại.
  Bản đồ đọc lần đầu mất khoảng một phút; mỗi frame NDT vài giây; chạy hết một track mất cỡ một hai tiếng.
- **Chữ:** `colcon build && source install/setup.bash && ros2 launch localization localization.launch.py`

### 4.5 Nhớ 3 ý
1. `localization.cpp` = đọc map → từng frame: scale, lọc, cắt submap, **NDT**, ghi pose.
2. Điểm xuất phát mỗi frame = **pose frame trước** (template).
3. Kết quả `.txt` (ma trận) → `txt_to_idx_x_y_yaw.py` → CSV Kaggle.

---

## Chương 5 – Mình đã làm gì (~9 phút)

### 5.1 Hook
- **Lời:** Bốn mươi bốn lượt nộp. Có lượt điểm tăng, có lượt tụt thê thảm. Đây là toàn bộ câu chuyện – kể cả chỗ dùng AI. (Trước đó có hai lượt nộp thử chỉ để làm quen định dạng.)
- **Chữ:** "44 lượt nộp 📈📉"

### 5.2 Mình dùng AI thế nào
- **Lời:**
  Nói trước cho minh bạch.
  Mình làm bài với một trợ lý AI tên là Claude Code, chạy trong terminal Ubuntu.
  Mình đưa cho nó: link cuộc thi, slide đề, ảnh chụp màn hình lỗi, dữ liệu đã tải, và các yêu cầu bằng lời.
  AI viết gần như toàn bộ code trong repo – từ sửa localization.cpp tới hai mươi script phân tích – chạy thí nghiệm, đề xuất hướng làm, và nộp phần lớn bài lên Kaggle bằng script.
  Phần mình: tải dữ liệu, tạo token, tự nộp sáu file GNSS đầu tiên, quyết định làm một mình, cho phép chỉnh theo điểm Kaggle, và quyết định chạy hay dừng từng thí nghiệm.
  Cách kiểm tra: mọi file đã nộp đều được tạo lại từ dữ liệu gốc bằng một script và so khớp từng byte. Ba mươi tư trên ba mươi tư file khớp.
- **Chữ:** "🤖 Claude Code (terminal)" · "AI: code + thí nghiệm + đề xuất + nộp bài" · "mình: dữ liệu, quyết định, cho phép" · "kiểm tra: tạo lại 34/34 file ✅"
- **Hình:** sơ đồ hai cột "Mình" – "AI"; ảnh chụp `git log --oneline` thật (các commit ở research_notes mục 1).

### 5.3 Bước 1 – Baseline lạc đường
- **Lời:**
  Việc đầu tiên: chạy baseline của TA.
  Kết quả: Track01 lệch chín mươi mốt mét, yaw lệch một trăm mười ba độ. Track02 lệch một trăm mười mét.
  Tức là xe… quay ngược đầu và đi lạc sang khu khác.
- **Chữ:** "Baseline: lệch 91 m / 110 m 💀"
- **Hình:** quỹ đạo baseline thật (`docs/nhat-ky/data/baseline_partial`) so với quỹ đạo GNSS, hai đường tách xa nhau.

### 5.4 Bước 2 – GNSS: phao cứu sinh
- **Lời:**
  Trong rosbag có một topic tên là localizer_node/gnss_pose, cập nhật bốn lần mỗi giây.
  Thử nộp thẳng nó: Track01 được 1.31, Track02 được 0.57 – baseline là 1.79 và 1.93.
  Làm mượt thêm một chút: Track01 xuống 1.26.
  Thử lấy hướng chạy làm yaw: Track02 xuống 0.47, nhưng Track01 lại tệ đi. Mỗi track mỗi tính.
- **Chữ:** "GNSS: 1.31 / 0.57 (baseline 1.79 / 1.93)" · "làm mượt → 1.26" · "yaw = hướng chạy → T2 0.47 ✅, T1 ❌"

### 5.5 Bước 3 – Phát hiện scale sai
- **Lời:**
  Tại sao NDT lạc? Mình đo point cloud: mặt đường cách camera 0.18 đơn vị, ổn định trên cả hai track.
  Camera thật cao một mét sáu. Tỉ lệ đúng phải khoảng chín. Template để ba.
  Sửa thành chín, ô NDT bốn mét: chín mươi hai phần trăm khung hình Track02 chỉ lệch dưới một mét so với GNSS.
  Nhưng ghép vào GNSS thì điểm lại tệ hơn – 0.535. NDT ổn định rồi, nhưng chưa chính xác bằng GNSS.
- **Chữ:** "mặt đường 0.18 → scale ×9 (không phải ×3)" · "NDT ổn định: 92 % < 1 m" · "nhưng ghép vào: 0.535 ❌"
- **Code thật (diff):** đoạn `PriorGuess` + `accepted = std::hypot(dx, dy) <= max_correction_xy_ ...`

### 5.6 Bước 4 – Bộ lọc Kalman
- **Lời:**
  Thay vì làm mượt kiểu tuỳ ý, mình dùng bộ lọc Kalman với mô hình xe: xe chạy theo hướng mũi, tốc độ và tốc độ quay thay đổi từ từ.
  Độ nhiễu không đoán bừa mà chọn sao cho mô hình giải thích dữ liệu GNSS tốt nhất – gọi là maximum likelihood.
  Kết quả: Track02 từ 0.47 xuống 0.408.
- **Chữ:** "KALMAN + mô hình xe (CTRV)" · "nhiễu: maximum likelihood" · "T2: 0.47 → 0.408 ✅"

### 5.7 Bước 5 – File thăm dò: điểm số nói gì
- **Lời:**
  Một mẹo hay: cố tình nộp file "sai có chủ đích".
  Dịch thời gian cộng trừ 0.1 giây. Dời ngang cộng trừ nửa mét. Xoay yaw cộng trừ một độ.
  Xem điểm thay đổi bao nhiêu, giải ngược ra: Track01 sai vị trí 0.905 mét, sai góc 1.77 độ.
  Ba nhóm thăm dò cho cùng một đáp số. Và công thức dự đoán điểm của bài tiếp theo 1.25339 – thực tế 1.25338.
- **Chữ:** "nộp sai có chủ đích 🎯" · "T1 = 0.905 m + 1.77°" · "dự đoán 1.25339 – thực tế 1.25338 🤯"

### 5.8 Bước 6 – Bí mật của yaw GNSS
- **Lời:**
  Soi kỹ GNSS thì lộ ra: góc yaw chỉ thay đổi khoảng 1.25 giây một lần.
  Và nó được tính từ chính vị trí GNSS trong một giây trước đó. Nên nó trễ.
  Tệ nhất: khi xe đứng yên, nó đóng băng. Track02 mười ba giây đầu: GNSS báo âm mười lăm độ, góc thật khoảng âm hai mươi độ.
  Mình dựng lại góc lúc đứng yên bằng con quay hồi chuyển – gyro – trong IMU. Track02 xuống 0.335.
  Nhưng có một cú lừa: bù độ trễ cho "đúng vật lý" lại làm điểm tệ đi. Đáp án không dùng hướng chạy đúng giờ. Đúng với dữ liệu chưa chắc đúng với đáp án.
- **Chữ:** "yaw GNSS: 1.25 s mới đổi 1 lần ⏱️" · "đứng yên → đóng băng 🧊" · "gyro cứu: T2 0.335 ✅" · "bù trễ 'đúng vật lý' → tệ hơn ❌"
- **Hình:** đồ thị bậc thang yaw GNSS vs đường mượt hướng chạy (dữ liệu thật Track02, 0–20 s).

### 5.9 "Chọn theo điểm Kaggle" là gì
- **Lời:**
  Tới phần nhạy cảm. Chọn theo điểm Kaggle nghĩa là: làm nhiều phiên bản, nộp lên, xem điểm, giữ cái tốt hơn.
  Bản nâng cao mình dùng: giữ nguyên vị trí, chỉ đổi yaw. Khi đó mỗi lượt nộp cho biết chính xác cái thay đổi đó tốt hay xấu bao nhiêu.
  Có vài lượt như vậy là giải được phương trình, ra tổ hợp tốt nhất – không cần nộp thử thêm. Dự đoán khớp điểm thật tới khoảng một phần nghìn.
  Ưu điểm: điểm lên nhanh, đo được những thứ dữ liệu không nói.
  Rủi ro thì phải nói thẳng.
  Một: leaderboard ở đây chấm trên toàn bộ dữ liệu test, không có bảng điểm ẩn. Chỉnh theo điểm là khớp thẳng vào đáp án – không phải thuật toán giỏi hơn. Trọng số tìm được nhiều khi vô nghĩa về vật lý, ví dụ âm bốn phẩy năm tám.
  Hai: tốn lượt – mỗi hướng một lượt, mười lăm lượt mỗi ngày.
  Ba: báo cáo chấm đóng góp gốc, nên phải ghi rõ phần nào chọn theo điểm.
- **Chữ:** "THỬ → NỘP → XEM ĐIỂM → GIỮ CÁI TỐT" · "✅ nhanh, đo được ẩn số" · "⚠️ khớp đáp án, không phải thuật toán" · "⚠️ 15 lượt/ngày" · "⚠️ phải ghi rõ trong báo cáo"
- **Hình:** sơ đồ vòng lặp; một bảng trọng số thật với số −4.58 được khoanh đỏ.

### 5.10 Bước 7 – NDT ba camera: lần đầu thắng GNSS
- **Lời:**
  Track01 sai chủ yếu ở vị trí, chín mươi phân. Cần nguồn vị trí mới.
  Thử NDT với point cloud ba camera. Tỉ lệ 1.0: tệ đi. Tỉ lệ 0.8: lỗi vị trí từ 0.905 xuống 0.836 mét.
  Tỉ lệ 0.8 ứng với camera cao khoảng một mét sáu lăm – khớp với tỉ lệ chín của LoGeR. Hai nguồn độc lập cho cùng một chiều cao camera.
  Đây là lần đầu scan matching thật sự sửa được GNSS.
  Kết hợp các hướng theo điểm Kaggle: Track01 xuống 1.054, Track02 xuống 0.299 – hạng hai.
- **Chữ:** "3 camera ×0.8: 0.905 → 0.836 m ✅" · "camera ~1.65 m ✔︎ khớp ×9" · "T1: 1.054 · T2: 0.299 (hạng 2) 🥈"
- **Hình:** đồ thị điểm theo thời gian của cả hai track (từ `docs/nhat-ky/data/kaggle_submissions.csv`), đánh dấu từng bước.

### 5.11 Bài học
- **Lời:**
  Kiểm tra dữ liệu đầu vào trước khi chạy thí nghiệm dài – bài này mất cả tiếng vì tỉ lệ sai.
  Một thước đo có thể thiên vị – lần đầu đo tỉ lệ, mình đo sai vì thế.
  Giả thuyết đẹp chưa chắc đúng với đáp án – chỉ một lượt nộp mới trả lời được.
  Và ghi lại mọi thứ để tạo lại được từng file.
- **Chữ:** "1. kiểm tra input trước 🔍" · "2. thước đo có thể lừa 🎭" · "3. giả thuyết đẹp ≠ đúng" · "4. ghi lại mọi thứ 📒"

### 5.12 Nhớ 3 ý
1. Lỗi lớn nhất của template: **scale ×3** (đúng ≈ 9 cho LoGeR, ≈ 0.8 cho 3 camera).
2. GNSS + **Kalman** mạnh nhất; **NDT 3 camera ×0.8** là lần đầu scan matching thắng GNSS.
3. Phần lớn điểm cuối đến từ **chọn theo điểm Kaggle** – hiệu quả nhưng phải ghi rõ, và không phải "thuật toán giỏi hơn".

---

## Chương 6 – Hướng cải thiện tiếp (~2 phút)

### 6.1 Hook
- **Lời:** Còn cách hạng nhất. Vậy đào ở đâu tiếp?

### 6.2 Các hướng (mỗi hướng gắn với một điểm yếu đã thấy)
- **Lời:**
  Một: NDT chỉ dùng ảnh còn trôi chín mét sau một trăm năm mươi frame vì thiếu motion model và hướng ban đầu sai mười lăm độ. Thêm dự đoán vận tốc và thử nhiều góc ở frame đầu.
  Hai: chưa thử ICP, nhất là point-to-plane.
  Ba: tỉ lệ ba camera mới thử 0.8, 0.85 và 1.0 – còn thử được 0.7, 0.75, và ô NDT hai mét.
  Bốn: lỗi yaw còn lại thay đổi nhanh – dò theo đoạn mười lăm giây không bắt được. Có thể dùng gyro tốt hơn.
  Năm: lọc outlier, bỏ mặt đường, mask nắp capo – đề có gợi ý, chưa làm.
- **Chữ:** "1. motion model + thử nhiều góc" · "2. ICP point-to-plane" · "3. scale 0.7–0.75, NDT 2 m" · "4. yaw tần số cao ← gyro" · "5. outlier / mặt đất / mask"

### 6.3 Nhớ 3 ý
1. Thuật toán chỉ dùng ảnh cần **motion model**.
2. Hướng sửa vị trí có hy vọng nhất: **NDT 3 camera** với tỉ lệ và độ phân giải khác.
3. Các bước tiền xử lý đề gợi ý **chưa được thử**.

---

## Chương 7 – Checklist nộp bài (~1.5 phút)

### 7.1 Hook
- **Lời:** Làm hay mà nộp thiếu file thì… cũng như không.

### 7.2 Checklist
- **Lời:**
  Kaggle đóng lúc chín giờ sáng ngày hai mươi chín tháng mười. Nhớ kiểm tra bài nào được chọn để chấm.
  E3 hạn mười một giờ năm mươi chín tối ngày năm tháng mười một: file zip gồm thư mục localization không kèm dữ liệu, result_1.csv, result_2.csv, báo cáo PDF và README cách chạy.
  Làm một mình thì tên file chỉ có một mã số sinh viên – nên hỏi TA cho chắc.
- **Chữ:** "Kaggle: 29/10 09:00" · "E3: 05/11 23:59" · "zip: code + result_1/2.csv + report.pdf + README" · "1 người → hỏi TA cách đặt tên"

### 7.3 Dàn ý báo cáo (30 điểm)
- **Lời:**
  Báo cáo có bốn phần.
  Pipeline – chương trình chạy thế nào.
  Contributions – đóng góp của bạn: phát hiện scale, NDT có prior, Kalman, NDT ba camera.
  Problems and Solutions – baseline lạc, yaw GNSS trễ, xe đứng yên.
  Workload – làm một mình, và ghi rõ phần nào AI hỗ trợ, phần nào chọn theo điểm Kaggle.
  Nhớ: dùng mã nguồn mở mà không sửa gì đáng kể thì phần đóng góp bằng không.
- **Chữ:** "Pipeline · Contributions · Problems & Solutions · Workload" · "⚠️ open-source không sửa = 0 điểm đóng góp"

### 7.4 Nhớ 3 ý
1. Kaggle **29/10 09:00**, E3 **05/11 23:59**.
2. Zip: code (không data) + `result_1.csv` + `result_2.csv` + PDF + README.
3. Báo cáo ghi rõ **AI** và **chọn theo điểm Kaggle**.

---

## Chương 8 – Tổng kết và thuật ngữ (~2 phút)

### 8.1 Tóm tắt cả video
- **Lời:**
  Localization là tìm pose của xe.
  Năm nay dùng ảnh: point cloud từ ảnh có scale sai, nhiễu, méo.
  Khớp nó vào bản đồ bằng ICP hoặc NDT, cần điểm xuất phát tốt và scale đúng.
  GNSS và bộ lọc Kalman cho nền vững; NDT ba camera sửa được vị trí; chọn theo điểm Kaggle đưa điểm xuống thêm – nhưng phải minh bạch.
- **Chữ:** 4 dòng tóm tắt hiện lần lượt.

### 8.2 Bảng thuật ngữ Việt – Anh (hiện từng trang, ~6 dòng/trang)

| Tiếng Anh | Tiếng Việt / giải thích |
|---|---|
| Localization | định vị – tìm vị trí và hướng của xe |
| Pose / 6DoF | tư thế – vị trí + hướng / 6 bậc tự do |
| Frame (map, base_link, camera) | hệ toạ độ gắn với bản đồ / thân xe / camera |
| Rotation, translation | phép xoay, phép dịch |
| Homogeneous matrix | ma trận đồng nhất 4×4 |
| Roll, pitch, yaw | nghiêng ngang, chúc đầu, quay trái-phải |
| Quaternion | biểu diễn phép xoay bằng 4 số |
| Gimbal lock | hiện tượng "kẹt" của góc Euler |
| Point cloud | đám điểm 3D |
| Voxel grid | lưới hộp để giảm mẫu |
| Outlier | điểm lạc loài |
| Scale ambiguity | không xác định được tỉ lệ |
| Scan matching / registration | khớp đám điểm |
| ICP (Iterative Closest Point) | khớp bằng ghép cặp điểm gần nhất, lặp |
| Correspondence | cặp điểm tương ứng |
| NDT (Normal Distributions Transform) | khớp bằng các ô phân phối chuẩn |
| Local minimum | cực tiểu cục bộ |
| Initial guess | điểm xuất phát |
| Motion model | mô hình chuyển động |
| GNSS | hệ thống định vị vệ tinh (GPS là một loại) |
| IMU, gyro | bộ đo quán tính, con quay hồi chuyển |
| Sensor fusion | trộn dữ liệu cảm biến |
| Kalman filter / RTS smoother | bộ lọc Kalman / làm mượt hai chiều |
| Maximum likelihood | chọn tham số giải thích dữ liệu tốt nhất |
| Node, topic, message, rosbag | thành phần ROS 2 |
| ATE, RMSE | sai số quỹ đạo tuyệt đối, căn trung bình bình phương |
| Leaderboard | bảng xếp hạng |
| Overfit | khớp quá mức vào dữ liệu đã thấy |

### 8.3 Kết
- **Lời:** Vậy là hết. Nếu bạn hiểu được tại sao ×3 là sai và ×9 là đúng – bạn đã hiểu bài này hơn phần lớn mọi người. Hẹn gặp ở midterm sau.
- **Chữ:** "×3 ❌ → ×9 ✅" · "THE END 🎬"
- **SFX:** ding + whoosh kết.
