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

# The industry-standard marker that says "made by an AI model". Meta reads it
# (with C2PA) to put the "AI info" label on a post.
#
# brand.md requires every AI asset to carry the platform's AI label. Posting by
# hand, that was a toggle in the app. Posting through the API there is no
# toggle — the only way to disclose is to carry the marker in the file itself.
# And this module was removing it: every photo is re-encoded here, and a
# re-encode drops whatever metadata the generator attached. So the pipeline was
# quietly breaking a disclosure rule Umer set in July.
#
# It is written into the JPEG as a metadata block without re-encoding the
# pixels. Cards are NOT tagged: they are built on real product photography, and
# labelling them AI would be its own false statement.
AI_XMP = (b'<?xpacket begin="\xef\xbb\xbf" id="W5M0MpCehiHzreSzNTczkc9d"?>'
          b'<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF '
          b'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
          b'<rdf:Description rdf:about="" '
          b'xmlns:Iptc4xmpExt="http://iptc.org/std/Iptc4xmpExt/2008-02-29/" '
          b'Iptc4xmpExt:DigitalSourceType='
          b'"http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia"/>'
          b'</rdf:RDF></x:xmpmeta>'
          b'<?xpacket end="w"?>')
_XMP_NS = b"http://ns.adobe.com/xap/1.0/\x00"


def tag_ai(path: str | Path) -> bool:
    """
    Insert the AI marker into an existing JPEG, losslessly. Idempotent.
    Returns True if the file was changed.
    """
    path = Path(path)
    data = path.read_bytes()
    if b"trainedAlgorithmicMedia" in data:
        return False
    if data[:2] != b"\xff\xd8":
        raise ValueError(f"{path} is not a JPEG")
    payload = _XMP_NS + AI_XMP
    seg = b"\xff\xe1" + (len(payload) + 2).to_bytes(2, "big") + payload
    # After SOI, and after a JFIF APP0 if there is one, which must come first.
    at = 2
    if data[2:4] == b"\xff\xe0":
        at = 4 + int.from_bytes(data[4:6], "big")
    path.write_bytes(data[:at] + seg + data[at:])
    return True
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
        tag_ai(path)
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
