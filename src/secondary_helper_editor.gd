extends Node
# User-reviewed derived asset revision. Original meshes/weights remain immutable.
const Model=preload("res://src/model.gd")
const Storage=preload("res://src/storage.gd")
const Labels=preload("res://src/bone_labels.gd")
var app
var button: Button
var window: Window
var parts: ItemList
var anchors: OptionButton
var info: Label
var apply_button: Button
var details: VBoxContainer
var scroll: ScrollContainer
var point_choice: OptionButton
var fields: Array[SpinBox]=[]
var assessment: Dictionary={}
var preview: Dictionary={}
var request: Dictionary={}
var target_id:=""
var source:=""
var revision:=-1
var pid:=-1
var stage:=""
var folder:=""
var deadline:=0
var changing:=false
var applying:=false
var before_world: Dictionary={}
var last_advanced:=false
var patch_toggle: CheckButton
var patch_operation: OptionButton
var patch_controls: HBoxContainer
var patch_hint: Label
var projected_vertices: Array=[]
var box_start:=Vector2.ZERO
var box_end:=Vector2.ZERO
var box_dragging:=false

func setup(parent: Node) -> void:
	button=app.icon_button(parent,"Set up loose parts","scene",open,"Review a connected hair/clothing region and attachment, then add weighted joints to a new HAS asset. Existing authored springs take priority.")
	app.renderer.assets_changed.connect(func():
		if not applying:close())

func actor() -> RefCounted:
	return app.renderer.world_runtime.instance(target_id) if app.renderer.world_runtime else app.renderer.model

func sync() -> void:
	var current: RefCounted=app.renderer.active_model()
	button.disabled=app.exporting or pid>0 or is_instance_valid(window) or current==null or current.order.is_empty() or current.data.get("kind","model")!="model" or not current.root.get_meta("has_secondary_rig",{}).get("error","").is_empty()

func open() -> void:
	if app.exporting or app.source_import.pid>0 or app.has_project.pid>0:return
	var current: RefCounted=app.renderer.active_model()
	if not current:return
	close();app.stop();app.pose_editor.finish_drag();app.finish_stroke()
	if not app.physics_editor.freeze_all():return
	target_id=current.data.id;source=ProjectSettings.globalize_path(current.data.source);revision=app.recovery_revision
	before_world=app.current_world().duplicate(true)
	request={"source_sha256":current.data.sha256,"segments":3}
	var shape_snapshot:=Model.Shape.snapshot(current.root)
	if not shape_snapshot.is_empty():request["morph_weights"]=shape_snapshot
	window=Window.new();window.title="Review loose parts";window.theme=app.theme;window.close_requested.connect(close);app.add_child(window)
	var panel:=PanelContainer.new();window.add_child(panel);panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var column:=VBoxContainer.new();panel.add_child(column)
	scroll=ScrollContainer.new();scroll.size_flags_vertical=Control.SIZE_EXPAND_FILL;scroll.horizontal_scroll_mode=ScrollContainer.SCROLL_MODE_DISABLED;column.add_child(scroll)
	var box:=VBoxContainer.new();box.size_flags_horizontal=Control.SIZE_EXPAND_FILL;scroll.add_child(box)
	info=app.label(box,"Inspecting geometry and existing weights…");info.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	parts=ItemList.new();parts.custom_minimum_size=Vector2(420,125);parts.item_selected.connect(select_part);box.add_child(parts)
	app.label(box,"Attach to")
	anchors=OptionButton.new();anchors.item_selected.connect(change_anchor);box.add_child(anchors)
	app.label(box,"Orange shows the selected area. Pale dots show the proposed joints.").autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	patch_toggle=CheckButton.new();patch_toggle.text="Choose a smaller patch";box.add_child(patch_toggle);patch_toggle.toggled.connect(patch_mode)
	patch_controls=HBoxContainer.new();box.add_child(patch_controls);patch_controls.visible=false
	patch_operation=OptionButton.new();patch_controls.add_child(patch_operation)
	for name in ["Replace patch","Add to patch","Remove from patch"]:patch_operation.add_item(name)
	app.button(patch_controls,"Whole part",reset_patch)
	patch_hint=app.label(box,"Drag a box around the patch. Front and back surfaces are included. Use Add or Remove to refine it. Escape cancels the box.");patch_hint.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;patch_hint.visible=false
	details=VBoxContainer.new();box.add_child(details);details.visible=app.advanced_mode
	app.label(details,"Joint positions (relative to attachment)")
	point_choice=OptionButton.new();details.add_child(point_choice);point_choice.item_selected.connect(func(_i):point_values())
	var row:=HBoxContainer.new();details.add_child(row)
	for axis in ["X","Y","Z"]:
		app.label(row,axis);var spin:=SpinBox.new();spin.min_value=-100000;spin.max_value=100000;spin.step=.005;spin.allow_greater=false;spin.custom_minimum_size.x=100;row.add_child(spin);fields.append(spin);spin.value_changed.connect(func(_v):change_point())
	app.button(details,"Reset proposed joints",reset_points)
	var actions:=HBoxContainer.new();column.add_child(actions);apply_button=app.button(actions,"Add joints to this part",apply);app.button(actions,"Cancel",close)
	window.popup_centered(Vector2i(470,mini(560,maxi(380,int(app.get_viewport_rect().size.y)-180))))
	window.position+=Vector2i(maxi(0,int((app.get_viewport_rect().size.x-window.size.x)/2)-12),0)
	launch("inspect")
	app.canvas.review_pointer=patch_pointer

