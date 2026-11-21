extends SceneTree
# Private ordinary-Open visual check. Takes protected .has and fresh output args.
# Never constructs a RenderControl or changes a mesh margin/material/visibility.
const ARCHIVE_SHA:="d304744dea70a05e7176b668bc10b0058b8cb4e6b1ffe5fc9fab05303da60efb"
const ASSET_SHA:="e3e233004f2ce1aed3c2f221f7d92d9218c0de1f133cad88557f8181644e6e8c"
var app
var checks:=0
var failures:=0
var images: Array=[]
func _initialize() -> void:
	create_timer(180).timeout.connect(func():push_error("Private ordinary face Open watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func bytes_digest(value: PackedByteArray) -> String:
	var hash:=HashingContext.new();hash.start(HashingContext.HASH_SHA256);hash.update(value);return hash.finish().hex_encode()
func digest(value: Variant) -> String:
	return bytes_digest(var_to_bytes(value))
func settle() -> void:
	for i in range(4):await process_frame
func pixels(image: Image) -> int:
	var bytes:=image.get_data();var count:=0
	for i in range(0,bytes.size(),4):
		if bytes[i+3]>0 and (bytes[i]>3 or bytes[i+1]>3 or bytes[i+2]>3):count+=1
	return count
func capture_private(folder: String,label: String) -> bool:
	var image: Image
	for i in range(2):
		if not app.renderer.begin_native_readback():return false
		var notification: RefCounted=app.renderer.native_frame_notification
		await notification.ready
		image=app.renderer.finish_native_readback()
	if image==null or image.is_empty():return false
	image.convert(Image.FORMAT_RGBA8)
	var saved: bool=image.save_png(folder.path_join(label+".png"))==OK
	images.append({"name":label+".png","width":image.get_width(),"height":image.get_height(),"nonblack_pixels":pixels(image),"rgba_sha256":bytes_digest(image.get_data()),"native_readbacks":app.renderer.native_readbacks})
	return saved and image.get_size()==Vector2i(1920,1080) and app.renderer.native_readbacks==0
func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if args.size()!=2 or DisplayServer.get_name()=="headless":push_error("Use private graphical job: protected stuff.has, fresh owned output folder");quit(2);return
	var source: String=args[0];var folder: String=args[1]
	if not DirAccess.dir_exists_absolute(folder) or not DirAccess.get_files_at(folder).is_empty() or not DirAccess.get_directories_at(folder).is_empty():push_error("Private output must be an existing empty owned folder");quit(2);return
	if FileAccess.get_sha256(source)!=ARCHIVE_SHA:push_error("This check requires the protected original saved scene");quit(2);return
	var original_time: int=FileAccess.get_modified_time(source)
	root.size=Vector2i(1600,1000);root.gui_embed_subwindows=true
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json");root.add_child(app);await settle()
	app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	app.has_project.open_file(source)
	while app.has_project.pid>0:await process_frame
	await settle()
	check(app.has_project.path==source and app.renderer.world_runtime!=null,"ordinary Open installs the protected project")
	if app.renderer.world_runtime==null or app.renderer.world_runtime.order.is_empty():await app.quit_studio();quit(1);return
	var actor: RefCounted=app.renderer.world_runtime.instance(app.renderer.world_runtime.order[0])
	check(FileAccess.get_sha256(actor.data.source)==ASSET_SHA,"ordinary Open restores the exact protected embedded GLB")
	app.world_selection.select_entity(actor.data.id,false);app.mode.select(2);app.change_mode(2);await settle()
	var original_frame: int=app.frame;var original_view: Dictionary=app.renderer.view_state()
	var world: String=digest(app.current_world());var shot: String=digest(app.keys);var history: int=app.history.size()
	var source_sha: String=FileAccess.get_sha256(actor.data.source)
	var diagnostics: Array=[]
	for at in [0,43]:
		app.set_frame(at)
		# Ordinary editor routes retain the saved draft at43; zero samples playback.
		app.renderer.evaluate(app.keys,at)
		if at==43:app.pose_editor.apply_frame()
		await settle()
		var view: Dictionary=app.renderer.view_state();var data: String=digest(actor.data)
		var info: Dictionary=actor.render_bounds_diagnostics();diagnostics.append({"frame":at,"active":info.active,"blocked":info.blocked,"error":info.error,"meshes":info.meshes,"builds":info.builds,"stats":info.stats})
		check(info.active and not info.blocked and info.error.is_empty(),"ordinary model evaluation activates every admitted mesh bounds cache")
		check(await capture_private(folder,"frame%d_saved_close" % at),"ordinary saved close view captures a full frame with balanced readback")
		var queried: Dictionary=app.renderer.PoseBounds.query(actor.root)
		if not queried.error.is_empty():push_error(queried.error);failures+=1;break
		var bounds: AABB=queried.bounds;var direction: Vector3=app.renderer.camera.global_basis.z.normalized()
		var distance: float=maxf(.1,bounds.size.length()*.625/sin(deg_to_rad(app.renderer.camera.fov*.5)))
		app.renderer.camera.global_position=bounds.get_center()+direction*distance
		app.renderer.camera.look_at(bounds.get_center(),Vector3.UP)
		check(await capture_private(folder,"frame%d_whole_body" % at),"temporary whole-body view captures without replacing shot keys")
		app.renderer.restore_view(view)
		check(digest(actor.data)==data and digest(app.keys)==shot and app.renderer.view_state()==view,"both visual captures preserve authored model camera keys and saved view")
	app.set_frame(original_frame);app.renderer.restore_view(original_view);await settle()
	check(FileAccess.get_sha256(source)==ARCHIVE_SHA and FileAccess.get_modified_time(source)==original_time and FileAccess.get_sha256(actor.data.source)==source_sha,"protected source archive and restored managed GLB remain unchanged")
	check(digest(app.current_world())==world and digest(app.keys)==shot and app.history.size()==history,"ordinary Open visual checks add no authored scene edit or Undo command")
	check(images.size()==4 and app.renderer.native_readbacks==0 and app.world_selection.pick_requests.is_empty(),"all four private captures complete with balanced native waits")
	var result:={"format":"has_private_ordinary_face_open_1","status":"CAPTURED_FOR_VISUAL_REVIEW" if failures==0 else "FAIL","checks":checks,"failures":failures,"user_profile":OS.get_user_data_dir(),"archive_sha256":ARCHIVE_SHA,"managed_source_sha256":source_sha,"images":images,"bounds_diagnostics":diagnostics,"authored_world_preserved":digest(app.current_world())==world,"shot_keys_preserved":digest(app.keys)==shot,"Undo_count_preserved":app.history.size()==history,"readbacks_balanced":app.renderer.native_readbacks==0,"visual_face_and_body_passed":false,"visual_review_required":true}
	var output:=FileAccess.open(folder.path_join("private-ordinary-face-result.json"),FileAccess.WRITE)
	if output==null:push_error("Cannot write private capture result");failures+=1
	else:output.store_string(JSON.stringify(result,"",true,true));output.flush();output.close()
	print("POSED_BOUNDS_OWNER_OPEN "+JSON.stringify({"checks":checks,"failures":failures,"captures":images.size(),"user_profile":OS.get_user_data_dir(),"authored_world_preserved":result.authored_world_preserved,"readbacks_balanced":result.readbacks_balanced,"visual_review_required":true}))
	await app.quit_studio();quit(0 if failures==0 else 1)
