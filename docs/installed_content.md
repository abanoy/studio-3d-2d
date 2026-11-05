# Installed Source content browser

Choose **Installed** in the blue navigation bar. This browser reads local content;
Garry's Mod must already be installed. No games, Workshop items or texture packs
are installed, subscribed to, downloaded or distributed by Studio.

1. Choose a location on the left, or enter an asset name and choose **Search all**.
2. Filter **Models**, **Maps**, or both. Search matches native paths and indexed
   addon titles. The location filter also matches addon IDs and physical paths.
3. Select an item to see its exact original location/member and size. Double-click
   or **Import selected** prepares it and loads it through the same standard GLB
   scene/model system used by MMD. Model replacement asks before replacing an actor;
   map import preserves the separate actor, drawings and camera keys.
4. **Locations…** changes the game/Workshop folders and adds content directories or
   VPK indexes, one per line. An SFM `game`/mod folder can be added here too.
5. Installed resources now resolve automatically. Uncheck **Use location for dependencies**
   to exclude a location when diagnosing a conflict. Explicit exclusions survive refresh. Preferences live in `output/source-paths.cfg`, outside project data.
   Refresh rescans locations. Cancel scan stops only the browser worker.

The browser indexes archive directories without unpacking their payloads. GMA and
legacy LZMA-bin files list their model/map members; VPK1/2 support includes directory
and numbered-segment storage. VPK import copies the selected MDL/BSP and available
model sidecars, validates their CRCs and resolves materials from mounted content.
Other files stay in place. Shared GMA dependencies are read selectively with size
and CRC checks. Lua is never executed. Source data and config files remain read-only.

## Discovery and mount order

The following locations are checked when present:

- GMod `garrysmod/`, `sourceengine/`, `platform/`, including `*_dir.vpk` files;
- loose/packed `garrysmod/addons/`, `garrysmod/cache/workshop/`, optional legacy
  `garrysmod/workshop/`, and `steamapps/workshop/content/4000/` in discovered libraries;
- `garrysmod/download/` (and optional legacy `downloads/`) and gamemode `content/`;
- data paths in `garrysmod/cfg/mount.cfg`, with immediate content subfolders/VPKs;
- Steam `libraryfolders.vdf`, relevant game manifests, and installed CS:S, TF2 and
  HL2 episode locations, honoring explicit disabled entries in `mountdepots.txt`;
- optional SFM `game/usermod/gameinfo.txt` search paths, familiar mod folders and
  local `steamapps/workshop/content/1840/` directories, plus explicit extra locations.