func launch(operation: String) -> void:
	if pid>0 or not is_instance_valid(window):return
	clear_preview();stage=operation;apply_button.disabled=true;parts.mouse_filter=Control.MOUSE_FILTER_IGNORE;anchors.disabled=true
	parts.release_focus();parts.focus_mode=Control.FOCUS_NONE
	for spin in fields:spin.editable=false
	if operation=="inspect":preview={}
	info.text="Checking geometry…" if operation!="build" else "Creating a new weighted asset…"
	folder=ProjectSettings.globalize_path("res://output/helper-authoring/run_"+str(ResourceUID.create_id()))
	if DirAccess.make_dir_recursive_absolute(folder)!=OK:info.text="Cannot create the authoring folder.";return
	var f:=FileAccess.open(folder.path_join("request.json"),FileAccess.WRITE)
	if not f:info.text="Cannot save the helper request.";return
	f.store_string(JSON.stringify(request));f.close()
	pid=OS.create_process(app.source_import.python(),[ProjectSettings.globalize_path("res://tools/secondary_helper_worker.py"),source,operation,folder],false)
	deadline=Time.get_ticks_msec()+120000
	if pid<0:info.text="Cannot start the local helper worker. Check Python.";parts.mouse_filter=Control.MOUSE_FILTER_STOP

func _process(_delta: float) -> void:
	if not is_instance_valid(button):return
	sync()
	if not is_instance_valid(window):return
	if app.playing or not app.physics_editor.simulations.is_empty() or not app.physics_editor.pending.is_empty():
		close();app.message("Live motion started. Pause it and reopen loose-part review to continue.");return
	if app.exporting:close();return
	details.visible=app.advanced_mode
	if not preview.is_empty() and last_advanced!=app.advanced_mode:refresh_anchor_labels()
	if app.recovery_revision!=revision or not actor() or actor().data.sha256!=request.get("source_sha256"):
		close();app.message("The scene changed. Open loose-part review again for the current model.");return
	if pid>0:
		if OS.is_process_running(pid):
			if Time.get_ticks_msec()>deadline:close();app.message("Loose-part preparation timed out; the original model was kept.")
			return
		pid=-1
		var path:=folder.path_join("result.json");var file:=FileAccess.open(path,FileAccess.READ)
		var result=JSON.parse_string(file.get_as_text()) if file and file.get_length()<=4*1024*1024 else null
		if not result is Dictionary or not result.get("ok",false):
			info.text=str(result.get("error","Helper worker ended without a result")) if result is Dictionary else "Helper worker ended without a result."
			parts.mouse_filter=Control.MOUSE_FILTER_STOP;parts.focus_mode=Control.FOCUS_ALL
			for spin in fields:spin.editable=true
			anchors.disabled=preview.is_empty();apply_button.disabled=stage!="build" or preview.is_empty() or not preview.get("can_apply",false);return
		completed(result.value)
	if not preview.is_empty():draw_preview()

