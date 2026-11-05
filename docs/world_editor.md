# Multi-object editor integration checkpoint

Status: **ordinary append importing, selection, posing, map transforms, Undo,
New/Open, complete saves and recovery restore work**. New uses an empty schema4
world. Legacy schema1–3 projects remain readable with their original defaults; the
next Add promotes existing content and appends an instance.

## Controls

- The World tree mirrors groups, maps and child actors using stable instance IDs.
- Click any visible object to select it without moving the camera. Map/group roots
  use the same move/rotate/uniform-scale controls; no source-specific pose engine.
- Hold Alt for bone reveal; release to hide. Bone/root edits auto-key; camera keys
  remain explicit. Hidden-parent selection shows an editor-only green ghost.
- Switching selection finishes an active drag on its original object. Undo/Redo
  restores that object's data even while another object remains selected.
- Parent transforms carry complete child sets. Root world-axis gizmos convert motion
  through rotated/scaled parents; local fields remain relative to the parent.

Selection meshes occupy helper layer20, preserve original skins/materials/layers and
stop at child instance boundaries. Up to64distinct ID colors distinguish repeated
instances of the same GLB. The outline compares color distance; parent selection can
outline descendants while picking still identifies the individual objects. The mask
uses nearest texture sampling, avoiding false IDs from interpolating neighboring colors.

## Data and save safety

Pose history stores `world_object` plus `object_id`, `before`, `after`. Restoring an
instance validates the complete resulting world record and its rig bindings. A pose
command cannot replace an asset or reparent an instance; structural Add/Remove commands snapshot the complete world. Reparent UI remains pending.
Runtime snapshots gather the current instance dictionaries after Undo, rather than
returning stale original rows.

When a world is installed, HAS, directory Save and recovery checkpoints use schema4
with every instance. Linked source inventory and recovery budget estimates include
unique shared assets. Legacy documents keep their existing schema3 path. Normal Open validates every GLB and rig before replacing the whole document. Add
retains an immutable managed revision even if its source changes. Linked saves use
matching originals or a persistent adjacent sidecar when a managed cache is involved.
Remove includes descendants; Undo restores the full set without changing other poses.

## Verification

Run `python tests/verify_world_edit.py` on a render-capable Windows desktop. It authors
the runtime fixture, runs37actual app checks and reopens authored, linked and native
HAS files in separate renderer processes. It verifies full-HD MP4/frame count and
reports pixel differences, native fixtures tested and all64GPU IDs picked correctly.

Checks include independent shared-asset rigs, map XYZ keys/child movement, parent
visibility ghosts, root gizmos through rotation/scale, Undo across selection, active
drag ownership, bad bone preservation, packed/linked/directory/recovery writes,
independent RGBA composition and actual app movie export. Prepared Miku, ValveBiped
and Scout are also selected/deformed/auto-keyed and undone beside one another; those
private inputs are optional and explicitly skipped when absent. Native source bytes
remain unchanged. Existing tests/world_selection_smoke.gd retains the original41
selection/gesture/outline/Alt regression checks.

Tests route app events/use real UI controls, GPU images, file workers and FFmpeg.
They do not certify physical mouse/tablet comfort, arbitrary DPI, native shader
fidelity, clean-machine setup or subjective sound. See progress_memo.md for final
canonical results. `tests/verify_world_workflow.py` exercises normal Add/Undo/Remove/
Save/Open/New/recovery/legacy transitions with two maps, two actors, drawing and WAV.
Remaining product work includes reparent UI, full multi-object timeline lanes/clips, keyed
visibility/fades, IK/physics and the rest of the governing addendum.
