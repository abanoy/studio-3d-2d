extends Node
const Transform=preload("res://src/drawing_transform.gd")
const Drawing=preload("res://src/drawing.gd")
var selection
var app
var launch: Button
var controls: VBoxContainer
var size: SpinBox
var angle: SpinBox
var independent: CheckButton
var width_scale: SpinBox
var height_scale: SpinBox
var detail: VBoxContainer
var scale_hint: Label
var keep_original: CheckButton
var preview_button: Button
var preview_row: HBoxContainer
var apply_button: Button
var thread: Thread
var request:={}
var pending:={}
var last_result:={}
var edited_text:={}
var work_frames:=0

func setup(owner_editor: Node) -> void:
	selection=owner_editor;app=selection.app
	launch=app.button(selection.panel,"Resize / rotate…",open);launch.focus_mode=Control.FOCUS_NONE
	controls=VBoxContainer.new();selection.panel.add_child(controls)
	size=app.spin(controls,"Size (%)",5,400,100);size.step=.1
	scale_hint=app.label(controls,"");scale_hint.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	angle=app.spin(controls,"Rotation (degrees)",-180,180,0);angle.step=.1;angle.tooltip_text="Positive turns clockwise in the drawing. Size/rotation are relative to the current selected pixels."
	var advanced:=VBoxContainer.new();controls.add_child(advanced);app.advanced(advanced)
	independent=CheckButton.new();independent.text="Separate width and height";advanced.add_child(independent)
	detail=VBoxContainer.new();advanced.add_child(detail);width_scale=app.spin(detail,"Width (%)",5,400,100);height_scale=app.spin(detail,"Height (%)",5,400,100);width_scale.step=.1;height_scale.step=.1
	keep_original=CheckButton.new();keep_original.text="Keep original pixels";advanced.add_child(keep_original)
	independent.toggled.connect(func(enabled):
		flush()
		if enabled:width_scale.value=size.value;height_scale.value=size.value
		invalidate();refresh())
	keep_original.toggled.connect(func(_value):invalidate())
	for spin in [size,angle,width_scale,height_scale]:
		spin.value_changed.connect(value_changed.bind(spin))
		spin.get_line_edit().text_changed.connect(text_changed.bind(spin))
	preview_button=app.button(controls,"Preview transform",start);preview_button.focus_mode=Control.FOCUS_NONE
	preview_row=HBoxContainer.new();controls.add_child(preview_row);apply_button=app.button(preview_row,"Apply transform",apply_pending);apply_button.focus_mode=Control.FOCUS_NONE
	var cancel_button: Button=app.button(preview_row,"Cancel",cancel_preview);cancel_button.focus_mode=Control.FOCUS_NONE
	controls.hide();preview_row.hide();refresh()

func busy() -> bool:return thread!=null and thread.is_started()
func active() -> bool:return not request.is_empty() or not pending.is_empty()
func settings() -> Dictionary:return {"size":float(size.value),"angle":float(angle.value),"independent":independent.button_pressed,"width":float(width_scale.value),"height":float(height_scale.value),"copy":keep_original.button_pressed}
func value_changed(_value: float,spin: SpinBox) -> void:
	# SpinBox refreshes display text later. A numeric update is already authored;
	# applying its old LineEdit text here would silently revert the new value.
	edited_text.erase(spin);invalidate()
func text_changed(_text: String,spin: SpinBox) -> void:
	edited_text[spin]=true;invalidate()
func flush() -> void:
	var edits:=edited_text.keys();edited_text.clear()
	for spin in edits:spin.apply()
func refresh() -> void:
	if not launch:return
	launch.disabled=not selection.selected.has_area() or not selection.gesture.is_empty() or not selection.available()
	preview_button.disabled=launch.disabled or busy();preview_button.text="Preparing transform…" if busy() else "Preview transform"
	apply_button.disabled=pending.is_empty() or busy()
	size.editable=not independent.button_pressed;detail.visible=independent.button_pressed
	scale_hint.text=("Width%s%% · Height%s%% (Advanced)"%[width_scale.value,height_scale.value] if independent.button_pressed else "")+("\nKeeping original pixels (Advanced)" if keep_original.button_pressed else "")
	scale_hint.visible=independent.button_pressed or keep_original.button_pressed

