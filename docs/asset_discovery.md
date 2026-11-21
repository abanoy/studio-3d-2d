# Asset discovery browser

Implemented on `worker/asset-browser-live-20261121`, based on GitHub `main`
`243e6a1edf1aee5cd07f107a34775db49a2caa01` (checked November 21, 2026).
Continues the preserved initial `worker/asset-browser-20261121` / `85d07df0`
implementation; that earlier branch and its checkout outputs are retained.
This feature checkout integrates the browser into normal Studio with two menu
hooks and one shutdown hook. Other checkouts and installed Studio remain unchanged.

## Launch

From this checkout, with the existing Godot 4.6 stable standard installation:

```powershell
python run.py
# Simple: Add → Asset discovery…; Advanced: Discover
# Standalone browser, without the rest of Studio:
python tools/asset_discovery_demo.py
```

Alternatively set `HYBRID_GODOT` to that engine's executable first. No dependency
installation, model files or project are needed. The engine project/main scene
remains unchanged. The demo offers Neon, Classic light and
Classic dark using the existing `studio_theme.gd` implementation.

Local starts offline. Choose one or more directories; filename search updates
the list, and the format menu combines with it. Clear directories starts over.
Selecting a filename shows its full path and extension-only evidence. **Use
selected local file** emits a path to the parent; the standalone demo reports
that selection without importing anything. Cancellation keeps partial filenames.
**Preview GLB geometry** explicitly opens a separate, orbitable geometry-only
window for supported GLBs. It does not change the Studio project or source file,
start a converter or fetch external resources. See its limits below.

Directories, provider, separate Local/Online format filters, the last tab and name
expansion choice survive restart in a personal JSON file. The standalone default
is `output/discovery-preferences.json`; the Studio bridge places it beside the
existing display preferences. It is not embedded in HAS projects. Network access
always restarts off; queries, accounts, credentials and images are never saved.
Returning to Local rescans saved directories; missing directories report errors.
Settings are schema-checked, limited to 32 directories / 64 KiB, and replaced by
temporary-file rename. Failed writes retain the previous file. Malformed settings
show defaults and a useful error without being overwritten on startup.

Online has independent website and format menus. Enable online access and press
Search (or Enter). An empty query starts discovery. The first batch targets 100
unique listings across the available metadata providers. **Load another batch**
adds up to another 100, preserving the relative order of earlier results while
moving newly discovered exact matches ahead of broad matches. This is a target,
not a fabricated quota: restricted, exhausted or failing providers can produce
fewer results. Website search links do not count as listings.
An activity bar shows work in progress. For a website-only provider, **Open
website search** is available directly beside the paging controls, even with
online access disabled. Other website/query variations are under provider details.

Click a listing to open its source page through the default browser. Enter also
opens the selected online listing. There are no model downloads, subscriptions,
account flows, conversion, model execution or automatic thumbnail requests.
**Thumbnail preview** is a separate opt-in, off by default. With online access
enabled, it loads only the selected result's supplied Poly Haven/Sketchfab CDN
image. No model data is fetched. A thumbnail never establishes a 3D preview or
access permission. Other providers do not gain image requests via website links.

## Implemented boundaries

