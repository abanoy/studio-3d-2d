extends SceneTree
const Joints=preload("res://src/joint_constraints.gd")
const T=preload("res://src/timeline.gd")
const Drawing=preload("res://src/drawing.gd")
var app
var checks:=0
func _initialize() -> void:
	create_timer(150).timeout.connect(func():quit(2));call_deferred("run")
func check(ok: bool,message: String) -> void:
	assert(ok,message);checks+=1;print("PASS ",message)
func settle() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func job() -> void:
	while app.has_project.pid>0:await process_frame
	await settle()
func bone(rig,name: String) -> String:
	for id in rig.order:
		if rig.bones[id].name==name:return id
	return ""
func reach(rig,effector: String,controller: String) -> float:
	return rig.bone_transform(effector).origin.distance_to(rig.bone_transform(controller).origin)
func begin_drag(editor) -> Vector2:
	editor.update_gizmo();check(editor.handles.size()==3,"all three controller move handles are available")
	var h: Dictionary=editor.handles[1];var start: Vector2=h.points[0].lerp(h.points[-1],.7)
	var press:=InputEventMouseButton.new();press.button_index=MOUSE_BUTTON_LEFT;press.pressed=true;editor.input(press,start)
	check(editor.dragging and not editor.drag_joints.is_empty(),"actual Y handle starts declared joint authoring")
	return start
func move(editor,start: Vector2,amount: float) -> void:
	editor.input(InputEventMouseMotion.new(),start+editor.drag_screen_axis.normalized()*amount/editor.drag_units*editor.drag_pixels)
