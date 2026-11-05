# Custom Hybrid 3D/2D Animation Studio

**Codex implementation brief and living engineering specification**  
**Prepared:** October 29, 2026  
**Target:** Windows 10/11 desktop, offline-first, single-artist workflow  
**Status:** Requirements confirmed through owner conversation; implementation not started  
**Working name:** *Hybrid Animation Studio* (placeholder; owner chooses final name)

> **Read this first, Codex:** The product's entire reason for existing is this workflow: **load an independently created 3D environment → position and animate a camera → draw 2D characters over the resulting view on separate layers without changing the environment → preview the same synchronized timeline → export an MP4.** Everything else is subordinate. Do not turn this into a full Blender replacement, a general-purpose video editor, an AI image generator, or a GMod clone. Build a usable vertical slice before adding advanced features.

---

## 1. Product intent and verified owner decisions

The owner previously used **Garry's Mod (GMod)** for 3D locations, camera positioning and captured background snapshots; **Krita** for rough sketches, clean line art, flat colors and frame-by-frame character animation; and **Kdenlive** for sound, timing, stacking sequences and finished video. The repeated transfers between programs are a bottleneck. The goal is an original, locally usable desktop application designed for that exact working style.

**Decided by owner:**

- **Windows first**, installed/run locally; offline functionality must not depend on a cloud service. Linux and public freeware distribution are possible later, not commitments.
- Load **standardized 3D scenes** created outside this app, potentially created via scripted Blender work with AI coding assistance and owner direction. Standard import is the main path; optional Source/GMod import is explicitly a later, separate compatibility feature.
- Offer a **GMod-like free-flying camera** with position, rotation/POV, field of view and camera keyframes. The user values familiarity over an extensive new set of modeling controls.
- A **single master timeline** synchronizes 3D camera, optional 3D character reference poses, hand-drawn 2D imagery, nested sequences, video, audio/voice and effects. Default **24 frames per second**, adjustable on a per-project basis.
- **Space** plays/pauses. Arrow keys move between frames when appropriate. Mouse/timeline scrubbing is essential. A frame number refers to the same instant across tracks.
- 2D drawings are placed **over** the 3D viewport but must be editable independently. The scene, meshes, materials and camera must remain unchanged when painting.
- The owner draws original rough sketches, cleans anatomy/line art and fills flats. This is a **human-directed drawing tool**, not an automatic AI animator.
- Prefer separate **rough, line-art, color and effects layers**, with visibility/opacity, erasing, frame holds and onion skinning.
- Allow separately poseable 3D character references (including three-quarter views), visibility/opacity toggle, saved poses and interpolation as *references* for drawings. Such references can be excluded from final renders.
- Audio clips/voice lines and sound effects share the timeline and are audible during preview and export.
- **MP4 video output** is the minimum finished deliverable; preferably H.264 video with AAC audio, subject to available encoder and licensing constraints. PNG image sequences remain useful for intermediate/export recovery.
- Later: stacked/nested sequences inspired by Kdenlive, chroma key of imported clips, shadows/VFX, improved fill and cleanup tools, character sheet references and optional line-art/consistency assistance.

**Not decided / do not assume:** final product name, proprietary vs open-source license of the app itself, publicly distributed assets, commercial rights to every third-party model, exact tablet hardware, chosen file extension, cloud features, trained AI models or a particular engine. Make sensible documented choices for an initial working prototype but leave irreversible choices configurable.

### 1.1 The central acceptance story

The owner creates a short 3D room externally, imports it, sets camera A at the empty side of the room on frame 0 and camera B facing a character on frame 48. The camera moves smoothly between those two keys. A rigged 3D reference model stands in the scene, turns three-quarter toward camera and waves an arm; the owner may show/hide it while drawing and may mark it reference-only. At selected frames, the owner draws the character's outlines and colors on independent transparent 2D layers, possibly holding a drawing for several frames. The owner adds a voice clip and an effect, presses Space to preview, and exports a 2-second 24-fps MP4 containing the animated environment, the hand-drawn character and audio, without the reference mannequin if hidden for output. The saved project reopens without losing data.

**Definition of success:** This entire story works end-to-end on a clean Windows machine. Its reliability matters more than a long feature menu.

---

## 2. Core artistic model: what exists at a frame?

At time `t = frame_index / fps`, the scene is built from **independent** sources:

```text
PROJECT (default 1920 x 1080, 24 fps)
│
├── 3D scene assets: environment + lights + optional reference rigs
│   └── 3D camera track: position, orientation, FOV, keyframes
│       └── 3D renderer → background image for frame N
│
├── 2D drawing / cel tracks (RGBA with actual transparency)
│   ├── Character A: rough [hidden for final]
│   ├── Character A: ink
│   ├── Character A: flats
│   └── Effects / shadow overlays
│
├── Imported image and video clip tracks
│   └── Optional alpha or chroma key
│
├── Audio tracks: dialogue / sound effects / music
│
└── Master timeline / transport: frame N
    └── Composite → preview at N → PNGs → MP4 + synchronized audio
```

