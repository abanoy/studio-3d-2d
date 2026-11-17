# Exact output transport audit

The root's first standard Neon attempt failed the Inset marker/file equality check after all 12384 assertions passed. The physical result preserved a full-precision maximum projection error ending in `...2494`; default stdout serialization ended in `...249`. The strict equality check correctly detected different JSON numeric values. Earlier focused geometry success remains a separate result; the failed standard attempt remains failed.

Inset and Compact each had the same source pattern: `JSON.stringify(value,"",true,true)` for the file and default `JSON.stringify(value)` for stdout. Each proposal computes the full-precision string once and reuses it in both places. The source inverse contains exactly three replacements per file; assertion lines, geometry/input operations, report fields and oracle thresholds remain unchanged. The added CPU negative reproduces the last-digit inequality and confirms the wrapper still refuses it.

Final proposed Inset SHA: `a131f750a99112fbde9c3522caa59de416ea1ecd12e3780b17346e257098baad`.

Final proposed Compact SHA: `d5d81a6fb8fc4454a9c88d4c45ad6654f3672ab57d5c0c4a111361103fc424d8`.

Rail uses the same default serialization for both file and stdout, with integer/bool/string report data, so its source stays unchanged. Behavior writes a full-precision result but has no aggregate JSON marker; its separate toast diagnostics are not compared as result JSON. Lifecycle has matching default serialization on both outputs and no float report fields. No general marker equality, numeric tolerance or engine-error predicate is relaxed.

This audit is source/CPU-only. It does not claim a corrected standard Neon run or a full Windows pass.
