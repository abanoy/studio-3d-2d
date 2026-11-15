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

## Merge with main f0dd57a (2026-11-15)
Merged (merge commit, no rebase) 164 main commits. Conflicts in `src/app.gd` were resolved in main's favour:
- **Add scene** uses main's `import_actions.add` path and file filters; `pick_scene_file()` now calls exactly that,
  so the Simple Add menu and the Advanced button behave identically.
- **View and physics rows** keep main's `ScrollContainer`s (`ViewControlsScroll`, `PhysicsControlsScroll`)
  instead of the redesign's `HFlowContainer`s; `physics_bar` is now the physics scroll strip.
- The empty-state hint sits beside main's new `scene_view` setup.
- `src/canvas_view.gd` `scene_contains()` gained a 0.01 px tolerance: with the redesign's header the canvas is
  928x392 in the editor smoke, and a pointer at the canvas's exact left edge round-tripped (32-bit Vector2) to
  -0.00001 px, so the camera drag was rejected (`tests/app_smoke.gd` "captured drag continues outside canvas
  bounds"). Real off-scene clicks are still rejected; `tests/scene_view_unit.gd` passes (12830 checks).

Results 2026-11-15 (Linux xvfb): main f0dd57a and the merged branch both PASS ui, editor, pose, world_selection,
recovery_write, recovery.

## Neon Pro port (2026-11-15): Iridescent Pro layout + Midnight Neon theme
The owner approved a new look ("neon pro"): the Iridescent Pro layout with the Midnight Neon theme,
using mock images of Simple Draw, Camera and Pose at 1440x900. It is ported in nine steps on this branch. Simple mode follows
the mock; Advanced keeps every control, restyled. Codex behaviour wins wherever it conflicts.

### Step 1: theme foundation (`src/studio_theme.gd`, `src/app.gd`, `src/canvas_view.gd`)
- `StudioTheme.style` = `"neon"` (default), `"light"` (the classic skin exactly as before), `"dark"`
  (classic re-toned by `tone()`, the old opt-in dark theme). `set_style()` keeps `StudioTheme.dark` in step.
- Tokens as constants (`BG #08090C`, `BAR #0C0D11`, `PANEL`, `RAISE`, `HOVER`, `LINE/LINE2/LINE3`,
  `TEXT/TEXT2/TEXT3`, `BLUE`, `PINK`, `MID`, `FOCUS`, `STAGE`, `ON_NEON`) plus the semantic colours
  `DRAWING #4DA3FF`, `CAMERA #FF5FAE`, `MODEL #A98BFF`, `SAVED`, `PROBLEM`, `WARNING`. `NEON_STOPS` is the
  mock's oklch gradient precomputed as five sRGB stops, because SVG cannot interpolate in oklch.
- In neon, `tone()` maps legacy light neutrals to neon surfaces: v>0.9 goes to BAR, v>0.8 to PANEL,
  mid greys to LINE2 and dark text to TEXT. `surface()` draws a flat rounded box with the same content
  margins. Untouched callers therefore go dark automatically (home screen, source browser/import,
  progress, movement path, tutorials, timeline cel boxes).
- Helpers: `flat()`, `neon_ring()`, `neon_fill()` (StyleBoxTexture from in-code SVG, rendered at 2x with
  `ImageTexture.set_size_override`, so 1.5 px rings are crisp while sizes and margins stay logical),
  `kbd_box()`, `focus_box()`, `switch_icon()`, `check_icon()`, `slider_styles()`, `font()`, `mono()`,
  `label_variation()`.
- `make_theme()` neon branch: 13 px UI font; outline Button/OptionButton/MenuButton; type variations
  `GhostButton`, `PrimaryButton`, `NeonButton`, `TabButton`, `RailTile`, `ToolButton` and labels `RailLabel`,
  `CaptionLabel`, `MonoLabel`, `KbdLabel` for the later steps. Also: dark fields, BAR panels/dialogs/
  embedded windows, popups and tooltips with shadows, raised list/tree selection, neon switch
  CheckButtons and CheckBoxes, a neon slider fill with a white grabber, hairline separators, thin
  scrollbars, tabs with a neon underline, invisible split grabbers (the drag area and separation are
  unchanged) and a violet focus ring with a pink glow.
- Icons: `icon(kind, color := TEXT2, size := 16)` returns 24-unit line icons (stroke 1.7) drawn from
  the mock's inline SVG paths, cached by kind, colour and size. Old `icon(kind)` calls still work.
  Classic styles keep the glossy icons. The window icon (`app_icon()`) stays glossy in every style.
- Settings (Advanced part): the "Dark theme" checkbox is replaced by the "Interface theme" dropdown
  (Midnight Neon / Classic light / Classic dark), saved as `[display] theme` only when the user picks a
  theme. A file with no `theme` key and the old `dark=true` opens in Classic dark. `apply_theme_style()`
  rebuilds the theme, background, header colours, canvas surround, hint and toast. Icons that already
  exist change after the next start (the tooltip says so).
- The header uses a flat BAR with light title text in neon. The two-row layout is unchanged until step 2.
  The canvas letterbox is `STAGE` in neon and the classic grey otherwise.

Deviations (step 1):
- **Font:** the mock's Geist / Geist Mono are not bundled, and downloading fonts is not allowed. `SystemFont` fallbacks:
  Geist, Inter, Segoe UI Variable Text, Segoe UI, Helvetica Neue, Arial, DejaVu Sans (UI) and Geist Mono,
  JetBrains Mono, Cascadia Mono, Consolas, DejaVu Sans Mono (mono). The Linux test box renders Inter and
  JetBrains Mono. Windows usually gets Segoe UI and Cascadia Mono or Consolas.
- **Text selection:** `tests/workspace_controls_smoke.gd` requires selected field text to be `#163854`,
  so the selection colour is a pale neon blue `#B9D7FF` (8.2:1) instead of the mock's translucent blue.
- **Glows:** each glow is one shadow colour (StyleBoxFlat cannot stack shadows). The switch-knob glow is
  a radial gradient drawn in the SVG.
- **Not yet restyled:** the timeline drawing code stays light until step 6, and its cel boxes already
  use the dark `surface()`. Header layout is step 2, viewport overlays step 4, inspector cards step 5.
- **Contrast:** TEXT3 `#8C93A3` is 6.3:1 on BAR, 5.65:1 on RAISE, 5.28:1 on HOVER and 4.97:1 on the
  outline-button hover fill. TEXT2 is at least 7.9:1 and TEXT at least 14:1. `#07080B` on the neon fill
  is at least 5.8:1.

### Step 2: header bar (`src/app.gd`, `src/studio_theme.gd`)
- One 56 px bar (`#0C0D11`, 1 px `#22252E` bottom hairline, padding 0 12, gap 4) replaces the two-row
  header. Neon drops the blue gradient. Classic styles keep the gradient and get white-text buttons.
- Left: a 28 px brand mark (`StudioTheme.brand_mark()`: neon ring, radius 9, white glyph with its corner cut).
  Next to it, `title_label` shows only the project name: the `.has` file name, else the folder name,
  else "Untitled". The window title stays "Hybrid Animation Studio". Under the name is a 12 px save
  line with a 6 px dot: mint with a glow and "Saved" for an opened or saved project, amber "Unsaved
  changes" when `dirty`, grey "Not saved yet" for a project that has never been saved. "Saved just
  now / N min ago" counts only from a save seen in this session, which `refresh_title()` detects as
  `dirty` turning false while `recovery_status` reports "Project saved" or "Saved; recovery copy
  retained". The tooltip is the recovery status text. Then a divider and ghost New / Open / Save
  (h40, 16 px line icons; Save keeps its shortcut decoration), a divider, and the Add menu with a
  chevron. The menu items are unchanged.
- Centre: the existing Draw / Camera / Pose `mode_tabs` are built into `header_tabs`, a group panel
  (`#0F1015`, 1 px `#22252E`, r10, pad 3) in a full-width `CenterContainer` overlay with
  `MOUSE_FILTER_IGNORE`. The group is centred on the window and never adds to the bar's minimum
  width. Each tab is 104x40 with r7. The active tab has a `#171A21` fill, a 1 px `#2C303B` border,
  13/600 white text and a 2 px neon underline with a pink glow. Inactive tabs show 13/500 `#8C93A3`
  text. The tabs still call `pick_mode()`, stay `simple_only`, and `refresh_mode_tabs()` re-syncs
  them from `mode`.
- Right: `advanced_toggle` is now a `CheckButton` "Advanced" with the neon switch. Its `pressed`
  signal still calls `set_advanced(advanced_toggle.button_pressed)`, and the tooltip and
  `set_pressed_no_signal` are unchanged. More is a ghost menu with a chevron and unchanged items.
  Settings is a 40x40 gear button, visible in both modes, with the tooltip "Settings: …". After a
  divider comes Export movie: neon fill, 14/600 `#07080B` text, a dark icon, a mono "MP4" chip, and a
  pink glow from a `show_behind_parent` panel.
- Advanced: the same bar plus a wrapping row with every Advanced button: Home, Recover, Save as…,
  Open folder…, Sample room, Add scene, Add model, Installed, Add audio, Options and About. They are
  ghost buttons with icons and labels. "Advanced workspace" (`workspace_label`) appears as a 12 px
  caption at the start of that row.
- `fit_header()` runs on resize, on title changes and after `refresh_workspace()`. It measures
  the groups and steps down only as far as needed for them to clear the centred tabs: (1) New, Open,
  Save, Add and More go icon-only, (2) Export drops the MP4 chip, (3) the tabs go icon-only, (4) the
  project name and save line hide. The brand mark's tooltip keeps the name, and every button keeps
  its tooltip. Measured under xvfb: level 0 at 1440 px, level 2 at 1200 px (Advanced switch ends at
  x 927), level 3 at 1100 and 1000 px. There is no horizontal scroll at any of these widths.

Deviations (step 2):
- **Settings gear:** the mock has no Settings button. It stays visible in both modes, as the plan
  asks, because Advanced has no More menu and Settings was always on the bar before.
- **Glows:** the mock's Export glow is two shadows with negative spread. Here it is one pink shadow
  (alpha .45, size 8, offset 0 6). The tab underline glow is pink only.
- **Fit thresholds:** the plan's fixed breakpoints (1320 px for icon-only buttons, 1100 px for tabs)
  became measured steps, because the project name and the save text change the width.
- **Classic styles:** they use the same new layout, with the gradient bar and white text. Theme
  overrides chosen at start-up (icons and button colours) change after the next start, as for step 1.
- **Contrast:** TEXT2 on the bar is 9.98:1 (8.36:1 on hover). Inactive tab text is 6.17:1 on
  `#0F1015`. `#07080B` on the neon fill is at least 5.9:1.
