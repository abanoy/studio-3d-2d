# Separate readonly PMX correspondence observation

This source packet is ready for Root's later ordinary CPU observation after the graphics lane closes. Preparation used only public source packets and authored 339-byte synthetic PMX files. The real provenance, four artist originals, four staged copies, and current graphics outputs were not opened here.

The first CLI phase imports only the independent oracle and writes each complete raw-table witness to a PRIVATE case file. Root must separately inspect and freeze the exact resulting PRIVATE_ORACLE_PHASE.json bytes/hash. The second CLI phase requires that manifest path, its SHA256, and an explicit Root-frozen flag before it reads a candidate input or imports the candidate reader, comparator or archive. The witness files are individually pinned by that frozen manifest. There is no automatic second phase.

Each case compares the original and staged copy against Root's pinned provenance: six identity fields, single-link regular files, size, SHA256, actual byte equality, and observed stable stamps before/through/after ordinary `rb` reads. The same pair, provenance and source packet bindings are rechecked before the child receipt. The candidate phase verifies the frozen witness again after the archive operation. These observations cannot exclude all concurrent filesystem races and do not establish denied-write/delete handles or preload/I/O confinement.

The second phase compares exact candidate declarations against the independent witness, then archives/extracts the canonical capsule in an authored empty GLB carrier. This exercises declaration correspondence and the inert archive only. It does not convert a PMX model, preserve an actual model's GLTF geometry or HAS helper output, simulate physics, qualify physical validity, establish a second layout authority, or adopt a production reader. Whole-native-protocol qualification stays false even if all four cases pass.

## Root's later commands

Use the approved Python recorded in common.py. Replace `HARNESS_INDEX_SHA` only with this packet's final INDEX digest. Both fresh phase directories must be direct children of Root/output and begin `PRIVATE-pmx-observation-`. A Root closed-lane flag is an explicit assertion supplied by Root; this tool does not inspect processes, graphics jobs or operating-system scopes.

```powershell
& 'C:\Program Files\Python313\python.exe' -I -S -B -X utf8 'C:\a\Programming\cloudflare\has-acceptance-session-20261111\experiments\pmx_physics_native_observation_harness_20261117\run_observation.py' --phase oracle --output 'C:\a\Programming\cloudflare\has-acceptance-session-20261111\output\PRIVATE-pmx-observation-oracle-attempt1' --harness-index-sha256 HARNESS_INDEX_SHA --root-graphics-lane-closed
```

Root then privately freezes the exact successful `PRIVATE_ORACLE_PHASE.json` and its four witnesses. The second command is a separate explicit operation; `FROZEN_ORACLE_SHA` is the actual frozen manifest SHA, never an inferred success flag.

```powershell
& 'C:\Program Files\Python313\python.exe' -I -S -B -X utf8 'C:\a\Programming\cloudflare\has-acceptance-session-20261111\experiments\pmx_physics_native_observation_harness_20261117\run_observation.py' --phase compare --output 'C:\a\Programming\cloudflare\has-acceptance-session-20261111\output\PRIVATE-pmx-observation-compare-attempt1' --harness-index-sha256 HARNESS_INDEX_SHA --root-graphics-lane-closed --oracle-manifest 'C:\a\Programming\cloudflare\has-acceptance-session-20261111\output\PRIVATE-pmx-observation-oracle-attempt1\PRIVATE_ORACLE_PHASE.json' --oracle-manifest-sha256 FROZEN_ORACLE_SHA --root-witness-frozen
```

Root must supply the actual closed-lane authority and independently decide when to invoke either phase. An accepted manifest requires all four child completions and preservation observations. Failed/refused/timeout cases remain explicit failures; missing final preservation is unobserved, rather than evidence that an original changed. Root should retain the whole PRIVATE phase directory, including failures, privately. Existing output directories and payload files are never overwritten.

If bounded cleanup cannot confirm that the retained child exited, the batch stops immediately: later cases stay unstarted, lane closure remains false, and a PRIVATE_OWNERSHIP_FAILURE.json records the exact owned child/command for Root. The API retains that Popen in RETAINED_UNCONFIRMED and refuses further batches while it remains unreaped. The CLI returns an explicit unconfirmed-closure failure and never claims the lane is closed. Root must resolve that ownership failure before starting another CLI invocation or any further activity; the private record does not authorize an arbitrary PID kill. If even private record writing fails, the retained reference and explicit failure remain, with no completion/preservation claim.

## Bounds, measurements and privacy

- Each input is at most 128 MiB. Provenance and phase manifests are at most 1 MiB; oracle witnesses at most 8 MiB; candidate capsules at most 2 MiB; helper JSON at most 16 MiB; small reports at most 256 KiB. The authored empty carrier adds only GLB framing and zero BIN bytes.
- The parent retains one ordinary `Popen` per case, waits at most 60 seconds, then terminates/kills only that retained child with 5-second closure waits. The ordinary timeout path has two such waits; exceptional cleanup may make one final 5-second kill/reap attempt. Closure is never accepted unless that retained child is observed reaped. There is no process search or arbitrary PID kill. No child process spawning is part of worker code.
- Wall time includes source verification, parsing and before/after preservation. Python allocation peak uses tracemalloc from worker-main entry through preservation, before writing its receipt. It excludes interpreter startup and does not equal total process RSS. Windows peak RSS is unmeasured. A timeout may have no allocation sample. Missing samples stay null with an explicit measurement count.
- These are file/output acceptance bounds and measured observations, without hard memory or I/O enforcement. Private stdout/stderr files have a 4 MiB post-exit acceptance bound each; output is redirected directly to files rather than held in parent RAM. Their size is not a live disk quota.
- All input-derived witnesses, declarations, archive bytes, reports, command paths, traces and logs use PRIVATE files. Parent stdout contains a fixed scalar projection or a fixed refusal type. It omits source/model/table names, paths, source hashes and raw values. Do not upload the PRIVATE output directories.

`--synthetic-root` is restricted to this packet's synthetic_runs subtree. It can never select Root's actual input/copy/output roots. It exists for tests and does not activate or qualify native observations. Source INDEX verification binds all three sealed predecessor packets and this packet; these are experiment source bindings rather than production module-admission proof.

Run `python -B -m unittest -v test_harness.py` from this directory for the authored-file tests. They create and remove only uniquely owned synthetic_runs children, and never inspect the fixed real-input context.
