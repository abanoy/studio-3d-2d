# Native static-choice extension matrix — read-only plan, 2026-11-13

This plan extends the import-time skin/bodygroup proposal beyond Nitori and Keiki. It does not implement a chooser or run a model. Only existing published metadata, its checksum-verified detailed JSON, and current source were read; no archive/MDL/VVD/VTX, Steam content, converter, Blender or graphics process was opened. All paths below are relative to this checkout unless explicitly marked private/local.

The corpus remains **22 archives /82 MDL49 files /71 distinct MDL hashes**. Counts establish native declarations, not working native shaders, controls, assembly or jiggle. All82 inspected sequence animation headers have one frame; this corpus supplies no positive native moving-sequence test. [Native inventory](../../docs/benchmarks/sfm_native_feature_inventory_2026-11-12.json), [inventory scope](../../docs/sfm_native_feature_inventory_2026-11-12.md).

## Exact input identities

Archive identities are recorded November12 observations, not fresh availability checks. Reverify SHA/size/nsmtime before any future bounded staging. The MDL SHA below covers the **entire native definition used for header parsing**; no separate header-slice SHA or MDL/VVD/VTX checksum pairing is recorded for these cases. Calling it a header-only hash would be inaccurate.

| Archive | Recorded bytes | Archive SHA256 |
| --- | ---: | --- |
| `Junko_Tamo_sfm_v25.zip` | 15,534,049 | `bf1ee55e29ce089f44cc512ea5e8b5caa1b299010ff582019501598776872984` |
| `mima.rar` | 19,404,452 | `b0a4b19afc4cf8d8a17351848e11cf4738fa0a7436d58699a66a4c4be501a50a` |
| `Kanako_Yasaka_DVebPRD.zip` | 6,584,738 | `e228e1fef8300c7509f0b1eae7e3b551efc5e9bb37b2b8f26db49324a68b0705` |

| Case | Exact archive member | MDL bytes | Native definition SHA256 |
| --- | --- | ---: | --- |
| J1 | `Junko_Tamo_sfm_v25.zip` → `models/touhou/tamo/junko.mdl` | 1,290,252 | `d916863f801d0894009fad43c587ae630bf05556f484ebae4803734bd15c8af7` |
| J2 | `Junko_Tamo_sfm_v25.zip` → `models/touhou/tamo/junko hair.mdl` | 37,644 | `8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716` |
| M1 | `mima.rar` → `mima/models/koikatsu/touhou/mima head.mdl` | 1,615,552 | `b0b128f994dd9939aa5e1978431fcc3afeec84d56ee1f14b0efec96999909224` |
| M2 | `mima.rar` → `mima/models/koikatsu/touhou/mima body.mdl` | 88,780 | `771c194ecf6da69210824d7a99afb9de110c68ccbc708e60b4ad6143ee400dda` |
| M3 | `mima.rar` → `mima/models/koikatsu/touhou/mima dress.mdl` | 72,972 | `0ff555f35633b4d9e25f77a07e3493a3c46e85ca3001e1350626f820a11331eb` |
| K1 | `Kanako_Yasaka_DVebPRD.zip` → `models/touhou/tamo/kanako yasaka props.mdl` | 22,828 | `ad9e57ed473eecd8df75068def4b74a51954b0b4617070c8b552b1a5a98d7759` |

Archive pins come from the [identity inventory](../../docs/benchmarks/sfm_extra_feature_inventory_2026-11-12.json), definition pins/counts from the [82-file inventory](../../docs/benchmarks/sfm_native_feature_inventory_2026-11-12.json). Exact choice names/vertex counts below additionally use the existing **private metadata JSON only**, [metadata-v2.json](../sfm-extra-native-inventory/1794519206301446900/metadata-v2.json), 4,184,410B, SHA256 `0cdec3ae27e19f662f3a79a2a85de49ed701b6d96bc656c69cd7307bf6ca1e14`; that hash matches the published inventory's `evidence` record. No new native parsing occurred.

## Observed features and smallest next cases

`Groups/choices/blanks` are native bodypart/model totals; `C/R/D` means controller/rule/flex-descriptor counts. Raw skin rows and distinct remaps are shown separately.

| Case | Bones | Skin rows/distinct | Groups/choices/zero-geometry blanks | C/R/D | JIGGLE declarations | Bounded next static test |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| J1 | 145 | 16/16 | 2/3/1 | 116/116/116 | 2 | Skin0 versus highest eligible native skin15; Belt group1:0→1 while base stays visible. Skin16 must refuse. |
| J2 | 69 | 1/1 | 2/3/1 | 0/0/0 | 49 | Hat group1:0→1; retain hair group0:0. Import separately, without auto-assembly or native-jiggle promises. |
| M1 | 229 | 1/1 | 3/5/2 | 82/82/156 | 0 | Hair group1 and hat group2: visible0/blank1 independently; retain face group0:0 and actual target identities. |
| M2 | 175 | 4/4 | 4/9/2 | 3/3/3 | 2 | Skin0 versus eligible3; Socks group2:0→1; swimsuit group3 offers four visible variants0–3 and blank4. |
| M3 | 169 | 1/1 | 4/8/4 | 0/0/0 | 2 | One visible/blank clothing pair, then explicit all-blank refusal; no body/head merge. |
| K1 | 43 | 1/1 | 4/8/4 | 0/0/0 | 20 | All0 baseline, Bat L group0:0→1, then all1 empty refusal; retain other components unchanged. |