This is an offline approximation of content availability, **not a copy of the live
game's mount state**. GMod can use an alternate `-mountcfgfile`, runtime addons and
other state Studio cannot infer. Add those paths explicitly. The game's read-only
[`path` console listing](https://wiki.facepunch.com/gmod/File_Search_Paths) can help
diagnose differences; Studio does not run that command or launch the game.

The selected asset's own resources take priority. Enabled locations use a contextual stable order: explicit additional roots, then
SFM declared search paths for an SFM asset, GMod/base/configured content, other
SFM base resources, and remaining add-on/custom packs as fallbacks. Duplicate
resources use the first hit. GMod loose/GMA addons and installed SFM content now
participate automatically; saved explicit exclusions remain authoritative. This
changes the older checkbox-only default. Browser and native-file imports share
the same resolver; only requested resource bytes are copied. Legacy-bin packages can import their own staged
resources; to share them as dependencies, mount their prepared native directory.
Search lists installed content regardless of dependency-checkbox state.

Full resource/provider identities and actual hashes are retained in each conversion
bundle's `dependencies.json`; only used dependency bytes are copied. Keep the entire
preparation bundle for native provenance. Standard project save still manages the
GLB and model metadata rather than every original/native/intermediate file.

## Missing CS:S textures and SFM

Facepunch's [July 2025 update](https://gmod.facepunch.com/news/july-2025-update) added
most CS:S and HL2 episode assets to GMod, excluding their maps, voice-over and music.
On this machine `sourceengine/content_cstrike_dir.vpk` exposes **1361 models** in
the index. The real office chair imports with its texture and zero resource warnings.
A separately installed CS:S copy is still useful for maps or assets not included.
Missing files cannot be manufactured by mount discovery; unsupported Source shaders
can also look wrong even when their textures resolve. Existing PBR limitations apply.

At the start of this task SFM's directory was empty. Its manifest and real game
files appeared during the work, with no installer, Steam launch or download invoked
by this assistant. Actual installed `usermod/gameinfo.txt` search paths were then
read, alongside [Valve's SFM search-path release notes](https://store.steampowered.com/news/posts/?appgroupname=Source+Filmmaker&appids=1840&enddate=1408130039&feed=steam_updates/1000)
and the [pinned SourceIO SFM detector](https://github.com/REDxEYE/SourceIO/blob/fe24260b97ac03b899d9b5d4f0fd7b34772f3647/library/shared/content_manager/detectors/sfm.py).
The browser distinguishes actual content markers from empty directory placeholders.

Enabling the available SFM content for the supplied shrine map improves resolved
props **112/525 → 524/525** and base textures **13 → 34**. The resulting51.7MB GLB
renders and saves/reopens in Godot. One native prop still fails a CRC check on its
embedded material; that error is retained rather than bypassed. Geometry is now
available, but shading, lightmaps, skies and material effects remain approximate.

This is Source **asset** compatibility. It does not read SFM sessions/DMX animation,
procedural rigs, particles, film clips, lighting controls or native engine effects.
SFM installation/use outside these read-only asset checks is not certified.

## Limits and verification

Discovery is bounded to4096 locations, archive indexes to100000 entries/32MiB VPK
trees, loose scans to100000 files per location, global matches to50000. At most2000
matches display at once; refine the query for more. Worker requests run in separate
processes, with cancellation and120s timeouts. Bad/unsupported archives produce
index warnings; they do not prevent other locations from being searched. Two local
GMA packages report unsupported versions. No persistent index cache or thumbnails
yet; titles are learned when indexed. Native conversion keeps its existing512MiB
GMA/legacy and128MiB-GLB limits. This is not a hardened hostile-file sandbox.

Run `python -u tests/verify_source_browser.py` for fixture tests and actual private
installed-content UI imports, including a texture supplied by a separate GMA.
`python run.py --test source-browser` runs the UI portion alone. The optional
`tests/source_mount_render.gd` compares the two private shrine preparation bundles.
`tests/verify_source.py` and `tests/verify.py` retain native/standard regression and
actual movie/audio verification. Physical input feel, all Steam arrangements,
arbitrary DPI and native appearance fidelity still need owner use.

Primary mount references: [Facepunch mount configuration/depot documentation](https://wiki.facepunch.com/gmod/Mounting_Content_on_a_Dedicated_Server),
[file search paths and priority](https://wiki.facepunch.com/gmod/File_Search_Paths),
[addon folder structure](https://wiki.facepunch.com/gmod/Addon_Creation).
Valve's public VPK format wiki returned403 during this research; the independent
reader was validated with VPK1/2 fixtures, actual installed VPK indexes/segments,
selected-file CRCs and successful native conversion.


## Verification checkpoint - 2026-10-29

Actual canonical runs: `python -u tests/verify_source_browser.py` exit0 (12content
fixture tests,28browser checks and an actual texture supplied by a separate GMA
through saved mount settings). Indexed562locations/1361included CSS models; actual
CSS chair, installed Workshop Reimu GMA/77bones and gm_construct BSP were selected
and imported through the in-app browser. Global search, dependency preference
reload, replace confirmation, cancellation, actor/environment isolation and managed
reopen pass. Saved model name retains chair_office.mdl. Actual light browser PNG
and native chair/shrine renders were visually inspected.

Canonical `tests/verify_source.py` exits0:8archive+6path tests and32native UI checks,
with both1080p24/48frame/2second model and map MP4s and exact frame24 pixel agreement.
Canonical full `tests/verify.py` exits0:unit24, editor39, GPU spikes, encoder failures,
audio24/Dummy, UI23, recovery14+13, pose44 with actual Miku; AAC onset1.000s and
RMS5658.30 retained. `source_mount_render.gd` exits0:8checks for the shrine baseline
and dependency-resolved GLB, visible rendering changes and managed save/reopen.

Known limits remain: two unreadable local GMA versions, one bad embedded material
CRC in the shrine, approximate native shaders/skies/lightmaps, no live mount-state
replica, thumbnails or SFM session/DMX/rig support. No physical-input/all-DPI or
native appearance acceptance claim. Game/Workshop/SFM folders remain read-only;
no game installation, launch, subscription, texture download or deployment occurred.


## SFM inspection and automatic fallback increment - 2026-10-29

Inspected the real SourceFilmmaker/game installation and its usermod/gameinfo.txt.
The declared order is usermod, tf_movies, tf, left4dead2_movies, hl2, workshop.
Present models include the HWM Scout; SFM's box BSP is also available. Neither
`game/workshop` nor `steamapps/workshop/content/1840` exists locally at this check.
Studio now reports that absence explicitly. There are no real SFM subscribed items
to certify yet. Refresh after they become available locally; no app/game launch,
subscription or download is performed by Studio.

Both the aggregate SFM game/workshop resource tree and numbered Steam1840 item
folders are discovered when present. Loose/nested content, GMA and VPK directory
indexes are supported; numbered VPK segments are not shown as independent packages.
Immediate custom game mods containing models/materials/maps are also found, even
if not yet declared in gameinfo. Workshop/script/session files remain data and
never run. Modern Source2 formats and SFM session/DMX animation remain unsupported.

The pinned decoder's existing extended VTX7 retry missed BufferError from its own
seek API. The adapter normalizes that error to struct.error only for VTX buffers,
allowing the existing alternate-layout validation to run; it never suppresses
CRC failures or accepts a file when both layouts fail. Vendor cache files are unchanged.

HWM Scout's native bind mesh is Y-up. Native first-animation/reference-pose experiments
were rejected after visual inspection: those poses do not give a reliable neutral
upright result. Bind data is preserved instead. For this model select the model root,
Advanced Rotate, set Local X to90 degrees, Apply, then Frame model. This is a known
manual asset-orientation step; automatic up-axis inference is not claimed. Ordinary
bone posing, explicit keys and export use the same standard controls afterward.

Unreadable/oversized dependency GMA indexes are skipped once per conversion and
recorded separately in parameters.json/mount_warnings, with a status count. They
are not misreported as defects in an otherwise resolved model. Current assets with
missing/corrupt requested resources still receive normal resource warnings. A bad
selected archive still fails its own staging integrity checks. GMA fallback cap
remains512MiB; prepared loose directories can be added for larger content.

Run `python -u tests/verify_sfm.py` for optional actual installed SFM model/map,
posing, managed-save and H264 export checks. It explicitly skips missing private
fixtures. Workshop layout/exclusion/order cases remain mandatory synthetic fixture
coverage in test_source_content.py until subscribed SFM data exists locally.


## Verification of SFM and automatic dependency increment - 2026-10-29

Actual canonical tests: verify_source_browser.py exit0 (14content fixture cases,
28real UI checks, included CSS model/texture, Workshop Reimu, gm_construct and
a separate GMA supplying a real missing material). verify_sfm.py exit0:13real
checks for library selection, extended VTX Scout83bones/5textures, arm deformation,
undo, shared project/cels, save/reopen and MP4, plus actual SFM box BSP import.
Native selected inputs/gameinfo hashes remain unchanged. Material provenance
confirms tf_movies VMTs and tf textures without manual dependency checkboxes.
SFM movie: H2641920x1080,24/1,48frames,2.000000s, exact exported frame24 agreement.
Actual upright Scout and map PNGs inspected; native eye/material rendering remains
approximate. The fixture explicitly applies Scout's documented90degree root-X
bind-axis correction; automatic orientation is not claimed.

Read-only inventory:8414model files and81maps across available SFM roots, not a
claim every listed file converts. Neither supported SFM Workshop content folder
exists yet. Workshop aggregate/numbered loose/VPK/GMA layouts, contextual order
and persistent exclusions are fixture-tested; no real subscribed SFM item test.

Automatic fallback exposed quadratic provider-membership work. Replaced it with
identity-set membership, fast GMA index misses and a per-import negative cache
invalidated by provider-count changes (including a newly mounted BSP pak). A slow
owned test run was stopped/restarted after this fix; final tests use the saved
code. Unrelated unsupported/oversized GMA indexes produce separate mount warnings,
not false missing-material dialogs. Native-resource CRC failures remain visible.

Canonical verify_source.py also exits0:8archive+6installation fixtures,32actual
native UI checks, original input hashes, cancellation/owned Blender termination,
model/map H2641080p24/48frame/2second exports and exact frame24 agreement. Existing
map reimport tolerance reports6changed color bytes across2pixels (mean0.000063/255).
Canonical full verify.py exits0:unit24, GPU spikes, editor39, encoder failures/cancel,
audio24/Dummy, UI23, recovery14+13 and pose44 with actual Miku. AAC onset1.000s,
RMS5658.30 retained. No native shader fidelity, physical-input/tablet, audible
listening, all-layout, clean-machine or hostile-file certification is implied.

Fresh canonical default-only shrine conversion also exits0, without mount settings,
content paths or an explicit plan:524/525props,718meshes,34textures,83resolved SFM
resources and51672788byte GLB. One embedded-material CRC failure remains visible;
5unsupported/oversized GMA fallback packages are recorded separately. Bundle:
output/compatibility/shrine-automatic-fallbacks. This is actual automatic cross-game
resolution, not just the prior explicit-SFM-mount experiment. Native shaders and
all other documented Source rendering limitations remain unchanged.
