# Generated loose-part contact cache

The generated hair/clothing solver now keeps a call-local cache of penetrating
skin rows. A corrected guide invalidates only its affected rows. Active rows are
examined in ascending original order, retaining collider order and strict ties.
Skipped points still contribute to unresolved-contact statistics.

Capsule arrays remain typed. Caching is permitted only when both capsule endpoint
bindings and their complete ancestry are independent of every rotating guide.
Unknown or dependent bindings use the original scan/rebuild path. Every new call
starts with fresh body geometry. The initial original scan also handles clear
or uncorrectable-only cases without building a row cache. Cached termination uses
the original full scan as authority. Geometry, morph, skin, skeleton and resource
invalidation checks remain; contact radii, geometry and the 24-correction budget
are unchanged. Live retargeting still requires restarting the runner.

`python -B tests/verify_secondary_contact_cache.py` runs 47 generated controls
against the frozen independent baseline. They cover ordinary, moved-body,
cross-weighted, blocked, tied, dependent-collider and stale-geometry cases. The
clear case proves one authoritative scan, zero cached scans and zero row-summary
initializations. Tests compare the actual installed solver.

The optional native route takes all of `--source`, `--candidate`, `--spec`, and
their three `--source-sha256`, `--candidate-sha256`, `--spec-sha256` arguments.
It adds 15 controls over 720 steps using explicitly supplied read-only private
fixtures. The ordinary Spring runner supplies the actual candidate control;
the separately instantiated frozen reference drives the baseline. Complete pose
and FK dictionaries and their bytes, nine constraint statistics, raw input and
call order are checked. No private fixture is downloaded or distributed.

The installed-source run passes all 47 + 15 controls, and the existing protected
Miku contract passes 54. The loose-part/local-blow integration passes its 208 CPU
controls. Source, original inputs, runtime copies and parent environments remain
unchanged; owned processes and jobs close. These counts are overlapping focused
controls, not additional acceptance conditions or a new Full pass.

In the installed-source paired run, contact calls average 47.218 ms for the
reference and 43.946 ms for the new solver, about 6.9% lower. Earlier prototype
runs measured different paired reductions, including 18.6% for the same final
solver source. Report each observation with its own baseline; scheduling/load
vary, and these figures do not establish viewport FPS or general speed.

The five-section Junko case still ends with 123 unresolved contact pairs and 710
iteration-limit hits across the test. Its worst recorded gap is about -4.45 cm.
This increment reduces repeated work while preserving those results; it does not
fix that collision quality or finish outline coverage. Movement-driven hair
inertia remains separate work. The canonical Full result remains bound to 5d37647c.

See the [production evidence](../experiments/contact_cache_production_20261121/summary.json)
and [prototype observations](../experiments/final_contact_cache_20261121/summary.json).


## Collinear rotation fallback, 2026-11-21

When a penetrating point and its pivot lie on the capsule axis, the preferred
pole can also lie on that axis. Both old search directions then become zero,
even when rotating sideways would clear the capsule. The solver now chooses a
deterministic perpendicular direction only for that degenerate fallback. It
preserves the pivot, orbit radius, collision radius and correction budget.

`python -B tests/verify_secondary_contact_rotation.py` runs 20 generated controls
against the actual installed source, including independent engine-geometry
clearance checks, finite unit rotations, preserved orbit radius, blocked orbits
and deterministic results. The retained pre-fix source failed six of these
20 controls; the installed fix passes all 20. The existing generated cache
regression passes 47 and the protected saved Miku case passes 54. All owned jobs
closed and source, original inputs and parent environments were preserved.
The optional `--reference` route deliberately remains a failing red test.

These results establish a mathematical edge-case repair, not the cause of the
remaining Junko contacts. Junko's residual-contact scheduling and outline
coverage remain separate work; no new Full or human/device acceptance is claimed.
The evidence preserves the initial prelaunch denial separately from executed
product failures. See experiments/contact_rotation_fallback_20261121/summary.json.