The exact static choices make the next matrix concrete:

- **Junko v25 J1:** group0 `reference`, choice0 `Base dmx.dmx` =18,232 native vertices; group1 `Belt`, choice0 `Belt.dmx` =297, choice1 =0. **J2:** group0 `reference`/`hair.smd` =8,011; group1 `Hat`/`Hat.smd` =1,650 or zero. There are16 distinct main skin rows, but that alone does not prove every nonzero row satisfies the prototype's native material-column guard. The older `Junko_Tamo_sfm.zip` main has8 skins and a different MDL SHA (`10dab6acf864678e8b500ea59494511bcc9518a7a3f174dc7c62a9f3302b3c03`); its archive SHA is `e7579f0e9b89b6f49047533ead2b17c6c56393f692f99fb17d4ac9612ef89fe6`. The hair definition is byte-identical across the two archives, so do not count it as a new definition or infer identical textures from the MDL hash alone.
- **Mima M1:** group0 `Mima_dmx`/`Mima_dmx.dmx` =5,197; hair =20,538 or zero; hat =1,166 or zero. The existing prepared head has143 targets on the face mesh, versus82 native controllers/82 rules/156 descriptors. Preserve these three counts and exact strings independently. Native controller0 is `"remove eye highlight "` (trailing space), controller18 is `" blink"` (leading space); controller2 `"Eyebrows angry"` drives descriptor40 via `FETCH1(2)`. These are real identity/mapping records, not proof that a same-named GLB target or material effect is equivalent. M2 has three nonfacial native controllers/rules, each0..1 with single FETCH1; their effects are outside the static chooser. [Current Mima metadata and limits](../../docs/benchmarks/sfm_extra_feature_inventory_2026-11-12.json).
- **Mima M2/M3:** body groups0/1 are fixed visible records; group2 `Socks` is2,896 vertices or zero; group3 `swimsuit` has visible choices2,787/1,784/2,779/1,776 and zero. Dress groups0–3 are `shoes`1,714, `skirt`4,230, `sleeves`1,486, `top`5,075, each visible0/zero1. Head/body/dress have different binding sets229/175/169; keep them separate until rest/inverse-bind/weighted alignment and authored pose propagation are independently established. “Compound” here is a component-assembly case, not evidence of compound native flex opcodes: the82-file inventory found only single FETCH1 rules.
- **Kanako K1:** exact indices are0 `Bat L`/`Bat L.dmx`203 vertices (1 mesh record);1 `Bat R`203 (1);2 `Pillars`3,632 (3);3 `Rope`1,738 (2). Every group has choice0 visible and choice1 genuine zero-vertex `blank`. This justifies four binary selectors from actual metadata, not from the aggregate8-choice count. The historical default conversion reports4 mesh objects; that is not the same unit as7 native mesh records across these choices. Its20 parsed procedural declarations are JIGGLE/type5, separate from these static alternatives.

The existing [next-representatives packet](../../experiments/source_appearance/native_geometry_oracle_20261113/next-representatives.json) preserves the same six identities and outstanding oracles. Junko main/hair share only six recorded name/parent matches; that is insufficient for bone merge. These models' complete resource closures and native geometry/control/jiggle oracles have not been newly established by this plan.

## What can be reused, and what is still unshipped

The [actual14-case worker record](../../experiments/source_appearance/actual_windows_20261113/metadata/actual_results.json), SHA256 `8bfa2071c9cc6846c9972d53ce93ce433fd8b46293b9155409fcef00f8f97478`, records12 successful bundles plus2 exact all-blank refusals at `2904f3f18e4211f95ddd385953219b2e5460aee9`. It covers Nitori skins0/1/2 and Keiki's seven visible tools/box/flame combinations, exact selected indices/catalogues, retained structural fingerprints and owned dependencies. Nitori's skin0/default bundle SHA is `2c0036cf3986ce3e8d53b665108c482d1afa7862cbc14989c4f2f9eb15dc1c11`; Keiki default/000 is `a279706ff438d8481a66c8e75770622c5456d50e137800b93fadd9ad0dd52403`.

Later [derived rendering/app evidence](../../docs/benchmarks/sfm_derived_render_app_actual_2026-11-13.json) passed388 checks at `4fa5efc175c0da53fcd61087e9685c89f4614db3`, including same prepared-GLB pose/Tools deformation, normal Add/Undo/Redo, packed HAS and exact fresh-reader pixels. It did **not** implement native import-choice UI or prove native Source shaders/flex. Keep this later pass separate from older documents saying GPU/app work was then unrun.

