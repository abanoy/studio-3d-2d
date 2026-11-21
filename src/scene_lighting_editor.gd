extends Node
const Document=preload("res://src/scene_lighting_document.gd")
const Runtime=preload("res://src/scene_lighting_runtime.gd")
var app
var launch: Button
var dialog: AcceptDialog
var list: ItemList
var ids: Array=[]
var selected:=""
var context:=""
var refreshing:=false
var name_field: LineEdit
var enabled: CheckBox
var shadows: CheckBox
var color: ColorPickerButton
var energy: SpinBox
var positions: Array=[]
var directions: Array=[]
var distance: SpinBox
var angle: SpinBox
var placement: VBoxContainer
var ambient: SpinBox
var ambient_color: ColorPickerButton
var hint: Label
var fields: VBoxContainer
var apply_button: Button
var remove_button: Button
var add_buttons: Array=[]
var reflection_enabled: CheckBox
var reflection_positions: Array=[]
var reflection_sizes: Array=[]
var reflection_strength: SpinBox
var reflection_fields: VBoxContainer
var undo_button: Button
var redo_button: Button
var indirect_enabled: CheckBox
var indirect_energy: SpinBox
var indirect_cell: SpinBox
var indirect_settle: SpinBox
var indirect_status: Label
var indirect_method: OptionButton
var voxel_fields: VBoxContainer
var voxel_positions: Array=[]
var voxel_sizes: Array=[]
var voxel_quality: OptionButton

func setup(owner_app: Control) -> void:
	app=owner_app
	launch=app.button(app.lighting_choice.get_parent(),"Lights…",open)
	launch.tooltip_text="Add and edit scene lights. Imported lights stay in their assets."
	app.lighting_choice.get_parent().move_child(launch,app.lighting_choice.get_index()+1)
	app.renderer.assets_changed.connect(func():if dialog and dialog.visible:call_deferred("refresh"))

func blocked() -> bool:
	return app.exporting or app.playing or app.source_import.pid>0 or app.has_project.pid>0

func token() -> String:
	return str(app.recovery_session)+"/"+str(app.sequence_editor.active_owner)+"/"+JSON.stringify(app.video)

