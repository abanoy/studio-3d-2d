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
graphics on private desktops. No implementation, downloads, app launches or
tests were performed for this report. Existing pause and ledger counts remain.
