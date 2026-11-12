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
var prefer_loose:=false
var existing_toggle: CheckButton
var mode_choice:="auto"
var selected_key:=""
var part_press:=false
var include_toggle: CheckButton
var include_status: Label
var included: Dictionary={}
var part_names: Array[String]=[]
var point_review_after:=0
var pending_install: Dictionary={}
var restore_list_focus:=false
var source_stamp:=0
var inclusion_navigation:=false
var preview_ready:=false

func setup(parent: Node) -> void:
	button=app.icon_button(parent,"Set up loose parts","scene",open,"Review a connected hair/clothing region and attachment, then add weighted joints to a new HAS asset. Existing authored springs take priority.")
	app.renderer.assets_changed.connect(func():
		if not applying:close())

func actor() -> RefCounted:
	return app.renderer.world_runtime.instance(target_id) if app.renderer.world_runtime else app.renderer.model

func sync() -> void:
	var current: RefCounted=app.renderer.active_model()
	button.disabled=app.exporting or pid>0 or is_instance_valid(window) or current==null or current.order.is_empty() or current.data.get("kind","model")!="model" or not current.root.get_meta("has_secondary_rig",{}).get("error","").is_empty()

func open(prefer_hair_clothing:=false) -> void:
	if app.exporting or app.source_import.pid>0 or app.has_project.pid>0:return
	var current: RefCounted=app.renderer.active_model()
	if not current:return
	close();prefer_loose=prefer_hair_clothing;app.stop();app.pose_editor.finish_drag();app.finish_stroke()
	if not app.physics_editor.freeze_all():return
	target_id=current.data.id;source=ProjectSettings.globalize_path(current.data.source);revision=app.recovery_revision
	source_stamp=FileAccess.get_modified_time(source)
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
	parts=ItemList.new();parts.custom_minimum_size=Vector2(420,125);parts.item_selected.connect(select_part);parts.gui_input.connect(include_key);box.add_child(parts)
	include_toggle=CheckButton.new();include_toggle.text="Include in setup";include_toggle.toggled.connect(include_part);box.add_child(include_toggle)
	include_toggle.tooltip_text="Check several reviewed parts to set them up together. Clicking a list row only changes the part in view. Space toggles this check when the list has focus."
	app.label(box,"Attach to")
	anchors=OptionButton.new();anchors.item_selected.connect(change_anchor);box.add_child(anchors)
	existing_toggle=CheckButton.new();existing_toggle.text="Use existing joints";existing_toggle.visible=false;box.add_child(existing_toggle);existing_toggle.toggled.connect(existing_mode)
	existing_toggle.tooltip_text="Review the model's existing joint chain without replacing its weights. Shared joints can move more than one connected part."
	app.label(box,"Click a part in the scene to make a best-effort selection, or correct it in this list. Drag to navigate; Ctrl keeps camera controls.").autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
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
	include_status=app.label(column,"Include several parts to set them up together.");include_status.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	var actions:=HBoxContainer.new();column.add_child(actions);apply_button=app.button(actions,"Add joints to this part",apply);app.button(actions,"Cancel",close)
	window.popup_centered(Vector2i(470,mini(560,maxi(380,int(app.get_viewport_rect().size.y)-180))))
	window.position+=Vector2i(maxi(0,int((app.get_viewport_rect().size.x-window.size.x)/2)-12),0)
	launch("inspect")
	app.canvas.review_pointer=patch_pointer

