"""Make a narrated, subtitled video with Ken Burns motion.

From a theme (LLM writes the script):
    uv run python make_video.py --theme "what if the Earth had two moons"
    uv run python make_video.py --theme "the strangest deep-sea creatures" --scenes 5

From a hand-written story JSON:
    uv run python make_video.py stories/two_moons.json
"""

import argparse
import json
from pathlib import Path

from pipeline import images, music, subtitles, tts, video

ROOT = Path(__file__).parent
OUT = ROOT / "output"
STORIES = ROOT / "stories"
TAIL = 0.5   # seconds of silence appended to each scene so narration isn't clipped


def _caption_runs(narration, emphasis):
    if emphasis and emphasis in narration:
        i = narration.index(emphasis)
        runs = []
        if narration[:i]:
            runs.append((narration[:i], "normal"))
        runs.append((emphasis, "em"))
        if narration[i + len(emphasis):]:
            runs.append((narration[i + len(emphasis):], "normal"))
        return runs
    return [(narration, "normal")]


def _render_overlay(sc, png):
    t = sc.get("type", "scene")
    if t == "title":
        subtitles.render_title(sc.get("title") or sc["narration"], png)
    elif t == "statement":
        subtitles.render_statement(sc.get("text") or sc["narration"], png)
    else:
        subtitles.render_caption(_caption_runs(sc["narration"], sc.get("emphasis")), png)


def run(story):
    base_seed = story.get("seed", 1)
    work = OUT / "work"
    work.mkdir(parents=True, exist_ok=True)

    clips = []
    kb = 0
    for i, sc in enumerate(story["scenes"]):
        t = sc.get("type", "scene")
        print(f"[shot {i + 1}/{len(story['scenes'])}] ({t}) {sc['narration']}")
        img = work / f"img_{i}.jpg"
        png = work / f"txt_{i}.png"
        clip = work / f"clip_{i}.mp4"

        print("  - generating image (Pollinations)...")
        images.fetch_image(sc["image"], img, seed=base_seed * 100 + i)
        print("  - synthesizing narration...")
        audio = tts.synthesize(sc["narration"], work / f"aud_{i}")
        dur = tts.probe_duration(audio) + TAIL
        print("  - rendering text overlay...")
        _render_overlay(sc, png)
        print(f"  - building shot clip ({dur:.1f}s)...")
        video.make_clip(t, img, png, audio, clip, dur, kb_index=kb)
        if t == "scene":
            kb += 1
        clips.append(clip)

    name = story.get("name", "video")
    narr = work / "_narration.mp4"
    print("[concat] joining scenes...")
    video.concat(clips, narr)

    print("[music] adding background music...")
    total = tts.probe_duration(narr)
    track = music.get_track(story.get("mood"), total, work / "bgm.mp3")

    final = OUT / f"{name}.mp4"
    music.mix(narr, track, final)
    print(f"\nDONE -> {final}")
    return final


def main():
    ap = argparse.ArgumentParser(description="Make a narrated video from a theme or a story JSON.")
    ap.add_argument("story", nargs="?", help="path to a story JSON")
    ap.add_argument("--theme", help="generate the script from a one-line theme via LLM")
    ap.add_argument("--scenes", type=int, default=4, help="number of scenes (with --theme)")
    ap.add_argument("--model", default="gpt-4o-mini", help="OpenAI model for script generation")
    args = ap.parse_args()

    if args.theme:
        from pipeline import script
        print(f"[script] generating from theme: {args.theme!r} ...")
        story = script.generate_story(args.theme, args.scenes, args.model)
        STORIES.mkdir(exist_ok=True)
        sp = STORIES / f"{story['name']}.json"
        sp.write_text(json.dumps(story, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[script] saved -> {sp}")
        for s in story["scenes"]:
            print(f"    - {s['narration']}")
    elif args.story:
        story = json.loads(Path(args.story).read_text(encoding="utf-8"))
    else:
        story = json.loads((STORIES / "two_moons.json").read_text(encoding="utf-8"))

    run(story)


if __name__ == "__main__":
    main()
