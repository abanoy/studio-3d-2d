extends Node
const Document=preload("res://src/particle_document.gd")
const World=preload("res://src/world_document.gd")
const Storage=preload("res://src/storage.gd")
var app
var window: Window
var systems_list: ItemList
var instances_list: ItemList
var notice: Label
var source_label: Label
var start: SpinBox
var finish: SpinBox
var coordinates: Array=[]
var size_value: SpinBox
var seed_label: Label
var options_scroll: ScrollContainer
var seed: SpinBox
var name_edit: LineEdit
var visible: CheckButton
var prepare_button: Button
var add_button: Button
var apply_button: Button
var remove_button: Button
var selected := ""
var rows: Array=[]
var provider: Dictionary={}
var member := ""
var prepared: Dictionary={}
var job_pid := -1
var job_result := ""
var job_started := 0
var job_action := ""
var job_session := ""
var job_video: Array=[]
var job_request: Dictionary={}
var document_session := ""
var signature := ""
var presented: Dictionary={}
var dependency_root := "" # Optional local decoder override, used by isolated tests.
var import_root := "res://output/imports"
var cache_root := "res://output/particle-browser"

func open() -> void:
	if app.exporting:return
	app.stop()
	if is_instance_valid(window):window.popup_centered(Vector2i(960,650));return
	window=Window.new();window.title="Particle effects";window.exclusive=false;window.transient=true;window.min_size=Vector2i(780,560);window.theme=app.theme;app.add_child(window);window.close_requested.connect(close)
	var panel:=PanelContainer.new();panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);panel.add_theme_stylebox_override("panel",preload("res://src/studio_theme.gd").surface("f4f7fb","dce5ee"));window.add_child(panel)
	var box:=VBoxContainer.new();panel.add_child(box)
	var heading:=HBoxContainer.new();box.add_child(heading);app.label(heading,"Installed effects → your scene").size_flags_horizontal=Control.SIZE_EXPAND_FILL
	app.button(heading,"Browse installed…",func():app.source_browser.open();app.source_browser.kind.select(3);app.source_browser.filter_assets())
	app.button(heading,"Close",close)
	source_label=app.label(box,"Choose a particle file from Installed, then choose one named system.");source_label.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	var split:=HSplitContainer.new();split.size_flags_vertical=Control.SIZE_EXPAND_FILL;box.add_child(split)
	var library:=VBoxContainer.new();library.custom_minimum_size.x=330;split.add_child(library)
	app.label(library,"Systems in the selected particle file")
	systems_list=ItemList.new();systems_list.size_flags_vertical=Control.SIZE_EXPAND_FILL;systems_list.item_selected.connect(select_system);library.add_child(systems_list)
	var actions:=HFlowContainer.new();library.add_child(actions);app.button(actions,"Check systems",read_systems);prepare_button=app.button(actions,"Load selected",prepare_selected);prepare_button.disabled=true
	app.label(library,"Effects already in this scene")
	instances_list=ItemList.new();instances_list.custom_minimum_size.y=115;instances_list.item_selected.connect(select_instance);library.add_child(instances_list)
	var scroll:=ScrollContainer.new();options_scroll=scroll;scroll.horizontal_scroll_mode=ScrollContainer.SCROLL_MODE_DISABLED;scroll.size_flags_horizontal=Control.SIZE_EXPAND_FILL;split.add_child(scroll)
	var options:=VBoxContainer.new();options.size_flags_horizontal=Control.SIZE_EXPAND_FILL;scroll.add_child(options)
	app.label(options,"Name");name_edit=LineEdit.new();name_edit.max_length=256;options.add_child(name_edit)
	var timing:=HBoxContainer.new();options.add_child(timing)
	var first_box:=VBoxContainer.new();first_box.size_flags_horizontal=Control.SIZE_EXPAND_FILL;timing.add_child(first_box)
	var last_box:=VBoxContainer.new();last_box.size_flags_horizontal=Control.SIZE_EXPAND_FILL;timing.add_child(last_box)
	start=app.spin(first_box,"First frame",0,app.video.duration_frames-1,app.frame)
	finish=app.spin(last_box,"Last frame",0,app.video.duration_frames-1,app.video.duration_frames-1)
	app.button(options,"Place in current view",place_in_view)
	app.label(options,"Position (metres)");var placement:=HBoxContainer.new();options.add_child(placement)
	for title in ["X","Y","Z"]:
		var column:=VBoxContainer.new();column.size_flags_horizontal=Control.SIZE_EXPAND_FILL;placement.add_child(column)
		var value: SpinBox=app.spin(column,title,-100000,100000,0);value.step=.01;coordinates.append(value)
	visible=CheckButton.new();visible.text="Show this effect";visible.button_pressed=true;options.add_child(visible)
	size_value=app.spin(options,"Size",.01,1000,1);size_value.step=.01
	seed_label=app.label(options,"Variation seed");seed=SpinBox.new();seed.min_value=1;seed.max_value=2147483646;seed.value=17;seed.step=1;options.add_child(seed)
	seed_label.visible=app.advanced_mode;seed.visible=app.advanced_mode
	seed.tooltip_text="A fixed seed repeats reliably when seeking and exporting. Prepare again after changing it."
	var edits:=HFlowContainer.new();box.add_child(edits)
	add_button=app.button(edits,"Add effect",add_prepared);add_button.disabled=true
	apply_button=app.button(edits,"Apply changes",apply_changes);apply_button.disabled=true
	remove_button=app.button(edits,"Remove",remove_selected);remove_button.disabled=true
	app.button(edits,"Go to effect",go_to_effect)
	notice=app.label(box,"Simple sprite effects are supported first. Unsupported systems show a reason; no add-on scripts run.");notice.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	document_session=app.recovery_session;selected="";signature="";place_in_view();refresh_instances();window.popup_centered(Vector2i(960,650))

