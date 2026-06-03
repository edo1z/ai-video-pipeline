"""ffmpeg glue. Builds one clip per shot (background treatment depends on the shot
type), applies a consistent color grade + vignette to the image layer, overlays the
text with a fade-in, muxes audio, then concatenates."""

import os
import subprocess
import tempfile

# One cinematic look applied to EVERY shot's image (not the text), so the
# differently-toned AI images feel like a single film: gentle contrast/saturation,
# a slight cool teal cast, and a vignette to darken the corners.
GRADE = ("eq=contrast=1.08:saturation=1.10:gamma=0.97,"
         "colorbalance=rs=-0.02:bs=0.04:rm=-0.02:bm=0.03:bh=-0.02,"
         "vignette=PI/4.2")


def _run(cmd):
    p = subprocess.run(cmd, capture_output=True)
    if p.returncode != 0:
        raise RuntimeError("ffmpeg failed:\n" + " ".join(map(str, cmd)) + "\n"
                           + p.stderr.decode("utf-8", "replace")[-2500:])


def _background(shot_type, frames, kb_index, w, h, fps):
    """Return the [0:v]... chain (image -> Ken Burns) WITHOUT an output label.
    Aspect-preserving fill+crop so any source ratio fits the target frame."""
    fill = f"scale={w * 2}:{h * 2}:force_original_aspect_ratio=increase,crop={w * 2}:{h * 2}"
    if shot_type == "title":
        return (f"[0:v]{fill},boxblur=14:1,eq=brightness=-0.22:saturation=0.9,"
                f"zoompan=z='min(zoom+0.0006,1.14)':d={frames}"
                f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps}")
    if shot_type == "statement":
        return (f"[0:v]{fill},boxblur=4:1,eq=brightness=-0.45:saturation=0.7,"
                f"zoompan=z='min(zoom+0.0005,1.10)':d={frames}"
                f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps}")
    # scene: full Ken Burns, alternate motion per index
    x = "iw/2-(iw/zoom/2)" if kb_index % 2 == 0 else f"(iw-iw/zoom)*on/{frames}"
    return (f"[0:v]{fill},"
            f"zoompan=z='min(zoom+0.0012,1.3)':d={frames}"
            f":x='{x}':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps}")


def make_clip(shot_type, image, overlay, audio, out, dur, kb_index=0, fps=30, w=1080, h=1920):
    frames = max(1, int(round(dur * fps)))
    vf = (_background(shot_type, frames, kb_index, w, h, fps) + f",{GRADE}[bg];"
          "[1:v]format=rgba,fade=t=in:st=0:d=0.6:alpha=1[txt];"
          "[bg][txt]overlay=0:0[v]")
    _run([
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(image),
        "-loop", "1", "-i", str(overlay),
        "-i", str(audio),
        "-filter_complex", vf,
        "-map", "[v]", "-map", "2:a",
        "-t", f"{dur:.3f}", "-r", str(fps),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        str(out),
    ])


def concat(clips, out, fps=30):
    lst = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8")
    for c in clips:
        lst.write(f"file '{os.path.abspath(str(c)).replace(chr(92), '/')}'\n")
    lst.close()
    try:
        _run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst.name,
            "-r", str(fps), "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", str(out),
        ])
    finally:
        os.unlink(lst.name)
