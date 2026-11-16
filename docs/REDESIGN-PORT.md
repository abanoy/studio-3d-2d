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

### Step 3: World rail and dock headers (`src/world_selection.gd`, `src/workspace_layout.gd`, `src/app.gd`, `src/studio_theme.gd`)
- The World dock opens as the mock's 64 px icon rail. It is `#0C0D11` with a 1 px `#22252E` right
  edge, and the shell's left and top margins are 0 in neon, so it sits flush against the window edge
  and the header. From the top it has a 40x40 ghost "Unfold World list" button, the "WORLD" label
  (11/600, letter spacing 2, `#8C93A3`), one 52x56 tile per World row plus one per effect, a spacer,
  a 28x1 `#2C303B` divider, then the Frame, Save asset .has... and Size map… tiles.
- Tiles are built in `refresh()` from `entity_rows()` and the world's effects, next to the Tree
  items, and building them never selects anything. Each tile has an 18 px icon over an 11/500 label:
  building for an environment or map, runner for a model, sparkle for an effect, box otherwise.
  Names are cut with an ellipsis and the full name is in the tooltip; `_process` keeps the tooltip
  and label in step with renames and "(hidden)", like the Tree. Clicking a tile calls `select_entity(id)`
  exactly like the Tree, and `select_entity()` ends with `sync_rail()`. The selected tile is `#171A21`
  with a 1 px `#2C303B` border, a white 11/600 label, a white icon, and a 2 px blue-to-pink bar flush
  with the rail edge (inset 10, pink glow). Selection, the outline mask, picking, the context menu and
  the Tree metadata are unchanged; the Tree stays the source of truth and only hides in the rail.
- The bottom three are the existing buttons, restyled. Frame selected shows "Frame" as a tile,
  with its tooltip unchanged. Save asset .has... keeps its exact text, so it is still the only button
  with that text: the tile caption wraps it as Save / asset / .has... Size map… keeps its text. Button
  autowrap does not wrap correctly under a top icon. A tile's own text is clipped and drawn
  transparent, and a child icon and caption Label (mouse ignored) draw the face instead. The caption
  puts a zero-width space before ".has", because ICU never breaks before "." after a space. The help
  text moves to the rail's tooltip.
