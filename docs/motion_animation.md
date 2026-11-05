# Saved motion feeling: Model8 development increment

The development app now has **Pose → Motion feeling…**. Enable it, choose a gentle
or lively amount and Apply. The setting belongs to that model and has one Undo.
Simple shows the compact control; Advanced additionally lists up to256 generated
helper frames, their kind and native part name. Authored timeline diamonds are
black. Generated helpers remain derived data; they are not stored as authored keys.

This is an opt-in first integration while style/default intensity is reviewed.
The canonical owner-approved installation is the frozen Model7 update; this Model8
work remains a separate development/checkpoint increment pending broader regression.
No normal installation of Model8 is implied by the tests or by the Model7 approval.

The owner clarified that they will be the first actual artist using this app. The
goal is GMod familiarity with much simpler, quicker work than Stop Motion Helper,
and useful polish from a few main poses. This is a product acceptance target, not
a benchmark already proved. First-use review must test the whole import/pose/key/
preview/draw/export loop, whether defaults produce useful character motion, and
where interruptions or extra choices slow the owner down. Mechanical test counts
do not establish that usability or artistic quality. Keep this acceptance OPEN.

## Standard data and evaluation

`studio_model_8` retains independent body/expression tracks and continuous foot
contacts. It adds exactly one descriptor:

```json
"motion_assist": {
  "format": "studio_motion_assist_1",
  "enabled": true,
  "strength": 0.65
}
```

Earlier versions reject this descriptor, and older readers reject Model8. New
readers retain versions1–7 behavior. Model7 contact operations and Model6 body
operations preserve Model8 rather than downgrading it. Geometry, native parameters,
expressions, visibility and original assets continue to use the same standard model.

The shared Model sampler compiles immutable source-time plans once per data/frame-
rate revision. Derived body/root changes enter before standard contact solving.
Normal preview and final render use this same evaluator. Invalid settings, failed
compilation, coordinate limits and unreachable contacts remain explicit errors;
they are not hidden by silently removing assistance. Source-time mechanics and
provisional profile choices are documented in motion_assistance.md.

Authored body/root accessors remain separate. A draft begins from those underlying
curves. Unchanged peers still get their derived motion; an actually edited visible
target is not offset twice. Auto-key compares authored draft changes and creates
only the affected main controls. Committing one bone must never bake generated
root/peer motion. Fresh main keys invalidate/rebuild the derived plan. Dense captured
take intervals retain their original motion rather than gaining extra bouncing.

Changing settings defers while Physics/Hair or pending import startup is active,
and asks that an unrecorded draft be recorded first. It validates complete-range
reach and the existing world metadata budget before making one history change.
Save stores the descriptor and authoritative controls, never a flattened helper
take. Reopening regenerates assistance using saved project timing. Independent RGBA
paint and explicit camera keys stay separate.

## Evidence and unfinished work

`python tests/verify_motion_animation.py` checks the contract, validation, exact
authored samples/main keys/Off, source/peer preservation, draft/key isolation,
frame-rate rebuilding and dense captured-take behavior.

`python tests/verify_motion_animation_app.py` runs actual Simple/Advanced controls,
Apply/Undo/Redo, auto-key, Off and fixed-foot evaluation on Miku, GMod Reimu, SFM
Scout and VRM0/1. It saves a normal packed HAS, exports a normal H2641080p24/48-frame/
two-second MP4 and compares its own frame10 exactly. A separate app cold-opens the
HAS and checks portable data, all97 reverse sampled pose hashes, editable cyan paint
and the final image within the established mesh-edge bound. Private desktop
receipts are required. These use prepared native standard assets, not fresh native
decoder conversions or physical mouse/tablet input. The movie is silent.

This is focused evidence, not the full suite, clean-machine packaging or subjective
acting-quality acceptance. Actual Model8 live physics/recording interactions,
parented assisted models, all clip/clipboard/contact-editor lifecycles, linked HAS,
recovery/lessons and large-rig performance still need wider coverage. The existing
physics/contact regression for earlier versions remains required. Individual
generated-helper adjustments/pins, detailed curves, walking and the contextual
face editor are unfinished. Advanced inspection is currently read-only; global
amount is editable. The full MD/addendum objective remains active.
