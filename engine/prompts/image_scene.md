# Image generation — subject placement

*Method confirmed by Umer 3 Sep 2026 after testing it himself. This replaces the July "edit the
reference photo into a new scene" approach, which produced the wrong handle three times.*

---

## The method

Attach **`content/images/reference/PRIMARY_pan_studio_2048.jpg`** and ask the model to place that pan
into a scene it composes around it. The model handles scale, angle and perspective by itself.

### Template

```
Use this frying pan in the image, then create an image for <PLATFORM> where <SCENE / ACTION>.
The setting is <SETTING>, <MOOD>, with <PALETTE> shades. <LIGHT>.
```

### Umer's tested example

```
Use this frying pan in the image and then create an image for instagram where the pan is being
used by a chef at home. The setting of the home is cozy but dark, with brown, black, cream shades.
```

---

## The one rule

**The prompt contains ZERO description of the pan.** Not its shape, not its handle, not its finish,
not its rivets, not its rim. The photograph is the specification.

Describing the pan is what broke July: the prompt said "droplet/bulb handle, widest near the end",
the model followed the prose over the attached photo, and drew a handle the pan does not have.

**If an output is wrong, the fix is a better or better-angled reference photo — never more
adjectives.** Adding a corrective sentence ("slim handle, no rim lip") re-creates the exact failure.

---

## Scene library

Vary these; never repeat within a rolling three-week window (see `../brand.md` §4).

**Pillar 2 — product in action**
- steak going into the pan, hob-lit, steam rising
- eggs cooking, morning window light from the side
- one-pan dinner mid-cook, hands out of frame or plausible
- pan moving from hob to oven, kitchen dark behind

**Pillar 4 — lifestyle / brand**
- hanging on a kitchen wall or rail among wooden utensils
- resting on a worn wooden counter, ingredients nearby
- Sunday meal-prep spread, pan as the hero object
- clean kitchen flat-lay, dark surface, few props

**Pillars 1 and 3 — education and social proof**
These are **built in code** (PIL) on real photographs, not generated. Text overlays and review cards
have zero drift risk when composited deterministically. Do not generate them.

---

## Constraints that still apply

- **No physics demonstrations** — no water tests, oil behaviour or sizzle-droplet effects. Real
  footage or nothing.
- **No AI humans as customers.** A cook may appear in a lifestyle scene, never speaking as a customer,
  always with the platform AI label on.
- **No text in the generated frame.** Overlays are added afterwards in code, where they are legible
  and spellable.
- **Induction hobs are flat black glass** with cross/plus zone markings only — never coil graphics or
  glowing rings.

---

## After generation

Every output goes through `automation/QC_process.md` at full resolution before it reaches the
approval Issue. This method removes the prose-versus-photo conflict; it does **not** remove drift —
the model still re-renders the pan rather than compositing it, so the gate stays mandatory.
