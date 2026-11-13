# Existing movie refusal and fresh audio verification

The full Windows run at `3a6f94f9b40d587d529bfcba9139a58ad615ab78`
passed all functional groups, then failed the final expected-AAC assertion.
Its 947 functional file hashes and HEAD stayed exact throughout. This run
remains failed; its later media checks were unrun.

The silent and tone spike tests reused `output/spikes/movie.mp4`. That movie
predated the run. FFmpeg refused to overwrite it with `-n`, printed an error,
and returned zero. The encoder accepted zero plus an existing file and reported
success. Older official FFmpeg source maps this refusal's `AVERROR_EXIT` to zero;
the installed build reproduces that behavior. Godot's Windows process polling
preserves the actual exit code: a controlled child that writes partial output
and exits 37 retains 37 across repeated polls.

The encoder now clears the previous success path at attempt start, refuses an
existing movie or directory before launching or writing a log, and rejects
error-level FFmpeg diagnostics even when the reported exit is zero. Existing
movies, logs and frames are preserved. Retry keeps its separate output filename.

Each default suite run now owns fresh silent, failure and tone folders. The tone
test never reuses the silent movie. Original AAC, frame/rate/duration, decoded
onset and audio-level assertions remain; a separate silent-spike stream check
was added. The shared final media function supports focused verification without
writing a partial result to the default aggregate file.

The strengthened failure suite passes five checks with real FFmpeg and the
approved Python runtime. An isolated preserved old encoder fails the new existing
output test and reproduces the zero-exit refusal. The corrected focused run
checks 21 movies: two newly encoded silent/tone movies plus 19 retained workflow
movies from the failed full run. Both decoded onsets are 1.0 seconds; editor
audio RMS is 5658.30 within the unchanged 5300–6000 bound. Two clean private
graphics receipts and unchanged functional sources are recorded.

That focused run is not a new full aggregate. The first restricted-context
graphics launch refused private desktop creation before starting the test;
its receipt is retained. A fresh run in the approved host context used private
desktops, with no visible fallback.

Run `python -B tests/verify_export_failures.py` for the self-contained headless
failure checks, then `python -B tests/verify.py` for the full default suite with
the documented native fixtures. Source, old failure, counterfactual, research
and scoped evidence are saved under `experiments/encoder_output_guard_20261113`.
Restore diagnostic scripts to `output/encoder-existing-output-20261113` before
running them; do not write generated work into the archive. Full media replay
needs fresh workflow reports or the explicitly retained private artifacts.

See [compact evidence](benchmarks/encoder_existing_output_fix_2026-11-13.json).
