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
| 1 Simple/Advanced shell | `simple_controls` list next to `advanced_controls`; `refresh_workspace()` hides Simple-only controls in Advanced, syncs the mode tabs, tool strip, Camera strip, icon-only Undo/Redo and the physics row (Advanced, or Pose in Simple). Simple top bar: New, Open, Save, **Add** menu (3D scene, Poseable model, Installed content, Audio), Export movie, **More** menu (Home screen, Recover, Project options, Interface size and fullscreen, Keyboard shortcuts, About). Advanced keeps every original button (Home, Recover, Save as, Open folder, Sample room, Add scene/model, Installed, Add audio, Options, About). Draw/Camera/Pose tabs drive the mode dropdown (still the source of truth, Advanced-only). Draw tool strip (Pen, Eraser, Fill, Pick color, Select area) drives the `tool` dropdown. Camera "Save key" strip. Fit view stays in Simple as on main (classic always; neon Simple shows it icon-only while the canvas is zoomed or panned, `sync_fit_view()`). Nav and view toolbars are `HFlowContainer`s so they wrap. | vars after `advanced_controls`; `style_nav()`, `simple_only()`, `menu_button()`, `pick_mode()`, `pick_tool()`, `refresh_tool_strip()`, `pick_scene_file()`; `refresh_workspace()`; header + view toolbar in `build_ui()`; `_process()` re-syncs the strip |
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
  - **Codex pill:** `mode` (Advanced), `lighting_choice`, Fit view (Advanced; neon Simple only while zoomed or panned), Frame scene, Undo / Redo
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

### Step 6: timeline (`src/timeline_view.gd`, `src/timeline_navigation.gd`, `src/app.gd`, `src/workspace_layout.gd`, `src/studio_theme.gd`)
- **Panel:** the Timeline dock is `#0C0D11` with a 1 px `#2C303B` top edge. Its rows sit flush
  (separation 0): transport, one compact toolbar row, the ruler and the lanes. In neon the lanes'
  ScrollContainer fills whatever height the dock has (`SIZE_EXPAND_FILL`) with an 84 px minimum, so
  dragging the divider shows more lanes.
- **Transport (52 px):** a 190 px block (`TimelineView.LEFT`) with a 1 px `#22252E` right edge holds
  Codex's four buttons: |◀ first frame, ◀ previous frame and ▶| next frame as 40 px ghost icon buttons
  (`#B4BAC7`, icons skip-back / step-back / skip-forward), and Play as a 40 px circle
  (`StudioTheme.play_ring()`): a 2 px neon ring on `#14161C`, a white play/pause icon and a 9 px
  `rgba(123,92,255,.5)` glow drawn past the button with expand margins. `play_button` is the same
  Button with the same action and tooltip; in neon its text is empty and `refresh_play_button()`
  swaps the icon instead of writing "Play"/"Pause". Next to it is the readout: `transport_time`
  (new, mono 18/600 `#F4F6FA`, "1.50") and `transport_info` (mono 13 `#B4BAC7`, "/ 4.00 s · 24 fps").
  `transport_info` still carries the fps text, so "23.976 fps" stays in it. Advanced appends Codex's
  "frames 0–95, key 96 is the end boundary", and Codex's full sentence is the tooltip. Then the "Frame"
  caption with `frame_box` (still the SpinBox) as an 84 px mono field, and the legend on the right
  (gap 18, 12 px `#B4BAC7`): a 16x8 r2 `#4DA3FF` chip "Drawings", `#FF5FAE` "Camera keys" and
  `#A98BFF` "Model keys" diamonds.
- **Toolbar row:** Codex's sequence toolbar ("Sequences…", "Back to parent" when inside a sequence,
  the breadcrumb) and the zoom/pan bar (− / + / Fit, scrollbar, "Frames a–b") share one row
  (`compact_timeline_rows()` moves the bar into the toolbar). The bar is restyled in
  `timeline_navigation.apply_neon_style()`: 28 px ghost buttons with − / + icons and a mono 11 px
  `#8C93A3` caption. The ruler now sits directly on the lanes (the 38 px gap the bar used is gone).
- **Ruler** (the header-only TimelineView, 52 px): the top 24 px are the time ruler with `#22252E`
  borders and ticks (major `#363B48` h14, half `#2C303B` h8, minor `#22252E` h4) and mono 11 px
  `#8C93A3` labels. Simple shows seconds ("0 s", "1 s", the step grows when zoomed out); Advanced shows
  Codex's frame stride. The bottom 28 px are the Camera lane (it always lived in the ruler): a pink bar,
  "Camera", the key count, and 12 px pink diamonds with a 2 px `#0C0D11` ring on a 2 px
  `rgba(255,95,174,.3)` connector. The playhead is a 2 px neon line (blue to violet here, violet to pink
  in the lanes) with a glow, under an r6 neon tag with the frame number (mono 11/600 `#07080B`).
- **Lanes** (x < 190): `#0C0D11`, a `#22252E` right edge and row lines; a 3x16 colour bar (objects
  `#A98BFF`, drawing layers `#4DA3FF` with a glow, hidden layers grey, audio `#3DDC97`), the name
  12 px `#F4F6FA` and a right-aligned 12 px `#B4BAC7` count: keys for objects and channels,
  "N drawings" for layers, "muted" for muted sounds. The lane being edited gets the blue gradient
  `rgba(77,163,255,.16→.06)` with a `rgba(77,163,255,.25)` top line and white 600 text: the active
  layer in Draw, Camera in Camera mode, and the selected object (and selected channel) as before.
  `sync_timeline_focus()` sets this from `_process`. The expand arrow is a small chevron at the same
  spot (x < 19 still expands).
- **Content:** drawing blocks r4 `rgba(46,140,255,.16)` + 1 px `rgba(80,160,255,.55)` with the "a–b"
  text 12/600 `#B9D7FF`; the block held at the playhead is `rgba(46,140,255,.28)` + 1 px `#6FB2FF` with
  a glow; a dragged block gets a 2 px `#6FB2FF` (or `#FF5A7A` when refused) edge. Object clips/pieces are
  faint blue blocks (`#6FB2FF` edge when selected, `#FF5A7A` when the drop is refused) over a faint violet
  presence band, with violet model diamonds on a `rgba(169,139,255,.3)` connector. Body rigs keep their
  keys per channel, not in `piece.keys`, so the app passes each object's authored key frames
  (`timeline_row_keys()`, cached per object until its data changes) and the row draws them as its
  summary, following drag previews. Visibility keys are `#3DDC97` / `#FF5A7A`. Audio is
  `rgba(61,220,151,.12)` with a `#3DDC97` waveform (grey when muted, blue while trimming).
- **Fonts:** `ThemeDB.fallback_font` is replaced by StudioTheme fonts in neon (Inter / Segoe UI for
  names, JetBrains Mono / Cascadia Mono for numbers; Geist is not bundled).
- **Unchanged:** `LEFT = 190`, `ROW_HEIGHT = 26`, 30 px layer rows, `x()`, `frame_at()`, `row_y()`,
  `channel_y()`, `layer_y()`, `audio_y()`, `header_height()`, `cel_rect()`, `audio_rect()`, every hit
  test, gesture and signal, `DEFAULT_VERTICAL_OFFSET`. The neon drawing is in `neon_draw()` /
  `neon_content()`; classic styles return to Codex's `_draw()` / `draw_content()` untouched. When Codex
  adds something to those, the neon pair needs the same addition.
- New StudioTheme pieces: `play_ring()` and the `step-back` and `minus` line icons.
- **Tests (Linux xvfb, step 6):** ui, editor, pose, world_selection, recovery_write and recovery pass.
  workspace_controls 48/0, workspace_docking 18/0, asset_package 22/0, brush_opacity 18/0, palette 23/0,
  layers 40/0, onion 37/0, animated_channels 35/0; timeline_navigation 35/0 and cel_timing 50/0 with the
  tone.wav / room.glb fixtures their verify_*.py scripts create. color_sampler keeps its 3 baseline
  failures on this box.

Deviations (step 6):
- **Lane order:** Codex's order is kept (Camera in the ruler, then objects, drawing layers, audio).
  The mock puts Drawings first; row geometry is API, so it is not reordered. At the default 1440x900
  layout the Camera lane and the first object rows show, and the drawing layers are a short scroll (or
  a divider drag) away.
- **Extra row:** the mock has no sequence toolbar or zoom bar. Both are Codex features visible in
  Simple, so they stay, in one compact row between the transport and the ruler.
