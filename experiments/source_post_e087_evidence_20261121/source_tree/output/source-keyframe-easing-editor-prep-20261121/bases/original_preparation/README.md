# Camera easing — source candidate, not adopted

This first increment gives camera keys numeric Arrive and Leave timing controls. It is original HAS code informed by a primary-source review of Stop Motion Helper, not copied Lua. The verified research and license boundary are recorded in ../stop-motion-helper-easing-research-20261121/.

Current production source, the owner’s review build, and all earlier candidates are unchanged. No code in this folder has been parsed or executed by its authors. Root must qualify isolated controls, actual editor behavior, Undo/Redo, save/cold-open and movie output before adoption.

## Small usable scope

The panel appears below the existing camera inspector. Select an authored camera key, enter Arrive / Leave as percentages from 0 to 100, and store its timing. Arrive affects the segment before that key; Leave affects the segment after it. Endpoint-only controls are disabled. The actual recipe stores normalized amounts 0..1.

Preview / Recalculate creates a complete bounded session plan from the unchanged authored camera keys. It does not add keys, change project metadata, write files or create Undo entries. Scrubbing and playback use the temporary camera sampler. Discard removes the plan and evaluates the original camera at the current frame. A source-key, scene duration, video settings or project-session change invalidates the preview. Recalculate is deterministic and does not accumulate generated helpers.

Save and renderer capture continue to use ordinary authored keys. The panel states this explicitly: temporary easing must be baked to appear in a saved project or movie. Capture bypasses the optional preview sampler, including PNG sequences. This is a deliberate first-increment limit, not persisted procedural animation.

Bake inserts one ordinary camera key at every missing integer frame of affected adjacent segments. It retains every original key dictionary, including its interpolation mode and any extra metadata; unselected segments remain unchanged. Generated keys use existing Linear interpolation. It adds one existing type=keys history command, with deep before/after snapshots, then disables the temporary recipe so it cannot apply twice. Ordinary Undo/Redo and project serialization remain the existing paths. It refuses before mutation if the result would exceed the current reader’s 241-key limit.

The integer-frame camera path is sampled; no subframe-equivalence claim is made. Quaternion sampling retains the existing normalization and shortest-arc interpolation behavior. Root must verify numerical replay and actual movie frames. A long selected segment may need a shorter selection to fit 241 keys; the limit is not raised.

## Original timing policy

The bounded monotone Hermite time map has start slope (1 - Leave) and end slope (1 - Arrive). Both zero returns the original time parameter exactly. Both one yields smoothstep. The result then passes through the segment’s existing Linear or fixed Ease mode. This adds numeric timing to the existing mode rather than silently redefining old projects. A nonzero control on a Hold segment refuses with an explanation; untouched Hold remains unchanged.

This is timing easing along the existing position line and quaternion path. It does not smooth a spatial spline, coordinate neighboring body joints, add Motion Feeling anticipation/overshoot, change face weights, or provide moving-frame hair inertia. A later model/shape adapter can reuse the independent timing policy after its own source-time/clip ownership and key-budget qualification. No new project version or ignored metadata field is introduced here.

## Source layout and qualification

- payload/src/keyframe_easing.gd: pure compile, bounded timing map, baseline/plan drift checks, sampling and all-or-nothing Bake plan.
- payload/src/camera_easing_editor.gd: session UI, exact current-scene ownership, one existing Undo command and explicit temporary-state lifecycle.
- payload/tests/keyframe_easing_math_unit.gd: 24 authored isolated math/budget/legacy/ownership controls. It depends only on these new core and unchanged src/timeline.gd.
- payload/tests/keyframe_easing_unit.gd: separate preview/editor/history controls being authored by Oracles; do not infer a count or pass until frozen.
- PATCHES.json: six unique exact-baseline anchors. Three app anchors install and route the optional sampler; three renderer anchors add the default-off hook and capture bypass. The app editor is set up after the Neon camera inspector rebuild, so its visible controls are not accidentally moved into Advanced-only details.
- bases/: byte-exact current app, renderer and Timeline source. BASES.json pins their provenance. No historical assertions are replaced.

Root can first stage just core + math test in an isolated current-source copy and run the Godot headless script res://tests/keyframe_easing_math_unit.gd through the existing private component coordinator. Expected marker is KEYFRAME_EASING_MATH_UNIT with checks=24 and failures=0. Authored status remains UNRUN until Root records an actual result. Full editor qualification additionally applies the six anchors to the exact baseline and stages the editor unit. No app/native/GPU/Git command is executed by this preparation.

After actual component and GUI qualification, adoption requires the normal changed-source tests/full verification. Existing Motion Feeling, camera K key/delete, legacy interpolation, sequence-child rules, body/shape formats, native originals and all owner assets remain outside this patch.
