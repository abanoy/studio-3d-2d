extends Node
const Ranges=preload("res://src/contact_ranges.gd")
const Model=Ranges.Model
const Correction=preload("res://src/contact_correction.gd")
var app
var window: Window
var end_frame: SpinBox
var note: Label
var first:=0
var before: Dictionary={}
var target_root: Node3D
var control: Button
var plant_button: Button
var release_button: Button
var correction_box: VBoxContainer
var foot_choice: OptionButton
var nudge_buttons: Array[Button]=[]
var reverse_button: Button
var step: SpinBox
var position_fields: Array[SpinBox]=[]
var rotation_fields: Array[SpinBox]=[]
var pole_fields: Array[SpinBox]=[]
var use_pole: CheckButton
var precise: VBoxContainer
var apply_target: Button
var field_baselines:={}
var loaded_position:=Vector3.ZERO
var loaded_rotation:=Vector3.ZERO
var loaded_pole:=Vector3.ZERO
var viewport: Node
var drag_foot: Button
var drag_knee: Button

func setup(parent: Node) -> void:
	control=app.button(parent,"Planted feet…",open)
	parent.move_child(control,mini(parent.get_child_count()-1,8))
	viewport=preload("res://src/contact_viewport.gd").new();viewport.app=app;viewport.editor=self;add_child(viewport);viewport.setup(parent)
	window=Window.new();window.title="Planted feet";window.theme=app.theme;window.close_requested.connect(window.hide);app.add_child(window)
	var panel:=PanelContainer.new();window.add_child(panel);panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var outer:=VBoxContainer.new();panel.add_child(outer)
	var scroll:=ScrollContainer.new();outer.add_child(scroll);scroll.size_flags_vertical=Control.SIZE_EXPAND_FILL
	var column:=VBoxContainer.new();scroll.add_child(column);column.size_flags_horizontal=Control.SIZE_EXPAND_FILL
	note=app.label(column,"");note.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	end_frame=app.spin(column,"Through frame (inclusive)",0,240,48)
	plant_button=app.button(column,"Plant feet",func():apply_range(true))
	release_button=app.button(column,"Release feet",func():apply_range(false))
	correction_box=VBoxContainer.new();column.add_child(correction_box)
	app.label(correction_box,"Adjust a planted foot in this range")
	foot_choice=OptionButton.new();foot_choice.add_item("Left foot");foot_choice.add_item("Right foot");correction_box.add_child(foot_choice);foot_choice.item_selected.connect(func(_index):load_foot())
	drag_foot=app.button(correction_box,"Drag foot in view",func():viewport.start("position"))
	drag_knee=app.button(correction_box,"Drag knee target in view",func():viewport.start("pole"));app.advanced(drag_knee)
	var nudges:=GridContainer.new();nudges.columns=3;correction_box.add_child(nudges)
	for spec in [["Left",Vector3.LEFT],["Up",Vector3.UP],["Toward view",Vector3.BACK],["Right",Vector3.RIGHT],["Down",Vector3.DOWN],["Away",Vector3.FORWARD]]:
		var direction: Vector3=spec[1]
		var button: Button=app.button(nudges,spec[0],func():nudge(direction));button.tooltip_text="Move this foot relative to the current view. Advanced sets the distance.";nudge_buttons.append(button)
	reverse_button=app.button(correction_box,"Reverse knee bend",reverse_knee)
	precise=VBoxContainer.new();correction_box.add_child(precise);app.advanced(precise)
	step=app.spin(precise,"Nudge distance (scene units)",.001,1000,.02);step.step=.001;step.set_value_no_signal(.02)
	position_fields=vector_fields(precise,"Foot position · world")
	rotation_fields=vector_fields(precise,"Foot rotation · degrees")
	use_pole=CheckButton.new();use_pole.text="Use a fixed knee target";precise.add_child(use_pole)
	pole_fields=vector_fields(precise,"Knee target · world")
	apply_target=app.button(outer,"Apply foot target",apply_fields);app.advanced(apply_target)
	app.button(outer,"Close",window.hide)
	app.renderer.assets_changed.connect(window.hide)

func vector_fields(parent: Node,title: String) -> Array[SpinBox]:
	app.label(parent,title);var row:=HBoxContainer.new();parent.add_child(row);var fields: Array[SpinBox]=[]
	for axis in ["X","Y","Z"]:
		app.label(row,axis);var value:=SpinBox.new();value.min_value=-100000;value.max_value=100000;value.step=.001;value.size_flags_horizontal=Control.SIZE_EXPAND_FILL;row.add_child(value);fields.append(value)
	return fields

func selected_foot() -> Dictionary:
	var segment:=Ranges.Contact.Contacts.active(before.get("animation_clips",[]),first)
	return {} if segment.is_empty() else segment.feet[foot_choice.selected]

