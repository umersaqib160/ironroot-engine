"""
Pick this week's scenes, enforcing variety.

The prompt skeleton is fixed and proven; this chooses only what goes in the
scene slot. Rules, in order:

  1. Nothing used in the last 3 weeks (the variety rule in brand.md).
  2. Alternate subject — a week is never all-people or all-pan.
  3. Prefer the least recently used, then randomise among ties, so the library
     rotates evenly instead of favouring whatever sits at the top of the file.

History lives in engine/scene_history.json — small, versioned, and readable, so
the record of what ran survives even though the generated media does not.
"""
from __future__ import annotations
import json, random, sys
from pathlib import Path
import yaml

HERE = Path(__file__).parent
LIBRARY = HERE / "scenes.yaml"
HISTORY = HERE / "scene_history.json"
COOLDOWN_WEEKS = 3


def load():
    lib = yaml.safe_load(LIBRARY.read_text(encoding="utf-8"))
    hist = json.loads(HISTORY.read_text(encoding="utf-8")) if HISTORY.exists() else {"weeks": []}
    return lib, hist


def recent_ids(hist: dict, weeks: int = COOLDOWN_WEEKS) -> set[str]:
    out = set()
    for wk in hist["weeks"][-weeks:]:
        out.update(wk["scene_ids"])
    return out


def last_used(hist: dict) -> dict[str, int]:
    """scene id -> index of the most recent week that used it."""
    seen: dict[str, int] = {}
    for i, wk in enumerate(hist["weeks"]):
        for sid in wk["scene_ids"]:
            seen[sid] = i
    return seen


def pick(n: int = 2, seed: int | None = None) -> list[dict]:
    lib, hist = load()
    rng = random.Random(seed)
    blocked = recent_ids(hist)
    seen = last_used(hist)
    moods = lib["moods"]

    pool = [s for s in lib["scenes"] if s["id"] not in blocked]
    if len(pool) < n:
        # Never repeat inside a week just to satisfy the cooldown; relax it and
        # say so rather than failing the Monday run.
        print(f"WARNING: only {len(pool)} scenes outside the {COOLDOWN_WEEKS}-week "
              f"cooldown; relaxing it.", file=sys.stderr)
        pool = lib["scenes"]

    chosen: list[dict] = []
    want = ["person", "pan_only"]
    for i in range(n):
        subject = want[i % len(want)]
        cands = [s for s in pool if s["subject"] == subject and s not in chosen] or \
                [s for s in pool if s not in chosen]
        oldest = min(seen.get(s["id"], -1) for s in cands)
        cands = [s for s in cands if seen.get(s["id"], -1) == oldest]
        s = dict(rng.choice(cands))
        s["mood"] = rng.choice(moods)
        chosen.append(s)
    return chosen


def record(week: str, scenes: list[dict]) -> None:
    _, hist = load()
    hist["weeks"] = [w for w in hist["weeks"] if w["week"] != week]
    hist["weeks"].append({"week": week, "scene_ids": [s["id"] for s in scenes]})
    HISTORY.write_text(json.dumps(hist, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=2)
    ap.add_argument("--week", default="")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--record", action="store_true")
    a = ap.parse_args()

    picks = pick(a.count, a.seed)
    for s in picks:
        print(f"{s['id']:24s} pillar {s['pillar']}  {s['subject']:9s}")
        print(f"  scene: {s['text']}")
        print(f"  mood : {s['mood']}")
    if a.record and a.week:
        record(a.week, picks)
        print(f"\nrecorded against week {a.week}")
