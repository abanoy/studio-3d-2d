# Next minimal representatives beyond Nitori and Keiki

This is read-only planning from the existing 82-file MDL49 header inventory.
No resource was extracted, staged or converted. `NEXT-REPRESENTATIVES.json`
binds the exact inventory and selected records. The hashes below are recorded
**full native MDL definition hashes**, not newly calculated header-prefix hashes.

| Archive | Exact member | Native MDL SHA256 |
| --- | --- | --- |
| Junko_Tamo_sfm_v25.zip | models/touhou/tamo/junko.mdl | `d916863f801d0894009fad43c587ae630bf05556f484ebae4803734bd15c8af7` |
| Junko_Tamo_sfm_v25.zip | models/touhou/tamo/junko hair.mdl | `8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716` |
| mima.rar | mima/models/koikatsu/touhou/mima head.mdl | `b0b128f994dd9939aa5e1978431fcc3afeec84d56ee1f14b0efec96999909224` |
| mima.rar | mima/models/koikatsu/touhou/mima body.mdl | `771c194ecf6da69210824d7a99afb9de110c68ccbc708e60b4ad6143ee400dda` |
| mima.rar | mima/models/koikatsu/touhou/mima dress.mdl | `0ff555f35633b4d9e25f77a07e3493a3c46e85ca3001e1350626f820a11331eb` |
| Kanako_Yasaka_DVebPRD.zip | models/touhou/tamo/kanako yasaka props.mdl | `ad9e57ed473eecd8df75068def4b74a51954b0b4617070c8b552b1a5a98d7759` |

| Representative | Small intended feature exercise | Outstanding independent oracle |
| --- | --- | --- |
| Junko v25 main + hair | Main: 145 bones, 16 distinct skin families. Hair: 69 bones, 49 native JIGGLE declarations and a Hat blank alternative. Begin with one skin remap and separate static hair adoption. | Exact material/dependency closure, native base geometry and skin remaps; then rest/inverse-bind/weighted alignment of the separate parts. Six common name/parent matches are a binding candidate, not automatic assembly proof. Native jiggle needs a later timed native/physics oracle. The hair hash is shared with the older archive; do not count it as a new definition. |
| Mima head/body/dress | Compound model candidate with different binding sets (229/175/169 bones). Head has 82 controllers / 156 descriptors, versus 143 prepared targets. Body has four skin families and three controllers; head has one skin family and hair/hat blank choices. Retain appearance/control distinctions beyond a facial-preset list. | Independently enumerate controller/rule/descriptor correspondence, including nonfacial/appearance effects; do not infer effects from labels or equate 82, 156 and 143. Existing report preserves exact names/spaces such as `remove eye highlight `. Then verify separate-part rest/binds/weights, native material variants, static assembly and authored pose propagation. No automatic bone merge or native-control equivalence is proved. |
| Kanako props, distinct archive/accessory case | Smaller independent accessory definition: 43 bones, four bodygroups, eight choices, four genuine zero-vertex blanks, one skin family and no flex controllers/descriptors. First enumerate exact group/choice names, then test one visible/blank pair with unchanged other components. | New exact resource closure and static native geometry/UV/VVD-weight/triangle correspondence, independent component presence and retained binding/scale. Its 20 procedural declarations are separate from static bodygroup coverage; no native jiggle result is implied. Group names/choice layout must be read before inventing selectors. |

All these headers report only one-frame reference/idle sequences. None supplies
a positive moving-native-sequence playback oracle. The first additions should
remain small, with separately reviewed resource allowlists. Native shader,
flex, jiggle, assembly, runtime variants and preview/movie behavior require
their own evidence; this matrix does not mark any of them implemented or tested.
