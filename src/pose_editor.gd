extends Node
const BoneLabels=preload("res://src/bone_labels.gd")
const Model = preload("res://src/model.gd")
const Timeline = preload("res://src/timeline.gd")
const LimbIK=preload("res://src/limb_ik.gd")
const Joints=preload("res://src/joint_constraints.gd")
const FootHold=preload("res://src/foot_hold.gd")
var app
var panel: VBoxContainer
var tree: Tree
var search: LineEdit
var operation: OptionButton
var space: OptionButton
var snap: CheckButton
var fields: Array[SpinBox] = []
var locks: Array[CheckBox] = []
var scale_field: SpinBox
var interpolation: OptionButton
var visible_toggle: CheckButton
var reference_toggle: CheckButton
var reference_opacity_row: HBoxContainer
var reference_opacity: SpinBox
var apply_reference_opacity: Button
var info: Label
var selected := "@root"
var tree_items := {}
var handles: Array = []
var joints: Array = []
var dragging := false
var drag_before := {}
var drag_start := Vector2.ZERO
var drag_axis := Vector3.ZERO
var drag_world := Transform3D.IDENTITY
var drag_screen_axis := Vector2.ZERO
var drag_pixels := 80.0
var drag_units := 1.0
var drag_ring_start := Vector3.ZERO
var drag_ring_previous := 0.0
var drag_ring_angle := 0.0
var import_control: Button
var scale_apply: Button
var auto_key: CheckButton
var reveal_bones := false
var limb_ik: CheckButton
var flip_bend: Button
var source_shape: CheckButton
var base_shapes: Node
var animated_shapes: Node
var shape_button: Button
var shape_window: Window
var shape_close: Button
var drag_chain:={}
var drag_joints:={}
var hold_feet: CheckButton
var drag_feet:={}
var contacts: Node
var motion: Node
var movement_path: Node
var pose_library: Node

func active_rig() -> RefCounted:
	return app.renderer.active_model()

func setup(owner_app, parent: Node) -> void:
	app = owner_app
	panel = app.section(parent, "Model / pose", "scene")
	import_control = app.button(panel, "Add model…", import_dialog)
	app.advanced(import_control)
	app.button(panel, "Frame model", frame_model)
	shape_button=app.button(panel,"Shapes / expressions…",open_shapes)
	app.label(panel,"Hold Alt to reveal bones.").add_theme_font_size_override("font_size",12)
	app.button(panel, "Record pose key", record_dialog)
	pose_library=preload("res://src/pose_library_editor.gd").new();add_child(pose_library);pose_library.setup(self,panel)
	auto_key = CheckButton.new()
	auto_key.text = "Auto-key pose edits"
	auto_key.button_pressed = true
	auto_key.tooltip_text = "Completed model/bone edits create a key at the current frame. Camera keys remain explicit. Turn off for static draft editing."
	panel.add_child(app.advanced(auto_key))
	auto_key.toggled.connect(func(_value): refresh_values())
	info = app.label(panel, "Add a prepared GLB model. Native imports share this standard pose system.")
	info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	search = LineEdit.new()
	search.placeholder_text = "Find bone (English or original)…"
	search.text_changed.connect(func(_text): rebuild_tree())
	panel.add_child(search)
	tree = Tree.new()
	tree.custom_minimum_size = Vector2(220, 125)
	tree.hide_root = false
	tree.item_selected.connect(func():
		if tree.get_selected(): selected = tree.get_selected().get_metadata(0); refresh_values())
	var system_font := SystemFont.new()
	system_font.font_names = PackedStringArray(["Yu Gothic UI", "Segoe UI", "Arial"])
	tree.add_theme_font_override("font", system_font)
	panel.add_child(tree)
	operation = OptionButton.new()
	operation.add_item("Rotate")
	operation.add_item("Move")
	operation.tooltip_text="Rotate with a colored axis ring, or use the outer pale ring to turn relative to your view. Unlock all axes to use the outer ring."
	operation.item_selected.connect(func(_index): refresh_values())
	panel.add_child(operation)
	space = OptionButton.new()
	space.add_item("Local axes")
	space.add_item("World axes")
	panel.add_child(space)
	panel.move_child(operation, 4)
	panel.move_child(space, 5)
	limb_ik=CheckButton.new();limb_ik.text="Move limbs naturally";limb_ik.button_pressed=true
	limb_ik.tooltip_text="Move a supported hand or foot to bend its limb. Imported joint controls also move their linked bones. Turn off for direct bone posing."
	panel.add_child(limb_ik);panel.move_child(limb_ik,6)
	limb_ik.toggled.connect(func(_value):finish_drag();refresh_values())
	hold_feet=CheckButton.new();hold_feet.text="Hold feet while posing"
	hold_feet.tooltip_text="Move the root or a body joint above both legs while keeping both feet in place. Frozen physics required. Saves editable leg poses, not a playback contact lock. Off at launch."
	panel.add_child(hold_feet);panel.move_child(hold_feet,7)
	hold_feet.toggled.connect(func(_value):finish_drag();refresh_values())
	contacts=preload("res://src/contact_editor.gd").new();contacts.app=app;app.add_child(contacts);contacts.setup(panel)
	motion=preload("res://src/motion_editor.gd").new();motion.app=app;app.add_child(motion);motion.setup(panel)
	movement_path=preload("res://src/movement_path_editor.gd").new();movement_path.app=app;app.add_child(movement_path);movement_path.setup(panel)
	flip_bend=app.button(panel,"Reverse limb bend",reverse_limb_bend);app.advanced(flip_bend)
	snap = CheckButton.new()
	snap.text = "Snap (15° / 0.1 units)"
	panel.add_child(app.advanced(snap))
	for axis in ["X", "Y", "Z"]:
		fields.append(app.advanced_spin(panel, "Local " + axis, -100000, 100000, 0))
	app.advanced(app.button(panel, "Apply local values", apply_numeric))
	var lock_row := HBoxContainer.new()
	panel.add_child(lock_row)
	app.advanced(lock_row)
	for axis in ["X", "Y", "Z"]:
		var lock := CheckBox.new()
		lock.text = "Lock " + axis
		lock.tooltip_text="Keep this axis locked. The camera-facing rotation ring is available when all axes are unlocked."
		lock_row.add_child(lock)
		locks.append(lock)
	scale_field = app.advanced_spin(panel, "Model uniform scale", 0.001, 10000, 1)
	scale_field.step = 0.001
	scale_apply = app.button(panel, "Apply model scale", apply_scale)
	app.advanced(scale_apply)
	app.advanced(app.button(panel, "Reset selected", reset_selected))
	interpolation = OptionButton.new()
	for name in ["ease", "linear", "hold"]: interpolation.add_item(name)
	panel.add_child(app.advanced(interpolation))
	app.advanced(app.button(panel, "Delete selected part key", delete_key))
	app.advanced(app.button(panel, "Save view as camera key", app.key_dialog))
	visible_toggle = CheckButton.new()
	visible_toggle.text = "Visible at this frame"
	visible_toggle.tooltip_text="Records visibility here. It stays until the next visibility key, independently of animation pieces."
	visible_toggle.toggled.connect(set_visibility_key)
	panel.add_child(visible_toggle)
	app.button(panel,"Remove visibility key here",remove_visibility_key).tooltip_text="Restore the preceding visibility state at this frame. Undo restores the key."
	reference_toggle = CheckButton.new()
	reference_toggle.text = "Reference only (hide in movie)"
	reference_toggle.toggled.connect(func(value): set_flag("reference_only", value))
	panel.add_child(reference_toggle)
	reference_opacity_row=HBoxContainer.new();panel.add_child(reference_opacity_row)
	app.label(reference_opacity_row,"Reference opacity (%)")
	reference_opacity=SpinBox.new();reference_opacity.min_value=0;reference_opacity.max_value=100;reference_opacity.step=1;reference_opacity.value=100;reference_opacity_row.add_child(reference_opacity)
	reference_opacity.tooltip_text="Working reference transparency only. Reference-only objects stay hidden in the movie."
	apply_reference_opacity=app.button(reference_opacity_row,"Apply",func():set_reference_opacity(reference_opacity.value))
	reference_opacity.get_line_edit().text_submitted.connect(func(_text):reference_opacity.apply();set_reference_opacity(reference_opacity.value))
	source_shape=CheckButton.new();source_shape.text="Use imported shape"
	source_shape.tooltip_text="Use declared model defaults underneath base-shape adjustments. Turning this off keeps your adjustments. This is a saved whole-project setting, not a pose key."
	panel.add_child(app.advanced(source_shape));source_shape.toggled.connect(set_source_shape)
	base_shapes=preload("res://src/base_shape_editor.gd").new();base_shapes.app=app;app.add_child(base_shapes);base_shapes.setup(panel)
	shape_window=Window.new();shape_window.title="Shapes at this frame";shape_window.theme=app.theme;app.add_child(shape_window)
	shape_window.close_requested.connect(func():shape_window.hide())
	var shape_panel:=PanelContainer.new();shape_window.add_child(shape_panel);shape_panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var shape_column:=VBoxContainer.new();shape_panel.add_child(shape_column)
	var shape_scroll:=ScrollContainer.new();shape_scroll.size_flags_vertical=Control.SIZE_EXPAND_FILL;shape_scroll.horizontal_scroll_mode=ScrollContainer.SCROLL_MODE_DISABLED;shape_column.add_child(shape_scroll)
	var shape_body:=VBoxContainer.new();shape_body.size_flags_horizontal=Control.SIZE_EXPAND_FILL;shape_scroll.add_child(shape_body)
	animated_shapes=preload("res://src/base_shape_editor.gd").new();animated_shapes.app=app;animated_shapes.animated=true;app.add_child(animated_shapes);animated_shapes.setup(shape_body)
	shape_close=app.button(shape_column,"Close",func():shape_window.hide())
	app.renderer.assets_changed.connect(func():shape_window.hide())
	app.advanced(app.button(panel, "Remove object", remove_dialog))
	app.label(panel, "Hold Alt to reveal all bones.\nClick a joint, then drag a colored handle.\nPose edits create keys automatically.\nEsc cancels a pose drag.").autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	rebuild_tree()

