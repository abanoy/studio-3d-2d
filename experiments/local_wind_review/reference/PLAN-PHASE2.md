# Pending helper wind preview: phase 2 design audit

Read-only audit of the exact-85fa482 helper editor/worker and the frozen phase-1
prototype. This is a proposal, not implemented behavior. No runtime, test, active
checkout, source asset or graphical session was changed for this audit.

## Smallest complete path

Let an already paused timeline review pending single/batch setups while existing
body/hair simulations continue. Build the reviewed setup into a disposable worker
folder, import it into Wind Review's existing main-view candidate, and simulate
only separately checked wind groups. Do not call the installation path at all.
Keep the current single/batch Apply behavior and its one-transaction history path
separate from try-out preparation.

There are three independent states: the focused source region, **Include in
setup**, and temporary wind inclusion. Build every reviewed setup member so that
turning off a temporary wind check does not delete a configured joint or change
the proposed asset. Empty setup membership retains the existing focused-single
workflow. After import, derive wind groups from the actual candidate declarations
and disclose every linked chain; map draft source regions to those groups using
the generated reports and original source-node bindings, never row order/name.

Host the try-out controls in the existing helper draft window. Reuse Wind Review's
controller/main-view candidate rather than opening a second inspector/renderer.
Expose explicit refine versus running-try-out state: changing a patch, attachment,
control point, setup membership or mode stops the candidate before revising its
request. Stopping returns the draft controls and their exact prior selections.

## Concrete refactor sites

- `secondary_helper_editor.gd:67 open`: remove implicit `freeze_all()` only after
  adding a read-only draft context. Gate entry while playing/drawing/dragging or
  recording rather than finishing an active gesture and thereby authoring it.
  Capture active actor/root instance, source SHA + nanosecond worker stamp,
  original authored world/revision/frame, source-node bindings, and one normalized
  shape snapshot. Live FK/body motion is not an authored-world invalidation.
- `secondary_helper_editor.gd:133 _process`: replace the blanket close-on-any-
  simulation rule with the shared context guard. Pending physics creation must
  settle before importing the try-out. A primary/body drive overlapping a checked
  wind rotator refuses that preview; it must never be detached or disposed.
- `proposal_entry/cache_included/queue_changed/refresh_inclusions:248–309`:
  preserve deep-copied reviewed requests and `preview_ready`. Add a distinct draft
  generation/request digest; every setup edit invalidates the candidate and its
  mapped wind IDs without silently changing setup membership.
- `launch/completed:114–228`: route a preview-purpose build result to candidate
  preparation, not `install()`. Keep the exact existing `build`, `batch_build`,
  `source_check`, request precision, bounds, shape-default comparison, overlap
  refusal and all-or-nothing batch publication. A preview receipt should bind the
  source identity, full reviewed request digest and final candidate SHA for both
  single and batch paths. Existing single Apply semantics need not change.
- `tools/secondary_helper_worker.py`: retain one owned process/job directory;
  return/verify that preview receipt around the existing builder. Existing
  `source_check` gives the exact source SHA/ns check; perform it again before
  accepting/importing a result and validate source identity after import. A
  generated GLB is temporary output, never a managed import/origins/history entry.
- `tools/secondary_helpers_batch.py`: reuse existing `plan/review/build` unchanged
  in meaning. Do not rebase the original reviewed SHA outside its existing private
  sequential composition. Preserve all per-item reports and shape settings,
  including `source_morph_defaults`; do not merge unlike snapshots.
- `wind_review.gd`: accept an explicit draft-provider/context rather than requiring
  a standalone declared-chain window. Its guard must refer to the original actor
  and source, while the solver catalogue belongs to the derived candidate. Keep
  owned synchronous construction/private space/cancellable callbacks, original-
  only visibility traversal, local airflow and all phase-1 stop/capture guards.
- `draw_preview/guess_part/patch_pointer/global_patch_event:383–541` and
  `close:590`: arbitrate the existing canvas pointer lease. Refine mode uses source
  bounds/patch boxes. Running wind mode cancels any pending patch gesture and owns
  navigation-only scene input. Stop restores the helper pointer only while its
  owner/context still exists; helper close stops wind first and clears only its
  own pointer. Ctrl/WASD/middle/right and off-frame rejection remain unchanged.

