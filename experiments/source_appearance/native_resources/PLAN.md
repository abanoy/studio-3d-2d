# Next supplied SFM native cases

This is planning and request-schema/hash-binding evidence only. No archive was
extracted, no Blender application or GPU was run, and no application source,
review source, original model or installed tool was changed. The source-only
appearance overlay remains unshipped at base
`85fa482b3ef1ed752e8a97191b5ea7b235cea7aa`; its published checkpoint is `c6782d2`.

The owner supplied 22 archives/82 MDLs, representing 71 different definitions.
The current native inventory records 28 files/27 definitions with differing
skins and 55 files/46 definitions with JIGGLE declarations. The two cases below
are the first bounded static-appearance tests, not substitutes for facial,
procedural, component-binding or broader native model coverage.

## Exact next cases

| Case | Native evidence | Future positive cases | Deliberate refusal |
| --- | --- | --- | --- |
| Nitori tanktop glove | MDL49 SHA `44cece1f44dfc3d7b32b91b5acfdae53ec9f6f90a0220a422ace92e323da7b32`; 66 native bones; one glove group, visible choice 0 has 6,544 vertices/2 meshes, choice 1 has zero geometry; three distinct six-column skin families; native flex `Ah`; no procedural bones | Skin 0/1/2, glove choice 0; ordinary default without an appearance request | Glove choice 1 leaves no renderable geometry |
| Keiki chisels | MDL49 SHA `d8b32165bef2ec4f1c09acd19b3b136b3492b556fcfb9da98fb01826c5e279ff`; 31 bones; tools/box/flame groups at indices 0/1/2; visible choice 0 has 1,180/38/1,479 native vertices, respectively; each choice 1 is genuinely zero geometry; `Tools` controller/descriptor 0, FETCH1(0), range 0..1; one skin; no procedural bones | All seven visible combinations; ordinary default without an appearance request; Tools 0/nonzero on the four combinations with tools present | Indices 1/1/1 leave no renderable geometry |

Native counts describe MDL metadata. Do not assert equal final GLB vertex counts:
VTX selection, shared vertices, material splits and export layout can change the
representation. Preserve actual per-primitive attributes and correspondence.

`plan.json` contains the exact native records, original archive identities,
five sidecars per candidate, material allowlists, VMT candidates and 14 future
command arrays. Twelve request files are in `requests/`. Their schemas and
binding to the two existing retained MDLs were checked; this does not prove the
skin/bodygroup choices can convert or render.

## A route constraint that must be respected

`prepare_source.py` accepts loose MDL/BSP, VPK, GMA and legacy BIN. It does not
accept these RAR/ZIP archives. Stage the selected full resources first using a
fresh owned resource allowlist, then call it on the staged loose MDL. On that
route both `source_sha256` and `native_mdl_sha256` are the selected MDL SHA. The
original RAR SHA and member identity belong in the external staging provenance.
A request bound to the RAR SHA will refuse when the input is the loose MDL.

The command arrays intentionally reference future staging paths. They are not
ready-to-run commands until the staging, worker-source and runtime checks below
pass. They use the existing approved Blender 5.1 executable and pinned SourceIO
fe242, not a new download or installation. Root retains the graphics/Blender
lease; do not launch these concurrently with its canonical run.

## Resource closure before conversion

1. Re-read each original archive index and compare it with the saved allowlist.
   Reject traversal, device names, streams, links/reparse targets, encryption,
   duplicate case-insensitive paths, changed member sizes/CRCs and unlisted
   suffixes. Reuse the audited metadata-stager's guards, but do not call that
   MDL-only tool as if it staged VVD/VTX/materials. New full-resource staging
   still needs a reviewed bounded implementation.
2. Preserve the original package directory layout. Stage all five selected
   model resources. Either parse a transitive closure of the six Nitori/four
   Keiki VMTs and their texture/patch references, or use the explicit complete
   material allowlists as a bounded first option. The latter is 230 files /
   134,276,708 bytes for Nitori and 66 files / 47,183,776 bytes for Keiki: 296
   files / 181,460,484 bytes combined. No model scripts or executables belong in
   staging. Hash every staged resource and verify each indexed CRC/length.
3. Keep the originals read-only and record SHA/size/mtime before and after.
   The retained MDLs are insufficient: they have no VVD/VTX or texture payloads.
4. The prepared empty mount-plan file suppresses appending discovered game
   mounts. The loose route still uses its own copied model sidecars and the
   staged content root containing the sibling `models` and `materials` folders.
   Verify every resolved provider remains under the owned staging/conversion
   roots. Installed Steam files must not silently fill a missing fixture input.
