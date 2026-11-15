extends "res://tests/large_project_smoke.gd"
const Packages=preload("res://src/asset_package.gd")
func clean(value):
	if value is int:return float(value)
	if value is Array:
		var result: Array=[]
		for item in value:result.append(clean(item))
		return result
	if value is Dictionary:
		var result: Dictionary={}
		for key in value:result[key]=clean(value[key])
		return result
	return value
func stamp(value) -> String:return JSON.stringify(clean(value),"",true,true)
func hashes() -> Array:
	var result: Array=[]
	for layer in app.layers:
		for cel in layer.cels:result.append(Storage.image_hash(Drawing.image(cel)))
	return result
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
	var reading:="--read" in OS.get_cmdline_user_args()
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("reader-recovery" if reading else "recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("reader-cache" if reading else "cache")
	if reading:await read_packages();return
	var figure:=folder.path_join("original.glb");check(preload("res://tests/helper_rig_fixture.gd").create(figure)==OK,"original skinned model with helper bones created")
	var room:=folder.path_join("room.glb");check(preload("res://src/scene3d.gd").make_fixture(room)==OK,"original map created")
	var placement: Dictionary=app.import_actions.placement();placement.physics_on_import=false;check(app.pose_editor.add_model(figure,0,placement).is_empty(),"ordinary model import succeeds")
	var rig=app.renderer.active_model();var id: String=rig.data.id;rig.data.metadata["native_parameters"]={"fixture_provenance":"Original helper figure","unsupported":"native fidelity is separate"};var native: Dictionary=rig.data.metadata.native_parameters.duplicate(true)
	app.pose_editor.selected="@root";app.pose_editor.operation.select(1);app.pose_editor.refresh_values()
	for field in app.pose_editor.fields:field.value=0
	app.pose_editor.apply_numeric();app.pose_editor.record_key();app.set_frame(12);app.pose_editor.operation.select(0);app.pose_editor.refresh_values();app.pose_editor.fields[1].value=30;app.pose_editor.apply_numeric();var authored:=stamp(rig.authored_keys())
	var map_report:={"kind":"original_fixture","source_file":"Original map.glb","source_sha256":FileAccess.get_sha256(room),"dependencies":["embedded original geometry"]};var report_file:=FileAccess.open(folder.path_join("parameters.json"),FileAccess.WRITE);report_file.store_string(JSON.stringify(map_report));report_file.close()
	check(app.load_scene(room).is_empty(),"ordinary map import succeeds");var map_id: String=app.last_import_id
	Drawing.insert(app.layers[1],0,48,Drawing.blank(1920,1080));var image: Image=Drawing.edit_image(app.layers[1].cels[0]).image;image.set_pixel(70,70,Color.CYAN);Drawing.touch(image);app.changed()
	app.keys=[Model.Timeline.key(0,Vector3(0,1,4),Quaternion.IDENTITY,60)];app.has_project.save_file(folder.path_join("Main.has"),"packed");await wait_job();app.changed()
	var identity: String=app.has_project.path;var session: String=app.recovery_session;var revision: int=app.recovery_revision;var before:=stamp(app.current_world());var pixels:=hashes();var camera:=stamp(app.keys);var video:=stamp(app.video);var history: int=app.history.size()
	var scene_hash:=FileAccess.get_sha256(identity);app.world_selection.select_entity(id);app.has_project.save_asset(identity)
	check(FileAccess.get_sha256(identity)==scene_hash and not app.exporting and app.dirty and app.has_project.path==identity and app.history.size()==history,"asset export refuses overwriting the current scene without changing file or state")
	app.world_selection.select_entity(id);var buttons: Array=app.find_children("*","Button",true,false).filter(func(node):return node.text=="Save asset .has...")
	check(buttons.size()==1 and buttons[0].is_visible_in_tree(),"Simple World panel exposes asset packaging action")
	await click(buttons[0]);var dialogs: Array=app.find_children("*","FileDialog",true,false).filter(func(node):return node.title=="Save selected asset as .has")
	check(dialogs.size()==1 and dialogs[0].visible,"actual packaging button opens dedicated HAS save dialog")
	if dialogs.size()!=1:await app.quit_studio();quit(1);return
	dialogs[0].file_selected.emit(folder.path_join("Figure.has"));await wait_job();app.world_selection.select_entity(map_id);app.has_project.save_asset(folder.path_join("Map.has"));await wait_job()
	check(FileAccess.file_exists(folder.path_join("Figure.has")) and FileAccess.file_exists(folder.path_join("Map.has")),"model and map independently save through existing portable HAS container")
	check(app.has_project.path==identity and app.dirty and app.recovery_session==session and app.recovery_revision==revision and app.history.size()==history,"asset export never marks scene clean, changes identity, resets recovery or adds Undo")
	check(stamp(app.current_world())==before and hashes()==pixels and stamp(app.keys)==camera,"asset export preserves source scene, independent paint and camera")
	var count: int=app.current_world().objects.size();app.pose_editor.import_dialog();var picker: Array=app.find_children("*","FileDialog",true,false).filter(func(node):return node.title=="Add 3D model")
	check(picker.size()==1 and "*.has" in picker[0].filters,"ordinary Add model picker accepts existing HAS asset packages")
	if picker.size()!=1:await app.quit_studio();quit(1);return
	picker[0].file_selected.emit(folder.path_join("Figure.has"));await wait_job();var added: String=app.last_import_id;rig=app.renderer.world_runtime.instance(added)
	check(app.current_world().objects.size()==count+1 and added!=id and rig.data.metadata.native_parameters==native and stamp(rig.authored_keys())==authored,"import creates an independent object with exact authored controls and native provenance")
	check(app.has_project.path==identity and hashes()==pixels and stamp(app.keys)==camera and stamp(app.video)==video and app.history.size()==history+1,"asset import is one Undo and preserves scene identity, settings, paint and camera")
	app.undo();check(app.current_world().objects.size()==count,"Undo removes only the imported package object");app.redo();check(app.current_world().objects.size()==count+1 and app.renderer.world_runtime.instance(added)!=null,"Redo restores independent packaged object")
	app.set_frame(0);app.import_actions.add(folder.path_join("Map.has"),false,0);await wait_job();var map_added: String=app.last_import_id;check(map_added!=map_id and app.renderer.world_runtime.instance(map_added).data.kind=="environment" and app.renderer.world_runtime.instance(map_added).data.metadata.native_parameters==map_report,"map package reuses ordinary independent environment world record")
	app.import_actions.add(folder.path_join("Map.has"),false,12);await wait_job();check(app.renderer.world_runtime.instance(app.last_import_id).data.start_frame==12,"static map package can be reused at a later introduction frame")
	var unchanged:=stamp(app.current_world());var old_history: int=app.history.size();app.import_actions.add(folder.path_join("Figure.has"),false,0);await wait_job();check(stamp(app.current_world())==unchanged and app.history.size()==old_history,"wrong model/map role refuses without modifying the scene")
	app.import_actions.add(folder.path_join("Figure.has"),true,12);await wait_job();check(stamp(app.current_world())==unchanged and app.history.size()==old_history,"animated package refuses implicit retiming instead of truncating authored controls")
	app.import_actions.add(folder.path_join("Main.has"),true,0);await wait_job();check(stamp(app.current_world())==unchanged and app.has_project.path==identity,"ordinary scene HAS is refused by asset import without replacing the project")
	app.set_frame(12);var expected: Image=await app.renderer.capture(app.keys,app.layers,12,true);expected.save_png(folder.path_join("expected.png"));app.has_project.save_file(folder.path_join("Combined.has"),"packed");await wait_job();DirAccess.rename_absolute(figure,figure+".offline");DirAccess.rename_absolute(room,room+".offline");app.new_project();app.has_project.open_file(folder.path_join("Combined.has"));await wait_job()
	check((await app.renderer.capture(app.keys,app.layers,12,true)).get_data()==expected.get_data() and app.renderer.world_runtime.instance(added).data.metadata.native_parameters==native,"combined scene reopens exact package pixels and native metadata with originals offline")
	var error: String=await app.export_movie(folder);check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000013.png")).get_data()==expected.get_data(),"movie includes exact independently imported package scene and cels")
	DirAccess.rename_absolute(figure+".offline",figure);DirAccess.rename_absolute(room+".offline",room)
	var expected_file:=FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE);expected_file.store_string(JSON.stringify({"native":native,"map_report":map_report,"authored":authored,"camera":app.keys}));expected_file.flush();expected_file.close()
	print("ASSET_PACKAGE "+JSON.stringify({"checks":checks,"failures":failures,"movie":app.last_export_folder.path_join("movie.mp4")}));await app.quit_studio();quit(0 if failures==0 else 1)

