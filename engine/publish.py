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
sys.path.insert(0, str(ROOT / "engine"))
import approval            # noqa: E402
import caption_lint        # noqa: E402
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


TOKEN_DEAD = ("Facebook no longer accepts the access token — it was cancelled by a "
              "password change or a Facebook security reset. Nothing can post until "
              "META_ACCESS_TOKEN is replaced (automation/meta_setup.md).")


def plain(err: str) -> str:
    """Put the one Meta error that needs a person into words a person can act on."""
    if '"code":190' in err.replace(" ", ""):
        return TOKEN_DEAD + "  [Meta: " + err[:160] + "]"
    return err


def page_token(token: str, page_id: str) -> str:
    """
    The Page token to post with, whatever kind of token the secret holds.

    Two kinds of token can sit in META_ACCESS_TOKEN:
      - a Page token, made in the Graph API Explorer (what we started with)
      - a system-user token from Business Settings, which is not tied to
        anyone's Facebook login

    The first died on 2 Oct 2026, three days after it was made: "the session has
    been invalidated because the user changed their password or Facebook has
    changed the session for security reasons." It hangs off Umer's personal
    login, so anything that resets that login kills the posting. A system-user
    token does not, which is why we are moving to it.

    Asking the Page for its own access_token works with either kind and returns
    a Page token, so the rest of this file never needs to know which it was
    given.
    """
    r = requests.get(f"{API}/{page_id}", timeout=60,
                     params={"fields": "access_token", "access_token": token})
    if r.status_code != 200:
        raise RuntimeError(plain(f"{r.status_code} {r.text[:400]}"))
    return r.json().get("access_token") or token


def _post(url: str, payload: dict) -> dict:
    r = requests.post(url, data=payload, timeout=120)
    if r.status_code != 200:
        raise RuntimeError(plain(f"{r.status_code} {r.text[:400]}"))
    return r.json()


