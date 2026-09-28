"""
A fingerprint of exactly what Umer approved.

APPROVED used to record only that a month was approved, not WHAT was in it. So
anything that changed the month afterwards — a dropped post, a re-run caption, a
hand edit — was silently covered by an approval given to different content. The
daily poster would have put up words and pictures nobody had signed off.

The fingerprint covers what reaches the public and nothing else: each post's
date and id, its Instagram and Facebook caption, and the bytes of the 4:5 image
that is actually uploaded. Change any of those and the approval no longer
matches, and nothing posts until the month is approved again.

Uses only the standard library, because the approval workflow runs it on a bare
runner with no dependencies installed.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path


def digest(folder: Path) -> str:
    folder = Path(folder)
    bundle = json.loads((folder / "bundle.json").read_text(encoding="utf-8"))
    caps = bundle.get("captions") or {}
    h = hashlib.sha256()
    for p in sorted(bundle["posts"], key=lambda x: x["index"]):
        c = caps.get(p["id"]) or {}
        h.update(json.dumps([p["index"], p["date"], p["id"],
                             c.get("instagram", ""), c.get("facebook", "")],
                            ensure_ascii=False).encode("utf-8"))
        img = folder / f"{p['id']}__4x5.jpg"
        h.update(hashlib.sha256(img.read_bytes()).digest() if img.exists()
                 else b"missing")
    return h.hexdigest()[:16]


def approved_digest(folder: Path) -> str | None:
    """The fingerprint recorded in APPROVED, or None if absent or old-format."""
    f = Path(folder) / "APPROVED"
    if not f.exists():
        return None
    for line in f.read_text(encoding="utf-8").splitlines():
        if line.startswith("content:"):
            return line.split(":", 1)[1].strip() or None
    return None


if __name__ == "__main__":
    print(digest(Path(sys.argv[1])))
