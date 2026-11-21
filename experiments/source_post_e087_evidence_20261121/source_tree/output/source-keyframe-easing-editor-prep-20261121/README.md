# Camera easing editor and history source candidate

Whole source packet, not adopted. The original preparation is preserved byte-exact under bases/original_preparation/. The Root-fixed math fixture and its source pins are preserved under bases/math_v2/. Ready payload uses unchanged core08aac, corrected math test4ba26a, the original session editor, and the45-control editor/history test. No Lua source was copied.

## Actual and pending qualification

Root actually passed24 pure easing controls with the corrected fixture as part of the separately recorded50-control run; ROOT_CORE_RESULT.json is copied exactly. Its contact-math26 controls are a separate component and are not evidence of actual Miku contact. The editor45 source has received this independent file/function/API review but has not been parsed or run. Real GUI, real Undo/Redo, cold save/open, baked preview/movie equality, performance, keyboard/window handling and ordinary app regressions remain pending. No current application file has changed.

## Root staging

In a fresh owned e087 runtime, verify the three exact source baselines in bases/original_preparation/BASES.json. Install the four payload files. Apply the six exact unique anchors in PATCHES.json to app.gd and renderer.gd only after checking those base SHA256 values. Existing Timeline is unchanged. First run tests/keyframe_easing_math_unit.gd (24 controls, already independently passed) and tests/keyframe_easing_unit.gd (45 controls, UNRUN). Use the usual private desktop launcher and retain/reap every job; no visible fallback.

The editor test uses a small RefCounted app/renderer spy and actual editor methods. It verifies session/keys/video/child-scene invalidation; all13 busy/worker/physics/draft guards; deterministic read-only preview; plan tamper refusal; exact authored endpoints; one existing type=keys command with deep before/after data; every authored key preserved; integer-frame baked samples; existing241-key budget; and no duplicate bake. Its explicit real_app_undo_tested=false is intentional: replaying a spy command payload does not qualify actual app Undo.

## Product scope

Select a camera key and set Arrive/Leave0–100%. Recalculate creates a temporary camera timing preview; it does not edit project keys, metadata or history. Save/capture/movie use authored keys until explicit Bake. Bake creates ordinary editable keys in a single existing history command and removes the temporary recipe. Old Hold/Linear/Ease sampling is untouched with zero controls; nonzero timing on Hold refuses. Original authored dictionaries and unselected segments remain intact; dense integer-frame baking is bounded by the existing241-key limit, with no subframe-equivalence claim.

This is timing along the existing line/rotation path. Spatial arc smoothing, neighboring-body-joint coordination, Motion Feeling and actor-driven hair inertia remain distinct work. The panel is added after Neon camera-inspector restructuring so it stays discoverable; Classic retains the same camera-section container. The optional renderer hook defaults absent/Off and every capture explicitly bypasses it.

Read bases/original_preparation/README.md for the original proposal and six file/function anchor details. SOURCE_REVIEW.json records this review without replacing the original unrun history.
