"""
Generate one scene master with the Gemini image API, using subject placement.

THE METHOD (Umer, 3 Sep 2026 — see engine/prompts/image_scene.md):
attach the pan photograph and describe ONLY the scene. The prompt must never
describe the pan's shape, handle, finish, rim or rivets. In July 2026 the prompts
described the pan in prose, the model followed the prose over the attached photo,
and shipped a handle the pan does not have. The photo is the specification.

The single framing sentence we add is about where the pan sits in the frame, so
the deterministic crops in reframe.py never clip it. That is composition, not a
description of the object, and it is the only addition allowed.

Masters are generated at 9:16 because it is the tallest target — reframe.py cuts
2:3 and 4:5 out of it without upscaling. One generation per concept, not three:
every generation is another chance to draw the pan wrong.
"""
from __future__ import annotations
import base64, json, os, sys, time
from pathlib import Path
import requests

BASE = "https://generativelanguage.googleapis.com/v1beta"
MODEL = os.environ.get("IRONROOT_IMAGE_MODEL", "gemini-3-pro-image")
REFERENCE = Path("content/images/reference/PRIMARY_pan_studio_2048.jpg")

# Umer's tested wording, reproduced EXACTLY when the defaults are used. Nothing
# is appended by default.
#
# The 3 Sep run proved why. Two sentences were added to this template — a
# lighting note and a framing instruction ("leaving clear space above and below,
# so the image can be cropped") — and aspect_ratio was forced to 9:16. The model
# returned a SQUARE composition padded with flat bands to 44% of the frame, and
# a pan with two handles and a rim lip. Asking for clear space produced literal
# empty space, and the extra instruction load pulled the model off the reference.
#
# This is the same failure as July in a new costume: words competing with the
# photograph. Extras are now opt-in via --extra and never silently on.

TEMPLATE = ("Use this frying pan in the image and then create an image for "
            "{platform} where {scene}. The setting of the home is {mood}, "
            "with {palette} shades.")


def build_prompt(platform: str, scene: str, mood: str, palette: str,
                 extra: str = "") -> str:
    """Umer's template verbatim. `extra` is for experiments only — never a default."""
    prompt = TEMPLATE.format(platform=platform, scene=scene, mood=mood,
                             palette=palette)
    return f"{prompt} {extra}".strip() if extra else prompt


# --- Two request shapes -----------------------------------------------------
# The first run failed and the endpoint shape was taken from a docs summary that
# could not be verified from here (no network to the API from either machine).
# So we try both known shapes and report which one worked, rather than guessing
# again. Whichever succeeds becomes the only one we keep.

def _req_interactions(prompt: str, ref_b64: str, ratio: str | None, size: str):
    fmt = {"type": "image", "image_size": size}
    if ratio:
        fmt["aspect_ratio"] = ratio
    return (f"{BASE}/interactions", {
        "model": MODEL,
        "input": [
            {"type": "text", "text": prompt},
            {"type": "image", "mime_type": "image/jpeg", "data": ref_b64},
        ],
        "response_format": fmt,
    })


def _req_generate_content(prompt: str, ref_b64: str, ratio: str | None, size: str):
    image_cfg = {"imageSize": size}
    if ratio:
        image_cfg["aspectRatio"] = ratio
    return (f"{BASE}/models/{MODEL}:generateContent", {
        "contents": [{"role": "user", "parts": [
            {"text": prompt},
            {"inline_data": {"mime_type": "image/jpeg", "data": ref_b64}},
        ]}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": image_cfg,
        },
    })


def _extract_image(body: dict) -> str | None:
    """Pull base64 image data out of either response shape."""
    img = body.get("output_image") or {}
    if isinstance(img, dict) and img.get("data"):
        return img["data"]
    for cand in body.get("candidates") or []:
        for part in (cand.get("content") or {}).get("parts") or []:
            blob = part.get("inlineData") or part.get("inline_data") or {}
            if blob.get("data"):
                return blob["data"]
    return None


def generate(prompt: str, out_path: Path, image_size: str = "2K",
             ratio: str | None = None, reference: Path = REFERENCE) -> Path:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        sys.exit("GEMINI_API_KEY is not set (repo secret, Settings > Secrets "
                 "and variables > Actions).")
    if not reference.exists():
        sys.exit(f"Reference photo missing: {reference}")

    ref_b64 = base64.b64encode(reference.read_bytes()).decode()
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
    errors = []

    for label, builder in (("generateContent", _req_generate_content),
                           ("interactions", _req_interactions)):
        url, payload = builder(prompt, ref_b64, ratio, image_size)
        print(f"\n--- trying {label}: POST {url}", flush=True)
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=240)
        except Exception as e:
            errors.append(f"{label}: request failed: {e}")
            print(f"    request failed: {e}", flush=True)
            continue

        print(f"    HTTP {r.status_code}", flush=True)
        if r.status_code == 200:
            data = _extract_image(r.json())
            if data:
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_bytes(base64.b64decode(data))
                print(f"    OK via {label}", flush=True)
                return out_path
            print("    200 but no image in the response. Body preview:", flush=True)
            print(json.dumps(r.json(), indent=2)[:1500], flush=True)
            errors.append(f"{label}: 200 without image data")
            continue

        # Show the real error — this is what the first run hid.
        body = r.text[:900]
        print(f"    error body: {body}", flush=True)
        errors.append(f"{label}: HTTP {r.status_code} {body[:250]}")

    sys.exit("Both request shapes failed:\n  " + "\n  ".join(errors))


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Generate one scene master.")
    ap.add_argument("--platform", default="Instagram")
    ap.add_argument("--scene", required=True,
                    help="what is happening, e.g. 'the pan is being used by a chef at home'")
    ap.add_argument("--mood", default="cozy but dark")
    ap.add_argument("--palette", default="brown, black, cream")
    ap.add_argument("--extra", default="",
                    help="EXPERIMENTS ONLY. Appended verbatim. Every word here "
                         "competes with the reference photo.")
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", default="2K", choices=["512px", "1K", "2K", "4K"])
    ap.add_argument("--ratio", default="",
                    help="Empty (default) sends no aspect ratio at all — forcing "
                         "one made the model pad instead of compose.")
    a = ap.parse_args()

    prompt = build_prompt(a.platform, a.scene, a.mood, a.palette, a.extra)
    print("PROMPT:", prompt, flush=True)
    p = generate(prompt, Path(a.out), image_size=a.size, ratio=a.ratio or None)
    print(f"WROTE: {p}  ({p.stat().st_size/1024:.0f} KB)")