func build() -> void:
	dialog=AcceptDialog.new();dialog.title="Scene lights";dialog.unresizable=false;dialog.exclusive=false
	dialog.ok_button_text="Close";app.add_child(dialog)
	var scroll:=ScrollContainer.new();scroll.custom_minimum_size=Vector2(620,470);scroll.horizontal_scroll_mode=ScrollContainer.SCROLL_MODE_DISABLED;dialog.add_child(scroll)
	var box:=VBoxContainer.new();box.size_flags_horizontal=Control.SIZE_EXPAND_FILL;scroll.add_child(box)
	var explanation: Label=app.label(box,"Add a light, choose it below, then edit and Apply. Lights affect the whole active scene.");explanation.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	var add_row:=HFlowContainer.new();box.add_child(add_row)
	for entry in [["Directional","directional"],["Point","point"],["Spot","spot"]]:
		add_buttons.append(app.button(add_row,"+ "+entry[0],add_light.bind(entry[1])))
	var presets:=MenuButton.new();presets.text="Add preset";add_row.add_child(presets);add_buttons.append(presets)
	for title in ["Daylight","Warm key + cool fill","Stage spotlight","Soft character"]:presets.get_popup().add_item(title)
	presets.get_popup().id_pressed.connect(func(index):add_preset(["daylight","warm_cool","stage","soft_character"][index]))
	app.button(add_row,"Use Lit",func():app.change_lighting(1);refresh())
	undo_button=app.button(add_row,"Undo",func():if not blocked():app.undo();refresh())
	redo_button=app.button(add_row,"Redo",func():if not blocked():app.redo();refresh())
	list=ItemList.new();list.custom_minimum_size.y=110;list.item_selected.connect(select);box.add_child(list)
	fields=VBoxContainer.new();box.add_child(fields)
	var title_row:=HBoxContainer.new();fields.add_child(title_row)
	name_field=LineEdit.new();name_field.max_length=120;name_field.placeholder_text="Light name";name_field.size_flags_horizontal=Control.SIZE_EXPAND_FILL;title_row.add_child(name_field)
	name_field.text_submitted.connect(func(_text):apply())
	enabled=CheckBox.new();enabled.text="Visible";title_row.add_child(enabled)
	enabled.toggled.connect(func(value):if not refreshing:change_visibility(value))
	var appearance:=HBoxContainer.new();fields.add_child(appearance)
	app.label(appearance,"Color");color=ColorPickerButton.new();color.edit_alpha=false;color.custom_minimum_size=Vector2(70,28);appearance.add_child(color)
	energy=number(appearance,"Intensity",0,64,.05)
	shadows=CheckBox.new();shadows.text="Shadows";appearance.add_child(shadows)
	var toggle:=CheckButton.new();toggle.text="Placement and beam";fields.add_child(toggle)
	placement=VBoxContainer.new();fields.add_child(placement);placement.hide();toggle.toggled.connect(placement.set_visible)
	var position_row:=HBoxContainer.new();placement.add_child(position_row)
	for axis in ["X","Y","Z"]:positions.append(number(position_row,axis,-1e12,1e12,.01))
	var rotation_row:=HBoxContainer.new();placement.add_child(rotation_row)
	for axis in ["Pitch","Yaw","Roll"]:directions.append(number(rotation_row,axis,-36000,36000,.1))
	var beam_row:=HBoxContainer.new();placement.add_child(beam_row)
	distance=number(beam_row,"Range",.01,100000,.1);angle=number(beam_row,"Spot half-angle °",1,89,.5)
	app.button(placement,"Aim at current selection",aim_at_selection)
	var convention: Label=app.label(placement,"Position uses scene units. Direction uses degrees; light points along local −Z. Point lights shine in all directions.");convention.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	var commands:=HBoxContainer.new();fields.add_child(commands)
	apply_button=app.button(commands,"Apply light",apply);app.button(commands,"Reload values",refresh)
	remove_button=app.button(commands,"Remove light",remove)
	var ambient_row:=HBoxContainer.new();box.add_child(ambient_row)
	ambient=number(ambient_row,"Ambient fill (Lit)",0,4,.01)
	ambient_color=ColorPickerButton.new();ambient_color.edit_alpha=false;ambient_color.custom_minimum_size=Vector2(65,28);ambient_row.add_child(ambient_color)
	var fill_button: Button=app.button(ambient_row,"Apply fill",apply_fill);add_buttons.append(fill_button)
	var fill_note: Label=app.label(box,"Ambient fill is uniform illumination, an approximation of indirect light. Imported lights and baked lighting remain unchanged.");fill_note.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	var reflection_toggle:=CheckButton.new();reflection_toggle.text="Room reflections and local fill (Forward+)";box.add_child(reflection_toggle)
	reflection_fields=VBoxContainer.new();box.add_child(reflection_fields);reflection_fields.hide();reflection_toggle.toggled.connect(reflection_fields.set_visible)
	reflection_enabled=CheckBox.new();reflection_enabled.text="Live room reflections and local fill (slower)";reflection_fields.add_child(reflection_enabled)
	var probe_position:=HBoxContainer.new();reflection_fields.add_child(probe_position)
	for axis in ["Center X","Center Y","Center Z"]:reflection_positions.append(number(probe_position,axis,-1e12,1e12,.01))
	var probe_size:=HBoxContainer.new();reflection_fields.add_child(probe_size)
	for axis in ["Room width","Room height","Room depth"]:reflection_sizes.append(number(probe_size,axis,.1,100000,.1))
	reflection_strength=number(reflection_fields,"Reflection strength",0,4,.05)
	var probe_actions:=HBoxContainer.new();reflection_fields.add_child(probe_actions)
	add_buttons.append(app.button(probe_actions,"Fit near scene",fit_reflection))
	add_buttons.append(app.button(probe_actions,"Apply reflections",apply_reflection))
	var probe_note: Label=app.label(reflection_fields,"Launch with python run.py --forward-plus for this optional mode. Set Ambient fill above 0 (try 0.3). A live room cubemap approximates reflections and local ambient fill; it does not trace light bounces or mirrors. Put its center in open air. Imported probes remain.");probe_note.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	var indirect_toggle:=CheckButton.new();indirect_toggle.text="Environment bounce (Forward+, experimental)";box.add_child(indirect_toggle)
	var indirect_fields:=VBoxContainer.new();box.add_child(indirect_fields);indirect_fields.hide();indirect_toggle.toggled.connect(indirect_fields.set_visible)
	indirect_enabled=CheckBox.new();indirect_enabled.text="Enable environment bounce (experimental)";indirect_fields.add_child(indirect_enabled)
	indirect_method=OptionButton.new();indirect_method.add_item("Open scene — SDFGI (models receive only)");indirect_method.add_item("Bounded room — VoxelGI (dynamic models)");indirect_fields.add_child(indirect_method)
	indirect_method.item_selected.connect(func(_index):update_indirect_fields())
	var indirect_row:=HBoxContainer.new();indirect_fields.add_child(indirect_row)
	indirect_energy=number(indirect_row,"Bounce strength",0,4,.05)
	indirect_cell=number(indirect_row,"Cell size (scene units)",.05,4,.05)
	indirect_settle=number(indirect_row,"Render settling frames",8,120,1)
	voxel_fields=VBoxContainer.new();indirect_fields.add_child(voxel_fields)
	var room_position:=HBoxContainer.new();voxel_fields.add_child(room_position)
	for axis in ["Center X","Center Y","Center Z"]:voxel_positions.append(number(room_position,axis,-1e12,1e12,.01))
	var room_size:=HBoxContainer.new();voxel_fields.add_child(room_size)
	for axis in ["Room width","Room height","Room depth"]:voxel_sizes.append(number(room_size,axis,1,128,.1))
	voxel_quality=OptionButton.new();voxel_quality.add_item("64 subdivisions (start here)");voxel_quality.add_item("128 subdivisions (slower, more detail)");voxel_fields.add_child(voxel_quality)
	add_buttons.append(app.button(voxel_fields,"Fit scene / near view",fit_voxel))
	var indirect_actions:=HBoxContainer.new();indirect_fields.add_child(indirect_actions)
	add_buttons.append(app.button(indirect_actions,"Apply indirect light",apply_indirect))
	add_buttons.append(app.button(indirect_actions,"Rebuild from current environment",rebuild_indirect))
	var indirect_note: Label=app.label(indirect_fields,"Use Lit with python run.py --forward-plus. SDFGI: environments contribute; models receive only. VoxelGI: one bounded room, static environment bake and dynamic model GI. Apply starts a bake that can pause Studio; reopening regenerates it from the saved settings and assets. Rebuild after changing static geometry. Custom shaders cannot provide static bake colors; thin/cutout walls can leak. Export holds each exact frame for the settling budget. These are approximations, not path tracing.");indirect_note.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	indirect_status=app.label(indirect_fields,"");indirect_status.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	hint=app.label(box,"");hint.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART

