"""
Mechanical checks on a caption, run twice: when it is written, and again at the
moment it is posted.

Only rules that can be checked without judgement live here. Each exists because
a caption broke it:

  a web address that is not the store  — "Shop: ironrootpans.com" (24 Sep). The
      address was missing from brand.md, so the model invented one. A wrong
      domain in a public post sends buyers to somebody else's site.

  a non-stick claim in other words     — "Eggs release, fish lifts, nothing
      sticks." (24 Sep). The brand never claims non-stick; saying it without the
      word is the same claim.

A model judging "does this caption match the picture" is useful but noisy — it
failed ten of thirteen October captions, mostly for stating true product facts,
and a check that fails everything gets ignored. These rules do not guess. If one
fires, the caption is wrong.
"""
from __future__ import annotations
import re

STORE = "ironrootstore.com"

# Anything that looks like a web address. Deliberately broad: a false alarm here
# costs a retry, a miss costs a public post pointing at the wrong site.
_DOMAIN = re.compile(r"\b(?:https?://)?(?:www\.)?([a-z0-9-]+(?:\.[a-z0-9-]+)*"
                     r"\.(?:com|co|net|org|shop|store|nl|be|us|io|app|uk))\b", re.I)

# Non-stick, said without the word. Comparisons ("what non-stick can't") are
# fine and common, so the word itself is not banned — only claims about OUR pan.
_STICK = re.compile(
    r"\b(nothing|never|won'?t|doesn'?t|does not|will not|no more)\s+(ever\s+)?stick"
    r"|\bstick[- ]?free\b"
    r"|\bno sticking\b"
    r"|\bsticking is a thing of the past\b"
    r"|\b(slides?|slid(e|ing)) (right |straight )?(off|out)\b"
    r"|\b(it|this pan|our pan|ironroot)('s| is) non[- ]?stick\b"
    r"|\bnaturally non[- ]?stick\b",
    re.I)


def problems(text: str) -> list[str]:
    """Every rule the caption breaks. Empty list means clean."""
    out = []
    for m in _DOMAIN.finditer(text or ""):
        host = m.group(1).lower()
        if host != STORE and not host.endswith("." + STORE):
            out.append(f"web address that is not the store: {m.group(0)!r} "
                       f"(the only address is {STORE})")
    for m in _STICK.finditer(text or ""):
        out.append(f"non-stick claim: {m.group(0)!r}")
    return out


def check_all(captions: dict) -> dict[str, list[str]]:
    """Problems per network, only for networks that have any."""
    return {k: p for k in ("instagram", "facebook", "pinterest", "tiktok")
            if (p := problems(captions.get(k, "")))}
