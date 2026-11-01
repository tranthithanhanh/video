"""Shared UI-independent scene workflow."""
from pathlib import Path
import subprocess

from moviepy.config import FFMPEG_BINARY
from ai_services import generate_image, synthesize_openai
from video_engine import synthesize, load_audio


def prepare_scenes(scenes, work: Path, voice: str, provider="Edge TTS",
                   key="", ai_images=False, portrait=False, progress=None):
    media, durations = [], []
    for i, scene in enumerate(scenes):
        if progress:
            progress(f"Cảnh {i + 1}/{len(scenes)} — tạo lời đọc")
        audio = work / f"speech_{i:03d}.mp3"
        if provider == "OpenAI TTS":
            synthesize_openai(scene["text"], audio, key, voice)
        else:
            synthesize(scene["text"], audio, voice)
        clip = load_audio(audio)
        durations.append(clip.duration)
        clip.close()
        if ai_images:
            if progress:
                progress(f"Cảnh {i + 1}/{len(scenes)} — tạo ảnh AI")
            media.append(generate_image(scene["prompt"], work / f"scene_{i:03d}.png",
                                        key, portrait))
    # Own generated filenames avoid quoting/path traversal issues in manifests.
    manifest = work / "speech.txt"
    manifest.write_text("".join(f"file 'speech_{i:03d}.mp3'\n"
                               for i in range(len(scenes))), encoding="utf-8")
    narration = work / "narration.mp3"
    subprocess.run([FFMPEG_BINARY, "-v", "error", "-y", "-f", "concat", "-safe", "0",
        "-i", str(manifest), "-c:a", "libmp3lame", str(narration)],
        capture_output=True, check=True)
    return media, narration, durations
