# Independent native point expectation: bounded CPU candidate

This new experiment implements source-derived point fields for the existing
`has_independent_native_point_expectation_1` consumer. It has not read original
native assets, private arrays or an owner scene, and has not run Blender,
SourceIO import, Godot, an exporter or a native repair. The original raw-normal
`2e-5` failure remains **FAILED_UNQUALIFIED**. Native SDK, normal fidelity,
export repair, full asset correspondence and adoption remain unqualified.

`native_point_expectation.py` accepts three immutable byte descriptors, each
containing `raw`, exact `bytes` and expected lowercase `sha256`. The outer host
must supply those expected identities from its already admitted immutable lock;
this API does not discover or authorize a replacement identity. It has no path
reader, writer, process launcher, scene accessor or carrier input. Returned
positions, topology, UVs, weights, bones and normals are private RAM data.

`derive_native_point_rows(native_refs)` independently reads MDL49 model/mesh and
bone records, VVD4 source fields and LOD0 fixups, and standard VTX7 topology.
It preserves native point identity rather than matching positions or normals.
`build_native_point_expectation(native_refs, setter_ID_order,
COORDINATE_POLICY, logical_name=...)` derives the existing consumer schema;
observed setter IDs are checked against the independently derived order only
after derivation. No setter payload or initial geometry enters the expectation.

The source rules are pinned in `SOURCE_DERIVATION.json`:

- VVD rows contain three F32 weight slots, three bone bytes, positions, normal
  words and UV0. LOD0 applies every supported fixup tag in file order.
- Point order follows mesh/strip-group `original_mesh_vertex_index`, mesh start
  and model start. Index offsets follow the actual sum of strip vertex counts.
  The importer reverses the **entire flattened** index stream before reshaping
  into triangles, reversing triangle order and winding.
- Positions multiply the existing F32 `.01905` scale, whose word is
  `0x3c9c0ebf`. UV V uses F32 `1-v`. Mesh-local native normal words, including
  signed zero, remain unchanged for the setter. GLB `x,z,-y` word transport is
  still the separate unchanged carrier strategy; this module does not swizzle
  or normalize normals.
- Groups follow exact native bone-name order. All three weight slots are
  inspected regardless of the stored bone-count/pad byte. Only positive slots
  issue a `REPLACE` write; repeated same-group positives retain the last value.
- The standalone MDL bridge gives newly created mesh and armature objects no
  later parent or placement transform. Identity matrices are source-derived
  expectations with positive zero entries, not readback observations. Their
  exact stored words and later native update/validate behavior remain subject
  to the existing exact join.

The deliberately closed profile requires ASCII names of at most 63 bytes,
unique bones and logical models, parent-before-child bone order, skinned MDL49
without flexes or eyeballs, an explicit VVD tangent table ending at EOF (no
extra UV layers), standard 25/27-byte VTX7 headers, exactly one VTX LOD, no
material replacements or bone-state changes, and contiguous complete trilist
strip partitions. Repeated point/raw identities, degenerate and duplicate
triangles, invalid ranges, nonfinite fields, weights outside `[0,1]`, or native
unit-normal deviation above the unchanged `2.5e-7` bound are refused. Bounds
are 128 MiB per file, 200,000 aggregate selected points, 1,000,000 corners,
256 bones, 1,024 models and 16,384 structural tables per file.

Full stored-weight expectations currently admit **at most one distinct
positive bone per vertex**, including repeated `REPLACE` writes to that bone.
This avoids guessing Blender's stored multi-group iteration order.
`replay_replace_weight_writes` separately supplies the generalized pure write
ledger: first positive insertion position, last positive replacement value.
Its 8,000 synthetic histories verify that candidate rule; they do not prove
Blender stores that order. A Root-owned synthetic Blender API probe can later
qualify this narrow storage rule with pinned runtime/harness/evidence and an
explicit new policy. Current code accepts no success marker or policy bypass.
Multi-group source facts can already be read; the full expectation refuses
them explicitly until that evidence is connected.

This is a point-source extractor, not a complete MDL/VVD/VTX asset validator.
Unconsumed MDL material/animation/attachment/physics subsystems, VVD lower-LOD
payloads and unrelated bytes are hash-bound but not semantically validated.
Actual B compatibility has not been observed. A valid extracted source relation
alone does not prove the old scene was produced from it: the existing saved /
current / setter / independent expectation join must still pass exactly.

Run the CPU suite with `python -B -X utf8 -m unittest discover -s
experiments/native_point_expectation_20261118 -p test_native_point_expectation.py
-v`. `audit_cpu.py` reruns it in-process, verifies 20 local SourceIO rule pins
and six unchanged prior-source/failure pins before and after, and writes fresh
aggregate-only validation/index files exclusively. No native/private inputs
are read by that audit. Peer review and final current-source CPU results are
separate evidence files. No original packet, application or documentation file
is changed by this experiment.