func completed(value: Dictionary) -> void:
	parts.mouse_filter=Control.MOUSE_FILTER_STOP;parts.focus_mode=Control.FOCUS_ALL
	for spin in fields:spin.editable=true
	if stage=="inspect":
		assessment=value
		for i in range(value.regions.size()):
			var row: Dictionary=value.regions[i];var name:=Labels.standard(row.anchor_name,Labels.role(actor().data,row.anchor_name))+" area "+str(i+1)
			parts.add_item(name+(" (already set up)" if row.already_rigged else " (suggested)" if row.suggested else " (review)"))
			parts.set_item_disabled(i,row.already_rigged and not patch_toggle.button_pressed)
			parts.set_item_tooltip(i,str(int(row.vertices))+" vertices; attachment: "+str(row.anchor_name) if app.advanced_mode else "Preview this connected part before adding joints.")
		if value.regions.is_empty():info.text="No usable skinned regions found. Unskinned meshes and unsupported data still need a separate rig/region editor.";return
		var selected:=-1
		for i in range(value.regions.size()):
			if value.regions[i].already_rigged and not patch_toggle.button_pressed:continue
			if selected<0:selected=i
			if value.regions[i].suggested:selected=i;break
		if selected<0:info.text="These connected surfaces already use spring joints. Their existing setup is kept.";return
		parts.select(selected);select_part(selected)
	elif stage=="preview":
		preview=value;request["points_in_anchor"]=value.points_in_anchor.duplicate(true)
		if request.has("vertex_mask"):request.vertex_mask=Array(value.region.vertex_mask).map(func(v):return int(v))
		anchors.clear();changing=true;var bindings: Dictionary=actor().root.get_meta("has_source_bones",{})
		for choice in value.anchors:
			var id: String=bindings.get(int(choice.node),"")
			anchors.add_item(Labels.display(choice.name,app.advanced_mode,Labels.role(actor().data,choice.name)));anchors.set_item_metadata(anchors.item_count-1,int(choice.node))
			anchors.set_item_disabled(anchors.item_count-1,id.is_empty() or not choice.get("available",false))
			if int(choice.node)==int(value.region.anchor_node):anchors.select(anchors.item_count-1)
		anchors.disabled=false;point_choice.clear()
		refresh_anchor_labels()
		for i in range(value.points_in_anchor.size()):point_choice.add_item("Joint "+str(i+1))
		point_choice.select(0);changing=false;point_values();apply_button.disabled=not value.can_apply
		info.text="Review the orange area and its attachment. Use this for flexible hair or clothing. The edge stays attached; Undo restores the original."
		if app.advanced_mode:info.text+=" "+str(int(value.region.vertices))+" vertices; "+str(int(value.region.attachment_vertices))+" pinned."
		if not assessment.get("skipped",[]).is_empty():info.text+=" Some sections could not be assessed."
		if not value.can_apply:info.text="This patch includes existing motion joints. Refine it to an unrigged area." if value.region.already_rigged else "Choose an available attachment in Attach to, or refine the patch."
	elif stage=="build":install(value)

func refresh_anchor_labels() -> void:
	last_advanced=app.advanced_mode
	for i in range(preview.anchors.size()):
		var choice: Dictionary=preview.anchors[i];var name:=Labels.display(choice.name,app.advanced_mode,Labels.role(actor().data,choice.name))
		if name=="Other part":name+=" "+str(i+1)
		anchors.set_item_text(i,name)

