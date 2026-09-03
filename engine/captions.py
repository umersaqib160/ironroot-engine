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
import base64, json, os, sys
from pathlib import Path
import requests

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
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(raw)


def verify(image: Path, captions: dict) -> dict:
    """Second pass: does the caption describe THIS image?"""
    check = f"""Here is an image and four captions written for it.

{json.dumps({k: captions[k] for k in ("instagram","facebook","pinterest","tiktok")}, indent=2)}

For each caption, check every concrete visual or factual detail against the image.
Flag anything asserted that is not visible or is contradicted. Be strict: a
caption that says "eggs" when the pan holds vegetables is a failure, and so is
one implying a claim the image cannot support.

Return ONLY valid JSON:
{{"match": true/false, "problems": ["..."]}}"""
    raw = _call([_image_block(image), {"type": "text", "text": check}], 800)
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(raw)


def for_scene(image: Path, scene: dict, brand: str, recent: str) -> dict:
    caps = write_captions(image, scene, brand, recent)
    caps["verification"] = verify(image, caps)
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
