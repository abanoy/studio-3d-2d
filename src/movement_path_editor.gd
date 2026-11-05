extends Node
const PathData=preload("res://src/movement_path.gd")
const Model=PathData.Model
const Preset=preload("res://src/movement_path_preset.gd")
var app
var button: Button
var window: Window
var plot: Control
var frame: SpinBox
var note: Label
var apply_button: Button
var add_button: Button
var remove_button: Button
var before: Dictionary={}
var draft: Dictionary={}
var video: Dictionary={}
var target: WeakRef
var generation:=0
var preset_name: LineEdit
var save_preset_button: Button
var load_preset_button: Button

func setup(parent: Node) -> void:button=app.button(parent,"Movement path…",open)

func sync() -> void:
	button.disabled=not app.renderer.active_model() or app.exporting or app.playing

func valid() -> bool:
	var rig: RefCounted=app.renderer.active_model()
	return rig!=null and target!=null and target.get_ref()==rig.root and rig.data==before and app.video==video and not app.exporting and not app.playing and not app.pose_editor.contacts.live_busy()

func open() -> void:
	var rig: RefCounted=app.renderer.active_model()
	if not rig or app.exporting or app.playing:return
	if app.pose_editor.contacts.live_busy():app.message("Turn Physics and Hair & clothes off before editing a movement path.");return
	app.finish_stroke();app.pose_editor.finish_drag()
	if rig.data.draft_frame==app.frame and (rig.sample_body(app.frame,true)!=rig.sample_body(app.frame,false) or rig.sample_authored_transform(app.frame,true)!=rig.sample_authored_transform(app.frame,false)):
		app.message("Record your draft pose before editing its movement path.");return
	close();before=rig.data.duplicate(true);draft=before.duplicate(true);video=app.video.duplicate(true);target=weakref(rig.root)
	if PathData.controls(before).size()>PathData.MAX_POINTS:app.message("Movement path supports up to256 model keys in this increment.");return
	window=Window.new();window.title="Movement path";window.theme=app.theme;window.exclusive=false;window.transient=true;window.min_size=Vector2i(720,480);app.add_child(window);window.close_requested.connect(close)
	window.focus_exited.connect(func():if is_instance_valid(plot):plot.dragging=-1)
	var panel:=PanelContainer.new();panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);window.add_child(panel)
	var box:=VBoxContainer.new();panel.add_child(box)
	app.label(box,"Add a point at a frame, then drag it. Change views to adjust depth.\nBlack dots are your keys; the line previews movement. Coordinates follow the model’s group.").autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	var row:=HBoxContainer.new();box.add_child(row)
	var views:=OptionButton.new();views.add_item("Top · X / Z");views.add_item("Front · X / Y");views.add_item("Side · Z / Y");row.add_child(views)
	views.item_selected.connect(func(index):plot.dragging=-1;plot.view=index;plot.fit())
	app.button(row,"Fit path",func():plot.fit())
	plot=preload("res://src/movement_path_view.gd").new();plot.custom_minimum_size=Vector2(550,300);plot.size_flags_vertical=Control.SIZE_EXPAND_FILL;plot.size_flags_horizontal=Control.SIZE_EXPAND_FILL;box.add_child(plot)
	plot.chosen.connect(func(at):frame.set_value_no_signal(at));plot.moved.connect(move_point)
	var actions:=HBoxContainer.new();box.add_child(actions);frame=app.spin(actions,"Frame",0,int(video.duration_frames),app.frame)
	add_button=app.button(actions,"Add point",add_point);remove_button=app.button(actions,"Delete point",remove_point)
	note=app.label(box,"Only model movement changes. Poses, expressions, camera and drawings stay independent. Walking steps are not generated yet.");note.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	var presets:=HBoxContainer.new();box.add_child(presets)
	preset_name=LineEdit.new();preset_name.max_length=80;preset_name.text=(str(rig.data.name)+" route").left(80);preset_name.size_flags_horizontal=Control.SIZE_EXPAND_FILL;presets.add_child(preset_name)
	save_preset_button=app.button(presets,"Save path preset…",save_preset);load_preset_button=app.button(presets,"Load path preset…",load_preset)
	var footer:=HBoxContainer.new();box.add_child(footer);apply_button=app.button(footer,"Apply path",apply);app.button(footer,"Cancel",close)
	window.popup_centered(Vector2i(850,650));refresh();call_deferred("fit")

func fit() -> void:
	if is_instance_valid(plot):plot.fit()

func refresh() -> void:
	plot.points=PathData.controls(draft);plot.line=PathData.preview(draft,video);plot.queue_redraw()

func stage(value: Dictionary) -> void:
	if value.has("error"):note.text=value.error;return
	generation+=1;draft=value.data;refresh();note.text="Path preview only. Apply saves the movement keys as one Undo action."

func move_point(at: int,position: Vector3) -> void:
	if not valid():return
	stage(PathData.change(draft,at,position,int(video.duration_frames)))