func launch(operation: String,payload: Dictionary={}) -> void:
	if pid>0 or not is_instance_valid(window):return
	clear_preview();stage=operation;apply_button.disabled=true;parts.mouse_filter=Control.MOUSE_FILTER_IGNORE;anchors.disabled=true
	if operation in ["inspect","preview","review"]:preview_ready=false
	existing_toggle.disabled=true;include_toggle.disabled=true
	restore_list_focus=parts.has_focus() or restore_list_focus
	parts.release_focus();parts.focus_mode=Control.FOCUS_NONE
	for spin in fields:spin.editable=false
	if operation=="inspect":preview={}
	info.text="Preparing all checked parts…" if operation=="batch_build" else "Checking the original source…" if operation=="source_check" else "Creating a new weighted asset…" if operation=="build" else "Checking geometry…"
	folder=ProjectSettings.globalize_path("res://output/helper-authoring/run_"+str(ResourceUID.create_id()))
	if DirAccess.make_dir_recursive_absolute(folder)!=OK:info.text="Cannot create the authoring folder.";return
	var f:=FileAccess.open(folder.path_join("request.json"),FileAccess.WRITE)
	if not f:info.text="Cannot save the helper request.";return
	f.store_string(JSON.stringify(request if payload.is_empty() else payload,"",true,true));f.close()
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
	if inclusion_navigation!=app.navigating:
		inclusion_navigation=app.navigating;refresh_inclusions()
	if point_review_after>0 and pid<=0 and Time.get_ticks_msec()>=point_review_after:
		point_review_after=0;launch("review")
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
			restore_list_focus=false
			parts.mouse_filter=Control.MOUSE_FILTER_STOP;parts.focus_mode=Control.FOCUS_ALL
			for spin in fields:spin.editable=true
			existing_toggle.disabled=false
			anchors.disabled=preview.is_empty();apply_button.disabled=stage!="build" or preview.is_empty() or not preview.get("can_apply",false)
			refresh_inclusions();return
		completed(result.value)
	if not preview.is_empty():draw_preview()

