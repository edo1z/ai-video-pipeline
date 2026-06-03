# ai-video-pipeline

Turn a one-line theme into a narrated, subtitled **vertical short video** — fully automated.
An LLM writes the script, images are AI-generated, and ffmpeg assembles the motion, captions,
color grade and music.

Unlike "stock-footage" tools, this **generates** every image, so the visuals always match the
script (no clip-matching problem). The output is 9:16 (1080×1920), sized for YouTube Shorts /
Reels / TikTok.

It can also make **character-driven story videos**: define a recurring cast once and keep them
consistent across scenes, each with their own voice — and optionally animate every shot with an
image-to-video model.

![character story demo](assets/cafe_cats.gif)

*A character story (`stories/cafe_cats.json`, rendered with `--motion sora`): two recurring cats
stay consistent across shots, each with its own voice, animated.*

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

## Character stories (consistent cast)

Add a `characters` block and the pipeline keeps a recurring cast looking the same across scenes:

1. Each character gets a **reference image** generated once from its description.
2. Every scene that features a character is generated from that reference (`gpt-image-1` edit),
   so the character stays consistent — minor drift, but recognizably the same.
3. Each character can have its own **voice**; scenes carry a `character` (or `characters`) and a `line`.

```json
{
  "characters": { "mike": { "desc": "a grey tabby kitten in a blue apron", "voice": "nova" } },
  "scenes": [ { "type": "scene", "character": "mike", "voice": "nova",
                "narration": "...", "image": "behind the cafe counter, flustered" } ]
}
```

## Motion (image-to-video)

By default each shot is a still with a Ken Burns pan/zoom. Pass `--motion <provider>` to instead
animate each keyframe into a real moving clip (its audio is dropped; narration/subtitles/grade/music
are layered on top). The provider is **pluggable**:

- `sora` — OpenAI Sora 2 (works with the same `OPENAI_API_KEY`). ⚠️ The Sora API is time-limited
  (sunset reported for late 2026), so don't depend on it long-term — swap in Kling/Runway/Luma later.

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

A character story, with real motion via Sora:

```bash
uv run python make_video.py stories/cafe_cats.json --motion sora
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
| `pipeline/video.py` | Ken Burns / motion-clip background, color grade + vignette, overlay, concat (ffmpeg) |
| `pipeline/music.py` | Background music (file or synthesized) + ducked mix |
| `pipeline/motion.py` | Image-to-video providers (Sora; pluggable) |

## Notes

- **Cost**: each video makes ~6 `gpt-image-1` images (~$0.04 each) plus TTS — roughly $0.2–0.3 per video.
  Drop quality to `low` in `pipeline/images.py` to cut it further.
- **Accuracy**: an LLM can invent "facts". For fact-based videos, write the story JSON yourself
  (verified) and render from it, rather than using `--theme`.
- **Music**: drop a royalty-free `music/default.mp3` (e.g. from pixabay.com/music) for real audio;
  otherwise a basic synthesized ambient bed is used.
- **Motion cost**: `--motion sora` adds ~$0.10/sec of video (Sora 2, 720p) — roughly $2–3 per short
  on top of the image/voice cost. Stills (the default) are far cheaper.

## License

MIT — see [LICENSE](LICENSE).
