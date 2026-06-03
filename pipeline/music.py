"""Background music. Uses a track from music/<mood>.mp3 (or music/default.mp3) if
present; otherwise synthesizes a calm ambient pad with ffmpeg (free, no copyright).
Then mixes it under the narration with fades.
"""

import subprocess
from pathlib import Path

MUSIC_DIR = Path(__file__).parent.parent / "music"


def _run(cmd):
    p = subprocess.run(cmd, capture_output=True)
    if p.returncode != 0:
        raise RuntimeError("ffmpeg(music) failed:\n" + p.stderr.decode("utf-8", "replace")[-2000:])


def generate_ambient(out, duration):
    """A soft, slow ambient drone (low chord + tremolo + lowpass + echo)."""
    d = f"{duration:.2f}"
    fade_out = f"{max(0.0, duration - 3):.2f}"
    fc = (
        f"sine=frequency=110:duration={d},volume=0.5[a];"
        f"sine=frequency=164.81:duration={d},volume=0.45[b];"
        f"sine=frequency=220:duration={d},volume=0.42[c];"
        f"sine=frequency=329.63:duration={d},volume=0.32[e];"
        f"sine=frequency=440:duration={d},volume=0.18[f];"
        f"[a][b][c][e][f]amix=inputs=5:normalize=0,"
        f"tremolo=f=0.12:d=0.5,lowpass=f=2200,aecho=0.8:0.7:550|800:0.4|0.3,"
        f"loudnorm=I=-18:TP=-1.0,"
        f"afade=t=in:d=3,afade=t=out:st={fade_out}:d=3"
    )
    _run(["ffmpeg", "-y", "-filter_complex", fc, "-t", d, "-ar", "44100", "-ac", "2", str(out)])


def get_track(mood, duration, out):
    """Pick a music file by mood, else fall back to a generated ambient bed."""
    for name in [f"{(mood or '').lower().replace(' ', '_')}.mp3", "default.mp3"]:
        cand = MUSIC_DIR / name
        if name != ".mp3" and cand.exists():
            return cand
    generate_ambient(out, duration)
    return out


def mix(video_in, music_path, out, music_volume=0.38):
    """Mix BGM under the narration (kept loud), looped to length, with a 2s fade-in."""
    fc = (f"[1:a]aloop=loop=-1:size=200000000,volume={music_volume},afade=t=in:d=2[bg];"
          f"[0:a][bg]amix=inputs=2:duration=first:normalize=0[a]")
    _run(["ffmpeg", "-y", "-i", str(video_in), "-i", str(music_path),
          "-filter_complex", fc, "-map", "0:v", "-map", "[a]",
          "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", str(out)])
