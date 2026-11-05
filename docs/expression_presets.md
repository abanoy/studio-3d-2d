# Embedded expression poses — development

Open **Shapes / expressions**. Models with declared VRM expressions or freshly
prepared MMD expression groups have a
separate **Expressions / emotes** chooser, Strength and **Use expression pose**.
Simple uses familiar preset labels; Advanced shows original group names and exact
node/target bindings. Custom expressions keep their native identity. A morph named
Smile alone does not become an embedded emote.

The Shapes window opens over the right inspector, leaving the framed subject
visible. It remains scrollable with Close pinned. Unsupported material-only groups
remain visible with an explanation, even on a model with no positional morphs.

Use expression pose replaces the model's entire set of **embedded expression
morph controls**, including custom ones. Other raw deforms retain their values.
Strength scales the declared bindings. Auto-key creates ordinary independent
deform keys in one Undo; with Auto-key off it creates a draft for explicit Record.
Repeated identical poses are no-ops. A pending raw amount or live/queued simulation
defers the operation without consuming edits or startup tickets. Complete world
metadata is checked before installing new deform keys.

This is **pose authoring**, not a separately animated native-expression channel.
Saved keys contain editable morph amounts, not a persistent Happy slider state.
Changing the preset later does not rewrite earlier keys. Binary sources quantize
the requested pose strength above 0.5 to one, otherwise zero; interpolation between
stored deform keys remains the ordinary editable HAS interpolation. Continuous
native binary/override behavior during animation, procedural blink/gaze/lip-sync,
material/color/texture effects and native appearance are still unfinished.

## Shared representation and source adapters

`expression_presets.gd` captures transient `studio_expression_presets_1` entries
from the source GLB. Each has stable native/custom identity, exact prepared
node/target bindings, weights, binary flag, overrides and an unsupported reason.
One shared evaluator resolves grouped amounts; the existing model, timeline,
Undo, HAS and MP4 paths handle them. No new saved project/model schema or external
format exporter. Authoring poses leaves the prepared GLB and native reports unchanged.

The VRM1 adapter uses node/target indices and fractional weights. VRM0 uses mesh
indices and percentage weights, resolving each active imported instance of that
mesh. Missing/duplicate/invalid bindings refuse instead of applying a partial
expression. Material/texture groups refuse as a whole. Unsupported versions and
more than 256 entries or 2048 declared/resolved bindings report a limit.
The pure evaluator supports additive groups and VRM1 block/blend procedural
overrides; the current UI authors one selected expression pose at a time.

MMD preparation now retains exact group membership, declared English/Japanese
names and weights. Nested groups flatten additively into exported vertex targets,
including repeated paths and signed weights. Fresh preparations embed the same
standard catalogue in `asset.extras.studio_expression_groups`; runtime verifies
version, identity, names, exact node/target bindings and supported semantics before
exposing it to the existing chooser/evaluator. There is no MMD pose engine.
English source names are preferred in Simple, with the small existing estimate
dictionary as fallback; Advanced retains original names and exact bindings.

Any nonzero bone/material/UV/unknown contribution refuses the entire group with
guidance. A zero contribution is inert. Missing targets, cycles, ambiguous names,
unsupported semantics, nonfinite/out-of-range weights or conflicting native
declarations also refuse. Limits:256 groups,2048 resolved binds,16384 source edges
or expansion operations,32 nested levels and magnitude100 per resolved amount.
Counts/diagnostics and raw bounded group data remain in the readable native report;
original properties remain in the retained native/Blender preparation. Metadata
injection preserves every exported GLB geometry chunk byte-for-byte. Source family
units, original files and existing projects are unchanged. Older preparations
containing only group names need a fresh import for these bindings; they are not
guessed or retroactively rewritten. Native continuous group-weight tracks and
bone/material/UV/flip/impulse effects remain unfinished.

