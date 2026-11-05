# Compare a deform without recording — development

In Advanced, open Shapes / expressions, select a control and scroll to Organize
this control → **Compare without recording…**. The left image has every deform
off; the right tests only the selected positional control. Both use the same
camera and imported neutral skeleton. The close-up follows the affected vertices.
Turn left/right to inspect another angle. Test amount supports -1 through 1;
these are mathematical tests, not a promise of the original control's valid range.

The comparison uses one disposable copy through the existing standard model and
renderer. It preserves the model's displayed orientation, removes scene placement
and uniform scale for inspection, and uses approximate Unshaded materials. It does
not include the current animated pose, other deforms, fan/physics or drawing.
Pending amount edits stay pending. Closing records no key or Undo command and
does not modify native names, source files, stored categories or the current view.
Use the ordinary catalogue controls to keep a reviewed category separately.

Stop live/queued Physics or Hair and playback first. Comparison refuses during
conversion, HAS work or export. Changing selection/source, editing the scene,
New/Open, Home or closing Shapes invalidates the temporary preview. An object-bound
one-shot readback callback is disconnected on close/teardown; no suspended Node
coroutine survives deletion. Snapshot rendering stops when the images are ready.

Source hashing/import and focus calculations run synchronously on this explicit
action. Large assets may pause the interface and require extra memory for the
temporary imported model. Existing 128MiB GLB and skin/shape limits still apply;
focus refuses more than 200,000 vertices in the selected mesh. Missing POSITION
movement reports unevaluated native effects rather than claiming no native effect.
Normal/material/UV/bone morphs, Source controller combinations, VRM grouped presets
and perfect native shader appearance remain unfinished. Scout eye shading is still
approximate. This is visual geometry review, not an emotion classifier or an
automatic category assignment.

Framing combines neutral/test positions with the existing skin palette and exact
native target identity. Godot's skeleton bake explicitly excludes blend shapes,
so it is unsuitable as the sole framing source here. See the primary
[Godot 4.6 MeshInstance3D reference](https://docs.godotengine.org/en/4.6/classes/class_meshinstance3d.html).

`python tests/verify_shape_comparison.py` runs real private-desktop GPU views for
an authored skinned fixture plus available native sample plans, and a separate
app-free test during an actual pending capture. It checks visible image changes,
identical cameras, exact document/view/history/pending-amount isolation, exact
final-scene/cyan-drawing exclusion, zero and negative amounts, turning, Close/New
and callback/resource teardown. Optional native plans come from prior catalogue
and height audits; absent private plans are reported, not bundled. The source
archives are never modified. Evidence is `output/shape-comparison-verification.json`.

Normal installed Model7 and the frozen web handoff do not contain this development
increment. The expanded full verifier is wired; that entire suite has not been
rerun for this change. No physical mouse/tablet, subjective artistic quality,
native appearance, clean-machine or universal performance acceptance is claimed.

## Verified increment — 2026-11-01

The final comparison wrapper passed 68 editor checks plus two pending-capture
teardown checks on an authored model and all six available native preparations:
Miku, GMod Reimu, SFM Scout, VRM1, VRM0 and supplied Mima head. The affected study
(47 app/reader/teardown +17 Python), catalogue (29 unit +112 app +5 cold reader)
and Simple/Advanced UI (23) also passed: 303 checks total, zero failures across
four commands, with eight accepted private GPU receipts. Current reports retain
exact source SHA/mtime checks. Existing study/catalogue HAS and ordinary MP4
regressions passed; this comparison adds no saved fields or movie exporter.

The first comparison test expected a pending amount of .125 despite an imported
.2 default; it now compares the exact value recorded before opening. Another
68/0 engine run exposed the outer report reader's cp1252 default on Japanese text;
explicit UTF8 fixes it. The added teardown test initially needed an explicit
WeakRef annotation. Failed logs remain separately retained. Final four-command
acceptance follows all fixes; no motion/pixel tolerance was changed. Miku blink
before/after and comparison UI images were visually inspected. Scout's approximate
Source eye shading remains visible and is not certified native appearance.
