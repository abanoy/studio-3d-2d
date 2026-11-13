# HLMV controls, capture and preference isolation follow-up

The bounded official-source search did **not retrieve an applicable Source HLMV
implementation**, so it cannot yet supply exact screenshot/menu/CLI syntax or
registry/cache write locations for the installed SFM viewer. No viewer, model,
GUI or GPU ran. No registry, Steam, main-source or Git writes occurred.

Valve did officially distribute this source historically. Its
[17 February 2005 release note](https://store.steampowered.com/news/392/)
names `src\utils\hlmviewer`; its
[18 June 2007 release note](https://store.steampowered.com/oldnews/1088)
again announces Modelviewer source. The correct conclusion is source
availability in the locations checked, not that Valve never released it.

The fetched current official SDK master/singleplayer utility listings omit the
viewer. Historical path/history web requests returned cache misses; no complete
Git history enumeration was performed. The official Half-Life repository has
[older viewer code](https://github.com/ValveSoftware/halflife/tree/master/utils/mdlviewer),
but its [loader](https://raw.githubusercontent.com/ValveSoftware/halflife/master/utils/mdlviewer/studio_utils.cpp)
uses embedded texture/palette data and OpenGL. That is a different model/render
pipeline and cannot establish Source MDL49/VVD/VTX/VMT viewer behavior.

A read-only filename search also checked the installed SFM/GMod trees: 216
source-like C/C++/header files were enumerated, with no matching viewer,
ViewerSettings or ControlPanel source filename. This did not inspect archives
or search the whole PC. The command and result are retained in
`installed-text-source-search.json`. No SDK was downloaded or installed.

## Exact control and capture status

| Route | Established evidence | Remaining exact-build gate |
| --- | --- | --- |
| Model loading / game root | Installed Valve SDK template calls HLMV with `-game` | Model argument grammar, loader/version checks, pairing/checksums and actual MDL49 load are unverified |
| Skin / bodygroups | Official SDK native APIs and packed body-field semantics | Actual HLMV selectors/callbacks/CLI, accepted ranges and recorded selection need matching implementation or native observation |
| Tools flex | Exact chisels inventory records controller 0, range 0..1, descriptor 0 via FETCH1(0) | Native HLMV controller enumeration/slider/rule application remain unrun; failed controller lookup returning zero is not proof |
| Screenshot menu | No matching Source HLMV menu implementation retrieved | Menu ID/action, readback timing, format/resolution, naming and write failures are unknown |
| Screenshot/batch CLI | No matching command parser retrieved | No guessed `-screenshot`, `.mvscript`, skin/flex flags or unattended exit contract may be treated as verified |
| Arbitrary bone rotation | Generic native SDK code can draw caller-provided bone matrices | No installed HLMV per-bone transform editor was established; BoneController sliders, sequences and pose parameters are not that evidence |
| Registry / preferences / caches | No matching viewer settings implementation retrieved | Exact keys/files, startup/close writes, shared globals and redirect switches are unknown |

The installed SFM binary's MDL49 support and current UI behavior remain
**UNRUN/UNVERIFIED**, despite SFM shipping MDL49 stock assets. No behavior is
inferred from a similarly named control in older Half-Life viewer code.

## What can be redirected on primary evidence

Valve's official
[SDK gameinfo example](https://github.com/ValveSoftware/source-sdk-2013/blob/master/game/mod_hl2mp/gameinfo.txt)
sets `mod_write`, `game_write` and `default_write_path` to the owned
`|gameinfo_path|` root. Along with the installed HLMV `-game` template, this
supports an **owned filesystem mount/write-root candidate**. It does not prove
that HLMV routes every screenshot/config through those paths or redirects its
registry/preferences. Current-game template behavior also cannot be assumed
identical in SFM's older branch before checking it.

No HLMV registry-root/profile/no-preferences redirect switch was established.
Changing the working directory or using another copied model pathname does not
prove shared preferences are isolated. A private desktop isolates the displayed
window, not the logged-in user's registry/profile.

## Eventual private capture plan

1. Before native launch, obtain the applicable officially delivered viewer text
   source or equally precise primary documentation. Audit its argument parser,
   model controls, screenshot menu/CLI, settings load/save and shutdown paths.
   Map every writer and any real redirect option. Hash that source and state
   how its branch relates to the installed binary; older source is conditional
   evidence, not a binary compatibility certificate.
2. If a genuine complete redirect exists, bind it to a fresh owned profile and
   mount. Otherwise use a separately approved disposable Windows profile/hive
   or comparable isolated environment, with Steam/tool trees read-only and only
   owned output writable. Availability and compatibility of such an environment
   have not been checked. Do not use a private desktop alone or shared-owner
   preference snapshot/restore as a substitute for isolation.
3. Under a later exclusive GPU lease, first verify the private window/job and
   actual MDL49 model/control/capture path on one native model. The output must
   be fresh, positively rendered, and accompanied by exact selector state,
   native warnings and resolved dependency paths. Stop before the matrix if
   isolation, load or capture is unproved. No visible fallback is allowed.
4. Only then run the existing twelve-state skin/bodygroup/Tools appearance
   matrix. Keep all source/runtime bytes and owner/Steam settings unchanged.
   Arbitrary bone/weight testing stays separate until an actual native
   per-bone transform path is proved, likely requiring SFM or a matching native
   harness rather than assuming HLMV BoneControllers provide it.

This is a concrete research prerequisite, not a native fidelity result or a
request to interrupt the owner. The canonical run retains the GPU lease.
The detailed primary-source audit and failed retrieval boundaries are in
`review/OFFICIAL-HLMV-SOURCE-FOLLOWUP.md`.