The group property API was inspected from the separately installed MMD Tools and
its [primary implementation](https://github.com/MMD-Blender/blender_mmd_tools/blob/main/mmd_tools/properties/morph.py).
No third-party implementation was copied. The PMX fixture writer uses that existing
file API only to generate original test data; the app gains no external exporter.

Primary references: [VRM expression specification](https://github.com/vrm-c/vrm-specification/blob/master/specification/VRMC_vrm-1.0/expressions.md),
[VRM0 binding schema](https://github.com/vrm-c/vrm-specification/blob/master/specification/0.0/schema/vrm.blendshape.bind.schema.json)
and [VRM0 group schema](https://github.com/vrm-c/vrm-specification/blob/master/specification/0.0/schema/vrm.blendshape.group.schema.json).
No third-party implementation was copied or installed.

## Actual verification

Initial VRM increment: `python tests/verify_expression_presets.py` ran24 domain checks,45 actual app checks
and five fresh-process reader checks, all pass. Authored compound bindings span
two independently bound mesh instances. Both supplied VRM1 and VRM0 expose their
14 declared groups. Tests cover grouped values, unrelated raw deforms, actual
visible GPU change, body/camera/native-data isolation, one Undo/Redo, no-op, pending
amount/queued simulation, unsupported groups including material-only visibility,
draft/Record, near-1MiB refusal, side-window placement, packed/linked HAS and cold
Open. Ordinary H264 1920×1080, 24fps, 48-frame/two-second MP4 matches its own
reopened frame12 exactly with an independent editable cyan cel. Source SHA/mtime
checks pass; two accepted private GPU receipts. Actual UI and model frame inspected.

The first harness needed an explicit padding type. A later 41-check run failed
two assertions expecting untouched zero controls to have explicit keys; checking
the exact effective shape configuration corrects that fixture without changing
production values. Material-only guidance increased the writer to42, then actual
side-window placement checks increased it to45. Earlier logs remain separate.

Affected animation/catalogue/study/comparison/UI tests run separately. Native
import tests can use original Desktop VRMs or SHA-verified original `.vrm` copies
retained in earlier import bundles; they never relabel a prepared GLB as raw VRM.
The initial native attempt skipped missing Desktop samples; a corrected fresh
8-unit/43-app conversion/HAS/movie run passed using verified retained inputs.
The entire expanded verifier is wired but has not been fully rerun. Native shaders,
all-rig semantics, physical input, subjective artistic quality and clean-machine
acceptance are not certified. Normal installed Model7 and the frozen web artifact
remain unchanged; this is the separate development source.

## MMD increment verification

`python tests/verify_mmd_groups.py` adds12 Python cases and actual PMX worker/UI/
HAS/cold/MP4 checks. The original fixture has compound, nested, signed and mixed-UV
groups. It passes through the ordinary in-app raw-PMX conversion, chooser, shared
editable deform keys, one Undo/Redo, independent body/shot/view/native data,
Simple English/Advanced original identities, whole-group unsupported refusal,
packed/linked/cold Open, editable cyan drawing and ordinary H2641080p24 two-second
movie with exact frame12 PNG comparison. Prepared geometry tail SHA and original
PMX SHA/mtime are verified. This fixture is original authored test data, not an
owner-supplied model with native emotes. Supplied samples inspected here have
vertex morphs but no group morphs; broader native group corpus acceptance remains
open. Unmodified PMD/PMX and VRM converter regressions run separately.

The first native harness passed only a physics flag as placement context and
failed before installing an actor. It now uses the complete context captured by
the real UI. Placement also refuses missing/nonfinite camera settings cleanly,
with explicit state-preservation tests. Failed log/receipt remain separate. No
geometry, pose, motion or pixel tolerance was relaxed. Current accepted scoped
counts are recorded in the progress memo/checkpoint; full verifier wiring is not
a fresh whole-suite pass.

Final current-source MMD wrapper passes39 checks (12Python,24editor/native,3cold).
Expanded common expression suite passes35domain+45editor+5cold=85, actual native
imports pass8unit+43app=51, placement23 and UI23 pass:221 scoped checks total,
zero failures, seven accepted private GPU receipts. Functional source SHA stayed
unchanged across the five final groups. Simple/Advanced screenshots were inspected.
Normal installed Model7 and frozen web remain unchanged; broader full-goal native
expression/fidelity and current whole-suite acceptance are still unfinished.
