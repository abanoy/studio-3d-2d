# Windows continuation — November 11

**Current consolidated reference: [RESUME_MASTER_PLAN.md](RESUME_MASTER_PLAN.md).**
It includes the earlier requests, later corrections and proposed ideas inline,
plus current status, inputs and resume instructions. This detailed pickup record
is retained as provenance; implementation remains paused.

**November 12 resume update:** owner explicitly said "you may continue";
the goal is active. Hair toggle-off restoration now passes focused8, fan63 and
import-physics41 software checks; see the master/evidence for scope. Later pause
wording below is historical, while no-participation-prompt and protected-data
rules remain current. Back hair/control work and the full aggregate continue.

Fetch current main from `https://github.com/abanoy/studio-3d-2d` and follow
`AGENTS.md`, the governing specification/addendum and the Windows goal. This
file is a pickup record, not an acceptance pass. The owner requested pausing work
on November 11, clarifying that the PC must remain running. No shutdown command
was sent. Resume work only when the owner asks.

November 12 addition: the owner reported further hair/accessory selection and
joint-assignment problems, especially Bikini Reimu's Back hair, and explicitly
requested **recording only, with no work yet**. The report and deferred steps
are in [hair_accessories_feedback_2026-11-12.md](hair_accessories_feedback_2026-11-12.md).
Keep the pause in effect; previous helper tests do not close these new issues.
The same note now also records the owner's toggle-off bug: a configured joint
deforms correctly while Hair & Cloth is on, but the deformation remains after
switching it off instead of returning. Reproduce and fix on resume, preserving
authored poses and recorded animation. No investigation has been started.

Further November 12 feedback: invert the affected RGB rotation ring's direction
(at least the top ring), and add a camera-facing relative rotation ring for
left/right rotation from the current view, with SMH/SFM as owner-provided
references. Details are in [rotation_gizmo_feedback_2026-11-12.md](rotation_gizmo_feedback_2026-11-12.md).
This is another deferred request; no implementation or diagnosis has begun.

Additional screenshot feedback: full-area scene setup with optional focused
camera framing, a possible 3 by 3 guide, rotation gizmos escaping that panel,
and configurable output resolution with a 1080p default. Timeline-varying
resolution is an exploratory Advanced idea, not an agreed design or acceptance
gate. See [viewport_framing_feedback_2026-11-12.md](viewport_framing_feedback_2026-11-12.md).
Owner subsequently clarified a **single-camera view preference**: the current
arrangement could suit multi-camera use, but favor one main camera view and
keep multi-camera layouts optional rather than making them the ordinary flow.
The private screenshot copy under `output\owner-feedback-20261112` is retained
locally and must not be uploaded or deleted as disposable output.

Future lighting direction: GMod/MMD, possible Ray-MMD/Raycast and Advanced Light
Entities controls; the priority is bounced/reflected illumination reaching props
and native character models as well as the map. The owner supplied GMod RTX
Remixed as a reference and asked about non-RTX feasibility. Research and deferred
steps: [lighting_feedback_2026-11-12.md](lighting_feedback_2026-11-12.md).
No renderer change or implementation has begun; the goal remains paused.

Later clarification: final video export can spend longer per frame than live
preview; distinguish lighting/render quality from existing encoder compression.
The lighting note records flat/simple/GMod-like/MMD-like/RTX-like choices and
retains the owner's uncertainty about an SFM default. Also record an optional
keyword-based online listings browser with provider labels/thumbnails, default
browser links, dismissible contextual retrieval notices, continued local
discovery and selection-triggered model previews with bounded conversion.
Details: [model_browser_feedback_2026-11-12.md](model_browser_feedback_2026-11-12.md).
Provider prerequisites and preview isolation remain unverified design work;
do not start online fetching, conversion or implementation during the pause.
The owner further requests broad international/non-English model-source
research for the future catalogue, client-bundled language/name/case/format
query variants, and evidence-based Downloadable/Preview/Password badges.
These labels may overlap; unverified metadata must stay unknown. Details are
in the same browser note. This does not authorize starting the research now.
Further clarification: open the online browser with a diverse initial feed of
about100listings, load about100more on scrolling to the bottom, and apply query
expansion when the top search bar is used. Explicit example: Hatsune Miku,
Hatsune, Miku, Miku Hatsune, with order-independent Miku/Hatsune keywords and
other relevant aliases. This remains deferred; no listings were fetched.
Also record separate, combinable **website/source** and **model-type/ecosystem**
filters (MMD, SFM, VRM, GMod), usable with discovery, search and pagination.
Details are in the same browser note; this is recording only, not implementation.
Owner invited an assistant design contribution: see the proposed
[model-browser remix](model_browser_concept_2026-11-12.md). It adds a local
shortlist/downloaded-file bridge, correctable search expansions, clear per-card
actions and calm previews/partial results. These are proposals distinct from
owner requirements; implementation and the goal remain paused.
Owner then clarified the organizing idea as **one Discovery tab covering Local
and Online with proper labels**. The concept is updated accordingly; Saved as
an internal filter remains an optional assistant proposal, not a separate
required main tab. This does not resume implementation.
Owner also suggests a later optional sounds category using the same researched
directory catalogue and Local/Online Discovery principle. Models remain the
priority; sound discovery is not a new prerequisite or acceptance gate.

