# Make a reviewed part flexible — experimental

In **Set up loose parts**, select a connected section and explicitly enable **Make this part flexible**. Orange lines show the selected source triangles; the notice states its vertex and guide-group counts. **Include in setup** checks or excludes a section. Nothing is installed until Apply. Outlines, bangs and other unchecked surfaces are not automatically included or matched by material name.

This option creates a separate owned HAS asset. Each original influence gets a guide attached to that same native joint. Original nodes, rest transforms, native joint/bind prefixes, vertex positions, morph targets, materials and animation tables remain in their original order. Only the reviewed vertices receive derived weights. At guide rest, the construction preserves the original FK algebra; it never overwrites the imported source. One Undo restores the original asset and edits.

After Apply, choose **Natural gravity** beside **Hair & clothes** for downward settling, then enable Hair & clothes. **Keep hair shape** retains the current rest-shape bias. **Try a local blow** can test the checked reconstruction before Apply without authoring the candidate into the scene. Hair & clothes Off restores authored transforms. Existing native physics is not reinterpreted.

## Original rendering at authored rest

New reconstructed assets retain the original weight-accessor references in
`extras.has_secondary_rest_views_1`. The importer creates two mesh resources for
the same scene instance: original weights at exact authored guide rest, and
flexible weights for live simulation or edited/recorded guide poses. Native
ancestor poses can change without selecting the flexible view. Generated
ancestors of weighted guides are tracked even if they have no direct weights.

Both views share the corrected source materials. Instance material overrides,
expressions, skin identities and source geometry are preserved across switches.
Contact runners hold a controller-scoped flexible-view lease until their caches
are disposed. Hidden-candidate reparenting and thumbnail clones bind their own
controllers; stale leases cannot release a new controller. Render-bounds caches
are rebuilt only on an actual mesh transition, and editor ID/outline copies
follow that transition too.

The new native Simple check passes **19/19**: the resting image has zero changed
channel bytes, and all **37,470** imported posed vertices match exactly. Off
restores authored transforms. Public generated lifecycle/clone checks and editor
proxy checks pass **36** controls. The older `7f1d85d7` result below remains a
recorded failure; it is not relabelled. Legacy derivatives without original-weight
references retain their previous behavior; references are never guessed.

A live simulation keeps its flexible resource while it owns contact caches,
including a direct final-mode evaluation during that lease. The exact-rest result
above covers ordinary authored rest without a live owner. Recorded/manual guide
poses keep flexible geometry when Hair & clothes is off. Portable save/reopen and
movie qualification now passes the bounded **30-check** scope below.

## Portable project and four-frame movie

One protected first-component candidate passes 19 writer checks, 10 fresh-process
reader checks and one FFprobe contract. Its four authored frames are rest,
edited guide FK, the same edited FK, and rest, with a constant nonzero native Head
pose. Standard export produces actual H.264 at 1920 × 1080, 24 fps and exactly
four frames. Every uncompressed movie-source PNG matches its preview exactly.

The cold reader receives only the packed HAS and private expected-state file.
The writer's Studio, data, profile and owned input copy are unavailable during
that read, then restored. All four cold images, rest/flexible selections and
native Head/guide transforms match exactly; the complete saved pose/key values
match in the ordinary JSON-number representation. Original inputs, test sources
and runtimes remain unchanged, and both private jobs and the inspection process
close. The packed owner-review file and media stay local.

Three failed attempts remain recorded: a fixture called scene-length controls
before opening Project options and saved 48 frames; a strict FFprobe file-read
guard refused before creating its child, with its internal identity change
unproven; and a container comparison rejected 74 integer/float type differences
with zero value or native-quaternion differences. The final fixture compares the
complete JSON-number-domain state plus exact native transforms for every frame.
No author field or pixel tolerance was removed. See the
[scalar evidence](../experiments/reconstructed_rest_movie_20261121/EVIDENCE.json).

