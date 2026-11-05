# Sparse sound mixing

When multiple sound clips leave silent gaps, the mixer now quantizes only the
union of sample intervals that actually received sound. Silent PCM stays exactly
zero. Overlaps are merged so final clipping counts and waveform peaks are counted
once; contributions still sum before clipping. The resampling, trim, fade, gain,
channel and rational start-time calculations remain unchanged.

A frozen corpus from the original mixer verifies full SHA-256 PCM, combined and
per-clip waveform peaks, sample counts and clipping counts across 16 cases:
24fps/30000÷1001, short/long internal mixes, disjoint/overlapping/muted sounds,
trims and fades. The oracle records the baseline source checksum and remains
read-only in the verifier.

The [recorded benchmark](benchmarks/audio_sparse_2026-11-05.json) uses three
0.2-second mono cues at the start, middle and one second before the end:

| Internal mix | Original | Sparse quantization | Speedup |
|---|---:|---:|---:|
| 10 seconds | 270.558 ms | 84.927 ms | 3.19× |
| 60 seconds | 1289.086 ms | 121.949 ms | 10.57× |

Both runs produce the same PCM and waveform digests. These are isolated headless
Godot4.6 software timings, not general playback guarantees. Dense continuous sound
still needs work across its full interval. The mixer still allocates full-length
PCM and a float accumulator; this optimization does not reduce that memory
strategy, raise source budgets or change the existing240-frame project ceiling.
The longer internal mix measures a dependency before project-length work.

```sh
python tests/verify_sparse_audio.py --isolated-display :100
```

Linux requires an explicit private display; Windows retains its private desktop
launcher. The portable check also exercises actual sound-fade editing, Undo/stale
edits, packed/linked files, recovery and lesson snapshots, exact PCM/picture
roundtrips, original WAV preservation, a real H264/AAC movie and decoded fade/peer
magnitudes. No native game assets or physical audio-device acceptance are implied.
