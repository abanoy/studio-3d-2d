# Project timing

**Options → Scene length (frames) → Apply scene length** changes the shot length
in Simple or Advanced, from 1 to 240 frames. The number is a duration: 24 frames
exports frames 0–23; frame 24 is an editable end boundary. Entering a value is a
draft until Apply. Scrubbing preserves that draft; New/Open and actual timing
changes refresh it. One Undo restores the previous length and exact audio mix.

Extending keeps all existing frame addresses, pose keys, camera keys, drawing
exposures and sound metadata. It adds scene time without stretching drawings or
blocks. A held model remains held; a drawing ending at frame 48 still ends there.
Posing, the frame field and timeline all use the new length, including after Redo.

Shortening refuses camera keys beyond the new end, drawings extending past it,
sounds starting at or after it, and object/effect animation that would no longer
validate. Move, remove or shorten that content first. A camera key exactly at the
end boundary is retained. Source sound tails may continue beyond the scene; only
the mixed output stops at the new scene end. Extending or Undo restores access to
those original samples. No automatic shot-end fade is added.

Active recording, export and unfinished pose/drawing/timeline gestures defer
changes. An over-budget mix refuses before changing settings or history. Playback
stops, and shortening clamps the current playhead to the new end; Undo preserves
the resulting playhead rather than restoring an old navigation position.

## Frame rate

Open **Options → Project frame rate** in Simple or Advanced. Presets include12,
15,24,25,30,48,50,60 and120fps, plus23.976,29.97 and59.94 using their exact
24000/1001,30000/1001 and60000/1001 fractions. New projects still default to24fps.
An already loaded custom rational rate is shown without rounding its stored
values or forcing a preset.

Changing rate **keeps frame numbers fixed**. It changes the real-time duration
and playback speed of frame-based keys/cels; it does not resample or rekey them.
A key at frame24 remains at frame24. At24fps that is1second; at24000/1001 it is
1.001seconds. Imported source audio is not stretched or pitch-shifted: its start
stays on the chosen frame, while samples, source trims, gain and fade durations
stay intact. Time-based particle source caches likewise retain their seconds
clock within their frame-addressed clip. Reprepare a source effect if a different
cache duration is needed; this control does not bake a new simulation.

The change stops playback/captured navigation, rebuilds the shared audio mix and
waveforms, updates the transport label and creates one Undo action. Undo/Redo
rebuilds the exact corresponding mix and selector. A no-op adds no history.
Invalid rates, an over-budget audio duration or an active physics recording refuse
before replacing timing; finish/cancel a take first. Opening a saved project loads
its rate normally without changing personal navigation/display preferences.

## Data and limits

Existing `video.fps_num` / `video.fps_den` fields remain the canonical rational
clock; there is no new model/container schema. Save/Open and particle evaluation
share a validator: positive whole numerator up to120000, denominator up to1001,
and actual rate at most120fps. Previously valid slow rational rates remain
readable, subject to the existing audio/project bounds. The presets avoid those
unusual low rates. There is no general numeric custom-rate editor yet.

The old reader capped the numerator at120, so it cannot open the new large-
numerator fractional rates even though their actual FPS is ordinary. The older
reader refuses them rather than changing playback. Use project copies with old
installed apps/reviews. Whole-number presets within the earlier range retain
their existing representation.

This increment does not change1920x1080 resolution, the240-frame project limit,
source/clip budgets, the60-second mixed-audio limit or synchronous mixing. It does
not add automatic keep-seconds retiming, drop-frame timecode, longer projects,
resolution settings, source-audio time stretch or externally exported model data.

## Verification

`python tests/verify_project_duration.py` exercises extension to 96 frames, a new
automatic pose key at frame 72, Undo/Redo of both edits, protected shortening,
source/mix/hold isolation, pending fields, invalid and busy/budget refusals,
smaller-window layout, and fresh packed/linked/recovery/lesson readers. Its
24-frame fractional-rate H264/AAC movie retains exact preview/PNG agreement and
frame-12 sound placement. Reports and hidden-desktop receipts are saved under
`output/project-duration-verification.json`. These are scoped same-machine checks,
not a complete regression, physical pointer or subjective audio acceptance.

`python tests/verify_project_timing.py` checks presets/invalid inputs, preservation
of legacy rational rates, an isolated particle clock probe, actual Simple preset
selection, exact sample placement at frame24, unchanged frame addresses/scene/
shot/source data/editor view, Undo/Redo/no-op, integer12fps, custom25/2fps,
recording/over-budget guards and the real older-reader refusal. Packed and linked
HAS, recovery and tutorial snapshots are read in fresh app processes with exact
rate, mix hash and selector checks.

The writer exports48 H2641920x1080 frames at24000/1001fps, lasting2.002seconds,
with an independent drawing and exact preview/export-frame comparison. The PCM
mix has96096stereo samples; frame24 begins at48048. Decoded AAC onset is measured
separately with a small codec-window bound. Actual measurements and private-
desktop receipts live in output/project-timing-verification.json and the dated
progress memo. This is analytical timing, not subjective listening or arbitrary
native-motion/long-project acceptance. Existing visibility and native-particle
regressions are separate evidence, not a new complete Studio regression.