- **Dock header:** the 28 px "TIMELINE" header (the drag handle) stays above the transport.
- **Four buttons, Frame field:** the mock shows previous/next key around Play; Codex has first frame,
  previous frame, Play, next frame, which all stay. The "Frame" SpinBox stays next to the readout.
- **Frame 0 edge:** frame 0 maps to x = 190 (geometry is API), so a key at frame 0 is cut in half at
  the label column (the frame tag is kept inside); the mock pads its content 12 px.
- **Clip names:** blocks show Codex's "a–b" frame range; the mock's "Run-up" / "Leap · frames 24–42"
  names and the dashed "Landing · no drawing yet" slot are sample data and are not faked.
- **Glow and diamonds:** the playhead glow is two translucent quads, and the diamonds have sharp
  corners (the mock rounds them by 2 px).
- **Start-up build:** like steps 2-5, the transport block, readout, legend and the shared toolbar row
  are built at start-up in neon. Switching the theme at run time switches the timeline drawing at once
  (classic returns to Codex's drawing); the classic transport row returns after a restart.
- **Contrast:** `#B9D7FF` on a drawing block is 10.9:1, `#DCEBFF` on the held block 10.9:1, `#BFF5DD`
  on audio 13.1:1, `#8C93A3` ruler labels on `#0C0D11` 6.3:1, `#8C93A3` on a hidden layer's block
  5.6:1, `#07080B` on the neon tag 5.9-6.0:1, white on the active lane 15.5:1.

### Step 7: inspector Camera panel (`src/app.gd`, `src/studio_theme.gd`)
- **How it is built:** `build_camera_inspector()` runs once at start-up in neon, after
  `camera_transform_editor` has added its panel to `camera_section`. It moves Codex's controls into
  the mock's cards and restyles them. Nothing is replaced: `fov`, `camera_near`, `camera_far`,
  `interpolation`, Save camera key, Delete key, the mouse-controls text, the hint and the numeric
  camera panel keep their types, values, signals and Simple/Advanced visibility. A control the build
  does not know about (a later Codex addition) lands in "Camera details" in its original order.
  `refresh_camera_inspector()` runs each frame from `_process`. It rebuilds the key rows only when the
  key frames, the "Just saved" key or the fps change, and restyles rows only when the frame changes.
  The old "Camera" heading is hidden. Classic styles keep the old card exactly.
- **Header card** (64 px): a 36 px neon-ring tile with the white camera icon and a violet glow,
  "Movie camera" 15/600 and "What the movie will show" 12 `#B4BAC7` (`inspector_header()`, ready for
  the Pose panel in step 8).
- **Camera keys:** the heading shows "N keys". There is one 44 px row per key in `keys`, sorted by frame
  (r8, padding 0 10 0 8, gap 10). Each row has a pink diamond, a 48x27 placeholder tile (`#121638`,
  1 px `#363B48`, r4, camera icon; there are no renders), "Frame N" 13/500 and "S.SS s" 12 `#B4BAC7`,
  with " · start" on the first key and " · end" on the last. The row for the key at the playhead is
  `#171A21` with a 1 px `#2C303B` edge, a 600 white title and the diamond with a ring and glow
  (`StudioTheme.key_glow()`). Clicking a row runs `stop()` and then `set_frame(frame)`.
- **"Just saved":** `insert_key()` keeps a copy of the key it stored in `last_saved_key`. This is a
  session-only UI note, never saved. The chip (h20, padding 0 7, r5, `rgba(255,95,174,.16)`, 1 px
  `rgba(255,95,174,.45)`, 11/600 `#FFD6EA`) shows on the row whose key equals that copy. Undo
  removes the key, so the chip goes with it; redo brings both back. Key storage, `put_key` and the
  history entry are unchanged.
- **Lens:** a Wide / Normal / Close segmented control. The group has padding 3, r10, `#0F1015` and a
  1 px `#22252E` edge. The selected button is `#171A21` with a 1 px `#2C303B` edge, 13/600 white; the
  others are 13/500 `#B4BAC7` as in the mock source. The presets are full-frame focal lengths, 24 /
  35 / 60 mm. `lens_fov(mm)` inverts step 4's `lens_mm()` (36 mm-wide sensor, horizontal angle at the
  project aspect, so the vertical `fov` of a 16:9 project is 46° / 32° / 19°). A preset is applied
  with `fov.value = …`, through the existing `value_changed` path, which applies only in Camera mode;
  the buttons are disabled when `fov` is not editable. The meta "NN mm" is `lens_mm()`, the same
  number as the stage caption. A preset shows as selected only when `fov` holds its value, so Codex's
  default 60° camera (18 mm) shows no selection.
- **Field of view (Advanced):** "Field of view" with the `fov` SpinBox as a flat "32 °" value and a
  neon slider bound to it (15-120, step 1, disabled when `fov` is not editable). Codex's "Editor
  camera FOV" caption follows. It is Advanced-only like `fov` itself (ui_smoke: "Simple hides
  technical controls").
- **Framing guides:** a 44 px switch row (grid icon, "Framing guides" / "Thirds and safe area") that
  calls `scene_view.set_guides(on, on)`, the same call and preference the view-row Frame / 3×3
  switches use. It shows on only when both guides are on (`frame_enabled and grid_enabled`).
  `scene_view.gd` is unchanged.
- **Save camera key [K]** stays in the panel (Codex) as the 44 px PrimaryButton with the key icon
  centred with the label (`style_primary()`, shared with New drawing; it re-centres if a shortcut
  change renames the button). Codex's hint "Move freely, then save a key. / Draw returns to the
  animated shot." follows in 12 `#B4BAC7`, then the Advanced-only "Delete key at this frame" (outline,
  eraser icon).
- **Help card:** "How camera keys work" / "Each key remembers a view. The camera glides between
  them." in the shared `inspector_card()` (28 px neon-ring tile with the path icon), which the Draw
  Next card now uses too.
- **Camera details** (only when something in it is visible, i.e. Advanced): the mouse-controls text
  (Advanced-only in neon now; Simple reads the same text in the "Mouse and keys" popover over the
  picture), Numeric camera view…, the near / far fields and Camera interpolation.
- Refactors with no visual change (the Draw inspector screenshot is pixel-identical): `neon_tile()`
  (tool card and card tiles), `inspector_card()` (Next card) and `style_primary()` (New drawing).
- The CRLF source made the two multi-line Codex labels render with blank lines between lines. In
  neon their text is stripped of `\r` (display only; the popover already did this).

Tests (Linux xvfb, step 7): ui, editor, pose, world_selection, recovery_write and recovery pass.
  camera_transform_smoke 25/0 (run directly), workspace_controls 48/0, workspace_docking 18/0,
  asset_package 22/0, brush_opacity 18/0, palette 23/0, layers 40/0, onion 37/0, animated_channels
  35/0. color_sampler keeps its 3 baseline failures. camera_range, timeline_navigation and cel_timing
  need the fixtures their verify_*.py scripts create and were not rerun with them (without fixtures
  they fail on the missing audio file exactly as before this step).

Deviations (step 7):
- **Simple FOV slider:** the mock shows "Field of view 54°" with a slider in Simple. Codex keeps `fov`
  out of Simple (ui_smoke), so the slider is Advanced-only. The lens presets give Simple users the
  same control in three steps. Showing a Simple slider is an owner decision.
- **Lens numbers:** the plan's sample presets (75 / 54 / 30°) and the 12 / tan(fov/2) formula assume a
  24 mm sensor height. Step 4's stage caption already reads the mock's 54° as 35 mm (36 mm width,
  horizontal angle), so the presets are defined in millimetres with that formula, and the caption,
  the Lens meta and the presets always agree. "Close" is 60 mm because 85 mm needs a FOV below Codex's
  15° minimum.
- **Thumbnails:** the tiles are placeholders (camera icon on `#121638`); the mock's scene thumbnails
  would need renders.
- **Save key and hint in the panel:** the mock has no Save button in the panel. Codex keeps
  "Save camera key [K]" and its hint visible there, so the help card sits below them and is a short
  scroll away at 1440x900 (the mock pins it to the bottom of a taller panel).
- **Dock header:** the 28 px "PROPERTIES" header (the drag handle) stays, as in step 5.
- **"°" spacing:** SpinBox suffixes always get a space ("32 °"; the mock shows "54°").
- **Toast wording:** `insert_key()` still posts Codex's "Camera key saved at frame N."; the mock's
  "Key saved at frame 24. Next: …" is not copied.
- **Contrast:** `#FFD6EA` on the chip over the current row (`#3C2538`) is 10.6:1, `#B4BAC7` on `#171A21`
  8.9:1, `#B4BAC7` on `#0F1015` 9.8:1, disabled `#8C93A3` on `#0F1015` 6.2:1, white on `#171A21` 17.4:1.

