"""LLM script generation: a one-line theme -> a full story (scenes with Japanese
narration + English image prompts). Requires OPENAI_API_KEY in the environment.
"""

import json
import os
import re

SYSTEM = "You write short narrated video scripts. Respond with JSON only, no markdown."


def _slug(s):
    s = re.sub(r"[^a-z0-9]+", "_", str(s).lower()).strip("_")
    return s or "story"


def generate_story(theme, n_scenes=4, model="gpt-4o-mini"):
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Set it once with:\n"
            '  [Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "<your-key>", "User")\n'
            "then open a NEW terminal and retry."
        )
    from openai import OpenAI

    user = f"""Theme: {theme}

Write a VERTICAL YouTube SHORT about this theme, directing it like an editor with shot types.
It must HOOK in the first 2-3 seconds and end with a surprising twist + a thought-provoking takeaway.
Return JSON exactly in this shape (no extra keys):
{{
  "name": "<short slug, lowercase a-z 0-9 and underscores only>",
  "title": "<a short punchy JAPANESE title for the whole video>",
  "mood": "<2-3 word ENGLISH background-music mood, e.g. calm ambient, eerie, wondrous, tense>",
  "scenes": [
    {{
      "type": "title | scene | statement",
      "narration": "<one or two sentences, natural JAPANESE, spoken in every shot>",
      "image": "<an ENGLISH image-generation prompt, concrete and cinematic, no text in image>",
      "title": "<JAPANESE big title text — ONLY for type=title>",
      "text": "<a short JAPANESE punch line shown big — ONLY for type=statement>",
      "emphasis": "<a short JAPANESE phrase that appears inside narration — ONLY for type=scene, optional>"
    }}
  ]
}}

Structure (a Short's arc — IMPORTANT):
- Shot 1: type "title" = the HOOK. "title" is a short, punchy, scroll-stopping line (a bold claim or question, ~12 chars or so). "narration" speaks that hook in one short line.
- Then {n_scenes} shots of type "scene" = escalating "wow" beats. Give each an "emphasis" key phrase (an exact substring of that beat's narration) shown enlarged.
- ONE shot of type "statement" = the TWIST: a surprising or counter-intuitive turn. Put the punch line in "text".
- Final shot of type "statement" = the PAYOFF: a short thought-provoking takeaway that ALSO asks the viewer a question. Put it in "text".

Rules:
- narration: SHORT, punchy JAPANESE — mostly ONE sentence per shot. Fast pace. Build curiosity, deliver a surprise, land an insight.
- narration must be CLEAN prose ONLY. NEVER append, repeat, or quote the emphasis phrase at the end of narration.
- emphasis MUST be an exact substring of that scene's narration.
- image: ENGLISH; ONE consistent epic/cinematic style across ALL shots; compose for a VERTICAL 9:16 frame.
"""
    client = OpenAI()
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": SYSTEM},
                  {"role": "user", "content": user}],
        response_format={"type": "json_object"},
        temperature=0.9,
    )
    data = json.loads(resp.choices[0].message.content)

    scenes = data.get("scenes") or []
    if not scenes:
        raise RuntimeError("LLM returned no scenes")
    norm = []
    for s in scenes:
        if not s.get("narration") or not s.get("image"):
            continue
        nar = str(s.get("narration", "")).strip()
        em = str(s.get("emphasis", "")).strip()
        # defensive: strip a trailing echoed/quoted emphasis the model sometimes appends
        if em:
            for wrap in (f'"{em}"', f'“{em}”', f'「{em}」', f'＂{em}＂'):
                if nar.endswith(wrap):
                    nar = nar[:-len(wrap)].rstrip()
                    break
        sc = {
            "type": (s.get("type") or "scene").strip(),
            "narration": nar,
            "image": str(s.get("image", "")).strip(),
        }
        if s.get("title"):
            sc["title"] = str(s["title"]).strip()
        if s.get("text"):
            sc["text"] = str(s["text"]).strip()
        if em:
            sc["emphasis"] = em
        norm.append(sc)
    data["scenes"] = norm
    data["name"] = _slug(data.get("name") or theme)
    data.setdefault("seed", 7)
    return data
