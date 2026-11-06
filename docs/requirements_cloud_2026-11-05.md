# Requirement reconciliation — 2026-11-05 UTC

The complete486-line original specification,613-line design addendum, README,
dependencies, AGENTS, voice audit and10,501-line chronological progress memo have
now been read. Root LLM.md is standalone; the missing Windows parent history has
not been invented. The supplied archive was recovered before selecting new work.
See [source provenance and baseline](cloud_source_recovery.md).

This matrix separates **present** code from **fresh** cloud checks. Present is not
a claim that every acceptance scenario passes. Historical Windows results remain
historical. The addendum governs conflicts and preserves its decision labels.

## Original specification

| Requirement | Present implementation / evidence | Remaining gate or work |
|---|---|---|
| §§1–2 artistic model | `app.gd`, `renderer.gd`, `drawing.gd`: shared 3D/camera plus independent RGBA cels; synchronized frame domain | End-to-end artist acceptance |
| §3 architecture / mandatory spikes | Pinned standard Godot4.6, Python workers, installed FFmpeg, no compulsory AI; recovered spikes and shared renderer | Real Windows GPU/device verification; software tests are a separate gate |
| §4 UI / keyboard | Simple/Advanced same document, viewport navigation, configurable shortcuts, explicit camera keys, body auto-key | Novice comfort and all routed interaction regressions |
| §4.2 timeline | `timeline_view.gd`, clip editors: sparse blocks, drawing exposure dragging, independent tracks and shared zoom/pan with fixed labels | Ripple/stretch/loop/cross-track ownership depth remains incomplete |
| Stage0 setup | Pinned checksummed engine and Python/FFmpeg cloud baseline | Clean Windows install acceptance |
| Stage1 3D / camera / cels / MP4 | Fresh procedural rig/body-pose and video imports, unit24, exact preview/export input, 48-frame movie | Entire core regression matrix below |
| Stage2 drawing / audio | Pressure/opacity, palettes, rect select/transform, fills/closure/growth, onion, MP3/Ogg, multiple audio, trims/fades present | Tablet feel; fresh decoded frame24 audio onset |
| Stage3 posing / reference | Rig-aware pose/IK, body library, Model9 root components/paths, shapes, reference-only rigs and a local/kept PNG reference viewer/Draw guide present | Multiple reference views/proportion tools, native inherited transforms/material/bone/cloth fidelity and broader locomotion |
| Stage4 imported alpha / chroma | **New:** bounded local video→editable holds; tolerance/softness/spill, original alpha and source preservation; fresh units11 + app19 + reader7 | Long/video-track workflows and artistic keying quality |
| Stage4 sequence assets / child propagation | **New:** editable embedded shared scene assets, nested timing/looping/placement, child invalidation and recursive audio; schema6 | Bounded4assets/8clips, child240frames and parent60seconds/7200frames; native and artist acceptance remain |
| Stage4 compositing / output | Multiple drawing layers, sequence placement transform/opacity tracks, simple2D shadows, reversible sequence crop/cutout masks and transparent PNG export present | General layer tracks, painted/lasso layer masks/glow and artistic quality remain |
| Stage5 quality / optional intelligence | Fills, ghost/onion, brush controls including optional smoothing, selection, sequence picture masks, palettes and named movie quality profiles present; no required AI | Optional suggestions require review/accept/reject, provenance and measured owner need; not a completion prerequisite for optional AI |
| §6 import / camera / assets | Original source retained; world/asset management, common/native conversion paths | Broader native fixture fidelity and lawful conversion gates |
| §7 raster engine | Independent full-resolution Images and held exposures, unified composition | Layer/cel bounds remain; lazy long-project support cannot be inferred |
| §8 exact timing / output | Rational rates, end-exclusive holds; new fractional-video tests and 1080p24 movie pass | Fresh full audio sync and export fault matrix |
| §9 project data | Existing scene5, Model9, audio4 plus sequence schema6; packed/linked, ancestry and source hashes | Explicit schema8 longer-parent wrapper present; lazy/dense caching and native scene acceptance remain |
| §11 ownership / distribution | Notices and source provenance retained, original procedural fixtures only | Owner license decision, clean distribution review; no native game assets redistributed |
| §§12–15 risks / finish line | Working vertical slice with documented incremental tests | Full requirement completion is not established |

## Addendum behavior

