# Online model discovery and selection previews — deferred ideas

Recorded November 12, 2026 while implementation remains paused. These are
owner requests and proposed design safeguards, not implemented adapters,
validated provider rules or new test results.

## Optional online listings browser

- A search box takes a keyword and lists matching models from sites such as
  **SFMLabs, BowlRoll and Steam Workshop**. Show the originating site clearly
  on each result, with an optional square thumbnail. Here "directory" means
  listing source/provider, distinct from a local filesystem folder.
- Clicking a result opens its original page in the user's **default browser**.
  This is not a request for automatic downloads, subscriptions, account access
  or scene imports.
- Relevant listings may show retrieval prerequisites and a **"Do not show
  this again"** checkbox. Owner example: when GMod is not detected and a result
  comes from its Workshop, explain that retrieving it may require a GMod copy
  and the Steam client. This is proposed messaging, not a verified universal
  Steam rule. Check current provider-specific installation/ownership/login and
  retrieval requirements before presenting them as facts. Scope dismissal to
  the applicable notice; do not suppress unrelated model/conversion errors.
- Preserve local discovery of models in installed content and user-selected
  directories. Online browsing should be explicit and optional, with the
  existing offline workflow usable independently. Do not fetch anything now or
  silently add background network activity to normal editing.

On resume, determine which providers actually support permitted search APIs or
other suitable search entry points before promising an aggregated results list.
Keep source attribution, links and unavailable-source messages clear. Merely
offering these ideas does not authorize implementing scraping, handling accounts
or downloading assets during the pause.

## Initial discovery feed and incremental browsing

### Separate website and model-type filters

Owner requests independent filters for **website/source** and **model type or
ecosystem**, with examples **MMD, SFM, VRM and GMod**. Let either filter narrow
the browser on its own, or combine them with each other and the search query.
Provide an unfiltered/All choice for each group. Apply the selected filters to
both the discovery feed and targeted search, including subsequent scroll batches.

Keep website identity distinct from model compatibility: a source can host
multiple types, and one model may support multiple ecosystems. Use available
listing/format metadata rather than assuming a site's name determines the
model type. On resume, define classification and verify combined filters,
clearing filters and pagination reset when filters change. This is recorded
only; no filtering UI, classification or source queries were implemented.

Owner clarification: when the optional online browser is opened without a
search query, first show **about 100 model listings**, prioritizing diversity
and discoverability. This is a combined initial feed, not a request to download
100 model files or to fetch 100 results from every provider. Possible diversity
dimensions include source, creator, subject and format where metadata permits;
the owner has not specified a balancing algorithm.

Scrolling to the bottom should fetch **another approximately 100 listings**,
appending them while preserving the current position and removing duplicate
results. Track provider pagination/cursors and exhausted sources, so the feed
can continue without repeating the same items. Retain source labels, optional
thumbnails and evidence-based availability badges.

The **top search bar** switches to targeted keyword search with the language,
name and formatting expansions below. Keep query relevance primary in search
results; the diversity-focused unfiltered feed is a separate entry experience.
The same incremental browsing pattern can support search results. Changing the
query must reset its pagination and discard obsolete responses without mixing
the previous query or unfiltered feed into the new result set. These are future
interaction/validation goals, not implemented network behavior.

## International source catalogue and client-side query variants

Owner clarification: future browser work includes **actively researching model
resources across the internet, including non-English communities**, to build
a useful catalogue of model-listing sites. The three named providers above
are examples, not the search boundary. Aim for broad international coverage;
do not promise an exhaustive index of the whole internet.

On resume, research and document each suitable source's name/URL, languages,
model formats or categories, supported search entry points, thumbnail/metadata
availability and retrieval prerequisites, with dated primary-source evidence.
Separate a discovered directory entry from a working/tested search adapter.
This is future research work; no new providers were searched or verified now.

Build possible query variations **locally in the client** so useful matching
does not require a translation service or compulsory AI. Proposed approach:

The owner's explicit example is `Hatsune Miku` expanding to **`Hatsune Miku`,
`Hatsune`, `Miku`, `Miku Hatsune`**, plus other relevant aliases. Also consider
the keywords **`Miku` and `Hatsune`** independent of their order. Preserve full
names and reordered names as strong matches, with individual words providing
broader alternatives. Combine or separate the terms according to each site's
actual keyword-search behavior rather than requiring only one exact phrase.

