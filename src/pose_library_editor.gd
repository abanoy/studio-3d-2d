extends Node
const Library=preload("res://src/pose_library.gd")
var app
var editor
var launch: Button
var dialog: AcceptDialog
var listing: ItemList
var name_edit: LineEdit
var save_button: Button
var use_button: Button
var rename_button: Button
var duplicate_button: Button
var remove_button: Button
var info: Label
var session:=""
var target:=""
var root_id:=0
var selected:=""
var revision:=-1
var frame:=-1
var capturing:=false
var observed_auto:=true
func setup(owner_editor,parent: Node) -> void:
	editor=owner_editor;app=editor.app;launch=app.button(parent,"Body poses…",open)
	launch.tooltip_text="Save named authored body poses and reuse them on this same imported rig. Position, face and motion helpers stay independent."
	dialog=AcceptDialog.new();dialog.title="Body poses";dialog.exclusive=false;dialog.unresizable=false;dialog.ok_button_text="Done";app.add_child(dialog)
	var box:=VBoxContainer.new();dialog.add_child(box)
	info=Label.new();info.custom_minimum_size.x=520;info.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;box.add_child(info)
	listing=ItemList.new();listing.custom_minimum_size=Vector2(520,190);listing.fixed_icon_size=Vector2i(96,54);listing.icon_mode=ItemList.ICON_MODE_LEFT;box.add_child(listing);listing.item_selected.connect(func(index):selected=str(listing.get_item_metadata(index));name_edit.text=listing.get_item_text(index);refresh_buttons())
	name_edit=LineEdit.new();name_edit.max_length=64;name_edit.placeholder_text="Pose name";box.add_child(name_edit)
	save_button=app.button(box,"Save current body pose",capture)
	var actions:=HBoxContainer.new();box.add_child(actions)
	use_button=app.button(actions,"Use at this frame",apply_pose);rename_button=app.button(actions,"Rename",rename_pose);duplicate_button=app.button(actions,"Duplicate",duplicate_pose);remove_button=app.button(actions,"Remove…",request_remove)
	var exchange:=HBoxContainer.new();box.add_child(exchange);app.advanced(exchange)
	app.button(exchange,"Import HAS poses…",import_file);app.button(exchange,"Export HAS poses…",export_file)
	dialog.close_requested.connect(func():dialog.hide())
func rig() -> RefCounted:
	return editor.active_rig()
func context() -> bool:
	return is_instance_valid(dialog) and dialog.visible and session==app.recovery_session and rig()!=null and rig().data.id==target and rig().root.get_instance_id()==root_id and not app.home.visible
func busy() -> bool:
	return app.mode.selected!=2 or app.playing or app.exporting or editor.dragging or app.physics_editor.is_running() or editor.contacts.live_busy() or app.source_import.pid>0 or app.has_project.pid>0 or app.raster_importer and app.raster_importer.pid>0 or app.has_dialog(app)
func ready_edit() -> bool:
	if not context() or busy() or capturing:app.message("Stop live motion and finish other edits before changing body poses.");return false
	return true
func open() -> void:
	if rig()==null or rig().order.is_empty():app.message("Select a rigged model to use body poses.");return
	app.stop();app.finish_stroke();editor.finish_drag();session=app.recovery_session;target=rig().data.id;root_id=rig().root.get_instance_id();selected="";name_edit.text="";refresh();dialog.popup_centered(Vector2i(560,390))
func _process(_delta: float) -> void:
	launch.disabled=rig()==null or rig().order.is_empty() or app.exporting
	if not dialog.visible:return
	if not context():dialog.hide();return
	if revision!=app.recovery_revision:refresh()
	refresh_buttons()
func refresh() -> void:
	if rig()==null:return
	listing.clear();var library:=Library.get_library(rig());var why:=Library.compatible(library,rig())
	if not why.is_empty():info.text=why;selected="";return
	for entry in library.entries:
		var picture:=Library.thumbnail(entry.thumbnail_png);var texture:=ImageTexture.create_from_image(picture.image)
		listing.add_item(entry.name,texture);listing.set_item_metadata(listing.item_count-1,entry.id)
		if entry.id==selected:listing.select(listing.item_count-1);name_edit.text=entry.name
	revision=app.recovery_revision;refresh_buttons()
