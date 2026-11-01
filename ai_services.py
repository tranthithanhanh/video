"""OpenAI adapters. Keys stay in memory and are never written to disk."""
from __future__ import annotations

import base64
import re
from pathlib import Path

import requests

API_ROOT = "https://api.openai.com/v1"


def split_scenes(script: str, maximum: int = 6) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+|\n+", script.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return []
    maximum = max(1, min(int(maximum), 12))
    count = min(maximum, len(sentences))
    # Keep sentence order and distribute complete sentences across scenes.
    return [" ".join(sentences[i * len(sentences) // count:
                              (i + 1) * len(sentences) // count]) for i in range(count)]


def image_prompt(scene: str, style: str) -> str:
    return (f"Create one illustration for a Vietnamese narrated video. Visual style: {style}. "
            "Illustrate the meaning of the following narration with a concrete relevant scene. "
            "Keep the main subject centered for cropping. No lettering, captions, watermarks or logos. "
            f"Narration: {scene}")


class AIServiceError(RuntimeError):
    pass


def _request(endpoint: str, key: str, payload: dict):
    if not key.strip():
        raise AIServiceError("Chưa nhập API key OpenAI. Nhập khóa ở mục Cấu hình AI.")
    try:
        response = requests.post(f"{API_ROOT}/{endpoint}",
            headers={"Authorization": f"Bearer {key.strip()}"}, json=payload,
            timeout=(15, 180))
    except requests.Timeout:
        raise AIServiceError("Dịch vụ AI hết thời gian chờ. Chưa tự gửi lại để tránh tính phí trùng.") from None
    except requests.RequestException:
        raise AIServiceError("Không kết nối được dịch vụ AI. Kiểm tra Internet hoặc proxy.") from None
    if response.status_code != 200:
        messages = {401: "API key không hợp lệ hoặc đã hết hiệu lực.",
                    403: "Tài khoản hoặc chính sách mạng chưa cho phép dịch vụ AI này.",
                    429: "Dịch vụ AI giới hạn lượt gọi hoặc tài khoản chưa đủ hạn mức/số dư.",
                    400: "Dịch vụ từ chối yêu cầu. Kiểm tra nội dung hoặc quyền sử dụng mô hình."}
        # Never expose raw provider responses that might echo user secrets.
        raise AIServiceError(messages.get(response.status_code,
                             f"Dịch vụ AI gặp lỗi HTTP {response.status_code}."))
    return response


def generate_image(prompt: str, destination: Path, key: str, portrait=False) -> Path:
    response = _request("images/generations", key, {
        "model": "gpt-image-1", "prompt": prompt, "n": 1,
        "size": "1024x1536" if portrait else "1536x1024", "quality": "low",
        "output_format": "png",
    })
    try:
        data = base64.b64decode(response.json()["data"][0]["b64_json"], validate=True)
        destination.write_bytes(data)
        # Decode now so invalid image responses fail before video rendering.
        from PIL import Image
        with Image.open(destination) as image:
            image.verify()
    except (ValueError, KeyError, IndexError, OSError):
        destination.unlink(missing_ok=True)
        raise AIServiceError("Dịch vụ không trả về ảnh hợp lệ.") from None
    return destination


def synthesize_openai(text: str, destination: Path, key: str, voice="nova") -> Path:
    response = _request("audio/speech", key, {
        "model": "tts-1", "input": text, "voice": voice, "response_format": "mp3",
    })
    if not response.content:
        raise AIServiceError("Dịch vụ AI trả âm thanh trống.")
    destination.write_bytes(response.content)
    return destination
