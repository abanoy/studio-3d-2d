extends SceneTree
const Timeline=preload("res://src/timeline.gd")
const Storage=preload("res://src/storage.gd")
const Model=preload("res://src/model.gd")
const Drawing=preload("res://src/drawing.gd")
const Fixture=preload("res://tests/limb_fixture.gd")
const Placement=preload("res://src/import_placement.gd")
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(170).timeout.connect(func():push_error("Camera range watchdog");quit(2));call_deferred("run")
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func native_pixels(renderer) -> Image:
	# Preserve manual visibility and the temporary camera; capture() would
	# reevaluate the world. Setup may have suspended the native viewport.
	if not renderer.begin_native_readback():return null
	var notification=renderer.native_frame_notification
	await notification.ready
	return renderer.finish_native_readback()
func wait_job(job) -> void:
	while job.pid>0:await process_frame
	await settled()
func green(image: Image) -> int:
	var data:=image.get_data();var count:=0
	for i in range(0,data.size(),4):
		if data[i+1]>200 and data[i]<20 and data[i+2]<20:count+=1
	return count
func fixture(path: String) -> Error:
	var scene:=Node3D.new();scene.name="DistantOriginalWall"
	var wall:=MeshInstance3D.new();wall.name="WallAt5000";wall.position.z=-5000
	var mesh:=BoxMesh.new();mesh.size=Vector3(2000,2000,10);wall.mesh=mesh
	var material:=StandardMaterial3D.new();material.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED;material.albedo_color=Color.GREEN;wall.material_override=material
	scene.add_child(wall);wall.owner=scene
	var doc:=GLTFDocument.new();var state:=GLTFState.new();var result:=doc.append_from_scene(scene,state)
	if result==OK:result=doc.write_to_filesystem(state,path)
	scene.free();return result
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0];var asset:=folder.path_join("distant.glb");var limb:=folder.path_join("limb.glb")
	check(fixture(asset)==OK and Fixture.create(limb)==OK,"original far-scene and small reference fixtures created")
	var source_hash:=FileAccess.get_sha256(asset);var limb_hash:=FileAccess.get_sha256(limb)
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.display_prefs_path=folder.path_join("display.cfg");app.recent_path=folder.path_join("recent.json");root.add_child(app);await settled()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	check(app.append_object(Model.definition(asset),"environment").is_empty(),"far scene loads through the standard world contract")
	var small:=Model.definition(limb);small.position=[20,0,-30];check(app.append_object(small,"model").is_empty(),"nearby pose reference loads independently")
	var actor: RefCounted=app.renderer.active_model();var actor_id: String=actor.data.id
	check(not app.advanced_mode and not app.camera_far.is_visible_in_tree(),"Simple mode keeps projection tuning hidden")
	app.advanced_toggle.button_pressed=true;app.advanced_toggle.pressed.emit();app.mode.select(1);app.change_mode(1)
	check(app.camera_near.is_visible_in_tree() and app.camera_near.editable and app.camera_far.editable,"Advanced exposes editable view-distance controls in camera mode")
	var count: int=app.keys.size();var history: int=app.history.size();var dirty: bool=app.dirty
	var prior_keys: Array=app.keys.duplicate(true)
	app.fov.value=75
	check(app.renderer.camera.fov==75 and app.keys==prior_keys and app.history.size()==history and app.dirty==dirty and "Save camera key [K]" in app.status.text,"field-of-view preview points to explicit recording without editing shot keys")
	app.camera_far.value=12000
	check(app.renderer.camera.far==12000 and app.keys.size()==count and app.history.size()==history and app.dirty==dirty,"view-distance edit stays temporary without keys, history or dirty changes")
	var prior_near: float=app.renderer.camera.near;app.camera_near.value=13000
	check(app.renderer.camera.near==prior_near and app.renderer.camera.far==12000,"invalid near/far UI combination refuses without changing the view")
	app.renderer.camera.transform=Transform3D.IDENTITY;app.renderer.camera.fov=60;app.insert_key()
	check(app.keys[0].far==12000 and is_equal_approx(app.keys[0].near,0.05),"explicit Save camera key records the actual projection range")
	var first: Dictionary=app.keys[0].duplicate(true)
	app.set_frame(24);app.renderer.camera.position.x=10;app.camera_near.value=0.25;app.camera_far.value=16000;app.insert_key()
	var middle:=Timeline.sample(app.keys,12)
	check(is_equal_approx(middle.near,0.15) and middle.far==14000 and middle.position.x==5,"visibility distances follow the shot's existing interpolation")
	var held: Array=app.keys.duplicate(true);held[0].interpolation="hold"
	check(Timeline.sample(held,23).far==12000 and Timeline.sample(held,24).far==16000,"hold and exact camera-key boundaries retain their projection range")
	var legacy: Array=[Timeline.key(0,Vector3.ZERO,Quaternion.IDENTITY,60)]
	check(Timeline.sample(legacy,12).far==2000 and Timeline.sample(legacy,12).near==0.05,"old keys retain the established cold-start clipping defaults")
	var mixed: Array=legacy.duplicate(true);mixed.append(app.keys[1].duplicate(true));mixed[0]["far"]=12000
	check(Timeline.range_error(mixed).is_empty() and is_equal_approx(Timeline.sample(mixed,12).near,0.15),"partially extended and old camera keys share the same explicit defaults")
	app.set_frame(12);app.mode.select(0);app.change_mode(0);app.create_cel(false);Drawing.edit_image(Drawing.cel_at(app.layers[1],12)).image.set_pixel(80,80,Color.CYAN)
	var before: Image=await app.renderer.capture(app.keys,app.layers,12,true);var visible:=green(before)
	check(visible>100000,"authored long-distance shot shows actual geometry 5000 units away")
	var close_clip: Array=app.keys.duplicate(true)
	for key in close_clip:key.near=6000
	var near_hidden: Image=await app.renderer.capture(close_clip,app.layers,12,true)
	check(green(near_hidden)==0 and near_hidden.get_pixel(80,80)==Color.CYAN,"near clipping affects 3D while independent screen-space drawing survives")
	var keys: Array=app.keys.duplicate(true);var actor_before: Dictionary=actor.data.duplicate(true);history=app.history.size()
	app.pose_editor.frame_model();var framed: Dictionary=app.renderer.view_state()
	check(framed.far==2000 and app.keys==keys and actor.data==actor_before and app.history.size()==history,"Frame model changes only the temporary view, including its own far distance")
	var after: Image=await app.renderer.capture(app.keys,app.layers,12,true)
	check(after.get_data()==before.get_data(),"framing a small model no longer removes distant geometry from the same shot")
	app.renderer.restore_view(framed)
	var export_error: String=await app.export_movie(folder)
	check(export_error.is_empty() and app.renderer.view_state()==framed,"MP4 export restores position, FOV and both editor clipping distances exactly")
	check(Image.load_from_file(app.last_export_folder.path_join("frame_000013.png")).get_data()==before.get_data(),"MP4 source frame matches the authored shot and independent cyan cel exactly")
	var movie: String=app.last_export_folder.path_join("movie.mp4")
	create_timer(0.03).timeout.connect(func():app.cancel_export=true)
	var cancelled: String=await app.export_movie(folder)
	check(cancelled.contains("cancelled") and app.renderer.view_state()==framed,"cancelled rendering restores the complete temporary view too")
	app.advanced_toggle.button_pressed=false;app.advanced_toggle.pressed.emit();var simple_view: Dictionary=app.renderer.view_state()
	check(not app.camera_far.is_visible_in_tree() and simple_view==framed,"returning to Simple hides tuning without changing projection")
	app.renderer.camera.near=0.2;app.renderer.camera.far=7777;var navigation: Dictionary=app.renderer.view_state()
	app.world_selection.clear();app.world_selection.select_entity(actor_id)
	check(app.renderer.view_state()==navigation,"world selection preserves the complete temporary camera view")
	app.change_lighting(2);check(app.renderer.view_state()==navigation,"project settings preserve temporary projection distances")
	app.undo();check(app.renderer.view_state()==navigation,"project-setting Undo preserves temporary projection distances")
	app.set_frame(0);app.mode.select(1);app.change_mode(1);app.camera_far.value=15000;app.insert_key();app.undo()
	check(app.keys[0]==first,"camera-key Undo restores the old range with its original shot")
	app.redo();check(app.keys[0].far==15000,"camera-key Redo restores the changed range")
	app.undo();app.set_frame(12)
	var portable_keys: Array=JSON.parse_string(JSON.stringify(keys,"",false,true))
	for kind in ["packed","linked"]:
		var project:=folder.path_join(kind+".has");app.has_project.save_file(project,kind);await wait_job(app.has_project)
		app.new_project();app.renderer.camera.near=9;app.renderer.camera.far=999999;app.has_project.open_file(project);await wait_job(app.has_project)
		check(app.keys==portable_keys and app.renderer.camera.far==14000 and is_equal_approx(app.renderer.camera.near,0.15),"normal HAS reopen restores projection from keys, independent of the previous document: "+kind)
		var reopened: Image=await app.renderer.capture(app.keys,app.layers,12,true)
		check(reopened.get_data()==before.get_data(),"portable shot and drawing render identically after HAS reopen: "+kind)
	var saved:=folder.path_join("directory");check(Storage.save_project(saved,app.video,app.keys,app.layers,app.source,app.frame,app.audio_clip,{}, {},false,app.renderer.world_state()).is_empty(),"ordinary directory save retains camera range")
	var manifest:=saved.path_join("project.json");var original:=FileAccess.get_file_as_bytes(manifest)
	for invalid in [NAN,INF,-1,"far",true,null,Timeline.MAX_FAR*2]:
		var bad: Array=app.keys.duplicate(true);bad[0].far=invalid
		var error:=Storage.save_project(saved,app.video,bad,app.layers,app.source,app.frame,app.audio_clip,{}, {},false,app.renderer.world_state())
		check(not error.is_empty() and FileAccess.get_file_as_bytes(manifest)==original,"bad camera range refuses before overwriting a good save: "+str(invalid))
	var malformed: Dictionary=JSON.parse_string(original.get_string_from_utf8());malformed.camera_keys[0].far=0
	var file:=FileAccess.open(manifest,FileAccess.WRITE);file.store_string(JSON.stringify(malformed));file.close()
	var state_before: Dictionary=app.renderer.world_state();var key_before: Array=app.keys.duplicate(true)
	check(not app.open_project(saved) and app.keys==key_before and app.renderer.world_state()==state_before,"invalid range on Open preserves the complete live project")
	file=FileAccess.open(manifest,FileAccess.WRITE);file.store_buffer(original);file.close()
	app.changed();app.autosave_tick(true);await preload("res://tests/recovery_wait.gd").checkpoint(app);var checkpoint: String=app.recovery_root.path_join(app.recovery_session)
	app.new_project();app.renderer.camera.near=5;app.renderer.camera.far=90000
	check(app.restore_checkpoint({"folder":checkpoint}) and app.keys==portable_keys,"actual recovery restores saved camera range and full keys")
	var recovered: Image=await app.renderer.capture(app.keys,app.layers,12,true)
	check(recovered.get_data()==before.get_data(),"recovered projection, world and independent drawing render identically")
	app.keys=legacy.duplicate(true);var old_project:=folder.path_join("legacy-camera.has");app.has_project.save_file(old_project,"packed");await wait_job(app.has_project)
	app.new_project();app.renderer.camera.near=2;app.renderer.camera.far=80000;app.has_project.open_file(old_project);await wait_job(app.has_project)
	check(not app.keys[0].has("near") and not app.keys[0].has("far") and app.renderer.camera.far==2000 and is_equal_approx(app.renderer.camera.near,0.05),"actual old-format HAS opens with established defaults without mutating its keys")
	var old_image: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	check(green(old_image)==0,"legacy cold-open output retains its original visibility-distance limit")
	app.mode.select(1);app.change_mode(1);app.renderer.camera.transform=Transform3D.IDENTITY;app.renderer.camera.near=100;app.renderer.camera.far=2000
	var context: Dictionary=app.import_actions.placement();var old_keys: Array=app.keys.duplicate(true)
	app.import_actions.add(limb,true,0);app.physics_editor.change(false)
	var imported: RefCounted=app.renderer.active_model();var box: AABB=app.renderer.scene_bounds(imported.root)
	check(context.near==100 and context.far==2000 and Placement.in_view(box,context) and app.renderer.camera.near==100 and app.renderer.camera.far==2000 and app.keys==old_keys,"interactive import respects the captured near plane without changing the view or shot")
	await settled();var shown: Image=await native_pixels(app.renderer);shown.save_png(folder.path_join("near-placement.png"))
	imported.root.hide();await settled();var hidden: Image=await native_pixels(app.renderer);imported.root.show()
	check(shown!=null and hidden!=null and shown.get_size()==Vector2i(1920,1080) and hidden.get_size()==shown.get_size() and app.renderer.native_readbacks==0,"native near-plane samples complete with balanced readback scopes")
	check(shown.get_data()!=hidden.get_data(),"model placed beyond a custom near plane produces actual visible pixels")
	app.renderer.camera.near=100;app.renderer.camera.far=100.01;var objects: Dictionary=app.renderer.world_state();var view: Dictionary=app.renderer.view_state()
	app.import_actions.add(limb,true,0)
	check(app.renderer.world_state()==objects and app.renderer.view_state()==view and app.status.text.contains("does not fit"),"a model too large for the current clip interval refuses with the complete world and view intact")
	app.renderer.camera.near=0.05;app.renderer.camera.far=3;context=app.import_actions.placement();app.import_actions.add(limb,true,0);app.physics_editor.change(false)
	check(Placement.in_view(app.renderer.scene_bounds(app.renderer.active_model().root),context) and app.renderer.camera.far==3,"interactive import also fits inside a short far distance without widening it")
	app.keys=keys.duplicate(true);app.set_frame(12)
	var plans: Array=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("native-plans.json")))
	var native_data:={};var native_orders:={}
	for plan in plans:
		var definition:=Model.definition(plan.source);definition.metadata=plan.metadata.duplicate(true);definition.position=[20,0,-30]
		var native_error: String=app.append_object(definition,"model")
		check(native_error.is_empty(),"native reference imports into the same shot: "+plan.label)
		if not native_error.is_empty():continue
		var native: RefCounted=app.renderer.active_model();var data: Dictionary=native.data.duplicate(true);var ids: Array=native.order.duplicate()
		var native_before: Image=await app.renderer.capture(app.keys,app.layers,12,true)
		app.pose_editor.frame_model();var native_after: Image=await app.renderer.capture(app.keys,app.layers,12,true)
		check(native_before.get_data()==native_after.get_data() and green(native_after)>100000 and native.data==data and native.order==ids and app.keys==keys,"native framing preserves distant shot, bone IDs and provenance: "+plan.label)
		native_data[native.data.id]=native.data.duplicate(true)
		native_orders[native.data.id]=ids
	var native_project:=folder.path_join("native-camera.has");app.has_project.save_file(native_project,"packed");await wait_job(app.has_project);app.new_project();app.has_project.open_file(native_project);await wait_job(app.has_project)
	var native_ok: bool=app.keys==portable_keys
	var reopened_data:={}
	for id in native_data:reopened_data[id]=app.renderer.world_runtime.instance(id).data.duplicate(true)
	var debug_file:=FileAccess.open(folder.path_join("native-before.json"),FileAccess.WRITE);debug_file.store_string(JSON.stringify(native_data,"",false,true));debug_file.close()
	debug_file=FileAccess.open(folder.path_join("native-after.json"),FileAccess.WRITE);debug_file.store_string(JSON.stringify(reopened_data,"",false,true));debug_file.close()
	for id in native_data:
		var loaded: RefCounted=app.renderer.world_runtime.instance(id)
		var expected: Dictionary=JSON.parse_string(JSON.stringify(native_data[id],"",false,true));var actual: Dictionary=loaded.data.duplicate(true)
		# Packed assets receive new managed addresses; compare every authored field
		# exactly and independently verify the relocated binary and bone identities.
		for address in ["source","path"]:expected.erase(address);actual.erase(address)
		native_ok=native_ok and actual==expected and loaded.order==native_orders[id] and FileAccess.get_sha256(loaded.data.source)==native_data[id].sha256
	check(native_ok and app.renderer.camera.far==14000,"combined native packed HAS retains projection and all original model data")
	check(FileAccess.get_sha256(asset)==source_hash and FileAccess.get_sha256(limb)==limb_hash,"projection work never changes source model files")
	var result:={"checks":checks,"failures":failures,"folder":folder,"movie":movie,"green_pixels":visible,"native_models":native_data.size()}
	file=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close();print("CAMERA_RANGE "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
