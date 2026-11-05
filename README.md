# Hybrid Animation Studio — first working slice

The installed Studio update includes [movable workspace panels](docs/workspace_panels.md):
resize separators, drag panel titles to swap docks, or use their menu to float.
Middle-click a selected model to switch Move/Rotate; middle-drag still navigates.
Editing panels allow main-window clicks, and selected text has darker contrast.
The resumed ten-group affected review and five fresh-folder checks pass. The
newest runnable review location is recorded in
`output/workspace-review-checkpoint.json`. The owner-approved update is now installed
in the normal Studio folder; `output/normal-source-state.json` records its verification.

A local Windows/GDScript application for **external 3D environment → animated
camera → independent transparent drawing cels → one frame timeline → MP4**.
Permanent owner-selected home: `C:\a\Programming\cloudflare\prototypes\studio-3d-2d`.
The managed Git worktree retains a development snapshot. This is a separate local
application; it does not deploy the game, portfolio, or older artist assistant.

Development Draw also has [brush opacity and gentle erasing](docs/brush_opacity.md).
Retracing a translucent stroke stays even; separate strokes build up normally.
This newer increment is separate from the normal installed application.

Opt-in [Tablet pressure size](docs/brush_pressure.md) now tapers pen/eraser size
from reported pressure, without a full-size initial click dot. Mouse drawing is
the default. Reproducible event tests pass; physical tablet acceptance remains open.

Development Fill also offers [Close gaps](docs/fill_gaps.md), default0, using
temporary boundaries and mandatory Apply/Cancel previews while preserving ink.

Draw now also has [project color swatches](docs/project_palette.md): Keep this
color, then click it to reuse across cels. Advanced provides names/replacement/
removal. The swatches travel with the project; artwork and3D data stay separate.

[Current Windows review](docs/current_review_2026-11-02.md): the full automated
suite plus native/SFM/common-format/HAS checks passed on frozen development inputs.
The current owner-approved normal installation is verified separately below and in
the current review notes. The frozen web preview remains unchanged.

A separate [Windows review copy](docs/portable_candidate.md) passes fresh-folder
animation/drawing/audio/HAS/movie checks without copied development caches. Its
saved location is in `output/portable-candidate-checkpoint.json`.

Studio [supports several sound clips](docs/multiple_audio.md): Add
audio appends, the chooser selects a sound, and each audio block can move on the
master timeline. Packed saves retain every clip. This is included in the current
normal installation; the earlier review copy predates it.

The development copy also accepts [MP3 and Ogg sounds](docs/compressed_audio.md)
through Add audio. Hidden local conversion feeds the same PCM clips, Undo,
timeline and packed HAS/movie path. This newer increment is separate from the
normal installed update described above.

Development **Shorten sound…** and a draggable right-edge timeline handle keep
original samples and let you restore the end later, with Undo. Edge dragging is
a preview until release; Escape cancels. [Trimmed projects use version3 audio](docs/audio_end_trim.md),
which older Studio builds refuse; untrimmed projects retain their existing layout.

**Size map…** in the World panel measures a known doorway/ceiling span, previews
uniform sizing against a six-foot guide, and applies it with Undo. See
[map sizing](docs/map_calibration.md) for static-map support and limitations.

Fresh MMD imports retain compatible native expression groups in **Shapes /
expressions**, using the same editable deform keys as VRM. Unsupported groups
stay visible with guidance. See [expression poses](docs/expression_presets.md).

Frame model / Frame selected follows the current posed skin and expressions,
including live ragdolls, while preserving explicit shot keys. Large models may be
framed with extra space. See [current-pose framing](docs/pose_framing.md).

Camera keys also retain their visibility distances, so framing a nearby reference
does not clip a distant background out of the movie. Advanced exposes the two
distances; Save camera key remains explicit. [Projection and compatibility](docs/camera_projection.md).

In Pose, **Planted feet…** keeps supported feet in place over a chosen frame range.
Plant or Release from the current frame; adjust a foot directly in the view, or
reveal knee targets in Advanced. Corrections have one-step Undo. Physics and Hair
must be off while editing targets. See [continuous contacts](docs/contact_animation.md)
for compatibility, reach limits and verification status. Automatic walking remains
unfinished.

**Motion feeling…** adds bounded anticipation and settling around main
pose keys. Simple hides generated helpers; Advanced lists their frames. Apply/Undo,
normal packed HAS/cold Open and MP4 have focused native evidence. Model8 is included
in the owner-approved current installation, which also reads older Model7 scenes.
Its earlier frozen source completed the98-process full regression before the newer
catalogue increment below. See [motion animation](docs/motion_animation.md).

Development also has an opt-in [Source particle rendering experiment](docs/source_particles.md):
one installed SFM flash and one Workshop glow convert to common deterministic
sprite data and render into an actual MP4. This is saved separately from the
installed app. The first foundation predates the scene integration described below.

The next [particle scene integration](docs/particle_scenes.md) now passes ordinary
development Save/Open, recovery and Export, including portable HAS and delayed
audio. It introduces an explicit scene version for effects. This newer source
is separate from the normal verified installation.

Development now also has an [installed particle browser and basic controls](docs/particle_browser.md):
choose Particle effects in Installed, load a compatible named system, then add it
and edit placement/size/timing with Undo. Existing effects reopen from World.
All eight affected review groups passed for this UI. The normal installed app
and the earlier full-tested backend snapshot remain separate. Broad Source
effect compatibility, animated attachments and viewport effect gizmos remain open.

