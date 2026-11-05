# Canonical particle scenes — development integration

The later [installed browser/basic controls](particle_browser.md) now uses this
contract in development. Its isolated UI checks and eight-group integrated
affected review pass. The full regression described below belongs to the
earlier frozen backend/fill snapshot, not a new complete UI regression.

The source adapter and common sprite renderer now participate in the ordinary
development scene runtime, Save/Open, recovery and Export workflow. This is a
backend increment; the later browser adds creation, selection and basic static
placement/timing controls. Animated transforms, attachment and amount controls
remain unfinished. The verified normal installed Studio folder is unchanged.
Developer fixtures created the first scenes through the same world transaction
the editor now uses.

## Versioning and compatibility

Existing worlds keep `studio_world_1` and project schema4. A world containing
effects uses `studio_world_2` and schema5. It retains the same `objects` array and
standard Model1–8 contracts, adding an explicit `effects` array, at most16 entries.
The HAS ZIP container remains version1: its project metadata explicitly requires
schema5. Actual old Storage and HAS worker source from checkpoint4e8e51788 were
executed against the new project and reject it. New readers still read schema1–4.
No native effect is hidden in mesh extras or silently discarded by an older reader.
An unversioned effects field on world1, or mismatched world/project versions, fails.

Each `studio_particle_instance_1` retains:

| Field | Meaning |
|---|---|
| `id`, `name` | Stable unique scene identity and display name; separate instances can share data |
| `source`, `sha256` | Prepared canonical sprite JSON and its exact hash |
| `texture_source`, `texture_sha256` | Decoded PNG and its exact hash; matches the descriptor's texture binding |
| `position`, `rotation_xyzw`, `scale` | Independent root placement with normalized rotation and uniform scale |
| `start_frame`, `end_frame` | Project frames; start included, end excluded |
| `source_in_seconds` | Trim into the prepared effect; must begin before its duration ends |
| `visible` | Independent instance visibility |

Managed saves replace the two source paths with `assets/<hash>.json` and
`assets/<hash>.png`. JSON and texture assets deduplicate across instances; the
original native PCF/VTF/VMT and game installation are not required for playback.
Linked mode includes both dependencies and uses the existing locate/relink flow.
Unknown instance fields and invalid IDs/placement/timing/paths/versions fail
instead of silently ignoring future semantics. Models cannot parent to effects;
attachments are not part of this first scene contract.

## Clock, preparation and resources

The shared runtime computes local age as
`source_in_seconds + (frame - start_frame) * fps_den / fps_num`. Seeking backwards
reuses the exact prepared seed values. Evaluation without a new clock retains the
last valid project rate; an invalid explicit rate reports an error and preserves
the previous state. There is no separate real-time particle simulation at export.
Instance clip ends can crop an effect; sampling beyond the prepared duration
naturally returns no particles. Looping/retriggering is not implemented.

All assets are checked before replacing an installed world. Each prepared JSON is
at most1MiB, PNG at most8MiB/4MP, total decoded particle image bytes at most64MiB,
and total prepared births at most8192. Per-effect limits from source_particles.md
remain in force. PNG IHDR dimensions are checked before decompression; descriptor
format/curves/capacity and texture identities are validated before allocating GPU
instances. Preparation is synchronous and bounded; stall/latency optimization and
texture-cache eviction are still unfinished. Aggregate caps are conservative and
count repeated instance textures as decoded inputs before GPU texture sharing.

The MultiMesh now computes a conservative bound from the currently sampled sprite
centres/radii, replacing the first experiment's fixed±1000 box. A real GPU control
5000 units away remains visible through the same shader. This fixes culling;
editor selection/framing still does not include particle geometry. Nonuniform
parents, source shader/simulation equivalence and performance profiling remain
outside the supported subset.

## Actual verification

Focused `tests/verify_particle_scene.py` passes25 writer+4 cold checks. It uses the
two exact retained prepared native SFM/Workshop packets, original procedural room,
editable cyan ink and an authored48kHz tone. Tests use ordinary `restore_world`,
linked/packed HAS Save/Open, recovery and `app.export_movie`, with private Windows
desktops throughout. Reopen clears HAS identity and requires a newly installed
runtime, avoiding a false pass from the previous still-open scene.

The fresh reader opens packed HAS after moving only the test's owned input folder
and writer cache aside. It restores both effects, exact timing, complete room/
particle/camera/ink pixels and delayed PCM audio without a game/native parser
lookup. Export is an actual H.2641080p24/48-frame movie with AAC; frame14's PNG
exactly equals preview frame13. Decoded AAC onset is1.000020833s for a sound placed
at frame24. This is a timing assertion, not a hearing or lossless-codec claim.
Reference image was visually inspected; artistic Source fidelity remains open.

Evidence: `output/particle-scene/1793669158267605900` and
`output/particle-scene-verification.json`. Container tests now have31 cases
(including6 particle-specific cases), and particle data tests11. Expanded sprite
controls pass31 writer+29 cold checks, including depth occlusion, parent uniform
placement, rotated cameras and distant bounds.

The first integration run exposed JSON float/integer membership differences,
which initially broke old/new world loading. Numeric equality fixes the gate.
Its weak linked-reopen assertion was replaced with fresh-runtime proof. The
fixture's first export used a nonexistent folder/misread the API's error return;
both were corrected. A subsequent bounds edit needed an explicit Vector3 type;
its failed private test was stopped by its exact owned PID, and the launcher
closed its job/desktop. Those failed runs remain retained, not counted as passes.
No production test tolerance was weakened.

The complete current `tests/verify.py` regression and separate `verify_has.py`
have now terminated0 on unchanged functional source. The orchestration also ran
the31 HAS Python cases,11 particle-data cases and31+29 sprite controls, all0.
Together with the focused scene reader/writer, 128 fresh private graphical
receipts are accepted; every job/desktop closed with no foreground child observed.
Evidence: `C:\Users\noble\.codex\worktrees\ec34\cloudflare\hybrid-animation-studio\output\particle-scene-regression\1793671475083491800` and `output/particle-scene-regression.json`.
This verifies the existing full suite on this source, not every spec/addendum
requirement, native asset or clean-machine/physical-input/artist-quality behavior.
The normal installed application and frozen web artifact remain unchanged.

The first full entry point stopped at a real drawing UI regression: resized
Properties clipped Fill's preview Apply/Cancel controls. No particle assertion
failed. That run and screenshot remain separate failed evidence. A deferred,
cancel-safe scroll reveal fixes the controls without changing fill pixels/history;
18 unit+48 app checks and real pointer Cancel/Apply pass. The fresh full run
includes this fix and reruns the particle scenes. See drawing_fill.md. The old
session89284 is terminal1; the replacement session64328 has now also terminated0, with its final
logs selected by `output/particle-scene-regression.json`. Do not restart a live
job merely because observation times out.

Next: the installed Source browser's data-only PCF discovery and system selection,
explicit supported/unsupported guidance, then simple place/time controls with
Undo. Broader operators, attachment, amount and native provenance UI follow
separate tested increments. Keep original source assets and the main
3D → shot camera → independent2D/audio → HAS → MP4 workflow intact.
