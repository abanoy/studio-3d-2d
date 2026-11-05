

## History continuation - Simple/Advanced studio UI and own startup identity

> OpenAI Codex / GPT-6, Windows desktop app, **2026-10-29 at 1421 EDT**.

- Owner prioritized Simple by default, optional Advanced, same underlying feature
  state, and XP/early Mac OS inspired gradients. Also requested hiding Godot header.
  Implemented that focused increment in the canonical studio-3d-2d and retained
  hybrid-animation-studio worktree snapshot. Fifteen changed/new source files synced
  after expected-hash checks; every replaced file backed up beneath canonical
  output/checkpoints/2026-10-29-141931-before-simple-ui. All copied hashes verified.
- Simple exposes contextual drawing/camera tools, main file/import/export actions,
  transport and audio start/mute after import. Advanced reveals exposure/delete,
  FOV/interpolation/key delete, trim/gain/remove, Save as, encoder and diagnostics.
  Toggle changes visibility only; retained settings keep affecting preview/export.
  No separate scene engine or project schema. Startup defaults to Simple every time;
  persistent preference is not implemented. No project edits/dirty flag from toggle.
- Added original in-memory SVG gradient icons and nine-patch theme in studio_theme.gd,
  pale beveled controls, blue gradient header and light timeline. No vendor artwork,
  external fonts, downloaded art or second UI framework. README/CREDITS/architecture/
  decision log/progress memo updated. Existing external art remains untouched.
- Godot boot image disabled, studio window title and original scene icon set.
  Start Studio.bat now starts launch.pyw through pythonw; normal launch uses installed
  windowed Godot executable with --quiet and hidden child console. Startup errors
  retain a user-visible message and output/launcher.log plus engine log. About keeps
  required Godot notices. Console python run.py remains explicit diagnostic route;
  batch itself may briefly flash. No packaged studio EXE or installer claimed.
- Actual canonical tests: python -u tests/verify.py exit0, including unit24, editor26,
  GPU spikes, encoder failure/cancel, audio24, Dummy fallback, new UI23. New checks
  cover routed real toggle clicks, camera/undo/frame, hidden FOV/hold and gain/trim,
  paint/source bytes, identical full-HD pixels, ongoing playback and1200px layout.
  FFprobe:48frames,1920x1080,24fps,2.000s; AAC onset1.000s and RMS5658.30 retained.
  python run.py --test legacy exit0:13checks for supplied prepared Miku/street.
  Actual pythonw launch.pyw --test ui completed with23checks; quiet regular Windows
  Godot launch exit0 and stdout has no engine header. git diff --check exit0.
  Final screenshots live in canonical output/ui-smoke/. Actual images inspected.
- Early iterations caught theme/icon layout issues, text encoding, runner type/syntax
  mistakes and intermittent global-injection toggle routing. Fixed the artwork/layout,
  UTF8 and test harness; direct viewport-local routed press/release passes full suite.
  Worktree retains the known restricted shader-cache warning; canonical final runs
  have no such warning. No physical mouse/tablet, accessibility, arbitrary DPI or
  subjective drawing/audio comfort certification from these synthetic checks.
- Full original spec remains open. Recovery/autosave, posing/parameter persistence,
  direct Source and native KRA remain pending. No unrelated app edits, deployment,
  publishing, external uploads, new install, vendor UI copying or background schedule.
  Same capabilities/limits as prior profile. Next: owner reviews this focused UI;
  resume a small recovery or posing increment after this usable checkpoint.
