# Browser target

This target reuses Studio's renderer, native model data, camera, timeline and
independent drawing. It is a **browser preview under development**, alongside the
Windows app. The Windows entry points remain unchanged.

`python tools/build_web.py` stages an isolated project under `output/web-builds/`,
uses the installed pinned Godot 4.6 standard and single-thread Web template, and
creates a size-bounded static site under `tools/hybrid-animation-studio/app/`.
It never deploys. Only checksummed original procedural examples are included.
Keep all generated files and their names together; serve through localhost/HTTPS.

Browser inputs are embedded GLB, packed HAS and supported PCM16 WAV. Local file
bytes stay in the browser. Save downloads a packed copy using the existing HAS
ZIPv1/schema3–4; it does not confirm an OS save or clear unsaved work. Browser
archive/expanded data limit128MiB, ASCII internal managed paths,128entries and
1MiB metadata; linked projects must first be packed in Windows Studio. The native
Windows reader remains the independent interoperability check.

Installed-game browsing, native Python/Blender conversions, local folder access,
automatic recovery, fill, guided lessons and browser MP4 export are unavailable
here. Audio and physics still need browser acceptance; do not claim desktop
parity. Windows Studio can open browser-authored HAS and export MP4.
See `docs/web_port.md` for actual verification and known failures/limitations.

The engine is split into checksummed16MiB parts to fit static-host per-file limits;
total download size and startup memory remain substantial. The loader changes
one engine JavaScript fetch line. The original raw export is retained outside the
site. No global fetch patch, service worker or isolation headers are required.
The shell preloads the engine before initialization so rejected downloads propagate,
then waits for the actual app-ready flag. Parent notifications are same-origin,
one-way ready/error signals. No message commands are accepted.

Godot and its bundled libraries retain their own notices; the app's license is
still the owner's decision. No third-party game/model/art files are bundled.
