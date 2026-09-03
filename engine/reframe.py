"""
Reframe one generated master into every platform ratio, deterministically.

Why one master and not three generations: every generation is another chance for
the model to draw the pan wrong (see automation/qc_regression/). Generating each
ratio natively would triple both the cost and the fidelity risk, and give three
different pans to QC. One master, checked once, cropped by arithmetic.

Why the master is 9:16: it is the tallest target, so 2:3 and 4:5 are both simple
centre crops of it. Nothing is ever upscaled or letterboxed.

    9:16  = 0.5625   master, as generated
    2:3   = 0.6667   Pinterest
    4:5   = 0.8000   Instagram / Facebook feed
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image

# name -> (ratio w/h, output pixels, platforms)
TARGETS = {
    "9x16": (9 / 16, (1080, 1920), "Reels · Stories · TikTok"),
    "2x3":  (2 / 3,  (1000, 1500), "Pinterest"),
    "4x5":  (4 / 5,  (1080, 1350), "Instagram feed · Facebook feed"),
}

JPEG_QUALITY = 88
# Crops are taken from the vertical centre of the master. The scene prompt asks
# for the pan in the central band precisely so this never clips it.
CROP_ANCHOR = 0.5


def reframe(master_path: str | Path, out_dir: str | Path, stem: str) -> dict[str, Path]:
    master = Image.open(master_path).convert("RGB")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}

    mw, mh = master.size
    for name, (ratio, (ow, oh), _) in TARGETS.items():
        # Take the full width and as much height as the ratio allows.
        crop_h = round(mw / ratio)
        if crop_h > mh:
            # Master is not tall enough (it should be) — fall back to full height
            # and crop width instead, so we degrade rather than fail.
            crop_h = mh
            crop_w = round(mh * ratio)
            left = round((mw - crop_w) * 0.5)
            box = (left, 0, left + crop_w, mh)
        else:
            top = round((mh - crop_h) * CROP_ANCHOR)
            box = (0, top, mw, top + crop_h)

        img = master.crop(box).resize((ow, oh), Image.LANCZOS)
        path = out_dir / f"{stem}__{name}.jpg"
        img.save(path, "JPEG", quality=JPEG_QUALITY, optimize=True,
                 progressive=True, subsampling=0)
        written[name] = path
    return written


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        sys.exit("usage: reframe.py <master image> <out dir> [stem]")
    src = Path(sys.argv[1])
    stem = sys.argv[3] if len(sys.argv) > 3 else src.stem
    for name, p in reframe(src, sys.argv[2], stem).items():
        w, h = Image.open(p).size
        print(f"  {name:5s} {w}x{h}  {p.stat().st_size/1024:6.0f} KB  {p.name}")
