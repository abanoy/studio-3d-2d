extends Node
const Parts=preload("res://src/character_parts.gd")
const SceneIO=preload("res://src/scene3d.gd")
const Model=preload("res://src/model.gd")
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
const Runtime=preload("res://src/world_runtime.gd")
const Bounds=preload("res://src/pose_bounds.gd")
var app
var dialog: AcceptDialog
var switches: Dictionary={}
var opened_world: Dictionary={}
var opened_frame:=0
var root_id:=""
var opened_session:=""
var opened_owner:=""
var info: Label
var follow_switches: Dictionary={}
var follow_notes: Dictionary={}
var follow_reference: OptionButton

func ready_to_edit() -> bool:
	return is_instance_valid(app) and not app.exporting and not app.playing and not app.navigating and not app.pose_editor.dragging and not app.physics_editor.is_running() and not app.physics_editor.recording.active and app.source_import.pid<=0 and app.has_project.pid<=0 and not (app.height_review and app.height_review.pending)

func can_manage(selected: String) -> bool:
	# WorldSelection asks every frame: inspect existing rows, never snapshot rigs.
	if not ready_to_edit() or app.renderer.world_runtime==null:return false
	var runtime: RefCounted=app.renderer.world_runtime
	var chosen: RefCounted=runtime.instance(selected)
	if chosen==null:return false
	var owner_id: String=selected if chosen.data.get("kind")=="group" else str(chosen.data.get("parent_id",""))
	var owner: RefCounted=runtime.instance(owner_id)
	if owner==null or owner.data.get("kind")!="group":return false
	var metadata=owner.data.get("metadata",{}).get("character_parts",{})
	return metadata is Dictionary and metadata.get("format")==Parts.FORMAT

func open(selected: String) -> void:
	if not ready_to_edit():app.message("Finish the current operation before editing character parts.");return
	var bundle:=Parts.describe(app.current_world(),selected,int(app.video.duration_frames))
	if bundle.has("error"):app.message(bundle.error);return
	if is_instance_valid(dialog):dialog.hide();dialog.queue_free()
	opened_world=app.current_world().duplicate(true);opened_frame=app.frame;root_id=bundle.root_id
	opened_session=app.recovery_session;opened_owner=app.sequence_editor.active_owner;switches.clear();follow_switches.clear();follow_notes.clear()
	dialog=AcceptDialog.new();dialog.title="Parts — "+str(bundle.name);dialog.min_size=Vector2i(420,300);dialog.unresizable=false
	app.add_child(dialog);dialog.get_ok_button().hide()
	var box:=VBoxContainer.new();dialog.add_child(box)
	info=app.label(box,"Show or hide parts at this frame. Later visibility keys use the project fade; rigs and expressions stay independent.");info.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	var reference_line:=HBoxContainer.new();box.add_child(reference_line)
	app.label(reference_line,"Body to follow:")
	follow_reference=OptionButton.new();follow_reference.size_flags_horizontal=Control.SIZE_EXPAND_FILL;reference_line.add_child(follow_reference)
	var reference_id: String=str(bundle.metadata.get("follow_reference_id",bundle.metadata.get("height_reference_id","")))
	for part in bundle.parts:
		follow_reference.add_item(str(part.row.name));var at: int=follow_reference.item_count-1
		follow_reference.set_item_metadata(at,part.row.id)
		if part.row.id==reference_id:follow_reference.select(at)
	follow_reference.item_selected.connect(func(_index):update_follow_options())
	var scroll:=ScrollContainer.new();scroll.custom_minimum_size=Vector2(430,220);scroll.size_flags_vertical=Control.SIZE_EXPAND_FILL;box.add_child(scroll)
	var list:=VBoxContainer.new();list.size_flags_horizontal=Control.SIZE_EXPAND_FILL;scroll.add_child(list)
	for part in bundle.parts:
		var entry:=VBoxContainer.new();list.add_child(entry)
		var line:=HBoxContainer.new();entry.add_child(line)
		var control:=CheckBox.new();control.text=str(part.row.name);control.size_flags_horizontal=Control.SIZE_EXPAND_FILL
		control.button_pressed=Parts.Visibility.target(part.row,opened_frame);line.add_child(control);switches[part.row.id]=control
		var id: String=part.row.id
		app.button(line,"Select",func():dialog.hide();app.world_selection.select_entity(id))
		app.button(line,"Remove…",func():remove_part(id))
		var follow_line:=HBoxContainer.new();entry.add_child(follow_line)
		var settings=part.row.metadata.get("character_part",{})
		var follow:=CheckBox.new();follow.text="Follow body joints";follow.button_pressed=settings is Dictionary and settings.get("follow_body",false)==true
		follow_line.add_child(follow);follow_switches[id]=follow
		var note:=Label.new();note.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;note.size_flags_horizontal=Control.SIZE_EXPAND_FILL;follow_line.add_child(note);follow_notes[id]=note
	var row:=HBoxContainer.new();box.add_child(row)
	app.button(row,"Show all",func():set_all_parts(true))
	app.button(row,"Hide all",func():set_all_parts(false))
	app.button(row,"Add part…",add_part_dialog)
	app.label(box,"Following is opt-in. Unmatched joints and expressions stay independent; live physics pauses following.").autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	app.button(box,"Apply part settings",apply_visibility)
	app.button(box,"Close",dialog.hide)
	update_follow_options()
	dialog.popup_centered(Vector2i(760,560))

