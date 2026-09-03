# IronRoot — Full Marketing & Automation Strategy
*Target market: USA | Budget: €300/month Meta ads | Updated: June 2026*

---

## 1. Brand Positioning

**Core angle:** PFAS-free is your unfair advantage. Every piece of content and every ad should lead with health safety, not cookware features.

**Primary headline:** *"Your non-stick pan has PFAS. IronRoot doesn't."*

**Secondary headline:** *"The last pan you'll ever buy."*

**Target customer:** Health-conscious US home cooks, ages 28–50, interested in clean eating, organic living, home improvement. Slightly female-skewed (60/40) but both genders respond to the health angle. Household income $60k+. Likely already paying attention to food quality, ingredients, and what goes into their body.

**Competitive angle:** You're not competing on price with cheap pans. You're competing with Made In ($99–149), Misen ($85), and Caraway ($145) — and you win on PFAS-free stainless steel at $79 with a 30-day guarantee. That is a compelling offer if you can get people to trust the brand.

---

## 2. Content Strategy

### Content Pillars (4 types, rotated weekly)

**Pillar 1 — Education / Fear Hook (40% of posts)**
Goal: make people realise their current pan is a problem.
- "What happens when you scratch a Teflon pan" 
- "The EPA just banned 7 PFAS chemicals. Here's what that means for your kitchen."
- "Why we cook with stainless steel, not non-stick"
- "3 signs it's time to throw away your pan"
- "PFAS in cookware: what the research says"

**Pillar 2 — Product in Action (30% of posts)**
Goal: show the pan performing beautifully. Appetite appeal.
- Sizzling steak hitting the pan (audio on)
- Eggs sliding around in stainless steel (no-stick technique)
- Pan going from stovetop directly into oven
- Close-up of the tri-ply base
- One-pan dinner from start to finish

**Pillar 3 — Social Proof (15% of posts)**
Goal: borrowed credibility.
- Screenshot customer reviews with product shot
- "What our customers say" carousel
- Before/after ("switched from Teflon, here's what happened")
- Milestone posts ("1,000 pans shipped 🎉")

**Pillar 4 — Lifestyle / Brand (15% of posts)**
Goal: make people want the life, not just the pan.
- Sunday meal prep aesthetic
- Clean kitchen flat-lay with the pan as hero
- "What's for dinner" cooking POV
- Behind-the-scenes of packaging / quality control

---

### Posting Schedule

| Day | Instagram | Facebook | TikTok |
|-----|-----------|----------|--------|
| Mon | Reel (Education) | Education post + store link | Education video |
| Tue | Feed post (Product) | — | — |
| Wed | Reel (Product in action) | Product post | Product video |
| Thu | Story (social proof) | Review post | — |
| Fri | Reel (Lifestyle) | Lifestyle post | Lifestyle video |
| Sat | Feed post (Education) | — | Education video |
| Sun | — | Weekly roundup | — |

**Total per week:** 5 Instagram posts/Reels, 4 Facebook posts, 4 TikTok videos.

---

### Content Formats by Platform

**Instagram**
- Reels: 7–15 seconds, vertical (9:16), hook in first 2 seconds, text overlay, trending audio
- Feed posts: Square (1:1) or portrait (4:5), clean product photography
- Stories: Poll stickers ("Does your pan have PFAS?"), swipe-up to product page

**Facebook**
- Mirror Instagram Reels as native video uploads (not links to Instagram)
- Add a link post 1x/week pointing to the product page
- Use longer captions (Facebook audiences read more than Instagram)

**TikTok**
- Native vertical video, 15–45 seconds
- Hook must be in the first 1–2 seconds on screen
- Trending sounds where relevant
- "Did you know?" and "POV:" formats perform well in the cookware niche
- Post at: 6–9am, 12–3pm, or 7–11pm EST (peak US engagement)

---

## 3. Meta Ads Strategy — €300/month (~€10/day)

### Campaign Structure

