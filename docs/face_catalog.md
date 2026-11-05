# Shared face catalogue: first deform-area controls

On2026-11-01 the owner asked HAS to organize the available facial deforms into one
consistent catalogue across models. Keep embedded expressions/emotes in their
own category and separate mouth, eye and brow deforms. Preserve Other/Unassigned
controls rather than hiding unfamiliar native names. This develops the existing
GMod-inspired face-editor requirement; it is not a source-format export feature.

## Catalogue and mapping rules

- **Expressions / emotes:** presets explicitly provided by the source, retaining
  compound bindings and native/custom identity. A named Smile morph is not proof
  that it is a whole-face preset.
- **Deforms:** Mouth, Eyes, Brows and Other, with left/right/both where known.
  Common labels such as Blink or Mouth open are intent labels, not renamed mesh
  targets. Preserve ranges and supported native behavior.
- Prefer native metadata, then a small local dictionary of known names/aliases,
  including repeated Japanese names and common Source/VRM names. Label uncertain
  guesses. Unknown controls stay accessible for manual assignment; no compulsory
  model/AI/cloud inference.
- Simple presents familiar labels and relevant controls. Advanced retains exact
  native names, group/category, ranges, original bindings and mapping confidence.
  Do not rewrite skeleton IDs or morph target identities to achieve a nicer UI.

### Implemented first UI increment (development source)

Shapes now has an **All areas** filter in Simple and Advanced: Brows, Eyes, Mouth,
Body, Clothing, Hair, Accessories, and Other/unassigned. A small local vocabulary
and explicit name tokens provide clearly labelled **Name estimates**. All areas
retains every original target; filtering does not renumber or rewrite bindings.
Unknown and mixed-area names remain Other. Ambiguous Smile/笑い names are not
automatically declared an eye control, a brow control or a compound expression.
This is a browsing foundation. A separate tested observation backend is described
in [deform_observations.md](deform_observations.md). Development offers an
[Advanced study/review action](shape_study.md), with explicit adoption of suggestions
and Undo; it does not silently classify controls.

Advanced adds **Organize this control** with the exact original name, chosen area,
optional friendly name, **Save name and area**, and **Use estimate again**. A manual
choice takes precedence over the estimate, is one Undo action, and is saved in
`metadata.shape_catalog` (`studio_shape_catalog_1`) with canonical node/target IDs
and the native name. At most256 assignments are accepted. Changing the native
identity prevents a stale choice from being applied. Unsupported catalogue versions
remain preserved and report a notice; they are not overwritten. Removing the final
manual choice removes only this metadata. Names/groups do not alter morph amounts,
keys, object format, poses, camera, native reports or source assets.

Pending amount edits and live/pending Physics/Hair defer organization rather than
consuming or freezing them. The project metadata limit is checked before the
one normal history edit. Ordinary refresh preserves pending rename/category input.
Simple uses chosen friendly names; Advanced retains native names and exposes the
manual fields through the existing scroll area. Search includes the original name
and displayed label. Close remains pinned and visible in the350x520 shape window.

Fresh evidence:21unit checks,109actual app checks on the authored fixture plus
Miku/GModReimu/SFMScout/VRM1/VRM0/suppliedMima, and5separate cold-reader checks.
Packed/linked HAS, exact classification Undo/Redo, unchanged rendered appearance,
actual categorized-target edits and H2641080p24/48frame MP4 passed. The initial cold
test wrote expected floating values with default JSON precision; full-precision
expected serialization and numeric canonicalization corrected the harness while
retaining exact authored-value assertions. Failed output remains retained.

