# Tạo video tự động bằng Python và Streamlit

## Bắt đầu trên Windows

1. Trên GitHub, chọn **Code → Download ZIP** rồi giải nén tệp vừa tải.
2. Cài **Python 3.12 (64-bit)** từ python.org, đánh dấu **Add python.exe to PATH**.
3. Mở thư mục đã giải nén, nhấp đúp **CAI_DAT.bat** và chờ thông báo hoàn tất.
4. Nhấp đúp **MO_UNG_DUNG.bat** để mở ứng dụng. Giữ cửa sổ lệnh đang chạy.
5. Nhập kịch bản, tải ảnh/video, chọn giọng và nhạc nền, bấm **Tạo Video**.
6. Khi hoàn tất, bấm **Tải video MP4**. Nhấn Ctrl+C trong cửa sổ lệnh để dừng.

Chỉ chạy CAI_DAT.bat lần đầu. Những lần sau chỉ mở MO_UNG_DUNG.bat.
Nếu trình duyệt không tự mở, nhập `http://localhost:8501` trên máy đang chạy ứng dụng.

Ứng dụng ghép tư liệu của bạn thành MP4 H.264/AAC với lời đọc tiếng Việt,
chuyển cảnh crossfade và nhạc nền giảm âm khi có lời nói. Bản 2 có thêm ảnh AI
theo từng cảnh và dịch vụ giọng đọc thay thế. Không sinh cảnh quay chuyển động AI.

## Tạo ảnh theo kịch bản — bản 2

1. Chọn **Tạo ảnh AI theo kịch bản**.
2. Mở **Cấu hình AI**, nhập API key OpenAI vào ô mật khẩu.
3. Kiểm tra/sửa lời đọc và mô tả ảnh của từng cảnh. Chọn phong cách người que
   trên nền đen nếu muốn gần phong cách video minh họa tài chính.
4. Chọn nguồn giọng đọc: Edge miễn phí, OpenAI TTS có phí, hoặc file tự thu.
5. Xác nhận API có phí rồi bấm **Tạo Video**.

Tạo khóa tại https://platform.openai.com/api-keys bằng **Create new secret key**.
Tài khoản cần bật thanh toán/hạn mức API; gói ChatGPT không bao gồm phí API.
Không gửi khóa cho người khác, không đưa vào GitHub. Có thể đặt biến môi trường
`VIDEO_AI_API_KEY` trên máy cá nhân thay vì nhập lại ở mỗi phiên.
Ảnh dùng `gpt-image-1` chất lượng low, một ảnh mỗi cảnh; giọng đọc thay thế dùng
`tts-1`. Quyền mô hình phụ thuộc tài khoản, đôi khi cần xác minh tổ chức.
Ứng dụng không tự gửi lại yêu cầu AI có phí khi timeout để tránh tính phí trùng.
Mỗi lần bấm tạo lại có thể phát sinh phí mới; hiện chưa lưu ảnh AI sau lần dựng lỗi.

**Thời lượng cảnh:** với TTS, mỗi cảnh được đọc riêng rồi lấy thời lượng âm thanh
để căn ảnh tương ứng. Cảnh chia theo câu, không dùng mô hình ngôn ngữ để lập
storyboard; mô tả ảnh được tạo từ lời đọc và có thể sửa trước khi gửi. Ảnh AI
có thể hiểu sai chi tiết hoặc thiếu nhất quán nhân vật. Khi tải lời đọc có sẵn,
ứng dụng chưa có forced alignment nên chia đều thời gian giữa các ảnh.

**Nếu Edge lỗi:** bản mới hiện loại lỗi, thử tối đa ba lần, không tự đổi giọng hay
chuyển dịch vụ có phí. Có thể chủ động chọn OpenAI TTS hoặc tải lời đọc đã thu.
Retry không sửa được sự cố dịch vụ, mạng bị chặn hay giới hạn từ nhà cung cấp.

**Cập nhật từ bản cũ trên Windows:** dừng ứng dụng, tải ZIP mới từ GitHub, giải nén
vào thư mục mới, chạy CAI_DAT.bat rồi MO_UNG_DUNG.bat. Không chép API key vào file.

## 1. Cài đặt

Yêu cầu Python 3.10 trở lên (đã kiểm tra với Python 3.12). Nên có FFmpeg
trên PATH; MoviePy dùng `imageio-ffmpeg`, có binary đi kèm trên các nền tảng
được hỗ trợ. Có thể cài FFmpeg trên Ubuntu bằng `sudo apt install ffmpeg`.

Mở terminal tại thư mục dự án:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Windows PowerShell dùng `.venv\Scripts\Activate.ps1` thay cho lệnh `source`.
MoviePy được ghim phiên bản 2.2.1; mã dùng API MoviePy 2, không dùng
`moviepy.editor` của các hướng dẫn MoviePy 1 cũ.

