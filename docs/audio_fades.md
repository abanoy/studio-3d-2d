# Sound fades

Select a sound in the timeline or Audio chooser, then **Fade sound…** in Simple.
Set fade-in and fade-out durations in milliseconds; 0 disables that end. Apply
creates one Undo action. Cancel leaves samples, mix and history unchanged.
**Remove fades** restores full level while keeping gain, source trims and timing.
The dialog is nonexclusive; changing the selected sound, scene, timing or project
while it is open invalidates its pending edit instead of overwriting newer work.

Fades are nondestructive per-clip gain envelopes, applied after source resampling
and before overlapping clips are summed and quantized. Preview, waveforms, saved
mix and MP4 all use the same48kHz stereo PCM. Original WAV/normalized import bytes
are retained. Other clips keep their own level and timing; fades do not move
camera keys, model animation or drawing cels.

Each linear ramp includes a zero endpoint and a full-level endpoint on the48kHz
output sample grid. A requested duration is limited to the available trimmed
source duration. If ramps overlap they multiply, producing a softer middle;
they do not normalize or automatically boost volume. A one-sample sound with a
fade becomes silent. Stored durations remain the user's requested values when
the sound is shortened or extended. Fade-out follows the sound's source end,
not the shot boundary: shorten an overlong sound if it should fade before the
movie ends. Durations do not change when FPS or clip placement changes.

## Native data and compatibility

Optional `fade_in_ms` / `fade_out_ms` are positive whole milliseconds1–60000.
Omitting a field disables it. Any faded clip requires the versioned collection
`studio_audio_4`, including a single sound; end trims may coexist in that format.
Old single/version2/version3 scenes remain readable and keep their previous mix
when no fades are present. Removing all fades returns to version3 if an end trim
remains, otherwise the prior single/version2 layout.

Older Studio readers refuse version4, rather than silently ignoring fades.
Keep project copies when using an older installed app or review. Packed/linked
HAS, recovery, lesson snapshots and Undo retain the same fields; this adds no
scene/model schema or external-format exporter. Existing audio/source/metadata
budgets still apply. There are no automatic crossfades, gain keyframes, pan,
curve editing, loop controls or recording in this increment. Mixing remains
synchronous and bounded; subjective sound quality is owner acceptance.

## Verification

`python tests/verify_audio_fades.py` runs25 domain checks and an actual private
Windows editor: Simple dialog, preview-only fields, cancel/no-op, one-step Undo/
Redo, stale scene/selection refusal, remove/restore, end-trim coexistence, packed
reopen with original WAVs temporarily unavailable, independent drawing and exact
preview/export PNG. Four fresh processes read packed/linked/recovery/lesson data
with exact metadata values and mixed PCM hashes. The resulting movie must have
48 H2641920x1080 frames at24fps and AAC with analytically measured fade ramps.
This is sample analysis, not subjective listening or physical mouse testing.

The initial direct Dictionary comparison treated integral JSON numbers read as
doubles as different from authored integers. Diagnostic before/after metadata
proved numerically identical and PCM hashes matched. Tests now compare exact
JSON values with no numeric tolerance, independently checked in Python, while
retaining the strict audio-byte check. Earlier failed logs remain in owned output.

`tests/test_has_project.py` also checks packed/linked fade metadata, coexistence
with an end trim, unversioned/invalid duration refusal and preservation of an
existing file on failure. Actual regression/checkpoint status is recorded in the
dated progress memo; this is not completion of the full Studio roadmap.
