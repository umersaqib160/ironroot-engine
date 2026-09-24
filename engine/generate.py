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
import base64, hashlib, json, os, sys, time
from pathlib import Path
import requests

BASE = "https://generativelanguage.googleapis.com/v1beta"
MODEL = os.environ.get("IRONROOT_IMAGE_MODEL", "gemini-3-pro-image-preview")
REFERENCE = Path("content/images/reference/PRIMARY_pan_studio_2048.jpg")

# Umer's verified wording (3 Sep 2026), reproduced exactly when defaults are used.
#
# CONSTRAINT is the one sentence about the pan that is allowed, and it earned its
# place: five generations produced a deep wok-shaped body, and this line fixed it.
#
# The rule is therefore NOT "never mention the pan". It is:
#   - never DESCRIBE the pan — the photograph is the specification
#   - a short CORRECTIVE CONSTRAINT against a known, repeated drift is allowed
# A flat ban on adjectives would have forbidden the very sentence that worked.
# Anything added here must be a correction to an observed failure, never a
# description of what the pan looks like.

TEMPLATE = ("Use the image from the frying pan and create an image for {platform} "
            "where {scene}. The setting of the home is {mood}.")

# Corrective constraints. Each one exists because a specific drift was observed
# in a real generation and this wording fixed it. Never add a line here to
# DESCRIBE the pan — only to correct a failure we have actually seen.
#
#   "not too deep"  -> 5 generations produced a deep wok-shaped body (3 Sep)
#   "no rim lip"    -> rolled lip on the rim, confirmed at full res (3 Sep).
#                      Was "no lip ring"; Umer reworded it — "rim lip" is the
#                      term the model is likelier to have learned.
#   "plain photograph" -> p4_meal_prep came back as a rendered INSTAGRAM POST:
#                      like/comment/share icons, carousel dots, a bookmark, white
#                      chrome top and bottom (24 Sep). The prompt says "an image
#                      for Instagram" and the model drew the app. The platform
#                      name stays because it is Umer's tested wording and it
#                      shapes the composition; this sentence blocks the app.
#   "only pan"      -> p2_couple_cooking put a BLACK NON-STICK pan on the next
#                      burner, beside the IronRoot one (24 Sep). The same month
#                      runs an education card saying non-stick pans carry PFAS.
#                      A coated pan in our own photo argues against us.
CONSTRAINT = ("Make sure the pan is not too deep and has no rim lip. "
              "It is the only pan in the picture. "
              "It must be a plain photograph with no app interface, no icons, "
              "no buttons, no border and no caption bar.")


def build_prompt(platform: str, scene: str, mood: str, palette: str = "",
                 extra: str = "") -> str:
    """Umer's template verbatim, plus the depth constraint. Extras are opt-in."""
    parts = [TEMPLATE.format(platform=platform, scene=scene, mood=mood)]
    if palette:
        parts.append(f"The shades are {palette}.")
    parts.append(CONSTRAINT)
    if extra:
        parts.append(extra)
    return " ".join(parts)


# --- Two request shapes -----------------------------------------------------
# The first run failed and the endpoint shape was taken from a docs summary that
# could not be verified from here (no network to the API from either machine).
# So we try both known shapes and report which one worked, rather than guessing
# again. Whichever succeeds becomes the only one we keep.

def _req_interactions(prompt: str, ref_b64: str | None, ratio: str | None, size: str):
    fmt = {"type": "image", "image_size": size}
    if ratio:
        fmt["aspect_ratio"] = ratio
    return (f"{BASE}/interactions", {
        "model": MODEL,
        "input": (
            [{"type": "text", "text": prompt}] +
            ([{"type": "image", "mime_type": "image/jpeg", "data": ref_b64}]
             if ref_b64 else [])
        ),
        "response_format": fmt,
    })


def _req_generate_content(prompt: str, ref_b64: str | None, ratio: str | None, size: str):
    image_cfg = {"imageSize": size}
    if ratio:
        image_cfg["aspectRatio"] = ratio
    return (f"{BASE}/models/{MODEL}:generateContent", {
        "contents": [{"role": "user", "parts": (
            [{"text": prompt}] +
            ([{"inline_data": {"mime_type": "image/jpeg", "data": ref_b64}}]
             if ref_b64 else [])
        )}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": image_cfg,
        },
    })


def _extract_image(body: dict) -> str | None:
    """
    Pull base64 image data out of the response.

    The newer Gemini image models return the image natively inside the standard
    SDK structure — candidates[0].content.parts[], as an inline_data blob — not
    as a URL and not as a dedicated top-level image field. REST JSON camel-cases
    it to inlineData, the SDK and the docs use inline_data, so accept both.

    A model that declines or explains itself returns TEXT parts instead. Surface
    that rather than reporting a bare "no image", because the text says why.
    """
    img = body.get("output_image") or {}
    if isinstance(img, dict) and img.get("data"):
        return img["data"]

    texts = []
    for cand in body.get("candidates") or []:
        for part in (cand.get("content") or {}).get("parts") or []:
            blob = part.get("inlineData") or part.get("inline_data") or {}
            if blob.get("data"):
                return blob["data"]
            if part.get("text"):
                texts.append(part["text"])
        if cand.get("finishReason") not in (None, "STOP"):
            print(f"    finishReason: {cand['finishReason']}", file=sys.stderr)

    if texts:
        print("    model returned TEXT instead of an image:", file=sys.stderr)
        print("    " + " ".join(texts)[:600], file=sys.stderr)
    return None


