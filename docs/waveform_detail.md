# Waveform detail while zooming

Zoomed sound tracks now use cached peak levels from256 to8192bins across the
scene. A suitable level follows the visible range and available width; Fit keeps
the existing256bin overview. Short cues late in a longer project therefore show
more of their envelope instead of stretching a few overview bars.

The mixer builds the cache from the same per-clip samples, gain, trims, fades and
mute state it already evaluates. Coarser levels preserve the exact maximum of
their finer bins. Single-clip and multi-clip peak semantics remain unchanged.
Nested projects retain the correct independent cache for each scene's own sound
rows. The mixed PCM, global/per-clip overview peaks and clipping counts retain
exact frozen-oracle results.

Zoom and pan select cached levels and draw only their visible bins. They do not
re-read a source file, rebuild the mix or resample source audio. Range changes
leave project history and dirty revision unchanged. Gain/mute/trim edits rebuild
the cache with the mix; Undo restores the original PCM and detail. A peak bin
straddling the sound's start is clipped to that boundary so its first transient
remains visible.

Six peak arrays contain64512bytes per clip, including its existing overview;
16clips use1032192bytes of float payload, plus array/dictionary overhead. The64MiB
source/mix limits,16clip budget and60second timing envelope remain unchanged.
The cache adds bounded work during mixing and remains transient editor data;
no project format or original source changes. It is a peak overview rather than
a source-sample editor. The finest level spans about7.3ms per bin in a60second
scene, and viewport pixels can still merge nearby details.

`python tests/verify_waveform_levels.py --isolated-display :101` requires an
already-provisioned private Linux display; Windows uses the existing private
launcher. It checks exact level reduction, four independently placed transients,
nested cache ownership, GUI pixels with the WAV temporarily unavailable, gain/
mute Undo, and unchanged PCM. It also runs the frozen sparse-audio corpus, actual
fade/AAC/cold-reader checks and the timeline/workspace/channel regression. Optional
native fixture skips stay separate from procedural checks.

A three-run headless comparison againstd7d42f2 measured10second mixing at84.343→
88.667ms and60second mixing at113.405→115.995ms for three original0.2second cues.
PCM/overview hashes are identical. The60second tracked peak rose94,924,391→
95,320,107bytes, including retained results during replacement. These are scoped
machine measurements, not a general latency guarantee; an earlier single pass
was121→141ms. Raw comparison metadata is in
[the benchmark artifact](benchmarks/waveform_levels_2026-11-05.json).
