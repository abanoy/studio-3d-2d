# Publication packet audit

Result: **all six authoritative packet indexes pass**. Every listed file exists
with its exact SHA256 and byte length; declared counts/totals match, there are no
unlisted files, and all 157 physical files (including six top-level indexes)
remained unchanged during the read-only check. JSON parses; gzip originals match
their retained hashes; decoded content is UTF-8 source/text metadata. No native
model/archive/project/media/executable payload or binary asset signature was
found. Source code that generates authored fixtures is source, not uploaded
owner artwork. This content audit does not certify arbitrary source safe to run.

| Packet | Indexed files, excluding its index | Indexed bytes |
| --- | ---: | ---: |
| `has_snapshot_ordering/canonical_failure_20261113` | 11 | 326,869 |
| `has_snapshot_ordering/candidate_20261113` | 39 | 148,844 |
| `has_snapshot_ordering/cwd_probe_20261113` | 11 | 33,743 |
| `has_snapshot_ordering/main_actual_20261113` | 16 | 233,126 |
| `source_appearance/static_choice_draft_20261113` | 53 | 344,989 |
| `owner_review/relocatable_prep_20261113` | 21 | 513,942 |

`RESULTS.json` records exact identities, content checks and preservation. The
independent delegated audit also checked both static/relocatable root indexes,
the static overlay source index and both relocatable audit indexes.

## One documentation finding

The static draft contains a copied **historical local child-catalogue index and
README** under `catalogue_source`. That child index describes its original
standalone nine-file folder. Eight entries are present at those historical
relative locations; the duplicate `source_mdl_choices.py` is deliberately stored
only in `overlay/tools` in the compact packet. Its SHA is exactly
`a0f5e551ba9e2e38e3a92ca1d824a09311bf4ec4979a0d9947c128d15666e555`.

The authoritative top-level `FILE_INDEX.json` correctly includes every actual
file and has no missing entry. This is not packet corruption. However, the
nested README's standalone command should not be presented as the compact
packet's reproduction route. A future surrounding addendum should say:

> `catalogue_source/FILE_INDEX.json` and its README preserve the historical local
> child-catalogue proof context; they are not a standalone executable bundle at
> their copied location. The duplicate parser is retained once at
> `overlay/tools/source_mdl_choices.py` with the same recorded SHA256. The
> authoritative compact-packet inventory is the top-level `FILE_INDEX.json`.
> Reproduce the complete authored CPU checks from the two `overlay/tests`
> suites in a fresh owned copy. Do not run the old child-folder command or write
> generated test output into this frozen archive. The static chooser remains an
> unshipped draft, with Godot/UI/native conversion and graphics acceptance unrun.

No existing packet or index was changed to add this note.

## Main versus draft evidence

- The canonical-failure packet keeps the full run **failed**, with body animation
  72/1, the original generic child-create error and unknown Win32 error number.
  Its separate unchanged focused retry is 24 + 72 passed and does not pass the
  failed full run retroactively.
- The ordering candidate preserves all four attempts. The first writer 31/0
  predicate result is still an overall failed dependency/log gate; the harness
  parse failure stays failed. Final candidate 32/0 uses an inert persistence
  override and does not claim whole-app/packer acceptance.
- The CWD experiment retains all 240 successful absolute Python launches and
  labels its samples intrusive. It says the suspected race was **not
  reproduced**, with no captured Win267 and no universal absence/causality claim.
- `main_actual` separately records the actual port and scoped main tests. The
  port's three exact hashes (two runtime files and the new unit) match both the
  background-save and body verification source maps. Background reports preserve
  domain 10, ordering 32, Python project 31, Python save-fault 16, writer 20 and
  reader 5 checks with zero failures. Body reports preserve 24 + 72 passed and
  explicitly limit native-format fidelity. The wind report says headless.
  These scoped passes do not claim a new full canonical pass.
- Static appearance is labelled draft/unshipped. Its 53 + 29 checks are authored
  Python methods, not native or visual cases. The new chooser's runtime checks
  remain unrun. Historical prototype/native/bundle results are not promoted to
  this draft's acceptance.
- Relocatable owner review is preparation only. Its coordinator requires a
  matching passed canonical/release record before building, and refuses the
  archived failed canonical. The example old revision/path and narrow retained
  default-runtime probe are historical context, not a new built review or 129
  actual replays.

The root subsequently reported commit
`12071fe182a17d17e2a1547c7dbb97f6aa4dd160` published and a new full suite running.
This audit does not inspect or pass that new full run. It reads only frozen
packets and does not claim a fixed current main revision during publication.

## Optional later CPU reproduction proposal — not executed

If a separate draft driver is useful, it should first verify all 53 top-level
static packet rows, then copy only its 15 indexed overlay source/test files to a
fresh owned output folder. Pin the approved Python SHA, run the two authored
Python suites sequentially with `-B`, retain fresh per-run results, and require
exact source/runtime preservation. Treat the stand-in worker's clearly fake GLB
bytes solely as a transport fixture. Do not read original models, import
SourceIO/Blender, run Godot, or depend on an installed model cache. That proposal
does not authorize or claim an additional run.

No packet code, graphical/native runtime, Git mutation or main-source change was
performed by this audit. Only the audit's Python index/content reader ran before
the root's final no-new-process freeze; all later work was output-only prose.