func close() -> void:
	cancel_job();prepared={};coordinates.clear()
	if is_instance_valid(window):window.hide();window.queue_free()
	window=null

func choose_file(location: Dictionary,path: String) -> void:
	open();provider=location.duplicate(true);member=path;prepared={};add_button.disabled=true;selected="";apply_button.disabled=true;remove_button.disabled=true
	sync_frame_limits()
	start.value=mini(app.frame,app.video.duration_frames-1);finish.value=app.video.duration_frames-1;visible.button_pressed=true;size_value.value=1;place_in_view()
	source_label.text=str(provider.get("label",provider.path))+"\n"+member;read_systems()

func clock() -> Array:return [app.video.fps_num,app.video.fps_den,app.video.duration_frames]

func sync_frame_limits() -> void:
	var last: int = app.video.duration_frames-1
	if start.max_value != last:
		start.max_value = last
		finish.max_value = last

func request() -> Dictionary:
	return {"provider":provider.path,"member":member,"duration":float(finish.value-start.value+1)*app.video.fps_den/app.video.fps_num,"seed":int(seed.value),"gmod":app.source_import.gmod_root,"workshop":app.source_import.workshop_root,"extra":app.source_import.extra_roots,"mount_overrides":app.source_import.mount_overrides}

func valid_frame_order() -> bool:
	if finish.value >= start.value: return true
	notice.text="Last frame must be at least %d. For a one-frame effect, use %d in both fields." % [int(start.value),int(start.value)]
	return false

func start_job(action: String) -> void:
	if provider.is_empty():notice.text="Choose a particle file first.";return
	if not valid_frame_order():return
	cancel_job();prepared={};add_button.disabled=true
	var base:=ProjectSettings.globalize_path(cache_root);DirAccess.make_dir_recursive_absolute(base)
	var stem:=base.path_join("%d_%d"%[OS.get_process_id(),Time.get_ticks_usec()]);job_result=stem+"-result.json"
	var data:=request();data["action"]=action;data["result"]=job_result
	if not dependency_root.is_empty():data["sourceio"]=dependency_root
	if action=="prepare":
		if systems_list.get_selected_items().is_empty():return
		data["system"]=rows[systems_list.get_selected_items()[0]].name;data["output"]=stem+"-prepared"
	var file:=FileAccess.open(stem+".json",FileAccess.WRITE)
	if not file:notice.text="Cannot write the particle preparation request.";return
	file.store_string(JSON.stringify(data));file.close()
	job_session=app.recovery_session;job_video=clock();job_action=action;job_request=data;job_started=Time.get_ticks_msec()
	job_pid=OS.create_process(app.source_import.python(),[ProjectSettings.globalize_path("res://tools/particle_browser.py"),stem+".json"],false)
	notice.text="Reading named systems…"if action=="list"else"Preparing the selected system and its installed material…"
	prepare_button.disabled=true
	if job_pid<0:notice.text="Cannot start the local particle worker."

func cancel_job() -> void:
	if job_pid>0 and OS.is_process_running(job_pid):OS.kill(job_pid)
	job_pid=-1

func read_systems() -> void:
	if provider.is_empty():notice.text="Choose a particle file using Browse installed.";return
	rows=[];systems_list.clear();start_job("list")

