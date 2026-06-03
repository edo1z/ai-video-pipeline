"""Render text overlays as transparent full-frame PNGs (Pillow gives full control
over Japanese text, sizes and colors). ffmpeg later overlays + fades these in.

Shot layouts:
  - render_title:     big centered title (for the title card)
  - render_statement: big centered line (for a "hold / beat" shot)
  - render_caption:   lower-third caption; an emphasized phrase is shown larger + colored
"""

import os

from PIL import Image, ImageDraw, ImageFont

_BODY = [r"C:\Windows\Fonts\meiryo.ttc"]
_BOLD = [r"C:\Windows\Fonts\YuGothB.ttc", r"C:\Windows\Fonts\meiryob.ttc", r"C:\Windows\Fonts\meiryo.ttc"]

CYAN = (0, 229, 255, 255)
ORANGE = (255, 138, 0, 255)
WHITE = (255, 255, 255, 255)


def _font(paths, size):
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _wrap_chars(items, max_w, draw):
    """items: list of (char, font, color). Returns list of lines (each a list of items)."""
    lines, cur, cur_w = [], [], 0
    for ch, f, col in items:
        if ch == "\n":
            lines.append(cur)
            cur, cur_w = [], 0
            continue
        w = draw.textlength(ch, font=f)
        if cur and cur_w + w > max_w:
            lines.append(cur)
            cur, cur_w = [], 0
        cur.append((ch, f, col))
        cur_w += w
    if cur:
        lines.append(cur)
    return lines


def _shadowed(d, x, y, ch, font, color):
    for dx in (-2, -1, 1, 2):
        for dy in (-2, -1, 1, 2):
            d.text((x + dx, y + dy), ch, font=font, fill=(0, 0, 0, 230))
    d.text((x, y), ch, font=font, fill=color)


def render_caption(runs, path, width=1080, height=1920, base=54, em=88):
    """runs: list of (text, kind) where kind is 'normal' or 'em'."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    fb, fe = _font(_BODY, base), _font(_BOLD, em)
    items = []
    for text, kind in runs:
        f = fe if kind == "em" else fb
        col = CYAN if kind == "em" else WHITE
        for ch in text:
            items.append((ch, f, col))
    lines = _wrap_chars(items, width - 110, d)

    def line_h(line):
        return max((f.size for _, f, _ in line), default=base) + 22

    total = sum(line_h(l) for l in lines)
    y = height - total - 360   # lifted off the very bottom (clear of Shorts UI)

    band = Image.new("RGBA", (width, total + 130), (0, 0, 0, 0))
    bd = ImageDraw.Draw(band)
    half = band.height / 2
    for yy in range(band.height):
        a = int(150 * (1 - abs(yy - half) / half))   # darkest in the middle, fades both ends
        bd.line([(0, yy), (width, yy)], fill=(0, 0, 0, a))
    img.alpha_composite(band, (0, y - 60))

    for line in lines:
        lw = sum(d.textlength(ch, font=f) for ch, f, _ in line)
        x = (width - lw) / 2
        h = line_h(line)
        for ch, f, col in line:
            _shadowed(d, x, y + (h - f.size - 18), ch, f, col)
            x += d.textlength(ch, font=f)
        y += h
    img.save(path)


def _render_big(text, path, width, height, size, color, y_frac, accent):
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = _font(_BOLD, size)
    items = [(ch, f, color) for ch in text]
    lines = _wrap_chars(items, width - 130, d)
    line_h = int(size * 1.32)
    total = line_h * len(lines)
    y0 = int(height * y_frac - total / 2)
    for i, line in enumerate(lines):
        lw = sum(d.textlength(ch, font=ff) for ch, ff, _ in line)
        x = (width - lw) / 2
        y = y0 + i * line_h
        for ch, ff, col in line:
            for dx in (-4, -3, 3, 4):
                for dy in (-4, -3, 3, 4):
                    d.text((x + dx, y + dy), ch, font=ff, fill=(0, 0, 0, 235))
            d.text((x, y), ch, font=ff, fill=col)
            x += d.textlength(ch, font=ff)
    if accent:
        lw = 360
        ax = (width - lw) / 2
        ay = y0 + total + 22
        d.rectangle([ax, ay, ax + lw, ay + 8], fill=accent)
    img.save(path)


def render_title(text, path, width=1080, height=1920):
    _render_big(text, path, width, height, size=112, color=WHITE, y_frac=0.42, accent=CYAN)


def render_statement(text, path, width=1080, height=1920):
    _render_big(text, path, width, height, size=84, color=WHITE, y_frac=0.46, accent=ORANGE)