The **2D canvas is camera-screen-space**, not a texture painted onto the 3D geometry. It has project-resolution coordinates, so the owner draws exactly the visible perspective generated by the 3D camera at that moment. Adding or clearing paint does not edit the 3D environment. A later optional **3D-anchored drawing** feature may exist, but must not replace screen-space cels.

Each drawn cel has a start frame, exposure/duration (hold), editable layers and source data. Cels may reuse drawings from earlier frames. The user can still redraw every frame by choice. A 3D pose's movement and the camera's movement are sampled at every frame, **independently of how often the user redraws**. Do not auto-warp a 2D cel to track the model unless explicitly requested; screen-space drawings cannot automatically maintain perspective with a moving camera.

**Critical workflow distinction:** camera/pose interpolation is automatic between keys; raster animation may hold a drawing on ones, twos, threes or custom exposures. At 24 fps, a held cel on twos appears over two rendered frames. The app must never silently assume every scene frame needs a new drawing.

---

## 3. Build strategy and candidate technology

### 3.1 Recommended implementation starting point: Godot 4.x

Use a pinned **stable Godot 4.x** version, preferably GDScript initially for speed of prototyping; C# or a native extension only when measurements justify it. Build a **standalone custom editor-like application**, not a plugin that requires users to operate the Godot editor. Godot gives cross-platform foundations but **ship Windows first**.

Why this is a candidate rather than a guarantee:

- Godot supports real 3D cameras, lighting and glTF scene/model imports.
- A `SubViewport` can render the 3D background to a texture, over which transparent 2D content can be composited.
- `Image`, `ImageTexture` and UI input events can support a prototype raster canvas, but **large-canvas, low-latency pressure-sensitive painting and GPU readback performance must be measured**. There is no assumption Godot includes a ready-made Krita-quality painting engine.
- Keyframe interpolation and audio facilities exist, but this application needs a **single custom project-time authority**, not uncoordinated engines with slightly different clocks.
- Godot's engine uses MIT licensing, which can accommodate a separately licensed/proprietary app if notice obligations are met.

Alternative if the raster tablet proof fails: **Qt 6 UI + specialized raster/compositing engine + embedded 3D engine**. This likely increases integration work; compare before committing. **Do not mix multiple UI frameworks in v0**. Qt tablet events expose stylus pressure/tilt, but Qt's own deployment license terms and, on Windows, device/driver behavior need evaluation. Avoid making licensing claims about components not yet selected.

### 3.2 Architectural decisions

- **Editor shell**: distinct panels for scene viewport, layers, timeline, brushes, assets, inspector, transport; dock/split preferred.
- **Scene render**: external `.glb`/`.gltf` file + separate camera animation and reference-only flags in project data.
- **Canvas**: RGBA, premultiplied-alpha-safe compositing, pixel-coordinate mapping, brush input abstraction, tiled or damage-rect updates as scale increases.
- **Timeline**: integer `frame_index` as canonical unit, rational `fps_num/fps_den` (default `24/1`), sample-accurate audio conversion using integer/rational math.
- **Storage**: editable directory project during development (`project.json` plus `assets/`, `cels/`, `audio/`, `cache/`); do not make a fragile opaque binary container the only way to recover work. Version schema and support migration.
- **Render**: same scene evaluation function in preview and offline render; a deterministic frame renderer outputs RGBA PNG, then external FFmpeg process muxes image sequence/audio into MP4.
- **Work files**: keep original source asset files intact; import by copy with explicit relinking or use managed asset references. Record provenance and licenses where available.
- **App boundaries**: editor cannot directly overwrite external source `.glb` or original audio files. Non-destructive changes are stored as project-level transforms, animation curves, masks and overlays.

### 3.3 First two risk spikes — mandatory before broad UI work

**Spike A: 3D viewport plus raster cels.** Import a sample `.glb`, move a camera, render into a SubViewport, draw a pressure-independent mouse stroke on transparent pixels, toggle visibility, and composite without touch to the scene. Test at 1920×1080, playback and zoom.

**Spike B: reliable frame/audio export.** For 48 frames at 24 fps, sample camera transform exactly for each frame, render sequential PNG files, encode an MP4 and add a known-tone WAV segment. Compare preview against output, verify duration with `ffprobe`, and check lip/audio position. Show clear errors if FFmpeg is absent. **Do not promise exact MP4/H.264/AAC output until a compatible FFmpeg distribution and actual encoder availability are confirmed.**

If a spike fails, document failure, alternative designs, benchmark and recommendation *before* building a sophisticated UI around it.

---

## 4. UI and interaction model

