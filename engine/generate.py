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

ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions"
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


def generate(prompt: str, out_path: Path, image_size: str = "2K",
             reference: Path = REFERENCE, retries: int = 2) -> Path:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        sys.exit("GEMINI_API_KEY is not set. In GitHub Actions this comes from "
                 "Settings > Secrets and variables > Actions.")
    if not reference.exists():
        sys.exit(f"Reference photo missing: {reference}")

    payload = {
        "model": MODEL,
        "input": [
            {"type": "text", "text": prompt},
            {"type": "image",
             "mime_type": "image/jpeg",
             "data": base64.b64encode(reference.read_bytes()).decode()},
        ],
        "response_format": {"type": "image", "aspect_ratio": "9:16",
                            "image_size": image_size},
    }

    last = None
    for attempt in range(1, retries + 2):
        r = requests.post(ENDPOINT, json=payload, timeout=180,
                          headers={"x-goog-api-key": api_key,
                                   "Content-Type": "application/json"})
        if r.status_code == 200:
            body = r.json()
            data = (body.get("output_image") or {}).get("data")
            if not data:
                # Shape changed or the model refused — show enough to diagnose
                # from the Actions log without dumping base64 into it.
                print("Unexpected response shape. Top-level keys:",
                      list(body.keys()), file=sys.stderr)
                print(json.dumps(body, indent=2)[:1500], file=sys.stderr)
                sys.exit("No image in response.")
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(base64.b64decode(data))
            return out_path

        last = f"HTTP {r.status_code}: {r.text[:600]}"
        # 429/5xx are worth retrying; 4xx client errors are not.
        if r.status_code not in (429, 500, 502, 503, 504):
            break
        wait = 5 * attempt
        print(f"  attempt {attempt} failed ({r.status_code}), retrying in {wait}s",
              file=sys.stderr)
        time.sleep(wait)

    sys.exit(f"Generation failed. {last}")


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
    a = ap.parse_args()

    prompt = build_prompt(a.platform, a.scene, a.setting, a.palette, a.light)
    print("PROMPT:", prompt, flush=True)
    p = generate(prompt, Path(a.out), image_size=a.size)
    print(f"WROTE: {p}  ({p.stat().st_size/1024:.0f} KB)")