| Area | Behavior |
| --- | --- |
| Local enumeration | PMX/PMD, VRM, MDL, GLB/glTF, FBX, OBJ and Blend filenames; recursive selected directories; hidden entries and links skipped. No archive or model parsing. |
| Explicit local preview | GLB only, maximum 8 MiB, embedded geometry buffers only. Materials/images/animations/morphs/cameras/extras/extensions are removed from an in-memory preview copy before import. Required extensions and compressed buffers are refused. No source file is rewritten. Counts, buffer bounds, node hierarchy and instanced vertex counts are bounded; at most 256 joints per skin. A separate world/camera renders plain geometry with an orbit slider. Parsing is synchronous after the explicit click; full-material/native-format previews remain unsupported. |
| Format labels | MMD, SFM, VRM, GMod, glTF, FBX, OBJ, Blend, Source MDL and Unknown. Online labels use title/tag terms and visibly say **(inferred)**. The selected-row details explain that file contents were not inspected. Provider identity alone never supplies a format. |
| Local MDL | Labelled Source MDL. SFM/GMod cannot be distinguished from the extension; neither compatibility is invented. |
| Access | Sketchfab viewerUrl gives Preview (source-site viewer); isDownloadable=true gives Downloadable, not a tested retrieval; explicit isProtected=true gives Password. Missing download/login/password information remains Unknown in labels/evidence. No current adapter has evidence for an item-specific Login required badge. |
| Names | Original query, ASCII width/case/spacing normalization, reverse word order, explicit aliases, individual words. Expand names can be disabled. Original titles are retained. |
| Aliases | Only Hatsune Miku / Miku Hatsune / 初音ミク / 初音未来 are bundled; primary references are in the source notes. Unknown names are not translated. |
| Query disclosure | Shows generated variations and actual Sketchfab queries sent. Poly Haven/feed matching is local against fetched metadata. Website searches let the user choose a variation. |
| Ranking | Exact loaded titles first, then contained full/reordered names and known aliases, then broad words. Newly fetched exact matches move ahead of earlier broad matches; existing rows retain their relative order and the visible row anchor is restored. Unfetched remote matches cannot be ranked. |
| Duplicates | Provider item IDs and source-page URLs (without query/fragment for the three current path-ID adapters); distinct entries sharing a title remain distinct. |
| Requests | One metadata request at a time, at least 600 ms apart, at most six requests per batch, 12-second timeout, 4 MiB response limit, no redirects/cookies/authentication. Normal editing never opts into networking. |
| Throttling | HTTP 429 stops that provider, preserves partial results and observes numeric Retry-After (at least 60 seconds). Without the header, wait 60 seconds; unrecognized/date-form hints pause that provider for the session. No automatic retry. Search can retry other failures. |
| Cache | Poly Haven metadata in memory for ten minutes; no persistent network cache or downloaded artwork. |
| Thumbnail bounds | Approved HTTPS image endpoints only; no redirects/auth/cookies. One image request at a time, at least 600 ms apart, 8-second timeout, 1 MiB encoded limit, dimensions checked before decoding (maximum 1024x1024), 96x96 display, eight cached images/errors in memory. Failures show a placeholder; 429 pauses image requests for this browser session. |
| Cancellation | Search/filter changes, Cancel, disabling network, switching tabs and closing the wrapper stop obsolete work. Generation checks reject late responses. |
| Local limits | 50,000 entries, 10,000 matching filenames, 32 directory levels; scan slices at most 128 entries / about 3 ms per frame. Errors and limits are reported. Slow filesystem calls themselves can still stall; arbitrary network-drive latency is not solved by this cooperative scanner. |

## Integration hooks (primary worker applies separately)

The **three-line app.gd integration is already applied on this feature branch**. It is the
only shared application source changed. Renderer/model/import/world files,
project.godot and the canonical verifier remain untouched. The independent patch
is retained for the primary to review or apply when adopting modules separately:

```powershell
git apply --check docs/asset_discovery_integration.patch
git apply docs/asset_discovery_integration.patch
```

Do not apply that patch again after adopting this branch's integrated app.gd.
The patch keeps app.gd's original CRLF source context and line endings.

One line adds **Asset discovery…** to Simple's Add menu. Another calls
`preload("res://src/discovery/studio_bridge.gd").install(self, toolbar)` beside
Installed in Advanced. The module owns its button/window and needs no app member.
A third line awaits the bridge's `finish()` in `quit_studio`, after setting
`closing_studio`. It drains pending browser requests before the SceneTree quits.
The earlier patch-only increment was tested in a disposable copy. Current tests
copy the already integrated application source, verify exactly one bridge install
and exercise both real entry points. They never modify the primary's checkout.

The bridge captures recovery session/revision, sequence owner/generation and
world/joint selections when opened. The deferred local callback checks them again,
checks active import/export/project/dialog/height-review/sequence operations and
**source_import.bundle_active**, validates the file and supported extension, then
calls the ordinary `import_actions.add(path, true, 0)`. The window is closed before
that call. Stale or busy callbacks report an error and preserve the scene; they
never silently retarget another scene or selection. Online actions remain browser
only. No HAS schema changes or alternate import pipeline are introduced.

For embedding, instantiate `browser.gd` in an existing Control, inherit the parent
theme, and connect `local_file_selected(path)`. `source_page_opened(url)` is an
optional notification. Call `cancel()` before hiding a retained panel; freeing
the panel also cancels work. `window.gd` already does this when closed. The wrapper
returns a Window and exposes its panel via `get_meta("discovery_panel")`.
Embedded panels may set `preferences_path` before adding them to the tree; use an
empty string for session-only behavior. The wrapper accepts the same setting in
its optional third options dictionary. The guarded Studio bridge is the preferred
import integration; the raw panel signal does not itself enforce host ownership.

