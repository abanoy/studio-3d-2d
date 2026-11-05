# Shorten a sound without losing its original samples

Select a sound in **Audio** or click its timeline row. **Shorten sound…** is
available in Simple and Advanced. Choose the **Last frame**, which is included,
then Apply. The start stays where it was; the block, waveform, preview mix and
export all honor the shortened end. **Restore original end** brings back the
remaining original source after the existing source-in trim. One Undo restores
the previous length. Opening/cancelling or applying an unchanged end adds no
history entry. Changing the selected sound or scene invalidates an open dialog.

You can also drag a sound block's **right edge** on the timeline. A blue preview
shows the tentative length; the actual sound/mix/history remain unchanged until
release. Dragging continues outside the panel. The original sample extent and a
one-frame minimum bound the gesture. Extending to the original end restores its
full source and legacy layout. Escape/right-click, control/window focus loss,
New/Open or export cancel; intervening scene/settings/audio edits refuse a stale
release without modifying the current sound. Drag the block's body to move it.
The end handle uses the same source-sample conversion as the dialog.

Autosave, lesson advancement and pending imported-physics activation wait while
a sound gesture is active. This covers existing body moves too. Splitting,
fades and ripple edits remain future work. A hard audio cut may click;
there is no automatic fade or gain modification.

## One shared native sound representation

The optional exclusive `source_out_sample` is an integer in the original
decoded source's sample grid. Original WAV/PCM bytes stay intact. Source-in trim
must remain strictly before source-out, which must be within the source. Moving
the clip moves its shortened playback window; it does not rewrite its samples.
Restoring the end removes the optional field and preserves source-in, gain/mute,
identity and original data. Existing decoded-source memory/clip/time limits apply.

Frame-selected cuts round down to the original sample grid, within one source
sample of the requested scene boundary, so they cannot spill into the next
frame. At44.1kHz/24fps, one frame is1837.5 source samples: its exclusive end is
1837 samples, not1838. Interpolation clamps its final neighbor to the trimmed
source window, avoiding a contribution from a hidden following sample. Each
overlapping clip retains its own window. Scene mixing still sums before output
quantization/clipping and uses the existing single preview/export PCM stream.

Timeline width and dialog endpoints use integer rational-rate arithmetic. This
also fixes older floating-point ceil expansion:2240 samples at8kHz are exactly
seven frames at25fps, but a floating product could become7.000000000000001 and
draw an eighth frame. Partial next frames still remain visible.

## Versioned compatibility

If any clip has an end trim, `audio` uses
`{"format":"studio_audio_3","clips":[...]}`, even for one clip. Individual
rows retain existing fields and optional `source_out_sample`. The new reader
accepts prior single-clip and `studio_audio_2` projects without alteration.
Untrimmed saves retain their prior layout; restoring all original ends returns
to that old layout. Trim values in an unversioned/version2 document are refused.

**Older Studio builds cannot open version3 audio projects.** Their existing
unknown-version guard refuses the scene, preserving it instead of silently
playing past a cut. Use this development build for trimmed scenes and retain
project copies when exchanging work with the older installed application.
No model, scene, HAS container or original audio-asset format is replaced.
Packed/linked storage, recovery and lesson checkpoints use the shared reader and
carry the same sample endpoint. The full original audio remains available there.

Changing project FPS reinterprets the sample-based duration at the new rate,
just as an ordinary audio source duration does; sound playback speed is unchanged.
Native sample endpoints can lie between scene frames. An unchanged Apply preserves
such an endpoint rather than snapping it to the displayed enclosing frame.

## Verification

`python tests/verify_audio_trim.py` runs constrained mixer/timeline cases and
container tests, loads actual previous-checkpoint audio code to verify old-reader
refusal, then runs the private Windows editor with original44.1kHz tones. It
checks Simple dialog/cancel/stale/no-op behavior, a one-frame quantized cut, a
twelve-frame cut with source-in trim, unchanged source samples, exact Undo/Redo,
restoring legacy layout, invalid source-in refusal, block/waveform endpoints,
overlapping peer independence, packed opening with original WAVs hidden, and
fresh packed/linked/recovery/lesson readers with exact audio metadata and PCM.
Ordinary H2641080p24/AAC export includes independent paint; actual decoded tone
windows verify the shortened voice ends while its peer continues. Original WAV
hashes and private-desktop receipts are checked. UI PNG is inspected separately.

The existing multi-audio/native-world and compressed-audio workflows are separate
regressions. Actual runs/results live in the dated progress memo. This is not a
complete Studio regression or subjective hearing/physical-input acceptance.

`python tests/verify_audio_edge.py` exercises actual app-routed pointer capture,
preview-only length/color, release outside the panel, one-step exact Undo/Redo,
unchanged click, one-frame lower bound, extension limited to original samples,
restoring version2 layout, stale revision, Escape/right-click/control/window
focus cancellation, export/New/Open cancellation and existing body-move behavior.
It verifies autosave deferral, unchanged peers/world/camera/source files, packed
reopening with exact PCM, independent paint and timed H264/AAC output. These are
injected application events on a private desktop, not physical mouse acceptance.