```text
┌───────────────────────────────────────────────────────────────────┐
│ File  Edit  View  Scene  Drawing  Animation  Audio  Export         │
├──────────────┬─────────────────────────────────┬──────────────────┤
│ Assets       │        Composite Preview        │ Layers / Brush    │
│ Scene GLB    │  3D environment                 │ Rough [eye]       │
│ Characters   │  + 2D drawing on top            │ Ink   [eye]       │
│ Audio        │  + optional 3D reference        │ Flat  [eye]       │
│ Sequences    │  Camera: pan/orbit/free-fly     │ VFX   [eye]       │
│              │                                 │ Size, opacity     │
├──────────────┴─────────────────────────────────┴──────────────────┤
│  ◀ | ▶ / Pause | frame 0024 | 24 FPS | 00:01.000                │
│  Camera  ├──────◆──────────────◆─────────────────┤               │
│  RefRig  ├────────◆────────────◆─────────────────┤               │
│  Drawing ├[cel 01][cel 02][ held cel 03          ]┤               │
│  Voice   ├─────[voice_01.wav ~~~~~~~~~~~~~~~~~~~ ]┤               │
│  SFX     ├─────────────────────[impact.wav]───────┤               │
└───────────────────────────────────────────────────────────────────┘
```

This is a layout concept, not a fixed pixel-level mockup. The artist can switch between **Scene**, **Pose**, **Draw**, **Composite**, and **Export** views, but switching views must preserve frame, camera and timeline state. Importing a background does not require leaving the project. Separate draw mode navigation from brush events to prevent accidental marks.

### 4.1 Keyboard defaults (configurable)

| Action | Default | Behavioral constraints |
|---|---|---|
| Play/pause | Space | Only if canvas text input isn't active; pause holds exact current frame |
| Step backward / forward | Left / Right | One frame per keypress when timeline/canvas navigation has focus |
| First/last frame | Home / End | Within active sequence |
| Undo/redo | Ctrl+Z / Ctrl+Y or Ctrl+Shift+Z | Drawing changes and keyframe edits with clear undo groups |
| Save | Ctrl+S | Atomic durable save; show saving state |
| Brush / eraser | B / E | Draw mode; do not activate in filename fields |
| Toggle selected reference | configurable (e.g. R) | Independent preview vs render visibility |
| Add camera keyframe | configurable (e.g. K) | At current exact frame; do not overwrite unintentionally |
| Pan canvas | Space+drag *only while stopped* or middle mouse | Resolve Space/play collision explicitly; recommend middle mouse and a remappable modifier |
| 3D navigate | WASD + mouse look while scene navigation active | GMod-style feel; speed modifier, sensitivity, up/down controls |

Camera control modes: free-fly, orbit around target, pan, dolly, FOV change, look-at marker, and numeric transform entry. In the first usable milestone, free-fly, rotate and position keyframes are enough. Do not bind WASD in drawing mode. Make selectable interpolation **hold, linear, ease-in/out**; quaternion/spherical interpolation is preferable for rotations to avoid sudden flipping. Explicitly specify angular convention and coordinate conversion for imported assets.

### 4.2 Timeline mechanics

- Frame ruler labels and timecode; zoom, horizontal scroll and scroll-to-playhead.
- Clicking a frame samples 3D scene, poses, cels and audio location at that instant.
- Camera keys and cel exposure boundaries are visually different.
- Create, duplicate, move, extend and delete cels; hold last image; insert blank cel; duplicate previous drawing without forcing that workflow.
- Play can run at lower interactive quality; exported frames must be deterministic, full resolution.
- Audio waveform and basic volume gain; play/pause synchronized to timeline with a master audio clock during normal playback, seek correction and frame-accurate offline render.
- Editing should use integer frame addresses; clip duration and audio sample position can be derived; implement fractional rates without drift.
- Playback behavior for heavy 3D scenes must be explicit: either drop visual preview frames while retaining timeline time, or use frame-locked preview mode. Never silently slow audio or change export timing.

---

## 5. Detailed components and delivery stages

### Stage 0 — repo, setup, build reproducibility

**Deliver:** source repository, pinned engine version, dependency manifest, `README.md` with one-command-ish Windows instructions, `docs/architecture.md`, `docs/decision_log.md`, `docs/licenses.md`, example test scene, automated smoke runner. Use Git and small commits. No dependence on cloud APIs.

Create runnable template and CI/build command first. Add developer debug overlay showing `frame`, `fps`, render time, scene loaded, cel count and audio position. No fake buttons or menus.

**Exit:** clean checkout can launch a window on target Windows system; tests can run; first import sample distributed under a compatible license or generated procedurally.

### Stage 1 — critical vertical slice (MVP minimum)

