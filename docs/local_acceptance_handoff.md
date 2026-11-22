# Target acceptance handoff — current Windows status

## Current Windows checkpoint — 2026-11-21

Frozen published `5d37647c0004849247239817364e093c010eddd6` passed the canonical
Windows Full verifier: 183 groups and all 21 movie groups, with 1,189 functional
source files unchanged and 259 unique private jobs closed (260 receipt paths).
The historical `hecatia.kra` fixture was later supplied; all 13 declared original
fixture files remain hash/size/timestamp exact. See the
[completed Full5d evidence](../experiments/integrated_full5d_20261121/summary.json).

Later published `43dbdecc759e971a80f0d1e468e1e7d1e3b9ed2b` includes separately
qualified focused VoxelGI and generated-gravity/control work. Those later results
do not extend the 183-group Full pass to newer source. Formal implementation
coverage remains **52/54** and acceptance closure **55/62**; human/device/install
and native appearance limitations remain open. The limited Junko setup still
retains its 13/14 quality failure and does not establish full-hair settling.

Use [current Windows follow-up and evidence](windows_acceptance_followup.md) and
retrieve the latest independently verified `origin/main` at pickup. The current
local review is `C:/a/Programming/cloudflare/HAS-Review-Gravity-43dbdecc`: 1,214
source files, three generated projects and one LOCAL PRIVATE limited-Junko project.
Its normal interactive shortcuts are prepared; headless main startup passed.
That startup is not private-project import, rendered GUI or owner acceptance.
See [the source-pinned review receipt](../experiments/generated_motion_publication_20261121/summary.json).

The remaining 53.6 MB browser residue and 6.88 GB completed Full5d clone were not
removed: automatic approval review rejected their exact cleanup actions, and direct
permission is pending. Do not retry or work around those rejections. Preserve owner
originals/projects, review copies and installed/shared tools. The Gravity review's
external SourceIO dependency under `has-neon-review-20261116-c2d52ff/output/dependencies/`
and existing Blender runtime remain protected; they are not disposable review caches.

## Historical November 9 handoff scope — not current pickup prerequisites

The remainder below preserves the November 9 baseline, older failures/skips and
then-open exercises. Its old fixture-availability, Full, score and cleanup wording
is historical. Current status and pickup requirements are the checkpoint above
and `windows_acceptance_followup.md`; no acceptance gate is promoted here.

Implementation/evidence baseline: `90ab1b30bd9b80814ddaac3bbdd213ec0b5e6b3f`.
It includes the preceding cutout fix `38a72ee6aa65c0fec311613fa197b7417c1eda84`.
Use the latest pushed `origin/main`, which also contains this handoff and updated
ledger. Record `git rev-parse HEAD` and the matching remote revision at pickup;
the final cloud message supplies the exact published tip.

This is not full product acceptance. The ledger remains 52/54 implementation
groups and 52/62 formally closed acceptance conditions. Two native capability
conditions and eight target/device/human gates are unclosed. A local worker can
run Windows software tests; it cannot invent missing files or human observations.

## Repository progress and local cleanup

Owner clarification, 2026-11-09: every completed increment's new source, tests,
findings and compact progress/evidence must be committed and pushed to this repo.
Verify the remote copy before removing that task's disposable local generated
outputs, staged copies and caches that no pending case needs. Record cleanup in
the next checkpoint. Later workers must clone/fetch/download progress from the repo.

At assignment end, push/verify the final state and retrieval commit, then remove
the session-owned isolated checkout/worktree and disposable staging files once
no pending work remains. Protect owner originals/projects, the existing install,
shared tools and final deliverables without a verified backup. Private artwork
must not be uploaded merely to make cleanup possible.

The small [Windows worker packet](handoff/windows/START_HERE.md) carries this rule
and the local continuation goal; its ZIP is in `docs/handoff/`.

## Completed cloud work to preserve

- Exact scenario A: 21 writer and 6 fresh-reader checks; actual drop handler,
  model/bone/gizmo events, frame 0/4 auto-keys, preview, portable reopen and movie.
  Grounded placement was fixed; 20 placement regressions passed.
