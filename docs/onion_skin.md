# Neighboring drawing guides

In **Draw**, enable **Onion skin**. The active layer's previous exposure appears
blue and its next exposure pink, beneath the current drawing layers and above3D.
Black ink is tinted too. A held drawing does not ghost itself on every held frame;
in a gap, the surrounding exposures remain available as guides. Other layers are
not borrowed. Hidden active layers, Scene/Pose navigation, playback, Home, movie
rendering and a pending fill preview hide the guides.

Advanced exposes opacity5–60%, initially25%. Toggle/opacity are personal tools,
retained through New/Open in this launch and reset next launch. They do not mark
the project dirty, add history/keys or count as autosave actions. No project/model/
world/HAS schema change. Saved pixels, fill sampling, recovery and final movie
frames never contain the guide rasters.

Two GPU alpha-tint materials reuse neighboring cel textures. Idle frames, scrubbing
inside a hold and painting the current cel do not reupload their full-HD rasters.
Drawing stroke, fill commit and pixel Undo/Redo increment a transient Image cache
revision; editing a neighbor refreshes only that texture. It is not PNG/HAS data.
New loaded Image identities invalidate older cached textures. Opacity uses shader
uniforms, leaving original pixel colors/alpha intact. The cache holds at most two
full-HD textures; cold cel caching and general large-document scaling remain open.

The scene background and ghosts use canvas child draw items behind the front
overlay, sharing its exact floating-point image rectangle. This keeps guides under
current opaque paint and aligns all image planes through zoom/pan, without using
Control offset reconstruction. Editor skeleton/review/lesson helpers retain their
existing front placement. The native3D viewport and final compositor are unchanged.

`python -u tests/verify_onion.py` exercises holds/gaps/endpoints, actual tinted GPU
pixels and front stacking, exact source/world/camera isolation, cache reuse and
stroke/Undo/Redo invalidation, Advanced opacity, hidden/empty layers, playback,
zoom/pan, New/Open, recovery, fill sampling, packed HAS metadata exclusion and an
MP4 with exact reopened-preview/export PNG. All graphical checks use the private
Windows desktop. See the latest progress memo for actual counts and saved-copy
status. This is one neighbor on each side of the active layer, not adjustable
multi-frame ranges, motion warping, anatomical advice or native KRA support.

Primary references: [CanvasItem draw order](https://docs.godotengine.org/en/4.6/classes/class_canvasitem.html#class-canvasitem-property-show-behind-parent)
and [CanvasItem shader alpha/color](https://docs.godotengine.org/en/4.6/tutorials/shaders/shader_reference/canvas_item_shader.html).
