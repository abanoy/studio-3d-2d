# Static Source brush lightmaps

The Source adapter now attempts to retain static LDR brush lightmaps. It matches
pinned SourceIO decoded faces to their exact float32 brush geometry, projects the
existing material UVs into luxel space and combines the base texture with bilinear
RGBExp32 lighting. Duplicate/ambiguous geometry, invalid bounds and unsupported
surfaces produce diagnostics rather than guessed lighting. No native file changes
or Source shader/gameplay execution occur.

Padded emission atlases preserve the static result without adding direct-light
illumination twice. The existing **Lit / Unshaded** control switches between baked
lighting and the original base colors/textures. Fresh GLB material metadata retains
both appearances; per-instance material copies implement Unshaded and fades.
SceneIO also restores explicit glTF emission UV1 selection and zero specular
response, which Godot4.6 otherwise drops. Current packed HAS, recovery and final
rendering use the same material interpretation. Existing projects remain readable.

The implementation handles static style0 LDR brush samples. HDR-only/styled light,
displacements, directional bump-light reconstruction and exact Source photometry
remain unsupported. Per-face baking is bounded to512pixels; reductions are
reported. Each atlas is at most2048square and consumes the existing512MiB decoded
texture budget. A brush capture accepts at most16384faces. Atlas overflow or
unsupported faces retain the ordinary material and a readable limitation report.
These are practical preservation bounds, not native renderer equivalence.

The final original decoded-record fixture verifies the exact production capture/
bake boundary, real Blender4.3.2 export, UV1/emission-strength metadata, original
striped texture, LDR color orientation, lighting independence, mode switching,
source-offline packed replay, provenance, recovery and exact movie input.
8Python contract checks and13actual-app checks pass with a48frame1080p24H264 movie.
47visibility/fade/material-isolation checks and18static-entity-light checks also
pass. Optional Draco compression is unavailable; uncompressed exports succeeded.

A complete approved native BSP plus recognized installed SFM/GMod content is still
needed to validate the complete native path. This original decoded-record fixture
does not establish that acceptance. Owner-supplied SFM model archives now support
separate read-only parser/dependency tests; they do not supply a BSP or installed
Source host. See [the evidence receipt](benchmarks/source_brush_lightmaps_2026-11-07.json).
