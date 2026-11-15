# Imported local pose contract

Godot 4.6 `Skeleton3D.set_bone_pose_rotation` stores an absolute local quaternion. It does not implicitly multiply the imported pose or rest quaternion. The glTF importer assigns the imported node transform to pose position/rotation/scale separately from the rest transform. Therefore the baseline for this probe is `get_bone_pose_rotation()` immediately before editing, not an assumed identity quaternion and not an unproved equality to `get_bone_rest()`.

Primary source:

- [Skeleton3D setters/getters](https://raw.githubusercontent.com/godotengine/godot/4.6-stable/scene/3d/skeleton_3d.cpp), lines 785–850: absolute pose components and reset-to-rest are distinct operations.
- [glTF SkinTool import](https://raw.githubusercontent.com/godotengine/godot/4.6-stable/modules/gltf/skin_tool.cpp), lines 585–590: imported pose channels and `GODOT_rest_transform` are assigned separately.
- [Basis quaternion/scale construction](https://raw.githubusercontent.com/godotengine/godot/4.6-stable/core/math/basis.cpp), lines 822–824: rotation multiplies the diagonal scale, giving `R*S`.

The product's `src/model.gd` apply loop already uses its captured base quaternion multiplied by the authored delta, while retaining base scale. No product fix is required by this audit.

The archived raw probe incorrectly replaced the imported quaternion with the delta. Its independent reference also post-multiplied the whole local matrix, yielding `T*R*S*delta`. That happens to coincide with the intended result for identity or uniform scale, but it is wrong for general nonuniform scale. V2 uses `T*R_import*R_delta*S_original`. It refuses posed matrix nodes and zero/reflected scales until a matching decomposition is independently proved. Other unposed matrix nodes remain supported.

The synthetic positive/negative fixture has root translation `(2,3,4)`, joint translation `(1,0,0)`, imported Z rotation 90 degrees, and X delta 90 degrees. Point `(1,0,0)` must become `(3,4,4)`; delta replacement instead gives `(4,3,4)`. With scale `(2,3,4)`, points `(1,0,0)` and `(0,1,0)` must become `(3,5,4)` and `(3,3,7)`; the old post-matrix delta produces Z=8 for the second point. These are hand-computed controls, not fitted transforms or engine proof.

Native index, palette index and source-node ID remain distinct: the existing exact names and parent joins select Nitori native `bip_hand_L` index 8 and Keiki native `box` index 23. The raw helper uses the bound source-node map to the actual skeleton identifier. CPU morph-before-skin follows the derived glTF transform formula; exact engine import/bake correspondence still requires the future graphical run.
