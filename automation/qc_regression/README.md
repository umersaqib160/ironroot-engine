# QC regression set

Known-bad assets the automated QC gate MUST reject before it is trusted (Phase 3 of
`../cloud_migration_plan.md`). Every one of these was signed off as PASS by the July process.

| Evidence | Asset | Defect | July verdict |
|---|---|---|---|
| `handle_canonical_vs_july.png` | `2026-07-13/post2_product_eggs.png` | **Wrong handle** — chunky sculpted bulb, short thick fork | "PASS v3" |
| `handle_canonical_vs_july.png` | `2026-07-13/post4_lifestyle_hanging.png` | **Wrong handle** — same defect, different angle (never flagged) | "PASS v3" |
| `rim_canonical_vs_july.png` | `2026-07-13/post4_lifestyle_hanging.png` | **Rolled lip** on the rim + rim-specific warm cast | "PASS v3" |
| (earlier) | `2026-07-06/rejected_v1/*` | chrome-ball water test, two-handled pan | rejected by Umer |

## Measured rim check — use this, not "does it look coppery"

Absolute warmth is useless because the scenes are warmly lit. Compare the **rim against the pan's own
interior in the same image**, which controls for lighting:

| Image | rim R−B | interior R−B | differential | verdict |
|---|---|---|---|---|
| Real pan (71mmlIaw10L) | +6.7 | −0.5 | **+7.2** | baseline — real steel is near-neutral (sat 4%) |
| July eggs | +57.9 | +80.1 | **−22.2** | rim not warmer than interior → warm light, PASS |
| July hanging | +69.2 | +48.6 | **+20.5** | ~3x baseline, +8.3pp saturation → FAIL |

## Root cause of the handle defect — the written spec is wrong

`content/images/reference/README.md` and `QC_process.md` describe the handle as a
*"droplet/bulb profile (widest near the end)"*. The real pan — see both real photos in
`handle_canonical_vs_july.png` — has a **slim, long, gently tapering** handle with a **long flat splayed
Y-fork** and a **small hole at the very tip**.

The prose spec describes the defect. The model followed the text, drew a bulbous handle, and the QC
checklist — which recites the same wrong text — passed it. **The written spec has been steering
generation into the error and then validating it.**

### Correction — CONFIRMED by Umer, 31 Aug 2026 (applied to QC_process.md and reference/README.md)

| Feature | Old wording (wrong) | Corrected |
|---|---|---|
| Handle profile | "droplet/bulb, widest near the end" | **slim and long**, gently swelling past the midpoint, never chunky or hourglass |
| Y-fork | "Y-fork where it meets the body" | **long, flat, splayed** fork with a long narrow slot — not a short thick fork |
| Hole | "small teardrop hole at the tip" | correct — small, at the **very tip** |
| Finish | "brushed" | **RESOLVED by Umer 3 Sep 2026: satin throughout, body AND handle.** The listing shot is retouched toward mirror — shape reference only. |

**Rule that follows from this:** shape is specified by *photographs*, never by adjectives. Prose may say
what to check, never what the shape is.

## Why "just attach the reference photo" is not the whole fix

Every July asset **was** generated with the canonical reference attached, and they still came out wrong.
Attaching a reference **biases** the model; it does not **constrain** it. Three reasons it got diluted:

1. **The prose fought the photo.** The prompt carried "droplet/bulb handle, widest near the end" alongside
   the correct photo. When text and image disagree, the explicit text instruction tends to win.
2. **The angle didn't match.** A hanging vertical composition asked from a top-down reference forces the
   model to invent the unseen geometry — and invention is where the generic cookware handle appears.
3. **The reference gets outweighed.** Every extra styling clause (scene, mood, lighting, food) dilutes the
   reference's pull on the output.

Ranked by how strongly each actually binds the result:

| Approach | Binding strength |
|---|---|
| Reference attached + contradicting prose | weak — this is what failed in July |
| Reference attached + corrected prose | better |
| Several references incl. handle/fork/rim crops, angle-matched to the shot | better still |
| **Mask the pan, regenerate only around it** | strong — pan pixels preserved by construction |
| **Composite real pan pixels into a generated scene** | strong — the pan is a photograph |
| **Photograph the real pan** | total — nothing to get wrong |
