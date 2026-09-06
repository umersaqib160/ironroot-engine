"""
Regenerate ONE image from a week's bundle, with Umer's change applied.

"Redo 2 - use salmon instead of potatoes" must give back the SAME shot with the
food swapped — same scene, same mood, same framing. Re-picking would hand him a
different photograph, which is not what redo means.

So the scene and mood come from bundle.json, and his note is appended as an extra
sentence. That is a scene detail, never a description of the pan: the reference
photograph still specifies the product, and the corrective constraints still ride
at the end of the prompt.
"""
from __future__ import annotations
import argparse, json, shutil, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import generate as gen   # noqa: E402
import reframe as rf     # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", required=True)
    ap.add_argument("--index", type=int, required=True)
    ap.add_argument("--note", default="",
                    help="what to change. Empty = re-roll the same scene, which "
                         "is what a bare 'redo' means.")
    ap.add_argument("--size", default="2K")
    a = ap.parse_args()

    outdir = ROOT / "content" / "weekly" / a.week
    bundle_path = outdir / "bundle.json"
    if not bundle_path.exists():
        sys.exit(f"No bundle.json for week {a.week} — nothing to redo.")

    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    post = next((p for p in bundle["posts"] if p["index"] == a.index), None)
    if post is None:
        sys.exit(f"Week {a.week} has no image {a.index} "
                 f"(it has {len(bundle['posts'])}).")

    note = (a.note.strip().rstrip(".") + ".") if a.note.strip() else ""
    print(f"redoing image {a.index} of week {a.week}: {post['id']}")
    print(f"  change requested: {note or '(none — plain re-roll)'}")

    prompt = gen.build_prompt("Instagram", post["text"], post["mood"], extra=note)
    print(f"\nPROMPT: {prompt}\n", flush=True)

    # Keep the superseded version rather than overwriting it — if the redo comes
    # back worse, the previous one must still exist.
    revs = sorted(outdir.glob(f"{post['id']}__master.v*.png"))
    version = len(revs) + 1
    master = outdir / post["master"]
    if master.exists():
        shutil.move(str(master), str(outdir / f"{post['id']}__master.v{version}.png"))

    gen.generate(prompt, master, image_size=a.size, ratio="9:16")
    files = rf.reframe(master, outdir, post["id"])
    for k, v in files.items():
        print(f"  {k:5s} {v.name}")

    post.setdefault("redos", []).append({"note": note, "version": version + 1})
    bundle_path.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")

    lines = [f"Redone image **{a.index}**" +
             (f" — *{note}*" if note else " — re-rolled, same scene"), "",
             f"Scene and mood unchanged: *{post['text']}* — {post['mood']}", ""]
    for name in ("4x5", "2x3", "9x16"):
        p = files.get(name)
        if p:
            lines.append(f"- `{name}` — `{p.relative_to(ROOT).as_posix()}`")
    lines += ["", "Reply `approve` if this one works, or `redo "
              f"{a.index} - ...` again.",
              "", f"_The previous version is kept as "
              f"`{post['id']}__master.v{version}.png`._"]
    Path("redo_comment.md").write_text("\n".join(lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
