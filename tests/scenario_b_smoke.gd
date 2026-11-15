extends SceneTree
const Timeline=preload("res://src/timeline.gd")
const World=preload("res://src/world_document.gd")
const Storage=preload("res://src/storage.gd")
const Lighting=preload("res://src/lighting.gd")
var app
var checks:=0
var failures:=0
var bundles:=[]
func _initialize() -> void:
	create_timer(290).timeout.connect(func():push_error("Scenario B watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settle() -> void:
	for i in range(5):await process_frame
	await RenderingServer.frame_post_draw
func jobs() -> void:
	while app.has_project.pid>0 or app.source_import.pid>0:await process_frame
	await settle()
func dismiss_notes() -> void:
	for child in app.get_children():
		if child is AcceptDialog and child.visible:child.confirmed.emit();child.hide()
	await settle()
func mode(kind: String) -> void:
	app.lighting_choice.item_selected.emit(Lighting.MODES.find(kind));await settle()
func move_root(id: String,point: Vector3) -> void:
	app.world_selection.select_entity(id);app.pose_editor.selected="@root"
	app.pose_editor.operation.select(1);app.pose_editor.refresh_values()
	for i in range(3):app.pose_editor.fields[i].value=point[i]
	app.pose_editor.apply_numeric();await settle()
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0];var packed:=folder.path_join("Native ecosystems.has")
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false
	app.has_project.cache_root=folder.path_join("reader-cache" if "--read" in args else "writer-cache")
	if "--read" in args:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
		app.has_project.open_file(packed);await jobs()
		check(app.has_project.path==packed and not app.dirty and app.current_world().objects.size()==4,"cold packed Open restores both BSP roots, VRM and textured PMX without missing files")
		check(World.portable(app.renderer.world_state())==expected.world and app.keys==expected.camera,"cold Open retains exact native reports, map transforms, poses and camera")
		check(app.source_import.pid<0,"cold packed replay does not start native conversion")
		for kind in ["unshaded","lit"]:
			await mode(kind)
			var image: Image=await app.renderer.capture(app.keys,[],0,true);image.save_png(folder.path_join("cold-"+kind+".png"))
			check(Storage.image_hash(image)==expected.pixels[kind],"cold "+kind+" native composite exactly matches writer")
		var result:={"checks":checks,"failures":failures,"mode":"reader"};print("SCENARIO_B "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1);return
	var plan: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("plan.json")))
	app.import_actions.add(plan.bsp,false,0);await settle()
	var confirmation: ConfirmationDialog
	for child in app.get_children():
		if child is ConfirmationDialog and child.title=="Import Source map" and child.visible:confirmation=child;break
	check(confirmation!=null,"step1 ordinary Add scene offers native Source preparation review")
	if confirmation:confirmation.confirmed.emit();await settle()
	check(app.source_import.pid>0,"step1 confirmed Add scene starts native BSP worker")
	await jobs();await dismiss_notes()
	check(app.current_world().objects.size()==1,"step1 BSP worker adds one native environment")
	if app.current_world().objects.size()!=1:app.free();quit(1);return
	var first: String=app.last_import_id;var map_bundle: String=app.source_import.folder;bundles.append(map_bundle)
	var map_report: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(map_bundle.path_join("parameters.json")))
	var native: Dictionary=map_report.get("native_parameters",{})
	check(int(native.get("props_found",0))>0 and native.props_found==native.props_loaded,"step1 complete native BSP retains every referenced static prop")
	check(map_report.counts.textures>0 and native.static_brush_lightmaps.faces>0,"step4 map retains native textures and supported baked LDR brush lighting")
	check(not map_report.warnings.is_empty() and not map_report.limits.is_empty(),"step6 native approximation and skipped lightmap features remain explicit")
	var asset:=map_bundle.path_join("scene.glb");check(app.load_scene(asset).is_empty(),"step2 another map root appends without replacing the first map")
	var second: String=app.last_import_id;var before: Dictionary=World.portable(app.current_world())
	await move_root(second,Vector3(1000,0,0))
	var moved: Dictionary=World.portable(app.current_world())
	check(moved!=before and app.renderer.world_runtime.instance(first).data.position==[0,0,0],"step2 tree-selected map root moves independently of the first map")
	app.undo();await settle();check(World.portable(app.current_world())==before,"step2 map-root Undo restores exact world")
	app.redo();await settle();check(World.portable(app.current_world())==moved,"step2 map-root Redo restores exact placement")
	app.import_actions.add(plan.vrm,true,0);await jobs();await dismiss_notes();bundles.append(app.source_import.folder)
	check(app.current_world().objects.size()==3,"step1 ordinary native VRM import coexists with both BSP roots")
	if app.current_world().objects.size()!=3:app.free();quit(1);return
	var actor: String=app.last_import_id
	if app.physics_editor.active(actor):app.physics_editor.toggle.button_pressed=false;await settle()
	app.world_selection.select_entity(actor);app.world_selection.context_action(1);await settle()
	var rig=app.renderer.world_runtime.instance(actor);var suffix: String=rig.data.metadata.native_parameters.humanoid.leftUpperArm.node_name;var arm:=""
	for id in rig.order:
		if id.ends_with("::"+suffix):arm=id;break
	check(not arm.is_empty(),"step3 native VRM humanoid retains an accessible arm binding")
	if arm.is_empty():app.free();quit(1);return
	app.pose_editor.selected=arm;app.pose_editor.operation.select(0);app.pose_editor.refresh_values();app.pose_editor.fields[0].value=30;app.pose_editor.apply_numeric();await settle()
	check(not app.renderer.world_runtime.instance(actor).authored_keys().is_empty(),"step3 ordinary native arm pose authors editable animation")
	app.import_actions.add(plan.pmx,true,0);await jobs();await dismiss_notes();bundles.append(app.source_import.folder)
	check(app.current_world().objects.size()==4,"step1 complete native PMX import coexists with VRM and two BSP roots")
	if app.current_world().objects.size()!=4:app.free();quit(1);return
	var prop: String=app.last_import_id;var pmx_report: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(app.source_import.folder.path_join("parameters.json")))
	check(["atlas03_street_d.png","atlas02_street_d.png","atlas03_props_d.png","atlas02_props_d.png","atlas09_props_d.png"].all(func(name):return pmx_report.texture_dependencies.has(name)) and not pmx_report.has("missing_textures"),"step6 complete PMX retains all five named atlas dependencies without missing-texture fallback")
	await move_root(prop,Vector3(20,0,0));check(app.renderer.world_runtime.instance(prop).sample_transform(0,true).position[0]==20,"step3 native PMX placement uses ordinary editable root transform")
	app.world_selection.select_entity(actor);app.world_selection.frame_selected();await settle()
	app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,app.renderer.camera.fov)];app.video.duration_frames=24;app.set_frame(0)
	var pixels:={}
	for kind in ["unshaded","lit"]:
		await mode(kind)
		var image: Image=await app.renderer.capture(app.keys,[],0,true);image.save_png(folder.path_join("preview-"+kind+".png"));pixels[kind]=Storage.image_hash(image)
	check(pixels.unshaded!=pixels.lit,"step4 actual Lit and Unshaded native composites differ")
	app.has_project.save_file(packed,"packed");await jobs()
	check(app.has_project.path==packed and not app.dirty,"step5 normal self-contained HAS Save succeeds")
	var expected:={"world":World.portable(app.renderer.world_state()),"camera":app.keys,"pixels":pixels}
	FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify(expected,"",true,true))
	var error: String=await app.export_movie(folder)
	check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000001.png")).get_data()==Image.load_from_file(folder.path_join("preview-lit.png")).get_data(),"step5 actual 1080p24 movie input exactly matches native lit preview")
	var managed_sources:={}
	for row in app.current_world().objects:managed_sources[row.source]=row.sha256
	var result:={"checks":checks,"failures":failures,"mode":"writer","movie":app.last_finished_movie,"bundles":bundles,"managed_sources":managed_sources,"map_report":map_report,"pmx_report":pmx_report}
	FileAccess.open(folder.path_join("writer.json"),FileAccess.WRITE).store_string(JSON.stringify(result,"",true,true));print("SCENARIO_B "+JSON.stringify({"checks":checks,"failures":failures,"mode":"writer"}));app.free();quit(0 if failures==0 else 1)
