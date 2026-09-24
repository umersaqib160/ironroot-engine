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
    st = json.loads(path.read_text(encoding="utf-8")) if path.exists() \
        else {"done": {}}
    st.setdefault("captions", {})
    return st


def recent_captions(month: str, n: int = 1) -> str:
    """Last month's captions, so the writer does not repeat its own hooks."""
    months = sorted(q for q in (ROOT / "content" / "monthly").glob("*/captions.md")
                    if q.parent.name < month)
    return "\n\n".join(q.read_text(encoding="utf-8")[:6000] for q in months[-n:])


def caption_brief(post: dict) -> dict:
    """
    What the caption writer is allowed to lean on, per post kind.

    A photo carries the scene's own guards. A card carries its printed line,
    because the card IS the claim — and the writer still reads it off the image,
    so a card whose text rendered wrong cannot be captioned as if it were right.
    """
    if post["kind"] == "education_card":
        return {"id": post["id"], "claim": post["headline"],
                "caption_must": "expand on the line printed on the card, in the "
                                "brand voice, without repeating it word for word",
                "caption_never": "claim or imply the pan is non-stick"}
    if post["kind"] == "review_card":
        return {"id": post["id"],
                "claim": f"a verified customer review from {post['name']}",
                "caption_must": "stay with what this customer actually said",
                "caption_never": "invent any detail of the customer, their order "
                                 "or their kitchen, or add a second quote"}
    return post


def captions_doc(month: str, posts: list[dict], written: dict) -> str:
    """
    The month's captions with each post's guards written in beside them.

    The guards stay even when a caption was generated, so Umer reviews what the
    caption was allowed to say next to what it said.
    """
    out = [f"# IronRoot — {month}", ""]
    for post in posts:
        g = caption_brief(post)
        out += [f"## {post['index']}. {post['date']} — `{post['id']}`",
                f"pillar **{post['pillar']}** · {post['kind'].replace('_', ' ')}", ""]
        if g.get("claim"):
            out += [f"- claim: {g['claim']}"]
        if g.get("caption_must"):
            out += [f"- must: {g['caption_must']}"]
        if g.get("caption_never"):
            out += [f"- never: {g['caption_never']}"]
        c = written.get(post["id"])
        if not c:
            out += ["", "_caption not written — ANTHROPIC_API_KEY was not set._", ""]
            continue
        out += [""]
        for net in ("instagram", "facebook", "pinterest", "tiktok"):
            out += [f"**{net.title()}**", "", c.get(net, "_missing_"), ""]
        v = c.get("verification") or {}
        mark = "PASS" if v.get("match") else "FAIL"
        out += [f"- caption/image check: **{mark}**"]
        for prob in v.get("problems") or []:
            out += [f"  - {prob}"]
        for con in c.get("concerns") or []:
            out += [f"  - concern in the image: {con}"]
        out += [""]
    return "\n".join(out) + "\n"