1. Load a standard `.glb` into a 3D viewport, with useful error messages for broken imports.
2. Implement free-fly camera, mouse-look and FOV. Store at least two camera keyframes and interpolate at exact frames.
3. Implement a simple timeline at 24 fps and 48-frame example; Space play/pause, arrows and click-to-scrub.
4. Implement a transparent drawing overlay with at least two editable RGBA layers, pen, eraser, brush radius and mouse drawing. Place paint in *output-frame coordinates*, not scene mesh coordinates.
5. Store independent drawing cels, each with frame exposure; support hold/duplicate and visibility.
6. Composite background + visible paint layers in correct order at every frame. Preview and export must agree.
7. Save/load the project; include source assets, cels and camera keys.
8. Export 48 full-sized PNGs; convert to MP4 via clearly detected FFmpeg binary. Show progress, cancel option and readable error messages.

**Exit demo:** animated camera traverses a procedural test room; hand-drawn circle or character remains correctly positioned on the canvas relative to *screen-space*; 2D layers toggle without changing the `.glb`; playback and exported MP4 match sample frames. Audio may be absent in this first narrow milestone, but must be added in Stage 2 before claiming the conversation's full minimum experience.

### Stage 2 — audio and real animation usability

- Import WAV first, then MP3/OGG where reliable decoder permits.
- Add timeline audio clips, start offset, gain, mute/solo, simple waveform, seek playback and scrub feedback (toggleable).
- Export mixed synchronized audio to MP4; use temporary uncompressed WAV and mux at final stage to limit time drift.
- Add rough/ink/flats layer presets, palette, eyedropper, undo/redo, timeline onion skin and brush opacity.
- Add pressure-sensitive tablet input once actual hardware or a reproducible event test is available; test Windows Ink/Wintab compatibility rather than claiming universal tablet support.
- Add pixel bucket fill and a configurable gap-closing threshold. Test connected-region logic, transparent boundaries, anti-alias fringes and undo; never fill whole canvas unexpectedly without an undo path.
- Fix input remapping, recovery and autosave before aesthetic polish.

**Exit:** owner can draw a rudimentary hand-drawn character, hear a voice line at a precise frame, save/reopen and export a 3D-background/2D-character/audio clip without using Krita or Kdenlive for the test.

### Stage 3 — reusable 3D reference characters

- Import a rigged glTF/GLB character with skeleton metadata and bones; show a meaningful skeleton/tree.
- Let user manually rotate selected bones with gizmos and local/global axes, position root and store/restores saved poses.
- Pose reference keyframes on same master timeline with interpolation between poses.
- Show reference in scene and/or separate **reference-only overlay**; independent preview and final-export visibility; adjustable transparency if renderer/composite allows it.
- Pose library with thumbnail, rename/duplicate, import/export within project. Optional ghost poses and alignment guides.
- Handle camera orbit/3⁄4 views, model scale and rig differences gracefully. An unrigged asset should load for viewing but disable pose controls with clear explanation.
- No need to implement inverse kinematics or automatic anatomy correction for this stage; allow manual keying first.

**Exit:** posed mannequin's waving arm and turning body can be scrubbed; owner toggles it while drawing and hides it on final export.

### Stage 4 — compositing and sequenced workflow

- Add multiple character/clip tracks, transform/opacity/keyframed placement and simple 2D shadows or glow.
- Implement a **sequence asset** with its own local timeline and references to child tracks; support placing a sequence as a clip on a parent timeline. Define explicit local-to-parent time mapping, offset, looping and duration. Guard against cyclic references.
- Import pre-rendered clips with alpha where possible; for solid green-screen clips implement chroma key with tolerance, softness and spill suppression. Prefer true transparency over green screen when available.
- Audio clip stack supports voice, sound and music with simple gain/fades; keep an independent sequence's audio synchronized when nested.
- Preserve editable sources; changing a sub-sequence updates parent preview after invalidating cache.
- Add optional transparent PNG sequence export and flattened still export.

**Exit:** character animation sequence can be reused over two backgrounds; second clip is composited on top; one exported file contains both and their audio.

### Stage 5 — quality-of-life and optional intelligence

Only pursue after stages 1–4 are demonstrated, prioritized by measured owner pain:

- Gap-aware fill, local line closure and cleaner anti-aliased flat colors.
- Frame-to-frame comparison, onion skin, colored drawing ghost, linked character sheet and anatomy proportion overlays.
- Optional line-art suggestions and consistency checks; keep original strokes and show review/accept/reject. AI, if used, must be opt-in, local/offline when possible, versioned and licensed, never required to open projects.
- Lightweight in-between suggestions, *not* a mandatory automatic interpolation of painted raster characters.
- Brush smoothing, selection/transform, masks, multiple color palettes and export profiles.
- Optional Source/GMod importer through lawful conversion paths; do not embed Valve or Workshop assets, bypass DRM or imply redistribution rights.
- Optional Blender-assisted scene authoring: external Blender scripts generate owner-directed original 3D geometry then export `.glb`.

