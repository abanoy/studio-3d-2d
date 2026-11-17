# Compact timeline input-fixture audit

This audit searched all 414 GD test files in the isolated redesign checkout for vertical scroll assignments, alternate scrollbar/deferred/page APIs, row/channel/audio coordinates and real routed input helpers. Candidate families were then inspected against the current compact layout and active-lane reveal code. This is source review, not a formal proof of every UI route or a new runtime pass. No engine, CIM or Git command ran, and the audit agents changed no functional checkout or minimum height.

The parent owns the actual failed `animated_channels` case and its successor. `PRESERVED_ANIMATED_FAILURE.json` retains the original scalar result's hash and 47-check/1-failure count, with all three optional native fixture paths actually executed. No raw native report, model arrays or screenshot is copied here.

## Result for the default full suite

No additional default-full scroll-to-content-end routed-click candidate was found beyond the parent's `animated_channels` case and the previously corrected `object_timing` case. Explicit assignments in the new compact regression intentionally test the negative case before revealing first/middle/last rows. The `multi_audio` assignment scrolls to `audio_y()` for a screenshot rather than asserting an offscreen real click. Many block/clip/audio gesture tests call handlers directly and therefore do not claim a visible routed hit.

`timeline_navigation_smoke.gd` deliberately expands the divider by 220 px before simultaneous ruler/channel/audio gestures. Exposure-edge/tool fixtures start with two drawing rows that fit the short viewport. The larger cel-timing fixture changes to Draw and settles before interaction, which invokes the implemented active-layer reveal. These distinctions avoid blanket changes to unrelated test input paths.

## Focused-suite successors prepared for review

### Movement-path channel inspection

`tests/movement_path_smoke.gd:77`, `:80` and `:82` route real viewport clicks through `event_at()` to Advanced position, rotation and scale channels. Their centers are y38/64/90 for the single expanded model, while Advanced may have a 30 px track viewport. The current focus helper reveals the model's root row, rather than whichever lower channel the test intends to click. The script never reveals those channels first.

`movement_path_smoke.proposed.gd` and `movement_path_reveal.patch` add a dedicated row-reveal helper and five pre-click calls for the two root disclosure clicks and three channel clicks. The helper exposes the existing inner viewport through the outer dock scroll, then scrolls to the actual requested row. Every original assertion and the existing `event_at`, `click`, `click_at`, `drag` and `wait_job` helpers remain unchanged. The exact inverse restores the original raw bytes and CRLF. Inheriting tests that override `run()` do not acquire new input behavior, because the existing shared input helpers were deliberately left untouched.

This standalone movement-path wrapper is not directly registered by the current default `verify.py`. Its successor has not been Godot-parsed or executed. The patch corrects input visibility only and does not promise the entire focused script passes.

### Waveform pixel inspection

`tests/waveform_levels_smoke.gd:27–38` captures Audio pixels at `audio_y()+14` without revealing that row. With no object rows and two drawing layers this is y79, beyond a 56–62 px compact viewport. Audio import does not select an Audio focus lane. `waveform_levels_smoke.proposed.gd` and `waveform_audio_reveal.patch` expose the dock's inner viewport and scroll to the actual Audio row immediately before its existing capture. All assertions and pixel predicates remain unchanged; the exact inverse restores the original bytes.

There is a separate, deliberately unmodified theme expectation: the test searches for classic waveform green `467d45`, while neon draws a different color with alpha. The input-only successor therefore is **not a complete waveform fix or a claimed pass**. A theme-independent rendering predicate or an explicitly scoped classic-theme fixture needs separate review before that focused test can qualify neon pixels. Its wrapper is also not directly registered in the current default `verify.py`.

## Evidence and next action

`AUDIT_SCOPE.json` pins the inspected candidate sources and states the keyword-review limit. `MOVEMENT_PATH_PROOF.json` and `WAVEFORM_INPUT_PROOF.json` pin original/proposed bytes and assertion/inverse preservation. The independent peer's matching findings are in `peer_audit.md`.

Parent should review each optional input patch before applying it after the frozen run is closed. The compact layout stays intact. Retain every original failure and run appropriate actual focused successors with normal private-desktop receipts before claiming a correction. This packet does not authorize or perform an engine launch.