func release(editor,start: Vector2) -> void:
	var up:=InputEventMouseButton.new();up.button_index=MOUSE_BUTTON_LEFT;up.pressed=false;editor.input(up,start)
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0]
	var cases: Array=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("cases.json")))
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	var reports: Array=[]
	for config in cases:
		app.new_project();check(app.pose_editor.add_model(config.source).is_empty(),"prepared standard model loads")
		app.physics_editor.freeze_all();var rig: RefCounted=app.renderer.active_model();var editor=app.pose_editor
		var controller:=bone(rig,config.controller);var effector:=bone(rig,config.effector)
		app.mode.select(2);app.change_mode(2);editor.record_key();editor.frame_model();app.keys=[T.from_camera(0,app.renderer.camera,"linear")];app.set_frame(12)
		editor.tree_items[controller].select(0);editor.selected=controller;editor.operation.select(1);editor.space.select(1);editor.refresh_values();await settle()
		var before: Dictionary=rig.data.duplicate(true);var camera: Array=app.keys.duplicate(true);var history: int=app.history.size();var baseline: Dictionary=rig.sample(12,true).duplicate(true)
		var lengths:={}
		for id in rig.order:
			if rig.parent_id(id)!="@root":lengths[id]=rig.bone_transform(id).origin.distance_to(rig.bone_transform(rig.parent_id(id)).origin)
		var amount:=.08 if config.controller=="左足ＩＫ" else .04
		var start:=begin_drag(editor);move(editor,start,amount);await settle()
		check(app.history.size()==history and rig.authored_keys().size()==1,"motion previews without authored keys or Undo noise")
		check(reach(rig,effector,controller)<.001,"dragged effector reaches its controller within one millimetre")
		check(editor.drag_axis.dot(Vector3.UP)>.999,"clicked handle is world Y")
		move(editor,start,0);check(rig.data==before,"returning to gesture origin restores exact starting data")
		move(editor,start,amount);var escape:=InputEventKey.new();escape.keycode=KEY_ESCAPE;escape.pressed=true;app._input(escape);await settle()
		check(rig.data==before and app.history.size()==history,"cancel restores the exact pose and key list")
		start=begin_drag(editor);move(editor,start,amount);release(editor,start);await settle()
		check(app.history.size()==history+1 and rig.authored_keys().size()==2,"release creates one auto-key edit and one Undo step")
		check(rig.authored_keys()[-1].authored_channels.size()>=3,"controller and coupled joints are authored together")
		check(reach(rig,effector,controller)<.001,"keyed FK endpoint retains the solved target")
		for id in lengths:check(absf(rig.bone_transform(id).origin.distance_to(rig.bone_transform(rig.parent_id(id)).origin)-lengths[id])<.00001,"joint length preserved: "+rig.bones[id].name)
		var affected:={controller:true}
		for chain in Joints.plan(rig,controller).chains:
			for link in chain.links:affected[link.id]=true
		var after: Dictionary=rig.sample(12,true)
		for id in baseline:
			if not affected.has(id):check(after.get(id)==baseline[id],"unrelated FK preserved: "+rig.bones[id].name)
		check(app.keys==camera,"posing leaves explicit camera keys intact")
		var solved: Dictionary=rig.data.duplicate(true);app.undo();check(rig.data==before,"Undo restores complete actor");app.redo();check(rig.data==solved,"Redo restores the saved FK solve")
		editor.operation.select(1);editor.refresh_values();var count: int=app.history.size();editor.apply_numeric();check(rig.data==solved and app.history.size()==count,"numeric no-op does not run a fresh solve")
		editor.fields[1].value+=.01;editor.apply_numeric();await settle()
		check(reach(rig,effector,controller)<.001 and app.history.size()==count+1,"numeric controller edit also solves and keys its joints")
		app.undo();check(rig.data==solved,"numeric edit undoes as one transaction")
		editor.reset_selected();await settle();check(reach(rig,effector,controller)<.001 and app.history.size()==count+1,"resetting a joint controller also solves its linked joints")
		app.undo();check(rig.data==solved,"controller reset undoes as one pose edit")
		editor.limb_ik.button_pressed=false;editor.refresh_values();editor.fields[1].value+=.01;editor.apply_numeric();await settle()
		check(reach(rig,effector,controller)>.005,"natural movement opt-out allows direct FK controller edits")
		app.undo();check(rig.data==solved,"direct controller edit undoes exactly");editor.limb_ik.button_pressed=true
		var retained: Dictionary=rig.root.get_meta(Joints.META).duplicate(true);var invalid: Dictionary=retained.duplicate(true);invalid.chains[0].iterations=10000;rig.root.set_meta(Joints.META,invalid)
		editor.refresh_values();editor.fields[1].value+=.01;editor.apply_numeric();check(rig.data==solved and app.history.size()==count,"invalid declaration refuses an edit without data changes");rig.root.set_meta(Joints.META,retained)
		var skipped: Dictionary=retained.duplicate(true);skipped.chains=[];skipped.skipped=[{"name":config.controller,"reason":"Native inherited movement is unsupported."}];rig.root.set_meta(Joints.META,skipped)
		editor.refresh_values();editor.fields[1].value+=.01;editor.apply_numeric();check(rig.data==solved and "unsupported" in app.status.text,"known unsupported native controller is disclosed without partial posing");rig.root.set_meta(Joints.META,retained)
		var skeleton: Skeleton3D=rig.bones[controller].skeleton;var original_scale:=skeleton.scale;skeleton.scale=Vector3(1.1,1,1)
		editor.refresh_values();editor.fields[1].value+=.01;editor.apply_numeric();check(rig.data==solved and "uniform" in app.status.text,"nonuniform skeleton scale refuses solving atomically");skeleton.scale=original_scale;editor.apply_frame()
		if label_for(config)=="miku":
			editor.contacts.open();editor.contacts.end_frame.value=24;editor.contacts.apply_range(true);await settle()
			check(rig.data!=solved and not editor.joint_plan().get("error","").is_empty(),"planted foot range owns the same leg joints")
			var planted: Dictionary=rig.data.duplicate(true);var planted_history: int=app.history.size();editor.refresh_values();editor.fields[1].value+=.01;editor.apply_numeric()
			check(rig.data==planted and app.history.size()==planted_history and "Release planted feet" in app.status.text,"controller edit cannot fight an active planted-foot range")
			app.undo();check(rig.data==solved,"Undo planting restores the authored joint pose")
		app.message("Joint posing check complete. Editable poses and camera keys retained.")
		Drawing.insert(app.layers[1],0,48,Drawing.blank(1920,1080));Drawing.edit_image(Drawing.cel_at(app.layers[1],12)).image.set_pixel(80,80,Color.CYAN)
		var expected: Image=await app.renderer.capture(app.keys,app.layers,12,true);var label: String="miku" if config.controller=="左足ＩＫ" else "pmx";expected.save_png(folder.path_join(label+"-pose.png"));root.get_texture().get_image().save_png(folder.path_join(label+"-editor.png"))
		var path:=folder.path_join(label+"-authoring.has");var actor_id: String=rig.data.id;app.has_project.save_file(path,"packed");await job();check(app.has_project.path==path,"solved editable pose saves to packed HAS")
		app.new_project();app.has_project.open_file(path);await job();rig=app.renderer.world_runtime.instance(actor_id)
		check(rig!=null and not Joints.plan(rig,controller).is_empty(),"packed reopen retains exact joint bindings")
		check(reach(rig,effector,controller)<.001,"packed reopen preserves FK target reach")
		check((await app.renderer.capture(app.keys,app.layers,12,true)).get_data()==expected.get_data(),"packed reopen preserves exact composite pixels")
		check(await app.export_movie(folder)=="","normal movie export succeeds")
		check(Image.load_from_file(app.last_export_folder.path_join("frame_000013.png")).get_data()==expected.get_data(),"ordinary export frame matches preview exactly")
		reports.append({"label":label,"reach":reach(rig,effector,controller),"movie":app.last_export_folder.path_join("movie.mp4"),"project":path})
	var result:={"cases":reports,"checks":checks};FileAccess.open(folder.path_join("authoring-result.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("JOINT_AUTHORING_SMOKE ",JSON.stringify(result));app.free();quit(0)
func label_for(config: Dictionary) -> String:
	return "miku" if config.controller=="左足ＩＫ" else "pmx"
