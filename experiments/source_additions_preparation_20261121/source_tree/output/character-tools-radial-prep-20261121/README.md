# Character tools radial candidate

Status: authored source only, UNPARSED and UNRUN. No current1084-source application, owner review, personal preferences or project has been changed. This is a usable code candidate for Root's isolated qualification, not a UI/adoption pass.

The owner's request is easier access to facial controls, body posing, hair/clothes setup and character parameters. This candidate adds a visible Character tools entry to the existing World rail/list and the configurable logicalC shortcut. Existing camera/WASD/Ctrl navigation, drawing shortcuts, Alt bone reveal and middle-click tool cycling remain unchanged. Ctrl+C is not assigned to this action.

## Existing tools, clear availability

The menu has icons and readable labels for Face/expressions, Pose/move, Hair/clothes setup, Model parameters, object Show/Hide, available Appearance and Materials. Face remains findable even when unavailable, with a direct explanation to select the head or full model instead of silently hiding the entry. The existing Shapes/expressions button likewise remains visible for an actual selected model and is disabled with that reason when no controls are retained. A separate selected environment does not acquire character controls.

Every enabled action calls its existing editor or object-visibility method. Body and parameter routing preserve the inspection camera when changing to Pose mode. Hair setup keeps its existing idle/validation requirement; simply opening the dial never stops or enables motion. An optional runtime appearance editor must expose its existing eligible(actor) predicate and accept that asset before its action is offered. Retained import-time choices are not treated as runtime appearance support.

Object Show/Hide uses the existing per-object current-frame visibility API, including its ordinary Undo/save semantics. This is separate from bodygroup selection, per-material surface visibility and physics activation. Materials is explicitly disabled with a reason: generic surface hiding needs its own persisted, forward-compatible capability and actual per-instance preview/render/picking/bounds/Undo/cold qualification. The dial does not approximate material hiding by changing textures, opacity or native material resources.

The popup supports arrow/Tab/Home/End navigation, Enter, Escape and outside-click cancellation. Disabled entries can still be inspected with keyboard navigation to read their reason. Compact windows use a scrollable list rather than clipped radial positions. Button invocation uses its containing floating dock window; keyboard invocation can bind an actual visible native dock window by the input event's owned-window ID. No global window enumeration is used. Popup theme and scale follow the current app/window. Native and embedded DPI/layout/floating behavior still require actual Root verification.

Opening or cancelling only reads selected-actor capability hints and manages owned UI. It does not sample/apply a pose, call physics On/Off, finish a gesture, stop playback, create keys, write history or change project data. Busy camera/drawing/pose/record/save/import contexts block opening. The menu closes on actor or scene-revision change and revalidates the target again after closing before invoking an action. All existing editor action guards remain in place.

The controller is created before build_ui/World.setup. It does not dereference the later Pose setup at creation. This explicitly avoids the eager World→uninitialized-Pose hookup previously identified in the separate Import info proposal. Popup/rail/button ownership is local; foreign tooltip windows remain ignored using the existing no-focus/mouse-passthrough rule. The normal per-frame path checks only simple flags and actor identity, without a new full scene-tree scan or model/metadata hashing loop.

## Preference migration

Current source and all five inspected preserved reviews (Nov13,52f63c9,f0dd57a,replay2,973039e) have15 logical actions. The previous14-action assumption is not used to guess a missing field. Version1's complete verified15-action dictionary migrates to version2's16 actions. Every existing key/remap/unassigned value is preserved. IfC is already assigned, only the new Character tools action starts unassigned; no previous action is silently unbound. Unknown/incomplete/duplicate/ill-typed layouts are refused with the existing defaults/explanation policy and are not overwritten during load.

Loading migration is in memory only. The existing atomic personal-preference save retains unrelated sections and writes version2 on an explicit shortcut edit. Project/model formats remain unchanged. The new action is available in the existing Keyboard shortcuts panel and uses its normal key capture, collision checks, Clear and restore-defaults controls.

## Source and authored controls

- character_tools.gd: owned popup/controller and calls to existing tools.
- character_tool_policy.gd: selected actual Model hints; disabled reasons; no simulation or resource qualification.
- shortcut_bindings.gd / shortcut_editor.gd: one added action plus strict known-schema migration and the existing personal save path.
- PATCHES.json: five unique source anchors for app construction/router, World entry and face-button availability; explicit source replacements/new files. The actual camera, middle-click, face/hair/pose action bodies remain untouched.
- character_tools_unit.gd:49 generated owned-widget/synthetic-model controls, all UNRUN. These cover remap preservation/collisions/rejections, exactC/modified-key behavior, capability hints, open/cancel immutable state, disabled actions, keyboard selection, stale selection/revision, busy contexts, optional editor eligibility, existing method routing, camera restoration and owned floating window/scale. They do not load native artist assets or qualify actual surface hiding, source motion, renderer fidelity or final GUI behavior.
- Existing shortcut_bindings_unit.gd changes only its deliberate default-count expectation15→16; its loops also exercise the new action. Existing shortcut_editor_smoke.gd changes only the invalid fixture's version to the new current version, ensuring it still reaches the duplicate-key guard instead of merely failing legacy collection size. All other old keyboard GUI/cold/drawing/camera/source assertions are preserved; original files remain exact under bases.

## Root qualification

Apply only to a fresh disposable snapshot after every base hash/unique anchor and absent new path is checked. No installer has been run. Compose other candidates explicitly; do not waive changed-source hashes, and keep all prior sources/results recoverable.

Parse the new modules, run the existing shortcut unit and new49-control unit in an approved isolated UI context, then run the existing shortcut GUI/cold verifier. Test actual pointer and keyboard input in Neon and Classic, normal and small windows, several interface scales and floating World docks. Inspect clipping, disabled reasons, click-away/focus handling, cancellation and personal remap persistence from an actual old15-action profile, including aC conflict. Confirm merely opening/cancelling retains exact authored pose/keys/history/project state and any running hair/body state.

Use actual Mima/Sakuya facial assets and a hair-only selection to confirm discoverability and correct editor targeting. Keep the separate face-value-range problem intact for its own fix; this menu does not reinterpret12 as12percent or silently rewrite existing facial keys. Exercise existing object visibility through its actual Undo/Redo, movie, packed/linked cold paths, and verify that a second actor is unaffected. Generic material hiding, coordinated body motion and moving-frame HairON inertia remain separate owner requests, not claims of this launcher candidate. Perform regression checks appropriate to any eventual adoption.
