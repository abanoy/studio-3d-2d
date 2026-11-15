Six-project review replay checker

This checker does not change application source or the six review packages and
does not create Studio. The snapshot builder owns that
directory and must first complete its exact committed-source and normal startup
proof at `output/owner-review-verified/Studio` for the explicitly supplied verified source revision.

Preparation (no GPU):

    python tools/verify_owner_review.py

After root review and GPU lease, from the checkout:

    python tools/verify_owner_review.py --run-gpu --expected-revision c6782d2f0f7b6ebbe868214ceb975e42afd129dd

The latter command deliberately starts six fresh private-desktop processes via
the review Studio's own `run.command`, with a generated scene in each fresh case
directory referencing the checker script and one package per process. It uses
the ordinary scene startup path, without `--script` or smoke flags, and waits for
`startup_recovery_finished` before checking that the fresh scene is empty at Home.
It then uses `app.has_project.open_file` with the normal
Python unpack worker, threaded project loader and application install transaction;
there is no direct fixture injection or alternate converter. Runtime unpacking
goes only into each case's fresh owned cache. The preparation command reads only
bounded `has.json` / `project.json` members in memory, without extracting payloads.

The builder's unique OS profile is shared and reported; every process has a new
recovery, recent-projects, display-preferences, workspace and project-cache path.
No personal installed Studio preferences or previous owner recovery is touched.
The builder's separate ordinary startup proof remains required; each replay also
records its own completed automatic recovery/Home startup before opening a file.
No direct Home call or forced mode replaces that startup behavior. Case paths
containing `smoke` refuse because the application treats that argument as testing.

The replay compares all saved schema4 world records (native metadata, IDs,
parentage, poses, shape tracks and other fields), camera keys, video, saved frame,
layer/cel metadata, audio and palette. JSON numbers tolerate at most 1e-12 absolute
round-trip variation, with no relative tolerance; dictionary keys, strings,
booleans, array order and identity strings remain exact. Explicit normalization:
managed runtime source paths become saved checksum-based portable paths; decoded
cel `image` / `raster_owner` values are removed; a missing optional palette becomes
`[]`. No other migration is accepted silently. Drawing pixels are checked against
their stored checksum. These six packages are schema4 and have no saved audio;
additional schemas or audio packages require an explicit extension to the contract.

Each case captures its saved camera at the saved frame in Setup and Focus, checks
native dimensions and identical native bytes, and records nonuniform, nonblack
pixels, full-area Setup geometry and unedited document/camera/history state. It
keeps four PNGs (Setup/Focus canvas evidence and the two native captures), with no
new movie renders. Native appearance/fidelity and usability are owner judgments;
this artifact proves a runnable review copy only. Existing project metadata can
still describe deliberately limited demos: Back hair is a synthetic helper demo;
Mima is a head-only 143-target expression demo, not a whole-character acceptance.

Before/after manifests include hashes, sizes and nanosecond modification times
for source files and input packages. Generated `output`, `.godot`, `__pycache__`
and bytecode are excluded from the source tree comparison. The committed builder
hash list is checked before replay; generated `override.cfg` is additionally
included in source preservation. Link/junction/reparse paths are refused.
Harness files are also hash/stamp checked. Evidence, logs, request files and
private-desktop receipts stay in a fresh `output/owner-review-validation/` run
directory. `--output` can select another fresh directory within this checkout's
`output`; it must remain separate from the review. `--review` can select an
existing six-package review within `output`. Existing evidence refuses overwrite;
links, junctions, parent traversal and paths outside `output` are refused. The
checker, replay script and this guide stay in their source locations. No private
art upload is authorized.

Metadata preparation and a headless syntax check do not establish runtime
validation. Accept a replay only when its fresh `verification.json` records all
six passes, clean private-desktop receipts, unchanged packages and unchanged
source/harness manifests. Retain failed attempts and their logs. A full software
aggregate and actual owner/device observations remain separate evidence.

Unpacked cache containment normalizes Windows separators, case and dot segments
in the replay. The Python driver additionally resolves the existing directory,
rejects reparse paths, and requires a strict descendant of that case's fresh
`has-cache` directory. A sibling directory with a similar prefix is refused.