func number(parent: Control,title: String,minimum: float,maximum: float,step: float) -> SpinBox:
	var box:=VBoxContainer.new();box.size_flags_horizontal=Control.SIZE_EXPAND_FILL;parent.add_child(box)
	app.label(box,title)
	var spin:=SpinBox.new();spin.min_value=minimum;spin.max_value=maximum;spin.step=step;spin.size_flags_horizontal=Control.SIZE_EXPAND_FILL;box.add_child(spin)
	spin.value_changed.connect(func(_value):if not refreshing:spin.set_meta("lighting_numeric_edited",true))
	spin.get_line_edit().text_changed.connect(func(_text):if not refreshing:spin.set_meta("lighting_numeric_edited",true))
	return spin

func load_number(spin: SpinBox,value: float) -> void:
	# Godot4.6 updates SpinBox text on draw. Hidden fields may still contain
	# their initial minimum, and visible values can be rounded to the UI step.
	# Retain the exact document value until a real edit, including across folds.
	spin.set_value_no_signal(value)
	var text:=JSON.stringify(value,"",true,true)
	spin.set_meta("lighting_numeric_snapshot",{"original":value,"value":spin.value,"text":text,"shown":String.num(spin.value,step_decimals(spin.step))})
	spin.set_meta("lighting_numeric_edited",false)
	spin.get_line_edit().text=text

func open() -> void:
	if blocked():return
	app.release_mouse()
	if not dialog:build()
	refresh();dialog.popup_centered(Vector2i(680,610))

