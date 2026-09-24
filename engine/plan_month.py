"""
Build a month's calendar: 13 dated posts, ordered, with nothing repeating from
one day to the next.

Mix comes from the strategy, not from whatever the scene library happens to hold
(automation/monthly_plan.md section 2):

    5 education  = 2 generated demos + 3 code-built claim cards
    4 product    = generated
    2 proof      = code-built review cards
    2 lifestyle  = generated

Adjacency rules — consecutive posts never share a pillar, a subject, a mood tone
or a dish. Benefit and education demonstrations are spread so a month does not
read as an advert block.
"""
from __future__ import annotations
import calendar, datetime as dt, json, os, random, re
from pathlib import Path
import yaml

HERE = Path(__file__).parent
HISTORY = Path(os.environ.get("IRONROOT_MONTH_HISTORY", HERE / "month_history.json"))
COOLDOWN_DAYS = 60

# Strategy ratios. The number of posts comes from how many Mon/Wed/Fri the month
# actually has — 12 in a short February, 14 in a long month — so the mix is
# allocated proportionally rather than hardcoded to 13. A February that produced
# 13 posts for 12 slots silently dropped one.
RATIOS = {"education": 0.40, "product": 0.30, "proof": 0.15, "lifestyle": 0.15}
EDUCATION_CARD_SHARE = 0.6      # of the education slots, this many are claim cards
PILLAR_OF = {"education": 1, "product": 2, "proof": 3, "lifestyle": 4}


def allocate(n: int) -> list[tuple[str, int, str]]:
    """Largest-remainder split of n posts across the pillars."""
    raw = {k: n * v for k, v in RATIOS.items()}
    base = {k: int(v) for k, v in raw.items()}
    for k, _ in sorted(raw.items(), key=lambda kv: kv[1] - int(kv[1]), reverse=True):
        if sum(base.values()) >= n:
            break
        base[k] += 1
    ed_cards = round(base["education"] * EDUCATION_CARD_SHARE)
    return [("education", base["education"] - ed_cards, "scene"),
            ("education", ed_cards, "card"),
            ("product", base["product"], "scene"),
            ("proof", base["proof"], "review"),
            ("lifestyle", base["lifestyle"], "scene")]

# Scenes that must NOT be given a dish.
#   NO_FOOD_SCENE — food in the pan makes no sense (it is being washed or stored)
#   NAMES_ITS_OWN — the scene already says what is cooking, so adding a dish
#                   contradicts it ("pressing a steak into the pan" + "eggs")
NO_FOOD_SCENE = re.compile(r"empty|clean|hanging|drying|shelf|flat lay|wall"
                           r"|dishwasher|scrub|rins", re.I)
NAMES_ITS_OWN = re.compile(r"\bsteak|\begg|\bsalmon|\bfish|\bchicken"
                           r"|\bvegetable|\bpotato|one-pan", re.I)


def takes_dish(text: str) -> bool:
    return not (NO_FOOD_SCENE.search(text) or NAMES_ITS_OWN.search(text))


def load():
    lib = yaml.safe_load((HERE / "scenes.yaml").read_text(encoding="utf-8"))
    cards = yaml.safe_load((HERE / "cards.yaml").read_text(encoding="utf-8"))
    revs = yaml.safe_load((HERE / "reviews.yaml").read_text(encoding="utf-8"))
    hist = json.loads(HISTORY.read_text(encoding="utf-8")) if HISTORY.exists() \
        else {"months": []}
    return lib, cards, revs, hist


def post_dates(year: int, month: int, n: int) -> list[dt.date]:
    """Monday, Wednesday, Friday through the month, first n of them."""
    days = calendar.monthrange(year, month)[1]
    out = [dt.date(year, month, d) for d in range(1, days + 1)
           if dt.date(year, month, d).weekday() in (0, 2, 4)]
    return out[:n]


def recently_used(hist: dict, upto: dt.date) -> set[str]:
    cut = upto - dt.timedelta(days=COOLDOWN_DAYS)
    used = set()
    for m in hist["months"]:
        when = dt.date.fromisoformat(m["month"] + "-01")
        if when >= cut:
            used.update(m["ids"])
    return used


def order_pillars(counts: dict[str, int], rng: random.Random) -> list[str]:
    """Lay pillars out so no two neighbours match — most frequent first."""
    remaining = dict(counts)
    seq: list[str] = []
    while sum(remaining.values()):
        options = [p for p, c in remaining.items()
                   if c > 0 and (not seq or p != seq[-1])]
        if not options:                       # only the previous pillar is left
            options = [p for p, c in remaining.items() if c > 0]
        p = max(options, key=lambda x: (remaining[x], rng.random()))
        seq.append(p)
        remaining[p] -= 1
    return seq