func sync_enabled(node: Node = panel) -> void:
	for child in node.get_children():
		if child == import_control: continue
		if child is BaseButton: child.disabled = active_rig() == null
		if child is SpinBox or child is LineEdit: child.editable = active_rig() != null
		sync_enabled(child)

func import_dialog() -> void:
	app.choose_file("Add 3D model", ["*.has", "*.gltf", "*.fbx", "*.obj", "*.pmd", "*.pmx", "*.vrm", "*.mdl", "*.gma", "*.bin"], func(path):app.import_actions.add(path,true,0), app.source_import.default_browse_dir())

func remove_dialog() -> void:
	if not active_rig():return
	if app.renderer.world_runtime:
		var id: String=active_rig().data.id
		app.confirm_action("Remove this object and its child objects? Undo restores them.",func():app.remove_world_object(id))
	else:app.confirm_action("Remove this model? Undo restores it.",func():restore_state({}))

func add_model(path: String, start_frame := 0, placement := {}) -> String:
	if path.get_extension().to_lower() != "glb": app.source_import.start(path, true, start_frame,placement); return ""
	var value:=definition(path)
	if value.has("error"):app.message(value.error);return value.error
	return app.append_object(value.data,"model",start_frame,placement)

func definition(path: String) -> Dictionary:
	var data := Model.definition(path)
	var report := path.get_base_dir().path_join("parameters.json")
	var file := FileAccess.open(report, FileAccess.READ) if FileAccess.file_exists(report) else null
	if FileAccess.file_exists(report):
		if file == null or file.get_length() > 256 * 1024:
			return {"error":"Cannot preserve parameter report (unreadable or over 256 KiB). Object not added."}
		var parser := JSON.new()
		if parser.parse(file.get_as_text()) != OK or not parser.data is Dictionary:
			return {"error":"Parameter report is invalid JSON; object not added."}
		data.name = str(parser.data.get("source_file", data.name)).left(200)
		data.metadata = {"native_parameters": parser.data, "external_bundle": path.get_base_dir(), "note": "Keep full native preparation bundle; only GLB and this supplied report are managed here. Native fidelity is not implied."}
	data.metadata["source_shape"]={"format":"studio_source_shape_1","enabled":true}
	return {"data":data}

