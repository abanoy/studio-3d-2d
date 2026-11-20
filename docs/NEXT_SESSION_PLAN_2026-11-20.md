# HAS continuation — November 20, 2026

## Scoped addition verified; complete Windows suite next

Worktree `C:/a/Programming/cloudflare/has-body-addition-20261120`, branch
`codex/reference-body-20261120`, base/main `ab62adff5f6961d8605f15c79a01a0215c9c5425`.
Scoped verification is complete. Commit/push/readback and the fresh complete
Windows suite are next. Do not call the current source a full-suite PASS yet.

Implemented the direct reference body plan in `src/reference_body_plan.gd` and
`physics_rig.gd`: metre shape/threshold/margin/anatomical planning, inverse bone
offsets, unit joint axes with retained pivots, complete validation before nodes.
Nonunit skeletons use it even when source bone scale compensates to unit world
bones. Reference-free/genuinely unit paths retain their existing behavior.
No `app.gd`/theme/schema/original source asset edits. See `reference_body_physics.md`.

The independent real-engine mechanical suite passes **1273 checks** total:
admission71, planner71, anatomy75, mechanics1039/nine fixed-tick cases, existing
recording17. Exact final run: `output/reference-body-units-1795193652100132800`.
Max world position error1.724e-6m, collision-surface error1.222e-6m,
canonical FK error1.565e-6m, angular error3.554e-7rad. Raw .001/1000 encodings,
rotated/translated B0, artist/static-parent/root-bone compensation and source
helper scale1.25 included. Defensive coordinate ceilings are not precision claims
for every possible world position/size.

Actual public editor writer passes72 checks: .5/1/2 shapes/contact,
viewport grab/lift/throw, Freeze/Undo/Redo, body/hair lifetime/cancellation,
rational25/2 Local/World Record, four packed saves and12-frame1080p H264 movie.
Independent cold reader passes21 and exact Python archived-definition checks for
all4projects. Neon and classic both pass, including parent18writer/6cold.
Earlier writer63 is historical.
Existing legacy physics regression passes41 with its optional native fixtures
absent in that first probe. Complete native six-case VRM0/VRM1 × .5/1/2 wrapper
passes23writer/9cold per case, originals/stages hash+size+ns-mtimes unchanged.

Final scoped run `output/reference-body-scoped-1795194059198769800` passes in
265.3367374seconds. All1059 source/launch-driver files preserve exact raw bytes
and ns-mtimes. All24actual private jobs close with confirmed placement and no
foreground/switch. Existing reference suites44writer/3cold also pass both themes.
Public evidence/source packet: `experiments/reference_body_20261120`; benchmark:
`docs/benchmarks/reference_body_2026-11-20.json`. Source tree content SHA256:
`9b97f7160b67c745cbf3eb58e479126dfa0f3115b1c9b06aa98aa397c3a6831a`.
The aggregator `finalize_scoped.py` is postprocessing, outside those1059 files.

## Recording bug reproduced and corrected

Actual animated-parent oracle initially fails14/2: held live root drifts only
5.365e-7m, but recorded/reopened root drifts **0.210010573m**. Corrected scoped
reference recording retains exact affine A=heldRootWorld*inverse(C*B0), then uses
inverse(parentWorld(destinationFrame))*A for each ordinary artist-root key.
It validates destination finite positive-uniform unsheared representability,
snapshots ancestor data, guards held-root/target/parent drift at tick and build,
checks parent lookup/cycles, and clears private maps on release/failed start.
Rational phase, legacy/unparented samples and saved schema are unchanged.

Repeat14/1 reduces BOTH recorded/reopened root error to5.365e-7m; remaining check
compared original source path against legitimate packed extraction path. Test
now compares portable parent data plus independently verified source hash/bytes.
Extended parent writer18/cold-reader6 passes in BOTH themes, including next-tick
and immediate-Stop ancestor mutation refusal. Recorded, warm-reopened and
separate cold world-root error all remain5.365e-7m against the .2mm gate.

## Cold-reader diagnostic, not a waived product failure

Two public wrapper attempts stop at overly strict double-string comparisons.
First compares a fresh Vector3 float32 sample with expected JSON parsed by Godot,
which differs by one double ULP (6.617e-24 in two shin components). Keeping writer
canonical strings fixes that computed-pose case, but frozen direct data reveals
Godot-loaded scalar differences too. Python independently proves each raw packed
pose equals the original writer pose **exactly** for all three frozen cases;
full-precision persistence is already correct. Source-native float32 values,
skin bounds and exact preview pixels remain identical.

Two independent strict gates now pass: Python compares complete
packed authored definitions against the raw writer snapshot (excluding only
source/path relocation), and Godot compares pose/root vector/quaternion native
float32 bytes exactly, with exact root scale and key identities. No epsilon or
product serialization workaround is justified. Preserve the failed artifacts:
`output/reference-body/neon-1795193360601077800` and
`output/reference-body/neon-1795193598937032800`. Fresh writer/reader repeat is
completed successfully; old expected files lack the new definition metadata.

## Next concrete actions

1. Scoped Neon/classic72/21+parent18/6, six native23/9 cases and old reference44/3
   regressions all pass. Do not repeat them without a source change/failure or
   the required complete-suite context.
2. Run the complete Windows suite, including affected existing physics/recording/
   secondary/framing behavior. `tests/verify.py` now integrates
   admission71/planner71/anatomy75/mechanics1039/nine ticks, both new workflow
   themes and native wrapper. Keep every old failure/skipped scope explicit.
3. Stage only declared legacy inputs using
   `experiments/reference_body_20261120/stage_legacy_inputs.py`. Actual13files,
   32,095,990bytes now copied with exact original/staged hashes and ns mtimes,
   including the optional PMD pose pair. Destination guard was reviewed/repaired
   before writes to reject links/reparse/hardlinked files. Originals untouched.
4. Commit exact verified source/tests/scalar evidence/docs/ledger/history using
   `git -c core.autocrlf=false add` on explicit files only. Never stage generated
   tracked output reports, bytecode or private artwork. Run full Windows verifier
   with `experiments/reference_body_20261120/run_full.py --revision <commit>` plus
   explicit approved fixture/sourceio paths. Coordinator retains/reaps child,
   checks exact Git source membership/raw bytes+after identities and private jobs.
5. Update final results/history and stable ledger evidence, push main without
   force and independently fetch/decode/hash every changed remote file. Only then
   clean disposable owned generated artifacts; protect originals, existing
   installation, prior reviews, shared tools and earlier dirty checkout.

All62 formal IDs/statuses and52/54 implementation/55/62 acceptance remain.
Human/device/artist/clean-offline observations remain deferred without owner
questions. The normal-source fidelity/reconstruction and larger discovery/light/
model-standard roadmap remain separate followups in the consolidated master.
