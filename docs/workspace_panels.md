# Workspace controls — owner feedback, 2026-11-02

## Owner-approved normal installation — 2026-11-02 at 1946 EST

The owner explicitly approved applying the tested workspace review copy with a
backup. Normal `C:/a/Programming/cloudflare/prototypes/studio-3d-2d` now contains
that update: Model8 motion feeling, multiple sound clips, deform catalogue/study/
comparison/presets, optional character height/static map sizing, and the four UI
changes. Older Model7 scenes remain readable. The frozen web preview is unchanged.

Exact approved source archive SHA256:
`4f55fa0ae06955bad3a8cf6ccad258186892ee433f5c981b51019720c805425a`. Every replaced source was backed up at
`C:\a\Programming\cloudflare\prototypes\studio-3d-2d\output\source-backups\2026-11-02-190733-before-approved-workspace`; new source paths are recorded as previously absent.
No source files were deleted. Projects, original assets, caches and the existing
append-only progress memo were preserved; no open owner window was controlled.

Fresh normal-path verification completed19 groups/21 command invocations with exit0 and
42 accepted private graphical receipts. It covers workspace/UI/layers,
beginner course, comparison, installed Source browser, native contact viewport,
multiple audio, tutorials/recovery history, motion feeling, HAS, native/common
imports, height, map sizing, MMD groups and expression presets. Functional source
hashes remained exact throughout; original assertions and own MP4/AAC checks pass.
Evidence: `C:\a\Programming\cloudflare\prototypes\studio-3d-2d\output\approved-workspace-checks\1793664473316133500` and `output/normal-source-state.json`.
Initial height/preset wrappers lacked their local catalogue references and covered
only their authored cases (height also ran one real raw VRM import). Those initial
reports are retained. A native followup staged verified data-only reference JSON,
ran the catalogue on six native preparations, then reran height on all six and
expression presets on both VRMs. No app code, original input or assertion changed.
Documentation was updated after checks; executable source remains byte-identical
to the approved archive. Earlier full116/audio and10+5 review checks retain their
own scopes; these19 groups are not a new complete full-verifier run.

Restart Studio to load updated files if an older session is still open. Physical
input/tablet feel, artist quality, all native fidelity, clean-PC and power-loss
acceptance remain open. The full MD/addendum goal and remaining product scope are
unfinished; this is a verified local update, not a public release or deployment.


This development increment addresses the owner's four UI requests without changing
scene/model data or the renderer's final output.

- **Middle-click** the viewport with a model selected in Scene/Pose to alternate
  Move and Rotate. The selected model/bone stays selected; no key, camera change
  or Undo command is created. From Scene it shows the posing controls while keeping
  the current view. A drag beyond4 UI pixels retains the previous middle-button
  navigation: Scene dolly, Pose canvas pan. Draw keeps its own pan behavior. Losing
  focus/Escape cancels a pending click rather than switching tools later.
- **Editing panels stay non-blocking.** Layers, Project options, Installed content,
  content-location settings, tutorial/recovery browsing and deformation comparison
  allow clicking the main window while open. Existing
  ordinary tool windows also no longer suppress all main-window shortcuts simply
  because they are visible. True confirmations/file pickers and temporary popup
  menus still protect their decisions. Layers follows changes made in the main
  layer chooser, so its fields do not silently address the wrong layer.
- **Resize and move workspace panels.** Drag the separators to resize World,
  Properties, Timeline and the central view. Drag a panel title over another dock
  to swap their positions. The title's menu offers Dock left/right/below, Float
  panel, and Reset workspace. A floating panel has a normal movable/resizable
  frame; closing it docks it back. These are the same live controls, not cloned
  editors. The central drawing/3D canvas remains in the main window.
- **Readable selection text.** Pale selected text fields now use dark text.
  Multiline fields use the same palette, and child windows inherit Studio's theme.
  White navigation captions remain on the blue header, where they are intentional.

## Preferences and scope

Dock assignments and splitter offsets are a local interface preference in
`output/workspace-layout.json`; they are not baked into HAS scenes and do not
alter Simple/Advanced project state. Invalid or excessive preference data is
ignored. Tests use isolated preference paths. Reset workspace restores the default
World-left/Properties-right/Timeline-below layout. Floating window geometry is
currently session-only; its last dock location is retained. Arbitrary tab groups,
nested custom docks and multi-monitor placement restoration are future work.