### Step 8: inspector Pose panel (`src/pose_editor.gd`, `src/app.gd`)
- **How it is built:** `pose_editor.build_neon_inspector()` runs once at start-up in neon. `app.gd`
  calls it after `mmd_pose_importer.setup()`, because that importer adds "Import MMD pose…" and
  "Import MMD motion…" to the panel after `build_ui()`. It moves Codex's controls into the mock's cards
  and restyles them with the step 5/7 helpers (`inspector_block`, `inspector_header`, `inspector_card`,
  `style_switch_row`, `style_outline`, `style_primary`, `lens_button_boxes`). Nothing is replaced, and
  every control keeps its type, value, signals and Simple/Advanced visibility. A control the build does
  not place (a later Codex addition) lands in "More pose options" in its original order.
  `pose_editor.refresh_neon_inspector()` runs each frame from `app._process`. It writes only when a
  shown value changes, and does the key lookup only when the model, selection, frame,
  `recovery_revision`, mode or auto-key changes. Sections with nothing
  visible hide themselves, and so do switch rows whose switch is hidden. The old "Model / pose" heading
  is hidden. Classic styles keep the old card exactly. `motion_editor.gd`, `contact_editor.gd`,
  `movement_path_editor.gd` and `pose_library_editor.gd` needed no change: their inspector buttons are
  restyled from `pose_editor.gd`, and their windows already use the app theme.
- **Header card** (64 px, `inspector_header()`): a 36 px neon-ring tile with the joint icon. The title
  is the selected bone's display name (`BoneLabels.display`, so Simple shows friendly names and
  Advanced the original), or the model name for the root, or "No model yet". The subtitle is "Joint
  on <model>" / "Whole model" / "Add a model to pose it", 12 `#B4BAC7`. On the right, "◆ Keyed" (a
  10 px `#A98BFF` diamond, 12 `#B4BAC7`) shows when the active model has an authored pose key
  (`authored_keys()`) at the current frame. That is the violet diamond under the playhead on its
  timeline lane. Auto-key stores only the changed channels, so a per-joint "keyed" answer would need
  new key semantics; the chip reports what the timeline shows.
- **Pose tool:** two segmented groups on one row, Rotate | Move and Local | World, styled like the
  Camera lens presets. Rotate/Move calls `app.pick_pose_operation()`, the same path as the Simple
  Pose strip (select + `item_selected`). Local/World selects `space`, emits `item_selected` and
  redraws the gizmo. Both re-sync from `operation.selected` / `space.selected` every frame, so tests
  and the middle-click tool cycle that call `select()` directly are reflected. The OptionButtons stay
  visible under "More pose options" (contract 9: a control visible in Simple stays visible).
- **Motion** (meta "Whole model"): "Move limbs naturally" / "Hands and feet bend the limb" and "Hold
  feet while posing" / "Feet stay put as the body moves" as 44 px switch rows with sub-lines (the
  same `limb_ik` / `hold_feet` CheckButtons, tooltips and signals), then Planted feet… (outline), and
  in Advanced, Reverse limb bend.
- **Next card** (`inspector_card()`, arrow tile), Simple Pose only, not while playing or exporting,
  like `draw_next_step()`: an empty project shows "Next: add a scene or a model"; no selected model
  shows "Next: pick a model to pose"; a model with no pose keys shows "Next: pose frame N" / "Click a
  joint, then drag a colored handle. Changes are keyed automatically." (or "Press Record pose key…"
  when auto-key is off). It is hidden otherwise. The mock's "Next: pose the landing / Go to frame 60…"
  is sample story data that the app cannot know.
