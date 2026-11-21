# Discovery providers — researched November 21, 2026

This extends the November 12 research catalogue without rewriting its historical
claims. Current code is in `src/discovery`; these notes separate a documented
interface from an actual successful live app retrieval. The original research
and metadata verification downloaded no models or thumbnails. The continuing
optional-preview probe later loaded one public CDN thumbnail into memory after
explicit opt-in; no model files or thumbnail artifacts were stored in Git.

| Directory | Language / scope | Actual search or API method | First-version boundary |
| --- | --- | --- | --- |
| Poly Haven | English/global props and environments | GET `https://api.polyhaven.com/assets?type=models`; dictionary keyed by asset ID, type 2, name/tags/thumbnail_url. Match query variants locally, paginate cached records in the client. | Public metadata API adapter. Actual browser metadata retrieval passed with host network access; earlier restricted-shell DNS failed. API listing alone does not prove a specific format or current file retrieval. |
| Sketchfab | English/global, original-language titles | GET `https://api.sketchfab.com/v3/search?type=models&count=24&q=...`; public search, space-separated keywords; follow returned same-endpoint next cursor. Separate queries, not all aliases in a single AND query. | Public metadata API adapter, no token. Official docs cap count at 24 and warn about 429. Actual browser retrieval, cursor paging and English/Japanese searches passed with host network access. |
| BowlRoll | Japanese; MMD ecosystem including models, motions and other files | Published feed `https://bowlroll.net/file/tag/MikuMikuDance.rss`; website keyword search `https://bowlroll.net/file/keyword/<encoded keyword>`. The administrator describes keyword search over title, description and filename, distinct from tags. | RSS adapter only; title filtering over recent entries. No invented feed pagination or keyword-feed API. Do not infer MMD model format merely from feed membership. Live endpoint returned HTML rather than RSS; reported unavailable with website fallback. No HTML scraping was added. |
| Steam Workshop SFM | Multilingual; app 1840, includes non-model content | Website `https://steamcommunity.com/workshop/browse/?appid=1840&searchtext=...`. Documented IPublishedFileService/QueryFiles uses key, appid, search_text, language, cursor/next_cursor. | Website only. No bundled key/server, HTML scraping, account access or subscription calls. Retrieval conditions vary; no universal GMod/SFM ownership claim. |
| Steam Workshop GMod | Multilingual; app 4000, includes non-model content | Same website/API methods with appid 4000. | Separate website filter; not an item-format inference. |
| SFMLab | English, SFM/general community uploads | Source homepage/search UI. Published Terms discuss an API but do not establish a public catalogue-search contract. Search query template was not verified. | Website only, opens home so the user can use its search. Terms prohibit automated scraping without explicit permission. Anubis was observed in the earlier catalogue and confirmed in the site's own description; no challenge bypass attempted. |
| BOOTH | Japanese/English; 3D models and goods | Website `https://booth.pm/en/search/<encoded keyword>`. Current VRM search page independently observed, with categories/tags and paid listings. | Website only. No verified catalogue API or scraping permission. VRM search results may include accessories or software rather than downloadable VRM files. |
| VRoid Hub | Japanese/English; VRM characters | Website search UI at `https://hub.vroid.com/en/`. Official API requires developer registration, ClientID/ClientSecret and OAuth 2.0. | Website only, opens home; no invented query template, credentials or authorization flow. Public viewability does not establish download permission. |

## Primary references and observations

