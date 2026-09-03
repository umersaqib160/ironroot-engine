# IronRoot — brand brief

*The single document the weekly generator reads before planning anything. Distilled from
`strategy/IronRoot_Marketing_Strategy.md` (Jun 2026) and `automation/content_engine_plan.md` (v2,
10 Jul 2026). If those and this disagree, this file wins for content generation.*

---

## 1. Positioning

**The angle: PFAS-free is the unfair advantage.** Lead with health safety, not cookware features.

- Primary: *"Your non-stick pan has PFAS. IronRoot doesn't."*
- Secondary: *"The last pan you'll ever buy."*

**Customer:** health-conscious US home cooks, 28–50, into clean eating and organic living. Skews
60/40 female but the health angle lands with both. Household income $60k+. Already paying attention
to what goes into their body.

**Competitive set:** Made In ($99–149), Misen ($85), Caraway ($145). IronRoot wins on PFAS-free
stainless at **$79** with a 30-day guarantee. Not competing on price with cheap pans — competing on
trust with premium ones.

**Voice (locked):** chemical-free / PFAS-free · durability · *a pan for life*.
Direct, plain, confident. No hype, no exclamation marks, no invented urgency.

---

## 2. The four pillars

| Pillar | Share | Goal | Examples |
|---|---|---|---|
| **1. Education / hook** | 40% | make people realise their current pan is a problem | what happens when you scratch Teflon · the EPA PFAS bans · why stainless, not non-stick · 3 signs to bin your pan |
| **2. Product in action** | 30% | show the pan performing; appetite appeal | steak hitting the pan · eggs not sticking · stovetop to oven · tri-ply base · one-pan dinner |
| **3. Social proof** | 15% | borrowed credibility | verbatim real reviews on real photos · switched-from-Teflon stories · shipping milestones |
| **4. Lifestyle / brand** | 15% | make people want the life, not the pan | Sunday meal prep · clean kitchen flat-lay · what's-for-dinner POV · packaging and QC |

---

## 3. Visual style

**The pan** is specified by `content/images/reference/PRIMARY_pan_studio_2048.jpg`. Never described
in words. See `prompts/image_scene.md`.

**The scene** is the only thing the prompt describes:

- **Mood:** cozy but dark. Warm, lived-in, a real home rather than a showroom.
- **Palette:** brown, black, cream. Warm amber from the cooking itself.
- **Light:** directional and soft — window light, a lamp, the hob. Deep shadows are wanted.
- **Framing:** the pan is the hero, in use or at rest. Real kitchens, real wear, real food.
- **Avoid:** flat bright studio light, cold blue-white kitchens, clutter that competes with the pan,
  anything that reads as stock photography.

---

## 4. Variety rule

Read the previous **two** weekly `captions.md` files before planning. No repeated concept, scene,
food, or hook across a rolling three-week window. Rotate the food, the time of day, the kitchen, and
the camera distance — not just the caption.

Two failed generations of the same concept → **change the concept.** The model is telling you it
can't do that one.

---

## 5. Claims discipline — non-negotiable

- **No invented reviews, quotes, numbers or milestones.** Social proof uses verbatim text from real
  verified reviews only, and the review must be checked in the store admin before it is used.
  (The site currently displays inflated review counts — 29,000 / 2,000+ against ~27 real. Content
  must never repeat those figures.)
- **No claim the image cannot support** — oven temperatures, "chef-grade", performance figures.
- **No AI humans presented as customers.** AI people may appear only in clearly non-testimonial
  lifestyle contexts, with the platform AI label on, and never speaking as a customer.
- **No AI-generated physics demos** — water tests, oil behaviour, sizzle droplets. Models fake these
  badly and a stainless audience spots it instantly. Physics is filmed on a real pan or not shown.
- Every AI-edited asset carries the platform **"AI-generated" label**. SynthID stays embedded.

---

## 5b. Benefit claims — what may and may not be said

Verified against the live product page and the 27 real reviews, 3 Sep 2026.

| Claim | Status | Basis |
|---|---|---|
| PFAS / PFOA free | **Say it** | product description, the core positioning |
| Tri-ply stainless, even heat | **Say it** | product description + reviews |
| Oven safe to 500F | **Say it** | product SEO description |
| **Dishwasher safe** | **Say it** | product SEO description; bundle description |
| **Easy to clean** | **Say it** | real reviews (Magnus B, Jeroen K) |
| Works on all cooktops incl. induction | **Say it** | product title tag + review (Jeroen K) |
| Handle stays cool | Say it, carefully | one review (Thomas R) — attribute, do not generalise |
| **No coating to ruin — scrub it** | **Say it** | follows from "free of chemical coatings"; the durability angle |
| **NON-STICK** | **NEVER** | see below |

### Never claim non-stick

Bare stainless is not non-stick. The product page does not claim it, and the
brand's entire position is *no chemical coatings* — so a non-stick claim
contradicts the thing being sold. The target audience is stainless-literate and
will say so in the comments, and any customer who skips the preheat will ask for
a refund.

The honest version is stronger: **technique.** Preheat the empty pan, then the
fat, then the food, and eggs release cleanly with no coating involved. That is
already how the July education post framed it, and a real review supports the
outcome — Lotte M: *"finally fry perfectly without sticking."*

Show eggs releasing. Never call the pan non-stick. The image does the work — a
chef frying eggs in bare steel signals it to anyone who knows how, and the people
who know are the ones worth convincing.

### The durability angle is the sharper version of "easy to clean"

Two different messages, two different scenes, do not mix them:

- **`bd_easy_clean`** — rinses clean under the tap. Everyday convenience.
- **`bd_durability_scrub`** — scoured hard with a metal pad. This one leads with
  the contrast: do that to a non-stick pan and it is finished. Bare stainless has
  nothing to scratch off, so a burnt-on mess is a scrub rather than a
  replacement. It is the buy-it-for-life argument made physical, and it turns the
  absence of a coating from a health claim into a practical one.

## 6. What the brand is not

Not a lifestyle influencer brand, not a bargain brand, not a gadget brand. One product, one promise:
a pan that won't poison you and won't wear out. Everything else is in service of that.
