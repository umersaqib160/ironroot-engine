# IronRoot — Cloud Migration Plan (v1, 31 Aug 2026)

*Goal: the weekly content engine runs itself, every Monday, with Umer's PC switched off.
Approval happens from a phone. Nothing in the pipeline depends on a logged-in Chrome session.*

Supersedes the execution half of `content_engine_plan.md` (v2, 10 Jul 2026).
The strategy half of that document — pillars, cadence, voice — stays authoritative.
`QC_process.md` stays authoritative in full, with one deletion noted in §4.

---

## 1. Why we are migrating

The v2 engine works, but it has three hard dependencies on Umer's desktop:

1. **Image/video generation** drives `gemini.google.com` through Claude-in-Chrome.
2. **Publishing** drives Meta Business Suite / Pinterest / TikTok schedulers through the same Chrome.
3. **Approval** happens inside a desktop Claude session.

Result: the PC must be on, awake, logged in and unattended-safe at 08:00 every Monday.
It has not been, and the engine has produced nothing since **17 July 2026 — six missed weeks**.

**Confirmed 31 Aug 2026:** the 6 Jul and 13 Jul bundles were **never posted** — the socials were never
connected, and there was never time to post by hand. So the accounts have **zero organic presence**.

**And that turned out to be lucky.** On review (31 Aug) the July assets are *defective*, despite carrying
"PASS v3" QC sign-offs: both images render the **wrong handle**, and the hanging shot has a **rolled rim
lip** the pan does not have. Evidence and measurements: `automation/qc_regression/`.

They are therefore **not a launch backlog — they are the regression set.** Nothing from July gets posted.

**Finding (31 Aug 2026):** moving the run into Claude's own cloud environment does *not* fix this
on its own. That environment sits behind a strict egress allowlist — package registries and GitHub
only. Verified blocked: `generativelanguage.googleapis.com`, `aiplatform.googleapis.com`,
`graph.facebook.com`, `api.pinterest.com`, `open.tiktokapis.com`.

So the migration is not "move to Claude Code." It is **move the pipeline to a runner that is always
on and allowed to reach the internet**, and swap browser automation for APIs.

---

## 2. Target architecture

```
GitHub repo (private)  ──  ironroot-engine
│
├── Monday 08:00 CET ── scheduled workflow: GENERATE
│     ├── read last 2 weekly bundles (avoid repeats)
│     ├── Claude plans 4 pillar posts + 2 TikTok formats
│     ├── Gemini API edits images from canonical references
│     ├── ffmpeg cuts video · PIL builds review cards
│     ├── Claude runs the QC gate on full-res output, re-rolls failures
│     └── opens a GitHub Issue: assets embedded + captions + QC block
│
├── Umer's phone ── GitHub notification → look → comment "approve"
│                                              or "redo 2 — darker"
│
└── on issue comment ── workflow: PUBLISH
      ├── Instagram  → Graph API (scheduled)
      ├── Facebook   → Graph API (scheduled)
      ├── Pinterest  → Pinterest API
      └── TikTok     → Content Posting API (private draft — see §7)
```

**Why GitHub Actions rather than a server or Claude Code on a VPS:**

- Free for this workload; no machine to patch, pay for, or watch fall over.
- `cron:` scheduling and encrypted secrets are built in.
- Every run leaves logs, so a silent failure is visible instead of invisible.
- The repo doubles as the asset store and the repeat-avoidance memory.
- A VPS running Claude Code is a valid alternative but adds sysadmin work for no gain here.

**Where Claude fits:** the mechanics (API calls, ffmpeg, PIL) are plain Python and need no model.
Claude is called for the two things that are actually judgment: **planning the week's concepts**
(varied, non-repeating, on-brand) and **running the QC gate** on the rendered output, including the
decision to re-roll or change concept.

---

## 3. What transfers, what gets rebuilt

### Transfers unchanged — the valuable 70%

| Asset | Destination in repo |
|---|---|
| `QC_process.md` (the whole gate) | `engine/qc/QC_process.md` — becomes the QC prompt + assertions |
| `content/images/reference/` (canonical set, 820 KB) | `assets/reference/` — the ground truth, unchanged |
| `content/videos/` supplier footage (51 MB) | `assets/video/` — real-footage source for TikToks |
| Past weekly bundles (`2026-07-06`, `2026-07-13`) | `content/weekly/` — feeds repeat-avoidance |
| Brand voice: chemical-free · durability · a pan for life | `engine/brand.md` |
| Locked visual style (dark, cinematic, chiaroscuro, amber) | `engine/brand.md` |
| Content-variety rule (July 2 directive) | `engine/brand.md` |
| Pillar mix + posting cadence | `engine/brand.md` |
| Six weeks of prompt learnings | prompt templates in `engine/prompts/` |

