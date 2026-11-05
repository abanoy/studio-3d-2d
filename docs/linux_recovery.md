# Automatic recovery on Linux

Linux now supports the same automatic startup recovery path as Windows. The old
helper always returned unknown ownership off Windows; crashed sessions therefore
stayed protected instead of being offered to automatic restoration.

The helper reads only the supplied owner PIDs' bounded `/proc/<pid>/stat` records.
Boot UUID plus the exact start-tick string identifies an incarnation across PID
reuse and reboot, without deriving identity from a changing wall clock. Zombies
and dead tasks have exited. A missing record requires a positive no-such-process
result from `kill(pid, 0)`; this existence query sends no signal. Hidden/denied,
malformed or unavailable observations remain unknown and protect the session.
There is no process enumeration or termination in production discovery.

Linux emits explicit `studio_process_liveness_2` with a `linux_start` map; session
sidecars store the matching `linux_start` token. Windows retains its v1 protocol,
native `created_100ns` identity and handle queries. Both validators use exact
strings. A malformed or ambiguous dual identity stays protected. Legacy PID-only
sidecars keep conservative existing behavior. Unknown liveness never becomes
recoverable merely because identities differ. Other unsupported platforms retain
unknown ownership. No HAS, scene, model, audio or journal schema changed.

Fresh 2026-11-05 UTC checks:

- Python discovery:280 run,279 pass, one unavailable independent MMD-reader skip.
- Linux probe tests:8 pass, including a real owned child before/after exit,
  comm names containing parentheses, hidden PIDs, missing `/proc`, malformed
  ticks, absent boot identity and invalid PID refusal.
- Existing platform ownership test:47 assertions pass, including real parent/
  writer identities, simulated PID reuse, corrupt sidecars, current/foreign live
  ownership, legacy behavior, exact bounds and no saved-scene changes.
- Existing journal test:33 assertions pass, including bounded12-entry retention,
  corrupt recent states/catalogs, shared data, atomic failure and older fallback.
- Existing normal-startup matrix, made portable:15 cases /147 assertions pass.
  Actual owned writer exits abruptly by SIGKILL; normal production `_ready`
  restores newest valid state or older valid state, preserves explicit manual
  HAS bytes, and refuses live/unknown/malformed/current owners. Rig, camera, ink,
  audio, dirty-copy identity, stale-work refusal and explicit Save are checked.
- Recovered export: H.2641080p24,48frames,2seconds, AAC; decoded frame24 audio
  onset1.0000417seconds. Export input PNG equals preview. Physical audio devices
  and subjective listening were not tested.

Graphical tests use a pre-provisioned isolated dummy X display with llvmpipe and
dummy audio. No native game fixtures were available (`native_models: 0`); the
original procedural room and skinned actor were exercised. The Windows guard,
private-desktop receipts and assertions are preserved, but not freshly run here.
Linux reports no Windows receipts or retained Windows handle proof.

Reproduce Python tests with `python -m unittest discover -s tests` and ownership
with `python tests/verify_recovery_identity.py`. Use pinned Godot4.6stable and an
absolute writable log for `tests/recovery_journal_unit.gd`. On Linux run
`python tests/verify_recovery_startup.py --isolated-display :99` only after creating
that owned private dummy display. Omitting the explicit display refuses. Windows
uses the existing private-desktop launcher with no visible fallback.

Fresh logs and copied JSON evidence are in `/workspace/has-handoff-audit/`, with
`linux-recovery-*` names. Generated tracked historical output files were restored
after preserving new evidence outside the checkout. These scoped passes do not
complete broader native fidelity, hardware/artist acceptance or the full roadmap.