func select_system(index: int) -> void:
	if index<0 or index>=rows.size():return
	selected="";apply_button.disabled=true;remove_button.disabled=true;prepared={};add_button.disabled=true
	seed.editable=true;visible.button_pressed=true
	var row: Dictionary=rows[index];name_edit.text=row.name;notice.text=row.reason;prepare_button.disabled=job_pid>0 or not row.candidate

func prepare_selected() -> void:start_job("prepare")

func place_in_view() -> void:
	if coordinates.size()!=3:return
	var point: Vector3=app.renderer.camera.global_position-app.renderer.camera.global_basis.z*3.
	for i in range(3):coordinates[i].value=point[i]

func effect_rows() -> Array:
	return app.renderer.world_runtime.data.get("effects",[])if app.renderer.world_runtime else []

func select_id(identity: String) -> void:
	refresh_instances()
	for i in range(instances_list.item_count):
		if str(instances_list.get_item_metadata(i))==identity:select_instance(i);instances_list.select(i);return

func refresh_instances() -> void:
	if not is_instance_valid(window):return
	instances_list.clear();var index:=0;var found:=false
	for row in effect_rows():
		instances_list.add_item(row.name+"  ·  "+frame_span(row));instances_list.set_item_metadata(index,row.id)
		if row.id==selected:instances_list.select(index);found=true
		index+=1
	if not found:selected="";apply_button.disabled=true;remove_button.disabled=true
	elif not selected_row().is_empty():load_instance_fields(selected_row())

func selected_row() -> Dictionary:
	for row in effect_rows():
		if row.id==selected:return row.duplicate(true)
	return {}

func frame_span(row: Dictionary) -> String:
	var first := int(row.start_frame)
	var last := int(row.end_frame)-1
	return "Frame %d" % first if first==last else "Frames %d–%d" % [first,last]

func select_instance(index: int) -> void:
	selected=str(instances_list.get_item_metadata(index));var row:=selected_row()
	if row.is_empty():return
	load_instance_fields(row)
	apply_button.disabled=false;remove_button.disabled=false;app.world_selection.clear();notice.text="Adjust placement or timing, then Apply changes. Undo restores the previous state."

func load_instance_fields(row: Dictionary) -> void:
	name_edit.text=row.name;start.value=row.start_frame;finish.value=row.end_frame-1;visible.button_pressed=row.visible;size_value.value=row.scale
	for i in range(3):coordinates[i].value=row.position[i]
	seed.editable=false
	if app.renderer.world_runtime and app.renderer.world_runtime.effects.has(row.id):seed.value=app.renderer.world_runtime.effects[row.id].data.get("seed",17)
	presented={"id":row.id,"name":name_edit.text,"scale":size_value.value,"position":[coordinates[0].value,coordinates[1].value,coordinates[2].value]}

func read_fields(row: Dictionary) -> Dictionary:
	var existing: bool=presented.get("id","")==row.id
	if not existing or name_edit.text!=presented.name:row.name=name_edit.text.strip_edges()
	if not existing or size_value.value!=presented.scale:row.scale=size_value.value
	for i in range(3):
		if not existing or coordinates[i].value!=presented.position[i]:row.position[i]=coordinates[i].value
	row.start_frame=int(start.value);row.end_frame=int(finish.value)+1;row.visible=visible.button_pressed;return row

func commit(before: Dictionary,after: Dictionary) -> String:
	if app.exporting or app.source_import.pid>0:return "Wait for the current operation to finish."
	var live: Dictionary=app.physics_editor.import_intents()
	if not app.physics_editor.freeze_all():return "Finish the current physics recording first."
	app.stop();app.finish_stroke();app.pose_editor.finish_drag()
	before=app.current_world();var candidate:=before.duplicate(true);candidate.format=after.format
	if after.has("effects"):candidate["effects"]=after.effects.duplicate(true)
	else:candidate.erase("effects")
	after=candidate
	var error: String=app.restore_world(after);app.physics_editor.restore_import_intents(live)
	if not error.is_empty():return error
	app.push_history({"type":"world","before":before,"after":after});app.changed();signature="";refresh_instances();return ""

