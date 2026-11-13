# HAS — consolidated master reference for resuming work

**Updated November 13, 2026. The owner explicitly resumed work; the goal is ACTIVE.**

This is the single reading document for the requests, corrections, proposals,
current software/test state, protected inputs and next steps from this chat.
The contents are included below; the detailed source notes are retained for
provenance, not required merely to reconstruct the requested behavior.

The owner has now said "you may continue." Continue independent authorized work,
starting with concrete hair/cloth and control bugs. This does not grant owner
participation time or authorize replacing installed tools/Studio. Earlier pause
and documentation-only entries below are historical observations. The owner
clarified that pausing work does **not** mean shutting down the PC; no shutdown
command was sent.

## 1. Owner instructions and working boundaries

- Continue Hybrid Animation Studio, preserving the core workflow: external 3D
  world, animated camera, independent editable 2D drawings, synchronized sound,
  portable HAS projects and playable movie export.
- The owner is busy and requested **no further test/review questions or repeated
  interruptions**. After permission to resume, continue independent authorized
  work. Actual artist/novice/learner/device participation remains deferred until
  the owner grants it. Do not invent observations or substitute automation.
- Preserve the installed Studio, original assets/projects, Steam content, shared
  tools, owner recovery and concurrent work. New tool installation, installed-app
  replacement, deployment, publishing and private-art redistribution need their
  own authorization. Previously approved temporary SourceIO use remains approved.
- All automated graphics use `run.command()` on **private Windows desktops**.
  Verify isolation receipts; never fall back to visible automation or take focus
  from the owner's desktop. No owner-visible app launch occurred for the notes.
- Use isolated session-owned checkouts. Save every completed increment's source,
  tests, findings and compact evidence to the authorized repository, push without
  force, fetch/verify the remote, then clean only finished disposable outputs.
  Retain pending private deliverables; do not upload their art to Git.
- Preserve required/optional/suggested/OPEN distinctions. New roadmap ideas do
  not silently become mandatory ledger items. Earlier successful scoped tests
  do not close newly reported bugs or establish a full aggregate pass.

Repository: `https://github.com/abanoy/studio-3d-2d`, branch `main`.
This compilation follows documentation checkpoint
`979d7fad91e868ae0a54b8e46fbb59ccabaae731`; fetch latest main rather than treating
that checkpoint as a permanent head. Application baseline before this resume:
`02631f916ef28c146d36b684aff0b26f32cf013c`.

## 2. Earlier requests: what changed and what is still unobserved

| Area | Owner request/report | Recorded state before the pause |
| --- | --- | --- |
| Scene space | The 3D scene was too small; its bottom divider could not enlarge it enough. | Timeline compression/scrolling and divider resizing implemented and software-tested. Keep scene space usable. |
| Interface size | A Windows-like 100% rather than an automatically oversized UI; retain larger zoom as an option. | Actual desktop-pixel 100% and persistent 125/150/175% choices implemented. Owner said sizing was good. |
| World clipping | World felt stuck; widening its dock left the tree/buttons narrow and model names clipped. | Tree/buttons now fill dock width, including reset/reload; owner explicitly confirmed clipping fixed. Do not repeatedly ask them to recheck it without a new failure. |
| Docks | Freely move, resize, tab, dock and detach panels, as in Krita/Kdenlive; split two docks across the top and allow further arrangements. | Recursive horizontal/vertical splits, tabs, individual floating windows and persistence implemented/tested. Owner found earlier docking visually rough; latest nested version has not received owner review. |
| Camera speed | Hold Ctrl during LMB/WASD flight to slow down; release Ctrl to resume normal speed during the same gesture. | Software checks pass. Recorded speeds: Ctrl 0.75, normal 3, Shift 8 units/s. |
| Cursor return | After camera navigation, return to the previous cursor location instead of the center. | Requested restore coordinates and gesture handling tested; physical owner-desktop cursor return remains unobserved. |
| Fan motion | Loose hair should respond forward/backward and continue to flutter under airflow; stronger wind should have an evident effect. | Aim at hair, selected-model targeting, scale-aware positioning, air-reach feedback and deterministic gust/crossflow implemented/tested. Naturalness and newest owner-reported hair defects remain open. |

Docking limits still documented: only World, Properties and Timeline participate
in this dock tree; floating windows contain one panel each. Docking all other
tools, detaching a whole compound group, explicit docking-target icons, direct
tab-strip reordering and redocking via the OS title bar are not established
features. Do not silently make those extra possibilities new requirements.

Camera behavior also records preservation of the original pointer position across
multiple held camera buttons, release/Escape restoration and suppression of a
warp during app switching. These are software observations, not physical approval.

Fan physics is bounded airflow, not fluid simulation or a full mesh-cloth solver.
No motion should be manufactured from a fan that is off or whose stream misses
the loose parts. The earlier owner reproduction had Hips Y about **-80.360916**
while the fan remained near its initial height; all 12 chains missed its stream
at strengths 3/12/50. Preserve that pose/recovery. Do not silently reset the model
to make a test look better. Aim/reposition through ordinary controls as needed.

## 3. Hair, clothes and accessories: current unresolved feedback

These are owner reports and requested refinements, **not diagnosed or fixed**
by the documentation work.

**Resumed software update:** item1 below now has a verified restoration fix;
focused8, full fan63 and import-physics41 checks (five native models) pass.
The unchanged focused test fails4/8 with the old controller. Ordinary body Freeze
and explicit Record remain intact, including cancellation of pending hair setup.
See [evidence](benchmarks/hair_disable_restoration_2026-11-12.json). Remaining
items and human/device/aggregate acceptance are still open.

**Back hair update:** an explicit reviewed existing-chain path now passes26
native checks and29checks with the existing ribbon setup preserved. Original
skin/weights/posed pixels remain unchanged;3shared regions/1369weighted vertices
are disclosed before Apply. See [evidence](benchmarks/back_hair_existing_joints_2026-11-12.json).
Direct scene-click selection and Simple's automatic reviewed-chain choice now
pass 20 unit and 25 routed interaction checks, with 30 pristine/33 ribbon-composed
native checks and the original helper/patch suites preserved. A click guesses
from current joint-transformed region bounds; the list corrects that approximate
guess. Manual mode correction, navigation and cancellation remain available.
See [selection evidence](benchmarks/secondary_part_picking_2026-11-12.json).
**Multiple-part setup update:** one precise focused part plus visible **Include
in setup** checks now retain separate reviewed requests and apply one complete
candidate as one Undo edit. Shared native-chain regions are linked/disclosed;
invalid plans stay marked rather than silently disappear. Full-precision control
transport and a persistent per-request eligibility flag prevent stale Apply.
Final 26 CPU/5 state/34 app, 38 combined native, 30 single/33 composition,
20+31 picker and unchanged 39/14/59/35 helper checks pass; source freeze covers
193 runtime/backend files. [Evidence](benchmarks/secondary_batch_setup_2026-11-12.json).
Local-blow preview, per-item wind exclusions and further refinement remain open;
setup membership is distinct from persistent simulation/blow membership.