| Section / requirement | Present code and current status | Outstanding scope |
|---|---|---|
| 1.1 Simple defaults | XP-style Simple inspector, common animation controls present | Five-minute novice observation |
| 1.2 Advanced depth | Same scene/state, extra controls | Whole-workflow usability |
| 1.3 ecosystem-neutral artist flow | Simple naming, import review and native conversion internals present | Broad real importer fidelity |
| 2.1 Home | Recent projects, New, import, tutorials and first-movie continuation present | Fresh full Home interaction run |
| 2.2 empty scene | Empty world with editor-only grid present | Full editor/export empty-scene rerun |
| 2.3 navigation | MMB-switch and established navigation retained | Physical-device feel |
| 3.1 drop / playhead import | Source/common/native import and presence at playhead present | Cross-ecosystem acceptance |
| 3.2 spawn / scale | View-based placement and height/map calibration present | Native scale/orientation coverage |
| 3.3 common world | Multiple world objects, parenting/selection and maps present | Very large worlds/caching |
| 3.4 format coverage | GLB/common/Source/MMD/VRM/Illusion paths in recovered code | Each format's native fixtures and tools required; do not claim blanket support |
| 3.5 fidelity / dependencies | Bounded workers, material handling, diagnostics and immutable originals | Native inheritance, materials, cloth/rig fidelity |
| 4.1 direct posing / selection | Auto-key, direct rig manipulation, actual selected bones and hold-Alt reveal present | Comfort and importer-specific binding coverage |
| 4.2 hidden selection | World tree / hidden-object inspection present | Full routed regression |
| 5.1 sparse keys | Model9 independent position/rotation/scale, body and part channels | General retiming UX depth |
| 5.2 interpolation | Per-channel controls/curve runtime and gap behavior present | Owner motion preference tests |
| 5.3 IK | Direct IK and planted/contact helpers present | Native rigs and whole-body goals |
| 5.4 Motion Assist | V3 per-part/per-helper corrections, clips/copy/delete and bounded assist present | Broad full-body assistance and artistic intensity preference |
| 5.5 walks / paths | Ordinary authored movement paths and reviewed data-only reusable position presets present; see `movement_path_presets.md` | Generated locomotion, terrain foot adaptation and multi-view path inference; OPEN details retained |
| 6 camera | Explicit numeric camera controls, cuts and shared composition present; unit interpolation passes | Entire camera UI test suite |
| 7.1 one timeline | Shared frame domain, camera/body/ink/audio/world tracks present | Editable child timelines now share the parent frame/rate domain; larger projects remain |
| 7.2 expandable tracks | Hierarchical track display and components present | Larger projects and richer track operations |
| 7.3 structural clips | Independent body/root clips preserve parameter data | Ripple, stretch, loop and cross-track semantics remain incomplete |
| 7.4 gaps | Existing hold/curve bridges and independent component handling present | Do not silently redefine unresolved algorithms |
| 8.1 visibility | Persistent visibility separated from first/last presence | Parent/inherited edge cases and routed regression |
| 8.2 fades | Global300ms transition and existing project controls present | Extra per-key overrides remain OPEN |
| 9.1 Simple physics | Live/freeze, ragdolls and native helper authoring present | Native joints/cloth and real fixtures |
| 9.2 explicit recording | Simulation does not continuously author keys | Fresh full record/export regression |
| 9.3 World/Local | Distinct world/local recording paths present | All addendum scenarioD assertions |
| 9.4 capture data | Bounded tracks and recordings present | Long capture/compression policy remains suggested |
| 10.1 rendering | Unshaded editing, lighting mode controls present | Native materials and real GPU quality |
| 10.2 photorealism | High-end renderer remains preference/OPEN | No ray-tracing promise or compulsory engine rewrite |
| 11.1 packed HAS | Fresh video/body-pose packed save/cold reopen pass | Broader native full-scene gate |
| 11.2 linked assets | Fresh video/body-pose linked save/cold reopen pass | Native relinking/fault matrix |
| 11.3 independent assets | Native data is retained in HAS; no independent model/map package | Owner packaging/extension choice explicitly OPEN; question pending |
| 11.4 settings | Existing project/personal settings preserved | Import prompt policy remains tentative |
| 11.5 save safety | Atomic writes, validation and backups present; Python tests pass | Interrupted/disk-full/platform gate |
| 12.1 courses | First-movie, basic pose/draw, advanced camera and versioned lighting/export and interpolation/cuts and rig/foot-constraint and physics-recording chapters; original dummy HAS assets present | Advanced topic/subsection coverage incomplete |
| 12.2 teacher | State grading, quiet15s hint, highlights and auto progress present | Richer demonstrations and artist feedback |
| 12.3 Previous | Full checkpoints and observations present | Skip remains OPEN |
| 12.4 Continue/Fresh | Separate saved practice sessions and optional personal Save present | Forced-crash lesson-context recovery and retention |
| 13.1 autosave | Bounded background recovery workers present | Measured long-session behavior |
| 13.2 history | Journal/checkpoint references, shared cel storage and validation present | Held-art240-frame cache test now reduces builds240→2; arbitrary long/dense projects remain |
| 13.3 recovery | Fresh explicit recovery restoration passes | Linux identity47 / journal33 / normal-startup147 checks now pass; broader native/hardware crash gate remains |
| 14.1 complete scene | Shared 3D/ink/audio, imported Krita/video and particle/VFX paths | Editable nested sequences and2D shadows now present; broader layer masks/glow remain |
| 14.2 final output | Default MP41080p24, project rate/duration and PNG options present; fresh movie verified | Device/audio sync and fault coverage |
| 15 invariants | Existing interactions/source safety/limits retained; no optional AI dependency | Continuous regression and hardware acceptance |
| 16 roadmap | Recovery→baseline→new video increment follows dependency order | Does not authorize an architectural restart |
| 17 acceptance A–F | See gate table below | Not all met |
| 18 decisions | Established later Alt/MMB/autokey choices retained; remaining OPEN labels preserved | Packaging, path inference, optional visibility/Skip/settings/high-end renderer choices |
| 19–20 usable product | Incremental implementation and honest history continue | Owner's finished-animation acceptance remains |