## 2. Chạy

Trong môi trường đã cài sẵn, chỉ cần mở terminal và chạy:

```bash
cd /workspace/video
bash run.sh
```

Để cài lại trên Linux/macOS, chạy `bash install.sh` tại thư mục dự án.
Giữ terminal chạy trong lúc sử dụng; nhấn Ctrl+C để dừng.

```bash
python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

Trên máy cá nhân, mở trình duyệt tại cổng 8501. Trên nền tảng đám mây,
sử dụng cơ chế truy cập ứng dụng do nền tảng cung cấp.

1. Nhập kịch bản (tối đa 20.000 ký tự).
2. Tải ảnh JPG/PNG/WebP và/hoặc video MP4/MOV/MKV/WebM theo thứ tự mong muốn.
3. Chọn nữ Hoài My hoặc nam Nam Minh; có thể thêm BGM MP3/WAV/M4A/OGG.
4. Chọn khung ngang, dọc hoặc vuông, âm lượng nhạc và thời gian chuyển cảnh.
5. Bấm **Tạo Video**, chờ hoàn tất, xem trước và tải MP4.

## 3. Cách xử lý

- Tổng thời lượng lấy từ lời đọc. Tư liệu tải lên được chia đều thời gian;
  ảnh AI với TTS căn theo thời lượng từng cảnh. Sai lệch xuất có thể đến một khung hình.
- Ảnh được giữ theo thời lượng phân bổ; video ngắn lặp lại, video dài cắt bớt.
  Hình ảnh cắt giữa để lấp đầy khung; âm thanh video gốc không được giữ lại.
- Crossfade tạo phần chồng lấn giữa các cảnh mà không kéo dài tổng video.
- BGM được lặp/cắt theo tổng thời lượng. Bộ phát hiện RMS phân tích cửa sổ
  20 ms của lời đọc; nhạc giảm còn 25% mức đã chọn khi có giọng nói, có
  khoảng đón trước, giữ và phục hồi dần. Đây là ducking theo năng lượng,
  không phải mô hình nhận diện tiếng nói; nhạc hồi phục ở các khoảng lặng dài.
- Tệp tạm được tạo riêng cho mỗi lần render và xóa sau khi hoàn tất/lỗi.
  MP4 giữ trong bộ nhớ phiên Streamlit cho đến khi phiên kết thúc hoặc tạo lại.

## 4. Kết nối và giới hạn

`edge-tts` cần Internet tới dịch vụ Microsoft Edge tại
`speech.platform.bing.com` qua HTTPS/WebSocket. Nội dung lời đọc được gửi
đến dịch vụ đó; tư liệu ảnh/video và BGM được xử lý trong môi trường chạy.
Nếu dịch vụ bị chặn, đổi giao thức hoặc giới hạn lượt gọi, ứng dụng báo lỗi;
không tự dùng giọng giả hay bỏ qua lời đọc. Trong cloud cần cho phép tên miền
này trong chính sách mạng. Không nhập khóa bí mật vào mã nguồn.

Streamlit mặc định giới hạn 200 MB mỗi file tải lên. Render dùng CPU, giới hạn
hai luồng FFmpeg; video dài và file lớn cần nhiều RAM/đĩa. Bản này phù hợp
chạy cá nhân, chưa có hàng đợi nền hay bảo vệ tài nguyên cho dịch vụ công cộng.
Chưa có phụ đề tự động hay tạo cảnh quay chuyển động AI. OpenAI cần kết nối
`api.openai.com` qua HTTPS; nếu dùng cloud bị giới hạn mạng, cần cho phép miền
này trong cấu hình môi trường. Nội dung lời đọc/mô tả ảnh được gửi đến dịch vụ
đã chọn; ảnh/video tải lên và nhạc nền được xử lý tại máy chạy ứng dụng.

## 5. Kiểm thử

```bash
python -m pip install pytest
python -m pytest -q
```

Kiểm thử dùng âm thanh tổng hợp để không phụ thuộc Internet, kiểm tra ducking,
ghép ảnh/video ngắn, màu tại chuyển cảnh, thời lượng và âm thanh MP4.
Kiểm thử này không xác minh dịch vụ TTS trực tuyến.
Các bài kiểm tra OpenAI dùng phản hồi giả lập và âm thanh tổng hợp; không chứng
minh tài khoản có quyền mô hình, có số dư hoặc API hoạt động thực tế.

## Cấu trúc

- `app.py`: giao diện, quản lý upload và tải MP4.
- `video_engine.py`: TTS, căn thời lượng, crossfade, ducking và xuất video.
- `ai_services.py`: chia cảnh, tạo prompt, adapter ảnh/giọng đọc OpenAI.
- `workflow.py`: tạo lời đọc/ảnh cho từng cảnh và ghép âm thanh.
- `tests/test_video_engine.py`: kiểm tra chức năng dựng video thực tế.
