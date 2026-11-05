# Retained native inputs for Windows regression tests

The owner-supplied Desktop VRM files may move after importing. Tests now use
`tests/native_sample_paths.gd` to prefer the original Desktop file, then look at
the existing worktree/normal native-import reports for an exact retained original.
This is test infrastructure; Studio's import or model evaluation behavior does
not change. No file is restored into Desktop or another game/application folder.

Fallback accepts only the two known sample names, a `vrm_preparation` report with
the exact original name, and a retained `.vrm` whose SHA256 matches that report.
Inputs over the existing128MiB limit refuse. It never renames a prepared GLB or
treats its geometry as proof of a raw native conversion. Missing/unverified inputs
retain the existing explicit skip/failure behavior. Tests log selected provenance;
normal source/dependency checksum checks remain authoritative.

Thirteen IK/body/contact/recording/appearance/timing/joint test sites share this
resolver. `native_sample_paths_smoke.gd` verifies both actual retained raw files
and refusal of an unrelated/traversing name. It is a small availability/integrity
probe, not hostile-file certification. The actual converters and graphics run in
the normal dependent suites on private Windows desktops.

The first current-source full review completed59 top-level commands, then failed
the five-native contact-persistence gate because both Desktop samples were absent.
All production inputs stayed unchanged. Some earlier optional VRM branches also
skipped; those passes do not certify the missing branches. The failure/logs and
private receipts remain preserved. A fresh complete review ran after the
test-only path correction and finished with exit0:115 top-level commands and126
private graphical runs. The functional source inventory stayed unchanged.
It includes the existing full verifier plus native/common/Source/browser/SFM/HAS/
placement/timing/joint wrappers. Full-goal completion, clean-machine/physical-input
and subjective artistic acceptance remain unproven. Normal Model7 and frozen web
are unchanged. See [the current review](current_review_2026-11-02.md) for its exact
scope and limitations.
