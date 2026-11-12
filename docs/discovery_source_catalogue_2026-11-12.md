# Discovery source catalogue — initial research

**November 12, 2026.** There are **12 researched directory entries plus one
requested, unverified SFMLab link**. They are not 12 working search adapters.
Some evidence is indexed official content, an older schema or a JavaScript shell.
No models, artwork or thumbnails were downloaded; no accounts, credentials,
subscriptions, provider code, app launches or endpoint tests were used.

The [machine-readable catalogue](../data/discovery_sources.json) holds stable
IDs/families, languages/categories,
observed URLs, API/auth states, metadata statuses, brief caveats and primary
evidence URLs. `documented_api` means documentation exists, not a functioning
HAS adapter. `public_search` means a public search entry/UI was observed, not
that a permitted aggregation method or exact query template is established.
Missing home/search fields were not independently established. This catalogue
records research only; provider integration remains unimplemented.

## Directory entries

| Source | Evidenced language/type | Observed entry and important boundary |
| --- | --- | --- |
| BowlRoll | Japanese; MMD/PMX, stages/motions | [Keyword page](https://bowlroll.net/file/keyword/MMD%E3%83%A2%E3%83%87%E3%83%AB). Direct response partial; official indexed results richer. Sample file metadata is not verified retrieval; API unknown. |
| Steam Workshop | Multilingual UI; GMod/SFM assets | [GMod](https://steamcommunity.com/app/4000/workshop/), [SFM](https://steamcommunity.com/app/1840/workshop/). Separate app catalogues include non-model addons. Official API needs a key; access prerequisites vary by app/item. |
| BOOTH | Japanese/English; characters, props, VRoid/general 3D | [Models](https://booth.pm/en/browse/3D%20Models). Category may include digital or physical goods. Keyword template/API/retrieval rules unverified; a proposed VRM request timed out. |
| VRoid Hub | English/Japanese; VRM avatars | [Catalogue](https://hub.vroid.com/en). Public visibility does not establish download permission. API requires registered app credentials and OAuth; none configured. |
| 模之屋/Aplaybox | Chinese; model/motion sharing and MMD | [Homepage](https://www.aplaybox.com/), [About](https://www.aplaybox.com/aboutUs). JS shell; About direct timeout. Indexed official text distinguishes protected preview-only content. Search/API/access unknown. |
| Sketchfab | English/global general 3D | [Search](https://sketchfab.com/search?type=models). Official indexed search and older schema available; direct pages returned 403. Documented downloadable/viewer fields require current validation. |
| Poly Haven | English; props/environments/general 3D | [Models](https://polyhaven.com/models). Official API documents source metadata and thumbnails; strongest first metadata-interface candidate. No endpoint or asset retrieval performed. |
| CGTrader | English plus listed European/Japanese/Chinese locales; general 3D | [Catalogue](https://www.cgtrader.com/3d-models). Public search/categories observed. API/query/auth and individual-preview fields unverified; free/paid labels are not retrieval proof. |
| TurboSquid | English; general 3D/exchange formats | [Catalogue](https://www.turbosquid.com/Search/3D-Models), [glTF filter](https://www.turbosquid.com/Search/3D-Models/gltf). Formats/price/rigging/animation filters observed. API and actual file access unknown. |
| BlendSwap | English; Blender and some exchange formats | [Models](https://blendswap.com/3d). Cards expose creator/formats/license. Officially advertised MCP/API page returned 403; schema/auth unknown. No MCP connection or downloads. |
| Kenney | English; game-ready 3D packs | [3D category](https://kenney.nl/assets/category:3D). Search and pack listings observed. A pack is not one known-compatible model; API/query template unverified. |
| 3ddd/3dsky | Russian/English; architecture/general props | [Russian models](https://3ddd.ru/3dmodels), [English site](https://3dsky.org/). Group as one family for diversity, without an ownership audit. Free/PRO/format fields observed; API/access unknown. |
| SFMLab — requested/unverified | Owner-requested source; catalogue not inspected | [Homepage](https://sfmlab.com/). Anubis challenge; no bypass. Search/API/language/type/access metadata unknown, not an empty-catalogue finding. |

## Documented interfaces and first-adapter proposals

1. **Poly Haven metadata first.** Its [official API page](https://polyhaven.com/our-api)
   states default endpoints require no key/login and documents names, tags, types,
   thumbnail URLs, authors/dates and file metadata. Unique application User-Agent
   and source attribution are required. The Models page explicitly links
   [`/assets?type=models`](https://api.polyhaven.com/assets?type=models); that
   endpoint was not called. Read current API terms before integration; website
   scraping permission is not implied by its [asset license](https://polyhaven.com/license).
2. **Useful external links before promising aggregation.** Other entries can
   appear in the source catalogue with clear capability states. Establish current
   search methods and permission before claiming working adapters. Do not bypass
   challenge/unavailable states.
3. **Credential-dependent interfaces stay separate.** Steam's
   [QueryFiles docs](https://partner.steamgames.com/doc/webapi/IPublishedFileService)
   specify key authentication, search text/language, pagination and previews.
   [VRoid API docs](https://developer.vroid.com/en/api/) require developer/app
   registration and OAuth. No key, secret or account flow is bundled by this draft.
4. **Verify advertised or older interfaces next.** Sketchfab's
   [official schema](https://docs.sketchfab.com/data-api/v3/index.html) documents
   downloadable/thumbnails/viewer fields but current access failed. BlendSwap
   links an [MCP/API page](https://blendswap.com/3d-mcp-api) that returned 403.
   Neither is a tested current integration. BowlRoll/BOOTH API support remains unknown.

## Browser interpretation and limits

- Downloadable, Preview and Password may overlap. Offered-file metadata does not
  establish actual retrieval, credentials, local compatibility or import readiness.
- A thumbnail is not a 3D preview. A protected hosted preview is not a downloadable
  model or permission to reproduce it. Password status remains unknown unless
  explicit listing evidence establishes it.
- Failed/blocked/missing metadata stays **Unknown**. Preserve its reason rather
  than inventing preview-only or no-download classifications.
- Catalogue families/source IDs and canonical URLs matter for deduplication.
  Similar titles or translated aliases alone do not establish identical models.
- Website retrieval prerequisites must not prohibit already-local, complete
  native files. Keep offline Local Discovery independent of online services.
- No automatic asset downloads/subscriptions/accounts follow from this research.
  Every current API/access/terms assumption needs validation before implementation.

This checkpoint saves research data and documentation only. It does not add
provider network code, credentials, downloads, UI or a working app adapter.