- Poly Haven [API overview and conditions](https://polyhaven.com/our-api): default
  endpoints need no key; unique application User-Agent and clear source attribution
  are required. The browser supplies its project/version User-Agent and source
  column. The [current model metadata endpoint](https://api.polyhaven.com/assets?type=models)
  returned type/name/tags/thumbnail metadata during independent research.
- Sketchfab [Data API introduction](https://sketchfab.com/developers/data-api/v3)
  and [official schema](https://docs.sketchfab.com/data-api/v3/index.html): public
  versus authenticated operations, search, cursor pagination, 24-item maximum,
  viewerUrl/isDownloadable, password-protected model handling and throttling.
  `isProtected=true`, if actually present, is the only Password badge evidence
  this adapter accepts. Missing fields stay Unknown; no download/password API is
  called. The developer-guidelines page returned 403 during this session.
- BowlRoll administrator's [version/search/feed explanation](https://bowlroll.blog.jp/archives/10398497.html)
  (July 28, 2014): published RSS tag URL and keyword/tag distinction. This is
  historical documentation, not proof the feed still responds. The site can
  have referrer, expiry, password and other restrictions; no protections are
  inferred to be absent and none are bypassed.
- Valve's [IPublishedFileService documentation](https://partner.steamgames.com/doc/webapi/IPublishedFileService)
  explicitly marks QueryFiles key authentication and documents app IDs, text,
  language, cursors and optional preview metadata. The browser never presents
  Workshop subscription or app ownership as item-level evidence.
- SFMLab [Terms of Service](https://sfmlab.com/about/tos/), updated October 26,
  2026, restrict automated scraping unless explicitly permitted; and the site's
  [account of its Anubis protection](https://sfmlab.com/news/the-roblox-scraper-technical-details/).
  No public search schema was established. Browser-only is deliberate.
- BOOTH [actual VRM keyword page](https://booth.pm/en/search/VRM), successfully
  read during research. A listing's price/category is not a download permission.
- VRoid [official API outline](https://developer.vroid.com/en/api/) requires
  registered application credentials and OAuth, and distinguishes listing data
  from issuing a model-file URL. The public [Hub](https://hub.vroid.com/en/)
  exposes its own search UI. Neither API nor source files are requested here.

## Bundled alias evidence

The small explicit dictionary links `Hatsune Miku`, `Miku Hatsune`, `初音ミク`
and `初音未来`. Crypton's [English character page](https://piapro.net/intl/en_character.html)
names Hatsune Miku; the [Japanese character page](https://piapro.net/pages/character/)
names 初音ミク; its [Simplified Chinese anniversary page](https://piapro.net/miku20th/index_zh-hans.html)
uses 初音未来. Reordering the English words is a deterministic search variation,
not a separate official character name. Capitalization/ASCII width/spacing are
local query variants, not claims about a provider's collation rules. No universal
translation, transliteration or language coverage is promised.

## Follow-up live observations

Host-network runs on November 21 retrieved real Poly Haven and Sketchfab listings
through the production browser, including 100 + 100 mixed discovery and original
Japanese search results. The earlier app DNS failures described above belong to
the restricted-shell attempt, not the final host-network result. No credentials
or authentication workaround was needed for these two public metadata APIs.

The documented BowlRoll RSS URL returned HTTP 200 **HTML**, with the normal
MikuMikuDance tag-page title and canonical URL. This is not usable RSS and is
reported as a provider limitation, without parsing the HTML into assets or
claiming that it is an anti-bot challenge. Website search remains available.
The RSS documentation is historical evidence, not a current availability claim.

SFMLab's current [Terms](https://sfmlab.com/about/tos/) still prohibit scraping
without explicit permission. Steam's documented QueryFiles still requires a key;
VRoid's official API outline still requires registration and OAuth. Those sources
remain website-only. No additional account API, scraped catalogue or invented
search template was introduced in this follow-up.

## Request policy

Only fixed public metadata endpoints and validated same-endpoint Sketchfab
cursors can be fetched. There are no cookies, accounts, download links, referrer
spoofing, anti-bot workarounds or automatic retries. The six-request batch budget,
600 ms minimum interval, 12-second timeout and 4 MiB cap are conservative client
limits, not claimed published provider quotas. Respect 429 with a persisted
in-session cooldown and numeric Retry-After; without the header use 60 seconds.
Unrecognized/date-form hints pause that provider for the session rather than
guessing a shorter delay. Provider failures remain visible alongside partial
results; website-only sources never become synthetic asset rows.

## Optional image policy

Only a selected listing's supplied Poly Haven or Sketchfab CDN image is eligible,
and only after both online access and Thumbnail preview are enabled. The loader
accepts `cdn.polyhaven.com/asset_img/thumbs/` or Sketchfab's model-thumbnail path on
`media.sketchfab.com`, with PNG/JPEG/WebP extensions. It does not visit arbitrary
uploader websites, source pages, item-download endpoints or protected providers.
The same application User-Agent is supplied. No redirects/cookies/auth are used.

Eight in-memory images/errors, one selected-item request, minimum 600 ms spacing,
8 seconds, 1 MiB encoded and 1024x1024 pre-decode dimensions bound this path.
Server 429 pauses image requests for the browser session; other failures remain
placeholders without automatic retries. Disabling network, Cancel, changing tabs
or closing the browser discards obsolete work. Thumbnails do not change format,
download, password, login, license or ownership labels.
