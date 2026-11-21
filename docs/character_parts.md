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

Importing a complete character is one Undo step. Visibility changes are one
step too. Whole-project saves retain the group, independent assets, visibility
keys and common height factor. Both generated fixtures and the supplied six
Junko parts have been exercised through ordinary project save/reload. Packed
`.has` and fresh-process visual checks are separate from the headless check.

Limitations:

- This is a static assembly feature. Posing the body does not automatically
  drive the separate clothing or hair skeletons. Physics and pose following
  need their own explicit setup; native simulation fidelity is not implied.
- Parts must share compatible prepared coordinates and units. HAS keeps their
  original alignment; it does not guess how unrelated models should attach.
- Clothing variants can overlap when simultaneously visible. Hide alternatives
  using Manage parts. The Junko body intentionally lacks some skin covered by
  clothing, including upper-arm areas: hiding that clothing can reveal gaps in
  the source geometry. HAS does not reconstruct missing skin.
- Folder discovery is bounded to 32 MDL/GLB files and five directory levels.
  PMX/VRM character imports continue through their existing individual route.
- Older HAS readers do not apply `character_parts.height_factor`. Do not expect
  backward visual compatibility: they can show the wrong character size.
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