func _process(_delta: float) -> void:
	if launch:launch.disabled=blocked()
	if not dialog or not dialog.visible:return
	if context!=token():refresh()
	for control in add_buttons:control.disabled=blocked()
	undo_button.disabled=blocked() or app.history.is_empty();redo_button.disabled=blocked() or app.redo_history.is_empty()
	enabled.disabled=blocked()
	var saved_reflection: bool=Document.document(app.video).get("reflection",{}).get("enabled",false)
	reflection_enabled.disabled=blocked() or not Runtime.reflections_supported() and not saved_reflection
	# A project from Forward+ must still be able to save GI off on other GPUs.
	indirect_enabled.disabled=blocked()
	indirect_status.text=app.renderer.scene_lighting.indirect.status
	apply_button.disabled=blocked() or selected.is_empty();remove_button.disabled=apply_button.disabled

func refresh() -> void:
	if not dialog:return
	refreshing=true;context=token();list.clear();ids.clear()
	var data:=Document.document(app.video)
	for row in data.lights:
		ids.append(row.id);list.add_item(("● " if row.visible else "○ ")+row.name+" ("+row.type+")")
	if not selected in ids:selected=ids[0] if not ids.is_empty() else ""
	fields.visible=not selected.is_empty()
	if not selected.is_empty():
		var index:=ids.find(selected);list.select(index);var row: Dictionary=data.lights[index]
		name_field.text=row.name;enabled.set_pressed_no_signal(row.visible);shadows.set_pressed_no_signal(row.shadows)
		color.color=Color(row.color[0],row.color[1],row.color[2]);load_number(energy,row.energy)
		for axis in range(3):load_number(positions[axis],row.position[axis]);load_number(directions[axis],row.rotation_degrees[axis]);directions[axis].editable=row.type!="point"
		load_number(distance,row.range);distance.editable=row.type!="directional"
		load_number(angle,row.spot_angle);angle.editable=row.type=="spot"
	load_number(ambient,data.ambient_energy);ambient_color.color=Color(data.ambient_color[0],data.ambient_color[1],data.ambient_color[2])
	var probe: Dictionary=data.get("reflection",default_reflection())
	reflection_enabled.set_pressed_no_signal(probe.enabled);load_number(reflection_strength,probe.intensity)
	for axis in range(3):load_number(reflection_positions[axis],probe.position[axis]);load_number(reflection_sizes[axis],probe.size[axis])
	var gi:=Document.indirect(data)
	indirect_enabled.set_pressed_no_signal(gi.enabled);load_number(indirect_energy,gi.energy);load_number(indirect_cell,gi.cell_size);load_number(indirect_settle,gi.settle_frames)
	indirect_method.select(1 if gi.get("method","sdfgi")=="voxelgi" else 0)
	var room:=Document.voxel(gi)
	for axis in range(3):load_number(voxel_positions[axis],room.position[axis]);load_number(voxel_sizes[axis],room.size[axis])
	voxel_quality.select(int(room.subdiv));update_indirect_fields()
	var message:="Unshaded hides light effects. Choose Use Lit to see your lights." if app.video.get("lighting_mode")=="unshaded" else "Studio light adds its legacy lamp and ambient fill." if app.video.get("lighting_mode","studio")=="studio" else "Lit uses authored and imported lights, plus your ambient fill."
	message+="\nCompatibility rendering supports 8 directional lights and normally 8 point + 8 spot lights per mesh, including imported lights. Reduce overlapping lights if one stops contributing."
	var limits:=Runtime.material_limits(app.renderer)
	if not limits.is_empty():message+="\n"+limits
	if data.get("reflection",{}).get("enabled",false) and data.ambient_energy<=0:message+="\nRoom reflections need Ambient fill above 0 with this Compatibility setup. Try 0.3 and Apply fill."
	if not Runtime.reflections_supported():message+="\nRoom reflections require Forward+: launch python run.py --forward-plus. Saved probe settings are retained; Compatibility continues to use authored direct lights and fill."
	hint.text=message;refreshing=false

func select(index: int) -> void:
	if refreshing or index<0 or index>=ids.size():return
	selected=ids[index];refresh()

