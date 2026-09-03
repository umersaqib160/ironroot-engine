# Video strategy

## Recommendation: no AI video generation, at least not yet

Veo-style generation from a seed image is available and would be the obvious
choice. I think it is the wrong one right now, for three reasons that are
specific to this project rather than general caution:

1. **Fidelity risk multiplies across frames.** It took eleven generations and
   three corrective constraints to get one still with the right pan. A video is
   hundreds of frames, and the failure mode in motion is *morphing* — a handle
   that grows a second handle halfway through a pan. The July TikTok needed a
   frame-by-frame handle count at 1fps to catch exactly that.
2. **QC gets much harder and slower.** A still is one full-resolution check. A
   clip needs sampled frames, plus audio continuity.
3. **Cost.** Roughly $0.10 per second of 720p — about $1–2 a clip, against
   near-zero for the two options below.

## What we do instead — both already proven here

### 1. Photo-swipe from approved stills (ffmpeg)

Take the QC-passed stills for the week, add slow pushes and crossfades, cut to a
single continuous music bed with an end fade. Deterministic: **if the stills
passed QC, the video cannot introduce a new defect**, because there are no new
pixels of the pan. This is what `post5_tiktok_photoswipe` did in July.

### 2. Real supplier footage cuts (ffmpeg)

51 MB of real footage already sits in `content/videos/`. Zero AI, zero fidelity
risk, and the only honest way to show physics — water beading, oil, sizzle —
which `QC_process.md` forbids generating. `post6_tiktok_preheat` was cut this way
in July and **passed QC on the first attempt**, the only asset that ever did.

## Weekly output

| Slot | Source | AI label |
|---|---|---|
| TikTok 1 | photo-swipe of that week's approved stills | ON (stills are AI-edited) |
| TikTok 2 | supplier-footage cut | OFF (no AI) |

Both are 9:16, 1080x1920, single continuous music bed with an end fade — verified
per segment with `ffmpeg volumedetect`, because music appearing and disappearing
between cuts shipped as a defect once already.

## When to revisit

Once the still pipeline has produced four consecutive clean weeks, a *single*
Veo clip is worth one controlled test, QC'd frame by frame, on a scene with no
physics in it. Not before. Motion is a luxury; a pan with two handles at 0:07 is
the same credibility problem as one in a photograph, only harder to spot.
