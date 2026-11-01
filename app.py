"""Streamlit video studio: scene images, narration and MP4 export."""
import hashlib
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import streamlit as st
from ai_services import image_prompt, split_scenes
from video_engine import VOICES, render_video
from workflow import prepare_scenes

st.set_page_config(page_title="Tạo video tự động", page_icon="🎬")
st.title("🎬 Tạo video tự động")
st.caption("Bản 2 — tạo ảnh theo từng cảnh, chọn dịch vụ giọng đọc và xuất MP4.")
script = st.text_area("Kịch bản", height=180, max_chars=20000)
mode = st.radio("Nguồn hình ảnh", ["Tải ảnh/video của tôi", "Tạo ảnh AI theo kịch bản"])
ai_images = mode == "Tạo ảnh AI theo kịch bản"
with st.expander("Cấu hình AI và hướng dẫn API key", expanded=ai_images):
    st.markdown("1. Mở https://platform.openai.com/api-keys và đăng nhập.\n"
                "2. Tạo khóa **Create new secret key**.\n"
                "3. Kiểm tra Billing và hạn mức API trên tài khoản.\n"
                "4. Dán khóa vào ô bên dưới. Không gửi khóa qua tin nhắn.")
    st.caption("OpenAI API tính phí riêng với ChatGPT. Khóa chỉ giữ trong bộ nhớ phiên ứng dụng, "
               "không lưu vào mã nguồn. Nội dung cảnh được gửi đến OpenAI khi bạn chọn dịch vụ đó.")
    api_key = st.text_input("API key OpenAI", type="password",
                            value=os.environ.get("VIDEO_AI_API_KEY", ""))
provider = st.selectbox("Nguồn giọng đọc", ["Edge TTS", "OpenAI TTS", "Tải file lời đọc có sẵn"])
if provider == "Edge TTS":
    voice = VOICES[st.selectbox("Giọng đọc tiếng Việt", list(VOICES))]
    st.caption("Miễn phí, cần kết nối Microsoft. Có thể tạm ngừng hoặc giới hạn lượt gọi.")
elif provider == "OpenAI TTS":
    voice = st.selectbox("Giọng OpenAI (có thể đọc tiếng Việt)", ["nova", "onyx", "alloy", "shimmer"])
    st.caption("Có phí API; không đảm bảo cùng chất giọng Hoài My/Nam Minh của Edge.")
else:
    voice = ""
spoken = st.file_uploader("File lời đọc đã thu (MP3/WAV/M4A)", type=["mp3", "wav", "m4a"]) if provider == "Tải file lời đọc có sẵn" else None
uploads = st.file_uploader("Ảnh/video theo thứ tự", type=["png", "jpg", "jpeg", "webp", "mp4", "mov", "mkv", "webm"], accept_multiple_files=True) if not ai_images else []
music = st.file_uploader("Nhạc nền (tùy chọn)", type=["mp3", "wav", "m4a", "ogg"])
with st.expander("Tùy chỉnh"):
    aspect = st.selectbox("Khung hình", ["Ngang 16:9", "Dọc 9:16", "Vuông 1:1"])
    volume = st.slider("Âm lượng nhạc nền (%)", 0, 50, 22) / 100
    transition = st.slider("Chuyển cảnh (giây)", 0.0, 1.0, 0.4, 0.1)
    limit = st.slider("Số cảnh tối đa", 1, 12, 4)
    style = st.selectbox("Phong cách ảnh AI", ["Cinematic realistic photography", "White stick figures on a black background, minimalist illustration", "Colorful flat illustration"])

scenes = []
if ai_images and script.strip():
    fingerprint = hashlib.sha256(f"{script}|{limit}|{style}".encode()).hexdigest()[:12]
    with st.expander("Xem và sửa nội dung từng cảnh trước khi tạo", expanded=True):
        st.caption("Chia cảnh theo câu; bạn có thể sửa lời đọc và mô tả ảnh để hình sát ý hơn. "
                   "Mỗi cảnh dùng một lần tạo ảnh. Thay đổi kịch bản/phong cách sẽ tạo lại bản chia cảnh.")
        for i, text in enumerate(split_scenes(script, limit)):
            narration = st.text_area(f"Cảnh {i+1} — lời đọc", text, key=f"text_{fingerprint}_{i}")
            prompt = st.text_area(f"Cảnh {i+1} — mô tả ảnh", image_prompt(text, style), key=f"prompt_{fingerprint}_{i}")
            scenes.append({"text": narration, "prompt": prompt})
