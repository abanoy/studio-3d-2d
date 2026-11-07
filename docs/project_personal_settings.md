# Project settings and personal controls

Opening a project restores its content and scene settings. It keeps your personal
controls and does not ask whether to replace them. The tentative alternative
load-prompt policy has not been introduced.

| Ownership | Current values | Persistence |
| --- | --- | --- |
| Project content | Camera/world/pose/visibility tracks, independent cels, palette, audio | HAS, directory save and recovery |
| Project scene settings | Native canvas, frame rate, duration, delivery size, lighting, background, visibility fade | HAS, directory save and recovery |
| Personal preferences | Interface scale, fly/orbit controls, shortcut bindings, dock arrangement | Separate preference files; never imported from a scene |
| Session/export controls | Advanced view, height-review offer, encoder path, export quality/PNG mode, recovery choices, brush settings/tool | Retained across New/Open during the active session; not claimed to persist at restart |

The current theme is fixed. This work adds no theme choice, preference prompt or
application behavior. It verifies the existing boundary. Per-export quality is
explicitly an export/retry choice; it is distinct from the project's saved native
canvas, delivery size, lighting and timing.

```sh
python tests/verify_settings_matrix.py --isolated-display :109 --output /absolute/new/result
```

Linux requires an already provisioned private display; Windows uses the existing
private launcher. The November 7 run passes 29 writer checks and 10 checks in each
of two fresh readers. Both readers open both projects with the owned original map,
voice file and writer cache offline. Each uses its own saved personal preferences
and explicitly seeded session controls. Project pixels/PCM/settings repeat exactly;
New, directory/recovery Open and malformed Open preserve the personal choices.
Normal project manifests contain no personal preference slots. Existing preference
bytes and an unrelated preference section remain intact.

Project A uses a 960×540 canvas, 1280×720 delivery, 30000/1001 fps, 61 frames,
unshaded lighting, black background and instant visibility. Project B uses a
1920×1080 canvas, 960×540 delivery, 24 fps, 48 frames, studio lighting, blue
background and a 725 ms fade. Both actual H.264/AAC movies match those delivery
settings and the resampled native preview; voice begins at samples 38439 and 48001.

[Curated evidence](benchmarks/settings_matrix_2026-11-07.json) covers STORE-03's
software ownership condition. Platform/device and native-format acceptance remain
separate. The related [posed reference case](posed_references.md) separately covers
saved root/arm interpolation and working-versus-final reference settings.