```
CAMPAIGN 1: AWARENESS — Top of Funnel (€4/day)
├── Ad Set: PFAS Awareness (USA, 28–55, health/cooking interests)
│   └── Creative: "Your pan has PFAS" hook video (15s)
└── Ad Set: Lifestyle (USA, 28–50, home improvement/cooking)
    └── Creative: Sizzle/cooking lifestyle video (15s)

CAMPAIGN 2: CONSIDERATION — Mid Funnel (€3/day)
└── Ad Set: Retarget 25%+ video viewers (last 30 days)
    └── Creative: Product benefits carousel (PFAS-free, tri-ply, 30-day guarantee)

CAMPAIGN 3: CONVERSION — Bottom of Funnel (€3/day)
└── Ad Set: Retarget website visitors + ATC (last 14 days)
    └── Creative: Direct response — "$79. PFAS-free. 30-day guarantee. Free shipping."
```

### Cold Audience Targeting (Campaign 1)
- Location: United States
- Age: 28–55
- Interests (layer 1): Organic food, clean eating, healthy living, Whole Foods Market
- Interests (layer 2): Home cooking, Food Network, cooking classes, kitchen gadgets
- Interests (layer 3): Le Creuset, All-Clad, Instant Pot, Caraway (competitor targeting)
- Exclude: existing purchasers

### Ad Creative Guidelines
- Every ad starts with a hook in the first 2 seconds (text on screen + voiceover)
- UGC-style (natural, phone-filmed looking) outperforms polished ads in this category
- Always end with the offer: "30-day risk-free trial. Free shipping. $79."
- Use captions/subtitles — 80% of Facebook/Instagram video is watched on mute
- Square (1:1) format for Feed placements, Vertical (9:16) for Stories/Reels

### Monthly Budget Breakdown
| Week | Spend | Focus |
|------|-------|-------|
| Week 1 | €75 | Test 3 creatives in Campaign 1. Identify winner. |
| Week 2 | €75 | Scale winning creative. Launch Campaign 2 (retargeting now has data). |
| Week 3 | €75 | Add Campaign 3 conversion. Pause losing creatives. |
| Week 4 | €75 | Consolidate. Double down on best performer. Review CPM/CTR/ROAS. |

### Key Metrics to Watch
- **CPM** (cost per 1,000 impressions): Target <$15 for cold audiences
- **CTR** (click-through rate): Target >2% for link ads
- **CPC** (cost per click): Target <$1.50
- **ROAS** (return on ad spend): Target >2x once conversion campaign is running
- **Thumb-stop rate** (3-second video views / impressions): Target >30%

---

## 4. Automation Pipeline Architecture

### Overview
```
[YOU] Send photo via Telegram
         │
         ▼
[n8n] Telegram Trigger node receives image
         │
         ▼
[n8n] Download image to local storage / Google Drive
         │
         ▼
[Claude API] Generate platform-specific content:
  • Instagram caption + 10 hashtags
  • Facebook post (longer, with CTA link)
  • TikTok script (hook + body + CTA, 30s spoken)
  • Ad copy variant (short direct response)
         │
         ▼
[n8n] Format approval message + send back to Telegram
  "Here's content for image: [filename]
   📸 INSTAGRAM: [caption]
   📘 FACEBOOK: [caption]
   🎵 TIKTOK SCRIPT: [script]
   📣 AD COPY: [copy]
   
   Reply ✅ to schedule, ✏️ [changes] to revise"
         │
         ▼
[YOU] Reply ✅ in Telegram
         │
         ▼
[n8n] Schedule posts:
  • Instagram + Facebook → Meta Content Publishing API
  • TikTok → TikTok Content Posting API (requires manual upload for now — see note)
         │
         ▼
[n8n] Confirm via Telegram: "✅ Scheduled for [date/time]"
```

