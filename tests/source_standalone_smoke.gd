extends SceneTree
const Timeline=preload("res://src/timeline.gd")
const Storage=preload("res://src/storage.gd")
var app
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(210).timeout.connect(func():push_error("Standalone Source watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settle() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func jobs() -> void:
	while app.has_project.pid>0:await process_frame
	await settle()
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0]
	var plans: Array=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("plans.json")))
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.display_prefs_path=folder.path_join("prefs.cfg");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("reader-cache" if "--read" in args else "writer-cache")
	if "--physics" in args:
		for plan in plans:
			app.new_project();app.load_demo_room();await settle()
			var definition: Dictionary=app.pose_editor.definition(plan.glb);definition.data.position=[0,3,0];app.append_object(definition.data,"model");await settle()
			var rig=app.renderer.active_model();var id: String=rig.data.id;var metadata: Dictionary=rig.data.metadata.duplicate(true);var keys: Array=rig.authored_keys();var history: int=app.history.size()
			app.physics_editor.toggle.button_pressed=true;await settle()
			check(app.physics_editor.active(id),plan.name+" compatible native rig starts actual HAS physics")
			if not app.physics_editor.active(id):continue
			var simulation=app.physics_editor.simulations[id];var start_y:=0.0
			for body in simulation.bodies.values():start_y+=body.global_position.y
			start_y/=simulation.bodies.size()
			for i in range(300):await physics_frame
			var end_y:=0.0;var finite:=true;var low:=INF
			for body in simulation.bodies.values():end_y+=body.global_position.y;finite=finite and body.global_position.is_finite();low=minf(low,body.global_position.y)
			end_y/=simulation.bodies.size()
			check(simulation.bodies.size()>=3 and finite and end_y<start_y-0.2 and low>-0.05,plan.name+" native bodies fall onto real map collision with finite positions")
			app.physics_editor.toggle.button_pressed=false;await settle();rig=app.renderer.world_runtime.instance(id)
			check(not app.physics_editor.active(id) and not rig.data.pose.is_empty() and rig.authored_keys()==keys,plan.name+" Physics off freezes native pose without authoring an animation take")
			check(rig.data.metadata==metadata and app.history.size()==history+1,plan.name+" freeze preserves native provenance and is one undoable edit")
		var result:={"checks":checks,"failures":failures,"mode":"physics"};FileAccess.open(folder.path_join("physics.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("STANDALONE_SOURCE "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1);return
	var observations:=[]
	for plan in plans:
		var packed:=folder.path_join(plan.name+".has")
		if "--read" in args:
			app.has_project.open_file(packed);await jobs()
			for object in app.current_world().objects:
				if object.kind=="model":app.world_selection.select_entity(object.id);break
			await settle()
			var rig=app.renderer.active_model();var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join(plan.name+"-expected.json")))
			check(rig!=null and rig.order.size()==int(expected.bones),"cold packed "+plan.name+" restores native rig without conversion bundle")
			if rig==null:continue
			check(rig.authored_keys().any(func(key):return not key.pose.is_empty()) and rig.data.metadata.native_parameters.source_profile=="standalone","cold packed "+plan.name+" retains authored pose and standalone provenance")
			var image: Image=await app.renderer.capture(app.keys,[],0,true)
			check(Storage.image_hash(image)==expected.pixels,"cold packed "+plan.name+" matches posed preview pixels exactly")
			continue
		app.new_project();await settle()
		check(app.pose_editor.add_model(plan.glb).is_empty(),"native converted "+plan.name+" imports through ordinary Add model")
		await settle();var rig=app.renderer.active_model()
		check(rig!=null and rig.order.size()==int(plan.bones),plan.name+" retains all converted native bones")
		if rig==null:continue
		check(not app.physics_editor.is_running(),"direct prepared setup leaves "+plan.name+" ready for manual pose inspection")
		app.pose_editor.frame_model();await settle()
		app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,app.renderer.camera.fov)]
		var before_image: Image=await app.renderer.capture(app.keys,[],0,true);before_image.save_png(folder.path_join(plan.name+"-rest.png"))
		var arm:=""
		for id in rig.order:
			if id.to_lower().ends_with("::bip_upperarm_l"):arm=id;break
		check(not arm.is_empty(),plan.name+" exposes its native left upper arm for posing")
		if arm.is_empty():continue
		var before: Dictionary=rig.data.duplicate(true);var history: int=app.history.size();var id: String=rig.data.id
		var editor=app.pose_editor;editor.selected=arm;editor.operation.select(0);editor.refresh_values();editor.fields[0].value=25;editor.apply_numeric();await settle();rig=app.renderer.world_runtime.instance(id)
		check(rig.data!=before and rig.authored_keys().size()>0 and app.history.size()==history+1,plan.name+" actual numeric pose authors one undoable native bone key")
		var posed: Dictionary=rig.data.duplicate(true)
		app.undo();await settle();rig=app.renderer.world_runtime.instance(id);check(rig.data==before,plan.name+" pose Undo restores exact native data")
		app.redo();await settle();rig=app.renderer.world_runtime.instance(id);check(rig.data==posed,plan.name+" pose Redo restores exact authored result")
		var image: Image=await app.renderer.capture(app.keys,[],0,true);image.save_png(folder.path_join(plan.name+"-posed.png"))
		check(image.get_data()!=before_image.get_data(),plan.name+" posed native geometry changes actual rendered pixels")
		app.get_viewport().get_texture().get_image().save_png(folder.path_join(plan.name+"-editor.png"))
		app.has_project.save_file(packed,"packed");await jobs();check(app.has_project.path==packed and not app.dirty,plan.name+" saves as an ordinary portable HAS")
		var expected:={"bones":rig.order.size(),"pixels":Storage.image_hash(image)};FileAccess.open(folder.path_join(plan.name+"-expected.json"),FileAccess.WRITE).store_string(JSON.stringify(expected))
		if plan.name=="Ran":
			app.video.duration_frames=24
			var why: String=await app.export_movie(folder);check(why.is_empty(),"standalone Ran exports a real posed movie")
			observations.append({"name":plan.name,"movie":app.last_export_folder.path_join("movie.mp4")})
	var result:={"checks":checks,"failures":failures,"observations":observations,"mode":"reader" if "--read" in args else "writer"};FileAccess.open(folder.path_join("reader.json" if "--read" in args else "writer.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("STANDALONE_SOURCE "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
