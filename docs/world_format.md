# Multi-object world record — schema 4 foundation

Status: **normal multi-object Add/New/Open/Save/recovery and rendering are connected**.
New documents use schema4. Legacy schema1–3 reads retain original defaults and promote
all existing content on the next Add. Detached complete validation precedes live replacement.

## Versioning and canonical data

The existing `.has` ZIP container remains version1. Its project.json can now use
schema4, with `world: {format: "studio_world_1", objects: [...]}`. There are no obsolete
`scene`/`model` slots in schema4. Schema1–3 directory readers and schema3 HAS remain
supported. `world_document.gd.from_legacy` explicitly converts loaded scene/model data
to two world records, preserving native metadata, poses and original geometry hashes.
Unusual legacy IDs get a stable replacement plus their original value in metadata;
scene/model collisions are resolved without mutating the original loaded document.

Each object uses the existing **studio_model_1** transform/pose/asset contract plus:

| Field | Meaning |
|---|---|
| `id` | Stable unique instance ID, independent of shared asset checksum. |
| `kind` | `environment`, `model` or `group`; all use the same normalized GLB/model record. |
| `parent_id` | Empty for world root, otherwise another object ID. Missing parents/cycles reject. |
| `start_frame` | First presence frame, separate from static visibility and pose key evaluation. |
| `position`, `rotation_xyzw`, `scale` | Local editable root transform, independent of source geometry. |
| `pose`, `draft_frame`, `pose_keys` | Existing sparse bone/root data with master-frame timing. |
| `metadata` | Original adapter/native parameters and unknown fields retained as data. |
| `source` / `path`, `sha256` | Runtime local source / portable content-addressed GLB reference. |

An empty group may reference the same tiny mesh-free GLB used by other empty groups.
The prototype uses one asset-backed record for all roles, not a separate MMD/GMod
pose engine or new native asset extension. Source format labels never change this
contract. Maps are independently transformable records in the normal editor.

Multiple instances of the same GLB retain independent IDs, hierarchy, poses, placement
and presence, while the package stores the geometry once under `assets/<sha256>.glb`.
This proves **disk/package deduplication**, not runtime GPU resource sharing yet.
The runtime builds separate rig/node instances; it does not promise shared GPU textures
or geometry memory across repeated imports.
Empty schema4 worlds can have zero assets and zero drawing layers. Camera, video,
RGBA cels, audio, editor frame and recovery metadata remain the existing project fields.

## Validation and bounded saves

`World.validate` checks complete records,64-object bound, IDs, root/pose values, source
identity, integer presence and acyclic parents. Portable paths must exactly match the
content-addressed asset identity; no absolute/external paths are embedded as playback
references. `Storage` verifies unique source hashes before committing, copies shared
geometry once, reads all world asset hashes and validates before returning the data.
Unknown native metadata remains data. UI/runtime still must validate all bone bindings
before swapping any live world; the package reader test does that for its fixtures.

Existing128MiB GLB,1MiB metadata,512MiB HAS expanded/archive and128-file limits remain.
Current project reader still bounds1080p/240frames/32cels/one PCM WAV. This increment
does not claim giant-scene performance, frame3000 timeline editing or unlimited rigs.
The world domain can represent later frames when supplied a larger duration; editor
time/clip scaling is subsequent work. Presence/parent visibility and multiple actors
now evaluate in the renderer. Map root gizmos and multi-object selection now work on a prepared world. Visibility
fades, physics and clip operations are not wired into the UI yet.

Both Python HAS inventory and GDScript reader reject invalid parent graphs, duplicate
IDs, unsafe asset references, unsupported versions and ambiguous old slots. Failed
saves preserve complete prior files. A corrupt current schema4 graph does not replace
a previous good manifest/container backup. This is not a power-loss/hostile-file guarantee.

## Reproduce the foundation checks

`python tests/verify_world_document.py` runs22 Python tests (13existing container tests
plus9world cases),36 real Godot storage checks, and separate package-reader processes:

- Five authored records: two maps, two independently posed/present actors and one group.
- Packed reopen with original fixture inputs temporarily moved, and linked relocation
  with three unique geometry relinks rather than one prompt per instance.
