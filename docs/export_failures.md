# Encoder failure checks

Run `python tests/verify_export_failures.py` for a self-contained headless
encoder-adapter check. `--output /absolute/new/directory` keeps its proof outside
the checkout. It uses the configured real FFmpeg and original generated RGB color
bars; it needs no historical `output/spikes` render or native assets.

The existing three engine assertions remain: a missing frame sequence reports
FFmpeg failure and preserves a log; a missing executable on retry reports its
location and preserves a separate diagnostic; cancellation clears the owned
encoder process ID and preserves PNG inputs. The Python wrapper additionally
checks the exact hashes/counts of all48 original/copied1080p PNGs and the separate
failure/cancellation logs. The original no-argument GDScript path still works for
the full verifier after its normal spikes stage.

The 2026-11-06 cloud run passes all three engine assertions and the wrapper's
artifact checks. Proof: `/workspace/has-handoff-audit/export-failures-accepted/verification.json`.
This headless adapter test does not verify window interaction, disk-full handling,
render-stage cancellation, audio devices or every application export fault.