func restore_state(data: Dictionary, history := true) -> String:
	app.stop()
	if app.renderer.world_runtime:
		if data.is_empty():
			app.message("Removing world objects is being connected; the current object has been kept.")
			return app.status.text
		var target: RefCounted=app.renderer.world_runtime.instance(str(data.get("id","")))
		if not target:return "World edit refers to a missing instance."
		var previous: Dictionary=target.data.duplicate(true)
		var error: String=app.renderer.world_runtime.restore_instance(data.id,data)
		if not error.is_empty():app.message(error);return error
		if history:
			app.push_history({"type":"world_object","object_id":data.id,"before":previous,"after":data.duplicate(true)})
			app.changed()
		rebuild_tree();apply_frame()
		return ""
	var before: Dictionary = (active_rig().data if active_rig() else {}).duplicate(true)
	var error := Model.validate(data, app.video.duration_frames)
	if not error.is_empty(): app.message(error); return error
	if active_rig() and not data.is_empty() and active_rig().data.source == data.source and active_rig().data.sha256 == data.sha256:
		var shape_error:=Model.Shape.check(active_rig().root,Model.Shape.setting(data))
		if not shape_error.is_empty():app.message(shape_error);return shape_error
		active_rig().data = data.duplicate(true)
	else:
		var prepared: Dictionary = app.renderer.prepare_model(data)
		if prepared.has("error"): app.message(prepared.error); return prepared.error
		app.renderer.install_model(prepared)
	if history:
		app.push_history({"type": "model", "before": before, "after": data.duplicate(true)})
		app.changed()
	rebuild_tree()
	apply_frame()
	return ""

func commit(before: Dictionary, authored := false) -> void:
	app.stop()
	var rig = app.renderer.world_runtime.instance(str(before.get("id",""))) if app.renderer.world_runtime else active_rig()
	if not rig:return
	var affects_contacts: bool=not contacts.affected(rig).is_empty()
	if authored and affects_contacts:
		var error: String=contacts.reach_error(rig,app.frame,true)
		if not error.is_empty():
			rig.data=before.duplicate(true);apply_frame();refresh_values();app.message(error+" Move less, or release the feet here.");return
	var keyed := false
	if authored and auto_key.button_pressed:
		var previous := Model.new()
		previous.data = before
		previous.motion_video=rig.motion_video.duplicate(true)
		var pose: Dictionary = rig.sample_body(app.frame,true) if Model.is_contact(rig.data) else rig.sample(app.frame, true)
		var transform: Dictionary = rig.sample_transform(app.frame, true)
		var old_pose := previous.sample_body(app.frame,true) if Model.is_contact(before) else previous.sample(app.frame, true)
		var old_transform:=previous.sample_transform(app.frame,true)
		var different := not same_transform(transform, old_transform)
		var channels: Array=["@root"] if different else []
		for id in pose.keys() + old_pose.keys():
			if not same_transform(pose.get(id, Model.identity()), old_pose.get(id, Model.identity())):
				different=true
				if not id in channels:channels.append(id)
		if different:
			var key:={"frame": app.frame, "pose": pose, "transform": transform, "authored_channels":channels,"interpolation": interpolation.get_item_text(interpolation.selected)}
			if before.get("format")=="studio_model_9" and "@root" in channels:key["root_component_fields"]=load("res://src/root_component_document.gd").changed_root_fields(old_transform,transform)
			var error: String=rig.put_pose_key(key,int(app.video.duration_frames),false,before)
			if not error.is_empty():
				rig.data=before.duplicate(true);apply_frame();refresh_values();app.message(error);return
			keyed = true
	if keyed and affects_contacts:
		for at in range(int(app.video.duration_frames)+1):
			var error: String=contacts.reach_error(rig,at)
			if not error.is_empty():
				rig.data=before.duplicate(true);apply_frame();refresh_values();app.message("Frame %d: %s Move less, or release the feet there." % [at,error]);return
		if contacts.metadata_bytes(app.current_world())>1024*1024:
			rig.data=before.duplicate(true);apply_frame();refresh_values();app.message("This pose exceeds the1MiB project metadata limit. Use fewer keys or a shorter range.");return
	var after: Dictionary = rig.data.duplicate(true)
	if JSON.stringify(before) != JSON.stringify(after):
		var command:={"type":"model","before":before,"after":after}
		if app.renderer.world_runtime:command.type="world_object";command["object_id"]=rig.data.id
		app.push_history(command)
		app.changed()
	apply_frame()
	refresh_values()
	if keyed: app.message("Pose key saved automatically at frame %d. Undo restores the edit and its key." % app.frame)
	elif authored and before != after and not auto_key.button_pressed:
		app.message("Pose adjusted. Use Record pose key to keep this pose on the timeline.")

func same_transform(a: Dictionary, b: Dictionary) -> bool:
	var qa := Timeline.quaternion(a.rotation_xyzw)
	var qb := Timeline.quaternion(b.rotation_xyzw)
	if qa.dot(qb) < 0: qb = -qb
	var difference := Vector4(qa.x-qb.x, qa.y-qb.y, qa.z-qb.z, qa.w-qb.w)
	# Absolute tolerances keep small authored moves keyable far from world origin.
	return Timeline.vector(a.position).distance_squared_to(Timeline.vector(b.position)) <= 1e-12 and difference.length_squared() <= 1e-12 and absf(float(a.get("scale", 1))-float(b.get("scale", 1))) <= 1e-7

func rebuild_tree() -> void:
	sync_enabled()
	tree.clear()
	tree_items.clear()
	if not active_rig():
		if source_shape:source_shape.visible=false
		if reference_opacity_row:reference_opacity_row.hide()
		info.text = "No model. Add a prepared GLB to pose."
		return
	var rig = active_rig()
	var root_item := tree.create_item()
	root_item.set_text(0, rig.data.name + " / root")
	root_item.set_metadata(0, "@root")
	tree_items["@root"] = root_item
	for id in rig.order:
		if search.text.is_empty(): make_tree_item(id)
		elif BoneLabels.matches(str(rig.bones[id].name),search.text,BoneLabels.role(rig.data,str(rig.bones[id].name))):
			var item := tree.create_item(root_item)
			item.set_text(0, BoneLabels.display(str(rig.bones[id].name),app.advanced_mode,BoneLabels.role(rig.data,str(rig.bones[id].name))))
			item.set_metadata(0, id)
			item.set_tooltip_text(0,BoneLabels.tooltip(str(rig.bones[id].name),id,app.advanced_mode,BoneLabels.role(rig.data,str(rig.bones[id].name))))
			tree_items[id] = item
	if not tree_items.has(selected): selected = "@root"
	tree_items[selected].select(0)
	tree.scroll_to_item(tree_items[selected])
	visible_toggle.set_pressed_no_signal(rig.visible_at(app.frame))
	reference_toggle.set_pressed_no_signal(rig.data.reference_only)
	refresh_values()

