extends Node
const Measure=preload("res://src/character_height.gd")
const Renderer=preload("res://src/renderer.gd")
const ImportBasis=preload("res://src/import_basis.gd")
var app
var pending:=false
var window: Window
var fit: CheckBox
var reference: CheckBox
var target: SpinBox
var accept: Button
var info: Label
var advanced_info: Label
var scratch: Node
var data:={}
var context:={}
var assessment:={}
var at_frame:=0
var revision:=-1
var world_id:=0
var prepared:=false
var generation:=0
var raw_import_root:=Transform3D.IDENTITY
var reference_error:=""

func decimal(value: float) -> String:return JSON.stringify(value,"",true,true)

func current_world_id() -> int:return app.renderer.world_runtime.get_instance_id() if app.renderer.world_runtime else 0
func valid() -> bool:
	return pending and is_instance_valid(window) and revision==app.recovery_revision and world_id==current_world_id() and not app.exporting and not app.playing and not app.home.visible and app.has_project.pid<=0

func start(definition: Dictionary,start_frame: int,placement: Dictionary) -> String:
	if pending:return "Finish the pending height review first."
	if definition.has("asset_basis"):return "This model already has a human reference. Its scale remains editable after import."
	if start_frame<0 or start_frame>=app.video.duration_frames:return "Import frame is outside this project."
	data=definition.duplicate(true);context=placement.duplicate(true);context.erase("review_height");at_frame=start_frame;revision=app.recovery_revision;world_id=current_world_id();pending=true;assessment={};prepared=false
	window=Window.new();window.title="Review character height";window.theme=app.theme;window.transient=true;window.close_requested.connect(cancel);app.add_child(window)
	var panel:=PanelContainer.new();window.add_child(panel);panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var column:=VBoxContainer.new();panel.add_child(column)
	var scroll:=ScrollContainer.new();scroll.size_flags_vertical=Control.SIZE_EXPAND_FILL;scroll.horizontal_scroll_mode=ScrollContainer.SCROLL_MODE_DISABLED;column.add_child(scroll)
	var body:=VBoxContainer.new();body.size_flags_horizontal=Control.SIZE_EXPAND_FILL;scroll.add_child(body)
	info=app.label(body,"Measuring a disposable neutral model…");info.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	fit=CheckBox.new();fit.text="Fit visible character height";fit.disabled=true;body.add_child(fit)
	fit.toggled.connect(func(enabled):
		if not enabled and is_instance_valid(reference):reference.set_pressed_no_signal(false)
		refresh_reference_choice())
	reference=CheckBox.new();reference.text="Six-foot reference — Scale 1";reference.disabled=true;body.add_child(reference)
	reference.tooltip_text="Keep the original asset intact and make Scale 1 use a six-foot visible neutral reference. Scale 0.5 or 2 then means half or twice that reference."
	reference.toggled.connect(func(_value):refresh_reference_choice())
	target=app.spin(body,"Target metres (6 ft = 1.8288)",.1,10,Measure.SIX_FEET);target.step=.0001;target.value=Measure.SIX_FEET;target.editable=false
	app.label(body,"Uniform scale preserves proportions. Maps need a separate reference.\nLeave the box unchecked to keep the original size.").autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	advanced_info=app.label(body,"");advanced_info.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;advanced_info.visible=app.advanced_mode
	var line:=HBoxContainer.new();column.add_child(line);accept=app.button(line,"Add model",apply);accept.disabled=true;app.button(line,"Cancel import",cancel)
	generation+=1
	window.popup_centered(Vector2i(530,mini(430,maxi(320,int(app.get_viewport_rect().size.y)-150))));call_deferred("prepare",generation)
	return ""

func prepare(token: int) -> void:
	if token!=generation:return
	if not valid():cancel();return
	if FileAccess.get_sha256(data.source)!=data.sha256:info.text="The source changed. Cancel and import it again.";prepared=true;return
	scratch=Renderer.new();add_child(scratch);scratch.setup(320,240);scratch.viewport.render_target_update_mode=SubViewport.UPDATE_DISABLED
	var candidate: Dictionary=scratch.prepare_model(data)
	if candidate.has("error"):info.text=candidate.error;release_scratch();prepared=true;return
	scratch.install_model(candidate);scratch.model.apply(0,false,true,{"lighting_mode":"unshaded"})
	raw_import_root=scratch.model.base_root
	assessment=Measure.query(scratch.model);release_scratch()
	prepared=true
	info.text=assessment.error if not assessment.error.is_empty() else assessment.reason
	if assessment.height>0:info.text="Visible neutral height: "+String.num(assessment.height,5)+" scene units.\n"+info.text
	fit.disabled=not assessment.complete or not assessment.error.is_empty();fit.button_pressed=assessment.suggest_fit and not fit.disabled;target.editable=not fit.disabled
	reference_error=""
	if not fit.disabled:
		var proposed:=reference_candidate(data)
		if proposed.has("error"):reference_error=proposed.error
		else:
			var configured:=ImportBasis.configure_import_root(raw_import_root,proposed.data,true,true)
			if configured.has("error"):reference_error=configured.error
	reference.disabled=fit.disabled or not reference_error.is_empty()
	reference.tooltip_text="Keep the original asset intact. Scale 1 uses a six-foot visible neutral reference; hair, hats and shoes are included." if reference_error.is_empty() else "Six-foot reference unavailable: "+reference_error+" Ordinary height fitting is still available."
	refresh_reference_choice()
	advanced_info.text="Leg/extent ratio: "+String.num(assessment.leg_ratio,4)+"\nSkin coverage (head, left leg, right leg): "+str(assessment.coverage)+"\nOriginal root scale: "+str(data.scale)+"\nSource: "+str(data.sha256)
	accept.disabled=false

