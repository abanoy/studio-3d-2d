# Brush opacity

Development Draw has **Brush opacity (%)**, available in Simple and Advanced.
100% keeps the previous full-strength pen and eraser. Lower values paint faint
ink or erase gently. 0% does nothing and does not create a drawing. Pen color
alpha multiplies brush opacity; erasing uses strength independently of pen color.
Fill retains its separate existing controls.

Retracing within a translucent stroke does not repeatedly darken its pixels.
Release and start another stroke to build up ink or erase further. Radius, color,
tool and strength are captured when the stroke starts. Release outside the view
and window focus loss finish it through the existing input paths. One stroke has
one pixel Undo; an automatically created cel retains its separate existing Undo.
Brush settings are session controls, like the current radius/color, rather than
authored scene values. Default opacity is100% on a new launch.

Partial strokes keep the original touched64pixel tiles plus a transient float
coverage mask. Each pixel blends once against its pre-stroke value using the
maximum coverage encountered. This avoids dependence on collinear event density
and repeated passes. A full1080p mask is bounded to about7.9MiB; sparse strokes
allocate only touched tiles. Masks are freed on finish, never serialized or
charged as retained Undo. Existing before/after pixel tiles remain under the
64MiB/128action history budget. Full-strength opaque strokes retain the old
distance-to-segment raster path, including its existing edge behavior.

The result is ordinary RGBA8 cel pixels. Layer opacity, onion guides, transparent
PNG, packed HAS, recovery and MP4 use the existing shared raster/compositor; no
scene schema or importer changes. This is opacity per stroke, not a flow-rate
control or texture brush. A newer opt-in [pressure-size brush](brush_pressure.md)
uses the same pixels. Tilt and inverted-stylus tool selection remain unfinished;
no physical tablet acceptance is claimed.

`tests/verify_brush_opacity.py` checks raster invariance, native routed editor
input, Undo/Redo, setting capture, outside release/focus completion, layer
opacity, a moving common-format3D scene, packed Save/fresh-process Open and exact
preview/movie PNG. Graphical runs use the private Windows desktop. Exact scope,
results and saved checkpoint are recorded in the dated progress memo.

The [Godot4.6 mouse-motion documentation](https://docs.godotengine.org/en/4.6/classes/class_inputeventmousemotion.html)
provides pressure0–1 and an inverted-pen flag. The documented default pressure
is0. A pressure brush therefore needs an explicit mouse fallback and a policy
for the initial button event; forwarding the pressure field alone is insufficient.
The newer pressure-size mode addresses this through explicit opt-in and deferred
painting, rather than automatically guessing which input device is in use.
