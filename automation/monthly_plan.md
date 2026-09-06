# Monthly batch — plan (draft, 4 Sep 2026)

*Replaces the weekly run. Umer's reasoning: a weekly review is a weekly chance to
forget or run out of time; a monthly batch gives days of slack to look properly
and fix things. Agreed — the risk of a missed week is higher than the risk of
planning a month wrong.*

**Settled (Umer, 6 Sep 2026):**
- Generate on the **1st of the PRIOR month**. November's batch is made on 1 October,
  giving a full month to review. (My earlier 24th gave a week; a month is better.)
- **Per-image approval**, **daily release from the repo**.
- **Repetition across months is fine** provided the pillar mix stays right. This
  removes the library-exhaustion problem entirely — the constraint is MIX, not
  novelty.
- **Dish rotates** so no two consecutive posts show the same food.
- **Code-built cards are made in the same run** as the images, so Umer reviews the
  whole month in one pass.

---

## 1. The cycle

| When | What |
|---|---|
| **1st of the prior month** | The batch runs. Everything for the following month: generated images, code-built cards, captions, QC, dated calendar. |
| that month | Umer reviews at his own pace, approving in passes. |
| **20th and 27th** | Reminder comment if anything is still unapproved. |
| **1st of the target month onward** | Daily release job posts whatever is due, if approved. |

**Bridge:** it is already 6 September. The rest of September and all of October
are covered by a one-off on-demand run once the workflow is built, not by the
monthly schedule. The first scheduled run is **1 October, for November**.

## 2. The calendar and the mix

**13 posts a month, three a week — Monday, Wednesday, Friday.** Each gets a real
date, and the batch is ordered before Umer sees it.

The mix follows the strategy rather than whatever the scene library happens to
hold:

| Pillar | Target | Posts | How it is made |
|---|---|---|---|
| 1 — education | 40% | 5 | 2 generated demos + 3 code-built claim cards |
| 2 — product in action | 30% | 4 | generated |
| 3 — social proof | 15% | 2 | code-built review cards, real reviews on real photos |
| 4 — lifestyle | 15% | 2 | generated |

So **8 generated images + 5 code-built cards**. Fewer generations than the 12 we
discussed, a better mix, and cheaper — the cards carry no drift risk at all.

**Adjacency rules** — no two consecutive posts may share:

- the same **pillar** (no two product shots back to back)
- the same **subject** (person / pan-only alternates)
- the same **mood tone** (light / warm / evening)
- the same **dish** (see §4)

Benefit demonstrations — dishwasher, easy-clean, eggs, durability — are spread at
least 8 days apart so the month does not read as an advert block.

## 3. Approval, per image

The issue lists all 12 with dates. Umer replies in passes, in his own words:

```
approve 1-6              locks the first six
approve all except 9     locks everything but 9
redo 9 - use salmon      only 9 comes back
4 is too dark            only 4 comes back
approve                  locks whatever is still pending
```

Approved images **lock**: a later comment never silently regenerates something
already accepted. Status lives in the batch file, so a review spread over three
days across two devices picks up where it left off.

## 4. The dish axis — new

Nothing currently controls what food appears; the model decides, so two posts can
easily show the same plate of potatoes. Scenes get a `dish` slot, rotated across
the month and checked for adjacency: salmon, steak, eggs, vegetables, chicken,
one-pan dinner, nothing (empty pan).

This uses the mechanism that already works — a scene detail appended to the
prompt, never a description of the pan.

---

## 5. Two problems that need a decision

### 5a. RESOLVED — repetition is allowed

Umer: repeating scenes month to month is fine as long as the pillar mix holds. A
scene may return after a **60-day cooldown** with a different mood and a different
dish. At 8 generated images a month against 26 scenes, that is comfortable.

### 5b. Pillar 1 needs more demo scenes

| Pillar | Scenes | Strategy target |
|---|---|---|
| 1 — education | **1** | 40% |
| 2 — product in action | 15 | 30% |
| 4 — lifestyle | 10 | 15% |

A 12-image month from this library is mostly product shots — closer to a catalogue
than the mix the strategy asks for.

Part of this is expected: most education posts are *claim cards* and all social
proof is *review cards*, both built in code from real photographs, and neither is
built yet. Until they are, generated images cannot hit the strategy mix.

Both are being done:

1. More **education demonstration** scenes — things that prove a point by being
   done, drawn only from claims already substantiated on the product page:
   oven transfer (oven-safe to 500F), induction hob (all cooktops), searing
   (tri-ply even heat), the durability scrub. No physics demos — those stay real
   footage or nothing.
2. **Code-built cards** in the same run: 3 education claim cards and 2 review
   cards per month.

### 5c. RESOLVED — reviews are translated to English

The 27 verified reviews visible in the product metafield are Dutch. The strategy
targets US home cooks. That is a problem specific to review cards, because their
entire value is being *verbatim* and *real*:

**Umer's decision, 6 Sep 2026: translate to English always.** Implemented in
`engine/reviews.yaml` — original Dutch and English kept side by side, and every
card carries **"Translated from Dutch"**. The label keeps the quote honest at no
cost to the message; a translated review presented as the customer's own English
is a small misrepresentation, and the whole value of a review card is that it is
real.

One translation was nearly a claim in disguise. Lotte M's *"zonder aanbranden"*
means **without burning**, not "without sticking". Rendering it the loose way
would have manufactured a non-stick claim out of a customer's words — exactly what
brand.md forbids. The accurate wording is recorded with a note so it cannot drift
back.

5 of the 27 reviews are transcribed, enough for about two months at two cards a
month. The remaining 22 need pulling from Judge.me before month three.

---

## 6. Build order, once the above is settled

1. `dish` axis + adjacency-aware calendar builder
2. Monthly batch run (resumable — 12 images is too many to lose to one failure)
3. Per-image approval state machine
4. Daily release job, publishing stubbed until Phase 5
5. The 28th reminder

## 7. Risks

- **One batch, one failure.** A crash at image 9 must not discard 1–8. The run
  writes each image as it completes and can resume.
- **12 images is a long page on a phone.** The issue needs a compact table with
  thumbnails and dates, not twelve stacked sections.
- **Nothing goes out if Umer never approves.** That is deliberate, but it means
  silence has a cost now — hence the reminder on the 28th.
- **A month of drift is a month of drift.** If the model shifts, twelve images are
  wrong rather than three. The QC gate matters more, not less.