1. **Deformation remains after switching Hair & Cloth off.** A configured joint
   deforms correctly while enabled, but the deformation stays after disabling
   the feature. Restore the appropriate authored/current-frame pose when removing
   live simulation offsets. Preserve manual posing, configured joints and
   explicitly recorded animation. This is not a request to delete keys or reset
   the entire model, nor to change body Physics' separate freeze behavior.
2. **Some items cannot be added to joints.** Specific case: **Bikini Reimu's
   Back hair**. Reproduce the actual selected part, inferred item, available
   joints and resulting assignment before choosing a fix. Existing ribbon/helper
   tests do not prove this part works.
3. **Keep single-item refinement.** Best-effort automatic selection/assignment
   is welcome, with easy correction rather than forcing its guess.
4. **Try a local blow should help choose affected parts.** The user wants to see
   which items respond, then deselect/uncheck parts that should stay still.
   Make per-item inclusion/exclusion clear. Distinguish the current selection
   being edited from persistent membership in the simulation/blow effect.
5. **Click a visible 3D part to infer its item.** Try to select the hair/accessory
   component the user likely meant and make the result inspectable/correctable.
6. **Select multiple items.** Support handling more than one item in the relevant
   picker/list. Exact gestures and their relationship to blow inclusion remain
   design work; particular modifier keys were not prescribed.
7. **Refine Simple mode.** The owner sees the idea working but finds the normal
   interaction jarring. Preserve the useful Advanced workflow, which they say
   works fine, while simplifying selection, assignment, preview and correction.

On resume, validate single/multiple assignments, Back hair, excluded parts,
toggle-off restoration from non-rest poses and recorded takes, repeated cycles,
re-enabling without accumulated offsets, Undo/Redo, cancel and saved/reopened
configuration. Preserve other live physics and originals. Do not ask the busy
owner to repeat tests without permission.

## 4. Rotation controls

**Resumed software update:** signed ring dragging and inner-frame overlay bounds
are fixed in software.131checks pass versus27failures with the two old sources;
the same24camera/axis/quadrant gestures and actual overlay clipping are checked.
See [evidence](benchmarks/rotation_gizmo_fix_2026-11-12.json). Camera-facing
relative rotation is still pending; owner visual/physical approval is unobserved.

**Camera-relative ring now implemented:** a pale outer ring follows the camera
for root/bone rotation in Local/World modes, with lock/snap/history/cancel and
normal saved-key behavior.309writer+4cold-reader checks and original45/41/41
pose/world cases pass. See [view-ring evidence](benchmarks/view_rotation_ring_2026-11-12.json).
These supersede the earlier pending status; human/device review remains unobserved.

- **Direction bug:** the RGB rotation interaction feels reversed, affecting at
  least the **top ring**. The exact axis/view/cause is not yet reproduced. Correct
  the affected direction; do not blindly invert all axes.
- **Camera-facing relative ring:** add a ring that always faces the camera and
  rotates left/right relative to the current view. The recorded interpretation
  is clockwise/counterclockwise rotation about the view axis, alongside the RGB
  rings. The owner cites SMH/SFM as references; exact gestures were not audited.
- **Focused-panel bounds bug:** the supplied screenshot shows the rotation rings
  outside the white camera frame in the gray area on the left. This is distinct
  from the sign bug. Reproduce positioning/drawing and hit testing; make controls
  respect the intended focused view and agree with displayed geometry.

The preceding bullets preserve the original reports. Check different camera
positions, local/world modes, left/right drags, angle
boundaries, panel resizing/aspect changes, existing axis controls, Undo/Redo and
normal pose/key persistence. Current resumed fixes and their actual tests are
recorded above; this original feedback is not a statement that they remain unrun.

## 5. Scene setup, camera framing and output size

**Resumed software update:** [Scene setup](scene_view.md) now fills the available
scene area, with optional Camera focus, Frame and 3×3 guides. Personal view
preferences preserve Draw zoom/pan and leave camera keys, native output and
project state unchanged. Native virtual coordinates keep outside-frame selection
and handles aligned; Focus retains clipping. Exact native capture and fresh
recovery readback are verified. Current scoped proof is 12,830 headless checks
across 144 configurations and 102 app checks, including zero guide changes outside
the frame. Nine regression groups pass on the same 188 runtime-file hashes,
including actual Miku45, native selection41/edit41 across Miku/Reimu/Scout,
picker20+31, rotation309+4 and drawing/bounds/recovery. The checks also caught and
fixed cached rings after deselection and valid clicks discarded during a pure
inspector translation. See [evidence](benchmarks/scene_view_2026-11-12.json).
No full aggregate, artist or performance approval follows from these counts.

**Capture teardown update:** closing during native capture/recovery is now
covered by 58 lifecycle checks. The shipped nested-wait path leaked six
coroutine states and crashed cleanup in the matched regression. A first
owner-bound signal fix passed 50 checks but failed the unchanged helper test
when its caller immediately freed Studio after capture. A locally retained
RefCounted notification now keeps the emitter alive, drains close/cancel waits,
returns no image for closed captures and suppresses obsolete thumbnails.
Current lifecycle58, SceneView102/12,830 and the unchanged helper39/native14/
multi59/patch35 pass. [Evidence](benchmarks/native_readback_lifecycle_2026-11-12.json).
The broader full aggregate is still pending; intermediate failures remain saved.

- Owner prefers **one main camera view**. Multi-camera layouts may be optional;
  they are not the desired ordinary workflow or a claimed implemented feature.
- Scene setup should use the whole available view. The white output-shaped
  rectangle/focused camera panel is useful for composing a shot, camera positions
  and output presets, but should be optional rather than constrain ordinary
  scene arrangement to a smaller area.
- Suggestion: an optional **3 by 3 / nine-cell rule-of-thirds grid**. Keep guides
  editor-only, absent from final artwork/output.
- Keep **1920 by 1080 as the default**, with requested choices for specific
  resolutions, presets such as **4K**, and custom sizes. Framing/aspect should
  make the selected output understandable.
- **Timeline-changing resolution** is an exploratory Advanced idea, described
  by the owner as a wild possibility. It is not an agreed design or acceptance
  gate. Distinguish actual output dimensions, animated framing/crop and per-shot
  choices before deciding how timeline/export should behave.

