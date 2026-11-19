# Independent peer review of blank-model successor

**Result: GO for this narrow source/CPU successor.** No outstanding defect was
found in the reviewed change. Native execution, complete asset validity,
actual point correspondence, normal fidelity, export repair and adoption
remain unqualified.

Reviewed source identities:

- Sealed predecessor producer, unchanged: `2631269a552a5dcbeb7091f8b1c903ff4f35cbd1713beba7b622a62b3aa1a283`
- Successor `native_point_expectation.py`: `0527c86cd36fc886cc7f4bde5c9363fa6226da4345382df7100e171a5b2401cf`
- Successor `test_native_point_expectation.py`: `5e72b23945af4b3ef8ac252ca1f8022229d5928ec6ae4b8284a8b9551e289540`

An independent text comparison found only the intended producer change:
decode the model vertex count before applying the name admission rule; map an
entirely NUL 64-byte name field to `blank` only for a zero-vertex model. The
existing renderable-name admission and all geometry, identity, numeric,
threshold and resource rules are unchanged.

This agrees with the local pinned SourceIO boundary. Its
`ModelV36Plus.from_buffer` substitutes `blank` when its fixed-field decoder
returns an empty name. The decoder strips leading and trailing NULs before
splitting an internal NUL, so an empty result requires the whole field to be
NUL. Its MDL49 importer skips a zero-vertex model before object-name handling,
mesh construction and point gathering. The successor keeps declared
mesh/eyeball seek checks before the later skip. Blank metadata does not enter
the returned renderable logical-model relation.

Review caught an initially broader condition that inspected only the name
prefix before the first NUL. It would also admit a leading NUL followed by
nonzero bytes. The final condition examines the entire fixed field, and
regressions refuse both leading-NUL ASCII content and leading-NUL invalid
bytes. Empty renderable names and invalid ASCII remain refused.

An independent current-source CPU invocation ran **16 tests with zero
failures and zero errors** in 0.041 seconds:

`python -B -X utf8 -m unittest discover -s experiments/native_point_expectation_blank_model_fix_20261118 -p test_native_point_expectation.py -v`

The new positive fixture contains a renderable model and an empty zero-vertex
model with matching VTX metadata. Its returned point IDs, raw IDs, positions,
corners, groups, weights, UVs, matrices and native normal words equal the
fixture without the blank model. Existing exact-word, parser refusal,
resource-bound and generalized weight-write tests continue to pass.

The parent reports a Root-approved, hash-pinned MDL metadata observation of
one all-NUL zero-vertex model. That narrow metadata observation motivated the
fix; this peer did not repeat the original-file read or independently qualify
that observation. No original native array, normal payload, artwork or owner
scene was read in this review. Source parity and synthetic fixtures do not
establish the complete original native-family profile or a saved-scene join.

All predecessor boundaries remain: trusted external identity lock, partial
source extractor rather than full asset validator, at most one distinct
positive stored weight group per vertex, unproved native storage/update/
validate behavior and positive-zero matrix expectations subject to exact
readback comparison. No nearest matching, tolerance change or success bypass
was added. The original `2e-5` failure remains failed and the native-unit bound
remains `2.5e-7`.

Only this successor peer note was written by the reviewer. The review did not
modify old packets, producer/tests, application source or documentation, and
did not run native apps, SourceIO import, process queries, Git or network work.
