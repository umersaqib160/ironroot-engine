# IronRoot — Weekly Content Engine v2
*Updated 10 Jul 2026. Replaces the Telegram/n8n plan — approval now runs through the Claude app (iPhone or desktop). The old n8n docs (`n8n_setup_guide.md`, `n8n_workflow.json`) are retired.*

---

## The loop (one line)
Every **Monday 08:00** a scheduled Claude run generates next week's content under the QC gate → Umer approves from the **Claude iPhone app** (or desktop) → Claude schedules everything via the platforms' native schedulers in Chrome → repeat.

**Brand voice (locked):** chemical-free / PFAS-free · durability · "a pan for life."
**Quality gate (locked):** every asset passes `automation/QC_process.md` at full resolution before it reaches the approval bundle. No exceptions.

---

## 1. Weekly output

| Channel | Content | Source |
|---|---|---|
| Instagram | 4 posts (one per pillar: education / product / proof / lifestyle) | AI-edited from real pan photos (Gemini Pro) + review cards built in code |
| Facebook | same 4 posts, longer captions | same assets |
| Pinterest | same 4 posts as Pins (4:5 or 2:3), keyword-rich descriptions | same assets |
| TikTok | 2 videos — format chosen weekly by Claude: supplier-footage cuts, photo-swipe posts, or atmospheric AI motion (Veo; no physics, no hands) | supplier videos / approved stills / monthly phone-shoot clips |

Assets land in `content/weekly/<week-of-DATE>/` with captions + QC sign-off in `captions.md`.

## 2. The Monday run (scheduled task, Mon 08:00)

**Requires: PC on, Claude desktop app open, Chrome running and logged into Gemini + platforms.**

1. Read last 2 weekly folders (avoid repetition) + `QC_process.md` + this plan.
2. Plan 4 pillar posts + 2 TikTok formats for the coming week.
3. Generate media: Gemini **Pro** (never Flash), every image edited from real photos in `content/images/scraped/`; ffmpeg for supplier-footage cuts (continuous music bed — audio QC rule).
4. Run the full QC gate at full resolution; regenerate or swap concepts on any failure.
5. Write `captions.md` (IG / FB / Pinterest / TikTok variants + QC block).
6. Post the preview bundle in the session and request approval.

## 3. Approval (Umer, from anywhere)

- Open the Claude app → the Monday session → review images/videos/captions.
- Reply **"approved"** — or changes per post ("redo post 2 darker", "swap the TikTok hook").
- Claude revises, re-QCs, re-presents until approved.

## 4. Scheduling (after approval; PC on)

- **Instagram + Facebook:** Meta Business Suite Planner — 4 posts each, spread Mon–Sat per the strategy calendar.
- **Pinterest:** native Pin scheduler (up to 2 weeks ahead).
- **TikTok:** web upload scheduler (up to 10 days ahead).
- All scheduling happens in Umer's logged-in Chrome via Claude. AI-label toggled ON for AI-edited assets (per QC doc). Confirmation summary posted in the session when done.

## 5. Access & accounts

| Platform | Status | Access method |
|---|---|---|
| Facebook Page | live | Umer's Chrome login → Business Suite |
| Instagram (business, linked to Page) | live | same |
| Pinterest (business) | **to create** — Umer signs up, Claude configures | Chrome login |
| TikTok (business) | **to create** — Umer signs up, Claude configures | Chrome login |
| Gemini (Google AI Pro) | live | Chrome login (image chat: "Photorealistic Kitchen Lifestyle Photo" has the pan reference) |

Claude never creates accounts or enters passwords — signups and logins are Umer's step.

## 6. Standing safety rails

- No invented reviews/numbers; social proof = verbatim real reviews.
- Meta ads stay **paused** until organic presence is established (separate decision).
- Physics demos only from real footage (supplier videos have a real water-bead test) or Umer's monthly 30-min phone shoot.
- If the Monday run can't reach Chrome/Gemini (PC off), it leaves a note in the session and Umer re-triggers when the PC is on.

## 7. Files
```
automation/
├── content_engine_plan.md    ← this file (v2)
├── QC_process.md             ← mandatory quality gate
└── (n8n_* files retired — kept only for reference)
content/weekly/<week-of>/     ← weekly bundles: media + captions.md + QC block
```
