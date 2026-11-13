# Static SFM components: derived rendering and packed replay

The v3 probe at `4fa5efc175c0da53fcd61087e9685c89f4614db3` passes
**328 writer and 60 fresh-reader checks** on private Windows desktops.

It imports all twelve previously prepared Nitori/Keiki bundles, retaining every
primitive, exact material identity, decoded embedded image pixels and native
bone names. Eight raw captures cover three Nitori skin choices, Keiki Tools at
0/0.5/1, and named hand/box poses. All 24 primitive point-set comparisons match
the independent derived-GLB reference: maximum error is `6.004e-7` world units,
below the unchanged `2e-4` bound. Unaffected components retain their point hashes.

Two ordinary Add model cases exercise import Undo/Redo, a named numeric pose and
its Undo/Redo, unchanged roots, native parameter reports, bindings and pose keys.
They use the normal Studio light selector before the import baseline. The same
images contain 563 and 4,873 significant samples, exceeding the unchanged 100
sample threshold at RGB contrast above 0.02.

Both projects save through ordinary packed HAS. A second process with a separate
source copy, preferences and empty unpack cache opens them after only this run's
owned input folder is renamed offline. Writer and reader pixels match exactly;
project metadata, GLB bytes, bindings, keys and transforms remain intact. Root
also reread the two packed archives' CRCs and complete payload SHA256 inventories.

Both private jobs exit zero with confirmed child desktops, no observed foreground
child and closed jobs/desktops. All 59 protected prepared-bundle/runtime/candidate
records, 963 root functional records, both 1,780-file source copies, references
and owned input membership pass final preservation. These counts follow the probe's
documented membership policy, which differs from the default suite's 947-file map.

The earlier v2 failures remain failed. V3 retains every raw log and classifies
only the exact pinned Godot verbose packed-layout notice after independently
rechecking all twelve bounded layout proofs. Other warnings, errors, lookalikes
and changed/invalid layouts still fail. Its 57 CPU controls and independent
source review are saved with the source packet.

This establishes derived GLB and current app behavior. It does not establish
native Source shader, flex-controller, topology, normal, hardware-palette or
jiggle equivalence. The separate native-geometry oracle retains its partial
successes and unresolved cases. Nitori's three skin captures still look alike
behind the unchanged opaque glow layer; its missing native hair bump remains
reported. No native material was deleted to manufacture a color difference.

Normal app Tools shape controls, new movies, runtime appearance switching and
integration of the new static skin/bodygroup worker and chooser remain unrun or
unimplemented. The existing default Source import route remains available. This is not
a full default-suite pass or artist/device acceptance. The wider Junko, Mima,
Kanako and 82-MDL feature inventory remains separate.

Reviewed source is in `experiments/source_appearance/derived_probe_candidate_v3_20261113`;
compact actual evidence is in `experiments/source_appearance/derived_probe_actual_v3_20261113`.
Private GLBs, image captures, references and HAS packages remain local while
pending cases need them. See [actual evidence](benchmarks/sfm_derived_render_app_actual_2026-11-13.json).
