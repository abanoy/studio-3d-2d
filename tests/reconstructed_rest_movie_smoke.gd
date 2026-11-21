extends SceneTree
const Model=preload("res://src/model.gd")
const Timeline=preload("res://src/timeline.gd")
const Storage=preload("res://src/storage.gd")
const Views=preload("res://src/reconstructed_rest_view.gd")
var app
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(130).timeout.connect(func():push_error("Rest movie watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settle() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func job() -> void:
	while app.has_project.pid>0:await process_frame
	await settle()
func pair_mesh(actor: RefCounted) -> MeshInstance3D:
	for value in actor.root.find_children("*","MeshInstance3D",true,false):
		if value.has_meta(Views.PAIR):return value
	return null
func mode(actor: RefCounted) -> String:
	var mesh:=pair_mesh(actor)
	if mesh==null:return "missing"
	var pair: Dictionary=mesh.get_meta(Views.PAIR)
	return "rest" if mesh.mesh==pair.rest else "flex" if mesh.mesh==pair.flex else "foreign"
func weighted_guide(actor: RefCounted) -> String:
	var mesh:=pair_mesh(actor);var pair: Dictionary=mesh.get_meta(Views.PAIR);var sk: Skeleton3D=mesh.get_node_or_null(mesh.skeleton);var names: Dictionary={};var totals: Dictionary={}
	for node in pair.guide_nodes:
		var id: String=actor.root.get_meta("has_source_bones",{}).get(int(node),"")
		if actor.bones.has(id):names[str(actor.bones[id].name)]=id
	for s in range(pair.flex.get_surface_count()):
		var arrays: Array=pair.flex.surface_get_arrays(s);var bones: PackedInt32Array=arrays[Mesh.ARRAY_BONES];var weights: PackedFloat32Array=arrays[Mesh.ARRAY_WEIGHTS]
		for i in range(bones.size()):
			var slot: int=bones[i];var name: String=mesh.skin.get_bind_name(slot)
			if name.is_empty():name=str(sk.get_bone_name(mesh.skin.get_bind_bone(slot)))
			if names.has(name) and weights[i]>0.:totals[names[name]]=float(totals.get(names[name],0.))+weights[i]
	var result:="";var maximum:=0.
	for id in totals:
		if totals[id]>maximum:maximum=totals[id];result=id
	return result
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0];var reader: bool="--read" in args
	root.size=Vector2i(1600,1000);app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	if reader:await read_project(folder,args[1],args[2]);return
	await write_project(folder,args[1],args[2])
func read_project(folder: String,project: String,expected_path: String) -> void:
	var expected: Dictionary=FileAccess.open(expected_path,FileAccess.READ).get_var();var project_sha:=FileAccess.get_sha256(project)
	app.has_project.open_file(project);await job()
	check(app.renderer.world_runtime.order.size()==1 and app.has_project.path==project,"fresh process opens packed reconstructed four-frame project")
	app.world_selection.select_entity(expected.id,false);var actor: RefCounted=app.renderer.active_model()
	check(actor!=null and actor.data.sha256==expected.sha and actor.data.source.replace("\\","/").begins_with(folder.path_join("cache").replace("\\","/")),"cold source is restored only into the reader's own cache")
	check(actor.data.pose_keys==expected.pose_keys and actor.data.pose==expected.pose and actor.bones.has(expected.head) and actor.bones.has(expected.guide),"native Head pose and all four guide keys survive portable storage exactly")
	check(pair_mesh(actor)!=null and actor.reconstruction_view_error.is_empty() and app.video.duration_frames==4 and app.video.fps_num==24 and app.video.fps_den==1,"cold import rebuilds both resource views with exact project timing")
	var hashes: Array=[]
	for frame in range(4):
		app.set_frame(frame);await settle();var image: Image=await app.renderer.capture(app.keys,app.layers,frame,true);var hash: String=Storage.image_hash(image);hashes.append(hash)
		check(image.get_size()==Vector2i(1920,1080) and hash==expected.hashes[frame] and mode(actor)==expected.modes[frame] and actor.bone_transform(expected.head)==expected.head_frames[frame] and actor.bone_transform(expected.guide)==expected.guide_frames[frame],"cold frame%d matches exact pixels resource and native Head/guide transforms"%frame)
	check(hashes[0]==hashes[3] and hashes[1]==hashes[2] and hashes[0]!=hashes[1],"cold captures retain visible guide FK and exact return to original rest")
	check(FileAccess.get_sha256(project)==project_sha and app.renderer.native_readbacks==0 and app.physics_editor.simulations.is_empty(),"cold read preserves packed file and leaves no borrowed simulation or readback")
	print("RECONSTRUCTED_REST_MOVIE_READ "+JSON.stringify({"checks":checks,"failures":failures,"user_profile":OS.get_user_data_dir(),"fresh_process":true,"frames":4,"source_arrays_published":false}));await app.quit_studio();quit(0 if failures==0 else 1)
func write_project(folder: String,source: String,candidate: String) -> void:
	var source_sha:=FileAccess.get_sha256(source);var candidate_sha:=FileAccess.get_sha256(candidate);var source_time:=FileAccess.get_modified_time(source);var candidate_time:=FileAccess.get_modified_time(candidate)
	check(app.pose_editor.add_model(candidate).is_empty(),"ordinary Add model loads newly reconstructed native candidate")
	var actor: RefCounted=app.renderer.active_model();var id: String=actor.data.id;var head:=""
	for bone in actor.order:
		if str(actor.bones[bone].name).to_lower().ends_with("head1"):head=bone;break
	var guide:=weighted_guide(actor)
	check(not head.is_empty() and not guide.is_empty() and head!=guide,"native Head and a positively weighted new guide are identified independently")
	if head.is_empty() or guide.is_empty():await app.quit_studio();quit(1);return
	var native_pose: Dictionary={head:{"position":[0,0,0],"rotation_xyzw":[0,.125,0,1]}};var edited: Dictionary=native_pose.duplicate(true);edited[guide]={"position":[0,0,0],"rotation_xyzw":[0,0,.1875,1]}
	actor.data.pose=native_pose.duplicate(true);var transform: Dictionary={"position":actor.data.position.duplicate(),"rotation_xyzw":actor.data.rotation_xyzw.duplicate(),"scale":actor.data.scale};actor.data.pose_keys=[]
	for frame in range(4):actor.data.pose_keys.append({"frame":frame,"pose":(native_pose if frame in [0,3] else edited).duplicate(true),"transform":transform.duplicate(true),"interpolation":"hold"})
	check(Model.validate(actor.data,4).is_empty() and actor.data.pose_keys.all(func(key):return key.pose.get(head)==native_pose[head]),"four authored keys preserve nonzero native Head FK with edited guide only in middle frames")
	app.pose_editor.apply_frame();app.pose_editor.frame_model();app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,app.renderer.camera.fov)]
	for layer in app.layers:layer.cels.clear()
	app.show_project_options();var timing_error: String=app.project_timing.apply_duration(4);app.project_options.hide();actor=app.renderer.world_runtime.instance(id)
	check(timing_error.is_empty() and app.video.duration_frames==4 and app.video.width==1920 and app.video.height==1080 and app.video.fps_num==24 and app.video.fps_den==1,"ordinary timing sets exactly four1080p24 authored frames")
	var hashes: Array=[];var modes: Array=["rest","flex","flex","rest"];var head_frames: Array=[];var guide_frames: Array=[]
	for frame in range(4):
		app.set_frame(frame);await settle();var image: Image=await app.renderer.capture(app.keys,app.layers,frame,true);hashes.append(Storage.image_hash(image));head_frames.append(actor.bone_transform(head));guide_frames.append(actor.bone_transform(guide));image.save_png(folder.path_join("preview-%d.png"%frame))
		check(image.get_size()==Vector2i(1920,1080) and mode(actor)==modes[frame] and app.physics_editor.simulations.is_empty(),"authored frame%d renders expected rest/flexible view without live cache owner"%frame)
	check(hashes[0]==hashes[3] and hashes[1]==hashes[2],"identical keyed poses reproduce exact rest and edited pixels")
	check(hashes[0]!=hashes[1],"edited guide changes actual rendered native hair instead of only resource flags")
	app.set_frame(0);await settle();var packed:=folder.path_join("Reconstructed hair four frames.has");app.has_project.save_file(packed,"packed");await job()
	check(app.has_project.path==packed and FileAccess.file_exists(packed),"ordinary packed Save creates portable owner-review project")
	var saved_data: Dictionary=actor.data.duplicate(true);var saved_keys: Array=app.keys.duplicate(true);var export_error: String=await app.export_movie(folder);var movie: String=app.last_finished_movie
	check(export_error.is_empty() and FileAccess.file_exists(movie) and app.selected_movie_profile()=="standard","ordinary exporter creates actual Standard H264 movie")
	for frame in range(4):check(Storage.image_hash(Image.load_from_file(app.last_export_folder.path_join("frame_%06d.png"%(frame+1))))==hashes[frame],"movie sourcePNG%d exactly matches shared authored preview"%frame)
	check(actor.data==saved_data and app.keys==saved_keys,"save and export preserve original native pose and guide/camera keys")
	check(FileAccess.get_sha256(source)==source_sha and FileAccess.get_sha256(candidate)==candidate_sha and FileAccess.get_modified_time(source)==source_time and FileAccess.get_modified_time(candidate)==candidate_time,"owned source and candidate remain byte/time unchanged")
	check(app.renderer.native_readbacks==0 and app.physics_editor.simulations.is_empty(),"movie completes without simulation leases or pending native readbacks")
	# Ordinary project JSON represents integral numbers as JSON numbers. Compare
	# the exact wire-domain dictionaries AND separate native Transform3D values;
	# never equate a changed author value with a numeric-type-only round trip.
	var expected: Dictionary={"id":id,"sha":actor.data.sha256,"head":head,"guide":guide,"pose":JSON.parse_string(JSON.stringify(actor.data.pose,"",true,true)),"pose_keys":JSON.parse_string(JSON.stringify(actor.data.pose_keys,"",true,true)),"hashes":hashes,"modes":modes,"head_frames":head_frames,"guide_frames":guide_frames}
	FileAccess.open(folder.path_join("expected.var"),FileAccess.WRITE).store_var(expected)
	print("RECONSTRUCTED_REST_MOVIE_WRITE "+JSON.stringify({"checks":checks,"failures":failures,"user_profile":OS.get_user_data_dir(),"frames":int(app.video.duration_frames),"timing_error":timing_error,"movie":movie,"encoder":app.encoder_path.text,"packed":packed,"source_arrays_published":false}));await app.quit_studio();quit(0 if failures==0 else 1)
