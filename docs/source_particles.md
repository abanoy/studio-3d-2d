# Installed Source particles: experimental sprite adapter

The later [canonical scene integration](particle_scenes.md) adds ordinary
development project-time sampling, schema5/world2 persistence, linked/packed HAS,
recovery and Studio Export with independent drawing/audio. Browser/editor controls
remain unfinished and the normal installed app is unchanged. The first foundation
checkpoint and its narrower proof below remain historical evidence.

## First foundation boundary — 2026-11-02 at2011 EST

There is now a small actual rendering experiment, separate from the normal
application. It converts two selected installed effects into the same
`studio_sprite_effect_1` descriptor and a decoded PNG, evaluated by one shared
GDScript sprite renderer. The first is SFM `Explosions_MA_Flash_1` from
`tf_movies/particles/explosion.pcf`; the second is Workshop `vFire_Glow_Tiny`
from item1525218777's `particles/vfire_base_big.pcf`. These are individual childless
systems, not the complete explosion/vfire families. The GPU uses their resolved
installed textures, not replacement procedural glow artwork.

This is **not normal in-app importing, particle selection/editing, ordinary Export,
or portable HAS support**. The opt-in fixture invokes the existing renderer and
encoder directly. Model versions1–8, the world format and ordinary editor remain
unchanged; an older reader must eventually reject required particle semantics
explicitly. No particles are silently hidden in generic mesh extras.

The new tools are `tools/source_particles.py`, `particle_effect.py` and
`prepare_particle_effect.py`. Resource lookup uses selected-provider precedence
and the existing installed mount order, including folder/GMA/VPK materials.
Only PCF/VMT/VTF data is read: no game launch, Lua, proxies or executable add-on
content. Each PCF/resource is bounded to8MiB, aggregate reads64MiB, GMA512MiB,
system graph50000 elements and256 operators per group. Preparation enforces
512MiB process commit/30CPU seconds, with65-second parent timeout in the verifier.
No dependency was installed. The pinned optional SourceIO datamodel and existing
Windows ABI3 native VTF codec are loaded directly without Blender. Redistribution
of that codec/dependency remains a packaging review, not a new license grant.

Supported interpretation: one camera-facing additive static sprite renderer,
one continuous or instantaneous emitter, seeded initial lifetime/radius/alpha/
color/rotation/sphere position/velocity/offset, analytic constant gravity and
age-based alpha/radius/color curves. Native vectors map x,z,-y at0.01905m per
Source unit. Preparation bakes an own Park–Miller random stream; this is a bounded
HAS approximation, **not Source random/distribution/operator/shader equivalence**.
There is no wall-clock tick or export-time rerandomization. Total births and live
capacity are limited to1024; duration is at most60s. Capacity overflow refuses the
effect rather than dropping births. Descriptor setup is transactional, and a
nonfinite evaluated time reports an error while preserving the last GPU state.

Unknown groups/operators/parameters, duplicate operators, children, forces,
constraints, active operator timing, nonzero drag, moving/control-point-dependent
behavior, local directional velocity, snapshots/replacements, screen/viewmodel
effects, nonzero sequences and multi-frame instantaneous emission are refused.
Known culling, sorting and performance hints remain in the report without native
simulation. Materials admit only the explicit simple additive SpriteCard/
UnlitGeneric subset. Textures currently require flat single-frame VTF7.2 with an
80-byte header, up to4MP; newer resource tables/sprite sheets, cubes, volumes,
animated textures, float pixels and other shaders are refused. This intentionally
restrictive first adapter is not a promise that every simple native effect works.

The canonical renderer uses a MultiMesh and textured billboard shader with depth
testing and no shadows. Uniform parent scale/translation and rotated cameras are
tested. Nonuniform parent scale, attachments, dynamic framing/culling (currently
a fixed local±1000 box), pick/selection proxies, performance profiling and broader
source fidelity remain open. The independent drawing overlay still composites
after the3D picture. No owner asset is changed.

