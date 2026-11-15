extends RefCounted
const Airflow=preload("res://src/airflow.gd")
const Model=preload("res://src/model.gd")
const Definition=preload("res://src/secondary_rig.gd")
const Secondary=preload("res://src/secondary_live.gd")
var app
var panel: HBoxContainer
var enabled: CheckButton
var speed: SpinBox
var aim: Button
var status: Label
var last_target_id:=""
func setup(parent: Node) -> void:
	app.icon_button(parent,"Add fan","fan",add_fan,"Add a movable fan. Its arrow points in the blowing direction; select it to change blowing speed.")
	panel=HBoxContainer.new();parent.add_child(panel)
	enabled=CheckButton.new();enabled.text="Fan on";panel.add_child(enabled);enabled.toggled.connect(func(value):edit("enabled",value))
	app.label(panel,"Blowing speed")
	speed=SpinBox.new();speed.min_value=0;speed.max_value=50;speed.step=0.5;speed.custom_minimum_size.x=82;panel.add_child(speed);speed.value_changed.connect(func(value):edit("speed",value))
	speed.tooltip_text="0 stops the airflow. Move and rotate this fan with the ordinary model handles. Speed is a relative air-strength control, not a calibrated real fan."
	aim=app.button(panel,"Aim at hair",aim_at_hair);aim.tooltip_text="Position and aim this fan at the last selected model's hair/clothing joints. Undo restores its previous placement."
	status=app.label(panel,"");status.add_theme_font_size_override("font_size",12);status.tooltip_text="Air reaches only joints in front of the arrow, within this fan's width and range. Raising speed does not make missed joints receive air."
func sync() -> void:
	var actor: RefCounted=app.renderer.active_model()
	if actor and not Airflow.is_fan(actor.data):last_target_id=actor.data.id
	panel.visible=actor!=null and Airflow.is_fan(actor.data)
	if not panel.visible:return
	var settings: Dictionary=actor.data.metadata.airflow
	enabled.set_pressed_no_signal(settings.enabled);speed.set_value_no_signal(settings.speed)
	var recording=app.physics_editor.recording
	var locked: bool=app.exporting or recording.active and recording.targets.has(actor.data.id)
	enabled.disabled=locked;speed.editable=not locked
	aim.disabled=locked or app.physics_editor.active(actor.data.id);update_status()
func target_model() -> RefCounted:
	var runtime: RefCounted=app.renderer.world_runtime
	if not runtime:return null
	var candidates:=[]
	for id in runtime.order:
		var actor: RefCounted=runtime.instance(id);var definition: Dictionary=actor.root.get_meta("has_secondary_rig",{})
		if not Airflow.is_fan(actor.data) and actor.root.is_visible_in_tree() and definition.get("error","").is_empty() and not definition.get("chains",[]).is_empty():
			if id==last_target_id:return actor
			candidates.append(actor)
	return candidates[0] if candidates.size()==1 else null
func aimed_world(target: RefCounted,world_scale:=1.0) -> Dictionary:
	if not target:return {}
	var definition: Dictionary=target.root.get_meta("has_secondary_rig",{});var chains: Array=definition.get("chains",[])
	if not definition.get("error","").is_empty() or chains.is_empty():return {}
	var center:=Vector3.ZERO
	for chain in chains:center+=Definition.binding_transform(target,chain.joints[0].binding).origin
	center/=chains.size()
	var direction: Vector3=center-app.renderer.camera.global_position;direction.y=0
	if direction.length_squared()<.000001:direction=-app.renderer.camera.global_basis.z;direction.y=0
	if direction.length_squared()<.000001:direction=Vector3.FORWARD
	direction=direction.normalized();var basis:=Basis(Quaternion(Vector3.BACK,direction)).scaled(Vector3.ONE*world_scale)
	return {"transform":Transform3D(basis,center-direction*1.5*world_scale-Vector3.UP*.85*world_scale)}
