# Background project opening

HAS Open now keeps the extraction progress window active while a low-priority
CPU worker validates the unpacked manifest, hashes dependencies, decodes PNGs,
and builds private drawing owners and audio data. Only a completed, joined result
reaches the main-thread document installation transaction. Scene nodes, imported
3D runtime preparation and GPU work stay on the main thread.

The existing synchronous directory/recovery loader remains available and uses
the same installer. Project schemas, pixel integrity, bounded cold raster loading,
linked-asset validation, backup-as-copy and included-practice-as-copy behavior
remain. The real extraction process ID stays the busy-operation identity while
private decoding drains; no synthetic process IDs are introduced.

Cancel checks occur between drawing reads and project decode stages, and after
worker completion. It can wait for the current file operation. The old document
stays installed until all incoming checks and runtime preparation succeed. A new
recovery session, changed scene owner, or newer edit revision refuses a late
result. Shutdown joins the private loader before freeing its owner. Loading has
a separate 600-second guard after extraction's existing 120-second allowance.

The actual400drawing packed fixture passed12 checks. Open took23.888seconds,
including23.098seconds of private load work and111.254ms of main-thread installation;
793application frames ran, maximum observed gap177.728ms. All400pixel hashes and
one exact final GPU composition matched the prior independent save fixture.
Cancel before installation and over a populated document, newer edits, corrupt
staged JSON and New while pending preserve current content and identity. Original
archive bytes remain exact. These are cloud observations, not universal latency
bounds or physical Windows/device certification. The process RSS sample peak was
469,876,736bytes and observed HWM472,657,920bytes, separately from registered raster
admission and GPU/whole-session resources.

The first editor-based parse attempt accidentally scanned generated assets and
created UID sidecars. That owned editor process was stopped and only its untracked
UID files removed. Direct script checks and the actual private application suite
then passed. No generated import output is included in the change.

Use `python tests/verify_has_background_open.py --fixture /absolute/prior-save-case
--output /absolute/new-case --isolated-display :109`. The fixture directory is the
output of `verify_has_background_large.py`; it contains Background400.has,
expected.json and expected.png. See the recorded benchmark for exact source and
input hashes. Long-session cleanup/retention/concurrent quotas, direct directory
and recovery responsiveness, native 3D preparation latency and physical hardware
acceptance remain separate.

Compatibility regressions pass:76manual-save worker/fault/live/cold checks,
70nested-reference/audio/crash/startup/lesson checks, and49project/personal
settings matrix checks. Actual48frame1080p24,61frame720p30000/1001 and48frame540p24
H264/AAC outputs retain exact preview inputs and scoped audio onset tolerances.
[Recorded evidence](benchmarks/background_project_open_2026-11-07.json).
