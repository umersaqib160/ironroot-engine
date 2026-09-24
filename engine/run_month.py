"""
Build a whole month: calendar, images, cards, captions, approval bundle.

Resumable by design. Thirteen posts is too much work to throw away because the
API failed on number nine, so every post is written to state.json the moment it
completes and a re-run skips whatever is already done.

Reuse is first class. An image already made for the same scene can fill a slot
instead of being generated again — that is how October is built almost entirely
from the nine images the weekly runs already produced, and it is also what makes
an approved redo reusable later.

Publishes nothing.
"""
from __future__ import annotations
import argparse, json, os, shutil, sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import generate as gen        # noqa: E402
import reframe as rf          # noqa: E402
import plan_month as pm       # noqa: E402
import render_card as rc      # noqa: E402
import qc_image              # noqa: E402
import yaml                   # noqa: E402

try:
    import captions as cap
except Exception:
    cap = None

ROOT = HERE.parent
HALT = HERE / "HALT"
RATIOS = ("4x5", "2x3", "9x16")


def find_reusable(scene_id: str, exclude: Path) -> Path | None:
    """
    An existing image for this scene, if there is one.

    Masters are gitignored — deliberately, they are 2-3 MB each — so on a fresh
    clone or a CI runner they do not exist. What IS committed is the 9:16 export,
    and that holds the full frame: 2:3 and 4:5 are centre crops of it, so
    reframing from the 9:16 loses no content at all.

    Masters first when one happens to be on disk, then the 9:16.
    """
    pats = [f"content/*/*/{scene_id}__master.png",
            f"content/*/*/{scene_id}__9x16.jpg"]
    for pat in pats:
        hits = [h for h in sorted(ROOT.glob(pat)) if exclude not in h.parents]
        if hits:
            return hits[-1]
    return None


def load_state(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() \
        else {"done": {}}


def save_state(path: Path, state: dict) -> None:
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", required=True, help="YYYY-MM, the month posted IN")
    ap.add_argument("--size", default="2K")
    ap.add_argument("--reuse", action="store_true",
                    help="fill a slot from an existing master when one exists")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--prefer-existing", action="store_true",
                    help="bridge batches: build the calendar from scenes that "
                         "already have an image")
    ap.add_argument("--exclude", default="",
                    help="comma-separated scene ids never to reuse — the ones "
                         "Umer rejected on review")
    ap.add_argument("--repo", default="")
    ap.add_argument("--sha", default="main")
    ap.add_argument("--run-url", default="")
    ap.add_argument("--out-issue", default="issue_body.md")
    a = ap.parse_args()

    if HALT.exists():
        print("engine/HALT present — stopped before spending anything.")
        return 78

    year, month = (int(x) for x in a.month.split("-"))
    outdir = ROOT / "content" / "monthly" / a.month
    outdir.mkdir(parents=True, exist_ok=True)
    state_path = outdir / "state.json"
    state = load_state(state_path)

    plan_path = outdir / "calendar.json"
    if plan_path.exists():
        posts = json.loads(plan_path.read_text(encoding="utf-8"))
        print(f"resuming — calendar already built ({len(posts)} posts)")
    else:
        posts = pm.build(year, month, a.seed, a.prefer_existing,
                         {x.strip() for x in a.exclude.split(",") if x.strip()})
        hard, soft = pm.validate(posts)
        for w in soft:
            print("  note:", w)
        if hard:
            for h in hard:
                print("  FAIL:", h, file=sys.stderr)
            return 1
        plan_path.write_text(json.dumps(posts, indent=2) + "\n", encoding="utf-8")
        pm.record(year, month, posts)
        print(f"calendar built: {len(posts)} posts")

    cards = yaml.safe_load((HERE / "cards.yaml").read_text(encoding="utf-8"))
    photos = [ROOT / p for p in cards["social_proof"]["photo_pool"]]

    made, reused, failed = 0, 0, 0
    qc_failed: list = []
    for post in posts:
        key = f"{post['index']:02d}_{post['id']}"
        if key in state["done"]:
            continue
        print(f"\n[{post['index']:2d}/{len(posts)}] {post['date']}  {post['id']}",
              flush=True)
        try:
            if post["kind"] == "generated":
                master = outdir / f"{post['id']}__master.png"
                rejected = (pm.load_rejects() |
                            {x.strip() for x in a.exclude.split(",") if x.strip()})
                src = (find_reusable(post["id"], outdir)
                       if a.reuse and post["id"] not in rejected else None)
                if src and not master.exists():
                    if src.suffix.lower() == ".png":
                        shutil.copy2(src, master)
                    else:
                        from PIL import Image
                        Image.open(src).convert("RGB").save(master, "PNG")
                    print(f"     reused {src.relative_to(ROOT)}", flush=True)
                    reused += 1
                elif not master.exists():
                    extra = f"There is {post['dish']} in the pan." if post.get("dish") else ""
                    prompt = gen.build_prompt("Instagram", post["text"],
                                              post["mood"], extra=extra)
                    print(f"     {prompt}", flush=True)
                    gen.generate(prompt, master, image_size=a.size, ratio="9:16")
                    made += 1
                files = rf.reframe(master, outdir, post["id"])
                # Gate every photo. p4_meal_prep reached the October calendar
                # carrying a whole rendered Instagram interface because nothing
                # looked at it between generation and scheduling.
                verdict = qc_image.check(files["4x5"])
                post["qc"] = verdict
                if not verdict["pass"]:
                    print("     QC FAILED:", flush=True)
                    for f_ in verdict["failures"]:
                        print(f"       - {f_}", flush=True)
                    qc_failed.append((post["index"], post["id"], verdict["failures"]))
                else:
                    print("     QC pass", flush=True)
            elif post["kind"] == "education_card":
                photo = photos[post["index"] % len(photos)]
                files = rc.education_card(photo, post["headline"],
                                          post.get("sub", ""), outdir, post["id"])
            else:
                photo = photos[(post["index"] + 1) % len(photos)]
                files = rc.review_card(photo, post["quote"], post["name"],
                                       outdir, post["id"])
            state["done"][key] = {name: str(p.relative_to(ROOT))
                                  for name, p in files.items()}
            save_state(state_path, state)
            print("     " + "  ".join(f"{n}" for n in files), flush=True)
        except SystemExit as e:
            failed += 1
            print(f"     FAILED: {e}", file=sys.stderr, flush=True)
            save_state(state_path, state)
        except Exception as e:
            failed += 1
            print(f"     FAILED: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
            save_state(state_path, state)

    print(f"\n{made} generated, {reused} reused, {failed} failed, "
          f"{len(state['done'])}/{len(posts)} complete")
    if qc_failed:
        print(f"\n{len(qc_failed)} image(s) FAILED QC and must not be posted:")
        for idx, sid, reasons in qc_failed:
            print(f"  [{idx}] {sid}")
            for x in reasons:
                print(f"      - {x}")
        print("Exclude them and re-run, or redo those slots.")

    (outdir / "bundle.json").write_text(
        json.dumps({"month": a.month, "posts": posts,
                    "status": {k: "pending" for k in state["done"]}},
                   indent=2) + "\n", encoding="utf-8")

    if os.environ.get("GITHUB_ENV"):
        with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as fh:
            fh.write(f"BUNDLE_DIR={outdir.relative_to(ROOT).as_posix()}\n")
    if failed:
        print("Re-run to retry only the failures — completed posts are skipped.")
    return 1 if failed and not state["done"] else 0


if __name__ == "__main__":
    sys.exit(main())
