extends Control
signal movie_export_finished(folder: String,success: bool)
signal startup_recovery_finished(result: Dictionary)
const Timeline = preload("res://src/timeline.gd")
const Drawing = preload("res://src/drawing.gd")
const FillEditor=preload("res://src/fill_editor.gd")
const OnionEditor=preload("res://src/onion_editor.gd")
const LayerEditor=preload("res://src/layer_editor.gd")
const ColorSampler=preload("res://src/color_sampler.gd")
const SceneIO = preload("res://src/scene3d.gd")
const Renderer = preload("res://src/renderer.gd")
const Storage = preload("res://src/storage.gd")
const Encoder = preload("res://src/encoder.gd")
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
const PoseEditor = preload("res://src/pose_editor.gd")
const PhysicsEditor=preload("res://src/physics_editor.gd")
const ImportPlacement = preload("res://src/import_placement.gd")
const SourceShape=preload("res://src/source_shape.gd")
const ImportActions = preload("res://src/import_actions.gd")
const SourceImport = preload("res://src/source_import.gd")
const SourceBrowser = preload("res://src/source_browser.gd")
const HasProject = preload("res://src/has_project.gd")
const WorldSelection = preload("res://src/world_selection.gd")
const WorldDocument = preload("res://src/world_document.gd")
var world_selection
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
var overlay_dirty := true
var exporting := false
var cancel_export := false
var encoder: RefCounted
var renderer: Node
var canvas: Control
var cel_timing: Node
var timeline_navigation: Node
var timeline_ruler: Control
var timeline: Control
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
var encoder_path: LineEdit
var encoder_quality: OptionButton
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
var audio_choice: OptionButton
var advanced_mode := false
var advanced_toggle: Button
var advanced_controls: Array[Control] = []
var drawing_section: VBoxContainer
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
var last_recovery_ms := 0.0
var last_recovery_preview_ms := 0.0
var last_recovery_preview_capture_ms := 0.0
var last_recovery_preview_worker_ms := 0.0
var recovery_preview=RecoveryPreview.new()
var recovery_preview_result: Dictionary={}
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
var source_import: Node
var source_browser: Node
var clip_editor: Node
var import_actions: Node
var height_review: Node
var map_calibration: Node
var height_choice: CheckBox
var project_options: AcceptDialog
var project_timing: Node
var workspace_layout: Node
var home
var recent_path:=""
var tutorials
var visibility_fade: SpinBox
const DISPLAY_PREFS := "user://display.cfg"
var display_prefs_path:=DISPLAY_PREFS
const UI_PERCENT := [100,125,150,175]
var display_dialog: AcceptDialog
var keyboard_shortcuts: Node
var camera_transform_editor: Node

func initialize_display() -> void:
	var prefs := ConfigFile.new()
	var screen := DisplayServer.screen_get_size().min(get_window().size)
	if OS.has_feature("web"):
		screen = Vector2i(JavaScriptBridge.eval("window.innerWidth"), JavaScriptBridge.eval("window.innerHeight"))
		resize_web_display()
		get_window().size_changed.connect(resize_web_display)
	var percent := 150 if screen.x >= 2400 and screen.y >= 1300 else 125 if screen.x >= 1800 and screen.y >= 1000 else 100
	if prefs.load(display_prefs_path)==OK:
		var saved = prefs.get_value("display","percent",percent)
		if saved in UI_PERCENT: percent = int(saved)
		var scheme=prefs.get_value("navigation","scheme","fly")
		if scheme in ["fly","orbit"]:navigation_scheme=scheme
	get_window().content_scale_factor = percent / 100.0

