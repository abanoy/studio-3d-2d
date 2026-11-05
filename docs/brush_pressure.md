# Tablet pressure size

Development Draw offers **Tablet pressure size**, off by default. Enable it for
a tablet that supplies pen pressure. The selected radius is the maximum; size
varies linearly with positive pressure, with a half-pixel radius floor so a very
light contact still leaves a mark. Zero pressure paints nothing. Pen opacity /
eraser strength stays independent.
Release and draw again to build up opacity. Choose Eraser normally to erase with
a pressure-sized footprint. Fill and color sampling keep their separate behavior.

Off is the ordinary mouse brush, including mouse events whose pressure is0.
On deliberately waits for positive pressure. An initial button press or zero-only
gesture paints nothing and creates no empty cel/history action. If pressure never
arrives, Studio explains how to return to mouse input. This explicit choice avoids
guessing that a pen's zero-pressure event means a full-strength mouse stroke.
A pressure-less tap cannot produce a pressure-aware mark; switch off to use
fixed-size taps. Tilt and automatically selecting the inverted stylus eraser are
not implemented.

The first positive sample sets the initial small radius. Radius interpolates
between samples as a continuous union of discs, rather than disconnected stamps.
Zero pressure breaks contact; resumed contact starts at its new point without
connecting across the gap. Nonfinite samples are ignored, finite pressure clamps
to0–1. Radius/opacity/tool/pressure choice freeze until release. Native button
release outside the view, focus loss, frame changes and Undo finish pending
gestures. New-cel allocation is deferred until actual pressure paint; its existing
cel Undo remains separate from the single pixel-stroke Undo. A cel-limit refusal
preserves its error and restores the input state.

While a tablet stroke is held, the app temporarily disables Godot's accumulated
input to receive individual motion events. Finish restores the previous value,
including a previously disabled value. The ordinary mouse path is unchanged.
The transient coverage tiles introduced for brush opacity also support tapering;
RGBA8 cels, world/camera independence, layer opacity, HAS and final compositor
remain shared. No new project fields or external-format exporter.

`verify_brush_pressure.py` uses reproducible native `InputEventMouseMotion`
pressure packets through the actual zoomed/panned canvas. Domain cases cover
sparse/dense tapers, stationary/rapid widening, opacity/erasing and invalid radii.
An independent numerical maximization checks six complete64×48 fields against
the closed-form raster, within one RGBA8 alpha unit. Preview/MP4 and fresh-process
reopening still require exact pixel equality. Measured routed-event and full-HD
overlay timings are stored in its report; these are a small local workload, not
physical pen-to-display latency or a dense-art performance guarantee.

The Windows test environment reports Windows Ink as current. Its enumerated
drivers are auto/winink/dummy, with no available Wintab device driver. Physical
Windows Ink/Wintab compatibility therefore remains unverified. No driver was
installed or silently switched, and no universal tablet support is claimed.
Testing a real pen and its available driver remains an explicit acceptance gate.

Primary references: [Godot4.6 mouse motion](https://docs.godotengine.org/en/4.6/classes/class_inputeventmousemotion.html)
defines pressure and event accumulation; [mouse button](https://docs.godotengine.org/en/4.6/classes/class_inputeventmousebutton.html)
has no pressure property; [DisplayServer tablet methods](https://docs.godotengine.org/en/4.6/classes/class_displayserver.html#class-displayserver-method-tablet-set-current-driver)
describe Windows Ink, Wintab and the requirement for a compatible device driver.
