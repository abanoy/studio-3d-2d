# Inactive PMX declaration capture: CPU prototype

This packet implements the fallback requested after the source gap audit: a
bounded pure helper for an **already decoded** PMX model. It is an experiment,
not a new HAS schema, importer, runtime feature or portable-model claim. Nothing
in main `src/`, `tools/`, `tests/`, owner reviews or installed MMD Tools changed.

`capture_decoded.capture_decoded` copies the exact named fields of the installed
MMD Tools `Rigid` and `Joint` classes into a JSON-transportable capsule. It copies
original table indices and a native bone index/name catalogue. It does not import
or execute the installed reader. The prototype requires that reader's exact
source bytes to bind its field contract, but this does **not** establish that the
decoded values came from the supplied source bytes.

Every result therefore has `applied: false`, `runtime_support: "NONE"`,
`native_file_join: "UNQUALIFIED"` and
`native_file_preservation_complete: false`. The fixed-header fingerprint accepts
only exact PMX binary32 version words `00000040` (2.0) and `66660640` (2.1), records
their bytes and the complete supplied-byte SHA256, and explicitly validates only
the fixed header. A synthetic/header-only byte string can pass that fingerprint;
it is not a native-file validator.

## Actual upstream binding and why no native join is claimed

The available installed addon manifest says MMD Tools **4.5.11**, distinct from
the historical 4.5.14 native receipt. `UPSTREAM_BINDING.json` pins its exact source
and relevant source locations, plus the current main `tools/mmd_ik.py` pattern.
No addon installation, download or preference change was made.

Installed `mmd_tools/core/pmx/__init__.py` SHA256:
`fb9aafe369025f221bc5a1c952d868260b1a4bb950dc33bca62645b4da454e5a`.

- `Header.load` accepts 2.0 only. The installed model has no soft-body table.
- `Rigid.load` maps **every** negative bone index to `None`, so this object API
  cannot distinguish native -1 from malformed -2 or other negative sentinels.
- `Joint.load` can substitute zero vectors after some truncated reads, and
  top-level `load` catches `struct.error` without re-raising it.
- String decoding uses replacement characters. Original encoded name bytes
  cannot be reconstructed from the decoded object.
- Reading all preceding geometry/material/bone/morph/display tables safely
  requires a separate bounded decoder/join qualification. Calling the existing
  permissive `load` would not provide that proof.

The prototype deliberately implements no full-file PMX decoder. PMX 2.1 always
reports unsupported reader/soft-body coverage, with soft-body count `null`
rather than a fabricated zero. Unexpected decoded attributes, including an
attached soft-body list, report their path/type/count with `values_captured:
false`; their values are not silently presented as preserved.

## Captured fields and guards

Native names are used unchanged. No metres/radians, basis, mass, gravity,
stiffness or damping conversion is invented. `velocity_attenuation` and
`rotation_attenuation` remain those original field names. This helper preserves
their decoded numbers without asserting physical validity or solver meaning.

| Object | Fields |
| --- | --- |
| Rigid body | `name`, `name_e`, `bone`, `collision_group_number`, `collision_group_mask`, `type`, `size`, `location`, `rotation`, `mass`, `velocity_attenuation`, `rotation_attenuation`, `bounce`, `friction`, `mode` |
| Joint | `name`, `name_e`, `mode`, `src_rigid`, `dest_rigid`, `location`, `rotation`, `maximum_location`, `minimum_location`, `maximum_rotation`, `minimum_rotation`, `spring_constant`, `spring_rotation_constant` |
| Native bone catalogue | Original index, exact `name` and `name_e`; other bone features are outside the capsule's stated scope |

All stored native floats must be finite, exact binary32 values represented as
Python `float`; implicit bool/int/string coercion and non-binary32 values refuse.
JSON transport preserves float values and signed zero. Body bone and joint body
references must be `None` (the upstream decoded sentinel) or exact nonnegative
integer indices in the original table. Negative decoded integers, booleans,
out-of-range references and references into empty tables refuse.

Masks retain all 16 unsigned bits, including bit 15. Negative/signed masks and
out-of-domain collision groups refuse. Known body shapes/modes 0/1/2 are retained.
Unknown signed-byte body or joint types are retained **and** make
`decoded_supported_fields_complete` false. This flag covers copied known decoded
fields only, not native-file integrity, name-byte fidelity, complete bone
preservation, or functioning simulation. It never overrides the unqualified
native join.

Every HAS binding remains unresolved: duplicate/empty native names are disclosed
and even unique names report `NO_HAS_CROSSWALK`. There is no fuzzy match, name
normalization or fabricated HAS bone identifier. Unknown decoded properties
likewise make coverage incomplete.

Hard maximums are 128 MiB supplied source bytes, 4,096 bones, 512 bodies, 1,024
joints, 1,024 UTF-8 bytes per native name and 128 KiB for the complete JSON capsule.
The caller can lower these limits but cannot raise them. Oversized inputs or
output raise `CaptureError`; the function never returns a truncated capsule.
The full capture is detached from its inputs. Capsule budget compliance is not
proof it will fit beside an existing 256 KiB MMD report or 1 MiB project metadata.

## CPU evidence

From this packet directory, run:

```powershell
python -B -X utf8 test_capture_decoded.py
```

The final source passed **22 synthetic CPU tests, zero failures**. See
`CPU_RESULT.json` and raw `unittest.log`, which bind the tested source hashes.
The tests construct Python objects and fixed-header bytes authored in this
packet; no owner model, native engine, converter, installed reader execution,
graphics, process inventory or Git command is used.

Coverage includes every body/joint field through typed JSON transport; exact
upstream constructor field coverage checked independently by AST; signed zero
and binary32 extremes; stable indices and duplicate names; sentinel/refusal
cases; high-bit masks; unknown modes/attributes; NaN/Inf/wrong types; name,
count and byte budgets; source-header versions; parser-source mismatch; and the
explicitly unqualified source/table join. The first CPU attempt failed on an
upstream joint constructor field-order mismatch. Its source, raw reproduced
failure and receipt are retained under `history/attempt1`; the tuple was then
corrected before the passing run. No earlier failure was overwritten.

`EXAMPLE_CAPTURE.json` is synthetic review data only. `INDEX.json` hashes the
packet; no private art, model geometry or native coordinates are included.

## Concrete next qualification

1. Independently implement or qualify a bounded PMX file reader/join that
   preserves original sentinel words, exact version/name bytes and table counts,
   rejects truncation, and accounts for trailing sections. Unsupported 2.1
   sections must remain explicit; do not promote this object capture into a
   complete native-file claim by merely calling the permissive pinned reader.
2. Compare all body/joint values and original indices against authored native
   PMX bytes and an independent reference. Add malformed/truncated files and
   unsupported-type/soft-body cases. Those native-file exercises are unrun here.
3. Only then propose additive inactive preparation-report integration, with full
   existing report/project budget checks, unchanged GLB geometry/source bytes,
   and actual isolated conversion plus cold portable HAS retention tests. No
   main integration or native/cold test has occurred in this packet.
4. Any later solver translation needs its own units/basis/normalization contract,
   reference motion, collision, Off restoration, recording/Undo and export
   qualification. No schema-9 or 200-item validator activation, model rebasing,
   scale conversion or trained reconstruction is part of this prototype.
