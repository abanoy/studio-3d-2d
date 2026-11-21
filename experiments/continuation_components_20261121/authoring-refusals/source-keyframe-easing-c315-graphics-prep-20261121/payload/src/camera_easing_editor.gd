extends Node
# Session-only camera recipe. Preview never changes keys or saved project metadata.
const Easing=preload("res://src/keyframe_easing.gd")
const Timeline=preload("res://src/timeline.gd")
var app
var panel: VBoxContainer
var details: VBoxContainer
var key_choice: OptionButton
var arrive: SpinBox
var leave: SpinBox
var note: Label
var context:={}
var controls: Array=[]
var plan:={}
var preview_enabled:=false
var last_error:=""

func setup(owner_app) -> void:
	app=owner_app
	panel=VBoxContainer.new();app.camera_section.add_child(panel)
	app.button(panel,"Camera timing / easing…",open)
	details=VBoxContainer.new();panel.add_child(details);details.hide()
	var introduction: Label=app.label(details,"Temporary camera timing. Arrive slows into this key; Leave slows away from it. The adjacent segment keeps its existing Linear / Ease shape. This does not add body anticipation or hair physics.")
	introduction.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	key_choice=OptionButton.new();details.add_child(key_choice);key_choice.item_selected.connect(select_key)
	arrive=app.spin(details,"Arrive (%)",0,100,0);arrive.step=1
	leave=app.spin(details,"Leave (%)",0,100,0);leave.step=1
	app.button(details,"Set timing on selected key",set_key_controls)
	app.button(details,"Preview / Recalculate smooth timing",preview)
	app.button(details,"Discard temporary preview",discard)
	app.button(details,"Bake preview into camera keys (one Undo)",bake_preview)
	note=app.label(details,"");note.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART

func editing_error() -> String:
	if app.exporting or app.playing or app.navigating:return "Stop playback/navigation and wait for export before editing camera timing."
	if app.has_dialog(app) or app.source_import.pid>0 or app.has_project.pid>0:return "Finish the open operation before editing camera timing."
	if app.mode.selected!=1:return "Choose Scene / camera before editing camera timing."
	if app.drawing or app.pose_editor.dragging or app.physics_editor.recording.active or app.physics_editor.is_running():return "Finish the current edit and switch live physics Off before editing camera timing."
	if app.camera_transform_editor and app.camera_transform_editor.has_draft():return "Apply or reload the numeric camera draft first."
	if app.sequence_editor and not app.sequence_editor.active_owner.is_empty():return "Camera easing currently works in the parent scene. Return to it before editing."
	return ""

func valid_context() -> bool:
	return not context.is_empty() and (not app.sequence_editor or app.sequence_editor.active_owner.is_empty()) and app.recovery_session==context.session and app.video==context.video and app.keys==context.keys and Easing.digest(app.keys)==context.source_sha256

func open() -> void:
	var error:=editing_error()
	if not error.is_empty():report(error);return
	if not valid_context():
		clear_preview();controls.clear()
		context={"session":app.recovery_session,"video":app.video.duplicate(true),"keys":app.keys.duplicate(true),"source_sha256":Easing.digest(app.keys)}
	if details:
		details.show();key_choice.clear()
		for key in app.keys:key_choice.add_item("Frame %d" % int(key.frame),int(key.frame))
		var selected:=0
		for index in range(app.keys.size()):
			if app.keys[index].frame==app.frame:selected=index;break
		key_choice.select(selected);select_key(selected)
	report("Temporary preview only. Save and movie export use authored keys until Bake. Discard leaves the project unchanged.")

func select_key(index: int) -> void:
	if not key_choice or index<0 or index>=key_choice.item_count:return
	var frame:=key_choice.get_item_id(index);var row:={"arrive":0.,"leave":0.}
	for value in controls:
		if value.frame==frame:row=value;break
	arrive.set_value_no_signal(float(row.arrive)*100.);leave.set_value_no_signal(float(row.leave)*100.)
	arrive.editable=index>0;leave.editable=index<key_choice.item_count-1