func select_part(index: int) -> void:
	if pid>0 or assessment.regions[index].already_rigged and not patch_toggle.button_pressed:return
	var row: Dictionary=assessment.regions[index]
	var shape_snapshot: Dictionary=request.get("morph_weights",{}).duplicate(true)
	request={"source_sha256":request.source_sha256,"segments":3,"node":int(row.node),"primitive":int(row.primitive),"component":int(row.component),"anchor_node":int(row.anchor_node)}
	if not shape_snapshot.is_empty():request["morph_weights"]=shape_snapshot
	request["review_only"]=true
	launch("preview")

func patch_mode(enabled: bool) -> void:
	cancel_patch_drag()
	patch_controls.visible=enabled;patch_hint.visible=enabled
	if assessment.is_empty():return
	for i in range(assessment.regions.size()):parts.set_item_disabled(i,assessment.regions[i].already_rigged and not enabled)
	if enabled and preview.is_empty():
		parts.select(0);select_part(0)

func reset_patch() -> void:
	if pid>0 or preview.is_empty():return
	request.erase("vertex_mask");request.erase("points_in_anchor");launch("preview")

func reset_points() -> void:
	if pid>0 or preview.is_empty():return
	request.erase("points_in_anchor");launch("preview")

func patch_pointer(event: InputEventMouse,point: Vector2) -> bool:
	if not is_instance_valid(window) or not patch_toggle.button_pressed:return false
	if event.ctrl_pressed:return false
	if app.navigating or app.pose_editor.dragging or app.playing:return false
	if event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT:
		if event.pressed and pid<=0 and not preview.is_empty():
			box_start=point;box_end=point;box_dragging=true;app.canvas.grab_focus();draw_patch_box()
		return true
	return false

func global_patch_event(event: InputEvent) -> bool:
	if not box_dragging:return false
	if event is InputEventKey and event.pressed and event.keycode==KEY_ESCAPE:cancel_patch_drag();return true
	if event is InputEventMouseMotion or event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT and not event.pressed:
		var local: Vector2=app.canvas.get_global_transform_with_canvas().affine_inverse()*event.position
		var rect: Rect2=app.canvas.image_rect();box_end=(local-rect.position)/rect.size*Vector2(app.video.width,app.video.height);draw_patch_box()
		if event is InputEventMouseButton:finish_patch_box()
		return true
	return false

func draw_patch_box() -> void:
	app.canvas.review_box=Rect2(box_start,box_end-box_start).abs();app.canvas.review_box_visible=box_dragging;app.canvas.queue_redraw()

func cancel_patch_drag() -> void:
	box_dragging=false
	if is_instance_valid(app.canvas):app.canvas.review_box_visible=false;app.canvas.queue_redraw()

func finish_patch_box() -> void:
	var rect:=Rect2(box_start,box_end-box_start).abs();cancel_patch_drag()
	if rect.size.x<4 or rect.size.y<4 or preview.is_empty():return
	var mask: Dictionary={}
	if patch_operation.selected!=0:
		for v in request.get("vertex_mask",preview.source_vertices):mask[int(v)]=true
	for i in range(projected_vertices.size()):
		if projected_vertices[i]!=null and rect.has_point(projected_vertices[i]):
			var v:=int(preview.source_vertices[i])
			if patch_operation.selected==2:mask.erase(v)
			else:mask[v]=true
	var values: Array=mask.keys();values.sort();request["vertex_mask"]=values;request.erase("points_in_anchor");launch("preview")

func change_anchor(index: int) -> void:
	if changing or pid>0:return
	request.anchor_node=anchors.get_item_metadata(index);request.erase("points_in_anchor");launch("preview")

func point_values() -> void:
	if request.get("points_in_anchor",[]).is_empty():return
	changing=true;var p: Array=request.points_in_anchor[point_choice.selected]
	for axis in range(3):fields[axis].set_value_no_signal(p[axis])
	changing=false

func change_point() -> void:
	if changing or pid>0 or preview.is_empty() or not request.has("points_in_anchor"):return
	request.points_in_anchor[point_choice.selected]=[fields[0].value,fields[1].value,fields[2].value]