consent = st.checkbox("Tôi đồng ý gửi nội dung đến OpenAI và sử dụng API có tính phí") if ai_images or provider == "OpenAI TTS" else False
st.info("Ảnh AI được dựng thành video có chuyển cảnh, không phải cảnh quay chuyển động do AI sinh. "
        "Khi dùng TTS, thời lượng mỗi ảnh khớp lời đọc của cảnh đó. Với file lời đọc tải lên, "
        "ảnh chia thời gian đều vì chưa có căn chỉnh câu tự động. Âm thanh tư liệu gốc được bỏ.")

if st.button("Tạo Video", type="primary"):
    needs_key = ai_images or provider == "OpenAI TTS"
    if not script.strip():
        st.warning("Vui lòng nhập kịch bản.")
    elif needs_key and not api_key.strip():
        st.warning("Nhập API key trong Cấu hình AI trước khi tạo.")
    elif needs_key and not consent:
        st.warning("Xác nhận sử dụng API có phí trước khi tạo.")
    elif provider == "Tải file lời đọc có sẵn" and spoken is None:
        st.warning("Vui lòng tải file lời đọc.")
    elif ai_images and (not scenes or any(not s['text'].strip() or not s['prompt'].strip() for s in scenes)):
        st.warning("Mỗi cảnh cần có lời đọc và mô tả ảnh.")
    else:
        st.session_state.pop("result", None)
        try:
            with TemporaryDirectory(prefix="video-studio-") as folder:
                work = Path(folder)
                paths = []
                for i, upload in enumerate(uploads):
                    path = work / f"media_{i}{Path(upload.name).suffix.lower()}"
                    path.write_bytes(upload.getvalue())
                    paths.append(path)
                bgm = None
                if music:
                    bgm = work / f"bgm{Path(music.name).suffix.lower()}"
                    bgm.write_bytes(music.getvalue())
                with st.status("Đang tạo video…", expanded=True) as status:
                    durations = None
                    if spoken is not None:
                        narration = work / f"narration{Path(spoken.name).suffix.lower()}"
                        narration.write_bytes(spoken.getvalue())
                        if ai_images:
                            from ai_services import generate_image
                            for i, scene in enumerate(scenes):
                                st.write(f"Tạo ảnh cảnh {i+1}/{len(scenes)}")
                                paths.append(generate_image(scene['prompt'], work / f"scene_{i}.png", api_key, aspect == "Dọc 9:16"))
                    else:
                        planned = scenes if ai_images else [{"text": script, "prompt": ""}]
                        generated, narration, durations = prepare_scenes(planned, work, voice,
                            provider, api_key, ai_images, aspect == "Dọc 9:16", st.write)
                        if ai_images:
                            paths = generated
                        else:
                            durations = None
                    st.write("Ghép cảnh, trộn nhạc và xuất MP4…")
                    sizes = {"Ngang 16:9": (1280, 720), "Dọc 9:16": (720, 1280), "Vuông 1:1": (720, 720)}
                    result = render_video(paths, narration, work / "video.mp4", bgm,
                        size=sizes[aspect], transition=transition, bgm_volume=volume, scene_durations=durations)
                    st.session_state.result = result.read_bytes()
                    status.update(label="Video đã hoàn tất", state="complete")
        except Exception as exc:
            st.error("Chưa tạo được video. " + str(exc) if isinstance(exc, RuntimeError) else
                     "Không đọc được tư liệu hoặc xuất video thất bại. Xem chi tiết bên dưới.")
            if not isinstance(exc, RuntimeError):
                with st.expander("Chi tiết lỗi"):
                    st.code(type(exc).__name__)
            st.info("Nếu Edge TTS không hoạt động, có thể chọn OpenAI TTS (cần API key) "
                    "hoặc tải file lời đọc tự thu. Ứng dụng không tự đổi sang dịch vụ có phí.")
if "result" in st.session_state:
    st.video(st.session_state.result)
    st.download_button("Tải video MP4", st.session_state.result, file_name="video.mp4", mime="video/mp4")
