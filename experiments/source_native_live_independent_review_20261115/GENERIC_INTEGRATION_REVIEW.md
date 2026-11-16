# Generic integration and coverage review

Source-only review of the frozen integration found no material generic regression. This note does not modify the earlier indexed review or assert a fresh default-suite PASS.

| Reviewed file | SHA256 |
| --- | --- |
| `src/secondary_live.gd` | `dc7aa47b462edaaa977fa3f2b110df02d3034ecea2462f7bc47bf1c40a3287be` |
| `src/physics_editor.gd` | `e351c0f5e2be18c33793a0ae6234b049095c923b35ca8ec1c6c7aaeb36bb8b6a` |
| `src/fan_editor.gd` | `85a575881cc13b9acb3f266dcbe401266a80bf424667e2984a3ff3c093fcb614` |
| `src/source_secondary.gd` | `d2c04165587ca3bb0f7b9f474b23dc81902cc78c1aa174d593534f0198f689c0` |
| `tests/verify.py` | `459b90eeeae9d5523654c07fcbb3de27dad0e889943f46947333e8eb5a65437a` |

`SecondaryLive` chooses native motion only for the exact qualified family with no generic chains. All ordinary declared-chain and explicit-helper cases retain Spring creation, the existing airflow smoothing, 0.35-second activation fade, rotation slew limit, primary-body ownership and complete-pose handling. Native output takes its separate absolute FK path. The new clock/seek guards run only in that path. Body coexistence on the same native actor remains refused; it is not implemented by the separate live-prop preservation checks.

`PhysicsEditor` makes the eligible untouched native model reachable from Hair & clothes without changing the generic setup fallback. Both pending setup and an open helper review prevent competing native setup. Native preview failure, Save and seek route through Hair Off, restoring authored state rather than creating a frozen draft. Explicit Record retains the existing authoring contract. Generic body/hair wrapping, cancellation and Off behavior stay in their existing branches.

`FanEditor` adds only a native target/anchor fallback when generic chains are absent. The local deep copy in `aimed_world` prevents the previously found chain-list alias mutation. Aiming must keep the model's secondary definition and source provenance unchanged. Existing nonphysical fan root edits, Undo, on/off and speed controls remain the same. Native airflow has separately documented relative acceleration mapping; it is not a calibrated fan or native SDK unit claim.

The native tooltip/status state that the first subset moves one of 49 imported joints, Body Physics must be off, Off restores authored motion, and Record keeps motion. This avoids implying all retained rules run. Nonblocking text polish remains: `moves1of49` and `(1of49 imported joints)` should eventually have ordinary spaces. No text or core source was changed during this review.

## Existing default verification that is affected

- `tests/verify.py:114` through `:120` schedules `secondary_motion_smoke.gd`, `fan_motion_smoke.gd`, body physics/contacts/props, and recording unit/smoke tests. These exercise generic runner behavior, native VRM chains where supplied, body/hair ownership, Record, Off, persistence and movies.
- `tests/verify.py:169` runs `verify_fan_flutter.py`. This covers long-running generic flutter, fan aim/field and ordinary UI controls. The independent `fan_motion` suite also checks visible non-rest Off restoration and preservation of the same borrowed primary body.
- `tests/verify.py:172` starts the guarded wind-review suite, including procedural, VRM0, VRM1, backhair, lifecycle and primary-body cases. These are useful checks against generic behavior changes.
- `tests/verify.py:277` through `:285` runs secondary helper, picking and batch suites. They cover explicit helper generation, weighted effects and artist selection paths; explicit helpers must continue to take priority over the new native route.
- `tests/verify.py:347` runs `verify_import_physics.py`, covering interactive import/default physics, live peers, explicit Record and portable movie behavior.
- `tests/verify.py:227` through `:235` runs Source choice foundation. Its separate `verify_source_bone_bindings.py` group has 79 authored binding and 17 helper-choice checks. This is static/admission foundation coverage, not the actual Junko native-motion runtime.

Current `tests/verify.py` does **not** schedule `verify_source_native_live.py` or `source_native_state_unit.gd`. A fresh default PASS will establish the affected generic regressions and foundation scope; it must not be described as automatically including the separately executed native live/state checks. Keep those exact actual reports and source catalogues separately joined to the feature's tested source, or deliberately add new plumbing before the next source freeze. Do not reuse the historical 1,008-file full-source proof for the expanded functional source set.

## State/header guard review and actual distinction

The current Source backend caches all 69 immutable rest/name/parent rows, actor order and info/base/skeleton identities, import map and native report. The comparison excludes authored pose, placement and solver state. It also checks source existence, modification time, length and the captured 12-byte GLB header. It rejects an empty initial binding stamp and preserves exact source/GLB/wire/prefix admission. These checks occur before numerical state commit. Full cryptographic source authentication occurs on creation/reload; an edited body with the same header, size and timestamp is explicitly outside continuous detection.

The first owned state-test parse failed at line 341 because Godot could not infer `complete` from an untyped array entry. Frozen script SHA256 was `46436bab631d12efdbc40474012234d82b2427a1af51676f5c6deab34dc36140`. The sole correction was `var complete: bool =` in place of `var complete :=`; no condition or planned assertion changed. Corrected test SHA256 is `008e694dfc3947e9ca3054e6dff14b64e22ee0d1dea3aaf8147df6c9ec0e74fc`. The first failed run remains preserved at `output/source-native-state-20261116T020159138961`.

The separate actual run at `output/source-native-state-20261116T020227823185` reports **180 checks, zero failures**, both parse/state exits zero, both owned children reaped, no forced kill, source/input/runtime preservation true and runtime lease released. Its verification SHA256 is `31e08e4c15915f543b9df9ad8b01b4bfe472b7d47fde4558090cacc834d3097f`; its exact result SHA256 is `a42cc5de39e6cbaadc5adbdf3811739ef979bc0f37c56c72e369e1f159d3d1e6`.

The 180-name preregistration combines 23 negative cases, nine additional creation refusals, isolated header/length/mtime observations, three real Model instances, independent per-actor state, wrapper resets and exact authored/provenance restoration. The physical-bone case uses an actual engine body solely as an adversarial refusal context. It does not qualify a complete Junko ragdoll, borrowed primary or same-actor body/hair coupling. Mutations are restricted to the three fresh test-owned GLB copies; original input GLB/report and source files remain read-only. Source review, the failed first parse, the successful state run and any future full default run remain distinct evidence scopes.

This review used source and completed metadata reads only. No engine, GUI, process/CIM query, Git operation, native-content publication or core source edit was performed by the reviewer. The root coordinator retains runtime and publication authority.