The owner is busy and expressly requested no further test/review questions.
After an explicit resume, continue independent work without prompting. The four checksum-bound November 4
historical backups are dead by owner report; retain their historical checks and
do not substitute other files or ask for those backups again.

## Current software work

Retrievable fix commit: `02631f916ef28c146d36b684aff0b26f32cf013c`.
It restores speculative contact distance to 0.02 m after the correctly upright
Scout exposed a 6.97 mm failure. All original contact thresholds remain intact.
The candidate plus two main repeats pass 76 checks each; normal physics 56,
props 35 and recording 17 unit + 62 app checks also pass with native fixtures,
private desktops and verified movies. See the compact contact-distance benchmark.

The complete default suite was interrupted at the owner's pause request in the retained checkout
`C:\a\Programming\cloudflare\has-acceptance-session-20261111`.
Its log is `output\canonical-contact002-20261111.log`. A previous full run failed
at physics contacts; individual scoped passes do not establish an aggregate pass.
The interrupted run passed physics contacts76, physics, props, recording,
workspace resize/docking/nested layouts, fan flutter, shortcuts, camera edits,
helpers/morphs, shape catalogue/study/comparison, expressions, MMD groups, native
height review and map calibration. It was stopped during the subsequent body
curves work. The verified suite PID36200 and its owned children were terminated;
no owner applications were targeted. There is no complete aggregate pass.

Next actions:

1. After the owner resumes work, reproduce and address the November 12 hair and
   accessories report in the linked note, preserving precise single-item edits
   and the useful Advanced workflow. Also reproduce and address the linked
   rotation-ring direction and camera-facing ring requests. Reproduce the linked
   focus-panel/gizmo bug and review scene-view, framing and resolution requests,
   keeping the timeline-resolution idea exploratory. Then resume the full default suite from
   stable source. Fix reproducible failures without loosening
   assertions; preserve each failure and rerun the affected scope.
2. Verify final movie metadata and decoded audio analyses included by the suite.
   Record a complete aggregate only after its process exits successfully.
3. Refresh a separate review from the final remotely verified source, preserving
   all existing projects, profiles and recovery. Current `owner-review-current`
   still contains the earlier physics settings. `owner-review-verified` contains
   only four hash-matched project copies staged for the next snapshot; it is not
   a runnable new review yet. Do not request owner feedback.
4. Commit compact evidence, ledger/history and accurate remaining prerequisites;
   push without force and fetch/verify. Then remove only finished disposable
   outputs that no remaining case needs. Preserve private inputs and deliverables.

Current suite environment:

```powershell
$env:HYBRID_HECATIA_KRA=(Resolve-Path output/owner-fixtures/hecatia.kra).Path
$env:HYBRID_NATIVE_INPUTS='C:\a\dump'
$env:HYBRID_FFMPEG='C:\Program Files\ffmpeg\bin\ffmpeg.exe'
Remove-Item Env:HYBRID_FAN_PROJECT -ErrorAction SilentlyContinue
python -u tests/verify.py
```

All automated graphics use `run.command()` private Windows desktops. Do not
fall back to visible windows. Verify child desktop, no foreground child and
closed job/desktop receipts. Reuse existing approved Godot 4.6 standard/Python/
FFmpeg and the pinned temporary SourceIO runtime; no new installations or
replacement of installed Studio is authorized.

## Preserved inputs and deliverables

Keep both November 10 and November 11 session checkouts while their unbacked
private deliverables are pending. Especially protect:

- November 10 `output\owner-review\Studio\output\recovery`: actual owner work.
- November 10 `output\fan-native-probe\input`: actual fan reproduction.
- November 11 `output\owner-review` and `output\owner-review-current`.
- Current native preparation inputs, Mima prepared head and project aliases
  required by remaining tests. Do not delete them during an aggregate run.

Original HAS/KRA, Downloads archives, `C:\a\dump`, `C:\a\tools`, Steam content,
installed Studio and shared tools remain protected. No private art is uploaded.
Mima can be reconstructed with `tests/prepare_mima_fixture.py` and the original
checksum-bound archive. Native fixture provenance/rotations must remain intact.

After remote verification of the contact fix, only the disposable
`output\physics-solver-probe\Studio` source/fixture copy was removed: 1,409 files,
349,432,050 bytes. Its parent retains all raw failed/successful candidate JSON,
logs and source snapshot receipt; compact results are in the repository.

## Required observations still pending

Ledger remains 55/62 accepted groups and 52/54 implementation groups. Actual
artist/native appearance, novice/learner use, physical tablet/cursor/audio and
clean offline Windows setup remain separate gates. Do not certify these with
automation or invent feedback. Resume participation only when the owner grants
time. Do not mark the goal complete while independent required work remains.
