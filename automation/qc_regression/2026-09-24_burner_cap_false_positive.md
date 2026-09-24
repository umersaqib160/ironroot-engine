# False positive: a gas burner cap read as a second pan

**Image:** `content/monthly/2026-10/p2_pan_on_hob__9x16.jpg` (24 Sep 2026)

**What the gate said**

    other_cookware: true
    "A black non-stick frying pan is clearly visible on the adjacent burner"

**What is actually there**

Two round black objects on the hob, one top-left and one bottom-left. Both are
gas BURNER CAPS. The bottom-left one is unambiguous at full resolution: the cast
pan supports radiate out from under it and the burner skirt is visible beneath.
The top-left one is the same part, further away and partly behind our pan.

**Why it matters more than one wrong answer**

The image is good. The handle rule added the same day worked — the handle points
down and to the right, toward the cook. Umer reviewed the batch and said the
posts looked fine, and he was right; the gate was the thing that was wrong.

A gate that cries wolf gets ignored, and then it is worth nothing on the day it
is right. This is the same failure as the first frame detector flagging a white
studio backdrop and a dark hob — a rule that fires on a legitimate photograph.

**Fix**

The other_cookware question now describes a burner cap and says what separates
one from a pan: a pan has a wall and a handle and stands above the supports; a
cap is flat, sits between them, and has neither. Dark rings printed on induction
and electric glass are called out for the same reason.

**Still true**

The constraint "It is the only pan in the picture" has not been disproved by
this. p2_couple_cooking had a real second pan and predates the constraint. No
generation made since has produced one.