**Exit:** each feature has a documented user story, measurable benefit, regression test and can be disabled without breaking earlier projects.

---

## 6. Import rules, 3D camera and project asset handling

**Primary 3D format:** `.glb` (binary glTF 2.0); `.gltf` with sidecar assets as secondary. Its supported building blocks include geometry, PBR materials, textures, cameras, joints/skin and animation, although importer/exporter feature coverage varies by version. Blender can author and export compatible projects; the studio is not obligated to edit meshes. Additional FBX, OBJ or Blend support should be via external conversion initially rather than a broad importer rewrite.

Define an import contract:

1. Asset source file and original path; optional copy into project package.
2. Units, up-axis, world origin, object hierarchy, coordinate transforms.
3. Default materials, texture paths, missing-texture warnings.
4. Optional camera and animations from file, but app-created camera keys remain editable separately.
5. Reference-only metadata on objects/skeleton instances; visibility in preview and final render deliberately separated.
6. Manifest stores generated asset IDs and checksum, so renames and missing files are diagnosable.
7. The importer never edits or overwrites the original `.glb`.

A **camera track** stores `[frame, position, quaternion, fov_degrees, interpolation_mode]`. The owner may set cameras at frame 0 and frame 48; if duration is 48 frames indexed `0..47`, a key on 48 belongs to the first sample of the following second. **Avoid off-by-one misunderstandings**: show both end-exclusive duration and frame numbers, and test exact values at 0/24/48. Use explicit out-frame convention in UI.

Camera movement example: empty room at `f=0`, subject in focus at `f=48`; animate position and orientation smoothly across two seconds. Character rig rotates from forward to three-quarter while waving; sample all three independently. Even if drawn cels change only at frames 0, 12, 24, 36, camera is evaluated for each exported frame.

### Scene navigation vs project camera

Keep a **temporary editor navigation camera** separate from the **animated shot camera** where feasible. The artist can inspect a scene without accidentally rewriting a shot. Provide `Look Through Shot Camera` and `Use Editor Camera`, and an explicit button to insert/overwrite a keyframe. Save safely.

---

## 7. 2D drawing engine details

The drawing canvas must correspond exactly to output resolution; map mouse/stylus through viewport zoom/pan and device scaling to raster coordinates. Use RGBA with alpha, document color space and interpolation. Separate rough, ink, flat and effects images by cel. All pencil changes are commands with reversible before/after tile data or compressed diffs (avoid full-frame snapshots on every stroke at 1080p).

**Input:** strokes with tool, points, timestamps, pressure if available, radius, opacity and color. For the first prototype, pixel-based raster stroke is acceptable. Later store path/stroke metadata to enable non-destructive re-render; do not promise vector behavior immediately.

**Performance:** do not send entire full-HD images from CPU to GPU on every pointer move without measurement. Consider dirty rectangle uploads, render-to-texture brushes or tiled caches after baseline. Test memory for many frames: a single 1920×1080 RGBA image is ~7.9 MiB; 100 frames × 4 layers is ~3.1 GiB uncompressed. Compress cold cels, lazy-load, cache recent frames, track dirty state, and bound history.

**Bucket fill:** implement iterative non-recursive flood fill, configurable connectivity, tolerance, border expansion and gap-closing preview; test anti-aliased line art with fine gaps. A fill must never mutate the reference scene or invisible layers. Add option to reference visible composited ink while painting into current flat layer, with clear sampling rules.

**Anatomy/consistency help (later):** allow a user-provided character sheet and translucent reference rigs, 3⁄4 views, overlays and prior-frame comparisons. Optional automated suggestions must be reversible and preserve artist choice.

---

## 8. Timing, output and sync contracts

- The project timeline stores integer frame indexes; FPS is rational.
- Frame timestamp for export sample `n` is `n * fps_den / fps_num` seconds, with image count exactly `N` for `N` duration frames.
- Typical target: 1920×1080, 24 fps, MP4 with H.264/AAC if legally available in the selected FFmpeg binary; optional user-installed FFmpeg path.
- Export in a temporary work directory: `frame_000001.png`, etc., and an audio mix. Never overwrite project files.
- Render **deterministically**: scene state at frame `n` is a pure function of project + asset data + `n`; not the current wall clock or engine frame delta. This matters for dropped interactive frames and reliable export.
- FFmpeg invocation must use an argument array, not a user-influenced shell string. Quote/escape Windows paths correctly; validate paths, missing codec cases and disk capacity. Avoid arbitrary command injection.
- Give progress/cancel/error info. On failure, offer to keep PNG frames and logs; do not quietly claim success.
- Preview should approximate final composite; test pixel comparisons for static samples with known color management differences and log unavoidable differences.
- When audio is absent, export silent video rather than fail. When audio exists, produce correct muxed output; avoid duplicate audio when nesting sequences.

