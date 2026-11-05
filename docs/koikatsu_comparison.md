# Misaki: two PMX routes from the same Koikatsu character

Read-only inspection2026-10-29, using the owner-provided `Kouhai.png` and:

- **A:** `C:/Games/Koikatsu/Export_PMX/20261029225144_OkutaMisaki`
- **B:** `C:/koikatsu_model/Okuta Misaki_4861`

The card has the base Koikatsu marker, not Sunshine. Its block index is readable:
Custom,Coordinate,Parameter,Status, with5trailing bytes reported rather than discarded.
The PMX files and card were checked for unchanged SHA256/modification time after reading.
No game, exporter, Blender or archive script was launched for this comparison.

| Root model.pmx | A: KKBP intermediate | B: conventional PMX export |
|---|---:|---:|
| Vertices | 30,550 | 40,852 |
| Triangles | 53,456 | 64,160 |
| Materials | 24 | 32 |
| Bones | 1,637 | 908 |
| Distinct bone names | 1,637 | 872 |
| Morph entries | 572 | 426 |
| Morph types | 572 vertex | 410vertex,7group,1bone,8UV |
| PMX texture entries | 0 | 29 |
| Missing listed texture files | 0, because none are listed | 1 |
| Rigid bodies / joints | 0 / 0 | 85 / 122 |
| Geometry height, source units | about1.50 | about18.98 |

The names overlap for805bones, but identical names are not proof of identical rest
transforms or skin bindings. B includes duplicate bone names; future conversion must
retain native indices/hierarchy instead of treating display names as unique identity.
A also has duplicate morph names:572entries but491distinct names. Source dimensions
are observations, not an automatically inferred scale policy.

A is an intermediate bundle, not an ordinary self-contained textured PMX. Exporter
configuration identifies version5.05, all variations/outfits and hitboxes enabled.
Seven `Outfit 00`–`06` PMXs contain additional geometry, also with no PMX texture
entries. Treating only its root PMX as the complete dressed character would lose data.
Companion files include283material records,1121texture records, blend-shape/bone-offset
data, dynamic bones/colliders and renderer information. `KK_CharacterInfoData.json`
contains52face-shape and44body-shape values and the character name OkutaMisaki.
The generic CustomFace/Body reports use `System.Single[]` placeholders for shape
arrays; the CharacterInfo arrays are the useful numeric source instead.

B's missing texture is `cf_m_eyeline_kage@330500.png`. Normal MMD preflight reports
that exact dependency and refuses conversion before creating the output bundle or
starting Blender. It does not guess a replacement. B's companion JSON includes a
trailing comma and fails strict JSON decoding; no executable interpretation or silent
repair was attempted. Its PMX still parses through the installed MMD reader.

The KKBP `card_data.png` has a misleading extension: its bytes begin with the native
product number/Koikatsu marker, not a PNG signature. It contains no embedded preview,
an81094byte native payload and an additional KKEx block. All matching block hashes
(Custom,Coordinate,Parameter,Status) differ from the original card. That proves they
are distinct serializations; it does not establish which settings changed or why.
A future adapter must identify data by structure/magic and keep original-card and
loaded/exported-state provenance separate. It must not try to decode this as an image.

## What this changes for HAS

Both rigs exceed the current512runtime-bone budget. Neither export has been certified
as a working HAS import. Raising the budget alone would not assemble A's outfits,
translate its materials, solve dynamic bones or repair B's missing dependency.

The correct destination remains one native HAS model contract. These findings call
for two input paths: ordinary PMX with complete dependencies, and a KKBP-aware bundle
adapter that assembles chosen outfit geometry plus companion material/parameter data.
That adapter must handle source units, stable bone/morph identities and truthful
physics/material loss reporting. No export-back subsystem or separate Koikatsu pose
engine is needed. Exact card-to-game assembly remains a later installed-game adapter.

Detailed private inventories are in ignored `output/misaki-comparison.json` and
`output/kouhai-card-inventory.json`. Geometry and complete skeleton/morph/physics
inventories were decoded using the existing installed MMD Tools4.5.11 pure PMX reader,
loaded directly without Blender. No reader code or owner assets were copied into Git.
The header/texture checks independently use Studio's original asset_audit.py.
This comparison is structural; matching pose/material rendering has not been proved.
