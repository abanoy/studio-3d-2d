# Selection raster mismatch: causal review

The pixel mismatch belongs to the **CPU-baked raster reference**, with no
selection-camera, alpha or geometry-ownership defect demonstrated. Its exact
internal floating-point arithmetic location remains uninstrumented.

Two unchanged five-model replays preserved67checks/1failure: only VRM0 frame6,
reference-only pixel(439,91), live5990 versus baked5991 foreground pixels. The
nearest live foreground is(441,91), exactly2pixels away. Both cameras and their
projection matrices match exactly at907x335 in the original1400x900 window.

The reference pixel centre lies only **0.0000943704pixels** inside an edge of Hair
surface2, triangle4869, material `N00_000_Hair_00_HAIR_03`. Complete private masks,
9x9RGBA neighbourhood and primitive data remain in the probe folders.

## Controls

| Controlled reference | Result at the unchanged frame/view |
| --- | --- |
| CPU-baked, original alpha |1different pixel,1outside the one-pixel bound |
| CPU-baked, alpha disabled |Same1pixel difference |
| CPU-baked, only Hair surface2, opaque |685reference versus684live; same1pixel |
| Original-source GPU mesh/skin, original alpha |Exact0different/outside;5990pixels |
| Original-source GPU Hair surface2, opaque |Exact0different/outside;684pixels |

These controls isolate GPU-skinned versus CPU-baked geometry coverage, rather
than cutout alpha or a different camera. They do not justify increasing a pixel
allowance or retuning the camera.

## Stronger source-display reference

The proposed test still derives CPU-baked vertices/bounds independently, but
renders original asset geometry for the silhouette under **a separate frozen
Skeleton3D**. All40reference snapshots have exactly matching local pose, global
bone pose and skeleton world transform, zero delta, separate instance IDs and no
modifiers. Mesh/Skin/texture data are shared immutable native inputs. Reference
mesh instances, skeleton/pose state, transforms, morph weights and ShaderMaterials
are independently constructed from the original model, never selection copies.

Both frozen-reference replays pass all67original assertions in the same five-model
order. The zero-outside-one-pixel and positive reference requirements, camera,
window, frame order and CPU numeric geometry code remain unchanged.

| Deliberate mask/reference corruption | Existing bound rejects it |
| --- | ---: |
| Mask moved0.03world units |757outside pixels |
| Mask Hair mesh omitted |87outside pixels |
| Mask uses stale frame1pose at frame6 (6bones differ) |320outside pixels |
| Mask alpha incorrectly multiplied by0.1 |5990outside pixels |
| Old960x540/native-camera reference |Explicit unequal-dimension rejection |
| Restore all owned control changes |Exact0different/outside |

Incorrect selection transforms, bindings/pose, missing geometry and alpha cannot
propagate into this reference because those mutable mask objects are not its
inputs. This is a selection-versus-displayed-source oracle, not a replacement for
native import fidelity, source-resource preservation or artist acceptance.

## Evidence and next action

Five private desktop receipts are clean: child desktop confirmed, no foreground
child, job and desktop closed; expected exits1/1/0/0/0. Every run preserves all932
functional source files and measured native/prepared/raw/package inputs by hash,
size and nanosecond modification time. No original asset or shared source changed.

The original67/1failures and CPU-baked diagnostic remain retained. The final
output-only proposal is `1794540814364056600/proposed-core-oracle.gd`, with its
small review patch and source hashes. Root must review/port that test change and
run its normal wrapper before claiming a core pass. Product renderer/picker code
and thresholds need no change based on this evidence.

The GPU lease has been returned to root. No further graphical work is pending.
