# Wind Review prototype: read-only review

Initial review November 12, 2026, against the frozen exact-85fa482 prototype.
All eleven runtime/test hashes matched `headless-verification.json` at review.
No source, test, native asset or active-checkout file was changed. No graphics
or new runtime checks were run for this review. The recorded 51 + 14 headless
checks remain separately scoped evidence, not a graphical pass.

## Finding 1 — Escape leaves camera navigation captured

**P2; fix before port.** `Studio/src/wind_review.gd:239` consumes Escape whenever
the review window exists. `Studio/src/app.gd:1561` then returns before its normal
Escape cleanup at line 1633. The invoked `stop_preview()` at wind-review line 256
only calls `world_selection.cancel_gesture(true)` when `pointer_pending` is true.
That method (`world_selection.gd:249`) clears pending click/motion, but does not
clear `app.navigating`, `camera_buttons`, `camera_free`, the orbit controller,
canvas middle gesture, or the captured cursor.

Concrete route: start a wind try-out; hold LMB and drag at least four pixels, or
hold LMB plus WASD so World Selection promotes the pending click to camera
navigation; press Escape while still holding the navigation button. The preview
stops, but camera capture remains armed and later WASD/mouse motion can continue
moving the camera. Ctrl/right/middle navigation can have the same result even
when the preview's `pointer_pending` is false. The second Escape closes the
window but still bypasses normal cleanup. Releasing the mouse button eventually
clears capture, so this is a missed cancellation boundary rather than a permanent
lock after every release.

Use the app's existing navigation cleanup before returning the consumed Escape,
or let the original app Escape branch execute after stopping the preview. Preserve
the existing original-cursor restoration and focus-out policy. Do not solve this
by freezing/discarding original physics. Add routed tests for LMB, Ctrl/right,
middle/orbit and the stopped-but-open window: zero camera flags, ended orbit,
cleared middle state, one requested cursor return, and no subsequent WASD motion.
The current fake cancellation test only counts `cancel_gesture()` calls; the
endpoint harness overrides `release_mouse()` to do nothing, so neither covers it.

## Finding 2 — readback interval needs an explicit interleaving test

**P2 static coverage gap; rendered reproduction pending.** The final-capture hook
at `Studio/src/renderer.gd:309` stops an already running try-out, but `capture()`
then awaits a native frame at line 329. Neither `WindReview.available()` (line 53)
nor `context_valid()` (line 57) rejects `renderer.capturing_final`. A new try-out
can therefore be requested between the final-capture entry guard and its GPU
readback, if a caller uses final capture without holding `app.exporting`. The
temporary candidate is outside `world_runtime`, so final world evaluation does
not hide a candidate created after that evaluation. The ordinary movie exporter
does hold `app.exporting`; this is not a demonstrated movie-export failure.

The recovery guard at `app.gd:2397` checks only whether a try-out is active when
the callback completes. Queue a recovery readback, start a try-out, and stop it in
a `frame_post_draw` callback ordered before native-frame dispatch: the captured
GPU frame can have contained the candidate even though the completion predicate
now sees a stopped preview. This callback-order route is a static counterexample,
not a newly measured pixel failure. The existing 14-check harness tests only
active-at-completion, and its capture endpoint exits before a real frame wait.

Add actual private-GPU interleavings: attempt restart during pending final
capture; and stop/close between drawing and a queued recovery completion. Reject
preview entry for an outstanding final-capture scope, and invalidate queued
recovery pixels with a preview generation/epoch when a try-out starts, or enforce
an equivalent ownership protocol covering the entire readback interval. Keep
scope counters balanced on cancellation. Do not broaden rendered-pass claims
until these cases have actual image/receipt evidence.

## Finding 3 — new chain bound is narrower than the existing import contract

**P2 compatibility edge; no supplied-model failure observed.**
`Studio/src/wind_review_groups.gd:79` rejects a chain above 256 joints. The existing
secondary parser accepts up to 512 (`secondary_rig.gd:106`), and the common model
allows up to 512 bones (`model.gd:231`). A valid single 300-bone VRM1 chain can be
loaded and simulated by the existing route but is rejected by this review as an
invalid motion group. The plan does not disclose a new 256-joint review profile.
Align the review guard with the existing bounded contract, or explicitly justify
and name a separate resource refusal. Test the accepted boundary and the next
refused value. This does not establish that any supplied model reaches this edge.

## Isolation and lifetime observations

The candidate has its own model, spring runner and private physics space, with
no borrowed primary passed into the temporary simulator. Only owned mesh
visibility is saved/restored, with independently parented model roots excluded.
Source metadata, authored state and the live simulation registry are read rather
than replaced. Selected/excluded chains are structurally filtered; linked skin
or hierarchy dependencies are coalesced. Closing synchronously hides the
candidate before deferred node deletion and disconnects its owned warm-up
callback. Renderer hook cleanup compares callable ownership before clearing.
These code observations support the intended design; they do not replace the
pending motion/pixel/native/lifetime tests in `PLAN.md`.

No additional concrete original-physics disposal or whole-world restore defect
was identified in this phase-1 implementation. The pending-helper integration
and permanent per-group authoring settings remain separate unimplemented work.

## Authorized private fixes and headless counterfactual

The parent subsequently authorized fixes inside this private prototype only.
`before-review-fixes/` preserves all eleven old source/test files, their hashes,
the initial review and original manifests. The active checkout remains untouched.

Escape now runs the real app navigation cleanup, including its ordinary cursor
return request, after stopping/closing this try-out. Both availability and the
restart context reject an outstanding `renderer.capturing_final` interval.
Starting a candidate increments an app-local generation before any temporary
mesh becomes visible. Queued recovery requests carry that generation; completion
releases the scope but refuses pixels if the try-out started in between, even
after it stopped. Fresh recovery remains eligible afterward. The five-argument
direct completion endpoint is retained for existing isolated callers/tests;
production queued requests always pass their explicit sixth generation argument.

Group validation now matches the existing 512-joint/512-total-rotator/128-chain
limits. No native rig or global normalizer limit was relaxed.

The final same-oracle counterfactual records **29 checks / 21 failures** against
the exact old eleven files, without parser, engine, leak or missing-method errors.
The fixed runtime gives **51 + 14 + 29 checks / zero failures**, plus a successful
app parse. The 29-check oracle uses actual app Escape/release code and synchronous
try-out construction, with a fake native readback that records whether pixels
would be consumed. The first two draft-oracle runs had fixture notification/
cleanup errors; their logs are retained and are not used as clean counterfactuals.

`headless-reviewfix-verification.json`, `audit-counterfactual.json`,
`review-fixes.patch` and `runtime-review-reviewfixed.json/.patch` identify the
current source and failures. The original 65-check proof describes pre-fix source.
No graphics, actual Windows cursor movement, rendered recovery/final pixels,
native motion or movie have been tested. Those remain required before any port.
