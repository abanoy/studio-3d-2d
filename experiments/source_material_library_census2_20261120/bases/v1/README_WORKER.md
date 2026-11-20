# Empty-request B library enumeration worker

2026-11-20. **AUTHORED, UNRUN.** This worker and its pure fake-RNA/synthetic-file
tests were source-reviewed without Blender, native input reads or executions.
Only library_worker.py, test_library_worker.py and this README are owned here;
Root authors the separate driver. No existing packet or application file changed.

## API and actual observation

`enumerate_library(bpy, owned_path)` takes a caller-authenticated owned B path.
It captures every BlendData RNA collection whose fixed type inherits ID,
retaining actual refs, pointers, exact Python types, name/name_full and library
refs/pointers privately. Unknown collections, aliases, evaluated IDs, pointer
reuse with a different ref or any surviving census change refuse. Collection
iteration order alone is irrelevant.

It calls only `bpy.data.libraries.load(path, link=False)`, reads the public
library directory/name lists and checks **all destination ID requests remain
empty**, before and after context exit. It never assigns a request list. Return:
`{material_names: tuple, summary: dict}`. Names are RAM-only. Public summary has
before/after ID counts, collection/type/name/material counts, catalogue/name
digests, empty-request observation and unchanged-ID-census observation. No ID
rows, pointers, material names, B paths or other source names are public.

Ceilings: 128 ID collections, 4096 actual IDs, 16384 source names; names at most
1024 Unicode characters/4096 UTF8 bytes. Metadata getters never read geometry,
image dimensions/channels/pixels, node graphs or packed contents. This observes
surviving IDs and empty direct requests; it does not prove no transient ID or
C-level read occurred, qualify B resources or label native geometry.

## Root request contract

CLI: `--request PATH --request-sha256 SHA` after Blender's `--` separator.
Request format `has_owned_B_empty_library_census_request_1`, phase
`ROOT_APPROVED_AFTER_FULL_PHYSICALLY_CLOSED`, private_arrays_public=false,
timezone-aware created_utc/expires_utc valid now and at most30minutes apart.

`source_context` requires full_suite_passed/full_job_physically_closed/
exclusive_runtime_lease=true, observed_owned_processes exact integer0,
functional_file_count exact integer1061, and tested_revision
`9e3b039039833adce4723bbb70681595cd4eef16`. It also binds
full_completion_sha256/graphics_release_sha256 to the corresponding file rows.
The driver owns the heavy whole-suite/source/Git/lease/physical verification.
The worker additionally checks pinned completion.whole_verifier_pass and
release.full_suite_passed are true.

`files` has exactly seven `{path, bytes, sha256}` rows:

| Role | Required identity/boundary |
| --- | --- |
| probe | actual library_worker.py; exact Root driver-pinned bytes |
| support_worker | published `experiments/source_current_native_ids_20261120/fresh_current_id_probe.py`,35572B, SHA256 `d78369585463dcc2a511e00889f7e768e10c61004cf4f3fac0df3885b7d60c93` |
| sentinel | setter_probe.py,17989B, SHA256 `034122697e8fa0e7a855ea42b51eddc351b647ae5f7641cad8d02994a51fc3c3` |
| blend | owned_stage/inputs/material-source.blend,2423175B, SHA256 `ead1f1913812593abd69e353fed375944a15f280738784886fcef7fda3ee65c6` |
| full_completion | Root-pinned successful whole-suite receipt |
| graphics_release | fresh Root-pinned graphics/lease release |
| blender_exe | exact installed Blender5.1,108687824B, SHA256 `1e6624af112b3c936f4b038b025ebd2bf00ae72c4b62881a6787166d71c58fa5` |

owned_stage must be inside this checkout's output; owned_output is exactly its
existing result directory and owned_temp exactly its existing temp directory.
TEMP, TMP and Python's selected temporary directory must match. Both public
result filenames must be absent. All paths pass the pinned support's link/
reparse guard. Seven rows plus root_request yield **eight retained input
identity records**; reads are repeated for preservation, not counted as exactly
eight underlying OS read calls.

Support is authenticated before import, then created with importlib's module
spec and compiled from its exact pinned raw bytes, avoiding pyc execution.
Only its safe/pinned_read/placement_sentinel helpers are used. Its main, native
imports and SourceIO loader never run. The owned zero-size hidden sentinel is
held for0.5seconds before bpy import. Root's unchanged outer private-desktop
monitor establishes placement and later job/desktop closure.

The actual host must be Windows little-endian Python3.13, Blender background,
factory filepathempty, offline and autoexec disabled; those context properties
remain checked after enumeration. This exact B must enumerate four Materials.
No scene open, material append, SourceIO import, mesh binding, save, render,
export, image getters or native labels are requested.

## Results and tests

result/PUBLIC_LIBRARY_ENUMERATION.json has format
`has_owned_B_empty_library_census_result_1`; success is
`ENUMERATED_WITH_EMPTY_REQUESTS_AND_UNCHANGED_ID_CENSUS`.
result/PLACEMENT_LIBRARY_ENUMERATION.json has format
`has_owned_B_empty_library_placement_1`, the original sentinel policy and
worker_verified_hidden_sentinel_closed. Both are capped at64KiB. Every retained
input is rehashed with size/stamp before publication. Only success plus input
preservation and sentinel closure returns0; outer physical closure remains a
driver duty. All fidelity/resource/binding/adoption flags stay false.

Prospective Root-only pure CPU command, **not executed by the author**:

```powershell
& 'C:\Program Files\Python313\python.exe' -B -m unittest discover -s 'C:\a\Programming\cloudflare\has-body-addition-20261120\output\source-material-library-prep-20261120' -p 'test_library_worker.py' -v
```

Tests use fake RNA/library contexts and synthetic temporary text only. They
cover unchanged genuine refs versus pointer-equal replacements, all collection
additions/removals/names/libraries, no image getter access, empty-request checks
across exit, source names/schema/digest order/budgets, fresh mandatory Root
context and raw authenticated support import. No test imports Blender/SourceIO
or reads a B/native asset. Actual API/empty-load behavior remains for Root's
separate qualified private job after these CPU checks pass.
