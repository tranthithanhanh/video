"""Streamlit entry point: streamlit run app.py."""
from pathlib import Path
from tempfile import TemporaryDirectory

import streamlit as st

from video_engine import VOICES, render_video, synthesize

st.set_page_config(page_title="Tạo video tự động", page_icon="🎬")
st.title("🎬 Tạo video tự động")
st.caption("Biến kịch bản, ảnh và video của bạn thành video có lời đọc tiếng Việt.")
script = st.text_area("Kịch bản", height=200, max_chars=20000,
                      placeholder="Nhập nội dung lời đọc cho video…")
uploads = st.file_uploader("Ảnh / video (ghép theo thứ tự tải lên)",
    type=["png", "jpg", "jpeg", "webp", "mp4", "mov", "mkv", "webm"],
    accept_multiple_files=True)
voice = st.selectbox("Giọng đọc tiếng Việt", list(VOICES))
music = st.file_uploader("Nhạc nền (tùy chọn)", type=["mp3", "wav", "m4a", "ogg"])
with st.expander("Tùy chỉnh"):
    aspect = st.selectbox("Khung hình", ["Ngang 16:9", "Dọc 9:16", "Vuông 1:1"])
    volume = st.slider("Âm lượng nhạc nền (%)", 0, 50, 22) / 100
    transition = st.slider("Chuyển cảnh (giây)", 0.0, 1.0, 0.4, 0.1)
st.info("Cần Internet để tạo giọng đọc. Khi không tải ảnh/video, ứng dụng dùng nền màu. "
        "Đây là ghép dựng tự động từ tư liệu, không sinh hình ảnh bằng AI. "
        "Ảnh/video được cắt giữa để lấp đầy khung; âm thanh gốc được bỏ.")

if st.button("Tạo Video", type="primary"):
    if not script.strip():
        st.warning("Vui lòng nhập kịch bản trước.")
    else:
        st.session_state.pop("result", None)
        try:
            with TemporaryDirectory(prefix="video-studio-") as folder:
                work = Path(folder)
                paths = []
                for index, upload in enumerate(uploads):
                    path = work / f"media_{index}{Path(upload.name).suffix.lower()}"
                    path.write_bytes(upload.getvalue())
                    paths.append(path)
                bgm = None
                if music:
                    bgm = work / f"bgm{Path(music.name).suffix.lower()}"
                    bgm.write_bytes(music.getvalue())
                with st.status("Đang tạo video…", expanded=True) as status:
                    st.write("1/2 — Tạo giọng đọc tiếng Việt")
                    narration = work / "narration.mp3"
                    synthesize(script, narration, VOICES[voice])
                    st.write("2/2 — Ghép hình, chuyển cảnh, trộn nhạc và xuất MP4")
                    sizes = {"Ngang 16:9": (1280, 720), "Dọc 9:16": (720, 1280),
                             "Vuông 1:1": (720, 720)}
                    result = render_video(paths, narration, work / "video.mp4", bgm,
                        size=sizes[aspect], transition=transition, bgm_volume=volume)
                    st.session_state.result = result.read_bytes()
                    status.update(label="Video đã hoàn tất", state="complete")
        except Exception as exc:
            st.error("Không thể tạo video. Hãy kiểm tra kết nối dịch vụ giọng đọc, "
                     "định dạng tư liệu và dung lượng trống.")
            with st.expander("Chi tiết lỗi"):
                st.code(f"{type(exc).__name__}: {exc}")

if "result" in st.session_state:
    st.video(st.session_state.result)
    st.download_button("Tải video MP4", st.session_state.result,
                       file_name="video.mp4", mime="video/mp4")
