extends SceneTree
# Real-app harness shared by the private jobs. No test replaces wind/physics code.
const Model=preload("res://src/model.gd")
const Timeline=preload("res://src/timeline.gd")
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
const Groups=preload("res://src/wind_review_groups.gd")
const Definition=preload("res://src/secondary_rig.gd")
const Airflow=preload("res://src/airflow.gd")
const Fixture=preload("res://tests/secondary_fixture.gd")
var app
var folder: String
var request: Dictionary={}
var checks:=0
var failures:=0
var metrics: Dictionary={}

func _initialize() -> void:
	create_timer(300).timeout.connect(func():push_error("Private wind review GPU watchdog");quit(2))
	call_deferred("run")

func run() -> void:pass

func setup_request() -> void:
	request=JSON.parse_string(FileAccess.get_file_as_string(OS.get_cmdline_user_args()[0]))
	folder=request.folder
	root.size=Vector2i(1800,1100)

func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1

func settled(count:=5) -> void:
	for i in range(count):await process_frame
	await RenderingServer.frame_post_draw

func wait_job(job) -> void:
	while job.pid>0:await process_frame
	await settled()

func fresh_app(label: String) -> void:
	app=load("res://main.tscn").instantiate()
	app.recovery_root=folder.path_join(label+"-recovery");app.recent_path=folder.path_join(label+"-recent.json");app.display_prefs_path=folder.path_join(label+"-display.cfg")
	root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false
	app.has_project.cache_root=folder.path_join(label+"-cache");app.workspace_layout.path=folder.path_join(label+"-layout.json")
	app.mode.select(2);app.change_mode(2);app.scene_view.set_setup(true,false)

func source_path() -> String:
	if not str(request.get("source","")).is_empty():return request.source
	var asset:=folder.path_join("original-hair-skirt.glb")
	if not FileAccess.file_exists(asset):check(Fixture.create(asset)==OK,"create an owned skinned hair/skirt fixture")
	return asset

func box_asset(path: String) -> Error:
	var node:=Node3D.new();node.name="WindReviewPeerBox"
	var instance:=MeshInstance3D.new();var mesh:=BoxMesh.new();mesh.size=Vector3(.35,.35,.35);instance.mesh=mesh
	var material:=StandardMaterial3D.new();material.albedo_color=Color("679fe1");instance.material_override=material;node.add_child(instance);instance.owner=node
	var document:=GLTFDocument.new();var state:=GLTFState.new();var result:=document.append_from_scene(node,state)
	if result==OK:result=document.write_to_filesystem(state,path)
	node.free();return result

func add_source(path: String,recorded_exclusion:=false) -> RefCounted:
	var data:=Model.definition(path)
	data.position[1]=float(request.get("raise_y",0.))
	if not str(request.get("parameters","")).is_empty():data.metadata.native_parameters=JSON.parse_string(FileAccess.get_file_as_string(request.parameters))
	check(app.append_object(data,"model").is_empty(),"ordinary world adoption loads the declared source")
	var actor: RefCounted=app.renderer.active_model()
	if actor==null:return null
	var declared: Dictionary=actor.root.get_meta("has_secondary_rig",{})
	check(declared.get("error","").is_empty() and not declared.get("chains",[]).is_empty(),"source has usable declared secondary chains")
	if recorded_exclusion and declared.get("chains",[]).size()>1:
		var id: String=declared.chains[1].joints[0].binding.id
		var a:=Model.identity();var b:=Model.identity();var qa:=Quaternion(Vector3.FORWARD,.22);var qb:=Quaternion(Vector3.FORWARD,-.31)
		a.rotation_xyzw=[qa.x,qa.y,qa.z,qa.w];b.rotation_xyzw=[qb.x,qb.y,qb.z,qb.w]
		actor.data.pose_keys=[{"frame":0,"pose":{id:a},"transform":Model.Clips.transform(actor.data),"interpolation":"linear"},{"frame":24,"pose":{id:b},"transform":Model.Clips.transform(actor.data),"interpolation":"linear"}];actor.data.draft_frame=-1
		app.set_frame(12)
	app.world_selection.select_entity(actor.data.id,false);app.mode.select(2);app.change_mode(2);app.pose_editor.frame_model()
	var camera: Camera3D=app.renderer.camera
	app.keys=[Timeline.key(0,camera.position,camera.quaternion,camera.fov)]
	# Stabilize the fixture through the authored key sampler before exact view
	# comparisons; look_at's basis need not equal its quaternion reconstruction.
	app.renderer.evaluate(app.keys,app.frame);app.pose_editor.apply_frame();await settled()
	return actor

func add_media() -> void:
	Drawing.insert(app.layers[1],0,int(app.video.duration_frames),Drawing.blank(1920,1080))
	Drawing.edit_image(Drawing.cel_at(app.layers[1],app.frame)).image.fill_rect(Rect2i(70,70,32,24),Color.CYAN)
	if not str(request.get("audio","")).is_empty():app.import_audio(request.audio)
	app.changed();await settled()