func aim_at_hair() -> void:
	var fan: RefCounted=app.renderer.active_model()
	if not fan or not Airflow.is_fan(fan.data) or app.exporting or aim.disabled:return
	var target:=target_model();var desired:=aimed_world(target,fan.root.global_basis.get_scale().x)
	if desired.is_empty():app.message("Select a model with hair/clothing joints, then select this fan and choose Aim at hair.");return
	var parent: Transform3D=fan.root.get_parent().global_transform
	var local: Transform3D=parent.affine_inverse()*desired.transform*fan.base_root.affine_inverse()
	var before: Dictionary=fan.data.duplicate(true);app.pose_editor.selected="@root";app.pose_editor.set_delta(local.origin,local.basis.orthonormalized().get_rotation_quaternion());app.pose_editor.commit(before,true)
	update_status();app.message("Fan aimed at "+str(target.data.name)+". Hair & clothes must be on; Undo restores the fan placement.")
func update_status() -> void:
	if not is_instance_valid(status) or not panel.visible:return
	var fan: RefCounted=app.renderer.active_model()
	if not fan or not Airflow.is_fan(fan.data):return
	var settings: Dictionary=fan.data.metadata.airflow
	if not settings.enabled or settings.speed<=0:status.text="Airflow off";return
	var total:=0;var reached:=0
	for simulation in app.physics_editor.simulations.values():
		if not simulation is Secondary:continue
		for chain in simulation.runner.chains:
			total+=1;var point:=Definition.binding_transform(simulation.rig,chain.source.joints[0].binding).origin
			if Airflow.field(fan.root.global_transform,settings,point).length_squared()>.00000001:reached+=1
	status.text="Hair & clothes is off" if total==0 else "Air misses hair/clothes" if reached==0 else "Air reaches %d/%d chains"%[reached,total]
func edit(key: String,value) -> void:
	var actor: RefCounted=app.renderer.active_model()
	if not actor or app.exporting or not Airflow.is_fan(actor.data):return
	var recording=app.physics_editor.recording
	if recording.active and recording.targets.has(actor.data.id):sync();app.message("Stop recording before changing this fan's settings.");return
	if actor.data.metadata.airflow.get(key)==value:return
	var before: Dictionary=actor.data.duplicate(true);var after:=before.duplicate(true);after.metadata.airflow[key]=value
	if not Model.validate(after,int(app.video.duration_frames)).is_empty():sync();return
	actor.data=after
	var command:={"type":"model","before":before,"after":after.duplicate(true)}
	if app.renderer.world_runtime:command.type="world_object";command["object_id"]=actor.data.id
	app.push_history(command);app.changed();app.message("Fan settings saved. Live motion needs Record to become animation.")
func add_fan() -> void:
	if app.exporting:return
	var target: RefCounted=app.renderer.active_model();var desired:=aimed_world(target)
	if target and not desired.is_empty():last_target_id=target.data.id
	var folder:=ProjectSettings.globalize_path("res://output/templates")
	if DirAccess.make_dir_recursive_absolute(folder)!=OK:app.message("Cannot create the fan asset folder.");return
	var path:=folder.path_join("fan_"+str(ResourceUID.create_id())+".glb")
	var error:=Airflow.create_asset(path)
	if error!=OK:app.message("Cannot create fan: "+error_string(error));return
	var data:=Model.definition(path);data.name="Fan";data.metadata["airflow"]=Airflow.defaults()
	var camera: Camera3D=app.renderer.camera;var position:=camera.global_position-camera.global_basis.z*2-Vector3.UP*0.8
	var q: Quaternion=(camera.global_basis.get_rotation_quaternion()*Quaternion(Vector3.UP,PI)).normalized()
	if not desired.is_empty():
		var parent: Transform3D=app.renderer.world_runtime.root.global_transform if app.renderer.world_runtime else app.renderer.world.global_transform
		var local: Transform3D=parent.affine_inverse()*desired.transform;position=local.origin;q=local.basis.get_rotation_quaternion()
	data.position=[position.x,position.y,position.z];data.rotation_xyzw=[q.x,q.y,q.z,q.w]
	var message: String=app.append_object(data,"model",0)
	if not message.is_empty():app.message(message)
