# Video bài giảng "SDC 2026 Midterm 01 – Localization"

Video tiếng Việt tự động: lời đọc `edge-tts` (giọng `vi-VN-HoaiMyNeural`), animation Manim Community Edition,
nhạc nền + hiệu ứng âm thanh tự tổng hợp, giảm nhạc khi có giọng đọc (ducking), phụ đề `.srt`.

| File / thư mục | Nội dung |
|---|---|
| `research_notes.md` | Dữ kiện lấy từ repo, nhật ký, Kaggle (bước 0) |
| `script.md` | Kịch bản đầy đủ: lời đọc, chữ trên màn hình, hình, SFX |
| `scenes/<id>.py` | Mỗi chương một file: `LINES` (lời đọc), `SFX`, class Manim |
| `lib/tts.py`, `lib/style.py` | Đọc lời + đo thời lượng; kiểu chữ, màu, chữ nhảy, thẻ tiêu đề / "nhớ 3 ý" |
| `assets/make_audio.py` | Tổng hợp nhạc nền và SFX (xem `assets/CREDITS.md`) |
| `build.py` | 1 lệnh: TTS → Manim → SFX → trộn tiếng → phụ đề → ghép chương |
| `docker/Dockerfile` | Môi trường render (Python 3.11, Manim 0.18.1, LaTeX, ffmpeg, font Noto) |
| `audio/`, `out/` | Âm thanh từng câu (`timing.json`), video ra |

## Cài đặt (Ubuntu, dùng Docker – không cài gì vào máy)

```bash
cd ~/SDC-midterm01/midterm01/video
docker build -t sdc-video:latest docker/          # lần đầu ~30–60 phút (LaTeX nặng)
```

## Chạy

```bash
cd ~/SDC-midterm01/midterm01/video
RUN="docker run --rm -u $(id -u):$(id -g) -e HOME=/tmp -v $PWD:/work -w /work sdc-video:latest"

$RUN python3 build.py --chapters c3_06_icp --preview   # 1 chương, 480p15, nhanh → out/c3_06_icp.preview.mp4
$RUN python3 build.py --chapters c3_06_icp             # 1 chương, 1080p30 → out/c3_06_icp.mp4
$RUN python3 build.py                                  # toàn bộ → out/midterm_localization.mp4 (+ .srt)
$RUN python3 build.py --no-music                       # chỉ giọng đọc + SFX
$RUN python3 build.py --concat-only                    # chỉ ghép các chương đã render sẵn
```

- Cần internet (edge-tts gửi lời thoại lên dịch vụ đọc của Microsoft). Câu đã đọc được lưu lại, sửa một câu chỉ đọc lại câu đó.
- Âm lượng nhạc từng chương: `music_volume` trong danh sách `CHAPTERS` ở `build.py` (0 = tắt nhạc chương đó).
- Nhạc riêng: đặt `assets/music/custom.mp3` (ghi nguồn vào `assets/CREDITS.md`), `build.py` sẽ ưu tiên.
- Mỗi chương render độc lập: sửa `scenes/<id>.py` rồi chạy lại với `--chapters <id>`, sau đó `--concat-only`.
- Emoji dùng font Symbola (nét đơn sắc), vì Manim đổi chữ thành đường vector và không vẽ được font emoji màu.
  Đổi font hoặc Docker image thì xoá `out/media/texts/` (Manim lưu SVG từng dòng chữ theo nội dung, sẽ dùng lại bản cũ).
- Dịch vụ đọc của Microsoft đôi khi không trả âm thanh (`NoAudioReceived`) hoặc treo: `lib/tts.py` tự thử lại; nếu
  một chương vẫn lỗi thì chạy lại chương đó.

## Thêm một chương
1. Tạo `scenes/<id>.py`. Cách nhanh: theo mẫu `scenes/c6_next.py` – danh sách `BEATS` gồm (câu đọc, các thành phần
   hiển thị: title, big, caption, bullets, image, formula, code, table, summary, note, custom), xem `lib/kit.py`.
   Cảnh tự vẽ hoàn toàn: theo mẫu `scenes/c3_06_icp.py` (`LINES`, `SFX`, class kế thừa `BeatScene`, mỗi nhịp kết thúc
   bằng `self.end_beat()` – nhịp kéo dài đúng bằng câu đọc).
2. Thêm một dòng vào `CHAPTERS` trong `build.py`.