func open() -> void:
	if not selection.valid_context() or not selection.selected.has_area() or not selection.gesture.is_empty():return
	controls.show();refresh();reveal_next()

func reveal_next() -> void:
	if not get_tree().process_frame.is_connected(reveal):get_tree().process_frame.connect(reveal,CONNECT_ONE_SHOT)
func reveal() -> void:
	if controls.is_visible_in_tree():app.inspector_scroll.ensure_control_visible(preview_row if not pending.is_empty() else preview_button)

func invalidate() -> void:
	request={};pending={}
	if preview_row:preview_row.hide()
	if is_instance_valid(app.canvas):app.canvas.selection_preview=null;selection.outline(selection.selected)

func cancel() -> void:
	invalidate()
	if controls:controls.hide()

func cancel_preview() -> void:
	invalidate();app.message("Transform canceled. Drawing unchanged; preparation is finishing in the background." if busy() else "Transform canceled. Drawing unchanged.")

func valid() -> bool:
	return not request.is_empty() and selection.valid_context() and selection.selected==request.rect and settings()==request.settings and selection.gesture.is_empty()

func start() -> void:
	if busy():app.message("The previous transform is finishing. You can keep editing; its old result will be discarded.");return
	flush()
	if not selection.valid_context() or not selection.selected.has_area() or not selection.gesture.is_empty():return
	invalidate();request={"rect":selection.selected,"settings":settings()}
	var values: Dictionary=request.settings
	var sx: float=(values.width if values.independent else values.size)/100.0;var sy: float=(values.height if values.independent else values.size)/100.0
	var image: Image=selection.context.image;thread=Thread.new();work_frames=0
	var error:=thread.start(Transform.calculate.bind(image.get_data(),image.get_width(),image.get_height(),request.rect,sx,sy,float(values.angle),bool(values.copy)),Thread.PRIORITY_LOW)
	if error!=OK:thread=null;request={};app.message("Cannot prepare drawing transform; pixels preserved.")
	else:preview_row.show();reveal_next();app.message("Preparing drawing transform. Review it before Apply; editing cancels stale work.")
	refresh()

func _process(_delta: float) -> void:
	refresh()
	if not request.is_empty() and not valid():invalidate()
	if not busy():return
	if thread.is_alive():work_frames+=1;return
	var result: Dictionary=thread.wait_to_finish();thread=null;last_result=result.duplicate();last_result.erase("data");last_result["ui_frames"]=work_frames
	if not valid():request={};return
	if result.has("error"):app.message(result.error);invalidate();return
	pending=result
	var candidate: Array=app.layers.duplicate(true);var cel:=Drawing.cel_at(candidate[app.active_layer],app.frame);cel.image=Image.create_from_data(app.video.width,app.video.height,false,Image.FORMAT_RGBA8,result.data)
	app.canvas.selection_preview=ImageTexture.create_from_image(Drawing.composite(candidate,app.frame,app.video.width,app.video.height));selection.outline(result.selection);preview_row.show();reveal_next()
	app.message("Transform preview. Repositioned to stay inside the frame; Apply or Cancel." if result.repositioned else "Transform preview. Apply or Cancel; original cel is unchanged.")

func apply_pending() -> void:
	if pending.is_empty():return
	flush()
	if not valid():invalidate();app.message("Transform changed. Preview the new settings before Apply.");return
	var result:=pending.duplicate();result.image=Image.create_from_data(app.video.width,app.video.height,false,Image.FORMAT_RGBA8,result.data);result.erase("data")
	# The shared commit path retains Image identity, tile Undo and live physics.
	request={};pending={};controls.hide();preview_row.hide()
	selection.commit_result(result,"Transformed selected drawing pixels. Undo restores the cel.")
	if not result.changed:app.message("Transform leaves drawing pixels unchanged.")

func _exit_tree() -> void:
	if get_tree().process_frame.is_connected(reveal):get_tree().process_frame.disconnect(reveal)
	if busy():thread.wait_to_finish();thread=null
