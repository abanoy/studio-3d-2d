# Model browser remix — proposed design

November 12, 2026. The owner invited an assistant contribution to the idea.
This is **design work only**: implementation remains paused. The original
[owner requests](model_browser_feedback_2026-11-12.md) remain authoritative;
additions below are assistant proposals, not silently approved requirements or
new completion gates. No adapters, UI, downloads or previews were implemented.

## A small model library with a useful journey

Owner clarification after the remix: **one Discovery tab covering local and
online models with proper labels**. This replaces the earlier three-entry-point
sketch as the preferred organizing idea. Keep one shared search bar and make
each item's source and available action clear:

| Source label | What it shows | Main next step |
| --- | --- | --- |
| Online, plus website name | International listings; about 100 varied results initially | Open original page or save listing |
| Local, plus location | Available files in installed content and chosen locations | Preview, then Add to scene |

The Saved shortlist can be an optional filter within Discovery rather than a
third main tab; that remains an assistant proposal. Exact source-switch/filter
layout is not settled, and the clarification does not approve every suggested
extra. Preserve both clear origin labels and website/model-type filtering.

Choosing the online area is explicit. Ordinary local model picking stays useful
offline. Searching from the top bar in Discover changes its feed to relevant
results; it does not need a second search screen. Website and type filters stay
independent and combinable. Local mode uses local locations rather than pretending
that a website filter identifies files on disk. Keep one selected model and an
optional details/preview area, preserving the owner's single-main-view preference.

## Proposed additions

### 1. A shortlist that bridges websites and local imports

Put a small Save/star action on listings and local models. Save the original
title, source link and known model metadata locally, without an account. A saved
online listing offers **Open website** and **Locate downloaded file**. After the
user retrieves a file in their browser/Steam, Locate lets them choose that file
or folder and associate it with the saved entry. Normal preview/import then takes
over. Keep source attribution with the entry.

This closes the gap between finding something and later using it. No automatic
downloads, subscription actions, background Downloads-folder scans or guessed
file associations. A linked file is not labelled compatible until inspected.

### 2. Search expansions the user can correct

Keep the normal search bar simple. A small **Also searched…** disclosure shows
the useful variants actually tried, such as `Miku Hatsune` or `初音ミク`. Offer
an exact-name option and a way to exclude an unwanted expansion when suggestions
become noisy. Preserve original-language titles; aliases help find them rather
than replacing their identity.

Rank full names and strong aliases first, and keep broad single-word matches
distinguishable. Discovery favors variety; a specific search favors relevance.
Do not let variety displace the actual model the user asked for.

### 3. Cards that make the next action clear

Keep cards light: optional image, original title, website, type and the established
Downloadable/Preview/Password badges. Put detailed requirements and local-readiness
information in the optional details area. Separate **access** from **usability**:
an offered download does not establish a working local model.

Preserve the owner's requested online title/thumbnail link to the default browser.
A small Details action can inspect listing metadata/images without opening a page.
Local single-selection attempts a 3D preview. Do not imply that an online thumbnail
means HAS has fetched the model or can render it in 3D. Add to scene is explicit.

### 4. One calm preview at a time

Prepare only the selected local model, with progress and Cancel. Keep the previous
good preview visible while it loads, clearly labelled so it cannot be mistaken
for the new selection. An obsolete result must never replace the current choice.
If preparation fails, show a compact per-item explanation and allow another
selection. The scene and saved work stay outside the preview operation.

Use existing separate-process foundations on resume, then verify bounds and
failure behavior. These are design goals, not guarantees against arbitrary
malformed files or driver failures. Do not convert 100 models merely to populate
a grid of cards; use available source images or existing cached thumbnails.

### 5. Discovery that stays varied without losing your place

Within the chosen filters, spread results across sources, creators, subjects
and formats where metadata supports it. Choose the exact balancing after research;
avoid presenting repeated near-identical variants as the whole first page.
Keep the requested roughly 100-item batches. Append new results without shuffling
loaded cards or resetting scroll position. Keep distinct editions with the same
title separate, while removing repeated source IDs/links.

### 6. Partial results and quiet explanations

Show useful results as providers answer. A slow or unavailable source gets a
small retry/status message; other sources remain browsable. Provider hints can
be dismissed as requested, while their concise requirement badges remain
inspectable. Unknown access stays unknown. Changing filters or search starts
a new result context and cancels obsolete work.

## Example journey

1. Open Discover and browse the diverse first batch.
2. Search `Hatsune Miku`, choose MMD and optionally narrow the website filter.
3. Inspect a result and Save it; its source page opens in the default browser
   when its title/thumbnail is clicked.
4. Retrieve the file using that site's normal process, then use the Saved filter and
   choose Locate downloaded file.
5. Select the linked local item, inspect its prepared preview, then Add to scene.

## Keep the first version focused

On an explicit resume, retain the owner's source research, international aliases,
badges, filters, pagination and preview goals. Prototype the shared browser/card
flow before multiplying controls. The shortlist/downloaded-file bridge and visible
alias correction are proposed additions to assess, not prerequisites that should
delay every useful increment. Leave social features, accounts, automatic downloads
and personalized cloud recommendations outside this concept.

Research provider capabilities before promising coverage. Validate the actual
local-preview isolation and preserve the current scene, originals, camera work
and independent drawings. No implementation, app launch, network model search or
tests were performed for this remix. The existing paused goal, unfinished
aggregate and acceptance ledger remain unchanged.
