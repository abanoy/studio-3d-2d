# Small derived SFM render/adoption candidate

This is an output-only candidate, not application implementation or GPU proof.
It uses the twelve already accepted Nitori/Keiki GLBs from the fourteen-case
conversion run. No model conversion, Blender, SourceIO, download, game mount or
production/Git change is part of this probe.

The source files are under `source/`. `probe_driver.py` prepares a fresh owned
run and defaults to preflight. `glb_reference.py` independently decodes the
actual derived GLB buffers, sparse morphs, joint/bind transforms and CRC-checked
PNG pixels with Python's standard library. The two GDScript files are copied
into fresh source snapshots; they do not modify the main application's code.

## Bounded future exercise

- Import and inspect all twelve retained GLBs, including both ordinary
  baselines. Verify every as-supplied primitive, exact material identity,
  decoded embedded texture pixels and all native bone names. Record extra
  runtime helpers separately.
- Keep Nitori's coincident glow surface and ordinary PBR materials intact.
  Capture the three skins with one fixed camera/light. Equal-looking skins
  are an observation of the retained glow limitation, not a reason to delete it.
- Capture Keiki Tools at 0, 0.5 and 1 and compare engine-baked world geometry to
  independently decoded derived positions. Verify box/flame remain exact.
- Pose native Keiki box 23 and Nitori hand 8 by 20 degrees. The native index,
  actual used-palette index and source node are explicitly joined by unique
  names and nearest-joint parent identity; those indices are not interchangeable.
  Verify derived point clouds, unchanged components and changed pixels.
  These are eight initial raw captures in total.
- Through ordinary Add model, adopt one Nitori skin-0 bundle and Keiki 000
  with their adjacent parameter reports. Verify one import Undo/Redo,
  unchanged component coordinates, a normal numeric pose and its Undo/Redo,
  complete report/binding/key retention and ordinary packed HAS Save.
- Open those packages in a second process with a distinct source snapshot,
  preference profile and empty unpack cache. Only this run's enumerated copied
  input folder is renamed to `inputs.offline`; original bundles never move.
  Verify exact packed GLB hashes, report/bindings/keys/transforms and writer pixels.

No external preparation report is injected into model data. The normal Add
path already preserves the adjacent report. That is static prepared-bundle
adoption, not a native appearance chooser or runtime skin/bodygroup switching.
The native model, textures, editable blend and complete preparation bundle are
not claimed to be embedded in HAS merely because their report survives.

## Source and execution guards

Preparation requires an exact stable base HEAD. Exact Git mode copies committed
blobs. Root separately authorized the current **working-source** preparation at
base `2a54f252d128e4c800ae608ae798e0041a996b6b`, including its reviewed uncommitted
Wind phase 1 port. This mode explicitly records that copied code is **not**
exact Git 2a54 source, its reviewed context, full functional membership/hashes
and HEAD before/after. The two copied projects and every candidate code file
are separately hashed. The older review note describes the earlier exact-Git
route; this paragraph and the actual manifest describe the working-source run.

The manifest binds all twelve original GLBs, matching parameter/dependency
reports, per-case accepted conversion receipts, the compact native review,
approved windowed Godot/Pythonw, candidate source and the private source copies.
Paths must remain inside this task; links/reparse points, unexpected owned
members, changed hashes/stamps, overwritten paths and stale source refuse.
Original archives/native assets are not opened or changed by this probe.

Default preflight launches no engine. `--parse-only` uses explicit
`--headless --check-only`; it does not run the harness or render anything.
It consumes its prepared run's writer folder. Prepare a **fresh** run for any
later graphics execution rather than reusing a parse folder.

Actual graphics require **both** a reviewed current manifest/hash and explicit
`--run-gpu --lease-confirmed` authorization. The driver uses the existing
private graphical wrapper and rejects missing/wrong private-window confirmation,
foreground activity, unclosed jobs/desktops, nonzero exits, engine warnings,
missing result membership and source/input changes. There is no visible fallback
or retry. Timeout partial output is retained before propagating the failure.
All unsuccessful/partial folders remain; no cleanup is automatic.

After the Wind checkpoint changes, prepare again with its actual stable HEAD:

```text
python -B source/probe_driver.py --prepare --expected-root-revision <40-character-stable-HEAD>
python -B source/probe_driver.py --manifest <fresh-manifest.json> --manifest-sha256 <printed-SHA>
```

Only when the root coordinator reviews the candidate and grants its exclusive
graphics lease may the second command append `--run-gpu --lease-confirmed`.
Do not run these source files directly from a future experiment archive; recreate
this owned `<checkout>/output/sfm-static-appearance-probe-20261113/source/` layout.

## What is and is not proved

CPU controls and check-only parsing are preparation evidence. The actual GPU,
normal app adoption, Undo/Redo, packed writer/reader and screenshots are still
**UNRUN**. If they later pass, that establishes derived-GLB renderer/app behavior.

Native Source visual/deformation fidelity remains separate: Nitori's genuine
missing `hairbump.vtf`, native additive/environment/Phong/warp behavior,
VTX face/UV assignments, VVD weights, native flex deltas and VTF pixel/gamma
semantics have no independent native renderer oracle here. The image called
black contains opaque greys 0/40/120. Runtime variants, jiggle, component
assembly, app shape-selection UI, linked HAS, movies, device/owner acceptance
and the rest of the 82-MDL corpus are outside this first exercise.

Raw GLBs, decoded point arrays, snapshots, packages and screenshots stay private
in this task's owned output. Promote only reviewed source and compact evidence.