func placement_context() -> Dictionary:
	var actor: RefCounted=app.renderer.active_model()
	var bounds: AABB=app.renderer.scene_bounds(actor.root) if actor else app.renderer.scene_bounds(app.renderer.world_runtime.root if app.renderer.world_runtime else app.renderer.environment_scene)
	var camera: Camera3D=app.renderer.camera
	var center:=camera.global_position-camera.global_basis.z*4.
	var scale:=2.
	if bounds.size.length_squared()>0:
		center=bounds.get_center();scale=clampf(bounds.size.length()*.6,1.,10000.)
		# Huge maps: place near the view instead of at an inaccessible map center.
		if (not actor or actor.data.get("kind")=="environment") and bounds.size.length()>100.:center=camera.global_position-camera.global_basis.z*4.;scale=4.
	return {"center":center,"scale":scale}

func add_light(kind: String) -> void:
	if blocked() or not kind in Document.TYPES:return
	var data:=Document.document(app.video).duplicate(true);var target:=placement_context()
	var row:=Document.create(kind,target.center,target.scale);data.lights.append(row);selected=row.id
	commit(data,"Added "+kind+" light. Choose Lit to see its illumination.")

func add_preset(kind: String) -> void:
	if blocked():return
	var data:=Document.document(app.video).duplicate(true);var target:=placement_context()
	var rows:=Document.preset(kind,target.center,target.scale);data.lights.append_array(rows);selected=rows[0].id
	commit(data,"Added editable lighting preset. Choose Lit to see it.")

func current() -> Dictionary:
	if blocked():return {}
	if context!=token():refresh();app.message("The scene changed. Reloaded light controls; edit the current scene and Apply again.");return {}
	return Document.document(app.video).duplicate(true)

func apply() -> void:
	var data:=current();var index:=ids.find(selected)
	if data.is_empty() or index<0:return
	var row: Dictionary=data.lights[index];row.name=name_field.text.strip_edges();row.shadows=shadows.button_pressed
	row.color=[color.color.r,color.color.g,color.color.b];row.energy=typed(energy)
	for axis in range(3):
		row.position[axis]=typed(positions[axis])
		if row.type!="point":row.rotation_degrees[axis]=typed(directions[axis])
	if row.type!="directional":row.range=typed(distance)
	if row.type=="spot":row.spot_angle=typed(angle)
	commit(data,"Light updated.")

func typed(spin: SpinBox) -> float:
	var value:=spin.get_line_edit().text.strip_edges()
	var snapshot: Dictionary=spin.get_meta("lighting_numeric_snapshot",{})
	if not snapshot.is_empty() and not spin.get_meta("lighting_numeric_edited",false) and spin.value==snapshot.value and value in [snapshot.text,snapshot.shown]:return snapshot.original
	return value.to_float() if value.is_valid_float() else NAN

func apply_fill() -> void:
	var data:=current()
	if data.is_empty():return
	data.ambient_energy=typed(ambient);data.ambient_color=[ambient_color.color.r,ambient_color.color.g,ambient_color.color.b]
	commit(data,"Ambient fill updated. This uniform fill does not simulate bounced light.")

func apply_indirect() -> void:
	var data:=current()
	if data.is_empty():return
	if indirect_enabled.button_pressed and not app.renderer.scene_lighting.indirect.supported():
		hint.text="Environment bounce requires Forward+. Launch python run.py --forward-plus and choose Lit."
		app.message(hint.text);return
	data["indirect"]={"enabled":indirect_enabled.button_pressed,"energy":typed(indirect_energy),"cell_size":typed(indirect_cell),"settle_frames":typed(indirect_settle)}
	data.indirect.method="voxelgi" if indirect_method.selected==1 else "sdfgi"
	data.indirect.voxel={"position":[],"size":[],"subdiv":voxel_quality.selected}
	for axis in range(3):data.indirect.voxel.position.append(typed(voxel_positions[axis]));data.indirect.voxel.size.append(typed(voxel_sizes[axis]))
	commit(data,"Indirect settings updated. Static environments contribute; models receive. Allow time to settle.")

func update_indirect_fields() -> void:
	voxel_fields.visible=indirect_method.selected==1
	indirect_cell.get_parent().visible=indirect_method.selected==0

