"""
Publish the post due today to Instagram and Facebook.

Three rules this file exists to enforce, in order of how badly they would hurt:

  1. NOTHING POSTS WITHOUT APPROVAL. The month must carry an APPROVED marker,
     written into the repo when Umer comments `approve` on the issue. A label on
     an issue is not enough — labels can be added by anyone with write access and
     leave no diff. The marker is a committed file.

  2. NOTHING POSTS TWICE. Every publish is written to posted.json before the run
     ends, and a date already in that ledger is skipped. A re-run, a retry after
     a network failure, a double-fired schedule: all no-ops.

  3. A FAILURE ON ONE NETWORK DOES NOT BLOCK THE OTHER. Facebook and Instagram
     are attempted independently and the ledger records each separately, so a
     retry posts only what is actually missing.

Instagram publishing is two calls, not one: create a media container from a
PUBLIC image URL, then publish that container. The image is served from the
repo's own raw URL, which works because the repo is public — that is a load
bearing fact, and if the repo is ever made private, Instagram will stop being
able to fetch the images and this will fail.
"""
from __future__ import annotations
import argparse, datetime as dt, json, os, sys, time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
GRAPH = os.environ.get("META_GRAPH_VERSION", "v26.0")
API = f"https://graph.facebook.com/{GRAPH}"


def due(date: str) -> tuple[Path, dict, dict] | None:
    """The month folder, the post due on `date`, and the captions for it."""
    folder = ROOT / "content" / "monthly" / date[:7]
    bundle = folder / "bundle.json"
    if not bundle.exists():
        return None
    data = json.loads(bundle.read_text(encoding="utf-8"))
    post = next((p for p in data["posts"] if p.get("date") == date), None)
    if not post:
        return None
    return folder, post, (data.get("captions") or {}).get(post["id"], {})


def ledger(folder: Path) -> dict:
    f = folder / "posted.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def save_ledger(folder: Path, data: dict) -> None:
    (folder / "posted.json").write_text(json.dumps(data, indent=2) + "\n",
                                        encoding="utf-8")


def _post(url: str, payload: dict) -> dict:
    r = requests.post(url, data=payload, timeout=120)
    if r.status_code != 200:
        raise RuntimeError(f"{r.status_code} {r.text[:400]}")
    return r.json()


def to_facebook(image_url: str, caption: str, page_id: str, token: str) -> str:
    """A Page photo post. One call."""
    out = _post(f"{API}/{page_id}/photos",
                {"url": image_url, "caption": caption, "access_token": token})
    return out.get("post_id") or out.get("id", "")


def to_instagram(image_url: str, caption: str, ig_id: str, token: str) -> str:
    """
    Container, then publish.

    The container is not always ready the instant it is created — Instagram has
    to fetch the image from the URL first — so the status is polled rather than
    assumed. Publishing an unfinished container fails, and the error it gives
    does not say why.
    """
    container = _post(f"{API}/{ig_id}/media",
                      {"image_url": image_url, "caption": caption,
                       "access_token": token})["id"]

    for attempt in range(12):                      # up to ~60s
        time.sleep(5)
        r = requests.get(f"{API}/{container}",
                         params={"fields": "status_code,status",
                                 "access_token": token}, timeout=60)
        status = r.json().get("status_code")
        if status == "FINISHED":
            break
        if status == "ERROR":
            raise RuntimeError(f"container failed: {r.json().get('status')}")
    else:
        raise RuntimeError("container was not ready after 60s")

    return _post(f"{API}/{ig_id}/media_publish",
                 {"creation_id": container, "access_token": token})["id"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--repo", required=True, help="owner/name, for the image URL")
    ap.add_argument("--sha", default="main",
                    help="commit to serve the image from. A sha pins the exact "
                         "image; main would serve whatever is there at fetch time")
    ap.add_argument("--dry-run", action="store_true",
                    help="say what would be posted, call nothing, write nothing")
    a = ap.parse_args()

    if (ROOT / "engine" / "HALT").exists():
        print("engine/HALT present — nothing posted.")
        return 0

    found = due(a.date)
    if not found:
        print(f"nothing due on {a.date}.")
        return 0
    folder, post, caps = found

    approved = folder / "APPROVED"
    if not approved.exists():
        print(f"{folder.name} is NOT approved — nothing posted.", file=sys.stderr)
        print(f"Approve it by commenting `approve` on the issue for {folder.name}.")
        return 0 if a.dry_run else 1

    book = ledger(folder)
    already = book.get(a.date, {})
    if already.get("instagram") and already.get("facebook"):
        print(f"{a.date} already posted — nothing to do. {already}")
        return 0

    shot = f"content/monthly/{folder.name}/{post['id']}__4x5.jpg"
    if not (ROOT / shot).exists():
        print(f"missing image {shot}", file=sys.stderr)
        return 1
    image_url = f"https://raw.githubusercontent.com/{a.repo}/{a.sha}/{shot}"

    ig_caption = caps.get("instagram", "")
    fb_caption = caps.get("facebook", ig_caption)
    if not ig_caption and not fb_caption:
        print(f"{post['id']} has no caption — refusing to post a bare image.",
              file=sys.stderr)
        return 1

    print(f"{a.date}  {post['id']}  ({post['pillar']})")
    print(f"  image: {image_url}")
    print(f"  instagram: {ig_caption[:120]}")
    print(f"  facebook : {fb_caption[:120]}")
    if a.dry_run:
        print("\ndry run — nothing was sent.")
        return 0

    token = os.environ.get("META_ACCESS_TOKEN")
    page_id = os.environ.get("META_PAGE_ID")
    ig_id = os.environ.get("META_IG_USER_ID")
    missing = [n for n, v in (("META_ACCESS_TOKEN", token), ("META_PAGE_ID", page_id),
                              ("META_IG_USER_ID", ig_id)) if not v]
    if missing:
        print("not set: " + ", ".join(missing), file=sys.stderr)
        return 1

    failures = []
    if not already.get("facebook"):
        try:
            already["facebook"] = to_facebook(image_url, fb_caption, page_id, token)
            print(f"  posted to Facebook: {already['facebook']}")
        except Exception as e:
            failures.append(f"facebook: {e}")
            print(f"  FACEBOOK FAILED: {e}", file=sys.stderr)

    if not already.get("instagram"):
        try:
            already["instagram"] = to_instagram(image_url, ig_caption, ig_id, token)
            print(f"  posted to Instagram: {already['instagram']}")
        except Exception as e:
            failures.append(f"instagram: {e}")
            print(f"  INSTAGRAM FAILED: {e}", file=sys.stderr)

    already["id"] = post["id"]
    already["at"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    book[a.date] = already
    save_ledger(folder, book)

    if failures:
        print("\nRe-running will retry only what is missing.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
