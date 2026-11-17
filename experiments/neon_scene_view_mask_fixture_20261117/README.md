# Scene-view mask fixture successor

Source-only proposal for the unchanged approved Neon viewport. Do not change product code or its editor mask.

The failed canonical run is retained: Scene106's predecessor executed102 checks with4 failures, all on the unchanged off-frame model color predicate. The source-pinned canvas intentionally composites a62% dark mask over the off-frame scene in Neon. This proposal evaluates that original strict model-color predicate on analytically recovered base RGB, without clamping or normalization. The literal predicate and every other original check remain byte-exact under the reversible source proof.

Each of the four original wide/tall and camera-roll cases gains one independent assertion. It reads the raw SceneSetupView SubViewport texel at the displayed pixel center, requires the original strict base green/blue thresholds, predicts the screen RGB from the source mask and compares that prediction with the actual root-screen readback. The fixed2/255 maximum channel tolerance bounds two UNORM8 writes; it was derived before actual diagnostic samples. It is not a fitted color, exposure, alpha or threshold. Classic light/dark keep their original observed pixel and predict the unmasked raw texture.

The fixture refuses source-pin changes, unknown palettes, HDR2D/non-Compatibility profiles, scaling/fractional translation, canvas/material modulation, nonidentity texture mapping, scene overlays, edge/mask-boundary samples, incompatible readback sizes/formats and translucent sample pixels. Refusal fails the added assertion with its reason; it does not normalize the unsupported profile.

Root staging consists only of these exact replacements after source review:

- `scene_view_smoke.proposed.gd` -> REVIEW/tests/scene_view_smoke.gd
- `verify_scene_view.proposed.py` -> REVIEW/tests/verify_scene_view.py

The wrapper keeps every original process, timeout, log rejection, private-desktop receipt and source-preservation predicate. It adds strict106-check/four-case/composition gates. There is no102-count gate in verify.py or the legacy result gates, so those files need no change. The full158 groups,36 core groups and21 movies remain unchanged. The actual updated GUI parse/execution is UNRUN by this packet; root owns the native lane and must run the ordinary wrapper before any complete successor.

Twenty CPU tests pass. They prove exact additive inverses to both original files, retain the original thresholds, check source constants/profile guards, and exercise independent color arithmetic, conservative quantization bounds, classic identity and negative cases. They do not qualify actual GPU behavior. An initial source-only default-codepage mistake was refused by the exact inverse test; its unexecuted derivative and CPU failure log are retained, and the final candidate was regenerated from the original UTF8 bytes.

No native model data, images, videos, audio, private arrays or output fixtures are copied. The original failure result is scalar synthetic review data. Original full closure and its48 physical receipts are separately preserved by the root failed-full archive; this packet does not reinterpret that run as a pass.

Primary renderer references: Godot4.6 Compatibility canvas rasterizer and canvas shader (URLs in SOURCE_PROOF.json). The inline rect color carries floating alpha. Compatibility LDR2D uses SRC_ALPHA / ONE_MINUS_SRC_ALPHA; use alpha.62, not an alpha8-rounded substitute and not a color-space conversion.