def preflight(image_url: str, page_id: str, ig_id: str, token: str) -> list[str]:
    """
    Everything a real post depends on, checked with read-only calls.

    A dry run used to stop before touching Meta, so it proved the captions and
    the approval but said nothing about the three secrets. A mistyped ID, or the
    one-hour token pasted instead of the permanent Page token, would only have
    surfaced at 15:00 on the first real posting day. Nothing here can post: every
    call is a GET.

    Never prints the token.
    """
    problems = []

    def get(path, **params):
        r = requests.get(f"{API}/{path}", params={**params, "access_token": token},
                         timeout=60)
        body = r.json() if r.headers.get("content-type", "").startswith(
            ("application/json", "text/javascript")) else {}
        return r.status_code, body

    # 1. The image, fetched the way Instagram will fetch it.
    r = requests.get(image_url, timeout=60)
    ctype = r.headers.get("content-type", "")
    if r.status_code != 200 or not ctype.startswith("image/jpeg"):
        problems.append(f"image not reachable as a JPEG: HTTP {r.status_code} {ctype}")
    else:
        print(f"  ok  image reachable ({len(r.content) // 1024} KB, {ctype})")

    # 2. Turn whatever token we were given into this Page's token. A dead token
    #    stops here, in plain words, instead of as three separate failures.
    try:
        given = token
        token = page_token(token, page_id)
        print("  ok  token accepted, Page token obtained" +
              ("" if token == given else
               " (the secret holds a user or system-user token; the Page token "
               "was derived from it)"))
    except Exception as e:
        problems.append(str(e))
        return problems

    # 3. The token is a PAGE token for THIS page. /me on a Page token answers
    #    with the Page; on a user token it answers with a person, which would
    #    post nothing and expire.
    code, me = get("me", fields="id,name")
    if code != 200:
        problems.append(f"token rejected by Meta: {me.get('error', {}).get('message', code)}")
        return problems
    if me.get("id") != page_id:
        problems.append(f"token belongs to {me.get('name')!r} ({me.get('id')}), not the "
                        f"Page in META_PAGE_ID ({page_id}) — likely the user token was "
                        f"pasted instead of the Page token")
    else:
        print(f"  ok  token is the Page token for {me.get('name')!r}")

    # 4. The Instagram account is the one linked to this Page.
    code, pg = get(page_id, fields="instagram_business_account{id,username}")
    linked = (pg.get("instagram_business_account") or {})
    if code != 200 or linked.get("id") != ig_id:
        problems.append(f"META_IG_USER_ID {ig_id} is not the Instagram account linked "
                        f"to the Page (linked: {linked.get('id')} {linked.get('username')})")
    else:
        print(f"  ok  Instagram @{linked.get('username')} is linked to the Page")

    # 5. Publishing rights on Instagram, and today's remaining allowance. This
    #    endpoint only answers for a token that may publish.
    code, lim = get(f"{ig_id}/content_publishing_limit", fields="config,quota_usage")
    if code != 200:
        problems.append("no permission to publish to Instagram: "
                        f"{lim.get('error', {}).get('message', code)}")
    else:
        d = (lim.get("data") or [{}])[0]
        total = (d.get("config") or {}).get("quota_total", "?")
        print(f"  ok  allowed to publish to Instagram "
              f"({d.get('quota_usage', 0)} of {total} used in the last 24h)")

    return problems


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
    ap.add_argument("--date", default="",
                    help="YYYY-MM-DD. Empty means today.")
    ap.add_argument("--repo", required=True, help="owner/name, for the image URL")
    ap.add_argument("--sha", default="main",
                    help="commit to serve the image from. A sha pins the exact "
                         "image; main would serve whatever is there at fetch time")
    ap.add_argument("--dry-run", action="store_true",
                    help="say what would be posted, call nothing, write nothing")
    a = ap.parse_args()

    # An argparse default does NOT cover this. The schedule has no date input,
    # so the workflow passes --date "" — an empty STRING, not an absent flag.
    # That made date[:7] an empty month, "nothing due" every single day, and an
    # exit code of 0, so the daily post would have quietly never run and nothing
    # would have complained. Caught in review before it shipped.
    if not a.date.strip():
        a.date = dt.date.today().isoformat()
    try:
        dt.date.fromisoformat(a.date)
    except ValueError:
        print(f"--date must be YYYY-MM-DD, got {a.date!r}", file=sys.stderr)
        return 2

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

    # Approval covers specific words and pictures, not a folder name. If the
    # month has changed since — a dropped post, a rewritten caption — the
    # approval was given to something else and does not count.
    want, have = approval.approved_digest(folder), approval.digest(folder)
    if want != have:
        why = ("was approved before approvals recorded what they covered"
               if want is None else "has changed since it was approved")
        print(f"{folder.name} {why} — nothing posted.", file=sys.stderr)
        print(f"  approved: {want or '(not recorded)'}   now: {have}", file=sys.stderr)
        print(f"Review it and comment `approve` again on the issue for {folder.name}.",
              file=sys.stderr)
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

    # Last gate before the public. The caption step runs the same rules, but a
    # caption can be edited by hand after that, and this is the one place every
    # caption has to pass through.
    bad = caption_lint.check_all({"instagram": ig_caption, "facebook": fb_caption})
    if bad:
        for net, probs in bad.items():
            for x in probs:
                print(f"  REFUSED {net}: {x}", file=sys.stderr)
        return 1

    print(f"{a.date}  {post['id']}  ({post['pillar']})")
    print(f"  image: {image_url}")
    print(f"  instagram: {ig_caption[:120]}")
    print(f"  facebook : {fb_caption[:120]}")
    if a.dry_run:
        token = os.environ.get("META_ACCESS_TOKEN")
        page_id = os.environ.get("META_PAGE_ID")
        ig_id = os.environ.get("META_IG_USER_ID")
        if token and page_id and ig_id:
            print("\nchecking the Meta connection (read-only, nothing is posted):")
            bad = preflight(image_url, page_id, ig_id, token)
            for b in bad:
                print(f"  FAIL {b}", file=sys.stderr)
            print("\ndry run — nothing was sent.")
            return 1 if bad else 0
        print("\ndry run — nothing was sent. (Meta secrets not set, so the "
              "connection was not checked.)")
        return 0

    token = os.environ.get("META_ACCESS_TOKEN")
    page_id = os.environ.get("META_PAGE_ID")
    ig_id = os.environ.get("META_IG_USER_ID")
    missing = [n for n, v in (("META_ACCESS_TOKEN", token), ("META_PAGE_ID", page_id),
                              ("META_IG_USER_ID", ig_id)) if not v]
    if missing:
        print("not set: " + ", ".join(missing), file=sys.stderr)
        return 1

    try:
        token = page_token(token, page_id)
    except Exception as e:
        print(f"  NOTHING POSTED: {e}", file=sys.stderr)
        print("\nRe-running after the token is replaced will post this day's item.",
              file=sys.stderr)
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