### Actual acceptance evidence

`python -m unittest discover -s tests -p test_source_particles.py`:11 tests, exit0.
`python -u tests/verify_particle_sprite.py`:29 writer+27 cold checks, exit0;
two accepted private desktop receipts, no foreground child observed and jobs/
desktops closed. These are new focused checks, not a new complete app regression.
The verifier needs the retained installed-PCF research inventory and actual local
games; missing native data fails rather than inventing a skipped native pass.

Latest evidence is `output/particle-sprite/1793668026558113500` and
`output/particle-sprite-verification.json`. Two earlier runs remain separate:
the initial19+17 checks and the strengthened29+27 before final parameter guards.
Accepted source files stayed unchanged during the final run. Exact PCF/GMA SHA256
and modification times remain unchanged. Each packet retains selected native
PCF/VTF/VMT data, material resolution provenance, descriptor and texture hashes.
Native packets and images stay in ignored private output, never the source ZIP.

Both systems have97 exact forward/reverse half-frame samples. Reverse seeking
reproduces identical rendered pixels. Actual flash/glow change40336/3176 sampled
pixels respectively; the flash is broad/bright and the tiny glow is visually subtle
in the full-room image. The cold engine repeats exactly after moving only owned
native packet copies aside: it consumes JSON+PNG, without native parsing/game
lookups. Authored controls separately prove known velocity/gravity, identical
uniform-parent/world-space pictures, rotated-camera visibility and full depth
occlusion. Editable cyan ink bytes and original room data are unchanged.

The fixture exports a real silent H.2641920×1080,24fps,48-frame,2s movie. Frame2's
pre-encode PNG exactly equals the corresponding preview. This is not a claim of
lossless H.264 pixels, audio-with-particles coverage, ordinary editor particle
export or whole-scene cold HAS loading. Both saved flash/glow images were visually
inspected. Source-specific artistic fidelity/owner acceptance remain open.

Next: version the common scene effect contract with explicit old-reader failure,
then dependency packing/cold HAS, world placement and project-frame timing, before
adding a simple choose/place/time browser workflow. Amount/attachment and broader
operators follow tested increments. Keep the installed editor separate until a
concrete reviewed update is ready.

