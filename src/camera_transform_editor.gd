extends Node
const MAX_POSITION:=1e12
const MAX_ANGLE:=36000.0
var app
var panel: VBoxContainer
var controls: VBoxContainer
var fields: Array[SpinBox]=[]
var edited_text:={}
var initial: Array=[]
var context:={}
var stale:=false
var hint: Label
var apply_button: Button
var launch: Button

func setup(owner_app: Control) -> void:
	app=owner_app
	panel=VBoxContainer.new();app.camera_section.add_child(app.advanced(panel));app.camera_section.move_child(panel,1)
	launch=app.button(panel,"Numeric camera view…",open);launch.focus_mode=Control.FOCUS_NONE
	controls=VBoxContainer.new();panel.add_child(controls);controls.hide()
	var introduction: Label=app.label(controls,"Position in scene units; angles in degrees (YXZ).");introduction.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	for name in ["Position X","Position Y","Position Z","Pitch X","Yaw Y","Roll Z"]:
		var position: bool=fields.size()<3
		var field: SpinBox=app.spin(controls,name,-MAX_POSITION if position else -MAX_ANGLE,MAX_POSITION if position else MAX_ANGLE,0);field.step=.001
		fields.append(field)
		field.get_line_edit().text_changed.connect(text_changed.bind(field))
		field.value_changed.connect(value_changed.bind(field))
	apply_button=app.button(controls,"Apply camera view",apply_view);apply_button.focus_mode=Control.FOCUS_NONE
	var reload_button: Button=app.button(controls,"Reload current view",reload_view);reload_button.focus_mode=Control.FOCUS_NONE
	hint=app.label(controls,"");hint.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART

func text_changed(_text: String,field: SpinBox) -> void:edited_text[field]=true
func value_changed(_value: float,field: SpinBox) -> void:edited_text.erase(field)

func available() -> bool:
	return app.mode.selected==1 and not app.exporting and not app.playing and not app.navigating and not app.has_dialog(app) and app.source_import.pid<=0 and app.has_project.pid<=0

func open() -> void:
	if not available():app.message("Choose Scene / camera and stop playback or navigation before editing the numeric view.");return
	controls.show();reload_view();call_deferred("reveal")

func reveal() -> void:
	await get_tree().process_frame
	await get_tree().process_frame
	if hint.is_visible_in_tree():app.inspector_scroll.ensure_control_visible(hint)

func reload_view() -> void:
	if not available():return
	context={"session":app.recovery_session,"frame":app.frame,"view":app.renderer.view_state().duplicate()}
	var camera: Camera3D=app.renderer.camera;var angles:=camera.basis.get_euler(EULER_ORDER_YXZ)*180./PI
	var numbers:=[camera.position.x,camera.position.y,camera.position.z,angles.x,angles.y,angles.z]
	edited_text.clear();initial.clear()
	for i in range(6):fields[i].set_value_no_signal(numbers[i]);initial.append(fields[i].value)
	stale=false;hint.text="Temporary view only. Apply, then Save camera key to keep it."

func valid_context() -> bool:
	return not context.is_empty() and context.session==app.recovery_session and context.frame==app.frame and context.view==app.renderer.view_state() and app.mode.selected==1

func has_draft() -> bool:
	if context.is_empty() or not controls.visible:return false
	if not edited_text.is_empty():return true
	for i in range(6):
		if fields[i].value!=initial[i]:return true
	return false

static func candidate(original: Transform3D,initial_values: Array,values: Array) -> Dictionary:
	if initial_values.size()!=6 or values.size()!=6:return {"error":"Camera view needs six numeric values."}
	for i in range(6):
		if not (values[i] is int or values[i] is float) or not is_finite(float(values[i])):return {"error":"Camera values must be finite numbers."}
		if absf(float(values[i]))>(MAX_POSITION if i<3 else MAX_ANGLE):return {"error":"Camera value exceeds the supported numeric range."}
	var result:=original;var angles:=original.basis.get_euler(EULER_ORDER_YXZ);var rotation_changed:=false
	for i in range(3):
		# Preserve untouched float32 components/basis exactly; displayed values round.
		if values[i]!=initial_values[i]:result.origin[i]=float(values[i])
		if values[i+3]!=initial_values[i+3]:angles[i]=deg_to_rad(float(values[i+3]));rotation_changed=true
	if rotation_changed:result.basis=Basis.from_euler(angles,EULER_ORDER_YXZ)
	return {"transform":result}

func apply_view() -> void:
	if not available():app.message("Stop playback/navigation and finish open operations before applying the camera view.");return
	if stale or not valid_context():stale=true;hint.text="The view or frame changed. Reload current view before applying.";return
	var edits:=edited_text.keys();edited_text.clear()
	for field in edits:field.apply()
	var values: Array=[]
	for field in fields:values.append(field.value)
	var result:=candidate(context.view.transform,initial,values)
	if result.has("error"):hint.text=result.error;return
	var changed: bool=result.transform!=app.renderer.camera.transform
	app.renderer.camera.transform=result.transform
	reload_view();app.refresh_camera_controls();app.canvas.queue_redraw()
	if changed:app.camera_preview_hint()
	else:hint.text="View is unchanged. Camera keys have not changed."

func _process(_delta: float) -> void:
	if not panel:return
	var can_edit:=available();launch.disabled=not can_edit
	if context.is_empty() or not controls.visible:return
	if context.session!=app.recovery_session:
		context.clear();edited_text.clear();initial.clear();stale=false;controls.hide();return
	if not valid_context():
		if has_draft():stale=true;hint.text="The view or frame changed. Reload current view to discard this old draft."
		elif can_edit:reload_view()
	apply_button.disabled=not can_edit or stale
	for field in fields:field.editable=can_edit and not stale