func completed(value: Dictionary) -> void:
	parts.mouse_filter=Control.MOUSE_FILTER_STOP;parts.focus_mode=Control.FOCUS_ALL
	for spin in fields:spin.editable=true
	if stage=="inspect":
		assessment=value
		for i in range(value.regions.size()):
			var row: Dictionary=value.regions[i];var name:=Labels.standard(row.anchor_name,Labels.role(actor().data,row.anchor_name))+" area "+str(i+1)
			if not str(row.get("material_name","")).is_empty():name=str(row.material_name).left(64).capitalize()+" · "+name
			part_names.append(name+(" (already set up)" if row.already_rigged else " (suggested)" if row.suggested else " (review)"));parts.add_item(part_names[-1])
			parts.set_item_disabled(i,row.already_rigged and not patch_toggle.button_pressed)
			parts.set_item_tooltip(i,str(int(row.vertices))+" vertices; attachment: "+str(row.anchor_name) if app.advanced_mode else "Preview this connected part before adding joints.")
		if value.regions.is_empty():info.text="No usable skinned regions found. Unskinned meshes and unsupported data still need a separate rig/region editor.";return
		var selected:=-1;var priority:=-1
		for i in range(value.regions.size()):
			if value.regions[i].already_rigged and not patch_toggle.button_pressed:continue
			var score:=region_priority(value.regions[i])
			if score>priority:selected=i;priority=score
		if selected<0:info.text="These connected surfaces already use spring joints. Their existing setup is kept.";return
		parts.select(selected);parts.ensure_current_is_visible();select_part(selected)
	elif stage in ["preview","review"]:
		if smart_existing(value):
			request.erase("vertex_mask");request.erase("points_in_anchor");request["use_existing_joints"]=true;launch("preview");return
		preview=value;preview_ready=true
		var use_existing: bool=value.get("mode","")=="existing_joints"
		if use_existing:request.erase("points_in_anchor")
		else:request["points_in_anchor"]=value.points_in_anchor.duplicate(true)
		changing=true;existing_toggle.visible=value.region.has("existing_chain");existing_toggle.disabled=false;existing_toggle.set_pressed_no_signal(use_existing);changing=false
		patch_toggle.disabled=use_existing
		if use_existing:patch_toggle.set_pressed_no_signal(false);patch_controls.visible=false;patch_hint.visible=false
		apply_button.text="Enable these existing joints" if use_existing else "Add joints to this part"
		if request.has("vertex_mask"):request.vertex_mask=Array(value.region.vertex_mask).map(func(v):return int(v))
		anchors.clear();changing=true;var bindings: Dictionary=actor().root.get_meta("has_source_bones",{})
		for choice in value.anchors:
			var id: String=bindings.get(int(choice.node),"")
			anchors.add_item(Labels.display(choice.name,app.advanced_mode,Labels.role(actor().data,choice.name)));anchors.set_item_metadata(anchors.item_count-1,int(choice.node))
			anchors.set_item_disabled(anchors.item_count-1,id.is_empty() or not choice.get("available",false))
			if int(choice.node)==int(value.region.anchor_node):anchors.select(anchors.item_count-1)
		anchors.disabled=use_existing;point_choice.clear()
		refresh_anchor_labels()
		for i in range(value.points_in_anchor.size()):
			var name: String="Joint "+str(i+1)
			if use_existing:name="Endpoint" if i==value.points_in_anchor.size()-1 else str(value.existing_chain.joint_names[i]).replace("_"," ").capitalize()
			point_choice.add_item(name)
		point_choice.select(0);changing=false;point_values();apply_button.disabled=not value.can_apply
		for spin in fields:spin.editable=not use_existing
		info.text="Review the orange area and its attachment. Use this for flexible hair or clothing. The edge stays attached; Undo restores the original."
		if app.advanced_mode:info.text+=" "+str(int(value.region.vertices))+" vertices; "+str(int(value.region.attachment_vertices))+" pinned."
		if not assessment.get("skipped",[]).is_empty():info.text+=" Some sections could not be assessed."
		if not value.can_apply:info.text="This patch includes existing motion joints. Refine it to an unrigged area." if value.region.already_rigged else "Choose an available attachment in Attach to, or refine the patch."
		if not use_existing and value.region.has("existing_chain") and not value.can_apply:info.text="This part spans existing joints. Turn on Use existing joints to review the shared chain without changing its weights."
		if use_existing:
			var names: Array=[]
			for name in value.existing_chain.joint_names:names.append(str(name).replace("_"," ").capitalize())
			info.text="Review: "+", ".join(names)+" and the pale endpoint. This moves "+str(value.affected_regions.size())+" connected regions ("+str(int(value.affected_vertices))+" weighted vertices). Orange shows all shared regions. Original weights and poses are kept; Undo removes this setup."
		cache_included(value);refresh_inclusions()
		if restore_list_focus and not app.navigating:parts.grab_focus()
		restore_list_focus=false
	elif stage=="batch_build":
		pending_install=value
		launch("source_check",{"source_sha256":request.source_sha256,"source_stamp_ns":value.batch.source_stamp_ns})
	elif stage=="source_check":install(pending_install)
	elif stage=="build":install(value)

func region_priority(row: Dictionary) -> int:
	var weighted: bool=float(row.get("anchor_min_weight",0))>=0.01
	var result: int=(2 if row.suggested else 0)+(1 if weighted else 0)
	# Source labels only choose the initial preview; every region stays selectable
	# and generation still requires the artist's explicit reviewed Apply.
	if prefer_loose and weighted:
		var hint: String=(str(row.get("material_name",""))+" "+str(row.anchor_name)).to_lower()
		for word in ["hair","ribbon","skirt","cloth","cape","sleeve"]:
			if word in hint:return result+4
	return result

func region_key(row: Dictionary) -> String:
	return "%d:%d:%d"%[int(row.node),int(row.primitive),int(row.component)]

func included_key(key: String) -> String:
	for group in included:
		if key in included[group].source_keys:return group
	return ""