func add_prepared() -> void:
	if not valid_frame_order():return
	if prepared.is_empty() or job_session!=app.recovery_session or job_video!=clock():notice.text="Prepare this effect for the current scene and frame rate first.";return
	var row:=Document.definition(str(prepared.output).path_join("effect.json"),str(prepared.output).path_join("sprite.png"),name_edit.text)
	row=read_fields(row)
	var error:=Document.validate(row,int(app.video.duration_frames))
	if not error.is_empty():notice.text=error;return
	var cache:=ProjectSettings.globalize_path(import_root);DirAccess.make_dir_recursive_absolute(cache)
	for asset in Document.assets(row):
		var target:=cache.path_join(asset.path.get_file());error=Storage.managed_copy(asset.source,target,asset.sha256)
		if not error.is_empty():notice.text=error;return
		# Derived native data has no independent user JSON/PNG original. Linked
		# saves externalize this managed cache beside HAS, never a worker temp path.
		app.has_project.origins[target.replace("\\","/")]=target
		if target.ends_with(".json"):row.source=target
		else:row.texture_source=target
	var before: Dictionary=app.current_world();var after:=before.duplicate(true)
	if after.format==World.FORMAT:after.format=World.EFFECT_FORMAT;after["effects"]=[]
	after.effects.append(row);error=commit(before,after)
	if not error.is_empty():notice.text=error;return
	selected=row.id;refresh_instances()
	for i in range(instances_list.item_count):
		if instances_list.get_item_metadata(i)==selected:select_instance(i)
	notice.text="Added "+row.name+". "+frame_span(row)+". Play the timeline or Go to effect to preview it."

func apply_changes() -> void:
	var row:=selected_row()
	if row.is_empty():return
	if not valid_frame_order():return
	var updated:=read_fields(row.duplicate(true))
	if updated==row:
		notice.text="These effect settings are already applied."
		return
	var before: Dictionary=app.current_world();var after:=before.duplicate(true)
	for i in range(after.effects.size()):
		if after.effects[i].id==selected:after.effects[i]=updated
	var error:=commit(before,after);notice.text="Effect updated. Undo restores it."if error.is_empty()else error

func remove_selected() -> void:
	if selected_row().is_empty():return
	var before: Dictionary=app.current_world();var after:=before.duplicate(true);after.effects=after.effects.filter(func(row):return row.id!=selected)
	if after.effects.is_empty():after.erase("effects");after.format=World.FORMAT
	var error:=commit(before,after);notice.text="Effect removed. Undo restores it."if error.is_empty()else error

func go_to_effect() -> void:
	var row:=selected_row()
	if not row.is_empty():app.set_frame(mini(int(row.end_frame)-1,int(row.start_frame)+1))

func _process(_delta: float) -> void:
	if not is_instance_valid(window):return
	sync_frame_limits()
	seed_label.visible=app.advanced_mode;seed.visible=app.advanced_mode
	if not prepared.is_empty() and selected.is_empty() and (int(seed.value)!=int(job_request.seed) or absf(float(finish.value-start.value+1)*app.video.fps_den/app.video.fps_num-float(job_request.duration))>.000001):
		prepared={};add_button.disabled=true;notice.text="Timing or variation changed. Load the selected system again."
	if document_session!=app.recovery_session:
		cancel_job();prepared={};rows=[];systems_list.clear();selected="";document_session=app.recovery_session;add_button.disabled=true;prepare_button.disabled=true;signature="";notice.text="Scene changed. Choose and prepare an effect for this scene."
		start.value=app.frame;finish.value=finish.max_value
	var current:=JSON.stringify(effect_rows())
	if current!=signature:signature=current;refresh_instances()
	if job_pid<=0:return
	if Time.get_ticks_msec()-job_started>65000:cancel_job();notice.text="Particle preparation stopped after its time limit. Current scene preserved.";return
	if OS.is_process_running(job_pid):return
	job_pid=-1
	if job_session!=app.recovery_session or job_video!=clock():notice.text="The scene or frame rate changed. Check systems again.";return
	var file:=FileAccess.open(job_result,FileAccess.READ);var value=JSON.parse_string(file.get_as_text())if file and file.get_length()<=1024*1024 else null
	if not value is Dictionary or not value.get("ok",false):notice.text=str(value.get("error","Particle worker did not complete; current scene preserved."))if value is Dictionary else"Particle worker did not complete; current scene preserved.";return
	if job_action=="list":
		rows=value.systems;systems_list.clear()
		rows.sort_custom(func(a,b):return str(a.name).naturalnocasecmp_to(str(b.name))<0 if a.candidate==b.candidate else a.candidate)
		for row in rows:systems_list.add_item(row.name+(""if row.candidate else" — unavailable"));systems_list.set_item_tooltip(systems_list.item_count-1,row.reason)
		notice.text="Choose a named system. Supported operators still need compatible installed materials."
	else:
		prepared=value;add_button.disabled=false;notice.text="Prepared "+str(value.system)+". Review placement and timing, then Add effect."
	if not systems_list.get_selected_items().is_empty():prepare_button.disabled=not rows[systems_list.get_selected_items()[0]].candidate

func _exit_tree() -> void:cancel_job()