func draw_preview() -> void:
	var current: RefCounted=actor();var bindings: Dictionary=current.root.get_meta("has_source_bones",{});var transforms:={};var camera: Camera3D=app.renderer.camera
	for row in preview.anchors:
		var id: String=bindings.get(int(row.node),"")
		if current.bones.has(id):transforms[int(row.node)]=current.bone_transform(id)
	var vertices: Array=[]
	projected_vertices=[]
	for vertex in preview.vertices:
		var p:=Vector3.ZERO
		for influence in vertex:
			if not transforms.has(int(influence[0])):clear_preview();return
			p+=(transforms[int(influence[0])]*Vector3(influence[1],influence[2],influence[3]))*float(influence[4])
		vertices.append(p)
		projected_vertices.append(null if camera.is_position_behind(p) else camera.unproject_position(p))
	var lines:=PackedVector2Array();var chain:=PackedVector2Array()
	for edge in preview.edges:
		var a: Vector3=vertices[int(edge[0])];var b: Vector3=vertices[int(edge[1])]
		if not camera.is_position_behind(a) and not camera.is_position_behind(b):lines.append(camera.unproject_position(a));lines.append(camera.unproject_position(b))
	var transform: Transform3D=transforms.get(int(preview.region.anchor_node),Transform3D.IDENTITY)
	for point in request.get("points_in_anchor",preview.points_in_anchor):
		var p:=transform*Vector3(point[0],point[1],point[2])
		if camera.is_position_behind(p):chain.clear();break
		chain.append(camera.unproject_position(p))
	app.canvas.review_lines=lines;app.canvas.review_chain=chain;app.canvas.queue_redraw()

func apply() -> void:
	if preview.is_empty() or not preview.get("can_apply",false) or pid>0 or app.exporting:return
	request["reviewed"]=true;launch("build")

func install(value: Dictionary) -> void:
	app.pose_editor.finish_drag();app.finish_stroke()
	if app.recovery_revision!=revision or app.current_world()!=before_world:close();app.message("The scene changed during preparation. Original and current edits were kept; open review again.");return
	var before: Dictionary=app.current_world();var after:=before.duplicate(true);var row: Dictionary={}
	for item in after.objects:
		if item.id==target_id:row=item;break
	if row.is_empty():close();return
	var sha:=FileAccess.get_sha256(value.glb);var managed:=ProjectSettings.globalize_path("res://output/imports").path_join(sha+".glb")
	var error:=Storage.managed_copy(value.glb,managed,sha)
	if not error.is_empty():info.text=error;return
	row.source=managed;row.sha256=sha;row.metadata["generated_helpers"]=value.report
	var stored_lineage=row.metadata.get("generated_helper_history",[])
	if not stored_lineage is Array or stored_lineage.size()>=128:info.text="The stored helper history needs review. Current model kept.";return
	var lineage: Array=stored_lineage.duplicate(true)
	if lineage.is_empty():
		for old in before.objects:
			if old.id==target_id and old.metadata.has("generated_helpers"):lineage.append(old.metadata.generated_helpers.duplicate(true))
	lineage.append(value.report.duplicate(true));row.metadata["generated_helper_history"]=lineage
	clear_preview();applying=true;error=app.restore_world(after);applying=false
	if not error.is_empty():info.text="The new rig could not preserve existing bindings. Original kept. "+error;return
	app.has_project.origins[managed.replace("\\","/")]=str(value.glb);app.push_history({"type":"world","before":before,"after":after});app.changed();close()
	app.message("Added weighted joints to the reviewed part. The original is kept; Undo restores it. Hair & clothes can now use the new chain.")

func clear_preview() -> void:
	if is_instance_valid(app.canvas):app.canvas.review_lines=PackedVector2Array();app.canvas.review_chain=PackedVector2Array();app.canvas.queue_redraw()

func close() -> void:
	cancel_patch_drag()
	if is_instance_valid(app.canvas):app.canvas.review_pointer=Callable()
	if pid>0 and OS.is_process_running(pid):OS.kill(pid)
	pid=-1;clear_preview()
	if is_instance_valid(window):window.hide();window.queue_free()
	window=null;preview={};assessment={};request={};fields.clear();target_id=""

func _exit_tree() -> void:close()
