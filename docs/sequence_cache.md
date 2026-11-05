# Held artwork cache

An editable drawing held for many frames now reuses its sequence picture while
the parent continues evaluating clip placement, opacity and shadow. An empty
child world also bypasses an unnecessary transparent3D capture. This reduces
repeated full-HD readbacks, alpha conversion and mip generation for held artwork.

The cache identifies visible held images by image identity, marked pixel revision
and layer opacity/order. It changes at exposure boundaries and after marked pixel
edits, including an edit at the same frame. Hidden/zero-opacity layers do not
contribute. Nested scenes and scenes containing world objects or effects keep
frame-by-frame evaluation; their animation, cameras, visibility and VFX cannot be
inferred static from an ink hold. Drawing-only output can reuse its independent
paint picture while excluding the world. Runtime replacement still invalidates
all caches after ordinary child edits. No new project format or persistent data.

In a240-frame1920×1080 procedural test with two120-frame holds, animated parent
placement and soft shadow, source picture builds dropped240→2. Cached assets stayed
at1. Every moving sample retained the right cel and shadow alpha; source pixels
stayed unchanged and first/last rendered hashes matched the pre-change baseline.
On this private Linux llvmpipe display, mean sample time was734.9→341.2ms, total
176.4→81.9seconds. These are exploratory software-renderer observations from one
run per version, not a hardware latency promise or24fps acceptance. The JSON
[measurement record](benchmarks/sequence_cache_2026-11-05.json) retains both runs.

Run `python tests/verify_sequence_cache.py --isolated-display :99` on Linux using
an already provisioned private display; Windows retains private-desktop checks.
The optional `--baseline-report` compares exact hashes to an archived baseline,
without asserting a machine-dependent timing ratio. `--baseline` in the Godot
measurement script labels a pre-optimization measurement explicitly and does not
claim the two-build acceptance gate passed. The baseline was captured on711c949
before changing the runtime. Final runtime regression also tests same-frame pixel
revision invalidation, exact source restoration, nesting and queued cancellation.

Child scene duration remains at most240frames; [extended parents](extended_timing.md)
support up to60seconds and7200frames. Shared cels remain at most32 and cached
asset pictures at most4. Audio, undo and archive limits stay in place. This is one
measured caching improvement, not support for arbitrarily long or dense projects.

[Sequence masks](sequence_masks.md) additionally cache up to8 derived per-clip
textures in each runtime; the original shared source-picture cache remains at4.
