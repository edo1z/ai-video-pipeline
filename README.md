# ai-video-pipeline

Turn a one-line theme into a narrated, subtitled **vertical short video** — fully automated.
An LLM writes the script, images are AI-generated, and ffmpeg assembles the motion, captions,
color grade and music.

Unlike "stock-footage" tools, this **generates** every image, so the visuals always match the
script (no clip-matching problem). The output is 9:16 (1080×1920), sized for YouTube Shorts /
Reels / TikTok.

## Pipeline

```
theme ─▶ LLM script ─▶ generated images ─▶ Ken Burns ─▶ TTS ─▶ subtitles ─▶ color grade ─▶ music ─▶ .mp4
```

| Stage | Default |
|---|---|
| Script | OpenAI (writes a Shorts arc: hook → beats → twist → payoff) |
| Images | OpenAI `gpt-image-1` (portrait), then aspect-fill crop |
| Motion | ffmpeg `zoompan` (Ken Burns) with per-shot variety |
| Narration | OpenAI TTS (falls back to Windows SAPI offline) |
| Subtitles | Pillow-rendered PNG overlays (title / emphasis / caption) |
| Look | consistent color grade + vignette on every shot |
| Music | a file in `music/`, else a synthesized ambient bed |

## Story / shot structure

Each video is a list of **shots**, each with a type that controls how it's shown:

- `title` — the **hook**: a big, scroll-stopping line over a dimmed/blurred image
- `scene` — a beat with a lower-third caption; an `emphasis` phrase is shown enlarged + colored
- `statement` — a held "beat" shot with one big centered line (used for the twist and the payoff)

The LLM is prompted to write this as a Short: **hook → escalating beats → twist → payoff + a
question to the viewer.**

## Requirements

- `ffmpeg` / `ffprobe` on PATH
- `OPENAI_API_KEY` in the environment (used for the script, images, and voice)
- Windows for the offline SAPI voice fallback (otherwise OpenAI TTS is used)

## Usage

From a one-line theme (the LLM writes the script):

```bash
uv sync
uv run python make_video.py --theme "what would happen if you fell into a black hole"
uv run python make_video.py --theme "the strangest deep-sea creatures" --scenes 4
# output: output/<name>.mp4 (1080x1920)
```

From a hand-written story JSON (recommended for **fact-based** videos, so you control accuracy):

```bash
uv run python make_video.py stories/sharks_older_than_trees.json
```

Generated scripts are saved to `stories/<name>.json` so you can edit and re-render them.

## Structure

| File | Role |
|---|---|
| `make_video.py` | Orchestrator (script → images → audio → subtitles → clips → music) |
| `pipeline/script.py` | LLM script generation (theme → shot JSON) |
| `pipeline/images.py` | Image generation (gpt-image-1 → Pollinations → placeholder) |
| `pipeline/tts.py` | Narration (OpenAI TTS / Windows SAPI) + duration probe |
| `pipeline/subtitles.py` | Pillow text overlays (title / statement / emphasis caption) |
| `pipeline/video.py` | Ken Burns, color grade + vignette, overlay, concat (ffmpeg) |
| `pipeline/music.py` | Background music (file or synthesized) + ducked mix |

## Notes

- **Cost**: each video makes ~6 `gpt-image-1` images (~$0.04 each) plus TTS — roughly $0.2–0.3 per video.
  Drop quality to `low` in `pipeline/images.py` to cut it further.
- **Accuracy**: an LLM can invent "facts". For fact-based videos, write the story JSON yourself
  (verified) and render from it, rather than using `--theme`.
- **Music**: drop a royalty-free `music/default.mp3` (e.g. from pixabay.com/music) for real audio;
  otherwise a basic synthesized ambient bed is used.

## License

MIT — see [LICENSE](LICENSE).