Four existing affected groups also passed: source shapes39, base shapes54, shape
animation73 and UI23 (plus those wrappers' existing unit checks). A final caption
refinement showing the exact original name was checked by the actual private UI
probe; Simple and Advanced screenshots were inspected. The first visual probe
had correctly reopened with nothing selected and therefore showed no popup; its
assertion now requires explicit selection and a visible shape window. No physical
input/artist-quality claim. Evidence: `output/shape-catalog-verification.json`,
`output/catalogue-regressions.json`, `output/shape-catalog-visual.json` and run logs.

The earlier frozen Model8 source completed all98original full-verifier processes
before this UI increment; that complete snapshot/evidence is retained separately.
It is not a full-suite result for the newer catalogue source. The catalogue suite
is now wired into the normal verifier. Normal installed Studio remains the approved
Model7 source until a later reviewed update; development checkpoints are separate.

VRM0/1 [embedded expression poses](expression_presets.md) now use exact grouped
bindings through the ordinary deform key/Undo path. Continuous native expression
animation, other native-panel/rule preservation, automatic geometry-based categories, calibrated confidence, richer
standard labels and broad supervised validation remain unfinished. This increment
does not substitute name estimates for those requirements.

### Owner-confirmed deformation probing and supervised development

The owner specifically wants each available deform tried against a neutral
before/after state to observe what it actually changes. Use the provided models,
their known names and observed deformations as labelled development examples for
an educated-guess estimator. Native names/metadata can seed labels, but observed
movement is important evidence, not merely a name lookup. The owner expects to
provide more varied models later, including non-facial features; existing samples
are enough to start. This authorizes local model/deform research, not an external
upload, mandatory cloud model or redistribution of the models/training examples.

Probe an isolated copy at a fixed neutral pose, one control at a time, and restore
the baseline between controls. Test both signs where the source range is signed.
Compare actual supported vertex/bone/material/UV effects; a missing evaluator must
be labelled unsupported, not counted as "no change". Context-dependent corrective
controls may have no standalone effect and must remain accessible. Preserve
embedded compound presets as such; affecting multiple regions alone does not
prove a deform is an emote. Include Body, Clothing, Hair/accessories and Other/
Custom categories instead of forcing every control into a facial group.

Useful features include affected vertex regions, normalized displacement/bounds,
direction, left/right symmetry and overlap with known eye/mouth/brow examples.
Use neutral head-local/anatomical references rather than current crouched height
or global camera pixels. Geometry and optional controlled renders can complement
each other. Names-derived seed labels are weak supervision until reviewed; do not
present them as artist-certified ground truth. Keep confidence, evidence and manual
correction paths. Split evaluation by character/model family, keeping VRM0/1 of the
same character together, so near-duplicate geometry does not inflate validation.
Measure transfer to new models and extra features, not memorization of one model's
names. A production estimator and complete multi-model probe dataset remain unfinished;
the metadata audit below is separate from the later bounded probe pilot.

### First actual labelled probe pilot

The local research helper now evaluates all15 positional morphs in the supplied
Miku PMD's prepared GLB, one target at+1 and-1, resetting to neutral each time:
30before/after probes across17 mesh primitives/9392vertices. It uses the existing
validated `GLB.shaped_skin` path, including sparse POSITION decoding, without
modifying the source. Morph operations total281760, below the existing evaluation
budget. Neutral mesh-local height agrees with the independent engine measurement
within.00001units. This orientation check is not full cross-model alignment.

Provisional model-specific annotations pair actual affected-region statistics
with known names: six brow controls, four eye controls and five mouth controls.
In this model, affected mean Y is about1.468 for brows,1.422 for eyes and1.359–1.365
for the mouth. The features include changed vertex counts/bounds, signed movement,
symmetry-side counts and same-model mask overlap. No rendered visual comparison or
artist-certified label review has occurred in this pilot.

A tiny one-dimensional nearest-labelled-prototype estimator fitted three seed
controls and matched all12other controls' provisional categories on this SAME
character. That is a useful sanity check, not evidence of generalization. A
synthetic out-of-region input returns Unassigned. The .01 distance threshold is
an experimental cutoff, not a calibrated probability. Neither the data nor the
estimator is installed in the app. Other characters, non-facial features,
material/UV/bone controls, emote groups and contextual correctives remain untested.
Evidence/helpers: `output/deform-probe-pilot.json`, its feature dataset,
`output/probe_miku_deforms.py`, `output/deform-estimator-pilot.json` and
`output/fit_deform_probe_pilot.py`. Future validation must keep character families
separate and preserve all the uncertainty/unknown-control rules above.

## Actual retained data inspected

The later [SFM sample corpus audit](sfm_sample_corpus.md) adds 66 native model
definitions and a nine-file raw vertex-delta pilot, including non-facial features.
One Mima head now has three actual direct controls verified from native deltas
through prepared GLB, Simple edits, animated keys, Undo/Redo, packed/linked HAS,
cold Open and MP4. A relocated packed demo also opens in the installed Model7 app.
Its 143 standard positional targets were probed separately; this does not prove
all 82 native controllers or the rest of the corpus works end-to-end.
Character variants, exact duplicates and suspected shared base meshes must stay
out of opposite sides of a claimed independent evaluation split.

A read-only metadata audit of the existing prepared five-native HAS found:

| Model | Available native face metadata |
| --- | --- |
| Miku PMD | 15 vertex morph names; no bone/group/material/UV morphs in this sample |
| GMod Reimu | 52 flex controllers and54 native flex names |
| SFM Scout | 66 flex controllers and616 native flex names |
| VRM1 | 14 declared expression presets with target bindings |
| VRM0 | 14 blend-shape groups with preset/name/binds metadata |

Evidence is `output/face-catalog-metadata-audit.json`. Counts are native metadata,
not a claim that every item has a complete runtime binding. Source controllers can
have signed ranges (Scout includes-1..1), unlike simple0..1 morph sliders. Controller
rules/correctives must not be replaced by a name-only one-target assumption. The
Miku report currently retains names, not reliable panel categories for every item;
dictionary fallback does not replace richer source-category preservation.

VRM1 node/target IDs and VRM0 mesh/target IDs use different source identities and
weight conventions. Resolve their exact prepared/runtime mesh bindings, including
shared meshes/reparenting, instead of treating every matching name as the same
target. Binary behavior, custom presets, exclusions/overrides, material/color/UV
bindings and MMD group/bone morphs need explicit support or visible limitations.
Do not show an apparently working full expression while silently dropping parts.

The existing model5/8 per-target positional expression controls, independent
timeline keys, Undo and HAS remain the foundation. The richer semantic catalogue,
compound preset editing and complete native rule
evaluation are unfinished. Tests must cover duplicate/unknown names, left/right,
signed ranges, actual native visible deformation, key isolation, preset overlap,
Undo/Save/cold Open/MP4 and original-source preservation. First-use facial posing
and artistic quality remain OPEN; metadata inspection is not that acceptance.

For visual review, development Advanced offers
[Compare without recording](shape_comparison.md). One temporary standard model
shows neutral and one selected positional control from an identical camera. This
is separate from animation Apply and category adoption, and preserves pending
amounts. Native compound/controller semantics, non-position effects and broad
semantic estimation remain unfinished.

In Simple mode, typing in Find shape searches all deformable parts of the selected
character. Choosing an area such as Eyes, Mouth or Brows also lists that area's
controls across the character. Typing narrows the list by friendly label, original
name or area. Duplicate displayed names include a part number. Selecting a result
switches to its actual model part and shape index. With All areas and an empty
search, the part picker returns. Advanced and base-shape browsing keep their
part-specific scope.

When correcting a control in Advanced mode, an active area filter follows its
new category. A search is kept if the revised name or category still matches.
Otherwise the editor clears the search so the corrected control remains selected.

Select a deform and choose Preview this control to see neutral and changed views
framed around its moving geometry. In Simple mode the preview uses the friendly
label and a 0–1 test amount. Turn the preview to inspect another angle. Advanced
also supports negative test amounts and shows geometry details. Closing the
comparison returns to the original scene and its pending deform amount.

Use this amount returns a completed preview's value to the same control and
frame. Apply at this frame uses the usual Auto-key or draft behavior. Closing
the preview instead keeps the value that was pending before you opened it.
Changing the timeline frame closes the preview to avoid staging on another pose.

The preview starts at a pending editor strength, including an explicit zero,
or the current nonzero animated amount. A neutral control with no pending edit
opens at full strength so its effect is visible. Preview values use the editor's
0.001 precision within the preview range (0 to 1 in Simple, -1 to 1 in Advanced).
The editor value itself changes only when Use this amount is chosen.

Keep the other expression controls at this frame compares the selected control
at zero and at the preview amount with the same surrounding deform weights on
both sides. Those weights come from the selected character's currently evaluated
deform tracks and base shape. The isolated preview still uses the neutral skeletal
pose and its own camera and lighting.

With Auto-key off, Apply at this frame updates the expression draft. While that
draft differs from the recorded motion, Record pose key at this frame is available
inside the face editor. This uses the standard pose-recording action, including
its existing prompt when replacing a pose key. A rejected Apply reports the reason
and leaves the pending strength available for correction.

Discard expression draft restores the recorded facial values at this frame,
including any interpolated values between keys. Undo recovers the draft.

Recovery preserves an unrecorded expression at its draft frame. The face editor
offers Record and Discard whenever such a draft is present, including after a
restart where the current Auto-key preference differs from the earlier session.
