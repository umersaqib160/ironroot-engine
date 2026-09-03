# IronRoot — content engine

Private repo for the IronRoot weekly content pipeline: generate four pillar posts and two short
videos every Monday, gate them on quality, get Umer's approval, publish.

**Store:** ironrootstore.com · stainless steel frying pan, $79/$85/$89 · USA market
**Why this repo exists:** the old pipeline needed Umer's PC switched on at 08:00 every Monday. It
wasn't, and the engine produced nothing for six weeks. This runs in the cloud instead.
Full reasoning: `automation/cloud_migration_plan.md`.

## The loop

```
Mon 08:00  GitHub Actions ── generate ── QC gate ── open approval Issue
                                                          │
Umer's phone ─────── "approve" / "redo 2 — darker" ───────┘
                                                          │
                                          on comment ── publish
```

Nothing publishes without an explicit approval. There is no auto-approve on a timer.

## How images are made — read this before changing any prompt

Attach `content/images/reference/PRIMARY_pan_studio_2048.jpg` and describe **only the scene**.
Never describe the pan.

> "Use this frying pan in the image, then create an image for Instagram where the pan is being used
> by a chef at home. The setting of the home is cozy but dark, with brown, black, cream shades."

The photo is the specification. In July 2026 the prompts *described* the pan — "droplet/bulb handle,
widest near the end" — the model followed the prose over the attached photo, drew the wrong handle,
and the QC checklist reciting that same prose passed it. Two assets shipped as "PASS v3" with a
handle the pan does not have. See `automation/qc_regression/`.

**Rule: shape and finish come from photographs. Prose says what to check, never what the pan is.**

## Layout

| Path | What |
|---|---|
| `engine/brand.md` | positioning, pillars, voice, scene style, variety rule — read every run |
| `engine/prompts/` | the scene templates and caption rules |
| `engine/platform_specs.md` | aspect ratios, exports, cadence |
| `automation/QC_process.md` | the mandatory quality gate |
| `automation/qc_regression/` | known-bad assets the gate must reject before it is trusted |
| `automation/cloud_migration_plan.md` | why this exists and how it gets built |
| `content/images/reference/` | canonical pan photos — the specification |
| `content/videos/` | supplier footage for real-footage cuts |
| `content/weekly/<date>/` | captions + QC sign-off (media is not versioned — see .gitignore) |
| `strategy/` | the original marketing strategy |

## Status

Phase 1 of five. Nothing is automated yet — see `automation/cloud_migration_plan.md` §7 for the
build phases and §6 for the T1–T4 test stages that must pass before anything reaches a live account.