Repo total ≈ 190 MB. Comfortably inside GitHub's limits; no file near the 100 MB cap.

### Rebuilt — the plumbing

| Was | Becomes | Notes |
|---|---|---|
| Gemini web app via Chrome | Gemini API (`gemini-3-pro-image`) | Reference photo attached as image input; same prompts |
| Veo via Chrome "Create video" | Veo via API | Seed image + motion prompt, same as now |
| `.tmp` download race in Downloads folder | direct API response bytes | **This whole class of bug disappears** |
| Watermark alpha-unblend + inpaint | *deleted* | API output carries no visible sparkle mark |
| Meta Business Suite Planner via Chrome | Graph API scheduled publish | |
| Pinterest scheduler via Chrome | Pinterest API | |
| TikTok web scheduler via Chrome | Content Posting API | see §7 — partial |
| Approval in desktop session | GitHub Issue comment from phone | |

---

## 3b. Per-platform fit — a real gap in the current engine

**Captions: already correct.** Every weekly `captions.md` carries genuinely distinct Instagram,
Facebook, Pinterest and TikTok variants — different length, different register, Pinterest keyword-led.
That part transfers as-is.

**Assets: not correct.** Every image made so far is a single 4:5 master pushed to all three image
platforms:

| Asset | Actual | IG feed | FB feed | Pinterest |
|---|---|---|---|---|
| July images (8 of 8) | 4:5 — 1856×2304 / 1600×2000 | correct | fine | **wrong** |
| July videos (3 of 3) | 9:16 — 1080×1920 | correct (Reels) | fine | — |

Pinterest's native ratio is **2:3** (1000×1500). A 4:5 pin displays smaller in the feed and gets cropped
in places — and Pinterest is arguably the *highest-intent* channel for a $79 buy-it-for-life pan, so it
is the worst one to treat as an afterthought. There is also no export step at all: 5–7 MB PNGs are handed
straight to platforms that will recompress them hard.

**The fix is cheap and deterministic — no extra generation cost.** One high-res master render per concept,
then programmatic reframes and exports:

- **4:5** → Instagram feed, Facebook feed
- **2:3** → Pinterest (reframed from the same master, not regenerated)
- **9:16** → Stories / Reels / TikTok
- export sized sRGB JPEG per platform rather than the raw PNG

Beyond aspect ratio, three platform behaviours the engine should respect:

- **TikTok** — hook inside the first 1–2 seconds, on-screen text, and a trending sound chosen in-app.
  Supplier music is a safe default, not a good one.
- **Pinterest** — a text overlay on the pin and a keyword-led description; pins keep working for months,
  unlike a feed post, so this is compounding rather than disposable content.
- **Instagram** — Reels out-reach feed images, and carousels are not being used at all. Worth testing
  once there is any baseline to measure against.

## 3c. Why the QC gate failed — and what replaces it

The July assets were checked against `QC_process.md` and signed off. They are still wrong. The gate did
not fail because the checklist was missing an item; it failed for two deeper reasons, and both must be
fixed before any automated run is trusted.

### Cause 1 — the written spec described the defect

`QC_process.md` and `reference/README.md` describe the handle as a *"droplet/bulb profile (widest near
the end)"*. The real pan has a **slim, long, gently tapering** handle with a **long flat splayed Y-fork**.
The model followed the prose, drew a bulbous handle, and the checklist — reciting the same wrong prose —
confirmed it. The spec was steering generation into the error and then validating it.

**Rule that follows: shape is specified by photographs, never by adjectives.** Prose may say what to
check; it may never say what the shape is. Corrected wording is proposed in
`automation/qc_regression/README.md` for Umer to confirm.

### Cause 2 — the checker was the author

The same context that wrote the generation prompt then "checked" the result against a list it had just
written. That is not a gate, it is a rationalisation. The QC pass must be **adversarial**:

1. **Separate pass, no prompt context.** The checker sees the candidate, the reference photos, and the
   checklist — never the prompt that produced it, and never the claim that it already passed.
2. **Crops, not glances.** Handle and rim are checked as full-resolution crops beside the reference crop,
   the way `qc_regression/*.png` are built. The rim lip is invisible at thumbnail scale and obvious at 100%.
