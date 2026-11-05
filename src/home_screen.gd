extends Control
const Recents=preload("res://src/recent_projects.gd")
const ThemeArt=preload("res://src/studio_theme.gd")
var app
var store=Recents.new()
var panel: PanelContainer
var recent_list: VBoxContainer
var notice: Label
var new_button: Button
var open_button: Button
var return_button: Button
var tutorials_button: Button

func _ready() -> void:
	name="StudioHome";set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);mouse_filter=Control.MOUSE_FILTER_STOP;z_index=100
	var background:=ColorRect.new();background.color=Color(0.86,0.91,0.96,0.97);background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);background.mouse_filter=Control.MOUSE_FILTER_IGNORE;add_child(background)
	var outer:=ScrollContainer.new();outer.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);add_child(outer)
	var center:=CenterContainer.new();center.size_flags_horizontal=Control.SIZE_EXPAND_FILL;center.size_flags_vertical=Control.SIZE_EXPAND_FILL;outer.add_child(center)
	panel=PanelContainer.new();panel.custom_minimum_size=Vector2(720,520);panel.add_theme_stylebox_override("panel",ThemeArt.surface("f7fcff","dce8f4","7899b7",18));center.add_child(panel)
	var box:=VBoxContainer.new();panel.add_child(box)
	resized.connect(size_home_panel)
	size_home_panel.call_deferred()
	var title: Label=app.label(box,"Hybrid Animation Studio");title.add_theme_font_size_override("font_size",26)
	app.label(box,"Build a scene. Animate. Draw. Make a movie.")
	var actions:=HBoxContainer.new();box.add_child(actions)
	new_button=app.icon_button(actions,"New scene","scene",app.new_dialog,"Start a clean empty world; unsaved edits require confirmation")
	open_button=app.icon_button(actions,"Open project…","folder",app.open_dialog)
	tutorials_button=app.icon_button(actions,"Tutorials","help",func():app.tutorials.open_catalog(),"Learn with real practice scenes and observed steps")
	return_button=app.icon_button(actions,"Return to scene","play",hide,"Keep the current scene and continue editing • Escape")
	for control in [new_button,open_button,tutorials_button,return_button]:control.custom_minimum_size.y=50;control.size_flags_horizontal=Control.SIZE_EXPAND_FILL;control.focus_mode=Control.FOCUS_ALL
	app.button(box,"Settings",app.show_display_settings)
	var heading: Label=app.label(box,"Recent projects");heading.add_theme_font_size_override("font_size",18)
	var scroll:=ScrollContainer.new();scroll.custom_minimum_size=Vector2(660,300);scroll.size_flags_vertical=Control.SIZE_EXPAND_FILL;box.add_child(scroll)
	recent_list=VBoxContainer.new();recent_list.size_flags_horizontal=Control.SIZE_EXPAND_FILL;scroll.add_child(recent_list)
	notice=app.label(box,"");notice.custom_minimum_size=Vector2(660,34);notice.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	notice.max_lines_visible=2;notice.text_overrun_behavior=TextServer.OVERRUN_TRIM_ELLIPSIS
	hide()

func size_home_panel() -> void:
	panel.custom_minimum_size=Vector2(maxf(720,size.x*0.82),maxf(520,size.y*0.82))

func open_home() -> void:
	if app.exporting or app.source_import.pid>0 or app.has_dialog(app):return
	if app.physics_editor.recording and app.physics_editor.recording.active:app.message("Finish recording before opening Home.");return
	app.stop();app.finish_stroke();app.pose_editor.finish_drag();app.release_mouse()
	app.pose_editor.reveal_bones=false;app.canvas.panning=false
	refresh();feedback("Choose a project, or return to your current scene.");show();new_button.grab_focus()

func feedback(text: String) -> void:
	notice.text=text;notice.tooltip_text=text

func refresh() -> void:
	for child in recent_list.get_children():recent_list.remove_child(child);child.queue_free()
	var rows:=store.read()
	if rows.is_empty():
		app.label(recent_list,"Your saved and opened .has projects will appear here.")
	if app.tutorials:
		var course: String=app.tutorials.First.ID
		var current_lesson: bool=app.tutorials.active and app.tutorials.course==course
		var progress: Dictionary=app.tutorials.store.progress(course)
		if rows.is_empty() or current_lesson or (not progress.is_empty() and not progress.done):
			var caption:="Make your first movie"
			if not progress.is_empty():
				caption="Open your finished practice" if progress.done else "Continue your first movie"
			if current_lesson:caption="Return to your first movie"
			var practice: Button=app.button(recent_list,caption,func():
				if app.tutorials.active and app.tutorials.course==course:hide()
				else:app.tutorials.request(course,progress.is_empty()))
			practice.name="FirstMoviePractice"
			practice.focus_mode=Control.FOCUS_ALL
			practice.tooltip_text="Use the included room and figure to pose, move the camera, draw and export a short movie."
	for row in rows:
		var line:=HBoxContainer.new();recent_list.add_child(line)
		var thumbnail:=TextureRect.new();thumbnail.custom_minimum_size=Vector2(96,54);thumbnail.expand_mode=TextureRect.EXPAND_IGNORE_SIZE;thumbnail.stretch_mode=TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		var image:=Recents.preview(row,app.recovery_root)
		thumbnail.texture=ImageTexture.create_from_image(image) if image else ThemeArt.icon("scene");line.add_child(thumbnail)
		var exists:=FileAccess.file_exists(row.path)
		var select: Button=app.button(line,row.path.get_file().get_basename()+(" • not found" if not exists else ""),func():open_recent(row.path))
		select.name="RecentProject";select.set_meta("path",row.path);select.tooltip_text=row.path+"\n"+("Last recovery preview" if image else "No preview yet");select.size_flags_horizontal=Control.SIZE_EXPAND_FILL;select.disabled=not exists;select.text_overrun_behavior=TextServer.OVERRUN_TRIM_ELLIPSIS
		var remove: Button=app.button(line,"Remove",func():
			if store.forget(row.path):refresh()
			else:notice.text=store.error)
		remove.tooltip_text="Remove from this list only. The project and its files stay intact."

func open_recent(path: String) -> void:
	if app.exporting or app.source_import.pid>0 or not FileAccess.file_exists(path):return
	var action:=func():notice.text="Opening "+path.get_file()+"…";app.has_project.open_file(path)
	if app.dirty:app.confirm_action("Replace unsaved edits with this project? Save first to keep them.",action)
	else:action.call()

func remember(path: String,revision: int = -1) -> void:
	if not store.remember(path,app.recovery_root.path_join(app.recovery_session),revision) and not store.error.is_empty() and visible:notice.text=store.error

func _process(_delta: float) -> void:
	if not visible:return
	var busy: bool=app.exporting or app.source_import.pid>0
	new_button.disabled=busy;open_button.disabled=busy;tutorials_button.disabled=busy;return_button.disabled=busy