- Rail or list: `workspace_layout.refresh_world_mode()` runs when the World panel resizes. It shows
  the rail while the panel is narrower than 140 px and not floating. A wider dock, a floating window
  or a tab group elsewhere shows the list: the full-width Tree (BAR with no border, 28 px rows,
  selected row RAISE with 1 px LINE2, interface font with Yu Gothic UI as the fallback for Japanese
  names), full-width outline buttons with left icons, and the help label, all 8 px from the dock edges
  (the WorldContentScroll panel's padding). The hierarchy's minimum width is 64 in neon (156 in classic)
  and the World scroll's is 64. The Tree's minimum width is 0 in neon, and buttons and help wrap their
  words. That keeps the list's minimum under 140 px, so a divider drag can always narrow the dock back
  into the rail. Nothing is saved when the mode changes or at start-up.
- Unfold: the rail's top button widens the left dock to 232 px. In list mode a 24 px fold button in
  the header returns it to 64 px. Both change `horizontal.split_offset` and call `save_later()`, the
  same as a divider drag. They only show while World is docked on the left.
- Dock headers (World, Properties, Timeline): 28 px `#0C0D11` bars with a 1 px `#22252E` bottom line, an
  uppercase 11/600 `#8C93A3` title and a ghost chevron menu (same items). The handle is still
  `panels[id].get_child(0).get_child(0)` and the menu is still child 1. In the rail, the header is 78 px:
  the unfold button is a child of the handle drawn above the handle's own rect, the handle spans the
  rail (negative header separation) so "WORLD" stays centred, and the menu is a 12 px chevron beside
  the unfold button. The handle's centre is a drag target in both modes. The left and right docks are
  flush with the stage (`separation` 0 in neon, `minimum_grab_thickness` 8 keeps the divider
  draggable).
- `apply_theme_style()` calls `workspace_layout.apply_style()`, so switching the theme at run time
  switches between rail and list headers too. Classic styles keep the "⋮⋮ Title ▾" rows and the
  156 px list exactly as before.

Deviations (step 3):
- **Docking menu in the rail:** the mock has no docking menu. Codex's menu stays as a 12 px chevron
  beside the unfold button.
- **Icon size:** the plan says 20 px. The mock source draws 18 px icons, and those are used.
- **Rail length:** the mock's rail runs down beside the timeline. Here the timeline dock spans the full
  width, so the rail ends above it and the Frame tile sits at the bottom of the World dock. The grid
  is not changed (dock logic is Codex's).
- **Tree minimum width:** the plan keeps a 156 px Tree minimum in list mode. That would stop a drag
  from ever narrowing the dock below 140 px back into the rail, so the Tree has no minimum width in
  neon. List mode only exists from 140 px anyway.
- **Small windows:** at 1200x760 the rail's bottom tiles need the dock to scroll, and the 6 px
  scrollbar widens the rail a little (asset button still reachable, as workspace_controls checks).
- **Contrast:** tile labels (TEXT2) are 9.98:1 on BAR, the WORLD label and icons (TEXT3) 6.3:1 on BAR
  and 5.28:1 on hover, white on RAISE 17.6:1.

### Step 4: viewport overlays (`src/app.gd`, `src/canvas_view.gd`, `src/studio_theme.gd`)
- **Stage:** in neon, the centre column is a `#05060A` "Stage" PanelContainer that takes the old
  centre's place, so `workspace_layout` still moves `middle`'s child 1. It holds the view row, the
  canvas in a 12 px margin ("StageCanvas") and the stage footer. `image_rect()`, `scene_rect()`, the
  input routing and the canvas maths are unchanged.
- **Viewfinder corners:** a "Viewfinder" Control (mouse ignored) sits above the canvas in the same
  margin. It draws four 22 px corners, 2.5 px wide with round ends, 7 px outside the visible camera
  frame: TL `#2E8CFF`, TR and BL `#9C5CFF`, BR `#FF3D9A`. When the user zooms past the canvas, the
  corners mark the canvas edge. They redraw whenever the canvas redraws.
- **Canvas (editor only, never rendered):** the frame line is `rgba(255,255,255,.08)`. When Scene setup
  fills the view (Camera and Pose), four `rgba(4,5,8,.62)` bands dim everything outside
  `image_rect()`, as in the mock. Pose joints are white 2 px rings on the stage colour (radius 4), and
  selected joints are `#FF5FAE` rings (radius 5.5). The 3D gizmo and the review lines are unchanged.
- **View row** (`ViewControlsScroll`, transparent, margins 12 / 5 / 12 / 3): a left lead pill, then
  Codex's view controls in a second small pill, then the badges on the right. `fit_view_row()` keeps
  all of them on one line when they fit. Otherwise the Codex pill moves to a second line, and then the
  badges do. It runs on resize and when the visible pills or the badge text width change.
  - **Tool pill** (Simple Draw): the existing `tool_strip` and `tool_buttons` in a pill,
    `rgba(12,13,17,.94)`, 1 px `#2C303B`, r10, pad 3, gap 2, shadow `rgba(0,0,0,.8)` size 11 at (0,12).
    Each button is a `ToolButton` h40 with pad 0 8 0 10, gap 8, 13/500 `#B4BAC7` text, a 16 px `#8C93A3`
    icon and an 18 px keycap. The keycap is a `KbdLabel` whose letter comes from `keyboard_shortcuts`
    (pen, eraser, fill, sample). The active tool gets the neon ring on `#171A22`, a violet glow
    (`rgba(123,92,255,.4)` size 7), a 600 white label and icon, and a `#C9CEDA` keycap. A divider
    sits before Select area, which has no keycap ([M] stays in its tooltip). Below about 1000 px of
    centre width, the tools show only the icon and keycap. `pick_tool()`, `tool` and
    `refresh_tool_strip()` are unchanged.
  - **Camera strip** (Simple Camera): "Save key" PrimaryButton (h40, pad 0 16 0 12, 14/600, pink
    diamond icon, same `key_dialog`, shortcut in the tooltip), a divider, a ghost "Mouse and keys"
    button and the hint "Move the view with the mouse" (12 px, mouse icon). The button opens a popover
    with the existing camera help text, which stays in the Camera panel too. When narrow, the help
    button is icon-only and the hint hides.
  - **Pose strip** (new, Simple Pose): "Pose joints" sets `pose_editor.operation` to Rotate, "Move
    model" sets it to Move (same as the panel dropdown and middle-click: select, `item_selected`,
    `update_gizmo`), and "Mouse and keys" shows the canvas posing help in the popover. The strip syncs
    from `operation` every frame and only writes on a click.
  - **Codex pill:** `mode` (Advanced), `lighting_choice`, Fit view (Advanced), Frame scene, Undo / Redo
    (32 px icon ghosts in Simple, labelled in Advanced) and Scene setup / Frame / 3×3. They are h32
    outline chips, and the switches stay switches. The Pose physics row is a second chip pill, inside
    its own `PhysicsControlsScroll` as before.
  - **Badges** (mouse ignored): "● Frame N · S.SS s" (h32, pad 0 12, r6, `rgba(10,11,15,.86)`, 1 px
    `rgba(255,255,255,.1)`, mono 12/500, a 7 px neon dot and a `#B4BAC7` middle dot). The mode badge
    shows: Draw "Drawing on ■ <layer>" (10 px r3 `#4DA3FF` chip); Camera "◆ Camera key on this frame"
    in pink when a key is at the playhead, otherwise "No camera key here" in `#B4BAC7`; Pose
    "Posing ◆ <model> · <bone>" in violet (just the model when the root is selected). It is
    recomputed every frame and written only when the text changes.
- **Stage footer** (h40 under the canvas): left, a camera icon and the caption. Simple shows
  "Camera view · W:H" (+ " · NN mm" in Camera). `lens_mm()` uses a 36 mm-wide full-frame sensor and the
  horizontal angle of view (18 / tan(hfov/2)), which matches the mock's 54° = 35 mm. Advanced shows
  Codex's `scene_name` text, unchanged. Centre: the toast. Right: the legend, "Onion skin ○ Before ○
  After" (2 px `#4DA3FF` / `#FF5FAE` rings) in Draw when onion skin is on, and "Handles ○ Joint ◉
  Selected" in Pose.
- **Toast:** `status` is now created inside the toast. `status.text` is still set only by `message()`
  and never cleared. In Simple, `status` is hidden and the toast mirrors it: a 22 px neon check ring
  (coral ring with "!" and a `#FF5A7A` border when `is_problem_message()`), the first sentence (or
  the part before the first ": ") in 13/600 white, and the rest in `#B4BAC7`. The toast is `#101217`,
  1 px `#2C303B`, r10, pad 0 16 0 10, with a shadow. A 2 px neon strip shrinks over the existing 6 s
  fade, and then the toast fades as before. Two ellipsizing Labels are used instead of a
  RichTextLabel, so a long message is cut, not widened. The full text is in the toast's tooltip. The
  toast is placed by `fit_stage_footer()` inside a plain Control: it is centred and clamped so it
  never covers the legend (the legend hides first), and a long message never adds to the window's
  minimum width. In Advanced the toast has no box, and `status` is the plain wrapping line between
  the caption and the legend.
- **Footer under the timeline:** it keeps Show movie folder, Show saved frames, Retry MP4, Cancel export
  and `recovery_status`. `recovery_status` is Advanced-only in neon, and the header save line's
  tooltip carries it in Simple. So in Simple the row has no height unless one of the buttons is
  showing, and it appears as soon as one is.
- `empty_hint`: a `#111318` card, 1 px `#2C303B`, r10, `#F4F6FA` text, mouse ignored as before.
- New StudioTheme glyphs (cached SVG): `neon_dot`, `diamond`, `ring_icon`, `selected_handle_icon`,
  `toast_ring`.

Deviations (step 4):
- **Codex controls in Simple:** the mock's view row has only the tools and the badges. The lighting
  menu (lighting_smoke and the lighting lesson need it visible), Frame scene, Undo / Redo, Scene setup /
  Frame / 3×3 and the Pose physics row stay visible as h32 chip pills. At 1440x900 the Codex pill does
  not fit beside the full tool pill and the badges, so it takes a second 38 px line (and the physics
  pill a third in Pose). With a centre column of about 1250 px or more, everything is on one line.
- **Floating vs. row:** the mock floats the pill and badges over the picture. Here they sit in a row
  above the canvas, so no control ever covers canvas points (tests click film pixels, including
  1440,270). For the same reason the stage footer is a row under the canvas.
- **Turn model:** left out of the Pose strip (no existing behaviour maps to it; owner decision).
- **Frame guide:** the mock always shows the 8 % frame line. Codex's Frame toggle now draws a clearer
  45 % line in Camera / Pose, so the toggle still does something visible. The dim bands are always on in
  Scene setup.
- **Glow:** the mock's active-tool glow is blue and pink. Here it is one violet shadow.
- **Layout choice at start-up:** like steps 2 and 3, the stage layout is chosen when the app starts.
  Switching the interface theme at run time recolours the stage, and the classic layout returns
  after a restart. Classic styles keep the old view toolbar, scene line and footer toast exactly.
- **Contrast:** `#B4BAC7` is 9.6:1 on `#101217` (toast), 10.2:1 on the badge fill, 10.4:1 on the stage
  and 9.4:1 on a keycap. White on `#171A22` is 17.4:1, and `#F4F6FA` on the hint card is 17.2:1.
  `#8C93A3` icons are 6.35:1 on the pill.

Tests (step 4, Linux xvfb): ui, editor, pose, world_selection, recovery_write and recovery pass.
workspace_controls (48/0), workspace_docking, asset_package_smoke, brush_opacity_smoke, palette_smoke,
layers_smoke, onion_smoke, first_movie_smoke, rotation_gizmo_smoke, scene_view_unit and
lighting_lesson_smoke pass. color_sampler_smoke has the same 3 failures as before this step (same
check names). Windows verify.py was not run.

### Step 5: inspector Draw panel (`src/app.gd`, `src/studio_theme.gd`)
- **Inspector:** in neon the Properties scroll is 288 px wide (was 276) on `#0C0D11` with a 1 px
  `#22252E` line on its left. `section()` is flat in neon (`inspector_block()`): padding 18 16, a
  bottom hairline, a 12/600 `#B4BAC7` heading with no icon and an optional 12/500 `#8C93A3` meta on the
  right (`section_meta(box)` returns that Label). Camera, Model / pose, Audio, Movie encoder and
  Recovery get the same flat look now; steps 7 and 8 do their content.
- **How it is built:** `build_draw_inspector()` runs once at start-up, after every editor has added
  its controls to `drawing_section`. It moves Codex's controls into cards and restyles them. Nothing
  is replaced: `tool`, `color`, `radius`, `brush_opacity`, `brush_pressure`, `layer_choice`,
  `layer_visibility`, `onion_editor.enabled`, `layer_editor.launch`, the palette, the tool panels and
  every Advanced control keep their types, values, signals and Simple/Advanced visibility. A control
  the build does not know about (a later Codex addition) lands in "More drawing options" in its
  original order. `refresh_draw_inspector()` runs each frame from `_process` and writes only when a
  shown value changes. The old "Drawing" heading is hidden.
- **Tool card** (64 px): a 36 px neon-ring tile on `#171A22` with a violet glow and the white tool icon,
  the title 15/600, the subtitle 12 `#B4BAC7` (Pen "Smooth freehand lines", Eraser "Clear ink from this
  drawing", Fill "Fill a closed area", Pick color "Take a colour from the picture", Select area "Move or
  cut part of the drawing") and a keycap from `keyboard_shortcuts`. It follows `tool.selected`.
  Below it, the fill, colour sampler and selection panels share one padded block that only shows when
  one of them is showing (sampler: tool 3, with `source` still Advanced-only).
- **Colour:** five 40 px tiles, r8, gap 8. Tile 1 is the real `color` ColorPickerButton. It still opens
  the picker, but its own square swatch is hidden (`self_modulate` alpha 0) and two mouse-ignoring
  panels draw it rounded, with a 1 px `rgba(255,255,255,.14)` edge, a 2 px gap and a 2 px white ring.
  Tiles 2-5 are recent colours: a per-session UI list, never project or palette data, seeded with
  coral `#FF5A7A`, sun yellow `#FFC24B`, sky blue `#4DA3FF` and ink `#4B3F66`. When the brush colour
  changes, the previous colour becomes tile 2 (not while the picker popup is open). Clicking a tile
  uses the palette swatch's guards and sets `color.color`. The meta shows the palette swatch name, a
  known name (Codex's default `#F4DFBD` is "Warm white") or the hex value. The default colour is
  unchanged.
- **Brush size:** the `radius` SpinBox stays visible (ui_smoke). It is now the flat right-aligned
  "6 px" value in the heading row (suffix "px", arrows hidden, typing and the wheel still work). There
  is a 40 px preview (`#0F1116`, 1 px `#22252E`, r8) whose dot shows the current colour and opacity,
  with a diameter of 4 + radius (10 px at 6), and a neon HSlider 1-64 bound both ways to `radius`.
  `brush_opacity` gets the same "Opacity" value and slider (brush_opacity_smoke). The sliders take no
  focus, so the arrow keys keep stepping frames. Codex's captions ("Brush size (radius in pixels)",
  "Brush opacity (%)") show in Advanced only. Stroke smoothing (Advanced) sits in this card.
- **Layer:** the heading shows "N layers". `layer_choice` is a 40 px picker (`#101218`, 1 px `#2C303B`,
  r8, 14 px `#4DA3FF` chip, 12 px `#8C93A3` chevron) next to `Layers…` (outline, layers icon). Below
  are switch rows (h40, 16 px `#8C93A3` icon, 13 px text): "Show this layer" (eye) and "Onion skin"
  (h44) with the sub-line "● 1 before ● 1 after" (`#4DA3FF` / `#FF5FAE`). The onion always shows the
  one previous and the one next drawing, so the counts are true. Onion opacity (Advanced) follows.
- **Next card:** margin 0 16 14, a `#111318` card with a 1 px `#2C303B` edge and r10, a 28 px neon-ring
  arrow tile, a 13/600 title and a 12 `#B4BAC7` body. It uses the same conditions as
  `refresh_empty_hint()` (Simple Draw, not playing or exporting): an empty world gives "Next: add a
  scene or a model", and no drawing at the frame on the active layer gives "Next: draw on frame N". It
  is hidden otherwise.
- **New drawing:** a full-width 44 px PrimaryButton with the icon and label centred as one group.
  `keyboard_shortcuts` has no copy-drawing binding, so there is no keycap hint row (no fake "Ctrl D").
  The visible "Copy drawing here" outline button stays right under it. The exposure controls
  (Advanced) follow.
- **More drawing options** (still visible in Simple): the project colours (caption, grid, "Keep this
  color" and the Advanced swatch editor), the "Tablet pressure size" switch row, the `tool` dropdown,
  Import Krita artwork…, Import video artwork… and Reference sheet….
- New StudioTheme helpers: `chip()` (rounded square) and `dot()` (filled circle), both cached.

Deviations (step 5):
- **Dock header:** the 28 px "PROPERTIES" dock header stays above the tool card. It is the drag handle
  that workspace_docking / workspace_controls need.
- **Tool dropdown:** the `tool` OptionButton was visible in Simple, so it stays visible under "More
  drawing options" (contract: never hide a Simple control). The tool pill and the card already show the
  tool, so hiding it in Simple is an owner decision.
- **Opacity row:** the mock has no opacity. Codex shows it in Simple, so it is the second row of the
  Brush card. Together with the taller Codex timeline, this means New drawing is below the fold at
  1440x900 until step 6 shrinks the timeline.
- **Texts kept:** "Show this layer" (mock "Show"), "Layers…" (mock "Layers") and the real layer names
  (the mock's "Layer 2 · Ink" is sample data). The meta drops the mock's "· recent".
- **Next card:** it only appears when there is a real next step. In the screenshot fixture the frame
  has a drawing, so the card is hidden there (it is checked with an empty layer instead).
- **Ring and glow:** the current-colour ring is 2 px (StyleBoxFlat border widths are whole pixels), not
  1.5 px. The tool tile's glow is one violet shadow instead of blue plus pink.
- **Start-up build:** like steps 2-4, the neon inspector is built at start-up. Switching the theme at
  run time recolours it, and the classic card returns after a restart. Classic styles keep the old
  "Drawing" card exactly.
- **Contrast:** `#B4BAC7` on `#0C0D11` is 10.3:1 and `#8C93A3` 6.3:1. `#F4F6FA` on `#111318` is 17.2:1,
  `#B4BAC7` on `#111318` 9.6:1, and white on `#1A1D25` 16.4:1.
