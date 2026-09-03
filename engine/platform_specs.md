# Platform specs — sizes, exports, cadence

*Gap found 31 Aug 2026: every July asset was a single 4:5 master pushed to all three image platforms.
Correct for Instagram, acceptable for Facebook, **wrong for Pinterest.* The fix costs no extra
generation — one high-res master per concept, then programmatic reframes.*

---

## 1. One master, many crops

Generate **one** high-resolution master per concept. Everything below is a deterministic reframe and
export from that master — never a second generation.

| Output | Ratio | Pixels | Used by |
|---|---|---|---|
| Feed | 4:5 | 1080 × 1350 | Instagram feed, Facebook feed |
| Pin | **2:3** | 1000 × 1500 | Pinterest |
| Vertical | 9:16 | 1080 × 1920 | Reels, Stories, TikTok |

Compose the master with headroom on all four sides so a 2:3 and a 9:16 crop can both be taken
without cutting the pan.

**Export:** sized sRGB JPEG, quality ~88 — not the raw 5–7 MB PNG. Platforms recompress hard;
handing them an oversized file makes the result worse, not better.

---

## 2. Why Pinterest matters more than it has been treated

2:3 is Pinterest's native ratio; a 4:5 pin displays smaller and gets cropped. More importantly a pin
keeps working for **months** while a feed post dies in a day — and for a $79 buy-it-for-life pan the
search intent on Pinterest is the highest of any channel here. Give it a text overlay on the pin and
a keyword-led description.

---

## 3. Platform behaviours

- **TikTok** — hook on screen in the first 1–2 seconds, on-screen text throughout, trending sound
  chosen in-app. Supplier music is a safe default, not a good one. 15–45 s.
- **Instagram** — Reels out-reach feed images. Carousels are unused so far and worth testing once
  there is a baseline. Stories can carry poll stickers ("does your pan have PFAS?").
- **Facebook** — mirror Reels as **native uploads**, never links to Instagram. One link post a week.
- **Pinterest** — evergreen, keyword-led, text on the pin.

---

## 4. Video

9:16, 1080 × 1920. Real supplier footage wherever physics is shown. Single continuous music bed with
an end fade — never music appearing or disappearing between cuts (this shipped as a defect once;
check with `ffmpeg volumedetect` per segment before sign-off).

---

## 5. Cadence — OPEN ITEM, needs Umer's call

The two source documents disagree and this has never been settled:

| Source | Instagram | Facebook | Pinterest | TikTok |
|---|---|---|---|---|
| `strategy/IronRoot_Marketing_Strategy.md` (Jun) | 5 /wk | 4 /wk | — | 4 /wk |
| `automation/content_engine_plan.md` v2 (Jul) | 4 /wk | 4 /wk | 4 /wk | 2 /wk |

**Default until decided: the v2 numbers** — 4 pillar posts mirrored to Instagram, Facebook and
Pinterest, plus 2 TikToks. It is the more recent document and the lower, more sustainable volume for
a first month with zero existing presence.

Day-of-week distribution follows the strategy calendar: education Monday, product Tuesday and
Wednesday, proof Thursday, lifestyle Friday, education Saturday.