Existing output-size documentation already describes Advanced Movie encoder
choices for 1080p/720p/540p, with saved settings and independent drawing coordinates.
**4K, arbitrary sizes and other aspects remain unsupported in that documented
profile.** Audit these controls and native-canvas limits instead of duplicating
them or claiming that simple upscaling creates new drawing detail. Existing
render attempts capture dimensions before rendering; dynamic dimensions require
explicit new design.

Preserve camera keys, temporary scene navigation, independent cels and preview/
export agreement when changing the viewport or output pipeline.

## 6. Lighting and rendering direction

### Desired appearance and controls

The requested range is **flat, simple, GMod-like, MMD-like and RTX-like** lighting.
Earlier wording also included **Raycasting lighting**, possibly Ray-MMD/Raycast;
that interpretation is not yet confirmed. The owner is unsure whether SFM has a
default lighting style; do not invent one. Styles involve material/shader response
as well as lamps and settings. Current Unshaded/Lit/Studio modes do not establish
all of these future styles or full native fidelity.

**Central priority: shared illumination on the map, character models and props.**
The owner especially likes bounced/reflected illumination reaching items/models,
instead of lighting only map geometry. A lit red wall tinting white clothing is
a useful intended result. Adding bloom or only a map lightmap is insufficient.
Include hair/accessories and material response. Preserve deliberate Unshaded
behavior. Separate objects receiving indirect light from contributing their own
light to further bounces; the latter is a more demanding dynamic quality goal.

### Owner references and recorded research, as of November 12

