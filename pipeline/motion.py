"""Motion providers: turn a still keyframe into a short moving clip (image-to-video).

Pluggable on purpose — Sora's API is time-limited, so the rest of the pipeline stays
provider-agnostic and you can swap in Kling/Runway/Luma (via fal/Replicate) later.

Each provider: generate(keyframe, prompt, seconds, out) -> out (an mp4 path).
The clip's own audio is ignored downstream; narration/subtitles/BGM are added separately.
"""

import subprocess
import time
from pathlib import Path


def _prep(src, dst, w=720, h=1280):
    """Sora wants the input image to match the output size (720x1280 vertical)."""
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(src),
         "-vf", f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}", str(dst)],
        check=True, capture_output=True,
    )


def generate(provider, keyframe, prompt, seconds, out):
    if provider == "sora":
        return _sora(keyframe, prompt, seconds, out)
    raise NotImplementedError(f"motion provider '{provider}' not implemented (available: sora)")


def _sora(keyframe, prompt, seconds, out, model="sora-2", size="720x1280"):
    from openai import OpenAI
    client = OpenAI()
    key_in = Path(out).with_suffix(".in.png")
    _prep(keyframe, key_in)
    with open(key_in, "rb") as f:
        v = client.videos.create(model=model, prompt=prompt, input_reference=f,
                                 size=size, seconds=str(seconds))
    while v.status not in ("completed", "failed", "cancelled", "error"):
        time.sleep(5)
        v = client.videos.retrieve(v.id)
    if v.status != "completed":
        raise RuntimeError(f"Sora job {v.id} ended: {v.status}")
    client.videos.download_content(v.id, variant="video").write_to_file(str(out))
    return out
