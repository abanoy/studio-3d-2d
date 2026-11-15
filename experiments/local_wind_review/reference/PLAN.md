# Local wind review: isolated phase 1

This copy starts at exact Git revision `85fa482b3ef1ed752e8a97191b5ea7b235cea7aa`.
Nothing here has been ported into the active checkout or the owner's review.
The controller and tests are a disposable prototype pending independent review
and private graphical verification. No native/private source asset was changed.

The initial review found Escape cancellation and readback interval gaps, plus a
narrower chain bound. Authorized private fixes now pass51+14+29 headless checks
and app parse, with the same29-check oracle failing21 times on the old source.
Use `runtime-review-reviewfixed.json/.patch` and
`headless-reviewfix-verification.json` for current source; the older manifests
describe the original65-check prototype and are preserved as historical proof.
See `REVIEW.md` for exact scope, fixes and still-unrun graphics.

## Implemented in this copy

- Separate focused row and checked wind groups. Checking does not change
  **Include in setup**, a rig declaration, scene metadata, history, or animation.
- Already declared VRM0, VRM1 and HAS chains share structural identities.
  Hierarchy dependencies and actual shared skin influences form explicitly
  linked groups. A weighted native group cannot promise independent surface
  exclusion without changing its weights.
- One disposable candidate appears in the existing main view. The source's
  owned meshes are hidden individually; independently parented child models are
  excluded from that traversal. No second camera view is introduced.
- The real spring implementation constructs only checked chains in a private
  physics space. The existing unsteady airflow calculation receives a local
  temporary field, with no authored fan, global wind registration or Record
  target. The original model and every other simulation remain separate.
- Candidate rest pose samples recorded/authored hair channels rather than
  copying the source's live hair offsets. Actual local body poses remain the
  baseline while body Physics is active. A selected hair/body binding conflict
  refuses preview rather than taking over a body joint.
- An owned one-shot callback warms the synchronous construction without adding
  a nested coroutine. Stop/cancel/close immediately hides the candidate,
  disconnects warm-up, disposes its own solver and restores owned visibility.
- Save, asset Save, Record, playback, frame changes, export and source replacement
  have synchronous stop guards. Native final capture has an independent guard.
  Recovery skips starting preview pixel capture and releases queued readbacks
  without pixels if a wind try-out is active.

## Evidence and limits

`headless-verification.json` records the fresh checks, exact commands and eleven
source/test hashes. `runtime-review.json` and `runtime-review.patch` identify the
nine runtime changes. The patch compares line endings consistently; the raw
active-checkout hashes are preserved independently and checked unchanged.

Headless checks establish filtering, real skin linkage, private solver ownership,
recorded/excluded baseline preservation, peer identity/visibility and cleanup.
The endpoint harness invokes the actual Save/Record/export/play/frame/replacement
and recovery/final guards, deliberately stopping downstream work before any
worker, file writer or unavailable native viewport. These are not rendered
motion, saved-movie or private-desktop proofs.

Still required before port: private main-view startup, real selected-chain
motion and excluded-chain stability under wind, original body motion continuing,
strong fan flutter, linked native Back hair plus configured ribbon, source
switch/cancel during warm-up/running, immediate close, Ctrl/WASD/middle/right
navigation, final/recovery pixels, source/media/history preservation, and the
original focused helper/physics/readback regressions. GPU remains reserved for
the active checkout's canonical verification until the root agent releases it.

## Separate later phase

Integrate pending helper setup plans into the non-freezing try-out lifecycle only
after this declared-chain path is proved. Persistent Hair & clothes per-group
inclusion/exclusion is a separate authoring/schema/Undo decision; this prototype
does not implement or claim it.
