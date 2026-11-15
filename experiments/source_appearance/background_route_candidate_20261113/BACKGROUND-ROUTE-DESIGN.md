# Explicit background conversion proof candidate

This is output-only code and CPU evidence for root review. **No new private
desktop, Blender, native worker or GPU run occurred.** The original `d8749db`
driver, schema1/schema2 locks, failed first-conversion bundle and original private
receipt remain intact. Production `tools/private_desktop.py` and all four frozen
appearance-worker files are unchanged.

The first actual conversion emitted an 836,088-byte Nitori GLB, then its private
wrapper exited 2 because no graphical window/child desktop was confirmed. That
case remains failed and unaccepted. This candidate never edits that receipt,
forges its `child_desktop_confirmed` field or accepts an old exit 2.

## Concrete protocol

1. The separate `background_conversion_driver.py` copy preserves the fourteen
   case schedule, worker commands, source/stage/runtime checks and native
   metadata/GLB/refusal guards. It requires a fresh **schema3** lock, including
   the observation code and frozen native helper files. Old locks refuse.
2. Only during an explicitly leased execution does `BG.prepare` create a fresh
   per-case nonce and hash-bound background request. The approved private tool
   launches the new Python bootstrap with a legitimate `--headless` flag. The
   bootstrap consumes that flag itself and creates no user interface. Production
   graphical-window requirements are unchanged; the existing explicit headless
   branch is used deliberately.
3. The Python bootstrap reads its own WinAPI process/thread ID, parent ID and
   creation times, current thread desktop name, process window station, actual
   executable path/hash and observation time. It hashes the frozen source
   files. It requires a `HAS_Test_<fresh UUID>` desktop and the parent's actual
   window station before running the unchanged worker through `runpy`.
4. A bounded interceptor accepts exactly the original frozen Blender `Popen`
   vector, output directory and `CREATE_NO_WINDOW` option, once only. It changes
   only the `--python` entry from the unchanged bridge to an observation entry,
   and adds two environment keys pointing to a fresh hash-bound observer request.
   Factory/offline/background options and the conversion JSON stay unchanged.
   The actual Blender PID/creation time and both command vectors are recorded.
5. Inside Blender itself, the observation entry independently calls the same
   WinAPI functions. Its actual current thread desktop/station must equal the
   Python bootstrap's observed desktop/station. Its actual parent PID/creation
   identity must equal that Python process. Only then does it run the unchanged
   bridge through `runpy`, preserving the original conversion argument and
   `__file__`. Native exceptions propagate; normal Blender completion is not
   replaced with a misleading `SystemExit`.
6. Both `runpy` sites restore the original prototype script-directory import
   context. They clear/save/restore the eleven relevant cached application
   helper modules, prepend the frozen prototype `tools` directory and record
   the actual role-specific helper origins/hashes. This avoids accidentally
   resolving the production guards that the observation utility imported.
   Parent verification requires the exact seven Python/eight Blender helper
   provenance records. All nineteen required code files are hash-bound.
7. Parent verification reads fresh, bounded, exclusive evidence files. Python
   PID equals the unmodified private receipt's child PID; its parent/creation
   equals the observed private wrapper. Blender PID equals the intercepted
   process and unchanged worker's `worker.json`; its parent/creation equals
   Python. Both self-attested desktop names equal the fresh private receipt's
   desktop exactly. Nonce, checkpoint, input-lock/source/request hashes, process
   creation/observation times and file modification times must match the fresh
   launch interval. Both completion records and source hashes are required.
8. The original private receipt must still have the expected exit 0 or 1,
   closed job/desktop, no error, no foreground-child observation and no desktop
   switch request. Its monitor's child-desktop flag is preserved verbatim and
   reported separately. A new isolation receipt records the independent proof.
   Expected all-blank exit 1 additionally needs the exact geometry refusal in
   both logs and no successful GLB/parameters. All other failures stop the batch.

This observes the **current Python/Blender threads' desktop and each process's
window station**. It does not enumerate all prior windows or other threads.
Literal no-window/no-switch fields describe the observation code's own actions;
they are not invented measurements of the whole process. The private launch/job
and no-foreground receipt remain separate evidence.

## Files and current evidence

- `source/win_desktop_attestation.py`: read-only WinAPI collection and explicit
  own-process probe; never creates, closes or switches a borrowed desktop.
- `source/background_route.py`: request/source guards, exact command observer,
  import-context restoration, fresh parent verification and explicit leased
  private launcher.
- `source/background_python_bootstrap.py`: real headless Python entry and exact
  frozen-worker invocation.
- `source/background_blender_observer.py`: Blender self-attestation before the
  unchanged bridge.
- `source/background_conversion_driver.py`: separate integrated candidate;
  `background-driver-integration.patch` shows its bounded difference from the
  retained original driver.
- `source/test_background_route.py`: **22 passing CPU controls**, including
  stale/wrong/missing proof, IDs, sources, executable, desktop/station, closed
  job, old actual exit 2, command changes and native import resolution.
- `source/test_background_driver.py`: **22 passing CPU controls**, comprising
  18 retained native/stage/geometry guards and four background integration
  controls. Synthetic data only; no native process was launched.

Independent read-only review found the initial `runpy` import-path/cache gap and
an overbroad literal-window field. Both were corrected before any rerun; the
follow-up found no remaining concrete blocker in those corrections or candidate
wiring. Earlier CPU logs/artifacts remain retained.

The reviewed read-only own-process probe at
`background-own-desktop-self-probe-reviewed.json` recorded its real `Default`
desktop and `WinSta0`, PID/thread/parent identities and creation times. Its
source hash is recorded. That proves these WinAPI calls work in that ordinary
context only. The controls explicitly reject it as private-placement proof.
**Actual private Python and Blender attestation remains unrun.**

## Next step after root review

Root is correcting a separate canonical wrapper-result publication contract.
Do not prepare a new functional/HEAD lock or execute during that change. Once
root's next checkpoint is stable and remotely verified, use the separate
candidate's `--prepare-inputs` with a fresh `conversion-inputs-background3.json`
and that exact forty-character revision. Run default preflight against its
printed hash. Only a later explicit exclusive conversion lease may add
`--run-conversions --lease-confirmed`; output must be fresh. There is no visible
fallback or automatic cleanup.

A future successful route proof still would not establish native material/skin
fidelity, rendered differences, app choices/adoption, Undo/HAS/movie behavior,
runtime variants, native jiggle/assembly or artist acceptance. Nitori's missing
native `materials/hairbump.vtf` remains explicit, with no guessed substitution.