5. Read actual VMTs. An indexed VMT candidate is not proof of texture closure.
   Record patch includes, base/alpha textures and other referenced resources.
   Classify optional failed lookup probes separately from an unresolved active
   VMT/base texture. Report every warning; an active fallback-gray material
   fails this appearance comparison. The bridge currently converts materials
   from hidden variants too, so label inactive-resource diagnostics explicitly.

## Required native assertions

| Stage | Assertion and independent evidence |
| --- | --- |
| Import/report | Preparation reports the original loose MDL checksum, native checksum, exact requested skin and both named/numeric group indices. Native choice catalogue equals the inventory. Ordinary no-request default and explicit all-zero choices select the same geometry/material semantics. Existing BSP/default branch checks still pass. |
| Nitori material selection | Record native material column -> Blender mesh slot -> selected family material -> VMT -> embedded GLB image/material for each active slot. Check all three native rows, including duplicate destination materials in skins 1/2. Mesh positions/indices/UVs/normals, rest skeleton, weights and applicable morph accessors stay equal across skins; only intended material/image references differ. Actual pixels must change in the affected glove region under a fixed camera/light. Wrong-family negative control must fail the oracle. |
| Keiki membership | For each of seven combinations, match selected native group/object and final GLB primitive membership. Present groups appear once and blank groups contribute no geometry. Compare each retained group's decoded geometry, material, skin and morph data against the same group in the all-present baseline. Single-group cases discriminate tools/box/flame; wrong-group and retained-hidden-mesh negative controls must fail. |
| Rig preservation | Bind every eligible original native bone by its recorded identity, parent/rest transform and inverse bind. Verify normalized weights and their actual joint bindings, rather than equating runtime bone count with the native count. Pose a bound limb/tool bone and compare skinning with an independent frozen source-pose reference; source bytes remain exact. |
| Morph preservation | Nitori's `Ah` and Keiki's `Tools` are native descriptors, not automatic proof of exported targets. Inspect actual source deltas and prepared targets. For Keiki with tools present, compare Tools at 0, an interior value and 1 against native selected-group deltas; prove affected tools vertices move and unrelated box/flame vertices remain unchanged. When tools are blank, absence of that group's target is expected; do not claim morph loss or apply a stale target to another mesh. A removed/wrong-target control must fail. |
| Refusal | Each all-blank request produces the explicit actionable geometry refusal, no successful scene GLB or import adoption, and no changed project/source/Undo state. Retain failed logs and partial owned outputs. |
| App integration, still unimplemented | Review native choices before adopting a new object. Cancel/error leaves the scene untouched. A successful import is one Undo/Redo transaction and records the chosen appearance/provenance. Do not reconvert an existing edited object to fake switching; it can invalidate target/helper identity. |
| Persistence and render | After the app integration exists, verify linked and packed HAS, a fresh source-offline process, exact source/choice metadata, shape keys and pose keys, Undo/Redo, independent preview/export pixel agreement and a real H264 movie with private-desktop receipts. A converter exit alone passes none of these. |

## Interpretation limits

The pinned skin helper infers native material columns from initial material
identity. The prototype refuses differing skins when default columns are
ambiguous or the default skin table is nonidentity. Both selected fixtures meet
the CPU metadata preconditions; actual Blender slots remain untested. Duplicate
native bodygroup names also refuse because the importer keys its dictionary by
name. Do not weaken these guards to get a fixture through.

The bridge implements a basic Base Color/alpha PBR approximation. Material names
containing `glow` do not establish emissive output, native self-illumination,
proxies, specular/Phong/environment-map or shader fidelity. Neither selected
candidate has native procedural bones. Junko v25 hair's 49 JIGGLE declarations
and possible main/hair assembly remain a separate later case; matching six bone
names and parents does not prove rest/bind alignment or Source bone merge.

All 82 supplied definitions have one-frame animation headers in the inventory.
They do not supply a positive moving-native-sequence test. Keep Scout compound,
signed/stereo controls, native sequences/IK, animated/runtime skin/bodygroups,
procedural physics, full assembly and artist acceptance separately pending.

## This planning run

`request-binding-checks.json` records 12 schema/hash-binding-only checks.
`preservation.json` records unchanged SHA/size/mtime for the two original RARs,
two retained MDLs, reviewed prototype sources and input metadata. No native
conversion, extraction, Blender/GPU, network, app adoption or owner observation
occurred. Promote the plan/evidence into Git only after root review; never add
the private resource payloads.
