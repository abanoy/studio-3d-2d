# Independent review of bounded bone-state metadata admission

**Result: GO for this source/CPU successor.** No outstanding defect was found
within the documented point-source extraction scope. Hardware palette/render
equivalence, native execution, full asset validity, actual point
correspondence, normal fidelity, repair and adoption remain unqualified.

Reviewed identities:

- Sealed blank-model predecessor producer, unchanged: `0527c86cd36fc886cc7f4bde5c9363fa6226da4345382df7100e171a5b2401cf`
- Successor `native_point_expectation.py`: `cbb4eca98a6cf5045211dc10bd8e060b79492ec306d61a4d29679fc0d5cc184d`
- Successor `test_native_point_expectation.py`: `7f045a07431ac700aa2868237174394747d9f0f6a5ae84221444d33c1ad944a9`

The independent producer comparison contains only the added bone-state count
budget, header-slot bound, state-table validation and explicit false hardware
palette qualification flags. Existing point addressing, corner order, VVD
weights, UVs, normals, coordinate rules and thresholds remain unchanged.

The reviewer independently read Valve's primary
[optimize.h](https://raw.githubusercontent.com/ValveSoftware/source-sdk-2013/master/src/public/optimize.h).
Its packed declaration gives the state record two signed 32-bit fields and
addresses its array relative to the owning strip. It also declares a maximum
of 512 bones per strip. These support the 8-byte `<2i` record layout and the
chosen closed limits; they do not establish palette lifetime or rendering
equivalence. The local prior format review corroborates this layout and
explicitly leaves hardware palette/render equivalence untested.

Local pinned SourceIO source establishes why this metadata is excluded from
the expected point fields. Its strip reader retains count/offset header
fields but does not read state rows. A full Python-source search found no
other consumers of those fields. `merge_strip_groups` uses group indices,
original mesh vertex IDs and the sum of strip vertex counts. The MDL49
importer obtains bone IDs and weights from the selected VVD rows, then writes
positive weights by native MDL bone name. State records cannot substitute for
those native global weight identities in this producer.

The successor validates each nonempty state span at `strip + relative_offset`
through the same bounded, nonoverlapping structural-table tracker. It caps
rows at 512 per strip and 200,000 in aggregate. Signed slots must be
nonnegative and below the declared bounded header count; signed global bone
IDs must be nonnegative and inside the native MDL bone table. These are
closed metadata admission rules, not validation of palette initialization,
state persistence, used VTX palette slots or rendered skinning.

An independent current-source CPU invocation ran **19 tests, zero failures
and zero errors** in 0.044 seconds:

`python -B -X utf8 -m unittest discover -s experiments/native_point_expectation_bone_state_fix_20261118 -p test_native_point_expectation.py -v`

Focused fixtures cover nonzero state tables, repeated slots with changed
mapping, signed negative/out-of-range fields, the slot-511/header-512
boundary, excessive per-strip and aggregate counts, invalid/truncated
relative spans and overlap with structural geometry/strip tables. Positive
cases preserve every expected point-field family despite a new synthetic
VTX identity. Existing exact-word, source identity, blank model, parser bound,
one-group storage and exact private-join checks continue to pass.

The parent reports a separately approved original VTX header-only metadata
observation motivating this successor. This reviewer did not repeat that
original-file read or read original state rows, geometry, native arrays,
normal payloads, artwork or owner scenes. Primary source browsing and
synthetic CPU tests provide source evidence only. No native app, SourceIO
import, process query, Git action, installation or upload was performed.

The external immutable identity lock, partial asset-validation boundary,
one-distinct-positive-stored-group limit, unproved native update/validate
behavior and exact future saved/current/source join remain required. No
nearest matching, matrix readback claim, normal reconstruction or tolerance
change was added. The original `2e-5` failure remains failed; the native-unit
bound remains `2.5e-7`.

Only this successor peer note was written by the reviewer. Old packets,
producer/tests, application source and documentation were not modified.
