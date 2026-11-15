# Derived SFM probe v2: source ready, engines unrun

This is an output-only replacement candidate copied from the five archived source files under `experiments/source_appearance/derived_probe_candidate_20261113/source`. It fixes four harness defects. It does not modify HAS, the old candidate, the twelve accepted GLBs or their native inputs. Preparation, parsing with Godot, graphical rendering and application acceptance have not run for v2.

## Bounded corrections

1. The child environment pins `HYBRID_PYTHON` to the approved `C:\Program Files\Python313\python.exe` and `HYBRID_GODOT` to the approved Godot 4.6 executable. The manifest protects python.exe, pythonw.exe and Godot. Each future phase records only these explicit overrides and executable stamps. The parent environment is restored even on error. The private graphical wrapper and strict desktop receipt fields remain required.
2. Final verification independently examines protected originals/runtimes/candidate source, root HEAD and functional hashes, derived reference, both private source memberships, then full manifest/context/owned-input membership. Exceptions such as missing files become retained failed gates. Any false gate changes the retained status to `FAILED_PRESERVATION_RETAIN_ALL`, and only then raises for nonzero exit. Earlier phase errors remain in the receipt. The final check knows whether this run moved its own copied inputs to `inputs.offline`.
3. The existing ordinary writer and reader images must each contain more than 100 significant samples on a four-pixel grid, with maximum RGB contrast above 0.02 relative to their top-left background sample. This uses the same captured Image and adds no second readback. Exact writer/reader pixel equality remains required. This guards equal blank frames, not native appearance fidelity.
4. The raw pose helper retains the imported local quaternion, applies `base_rotation * delta`, and retains position/scale. The independent GLB reference composes `T * R_import * R_delta * S_original`, and refuses posed matrix targets or nonpositive scales rather than guessing a decomposition. The exact native-name/parent to GLB-palette/source-node join is unchanged. See `POSE-CONTRACT.md`.

`39` synthetic CPU tests pass, including blank/dither images, deliberately bad inherited runtime overrides, missing/changed protected files, wrong root/context, both private source memberships, and hand-computed nonidentity rotation with nonuniform scale. All five candidate sources remained exact during that run. The first run's single incorrect exception-type expectation and its failed evidence remain retained; `CPU-FIRST-FAILURE.md` explains it. Source-contract checks are explicitly not Godot execution.

## Preserved scope

Twelve bound GLBs remain the structural inputs. Eight raw capture cases remain three Nitori skin states, three Keiki Tools weights (0, 0.5, 1), and hand/box pose cases with unaffected controls. Two ordinary app cases remain Nitori skin 0 and Keiki 000, exercising Add, Undo/Redo, authored pose, packed Save and fresh-reader Open without the owned source alias. All materials are unchanged as supplied, including the coincident opaque glow limitation. No native shader/flex/jiggle fidelity or native appearance acceptance is claimed. Separate independent native base-geometry results must be consulted for their partial successes/refusals; this derived harness cannot replace them.

## Next authorized execution boundary

Root must review this source packet, select a final stable forty-character commit, and prepare a fresh schema-2 v2 manifest. Old manifest/working-tree contexts and old output folders are not reusable. Future commands are candidates only:

```powershell
& 'C:\Program Files\Python313\python.exe' -B output/sfm-static-appearance-probe-20261113-v2/source/probe_driver.py --prepare --expected-root-revision <EXACT_REVIEWED_HEAD>
& 'C:\Program Files\Python313\python.exe' -B output/sfm-static-appearance-probe-20261113-v2/source/probe_driver.py --manifest <FRESH_MANIFEST> --manifest-sha256 <ACTUAL_SHA256>
```

Only after review and an exclusive graphics lease should the same fresh manifest use `--parse-only`, or use `--run-gpu --lease-confirmed` for actual graphical/app proof. Every unexpected failure retains artifacts and stops. No such preparation or runtime was performed here.