### n8n Nodes Required
1. **Telegram Trigger** — listens for messages from your Telegram bot
2. **IF node** — routes based on message type (photo vs text reply)
3. **HTTP Request** — downloads image from Telegram file API
4. **HTTP Request (Claude API)** — sends image + prompt to claude-3-5-haiku for speed/cost
5. **Telegram Send** — sends draft back to you for approval
6. **Wait / Webhook** — waits for your ✅ reply
7. **HTTP Request (Meta Graph API)** — creates media container + publishes to Instagram/Facebook
8. **HTTP Request (TikTok API)** — initiates direct post (see note below)
9. **Telegram Send** — confirmation message

### TikTok Note
TikTok's Content Posting API supports direct video publishing but requires the video file, not just a static image. For photo-based content, the workflow will instead send you a ready-to-post package (video script + suggested audio + the image) so you can record/create the TikTok in under 5 minutes. For video assets (once you have them), direct posting is fully automatable.

### Posting Schedule Logic
When you approve a post, n8n automatically schedules it to the next available slot in the posting calendar (not immediately). This prevents everything going out at once and maintains the rhythm above.

---

## 5. AI Tools for Content Creation

### For Static Image Enhancement
- **Canva API** (or Canva manually): Add text overlays, brand colours, formatted quote cards
- **Adobe Firefly API**: Generative fill to extend backgrounds, add lifestyle context to product shots
- **Remove.bg API**: Auto-remove backgrounds for clean product-only shots

### For Video Generation from Images
- **Runway Gen-3 Alpha** (runway.ml): Animate a static product image into a 4-second clip (sizzle effect, subtle motion). ~$0.05/second generated.
- **Pika 2.0** (pika.art): Similar to Runway, good for "bring image to life" motion. Has a free tier.
- **Kling AI**: Strong for realistic food/cooking motion from stills.

### Recommended Starting Stack
For phase 1 (first 4–6 weeks), keep it simple:
1. Use scraped images as-is for static Instagram/Facebook posts
2. Use Claude API for all captions and scripts
3. Create TikTok videos manually using the generated script + your phone (5 min/video)
4. Add Runway/Pika once you have the n8n pipeline running smoothly

---

## 6. Folder Structure (this project)

```
IronRoot/
├── strategy/
│   └── IronRoot_Marketing_Strategy.md   ← this file
├── content/
│   ├── images/
│   │   └── scraped/                     ← 15 product images from store
│   ├── videos/                          ← generated/recorded videos
│   ├── captions/                        ← weekly caption batches
│   └── ads/                             ← Meta ad copy + creatives
└── automation/
    ├── n8n_workflow.json                ← importable n8n workflow
    └── n8n_setup_guide.md               ← step-by-step setup instructions
```

---

## 7. Launch Sequence (First 30 Days)

**Week 1: Fix & Foundation**
- [ ] Fix `support@ironroot.com.co` on product page
- [ ] Fix language issue (Dutch showing to US visitors)
- [ ] Run `download_images.py` to pull all store photos
- [ ] Set up Telegram bot + connect to n8n
- [ ] Connect Instagram + Facebook to Meta Graph API
- [ ] Generate first 2 weeks of captions (done — see `content/captions/`)

**Week 2: Organic Launch**
- [ ] Post first content batch across Instagram + Facebook
- [ ] Set up TikTok account (username: @ironrootpan or similar)
- [ ] Test Telegram → n8n → Meta posting pipeline end-to-end
- [ ] Post manually on TikTok using generated scripts

**Week 3: Paid Launch**
- [ ] Set up Meta Business Manager + Pixel on the store
- [ ] Launch Campaign 1 (awareness) with 2 test creatives
- [ ] Monitor CPM + thumb-stop rate daily
- [ ] Identify winning creative by day 5

**Week 4: Optimise**
- [ ] Scale winning creative in Campaign 1
- [ ] Launch Campaign 2 (retarget video viewers)
- [ ] Review all organic content performance
- [ ] Brief second batch of content for weeks 5–8
