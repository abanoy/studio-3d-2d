# Owner review follow-up — 2026-11-21 continuation

This continues the preserved November20 notes; original observations and their qualification limits remain intact.

## Distance-dependent face visibility and saved reproduction

The owner clarifies that the face returns far away and disappears close. The earlier Amount12 UI range issue does not fully explain that behavior. Original old973 review Studio/stuff.has was staged read-only as output/owner-stuff-project-1795238638994/stuff.has,5194461bytes, SHA256 d304744dea70a05e7176b668bc10b0058b8cb4e6b1ffe5fc9fab05303da60efb; original identity stayed stable and copy readback matched. This private saved artifact contains one youmu_konpaku_school.mdl actor with empty shape_pose/shape_base and four camera keys0/24/43/48, near≈0.05,far2000,FOV60. It differs from the earlier Sakuya screenshot. Reproduce both cases where relevant and inspect near-plane clipping, skinned/morph bounds/culling, backface and depth/material behavior. No exact cause or fix is qualified. Retain both original and owned private archive; model/project contents are not authorized for Git.

## StopMotionHelper easing and smooth-key request

Owner explicitly asks to inspect https://github.com/PEAK-Incompetence/StopMotionHelper and remix its ease-in/ease-out numeric controls for neighboring keys and remembered smooth-curve behavior. Verify actual upstream behavior and license from primary code before attributing generated-key smoothing. Propose original HAS controls with editable preview, explicit Bake into keyframes and Recalculate smooths on keyframes actions. Preserve authored keys, holds, clip/frame domains, camera lens/projection, native control identities and atomic Undo/cancellation; regenerated helper keys must be distinguishable from hand edits. Upstream review is assigned and pending, not an implementation or test result.

## Prior notes (checkpoint snapshot)

# Owner review follow-up — 2026-11-20

Review used: `C:/a/Programming/cloudflare/HAS-Review-Neon-973039e-native`.
These are actual owner reports, source findings and requested changes, not a
passing native appearance, usability, timing or performance acceptance result.
Current source1084 Full remains running; no change below is adopted into it.

## Motion coverage and responsiveness

- Owner reports that not all Junko hair moves. The exact review source admits
  five imported owners `[8,17,18,26,27]` while retaining49 native motion rules.
  Increasing fan strength does not enable the inactive owners. The prepared
  twelve-owner expansion is unrun and is a stepping stone, not all-hair support.
- Owner reports Hair & clothes ON feels laggy. A single system sample saw the
  owner review at73.12% of one CPU core and43% of one3D GPU engine, while a private
  verifier process also ran. This is not a solver/FPS measurement and does not
  establish contention as the cause. Startup arguments named Mima; the currently
  loaded scene was not observed. Retain those limits in any later report.
- Owner reports Try a local blow starts very slowly, then eventually works.
  Measure preparation/import latency separately from first visible motion and
  steady-state simulation cost. The temporary preview has preparation/import and
  two post-draw warmup frames; do not label the full reported delay intentional.
- Source review found repeated full-model checks/restores on the120Hz five-owner
  route. Qualify a phased benchmark and a safe preview batching optimization
  before wider activation. Preserve the exact numerical tick rate, source/binding
  validation, original authored data, independent actors and Off/Record behavior.
- The exact9b007 retained report has49 unique owners using the same supported
  0x31 flag family and two existing coefficient/prefix families. Investigate all49
  authenticated owners and full69-bone closure; do not invent new physics or treat
  an unrun prototype as visible coverage.

## Multiple hair-part and joint selection

Owner says they cannot freely drag/select multiple hair joints in the setup
context, including Ctrl-click, Shift selection or their combination.

The existing part list is single-select. Include in setup maintains a separate
batch-inclusion set, and a temporary wind group has another independent check.
The viewport also reserves Ctrl for camera controls. Existing batch checkmarks do
not meet the requested normal multi-selection gestures.

