# Final independent review: PASS

Scope: the output-only JunkoHair MDL49 numeric-prefix reader, its authored fixtures, actual extraction run `runs/1794614279712394400`, and the adjacent inert metadata proposal. No source, runtime, original asset, archive, Git state, native viewer, GPU or converter was modified or invoked by this reviewer. Writes were confined to this review directory.

## Findings

No actionable parser or metadata correctness defects were found. The inspected reader uses the pinned wire order, bounds every admitted record/pointer/string, follows native indices instead of names/order, rejects parent cycles, overlapping/aliased prefixes, nonfinite numbers and ambiguous zero/nonzero declarations, and preserves unknown flag bits explicitly. Its conservative admission rules are supported-subset policies rather than claims about every native MDL.

The original 26 authored tests passed independently in memory with zero failures/errors. Only the test module's top-level output-folder creation was suppressed; its fixture/test bodies were unchanged. Separate reviewer fixtures verified rejection of partial prefix overlap and misaligned targets. The unequal pitch_friction=-7.25 and pitch_bounce=8.5 sentinel correctly detects the misleading pinned dataclass declaration order.

All 49 actual RAW_VALUES rows and all 49 proposal rows match the independent direct-byte audit: native bone identity/parent, relative and absolute offsets, signed/unsigned flags, all 29 float values, raw float32 words and 120-byte prefix hashes. All 69 bone record/name hashes and native flags/types match the MDL bytes. There are zero row discrepancies.

Measured facts: 69 native bones; 49 type-5 declarations; 1,421 finite floats; flags 0x31 throughout; known mask 0x7f; unknown bits zero; two exact float32 parameter groups of 17 and 32 bones. Prefix positions are nonmonotonic in bone order and collectively cover [15568,21448). These are 120-byte decoded prefixes; the complete native rule layout remains unverified.

The proposal is explicitly PROPOSAL_NOT_IMPLEMENTED, runtime_support=not_implemented, applied=false and binding_status=unattempted for every rule. full_native_rule_layout_verified=false is accurate. Values remain unconverted and unclamped; no solver equivalence, units mapping, binding or simulation has been established. Proposal size is 67,525 bytes, below its proposed 128 KiB budget. The full adjacent importer-report 256 KiB admission/roundtrip remains explicitly UNTESTED.

All 24 independent actual-run checks passed. Artifact hashes/sizes/mtimes match verification.json. The preservation archive has 1,153 equal before/after entries, with 561 staged native resources, five original archives and 574 pinned SourceIO source files. A separate current read of all 1,153 files (580,637,628 bytes) exactly matched recorded SHA256, size and mtime. This supports the stated preservation scope; it is not a claim that unrelated current production files were frozen.

## Frozen evidence

- `independent-byte-audit.json`: initial independent MDL fields/offsets/hashes, all 49 numeric rows and observed ranges.
- `layout-review.md`: pinned layout facts, semantic boundaries and two pinned reader discrepancies that were avoided without changing SourceIO.
- `reader-review-checks.json`: 26-test rerun, extra partial-overlap/alignment checks, source hashes and unchanged-source evidence.
- `reader-review-test-output.txt`: independent test transcript.
- `actual-extraction-review.json`: 24 actual-run comparisons, artifact hashes, zero mismatches and independent current preservation read.
- `REVIEW_INDEX.json`: identities of these frozen review artifacts.

Suitable for an indexed source/metadata-only publication candidate. No runtime integration or native simulation approval is implied.