3. **Measure what can be measured.** The copper check compares rim hue against the pan's **own interior
   in the same image**, which controls for warm lighting — absolute warmth is not a usable test. Real
   steel sits near-neutral (saturation ~4%); the July hanging rim ran +20.5 R−B against its own interior,
   ~3x the real pan's baseline.
4. **Regression set.** The gate must reject every asset in `automation/qc_regression/` before it is
   allowed to approve anything new.

### Cause 3 — the model keeps redrawing the pan instead of preserving it

This is the fourth failure of the same class (6 Jul, 13 Jul, 17 Jul, and now this review). Three
escalating options, in order of reliability:

| Option | What it is | Reliability |
|---|---|---|
| Tighten the edit | corrected spec + reference images attached + adversarial QC | better, not solved |
| Composite | generate the scene, then composite **real pan pixels** into it | high — the pan is photographic |
| **Shoot it** | 30–60 min on a phone with the real pan: on the hob, hanging, with eggs | total — no fidelity risk at all |

Umer owns the pan. One short shoot permanently removes this entire class of failure for the *product in
action* and *lifestyle* pillars — the two that keep breaking — and those real frames also become the
seed of `assets/inspiration/`. AI editing then covers only backgrounds, seasonal scenes and variants,
where a mistake is cosmetic rather than a credibility problem.

## 3d. Test runs before anything goes live

Umer's requirement, and the correct one. No content reaches a public account until the engine has proven
itself through four stages:

| Stage | What runs | What is published | Exit condition |
|---|---|---|---|
| **T1 — dry run** | full generate + QC + approval Issue | nothing | 2 consecutive weeks pass QC *and* Umer approves both with no changes |
| **T2 — render test** | one post per platform | posted **private / draft / unlisted**, then deleted | Umer confirms it renders correctly in-feed on each platform |
| **T3 — soft launch** | Instagram only, manually triggered | 1 real post | Umer approves the live result |
| **T4 — live** | full Monday schedule | all platforms | — |

Two standing rules, permanent and not just during testing:

- **Nothing publishes without an explicit approval from Umer.** The automation covers generation,
  QC and scheduling — never autonomous posting. There is no "auto-approve after N hours".
- **A kill switch.** One flag in the repo halts all publishing without touching the generation side.

## 4. Change to the QC gate

One rule is retired: **§3 "Visible Gemini sparkle watermark REMOVED"**. The API returns clean images —
there is no visible mark to remove. The invisible SynthID watermark is still embedded, so the
platform **"AI-generated" label stays ON** for every AI-edited asset. Disclosure is unchanged.

Everything else in `QC_process.md` carries over verbatim and gets *stronger*, because the checks
become automated assertions run on the full-resolution file before an asset is ever shown:

- copper-rim drift → programmatic hue check on the rim region, plus Claude's visual pass
- handle count / rivets / rim lip → Claude vision check against the canonical reference
- audio continuity on cut videos → `ffmpeg volumedetect` per segment, as now
- aspect ratio, resolution, stray text → deterministic checks

The two-strikes rule stands: two failed generations of a concept → change the concept.

---

## 5. What Umer needs to set up (one time)

Nothing here requires the PC beyond a browser — a phone works for most of it.

| # | Item | Where | Effort | Cost |
|---|---|---|---|---|
| 1 | GitHub account + private repo | github.com | 10 min | free |
| 2 | Google AI Studio API key | aistudio.google.com | 5 min | pay per use |
| 3 | Meta app + long-lived Page/IG token | developers.facebook.com | 45 min, fiddly | free |
| 4 | Pinterest business account + app | pinterest.com + developers | 30 min | free |
| 5 | TikTok business account + dev app | tiktok.com + developers | 30 min | free |
| 6 | Anthropic API key | console.anthropic.com | 5 min | pay per use |

Steps 3–5 are the tedious part and are best done in one sitting. Claude can walk each one
click-by-click, but **Umer must do the logins and approvals himself** — Claude never enters
credentials. Nothing else in the build is blocked on these; the generate half can be built and
tested first, with publishing wired last.

---

## 6. Build phases

**Phase 1 — Repo + assets (half a day)**
Create the private repo, move the canonical references, supplier video, past bundles, QC gate and
brand docs into it. Nothing runs yet. Outcome: the project's memory lives somewhere the PC can't take
down, which is worth doing even if the rest stalls.