Implement familiar selection behavior for the relevant lists: plain click sets
focus/selection, Ctrl-click toggles a row, Shift-click selects an anchored range,
and Ctrl+Shift extends it. Retain an explicit focused part for individual refine
controls, with a visible selection count and clear batch actions. Keep selection,
inclusion in the authored setup and temporary wind participation distinct and
understandable. Deselecting a wind group must not remove its joints.

Add a clear viewport selection gesture/mode for a marquee over joints or parts,
with additive/toggle behavior and accurate highlights. Preserve normal camera
navigation, especially Ctrl slow movement with LMB+WASD. A drag inside the setup
list must not be silently repurposed as viewport camera navigation. Verify actual
input events, empty/malformed selections, changed actor, filtered lists, pending
worker completion and independent per-part attachments/weights.

## Expressions and character shortcuts

Owner cannot find the facial expression controls and requests an icon-based
radial dial for Face/expressions, body posing/movement and other character
parameters.

Verified existing route in this review: select the model/head, choose Pose, then
the right inspector's Keys and helpers → Shapes / expressions. That button is
currently hidden when the selected asset has no retained shape/expression data.
The separate Open Mima head expressions.bat example is present. A hair-only
selection may therefore offer no expression control; the current scene/selection
was not observed, so this is a possible explanation, not an attributed user error.

Improve discoverability: keep the Face/expressions entry findable, with an
actionable explanation when the selected part has no facial controls. Preserve
separate head/body/hair model selection and the existing expression editor.

Add a Character tools radial menu with icons and readable labels. Initial actions
should open existing Face/expressions, body pose/movement, hair/clothes setup and
available appearance/parameter editors. Expose it through a visible Character
tools button and a configurable shortcut. Decide any default key against the
actual shortcut registry; do not steal camera movement, drawing or OS shortcuts.
Use capability-aware disabled actions with a reason, keyboard navigation and
Escape/click-away cancellation. Merely opening or cancelling the dial must not
modify pose, keys, physics, history or the project. Follow Neon/Classic scaling,
docking/floating and small-window behavior, and preserve current middle-click
tools until a reviewed replacement is qualified.

Owner additionally requests radial item ON/OFF and material hiding, as in GMod.
Provide a Show/hide item action for the selected object/accessory, plus a separate
Materials submenu with individual material visibility switches. Material hiding
means hiding the corresponding rendered surfaces; it is not merely disabling a
texture or replacing its color. Preserve original material resources and use
per-instance state so another actor using the same asset is unaffected. Identify
materials with readable original labels and handle duplicate/unnamed materials
unambiguously. Support restore/show-all, Undo/Redo and portable project persistence.
Keep object/bodygroup visibility, per-material visibility and physics activation
separate. Preview, render, selection/highlights and framing must agree with the
visible surfaces, including parented objects and live/recorded motion. Any new
saved capability must be rejected clearly by older unsupported readers rather
than silently losing the hidden-material state.

## Qualification and preservation

Owner tried Motion feeling and reports the right/lively end looks robotic instead
of neighboring joints helping the movement; the left/gentle end does practically
nothing. Record this as actual negative qualitative feedback, not a passing
native artist/usability result. Current source adds bounded anticipation/settling
to keyed controls; strength0 follows authored controls and does not coordinate
adjacent joints. Investigate coordinated body motion using relevant neighboring
joints/kinematic constraints while keeping main authored keys and deliberate
holds exact, avoiding unrelated fingers/accessories, and providing visible
control over assistance strength/scope. Do not claim that existing per-track
overshoot already meets this request or that timing alone proves natural motion.

