# Exact JSON-number comparison for the isolated six-foot domain

Status: source and CPU preparation complete. The successor Godot probe is **unparsed and unrun**. The original actual Godot run remains a failure: 444 checks executed, 437 passed, and seven `schema_encode_0` through `schema_encode_6` checks failed. The boundary probe remains unrun. No production import behavior, main source, encoder algorithm, transform tolerance, original corpus, or original packet was changed.

## Why the harness needs a correction

The actual run used Godot 4.6 stable, as recorded in the exact copied stdout. Its old result reports booleans without payload or type diagnostics. The seven failures align with a concrete transport mismatch: the expected encoded documents were parsed from JSON, so version numbers became floats; `encode_capability` assigns the literal integer `9` to the new outer `schema_version`. The five successful legacy identity encodes do not author that number.

This behavior follows the matching engine implementation. Its [JSON numeric parser](https://github.com/godotengine/godot/blob/4.6-stable/core/io/json.cpp#L366-L373) creates a double for every JSON number. [Dictionary equality](https://github.com/godotengine/godot/blob/4.6-stable/core/variant/dictionary.cpp#L249-L269) recursively compares values through `hash_compare`; that [Variant comparison](https://github.com/godotengine/godot/blob/4.6-stable/core/variant/variant.cpp#L3033-L3045) rejects differing Variant types before comparing numeric values. JSON itself has a single number category, as explained in the [official JSON documentation](https://docs.godotengine.org/en/4.6/classes/class_json.html#class-json-method-stringify).

`CPU_DIAGNOSIS.json` records 59 actual CPU checks. The sealed Python encoder receives the exact corpus after decoding all JSON numbers as floats. Its twelve successful encode fixtures preserve exact JSON values. Exactly the seven active encodes predict one strict-type difference: integer 9 versus float 9 at `$.document.schema_version`. That predicted failed set matches the original actual result. This is a source-supported diagnosis and CPU reproduction, **not actual Godot payload evidence**; the new probe must establish those types and paths itself.

## What the successor checks

`import_basis_domain.gd` and `PARITY_CORPUS_v3.json` are exact copies of the sealed predecessor, with the same SHA256 values. All ten transform checks and the existing `checked_job` authorization/path/expiry checks retain their original text. Domain code and its decimal-string authentication remain unchanged.

Only the expected `document` field in encode rows uses an exact recursive JSON-value comparator. Other corpus operations retain the previous predicates. The comparator keeps dictionary keys, required fields, nulls, booleans, strings, ordered array contents, and finite numeric values exact. It does not use an epsilon, approximate comparison, JSON stringify/parse roundtrip, case folding, or general coercion. Mixed integer/float equality is allowed only for an exactly equal finite value with the integer within the inclusive ±2^53 safe range. Larger mixed representations are conservatively refused; equal large integers still compare exactly. Non-JSON types and structures deeper than 64 levels fail.

The planned result has **480 named checks**:

- 434 unchanged corpus inputs and ten unchanged transform checks, with corrected JSON-value comparison on successful encode documents.
- 28 comparator contracts, including changed numbers, fractional changes, boolean/number distinctions, missing null fields, extra keys, array order and length, case-sensitive strings, unsafe integer aliasing, nonfinite values, non-JSON values, and depth refusal.
- Seven actual typed-difference checks requiring precisely one raw difference per historical failed case: `$.document.schema_version`, int versus float, exactly equal numeric value 9.
- One gate requiring all 434 original raw corpus comparisons to reproduce precisely the same seven historical failures. Those raw booleans remain in `raw_corpus_named_checks` even if the corrected checks pass.

Thus another encoder defect cannot be excused as this representation issue. A missing field, changed value, unexpected difference path or different old failed set fails the new probe. No success is inferred for the actual successor until root executes it.

## Root-owned later execution

Stage this new folder at its same relative path inside a fresh isolated Studio checkout. Required runtime files are `basis_domain_unit.gd`, `import_basis_domain.gd`, and `PARITY_CORPUS_v3.json`; the comparison helper is inlined in the probe and pinned by its script SHA. `comparison_functions.gd.txt` is reviewable generation input, not a runtime preload. `SOURCE_PINS.json` holds exact hashes.

The existing job schema and root closure rules are unchanged: `has_six_foot_domain_job_1`, `ROOT_APPROVED_SIX_FOOT_DOMAIN`, root closure, expiry, script/corpus SHA pins and fresh output under the isolated project's output folder. Parse the successor first, then execute through root's existing owned headless runner. Expect 480 checks and zero failures for success, while the diagnostic raw corpus still contains exactly seven false values. Keep the old 444/7 run and its receipts permanently distinct. The original 21-check boundary probe is a separate later gate.

`prepare_successor.py` is a reproduction recipe, not an engine runner. `cpu_transport_diagnosis.py` runs only the Python/source preflight. Do not regenerate this sealed packet in place; use a new folder for later changes. `SETUP_REFUSALS.md` retains preparation issues.

Nothing here qualifies production schema9 acceptance, automatic human classification, import normalization, real-model stature measurement, helper lineage, native simulation under an adjusted basis, PMX physics, all-model standardization, or artist acceptance. Production remains unchanged and closed to active basis data.