func set_key_controls() -> void:
	var error:=editing_error()
	if not error.is_empty():report(error);return
	if not valid_context():report("The authored scene changed. Open Camera timing again to start a fresh recipe.");return
	if not key_choice or key_choice.selected<0:return
	arrive.apply();leave.apply()
	var frame:=key_choice.get_item_id(key_choice.selected)
	set_controls_at(frame,float(arrive.value)/100.,float(leave.value)/100.)

# Also exposed as a small testable transaction; it never edits app.keys.
func set_controls_at(frame,arrival,departure) -> String:
	var error:=editing_error()
	if error.is_empty() and not valid_context():error="The authored scene changed. Open Camera timing again."
	if not error.is_empty():report(error);return error
	var upcoming: Array=controls.duplicate(true)
	for index in range(upcoming.size()-1,-1,-1):
		if upcoming[index].frame==frame:upcoming.remove_at(index)
	upcoming.append({"frame":frame,"arrive":arrival,"leave":departure})
	var checked:=Easing.compile(app.keys,upcoming,int(app.video.duration_frames))
	if checked.has("error"):report(checked.error);return checked.error
	var had_preview:=preview_enabled
	controls=upcoming;clear_preview()
	if had_preview:app.renderer.evaluate(app.keys,app.frame)
	report("Timing stored in this temporary recipe. Preview / Recalculate to inspect it.");return ""

func preview() -> String:
	var error:=editing_error()
	if error.is_empty() and not valid_context():error="The authored scene changed. Open Camera timing again."
	if not error.is_empty():report(error);return error
	var upcoming:=Easing.compile(app.keys,controls,int(app.video.duration_frames))
	if upcoming.has("error"):report(upcoming.error);return upcoming.error
	plan=upcoming;preview_enabled=not plan.segments.is_empty()
	app.renderer.evaluate(app.keys,app.frame)
	report("Temporary smooth timing preview. Scrub or play to inspect it. Bake adds at most 241 ordinary camera keys; Save / movie use authored keys until then." if preview_enabled else "No affected camera segments: the original interpolation is unchanged.")
	return ""

func preview_active() -> bool:
	if preview_enabled and not valid_context():clear_preview()
	return preview_enabled

# Installed once on Renderer; an empty result asks it to use untouched Timeline.sample.
func sample_preview(keys: Array,frame: int) -> Dictionary:
	if app.exporting or not preview_active() or keys!=context.keys:return {}
	var result:=Easing.sample(plan,frame)
	if result.has("error"):clear_preview();return {}
	return result

func clear_preview() -> void:
	preview_enabled=false;plan.clear()

func discard() -> void:
	var had_preview:=preview_enabled;var same:=valid_context()
	clear_preview();controls.clear();context.clear()
	if details:details.hide()
	if had_preview and same and not app.exporting and not app.navigating:app.renderer.evaluate(app.keys,app.frame)
	report("Temporary easing discarded. Authored camera keys and Undo history are unchanged.")

func bake_preview() -> String:
	var error:=editing_error()
	if error.is_empty() and (not valid_context() or not preview_active()):error="Preview a current camera timing recipe before baking."
	if not error.is_empty():report(error);return error
	var upcoming:=Easing.bake(plan)
	if upcoming.has("error"):report(upcoming.error);return upcoming.error
	if upcoming.added_keys==0:report("No in-between integer frames to bake. Authored keys are unchanged.");return ""
	var before: Array=app.keys.duplicate(true);var after: Array=upcoming.keys.duplicate(true)
	# No signal/await/edit callback separates the last baseline check and this replacement.
	if not valid_context():report("The authored scene changed before Bake.");return "The authored scene changed before Bake."
	clear_preview();controls.clear();context.clear()
	if details:details.hide()
	app.keys=after
	app.push_history({"type":"keys","camera_timing_bake":true,"before":before,"after":after.duplicate(true),"bytes":2*(var_to_bytes(before).size()+var_to_bytes(after).size())})
	app.changed();app.set_frame(app.frame)
	report("Baked %d ordinary camera keys in one Undo. Original keys were kept. Temporary easing is now Off." % upcoming.added_keys)
	return ""

func report(message: String) -> void:
	last_error=message
	if is_instance_valid(note):note.text=message
	if app:app.message(message)

func _process(_delta: float) -> void:
	if not context.is_empty() and not valid_context():
		clear_preview();controls.clear();context.clear()
		if details:details.hide()
