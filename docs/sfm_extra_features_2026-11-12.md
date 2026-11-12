# Supplied SFM extra-feature review — November 12, 2026

This is a read-only inventory and test-gap review, not a new application pass.
No model was extracted, converted, launched, downloaded or uploaded. No supplied
script was executed. Original archives were read only for identity checks.

The later same-day [native metadata follow-up](sfm_native_feature_inventory_2026-11-12.md)
now resolves the initial unknown skin/procedural/sequence counts across all 82
definitions. It confirms 28 files with differing skins and 55 with native JIGGLE
declarations; all animation headers are one frame. The initial pass below remains
scoped to existing evidence. Neither pass certifies native feature behavior.

## What the existing evidence actually covers

- The November 8 receipt records **22 supplied archives, 82 MDL files and 82
  successful default conversions**, followed by normal Add-model/bone-provenance
  and captured-image checks. The 82 recorded MDL hashes represent **71 distinct
  definitions**. This does not prove every extra feature is editable or faithful.
- The earlier November 1 research covered **20 archives / 66 definitions / 59
  distinct hashes**. Its totals of 2,332 controllers, 3,031 descriptors, 247
  bodygroups and 421 bodygroup choices belong to that earlier subset. They must
  not be relabelled as a fresh inventory of all 82 files.
- Nine selected MDL/VVD files have historical raw positional-delta probes. These
  cover Mima head, Momiji head, Reimu V2, Junko skirt, Keiki main/props/chisels and
  Shinki head/wings. This is target-delta evidence, not arbitrary native-rule,
  shader, full-character assembly or live simulation acceptance.
- Nine complete native characters have separately scoped pose/contact/freeze
  evidence. Ran, Reimu V2 and Chen also have explicit cold packed-HAS tests; Ran
  has a normal movie check. These historical Linux checks are not new Windows
  results from this review.
- Current Windows evidence includes the restored Mima head and its shape
  catalogue case. Historical comparison/study evidence also uses Mima, beyond Scout.

## Concrete features and remaining tests

| Feature | Evidence beyond Scout | What remains to prove |
| --- | --- | --- |
| Facial controls and native identities | Mima head: 82 controller names, 156 descriptors and 143 prepared facial targets. Three isolated controls were traced through native MDL/VVD rules/deltas: `Eyebrows raise`, ` blink` and `mouth angry open`. Existing app/HAS/movie and later catalogue evidence is separate from those native comparisons. | Expand independent controls and combinations; preserve leading/trailing spaces and left/right identity. Do not equate controller, descriptor and GLB-target counts. |
| Nonfacial positional controls | The nine-file raw pilot reports Keiki's `Tools` control moving tool vertices, and distinct hair/wing affected regions. | A Keiki tool or Shinki wing control needs a named native-to-GLB comparison plus actual editor/Undo/HAS/export checks. Positional deltas alone do not establish intended semantics or rule combinations. |
| Bodygroups and blank alternatives | The retained Mima native report has `hair: [hair.smd, null]` and `hat: [hat.smd, null]`, plus the facial bodygroup. Default choices are zero. Earlier corpus research counted multiple bodygroup choices. | Actual in-app choice switching, blank selection, persistence, Undo and preview/export agreement. The production bridge currently exports default choices; imported variants remain in the Blender intermediate. |
| Skins and material families | Mima has **one** recorded skin family. The adapter retains a `skin_groups` report and selects skin zero. | Identify a genuinely multi-skin sample first. No positive alternative-skin example is established by this review; multiple VMTs/textures or differently named model versions do not prove selectable skins. |
| Separate accessories and component models | Keiki main/props/chisels; Shinki body/hair/skirt/wings; Junko main/hair/dress/skirts/character mask; Hijiri hair/rosary/clothing; Kanako skirt/props; Cirno props; Takane's box and Nitori glove are recorded native members/conversions. | Native bone binding/assembly, local selection, placement, save/reopen and independent motion. An ordinary object parent is not Source bone merge. Do not size an isolated component as a complete person. |
| Additional joints and hair chains | Conversion receipts retain 3–234 bones depending on the component. Mima head specifically retains 229 bones, including explicit `Hair_R` / `_yure_hair_*` parent chains. | Weighted joint movement, selected/excluded regions, live Hair & clothes, off/reset restoration and saved replay on representative supplied models. Native bone presence/names do not establish a native jiggle or cloth solver. |
| Material differences and missing resources | Momoyo has a recorded missing `Baby` material; Nitori variants have a recorded missing texture dependency. The older standalone audit reports 38 unresolved texture references and four recoverable VMT brace diagnostics. | Accurate missing-resource reporting and user-chosen dependency resolution; material variants must be inspected rather than inferred. Existing PBR conversion is approximate; native proxies/shaders remain outside equivalence claims. |
| Native animations, sequences, pose parameters and procedural rules | The bridge explicitly disables native animation import and documents no native sequence/physics/IK playback. Per-model sequence/procedural counts are not retained in the reviewed compact receipts. | Inventory actual records with the pinned native reader before selecting a positive test. Do not claim these features exist on a particular supplied model from its filename, number of bones or a `no jig` label. |