- Native cutout ordering: 9 contract units, 16 exact allocation/state checks,
  37 native writer and 16 cold-reader checks, 28 expression/spring and 31 material/
  lighting/fade/persistence checks. Four native models are exact in current replay.
- Required-feature diagnostics: 9 unit and 5 actual native refusal/preservation
  checks, 7 Source/MMD and 9 VRM worker checks, 28 Python regressions. Current
  scenario A wrapper repeats its 21+6 checks with original SHA/mtime and exact
  packed values preserved.
- Scenario C has all seven routed software steps and a movie; D has all six
  mechanical steps, contacts, exact recorded samples, bounded take timing and a
  movie. Tutorials and actual forced-exit recovery have separate committed evidence.

Do not repeat these unchanged cases in cloud just to report activity. Windows
execution is a distinct reason to run their target commands.

## Environment and execution

Use an isolated checkout/review copy, with a clean worktree. Preserve the owner's
normal installation and private originals. Installing or replacing software on
the owner's PC, publishing, releases and deployment need separate authorization.
Use approved existing runtimes or an approved clean Windows test environment.

The target uses Godot 4.6 stable standard, Python and FFmpeg with libx264/AAC.
MMD native workers additionally need compatible Blender/MMD Tools and Python
3.11+; Source native workers need the documented compatible SourceIO runtime.
See README/dependency documentation for discovery and overrides. No SFM/GMod
installation is required for complete standalone input files.

If discovery needs explicit existing paths, set `HYBRID_GODOT` and
`HYBRID_FFMPEG` to those executables. Keep `ffprobe` beside FFmpeg. Core runtime
prerequisites are documented; an all-binaries-bundled MSI is not claimed.

The automated wrappers below use `run.command` and an isolated Windows desktop.
Require their private-desktop receipts: child desktop confirmed, no foreground
child observed, process job closed and desktop closed. Never fall back to a
visible automated window. Linux reruns require an explicitly provisioned private
`--isolated-display`; no owner display fallback is permitted.

## Runnable automated Windows checks

Run from the repository root, keeping logs and generated output outside commits.
Replace the example VRM path with the approved original matching SHA256
`14d2b2c751e2d6b7739471b961d71b7b16ca28089c04d9465b9c71a113033ee3`.
The scenario A wrapper stages its own copy and never renames that original.

```powershell
python tools/check_completion.py
python tests/verify.py
python tests/verify_scenario_a.py --native 'D:\approved-inputs\AvatarSample_A.vrm'
python tests/verify_scenario_c.py
python tests/verify_scenario_d.py
python tests/verify_tutorials.py
python tests/verify_first_movie.py
python tests/verify_recovery_schedule.py
python tests/verify_recovery_startup.py
python tests/verify_recovery_history.py
```

The full aggregate is not represented as freshly passed in Linux. Its opaque
unit marker now expects nine checks and its new required-feature unit expects
nine; both pass through its actual headless runner. If a wrapper reports a missing
native or checksum-bound historical fixture, preserve that skip/unrun result and
identify the exact missing input. Do not convert it to a pass or remove assertions.

Expected automated evidence: zero failed assertions for executed cases, original
hashes/mtime unchanged where checked, exact authored state and required pixels,
owned-source/cache-offline cold replay, unchanged manual HAS, valid private-desktop
receipts, and actual `ffprobe`/decoded-media results. Keep prior failed attempts
with their diagnoses. Investigate failures before promoting target acceptance.

## Exact remaining acceptance