- [Advanced Light Entities](https://steamcommunity.com/workshop/filedetails/?id=493751477):
  editable shadowed/inexpensive point, projected and spot lights, colors,
  projection textures and shadow-update controls. A useful editing reference,
  not a GI renderer. Source's shadow-texture restrictions need not be copied.
- [Ray-MMD](https://github.com/ray-cast/ray-mmd): DirectX 9 shader-based PBR,
  soft shadows, environment lighting and screen-space effects. Demonstrates a
  polished non-RTX appearance reference, not HAS compatibility.
- [GMod RTX Remixed](https://github.com/Xenthio/garrys-mod-rtx-remixed): the owner
  supplied this as the shared-illumination example. Its README lists PBR conversion,
  model skinning and Remix integration. It now marks the project deprecated and
  points to [SourcePT](https://github.com/sambow23/SourcePT), which describes
  submitting Source rendering through a wrapper to OpenRemix. No installation,
  fidelity audit or hardware compatibility test was performed.
- NVIDIA's own Remix requirements specify RTX; OpenRemix describes vendor-agnostic
  path tracing. Vendor-agnostic is not proof of support for arbitrary GPUs without
  ray-tracing capability. Exact Windows boundaries were not established here.

### Non-RTX feasibility and current application limits

Godot 4.6 provides baked-light probes for moving objects and approximate real-time
GI techniques. Thus characters can receive indirect environment illumination
without an RTX card. SDFGI's dynamic objects receive GI but do not act as dynamic
contributors; VoxelGI offers different dynamic behavior and approximation limits.
Screen-space effects need fallbacks for off-screen/occluded information. Do not
promise full path-traced parity, a quality percentage, frame rate or 4K speed
without actual representative tests.

HAS currently selects **GL Compatibility**. Godot's VoxelGI, SDFGI, SSIL, SSR and
volumetric fog require Forward+. A higher-quality optional rendering path needs
real engineering; it is not an already-working lighting checkbox. Lightmap baking
also needs an authoring pipeline. No compulsory engine rewrite/new dependency was
authorized by recording these ideas. Recheck current primary docs on resume.

### Render time is allowed to exceed playback time

The owner emphasizes **final video rendering**: expensive lighting can be laggy
in live editing but can spend longer per output frame. Keep intended video timing
independent of wall-clock rendering speed. Explore economical editing preview
and higher-quality final rendering, with a way to inspect the intended final look.
Preserve fixed animation/physics sampling, camera timing, synchronized sound,
independent 2D layers and the PNG sequence contract. Extra render time does not
remove memory limits or automatically supply a missing renderer.

Existing Movie quality settings change **compression**, keeping rendered PNG
inputs identical. They do not add GI or improve light-bounce accuracy. Scene
lighting quality, output dimensions and encoder compression are separate choices.

## 7. Model Discovery: complete requested behavior

### One place, clearly labelled sources

The latest owner clarification is **one Discovery tab covering Local and Online**,
with proper labels. This supersedes the assistant's earlier three-main-entry
sketch. Local cards identify their filesystem location; online cards identify the
website/source. Exact source-switch/filter layout remains design work. Preserve
offline local browsing; online discovery is explicit and optional.

Clicking an online title/thumbnail opens its original listing in the **default
browser**. This is not an automatic download, Steam subscription, account login
or import. Available local models can be previewed and explicitly added to the
scene. A source website is not the same thing as a local directory or compatibility.

### Research a broad international source catalogue

**Resumed research update:** the saved
[catalogue](discovery_source_catalogue_2026-11-12.md) and
[structured metadata](../data/discovery_sources.json) now cover 12 researched
directory entries across Japanese, Chinese, Russian and international sources,
plus the requested but challenge-blocked SFMLab link. These are research records,
not working HAS search adapters. Every live-interface test remains false;
authentication, uncertain metadata and failed access are recorded explicitly.
Provider integration, multilingual query behavior, feed pagination and the
Discovery UI remain future implementation work.

On resume, actively research model-directory resources across the internet,
including **non-English communities**. SFMLabs, BowlRoll and Steam Workshop are
examples, not the search boundary. Build a saved provider catalogue documenting
source URLs, languages, model categories/formats, search support, thumbnail/
metadata availability and retrieval prerequisites, with dated primary evidence.
Distinguish discovered sites from working/tested search adapters. Do not promise
an exhaustive global index or universal site search support before researching it.

### Browse first, search when a query is entered

- Empty-query online discovery initially offers **about 100 diverse listings
  combined across providers**. These are listings, not downloaded/converted models.
- Favor discoverability across sources, creators, subjects and formats where
  metadata permits. The exact balance is not yet prescribed.
- Bottom scrolling appends **roughly another 100**. Preserve scroll position and
  loaded-card order. Track provider cursors/exhaustion, remove duplicate source
  IDs/URLs and preserve distinct models/editions that merely share titles.
- The top search bar activates **targeted keyword search**. Relevance takes
  priority there; diversity should not displace the requested model.
- Query/filter changes reset the relevant pagination and reject obsolete
  responses. Do not mix old searches or discovery batches into new results.

### Separate, combinable filters

Provide **website/source** and **model type/ecosystem** filters independently,
with MMD, SFM, VRM and GMod as the owner's examples. Each can have an All choice;
either can work alone or with the other and the query. Apply selected filters
to discovery, search and later batches. Use metadata rather than assuming a
website determines model compatibility; some models support multiple ecosystems.

### Local query expansion and language/format variations

Owner example: `Hatsune Miku` can produce **Hatsune Miku, Hatsune, Miku,
Miku Hatsune**, plus other useful aliases. Consider the terms **Miku/Hatsune**
independent of order. Full/reordered names and strong aliases are the strongest
matches; individual words broaden recall. Respect each site's actual keyword
semantics rather than universally requiring one literal phrase.

Bundle useful variants locally, without compulsory cloud translation or AI:
known aliases, original-script names, romanizations, spellings, capitalization,
character width, spacing, punctuation, hyphens/underscores and word order.
For example, Hatsune Miku and `初音ミク` can be explicitly known aliases. Preserve
original titles/queries and do not invent proper-name translations from a guess.

Query syntax, escaping/encoding and case sensitivity are provider-specific.
Bound variant searches and merge their results; putting every alias in one
query may cause a site to require every word and return fewer results. Preserve
case-sensitive provider IDs, URLs, asset paths and credentials; these query
transformations do not apply to passwords. No universal translation/search
success was claimed or tested.

### Badges and prerequisite explanations

- Owner labels: **Downloadable, Preview, Password**. They can overlap.
- Base them on source evidence. Keep **Unknown/unverified** when fetching or
  metadata fails; that does not prove preview-only or unavailable access.
- Define image preview versus interactive 3D or preview-only access. A thumbnail
  does not prove an actual 3D model preview is available.
- A download-page link is different from successfully retrieving a compatible
  file. Password means a known access condition, not that HAS knows the password.
- Track when availability was checked. Keep source attribution and access details.
- Contextual notices can offer **Do not show this again**, scoped to that notice;
  do not suppress unrelated conversion errors or hide uncertain access.
- Owner example: if GMod is not detected and a listing comes from its Workshop,
  explain the relevant game/Steam retrieval requirement. Verify the actual
  provider rule before using categorical wording. This is not a universal ban
  on native files without installed GMod/SFM: complete standalone inputs can
  remain usable. Missing installation and missing dependency are distinct.

### Preview-on-selection, without committing scene changes

Selecting a local/cached model should try to show it in a preview, as the owner
likes in SFM. Some native formats require conversion. Use a separate asynchronous,
bounded and cancellable job; debounce rapid selection, cancel obsolete work,
reuse validated caches and reject stale results. Preserve originals and current
scene/project state. **Add/Load remains explicit.**

Bad or unsupported files should produce understandable per-item failures and
allow another selection. Check missing dependencies, corrupt files, time/memory
bounds, cancellation, cache invalidation and rapid changes. Existing workers are
a foundation, not proof this UI exists or an absolute guarantee against all
malformed-file/GPU-driver failures. Online listings still open source pages;
do not automatically fetch their model binaries for preview.

## 8. Assistant contributions: proposals, not blanket-approved requirements

The owner invited a remix and accepted the Discovery/Local/Online organizing
idea. That did not approve every optional extra. Keep these labelled proposals:

1. **Saved shortlist inside Discovery**, possibly a filter, not another required
   main tab. Star listing links/local models and retain attribution locally.
2. **Locate downloaded file** bridge: after visiting the source and retrieving
   a model, manually associate its file/folder with a saved listing, preview it,
   then Add to scene. No guessed associations or background Downloads scan.
3. **Also searched…** disclosure with actual aliases/variants, exact-name mode
   and the ability to remove unwanted expansions.
4. **Cards explain the next action.** Website/type/access on the card, detailed
   requirements/readiness in an optional Details area. Distinguish offered access
   from a local file actually inspected for use.
5. **One calm preview.** Prepare only the selected local model. Keep the previous
   good preview while loading, clearly labelled as previous, with progress/Cancel.
   Do not convert 100 models to fill a thumbnail grid.
6. **Useful partial results.** An unavailable source gets a small retry/status
   message while other results stay available. Dismissible hints can remain
   inspectable without repeated disruptive prompts.

Example proposed journey: Discovery -> search/filter -> save an online listing ->
open its source -> retrieve normally -> Locate downloaded file -> local preview ->
explicit Add to scene. Keep the original online title/thumbnail browser action.

## 9. Optional later extension: sounds

The owner suggests reusing Discovery for **sounds**, explicitly **not the main
focus**. Models come first. Later research suitable sound-directory websites,
save their provider records, and reuse labelled Local/Online listings, search
and source links. Define sound-specific metadata/filters when actually taking
it up; do not assume model sites all offer audio. No sound-site research,
downloads, playback or implementation has occurred. This is not a new required
acceptance gate or a prerequisite for the model browser.

## 10. Current verification and incomplete acceptance

### Latest software correction — November 13

A later suffix passed fill, gap fill, expanded fill, connection fill, palette and
drawing history, then the drawing-selection writer printed35/0 but crashed
during native shutdown. Its cold reader and nine later wrappers were not run.
Preserve that failure; it is not a successful aggregate.

The pending scene picker retained one camera Transform3D while awaiting the
global frame signal. Explicit owned request receivers now disconnect and clear
on close. New28checks pass with clean private exits; exactold2904source prints
four passes but repeats0xC0000005. Final source also passes unchanged selection41,
world edit41, SceneView12830+102 and drawing selection12+35+3 with the original
pixel, persistence and movie predicates. Initial harness type errors and a
rejected bound-callback candidate(28/5) remain recorded. The regression is now
in the default suite. [Fix/evidence](selection_readback_shutdown_2026-11-13.md).
Continue nine later wrappers, phase1 Wind integration and a final full suite;
existing human/device/native/clean-install gates remain open.

Formal ledger remains **55/62 acceptance groups verified** and **52/54 required
implementation groups implemented**. Seven open acceptance IDs:
`IMPORT-02`, `IMPORT-03`, `ACCEPT-A`, `ACCEPT-B`, `ACCEPT-E`, `ACCEPT-TABLET`,
`ACCEPT-INSTALL`. Required implementation groups IMPORT-02/03 remain partial
because supported native appearance still needs actual comparison. Counts are
not a single release-readiness percentage. C/D/F remain closed.

### Resumed QA and preserved experiments — November 12

The full canonical is **still unpassed**. Three exact85fa attempts are retained:
one Python pack launch failure (unchanged31+60 focused replay passes), an
interrupted replay, and a dedicated hidden run that passed the core/contact/
workspace/helper/shape/body/lighting groups before live-appearance32/4 failed.
Its932 functional hashes and revision remained identical before/after.

That last failure sampled the native viewport while Scene Setup rendered through
its separate view. Test-only fresh, non-evaluating readbacks now pass live38,
camera-range60 and manual foot-contact74 checks with their original pixel/error
assertions. Contact animation44/editor34 also pass with fresh diagnostic images.
The selection reference first needed the displayed projection/extent (67/40 to
67/1), then exposed one CPU-baked versus GPU-skinned hair-edge coverage difference.
Separate frozen native skeletons pass67/0, retaining all assertions, the
zero-outside-one-pixel bound and independent CPU-baked vertices/bounds. Deliberate
wrong transform, omitted hair, stale pose, wrong alpha and old projection fail.
The old failures remain preserved; exact internal engine arithmetic is unproven.
See [QA evidence](benchmarks/resumed_canonical_qa_2026-11-12.json) and
[selection diagnosis](selection_raster_reference_2026-11-12.md). Product renderer/
picker code was not changed by these test corrections. Run the full suite again
from the new published checkpoint; scoped checks do not substitute for it.

Source-only [experiment checkpoints](../experiments/README.md) preserve the local
wind prototype (94 headless; later830 isolated GPU checks below), static Source appearance worker
(21 CPU, actual conversion/app/render unrun), and the historical first review
checker. The current checker is now in `tools/verify_owner_review.py` and
`tests/owner_review_replay.gd`: all six existing packages pass **129 checks** in
fresh private processes against committed-source review `c6782d2`. Normal
recovery/Home startup, ordinary Python unpack/loading, saved metadata, native
Setup/Focus pixels, strict cache containment and unchanged source/package/harness
hashes are verified. The first failed checker attempt remains preserved: its
`--script` route suppressed Home and its cache test mishandled Windows separators.
The corrected checker uses ordinary scene startup and resolved containment;
application source and the review snapshot were unchanged. See
[review evidence](benchmarks/owner_review_six_projects_2026-11-12.json) and
[replay contract](owner_review_validation.md). This is runnable-review evidence,
not artist approval, a clean installation or six new movies.

The wind and Source appearance overlays are **not installed in the normal app**.
Wind's pending-helper integration and permanent inclusion settings,
and Source runtime/animated skin/bodygroup switching remain separate work.
Do not claim native jiggle/assembly fidelity or accept the features from CPU
tests alone. Their plans, exact source and limitations are recoverable from Git.

An individual-file cleanup plan covers only16,875 Git-reconstructible source/cache
files (224,835,913bytes) in13older readback snapshots. All104 unique source-tree
files and142parent evidence files stay in place; both previous canonical copies
and every unlisted future copy are excluded. No deletion has occurred at this
checkpoint. Publish/fetch/verify this plan first, then independently revalidate
every file/path/recipe and delete only exact listed files. Old snapshots become
intentionally sparse; reconstruct from recorded Git blobs plus retained overlays.
The compressed machine-readable plan is in the benchmark directory; no private
asset payload is in it. Keep owner reviews, recovery, originals and pending work.

**Later verified outcome:** the exact plan was executed after remote verification.
All **16,875 files / 224,835,913 bytes** were removed; no directories were removed.
The runner and root independently rechecked all104 retained source files and142
parent evidence files. All planned paths are absent and the journal matches the
ordered plan. Both protected canonical copies and all unlisted/future copies stay
excluded. Process checks establish no observed session/test use, with five exact
reviewed protected-helper exceptions; universal ownership/CWD/open-handle freedom
is not claimed. [Actual receipt](benchmarks/readback_reconstructible_cleanup_result_2026-11-12.json)
and [reviewed runner source](../experiments/readback_cleanup/README.md).

### Later canonical contract correction — November 12

The next full run at `4fee0a9` also remains **failed/incomplete**. All934 functional
file hashes and HEAD stayed exact. Body editing, lighting, live hair appearance,
camera range, foot contacts and contact animation/editor/clipboard passed before
one old contact-physics expectation failed (48checks/1failure). It expected Hair
OFF to author a freeze and add an Undo entry, contradicting the owner's requested
restoration behavior already implemented in the app.

An exact-old-assert private diagnostic showed all91 native bone poses restored
exactly and full world/data/history/redo/dirty unchanged after OFF. The old Undo
then removed the earlier fan addition. The corrected test asserts exact authored
restoration, no phantom edit, and real prior fan Undo/Redo, preserving every other
contact/body/recording/HAS/movie check and limit. Ordinary51 and component53 checks
pass with actual48-frame1080p24H264 movies. No product code changed. See
[contract evidence](benchmarks/contact_hair_off_contract_2026-11-12.json).
Continue the unrun suffix independently before another final full run; scoped
replays never turn this failed aggregate into a pass.

Wind's first actual graphical attempt reached only its procedural case:56checks,
one failed fixture-adoption assertion. Native, lifecycle and primary jobs did not
run. Separate-child preservation is unproven because the fixture did not establish
a distinct peer; diagnose the exact append error before changing the harness.
The runtime and originals stayed exact. The strengthened hidden-mesh, nonzero
excluded-pose and both-simulator oracles remain saved separately. [First failed
GPU receipt](benchmarks/wind_review_first_gpu_2026-11-12.json). The feature remains
unshipped; do not infer a production failure or a complete graphical pass.

**Later Wind outcome:** the corrected fixture uses valid draft frame0, adopts
the peer through normal Add model and then validates explicit world parenting,
with distinct IDs/roots and logged errors. All six private cases now pass:
procedural60, VRM045, VRM145, derived Back hair47, lifecycle544 and primary89 —
**830 checks, zero failures**. Runtime/source/native/root hashes remain exact;
all six desktop receipts are clean. Two real48-frame1080p PNG exports exclude
the candidate at frame1; no new movie is claimed. Source-only
`experiments/local_wind_review/production_port_candidate_20261112` contains the
exact tested overlay, retrieval chain and normal-regression/UI review plan.
No main-app port occurred. Pending helper-before-Apply preview, permanent choices,
physical/human observations and normal regressions stay separate. [Actual matrix](benchmarks/wind_review_gpu_matrix_2026-11-12.json).

**Remaining-scope continuation:** a separate2c scoped run passed19 wrappers
through layers, then caught an old central onion summary. The actual fresh onion
wrapper passed37 checks/movie, but wrote only its per-case result. The reporting
fix publishes identical UTF8 per-case/central bytes after all unchanged assertions;
a fresh37-check replay passes. No app code changed. All16 later report channels
are statically correct but their wrappers remain unrun. Continue those16, then
run the final full aggregate; neither this suffix nor prior partial runs count
as a complete aggregate. [Onion provenance evidence](benchmarks/onion_fresh_summary_2026-11-12.json).

### What the last application fix actually established

The upright Scout fixture exposed **6.97 mm** final joint separation, failing
the unchanged **5 mm** contact assertion. Eight position iterations still failed
at about 6.88 mm. Restoring speculative contact distance from 0.1 to **0.02 m**
passed a disposable comparison and two independent 76-check full contact runs,
with Scout about **2.60 mm**. Preserve 120 Hz, four position iterations, ten default
velocity iterations, 2 mm penetration slop, CCD and existing collision rules.
No sideways Scout workaround, extra runtime pair exclusion or relaxed assertion.

Additional scoped checks passed: normal physics 56 with three native rigs;
props 35; recording 17 unit + 62 app. Movies, audio timing and private desktop
receipts are recorded. Windows metadata containment also has a verified separator
fix; preserve all containment, ownership and link checks.

### The full default suite is still unpassed

The last run from `02631f916ef28c146d36b684aff0b26f32cf013c` was intentionally
stopped at the owner's pause request. It passed through core editing/recovery,
native MMD posing, physics/contact/props/recording, workspace resize/docking/nested
layouts, fan flutter, shortcuts/camera, helpers/morphs, shapes/studies, expressions,
MMD groups, height review and map calibration. It was interrupted during the
subsequent **body curves** work. Later phases have prior scoped passes, not a
new complete aggregate. Preserve that distinction.

Log: `output/canonical-contact002-20261111.log` in the November 11 checkout.
The exact suite process tree was stopped; owner applications were not targeted.
The prior complete attempt failed at contacts; neither attempt is a full pass.

On resume from stable fixed source, stage exact prerequisites and run:

```powershell
$env:HYBRID_HECATIA_KRA=(Resolve-Path output/owner-fixtures/hecatia.kra).Path
$env:HYBRID_NATIVE_INPUTS='C:\a\dump'
$env:HYBRID_FFMPEG='C:\Program Files\ffmpeg\bin\ffmpeg.exe'
Remove-Item Env:HYBRID_FAN_PROJECT -ErrorAction SilentlyContinue
python -u tests/verify.py *> output/acceptance-resumed.log
```

Require exit 0 and a freshly written aggregate, including final movie metadata
and decoded audio checks. Fix actual failures without weakening or skipping
assertions. Keep failure/skip/unrun evidence. Do not start this command while paused.

### Historical reader backups are unavailable

The owner said the four November 4 source ZIPs are **dead**. Do not ask for them
again, fabricate substitutes or change their expected hashes. Historical names:
`2026-11-04-015322-mp3-ogg-audio`, `2026-11-04-035230-joint-sound-review`,
`2026-11-04-134345-media-review`, `2026-11-04-145211-project-duration`, each with
`development-source.zip`. Separate checksum-bound historical readers remain
unpassed. Current-candidate Git inventory support does not certify those readers.
Older plans telling the worker to request these files or prompt owner reviews
are superseded by the owner's later instructions.

### Supplied SFM extra features: independent coverage work

The owner reminded us on November 12 that the other supplied SFM models have
additional features. Review the broader archive corpus and test representative
controls actually present in those sources, rather than treating Scout as
complete SFM coverage. Candidate areas include facial/flex controls,
bodygroups/skins, material variants, accessories and extra joints; inventory
which are truly present before claiming support. Default conversion success
alone does not certify editable extra features. This independent feature review
is in progress; it does not depend on asking the busy owner to enumerate files
again or provide new observations.

**Inventory update:** [the feature map](sfm_extra_features_2026-11-12.md) and
[metadata receipt](benchmarks/sfm_extra_feature_inventory_2026-11-12.json) now
separate the historical 82 default conversions / 71 distinct MDL hashes from
extra-feature acceptance. All 22 supplied archives were freshly hash/size checked
under `C:\a\dump\New folder`, unchanged before/after. The older 20-archive /
66-definition totals remain historical. Retained Mima head metadata establishes
hair/hat blank bodygroups, 82 controllers, 156 descriptors, 143 prepared facial
targets and 229 bones, but only one skin family. Keiki Tools, Shinki wings and
separate Junko/clothing components provide grounded next cases. The bridge
currently exports default bodygroup/skin choices to GLB; editable choices,
native assembly and sequence/procedural support need separate implementation
and validation. Exact multi-skin positives and broader native rule counts now
have a fresh [native metadata inventory](sfm_native_feature_inventory_2026-11-12.md):
all 82 actual MDL49 files parse, representing 71 distinct definitions. There are
28 files/27 distinct definitions with differing skin families and 55 files/46
distinct definitions declaring native JIGGLE bones. Nitori's glove has three
skins; Junko v25 main has 16, and its hair has 49 JIGGLE declarations. Keiki Tools
is a positive nonfacial control. All 3,203 rules in this supplied corpus are
single FETCH1 with declared 0..1 controls; moving native sequences are not a
positive case here (all animation headers are one-frame). Portable extraction/
parser reproduction also passes 82/82 with exact native records and unchanged
original archives. Switching skins/bodygroups, native jiggle fidelity, assembly
and rendered appearance remain separate work; these metadata checks do not
establish their implementation or acceptance.

The native inventory also records a proposed first appearance increment: choose
validated skins/bodygroups before importing a new object, beginning with Nitori's
glove and Keiki's chisels. Bake that selected appearance into a derived GLB and
report the actual indices; preserve old embedded projects. This does not implement
later runtime/animated variant switching or justify replacing an edited object
whose shape/helper identities must survive. Full geometry/material dependencies
and actual rendered/persistence tests are required beyond the MDL-only inventory.

**Resource preparation now completed:** exact296 native resources /181,460,484
bytes were staged read-only from the two RARs, with all originals unchanged.
Thirty-four CPU controls pass. Keiki's4VMTs/16 observed texture references resolve;
Nitori's6VMTs have25/28 resolved references, with three references to one missing
`materials/hairbump.vtf`. All basic bridge base textures resolve, but native
bump/Phong/environment/warp/glow fidelity is unproven; no substitute or installed
fallback was used. [Actual staging/closure report](sfm_native_resource_staging_2026-11-12.md).
Source-only staging, allowlists, requests and an unrun serial conversion driver
are preserved under `experiments/source_appearance/native_resources`. Its21 CPU
controls pass after independent review of bind/rest and stage-membership guards.
Prepare a fresh schema2 input lock at the next stable HEAD before any conversion;
the old schema1 preflight is historical and deliberately refuses current code.
Selected skin/bodygroup exports, rendered comparisons and app adoption remain unaccepted; the first baseline observation follows.

**First actual converter attempt:** the no-request Nitori baseline emitted an
836,088-byte GLB (1mesh/2textures/66bones), but the original private wrapper
returned2 because no window/child-desktop placement was confirmed for the
background route. Accepted0/14;13 cases remain unrun. All protected inputs and
source stayed exact; owned processes exited. [Failure receipt](benchmarks/sfm_first_conversion_isolation_2026-11-12.json).
The separate `background_route_candidate_20261113` preserves an explicit headless
bootstrap and independent Python/Blender WinAPI desktop/process/source/import
attestations. Its44 CPU controls pass, with no forged private flags or acceptance
of old exit2. Actual private attestation/rerun is unrun. Review and prepare a fresh
schema3 lock at the next stable remote checkpoint before granting its exclusive
conversion lease. Native material/render/app acceptance remains incomplete.

### Actual external observations still needed, only when participation is granted

- **Native appearance:** supported originals versus imports, materials/UVs/rigs/
  expressions/lighting and useful posing. Exact cold self-replay is not approval.
- **Novice A:** a real new user's timed VRM/pose/save/reopen/export exercise plus
  the environment/camera/independent drawing/sound story. Record help, elapsed
  time, Explorer drop and confusing controls.
- **Learner E:** actual tutorial clarity, a genuine 10–30 second stuck interval,
  quiet hint, Previous, Continue/Start Fresh, completion and required assistance.
- **Tablet/audio:** real device/driver/display/audio setup, pressure/eraser/comfort,
  measured input-to-visible delay and listening after preview/export/seek.
- **Clean offline Windows:** an approved clean Windows 10/11 PC/VM with approved
  prerequisites, networking disconnected, original import, HAS save/reopen and
  playable MP4 plus missing-tool behavior. This configured PC is not that result.
- Physical cursor return, latest docking polish and fan naturalness remain
  unobserved. No more participation prompts until the owner grants time.

## 11. Inputs, approved tools and protected private deliverables

### Working and review folders

| Path | Meaning / protection |
| --- | --- |
| `C:\a\Programming\cloudflare\has-acceptance-session-20261111` | Current retained isolated checkout; generated output/bytecode may be dirty. Do not reset blindly. |
| `C:\a\Programming\cloudflare\has-acceptance-session-20261110` | Older retained checkout with private owner work/reproduction inputs. |
| November 10 `output\owner-review\Studio\output\recovery` | **Actual owner recovery. Never treat as disposable test output.** |
| November 10 `output\fan-native-probe\input` | Owned copy of actual fan/pose reproduction. |
| November 11 `output\owner-review` | Earlier separate runnable review; preserve. |
| November 11 `output\owner-review-current` | Runnable later review, source from `bd09769150ede7a47590b6024928bc050bc52c9d`; **does not yet contain the final 0.02 m physics setting**. |
| November 11 `output\owner-review-verified` | Four hash-matched project copies only; **not a runnable new Studio snapshot**. |
| November 11 `output\owner-feedback-20261112\viewport-camera-frame.png` | Private screenshot evidence; do not upload/delete as disposable. |

Existing runnable review launchers: `Open Avatar.bat`, `Open Flatgrass.bat`,
`Open Street.bat`, `Open Reimu helpers.bat` where provided, and `Start review.bat`.
They are owner-operated, not permission for visible automation. Preserve profiles
and recovery when preparing a newer snapshot. Do not overwrite an existing Studio;
the snapshot builder supports a new owned output target and refuses replacement.

The preserved framing screenshot is 60,256 bytes with SHA256
`255c5b3fc02ef2765e8fab5ffd32c68498b3ccf3ed778ee21c2814995c38434d`.
It shows the frame/right-side scene and rotation rings far outside its left edge.
Earlier attached screenshots showed the cramped scene/timeline and the narrow
World tree/buttons within a wider dock; their original Temp paths may no longer
persist. No screenshot/art was pushed to Git.

### Native originals and important fixture identities

Owner-provided locations below are recorded context, not a fresh inventory
performed for this consolidation. Read originals only; stage owned copies.

- `C:\a\Programming\HAS\hecatia.kra`: exact **19-layer** original, SHA256
  `fff3599293023f41f05eb27c9d51d2af45d01493b8618c5da51067f3449ff758`.
  The 18-layer `C:\a\dump\hecatia.kra~` is different and must not substitute.
- `C:\a\dump\AvatarSample_A.vrm` and `AvatarSample_Avrm0.vrm`.
- `C:\a\tools\mmd64\UserFile\Model\Miku_Hatsune.pmd` (126-bone fixture).
- Street PMX under `C:\a\tools\mmd64\UserFile\Model\environments pack 03 (FFA)\street01_android`,
  with the five exact atlases: `atlas03_street_d.png`, `atlas02_street_d.png`,
  `atlas03_props_d.png`, `atlas02_props_d.png`, `atlas09_props_d.png`.
- `C:\a\tools\touhou_reimu_bikini.gma`; actual player/ragdoll imports and selected
  ribbon helper evidence exist, but do not close the new Back hair report.
- `C:\a\tools\temp.gma`: Transit map, not automatically a universally compatible
  map; current documented 64-static-light limit refuses that case.
- `C:\a\tools\716412401162652161_legacy.bin` and
  `C:\a\tools\883003003936997315_legacy.bin`; first supplied legacy input contains
  Hakurei Shrine. Preserve native reports instead of guessing all package contents.
- Owner authorized read-only content inspection under
  `C:\Program Files (x86)\Steam\steamapps\common`. A used complete BSP is
  `GarrysMod\garrysmod\maps\gm_flatgrass.bsp`. Do not launch/alter Steam installs.
- Also supplied: `C:\a\tools\mmd64\UserFile\Model\` and `C:\a\tools\models\`.
- Reproducible Mima facial-head fixture uses `C:\a\dump\New folder\mima.rar`,
  SHA256 `b0a4b19afc4cf8d8a17351848e11cf4738fa0a7436d58699a66a4c4be501a50a`,
  through `tests/prepare_mima_fixture.py`; 115 checksum-bound resources. Retain
  the prepared head and native project aliases while tests need them.
- Scout's native fixture must retain its deliberate **90-degree X** root
  orientation. Do not turn it sideways to pass physics. Current independent
  fixture plans/provenance replace dead machine-specific audit pointers.

Original archive names supplied under `C:\Users\noble\Downloads\New folder`
(locations may have changed; preserve originals and confirm on resume):

```text
SFM-Reisen_Udongein_3a9qsw1.rar
SFM-Ran_Yakumo.rar
SFM-Reimu_Hakurei_gYGjX5u.rar
SFM-Young_Ran_Yakumo_3YWxQCa.rar
Takane_and_Nitori_tanktop.rar
Junko_Tamo_sfm.zip
Junko_Tamo_sfm_v25.zip
Bunny_suit_Patchi.rar
Kanako_Yasaka_DVebPRD.zip
SFM-Reimu_Hakurei_V2.rar
SFM-Chen.rar
Patchouli_knowledge_fix.rar
Patchouli_knowledge.rar
Hijiri_Byakuren.rar
Hijiri_v2.rar
chimata_and_momoyo.rar
Keiki.rar
shinki.rar
mima.rar
momiji_inubashiri.rar
Cirno_Mister_Orzo_v2.1_edit.rar
aa.rar
```

### Approved tools and latest disposable cleanup

Reuse Godot **4.6 stable standard**, not .NET, at
`C:\a\tools\Godot\Godot_v4.6-stable_win64.exe`; Python under
`C:\Program Files\Python313`; FFmpeg under `C:\Program Files\ffmpeg\bin`.
The temporary SourceIO runtime was explicitly approved; pinned revision
`fe24260b97ac03b899d9b5d4f0fd7b34772f3647` is staged in
`output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647`.
Its archive SHA256 is
`cd44e1d053ac853c5d1628da9faa27a594337ebacb3587744dfa5d60758623de`.
Reuse/recreate the already approved exact disposable runtime without treating
that as authorization to install or replace shared tools.

After remote verification of the physics fix, only the disposable
`output/physics-solver-probe/Studio` copy was removed: **1,409 files / 349,432,050
bytes**. Parent JSON/logs/source receipt remain. Previous scoped cleanup is
recorded in benchmarks. Do not redo deletion or generalize it to other Studio,
output, native fixture, review or recovery directories.

After remote verification of `12f5d612f2c748b5ed4dc46878291251ffb836de`, only
`output/rotation-counterfactual/1794515417597023600/Studio` was removed:
**1,284 files / 17,967,128 bytes**. Its parent failed/fixed comparison, logs and
receipts remain, with compact evidence in Git. No private originals were used
by that counterfactual. Other reviews, recovery and native fixtures are retained.

After remote re-verification of `e82580da9fe8d12ea29afc1f3e1780035605daa2`,
**576 disposable interior PNG frames / 23,442,386 bytes** were removed from
16 explicitly bound completed hair/helper render attempts. All encoded movies,
compared/representative frames, HAS files, WAVs, inputs, metadata, failure logs
and desktop receipts remain. Current SceneView outputs and owner reviews/
recovery were excluded. Exact attempts/frame numbers and evidence commits are
in [the cleanup receipt](benchmarks/generated_frame_cleanup_2026-11-12.json).
Those old attempt folders intentionally no longer contain complete PNG sequences;
fresh wrappers create new ones. Use the retained movies or rerun the saved source.

After remote verification of `0af5d417d00a9053181e2c6b72ba4a07e729c33a`, the
duplicate native stage `output/sfm-extra-native-inventory/1794519206301446900/stage`
was removed: **82 files / 62,843,920 bytes**. All 82 hashes were checked against
the identical private definitions retained at
`output/sfm-extra-native-inventory/portable-root-639301165838922272/stage` for
ongoing SFM cases. Original archives, complete/failed metadata, logs and staging
manifests remain. [Receipt](benchmarks/sfm_native_definition_cleanup_2026-11-12.json).

## 12. Order of work after an explicit resume

1. Fetch latest repository state and inspect local status; preserve private and
   concurrent work. Read the governing documents. This master is the consolidated
   chat reference, not a replacement for the full specification/addendum.
2. Prioritize concrete owner bugs: Hair & Cloth restoration/Back hair assignment,
   Simple selection/refinement, ring direction and focused-panel bounds. Preserve
   old confirmed fixes. Implement requested camera-relative controls and framing
   changes in small reviewable increments with relevant validation.
3. Keep exploratory resolution animation, optional sounds and assistant additions
   separate. Research/phase Discovery and lighting requirements deliberately;
   broad future roadmap work must not hide a newly failing ordinary control.
4. Run the full default suite from stable final source and complete its media/
   audio checks. Preserve actual failures/skips; do not present scoped composition
   or an interrupted run as an aggregate pass.
5. Prepare a separate current runnable review with existing private projects,
   without replacing installations, earlier reviews or owner recovery. Do not
   issue participation prompts while the owner remains unavailable.
   The review builder now accepts `--revision` to freeze a verified commit
   without including concurrent working edits; seven CPU cases and an exact
   1,282-file repository probe pass. This tool evidence alone is not a new
   runnable-review or application-startup result.
6. Update compact evidence, history and stable ledger; commit, push and verify
   remote contents before exact safe cleanup. All completed source/progress must
   be retrievable from Git, not PC-only caches.
7. Keep actual external observations pending until granted. Do not claim full
   completion or mark the goal complete without satisfying its actual conditions.
   At assignment end, remove a verified session checkout only when no pending
   work or unbacked private deliverable remains; retain/report protected data.

## 13. Governing documents and detailed provenance

The master includes the requests/status inline; these remain the exact technical
authorities, full exercises and historical receipts:

- `AGENTS.md`, `CODEX_CUSTOM_ANIMATION_STUDIO_SPEC.md`, root `LLM.md` and
  [overriding voice addendum](design/HAS_2026-10-29_Voice_Design_Addendum_for_Codex.md).
- Windows goal packet: `C:\a\Programming\HAS\START_HERE.md` and
  `WINDOWS_CODEX_GOAL.md`. Its SESSION_STATE is a snapshot, not current main.
- [Current ledger](completion_checklist.json), [history](progress_memo.md),
  [Windows handoff](local_acceptance_handoff.md),
  [actual remaining exercises](windows_acceptance_followup.md),
  [native profiles](native_profile_acceptance_review.md),
  [fixture rebuilding](windows_aggregate_fixtures.md) and
  [native-worker runtime](sourceio_worker_runtime.md).
- Original detailed feedback: [hair/accessories](hair_accessories_feedback_2026-11-12.md),
  [rotation](rotation_gizmo_feedback_2026-11-12.md),
  [viewport](viewport_framing_feedback_2026-11-12.md),
  [lighting](lighting_feedback_2026-11-12.md),
  [Discovery requirements](model_browser_feedback_2026-11-12.md) and
  [assistant concept](model_browser_concept_2026-11-12.md).
- [November 11 pickup](NEXT_SESSION_PLAN_2026-11-11.md) and
  [November 10 historical pickup](NEXT_SESSION_PLAN_2026-11-10.md). Later owner
  pause/no-prompt/dead-backup instructions override stale next-step prose there.
- Current evidence: [pause receipt](benchmarks/windows_pause_2026-11-11.json),
  [contact fix](benchmarks/windows_contact_distance_fix_2026-11-11.json),
  [metadata fix](benchmarks/windows_metadata_separator_fix_2026-11-11.json),
  [remaining scoped checks](benchmarks/motion_remaining_scope_2026-11-11.json),
  and [review source](benchmarks/current_review_ready_2026-11-11.json).

The initial compilation was documentation only; the owner subsequently resumed
work. This reference does not certify acceptance or current input availability,
grant participation time, or authorize replacing installations or private-art
redistribution. Update actual results incrementally as resumed work is verified.