func fit_voxel() -> void:
	if blocked():return
	var bounds: AABB=app.renderer.scene_bounds(app.renderer.world_runtime.root if app.renderer.world_runtime else app.renderer.environment_scene)
	var center:=bounds.get_center();var size:=bounds.size+Vector3.ONE
	if bounds.size.length_squared()==0 or size.x>128 or size.y>128 or size.z>128:
		center=app.renderer.camera.global_position-app.renderer.camera.global_basis.z*4.;size=Vector3(12,8,12)
	for axis in range(3):load_number(voxel_positions[axis],center[axis]);load_number(voxel_sizes[axis],clampf(size[axis],1,128))
	app.message("Room bounds fitted. Review them, then Apply indirect light to bake.")

func rebuild_indirect() -> void:
	if blocked():return
	app.renderer.scene_lighting.indirect.rebuild()
	app.message("Rebuilding indirect light from the current environment. VoxelGI rebakes the room; SDFGI resets its cascades. Allow time to settle.")

func default_reflection() -> Dictionary:
	var target:=placement_context();var center: Vector3=target.center
	var extent:=clampf(target.scale*4.,2.,100000.)
	return {"enabled":false,"position":[center.x,center.y,center.z],"size":[extent,extent,extent],"intensity":1.}

func fit_reflection() -> void:
	var probe:=default_reflection()
	for axis in range(3):reflection_positions[axis].value=probe.position[axis];reflection_sizes[axis].value=probe.size[axis]

func apply_reflection() -> void:
	var data:=current()
	if data.is_empty():return
	if not Runtime.reflections_supported():
		# A project made in Forward+ can retain a probe in Compatibility. Allow
		# switching it Off without changing its saved placement/strength fields.
		if not reflection_enabled.button_pressed and data.has("reflection"):
			data.reflection.enabled=false
			commit(data,"Room reflections turned off. Saved placement and strength are retained.")
			return
		hint.text="Room reflections require Forward+. Launch python run.py --forward-plus. Direct lights remain available in Compatibility."
		app.message(hint.text);return
	if reflection_enabled.button_pressed and data.ambient_energy<=0:
		hint.text="Set Ambient fill above 0 and Apply fill first (try 0.3) for the room reflection/local-fill approximation."
		app.message(hint.text);return
	var probe:={"enabled":reflection_enabled.button_pressed,"position":[],"size":[],"intensity":typed(reflection_strength)}
	for axis in range(3):probe.position.append(typed(reflection_positions[axis]));probe.size.append(typed(reflection_sizes[axis]))
	data["reflection"]=probe
	commit(data,"Room reflections/local fill updated. This live cubemap approximation costs extra render time.")

func change_visibility(value: bool) -> void:
	var data:=current();var index:=ids.find(selected)
	if data.is_empty() or index<0:return
	data.lights[index].visible=value;commit(data,"Light visibility updated.")

func remove() -> void:
	var data:=current();var index:=ids.find(selected)
	if data.is_empty() or index<0:return
	data.lights.remove_at(index);commit(data,"Light removed. Undo restores it.")

func aim_at_selection() -> void:
	if selected.is_empty() or context!=token():return
	var position:=Vector3(typed(positions[0]),typed(positions[1]),typed(positions[2]))
	var target:=placement_context();var delta: Vector3=target.center-position
	if not position.is_finite() or delta.length_squared()<.000001:return
	var up:=Vector3.RIGHT if absf(delta.normalized().dot(Vector3.UP))>.999 else Vector3.UP
	var rotation:=Basis.looking_at(delta,up).get_euler()
	for axis in range(3):directions[axis].value=rad_to_deg(rotation[axis])

func commit(data: Dictionary,message: String) -> void:
	if blocked():return
	var why:=Document.error(data)
	if not why.is_empty():
		refresh()
		if hint:hint.text=why
		app.message(why);return
	if data==Document.document(app.video):return
	app.stop();app.pose_editor.finish_drag();app.finish_stroke()
	var before: Dictionary=app.video.duplicate(true);app.video["scene_lighting"]=data
	app.push_history({"type":"video","before":before,"after":app.video.duplicate(true)})
	var view: Dictionary=app.renderer.view_state();app.changed();app.set_frame(app.frame);app.renderer.restore_view(view)
	refresh();app.message(message)
