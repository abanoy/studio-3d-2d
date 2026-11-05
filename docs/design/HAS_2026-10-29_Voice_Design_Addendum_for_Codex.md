# HAS (Hybrid Animation Studio) — Voice Design Interview Addendum

**Date:** October 29, 2026  
**Audience:** Existing HAS coding worker / Codex  
**Document role:** Additive design and implementation requirements, **not** a replacement for the project's existing documentation or source code.  
**Project:** Windows-first Hybrid Animation Studio (HAS), a unified 3D/2D animation environment.  
**Evidence:** Detailed user–assistant voice design interview on October 29, 2026, supplemented by the same conversation's preceding clarification of native-model importing and distribution.

> **WORKER: READ THIS FIRST.** The user's request is to **build on top of the project already under development**. Before planning changes, read the current repository, `AGENTS.md`, `LLM.md`, design notes, existing `.has` serialization, UI, timeline, importers, Godot-related code if applicable, and current tests. This addendum describes intended behavior; it does **not** certify that any feature already exists. Do not silently rewrite working subsystems, decide unresolved design conflicts for the user, or convert suggestions into commitments. Keep a short *existing state / missing pieces / design conflicts / proposed next step* assessment and seek approval for true conflicts. **No external-format exporting is in scope now.**

---

## 0. What this addendum is for

The discussion explored the actual everyday user experience of HAS, not just the list of accepted file extensions. The governing objective is a tool that can animate objects from unrelated 3D communities **immediately** and with **minimal hassle**, while retaining sophisticated capabilities behind unobtrusive Advanced controls.

**The user's repeated principle is simplicity.** They may describe sophisticated technical behavior during design conversations, but the exposed workflow must remain directly understandable through visual interaction, icons, sensible defaults, and immediate feedback. If a feature requires a long technical explanation before a beginner can use it, simplify its default path or expose the complexity under **Advanced**.

The desired example is a GMod environment, a VRoid character, and an MMD item appearing and animating together in the same HAS world, without the animator having to manually convert files, repair rigs in a separate tool, or learn the original ecosystems.

### Requirement/decision labels used here

- **[DECIDED]**: User clearly preferred or agreed to this behavior in the interview.
- **[PREFERENCE / TEST]**: User expressed a preference but explicitly left room to test how it feels, especially assistive motion.
- **[SUGGESTED]**: Reasonable engineering proposal or assistant suggestion; do not pretend the user explicitly approved every implementation detail.
- **[OPEN]**: Needs a design choice or project-code assessment.
- **[CONFLICT CHECK]**: Must compare to existing docs or implementation, and return to the user if meaningfully contradictory.

**Precedence:** Existing working code and existing design documents are *context*, not inherently higher or lower priority. The user explicitly said **conflicts are theirs to resolve**. Surface conflicts rather than picking a winner without permission. A new user decision that clearly addresses a previously open question may be documented as such, but destructive changes still require confirmation.

---

## 1. Non-negotiable product philosophy

### 1.1 Simple, instantly usable animation [DECIDED]

A first-time user should be able to do this without opening Advanced:

1. Start a new scene.
2. Drag a supported local model, prop, or map into the 3D viewport.
3. Click a model, manipulate it with intuitive gizmos, click accessible bones, and pose it.
4. Move the playhead, change a pose, and get keyframes automatically.
5. Enable or disable visible physics controls, including playful ragdoll interaction.
6. Arrange basic camera shots and edit animation blocks on a bottom timeline.
7. Save the project, reopen exactly where they left off, and render at least an MP4.

All operations should be understandable through visuals and familiar direct-manipulation patterns. Icons should have short explanatory hover labels or accessible descriptions, rather than relying on unlabeled mystery symbols. This last accessibility implementation detail is **[SUGGESTED]**, consistent with the user's icons-first request.

### 1.2 Advanced is additional depth, not a separate workflow [DECIDED]

Keep a subtle **Advanced** control that progressively reveals detailed parameters: per-bone IK constraints, sophisticated interpolation/curves, physics tuning, shaders/lighting, importer diagnostics, advanced keyframe tracks, etc. Simple and Advanced operate on the same data and project; toggling must never reset the scene or change animation results by itself. Do not make an ordinary task require several mode changes merely to select an object or move a bone.

Advanced functionality may remain comprehensive, but the default should never resemble an overwhelming general-purpose DCC interface. The user specifically dislikes the intimidation of Blender's UI even while acknowledging its power.

### 1.3 No source-ecosystem knowledge required [DECIDED]

Once imported, a model or map should behave as a native HAS asset. Users should not need to know whether a rig originated in MMD, VRoid, FBX, Source, or elsewhere just to move, pose, animate, or render it. Handle unavoidable compatibility issues with understandable, actionable messages, not unexplained failures.

---

## 2. First launch, home screen, and default scene

### 2.1 Home screen [DECIDED]

A clear home screen roughly comparable in purpose to Blender's splash/start screen:

- **New** project/scene.
- **Tutorials** entry.
- **Recent projects** with a title and small visual thumbnail when available.

Clicking Tutorials opens a course browser; see §12. Starting a course from the beginning progresses from simple topics into advanced topics, but experienced users can jump to a particular section.

### 2.2 Empty 3D scene [DECIDED]

- Visually **black empty space**.
- A **horizontal white outlined grid** on a floor/reference plane in 3D space.
- Grid lines visibly **fade into the distance**, as if toward infinity; this is visual fading, not an infinite geometry allocation.
- Camera initially navigates freely; nothing starts selected.
- The synchronized editing timeline runs **horizontally along the bottom**.
- A vertical **scene tree/hierarchy** organizes models, maps, props, root groups, and other objects.