**Phase 2 — Generation in the cloud (1 day)**
Wire the Gemini API: image editing from the canonical reference, Veo motion, ffmpeg cuts, PIL review
cards. Run it manually and compare output against the approved 13 Jul bundle. **Gate: the API path
must clear the QC bar the Chrome path reached.** If it can't hold pan fidelity, stop and reassess
before building anything on top.

**Phase 3 — The QC gate, automated (1 day — was half a day)**
First correct the written spec (§3c, cause 1), then port the gate into deterministic assertions plus an
**adversarial** vision pass that never sees the generation prompt. Validate against
`automation/qc_regression/`: the chrome-ball water test, the two-handled pan, **and the two July assets
that wrongly passed**. **It must reject every one.** A QC gate that has never rejected anything is
decorative — and this one has now demonstrably passed defects.

**Phase 4 — Schedule + approval (half a day)**
Monday cron, Issue-based approval, comment-triggered publish. Test with a dry-run flag that generates
and posts the Issue but publishes nothing.

**Phase 5 — Publishing (1 day, spread over the token setup)**
Instagram and Facebook first — they share the Graph API and cover most of the reach. Pinterest next.
TikTok last, given §7.

**Total: roughly 4–5 focused days**, plus the T1–T4 test stages in §3d, which run over calendar weeks
rather than working days.

**Total (was 3–4 days before the QC findings).** Phases 1–4 are independent of the API token paperwork, so the
engine can be complete and proven before the first platform is connected.

---

## 7. Known limits — read before committing

**TikTok will not be fully automatic at first.** TikTok's own documentation states that *"all content
posted by unaudited clients will be restricted to private viewing mode."* Until the app passes
TikTok's audit, the workflow can push the finished video to the account as private — Umer opens the
TikTok app and flips it public. Ten seconds on a phone, no PC. Audit can be applied for later.

**Meta tokens expire.** Long-lived Page tokens last ~60 days. The workflow needs a refresh step and a
loud failure when it can't publish — the standard reason these pipelines die quietly six weeks in.
The Monday run should notify on failure, not just on success.

**Model drift is not solved by moving hosts.** The copper-rim problem and pan-geometry drift are
properties of the model, not of Chrome. The canonical reference set and the QC gate remain the
defence, which is why Phase 3 exists and why Phase 2 has a hard gate.

**A quiet engine is worse than no engine.** Every workflow must fail loudly to the same Issue channel.

---

## 8. Running cost

| Item | Rate | Weekly |
|---|---|---|
| 4 pillar images | ~$0.07–0.12 each (Nano Banana Pro, 2K) | ~$0.40 |
| 2 × ~10 s video | ~$0.10 per second of 720p | ~$2.00 |
| Claude — planning + QC | per run | ~$0.50–2.00 |
| GitHub Actions | free tier | $0 |
| **Total** | | **≈ $3–5 / week** |

**≈ $15–25 per month**, and the **Google AI Pro subscription can be dropped** once generation moves to
the API — so the net change is close to zero.

Not included: the Shopify plan. The store is currently on **Pause and Build**, where checkout is
disabled. Content sent to a store that cannot take orders earns nothing, however well it is made.
Pipeline-first is a defensible order of work, but the store must come off pause before publishing
starts, or the first automated week is spent driving traffic into a closed door.

---

## 9. Open decisions

1. **Approval channel** — GitHub Issue (zero extra infrastructure, recommended) or Telegram bot
   (nicer to use, needs a webhook receiver such as a free Cloudflare Worker). Issue first; Telegram
   can be added later without changing the engine.
2. **Repo history** — start clean, or import the existing `IronRoot/` tree wholesale.
3. **TikTok** — accept private-draft + manual flip, or pursue the audit before launch.
4. **Backfill** — six weeks of content were never made. Resume from the coming Monday, or generate a
   catch-up batch first.
5. **Launch backlog.** Two QC-passed bundles are ready to post. Publish them first as weeks 1–2 while
   the engine is still being built, or hold them and launch everything at once?
6. **Inspiration library.** Umer has assets collected in `Downloads\IronRoot`, which is not connected to
   this session. They need to be reviewed and folded into `assets/inspiration/` before Phase 2.

---

## 10. Next action

Nothing is built yet — this document is the plan only.

The first reversible, useful step is **Phase 1**: get the canonical references, the QC gate and the
brand docs into a private repo. It takes under an hour, needs no API keys, and ends the situation
where the entire project lives on one machine that is usually switched off.