func selected_follow_reference() -> String:
	return str(follow_reference.get_item_metadata(follow_reference.selected)) if is_instance_valid(follow_reference) and follow_reference.selected>=0 else ""

func update_follow_options() -> void:
	if app.renderer.world_runtime==null:return
	var reference:=selected_follow_reference()
	for id in follow_switches:
		var control: CheckBox=follow_switches[id];var note: Label=follow_notes[id]
		var report: Dictionary=app.renderer.world_runtime.follow_report(id,reference)
		if report.has("error"):
			note.text=str(report.error);control.disabled=not control.button_pressed
		else:
			note.text="%d matched · %d unmatched · %d ambiguous · %d procedural kept independent" % [report.matched,report.unmatched,report.ambiguous,report.procedural]
			control.disabled=report.matched==0 and not control.button_pressed

func set_all_parts(value: bool) -> void:
	for control in switches.values():control.button_pressed=value

func context_matches() -> bool:
	return ready_to_edit() and app.recovery_session==opened_session and app.sequence_editor.active_owner==opened_owner and app.frame==opened_frame and app.current_world()==opened_world

func apply_visibility() -> void:
	if not context_matches():info.text="The scene changed. Reopen Parts before applying.";return
	if switches.is_empty():info.text="Add a part before applying settings.";return
	var values:={}
	for id in switches:values[id]=switches[id].button_pressed
	var edit:=Parts.visibility_edit(opened_world,root_id,values,opened_frame,int(app.video.duration_frames))
	if edit.has("error"):info.text=edit.error;return
	var proposed:=opened_world.duplicate(true)
	for i in range(proposed.objects.size()):
		if edit.after.has(proposed.objects[i].id):proposed.objects[i]=edit.after[proposed.objects[i].id]
	var follows:={}
	for id in follow_switches:follows[id]=follow_switches[id].button_pressed
	var follow_edit:=Parts.follow_edit(proposed,root_id,follows,selected_follow_reference(),int(app.video.duration_frames))
	if follow_edit.has("error"):info.text=follow_edit.error;return
	for id in follow_edit.after:
		if not edit.before.has(id):edit.before[id]=follow_edit.before[id]
		edit.after[id]=follow_edit.after[id]
	if edit.after.is_empty():info.text="Those visibility states are already set.";return
	var why: String=app.renderer.world_runtime.restore_instances(edit.after)
	if not why.is_empty():info.text=why;return
	app.push_history(edit);app.set_frame(app.frame);app.changed();app.refresh_timeline()
	opened_world=app.current_world().duplicate(true);info.text="Parts updated. Undo restores visibility and following together."
	update_follow_options()

func remove_part(id: String) -> void:
	if not context_matches():info.text="The scene changed. Reopen Parts before removing a part.";return
	app.confirm_action("Remove this part from the character and scene? Undo restores it.",func():
		if not context_matches():return
		var before: Dictionary=app.current_world().duplicate(true);var after:=before.duplicate(true)
		var removed:={id:true};var expanded:=true
		while expanded:
			expanded=false
			for row in after.objects:
				if removed.has(row.parent_id) and not removed.has(row.id):removed[row.id]=true;expanded=true
		after.objects=after.objects.filter(func(row):return not removed.has(row.id))
		for row in after.objects:
			if row.id==root_id:row.metadata.character_parts.members=row.metadata.character_parts.members.filter(func(member):return not removed.has(member.id))
		var why: String=app.restore_world(after)
		if why.is_empty():app.push_history({"type":"world","before":before,"after":after});app.changed();dialog.hide())