def generate(prompt: str, out_path: Path, image_size: str = "2K",
             ratio: str | None = None, reference: Path = REFERENCE) -> Path:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        sys.exit("GEMINI_API_KEY is not set (repo secret, Settings > Secrets "
                 "and variables > Actions).")
    if reference is not None and not reference.exists():
        sys.exit(f"Reference photo missing: {reference}")

    if reference is None:
        ref_b64 = None
        print("REFERENCE: *** NONE — control run, text prompt only ***", flush=True)
    else:
        raw = reference.read_bytes()
        if len(raw) < 10_000:
            sys.exit(f"Reference {reference} is only {len(raw)} bytes — refusing "
                     "to generate. A truncated or missing reference is how the "
                     "pan drifts.")
        ref_b64 = base64.b64encode(raw).decode()
        print(f"REFERENCE ATTACHED: {reference}", flush=True)
        print(f"  {len(raw):,} bytes  sha256 {hashlib.sha256(raw).hexdigest()[:16]}"
              f"  -> {len(ref_b64):,} chars base64", flush=True)
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
    errors = []

    for label, builder in (("generateContent", _req_generate_content),
                           ("interactions", _req_interactions)):
        url, payload = builder(prompt, ref_b64, ratio, image_size)
        print(f"\n--- trying {label}: POST {url}", flush=True)
        parts = (payload["contents"][0]["parts"] if "contents" in payload
                 else payload["input"])
        img_parts = [p for p in parts
                     if "inline_data" in p or "inlineData" in p
                     or p.get("type") == "image"]
        print(f"    payload parts: {len(parts)} -> "
              f"{[sorted(p.keys()) for p in parts]}", flush=True)
        if ref_b64 and not img_parts:
            sys.exit("ABORT: the reference was loaded but is NOT in the request "
                     "payload. Generating without it is what produces a generic "
                     "pan — refusing to spend the call.")
        if ref_b64:
            sent = img_parts[0].get("inline_data") or img_parts[0].get("inlineData") or img_parts[0]
            print(f"    image part confirmed: {len(sent.get('data','')):,} chars"
                  f" ({sent.get('mime_type') or sent.get('mimeType')})", flush=True)
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=240)
        except Exception as e:
            errors.append(f"{label}: request failed: {e}")
            print(f"    request failed: {e}", flush=True)
            continue

        print(f"    HTTP {r.status_code}", flush=True)
        if r.status_code == 200:
            body = r.json()
            # The API may silently serve a different build than the ID we asked
            # for. Log what actually answered — never assume.
            served = body.get("modelVersion") or body.get("model") or "(not reported)"
            print(f"    requested model : {MODEL}", flush=True)
            print(f"    served by       : {served}", flush=True)
            # A silent substitution would invalidate every conclusion drawn from
            # the output, so say so rather than letting it pass unnoticed.
            base = MODEL.removesuffix("-preview")
            if served != "(not reported)" and MODEL not in served and base not in served:
                print(f"    *** WARNING: asked for {MODEL} but {served} answered. "
                      f"Results are NOT from the requested model. ***", flush=True)
            data = _extract_image(body)
            if data:
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_bytes(base64.b64decode(data))
                print(f"    OK via {label}", flush=True)
                return out_path
            print("    200 but no image in the response. Body preview:", flush=True)
            print(json.dumps(body, indent=2)[:1500], flush=True)
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
    ap.add_argument("--mood", default="dim light but cozy")
    ap.add_argument("--palette", default="",
                    help="Optional. Umer's verified prompt carries mood only.")
    ap.add_argument("--extra", default="",
                    help="EXPERIMENTS ONLY. Appended verbatim. Every word here "
                         "competes with the reference photo.")
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", default="2K", choices=["512px", "1K", "2K", "4K"])
    ap.add_argument("--no-reference", action="store_true",
                    help="CONTROL RUN: send the text prompt with NO reference "
                         "photo. If output quality is unchanged, the reference "
                         "was never influencing the result.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Build and print the prompt, then exit. No API call, "
                         "no cost. Catches CLI/workflow mismatches.")
    ap.add_argument("--model", default="",
                    help="Override the image model ID. Empty uses "
                         "IRONROOT_IMAGE_MODEL or the built-in default.")
    ap.add_argument("--ratio", default="",
                    help="Empty (default) sends no aspect ratio at all — forcing "
                         "one made the model pad instead of compose.")
    a = ap.parse_args()

    if a.model:
        MODEL = a.model  # noqa: F841 - rebinding the module global below
        globals()["MODEL"] = a.model
    print(f"MODEL REQUESTED: {MODEL}")
    prompt = build_prompt(a.platform, a.scene, a.mood, a.palette, a.extra)
    print("PROMPT:", prompt, flush=True)
    if a.dry_run:
        print("DRY RUN — arguments accepted, no API call made.")
        raise SystemExit(0)
    p = generate(prompt, Path(a.out), image_size=a.size, ratio=a.ratio or None,
                 reference=None if a.no_reference else REFERENCE)
    print(f"WROTE: {p}  ({p.stat().st_size/1024:.0f} KB)")