func refresh_labels() -> void:
	var rig=active_rig()
	if not rig:return
	for id in tree_items:
		if id=="@root":continue
		var name: String=rig.bones[id].name
		var role:=BoneLabels.role(rig.data,name)
		tree_items[id].set_text(0,BoneLabels.display(name,app.advanced_mode,role))
		tree_items[id].set_tooltip_text(0,BoneLabels.tooltip(name,id,app.advanced_mode,role))

func make_tree_item(id: String) -> TreeItem:
	if tree_items.has(id): return tree_items[id]
	var rig = active_rig()
	var parent: String = rig.parent_id(id)
	var item := tree.create_item(tree_items["@root"] if parent == "@root" else make_tree_item(parent))
	item.set_text(0, BoneLabels.display(str(rig.bones[id].name),app.advanced_mode,BoneLabels.role(rig.data,str(rig.bones[id].name))))
	item.set_metadata(0, id)
	item.set_tooltip_text(0, BoneLabels.tooltip(str(rig.bones[id].name),id,app.advanced_mode,BoneLabels.role(rig.data,str(rig.bones[id].name))))
	tree_items[id] = item
	return item

func refresh_values() -> void:
	if motion:motion.sync()
	if movement_path:movement_path.sync()
	if app.physics_editor:app.physics_editor.sync()
	if base_shapes:base_shapes.sync()
	if animated_shapes:animated_shapes.sync()
	if shape_button:shape_button.visible=active_rig()!=null and (not active_rig().root.get_meta(Model.Shape.META,{"rows":[]}).rows.is_empty() or preload("res://src/expression_presets.gd").has_data(active_rig().root));shape_button.disabled=app.exporting or app.playing
	if source_shape:source_shape.visible=app.advanced_mode and active_rig()!=null and not active_rig().root.get_meta(Model.Shape.META,{"rows":[]}).rows.is_empty()
	if reference_opacity_row:reference_opacity_row.visible=active_rig()!=null and active_rig().data.reference_only
	if not active_rig(): return
	var rig = active_rig()
	reference_toggle.set_pressed_no_signal(rig.data.reference_only)
	reference_opacity.set_value_no_signal(float(rig.data.get("reference_opacity",1.))*100)
	apply_reference_opacity.disabled=app.exporting or app.playing
	if source_shape:source_shape.set_pressed_no_signal(Model.Shape.enabled(rig.data))
	visible_toggle.set_pressed_no_signal(rig.visible_at(app.frame))
	var value: Dictionary = rig.sample_transform(app.frame, true) if selected == "@root" else rig.sample(app.frame, true).get(selected, Model.identity())
	var values := Timeline.vector(value.position) if operation.selected == 1 else Timeline.quaternion(value.rotation_xyzw).get_euler() * 180.0 / PI
	for i in range(3):
		fields[i].step = 0.01 if operation.selected == 1 else 1
		fields[i].set_value_no_signal(values[i])
	scale_field.set_value_no_signal(rig.sample_transform(app.frame, true).scale)
	info.text = "%s • %d bones\n%s\n%s" % [rig.data.name, rig.order.size(), "No animation pieces: hidden in movie." if rig.data.has("animation_clips") and rig.data.animation_clips.is_empty() else "Visibility off at this frame." if not rig.visible_at(app.frame) else "Reference only: hidden in movie." if rig.data.reference_only else "Static pose: included in movie." if not rig.has_animation() else "Animation uses recorded keys.", "Auto-key: edits save at this frame." if auto_key.button_pressed else "Auto-key off: record edits explicitly."]
	if not rig.evaluation_error.is_empty():info.text+="\n"+rig.evaluation_error+" Release feet or correct the body pose."
	if app.timeline:app.timeline.sync_bone(selected)

func apply_frame() -> void:
	if app.renderer.world_runtime:
		app.renderer.world_runtime.evaluate(app.frame,false,app.renderer.active_instance_id if app.mode.selected==2 and not app.playing else "",app.video)
	elif active_rig(): active_rig().apply(app.frame, app.mode.selected == 2 and not app.playing,false,app.video)
	app.canvas.queue_redraw()

func begin_draft() -> void:
	var moving_fan: bool=active_rig()!=null and preload("res://src/airflow.gd").is_fan(active_rig().data) and not app.physics_editor.active(active_rig().data.id)
	if app.physics_editor and not moving_fan:
		app.physics_editor.freeze_all()
		app.physics_editor.clear_previews()
	var rig = active_rig()
	if rig.data.draft_frame != app.frame:
		var transform: Dictionary = rig.sample_authored_transform(app.frame)
		rig.data.position = transform.position
		rig.data.rotation_xyzw = transform.rotation_xyzw
		rig.data.scale = transform.scale
		rig.data.pose = rig.sample_body(app.frame) if Model.is_contact(rig.data) else rig.sample(app.frame)
		if rig.data.get("format")==Model.ShapeAnimation.LEGACY_FORMAT:rig.data.shape_pose=rig.sample_shapes(app.frame)
		rig.data.draft_frame = app.frame

func set_delta(position: Vector3, rotation: Quaternion) -> void:
	begin_draft()
	var value := {"position": [position.x, position.y, position.z], "rotation_xyzw": [rotation.x, rotation.y, rotation.z, rotation.w]}
	if selected == "@root":
		active_rig().data.position = value.position
		active_rig().data.rotation_xyzw = value.rotation_xyzw
	else:
		active_rig().data.pose[selected] = value

