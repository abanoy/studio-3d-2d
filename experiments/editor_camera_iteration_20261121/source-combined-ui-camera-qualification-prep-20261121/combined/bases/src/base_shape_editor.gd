extends Node
# Static asset setup, explicitly separate from authored animation/physics capture.
const Shape=preload("res://src/source_shape.gd")
const ShapeLabels=preload("res://src/shape_labels.gd")
const Catalog=preload("res://src/shape_catalog.gd")
var app
var panel: VBoxContainer
var parts: OptionButton
var area_filter: OptionButton
var organize: VBoxContainer
var native_caption: Label
var organizing_signature:=""
var assigned_area: OptionButton
var assigned_label: LineEdit
var assign_button: Button
var estimate_button: Button
var search: LineEdit
var shapes: ItemList
var result_nodes: Array[int]=[]
var amount: SpinBox
var apply_button: Button
var reset_button: Button
var reset_all: Button
var remove_button: Button
var record_draft: Button
var discard_draft: Button
var info: Label
var node_index:=-1
var shape_index:=-1
var signature:=""
var dirty:=false
var animated:=false
var value_frame:=-1
var shown_values:=""
var study: Node
var comparison: Node
var presets: Node

func current_config() -> Dictionary:
	var base:=Shape.setting(actor().data)
	return preload("res://src/shape_animation.gd").configuration(base,actor().sample_shapes(app.frame,true)) if animated else base

func actor() -> RefCounted:return app.renderer.active_model()
func rows() -> Array:return actor().root.get_meta(Shape.META,{"rows":[]}).rows if actor() else []
func row() -> Dictionary:
	for value in rows():
		if int(value.node)==node_index:return value
	return {}

func setup(parent: Node) -> void:
	panel=VBoxContainer.new();parent.add_child(panel if animated else app.advanced(panel))
	app.label(panel,"Shape at this frame" if animated else "Base shape · whole project").tooltip_text="Apply creates a shape key at the current frame when Auto-key is on." if animated else "These adjustments affect the model throughout the project. They do not create animation keys."
	if animated:
		presets=preload("res://src/expression_pose_editor.gd").new();add_child(presets);presets.setup(self,panel)
	parts=OptionButton.new();parts.clip_text=true;panel.add_child(parts)
	parts.item_selected.connect(func(index):node_index=int(parts.get_item_metadata(index));shape_index=-1;rebuild())
	area_filter=OptionButton.new();area_filter.add_item("All areas")
	for area in Catalog.AREAS:area_filter.add_item(area if area!="Other" else "Other / unassigned")
	area_filter.tooltip_text="Areas are estimates unless you assign them. Every control remains under All areas.";panel.add_child(area_filter)
	area_filter.item_selected.connect(func(_index):rebuild())
	search=LineEdit.new();search.placeholder_text="Find shape…";panel.add_child(search);search.text_changed.connect(func(_text):rebuild())
	shapes=ItemList.new();shapes.custom_minimum_size=Vector2(220,105);panel.add_child(shapes)
	var font:=SystemFont.new();font.font_names=PackedStringArray(["Yu Gothic UI","Segoe UI","Arial"]);shapes.add_theme_font_override("font",font)
	shapes.item_selected.connect(func(index):select_result(index);load_amount())
	var line:=HBoxContainer.new();panel.add_child(line);app.label(line,"Amount")
	amount=SpinBox.new();amount.min_value=-100;amount.max_value=100;amount.step=.001;amount.size_flags_horizontal=Control.SIZE_EXPAND_FILL;line.add_child(amount)
	amount.value_changed.connect(func(_value):dirty=true;buttons())
	apply_button=app.button(panel,"Apply at this frame" if animated else "Apply base amount",apply_amount)
	if animated:
		record_draft=app.button(panel,"Record pose key at this frame",app.pose_editor.record_dialog)
		record_draft.tooltip_text="Record the current model pose, including this expression draft."
		record_draft.hide()
		discard_draft=app.button(panel,"Discard expression draft",discard_expression_draft)
		discard_draft.tooltip_text="Return all expression controls at this frame to their recorded values. Undo restores the draft."
		discard_draft.hide()
	reset_button=app.button(panel,"Use base amount here" if animated else "Reset this adjustment",reset_selected)
	reset_all=app.button(panel,"Use all base amounts here" if animated else "Reset all shape adjustments",reset_adjustments)
	if animated:remove_button=app.button(panel,"Remove this shape key here",remove_key)
	info=app.label(panel,"");info.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	if animated:
		organize=VBoxContainer.new();panel.add_child(app.advanced(organize));app.label(organize,"Organize this control")
		native_caption=app.label(organize,"");native_caption.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
		assigned_area=OptionButton.new();organize.add_child(assigned_area)
		for area in Catalog.AREAS:assigned_area.add_item(area)
		assigned_label=LineEdit.new();assigned_label.max_length=80;assigned_label.placeholder_text="Display name (optional)";organize.add_child(assigned_label)
		assign_button=app.button(organize,"Save name and area",assign_control)
		estimate_button=app.button(organize,"Use estimate again",clear_assignment)
		app.label(organize,"Organizing changes the list, not the animation.").autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
		comparison=preload("res://src/shape_comparison.gd").new();add_child(comparison);comparison.setup(self,panel)
		panel.move_child(comparison.button,shapes.get_index()+1)
		study=preload("res://src/shape_study.gd").new();add_child(study);study.setup(self,organize)
	sync()

