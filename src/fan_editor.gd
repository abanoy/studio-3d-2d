extends RefCounted
const Airflow=preload("res://src/airflow.gd")
const Model=preload("res://src/model.gd")
var app
var panel: HBoxContainer
var enabled: CheckButton
var speed: SpinBox
func setup(parent: Node) -> void:
	app.icon_button(parent,"Add fan","fan",add_fan,"Add a movable fan. Its arrow points in the blowing direction; select it to change blowing speed.")
	panel=HBoxContainer.new();parent.add_child(panel)
	enabled=CheckButton.new();enabled.text="Fan on";panel.add_child(enabled);enabled.toggled.connect(func(value):edit("enabled",value))
	app.label(panel,"Blowing speed")
	speed=SpinBox.new();speed.min_value=0;speed.max_value=50;speed.step=0.5;speed.custom_minimum_size.x=82;panel.add_child(speed);speed.value_changed.connect(func(value):edit("speed",value))
	speed.tooltip_text="0 stops the airflow. Move and rotate this fan with the ordinary model handles. Speed is a relative air-strength control, not a calibrated real fan."
func sync() -> void:
	var actor: RefCounted=app.renderer.active_model();panel.visible=actor!=null and Airflow.is_fan(actor.data)
	if not panel.visible:return
	var settings: Dictionary=actor.data.metadata.airflow
	enabled.set_pressed_no_signal(settings.enabled);speed.set_value_no_signal(settings.speed)
	var recording=app.physics_editor.recording
	var locked: bool=app.exporting or recording.active and recording.targets.has(actor.data.id)
	enabled.disabled=locked;speed.editable=not locked
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
	var folder:=ProjectSettings.globalize_path("res://output/templates")
	if DirAccess.make_dir_recursive_absolute(folder)!=OK:app.message("Cannot create the fan asset folder.");return
	var path:=folder.path_join("fan_"+str(ResourceUID.create_id())+".glb")
	var error:=Airflow.create_asset(path)
	if error!=OK:app.message("Cannot create fan: "+error_string(error));return
	var data:=Model.definition(path);data.name="Fan";data.metadata["airflow"]=Airflow.defaults()
	var camera: Camera3D=app.renderer.camera;var position:=camera.global_position-camera.global_basis.z*2-Vector3.UP*0.8
	var q: Quaternion=(camera.global_basis.get_rotation_quaternion()*Quaternion(Vector3.UP,PI)).normalized()
	data.position=[position.x,position.y,position.z];data.rotation_xyzw=[q.x,q.y,q.z,q.w]
	var message: String=app.append_object(data,"model",0)
	if not message.is_empty():app.message(message)