**[SUGGESTED]** Treat the fading grid as an editor overlay, not a light-emitting surface or automatically rendered object. Keep the black background distinct from the Unshaded/Lit mode behavior.

### 2.3 Viewport navigation [DECIDED]

Default to **GMod-style free-fly camera navigation** (WASD and mouse behavior as appropriate to controls and focus). Blender-style orbit/pan navigation is an optional alternate scheme in **Advanced Settings**, not a choice forced on first-time users or a persistent front-page switch. Do not hardcode mouse capture behavior without escape/focus handling; preserve the app's existing scheme if it serves this intent and flag differences.

---

## 3. Importing models and maps into one world

### 3.1 Drag and drop and import-at-playhead [DECIDED]

Two complementary ways to add content:

1. **Drag a file from Windows Explorer into the viewport**. Import it into the scene and position its timeline presence at **frame 0** by default, even when the user happens to be viewing another frame.
2. **Right-click a specific timeline frame** and choose to import from the file picker at that frame. For example, importing at frame 100 means that the object is **not shown at frames 0–99** unless the user later moves or extends its timeline presence.

The user also appreciates visual thumbnails in asset browsers. **[SUGGESTED]** Generate/cache them lazily to avoid long import waits and manage caches transparently; thumbnail rendering must not block the main import/use path.

**[OPEN]** Exact behavior when a dropped asset contains multiple entities/scenes and when a drag occurs during playback. Use existing app conventions where possible.

### 3.2 Spawn where the animator is looking [DECIDED]

When a character is imported, place it **in the current camera view**, not at a distant world origin requiring the user to hunt for it. Try to settle it against the floor or nearby supporting surface so it does not start floating.

If placement collides with another object, try approximately **5–10 nearby candidate positions** to avoid overlap. If there is no satisfactory nearby free location, **place it visibly anyway**, even if collision/overlap remains, instead of silently refusing import or losing the model.

**[SUGGESTED]** This placement heuristic should be stable and bounded, with clear fallback behavior for models without trustworthy bounding boxes or for maps whose geometry is large. Do not silently relocate huge maps based on the same heuristic as a humanoid model.

### 3.3 One giant editable world, multiple maps [DECIDED]

The animator may import **multiple entire maps into the same effectively large black world**, rather than only one active map at a time or forcing scene-to-scene replacement. Each imported map has a parent/root in the scene tree with a transform; selecting the root lets the user **translate the entire map as one group** along X/Y/Z. This handles multiple maps initially occupying or overlapping the world origin.

The scene tree is also a practical way to find distant objects or maps rather than flying around searching for them. Avoid introducing invisible world partitioning that makes a loaded map disappear without an explicit user action.

**[SUGGESTED]** Implement bounds-aware framing/focus shortcuts and spatial organization for large environments; use efficient streaming/culling where necessary without violating the conceptual one-world model.

### 3.4 Format coverage and the 'Hotel California' architecture [DECIDED]

HAS is a **unified destination** for models and environments from major active sharing communities. Priority families include:

- **Source/GMod/SFM**: compiled model ecosystems (`.mdl` and sidecar files), suitable Source model/source data (`.smd`, `.dmx` where relevant), Steam Workshop addon packages (`.gma` as a container where lawful/feasible), and **Source BSP maps (`.bsp`)** with material, prop, texture, and other dependencies.
- **MikuMikuDance**: `.pmx`, legacy `.pmd`, and associated motion/pose data where separately supported (`.vmd`, `.vpd`).
- **VRoid / VTubers**: `.vrm`, preserving humanoid structure, expressions, and material semantics as reasonably possible.
- **General exchange**: `.fbx`, `.glb`, `.gltf`, `.obj` (+ materials/textures); possible native source importers such as `.blend`, and more advanced scene formats such as USD if feasible and justified.
- Other communities can be ranked by active distribution and implementation feasibility, not by extension count alone.

This is a **roadmap of import coverage**, not a promise that all formats already work or that all can be implemented at once. Direct support for a proprietary project format may require an installed compatible application or a permitted conversion library; prefer safe, maintainable paths rather than pretending every binary can be parsed equally well.

All imported assets must be **standardized into HAS's own native binary representation**. The user reports native model data are **currently baked within `.has` scenes**. Confirm the existing storage schema before changing it. Native HAS models and maps should eventually be shareable independently, while also being embeddable in a scene. **Do not invent or impose a separate model/map file extension without checking existing decisions.**

**No third-party/export-back pipeline is a current requirement.** PMX-to-FBX, native-to-MDL, etc., are not product priorities. They are not categorically forbidden in the future. "Hotel California" is the user's joke for **easy import, standardized inside, output mainly a completed animation**.

### 3.5 Importer fidelity and dependencies [DECIDED as goal; mechanics SUGGESTED]

Imported assets should preserve as much practical function as possible: geometry, UVs, textures, materials, bones, rig behavior, IK/constraints, morphs/facial expressions, animation tracks, collision/physics, object hierarchies, and provenance. For a BSP map, importing mesh geometry alone is insufficient if surfaces lose materials, embedded/lightmapped lighting, props, or dependencies.

Use format adapters into one canonical internal representation. Track unsupported capabilities and report them explicitly rather than claiming perfect conversion. Cache converted assets to avoid reparsing each time. Do not execute imported scripts/macros or unsafe code merely to view an asset. Respect distribution licenses and authors' usage restrictions: being technically importable does not confer redistribution rights.

---

## 4. Selection, bones, manipulation, and the scene tree

### 4.1 Default interactions [DECIDED]

- On scene open, the user can freely navigate the camera with **nothing selected**.
- **Left-click a model or item** to select it; its selection displays a **green outline**.
- While selected, users may click individual **visible bones/body regions** to pose them directly.
- Pressing/holding **Alt** should make the model's full bone structure visible for easy selection, including bones otherwise hard to find visually.
- **Right-click empty/appropriate scene area to deselect** the selected model as the default simple behavior.
- Manipulation gizmos for moving, rotating, and scaling should remain straightforward and immediately accessible.

