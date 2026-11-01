from pathlib import Path
from unittest.mock import AsyncMock

import edge_tts
import numpy as np
import pytest
from moviepy import AudioClip

import video_engine as engine


def test_transient_failure_retries_segments_without_duplicate_audio(tmp_path, monkeypatch):
    sample = tmp_path / "sample.mp3"
    clip = AudioClip(lambda t: 0.1 * np.sin(2 * np.pi * 220 * t),
                     duration=0.3, fps=16000)
    clip.write_audiofile(str(sample), codec="libmp3lame", logger=None)
    clip.close()
    calls = []

    class FakeTTS:
        def __init__(self, text, *args, **kwargs):
            self.text = text

        async def save(self, path):
            calls.append(self.text)
            if len(calls) == 1:
                Path(path).write_bytes(b"incomplete")
                raise edge_tts.exceptions.NoAudioReceived("temporary failure")
            Path(path).write_bytes(sample.read_bytes())

    monkeypatch.setattr(engine.edge_tts, "Communicate", FakeTTS)
    monkeypatch.setattr(engine.asyncio, "sleep", AsyncMock())
    output = tmp_path / "voice.mp3"
    engine.synthesize("Xin chào các bạn. " * 40, output, "vi-VN-HoaiMyNeural")
    assert len(calls) == 3
    assert calls[0] == calls[1]
    decoded = engine.load_audio(output)
    assert 0.5 < decoded.duration < 1.1
    decoded.close()
    assert not list(tmp_path.glob("tts-*"))


def test_persistent_failure_preserves_existing_output(tmp_path, monkeypatch):
    save = AsyncMock(side_effect=edge_tts.exceptions.NoAudioReceived("unavailable"))

    class FailedTTS:
        def __init__(self, *args, **kwargs):
            self.save = save

    monkeypatch.setattr(engine.edge_tts, "Communicate", FailedTTS)
    monkeypatch.setattr(engine.asyncio, "sleep", AsyncMock())
    output = tmp_path / "voice.mp3"
    output.write_bytes(b"previous result")
    with pytest.raises(RuntimeError, match="sau 3 lần thử"):
        engine.synthesize("Xin chào", output, "vi-VN-HoaiMyNeural")
    assert save.await_count == 3
    assert output.read_bytes() == b"previous result"
    assert not list(tmp_path.glob("tts-*"))
