# Cloud source recovery checkpoint — 2026-11-04 (America/New_York)

This checkpoint restores the supplied Windows development source. It is not a
new full-spec implementation or Windows acceptance result.

## Provenance and preservation

- Starting local HEAD and freshly queried remote main:
  `c5f34e9779d87f4b1f00f46ea5e506d4025f5b4f`.
- Supplied archive SHA256:
  `16f737db752c2a367d7819fe5d283be77069f99ebb1ee1cefcfe3c354b7f69b4`.
- 695 files, 6,013,195 uncompressed bytes; ZIP CRC, entry paths, duplicate
  names, symlink modes and expanded-size bounds checked before extraction.
- Comparison: 352 identical, 105 changed, 238 added. All 695 recovered files
  matched the archive byte-for-byte before this new documentation was written.
- No old source, tracked output or native evidence was removed. Git history is
  retained. Pre-recovery changed files are backed up outside the checkout.
- `Start Studio.bat` initially appeared locally modified, but its physical bytes
  matched the HEAD blob exactly. The difference was Git newline conversion.
  The recovered launcher retains CRLF and adds the archive's project argument support.
- Neither root nor parent LLM.md existed. No Windows parent history is available;
  the new root LLM.md starts an honest standalone history.
- Source completeness scan: 381 literal load/preload references in src/*.gd,
  none missing. This does not validate dynamic paths or external dependencies.

## Fresh validation

Godot `4.6.stable.official.89cea1439`, standard Linux build, Python 3.12.14,
FFmpeg with libx264/AAC. Graphical checks used an owned isolated Xorg dummy
screen and llvmpipe software rendering, never the shared desktop.

| Check | Actual result |
|---|---|
| Before recovery: Python discovery | 146 passed |
| Before recovery: headless engine / animation-block units | 24 / 32 checks passed |
| Recovered Python discovery | 260 run: 259 passed, 1 skipped |
| Recovered headless engine units | 24 checks passed |
| Recovered pose-library corpus | 30 checks passed |
| Procedural pose-library editor integration | 35 checks passed |
| Fresh-process packed / linked / recovery readers | 6 checks passed |
| Movie decoding metadata | H.264, 1920×1080, 24/1 fps, 48 frames, 2 seconds |
| Editor/export agreement | Exact exported frame pixels, asserted by editor test |

The skipped Python test requires the installed independent MMD Tools reader.
No native Miku/Reimu/Scout/VRM fidelity, physical GPU, hardware audio, tablet,
clean-Windows, subjective animation or complete regression acceptance is claimed.
The older-source Linux recovery-liveness limitation from onboarding was not fixed
by this checkpoint; explicit recovery restoration in the pose test is a separate
capability. The full Windows/native verifier was not rerun after recovery.

## Acceptance evidence map (not a completed requirement audit)

This table covers the specification acceptance gates and addendum scenarios.
Existing code and historical reports are not promoted to fresh passes. A complete
feature matrix and full chronological progress-memo review remain work before
selecting a new application implementation increment.

| Requirement | Current cloud evidence / remaining gate |
|---|---|
| CORE-01 import | Procedural rig and room load in pose editor test; general/native import unverified |
| CORE-02 camera | Headless exact frame 0/24/48, quaternion and hold checks pass |
| CORE-03 drawing isolation | Pose test preserves source checksum, camera keys and drawing hash |
| CORE-04 layer toggles | Headless hidden-layer compositing passes; full routed layer UX not rerun |
| CORE-05 cel exposures | Held-twos, boundary and end-exclusive headless checks pass |
| CORE-06 navigation | Space/arrows/focus interactions not freshly exercised |
| CORE-07 save/reopen | Packed, linked and explicit recovery body-pose state passes fresh process |
| CORE-08 export | Procedural pose-library movie: 48 full-HD frames at 24fps / two seconds |
| AUDIO-01 frame-24 onset | Not freshly decoded on recovered source |
| AUDIO-02 silence | Pose-library silent movie succeeds; broader silence cases not rerun |
| REF-01 manual pose | Procedural rig body poses, auto-key/draft, Undo and persistence pass |
| REF-02 reference-only | Not freshly checked on recovered source |
| SEQ-01 nested clips | No completed nested editable sequence gate established |
| KEY-01 chroma key | No completed chroma-import gate established |
| SAFE-01 corrupt data | Python container/pose validation tests pass; full failure matrix remains |
| PERF-01 owner drawing | No physical tablet/artist latency acceptance |
| Addendum A novice workflow | Pose library reuse subset passes; five-minute artist acceptance remains |
| Addendum B cross-ecosystem | Native fixtures/tools absent; not certified |
| Addendum C blocks/presence/visibility | Earlier-source 32 domain checks passed; recovered end-to-end gate not rerun |
| Addendum D physics scopes | Source recovered; no fresh physics recording acceptance |
| Addendum E tutorials | Source recovered; no fresh full Previous/Continue/Fresh acceptance |
| Addendum F crash recovery | Explicit pose recovery passes; automatic newest-valid crash gate not certified |

## Reproduce the scoped baseline

From /workspace/studio-3d-2d, source /workspace/.studio-tools/activate.sh.
Run `python -m unittest discover -s tests -p 'test_*.py'`.
Use the pinned engine with `--headless --path /workspace/studio-3d-2d`, an
absolute writable `--log-file`, and `--script tests/unit.gd`.
Generate the pose corpus with
`python tests/test_pose_library.py --corpus /workspace/has-handoff-audit/pose-library-corpus.json`,
then run tests/pose_library_unit.gd headlessly with that JSON after `--`.

The recovered verify_pose_library.py wrapper is Windows-specific (creation flags,
private-desktop receipts, hard-coded ffprobe). Its underlying GDScript assertions
were run unchanged on the isolated Linux display: tests/pose_library_smoke.gd with
an absolute writable test directory after `--`, followed by a separate process
with the same directory and `--read`. FFprobe assertions were checked separately.
Do not run these graphical scripts on the shared desktop. Preserve any tracked
output files before other test runners overwrite them. Do not automatically invoke
the full tests/verify.py on fixture-free Linux.

Logs, the untouched extracted archive, comparison JSON, backup, corpus and fresh
movies are under /workspace/has-handoff-audit. Those local artifacts are not Git
source and are not a substitute for this recorded scope.

## Remaining work

The recovered source includes Krita import, reusable body poses, Model9 independent
root components, paths, audio trims/fades, drawing improvements and particle work.
These were recovered, not reimplemented. Their existing format changes include
Model9, audio version4 and scene schema5; this checkpoint invents no new schema.
Read their contracts before editing; older readers may refuse newer data.

Finish reading all authoritative documents, including the complete 10,501-line
progress memo, and reconcile the historical feature matrix with actual recovered
code. That full review is not claimed complete here. Then choose one unmet goal,
preserving the confirmed interactions and the existing representation. Native
fixtures should be requested individually only when needed. No deployment or
public distribution is authorized or performed.
