# Independent native leaf source and driver review — November 15, 2026

Initial source packet b0b87a57… received GO only for a root-controlled first parse. The audit joined source200 to the passed full, checked native8 FrontHair1 stiffness100/parent7/no descendants, and reviewed 152 affected, 144 shared and 9,509 unaffected vertices. Complete authored samples, positions, the other68 bones and exact frame24/frame12 restoration remain mandatory.

The reviewed driver SHA is 8d6bbfd55d4b1f8fddc063f65e2724908f0a6a3baf26bedc7cccce264a59f65a. It preregistered 7,289 checks, 1,440 steps and12 cases, checked full1008/source200/data3/staged aliases, and retained process timeout/reap evidence. The JSON separately records a later observed hash; earlier GO does not automatically cover subsequent revisions.

Actual attempts1/2 parsed but failed at the context guard: two checks, one failure, zero dynamics. Attempt2 measured parent7, rest-only false, final-pose count0 and one direct internal PhysicalBoneSimulator3D, active true, simulation false and no physical bodies. Its broad modifier-presence guard failed. No skin or Off-style runtime pass follows.

Pinned primary Godot source is revision89cea143987d564363e15d207438530651d943ac; exact hashes/line ranges are in the JSON:

- [Skeleton setup274–284](https://github.com/godotengine/godot/blob/89cea143987d564363e15d207438530651d943ac/scene/3d/skeleton_3d.cpp#L274) creates the internal compatibility simulator. [Header73](https://github.com/godotengine/godot/blob/89cea143987d564363e15d207438530651d943ac/scene/3d/skeleton_3d.h#L73) defaults animation on, explaining why active alone is insufficient.
- [Node bindings3768–3770](https://github.com/godotengine/godot/blob/89cea143987d564363e15d207438530651d943ac/scene/main/node.cpp#L3768) expose include_internal on child queries. [Header555](https://github.com/godotengine/godot/blob/89cea143987d564363e15d207438530651d943ac/scene/main/node.h#L555) has C++ is_internal, but it is not script-bound. Compare get_children(true) and get_children(false) instead.
- [Simulator367–378](https://github.com/godotengine/godot/blob/89cea143987d564363e15d207438530651d943ac/scene/3d/physics/physical_bone_simulator_3d.cpp#L367) skips slots without a physical body. Line387 binds is_simulating_physics. Bone count describes skeleton slots, not body count.

A proposed successor may accept only the measured native, scriptless, direct/internal simulator profile: no simulation or physical-body descendants, and no other modifiers. Preserve parent/rest/final-pose and every source/skin/reset guard. Do not disable/remove nodes or claim to observe the private compatibility flag. Keep both failures and create separately pinned successors.

This records source review and separate failure metadata only. No engine, Godot parser, process query, Git action or lease grant occurred; no private arrays were copied. Root owns later changes, execution and current documentation.
