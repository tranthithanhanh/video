from pathlib import Path

import numpy as np
from PIL import Image
from moviepy import AudioClip, ColorClip, VideoFileClip

from video_engine import ducking_envelope, render_video, load_audio


def test_ducking_detects_speech_and_recovers():
    rate = 16000
    t = np.arange(rate * 4) / rate
    samples = np.where((t > 1) & (t < 2), 0.3 * np.sin(2 * np.pi * 220 * t), 0)
    times, gains = ducking_envelope(samples, rate, 4)
    assert np.interp(1.5, times, gains) < 0.07
    assert np.interp(0.2, times, gains) > 0.2
    assert np.interp(3.8, times, gains) > 0.2


def test_render_images_short_video_and_bgm(tmp_path: Path):
    image = tmp_path / "image.png"
    Image.new("RGB", (120, 200), "red").save(image)
    video = tmp_path / "source.mp4"
    source = ColorClip((160, 90), color=(0, 0, 255), duration=0.3)
    source.write_videofile(str(video), fps=12, codec="libx264", logger=None)
    source.close()
    voice = tmp_path / "voice.wav"
    music = tmp_path / "music.wav"
    for path, duration in [(voice, 2), (music, 0.4)]:
        clip = AudioClip(lambda t: 0.15 * np.sin(2 * np.pi * 220 * t),
                         duration=duration, fps=16000)
        clip.write_audiofile(str(path), fps=16000, logger=None)
        clip.close()
    output = render_video([image, video], voice, tmp_path / "out.mp4", music,
                          size=(160, 90), fps=12)
    with VideoFileClip(str(output)) as result:
        assert abs(result.duration - 2) < 0.12
        assert result.size == [160, 90]
        assert result.audio is not None
        assert result.get_frame(0.2)[45, 80, 0] > 200
        assert result.get_frame(1.8)[45, 80, 2] > 200
        mixed = result.get_frame(1.2)[45, 80]
        assert mixed[0] > 30 and mixed[2] > 30
        decoded = load_audio(output)
        assert np.max(np.abs(decoded.to_soundarray(fps=8000))) > 0.01
        decoded.close()
    plain = render_video([], voice, tmp_path / "plain.mp4", size=(160, 90), fps=12)
    assert plain.stat().st_size > 1000
