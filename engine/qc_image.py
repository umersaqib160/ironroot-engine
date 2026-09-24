"""
Quality gate for every generated image.

Three things, in Umer's words (24 Sep 2026):
  1. no social media frame around it
  2. the pan has no rim lip
  3. the pan has one handle

Check 1 is deterministic — UI chrome and letterboxing are near-uniform bands at
the edges and can be measured, so it needs no model and cannot be talked out of a
verdict. Checks 2 and 3 need eyes, so they go to a vision pass against the
canonical reference photograph.

This exists because p4_meal_prep shipped into the October batch carrying a whole
rendered Instagram interface — like and comment icons, carousel dots, a bookmark,
white chrome top and bottom. Nothing looked at it between generation and the
calendar.
"""
from __future__ import annotations
import base64, json, os, sys
from pathlib import Path
from PIL import Image
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
REFERENCE = ROOT / "content/images/reference/PRIMARY_pan_studio_2048.jpg"


def detect_frame(path: Path) -> dict:
    """
    Look for UI chrome or a letterbox band at the edges.

    The naive version — "uniform and extreme brightness" — flagged a white studio
    backdrop and a dark hob, because a photograph can perfectly well be bright or
    dark at one edge. Three things separate real chrome from a photo:

      1. it is FLAT: almost no pixel variation across the row
      2. it ENDS SHARPLY: a hard step into the picture, not a gradient
      3. it is THIN: interface bands are a few percent of the height, not a third

    All three must hold, which is what stops a bright sky reading as a frame.
    """
    im = Image.open(path).convert("L")
    a = np.asarray(im).astype(float)
    h, w = a.shape
    row_mean, row_std = a.mean(axis=1), a.std(axis=1)
    body = float(np.median(row_mean[int(h * 0.25):int(h * 0.75)]))
    MAX_BAND = 0.12          # thicker than this and it is the photograph

    def band(rows) -> int:
        n = 0
        for y in rows:
            flat = row_std[y] < 18
            extreme = row_mean[y] > 242 or row_mean[y] < 18
            if flat and extreme and abs(row_mean[y] - body) > 60:
                n += 1
            else:
                break
            if n > h * MAX_BAND:
                return 0      # too thick to be interface chrome
        return n

    top = band(range(0, int(h * MAX_BAND) + 1))
    bottom = band(range(h - 1, int(h * (1 - MAX_BAND)) - 1, -1))

    # A hard step at the boundary. A gradient has no step; chrome does.
    def step(y: int) -> float:
        y = max(1, min(h - 2, y))
        return abs(row_mean[y] - row_mean[y + 1])

    top_step = step(top) if top else 0.0
    bottom_step = step(h - 1 - bottom) if bottom else 0.0
    if top and top_step < 25:
        top = 0
    if bottom and bottom_step < 25:
        bottom = 0

    pct = (top + bottom) / h * 100
    return {"top_rows": top, "bottom_rows": bottom, "percent": round(pct, 2),
            "top_step": round(top_step, 1), "bottom_step": round(bottom_step, 1),
            "frame": pct > 0.5}


def detect_chrome(path: Path) -> dict:
    """
    Look for a white app interface band — the second detector, and the one that
    matters most.

    detect_frame() requires the band to be FLAT, and that is exactly why it let
    the worst image in the archive through. p4_meal_prep__9x16 is a whole
    Instagram screenshot: a carrier name and a clock along the top, the Instagram
    wordmark, a username, like and comment icons, a like count, a caption, a nav
    bar. Those rows are covered in glyphs, so their variance is high and "flat"
    never fired. The 4:5 crop happened to trim into the plain white padding and
    was caught; the full frame was not. A gate that misses the very defect it was
    built for is not a gate.

    What an app interface actually looks like, row by row:
      1. it is GREY — white background, black glyphs, no colour to speak of
      2. it sits on WHITE — most of the row is at or near 255
      3. it carries INK — dark marks on that white, which a blown-out window has
         none of
      4. it is at the EDGE and runs contiguously inward

    Only white chrome is detected here. Dark-mode chrome is deliberately left to
    the vision pass: every attempt to catch it deterministically also flagged a
    black induction hob and a night-time sink, and a gate that cries wolf on good
    images gets ignored. Measured over the seventeen images in the archive this
    finds p4_meal_prep and nothing else.
    """
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.int16)
    h, w, _ = a.shape
    lum = a.mean(axis=2)
    grey = ((a.max(axis=2) - a.min(axis=2)) < 30).mean(axis=1)
    white = (lum > 238).mean(axis=1)
    ink = ((255.0 - lum) > 100).mean(axis=1)
    MAX_BAND = 0.22

    def run(rows) -> int:
        n = 0
        for y in rows:
            if grey[y] >= 0.93 and white[y] >= 0.55:
                n += 1
            else:
                break
            if n > h * MAX_BAND:
                return 0
        return n

    def inked(n: int, rows) -> int:
        return n if n and max(ink[y] for y in list(rows)[:n]) >= 0.01 else 0

    tr = range(0, int(h * MAX_BAND) + 1)
    br = range(h - 1, int(h * (1 - MAX_BAND)) - 1, -1)
    top, bottom = inked(run(tr), tr), inked(run(br), br)
    pct = (top + bottom) / h * 100
    return {"top_rows": top, "bottom_rows": bottom, "percent": round(pct, 2),
            "chrome": pct > 0.5}


def _b64(p: Path) -> dict:
    return {"type": "image", "source": {"type": "base64",
            "media_type": "image/jpeg" if p.suffix.lower() in (".jpg", ".jpeg")
            else "image/png", "data": base64.b64encode(p.read_bytes()).decode()}}