func apply_numeric() -> void:
	if not active_rig(): return
	var contact_error:=contact_edit_error()
	if not contact_error.is_empty():app.message(contact_error);return
	var before: Dictionary = active_rig().data.duplicate(true)
	var old: Dictionary = active_rig().sample_transform(app.frame, true) if selected == "@root" else active_rig().sample(app.frame, true).get(selected, Model.identity())
	var values := Vector3(fields[0].value, fields[1].value, fields[2].value)
	var p := Timeline.vector(old.position)
	var r := Timeline.quaternion(old.rotation_xyzw).get_euler() * 180 / PI
	for i in range(3):
		if not locks[i].button_pressed:
			if operation.selected == 0: r[i] = snappedf(values[i], 15) if snap.button_pressed else values[i]
			else: p[i] = snappedf(values[i], 0.1) if snap.button_pressed else values[i]
	if p==Timeline.vector(old.position) and operation.selected==1:return
	var joints_plan:=joint_plan()
	if joints_plan.has("error"):app.message(joints_plan.error);return
	var desired_rotation:=Quaternion.from_euler(r*PI/180)
	if not joints_plan.is_empty() and same_transform({"position":[p.x,p.y,p.z],"rotation_xyzw":[desired_rotation.x,desired_rotation.y,desired_rotation.z,desired_rotation.w]},old):return
	var feet:=prepare_feet()
	if feet.has("error"):app.message(feet.error);return
	set_delta(p, Quaternion.from_euler(r * PI / 180))
	if not joints_plan.is_empty():
		var solved:=Joints.solve(active_rig(),joints_plan,active_rig().data.pose)
		if solved.has("error"):active_rig().data=before;apply_frame();refresh_values();app.message(solved.error);return
		active_rig().data.pose=solved.pose
	if not feet.is_empty():
		apply_frame()
		var error:=FootHold.solve(active_rig(),feet,apply_frame)
		if not error.is_empty():active_rig().data=before;apply_frame();refresh_values();app.message(error);return
	commit(before, true)

func joint_plan() -> Dictionary:
	if not limb_ik.button_pressed or selected=="@root":return {}
	var rig=active_rig();var result:=Joints.plan(rig,selected)
	if result.is_empty() or result.has("error"):return result
	if Model.is_contact(rig.data):
		var segment: Dictionary=Model.contact_animation().Contacts.active(rig.data.animation_clips,app.frame)
		for foot in segment.get("feet",[]):
			for chain in result.chains:
				if chain.effector in foot.ids:return {"error":"Release planted feet before moving this joint control."}
				for link in chain.links:
					if link.id in foot.ids:return {"error":"Release planted feet before moving this joint control."}
	return result

func apply_scale() -> void:
	if not active_rig() or app.exporting:return
	# This is a root operation even when a planted leg is selected. Share the
	# live guard with other edits without treating it as a direct leg edit.
	var error:=contact_live_edit_error()
	if not error.is_empty():app.message(error);return
	var before: Dictionary=active_rig().data.duplicate(true)
	begin_draft();active_rig().data.scale=scale_field.value;commit(before,true)

func prepare_feet() -> Dictionary:
	if not hold_feet.button_pressed or operation.selected!=1:return {}
	var rig=active_rig();var legs:=FootHold.chains(rig)
	if Model.is_contact(rig.data) and not Model.contact_animation().Contacts.active(rig.data.animation_clips,app.frame).is_empty():return {}
	# A hand/individual leg remains freely poseable with this option enabled.
	if selected!="@root" and not FootHold.supports(rig,selected,legs):return {}
	if app.physics_editor.is_running():return {"error":"Turn Physics and Hair & clothes off before holding feet."}
	if legs.is_empty():return {"error":"Hold feet needs two supported legs. Turn it off to move this object freely."}
	return FootHold.capture(rig,selected)

func reset_selected() -> void:
	var contact_error:=contact_edit_error()
	if not contact_error.is_empty():app.message(contact_error);return
	if not active_rig(): return
	var before: Dictionary = active_rig().data.duplicate(true)
	var joints_plan:=joint_plan()
	if joints_plan.has("error"):app.message(joints_plan.error);return
	if not joints_plan.is_empty() and same_transform(active_rig().sample(app.frame,true).get(selected,Model.identity()),Model.identity()):return
	set_delta(Vector3.ZERO, Quaternion.IDENTITY)
	if not joints_plan.is_empty():
		var solved:=Joints.solve(active_rig(),joints_plan,active_rig().data.pose)
		if solved.has("error"):active_rig().data=before;apply_frame();refresh_values();app.message(solved.error);return
		active_rig().data.pose=solved.pose
	commit(before, true)

func reverse_limb_bend() -> void:
	var contact_error:=contact_edit_error()
	if not contact_error.is_empty():app.message(contact_error);return
	if not active_rig() or app.exporting:return
	finish_drag()
	var rig=active_rig();var limb:=LimbIK.chain(rig,selected)
	if limb.is_empty():app.message("Select a supported hand or foot to reverse its bend.");return
	var before: Dictionary=rig.data.duplicate(true);begin_draft();apply_frame()
	var solved:=LimbIK.solve(rig,limb,rig.bone_transform(selected).origin,true)
	if solved.has("error"):restore_state(before,false);app.message(solved.error);return
	rig.data.pose=solved.pose;commit(before,true)

func set_flag(flag: String, value: bool) -> void:
	if not active_rig() or app.exporting: return
	var before: Dictionary = active_rig().data.duplicate(true)
	active_rig().data[flag] = value
	commit(before)

func set_reference_opacity(percent: float) -> void:
	if not active_rig() or app.exporting or app.playing:return
	if not active_rig().data.reference_only:return
	if not is_finite(percent) or percent<0 or percent>100:app.message("Reference opacity must be between0 and100 percent.");return
	var data: Dictionary=active_rig().data.duplicate(true)
	if float(data.get("reference_opacity",1.))==percent/100.:return
	if percent==100:data.erase("reference_opacity")
	else:data["reference_opacity"]=percent/100.
	if restore_state(data).is_empty():app.message("Working reference opacity saved. Undo restores the previous amount.")

func set_source_shape(value: bool) -> void:
	if not active_rig() or app.exporting:return
	app.stop();finish_drag()
	if not app.physics_editor.freeze_all():refresh_values();return
	var data: Dictionary=active_rig().data.duplicate(true)
	var shape:=Model.Shape.setting(data).duplicate(true);shape.enabled=value;data.metadata["source_shape"]=shape
	var error:=restore_state(data)
	if not error.is_empty():refresh_values();return
	app.message("Imported defaults enabled; base adjustments retained." if value else "Imported defaults disabled; base adjustments retained.")