## Actual verification and limits

`python tests/verify_asset_discovery.py` passes **88 runtime checks** in Godot
4.6 stable, headless. It operates production Controls, including viewport mouse
events for Search and the online Tree, FileDialog directory-selection signal,
filter/button/tab signals, real filesystem enumeration of synthetic empty model
filenames, and production response parsers through an injected metadata transport.
Browser openings are intercepted; no owner browser is opened by tests.

Coverage includes mixed 100 + 100 batches, preserved first-batch order, repeated
IDs/URLs, distinct same-title records, Japanese queries/RSS, exact ranking,
Unknown/protected metadata, malformed JSON/field types/RSS, 403, timeout, 429,
cooldown, cancellation, stale replies, online opt-out, safe source URLs, unchanged
fixture files, three themes, and the standalone window's open/close lifecycle.
The initial run found truncated RSS accepted by Godot's parser; explicit nesting
and closure checks fixed it. Pointer testing also exposed reselect activation;
the final Tree handler opens directly from the clicked row and supports Enter.

The earlier `e1383a38` live probe (`--live --require-listings`) passed using
the actual production HTTPRequest and UI paths with host network access. Initial
discovery returned **100 real individual listings** (76 Poly Haven / 24 Sketchfab),
then **200 total** (152 / 48) with no repeated identities or lost earlier entries.
The English name search returned **54** unique listings after five queries,
including Japanese/Chinese aliases; **21** matched a separate `初音ミク` query.
The name search honestly stopped short of 100 with more available. A real
in-flight request was cancelled, its HTTPRequest released and loading cleared.
Cold startup was offline; opening a real result's source URL was intercepted
in the test. No model/image file or actual download was requested. Counts are
observations of that run, not permanent provider guarantees. The non-strict
`--live` mode records provider outages without inventing a success requirement.
Earlier restricted-shell DNS failures remain historical failures; host access
resolved that test environment limitation.

`python tests/verify_asset_discovery.py --graphical` passed **100 runtime checks**
on the private Windows desktop with Intel OpenGL, including pointer interaction
and six inspected PNG captures: Neon, Classic light and Classic dark at 1240x860
and 960x700. Each owned child/desktop/job closed; no foreground child was observed.
The earlier restricted-shell private-desktop refusal remains historical. The
new layout assertion initially confused native pixels with stretched viewport
coordinates; comparing the viewport boundary fixed the fixture. The fixture now
uses the same background surface as the demo, preserving readable Classic text.
No application tolerance was relaxed. Captures stay ignored in output, outside
Git. See `docs/benchmarks/asset_discovery_2026-11-21.json` for safe run observations.
Only focused discovery checks ran; no complete-suite or owner-acceptance claim.

Remaining limitations: several providers are website-only, BowlRoll's historical
mixed-content feed is not currently RSS, known-type filtering can exclude useful
Unknown entries, and aliases are deliberately small. Fully materialled/native
3D previews, sounds and account APIs are later work. Thumbnails are selected-item previews rather
than an image grid; cache and opt-in last for the current browser instance.
There are no blocking owner decisions for this increment.

The live BowlRoll endpoint returned HTML instead of RSS (HTTP 200). Its historical
RSS adapter remains available if RSS returns, but current BowlRoll discovery is
website-only in practice. No HTML scraping fallback was added. Steam, SFMLab,
BOOTH and VRoid likewise have website actions rather than fabricated result rows.

## Persistence, thumbnails and guarded integration follow-up

The persistence increment is based on the preserved `e1383a38` browser. Its
patch-only scope is historical; the subsequent integration increment applies the
two hooks in this feature checkout and adds explicit local geometry preview.

```powershell
# New checks: thumbnail limits + two-process persistence + patched real Studio
python tests/verify_asset_discovery_additions.py
python tests/verify_asset_discovery_additions.py --graphical
# Thumbnail/persistence scopes without another Studio run
python tests/verify_asset_discovery_additions.py --persistence-only
# Actual public provider/filter/image retrieval, separate from fixture tests
python tests/verify_asset_discovery.py --live --require-listings
```

Executed scopes, kept separate:

