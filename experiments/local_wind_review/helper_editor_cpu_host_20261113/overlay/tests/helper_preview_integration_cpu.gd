extends SceneTree
const Model=preload("res://src/model.gd")
const Runtime=preload("res://src/wind_helper_runtime.gd")
const Bridge=preload("res://src/wind_helper_bridge.gd")
const Adapter=preload("res://src/wind_helper_candidate.gd")
var app
var helper
var host
var config: Dictionary={}
var checks: Array=[]
var failures: Array=[]
func _initialize() -> void:
	create_timer(110).timeout.connect(func():printerr("INTEGRATION watchdog");quit(2));call_deferred("run")
func need(value: bool,label: String) -> void:
	checks.append(label);print(("PASS " if value else "FAIL ")+label)
	if not value:failures.append(label)
func frames(count:=3) -> void:
	for i in count:await process_frame
func wait_review() -> void:
	var until:=Time.get_ticks_msec()+15000
	while is_instance_valid(helper.window) and helper.pid>0 and Time.get_ticks_msec()<until:await process_frame
	await frames()
func wait_prepared() -> void:
	var until:=Time.get_ticks_msec()+20000
	while host.active() and host.phase!="prepared_hidden" and Time.get_ticks_msec()<until:await process_frame
	await frames()
func state(actor: RefCounted) -> Dictionary:
	return {"data":actor.data.duplicate(true),"world":app.current_world().duplicate(true),"history":app.history.duplicate(true),"redo":app.redo_history.duplicate(true),"dirty":app.dirty,"revision":app.recovery_revision,"live":Adapter.live_state(actor)}
func peer_file(path: String) -> void:
	var node:=Node3D.new();var mesh:=MeshInstance3D.new();mesh.mesh=BoxMesh.new();node.add_child(mesh)
	var doc:=GLTFDocument.new();var data:=GLTFState.new();need(doc.append_from_scene(node,data)==OK and doc.write_to_filesystem(data,path)==OK,"unskinned peer fixture writes")
	node.free()
func open_review() -> void:
	helper.open();await wait_review()
	need(is_instance_valid(helper.window) and helper.preview_ready and helper.preview.get("can_apply",false),"real helper editor completes geometry review")
func start_hidden() -> void:
	helper.try_wind.button_pressed=true;await wait_prepared()
	need(host.phase=="prepared_hidden","real reviewed worker and imported transfer reach hidden host: "+host.last_error)
