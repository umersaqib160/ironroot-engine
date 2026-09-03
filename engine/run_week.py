"""
The Monday run: pick the week's scenes, generate, reframe, and assemble the
approval bundle.

Publishes NOTHING. This is stage T1 of the test plan — it produces the images and
the Issue body, and stops. Nothing reaches a public account without Umer's
explicit approval, and there is no auto-approve on a timer.
"""
from __future__ import annotations
import argparse, datetime as dt, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import generate as gen          # noqa: E402
import reframe as rf            # noqa: E402
import plan_week as pw          # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
HALT = ROOT / "engine" / "HALT"


def monday(today: dt.date | None = None) -> str:
    d = today or dt.date.today()
    return (d - dt.timedelta(days=d.weekday())).isoformat()


def captions_stub(week: str, picks: list[dict]) -> str:
    """
    Caption skeleton carrying each scene's claim guards.

    Captions are not written here yet — that needs the Claude API key (Phase 4b).
    Until then the guards travel with the file so whoever writes them, human or
    model, cannot lose the constraint.
    """
    out = [f"# IronRoot — week of {week}", ""]
    for i, s in enumerate(picks, 1):
        out += [f"## Post {i} — `{s['id']}` (pillar {s['pillar']}, {s['subject']})",
                "", f"**Scene:** {s['text']}", f"**Mood:** {s['mood']}", ""]
        if s.get("claim"):
            out += [f"**Claim:** {s['claim']}", ""]
            if s.get("claim_source"):
                out += [f"> Source: {s['claim_source'].strip()}", ""]
        if s.get("caption_must"):
            out += [f"**Caption MUST:** {s['caption_must'].strip()}", ""]
        if s.get("caption_never"):
            out += [f"**Caption NEVER:** {s['caption_never'].strip()}", ""]
        if s.get("qc_watch"):
            out += [f"**QC watch:** {s['qc_watch'].strip()}", ""]
        out += ["**INSTAGRAM**", "_to write_", "", "**FACEBOOK**", "_to write_", "",
                "**PINTEREST**", "_to write_", "", "**TIKTOK**", "_to write_", "",
                "---", ""]
    out += ["## QC sign-off (per automation/QC_process.md)", "",
            "```", "_pending — check every asset at FULL resolution_", "```", ""]
    return "\n".join(out)


def issue_body(week: str, picks: list[dict], files: dict, repo: str, sha: str,
               run_url: str) -> str:
    b = [f"Week of **{week}** — {len(picks)} images, nothing published.", "",
         "Reply **`approve`** to accept, or **`redo 1 — darker`** to send one back.",
         "", "---", ""]
    for i, s in enumerate(picks, 1):
        b += [f"### {i}. `{s['id']}` — pillar {s['pillar']}, {s['subject']}", "",
              f"*{s['text']}* — {s['mood']}", ""]
        if s.get("claim"):
            b += [f"**Claim:** {s['claim']}", ""]
        for name in ("4x5", "2x3", "9x16"):
            p = files[s["id"]].get(name)
            if p:
                rel = p.relative_to(ROOT).as_posix()
                b.append(f"[{name}](https://github.com/{repo}/blob/{sha}/{rel}) ")
        b += ["", "---", ""]
    b += ["**Check before approving** — handle count, splayed fork, rim with no "
          "lip, depth, satin finish, no mangled text on background props.", "",
          f"[Full-resolution masters (artifact)]({run_url})", "",
          "_Generated automatically. Nothing publishes without an explicit approval._"]
    return "\n".join(b)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=2)
    ap.add_argument("--week", default="")
    ap.add_argument("--size", default="2K")
    ap.add_argument("--repo", default="")
    ap.add_argument("--sha", default="main")
    ap.add_argument("--run-url", default="")
    ap.add_argument("--out-issue", default="issue_body.md")
    a = ap.parse_args()

    if HALT.exists():
        print("HALT file present — the engine is stopped. Delete engine/HALT to resume.")
        return 78  # neutral

    week = a.week or monday()
    outdir = ROOT / "content" / "weekly" / week
    outdir.mkdir(parents=True, exist_ok=True)

    picks = pw.pick(a.count)
    print(f"week {week}: " + ", ".join(p["id"] for p in picks), flush=True)

    files: dict[str, dict] = {}
    for s in picks:
        prompt = gen.build_prompt("Instagram", s["text"], s["mood"])
        print(f"\n=== {s['id']} ===\n{prompt}", flush=True)
        master = outdir / f"{s['id']}__master.png"
        gen.generate(prompt, master, image_size=a.size, ratio="9:16")
        files[s["id"]] = rf.reframe(master, outdir, s["id"])
        for k, v in files[s["id"]].items():
            print(f"  {k:5s} {v.name}", flush=True)

    (outdir / "captions.md").write_text(captions_stub(week, picks), encoding="utf-8")
    pw.record(week, picks)

    Path(a.out_issue).write_text(
        issue_body(week, picks, files, a.repo, a.sha, a.run_url), encoding="utf-8")
    print(f"\nbundle ready in {outdir.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
