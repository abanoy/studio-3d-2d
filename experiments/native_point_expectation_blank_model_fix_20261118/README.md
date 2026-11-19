# Zero-vertex MDL model-name fix: source/CPU successor

This fresh successor preserves the sealed `native_point_expectation_20261118`
packet (`INDEX` SHA256 `482f888349c19617bc540df723ed76104d3d6056cab085ecf6b99a56f42040f6`)
and its observed refusal. The only producer change admits the pinned SourceIO
empty-name fallback for a zero-vertex MDL model: an entirely NUL-filled 64-byte
name field becomes `blank`. The importer skips that zero-vertex record before
object-name handling or geometry creation. It never becomes a rendered logical
model. Renderable names retain the original strict nonempty ASCII profile.

Root's first read-only native-family attempt recorded `Bounded ASCII model name
required` in `native_point_expectation_actual_20261118/RESULT.json`. Under
Root's explicit metadata-only approval, the exact 37,644-byte SHA-pinned MDL
header/bodypart/model records were read in RAM. The scalar observation found
two bodyparts, three model records, one zero-vertex model, one entirely
NUL-filled zero-vertex name and two valid nonempty renderable name fields.
There were no unterminated fields, invalid nonempty ASCII/length fields, empty
renderable names or leading-NUL/nonzero name fields. Original MDL size, hash
and file stamp remained unchanged. No native arrays or names were published.
The VVD/VTX geometry was not read by this investigation.

Pinned `ModelV36Plus.from_buffer` maps an empty decoded name to `blank`.
`read_ascii_string(64)` strips leading/trailing NULs before decoding;
consequently a leading NUL followed by other bytes is not this empty-name
case. The successor requires the entire fixed field to be NUL for fallback
and explicitly refuses leading-NUL/nonzero fields. Pinned `mdl49.import_model`
checks `vertex_count == 0` before assigning the rendered object's name.
Existing mesh/eyeball metadata seek guards still run before the record is
skipped; this is not a bypass for malformed empty-model tables.

The CPU suite retains all 14 original tests and adds two focused regressions:
a blank MDL/VTX model leaves every rendered point expectation unchanged; empty
renderable names, invalid ASCII, leading-NUL/nonzero names and malformed blank
table seeks remain refused. All 16 tests pass. The generalized three-slot
write ledger retains its 8,000 synthetic histories. Existing exact joins and
the unchanged `2e-5` failure / `2.5e-7` source-unit bound remain intact.

All other original candidate limits remain: RAM-only pinned immutable bytes,
standard VTX7 one-LOD profile, no extra UV/flex/eyeball/material-replacement/
bone-state-change support, strict point/raw identities and topology, unchanged
F32 `.01905`, unchanged native normal words, no nearest matching, no six-foot
normalization, and at most one distinct positive stored bone group per point.
Multi-group raw write facts remain available; storage policy qualification is
separate. This is a point-source extractor, not full asset validity.

This successor has not run a fresh native-family compatibility read, Blender,
SourceIO import, a scene open/save, an exporter or native repair. Actual B
compatibility, native SDK/fidelity, full asset correspondence, exporter binding,
repair and adoption remain unqualified. Only synthetic CPU tests and the
approved MDL metadata observation support this change.

`SOURCE_DERIVATION.json` binds the source rules, original sealed packet, prior
refusal and aggregate MDL observation. `audit_cpu.py` verifies 20 SourceIO pins
and 10 prior-source/result pins before and after its in-process CPU run, then
writes fresh aggregate-only `CPU_VALIDATION.json` and `INDEX.json` exclusively.
The audit itself reads no original native data. Run the suite with:

`python -B -X utf8 -m unittest discover -s experiments/native_point_expectation_blank_model_fix_20261118 -p test_native_point_expectation.py -v`
