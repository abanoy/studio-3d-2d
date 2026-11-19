# Finite synthetic Blender weight-storage API probe — unrun

This future source packet supplies a bounded API observation and CPU oracle.
No Blender/native job, scene/model file, original array, export or installation
was run or read to implement it. It does not change the prior sealed packets,
actual refusal/pass records, Main, application source or current publication.
Root alone may authorize and execute a later native run after source review.
No expired admission is reused and no launcher is implemented here.

The SourceIO rule is pinned to the actual MDL49 importer: create groups in
native bone order, then for each vertex inspect all three slots in order and
call `group.add([vertex], weight, 'REPLACE')` only when weight is positive.
The probe creates 69 synthetic groups and one owned loose-point mesh, with
one vertex for every three-slot product over group IDs `{0,1,2,68}` and exact
F32 words `{+0,-0,minimum-positive-subnormal,.1,.2,.3,1}`. There are exactly
21,952 cases and 47,040 positive calls. Effective shorter histories are already
covered by zero slots. No names, weights or geometry come from an owner model.

The independent event oracle orders each group by its first positive event
and takes its last positive value. That is the candidate behavior being
observed, not a claimed native fact. The expected stored-group histogram for
zero/one/two/three groups is 512/6,740/11,700/3,000. Actual `vertex.groups`
iteration order is captured directly, retaining zero or subnormal readback
words rather than filtering them. Separate expected and observed ordered-row
hashes, all-case mismatch counts/categories and at most 12 synthetic examples
per phase are reported. A failed minimum-subnormal or REPLACE observation
stays failed; no normalization, threshold or value substitution is provided.

Readback occurs immediately after writes and again after the same no-argument
`mesh.validate()` call used by SourceIO. The report distinguishes those phases
and their exact ordered words. Owned object/mesh IDs are removed in `finally`;
preexisting datablock-ID sets must match afterwards. No scene objects are
deleted, no object is linked into a scene, and no operator, exporter, GUI,
window, desktop or process API is called by the probe.

`weight_storage_contract.py` defines the finite alphabet and independent
oracle. `blender_weight_storage_probe.py` is importable without Blender and
imports `bpy` only in its future CLI entry. Eleven CPU tests use explicit fakes
to verify the correct rule and detect sorted groups, first-write retention,
flushed subnormals and validation-time reordering. They exercise failure and
cleanup paths, missing/extra/reordered readback, fresh requests and background
receipt semantics. CPU fakes never establish native storage behavior.

All qualification fields remain false, even when a later bounded synthetic
run matches. These cases do not exhaust all 69 group IDs or all F32 weights;
they do not prove full model correspondence, triangle/save/reopen behavior,
normal fidelity, export, repair or adoption. A later Root qualifier must bind
the precise observed domain/runtime and independently connect any actual
source-row expectations. This packet supplies no universal policy or bypass
for the existing multi-group expectation refusal.

## Future Root-only launch recipe — not executed

1. Obtain fresh authoritative native-lane/graphics closure and permission for
   this synthetic-only run. Recheck the exact approved runtime identities,
   SourceIO/exporter catalogues, current 1029/source context and all original
   tools before and after. The request is not a substitute for these checks.
2. Reserve a fresh single-link, nonreparse directory beneath this workspace's
   `output`. Create `source` and `temp`, and copy only the two runtime scripts
   there with byte-identical packet hashes, verified externally before Blender
   imports either file. The probe's later self-check cannot replace that
   authority; it also checks the actual imported contract module path. Set inherited `TEMP` and `TMP` to
   this owned `temp`. Keep all receipts/logs/output in the same owned directory.
3. Create `request.json` there with exactly the fields shown below. Use a new
   32-character lowercase hex run ID, expiry at most 15 minutes ahead, approved
   Blender identity and exact copied script sizes/hashes. Retain the exact
   request SHA and source packet identity in the outer host evidence.
4. The proposed command is the existing approved wrapper around factory,
   background, disabled-autoexec/offline Blender with one thread. Root must
   construct/review it against current pins; the placeholders are deliberate:

```text
<approved pythonw.exe> <ROOT>/tools/private_desktop.py
  --receipt <OWNED>/private-receipt.json --timeout 120 --memory-limit-mib 4096 --
  <approved blender.exe> --factory-startup --disable-autoexec --offline-mode
  --background --threads 1 --python-exit-code 1
  --python <OWNED>/source/blender_weight_storage_probe.py --
  --plan <OWNED>/request.json
```

5. A separate bounded Root host must retain/wait/reap its wrapper handle with
   a proposed 135-second outer timeout, preserve failed outputs and close its
   owned job. It must require exit 0, no timeout, exact source/request binding,
   all 21,952 immediate/post-validation cases, exact cleanup and appropriate
   authoritative post-run closure. This host has not been implemented here.
6. `qualify_background_receipt` checks the existing wrapper's explicit
   `child_desktop_confirmed=true`, clean job/desktop closure and no foreground
   child or desktop switch. `private_window_seen=false` is acceptable for this
   background API probe. No window or sentinel is fabricated, and no headless
   bypass is added. Missing wrapper child-desktop confirmation still refuses.
   The existing wrapper can confirm via its thread lookup or an owned window
   enumerated on the private desktop; the receipt does not distinguish those
   sources when a window is observed. With no private window observed, its
   confirmation necessarily comes from the thread lookup.

```json
{
  "format": "has_fresh_synthetic_weight_storage_request_1",
  "phase": "ROOT_APPROVED_FRESH_SYNTHETIC_ONLY",
  "run_id": "<fresh lowercase 32-hex value>",
  "expires_utc": "<fresh timezone-aware UTC ISO timestamp>",
  "owned_root": "<absolute OWNED path>",
  "owned_temp": "<absolute OWNED/temp path>",
  "public_output": "<absolute OWNED/PUBLIC_WEIGHT_STORAGE.json path>",
  "runtime": {"path": "<approved Blender absolute path>", "bytes": 0, "sha256": "<approved SHA256>"},
  "scripts": {
    "blender_weight_storage_probe.py": {"bytes": 0, "sha256": "<packet SHA256>"},
    "weight_storage_contract.py": {"bytes": 0, "sha256": "<packet SHA256>"}
  }
}
```

The zero sizes above are placeholders and are rejected by an actual request.
The probe checks its actual binary path and records runtime build/version;
binary hash/size verification remains an explicit Root before/after duty.
It reads only its owned copied scripts and request. It creates only its owned
synthetic datablocks and exclusive public result file, then prints a bounded
`HAS_SYNTHETIC_WEIGHT_STORAGE` status marker. Mismatch exit is 1 with retained
synthetic failure evidence. A status marker alone is never qualification.

After parsing the exclusive result JSON, the Root host can call the pinned
contract's `validate_matching_public_report(report, expected_request_sha256=…,
expected_run_id=…, expected_scripts=…, expected_runtime=…)`. It independently recomputes both
finite hashes, exact coverage/counts/histograms and both phase results, binds
the known request/scripts/runtime descriptors and rejects type-only changes
or canned success markers. It deliberately does not verify an actual binary
hash or a receipt; the outer host must bind those independently and require
fresh authoritative closure and retained-handle wait/reap. A mismatch/failed
file remains retained evidence and is never converted into a passing report.

CPU verification: `python -B -X utf8 -m unittest discover -s experiments/blender_weight_storage_probe_20261118 -p test_weight_storage_probe.py -v`.
