# Bounded integration plan

1. Wait for root's current main-source verification to finish and release the
   source/HEAD freeze. Keep a single GPU lease. Fetch/reconcile newer progress;
   if HEAD has moved, repeat the baseline audit instead of assuming this package
   still applies. Current retrieval checkpoint is `2c7320fa5195245fc2bd65ee50a031dbd9daad2a`.
2. Review the nine runtime deltas and final peer-fixture test changes. Verify
   every source byte against `manifest.json`, and each existing destination
   against its recorded current-main hash. Stop on a functional difference;
   five documented CRLF/LF differences are not code changes. The full overlay is
   authoritative, not the normalized review diff.
3. Apply only the sixteen listed overlay paths to the owned development checkout
   after the guards pass. Seven existing runtime files change, two runtime files
   are added, and seven new test files are added. There are no schema, package,
   discovery, lighting, original-input or installed-app changes in this increment.
   Do not copy the prototype's other tests/tools or revert current QA fixes.
4. Adapt the existing private GPU driver into the main `tests` workflow as
   described separately. Preserve its real six-case assertions and private
   isolation protocol. Add the three headless units and explicit graphical
   invocation to the canonical runner; a default parse-only success must never
   stand in for graphical execution. Keep native prerequisites explicit.
5. Verify the port on the actual main project root. Run headless units, the new
   six-case matrix and the existing integration gates in the checklist. Preserve
   failures, no visible fallback, no tolerance changes and no invented hardware
   or human results. Once checks pass, freeze stable source/HEAD for the required
   default canonical; scoped prototype/main replays are not an aggregate pass.
6. Publish source, tests, compact actual evidence, history/master updates and
   stable-ledger scope without promoting the seven external acceptance gates.
   Verify the remote copy before exact disposable cleanup. The old c678 overlay,
   2c strengthening overlay and failed evidence remain retrievable.
7. Prepare a new separate owner-review snapshot from the verified published
   revision when appropriate. Do not patch the old c678 review's Studio or its
   protected recovery. The owner remains unavailable for participation prompts.

## Runtime change boundaries

| File | Bounded change |
| --- | --- |
| app.gd | Own the review reference/epoch, stop before authored operations, route input, and guard queued recovery pixels over the full preview interval. |
| has_project.gd | Stop temporary preview before save and asset-package operations. |
| physics_editor.gd | Construct the review controller in the existing controls. Existing Hair OFF restoration and body Freeze/Record contracts remain. |
| physics_recording.gd | Stop temporary preview before locking original Local/World recording targets. |
| pose_editor.gd | Stop temporary preview before authoring a pose gesture. |
| renderer.gd | Owned final-capture/asset-replacement hooks; native readback lifecycle stays intact. |
| secondary_spring.gd | Extract synchronous construction with an optional private host; retain the original asynchronous creation contract for ordinary simulation. |
| wind_review.gd / wind_review_groups.gd | Session-only declared-group catalogue, linked influences, one owned main-view candidate/private solver, independent checks, cancellation and visibility/input cleanup. |

## Still open after this increment

Pending single/batch helper drafts cannot yet run this preview before Apply. Their
window still uses the existing setup/install lifecycle. Temporary wind checks
do not author **Include in setup** membership or permanent Hair & clothes
exclusions. Phase2's read-only draft context, worker generation/receipt, binding
mapping, pointer ownership and safe Apply behavior remain separate work. See the
retained `reference/PLAN-PHASE2.md`. Native Source jiggle/assembly, lighting,
Discovery and dynamic output resolution are not supplied by this port.
