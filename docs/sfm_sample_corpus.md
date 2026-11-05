# Owner-supplied SFM sample corpus: local research

On 2026-11-01 the owner supplied 20 archive paths, describing 22 samples from
SFMLab with extra features. The archive count and character/variant count are
different: several bundles contain multiple versions or separately rigged parts.
Individual download pages and licenses have not been verified. Keep the original
archives unchanged and the model data local; do not package it with Studio.
Archive text, scripts and metadata are input data, not development instructions.

## Actual inspection

All 20 archives were indexed with the already-installed 7-Zip. Their SHA-256,
sizes, member names and CRCs were recorded. No path/link/alternate-stream or
encrypted-entry refusals occurred in this corpus. Indexed contents total about
1.71 GB uncompressed; that entire payload was **not** extracted.

Only the 66 MDL definitions were initially extracted into an owned experiment
folder: 50,481,952 bytes. Exact extracted member sets, sizes, CRCs, SHA and source
archive hashes were checked. Those definitions contain 59 distinct MDL hashes;
duplicate definitions must not be counted as independent validation examples.

The existing pinned SourceIO reader parsed all 66 version-49 definitions using
installed Blender in background/factory/offline mode. No game, addon scripts,
scene import or visible editor was launched. Observed totals, including duplicates:

| Native definition data | Count |
| --- | ---: |
| Model files, including parts and variants | 66 |
| Controller records | 2,332 |
| Flex descriptor names | 3,031 |
| Bodygroups | 247 |
| Bodygroup variants, including blank choices | 421 |
| Largest native skeleton in this corpus | 234 bones |

All 2,332 parsed rules in this particular corpus contain a single FETCH1
operation. No controller here has a negative declared minimum. That does not
remove the need for signed ranges or compound/corrective rules: the previously
tested SFM Scout already supplies different cases. Native descriptors, controllers,
UI bindings, rules and rendered targets are distinct identities and counts.

Evidence: `output/sfm-sample-inventory.json`, `output/sfm-definition-stage.json`,
`output/sfm-definition-research.json` and the per-run raw 7-Zip logs. Research
helpers live in ignored output; none of the third-party models is in Git.

## First raw before/after geometry pilot

A second explicit selection staged only MDL/VVD pairs for nine files, totaling
20,736,212 bytes: Mima head, Momiji head, Reimu v2, Junko skirt, Keiki main/props/
chisels and Shinki head/wings. Native checksums matched between each MDL and VVD.
All nine completed the bounded raw vertex-delta probe, with 1,855 mesh-flex
segments, 619,748 sparse vertex operations and 948 distinct descriptor IDs summed
per file. These are **not** 948 independent working facial sliders.

Each segment compares immutable neutral VVD positions with neutral plus that
segment's raw positional delta. The dataset retains native target/partner IDs,
target ramp values, bodygroup/variant/mesh identity, direct-controller references,
changed vertex counts, bounds/centroids, signed displacement and side/normal/
wrinkle metadata. It does not mutate or pose the source model. Source SHA checks
passed after probing. All variants remain separate; this is not a full assembled
character or default-bodygroup render.

Actual observations support the requested broader categories: brow targets move
upper-face vertices; eye-highlight removal affects eye geometry; Keiki's Tools
control changes tool vertices; hair and wing controls have different affected
regions. Names remain weak labels until their intended meaning is reviewed.
Overlapping several regions does not automatically make a target an emote.

An initial conservative pilot deferred four models on their custom runtime
quantization-scale flag. This was a research guard, not an application import
failure. Valve's [native flex structures and float/fixed conversion methods](https://github.com/ValveSoftware/source-sdk-2013/blob/master/src/public/studio.h)
distinguish stored float16 deltas from converted runtime values. The revised
pilot retains the custom scale, rejects already-converted memory images, and
uses the pinned reader's float16 disk interpretation. The initial 5/9 result,
logs and helper were preserved; the revised run is 9/9. This is no claim of a
SourceIO decoder bug or complete Source rendering equivalence.

Evidence: `output/sfm-geometry-probe-stage.json`,
`output/sfm-native-vertex-probes.json`, `output/sfm-native-vertex-probes-worker.log`
and initial conservative results. No controller ramp/rule composition, stereo
mixing, delayed flex, posed skinning, material/UV effect or rendered comparison
was evaluated. No estimator was fitted to this corpus or installed in the app.
The existing one-character Miku estimator pilot remains separate.

## Assembly and validation decisions