Owner explicitly requests that, with Hair & clothes ON, moving the character
causes appropriate hair/loose-cloth response. Feed supported live model/root and
pose movement into secondary simulation, including translation/turning inertia,
delayed response and damped settling without requiring a fan. Preserve attachment
points, authored pose and ongoing model manipulation. Check current nonrecorded
SecondaryLive's initial_world/initial_pose behavior and pose-edit freeze paths;
do not pin the character to its activation transform or silently stop its preview
when the intended supported move begins. Batch optimization must not reuse a
stale fixed baseline across a moved actor; freeze fresh per-tick/frame inputs and
retain source/binding/scale guards. Verify start/stop/reversal, parented movement,
seek/discontinuity, different uniform scales, repeated On/Off restoring authored
state, fan composition, Record/Undo and exported/cold-open motion. Current
all49/scalar/queued preview prototypes are not an actual qualification of this
interactive response.

Owner requests RMB+scroll for the camera lens zoom parameter. In the3D camera
view, holding RMB while scrolling should adjust the temporary camera's field of
view/lens, keeping position/orientation unchanged. Use current projection/range
validation and display a clear lens/FOV readout; Save camera key must capture this
value through the existing camera-key format. Preserve ordinary movement/dolly,
RMB look, release/cursor restoration, drawing/context menus, Ctrl slow fly and
high-resolution/repeated wheel handling. Verify the gesture through actual root
input delivery, finite/clamped zoom extremes, explicit key replacement/Undo,
animated sampling and preview/export/cold-open agreement. Merely navigating must
not silently insert camera keys.

Camera timeline owner findings: cannot select or drag the displayed camera key,
and expects double-click at an empty position to add a key or on an existing key
to remove it. Exact old review TimelineView only draws Camera diamonds; its input
handlers retime model/audio/cels and otherwise scrub the playhead. Add proper
Camera key hit-testing, visible selection, drag-to-retime and the requested
double-click toggle. Retiming must preserve every camera/projection/interpolation
field, handle occupied/end-boundary frames explicitly, cancel with Escape, and
produce one atomic Undo step. The current app silently refuses deleting its only
camera key; preserve a valid document while giving a clear actionable reason,
rather than leaving the marker apparently stuck. Existing current shortcut is K
or Save camera key; replacing an existing key asks before overwriting.

Owner also reports Ctrl+wheel cannot zoom the timeline. A Ctrl/Shift-wheel handler
already exists in TimelineView and emits navigation_requested, so investigate the
whole app event route, children/scroll containers, signal connections and correct
pointer anchoring instead of adding another unconnected handler. Exercise actual
root-window input delivery over ruler, Camera row and other lanes at different
Neon/Classic scales/dock sizes. Preserve ordinary scroll, Shift horizontal pan,
text editing, keyboard remaps and camera navigation. Distinguish horizontal time
zoom from resizing the Timeline dock, and keep the existing controls available.

Owner's3440×1440 screenshot shows the rotation rings around the selected left
foot are too small to grab comfortably. Add a distinct Handle size preference,
independent of interface zoom, with a useful large-screen default/range and wider
screen-space drag tolerance. Scale ring visuals, move handles and camera-facing
rotation ring coherently; keep picking and highlighted active handle consistent,
including edge-on/intersecting rings. Preserve axis direction, local/world/view
rotation semantics, pose results, snap, cancellation and Undo. Validate different
viewport sizes/DPI/interface scales and floating docks, and do not change the
model's world scale or render output to enlarge editor handles. Screenshot source
is private codex-clipboard-4ff9c34e-191e-4182-8208-10f40ac6186e.png.

Owner screenshots additionally show a cramped Shapes at this frame window, a
short shape list, substantial unused vertical space, and no practical resize
control. Make it resizable and remember useful size/placement without forcing it
back during refresh. Let the shape list and relevant controls consume added space,
use sensible minimum bounds and compact action layout, and preserve readability
at100% and other interface scales in both themes/floating dock arrangements.

