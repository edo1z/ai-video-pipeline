"""Image provider.

Order: OpenAI (gpt-image-1) when OPENAI_API_KEY is set -> Pollinations (free, but now
often gated) -> a procedural placeholder gradient if everything fails.
"""

import base64
import hashlib
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

# Appended to every prompt so the whole video shares one look.
STYLE = "cinematic, dramatic lighting, highly detailed, digital painting, no text"


def fetch_image(prompt, path, width=1280, height=720, seed=0, retries=3):
    """Generate one image for `prompt` and save to `path`."""
    full = f"{prompt}, {STYLE}"
    if os.getenv("OPENAI_API_KEY"):
        try:
            _openai_image(full, path)
            return True
        except Exception as e:
            print(f"    openai image failed ({e}); trying Pollinations")
    if _pollinations(full, path, width, height, seed, retries):
        return True
    print("    image: falling back to placeholder")
    _placeholder(full, path, width, height)
    return False


def _openai_image(prompt, path, model="gpt-image-1", size="1024x1536", quality="medium"):
    from openai import OpenAI
    client = OpenAI()
    r = client.images.generate(model=model, prompt=prompt, size=size, quality=quality, n=1)
    Path(path).write_bytes(base64.b64decode(r.data[0].b64_json))


def _pollinations(prompt, path, width, height, seed, retries):
    q = urllib.parse.quote(prompt)
    url = (f"https://image.pollinations.ai/prompt/{q}"
           f"?width={width}&height={height}&nologo=true&seed={seed}")
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=150) as resp:
                data = resp.read()
            if len(data) > 2000:
                Path(path).write_bytes(data)
                return True
        except Exception as e:
            print(f"    pollinations retry {attempt + 1}/{retries}: {e}")
            time.sleep(2)
    return False


def _placeholder(text, path, w, h):
    from PIL import Image, ImageDraw
    seed = int(hashlib.md5(text.encode()).hexdigest(), 16)
    top = ((seed % 120) + 30, ((seed >> 8) % 120) + 20, ((seed >> 16) % 120) + 70)
    bot = (10, 14, 26)
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)], fill=tuple(int(top[i] * (1 - t) + bot[i] * t) for i in range(3)))
    img.save(path)