- Exact canonical world records, drawing pixels and audio timing after package reopen.
- A zero-object package and a native package normalized from actual prepared
  MMD/Miku, GMod/ValveBiped and SFM/Scout projects, with every GLB decoded and stored
  poses checked against the actual skeleton bindings.
- Missing/changed assets, invalid hierarchy/presence/scale, unsafe paths, unknown
  formats, legacy migration/IDs and preserving prior valid saves/backups.

Python unit payloads are intentionally opaque inventory fixtures; those tests do not
prove geometry decoding. The Godot/package-reader cases use actual GLBs and native
fixtures. They prove persistence and binding, **not simultaneous multi-object rendering**.
Full `tests/verify.py` also includes the storage smoke alongside current app regressions.

## Normal document transitions

Add scene/model append at frame0, preserving all existing object IDs/poses, shot keys,
cels and audio. Imports retain immutable content-addressed GLBs under output/imports.
Structural Add/Remove history restores whole worlds; failed restoration keeps live
state and Undo/Redo stacks. Remove also removes descendants. Ordinary New has no
fabricated environment asset. Normal Open/recovery rebuild every object and clear
selection. Zero-layer imported worlds gain empty Rough/Ink templates for usable drawing.
Linked saves prefer unchanged originals; changed/moved originals use managed revisions,
externalized into persistent HAS sidecars. Full clip/lifetime editing is still pending.

## Multi-object renderer checkpoint

`world_runtime.gd` prepares detached GLB/model instances and checks every stored bone
binding before installation. Inventory happens before parenting, so independent
child rigs cannot become part of a parent's bone inventory. A deterministic topological
order attaches/evaluates parents before children, independent of serialization order.
Transforms are local to the parent's normalized imported root, including its existing
base transform. Group rotation/translation/uniform scale carry whole child sets.

`renderer.gd.prepare_world/install_world` replaces a complete prepared world in one
step, emitting one asset-change notification. Bad files/rigs/graphs keep the old world.
Legacy single-slot calls refuse to partially overwrite an installed multi-object world.
Every instance samples the master integer frame, retains an independent rig and
honors first presence, static visibility and reference-only flags. Hidden/absent parents
hide children through the actual scene hierarchy; they do not rewrite child flags.
Final capture restores the editor's reference visibility after reading the image.

`python tests/verify_world_runtime.py` runs43 actual renderer checks, a two-map/two-actor
movie with independent screen-space drawing, and a packed HAS reopen in a separate
process with authored inputs moved away. Actual prepared MMD/GMod/SFM rigs coexist,
contribute separate pixels and deform independently. This is rendering/persistence
evidence. Normal Add/New/Open and recovery now use this registry. No unlimited-world-size claim. See progress_memo.md for
final canonical results, intermediate failures and unchanged original-source checks.


## Stable-ID editor controls and saves

WorldSelection builds a nested tree and distinct GPU ID colors for up to64instances.
Copies stop at child instance boundaries, avoiding duplicate mesh ownership. Picking
uses nearest color matching; the outline shader compares color distance instead of
confusing nonprimary ID colors with another object. A selected group outlines its
descendants; hidden-parent selection produces an editor ghost without changing
visibility data. Shot cameras still exclude helper layer20.

PoseEditor resolves the active instance through Renderer.active_model(), keeping
legacy model slots separate from the world registry. Maps/groups use the same root
XYZ/rotate/uniform-scale controls. Root world-axis gizmos convert through parent
rotation/scale. World history snapshots include a stable object_id; Undo/Redo can
restore another instance while retaining the user's current selection. Selection
switches finish a pending drag on its original target first.

Runtime.snapshot reads current instance data, including dictionary replacements from
Undo. restore_instance validates the entire resulting record and bone bindings, and
rejects asset replacement/reparenting through a pose command. HAS, directory Save and
recovery writers now pass all world records; linked source inventory and recovery
estimates include unique world assets. Ordinary import/New/Open and structural Add/Remove Undo now work; reparent UI and
timeline clips remain next. See world_editor.md for normal workflow tests.