Owner reports Summer Sakuya's face disappears after setting brow happy to12.
Located actual review import: Workshop1298211035/sakuya_izayoi.gma, selected
models/npc/sakuya_izayoi_summer_npc.mdl, request SHA
be9ca7158c902df67a32ebb3fc9e54cceec7b18bdf70dbbabad518fc1cd3fe3c.
The retained native report declares brows_left_happy and brows_right_happy min0,
max1. Current UI exposes raw normalized amounts from-100 to100, directly applied;
12 therefore means1200%, not12%. This range mismatch is demonstrated by source;
the exact disappearing-face render is still awaiting independent reproduction.
Use a clear normal/percentage display and native normal bounds in Simple, retain
explicit Advanced overdrive for intentional extreme/negative weights, and never
silently rewrite existing saved extreme values. Verify this exact channel at0,
0.12,1 and the previously accepted12, Undo/reset/all-base restoration, unaffected
channels/parts, native morph conversion and preview/export/cold persistence. The
worker advised Undo and raw0..1 as the temporary existing-build workaround.
Screenshot originals remain private at the two supplied Temp clipboard PNG paths;
no screenshot or model artwork is authorized for source publication.

Owner requests physics OFF by default when importing a model. Apply this to new
model instances: body Physics and Hair & clothes start off, while imported joint,
rigid-body, constraint and spring declarations remain available for explicit
activation. Existing project save/open behavior and authored settings stay intact;
the current implementation freezes live simulation when saving and does not
serialize a live-ON flag. Do not invent such a flag as part of this default change.
Do not use the new default as a substitute for fixing lag when a user enables
simulation. Update any old auto-on expectation with this explicit owner request
recorded; preserve the previous result as historical evidence. Verify new imports,
explicit activation, Off restoration and saved-project restoration independently.

Owner also reports failures importing gm_construct and ttt_tinyspaceship. Read-only
review outputs identified the exact selected inputs as installed gm_construct.bsp
and Workshop member maps/ttt_tiny_spaceship_v3.bsp. The former fails because the
converter rejects an outer spotlight angle of90 degrees (six actual map lights).
The latter fails on a light_environment whose _light is -1 -1 -1 -1; its entity
lump has105 ordinary/spot/environment lights before flags/style filtering. Retest
actual maps after correcting supported boundary handling and making optional
unrepresentable/excess entity lights report clear omissions while retaining raw
entities and the global64-light budget. Do not claim a missing-file cause, bypass
geometry/resource checks or label the maps fixed before native load/cold tests.

Owner additionally requests a loading progress bar. Apply this to model/project
loading and the local-blow preparation flow where supported: show feedback as
soon as loading starts, a useful current stage, and real measured progress when
the worker/byte/step total is known. Use an indeterminate bar when it is not;
never invent an elapsed-time percentage. Keep the interface repainting, preserve
existing cancellation/error/source protections, and clear the loading display
reliably on success, failure, cancellation or stale completion. Match Neon and
Classic themes. Measure preparation latency separately from steady preview FPS.

Stage new work only in owned isolated copies once the running Full closes. Keep
the old review and current source1084 unchanged during that run. Record actual
failures and measured costs, then verify input/Undo/Off, packed/linked cold-open
and preview/movie behavior as appropriate. Publish source and compact findings,
including these owner observations, before cleaning any eligible generated work.
All acceptance statuses remain unchanged until their own evidence is complete.


## Manual lights and current Lit mode

Owner asks how to add a light. Verified exact old973 source: viewport menu offers Unshaded/Lit/Studio light; Lit enables imported scene lighting with built-in studio directional/ambient disabled. This build has no Add light control. The current workaround is Studio light for built-in illumination. Add explicit placeable point, spot and directional lights with editable color/intensity/shadows and suitable range/cone controls. Reuse validated camera/world transforms and existing lighting/export; preserve source materials, Undo/Redo and portable document capabilities. Expose meaningful World/radial controls, light selection icons and clear saved behavior; test multiple scenes/native models, Lit/Studio interaction, shadow and preview/export/cold parity. This is an owner-requested addition, not an implemented feature or a requirement-score change.
