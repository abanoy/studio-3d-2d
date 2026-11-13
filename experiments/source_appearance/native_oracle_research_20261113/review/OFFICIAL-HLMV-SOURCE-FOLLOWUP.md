# Official HLMV source availability follow-up

Researched 2026-11-13. Scope: primary Valve web sources only; no executable, model runtime, GUI, GPU, installer, archive download, Steam/registry/main/Git write, or third-party source mirror. This adds historical publication evidence to `VALVE-NATIVE-ORACLE.md`; it does not replace that proposal's unrun native fidelity status.

## Positive historical publication evidence

Valve officially distributed Source Model Viewer source before the current GitHub repository layout:

- The **17 February 2005** Valve product update states: “Added source code for Source Model Viewer included (src\utils\hlmviewer)”. This names an exact historical SDK source location. The same page's FacePoser slider fix concerns FacePoser, not HLMV controls. [Valve's release note](https://store.steampowered.com/news/392/), redirecting to [oldnews/392](https://store.steampowered.com/oldnews/392).
- The **18 June 2007** Valve product update states: “Added HL Modelviewer and phonemeextractor source code”. This independently confirms historical SDK distribution. It supplies no source-file links or viewer feature/argument specification. The search result was readable; direct open returned a cache miss in this session. [Valve's release note](https://store.steampowered.com/oldnews/1088).

Therefore **“Valve has never released Source HLMV source” would be incorrect**. Neither announcement identifies the current installed viewer's build or guarantees unchanged-file MDL49 support. The dated distribution source, if found from its original approved delivery, still needs its version and behavioral relationship to the installed binary established.

## Bounded current repository observations

The official [source-sdk-2013 all-branches page](https://github.com/ValveSoftware/source-sdk-2013/branches/all) showed `master` and `singleplayer`. The fetched directory listings at both [master/src/utils](https://github.com/ValveSoftware/source-sdk-2013/tree/master/src/utils) and [singleplayer/src/utils](https://github.com/ValveSoftware/source-sdk-2013/tree/singleplayer/src/utils) contained neither `hlmv` nor `hlmviewer`. Both included other SDK utilities such as phonemeextractor. These observations are about those fetched directory listings only.

Several explicit historical-path/history-page web requests were attempted, including `src/utils/hlmviewer`, `sp/src/utils/hlmv`, and `mp/src/utils/hlmv` history views and guessed raw singleplayer file paths. They returned cache misses and are **not negative proof that those paths never occurred in Git history**. No complete commit-object/tree enumeration was performed by this reviewer. The parent is separately checking official history; its verified results must be incorporated before making a stronger repository-history claim.

Valve's Source SDK 2013 [studio.h](https://raw.githubusercontent.com/ValveSoftware/source-sdk-2013/master/src/public/studio.h) still declares `STUDIO_VERSION 48` in the fetched primary content. That establishes this public header's model version, not a capability statement about every current Source-family executable.

The official [ValveSoftware/halflife/utils/mdlviewer](https://github.com/ValveSoftware/halflife/tree/master/utils/mdlviewer) tree **does contain viewer implementation source**, including `mdlviewer.cpp`, `studio_render.cpp`, and `studio_utils.cpp`. However its [loader](https://raw.githubusercontent.com/ValveSoftware/halflife/master/utils/mdlviewer/studio_utils.cpp) includes the Half-Life [engine/studio.h](https://raw.githubusercontent.com/ValveSoftware/halflife/master/engine/studio.h), loads in-model texture/palette data, and uploads it to OpenGL. It is the Half-Life viewer path, not evidence of the required Source MDL49/VVD/VTX/VMT pipeline. Its similarly named controls must not be substituted as proof of an installed Source HLMV's behavior.

## Requested behavior audit: exact evidence still unavailable

No applicable Source HLMV implementation was retrieved from an official source in this follow-up. The following remain **unverified for the exact installed viewer**, not claims of universal feature absence:

| Requested behavior | What remains to inspect in official, matching viewer implementation |
|---|---|
| Model loading | Argument parser, game/mount root selection, version gate, MDL/VVD/VTX checksum pairing, VMT/VTF lookup, error-model behavior, and external/absolute paths. Historical source distribution alone establishes none of these details. |
| Skins | Actual skin menu callback, range validation, selected family storage, and renderer parameter. Generic SDK `SetSkin` APIs are separate evidence from HLMV UI/CLI support. |
| Bodygroups | Viewer group/choice selectors and packed-body construction; confirm group indices/names and blank choices. Do not assume the experimental textual `010` tuple is a native packed body integer. |
| Flex | Exact controller enumeration, min/max/UI remaps, descriptor/rule application and slider behavior. A descriptor name or a generic SDK flex API is not enough to prove the viewer exposes the required Tools control. |
| Arbitrary bone rotation | An actual per-bone transform edit path and render usage. Bone visibility, bone-controller sliders, pose parameters, sequences and ragdoll/physics constraints do not establish arbitrary bone posing. No such exposure was verified. |
| Screenshot menu | Menu binding, implementation, render target/readback, output naming/format, image-write failure behavior and saved resolution. No exact HLMV screenshot-menu implementation was verified. |
| Screenshot/batch CLI | Actual accepted flag names, model/variant inputs, capture timing, no-dialog path, output and exit contract. No executable command is proposed from guessed flags, generic engine options or third-party scripts. |
| Settings/cache/registry | Every file/registry write, key/root derivation, relative path base, load/close persistence, default/missing settings behavior, and any documented redirection. No exact redirect was verified. A private desktop and an owned model mount do not by themselves isolate preferences or registry writes. |

The Valve Developer Community HLMV/MDL and Source SDK release-note pages still returned HTTP 403. Primary Steam release notes resolve the historical distribution question, but do not unlock those detailed feature claims. Search results from community issue authors, tutorial mirrors, third-party maintained ports and leaked-source repositories were not accepted as original matching viewer implementation.

## Concrete next step

Look for **already present, officially delivered SDK text source** at the documented `src\utils\hlmviewer` path and later `utils\hlmv` paths, without running the viewer or changing Steam. If present, hash it, establish its origin/build/version, and audit the exact paths above. Otherwise finish the parent's bounded official Git history check and record the source availability limit. Retrieving a historical SDK package or adding a third-party viewer is separate scope; neither happened here.

Until matching implementation or equivalently precise primary documentation is available, leave native viewer launches, state changes, screenshots, arbitrary bone posing and MDL49 compatibility **UNRUN/UNVERIFIED**. This is a source-availability limit, not a conclusion that HLMV cannot do these things.