**[OPEN]** Whether Alt is *hold-to-reveal* or *press-to-toggle* was explicitly left undecided. Test ease of use and keyboard conflicts; do not claim either is user-approved. Distinguish right-click deselect from right-click *on an entity* opening a contextual menu, a behavior also requested for actions such as Reset to T-Pose. A consistent priority/focus rule is needed.

### 4.2 Invisible objects remain editable [DECIDED]

Selection outline should work **regardless of an object's rendered visibility**. If an individual object or any parent group has been hidden, selecting the object from the scene tree may still show a **ghostlike green silhouette/outline** in the editor for pose/edit operations. This editor-only silhouette must **not** change visibility keys and should not appear in final renders merely because an object is selected. The green outline is shown whenever selected, not through a separate persistent-outlines toggle.

---

## 5. Keyframes and sparse, understandable animation

### 5.1 Auto-keyframe manual edits [DECIDED]

Manual posing and transforming should be frictionless:

- Pose a character at an initial frame; the program automatically records appropriate keyframe parameters.
- Move the playhead to frame 4 (for example); move that bone or object; those changed parameters are keyed at frame 4.
- Do not require the user to click a hidden Key button after every transform.
- Pose/transform changes follow the selected model, selected bone, and current frame.

Important distinction: **automatic keyframing for direct edits is not the same as continuously recording a live physics simulation**. Physics recording requires explicit Record; see §9.

**[SUGGESTED]** Provide unambiguous feedback when the edit creates a keyframe, support undo, and ensure editing without a selected animatable object cannot accidentally alter unrelated tracks.

### 5.2 Motion interpolation [DECIDED / PREFERENCE TEST]

The user wants to animate with **few but meaningful key poses**. **Smooth transitions/easing** are the normal default between keyed poses. In Advanced, allow more precise choices including linear, cubic, quadratic, exponential, stepped/hold, and custom curve controls as supported by the animation runtime.

**[PREFERENCE / TEST]** The user liked the possibility of subtle **overshoot, bounce, and natural settling** even without full physics, and would be willing to try having it enabled by default. This is not a mandate to generate exaggerated motion on every curve or to alter exact intended poses. Make it an obvious, reversible assist that can be turned off and fine-tuned under Advanced. The exact default intensity is **not decided**.

**[SUGGESTED]** Preserve the exact user-authored key poses, apply assistive motion through non-destructive interpolation/procedural layers, and support stepped camera cuts and visibility changes rather than applying smoothing to every parameter indiscriminately.

### 5.3 Direct IK posing [DECIDED]

**Inverse kinematics should work by default where the imported rig supports it**. Dragging a hand should pull its elbow/arm chain naturally instead of forcing separate joint rotations. A crouch or root movement should be able to keep the feet planted when appropriate. Missing rigs or unusual bones need graceful fallback, not a crash or an assumption that every imported skeleton is humanoid.

### 5.4 Motion Assist [DECIDED goal; behavior PREFERENCE / TEST]

Motion help should reduce beginner busywork and help amateurs add finer details. Potential assistance includes foot planting, subtle secondary body motion, short overshoot/settle, walking assistance, and guessed movement paths. The user wants the computer to make a reasonable guess and let them correct it, rather than requiring complex setup.

Guardrails:

- It must remain **user-directed**, **easy to disable**, and **editable manually**.
- Expose a useful simple toggle; reserve precision parameters for Advanced.
- Do not modify a deliberately keyed pose without clear control or make an opaque prediction impossible to undo.
- If the system cannot confidently infer something, do the safe simple behavior and let the animator correct it.
- Avoid making online generative AI a prerequisite for normal animations; deterministic procedural/rig methods are valid first implementations. **[SUGGESTED]**

### 5.5 Reusable walks and motion paths [DECIDED concept, OPEN details]

The user likes **reusable motion-path or animation clips** on the timeline that can be assigned to a character, instead of animating each walking cycle manually. The worker proposed a draw-a-path workflow, and the user accepted trying it. A motion path could be drawn in the viewport, assigned to a character, and backed by auto-generated/suggested locomotion with feet adapting appropriately.

The user also speculated that a 2D drawing from one camera angle may leave 3D depth ambiguous: the software could ask for a side, top, or bottom view (especially if a ceiling obscures the top) and infer a path from multiple projections. **Preferred simple behavior:** guess from the first input; only ask for a second viewpoint if needed; visibly preview the guess and let the user revise it. **[OPEN]** Algorithms, depth inference rules, UI details, and accuracy targets are not decided.

---

## 6. One camera, one world, instant cuts

### 6.1 Camera workflow [DECIDED]

The user's prior GMod/Stop Motion Helper approach often used **one universal camera**. To cut from a wide shot to a close-up or another set, position the camera at one frame, then **teleport it to another camera location on the next frame**. For example, frame N shows location A; frame N+1 shows location B. The shot change must be **instant**, not an unwanted travel animation between those adjacent frames.

Keep normal camera interpolation available for intentional dolly/pan motion, but include **stepped/discontinuous camera transforms** for cuts. Multiple independent maps can be loaded in the giant world, and this same camera can jump between their locations. Do **not** force the user to manage one map per scene or use a multicamera editing workflow to obtain a simple cut. Optional multicamera features may exist later if compatible with the primary simplicity goal.

**[SUGGESTED]** Expose an easy "Cut" action or ensure abrupt adjacent-frame keyframes have explicit stepped interpolation; don't rely on interpolation that can cause a fast, visible streak between sets.

---

## 7. Timeline as visually editable Kdenlive-style blocks