func sync() -> void:
	if not panel:return
	if animated and not panel.get_window().visible:return
	panel.visible=(animated or app.advanced_mode) and actor()!=null and (not rows().is_empty() or animated and preload("res://src/expression_presets.gd").has_data(actor().root))
	var next: String=str(actor().root.get_instance_id())+(str(app.advanced_mode) if animated else JSON.stringify(current_config())) if actor() else ""
	if actor():next+=JSON.stringify(actor().data.get("metadata",{}).get("shape_catalog",{}))
	var values: String=JSON.stringify(current_config()) if animated and actor() else ""
	if next!=signature:
		signature=next;parts.clear()
		for value in rows():
			parts.add_item(ShapeLabels.part(str(value.name),parts.item_count,not animated or app.advanced_mode));parts.set_item_metadata(parts.item_count-1,int(value.node));parts.set_item_tooltip(parts.item_count-1,str(value.name)+" · source part "+str(value.node))
		if row().is_empty():node_index=int(rows()[0].node) if not rows().is_empty() else -1
		for i in range(parts.item_count):
			if int(parts.get_item_metadata(i))==node_index:parts.select(i)
		rebuild()
	elif animated and (not dirty or value_frame!=app.frame or shown_values!=values):load_amount()
	if animated:value_frame=app.frame;shown_values=values
	buttons()
	if presets:presets.sync()

func rebuild() -> void:
	shapes.clear();result_nodes.clear();var selected:=-1
	var query:=search.text.strip_edges().to_lower()
	var global_search: bool=animated and not app.advanced_mode and (not query.is_empty() or area_filter.selected>0)
	parts.visible=not global_search
	var candidates: Array=rows() if global_search else [row()]
	var matching_labels: Dictionary={}
	var part_numbers: Dictionary={}
	for part in range(parts.item_count):part_numbers[int(parts.get_item_metadata(part))]=part+1
	for current in candidates:
		if current.is_empty():continue
		var owner:=int(current.node)
		for i in range(current.names.size()):
			var name: String=str(current.names[i])
			var entry:=Catalog.lookup(actor().data,owner,i,name)
			if area_filter.selected>0 and entry.area!=Catalog.AREAS[area_filter.selected-1]:continue
			var label: String=name if not animated or app.advanced_mode else str(entry.label)
			if not matches_query(query,name,entry):continue
			var index:=shapes.add_item(label if not label.is_empty() else "Shape "+str(i+1))
			result_nodes.append(owner)
			if global_search:
				if not matching_labels.has(label):matching_labels[label]=[]
				matching_labels[label].append(index)
			shapes.set_item_metadata(index,i);shapes.set_item_tooltip(index,name+" · "+str(entry.area)+" · "+str(entry.evidence)+"\nPart "+str(owner)+", shape "+str(i)+("\n"+str(entry.notice) if entry.has("notice") else ""))
			if owner==node_index and i==shape_index:selected=index
	for label in matching_labels:
		if matching_labels[label].size()<2:continue
		for index in matching_labels[label]:
			shapes.set_item_text(index,"%s · Part %d" % [label,part_numbers[result_nodes[index]]])
	if selected<0 and shapes.item_count>0:selected=0
	if selected>=0:shapes.select(selected);select_result(selected)
	else:shape_index=-1
	load_amount()