def save_state(path: Path, state: dict) -> None:
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def issue_body(month: str, posts: list[dict], state: dict, written: dict,
               qc_failed: list, repo: str, sha: str, run_url: str) -> str:
    """
    The approval issue: the whole month on one page, with every warning on it.

    A batch of thirteen is too much to check by clicking through a zip, so the
    images are linked inline at the pushed sha and anything the run is unsure
    about is stated next to the post it belongs to, not buried in a log.
    """
    raw = f"https://raw.githubusercontent.com/{repo}/{sha}"
    out = [f"# IronRoot — {month}", "",
           f"{len(posts)} posts. **Nothing is published by this run.**", ""]
    if qc_failed:
        out += [f"## {len(qc_failed)} image(s) failed the QA gate — do not post",
                ""]
        for idx, sid, reasons in qc_failed:
            out += [f"- **{idx}. `{sid}`** — " + "; ".join(reasons)]
        out += [""]
    else:
        out += ["The QA gate passed on every image: no app interface, no "
                "letterbox band. Rim lip, handle count and second-pan checks "
                "ran against the reference photograph.", ""]

    out += ["| # | Date | Pillar | Post | Image | Caption check |",
            "|---|------|--------|------|-------|---------------|"]
    for post in posts:
        shot = state["done"].get(f"{post['index']:02d}_{post['id']}", {}).get("4x5")
        link = f"[view]({raw}/{shot})" if shot else "—"
        c = written.get(post["id"]) or {}
        v = c.get("verification") or {}
        if not c:
            chk = "not written"
        elif v.get("match"):
            chk = "pass"
        else:
            chk = "**FAIL** — " + "; ".join(v.get("problems") or ["see captions.md"])
        out += [f"| {post['index']} | {post['date']} | {post['pillar']} | "
                f"`{post['id']}` | {link} | {chk} |"]

    concerns = [(post["index"], post["id"], x)
                for post in posts
                for x in ((written.get(post["id"]) or {}).get("concerns") or [])]
    if concerns:
        out += ["", "## Flagged while writing the captions", ""]
        out += [f"- **{i}. `{sid}`** — {x}" for i, sid, x in concerns]

    out += ["", "Captions for all four platforms, with the guards each one was "
            f"held to: [`content/monthly/{month}/captions.md`]"
            f"(https://github.com/{repo}/blob/{sha}/content/monthly/{month}/captions.md)",
            ""]
    if run_url:
        out += [f"Full-resolution masters are in the [run artifact]({run_url}) "
                "for 30 days.", ""]
    out += ["---", "",
            "**To approve the month**, comment `approve`.",
            "",
            "**To change something**, comment in plain English — say which post "
            "and what to change (`redo 4 with salmon instead of potatoes`). "
            "Anything that is not `approve` is read as a change request, and the "
            "whole comment is passed through as the instruction.", ""]
    return "\n".join(out)


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
    ap.add_argument("--drop", default="",
                    help="comma-separated post ids to throw out of a month that "
                         "is already built. Each one is replaced in place — same "
                         "date, same pillar — and its image and caption are "
                         "discarded so the slot is rebuilt from scratch.")
    ap.add_argument("--reject", action="store_true",
                    help="with --drop: also add the scene to rejects.yaml so it "
                         "is never scheduled again. Without it the scene stays "
                         "in the pool and only this generation is thrown away.")
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

    dropped = [x.strip() for x in a.drop.split(",") if x.strip()]
    if dropped:
        was = {x["id"]: x["index"] for x in posts}
        for did in dropped:
            posts, fresh = pm.swap(posts, did, a.seed,
                                   {x.strip() for x in a.exclude.split(",")
                                    if x.strip()})
            key = f"{was[did]:02d}_{did}"
            # Only ever delete inside THIS month's folder. state.json records
            # repo-relative paths, and a state file copied from another month
            # would otherwise point the unlink at that month's images — which is
            # exactly what happened the first time this was tested.
            for rel in (state["done"].pop(key, {}) or {}).values():
                f = (ROOT / rel).resolve()
                if f.is_relative_to(outdir.resolve()):
                    f.unlink(missing_ok=True)
                else:
                    print(f"     refusing to delete outside {a.month}: {rel}")
            for ratio in RATIOS:
                (outdir / f"{did}__{ratio}.jpg").unlink(missing_ok=True)
            (outdir / f"{did}__master.png").unlink(missing_ok=True)
            state["captions"].pop(did, None)
            print(f"dropped {did} -> {fresh['id']} "
                  f"({fresh['pillar']}, {fresh['date']})")
            if a.reject:
                pm.add_reject(did, "Umer", f"dropped from {a.month} at review")
                print(f"  {did} added to rejects.yaml — it will not be "
                      f"scheduled again")
        hard, soft = pm.validate(posts)
        for w in soft:
            print("  note:", w)
        if hard:
            for h in hard:
                print("  FAIL:", h, file=sys.stderr)
            return 1
        plan_path.write_text(json.dumps(posts, indent=2) + "\n", encoding="utf-8")
        pm.record(year, month, posts)
        save_state(state_path, state)

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

    # Captions, from the image and never from the prompt — see captions.py.
    # Resumable like everything else: a caption already written is not paid for
    # twice on a re-run.
    written = dict(state["captions"])
    if cap and os.environ.get("ANTHROPIC_API_KEY"):
        brand = (HERE / "brand.md").read_text(encoding="utf-8")
        recent = recent_captions(a.month)
        for post in posts:
            if post["id"] in written:
                continue
            shot = state["done"].get(f"{post['index']:02d}_{post['id']}", {}).get("4x5")
            if not shot:
                continue
            try:
                print(f"\n--- captions for {post['id']} (from the image)", flush=True)
                written[post["id"]] = cap.for_scene(ROOT / shot, caption_brief(post),
                                                    brand, recent)
                v = written[post["id"]].get("verification", {})
                print("    caption/image check: " +
                      ("PASS" if v.get("match")
                       else "FAIL " + str(v.get("problems"))), flush=True)
                state["captions"] = written
                save_state(state_path, state)
            except Exception as e:
                print(f"    caption step failed: {e}", file=sys.stderr, flush=True)
    else:
        print("\nANTHROPIC_API_KEY not set — captions left unwritten.", flush=True)

    (outdir / "captions.md").write_text(captions_doc(a.month, posts, written),
                                        encoding="utf-8")

    (outdir / "bundle.json").write_text(
        json.dumps({"month": a.month, "posts": posts, "captions": written,
                    "status": {k: "pending" for k in state["done"]}},
                   indent=2) + "\n", encoding="utf-8")

    if a.repo:
        Path(a.out_issue).write_text(
            issue_body(a.month, posts, state, written, qc_failed,
                       a.repo, a.sha, a.run_url), encoding="utf-8")

    if os.environ.get("GITHUB_ENV"):
        with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as fh:
            fh.write(f"BUNDLE_DIR={outdir.relative_to(ROOT).as_posix()}\n")
    if failed:
        print("Re-run to retry only the failures — completed posts are skipped.")
    return 1 if failed and not state["done"] else 0


if __name__ == "__main__":
    sys.exit(main())
