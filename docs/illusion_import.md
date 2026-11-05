# Illusion compatibility investigation

Status: **read-only character-card inventory implemented; direct character assembly
and map importing remain unsupported**. These formats will feed the same GLB /
studio_model_1 world contract as MMD, Source and common formats. No second pose engine.

The supplied Koikatsu PNG files contain a normal PNG preview followed by character
configuration and extension blocks. They require compatible installed game assets
and, where used, mods/plugins to reproduce the character. Embedded overlays are
not a substitute for resolving the full character. Re-encoding such a PNG as an
ordinary image can discard its appended data; Studio never rewrites the originals.

`python tools/illusion_cards.py <card.png> ...` checks PNG chunk bounds/CRCs, recognizes
KK/KKS/AI markers and reads only the bounded MessagePack block index. It reports family,
versions, block sizes and hashes. Character and plugin payloads remain opaque.
The tool does not import geometry, execute plugins, unpack game resources or claim
to resolve card dependencies. It deliberately omits AI card user/data identifiers.
Limits:64MiB card,64KiB index,128 blocks,4096 decoder nodes,12 nesting levels.
These checks are not a hostile-file security certification or full PNG decoder.

## Installed samples inspected

- All six supplied cards have readable appended indexes. Alice, hecatia3, Stubborn,
  Trendy and Marisa use the base Koikatsu marker. Keine uses the **Sunshine** marker;
  cross-version character assembly cannot be assumed merely from its folder location.
- Koikatsu has `abdata/map/scene/*.unity3d` maps, installed KKBP/PMX exporters and
  existing PMX exports. Most examined PMXs reference missing textures. Hecatia's
  `20260618131142_LapislazuliHecatia/modelBL.pmx` and `modelBL_org.pmx` have all listed
  texture files present. Actual modelBL conversion warned of an invalid mesh and
  timed out after180s during GLB export; it is not a successful import.
- AI Shoujo has Unity map bundles and mod APIs. `map_00_data.unity3d` is approximately
  1.02GB, exceeding the current GLB/input budget; selective dependency extraction is
  needed. A plugin called CharacterExport is not evidence of a usable mesh exporter.
- AA2MiniPPX has AAUnlimited, PP/PPX archives and XX-related tools. It needs a separate
  legacy adapter; the Koikatsu/AI Unity pipeline cannot be applied to it.

No game, installed plugin, archive script or external extraction executable was
launched. No game installation/configuration or supplied card was changed.

## Practical route and limits

First prove a complete existing PMX export through the installed MMD adapter, posing,
packed HAS and render path. Then investigate a narrow installed-game assembly/export
bridge for cards, preserving body parameters, bone edits and mod provenance. Unity
maps require a separate bounded resource adapter. AA2 needs XX/PP/PPX investigation.
Do not accept arbitrary PNGs in Add model until the route produces actual geometry.
Full native materials, morph controls, physics and card round-trip are not implemented.

Primary layout references (consulted2026-10-29; no code copied):
[KKManager card dispatch](https://github.com/IllusionMods/KKManager/blob/master/src/KKManager.Core/Data/Cards/CardLoader.cs),
[KK reader](https://github.com/IllusionMods/KKManager/blob/master/src/KKManager.Core/Data/Cards/KK/KoiCard.cs),
[KKS reader](https://github.com/IllusionMods/KKManager/blob/master/src/KKManager.Core/Data/Cards/KKS/KoiSunCard.cs),
[AI reader](https://github.com/IllusionMods/KKManager/blob/master/src/KKManager.Core/Data/Cards/AI/AiCard.cs),
[MessagePack specification](https://github.com/msgpack/msgpack/blob/master/spec.md).
Conversion research:
[KKBP workflow](https://kkbpwiki.github.io/),
[Illusion Modding API](https://github.com/IllusionMods/IllusionModdingAPI),
[AA2Unlimited](https://github.com/aa2g/AA2Unlimited),
[SB3Utility](https://github.com/enimaroah/SB3Utility).
The original linked KKBP GitHub repository/release returned404; no substitute downloaded.

Verification:9authored Python cases pass, including KK/KKS/AI layouts, ordinary PNG, CRC, bounds, duplicate/overlapping blocks, excessive nesting and unsupported opcodes. All6actual supplied cards validate with source SHA/mtime unchanged. Initial test miscounted an authored payload length; corrected to derive the expected length. AI uses an authored fixture here, not a tested real AI character.