**FFmpeg example (illustrative, verify binary and build licensing):**

```bash
ffmpeg -framerate 24 -i frame_%06d.png -i mixed_audio.wav \
  -c:v libx264 -pix_fmt yuv420p -crf 18 -preset medium \
  -c:a aac -b:a 192k -movflags +faststart -shortest output.mp4
```

The example requires an FFmpeg build that actually supports `libx264`; not all builds do. Document its license and any patent/distribution issues for the chosen binaries. Default to a user-configurable encoder path and display capability detection before using optional codecs. Avoid `-shortest` when audio length and desired picture length would cause truncation; ensure output runs for the exact intended sequence duration (trim/pad audio explicitly).

---

## 9. Suggested project format (provisional schema)

Use a clear versioned JSON document; actual storage may evolve. Example below is **illustrative**, not production schema or executable application.

```json
{
  "schema_version": 1,
  "project_name": "CameraAndWaveTest",
  "video": { "width": 1920, "height": 1080, "fps_num": 24, "fps_den": 1, "duration_frames": 96 },
  "assets": [
    { "id": "room", "kind": "gltf", "path": "assets/room.glb", "sha256": "computed-on-import" },
    { "id": "voice", "kind": "audio", "path": "audio/line.wav", "sha256": "computed-on-import" }
  ],
  "scene": { "asset_id": "room" },
  "camera_track": {
    "keys": [
      { "frame": 0, "position": [0, 1.7, -5], "rotation_xyzw": [0, 0, 0, 1], "fov": 60, "interpolation": "linear" },
      { "frame": 48, "position": [2, 1.7, -2], "rotation_xyzw": [0, 0.3, 0, 0.953939], "fov": 55, "interpolation": "ease" }
    ]
  },
  "tracks": [
    { "id": "ink", "type": "raster_cels", "z_order": 20, "visibility": true,
      "cels": [{ "start": 0, "duration": 2, "path": "cels/ink/000000.png" }] },
    { "id": "voice1", "type": "audio", "clips": [{ "asset_id": "voice", "start_frame": 12, "gain_db": 0 }] }
  ],
  "editor": { "active_frame": 0, "view": "composite" }
}
```

Important refinements: UUIDs rather than display name as identifiers, relative asset paths, stable sorting, layer blend modes, project-wide and sequence-relative coordinate conventions, editor-only state separated from export state, and migration tests. Hashes must be actual computed values in real projects, never strings like the example. Do not deserialize arbitrary code or trust paths containing `..` in imported projects. Atomic save with backup and recovery journal.

**Crash recovery:** save to temporary file + fsync/rename where supported; back up previous manifest; autosave after configurable intervals, never while mid-brush command; recover from interrupted export by keeping generated frames. Incomplete work must be detectable rather than silently discarded.

---

## 10. Acceptance tests and engineering verification

| ID | Test | Passing behavior |
|---|---|---|
| CORE-01 | Import `.glb` sample room | Correct scene visible; missing textures warn |
| CORE-02 | Camera keys 0 and 48 | Changing frame interpolates reproducibly; no angle flip |
| CORE-03 | Canvas isolation | Draw on overlay; original 3D scene hash and materials unchanged |
| CORE-04 | Layer toggle | Hiding rough layer removes it from preview and optionally export |
| CORE-05 | Cel exposure | Cel held 2 frames appears on both, advances correctly at next boundary |
| CORE-06 | Navigation | Space play/pause; Left/Right one frame; no unintended paint |
| CORE-07 | Save/reopen | Scene, keys, layers, frame timing and assets restored |
| CORE-08 | Export video | 48 frames at 24 fps produce ~2 seconds; frame count verified by ffprobe |
| AUDIO-01 | Voice offset | Known transient at frame 24 aligns at 1.000 seconds at 24 fps |
| AUDIO-02 | Silence | Export video with no audio tracks still succeeds |
| REF-01 | Manual pose | Imported rig bones can be rotated, keyed and saved |
| REF-02 | Reference-only | Posed character visible in working preview but absent in final render |
| SEQ-01 | Nested clips | Changing child appears in parent without duplicate/manual rasterization |
| KEY-01 | Chroma key | Green background removed from import without erasing original file |
| SAFE-01 | Corrupt project | Explicit error / recovery, not crash or data loss |
| PERF-01 | 1080p scribble | Brushes feel interactive on owner's actual machine; measured latency logged |

Create integration fixtures for two 3D camera keys, one held red cel, second blue cel, one known WAV impulse and a reference rig. Include tests for Windows paths containing spaces/unicode, long filenames, no FFmpeg, invalid `.glb`, unavailable audio device, missing textures, disk full and interrupted save. Record `ffprobe` metadata and representative frame PNG hashes in CI or local smoke scripts. Be cautious about pixel hashes changing across GPU drivers; compare with tolerance if necessary.

