# Nguồn âm thanh

| File | Nguồn | Giấy phép |
|---|---|---|
| `music/upbeat_loop.wav` | Tự tổng hợp bằng code (`assets/make_audio.py`, numpy) | CC0 – tự tạo, không dùng mẫu bên ngoài |
| `sfx/whoosh.wav`, `sfx/pop.wav`, `sfx/ding.wav` | Tự tổng hợp bằng code (`assets/make_audio.py`) | CC0 – tự tạo |
| Giọng đọc | Microsoft Edge TTS (`edge-tts`, giọng `vi-VN-HoaiMyNeural`) | Dịch vụ đọc văn bản của Microsoft |

## Muốn dùng nhạc "viral" thật hơn
1. Tải một bài nhạc không bản quyền, ví dụ từ Pixabay Music (https://pixabay.com/music/, giấy phép Pixabay Content License).
2. Đặt file vào `video/assets/music/` với tên `custom.mp3` (hoặc `.wav`).
3. Thêm một dòng vào bảng trên: tên bài, tác giả, link, giấy phép.
4. `build.py` tự ưu tiên `assets/music/custom.*` nếu có.