def build(year: int, month: int, seed: int | None = None,
          prefer_existing: bool = False,
          exclude: set[str] | None = None) -> list[dict]:
    """
    Choose the 13 items FIRST, then order them, then dress them.

    The earlier version decided card-vs-scene inside the ordering loop, which
    quietly under-allocated cards — a month asking for 3 education cards got 1.
    Picking the exact set up front makes the mix impossible to get wrong.
    """
    lib, cards, revs, hist = load()
    rng = random.Random(seed)
    first = dt.date(year, month, 1)
    blocked = recently_used(hist, first)

    # Which scenes already have a rendered master somewhere in the repo.
    # Masters are gitignored; the committed 9:16 export is what actually
    # survives, so count either as "we already have this scene".
    have = {p.name.split("__")[0]
            for pat in ("*/*/*__master.png", "*/*/*__9x16.jpg")
            for p in (HERE.parent / "content").glob(pat)}

    def freshest(pool):
        pool = list(pool)
        rng.shuffle(pool)
        if prefer_existing:
            # Bridge batches invert the rule: fill slots from images that already
            # exist rather than avoiding recently-used scenes. The September runs
            # produced nine images that were never posted, and the cooldown would
            # otherwise route around exactly the ones we want to spend.
            pool.sort(key=lambda x: x["id"] not in have)
        else:
            pool.sort(key=lambda x: x["id"] in blocked)   # not-recently-used first
        return pool

    # Scenes Umer rejected at review are dropped before selection, not merely
    # barred from reuse — otherwise the calendar picks one and pays to
    # regenerate the thing he just turned down.
    dropped = exclude or set()
    scenes = {k: freshest(s for s in lib["scenes"]
                          if s["pillar"] == PILLAR_OF[k] and s["id"] not in dropped)
              for k in ("education", "product", "lifestyle")}
    ed_cards = freshest(cards["education_cards"])
    reviews = freshest(revs["reviews"])

    # --- the exact set, per the strategy mix ---------------------------------
    n_posts = len(post_dates(year, month, 99))
    items: list[dict] = []
    for pillar, n, kind in allocate(n_posts):
        for _ in range(n):
            if kind == "card":
                it = ed_cards.pop(0) if ed_cards else rng.choice(cards["education_cards"])
                items.append({"kind": "education_card", "id": it["id"],
                              "headline": it["headline"], "sub": it.get("sub", ""),
                              "subject": "card", "mood_tone": "card",
                              "dish": None, "pillar": pillar})
            elif kind == "review":
                it = reviews.pop(0) if reviews else rng.choice(revs["reviews"])
                items.append({"kind": "review_card", "id": it["id"],
                              "name": it["name"], "quote": it["english"].strip(),
                              "subject": "card", "mood_tone": "card",
                              "dish": None, "pillar": pillar})
            else:
                pool = scenes[pillar]
                it = pool.pop(0) if pool else rng.choice(
                    [x for x in lib["scenes"] if x["pillar"] == PILLAR_OF[pillar]])
                items.append({"kind": "generated", "id": it["id"],
                              "text": it["text"], "subject": it["subject"],
                              "claim": it.get("claim"), "pillar": pillar,
                              "mood_tone": None, "dish": None})

    # --- order so neighbours never share a pillar ---------------------------
    counts: dict[str, int] = {}
    for it in items:
        counts[it["pillar"]] = counts.get(it["pillar"], 0) + 1
    by_pillar = {p: [i for i in items if i["pillar"] == p] for p in counts}
    ordered = [by_pillar[p].pop(0) for p in order_pillars(counts, rng)]

    # Ordering by pillar alone left person/person and pan_only/pan_only pairs.
    # Restricting swaps to the same pillar was too tight to always fix them, so
    # this scores the whole sequence and takes any swap that lowers the score.
    # Pillar clashes are weighted heavily, subject clashes lightly, so a subject
    # fix is never bought at the cost of a pillar clash.
    def score(seq):
        bad = 0
        for a, b in zip(seq, seq[1:]):
            if a["pillar"] == b["pillar"]:
                bad += 10
            if (a["subject"] == b["subject"] != "card"):
                bad += 1
        return bad

    best = score(ordered)
    for _ in range(200):
        if best == 0:
            break
        improved = False
        for i in range(len(ordered)):
            for j in range(i + 1, len(ordered)):
                ordered[i], ordered[j] = ordered[j], ordered[i]
                new_score = score(ordered)
                if new_score < best:
                    best, improved = new_score, True
                    break
                ordered[i], ordered[j] = ordered[j], ordered[i]
            if improved:
                break
        if not improved:
            break

    # --- dress: mood and dish, neither repeating day to day -----------------
    # "nothing, the pan is empty" is not a dish to rotate onto a cooking scene —
    # scenes that take no food already get None, so it is excluded here.
    dish_pool = [d for d in lib["dishes"] if not d.startswith("nothing")]
    unused_dishes = list(dish_pool)
    rng.shuffle(unused_dishes)
    evening = [m for m in lib["moods"] if m["tone"] == "evening"]
    bright = [m for m in lib["moods"] if m["tone"] in ("light", "warm")]

    dates = post_dates(year, month, len(ordered))
    prev: dict = {}
    for i, (date, post) in enumerate(zip(dates, ordered), 1):
        if post["kind"] == "generated":
            pool = evening if (evening and prev.get("mood_tone") != "evening"
                               and rng.random() < 0.13) else bright
            mood = rng.choice([m for m in pool
                               if m["tone"] != prev.get("mood_tone")] or pool)
            post["mood"], post["mood_tone"] = mood["text"], mood["tone"]

            if takes_dish(post["text"]):
                if not unused_dishes:                 # month longer than the list
                    unused_dishes = list(dish_pool)
                    rng.shuffle(unused_dishes)
                opts = [d for d in unused_dishes if d != prev.get("dish")] \
                    or unused_dishes
                post["dish"] = opts[0]
                unused_dishes.remove(post["dish"])

        post.update({"index": i, "date": date.isoformat()})
        prev = post
    return ordered


