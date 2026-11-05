# Installed particle browser — development UI

The development app now has a small choose/load/place/time workflow for supported
installed Source particle systems. It uses the same canonical effect descriptor,
world instances, project clock, `.has` packing and renderer as particle_scenes.md.
The normal installed Studio has not been updated with this increment.

## Using it

1. Open **Installed**, choose **Particle effects**, then a location or Search all.
2. Select a `.pcf` and **Import selected**. The Effects panel lists its named
   systems, with basic-operator candidates first. Unavailable systems remain
   visible with a refusal reason; Studio does not silently import part of them.
3. Choose a candidate and **Load selected**. Materials/textures are checked now;
   a compatible operator list alone does not promise that a system can load.
4. Review the first/end frames, name, position and size, then **Add effect**.
   **Place in current view** fills the position fields with a point three metres
   ahead of the current camera. It never writes camera keys.
5. Select an existing effect under **World → Effects**, or use **Scene effects…**
   in Installed. Change its fields and **Apply changes**; **Remove** and **Undo**
   work through the ordinary world history. **Go to effect** moves the playhead.

The end frame is excluded. The instance is static in space in this first UI;
timing/visibility crop deterministic prepared animation. Longer clip ranges do
not loop or create new births beyond the prepared duration. Changing preparation
timing/variation requires loading again. Advanced shows a fixed variation seed;
an existing instance retains its prepared seed. This is not a new animated root
keyframe channel, physics capture mode or dynamic attachment system.

The panel is modeless. Its primary actions stay in a fixed footer, and frame and
position fields use compact rows so they remain usable when reopened. Simple
controls preserve untouched stored coordinates/tiny scales even when the display
rounds them. New size edits use aligned hundredths. Camera keys, drawing cels,
ordinary models and saved native asset hashes remain independent.

## Adapter and storage boundaries

Discovery extends the existing read-only folder/GMA/VPK index behind an explicit
opt-in flag; its old model/map API defaults remain unchanged. Particle loading
uses an installed-host preflight, SFM paths and contextual mount order. Recognized
SFM content now works with SFM alone in development; GMod content still requires
GMod. See sfm_standalone.md for validation and scope.
Saved dependency mount overrides and additional content paths now reach the
particle worker. Selected content has priority. Particles inside compressed
legacy BIN providers still need further work.

Parsing/preparation runs in a bounded local worker with atomic structured results,
one exact system name, fixed seed and explicit duration. Close, timeout, New/Open
or project-rate changes prevent stale results from silently entering a new scene.
Adding remains an explicit action after preparation. Imported canonical JSON/PNG
are copied into the managed cache. Linked saves externalize derived cached assets
beside the HAS file; they do not depend on an expendable worker folder. Complete
original game files and native scripts are never bundled into a project.

The deliberately supported subset is still narrow: childless, simple additive
camera-facing sprites with supported initialization/age curves/constant gravity,
static VTF7.2 textures and an own deterministic random stream. See
source_particles.md for exact limits. Full Source operator/shader/random fidelity,
child systems, trails, animated sheets, forces and moving control points remain
unsupported. No Lua or game is launched. No new dependency is installed.

An actual SFM explosion file contains41 systems:2 pass the basic operator check.
The tested vfire Workshop file contains101:1 passes it. These are eligibility
counts, not complete imported packs. The two actual rendered test systems are
`Explosions_MA_Flash_1` and `vFire_Glow_Tiny`, with their resolved installed textures.
User assets retain their original rights and stay private local test data.

Direct viewport picking/gizmos for effects, animated transform tracks, attach/
amount controls, richer source fidelity, provenance UI and performance profiling
remain unfinished. Use the World entry or panel instance list in this increment.

## Verification scope

The UI was first built in an isolated source copy while the earlier canonical
scene backend completed its full regression. That backend plus the fill visibility
correction passed the real full verifier and separate HAS wrapper with128 private
graphics receipts. Its full-pass claim applies to that earlier frozen snapshot.

The final isolated UI passes28 actual-app and5 cold-reader checks with two clean
private desktop receipts. Real routed button events select/load/add both native
families, Apply placement/size/visibility/name, Undo, Remove and reopen. A fresh
reader loads packed HAS after only owned input/import/worker folders move aside,
reproduces exact complete room/effect/ink/camera pixels and retains editable
instances. Linked headers externalize all four effect assets to a sidecar. An
actual1080p24/48-frame MP4 exports through the normal app. Untouched field
precision, footer visibility, main-window clicks while the panel is open and
closing followed by Advanced toggling are checked.

Four new Python browser tests and14 existing content-index tests pass. Real
worker tests enumerate41/101 native systems, reproduce the earlier prepared
descriptor/PNG hashes, refuse disabled dependency mounts, resolve explicit extra
content and leave original PCF/GMA hashes/times unchanged. Stage evidence is
recorded by `output/particle-ui-development.json` and its local test reports.

The test-driver failure on initial embedded-window clicks was isolated with a
minimal button probe: embedded child input must enter the parent viewport with
the child offset. The production button was not bypassed with a signal emit.
Tests then caught/corrected size-range offset, a stale scroll request after moving
actions into the footer, and a cold-test signal that did not toggle a CheckButton.
Failed runs remain separate. No pixel, lifecycle, data or production tolerance was
weakened to obtain a pass. Accepted panel screenshots were visually inspected.

The tested12-file UI change is now in the development checkout. Its eight-group
affected review completed with every command exiting0 on unchanged functional
inputs: browser unit/native-data/UI, existing Source browser, workspace, world,
HAS and fill. Seven new private graphical receipts confirm closed jobs/desktops
and no foreground child observed. Evidence is in
`output/particle-browser-review/1793675809924028900` and
`output/particle-browser-review.json`. This is an affected review, not a fresh
full-verifier result for the UI source or an approved normal installation.
An additional focused follow-up now passes29 app+5 cold checks. Routed typing of
`b e` into the embedded panel name field changes its text while leaving playback
and the drawing tool unchanged. This verifies those keys through engine input;
physical artist use and comprehensive keyboard/IME acceptance remain open.
No physical desktop input/focus,
artist-quality, tablet or clean-machine guarantee follows from these tests.