func set_visibility_key(value: bool) -> void:
	if not active_rig() or app.exporting:return
	var data:=preload("res://src/animation_clips.gd").promote(active_rig().data)
	if not Model.ShapeAnimation.has_data(data):data.format=Model.Visibility.FORMAT
	if not data.has("visibility_keys"):data["visibility_keys"]=[]
	Model.Visibility.put(data,app.frame,value)
	if data==active_rig().data:return
	if restore_state(data).is_empty():app.message("Visibility saved at frame %d. It stays until you change it again." % app.frame)

func open_shapes() -> void:
	if not active_rig() or app.exporting:return
	app.stop();finish_drag();app.finish_stroke()
	var height:=mini(520,maxi(360,int(app.get_viewport_rect().size.y)-180))
	shape_window.popup_centered(Vector2i(350,height))
	# Keep the framed subject visible while choosing facial poses.
	shape_window.position=Vector2i(maxi(12,int(app.get_viewport_rect().size.x)-shape_window.size.x-12),maxi(28,mini(150,int(app.get_viewport_rect().size.y)-shape_window.size.y-28)))
	animated_shapes.sync()

func set_shape_amounts(values: Dictionary) -> String:
	if not active_rig() or app.exporting:return "Select an imported model first."
	app.stop();finish_drag();app.finish_stroke()
	if not app.physics_editor.freeze_all():return "Could not freeze the current simulation."
	var rig=active_rig();var original: Dictionary=rig.data.duplicate(true)
	var data:=Model.ShapeAnimation.promote(original)
	var amount_values: Dictionary=rig.sample_shapes(app.frame,true)
	var known:={}
	for row in rig.root.get_meta(Model.Shape.META).rows:known[str(row.node)]=row
	if not Model.ShapeAnimation.values_valid(values):return "Invalid shape amounts."
	var changed:=false;var changes: Dictionary={}
	for node in values:
		if not known.has(node):return "Shape refers to a missing model part."
		var inherited:=Model.Shape.effective(known[node],Model.Shape.setting(original))
		for index in values[node]:
			if int(index)>=inherited.size():return "Shape refers to a missing channel."
			var current: float=amount_values.get(node,{}).get(index,inherited[int(index)])
			if absf(current-float(values[node][index]))<.0000001:continue
			changed=true
			if not data.shape_base.has(node):data.shape_base[node]={}
			if not data.shape_base[node].has(index):data.shape_base[node][index]=inherited[int(index)]
			if not data.shape_starts.has(node):data.shape_starts[node]={}
			if not data.shape_starts[node].has(index):data.shape_starts[node][index]=int(original.get("start_frame",0))
			if not data.has("shape_names"):data["shape_names"]={}
			if not data.shape_names.has(node):data.shape_names[node]={}
			data.shape_names[node][index]=str(known[node].names[int(index)]).left(200)
			if not amount_values.has(node):amount_values[node]={}
			amount_values[node][index]=values[node][index]
			if not changes.has(node):changes[node]={}
			changes[node][index]=values[node][index]
	if not changed:return ""
	data.shape_pose=Model.ShapeAnimation.fill(amount_values,data.shape_base);data.shape_draft_frame=app.frame
	if auto_key.button_pressed:
		data=Model.ShapeAnimation.put_key(data,{"frame":app.frame,"shapes":changes,"interpolation":interpolation.get_item_text(interpolation.selected)},int(app.video.duration_frames))
	var candidate_world: Dictionary=app.current_world()
	for i in range(candidate_world.objects.size()):
		if candidate_world.objects[i].id==data.id:candidate_world.objects[i]=data
	if contacts.metadata_bytes(candidate_world)>1024*1024:return "These deform keys exceed the 1MiB project metadata limit. Use fewer keys or controls."
	var error:=restore_state(data)
	if error.is_empty():app.message("Shape keyed at frame %d." % app.frame if auto_key.button_pressed else "Shape draft changed; Record pose key to save its animation.")
	return error

func remove_shape_key(node: String,index: String) -> void:
	if not active_rig() or app.exporting:return
	app.stop();finish_drag();app.finish_stroke()
	if not app.physics_editor.freeze_all():return
	if not Model.ShapeAnimation.has_control(active_rig().data,app.frame,node,index):return
	var data:=Model.ShapeAnimation.remove_key(active_rig().data,app.frame,node,index)
	if restore_state(data).is_empty():app.message("Shape key removed at frame %d." % app.frame)

func remove_visibility_key() -> void:
	if not active_rig() or app.exporting:return
	var data: Dictionary=active_rig().data.duplicate(true)
	if not data.has("visibility_keys"):return
	data.visibility_keys=data.visibility_keys.filter(func(key):return key.frame!=app.frame)
	if data.visibility_keys==active_rig().data.visibility_keys:return
	restore_state(data)

func record_dialog() -> void:
	if not active_rig(): return
	app.stop()
	for key in active_rig().authored_keys():
		if key.frame == app.frame:
			app.confirm_action("Replace pose key at frame %d? Undo restores it." % app.frame, record_key)
			return
	record_key()

func record_key() -> void:
	if not active_rig(): return
	app.physics_editor.freeze_all()
	app.stop()
	var rig = active_rig()
	var before: Dictionary = rig.data.duplicate(true)
	var pose: Dictionary=rig.sample(app.frame,true)
	var channels: Array=["@root"]+pose.keys()
	var error: String=rig.put_pose_key({"frame": app.frame, "pose": pose, "transform": rig.sample_transform(app.frame, true),"authored_channels":channels,"interpolation": interpolation.get_item_text(interpolation.selected)},int(app.video.duration_frames),true,before)
	if not error.is_empty():app.message(error);return
	commit(before)
	app.message("Pose key recorded at frame %d." % app.frame)

func delete_key() -> void:
	if not active_rig(): return
	var before: Dictionary = active_rig().data.duplicate(true)
	var error: String=active_rig().remove_pose_key(app.frame,int(app.video.duration_frames),selected)
	if not error.is_empty():app.message(error);return
	commit(before)

func frame_model() -> void:
	if not active_rig(): return
	app.mode.select(2)
	app.change_mode(2)
	if app.renderer.frame_scene(active_rig().root):
		app.message("Current model pose framed. This view is temporary; Advanced has Save view as camera key."+(" Large models may include extra space." if app.renderer.last_framing.conservative>0 else ""))
	else:app.message(app.renderer.last_framing.get("error","No mesh geometry to frame."))

