# Unshipped Source appearance experiment

This source-only worker prototype is not loaded by the normal app. It adds
bounded, checksum-bound static skin/bodygroup choices before adopting a new
object. Default conversion remains the existing route. It does not implement
runtime or animated variant switching, native jiggle or model assembly.

Use a new owned checkout at `checkpoint.json`'s exact base commit, then copy the
four overlay files into it. Run `tests/test_source_appearance.py` and the existing
`tests/test_source_failure.py` with the approved Python. Recorded total:
21 CPU checks, zero failures or skips. Native hash bindings were checked against
two retained MDLs; model bytes are not included. The reference verifier is a
session aid and requires review of its owned-output/input paths when relocating.

The real pinned skin functions were executed with inert stand-ins. This is not
a Blender export or rendered material proof. Nonidentity default skin tables and
ambiguous duplicate material columns refuse; an all-empty selection also refuses.
Nitori and Keiki supplied the actual metadata positives. Later fixtures and
validation are in `reference/PLAN.md` and `native-fixture-requirements.json`.

Blender conversion, textures, rig/morph preservation, app review/adoption,
Undo/Redo, portable replay and movie agreement remain unrun. Do not port to the
active application on the strength of CPU tests alone. No private art or native
model/archive payload is included here.

Later native resource preparation is preserved in `native_resources/`:296exact
sidecar/material files were staged locally;34CPU controls and actual10VMT
reference analysis are complete. No native payloads are in Git. Keiki's16refs
resolve; Nitori25/28refs leaves one missing native hairbump resource repeated3times.
Base textures resolve in both, with no substitution or installed fallback.
The source-only serial converter driver has21CPU controls after review; it has
not run actual conversions. Prepare a fresh schema2 input lock at a stable HEAD.
Its retained schema1 lock/preflight is historical and current code refuses it.
See docs/sfm_native_resource_staging_2026-11-12.md. Rendered/native/app acceptance
remains unrun. Recreate the source tree under its documented owned output layout
before invoking these machine-specific helpers; review paths, stamps and hashes.
