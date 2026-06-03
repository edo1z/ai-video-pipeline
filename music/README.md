# music/

Drop royalty-free background tracks here. The pipeline picks one in this order:

1. `music/<mood>.mp3` — where `<mood>` is the story's mood (spaces → underscores),
   e.g. mood "calm ambient" → `music/calm_ambient.mp3`
2. `music/default.mp3` — used for any story if no mood-specific file exists
3. (fallback) a synthesized ambient drone — free but basic ("boooo")

So the easiest upgrade: download one calm/ambient track and save it as `music/default.mp3`.

Good free sources (commercial use OK, no attribution required):
- https://pixabay.com/music/  (search "ambient" / "calm")
- https://chosic.com/free-music/

mp3 files in this folder are git-ignored (so you don't commit copyrighted audio).