func update_gizmo() -> void:
	app.canvas.pose_lines = []
	app.canvas.pose_joints = []
	handles.clear(); joints.clear()
	if contacts.viewport.active and contacts.viewport.draw():return
	if app.mode.selected != 2 or not active_rig(): return
	if app.physics_editor and app.physics_editor.active(active_rig().data.id):return
	var rig = active_rig()
	var camera: Camera3D = app.renderer.camera
	for id in rig.order:
		var transform: Transform3D = rig.bone_transform(id)
		if camera.is_position_behind(transform.origin): continue
		var point := camera.unproject_position(transform.origin)
		joints.append({"id": id, "point": point})
		if reveal_bones or id == selected: app.canvas.pose_joints.append({"point": point, "selected": id == selected})
		var parent: String = rig.parent_id(id)
		if reveal_bones and parent != "@root":
			var origin: Vector3 = rig.bone_transform(parent).origin
			if not camera.is_position_behind(origin): app.canvas.pose_lines.append({"a": point, "b": camera.unproject_position(origin), "color": Color(0.5, 0.9, 1, 0.55)})
	var transform: Transform3D = rig.bone_transform(selected)
	if camera.is_position_behind(transform.origin): return
	var center := camera.unproject_position(transform.origin)
	var depth := maxf(camera.near, -camera.to_local(transform.origin).z)
	var radius := camera.project_position(center + Vector2(70, 0), depth).distance_to(transform.origin)
	var basis := transform.basis.orthonormalized() if space.selected == 0 else Basis.IDENTITY
	var colors := [Color("ef5b50"), Color("6bd978"), Color("6c9eff")]
	for axis in range(3):
		if locks[axis].button_pressed: continue
		var direction: Vector3 = basis[axis]
		var points: Array[Vector2] = []
		if operation.selected == 1:
			points = [center, camera.unproject_position(transform.origin + direction * radius)]
		else:
			for i in range(49):
				var angle := TAU * i / 48
				var point: Vector3 = transform.origin + (basis[(axis + 1) % 3] * cos(angle) + basis[(axis + 2) % 3] * sin(angle)) * radius
				points.append(camera.unproject_position(point))
		for i in range(points.size() - 1):
			app.canvas.pose_lines.append({"a": points[i], "b": points[i + 1], "color": colors[axis]})
		handles.append({"axis": direction, "points": points, "world": transform, "units": radius})
	if operation.selected==0:
		# View-relative rotation is independent of Local/World axis display. A
		# separate outer ring keeps its target clear of the three RGB ellipses.
		var unlocked: bool=locks.all(func(lock):return not lock.button_pressed)
		var view_radius:=radius*(90./70.)
		var points: Array[Vector2]=[]
		for i in range(65):
			var angle:=TAU*i/64.
			var radial: Vector3=(camera.global_basis.x*cos(angle)+camera.global_basis.y*sin(angle))*view_radius
			points.append(camera.unproject_position(transform.origin+radial))
		var color:=Color("e4eaf0") if unlocked else Color(0.65,0.68,0.72,0.4)
		for i in range(points.size()-1):app.canvas.pose_lines.append({"a":points[i],"b":points[i+1],"color":color})
		handles.append({"axis":camera.global_basis.z.normalized(),"points":points,"world":transform,"units":view_radius,"view":true,"enabled":unlocked})
	app.canvas.queue_redraw()