Development now also allows
[recognized installed SFM content without GMod](docs/sfm_standalone.md), retaining
the installed-GMod requirement for GMod assets. Native material fidelity is still
incomplete. A [Source texture row correction](docs/source_textures.md) fixes
Scout's misplaced texture regions in new development preparations; existing saved
assets keep their original bytes. Development also adds
[neutral Source eyes](docs/source_eyes.md) from native iris/helper data. Animated
gaze and native eye shading remain incomplete.

Shapes recognizes common Source CamelCase names while leaving
mixed-area controls unassigned. The separate [deform observation backend](docs/deform_observations.md)
measures before/after geometry. Advanced Shapes now offers
[Study deform areas](docs/shape_study.md), with explicit adoption and Undo.
Advanced also offers [Compare without recording](docs/shape_comparison.md):
neutral and selected-deform images from the same view, keeping pending edits intact.
VRM models also offer [embedded expression poses](docs/expression_presets.md):
choose a named expression, set its strength and author its grouped deform keys.
Options offers [character height review on import](docs/height_import.md), off by
default: review a six-foot reference or keep the original size before adding it.
Tentative guesses are never applied automatically; saved manual choices remain authoritative.

## Launch

Draw → **Layers…** adds, renames, reorders and removes drawing layers with Undo.
The top row paints over lower rows; Show this layer and Apply opacity are undoable.
Use a low [layer opacity](docs/layer_opacity.md) for faint rough sketches beneath ink.
Press **I** in Draw to [pick a color](docs/color_picker.md) from the picture without
sampling editor guides; Advanced adds drawing-only and original-cel sources.
See [drawing layers](docs/drawing_layers.md) for the current four-layer limit.

Drop a `.has` file onto `Start Studio.bat` to open that project directly. From a
terminal, use `python run.py "C:\path to\your scene.has"`. With an explicit
project, Studio opens that file and keeps earlier checkpoints available in Recover.

Double-click `Start Studio.bat` for the windowed app. It uses `pythonw.exe` and
the installed windowed Godot executable, with startup diagnostics kept in
`output/launcher.log` / `output/studio-engine.log`. The default engine splash is
disabled; the application has its own title and original gradient scene icon.
A batch window may flash briefly at launch; opening `launch.pyw` directly avoids
that when Windows associates .pyw with Python. For console diagnostics, run:

```powershell
python run.py
```

