# Walking along a path: bounded evaluator experiment

`src/path_locomotion.gd` is an internal read-only prototype. It is not connected to
the app's menus, saved model settings or final rendering yet. Existing movement
paths and preset behavior stay unchanged; MOTION-03 remains partial.

The first feasibility spike solved49samples on the original seventeen-bone figure
along a flat straight0.6m path, using0.3m stride,0.06m lift and0.025m root lowering.
It left model data/source bytes unchanged. The generalized evaluator derives
stride/lift/lowering from measured leg length and accepts bounded correction
amounts. It samples the authored path exactly rather than replacing its keys.
Stance targets remain fixed; the opposite foot swings with eased travel and lift.
The existing two-leg IK solver resolves both feet and verifies actual positions.
Root/turn/scale and upper-body channels remain authored; the derived root lowering
and leg pose are returned separately.

Build publishes only after every half-frame is checked. It refuses keyed legs or
hips (even explicit identity keys), competing planted contacts, missing/ambiguous
legs, grouped characters, nonuniform parents, changing turn/scale, slopes, corners,
reversals, Hold jumps, excessive speed/length and invalid correction values.
The experiment supports up to240frames and64strides. This is a flat-ground bound,
not terrain adaptation or general native-rig certification.

Sampling snapshots/restores live root and every bone field around temporary IK.
It retains only a weak actor/skeleton binding and a single cached returned pose.
Changed source data, parent, root or any bone binding refuses before use. Caller
changes cannot mutate the cache. Zero amount returns the exact authored result.
Failed builds preserve the previous usable plan.

```sh
python tests/verify_path_locomotion.py --output /absolute/new/result
```

29checks pass on the included original figure, including97half-frame samples,
actual feet within0.2mm of targets, exact source/live-state restoration, zero and
partial amount, deterministic seeks, keyed arm preservation, source/binding
staleness and all stated refusal cases. Whole-valued JSON timing/routes also work.
Initial test fixture corrections used the real loader result/name normalization
and anchored both endpoints to create an actual changing turn; assertions stayed.
See [walking evidence](benchmarks/path_locomotion_2026-11-06.json).

Next is a strict saved-intent contract and explicit editor enable/disable/preview/
correction controls, followed by actual Undo/HAS/cold-open/recovery/render checks.
No walking UI, exported movie behavior, native fidelity, terrain adaptation or
artist acceptance is claimed by this experiment.