| Gate | Required target or input check | Evidence to record |
| --- | --- | --- |
| A | A real novice follows addendum 17.A's eight steps: Home/New, visible grounded import, model/bone selection, gizmo poses at 0/4 without Record, motion preview, baked save/close/reopen and 1080p/24 MP4. Also observe the original specification's independent drawing/sound workflow. | Elapsed human time, assistance needed, confusing controls, actual OS file-drop/input behavior and the finished project/movie. Automation time is not five-minute novice evidence. |
| B | Import a complete Source/GMod BSP with available materials/props/lightmaps, a VRM and PMX prop; place multiple map roots, pose/position, compare Lit/Unshaded, save one self-contained HAS and cold reopen without missing embedded dependencies. | Native source/dependency hashes, supported/unsupported feature report, appearance/rig/material/lighting observations, map transforms, portable replay and movie evidence. Missing-map data is an input blocker that can also resume in cloud. |
| C | Run the seven-step C route on Windows, including presence 0–99/100, clip-relative movement, split gaps, persistent OFF, editor-only hidden selection, fade default/0 ms and adjacent camera cuts. | Routed assertions, cold state/pixels, actual movie/audio and target input/GPU results. |
| D | Run the six-step D route: compatible ragdoll falls/throws, freezes/resets, no unrecorded keys, World captures impacted objects, Local captures selection, ordinary take stays responsive. | Actual contacts, exact saved samples, movie agreement, metadata size and frame/sample timing on target hardware. |
| E | A learner uses the real Basic practice, correct grading/auto-advance, an actual 10–30-second stuck interval and quiet hint, full Previous, Continue/Fresh and optional normal Save. | Learner clarity/usefulness observations, full restored state and preserved practice/personal project. The cloud hint test simulated 16 seconds. |
| F | Exercise background autosave, abrupt termination of only an owned test process, newest valid recovery, corrupt-latest older fallback, timestamp/thumbnail history and unchanged manual HAS on Windows. Include target storage-failure cases. | Process/owner receipts, original/manual hashes, restored state, history images and fault/recovery logs. Process termination does not certify physical power-loss durability. |
| Tablet/audio | Draw at 1080p with the actual tablet/driver/GPU and listen to target audio synchronization. | Device/driver identity, measured input-to-stroke latency and pressure behavior, comfort observations and audible timing. Synthetic packets/decoded PCM are separate evidence. |
| Clean install | In a clean supported Windows environment, install/launch offline using documented approved prerequisites, import an original sample, save/reopen and export a playable MP4 with a detected compatible encoder. | OS/tool versions, setup steps and missing-dependency messages, offline launch and original/project/movie hashes. A configured development machine is not a clean-install result. |

## Missing inputs and preserved limitations

No complete native `.bsp` is present in the uploaded attachments. `temp.gma`
could not transfer above the tool's 32 MiB limit; its contents remain unknown.
If accessible locally, inspect it read-only before deciding whether it supplies
the map. Preserve archive/original hashes and extract only to an owned test area.

Street PMX requires these exact files:

- `atlas03_street_d.png`
- `atlas02_street_d.png`
- `atlas03_props_d.png`
- `atlas02_props_d.png`
- `atlas09_props_d.png`

The chat images have no verified filename mapping. Do not guess or substitute
unrelated textures to claim native fidelity. The current import fallback and
missing-texture diagnostics are already tested.

The old VRM reference images recorded arbitrary equal-depth cutout winners. Their
original assertions and failed results remain intact. Replaying those old hashes
after the deterministic fix has three one-pixel failures; current fixed-version
writer/cold replay passes every exact assertion. This is a documented rendering
tie-policy correction, not lost authored data or an introduced image tolerance.
Cross-driver pixel identity and full native shader/constraint/simulator reproduction
are not claimed. Native approximation/unsupported warnings remain authoritative.

Windows directory sync reports unsupported. Apply the specification's
“fsync/rename where supported” condition; do not invent an unconditional Windows
directory-flush implementation gate. Current POSIX fault/rollback tests do not
replace the Windows crash/installer observations above.

The current [ledger](completion_checklist.json), [native review](native_profile_acceptance_review.md),
[A–F review](acceptance_handoff_review.md), [cutout receipt](benchmarks/vrm_cutout_order_2026-11-09.json)
and [required-feature receipt](benchmarks/required_feature_diagnostics_2026-11-09.json)
separate current passes, historical failures, skips and unrun external work. The
continuous [goal](goals/complete-has.md) stays in GitHub/cloud independently of the PC.


## 2026-11-21 — Reconstructed rest, portable movie and current review