This checks authored guide keys without a live simulation owner. It does not
qualify a new physics bake, whole-hair coverage, all-frame collision, performance
or owner appearance acceptance.

## First-component result and limitations

The protected diagonal Junko model has 3,629 vertices on its colored back-hair surface, separate front/bangs and ribbon surfaces, and additional outline geometry. This first increment explicitly reviews one 1,292-vertex connected colored section. It builds 13 per-influence guide chains with 65 appended nodes. It does **not** configure the other back-hair sections or their outlines; those can visibly retain the old diagonal shape while the checked section moves. The full Junko request remains open.

After 720 fixed steps, the entire reviewed section's centroid dropped 12.24 cm, exceeding the retained 1 cm criterion. All original joints and guide attachment positions stayed fixed; Off restored every reviewed vertex exactly in that CPU observation. Actual contact was present: 52 collider instances, 1,236 affected cached skin rows and 720 refreshes. No sampled contact pairs remained in that trial. This is a bounded skeletal test, not universal collision or appearance acceptance.

The measured loop took about 12.5 ms per 120 Hz step, exceeding an 8.33 ms real-time step budget. It needs performance work before claiming smooth playback on this hardware.

The earlier `7f1d85d7` private Simple UI test passed 18 of 19 controls. Exact rest-image preservation failed by 165 channel bytes, with imported posed-vertex drift up to 0.00004823 m. Actual engine readback and protected-input counterfactuals identified aggregate weight packing as the dominant cause. Keeping the original imported weight view resolves the new candidate's static-rest comparison without a pixel allowance. Those earlier failed attempts and the original source-level algebra evidence remain distinct.

The supported authoring profile requires original float32 weights with at most four nonzero influences per selected vertex; splitting never exceeds eight slots or silently truncates. Shared guides across skins require compatible relative bind frames. Unsupported/ambiguous surfaces, imported physics joints, incompatible frames and budget excesses are refused. Shared outline surfaces merged with front hair need explicit masks/correspondence, not an automatic weld.

## Focused checks and pickup

`python tests/test_secondary_reconstruction.py` runs 15 generated-only preservation/admission tests, including original-reference inheritance and distinct skin joint sets. `python tests/test_reconstruction_wind_mapping.py` runs 16 generated-only wind-binding checks, including translation, parent, scale and inverse-bind tampering. `python tests/verify_reconstructed_rest_view.py` runs the 36 owned headless lifecycle/clone/proxy controls. Existing helper/batch/morph suites and the protected Miku 54-check contract passed separately on the earlier scoped source.

`python tests/verify_secondary_reconstruction.py` runs the generated-only checks. Optional `--source <read-only GLB> --region <node> <primitive> <component>` prepares a private candidate and checks actual imported weighted geometry headlessly. The protected Junko-only `--gui --gui-only` route requires the approved private Windows desktop and now passes its unchanged exact-image criterion on the new metadata-bearing candidate. No source assets, vertex arrays or screenshots are embedded in these tests or the scalar benchmark.

`python tests/verify_reconstructed_rest_movie.py --source <protected GLB>` runs
the optional 30-check portable/movie scope on Windows with the existing approved
private-desktop and encoder tools. It requires the pinned protected source; it
does not distribute or download that asset.

The standalone `tools/secondary_reconstruction.py` accepts a source, explicit recipe and **new** output folder. A recipe uses `studio_secondary_reconstruction_1`, a matching source checksum, `reviewed: true`, `segments` and a list of `{node, primitive, component}` regions; optional vertex masks and reviewed controls remain explicit. Multi-region recipes can share guides, but only the one-section native result above is qualified here. Next work: review the other colored back-hair groups, pair outline masks without crossing into bangs, and reduce the multi-chain contact cost.

See [the compact benchmark](benchmarks/secondary_reconstruction_20261121.json). The prior existing-chain 13/14 settling failure is retained and is not relabelled by this result.