Primary implementation references: [Godot4.6 MultiMesh](https://docs.godotengine.org/en/4.6/classes/class_multimesh.html),
[Valve's VTF declaration](https://github.com/ValveSoftware/source-sdk-2013/blob/master/src/public/vtf/vtf.h)
and [Valve's Bias math declaration](https://github.com/ValveSoftware/source-sdk-2013/blob/master/src/public/mathlib/mathlib.h).
The descriptor, preparation adapter and renderer are original implementation;
no Valve engine code was copied.

## Earlier research and requested workflow

The owner explicitly requested GMod/SFM particle effects, including installed GMod
Workshop packs, on2026-11-01. Use the installed-game content paths already supported
by the browser. Do not bundle game assets or require a particular Workshop item.
Keep the few-tweak workflow: choose an effect, place/attach it, set its timing and
simple amount, then preview/export from the same scene clock.

## Actual local evidence

A read-only survey using the existing mounted-content discovery and bounded GMA/
VPK index readers found563 providers and261 `.pcf` file entries across18 particle
providers. Entries include duplicate mounts/cached add-ons and are **not**261 unique
particle systems. A PCF can contain several systems. The survey did not extract
assets, execute addon code, launch either game, install dependencies or render an
effect. Evidence is `output/installed-particle-inventory.json`; the survey helper
is `output/inspect_installed_particles.py` and is deliberately outside production.

Observed content includes GMod loose particles, HL2 VPKs, local add-ons and Workshop
packs such as242776816,1525218777/vfire and1551310214/PPEv11. SFM's declared paths
provide particles under `tf_movies`, `tf` and `hl2`. SFM is installed, but neither
its declared `game/workshop` directory nor local Steam Workshop1840 content exists
in this observed discovery. Refresh/search must handle that absence gracefully.
Two GMod Workshop archives (2563582365 and2588046325) were refused by the existing
index reader as unsupported GMA versions. Compressed legacy providers were not
decompressed during this survey. These are explicit coverage gaps.

The current source browser lists models/maps, and resource staging admits only
their model/material/map paths. `.pcf`/`particles` are not yet supported there.
Finding files is not import or playback support.

### Actual system decoding experiment

The next read-only experiment successfully decoded six real PCFs using only the
already installed pinned SourceIO `datamodel.py` reader: GMod antlion blood,
Workshop vfire and PPEv11, plus SFM chemspill/explosion/spitter files covering
binary2/3/4/5 and PCF1/2. They contain750 system definitions (2/101/567/10/41/29),
not750 rendered effects or750 fully supported imports. The bounded workers read
8MiB-or-smaller inputs, enforce512MiB process commit and20CPU seconds, and have a
30-second parent timeout. Observed peak commit stayed below37MiB. Selected GMA
payload CRC/SHA and source stat preservation were checked. No files were extracted
into the games, no addon scripts ran, no model was downloaded and no effect was
rendered. The parser module was loaded directly; the SourceIO Blender addon was
not launched. This is a local research adapter, not production importer adoption.

Reports: `output/particle-system-research.json`, its per-run result/log files and
`output/particle-operator-summary.json`. Parameters, child names and material
references are retained in the later research run. Across the samples there are
85 group/operator categories and143 distinct material reference strings. Common
features include random lifetime/radius/color/position, continuous or instant
emission, basic movement, sprite rendering and alpha/radius fades. Other systems
use noise/remapping, control-point locking, ropes/trails, forces and nested children.
The material names include VMT references; their textures/shaders/atlas sheets are
not resolved or converted by this experiment. Simple-looking children must not be
treated as a complete imported parent effect. Source-time simulation/rendering
support remains unimplemented.

## Technical direction and boundaries

Valve's [particle entity implementation](https://github.com/ValveSoftware/source-sdk-2013/blob/master/src/game/server/particle_system.cpp)
shows effect names, start state/time, parenting and control-point relationships.
The [ValvePCF author's class documentation](https://pysourcesdk.github.io/ValvePCF/api/classes.html)
describes a PCF collection of systems with emitters, initializers, operators,
renderers, forces, constraints and children. This motivates a data adapter rather
than treating the file as a mesh or assuming a single effect. No Valve engine code
is copied here. No new parser dependency has been installed. The existing pinned
SourceIO tree contains a DMX datamodel reader, used by the bounded research pilot
above. Production adoption still needs compatible bounds and an actual effect
adapter; parsing the research samples is not particle playback support.

Next bounded increment:

1. Extend the completed six-file PCF inspection to material resolution and a
   deliberately supported effect; retain hashes and report unsupported data.
2. Extend discovery/staging for particle data and material dependencies without
   admitting executable addon files. GMod Lua-created effects need a separate
   compatibility decision; do not execute arbitrary Lua to pretend support.
3. Define a versioned native HAS effect descriptor and explicit supported operator
   subset. Preserve source identities/control points, textures and provenance;
   unsupported operators/children must produce a visible limitation report.
4. Build one small actual effect through deterministic project-time sampling, with
   fixed seeds, reverse seeks and preview/final agreement. Then portable HAS/cold
   Open and MP4. Frame sampling cannot depend on a new uncontrolled simulation at
   export time. Attachment, clipping/lifetime and parenting need explicit tests.

The native render/simulation adapter, standard descriptor, importer, selection UI,
timeline controls and dependency packing are unfinished. Exact Source shader/
operator equivalence is not promised. The owner's first-use artistic/speed goal
remains OPEN; the particle request supplements the original 3D/camera/independent
2D/audio/HAS/MP4 workflow and does not replace it.
