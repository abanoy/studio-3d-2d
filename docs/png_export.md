# PNG sequence export

MP4 remains the normal navbar export. In **Advanced → Movie encoder**, use
**Export PNG sequence…** for an image sequence beside the saved HAS. An unsaved
scene asks for a destination. **PNG to another folder…** always lets you choose.
Each export creates a fresh `images_*` directory; earlier sequences remain intact.
No FFmpeg executable or codec detection is needed.

Leave **PNG: drawings only (transparent)** off to export the complete scene and
visible drawings through the same final renderer as MP4. Turn it on to export
only visible drawing layers as RGBA with transparent empty pixels. Cel holds,
layer order and opacity are retained. Editor grid, selection and onion guides
are excluded. Drawing-only output does not render the 3D background.

If the scene has audio, `mixed_audio.wav` contains the exact full-length48kHz
stereo preview mix, including clip placement, trims, gains and fades. Silence is
padded to the intended sequence duration. A silent project has no WAV sidecar.
Audio is separate from PNG files, so external compositing software can align it
to the same time origin.

`frame_000001.png` corresponds to project frame0 at time0. The last file is
`frame_NNNNNN.png` for the number of duration frames. `sequence.json` records
format `studio_image_sequence_1`, output video dimensions, rational FPS and
intended duration, the numbering pattern, first project/file frame, actual
rendered frame count, drawing-only setting, audio filename and completion state.
Frame n's timestamp is `n * fps_den / fps_num`, starting from project frame0.

Cancel keeps completed images. A failed image/WAV write reports the error and
keeps existing output. On normal completion, cancellation or handled failure,
the timing record is written through a temporary file and rename. If that write
itself fails, the images remain usable and the error names the output folder.
**Show saved frames** exposes both successful PNG exports and incomplete output.
No successful movie or completed movie tutorial is reported for PNG-only output.
An earlier finished movie remains available separately.

Rendering shares the existing export controls, physics-freeze policy and final
scene evaluation. It restores the prior editor view/mode/playhead and keeps shot
keys, drawing sources and authored records unchanged for the tested frozen scene.
This does not add a per-shot export range, automatic image-sequence reimport,
resume rendering, a new scene schema or a model-format exporter. A sudden process
or power failure may leave frames without a completed timing record; disk-full
and clean-machine behavior are not certified by the targeted tests.

## Verification

`python tests/verify_png_export.py` runs the actual hidden Windows app on an
original GLB room, animated camera, held red/blue cels with50% layer opacity and
faded audio. It verifies the Advanced action, saved-project destination, complete
scene PNG equality with the final renderer, exact transparent Drawing composite,
exact WAV PCM,48files at24fps,6silent files at25/2fps, no FFmpeg/movie/log, unique
output directories, editor/source/history isolation and no movie-completion
signal. Cancel and deliberately obstructed PNG/manifest paths check retained
frames, exact partial counts and restored controls. These are scoped fault
injections in owned output, not a real full-disk or power-loss test.

After adding the GUI-action check, one assertion incorrectly compared the last
output folder with an older transparent export. It now captures the immediately
preceding output before checking encoder refusal; no product behavior or boundary
was weakened. Existing MP4 cancellation/retry and audio compatibility regressions
are separate checks recorded in the dated progress memo.
