# IronRoot — Content QC Gate (mandatory, every asset, every week)

*No asset is saved to `content/weekly/` or shown for approval until it passes every check below at FULL resolution. Created July 2026 after the week-of-Jul-6 batch shipped a water test with chrome balls instead of water and a testimonial pan with two handles.*

---

## 1. Product ground truth (check against these reference photos)

Reference files in `content/images/reference/` (see its README):
- **`PRIMARY_pan_studio_2048.jpg` — THE reference to attach (Umer, 3 Sep 2026).** 2048x2048 studio shot,
  whole pan, clean white background; verified at full res: no rim lip, correct slim handle, splayed fork,
  2 dome rivets, satin body.
- `H139cfe9712a64fd194516f7f9598fdb07.jpg` — lifestyle on wood (secondary)
- `71mmlIaw10L._AC_SL1000.jpg` — top-down 3/4 on gray fabric
- `ic5.jpg`, `ic7.jpg` — real customer photos

**WARNING:** several photos in `content/images/scraped/` show a DIFFERENT variant pan
(rim lip + slimmer handle): `61B8O9tbT5L`, `71uzNinbM5L`, `71Gr-_Gs6PL`, `91ql3nHTu9S` and similar.
Never use them as the pan reference — this caused the 13-Jul-2026 rework.

> **CORRECTED 31 Aug 2026.** The previous wording — *"droplet/bulb profile (widest near the end)"* and
> *"never a slim straight handle"* — described the DEFECT, not the pan. It steered generation into the
> wrong handle and then passed it at QC (see `qc_regression/`). The real handle IS slim.
>
> **Shape is specified by the photographs below. Prose says what to check; it never says what the shape is.**

**The real pan:**
| Feature | Spec |
|---|---|
| Handles | **ONE** long handle. Never two. Never a helper handle. |
| Handle shape | **Slim, long, gently tapering.** Flat in profile, swelling only slightly past the midpoint. NEVER chunky, hourglass or bulbous. |
| Handle fork | **Long, flat, SPLAYED Y-fork** with a long narrow slot where it meets the body — never a short thick fork |
| Handle hole | Small hole at the **very tip** |
| Finish | **Satin throughout — body AND handle.** (Umer, 3 Sep 2026, from the real pan. Supersedes the 31 Aug "shiny handle" note.) `reference/71mmlIaw10L` is a retouched listing shot whose mirror-look handle is NOT the real finish — use it for SHAPE only, never for finish. Trust `ic5`/`ic7`. |
| Rivets | Two dome-head rivets visible on the inside wall at the handle |
| Interior | Satin stainless, concentric circular grain |
| Rim | **Plain stainless. NO copper/orange/brass accent line.** (Known model drift — Nano Banana keeps adding a copper rim. Reject on sight.) |
| Walls | Flared, no straight sides, no pour spouts, no lid |
| Rim edge | **NO lip / rolled edge** — the wall ends in a plain straight-cut edge (reject any rolled or flared lip) |
| Coating | None — surface must read as bare steel, never dark/non-stick |

## 2. Generation rules (before anything is made)

1. **Never free-generate the pan.** Every image starts from the reference photos above via image *editing*.
   Attaching a reference is necessary but **NOT sufficient** — it biases the model, it does not constrain it.
   The July assets were all generated with the canonical photo attached and still came out wrong. So also:
   - **Attach several references, not one** — full pan, plus close crops of the handle, the fork and the rim edge (the three features that drift).
   - **Match the reference angle to the shot.** Never ask for a vertical hanging composition from a top-down reference — unseen geometry gets invented, and invention is where the wrong handle comes from.
   - **Never let prose contradict the photo.** If the text and the reference disagree, the text tends to win. That is exactly what went wrong in July.
   - **Prefer preservation over regeneration.** Where the composition allows, mask the pan and regenerate only around it, or composite the real pan pixels into a generated scene. Then fidelity is guaranteed by construction rather than hoped for.
