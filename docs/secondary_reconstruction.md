# Make a reviewed part flexible — experimental

In **Set up loose parts**, select a connected section and explicitly enable **Make this part flexible**. Orange lines show the selected source triangles; the notice states its vertex and guide-group counts. **Include in setup** checks or excludes a section. Nothing is installed until Apply. Outlines, bangs and other unchecked surfaces are not automatically included or matched by material name.

This option creates a separate owned HAS asset. Each original influence gets a guide attached to that same native joint. Original nodes, rest transforms, native joint/bind prefixes, vertex positions, morph targets, materials and animation tables remain in their original order. Only the reviewed vertices receive derived weights. At guide rest, the construction preserves the original FK algebra; it never overwrites the imported source. One Undo restores the original asset and edits.

After Apply, choose **Natural gravity** beside **Hair & clothes** for downward settling, then enable Hair & clothes. **Keep hair shape** retains the current rest-shape bias. **Try a local blow** can test the checked reconstruction before Apply without authoring the candidate into the scene. Hair & clothes Off restores authored transforms. Existing native physics is not reinterpreted.

## First-component result and limitations

The protected diagonal Junko model has 3,629 vertices on its colored back-hair surface, separate front/bangs and ribbon surfaces, and additional outline geometry. This first increment explicitly reviews one 1,292-vertex connected colored section. It builds 13 per-influence guide chains with 65 appended nodes. It does **not** configure the other back-hair sections or their outlines; those can visibly retain the old diagonal shape while the checked section moves. The full Junko request remains open.

After 720 fixed steps, the entire reviewed section's centroid dropped 12.24 cm, exceeding the retained 1 cm criterion. All original joints and guide attachment positions stayed fixed; Off restored every reviewed vertex exactly in that CPU observation. Actual contact was present: 52 collider instances, 1,236 affected cached skin rows and 720 refreshes. No sampled contact pairs remained in that trial. This is a bounded skeletal test, not universal collision or appearance acceptance.

The measured loop took about 12.5 ms per 120 Hz step, exceeding an 8.33 ms real-time step budget. It needs performance work before claiming smooth playback on this hardware.

The private Simple UI test passed 18 of 19 controls, including temporary wind, Apply, Undo/Redo, nonzero native Head FK and a pose key, Natural live startup, Off and source preservation. **Exact rest-image preservation failed:** 165 channel bytes differed at the properly framed view, and actual imported posed vertices differed by up to 0.00004823 m. The source-level FK/morph algebra passed separately; it does not prove identical imported packing or rasterization. Investigate four-to-eight-weight normalization/UNORM16 conversion and bind/accumulation precision before resolving this defect. The exact-zero image assertion remains a failing control; no pixel allowance was substituted.

The supported authoring profile requires original float32 weights with at most four nonzero influences per selected vertex; splitting never exceeds eight slots or silently truncates. Shared guides across skins require compatible relative bind frames. Unsupported/ambiguous surfaces, imported physics joints, incompatible frames and budget excesses are refused. Shared outline surfaces merged with front hair need explicit masks/correspondence, not an automatic weld.

## Focused checks and pickup

`python tests/test_secondary_reconstruction.py` runs 11 generated-only preservation/admission tests. `python tests/test_reconstruction_wind_mapping.py` runs 16 generated-only wind-binding checks, including translation, parent, scale and inverse-bind tampering. Existing helper/batch/morph suites and the protected Miku 54-check contract passed separately.

`python tests/verify_secondary_reconstruction.py` runs the generated-only checks. Optional `--source <read-only GLB> --region <node> <primitive> <component>` prepares a private candidate and checks actual imported weighted geometry headlessly. The protected Junko-only `--gui --gui-only` route requires the approved private Windows desktop; its exact-image check currently remains adverse. No source assets, vertex arrays or screenshots are embedded in these tests or the scalar benchmark.

The standalone `tools/secondary_reconstruction.py` accepts a source, explicit recipe and **new** output folder. A recipe uses `studio_secondary_reconstruction_1`, a matching source checksum, `reviewed: true`, `segments` and a list of `{node, primitive, component}` regions; optional vertex masks and reviewed controls remain explicit. Multi-region recipes can share guides, but only the one-section native result above is qualified. Next work: explain imported precision drift, review the other colored back-hair groups, pair outline masks without crossing into bangs, and reduce the multi-chain contact cost.

See [the compact benchmark](benchmarks/secondary_reconstruction_20261121.json). The prior existing-chain 13/14 settling failure is retained and is not relabelled by this result.
