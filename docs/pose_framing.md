# Framing the current model pose

Frame model and World > Frame selected use the current deformed mesh, including
HAS base shapes and animated positional expressions. A posed or fallen model can
therefore be found where it currently appears, rather than at its imported rest
location. Hidden selected models can still be framed without turning them on.
Frame scene uses the same query for its selected environment subtree.

This changes the temporary editor view. Camera keys remain explicit. Framing does
not freeze live physics, record motion, change object visibility, edit poses or
add an Undo entry. The camera's existing near plane is respected for tiny models.
Ordinary project/HAS versions and native model identities are unchanged.

## Implementation and limits

`pose_bounds.gd` reads shared SourceShape vertices and the current skin palette on
demand. Immediate static edits use fresh skeleton transforms. Physical modifiers
restore their base bone poses outside their processing callback, so PhysicsRig
publishes the final globals it already captures there. The transient skeleton
cache has a weak provider reference and is removed on stop/disposal; it is never
project data. Secondary-only posing uses its current FK transforms. Import
placement continues to use its existing shaped bind bounds.

Exact deformation is bounded to 200,000 vertices across the requested subtree,
four/eight influences and 512 bind transforms. Larger affected meshes use the
union of their shaped box transformed by every skin bind plus the original box.
This deliberately includes extra space; it relies on ordinary normalized,
nonnegative skin weights. Invalid exact-query data refuses without moving the
camera. At most 100,000 hierarchy nodes are visited. Unsupported custom shader
vertex motion, particles and MultiMesh geometry are not inferred. Framing is an
explicit synchronous operation, not a new per-frame deformation pass.

Lifecycle checks also exposed stale references in the existing native secondary
adapter. Source nodes are now tagged before generation and resolved from the live
scene tree by exact source ID. The adapter avoids GLTFState's discarded node
placeholders, retaining generated native bone identities and refusing ambiguous
non-bone bindings. Duplicate display names are not used as identity guesses.

## Verification

Run `python -u tests/verify_pose_bounds.py` in an approved Windows execution
context. All graphical work uses the private desktop launcher with no visible
fallback. The focused runner checks current and immediate poses, transformed
parents, named binds, normalized eight-influence geometry, signed morphs, hidden
selection, bounded fallback, small models and refusal on empty geometry. It
compares to independent Godot morph and skeleton mesh snapshots, then checks every
vertex against the framed camera. Native MMD/GMod/SFM/VRM0/1 fixtures are used when
the local prepared assets are available; the report lists what was actually run.
Live motion, stop/disposal cache cleanup, frozen packed-HAS reopen, exact authored
camera/cel export and a 48-frame 1080p24 MP4 are included. This wrapper is part of
the full verifier. See the latest progress memo for actual run results and whether
the worktree or canonical application was tested.

The eight-weight fixture uses integer UNORM16 units totaling 65535. Eight equal
eighths quantize to a sum below one: the engine's affine bake and direct weighted
point sum then differ slightly. Earlier failed diagnostic runs are retained;
the exact normalized fixture avoids changing the comparison tolerance.

## Primary references

- [Godot 4.6 MeshInstance3D](https://docs.godotengine.org/en/4.6/classes/class_meshinstance3d.html): skeleton bake omits blend shapes, so tests apply morphs separately.
- [Godot 4.6 SkeletonModifier3D](https://docs.godotengine.org/en/4.6/classes/class_skeletonmodifier3d.html): final modified poses are available during modification_processed.
- [Pinned 4.6 engine mesh baking](https://github.com/godotengine/godot/blob/4.6-stable/scene/3d/mesh_instance_3d.cpp): registered palette and four/eight influence behavior. No engine implementation copied.
- [Pinned 4.6 glTF scene generation](https://github.com/godotengine/godot/blob/4.6-stable/modules/gltf/gltf_document.cpp): metadata propagation to generated nodes and skinned-node reparenting.