1b. **PREFERRED METHOD (Umer, 3 Sep 2026 — tested and working): subject placement, not photo editing.**
   Attach `PRIMARY_pan_studio_2048.jpg` and instruct the model to *place that pan into a scene it composes around it*,
   describing ONLY the setting — never the pan. The model handles scale, angle and perspective itself.

   Template: `"Use this frying pan in the image, then create an image for <platform> where <scene>.
   The setting is <mood, palette, lighting>."`

   Worked example: *"Use this frying pan in the image and then create an image for instagram where the
   pan is being used by a chef at home. The setting of the home is cozy but dark, with brown, black,
   cream shades."*

   **The prompt must contain ZERO description of the pan's shape, finish or features.** Describing the pan
   is what caused the July defects — the photo is the specification. If a QC failure recurs, the fix is a
   better or better-angled reference photo, never more adjectives.

   Note this is still generation, not compositing: the model re-renders the pan, so QC at full resolution
   remains mandatory. It removes the prose-vs-photo conflict; it does not remove drift.

2. **No physics demonstrations, ever.** Water tests, oil behavior, sizzle-droplet effects — models fake these badly and the stainless audience will spot it. Physics demos are filmed on a phone with the real pan or not made at all.
3. **No AI humans presented as customers.** AI people may appear ONLY in clearly non-testimonial lifestyle contexts, must be disclosed with the platform's AI label, and never speak "as a customer."
4. **No invented quotes, reviews, or numbers.** Social proof uses verbatim text from real verified reviews only.
5. **Deterministic where possible.** Quote cards, text overlays, and simple composites are built with code (PIL), not generated — zero drift risk.

## 3. Per-asset checklist (run at 100% zoom; videos: check first, middle, last frames)

**Product fidelity**
- [ ] Exactly one handle; slim tapering shape, long splayed fork, hole at the very tip; handle reads shiny, body satin
- [ ] Two rivets, correct position (not three, not zero, not inside floor)
- [ ] Rim is plain stainless — no copper line
- [ ] Interior grain looks brushed/concentric, not mirror or coated
- [ ] Pan proportions match reference (not a wok, not a saucier)

**Physics & plausibility**
- [ ] Water looks like water (translucent, irregular, flattened) — never metallic spheres
- [ ] Steam/smoke rises plausibly; oil pools flat; food contact shadows exist
- [ ] Hands: 5 fingers, correct grip, one thumb
- [ ] Appliances correct: induction hob = flat black glass, cross/plus zone markings only — NO coil graphics, no glowing rings

**Integrity & compliance**
- [ ] Visible Gemini sparkle watermark REMOVED before sign-off (standing instruction, Umer 13 Jul 2026): locate at bottom-right (check all corners), remove via alpha-unblend/inpaint from the pristine original, verify zero residue at 100% zoom. The invisible SynthID mark stays embedded and the platform AI label is STILL required — removal never waives disclosure.
- [ ] Photorealistic AI people → platform "AI-generated" label required at posting
- [ ] Any quote traceable to a named, real, verified review
- [ ] No claim in the caption the image can't support (oven temp, "chef-grade", etc.)

**Technical**
- [ ] Correct aspect ratio for slot (4:5 feed, 9:16 reels/TikTok)
- [ ] No mangled text/logos anywhere in frame (check pans, labels, appliances)
- [ ] Video: no morphing between frames (handle count stays 1 for every sampled frame)
- [ ] Video AUDIO continuity: when cutting from multiple sources, the soundtrack must be consistent across
      every cut — no music appearing/disappearing between segments (found in the first post5 cut: source A had
      baked-in music, source B didn't). Fix: replace the full track with one continuous music bed (+ fade-out),
      or strip music entirely. Listen to the whole clip (or run volumedetect per segment) before sign-off.

## 4. Verdict rules

- Any single product-fidelity failure → **reject, regenerate**. Never "fix in caption."
- Two failed generations of the same concept → **change concept** (the model is telling you it can't do it).
- A physics-demo asset that "looks pretty good" → **still reject.** Pretty-good physics is the uncanny valley that gets roasted in comments.
- Every batch review happens on the actual full-res file, not the chat thumbnail.

## 5. Sign-off record

Each weekly `captions.md` must end with a QC block per asset:
```
QC: post2_product_steak.png — PASS (1 handle, 2 rivets, no copper rim, no watermark, 4:5) — checked 2026-07-07
```
No QC block = not ready for Telegram approval.