def record(year: int, month: int, posts: list[dict]) -> None:
    _, _, _, hist = load()
    key = f"{year:04d}-{month:02d}"
    hist["months"] = [m for m in hist["months"] if m["month"] != key]
    hist["months"].append({"month": key, "ids": [p["id"] for p in posts]})
    HISTORY.write_text(json.dumps(hist, indent=2) + "\n", encoding="utf-8")


def validate(posts: list[dict]) -> tuple[list[str], list[str]]:
    """
    Returns (hard failures, soft warnings).

    Hard   — a wrong pillar mix, two of the same pillar back to back, a post with
             no date. These make the month wrong and must never ship.
    Soft   — one repeated subject or mood tone. In a short month the item set can
             make perfect alternation impossible, and forcing it would mean
             breaking pillar adjacency, which is worse. Reported, not fatal.
    """
    problems, warnings = [], []
    for a, b in zip(posts, posts[1:]):
        if a["pillar"] == b["pillar"]:
            problems.append(f"{b['date']}: same pillar as the day before ({a['pillar']})")
        for field, label, hard in (("subject", "subject", False),
                                   ("mood_tone", "mood tone", False),
                                   ("dish", "dish", True)):
            va, vb = a.get(field), b.get(field)
            if va and vb and va == vb and va != "card":
                msg = f"{b['date']}: same {label} as the day before ({va})"
                (problems if hard else warnings).append(msg)
    want: dict[str, int] = {}
    for pillar, n, _ in allocate(len(posts)):
        want[pillar] = want.get(pillar, 0) + n
    got: dict[str, int] = {}
    for p in posts:
        got[p["pillar"]] = got.get(p["pillar"], 0) + 1
    if got != want:
        problems.append(f"pillar mix is {got}, wanted {want}")
    if any("date" not in p for p in posts):
        problems.append("some posts have no date — more posts than Mon/Wed/Fri slots")
    for p in posts:
        if p["kind"] == "generated" and p.get("dish") and not takes_dish(p["text"]):
            problems.append(f"{p['date']}: {p['id']} was given a dish it should not have")
    return problems, warnings


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", required=True, help="YYYY-MM")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--record", action="store_true")
    ap.add_argument("--exclude", default="")
    ap.add_argument("--prefer-existing", action="store_true",
                    help="bridge batches: favour scenes that already have an "
                         "image over the usual not-recently-used rule")
    a = ap.parse_args()
    y, m = (int(x) for x in a.month.split("-"))
    posts = build(y, m, a.seed, a.prefer_existing,
                  {x.strip() for x in a.exclude.split(",") if x.strip()})
    for p in posts:
        extra = p.get("text") or p.get("headline") or f"\"{p['quote'][:44]}...\" — {p['name']}"
        dish = f" | {p['dish']}" if p.get("dish") else ""
        print(f"{p['date']}  {p['index']:2d}  {p['pillar']:9s} {p['kind']:15s} "
              f"{p['id']:22s} {extra[:52]}{dish}")
    bad, warn = validate(posts)
    print()
    for w in warn:
        print("  note:", w)
    if bad:
        print("VALIDATION FAILED:")
        for b in bad:
            print("  -", b)
        raise SystemExit(1)
    print("validation: pillar mix, pillar adjacency, dishes and dates all hold"
          + (f" ({len(warn)} soft note{'s' if len(warn) != 1 else ''})" if warn else ""))
    if a.record:
        record(y, m, posts)