func input(event: InputEvent, point: Vector2) -> void:
	if not active_rig(): return
	# Letterbox margins are outside the displayed 3D view. Continuing gestures
	# still receive motion/release globally, but no invisible handle starts here.
	if event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT and event.pressed and not Rect2(Vector2.ZERO,app.canvas.resolution).has_point(point):return
	if contacts.viewport.active:contacts.viewport.input(event,point);return
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if not event.pressed: finish_drag(); return
		var threshold: float = 10.0 * app.video.width / maxf(1, app.canvas.image_rect().size.x)
		var best := threshold
		var hit := {}
		var hit_segment:=0
		for handle in handles:
			for i in range(handle.points.size() - 1):
				var distance: float = point.distance_to(Geometry2D.get_closest_point_to_segment(point, handle.points[i], handle.points[i + 1]))
				if distance < best: best = distance; hit = handle;hit_segment=i
		if not hit.is_empty():
			if not hit.get("enabled",true):return
			var contact_error:=contact_edit_error()
			if not contact_error.is_empty():app.message(contact_error);return
			var joints_plan:=joint_plan()
			if joints_plan.has("error"):app.message(joints_plan.error);return
			var before: Dictionary=active_rig().data.duplicate(true)
			drag_feet=prepare_feet()
			if drag_feet.has("error"):app.message(drag_feet.error);drag_feet={};return
			dragging = true
			drag_joints=joints_plan
			drag_chain=LimbIK.chain(active_rig(),selected) if limb_ik.button_pressed and operation.selected==1 and drag_joints.is_empty() else {}
			drag_before = before
			drag_start = point; drag_axis = hit.axis; drag_world = hit.world; drag_units = hit.units
			drag_screen_axis = hit.points[-1] - hit.points[0] if operation.selected == 1 else hit.points[hit_segment+1]-hit.points[hit_segment]
			drag_pixels = maxf(1, drag_screen_axis.length())
			if operation.selected==0:
				# Ray/plane angles follow the actual ring and camera. The projected
				# tangent is a usable fallback when its plane is viewed edge-on.
				drag_pixels=maxf(1,drag_screen_axis.length()/ (TAU/(hit.points.size()-1)))
				drag_ring_start=ring_vector(point)
				drag_ring_previous=0.;drag_ring_angle=0.
			return
		for joint in joints:
			if point.distance_to(joint.point) < best:
				best = point.distance_to(joint.point)
				selected = joint.id
		if tree_items.has(selected): tree_items[selected].select(0); tree.scroll_to_item(tree_items[selected])
		refresh_values()
	if event is InputEventMouseMotion and dragging:
		if (not contacts.affected(active_rig()).is_empty() or not drag_joints.is_empty()) and point==drag_start:
			active_rig().data=drag_before.duplicate(true);apply_frame();refresh_values();return
		var value: Dictionary = drag_before if selected == "@root" else active_rig().sample(app.frame, true).get(selected, Model.identity())
		# Always derive from the gesture's original state, so events do not accumulate error.
		var old_data: Dictionary = active_rig().data
		active_rig().data = drag_before
		value = active_rig().sample_transform(app.frame, true) if selected == "@root" else active_rig().sample(app.frame, true).get(selected, Model.identity())
		active_rig().data = old_data
		var position := Timeline.vector(value.position)
		var rotation := Timeline.quaternion(value.rotation_xyzw)
		if operation.selected == 0:
			var angle:=ring_angle(point)
			if snap.button_pressed: angle = snappedf(angle, deg_to_rad(15))
			if selected == "@root":
				var axis:=drag_axis
				if active_rig().root.get_parent() is Node3D:axis=active_rig().root.get_parent().global_basis.orthonormalized().inverse()*axis
				rotation = Quaternion(axis.normalized(), angle) * rotation
			else: rotation = rotation * Quaternion((drag_world.basis.orthonormalized().inverse() * drag_axis).normalized(), angle)
		else:
			var amount := (point - drag_start).dot(drag_screen_axis.normalized()) / drag_pixels * drag_units
			if snap.button_pressed: amount = snappedf(amount, 0.1)
			if not drag_feet.is_empty() and is_zero_approx(amount):
				active_rig().data=drag_before.duplicate(true);apply_frame();refresh_values();return
			if not drag_chain.is_empty():
				var rig=active_rig();rig.data=drag_before.duplicate(true);begin_draft();apply_frame()
				var solved:=LimbIK.solve(rig,drag_chain,drag_world.origin+drag_axis*amount)
				if solved.has("error"):rig.data=drag_before.duplicate(true);app.message(solved.error)
				else:
					rig.data.pose=solved.pose
					app.message("Target is beyond this limb's reach. Move it closer or move the model." if solved.clamped else "Release to apply the pose. Escape cancels.")
				apply_frame();refresh_values();return
			var delta := drag_axis * amount
			if selected=="@root" and active_rig().root.get_parent() is Node3D:
				delta=active_rig().root.get_parent().global_basis.inverse()*delta
			elif selected != "@root":
				var rig = active_rig()
				var parent: String = rig.parent_id(selected)
				var parent_basis: Basis = rig.bones[selected].skeleton.global_basis if parent == "@root" else rig.bone_transform(parent).basis
				delta = parent_basis.inverse() * delta
			position += delta
		var affects_contacts: bool=not contacts.affected(active_rig()).is_empty()
		var last_valid: Dictionary=active_rig().data.duplicate(true) if affects_contacts else active_rig().data
		if not drag_feet.is_empty() or not drag_joints.is_empty():active_rig().data=drag_before.duplicate(true)
		set_delta(position, rotation.normalized())
		if not drag_joints.is_empty():
			var solved:=Joints.solve(active_rig(),drag_joints,active_rig().data.pose)
			if solved.has("error"):active_rig().data=drag_before.duplicate(true);apply_frame();refresh_values();app.message(solved.error);return
			active_rig().data.pose=solved.pose
			var limited:=false
			for chain in solved.chains:limited=limited or float(chain.residual)>.001
			app.message("A joint target is outside reach. Release to keep this pose, or Escape to cancel." if limited else "Joint pose preview. Release to apply; Escape cancels.")
		apply_frame()
		var contact_error: String=contacts.reach_error(active_rig(),app.frame,true) if affects_contacts else ""
		if not contact_error.is_empty():
			active_rig().data=last_valid;apply_frame();app.message(contact_error+" Move less, or release the feet here.")
		elif affects_contacts:app.message("Planted feet held. Release to apply; Escape cancels.")
		if not drag_feet.is_empty():
			var error:=FootHold.solve(active_rig(),drag_feet,apply_frame)
			if not error.is_empty():active_rig().data=last_valid;apply_frame();app.message(error)
		refresh_values()

func ring_vector(point: Vector2) -> Vector3:
	var camera: Camera3D=app.renderer.camera
	var direction:=camera.project_ray_normal(point)
	if absf(direction.dot(drag_axis))<0.08:return Vector3.ZERO
	var intersection=Plane(drag_axis.normalized(),drag_world.origin).intersects_ray(camera.project_ray_origin(point),direction)
	if intersection==null:return Vector3.ZERO
	var radial: Vector3=intersection-drag_world.origin
	return radial.normalized() if radial.length_squared()>0.00000001 else Vector3.ZERO

func ring_angle(point: Vector2) -> float:
	if drag_ring_start!=Vector3.ZERO:
		var radial:=ring_vector(point)
		if radial==Vector3.ZERO:return drag_ring_angle
		var principal:=atan2(drag_axis.dot(drag_ring_start.cross(radial)),drag_ring_start.dot(radial))
		drag_ring_angle+=wrapf(principal-drag_ring_previous,-PI,PI)
		drag_ring_previous=principal
		return drag_ring_angle
	return (point-drag_start).dot(drag_screen_axis.normalized())/drag_pixels

func finish_drag(cancel := false) -> void:
	if contacts and contacts.viewport and contacts.viewport.dragging:contacts.viewport.finish(cancel);return
	if cancel and contacts and contacts.viewport and contacts.viewport.active:contacts.viewport.stop();return
	if not dragging: return
	dragging = false
	if cancel:
		restore_state(drag_before, false)
		app.message("Pose edit cancelled. Previous pose restored.")
	else: commit(drag_before, true)
	drag_chain={}
	drag_joints={}
	drag_feet={}

func contact_live_edit_error() -> String:
	var rig=active_rig()
	if rig and not contacts.affected(rig).is_empty() and contacts.live_busy():return "Turn Physics and Hair & clothes off before editing a planted model or its parent."
	return ""

func contact_edit_error() -> String:
	var error:=contact_live_edit_error()
	if not error.is_empty():return error
	var rig=active_rig()
	if not rig or not Model.is_contact(rig.data):return ""
	var segment: Dictionary=Model.contact_animation().Contacts.active(rig.data.animation_clips,app.frame)
	for foot in segment.get("feet",[]):
		if selected in foot.ids:return "Release the feet in Planted feet before moving this leg. Plant them again to set new foot positions."
	return ""
