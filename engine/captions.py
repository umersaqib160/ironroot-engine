"""
Write captions FROM THE IMAGE, never from the prompt.

Why this matters more than it sounds:

The prompt is what we ASKED FOR. The image is what we GOT, and the model composes
freely around the brief. Real examples from the 3 Sep generations, none of which
were requested:

  - a baby in a carrier, and a second child playing with blocks
  - fairy lights strung across the window
  - a gas hob (the brand sells to induction users too)
  - COPPER pans on the shelf, in a stainless brand's photograph
  - a book with garbled fake lettering on the cover

A caption written from the prompt would describe a kitchen that does not exist,
and would happily say "the only pan you need" beside visible copper cookware.
Only a caption written from the actual pixels can avoid that.

So the split is:

  INTENT  -> from the scene record (which claim this post carries, what the
             caption must say, what it must never say). Structured, not prose.
  FACTS   -> from the image, via vision.

The raw prompt is deliberately NOT passed to the caption model at all. If it were
in context it would read as a description of reality, which is the exact error
this design exists to prevent.

A second pass then checks the caption against the image again: does every
concrete visual detail it mentions actually appear? That is cheap and catches the
mismatch that matters.
"""
from __future__ import annotations
import base64, json, os, sys, time
from pathlib import Path
import requests

import caption_lint

API = "https://api.anthropic.com/v1/messages"
MODEL = os.environ.get("IRONROOT_CAPTION_MODEL", "claude-sonnet-4-5")
ROOT = Path(__file__).resolve().parent.parent


def _call(blocks: list[dict], max_tokens: int = 1500) -> str:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    r = requests.post(API, timeout=180,
                      headers={"x-api-key": key,
                               "anthropic-version": "2023-06-01",
                               "content-type": "application/json"},
                      json={"model": MODEL, "max_tokens": max_tokens,
                            "messages": [{"role": "user", "content": blocks}]})
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:600]}")
    body = r.json()
    print(f"    caption model: {body.get('model', '?')}", flush=True)
    return "".join(b.get("text", "") for b in body.get("content", []))


def _json(raw: str) -> dict:
    """
    Pull the JSON object out of a reply, whatever surrounds it.

    Stripping a ```json fence was the only tolerance before, so a reply that
    opened with a sentence ("Here are the captions:") or closed with one failed
    to parse and the post was left with no caption at all. That is what happened
    to jeroen_k in October — one post out of thirteen, silently captionless.
    """
    raw = raw.strip()
    a, b = raw.find("{"), raw.rfind("}")
    if a == -1 or b <= a:
        raise ValueError(f"no JSON object in reply: {raw[:200]!r}")
    return json.loads(raw[a:b + 1])


def _image_block(path: Path) -> dict:
    return {"type": "image",
            "source": {"type": "base64", "media_type": "image/jpeg",
                       "data": base64.b64encode(path.read_bytes()).decode()}}


def write_captions(image: Path, scene: dict, brand: str, recent: str) -> dict:
    guards = []
    if scene.get("claim"):
        guards.append(f"This post carries the claim: {scene['claim']}")
    if scene.get("caption_must"):
        guards.append(f"The caption MUST: {scene['caption_must'].strip()}")
    if scene.get("caption_never"):
        guards.append(f"The caption MUST NEVER: {scene['caption_never'].strip()}")

    instruction = f"""You are writing social captions for IronRoot, a stainless steel frying pan brand.

Look at the attached image. Write the captions from WHAT YOU CAN SEE IN IT.
You have not been given the prompt that produced this image, deliberately — the
image is the only source of visual fact. Never describe anything you cannot see.

{chr(10).join(guards) if guards else "This post carries no specific product claim."}

BRAND (voice, pillars, and the verified claims table — the claims table is binding):
{brand}

THE LAST TWO WEEKS OF CAPTIONS — do not repeat these hooks, angles or phrasing:
{recent or "(none yet)"}

Return ONLY valid JSON, no markdown fence, with exactly these keys:
{{"instagram": "...", "facebook": "...", "pinterest": "...", "tiktok": "...",
  "visible_in_image": ["concrete things you can actually see"],
  "concerns": ["anything in the image that undercuts the brand, e.g. visible
               copper cookware, mangled text on props, a second pan, a damaged
               finish — empty list if none"]}}"""

    raw = _call([_image_block(image), {"type": "text", "text": instruction}])
    out = _json(raw)
    missing = [k for k in ("instagram", "facebook") if not (out.get(k) or "").strip()]
    if missing:
        raise ValueError(f"reply had no {', '.join(missing)} caption")
    # Rules that need no judgement: a wrong web address, a non-stick claim.
    # Raising sends it round the retry loop; three strikes and the post has no
    # caption, which the poster refuses — a gap, never a wrong post.
    bad = caption_lint.check_all(out)
    if bad:
        raise ValueError("caption broke a rule: " +
                         "; ".join(f"{k}: {x}" for k, v in bad.items() for x in v))
    return out


def verify(image: Path, captions: dict) -> dict:
    """Second pass: does the caption describe THIS image?"""
    check = f"""Here is an image and four captions written for it.

{json.dumps({k: captions[k] for k in ("instagram","facebook","pinterest","tiktok")}, indent=2)}

Check only what the captions say ABOUT THIS PICTURE — the scene, the food, the
people, what is happening, where the pan is. Flag anything that contradicts the
image or describes something that is not in it. Be strict: a caption that says
"eggs" when the pan holds vegetables fails, and so does one that puts the pan on
a stovetop when it is going into an oven.

Do NOT flag product facts. These are verified against the store and are allowed
in every caption even though a photo cannot show them: the brand name IronRoot,
the price, PFAS-free, tri-ply, oven safe to 500F, dishwasher safe, works on all
cooktops including induction, free shipping, the 30-day guarantee, and
durability or "pan for life" language. An earlier version of this check failed
ten of thirteen captions for stating exactly these, which made its verdict
worthless.

Return ONLY valid JSON:
{{"match": true/false, "problems": ["..."]}}"""
    raw = _call([_image_block(image), {"type": "text", "text": check}], 800)
    return _json(raw)


def for_scene(image: Path, scene: dict, brand: str, recent: str,
              attempts: int = 3) -> dict:
    """
    Write, then check. Retried, because one failed call should not leave a post
    with no caption — the poster refuses to publish a bare image, so a single
    transient error here becomes a missed day two weeks later.
    """
    last = None
    for n in range(1, attempts + 1):
        try:
            caps = write_captions(image, scene, brand, recent)
            break
        except Exception as e:                      # noqa: BLE001
            last = e
            print(f"    caption attempt {n}/{attempts} failed: {e}", flush=True)
            time.sleep(3 * n)
    else:
        raise RuntimeError(f"no caption after {attempts} attempts: {last}")

    # The check is advisory; a failed check must not throw away a good caption.
    try:
        caps["verification"] = verify(image, caps)
    except Exception as e:                          # noqa: BLE001
        caps["verification"] = {"match": False,
                                "problems": [f"check could not run: {e}"]}
    return caps


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--scene-id", required=True)
    a = ap.parse_args()
    import yaml
    lib = yaml.safe_load((ROOT / "engine" / "scenes.yaml").read_text(encoding="utf-8"))
    scene = next(s for s in lib["scenes"] if s["id"] == a.scene_id)
    brand = (ROOT / "engine" / "brand.md").read_text(encoding="utf-8")
    out = for_scene(Path(a.image), scene, brand, "")
    print(json.dumps(out, indent=2))
