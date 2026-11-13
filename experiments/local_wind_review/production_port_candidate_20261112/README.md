# Local Wind Preview production-port candidate

This is a source-only review package. **It has not been copied into main or
shipped.** No application, graphical test, Blender job or native conversion ran
while preparing it. The source-copy audit was taken at `2c7320fa`. Root's later
onion report-publication correction is recorded in `HANDOFF.json` and must be
preserved; this task changed no main files.

`overlay` contains the exact **9 runtime files, 3 headless unit scripts and 4
current GPU scripts** from the isolated prototype. All bytes match their recorded
hashes; the current GPU harness is the final peer-fixture version used for the
830-check pass. It is not the older c678 or first-failure harness.

`baseline-compatibility.json` checks all seven existing main runtime paths against
85fa. Their code matches exactly after line-ending normalization. `app.gd` and
`renderer.gd` are also raw-byte identical. Five other working files use CRLF while
their 85fa Git blobs use LF; exact reconstruction recipes and both hashes are
recorded. There is **no functional divergence** in those seven files. The two new
runtime and all seven new test paths are absent in main. Preparation verified
934 main functional files unchanged by hash, size and modification time.

`manifest.json` is authoritative for exact overlay bytes. The normalized
`runtime-review.patch` and `integration-review.patch` are for review, not blind
application to mixed-line-ending files. Do not replace any other current main
test, tool or fixture with an old prototype copy. In particular, retain the
current native-readback QA and Hair OFF/contact-history contract corrections.

The isolated prototype has 94 headless checks and an actual six-process private
GPU pass: procedural60, VRM045, VRM145, Back hair47, lifecycle544, primary89.
All830 checks pass, original inputs and source identities remain unchanged, and
all six private-desktop receipts are clean. Those results do not certify the
future main port. The retained first GPU attempt failed its invalid peer fixture
(56 checks, one failure); its later peer check could alias the source. That first
attempt must not be used as independent-child evidence.

Read `INTEGRATION_PLAN.md`, `DRIVER_ADAPTATION.md`, `REGRESSION_CHECKLIST.md` and
`UI_WORDING_REVIEW.md` before using the candidate. The prototype wrapper is kept
unchanged as `reference/verify_gpu_prototype.py`; its old machine paths do not run
the candidate in main. Adapt the driver deliberately and verify its actual
project root and source manifest.

`retrieval-chain.json` binds every file to exact c678 and 2c Git objects where
available, then the final full peer-fixture test bytes. Old checkpoints remain
reconstructible and were not overwritten. Fetch latest main for a future resume;
85fa is a comparison baseline, not an instruction to reset newer work.

This phase previews **already declared groups** in a temporary candidate in the
existing scene. Pending helper setup preview before Apply and permanent per-group
inclusion/exclusion remain open. No private art, project, WAV, PNG or GLB payload
is in this candidate. Earlier reviews, preferences/recovery, originals, Steam
content, installed Studio and shared tools remain protected.
