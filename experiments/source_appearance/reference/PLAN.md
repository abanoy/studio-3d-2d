# Static Source appearance prototype

This isolated source copy starts at exact Git revision
`85fa482b3ef1ed752e8a97191b5ea7b235cea7aa`. Nothing is ported into the active
checkout, installed Studio or owner review. All source changes and tests are in
`Studio`; original archives, retained definitions and approved runtimes are read
only. No extraction, Blender application, GPU, network or new runtime was used.

## Implemented in this copy

- `prepare_source.py --appearance <json>` accepts a strict request no larger than
  64 KiB, bound to both the original input checksum and the selected native MDL
  checksum. Duplicate JSON keys, unknown fields, noninteger/negative/excessive
  indices and changed inputs refuse. The worker binds the selected model again.
- `source_appearance.py` validates native bodygroup/skin metadata and the converted
  container's correspondence before changing its disposable objects. Bodygroups
  use native numeric indices, with omitted groups retaining zero. Native zero
  vertex counts establish blanks; labels do not. An all-blank result explicitly
  refuses because this converter requires renderable geometry.
- The bridge uses the pinned SourceIO skin helper, then shows only selected
  variants. Actual selected skin and named/numeric bodygroup indices plus the
  native choice catalogue enter the preparation report. The GLB bakes one static
  appearance; the intermediate retains all imported variants.
- Ordinary default preparation and BSP-prop selection retain the existing branch.
  No new appearance field is added to their worker request, and no app or project
  schema change occurs. Existing edited objects are never reconverted here.

Request example (replace both checksums with the actual reviewed values):

```json
{
  "format": "studio_source_appearance_request_1",
  "source_sha256": "<SHA256 of the original loose MDL or selected archive>",
  "native_mdl_sha256": "<SHA256 of the selected MDL definition>",
  "skin": 2,
  "bodygroups": {"0": 0}
}
```

The placeholders are explanatory, not accepted checksum strings. A new derived
bundle is still required; this prototype does not expose an application selector.

## A material mapping limit found during assessment

The pinned helper remembers initial material-slot identities to switch back from
families that share materials. Its initial inference still uses the default skin
material identity. If several native default columns use the same material but a
requested family assigns different materials to those columns, that inference
cannot identify the intended native column safely. This prototype refuses that
case instead of guessing. Nonidentity default tables also refuse a different
skin because the pinned importer begins from native mesh material indices. A
future explicit native mesh-slot mapping can extend coverage. Nitori's actual
six-column default row is unambiguous and follows the native material table.

Duplicate native bodygroup names are also refused for explicit selection because
the pinned importer stores variants in a dictionary keyed by those names. Missing
or truncated variant lists and native/converted blank mismatches refuse before
calling the skin helper or changing visibility. The ordinary default branch is
unchanged; these new guards do not silently claim its broader native fidelity.

## Actual CPU evidence

Run `python output/source-appearance-prototype/verify_prototype.py` from the active
checkout. The script records 18 new tests and three unchanged conversion-error
tests, zero failures/skips, source hashes and exact commands in
`cpu-verification.json`. It also checks the two already retained MDL hashes against
their requests without decoding or extracting them. Both original archives and
definitions retain exact hashes, lengths and modification stamps; approved runtime
and active source files checked by the probe remain unchanged.

The tests use the actual Nitori three-family table and Keiki's native bodygroup,
blank and `Tools` metadata. They execute the actual pinned skin-helper functions
with inert materials/containers: all three Nitori families and return-to-default,
all seven visible Keiki combinations/all-blank refusal, request transport, exact
old/new default and BSP-prop function behavior, and failure-before-mutation.
The worker path uses its real preparation function with the external process
mocked. These are neither Blender material-slot tests nor real geometry, rig,
morph deformation or converter/exporter results.

## Required next tests, all unrun

`native-fixture-requirements.json` identifies exact archive SHA/size/mtime,
selected MDL SHA, indexed MDL/VVD/VTX sidecars and explicit material-resource
allowlists. Nitori needs five model resources (924,338 bytes); its archive has
225 material resources (133,352,370 bytes). Keiki chisels needs five model
resources (364,092 bytes); its archive has 61 material resources (46,819,684
bytes). Six Nitori and four Keiki native material names each have one indexed
VMT candidate. VMT references and actual dependency resolution remain untested;
an archive index is not evidence that all references resolve.

After authorized staging of those exact full resources, verify actual skin
material remaps and rendered differences, native bodygroup mesh membership,
Keiki `Tools` at zero/nonzero, retained bones/skin/weights/shape identity, and the
default-path regressions. Then implement the app's reviewed pre-adoption choices
with one import Undo/Redo and verify packed/linked HAS, fresh source-offline
reopen, preview/export pixels, actual movies and private-desktop receipts.

Runtime/animated skin or bodygroup switching, native jiggle/assembly fidelity,
artist acceptance and broader native coverage remain separate unfinished work.
Do not promote this CPU prototype as completed appearance support.
