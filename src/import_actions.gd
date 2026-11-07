extends Node
# User import intent stays attached to each request across asynchronous preparation.
var app
var offer_height:=false
const MODEL_FILTERS=["*.has","*.glb","*.gltf","*.fbx","*.obj","*.pmd","*.pmx","*.vrm","*.mdl","*.gma","*.bin"]
const MAP_FILTERS=["*.has","*.glb","*.gltf","*.fbx","*.obj","*.pmd","*.pmx","*.bsp","*.gma","*.bin"]

func canvas_point(screen_point: Vector2) -> Vector2:
	return app.canvas.get_global_transform()*(app.canvas.get_screen_transform().affine_inverse()*screen_point)

func os_drop(files: PackedStringArray) -> void:
	# Native shell drags need the current OS cursor, not cached viewport mouse motion.
	drop(files,canvas_point(Vector2(DisplayServer.mouse_get_position())))

func placement() -> Dictionary:
	return {"camera":app.renderer.camera.global_transform,"fov":app.renderer.camera.fov,"near":app.renderer.camera.near,"far":app.renderer.camera.far,"aspect":float(app.renderer.viewport.size.x)/app.renderer.viewport.size.y,"physics_on_import":true,"review_height":offer_height}

func busy() -> bool:
	if app.exporting or app.source_import.pid>0 or app.has_project.pid>0 or app.height_review and app.height_review.pending:return true
	return app.has_dialog(app)

func pick(at_frame: int, actor: bool) -> void:
	if busy():app.message("Finish the current import or dialog first.");return
	app.stop();app.finish_stroke();app.pose_editor.finish_drag();app.release_mouse()
	var target:=clampi(at_frame,0,int(app.video.duration_frames)-1)
	app.set_frame(target)
	app.choose_file("Add model at frame %d" % target if actor else "Add environment at frame %d" % target,MODEL_FILTERS if actor else MAP_FILTERS,func(path):add(path,actor,target),app.source_import.default_browse_dir())

func add(path: String, actor: bool, at_frame: int) -> void:
	if busy():app.message("Finish the current import or dialog first.");return
	if at_frame<0 or at_frame>=app.video.duration_frames:app.message("Import frame is outside this project.");return
	app.stop()
	if path.get_extension().to_lower()=="has":app.has_project.import_asset(path,"model" if actor else "environment",at_frame);return
	var error: String=app.pose_editor.add_model(path,at_frame,placement()) if actor else app.load_scene(path,at_frame)
	if not error.is_empty():app.message(error)

func drop(files: PackedStringArray, point: Vector2) -> void:
	if app.home and app.home.visible:app.message("Choose New scene or Return to scene before dropping a 3D file.");return
	if not app.canvas.get_global_rect().has_point(point):app.message("Drop a 3D file over the scene viewport.");return
	if busy():app.message("Finish the current import or dialog first.");return
	if files.size()!=1:app.message("Drop one file at a time. No files were added.");return
	var path:=files[0];var extension:=path.get_extension().to_lower()
	if not extension in ["has","glb","gltf","fbx","obj","pmd","pmx","vrm","mdl","bsp","gma","bin"]:
		app.message("This file is not a supported 3D import. Use Add model or Add scene for supported types.");return
	app.stop();app.finish_stroke();app.pose_editor.finish_drag();app.release_mouse()
	if extension in ["mdl","vrm","pmd"]:add(path,true,0);return
	if extension=="bsp":add(path,false,0);return
	var dialog:=ConfirmationDialog.new();dialog.title="Add "+path.get_file();dialog.dialog_text="Add this as a model/prop or an environment/map?\nIt will be present from frame 0. Existing objects stay in the scene."
	dialog.ok_button_text="Model / prop"
	var map_button:=dialog.add_button("Environment / map",false,"map")
	app.add_child(dialog)
	var action:=func(actor: bool):dialog.hide();dialog.queue_free();add(path,actor,0)
	dialog.confirmed.connect(func():action.call(true))
	dialog.custom_action.connect(func(_name):action.call(false))
	dialog.canceled.connect(dialog.queue_free);dialog.popup_centered(Vector2i(600,220))
