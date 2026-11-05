# Installed SFM without GMod — development increment

The common installed-content browser and native MDL/BSP/PCF preparation no longer
require GMod for content recognized as belonging to an installed SFM location.
GMod content retains the owner's installed-GMod requirement. Studio downloads,
installs, launches and distributes neither host application nor its assets.

SFM discovery still follows Steam libraries/manifests, the local usermod search
paths, mod folders and Workshop1840 locations. Its installation must contain a
usermod gameinfo with FileSystem SteamAppId1840 and game/sfm.exe. This is a bounded
presence/configuration check; the executable is never run and this is not DRM.
Discovered SFM providers record the installation that declared them. A broken
second installation cannot borrow another valid installation's admission.

With GMod absent or incomplete, GMod base/addon/download/configuration providers
are removed from automatic dependency fallback. Installed SFM and other installed
Steam games, plus explicitly supplied dependencies, remain. A manually added
arbitrary folder alone does not turn a native file into an installed SFM asset.
GMod4000 Workshop assets still refuse before conversion/output creation. Search
and index are read-only inventory, not permission to import an unrelated model.

Native-file and browser imports use the same admission and contextual mount plan.
Source reports retain the detected source profile, empty GMod installation when
absent, and validated SFM installation locations. GLB/Model/world/HAS data formats
do not change. Existing projects and prepared assets do not need a host to reopen.

Eight installation fixture tests cover standalone browsing/source/Workshop,
missing/broken/wrong-ID hosts, unrelated/GMod assets, a broken second SFM location
and existing GMod admission. The first test run found an incorrect test-only
parent path for the fake sfm.exe; correcting that fixture yields8/8. Existing
source-path6, content14 and browser4 Python tests also pass.

Actual Windows standalone evidence is recorded in
`output/sfm-standalone/1793676845280016400` and
`output/sfm-standalone-verification.json`: the configured GMod path is nonexistent,
SFM discovery/index/search work, Scout retains83 bones and cross-mod textures,
poses and exact Undo work, independent ink/camera survive ordinary Save/Open and
packed HAS, and Studio exports H2641080p24/48frames. SFM box BSP appends without
losing the actor. All16 app checks pass on one confirmed closed private desktop
with no foreground child observed. Real SFM flash JSON/PNG hashes match the
earlier preparation. An actual GMod Workshop particle request refuses before its
output exists. Selected original model/map/config/executable hashes and times
remain unchanged. No game/add-on scripts execute. Other dependency files were
read, not exhaustively hash-audited in this wrapper.

The ten-group affected regression completed with every command exiting0 and seven
additional clean private graphical receipts on unchanged functional inputs. It
covers the8 installation fixtures,6 old preflight cases,4 browser cases, actual
particle data,29+5 particle UI/cold checks, existing native GMod/CS:S browser,
workspace, world, HAS and fill. Evidence is in
`output/source-host-review/1793676943878365600` and `output/source-host-review.json`.
No new full-verifier pass is claimed.
Normal installed Studio and the frozen web preview remain unchanged.

## Fidelity and remaining work

The subsequent [Source texture row correction](source_textures.md) now resolves
the misplaced regions described below in new development preparations. Its
thirteen-group affected regression now passes. Earlier standalone evidence remains unchanged
and correctly records the original defect; native eye shading is still incomplete.

The captured Scout has conspicuous misplaced material regions and approximate
eyes. Its PNG is byte-identical to the earlier GMod-assisted SFM test image: this
admission change neither fixes nor introduces that rendering defect. Passing
roundtrip/texture-presence tests is not visual fidelity acceptance. Inspection of
the bridge versus the installed SourceIO texture path suggests a pixel-row
orientation difference to investigate with an asymmetric test image; no fix or
cause is yet proven. Do not dismiss the visible defect as merely lighting.

Nonstandard SFM installations outside discovered Steam libraries, external loose
assets whose host cannot be inferred, malformed configuration isolation and full
native shader/UV/physics fidelity remain open. Place externally obtained SFM
content in a recognized installed SFM mod/Workshop root for this increment.
Broader PCF semantics and the rest of the full HAS specification remain required.
No separate relocated installation, clean-PC, physical mouse/tablet, subjective
audio or artist acceptance follows from these automated tests.