func proposal_entry(value: Dictionary) -> Dictionary:
	var group: String="part:"+selected_key;var keys: Array=[selected_key]
	if value.get("mode","")=="existing_joints":
		var nodes:=PackedStringArray()
		for node in value.existing_chain.joint_nodes:nodes.append(str(int(node)))
		group="native:%d:%s"%[int(value.existing_chain.center_node),",".join(nodes)];keys=[]
		for row in value.affected_regions:keys.append(region_key(row))
	var reviewed:=request.duplicate(true);reviewed["reviewed"]=true
	return {"group":group,"focus_key":selected_key,"source_keys":keys,"request":reviewed,"valid":value.get("can_apply",false),"mode":value.get("mode","weighted")}

func cache_included(value: Dictionary) -> void:
	var old:=included_key(selected_key)
	if old.is_empty():return
	if not value.get("can_apply",false):included[old].valid=false;return
	var entry:=proposal_entry(value)
	if old!=entry.group:included.erase(old)
	included[entry.group]=entry

func queue_changed() -> bool:
	var group:=included_key(selected_key)
	if group.is_empty():return false
	included[group].request=request.duplicate(true);included[group].request["reviewed"]=true;included[group].valid=false
	refresh_inclusions();return true

func preview_operation() -> String:
	return "review" if not included_key(selected_key).is_empty() else "preview"

func include_part(enabled: bool) -> void:
	if changing:return
	if pid>0 or app.navigating:refresh_inclusions();return
	var group:=included_key(selected_key)
	if not enabled:
		included.erase(group);point_review_after=0;refresh_inclusions();return
	if not preview_ready or preview.is_empty() or not preview.get("can_apply",false):refresh_inclusions();return
	var entry:=proposal_entry(preview);entry.valid=false;included[entry.group]=entry
	refresh_inclusions();launch("review")

