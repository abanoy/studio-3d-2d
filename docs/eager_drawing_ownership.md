# Ownership when accepting eager projects

Small projects and the explicit eager decoding mode still use the existing Image
loader without compression during Open. Before the application installs the
candidate project, it now registers those Images as raster owners in one
project-owned cache. Nested child drawings use the same cache. Existing adaptive
owners keep their original identities and cache.

Preparation checks the complete incoming graph before publishing any cel changes.
A missing/invalid late child or incompatible cache refuses the candidate without
installing a partially adopted project. Wrapping preserves Image identity and RGBA;
it does not paint, resample, compress or change the stored project schema. The
standalone Storage eager API continues to return eager Images.

Once accepted, eager drawings take part in the existing soft hot-memory budget,
owner-addressed pixel Undo and idle cooling. Borrowed writable Image handles and
incompressible artwork still prevent release. The counter is conservative logical
ownership accounting, not physical/RSS/GPU measurement or a hard admission limit.
The 32-cel limit is unchanged. Clipboard, history tiles, derived resources and
whole-project admission remain independent work.

`tests/project_raster_ownership_unit.gd` checks root/child adoption, exact identity,
accounting, idempotence, independent edits, atomic refusal, cache mismatch and
exact cold rehydration. `verify_cel_raster_reader.py` without adaptive/automatic
flags now exercises eager-decoded input through the ordinary application,
including drawing Undo/Redo, source preservation, packed cold Open, real abrupt
recovery, preview and H264/AAC output. A separate masked nested-sequence workflow
covers parent/child navigation and recovery.

See [recorded evidence](benchmarks/eager_drawing_ownership_2026-11-06.json).
Native Windows, hardware and native-format fidelity are separate acceptance gates.