### 10.1 Owner-friendly first demo instructions

1. Launch app with sample room.
2. Choose shot camera; set key at frame 0.
3. Move camera with familiar mouse/WASD; set key at frame 48.
4. Switch to Draw tab, make ink stroke on frame 0; toggle rough/ink visibility.
5. Make another cel at frame 24; hold or duplicate as desired.
6. Press Space, observe camera movement behind character sketches.
7. Add a short WAV after audio milestone; press Space to hear it.
8. Save; reopen; export `demo.mp4`; play video outside the app.

If this fails, do **not** label the milestone complete.

---

## 11. Licensing, ownership, provenance and eventual freeware

The owner wants greater confidence that their animation uses **owner-directed original creative assets**, rather than relying on someone else's GMod maps/models. **Writing/commissioning/AI-assisting the creation of original geometry is not proof that every included asset is legally owned or exclusive**. Import tools do not transfer ownership. Third-party textures, models, music, voices, sound effects and franchise character designs may carry different rights. Building your own drawing of a Touhou character, for example, does not automatically make the underlying franchise character 100% yours. Handle each asset separately and review the applicable fan-creation guidelines before publishing.

**Do not conflate:** (a) the app's copyright/license, (b) underlying engine/library license, (c) licenses for individual imported assets, (d) copyright status of AI-assisted output, and (e) distribution rules for FFmpeg codecs. These are different questions and may depend on jurisdiction and circumstances. This document is engineering guidance, not legal advice.

Prefer MIT/BSD/Apache-licensed code where feasible, but preserve all notices. Godot's MIT engine is compatible with separately licensed applications if required notices are included. FFmpeg builds vary between LGPL and GPL depending on enabled components; do not simply redistribute arbitrary downloaded executables without license review. Never download models/assets silently from the web. Provide a built-in **Credits / Open Source Notices** panel and machine-readable third-party manifest; keep source links, versions, licenses, modifications and authors. Owners may later choose freeware distribution via banderov.com; don't prematurely force any app license.

**Suggested metadata for each asset:** `source`, `author`, `license`, `license_url`, `acquisition_date`, `changes`, `attribution_required`, `redistribution_allowed`, `owner_created` and `provenance_notes`. Empty fields should show “unknown / must verify,” never fabricated rights claims. If user prefers a special copyleft credit line in finished films, allow configurable export credits; don't mislabel the software's legal license.

---

## 12. Risks and priority order

**Priority 1: verify that this exact art workflow works.** Potential problems:

1. **Drawing performance:** Godot image updates, tablet stroke quality, memory pressure from 1080p raster cels. Mitigate with measured proof, caching, tile updates and possible specialized drawing subsystem.
2. **Camera/2D registration:** rendered camera motion changes perspective but screen-space cels do not follow automatically. This is intentional, yet artist must redraw/hold drawings and get clear reference frames. Add optional tracking later if actually requested.
3. **Timing drift:** preview delta-time vs exact export-frame sampling and audio resampling. Use single time model and tests.
4. **Source asset limitations:** GLB import may not preserve Blender's every shader, physics, particle simulation or script; provide compatibility guidelines and baking/export helpers.
5. **Paint editing safety:** canvas layers accidentally flattened, files corrupted on crash, expensive undo. Use proper project state and recovery.
6. **Encoder licensing/availability:** detect and document FFmpeg and codecs, allow an encoder path, test on clean Windows machine.
7. **Feature creep:** built-in modeling, GMod conversion, 3D rigging, AI anatomy, high-end VFX, and full Kdenlive replacement could consume the project before the essential workflow runs.

**Guardrails:** No cloud dependencies, no compulsory subscriptions, no AI-generated paintings automatically applied, no dependence on ownership of proprietary GMod assets, and no asset formats that can only be read by an online vendor service.

---

## 13. What Codex should do immediately

1. Read this entire specification. Restate the **confirmed requirements**, **provisional engineering decisions**, and **deferred ideas** in a short project README, preserving these distinctions.
2. Inspect the working directory. **If a repo already exists, examine it before modifying it**; do not overwrite work. If new, initialize a Git repository and a clean Godot 4.x application structure.
3. Check installed tools, Windows OS/build environment and FFmpeg availability. Where absent, give reproducible installation instructions rather than pretending installations succeeded.
4. Pin the chosen versions and document why. Review license obligations for every dependency or borrowed asset before distribution.
5. Run **Spike A** and **Spike B** as standalone reproducible demonstrations, report timings, and explain any blockers.
6. After working spikes, implement **Stage 1** incrementally with real functionality and tests. Keep each milestone runnable; avoid placeholder controls in demos.
7. Build an owner-facing demo based on section 10.1; include screenshots or exported sample media if available.
8. Before Stage 2 or anything more complex, write a short progress memo listing implemented features, failing tests, known limitations, and the **one or two decisions the owner must make**. Do not bury them in a giant backlog.
9. Do not implement Stage 3–5 without a working Stage 1 and explicit prioritization, though interfaces should leave room for them.