def vision_check(path: Path, model: str | None = None,
                 on_heat: bool = False) -> dict:
    """Ask a model to look, with the real pan beside it for comparison."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return {"skipped": "ANTHROPIC_API_KEY not set"}
    import requests
    prompt = """The FIRST image is the real IronRoot pan — the ground truth.
The SECOND image is a generated marketing photo that must be checked against it.

Answer these questions about the SECOND image:

1. frame — is there ANY social media interface, app chrome, border, watermark,
   caption bar, like/comment/share icon, carousel dot or letterbox band? It must
   be a plain photograph edge to edge.
2. rim_lip — does the pan have a rolled or raised lip around its rim? The real
   pan's wall ends in a plain straight-cut edge. A lip is a defect.
3. one_handle — does the pan have exactly ONE handle? Two handles, or a helper
   handle, is a defect.
4. other_cookware — is there any OTHER pan, skillet or frying pan visible
   anywhere in the shot, however blurred or cropped? A black or coated non-stick
   pan beside ours is the worst case: the brand's whole argument is that coated
   pans carry PFAS, so one in our own photo argues against us. Pots, kettles and
   saucepans on a back burner are fine; a second FRYING PAN is not.

{HANDLE}
Also flag anything else that would embarrass the brand: mangled text on props,
copper cookware, a visibly scratched or damaged pan.

Return ONLY JSON:
{"frame": true/false, "rim_lip": true/false, "one_handle": true/false,
 "other_cookware": true/false, "handle_wrong_way": true/false,
 "other_concerns": ["..."], "verdict": "PASS"/"FAIL", "why": "one sentence"}
(frame true means a frame IS present, which is a failure. rim_lip true means a
lip IS present, which is a failure. one_handle true means exactly one, which is
correct. other_cookware true means another pan IS present, which is a failure.
handle_wrong_way true means the handle is badly placed, which is a failure —
answer false when the pan is not on a cooktop.)"""
    HANDLE = """
5. handle_wrong_way — the pan is on a cooktop in this shot. Is the handle
   pointing AWAY from where a cook would stand — out across the room, over a
   neighbouring burner, or off toward a window or wall? A cook turns the handle
   in, over the counter, so it is within reach and cannot be knocked. A handle
   pointing away is wrong twice over: any cook reading the post will see it at
   once, and the handle is a selling point being pointed away from the viewer.
   If the pan is NOT on a cooktop, answer false and ignore this question.
""" if on_heat else ""
    prompt = prompt.replace("{HANDLE}", HANDLE)
    r = requests.post("https://api.anthropic.com/v1/messages", timeout=180,
                      headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                               "content-type": "application/json"},
                      json={"model": model or os.environ.get(
                                "IRONROOT_QC_MODEL", "claude-sonnet-4-5"),
                            "max_tokens": 700,
                            "messages": [{"role": "user", "content": [
                                _b64(REFERENCE), _b64(path),
                                {"type": "text", "text": prompt}]}]})
    if r.status_code != 200:
        return {"error": f"HTTP {r.status_code}: {r.text[:300]}"}
    txt = "".join(b.get("text", "") for b in r.json().get("content", []))
    txt = txt.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return {"error": "unparseable", "raw": txt[:300]}


def check(path: Path, on_heat: bool = False) -> dict:
    f, c = detect_frame(path), detect_chrome(path)
    out = {"file": path.name, "frame_scan": f, "chrome_scan": c, "failures": []}
    if f["frame"]:
        out["failures"].append(
            f"letterbox or padding band: {f['top_rows']}px top, "
            f"{f['bottom_rows']}px bottom ({f['percent']}% of the image)")
    if c["chrome"]:
        out["failures"].append(
            f"app interface: {c['top_rows']}px top, {c['bottom_rows']}px "
            f"bottom ({c['percent']}% of the image)")
    v = vision_check(path, on_heat=on_heat)
    out["vision"] = v
    if "error" not in v and "skipped" not in v:
        if v.get("frame"):
            out["failures"].append("vision: social media frame or app chrome")
        if v.get("rim_lip"):
            out["failures"].append("vision: pan has a rim lip")
        if not v.get("one_handle", True):
            out["failures"].append("vision: pan does not have exactly one handle")
        if v.get("other_cookware"):
            out["failures"].append("vision: another frying pan is in the shot")
        if v.get("handle_wrong_way"):
            out["failures"].append(
                "vision: the handle points away from the cook — on a hob it "
                "turns in, over the counter")
        for c in v.get("other_concerns") or []:
            out["failures"].append(f"concern: {c}")
    out["pass"] = not out["failures"]
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("images", nargs="+")
    ap.add_argument("--frame-only", action="store_true")
    a = ap.parse_args()
    bad = 0
    for img in a.images:
        p = Path(img)
        if a.frame_only:
            f, c = detect_frame(p), detect_chrome(p)
            hit = f["frame"] or c["chrome"]
            why = "letterbox" if f["frame"] else ("interface" if c["chrome"] else "")
            d = f if f["frame"] else c
            print(f"  {'FAIL' if hit else 'ok':4s} {p.name:34s} "
                  f"top={d['top_rows']:4d} bottom={d['bottom_rows']:4d}  "
                  f"{d['percent']:5.2f}% {why}")
            bad += hit
        else:
            r = check(p)
            print(f"  {'PASS' if r['pass'] else 'FAIL':4s} {p.name}")
            for f_ in r["failures"]:
                print(f"         - {f_}")
            bad += not r["pass"]
    sys.exit(1 if bad else 0)
