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

FRAMING = (
    "Compose it vertically with the pan in the central band of the frame, "
    "leaving clear space above and below, so the image can be cropped to "
    "narrower shapes without cutting the pan."
)


def build_prompt(platform: str, scene: str, setting: str, palette: str, light: str) -> str:
    """Assemble the prompt. Contains no description of the pan — by design."""
    return (
        f"Use this frying pan in the image, then create an image for {platform} "
        f"where {scene}. The setting is {setting}, with {palette} shades. {light} "
        f"{FRAMING}"
    )


# --- Two request shapes -----------------------------------------------------
# The first run failed and the endpoint shape was taken from a docs summary that
# could not be verified from here (no network to the API from either machine).
# So we try both known shapes and report which one worked, rather than guessing
# again. Whichever succeeds becomes the only one we keep.

def _req_interactions(prompt: str, ref_b64: str, ratio: str, size: str):
    return (f"{BASE}/interactions", {
        "model": MODEL,
        "input": [
            {"type": "text", "text": prompt},
            {"type": "image", "mime_type": "image/jpeg", "data": ref_b64},
        ],
        "response_format": {"type": "image", "aspect_ratio": ratio,
                            "image_size": size},
    })


def _req_generate_content(prompt: str, ref_b64: str, ratio: str, size: str):
    return (f"{BASE}/models/{MODEL}:generateContent", {
        "contents": [{"role": "user", "parts": [
            {"text": prompt},
            {"inline_data": {"mime_type": "image/jpeg", "data": ref_b64}},
        ]}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": ratio, "imageSize": size},
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
             ratio: str = "9:16", reference: Path = REFERENCE) -> Path:
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
    ap.add_argument("--setting", default="a cozy but dark home kitchen")
    ap.add_argument("--palette", default="brown, black and cream")
    ap.add_argument("--light", default="Warm directional light, deep shadows.")
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", default="2K", choices=["512px", "1K", "2K", "4K"])
    ap.add_argument("--ratio", default="9:16")
    a = ap.parse_args()

    prompt = build_prompt(a.platform, a.scene, a.setting, a.palette, a.light)
    print("PROMPT:", prompt, flush=True)
    p = generate(prompt, Path(a.out), image_size=a.size, ratio=a.ratio)
    print(f"WROTE: {p}  ({p.stat().st_size/1024:.0f} KB)")