### 13.1 Expected repository layout

```text
hybrid-animation-studio/
├── README.md
├── AGENTS.md                 # instructions for AI coding agent
├── project.godot
├── addons/                   # only verified, licensed extensions
├── src/
│   ├── app/                 # editor shell, panel focus, shortcuts
│   ├── scene3d/             # importer, environment, cameras, reference rigs
│   ├── drawing/             # brush, cels, layers, compositing
│   ├── timeline/            # project time and keyframe evaluation
│   ├── audio/               # clips, playback, mix
│   ├── project/             # serialization, manifests, recovery
│   ├── export/              # PNG renderer, encoder adapter
│   └── ui/
├── tests/
│   ├── fixtures/            # self-created test scene/rig/cels/WAV
│   ├── unit/
│   └── integration/
├── docs/
│   ├── architecture.md
│   ├── decision_log.md
│   ├── milestones.md
│   ├── licenses.md
│   └── benchmarks.md
└── examples/
    └── camera_wave_demo/
```

### 13.2 Suggested `AGENTS.md` instructions to implement

- Read `CODEX_CUSTOM_ANIMATION_STUDIO_SPEC.md` and existing code before modifying files.
- Always prioritize **3D environment → animated camera → 2D drawing overlay → synchronized preview → MP4**.
- Work in small tested increments, explain deviations from spec and note provisional design choices.
- Do not fabricate test outcomes, support claims, citations, license permissions or benchmark numbers.
- Do not assume 3D model generation, Krita-quality tools, lip-sync or neural in-betweening are part of the initial prototype.
- Preserve original assets and non-destructive 2D layers. Add autosave/recovery tests.
- Do not add network calls without owner approval.
- Ask for owner decisions only when blocking implementation or materially affecting the workflow; otherwise make reversible documented defaults.
- Distinguish between *working*, *implemented but unverified*, *planned* and *unsupported* features.

---

## 14. Documentation and technical sources for Codex to verify

These are official or primary sources for the proposed building blocks, not claims that a finished program already exists. **Codex should re-check current stable docs and dependency licenses at implementation time.**

1. Godot Engine. (n.d.). *SubViewport*. https://docs.godotengine.org/en/stable/classes/class_subviewport.html
2. Godot Engine. (n.d.). *Image*. https://docs.godotengine.org/en/stable/classes/class_image.html
3. Godot Engine. (n.d.). *ImageTexture*. https://docs.godotengine.org/en/stable/classes/class_imagetexture.html
4. Godot Engine. (n.d.). *License*. https://godotengine.org/license/
5. Godot Engine. (n.d.). *Complying with licenses*. https://docs.godotengine.org/en/stable/about/complying_with_licenses.html
6. Blender Foundation. (n.d.). *glTF 2.0 import/export*. https://docs.blender.org/manual/en/dev/addons/scene_gltf2.html
7. FFmpeg project. (n.d.). *FFmpeg licensing*. https://ffmpeg.org/doxygen/trunk/md_LICENSE.html
8. Qt Company. (n.d.). *QTabletEvent, Qt 6*. https://doc.qt.io/qt-6/qtabletevent.html
9. Qt Company. (n.d.). *Tablet example*. https://doc.qt.io/qt-6/qtwidgets-widgets-tablet-example.html
10. Khronos Group. (n.d.). *glTF specification / resources*. https://www.khronos.org/gltf/
11. FFmpeg project. (n.d.). *FFmpeg documentation*. https://ffmpeg.org/ffmpeg.html
12. Godot Engine. (n.d.). *Animation*. https://docs.godotengine.org/en/stable/classes/class_animation.html

**Attribution practice:** maintain `CREDITS.md` and `THIRD_PARTY_NOTICES.md` with author, title, year if available, source URL, license and what is reused. For borrowed algorithms or designs, add proper citations and distinguish inspiration from copying.

---

## 15. Plain-language finish line

This app should feel like the owner is working in **one place** rather than jumping between GMod, Krita and Kdenlive. They can orbit/fly through their own 3D scene and animate the camera, manually pose a character reference if desired, switch into drawing and paint a hand-drawn 2D character *over* that rendered perspective, arrange drawings and sounds on one 24-fps timeline, preview with Space, and export a playable MP4. They do **not** need to construct 3D environments inside this app, own a particular third-party GMod model, use an AI art generator, or understand Blender's full interface.

**Build this first. Preserve the creative separation between 3D backgrounds and 2D artwork. Make the owner able to complete a tiny film from start to finish.**