func save_display_preference(section_name: String,key_name: String,value) -> void:
	var prefs:=ConfigFile.new();prefs.load(display_prefs_path)
	prefs.set_value(section_name,key_name,value)
	if prefs.save(display_prefs_path)!=OK:message("Could not save the interface preference for next time.")

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
	button(box,"Toggle fullscreen",func():
		var full := DisplayServer.window_get_mode() in [DisplayServer.WINDOW_MODE_FULLSCREEN,DisplayServer.WINDOW_MODE_EXCLUSIVE_FULLSCREEN]
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED if full else DisplayServer.WINDOW_MODE_FULLSCREEN))
	button(box,"Keyboard shortcuts…",keyboard_shortcuts.open)
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
	DisplayServer.set_icon(StudioTheme.icon("scene").get_image())
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
	clip_editor=ClipEditor.new();clip_editor.app=self;add_child(clip_editor)
	particle_editor=preload("res://src/particle_editor.gd").new();particle_editor.app=self;add_child(particle_editor)
	build_ui()
	mmd_pose_importer=preload("res://src/mmd_pose_import.gd").new();add_child(mmd_pose_importer);mmd_pose_importer.setup(self)
	audio_importer=preload("res://src/audio_import.gd").new();audio_importer.app=self;add_child(audio_importer)
	audio_trim_editor=preload("res://src/audio_trim_editor.gd").new();audio_trim_editor.app=self;add_child(audio_trim_editor)
	audio_fade_editor=preload("res://src/audio_fade_editor.gd").new();audio_fade_editor.app=self;add_child(audio_fade_editor)
	project_timing=preload("res://src/project_timing.gd").new();project_timing.app=self;add_child(project_timing)
	timeline.audio_trim_context=audio_trim_editor.drag_context
	fill_editor=FillEditor.new();fill_editor.app=self;add_child(fill_editor);fill_editor.setup(drawing_section)
	onion_editor=OnionEditor.new();onion_editor.app=self;add_child(onion_editor);onion_editor.setup(drawing_section)
	reference_sheet=preload("res://src/reference_sheet.gd").new();reference_sheet.app=self;add_child(reference_sheet);reference_sheet.setup(drawing_section)
	layer_editor=LayerEditor.new();layer_editor.app=self;add_child(layer_editor);layer_editor.setup(drawing_section)
	cel_timing=preload("res://src/cel_timing_editor.gd").new();cel_timing.app=self;add_child(cel_timing);timeline.cel_context_provider=cel_timing.begin;timeline.cel_moved.connect(cel_timing.commit);timeline.cel_resized.connect(cel_timing.resize)
	raster_importer=preload("res://src/krita_import.gd").new();add_child(raster_importer);raster_importer.setup(self)
	video_importer=preload("res://src/video_import.gd").new();add_child(video_importer);video_importer.setup(self)
	color_sampler=ColorSampler.new();color_sampler.app=self;add_child(color_sampler);color_sampler.setup(drawing_section)
	palette_editor=preload("res://src/palette_editor.gd").new();palette_editor.app=self;add_child(palette_editor);palette_editor.setup(drawing_section)
	drawing_selection_editor=preload("res://src/drawing_selection_editor.gd").new();drawing_selection_editor.app=self;add_child(drawing_selection_editor);drawing_selection_editor.setup(drawing_section)
	camera_transform_editor=preload("res://src/camera_transform_editor.gd").new();add_child(camera_transform_editor);camera_transform_editor.setup(self)
	sequence_editor=preload("res://src/sequence_editor.gd").new();add_child(sequence_editor);sequence_editor.setup(self)
	keyboard_shortcuts.refresh_labels()
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

func nav_button(parent: Node, text: String, kind: String, action: Callable, hint := "") -> Button:
	var control := icon_button(parent, text, kind, action, hint)
	control.custom_minimum_size = Vector2(86, 66)
	control.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
	control.vertical_icon_alignment = VERTICAL_ALIGNMENT_TOP
	control.add_theme_constant_override("icon_max_width", 32)
	control.add_theme_font_size_override("font_size", 13)
	var normal := StyleBoxFlat.new()
	normal.bg_color = Color.TRANSPARENT
	normal.set_content_margin_all(6)
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

func advanced_spin(parent: Node, text: String, low: float, high: float, value: float) -> SpinBox:
	var row := VBoxContainer.new()
	parent.add_child(row)
	advanced(row)
	return spin(row, text, low, high, value)

func section(parent: Node, title: String, kind: String) -> VBoxContainer:
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

func set_advanced(enabled: bool) -> void:
	# Presentation only: never reset project values, shot/navigation, transport or undo.
	advanced_mode = enabled
	advanced_toggle.set_pressed_no_signal(enabled)
	if pose_editor:pose_editor.refresh_labels()
	if timeline:timeline.set_label_mode(enabled)
	refresh_workspace()

func refresh_workspace() -> void:
	canvas.scene_navigation = mode.selected == 1
	canvas.tooltip_text = "Click: select • Ctrl + left: free fly • Left drag: move • Right click: menu/deselect • Right drag: POV • Middle: dolly • Esc: release" if mode.selected == 1 else "Wheel: zoom • Middle drag: pan • %s: play/pause" % keyboard_shortcuts.label_for("play")
	if mode.selected == 2: canvas.tooltip_text = "Hold Alt: reveal bones • Click joint; drag RGB handles • Edits auto-key • Right click: object menu / deselect • Esc: cancel"
	if mode.selected in [1,2] and navigation_scheme=="orbit":
		canvas.tooltip_text=canvas.tooltip_text.replace("Ctrl + left: free fly","Ctrl + left: orbit")+" • Orbit: Ctrl+left • Pan: Ctrl+right • Dolly: Ctrl+wheel"
	for control in advanced_controls: control.visible = advanced_mode
	drawing_section.get_parent().visible = advanced_mode or mode.selected == 0
	camera_section.get_parent().visible = advanced_mode or mode.selected == 1
	pose_editor.panel.get_parent().visible = advanced_mode or mode.selected == 2
	audio_section.get_parent().visible = advanced_mode or not audio_clip.is_empty()
	workspace_label.text = "Advanced workspace" if advanced_mode else "Simple workspace"
	inspector_scroll.scroll_vertical = 0
	if pose_editor:pose_editor.refresh_values()

