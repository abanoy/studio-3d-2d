# Verification after an actual port

Nothing below ran as part of preparing this source-only candidate. Historical
prototype evidence is94 headless and830 private GPU checks; it is not a main or
aggregate pass. Use root's existing coordinator and single GPU lease. Do not
repeat a suite merely to accumulate passes; a new edit/failure justifies reruns.

## First gates

- Verify all sixteen copied files and the adapted verifier's project/root binding.
  Parse `src/app.gd` and the four GPU scripts through the actual main runner.
- Run these headless scripts through main's `run.command(headless=True)`:

| Script | Expected marker | Historical count |
| --- | --- | --- |
| tests/wind_review_unit.gd | WIND_REVIEW_UNIT | 51 |
| tests/wind_review_hooks_unit.gd | WIND_REVIEW_HOOKS_UNIT | 14 |
| tests/wind_review_review_unit.gd | WIND_REVIEW_AUDIT_UNIT | 29 |

Require actual zero failures/errors/leaks. These scripts use controlled endpoint
fixtures and must not be described as physical input or GPU evidence.

- Run the adapted six-job matrix on **main**, including declared native groups,
  the distinct parented peer, independently known nonzero excluded recording,
  main-view pixels, cancellation/readback/input/lifetime cases, real body/prop
  continuation and original-only Local/World recording targets. Require complete
  source/input preservation and all six clean receipts.

## Existing integration gates

Use these existing tests for focused triage before the full default run. If a
single stable canonical run already covers them after the port, reuse that
evidence rather than running the same complete groups again without cause.

| Existing test/workflow | Reason |
| --- | --- |
| tests/verify_native_readback_lifecycle.py, default working-source mode | App/renderer capture hooks, pending native scope drain, immediate free/queue-free/remove, normal Home startup. Default must freeze all nine new runtime files; the diagnostic two-file --overlay-runtime option is insufficient to certify this port. |
| tests/verify_secondary_helpers.py | Original39/14/59/35 helper paths, actual worker/source/shape identity, immediate capture/free, portable HAS, movies and decoded audio. |
| tests/verify_secondary_picking.py; tests/verify_secondary_batch.py; tests/verify_helper_morphs.py | Existing picker/window input, single/batch Apply and one-Undo setup, failure/stale eligibility, shape defaults. This does not close pending-helper wind preview. |
| Existing core secondary_motion/fan_motion/physics/physics_contacts/physics_props/physics_recording groups and tests/verify_fan_flutter.py | Ordinary spring construction, body ownership, cancellation, fan editing and actual native/media paths after the constructor/hook changes. Preserve the upright Scout and original contact bounds. |
| tests/verify_contact_physics.py and --components | Current Hair OFF restores authored data and all current bones without a phantom history entry; prior real fan Undo/Redo survives. Body Freeze and explicit Record still author their established edits, release only body-owned intervals, retain knee targets, reopen HAS and match the movie. Do not reinstate the stale one-hair-freeze-Undo assertion. |
| tests/verify_scene_view.py and existing workspace/fan1200px checks | Full scene/camera-focus drawing, native guide exclusion, current readback teardown and wrapped toolbar/scene space after adding the control. |
| tests/verify_shortcuts.py; tests/verify_camera_transform.py | Existing key/text routing, temporary camera/explicit keys and cursor/navigation behavior in addition to the new preview-specific input checks. |
| tests/verify_live_appearance.py; tests/verify_import_physics.py | Existing live hair preserves lighting/fades and native body/hair import/Record ownership. Keep the current non-evaluating native readback QA corrections. |

## Final default run and review

Run the exact `python -u tests/verify.py` workflow from stable final source, with
documented native fixtures, exact19-layer KRA, approved FFmpeg and no obsolete fan
override. Add the new tests deliberately to that workflow before this run.
Hold source/revision fixed, require exit0 and a fresh aggregate, and preserve every
failure/skip/unrun result. Pre-port36-core/suffix passes plus prototype830 are not
a post-port aggregate.

Check actual normal Home/New/Simple startup from the published revision and build
a new separate owner review. Do not patch old review Studio/recovery, replace an
installation or solicit participation while the owner is unavailable. Native
artist fidelity, novice/learner timing, tablet/audio hardware and clean offline
Windows installation remain external acceptance conditions.
