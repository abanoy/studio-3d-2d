

## History continuation - Recovery and Ctrl+LMB studio increment
> OpenAI Codex / GPT-6, Windows desktop app, **2026-10-29 at 1454 EDT**.

- Owner asked continued development, keeping canonical source at
  C:/a/Programming/cloudflare/prototypes/studio-3d-2d; later steering explicitly
  requested Ctrl+LMB free camera. Added Ctrl-left mouse look with WASD/QE flight;
  plain pan, right POV, middle dolly and combined roll retain previous behavior.
  Release clears free-camera state. Synthetic flight checks pass; physical comfort
  and configurable sensitivity remain unverified/deferred.
- Implemented recovery.gd and an enabled-by-default60s recovery timer. Skips gestures,
  playback/export and open dialogs; Advanced offers30-600s interval, enable, explicit
  checkpoint, cache folder and previous manual-save restore. Recover nav is available
  in Simple. Restart offers latest/previous checkpoints; Later retains; Dismiss session
  hides matching manifests without deleting data. Restores are dirty unsaved copies
  requiring a chosen Save destination. Normal save clears recovered-session notices.
- Recovery sessions have process ownership, original project label, revision/timestamp;
  other live writers are hidden. Manual saves are untouched by autosave. Startup sample
  now starts clean. Immutable content-addressed recovery PNGs have pixel checksums;
  normal project generation structure/schema2 remains. Backup manifest loading is
  explicit/allowlisted. Initial checkpoint benchmark32.404ms was before full cached-file
  validation; final small fixture checkpoint54.839ms. No complex-map timing claim.
- Hardened managed GLB/WAV copies and PNG writes using temporary files, verified asset
  hashes and rename. Retry repairs partial cached files before committing metadata.
  A corrupt current JSON is never promoted over the previous readable backup. Loader
  rejects changed cached raster pixels. This is bounded interruption handling, not
  a hardware power-loss guarantee or fully hardened arbitrary untrusted-file loader.
- Conservative512MiB cache preflight budget; unchanged cels reused, old data retained.
  No automatic deletion or atomic concurrent-instance quota. PID reuse can hide an old
  session. Writes synchronous; large scenes/cel sets need profiling. Recovery stores
  committed drawings/keys/visibility/audio/frame, not undo, UI preferences or unkeyed
  navigation. Current session changes within60s can be lost. Preferences reset on launch.
- Saved13source/test/docs files with hash checks/backups under canonical
  output/checkpoints/2026-10-29-144940-before-recovery. Two storage/test follow-ups
  retained backups at145158-before-atomic-assets and145300-before-backup-guard.
  Kept matching development snapshot in managed hybrid-animation-studio. New docs
  describe controls/recovery/limits; no original specification/art/model edits.
- Actual canonical full python -u tests/verify.py exit0 after atomic cached-file repair:
  unit24, editor39, GPU spikes, encode failure/cancel, audio24, Dummy fallback, UI23,
  independent writer/restart recovery. After the last corrupt-JSON backup guard,
  targeted recovery-write, recovery and editor reran exit0:14writer +13restart checks,
  editor39. These exercise deferral, original-manifest byte equality, editable paint/
  keys/audio/frame restoration, partial manifests/assets, failed writes, cache checks,
  explicit prior backup, resolution and preserving live data on failed restore.
  FFprobe full-suite H264/AAC1920x1080,24fps,48frames,2.000s; AAC onset1.000/RMS5658.30.
  Final canonical recovery dialog screenshot inspected. git diff --check passed.
- Writer exits without resolving a checkpoint; reader is a separate real Godot process.
  Partial writes and write failure are injected in owned test files. No physical
  power cut, real full disk or forced OS crash claim. Worktree shader-cache warning
  remains; canonical final run has none. No new package, engine branding reintroduced,
  deployment, publishing, account changes, artwork uploads or unrelated edits.
  Capabilities unchanged; full spec still open. Next useful increment: owner feedback
  on navigation/drawing, then bounded pose/parameter persistence or drawing usability.
