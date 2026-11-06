# Reusing PNG verification within a save

Content-addressed Save/recovery checks now retain verified encoded-byte and pixel
hashes for one save operation. Every cached file is still opened and read, with
size, PNG signature and canvas dimensions checked before reuse. New bytes get a
full PNG decode and canonical RGBA checksum. Source artwork is freshly hashed
for every cel, so raw edits cannot be hidden by stale pixel-revision metadata.

The verifier retains strings only. Decoded validation Images die at each call,
so distinct-art projects do not accumulate another32fullHD buffers. Each child
scene save has its own verifier. No persistent cache, project fields, schema or
resource-limit changes are introduced.

This also repairs an existing cache-validation gap: a PNG with the same RGBA
byte sequence but different dimensions could previously pass the pixel-hash
check. Such a member now fails verification and is atomically rewritten from
the authoritative source Image before the manifest is committed. Truncated or
changed cached members likewise trigger the existing repair path.

The original32cel1080p warm-save benchmark changed from2388.642/2401.420/2370.599ms
to915.003/905.909/903.673ms. Fixture creation and readback are excluded; all32cel
RGBA hashes survive readback. These are scoped headless measurements, not whole
Studio responsiveness or hardware frame-rate claims. Reproduce with
`tests/cel_save_benchmark.gd` through `run.command(..., headless=True)` and a fresh
output directory after `--`.

`tests/cel_png_verifier_unit.gd` passes10checks: one decode for repeated bytes,
every-file reads, digest-only ownership, bad expected hash, missing/changed file,
normal Save, equal-pixel/wrong-dimension repair, truncated PNG repair and invalid
later-save preservation. Proof and benchmark logs are under
`/workspace/has-handoff-audit/cel-png-verifier-unit.log` and `cel-save-cached.json`.

Existing61raster workflow checks plus16PNG compatibility cases,70reference/
lesson checks and312Python tests (311pass,1existing skip) also pass. Scoped
raw timing/source hashes: [measurement](benchmarks/cel_save_verification_2026-11-06.json).
