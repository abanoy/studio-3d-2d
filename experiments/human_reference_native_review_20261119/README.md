# Recoverable native human-reference review recipe

This directory contains authored review code and a reproducible builder. It
contains no private model, geometry array, screenshot, packed project, full
runtime snapshot, or full source-hash inventory.

The coordinator retained the earlier exact `5f0a91e` review separately under
`output/human-reference-native-review`. Its private run reported 23 checks,
zero failures, no errors and one closed private-desktop receipt. Those entry
files and receipts remain unchanged. This archived entry adds an explicit
optional Body Physics refusal check for a subsequently guarded revision;
that new 25-check path is authored and has no inherited execution result.

After committing the runtime and this recipe, build a fresh private review.
Replace `COMMITTED_REVISION` with the exact reviewed commit; the builder has no
implicit HEAD default:

```powershell
& 'C:\Program Files\Python313\python.exe' 'experiments\human_reference_native_review_20261119\build_review.py' --revision COMMITTED_REVISION --output 'C:\a\Programming\cloudflare\has-height-addition-20261119\output\human-reference-native-review-guarded' --fixture-root 'C:\a\Programming\cloudflare\has-acceptance-session-20261111\output'
```

The builder uses `freeze_source(..., runtime_scope=True)` on exact committed
Git blobs. It refuses an existing output, destinations outside this checkout's
output tree, links/reparse paths, changed fixture identities and mismatched
VRM0 provenance. It resolves only the VRM0 role from `wind-review-inputs.json`,
copies only its pinned `scene.glb` and `parameters.json`, preserves nanosecond
modification times and confirms the originals remain unchanged. It adds a
unique Godot profile, authored entry/helper code and a manual owner launcher.
It never launches an application.

Both Python launch helpers recheck output ancestry for symlinks/reparse points
and verify all recorded review entry/helper/override hashes immediately before
launch. They own the Windows launch boundary. The direct GDScript entry also
refuses ancestor links reported by the engine filesystem; use the provided
helpers for the full Windows reparse checks.

The pinned prepared identities are source
`3caa50b76d0f481bb7ee66daeb6ebe7485aefb966140321b599ca60d9d464b56`,
parameters
`0f8f746ca68a821acaf9e502b6895a2f2798d8d1d2bd62569d78deea652fc0ef`,
and original VRM0 provenance
`f7b4573b241b3e91c7c5f58bed342133a4e5f7e0c1125e1cedc49723ace9b288`.
These are identity metadata, not redistribution permission.

After the full graphics lane closes, run the private verifier from the newly
prepared snapshot:

```powershell
& 'C:\Program Files\Python313\python.exe' 'C:\a\Programming\cloudflare\has-height-addition-20261119\output\human-reference-native-review-guarded\Studio\review\verify_native_reference.py' --lease-confirmed --body-guard
```

The helper uses the snapshot's private-desktop `run.command` with
`review/native_reference.gd`, `--verify` and optional `--body-guard`. A complete
successful guarded run emits `NATIVE_HUMAN_REFERENCE` with `checks=25`,
`failures=0`, `status="passed"` and `body_guard_requested=true`. Without that
option it retains the 23-check size workflow. The owner launcher runs only
when a person opens it; automated verification never uses a visible launch.

Checks exercise actual complete-human eligibility, six-foot visible neutral
height within 0.00002 scene units, artist Scale 1, source identity, Simple
controls, relative 0.5/2 geometry and Undo/Redo, packed save/reopen with explicit
model reselection and no remeasurement, screenshot output, original/staged
hashes and modification times, frozen source hashes, and private job/desktop
closure. The two optional checks require the current nonunit reference to
refuse Body Physics before allocation while preserving model data, poses,
intrinsic roots, secondary metadata and topology.

This is a workflow check on an existing VRM preparation. It does not certify
native appearance/physics fidelity, a scale-preserving body adapter, encoded
video fidelity, or owner acceptance. Generated assets/results stay private
under the chosen output directory. `INDEX.json` binds only this public recipe.
