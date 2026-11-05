# Installed Source particles: requested compatibility, not implemented playback

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