func load_foot() -> void:
	var foot:=selected_foot()
	if foot.is_empty():return
	var p:=Model.Timeline.vector(foot.position);var r:=Model.Timeline.quaternion(foot.rotation_xyzw).get_euler()*180/PI
	var rig: RefCounted=app.renderer.active_model();var pole: Vector3=Model.Timeline.vector(foot.pole) if foot.has("pole") else rig.bone_transform(foot.ids[1]).origin
	for axis in range(3):position_fields[axis].set_value_no_signal(p[axis]);rotation_fields[axis].set_value_no_signal(r[axis]);pole_fields[axis].set_value_no_signal(pole[axis])
	loaded_position=p;loaded_rotation=r;loaded_pole=pole;field_baselines={}
	for field in position_fields+rotation_fields+pole_fields:field_baselines[field]=field.value
	use_pole.set_pressed_no_signal(foot.has("pole"))

func field_vector(fields: Array[SpinBox],original: Vector3) -> Vector3:
	var value:=original
	for axis in range(3):
		if fields[axis].value!=field_baselines.get(fields[axis]):value[axis]=fields[axis].value
	return value

func open() -> void:
	viewport.stop()
	var rig: RefCounted=app.renderer.active_model()
	if not rig or app.exporting:return
	if live_busy():app.message("Wait for physics setup, then turn Physics and Hair & clothes off before editing planted feet.");return
	app.stop();app.pose_editor.finish_drag();app.finish_stroke();app.pose_editor.apply_frame()
	before=rig.data.duplicate(true);target_root=rig.root;first=app.frame
	end_frame.max_value=int(app.video.duration_frames);end_frame.set_value_no_signal(int(app.video.duration_frames))
	note.text="Keep both feet in place from frame %d.\nRelease lets them follow your pose keys again." % first
	correction_box.visible=not selected_foot().is_empty();precise.visible=app.advanced_mode;apply_target.visible=app.advanced_mode and correction_box.visible;load_foot()
	window.popup_centered(Vector2i(460,650 if app.advanced_mode and correction_box.visible else 450 if correction_box.visible else 250))

func nudge(direction: Vector3) -> void:
	var foot:=selected_foot()
	if foot.is_empty():return
	var delta: Vector3=app.renderer.camera.global_basis*direction*step.value
	var position:=Model.Timeline.vector(foot.position)+delta
	apply_correction({"position":[position.x,position.y,position.z]})

func reverse_knee() -> void:
	var foot:=selected_foot()
	if not foot.is_empty():apply_correction({"flip_bend":not foot.get("flip_bend",false)})

func apply_fields() -> void:
	var foot:=selected_foot()
	if foot.is_empty():return
	var p:=field_vector(position_fields,loaded_position);var r:=field_vector(rotation_fields,loaded_rotation)
	var rotation: Array=foot.rotation_xyzw.duplicate()
	if r!=loaded_rotation:
		var q:=Quaternion.from_euler(r*PI/180).normalized();rotation=[q.x,q.y,q.z,q.w]
	var pole:=field_vector(pole_fields,loaded_pole)
	var changes:={"position":[p.x,p.y,p.z],"rotation_xyzw":rotation,"pole":[pole.x,pole.y,pole.z] if use_pole.button_pressed else null}
	apply_correction(changes)

func apply_correction(changes: Dictionary) -> void:
	var rig: RefCounted=app.renderer.active_model()
	if not window.visible or not rig or rig.data!=before or not is_instance_valid(target_root) or rig.root!=target_root or app.frame!=first or app.exporting or live_busy():note.text="The scene changed. Close this window and choose the range again.";return
	if has_draft(rig):note.text="Record your draft pose before correcting planted feet.";return
	var changed:=Correction.edit(before,first,int(end_frame.value)+1,foot_choice.selected,changes,int(app.video.duration_frames))
	if changed.has("error"):note.text=changed.error;return
	if not changed.changed:note.text="This foot target is unchanged.";return
	var error:=correction_error(rig,changed.data,first,int(end_frame.value)+1)
	if not error.is_empty():note.text=error;return
	window.hide();error=app.pose_editor.restore_state(changed.data)
	if not error.is_empty():app.message(error);return
	app.refresh_timeline();app.message("Corrected %s for frames %d–%d. Undo restores its target." % [foot_choice.get_item_text(foot_choice.selected).to_lower(),first,int(end_frame.value)])

func correction_error(rig: RefCounted,value: Dictionary,from_frame: int,to_frame: int) -> String:
	var probe:=Model.new();probe.root=rig.root;probe.base_root=rig.base_root;probe.order=rig.order;probe.bones=rig.bones;probe.world_context=rig.world_context;probe.data=value
	var error:=probe.check_bindings()
	if not error.is_empty():return error
	for frame in range(from_frame,to_frame):
		probe.sample(frame)
		if not probe.evaluation_error.is_empty():return "Frame %d: %s Choose a smaller adjustment or a shorter range." % [frame,probe.evaluation_error]
	var world: Dictionary=app.current_world()
	for i in range(world.objects.size()):
		if world.objects[i].id==rig.data.id:world.objects[i]=value
	return "This correction exceeds the1MiB project metadata limit." if metadata_bytes(world)>1024*1024 else ""

