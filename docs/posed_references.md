# Poseable working references

Select a model in Pose and enable **Reference only (hide in movie)**. The model
stays available while drawing and disappears from final captures and movie output.
Use **Reference opacity (%)** and **Apply** to fade the working reference. Zero
hides its geometry; 100 restores the normal appearance. The selected-object guide
remains an editor aid. Turning Reference only off restores full output geometry;
the working amount is retained for the next time you enable it.

The amount is saved per model and each Apply is one Undo command. It does not add
pose keys or change original materials/model files. Old projects default to 100%.
The optional `reference_opacity` value is a finite number from 0 through 1, checked
by the Godot model reader and the HAS asset reader. Full opacity omits the field.
Recovery and packed save/Open preserve the setting and independent drawing pixels.
Older builds may ignore this new working-opacity setting. Fading uses the existing
instance-local standard material path; arbitrary custom shaders are not certified.

Root and bone poses keep their ordinary shared-timeline interpolation. Orbiting a
model changes only the inspection view until a camera key is explicitly saved.
Visibility keys remain separate from Reference only and working opacity.

```sh
python tests/verify_posed_reference.py --isolated-display :109 --output /absolute/new/result
```

Linux needs a provisioned private display; Windows uses the existing private
launcher. The November 7 run passes 15 engine, 23 container, 37 actual-app and 7
fresh-reader checks. It exercises an original included 17-bone character waving
and turning, three-quarter orbit, actual reference/visibility/opacity controls,
Undo/Redo, recovery, packed cold Open and a 48-frame 1080p/24 H.264/AAC movie.
Five reopened poses and three final images match exactly with the owned original
sources and writer cache unavailable; audio begins at sample 48001 as expected.
The shared-model walking regression passes all 98 checks.

[Curated acceptance evidence](benchmarks/posed_reference_2026-11-07.json) covers
POSE-04's reference-only software contract. Native-format fidelity, physical
Windows/device performance and artist comfort remain separate requirements.
