"""
Render the code-built cards: education claims and customer reviews.

These are composited onto REAL photographs of the pan, never generated. That is
the whole reason they exist — a card carries a claim or a customer's words, and
neither should sit on top of a pan a model invented. Zero fidelity risk by
construction.

Each ratio is rendered natively rather than cropped from one master, because the
text has to be laid out for the shape it will be seen in. A 9:16 story and a 4:5
feed post want different line lengths.
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = Path(__file__).parent
FONTS = HERE / "fonts"
ROOT = HERE.parent

RATIOS = {"4x5": (1080, 1350), "2x3": (1000, 1500), "9x16": (1080, 1920)}

# Warm, not gloomy — brand.md was revised away from heavy shadow on 3 Sep.
INK = (255, 253, 250)
MUTED = (232, 226, 217)
AMBER = (232, 168, 67)
JPEG_QUALITY = 90


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / f"{name}.ttf"), size)


def cover(img: Image.Image, w: int, h: int, lift: float = 0.0) -> Image.Image:
    """
    Fill w x h without distorting.

    `lift` shifts the photograph upward inside the frame so the pan sits in the
    top half and the text gets the bottom to itself. The first draft laid the
    headline straight across the pan, which hides the product — the one thing the
    card is selling.
    """
    src_r, dst_r = img.width / img.height, w / h
    if src_r > dst_r:
        new_w = int(img.height * dst_r)
        img = img.crop(((img.width - new_w) // 2, 0,
                        (img.width - new_w) // 2 + new_w, img.height))
    else:
        new_h = int(img.width / dst_r)
        top = int((img.height - new_h) * 0.5)
        img = img.crop((0, top, img.width, top + new_h))
    img = img.resize((w, h), Image.LANCZOS)

    if lift > 0:
        shift = int(h * lift)
        canvas = Image.new("RGB", (w, h))
        scaled = img.resize((w, h - shift), Image.LANCZOS)
        canvas.paste(scaled, (0, 0))
        # extend the last row downward so the band under the photo is not black
        tail = scaled.crop((0, scaled.height - 2, w, scaled.height))
        canvas.paste(tail.resize((w, shift + 2)), (0, scaled.height - 2))
        img = canvas
    return img


def scrim(base: Image.Image, strength: float = 0.9, start: float = 0.42):
    """
    Darken the lower band the text sits on, fading up to nothing.

    The first draft faded in from 25% at 0.72 strength, which left white type
    sitting on bright wood and on the lit side of the pan — legible on a desktop,
    marginal on a phone in daylight. It now reaches `strength` at the bottom and
    only begins at `start`, so the top of the photograph is untouched and the type
    always has something solid under it.
    """
    w, h = base.size
    grad = Image.new("L", (1, h))
    for y in range(h):
        t = max(0.0, (y / h - start) / (1 - start)) ** 0.85
        grad.putpixel((0, y), int(255 * strength * t))
    mask = grad.resize((w, h))
    dark = Image.new("RGB", (w, h), (12, 10, 9))
    return Image.composite(dark, base, mask)


def wrap(draw, text: str, fnt, max_w: int) -> list[str]:
    words, lines, line = text.split(), [], ""
    for word in words:
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=fnt) <= max_w or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def draw_stars(d: ImageDraw.ImageDraw, x: int, y: int, size: int, n: int = 5):
    """Drawn, not typed — a star glyph is a font-availability gamble."""
    import math
    for i in range(n):
        cx, cy = x + i * int(size * 1.35) + size / 2, y + size / 2
        pts = []
        for k in range(10):
            r = size / 2 if k % 2 == 0 else size / 4.6
            a = math.radians(-90 + k * 36)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        d.polygon(pts, fill=AMBER)


def _brand(d: ImageDraw.ImageDraw, w: int, h: int, pad: int):
    f = font("Lato-Black", max(18, w // 48))
    text = "I R O N R O O T"
    d.text(((w - d.textlength(text, font=f)) / 2, h - pad + int(h * 0.005)),
           text, font=f, fill=MUTED)


def education_card(photo: Path, headline: str, sub: str, out_dir: Path,
                   stem: str) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = {}
    src = Image.open(photo).convert("RGB")
    for name, (w, h) in RATIOS.items():
        img = scrim(cover(src, w, h, lift=0.10), 0.9, 0.40)
        d = ImageDraw.Draw(img)
        pad = int(w * 0.085)
        max_w = w - pad * 2

        f_head = font("Lato-Black", int(w * 0.092))
        f_sub = font("Lato-Regular", int(w * 0.042))
        head = wrap(d, headline, f_head, max_w)
        subl = wrap(d, sub, f_sub, max_w) if sub else []

        lh_h = int(w * 0.092 * 1.12)
        lh_s = int(w * 0.042 * 1.45)
        block = len(head) * lh_h + (int(w * 0.05) + len(subl) * lh_s if subl else 0)
        y = h - pad - int(h * 0.055) - block

        for line in head:
            d.text((pad, y), line, font=f_head, fill=INK)
            y += lh_h
        if subl:
            y += int(w * 0.02)
            d.line([(pad, y), (pad + int(w * 0.11), y)], fill=AMBER, width=4)
            y += int(w * 0.03)
            for line in subl:
                d.text((pad, y), line, font=f_sub, fill=MUTED)
                y += lh_s

        _brand(d, w, h, pad)
        p = out_dir / f"{stem}__{name}.jpg"
        img.save(p, "JPEG", quality=JPEG_QUALITY, optimize=True, subsampling=0)
        written[name] = p
    return written


def review_card(photo: Path, quote: str, name_: str, out_dir: Path,
                stem: str) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = {}
    src = Image.open(photo).convert("RGB")
    for name, (w, h) in RATIOS.items():
        img = scrim(cover(src, w, h, lift=0.08), 0.92, 0.36)
        d = ImageDraw.Draw(img)
        pad = int(w * 0.085)
        max_w = w - pad * 2

        f_q = ImageFont.truetype(str(FONTS / "Lora-Italic-Variable.ttf"),
                                 int(w * 0.052))
        f_n = font("Lato-Semibold", int(w * 0.036))
        lines = wrap(d, f'"{quote}"', f_q, max_w)
        lh = int(w * 0.052 * 1.5)
        star = int(w * 0.035)

        block = star + int(w * 0.055) + len(lines) * lh + int(w * 0.06)
        y = h - pad - int(h * 0.055) - block

        draw_stars(d, pad, y, star)
        y += star + int(w * 0.055)
        for line in lines:
            d.text((pad, y), line, font=f_q, fill=INK)
            y += lh
        y += int(w * 0.025)
        d.text((pad, y), f"— {name_}", font=f_n, fill=MUTED)

        _brand(d, w, h, pad)
        p = out_dir / f"{stem}__{name}.jpg"
        img.save(p, "JPEG", quality=JPEG_QUALITY, optimize=True, subsampling=0)
        written[name] = p
    return written