func refresh_buttons() -> void:
	var blocked:=not context() or busy() or capturing;var empty:=entry().is_empty()
	save_button.disabled=blocked;use_button.disabled=blocked or empty;rename_button.disabled=blocked or empty;duplicate_button.disabled=blocked or empty;remove_button.disabled=blocked or empty
	frame=app.frame;observed_auto=editor.auto_key.button_pressed
	info.text="%s · frame %d\nBody only: position, face, planted-foot targets and motion helpers stay separate.\n%s" % [rig().data.name,app.frame,"Use creates ordinary editable keys; camera keys stay explicit." if observed_auto else "Auto-key is off: Use adjusts the draft; Record pose key keeps it on the timeline."]
	if blocked:info.text+="\nChoose Pose mode, stop Physics / Hair & clothes and finish pending operations to save or apply."
func entry() -> Dictionary:
	if rig()==null:return {}
	for value in rig().data.metadata.get(Library.FIELD,{}).get("entries",[]):
		if value.id==selected:return value
	return {}
func store(value: Dictionary) -> bool:
	if not ready_edit():return false
	var why:=Library.compatible(value,rig())
	if not why.is_empty():app.message(why);return false
	var data: Dictionary=rig().data.duplicate(true);data.metadata[Library.FIELD]=value.duplicate(true)
	if data==rig().data:return true
	var world: Dictionary=app.current_world()
	for i in range(world.objects.size()):
		if world.objects[i].id==target:world.objects[i]=data
	if editor.contacts.metadata_bytes(world)>1024*1024:app.message("Saved poses would exceed this scene's metadata budget. Remove a saved pose first.");return false
	why=editor.restore_state(data)
	if not why.is_empty():app.message(why);return false
	refresh();return true
func capture() -> void:
	if not ready_edit():return
	var title:=name_edit.text.strip_edges()
	if title.is_empty():title="Body pose"
	if not Library.text(title,64):app.message("Use a single-line pose name of1–64characters.");return
	var library:=Library.get_library(rig())
	if library.entries.size()>=Library.MAX_ENTRIES:app.message("This library already has sixteen body poses.");return
	var pose: Dictionary=rig().sample_body(app.frame,true);var current_revision: int=app.recovery_revision;var at: int=app.frame;var view: Dictionary=app.renderer.view_state();capturing=true
	var picture: Dictionary=await preload("res://src/pose_thumbnail.gd").capture(rig(),pose,self)
	capturing=false
	if not context() or busy() or current_revision!=app.recovery_revision or at!=app.frame or view!=app.renderer.view_state():app.message("The scene or view changed while saving the pose. Try again.");return
	if picture.has("error"):app.message(picture.error);return
	var image: Image=picture.image
	var value:={"id":str(ResourceUID.create_id()),"name":Library.unique_name(title,library.entries),"pose":pose,"thumbnail_png":Marshalls.raw_to_base64(image.save_png_to_buffer())};library.entries.append(value)
	if store(library):selected=value.id;refresh();app.message("Body pose saved. It stays with this model in HAS; Undo removes this save.")
func apply_pose() -> void:
	if not ready_edit():return
	var value:=entry()
	if value.is_empty():return
	var why:=Library.compatible(Library.get_library(rig()),rig())
	if not why.is_empty():app.message(why);return
	var before: Dictionary=rig().data.duplicate(true)
	editor.begin_draft();rig().data.pose=value.pose.duplicate(true);editor.commit(before,true);refresh_buttons()
