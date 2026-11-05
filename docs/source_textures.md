# Source texture row correction — development

The Source bridge previously copied decoded VTF pixels directly into Blender's
Image.pixels buffer. The codec returns rows from the top; that buffer starts at
the bottom. Consequently exported GLB textures were vertically inverted relative
to their existing mesh UVs. This affected both SFM and GMod preparations, rather
than being an SFM installation issue or merely approximate lighting.

The shared boundary now reverses rows once before setting Blender pixels. Columns,
RGBA channels, Source UVs, geometry, rig data and original assets remain unchanged.
No different source-family model format or runtime correction is introduced.
Particle PNG preparation has its own correct top-down PNG path and is unchanged.

The original asymmetric2x2 VTF diagnostic proved that direct image assignment
disagrees with loading the corresponding PNG, whereas row reversal matches.
Evidence: `output/source-orientation/1793677311309369500`. A separate copied bridge
then re-prepared Scout without changing production source; before/after images
were rendered on a private desktop and visually inspected. His shirt/skin/shorts/
wraps/shoes return to their expected regions. Evidence:
`output/source-orientation-candidate/1793677354510729200`. Eyes still use an
incomplete native eye-shader approximation; this change does not fix them.

The production boundary is `tools/source_texture.py`, used only by the offline
Source Blender bridge. Its actual Blender test creates authored uncompressed
VTF7.2/PNG pairs at2x2,2x3 and3x1, including mixed colors and partial alpha. Native
decoded bytes match the authored data. Production image buffers match independently
loaded PNG buffers with zero difference; malformed three-channel data refuses.
This tests real codec/image behavior rather than assuming the two row conventions.
Run `python -u tests/verify_source_texture.py` using the existing installed tools.

The thirteen-group affected regression completed with all commands exiting0 on
unchanged functional inputs: texture boundary, actual standalone SFM Scout/box16,
actual GMod model/map32, host/preflight/browser tests, particle data/UI29+5,
existing CSS/cross-addon browsing, workspace/world/HAS/fill. Nine fresh private
graphical receipts are confirmed/closed/no foreground child observed, plus one
earlier isolated comparison receipt. Evidence: `C:\Users\noble\.codex\worktrees\ec34\cloudflare\hybrid-animation-studio\output\source-texture-review\1793677484987036600` and
`output/source-texture-review.json`. This is an affected review, not a new full
verify.py pass. Fresh corrected SFM and GMod images were visually inspected.

## Existing projects and limitations

The later [neutral Source eye increment](source_eyes.md) adds a native iris with
an explicit static approximation. Refraction and animated gaze remain unfinished.
The earlier images and row-fix verification above keep their original scope.

Already saved GLBs/HAS projects retain their exact embedded texture bytes and
appearance. This patch applies when preparing a new Source import. Reimport into
a separate scene to compare; the app does not rewrite existing projects or swap
their assets automatically. A future explicit asset-refresh workflow remains open.
Normal installed Studio and the frozen web preview have not been updated.

This is a pixel-layout fix, not complete native Source materials: eye refract,
normal/specular/detail/proxy behavior, wrinkle maps, animated textures, layered
materials, baked lighting and other shader semantics remain incomplete. MMD and
common-format importers do not call this boundary. No artistic-quality or complete
native-model acceptance follows from texture-presence or exact roundtrip checks.
Large-scene memory/latency and clean-PC/physical-input acceptance remain open.
