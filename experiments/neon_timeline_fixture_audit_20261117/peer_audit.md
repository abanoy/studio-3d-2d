# Peer audit of compact timeline fixture assumptions

Source-only audit of the current review checkout `C:/a/Programming/cloudflare/has-neon-review-20261116-c2d52ff`. No engine, real input, CIM or Git calls ran. No review checkout source or assertions were edited. The root is separately handling the actual `animated_channels_smoke.gd` failure.

Search scope: all `tests/*.gd` for vertical/horizontal scroll assignments, scrollbar/range values, max/page values, `set_deferred`, `ensure_control_visible`, wheel/pan/page/home/end input, row/channel/layer/audio geometry helpers, and routed click/drag helpers. Reviewed the relevant inherited `event_at()` path and test context, distinguishing direct `_gui_input()` component tests from viewport-routed UI tests.

## Additional candidates in focused suites

### Movement-path Advanced channel clicks omit row reveal

- `tests/movement_path_smoke.gd:16–27` routes `click_at()` through the owning viewport's actual `push_input()`.
- `:74–82` changes to Advanced, then clicks the position, rotation and scale child rows without revealing those rows or enlarging Timeline.
- With one expanded object and `ROW_HEIGHT=26`, the click centers are local y=38, 64 and 90. The test has no explicit Timeline expansion or inner/outer viewport containment check.
- Current `src/app.gd:3718` permits the Advanced inner viewport to be 30 px tall. Changing Advanced mode clears `timeline_focus_key` at `:2916`; `sync_timeline_focus()` only reveals the selected object's root row at `:2888`. It does not reveal the three child channels.

This is a concrete clipping candidate when the dock leaves less than the required channel height. It is not an observed runtime failure. A later fixture successor should reveal each requested channel by its geometry and establish containment in both scroll viewports before routing the existing click. The compact default should remain intact.

### Waveform pixel test omits Audio-row reveal

- `tests/waveform_levels_smoke.gd:24` changes the horizontal timeline scrollbar only.
- `:27–38` captures screen pixels at `view.global_position + (..., view.audio_y()+14)` without revealing the Audio row or enlarging Timeline.
- With no objects, two drawing layers and a hidden header, `audio_y()` is 65 and the sample center is y=79 (`src/timeline_view.gd:169–178`). A compact 56 px track viewport can clip this sample into the footer or outside the track viewport.
- Importing/selecting audio does not add an Audio case to `sync_timeline_focus()`; its focus lanes remain layer/camera/model (`src/app.gd:2854` onward).

There is also a separate theme expectation: this test samples classic green `467d45` at `:28`, while the neon waveform path draws `Color(0.239,0.863,0.592,0.85)` at `src/timeline_view.gd:722`. A later focused fixture review must distinguish visibility from that independent visual expectation. No color or threshold was changed here.

Both candidates are invoked by their dedicated Python wrappers (`tests/verify_movement_path.py` and `tests/verify_waveform_levels.py`); neither is in the current `tests/verify.py` default case list.

## No further default full-suite candidate found

- `object_timing_smoke.gd:125` now reveals the last object's semantic `row_y()` position; its outer viewport is exposed first at `:123`.
- `neon_compact_timeline_reveal_smoke.gd:77–80` deliberately demonstrates the content-end negative case, then reveals first/middle/last requested rows at `:90–96`.
- `multi_audio_smoke.gd:104` uses `audio_y()` for a final screenshot, not a routed click; its earlier timing gestures directly exercise `_gui_input()` and are not viewport-clipping tests.
- `timeline_navigation_smoke.gd:15–18` deliberately expands Timeline before its simultaneous ruler/channel/audio gestures. Its `nav.scrollbar.value` assignments pan time horizontally.
- Drawing-row suites (`cel_timing`, `cel_clipboard`, `cel_exposure_edge`, `cel_timing_tools`) target the active drawing layer in Draw mode; the focus helper has an active-layer reveal path. No additional proven clipping condition was found in their inspected setup.
- Late-clip and Scenario C routed model drags select the intended model first, allowing the model-root focus path to reveal that semantic row. Other inspected model block tests directly call `_gui_input()`.
- Remaining scrollbar and wheel searches referred to horizontal time navigation, canvas/reference navigation or inspector/dialog controls revealed with `ensure_control_visible`, rather than another content-end timeline click.

This is a source finding, not a claim that unrun suites passed or that every possible geometry is covered.

## Source identities read at completion

- `src/app.gd`: `88871ebd831d5a466b31336282a9bb53f264653dd5ff299fb10dc90a3080dd67`
- `src/timeline_view.gd`: `f2b3e712b8ff0d5c67914c3ef783ad770abab30c8745cc0bae40c445debcc48e`
- `tests/verify.py`: `14e6fc7b7e8c914b301e8e5d4d590ca0b2398a7abbd65cac0f6159f99de96048`
- `tests/movement_path_smoke.gd`: `d53d556fffe5eff0e8d97ddb7d565ffa0a7b2f0b5d0b309ea6859c9698aba8e2`
- `tests/waveform_levels_smoke.gd`: `28b9be24ede2068f562458584830df2a65d8ff6db0c1f863e1f97f3606f59621`
- `tests/timeline_navigation_smoke.gd`: `8067470a028abcb91bd9336bac81b6cf2a636d39873e8e50596f1e0707b720c1`
- `tests/object_timing_smoke.gd`: `d8cd3048e23db2c5f94798fb8aac0df66a26262fb5d10c367baba3e3ff8eb267`
