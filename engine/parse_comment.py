"""
Turn an issue comment into a decision.

Old rule: only "redo <number> - <note>" counted. Anything else fell through to
"none" and NOTHING happened — Umer commented "redo", nothing ran, and the loop
looked broken. Requiring him to remember a syntax was the mistake.

New rule, deliberately blunt:

    starts with "approve"  -> approve
    ANYTHING ELSE          -> feedback, and the whole comment is the instruction

An image number is used if one appears; otherwise the note applies to every image
that week. An empty note means a plain re-roll of the same scene, which is a
perfectly normal thing to want and used to be impossible to ask for.

A redo costs about ten cents and publishes nothing, so acting on an ambiguous
comment is much cheaper than ignoring a real one.
"""
from __future__ import annotations
import re

ORDINALS = {"first": 1, "second": 2, "third": 3, "fourth": 4,
            "1st": 1, "2nd": 2, "3rd": 3, "4th": 4}


def parse(body: str, n_images: int = 3) -> dict:
    text = (body or "").strip()
    if not text:
        return {"decision": "none"}

    if re.match(r"^\s*approve", text, re.I):
        return {"decision": "approve"}

    # An image number, however it is written: "2", "#2", "image 2", "second".
    index = None
    m = re.search(r"(?:image|photo|pic|post|#)\s*#?\s*(\d+)", text, re.I) \
        or re.match(r"^\s*redo\s+(\d+)\b", text, re.I)
    if m:
        index = int(m.group(1))
    else:
        for word, num in ORDINALS.items():
            if re.search(rf"\b{word}\b", text, re.I):
                index = num
                break

    # The instruction: drop a leading "redo", its number, and any separator.
    note = re.sub(r"^\s*redo\b\s*", "", text, flags=re.I)
    if index is not None:
        note = re.sub(rf"^\s*(?:image|photo|pic|post|#)?\s*#?\s*{index}\b", "",
                      note, flags=re.I)
    note = re.sub(r"^\s*[-–—:,.]\s*", "", note)
    note = " ".join(note.split())[:300]

    if index is not None and not 1 <= index <= n_images:
        return {"decision": "bad_index", "index": index, "note": note}

    return {"decision": "redo", "index": index, "note": note}


if __name__ == "__main__":
    import json, os, sys
    r = parse(os.environ.get("BODY", ""), int(os.environ.get("N_IMAGES", "3")))
    if len(sys.argv) > 1 and sys.argv[1] == "--github":
        for k, v in r.items():
            print(f"{k}={v if v is not None else ''}")
    else:
        print(json.dumps(r))
