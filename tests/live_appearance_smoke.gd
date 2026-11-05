extends SceneTree
const Fixture=preload("res://tests/secondary_fixture.gd")
const World=preload("res://src/world_document.gd")
const Model=preload("res://src/model.gd")
var checks:=0
var failures:=0
var app
var folder: String
var metrics:={}
func _initialize() -> void:
	create_timer(100).timeout.connect(func():push_error("Live appearance watchdog");quit(2));call_deferred("run")
func check(value: bool,message: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+message)
	if not value:failures+=1
func settled() -> void:
	for i in range(6):await process_frame
	await RenderingServer.frame_post_draw
func colors(image: Image) -> int:
	var count:=0
	for y in range(0,image.get_height(),3):
		for x in range(0,image.get_width(),3):
			var c:=image.get_pixel(x,y)
			if maxf(c.r,maxf(c.g,c.b))-minf(c.r,minf(c.g,c.b))>.12:count+=1
	return count
func start_hair(rig) -> void:
	app.physics_editor.hair_toggle.button_pressed=true
	while app.physics_editor.pending.has(rig.data.id):await process_frame
	await settled()
func appearance(rig,label: String,flat: bool,parent_alpha:=1.) -> void:
	var data: Dictionary=rig.data.duplicate(true);var shots: Array=app.keys.duplicate(true);var view: Dictionary=app.renderer.view_state()
	var before: Image=app.renderer.viewport.get_texture().get_image();before.save_png(folder.path_join(label+"-before.png"))
	var count:=colors(before)
	await start_hair(rig)
	var after: Image=app.renderer.viewport.get_texture().get_image();after.save_png(folder.path_join(label+"-live.png"))
	check(app.physics_editor.active(rig.data.id),"actual Hair & clothes control starts: "+label)
	check(rig.opacity_materials.unshaded==flat and absf(rig.evaluated_opacity-parent_alpha)<.000001,"live secondary update retains project lighting and inherited opacity: "+label)
	if flat:check(count>1000 and colors(after)>1000,"native colored skin remains visible in Unshaded live motion: "+label)
	check(rig.data==data and app.keys==shots and app.renderer.view_state()==view,"live appearance changes no authored model, shot key or view: "+label)
	metrics[label]={"before_colors":count,"live_colors":colors(after),"unshaded":rig.opacity_materials.unshaded,"opacity":rig.evaluated_opacity}
	app.physics_editor.clear()
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
	var asset:=folder.path_join("secondary.glb");Fixture.create(asset);var sha:=FileAccess.get_sha256(asset)
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false
	app.pose_editor.add_model(asset);var rig: RefCounted=app.renderer.active_model();app.pose_editor.frame_model();await settled()
	check(app.video.lighting_mode=="unshaded" and not app.renderer.studio_light.visible,"real new project uses Unshaded without studio illumination")
	await appearance(rig,"original-unshaded",true)
	app.change_lighting(1);await settled();await appearance(rig,"original-lit",false)
	app.change_lighting(2);await settled();await appearance(rig,"original-studio",false)
	check(FileAccess.get_sha256(asset)==sha,"original fixture bytes stay unchanged")
	# A faded parent must be inherited once while live, not replaced with default alpha1.
	app.new_project();var empty:=folder.path_join("empty.glb");preload("res://src/scene3d.gd").make_empty(empty)
	var parent:=Model.Clips.promote(World.object(empty,"group","Fading parent"));parent.format=Model.Visibility.FORMAT;parent.visibility_keys=[{"frame":0,"visible":false}]
	var child:=World.object(asset);child.parent_id=parent.id
	var world:=World.empty();world.objects=[parent,child];check(app.restore_world(world).is_empty(),"parented secondary fixture installs")
	app.video.visibility_fade_ms=1000;app.set_frame(12);app.world_selection.select_entity(child.id);rig=app.renderer.active_model();app.pose_editor.frame_model();await settled()
	check(absf(rig.evaluated_opacity-.5)<.000001,"ordinary world evaluation starts at half parent opacity")
	await appearance(rig,"parent-fade",true,.5)
	app.set_frame(12);await start_hair(rig)
	app.pose_editor.add_model(asset)
	for i in range(240):
		await process_frame
		if app.physics_editor.active(child.id) and app.physics_editor.import_starts.is_empty() and app.physics_editor.pending.is_empty():break
	await settled();rig=app.renderer.world_runtime.instance(child.id)
	check(app.physics_editor.active(child.id) and rig.opacity_materials.unshaded and absf(rig.evaluated_opacity-.5)<.000001,"live peer restart after normal Add retains inherited fade and Unshaded")
	app.physics_editor.clear()
	rig.apply(12)
	check(not rig.opacity_materials.unshaded and rig.evaluated_opacity==1.,"explicit legacy apply defaults remain independent of cached world context")
	var natives:=[]
	for name in ["AvatarSample_A.vrm","AvatarSample_Avrm0.vrm"]:
		var path: String=preload("res://tests/native_sample_paths.gd").vrm(name)
		if not FileAccess.file_exists(path):print("SKIP private "+name);continue
		var original:=FileAccess.get_sha256(path);app.new_project();app.pose_editor.add_model(path)
		while app.source_import.pid>0:await process_frame
		for node in app.get_children():
			if node is AcceptDialog and node.title=="Imported with limitations":node.hide();node.queue_free()
		await settled();rig=app.renderer.active_model();check(rig!=null,"native VRM loads: "+name)
		if not rig:continue
		app.pose_editor.frame_model();await settled();await appearance(rig,name.get_basename(),true)
		check(FileAccess.get_sha256(path)==original,"original native file remains unchanged: "+name);natives.append(name)
	var result:={"checks":checks,"failures":failures,"metrics":metrics,"folder":folder,"native_models":natives}
	var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close();app.free();await settled()
	print("LIVE_APPEARANCE "+JSON.stringify(result));quit(0 if failures==0 else 1)