## Correct candidate baseline and bindings

Import a minimal temporary model definition, not a deep copy of all source
metadata. In particular, a body pose library validated against the original SHA
must not be transplanted to a derived SHA. Keep the original library untouched.
Use a static snapshot of the current full morph weights (explicit zero/default
semantics), then source-authored/recorded hair pose plus actual live body FK.
Newly generated joint IDs start at identity. Never capture the source's live hair
offsets as the candidate rest pose.

Before showing the candidate, prove every retained source bone/node binding and
base transform still maps to the same original source node; refuse missing or
changed bindings. Original animation is evaluated by the original model and read
into the candidate baseline each step, so this phase need not copy its animation
schema or pose-library metadata. Root/global placement follows the original live
transform. Unchecked chains are omitted from the solver altogether, preserving
their recorded motion rather than merely applying zero wind to gravity-enabled
chains. A native/shared chain may include several source regions and cannot offer
independent region exclusion without reweighting.

## Cancellation and acceptance boundaries

No nested worker/spring `await` chain is needed. Poll the existing owned worker;
use generation + root/context + request digest to reject late completion. On an
edit, close, seek, save, record, export, replacement or timeout, synchronously stop
and hide the main-view candidate, disconnect warm-up, release owned input and
visibility, and invalidate the job token. Kill only its owned running process.
Do not remove a work folder while the process could still publish into it; retain
or prune it only after confirmed exit and bounded path validation. Late results
can affect only that private folder and can never install a scene.

The phase-1 final native-capture guard and explicit recovery start/completion
guards must cover a helper-hosted draft too. A nonexclusive window alone does not
block recovery pixel capture. Existing original/peer simulations continue; no
world snapshot restoration may rewind them on preview stop.

**Apply is a separate limitation:** current `install()` calls `restore_world()`,
which clears every physics instance and replaces actor roots. Simply moving
`freeze_all()` from Open to Apply would mutate the world before its snapshot
guard and can bake unrelated live poses. A scoped first version should refuse
Apply while real simulations/physics creation are active, while still allowing
the non-freezing try-out. Preserve the existing authored-world conflict guard.
Supporting Apply during ongoing physics needs a separately reviewed transaction
that prepares before commit and preserves/rebinds every primary/peer; it is not a
small preview-only change and must not be smuggled into this increment.

## Acceptance matrix before port

| Case | Required observation |
| --- | --- |
| Focused single, empty setup set | Original precise controls produce the same candidate; focus alone never checks wind. |
| Two disjoint weighted plans | Both setups exist in the candidate; unchecking wind leaves that setup and its authored baseline intact. |
| Native Back hair plus ribbon | Original bindings/weights preserved; linked affected regions disclosed; existing chain history unchanged. |
| VRM0/VRM1/HAS plus new helpers | Existing declarations retained; duplicate comments/reorder cannot misidentify groups. |
| Nonzero shape defaults, corrected points | Exact complete snapshot/control precision; unlike shape settings or stale digest refused. |
| Live body, source hair and peer simulation | They keep advancing; candidate excludes live hair offsets and follows actual body/root baseline; no borrowed disposal. |
| Body/checked-hair binding conflict | Friendly refusal with no change to original body, setup requests or peer state. |
| Worker failure/later batch failure/import refusal | No displayed partial candidate, managed asset, authored edit, history entry or source change. |
| Refine during build/warm/run | Old token/result rejected, own candidate restored/removed, refined request needs review again. |
| Close/seek/save/Record/export/source switch | Synchronous cleanup before authoring/capture, no stale callback or queued preview pixels. |
| Draft box/direct pick and navigation | Correct source list/patch ownership in Refine; clean pointer restoration; Ctrl/WASD/middle/right work in both states. |
| Apply while real physics active | Refused safely in the scoped preview increment; no implicit freeze or lost primary/peer. |
| Apply while stopped | Existing one Undo/Redo/save/reopen behavior and all original helper/patch/batch assertions remain intact. |

Persistent per-group **Hair & clothes** inclusion/exclusion remains separate from
both setup membership and temporary wind checks. This audit adds no schema,
permanent setting, authored fan, Record target or global wind behavior.