### 7.1 Unified bottom timeline [DECIDED]

Use one **synchronized timeline** for 3D animation, character movement, maps/visibility, camera, 2D animation/overlays, VFX, sound effects, music/audio, and the rendered sequence. The reference is **Kdenlive**: horizontally arranged tracks, clips as blocks, easy select/drag/cut/paste/split.

Nested sequences are **desirable but lower priority**. The user explicitly said at least one synchronized timeline is mandatory; nested sequences could come later or be more advanced.

### 7.2 Object tracks and expansion [DECIDED]

A newly loaded character or model normally appears as **one collapsed model track**. The user can expand the track (in Simple or Advanced according to final UI design) to reveal subtracks for the **individual parts/parameters that have actually been animated**, rather than overwhelming them with hundreds of inactive bones. More complete per-bone/channel inspection belongs in Advanced.

**[SUGGESTED]** Group bone channels hierarchically and provide jump/focus selection so selecting a bone in the viewport highlights its corresponding subtrack.

### 7.3 Clip operations are structural, not destructive [DECIDED]

- An object/animation appears as a draggable **block/clip**.
- Cut/paste or dragging a clip shifts its place in time, carrying its relative animation/keyframes with it.
- Splitting a clip produces independently movable pieces that preserve their internal animation and relative keyframe timing.
- Moving a clip from frame 3000 back to frame 0 is a direct timeline operation, not manual rekeying.
- Copy/paste, splitting, dragging, and other edits should be undoable, consistent, and visually obvious.

**[OPEN]** Exact clipping, trimming, keyframe ownership at boundaries, duplicate instance behavior, ripple edits, and cross-track moves need to be reconciled with the existing timeline. Do not assume a clip is literally a pre-rendered video; for characters, it must remain an animatable asset with meaningful parametric tracks.

### 7.4 Gaps between animation blocks [DECIDED intent, OPEN detailed algorithm]

The user distinguished **no prior object existence** from a **gap between two pieces of animation for an existing object**:

- If the first imported clip starts at frame 100 and no earlier presence exists, show **nothing** before frame 100.
- If an object already exists from an earlier block and there are two animation blocks separated by a gap, HAS may **try to infer/interpolate a plausible connecting motion** from the surrounding values. It should not automatically erase the existing object just because its animation clip is absent during that gap.
- The interpolation must respect visibility keys and any deliberate holds. If the user manually turned visibility off and never turned it on, no automatic animation-gap inference should turn it back on.

**[SUGGESTED]** Separate **object presence/lifetime**, **visibility**, and **animation evaluation** in the internal model, even if the simple UI presents them intuitively together. This allows unambiguous frame-100 imports, visibility overrides, persistent poses, clips, and interpolation. Gracefully fall back to a held pose when no reliable connecting values exist. The specific blending rule is **[OPEN]**.

---

## 8. Visibility and fades

### 8.1 Visibility is a persistent parameter [DECIDED]

Visibility is a **keyable state parameter**, independent from motion clips. Once set to `false` at frame 10, it stays false at frame 100 (or later) **until some explicit later keyframe changes it to true**. Do not assume starting a new animation clip switches visibility back on.

If visibility is enabled at a prior frame and animation blocks have a gap, the object may remain visible; do not auto-hide solely due to the clip gap. If it has never been introduced before frame 100, it is absent before that frame. Selected hidden objects still display an editor-only green ghost silhouette (§4.2).

### 8.2 Default visibility transition [DECIDED]

- Default visibility on/off **fade duration: 300 milliseconds**.
- **0 ms means an instantaneous pop/cut**.
- The user wants this configured from **Options/project settings**, rather than a separate VFX clip pasted on the timeline.
- Treat this as a **project-wide default** and store it with the project; do not add a visible fade block for every object toggle.

**[OPEN]** How this global fade interacts with individual object overrides was not firmly decided. The user explicitly clarified that the setting is global, not a per-object VFX timeline item. Preserve that default; don't invent a complex per-keyframe UI without a reason. Decide how hard cuts behave when a project defaults to 300 ms while a user wants an instantaneous camera/visibility cut—an explicit zero setting should be possible.

---

## 9. Physics, ragdolls, and recording

### 9.1 Physics in Simple [DECIDED]

The **Physics** toggle must be **visible in Simple mode**, not hidden behind Advanced. The user wants a playful GMod-like experience: drop a ragdoll into the scene, grab it, toss it with velocity, slam it into boxes, or manipulate joints. This matters even for "stupid little animations" made quickly.

The user favored ragdolls importing with **physics ON by default**, so they collapse/fall under gravity, with an immediate toggle to stop it. Treat that as the desired default subject to practical compatibility and testing; imported assets with no suitable physics rig cannot be forced to behave as a valid ragdoll.

Turning physics **OFF** should **freeze the model in its current simulated pose**, not snap it back to T-pose. An accessible **Reset to T-Pose** action is desirable from an object context menu. Manual posing/gizmos must remain usable when physics is off. Consider safe transitions back to simulation and what happens to velocities; details **[OPEN]**.

### 9.2 Simulation is not continuously recorded [DECIDED]

**Do not automatically bake all live simulation into animation keyframes.** The user explicitly requires pressing a **Record** button to capture a ragdoll tumbling or objects reacting to physics. The Record control belongs in **Simple mode**.

This is separate from automatic *manual pose* keyframing (§5.1).

### 9.3 World Record vs Local Record [DECIDED]

- **World Record**: captures relevant movement/physics of the whole active world while recording. If a ragdoll knocks over a pile of boxes, those boxes' flight/fall should also be recorded.
- **Local Record**: records motion for the **selected object/model only**, even when it collides with other objects. Nonselected interacting bodies are not automatically added to the saved local recording.
- A potential **third collision-following capture mode** was mentioned as a future option, **not a confirmed near-term requirement**.