- **Reset selected / Frame model:** Reset selected is the 44 px PrimaryButton with the reset icon
  (`style_primary()`). Frame model is a 40 px outline button (`#101218`, 1 px `#2C303B`, 13/500) with
  the frame icon centred with its label. The hint follows in 12 `#B4BAC7`: "Reset returns this joint
  to its rest pose." for a bone, and "Reset returns the model to its starting place." for the root
  (`reset_selected()` zeroes the root's position and rotation). **Visibility change:** in neon, Reset
  selected is taken off the Advanced list, so Simple shows it as in the mock. It is the same button,
  calling the same `reset_selected()`; this adds a control and removes none. Classic keeps it
  Advanced-only.
- **Below the mock's content:** "Keys and helpers" holds Record pose key (key icon), Auto-key pose
  edits (Advanced switch row), Body poses…, Motion feeling… / Try motion feeling…, Movement path…,
  Shapes / expressions… (shown only when the model has shapes, as before) and the two MMD imports.
  "Bones" holds Codex's model summary (`info`), the bone search (h36), the bone tree, "Hold Alt to
  reveal bones." and the Alt/drag help text, all captions in 12 `#B4BAC7`. "Visibility" holds
  Visible at this frame and Reference only (switch rows), Remove visibility key here, Reference
  opacity (when reference-only) and, in Advanced, Use imported shape. "More pose options" holds the
  Rotate/Move and Local/World dropdowns plus Advanced controls in Codex's order: Add model…, Snap
  (switch row), Local X/Y/Z, Apply local values, the locks, uniform scale, Apply model scale,
  interpolation, Delete selected part key, Save view as camera key, Remove object and the base-shape
  editor (`base_shapes.panel`, still Advanced-only).
- **Not changed:** pose maths, the gizmo, auto-key, IK, contacts, the sub-editors' logic and
  `refresh_values()` / `rebuild_tree()`. `setup()` only keeps references to six existing controls
  (`frame_button`, `record_button`, `reset_button`, `remove_visibility_button`, `alt_hint`,
  `help_label`).
- **Contrast:** `#B4BAC7` sub-lines, hints and captions on `#0C0D11` are 10.0:1. Unselected segment
  labels `#B4BAC7` on `#0F1015` are 9.8:1, and selected white on `#171A21` is 17.4:1. White on the
  Reset button (`#1A1D25`) is 16.8:1, and `#F4F6FA` on the Frame model button (`#101218`) is 17.3:1.

Tests (Linux xvfb, step 8, run by the coordinator): ui, editor, pose, world_selection, recovery_write
  and recovery pass; workspace_controls 48/0, workspace_docking 18/0, asset_package 22/0. The step 8
  log of the remaining smokes was cut short; step 9 re-ran all of them on top of step 8 (below).

Deviations (step 8), owner decisions:
- **Bend / Twist sliders:** not implemented. They would be new pose maths: a per-joint "bend" and
  "twist" decomposition, with limits ("Straight" to "Fully bent", "Inward" to "Outward"), on top of
  the Advanced Local X/Y/Z rotation fields, and the rig has no joint-axis metadata to map them
  reliably. Posing stays with the gizmo (and the Advanced numbers). Adding them is an owner decision.
- **Physics follow-through switch:** not implemented. It would mirror the Physics / Hair & clothes
  toggles in the Pose view row, which have side effects (freezing, previews, recording). Those
  toggles stay where Codex put them. Adding the switch is an owner decision.
- **Pose tool section:** not in the mock (Bend/Twist take its place there). Rotate/Move and
  Local/World are kept as the task requires, so Reset selected / Frame model sit a short scroll lower
  at 1440x900 than in the mock.
- **Keyed chip semantics:** model-level (a key of this model at this frame), not per-joint (see
  above). The diamond has no glow.
- **Header text gap:** the shared `inspector_header()` uses a 2 px gap between title and subtitle
  (the mock uses 4 px) so the Draw and Camera headers stay pixel-identical.
- **Duplicate dropdowns:** the Rotate/Move and Local/World OptionButtons stay visible in Simple under
  "More pose options", as the Draw panel keeps the tool dropdown.
- **Extra Simple controls below the mock content:** Record pose key, Body poses…, Motion feeling…,
  Movement path…, MMD imports, bone search/tree and the visibility switches are visible in Simple
  today, so they stay (restyled) below the mock's cards.
- **Dock header:** the 28 px "PROPERTIES" header (the drag handle) stays, as in steps 5 and 7.

### Step 9: Advanced mode, secondary surfaces and final pass (`src/app.gd`, `src/dock_tree.gd`, `src/workspace_layout.gd`, `src/home_screen.gd`, `src/movement_path_view.gd`, `src/movement_path_editor.gd`, `src/sequence_timeline.gd`, `src/reference_sheet_view.gd`)
Every change is neon-only (`StudioTheme.is_neon()`); "Classic light" and "Classic dark" draw exactly
as before. Behaviour, control types, texts that tests look up and Simple visibility are unchanged.
- **Already neon from steps 1-8 (checked, no change):** the Advanced header row (ghost icon+label
  buttons that wrap, "Advanced workspace" 12 `#8C93A3`), the Settings, Project options, Credits,
  Recover work, Keyboard shortcuts, Tutorials, Reference sheet, Scene effects, Installed Source
  content, Editable sequences and Movement path windows (`AcceptDialog` / `Window` panels, tabs,
  fields, lists and switches all come from the neon Theme on the root window), the Advanced
  inspector sections (Audio, Movie encoder, Recovery and the rest use the step 5 section style) and
  the Advanced plain status line (a theme Label: 13 px `#F4F6FA`, 16.8:1 on the stage). Panels that
  still call `StudioTheme.surface()` with light colours (`has_project.gd` progress, `source_browser.gd`,
  `source_import.gd`, `particle_editor.gd`, `tutorials.gd`) already get the flat `#0C0D11` neon surface
  with a `#2C303B` edge from step 1's `surface()`.
- **Footer** (`style_app_footer()`, `draw_app_footer()`, new `app_footer` reference): the Advanced
  `debug_label` is mono 11 `#8C93A3` (6.3:1) on a `#0C0D11` band with a 1 px `#22252E` top hairline
  and 12 px side padding. The band's expand margins cover the 8 px column gap and the 10 px right
  margin. The footer row below it (`recovery_status`, Show movie folder, Show saved frames, Retry
  MP4, Cancel export) draws `#0C0D11` to the window's right and bottom edges, with the hairline
  itself when the debug line is hidden. It draws nothing while the row is empty, which is Simple's
  usual state, so Simple stays pixel-identical. `recovery_status` keeps step 4's CaptionLabel
  (12 `#B4BAC7`, 10:1), now vertically centred. `apply_theme_style()` restyles the footer too.
- **Docked tabs** (`dock_tree.style_book()`): tab groups no longer copy the Button styleboxes and the
  `#163854` text in neon. That text was dark-on-dark, about 1.4:1 on `#171A21`. They use the theme's
  tabs instead: the selected tab is `#171A21` (RAISE) with a 2 px neon underline and white text, the
  others `#8C93A3` text (5.7:1 or more), hover `#1D2029`. The tab strip is `#0C0D11` with a 1 px
  `#22252E` bottom hairline. `workspace_layout.apply_style()` restyles every book and the theme of
  every floating window when the theme changes.
- **Drop preview** (`workspace_layout.style_preview()`): rgba(46,140,255,.18) fill, a 2 px `#2E8CFF`
  border, r8, and a 600-weight `#F4F6FA` label ("Tab here", "Split left", "Dock right", "Detach as a
  window"; 15.5:1 on the stage). Classic keeps its rgba(38,122,204) box.
- **Floating panel windows:** they already took `app.theme`. Now a floating Properties panel also
  draws the `#0C0D11` chrome (`draw_panel()`), as World and Timeline already did.
- **Home screen:** the full-window backdrop is `#08090C` at 97 % instead of pale blue. The card was
  already the neon surface.
- **Movement path plot:** a `#05060A` stage card with a 1 px `#2C303B` border and r8. Axes are
  `#363B48`, the path line is `#4DA3FF` and key dots are `#A98BFF` (selected `#FFC24B`) with a stage
  centre. Frame numbers are mono 13 `#F4F6FA`. Before this, the classic navy dots and numbers were
  drawn on the dark card. The help line reads "Violet dots are your keys" in neon ("Black dots…" in
  classic).
- **Sequence strip** (`sequence_timeline.gd`): rows alternate `#0C0D11` / `#111318` with `#22252E`
  hairlines and `#B4BAC7` "Sequence N" labels. Clips are `#1D2029` with a `#363B48` edge; the selected
  clip is `#1C2A44` with a `#2E8CFF` edge. Clip names are `#F4F6FA` (13:1 or more) and the playhead is
  `#FF3D9A`. Geometry (rows of 26 px, `row_rect()`) is unchanged.
- **Reference sheet viewer:** the backdrop is `#05060A` with a `#363B48` frame line. The transparency
  checkerboard stays light, so the artwork's own colours read the same.
- **Colour sweep:** a grep for `Color("`, `Color(0…` and `surface(` across `src/` found no other white
  panel or dark text in neon. The remaining literals are 3D scene materials, renderer backgrounds,
  transparency checkerboards, gizmo axis colours, swatches or classic-only branches.

Tests (Linux xvfb, step 9): ui, editor, pose, world_selection, recovery_write and recovery pass.
  Full extra.sh: workspace_controls 48/0, workspace_docking 18/0, asset_package 22/0, brush_opacity
  18/0, palette 23/0, layers 40/0, onion 37/0 (baseline numbers). color_sampler keeps its 3 baseline
  failures. Also run directly: sequence_editor_smoke 45/0, reference_sheet_smoke 30/0, home_smoke
  34/0 and tutorial_catalog_smoke 17/0. movement_path_smoke fails the same way with and without this
  step on this Linux box ("scale row exposes its numeric control", then a script error at line 103),
  so the failure was there before step 9. Classic light check: screenshots of every surface above
  with `[display] theme = light` match the pre-step-9 build pixel for pixel. The only difference is
  the live "overlay N ms" timing in the Advanced debug line.

### Remaining deviations from the mock after the final pass
A final `shoot.sh` run at 1440x900 was compared with mock-draw.png, mock-camera.png and mock-pose.png.
The deviations below remain. The per-step lists above give the details.
- **Fonts:** the mock's Geist / Geist Mono are not bundled and fonts may not be downloaded, so system
  fonts are used through `SystemFont` fallbacks (UI: Geist, Inter, Segoe UI Variable Text, Segoe UI,
  Helvetica Neue, Arial, DejaVu Sans; mono: Geist Mono, JetBrains Mono, Cascadia Mono, Consolas,
  DejaVu Sans Mono). The Linux test box renders Inter + JetBrains Mono; Windows will usually show
  Segoe UI + Cascadia Mono or Consolas. Widths differ a little from the mock.
- **Codex controls kept visible in Simple** (contract 9: a control that Simple shows today stays
  visible): the lighting dropdown, Frame scene, Undo / Redo, Scene setup / Frame / 3×3 guides
  (Camera, Pose), the Physics / Hair & clothes / local record row (Pose), "More drawing options" and
  the extra Draw / Camera / Pose panel controls below the mock's cards. Because of these, the view
  controls take a second line under the tool pill, and the inspector scrolls further than in the mock.
- **Sample data not faked:** "Rooftop Chase" / "Saved 2 min ago" (the real project name and save
  state are shown), the Rooftop / Sky / Pigeon / Props rail items (real World rows), the drawing
  clip names and the "Landing · no drawing yet" slot, camera-key thumbnails (placeholder tiles),
  "Scarf keeps swinging…", "Next: draw / pose the landing" (real next steps instead), the Bend / Twist
  values and "Ctrl D" (only real shortcut labels are shown).
- **Owner decisions:** the Bend / Twist joint sliders and the Physics follow-through switch (new pose
  maths and new side effects; step 8), a Simple field-of-view slider (Codex keeps `fov` Advanced-only;
  step 7) and Turn model in the Pose strip (no existing behaviour maps to it; step 4).
- **Dock headers:** the 28 px "PROPERTIES" / "TIMELINE" headers stay. They are the drag handles that
  docking relies on (contract 4).

## Review 1 fixes (layout budget, overlays, timeline, Pose)
Applied after the first review of the neon port (screenshots: neonport/review1-fixed/ in the session
scratchpad). Simple mode at 1440x900 now gives a camera frame of about 975x548 (mock 992x558).
- **Stage overlays:** the canvas fills the whole stage. The view rows, the simulation row and the stage
  footer float over it (`StageOverlay`; only pills and buttons take the mouse). `CanvasView.fit_inset`
  (neon only, zero elsewhere) keeps the fitted frame clear of them: symmetric, 48 px at the sides,
  max(top rows, footer) + 10 px top and bottom. In Scene setup, `scene_view.copy_camera()` now also
  overscans vertically (display height / frame height), so the dimmed scene shows on all four sides.
  Picking still goes through `image_rect()`; scene_view_unit passes with its zero-inset canvas.
  The tool pill and the caption start at the frame's left edge, and the badges end at its right edge.
- **One pill row in Simple:** Codex's view controls stay available but are compact in neon Simple:
  icon-only lighting and Scene setup dropdowns, an icon-only Frame scene, and Frame + 3×3 merged into
  one "Guides" menu with two check items (`scene_view.guides_button`, calls `set_guides`). If the pill
  still does not fit beside the tools and badges, it moves to the right end of the stage footer. The
  footer legend hides first when the footer is short of space. A second row is only a fallback for
  narrow windows. Advanced keeps every labelled control.
- **Camera pill:** "Move the view with the mouse" is plain text after the pill. **Pose pill:** "Turn
  model" = Rotate with the model root selected (no new semantics).
- **Simulation row (neon Simple):** hidden unless a simulation or recording is running. While one is
  running it stays visible in every mode, so its off switches never disappear (Codex behaviour). The
  Pose inspector's Motion block mirrors Codex's Physics and Hair & clothes switches ("Physics" and
  "Physics follow-through"). Classic Simple and Advanced show the row as before.
- **Pose inspector:** the Rotate/Move group is Advanced-only (Simple uses the viewport pill).
  Local/World moved next to Codex's space dropdown under "More pose options". Hold feet and Planted
  feet… moved to "Keys and helpers" (same visibility and behaviour).
- **Timeline:** the dock opens about 166 px tall. In neon Simple the docked PROPERTIES / TIMELINE
  title bars are 6 px grab strips: `panels[id].get_child(0).get_child(0)` is still the drag handle,
  and the full header returns in Advanced or when the panel floats. There are no split gaps and no
  outer window margins. The Sequences… toolbar and the zoom bar sit inside the transport row: still
  visible in Simple (timeline_navigation_smoke clicks them), and `editor.toolbar` is unchanged. The
  lanes area is at least 56 px. The ruler holder stays 52 px because it also holds the Camera lane.
  Codex's sequence strip opens under the transport row. Content starts 12 px inside the lane area
  (`CONTENT_PAD`, neon only). `x()` and `frame_at()` share that origin and span. Lane colours:
  Camera lane pink (band, glowing bar, "N keys"); posed model lane violet with an "Auto key" chip.
  Draw and Pose scroll the lanes once to the lane being edited. The legend is Simple-only. Advanced
  puts the debug line and recovery status on one footer row.
- **Inspector:** the Opacity row is one line (label, slider, value). "Stroke smoothing" uses
  CaptionLabel. SpinBox steppers are themed: 12 px chevrons, no default white arrows.
- **Smaller fixes:** the toast says "Drag a joint to pose. Changes are keyed automatically." with the
  hand glyph. Fixed: a faded status message came back on refresh, and a message posted in Advanced
  never faded in Simple. Windows created earlier now follow a theme switch. Classic skins map neon
  icon names to glossy icons, and Classic shows the Settings label. New home and package icons. Rail
  tiles show the short captions "Save asset" and "Size map" (button texts are unchanged). The rail's
  docking chevron only shows on hover. Camera key rows restyle only when they change. The view row is
  refitted only when the badge width changes. Pill keycaps follow rebound shortcuts. The zoom
  buttons use 16 px icons with a distinct disabled tint.
- **Declined / partial:** the full-height World rail with the timeline beside it is a structural
  change to the dock tree and to saved layouts, so it is left as a documented deviation. "Save
  asset .has..." and "Size map…" stay labelled tiles in Simple (contract 3). The Frame field and the
  single-frame step buttons stay in Simple, where Codex shows them. At 1440x900 Advanced, the default
  split leaves the Timeline dock a little short (28 px header plus the footer row), so its outer
  scrollbar can still show until the divider is dragged; the split is not changed on the Advanced
  toggle, to keep saved layouts untouched. The Pose actions are not pinned to the bottom (blocks
  follow them in Simple). In Pose at 1440 px the Codex pill sits in the footer, so the "Handles"
  legend hides.

### Review 2 fixes (`src/app.gd`, `src/workspace_layout.gd`, `src/timeline_view.gd`, `src/studio_theme.gd`, `src/world_selection.gd`, `src/timeline_navigation.gd`, `src/sequence_editor.gd`, `src/pose_editor.gd`)
- **Grab strip overlay:** in neon Simple the docked Properties / Timeline grab strip is now 10 px and
  overlays the top padding of its content (panel separation `-STRIP_HEIGHT`, header `z_index` 1), so
  the inspector and the transport row start right under the bar (Pen card 56-120 as in the mock).
  Godot picks controls by tree order, not z_index, so `workspace_layout.strip_input()` (from `_input`)
  routes a left press inside the strip to the same heading drag, and hover draws a 2 px `#363B48`
  line on the panel's top edge. A splitter's drag area wins where it overlaps the strip (it reaches
  4 px into the panel). The strip is 10 px rather than 6 so the handle's centre stays outside that
  drag area (workspace_controls presses the handle centre, timeline_navigation the divider centre).
  The strip takes the top 4 px of the transport buttons' click area. Advanced, classic and floating
  docks are unchanged.
- **Splitters:** the no-grabber icon is a zero-size `PlaceholderTexture2D`, so docks meet with no
  2 px `#08090C` seam; `get_drag_area_control()` still gives the drag strip.
- **Top bar:** Export movie's glow is a soft 6 px pink shadow on a panel inset 6 px plus a fainter
  blue one inset 8 px (no hard band at the bar edge). The gear (Settings) is Advanced-only in neon;
  Simple reaches the same dialog through More > "Interface size and fullscreen…" (classic keeps it).
- **Header save line:** the last save time is forgotten when the shown project changes (path or
  folder), so New / Open no longer inherit "Saved N min ago" from the previous project.
- **Interface theme:** Classic light <-> Classic dark still switch live. A switch to or from Midnight
  Neon is saved and applies at the next start (the neon panels, pills and cards are built at start-up,
  so a live switch left low-contrast mixes). The tooltip and a status message say so.
- **Stage footer:** left (caption, at most 170 px) and right (Codex view pill + legend) are reserved
  separately. The toast is centred when that fits, otherwise it sits in the free gap. When it still
  cannot fit, the grey part wraps to a second line (only when two lines hold it; narrower stays one
  cut line with the tooltip). The legend first drops its title ("Handles" / "Onion skin"), then hides.
  In neon Simple the Codex dropdown chips use a 5 px pad and the view toolbar a 2 px gap. At
  1440x900 Pose shows the full hint and "○ Joint ◉ Selected" (the "Handles" title is dropped there).
- **Camera pill:** Save key uses a new 18 px filled pink diamond with a dark plus (`key-solid`,
  classic alias `key`).
- **Timeline:** the held drawing block is an opaque `#193961` fill (the StyleBoxFlat shadow drew
  under the translucent fill). Model lanes use violet boxes (`object`, `object_selected`); a
  one-frame object or piece without keys draws no stub box (the presence band shows it). The Camera
  lane count is a bare number like the model lanes; drawing layers keep "N drawings" as in the mock.
  A ruler label the playhead tag would half cover is skipped whole (`tag_rect()`).
- **Transport row (Simple):** the "Frames a–b" caption is Advanced-only, the pan scrollbar shows
  once the view is zoomed in (always in Advanced), the root "Main scene" crumb is hidden in neon
  Simple (shown inside a sequence and in Advanced), and the toolbar buttons (Sequences…) are ghost
  buttons. The Frame field, Sequences… and − + Fit stay visible.
- **Focus lane:** the scroll-to-lane step runs again after the Simple / Advanced switch and when the
  lane area resizes, and it measures the part of the lanes the dock's own scroll actually shows, so
  Advanced at 1440x900 shows the Ink lane being drawn on.
- **Inspector:** "Brush opacity (%)" sits above its row (Advanced). Stroke smoothing has the Opacity
  treatment (label, neon slider, flat "N px" value; same SpinBox, still Advanced-only). The Layer
  switch reads "Show" (tooltip "Show this layer"). Advanced recovery status has a 12 px right inset.
- **World rail (Simple):** Save asset and Size map are 40 px icon-only tiles under Frame (names in
  the tooltip; button texts and visibility unchanged). Advanced shows their captions.
- **Pose:** `model_keyed()` caches key frames by model data identity (no per-frame deep copy).
- **Declined:** the full-height World rail beside the timeline (dock tree nesting and saved-layout
  shape, items 8 / 18). Collapsing Pose's Keys and helpers / Bones / Visibility / More behind one
  disclosure in Simple (item 15): Codex smokes require those controls visible in Simple (for example
  "motion control is available in Simple", the contacts lesson marker, shape_button). Hiding the
  Sequences toolbar and Frame field in Simple (item 17): they stay visible where Codex shows them.
- **Deviation kept (item 28):** Codex's simulation row (Physics, Hair & clothes, physics recording,
  fans / local wind, loose parts) is hidden in neon Simple unless a simulation or recording runs;
  Pose mirrors Physics / Hair & clothes. Recording, fans, wind and loose parts are reached in
  Advanced. Showing the row in Simple shrinks the frame and turns the tool pill icon-only.

### Review 3 fixes (`src/app.gd`, `src/workspace_layout.gd`, `src/timeline_view.gd`, `src/studio_theme.gd`, `src/pose_editor.gd`)

- **Full-height World rail (item 9, replaces the review 2 decline):** while World is docked alone on
  the left (neon), the same four splits nest as `horizontal[left, vertical[top_split[top, right_split],
  bottom]]`, so the 64 px rail runs from the header to the bottom and the timeline starts beside it
  (mock grid). Classic styles, World floating or sharing / leaving the left dock use Codex's nesting.
  The switch runs only on docking / theme changes (`apply_nesting()`, checked in `_process` while no
  heading drag runs), never on a divider drag; split roles and `state()` / saved layouts are unchanged.
- **Inspector:** New drawing's top hairline shows only under the Next card (one 1 px line). A thin
  4 px inspector scrollbar; while it shows, every inspector section and card gives up its width on
  the right (`fit_inspector_pad()`), keeping 16 px of visual padding. Colour keeps the 8 px block gap
  and the Brush size heading is 20 px. Help / Next cards have 12 px side padding (the substitute UI
  font is ~6% wider than Geist, so "How camera keys work" wraps to two lines as in the mock).
  Switch rows trim long labels with an ellipsis (full text in the tooltip), so no control widens the
  288 px column; Pose's switch reads "Reference only" with the sub-line "Hidden in the movie" (classic
  keeps Codex's wording). Advanced Brush card: the three sliders share one column (lead / end slots),
  the short bold labels are Simple-only (Codex's captions label them in Advanced).
- **Stage footer:** neon Simple Camera toast "Move the view, then save a key. Press Save camera key
  [K] to keep it." (one line, bold first sentence; classic and Advanced keep Codex's text); the caption
  reserve is 210 px so "Camera view · 16:9 · 35 mm" is not cut. While Codex's pill sits in the footer
  it drops the dropdown chevrons, uses 30 px chips and a 2 px gap (`set_codex_footer()`), so Pose keeps
  the "Handles" legend title at 1440x900; fit decisions measure the pill in its normal look.
- **Timeline:** content gets a 12 px right pad matching the left (`content_width()`), so the last
  key is whole; the focus-lane scroll snaps to a lane boundary (no sliver of the row above); the
  Camera lane reads "N keys" in Camera mode and its track band is the mock's faint 0.07 → 0.02 pink
  with no edge; Advanced lanes minimum is 30 px so the docked 166 px timeline never engages the dock's
  own scroll (one scrollbar).
- **Theme:** neon scrollbar thumbs `#5C6272` (3.2:1 on `#0C0D11`), hover `#8C93A3`, pressed `#B4BAC7`.
  The Draw/Camera/Pose underline glow is a soft violet (9 px) over faint blue (10 px).
- **Behaviour fixes:** strip_input ignores the Home overlay and exports and tests the cheap strip
  rects before the dialog walk (nested DockSplits only on a press); the Advanced FOV slider follows
  `fov.set_value_no_signal`; Fit view is back in Simple (see above); Turn model selects the root row
  of the Bones tree; the tool pill's Pick color / Select area take the I / M `arm()` path; tool pill
  tooltips follow rebound shortcuts; the Camera key list rebuilds only when a cheap token changes;
  Simple Physics mirrors copy Codex's live tooltips.
- **Declined:** `TimelineView.LEFT = 200` (item 10): LEFT is test-visible API documented as 190,
  `sequence_timeline.gd` hard-codes 190 and the change would also move the classic timeline.
  Asymmetric `fit_inset` (item 18): the 3D view renders a centred perspective camera, so an off-centre
  frame would misalign drawings with the scene (and scene_view's setup camera math).

## Neon pro theme (summary for Codex, 2026-11-16)
This section sums up the finished Neon Pro port. The step and review sections above have the details.
The owner approved the "neon pro" mock: the Iridescent Pro layout with the Midnight Neon theme. Simple
mode follows the mock ("Simplicity is key"). Advanced keeps every control, restyled with the same tokens.
Project data, renders, saves and undo are unchanged; this is presentation only. Nothing under `tests/` was edited.

### Screenshots: mock vs app (1440x900, Linux xvfb, opengl3)
| | Mock (approved) | App on this branch |
|---|---|---|
| Simple Draw (the main reference) | `docs/redesign-mock/mock-draw.png` | `docs/redesign-mock/app-draw.png` |
| Simple Camera | `docs/redesign-mock/mock-camera.png` | `docs/redesign-mock/app-camera.png` |
| Simple Pose | `docs/redesign-mock/mock-pose.png` | `docs/redesign-mock/app-pose.png` |
| Advanced Draw | (not in the mock) | `docs/redesign-mock/app-advanced.png` |

The app shots show a 2-bone fixture model (`rig.glb`), the demo room, one painted stroke and a
sample status message. The project name and save state are real ("Untitled", "Unsaved changes"),
not the mock's sample data.

### What changed
- **Theme:** a new default `"neon"` style next to the classic `"light"` and `"dark"` skins. Settings
  (Advanced part) has an "Interface theme" dropdown (Midnight Neon / Classic light / Classic dark),
  saved as `[display] theme` in `user://display.cfg`. A switch to or from neon applies at the next start.
- **Header:** one 56 px bar with the brand mark, project name and save line, New / Open / Save / Add,
  centred Draw / Camera / Pose tabs with a neon underline, the Advanced switch, More, and the neon
  Export movie button. Advanced adds a second row with every original button.
- **World rail:** a 64 px rail of labelled icon tiles for the World rows, with the Frame, Save asset
  and Size map tiles at the bottom. While World is docked alone on the left it runs full height,
  and the timeline sits beside it.
- **Stage:** the canvas fills the stage. The tool pill, view badges, viewfinder corners, the stage
  footer (caption, toast with a progress strip, legend) and Codex's view controls float over it.
- **Inspector:** card-based Draw (tool card, colour, brush, layer, next step, new drawing), Camera
  (keys, lens, guides, save) and Pose (motion, next step, actions, keys and helpers) panels. Codex's
  extra controls stay below the cards.
- **Timeline:** a compact transport row (play ring, mono time, Frame field, Sequences…, zoom) and
  neon lanes: blue drawings, pink camera keys, violet model keys, and a gradient playhead tag.
- **Secondary surfaces:** home screen, dialogs, popups, dock tree, movement path editor, sequence
  timeline and the reference sheet follow the tokens through `StudioTheme.tone()` and `surface()`.

### File / function map
| File | Neon work |
|---|---|
| `src/studio_theme.gd` (LF) | tokens, `set_style()`/`is_neon()`, `tone()`, `flat()`, `neon_ring()`, `neon_fill()`, `neon_line()`, `neon_bar()`, `brand_mark()`, `diamond()`, `key_glow()`, `toast_ring()`, `play_ring()`, `focus_box()`, `switch_icon()`, `check_icon()`, `slider_styles()`, `font()`/`mono()`, `make_neon_theme()` (type variations `GhostButton`, `PrimaryButton`, `NeonButton`, `TabButton`, `RailTile`, `ToolButton`, `RailLabel`, `CaptionLabel`, `MonoLabel`, `KbdLabel`), `LINE_ICONS` + `line_icon()`/`icon()`, `CLASSIC_ALIASES` |
| `src/app.gd` (CRLF) | theme switch: `apply_theme_style()`, `back_gradient()`, `apply_header_style()`; header: `style_header()`, `style_tab()`, `refresh_mode_tabs()`, `style_export()`, `fit_header()`; stage: `view_pill()`, `refresh_tool_strip()`, `refresh_view_row()`, `fit_view_row()`, `set_codex_compact()`, `set_codex_footer()`, `build_view_badges()`, `refresh_badges()`, `draw_viewfinder()`, `build_stage_footer()`, `fit_stage_inset()`, `fit_stage_footer()`, `refresh_toast()`, `draw_toast_strip()`; inspector: `build_draw_inspector()`/`refresh_draw_inspector()`, `build_camera_inspector()`/`refresh_camera_inspector()`, `inspector_block()`, `inspector_card()`, `fit_inspector_pad()`; timeline: `transport_block()`, `style_transport()`, `compact_timeline_rows()`, `sync_timeline_focus()`; footer: `style_app_footer()`, `draw_app_footer()` |
| `src/workspace_layout.gd` (LF) | dock headers and Simple grab strips (`style_header()`, `strip_header()`, `strip_input()`, `draw_header()`, `draw_panel()`), full-height rail nesting (`want_full_left()`, `apply_nesting()`) |
| `src/world_selection.gd` (CRLF) | World rail tiles: `rebuild_rail()`, `sync_rail()`, `entity_tile()`, `style_tile()`, `style_action()` |
| `src/timeline_view.gd` (CRLF) | neon lanes: `neon_draw()`, `neon_lane()`, `neon_band()`, `neon_keys()`, `neon_diamond()`, `neon_ticks()`, `neon_playhead()`, `neon_tag()`, `content_pad()`/`content_width()` (12 px pad; `x()` and `frame_at()` stay inverse) |
| `src/pose_editor.gd` (LF) | Pose inspector: `build_neon_inspector()`, `refresh_neon_inspector()`, `neon_block()`, `neon_switch()`, `neon_segmented()`, `next_step()`, `model_keyed()` |
| `src/canvas_view.gd` (CRLF) | `fit_inset` (neon only, zero in classic and unit tests), `fit_area()`, `setup_frame_size()`, `refresh_surround()` |
| `src/scene_view.gd` | compact Guides menu (`guides_button`), `copy_camera(..., frame_size)` overscan for the inset frame |
| `src/timeline_navigation.gd`, `src/dock_tree.gd`, `src/sequence_timeline.gd`, `src/sequence_editor.gd`, `src/movement_path_*.gd`, `src/reference_sheet_view.gd`, `src/home_screen.gd` | small restyles (`apply_neon_style()`, `style_book()`, tokens) |

### Theme tokens (all in `src/studio_theme.gd`, constants at the top)
| Token | Value | Use |
|---|---|---|
| `BG` / `STAGE` | `#08090C` / `#05060A` | app background / canvas surround |
| `BAR` / `PANEL` / `RAISE` / `HOVER` | `#0C0D11` / `#111318` / `#171A21` / `#1D2029` | bars and docks / cards / raised rows / hover |
| `LINE` / `LINE2` / `LINE3` | `#22252E` / `#2C303B` / `#363B48` | hairlines / outlines / hover outlines |
| `TEXT` / `TEXT2` / `TEXT3` | `#F4F6FA` / `#B4BAC7` / `#8C93A3` | primary / secondary / muted text |
| `BLUE` / `MID` / `PINK` / `FOCUS` | `#2E8CFF` / `#9C5CFF` / `#FF3D9A` / `#7B5CFF` | neon gradient ends and middle / focus ring |
| `ON_NEON` | `#07080B` | text on the neon fill |
| `FIELD`, `POPUP`, `KBD`, `TOOL_INNER`, `SWITCH_INNER`, `TRACK`, `SCROLL_THUMB` | see the file | field, popup, keycap, ring interiors, slider track, scrollbar thumb |
| `DRAWING` / `CAMERA` / `MODEL` | `#4DA3FF` / `#FF5FAE` / `#A98BFF` | drawings and onion "before" / camera keys and onion "after" / model keys |
| `SAVED` / `PROBLEM` / `WARNING` | `#3DDC97` / `#FF5A7A` / `#FFC24B` | save dot / problem toast / unsaved dot |
| `NEON_STOPS` | `#2E8CFF 0, #8079FF .25, #B565F8 .5, #DF51D2 .75, #FF3D9A 1` | the mock's oklch gradient as sRGB stops |
| `UI_FONTS` / `MONO_FONTS` | SystemFont fallback lists | see "Known deviations" |

Contrast: TEXT3 is at least 4.97:1 on every surface it is used on, TEXT2 at least 7.9:1, TEXT at least
14:1, and `ON_NEON` on the neon fill at least 5.8:1.

### Godot equivalents of the mock's CSS
| Mock CSS | Godot |
|---|---|
| `linear-gradient(in oklch …, #2E8CFF, #FF3D9A)` | SVG `linearGradient` with the five `NEON_STOPS` (`neon_defs()`). SVG cannot interpolate in oklch |
| gradient border (`padding-box` fill + `border-box` gradient) | `neon_ring()`: `StyleBoxTexture` from an in-code SVG rect with a gradient stroke, rendered at 2x (`ImageTexture.set_size_override`), so 1.5 px rings stay crisp while margins stay logical |
| full neon fill (Export, playhead tag, brand mark) | `neon_fill()`, `neon_tag()`, `brand_mark()`, with `ON_NEON` text |
| `box-shadow` glow | `StyleBoxFlat.shadow_color/size/offset` (one colour per box). Two-colour glows use two stacked panels: Export movie has a pink 6 px shadow on a panel inset 6 px over a fainter blue one inset 8 px, and the Draw / Camera / Pose underline has a soft violet glow over a faint blue one. Negative spread becomes a smaller `shadow_size` |
| radial glows (switch knob, key glow, toast ring) | radial gradients drawn inside the SVG icon (`switch_icon()`, `key_glow()`, `toast_ring()`) |
| `inset 0 0 0 1px` | 1 px `StyleBoxFlat` border (`flat()`) |
| focus ring | `focus_box()`: no fill, 2 px `FOCUS` border, `expand_margin` 2, pink shadow |
| `position:absolute` overlays (tabs, tool pill, badges, footer) | full-rect overlay Controls with `MOUSE_FILTER_IGNORE`; only the pills and buttons take the mouse |
| uppercase + `letter-spacing` | `FontVariation.spacing_glyph` (`RailLabel`, dock headers), text written in capitals |
| `tabular-nums` | the mono SystemFont (`MonoLabel`) |
| out-of-frame dim and viewfinder corners | `draw_rect` / `draw_polyline` in `_draw()` (`draw_viewfinder()`), editor-only, never rendered |
| `rotate(45deg)` diamonds | `diamond()` SVG / `draw_colored_polygon` in the timeline |
| toast progress bar | `draw_toast_strip()`, which follows the existing 6 s status fade (the status text is never cleared) |
| hover transitions | instant hover styleboxes (no tweens) |

### Known deviations from the mock
- **Fonts:** Geist / Geist Mono are not bundled and fonts may not be downloaded. The `SystemFont`
  lists fall back to Inter + JetBrains Mono on the Linux test box, and usually to Segoe UI + Cascadia
  Mono or Consolas on Windows. Text is about 6% wider than in the mock.
- **Codex controls kept visible in Simple:** the lighting dropdown, Frame scene, Undo / Redo, Scene
  setup / Guides, Fit view, the Frame field, Sequences…, zoom, Save asset / Size map tiles, Keys and
  helpers / Bones / Visibility in Pose, and "More drawing options". They are compacted (icon chips,
  the footer pill) instead of hidden.
- **Simulation row:** hidden in neon Simple unless a simulation or recording runs. Pose mirrors the
  Physics and Hair & clothes switches. Recording, fans, wind and loose parts are reached in Advanced.
- **Sample data not faked:** the project name, save time, rail items, clip names, camera key
  thumbnails (placeholder tiles), "next step" text and shortcut labels come from the real project.
- **Left for the owner to decide:** the Bend / Twist joint sliders, a Simple field-of-view slider, and
  new pose behaviour behind "Physics follow-through" (it mirrors Codex's Hair & clothes switch).
- **Dock headers:** in Simple they are 10 px grab strips, not hidden, because docking needs a drag handle.
  Advanced and floating docks keep the 28 px headers.
- **Declined:** `TimelineView.LEFT = 200` (test-visible API) and an off-centre `fit_inset` (it would
  misalign drawings with the centred 3D camera). Each glow is limited to one shadow colour per box.
- **Text selection colour:** pale blue `#B9D7FF`, because `workspace_controls_smoke` checks the
  selected-text colour.

### How to test (Linux)
```
GODOT=/path/to/Godot_v4.6-stable_linux.x86_64 tools/linux/run_test.sh . ui
# also: editor, pose, world_selection, recovery_write, recovery (1-5 min each)
git checkout -- tests tools/__pycache__   # the tests rewrite these committed files
```
The UI-sensitive Codex smokes that `run_test.sh` does not cover were run with the same
xvfb/opengl3 command line: `godot --rendering-driver opengl3 --audio-driver Dummy --path . --script
tests/<name>.gd -- output/extra-<name>` for `workspace_controls_smoke`, `workspace_docking_smoke`,
`asset_package_smoke`, `brush_opacity_smoke`, `palette_smoke`, `layers_smoke`, `onion_smoke` and
`color_sampler_smoke`, comparing the FAIL count with main. That wrapper is not committed because
these smokes rewrite `tools/__pycache__`. `color_sampler_smoke` has 3 failures on main on this
Linux box too. `camera_range_smoke` and `lighting_smoke` need fixtures from `tests/verify_*.py`.

### Screenshot tool (`tools/linux/shoot.sh` + `tools/linux/shoot.gd`)
```
GODOT=/path/to/Godot_v4.6-stable_linux.x86_64 tools/linux/shoot.sh output/shots   # from the repo root
```
- It runs the app under `xvfb-run` with `--rendering-driver opengl3 --resolution 1440x900` and the
  helper `shoot.gd` through an absolute `--script` path, with the user args
  `--demo-room --shoot-out <dir>`.
- The helper hides Home, adds a 2-bone fixture model (`SHOOT_MODEL=0` skips it), paints one stroke
  and posts a sample status message. It saves `draw.png`, `camera.png`, `pose.png` (Simple) and
  `advanced.png` (Advanced Draw), plus `shoot.log`. A run takes about 7 s.
- It never touches prefs. `XDG_DATA_HOME`, `XDG_CONFIG_HOME` and `XDG_CACHE_HOME` point at a
  `mktemp` directory that is deleted afterwards. `app.display_prefs_path` and `recovery_root` point
  into `output/neon-shoot/` (git-ignored), and because `--script` is on the command line, the workspace
  layout goes to `output/test-preferences/`. `git status` stays clean after a run.
- To refresh the docs images: run it, then copy the four PNGs to `docs/redesign-mock/app-*.png`.

## Windows review — November 16, 2026

The owner requested this review before merging. Original branch commit
`c2d52ff5fd0f9aeffae6a343f6d4b71698ed9ff2` was tested on Windows with the approved
Godot4.6/private-desktop runner. The first complete verifier stopped at object
timing:28 checks,2 failures. Its old input scrolled to the end of all lanes,
putting the last model above the new62px track viewport. The successor reveals
the requested model row by its geometry; every original assertion remains.
The failed run, unchanged source map and24 physically closed jobs are retained.

Source review and real input checks found and corrected four regressions:
idle Simple simulation tools were hidden; unmodified F11 overrode a saved user
shortcut; a faded toast intercepted canvas clicks; the timeline cache retained
deleted/prior-project model dictionaries. The original focused probe executed
32 checks with13 failures. Corrections preserve the neon look and restore the
existing Simple simulation strip, including fan/loose-parts/wind/recording access.
Assigned F11 has priority; unassigned F11 still toggles fullscreen. Faded toast
input is ignored without clearing status text. Cache entries are bounded to live rows.

World's icon rail is now limited to its supported solitary left placement.
Right, nested, tabbed and floating placements retain the full hierarchy list.
The narrow-right/nested/floating/persisted-layout regression passes45 checks.
Inset camera mapping passes12384 checks across576 configurations, with maximum
projection error0.000790571px and ray error2.25e-7. Compact first/middle/last model
clicks with drawing/audio lanes below them pass14 checks. The corrected existing
Windows UI smoke passes23 checks and preserves Simple/Advanced render identity.

The final32-check behavior probe passes. Two intermediate32/1 fixture results
and a diagnostic are preserved: a successful empty-scene click publishes a NEW
Camera hint, and a later click can publish another. The final test measures
refresh's faded-message state before the click, then independently requires the
actual canvas event; it never waits after refresh to mask a resurrection.

The strict wind manifest updates only the reviewed app/pose hash rows. Its
16-file scope,14 other rows and original94/845 predicates remain unchanged.
The standard verifier gains one guarded `neon_workspace` group with all four
regressions (12475 checks). Existing36 core entries remain unchanged.

This is a reviewed candidate, not yet merged. The fresh complete corrected
Windows verifier remains the final gate. Original native fixtures and earlier
review builds are protected; no human acceptance result is inferred.

### Windows focused fixture follow-up (November17UTC)

The381 complete verifier stopped at animated native channels47/1; all1028
functional files stayed unchanged. Root audited27 closed private jobs and the
exact coordinator/Python birth identities, then released only the failed lease.
Its raw failure and all three executed MMD/GMod/SFM fixtures remain recorded.

The native-channel successor scrolls the requested channel into view and adds
a pre-click visibility assertion. All original assertions remain;48/0 passes
with all three native rigs. Older standalone movement fixtures also assumed
lower channels were already visible and used a stale eager cel.image field.
Those original errors are retained. Revealing each channel and using the current
mutable drawing accessor passes both legacy/component profiles:34UI+13unit each.
The Drawing API and original test were already identical in main52f; this was
preexisting focused fixture code, not a new production Drawing change.

Waveform checks reveal Audio before pixel capture and keep Classic467d45,
four transients and RGB tolerance.02. A first Neon palette expectation failed
14/1 because a fractional clip border is antialiased, rather than opaque.
Diagnostic-only output preserved every predicate and identified the unmatched
first transient. The source-derived Godot4.6 straight-edge feather expectation
uses live geometry, with explicit unscaled/non-HDR/non-MSAA/raster guards.
Both Neon and Classic now pass15/0, four visible bars; all13 original checks
remain and bounds/raster guards add2. No expected color was taken from pixels,
no tolerance/count was widened, and production colors/layout did not change.

These focused results do not replace a complete default. The next frozen commit
must run all158groups before merge; manual owner review remains deferred.


## Windows review follow-up — 2026-11-17

The strict Windows workspace checks exposed a live Tree font replacement error.
Retaining the original Neon/classic SystemFont profiles in StudioTheme.fonts
fixes it without changing font family, weight or Japanese fallback. Lifecycle
guards reject styling detached/queued controls and reconnect World resize once
on reentry. A separate mode-acceptance fix commits the layout cache only after
the World presentation applies; one deferred refresh finishes World detachment.
This preserves full lists in floating/right/nested/tabbed World arrangements.

Actual private Windows verification now passes workspace controls48, integrated
Neon12504 (inset12384, behavior32, compact14, rail45, lifecycle29), resize, docking
and nested layouts. Source1029 is unchanged within the run; physical desktops
close and root scope observations are empty. The new lifecycle fixture preserves
all29 predicates; six explicit WeakRef types resolve parser warnings. Inset and
Compact reuse the same full-precision JSON string for file and log, preserving
all numeric checks and strict equality. Original failures and the incorrect
concat-stream teardown attribution are retained and corrected in main evidence.

The complete Windows default still needs a fresh successful run before merge.
Prior f387 full passed36 core groups then failed strict workspace diagnostics.
No owner observation, native-normal repair, PMX solver or new scale basis follows
from these UI checks. All earlier owner reviews and installed Studio are preserved.


## Windows scene-presentation fixture — 2026-11-17

The unchanged fullffcf run stopped at scene-view102/4 because the approved Neon
mask dims off-frame colors62percent. The source-pinned successor preserves all
102 original semantic predicates and their thresholds, recovers underlying color
analytically, and adds four independent raw-viewport/composited-screen checks
under an explicit Compatibility/LDR/opaque/identity-transform profile. The fixed
2/255 bound follows two8-bit writes; no expected value is fitted to observed
pixels. Product code and the approved look are unchanged. Actual Windows wrapper
now passes106/0 plus its headless unit case, all4 profiles/composites valid, source
1029 preserved and private jobs/scopes closed. Original102/4 evidence is retained.
The next complete default run remains unrun; no full PASS or merge is claimed.

## Windows helper preview source manifest — 2026-11-17

The4ed complete Windows run passed36core,Neon12504,scene106+unit12830 and
subsequent readback/fan/wind stages, then stopped03:19:31Z at the helper-preview
CPU source gate. Its old manifest rejected reviewed app.gd before snapshot or
helper engine/worker/graphical launch, with0checks. Root closed49physical jobs
(48exit0+registeredKrita cancel2), exact inline/source1029/birth/scope checks and
released03:19:55Z. No full PASS or merge is claimed. The minimal manifest refresh
changes only app/pose exact+LF hash strings to the reviewed Neon bytes, already
pinned in the wind manifest. Membership25,23other rows and driver/208CPU/266GPU
predicates are unchanged. Source-only18tamper tests and independent peer18 pass;
fresh actual helper profiles and another complete default are still required.

## Windows authored bone fixture line endings — 2026-11-17

The375 complete default passed helper208CPU/266graphical and later snapshot/editing
stages, then failed the authored bone fixture40/40 at base64 decoding. Its canonical
Git/main52 source was identical, but the working CRLF literal retained103CRs after
LF-only stripping. The fixture-only successor removes CR andLF before decoding;
9360-byte golden39637fa3 and9364-byte malformed95e0c878 remain exact. One expression
changes; all79+17predicates/wrapper/timeouts/error policy remain. Source10CPU methods
and independent10 pass; actual Foundation167/separate77+96 and full successor are
still required. Root closed51private jobs50exit0+Krita2 and separate headless exit1,
source1029 unchanged, released03:51:37Z. No product change/fullPASS/merge is claimed.