func read_packages() -> void:
	var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
	app.import_actions.add(folder.path_join("Figure.has"),true,0);await wait_job();var model_id: String=app.last_import_id;var rig=app.renderer.world_runtime.instance(model_id)
	check(rig!=null and rig.data.metadata.native_parameters==expected.native and stamp(rig.authored_keys())==expected.authored,"fresh process imports model package with exact native report and authored controls")
	app.import_actions.add(folder.path_join("Map.has"),false,0);await wait_job();var map=app.renderer.world_runtime.instance(app.last_import_id)
	check(app.current_world().objects.size()==2 and map.data.metadata.native_parameters==expected.map_report,"fresh process independently imports map package and its supplied provenance")
	app.keys=expected.camera;Drawing.insert(app.layers[1],0,48,Drawing.blank(1920,1080));var image: Image=Drawing.edit_image(app.layers[1].cels[0]).image;image.set_pixel(70,70,Color.CYAN);Drawing.touch(image);app.set_frame(12)
	var picture: Image=await app.renderer.capture(app.keys,app.layers,12,true);check(picture.get_data()==Image.load_from_file(folder.path_join("expected.png")).get_data(),"cold package-only reader matches saved scene composition with originals and writer HAS cache offline")
	check(app.has_project.path.is_empty() and app.dirty,"asset-only import leaves an independent unsaved scene")
	print("ASSET_PACKAGE_READ "+JSON.stringify({"checks":checks,"failures":failures}));await app.quit_studio();quit(0 if failures==0 else 1)