Uses **Godot 4.6 stable, standard (GDScript), not .NET**. The launcher discovers
the existing `C:\a\tools\Godot\Godot_v4.6-stable_win64_console.exe`. Else download
the [portable standard Windows 4.6 release](https://godotengine.org/download/archive/4.6-stable/),
extract it, and set `$env:HYBRID_GODOT` to its executable's full path.
No Python packages, npm dependencies, cloud APIs, engine editor, or accounts are
required. Python 3.13.1 was used for the launcher/tests; Python 3.10+ is expected
but other versions have not been tested. You can also run the pinned Godot binary
with `--path` pointing to this directory and `--log-file` pointing to a writable file.

MP4 uses your separately installed FFmpeg. The app detects libx264 and AAC and
offers an executable path field/browse button. It defaults to the existing
`C:\Program Files\ffmpeg\bin\ffmpeg.exe`. `HYBRID_FFMPEG` overrides this for tests
and launch. No FFmpeg or Godot binaries are bundled. See `docs/licenses.md`.
The application makes no network calls.

Launch starts in a **black empty world** with a fading white floor grid and no
selection. **New** starts another empty project, asking before discarding edits.
The grid is an editor guide and never enters saved asset geometry or final frames.
Use **Advanced > Sample room** to open the original room/camera example as an
unsaved project. No native project format migration is needed for empty scenes.

Use the left **World** hierarchy or click a model in Scene/Pose to select it, with
a green outline. **Hold Alt** to reveal all bones; release to hide the full skeleton.
Right-click empty space to deselect or an object for its context menu; right-drag
still adjusts POV. Hidden selected models retain an editor-only green ghost.
See [world selection and controls](docs/world_selection.md).
Simple shows standard body-part names; Advanced reveals internal bone names and IDs.
Search accepts either vocabulary. See [the local bone-name dictionary](docs/bone_names.md).
Move a supported hand or foot with **Move limbs naturally** enabled (the default)
to bend its arm/leg. See [natural limb posing and current limits](docs/limb_posing.md).
Enable **Hold feet while posing** to move the body/root while keeping both feet
in place during the edit. Physics must be off. See [scope and playback limits](docs/foot_hold.md).
Simple now also offers **Physics**: simulate a supported ragdoll or solid prop, grab/lift it with
left mouse, release to throw, or switch Physics off to freeze. Use an actual map
floor; the grid is a guide. **Local record / World record → Record** captures a
take as editable animation. Stop keeps it; Escape discards an unfinished take.
Compatible interactive ragdoll imports now start Physics after import dialogs close;
existing live bodies/hair resume after adding another asset. Saved projects reopen
their authored state. See [import defaults](docs/import_physics.md), [recording controls and limits](docs/physics_recording.md)
and [physics controls](docs/physics.md).
Live boxes can collide with ragdolls and other props. Physics off freezes the
prop's position/rotation as ordinary HAS model data; source assets stay untouched.
Ragdolls now use limb-aligned shoulder/hip joints and separate elbow/knee hinges,
with less angular damping. These are shared approximations; native collision and
anatomical fidelity still need refinement on unusual rigs.
Body fitting now separates loose descendant weights from rigid collision proxies,
and overlapping connected proxies receive bounded self-contact exceptions.
Hair/skirt wind and generated helpers are tracked in
[the secondary-motion guide](docs/secondary_motion.md). Simple **Hair & clothes**
uses supported existing VRM chains, independently of body **Physics**. **Add fan**,
move/aim its arrow with the usual handles, and select it to adjust **Blowing speed**.
Use **Local/World Record** to keep the motion as editable animation; live motion
alone adds no keys. OFF freezes the current whole pose, including body physics.
For a skinned model, **Set up loose parts** offers a review of unrigged connected
regions, attachment joints and proposed helper positions. Repeat it to set up more
parts; regions already driven by springs are protected.
Apply creates weighted joints in a new HAS asset revision; Undo restores the
original. **Choose a smaller patch** lets you box-select part of a connected mesh,
then add/remove areas before applying. The cut edge stays attached to the surrounding
surface. See [reviewed helper setup and limits](docs/secondary_motion.md#reviewed-weighted-helper-setup).
The declared-chain experiment also adapts VRM0/1 into one secondary rig,
tests fixed-step motion and bakes ordinary editable takes through packed HAS/MP4.
It runs via `python tests/verify_secondary_motion.py`; normal imports do not start
hair physics automatically. `python tests/verify_fan_motion.py` checks normal fan,
hair/body controls, recording, packed reopen and MP4, plus optional actual VRM samples.

The owner's [voice design addendum and implementation audit](docs/voice_addendum_audit.md)
now govern earlier conflicting product decisions. The audit separates working features
from remaining independent curves, foot planting, physics and tutorials.

Native GMod import requires your own installed Garry's Mod; the game and Workshop
add-ons are never supplied or downloaded by Studio. Default lookup is
`C:\Program Files (x86)\Steam\steamapps\common\GarrysMod`, with browsing in
`C:\Program Files (x86)\Steam\steamapps\workshop\content\4000`. The Source import
dialog lets you choose and save other library locations. GLB/MMD use remains independent.

Use **Installed** in the blue navbar to browse/search installed GMod models and
maps, including Workshop and VPK members. Dependency checkboxes enable extra mounted
content; installed SFM search paths and add-on resources resolve automatically as
fallbacks, with persistent exclusions for conflicts. Locations supports other folders.
See [installed-content browser and missing-texture guide](docs/installed_content.md).

## FBX, OBJ and glTF

**Add scene** and **Add model** now accept binary FBX, OBJ/MTL and glTF2.0 with
local sidecars or embedded data. Local Blender preparation feeds the same GLB/model
contract and `.has` saves. Choose scale and, for OBJ, up axis; an explicit asset
folder can include shared texture/buffer directories. Native actions remain in
the preparation bundle; manually keyed Studio animation remains the timeline source.
See [common-format import guide](docs/common_import.md) for scope and limits.

## HAS project files

New Save/Open use **`.has`**. Packed saves include the standardized scene, model,
drawings, audio and animation; linked saves keep smaller files with checked local
GLB/WAV references and relinking when assets move. Packed is the default. Advanced
Save as changes filename/mode; Open folder keeps older directory projects usable.
See [HAS format and save guide](docs/has_format.md), including native-bundle limits
and future importer adapters.

The [multi-object world format and renderer](docs/world_format.md) have tested combined
maps/actors, independent poses, packed reopen and MP4 output. [Editor controls](docs/world_editor.md)
now select/pose multiple prepared instances with stable-ID Undo and all-object saves.
Normal Add scene/model now appends independent instances. New creates a genuinely empty
schema4 world; normal Open/recovery restores all objects after complete validation.
Old schema1–3 projects remain readable and promote when another object is added.
See [Illusion card investigation](docs/illusion_import.md) for the new Koikatsu/AI/AA2 scope;
card recognition is implemented, direct card/map assembly is still pending.
The [two Misaki PMX exports](docs/koikatsu_comparison.md) expose distinct bundle/material
and skeleton requirements; neither is falsely labelled a successful import.
[VRoid/VRM sample checks](docs/vrm_samples.md) document the shared-runtime feasibility
test; VRM geometry/rig import and facing normalization now work directly; MToon/springs/
expressions and native .vroid parsing remain incomplete.

## Object animation on the timeline

Every map/model/group has a row. Right-click a block to split, copy, cut or delete;
right-click free row space to paste. Drag pieces independently, or Shift-drag all
animation/presence together. Manual keys edit their owning piece. Motion connects
across gaps, stays absent before introduction and holds afterward. Camera, drawings
and audio keep their timing; edits are undoable. See [timeline workflow and limits](docs/timeline_blocks.md)
and [native piece records](docs/animation_clips.md). Visibility fades/channel expansion remain pending.

## Drop files and import timing

Drop one supported3D file over the viewport to add it from frame0. For ambiguous
formats, choose Model/prop or Environment/map. Right-click a timeline frame to add
a model or map from that frame onward. Earlier frames do not show the new object;
Undo/Redo and HAS saves retain its first presence. Playback pauses for import.
Model imports now try nearby ground/support and up to9positions near the import view;
maps keep their original placement. If no free/supporting spot fits, the model remains
in view with an explanatory status. This is approximate placement, not physics.
Multi-file drop queues are not implemented yet.
Automated handler/picker/render tests pass; physical Explorer drag still needs checking.

## Simple and Advanced

Every launch starts in **Simple**. Use **Draw** for layers, pen/eraser, color, brush
size, New drawing and Copy drawing here; use **Scene / camera** for navigation
and Save camera key. Open, Save, Add scene, Add audio, Play and Export movie stay
available. Adding audio reveals its start-frame and mute controls.

Add audio appends another sound. Choose a clip in Audio or click its timeline row;
drag that sound's block to move its start. Remove audio clip affects the selected
sound only. All sounds remain active when switching workspaces.

The **Advanced** toggle at the upper right reveals precise cel exposure/deletion,
camera FOV/interpolation/key deletion, audio trim/gain, Save as, FFmpeg
configuration and diagnostics. All underlying project settings remain active in
Simple. Toggling changes visibility only: no flattening, quality reduction, key
reset, seek, playback restart or removal of hidden settings. This workspace choice
is not written into the project; startup intentionally defaults to Simple.

Original gradient icons, pale beveled controls and a full-width blue gradient header follow
the owner's XP / early Mac OS visual direction. The header contains icon navigation
with large icons above short captions, plus hover/press feedback. Labels and tooltips accompany
icons; no Microsoft/Apple artwork or external icon/font package is bundled.

## Try the tiny film

1. Launch, turn on **Advanced**, choose **Sample room**, then return to Simple.
   This explicitly opens the original procedural room **through the runtime GLB importer**.
2. Scrub the bottom timeline: the shot already has keys at 0 and 48. Export
   duration is end-exclusive `[0,48)`, so there are 48 samples, frames 0–47.
3. To change a shot, choose **Scene / camera**. **Ctrl + left-drag** enters free
   camera: mouse look with WASD flight and Q/E down/up. **Left-drag** moves the camera
   sideways/up, **right-drag** adjusts view direction (POV), **middle-drag** moves
   forward/back (dolly), and **left + right drag** rolls around the viewing axis.
   While dragging, WASD flies and Q/E move down/up; Shift moves faster. Escape or
   releasing all held camera buttons releases the mouse. These gestures change
   only the temporary camera, not drawing pixels or saved keys. Advanced reveals
   FOV and interpolation. Then
   **Save camera key**. Replacing an existing key asks explicitly; Undo works.
   Scene navigation stays temporary until keyed. Switch to Draw to restore the shot.
   **Frame scene** positions the editor camera around an imported asset without
   rewriting shot keys; it helps with unfamiliar model/environment sizes.
4. In **Draw**, select Rough or Ink and paint. B/E choose pen/transparent eraser.
   **Fill [F]** colors connected regions. **Color layer below** adds/selects Flats
   beneath the line art; Sample visible drawings uses only2D boundaries. Large/edge
   fills preview before Apply/Cancel. See [color fill](docs/drawing_fill.md).
   **Onion skin** shows previous/next exposures as blue/pink editing guides. They
   stay out of fill sampling and movies. [Guide details](docs/onion_skin.md).
   Middle-drag pans the 2D canvas in Draw mode; it dollies only in Scene mode.
   Brush radius is measured in the full 1920×1080 output, regardless of window size.
   Wheel zooms; middle drag pans; Fit view restores framing. Space only plays/pauses.
5. Step/scrub to frame 24, then **Copy drawing here** or **New drawing**.
   A drawing holds until its exposure ends. Editing a held cel changes that drawing
   throughout its exposure; duplicate at a later frame to make an independent version.
   Advanced reveals exposure length and cel deletion, including holds and gaps.
   Visibility affects both preview and export. Undo/Redo supports strokes, cels and keys.
6. Press Space to preview; arrows step frames, Home/End seek first/last exported frame.
   Text-entry fields retain their keyboard input. Click the canvas to resume shortcuts.
7. Choose **Add audio** for each voice, music or sound clip. Use PCM **16-bit mono/stereo WAV**,
   8–96 kHz, or desktop **MP3/Ogg**, up to 60 seconds/32 MiB. MP3/Ogg converts
   locally to PCM48kHz mono/stereo using the configured FFmpeg; Cancel preserves your
   sounds. Float/24-bit WAV still needs conversion in your audio program. The inspector scrolls to Audio.
   Set start frame, source trim in milliseconds, and gain, then **Apply audio settings** (Advanced reveals trim and gain). Mute affects preview/export. Audio edits and removal support Undo/Redo.
   Select a sound in Audio or its own timeline row; drag its block to change timing.
   Each clip has a waveform on the same timeline; overlapping sounds mix together.
   Preview follows the audio playback
   clock; if the audio driver is unavailable, the app reports a silent fallback.
8. **Save** a `.has` file. Keep **Pack assets into this file** enabled for a portable
   project, or turn it off for linked GLB/WAV assets. Reopen with **Open**; Ctrl+S
   saves the current file. Advanced > Save as changes its filename/storage mode.
9. **Export movie** creates a new render folder **beside your saved `.has`**.
   Unsaved/recovered projects and legacy directory projects ask for a destination.
   Use **Advanced > Movie encoder > Export to another folder** for a one-off override.
   It contains numbered full-HD PNGs, `movie.mp4`, an encoder log, and (when audio is
   present) a deterministic `mixed_audio.wav`. Cancel keeps
   completed frames. The app reports errors and restores the editor after cancellation.

With sound clips, MP4 contains synchronized H.264/AAC. Without any, it exports silent
video. Playback runs once to the end and stops on the last frame; seek to restart.
Scrubbing is silent and sets the next playback position. Up to16 clips share one
mix; live audio recording, a mixing desk and scrub sound remain unimplemented.
See [multiple audio clips](docs/multiple_audio.md) for limits and older-app compatibility.

## Project timing

The [timeline navigation controls](docs/timeline_navigation.md) provide zoom,
horizontal panning and Fit. Ctrl + wheel zooms around the pointer; Shift + wheel
pans. Track labels stay fixed, and the ruler shares the same visible range.

**Options → Scene length (frames)** extends a parent up to 60 seconds and 7200
frames with Undo (1440 frames at24fps). Child scenes remain bounded to240frames.
It keeps existing timing and refuses shortening that would discard authored
content. Sound tails stop at the scene end while original samples remain intact.
See [longer parent timelines](docs/extended_timing.md) for schema8 compatibility,
exact rational limits and the retained drawing/import/resource budgets.

**Options → Project frame rate** now offers common integer and fractional rates.
It keeps frame numbers fixed, updates synchronized audio, and supports Undo.
New projects remain24fps; see [project timing](docs/project_timing.md) for exact
fractions, older-reader compatibility and current duration/resolution limits.

## Orbit navigation

For orbit-style pose inspection, **Advanced → Settings → Camera controls** offers
**Orbit around selection**. Ctrl+left orbits, Ctrl+right pans, Ctrl+wheel dollies.
The existing fly scheme stays the default; camera keys remain explicit. See
[orbit navigation](docs/orbit_navigation.md).

## Image sequences

For image output, **Advanced → Movie encoder → Export PNG sequence…** exports
the complete scene, or transparent drawing layers when that option is checked.
No FFmpeg is required; sound is included as a synchronized WAV sidecar. See
[PNG export](docs/png_export.md).

## Sound fades

For sound editing, select a clip and use **Fade sound…** for gentle starts/ends.
Both durations are editable in milliseconds and undoable; source samples stay
intact. Faded scenes use version4 audio data; older builds refuse them. See
[sound fades](docs/audio_fades.md).

## Pose a model (shared MMD / GMod path)

Desktop MMD characters also offer **Import MMD pose…** in their pose properties.
Choose a VPD and review its matched bones and shapes before applying editable
keys at the current frame in one Undo step. [Pose import](docs/mmd_pose_import.md) explains skipped controls
and the current native IK limitations.

**Import MMD motion…** accepts a bounded VMD range as a movable standard timeline
block, with body and expression keys in one Undo step. [Motion import](docs/mmd_motion_import.md)
explains timing, source-range review and the remaining native IK limitations.

Fresh PMD/PMX preparations now retain [supported joint chains](docs/standard_ik.md).
VPD/VMD foot targets and IK switches bake into ordinary editable body keys.
With Move limbs naturally enabled, imported joint controllers also pose their
declared links through dragging, numeric edits and reset. Release auto-keys the
changed joints together. Between keys, animation uses the saved FK poses; use
Planted feet for persistent foot locks. Inherited effects remain unsupported;
older models need reimporting to gain declarations.

Use **Add scene** for the environment and **Add model** for a prepared GLB character.
In **Pose model**, select a bone or click its joint, choose Move/Rotate and Local/World,
and drag the colored handles. Completed bone/root edits **automatically create or update
a pose key at the current master frame**. Start with a pose at frame0, then move the
playhead and pose again. One Undo restores the edit and its key; Escape cancels a drag.
Camera keys stay explicit. Advanced reveals **Auto-key pose edits** (turn off to edit
static drafts), snapping, axis locks, local numeric values, root scale and interpolation.
**Record pose key** remains available for adding an unchanged hold pose or explicit drafts.
Reference only hides
the model from movies while keeping it visible while drawing.

This is one shared GLB/model contract, with a native parameter report preserved as
metadata. MMD and Source/GMod decoding are tested. This increment supports
one model beside the environment. Keep the entire native preparation bundle; it is
not fully packaged into the project yet. See [standard model and posing guide](docs/standard_model.md)
for exact draft/key behavior, a local Miku demo path, preservation and limits.

## Recovery copies

Normal launch restores valid recovery first; otherwise it shows **Home** with New
scene, Open project and up to12 recent projects. The top Home button returns there
without discarding your scene. Missing recent files stay listed; Remove changes
only the list. Thumbnails use matching recovery previews when available. Return to
scene or Escape continues editing. **Tutorials** opens **Your first movie**, an
11-task beginner path from an empty world through map/model imports, physics,
camera keys, posing, Ink, playback, timeline split/drag and MP4. Personal saving is
optional. Focused Pose and draw / Camera shots chapters remain available, with
whole-scene Previous, Continue and Start fresh. Requested hints highlight a real
control/joint; collapse the guide for more room. Advanced courses remain partial.
See [tutorials](docs/tutorials.md).
See [Home and recent projects](docs/home.md) for persistence and limits.

Automatic recovery is on by default, checking changed work every **60 seconds**.
It waits until brush/camera gestures, playback, export and dialogs finish. The
footer reports success or failure. This is separate from **Save**; manual saves
stay untouched and the unsaved marker remains until you save the actual project.

After a stopped/interrupted session, startup restores the newest valid checkpoint
as an **unsaved copy**. If its assets, drawing, audio or rig bindings fail validation,
Studio tries the next earlier checkpoint. Your last manual `.has` stays untouched.
If none can open, startup keeps the clean empty world and retains all copies.
Use **Recover** in the top bar at any time. Select latest or previous checkpoint,
then **Restore as unsaved copy**. Save that copy to a new `.has` file.
**Later** leaves everything available; **Dismiss session** hides both generations
without deleting their files. Sessions still owned by a running app are excluded.
New recovery records distinguish writers by process number and Windows creation
time, so reuse of a stopped writer's number does not hide its checkpoint. Older
PID-only records keep conservative protection; uncertain ownership stays untouched.

Advanced > Recovery offers **By time** (0.5–10 minutes) or **After edits**
(1–1000 completed edits, initially25), an enable toggle, Checkpoint now,
**Recovery History**, Open recovery folder, and **Open saved backup**. A long
stroke counts once on release; creating its cel counts separately. Undo/Redo and
real layer visibility changes count; navigation, playback and unchanged edits do
not. Successful recovery or a fully current manual Save resets the count.
See [recovery scheduling](docs/recovery_schedule.md) for failure/retry rules. History
shows timestamped states and small scene/drawing previews. It retains up to12
states per session, including saved/dismissed sessions, and restores an unsaved
copy after confirming replacement of current edits. Simple Recover shows recent
choices only. Open saved backup opens a project's
previous legacy-directory manifest as an unsaved copy. For HAS, use Open on
`<file>.has.backup`; that also restores an unsaved copy.
Recovery settings reset at launch. A manual save of restored work resolves its
pending notice. A corrupt/failed recovery leaves the current project open.
See [startup recovery](docs/startup_recovery.md) for verification and remaining limits.

Copies live in `output/recovery/` beside the studio source. A checksummed history
index references immutable small metadata snapshots and shared geometry/WAV/cel
files. Old journal metadata/previews outside retention are pruned; shared asset
cleanup remains unfinished. The conservative **512 MiB cache budget** still
bounds protection. If the budget is reached,
recovery stops and reports a warning; manual Save still works. After saving and
closing active work, review old session folders before removing them yourself.
No automatic shared-asset cleanup or multi-instance quota locking is implemented.
See [recovery history](docs/recovery_history.md) for retention and preview limits.
Preview resizing, blending and file writing run in one background worker, so
editing and playback can continue after its image snapshot. Checkpoint writers
take turns; Checkpoint now stays queued until safe. See the [preview worker](docs/recovery_preview.md).

Recovery preserves committed cels, camera **keys**, layer visibility, audio and
frame. Temporary unkeyed navigation, undo history and UI preferences are not
checkpointed. Last edits within the interval may be lost. Synchronous copies can
briefly pause a large project. Filesystem flush/rename and interruption tests are
not proof against real power loss, hardware failure or a full physical disk.

## Requirements, decisions, deferred work

**Confirmed:** Windows/offline first; standard external 3D scenes; GMod-style camera;
screen-space human drawing separate from geometry; integer frame authority; cel holds;
default 24 fps; editable projects; MP4. The original complete specification is included
unchanged as `CODEX_CUSTOM_ANIMATION_STUDIO_SPEC.md`.

**Provisional implementation choices:** installed Godot 4.6 stable with Compatibility
renderer; GDScript only; 1080p/48-frame starter; self-contained static GLB import;
RGBA8/sRGB drawings; schema4/5 worlds and schema6 sequences (reads schema1–6); external FFmpeg; 32-cel memory limit;
small flat source modules rather than empty future subsystem folders. The app name,
software license and shipping/installer design remain open decisions.

**Requested compatibility work:** GMod maps/models and MMD environments/characters,
with GMod-style manipulation and parameter preservation. A tested external PMD/PMX
preparation path and a Source MDL/BSP/GMA/legacy-bin conversion path are available. See
[compatibility and workflow evidence](docs/legacy_compatibility.md) for commands,
verified samples, Ragdoll Mover/SMH references and gaps. Add scene accepts BSP/GMA/bin;
Add model accepts MDL/GMA/bin and offers an archive-member chooser. Local Blender /
SourceIO preparation runs asynchronously, with cancellation and missing-content warnings.
See [Source import instructions](docs/source_import.md). PMD/PMX now open directly through Add scene/model, using the installed local converter.
VRM0/1 open directly through Add model. Manual bone/root posing works
through the same source-independent controls. Shape and physics controls are present;
per-format native fidelity still requires scoped fixtures.

**Implemented beyond the initial slice:** multiple audio/MP3/Ogg, tablet-pressure
software support, fill/onion controls, shape controls, planted feet, editable nested
sequences, video alpha/chroma, sequence shadows/masks, smoothing and quality profiles.
**Remaining work/acceptance:** broader native fidelity, reusable locomotion,
long/dense projects, general drawing-layer masks/reference workflows and real
hardware/artist acceptance. AI remains optional. See the
[current requirement matrix](docs/requirements_cloud_2026-11-05.md) for scoped evidence.

The supplied layered/animated Krita projects were inspected as references. See
[KRA findings](docs/kra_reference_findings.md) for actual timing, layer counts and
memory implications. Desktop [Krita import](docs/krita_import.md) now renders
reviewed native layers into one editable drawing layer; native-layer editing stays in Krita.

## Reproduce verification

Automated Windows graphical tests now run on a **private hidden desktop**, so
their windows and screenshots do not interrupt your current desktop. Real GPU
rendering is retained. Normal manual Studio launches remain interactive. See
[background testing](docs/background_testing.md) for receipts and requirements.

```powershell
python tests/verify.py
python -m unittest discover -s tests -p test_asset_audit.py -v
```

Runs headless unit tests, then real GPU/GLB/full-HD spikes and a temporary editor
window. The editor test exercises own controls/input handlers, not OS-level mouse
automation. FFprobe checks silent and tone exports; decoded WAV RMS checks onset.
The audio editor runner captures the application's actual audio bus (muted after
capture) and tests real WASAPI playback/seek/pause; a separate Dummy driver run
checks fallback. FFprobe and decoded PCM verify the editor's AAC onset/gain.
Logs, sample media, screenshot, representative PNG hashes and JSON reports are
written beneath ignored `output/`. A render-capable desktop and ffprobe are needed.
Godot may exit zero on a script error, so the runner also checks error text/markers.

Individual checks: `python run.py --test unit`, `--test spikes`, `--test editor`,
`--test ui`, `--test pose`. The UI check follows fixture generation by tests/verify.py and verifies
23 presentation/state/render invariants with routed viewport mouse events. It saves
Simple/Advanced and 1200px screenshots; this is not an OS-level human usability test.
Audio spike requires the WAV generated by `tests/verify.py`.

See `docs/progress_memo.md`, `docs/architecture.md`, `docs/benchmarks.md`, and
`docs/decision_log.md` for evidence and next steps.

SFM model/map support and current Workshop availability: see [installed-content guide](docs/installed_content.md). HWM bind-axis adjustment and unsupported session/DMX animation remain documented limits.


Visibility: select an object and change **Visible at this frame**, or use viewport Show/Hide. Keys persist across motion pieces. **Options** sets the project-wide fade:300ms by default,0 for instant cuts. Remove a key or Undo to restore earlier behavior. See docs/visibility.md.


Keyed object rows now expand with the small arrow. Click an animated part or its key to select the original bone and inspect that frame; the camera view stays put. Visibility has its own row. See docs/animated_channels.md for key inspection, legacy behavior and current limits.

New imports use their declared default shape. Older projects keep their previous
neutral appearance; Advanced > **Use imported shape** enables it with Undo. Loose-part
review follows the rendered shape. Advanced > **Base shape · whole project** lets
you choose a mesh part, search its imported shape names, enter an Amount and press
**Apply base amount**. Reset this/all and Undo restore earlier adjustments. These
are static model setup controls. **Shapes / expressions…** is available in Simple:
choose a part/shape, set its Amount and Apply at this frame. With Auto-key on,
move to another frame and apply another amount to animate it. Shape motion follows
its animation block when split, moved or copied. Known Japanese expression names
have marked English estimates; Advanced shows original names. These are direct
imported positional shapes; VRM expression presets and material/bone morphs remain open.
Development **All areas** filters Brows/Eyes/Mouth and non-facial deforms without
changing target identities. Advanced **Organize this control** saves a friendly
name and area with Undo, or returns to the estimate. Unknown controls remain
available. Current automatic areas are name estimates; the geometric estimator
and compound expression catalogue remain unfinished. See [face catalogue](docs/face_catalog.md).
Expression keys are independent of body keys: changing a face preserves existing
body easing. **Remove this shape key here** removes just that expression control,
with Undo. New edits use model5; older model4 files retain their saved motion and
upgrade only when an expression is edited. Root/bone per-axis curves remain open.
**Use imported shape** controls the defaults underneath your explicit adjustments.
See [standard model](docs/standard_model.md) and [secondary motion](docs/secondary_motion.md).
Developer checks: `python tests/verify_helper_morphs.py` and
`python tests/verify_source_shapes.py` compare actual GPU geometry and the normal
review/Undo/HAS/MP4 workflow on hidden desktops.
`python tests/verify_base_shapes.py` additionally checks editable base amounts,
native MMD/GMod/SFM channels, packed/linked saves and failed-edit preservation.
`python tests/verify_shape_animation.py` tests per-frame controls, source-time
blocks/clipboard, native MMD/GMod/SFM/VRM, helper recording, recovery and MP4.
`python tests/verify_shape_catalog.py` checks area filters, manual corrections,
unchanged geometry/animation, native identities, Undo, HAS/cold Open and MP4.

Body edits now key each root/bone independently, preserving untouched parts' easing.
Advanced **Delete selected part key** removes only that part's key. New body edits
use model6; old projects retain their saved motion and promote when edited. Packed/
linked saves and recovery retain editable controls. See [body controls](docs/body_animation.md).
`python tests/verify_body_animation.py` checks normal editing and direct rendering;
`verify_body_curves.py` retains the earlier standalone comparison.
Independent per-axis curves remain open.

New projects default to **Unshaded**: base colors and textures without lighting.
The Simple lighting menu also offers **Lit** for imported scene lights (unlit scenes
can be dark) and **Studio light** for the original preview illumination. Older
projects keep Studio light until changed. Preview and export share the saved choice,
with Undo. See [lighting](docs/lighting.md) for material safety, native limits and
`python tests/verify_lighting.py`. Native Source lightmaps remain unfinished.

Drawing Undo/Redo preserves running 3D physics while refreshing pixels, cels and
layer controls. See [independent drawing history](docs/drawing_history.md) for
the regression check and the separate recording/export policies.

Advanced Fill offers [Grow under lines](docs/fill_expand.md), a previewed0–8pixel
expansion for color beneath translucent ink edges. Use Flats below ink; growth
can cross narrow boundaries. Default0 preserves previous fill behavior.

Advanced [Fill connections](docs/fill_connections.md) chooses Edges only (the
default) or Edges and corners for diagonally touching areas. Canvas-edge/large
fills still preview first; the choice does not change the common scene format.

Draw → [Select area [M]](docs/drawing_selection.md) selects a rectangle, moves
pixels by dragging inside, or Shift-drags a copy. Drop creates one Undo step;
Escape cancels. This first raster tool preserves live3D physics and camera keys.
Its [Resize / rotate](docs/drawing_transform.md) action adds numeric size/free
rotation with preview/Apply and Advanced stretch/copy. Lasso, clipboard, canvas
transform handles and animated2D placement remain unfinished.
## Personal keyboard controls

Settings → Keyboard shortcuts changes fifteen main keyboard actions, including
playback, frame steps, drawing tools, Undo/Redo, Save and explicit camera keys.
Clear and restore-defaults are available; duplicate keys refuse. Preferences stay
personal and out of HAS. Mouse/WASD/Alt controls remain unchanged. See
[keyboard shortcuts](docs/keyboard_shortcuts.md) for scope, validation and tests.

Advanced Scene / camera also offers a [numeric camera view](docs/numeric_camera.md):
draft position/angles, Apply to the temporary view, then explicitly Save camera
key. Stale drafts refuse after view/frame changes; source3D and paint stay separate.

[Krita preparation groundwork](docs/krita_preparation.md) now has a read-only
native inventory and a measured installed-Krita animation-rendering experiment.
Desktop KRA import is exposed in Draw; the current application limits and
background/alpha review still apply.

The [prepared raster clip worker](docs/raster_clip_preparation.md) now exercises
explicit scratch-layer choices, transparent normalization, exact holds, fractional
timing and hidden converter cancellation. [In-app review and adoption](docs/krita_import.md)
adds one new editable layer with one Undo, portable ancestry and ordinary HAS/MP4.

Pose mode now includes [Body poses](docs/body_pose_library.md): save a named
authored pose with an isolated thumbnail, reuse it at another frame, and rename,
duplicate or remove it with Undo. Advanced exchanges native HAS-pose data for the
identical imported rig. Position, face and generated motion stay independent.


Video artwork import (2026-11-05): in Draw mode, choose **Import video artwork…**,
review local video with preserved alpha or optional green/blue removal, prepare
and scrub the checkerboard preview, then add one editable drawing layer. Original
files stay unchanged; Add is one Undo. The full clip must fit the current frame
and cel budgets. Audio is imported separately. See [video import](docs/video_import.md)
for bounds, compatibility and tests, and [cloud requirement reconciliation](docs/requirements_cloud_2026-11-05.md)
for remaining features and acceptance gates.

Linux automatic crash recovery now identifies process instances safely and restores
newest valid or older checkpoints through normal startup. See [Linux recovery](docs/linux_recovery.md)
for the portable tests, exact ownership protocol and remaining acceptance limits.

Home -> Tutorials also offers **Advanced - Lighting and export**, with real
lighting controls, a successful MP4 task, hints, checkpointed Previous and
Continue/Start fresh. See [tutorials](docs/tutorials.md).


[Editable sequences](docs/editable_sequences.md) now reuse a child scene with its own
world, camera, cels and sound. Use **Sequences…** above the timeline to create/edit
a child or place another instance, then **Back to parent**. Clip timing, looping,
placement keys and sound stay independent per instance; child edits propagate.
Save and crash recovery retain the enclosing project and active child/frame.
Projects containing sequences require the new schema6 reader.

Home → Tutorials now includes **Advanced · Interpolation and cuts**, an editable
five-task comparison of camera hold, linear and ease with actual saved keys and
recorded-shot evaluation. See [interactive practice](docs/tutorials.md).

**Advanced · Rig posing and foot constraints** adds real arm keys, saved planted
foot ranges, constrained root movement and partial release to the tutorial catalog.

**Advanced · Physics recording** teaches live/frozen motion, explicit Local capture,
recorded playback and MP4. Cancelled or wrong-scope takes do not complete the task.
The course catalog scrolls, and the first-movie verifier now supports private Linux
displays while retaining the Windows private-desktop checks.

Sequence instances now offer [drop shadows](docs/sequence_shadows.md) with offset,
softness and color/opacity, shared by preview, recovery and export. Original child
art stays editable; enabling a shadow uses the explicit studio_sequences_2 format.

[Held artwork caching](docs/sequence_cache.md) reuses sequence pictures across
exposures without freezing parent placement or shadows. The measured240-frame
software-rendering test reduced source builds240→2 while preserving exact output.

Advanced Draw now offers optional [stroke smoothing](docs/stroke_smoothing.md),
default0. It stabilizes pen/eraser paths, finishes tails on release and keeps
pressure gaps empty. Only normal raster pixels are saved; existing formats remain.

Advanced Movie encoder now offers [Standard, Smaller file and High quality](docs/export_profiles.md).
Standard keeps the original defaults; Retry MP4 can use another quality with the
same saved frames/audio while preserving earlier movies.

Sequence instances now have reversible [picture masks](docs/sequence_masks.md):
rectangular crop or cutout before shadow generation. Source art and audio remain
editable; applying a mask opts into studio_sequences_3 within schema6 HAS.

Pose now saves and loads [reusable waypoint paths](docs/movement_path_presets.md).
Preview a route on another model before Apply; position stays independent of pose,
turn, size and expressions, with planted-foot validation and one Undo.
Walking generation and depth inference remain separate work.

Draw also has a [character-sheet reference viewer](docs/reference_sheet.md):
open a local PNG beside the canvas, zoom/pan it, or enable a translucent guide.
It stays out of MP4/PNG output. Enable [Keep PNG in project](docs/project_reference_sheet.md)
to include one sheet in packed/linked saves and crash recovery, with Undo. Kept
sheets use schema7; leaving Keep off preserves the existing project format.

Right-click a visible [reference-sheet color](docs/reference_sheet.md) to choose it
for the brush, including alpha. Transparent pixels and margins leave the current
color intact; the PNG and project history stay unchanged until you draw.

[Reference guide alignment](docs/reference_alignment.md) fits a viewed sheet region
over Draw, with size and output-pixel offsets. It follows canvas zoom/pan and keeps
the full PNG intact; movie frames continue to exclude the guide.

[Sparse sound mixing](docs/sparse_audio.md) now skips quantization across silent
timeline gaps while retaining exact PCM, fades, peaks and clipping counts. The
measured60-second internal case improved1289ms to122ms; source and mixer memory
bounds remain unchanged. [Longer parent timelines](docs/extended_timing.md) now use
the explicit schema8 wrapper while retaining those resource limits.