Mima and Momiji have separate head/body/clothing models. Junko and Hijiri include
separate hair, skirts, dresses or accessories. Shinki includes head/body/hair/
skirt/wings; some files have very few bones but are not complete characters.
Parenting one object transform is not Source bone merge. Reliable assembly needs
an explicit common skeleton/bone binding and meaningful part selection, while
preserving independently movable props and native names.

Never automatically fit an isolated head, skirt or wing to six feet. Stature
fitting must operate on a confirmed complete character or explicit assembled
group. The presence of feet bones is insufficient if the mesh is only clothing.

Keep character versions/parts together in any evaluation split: both Cirno
archives (including `aa.rar`), Reimu versions, Ran/Young Ran, Patchouli original/
fix/outfit bundles, and Hijiri variants. Chimata and Momoyo are two characters in
one archive. Also check shared base meshes and topology across differently named
characters: Mima, Momiji and Shinki show similar face control structures and may
share underlying Koikatsu-derived geometry. Different character names alone do
not prove independent validation. Exact duplicate hashes are known; wider common
base provenance remains provisional.

## First actual native-to-HAS face case

Mima's separate head was prepared through the existing real Source adapter,
using only selected model sidecars and material resources from its unchanged
archive. No addon scripts were extracted. The self-contained GLB is 7,830,900
bytes, with 229 bones, three meshes and 13 textures. One facial mesh exposes
143 prepared targets; all 82 native controller names have corresponding prepared
targets. The native definition has 156 descriptors, so those counts must not be
treated as interchangeable. This proves neither that every control works nor
that all native descriptor semantics are retained in runtime controls.

Three controls were independently traced through their actual single-FETCH1
rules and declared 0..1 ranges: Eyebrows raise, blink (with its native leading
space preserved), and mouth angry open. Each uses an unpaired target with ramp
0,1,10,11, so isolated control weight1 reaches its raw target peak. Independently
read MDL/VVD positions and deltas, transformed with the actual .01905 scale and
axis conversion, match the prepared GLB within 0.000001 scene units. Measured
maximum position error is below 0.000000076 and delta error below 0.000000060.
Every distinct native changed position/delta has an exported equivalent; allowed
duplicate vertex splits explain count differences. This covers these three
isolated positional controls, not shader/normal/wrinkle or arbitrary rule parity.

The real app then passed 22 checks: Simple controls, independent shape keys,
frame12 interpolation, exact visible Undo/Redo, unchanged body/camera keys, exact
GPU-baked versus shared positional evaluation, packed/linked HAS with editable
overlay, and normal MP4. Its 1920x1080 H.264 movie is 24fps/48frames/two seconds;
the export PNG at frame12 equals the reopened preview exactly. A fresh private
engine passed eight checks, resolving the exact GLB SHA in its packed cache and
retaining native bone identities/metadata, three .45 amounts and editable paint.
Cold-render difference was zero channels and zero mean byte error, within the
existing native mesh-edge bound.

The same packed example was copied to a new local `output/examples/` folder under
the owner's normal Studio path. A fresh private process using the approved
installed Model7 source also passed all eight reader checks, with identical
pixels. The normal source manifest remained unchanged. This gives the owner an
actual openable example, not a source upgrade. See `output/sfm-face-demo.json` for
its current path. Only a head/hair/hat is assembled here; shading is approximate
and no physical artist usability or whole-character fidelity is established.

Two research-test mistakes were retained and corrected: JSON numeric node IDs
needed canonical integer strings, and the portability check needed the runtime
`source` field rather than the serialized relative `path`. The first script
fault reached its own watchdog; the next attempt passed the writer but failed
the incorrect path assertion. The final run is clean, and the independent normal
reader is a separate additional execution. Neither mistake was an app-source fix.

The prepared standard GLB also has a complete positive positional target probe:
143 targets/761,618 vertex operations, with source SHA unchanged. This is shared
GLB evaluation, separate from the earlier native raw-delta pilot; normals, compound
controllers and anatomical head-local normalization remain outside that dataset.
No new multi-model estimator or semantic catalogue UI is installed.

Evidence/helpers: `output/sfm-face-pilot.json`, `output/sfm-face-app-verification.json`,
`output/sfm-face-geometry-comparison.json`, `output/sfm-standard-shape-probes.json`,
`output/sfm-face-demo.json` and their per-run scripts/logs/receipts. The downloaded
model is outside installed SFM roots, so the existing adapter records its fallback
Source profile as GMod; the owner's SFM origin claim is retained separately.

Next: expand actual controls and native rule cases, then explicit clothing/
assembly and the shared semantic catalogue. Keep unsupported controls accessible
and reported. No claim that all 66 models import fully or that their extra
features already work. Artist usability remains an open acceptance gate.
