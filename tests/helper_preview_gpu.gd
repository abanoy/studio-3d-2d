extends "res://tests/helper_preview_gpu_common.gd"
const Adapter=preload("res://src/wind_helper_candidate.gd")
var helper
var host

func source_pose(source: RefCounted) -> Dictionary:
	var result:={}
	for id in source.order:
		var info: Dictionary=source.bones[id]
		result[id]=info.skeleton.get_bone_pose(info.index)
	return result

func wait_review() -> bool:
	var until:=Time.get_ticks_msec()+20000
	while is_instance_valid(helper.window) and (helper.pid>0 or not helper.preview_ready) and Time.get_ticks_msec()<until:await process_frame
	await settled()
	return is_instance_valid(helper.window) and helper.pid<=0 and helper.preview_ready and helper.preview.get("can_apply",false)

func open_pending() -> bool:
	helper=app.physics_editor.helper_editor;host=helper.pending_preview
	helper.open(true)
	var ready:=await wait_review()
	check(ready,"real helper window completes focused geometry review")
	return ready

func start_pending() -> bool:
	helper.try_wind.button_pressed=true
	var until:=Time.get_ticks_msec()+30000
	while host.phase not in ["running","stopped"] and Time.get_ticks_msec()<until:await process_frame
	await settled()
	var ready: bool=host.phase=="running" and is_instance_valid(host.player) and host.player.phase=="running"
	check(ready,"actual reviewed CPU worker, hidden binding admission and wind reach running: "+str(host.last_error))
	return ready

func prepare_case(label: String) -> RefCounted:
	if is_instance_valid(app):app.free();app=null;await settled()
	await fresh_app(label)
	app.helper_preview_runtime_path=request.python;app.helper_preview_work_root=folder.path_join(label+"-helper-work")
	if label=="endpoint-popup-escape":
		while app.helper_preview_work_root.length()<200:app.helper_preview_work_root=app.helper_preview_work_root.path_join("padding")
	check(OS.get_user_data_dir().replace("\\","/").ends_with(str(request.profile)),label+" uses the unique private preference profile")
	var source: RefCounted=await add_source(source_path())
	if source==null:return null
	var head: String=source.root.get_meta("has_source_bones",{}).get(2,"")
	if head.is_empty():check(false,"fixture Head has exact source-node binding");return null
	var a:=Model.identity();var b:=Model.identity();var q:=Quaternion(Vector3.UP,.3)
	b.rotation_xyzw=[q.x,q.y,q.z,q.w];b.position=[.04,-.01,.02]
	source.data.pose_keys=[{"frame":0,"pose":{head:a},"transform":Model.Clips.transform(source.data),"interpolation":"linear"},{"frame":24,"pose":{head:b},"transform":Model.Clips.transform(source.data),"interpolation":"linear"}];source.data.draft_frame=0
	source.data.metadata.source_shape={"format":"studio_source_shape_2","enabled":false,"overrides":{"3":{"0":.5}}}
	app.set_frame(12);app.changed();await settled()
	return source

func assert_restored(before: Dictionary,pose: Dictionary,source: RefCounted,meshes: Dictionary,label: String) -> void:
	check(document_matches(before),label+" leaves authored world, camera, drawings, sound, history and dirty state exact")
	check(source_pose(source)==pose,label+" restores original bone poses exactly")
	check(meshes.keys().all(func(mesh):return is_instance_valid(mesh) and mesh.visible==meshes[mesh]),label+" restores each original mesh visibility exactly")
	check(host.phase=="stopped" and host.candidate==null and not app.local_wind_active(),label+" has no admitted candidate or active try-out")
	check(not RenderingServer.frame_post_draw.is_connected(host.player.warm_frame),label+" removes its pending native-frame callback")
	if is_instance_valid(helper.window):check(app.canvas.review_pointer==Callable(helper,"patch_pointer"),label+" restores the original helper refinement pointer")
	else:check(app.canvas.review_chain.is_empty() and app.canvas.review_lines.is_empty(),label+" clears closed helper overlays")

