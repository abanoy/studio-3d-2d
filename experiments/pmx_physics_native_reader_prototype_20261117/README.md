# Direct PMX2.0 native physics reader prototype

This isolated source/CPU prototype reads exact native physics-table bytes from an in-memory PMX2.0 stream after a bounded prefix traversal. It preserves native body/joint references, raw F32 words and byte offsets plus a bone catalogue and sourceSHA. It is inactive and does not change HAS import, rendering, simulation or the current Windows review.

Read `CURRENT_CONTRACT.md` for the implementation policy. `LAYOUT.md` is the preserved historical independent layout design, not the current finite-policy or metadata-size contract. The parser intentionally retains/classifies nonfinite raw words without claiming valid physics. It does not import or execute the tolerant installed MMD reader; that primary source is pinned in `SOURCE_BINDING.json` and was inspected as code only.

`MANUAL_FIXTURE_EXPECTATIONS.json` is a separate authored339-byte fixed-offset oracle. `synthetic_pmx.py` was written independently without using this parser and includes full prefix variants, manually captured field/record offsets, Japanese names, duplicate bone names and raw signedzero/subnormal/NaN/Inf word challenges. Its geometry and physical parameters have no validity qualification. The tests compare sourceSHA, exact table boundaries, native indices, raw names and every native physics word; they also exercise selector/count/UTF/resource/refusal guards, all truncation points, mixed index-width roles and unsigned vertex indices.

Run only CPU tests with Python: `python -B -m unittest discover -s <this folder> -p "test_*.py" -v`.

This is a source-only packet. Native PMX file reads, integration and portable/cold/runtime qualification remain root-owned future work; no corresponding success is asserted here. No artist assets, previews, native arrays or generated model files are included. The API returns metadata and performs no writes.