The mode choice should be easy to discover near the visible Simple Record button. Prefer compact controls over an intimidating panel.

### 9.4 Recording storage [SUGGESTED]

World capture may produce very many samples/keyframes. Consider compact sample tracks, delta encoding, or post-recording keyframe thinning with error tolerances that preserve collisions and visible impacts. A recorded take must replay consistently across scrubbing and final rendering; do not depend on uncontrolled fresh simulation for a supposedly baked recording. Exact capture rate, determinism guarantees, and the keyframe reduction algorithm are **[OPEN]** engineering decisions.

---

## 10. Lighting, viewport presentation, and render quality

### 10.1 No-lighting/Unshaded as the normal modeling and posing view [DECIDED]

By default, the scene should be easy to understand without having to light it. The user wants a **No Lighting / Unshaded** mode in which models show their base colors/textures without scene illumination, useful for posing and animating without the distraction of shadows. This is distinct from a physically lit scene.

A **Lit** mode uses actual scene lighting. In an enclosed map with no lights, a room can be dark. If an imported GMod/Source map contains valid baked lighting/lightmaps, the importer should **attempt to retain it**, with a control to toggle relevant map lighting or lighting contribution.

**[SUGGESTED]** Provide a small, visually understandable Unshaded/Lit toggle; complex sliders belong under Advanced. Ensure a loaded map remains navigable when the Lit view is dark (e.g., users can temporarily return to Unshaded).

### 10.2 Godot and photorealistic possibilities [PREFERENCE / OPEN]

The user mentioned using **Godot's rendering and lighting** if that is the current rendering technology. They would welcome higher-quality shaders, ray tracing, or a photorealistic final output **if technically achievable**, but this is an aspiration, **not** a mandate to promise real-time path tracing or rewrite the renderer. Verify the actual existing rendering backend and capabilities.

Primary rule: **fast, responsive basic animation first**. Any expensive optional render pipeline must not make the simple viewport unusable.

---

## 11. `.has` project packaging, native assets, and project settings

### 11.1 Self-contained saved scenes by default [DECIDED]

The normal `Ctrl+S` / File > Save behavior should produce a **single self-contained `.has` scene/project file**. The user describes it conceptually as a native binary ZIP-style package; do not assume an actual ZIP implementation is required until examining existing `.has` serialization.

**By default, bake/embed everything needed to reopen the project**, including:

- Native-converted character and prop models, maps, geometry, textures, materials and other dependencies.
- Rigs, poses, animation/keyframes, camera tracks, light data, physics or recorded tracks, scene hierarchy, settings.
- Audio, sound effects/music where permitted, VFX resources, 2D drawing/overlay assets and layers, compositing/timeline information.

The intended benefit: copy/share/reopen **one `.has` file** and continue where you left off without discovering a missing texture, model, audio clip, or map dependency.

### 11.2 Optional linked assets [DECIDED]

In the Save workflow, the user can **uncheck a baked/self-contained option** and store file references to external assets instead. The program may warn about nonportable assets and, on reopening, offer a straightforward **Locate Missing File** workflow if external references are absent. This should not be the default. Dependency resolution should be transparent and reliable rather than relying on absolute Windows paths where unnecessary.

### 11.3 Independently share native models/maps/scenes [DECIDED]

The user wants the native binary representation to support **distribution of individual model assets**, **individual map assets**, or **complete scene/project packages**, without converting back to PMX/MDL/VRM. Whether those are separate native extensions or variations of the same container is **[OPEN]** and should follow the existing design, not a new assumption. Existing `.has` currently contains native model data baked inside scenes.

### 11.4 Project vs personal settings [TENTATIVE]

Each project can store its own animation, timeline, lighting, render, and visibility-fade settings, so reopening reproduces the project accurately. The user tentatively agreed that **project content settings** load with the project while **personal interface preferences** (layout/theme/input preference) remain global. They were uncertain about asking on load whether to use a project's settings, so **do not introduce a disruptive dialog by default** without later approval. Flag any conflicts with existing preferences code.

### 11.5 Save safety [SUGGESTED]

Use versioned, validated serialization, atomic saves, checksums where appropriate, and an import provenance/dependency manifest. Avoid silently overwriting the only good copy if packaging fails. For embedded media, ensure archive size/resource limits and test portability on another Windows machine or clean environment.

---

## 12. Visual, interactive, learn-by-doing tutorials

### 12.1 Course browser and supplied practice assets [DECIDED]

The home-screen **Tutorials** button opens a course catalog containing at least:

- A **Basic** course that starts with opening a scene, importing a dummy model/map, camera navigation, selection, bones, auto-keyframes, physics, timeline editing, saving, and rendering.
- An **Advanced** course with optional focused sections such as detailed lighting, interpolation, rigging, constraints, physics, rendering, etc.

Courses should contain sections and subsections so users can jump to a topic, while a full start-to-finish path moves logically from simple to advanced.

Use **real included tutorial `.has` scenes** with **dummy models and a dummy map**; the learner can actually manipulate the project, not merely watch a video or read a page. Sample scenes should be safe, small, and ideally work offline. Provide clear visual instruction/hints, not wall-of-text documentation.

### 12.2 Interactive teacher behavior [DECIDED]

Tutorials should approximately **observe whether a requested action has been performed correctly**. For example, "Raise this character's arm" can be validated within a rough tolerance. This need not be perfect evaluation, but it must check that the student followed the intended exercise rather than blindly moving on.

- Once the step is completed, show short success feedback and **automatically advance** to the next instruction.
- If the learner seems stuck with no meaningful progress for roughly **10–30 seconds**, assume they may need help and **quietly offer a hint**.
- Hints can progress from highlighting the correct bone/button to a short visual demonstration if needed.
- Do not interrupt merely because the learner is reading, contemplating, or experimenting; offer rather than take over. **[SUGGESTED detail]**