func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if args.size()!=1:quit(2);return
	config=JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	need(DisplayServer.get_name()=="headless" and ProjectSettings.globalize_path("res://").trim_suffix("/").replace("\\","/").to_lower()==str(config.code_root).replace("\\","/").to_lower(),"headless exact private source copy")
	app=load("res://main.tscn").instantiate();app.recovery_root=config.folder.path_join("recovery");app.recent_path=config.folder.path_join("recent.json");app.display_prefs_path=config.folder.path_join("display.cfg")
	app.helper_preview_runtime_path=config.python;app.helper_preview_work_root=config.folder.path_join("profile-work")
	root.size=Vector2i(1400,900);root.gui_embed_subwindows=true
	root.add_child(app);await frames();app.autosave_enabled.set_pressed_no_signal(false)
	need(OS.get_user_data_dir().replace("\\","/").ends_with(str(config.profile)),"actual Godot profile uses unique supplied custom directory name")
	app.has_project.cache_root=config.folder.path_join("project-cache");need(app.new_project(),"ordinary New creates empty world")
	need(app.append_object(Model.definition(config.source),"model").is_empty(),"ordinary Add imports source fixture")
	var target_id: String=app.renderer.active_model().data.id
	var path: String=config.folder.path_join("peer.glb");peer_file(path)
	need(app.append_object(Model.definition(path),"model").is_empty(),"ordinary Add imports independent peer")
	var peer_id: String=app.renderer.active_model().data.id
	var target: RefCounted=app.renderer.world_runtime.instance(target_id);var peer: RefCounted=app.renderer.world_runtime.instance(peer_id)
	app.world_selection.select_entity(target_id,false);app.mode.select(2);app.change_mode(2)
	var head: String=target.root.get_meta("has_source_bones")[2]
	var q:=Quaternion(Vector3.UP,.4);var a:=Model.identity();var b:=Model.identity();b.rotation_xyzw=[q.x,q.y,q.z,q.w];b.position=[.05,-.02,.03]
	target.data.pose_keys=[{"frame":0,"interpolation":"linear","pose":{head:a},"transform":Model.Clips.transform(target.data)},{"frame":24,"interpolation":"linear","pose":{head:b},"transform":Model.Clips.transform(target.data)}];target.data.draft_frame=0
	target.data.position=[.5,.2,-.3];target.data.scale=1.2
	target.data.metadata["source_shape"]={"format":"studio_source_shape_2","enabled":false,"overrides":{"3":{"0":.5}}}
	target.data=Model.ShapeAnimation.promote(target.data)
	target.data.shape_base={"3":{"0":0.}};target.data.shape_pose={"3":{"0":0.}};target.data.shape_starts={"3":{"0":0}}
	target.data=Model.ShapeAnimation.put_key(target.data,{"frame":0,"interpolation":"linear","shapes":{"3":{"0":.25}}},48)
	target.data=Model.ShapeAnimation.put_key(target.data,{"frame":24,"interpolation":"linear","shapes":{"3":{"0":.75}}},48)
	need(Model.validate(target.data,48).is_empty() and target.authored_keys().size()==2,"recorded body and expression fixture is valid with original body keys")
	app.set_frame(12);app.pose_editor.apply_frame();await frames()
	need(target.sample(12,false)[head].rotation_xyzw!=Model.identity().rotation_xyzw and target.sample_shapes(12,false)["3"]["0"]==.5,"paused frame really evaluates nonzero recorded pose and expression")
	helper=app.physics_editor.helper_editor;host=helper.pending_preview
	var precision:=Bridge.new();var number:=0.12345678901234567;var label:=String.chr(39080)+String.chr(0x1f300);var encoded: String=precision.ascii_json({"value":number,"text":label});var decoded=JSON.parse_string(encoded)
	need(decoded.value==number and decoded.text==label and encoded.to_utf8_buffer().size()==encoded.length(),"submission preserves reviewed double precision and ASCII Unicode transport")
	precision.free()
	need(Runtime.resolve_hint(config.python,"").get("path")==config.python,"explicit approved runtime resolves")
	need(Runtime.resolve_hint(config.folder.path_join("changed-python.exe"),str(config.python).get_base_dir()).has("error"),"changed explicit runtime refuses without PATH fallback")
	need(str(Runtime.resolve_hint("python",str(config.python).get_base_dir()).get("path","")).replace("\\","/").to_lower()==str(config.python).replace("\\","/").to_lower(),"bare hint resolves literal PATH to approved absolute runtime")
	need(Runtime.resolve_hint("python",config.folder).has("error") and Runtime.resolve_hint("powershell",str(config.python).get_base_dir()).has("error"),"unsupported and missing bare hints refuse")
	app.physics_editor.enable_body(peer);await physics_frame;await frames()
	need(app.physics_editor.active(peer_id),"independent peer body really starts")
	var peer_sim=app.physics_editor.simulations.get(peer_id);var peer_bodies: Dictionary=peer_sim.bodies;var peer_data: Dictionary=peer.data.duplicate(true)
	var before:=state(target);var visibility: Dictionary={}
	var managed_before:=DirAccess.get_files_at(ProjectSettings.globalize_path("res://output/imports"))
	for mesh in target.root.find_children("*","MeshInstance3D",true,false):visibility[mesh]=mesh.visible
	await open_review()
	need(state(target)==before,"opening review never freezes peer or authors target")
	need(app.physics_editor.simulations.get(peer_id)==peer_sim and peer_sim.running and peer_sim.bodies==peer_bodies and peer.data==peer_data,"opening preserves exact peer solver/body ownership and authored data")
	var epoch: int=app.local_wind_generation;await start_hidden()
	if host.phase=="prepared_hidden":
		need(app.local_wind_active() and app.local_wind_generation==epoch+1,"pending hidden interval gates recovery and advances capture epoch")
		need(host.candidate!=null and not host.holder.visible and host.holder.get_parent()==host.hidden_space and host.hidden_space.get_parent()==host and host.hidden_space.own_world_3d and host.hidden_space.render_target_update_mode==SubViewport.UPDATE_DISABLED,"candidate is attached only to owned hidden host")
		need(host.last_receipt.setup_members_built==1 and host.last_receipt.purpose=="preview_only","focused reviewed submission is preview-only")
		need(host.last_transport.releases==1 and host.last_transport.result==OK,"completed worker/controller exact map ownership released once")
		need(state(target)==before,"actual helper build/import/pose transfer preserves all authored/live target state")
		need(DirAccess.get_files_at(ProjectSettings.globalize_path("res://output/imports"))==managed_before,"temporary helper preparation creates no managed imported asset")
		need(host.candidate.data.pose.size()>=target.order.size() and Adapter.shape_matches(host.candidate,host.frozen_shape),"candidate carries complete paused recorded pose and actual effective morph")
		need(visibility.keys().all(func(mesh):return is_instance_valid(mesh) and mesh.visible==visibility[mesh]),"hidden-only preparation never borrows source visibility")
		need(app.physics_editor.simulations.get(peer_id)==peer_sim and peer_sim.running and peer_sim.bodies==peer_bodies and peer.data==peer_data,"actual preparation keeps independent peer solver running unchanged")
	helper.try_wind.button_pressed=false;await frames()
	need(not host.active() and host.candidate==null and not app.local_wind_active(),"turning try-off disposes only hidden candidate")
	need(state(target)==before and app.physics_editor.simulations.get(peer_id)==peer_sim,"try-off preserves source/document and unrelated peer")
	# Checked batch uses real review state and the same CPU preparation channel.
	helper.include_toggle.button_pressed=true;await wait_review()
	need(helper.included.size()==1 and helper.included.values()[0].valid,"real checked part receives reviewed batch membership")
	await start_hidden()
	need(host.run_mode=="included-batch" and host.last_receipt.get("setup_members_built")==1,"checked draft uses explicit batch admission")
	helper.request.points_in_anchor[1][0]+=.001;helper.queue_changed()
	need(not host.active() and host.candidate==null,"draft edit synchronously invalidates pending generation")
	helper.launch("review");await wait_review();await start_hidden()
	app.physics_editor.change_hair(false)
	need(not host.active() and app.physics_editor.simulations.get(peer_id)==peer_sim,"target Hair-off synchronously stops pending setup without peer freeze")
	var history: int=app.history.size();helper.apply()
	need(helper.pid<0 and app.history.size()==history and app.physics_editor.simulations.get(peer_id)==peer_sim,"Apply conservatively refuses active peers before authoring build")
	helper.install({})
	need(helper.pid<0 and app.history.size()==history and app.physics_editor.simulations.get(peer_id)==peer_sim,"late install refuses peer before accessing candidate or whole-world restore")
	helper.close();await frames()
	need(not is_instance_valid(helper.window) and not host.active(),"closing actual editor cancels owned pending state")
	# Source target live motion refuses before open, without freezing it.
	# Synthetic pending-map lifecycle control; actual native hair waits a drawn frame.
	app.physics_editor.pending[target_id]=app.physics_editor.generation+1;helper.open()
	need(not is_instance_valid(helper.window) and app.physics_editor.pending.has(target_id),"synthetic pending target refuses editor without cancelling pending state")
	app.physics_editor.pending.erase(target_id)
	app.world_selection.select_entity(peer_id,false);helper.open()
	need(not is_instance_valid(helper.window) and app.physics_editor.simulations.get(peer_id)==peer_sim and peer_sim.running,"actual live prop selected as target refuses before any freeze")
	app.world_selection.select_entity(target_id,false)
	app.physics_editor.freeze(peer_id,false);app.pose_editor.apply_frame();await frames()
	await open_review();await start_hidden();app.set_frame(13)
	need(not host.active(),"seek synchronously invalidates prepared setup")
	var stale_error: String=host.start()
	need(not stale_error.is_empty() and not host.active() and host.bridge==null and is_instance_valid(helper.window),"seek to a changed expression refuses old reviewed shape draft before worker")
	await frames();helper.close();await open_review()
	helper.try_wind.button_pressed=true;helper.close();await frames(8)
	need(not host.active() and host.candidate==null,"close immediately during worker creation denies late candidate")
	await open_review();await start_hidden();var old_revision: int=app.recovery_revision;app.changed()
	need(not host.active() and app.recovery_revision==old_revision+1,"document edit synchronously invalidates hidden setup")
	helper.close();await frames();await open_review();await start_hidden()
	# Existing authoring action remains a separate one-Undo revision.
	helper.try_wind.button_pressed=false
	var original: Dictionary=target.data.duplicate(true);history=app.history.size();helper.apply();await wait_review()
	target=app.renderer.world_runtime.instance(target_id)
	need(not is_instance_valid(helper.window) and app.history.size()==history+1 and target.data.sha256!=original.sha256,"ordinary Apply still installs as exactly one Undo after motion stops")
	need(target.data.animation_clips==original.animation_clips and target.data.metadata.source_shape==original.metadata.source_shape,"ordinary Apply retains recorded pose keys and source-shape setting")
	app.undo();target=app.renderer.world_runtime.instance(target_id)
	need(target.data.sha256==original.sha256 and target.data.animation_clips==original.animation_clips,"ordinary Undo restores original asset and recorded pose")
	await frames();await open_review()
	# App destruction while admission is awaiting uses a WeakRef RefCounted request.
	helper.try_wind.button_pressed=false;helper.try_wind.button_pressed=true
	var until:=Time.get_ticks_msec()+20000
	while host.phase not in ["importing","prepared_hidden","stopped"] and Time.get_ticks_msec()<until:await process_frame
	need(host.phase in ["importing","prepared_hidden"],"final teardown reaches actual asynchronous admission")
	app.free();app=null;helper=null;host=null;await frames(8)
	need(root.get_child_count()==0,"late admission and app teardown release every owned hidden root")
	var file:=FileAccess.open(config.folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify({"checks":checks,"failures":failures,"headless":true,"gpu":false},"\t",true,true)+"\n");file.close()
	print("INTEGRATION "+JSON.stringify({"checks":checks.size(),"failures":failures.size()}));quit(0 if failures.is_empty() else 1)
