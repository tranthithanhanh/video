"""Vietnamese narration and deterministic MoviePy 2 video rendering."""
from __future__ import annotations

import asyncio
import os
import subprocess
from contextlib import ExitStack
from pathlib import Path

import edge_tts
from edge_tts import communicate as edge_communicate
import numpy as np
from moviepy.audio.AudioClip import AudioArrayClip
from moviepy.config import FFMPEG_BINARY
from moviepy import (
    AudioClip, ColorClip, CompositeAudioClip, CompositeVideoClip,
    ImageClip, VideoFileClip, afx, vfx,
)

VOICES = {"Nữ — Hoài My": "vi-VN-HoaiMyNeural", "Nam — Nam Minh": "vi-VN-NamMinhNeural"}
IMAGES = {".jpg", ".jpeg", ".png", ".webp"}


def synthesize(text: str, destination: Path, voice: str) -> None:
    """Requires access to Microsoft's online Edge speech service."""
    if not text.strip():
        raise ValueError("Vui lòng nhập kịch bản.")
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    # Edge TTS 7 builds its own certifi context. Add the system/SSL_CERT_FILE
    # trust roots for managed HTTPS proxies; certificate verification stays on.
    edge_communicate._SSL_CTX.load_default_certs()
    asyncio.run(edge_tts.Communicate(text.strip(), voice, proxy=proxy).save(str(destination)))


def load_audio(path: Path):
    """Decode once; avoid MoviePy 2.2.1's large-array reader buffer issue."""
    result = subprocess.run([FFMPEG_BINARY, "-v", "error", "-i", str(path),
        "-vn", "-f", "f32le", "-acodec", "pcm_f32le", "-ar", "44100",
        "-ac", "2", "pipe:1"], capture_output=True, check=True)
    samples = np.frombuffer(result.stdout, dtype="<f4").reshape(-1, 2).copy()
    if not len(samples):
        raise ValueError("Không đọc được dữ liệu âm thanh.")
    return AudioArrayClip(samples, fps=44100).with_duration(len(samples) / 44100)


def ducking_envelope(samples: np.ndarray, sample_rate: int,
                     duration: float, base_volume: float = 0.22):
    """RMS speech detection with anticipation, hold and smooth gain changes.

    Returns interpolation points for BGM gain. Silence keeps the selected gain;
    detected speech reduces it to 25% of that gain.
    """
    mono = np.asarray(samples, dtype=float)
    if mono.ndim == 2:
        mono = np.mean(mono, axis=1)
    block = max(1, int(sample_rate * 0.02))
    count = max(1, int(np.ceil(len(mono) / block)))
    padded = np.pad(mono, (0, count * block - len(mono)))
    rms = np.sqrt(np.mean(padded.reshape(count, block) ** 2, axis=1))
    threshold = max(0.008, float(rms.max()) * 0.08)
    speech = rms > threshold
    held = speech.copy()
    for shift in range(-5, 13):
        if shift < 0 and -shift < count:
            held[:shift] |= speech[-shift:]
        elif shift > 0 and shift < count:
            held[shift:] |= speech[:-shift]
    target = np.where(held, base_volume * 0.25, base_volume)
    gain = target.copy()
    for i in range(1, count):
        # Fast attack, gradual release; preserve continuous gain between windows.
        alpha = 0.55 if target[i] < gain[i - 1] else 0.08
        gain[i] = gain[i - 1] + alpha * (target[i] - gain[i - 1])
    times = np.arange(count) * block / sample_rate
    return np.append(times, max(duration, times[-1] + 0.02)), np.append(gain, gain[-1])


def render_video(media: list[Path], narration: Path, output: Path,
                 bgm: Path | None = None, size=(1280, 720), fps=24,
                 transition=0.4, bgm_volume=0.22) -> Path:
    """Fit all visuals to narration, looping short videos and discarding source audio.

    Crossfades overlap adjacent clips. All media readers close even on failure.
    Without uploads, render a neutral background for text-only narration.
    """
    with ExitStack() as stack:
        def own(clip):
            stack.callback(clip.close)
            return clip

        voice = own(load_audio(narration))
        duration = voice.duration
        if not duration or duration <= 0:
            raise ValueError("File giọng đọc không có thời lượng hợp lệ.")
        count = max(1, len(media))
        step = duration / count
        fade = min(max(0, transition), step / 2)
        layers = []
        for i in range(count):
            start = i * step
            length = step + (fade if i < count - 1 else 0)
            if not media:
                clip = own(ColorClip(size, color=(24, 32, 48), duration=length))
            elif media[i].suffix.lower() in IMAGES:
                clip = own(ImageClip(str(media[i])).with_duration(length))
            else:
                source = own(VideoFileClip(str(media[i]), audio=False))
                if not source.duration or source.duration <= 0:
                    raise ValueError(f"Video không hợp lệ: {media[i].name}")
                clip = source.with_effects([vfx.Loop(duration=length)])
            scale = max(size[0] / clip.w, size[1] / clip.h)
            clip = clip.resized(scale).cropped(
                x_center=clip.w * scale / 2, y_center=clip.h * scale / 2,
                width=size[0], height=size[1],
            ).with_duration(length).with_start(start)
            if i:
                clip = clip.with_effects([vfx.CrossFadeIn(fade)])
            layers.append(clip)

        audio = voice
        if bgm:
            music = own(load_audio(bgm))
            if not music.duration or music.duration <= 0:
                raise ValueError("Nhạc nền không có thời lượng hợp lệ.")
            looped = music.with_effects([afx.AudioLoop(duration=duration)])
            samples = voice.to_soundarray(fps=16000)
            times, gain = ducking_envelope(samples, 16000, duration, bgm_volume)

            def music_frame(t):
                values = looped.get_frame(t)
                volume = np.interp(t, times, gain)
                if np.ndim(t) and np.ndim(values) == 2:
                    volume = volume[:, None]
                return values * volume

            ducked = own(AudioClip(music_frame, duration=duration, fps=44100))
            # Bound the mix so simultaneous peaks cannot digitally clip.
            audio = own(CompositeAudioClip([
                voice.with_effects([afx.MultiplyVolume(0.85)]), ducked,
            ]).transform(lambda get_frame, t: np.clip(get_frame(t), -0.99, 0.99),
                         keep_duration=True))
        final = own(CompositeVideoClip(layers, size=size).with_duration(duration).with_audio(audio))
        output.parent.mkdir(parents=True, exist_ok=True)
        final.write_videofile(str(output), codec="libx264", audio_codec="aac",
                              temp_audiofile=str(output.with_suffix(".audio.m4a")),
                              fps=fps, preset="medium", threads=2, logger=None)
    return output
