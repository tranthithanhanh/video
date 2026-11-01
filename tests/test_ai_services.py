import base64
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock

import numpy as np
import pytest
from PIL import Image
from moviepy import AudioClip, VideoFileClip

import ai_services as ai
import workflow
from video_engine import render_video


def test_scene_split_preserves_all_words_and_order():
    script = "Tiết kiệm tiền. Học kỹ năng! Tăng thu nhập? Đừng đầu tư mù quáng."
    scenes = ai.split_scenes(script, 3)
    assert len(scenes) == 3
    assert " ".join(scenes) == script
    assert " ".join(ai.split_scenes("Giữ tiền\nHọc kỹ năng\nĐầu tư", 2)) == "Giữ tiền Học kỹ năng Đầu tư"


def test_image_request_and_auth_error_are_safe(tmp_path, monkeypatch):
    buffer = BytesIO()
    Image.new("RGB", (20, 30), "red").save(buffer, format="PNG")
    response = Mock(status_code=200)
    response.json.return_value = {"data": [{"b64_json": base64.b64encode(buffer.getvalue()).decode()}]}
    post = Mock(return_value=response)
    monkeypatch.setattr(ai.requests, "post", post)
    path = ai.generate_image("Một người tiết kiệm", tmp_path / "image.png", "test-key", True)
    assert path.exists()
    assert post.call_args.kwargs['json']['size'] == '1024x1536'
    assert post.call_args.kwargs['json']['prompt'] == 'Một người tiết kiệm'
    response.status_code = 401
    with pytest.raises(ai.AIServiceError, match="API key không hợp lệ"):
        ai.synthesize_openai("Xin chào", tmp_path / "voice.mp3", "test-key")


def test_scene_pipeline_uses_individual_narration_durations(tmp_path, monkeypatch):
    def speech(text, path, key, voice):
        length = 0.5 if text == "Ngắn." else 1.5
        clip = AudioClip(lambda t: .1 * np.sin(2 * np.pi * 220 * t), duration=length, fps=16000)
        clip.write_audiofile(str(path), codec="libmp3lame", logger=None)
        clip.close()

    def image(prompt, path, key, portrait):
        Image.new("RGB", (160, 90), "red" if prompt == "red" else "blue").save(path)
        return path

    monkeypatch.setattr(workflow, "synthesize_openai", speech)
    monkeypatch.setattr(workflow, "generate_image", image)
    scenes = [{"text": "Ngắn.", "prompt": "red"}, {"text": "Dài hơn.", "prompt": "blue"}]
    media, voice, durations = workflow.prepare_scenes(scenes, tmp_path, "nova", "OpenAI TTS", "fake", True)
    assert durations[1] > durations[0] * 2
    output = render_video(media, voice, tmp_path / "out.mp4", size=(160, 90), fps=12,
                          transition=0, scene_durations=durations)
    with VideoFileClip(str(output)) as video:
        assert video.get_frame(.2)[45, 80, 0] > 200
        # Second scene must start near 0.5s, not halfway through the full video.
        assert video.get_frame(.8)[45, 80, 2] > 200