- Keep the exact original query and original-script model titles intact.
- Bundle an extensible alias dictionary for known names and terms, including
  alternate spellings, original-script names and romanizations. For example,
  `Hatsune Miku` and `初音ミク` can be explicit aliases. Do not assume mechanical
  transliteration or word-for-word translation recovers every proper name.
- Generate relevant alternate forms for capitalization, full-width/half-width
  characters, spacing, punctuation, hyphens/underscores and word order. Treat
  these as additional candidates rather than destructively rewriting every
  query. Case and character-width changes can matter differently by provider.
- Keep query syntax, encoding and case-sensitive behavior provider-specific.
  Preserve provider IDs, URLs and access credentials as supplied; these search
  transformations apply to query candidates, not passwords or asset paths.
  Run a bounded set of useful variant searches where necessary; appending all
  aliases to one query may make a provider require every term and lose matches.
- Merge duplicate results using provider item IDs/canonical URLs, retain source
  attribution and rank exact/original matches ahead of less-certain expansions.
  Preserve different models that merely share a title. Cancellation, caching
  and provider request limits must keep broad searches manageable.

The exact dictionaries, languages, normalization tools and provider adapters
remain to be researched and chosen on resume. Do not claim universal translation,
case-insensitive retrieval or successful cross-language matching from this note.

## Evidence-based availability badges

Owner proposes **"Downloadable," "Preview," and "Password"** labels based on
what HAS can actually retrieve or establish from a source's listing metadata.
These can overlap: a password-protected download may also offer a preview.
Do not force them into mutually exclusive availability states.
Define whether Preview means an image, interactive 3D or preview-only access;
a thumbnail alone does not establish an available 3D model preview.

Determine each badge from explicit provider evidence. Preserve the distinction
between a link to a download page, an available image/3D preview and a verified
file retrieval; a listing does not prove a compatible local model is ready to
import. A password label reports an access condition, not that HAS knows the
password. A failed fetch, sign-in wall or missing metadata is **unknown/unverified**,
not proof of "preview only" or "no download." Record when the information was
checked and keep prerequisite notices separate from uncertain availability.
No availability rules or live badge classifications were implemented or tested.

## Model preview when selecting a result

Owner asks for SFM-like behavior: selecting a model attempts to load/show it in
a preview, then notes native conversion and malformed files could destabilize
the program. Record **preview on selection** as the desired convenience.

Proposed design for resume: a separate preview area; selection previews without
adding or replacing objects in the open scene. Explicit Add/Load performs the
actual import. Use already available local files or validated cached data;
clicking a web listing still opens its page rather than fetching/converting
the model automatically. Standard formats may load directly; native formats
may need temporary conversion.

Keep conversion asynchronous and in a separate bounded, cancellable worker.
Debounce rapid selection changes, cancel obsolete jobs and reject stale results.
Reuse valid owned caches, invalidate changed inputs/dependencies and preserve
original files, project state and previous good previews. An unsupported or
malformed item should produce an understandable preview failure and allow the
next selection. Exact time/memory limits and supported preview formats need
design and verification; this is not a claim of hostile-file isolation or an
absolute guarantee against parser, GPU-driver or other failures.

## Existing foundations and future checks

[Installed content](installed_content.md) and
[native runtime profiles](native_profile_acceptance_review.md) describe local
discovery and bounded import paths. Existing separate-process workers are a
foundation, not evidence that preview-on-selection already exists. Standalone
complete native files can be usable without GMod/SFM installed; do not turn a
provider's retrieval prerequisite into a blanket prohibition on local imports.

After an explicit resume, review these entry points and define the Simple-mode
browser/preview flow. Verify direct loads and conversions, missing dependencies,
corrupt assets, rapid selection, cancellation, stale results, cache invalidation
and unchanged scenes/originals. Validate each online adapter and prerequisite
notice separately; provide source-specific unavailable states. Keep automated
graphics on private desktops. Include original-script/alias searches, case and
format variants, overlapping badges, unavailable metadata and duplicate titles
in future browser verification. Include the diverse first approximately100
listings, subsequent scroll batches, feed/search transitions, pagination reset
and rejection of obsolete query responses. No implementation, downloads, app launches or
tests were performed for this report. Existing pause and ledger counts remain.
