# Character parts

Use **Add → Character parts…** in the Simple workspace, or **Add character**
in Advanced. Choose a folder containing the character's MDL or prepared GLB
parts. You can also choose **Load sibling parts together…** from the Source
model import dialog. Select the parts to retain and the body reference, then
choose **Prepare character**.

Preparation uses the ordinary local converters. Nothing is added to the scene
until every selected part succeeds. A cancellation or failed part keeps the
current scene. Prepared intermediate files remain in `output/compatibility`.

The character appears as one group in World, with its parts underneath. Move
or scale that group to move all parts together. Each part keeps its original
prepared origin, skeleton, expressions and editable pose. Bones are not merged.
The six-foot option measures the chosen body's visible neutral bounds once and
applies one shared intrinsic factor to the group. **Group Scale 1** then uses
that reference; the individual parts stay at Scale 1 and keep their proportions.
Choose a genuine complete body reference rather than a hair or clothing part.
If measurement fails, the original size is retained and the status explains it.

Select the character or a part and choose **Manage parts…** in World or the
3D context menu. Check or uncheck individual parts, then apply visibility.
Frame 0 sets immediate startup visibility; later visibility keys follow the
project's fade setting. **Select** opens the part for its ordinary pose and
expression controls. **Add part…** adds another GLB or MDL at the shared origin.
**Remove…** removes that part and its attached child objects from the scene.
Undo restores the removal. An empty character root can still be managed.

## Follow the body

Following starts **Off**. In Manage parts, choose **Body to follow**, then enable
**Follow body joints** for a compatible separate part and apply the settings.
Changing this body choice does not change the six-foot height reference.
Following is a saved part setting, not an animated enable key; the visibility
checkboxes still create visibility states at the current frame.

The counts explain what will follow: matched joints have unique prepared source
identities, matching names, parents and rest frames. Unmatched or ambiguous
local poses are left independent; children still inherit their followed
parents' normal movement. Declared procedural joints and their descendants
are excluded from direct following. The supplied Junko body and dress have **50 matched joints**;
56 dress joints are unmatched and six shared procedural/descendant joints are
kept independent. This describes the prepared rigs, not original native-file
fidelity or reconstructed physics.

The body motion is combined with the part's existing authored pose. Expressions,
original pose keys, separate skeletons and the shared group scale are retained.
Following derives the displayed joint transforms without writing them into pose
keys. Repeating a frame does not accumulate movement. Turning following Off, or
Undoing it, restores the independently authored pose. The setting saves with
the project and is recomputed when reopened.

Following pauses when either rig is owned by live hair/clothes/body simulation,
a final simulation pose, an external skeleton modifier or a global-only bone
override. It resumes when that owner releases. A changed rest, source binding
or sibling hierarchy is refused rather than guessed. Multiple skeletons within
one part, unsupported procedural ownership, reflected joint transforms and
sheared local results are outside this initial mode.

Importing a complete character is one Undo step. Visibility changes are one
step too. Whole-project saves retain the group, independent assets, visibility
keys and common height factor. Both generated fixtures and the supplied six
Junko parts have been exercised through ordinary project save/reload. Packed
`.has` and fresh-process visual checks are separate from the headless check.

Limitations:

- Independent rigs remain the default. Compatible parts can opt into body
  following as described above; live following and hair/clothes simulation do
  not run together in this initial mode. Native simulation fidelity is not
  implied.
- Parts must share compatible prepared coordinates and units. HAS keeps their
  original alignment; it does not guess how unrelated models should attach.
- Clothing variants can overlap when simultaneously visible. Hide alternatives
  using Manage parts. The Junko body intentionally lacks some skin covered by
  clothing, including upper-arm areas: hiding that clothing can reveal gaps in
  the source geometry. HAS does not reconstruct missing skin.
- Folder discovery is bounded to 32 MDL/GLB files and five directory levels.
  PMX/VRM character imports continue through their existing individual route.
- Older HAS readers do not apply `character_parts.height_factor` or the opt-in
  following metadata. Do not expect backward visual compatibility: they can
  show the wrong character size or the independent pose.
- Reopening a whole saved project is supported. Repacking/importing bundles as
  additive assets with remapped object IDs has not been qualified here.

Run the focused generated-asset check from the repository root:

```powershell
python tests/verify_character_parts.py
```

It runs 22 headless checks through `run.command`, with an owned descendant Job
on Windows. It covers the actual app, GLB assembly, ordinary preparer lifecycle
using a generated-file relay, independent rigs, common scale, visibility,
Undo/Redo and directory save/reload. The relay is not a native conversion test.
`tests/character_parts_native_smoke.gd` separately exercises the ordinary native
queue when supplied an owned native-input configuration.

The following component has its own focused check:

```powershell
python tests/verify_character_parts_follow.py
python tests/verify_character_parts_follow.py --native-snapshot PATH_TO_PREPARED_PROJECT_DIRECTORY
```

The default 47 checks cover the actual controls, derived motion, authored-pose
preservation, repeated frames, Off/Undo/Redo, save/reload and conflicting-owner
refusals, including 19 malformed-metadata and cached-ownership counterexamples.
Supplying the prepared six-part Junko directory adds seven actual-rig
checks without reconverting or editing those source assets. These headless checks
do not substitute for rendered or packed fresh-process tests.

The final focused headless run passed all 54 checks. Rendered following was also
checked separately in Neon and Classic, both in Simple mode: each passed 14 writer
checks and seven checks in a fresh reader after a packed `.has` save. The dress
was rendered with the body hidden to isolate the moving sleeve. Those checks
cover visible following, Off, Undo and persistence. The typed metadata/cache
correction was rerun in both themes; the subsequent numeric-count guard was
covered by the final 54 headless checks. None of these results qualifies original
native physics or shared-skeleton reconstruction.

A reproducible steady-frame CPU measurement is available:

```powershell
python tests/verify_character_parts_follow.py --benchmark --native-snapshot PATH_TO_PREPARED_PROJECT_DIRECTORY
```

On this Windows machine, the prepared six-part scene contained seven world
objects, 617 bones and 50 followed dress joints. Two alternating Off/On pairs
used eight warmup evaluations and 60 measured evaluations per state in each
pair, giving 120 samples per state. The table measures the entire world
evaluation with a posed body; it excludes loading, user input, drawing and export.
Authored poses remained unchanged.

| Following | Mean | Median | 95th percentile | Maximum |
| --- | ---: | ---: | ---: | ---: |
| Off | 4.88 ms | 4.53 ms | 7.79 ms | 10.89 ms |
| On | 8.04 ms | 7.28 ms | 12.82 ms | 30.09 ms |

These timings are observations under the machine's background load, not an FPS
promise or a rendered-performance benchmark. The final measurement includes
the metadata and source-ownership checks.