func document_state() -> Dictionary:
	var paint: Array=[]
	for layer in app.layers:
		var cels: Array=[]
		for cel in layer.cels:cels.append({"id":cel.id,"start":cel.start,"duration":cel.duration,"pixels":Storage.image_hash(Drawing.image(cel))})
		paint.append({"id":layer.id,"visible":layer.visible,"cels":cels})
	return {"world":World.portable(app.current_world()),"keys":app.keys.duplicate(true),"video":app.video.duplicate(true),"paint":paint,"audio":app.audio_document().duplicate(true),"palette":app.palette.duplicate(true),"history":app.history.size(),"redo":app.redo_history.size(),"dirty":app.dirty}

func document_matches(before: Dictionary,dirty:=true) -> bool:
	var after:=document_state();var wanted:=before.duplicate(true)
	if not dirty:after.erase("dirty");wanted.erase("dirty")
	return after==wanted

func open_review() -> bool:
	var review=app.local_wind_review
	check(review.available(),"real local-wind control is available for this model")
	review.button.pressed.emit();await settled()
	var ok: bool=is_instance_valid(review.window) and review.window.visible and not review.catalog.get("groups",[]).is_empty()
	check(ok,"real review window lists declared motion groups")
	if not ok:return false
	var source: RefCounted=app.renderer.active_model();var before: Dictionary=source.data.duplicate(true)
	review.parts.select(0);review.parts.item_selected.emit(0)
	check(review.wind_ids.is_empty(),"focusing a real list row does not check it")
	review.wind_check.button_pressed=true
	var first: String=review.catalog.groups[0].id
	if review.catalog.groups.size()>1:
		review.parts.select(1);review.parts.item_selected.emit(1)
		check(review.wind_ids.has(first) and review.wind_ids.size()==1 and not review.wind_check.button_pressed,"focusing another row preserves the first check and its separate focus")
		review.wind_check.button_pressed=true;check(review.wind_ids.size()==2,"multiple actual window checks coexist")
		review.wind_check.button_pressed=false
		review.parts.select(0);review.parts.item_selected.emit(0)
	check(source.data==before,"window checks and focus leave source model data unchanged")
	return true

func begin_review(running:=true) -> bool:
	var review=app.local_wind_review
	review.master.button_pressed=true
	check(review.phase=="warming" and review.candidate!=null,"actual Try a local blow creates one warming candidate")
	if review.candidate==null:return false
	var source: RefCounted=app.renderer.active_model()
	check(review.candidate!=source and review.candidate.root.get_parent()==app.renderer.world and not app.renderer.world_runtime.instances.has(review.candidate.data.id),"candidate appears in the existing world without entering the authored model registry")
	check(review.hidden.keys().all(func(mesh):return not mesh.visible),"only the original owned meshes are hidden while the candidate is shown")
	check(review.simulation.primary==null and review.private_space.find_world_3d().space!=source.root.get_world_3d().space,"temporary solver has no borrowed primary and owns a separate physics space")
	if running:
		await settled()
		check(review.phase=="running","owned native-frame warm-up reaches running")
		return review.phase=="running"
	return review.phase=="warming"

func selected_ids() -> Array:
	var result: Array=[]
	for group in app.local_wind_review.catalog.groups:
		if app.local_wind_review.wind_ids.has(group.id):result.append_array(group.rotating_ids)
	return result

func angle(a: Dictionary,b: Dictionary,ids: Array) -> float:
	var maximum:=0.
	for id in ids:maximum=maxf(maximum,Timeline.quaternion(a.get(id,Model.identity()).rotation_xyzw).angle_to(Timeline.quaternion(b.get(id,Model.identity()).rotation_xyzw)))
	return maximum

func native_image(final:=false,layers:=true) -> Image:
	return await app.renderer.capture(app.keys,app.layers if layers else [],app.frame,final)

func changed_bytes(a: Image,b: Image) -> int:
	if a==null or b==null or a.get_size()!=b.get_size():return -1
	var aa:=a.get_data();var bb:=b.get_data();var count:=0
	for i in range(aa.size()):
		if aa[i]!=bb[i]:count+=1
	return count

func main_picture(name: String) -> void:
	root.get_texture().get_image().save_png(folder.path_join(name+"-main.png"))
	if is_instance_valid(app.local_wind_review.window):app.local_wind_review.window.get_texture().get_image().save_png(folder.path_join(name+"-window.png"))

func finish(label: String,extra: Dictionary={}) -> void:
	if is_instance_valid(app):app.free();await settled()
	var result:={"checks":checks,"failures":failures,"metrics":metrics,"mode":request.get("mode",label)};result.merge(extra)
	FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result,"",true,true))
	print(label+" "+JSON.stringify({"checks":checks,"failures":failures,"mode":request.get("mode",label)}));quit(0 if failures==0 else 1)