func matches_query(query: String,native_name: String,entry: Dictionary) -> bool:
	return query.is_empty() or query in (native_name+" "+str(entry.label)+" "+str(entry.area)).to_lower()

func select_result(index: int) -> void:
	node_index=result_nodes[index]
	shape_index=int(shapes.get_item_metadata(index))
	for part in range(parts.item_count):
		if int(parts.get_item_metadata(part))==node_index:
			parts.select(part)
			break

func load_amount() -> void:
	dirty=false;var current:=row()
	if shape_index>=0 and not current.is_empty():
		var value: float=Shape.effective(current,current_config())[shape_index]
		amount.set_value_no_signal(value);info.text="Amount: "+str(value)+("\nFrame "+str(app.frame)+" · auto-key "+("on" if app.pose_editor.auto_key.button_pressed else "off") if animated else "\nApplies throughout the project.")
		var entry:=Catalog.lookup(actor().data,node_index,shape_index,str(current.names[shape_index]))
		info.text+="\n"+str(entry.area)+" · "+str(entry.evidence)
		if entry.has("notice"):info.text+="\n"+str(entry.notice)
		if organize:
			native_caption.text="Original: "+str(current.names[shape_index]);native_caption.tooltip_text="Part "+str(node_index)+", shape "+str(shape_index)
			var key: String=str(actor().root.get_instance_id())+":"+str(node_index)+":"+str(shape_index)+":"+JSON.stringify(actor().data.get("metadata",{}).get("shape_catalog",{}))
			if key!=organizing_signature:
				organizing_signature=key;assigned_area.select(Catalog.AREAS.find(entry.area));assigned_label.text=str(entry.label) if entry.manual else ""
	else:info.text="No matching shapes."
	if shape_index>=0:shapes.ensure_current_is_visible()
	buttons()

func buttons() -> void:
	if not apply_button:return
	var valid:=actor()!=null and shape_index>=0 and not row().is_empty();var busy: bool=app.exporting or app.playing
	apply_button.disabled=not valid or not dirty or busy;amount.editable=valid and not busy
	parts.disabled=busy or parts.item_count==0;search.editable=not busy
	area_filter.disabled=busy
	if organize:
		var organizing_busy: bool=busy or dirty or app.pose_editor.contacts.live_busy()
		assign_button.disabled=not valid or organizing_busy;estimate_button.disabled=not valid or organizing_busy
		assigned_area.disabled=not valid or organizing_busy;assigned_label.editable=valid and not organizing_busy
	var overrides: Dictionary=Shape.setting(actor().data).get("overrides",{}) if actor() else {}
	reset_button.disabled=not valid or busy or not overrides.get(str(node_index),{}).has(str(shape_index))
	reset_all.disabled=busy or overrides.is_empty()
	if animated:
		var rig: RefCounted=actor()
		record_draft.visible=rig!=null and rig.data.get("shape_draft_frame",-1)==app.frame and rig.sample_shapes(app.frame,true)!=rig.sample_shapes(app.frame,false)
		record_draft.disabled=busy or dirty or app.pose_editor.contacts.live_busy()
		discard_draft.visible=record_draft.visible
		discard_draft.disabled=record_draft.disabled
		reset_button.disabled=not valid or busy
		reset_all.disabled=busy or actor()==null or actor().data.get("shape_base",{}).is_empty()
		remove_button.disabled=not valid or busy or not preload("res://src/shape_animation.gd").has_control(actor().data,app.frame,str(node_index),str(shape_index))

func organize_control(clear:=false) -> void:
	if not actor() or shape_index<0 or row().is_empty() or app.playing or app.exporting:return
	if dirty:app.message("Apply the amount change before organizing this control.");return
	if app.pose_editor.contacts.live_busy():app.message("Turn Physics and Hair & clothes off before organizing controls.");return
	var updated:=Catalog.clear(actor().data,node_index,shape_index) if clear else Catalog.assign(actor().data,node_index,shape_index,str(row().names[shape_index]),Catalog.AREAS[assigned_area.selected],assigned_label.text)
	if updated.has("error"):app.message(updated.error);return
	if updated.data==actor().data:return
	var selected_node:=node_index;var selected_shape:=shape_index
	var native_name:=str(row().names[selected_shape])
	var next_entry:=Catalog.lookup(updated.data,selected_node,selected_shape,native_name)
	var world: Dictionary=app.current_world()
	for i in range(world.objects.size()):
		if world.objects[i].id==actor().data.id:world.objects[i]=updated.data
	if app.pose_editor.contacts.metadata_bytes(world)>1024*1024:app.message("This assignment exceeds the project metadata limit.");return
	var error: String=app.pose_editor.restore_state(updated.data)
	if not error.is_empty():app.message(error);return
	node_index=selected_node;shape_index=selected_shape
	if area_filter.selected>0:area_filter.select(Catalog.AREAS.find(next_entry.area)+1)
	if not matches_query(search.text.strip_edges().to_lower(),native_name,next_entry):search.text=""
	signature="";sync();app.message("Control organization saved. Undo restores the previous choice.")