The tutorial is meant to be an encouraging guide, not a punitive grader. Approximate state-based verification is enough for initial lessons.

### 12.3 Previous/forward history and checkpoints [DECIDED]

The learner can go **Previous** to an earlier lesson step, and the **entire exercise scene restores** to that step's checkpoint: model positions, poses, camera, playhead/timeline, and other relevant exercise state. This requires **microstate/checkpoint snapshots for each lesson step**, not a record of every individual mouse movement. The user explicitly wants Previous to **change the whole scene**, not just display the previous text while leaving the exercise in a later state.

**[OPEN]** Whether tutorials need a Skip button was asked but not conclusively answered. Don't silently enforce or prohibit skipping; review later.

### 12.4 Resuming and keeping the practice scene [DECIDED]

When reopening a partially completed tutorial, support both **Continue** (restore progress) and **Start Fresh** (restart the lesson), without unnecessarily destroying the earlier saved progress. After completion, the learner may **keep/save the practice scene as a normal project**, but this is optional. The tutorial's purpose is to teach; it should not force saving a disposable exercise.

Lesson checkpoints are conceptually separate from project crash-recovery snapshots (§13), even if they share an internal snapshot mechanism.

---

## 13. Silent autosave, checkpoints, and crash recovery

### 13.1 Automatic background protection [DECIDED]

Autosave must be **enabled by default** and operate **quietly in the background**. Users can select scheduling either by:

- elapsed **minutes**, or
- a configurable **number of meaningful user actions**.

Do not open disruptive progress dialogs for routine autosaving. If the project has an associated directory, keep its backup/recovery data in that project context (or an appropriate managed backup directory). Any backup naming should clearly indicate it is a backup, not a second competing final project.

### 13.2 Journal/checkpoints rather than endless copies [DECIDED objective; SUGGESTED implementation]

The user prefers something like a **single recovery file/journal** containing recoverable key states or snapshots, rather than an ever-growing stack of duplicate full project copies. The implementation can use checkpoint+delta storage or another robust structure with the same user-facing result. The user compared optional history browsing to Git commits, but **does not require Git internals**.

A recovery entry should contain:

- **timestamp** of when the snapshot was taken;
- a **small, low-resolution thumbnail** representing what the viewport showed;
- enough data to restore the project state from that checkpoint.

History browsing should live in **Advanced**, not clutter the default workflow.

### 13.3 Crash recovery [DECIDED]

After a crash, the program should **attempt to restore the newest valid checkpoint by default**. If it is corrupt or incomplete, **fall back to the next earlier valid checkpoint**. Keep an accessible Recovery History so the user can choose older states. **Do not overwrite the last explicitly saved `.has` project merely because crash recovery runs.** A restored state can remain unsaved until the user explicitly saves it.

**[SUGGESTED]** Use validated journaling with version headers/checksums, atomic checkpoint commits, size/retention controls, and thumbnail generation that does not block animation. Ensure recovery files are bounded and tested with abrupt termination, disk-full scenarios, and deliberately corrupted latest entries.

---

## 14. Audio, VFX, 2D-over-3D, and final output

### 14.1 One workspace for finished scenes [DECIDED as broader project goal]

The user wants a **3D camera and environment** with **2D drawing and visual-effect layers on top** without destroying or editing the underlying 3D geometry, and a Kdenlive-like synchronization/editing experience. Audio, sound effects, music, VFX, 2D layers, character animation, and camera changes share the timeline. Chroma/green-screen style compositing is part of the broader HAS concept. Keep this integrated with existing features; this addendum does not demand rebuilding them.

### 14.2 Simple export settings [DECIDED]

The effortless default is:

| Parameter | Default |
|---|---|
| Output | **MP4** |
| Resolution | **1920 × 1080** |
| Frame rate | **24 fps** |
| Location | **Next to the saved `.has` project** |

Users can change defaults in export/project settings. Also support **image sequence export** (such as PNG frames) as an alternative. The user expects at minimum an MP4 with reasonable defaults, without configuring a complicated encoder panel for an everyday render. **[SUGGESTED]** If a project has not yet been saved, ask once for an output destination rather than inventing a nonexistent folder.

The resulting render must honor visibility, fades, lighting/render mode, cameras, animation, physics recordings, audio, and 2D/VFX compositing as applicable.

---

## 15. Interactions and technical invariants to preserve

The following separates related notions so that software implementation does not accidentally contradict the user's description:

| Concept | Expected meaning |
|---|---|
| Import into scene | Convert source content to native HAS representation, create object(s), make manipulable. |
| Object's initial timeline presence | If first introduced at frame N > 0, absent before N unless user explicitly moves or extends its presence. |
| Visibility keyframe | Persistent on/off state until next explicit change; independent of animation clips. |
| Fade | Project-level default 300 ms for visibility transitions; 0 ms is instantaneous. |
| Selected but invisible | Editor-only green ghost outline/silhouette remains accessible, including under hidden parent. |
| Auto-keyframe | Record direct authored poses/transforms at the current frame. |
| Live physics | Can simulate interactively without creating playback keyframes. |
| World Record | Capture all relevant simulated objects, including impacted boxes. |
| Local Record | Capture only selected object(s) as specified by the local-record mode. |
| Animation clip drag | Retimes clip and its keyframes together, rather than leaving motion behind. |
| Gap between two animation clips | Existing object may persist; optional interpolation/bridge if adequately defined. |
| Camera cut | Intentional discontinuous placement at adjacent frames, never accidental camera flight. |
| Embedded `.has` | Portable scene package containing all needed assets, unless user explicitly chooses external links. |
| Recovery checkpoint | Hidden journal/history state separate from the explicitly saved `.has` file. |