func rename_pose() -> void:
	if not ready_edit():return
	var title:=name_edit.text.strip_edges()
	if not Library.text(title,64):app.message("Use a single-line pose name of1–64characters.");return
	var library:=Library.get_library(rig())
	for value in library.entries:
		if value.id!=selected and value.name.nocasecmp_to(title)==0:app.message("Another saved pose already uses this name.");return
	for value in library.entries:
		if value.id==selected:value.name=title
	store(library)
func duplicate_pose() -> void:
	if not ready_edit():return
	var value:=entry().duplicate(true)
	if value.is_empty():return
	var library:=Library.get_library(rig());value.id=str(ResourceUID.create_id());value.name=Library.unique_name(value.name,library.entries);library.entries.append(value)
	if store(library):selected=value.id;refresh()
func request_remove() -> void:
	if not ready_edit() or entry().is_empty():return
	var id:=selected;var old_revision: int=app.recovery_revision;var confirmation:=ConfirmationDialog.new();confirmation.title="Remove saved body pose?";confirmation.dialog_text="Remove %s from the library?\nExisting animation keys stay in the scene. Undo restores the saved pose." % entry().name;confirmation.exclusive=false;app.add_child(confirmation)
	confirmation.confirmed.connect(func():
		confirmation.hide()
		if context() and old_revision==app.recovery_revision:
			var library:=Library.get_library(rig());library.entries=library.entries.filter(func(value):return value.id!=id)
			if store(library):selected="";refresh()
		confirmation.queue_free())
	confirmation.canceled.connect(confirmation.queue_free);confirmation.popup_centered(Vector2i(480,170))
func import_file() -> void:
	if not ready_edit():return
	var old_revision: int=app.recovery_revision
	app.choose_file("Import HAS body poses",PackedStringArray(["*.json ; HAS body-pose library"]),func(path):
		if not context() or app.recovery_revision!=old_revision:app.message("The scene changed. Import body poses again.");return
		var file:=FileAccess.open(path,FileAccess.READ)
		if not file or file.get_length()>Library.MAX_BYTES:app.message("Body-pose library is missing or exceeds192KiB.");return
		var parsed=JSON.parse_string(file.get_as_text());file.close();var why:=Library.error(parsed)
		if not why.is_empty():app.message(why);return
		why=Library.compatible(parsed,rig())
		if not why.is_empty():app.message(why);return
		var library:=Library.get_library(rig())
		for value in parsed.entries:
			if library.entries.any(func(e):return Library.equivalent(e,value)):continue
			var copy: Dictionary=value.duplicate(true);copy.id=str(ResourceUID.create_id());copy.name=Library.unique_name(copy.name,library.entries);library.entries.append(copy)
		store(library))
func export_file() -> void:
	if not ready_edit():return
	var library:=Library.get_library(rig());var old_revision: int=app.recovery_revision
	var file_dialog:=FileDialog.new();file_dialog.access=FileDialog.ACCESS_FILESYSTEM;file_dialog.file_mode=FileDialog.FILE_MODE_SAVE_FILE;file_dialog.title="Export HAS body poses";file_dialog.filters=PackedStringArray(["*.json ; HAS body-pose library"]);file_dialog.current_file="Body poses.hasposes.json";app.add_child(file_dialog)
	file_dialog.file_selected.connect(func(path):
		file_dialog.hide();file_dialog.queue_free()
		if not context() or app.recovery_revision!=old_revision:app.message("The scene changed. Export body poses again.");return
		var why:=Library.compatible(library,rig())
		if not why.is_empty():app.message(why);return
		var temporary: String=path+".studio-"+str(Time.get_ticks_usec())+".tmp";var file:=FileAccess.open(temporary,FileAccess.WRITE)
		if not file:app.message("Cannot write this body-pose library.");return
		file.store_string(JSON.stringify(library,"",true,true));file.flush();file.close()
		if DirAccess.rename_absolute(temporary,path)!=OK:app.message("Cannot commit this body-pose library; the previous file was kept.");return
		app.message("HAS body poses exported. Only the identical imported rig can use them."))
	file_dialog.canceled.connect(file_dialog.queue_free);file_dialog.popup_centered_ratio(.7)