func discard_expression_draft() -> void:
	var rig: RefCounted=actor()
	if not rig or dirty or app.playing or app.exporting or app.pose_editor.contacts.live_busy():return
	if rig.data.get("shape_draft_frame",-1)!=app.frame:return
	var recorded: Dictionary=rig.sample_shapes(app.frame,false)
	if recorded==rig.sample_shapes(app.frame,true):return
	var candidate: Dictionary=rig.data.duplicate(true)
	candidate.shape_pose=recorded
	var error: String=app.pose_editor.restore_state(candidate)
	if error.is_empty():app.message("Expression draft discarded. Undo restores it.")
	else:app.message(error)

func assign_control() -> void:organize_control()
func clear_assignment() -> void:organize_control(true)

func remove_key() -> void:
	if not actor() or shape_index<0:return
	app.pose_editor.remove_shape_key(str(node_index),str(shape_index));signature="";sync()

func commit(overrides: Dictionary) -> void:
	if not actor() or app.exporting:return
	if overrides==Shape.setting(actor().data).get("overrides",{}):load_amount();return
	app.stop();app.pose_editor.finish_drag();app.finish_stroke()
	if not app.physics_editor.freeze_all():sync();return
	var data: Dictionary=actor().data.duplicate(true)
	data.metadata["source_shape"]={"format":"studio_source_shape_2","enabled":Shape.enabled(data),"overrides":overrides}
	var error: String=app.pose_editor.restore_state(data)
	if not error.is_empty():signature="";sync();return
	app.message("Base shape updated for the whole project.")

func apply_amount() -> void:
	if not dirty or shape_index<0 or row().is_empty():return
	if animated:
		var error: String=app.pose_editor.set_shape_amounts({str(node_index):{str(shape_index):amount.value}})
		if not error.is_empty():
			app.message(error)
			return
		signature="";sync();return
	var config:=Shape.setting(actor().data);var overrides: Dictionary=config.get("overrides",{}).duplicate(true)
	var inherited: float=row().weights[shape_index] if config.enabled else 0.
	if absf(amount.value-inherited)<.0000001:
		if overrides.has(str(node_index)):overrides[str(node_index)].erase(str(shape_index))
	else:
		if not overrides.has(str(node_index)):overrides[str(node_index)]={}
		overrides[str(node_index)][str(shape_index)]=amount.value
	if overrides.has(str(node_index)) and overrides[str(node_index)].is_empty():overrides.erase(str(node_index))
	commit(overrides)

func reset_selected() -> void:
	if not actor():return
	if animated:
		if shape_index>=0 and not row().is_empty():app.pose_editor.set_shape_amounts({str(node_index):{str(shape_index):Shape.effective(row(),Shape.setting(actor().data))[shape_index]}})
		signature="";sync()
		return
	var overrides: Dictionary=Shape.setting(actor().data).get("overrides",{}).duplicate(true)
	if not overrides.has(str(node_index)) or not overrides[str(node_index)].has(str(shape_index)):return
	overrides[str(node_index)].erase(str(shape_index))
	if overrides[str(node_index)].is_empty():overrides.erase(str(node_index))
	commit(overrides)

func reset_adjustments() -> void:
	if animated and actor():
		var values: Dictionary=actor().data.get("shape_base",{}).duplicate(true)
		for current in rows():
			if not values.has(str(current.node)):continue
			var base:=Shape.effective(current,Shape.setting(actor().data))
			for index in values[str(current.node)]:values[str(current.node)][index]=base[int(index)]
		app.pose_editor.set_shape_amounts(values);signature="";sync();return
	if actor() and not Shape.setting(actor().data).get("overrides",{}).is_empty():commit({})
