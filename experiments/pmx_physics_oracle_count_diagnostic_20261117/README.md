# Passive oracle table-count diagnostic

`diagnostic_counts(data)` accepts immutable PMX bytes already obtained by Root's stable readonly worker and returns a small PRIVATE diagnostic. It does not open an input file, print, write output, import a candidate reader/comparator/archive, return a native witness, widen a limit or qualify an input. Preparation uses public pinned source and authored RAM fixtures only. No original, staged copy, private provenance or running full output was read here.

The helper verifies the exact independent-oracle INDEX d27d9873bc08ec2bc37f8939ae09f9b071f9f4e6fda8b112a2626fef7fabbb45 and the exact 14,055-byte oracle source f1dfc3a37c32c1c8b57537b1500b701792df13e4e8b87abe13b0ce49be2c4cec. It adds exactly one passive callback immediately before the original `oracle table-count budget` guard, compiles that source in a fresh temporary module, and calls its original `read_oracle(data)` with the original default Limits. Removing that one callback restores every original source byte and SHA. All old packets, including the observation harness4258, remain unchanged.

The callback records four existing local values: source-authored table name, signed decoded count, original ceiling and byte offset of the count token's first byte. The report also marks whether that count falls within the original count budget. Counts are observed before the original budget guard, so a count above a ceiling or below zero remains visible without reading that table's entries. If the count word is truncated, no observation is fabricated. A count within its ceiling can still fail the original next extent guard or a later parser guard. The exact original Refused label is retained; all other exceptions propagate to Root's worker error handling. Successful witnesses are immediately discarded and never returned by this API.

This distinguishes which table/count/offset triggered a capacity refusal. It does not prove that a prefix was interpreted correctly: a wrong prefix offset may also yield a large decoded count. Root must assess those observations separately; no native expected values are hardcoded, no budgets are fitted to observed input, and whole native protocol qualification remains false. The original oracle retains its existing source/work/string/output limits and may refuse before a physics table is reached.

The returned `observed_tables` and `refusal` are PRIVATE input-derived observations even though the table names are fixed source roles. Do not publish the returned table rows or witness/model data. A later public projection should contain only separately reviewed scalar completion/preservation/count-summary flags permitted by Root.

```python
# Inside a separate Root-owned worker, after its exact source/input/closed-lane checks:
# module is loaded by exact file path after this packet's INDEX is verified.
report = module.diagnostic_counts(stable_original_bytes)
# Root writes report only to a fresh PRIVATE output and rechecks original/copy
# identities, sizes, bytes/SHA and source bindings before its private receipt.
```

This packet intentionally adds no native runner or activation mechanism. Root must run any actual observation only after the exclusive full/native lane closes, retaining its worker/deadline and original/copy preservation checks. The previously incomplete oracle phase remains incomplete; this diagnostic cannot freeze it, start a candidate comparison, repair it or claim a full protocol pass.

`instrument_module(observer)` is the small context-manager API used for the passive source proof and witness-equivalence tests. The public source files are the only files the diagnostic itself reads. It removes its temporary oracle module entry on success or failure and supports explicit-file loading without this directory on the import search path.

Run `python -B -m unittest -v test_diagnostic.py` here for authored tests covering exact inverse, all nine default count ceilings/offsets, body/joint capacity, negative counts, count/extent truncation, populated witness byte identity, unsupported headers, import isolation and absent candidate imports. No test opens a native input.
