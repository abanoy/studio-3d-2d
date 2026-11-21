extends Control
const DrawingLimits=preload("res://src/drawing_limits.gd")
signal movie_export_finished(folder: String,success: bool)
signal startup_recovery_finished(result: Dictionary)
signal camera_cursor_return_requested(position: Vector2)
const Timeline = preload("res://src/timeline.gd")
const Drawing = preload("res://src/drawing.gd")
const PixelHistory=preload("res://src/cel_pixel_history.gd")
const CelPatch=preload("res://src/cel_patch.gd")
const FillEditor=preload("res://src/fill_editor.gd")
const OnionEditor=preload("res://src/onion_editor.gd")
const LayerEditor=preload("res://src/layer_editor.gd")
const ColorSampler=preload("res://src/color_sampler.gd")
const SceneIO = preload("res://src/scene3d.gd")
const Renderer = preload("res://src/renderer.gd")
const Storage = preload("res://src/storage.gd")
const Encoder = preload("res://src/encoder.gd")
const OutputSize=preload("res://src/output_size.gd")
const CanvasView = preload("res://src/canvas_view.gd")
const HomeScreen=preload("res://src/home_screen.gd")
const Tutorials=preload("res://src/tutorials.gd")
const TimelineView = preload("res://src/timeline_view.gd")
const ClipEditor=preload("res://src/clip_editor.gd")
const ObjectTiming = preload("res://src/object_timing.gd")
const AudioTrack = preload("res://src/audio_track.gd")
const StudioTheme = preload("res://src/studio_theme.gd")
const Recovery = preload("res://src/recovery.gd")
const RecoveryJournal=preload("res://src/recovery_journal.gd")
const RecoveryPreview=preload("res://src/recovery_preview.gd")
const RecoveryWriter=preload("res://src/recovery_writer.gd")
const PoseEditor = preload("res://src/pose_editor.gd")
const PhysicsEditor=preload("res://src/physics_editor.gd")
const ImportPlacement = preload("res://src/import_placement.gd")
const ImportBasis = preload("res://src/import_basis.gd")
const SourceShape=preload("res://src/source_shape.gd")
const ImportActions = preload("res://src/import_actions.gd")
const SourceImport = preload("res://src/source_import.gd")
const SourceBrowser = preload("res://src/source_browser.gd")
const HasProject = preload("res://src/has_project.gd")
const WorldSelection = preload("res://src/world_selection.gd")
const WorldDocument = preload("res://src/world_document.gd")
var world_selection
var character_parts_editor: Node
var particle_editor: Node
var has_project
var video := {"width": 1920, "height": 1080, "fps_num": 24, "fps_den": 1, "duration_frames": 48,"visibility_fade_ms":300}
var keys: Array = []
var layers: Array = []
var palette: Array=[]
var palette_editor: Node
var source := ""
var last_import_id := ""
var project_folder := ""
var frame := 0
var active_layer := 1
var playing := false
var play_origin := 0
var play_start := 0
var drawing := false
var navigating := false
var camera_buttons := 0
var camera_free := false
var camera_cursor_origin := Vector2.ZERO
var camera_cursor_restore_pending := false
var navigation_scheme:="fly"
var orbit_control=preload("res://src/orbit_navigation.gd").new()
var navigation_choices: OptionButton
var previous_point := Vector2.ZERO
var stroke_image: Image
var before_tiles := {}
var active_brush: RefCounted
var stroke_stabilizer: RefCounted
var previous_pressure:=-1.0
var stroke_accumulated_input:=true
var history: Array = []
var redo_history: Array = []
var history_bytes := 0
var dirty := false
var raster_budget=preload("res://src/cel_raster_budget.gd").new()
var raster_budget_due:=0
var cold_cel_loading:=true
var cold_cel_min_bytes:=64*1024*1024 # Preserve eager small-project latency.
var raster_preview_error:=""
var drawing_overlay_cache=preload("res://src/drawing_overlay_cache.gd").new()
var overlay_dirty := true
var exporting := false
var cancel_export := false
var encoder: RefCounted
var renderer: Node
var canvas: Control
var cel_timing: Node
var cel_clipboard: Node
var timeline_navigation: Node
var timeline_ruler: Control
var timeline: Control
var camera_key_editor: Node
var mode: OptionButton
var lighting_choice: OptionButton
var tool: OptionButton
var fill_editor
var onion_editor
var reference_sheet
var layer_editor
var color_sampler
var drawing_selection_editor
var color: ColorPickerButton
var radius: SpinBox
var brush_opacity: SpinBox
var brush_pressure: CheckButton
var brush_smoothing: SpinBox
var fov: SpinBox
var camera_near: SpinBox
var camera_far: SpinBox
var interpolation: OptionButton
var layer_choice: OptionButton
var layer_visibility: CheckButton
var exposure: SpinBox
var frame_box: SpinBox
var status: Label
var debug_label: Label
var transport_info: Label
var transport_time: Label # Neon Pro step 6: mono "S.SS" readout (neon style only)
var timeline_key_cache := {}
var encoder_path: LineEdit
var encoder_quality: OptionButton
var output_size: OptionButton
var cancel_button: Button
var controls: VBoxContainer
var elapsed_overlay_ms := 0.0
var last_export_folder := ""
var png_drawing_only: CheckButton
var last_finished_movie := ""
var movie_folder_button: Button
var saved_frames_button: Button
var interrupted_frames_folder: String=""
var retry_encode_button: Button
var retry_render: Dictionary={}
var audio_clips: Array = []
var selected_audio := 0
# Existing single-clip callers still address the selected clip. Whole-project
# writers/Undo always use audio_document(), never this editing selection.
var audio_clip: Dictionary:
	get:
		return audio_clips[clampi(selected_audio,0,audio_clips.size()-1)] if not audio_clips.is_empty() else {}
	set(value):
		audio_clips = AudioTrack.clips(value)
		selected_audio = 0
var audio_mix := {}
var audio_player: AudioStreamPlayer
var audio_clock := false
var last_audio_time := 0.0
var preview_sample_seconds := 0.0 # Clock used for the latest processed preview frame.
var audio_latency := 0.0
var audio_info: Label
var audio_start: SpinBox
var audio_trim: SpinBox
var audio_gain: SpinBox
var audio_mute: CheckButton
var audio_solo: CheckButton
var audio_choice: OptionButton
var advanced_mode := false
var advanced_toggle: Button
var advanced_controls: Array[Control] = []
# Redesign (Simple/Advanced): Simple-only shortcuts to Advanced controls; see docs/REDESIGN-PORT.md.
var simple_controls: Array[Control] = []
var mode_tabs: Array[Button] = []
var tool_strip: HBoxContainer
var tool_buttons: Array[Button] = []
var camera_strip: HBoxContainer
var physics_bar: Control
var undo_button: Button
var title_label: Label
var back_texture: TextureRect
var keyboard_nav := false
var keyboard_focusable: Array = []
var status_serial := 0
var status_faded := false
var timeline_focus_key := "" # the Simple toast faded this message (status.text itself is kept)
const POSE_HINT := "Drag a joint to pose. Changes are keyed automatically."
var empty_hint: PanelContainer
var empty_hint_label: Label
var redo_button: Button
var drawing_section: VBoxContainer
var new_drawing_button: Button
var copy_drawing_button: Button
var exposure_button: Button
var delete_cel_button: Button
var camera_section: VBoxContainer
var audio_section: VBoxContainer
var workspace_label: Label
var scene_name: Label
var play_button: Button
var inspector_scroll: ScrollContainer
var recovery_root := ""
var recovery_session := ""
var recovery_revision := 0
var checkpoint_revision := -1
var checkpoint_lesson_signature := ""
var autosave_due := 0
var autosave_enabled: CheckButton
var autosave_interval: SpinBox
var autosave_schedule: OptionButton
var autosave_action_limit: SpinBox
var autosave_time_controls: VBoxContainer
var autosave_action_controls: VBoxContainer
var autosave_actions := 0
var autosave_retry_due := 0
var recovery_status: Label
var app_footer: HBoxContainer # Neon Pro step 9: export / recovery row under the workspace
var last_recovery_ms := 0.0
var last_recovery_preview_ms := 0.0
var last_recovery_preview_capture_ms := 0.0
var last_recovery_preview_worker_ms := 0.0
var recovery_writer=RecoveryWriter.new()
var recovery_writer_result: Dictionary={}
var recovery_schedule_generation:=0
var last_recovery_capture_ms:=0.0
var last_recovery_worker_ms:=0.0
var recovery_preview=RecoveryPreview.new()
var recovery_preview_result: Dictionary={}
var recovery_native_requests: Array=[]
var recovery_checkpoint_requested:=false
var recovered_from := ""
var startup_recovery_result: Dictionary={}
var open_project_error := ""
var pose_editor: Node
var mmd_pose_importer: Node
var audio_importer: Node
var raster_importer: Node
var video_importer: Node
var sequence_editor: Node
var audio_trim_editor: Node
var audio_fade_editor: Node
var physics_editor: Node
var local_wind_review: Node
var local_wind_generation:=0
var helper_preview_runtime_path:=""
var helper_preview_work_root:=""
var source_import: Node
var source_browser: Node
var clip_editor: Node
var import_actions: Node
var height_review: Node
var map_calibration: Node
var height_choice: CheckBox
var project_options: AcceptDialog
var project_timing: Node
var project_canvas: Node
var workspace_layout: Node
var home
var recent_path:=""
var tutorials
var visibility_fade: SpinBox
const DISPLAY_PREFS := "user://display.cfg"
var display_prefs_path:=DISPLAY_PREFS
const UI_PERCENT := [100,125,150,175]
var display_dialog: AcceptDialog
var header_box: StyleBoxTexture
# Neon Pro step 2: header bar parts (see build_ui, fit_header, refresh_title).
var header_row: HBoxContainer
var header_spacer: Control
var header_tabs: HBoxContainer
var header_tab_overlay: CenterContainer
var header_tab_frame: PanelContainer
var header_project: VBoxContainer
var header_mark: TextureRect
var header_compact: Array[Button] = []
var header_level := -1
var header_saved_at := -1
var header_identity := "" # project shown in the bar; a change forgets the last save time
var header_was_dirty := false
var header_dots := {}
var save_dot: Panel
var save_label: Label
var export_button: Button
var export_chip: Label
var keyboard_shortcuts: Node
var camera_transform_editor: Node
var scene_view: Node
# Neon Pro step 4: viewport overlays (stage, tool pill, badges, viewfinder, stage footer, toast).
var stage_panel: PanelContainer
var stage_overlay: Control # neon: view rows, physics row and stage footer float over the canvas
var stage_top: VBoxContainer
var stage_inset_pending := false
var stage_view_margin: MarginContainer
var view_scroll: ScrollContainer
var view_row: HBoxContainer
var view_row2: HBoxContainer
var view_spacer: Control
var view_spacer2: Control
var view_fit_pending := false
var tool_pill: PanelContainer
var camera_pill: PanelContainer
var pose_pill: PanelContainer
var codex_pill: PanelContainer
var pose_strip: HBoxContainer
var pose_buttons: Array[Button] = []
var turn_button: Button # Simple Pose pill: Rotate with the model root selected
var frame_scene_button: Button
var fit_view_button: Button
var codex_compact := false
var footer_tools: HBoxContainer # neon Simple: the Codex view pill when it does not fit the view row
var tool_compact := false
var camera_hint: Control
var camera_help_button: Button
var pose_help_button: Button
var camera_help_label: Label
var camera_key_button: Button  # "Save camera key [K]" in the Camera panel
var camera_delete_button: Button
var camera_hint_label: Label
var help_popup: PopupPanel
var help_popup_title: Label
var help_popup_body: Label
var badges: HBoxContainer
var frame_badge_frame: Label
var frame_badge_time: Label
var mode_badge_lead: Label
var mode_badge_chip: Panel
var mode_badge_diamond: TextureRect
var mode_badge_value: Label
var mode_badge_key := ""
var viewfinder: Control
var stage_footer: Control
var footer_left: HBoxContainer
var view_caption: Label
var toast: PanelContainer
var toast_icon: TextureRect
var toast_lead: Label
var toast_rest: Label
var toast_progress := 0.0
var toast_tween: Tween
var toast_strip: Texture2D
var legend: HBoxContainer
var legend_title: Label
var legend_items: Array = []
var legend_key := ""
var legend_wanted := false

func initialize_display() -> void:
	var prefs := ConfigFile.new()
	if OS.has_feature("web"):
		resize_web_display()
		get_window().size_changed.connect(resize_web_display)
	else:
		# Desktop zoom is explicit: resizing a window must not magnify a 1400x900 UI.
		get_window().content_scale_size=Vector2i.ZERO
	var percent := 100
	# Neon Pro port: [display] theme = neon (default) / light / dark. Older files only have
	# dark=true for the classic dark skin. Reading never writes the file.
	var theme_style := "neon"
	if prefs.load(display_prefs_path)==OK:
		var saved = prefs.get_value("display","percent",percent)
		if saved in UI_PERCENT: percent = int(saved)
		var saved_theme = prefs.get_value("display","theme","")
		if saved_theme in StudioTheme.STYLES: theme_style = saved_theme
		elif bool(prefs.get_value("display","dark",false)): theme_style = "dark"
		keyboard_nav = bool(prefs.get_value("display","keyboard_nav",false))
		var scheme=prefs.get_value("navigation","scheme","fly")
		if scheme in ["fly","orbit"]:navigation_scheme=scheme
	StudioTheme.set_style(theme_style)
	get_window().content_scale_factor = percent / 100.0

func save_display_preference(section_name: String,key_name: String,value) -> void:
	var prefs:=ConfigFile.new();prefs.load(display_prefs_path)
	prefs.set_value(section_name,key_name,value)
	if prefs.save(display_prefs_path)!=OK:message("Could not save the interface preference for next time.")

func toggle_fullscreen() -> void:
	# Redesign: F11 and Settings share one fullscreen toggle (editor window only; movies are unaffected).
	var full := DisplayServer.window_get_mode() in [DisplayServer.WINDOW_MODE_FULLSCREEN,DisplayServer.WINDOW_MODE_EXCLUSIVE_FULLSCREEN]
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED if full else DisplayServer.WINDOW_MODE_FULLSCREEN)

func back_gradient() -> Texture2D:
	if StudioTheme.is_neon(): return StudioTheme.svg_texture('<rect width="64" height="64" fill="%s"/>' % StudioTheme.hex(StudioTheme.BG), 64, 64)
	return StudioTheme.svg_texture('<defs><linearGradient id="back" x2="0" y2="1"><stop stop-color="#%s"/><stop offset="1" stop-color="#%s"/></linearGradient></defs><rect width="64" height="64" fill="url(#back)"/>' % [StudioTheme.tone_hex("f4f7fb"), StudioTheme.tone_hex("dce5ee")], 64, 64)

func header_texture() -> Texture2D:
	# Neon: flat #0C0D11 bar with a 1 px #22252E bottom hairline (kept unstretched by texture_margin_bottom).
	if StudioTheme.is_neon(): return StudioTheme.svg_texture('<rect width="64" height="64" fill="%s"/><rect y="63" width="64" height="1" fill="%s"/>' % [StudioTheme.hex(StudioTheme.BAR), StudioTheme.hex(StudioTheme.LINE)], 64, 64)
	return StudioTheme.svg_texture('<defs><linearGradient id="header" x2="0" y2="1"><stop stop-color="#b6e1ff"/><stop offset="0.35" stop-color="#78b5e3"/><stop offset="1" stop-color="#3979b1"/></linearGradient></defs><rect width="64" height="64" fill="url(#header)"/>', 64, 64)

func apply_header_style() -> void:
	# Header background and text colours follow the interface theme (classic: blue gradient).
	# Neon Pro step 2: neon bar padding is 0 12; classic keeps its old padding.
	if header_box == null: return
	var neon := StudioTheme.is_neon()
	header_box.texture = header_texture()
	header_box.texture_margin_bottom = 1 if neon else 0
	header_box.content_margin_left = 12 if neon else 14
	header_box.content_margin_right = 12 if neon else 14
	header_box.content_margin_top = 0 if neon else 6
	header_box.content_margin_bottom = 0 if neon else 6
	if title_label: title_label.add_theme_color_override("font_color", StudioTheme.TEXT if neon else Color("102e4d"))
	if save_label: save_label.add_theme_color_override("font_color", StudioTheme.TEXT2 if neon else Color("102e4d"))
	if workspace_label: workspace_label.add_theme_color_override("font_color", StudioTheme.TEXT3 if neon else Color("102e4d"))

func apply_theme_style(style_name: String) -> void:
	# Neon Pro port: Settings (Advanced) "Interface theme". Rebuilds the theme, background, header,
	# viewport surround, hint and toast; the drawing paper, renders and saved projects are unchanged.
	StudioTheme.set_style(style_name)
	var old_theme := theme
	theme = StudioTheme.make_theme()
	get_window().theme = theme
	# Codex's windows copied `window.theme = app.theme` when they were made (some at start-up):
	# re-point every one still holding the old Theme so dialogs follow the new style too.
	for window in find_children("*", "Window", true, false):
		if window.theme == old_theme: window.theme = theme
	if back_texture: back_texture.texture = back_gradient()
	apply_header_style()
	if canvas: canvas.refresh_surround(); canvas.queue_redraw()
	if timeline: timeline.queue_redraw()
	if workspace_layout and workspace_layout.horizontal: workspace_layout.apply_style()
	style_empty_hint()
	if stage_panel: stage_panel.add_theme_stylebox_override("panel", StudioTheme.flat(StudioTheme.STAGE if StudioTheme.is_neon() else Color.TRANSPARENT, Color.TRANSPARENT, 0, 0, Vector4(0, 0, 0, 0)))
	refresh_status_style()
	style_app_footer()

func apply_keyboard_nav(on: bool) -> void:
	# Redesign: buttons normally use FOCUS_NONE so Space drives playback; this opt-in makes them
	# Tab-reachable (theme focus outline) and restores FOCUS_NONE when turned off.
	keyboard_nav = on
	if on:
		keyboard_focusable.clear()
		var pending: Array = [self]
		while not pending.is_empty():
			var node: Node = pending.pop_back()
			if node is Window: continue
			if node is BaseButton and node.focus_mode == Control.FOCUS_NONE:
				node.focus_mode = Control.FOCUS_ALL
				keyboard_focusable.append(node)
			pending.append_array(node.get_children())
	else:
		var focus := get_viewport().gui_get_focus_owner()
		if focus and keyboard_focusable.has(focus): focus.release_focus()
		for node in keyboard_focusable:
			if is_instance_valid(node): node.focus_mode = Control.FOCUS_NONE
		keyboard_focusable.clear()

func resize_web_display() -> void:
	var css := Vector2i(JavaScriptBridge.eval("window.innerWidth"), JavaScriptBridge.eval("window.innerHeight"))
	if css.x > 0 and css.y > 0 and get_window().content_scale_size != css:
		get_window().content_scale_size = css

func show_display_settings() -> void:
	if is_instance_valid(display_dialog):
		display_dialog.popup_centered()
		return
	display_dialog = AcceptDialog.new()
	display_dialog.title = "Settings"
	display_dialog.exclusive = false
	add_child(display_dialog)
	var box := VBoxContainer.new()
	display_dialog.add_child(box)
	label(box,"Interface scale")
	var choices := OptionButton.new()
	box.add_child(choices)
	for percent in UI_PERCENT: choices.add_item("%d%%" % percent)
	choices.select(UI_PERCENT.find(roundi(get_window().content_scale_factor*100)))
	choices.item_selected.connect(func(index: int):
		var percent: int = UI_PERCENT[index]
		get_window().content_scale_factor = percent / 100.0
		save_display_preference("display","percent",percent)
		display_dialog.popup_centered())
	pose_editor.add_handle_size_control(box)
	button(box,"Toggle fullscreen  [F11]",toggle_fullscreen)
	button(box,"Keyboard shortcuts…",keyboard_shortcuts.open)
	var access:=VBoxContainer.new();box.add_child(advanced(access))
	access.visible=advanced_mode
	label(access,"Interface theme")
	var theme_choice:=OptionButton.new();access.add_child(theme_choice)
	for theme_name in ["Midnight Neon","Classic light","Classic dark"]: theme_choice.add_item(theme_name)
	theme_choice.select(StudioTheme.STYLES.find(StudioTheme.style))
	theme_choice.tooltip_text="Studio interface colours. Drawing paper and your movie are not affected. Switching to or from Midnight Neon applies the next time the studio starts."
	theme_choice.item_selected.connect(func(index: int):
		# Neon panels, pills and cards are built for neon at start-up, so only Classic light <-> dark
		# switches live; a change to or from neon is saved and applies at the next start.
		var target: String = StudioTheme.STYLES[index]
		save_display_preference("display","theme",target)
		if (target == "neon") != StudioTheme.is_neon(): message("The new interface theme applies the next time the studio starts.")
		else: apply_theme_style(target))
	var keyboard_check:=CheckBox.new();keyboard_check.text="Keyboard navigation";access.add_child(keyboard_check)
	keyboard_check.tooltip_text="Tab / Shift+Tab move between buttons with a visible outline; Enter presses. Playback keys keep working."
	keyboard_check.button_pressed=keyboard_nav
	keyboard_check.toggled.connect(func(on): apply_keyboard_nav(on);save_display_preference("display","keyboard_nav",on))
	var navigation:=VBoxContainer.new();box.add_child(advanced(navigation))
	navigation.visible=advanced_mode
	label(navigation,"Camera controls")
	navigation_choices=OptionButton.new();navigation.add_child(navigation_choices)
	navigation_choices.add_item("Fly (GMod)");navigation_choices.add_item("Orbit around selection")
	navigation_choices.select(1 if navigation_scheme=="orbit" else 0)
	navigation_choices.item_selected.connect(func(index):
		release_mouse();navigation_scheme="orbit" if index==1 else "fly"
		save_display_preference("navigation","scheme",navigation_scheme);refresh_workspace())
	label(navigation,"Orbit: Ctrl + left drag rotates; Ctrl + right drag pans.\nCtrl + wheel moves nearer/farther. Alt still reveals bones.")
	display_dialog.popup_centered()

func _ready() -> void:
	initialize_display()
	keyboard_shortcuts=preload("res://src/shortcut_editor.gd").new();add_child(keyboard_shortcuts);keyboard_shortcuts.setup(self)
	get_window().title = "Hybrid Animation Studio"
	DisplayServer.set_icon(StudioTheme.app_icon())
	get_tree().auto_accept_quit = false
	keys = [Timeline.key(0, Vector3(-1.5, 2, 5), Quaternion.IDENTITY, 60), Timeline.key(48, Vector3(1.5, 1.6, 3), Quaternion(Vector3.UP, -0.15), 52)]
	for title in ["Rough", "Ink"]:
		layers.append({"id": str(ResourceUID.create_id()), "name": title, "visible": true, "cels": []})
	renderer = Renderer.new()
	add_child(renderer)
	renderer.setup()
	audio_player = AudioStreamPlayer.new()
	add_child(audio_player)
	audio_player.finished.connect(audio_finished)
	pose_editor = PoseEditor.new()
	add_child(pose_editor)
	physics_editor=PhysicsEditor.new();physics_editor.app=self;add_child(physics_editor)
	source_import = SourceImport.new()
	source_import.app = self
	add_child(source_import)
	source_browser = SourceBrowser.new()
	has_project = HasProject.new(); has_project.app = self; add_child(has_project)
	source_browser.app = self
	add_child(source_browser)
	world_selection = WorldSelection.new(); world_selection.app = self; add_child(world_selection)
	character_parts_editor=preload("res://src/character_parts_editor.gd").new();character_parts_editor.app=self;add_child(character_parts_editor)
	clip_editor=ClipEditor.new();clip_editor.app=self;add_child(clip_editor)
	particle_editor=preload("res://src/particle_editor.gd").new();particle_editor.app=self;add_child(particle_editor)
	build_ui()
	mmd_pose_importer=preload("res://src/mmd_pose_import.gd").new();add_child(mmd_pose_importer);mmd_pose_importer.setup(self)
	if StudioTheme.is_neon(): pose_editor.build_neon_inspector()
	audio_importer=preload("res://src/audio_import.gd").new();audio_importer.app=self;add_child(audio_importer)
	audio_trim_editor=preload("res://src/audio_trim_editor.gd").new();audio_trim_editor.app=self;add_child(audio_trim_editor)
	audio_fade_editor=preload("res://src/audio_fade_editor.gd").new();audio_fade_editor.app=self;add_child(audio_fade_editor)
	project_timing=preload("res://src/project_timing.gd").new();project_timing.app=self;add_child(project_timing)
	project_canvas=preload("res://src/project_canvas.gd").new();project_canvas.app=self;add_child(project_canvas)
	timeline.audio_trim_context=audio_trim_editor.drag_context
	fill_editor=FillEditor.new();fill_editor.app=self;add_child(fill_editor);fill_editor.setup(drawing_section)
	onion_editor=OnionEditor.new();onion_editor.app=self;add_child(onion_editor);onion_editor.setup(drawing_section)
	reference_sheet=preload("res://src/reference_sheet.gd").new();reference_sheet.app=self;add_child(reference_sheet);reference_sheet.setup(drawing_section)
	layer_editor=LayerEditor.new();layer_editor.app=self;add_child(layer_editor);layer_editor.setup(drawing_section)
	cel_timing=preload("res://src/cel_timing_editor.gd").new();cel_timing.app=self;add_child(cel_timing);timeline.cel_context_provider=cel_timing.begin;timeline.cel_moved.connect(cel_timing.commit);timeline.cel_resized.connect(cel_timing.resize)
	cel_clipboard=preload("res://src/cel_clipboard.gd").new();cel_clipboard.app=self;add_child(cel_clipboard);timeline.cel_menu_provider=cel_clipboard.open_menu
	raster_importer=preload("res://src/krita_import.gd").new();add_child(raster_importer);raster_importer.setup(self)
	video_importer=preload("res://src/video_import.gd").new();add_child(video_importer);video_importer.setup(self)
	color_sampler=ColorSampler.new();color_sampler.app=self;add_child(color_sampler);color_sampler.setup(drawing_section)
	palette_editor=preload("res://src/palette_editor.gd").new();palette_editor.app=self;add_child(palette_editor);palette_editor.setup(drawing_section)
	drawing_selection_editor=preload("res://src/drawing_selection_editor.gd").new();drawing_selection_editor.app=self;add_child(drawing_selection_editor);drawing_selection_editor.setup(drawing_section)
	if StudioTheme.is_neon(): build_draw_inspector()
	camera_transform_editor=preload("res://src/camera_transform_editor.gd").new();add_child(camera_transform_editor);camera_transform_editor.setup(self)
	if StudioTheme.is_neon(): build_camera_inspector()
	sequence_editor=preload("res://src/sequence_editor.gd").new();add_child(sequence_editor);sequence_editor.setup(self)
	if StudioTheme.is_neon(): compact_timeline_rows()
	keyboard_shortcuts.refresh_labels()
	if keyboard_nav: apply_keyboard_nav(true)
	renderer.view_changed.connect(refresh_camera_controls)
	import_actions=ImportActions.new();import_actions.app=self;add_child(import_actions)
	height_review=preload("res://src/import_height_review.gd").new();height_review.app=self;add_child(height_review)
	map_calibration=preload("res://src/map_calibration.gd").new();map_calibration.app=self;add_child(map_calibration)
	get_window().files_dropped.connect(import_actions.os_drop)
	world_selection.initialize_mask()
	var opened: bool = load_demo_room() if "--demo-room" in OS.get_cmdline_user_args() else new_project()
	if not opened: return
	dirty = false
	var testing := "--script" in OS.get_cmdline_args()
	for argument in OS.get_cmdline_user_args():
		if argument.contains("smoke"): testing = true
	home=HomeScreen.new();home.app=self
	home.store.file_path=recent_path if not recent_path.is_empty() else (ProjectSettings.globalize_path("res://output/test-preferences/%d.json" % OS.get_process_id()) if testing else recovery_root.get_base_dir().path_join("recent-projects.json"))
	add_child(home)
	tutorials=Tutorials.new();tutorials.app=self;add_child(tutorials)
	var recovery_timer := Timer.new()
	recovery_timer.wait_time = 1
	recovery_timer.timeout.connect(autosave_tick)
	add_child(recovery_timer)
	recovery_timer.start()
	message("New empty world. Add a scene or model, or move freely with Ctrl + left-drag and WASD. The grid is an editor guide and stays out of your movie.")
	if "--demo-room" in OS.get_cmdline_user_args(): message("Sample room: draw on Ink, or choose Scene / camera to set your shot. %s previews your movie." % keyboard_shortcuts.label_for("play"))
	if "--smoke" in OS.get_cmdline_user_args():
		call_deferred("smoke")
	if "--ui-smoke" in OS.get_cmdline_user_args():
		get_tree().create_timer(40).timeout.connect(func(): push_error("UI smoke watchdog expired"); get_tree().quit(2))
		call_deferred("ui_smoke")
	if "--audio-smoke" in OS.get_cmdline_user_args():
		get_tree().create_timer(45).timeout.connect(func(): push_error("Audio smoke watchdog expired"); get_tree().quit(2))
		call_deferred("audio_smoke")
	if "--recovery-smoke" in OS.get_cmdline_user_args():
		get_tree().create_timer(40).timeout.connect(func(): push_error("Recovery watchdog expired"); get_tree().quit(2))
		call_deferred("recovery_smoke")
	if "--pose-smoke" in OS.get_cmdline_user_args():
		get_tree().create_timer(90).timeout.connect(func(): push_error("Pose watchdog expired"); get_tree().quit(2))
		call_deferred("pose_smoke")
	var arguments:=OS.get_cmdline_user_args()
	var requested:=arguments.find("--open-project")
	if requested>=0 and requested+1<arguments.size():
		call_deferred("open_startup_project",arguments[requested+1])
	elif not testing:call_deferred("recover_latest",recovery_session,recovery_revision)

func open_startup_project(path: String) -> void:
	if path.get_extension().to_lower()!="has" or not FileAccess.file_exists(path):
		home.open_home()
		home.feedback("Could not find the requested .has project.")
		return
	home.open_recent(path)

func button(parent: Node, text: String, action: Callable) -> Button:
	var b := Button.new()
	b.text = text
	b.pressed.connect(action)
	b.focus_mode = Control.FOCUS_NONE
	parent.add_child(b)
	return b

func label(parent: Node, text: String) -> Label:
	var l := Label.new()
	l.text = text
	parent.add_child(l)
	return l

func spin(parent: Node, text: String, low: float, high: float, value: float) -> SpinBox:
	label(parent, text)
	var s := SpinBox.new()
	s.min_value = low
	s.max_value = high
	s.value = value
	parent.add_child(s)
	return s

func icon_button(parent: Node, text: String, kind: String, action: Callable, hint := "") -> Button:
	var control := button(parent, text, action)
	control.icon = StudioTheme.icon(kind)
	control.expand_icon = false
	control.add_theme_constant_override("icon_max_width", 22)
	control.tooltip_text = hint if not hint.is_empty() else text
	return control

func header_button(parent: Node, text: String, kind: String, action: Callable, hint := "") -> Button:
	# Neon Pro step 2: top-bar button with a 16 px icon left of a short label (see style_header).
	return style_header(icon_button(parent, text, kind, action, hint), kind)

func override_button_boxes(control: Button, normal: StyleBox, hover: StyleBox, pressed: StyleBox, disabled: StyleBox) -> void:
	for suffix in ["", "_mirrored"]:
		control.add_theme_stylebox_override("normal" + suffix, normal)
		control.add_theme_stylebox_override("hover" + suffix, hover)
		control.add_theme_stylebox_override("pressed" + suffix, pressed)
		control.add_theme_stylebox_override("hover_pressed" + suffix, pressed)
		control.add_theme_stylebox_override("disabled" + suffix, disabled)

func override_button_colors(control: Button, normal: Color, hover: Color, pressed: Color) -> void:
	# Text and icon share one colour per state (icons are drawn white and tinted).
	for prefix in ["font_", "icon_"]:
		control.add_theme_color_override(prefix + ("normal_color" if prefix == "icon_" else "color"), normal)
		control.add_theme_color_override(prefix + "focus_color", normal)
		control.add_theme_color_override(prefix + "hover_color", hover)
		control.add_theme_color_override(prefix + "pressed_color", pressed)
		control.add_theme_color_override(prefix + "hover_pressed_color", pressed)
		control.add_theme_color_override(prefix + "disabled_color", StudioTheme.TEXT3)

func style_header(control: Button, kind: String, chevron := false) -> Button:
	# Neon Pro step 2: ghost header button: h40, pad 0 12, r8, gap 8, 13/500 #B4BAC7 and a 16 px icon
	# in the same colour; hover #1D2029 with #F4F6FA. Menus get a 12 px #8C93A3 chevron on the right.
	# Buttons with a label join header_compact so fit_header() can show them icon-only.
	control.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	if not control.text.is_empty():
		control.set_meta("label", control.text)
		header_compact.append(control)
	if not StudioTheme.is_neon(): return style_nav(control)
	control.custom_minimum_size.y = 40
	control.icon = StudioTheme.icon(kind, Color.WHITE, 16)
	control.add_theme_constant_override("icon_max_width", 16)
	control.add_theme_constant_override("h_separation", 8)
	control.add_theme_font_override("font", StudioTheme.font(500))
	control.add_theme_font_size_override("font_size", 13)
	var pad := Vector4(12, 0, 30 if chevron else 12, 0)
	var clear := StudioTheme.flat(Color.TRANSPARENT, Color.TRANSPARENT, 8, 0, pad)
	override_button_boxes(control, clear, StudioTheme.flat(StudioTheme.HOVER, Color.TRANSPARENT, 8, 0, pad), StudioTheme.flat(StudioTheme.RAISE, Color.TRANSPARENT, 8, 0, pad), clear)
	override_button_colors(control, StudioTheme.TEXT2, StudioTheme.TEXT, Color.WHITE)
	if chevron:
		var arrow := TextureRect.new()
		arrow.texture = StudioTheme.icon("chevron", StudioTheme.TEXT3, 12)
		arrow.mouse_filter = Control.MOUSE_FILTER_IGNORE
		control.add_child(arrow)
		arrow.set_anchors_preset(Control.PRESET_CENTER_RIGHT)
		arrow.offset_left = -24; arrow.offset_right = -12; arrow.offset_top = -6; arrow.offset_bottom = 6
	return control

func header_divider(parent: Node) -> Control:
	# 1x24 #2C303B hairline with 4 px on each side.
	var holder := MarginContainer.new()
	holder.add_theme_constant_override("margin_left", 4)
	holder.add_theme_constant_override("margin_right", 4)
	holder.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var line := ColorRect.new()
	line.color = StudioTheme.LINE2 if StudioTheme.is_neon() else Color(1, 1, 1, 0.35)
	line.custom_minimum_size = Vector2(1, 24)
	line.mouse_filter = Control.MOUSE_FILTER_IGNORE
	holder.add_child(line)
	parent.add_child(holder)
	return holder

func style_tab(control: Button, kind: String) -> void:
	# Neon Pro step 2: Draw / Camera / Pose tab, 104x40, r7. Active: #171A21 + 1 px #2C303B, 13/600
	# white with a white icon and a 2 px neon underline (inset 30, 3 from the bottom) with a pink glow;
	# inactive: transparent, 13/500 #8C93A3. The icon+label group is centred by equal padding.
	control.set_meta("label", control.text)
	control.custom_minimum_size = Vector2(104, 40)
	control.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	if not StudioTheme.is_neon(): return
	control.icon = StudioTheme.icon(kind, Color.WHITE, 16)
	control.add_theme_constant_override("icon_max_width", 16)
	control.add_theme_constant_override("h_separation", 8)
	control.add_theme_font_size_override("font_size", 13)
	var content := StudioTheme.font(600).get_string_size(control.text, HORIZONTAL_ALIGNMENT_LEFT, -1, 13).x + 24
	var side := maxf(8.0, floorf((104.0 - content) / 2.0))
	control.set_meta("pad", side)
	var pad := Vector4(side, 0, side, 0)
	var boxes := [StudioTheme.flat(Color.TRANSPARENT, Color.TRANSPARENT, 7, 0, pad), StudioTheme.flat(StudioTheme.HOVER, Color.TRANSPARENT, 7, 0, pad), StudioTheme.flat(StudioTheme.RAISE, StudioTheme.LINE2, 7, 1, pad)]
	control.set_meta("boxes", boxes)
	override_button_boxes(control, boxes[0], boxes[1], boxes[2], boxes[0])
	override_button_colors(control, StudioTheme.TEXT3, StudioTheme.TEXT, Color.WHITE)
	var underline := Control.new()
	underline.mouse_filter = Control.MOUSE_FILTER_IGNORE
	control.add_child(underline)
	underline.anchor_left = 0; underline.anchor_right = 1; underline.anchor_top = 1; underline.anchor_bottom = 1
	underline.offset_left = 30; underline.offset_right = -30; underline.offset_top = -5; underline.offset_bottom = -3
	# Soft halo as the mock's two 10 px shadows (accent 55% + blue 45%): a faint blue panel under a
	# mixed violet one, so the line reads violet-blue rather than as a strong pink band.
	for shade in [Color(0.18, 0.55, 1, 0.2), Color(0.48, 0.36, 1, 0.3)]:
		var glow := Panel.new()
		glow.mouse_filter = Control.MOUSE_FILTER_IGNORE
		glow.add_theme_stylebox_override("panel", StudioTheme.flat(Color(shade, 0), Color.TRANSPARENT, 1, 0, Vector4(0, 0, 0, 0), shade, 10 if shade.b > 0.99 and shade.r < 0.2 else 9))
		underline.add_child(glow)
		glow.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var line := TextureRect.new()
	line.texture = StudioTheme.neon_line()
	line.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	line.stretch_mode = TextureRect.STRETCH_SCALE
	line.mouse_filter = Control.MOUSE_FILTER_IGNORE
	underline.add_child(line)
	line.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	underline.visible = false
	control.set_meta("underline", underline)

func set_tab_compact(tab: Button, compact: bool) -> void:
	var text: String = "" if compact else str(tab.get_meta("label", tab.text))
	if tab.text == text: return
	tab.text = text
	tab.custom_minimum_size.x = 44 if compact else 104
	var side: float = 14.0 if compact else float(tab.get_meta("pad", 12.0))
	for box in tab.get_meta("boxes", []):
		box.content_margin_left = side
		box.content_margin_right = side
	var underline = tab.get_meta("underline") if tab.has_meta("underline") else null
	if underline:
		underline.offset_left = 12 if compact else 30
		underline.offset_right = -12 if compact else -30

func refresh_mode_tabs() -> void:
	# The mode dropdown stays the source of truth; tabs only mirror it.
	for i in mode_tabs.size():
		var on := mode.selected == i
		var tab := mode_tabs[i]
		if tab.button_pressed != on: tab.set_pressed_no_signal(on)
		var underline = tab.get_meta("underline") if tab.has_meta("underline") else null
		if underline and underline.visible != on: underline.visible = on
		if StudioTheme.is_neon(): tab.add_theme_font_override("font", StudioTheme.font(600 if on else 500))

func style_export(control: Button) -> void:
	# Neon Pro step 2: Export movie: h40, pad 0 10 0 14, r8, neon fill, 14/600 #07080B with a dark
	# icon, an MP4 chip (mono 11/600 #07080B on rgba(255,255,255,.24), r5, h20, pad 0 6) and a pink
	# glow from a decorative panel drawn behind the button.
	control.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	if not StudioTheme.is_neon():
		style_accent(style_nav(control))
		return
	control.theme_type_variation = "NeonButton"
	control.custom_minimum_size.y = 40
	control.icon = StudioTheme.icon("export", StudioTheme.ON_NEON, 16)
	control.add_theme_constant_override("icon_max_width", 16)
	control.add_theme_constant_override("h_separation", 8)
	# Mock: 0 6px 22px -6px pink at 65 % plus a wider blue one. A soft 6 px pink shadow on a panel
	# inset 6 px (the negative spread) fades out above the bar's edge; a fainter blue panel inset 8 px.
	for spec in [[Color(0.18, 0.549, 1, 0.25), 8.0, 8], [Color(1, 0.239, 0.604, 0.32), 6.0, 6]]:
		var glow := Panel.new()
		glow.show_behind_parent = true
		glow.mouse_filter = Control.MOUSE_FILTER_IGNORE
		glow.add_theme_stylebox_override("panel", StudioTheme.flat(Color(spec[0], 0), Color.TRANSPARENT, 8, 0, Vector4.ZERO, spec[0], spec[2], Vector2(0, 2)))
		control.add_child(glow)
		glow.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		glow.offset_left = spec[1]
		glow.offset_right = -spec[1]
	export_chip = Label.new()
	export_chip.text = "MP4"
	export_chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	export_chip.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	export_chip.custom_minimum_size.y = 20
	export_chip.add_theme_font_override("font", StudioTheme.mono(600))
	export_chip.add_theme_font_size_override("font_size", 11)
	export_chip.add_theme_color_override("font_color", StudioTheme.ON_NEON)
	export_chip.add_theme_stylebox_override("normal", StudioTheme.flat(Color(1, 1, 1, 0.24), Color.TRANSPARENT, 5, 0, Vector4(6, 0, 6, 0)))
	control.add_child(export_chip)
	export_chip.set_anchors_and_offsets_preset(Control.PRESET_CENTER_RIGHT, Control.PRESET_MODE_MINSIZE, 10)
	var right := 10.0 + export_chip.get_combined_minimum_size().x + 10.0
	var normal := StudioTheme.neon_fill(8.0)
	var hover := StudioTheme.neon_fill(8.0)
	hover.modulate_color = Color(1.08, 1.08, 1.08)
	var disabled := StudioTheme.neon_fill(8.0)
	disabled.modulate_color = Color(1, 1, 1, 0.55)
	for box in [normal, hover, disabled]:
		box.content_margin_left = 14; box.content_margin_right = right; box.content_margin_top = 0; box.content_margin_bottom = 0
	control.set_meta("boxes", [normal, hover, disabled])
	override_button_boxes(control, normal, hover, normal, disabled)

func header_fits() -> bool:
	# True when the left and right groups clear the centred tab group by 8 px (or simply fit when
	# the tabs are hidden, as in Advanced).
	var width := header_row.size.x
	var gap := float(header_row.get_theme_constant("separation"))
	var left := 0.0
	var right := 0.0
	var after := false
	for child in header_row.get_children():
		if child == header_spacer:
			after = true
			continue
		if not (child as Control).visible: continue
		var used: float = (child as Control).get_combined_minimum_size().x + gap
		if after: right += used
		else: left += used
	if header_tab_overlay == null or not header_tab_overlay.visible: return left + right <= width
	var side := (width - header_tab_frame.get_combined_minimum_size().x) / 2.0
	return left + 8.0 <= side and right + 8.0 <= side

func set_header_level(level: int) -> void:
	if level == header_level: return
	header_level = level
	for control in header_compact:
		var text: String = str(control.get_meta("label")) if level < 1 else ""
		if control.text != text: control.text = text
	if export_chip and export_button.has_meta("boxes"):
		if export_chip.visible != (level < 2): export_chip.visible = level < 2
		var right := 10.0 + (export_chip.get_combined_minimum_size().x + 10.0 if level < 2 else 0.0)
		for box in export_button.get_meta("boxes"): box.content_margin_right = right
		export_button.update_minimum_size()
	for tab in mode_tabs: set_tab_compact(tab, level >= 3)
	if header_project and header_project.visible != (level < 4): header_project.visible = level < 4

func fit_header() -> void:
	# Neon Pro step 2: the centred tabs are an overlay, so the bar never adds horizontal scrolling.
	# When a side group would run under the tabs, step down until it fits: 1 ghost buttons go
	# icon-only, 2 Export drops the MP4 chip, 3 tabs go icon-only, 4 the project name/save line
	# hides (the brand mark's tooltip keeps the name). Tooltips keep every button name.
	if header_row == null or header_row.size.x <= 0: return
	for level in 5:
		set_header_level(level)
		if level == 4 or header_fits(): return

func style_nav(control: Button) -> Button:
	# Classic styles: transparent top-bar button (icon left of the label) that lights up on hover.
	control.custom_minimum_size.y = 40
	control.add_theme_constant_override("icon_max_width", 22)
	control.add_theme_font_size_override("font_size", 13)
	var normal := StyleBoxFlat.new()
	normal.bg_color = Color.TRANSPARENT
	normal.content_margin_left = 10
	normal.content_margin_right = 10
	normal.content_margin_top = 4
	normal.content_margin_bottom = 4
	normal.set_corner_radius_all(6)
	var hover: StyleBoxFlat = normal.duplicate()
	hover.bg_color = Color(1, 1, 1, 0.2)
	hover.set_border_width_all(1)
	hover.border_color = Color(1, 1, 1, 0.35)
	var pressed: StyleBoxFlat = hover.duplicate()
	pressed.bg_color = Color(0.08, 0.25, 0.44, 0.25)
	control.add_theme_stylebox_override("normal", normal)
	control.add_theme_stylebox_override("disabled", normal)
	control.add_theme_stylebox_override("hover", hover)
	control.add_theme_stylebox_override("pressed", pressed)
	for state in ["font_color", "font_hover_color", "font_pressed_color", "font_hover_pressed_color"]:
		control.add_theme_color_override(state, Color("ffffff"))
	control.add_theme_color_override("font_shadow_color", Color(0.08, 0.2, 0.34, 0.7))
	control.add_theme_constant_override("shadow_offset_y", 1)
	return control

func advanced(control: Control) -> Control:
	advanced_controls.append(control)
	return control

func simple_only(control: Control) -> Control:
	# Mark a control as Simple-only (a shortcut to an Advanced control); refresh_workspace() hides it in Advanced.
	simple_controls.append(control)
	return control

func menu_button(parent: Node, text: String, kind: String, items: Array, hint := "") -> MenuButton:
	# Redesign: one top-bar button that opens a short list instead of a row of buttons.
	var m := MenuButton.new()
	m.text = text
	m.icon = StudioTheme.icon(kind)
	m.flat = false
	m.focus_mode = Control.FOCUS_NONE
	m.tooltip_text = hint if not hint.is_empty() else text
	var popup := m.get_popup()
	for i in items.size(): popup.add_item(items[i][0], i)
	popup.id_pressed.connect(func(id): items[id][1].call())
	parent.add_child(m)
	style_header(m, kind, true)
	return m

func pick_mode(index: int) -> void:
	# Simple Draw/Camera/Pose tabs drive the mode dropdown, which stays the source of truth.
	if exporting or mode.selected == index: refresh_workspace(); return
	mode.select(index)
	change_mode(index)

func pick_tool(index: int) -> void:
	# Simple tool strip drives the same tool OptionButton the shortcuts use. Pick color and Select area
	# take the shortcut path (I / M in _unhandled_key_input): their arm() guards, cancels the other
	# pending tool and shows the instruction.
	if index == 3 and color_sampler: color_sampler.arm()
	elif index == 4 and drawing_selection_editor: drawing_selection_editor.arm()
	elif tool.selected != index:
		tool.select(index)
		tool.item_selected.emit(index)
	refresh_tool_strip()

func refresh_tool_strip() -> void:
	if tool_strip == null or tool == null: return
	var show_strip := not advanced_mode and mode.selected == 0
	if tool_strip.visible != show_strip: tool_strip.visible = show_strip
	for i in tool_buttons.size():
		if tool_buttons[i].button_pressed != (tool.selected == i): tool_buttons[i].set_pressed_no_signal(tool.selected == i)
	refresh_view_row()

# ---- Neon Pro step 4: viewport overlays ---------------------------------------------------
# The stage, tool pill, badges, viewfinder corners and stage footer only exist in the neon style
# (built at start-up); classic styles keep the old view toolbar, scene line and footer toast.

func view_pill(parent: Node) -> PanelContainer:
	# Floating pill on the stage: rgba(12,13,17,.94), 1 px #2C303B, r10, pad 3, soft drop shadow.
	var pill := PanelContainer.new()
	pill.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	pill.add_theme_stylebox_override("panel", StudioTheme.flat(Color(12 / 255.0, 13 / 255.0, 17 / 255.0, 0.94), StudioTheme.LINE2, 10, 1, Vector4(3, 3, 3, 3), Color(0, 0, 0, 0.8), 11, Vector2(0, 12)))
	parent.add_child(pill)
	return pill

func pill_divider(parent: Node) -> void:
	# 1x24 #2C303B divider with 3 px on each side.
	var holder := MarginContainer.new()
	holder.add_theme_constant_override("margin_left", 3)
	holder.add_theme_constant_override("margin_right", 3)
	holder.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var line := ColorRect.new()
	line.color = StudioTheme.LINE2
	line.custom_minimum_size = Vector2(1, 24)
	line.mouse_filter = Control.MOUSE_FILTER_IGNORE
	holder.add_child(line)
	parent.add_child(holder)

func overlay_icon(parent: Node, kind: String, color: Color, size := 16) -> TextureRect:
	var image := TextureRect.new()
	image.texture = StudioTheme.icon(kind, color, size)
	image.stretch_mode = TextureRect.STRETCH_KEEP_CENTERED
	image.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	image.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(image)
	return image

func overlay_label(parent: Node, text: String, color: Color, size := 12, weight := 400, mono := false) -> Label:
	var l := label(parent, text)
	l.add_theme_color_override("font_color", color)
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_font_override("font", StudioTheme.mono(weight) if mono else StudioTheme.font(weight))
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l

func style_tool_button(control: Button, text: String, kind: String, shortcut := "") -> void:
	# Labelled pill tool: h40, pad 0 8 0 10, gap 8, 13/500 #B4BAC7 with a 16 px #8C93A3 icon and an
	# 18 px keycap on the right (letter from keyboard_shortcuts). Active: neon ring on #171A22 with a
	# violet glow, 600 white label and white icon (refresh_view_row switches the weight).
	control.theme_type_variation = "ToolButton"
	control.set_meta("label", text)
	control.text = text
	control.custom_minimum_size = Vector2(0, 40)
	control.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	control.icon = StudioTheme.icon(kind, Color.WHITE, 16)
	control.add_theme_constant_override("icon_max_width", 16)
	control.add_theme_constant_override("h_separation", 8)
	control.add_theme_font_size_override("font_size", 13)
	control.add_theme_font_override("font", StudioTheme.font(500))
	for state in ["icon_normal_color", "icon_focus_color", "icon_disabled_color"]: control.add_theme_color_override(state, StudioTheme.TEXT3)
	control.add_theme_color_override("icon_hover_color", StudioTheme.TEXT2)
	for state in ["icon_pressed_color", "icon_hover_pressed_color"]: control.add_theme_color_override(state, Color.WHITE)
	var glow := Panel.new()
	glow.mouse_filter = Control.MOUSE_FILTER_IGNORE
	glow.show_behind_parent = true
	glow.visible = false
	glow.add_theme_stylebox_override("panel", StudioTheme.flat(Color(0.482, 0.361, 1, 0), Color.TRANSPARENT, 8, 0, Vector4(0, 0, 0, 0), Color(0.482, 0.361, 1, 0.4), 7))
	control.add_child(glow)
	glow.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	control.set_meta("glow", glow)
	if not shortcut.is_empty():
		var chip := Label.new()
		chip.theme_type_variation = "KbdLabel"
		chip.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		chip.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
		control.add_child(chip)
		control.set_meta("kbd", chip)
		control.set_meta("shortcut", shortcut)
	set_tool_kbd(control)

func set_tool_kbd(control: Button) -> void:
	# Keycap text follows keyboard_shortcuts; the button's right padding makes room for the chip.
	if control.has_meta("tool_key"):
		var bound: String = keyboard_shortcuts.label_for(control.get_meta("tool_key"))
		var tip: String = control.get_meta("tool_name") if bound.is_empty() else "%s [%s]" % [control.get_meta("tool_name"), bound]
		if control.tooltip_text != tip: control.tooltip_text = tip
	var right := 12.0
	if control.has_meta("kbd"):
		var chip: Label = control.get_meta("kbd")
		var text: String = keyboard_shortcuts.label_for(control.get_meta("shortcut"))
		if chip.text != text: chip.text = text
		var width := maxf(18.0, chip.get_combined_minimum_size().x)
		chip.set_anchors_preset(Control.PRESET_CENTER_RIGHT)
		chip.offset_left = -8 - width; chip.offset_right = -8; chip.offset_top = -9; chip.offset_bottom = 9
		right = 8 + width + 8
	if control.has_meta("right") and control.get_meta("right") == right: return
	control.set_meta("right", right)
	var pad := Vector4(10, 0, right, 0)
	var clear := StudioTheme.flat(Color.TRANSPARENT, Color.TRANSPARENT, 8, 0, pad)
	var on := StudioTheme.neon_ring(8.0, 1.5, StudioTheme.TOOL_INNER)
	on.content_margin_left = pad.x; on.content_margin_top = 0; on.content_margin_right = pad.z; on.content_margin_bottom = 0
	override_button_boxes(control, clear, StudioTheme.flat(StudioTheme.HOVER, Color.TRANSPARENT, 8, 0, pad), on, clear)

func style_save_key(control: Button) -> void:
	# Camera strip's main action: PrimaryButton h40, pad 0 16 0 12, 14/600, pink diamond icon.
	control.theme_type_variation = "PrimaryButton"
	control.custom_minimum_size = Vector2(0, 40)
	control.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	control.icon = StudioTheme.icon("key-solid", StudioTheme.CAMERA, 18)
	control.add_theme_constant_override("icon_max_width", 18)
	control.add_theme_constant_override("h_separation", 8)
	var pad := Vector4(12, 0, 16, 0)
	override_button_boxes(control, StudioTheme.flat(Color("1a1d25"), StudioTheme.LINE3, 8, 1, pad), StudioTheme.flat(Color("21252f"), StudioTheme.LINE3, 8, 1, pad), StudioTheme.flat(StudioTheme.RAISE, StudioTheme.LINE3, 8, 1, pad), StudioTheme.flat(Color("0f1116"), StudioTheme.LINE, 8, 1, pad))

func style_ghost(control: Button, kind: String, height := 40) -> void:
	# Ghost button: transparent, hover #1D2029; 13/500 #B4BAC7 text and icon, #F4F6FA on hover.
	control.set_meta("label", control.text)
	control.custom_minimum_size = Vector2(height if control.text.is_empty() else 0, height)
	control.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	control.icon = StudioTheme.icon(kind, Color.WHITE, 16)
	control.add_theme_constant_override("icon_max_width", 16)
	control.add_theme_constant_override("h_separation", 8)
	control.add_theme_font_override("font", StudioTheme.font(500))
	control.add_theme_font_size_override("font_size", 13)
	var pad := Vector4(8 if height < 40 else 10, 0, 8 if height < 40 else 12, 0)
	var clear := StudioTheme.flat(Color.TRANSPARENT, Color.TRANSPARENT, 8, 0, pad)
	override_button_boxes(control, clear, StudioTheme.flat(StudioTheme.HOVER, Color.TRANSPARENT, 8, 0, pad), StudioTheme.flat(StudioTheme.RAISE, Color.TRANSPARENT, 8, 0, pad), clear)
	override_button_colors(control, StudioTheme.TEXT2, StudioTheme.TEXT, Color.WHITE)

func style_view_chips(controls_to_style: Array) -> void:
	# Codex's view controls stay visible in Simple (lighting, Frame scene, Scene setup / Frame / 3×3)
	# as compact h32 outline chips in the second pill: a deliberate deviation from the mock.
	var pad := Vector4(10, 0, 10, 0)
	for control in controls_to_style:
		if not (control is Button): continue
		control.custom_minimum_size.y = 32
		control.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		control.add_theme_font_size_override("font_size", 12)
		if control is CheckButton:
			var row := StudioTheme.flat(Color.TRANSPARENT, Color.TRANSPARENT, 8, 0, Vector4(8, 0, 6, 0))
			override_button_boxes(control, row, StudioTheme.flat(StudioTheme.HOVER, Color.TRANSPARENT, 8, 0, Vector4(8, 0, 6, 0)), row, row)
			continue
		override_button_boxes(control, StudioTheme.flat(StudioTheme.FIELD, StudioTheme.LINE2, 8, 1, pad), StudioTheme.flat(Color("21252f"), StudioTheme.LINE3, 8, 1, pad), StudioTheme.flat(StudioTheme.RAISE, StudioTheme.LINE2, 8, 1, pad), StudioTheme.flat(Color("0f1116"), StudioTheme.LINE, 8, 1, pad))

func pick_pose_operation(index: int) -> void:
	# Simple Pose strip drives the same Rotate / Move dropdown as the Pose panel (pose_smoke uses it).
	if pose_editor.operation.selected != index:
		pose_editor.operation.select(index)
		pose_editor.operation.item_selected.emit(index)
		pose_editor.update_gizmo()
	refresh_view_row()

func show_help_popover(anchor: Control, title: String, text: String) -> void:
	# "Mouse and keys": the existing help text in a small popover under its button.
	if anchor == null: return
	if help_popup == null:
		help_popup = PopupPanel.new()
		add_child(help_popup)
		var pad := MarginContainer.new()
		for side in ["left", "right", "top", "bottom"]: pad.add_theme_constant_override("margin_" + side, 8)
		help_popup.add_child(pad)
		var box := VBoxContainer.new()
		box.add_theme_constant_override("separation", 6)
		pad.add_child(box)
		help_popup_title = overlay_label(box, "", StudioTheme.TEXT, 13, 600)
		help_popup_body = overlay_label(box, "", StudioTheme.TEXT2, 12)
	help_popup_title.text = title
	help_popup_body.text = text.replace("\r", "").strip_edges()
	var scale := anchor.get_global_transform_with_canvas().get_scale()
	var at := anchor.get_screen_position() + Vector2(0, (anchor.size.y + 6) * scale.y)
	help_popup.reset_size()
	help_popup.position = Vector2i(at)
	help_popup.popup()

func refresh_view_row() -> void:
	# Pills follow the strips they hold; the Pose strip mirrors pose_editor.operation without writing.
	if view_row == null or tool_pill == null or tool == null or mode == null: return
	var changed := false
	var pose_on := not advanced_mode and mode.selected == 2
	for pair in [[tool_pill, tool_strip.visible], [camera_pill, camera_strip.visible], [pose_pill, pose_on]]:
		if pair[0].visible != pair[1]: pair[0].visible = pair[1]; changed = true
	for i in tool_buttons.size(): sync_tool_look(tool_buttons[i])
	if camera_hint:
		var hint_on := camera_strip.visible and not tool_compact
		if camera_hint.visible != hint_on: camera_hint.visible = hint_on; changed = true
	if pose_editor and pose_editor.operation:
		var turning: bool = turn_button != null and pose_editor.operation.selected == 0 and pose_editor.selected == "@root"
		for i in pose_buttons.size():
			var on: bool = pose_editor.operation.selected == i and not (i == 0 and turning)
			if pose_buttons[i].button_pressed != on: pose_buttons[i].set_pressed_no_signal(on)
			sync_tool_look(pose_buttons[i])
		if turn_button:
			if turn_button.button_pressed != turning: turn_button.set_pressed_no_signal(turning)
			sync_tool_look(turn_button)
	if changed: queue_view_fit()

func sync_fit_view() -> void:
	if fit_view_button == null or canvas == null: return
	var want: bool = advanced_mode or not StudioTheme.is_neon() or not is_equal_approx(canvas.zoom, 1.0) or canvas.pan != Vector2.ZERO
	if fit_view_button.visible != want:
		fit_view_button.visible = want
		queue_view_fit()

func pick_turn_model() -> void:
	# "Turn model": select the model root and use Rotate, exactly as the Pose panel would.
	# Through Codex's own path (the Bones tree row), so the tree highlights the root and a click on
	# the previously selected bone selects it again; the direct write is only a fallback.
	if pose_editor.selected != "@root":
		var root_item = pose_editor.tree_items.get("@root") if pose_editor.tree_items is Dictionary else null
		if root_item is TreeItem and is_instance_valid(root_item):
			root_item.select(0)
			pose_editor.tree.scroll_to_item(root_item)
		if pose_editor.selected != "@root":
			pose_editor.selected = "@root"
			pose_editor.refresh_values()
	pick_pose_operation(0)

func compact_option(control: OptionButton, on: bool, kinds: Array) -> void:
	# Icon + chevron only (text transparent and clipped; the full names stay in the popup and tooltip).
	control.fit_to_longest_item = not on
	control.clip_text = on
	for i in control.item_count: control.set_item_icon(i, StudioTheme.icon(kinds[mini(i, kinds.size() - 1)], Color.WHITE, 16) if on else null)
	control.add_theme_constant_override("icon_max_width", 16)
	for state in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color", "font_hover_pressed_color"]:
		if on: control.add_theme_color_override(state, Color.TRANSPARENT)
		else: control.remove_theme_color_override(state)
	for state in ["icon_normal_color", "icon_focus_color", "icon_pressed_color"]: control.add_theme_color_override(state, StudioTheme.TEXT2)
	control.add_theme_color_override("icon_hover_color", StudioTheme.TEXT)

func set_codex_compact(on: bool) -> void:
	# Neon Simple: Codex's view controls stay available but icon-only (lighting, Frame scene, Scene
	# setup) and Frame / 3×3 share one Guides menu, so the pill fits beside the tools on one line.
	# Advanced keeps every labelled control.
	if codex_compact == on or lighting_choice == null: return
	codex_compact = on
	compact_option(lighting_choice, on, ["sky"])
	# Icon-only chips stay 32 px tall with a tighter pad and gap, so the pill leaves room for the
	# stage footer's Pose legend (Advanced keeps the labelled chips and their padding).
	var chip_pad := Vector4(5 if on else 10, 0, 5 if on else 10, 0)
	for control in [lighting_choice, scene_view.choice if scene_view else null]:
		if control == null: continue
		override_button_boxes(control, StudioTheme.flat(StudioTheme.FIELD, StudioTheme.LINE2, 8, 1, chip_pad), StudioTheme.flat(Color("21252f"), StudioTheme.LINE3, 8, 1, chip_pad), StudioTheme.flat(StudioTheme.RAISE, StudioTheme.LINE2, 8, 1, chip_pad), StudioTheme.flat(Color("0f1116"), StudioTheme.LINE, 8, 1, chip_pad))
		control.add_theme_constant_override("h_separation", 2 if on else 4)
	if lighting_choice.get_parent() is BoxContainer: lighting_choice.get_parent().add_theme_constant_override("separation", 2 if on else 4)
	if fit_view_button:
		# Icon-only like Frame scene; the tooltip keeps the name.
		fit_view_button.text = "" if on else "Fit view"
		fit_view_button.icon = StudioTheme.icon("reset", Color.WHITE, 16) if on else null
		fit_view_button.add_theme_constant_override("icon_max_width", 16)
		fit_view_button.custom_minimum_size.x = 32 if on else 0
		fit_view_button.tooltip_text = "Fit view: back to the whole frame (undo zoom and pan)"
		override_button_colors(fit_view_button, StudioTheme.TEXT2, StudioTheme.TEXT, Color.WHITE)
	if frame_scene_button:
		frame_scene_button.text = "" if on else "Frame scene"
		frame_scene_button.icon = StudioTheme.icon("frame-target", Color.WHITE, 16) if on else null
		frame_scene_button.add_theme_constant_override("icon_max_width", 16)
		frame_scene_button.custom_minimum_size.x = 32 if on else 0
		override_button_colors(frame_scene_button, StudioTheme.TEXT2, StudioTheme.TEXT, Color.WHITE)
	if scene_view:
		compact_option(scene_view.choice, on, ["scene", "camera"])
		scene_view.compact = on
		if scene_view.guides_button:
			scene_view.guides_button.icon = StudioTheme.icon("grid", Color.WHITE, 16)
			scene_view.guides_button.add_theme_constant_override("icon_max_width", 16)
		scene_view.sync()
	queue_view_fit()

var codex_footer := false
var codex_footer_none: ImageTexture

func set_codex_footer(on: bool) -> void:
	# Neon Simple, Codex pill in the stage footer: no dropdown chevrons (the popups and tooltips stay),
	# 30 px chips and a 2 px gap, so the Pose legend keeps its "Handles" title at 1440x900. The normal
	# look comes back when the pill returns to the view row.
	if codex_footer == on or codex_pill == null or codex_pill.get_child_count() == 0: return
	codex_footer = on
	if codex_footer_none == null: codex_footer_none = ImageTexture.create_from_image(Image.create(1, 1, false, Image.FORMAT_RGBA8))
	for control in [lighting_choice, scene_view.choice if scene_view else null]:
		if control == null: continue
		if on:
			control.add_theme_icon_override("arrow", codex_footer_none)
			control.add_theme_constant_override("arrow_margin", 0)
		else:
			control.remove_theme_icon_override("arrow")
			control.remove_theme_constant_override("arrow_margin")
	(codex_pill.get_child(0) as Control).add_theme_constant_override("separation", 2 if on else 4)  # the view toolbar
	for control in codex_pill.find_children("*", "Button", true, false):
		if on and control.custom_minimum_size.y == 32: control.custom_minimum_size.y = 30; control.set_meta("footer_chip", true)
		elif not on and control.has_meta("footer_chip"): control.custom_minimum_size.y = 32; control.remove_meta("footer_chip")

func sync_tool_look(control: Button) -> void:
	# Active tool: 600 white label, glow and brighter keycap; written only when the state changes.
	var on := control.button_pressed
	if control.has_meta("on") and control.get_meta("on") == on: return
	control.set_meta("on", on)
	control.add_theme_font_override("font", StudioTheme.font(600 if on else 500))
	(control.get_meta("glow") as Control).visible = on
	if control.has_meta("kbd"): (control.get_meta("kbd") as Label).add_theme_color_override("font_color", Color("c9ceda") if on else StudioTheme.TEXT2)

func set_tool_compact(on: bool) -> void:
	# Narrow centre column (under ~1000 px): tools show icon + keycap, Camera / Pose help icon-only.
	if tool_compact == on: return
	tool_compact = on
	for control in tool_buttons + pose_buttons + ([turn_button] if turn_button else []): control.text = "" if on else control.get_meta("label")
	for control in [camera_help_button, pose_help_button]:
		if control: control.text = "" if on else control.get_meta("label")
	if camera_hint: camera_hint.visible = not on and camera_strip.visible

func queue_view_fit() -> void:
	if view_row == null or view_fit_pending: return
	view_fit_pending = true
	fit_view_row.call_deferred()

func fit_view_row() -> void:
	# One line when everything fits (leads, Codex pill, badges); otherwise the Codex pill, then the
	# badges, move to a second line. Badges stay right-aligned; nothing here changes behaviour.
	view_fit_pending = false
	if view_row == null: return
	var avail: float = view_scroll.size.x - (stage_view_margin.get_theme_constant("margin_left") + stage_view_margin.get_theme_constant("margin_right") if stage_view_margin else 24)
	if avail <= 0: return
	set_tool_compact(avail < 976)
	for control in tool_buttons: set_tool_kbd(control)
	var gap := 8.0
	var leads := [tool_pill, camera_pill, pose_pill].filter(func(p): return p.visible)
	var lead_w := 0.0
	for p in leads: lead_w += p.get_combined_minimum_size().x + gap
	if camera_hint and camera_hint.visible: lead_w += camera_hint.get_combined_minimum_size().x + gap
	# Measured in its normal look: the footer-only compact look (set_codex_footer) must not decide
	# whether the pill fits in the row, or it would flip between the two places.
	var was_footer := codex_footer
	set_codex_footer(false)
	var codex_w: float = codex_pill.get_combined_minimum_size().x + gap
	set_codex_footer(was_footer)
	# + gap: the row's separation before the expanding spacer that pushes the badges right.
	var badge_w: float = badges.get_combined_minimum_size().x + gap
	var codex_row: Control = view_row
	var badge_row := view_row
	# Neon Simple: one floating row like the mock. When the Codex pill does not fit beside the tools
	# and badges it moves into the stage footer (right side); the second line is only a fallback.
	var footer_ok := footer_tools != null and not advanced_mode
	if lead_w + codex_w + badge_w <= avail: pass
	elif footer_ok and not leads.is_empty() and lead_w + badge_w <= avail: codex_row = footer_tools
	elif not leads.is_empty() and lead_w + badge_w <= avail: codex_row = view_row2
	elif leads.is_empty(): badge_row = view_row2
	else: codex_row = footer_tools if footer_ok else view_row2; badge_row = view_row2
	for item in [[codex_pill, codex_row], [badges, badge_row]]:
		if item[0].get_parent() != item[1]: item[0].reparent(item[1], false)
	set_codex_footer(codex_row == footer_tools)
	view_row.move_child(view_spacer, view_row.get_child_count() - 1)
	view_row2.move_child(view_spacer2, view_row2.get_child_count() - 1)
	if codex_row == view_row: view_row.move_child(codex_pill, pose_pill.get_index() + 1 if pose_pill else 3)
	elif codex_row == view_row2: view_row2.move_child(codex_pill, 0)
	badge_row.move_child(badges, badge_row.get_child_count() - 1)
	var two_rows := codex_row == view_row2 or badge_row == view_row2
	if view_row2.visible != two_rows: view_row2.visible = two_rows
	fit_stage_footer()

func badge_panel(parent: Node) -> HBoxContainer:
	# h32, pad 0 12, r6, rgba(10,11,15,.86), 1 px rgba(255,255,255,.1); gap 8.
	var panel := PanelContainer.new()
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.custom_minimum_size.y = 32
	panel.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	panel.add_theme_stylebox_override("panel", StudioTheme.flat(Color(10 / 255.0, 11 / 255.0, 15 / 255.0, 0.86), Color(1, 1, 1, 0.1), 6, 1, Vector4(12, 0, 12, 0)))
	parent.add_child(panel)
	var row := HBoxContainer.new()
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_theme_constant_override("separation", 8)
	panel.add_child(row)
	return row

func build_view_badges() -> void:
	# Right end of the view row (mouse ignored): "● Frame N · S.SS s" and the mode badge.
	view_spacer = Control.new()
	view_spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	view_spacer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	view_row.add_child(view_spacer)
	view_spacer2 = Control.new()
	view_spacer2.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	view_spacer2.mouse_filter = Control.MOUSE_FILTER_IGNORE
	view_row2.add_child(view_spacer2)
	badges = HBoxContainer.new()
	badges.name = "ViewBadges"
	badges.mouse_filter = Control.MOUSE_FILTER_IGNORE
	badges.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	badges.add_theme_constant_override("separation", 8)
	view_row.add_child(badges)
	var frame_row := badge_panel(badges)
	var dot := TextureRect.new()
	dot.texture = StudioTheme.neon_dot(7)
	dot.stretch_mode = TextureRect.STRETCH_KEEP_CENTERED
	dot.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	dot.mouse_filter = Control.MOUSE_FILTER_IGNORE
	frame_row.add_child(dot)
	frame_badge_frame = overlay_label(frame_row, "Frame 0", StudioTheme.TEXT, 12, 500, true)
	overlay_label(frame_row, "·", StudioTheme.TEXT2, 12, 500, true)
	frame_badge_time = overlay_label(frame_row, "0.00 s", StudioTheme.TEXT, 12, 500, true)
	var mode_row := badge_panel(badges)
	mode_badge_lead = overlay_label(mode_row, "", StudioTheme.TEXT2, 12, 500)
	mode_badge_chip = Panel.new()
	mode_badge_chip.custom_minimum_size = Vector2(10, 10)
	mode_badge_chip.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	mode_badge_chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	mode_badge_chip.add_theme_stylebox_override("panel", StudioTheme.flat(StudioTheme.DRAWING, Color.TRANSPARENT, 3, 0))
	mode_row.add_child(mode_badge_chip)
	mode_badge_diamond = TextureRect.new()
	mode_badge_diamond.stretch_mode = TextureRect.STRETCH_KEEP_CENTERED
	mode_badge_diamond.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	mode_badge_diamond.mouse_filter = Control.MOUSE_FILTER_IGNORE
	mode_row.add_child(mode_badge_diamond)
	mode_badge_value = overlay_label(mode_row, "", StudioTheme.TEXT, 12, 500)

func set_label_text(target: Label, text: String) -> bool:
	if target.text == text: return false
	target.text = text
	return true

func pose_badge_text() -> String:
	var rig = pose_editor.active_rig()
	if rig == null: return "No model"
	var model := str(rig.data.get("name", "Model"))
	var bone: String = pose_editor.selected
	if bone == "@root" or not pose_editor.tree_items.has(bone) or not is_instance_valid(pose_editor.tree_items[bone]): return model
	return model + " · " + pose_editor.tree_items[bone].get_text(0)

func aspect_text() -> String:
	var w := int(video.width)
	var h := int(video.height)
	if w <= 0 or h <= 0: return "?"
	var a := w
	var b := h
	while b != 0:
		var t := b
		b = a % b
		a = t
	if w / a <= 32 and h / a <= 32: return "%d:%d" % [w / a, h / a]
	return "%.2f:1" % (float(w) / h)

func lens_mm() -> float:
	# Display only: lens length for a 36 mm-wide full-frame sensor from the horizontal angle of view
	# (the mock's 54° horizontal reads 35 mm). The camera keeps its FOV; nothing is stored.
	var cam: Camera3D = renderer.camera
	var aspect := float(video.width) / maxf(1.0, float(video.height))
	var half := tan(deg_to_rad(cam.fov) / 2.0)
	var horizontal := half if cam.keep_aspect == Camera3D.KEEP_WIDTH else half * aspect
	return 18.0 / maxf(horizontal, 0.0001)

func refresh_badges() -> void:
	# Badges, stage caption and legend: computed every frame, written only when their text changes.
	if badges == null or mode == null: return
	var seconds := float(frame) * float(video.fps_den) / maxf(1.0, float(video.fps_num))
	# Mono badge: its width only changes with the number of digits, so the row is refitted only then.
	var before := badges.get_combined_minimum_size().x
	var width_changed := false
	var frame_changed := set_label_text(frame_badge_frame, "Frame %d" % frame)
	var time_changed := set_label_text(frame_badge_time, "%.2f s" % seconds)
	if frame_changed or time_changed:
		width_changed = badges.get_combined_minimum_size().x != before
	var lead := ""
	var marker := ""
	var value := ""
	match mode.selected:
		0:
			lead = "Drawing on"; marker = "chip"
			value = str(layers[active_layer].name) if active_layer >= 0 and active_layer < layers.size() else "No layer"
		1:
			var keyed := keys.any(func(k): return int(k.frame) == frame)
			marker = "camera" if keyed else ""
			value = "Camera key on this frame" if keyed else "No camera key here"
		_:
			lead = "Posing"; marker = "model"; value = pose_badge_text()
	var key := "%s|%s|%s" % [lead, marker, value]
	if key != mode_badge_key:
		mode_badge_key = key
		mode_badge_lead.text = lead
		mode_badge_lead.visible = not lead.is_empty()
		mode_badge_chip.visible = marker == "chip"
		mode_badge_diamond.visible = marker in ["camera", "model"]
		if mode_badge_diamond.visible: mode_badge_diamond.texture = StudioTheme.diamond(StudioTheme.CAMERA if marker == "camera" else StudioTheme.MODEL, 10)
		mode_badge_value.text = value
		mode_badge_value.add_theme_color_override("font_color", StudioTheme.TEXT2 if mode.selected == 1 and marker.is_empty() else StudioTheme.TEXT)
		width_changed = true
	if width_changed: queue_view_fit()
	refresh_stage_footer()

func build_stage_footer(center: Control) -> void:
	# Stage footer row (h40, under the canvas): camera caption left, status toast centred, legend right.
	# The toast is placed by fit_stage_footer() inside a plain Control, so a long message never adds to
	# the window's minimum width.
	var margin := MarginContainer.new()
	margin.name = "StageFooter"
	for side in [["left", 16], ["right", 16], ["top", 0], ["bottom", 8]]: margin.add_theme_constant_override("margin_" + side[0], side[1])
	margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	center.add_child(margin)
	if center == stage_overlay:
		# Floats over the bottom of the canvas and grows upwards with a wrapped toast.
		margin.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
		margin.grow_vertical = Control.GROW_DIRECTION_BEGIN
		margin.resized.connect(queue_stage_inset)
	stage_footer = Control.new()
	stage_footer.custom_minimum_size.y = 40
	stage_footer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	margin.add_child(stage_footer)
	var row := HBoxContainer.new()
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_theme_constant_override("separation", 12)
	stage_footer.add_child(row)
	row.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	footer_left = HBoxContainer.new()
	footer_left.mouse_filter = Control.MOUSE_FILTER_IGNORE
	footer_left.add_theme_constant_override("separation", 8)
	footer_left.clip_contents = true
	row.add_child(footer_left)
	overlay_icon(footer_left, "camera", StudioTheme.TEXT2, 14)
	scene_name = overlay_label(footer_left, "", StudioTheme.TEXT2, 12)
	scene_name.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	view_caption = overlay_label(footer_left, "", StudioTheme.TEXT2, 12)
	view_caption.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	view_caption.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	var gap := Control.new()
	gap.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	gap.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(gap)
	legend = HBoxContainer.new()
	legend.mouse_filter = Control.MOUSE_FILTER_IGNORE
	legend.add_theme_constant_override("separation", 14)
	legend.visible = false
	row.add_child(legend)
	legend_title = overlay_label(legend, "", StudioTheme.TEXT2, 12)
	for i in 2:
		var item := HBoxContainer.new()
		item.mouse_filter = Control.MOUSE_FILTER_IGNORE
		item.add_theme_constant_override("separation", 6)
		legend.add_child(item)
		var ring := TextureRect.new()
		ring.stretch_mode = TextureRect.STRETCH_KEEP_CENTERED
		ring.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		ring.mouse_filter = Control.MOUSE_FILTER_IGNORE
		item.add_child(ring)
		legend_items.append([ring, overlay_label(item, "", StudioTheme.TEXT2, 12)])
	footer_tools = HBoxContainer.new()
	footer_tools.name = "StageFooterTools"
	footer_tools.mouse_filter = Control.MOUSE_FILTER_IGNORE
	footer_tools.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(footer_tools)
	toast = PanelContainer.new()
	toast.name = "StatusToast"
	toast.mouse_filter = Control.MOUSE_FILTER_PASS # tooltip only: shows the full message when it is cut
	stage_footer.add_child(toast)
	var toast_row := HBoxContainer.new()
	toast_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	toast_row.add_theme_constant_override("separation", 10)
	toast.add_child(toast_row)
	toast_icon = TextureRect.new()
	toast_icon.texture = StudioTheme.toast_ring(false)
	toast_icon.stretch_mode = TextureRect.STRETCH_KEEP_CENTERED
	toast_icon.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	toast_icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
	toast_row.add_child(toast_icon)
	toast_lead = overlay_label(toast_row, "", StudioTheme.TEXT, 13, 600)
	toast_lead.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	toast_rest = overlay_label(toast_row, "", StudioTheme.TEXT2, 13)
	toast_rest.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	toast_rest.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	toast_strip = StudioTheme.neon_line(128)
	toast.draw.connect(draw_toast_strip)
	stage_footer.resized.connect(fit_stage_footer)

func queue_stage_inset() -> void:
	if stage_overlay == null or stage_inset_pending: return
	stage_inset_pending = true
	fit_stage_inset.call_deferred()

func fit_stage_inset() -> void:
	# Mock: frame inset 48 px at the sides and about 63 px top and bottom, so the pills, badges, caption
	# and toast float over the dimmed scene around the frame. The inset is symmetric (a centred
	# perspective camera keeps its frame centred) and never smaller than the overlays above and below.
	stage_inset_pending = false
	if stage_overlay == null or canvas == null: return
	var footer: Control = stage_footer.get_parent() if stage_footer else null
	var top_h := stage_top.get_combined_minimum_size().y if stage_top else 0.0
	var foot_h := footer.get_combined_minimum_size().y if footer else 0.0
	var inset := Vector2(minf(48.0, canvas.size.x * 0.05), minf(maxf(top_h, foot_h) + 10.0, canvas.size.y * 0.3))
	inset = inset.floor()
	if empty_hint and empty_hint.position.y != inset.y + 8: empty_hint.position.y = inset.y + 8
	if canvas.fit_inset != inset:
		canvas.fit_inset = inset
		canvas.queue_redraw()
	# Mock: the tool pill starts at the frame's left edge and the badges end at its right edge; the
	# stage caption and legend line up the same way (unzoomed frame; at least 12 px from the edge).
	var fit: Vector2 = canvas.fit_area(canvas.size)
	var frame_w: float = canvas.resolution.x * minf(fit.x / canvas.resolution.x, fit.y / canvas.resolution.y)
	var side := 12.0 if advanced_mode else clampf(floorf((canvas.size.x - frame_w) / 2.0), 12.0, 160.0)
	for holder in [stage_view_margin, footer]:
		if holder == null: continue
		for edge in ["margin_left", "margin_right"]:
			if absf(holder.get_theme_constant(edge) - side) > 1.0:
				holder.add_theme_constant_override(edge, int(side))
				queue_view_fit()

func refresh_stage_footer() -> void:
	# Simple caption "Camera view · W:H" (+ lens in Camera); Advanced keeps Codex's scene_name text.
	if stage_footer == null: return
	var caption := "Camera view · " + aspect_text()
	if mode.selected == 1: caption += " · %d mm" % roundi(lens_mm())
	var changed := set_label_text(view_caption, caption)
	if scene_name.visible != advanced_mode: scene_name.visible = advanced_mode; changed = true
	if view_caption.visible == advanced_mode: view_caption.visible = not advanced_mode; changed = true
	var kind := ""
	if mode.selected == 0 and onion_editor and onion_editor.enabled and onion_editor.enabled.button_pressed: kind = "onion"
	elif mode.selected == 2: kind = "pose"
	if kind != legend_key:
		legend_key = kind
		legend_wanted = not kind.is_empty()
		if kind == "onion":
			legend_title.text = "Onion skin"
			legend_items[0][0].texture = StudioTheme.ring_icon(StudioTheme.DRAWING, 10); legend_items[0][1].text = "Before"
			legend_items[1][0].texture = StudioTheme.ring_icon(StudioTheme.CAMERA, 10); legend_items[1][1].text = "After"
		elif kind == "pose":
			legend_title.text = "Handles"
			legend_items[0][0].texture = StudioTheme.ring_icon(Color.WHITE, 10); legend_items[0][1].text = "Joint"
			legend_items[1][0].texture = StudioTheme.selected_handle_icon(14); legend_items[1][1].text = "Selected"
		changed = true
	if changed: fit_stage_footer()

func toast_natural_width() -> float:
	var lead_w := StudioTheme.font(600).get_string_size(toast_lead.text, HORIZONTAL_ALIGNMENT_LEFT, -1, 13).x
	var rest_w := StudioTheme.font(400).get_string_size(toast_rest.text, HORIZONTAL_ALIGNMENT_LEFT, -1, 13).x
	return 10 + 22 + 10 + ceilf(lead_w) + (10 + ceilf(rest_w) if not toast_rest.text.is_empty() else 0.0) + 16 + 2

func fit_stage_footer() -> void:
	# Simple: the toast is centred under the frame at its natural width, clamped so it never covers
	# the legend; the legend hides first when the stage is too narrow. Advanced: status is a plain
	# line between Codex's scene caption and the legend.
	if stage_footer == null or toast == null: return
	var width := stage_footer.size.x
	if width <= 0: return
	var caption: Label = scene_name if advanced_mode else view_caption
	var caption_w := StudioTheme.font(400).get_string_size(caption.text, HORIZONTAL_ALIGNMENT_LEFT, -1, 12).x + 24
	var legend_w := 0.0
	legend.visible = legend_wanted
	legend_title.visible = true
	if legend_wanted: legend_w = legend.get_combined_minimum_size().x
	var x := 0.0
	var w := 0.0
	if advanced_mode:
		caption_w = minf(caption_w, width * 0.35)
		x = caption_w + 12
		w = maxf(0.0, width - x - legend_w - 12)
	else:
		var want := toast_natural_width()
		var tools_w := footer_tools.get_combined_minimum_size().x if footer_tools and footer_tools.get_child_count() > 0 else 0.0
		# Left and right are reserved separately: the caption (at most 170 px) on the left, the Codex
		# view pill and the legend on the right. Centred under the frame when that fits; otherwise the
		# toast sits in the free gap between them; the legend hides only when the toast would be cut.
		var left := minf(caption_w, 210.0)  # room for "Camera view · 16:9 · 35 mm" with its icon
		var right := legend_w + (tools_w + 12.0 if tools_w > 0 and legend_wanted else tools_w)
		if legend_wanted and width - left - right - 24 < want:
			# First drop the legend's title ("Handles" / "Onion skin"), then the whole legend.
			var title_w := legend_title.get_combined_minimum_size().x + float(legend.get_theme_constant("separation"))
			if legend_title.visible and width - left - (right - title_w) - 24 >= want:
				legend_title.visible = false
				legend_w -= title_w
				right -= title_w
			else:
				legend.visible = false
				legend_w = 0.0
				right = tools_w
		var gap := maxf(0.0, width - left - right - 24)
		w = clampf(want, 0.0, gap)
		x = floorf((width - w) / 2.0)
		if x < left + 12 or x + w > width - right - 12: x = left + 12 + floorf((gap - w) / 2.0)
		caption_w = maxf(0.0, x - 12)
		# Still too narrow: wrap the grey part to a second line instead of cutting it with "..." when two
		# lines hold it; narrower than that it stays one cut line (the full text is in the tooltip).
		var rest_w := ceilf(StudioTheme.font(400).get_string_size(toast_rest.text, HORIZONTAL_ALIGNMENT_LEFT, -1, 13).x)
		var rest_room := w - (want - rest_w)
		var wrap := w < want - 0.5 and rest_room >= 80.0 and rest_room * 2.0 >= rest_w + 24.0
		toast_rest.max_lines_visible = 2
		var wrap_mode := TextServer.AUTOWRAP_WORD_SMART if wrap else TextServer.AUTOWRAP_OFF
		if toast_rest.autowrap_mode != wrap_mode:
			toast_rest.autowrap_mode = wrap_mode
			toast_rest.text_overrun_behavior = TextServer.OVERRUN_NO_TRIMMING if wrap else TextServer.OVERRUN_TRIM_ELLIPSIS
		var lead_w := ceilf(StudioTheme.font(600).get_string_size(toast_lead.text, HORIZONTAL_ALIGNMENT_LEFT, -1, 13).x)
		toast_lead.custom_minimum_size.x = clampf(lead_w, 0.0, maxf(0.0, w - 60))
	footer_left.custom_minimum_size.x = caption_w
	toast.position = Vector2(x, 0)
	toast.size = Vector2(w, 40)
	var height := maxf(40.0, toast.get_combined_minimum_size().y)
	if toast.size.y != height: toast.size.y = height
	if stage_footer.custom_minimum_size.y != height: stage_footer.custom_minimum_size.y = height

func split_status(text: String) -> PackedStringArray:
	# First sentence (or the part before the first ": ") in bold, the rest in grey.
	var cut := -1
	for mark in [". ", "! ", "? ", ": "]:
		var at := text.find(mark)
		if at > 0 and (cut < 0 or at < cut): cut = at
	if cut < 0: return PackedStringArray([text, ""])
	return PackedStringArray([text.substr(0, cut + 1), text.substr(cut + 2).strip_edges()])

func refresh_toast() -> void:
	# status.text stays the source of truth and is never cleared. Simple: neon toast (coral ring and
	# #FF5A7A border for problems) mirroring it; Advanced: status itself as a plain line.
	var problem := is_problem_message(status.text)
	status.visible = advanced_mode
	# Alpha does not remove a Control from hit testing. Only a displayed Simple toast needs a tooltip.
	toast.mouse_filter = Control.MOUSE_FILTER_PASS if not advanced_mode and not status.text.is_empty() and not status_faded else Control.MOUSE_FILTER_IGNORE
	toast_icon.visible = not advanced_mode
	toast_lead.visible = not advanced_mode
	if advanced_mode:
		toast_rest.visible = false
		toast.add_theme_stylebox_override("panel", StyleBoxEmpty.new())
		toast.modulate.a = 1.0
		if toast_tween: toast_tween.kill()
		set_toast_progress(0.0)
	else:
		var parts := split_status(status.text)
		toast_lead.text = parts[0]
		toast_rest.text = parts[1]
		toast_rest.visible = true
		toast_icon.texture = StudioTheme.toast_ring(problem, "hand" if status.text == POSE_HINT else "check")
		toast.add_theme_stylebox_override("panel", StudioTheme.flat(StudioTheme.POPUP, StudioTheme.PROBLEM if problem else StudioTheme.LINE2, 10, 1, Vector4(10, 0, 16, 0), Color(0, 0, 0, 0.8), 11, Vector2(0, 12)))
		toast.modulate.a = 0.0 if status.text.is_empty() or status_faded else 1.0
	toast.tooltip_text = "" if advanced_mode else status.text
	fit_stage_footer()

func set_toast_progress(value: float) -> void:
	toast_progress = value
	if toast: toast.queue_redraw()

func draw_toast_strip() -> void:
	# 2 px neon strip along the toast's bottom edge (inset past the rounded corners).
	if toast_progress <= 0.0 or advanced_mode or toast_strip == null: return
	var width := (toast.size.x - 12.0) * toast_progress
	if width > 0.5: toast.draw_texture_rect(toast_strip, Rect2(6, toast.size.y - 3, width, 2), false)

func draw_viewfinder() -> void:
	# Gradient viewfinder corners 7 px outside the visible camera frame: 22 px arms, 2.5 px, round
	# caps. TL #2E8CFF, TR / BL #9C5CFF, BR #FF3D9A (mock: M41 81V59H63 for a frame at 48,66).
	if viewfinder == null or canvas == null: return
	var frame_rect: Rect2 = canvas.image_rect().intersection(Rect2(Vector2.ZERO, canvas.size))
	if frame_rect.size.x < 8 or frame_rect.size.y < 8: return
	frame_rect = frame_rect.grow(7)
	var arm := 22.0
	var corners := [[frame_rect.position, Vector2(0, 1), Vector2(1, 0), StudioTheme.BLUE], [Vector2(frame_rect.end.x, frame_rect.position.y), Vector2(-1, 0), Vector2(0, 1), StudioTheme.MID], [Vector2(frame_rect.position.x, frame_rect.end.y), Vector2(0, -1), Vector2(1, 0), StudioTheme.MID], [frame_rect.end, Vector2(-1, 0), Vector2(0, -1), StudioTheme.PINK]]
	for corner in corners:
		var p: Vector2 = corner[0]
		var points := PackedVector2Array([p + corner[1] * arm, p, p + corner[2] * arm])
		viewfinder.draw_polyline(points, corner[3], 2.5, true)
		for q in points: viewfinder.draw_circle(q, 1.25, corner[3])

func style_empty_hint() -> void:
	# Neon: #111318 card, 1 px #2C303B, r10, #F4F6FA text. Classic: the old pale rounded card.
	if empty_hint == null: return
	if StudioTheme.is_neon():
		empty_hint.add_theme_stylebox_override("panel", StudioTheme.flat(StudioTheme.PANEL, StudioTheme.LINE2, 10, 1, Vector4(14, 14, 14, 14)))
		if empty_hint_label: empty_hint_label.add_theme_color_override("font_color", StudioTheme.TEXT)
		return
	var hint_style := StyleBoxFlat.new()
	hint_style.bg_color = StudioTheme.tone(Color(0.93, 0.96, 0.99, 0.92))
	hint_style.set_corner_radius_all(10)
	hint_style.set_content_margin_all(14)
	empty_hint.add_theme_stylebox_override("panel", hint_style)
	if empty_hint_label: empty_hint_label.remove_theme_color_override("font_color")

func advanced_spin(parent: Node, text: String, low: float, high: float, value: float) -> SpinBox:
	var row := VBoxContainer.new()
	parent.add_child(row)
	advanced(row)
	return spin(row, text, low, high, value)

func section(parent: Node, title: String, kind: String) -> VBoxContainer:
	# Neon Pro step 5: flat sections (padding 18 16, bottom hairline, 12/600 heading, no icon).
	if StudioTheme.is_neon(): return inspector_block(parent, title)
	var panel := PanelContainer.new()
	parent.add_child(panel)
	var box := VBoxContainer.new()
	panel.add_child(box)
	var heading := HBoxContainer.new()
	box.add_child(heading)
	var image := TextureRect.new()
	image.texture = StudioTheme.icon(kind)
	image.custom_minimum_size = Vector2(24, 24)
	image.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	image.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	heading.add_child(image)
	label(heading, title).add_theme_font_size_override("font_size", 16)
	return box

# ---- Neon Pro step 5: right inspector, Draw panel -----------------------------------------
# Built once at start-up in the neon style, after every editor has added its controls to
# drawing_section. Codex's controls are moved and restyled, never replaced: tool, color, radius,
# brush_opacity, brush_pressure, layer_choice, layer_visibility, the onion switch, Layers…, the
# palette, the tool panels and every Advanced control keep their types, values, signals and
# Simple/Advanced visibility. Classic styles keep the old single "Drawing" card.

const TOOL_TITLES := ["Pen", "Eraser", "Fill", "Pick color", "Select area"]
const TOOL_HINTS := ["Smooth freehand lines", "Clear ink from this drawing", "Fill a closed area", "Take a colour from the picture", "Move or cut part of the drawing"]
const TOOL_ICONS := ["draw", "eraser", "fill", "picker", "select"]
const TOOL_KEYS := ["pen", "eraser", "fill", "sample", "select"]
const COLOUR_NAMES := {"f4dfbd": "Warm white", "ff5a7a": "Coral", "ffc24b": "Sun yellow", "4da3ff": "Sky blue", "4b3f66": "Ink"}
var draw_inspector := {}  # neon only: inspector card nodes and the values they last showed
# Recent colours are a per-session UI convenience (never project or palette data): the four colours
# used before the current one, seeded with the mock's coral, sun yellow, sky blue and ink.
var recent_colors: Array = [Color("ff5a7a"), Color("ffc24b"), Color("4da3ff"), Color("4b3f66")]
var recent_base := Color()
var color_popup_open := false

func inspector_box(pad := Vector4(16, 18, 16, 18), top_line := false, bottom_line := true) -> StyleBoxFlat:
	# Flat inspector section: #0C0D11 with a 1 px #22252E hairline below (or above). The right pad
	# gives up the scrollbar's width while it shows (fit_inspector_pad), so content keeps 16 px.
	var box := StudioTheme.flat(StudioTheme.BAR, StudioTheme.LINE, 0, 0, pad)
	box.border_width_top = 1 if top_line else 0
	box.border_width_bottom = 1 if bottom_line else 0
	box.set_meta("pad_right", pad.z)
	box.content_margin_right = maxf(0.0, pad.z - inspector_bar_width)
	inspector_boxes.append(box)
	return box

var inspector_boxes: Array = []
var inspector_holders: Array = []  # inspector_card margins (16 px sides), same right-pad rule
var inspector_bar_width := 0.0

func fit_inspector_pad() -> void:
	var bar := inspector_scroll.get_v_scroll_bar()
	var width := bar.get_combined_minimum_size().x if bar.visible else 0.0
	if is_equal_approx(width, inspector_bar_width): return
	inspector_bar_width = width
	for box in inspector_boxes: box.content_margin_right = maxf(0.0, float(box.get_meta("pad_right", 16.0)) - width)
	for holder in inspector_holders:
		if is_instance_valid(holder): holder.add_theme_constant_override("margin_right", int(16 - width))

func inspector_block(parent: Node, title: String, meta := "") -> VBoxContainer:
	# Padding 18 16, bottom hairline, heading 12/600 #B4BAC7 with an optional right meta 12/500
	# #8C93A3 (section_meta() returns it so callers can fill it).
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", inspector_box())
	parent.add_child(panel)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 8)
	panel.add_child(box)
	if title.is_empty(): return box
	var heading := HBoxContainer.new()
	heading.custom_minimum_size.y = 20
	heading.add_theme_constant_override("separation", 8)
	box.add_child(heading)
	var name_label := overlay_label(heading, title, StudioTheme.TEXT2, 12, 600)
	name_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var meta_label := overlay_label(heading, meta, StudioTheme.TEXT3, 12, 500)
	meta_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	box.set_meta("heading", heading)
	box.set_meta("title", name_label)
	box.set_meta("meta", meta_label)
	return box

func section_meta(box: Control) -> Label:
	return box.get_meta("meta") if box.has_meta("meta") else null

func move_to(control: Node, parent: Node) -> Node:
	if control.get_parent(): control.get_parent().remove_child(control)
	parent.add_child(control)
	return control

func style_value_field(field: SpinBox, suffix: String) -> void:
	# The SpinBox stays (tests and keyboard entry use it) as a flat right-aligned 12/500 value with a
	# unit, e.g. "6 px" (SpinBox adds the space before the suffix); the slider beside it does the
	# dragging, so the arrows are hidden.
	field.suffix = suffix
	field.alignment = HORIZONTAL_ALIGNMENT_RIGHT
	field.custom_minimum_size = Vector2(68, 24)
	field.size_flags_horizontal = Control.SIZE_SHRINK_END
	field.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	var none := ImageTexture.create_from_image(Image.create(1, 1, false, Image.FORMAT_RGBA8))
	for state in ["updown", "up", "up_hover", "up_pressed", "up_disabled", "down", "down_hover", "down_pressed", "down_disabled"]: field.add_theme_icon_override(state, none)
	for state in ["up_background", "up_background_hovered", "up_background_pressed", "up_background_disabled", "down_background", "down_background_hovered", "down_background_pressed", "down_background_disabled", "field_and_buttons_separator", "up_down_buttons_separator"]: field.add_theme_stylebox_override(state, StyleBoxEmpty.new())
	for constant in ["buttons_width", "field_and_buttons_separation", "buttons_vertical_separation", "set_min_buttons_width_from_icons"]: field.add_theme_constant_override(constant, 0)
	var edit := field.get_line_edit()
	edit.add_theme_constant_override("minimum_character_width", 0)
	edit.add_theme_font_override("font", StudioTheme.font(500))
	edit.add_theme_font_size_override("font_size", 12)
	edit.add_theme_color_override("font_color", StudioTheme.TEXT2)
	edit.add_theme_stylebox_override("normal", StudioTheme.flat(Color.TRANSPARENT, Color.TRANSPARENT, 6, 0, Vector4(4, 2, 2, 2)))

func bound_slider(parent: Node, field: SpinBox) -> HSlider:
	# Neon slider two-way bound to an existing SpinBox (the SpinBox stays the source of truth).
	var slider := HSlider.new()
	slider.min_value = field.min_value
	slider.max_value = field.max_value
	slider.step = 1
	slider.value = field.value
	slider.focus_mode = Control.FOCUS_NONE  # arrow keys keep stepping frames
	slider.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	slider.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	slider.custom_minimum_size.y = 40
	slider.tooltip_text = field.tooltip_text
	slider.value_changed.connect(func(value):
		if field.value != value: field.value = value)
	field.value_changed.connect(func(value): slider.set_value_no_signal(value))
	parent.add_child(slider)
	return slider

func style_switch_row(control: CheckButton, kind: String, height := 40, sub_line := false) -> Control:
	# Switch row h40: 16 px #8C93A3 icon, 13 px #F4F6FA label, neon switch on the right. The row
	# bleeds 8 px into the section padding (mock: padding 0 8, margin 0 -8) so the icon and switch
	# line up with the other controls and the hover fill has room.
	control.custom_minimum_size.y = height
	control.add_theme_font_size_override("font_size", 13)
	control.add_theme_font_override("font", StudioTheme.font(400))
	var pad := Vector4(34, 3 if sub_line else 0, 8, 19 if sub_line else 0)
	var clear := StudioTheme.flat(Color.TRANSPARENT, Color.TRANSPARENT, 8, 0, pad)
	var hover := StudioTheme.flat(StudioTheme.HOVER, Color.TRANSPARENT, 8, 0, pad)
	override_button_boxes(control, clear, hover, clear, clear)
	for suffix in ["", "_mirrored"]: control.add_theme_stylebox_override("hover_pressed" + suffix, hover)
	# A long label never widens the 288 px inspector: it is trimmed, the full text stays in the tooltip.
	control.clip_text = true
	control.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	if control.tooltip_text.is_empty(): control.tooltip_text = control.text
	var image := TextureRect.new()
	image.texture = StudioTheme.icon(kind, StudioTheme.TEXT3, 16)
	image.mouse_filter = Control.MOUSE_FILTER_IGNORE
	control.add_child(image)
	image.set_anchors_preset(Control.PRESET_CENTER_LEFT)
	image.offset_left = 8; image.offset_right = 24; image.offset_top = -8; image.offset_bottom = 8
	var bleed := MarginContainer.new()
	bleed.add_theme_constant_override("margin_left", -8)
	bleed.add_theme_constant_override("margin_right", -8)
	if control.get_parent(): control.get_parent().remove_child(control)
	bleed.add_child(control)
	return bleed

func onion_sub_line(control: CheckButton) -> void:
	# "● 1 before ● 1 after" under "Onion skin": the onion shows the previous drawing in blue and the
	# next one in pink (OnionEditor), so the counts describe what the switch turns on.
	var line := HBoxContainer.new()
	line.mouse_filter = Control.MOUSE_FILTER_IGNORE
	line.add_theme_constant_override("separation", 5)
	control.add_child(line)
	line.position = Vector2(34, 24)
	for part in [[StudioTheme.DRAWING, "1 before"], [StudioTheme.CAMERA, "1 after"]]:
		if part[1] == "1 after":
			var gap := Control.new(); gap.custom_minimum_size.x = 1; gap.mouse_filter = Control.MOUSE_FILTER_IGNORE; line.add_child(gap)
		var dot := TextureRect.new()
		dot.texture = StudioTheme.dot(part[0], 7)
		dot.stretch_mode = TextureRect.STRETCH_KEEP_CENTERED
		dot.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		dot.mouse_filter = Control.MOUSE_FILTER_IGNORE
		line.add_child(dot)
		overlay_label(line, part[1], StudioTheme.TEXT2, 12)

func style_outline(control: Button, kind := "", height := 40) -> void:
	# Outline button (theme default) at h40 with 13/500 #F4F6FA text and an optional #8C93A3 icon.
	control.custom_minimum_size.y = height
	control.add_theme_font_override("font", StudioTheme.font(500))
	control.add_theme_font_size_override("font_size", 13)
	for state in ["font_color", "font_focus_color", "font_hover_color", "font_pressed_color", "font_hover_pressed_color"]: control.add_theme_color_override(state, StudioTheme.TEXT)
	if kind.is_empty(): return
	control.icon = StudioTheme.icon(kind, Color.WHITE, 16)
	control.add_theme_constant_override("icon_max_width", 16)
	control.add_theme_constant_override("h_separation", 8)
	for state in ["icon_normal_color", "icon_focus_color", "icon_pressed_color", "icon_hover_pressed_color"]: control.add_theme_color_override(state, StudioTheme.TEXT3)
	control.add_theme_color_override("icon_hover_color", StudioTheme.TEXT2)

func build_tool_card() -> void:
	# 64 px card: 36 px neon-ring tile with the white tool icon and a violet glow, title 15/600,
	# subtitle 12 #B4BAC7, keycap on the right. Driven by tool.selected (refresh_draw_inspector).
	var card := PanelContainer.new()
	card.add_theme_stylebox_override("panel", inspector_box(Vector4(16, 0, 16, 0)))
	card.custom_minimum_size.y = 64
	drawing_section.add_child(card)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 12)
	card.add_child(row)
	var image := neon_tile(row, null, 36, StudioTheme.TOOL_INNER, 1.0, true)
	var text := VBoxContainer.new()
	text.add_theme_constant_override("separation", 2)
	text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	text.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	text.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(text)
	var title := overlay_label(text, "", StudioTheme.TEXT, 15, 600)
	var hint := overlay_label(text, "", StudioTheme.TEXT2, 12)
	var chip := Label.new()
	chip.theme_type_variation = "KbdLabel"
	chip.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	chip.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	chip.custom_minimum_size = Vector2(18, 18)
	chip.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(chip)
	draw_inspector.merge({"tool_icon": image, "tool_title": title, "tool_hint": hint, "tool_kbd": chip, "tool_sig": ""})

func build_colour_block() -> void:
	# Five 40 px tiles, r8, gap 8. Tile 1 is the real ColorPickerButton (it still opens the picker)
	# drawn as the current colour with a 2 px gap and a white ring; tiles 2-5 are recent colours.
	var block := inspector_block(drawing_section, "Colour")
	var grid := GridContainer.new()
	grid.columns = 5
	grid.add_theme_constant_override("h_separation", 8)
	grid.add_theme_constant_override("v_separation", 8)
	block.add_child(grid)
	move_to(color, grid)
	color.custom_minimum_size = Vector2(0, 40)
	color.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	color.self_modulate = Color(1, 1, 1, 0)  # the button's square swatch; the panels below draw it rounded
	var swatch_style := StudioTheme.flat(color.color, Color(1, 1, 1, 0.14), 8, 1, Vector4(0, 0, 0, 0))
	var swatch := Panel.new()
	swatch.mouse_filter = Control.MOUSE_FILTER_IGNORE
	swatch.add_theme_stylebox_override("panel", swatch_style)
	color.add_child(swatch)
	swatch.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var ring_style := StudioTheme.flat(Color.TRANSPARENT, Color.WHITE, 12, 2, Vector4(0, 0, 0, 0))
	ring_style.draw_center = false
	ring_style.set_expand_margin_all(4)
	var ring := Panel.new()
	ring.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ring.add_theme_stylebox_override("panel", ring_style)
	color.add_child(ring)
	ring.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	color.pressed.connect(func(): color_popup_open = true)
	color.popup_closed.connect(func(): color_popup_open = false)
	var tiles: Array = []
	for i in range(4):
		var tile := Button.new()
		tile.focus_mode = Control.FOCUS_NONE
		tile.custom_minimum_size = Vector2(0, 40)
		tile.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		tile.pressed.connect(pick_recent_color.bind(i))
		grid.add_child(tile)
		tiles.append(tile)
	recent_base = color.color
	draw_inspector.merge({"colour_meta": section_meta(block), "swatch": swatch_style, "recent_tiles": tiles, "shown_color": Color(-1, -1, -1, -1)})
	refresh_recent_tiles()

func colour_name(value: Color) -> String:
	var html := value.to_html()
	for row in palette:
		if row.rgba == html: return row.name
	var rgb := value.to_html(false)
	if value.a >= 1.0 and COLOUR_NAMES.has(rgb): return COLOUR_NAMES[rgb]
	return "#" + rgb.to_upper() + ("" if value.a >= 1.0 else " · %d%%" % roundi(value.a * 100))

func refresh_recent_tiles() -> void:
	var tiles: Array = draw_inspector.get("recent_tiles", [])
	for i in range(tiles.size()):
		var value: Color = recent_colors[i]
		var normal := StudioTheme.flat(value, Color(1, 1, 1, 0.14), 8, 1, Vector4(0, 0, 0, 0))
		var hover := StudioTheme.flat(value, Color(1, 1, 1, 0.45), 8, 1, Vector4(0, 0, 0, 0))
		override_button_boxes(tiles[i], normal, hover, hover, normal)
		tiles[i].tooltip_text = "Recent colour: " + colour_name(value)

func pick_recent_color(index: int) -> void:
	# Same guards as a project palette swatch; only the brush colour changes.
	if index >= recent_colors.size() or (palette_editor and not palette_editor.editable()): return
	finish_stroke()
	if color_sampler: color_sampler.cancel()
	color.color = recent_colors[index]

func track_recent_color() -> void:
	# The colour in use before a new one becomes the first recent tile (not while the picker popup
	# is open, so dragging in the picker does not fill the row with in-between colours).
	var current := color.color
	if current == recent_base or color_popup_open: return
	var previous := recent_base
	recent_base = current
	var kept: Array = recent_colors.filter(func(c): return c != current and c != previous)
	kept.push_front(previous)
	recent_colors = kept.slice(0, 4)
	refresh_recent_tiles()

func build_brush_block(children: Array) -> void:
	# "Brush size" + the radius SpinBox as a flat "6 px" value; 40 px preview dot + neon slider.
	# brush_opacity gets the same value + slider row. Codex captions show in Advanced only.
	var block := inspector_block(drawing_section, "Brush size")
	var heading: HBoxContainer = block.get_meta("heading")
	section_meta(block).visible = false
	var radius_caption: Node = children[children.find(radius) - 1]
	move_to(radius, heading)
	style_value_field(radius, "px")
	radius.custom_minimum_size.y = 20  # the heading row stays 20 px like the other headings
	if radius_caption is Label:
		advanced(move_to(radius_caption, block))
		radius_caption.theme_type_variation = "CaptionLabel"
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 12)
	block.add_child(row)
	var preview := Panel.new()
	preview.custom_minimum_size = Vector2(40, 40)
	preview.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	preview.mouse_filter = Control.MOUSE_FILTER_IGNORE
	preview.add_theme_stylebox_override("panel", StudioTheme.flat(Color("0f1116"), StudioTheme.LINE, 8, 1))
	row.add_child(preview)
	var dot := Control.new()
	dot.mouse_filter = Control.MOUSE_FILTER_IGNORE
	preview.add_child(dot)
	dot.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	dot.draw.connect(func():
		# Diameter follows the radius (6 → 10 px as in the mock), capped to the 40 px box.
		var diameter := clampf(4.0 + radius.value, 3.0, 32.0)
		var ink := color.color
		ink.a *= brush_opacity.value / 100.0
		var centre := dot.size / 2.0
		if ink.a < 0.3: dot.draw_arc(centre, diameter / 2.0, 0, TAU, 32, StudioTheme.TEXT3, 1.0, true)
		dot.draw_circle(centre, diameter / 2.0, ink, true, -1.0, true))
	radius.value_changed.connect(func(_value): dot.queue_redraw())
	brush_opacity.value_changed.connect(func(_value): dot.queue_redraw())
	bound_slider(row, radius)
	# Advanced: the three sliders share one column (Codex's captions above label them, so the short
	# bold labels are Simple-only): a 42 px lead slot + 10 lines up with the 40 px preview + 12, and a
	# 54 px end slot + 12 with the 56 px values + 10.
	var end_slot := Control.new()
	end_slot.custom_minimum_size.x = 54
	end_slot.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(end_slot)
	advanced(end_slot)
	# Opacity on one compact row (label, slider, value), so New drawing stays above the fold.
	var opacity_row := HBoxContainer.new()
	opacity_row.add_theme_constant_override("separation", 10)
	block.add_child(opacity_row)
	simple_only(overlay_label(opacity_row, "Opacity", StudioTheme.TEXT2, 12, 600)).custom_minimum_size.x = 52
	var opacity_lead := Control.new()
	opacity_lead.custom_minimum_size.x = 42
	opacity_lead.mouse_filter = Control.MOUSE_FILTER_IGNORE
	opacity_row.add_child(opacity_lead)
	advanced(opacity_lead)
	var opacity_caption: Node = children[children.find(brush_opacity) - 1]
	bound_slider(opacity_row, brush_opacity).custom_minimum_size.y = 32
	move_to(brush_opacity, opacity_row)
	style_value_field(brush_opacity, "%")
	brush_opacity.custom_minimum_size.x = 56
	if opacity_caption is Label:
		advanced(move_to(opacity_caption, block))
		opacity_caption.theme_type_variation = "CaptionLabel"
		block.move_child(opacity_caption, opacity_row.get_index())  # above its row, like the radius caption
	var smoothing_holder: Control = brush_smoothing.get_parent()
	move_to(smoothing_holder, block)  # Advanced-only row
	# Its caption matches the other Advanced captions in the card (12 px #B4BAC7); the SpinBox gets the
	# Opacity treatment (label, neon slider, flat "N px" value) and stays the same control.
	for child in smoothing_holder.get_children():
		if child is Label: child.theme_type_variation = "CaptionLabel"
	var smoothing_row := HBoxContainer.new()
	smoothing_row.add_theme_constant_override("separation", 10)
	smoothing_holder.add_child(smoothing_row)
	var smoothing_lead := Control.new()  # the row is Advanced-only: its caption above labels it
	smoothing_lead.custom_minimum_size.x = 42
	smoothing_lead.mouse_filter = Control.MOUSE_FILTER_IGNORE
	smoothing_row.add_child(smoothing_lead)
	var smoothing_slider := bound_slider(smoothing_row, brush_smoothing)
	smoothing_slider.custom_minimum_size.y = 32
	smoothing_slider.step = brush_smoothing.step
	move_to(brush_smoothing, smoothing_row)
	style_value_field(brush_smoothing, "px")
	brush_smoothing.custom_minimum_size.x = 56
	draw_inspector["brush_dot"] = dot

func style_layer_picker() -> void:
	# layer_choice as the mock's picker: h40, #101218, 1 px #2C303B, r8, 14 px #4DA3FF chip,
	# 12 px #8C93A3 chevron. It stays the same OptionButton (items, signal, selection).
	layer_choice.custom_minimum_size = Vector2(0, 40)
	layer_choice.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	layer_choice.fit_to_longest_item = false
	layer_choice.clip_text = true
	layer_choice.add_theme_font_override("font", StudioTheme.font(500))
	layer_choice.add_theme_font_size_override("font_size", 13)
	layer_choice.add_theme_icon_override("arrow", StudioTheme.icon("chevron", StudioTheme.TEXT3, 12))
	var pad := Vector4(34, 0, 12, 0)
	override_button_boxes(layer_choice, StudioTheme.flat(StudioTheme.FIELD, StudioTheme.LINE2, 8, 1, pad), StudioTheme.flat(Color("21252f"), StudioTheme.LINE3, 8, 1, pad), StudioTheme.flat(StudioTheme.RAISE, StudioTheme.LINE2, 8, 1, pad), StudioTheme.flat(Color("0f1116"), StudioTheme.LINE, 8, 1, pad))
	for state in ["font_color", "font_focus_color", "font_hover_color", "font_pressed_color", "font_hover_pressed_color"]: layer_choice.add_theme_color_override(state, StudioTheme.TEXT)
	var chip := TextureRect.new()
	chip.texture = StudioTheme.chip(StudioTheme.DRAWING, 14, 4.0)
	chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer_choice.add_child(chip)
	chip.set_anchors_preset(Control.PRESET_CENTER_LEFT)
	chip.offset_left = 12; chip.offset_right = 26; chip.offset_top = -7; chip.offset_bottom = 7

func build_layer_block() -> void:
	# "Layer" + "N layers"; picker + Layers…; Show and Onion skin switch rows.
	var block := inspector_block(drawing_section, "Layer")
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	block.add_child(row)
	move_to(layer_choice, row)
	style_layer_picker()
	move_to(layer_editor.launch, row)
	style_outline(layer_editor.launch, "layers")
	var rows := VBoxContainer.new()
	rows.add_theme_constant_override("separation", 0)
	block.add_child(rows)
	layer_visibility.text = "Show"  # mock copy; the full meaning stays in the tooltip
	layer_visibility.tooltip_text = "Show this layer"
	rows.add_child(style_switch_row(layer_visibility, "eye"))
	var onion: CheckButton = onion_editor.enabled
	rows.add_child(style_switch_row(onion, "onion", 44, true))
	onion_sub_line(onion)
	move_to(onion_editor.opacity.get_parent(), block)  # Advanced-only row
	draw_inspector["layer_meta"] = section_meta(block)
	draw_inspector["layer_count"] = -1

func build_next_card() -> void:
	# The shared inspector card (arrow tile) under the Layer section. Same conditions as
	# refresh_empty_hint(); hidden otherwise.
	var card := inspector_card(drawing_section, "arrow-right")
	card.holder.visible = false
	draw_inspector.merge({"next": card.holder, "next_title": card.title, "next_body": card.body})

func draw_next_step() -> Array:
	# Mirrors refresh_empty_hint(): Simple Draw only, not while playing or exporting.
	if advanced_mode or playing or exporting or mode.selected != 0: return []
	var empty: bool = source.is_empty() and (renderer.world_runtime == null or renderer.world_runtime.instances.is_empty())
	if empty: return ["Next: add a scene or a model", "Add a 3D scene or a model, move the camera and save a key, then draw on top."]
	if active_layer < layers.size() and Drawing.cel_at(layers[active_layer], frame).is_empty():
		return ["Next: draw on frame %d" % frame, "Frame %d has no drawing yet. Press New drawing, then draw on the picture." % frame]
	return []

func build_new_drawing_block() -> void:
	# Full-width PrimaryButton h44 (14/600 white, + icon). No copy-drawing shortcut exists in
	# keyboard_shortcuts, so instead of a keycap hint the visible "Copy drawing here" button stays.
	var block := VBoxContainer.new()
	block.add_theme_constant_override("separation", 10)
	var panel := PanelContainer.new()
	# The top hairline only shows while the Next card sits above (mock: one 1 px line between
	# them); otherwise the Layer block's bottom line already separates it.
	var new_box := inspector_box(Vector4(16, 16, 16, 18), true, true)
	draw_inspector["new_box"] = new_box
	panel.add_theme_stylebox_override("panel", new_box)
	drawing_section.add_child(panel)
	panel.add_child(block)
	move_to(new_drawing_button, block)
	style_primary(new_drawing_button, "cel")
	move_to(copy_drawing_button, block)
	style_outline(copy_drawing_button)
	for control in [exposure.get_parent(), exposure_button, delete_cel_button]: move_to(control, block)

func build_draw_inspector() -> void:
	# Re-arranges drawing_section into the mock's cards. Anything not placed explicitly (a control a
	# later Codex change adds) lands in "More drawing options" in its original order.
	var children: Array = drawing_section.get_children()
	var heading: Node = children[0]
	heading.visible = false
	var outer: PanelContainer = drawing_section.get_parent()
	outer.add_theme_stylebox_override("panel", StudioTheme.flat(StudioTheme.BAR, Color.TRANSPARENT, 0, 0, Vector4(0, 0, 0, 0)))
	drawing_section.add_theme_constant_override("separation", 0)
	build_tool_card()
	var options := PanelContainer.new()
	options.add_theme_stylebox_override("panel", inspector_box(Vector4(16, 14, 16, 14)))
	drawing_section.add_child(options)
	var option_box := VBoxContainer.new()
	option_box.add_theme_constant_override("separation", 8)
	options.add_child(option_box)
	var tool_panels: Array = [fill_editor.panel, color_sampler.panel, drawing_selection_editor.panel]
	for panel in tool_panels: move_to(panel, option_box)
	color_sampler.hint.theme_type_variation = "CaptionLabel"
	draw_inspector.merge({"tool_options": options, "tool_panels": tool_panels})
	build_colour_block()
	build_brush_block(children)
	build_layer_block()
	build_next_card()
	build_new_drawing_block()
	var more := inspector_block(drawing_section, "More drawing options")
	palette_editor.hint.theme_type_variation = "CaptionLabel"
	move_to(palette_editor.panel, more)
	for b in palette_editor.panel.get_children():
		if b is Button: style_outline(b)
	more.add_child(style_switch_row(brush_pressure, "hand"))
	move_to(tool, more)
	tool.custom_minimum_size.y = 40
	tool.tooltip_text = "Drawing tool (also in the tool bar over the picture)"
	for launch in [raster_importer.launch, video_importer.launch, reference_sheet.launch]:
		move_to(launch, more)
		style_outline(launch)
	for child in children:
		if child != heading and is_instance_valid(child) and child.get_parent() == drawing_section: move_to(child, more)
	draw_inspector["more"] = more
	refresh_draw_inspector()

func refresh_draw_inspector() -> void:
	# Per frame, cheap: every write happens only when the shown value changes.
	if draw_inspector.is_empty() or not drawing_section.is_visible_in_tree(): return
	var d := draw_inspector
	var index := clampi(tool.selected, 0, TOOL_TITLES.size() - 1)
	var key: String = keyboard_shortcuts.label_for(TOOL_KEYS[index])
	var signature := "%d|%s" % [index, key]
	if d.tool_sig != signature:
		d.tool_sig = signature
		d.tool_icon.texture = StudioTheme.icon(TOOL_ICONS[index], Color.WHITE, 18)
		d.tool_title.text = TOOL_TITLES[index]
		d.tool_hint.text = TOOL_HINTS[index]
		d.tool_kbd.text = key
		d.tool_kbd.visible = not key.is_empty()
	var any := false
	for panel in d.tool_panels: any = any or panel.visible
	if d.tool_options.visible != any: d.tool_options.visible = any
	track_recent_color()
	if color.color != d.shown_color:
		d.shown_color = color.color
		d.swatch.bg_color = color.color
		d.colour_meta.text = colour_name(color.color)
		d.brush_dot.queue_redraw()
	if d.layer_count != layers.size():
		d.layer_count = layers.size()
		d.layer_meta.text = "%d layer%s" % [layers.size(), "" if layers.size() == 1 else "s"]
	var next := draw_next_step()
	if next.is_empty():
		if d.next.visible: d.next.visible = false
	else:
		if d.next_title.text != next[0]: d.next_title.text = next[0]
		if d.next_body.text != next[1]: d.next_body.text = next[1]
		if not d.next.visible: d.next.visible = true
	var line := 1 if d.next.visible else 0
	if d.new_box.border_width_top != line: d.new_box.border_width_top = line

# ---- Neon Pro step 7: right inspector, Camera panel ---------------------------------------
# Built once at start-up in the neon style, after camera_transform_editor has added its panel.
# Codex's controls are moved and restyled, never replaced: fov, camera_near, camera_far,
# interpolation, the Save camera key / Delete key buttons, the mouse-controls text and the numeric
# camera panel keep their types, values, signals and Simple/Advanced visibility. The key list, lens
# presets and guides switch only read app state and act through the existing paths (set_frame,
# fov.value, scene_view.set_guides). Classic styles keep the old single "Camera" card.

# Lens presets as full-frame focal lengths, so the meta and the stage caption (lens_mm()) read the
# preset exactly: Wide 24 mm, Normal 35 mm, Close 60 mm. lens_fov() turns one into the camera FOV.
const LENS_PRESETS := [["Wide", 24.0], ["Normal", 35.0], ["Close", 60.0]]
var camera_inspector := {}  # neon only: Camera panel nodes and the values they last showed
# Session-only UI note for the "Just saved" chip: a copy of the key insert_key() stored last. Never
# saved; undo removes the key, so the chip goes with it.
var last_saved_key := {}

func neon_tile(parent: Node, texture: Texture2D, size: int, inner: Color, ring_width: float, glow: bool, align := Control.SIZE_SHRINK_CENTER) -> TextureRect:
	# Neon-ring icon tile, r8: the header tiles (36 px, 1 px ring, violet glow) and the card tiles
	# (28 px, 1.5 px ring, no glow). Returns the icon so callers can swap it.
	var holder: Node = parent
	var outer: Control = null
	if glow:
		var glow_panel := PanelContainer.new()
		glow_panel.add_theme_stylebox_override("panel", StudioTheme.flat(inner, Color.TRANSPARENT, 8, 0, Vector4(0, 0, 0, 0), Color(0.482, 0.361, 1, 0.4), 7))
		glow_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
		parent.add_child(glow_panel)
		holder = glow_panel
		outer = glow_panel
	var tile := PanelContainer.new()
	var ring := StudioTheme.neon_ring(8.0, ring_width, inner, false)
	ring.set_content_margin_all(0)
	tile.add_theme_stylebox_override("panel", ring)
	tile.mouse_filter = Control.MOUSE_FILTER_IGNORE
	holder.add_child(tile)
	if outer == null: outer = tile
	outer.custom_minimum_size = Vector2(size, size)
	outer.size_flags_vertical = align
	var image := TextureRect.new()
	image.texture = texture
	image.stretch_mode = TextureRect.STRETCH_KEEP_CENTERED
	image.mouse_filter = Control.MOUSE_FILTER_IGNORE
	tile.add_child(image)
	return image

func inspector_header(parent: Node, kind: String, title: String, subtitle: String) -> Array:
	# 64 px header card: 36 px neon tile with a white icon, title 15/600, subtitle 12 #B4BAC7.
	# Returns [title Label, subtitle Label].
	var card := PanelContainer.new()
	card.add_theme_stylebox_override("panel", inspector_box(Vector4(16, 0, 16, 0)))
	card.custom_minimum_size.y = 64
	parent.add_child(card)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 12)
	card.add_child(row)
	neon_tile(row, StudioTheme.icon(kind, Color.WHITE, 18), 36, StudioTheme.TOOL_INNER, 1.0, true)
	var text := VBoxContainer.new()
	text.add_theme_constant_override("separation", 2)
	text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	text.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	text.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(text)
	return [overlay_label(text, title, StudioTheme.TEXT, 15, 600), overlay_label(text, subtitle, StudioTheme.TEXT2, 12)]

func inspector_card(parent: Node, kind: String) -> Dictionary:
	# margin 14 16, pad 12 14, r10, #111318, 1 px #2C303B: 28 px neon-ring tile, title 13/600, body 12
	# #B4BAC7 (line height ~1.45). Used by the Draw "Next" card and the Camera help card.
	var holder := MarginContainer.new()
	holder.add_theme_constant_override("margin_left", 16)
	holder.add_theme_constant_override("margin_right", int(16 - inspector_bar_width))
	holder.add_theme_constant_override("margin_top", 14)
	holder.add_theme_constant_override("margin_bottom", 14)
	inspector_holders.append(holder)
	parent.add_child(holder)
	var card := PanelContainer.new()
	# 12 px side padding (mock 14): the substitute UI font is ~6% wider than Geist, so the text
	# column gets those pixels back and wraps like the mock.
	card.add_theme_stylebox_override("panel", StudioTheme.flat(StudioTheme.PANEL, StudioTheme.LINE2, 10, 1, Vector4(12, 12, 12, 12)))
	holder.add_child(card)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 12)
	card.add_child(row)
	neon_tile(row, StudioTheme.icon(kind, Color.WHITE, 14 if kind == "arrow-right" else 16), 28, StudioTheme.PANEL, 1.5, false, Control.SIZE_SHRINK_BEGIN)
	var text := VBoxContainer.new()
	text.add_theme_constant_override("separation", 4)
	text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(text)
	var title := overlay_label(text, "", StudioTheme.TEXT, 13, 600)
	var body := overlay_label(text, "", StudioTheme.TEXT2, 12)
	for l in [title, body]:
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		l.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
		l.custom_minimum_size.x = 120
	body.add_theme_constant_override("line_spacing", 3)
	return {"holder": holder, "title": title, "body": body}

func style_primary(control: Button, kind: String) -> TextureRect:
	# Full-width PrimaryButton h44 (14/600 white) with the icon and label centred as one group (a
	# Button icon would stick to the left edge): the label is shifted 12 px right by the padding and
	# the icon sits 8 px before it. center_primary_icon() re-centres it after a text change.
	control.theme_type_variation = "PrimaryButton"
	control.custom_minimum_size.y = 44
	control.icon = null
	var pad := Vector4(36, 0, 12, 0)
	override_button_boxes(control, StudioTheme.flat(Color("1a1d25"), StudioTheme.LINE3, 8, 1, pad), StudioTheme.flat(Color("21252f"), StudioTheme.LINE3, 8, 1, pad), StudioTheme.flat(StudioTheme.RAISE, StudioTheme.LINE3, 8, 1, pad), StudioTheme.flat(Color("0f1116"), StudioTheme.LINE, 8, 1, pad))
	var image := TextureRect.new()
	image.texture = StudioTheme.icon(kind, Color.WHITE, 16)
	image.mouse_filter = Control.MOUSE_FILTER_IGNORE
	control.add_child(image)
	image.set_anchors_preset(Control.PRESET_CENTER)
	center_primary_icon(control, image)
	return image

func center_primary_icon(control: Button, image: TextureRect) -> void:
	var text_width := StudioTheme.font(600).get_string_size(control.text, HORIZONTAL_ALIGNMENT_LEFT, -1, 14).x
	image.offset_left = -text_width / 2.0 - 12; image.offset_right = image.offset_left + 16; image.offset_top = -8; image.offset_bottom = 8
	image.set_meta("text", control.text)

func lens_fov(mm: float) -> float:
	# Inverse of lens_mm(): the camera FOV (Godot's fov: vertical unless KEEP_WIDTH) that reads mm
	# on a 36 mm-wide full-frame sensor at the project's aspect.
	var cam: Camera3D = renderer.camera
	var aspect := float(video.width) / maxf(1.0, float(video.height))
	var horizontal := 18.0 / maxf(mm, 0.001)
	var half := horizontal if cam.keep_aspect == Camera3D.KEEP_WIDTH else horizontal / aspect
	return rad_to_deg(2.0 * atan(half))

func lens_preset_value(mm: float) -> float:
	# The value fov would hold for a preset (clamped and snapped like the SpinBox does).
	return snappedf(clampf(lens_fov(mm), fov.min_value, fov.max_value), fov.step if fov.step > 0 else 0.0)

func apply_lens(mm: float) -> void:
	# Through fov.value and its existing value_changed path, which applies only in Camera mode.
	if exporting: return
	if not fov.editable: message("Switch to Camera to change the lens."); return
	fov.value = lens_preset_value(mm)

func go_to_camera_key(target: int) -> void:
	if exporting: return
	stop()
	set_frame(target)

func lens_button_boxes(control: Button, selected: bool) -> void:
	var pad := Vector4(6, 0, 6, 0)
	var normal := StudioTheme.flat(StudioTheme.RAISE, StudioTheme.LINE2, 7, 1, pad) if selected else StudioTheme.flat(Color.TRANSPARENT, Color.TRANSPARENT, 7, 0, pad)
	var hover := normal if selected else StudioTheme.flat(StudioTheme.HOVER, Color.TRANSPARENT, 7, 0, pad)
	override_button_boxes(control, normal, hover, normal, StudioTheme.flat(Color.TRANSPARENT, Color.TRANSPARENT, 7, 0, pad))
	control.add_theme_font_override("font", StudioTheme.font(600 if selected else 500))
	var ink := Color.WHITE if selected else StudioTheme.TEXT2
	for state in ["font_color", "font_focus_color", "font_pressed_color", "font_hover_pressed_color"]: control.add_theme_color_override(state, ink)
	control.add_theme_color_override("font_hover_color", Color.WHITE)
	control.add_theme_color_override("font_disabled_color", StudioTheme.TEXT3)

func build_camera_keys_block(parent: Node) -> void:
	# "Camera keys" + "N keys"; one 44 px row per key (rebuilt only when the keys change).
	var block := inspector_block(parent, "Camera keys")
	block.add_theme_constant_override("separation", 12)
	var rows := VBoxContainer.new()
	rows.add_theme_constant_override("separation", 2)
	block.add_child(rows)
	camera_inspector.merge({"keys_meta": section_meta(block), "key_rows": rows, "keys_sig": "", "rows": [], "row_frame": -2})

func camera_key_row(parent: Node, key_frame: int, detail: String, saved: bool) -> Dictionary:
	# 44 px, r8, pad 0 10 0 8, gap 10: 9 px pink diamond, 48x27 placeholder tile (no renders),
	# "Frame N" 13/500 over "S.SS s" 12 #B4BAC7, optional "Just saved" chip. Click: go to the key.
	var row := Button.new()
	row.focus_mode = Control.FOCUS_NONE
	row.custom_minimum_size.y = 44
	row.tooltip_text = "Go to camera key at frame %d" % key_frame
	row.pressed.connect(go_to_camera_key.bind(key_frame))
	parent.add_child(row)
	var line := HBoxContainer.new()
	line.add_theme_constant_override("separation", 10)
	line.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(line)
	line.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	line.offset_left = 8; line.offset_right = -10
	var diamond := TextureRect.new()
	diamond.texture = StudioTheme.diamond(StudioTheme.CAMERA, 12)
	diamond.expand_mode = TextureRect.EXPAND_IGNORE_SIZE  # the glow texture is wider than the slot
	diamond.custom_minimum_size = Vector2(15, 22)
	diamond.stretch_mode = TextureRect.STRETCH_KEEP_CENTERED
	diamond.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	diamond.mouse_filter = Control.MOUSE_FILTER_IGNORE
	line.add_child(diamond)
	var thumb := PanelContainer.new()
	thumb.add_theme_stylebox_override("panel", StudioTheme.flat(Color("121638"), StudioTheme.LINE3, 4, 1, Vector4(0, 0, 0, 0)))
	thumb.custom_minimum_size = Vector2(48, 27)
	thumb.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	thumb.mouse_filter = Control.MOUSE_FILTER_IGNORE
	line.add_child(thumb)
	var lens := TextureRect.new()
	lens.texture = StudioTheme.icon("camera", StudioTheme.TEXT3, 14)
	lens.stretch_mode = TextureRect.STRETCH_KEEP_CENTERED
	lens.mouse_filter = Control.MOUSE_FILTER_IGNORE
	thumb.add_child(lens)
	var text := VBoxContainer.new()
	text.add_theme_constant_override("separation", 1)
	text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	text.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	text.mouse_filter = Control.MOUSE_FILTER_IGNORE
	line.add_child(text)
	var name_label := overlay_label(text, "Frame %d" % key_frame, StudioTheme.TEXT, 13, 500)
	overlay_label(text, detail, StudioTheme.TEXT2, 12)
	if saved:
		var chip := overlay_label(line, "Just saved", Color("ffd6ea"), 11, 600)
		chip.add_theme_stylebox_override("normal", StudioTheme.flat(Color(1, 0.373, 0.682, 0.16), Color(1, 0.373, 0.682, 0.45), 5, 1, Vector4(7, 0, 7, 0)))
		chip.custom_minimum_size.y = 20
		chip.tooltip_text = "The camera key you saved last"
	return {"frame": key_frame, "button": row, "name": name_label, "diamond": diamond}

func style_camera_key_row(entry: Dictionary, current: bool) -> void:
	var pad := Vector4(0, 0, 0, 0)
	var normal := StudioTheme.flat(StudioTheme.RAISE, StudioTheme.LINE2, 8, 1, pad) if current else StudioTheme.flat(Color.TRANSPARENT, Color.TRANSPARENT, 8, 0, pad)
	var hover := normal if current else StudioTheme.flat(StudioTheme.HOVER, Color.TRANSPARENT, 8, 0, pad)
	override_button_boxes(entry.button, normal, hover, hover, normal)
	entry.name.add_theme_font_override("font", StudioTheme.font(600 if current else 500))
	entry.name.add_theme_color_override("font_color", Color.WHITE if current else StudioTheme.TEXT)
	entry.diamond.texture = StudioTheme.key_glow(StudioTheme.CAMERA, StudioTheme.RAISE) if current else StudioTheme.diamond(StudioTheme.CAMERA, 12)

func rebuild_camera_key_rows(frames: Array, saved_frame: int) -> void:
	var c := camera_inspector
	for child in c.key_rows.get_children():
		c.key_rows.remove_child(child)
		child.queue_free()
	c.rows = []
	for i in range(frames.size()):
		var value: int = frames[i]
		var seconds := float(value) * float(video.fps_den) / maxf(1.0, float(video.fps_num))
		var detail := "%.2f s" % seconds
		if i == 0: detail += " · start"
		elif i == frames.size() - 1: detail += " · end"
		c.rows.append(camera_key_row(c.key_rows, value, detail, value == saved_frame))
	c.keys_meta.text = "%d key%s" % [frames.size(), "" if frames.size() == 1 else "s"]
	c.row_frame = -2

func build_lens_block(parent: Node) -> void:
	# "Lens" + "NN mm" (lens_mm(), like the stage caption); Wide / Normal / Close segmented control
	# (group pad 3, r10, #0F1015, 1 px #22252E). Advanced adds "Field of view": the fov SpinBox as a
	# flat "54 °" value with a neon slider bound to it (fov stays Advanced-only, ui_smoke).
	var block := inspector_block(parent, "Lens")
	block.add_theme_constant_override("separation", 12)
	section_meta(block).add_theme_color_override("font_color", StudioTheme.TEXT2)
	var group := PanelContainer.new()
	group.add_theme_stylebox_override("panel", StudioTheme.flat(Color("0f1015"), StudioTheme.LINE, 10, 1, Vector4(3, 3, 3, 3)))
	block.add_child(group)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 2)
	group.add_child(row)
	var buttons: Array = []
	for preset in LENS_PRESETS:
		var choice := Button.new()
		choice.text = preset[0]
		choice.focus_mode = Control.FOCUS_NONE
		choice.custom_minimum_size.y = 40
		choice.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		choice.add_theme_font_size_override("font_size", 13)
		choice.tooltip_text = "%s lens: %d mm. Changes the view until you save a camera key." % [preset[0], preset[1]]
		choice.pressed.connect(apply_lens.bind(preset[1]))
		lens_button_boxes(choice, false)
		row.add_child(choice)
		buttons.append(choice)
	var fov_block := VBoxContainer.new()
	fov_block.add_theme_constant_override("separation", 4)
	block.add_child(advanced(fov_block))
	fov_block.visible = advanced_mode
	var head := HBoxContainer.new()
	head.custom_minimum_size.y = 20
	fov_block.add_child(head)
	overlay_label(head, "Field of view", StudioTheme.TEXT2, 12, 600).size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var fov_row: Node = fov.get_parent()
	move_to(fov, head)
	style_value_field(fov, "°")
	var slider := bound_slider(fov_block, fov)
	slider.step = fov.step if fov.step > 0 else 1
	slider.custom_minimum_size.y = 32
	move_to(fov_row, fov_block)  # Codex's "Editor camera FOV" caption (Advanced row)
	for caption in fov_row.get_children():
		if caption is Label: caption.theme_type_variation = "CaptionLabel"
	camera_inspector.merge({"lens_meta": section_meta(block), "lens_buttons": buttons, "lens_sig": "", "fov_slider": slider})

func build_guides_block(parent: Node) -> void:
	# Switch row h44 (grid icon, "Framing guides" / "Thirds and safe area"): both scene guides at
	# once through scene_view.set_guides(); synced from its frame_enabled and grid_enabled.
	var block := inspector_block(parent, "")
	var guides := CheckButton.new()
	guides.text = "Framing guides"
	guides.focus_mode = Control.FOCUS_NONE
	guides.tooltip_text = "Show the camera frame and the rule-of-thirds grid on the picture (also Frame and 3×3 above the picture)."
	guides.toggled.connect(func(on):
		if scene_view: scene_view.set_guides(on, on))
	block.add_child(style_switch_row(guides, "grid", 44, true))
	var sub := overlay_label(guides, "Thirds and safe area", StudioTheme.TEXT2, 12)
	sub.position = Vector2(34, 23)
	camera_inspector["guides"] = guides

func build_camera_save_block(parent: Node) -> void:
	# Save camera key [K] stays in the panel (Codex) as the 44 px PrimaryButton, with Codex's hint
	# under it; Delete key (Advanced) follows as an outline button.
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", inspector_box(Vector4(16, 16, 16, 18)))
	parent.add_child(panel)
	var block := VBoxContainer.new()
	block.add_theme_constant_override("separation", 10)
	panel.add_child(block)
	move_to(camera_key_button, block)
	var image := style_primary(camera_key_button, "key")
	move_to(camera_hint_label, block)
	camera_hint_label.theme_type_variation = "CaptionLabel"
	camera_hint_label.add_theme_color_override("font_color", StudioTheme.TEXT2)
	camera_hint_label.add_theme_font_size_override("font_size", 12)
	camera_hint_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	camera_hint_label.add_theme_constant_override("line_spacing", 3)
	camera_hint_label.text = camera_hint_label.text.replace("\r", "")  # CRLF source: one break per line
	move_to(camera_delete_button, block)
	style_outline(camera_delete_button, "eraser")
	camera_inspector["key_icon"] = image

func build_camera_inspector() -> void:
	# Re-arranges camera_section into the mock's cards. Anything not placed explicitly (a control a
	# later Codex change adds) lands in "Camera details" in its original order.
	var children: Array = camera_section.get_children()
	var heading: Node = children[0]
	heading.visible = false
	var outer: PanelContainer = camera_section.get_parent()
	outer.add_theme_stylebox_override("panel", StudioTheme.flat(StudioTheme.BAR, Color.TRANSPARENT, 0, 0, Vector4(0, 0, 0, 0)))
	camera_section.add_theme_constant_override("separation", 0)
	inspector_header(camera_section, "camera", "Movie camera", "What the movie will show")
	build_camera_keys_block(camera_section)
	build_lens_block(camera_section)
	build_guides_block(camera_section)
	build_camera_save_block(camera_section)
	var help := inspector_card(camera_section, "path")
	help.holder.add_theme_constant_override("margin_bottom", 16)
	help.title.text = "How camera keys work"
	help.body.text = "Each key remembers a view. The camera glides between them."
	# Mouse controls: Simple reads them in the "Mouse and keys" popover over the picture
	# (camera_help_button shows this label's text); Advanced keeps them inline here.
	var details := inspector_block(camera_section, "Camera details")
	move_to(advanced(camera_help_label), details)
	camera_help_label.visible = advanced_mode
	camera_help_label.add_theme_font_size_override("font_size", 12)
	camera_help_label.text = camera_help_label.text.replace("\r", "")
	camera_help_label.add_theme_constant_override("line_spacing", 3)
	camera_help_label.add_theme_color_override("font_color", StudioTheme.TEXT2)
	for child in children:
		if child != heading and is_instance_valid(child) and child.get_parent() == camera_section: move_to(child, details)
	for child in details.get_children():
		if child is Button: style_outline(child)
		elif child is VBoxContainer:
			for inner in child.get_children():
				if inner is Button: style_outline(inner)
	camera_inspector["details"] = details.get_parent()
	camera_inspector["details_box"] = details
	refresh_camera_inspector()

func refresh_camera_inspector() -> void:
	# Per frame, cheap: rows rebuild only when the keys change; other writes only when a shown
	# value changes.
	if camera_inspector.is_empty() or not camera_section.is_visible_in_tree(): return
	var c := camera_inspector
	# Cheap change token first: every key edit (insert, delete, undo) goes through changed(), which
	# bumps recovery_revision; a loaded project brings a new keys array. Only when it differs are the
	# frames sorted and the row signature built.
	var token := "%d|%d|%d|%d/%d" % [recovery_revision, keys.size(), hash(last_saved_key), video.fps_num, video.fps_den]
	if c.get("keys_token", "") != token or not is_same(c.get("keys_ref"), keys):
		c.keys_token = token
		c.keys_ref = keys
		var frames: Array = []
		for key in keys: frames.append(int(key.frame))
		frames.sort()
		var saved_frame := -1
		if not last_saved_key.is_empty():
			for key in keys:
				if key == last_saved_key: saved_frame = int(key.frame)
		var signature := "%s|%d|%d/%d" % [frames, saved_frame, video.fps_num, video.fps_den]
		if c.keys_sig != signature:
			c.keys_sig = signature
			rebuild_camera_key_rows(frames, saved_frame)
	# Codex sets fov with set_value_no_signal (refresh_camera_controls, change_mode), which the bound
	# slider never hears: follow it here so a grab never jumps from a stale value.
	if not is_equal_approx(c.fov_slider.value, fov.value): c.fov_slider.set_value_no_signal(fov.value)
	if c.row_frame != frame:
		# Restyle only the rows that change (all of them after a rebuild, which sets row_frame = -2).
		var old: int = c.row_frame
		c.row_frame = frame
		for entry in c.rows:
			if old == -2 or entry.frame == old or entry.frame == frame: style_camera_key_row(entry, entry.frame == frame)
	var editable: bool = fov.editable
	var selected := -1
	for i in range(LENS_PRESETS.size()):
		if absf(fov.value - lens_preset_value(LENS_PRESETS[i][1])) < 0.001: selected = i
	var mm := "%d mm" % roundi(lens_mm())
	var lens_signature := "%d|%s|%s" % [selected, editable, mm]
	if c.lens_sig != lens_signature:
		c.lens_sig = lens_signature
		c.lens_meta.text = mm
		for i in range(c.lens_buttons.size()):
			lens_button_boxes(c.lens_buttons[i], i == selected)
			c.lens_buttons[i].disabled = not editable
		c.fov_slider.editable = editable
	if scene_view:
		var on: bool = scene_view.frame_enabled and scene_view.grid_enabled
		if c.guides.button_pressed != on: c.guides.set_pressed_no_signal(on)
	if c.key_icon.get_meta("text", "") != camera_key_button.text: center_primary_icon(camera_key_button, c.key_icon)
	var any := false
	for child in c.details_box.get_children():
		if child != c.details_box.get_meta("heading", null) and child.visible: any = true
	if c.details.visible != any: c.details.visible = any

# ---- Neon Pro step 6: timeline transport ---------------------------------------------------
func transport_block(transport: HFlowContainer) -> HBoxContainer:
	# 190 px block (TimelineView.LEFT) over the lane labels, with a 1 px #22252E right edge.
	var block := HBoxContainer.new()
	block.name = "TransportButtons"
	block.custom_minimum_size = Vector2(TimelineView.LEFT, 52)
	block.alignment = BoxContainer.ALIGNMENT_CENTER
	block.add_theme_constant_override("separation", 4)
	block.draw.connect(func(): block.draw_rect(Rect2(block.size.x - 1, 0, 1, block.size.y), StudioTheme.LINE))
	transport.add_child(block)
	return block

func style_transport(transport: HFlowContainer, block: Control) -> void:
	# 52 px row: |◀ ◀ ▶| as 40 px ghost icon buttons (#B4BAC7) around a 40 px neon-ring Play;
	# mono readout "S.SS / D.DD s · N fps"; compact mono Frame field; legend on the right.
	transport.add_theme_constant_override("h_separation", 16)
	transport.add_theme_constant_override("v_separation", 0)
	var kinds := ["skip-back", "step-back", "", "skip-forward"]
	for i in range(block.get_child_count()):
		var control: Button = block.get_child(i)
		if control == play_button: continue
		control.text = ""
		style_ghost(control, kinds[i], 40)
	play_button.text = ""
	play_button.custom_minimum_size = Vector2(40, 40)
	play_button.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	play_button.icon = StudioTheme.icon("play", Color.WHITE, 16)
	play_button.set_meta("kind", "play")
	play_button.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
	play_button.add_theme_constant_override("icon_max_width", 16)
	override_button_boxes(play_button, StudioTheme.play_ring(), StudioTheme.play_ring(true), StudioTheme.play_ring(true), StudioTheme.play_ring())
	override_button_colors(play_button, Color.WHITE, Color.WHITE, Color.WHITE)
	play_button.add_theme_stylebox_override("focus", StudioTheme.focus_box(22))
	# Readout: the fps text stays in transport_info (tests read "23.976 fps" there).
	var readout := HBoxContainer.new()
	readout.add_theme_constant_override("separation", 8)
	readout.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	transport.add_child(readout)
	transport.move_child(readout, block.get_index() + 1)
	transport_time = Label.new()
	transport_time.text = "0.00"
	transport_time.add_theme_font_override("font", StudioTheme.mono(600))
	transport_time.add_theme_font_size_override("font_size", 18)
	transport_time.add_theme_color_override("font_color", StudioTheme.TEXT)
	transport_time.size_flags_vertical = Control.SIZE_SHRINK_END
	readout.add_child(transport_time)
	transport_info.reparent(readout, false)
	transport_info.text_overrun_behavior = TextServer.OVERRUN_NO_TRIMMING
	transport_info.size_flags_horizontal = Control.SIZE_FILL
	transport_info.size_flags_vertical = Control.SIZE_SHRINK_END
	transport_info.add_theme_font_override("font", StudioTheme.mono(400))
	transport_info.add_theme_font_size_override("font_size", 13)
	transport_info.add_theme_color_override("font_color", StudioTheme.TEXT2)
	# Frame field: "Frame" caption + the SpinBox as a compact mono field.
	var frame_group := HBoxContainer.new()
	frame_group.add_theme_constant_override("separation", 8)
	frame_group.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	var frame_caption: Label = transport.get_child(frame_box.get_index() - 1)
	transport.add_child(frame_group)
	transport.move_child(frame_group, readout.get_index() + 1)
	frame_caption.reparent(frame_group, false)
	frame_box.reparent(frame_group, false)
	frame_caption.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	frame_caption.add_theme_font_size_override("font_size", 12)
	frame_caption.add_theme_color_override("font_color", StudioTheme.TEXT3)
	frame_box.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	frame_box.custom_minimum_size = Vector2(84, 30)
	var edit := frame_box.get_line_edit()
	edit.add_theme_font_override("font", StudioTheme.mono(500))
	edit.add_theme_font_size_override("font_size", 13)
	edit.add_theme_color_override("font_color", StudioTheme.TEXT)
	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	spacer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	transport.add_child(spacer)
	# Legend, gap 18, 12 px #B4BAC7: 16x8 r2 drawing chip, 8 px camera / model diamonds.
	var legend := HBoxContainer.new()
	legend.name = "TimelineLegend"
	legend.add_theme_constant_override("separation", 18)
	legend.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	transport.add_child(legend)
	var chip := StudioTheme.svg_texture('<rect width="16" height="8" rx="2" fill="%s"/>' % StudioTheme.hex(StudioTheme.DRAWING), 16, 8, 2.0)
	for item in [[chip, "Drawings"], [StudioTheme.diamond(StudioTheme.CAMERA, 11), "Camera keys"], [StudioTheme.diamond(StudioTheme.MODEL, 11), "Model keys"]]:
		var entry := HBoxContainer.new()
		entry.add_theme_constant_override("separation", 7)
		legend.add_child(entry)
		var swatch := TextureRect.new()
		swatch.texture = item[0]
		swatch.stretch_mode = TextureRect.STRETCH_KEEP_CENTERED
		swatch.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		entry.add_child(swatch)
		var caption := label(entry, item[1])
		caption.add_theme_font_size_override("font_size", 12)
		caption.add_theme_color_override("font_color", StudioTheme.TEXT2)
	var end_pad := Control.new()
	end_pad.mouse_filter = Control.MOUSE_FILTER_IGNORE
	transport.add_child(end_pad)

func compact_timeline_rows() -> void:
	# Codex's sequence toolbar and the zoom/pan bar share one compact group, which joins the 52 px
	# transport row (it wraps under it only when the dock is narrow), and the ruler sits right above
	# the lanes. Nothing is hidden: Sequences…, the breadcrumb and − + Fit stay where Simple shows them.
	var toolbar: HFlowContainer = sequence_editor.toolbar
	var bar: HBoxContainer = timeline_navigation.bar
	bar.set_anchors_and_offsets_preset(Control.PRESET_TOP_LEFT)
	bar.reparent(toolbar, false)
	bar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	bar.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	timeline_navigation.apply_neon_style()
	var transport := frame_box.get_parent().get_parent() as HFlowContainer
	if transport and toolbar.get_parent() != transport:
		var frame_group: Control = frame_box.get_parent()
		toolbar.reparent(transport, false)
		transport.move_child(toolbar, frame_group.get_index() + 1)
		toolbar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		toolbar.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		# A 12 px left inset so the group never touches the window edge when it wraps to its own line
		# (the toolbar node itself is unchanged: tests find "Sequences…" inside it).
		var inset := MarginContainer.new()
		inset.name = "SequenceToolbarInset"
		inset.add_theme_constant_override("margin_left", 12)
		inset.add_theme_constant_override("margin_right", 4)
		inset.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		inset.size_flags_stretch_ratio = 20.0
		inset.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		transport.add_child(inset)
		transport.move_child(inset, toolbar.get_index())
		toolbar.reparent(inset, false)
		# The legend is a Simple aid (Advanced shows Codex's longer readout, so the row stays one line).
		var legend := transport.get_node_or_null("TimelineLegend")
		if legend: simple_only(legend)
		# "Frames a–b" repeats the readout in Simple; Advanced keeps Codex's range caption.
		advanced(timeline_navigation.caption)
		# Codex's sequence strip followed the toolbar; it now opens right under the transport row.
		var strip: Control = sequence_editor.strip_scroll
		if strip and strip.get_parent() == timeline_ruler.get_parent().get_parent(): strip.get_parent().move_child(strip, transport.get_index() + 1)
	toolbar.add_theme_constant_override("h_separation", 8)
	toolbar.add_theme_constant_override("v_separation", 0)
	for child in toolbar.get_children():
		if child is Button:
			# Ghost like − + Fit beside it, so Sequences… is not the brightest thing in the row.
			child.custom_minimum_size.y = 28
			child.add_theme_font_override("font", StudioTheme.font(500))
			child.add_theme_font_size_override("font_size", 12)
			child.size_flags_vertical = Control.SIZE_SHRINK_CENTER
			var ghost_pad := Vector4(8, 0, 8, 0)
			var ghost_clear := StudioTheme.flat(Color.TRANSPARENT, Color.TRANSPARENT, 6, 0, ghost_pad)
			override_button_boxes(child, ghost_clear, StudioTheme.flat(StudioTheme.HOVER, Color.TRANSPARENT, 6, 0, ghost_pad), StudioTheme.flat(StudioTheme.RAISE, Color.TRANSPARENT, 6, 0, ghost_pad), ghost_clear)
			override_button_colors(child, StudioTheme.TEXT2, StudioTheme.TEXT, Color.WHITE)
		elif child is Label:
			child.add_theme_font_size_override("font_size", 12)
			child.add_theme_color_override("font_color", StudioTheme.TEXT3)
			child.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	var holder: Control = timeline_ruler.get_parent()
	holder.custom_minimum_size.y = 52
	timeline_ruler.position.y = 0
	# Rows sit flush (transport, toolbar, ruler, lanes), like the mock's grid.
	if holder.get_parent() is VBoxContainer: holder.get_parent().add_theme_constant_override("separation", 0)

func timeline_row_keys() -> Dictionary:
	# Neon timeline row summary: each object's authored key frames, recomputed only when that
	# object's data changes (same identity check the model uses for its own cache).
	var result := {}
	if not renderer.world_runtime:
		timeline_key_cache.clear()
		return result
	for row in renderer.world_runtime.data.objects:
		var instance: RefCounted = renderer.world_runtime.instance(row.id)
		if instance == null or not instance.has_method("authored_keys"): continue
		var cached: Array = timeline_key_cache.get(row.id, [])
		if cached.is_empty() or not is_same(cached[0], instance.data):
			var frames: Array = []
			for key in instance.authored_keys(): frames.append(int(key.frame))
			cached = [instance.data, frames]
			timeline_key_cache[row.id] = cached
		result[row.id] = cached[1]
	# Removed objects and old projects must not retain their complete data dictionaries here.
	for id in timeline_key_cache.keys():
		if not result.has(id): timeline_key_cache.erase(id)
	return result

func refresh_transport_text() -> void:
	var rate: String = preload("res://src/video_timing.gd").label(video.fps_num, video.fps_den)
	var full := "%s fps  •  %.2f seconds  •  Frames 0–%d; key %d is the end boundary" % [rate, Timeline.seconds(video.duration_frames, video), video.duration_frames - 1, video.duration_frames]
	if transport_time == null:
		transport_info.text = full
		return
	# Neon: "S.SS" + "/ D.DD s · N fps"; Advanced adds Codex's frame range; the full sentence is the tooltip.
	var time_text := "%.2f" % Timeline.seconds(frame, video)
	if transport_time.text != time_text: transport_time.text = time_text
	var info := "/ %.2f s · %s fps" % [Timeline.seconds(video.duration_frames, video), rate]
	if advanced_mode: info += " · frames 0–%d, key %d is the end boundary" % [video.duration_frames - 1, video.duration_frames]
	transport_info.text = info
	transport_info.tooltip_text = full

func refresh_play_button() -> void:
	if transport_time == null:
		play_button.text = "Pause" if playing else "Play"
		return
	var kind := "pause" if playing else "play"
	if play_button.get_meta("kind", "") != kind:
		play_button.set_meta("kind", kind)
		play_button.icon = StudioTheme.icon(kind, Color.WHITE, 16)

func sync_timeline_focus() -> void:
	# The lane being edited gets the highlight: the active layer in Draw (blue), Camera in Camera
	# (pink) and the posed model in Pose (violet, with an "Auto key" chip while auto-key is on).
	if transport_time == null or timeline == null: return
	var lane := "layer" if mode.selected == 0 else "camera" if mode.selected == 1 else "model"
	var chip: bool = pose_editor != null and pose_editor.auto_key != null and pose_editor.auto_key.button_pressed
	if timeline.focus_lane != lane or timeline.active_layer != active_layer or timeline.auto_key_chip != chip:
		timeline.focus_lane = lane
		timeline.active_layer = active_layer
		timeline.auto_key_chip = chip
		timeline.queue_redraw()
	# Bring the lane being edited (Draw: active layer, Pose: posed model) into the short lane area
	# once, when it becomes the focus; the user's own scrolling is left alone afterwards.
	var focus_key := "%s|%d|%s" % [lane, active_layer, timeline.selected_id]
	var lanes := timeline.get_parent() as ScrollContainer
	if lanes and not lanes.has_meta("focus_hooked"):
		lanes.set_meta("focus_hooked", true)
		lanes.resized.connect(func(): timeline_focus_key = "")  # new layout: bring the lane into view again
	# Visible part of the lane area: the dock's own scroll can clip the bottom of the lanes too.
	var view_top := 0.0
	var view_h := lanes.size.y if lanes else 0.0
	var dock_scroll: Control = workspace_layout.panels.timeline.get_node_or_null("TimelineContentScroll") if workspace_layout and workspace_layout.panels.has("timeline") else null
	if lanes and dock_scroll:
		var clip := lanes.get_global_rect().intersection(dock_scroll.get_global_rect())
		if clip.size.y > 0.0:
			view_top = clip.position.y - lanes.get_global_rect().position.y
			view_h = clip.size.y
	if focus_key != timeline_focus_key and lanes and lanes.is_visible_in_tree() and view_h >= 20.0:
		timeline_focus_key = focus_key
		var top := -1.0
		var tall := 30.0
		if lane == "layer" and active_layer >= 0 and active_layer < layers.size(): top = timeline.layer_y(active_layer) - 3
		elif lane == "model":
			for i in timeline.object_rows.size():
				if timeline.object_rows[i].id == timeline.selected_id: top = timeline.row_y(i); tall = 26.0; break
		if top >= 0.0 and (top < lanes.scroll_vertical + view_top or top + tall > lanes.scroll_vertical + view_top + view_h):
			var target := int(maxf(0.0, top + tall - view_top - view_h))
			if StudioTheme.is_neon() and target > 0:
				# Snap to the next lane boundary so no sliver of the row above (its row line) shows.
				var bounds: Array = []
				if not timeline.object_rows.is_empty():
					for k in range(timeline.visual_rows.size() + 1): bounds.append(timeline.header_height() + k * TimelineView.ROW_HEIGHT)
				for i in range(layers.size()): bounds.append(timeline.layer_y(i) - 3)
				bounds.append(timeline.audio_y())
				var snap_to := INF
				for b in bounds:
					if b >= target - 0.5 and b < snap_to and b <= top: snap_to = b
				if snap_to < INF: target = int(ceilf(snap_to - 0.01))
			# The lanes cull rows by scroll position when drawn, so redraw after scrolling.
			(func(): lanes.scroll_vertical = target; timeline.queue_redraw()).call_deferred()
	if timeline_ruler.focus_lane != lane:
		timeline_ruler.focus_lane = lane
		timeline_ruler.queue_redraw()

func set_advanced(enabled: bool) -> void:
	# Presentation only: never reset project values, shot/navigation, transport or undo.
	advanced_mode = enabled
	advanced_toggle.set_pressed_no_signal(enabled)
	if pose_editor:pose_editor.refresh_labels()
	if timeline:timeline.set_label_mode(enabled)
	if timeline_ruler and timeline_ruler.ruler_seconds == enabled: timeline_ruler.ruler_seconds = not enabled; timeline_ruler.queue_redraw()
	if transport_info: refresh_transport_text()
	timeline_focus_key = ""  # the taller Advanced chrome can push the edited lane out of view
	if StudioTheme.is_neon() and timeline and timeline.get_parent() is ScrollContainer and timeline.get_parent().name == "TimelineScroll":
		timeline.get_parent().custom_minimum_size.y = 30 if enabled else 56  # same rule as fit_panels
	if sequence_editor: sequence_editor.refresh()  # neon Simple hides the root "Main scene" crumb
	if timeline_navigation and timeline_navigation.scrollbar: timeline_navigation.update_controls()
	if world_selection and world_selection.has_method("refresh_actions"): world_selection.refresh_actions()
	# Neon: docked panels show their title bar only in Advanced (a thin grab strip in Simple).
	if workspace_layout and workspace_layout.horizontal:
		for id in workspace_layout.panels: workspace_layout.style_header(id)
	refresh_workspace()
	# A message carried over from Advanced (where nothing fades) still fades in Simple.
	if not enabled and not status_faded and status and not status.text.is_empty(): schedule_status_fade(status_serial)

func refresh_workspace() -> void:
	canvas.scene_navigation = mode.selected == 1
	canvas.tooltip_text = "Click: select • Ctrl + left: free fly • Left drag: move • Right click: menu/deselect • Right drag: POV • Middle: dolly • Esc: release" if mode.selected == 1 else "Wheel: zoom • Middle drag: pan • %s: play/pause" % keyboard_shortcuts.label_for("play")
	if mode.selected == 2: canvas.tooltip_text = "Hold Alt: reveal bones • Click joint; drag RGB handles • Edits auto-key • Right click: object menu / deselect • Esc: cancel"
	if mode.selected in [1,2] and navigation_scheme=="orbit":
		canvas.tooltip_text=canvas.tooltip_text.replace("Ctrl + left: free fly","Ctrl + left: orbit")+" • Orbit: Ctrl+left • Pan: Ctrl+right • Dolly: Ctrl+wheel"
	for control in advanced_controls: control.visible = advanced_mode
	for control in simple_controls: control.visible = not advanced_mode
	refresh_mode_tabs()
	refresh_physics_bar()
	if stage_overlay: set_codex_compact(not advanced_mode)
	for control in tool_buttons: set_tool_kbd(control) # keycaps follow rebound shortcuts
	refresh_tool_strip()
	if camera_strip: camera_strip.visible = not advanced_mode and mode.selected == 1
	refresh_status_style()
	if undo_button: undo_button.text = "Undo" if advanced_mode else ""; redo_button.text = "Redo" if advanced_mode else ""
	drawing_section.get_parent().visible = advanced_mode or mode.selected == 0
	camera_section.get_parent().visible = advanced_mode or mode.selected == 1
	pose_editor.panel.get_parent().visible = advanced_mode or mode.selected == 2
	audio_section.get_parent().visible = advanced_mode or not audio_clip.is_empty()
	workspace_label.text = "Advanced workspace" if advanced_mode else "Simple workspace"
	inspector_scroll.scroll_vertical = 0
	if pose_editor:pose_editor.refresh_values()
	if scene_view:scene_view.sync()
	refresh_camera_inspector()
	refresh_view_row()
	refresh_badges()
	queue_view_fit()
	queue_stage_inset()
	fit_header()

func physics_live() -> bool:
	return physics_editor != null and (physics_editor.is_running() or (physics_editor.recording != null and physics_editor.recording.active))

func refresh_physics_bar() -> void:
	# Preserve the existing Simple simulation entry points even while idle.
	# The neon stage inset already reserves space when this strip is visible.
	if physics_bar != null and not physics_bar.visible: physics_bar.visible = true

func style_accent(control: Button) -> void:
	# Redesign: Export movie gets a light pill on hover so the main action stands out.
	var accent := StyleBoxFlat.new()
	accent.bg_color = Color(1, 1, 1, 0.22)
	accent.border_color = Color(1, 1, 1, 0.6)
	accent.set_border_width_all(1)
	accent.set_corner_radius_all(8)
	accent.set_content_margin_all(6)
	control.add_theme_stylebox_override("hover", accent)

func refresh_title() -> void:
	# Neon Pro step 2: the bar shows the project name (or "Untitled") over a save line; the window
	# title stays "Hybrid Animation Studio". "Saved N min ago" only counts from a save seen in this
	# session (dirty turning false while the recovery status reports the save); nothing is invented.
	if title_label == null: return
	var named: bool = has_project != null and not has_project.path.is_empty()
	var shown: String = has_project.path.get_file().get_basename() if named else project_folder.get_file() if not project_folder.is_empty() else "Untitled"
	named = named or not project_folder.is_empty()
	var identity: String = (has_project.path if has_project != null else "") + "|" + project_folder
	if identity != header_identity:
		header_identity = identity
		header_saved_at = -1
	var report := recovery_status.text if recovery_status else ""
	if header_was_dirty and not dirty:
		header_saved_at = Time.get_ticks_msec() if report in ["Project saved", "Saved; recovery copy retained"] else -1
	header_was_dirty = dirty
	var state := "new"
	var line := "Not saved yet"
	if dirty:
		state = "dirty"; line = "Unsaved changes"
	elif header_saved_at >= 0 and named:
		state = "saved"
		var minutes := int((Time.get_ticks_msec() - header_saved_at) / 60000.0)
		line = "Saved just now" if minutes < 1 else "Saved %d min ago" % minutes if minutes < 60 else "Saved %d h ago" % int(minutes / 60.0)
	elif named:
		state = "saved"; line = "Saved"
	var changed := false
	if title_label.text != shown:
		title_label.text = shown
		header_mark.tooltip_text = shown
		changed = true
	if save_label.text != line:
		save_label.text = line
		save_dot.add_theme_stylebox_override("panel", save_dot_style(state))
		changed = true
	if header_project.tooltip_text != report: header_project.tooltip_text = report
	if changed: fit_header()

func save_dot_style(state: String) -> StyleBoxFlat:
	# 6 px dot: mint with a soft glow when saved, amber when there are unsaved changes, grey when the
	# project has never been saved.
	if not header_dots.has(state):
		var colour: Color = {"saved": StudioTheme.SAVED, "dirty": StudioTheme.WARNING}.get(state, StudioTheme.TEXT3)
		var glow := Color(colour, 0.7) if state == "saved" else Color.TRANSPARENT
		header_dots[state] = StudioTheme.flat(colour, Color.TRANSPARENT, 3, 0, Vector4(0, 0, 0, 0), glow, 3 if state == "saved" else 0)
	return header_dots[state]

func pick_scene_file() -> void:
	choose_file("Import 3D environment", ["*.has", "*.gltf", "*.fbx", "*.obj", "*.pmd", "*.pmx", "*.bsp", "*.gma", "*.bin"], func(path):import_actions.add(path,false,0), source_import.default_browse_dir())

func build_ui() -> void:
	theme = StudioTheme.make_theme()
	get_window().theme=theme
	var back := TextureRect.new()
	back_texture = back
	back.texture = back_gradient()
	back.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	back.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	back.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(back)
	var shell := VBoxContainer.new()
	var workspace_scroll := ScrollContainer.new()
	workspace_scroll.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	workspace_scroll.follow_focus = true
	add_child(workspace_scroll)
	shell.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	shell.size_flags_vertical = Control.SIZE_EXPAND_FILL
	shell.add_theme_constant_override("separation", 0)
	workspace_scroll.add_child(shell)
	var title_panel := PanelContainer.new()
	var header_style := StyleBoxTexture.new()
	header_box = header_style
	title_panel.add_theme_stylebox_override("panel", header_style)
	shell.add_child(title_panel)
	# Neon Pro step 2: one 56 px bar: brand mark + project name/save line, ghost New / Open / Save,
	# Add, centred Draw / Camera / Pose (an overlay, see below), Advanced switch, More, Settings and
	# Export movie. Advanced adds a wrapping row with its extra buttons under it.
	var header_column := VBoxContainer.new()
	header_column.add_theme_constant_override("separation", 0)
	title_panel.add_child(header_column)
	var title_row := HBoxContainer.new()
	header_row = title_row
	title_row.custom_minimum_size.y = 56
	title_row.add_theme_constant_override("separation", 4)
	header_column.add_child(title_row)
	var brand_margin := MarginContainer.new()
	brand_margin.add_theme_constant_override("margin_right", 8)
	brand_margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	title_row.add_child(brand_margin)
	var brand := HBoxContainer.new()
	brand.add_theme_constant_override("separation", 12)
	brand.mouse_filter = Control.MOUSE_FILTER_IGNORE
	brand_margin.add_child(brand)
	header_mark = TextureRect.new()
	header_mark.texture = StudioTheme.brand_mark()
	header_mark.custom_minimum_size = Vector2(28, 28)
	header_mark.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	header_mark.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	header_mark.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	header_mark.tooltip_text = "Untitled"
	brand.add_child(header_mark)
	header_project = VBoxContainer.new()
	header_project.alignment = BoxContainer.ALIGNMENT_CENTER
	header_project.add_theme_constant_override("separation", 1)
	header_project.mouse_filter = Control.MOUSE_FILTER_PASS
	brand.add_child(header_project)
	title_label = label(header_project, "Untitled")
	title_label.add_theme_font_override("font", StudioTheme.font(600))
	title_label.add_theme_font_size_override("font_size", 14)
	var save_line := HBoxContainer.new()
	save_line.add_theme_constant_override("separation", 6)
	save_line.mouse_filter = Control.MOUSE_FILTER_IGNORE
	header_project.add_child(save_line)
	save_dot = Panel.new()
	save_dot.custom_minimum_size = Vector2(6, 6)
	save_dot.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	save_dot.mouse_filter = Control.MOUSE_FILTER_IGNORE
	save_dot.add_theme_stylebox_override("panel", save_dot_style("new"))
	save_line.add_child(save_dot)
	save_label = label(save_line, "Not saved yet")
	save_label.add_theme_font_size_override("font_size", 12)
	apply_header_style()
	header_divider(title_row)
	header_button(title_row, "New", "new", new_dialog, "Start an empty world • unsaved edits are protected by a confirmation")
	header_button(title_row, "Open", "open", open_dialog, "Open an editable project")
	keyboard_shortcuts.decorate(header_button(title_row, "Save", "save", save),"save","Save project")
	simple_only(header_divider(title_row))
	simple_only(menu_button(title_row, "Add", "add", [
		["3D scene or map…", pick_scene_file],
		["Poseable model…", func(): pose_editor.import_dialog()],
		["Installed content…", func(): source_browser.open()],
		["Audio (WAV, MP3, Ogg)…", func(): choose_audio_at_playhead()]],
		"Add a scene, a model, installed content or audio"))
	header_spacer = Control.new()
	header_spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header_spacer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	title_row.add_child(header_spacer)
	# The Advanced switch stays a Button (CheckButton) whose pressed signal reads button_pressed.
	var switch := CheckButton.new()
	advanced_toggle = switch
	switch.text = "Advanced"
	switch.focus_mode = Control.FOCUS_NONE
	switch.pressed.connect(func(): set_advanced(advanced_toggle.button_pressed))
	switch.tooltip_text = "Show detailed controls. Your scene, drawings, audio and settings keep working in either mode."
	switch.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	title_row.add_child(switch)
	if StudioTheme.is_neon():
		switch.custom_minimum_size.y = 40
		switch.add_theme_font_override("font", StudioTheme.font(500))
		switch.add_theme_font_size_override("font_size", 13)
		switch.add_theme_constant_override("h_separation", 10)
		var switch_pad := Vector4(12, 0, 12, 0)
		var switch_clear := StudioTheme.flat(Color.TRANSPARENT, Color.TRANSPARENT, 8, 0, switch_pad)
		var switch_hover := StudioTheme.flat(StudioTheme.HOVER, Color.TRANSPARENT, 8, 0, switch_pad)
		override_button_boxes(switch, switch_clear, switch_hover, switch_clear, switch_clear)
		switch.add_theme_stylebox_override("hover_pressed", switch_hover)
		switch.add_theme_stylebox_override("hover_pressed_mirrored", switch_hover)
		for state in ["font_color", "font_focus_color", "font_pressed_color"]: switch.add_theme_color_override(state, StudioTheme.TEXT2)
		for state in ["font_hover_color", "font_hover_pressed_color"]: switch.add_theme_color_override(state, StudioTheme.TEXT)
	simple_only(menu_button(title_row, "More", "more", [
		["Home screen…", func(): home.open_home()],
		["Recover…", func(): show_recovery()],
		["Project options…", func(): show_project_options()],
		["Interface size and fullscreen…", func(): show_display_settings()],
		["Keyboard shortcuts…", func(): keyboard_shortcuts.open()],
		["About and credits", func(): show_notices()]], "Home screen, recovery, project options, shortcuts and credits"))
	var gear := header_button(title_row, "" if StudioTheme.is_neon() else "Settings", "settings", show_display_settings, "Settings: interface scale and fullscreen (F11). Advanced also offers orbit camera controls.")
	gear.custom_minimum_size.x = 40
	# Neon Simple: More > "Interface size and fullscreen…" is the one way in (the mock has no gear).
	if StudioTheme.is_neon(): advanced(gear)
	header_divider(title_row)
	export_button = icon_button(title_row, "Export movie", "export", export_dialog, "Export MP4 beside your saved HAS project, with a recoverable PNG frame sequence")
	style_export(export_button)
	# Advanced: every extra file/scene/help button, as ghost icon+label buttons that wrap.
	var advanced_row := MarginContainer.new()
	advanced_row.add_theme_constant_override("margin_bottom", 4)
	header_column.add_child(advanced_row)
	advanced(advanced_row)
	var toolbar := HFlowContainer.new()
	toolbar.add_theme_constant_override("h_separation", 4)
	toolbar.add_theme_constant_override("v_separation", 4)
	advanced_row.add_child(toolbar)
	workspace_label = label(toolbar, "Simple workspace")
	workspace_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	workspace_label.custom_minimum_size.y = 40
	workspace_label.add_theme_font_size_override("font_size", 12)
	apply_header_style()
	header_button(toolbar,"Home","home",func():home.open_home(),"New, Open and recent projects; your current scene stays intact")
	header_button(toolbar, "Recover", "reset", show_recovery, "Review retained recovery checkpoints")
	header_button(toolbar, "Save as…", "save", save_as)
	header_button(toolbar, "Open folder…", "folder", func():
		var action := func(): choose_directory("Open legacy project directory", open_project)
		if dirty: confirm_action("Discard unsaved edits and open another project?", action)
		else: action.call())
	header_button(toolbar, "Sample room", "building", demo_dialog, "Open the original camera/drawing example as a new unsaved project")
	header_button(toolbar, "Add scene", "scene", pick_scene_file, "Add a 3D environment: GLB, glTF, FBX, OBJ, MMD or an installed Source map")
	header_button(toolbar, "Add model", "figure", pose_editor.import_dialog, "Add a poseable standard GLB model beside the environment")
	header_button(toolbar, "Installed", "package", func(): source_browser.open(), "Browse installed GMod models/maps, Workshop addons and dependency mounts")
	header_button(toolbar, "Add audio", "audio", choose_audio_at_playhead, "Add a WAV, MP3 or Ogg sound starting at the playhead")
	header_button(toolbar,"Options","grid",show_project_options,"Project settings, including visibility fades. Saved with this HAS project.")
	header_button(toolbar, "About", "help", show_notices, "Credits and open source notices")
	# The Advanced row keeps its labels (it wraps instead); only main-row buttons go icon-only.
	header_compact.assign(header_compact.filter(func(control): return control.get_parent() == title_row))
	# Centre: Draw / Camera / Pose tab group as a full-width overlay that ignores the mouse, so it is
	# centred on the window and never adds to the bar's minimum width (the tabs are built below).
	header_tab_overlay = CenterContainer.new()
	header_tab_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	title_panel.add_child(header_tab_overlay)
	simple_only(header_tab_overlay)
	header_tab_frame = PanelContainer.new()
	header_tab_frame.add_theme_stylebox_override("panel", StudioTheme.flat(Color("0f1015"), StudioTheme.LINE, 10, 1, Vector4(4, 4, 4, 4)) if StudioTheme.is_neon() else StyleBoxEmpty.new())
	header_tab_overlay.add_child(header_tab_frame)
	header_tabs = HBoxContainer.new()
	header_tabs.add_theme_constant_override("separation", 2)
	header_tab_frame.add_child(header_tabs)
	title_row.resized.connect(fit_header)
	var margin := MarginContainer.new()
	margin.size_flags_vertical = Control.SIZE_EXPAND_FILL
	for side in ["left", "right", "top", "bottom"]:
		# Neon Pro step 3: the World rail sits flush against the window edge and the header bar; the
		# inspector and the timeline reach the right and bottom edges too (mock grid, no outer margin).
		margin.add_theme_constant_override("margin_" + side, 0 if StudioTheme.is_neon() else 10)
	shell.add_child(margin)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 0 if StudioTheme.is_neon() else 8)
	margin.add_child(column)
	var middle := HBoxContainer.new()
	middle.size_flags_vertical = Control.SIZE_EXPAND_FILL
	column.add_child(middle)
	var hierarchy := VBoxContainer.new()
	# Neon Pro step 3: the World dock opens as the 64 px icon rail (classic keeps its 156 px list).
	hierarchy.custom_minimum_size.x = 64 if StudioTheme.is_neon() else 156
	middle.add_child(hierarchy)
	world_selection.setup(hierarchy)
	var center := VBoxContainer.new()
	center.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	# Neon Pro step 4: the centre column is the #05060A stage (view row, canvas, stage footer).
	# The stage panel takes the centre's place, so workspace_layout still moves middle's child 1.
	var neon_stage := StudioTheme.is_neon()
	if neon_stage:
		stage_panel = PanelContainer.new()
		stage_panel.name = "Stage"
		stage_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		stage_panel.add_theme_stylebox_override("panel", StudioTheme.flat(StudioTheme.STAGE, Color.TRANSPARENT, 0, 0, Vector4(0, 0, 0, 0)))
		middle.add_child(stage_panel)
		center.add_theme_constant_override("separation", 0)
		stage_panel.add_child(center)
	else:
		middle.add_child(center)
	var view_strip:=ScrollContainer.new();view_strip.name="ViewControlsScroll";view_strip.follow_focus=true
	view_strip.horizontal_scroll_mode=ScrollContainer.SCROLL_MODE_AUTO;view_strip.vertical_scroll_mode=ScrollContainer.SCROLL_MODE_DISABLED
	center.add_child(view_strip)
	var view_toolbar := HBoxContainer.new()
	if neon_stage:
		# View row: the tool pill (or the Camera / Pose strip) on the left, badges on the right, and
		# Codex's view controls in a second small pill that drops to a second line when space is short.
		var view_margin := MarginContainer.new()
		view_margin.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		for side in [["left", 12], ["right", 12], ["top", 5], ["bottom", 3]]: view_margin.add_theme_constant_override("margin_" + side[0], side[1])
		view_scroll = view_strip
		stage_view_margin = view_margin
		view_strip.resized.connect(queue_view_fit)
		view_strip.add_child(view_margin)
		var view_rows := VBoxContainer.new()
		view_rows.add_theme_constant_override("separation", 6)
		view_margin.add_child(view_rows)
		view_row = HBoxContainer.new()
		view_row.add_theme_constant_override("separation", 8)
		view_rows.add_child(view_row)
		view_row2 = HBoxContainer.new()
		view_row2.add_theme_constant_override("separation", 8)
		# The rows float over the canvas: only the pills and their buttons take the mouse.
		for holder in [view_strip, view_margin, view_rows, view_row, view_row2]: holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
		view_row2.visible = false
		view_rows.add_child(view_row2)
		codex_pill = view_pill(view_row)
		view_toolbar.add_theme_constant_override("separation", 4)
		codex_pill.add_child(view_toolbar)
	else:
		view_strip.add_child(view_toolbar)
	mode = OptionButton.new()
	mode.add_icon_item(StudioTheme.icon("draw"), "Draw")
	mode.add_icon_item(StudioTheme.icon("camera"), "Scene / camera")
	mode.add_icon_item(StudioTheme.icon("scene"), "Pose model")
	mode.add_theme_constant_override("icon_max_width", 22)
	mode.item_selected.connect(change_mode)
	mode.tooltip_text = "Draw on independent layers, or move the temporary 3D camera."
	view_toolbar.add_child(mode)
	advanced(mode)
	# Redesign: Simple shows Draw / Camera / Pose tabs instead of the dropdown.
	# Neon Pro step 2: the tabs live in the header's centred group (header_tabs).
	var tab_group := ButtonGroup.new()
	for tab in [["Draw", "draw"], ["Camera", "camera"], ["Pose", "figure"]]:
		var index := mode_tabs.size()
		var t := icon_button(header_tabs, tab[0], tab[1], func(): pick_mode(index), tab[0] + " mode")
		t.toggle_mode = true
		t.button_group = tab_group
		style_tab(t, tab[1])
		mode_tabs.append(t)
		simple_only(t)
	lighting_choice=OptionButton.new()
	for lighting_title in ["Unshaded","Lit","Studio light"]:lighting_choice.add_item(lighting_title)
	lighting_choice.tooltip_text="Unshaded shows base colors. Lit uses imported scene lights. Studio light retains older projects' illumination."
	lighting_choice.item_selected.connect(change_lighting)
	view_toolbar.add_child(lighting_choice)
	# Redesign: Simple Draw tool strip; drives the tool dropdown (Advanced Drawing panel).
	tool_strip = HBoxContainer.new()
	if neon_stage:
		# Neon Pro step 4: labelled tools with keycaps in the floating pill (divider before Select area).
		tool_pill = view_pill(view_row)
		tool_strip.add_theme_constant_override("separation", 2)
		tool_pill.add_child(tool_strip)
		view_row.move_child(tool_pill, 0)
	else:
		view_toolbar.add_child(tool_strip)
		tool_strip.add_child(VSeparator.new())
	var tool_group := ButtonGroup.new()
	var tool_shortcuts := ["pen", "eraser", "fill", "sample", ""]  # keycaps (mock: none on Select area)
	for entry in [["Pen", "draw", "B"], ["Eraser", "eraser", "E"], ["Fill", "fill", "F"], ["Pick color", "picker", "I"], ["Select area", "cel", "M"]]:
		var tool_index := tool_buttons.size()
		if neon_stage and tool_index == 4: pill_divider(tool_strip)
		var tb := icon_button(tool_strip, "", entry[1], func(): pick_tool(tool_index), "%s [%s]" % [entry[0], entry[2]])
		tb.toggle_mode = true
		tb.button_group = tool_group
		tb.custom_minimum_size = Vector2(40, 36)
		# The tooltip's key follows keyboard_shortcuts like the keycaps (set_tool_kbd).
		tb.set_meta("tool_name", entry[0])
		tb.set_meta("tool_key", TOOL_KEYS[tool_index])
		if neon_stage: style_tool_button(tb, entry[0], "select" if tool_index == 4 else entry[1], tool_shortcuts[tool_index])
		tool_buttons.append(tb)
	# Redesign: Simple Camera mode has its main action beside the tabs.
	camera_strip = HBoxContainer.new()
	if neon_stage:
		# Neon Pro step 4: Save key, then a "Mouse and keys" popover with the camera help and a hint.
		camera_pill = view_pill(view_row)
		camera_strip.add_theme_constant_override("separation", 2)
		camera_pill.add_child(camera_strip)
		view_row.move_child(camera_pill, 1)
		var save_key := icon_button(camera_strip, "Save key", "key", key_dialog, "Save camera key at this frame")
		style_save_key(save_key)
		keyboard_shortcuts.decorate(save_key, "camera", "Save camera key at this frame")
		pill_divider(camera_strip)
		camera_help_button = icon_button(camera_strip, "Mouse and keys", "help", func(): show_help_popover(camera_help_button, "Camera: mouse and keys", camera_help_label.text if camera_help_label else ""), "Show the camera mouse and keyboard controls")
		style_ghost(camera_help_button, "help")
		var hint := HBoxContainer.new()
		hint.add_theme_constant_override("separation", 6)
		hint.mouse_filter = Control.MOUSE_FILTER_IGNORE
		hint.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		var hint_margin := MarginContainer.new()
		hint_margin.add_theme_constant_override("margin_left", 6)
		hint_margin.add_theme_constant_override("margin_right", 10)
		hint_margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
		hint_margin.add_child(hint)
		# Mock: plain text after the pill (14 px gap with the row's 8 px separation), not inside it.
		hint_margin.add_theme_constant_override("margin_right", 0)
		view_row.add_child(hint_margin)
		view_row.move_child(hint_margin, camera_pill.get_index() + 1)
		overlay_icon(hint, "mouse", StudioTheme.TEXT2, 14)
		overlay_label(hint, "Move the view with the mouse", StudioTheme.TEXT2, 12)
		camera_hint = hint_margin
		# New Simple-only Pose strip: drives pose_editor.operation (Rotate / Move) and shows the
		# canvas posing help. "Turn model" = Rotate with the model root selected (no new semantics).
		pose_strip = HBoxContainer.new()
		pose_pill = view_pill(view_row)
		pose_strip.add_theme_constant_override("separation", 2)
		pose_pill.add_child(pose_strip)
		view_row.move_child(pose_pill, 2)
		var pose_group := ButtonGroup.new()
		for entry in [["Pose joints", "joint", "Rotate the selected joint or model with the colored rings"], ["Move model", "move", "Move the selected model or joint"]]:
			var operation_index := pose_buttons.size()
			var pb := icon_button(pose_strip, entry[0], entry[1], func(): pick_pose_operation(operation_index), entry[2])
			pb.toggle_mode = true
			pb.button_group = pose_group
			style_tool_button(pb, entry[0], entry[1])
			pose_buttons.append(pb)
		turn_button = icon_button(pose_strip, "Turn model", "turn", pick_turn_model, "Turn the whole model with the colored rings")
		turn_button.toggle_mode = true
		turn_button.button_group = pose_group
		style_tool_button(turn_button, "Turn model", "turn")
		pill_divider(pose_strip)
		pose_help_button = icon_button(pose_strip, "Mouse and keys", "help", func(): show_help_popover(pose_help_button, "Posing: mouse and keys", canvas.tooltip_text.replace(" • ", "\n")), "Show the posing mouse and keyboard controls")
		style_ghost(pose_help_button, "help")
	else:
		view_toolbar.add_child(camera_strip)
		camera_strip.add_child(VSeparator.new())
		icon_button(camera_strip, "Save key", "key", key_dialog, "Save camera key at this frame")
	simple_only(camera_strip)
	# Codex shows Fit view in Simple too; neon Simple shows it only while the canvas is zoomed or
	# panned (sync_fit_view), the one way back without switching to Advanced.
	fit_view_button = button(view_toolbar, "Fit view", func(): canvas.zoom = 1; canvas.pan = Vector2.ZERO; canvas.queue_redraw(); queue_view_fit())
	frame_scene_button = button(view_toolbar, "Frame scene", frame_3d_scene)
	frame_scene_button.tooltip_text = "Fit the 3D asset in the temporary editor camera; shot keys stay unchanged."
	undo_button = keyboard_shortcuts.decorate(icon_button(view_toolbar, "Undo", "undo", undo),"undo","Undo") as Button
	redo_button = keyboard_shortcuts.decorate(icon_button(view_toolbar, "Redo", "redo", redo),"redo","Redo") as Button
	var physics_strip:=ScrollContainer.new();physics_strip.name="PhysicsControlsScroll";physics_strip.follow_focus=true
	physics_strip.horizontal_scroll_mode=ScrollContainer.SCROLL_MODE_AUTO;physics_strip.vertical_scroll_mode=ScrollContainer.SCROLL_MODE_DISABLED
	center.add_child(physics_strip);physics_bar=physics_strip
	var physics_toolbar:=HBoxContainer.new()
	if neon_stage:
		var physics_margin := MarginContainer.new()
		physics_margin.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		for side in [["left", 12], ["right", 12], ["top", 3], ["bottom", 3]]: physics_margin.add_theme_constant_override("margin_" + side[0], side[1])
		physics_strip.add_child(physics_margin)
		var physics_row := HBoxContainer.new();physics_margin.add_child(physics_row)
		for holder in [physics_strip, physics_margin, physics_row]: holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
		view_pill(physics_row).add_child(physics_toolbar)
		physics_toolbar.add_theme_constant_override("separation", 4)
	else:physics_strip.add_child(physics_toolbar)
	physics_editor.setup(physics_toolbar)
	if neon_stage:style_view_chips(physics_toolbar.get_children())
	canvas = CanvasView.new()
	canvas.custom_minimum_size = Vector2(400, 180)
	canvas.size_flags_vertical = Control.SIZE_EXPAND_FILL
	canvas.background = renderer.viewport.get_texture()
	canvas.pointer.connect(canvas_input)
	canvas.middle_target=middle_pose_target
	canvas.middle_clicked=cycle_pose_operation
	canvas.tooltip_text = "Wheel: zoom • Middle drag: pan • Space: play/pause"
	if neon_stage:
		# Neon Pro: the canvas fills the whole stage, like the mock's 1088x684 viewport. The view rows,
		# the physics row and the stage footer float over it (StageOverlay, mouse ignored except on the
		# pills), and CanvasView.fit_inset keeps the camera frame clear of them (fit_stage_inset()).
		# The viewfinder corners are drawn by an overlay sibling above the canvas that ignores the mouse.
		var canvas_holder := MarginContainer.new()
		canvas_holder.name = "StageCanvas"
		canvas_holder.size_flags_vertical = Control.SIZE_EXPAND_FILL
		for side in ["left", "right", "top", "bottom"]: canvas_holder.add_theme_constant_override("margin_" + side, 0)
		center.add_child(canvas_holder)
		canvas_holder.add_child(canvas)
		viewfinder = Control.new()
		viewfinder.name = "Viewfinder"
		viewfinder.mouse_filter = Control.MOUSE_FILTER_IGNORE
		canvas_holder.add_child(viewfinder)
		viewfinder.draw.connect(draw_viewfinder)
		canvas.draw.connect(viewfinder.queue_redraw)
		stage_overlay = Control.new()
		stage_overlay.name = "StageOverlay"
		stage_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
		canvas_holder.add_child(stage_overlay)
		stage_top = VBoxContainer.new()
		stage_top.name = "StageTop"
		stage_top.mouse_filter = Control.MOUSE_FILTER_IGNORE
		stage_top.add_theme_constant_override("separation", 0)
		stage_overlay.add_child(stage_top)
		stage_top.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE)
		view_strip.reparent(stage_top, false)
		physics_strip.reparent(stage_top, false)
		stage_top.resized.connect(queue_stage_inset)
		canvas.resized.connect(queue_stage_inset)
	else:
		center.add_child(canvas)
	# Redesign: friendly next step on an empty world / frame (Simple only; a child of the canvas control, not the film).
	empty_hint = PanelContainer.new()
	empty_hint.mouse_filter = Control.MOUSE_FILTER_IGNORE
	empty_hint_label = label(empty_hint, "")
	style_empty_hint()
	empty_hint_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	empty_hint_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	empty_hint.visible = false
	canvas.add_child(empty_hint)
	empty_hint.set_anchors_and_offsets_preset(Control.PRESET_CENTER_TOP)
	empty_hint.position.y = 24
	empty_hint.grow_horizontal = Control.GROW_DIRECTION_BOTH
	scene_view=preload("res://src/scene_view.gd").new();add_child(scene_view);scene_view.setup(self,view_toolbar)
	if neon_stage:
		build_view_badges()
		style_view_chips([mode, lighting_choice, scene_view.choice, scene_view.frame_button, scene_view.grid_button, scene_view.guides_button])
		for b in view_toolbar.get_children():
			if b is Button and b.text in ["Fit view", "Frame scene"]: style_view_chips([b])
		for b in [undo_button, redo_button]: style_ghost(b, "undo" if b == undo_button else "redo", 32)
		build_stage_footer(stage_overlay)
	else:
		scene_name = label(center, "")
	scene_name.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	var scroll := ScrollContainer.new()
	inspector_scroll = scroll
	scroll.custom_minimum_size.x = 276
	if StudioTheme.is_neon():
		# Neon Pro step 5: 288 px inspector on #0C0D11 with a 1 px #22252E line on its left.
		scroll.custom_minimum_size.x = 288
		var inspector_bg := StudioTheme.flat(StudioTheme.BAR, StudioTheme.LINE, 0, 0, Vector4(1, 0, 0, 0))
		inspector_bg.border_width_left = 1
		scroll.add_theme_stylebox_override("panel", inspector_bg)
		# Thin 4 px bar (the mock has none; Simple Draw overflows at 1440x900) with the theme's
		# 3:1 thumb; the sections' right pad shrinks by its width while it shows.
		var bar := scroll.get_v_scroll_bar()
		for state in ["scroll", "scroll_focus"]: bar.add_theme_stylebox_override(state, StudioTheme.flat(Color.TRANSPARENT, Color.TRANSPARENT, 2, 0, Vector4(2, 0, 2, 0)))
		for pair in [["grabber", StudioTheme.SCROLL_THUMB], ["grabber_highlight", StudioTheme.TEXT3], ["grabber_pressed", StudioTheme.TEXT2]]: bar.add_theme_stylebox_override(pair[0], StudioTheme.flat(pair[1], Color.TRANSPARENT, 2, 0, Vector4(2, 0, 2, 0)))
		bar.visibility_changed.connect(fit_inspector_pad)
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	middle.add_child(scroll)
	controls = VBoxContainer.new()
	controls.custom_minimum_size.x = 256
	controls.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(controls)
	drawing_section = section(controls, "Drawing", "draw")
	layer_choice = OptionButton.new()
	for layer in layers: layer_choice.add_item(layer.name)
	layer_choice.select(active_layer)
	layer_choice.item_selected.connect(func(index): finish_stroke(); active_layer = index; refresh_layer())
	drawing_section.add_child(layer_choice)
	layer_visibility = CheckButton.new()
	layer_visibility.text = "Show this layer"
	layer_visibility.button_pressed = true
	layer_visibility.toggled.connect(func(visible):
		if layer_editor:layer_editor.set_visible(visible))
	drawing_section.add_child(layer_visibility)
	tool = OptionButton.new()
	tool.add_item("Pen [B]")
	tool.add_item("Eraser [E]")
	tool.add_item("Fill [F]")
	tool.add_item("Pick color [I]")
	tool.add_item("Select area [M]")
	tool.item_selected.connect(func(_index):
		finish_stroke()
		if drawing_selection_editor:drawing_selection_editor.cancel()
		if fill_editor:fill_editor.refresh())
	tool.item_selected.connect(func(index):
		if index==3 and color_sampler:color_sampler.call_deferred("arm"))
	drawing_section.add_child(tool)
	color = ColorPickerButton.new()
	color.color = Color("f4dfbd")
	color.custom_minimum_size.y = 32
	color.tooltip_text = "Drawing color"
	drawing_section.add_child(color)
	radius = spin(drawing_section, "Brush size (radius in pixels)", 1, 64, 6)
	brush_opacity = spin(drawing_section, "Brush opacity (%)", 0, 100, 100)
	brush_opacity.tooltip_text = "Pen opacity / eraser strength for each stroke. Overlapping passes within one stroke stay even; release and draw again to build up. Fill keeps its own controls."
	brush_pressure=CheckButton.new();brush_pressure.text="Tablet pressure size"
	brush_pressure.tooltip_text="Off: normal mouse brush. On: pen pressure controls size; waits for positive pressure before painting. Turn off for a mouse or a tablet driver that supplies no pressure. Fill is unchanged."
	drawing_section.add_child(brush_pressure)
	brush_smoothing=advanced_spin(drawing_section,"Stroke smoothing (pixels)",0,32,0)
	brush_smoothing.tooltip_text="0 keeps the original brush. Larger values reduce jitter by trailing the pointer in canvas pixels; the tail finishes on release. Mouse and tablet; pressure still controls size."
	new_drawing_button = icon_button(drawing_section, "New drawing", "cel", func(): create_cel(false), "Start a blank cel at this frame; it holds until the next drawing.")
	copy_drawing_button = button(drawing_section, "Copy drawing here", func(): create_cel(true))
	copy_drawing_button.tooltip_text = "Make an independent copy of the held drawing at this frame."
	exposure = advanced_spin(drawing_section, "Exposure length (frames)", 1, preload("res://src/extended_timing.gd").MAX_FRAMES, 48)
	exposure_button = advanced(button(drawing_section, "Set held cel exposure", set_exposure))
	delete_cel_button = advanced(button(drawing_section, "Delete held cel", delete_cel))
	camera_section = section(controls, "Camera", "camera")
	camera_help_label = label(camera_section, "Ctrl + left: free camera / WASD
Left drag: move sideways / up
Right drag: adjust view direction
Right + wheel: change lens zoom
Middle drag: move forward / back
Left + right drag: roll camera
WASD / Q,E: fly while dragging
Shift: faster • Esc: release mouse")
	fov = advanced_spin(camera_section, "Editor camera FOV", 15, 120, 60)
	fov.value_changed.connect(func(value):
		if mode.selected != 1 or exporting: refresh_camera_controls();return
		renderer.camera.fov = value
		camera_preview_hint())
	camera_near=advanced_spin(camera_section,"Nearest visible distance",0.001,Timeline.MAX_FAR,0.05);camera_near.step=0.001
	camera_far=advanced_spin(camera_section,"Farthest visible distance",0.001,Timeline.MAX_FAR,2000);camera_far.step=0.001
	camera_near.value_changed.connect(func(value):change_camera_range(value,true))
	camera_far.value_changed.connect(func(value):change_camera_range(value,false))
	camera_far.tooltip_text="Temporary until Save camera key. Stored with that shot; framing a reference does not change it."
	interpolation = OptionButton.new()
	for item in ["ease", "linear", "hold"]: interpolation.add_item(item)
	advanced(label(camera_section, "Camera interpolation"))
	camera_section.add_child(interpolation)
	advanced(interpolation)
	camera_key_button = keyboard_shortcuts.decorate(icon_button(camera_section, "Save camera key [K]", "key", key_dialog),"camera","Store this view at the current frame. Replacing an existing key asks first.","Save camera key")
	camera_delete_button = advanced(button(camera_section, "Delete key at this frame", delete_key))
	camera_hint_label = label(camera_section, "Move freely, then save a key.
Draw returns to the animated shot.")
	pose_editor.setup(self, controls)
	audio_section = section(controls, "Audio", "audio")
	audio_choice = OptionButton.new(); audio_section.add_child(audio_choice)
	audio_choice.item_selected.connect(func(index): select_audio(index))
	audio_info = label(audio_section, "No audio clip")
	audio_info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	audio_start = spin(audio_section, "Start at frame", 0, video.duration_frames - 1, 0)
	audio_trim = advanced_spin(audio_section, "Source trim in (milliseconds)", 0, 60000, 0)
	audio_trim.step = 0.001
	audio_gain = advanced_spin(audio_section, "Clip gain (dB)", -60, 12, 0)
	audio_gain.step = 0.1
	button(audio_section, "Apply audio settings", apply_audio_settings)
	audio_mute = CheckButton.new()
	audio_mute.text = "Mute audio"
	audio_mute.toggled.connect(func(value):
		if not audio_clip.is_empty():
			var before := audio_document().duplicate(true)
			audio_clip.muted = value
			commit_audio(before))
	audio_section.add_child(audio_mute)
	audio_solo=CheckButton.new();audio_solo.text="Solo audio clip"
	audio_solo.tooltip_text="Hear only soloed sound clips in this scene, including export. Mute still silences a soloed clip."
	audio_solo.toggled.connect(func(value):
		if exporting or audio_clip.is_empty():return
		var before:=audio_document().duplicate(true)
		if value:audio_clip["solo"]=true
		else:audio_clip.erase("solo")
		commit_audio(before))
	audio_section.add_child(audio_solo)
	button(audio_section,"Shorten sound…",func():audio_trim_editor.open())
	button(audio_section,"Fade sound…",func():audio_fade_editor.open())
	button(audio_section, "Remove audio clip", remove_audio)
	var encoder_section := section(controls, "Movie encoder", "export")
	advanced(encoder_section.get_parent())
	label(encoder_section,"Output size")
	output_size=OptionButton.new();encoder_section.add_child(output_size)
	for id in OutputSize.PROFILES:
		var dimensions: Vector2i=OutputSize.PROFILES[id]
		output_size.add_item("%d x %d" % [dimensions.x,dimensions.y]+(" (default)" if id=="1080p" else ""));output_size.set_item_metadata(output_size.item_count-1,id)
	output_size.tooltip_text="Delivery dimensions for new movies and PNG sequences. Artwork keeps its native canvas size. Saved with this scene. Captured at render start; Retry MP4 keeps its saved frame size."
	output_size.item_selected.connect(change_output_size)
	label(encoder_section,"Movie quality")
	encoder_quality=OptionButton.new();encoder_section.add_child(encoder_quality)
	for id in ["standard","small","high"]:
		encoder_quality.add_item(Encoder.PROFILES[id].label);encoder_quality.set_item_metadata(encoder_quality.item_count-1,id)
	encoder_quality.tooltip_text="Standard keeps the existing quality. Smaller file sacrifices detail; High quality keeps more detail with a larger file and slower encoding. Applies to this export or Retry MP4."
	button(encoder_section, "Export to another folder…", export_elsewhere).tooltip_text = "Choose a destination for this export. The main Export movie action uses the saved HAS project folder."
	png_drawing_only=CheckButton.new();png_drawing_only.text="PNG: drawings only (transparent)";encoder_section.add_child(png_drawing_only)
	png_drawing_only.tooltip_text="Off: complete scene and drawings. On: visible drawing layers on transparent pixels. Audio is a separate synchronized WAV."
	button(encoder_section,"Export PNG sequence…",export_images_dialog).tooltip_text="Export full-resolution PNG frames and any sound as WAV. Does not require FFmpeg."
	button(encoder_section,"PNG to another folder…",export_images_elsewhere)
	encoder_path = LineEdit.new()
	encoder_path.text = default_ffmpeg()
	encoder_path.placeholder_text = "Full path to ffmpeg.exe"
	encoder_section.add_child(encoder_path)
	button(encoder_section, "Locate FFmpeg", func(): choose_file("Locate ffmpeg.exe", ["*.exe"], func(path): encoder_path.text = path))
	var recovery_section := section(controls, "Recovery", "save")
	advanced(recovery_section.get_parent())
	autosave_enabled = CheckButton.new()
	autosave_enabled.text = "Automatic recovery copies"
	autosave_enabled.button_pressed = true
	recovery_section.add_child(autosave_enabled)
	autosave_enabled.toggled.connect(func(_value):refresh_recovery_schedule(false))
	label(recovery_section,"Save recovery copies")
	autosave_schedule=OptionButton.new();autosave_schedule.add_item("By time");autosave_schedule.add_item("After edits");recovery_section.add_child(autosave_schedule)
	autosave_time_controls=VBoxContainer.new();recovery_section.add_child(autosave_time_controls)
	autosave_interval=spin(autosave_time_controls,"Every (minutes)",0.5,10,1);autosave_interval.step=0.5;autosave_interval.value=1
	autosave_action_controls=VBoxContainer.new();recovery_section.add_child(autosave_action_controls)
	autosave_action_limit=spin(autosave_action_controls,"Completed edits",1,1000,25)
	autosave_action_limit.tooltip_text="Completed edits, including Undo/Redo. A long stroke counts once; creating a cel also counts. Navigation and playback do not count."
	autosave_schedule.item_selected.connect(func(_index):refresh_recovery_schedule())
	autosave_interval.value_changed.connect(func(_value):refresh_recovery_schedule())
	autosave_action_limit.value_changed.connect(func(_value):refresh_recovery_schedule(false))
	button(recovery_section, "Checkpoint now", func(): autosave_tick(true))
	button(recovery_section,"Recovery History…",func():show_recovery(true))
	button(recovery_section, "Open recovery folder", func():
		if DirAccess.dir_exists_absolute(recovery_root): OS.shell_open(recovery_root)
		else: message("No recovery folder yet. Create a checkpoint first."))
	button(recovery_section, "Open saved backup…", func(): choose_directory("Choose project whose previous save you want to restore", func(folder): request_recovery({"folder": folder, "manifest": "project.backup.json", "recovery": false})))
	var transport := HFlowContainer.new()
	column.add_child(transport)
	# Neon Pro step 6: the four Codex transport buttons sit in a 190 px block above the lane labels.
	var transport_buttons: Control = transport_block(transport) if StudioTheme.is_neon() else transport
	button(transport_buttons, "|◀", func(): stop(); set_frame(0)).tooltip_text = "First frame • Home"
	button(transport_buttons, "◀", func(): step(-1)).tooltip_text = "Previous frame • Left arrow"
	play_button = icon_button(transport_buttons, "Play", "play", toggle_play, "Play / pause • Space")
	button(transport_buttons, "▶|", func(): step(1)).tooltip_text = "Next frame • Right arrow"
	frame_box = spin(transport, "Frame", 0, video.duration_frames, 0)
	frame_box.value_changed.connect(func(value): stop(); set_frame(int(value)))
	transport_info = label(transport, "")
	transport_info.text_overrun_behavior=TextServer.OVERRUN_TRIM_ELLIPSIS
	transport_info.size_flags_horizontal=Control.SIZE_EXPAND_FILL
	if StudioTheme.is_neon(): style_transport(transport, transport_buttons)
	timeline = TimelineView.new()
	timeline.custom_minimum_size.y = 160
	timeline.size_flags_horizontal=Control.SIZE_EXPAND_FILL
	timeline.hide_header=true
	timeline.seek.connect(func(value): stop(); set_frame(value))
	timeline.import_requested.connect(func(value,actor):import_actions.pick(value,actor))
	timeline.audio_chosen.connect(select_audio)
	timeline.audio_moved.connect(retime_audio)
	timeline.audio_end_trimmed.connect(func(id,last,context):audio_trim_editor.apply_drag(id,last,context))
	timeline.object_selected.connect(func(id):stop();finish_stroke();world_selection.select_entity(id))
	timeline.channel_selected.connect(select_timeline_channel)
	timeline.object_moved.connect(retime_object)
	timeline.piece_moved.connect(clip_editor.move_piece)
	timeline.clip_action.connect(clip_editor.request)
	timeline_ruler=TimelineView.new();timeline_ruler.header_only=true
	timeline_ruler.seek.connect(func(value):stop();set_frame(value))
	timeline_ruler.import_requested.connect(func(value,actor):import_actions.pick(value,actor))
	var ruler_holder:=Control.new();ruler_holder.custom_minimum_size.y=90
	column.add_child(ruler_holder);ruler_holder.add_child(timeline_ruler);timeline_ruler.position.y=38
	if StudioTheme.is_neon(): timeline_ruler.rate_fps=float(video.fps_num)/video.fps_den
	timeline_navigation=preload("res://src/timeline_navigation.gd").new();timeline_navigation.app=self;add_child(timeline_navigation);timeline_navigation.setup(ruler_holder,timeline,timeline_ruler)
	camera_key_editor=preload("res://src/camera_timeline_editor.gd").new();add_child(camera_key_editor);camera_key_editor.setup(self,timeline_ruler)
	timeline.resized.connect(func():timeline_ruler.size=Vector2(timeline.size.x,52);timeline_ruler.queue_redraw())
	var timeline_scroll:=ScrollContainer.new()
	timeline_scroll.name="TimelineScroll";timeline_scroll.custom_minimum_size.y=144
	timeline_scroll.horizontal_scroll_mode=ScrollContainer.SCROLL_MODE_DISABLED
	timeline_scroll.vertical_scroll_mode=ScrollContainer.SCROLL_MODE_RESERVE
	# Neon: the lanes take whatever height the Timeline dock has left (drag the divider for more).
	if StudioTheme.is_neon(): timeline_scroll.size_flags_vertical=Control.SIZE_EXPAND_FILL
	column.add_child(timeline_scroll);timeline_scroll.add_child(timeline)
	debug_label = label(column, "")
	advanced(debug_label)
	var footer := HBoxContainer.new()
	column.add_child(footer)
	app_footer = footer
	if StudioTheme.is_neon():
		# Neon: the Advanced debug line shares the footer row with the recovery status (one row instead
		# of two), so the Timeline dock keeps its lanes at 1440x900 without an outer scrollbar.
		move_to(debug_label, footer)
		debug_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		debug_label.size_flags_stretch_ratio = 4.0
		debug_label.clip_text = true
		debug_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	footer.draw.connect(draw_app_footer)
	debug_label.visibility_changed.connect(footer.queue_redraw)
	if toast:
		# Neon Pro step 4: status lives in the stage toast (plain line in Advanced). This footer keeps
		# the export/recovery buttons; recovery_status is Advanced-only (the header save line's
		# tooltip carries it in Simple), so in Simple the row only takes space while a button shows.
		var footer_spacer := Control.new()
		footer_spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		footer_spacer.mouse_filter = Control.MOUSE_FILTER_IGNORE
		footer.add_child(footer_spacer)
	status = label(toast.get_child(0) if toast else footer, "")
	status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	if toast:status.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	status.custom_minimum_size.y = 36
	status.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	movie_folder_button=button(footer,"Show movie folder",show_movie_folder)
	movie_folder_button.hide()
	saved_frames_button=button(footer,"Show saved frames",func():open_result_folder(interrupted_frames_folder))
	saved_frames_button.hide()
	retry_encode_button=button(footer,"Retry MP4",retry_saved_movie)
	retry_encode_button.tooltip_text="Encode the frames and sound saved by the last render."
	retry_encode_button.hide()
	recovery_status = label(footer, "Recovery on • every 1 min")
	recovery_status.tooltip_text = "Separate from manual Save. Waits until gestures, playback, export and dialogs finish."
	if toast:
		advanced(recovery_status)
		recovery_status.theme_type_variation = "CaptionLabel"
	cancel_button = button(footer, "Cancel export", func(): cancel_export = true; if encoder: encoder.cancel())
	cancel_button.visible = false
	style_app_footer()
	set_advanced(false)
	workspace_layout=preload("res://src/workspace_layout.gd").new();add_child(workspace_layout)
	workspace_layout.setup(self,column,middle,hierarchy,scroll,transport,ruler_holder,timeline_scroll)
	var fit_panels := func():
		var usable_height:=minf(get_viewport_rect().size.y,float(get_window().size.y)/get_window().content_scale_factor)
		var compact := usable_height < 800
		world_selection.tree.custom_minimum_size.y = 80 if compact else 150
		# Neon: 56 px (two 28 px lanes under the ruler's Camera lane) = the mock's 84 px lane area.
		# Advanced: 30 px (one layer row), so its taller chrome (header, two-line transport) fits the docked 166 px timeline
		# without the dock's own TimelineContentScroll engaging (one scrollbar, the lanes' own).
		timeline_scroll.custom_minimum_size.y = (30 if advanced_mode else 56) if StudioTheme.is_neon() else 84 if compact else 144
		canvas.custom_minimum_size.y = 90 if compact else 180
		if not toast:scene_name.visible=not compact
	resized.connect(fit_panels)
	get_window().size_changed.connect(fit_panels)
	fit_panels.call()

func style_app_footer() -> void:
	# Neon Pro step 9: Advanced debug line in mono 11 #8C93A3 (6.6:1 on #0C0D11) on a #0C0D11 band
	# with a 1 px #22252E top hairline; the band also covers the 8 px column gap below it and the
	# 10 px right margin, so it meets the footer and the window edge. Classic keeps the plain label.
	if debug_label == null: return
	if StudioTheme.is_neon():
		var band := StudioTheme.flat(StudioTheme.BAR, StudioTheme.LINE, 0, 0, Vector4(12, 5, 12, 4))
		band.border_width_top = 1
		band.expand_margin_bottom = 8
		band.expand_margin_right = 10
		if debug_label.get_parent() == app_footer: band = StudioTheme.flat(Color.TRANSPARENT, Color.TRANSPARENT, 0, 0, Vector4(12, 5, 12, 4))
		debug_label.add_theme_stylebox_override("normal", band)
		debug_label.add_theme_font_override("font", StudioTheme.mono(400))
		debug_label.add_theme_font_size_override("font_size", 11)
		debug_label.add_theme_color_override("font_color", StudioTheme.TEXT3)
	else:
		debug_label.remove_theme_stylebox_override("normal")
		debug_label.remove_theme_font_override("font")
		debug_label.remove_theme_font_size_override("font_size")
		debug_label.remove_theme_color_override("font_color")
	if recovery_status and toast: recovery_status.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	if recovery_status:
		# Same 12 px inset from the window edge as the debug band on the left.
		if StudioTheme.is_neon(): recovery_status.add_theme_stylebox_override("normal", StudioTheme.flat(Color.TRANSPARENT, Color.TRANSPARENT, 0, 0, Vector4(0, 0, 12, 0)))
		else: recovery_status.remove_theme_stylebox_override("normal")
	if app_footer: app_footer.queue_redraw()

func draw_app_footer() -> void:
	# Neon footer (debug line + recovery status in Advanced, export buttons): a #0C0D11 band to the
	# window edges with a 1 px #22252E hairline on top. Nothing while the row is empty.
	if not StudioTheme.is_neon() or app_footer == null or app_footer.size.y <= 0.0: return
	app_footer.draw_rect(Rect2(Vector2.ZERO, app_footer.size), StudioTheme.BAR)
	app_footer.draw_rect(Rect2(0, 0, app_footer.size.x, 1), StudioTheme.LINE)

func default_ffmpeg() -> String:
	var setting := OS.get_environment("HYBRID_FFMPEG")
	if not setting.is_empty(): return setting
	var common := "C:/Program Files/ffmpeg/bin/ffmpeg.exe"
	return common if FileAccess.file_exists(common) else "ffmpeg"

func message(text: String) -> void:
	status.text = text
	status_serial += 1
	status_faded = false
	refresh_status_style()
	schedule_status_fade(status_serial)
	if home and home.visible and home.notice:home.feedback(text)

func schedule_status_fade(serial: int) -> void:
	# Redesign: the Simple toast fades after 6 s. Only the look changes; status.text is kept,
	# because Codex's code and tests read it back as the latest result.
	if advanced_mode or not is_inside_tree(): return
	if toast:
		# Neon Pro step 4: a 2 px neon strip under the toast shrinks over the same 6 s.
		if toast_tween: toast_tween.kill()
		toast_tween = create_tween()
		toast_tween.tween_method(set_toast_progress, 1.0, 0.0, 6.0)
	get_tree().create_timer(6.0).timeout.connect(func():
		if serial == status_serial and not advanced_mode and status:
			status_faded = true
			if toast:
				toast.modulate.a = 0.0
				toast.mouse_filter = Control.MOUSE_FILTER_IGNORE
			else: status.self_modulate.a = 0.0)

func refresh_status_style() -> void:
	# Redesign: Simple shows status as a rounded toast (red for problems); Advanced keeps the plain line.
	if status == null: return
	if toast: refresh_toast(); return
	if advanced_mode:
		status.remove_theme_stylebox_override("normal")
		status.self_modulate.a = 1
		return
	var problem := is_problem_message(status.text)
	var toast := StyleBoxFlat.new()
	toast.bg_color = StudioTheme.tone(Color("fdecea") if problem else Color("eaf3fb"))
	toast.border_color = StudioTheme.tone(Color("d9534f") if problem else Color("9cc3e4"))
	toast.set_border_width_all(1)
	toast.set_corner_radius_all(10)
	toast.content_margin_left = 12
	toast.content_margin_right = 12
	toast.content_margin_top = 6
	toast.content_margin_bottom = 6
	status.add_theme_stylebox_override("normal", toast)
	status.self_modulate.a = 0.0 if status.text.is_empty() or status_faded else 1.0

func is_problem_message(text: String) -> bool:
	var lower := text.to_lower()
	return lower.contains("fail") or lower.contains("error") or lower.contains("cannot") or lower.contains("could not") or lower.contains("unsupported")

func refresh_empty_hint() -> void:
	# Redesign: Simple-only next-step hint over the canvas (editor overlay, never in renders). Writes only on change.
	if empty_hint == null: return
	var text := ""
	if not advanced_mode and not playing and not exporting:
		var empty: bool = source.is_empty() and (renderer.world_runtime == null or renderer.world_runtime.instances.is_empty())
		if empty: text = "Start here:  Add a 3D scene or a model,\nmove the camera and save a key, then draw on top."
		elif mode.selected == 0 and active_layer < layers.size() and Drawing.cel_at(layers[active_layer], frame).is_empty(): text = "No drawing at this frame yet.\nPress New drawing, then draw on the picture."
		elif mode.selected == 1 and keys.is_empty(): text = "No camera keys yet.\nMove the view, then press Save key."
	var show_hint := not text.is_empty()
	if show_hint and empty_hint_label.text != text: empty_hint_label.text = text
	if empty_hint.visible != show_hint: empty_hint.visible = show_hint

func changed() -> void:
	stop_local_wind("Document edited")
	if drawing_selection_editor:drawing_selection_editor.cancel()
	recovery_revision += 1
	dirty = true
	overlay_dirty = true
	if sequence_editor and not sequence_editor.graph.is_empty():sequence_editor.sync_current()
	refresh_timeline()

func refresh_timeline() -> void:
	timeline_ruler.keys=keys;timeline_ruler.frame=frame;timeline_ruler.duration=video.duration_frames;timeline_ruler.rate_fps=float(video.fps_num)/video.fps_den;timeline_ruler.queue_redraw()
	timeline.keys = keys
	timeline.layers = layers
	timeline.frame = frame
	timeline.duration = video.duration_frames
	timeline.audio_clip = audio_clip.duplicate()
	if not audio_clip.is_empty(): timeline.audio_clip["fps"] = float(video.fps_num) / video.fps_den
	timeline.audio_clips = audio_clips
	timeline.audio_fps = float(video.fps_num) / video.fps_den
	timeline.audio_rate={"fps_num":int(video.fps_num),"fps_den":int(video.fps_den)}
	timeline.audio_selected = selected_audio
	timeline.clip_waveforms = audio_mix.get("clip_peaks",[])
	timeline.clip_waveform_levels=audio_mix.get("clip_waveform_levels",[])
	timeline.waveform = audio_mix.get("peaks", PackedFloat32Array())
	var active: RefCounted=renderer.active_model()
	timeline.can_paste=not clip_editor.clipboard.is_empty()
	timeline.pose_keys = active.authored_keys() if active else []
	timeline.has_model = active != null
	timeline.presence_start=int(active.data.get("start_frame",0)) if active else 0
	var rows: Array=[]
	if renderer.world_runtime:
		for row in renderer.world_runtime.data.objects:rows.append(renderer.world_runtime.instance(row.id).data)
	if transport_time: timeline.row_keys = timeline_row_keys()
	timeline.set_objects(rows,renderer.world_runtime.get_instance_id() if renderer.world_runtime else 0,renderer.active_instance_id)
	timeline.sync_bone(pose_editor.selected)
	if timeline_navigation:timeline_navigation.sync()
	timeline.queue_redraw()

func select_timeline_channel(id: String, channel: String, at: int) -> void:
	if exporting or not renderer.world_runtime:return
	var rig: RefCounted=renderer.world_runtime.instance(id)
	var root_component: bool=rig!=null and rig.data.get("format")=="studio_model_9" and channel in ["@root/position","@root/rotation_xyzw","@root/scale"]
	if not rig or not root_component and channel not in ["@root","@visibility"] and not rig.bones.has(channel) and not rig.shape_channel_valid(channel):return
	var view: Dictionary=renderer.view_state()
	stop();finish_stroke();pose_editor.finish_drag();world_selection.select_entity(id)
	if channel!="@visibility" and not channel.begins_with("@shape/"):
		pose_editor.search.text="";pose_editor.selected="@root" if root_component else channel;pose_editor.rebuild_tree()
	if root_component:
		if channel=="@root/position":pose_editor.operation.select(1)
		elif channel=="@root/rotation_xyzw":pose_editor.operation.select(0)
	if at>=0:set_frame(at)
	if channel.begins_with("@shape/"):
		pose_editor.open_shapes()
		var parts:=channel.split("/");var editor=pose_editor.animated_shapes
		for i in range(editor.parts.item_count):
			if int(editor.parts.get_item_metadata(i))==int(parts[1]):editor.parts.select(i);editor.parts.item_selected.emit(i)
		editor.search.clear();editor.rebuild()
		for i in range(editor.shapes.item_count):
			if int(editor.shapes.get_item_metadata(i))==int(parts[2]):editor.shapes.select(i);editor.shapes.item_selected.emit(i)
	pose_editor.refresh_values();timeline.selected_channel=channel;timeline.queue_redraw()
	if root_component and channel=="@root/scale":inspector_scroll.ensure_control_visible(pose_editor.scale_field)
	renderer.restore_view(view)

func retime_object(id: String, delta: int, before: Dictionary) -> void:
	if exporting or not renderer.world_runtime:return
	var rig: RefCounted=renderer.world_runtime.instance(id)
	if not rig or JSON.stringify(rig.data)!=JSON.stringify(before):
		message("The object changed while dragging. Try moving its block again.");return
	var view: Dictionary=renderer.view_state()
	stop();pose_editor.finish_drag();finish_stroke()
	var actual:=ObjectTiming.clamp_delta(rig.data,delta,int(video.duration_frames))
	if actual==0:return
	var after:=ObjectTiming.move(rig.data,actual,int(video.duration_frames))
	if Renderer.Model.is_contact(after) or not pose_editor.contacts.affected(rig).is_empty():
		if pose_editor.contacts.live_busy():message("Turn Physics and Hair & clothes off before moving planted animation.");return
		clip_editor.commit(after,"Moved %s by %d frames, with its presence, contacts and motion. Undo restores the timing." % [rig.data.name,actual])
		return
	var error: String=pose_editor.restore_state(after)
	if not error.is_empty():message(error);return
	set_frame(frame)
	renderer.restore_view(view)
	message("Moved %s by %d frames, with its presence and all pose keys. Undo restores the timing." % [rig.data.name,actual])

func refresh_layer() -> void:
	layer_visibility.set_pressed_no_signal(layers[active_layer].visible)
	var cel := Drawing.cel_at(layers[active_layer], frame)
	if not cel.is_empty(): exposure.value = cel.duration

func refresh_layer_choices() -> void:
	layer_choice.clear()
	for layer in layers:layer_choice.add_item(layer.name)
	active_layer=clampi(active_layer,0,layers.size()-1);layer_choice.select(active_layer);refresh_layer()
	if layer_editor:layer_editor.refresh()

func stop_local_wind(reason: String) -> void:
	if is_instance_valid(local_wind_review):local_wind_review.stop_preview(reason)
	if is_instance_valid(physics_editor) and is_instance_valid(physics_editor.helper_editor):physics_editor.helper_editor.stop_pending_preview(reason)

func local_wind_display_active() -> bool:
	return (is_instance_valid(local_wind_review) and local_wind_review.phase in ["warming","running"]) or (is_instance_valid(physics_editor) and is_instance_valid(physics_editor.helper_editor) and is_instance_valid(physics_editor.helper_editor.pending_preview) and physics_editor.helper_editor.pending_preview.display_active())

func local_wind_active() -> bool:
	return (is_instance_valid(local_wind_review) and local_wind_review.phase in ["warming","running"]) or (is_instance_valid(physics_editor) and is_instance_valid(physics_editor.helper_editor) and physics_editor.helper_editor.pending_preview_active())

func set_frame(value: int) -> void:
	if exporting: return
	if value!=frame:stop_local_wind("Frame changed")
	if drawing_selection_editor and value!=frame:drawing_selection_editor.cancel()
	if fill_editor and value!=frame:fill_editor.cancel()
	if physics_editor and physics_editor.recording and physics_editor.recording.active and not physics_editor.recording.advancing:
		physics_editor.recording.finish("seek")
	if value!=frame and physics_editor and not (physics_editor.recording and physics_editor.recording.advancing):
		physics_editor.freeze_all();physics_editor.clear_previews()
	pose_editor.finish_drag()
	finish_stroke()
	frame = clampi(value, 0, video.duration_frames)
	renderer.video_settings=video
	if renderer.world_runtime:renderer.world_runtime.duration=int(video.duration_frames)
	renderer.apply_lighting()
	if lighting_choice:lighting_choice.select(Renderer.Lighting.MODES.find(Renderer.Lighting.mode(video)))
	var frame_signals_blocked:=frame_box.is_blocking_signals()
	frame_box.set_block_signals(true);frame_box.max_value=video.duration_frames;frame_box.set_value_no_signal(frame);frame_box.set_block_signals(frame_signals_blocked)
	refresh_transport_text()
	if project_timing:project_timing.sync()
	if mode.selected != 1: renderer.evaluate(keys, frame)
	pose_editor.apply_frame()
	pose_editor.refresh_values()
	overlay_dirty = true
	refresh_layer()
	refresh_timeline()

func show_project_options() -> void:
	if exporting:return
	stop();pose_editor.finish_drag();finish_stroke()
	if not project_options:
		project_options=AcceptDialog.new();project_options.title="Project options";project_options.exclusive=false;project_options.unresizable=false;add_child(project_options)
		var options_scroll:=ScrollContainer.new();options_scroll.custom_minimum_size=Vector2(520,minf(600,maxf(320,size.y-180)));options_scroll.horizontal_scroll_mode=ScrollContainer.SCROLL_MODE_DISABLED;project_options.add_child(options_scroll)
		var content:=VBoxContainer.new();content.size_flags_horizontal=Control.SIZE_EXPAND_FILL;options_scroll.add_child(content)
		project_canvas.setup(content)
		project_timing.setup(content)
		visibility_fade=spin(content,"Visibility fade (milliseconds)",0,10000,300)
		label(content,"Applies to all visibility changes. 0 makes an instant cut.")
		visibility_fade.value_changed.connect(change_visibility_fade)
		height_choice=CheckBox.new();height_choice.text="Offer character height matching on model import";content.add_child(height_choice)
		height_choice.tooltip_text="Optional review before placement/physics. Off means no extra height analysis or fitting. Session preference; maps stay unchanged."
		height_choice.toggled.connect(func(value):import_actions.offer_height=value)
	visibility_fade.set_value_no_signal(int(video.get("visibility_fade_ms",300)))
	height_choice.set_pressed_no_signal(import_actions.offer_height)
	project_timing.sync();project_options.popup_centered(Vector2i(600,480))

func change_lighting(index: int) -> void:
	if exporting or index<0 or index>=Renderer.Lighting.MODES.size():return
	var kind: String=Renderer.Lighting.MODES[index]
	if Renderer.Lighting.mode(video)==kind:return
	stop();pose_editor.finish_drag();finish_stroke()
	var before:=video.duplicate(true);video["lighting_mode"]=kind
	push_history({"type":"video","before":before,"after":video.duplicate(true)})
	var view: Dictionary=renderer.view_state()
	changed();set_frame(frame);renderer.restore_view(view)
	message("Unshaded: base colors and textures." if kind=="unshaded" else "Lit: uses the lights supplied by your scene." if kind=="lit" else "Studio light: original preview illumination.")

func change_visibility_fade(value: float) -> void:
	if exporting or int(value)==int(video.get("visibility_fade_ms",300)):return
	stop();pose_editor.finish_drag();finish_stroke()
	var before:=video.duplicate(true)
	video["visibility_fade_ms"]=clampi(int(value),0,10000)
	push_history({"type":"video","before":before,"after":video.duplicate(true)})
	var view: Dictionary=renderer.view_state()
	changed();set_frame(frame);renderer.restore_view(view)

func stop() -> void:
	playing = false
	if audio_player: audio_player.stop()
	audio_clock = false

func step(amount: int) -> void:
	if exporting: return
	stop()
	set_frame(clampi(frame + amount, 0, video.duration_frames - 1))

func toggle_play() -> void:
	if exporting: return
	stop_local_wind("Playback")
	physics_editor.freeze_all();physics_editor.clear_previews()
	finish_stroke()
	if playing:
		stop()
	else:
		mode.select(0)
		change_mode(0)
		if frame >= video.duration_frames: set_frame(0)
		playing = true
		play_start = frame
		play_origin = Time.get_ticks_usec()
		if not audio_mix.is_empty():
			audio_player.stream = audio_mix.stream
			audio_latency = AudioServer.get_output_latency()
			last_audio_time = Timeline.seconds(frame, video)
			audio_player.play(last_audio_time)
			audio_clock = AudioServer.get_driver_name() != "Dummy"
			if not audio_clock: message("Audio device unavailable (Dummy driver). Preview uses silent wall-clock fallback; export is unaffected.")

func change_mode(index: int) -> void:
	if exporting: return
	if drawing_selection_editor:drawing_selection_editor.cancel()
	if fill_editor and index!=0:fill_editor.cancel()
	if index==0 and physics_editor.recording and physics_editor.recording.active:physics_editor.recording.finish("switch to drawing")
	pose_editor.finish_drag()
	refresh_workspace()
	finish_stroke()
	stop()
	release_mouse()
	renderer.evaluate(keys, frame)
	fov.set_value_no_signal(renderer.camera.fov)
	pose_editor.apply_frame()
	pose_editor.refresh_values()
	if index == 2 and not renderer.world_runtime and renderer.model and world_selection.selected != "model": world_selection.select_entity("model",false)
	# Redesign: plain wording in Simple; Advanced keeps the original messages.
	# Neon Simple: a one-line toast whose bold first sentence reads on its own (the classic wording
	# stays for the classic styles).
	if index == 1 and not advanced_mode and StudioTheme.is_neon(): message("Move the view, then save a key. Press Save camera key [%s] to keep it." % keyboard_shortcuts.label_for("camera"))
	elif index == 1: message("Camera: move around freely, then press Save camera key [%s] to keep this view in the movie." % keyboard_shortcuts.label_for("camera") if not advanced_mode else "Editor camera is temporary. Insert a key explicitly; switching to Draw restores the shot.")
	elif index == 2 and not advanced_mode and not pose_editor.active_rig(): message("Pose: no model yet. Press Add, then Poseable model…")
	elif index == 2: message(POSE_HINT if not advanced_mode else "Pose model: click a joint, then drag colored handles. Completed edits auto-key by default. Camera keys and drawing remain separate.")
	else: message("Draw: this drawing stays on screen until the next one. Use New drawing to change it from this frame on." if not advanced_mode else "Drawing edits only the active cel. Held frames share this drawing; duplicate to make a variation.")

func refresh_camera_controls() -> void:
	if fov:fov.set_value_no_signal(renderer.camera.fov);fov.editable=mode.selected==1 and not exporting
	if camera_near:camera_near.set_value_no_signal(renderer.camera.near);camera_near.editable=mode.selected==1 and not exporting
	if camera_far:camera_far.set_value_no_signal(renderer.camera.far);camera_far.editable=mode.selected==1 and not exporting

func middle_pose_target() -> String:
	if mode.selected not in [1,2] or world_selection.selected.is_empty() or exporting or playing or pose_editor.dragging or physics_editor.grabbing():return ""
	var actor: RefCounted=world_selection.selected_rig()
	return actor.data.get("id","model") if actor and actor.data.get("kind","model")=="model" else ""

func cycle_pose_operation() -> void:
	if middle_pose_target().is_empty():return
	if mode.selected!=2:
		var view: Dictionary=renderer.view_state();mode.select(2);change_mode(2);renderer.restore_view(view)
	pose_editor.operation.select(1-pose_editor.operation.selected)
	pose_editor.refresh_values();pose_editor.update_gizmo()
	message(("Move" if pose_editor.operation.selected==1 else "Rotate")+" selected model or bone. Middle-click switches the tool; middle-drag still navigates.")

func change_camera_range(value: float,nearest: bool) -> void:
	if exporting or mode.selected!=1:refresh_camera_controls();return
	var candidate:={"near":value if nearest else renderer.camera.near,"far":renderer.camera.far if nearest else value}
	var error:=Timeline.range_error([candidate])
	if not error.is_empty():refresh_camera_controls();message(error);return
	renderer.camera.near=candidate.near;renderer.camera.far=candidate.far
	refresh_camera_controls();camera_preview_hint()

func camera_preview_hint() -> void:
	message("Camera preview changed. Use Save camera key [%s] to keep this view at frame %d." % [keyboard_shortcuts.label_for("camera"),frame])

func trim_idle_rasters() -> void:
	if raster_budget.cache==null or Time.get_ticks_msec()<raster_budget_due:return
	raster_budget_due=Time.get_ticks_msec()+1000
	if playing or exporting or drawing or navigating or pose_editor.dragging or physics_editor.recording.active or physics_editor.is_running() or has_dialog(self) or home.visible:return
	if fill_editor.busy() or drawing_selection_editor.transforms.busy():return
	var protected: Array=[]
	for layer in layers:
		var cel:=Drawing.cel_at(layer,frame)
		if cel.get("raster_owner")!=null:protected.append(cel.raster_owner)
	raster_budget.step(protected,true)

func _process(delta: float) -> void:
	trim_idle_rasters()
	poll_recovery_preview()
	if recovery_checkpoint_requested and not recovery_writer.busy() and not recovery_preview.busy():autosave_tick(true)
	refresh_play_button()
	sync_timeline_focus()
	refresh_empty_hint()
	refresh_title()
	refresh_tool_strip() # tool can change without a signal (shortcuts, color sampler)
	refresh_physics_bar() # a simulation can start without a workspace refresh (imports, lessons)
	refresh_badges()
	sync_fit_view()
	refresh_draw_inspector()
	refresh_camera_inspector()
	pose_editor.refresh_neon_inspector()
	if playing:
		var seconds := preview_seconds()
		preview_sample_seconds=seconds
		var next := floori(seconds * video.fps_num / video.fps_den)
		if next >= video.duration_frames:
			stop()
			set_frame(video.duration_frames - 1)
		elif next != frame: set_frame(next)
	if navigating and not exporting and not orbit_control.active:
		var motion := Vector3(float(Input.is_physical_key_pressed(KEY_D)) - float(Input.is_physical_key_pressed(KEY_A)), float(Input.is_physical_key_pressed(KEY_E)) - float(Input.is_physical_key_pressed(KEY_Q)), float(Input.is_physical_key_pressed(KEY_S)) - float(Input.is_physical_key_pressed(KEY_W)))
		var fly_speed := .75 if Input.is_key_pressed(KEY_CTRL) else 8.0 if Input.is_key_pressed(KEY_SHIFT) else 3.0
		renderer.camera.position += renderer.camera.basis * motion.limit_length() * delta * fly_speed
	pose_editor.update_gizmo()
	if overlay_dirty:
		var start := Time.get_ticks_usec()
		var sampled: Dictionary=drawing_overlay_cache.sample(layers,frame,video.width,video.height,recovery_revision)
		if sampled.has("error"):
			raster_preview_error=sampled.error;stop();message(raster_preview_error+" Last valid preview retained.")
		else:
			raster_preview_error=""
			var overlay: Image=sampled.image
			if canvas.overlay == null or Vector2i(canvas.overlay.get_size())!=overlay.get_size(): canvas.overlay = ImageTexture.create_from_image(overlay)
			elif sampled.changed: canvas.overlay.update(overlay)
		elapsed_overlay_ms = (Time.get_ticks_usec() - start) / 1000.0
		canvas.queue_redraw()
		overlay_dirty = false
	var cel_count := 0
	for layer in layers: cel_count += layer.cels.size()
	debug_label.text = "Frame %03d / [0,%d) | %.3f s | %d/%d fps | GLB %s | %d cels | overlay %.2f ms | %s | %s" % [frame, video.duration_frames, Timeline.seconds(frame, video), video.fps_num, video.fps_den, source.get_file().left(12), cel_count, elapsed_overlay_ms, "audio clock %.3fs" % last_audio_time if audio_clock else ("silent/device fallback" if not audio_clip.is_empty() and playing else "audio ready" if not audio_clip.is_empty() else "no audio"), "unsaved" if dirty else "saved"]

func canvas_input(event: InputEvent, point: Vector2) -> void:
	if home and home.visible:return
	if exporting or playing: return
	if preload("res://src/camera_lens_gesture.gd").handle(self,event):return
	# Only new editing presses are bounded. Captured camera motion, active drags,
	# releases and cancellation must continue after leaving the displayed scene.
	if mode.selected in [1,2] and event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT and event.pressed and not event.ctrl_pressed and not canvas.scene_contains(point):return
	if not raster_preview_error.is_empty():message(raster_preview_error+" Reopen a valid drawing before editing.");return
	if mode.selected in [1,2] and navigation_scheme=="orbit" and event is InputEventMouseButton and event.pressed and event.ctrl_pressed and event.button_index in [MOUSE_BUTTON_WHEEL_UP,MOUSE_BUTTON_WHEEL_DOWN]:
		var active: bool=orbit_control.active;var action: String=orbit_control.action
		var focal_point: Vector3=orbit_control.pivot if active else orbit_pivot()
		if orbit_control.begin(renderer.camera,focal_point,"dolly"):
			orbit_control.motion(renderer.camera,Vector2(0,-12 if event.button_index==MOUSE_BUTTON_WHEEL_UP else 12))
			if active:orbit_control.action=action
			else:orbit_control.end()
		return
	if mode.selected==0 and tool.selected==3:
		if event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT and event.pressed:color_sampler.start(point)
		return
	if mode.selected==0 and tool.selected==4:
		drawing_selection_editor.pointer(event,point);return
	if drawing_selection_editor and not drawing_selection_editor.context.is_empty():drawing_selection_editor.cancel()
	if physics_editor.pointer(event,point):return
	if mode.selected in [1,2] and event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT and event.ctrl_pressed:
		world_selection.input(event,point); return
	if mode.selected == 2:
		if event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT and event.pressed:
			var joint_hit := false
			for joint in pose_editor.joints:
				if point.distance_to(joint.point) < 10.0*video.width/maxf(1,canvas.image_rect().size.x): joint_hit=true; break
			pose_editor.input(event,point)
			if pose_editor.dragging or joint_hit: return
		elif pose_editor.dragging: pose_editor.input(event,point); return
		world_selection.input(event,point)
		return
	if mode.selected == 1:
		world_selection.input(event,point)
		return
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			if not Rect2(0, 0, video.width, video.height).has_point(point) or frame >= video.duration_frames: return
			if not layers[active_layer].visible or float(layers[active_layer].get("opacity",1.0))<=0:
				message("Show the active layer and raise its opacity before drawing.")
				return
			if tool.selected==2:finish_stroke();fill_editor.start(point);return
			if brush_opacity.value<=0 or tool.selected==0 and color.color.a<=0:return
			var cel := Drawing.cel_at(layers[active_layer], frame)
			if cel.is_empty() and not brush_pressure.button_pressed:
				create_cel(false)
				cel = Drawing.cel_at(layers[active_layer], frame)
			if cel.is_empty() and not brush_pressure.button_pressed:return
			stroke_image = null
			drawing = true
			before_tiles = {}
			active_brush=preload("res://src/brush_stroke.gd").new()
			active_brush.radius=float(radius.value);active_brush.ink=color.color
			active_brush.erase=tool.selected==1;active_brush.opacity=float(brush_opacity.value)/100.0
			active_brush.pressure_size=brush_pressure.button_pressed
			if active_brush.pressure_size:
				stroke_accumulated_input=Input.use_accumulated_input
				Input.use_accumulated_input=false
			active_brush.before=before_tiles
			stroke_stabilizer=preload("res://src/stroke_stabilizer.gd").new();stroke_stabilizer.distance=brush_smoothing.value;stroke_stabilizer.reset(point)
			previous_point = point
			previous_pressure=-1
			if not active_brush.pressure_size:paint_segment(point)
		else: finish_stroke()
	if event is InputEventMouseMotion and drawing:paint_segment(point,event.pressure if active_brush.pressure_size else 1.0)

func paint_segment(point: Vector2,pressure: float=1.0) -> void:
	if not drawing or active_brush==null or not point.is_finite() or not is_finite(pressure):return
	point = point.clamp(Vector2.ZERO, Vector2(video.width - 1, video.height - 1))
	var from:=previous_point
	var r0: float=active_brush.radius;var r1:=r0
	if active_brush.pressure_size:
		pressure=clampf(pressure,0,1)
		if pressure==0:
			if previous_pressure>0:flush_stabilizer()
			previous_pressure=0;previous_point=point
			if stroke_stabilizer:stroke_stabilizer.reset(point)
			return
		r1=maxf(.5,r1*pressure)
		if previous_pressure>0:r0=maxf(.5,r0*previous_pressure)
		else:
			r0=r1
			if previous_pressure==0 or stroke_stabilizer and stroke_stabilizer.distance>0:
				from=point
				if stroke_stabilizer:stroke_stabilizer.reset(point)
		previous_pressure=pressure
	if stroke_stabilizer:point=stroke_stabilizer.sample(point)
	if stroke_image==null:
		# A tablet press alone is not paint. Allocate a cel only at first contact.
		var cel:=Drawing.cel_at(layers[active_layer],frame)
		if cel.is_empty():
			create_cel(false,false);cel=Drawing.cel_at(layers[active_layer],frame)
		if cel.is_empty():finish_stroke();return
		var editable:=Drawing.edit_image(cel)
		if editable.has("error"):message(editable.error);finish_stroke();return
		stroke_image=editable.image
	var painted: bool=active_brush.paint(stroke_image,from,point,r0,r1)
	previous_point = point
	if painted:changed()

func flush_stabilizer() -> void:
	if not drawing or not active_brush or not stroke_stabilizer or stroke_stabilizer.distance<=0 or stroke_image==null:return
	if active_brush.pressure_size and previous_pressure<=0:return
	var end: Vector2=stroke_stabilizer.raw
	if end==previous_point:return
	var size: float=active_brush.radius*maxf(0,previous_pressure) if active_brush.pressure_size else active_brush.radius
	if active_brush.pressure_size:size=maxf(.5,size)
	var painted: bool=active_brush.paint(stroke_image,previous_point,end,size,size)
	previous_point=end;stroke_stabilizer.reset(end)
	if painted:changed()

func finish_stroke() -> void:
	if not drawing: return
	flush_stabilizer()
	drawing = false
	if active_brush and active_brush.pressure_size:Input.use_accumulated_input=stroke_accumulated_input
	var after := {}
	var cost := 0
	for pos in before_tiles:
		after[pos] = stroke_image.get_region(Rect2i(pos, before_tiles[pos].get_size()))
		cost += before_tiles[pos].get_data_size() * 2
	if not before_tiles.is_empty():push_history({"type": "pixels", "image": stroke_image, "before": before_tiles, "after": after, "bytes": cost})
	elif active_brush and active_brush.pressure_size and previous_pressure<=0:message("No pen pressure received. Turn off Tablet pressure size for mouse drawing.")
	stroke_image = null
	active_brush = null
	stroke_stabilizer = null
	before_tiles = {}
	previous_pressure=-1

func push_history(command: Dictionary) -> void:
	PixelHistory.promote(command,layers,sequence_editor.active_owner if sequence_editor else "")
	command["sequence_stamp"]=Time.get_ticks_usec()
	if command.type in ["model","world_object","world_objects","world"]:
		# Charge serialized snapshots conservatively; native metadata is copied too.
		command["bytes"] = 2 * (JSON.stringify(command.before).to_utf8_buffer().size() + JSON.stringify(command.after).to_utf8_buffer().size())
	if command.type == "cels":
		# Conservatively charge referenced rasters, including deleted cels retained by undo.
		command["bytes"] = (command.before.size() + command.after.size()) * video.width * video.height * 4
	history.append(command)
	note_recovery_action(command)
	redo_history.clear()
	history_bytes += command.get("bytes", 0)
	while (history_bytes > 64 * 1024 * 1024 or history.size() > 128) and history.size() > 1:
		history_bytes -= history.pop_front().get("bytes", 0)
	if sequence_editor:sequence_editor.trim_history()

func apply_command(command: Dictionary, side: String) -> bool:
	if command.type=="canvas_size":
		var why: String=project_canvas.restore(command[side])
		if not why.is_empty():message(why);return false
		return true
	if command.type=="output_size":
		var value=command[side]
		if value!=null and not OutputSize.error(value).is_empty():message("Invalid output size history.");return false
		if value==null:video.erase("output_size")
		else:video["output_size"]=value
		sync_output_size();changed();return true
	if command.type=="reference_sheet":
		var why: String=reference_sheet.restore_state(command[side])
		if not why.is_empty():message(why);return false
		changed();return true
	if command.type=="sequence_graph":
		var why: String=sequence_editor.restore(command[side])
		if not why.is_empty():message(why);return false
		changed();return true
	if command.type=="palette":
		palette=command[side].duplicate(true);palette_editor.refresh(true);changed();return true
	# Drawing history refreshes the independent overlay, without resetting live 3D.
	var drawing_command: bool=command.type in ["pixels","cels","cel_patch","cel_timing","cel_exposure","layer_properties","layers"]
	if command.type in ["cels","layer_properties"]:
		var live_layer: Dictionary=cel_timing.layer_by_id(str(command.layer.get("id","")))
		if live_layer.is_empty():message("Drawing history layer is missing.");return false
		command.layer=live_layer
	if not drawing_command:physics_editor.clear();physics_editor.clear_previews()
	var view: Dictionary=renderer.view_state()
	if command.type == "pixels":
		var applied:=PixelHistory.apply(command,side,layers,sequence_editor.active_owner if sequence_editor else "")
		if applied.has("error"):message(applied.error);return false
	elif command.type in ["cel_timing","cel_exposure"]:
		var error: String=cel_timing.apply_command(command,side)
		if not error.is_empty():message(error);return false
	elif command.type=="cel_patch":
		var error: String=cel_clipboard.apply_patch(command,side)
		if not error.is_empty():message(error);return false
	elif command.type == "cels": command.layer.cels = command[side].duplicate(true)
	elif command.type=="layer_properties":
		command.layer.name=command[side].name;command.layer.visible=command[side].visible
		if command[side].has("opacity"):command.layer.opacity=command[side].opacity
		else:command.layer.erase("opacity")
		refresh_layer_choices()
	elif command.type=="layers":
		layers=command[side].duplicate()
		for i in range(layers.size()):
			if layers[i].id==command[side+"_selected"]:active_layer=i
		refresh_layer_choices()
	elif command.type == "keys": keys = command[side].duplicate(true)
	elif command.type=="video":
		var upcoming: Dictionary=command[side]
		var timing_prepared: Dictionary={}
		if video.fps_num!=upcoming.fps_num or video.fps_den!=upcoming.fps_den or video.duration_frames!=upcoming.duration_frames:
			timing_prepared=sequence_editor.prepare_timing(upcoming)
			if timing_prepared.has("error"):message(timing_prepared.error);return false
			audio_mix=timing_prepared.mix
		video=command[side].duplicate(true);renderer.video_settings=video
		sync_output_size()
		if not timing_prepared.is_empty():sequence_editor.install_timing(timing_prepared)
		if visibility_fade:visibility_fade.set_value_no_signal(int(video.get("visibility_fade_ms",300)))
		refresh_audio_controls()
	elif command.type == "model":
		if not pose_editor.restore_state(command[side],false).is_empty():return false
	elif command.type == "world_object":
		if not renderer.world_runtime or command[side].get("id")!=command.object_id:return false
		if not pose_editor.restore_state(command[side],false).is_empty():return false
	elif command.type=="world_objects":
		if not renderer.world_runtime or not renderer.world_runtime.restore_instances(command[side]).is_empty():return false
	elif command.type=="world":
		if not restore_world(command[side]).is_empty():return false
	elif command.type == "audio":
		audio_clip = command[side].duplicate(true)
		var selected: String=command.get("selected_"+side,"")
		for index in range(audio_clips.size()):
			if audio_clips[index].id==selected:selected_audio=index;break
		rebuild_audio()
	changed()
	if drawing_command:refresh_layer();return true
	set_frame(frame)
	if command.type=="video":renderer.restore_view(view)
	return true

func undo() -> void:
	if exporting: return
	if timeline and timeline.cel_gesture_active():timeline.cancel_cel();return
	if drawing_selection_editor and drawing_selection_editor.before_history():return
	if physics_editor.recording and physics_editor.recording.active:physics_editor.recording.cancel();return
	pose_editor.finish_drag()
	finish_stroke()
	if history.is_empty(): return
	var command: Dictionary = history[-1]
	if not apply_command(command,"before"):return
	history.pop_back();history_bytes -= command.get("bytes", 0)
	redo_history.append(command)
	sequence_editor.trim_history()
	note_recovery_action(command)

func redo() -> void:
	if exporting:return
	if timeline and timeline.cel_gesture_active():timeline.cancel_cel();return
	if redo_history.is_empty():return
	if drawing_selection_editor and drawing_selection_editor.before_history():return
	pose_editor.finish_drag()
	finish_stroke()
	if redo_history.is_empty():return
	var command: Dictionary = redo_history[-1]
	if not apply_command(command,"after"):return
	redo_history.pop_back()
	history.append(command)
	history_bytes += command.get("bytes", 0)
	sequence_editor.trim_history()
	note_recovery_action(command)

func own_created_cel(cel: Dictionary) -> String:
	var cache=raster_budget.cache
	if cache==null:cache=preload("res://src/cel_raster_snapshot_cache.gd").new()
	var why:=Drawing.adopt_owner(cel,cache)
	if why.is_empty() and raster_budget.cache==null:
		raster_budget.install(cache);raster_budget_due=Time.get_ticks_msec()+1000
	return why

func create_cel(duplicate: bool,finish_current: bool=true) -> void:
	if exporting or frame >= video.duration_frames: return
	if finish_current:finish_stroke()
	var count := 0
	for layer in layers: count += layer.cels.size()
	if sequence_editor:count=sequence_editor.used("cels")
	if count >= DrawingLimits.MAX_CELS: message("This project already has %d drawings." % DrawingLimits.MAX_CELS); return
	var layer: Dictionary = layers[active_layer]
	for existing in layer.cels:
		if existing.start == frame:
			message("A cel already starts here. Move to another frame or delete this cel first.")
			return
	var before: Array = layer.cels.duplicate(true)
	var current := Drawing.cel_at(layer, frame)
	var image: Image
	if duplicate and not current.is_empty():
		var pixels:=Drawing.read_image(current)
		if pixels.has("error"):message(pixels.error);return
		image=pixels.image.duplicate()
	else:image=Drawing.blank(video.width,video.height)
	var created:=Drawing.insert(layer, frame, video.duration_frames, image)
	var why:=own_created_cel(created)
	if not why.is_empty():layer.cels=before;message(why);return
	push_history(CelPatch.create(str(layer.id),sequence_editor.active_owner,before,layer.cels))
	changed()
	refresh_layer()

func set_exposure() -> void:
	if exporting: return
	var layer: Dictionary = layers[active_layer]
	var cel := Drawing.cel_at(layer, frame)
	if cel.is_empty(): message("No cel at this frame."); return
	cel_timing.set_exposure(layer.id,cel.id,int(exposure.value))

func delete_cel() -> void:
	if exporting: return
	finish_stroke()
	var layer: Dictionary = layers[active_layer]
	var cel := Drawing.cel_at(layer, frame)
	if cel.is_empty(): return
	var before: Array = layer.cels.duplicate(true)
	layer.cels.erase(cel)
	push_history(CelPatch.create(str(layer.id),sequence_editor.active_owner,before,layer.cels))
	changed()

func key_dialog() -> void:
	if exporting: return
	if camera_transform_editor and camera_transform_editor.has_draft():message("Apply or reload the numeric camera draft in Advanced Camera before saving a camera key.");return
	if mode.selected not in [1, 2]: message("Switch to Scene or Pose mode and position the editor camera first."); return
	for key in keys:
		if key.frame == frame:
			confirm_action("Replace camera key at frame %d? Undo restores the previous key." % frame, insert_key)
			return
	insert_key()

func insert_key() -> void:
	var value:=Timeline.from_camera(frame,renderer.camera,interpolation.get_item_text(interpolation.selected))
	var error:=Timeline.range_error([value])
	if not error.is_empty():message(error);return
	var before := keys.duplicate(true)
	Timeline.put_key(keys,value)
	for key in keys: # Neon "Just saved" chip (session-only UI note, never stored)
		if int(key.frame) == frame: last_saved_key = key.duplicate(true)
	push_history({"type": "keys", "before": before, "after": keys.duplicate(true)})
	changed()
	message("Camera key saved at frame %d." % frame)

func delete_key() -> void:
	if exporting or keys.size() <= 1: return
	var before := keys.duplicate(true)
	keys = keys.filter(func(key): return key.frame != frame)
	push_history({"type": "keys", "before": before, "after": keys.duplicate(true)})
	changed()
	set_frame(frame)

func camera_button(index: int, pressed: bool, ctrl := false, cursor_origin:=Vector2(INF,INF)) -> void:
	if index not in [MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT, MOUSE_BUTTON_MIDDLE]: return
	if index == MOUSE_BUTTON_LEFT: camera_free = pressed and ctrl
	if pressed and ctrl and navigation_scheme=="orbit" and index in [MOUSE_BUTTON_LEFT,MOUSE_BUTTON_RIGHT] and camera_buttons==0:
		if not orbit_control.begin(renderer.camera,orbit_pivot(),"orbit" if index==MOUSE_BUTTON_LEFT else "pan"):
			camera_free=false;message("Frame the selected object before orbiting this close.");return
	if pressed and camera_buttons==0:
		camera_cursor_origin=cursor_origin if cursor_origin.is_finite() else get_viewport().get_mouse_position()
		camera_cursor_restore_pending=true
	var flag := 1 << (index - 1)
	if pressed: camera_buttons |= flag
	else: camera_buttons &= ~flag
	navigating = camera_buttons != 0
	if navigating:Input.mouse_mode=Input.MOUSE_MODE_CAPTURED
	else:
		orbit_control.end();finish_camera_capture()

func camera_motion(relative: Vector2) -> void:
	var camera: Camera3D = renderer.camera
	var speed := 0.02 if Input.is_key_pressed(KEY_SHIFT) else 0.008
	if (camera_buttons & 3) == 3:
		# Both primary buttons roll about the viewing axis without changing position.
		camera.rotate_object_local(Vector3.FORWARD, -relative.x * 0.003)
	elif orbit_control.active:
		orbit_control.motion(camera,relative)
	elif camera_buttons & MOUSE_BUTTON_MASK_MIDDLE:
		camera.position += camera.basis.z * relative.y * speed
	elif camera_buttons & MOUSE_BUTTON_MASK_RIGHT or camera_free:
		# World-up yaw plus local pitch preserves existing camera roll.
		camera.global_rotate(Vector3.UP, -relative.x * 0.003)
		camera.rotate_object_local(Vector3.RIGHT, -relative.y * 0.003)
		camera.quaternion = camera.quaternion.normalized()
	elif camera_buttons & MOUSE_BUTTON_MASK_LEFT:
		camera.position += (-camera.basis.x * relative.x + camera.basis.y * relative.y) * speed

func finish_camera_capture(restore_cursor:=true) -> void:
	Input.mouse_mode=Input.MOUSE_MODE_VISIBLE
	var pending:=camera_cursor_restore_pending;camera_cursor_restore_pending=false
	if pending and restore_cursor:
		var point:=camera_cursor_origin.clamp(Vector2.ZERO,get_viewport_rect().size-Vector2.ONE)
		get_viewport().warp_mouse(point);camera_cursor_return_requested.emit(point)

func release_mouse(restore_cursor:=true) -> void:
	orbit_control.end()
	if canvas:canvas.cancel_middle()
	if physics_editor:physics_editor.release_grab()
	if world_selection: world_selection.cancel_gesture(true)
	camera_free = false
	camera_buttons = 0
	navigating = false
	finish_camera_capture(restore_cursor)

func orbit_pivot() -> Vector3:
	var node=world_selection.entity_root(world_selection.selected) if world_selection else null
	if node:
		var bounds:=preload("res://src/pose_bounds.gd").query(node)
		if bounds.error.is_empty():return bounds.bounds.get_center()
		if node is Node3D:return node.global_position
	return renderer.camera.global_position-renderer.camera.global_basis.z*5.

func frame_3d_scene() -> void:
	if exporting: return
	mode.select(1)
	change_mode(1)
	if renderer.frame_scene(renderer.environment_root()): message("Editor camera framed the imported scene. Insert a key to use this view in the shot.")
	else: message(renderer.last_framing.get("error","No renderable mesh to frame."))

func _input(event: InputEvent) -> void:
	if preload("res://src/camera_lens_gesture.gd").handle(self,event):get_viewport().set_input_as_handled();return
	if local_wind_review and local_wind_review.global_event(event):get_viewport().set_input_as_handled();return
	if keyboard_shortcuts and keyboard_shortcuts.capture(event):get_viewport().set_input_as_handled();return
	# Redesign keyboard navigation: a focused button must not swallow studio shortcuts (Space, arrows, Home/End...).
	if keyboard_nav and event is InputEventKey and event.pressed and not event.keycode in [KEY_TAB, KEY_ENTER, KEY_KP_ENTER] and get_viewport().gui_get_focus_owner() is BaseButton:
		_unhandled_key_input(event)
		if get_viewport().is_input_handled(): return
	if timeline and timeline.cel_gesture_active():
		if event is InputEventKey and event.pressed and event.keycode==KEY_ESCAPE or event is InputEventMouseButton and event.pressed and event.button_index==MOUSE_BUTTON_RIGHT:timeline.cancel_cel();get_viewport().set_input_as_handled();return
		if event is InputEventMouseMotion or event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT and not event.pressed:
			var local_event: InputEventMouse=event.duplicate();local_event.position=timeline.get_global_transform().affine_inverse()*event.position
			timeline._gui_input(local_event);get_viewport().set_input_as_handled();return
	if drawing_selection_editor and drawing_selection_editor.global_event(event):get_viewport().set_input_as_handled();return
	if color_sampler and mode.selected==0 and tool.selected==3 and not (home and home.visible) and not has_dialog(self) and event is InputEventKey and event.pressed and event.keycode==KEY_ESCAPE:
		color_sampler.cancel();get_viewport().set_input_as_handled();return
	if fill_editor and not fill_editor.context.is_empty() and event is InputEventKey and event.pressed and event.keycode==KEY_ESCAPE and (fill_editor.busy() or not fill_editor.pending.is_empty()):
		fill_editor.cancel();get_viewport().set_input_as_handled();return
	if home and home.visible:
		if event is InputEventKey and event.pressed and event.keycode==KEY_ESCAPE and not has_dialog(self):home.hide();get_viewport().set_input_as_handled()
		return
	if pose_editor and pose_editor.contacts and pose_editor.contacts.viewport and pose_editor.contacts.viewport.global_event(event):get_viewport().set_input_as_handled();return
	if physics_editor and physics_editor.helper_editor and physics_editor.helper_editor.global_patch_event(event):
		get_viewport().set_input_as_handled();return
	if physics_editor and physics_editor.grabbing():
		if event is InputEventKey and event.pressed and event.keycode==KEY_ESCAPE:
			physics_editor.release_grab();get_viewport().set_input_as_handled();return
		if event is InputEventMouseMotion or event is InputEventMouseButton:
			var rect: Rect2=canvas.image_rect()
			var local: Vector2=canvas.get_global_transform().affine_inverse()*event.position
			if physics_editor.pointer(event,(local-rect.position)/rect.size*Vector2(video.width,video.height)):
				get_viewport().set_input_as_handled();return
	if physics_editor and physics_editor.recording and physics_editor.recording.active and event is InputEventKey and event.pressed and event.keycode==KEY_ESCAPE:
		physics_editor.recording.cancel();get_viewport().set_input_as_handled();return
	if timeline and timeline.audio_gesture_active():
		if event is InputEventKey and event.pressed and event.keycode==KEY_ESCAPE or event is InputEventMouseButton and event.pressed and event.button_index==MOUSE_BUTTON_RIGHT:
			timeline.cancel_audio();get_viewport().set_input_as_handled();return
		if event is InputEventMouseMotion or event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT and not event.pressed:
			var local_event: InputEventMouse=event.duplicate()
			local_event.position=timeline.get_global_transform().affine_inverse()*event.position
			timeline._gui_input(local_event);get_viewport().set_input_as_handled();return
	if timeline and not timeline.moving_id.is_empty():
		if event is InputEventKey and event.pressed and event.keycode==KEY_ESCAPE:
			timeline.finish_move(true);get_viewport().set_input_as_handled();return
		if event is InputEventMouseMotion:
			timeline.drag_motion(timeline.get_global_transform().affine_inverse()*event.position)
			get_viewport().set_input_as_handled();return
		if event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT and not event.pressed:
			timeline.finish_move();get_viewport().set_input_as_handled();return
	if event is InputEventKey and event.keycode==KEY_ALT:
		var focus := get_viewport().gui_get_focus_owner()
		pose_editor.reveal_bones = event.pressed and mode.selected in [1,2] and not (focus is LineEdit or focus is TextEdit) and not exporting and not has_dialog(self)
		pose_editor.update_gizmo()
	if world_selection and world_selection.pending_button!=0 and event is InputEventMouseButton and not event.pressed:
		if not canvas.get_global_rect().has_point(event.position): world_selection.cancel_gesture(true)
	if event is InputEventKey and event.keycode == KEY_CTRL and not event.pressed:
		camera_free = false
		if orbit_control.active:release_mouse()
	if event is InputEventMouseMotion and pose_editor.dragging and not exporting:
		var rect: Rect2 = canvas.image_rect()
		var point: Vector2 = (event.position - canvas.global_position - rect.position) / rect.size * Vector2(video.width,video.height)
		pose_editor.input(event, point)
		get_viewport().set_input_as_handled()
		return
	# Captured motion must continue even if the pointer leaves the canvas area.
	if event is InputEventMouseMotion and navigating and not exporting and not playing:
		camera_motion(event.relative)
		get_viewport().set_input_as_handled()
		return
	if event is InputEventMouseButton and not event.pressed:
		if event.button_index == MOUSE_BUTTON_LEFT:
			pose_editor.finish_drag()
			finish_stroke()
			if timeline: timeline.dragging = false
			if timeline_ruler:timeline_ruler.dragging=false
		if camera_buttons != 0: camera_button(event.button_index, false)
		if event.button_index == MOUSE_BUTTON_MIDDLE and canvas: canvas.panning = false
		if event.button_index == MOUSE_BUTTON_MIDDLE and canvas and not canvas.get_global_rect().has_point(event.position):canvas.cancel_middle()
	if event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE:
		pose_editor.reveal_bones = false
		pose_editor.finish_drag(true)
		release_mouse()
	if event is InputEventKey:
		_unhandled_key_input(event)

func _unhandled_key_input(event: InputEvent) -> void:
	if home and home.visible:return
	if not event is InputEventKey or not event.pressed or event.echo or exporting or navigating: return
	var focus := get_viewport().gui_get_focus_owner()
	if focus is LineEdit or focus is TextEdit: return
	if has_dialog(self): return
	if event.keycode == KEY_F11 and not event.ctrl_pressed and not event.alt_pressed and not event.shift_pressed and not event.meta_pressed and preload("res://src/shortcut_bindings.gd").action(keyboard_shortcuts.bindings,event).is_empty():
		toggle_fullscreen();get_viewport().set_input_as_handled();return
	match preload("res://src/shortcut_bindings.gd").action(keyboard_shortcuts.bindings,event):
		"save": save()
		"undo": undo()
		"redo", "redo_alternate": redo()
		"play": toggle_play()
		"previous": step(-1)
		"next": step(1)
		"first": stop();set_frame(0)
		"last": stop();set_frame(video.duration_frames-1)
		"pen": if mode.selected==0:finish_stroke();tool.select(0)
		"eraser": if mode.selected==0:finish_stroke();tool.select(1)
		"fill": if mode.selected==0:finish_stroke();tool.select(2)
		"sample": if mode.selected==0:color_sampler.arm()
		"select": if mode.selected==0:drawing_selection_editor.arm()
		"camera": key_dialog()
		_: return
	get_viewport().set_input_as_handled()

func choose_file(title: String, filters: PackedStringArray, action: Callable, initial_dir := "") -> void:
	if exporting: return
	stop()
	var dialog := FileDialog.new()
	dialog.access = FileDialog.ACCESS_FILESYSTEM
	dialog.file_mode = FileDialog.FILE_MODE_OPEN_FILE
	dialog.title = title
	dialog.filters = filters
	add_child(dialog)
	if not initial_dir.is_empty() and DirAccess.dir_exists_absolute(initial_dir): dialog.current_dir = initial_dir
	dialog.file_selected.connect(func(path): dialog.hide(); dialog.queue_free(); action.call(path))
	dialog.canceled.connect(dialog.queue_free)
	dialog.popup_centered_ratio(0.7)

func choose_directory(title: String, action: Callable, initial_dir := "") -> void:
	if exporting: return
	stop()
	var dialog := FileDialog.new()
	dialog.title = title
	dialog.access = FileDialog.ACCESS_FILESYSTEM
	dialog.file_mode = FileDialog.FILE_MODE_OPEN_DIR
	add_child(dialog)
	if not initial_dir.is_empty() and DirAccess.dir_exists_absolute(initial_dir): dialog.current_dir = initial_dir
	dialog.dir_selected.connect(func(path): dialog.hide(); dialog.queue_free(); action.call(path))
	dialog.canceled.connect(dialog.queue_free)
	dialog.popup_centered_ratio(0.7)

func confirm_action(text: String, action: Callable) -> void:
	var dialog := ConfirmationDialog.new()
	dialog.dialog_text = text
	add_child(dialog)
	dialog.confirmed.connect(func(): dialog.hide(); dialog.queue_free(); action.call())
	dialog.canceled.connect(dialog.queue_free)
	dialog.popup_centered()

func project_snapshot() -> Dictionary:
	var snapshot: Dictionary=sequence_editor.project_snapshot()
	snapshot["reference_sheet"]=reference_sheet.document()
	return snapshot

func current_world() -> Dictionary:
	if renderer.world_runtime:return renderer.world_state()
	return WorldDocument.from_legacy({"schema_version":3,"source":source,"scene":{"source_name":source.get_file()},"model":renderer.model_state()})

func refresh_scene_name() -> void:
	if renderer.world_runtime:
		source=""
		for row in renderer.world_state().objects:
			if row.kind=="environment":source=row.source
		scene_name.text="World • %d objects • %d × %d" % [renderer.world_runtime.instances.size()+renderer.world_runtime.effects.size(),video.width,video.height]
	else:scene_name.text="Scene: "+source.get_file()+" • %d × %d" % [video.width,video.height]

func restore_world(document: Dictionary) -> String:
	stop_local_wind("World changed")
	if sequence_editor:
		var why: String=sequence_editor.scene_error(document)
		if not why.is_empty():message(why);return why
	var prepared: Dictionary=renderer.prepare_world(document,int(video.duration_frames))
	if prepared.has("error"):message(prepared.error);return prepared.error
	physics_editor.clear()
	stop();finish_stroke();pose_editor.finish_drag();release_mouse()
	var selected: String=world_selection.selected
	var view: Dictionary=renderer.view_state()
	world_selection.clear()
	renderer.install_world(prepared,frame)
	world_selection.refresh()
	if renderer.world_runtime.instances.has(selected):world_selection.select_entity(selected,false)
	pose_editor.rebuild_tree();pose_editor.apply_frame()
	renderer.restore_view(view)
	refresh_scene_name();refresh_timeline()
	return ""

func append_object(data: Dictionary, kind: String, start_frame := 0, placement := {}) -> String:
	if exporting:return "Wait for the current operation to finish."
	if height_review and height_review.pending:return "Finish the pending height review first."
	if kind=="model" and placement.get("review_height",false):return height_review.start(data,start_frame,placement)
	var live: Dictionary=physics_editor.import_intents()
	var error:=append_object_data(data,kind,start_frame,placement)
	physics_editor.restore_import_intents(live)
	if error.is_empty() and kind=="model" and placement.get("physics_on_import",false):
		physics_editor.queue_import_start(last_import_id,true,false,true)
	return error

func append_object_data(data: Dictionary, kind: String, start_frame := 0, placement := {}) -> String:
	if sequence_editor and sequence_editor.used("objects")>=64:return "This project and its sequences already contain64 world objects."
	if exporting:return "Wait for the current operation to finish."
	var basis_error:=ImportBasis.record_error(data)
	if not basis_error.is_empty():return basis_error
	if data.has("asset_basis") and kind!="model":return "Human references apply only to character models."
	if not physics_editor.freeze_all():return status.text
	pose_editor.finish_drag();finish_stroke()
	var before:=current_world();var after:=before.duplicate(true);var row:=data.duplicate(true)
	row["kind"]=kind;row["parent_id"]="";row["start_frame"]=start_frame
	if kind=="model" and not placement.is_empty():
		if renderer.world_runtime:renderer.world_runtime.evaluate(start_frame)
		var root_transform:=Transform3D(Basis(Timeline.quaternion(row.rotation_xyzw)).scaled(Vector3.ONE*float(row.scale)),Vector3.ZERO)
		var basis:=ImportBasis.model_admission(row,true,true)
		if basis.has("error"):return basis.error
		root_transform=root_transform*Transform3D(Basis.IDENTITY.scaled(Vector3.ONE*float(basis.factor)),Vector3.ZERO)
		var planned: Dictionary=ImportPlacement.plan(renderer,row.source,placement,SourceShape.setting(row),root_transform)
		if renderer.world_runtime:renderer.world_runtime.evaluate(frame,false,renderer.active_instance_id if mode.selected==2 else "")
		if planned.has("error"):message(planned.error);return planned.error
		var point: Vector3=planned.position
		row.position=[point.x,point.y,point.z]
		planned.erase("position");row.metadata["initial_placement"]=planned

	# Retain the imported revision even if the author later edits/moves that source.
	var original: String=ProjectSettings.globalize_path(row.source)
	var input:=FileAccess.open(original,FileAccess.READ)
	if input==null or input.get_length()>128*1024*1024:return "Cannot read the GLB, or it exceeds128MiB."
	var cache:=ProjectSettings.globalize_path("res://output/imports")
	if DirAccess.make_dir_recursive_absolute(cache)!=OK:return "Cannot create the managed import folder."
	var managed:=cache.path_join(row.sha256+".glb")
	var copy_error:=Storage.managed_copy(original,managed,row.sha256)
	if not copy_error.is_empty():return copy_error
	row.source=managed;row.metadata["import_source"]=original
	after.objects.append(row)
	var error:=restore_world(after)
	if not error.is_empty():return error
	last_import_id=row.id
	has_project.origins[managed.replace("\\","/")]=original
	push_history({"type":"world","before":before,"after":after});changed()
	world_selection.select_entity(row.id)
	message("Added "+row.name+". Other objects, drawing and shot keys are preserved."+placement_message(row))
	return ""

func placement_message(data: Dictionary) -> String:
	var placement: Dictionary=data.get("metadata",{}).get("initial_placement",{})
	if placement.get("overlap",false):return " Nearby spaces are occupied; the model was placed in view so you can adjust it."
	if placement.get("support")=="view":return " No nearby floor was found; the model was placed in view."
	return ""

func remove_world_object(id: String) -> String:
	physics_editor.freeze_all()
	var before:=current_world();var removed:={id:true};var expanded:=true
	while expanded:
		expanded=false
		for row in before.objects:
			if removed.has(row.parent_id) and not removed.has(row.id):removed[row.id]=true;expanded=true
	var after:=before.duplicate(true);after.objects=after.objects.filter(func(row):return not removed.has(row.id))
	var error:=restore_world(after)
	if not error.is_empty():return error
	push_history({"type":"world","before":before,"after":after});changed()
	return ""

func load_scene(path: String, start_frame := 0) -> String:
	if exporting:return "Wait for the current operation to finish."
	if path.get_extension().to_lower() != "glb":source_import.start(path,false,start_frame);return ""
	var definition: Dictionary=pose_editor.definition(path)
	if definition.has("error"):message(definition.error);return definition.error
	return append_object(definition.data,"environment",start_frame)

func new_dialog() -> void:
	if exporting or source_import.pid > 0: return
	if dirty: confirm_action("Start a new empty project and discard unsaved edits? Save first to keep them.", new_project)
	else: new_project()

func demo_dialog() -> void:
	if exporting or source_import.pid > 0: return
	if dirty: confirm_action("Open the sample room as a new project and discard unsaved edits?", load_demo_room)
	else: load_demo_room()

func reset_document(path: String, sample := false) -> bool:
	if exporting or source_import.pid > 0: return false
	stop_local_wind("Document changed")
	var prepared: Dictionary=renderer.prepare_legacy(path) if sample else renderer.prepare_world(WorldDocument.empty(),48)
	if prepared.has("error"):message(prepared.error);return false
	if tutorials:tutorials.document_changing()
	reference_sheet.install_prepared({"data":{}})
	sequence_editor.clear()
	raster_budget.install(null)
	stop(); finish_stroke(); pose_editor.finish_drag(); release_mouse()
	world_selection.clear()
	if sample:renderer.install_legacy(prepared)
	else:renderer.install_world(prepared)
	pose_editor.selected = "@root"
	pose_editor.rebuild_tree()
	source = path if sample else "";last_import_id="";project_folder = ""; has_project.clear_identity()
	video = {"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":48,"visibility_fade_ms":300,"world_background":"legacy_blue" if sample else "black","lighting_mode":"studio" if sample else "unshaded"}
	sync_output_size()
	renderer.set_background(video.world_background)
	palette=[];palette_editor.refresh(true)
	layers.clear(); layer_choice.clear()
	for title in ["Rough", "Ink"]:
		layers.append({"id":str(ResourceUID.create_id()),"name":title,"visible":true,"cels":[]})
		layer_choice.add_item(title)
	active_layer = 1; layer_choice.select(1)
	audio_clip = {}; rebuild_audio()
	history.clear(); redo_history.clear(); history_bytes = 0
	canvas.zoom = 1; canvas.pan = Vector2.ZERO; canvas.panning = false
	if sample:
		keys = [Timeline.key(0,Vector3(-1.5,2,5),Quaternion.IDENTITY,60),Timeline.key(48,Vector3(1.5,1.6,3),Quaternion(Vector3.UP,-0.15),52)]
	else:
		renderer.camera.position = Vector3(6,5,8)
		renderer.camera.look_at(Vector3.ZERO,Vector3.UP)
		keys = [Timeline.key(0,renderer.camera.position,renderer.camera.quaternion,60)]
	renderer.evaluate(keys,0)
	mode.select(0 if sample else 1); refresh_workspace()
	set_frame(0)
	scene_name.text = "Sample room • 1920 × 1080" if sample else "Empty world • 1920 × 1080"
	begin_recovery_session()
	refresh_recovery_schedule(false)
	dirty = false
	message("Sample room opened as a new project." if sample else "New empty world. Add a model or scene; Ctrl + left-drag enters free camera. Grid is editor-only.")
	if home:home.hide()
	return true

func new_project() -> bool:
	return reset_document("")

func load_demo_room() -> bool:
	var path := ProjectSettings.globalize_path("res://examples/room.glb")
	if not FileAccess.file_exists(path) and SceneIO.make_fixture(path) != OK:
		message("Cannot create the sample room. Current project preserved."); return false
	return reset_document(path,true)

func save() -> void:
	if exporting: return
	stop_local_wind("Save")
	if not physics_editor.freeze_all():return
	finish_stroke()
	pose_editor.finish_drag()
	if not has_project.path.is_empty() or project_folder.is_empty(): has_project.save_current(); return
	var snapshot:=project_snapshot()
	var error := Storage.save_project(project_folder,snapshot.video,snapshot.camera_keys,snapshot.layers,str(snapshot.get("source","")),int(snapshot.editor.frame),snapshot.audio,{},snapshot.get("model",{}),false,snapshot.world,{"sequence_editor":snapshot.sequence_context} if not snapshot.get("sequence_context",{}).is_empty() else {},snapshot.palette,snapshot.sequence_graph,null,snapshot.get("reference_sheet",{}))
	if error.is_empty():
		dirty = false
		reset_recovery_schedule()
		var resolved := Recovery.resolve(recovery_root.path_join(recovery_session))
		if not recovered_from.is_empty():
			var recovered_error := Recovery.resolve(recovered_from)
			if not recovered_error.is_empty(): resolved = recovered_error
			else: recovered_from = ""
		recovery_status.text = "Project saved" if resolved.is_empty() else "Saved; recovery copy retained"
		message("Saved editable project: " + project_folder)
	else: message(error)

func save_as() -> void:
	has_project.save_dialog()

func open_dialog() -> void:
	var action := func(): choose_file("Open Hybrid Animation Studio project", ["*.has ; Hybrid Animation Studio project", "*.has.backup ; Previous HAS save"], has_project.open_file)
	if dirty: confirm_action("Discard unsaved edits and open another project?", action)
	else: action.call()

func open_project(folder: String, manifest_name := "project.json",report_error := true) -> bool:
	open_project_error=""
	if exporting:open_project_error="Cannot open a project during export.";return false
	var data := Storage.load_project(folder, manifest_name,cold_cel_loading,cold_cel_min_bytes)
	return install_project_data(data,folder,report_error)

func install_project_data(data: Dictionary,folder: String,report_error := true) -> bool:
	# Worker loading ends before this main-thread transaction prepares scene nodes.
	open_project_error=""
	if exporting:open_project_error="Cannot open a project during export.";return false
	if data.has("error"):
		open_project_error=data.error
		if report_error:message(open_project_error)
		return false
	var content_schema: int=preload("res://src/import_basis_project.gd").decoded_content_schema(data)
	if content_schema<1:
		open_project_error="Unsupported project size/reference capability. Current project preserved."
		if report_error:message(open_project_error)
		return false
	var world_project:=content_schema>=4
	var ownership_error:=preload("res://src/project_raster_ownership.gd").adopt(data)
	if not ownership_error.is_empty():
		open_project_error=ownership_error
		if report_error:message(open_project_error)
		return false
	var reference_candidate: Dictionary=reference_sheet.prepare_project(data.get("reference_sheet",{}))
	if reference_candidate.has("error"):
		open_project_error=reference_candidate.error
		if report_error:message(open_project_error)
		return false
	var prepared: Dictionary = renderer.prepare_world(data.world,int(data.video.duration_frames),data.video) if world_project else renderer.prepare_legacy(data.source,data.model,data.video)
	if prepared.has("error"):
		open_project_error=prepared.error
		if report_error:message(open_project_error)
		return false
	var sequence_candidate: Dictionary=sequence_editor.prepare_runtime(data.get("sequence_graph",{}),data)
	if sequence_candidate.has("error"):
		if world_project:prepared.runtime.dispose()
		else:
			prepared.scene.free()
			if prepared.model:prepared.model.root.free()
		open_project_error=sequence_candidate.error
		if report_error:message(open_project_error)
		return false
	if tutorials:tutorials.document_changing()
	sequence_editor.clear()
	stop()
	finish_stroke()
	pose_editor.finish_drag()
	release_mouse()
	world_selection.clear()
	if world_project:renderer.install_world(prepared)
	else:renderer.install_legacy(prepared)
	reference_sheet.install_prepared(reference_candidate)
	pose_editor.selected="@root";pose_editor.rebuild_tree()
	source = str(data.get("source",""));last_import_id=""
	video = data.video
	sync_output_size()
	renderer.set_background(str(video.get("world_background","legacy_blue")))
	keys = data.camera_keys
	layers = data.layers
	raster_budget.install(data.get("raster_cache"));raster_budget_due=Time.get_ticks_msec()+1000
	palette=data.get("palette",[]).duplicate(true);palette_editor.refresh(true)
	if layers.is_empty():
		for title in ["Rough","Ink"]:layers.append({"id":str(ResourceUID.create_id()),"name":title,"visible":true,"cels":[]})
	audio_clip = data.audio
	project_folder = folder
	has_project.clear_identity()
	active_layer = mini(active_layer, layers.size() - 1)
	layer_choice.clear()
	for layer in layers: layer_choice.add_item(layer.name)
	layer_choice.select(active_layer)
	history.clear()
	redo_history.clear()
	history_bytes = 0
	mode.select(1)
	refresh_scene_name()
	refresh_workspace()
	sequence_editor.adopt(data,sequence_candidate.runtime)
	rebuild_audio()
	var saved_editor = data.get("editor", {})
	var saved_frame := 0
	if saved_editor is Dictionary and Storage.integer(saved_editor.get("frame"), 0, video.duration_frames):
		saved_frame = int(saved_editor.frame)
	renderer.evaluate(keys,saved_frame)
	set_frame(saved_frame)
	world_selection.refresh();world_selection.clear()
	dirty = false
	begin_recovery_session()
	var context_error: String=sequence_editor.restore_context(saved_editor.get("sequence_editor",{}) if saved_editor is Dictionary else {})
	if not context_error.is_empty():message(context_error)
	message("Opened " + folder)
	if home:home.hide()
	return true

func export_dialog() -> void:
	if exporting: return
	if not has_project.path.is_empty(): export_movie(has_project.path.get_base_dir())
	else: export_elsewhere()

func export_elsewhere() -> void:
	var initial: String = has_project.path.get_base_dir() if not has_project.path.is_empty() else project_folder
	choose_directory("Choose export folder (a new render folder will be created)", func(path): export_movie(path), initial)

func export_movie(parent: String) -> String:
	return await export_frames(parent,false,false)

func export_images_dialog() -> void:
	if exporting:return
	var drawings: bool=png_drawing_only.button_pressed
	if not has_project.path.is_empty():export_images(has_project.path.get_base_dir(),drawings)
	else:export_images_elsewhere()

func export_images_elsewhere() -> void:
	if exporting:return
	var drawings: bool=png_drawing_only.button_pressed
	var initial: String=has_project.path.get_base_dir() if not has_project.path.is_empty() else project_folder
	choose_directory("Choose PNG sequence folder (a new images folder will be created)",func(path):export_images(path,drawings),initial)

func export_images(parent: String,drawings_only:=false) -> String:
	return await export_frames(parent,true,drawings_only)

func selected_movie_profile() -> String:
	return str(encoder_quality.get_item_metadata(encoder_quality.selected)) if encoder_quality and encoder_quality.selected>=0 else ""

func sync_canvas_size() -> void:
	var size:=preload("res://src/canvas_size.gd").size(video)
	if size==Vector2i.ZERO:return
	if canvas:canvas.resolution=Vector2(size);canvas.queue_redraw()
	if renderer and renderer.viewport:renderer.viewport.size=size
	drawing_overlay_cache.clear();Drawing.opacity_cache.clear()
	if onion_editor:onion_editor.release_guides()
	if project_canvas:project_canvas.sync()

func sync_output_size() -> void:
	sync_canvas_size()
	if not output_size:return
	for i in range(output_size.item_count):
		var id=output_size.get_item_metadata(i);var dimensions: Vector2i=OutputSize.PROFILES[id]
		output_size.set_item_text(i,"%d x %d" % [dimensions.x,dimensions.y]+(" (native)" if id==preload("res://src/canvas_size.gd").profile(video) else ""))
		if id==preload("res://src/canvas_size.gd").delivery(video):output_size.select(i)

func change_output_size(index: int) -> void:
	if exporting or index<0 or index>=output_size.item_count:return
	var value=output_size.get_item_metadata(index)
	if not OutputSize.error(value).is_empty():message(OutputSize.error(value));sync_output_size();return
	if value==preload("res://src/canvas_size.gd").delivery(video):return
	finish_stroke();pose_editor.finish_drag()
	var before=video.get("output_size")
	if value==preload("res://src/canvas_size.gd").profile(video):video.erase("output_size")
	else:video["output_size"]=value
	push_history({"type":"output_size","before":before,"after":video.get("output_size"),"bytes":256})
	changed()

func selected_output_size() -> String:
	return str(output_size.get_item_metadata(output_size.selected)) if output_size and output_size.selected>=0 else ""

func export_frames(parent: String,images_only: bool,drawings_only: bool) -> String:
	if exporting: return "Export already running."
	stop_local_wind("Export")
	var delivery:=selected_output_size()
	var size_error:=OutputSize.error(delivery)
	if not size_error.is_empty():message(size_error);return size_error
	var source_video: Dictionary=video.duplicate(true)
	var output_video: Dictionary=source_video.duplicate(true)
	var dimensions: Vector2i=OutputSize.PROFILES[delivery]
	output_video.width=dimensions.x;output_video.height=dimensions.y
	var profile:=selected_movie_profile()
	if not images_only:
		var why:=Encoder.profile_error(profile)
		if not why.is_empty():message(why);return why
	if drawing_selection_editor:drawing_selection_editor.cancel()
	if not physics_editor.freeze_all():return status.text
	finish_stroke()
	pose_editor.finish_drag()
	stop()
	release_mouse()
	if not images_only:
		var capabilities := Encoder.detect(encoder_path.text)
		if not capabilities.ok:
			message("FFmpeg missing or libx264/AAC unavailable. Turn on Advanced, then locate a compatible FFmpeg in Movie encoder.")
			return status.text
	if not DirAccess.dir_exists_absolute(parent):
		message("Export folder is unavailable. Use Advanced → Movie encoder → PNG to another folder." if images_only else "Export folder is unavailable. Use Advanced → Movie encoder → Export to another folder, or save your HAS project in an available folder.")
		return status.text
	var folder := ""
	for attempt in range(32):
		var candidate := parent.path_join(("images_" if images_only else "render_")+"%d_%d_%d" % [Time.get_unix_time_from_system(), Time.get_ticks_usec(), attempt])
		# Only a newly created directory is ours; never reuse an existing render.
		if DirAccess.make_dir_absolute(candidate) == OK:
			folder = candidate
			break
	if folder.is_empty():
		message("Cannot create a new export folder. Check disk space/permissions or choose another folder in Advanced → Movie encoder.")
		return status.text
	last_export_folder = folder
	interrupted_frames_folder=""
	saved_frames_button.hide()
	retry_render.clear()
	retry_encode_button.hide()
	exporting = true
	export_controls(self, true)
	cancel_export = false
	cancel_button.visible = true
	var old_mode := mode.selected
	var old_view: Dictionary=renderer.view_state()
	var error := ""
	var export_keys := keys.duplicate(true)
	var export_layers := layers.duplicate(true)
	var completed:=0
	for n in range(output_video.duration_frames):
		if cancel_export: error = "Export cancelled. PNG frames preserved."; break
		message("Rendering %d / %d • %s" % [n + 1, output_video.duration_frames, folder])
		var image: Image
		if images_only and drawings_only:
			image=Drawing.blank(int(source_video.width),int(source_video.height))
			if renderer.sequence_runtime:
				var nested: Image=await renderer.sequence_runtime.render(renderer.sequence_owner,n,true,true)
				if nested==null:error=renderer.sequence_runtime.last_error;break
				image.blend_rect(nested,Rect2i(0,0,int(source_video.width),int(source_video.height)),Vector2i.ZERO)
			var ink:=Drawing.composite_result(export_layers,n,int(source_video.width),int(source_video.height))
			if ink.has("error"):error=ink.error;break
			image.blend_rect(ink.image,Rect2i(0,0,int(source_video.width),int(source_video.height)),Vector2i.ZERO)
			await get_tree().process_frame
		else:image=await renderer.capture(export_keys, export_layers, n, true)
		if image==null:
			error=renderer.last_capture_error;break
		image=OutputSize.resample(image,dimensions)
		if image==null:error="Cannot prepare the selected output size. Frames preserved.";break
		if image.save_png(folder.path_join("frame_%06d.png" % (n + 1))) != OK:
			error = "Could not write PNG (check disk space/permissions). Frames preserved."
			break
		completed+=1
	if cancel_export and error.is_empty():
		error = "Export cancelled. PNG frames preserved."
	var mix_path := ""
	if error.is_empty():
		if not audio_mix.is_empty():
			message("Writing synchronized audio mix…")
			mix_path = folder.path_join("mixed_audio.wav")
			if audio_mix.is_empty() or audio_mix.stream.save_to_wav(mix_path) != OK:
				error = "Cannot write synchronized WAV mix. PNGs preserved."
		if error.is_empty() and not images_only:
			message("Encoding H.264 MP4… Cancel remains available.")
			encoder = Encoder.new();encoder.profile=profile
			error = await encoder.encode(get_tree(), encoder_path.text, folder, output_video, mix_path)
			if not error.is_empty():
				retry_render={"folder":folder,"video":output_video.duplicate(true),"audio":mix_path,"session":recovery_session,"revision":recovery_revision}
				retry_encode_button.show()
	if images_only:
		var summary:={"format":"studio_image_sequence_1","video":output_video.duplicate(true),"pattern":"frame_%06d.png","first_frame":1,"first_project_frame":0,"rendered_frames":completed,"drawing_only":drawings_only,"audio":"mixed_audio.wav" if not mix_path.is_empty() and error.is_empty() else "","status":"complete" if error.is_empty() else "cancelled" if cancel_export else "failed"}
		if dimensions!=Vector2i(int(source_video.width),int(source_video.height)):summary["source_video"]=source_video
		var temporary:=folder.path_join("sequence.json.tmp");var file:=FileAccess.open(temporary,FileAccess.WRITE)
		if file:
			file.store_string(JSON.stringify(summary,"",true,true));file.flush();var written:=file.get_error()==OK;file.close()
			if not written or DirAccess.rename_absolute(temporary,folder.path_join("sequence.json"))!=OK:error="Cannot write PNG sequence timing record. Frames preserved."
		else:error="Cannot write PNG sequence timing record. Frames preserved."
	encoder = null
	exporting = false
	export_controls(self, false)
	pose_editor.sync_enabled()
	cancel_button.visible = false
	mode.select(old_mode)
	if old_mode in [1, 2]:
		renderer.restore_view(old_view)
	else: renderer.evaluate(keys, frame)
	pose_editor.apply_frame()
	if error.is_empty() and not images_only:
		last_finished_movie=folder.path_join("movie.mp4")
		movie_folder_button.tooltip_text=last_finished_movie
		movie_folder_button.show()
	elif FileAccess.file_exists(folder.path_join("frame_000001.png")):
		interrupted_frames_folder=folder
		saved_frames_button.tooltip_text=folder
		saved_frames_button.show()
	message(("Exported PNG sequence: " + folder if images_only else "Exported " + folder.path_join("movie.mp4")) if error.is_empty() else error + "\n" + folder)
	if not images_only:movie_export_finished.emit(folder,error.is_empty())
	return error

func show_movie_folder() -> void:
	if exporting or last_finished_movie.is_empty():return
	open_result_folder(last_finished_movie.get_base_dir())

func retry_saved_movie() -> void:
	if exporting or retry_render.is_empty():return
	var profile:=selected_movie_profile();var why:=Encoder.profile_error(profile)
	if not why.is_empty():message(why);return
	var source:=retry_render.duplicate(true)
	for n in range(source.video.duration_frames):
		var frame_name:="frame_%06d.png" % (n+1)
		if not FileAccess.file_exists(source.folder.path_join(frame_name)):
			message("Missing %s. Restore it in Show saved frames, then retry, or export the scene again." % frame_name)
			return
	if not source.audio.is_empty() and not FileAccess.file_exists(source.audio):
		message("Missing %s. Restore it in Show saved frames, then retry, or export the scene again." % str(source.audio).get_file())
		return
	stop();exporting=true;cancel_export=false;export_controls(self,true);cancel_button.show()
	message("Encoding the saved frames and sound…")
	encoder=Encoder.new();encoder.profile=profile
	var error: String=await encoder.encode(get_tree(),encoder_path.text,source.folder,source.video,source.audio,true)
	var finished: String=encoder.finished_path
	encoder=null;exporting=false;export_controls(self,false);pose_editor.sync_enabled();cancel_button.hide()
	if not error.is_empty():message(error);return
	last_finished_movie=finished;movie_folder_button.tooltip_text=finished;movie_folder_button.show()
	retry_render.clear();retry_encode_button.hide();saved_frames_button.hide()
	message("Exported "+finished)
	if source.session==recovery_session and source.revision==recovery_revision:movie_export_finished.emit(source.folder,true)

func open_result_folder(folder: String) -> void:
	if exporting or folder.is_empty():return
	if not DirAccess.dir_exists_absolute(folder):
		message("The export folder has moved: "+folder)
		return
	if OS.shell_open(folder)!=OK:message("Open this export folder: "+folder)

func export_controls(node: Node, busy: bool) -> void:
	if node is TimelineView:
		node.interactive=not busy
		if busy:node.finish_move(true);node.cancel_audio();node.cancel_cel();node.dragging=false
	if node == cancel_button: return
	if node is BaseButton: node.disabled = busy
	if node is SpinBox or node is LineEdit: node.editable = not busy
	for child in node.get_children(): export_controls(child, busy)

func show_notices() -> void:
	var dialog := AcceptDialog.new()
	dialog.title = "Credits / open source notices"
	dialog.exclusive=false
	dialog.dialog_text = "Godot Engine 4.6 — MIT\nCopyright (c) 2014-present Godot Engine contributors.\nCopyright (c) 2007-2014 Juan Linietsky, Ariel Manzur.\nhttps://godotengine.org/license/\n\nFFmpeg is invoked as your separately installed executable.\nLicense and codec options depend on the installed build; no binary is bundled.\nhttps://ffmpeg.org/legal.html\n\nRoom fixture: original procedural geometry. Imported asset rights must be verified.\nApplication license: owner decision pending.\nFull records: THIRD_PARTY_NOTICES.md and docs/licenses.md."
	add_child(dialog)
	dialog.confirmed.connect(dialog.queue_free)
	dialog.popup_centered(Vector2i(720, 430))

func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST:
		if raster_importer and raster_importer.pid>0:
			raster_importer.cancel();message("Cancelling artwork preparation. Close again after it stops.")
		elif video_importer and video_importer.pid>0:
			video_importer.cancel();message("Cancelling video preparation. Close again after it stops.")
		elif source_import and source_import.pid > 0:
			source_import.cancel()
			message("Cancelling Source preparation. Close again after it stops.")
		elif has_project and has_project.pid > 0:
			has_project.cancel()
			message("Cancelling project operation. Close again after it stops.")
		elif exporting:
			cancel_export = true
			if encoder: encoder.cancel()
			message("Cancelling export. Close again after it stops.")
		elif dirty: confirm_action("Close with unsaved edits?", quit_studio)
		else: quit_studio()
	if what == NOTIFICATION_WM_WINDOW_FOCUS_OUT:
		if keyboard_shortcuts:keyboard_shortcuts.cancel_capture()
		if physics_editor and physics_editor.helper_editor:physics_editor.helper_editor.cancel_patch_drag()
		if pose_editor: pose_editor.reveal_bones = false; pose_editor.finish_drag()
		finish_stroke()
		release_mouse(false)
		if canvas: canvas.panning = false
		if canvas: canvas.cancel_middle()
		if timeline: timeline.dragging = false;timeline.cancel_audio();timeline.cancel_cel();timeline.finish_move(true);timeline.queue_redraw()
		if timeline_ruler:timeline_ruler.dragging=false

var closing_studio:=false
func quit_studio() -> void:
	if closing_studio:return
	closing_studio=true
	if tutorials and tutorials.active:tutorials.save_resume()
	if sequence_editor:await sequence_editor.finish()
	get_tree().quit()

func smoke() -> void:
	# Integration checks are in a separate runner, loaded only when requested.
	var runner = load("res://tests/app_smoke.gd").new()
	add_child(runner)
	await runner.run(self)

func audio_smoke() -> void:
	var runner = load("res://tests/audio_editor_smoke.gd").new()
	add_child(runner)
	await runner.run(self)

func ui_smoke() -> void:
	var runner = load("res://tests/ui_smoke.gd").new()
	add_child(runner)
	await runner.run(self)

func recovery_smoke() -> void:
	var runner = load("res://tests/recovery_smoke.gd").new()
	add_child(runner)
	await runner.run(self)

func pose_smoke() -> void:
	var runner = load("res://tests/pose_smoke.gd").new()
	add_child(runner)
	await runner.run(self)

func begin_recovery_session() -> void:
	if drawing_selection_editor:drawing_selection_editor.cancel()
	if color_sampler:color_sampler.cancel()
	Drawing.opacity_cache.clear()
	if fill_editor:fill_editor.cancel()
	recovered_from = ""
	if recovery_root.is_empty(): recovery_root = ProjectSettings.globalize_path("res://output/recovery")
	recovery_session = "%d_%s" % [Time.get_unix_time_from_system(), str(ResourceUID.create_id())]
	if project_timing:project_timing.sync()
	if timeline:timeline.cancel_cel()
	if timeline_navigation:timeline_navigation.sync()
	checkpoint_revision = -1
	checkpoint_lesson_signature = ""
	reset_recovery_schedule()
	refresh_recovery_schedule(false)

func reset_recovery_schedule() -> void:
	recovery_schedule_generation+=1
	autosave_actions=0;autosave_retry_due=0
	recovery_checkpoint_requested=false
	autosave_due=Time.get_ticks_msec()+int(autosave_interval.value*60000)

func refresh_recovery_schedule(reset_deadline := true) -> void:
	autosave_time_controls.visible=autosave_schedule.selected==0
	autosave_action_controls.visible=autosave_schedule.selected==1
	if reset_deadline:autosave_due=Time.get_ticks_msec()+int(autosave_interval.value*60000)
	if recovery_status:recovery_status.text=("Recovery on • every %s min" % str(autosave_interval.value) if autosave_schedule.selected==0 else "Recovery on • after %d edits" % int(autosave_action_limit.value)) if autosave_enabled.button_pressed else "Recovery off — save manually"

func note_recovery_action(command: Dictionary) -> void:
	if command.type=="pixels":
		for position in command.before:
			if command.after.has(position) and command.before[position].get_data()!=command.after[position].get_data():autosave_actions+=1;return
	elif JSON.stringify(command.before,"",true,true)!=JSON.stringify(command.after,"",true,true):autosave_actions+=1

func has_dialog(node: Node) -> bool:
	for child in node.get_children():
		# Godot tooltips are unfocusable, mouse-transparent windows, not edits/dialogs.
		if child is Window and child.get_flag(Window.FLAG_NO_FOCUS) and child.get_flag(Window.FLAG_MOUSE_PASSTHROUGH):continue
		if child is Window and child.visible and (child.exclusive or child is Popup): return true
		if has_dialog(child): return true
	return false

func autosave_tick(force := false) -> void:
	if force:recovery_checkpoint_requested=true
	poll_recovery_preview()
	# Serialize journal writers without waiting on the UI thread.
	if recovery_writer.busy() or recovery_preview.busy():return
	if not autosave_enabled.button_pressed and not force: return
	# Lesson view/progress can change after Save without editing scene content.
	var lesson_context: Dictionary=tutorials.recovery_context() if tutorials else {}
	var lesson_signature := JSON.stringify({"lesson":lesson_context,"frame":frame},"",true,true) if not lesson_context.is_empty() else ""
	if (not dirty or recovery_revision == checkpoint_revision) and lesson_signature==checkpoint_lesson_signature:recovery_checkpoint_requested=false;return
	if physics_editor and physics_editor.is_running():return
	if drawing or navigating or playing or exporting or pose_editor.dragging or timeline and (not timeline.moving_id.is_empty() or timeline.audio_gesture_active() or timeline.cel_gesture_active()): return
	if has_dialog(self): return
	if not force:
		if Time.get_ticks_msec()<autosave_retry_due:return
		if autosave_retry_due==0:
			if autosave_schedule.selected==0 and Time.get_ticks_msec()<autosave_due:return
			if autosave_schedule.selected==1 and autosave_actions<int(autosave_action_limit.value):return
	recovery_checkpoint_requested=false
	autosave_due = Time.get_ticks_msec() + int(autosave_interval.value * 60000)
	var request:={"root":recovery_root,"session":recovery_session,"revision":recovery_revision,"generation":recovery_schedule_generation,"actions":autosave_actions,"lesson_signature":lesson_signature,"lesson_context":lesson_context,"frame":frame,"view":renderer.view_state(),"origin":has_project.path if not has_project.path.is_empty() else project_folder}
	var error: String=recovery_writer.start(project_snapshot(),request)
	if error.is_empty():recovery_status.text="Saving recovery copy…"
	else:recovery_checkpoint_failed(error)

func recovery_checkpoint_failed(error: String) -> void:
	autosave_retry_due=Time.get_ticks_msec()+30000
	recovery_status.text="Recovery failed. Edits are pending."
	message(error + (" Studio will retry after 30 seconds when idle. You can also save manually." if autosave_enabled.button_pressed else " Use Checkpoint now to retry, or save manually."))

func poll_recovery_checkpoint() -> void:
	var result: Dictionary=recovery_writer.poll()
	if result.is_empty():return
	recovery_writer_result=result
	var request: Dictionary=result.request
	if request.root!=recovery_root or request.session!=recovery_session:return
	if request.generation!=recovery_schedule_generation:
		# An exact-current manual Save reset this schedule during the write.
		# Resolve its now-obsolete checkpoint only after its final commit.
		if result.error.is_empty():recovery_writer_result["resolve_error"]=Recovery.resolve(result.folder)
		return
	last_recovery_capture_ms=request.capture_ms;last_recovery_worker_ms=result.worker_ms
	last_recovery_ms=last_recovery_capture_ms+last_recovery_worker_ms
	if not result.error.is_empty():recovery_checkpoint_failed(result.error);return
	checkpoint_revision=int(request.revision);checkpoint_lesson_signature=request.lesson_signature
	autosave_actions=maxi(0,autosave_actions-int(request.actions));autosave_retry_due=0
	recovery_status.text="Recovery copy saved" if recovery_revision==checkpoint_revision else "Recovery saved; newer edits pending"
	finish_recovery_preview.call_deferred(result.folder,result.digest,int(request.frame),int(request.revision),request.view)

func finish_recovery_preview(folder: String,digest: String,at: int,revision: int,view: Dictionary) -> void:
	if local_wind_active():return
	if not renderer.begin_native_readback():return
	recovery_native_requests.append({"folder":folder,"digest":digest,"at":at,"revision":revision,"view":view,"wind_generation":local_wind_generation})
	if not renderer.native_frame_ready.is_connected(complete_recovery_previews):renderer.native_frame_ready.connect(complete_recovery_previews,CONNECT_ONE_SHOT)

func complete_recovery_previews() -> void:
	var requests: Array=recovery_native_requests;recovery_native_requests=[]
	for request in requests:complete_recovery_preview(request.folder,request.digest,request.at,request.revision,request.view,int(request.wind_generation))

func complete_recovery_preview(folder: String,digest: String,at: int,revision: int,view: Dictionary,wind_generation:=-1) -> void:
	var current: bool=is_inside_tree() and renderer.native_view_available() and folder==recovery_root.path_join(recovery_session) and recovery_revision==revision and frame==at and renderer.view_state()==view
	current=current and not (playing or exporting or drawing or navigating or pose_editor.dragging or physics_editor.is_running() or has_dialog(self))
	current=current and not local_wind_active()
	# Queued production requests always carry their start epoch. The five-argument
	# direct endpoint stays compatible with existing focused callers/tests.
	current=current and (wind_generation<0 or wind_generation==local_wind_generation)
	current=current and not (recovery_writer.busy() or recovery_preview.busy())
	# Release even a detached/stale request, without reading obsolete GPU pixels.
	var image: Image=renderer.finish_native_readback(current)
	if not current or image==null:return
	var started:=Time.get_ticks_usec()
	var overlays: Array=[]
	if canvas.sequence_overlay:overlays.append(canvas.sequence_overlay.get_image().duplicate())
	for layer in layers:
		if not layer.visible:continue
		var cel:=Drawing.cel_at(layer,at)
		if cel.is_empty():continue
		var pixels:=Drawing.read_image(cel)
		if pixels.has("error"):recovery_status.text="Recovery saved; preview unavailable";return
		var copied: Image=pixels.image.duplicate();copied.set_meta("studio_layer_opacity",float(layer.get("opacity",1.0)));overlays.append(copied)
	var preview_error: String=recovery_preview.start(folder,digest,image,overlays)
	last_recovery_preview_capture_ms=(Time.get_ticks_usec()-started)/1000.0
	if not preview_error.is_empty():recovery_status.text="Recovery saved; preview unavailable"

func poll_recovery_preview() -> void:
	poll_recovery_checkpoint()
	var result: Dictionary=recovery_preview.poll()
	if result.is_empty():return
	recovery_preview_result=result
	last_recovery_preview_worker_ms=result.worker_ms
	last_recovery_preview_ms=last_recovery_preview_capture_ms+last_recovery_preview_worker_ms
	if result.folder==recovery_root.path_join(recovery_session) and not result.error.is_empty():recovery_status.text="Recovery saved; preview unavailable"

func _exit_tree() -> void:
	Drawing.opacity_cache.clear()
	# Join only at teardown; ordinary processing polls completed work without waiting.
	var completed: Dictionary=recovery_writer.finish()
	if not completed.is_empty() and completed.error.is_empty():
		var request: Dictionary=completed.request
		if request.root==recovery_root and request.session==recovery_session and request.generation!=recovery_schedule_generation:Recovery.resolve(completed.folder)
	recovery_preview.finish()

func show_recovery(history_view := false) -> void:
	if exporting: return
	stop()
	finish_stroke()
	release_mouse()
	# Review our own sessions too, with actual checkpoint times; other live apps stay hidden.
	var entries := Recovery.candidates(recovery_root,"",true,history_view)
	if not history_view:
		var counts:={};var recent: Array=[]
		for entry in entries:
			var count: int=counts.get(entry.folder,0)
			if count<2:recent.append(entry)
			counts[entry.folder]=count+1
		entries=recent
	var dialog := AcceptDialog.new()
	dialog.title = "Recovery History" if history_view else "Recover work"
	dialog.exclusive=false
	dialog.ok_button_text = "Restore as unsaved copy"
	dialog.dialog_hide_on_ok = false
	dialog.add_cancel_button("Later")
	add_child(dialog)
	var box := VBoxContainer.new()
	dialog.add_child(box)
	label(box, "Recovery keeps your manual project intact. Restore, then choose Save as.")
	var row:=HBoxContainer.new();box.add_child(row)
	var list := ItemList.new()
	list.name="RecoveryHistoryList" if history_view else "RecoveryChoices"
	list.custom_minimum_size = Vector2(550 if history_view else 370,260 if history_view else 220)
	row.add_child(list)
	var preview: TextureRect
	var details: Label
	if not entries.is_empty():
		var side:=VBoxContainer.new();row.add_child(side)
		preview=TextureRect.new();preview.name="RecoveryHistoryPreview" if history_view else "RecoveryChoicePreview";preview.custom_minimum_size=Vector2(256,144) if history_view else Vector2(192,108);preview.expand_mode=TextureRect.EXPAND_IGNORE_SIZE;preview.stretch_mode=TextureRect.STRETCH_KEEP_ASPECT_CENTERED;side.add_child(preview)
		details=label(side,"");details.custom_minimum_size.x=preview.custom_minimum_size.x
	for entry in entries:
		var age := maxi(0, int((Time.get_unix_time_from_system() - entry.saved_at) / 60))
		var stamp:=Time.get_datetime_string_from_unix_time(int(entry.saved_at)).replace("T"," ")+" UTC"
		var time_label:=stamp if history_view else ("%dm ago" % age if age>0 else "Just now")
		list.add_item(("Untitled" if entry.origin.is_empty() else entry.origin.get_file())+" • "+time_label+" • frame %d" % entry.get("frame",0))
	if preview:
		var update_preview:=func(index):
			var entry: Dictionary=entries[index];var image:=RecoveryJournal.preview(entry.folder,entry.get("preview",""))
			preview.texture=ImageTexture.create_from_image(image) if image else null
			details.text="Frame %d\n" % entry.get("frame",0)
			if history_view:details.text+="Revision %d\n" % entry.get("revision",0)
			details.text+= "Scene and drawing preview" if image else "Preview unavailable.\nRestore is still available."
		list.item_selected.connect(update_preview)
		if not entries.is_empty():update_preview.call(0)
	if not entries.is_empty(): list.select(0)
	else: label(box, "No pending checkpoints. Advanced > Recovery can open a project's saved backup.")
	dialog.get_ok_button().disabled = entries.is_empty()
	dialog.confirmed.connect(func():
		var selected := list.get_selected_items()
		if selected.is_empty(): return
		var entry: Dictionary = entries[selected[0]]
		dialog.queue_free()
		dialog.hide()
		request_recovery(entry))
	var dismiss := dialog.add_button("Dismiss session", true, "dismiss")
	dismiss.tooltip_text = "Hide this session's retained checkpoints; keep their files in the recovery cache."
	dismiss.disabled = entries.is_empty()
	dialog.custom_action.connect(func(action):
		if action != "dismiss" or list.get_selected_items().is_empty(): return
		var error := Recovery.resolve(entries[list.get_selected_items()[0]].folder)
		message("Checkpoint dismissed; files retained in recovery cache." if error.is_empty() else error)
		dialog.queue_free())
	dialog.canceled.connect(dialog.queue_free)
	dialog.popup_centered()

func request_recovery(entry: Dictionary) -> void:
	if dirty: confirm_action("Replace the current unsaved edits with this recovery copy?", func(): restore_checkpoint(entry))
	else: restore_checkpoint(entry)

func restore_checkpoint(entry: Dictionary,report_error := true) -> bool:
	if not open_project(entry.folder, entry.get("manifest", "project.json"),report_error): return false
	if entry.get("recovery", true): recovered_from = entry.folder
	project_folder = ""
	changed()
	var lesson_notice := ""
	if tutorials and entry.get("recovery",true):
		var metadata := Recovery.read_json(str(entry.folder).path_join(str(entry.get("manifest","project.json"))))
		var recovery = metadata.get("editor",{}).get("recovery",{}) if metadata.get("editor",{}) is Dictionary else {}
		lesson_notice=tutorials.restore_recovery_context(recovery.get("lesson",{}) if recovery is Dictionary else {})
	message("Recovered as an unsaved copy. Use Save to choose a .has file; the old manual save is untouched."+(" "+lesson_notice if not lesson_notice.is_empty() else ""))
	return true

func recover_latest(expected_session: String,expected_revision: int) -> void:
	# Deferred startup must never replace work begun since New was initialized.
	var result:={"restored":false,"attempts":[],"cancelled":false}
	if recovery_session!=expected_session or recovery_revision!=expected_revision or dirty or playing or exporting or drawing or navigating or has_dialog(self):
		result.cancelled=true
	else:
		for entry in Recovery.candidates(recovery_root,recovery_session):
			var restored:=restore_checkpoint(entry,false)
			result.attempts.append({"folder":entry.folder,"manifest":entry.manifest,"restored":restored,"error":open_project_error})
			if restored:
				result.restored=true
				result["checkpoint"]=entry.duplicate(true)
				result["lesson_restored"]=tutorials.active if tutorials else false
				# Keep any nonmodal lesson-context diagnostic from restore_checkpoint.
				message(status.text+" Use Recover for older copies.")
				break
		if not result.restored and not result.attempts.is_empty():message("No valid recovery checkpoint could be opened. Retained copies are available in Recover; your manual saves are untouched.")
		if not Recovery.discovery_warning.is_empty():
			result["warning"]=Recovery.discovery_warning
			message(Recovery.discovery_warning)
	startup_recovery_result=result
	if home and not result.restored and not result.cancelled and not dirty:
		home.open_home()
		if not result.attempts.is_empty() or not Recovery.discovery_warning.is_empty():home.feedback(status.text)
	startup_recovery_finished.emit(result.duplicate(true))

func preview_seconds() -> float:
	if audio_clock and audio_player.playing:
		var time := audio_player.get_playback_position() + AudioServer.get_time_since_last_mix() - audio_latency
		last_audio_time = maxf(last_audio_time, time)
		return last_audio_time
	return Timeline.seconds(play_start, video) + (Time.get_ticks_usec() - play_origin) / 1000000.0

func audio_finished() -> void:
	if playing and audio_clock:
		stop()
		set_frame(video.duration_frames - 1)

func choose_audio_at_playhead() -> void:
	var at:=frame
	if at>=video.duration_frames:
		message("Move the playhead before the end of the movie to add a sound.")
		return
	choose_file("Add sound at frame %d" % at,["*.wav","*.mp3","*.ogg"],func(path):import_audio_selected(path,at))

func import_audio_dialog(path: String) -> void:
	import_audio_selected(path,frame)

func import_audio_selected(path: String,at: int) -> void:
	if path.get_extension().to_lower()=="wav":import_audio(path,at)
	else:audio_importer.begin(path,at)

func audio_document() -> Dictionary:
	return AudioTrack.document(audio_clips)

func select_audio(index: int) -> void:
	if exporting or index < 0 or index >= audio_clips.size(): return
	selected_audio = index
	refresh_audio_controls(); refresh_timeline()
	inspector_scroll.ensure_control_visible.call_deferred(audio_mute)

func retime_audio(id: String, start: int, previous: int) -> void:
	if exporting or start < 0 or start >= video.duration_frames: return
	for index in range(audio_clips.size()):
		if audio_clips[index].id != id: continue
		if audio_clips[index].start_frame != previous or start == previous: return
		stop()
		var before := audio_document().duplicate(true)
		selected_audio = index; audio_clip.start_frame = start
		commit_audio(before)
		message("Sound clip moved. Undo restores its previous timing.")
		return

func import_audio(path: String,start_frame:=0) -> String:
	if exporting: return "Cannot import during export."
	if start_frame<0 or start_frame>=video.duration_frames:
		var error:="Choose a frame before the end of the movie for this sound."
		message(error);return error
	if sequence_editor.used("audio")>=AudioTrack.MAX_CLIPS:message("This project and its sequences already have16 sound clips.");return "Audio clip limit reached."
	stop()
	var decoded := AudioTrack.read_wav(path)
	if decoded.has("error"): message(decoded.error); return decoded.error
	return append_audio(decoded,start_frame)

func append_audio(decoded: Dictionary,start_frame: int) -> String:
	if exporting:return "Cannot import during export."
	if start_frame<0 or start_frame>=video.duration_frames:return "Choose a frame before the end of the movie for this sound."
	if sequence_editor.used("audio")>=AudioTrack.MAX_CLIPS:return "Project and sequence audio clip limit reached."
	stop()
	var candidate := AudioTrack.make_clip(decoded)
	candidate.start_frame=start_frame
	var proposed := audio_clips.duplicate()
	proposed.append(candidate)
	var mixed: Dictionary=sequence_editor.mix(AudioTrack.document(proposed),video)
	if mixed.has("error"): message(mixed.error); return mixed.error
	var before := audio_document().duplicate(true)
	var before_selection: String=audio_clip.get("id","")
	audio_clips = proposed
	selected_audio = audio_clips.size()-1
	commit_audio(before,before_selection)
	inspector_scroll.ensure_control_visible.call_deferred(audio_mute)
	message("Sound added at frame %d. Drag its timeline block to change the timing." % start_frame)
	return ""

func rebuild_audio() -> void:
	refresh_workspace()
	stop()
	audio_mix = {}
	var mixed: Dictionary=sequence_editor.mix(audio_document(),video)
	if mixed.has("error"):message(mixed.error)
	else:audio_mix=mixed
	refresh_audio_controls()
	refresh_timeline()

func refresh_audio_controls() -> void:
	audio_start.max_value = video.duration_frames - 1
	audio_choice.clear()
	for clip in audio_clips: audio_choice.add_item(clip.source.name.left(40))
	audio_choice.visible = audio_clips.size() > 1
	if not audio_clips.is_empty():
		selected_audio = clampi(selected_audio,0,audio_clips.size()-1)
		audio_choice.select(selected_audio)
	if audio_clip.is_empty():
		audio_info.text = "No audio clip"
		audio_mute.set_pressed_no_signal(false)
		audio_solo.set_pressed_no_signal(false)
		audio_start.value = 0
		audio_trim.value = 0
		audio_gain.value = 0
	else:
		audio_info.text = "%s\n%.2f s • %d Hz • %s" % [audio_clip.source.name.left(35), float(AudioTrack.source_end(audio_clip)-audio_clip.source_in_sample) / audio_clip.source.rate, audio_clip.source.rate, "stereo" if audio_clip.source.channels == 2 else "mono"]
		audio_start.value = audio_clip.start_frame
		audio_trim.value = float(audio_clip.source_in_sample) * 1000 / audio_clip.source.rate
		audio_gain.value = audio_clip.gain_db
		audio_mute.set_pressed_no_signal(audio_clip.muted)
		audio_solo.set_pressed_no_signal(audio_clip.get("solo",false))
		if audio_mix.get("clipped_samples",0) > 0: audio_info.text += "\nSounds overlap too loudly. Lower clip gain in Advanced."

func commit_audio(before: Dictionary, before_selection: String="") -> void:
	var selected: String=audio_clip.get("id","")
	push_history({"type": "audio", "before": before, "after": audio_document().duplicate(true), "selected_before":before_selection if not before_selection.is_empty() else selected,"selected_after":selected,"bytes": AudioTrack.memory(before) + AudioTrack.memory(audio_document())})
	rebuild_audio()
	changed()

func apply_audio_settings() -> void:
	if exporting or audio_clip.is_empty(): return
	stop()
	var trimmed := roundi(audio_trim.value / 1000 * audio_clip.source.rate)
	if trimmed >= AudioTrack.source_end(audio_clip):
		message("Source trim must be before the sound's end. Previous settings preserved.")
		return
	var before := audio_document().duplicate(true)
	audio_clip.start_frame = int(audio_start.value)
	audio_clip.source_in_sample = trimmed
	audio_clip.gain_db = float(audio_gain.value)
	commit_audio(before)
	message("Audio timing/gain applied; preview and export updated.")

func remove_audio() -> void:
	if exporting or audio_clip.is_empty(): return
	var before := audio_document().duplicate(true)
	var selected: String=audio_clip.id
	audio_clips.remove_at(selected_audio)
	selected_audio = maxi(0,mini(selected_audio,audio_clips.size()-1))
	commit_audio(before,selected)