func build_ui() -> void:
	theme = StudioTheme.make_theme()
	get_window().theme=theme
	var back := TextureRect.new()
	back.texture = StudioTheme.svg_texture('<defs><linearGradient id="back" x2="0" y2="1"><stop stop-color="#f4f7fb"/><stop offset="1" stop-color="#dce5ee"/></linearGradient></defs><rect width="64" height="64" fill="url(#back)"/>', 64, 64)
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
	header_style.texture = StudioTheme.svg_texture('<defs><linearGradient id="header" x2="0" y2="1"><stop stop-color="#b6e1ff"/><stop offset="0.35" stop-color="#78b5e3"/><stop offset="1" stop-color="#3979b1"/></linearGradient></defs><rect width="64" height="64" fill="url(#header)"/>', 64, 64)
	header_style.content_margin_left = 14
	header_style.content_margin_right = 14
	header_style.content_margin_top = 10
	header_style.content_margin_bottom = 6
	title_panel.add_theme_stylebox_override("panel", header_style)
	shell.add_child(title_panel)
	var header_column := VBoxContainer.new()
	header_column.add_theme_constant_override("separation", 4)
	title_panel.add_child(header_column)
	var title_row := HBoxContainer.new()
	header_column.add_child(title_row)
	var title := label(title_row, "Hybrid Animation Studio")
	title.add_theme_color_override("font_color", Color("102e4d"))
	title.add_theme_font_size_override("font_size", 20)
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	icon_button(title_row,"Home","scene",func():home.open_home(),"New, Open and recent projects; your current scene stays intact")
	workspace_label = label(title_row, "Simple workspace")
	workspace_label.add_theme_color_override("font_color", Color("102e4d"))
	advanced_toggle = button(title_row, "Advanced", func(): set_advanced(advanced_toggle.button_pressed))
	advanced_toggle.toggle_mode = true
	advanced_toggle.tooltip_text = "Show detailed controls. Your scene, drawings, audio and settings keep working in either mode."
	var toolbar := HBoxContainer.new()
	header_column.add_child(toolbar)
	nav_button(toolbar, "New", "scene", new_dialog, "Start an empty world • unsaved edits are protected by a confirmation")
	nav_button(toolbar, "Open", "folder", open_dialog, "Open an editable project")
	keyboard_shortcuts.decorate(nav_button(toolbar, "Save", "save", save),"save","Save project")
	nav_button(toolbar, "Recover", "undo", show_recovery, "Review retained recovery checkpoints")
	advanced(nav_button(toolbar, "Save as…", "save", save_as))
	advanced(nav_button(toolbar, "Open folder…", "open", func():
		var action := func(): choose_directory("Open legacy project directory", open_project)
		if dirty: confirm_action("Discard unsaved edits and open another project?", action)
		else: action.call()))
	advanced(nav_button(toolbar, "Sample room", "scene", demo_dialog, "Open the original camera/drawing example as a new unsaved project"))
	nav_button(toolbar, "Add scene", "scene", func(): choose_file("Import 3D environment", ["*.glb", "*.gltf", "*.fbx", "*.obj", "*.pmd", "*.pmx", "*.bsp", "*.gma", "*.bin"], load_scene, source_import.default_browse_dir()), "Add a 3D environment: GLB, glTF, FBX, OBJ, MMD or an installed Source map")
	nav_button(toolbar, "Add model", "scene", pose_editor.import_dialog, "Add a poseable standard GLB model beside the environment")
	nav_button(toolbar, "Installed", "folder", func(): source_browser.open(), "Browse installed GMod models/maps, Workshop addons and dependency mounts")
	nav_button(toolbar, "Add audio", "audio", choose_audio_at_playhead, "Add a WAV, MP3 or Ogg sound starting at the playhead")
	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	toolbar.add_child(spacer)
	nav_button(toolbar, "Export movie", "export", export_dialog, "Export MP4 beside your saved HAS project, with a recoverable PNG frame sequence")
	button(title_row,"Options",show_project_options).tooltip_text="Project settings, including visibility fades. Saved with this HAS project."
	button(title_row,"Settings",show_display_settings).tooltip_text="Interface scale and fullscreen. Advanced also offers orbit camera controls."
	nav_button(toolbar, "About", "help", show_notices, "Credits and open source notices")
	var margin := MarginContainer.new()
	margin.size_flags_vertical = Control.SIZE_EXPAND_FILL
	for side in ["left", "right", "top", "bottom"]:
		margin.add_theme_constant_override("margin_" + side, 10)
	shell.add_child(margin)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 8)
	margin.add_child(column)
	var middle := HBoxContainer.new()
	middle.size_flags_vertical = Control.SIZE_EXPAND_FILL
	column.add_child(middle)
	var hierarchy := VBoxContainer.new()
	hierarchy.custom_minimum_size.x = 156
	middle.add_child(hierarchy)
	world_selection.setup(hierarchy)
	var center := VBoxContainer.new()
	center.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	middle.add_child(center)
	var view_toolbar := HBoxContainer.new()
	center.add_child(view_toolbar)
	mode = OptionButton.new()
	mode.add_icon_item(StudioTheme.icon("draw"), "Draw")
	mode.add_icon_item(StudioTheme.icon("camera"), "Scene / camera")
	mode.add_icon_item(StudioTheme.icon("scene"), "Pose model")
	mode.add_theme_constant_override("icon_max_width", 22)
	mode.item_selected.connect(change_mode)
	mode.tooltip_text = "Draw on independent layers, or move the temporary 3D camera."
	view_toolbar.add_child(mode)
	lighting_choice=OptionButton.new()
	for lighting_title in ["Unshaded","Lit","Studio light"]:lighting_choice.add_item(lighting_title)
	lighting_choice.tooltip_text="Unshaded shows base colors. Lit uses imported scene lights. Studio light retains older projects' illumination."
	lighting_choice.item_selected.connect(change_lighting)
	view_toolbar.add_child(lighting_choice)
	button(view_toolbar, "Fit view", func(): canvas.zoom = 1; canvas.pan = Vector2.ZERO; canvas.queue_redraw())
	button(view_toolbar, "Frame scene", frame_3d_scene).tooltip_text = "Fit the 3D asset in the temporary editor camera; shot keys stay unchanged."
	keyboard_shortcuts.decorate(icon_button(view_toolbar, "Undo", "undo", undo),"undo","Undo")
	keyboard_shortcuts.decorate(icon_button(view_toolbar, "Redo", "redo", redo),"redo","Redo")
	var physics_toolbar:=HFlowContainer.new();center.add_child(physics_toolbar)
	physics_editor.setup(physics_toolbar)
	canvas = CanvasView.new()
	canvas.custom_minimum_size = Vector2(400, 180)
	canvas.size_flags_vertical = Control.SIZE_EXPAND_FILL
	canvas.background = renderer.viewport.get_texture()
	canvas.pointer.connect(canvas_input)
	canvas.middle_target=middle_pose_target
	canvas.middle_clicked=cycle_pose_operation
	canvas.tooltip_text = "Wheel: zoom • Middle drag: pan • Space: play/pause"
	center.add_child(canvas)
	scene_name = label(center, "")
	scene_name.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	var scroll := ScrollContainer.new()
	inspector_scroll = scroll
	scroll.custom_minimum_size.x = 276
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
	icon_button(drawing_section, "New drawing", "cel", func(): create_cel(false), "Start a blank cel at this frame; it holds until the next drawing.")
	button(drawing_section, "Copy drawing here", func(): create_cel(true)).tooltip_text = "Make an independent copy of the held drawing at this frame."
	exposure = advanced_spin(drawing_section, "Exposure length (frames)", 1, preload("res://src/extended_timing.gd").MAX_FRAMES, 48)
	advanced(button(drawing_section, "Set held cel exposure", set_exposure))
	advanced(button(drawing_section, "Delete held cel", delete_cel))
	camera_section = section(controls, "Camera", "camera")
	label(camera_section, "Ctrl + left: free camera / WASD
Left drag: move sideways / up
Right drag: adjust view direction
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
	keyboard_shortcuts.decorate(icon_button(camera_section, "Save camera key [K]", "key", key_dialog),"camera","Store this view at the current frame. Replacing an existing key asks first.","Save camera key")
	advanced(button(camera_section, "Delete key at this frame", delete_key))
	label(camera_section, "Move freely, then save a key.
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
	button(audio_section,"Shorten sound…",func():audio_trim_editor.open())
	button(audio_section,"Fade sound…",func():audio_fade_editor.open())
	button(audio_section, "Remove audio clip", remove_audio)
	var encoder_section := section(controls, "Movie encoder", "export")
	advanced(encoder_section.get_parent())
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
	button(transport, "|◀", func(): stop(); set_frame(0)).tooltip_text = "First frame • Home"
	button(transport, "◀", func(): step(-1)).tooltip_text = "Previous frame • Left arrow"
	play_button = icon_button(transport, "Play", "play", toggle_play, "Play / pause • Space")
	button(transport, "▶|", func(): step(1)).tooltip_text = "Next frame • Right arrow"
	frame_box = spin(transport, "Frame", 0, video.duration_frames, 0)
	frame_box.value_changed.connect(func(value): stop(); set_frame(int(value)))
	transport_info = label(transport, "")
	transport_info.text_overrun_behavior=TextServer.OVERRUN_TRIM_ELLIPSIS
	transport_info.size_flags_horizontal=Control.SIZE_EXPAND_FILL
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
	timeline_navigation=preload("res://src/timeline_navigation.gd").new();timeline_navigation.app=self;add_child(timeline_navigation);timeline_navigation.setup(ruler_holder,timeline,timeline_ruler)
	timeline.resized.connect(func():timeline_ruler.size=Vector2(timeline.size.x,52);timeline_ruler.queue_redraw())
	var timeline_scroll:=ScrollContainer.new()
	timeline_scroll.name="TimelineScroll";timeline_scroll.custom_minimum_size.y=144
	timeline_scroll.horizontal_scroll_mode=ScrollContainer.SCROLL_MODE_DISABLED
	timeline_scroll.vertical_scroll_mode=ScrollContainer.SCROLL_MODE_RESERVE
	column.add_child(timeline_scroll);timeline_scroll.add_child(timeline)
	debug_label = label(column, "")
	advanced(debug_label)
	var footer := HBoxContainer.new()
	column.add_child(footer)
	status = label(footer, "")
	status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
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
	cancel_button = button(footer, "Cancel export", func(): cancel_export = true; if encoder: encoder.cancel())
	cancel_button.visible = false
	set_advanced(false)
	workspace_layout=preload("res://src/workspace_layout.gd").new();add_child(workspace_layout)
	workspace_layout.setup(self,column,middle,hierarchy,scroll,transport,ruler_holder,timeline_scroll)
	var fit_panels := func():
		var compact := get_viewport_rect().size.y < 800
		world_selection.tree.custom_minimum_size.y = 80 if compact else 150
		timeline_scroll.custom_minimum_size.y = 84 if compact else 144
		canvas.custom_minimum_size.y = 140 if compact else 180
	resized.connect(fit_panels)
	fit_panels.call()

func default_ffmpeg() -> String:
	var setting := OS.get_environment("HYBRID_FFMPEG")
	if not setting.is_empty(): return setting
	var common := "C:/Program Files/ffmpeg/bin/ffmpeg.exe"
	return common if FileAccess.file_exists(common) else "ffmpeg"

func message(text: String) -> void:
	status.text = text
	if home and home.visible and home.notice:home.feedback(text)

func changed() -> void:
	if drawing_selection_editor:drawing_selection_editor.cancel()
	recovery_revision += 1
	dirty = true
	overlay_dirty = true
	if sequence_editor and not sequence_editor.graph.is_empty():sequence_editor.sync_current()
	refresh_timeline()

func refresh_timeline() -> void:
	timeline_ruler.keys=keys;timeline_ruler.frame=frame;timeline_ruler.duration=video.duration_frames;timeline_ruler.queue_redraw()
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

func set_frame(value: int) -> void:
	if exporting: return
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
	transport_info.text = "%s fps  •  %.2f seconds  •  Frames 0–%d; key %d is the end boundary" % [preload("res://src/video_timing.gd").label(video.fps_num,video.fps_den), Timeline.seconds(video.duration_frames, video), video.duration_frames - 1, video.duration_frames]
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
		var content:=VBoxContainer.new();project_options.add_child(content)
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
	if index == 1: message("Editor camera is temporary. Insert a key explicitly; switching to Draw restores the shot.")
	elif index == 2: message("Pose model: click a joint, then drag colored handles. Completed edits auto-key by default. Camera keys and drawing remain separate.")
	else: message("Drawing edits only the active cel. Held frames share this drawing; duplicate to make a variation.")

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

func _process(delta: float) -> void:
	poll_recovery_preview()
	if recovery_checkpoint_requested and not recovery_preview.busy():autosave_tick(true)
	pose_editor.update_gizmo()
	play_button.text = "Pause" if playing else "Play"
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
		renderer.camera.position += renderer.camera.basis * motion.limit_length() * delta * (8 if Input.is_key_pressed(KEY_SHIFT) else 3)
	if overlay_dirty:
		var start := Time.get_ticks_usec()
		var overlay := Drawing.composite(layers, frame, video.width, video.height)
		if canvas.overlay == null: canvas.overlay = ImageTexture.create_from_image(overlay)
		else: canvas.overlay.update(overlay)
		elapsed_overlay_ms = (Time.get_ticks_usec() - start) / 1000.0
		canvas.queue_redraw()
		overlay_dirty = false
	var cel_count := 0
	for layer in layers: cel_count += layer.cels.size()
	debug_label.text = "Frame %03d / [0,%d) | %.3f s | %d/%d fps | GLB %s | %d cels | overlay %.2f ms | %s | %s" % [frame, video.duration_frames, Timeline.seconds(frame, video), video.fps_num, video.fps_den, source.get_file().left(12), cel_count, elapsed_overlay_ms, "audio clock %.3fs" % last_audio_time if audio_clock else ("silent/device fallback" if not audio_clip.is_empty() and playing else "audio ready" if not audio_clip.is_empty() else "no audio"), "unsaved" if dirty else "saved"]

func canvas_input(event: InputEvent, point: Vector2) -> void:
	if home and home.visible:return
	if exporting or playing: return
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
				if point.distance_to(joint.point) < 10.0*1920/maxf(1,canvas.image_rect().size.x): joint_hit=true; break
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
			stroke_image = cel.get("image",null)
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
		create_cel(false,false)
		var cel:=Drawing.cel_at(layers[active_layer],frame)
		if cel.is_empty():finish_stroke();return
		stroke_image=cel.image
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
	var drawing_command: bool=command.type in ["pixels","cels","cel_timing","cel_exposure","layer_properties","layers"]
	if command.type in ["cels","layer_properties"]:
		var live_layer: Dictionary=cel_timing.layer_by_id(str(command.layer.get("id","")))
		if live_layer.is_empty():message("Drawing history layer is missing.");return false
		command.layer=live_layer
	if not drawing_command:physics_editor.clear();physics_editor.clear_previews()
	var view: Dictionary=renderer.view_state()
	if command.type == "pixels":
		var damage:=Rect2i()
		for pos in command[side]:
			var image: Image = command[side][pos]
			command.image.blit_rect(image, Rect2i(Vector2i.ZERO, image.get_size()), pos)
			var tile:=Rect2i(pos,image.get_size());damage=damage.merge(tile) if damage.has_area() else tile
		Drawing.touch(command.image,damage)
	elif command.type in ["cel_timing","cel_exposure"]:
		var error: String=cel_timing.apply_command(command,side)
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

func create_cel(duplicate: bool,finish_current: bool=true) -> void:
	if exporting or frame >= video.duration_frames: return
	if finish_current:finish_stroke()
	var count := 0
	for layer in layers: count += layer.cels.size()
	if sequence_editor:count=sequence_editor.used("cels")
	if count >= 32: message("Prototype memory limit: 32 full-HD cels."); return
	var layer: Dictionary = layers[active_layer]
	for existing in layer.cels:
		if existing.start == frame:
			message("A cel already starts here. Move to another frame or delete this cel first.")
			return
	var before: Array = layer.cels.duplicate(true)
	var current := Drawing.cel_at(layer, frame)
	var image: Image = current.image.duplicate() if duplicate and not current.is_empty() else Drawing.blank(video.width, video.height)
	Drawing.insert(layer, frame, video.duration_frames, image)
	push_history({"type": "cels", "layer": layer, "before": before, "after": layer.cels.duplicate(true)})
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
	push_history({"type": "cels", "layer": layer, "before": before, "after": layer.cels.duplicate(true)})
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

func camera_button(index: int, pressed: bool, ctrl := false) -> void:
	if index not in [MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT, MOUSE_BUTTON_MIDDLE]: return
	if index == MOUSE_BUTTON_LEFT: camera_free = pressed and ctrl
	if pressed and ctrl and navigation_scheme=="orbit" and index in [MOUSE_BUTTON_LEFT,MOUSE_BUTTON_RIGHT] and camera_buttons==0:
		if not orbit_control.begin(renderer.camera,orbit_pivot(),"orbit" if index==MOUSE_BUTTON_LEFT else "pan"):
			camera_free=false;message("Frame the selected object before orbiting this close.");return
	var flag := 1 << (index - 1)
	if pressed: camera_buttons |= flag
	else: camera_buttons &= ~flag
	navigating = camera_buttons != 0
	if not navigating:orbit_control.end()
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED if navigating else Input.MOUSE_MODE_VISIBLE

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

func release_mouse() -> void:
	orbit_control.end()
	if canvas:canvas.cancel_middle()
	if physics_editor:physics_editor.release_grab()
	if world_selection: world_selection.cancel_gesture(true)
	camera_free = false
	camera_buttons = 0
	navigating = false
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE

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
	if keyboard_shortcuts and keyboard_shortcuts.capture(event):get_viewport().set_input_as_handled();return
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
			if physics_editor.pointer(event,(local-rect.position)/rect.size*Vector2(1920,1080)):
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
		var point: Vector2 = (event.position - canvas.global_position - rect.position) / rect.size * Vector2(1920, 1080)
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
	if not physics_editor.freeze_all():return status.text
	pose_editor.finish_drag();finish_stroke()
	var before:=current_world();var after:=before.duplicate(true);var row:=data.duplicate(true)
	row["kind"]=kind;row["parent_id"]="";row["start_frame"]=start_frame
	if kind=="model" and not placement.is_empty():
		if renderer.world_runtime:renderer.world_runtime.evaluate(start_frame)
		var root_transform:=Transform3D(Basis(Timeline.quaternion(row.rotation_xyzw)).scaled(Vector3.ONE*float(row.scale)),Vector3.ZERO)
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
	var prepared: Dictionary=renderer.prepare_legacy(path) if sample else renderer.prepare_world(WorldDocument.empty(),48)
	if prepared.has("error"):message(prepared.error);return false
	if tutorials:tutorials.document_changing()
	reference_sheet.install_prepared({"data":{}})
	sequence_editor.clear()
	stop(); finish_stroke(); pose_editor.finish_drag(); release_mouse()
	world_selection.clear()
	if sample:renderer.install_legacy(prepared)
	else:renderer.install_world(prepared)
	pose_editor.selected = "@root"
	pose_editor.rebuild_tree()
	source = path if sample else "";last_import_id="";project_folder = ""; has_project.clear_identity()
	video = {"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":48,"visibility_fade_ms":300,"world_background":"legacy_blue" if sample else "black","lighting_mode":"studio" if sample else "unshaded"}
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
	var data := Storage.load_project(folder, manifest_name)
	if data.has("error"):
		open_project_error=data.error
		if report_error:message(open_project_error)
		return false
	var reference_candidate: Dictionary=reference_sheet.prepare_project(data.get("reference_sheet",{}))
	if reference_candidate.has("error"):
		open_project_error=reference_candidate.error
		if report_error:message(open_project_error)
		return false
	var prepared: Dictionary = renderer.prepare_world(data.world,int(data.video.duration_frames)) if data.schema_version>=4 else renderer.prepare_legacy(data.source,data.model)
	if prepared.has("error"):
		open_project_error=prepared.error
		if report_error:message(open_project_error)
		return false
	var sequence_candidate: Dictionary=sequence_editor.prepare_runtime(data.get("sequence_graph",{}),data)
	if sequence_candidate.has("error"):
		if data.schema_version>=4:prepared.runtime.dispose()
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
	if data.schema_version>=4:renderer.install_world(prepared)
	else:renderer.install_legacy(prepared)
	reference_sheet.install_prepared(reference_candidate)
	pose_editor.selected="@root";pose_editor.rebuild_tree()
	source = str(data.get("source",""));last_import_id=""
	video = data.video
	renderer.set_background(str(video.get("world_background","legacy_blue")))
	keys = data.camera_keys
	layers = data.layers
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

func export_frames(parent: String,images_only: bool,drawings_only: bool) -> String:
	if exporting: return "Export already running."
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
	for n in range(video.duration_frames):
		if cancel_export: error = "Export cancelled. PNG frames preserved."; break
		message("Rendering %d / %d • %s" % [n + 1, video.duration_frames, folder])
		var image: Image
		if images_only and drawings_only:
			image=Drawing.blank(int(video.width),int(video.height))
			if renderer.sequence_runtime:
				var nested: Image=await renderer.sequence_runtime.render(renderer.sequence_owner,n,true,true)
				if nested==null:error=renderer.sequence_runtime.last_error;break
				image.blend_rect(nested,Rect2i(0,0,int(video.width),int(video.height)),Vector2i.ZERO)
			image.blend_rect(Drawing.composite(export_layers,n,int(video.width),int(video.height)),Rect2i(0,0,int(video.width),int(video.height)),Vector2i.ZERO)
			await get_tree().process_frame
		else:image=await renderer.capture(export_keys, export_layers, n, true)
		if image==null:
			error=renderer.last_capture_error;break
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
			error = await encoder.encode(get_tree(), encoder_path.text, folder, video, mix_path)
			if not error.is_empty():
				retry_render={"folder":folder,"video":video.duplicate(true),"audio":mix_path,"session":recovery_session,"revision":recovery_revision}
				retry_encode_button.show()
	if images_only:
		var summary:={"format":"studio_image_sequence_1","video":video.duplicate(true),"pattern":"frame_%06d.png","first_frame":1,"first_project_frame":0,"rendered_frames":completed,"drawing_only":drawings_only,"audio":"mixed_audio.wav" if not mix_path.is_empty() and error.is_empty() else "","status":"complete" if error.is_empty() else "cancelled" if cancel_export else "failed"}
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
	dialog.dialog_text = "Godot Engine 4.6 — MIT\nCopyright (c) 2014-present Godot Engine contributors.\nCopyright (c) 2007-2014 Juan Linietsky, Ariel Manzur.\nhttps://godotengine.org/license/\n\nFFmpeg is invoked as your separately installed executable.\nThis installed build enables GPL/version3; no binary is bundled.\nhttps://ffmpeg.org/legal.html\n\nRoom fixture: original procedural geometry; no downloaded models.\nApplication license: owner decision pending.\nFull records: THIRD_PARTY_NOTICES.md and docs/licenses.md."
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
		release_mouse()
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
	reset_recovery_schedule()
	refresh_recovery_schedule(false)

func reset_recovery_schedule() -> void:
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
	if recovery_preview.busy():return
	if not autosave_enabled.button_pressed and not force: return
	if not dirty or recovery_revision == checkpoint_revision:recovery_checkpoint_requested=false;return
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
	var started := Time.get_ticks_usec()
	var snapshot:=project_snapshot()
	var error := Recovery.checkpoint(recovery_root,recovery_session,snapshot.video,snapshot.camera_keys,snapshot.layers,str(snapshot.get("source","")),int(snapshot.editor.frame),snapshot.audio,has_project.path if not has_project.path.is_empty() else project_folder,recovery_revision,snapshot.get("model",{}),snapshot.world,snapshot.palette,snapshot.sequence_graph,snapshot.get("sequence_context",{}),snapshot.get("reference_sheet",{}))
	last_recovery_ms = (Time.get_ticks_usec() - started) / 1000.0
	if error.is_empty():
		checkpoint_revision = recovery_revision
		autosave_actions=0;autosave_retry_due=0
		recovery_status.text = "Recovery copy saved"
		var folder:=recovery_root.path_join(recovery_session)
		finish_recovery_preview.call_deferred(folder,FileAccess.get_sha256(folder.path_join("project.json")),frame,recovery_revision,renderer.view_state())
	else:
		autosave_retry_due=Time.get_ticks_msec()+30000
		recovery_status.text = "Recovery failed. Edits are pending."
		message(error + (" Studio will retry after 30 seconds when idle. You can also save manually." if autosave_enabled.button_pressed else " Use Checkpoint now to retry, or save manually."))

func finish_recovery_preview(folder: String,digest: String,at: int,revision: int,view: Dictionary) -> void:
	await RenderingServer.frame_post_draw
	if not is_inside_tree() or folder!=recovery_root.path_join(recovery_session) or recovery_revision!=revision or frame!=at or renderer.view_state()!=view:return
	if playing or exporting or drawing or navigating or pose_editor.dragging or physics_editor.is_running() or has_dialog(self):return
	if recovery_preview.busy():return
	var started:=Time.get_ticks_usec()
	var image: Image=renderer.viewport.get_texture().get_image()
	if not image or image.is_empty():return
	var overlays: Array=[]
	if canvas.sequence_overlay:overlays.append(canvas.sequence_overlay.get_image().duplicate())
	for layer in layers:
		if not layer.visible:continue
		var cel:=Drawing.cel_at(layer,at)
		if cel.is_empty():continue
		var copied: Image=cel.image.duplicate();copied.set_meta("studio_layer_opacity",float(layer.get("opacity",1.0)));overlays.append(copied)
	var preview_error: String=recovery_preview.start(folder,digest,image,overlays)
	last_recovery_preview_capture_ms=(Time.get_ticks_usec()-started)/1000.0
	if not preview_error.is_empty():recovery_status.text="Recovery saved; preview unavailable"

func poll_recovery_preview() -> void:
	var result: Dictionary=recovery_preview.poll()
	if result.is_empty():return
	recovery_preview_result=result
	last_recovery_preview_worker_ms=result.worker_ms
	last_recovery_preview_ms=last_recovery_preview_capture_ms+last_recovery_preview_worker_ms
	if result.folder==recovery_root.path_join(recovery_session) and not result.error.is_empty():recovery_status.text="Recovery saved; preview unavailable"

func _exit_tree() -> void:
	Drawing.opacity_cache.clear()
	# Join only at teardown; ordinary processing polls completed work without waiting.
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
	message("Recovered as an unsaved copy. Use Save to choose a .has file; the old manual save is untouched.")
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
				message("Recovered the newest valid checkpoint as an unsaved copy. Use Recover for older copies; Save chooses a .has file. Your manual save is untouched.")
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
		audio_start.value = 0
		audio_trim.value = 0
		audio_gain.value = 0
	else:
		audio_info.text = "%s\n%.2f s • %d Hz • %s" % [audio_clip.source.name.left(35), float(AudioTrack.source_end(audio_clip)-audio_clip.source_in_sample) / audio_clip.source.rate, audio_clip.source.rate, "stereo" if audio_clip.source.channels == 2 else "mono"]
		audio_start.value = audio_clip.start_frame
		audio_trim.value = float(audio_clip.source_in_sample) * 1000 / audio_clip.source.rate
		audio_gain.value = audio_clip.gain_db
		audio_mute.set_pressed_no_signal(audio_clip.muted)
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
