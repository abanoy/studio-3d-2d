extends SceneTree
const Support=preload("res://tests/world_test_support.gd")
const Drawing=preload("res://src/drawing.gd")
const Timeline=preload("res://src/timeline.gd")
const World=preload("res://src/world_document.gd")
var checks:=0
var failures:=0

func _initialize() -> void:
	create_timer(170).timeout.connect(func():push_error("Native import watchdog expired");quit(2))
	call_deferred("run")

func check(ok: bool,text: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+text)
	if not ok:failures+=1

func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw

func wait_job(job) -> void:
	while job.pid>0:await process_frame
	await settled()

func close_warnings(app) -> void:
	for child in app.get_children():
		if child is AcceptDialog and child.title=="Imported with limitations":child.hide();child.queue_free()

func arm_id(rig, wanted: String) -> String:
	for id in rig.order:
		if rig.bones[id].name==wanted:return id
	return ""

func run() -> void:
	var file_path:=ProjectSettings.globalize_path("res://output/native-import-request.json")
	if not FileAccess.file_exists(file_path):print("SKIP private native import request absent");quit(0);return
	var request: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(file_path))
	var folder:=ProjectSettings.globalize_path("res://output/native-import/run_%d" % Time.get_ticks_usec());DirAccess.make_dir_recursive_absolute(folder)
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	app.source_import.gmod_root=folder.path_join("no-gmod")
	app.pose_editor.import_dialog();await settled()
	var picker: FileDialog=null
	for child in app.get_children():
		if child is FileDialog and child.visible:picker=child;break
	check(picker!=null and "*.pmd" in picker.filters and "*.pmx" in picker.filters and "*.vrm" in picker.filters,"real model picker accepts PMD/PMX/VRM")
	var ids: Array[String]=[];var snapshots:={};var bundles: Array[String]=[];var bone_ids:={};var vrm0:="";var vrm1:=""
	for row in request.assets:
		app.set_frame(0)
		var previous: Dictionary=app.renderer.world_state().duplicate(true)
		if ids.is_empty() and picker:picker.file_selected.emit(row.path)
		elif row.actor:app.pose_editor.add_model(row.path)
		else:app.load_scene(row.path)
		check(app.source_import.pid>0 and app.source_import.progress.visible,"native file starts responsive local worker without external conversion UI: "+row.name)
		await wait_job(app.source_import);close_warnings(app);await settled()
		check(app.renderer.world_runtime.instances.size()==ids.size()+1,"native import appends one standard instance: "+row.name)
		if app.renderer.world_runtime.instances.size()!=ids.size()+1:print(app.status.text);app.free();quit(1);return
		var id: String=app.last_import_id;ids.append(id);bundles.append(app.source_import.folder)
		var rig: RefCounted=app.renderer.active_model()
		var report: Dictionary=rig.data.metadata.get("native_parameters",{})
		check(not report.is_empty() and report.source_sha256==row.sha256,"native source identity/parameters retained: "+row.name)
		for old in previous.objects:check(app.renderer.world_runtime.instance(old.id).data==old,"append keeps earlier instance data: "+old.name)
		check(FileAccess.get_sha256(row.path)==row.sha256,"native input bytes unchanged: "+row.name)
		if row.actor:
			var bone:=arm_id(rig,row.arm)
			check(not bone.is_empty(),"native arm remains selectable: "+row.name)
			if bone.is_empty():app.free();quit(1);return
			bone_ids[id]=bone
			app.pose_editor.frame_model();app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,app.renderer.camera.fov)]
			app.mode.select(0);app.change_mode(0)
			var before: Image=await app.renderer.capture(app.keys,app.layers,0,true)
			app.mode.select(2);app.change_mode(2);app.pose_editor.tree_items[bone].select(0);app.pose_editor.operation.select(0);app.pose_editor.refresh_values()
			app.pose_editor.fields[2].value=30;app.pose_editor.apply_numeric();app.set_frame(24);app.pose_editor.fields[2].value=65;app.pose_editor.apply_numeric()
			var posed: Image=await app.renderer.capture(app.keys,app.layers,24,true)
			check(before.get_data()!=posed.get_data() and rig.authored_keys().size()==2,"native skin deformation and auto-key at0/24: "+row.name)
			var state: Dictionary=rig.data.duplicate(true);app.undo();app.redo()
			check(rig.data==state,"native pose Undo/Redo restores same standard data: "+row.name)
			if row.name=="VRM0":vrm0=id
			if row.name=="VRM1":vrm1=id
			posed.save_png(folder.path_join(row.name+".png"))
		else:
			app.pose_editor.operation.select(1);app.pose_editor.refresh_values();app.pose_editor.fields[0].value=20;app.pose_editor.apply_numeric()
			check(rig.authored_keys().size()==1 and rig.sample_transform(0).position[0]==20,"native PMX map uses shared root transform and auto-key")
		app.pose_editor.set_flag("visible",false);snapshots[id]=rig.data.duplicate(true)
	check(app.renderer.world_runtime.instances.size()==request.assets.size(),"MMD model/map and both VRM versions coexist in one native HAS world")
	if not vrm0.is_empty() and not vrm1.is_empty():
		var one: Dictionary=app.renderer.world_runtime.instance(vrm1).data.metadata.native_parameters
		var zero: Dictionary=app.renderer.world_runtime.instance(vrm0).data.metadata.native_parameters
		check(one.humanoid.has("leftUpperArm") and zero.humanoid.has("leftUpperArm") and "rotated180" in zero.orientation,"VRM0/1 canonical humanoid metadata and explicit facing normalization retained")
	app.world_selection.select_entity(vrm0 if not vrm0.is_empty() else ids[0]);app.pose_editor.set_flag("visible",true);app.pose_editor.frame_model()
	app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,app.renderer.camera.fov)]
	app.mode.select(0);app.change_mode(0);app.set_frame(24);app.create_cel(false)
	Drawing.stroke(Drawing.cel_at(app.layers[1],24).image,Vector2(80,80),Vector2(200,80),5,Color.RED,false);app.changed()
	var preview: Image=await app.renderer.capture(app.keys,app.layers,24,true)
	var saved_world:=World.portable(app.renderer.world_state());var saved_transforms:={}
	var saved_keys: Array=app.keys.duplicate(true);var saved_video: Dictionary=app.video.duplicate(true)
	var saved_paint: PackedByteArray=Drawing.cel_at(app.layers[1],24).image.get_data()
	for object_id in app.renderer.world_runtime.order:
		var object: RefCounted=app.renderer.world_runtime.instance(object_id);saved_transforms[object_id]={"root":object.root.global_transform,"bones":{}}
		for part in object.order:saved_transforms[object_id].bones[part]=object.bone_transform(part)
	var saved:=folder.path_join("native.has");app.has_project.save_file(saved,"packed");await wait_job(app.has_project)
	check(app.has_project.path==saved and not app.dirty,"all direct native imports save as portable HAS with editable drawing and pose keys")
	app.new_project();app.has_project.open_file(saved);await wait_job(app.has_project)
	check(app.renderer.world_runtime.instances.size()==ids.size() and app.world_selection.selected.is_empty(),"normal HAS Open restores complete native scene without selection")
	var restored: Image=await app.renderer.capture(app.keys,app.layers,24,true)
	preview.save_png(folder.path_join("before-open.png"));restored.save_png(folder.path_join("after-open.png"))
	var old_pixels:=preview.get_data();var new_pixels:=restored.get_data();var changed_channels:=0;var byte_difference:=0;var locations:=[]
	for i in range(old_pixels.size()):
		if old_pixels[i]!=new_pixels[i]:
			changed_channels+=1;byte_difference+=absi(int(old_pixels[i])-int(new_pixels[i]))
			if locations.size()<30:locations.append([int(i/4)%1920,int(int(i/4)/1920),i%4,int(old_pixels[i]),int(new_pixels[i])])
	var exact_transforms:=true
	for object_id in app.renderer.world_runtime.order:
		var object: RefCounted=app.renderer.world_runtime.instance(object_id)
		exact_transforms=exact_transforms and object.root.global_transform==saved_transforms[object_id].root
		for part in object.order:exact_transforms=exact_transforms and object.bone_transform(part)==saved_transforms[object_id].bones[part]
	var exact_state: bool=World.portable(app.renderer.world_state())==JSON.parse_string(JSON.stringify(saved_world,"",true,true))
	var exact_media: bool=Drawing.cel_at(app.layers[1],24).image.get_data()==saved_paint and app.keys==JSON.parse_string(JSON.stringify(saved_keys,"",true,true)) and app.video==JSON.parse_string(JSON.stringify(saved_video,"",true,true))
	print("NATIVE_PACKED_DIAGNOSTIC "+JSON.stringify({"channels":changed_channels,"mean":float(byte_difference)/old_pixels.size(),"locations":locations,"transforms_exact":exact_transforms,"data_exact":exact_state,"media_exact":exact_media}))
	var packed_pixels:={"channels":changed_channels,"mean":float(byte_difference)/old_pixels.size()}
	check(exact_state and exact_transforms and exact_media and changed_channels<=384 and packed_pixels.mean<0.002,"native HAS reopen retains exact scene/transforms/media within established GLB rebuild bounds")
	var error: String=await app.export_movie(folder)
	check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000025.png")).get_data()==restored.get_data(),"native poses/camera/independent RGBA export exactly matches preview")
	# A corrupt native file must fail before replacing the complete current scene.
	var before_failure: Dictionary=app.renderer.world_state().duplicate(true)
	var bad:=folder.path_join("broken.vrm");var file:=FileAccess.open(bad,FileAccess.WRITE);file.store_string("not a VRM");file.close()
	app.pose_editor.add_model(bad);await wait_job(app.source_import)
	check(app.renderer.world_state()==before_failure and not app.status.text.is_empty(),"failed native import preserves all current instances and authored keys")
	app.pose_editor.add_model("C:/Users/noble/Desktop/model.vroid")
	check(app.source_import.pid<0 and "VRoid Studio" in app.status.text,"native VRoid project gets actionable VRM guidance instead of false import")
	app.pose_editor.add_model(request.assets[0].path)
	var worker_file: String=app.source_import.folder.path_join("worker.json")
	var deadline:=Time.get_ticks_msec()+15000
	while not FileAccess.file_exists(worker_file) and app.source_import.pid>0 and Time.get_ticks_msec()<deadline:await process_frame
	var owned_pid:=-1
	if FileAccess.file_exists(worker_file):
		var worker: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(worker_file));owned_pid=int(worker.get("blender_pid",-1))
	check(owned_pid>0,"MMD cancellation identifies its actual owned Blender process")
	app.source_import.cancel();await wait_job(app.source_import)
	var finished: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(worker_file))
	check(app.renderer.world_state()==before_failure and finished.get("blender_pid")==owned_pid and finished.get("cancelled_while_running",false) and finished.get("finished",false) and finished.get("exit_code",0)!=0,"cancelled MMD import preserves complete world and waits for its live converter to terminate")
	var result:={"checks":checks,"failures":failures,"folder":folder,"project":saved,"movie":app.last_export_folder.path_join("movie.mp4"),"bundles":bundles,"packed_pixels":packed_pixels}
	file=FileAccess.open("res://output/native-import-result.json",FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close()
	print("NATIVE_IMPORT "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