## Recommended next tests

1. **Use the already staged Mima head first.** Add native comparisons for
   `remove eye highlight ` and distinct left/right controls, checking exact native
   names, affected vertices, isolated versus combined amounts and current
   editor/Undo/packed-HAS/movie behavior. Reuse its immutable MDL/VVD and prepared
   GLB; no new extraction is needed. Its bodygroups also give a concrete future
   hair/hat blank-choice case, once choice switching is implemented.
2. **Recreate a bounded metadata manifest for the broader corpus**, using bounded metadata-only staging. For each distinct MDL hash, record bodygroup choices,
   actual skin-family count, controller/rule identities, attachments, extra joint
   parents, native sequences/include dependencies and procedural rule types.
   Preserve related versions/duplicates as families. Native input extraction is
   outside this review; existing approved tooling can be reused later.
3. **Choose one nonfacial control and one assembly case** from that manifest:
   Keiki Tools/props/chisels and Shinki wings or Junko hair/clothing are grounded
   candidates. Separate raw-delta correctness, native bone binding, live helper
   behavior and normal editor/HAS/export tests. Do not silently auto-assemble.
4. **Choose a verified multi-skin/bodygroup sample and a missing-resource case.**
   Mima already proves bodygroup alternatives but cannot prove multiple skins;
   Momoyo/Nitori supply explicit dependency diagnostics. Keep unsupported choices
   visible and diagnosed rather than treating a default render as full support.

## Local availability and preservation

All 22 exact archive names from the supplied list are present under
`C:\a\dump\New folder`. Their fresh SHA-256/size checks match the November 7
archive provenance record. The originally mentioned Downloads copies are absent.
`C:\a\tools\models` contains no MDLs. Only the existing Mima head staging was
inspected; no broader archive extraction occurred. Original hashes and file
modification stamps were checked before/after this review.

[The recorded inventory](benchmarks/sfm_extra_feature_inventory_2026-11-12.json)
contains exact local identities, compact historical conversion entries, local
Mima metadata, evidence hashes and explicit scope boundaries. The portable
[audit tool](../tools/audit_supplied_sfm_features.py) accepts an explicit archive
root and new output file, plus an optional retained Mima report. It reads metadata
without launching applications, parsing model scripts, extracting archives or
accessing the network. It refuses changed archive identities and existing output.

```powershell
python tools/audit_supplied_sfm_features.py --archive-root "C:/a/dump/New folder" --output output/sfm-identity-audit.json --mima-report output/sfm-face-pilot.json
```

Omit `--mima-report` when that private fixture has not been recreated. The
committed inventory records the original November 12 review; a later tool run
produces a separate identity audit rather than replacing that historical receipt.

Primary local evidence:

- [82-model conversion receipt](benchmarks/supplied_source_corpus_2026-11-08.json)
- [archive/metadata provenance](benchmarks/sfm_uploaded_samples_2026-11-07.json)
- [standalone sample checks](benchmarks/standalone_source_samples_2026-11-07.json)
- [native pose/contact checks](benchmarks/native_diversity_contact_2026-11-08.json)
- [earlier sample research](sfm_sample_corpus.md), [uploaded sample notes](sfm_uploaded_samples.md)
- [shape study](shape_study.md), [shape comparison](shape_comparison.md)
- [Mima fixture restoration](benchmarks/mima_fixture_restore_2026-11-11.json)
- `output/sfm-face-pilot.json` and its current prepared Mima bundle
- [Source bridge](../tools/blender_source_bridge.py) (actual default/disabled import behavior)