func include_key(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.keycode==KEY_SPACE and parts.has_focus() and pid<=0 and not app.navigating and not app.playing and not include_toggle.disabled:
		include_toggle.button_pressed=not include_toggle.button_pressed;parts.accept_event()

func refresh_inclusions() -> void:
	if not is_instance_valid(include_toggle) or not is_instance_valid(apply_button):return
	var current:=included_key(selected_key);var pending:=0;var areas: Dictionary={}
	for group in included:
		if not included[group].valid:pending+=1
		for key in included[group].source_keys:areas[key]=true
	changing=true;include_toggle.set_pressed_no_signal(not current.is_empty());changing=false
	include_toggle.disabled=pid>0 or app.navigating or current.is_empty() and (not preview_ready or preview.is_empty() or not preview.get("can_apply",false))
	include_toggle.tooltip_text="Included shared group: these "+str(included[current].source_keys.size())+" areas move together. Unchecking removes the whole group; individual exclusion needs different weights." if not current.is_empty() and included[current].mode=="existing_joints" else "Check several reviewed parts to set them up together. Clicking a row only changes the part in view. Space toggles this check when the list has focus."
	for i in range(mini(part_names.size(),assessment.get("regions",[]).size())):
		var group:=included_key(region_key(assessment.regions[i]))
		parts.set_item_text(i,(("✓ " if included[group].valid else "? ") if not group.is_empty() else "")+part_names[i])
	if included.is_empty():
		include_status.text="Include several parts to set them up together."
		apply_button.text="Enable these existing joints" if preview.get("mode","")=="existing_joints" else "Add joints to this part"
		apply_button.disabled=pid>0 or not preview_ready or preview.is_empty() or not preview.get("can_apply",false)
	else:
		include_status.text=str(included.size())+" checked setup"+("s" if included.size()!=1 else "")+" · "+str(areas.size())+" connected area"+("s" if areas.size()!=1 else "")+(" · "+str(pending)+" needs review" if pending>0 else " · reviewed")
		apply_button.text="Set up "+str(included.size())+" checked part"+("s" if included.size()!=1 else "")
		apply_button.disabled=pid>0 or pending>0 or point_review_after>0

func refresh_anchor_labels() -> void:
	last_advanced=app.advanced_mode
	for i in range(preview.anchors.size()):
		var choice: Dictionary=preview.anchors[i];var name:=Labels.display(choice.name,app.advanced_mode,Labels.role(actor().data,choice.name))
		if name=="Other part":name+=" "+str(i+1)
		anchors.set_item_text(i,name)

func select_part(index: int) -> void:
	if pid>0 or index<0 or index>=assessment.get("regions",[]).size() or assessment.regions[index].already_rigged and not patch_toggle.button_pressed:return
	var row: Dictionary=assessment.regions[index]
	point_review_after=0
	var key:=region_key(row)
	var keep_existing: bool=key==selected_key and preview.get("mode","")=="existing_joints"
	if key!=selected_key:mode_choice="auto"
	selected_key=key;parts.select(index);parts.ensure_current_is_visible()
	var group:=included_key(key)
	if not group.is_empty():
		request=included[group].request.duplicate(true);included[group].valid=false
		mode_choice="existing" if request.get("use_existing_joints",false) else "weighted"
		patch_toggle.set_pressed_no_signal(request.has("vertex_mask"));patch_controls.visible=patch_toggle.button_pressed;patch_hint.visible=patch_toggle.button_pressed
		refresh_inclusions();launch("review");return
	var shape_snapshot: Dictionary=request.get("morph_weights",{}).duplicate(true)
	request={"source_sha256":request.source_sha256,"segments":3,"node":int(row.node),"primitive":int(row.primitive),"component":int(row.component),"anchor_node":int(row.anchor_node)}
	if not shape_snapshot.is_empty():request["morph_weights"]=shape_snapshot
	if mode_choice=="existing" or mode_choice=="auto" and keep_existing:request["use_existing_joints"]=true
	request["review_only"]=true
	refresh_inclusions();launch("preview")

func existing_mode(enabled: bool) -> void:
	if changing or pid>0 or not request.has("node"):return
	mode_choice="existing" if enabled else "weighted"
	request.erase("vertex_mask");request.erase("points_in_anchor")
	if enabled:request["use_existing_joints"]=true
	else:
		request.erase("use_existing_joints")
		for row in assessment.get("regions",[]):
			if region_key(row)==selected_key:
				for key in ["node","primitive","component","anchor_node"]:request[key]=int(row[key])
				break
	queue_changed();launch(preview_operation())

func smart_existing(value: Dictionary) -> bool:
	if app.advanced_mode or mode_choice!="auto" or patch_toggle.button_pressed or value.get("mode","")=="existing_joints" or value.get("can_apply",false) or not value.get("region",{}).has("existing_chain"):return false
	var current: RefCounted=actor()
	if not current:return false
	var bindings: Dictionary=current.root.get_meta("has_source_bones",{})
	for choice in value.get("anchors",[]):
		if choice.get("available",false) and not str(bindings.get(int(choice.node),"")).is_empty():return false
	var proposal: Dictionary=value.region.existing_chain
	for node in [proposal.center_node]+proposal.joint_nodes:
		var id: String=bindings.get(int(node),"")
		if id.is_empty() or not current.bones.has(id):return false
	return true

static func ray_region(rows: Array,transforms: Dictionary,origin: Vector3,direction: Vector3,distance_limit:=1000.0) -> int:
	if not origin.is_finite() or not direction.is_finite() or direction.length_squared()<0.0000000001 or not is_finite(distance_limit) or distance_limit<=0:return -1
	var finish:=origin+direction.normalized()*distance_limit;var best:=-1;var depth:=INF;var volume:=INF
	for i in range(rows.size()):
		if not rows[i] is Dictionary:continue
		var row: Dictionary=rows[i];var bounds=row.get("bounds_in_anchor",[]);var node:=int(row.get("anchor_node",-1))
		if not transforms.has(node) or not transforms[node] is Transform3D or not bounds is Array or bounds.size()!=2:continue
		if not bounds[0] is Array or not bounds[1] is Array or bounds[0].size()!=3 or bounds[1].size()!=3:continue
		var lower:=Vector3(bounds[0][0],bounds[0][1],bounds[0][2]);var upper:=Vector3(bounds[1][0],bounds[1][1],bounds[1][2]);var extent:=upper-lower
		var transform: Transform3D=transforms[node]
		if not lower.is_finite() or not upper.is_finite() or extent.x<0 or extent.y<0 or extent.z<0 or not transform.is_finite() or absf(transform.basis.determinant())<1e-30:continue
		var padding:=maxf(maxf(extent.x,maxf(extent.y,extent.z))*.01,.00001)
		var box:=AABB(lower,extent).grow(padding);var inverse:=transform.affine_inverse();var hit=box.intersects_segment(inverse*origin,inverse*finish)
		if not hit is Vector3:continue
		var current_depth: float=origin.distance_to(transform*hit);var current_volume: float=box.get_volume()*absf(transform.basis.determinant())
		if current_depth<depth-.00001 or absf(current_depth-depth)<=.00001 and current_volume<volume:
			best=i;depth=current_depth;volume=current_volume
	return best

func guess_part(point: Vector2) -> int:
	if not app.canvas.scene_contains(point) or assessment.is_empty():return -1
	var current: RefCounted=actor()
	if not current:return -1
	var transforms:={};var bindings: Dictionary=current.root.get_meta("has_source_bones",{})
	for row in assessment.get("regions",[]):
		var node:=int(row.anchor_node);var id: String=bindings.get(node,"")
		if not transforms.has(node) and current.bones.has(id):transforms[node]=current.bone_transform(id)
	var camera: Camera3D=app.renderer.camera
	return ray_region(assessment.get("regions",[]),transforms,camera.project_ray_origin(point),camera.project_ray_normal(point),camera.far)

func choose_part(point: Vector2) -> void:
	if pid>0:return
	var index:=guess_part(point)
	if index<0:info.text="No part was found there. Try another point or choose from the list.";return
	if assessment.regions[index].already_rigged and not patch_toggle.button_pressed:
		var row: Dictionary=assessment.regions[index]
		selected_key="%d:%d:%d"%[int(row.node),int(row.primitive),int(row.component)];mode_choice="auto"
		parts.deselect_all();parts.select(index);parts.ensure_current_is_visible()
		clear_preview();preview={};preview_ready=false;apply_button.disabled=true;anchors.clear();anchors.disabled=true;existing_toggle.visible=false;patch_toggle.disabled=false
		for field in fields:field.editable=false
		refresh_inclusions();info.text="That area already has motion joints. Its setup is kept. Choose a smaller patch to review an unconfigured section, or choose another part.";return
	select_part(index)

func part_pointer(event: InputEventMouse,point: Vector2) -> bool:
	if not is_instance_valid(window) or app.playing or app.pose_editor.dragging:return false
	if event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT:
		if event.pressed:
			if event.ctrl_pressed or app.navigating or not app.canvas.scene_contains(point):return false
			part_press=true;app.canvas.grab_focus();app.world_selection.input(event,point);return true
		if part_press:
			part_press=false
			if app.navigating or app.camera_buttons!=0:app.world_selection.input(event,point)
			else:
				app.world_selection.cancel_gesture(true)
				if not event.ctrl_pressed:choose_part(point)
			return true
	if part_press:
		if event is InputEventMouseButton and event.button_index not in [MOUSE_BUTTON_LEFT,MOUSE_BUTTON_RIGHT,MOUSE_BUTTON_MIDDLE]:return false
		app.world_selection.input(event,point);return true
	return false

func patch_mode(enabled: bool) -> void:
	cancel_patch_drag()
	patch_controls.visible=enabled;patch_hint.visible=enabled
	if assessment.is_empty():return
	for i in range(assessment.regions.size()):parts.set_item_disabled(i,assessment.regions[i].already_rigged and not enabled)
	if enabled and preview.is_empty():
		var selected:=0
		for i in range(assessment.regions.size()):
			var row: Dictionary=assessment.regions[i]
			if selected_key=="%d:%d:%d"%[int(row.node),int(row.primitive),int(row.component)]:selected=i;break
		parts.select(selected);select_part(selected)

func reset_patch() -> void:
	if pid>0 or preview.is_empty():return
	request.erase("vertex_mask");request.erase("points_in_anchor");queue_changed();launch(preview_operation())

func reset_points() -> void:
	if pid>0 or preview.is_empty():return
	request.erase("points_in_anchor");queue_changed();launch(preview_operation())

func patch_pointer(event: InputEventMouse,point: Vector2) -> bool:
	if not is_instance_valid(window):return false
	if not patch_toggle.button_pressed:return part_pointer(event,point)
	if event.ctrl_pressed:return false
	if app.navigating or app.pose_editor.dragging or app.playing:return false
	if event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT:
		if event.pressed and pid<=0 and not preview.is_empty():
			box_start=point;box_end=point;box_dragging=true;app.canvas.grab_focus();draw_patch_box()
		return true
	return false

func global_patch_event(event: InputEvent) -> bool:
	if part_press:
		if event is InputEventKey and event.pressed and event.keycode==KEY_ESCAPE:
			part_press=false;app.world_selection.cancel_gesture(true);return not app.navigating
		if event is InputEventMouse:
			var local: Vector2=app.canvas.get_global_transform_with_canvas().affine_inverse()*event.position
			var image: Rect2=app.canvas.image_rect()
			var point: Vector2=(local-image.position)/image.size*Vector2(app.video.width,app.video.height)
			if not app.canvas.get_global_rect().has_point(event.position) and event is InputEventMouseButton and not event.pressed:point=Vector2(-1,-1)
			return part_pointer(event,point)
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
	if part_press and app.world_selection:app.world_selection.cancel_gesture(true)
	part_press=false
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
	var values: Array=mask.keys();values.sort();request["vertex_mask"]=values;request.erase("points_in_anchor");queue_changed();launch(preview_operation())

func change_anchor(index: int) -> void:
	if changing or pid>0:return
	request.anchor_node=anchors.get_item_metadata(index);request.erase("points_in_anchor");queue_changed();launch(preview_operation())

func point_values() -> void:
	if preview.get("mode","")=="existing_joints":
		changing=true;var p: Array=preview.points_in_anchor[point_choice.selected]
		for axis in range(3):fields[axis].set_value_no_signal(p[axis])
		changing=false;return
	if request.get("points_in_anchor",[]).is_empty():return
	changing=true;var p: Array=request.points_in_anchor[point_choice.selected]
	for axis in range(3):fields[axis].set_value_no_signal(p[axis])
	changing=false

func change_point() -> void:
	if changing or pid>0 or preview.is_empty() or not request.has("points_in_anchor"):return
	request.points_in_anchor[point_choice.selected]=[fields[0].value,fields[1].value,fields[2].value]
	if queue_changed():point_review_after=Time.get_ticks_msec()+250

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
	if pid>0 or app.exporting or app.navigating:return
	if not included.is_empty():
		var plans: Array=[]
		for group in included:
			if not included[group].valid or point_review_after>0:refresh_inclusions();return
			plans.append(included[group].request.duplicate(true))
		var lineage=actor().data.metadata.get("generated_helper_history",[])
		if not lineage is Array or lineage.size()+plans.size()+(1 if lineage.is_empty() and actor().data.metadata.has("generated_helpers") else 0)>128:
			info.text="The stored helper history needs review before adding these parts.";return
		launch("batch_build",{"format":"studio_secondary_batch_1","source_sha256":request.source_sha256,"source_stamp_ns":assessment.get("source_stamp_ns",""),"reviewed":true,"items":plans});return
	if not preview_ready or preview.is_empty() or not preview.get("can_apply",false):return
	request["reviewed"]=true;launch("build")

func install(value: Dictionary) -> void:
	app.pose_editor.finish_drag();app.finish_stroke()
	if app.recovery_revision!=revision or app.current_world()!=before_world:close();app.message("The scene changed during preparation. Original and current edits were kept; open review again.");return
	if value.has("batch") and (FileAccess.get_sha256(source)!=request.source_sha256 or FileAccess.get_modified_time(source)!=source_stamp or value.batch.source_sha256!=request.source_sha256):
		info.text="The original source changed. Reopen loose-part review; the current scene is kept.";refresh_inclusions();return
	var before: Dictionary=app.current_world();var after:=before.duplicate(true);var row: Dictionary={}
	for item in after.objects:
		if item.id==target_id:row=item;break
	if row.is_empty():close();return
	var sha:=FileAccess.get_sha256(value.glb);var managed:=ProjectSettings.globalize_path("res://output/imports").path_join(sha+".glb")
	if value.has("batch") and value.batch.get("final_sha256","")!=sha:
		info.text="The checked candidate changed. Current model kept; review the checked parts again.";refresh_inclusions();return
	var error:=Storage.managed_copy(value.glb,managed,sha)
	if not error.is_empty():info.text=error;return
	var reports: Array=value.get("reports",[value.report])
	if reports.is_empty() or reports.size()>128 or reports.any(func(report):return not report is Dictionary or report.get("format","")!="studio_generated_helpers_1"):
		info.text="The checked setup returned invalid history. Current model kept.";return
	row.source=managed;row.sha256=sha;row.metadata["generated_helpers"]=reports[-1]
	var stored_lineage=row.metadata.get("generated_helper_history",[])
	if not stored_lineage is Array or stored_lineage.size()>=128:info.text="The stored helper history needs review. Current model kept.";return
	var lineage: Array=stored_lineage.duplicate(true)
	if lineage.is_empty():
		for old in before.objects:
			if old.id==target_id and old.metadata.has("generated_helpers"):lineage.append(old.metadata.generated_helpers.duplicate(true))
	if lineage.size()+reports.size()>128:info.text="The stored helper history needs review. Current model kept.";return
	for report in reports:lineage.append(report.duplicate(true))
	row.metadata["generated_helper_history"]=lineage
	clear_preview();applying=true;error=app.restore_world(after);applying=false
	if not error.is_empty():info.text="The new rig could not preserve existing bindings. Original kept. "+error;refresh_inclusions();return
	app.has_project.origins[managed.replace("\\","/")]=str(value.glb);app.push_history({"type":"world","before":before,"after":after});app.changed();close()
	app.message("Set up "+str(reports.size())+" checked parts as one edit. Original poses are kept; Undo removes the whole setup. Turn on Hair & clothes to simulate them." if value.has("batch") else "Enabled the reviewed existing joints. Original weights are kept; Undo removes the setup. Turn on Hair & clothes to simulate the chain." if value.report.get("mode","")=="existing_joints" else "Added weighted joints to the reviewed part. The original is kept; Undo restores it. Turn on Hair & clothes to simulate the new chain.")

func clear_preview() -> void:
	if is_instance_valid(app.canvas):app.canvas.review_lines=PackedVector2Array();app.canvas.review_chain=PackedVector2Array();app.canvas.queue_redraw()

func close() -> void:
	if part_press and app.world_selection:app.world_selection.cancel_gesture(true)
	part_press=false;mode_choice="auto";selected_key=""
	included.clear();part_names.clear();point_review_after=0;pending_install={};restore_list_focus=false;inclusion_navigation=false;preview_ready=false
	cancel_patch_drag()
	if is_instance_valid(app.canvas):app.canvas.review_pointer=Callable()
	if pid>0 and OS.is_process_running(pid):OS.kill(pid)
	pid=-1;clear_preview()
	if is_instance_valid(window):window.hide();window.queue_free()
	window=null;preview={};assessment={};request={};fields.clear();target_id="";prefer_loose=false

func _exit_tree() -> void:close()