func refresh_reference_choice() -> void:
	if not is_instance_valid(target) or not is_instance_valid(reference):return
	if reference.button_pressed and not reference.disabled:fit.button_pressed=true;target.value=Measure.SIX_FEET
	target.editable=not fit.disabled and not reference.button_pressed

func reference_candidate(original: Dictionary) -> Dictionary:
	var original_scale: float=float(original.get("scale",0.))
	if not is_finite(original_scale) or original_scale<=0:return {"error":"The imported model has no positive reference scale."}
	var raw_height: float=float(assessment.get("height",0.))/original_scale
	if not is_finite(raw_height) or raw_height<=0:return {"error":"The visible neutral reference could not be measured."}
	var created:=ImportBasis.create_record(str(original.sha256),decimal(raw_height),"explicit_complete_human_override")
	if created.has("error"):return created
	var result:=original.duplicate(true)
	result["asset_basis"]=created.record
	result.scale=1.0
	return {"data":result}

func apply() -> void:
	if not valid():cancel();return
	if accept.disabled:return
	if FileAccess.get_sha256(data.source)!=data.sha256:info.text="The source changed. Cancel and import it again.";return
	var candidate:=data.duplicate(true)
	if fit.button_pressed:
		if not assessment.get("complete",false) or not assessment.get("error","").is_empty():return
		if reference.button_pressed:
			if reference.disabled:info.text="This model cannot use the six-foot reference. Keep its original size or use ordinary fitting.";return
			var chosen:=reference_candidate(data)
			if chosen.has("error"):info.text=chosen.error;return
			candidate=chosen.data
			var configured:=ImportBasis.configure_import_root(raw_import_root,candidate,true,true)
			if configured.has("error"):info.text=configured.error;return
		else:
			var scale: float=float(candidate.scale)*target.value/float(assessment.height)
			if not Renderer.Model.scale_valid(scale):info.text="The resulting scale is outside Studio's supported range.";return
			candidate.scale=(Vector3.ONE*scale).x
		# Model transforms use float32. Preserve diagnostic decimals as text so
		# repeated JSON parses do not rewrite the original measurement record.
		candidate.metadata["import_height"]={"format":"studio_import_height_1","source_sha256":data.sha256,"measured_visible_height":decimal(assessment.height),"target_metres":decimal(target.value),"original_root_scale":decimal(data.scale),"factor":decimal(target.value/float(assessment.height)),"axis":assessment.axis.map(func(value):return decimal(value)),"leg_ratio":decimal(assessment.leg_ratio),"coverage":assessment.coverage.map(func(value):return decimal(value)),"root_scale_float32_hex":PackedFloat32Array([candidate.scale]).to_byte_array().hex_encode(),"note":"Measurements stored as exact decimal text. Visible neutral extent, not certified anatomical stature; explicit import choice."}
	var placement:=context.duplicate(true);close()
	var error: String=app.append_object(candidate,"model",at_frame,placement)
	if not error.is_empty():app.message(error)

func release_scratch() -> void:
	if is_instance_valid(scratch):scratch.camera.current=false;scratch.viewport.world_3d=null;scratch.viewport.render_target_update_mode=SubViewport.UPDATE_DISABLED;scratch.queue_free()
	scratch=null

func close() -> void:
	pending=false;generation+=1;release_scratch()
	if is_instance_valid(window):window.hide();window.queue_free()
	window=null

func cancel() -> void:
	close();app.message("Height review cancelled. No model was added.")

func _process(_delta: float) -> void:
	if pending and not valid():cancel()
	elif pending and is_instance_valid(advanced_info):advanced_info.visible=app.advanced_mode

func _exit_tree() -> void:
	release_scratch()
	if is_instance_valid(window):window.hide();window.queue_free()