- **21 thumbnail checks:** generated PNG/JPEG/WebP decoding, pre-decode dimension
  and encoded-byte limits, approved URLs, offline default, selected-row opt-in,
  eight-entry cache bound, 503/429, cancellation/stale image rejection and visible
  inferred-format labels. Fixture images/transport do not prove provider access.
- **17 persistence checks in two fresh processes:** actual Unicode directories,
  independent filters/provider/tab/expansion, network opt-in not saved, clear-list
  persistence, malformed/oversized/invalid values, failed-write preservation and
  no startup rewrite of corrupt settings. These are actual JSON writes/readbacks.
- **22 patched real-Studio checks per theme headlessly**, then **23 per theme
  on private Windows desktops** (extra capture check): Simple menu, Advanced
  toolbar, offline opening, online-only source action, bundle queue and active
  operation guards, stale document/world/joint/sequence refusal, missing and
  unsupported files, real generated-GLB import and Undo. The patch is applied only
  to a disposable source copy; the root app.gd hash is checked before/after.
- **100 standalone private-desktop checks** rerun after the additions, including
  six inspected theme/size layouts. Two real-Studio captures were also inspected.
- Updated **live provider probe** retrieved 100 then 200 real mixed listings,
  English/Japanese hits, an MMD-filtered Sketchfab subset, and one public Poly
  Haven thumbnail after explicit opt-in. It checked actual in-flight cancellation.
  Current counts and safe evidence are in
  `docs/benchmarks/asset_discovery_persistence_integration_2026-11-21.json`.

Observed failures were fixed rather than waived: JSON numeric tabs deserialize
as floats (the preference reader now validates/canonicalizes them); the initial
integration fixture compared doubled Windows argument separators with normalized
scanner paths (the launcher now passes forward-slash paths); a NUL literal in a
validation check emitted parser warnings (validation now checks UTF-8 bytes).
Initial attempts and local captures remain in ignored output; no private model,
generated binary or thumbnail image was added to Git. Earlier 88/100 checks and
100→200 / 54-English / 21-Japanese retrieval remain historical scopes, not a new
single aggregate run. No complete-suite or owner-acceptance claim is made.

## Integrated geometry-preview checkpoint

The subsequent feature-branch increment includes the two normal Studio hooks
and **Preview GLB geometry**. A current focused invocation passed **109 checks**:
17 preview, 21 thumbnail, 17 two-process persistence, and 27 integrated Studio
controls in each of Neon/Classic on private Windows desktops. Preview images
were inspected and show the generated cube. Preview preserves source bytes and
the Studio world; the same selected cube then imports through ordinary
ImportActions and is removed by ordinary Undo. The normal main.tscn entry also
started headlessly and exited successfully in a bounded startup smoke without
recovering an existing project. No installation was changed.

The live provider probe on the integrated code returned 100→200 mixed listings,
55 English-name hits, 22 Japanese-name hits, eight MMD-filtered Sketchfab hits,
one explicitly enabled public thumbnail and real cancellation cleanup. These
counts are observations, not provider guarantees. Current safe evidence is in
`docs/benchmarks/asset_discovery_integrated_preview_2026-11-21.json`.

The preview hierarchy validator initially needed an explicit GDScript int type;
that compile failure occurred before graphical launch and was fixed. Materials,
animation/morph fidelity, preview conversion of other formats and large GLBs
remain unsupported. The full HAS suite and owner acceptance are separate work.

## Native shutdown follow-up

An additional live lifecycle audit found a real leak: closing a browser during
its native HTTPRequest freed its nodes, but Godot reported one resource still
in use at exit. The wrapper now hides/cancels immediately, allows a frame for
nested service work to unwind, then frees the window. Explicit local imports
wait until that close completes and recheck ownership/busy/closing state.

Studio's shutdown hook similarly awaits the bridge before quitting. New live
checks close the actual window during a native connection and quit actual Studio
with one pending. Both free the window/service/request without ScriptError,
ObjectDB-leak or resources-still-in-use diagnostics. Run them independently:

```powershell
python tests/verify_asset_discovery.py --close-live
python tests/verify_asset_discovery.py --quit-live
```

The current headless additions run passes **111 checks**, including 28 real
Studio controls per theme, with new refusal checks for a closing application
and a scene change during deferred close. Earlier 109/private graphical results
remain historical; no new GPU run was performed while the primary owns that
slot. Safe evidence is `docs/benchmarks/asset_discovery_shutdown_2026-11-21.json`.
The primary should adopt the current three-hook patch rather than the older
two-menu-hook checkpoint alone.