## Explicit acceptance gates

| ID | Fresh recovered-source cloud evidence / remaining gate |
|---|---|
| CORE-01 | Original procedural room loads in actual app; native missing-texture matrix not rerun |
| CORE-02 | Unit exact0/24/48, normalized quaternion, holds and easing pass |
| CORE-03 | Actual video candidate, commit, Undo preserve old ink/camera/world and source |
| CORE-04 | Unit hidden layer pass; full routed hide/export regression not rerun |
| CORE-05 | Unit twos/boundary/end-exclusive; new video exact rational holds pass |
| CORE-06 | Full Space/arrows/focus routed regression not rerun |
| CORE-07 | Packed, linked and recovery pixels/state pass; fresh-process readers pass |
| CORE-08 | Actual decoded H.2641080p24,48frames,2seconds and exact shared-compositor render input |
| AUDIO-01 | Actual recovered AAC export decodes frame24 onset at1.0000417seconds; physical-device gate remains |
| AUDIO-02 | No-audio real movie succeeds |
| REF-01 | Actual procedural pose-library writer35 + reader6 pass |
| REF-02 | Reference-only state present; full recovered-source gate not rerun |
| SEQ-01 | Fresh editable child update over two parent backgrounds, shared instances, nested alpha, packed/linked cold reopen, split audio and ordinary startup recovery pass; bounded procedural cloud gate |
| KEY-01 | Actual green removal, original immutability, transparent/half-alpha unit checks, spill filter; app19 + reader7 |
| SAFE-01 | Full Python discovery290run/289pass/1skip, origin corpus51, raster packet17, recovery identity47/journal33/startup147 pass; full interruption/fault matrix remains |
| PERF-01 | Physical tablet/owner machine unavailable; no latency/comfort claim |
| Addendum A | Procedural subset works; five-minute novice observation absent |
| Addendum B | Owner-approved native model/map fixtures and Windows environment needed |
| Addendum C | Domain/clip code present; fresh full presence/cut/visibility routed run remains |
| Addendum D | Physics present; full native World/Local recording gate not freshly run |
| Addendum E | Existing pose/camera52+5 and new lighting/export19+5 checks pass; interpolation/cuts26+6 now pass; rig/constraint24+5 now pass; physics25+5 and first-movie79+8 now pass; deeper rig authoring/demonstrations and artist gate remain |
| Addendum F | Actual Linux automatic newest/older startup restoration passes15cases/147checks; native/GPU/physical gates remain |

Next engineering priorities are remaining tutorial chapters, richer compositing, then
broader native fidelity and long-project measurement. Keep units, headless tests,
isolated software rendering, native Windows GPU/device checks and subjective artist
acceptance distinct. New video behavior and exact reproduction are documented in
[video_import.md](video_import.md). Do not report the application fully complete.

Linux recovery was completed after the initial video checkpoint; see [linux_recovery.md](linux_recovery.md). Earlier checkpoint counts remain historical scoped results.

Editable sequences were completed after the earlier checkpoints; see [editable sequences](editable_sequences.md) for schema6, usage, limits and the portable acceptance verifier. Native packaging remains OPEN.

