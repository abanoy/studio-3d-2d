# Closed carrier input-domain bridge

Pure CPU code; no native launcher, exporter, source reconstruction or file IO.
The exact parent semantic comparator and synthetic fixture remain unchanged.
`read_semantic_glb(raw)` passes the original JSON chunk to the parent's strict
reader before ordinary integer parsing can erase lexical `-0`. Duplicate keys,
nonfinite numbers, extra chunks, invalid lengths and nonzero BIN padding refuse.

`qualify_input_domain(document, binary, carrier=False)` adds owning-skin joint
component ranges, unique skin joints, forest/scene ownership, morph counts and
animation target/output shape, key count and time checks. It binds the complete
typed document, BIN and rest/skin/matrix metadata by hashes. A cheap typed decode
cost and reference/primitive/channel preflight runs before the parent decoder.
Scene reverse membership, DFS ancestry intervals and owner sets avoid quadratic
cross-products. All mesh resources must have node owners, and all animation
samplers must have channels, because an unused resource has no target domain.

`compare_qualified_non_normal(original_glb, raw_carrier_glb)` qualifies both
inputs, then invokes the unchanged non-NORMAL comparator. This is for the raw
carrier export before normal correction; the append-only correction's retained
unused storage is governed by its separate preservation and NORMAL contracts.

The profile is deliberately narrower than glTF. It is not complete conformance:
quaternion unit length, weight sums, arbitrary camera/material semantics,
historical/native correspondence and normal correctness are not qualified.
The actual retained B input passed this closed domain; no carrier export exists
and no input was modified. Native fidelity, repair and adoption remain false.

Bounds are 128 MiB GLB, 65,536 entries per named table, 262,144 cumulative graph,
scene, primitive and channel visits, and 8,000,000 declared decoded component
visits. They bound this CPU profile, not an arbitrary decoder/native process.

Run `python -B -m unittest -v test_domain` from this directory. Eighteen new
methods cover the four previously documented malformed-preservation witnesses,
strict JSON identity, actual owning skins, graph failures, unused targets,
animation counts, exact rest binding and early-budget refusal. Independent peer
review found budget-order and orphan-resource gaps; corrected regressions remain.
The first run's internal tuple/hash error was fixed with JSON list bindings.

The standards basis is the [Khronos glTF 2.0 specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html),
especially skins, node hierarchy, animations and GLB layout. Source-derived
checks and explicit exclusions above define the narrower implemented scope.