The [independent native base-geometry oracle](../../docs/benchmarks/sfm_native_geometry_oracle_2026-11-13.json) is partial:7/12 complete base maps,3/12 supported whole triangle matches; Nitori's legacy VTX topology remains unrun and five Tools cases retain unresolved seam correspondences. It does not certify new Junko/Mima/Kanako data. Nitori's missing `hairbump.vtf`, ordinary-PBR treatment of native additive glow, and opaque grey “black” overlay remain explicit. A static skin dropdown cannot close shader or native-delta fidelity gaps.

Current main [source_import.gd](../../src/source_import.gd) exposes archive-member selection in `start()` and launches `prepare_source.py` from `launch()`; it has no skin/bodygroup selector. Main [prepare_source.py](../../tools/prepare_source.py) has member `--catalog` but no `--appearance`; main [blender_source_bridge.py](../../tools/blender_source_bridge.py) `load_model()` selects skin0 and the first bodygroup variants and reports those defaults. This inspection does not change main.

The reviewed [appearance request module](../../experiments/source_appearance/overlay/tools/source_appearance.py) already provides `validate/load/bind/catalogue/choose/apply`, and the [worker overlay](../../experiments/source_appearance/overlay/tools/prepare_source.py) adds `--appearance`. Requests bind original-input SHA **and** selected native MDL SHA, strict integer skin/bodygroup indices and canonical numeric group keys. `choose()` checks actual converted-object/native-choice correspondence, default material-slot identity and ambiguous remaps; all-empty geometry refuses. These are a bounded port basis, not a production-selector claim.

## Bounded main extension seams

1. Add a small native metadata catalogue after choosing one MDL member. Keep the existing archive `--catalog` contract unchanged; it currently lists members, not appearance choices. The new response must bind archive SHA/member/MDL SHA and actual native group/choice indices, raw/distinct skin counts, zero-vertex flags and diagnostic eligibility. Read only the selected definition into a fresh owned scope with existing approved tooling. On member/input changes invalidate the catalogue/selection token; never reuse choices by filename or bone name.
2. Add skin/bodygroup controls to the existing Source import dialog. Display native indices alongside exact names; label genuine blanks from vertex counts. Single-choice groups can stay fixed. Retain default0 when no appearance was requested; a rejected requested choice must report its reason rather than silently importing a default. Distinguish `skin0` from “no override” in provenance. Junko's16 skins fit the existing256 bound; preserve repeated/nonidentity material-column refusals until an explicit native mesh-column join is implemented.
3. Carry a checksum-bound request through `source_import.launch` → main `prepare_source.py --appearance` → bridge `load_model(..., appearance=...)`, with catalogue/selected-native-indices returned in parameters. Begin with MDL models only; preserve BSP/default and other import paths. Retain cancellation, original-file identity and owned dependency closure. Do not reconvert an already edited object or change existing mesh/shape/helper identities; use ordinary new-object adoption after a successful preparation.
4. Port and verify Nitori/Keiki first, using the existing14 worker cases and388 derived-app predicates as separate baselines. Then extend one bounded worker/adoption matrix per row above: Junko highest eligible skin+one belt/hat blank; Mima head hair/hat and body skin/Socks; Kanako Bat L blank plus all-empty refusal. Resolve each selected skin's actual VMT/VTF/include closure, preserve active/inactive missing-resource diagnostics, and reject mismatched MDL/VVD/VTX identities. Original archives were not reverified here; no new extraction is authorized by this plan.
5. For each new static bundle verify actual native selected indices, mesh/material membership, unchanged remaining bones/rest/binds/weights/morph provenance and exact packed payload. Test normal import Undo/Redo, saved selected provenance, fresh source-offline reopen and positive same-frame pixels. Per-MDL resource/material/native-geometry oracles stay explicit; a matching prepared-GLB reference alone proves only derived rendering/adoption.

Existing [base-shape editing](../../src/base_shape_editor.gd), [shape catalogue](../../src/shape_catalog.gd), [expression editing](../../src/expression_pose_editor.gd) and [shape animation](../../src/shape_animation.gd) operate on prepared GLB targets; preserve them. Native controller/rule evaluation (including Mima's appearance/nonfacial controls), runtime/animated skin-bodygroup switching, Source shader/proxy behavior, native JIGGLE parameters/solver equivalence, compound-character assembly and bone merge remain separate features. A HAS-authored loose-chain wind preview is not a native Source JIGGLE oracle.

## Evidence boundaries to retain

No separate header-slice SHA, source checksum pairing, new sidecar/material closure, native rest/bind alignment, controller-delta oracle or native jiggle render was created for these six candidates. Full MDL hashes and parsed header counts are the current pins. Keep exact names/spaces/case, actual blank geometry and archive versions; do not infer controller semantics from labels, distinct appearances from row count, new definitions from duplicate hashes, or whole-character scale from an isolated accessory. This plan is data-grounded staging for later work, with all conversion/render/app/native-fidelity execution for these added cases **unrun here**.