func main_case() -> void:
	var source: RefCounted=await prepare_case("motion")
	if source==null:return
	await add_media()
	var before:=document_state();var pose:=source_pose(source);var original: Image=await native_image(false)
	var meshes:={}
	for mesh in owned_source_meshes(source):meshes[mesh]=mesh.visible
	if not await open_pending():return
	check(helper.window.size.y==mini(680,maxi(380,int(app.get_viewport_rect().size.y)-180)),"helper dialog uses the reviewed680default within current viewport bounds")
	check(not helper.wind_parts.visible and not helper.wind_check.visible and not helper.wind_options.visible,"unused wind controls leave room for ordinary part and joint refinement")
	var refinement_lines: PackedVector2Array=app.canvas.review_lines.duplicate();var refinement_chain: PackedVector2Array=app.canvas.review_chain.duplicate()
	check(not refinement_lines.is_empty() and not refinement_chain.is_empty(),"ordinary helper refinement displays orange surface and proposed-joint overlays before wind")
	if not await start_pending():return
	check(host.focused_group>=0 and host.wind_ids.has(host.catalog.groups[host.focused_group].id) and helper.wind_check.button_pressed,"initial wind focus is an actually checked candidate group")
	check(helper.wind_parts.visible and helper.wind_check.visible and helper.wind_options.visible,"prepared motion groups reveal their separate temporary wind controls")
	var player=host.player;var candidate: RefCounted=player.candidate;var candidate_root: WeakRef=weakref(candidate.root)
	check(candidate!=source and candidate.root.get_parent()==app.renderer.world and not app.renderer.world_runtime.instances.has(candidate.data.id),"temporary derived candidate displays in the real viewport without entering authored instances")
	check(mesh_id_set(player.hidden.keys())==mesh_id_set(meshes.keys()) and player.hidden.keys().all(func(mesh):return not mesh.visible),"exactly the independently inventoried source meshes are hidden")
	check(player.simulation.primary==null and player.private_space.find_world_3d().space!=source.root.get_world_3d().space,"pending helper owns an independent secondary solver and physics space")
	check(document_matches(before) and source_pose(source)==pose,"running wind leaves authored data and original poses exact")
	var initial: Dictionary=player.simulation.latest.duplicate(true)
	var initial_candidate: Image=await native_image(false)
	for i in 90:await physics_frame
	var moving: Array=[]
	for operation in host.last_receipt.operations:
		for index in operation.candidate_helper_nodes:
			var id: String=candidate.root.get_meta("has_source_bones",{}).get(int(index),"")
			if not id.is_empty():moving.append(id)
	var movement:=angle(initial,player.simulation.latest,moving)
	metrics["derived_helper_max_angle"]=movement
	check(not moving.is_empty() and movement>.001,"actual newly proposed weighted helpers move before Apply")
	var blowing: Image=await native_image(false)
	var pixels:=changed_bytes(initial_candidate,blowing);metrics["same_candidate_wind_changed_image_bytes"]=pixels
	metrics["original_vs_blowing_image_bytes"]=changed_bytes(original,blowing)
	check(pixels>100,"the same admitted candidate's native pixels change as its weighted helpers move")
	var included: Dictionary=helper.included.duplicate(true);var reviewed: Dictionary=helper.request.duplicate(true);var checked: Dictionary=host.wind_ids.duplicate()
	var focus: int=host.focused_group;var other: int=(focus+1)%host.catalog.groups.size()
	helper.wind_parts.select(other);helper.wind_parts.item_selected.emit(other)
	check(host.wind_ids==checked and helper.included==included and helper.request==reviewed,"focusing a wind row changes neither wind checks nor Apply membership")
	var unchecked: int=-1
	for index in host.catalog.groups.size():
		if not host.wind_ids.has(host.catalog.groups[index].id):unchecked=index;break
	check(unchecked>=0,"fixture retains a distinct unchecked motion group")
	if unchecked>=0:
		helper.wind_parts.select(unchecked);helper.wind_parts.item_selected.emit(unchecked)
		var id: String=host.catalog.groups[unchecked].id
		helper.wind_check.button_pressed=true;await settled()
		check(host.wind_ids.has(id) and host.wind_ids.size()>checked.size() and helper.included==included and helper.request==reviewed,"multiple temporary group checks are separate from the reviewed Apply setup")
		helper.wind_check.button_pressed=false;await settled()
	check(host.wind_ids==checked,"temporary check restoration preserves the same candidate-bound groups")
	app.pose_editor.update_gizmo()
	check(app.canvas.pose_lines.is_empty() and app.canvas.pose_joints.is_empty(),"pose redraw keeps original handles suppressed over the temporary candidate")
	var view: Dictionary=app.renderer.view_state();app.renderer.camera.position+=Vector3(.1,0,0);app.pose_editor.update_gizmo();await settled()
	check(host.phase=="running" and app.canvas.pose_lines.is_empty(),"camera navigation keeps pending wind active without original pose handles")
	app.renderer.restore_view(view);await settled()
	root.get_texture().get_image().save_png(folder.path_join("pending-helper-main.png"))
	helper.window.get_texture().get_image().save_png(folder.path_join("pending-helper-window.png"))
	helper.try_wind.button_pressed=false;await settled()
	assert_restored(before,pose,source,meshes,"master Off")
	check(app.canvas.review_lines==refinement_lines and app.canvas.review_chain==refinement_chain,"master Off restores the exact original orange surface and proposed-joint overlays")
	check(candidate_root.get_ref()==null or not candidate_root.get_ref().visible,"master Off hides or frees the exact candidate")
	check(changed_bytes(original,await native_image(false))==0,"master Off restores exact original native scene pixels")
	check(not app.canvas.pose_lines.is_empty(),"ordinary pose handles return after Stop")
	helper.close();await settled()
	app.free();app=null;await settled()

