# Redesign port ("Simplicity is key") — notes for Codex

Branch `claude/studio-redesign`, cut from `origin/main` at b0dab90 (2026-11-07). The finished
redesign was a separate Godot copy (`prototypes/studio-3d-2d-redesign` in banderov-cloudflare).
It was **not** copied over main: each piece was re-applied onto current main. Where main had
already changed the same behaviour, main's behaviour was kept and the redesign fitted around it.
Nothing under `tests/` was edited. Project data, renders, saves and undo are unchanged; the
redesign is presentation only.

Status: implemented and tested on Linux (Godot 4.6, xvfb, llvmpipe) with the commands below.
`python tests/verify.py` on Windows (private desktop runner) has **not** been run.

## What was ported (one commit per step)

| Step | What | Where (src/app.gd unless noted) |
|---|---|---|
| 1 Simple/Advanced shell | `simple_controls` list next to `advanced_controls`; `refresh_workspace()` hides Simple-only controls in Advanced, syncs the mode tabs, tool strip, Camera strip, icon-only Undo/Redo and the physics row (Advanced, or Pose in Simple). Simple top bar: New, Open, Save, **Add** menu (3D scene, Poseable model, Installed content, Audio), Export movie, **More** menu (Home screen, Recover, Project options, Interface size and fullscreen, Keyboard shortcuts, About). Advanced keeps every original button (Home, Recover, Save as, Open folder, Sample room, Add scene/model, Installed, Add audio, Options, About). Draw/Camera/Pose tabs drive the mode dropdown (still the source of truth, Advanced-only). Draw tool strip (Pen, Eraser, Fill, Pick color, Select area) drives the `tool` dropdown. Camera "Save key" strip. Fit view is Advanced-only. Nav and view toolbars are `HFlowContainer`s so they wrap. | vars after `advanced_controls`; `style_nav()`, `simple_only()`, `menu_button()`, `pick_mode()`, `pick_tool()`, `refresh_tool_strip()`, `pick_scene_file()`; `refresh_workspace()`; header + view toolbar in `build_ui()`; `_process()` re-syncs the strip |
| 2 Icons | Original SVG icons: eraser, fill, picker, figure, add, pause, layers | src/studio_theme.gd `icon()` |
| 3 Window fill | Main already had `window/stretch/aspect="expand"` and a saved interface scale (100–175 %) plus fullscreen in its Settings dialog, so only **F11** and a shared `toggle_fullscreen()` were added | `toggle_fullscreen()`, `_unhandled_key_input()`, `show_display_settings()` |
| 4 Guidance | Simple empty-state hint over the canvas (empty world / empty Draw frame / no camera keys); Simple status toast (rounded, red for problems) that fades after 6 s; plain wording for mode messages in Simple (Advanced keeps the original text) | `refresh_empty_hint()`, `refresh_status_style()`, `is_problem_message()`, `schedule_status_fade()`, `message()`, `change_mode()`; hint built after the canvas in `build_ui()` |
| 5 Opt-in dark theme + keyboard navigation | `StudioTheme.dark`/`tone()`/`tone_hex()` re-tone neutrals (theme colours and `surface()` stops); `apply_dark()` rebuilds theme, background, hint and toast. `apply_keyboard_nav()` makes buttons Tab-reachable and `_input()` forwards studio shortcuts from a focused button. Both are checkboxes in the Advanced part of Settings, saved in main's `user://display.cfg` `[display] dark / keyboard_nav`; off by default | src/studio_theme.gd; `back_gradient()`, `apply_dark()`, `apply_keyboard_nav()`, `initialize_display()`, `_input()` |
| 6 Polish | Header title `<project or Untitled>[ •] — Hybrid Animation Studio` (window title unchanged); Export movie hover pill | `refresh_title()`, `style_accent()` |

## Kept from main instead of the redesign
- **Status text is never cleared.** The redesign cleared `status.text` after 6 s; main's code
  (`return status.text`) and many tests read it back, so the toast only fades (`self_modulate`).
- **Settings dialog / display.cfg** instead of the redesign's `user://studio_prefs.cfg`
  interface-size menu and UI-size dropdown. More → "Interface size and fullscreen…" opens it.
- **Lighting dropdown stays visible in Simple** (tests/lighting_smoke.gd requires it).
- **Shortcut editor**: Save/Undo/Redo stay decorated by `keyboard_shortcuts`; the redesign's
  hard-coded keys (Ctrl+N, Ctrl+O, 1/2/3, `,`/`.`, Ctrl+D, `?`) were not added, so they cannot
  clash with user bindings. Main's own "Scene / camera" and "Pose model" dropdown labels are kept.
- **Window title** stays "Hybrid Animation Studio" (ui_smoke checks it); only the header label changes.
- The 5th tool (Select area [M]) that main added gets a strip button too.

## Dropped (and why)
- Folded World rail with object icons (`refresh_world_rail`, world_selection.gd changes):
  world_selection.gd and the hierarchy/workspace_layout code diverged a lot on main; left for a later step.
- Pose panel folding with no model (pose_editor.gd `fold_empty_panel`), Simple Pose "Frame model" strip:
  pose_editor.gd diverged; not ported.
- Welcome walkthrough, shortcut sheet (`?`), recent colour swatches, brush preview dot,
  `fill_missing_tooltips`, remembered picker folders, flat panel restyle and 13 px type,
  timeline_view.gd lane/stripe restyle, dark re-toning of timeline/canvas/home drawing code:
  larger visual changes in files main rewrote; not needed for the Simple/Advanced core.
- Simple short transport text and shorter Simple timeline: main's `workspace_layout.gd` now owns panel
  sizes; not changed.
- No redesign change had to be dropped because it broke a test.

## How to test (Linux)
```
GODOT=/path/to/Godot_v4.6-stable_linux.x86_64 tools/linux/run_test.sh . ui
# also: editor, pose, world_selection, recovery (runs recovery_write first)
```
`tools/linux/run_test.sh` mirrors `tests/verify.py`'s commands (`--ui-smoke --demo-room` etc.) under
xvfb. It now sets `HYBRID_PYTHON` to `python3` because main's `tools/recovery_processes.py` and save
workers run on Linux; `liveness_shim.sh` (the old Windows-only workaround) is kept for old snapshots
only. Logs go to `output/<test>-stdout.log`; tests rewrite tracked files in `output/` and
`tools/__pycache__/`, so `git checkout -- output tools/__pycache__` before committing.

Results 2026-11-07: baseline main b0dab90 and this branch both PASS ui, editor, pose,
world_selection, recovery_write, recovery. Not run here: the rest of verify.py, Windows.
