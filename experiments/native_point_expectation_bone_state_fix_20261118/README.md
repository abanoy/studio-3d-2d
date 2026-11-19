# Bounded nonconsumed VTX bone-state metadata: CPU successor

This fresh successor preserves both earlier sealed source packets and their
actual read-only refusal records. Root's second exact-family read, using
`0527c86c…`, passed the blank-model name fix and refused the combined
trilist/no-bone-state-change condition. The approved exact VTX strip-metadata
investigation identified **only the nonzero state-count predicate** as the
cause. Actual family compatibility still remains refused until a fresh Root
read with this candidate; no success or native repair is claimed here.

The metadata-only read checked the exact SHA-pinned 173,309-byte VTX header
and packed structural records. It found four groups/four strips, all explicit
trilists, strip bone count at most three and nonzero state counts on all four
strips: 66 total rows, at most 51 per strip. The header permits 53 hardware
slots. All existing SourceIO state-offset assertions, contiguous strip
partitions and count-times-eight relative spans fit the file. Source bytes,
size and file stamp remained unchanged. No actual state-row contents, native
geometry arrays or names were read or published by this investigation.

The source reason for admitting these records is independent of that actual
observation. Pinned `merge_strip_groups` reads only group indices, original
mesh vertex IDs and the sum of strip vertex counts. It never consumes the
state count, pointer or rows. The MDL49 importer takes weight slots and global
bone IDs directly from the selected VVD rows. Hardware palette entries do not
replace that native identity or weight source. The official packed VTX7
[Valve declaration](https://raw.githubusercontent.com/ValveSoftware/source-sdk-2013/master/src/public/optimize.h)
documents each state entry as two signed 32-bit fields and locates its table
relative to the owning strip. The separately pinned earlier format review
and source reader corroborate that layout; they are source references, not
new tests or renderer qualification.

The successor replaces the blanket zero-count requirement with explicit
metadata validation. The declared hardware-slot limit must be 1–512; each
strip may have 0–512 state rows and the file at most 200,000. Nonempty tables
need a positive strip-relative offset, a complete eight-byte-per-row span and
the same structural nonoverlap checks as geometry/header tables. Each signed
slot must lie within the header limit and each signed global bone within the
independently decoded MDL bone count. Negative values, out-of-range indices,
huge counts, truncated spans and overlaps are refused. The SourceIO raw-offset
assertion remains even for zero count. Repeated slots are not interpreted as
palette state or used to change the point derivation.

All point, raw-ID, topology, F32 normal/position/UV, group/weight and matrix
rules remain unchanged. The blank-only fix, strict names, single VTX LOD,
trilist/partition checks, no extra UV/flex/eyeball/material replacement profile,
unchanged `.01905`, `2e-5` failure and `2.5e-7` normal-unit bound remain intact.
There is no nearest matching, tolerance relaxation or six-foot normalization.
Full stored expectations still refuse more than one distinct positive bone
group per point. `VTX_hardware_palette_or_render_equivalence_qualified` remains
false in both source facts and full expectations.

The 19-test CPU suite retains the previous 16 tests and adds nonzero-state
invariance, signed/range/offset/count/overlap negatives and declared maximum /
aggregate bounds. Positive fixtures deliberately change hardware mappings and
repeat slots while all rendered expectation fields retain exact types and
float words. Source identities still change when bytes change. The candidate
does not reconstruct, render or qualify a hardware palette. These synthetic
tests cannot certify native hardware skinning or actual B correspondence.

`SOURCE_DERIVATION.json` binds 20 SourceIO rule files, both sealed predecessors,
the actual refusals, format references and scalar observation. The audit
rechecks 20 SourceIO and 16 prior/reference pins around its in-process CPU run.
It reads no original native input and writes only fresh aggregate validation /
index files in this folder. Independent review is separate. No Blender,
SourceIO import, model open/save, exporter, native job, Git, Main/application
or documentation modification was performed. Native SDK, fidelity, exporter
binding, repair, runtime, correspondence and adoption remain unqualified.

`python -B -X utf8 -m unittest discover -s experiments/native_point_expectation_bone_state_fix_20261118 -p test_native_point_expectation.py -v`