`workspace_layout.gd` reparents the original hierarchy, inspector and timeline
controls. Renderer/world nodes, drawing images and channel data are untouched.
The timeline's scroll container/ruler relationships remain intact. Floating tool
windows are non-exclusive; true choice dialogs remain exclusive. Source notes:
[Window exclusivity](https://docs.godotengine.org/en/4.6/classes/class_window.html#class-window-property-exclusive)
and [AcceptDialog defaults](https://docs.godotengine.org/en/4.6/classes/class_acceptdialog.html).

## Verification

`python tests/verify_workspace_controls.py` tests actual private Windows UI:
middle-click cycles, preserved drag/navigation/drawing, routed main-window clicks
with panels open, selection colors/theme inheritance, real viewport heading drag,
split resizing, docking/floating/closing/reset/reload and exact unchanged scene
output. It also checks1200×760 logical and physical bounds. The original failing
small-window assertion mixed viewport coordinates with physical pixels; screenshots
showed the layout fit, and the corrected test checks both coordinate systems.
No renderer/pose/pixel tolerance was relaxed. An early helper name collided with
Godot's global wrap function; it was renamed before GPU acceptance.

The affected regression additionally checks UI, layer editing, first-movie lesson,
deform comparison, installed browser, native contact viewport and multiple audio.
Actual run status and saved checkpoint are recorded in the dated progress memo.
The earlier116-command/131-GPU full acceptance belongs to the preceding audio
baseline; it is not a fresh full-suite result for these UI changes.

Physical mouse/tablet feel, every panel arrangement and multiple monitors remain
hands-on acceptance. Automated graphics stay on private desktops. No owner window
is moved or focused during verification; no normal installation/web deployment is
implied by a development checkpoint.

## Resumed verification — 2026-11-02

The fresh ten-group run in
`output/workspace-regression/1793659039910878200` completed with every command
returning0. All21 private graphical receipts confirm placement on their own
desktops, no foreground child observed, and closed jobs/desktops. Functional
source hashes stayed unchanged throughout the run.

The groups cover workspace35, original Simple/Advanced UI, layers, first-movie
course, deformation comparison, installed Source content browser, native contact
viewport plus cold reader, multiple audio, tutorials and recovery history. Real
HAS save/reopen and MP4 checks retain their existing assertions. These are
affected checks on the final UI source; they do not claim a new full116-command
regression. The earlier shutdown run remains explicitly interrupted.

The fresh-folder review in `output/workspace-candidate/1793659495624949500`
also passed five commands/six private graphical runs: workspace35, included
beginner49+8, native Model7 world20, assisted Model8 scene19 and multiple-sound
cold reader6. The native copies move before their first launch. Packed scenes
extract into new local caches with verified asset hashes; editable paint, exact
authored poses, Undo, Save and ordinary MP4 export remain usable.

Both native reference images rebuild with0 changed channels in this run. Their
movies retain AAC onset1.0000417s; the multi-clip movie starts at0.2500417s and
retains independently measured voice, effect and stereo music levels. These are
analytical audio checks, not subjective listening. Source hashes remain exact.
This fresh-folder result does not certify a clean Windows PC or artist comfort.

The saved runnable location is in `output/workspace-review-checkpoint.json`.
Normal installed Model7 Studio and the frozen web preview remain separate.

## Responsive dock bounds

The World body now scrolls when its hierarchy/actions exceed the available dock.
The same live controls remain in place, including independent asset packaging.
View and physics controls stay on horizontally scrollable rows instead of forcing
minimum window width or additional tall rows. Focused controls scroll into view.
Compact sizing observes physical window changes even when Godot keeps a fixed
logical viewport. The extra scene caption is hidden in compact mode; scene data
and final output remain unchanged.

The original1200x760 accessibility check exposed an overflow and remains intact.
The final suite also checks same-aspect1120x720,125percent at1400x900, both footer
bounds, reachable World actions and identical final pixels.156timeline/workspace/
channel checks pass, plus65Local/World recording and74asset-package regressions.
These include real movies, audio, Undo and source-offline packed replay where
applicable. Native/physical-device/Windows acceptance remains separate. See
[the evidence receipt](benchmarks/responsive_workspace_2026-11-07.json).


## Scene and Timeline height

Drag the horizontal divider immediately above the Timeline title downward to enlarge the scene, or upward for more tracks. The Timeline body scrolls when compressed; its controls remain live and retain their full available width. A new/reset workspace starts with a234logical-pixel Timeline. The title menu's Reset workspace also restores sensible Properties width. Normal project launches save the layout between sessions.

The owner screenshot exposed the previous367pixel Timeline minimum. Real mouse-drag regressions now cover the native Avatar at3440x1440 and two smaller sizes, plus125percent interface scale. Exact pose/camera/Undo state and render pixels remain unchanged. See [verification](benchmarks/scene_workspace_resize_2026-11-10.json).
