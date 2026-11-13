# Small next SFM render/adoption probe

This plan comes from the actual twelve successful derived GLBs/reports and a
bounded read-only native MDL49 metadata inspection. No graphics, Blender app,
adoption or code change ran during this review. Full exact mappings/hashes are in
`experiments/source_appearance/actual_windows_20261113/metadata/next_probe_compact.json`; raw native rest/name provenance remains
private under `native-column-probe/run-1794547085150690200`.

## Actual material correspondence

Nitori's native visible glove has two meshes of 3,272 vertices each. Native
mesh 0 uses skin-reference column 0; mesh 1 uses column 1. The original native
material-table indices are **0/1 → 2/3 → 4/5** across skins 0/1/2. The native
CDMaterials paths resolve each expected VMT uniquely within the staged package.
The actual GLB material names, VMT report and embedded images match those choices.

| Native column | Skin 0 | Skin 1 | Skin 2 |
| --- | --- | --- | --- |
| 0, base | Gloves, table 0 | Glovesg, table 2 | Glovesw, table 4 |
| 1, glow overlay | Gloves glow, table 1 | Gloves glowg, table 3 | Gloves gloww, table 5 |

The three actual 1024×1024 base PNG hashes are
`31d7d4e9fdfc3e377b836fdc33362c4a0e076af0ccf3807941cb1b786b56f0e0`,
`12adf37b798a1a1bd578be6cd0c0ccc9ffed60ef56e2bc46b0af8a11db63450d`,
and `3aebcbfee0fccf84b574ac499be502bf3ac1d4a199cc11186f1617651c1b828e`.
The three GLB hashes, VMT hashes and original VTF hashes are recorded in the
authoritative JSON rather than inferred from names.

There is a concrete visual-fidelity limit to observe before expecting a clean
three-color screenshot. The base and glow primitives have exactly equal decoded
POSITION/NORMAL/UV/JOINTS/WEIGHTS values and triangle indices: each has 3,339 used
GLB vertex records and 16,608 indices. Geometry fingerprints cannot distinguish
their material roles. A preliminary fingerprint-keyed column proposal collided;
it is discarded and retained for provenance. Actual native mesh columns provide
the corrected correspondence.

All glow variants use the same 4×4 embedded PNG,
`4c5961510a1be436170e2b35ff2fdfa621e227058b3106f166e0f07032304a20`.
Despite the source filename `black.vtf`, CRC-checked PNG decoding found opaque
grey values **0, 40 and 120**, not a uniformly black image. Native glow VMTs request
`$additive 1` and environment/Phong/warp effects. Actual GLB materials contain
ordinary PBR base textures, metallic 0 and roughness about 0.8; alpha mode,
emissive and blend extensions are absent. Missing native `hairbump.vtf` also
remains explicit. Coincident ordinary surfaces may therefore hide or alter the
base appearance; that is a later observed outcome, not a pixel pass promised
by these metadata checks. Do not substitute a texture or silently remove the
overlay to pass the test.

## Actual shape and pose data

Keiki's actual seven visible selections are:

| Bits (tools/box/flame; 0 present) | Actual GLB nodes | Actual Tools target |
| --- | --- | --- |
| 000 | tools.dmx, box.smd, flame.smd | Present; 1,180 nonzero used deltas |
| 001 | tools.dmx, box.smd | Present; 1,180 nonzero used deltas |
| 010 | tools.dmx, flame.smd | Present; 1,180 nonzero used deltas |
| 011 | tools.dmx | Present; 1,180 nonzero used deltas |
| 100 | box.smd, flame.smd | Absent |
| 101 | box.smd | Absent |
| 110 | flame.smd | Absent |

Native tools uses column 0 (`props`), box column 1, and the flame group columns
2/3 (`blush`/`excl mark`). Native vertex counts are tools 1,180, box 38 and flame
1,471+8. These come from original MDL mesh records, not bodygroup labels.

The derived Tools target's maximum delta length is **0.0842537007 local units**;
its Y deltas span approximately −0.0842367411..0.0185384154. Its rest local
bounds and target-1 local bounds differ, so a fixed shot must fit their union.
Nitori's actual `Ah` target is present on both primitives with 2,751 nonzero used
deltas each, maximum about **0.000619919 local units**. That is a small actual
derived deformation, not evidence that a glove has a facial-expression meaning.
Do not use it as the first large visible-change oracle.

Useful pose candidates join native index/name/parent with actual used GLB skin
influences. Counts are used GLB vertex records, deduplicated by accessor triplet
and index; they are not independent native vertex counts.

| Candidate | Actual influence evidence | Use |
| --- | --- | --- |
| Nitori native 8 `bip_hand_L`, parent 6 | 538 direct records; 2,214 in its weighted subtree; 4,464 unaffected records | Local hand pose with a large unchanged control region |
| Nitori native 19 `ValveBiped.Bip01_L_Finger2`, parent 18 | 176 direct; 360 subtree; 6,318 unaffected | Smaller follow-up finger/binding test |
| Keiki native 23 `box`, parent 2 | All 38 box records have weight 1; tools/flame have no influence from this bone | Clear independent component pose; preferred first Keiki pose |
| Keiki native 8/17 `bip_hand_L/R` | No direct tool weights; actual descendant tool records 620/560 | Optional later inherited-chain check |

Do not select Keiki's `Flame` bone merely by its label: native index 30 directly
influences only 8 of 1,578 used flame-group GLB records. Thirteen Keiki native
names contain non-ASCII bytes. Keep native indices, exact pinned reader names
and raw-name hashes; do not translate/repair identifiers. Native LOD0 flags are
ancestor-inclusive and were not used as direct-weight eligibility proof.

## A bounded first run, still unrun

1. Render the three Nitori skins as supplied, under one fixed camera/light and
   native output size. Confirm the actual material/image selection and record
   the coincident-overlay result. A separately labelled base-only diagnostic is
   permissible for diagnosis, but cannot replace full-as-supplied acceptance.
2. Use Keiki 000 for Tools values 0, 0.5 and 1, with one fixed camera fitted to
   the union of the independent decoded posed bounds. Compare actual derived
   source deformation and visible pixels; box/flame must remain unchanged by
   Tools. Then pose native box bone 23 with a modest local rotation and verify
   only its weighted component changes against an independent frozen-source
   skeleton/reference. Add a Nitori hand-8 pose with its large unaffected region.
   This is at most eight initial scene captures, not a seven-combination movie
   or a whole native-physics harness.
3. Adopt one selected Nitori bundle and one Keiki bundle through the existing
   ordinary application path. Preserve original scale/root orientation and
   component bounds; do not size isolated gloves/chisels as whole people.
   Verify what native selection/catalogue provenance the path actually retains;
   direct GLB import must not be assumed to retain an external preparation
   report. Check one import Undo/Redo, a pose/shape edit, packed HAS and a fresh
   source-offline reopen, including exact embedded GLB hash and saved keys.
   Report any lost metadata or unsupported path rather than injecting fields
   and calling it normal adoption.

Keep the same private test discipline and original preservation. No new owner
participation prompt is needed. Movie/linked-HAS/broader cold-path checks can
follow after this small route works; they are not claimed here.

Independent original VTX face/UV/material assignment, VVD weights, native
vertex-animation deltas, VTF pixels/gamma/alpha and Source shader output still
need comparisons. A frozen derived-GLB reference tests HAS rendering/adoption;
it does not by itself establish native SFM fidelity. The broader supplied
82-MDL corpus, runtime variants, jiggle and component assembly remain separate.