func endpoint_cases() -> void:
	for action in ["off","seek","save","final","close","source","record","popup-escape"]:
		var label: String="endpoint-"+action
		var source: RefCounted=await prepare_case(label)
		if source==null:return
		var before:=document_state();var pose:=source_pose(source);var original: Image=await native_image(true)
		var meshes:={}
		for mesh in owned_source_meshes(source):meshes[mesh]=mesh.visible
		if not await open_pending() or not await start_pending():return
		if action=="popup-escape":
			var launch: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(host.bridge.job.path_join("owned-launch.json")))
			check(host.bridge.job.length()>=260 and str(launch.get("cwd","")).replace("\\","/").simplify_path()==app.helper_preview_work_root.replace("\\","/").simplify_path() and launch.get("job_assigned")==true,"a real helper worker prepares the long private job from its checked shorter work folder")
		var candidate: WeakRef=weakref(host.player.candidate.root)
		match action:
			"off":helper.try_wind.button_pressed=false
			"seek":app.set_frame(app.frame+1)
			"save":app.has_project.save_file(folder.path_join(label+".has"),"packed")
			"final":
				var final: Image=await native_image(true)
				check(changed_bytes(final,original)==0,"real final capture cancels pending wind and renders exact authored pixels")
			"close":helper.window.close_requested.emit()
			"source":app.new_project()
			"record":check(not app.physics_editor.recording.start(),"ordinary no-physics Record refusal remains after stopping pending wind")
			"popup-escape":
				var escape:=InputEventKey.new();escape.keycode=KEY_ESCAPE;escape.pressed=true;helper.window.window_input.emit(escape)
		check(host.phase=="stopped" and host.candidate==null,label+" synchronously invalidates the preview")
		var node=candidate.get_ref()
		check(node==null or not node.visible,label+" hides the candidate before the normal operation continues")
		if action=="save":
			await wait_job(app.has_project)
			check(FileAccess.file_exists(folder.path_join(label+".has")),"ordinary packed save completes with pending wind stopped")
		await settled()
		if action in ["off","record","final","popup-escape"]:assert_restored(before,pose,source,meshes,label)
		elif action!="source":check(document_matches(before,false),label+" preserves authored document and history")
		else:check(app.current_world().objects.is_empty(),"New retains its intended empty authored world")
		if action=="popup-escape":
			for i in 30:await process_frame
			check(host.phase=="stopped" and host.candidate==null and not helper.try_wind.button_pressed,"popup Window-input API Escape keeps master unchecked and denies any late candidate resurrection")
			check(changed_bytes(original,await native_image(true))==0,"popup Window-input API Escape restores exact original authored native pixels")
		check(app.renderer.native_readbacks==0,label+" drains native readback scopes")
		app.free();app=null;await settled()

func building_cases() -> void:
	for spec in [{"stage":"startup","action":"off"},{"stage":"startup","action":"close"},{"stage":"startup","action":"seek"},{"stage":"startup","action":"save"},{"stage":"worker","action":"off"},{"stage":"worker","action":"close"},{"stage":"worker","action":"seek"},{"stage":"worker","action":"save"}]:
		var action: String=spec.action;var label: String=str(spec.stage)+"-"+action
		var source: RefCounted=await prepare_case(label)
		if source==null:return
		if not await open_pending():return
		var before:=document_state();var pose:=source_pose(source)
		helper.try_wind.button_pressed=true
		if spec.stage=="worker":
			var until:=Time.get_ticks_msec()+20000
			while host.phase in ["starting","building"] and (not is_instance_valid(host.bridge) or host.bridge.worker_owner.is_empty()) and Time.get_ticks_msec()<until:await process_frame
			check(host.phase=="building" and is_instance_valid(host.bridge) and not host.bridge.worker_owner.is_empty() and not str(host.bridge.job).is_empty(),label+" observes an actual owned helper worker before cancellation")
		else:check(host.active() and host.phase in ["starting","building","importing"],label+" observes actual asynchronous startup")
		match action:
			"off":helper.try_wind.button_pressed=false
			"close":helper.close()
			"seek":app.set_frame(app.frame+1)
			"save":app.has_project.save_file(folder.path_join(label+".has"),"packed")
		check(host.phase=="stopped" and host.candidate==null,label+" invalidates synchronously")
		if action=="save":await wait_job(app.has_project)
		for i in 30:await process_frame
		check(host.phase=="stopped" and host.candidate==null,label+" late completion cannot resurrect")
		check(document_matches(before,false),label+" preserves authored document and pose keys")
		if action=="seek":check(app.frame==13 and source_pose(source)!=pose,label+" keeps the intended new recorded-frame pose")
		else:check(source_pose(source)==pose,label+" preserves the unchanged paused pose")
		app.free();app=null;await settled()

func run() -> void:
	setup_request()
	await main_case()
	await endpoint_cases()
	await building_cases()
	await finish("PENDING_HELPER_GPU",{"prototype_only":false,"native_fidelity":false,"new_movies":false})
