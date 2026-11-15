# Isolated Windows acceptance fixtures — 2026-11-10

The original historical `hecatia.kra` is now supplied at
`C:/a/Programming/HAS/hecatia.kra`. Its SHA256 is
`fff3599293023f41f05eb27c9d51d2af45d01493b8618c5da51067f3449ff758`.
It has the required 19 layers; the `C:/a/dump/hecatia.kra~` backup has 18 layers
and a different hash. Keep both originals unchanged. The historical verifier
now accepts `HYBRID_HECATIA_KRA` pointing to an owned exact copy and checks that
identity before running. All existing layer/hold/pixel/native-cancellation
assertions remain. Fresh 32 writer and 5 reader checks pass on the supplied file.

The aggregate next exposed mandatory native-pose inputs hardcoded to an old
installed Studio output directory. That cache is not a prerequisite. Native
fixture consumers now use `tests/native_fixture_root.py`: default to this
checkout's `output`, or explicitly select an existing directory with
`HYBRID_NATIVE_FIXTURES`. The resolver selects test data; it does not change
assertions or write to the old installation. Historical compatibility archives
and oracles are separate inputs and are not silently substituted.

For the supplied raw VRMs, `HYBRID_NATIVE_INPUTS=C:/a/dump` selects the original
input directory in both Python and GDScript native test resolution. Actual VRM
workers still validate and convert native bytes. A GLB is never relabelled VRM.

## Rebuild from originals in a new session

Reuse existing approved Godot 4.6 stable standard, Python, FFmpeg, Blender and
MMD Tools. The owner already authorized a disposable pinned SourceIO download;
its revision/archive hash is recorded in `dependencies.json` and the native
Windows receipts. Recreate it only in owned session staging, not shared tools.

Set these for the current PowerShell session, using an owned exact KRA copy:

```powershell
$env:HYBRID_HECATIA_KRA='C:\path\to\owned\hecatia.kra'
$env:HYBRID_NATIVE_INPUTS='C:\a\dump'
$env:HYBRID_FFMPEG='C:\Program Files\ffmpeg\bin\ffmpeg.exe'
python tests/verify_native_import.py
```

That actual app wrapper generates `output/native-import-verification.json` and
four complete bundles: Miku PMD, textured street PMX, original VRM1 and VRM0.
This session passes 43 actual app checks, exact packed pixel replay and an
actual 48-frame 1080p24 H264 movie, preserving all original sources/textures.

Prepare the two required Source rigs with the real adapter:

```powershell
python tools/prepare_source.py 'C:\a\tools\touhou_reimu_bikini.gma' --member models/ragdoll/reimu_hakurei_bikini_ragdoll.mdl --output output/acceptance-native-inputs/gmod
python tools/prepare_source.py 'C:\Program Files (x86)\Steam\steamapps\common\SourceFilmmaker\game\tf_movies\models\player\hwm\scout.mdl' --output output/acceptance-native-inputs/sfm
```

Create `output/native-project-plan.json` with an array of `label`, `source`
(absolute prepared GLB) and `project` (absolute owned output directory) records:

- MMD: the actual PMD bundle above → `output/pose-smoke/miku-project`.
- GMod: the actual selected GMA rig → `output/source-smoke/source-project`.
- SFM: actual installed Scout → `output/sfm-smoke/project`.

Run `tests/prepare_native_projects.gd` through `run.command`, passing the
absolute `output` directory after `--`. It uses the normal app Add model and
managed Save path; it does not fabricate project manifests or verification
reports. This session retains 126 MMD, 77 GMod and 83 SFM bones with native
metadata, then passes the existing 24-assertion native body-pose wrapper.

Finally run `python tests/verify.py` with the environment above. Preserve each
actual stop/skip/unrun case. The rerun was deliberately interrupted at the owned physics child to fix the
owner-reported scene layout defect. Its private desktop/job closed. Successful
prerequisite rebuilding is not a full aggregate pass; rerun after UI fixes.

## Concrete owner review

`tools/build_owner_review.py` prepares isolated Flatgrass/Avatar/Street packed
HAS projects from actual conversion bundles, with 7 writer and 12 cold-reader
checks. Each native asset has its own scene, without overlapping environments.
`tools/build_owner_review_snapshot.py` then creates a separate source-only
`output/owner-review/Studio` application and a unique user profile, and verifies
ordinary Home/New/Tutorial startup on a private desktop. No development cache
is copied and the installed Studio remains untouched.

The generated `Open Avatar.bat`, `Open Flatgrass.bat`, `Open Street.bat` and
`Start review.bat` launch only when the owner clicks them. Automated acceptance
keeps using private desktops. The owner review app has separate output,
preferences and recovery from the running aggregate. Keep the source snapshot
and private projects while review is pending; do not upload the private artwork
or remove an unbacked user-edited project. Source hashes and compact evidence
are saved in the dated receipt. Actual appearance/usability/device observations
remain required; a cold self-replay pass is not artist approval.