**Suggested priority for implementation of state evaluation:** (1) object presence/lifetime, (2) parent and local visibility values, (3) visibility fade, (4) evaluation of keyed/recorded animation or hold/bridge, (5) editor-only selection overlays. This is an **engineering suggestion**, not a requested exact architecture. Review the existing engine's evaluation order before changing it.

---

## 16. Suggested engineering roadmap (do not treat as orders to rewrite existing work)

1. **Audit before coding.** Read repo rules, `AGENTS.md`, `LLM.md`, `.has` file implementation, existing editor UI and timeline, render pipeline, and current importer list. Report what is already present and working. Note potential conflicts and ask rather than overwrite.
2. **Establish the first-five-minutes vertical slice.** New black scene/fading white grid, free-fly viewport, bottom timeline, tree, simple drag/drop import, visible selection outline, manipulation gizmo, auto-keying, save/reopen, default MP4 output.
3. **Unify native asset handling.** Make embedded `.has` assets reliable, maintain external-link opt-out, dependency checks, and independent native distribution as the current architecture supports. Avoid premature file-format replacement.
4. **Add high-value importers incrementally.** First use the formats already supported by the runtime. Add high-demand community ecosystems (Source/GMod maps and models, MMD, VRM) with verified sample assets, dependency handling, and honest compatibility reporting.
5. **Make the timeline behave like editing blocks.** Collapsed character tracks, expand animated channels, split/drag/cut/paste with animation retained, explicit visibility and presence semantics, camera hard cuts.
6. **Add approachable physics and capture.** Toggle, freeze pose, T-pose reset, playful drag/throw interactions, explicit Local/World recording, playback determinism and compression.
7. **Add motion assistance safely.** Default IK where appropriate; smooth easing; optional reversible bounce/overshoot; ground contact and reusable walking/path clips. Test quality with beginner animators, keep assisted changes editable.
8. **Build interactive tutorials.** Dummy `.has` files, Basic/Advanced courses, visual task checking, 10–30-second idle hints, checkpointed Previous, resume/start fresh.
9. **Harden reliability.** Quiet journal autosave, latest-valid recovery with fallback, advanced history thumbnail viewer, packaged asset portability and failure handling.
10. **Expand rendering and polish.** Project-level unshaded/lit behavior, BSP lightmaps where possible, audio/VFX/2D overlay integration, 1080p24 export; optional higher-end rendering after the core workflow is stable.

This order is **[SUGGESTED]**. Adjust to actual code progress and dependencies, but do not demote the user's simplicity principle to cosmetic polish.

---

## 17. Acceptance scenarios: test behavior, not buzzwords

### A. Five-minute novice animation

1. Launch HAS; see New, Tutorials, and Recent with thumbnails if present.
2. New scene: black background, white fading floor grid, timeline below.
3. Drag a local supported humanoid model; it spawns visibly near camera and grounded.
4. Click it: green outline; select an accessible bone or reveal rig via Alt; use gizmo.
5. Pose at frame 0; move to frame 4 and pose again; keys are created without manually pressing Record.
6. Preview a smooth transition; optionally disable assist to control it yourself.
7. Save a baked `.has`, close and reopen, and verify poses/assets persist.
8. Render an MP4 at 1920×1080, 24 fps, next to the project.

### B. The original cross-ecosystem goal

1. Import a Source/GMod map (with the available materials/props/lightmaps), a VRM character, and a PMX prop.
2. Position several maps in one world by selecting their root nodes from the tree.
3. Pose the VRM humanoid and place the PMX prop without manual use of Blender or unrelated converters.
4. Switch Unshaded/Lit view; if the BSP contains compatible lighting data, retain/use it where feasible.
5. Save as one self-contained project; reopen without file-not-found prompts for embedded dependencies.
6. Report any unsupported imported features clearly rather than silently dropping critical bones or materials.

### C. Timeline cuts, presence, gaps, and visibility

1. Import an object at frame 100 via the timeline; at frame 0–99 it is absent.
2. Move its clip to frame 0; its animation keyframes move relative to the clip.
3. Split a walk clip into two and drag pieces apart; preview a predictable motion hold/bridge without automatic disappearance.
4. Set visibility OFF at frame 10; leave it unset thereafter. The object remains invisible at frame 100 despite having a later animation clip.
5. Select the hidden object from tree; see only its editor ghost/green silhouette without changing visibility.
6. A visibility transition defaults to 300 ms; set the project default to 0 for an instantaneous transition.
7. Animate one camera at two map locations across adjacent frames and confirm an instantaneous cut, not a camera journey.

### D. Physics and recordings

1. Load a ragdoll; physics is enabled where supported; it falls and can be thrown into boxes.
2. Disable physics and confirm the ragdoll holds its current pose; context action can reset T-pose.
3. Without Record, live tumbling does not fill the timeline with recorded simulation keys.
4. Record with World: both ragdoll and impacted boxes have reproducible motion on playback.
5. Record with Local: only the selected ragdoll's motion is captured.
6. Timeline remains responsive and does not balloon uncontrollably with an ordinary short take.

### E. Tutorials

1. Start a Basic lesson with a bundled dummy map/model.
2. Follow a prompt to move a bone; the lesson roughly detects success and automatically advances.
3. Remain genuinely stuck; after roughly 10–30 seconds an unobtrusive hint appears, possibly highlighting the bone.
4. Press Previous; the entire scene/pose/camera/timeline returns to the checkpoint for that step.
5. Exit midway and later choose Continue or Start Fresh.
6. Finish and optionally save the practice scene as a normal `.has`.

### F. Crash recovery

