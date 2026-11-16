# Source normal boundary and unit analysis — November 15, 2026

This increment uses Python stdlib analysis and read-only source inspection.
No Godot, Blender, converter or original SDK executable was run. Production,
test, installed-runtime and native input files were not changed. Private native
coordinates, normals, geometry and the full official sources are not published.

## Measured normal failure remains failed

`diagnose_normals.py` reuses a SHA-pinned prefix of the earlier independent
native/glTF reader and matching rules, without executing its output section.
It reproduces 9,661 matched vertices and the exact prior maximum normal distance
0.00121654672362075; 8,364 are above the unchanged 2e-5 gate. Four repeated-
attribute ambiguities remain; this is not a unique native-vertex identity claim.

Native VVD normals are already unit length within 2.10821e-7. Normalizing them
fixes none of those failures. The VVD record contains float32 normal components;
packed-normal decoding/normalization does not explain this input's discrepancy.

The installed [glTF exporter](https://github.com/blender/blender/blob/ec6e62d40fa9e9d1bea33ad5d00148c99a4f0832/scripts/addons_core/io_scene_gltf2/blender/exp/primitive_extract.py#L1435)
explicitly rounds corner normals to four decimals,
normalizes, applies the skin normal transform, normalizes and maps Z-up to Y-up.
A stdlib round4/normalize prediction matches 7,966 rows within 2e-7, but its
maximum remaining difference is 0.0012081099462259133. Round4 alone cannot
explain that outlier: rounding a unit vector contributes at most about 0.00017321
after normalization, excluding the negligible input-length/float error.

The official [Blender custom-normal API](https://github.com/blender/blender/blob/ec6e62d40fa9e9d1bea33ad5d00148c99a4f0832/source/blender/blenkernel/intern/mesh_normals.cc#L1524)
uses a per-corner fan-space short2 representation with approximate-angle
calculation. That is a candidate boundary, not an exact reproduced cause.
The original conversion log reports Blender 5.1.2 build ec6e62d40fa9, resolved
to immutable commit ec6e62d40fa9e9d1bea33ad5d00148c99a4f0832. The installed
exporter/constants match that commit after explicit CRLF/LF normalization;
SourceIO's importer matches its pinned official bytes exactly. This is provenance,
not an independently reproduced Blender binary build. The original normal gate
remains **FAILED / UNQUALIFIED**; no tolerance or artist-fidelity acceptance changes.

An initial interactive instrumentation attempt used the last candidate normal,
not the selected native vertex. Its diagnostic output is invalid and excluded.
The saved script selects `source_vertices[vi]` and asserts the stored error join.

## Native tip, units and fan transport

The qualified fixed input has `G = C * N_scaled`, where `C(x,y,z)=(x,z,-y)`.
This is a world-coordinate conversion; it does not rename the joint-local axes.
The native tip is local **+Z**. With a verified world bone transform `T`, use
`T * (0,0,native_length * source_conversion_scale)`. The transform already
includes model/parent uniform scale. Do not multiply that scale a second time,
use local Y, or substitute the next-child direction. Junko's declared length20
at conversion0.01905 is0.381 before later model/parent scale.

For positive uniform size factor `lambda=source_conversion_scale*root_scale`,
positions, lengths, velocity and acceleration scale by lambda. Angular limits
and the yaw/pitch stiffness/damping coefficients keep their units and values.
The SDK's tipMass is a downward acceleration term; it is not inverse mass.
Similarity-preserving conversion maps it to `lambda*tipMass`, Source-global -Z
becoming HAS-global -Y. Model/root rotation must not rotate world gravity with
the model. Fixed real-world gravity instead of similarity-scaled native gravity
is a separate artistic policy, not a mathematically equivalent translation.

A HAS fan sample is already a world vector. A future solver working in HAS units
must not apply C to it again. A native-unit reference instead receives
`inverse(C)*world_acceleration/lambda`. Define the acceleration policy explicitly:
current `airflow.gd` supplies a bounded artistic field to the engine spring,
not an established native Source wind API or measured physical unit contract.
Sample actual displaced world positions; test misses, speed0, opposite flow and
strengths3/12/50 separately. The source SDK reference has no corresponding fan
behavior to claim as artist-exact.

`check_unit_covariance.py` passes120 synthetic combinations with maximum error
1.1721597256030656e-14 for tip position, yaw/pitch acceleration, one Euler step
and length projection. Wrong local axis, unscaled mass, rotated world gravity
and repeated length conversion are detected. This is algebra, not a complete
0x31 solver, angle/history/stability test, actual HAS pose result, or qualification
of a second source conversion scale.

## Prepared intermediate probe — AST-only, runtime UNRUN

`capture_blender_normals_UNRUN.py` is a candidate for a root-reviewed private
desktop run **after fresh complete default PASS and authoritative closure**.
It reads the pre-export editable snapshot and captures geometry/weights/UVs,
stored corner/custom-normal data and exact float32 exporter stages. It does not
import SourceIO, patch installed files, save the original blend or invoke export.
Detailed arrays go only to a fresh `ROOT/output/.../PRIVATE_NORMALS.json`.
`PUBLIC_CAPTURE.json` contains hashes/counts only. Automatic file execution must
be disabled, and the copied `.blend` must be hash-locked before loading.

The mandatory lease format is `has_blender_normal_probe_lease_1`; phase
`ROOT_APPROVED_AFTER_FULL_PASS`, full_terminal_status `PASS`, root closure true,
publish_private_arrays false, matching HEAD, future expiry and fresh private
output directory. Lock these exact files by path/SHA256: blend, mdl, vvd, glb,
parameters, blender_exe, probe, exporter_extract, exporter_constants,
sourceio_import, full_receipt and closure_receipt. No lease was created and no
runtime was parsed/launched here. The root must audit source/clock/desktops,
run identity and closure under the existing process policy before execution.

`compare_private_normals_UNRUN.py` prepares an aggregate comparison of raw VVD,
saved Blender corner normals, reconstructed exporter stages and emitted GLB.
It requires complete position/weight/UV-compatible corner witnesses and reports
ambiguities. Predicted normal selection does not establish unique native/corner
identity. Capturing a saved snapshot localizes a boundary but does not observe
the original SourceIO setter call or independently reproduce the C++ fan encoder.
Both new candidates have only Python AST checks; Blender RNA/API/UV/transform
assumptions remain untested and any refusal must be preserved.

## Bounded next runtime step

After the root's fresh full closes, first regenerate/review and run the saved
actual Model/SceneIO FK/rest/native-Z probe at its exact declared scope. Keep
normal/artist fidelity separate from skeleton transport. Use those actual joins
before a separate Source0x31 scratch solver. Add an independent numerical trace
and clock policy, then single FrontHair1, parent17→18 and26→27, fan response,
Off restoration and portable recorded motion. Generic VRM/helper spring tails
remain unchanged; unsupported native flags/controllers remain explicit.

The new six-foot standardization requirement reinforces the need to keep source
conversion, derived normalization and artist-relative scale distinct. Neither
the current optional height fit nor these synthetic checks implements that new
scale-1 baseline or permits retroactive resizing of existing authored scenes.

Provenance and exact code/input-source hashes are in `PROVENANCE.json`; numeric
results are `NORMAL_DIAGNOSIS.json` and `UNIT_COVARIANCE.json`. No main-file edit,
git-index mutation, app runtime, cleanup or native-data upload was performed.