func apply_range(plant: bool) -> void:
	var rig: RefCounted=app.renderer.active_model()
	if not window.visible or not rig or rig.data!=before or not is_instance_valid(target_root) or rig.root!=target_root or app.frame!=first or app.exporting or live_busy():
		note.text="The scene changed. Close this window and choose the range again.";return
	if end_frame.value<first:note.text="The last frame must follow the first frame.";return
	var target:={}
	if plant:
		if has_draft(rig):note.text="Record your draft pose before planting feet.";return
		var captured:=Ranges.Contact.Contacts.capture(rig,0,1,str(ResourceUID.create_id()))
		if captured.has("error"):note.text=captured.error;return
		target=captured.segments[0]
	var changed:=Ranges.edit(before,first,int(end_frame.value)+1,target,int(app.video.duration_frames))
	if changed.has("error"):note.text=changed.error;return
	if not changed.changed:note.text="The feet already follow their pose keys in this range.";return
	var probe:=Model.new();probe.root=rig.root;probe.base_root=rig.base_root;probe.order=rig.order;probe.bones=rig.bones;probe.world_context=rig.world_context;probe.data=changed.data
	var error: String=probe.check_bindings()
	if plant and error.is_empty():
		for frame in range(first,int(end_frame.value)+1):
			probe.sample(frame)
			if not probe.evaluation_error.is_empty():error="Frame %d: %s Move the body less or choose a shorter range." % [frame,probe.evaluation_error];break
	if not error.is_empty():note.text=error;return
	# Bound the complete world's metadata before a history edit; raster bytes stay separate.
	var world: Dictionary=app.current_world()
	for i in range(world.objects.size()):
		if world.objects[i].id==rig.data.id:world.objects[i]=changed.data
	if metadata_bytes(world)>1024*1024:note.text="This range exceeds the1MiB project metadata limit. Shorten it or remove unused animation.";return
	window.hide()
	error=app.pose_editor.restore_state(changed.data)
	if not error.is_empty():app.message(error);return
	app.refresh_timeline();app.message(("Feet planted" if plant else "Feet released")+" for frames %d–%d. Undo restores the range." % [first,int(end_frame.value)])

func has_draft(rig: RefCounted) -> bool:
	if not rig.has_animation() or rig.data.draft_frame!=first:return false
	if not app.pose_editor.same_transform(rig.sample_transform(first,true),rig.sample_transform(first)):return true
	var a: Dictionary=rig.sample_body(first,true);var b: Dictionary=rig.sample_body(first)
	for id in a.keys()+b.keys():
		if not app.pose_editor.same_transform(a.get(id,Model.identity()),b.get(id,Model.identity())):return true
	return false

func live_busy() -> bool:
	return app.physics_editor.is_running() or not app.physics_editor.pending.is_empty() or not app.physics_editor.import_starts.is_empty()

func affected(edited: RefCounted) -> Array:
	var result:=[]
	if not edited:return result
	var rigs: Array=app.renderer.world_runtime.instances.values() if app.renderer.world_runtime else [edited]
	for rig in rigs:
		if Model.is_contact(rig.data) and (rig==edited or edited.root.is_ancestor_of(rig.root)):result.append(rig)
	return result

func reach_error(edited: RefCounted,frame: int,draft:=false) -> String:
	for rig in affected(edited):
		rig.sample(frame,draft and rig==edited,str(edited.data.id) if draft else "")
		if not rig.evaluation_error.is_empty():return "%s: %s" % [rig.data.name,rig.evaluation_error]
	return ""

func metadata_bytes(world: Dictionary) -> int:
	var layers:=[]
	for layer in app.layers:
		var cels:=[]
		for cel in layer.cels:cels.append({"id":cel.id,"start":cel.start,"duration":cel.duration,"path":"cels/"+"0".repeat(128+str(cel.id).length())+".png","pixel_sha256":"0".repeat(64)})
		layers.append({"id":layer.id,"name":layer.name,"visible":layer.visible,"cels":cels})
		if layer.has("opacity"):layers[-1].opacity=layer.opacity
		if layer.has("origin"):layers[-1].origin=layer.origin
	var audio: Dictionary=preload("res://src/audio_track.gd").metadata(app.audio_document())
	return JSON.stringify({"world":preload("res://src/world_document.gd").portable(world),"video":app.video,"camera_keys":app.keys,"layers":layers,"audio":audio,"editor":{"frame":app.frame}},"",true,true).to_utf8_buffer().size()+8192
