# Browser preview alongside Windows Studio

The owner requested a Godot Web target through the Frontend chat. It reuses the
existing renderer, standard model, camera, drawing and timeline. Frontend owns
the Tools wrapper and hosting; this work does not deploy anything. The installed
Windows app remains approved Model7. The browser stages current development
source with small platform adapters; it does not replace Windows source files.

## Build and boundary

Run `python tools/build_web.py` from this project using installed Godot4.6 stable
standard and its matching single-thread Web template. Optional `--godot` and
`--template` select those installed files. No download or deployment occurs.
Each build creates a new `output/web-builds/<id>/` containing staged source,
isolated editor settings, import/export logs, raw export, site and SHA256 inventory.
`web/procedural-assets.json` allowlists six original procedural example files by
hash. Private game/model/art files, converter executables and test output are
excluded. Public handoff packages must contain **only that build's `site/`**,
never all of `output/web-port/`, which includes private native test fixtures.

The browser opens embedded GLB, packed HAS and supported PCM16 WAV through its
own file chooser. Bytes remain in the browser. Save downloads a packed `.has`
using existing ZIPv1/schema3–4, retaining model data, native identities and editable
paint. Download cannot confirm durable OS saving, so it deliberately does not
clear the dirty state. Browser compressed and expanded packages are bounded to
128MiB,128entries,1MiB metadata and ASCII managed internal paths. Linked projects
must first be packed in Windows Studio. The native Python reader is unchanged.

Installed-game browsing, native Source/MMD/FBX/OBJ/glTF conversion workers, OS folder
access, automatic recovery, fill, guided lessons and browser MP4 export are
unavailable with guidance or disabled controls. Existing GLB and packed HAS are the
browser interchange paths. Audio and physics have not received browser acceptance.
WAV chooser support is not a claim of audible playback/export synchronization.
Download HAS before closing; do not rely on browser caches or recovery.

## Actual verification on the frozen preview

Final build `output/web-builds/1793583765273476000` passed five sequential groups,
all exit0, with staged source and public-file SHA checks before/after every group.
The original controller completed; it was not restarted after an observation gap.
Evidence: its `final-checks/state.json` and per-group logs.

- Codec:34checks/0 in headless native Godot against two original practice packages
  and the supplied Mima example; three independent original Python codec readers.
  Includes16 malformed/path/checksum/size/version refusal cases. This group alone
  is not a browser-runtime test or hostile-file certification.
- Real hidden Chrome: New, actual file-chooser room GLB upload, frame24, right-drag
  camera adjustment with explicit K key, independent Draw stroke, filename/Enter
  download, fresh browser context, actual Open chooser and a second download.
  Ready means actual app UI readiness. No console errors or failed requests were
  recorded in the final normal roundtrip. Software SwiftShader was explicit;
  no hardware-browser performance, tablet or artist-usability claim.
- Independent content:26checks/0; same GLB SHA, camera controls at0/24, video
  timing, editable Ink exposure24–47 and exact PNG bytes after fresh-context reopen.
  Camera decimal JSON reparse differs by at most1.1102230246251565e-16; actual
  engine float32 quaternion bytes are EXACT. Every other project value is exact.
  Raw JSON decimal or archive-byte identity is not claimed.
- Actual installed Windows Model7:10checks/0 on both browser downloads, hidden
  GPU app through `run.command()`. Exact engine matrices/Ink bytes; camera motion
  changes1,086,885channels. Separate geometry rebuild differs45channels,
  mean0.000316478587962963 on0–255 scale, within the existing384/.002 bound.
  The same reopened preview and its own exported frame24 are exact. Actual silent
  H2641920x1080/24fps/48frames/2s MP4; no new audio claim. All361normal nonmemo source
  files SHA-verified unchanged; only owned output helpers/evidence added.
- Five startup failures: missing middle engine chunk, same-size corrupt chunk,
  missing engine JavaScript, missing engine-loader helper, missing file helper.
  Each exposes an error without false ready/unhandled page errors. Restoring
  responses and reloading actually starts the editor with the exact engine SHA.
  Tests simulate responses, never alter the frozen files. This does not certify
  every possible engine initialization/filesystem/runtime failure.

Reports in `output/web-port/`: `roundtrip-browser.json`,
`roundtrip-content-verification.json`, `windows-interop.json`,
`download-failure-verification.json`, `final-checks.json`. Their unique run folders
retain actual downloads, images, logs and failed earlier attempts. The content
report's `desktop_gui_pending` records its earlier group boundary; the subsequent
Windows report supplies that proof. Browser tests close their own contexts/server;
the Windows receipt confirms private placement and cleanup, without owner focus.

The earlier five-pixel-test startup spike remains historical evidence. Its failed
blob was initially guessed to be audio-related. Actual MIME/stack/create/revoke
tracing proved it was the replaced window-icon PNG. Browser staging now sets the
original project icon once and skips the duplicate runtime icon replacement;
the final roundtrip has no failed blob request. Audio remains untested. Initial
restricted editor save and file-chooser/timing harness failures remain retained;
later isolated editor-profile exports have clean logs. A trusted chooser click is
required; browser-only unaccumulated input and paced automation passed, without
proving a universal physical-input diagnosis.

## Static hosting contract

Place the exact site tree at `/tools/hybrid-animation-studio/app/`. Preserve names
and companions. Final site:13files,38,809,105bytes; each below25MiB. Keep the included
Godot/bundled library notices. The application's license remains the owner's
decision; no third-party game/model/art is bundled.

Pinned unchanged WASM:37,686,550bytes, SHA256
`2b558bdb3c3af1f822ce6c43e09e1fa844d82fa440fe40d2d25d6c36ddf95137`.
Three same-origin relative parts (16MiB/16MiB/4,132,118bytes) each receive size/SHA
checks, then the reconstructed whole receives its original SHA check. One exact
engine JS fetch line calls the small adapter. Original JS/unsplit export remain
outside the site. Total download size is unchanged; buffering/hashing adds memory
and latency, not a size optimization.

Single-thread Compatibility/WebGL2; no service worker, global fetch interception
or global COOP/COEP headers. Loader preflight happens before engine initialization
because the installed loader otherwise does not forward a rejected load promise.
An outer guard catches missing bootstrap scripts. The shell waits for the actual
app-ready flag, then sends same-origin `has:ready`; startup failures send
`has:error`. There are no inbound message commands. A frontend wrapper must check
message origin/source and owns its visible retry/fullscreen controls.

Primary references: [Godot4.6 Web export](https://docs.godotengine.org/en/4.6/tutorials/export/exporting_for_web.html),
[JavaScriptBridge](https://docs.godotengine.org/en/4.6/classes/class_javascriptbridge.html),
[ZIPReader](https://docs.godotengine.org/en/4.6/classes/class_zipreader.html),
[ZIPPacker](https://docs.godotengine.org/en/4.6/classes/class_zippacker.html).
The [HTML shell reference](https://docs.godotengine.org/en/4.6/tutorials/platform/web/html5_shell_classref.html)
is incomplete; the actual pinned installed loader was inspected too. Browser
gestures, background suspension, storage limits and memory remain platform limits.

This is a tested limited preview candidate, not desktop parity or completion of
the MD/addendum. Frontend independently checks/integrates the frozen site before
any separately authorized publication. Native face inference/assembly, particles,
optional scale fitting and the full retained Studio goal remain active.