Published main b637fb10f8a78f1e03b137bfa8af4845296726bb is independently retrieved:
1230 raw functional/changed-evidence files,12,442,934bytes, exact tree/blob/mode
and raw-file comparison, no alternates. Source7d15 fixes Godot's packed-weight
rest drift with original-weight/rest and flexible resource views of the same
instance. Native Simple19 and public36 pass; all37470 posed vertices and resting
pixel bytes match exactly. Live simulation leases deliberately retain the flexible
view; old derivatives without original references are not guessed or rewritten.

Portable/movie tests0c159b43 pass30: four authored guide-FK frames, actual1080p24
H264, fresh packed-project reopening, exact pixel/resource/native-transform
comparisons. Source5d967664 also preserves an explicit reviewed reference through
the ordinary editor recipe; generated17+26+16 tests pass. Three movie failures,
the old7f rest-render failure and the shared13-chain settling failure stay recorded.
See docs/secondary_reconstruction.md and its linked compact evidence packets.

All five colored back-hair sections now settle11.22cm in the scoped12-check CPU
trial, with exact Off restoration and fixed original joints/attachments. This is
not full-hair readiness:123 final contact pairs,-4.45cm worst recorded gap and
60.5ms average simulation step remain. Outlines/bangs/ribbons are excluded.
Current work compares a bounded per-row contact cache against the unchanged
solver, then will address body penetration and explicit outline correspondence.
Do not promote a source-only experiment to accepted collision or realtime quality.

New stable review: C:/a/Programming/cloudflare/HAS-Review-Reconstructed-Hair-b637fb10.
Open Reconstructed hair.bat launches the local private first-section four-frame
project with its own profile.1221 exact committed runtime source files and the
packed payloads were checked. Prepared without launching an owner window; the
original project and installed Studio/tools are unchanged. Keep this review and
its private artwork local. It supplements the existing discovery/lighting reviews.
The busy owner has not been asked to interrupt work for another manual check.

Formal52/54 implementation and55/62 acceptance stay unchanged. Remaining required
observations: native appearance (IMPORT-02/03 and ACCEPT-B), timed noviceACCEPT-A,
learnerACCEPT-E, actual tablet/audioACCEPT-TABLET and clean offlineACCEPT-INSTALL.
CanonicalFull183 remains bound to exact5d37647c; no later Full pass is inferred.
CompletedFull5d clone and browser Git residue remain untouched after automatic
approval review rejected their deletion; exact-path permission is pending.


Independent read-only review audit also passes:1221 immutable Git blob files,
10,126,412 source bytes, exact runtime membership, both packed payloads and the
private asset checksum, native Head/all four guide-key states, and normal launcher
arguments/profile paths. The review and original packed-project bytes/nsmtime
are unchanged. No engine was launched by this preparation/audit. Compact receipt:
experiments/reconstructed_hair_review_20261121/verification.json.


## 2026-11-21 — Published cache source and current runnable review

Mainff852f93c0bc048be527bfe8d6481f74eeefdf6d is pushed and independently fetched:
1257 exact raw functional/changed-evidence files,12,705,615bytes, tree/blob/mode
match and no alternates. Functional source equals qualifiedcbcab43b; only history
append conflicts were reconciled, preserving all old lines and incoming notes.
Current-source62(47+15), protectedMiku54 and helper208 CPU results remain scoped,
not a new Full or human/device acceptance. Installed pairedmean6.93% does not
replace distinct18.6/31.7 prototype observations or promise FPS/worst-case speed.

Prepared source-pinned review HAS-Review-Reconstructed-Hair-ff852f93 includes1225
immutable source files plus the private first-section four-frame packed project.
Independent read-only audit confirms all10,180,928 source bytes, membership,
payloads/portable references/nativeHead+guide keys, launcher/profile paths and
unchanged source/original SHA+nsmtime. No owner app was launched. Previousb637
review and installed Studio/tools are unchanged. Keep private artwork local.
Compact publication/review proof: experiments/contact_cache_publication_20261121.

Master pickup and finite ledger now identify this source and concrete next tasks:
residual contacts/global solve budget, explicit outline/physical surfaces, then
moving-model hair inertia. Formal52/54+55/62 and seven external prerequisites stay.
No repeated owner/manual request. Automatic cleanup rejection remains pending
direct approval for the two named old targets; no retry/workaround or deletion.