func add_point() -> void:
	if not valid():return
	var probe:=Model.new();probe.data=draft;var at:=int(frame.value);var position: Vector3=Model.Timeline.vector(probe.sample_authored_transform(at).position)
	stage(PathData.change(draft,at,position,int(video.duration_frames)));plot.selected=at;plot.queue_redraw()

func remove_point() -> void:
	if not valid():return
	var at:=int(frame.value)
	if not PathData.controls(draft).any(func(point):return point.frame==at):note.text="Choose a black movement key to delete.";return
	stage(PathData.remove(draft,at,int(video.duration_frames)));plot.selected=-1

func apply() -> void:
	if not valid():note.text="The scene changed. Close and reopen its movement path.";return
	if draft==before:close();return
	var rig: RefCounted=app.renderer.active_model();var error: String=preload("res://src/contact_clipboard.gd").validate_candidate(rig,draft,int(video.duration_frames))
	if not error.is_empty():note.text=error;return
	var world: Dictionary=app.current_world()
	for n in range(world.objects.size()):
		if world.objects[n].id==draft.id:world.objects[n]=draft
	if app.pose_editor.contacts.metadata_bytes(world)>1024*1024:note.text="This path exceeds the scene metadata limit.";return
	error=app.pose_editor.restore_state(draft)
	if not error.is_empty():note.text=error;return
	var at:=mini(int(frame.value),int(video.duration_frames)-1);close();app.set_frame(at);app.message("Movement path saved. Undo restores its previous keys.")

func close() -> void:
	generation+=1
	if is_instance_valid(window):window.hide();window.queue_free()
	window=null;plot=null;before={};draft={};target=null

func _process(_delta: float) -> void:
	if not is_instance_valid(window):return
	var ready:=valid();plot.enabled=ready;apply_button.disabled=not ready;add_button.disabled=not ready;remove_button.disabled=not ready;save_preset_button.disabled=not ready;load_preset_button.disabled=not ready
	if not ready:note.text="The scene or selection changed. Close and reopen its movement path."

func protected_paths() -> Array:
	var result: Array=[]
	for object in app.current_world().objects:
		if object.has("source"):
			result.append(object.source);result.append(str(object.source).get_base_dir().path_join("parameters.json"))
		var imported: String=str(object.get("metadata",{}).get("import_source",""))
		if not imported.is_empty():result.append(imported);result.append(imported.get_base_dir().path_join("parameters.json"))
		for key in ["source_dir","external_bundle"]:
			var directory: String=str(object.get(key,object.get("metadata",{}).get(key,"")))
			if not directory.is_empty():result.append(directory.path_join("parameters.json"))
	return result

func preset_dialog(save: bool) -> FileDialog:
	var dialog:=FileDialog.new();dialog.access=FileDialog.ACCESS_FILESYSTEM
	dialog.file_mode=FileDialog.FILE_MODE_SAVE_FILE if save else FileDialog.FILE_MODE_OPEN_FILE
	dialog.title="Save movement path preset" if save else "Load movement path preset"
	dialog.filters=PackedStringArray(["*.json ; HAS movement path preset"])
	if save:dialog.current_file="Route.haspaths.json"
	app.add_child(dialog);dialog.canceled.connect(dialog.queue_free)
	return dialog

func save_preset() -> void:
	if not valid():return
	var captured:=Preset.capture(draft,video,preset_name.text)
	if captured.has("error"):note.text=captured.error;return
	var token:=generation;var revision: int=app.recovery_revision;var protected:=protected_paths()
	var dialog:=preset_dialog(true)
	dialog.file_selected.connect(func(path):
		dialog.hide();dialog.queue_free()
		if not valid() or generation!=token or app.recovery_revision!=revision:app.message("The path or scene changed. Save the preset again.");return
		var why:=Preset.write_file(path,captured.preset,protected)
		note.text="Path preset saved. The scene still waits for Apply path." if why.is_empty() else why)
	dialog.popup_centered_ratio(.7)

func load_preset() -> void:
	if not valid():return
	var token:=generation;var revision: int=app.recovery_revision;var dialog:=preset_dialog(false)
	dialog.file_selected.connect(func(path):
		dialog.hide();dialog.queue_free()
		if not valid() or generation!=token or app.recovery_revision!=revision:app.message("The path or scene changed. Load the preset again.");return
		var loaded:=Preset.read_file(path)
		if loaded.has("error"):note.text=loaded.error;return
		var changed:=Preset.assign(draft,video,loaded.preset,app.frame)
		stage(changed)
		if not changed.has("error"):
			preset_name.text=loaded.preset.name;plot.fit()
			note.text="Preview: replaces the whole position path from this model's introduction, relative to its starting position. Turn, size and pose stay independent. Apply checks foot constraints. No walking steps are generated.")
	dialog.popup_centered_ratio(.7)