func add_part_dialog() -> void:
	var picker:=FileDialog.new();picker.title="Add part to character";picker.access=FileDialog.ACCESS_FILESYSTEM
	picker.file_mode=FileDialog.FILE_MODE_OPEN_FILE;picker.filters=PackedStringArray(["*.glb,*.mdl ; Character parts"]);app.add_child(picker)
	var destination:=root_id
	picker.file_selected.connect(func(path):
		picker.queue_free();dialog.hide()
		app.source_import.start_bundle([{"path":path,"member":"","role":Parts.role_for(path)}],{"existing_root":destination,"name":"Character","start_frame":app.frame,"fit_height":false}))
	picker.canceled.connect(picker.queue_free);picker.popup_centered(Vector2i(800,520))

func sibling_requests(path: String, choices: Array) -> Array:
	var result: Array=[]
	if path.get_extension().to_lower()=="mdl":
		var folder:=DirAccess.open(path.get_base_dir())
		if folder:
			var names:=folder.get_files();names.sort()
			for name in names:
				if name.get_extension().to_lower()=="mdl":result.append({"path":path.get_base_dir().path_join(name),"member":"","role":Parts.role_for(name)})
	else:
		for member in choices:result.append({"path":path,"member":str(member),"role":Parts.role_for(str(member))})
	return result.slice(0,Parts.MAX_PARTS)

func folder_requests(folder: String, depth:=0) -> Array:
	var result: Array=[]
	if depth>5:return result
	var directory:=DirAccess.open(folder)
	if directory==null:return result
	var files:=directory.get_files();files.sort()
	for name in files:
		if name.get_extension().to_lower() in ["mdl","glb"]:
			var path:=folder.path_join(name)
			var role: String=Parts.role_for(folder.get_file()) if name.to_lower()=="scene.glb" else Parts.role_for(name)
			result.append({"path":path,"member":"","role":role})
			if result.size()>=Parts.MAX_PARTS:return result
	for name in directory.get_directories():
		if name.begins_with("."):continue
		result.append_array(folder_requests(folder.path_join(name),depth+1))
		if result.size()>=Parts.MAX_PARTS:return result.slice(0,Parts.MAX_PARTS)
	return result

func open_folder() -> void:
	if not ready_to_edit():app.message("Finish the current operation before importing character parts.");return
	var picker:=FileDialog.new();picker.title="Choose a character parts folder";picker.access=FileDialog.ACCESS_FILESYSTEM;picker.file_mode=FileDialog.FILE_MODE_OPEN_DIR
	app.add_child(picker)
	picker.dir_selected.connect(func(path):picker.queue_free();open_sources(path,[],.01905,app.frame,"",folder_requests(path)))
	picker.canceled.connect(picker.queue_free);picker.popup_centered(Vector2i(800,520))

func open_sources(path: String, choices: Array, unit_scale:=.01905, start_frame:=0, content:="", provided: Array=[]) -> void:
	if not ready_to_edit():return
	var requests: Array=provided if not provided.is_empty() else sibling_requests(path,choices)
	if requests.is_empty():app.message("No sibling model parts were found.");return
	var window:=ConfirmationDialog.new();window.title="Load character parts together";window.ok_button_text="Prepare character";window.unresizable=false
	app.add_child(window)
	var box:=VBoxContainer.new();window.add_child(box)
	app.label(box,"Choose parts that share the same source origin. HAS keeps their alignment and independent rigs.").autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	var name:=LineEdit.new();name.text=path.get_file().get_basename();box.add_child(name)
	var scroll:=ScrollContainer.new();scroll.custom_minimum_size=Vector2(550,240);box.add_child(scroll)
	var list:=VBoxContainer.new();list.size_flags_horizontal=Control.SIZE_EXPAND_FILL;scroll.add_child(list)
	var controls: Array=[];var body:=OptionButton.new()
	for i in range(requests.size()):
		var request: Dictionary=requests[i];var label: String=request.path.get_file() if str(request.member).is_empty() else str(request.member).get_file()
		var check:=CheckBox.new();check.text=label;check.button_pressed=true;list.add_child(check);controls.append(check)
		body.add_item(label)
		if request.role=="body" or label.to_lower().get_basename() in ["junko","body"]:body.select(i)
	app.label(box,"Body reference for the shared height:");box.add_child(body)
	var fit:=CheckBox.new();fit.text="Make the body 6 ft at character Scale 1 (all parts share this factor)";fit.button_pressed=true;box.add_child(fit)
	window.confirmed.connect(func():
		var selected: Array=[];var reference_index:=-1
		for i in range(requests.size()):
			if controls[i].button_pressed:
				if i==body.selected:reference_index=selected.size()
				selected.append(requests[i])
		if selected.is_empty():app.message("Choose at least one part.");return
		if fit.button_pressed and reference_index<0:app.message("Include the selected body reference, or turn off height fitting.");return
		window.hide()
		app.source_import.start_bundle(selected,{"name":name.text,"unit_scale":unit_scale,"start_frame":start_frame,"fit_height":fit.button_pressed,"reference_index":maxi(reference_index,0),"content":content});window.queue_free())
	window.canceled.connect(window.queue_free);window.popup_centered(Vector2i(650,500))