Simple sequence shadows now pass23writer+6cold checks with exact MP4 input; graph87/runtime12 and the complete sequence recovery suite also pass. See [sequence shadows](sequence_shadows.md).

Held-art sequence caching now passes the240-frame/two-cel source-reuse gate; see [measured cache scope](sequence_cache.md). This does not remove the existing duration or cel budgets.

Optional stroke smoothing now passes12domain/26app/4cold checks with original pressure/opacity regressions; see [scope and acceptance](stroke_smoothing.md). Physical tablet feel remains untested.

Named MP4 quality profiles now pass17app/3cold checks plus real three-profile H264/AAC decoding; see [export profiles](export_profiles.md). Scene timing/render inputs and existing Standard defaults are preserved.

Sequence masks now pass26app/10cold checks, graph106/runtime23 and the full graph3 crash/startup variant48writer/19cold/5startup. See [mask scope and evidence](sequence_masks.md); general drawing-layer masks remain separate work.

Reusable position path presets now pass23domain/41app/6cold checks and both original
path-editor regressions13+34. See [preset scope](movement_path_presets.md); generated
locomotion, terrain adaptation and path-inference details remain separate work.

A local PNG reference viewer and translucent Draw guide now pass30app/3cold checks,
including exact MP4/PNG exclusion and cold Open with reference sources unavailable.
See [viewer scope](reference_sheet.md); project-managed sheets remain separate work.

Optional kept reference PNGs now pass19storage/25app/14cold/5normal-startup/7lesson checks
through schema7, source/cache loss and actual SIGKILL. See
[project references](project_reference_sheet.md); the earlier session viewer remains
available without changing the saved format.

Reference viewed-region/size/offset alignment now passes20app checks with exact
source preservation and movie exclusion; color13 and the complete kept-reference
recovery/lesson suites also pass. See [guide alignment](reference_alignment.md).

Sparse multi-sound quantization now matches a16-case frozen full-PCM/peaks oracle
and passes real fade editing/cold storage/AAC checks. See [measured scope](sparse_audio.md).
This reduces CPU work across silent gaps; duration/dense-project memory limits remain.

The decided addendum7.3 frame3000→0 example now passes61private Model6/Model9
writer/cold/crash checks; see [late clip movement](late_clip_move.md). This does
not resolve the separate OPEN ripple/cross-track/ownership decisions.

Standalone real encoder failure/cancellation checks now run without historical
render caches; see [scope](export_failures.md). The full export fault matrix
remains separate.

Addendum visibility/gap/parent behavior now has a fresh47check procedural cloud
run, with48frame H264/AAC and sample48002 one-second cue. See
[visibility scope](visibility.md); three absent native fixtures explicitly skip.
This is additional scoped evidence for scenarioC, not the full native/artist gate.

ScenarioD now has fresh17domain+48procedural World/Local recording checks,
including actual contacts, partial/cancel/focus/stale/budget/Save behavior and
exact movie input. See [scope](physics_recording.md); three native and two VRM
fixtures explicitly skip, so the full cross-ecosystem/artist gate stays open.

Ordinary held-drawing preview now avoids repeated fullHD composition/uploads,
with one8MiB-bounded derived image and weak source ownership.50new checks,
existing34onion/161timing and scoped before/after GPU-texture benchmark pass;
see [measured preview scope](held_drawing_preview.md). The320self-contained
root-component checks pass separately;2native-plan suites explicitly skip.
Physical tablet/owner-GPU and dense/long-project memory gates remain.

Project-scoped cel PNG decode reuse now preserves independent writable Image
identities with shared lossless backing. The32repeated-PNG fixture drops tracked
load memory265.5MB to8.37MB; distinct-PNG memory is unchanged with measured
~5.4percent load-time overhead in that separate fixture.31domain+16PNG cases+
19GUI+5cold+6SIGKILL startup and existing161timing/70reference/lesson checks pass.
See [precise scope](cel_raster_reuse.md). Existing32cel limits remain; unique-art
lazy loading and owner/native/device acceptance remain open.

Directory-save raster names now derive from row indices, preventing opaque cel
IDs from escaping the folder or merging equal-ID layer rasters.30targeted
checks plus existing61+16raster and70reference/lesson checks pass; see
[reproductions and scoped verification](cel_file_paths.md). No format change.

Warm content-addressed Save now reuses verified PNG hash results within each
save, with no retained validation rasters. Original32cel benchmark drops about
2.39s to0.91s; dimension-mismatched cache members are repaired.10new cases and
existing61+16raster/70reference checks pass; see [scope](cel_save_verification.md).