1. Configure autosave by time or action count; confirm it runs silently in the background.
2. Make changes, simulate an abrupt crash, restart; recover from newest valid checkpoint.
3. Corrupt latest recovery checkpoint; confirm fallback to an older valid one.
4. Inspect Advanced > Recovery History: entries have timestamps and low-resolution thumbnails.
5. Confirm recovery did not silently overwrite the last manually saved `.has`.

---

## 18. User decisions vs topics that still need approval

### Strongly established decisions

- Simplicity and icon-first, visually understandable direct manipulation are the guiding product priority.
- The default interface is usable for a full animation-to-MP4 pipeline without Advanced.
- Simple mode includes manipulators, camera editing, keyframes, ragdoll physics toggle, and an explicit Record button.
- Black new scene, white horizontal fading grid, bottom timeline, vertical object/map tree.
- GMod-style fly camera as default; alternative orbit navigation in Advanced Settings.
- Drag/drop import from Windows Explorer at frame 0, timeline-context import at chosen frame.
- Import models near the camera, try grounding and bounded collision avoidance, visible fallback on failure.
- Multiple maps in one world; transform map root to reposition whole map.
- Selected object has a green outline; Alt can reveal bones; right-click can deselect; hidden selection can display ghost outline.
- Direct pose changes auto-keyframe; smooth interpolation normally preferred.
- IK posing by default where appropriate; Motion Assist should help but remain user-correctable.
- Character starts with a collapsed track, expanding to animated subtracks.
- Kdenlive-like unified timeline, draggable/splittable blocks, preserved relative keyframe timing.
- Persistent visibility parameters independent of animation clips, 300 ms project-level fade default, 0 for immediate cut.
- Simple physics by default for compatible ragdolls, freeze on disable, optional T-pose reset.
- Manual physics must be explicitly recorded; World and Local recording have different scopes.
- Default save embeds all project assets in one native `.has`; linked references are optional.
- One native representation inside HAS; external-format exporters are not a current interest.
- Interactive Basic/Advanced tutorials with bundled dummy `.has` practice scenes; hints after 10–30 seconds stuck; automatic progression; checkpointed Previous; resume/start fresh.
- Background autosave on by default; time/action schedules; recovery journal/checkpoints, auto-recover newest valid, older fallback; low-res preview thumbnails in Advanced.
- Default MP4 output 1920×1080 at 24fps beside the project, with configurable overrides and image sequence option.

### Specific questions the worker should **not silently answer on the user's behalf**

1. **[OPEN]** Is Alt momentary reveal or toggle reveal? How should shortcuts coexist with viewport navigation?
2. **[OPEN]** Exact right-click click-target logic: deselect versus context menu for T-pose and imports.
3. **[PREFERENCE / TEST]** Default overshoot/bounce intensity, and how aggressive Motion Assist should be on secondary body parts.
4. **[OPEN]** Motion path interpretation and 3D drawing interaction: 1-view guess plus optional side/top/bottom corrections, algorithm, and user-feedback threshold.
5. **[OPEN]** Clip boundary/keyframe semantics, gap interpolation and hold behavior, record sample compression, and handling parent visibility.
6. **[OPEN]** Whether extra per-object/per-key visibility fade overrides should exist; only the global project option is clearly requested.
7. **[OPEN]** Skip functionality in tutorials (Previous is clear; Skip not settled).
8. **[TENTATIVE]** Project settings versus global interface preferences; user was undecided about prompts for importing/loading project settings.
9. **[OPEN]** Native independently shareable model/map packaging and extensions, as existing `.has` stores native model data already.
10. **[OPEN]** Technical approach for Godot/renderer fidelity and high-end ray tracing; do not promise capabilities not established by the current engine.
11. **[CONFLICT CHECK]** Any mismatches with older project documents or features under implementation. **Present them to the user for resolution**, with no surprise destructive migration.

---

## 19. Concrete instructions to the current Codex worker

1. **Do not treat this as an instruction to create a new application.** Continue the existing HAS implementation and retain working user interactions and saved projects.
2. **Inspect and report** current repo structure and project docs before making a change. If running as local Codex, use the actual local worktree, not an assumed GitHub repository.
3. **Create a comparison matrix** of existing behavior against requirements in this addendum, including statuses: present/tested, partially implemented, missing, blocked, or conflicts with prior spec.
4. **Propose minimal incremental patches**, tested in the Windows-targeted workflow, and implement only within the user's existing authorized development scope.
5. **Preserve native format compatibility.** If a format migration becomes necessary, propose versioning and lossless read compatibility; do not silently break existing `.has` files.
6. **Resolve user-facing simplicity first.** Put advanced technical configuration behind progressive controls, not in a wall of default sliders.
7. **Keep imported asset fidelity honest.** Test with representative model/map files and check material/rig/morph/physics/dependency handling. State clearly when a feature cannot be preserved.
8. **Do not build external-format exporters now.** They are nonpriority, not permanently prohibited. Independent distribution of **native HAS assets** is within scope.
9. **Keep a decision/conflict log**. Label user-confirmed choices separately from this document's engineering suggestions, and ask the user to resolve substantive conflicts.
10. **Report progress with observable demos and acceptance tests**, ideally against scenarios in §17. A simple animatable end-to-end slice is more valuable than an impressive but unusable advanced control panel.

## 20. Final product test

The user should be able to open HAS, drop a random supported character and environment into one world, grab a body part, create a few meaningful key poses, throw a ragdoll for fun, arrange a camera cut, add sound or an overlay, save a portable `.has`, and render a short **1080p/24 MP4**—all without understanding Source, PMX, VRM, conversion pipelines, physics solvers, or complex interpolation terminology.

**Complex engineering inside. Simple animation outside.**

---

*Document prepared as a standalone addendum from the voice design conversation; no claim is made that the local Codex worker or repository has already received or implemented it.*
