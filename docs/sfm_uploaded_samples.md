# Owner-supplied SFM samples

The22uploaded archives contain82MDL49 files,1,044VMT files and640VTF files
(401unique texture payloads). Every native MDL parsed with the pinned SourceIO
reader and has a valid bone-parent hierarchy. All401unique textures decoded to
finite RGBA arrays with matching dimensions. All22archive hashes and2,089extracted
file hashes remain unchanged. Archives, extracted assets and auxiliary scripts stay
private outside Git; no supplied script or document instruction was executed.

The samples exposed a Linux loose-resource bug: Source paths are case-insensitive,
while the staging and loose-file provider used exact filesystem spelling.
24sidecar spellings differ in case. The new bounded lookup resolves every model's
geometry set and checks its MDL/VVD/VTX identity. It refuses case ambiguities,
mount escapes and excessive directory indexes. Managed copies use a consistent
basename while native reports retain the original sidecar names. Original files
are not renamed. All78Source unit checks pass, including8new case-lookup cases.

Dependency diagnostics remain separate from decode success.80models have all
referenced VMT files in their own package. Reisen has an unresolved`,`material
slot; Momoyo references`models/touhou/tamo/momoyo himemushi/Baby`. The standalone
package audit reports38texture references needing additional dependencies.
Four circle materials have a missing closing brace that SourceIO recovers at EOF.
These diagnostics are recorded; no source materials were repaired or substituted.

The documented SourceIO archive checksum was verified before loading its code.
Its Linux native binary requires GLIBC2.43; the host has2.41. The unchanged pinned
binary ran in an offline compatible container with read-only sample mounts, a
non-root user and dedicated output. The host was not upgraded. The tested runtime
image ID and decoder hash are retained in the receipt. A pinned-base Dockerfile is
at`tools/docker/sourceio_metadata.Dockerfile`.

A separate [compatible Blender worker runtime](sourceio_worker_runtime.md) now
imports the full SourceIO bindings and exports an original skinned, morph-animated
GLB. Its offline probe does not load these owner samples and does not bypass the
installed-game requirement. This removes the host ABI obstacle for runtime
preparation; it does not establish native conversion or app fidelity.

Full native conversion, mesh/material appearance, posing, HAS replay and movie
acceptance remain unrun for these models. The actual preparation command still
refuses before creating output because no recognized installed SFM/GMod host is
available. The installed-game requirement was preserved. This metadata/codec
inspection does not certify native app or rig/physics fidelity. An existing
cloud-accessible installation path has been requested; BSP/MMD/VRM and Windows/
artist/device prerequisites remain separate.

Reproduce against the private cloud inventory:

```sh
python tests/verify_sfm_readonly.py \
  --inventory /workspace/has-handoff-audit/sfm_extracted_inventory.json \
  --asset-root /workspace/has-private-sfm \
  --sourceio /workspace/.studio-tools/sourceio-source/SourceIO-fe24260b97ac03b899d9b5d4f0fd7b34772f3647 \
  --sourceio-archive /workspace/.studio-tools/sourceio-fe24260.zip \
  --archive-index /workspace/has-handoff-audit/sfm_uploaded_inventory.json \
  --output /absolute/new-evidence-folder
```

The private inventory contains archive provenance, explicit extracted folders,
relative member hashes and model paths. The runner verifies the entire pinned
SourceIO archive, freezes functional sources, uses the local Docker daemon and
never uploads assets. The two native probes are reviewable test source.
See [the receipt](benchmarks/sfm_uploaded_samples_2026-11-07.json).