func install_prepared(prepared: Array, options: Dictionary) -> String:
	if not ready_to_edit():return "Finish the current operation before adding the character."
	var incoming: Array=[];var origins:={}
	var cache:=ProjectSettings.globalize_path("res://output/imports")
	if DirAccess.make_dir_recursive_absolute(cache)!=OK:return "Cannot create the managed import folder."
	for item in prepared:
		var definition: Dictionary=app.pose_editor.definition(str(item.path))
		if definition.has("error"):return definition.error
		var row: Dictionary=definition.data
		var managed:=cache.path_join(row.sha256+".glb")
		var why: String=Storage.managed_copy(str(item.path),managed,row.sha256)
		if not why.is_empty():return why
		row.source=managed;row.metadata["import_source"]=str(item.path);origins[managed.replace("\\","/")]=str(item.path)
		incoming.append({"row":row,"role":str(item.get("role","part"))})
	var empty:=cache.path_join("character-root-"+str(Time.get_ticks_usec())+".glb")
	if SceneIO.make_empty(empty)!=OK:return "Cannot create the character root."
	var group: Dictionary=Model.definition(empty);var managed_group:=cache.path_join(group.sha256+".glb")
	var copy_error: String=Storage.managed_copy(empty,managed_group,group.sha256)
	DirAccess.remove_absolute(empty)
	if not copy_error.is_empty():return copy_error
	group.source=managed_group;group.name=str(options.get("name","Character")).left(200)
	var settings:=options.duplicate(true);settings.reference_id=incoming[mini(int(options.get("reference_index",0)),incoming.size()-1)].row.id
	var before: Dictionary=app.current_world().duplicate(true)
	var proposed:=Parts.assemble(before,group,incoming,int(app.video.duration_frames),settings)
	if proposed.has("error"):return proposed.error
	var warning:=""
	if options.get("fit_height",false) and str(options.get("existing_root","")).is_empty():
		var reference: Dictionary=incoming[mini(int(options.get("reference_index",0)),incoming.size()-1)].row.duplicate(true)
		reference.kind="model";reference.parent_id="";reference.start_frame=0
		var measured:=Runtime.prepare({"format":World.FORMAT,"objects":[reference]},int(app.video.duration_frames),app.video)
		if not measured.has("error"):
			add_child(measured.runtime.root);measured.runtime.evaluate(0,true,"",app.video)
			var bounds:=Bounds.query(measured.runtime.root)
			if bounds.error.is_empty() and bounds.bounds.size.y>.00001:
				var factor: float=1.8288/bounds.bounds.size.y
				if Model.scale_valid(factor):
					for row in proposed.world.objects:
						if row.id==proposed.root_id:row.metadata.character_parts.height_factor=factor;row.metadata.character_parts.reference_height_metres=bounds.bounds.size.y
			else:warning=" Height could not be measured; source size was kept."
			measured.runtime.dispose()
		else:warning=" Height could not be measured; source size was kept."
	var why: String=app.restore_world(proposed.world)
	if not why.is_empty():return why
	for path in origins:app.has_project.origins[path]=origins[path]
	app.push_history({"type":"world","before":before,"after":proposed.world.duplicate(true)});app.changed()
	app.world_selection.select_entity(proposed.root_id,false)
	app.message("Character added with %d independent parts. Move and scale its root; Manage parts controls visibility.%s" % [incoming.size(),warning])
	return ""
