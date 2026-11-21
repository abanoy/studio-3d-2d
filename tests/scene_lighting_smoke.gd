extends SceneTree
const Document=preload("res://src/scene_lighting_document.gd")
const Runtime=preload("res://src/scene_lighting_runtime.gd")
const SceneIO=preload("res://src/scene3d.gd")
const Timeline=preload("res://src/timeline.gd")
const Storage=preload("res://src/storage.gd")
var checks:=0
var failures:=0
var folder: String
var graphics:=true
var measurements:={}
func _initialize() -> void:
	root.gui_embed_subwindows=true
	create_timer(240).timeout.connect(func():push_error("Scene lighting watchdog");quit(2));call_deferred("run")
func check(value: bool,title: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+title)
	if not value:failures+=1
func settled() -> void:
	for index in range(3):await process_frame
	if graphics:await RenderingServer.frame_post_draw
func wait_job(job: Node) -> void:
	while job.pid>0:await process_frame
	await settled()
func press(control: Control) -> void:
	var window:=control.get_window();var position:=control.get_global_rect().get_center()
	if window.is_embedded():position+=Vector2(window.position)
	var view: Window=root if window.is_embedded() else window
	var motion:=InputEventMouseMotion.new();motion.position=position;view.push_input(motion,true)
	for down in [true,false]:
		var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.pressed=down;event.position=position
		view.push_input(event,true);await process_frame
	await settled()
func write_json(path: String,data: Dictionary) -> void:
	var file:=FileAccess.open(path,FileAccess.WRITE);file.store_string(JSON.stringify(data,"",true,true));file.close()
func saved_equal(a: Variant,b: Variant) -> bool:
	# JSON decimal parsing can differ in the final double bits. IDs, keys and
	# booleans stay exact; numeric fixture values have a strict absolute bound.
	if (a is float or a is int) and (b is float or b is int):return absf(float(a)-float(b))<=1e-10
	if a is Dictionary and b is Dictionary:
		if a.size()!=b.size():return false
		for key in a:
			if not b.has(key) or not saved_equal(a[key],b[key]):return false
		return true
	if a is Array and b is Array:
		if a.size()!=b.size():return false
		for index in range(a.size()):
			if not saved_equal(a[index],b[index]):return false
		return true
	return a==b
func fixture(path: String,environment: bool) -> void:
	var scene:=Node3D.new();scene.name="ImportedRoom" if environment else "ImportedModel"
	if environment:
		SceneIO.box(scene,"Floor",Vector3(0,-.1,0),Vector3(14,.2,14),Color(.65,.65,.65))
		SceneIO.box(scene,"Wall",Vector3(0,2,-3),Vector3(14,4,.2),Color(.7,.7,.7))
		var original:=DirectionalLight3D.new();original.light_energy=0.;original.name="ImportedLamp";scene.add_child(original);original.owner=scene
	else:
		SceneIO.box(scene,"Body",Vector3(0,1,0),Vector3(1,2,1),Color(.8,.8,.8))
		SceneIO.box(scene,"Head",Vector3(0,2.3,0),Vector3(.65,.6,.65),Color(.8,.8,.8))
		var sphere:=MeshInstance3D.new();sphere.mesh=SphereMesh.new();sphere.position=Vector3(1.5,1.,0.)
		var chrome:=StandardMaterial3D.new();chrome.metallic=1.;chrome.roughness=.12;sphere.material_override=chrome
		scene.add_child(sphere);sphere.owner=scene;sphere.name="ReflectiveProp"
	var document:=GLTFDocument.new();var state:=GLTFState.new()
	check(document.append_from_scene(scene,state)==OK and document.write_to_filesystem(state,path)==OK,"Generated private "+scene.name+" GLB")
	scene.free()
func first_light(node: Node) -> Light3D:
	if node is Light3D:return node
	for child in node.get_children():
		var light:=first_light(child)
		if light:return light
	return null
func sum_region(image: Image,center: Vector2,radius:=12) -> Vector3:
	var sum:=Vector3.ZERO
	for y in range(maxi(0,int(center.y)-radius),mini(image.get_height(),int(center.y)+radius)):
		for x in range(maxi(0,int(center.x)-radius),mini(image.get_width(),int(center.x)+radius)):
			var c:=image.get_pixel(x,y);sum+=Vector3(c.r,c.g,c.b)
	return sum
func difference(a: Image,b: Image) -> float:
	var x:=a.get_data();var y:=b.get_data();var total:=0.
	for index in range(0,x.size(),12):total+=absf(int(x[index])-int(y[index]))
	return total
func edit(editor: Node,kind: String) -> void:
	editor.add_light(kind);editor.refresh()
func unit() -> void:
	var data:=Document.empty();data.lights.append(Document.create("spot",Vector3.ZERO))
	check(Document.error(data).is_empty(),"Valid scene light document")
	for change in ["duplicate","type","nan","range","angle","name","ambient","boolean"]:
		var bad:=data.duplicate(true)
		match change:
			"duplicate":bad.lights.append(bad.lights[0].duplicate(true))
			"type":bad.lights[0].type="area"
			"nan":bad.lights[0].energy=NAN
			"range":bad.lights[0].range=0
			"angle":bad.lights[0].spot_angle=90
			"name":bad.lights[0].name=" "
			"ambient":bad.ambient_energy=-1
			"boolean":bad.lights[0].visible=1
		check(not Document.error(bad).is_empty(),"Reject invalid lighting: "+change)
	check(Document.document({})==Document.empty(),"Old projects have no authored lights or injected ambient")
	var invalid:=data.duplicate(true);invalid["reflection"]={"enabled":true,"position":[0,0,0],"size":[0,10,10],"intensity":1.}
	check(not Document.error(invalid).is_empty(),"Reject zero-sized reflection region")
func make_app(theme: String):
	var prefs:=ConfigFile.new();prefs.set_value("display","theme",theme);prefs.save(folder.path_join("prefs-"+theme+".cfg"))
	var app=load("res://main.tscn").instantiate()
	app.recovery_root=folder.path_join("recovery-"+theme);app.recent_path=folder.path_join("recent-"+theme+".json");app.display_prefs_path=folder.path_join("prefs-"+theme+".cfg")
	root.add_child(app);await settled();app.home.hide();app.autosave_enabled.set_pressed_no_signal(false);app.has_project.cache_root=folder.path_join("cache-"+theme)
	return app
func run() -> void:
	var args:=OS.get_cmdline_user_args();folder=args[0];graphics=not "--cpu" in args
	if "--read" in args:
		await cold_read();return
	unit();fixture(folder.path_join("environment.glb"),true);fixture(folder.path_join("model.glb"),false)
	for theme in ["neon","light"]:
		var app=await make_app(theme)
		check(preload("res://src/studio_theme.gd").style==theme,"Actual app uses "+theme+" theme")
		check(app.load_scene(folder.path_join("environment.glb")).is_empty(),"Import environment through actual World workflow")
		var environment_id: String=app.last_import_id
		check(app.pose_editor.add_model(folder.path_join("model.glb")).is_empty(),"Import separate model through actual workflow")
		var model_id: String=app.last_import_id
		# Explicit placement removes import's intentional near-camera auto-placement.
		for id in [environment_id,model_id]:
			var actor=app.renderer.world_runtime.instance(id);actor.data.position=[0,0,0];actor.data.rotation_xyzw=[0,0,0,1];actor.data.scale=1.
		app.renderer.camera.position=Vector3(5,4,8);app.renderer.camera.look_at(Vector3(0,1,0))
		app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,55.)];app.set_frame(0)
		var world: Dictionary=app.renderer.world_state().duplicate(true);var keys: Array=app.keys.duplicate(true);var view: Dictionary=app.renderer.view_state()
		var imported:=first_light(app.renderer.world_runtime.instance(environment_id).root)
		check(imported!=null and imported.light_energy==0.,"Imported scene light retained")
		var editor: Node=app.scene_lighting_editor
		if graphics:await press(editor.launch)
		else:editor.launch.pressed.emit()
		await settled()
		check(editor.dialog.visible and editor.launch.is_visible_in_tree() and not app.advanced_mode,"Simple workspace offers actual Lights panel")
		var history: int=app.history.size()
		if graphics:await press(editor.add_buttons[0])
		else:editor.add_buttons[0].pressed.emit()
		if graphics:root.get_texture().get_image().save_png(folder.path_join(theme+"-lights-panel.png"))
		check(Document.document(app.video).lights.size()==1 and app.history.size()==history+1,"Directional creation is one Undo edit")
		var directional: String=editor.selected
		check(app.renderer.scene_lighting.nodes[directional] is DirectionalLight3D,"Directional runtime exists")
		var actor=app.renderer.world_runtime.instance(model_id);var bounds: AABB=app.renderer.scene_bounds(actor.root)
		var row: Dictionary=Document.document(app.video).lights[0]
		check(Vector3(row.position[0],row.position[1],row.position[2]).distance_to(bounds.get_center())<bounds.size.length()*3.,"Initial light is near the selected model")
		editor.undo_button.pressed.emit();await settled();check(Document.document(app.video).lights.is_empty() and app.renderer.scene_lighting.nodes.is_empty(),"Panel Undo removes authored light and runtime")
		editor.redo_button.pressed.emit();await settled();check(Document.document(app.video).lights.size()==1,"Panel Redo restores light")
		editor.refresh();editor.name_field.text="Key light";editor.energy.get_line_edit().text="2.5";editor.color.color=Color(1,.35,.2)
		editor.positions[0].get_line_edit().text="3.25";editor.directions[1].get_line_edit().text="-35";editor.shadows.set_pressed_no_signal(true)
		editor.apply_button.pressed.emit();await settled();row=Document.document(app.video).lights[0]
		check(row.name=="Key light" and row.energy==2.5 and row.position[0]==3.25 and row.rotation_degrees[1]==-35.,"Apply reads typed name, intensity, position and direction")
		check(app.renderer.scene_lighting.nodes[directional].light_color.is_equal_approx(Color(1,.35,.2)),"Color reaches real light")
		editor.enabled.set_pressed(false);check(not app.renderer.scene_lighting.nodes[directional].visible,"Visibility turns light off")
		app.undo();await settled();check(app.renderer.scene_lighting.nodes[directional].visible,"Undo restores visibility")
		editor.add_buttons[1].pressed.emit();var point: String=editor.selected
		editor.distance.get_line_edit().text="9.5";editor.apply_button.pressed.emit()
		check(app.renderer.scene_lighting.nodes[point] is OmniLight3D and app.renderer.scene_lighting.nodes[point].omni_range==9.5,"Point creation and range edit")
		editor.add_buttons[2].pressed.emit();var spot: String=editor.selected
		editor.distance.get_line_edit().text="12";editor.angle.get_line_edit().text="32";editor.apply_button.pressed.emit()
		check(app.renderer.scene_lighting.nodes[spot] is SpotLight3D and app.renderer.scene_lighting.nodes[spot].spot_range==12. and app.renderer.scene_lighting.nodes[spot].spot_angle==32.,"Spot creation, range and angle edits")
		editor.list.item_selected.emit(0);check(editor.selected==directional and editor.name_field.text=="Key light","Light list changes selected controls")
		editor.remove_button.pressed.emit();check(not app.renderer.scene_lighting.nodes.has(directional),"Remove selected light")
		app.undo();await settled();check(app.renderer.scene_lighting.nodes.has(directional),"Undo removal restores directional light")
		editor.refresh();var count: int=Document.document(app.video).lights.size();editor.add_preset("warm_cool")
		check(Document.document(app.video).lights.size()==count+2,"Preset adds editable key and fill")
		app.undo();await settled();check(Document.document(app.video).lights.size()==count,"Preset Undo is atomic")
		editor.refresh();editor.ambient.get_line_edit().text="0.15";editor.ambient_color.color=Color(.6,.8,1.);editor.apply_fill()
		app.change_lighting(1);await settled()
		check(is_equal_approx(app.renderer.world_environment.environment.ambient_light_energy,.15),"Explicit ambient fill applies in Lit")
		app.change_lighting(2);await settled();check(app.renderer.studio_light.visible and app.renderer.world_environment.environment.ambient_light_color==Color("d2e2f2"),"Studio restores legacy ambient color and lamp")
		app.change_lighting(1);await settled()
		check(app.renderer.world_state()==world and app.keys==keys and app.renderer.view_state()==view and imported.light_energy==0.,"Light edits preserve world, shot, navigation and imported light")
		var material: Material=actor.opacity_materials.authored_material(actor.opacity_materials.meshes[0],0)
		check(material is BaseMaterial3D and material.shading_mode!=BaseMaterial3D.SHADING_MODE_UNSHADED,"Imported model remains authored lit material")
		var original_mode: int=material.shading_mode;material.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
		editor.refresh();check("unlit surfaces cannot receive" in editor.hint.text,"Unlit material has an actionable limitation")
		material.shading_mode=original_mode
		var data:=Document.empty();var sun:=Document.create("directional",Vector3(0,1,0),3.);sun.rotation_degrees=[-45.,-35.,0.];data.lights=[sun];editor.commit(data,"Fixture lighting")
		editor.refresh()
		var bad: Dictionary=app.video.duplicate(true);bad.scene_lighting.lights[0].range=-1
		check(not Storage.save_project(folder.path_join("bad-"+theme),bad,app.keys,app.layers,"",0,{}, {},{},false,world).is_empty() and not FileAccess.file_exists(folder.path_join("bad-"+theme+"/project.json")),"Invalid light refuses project save before manifest write")
		if graphics:await pixels(app,editor,theme,model_id,environment_id)
		editor.refresh();count=Document.document(app.video).lights.size();editor.add_preset("soft_character")
		check(Document.document(app.video).lights.size()==count+2,"Soft character preset adds two editable directional lights")
		app.undo();await settled();editor.refresh()
		editor.reflection_enabled.set_pressed_no_signal(true)
		for axis in range(3):
			editor.reflection_positions[axis].get_line_edit().text=str([0.,3.,2.][axis])
			editor.reflection_sizes[axis].get_line_edit().text="20"
		editor.reflection_strength.get_line_edit().text="1";editor.apply_reflection();await settled()
		check(app.renderer.scene_lighting.reflection is ReflectionProbe and app.renderer.scene_lighting.reflection.update_mode==ReflectionProbe.UPDATE_ALWAYS,"Live room cubemap creates actual reflection probe")
		check(app.renderer.scene_lighting.reflection.ambient_mode==ReflectionProbe.AMBIENT_DISABLED and app.renderer.scene_lighting.reflection.cull_mask & ((1<<18)|(1<<19))==0,"Reflections exclude editor copies and add no hidden ambient light")
		if graphics:
			for warmup in range(8):await settled()
			var reflected: Image=await app.renderer.capture(app.keys,[],0,true)
			editor.reflection_enabled.set_pressed_no_signal(false);editor.apply_reflection();await settled()
			var plain: Image=await app.renderer.capture(app.keys,[],0,true)
			var reflection_delta:=difference(reflected,plain);measurements[theme].reflection_difference=reflection_delta
			check(reflection_delta>100,"Room cubemap visibly affects authored reflective material")
			reflected.save_png(folder.path_join(theme+"-reflections.png"))
			app.undo();await settled()
		app.undo();await settled();check(app.renderer.scene_lighting.reflection==null,"Undo removes room reflections")
		app.redo();await settled();check(app.renderer.scene_lighting.reflection!=null,"Redo restores room reflections")
		var saved:=Document.document(app.video).duplicate(true)
		for kind in ["point","spot"]:
			var extra:=Document.create(kind,Vector3(0,1,0));extra.visible=false;saved.lights.append(extra)
		editor.commit(saved,"Save all three light types")
		var expected: Dictionary=Document.document(app.video).duplicate(true)
		if not graphics:
			var directory:=folder.path_join(theme+"-snapshot")
			check(Storage.save_project(directory,app.video,app.keys,app.layers,"",0,{}, {},{},false,app.renderer.world_state()).is_empty(),"Actual Storage writes all light types")
			write_json(folder.path_join(theme+"-expected.json"),{"lighting":expected})
			app.new_project();var loaded:=Storage.load_project(directory)
			check(not loaded.has("error") and app.install_project_data(loaded,directory),"Actual app installs directory project reopening")
			check(saved_equal(Document.document(app.video),expected) and app.renderer.scene_lighting.nodes.size()==3,"Reopened data and runtime retain directional, point and spot lights")
			app.set_advanced(true);editor.open();check(editor.launch.is_visible_in_tree(),"Advanced keeps the Lights entry point")
			app.free();await process_frame;continue
		var path:=folder.path_join(theme+".has");app.has_project.save_file(path,"packed");await wait_job(app.has_project)
		check(FileAccess.file_exists(path),"Packed authored-light project saved")
		app.new_project();app.has_project.open_file(path);await wait_job(app.has_project)
		check(saved_equal(Document.document(app.video),expected) and app.renderer.scene_lighting.nodes.size()==expected.lights.size(),"Saved project reopens with authored lights")
		if graphics and theme=="neon":
			var preview: Image=await app.renderer.capture(app.keys,[],0,true)
			preview.save_png(folder.path_join("reopen-preview.png"))
			var why: String=await app.export_movie(folder)
			check(why.is_empty(),"Actual 48-frame movie export succeeds")
			if why.is_empty():
				var frame:=Image.load_from_file(app.last_export_folder.path_join("frame_000001.png"))
				check(preview.get_data()==frame.get_data(),"Export frame exactly matches reopened authored-light preview")
				measurements.movie=app.last_export_folder.path_join("movie.mp4")
			write_json(folder.path_join("expected.json"),{"lighting":expected,"sha256":preview.get_data().hex_encode().sha256_text()})
		app.set_advanced(true);editor.open();check(editor.launch.is_visible_in_tree(),"Advanced keeps the Lights entry point")
		app.free();await process_frame
	if graphics and FileAccess.file_exists(folder.path_join("native-inputs.json")):await native_pixels()
	finish("writer")
func native_pixels() -> void:
	var inputs: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("native-inputs.json")))
	for kind in inputs:
		var app=await make_app("neon");var path: String=inputs[kind];var original:=FileAccess.get_sha256(path)
		var why: String=app.load_scene(path) if kind=="environment" else app.pose_editor.add_model(path)
		check(why.is_empty(),"Prepared native "+kind+" imports through ordinary workflow")
		if not why.is_empty():app.free();continue
		var actor=app.renderer.active_model();var data: Dictionary=actor.data.duplicate(true)
		app.renderer.frame_scene(actor.root)
		var camera: Camera3D=app.renderer.camera
		var key:=Timeline.key(0,camera.position,camera.quaternion,camera.fov);key.near=camera.near;key.far=camera.far;app.keys=[key]
		app.change_lighting(1);app.scene_lighting_editor.open()
		var dark: Image=await app.renderer.capture(app.keys,[],0,true)
		app.scene_lighting_editor.add_light("directional")
		var lit: Image=await app.renderer.capture(app.keys,[],0,true);var gain:=difference(dark,lit)
		measurements["native_"+kind]={"pixel_difference":gain,"material_limits":Runtime.material_limits(app.renderer)}
		check(gain>100,"Authored directional visibly illuminates prepared native "+kind)
		lit.save_png(folder.path_join("native-"+kind+"-lit.png"))
		check(actor.data==data and FileAccess.get_sha256(path)==original,"Native "+kind+" data and prepared source remain unchanged")
		app.free();await process_frame
func pixels(app,editor: Node,theme: String,model_id: String,environment_id: String) -> void:
	var data:=Document.document(app.video).duplicate(true);data.lights[0].visible=false;editor.commit(data,"Dark control")
	var dark: Image=await app.renderer.capture(app.keys,[],0,true)
	var camera: Camera3D=app.renderer.camera
	var model_point:=camera.unproject_position(Vector3(0,1.4,.5));var wall_point:=camera.unproject_position(Vector3(-2,2,-2.85))
	data.lights[0].visible=true;editor.commit(data,"Directional on")
	var lit: Image=await app.renderer.capture(app.keys,[],0,true);lit.save_png(folder.path_join(theme+"-directional.png"))
	var model_energy:=sum_region(lit,model_point).length()-sum_region(dark,model_point).length()
	var environment_energy:=sum_region(lit,wall_point).length()-sum_region(dark,wall_point).length()
	measurements[theme]={"model_light_gain":model_energy,"environment_light_gain":environment_energy}
	check(model_energy>10 and environment_energy>10,"Visible directional illumination reaches imported model AND environment")
	data.lights[0].shadows=false;editor.commit(data,"Shadows off")
	var no_shadow: Image=await app.renderer.capture(app.keys,[],0,true)
	var shadow_delta:=difference(lit,no_shadow);measurements[theme].shadow_difference=shadow_delta
	check(shadow_delta>100,"Shadow toggle changes actual rendered pixels")
	for kind in ["point","spot"]:
		var row:=Document.create(kind,Vector3(0,1,0),3.);row.energy=3.;data.lights=[row];editor.commit(data,kind)
		var picture: Image=await app.renderer.capture(app.keys,[],0,true)
		check(sum_region(picture,model_point).length()>sum_region(dark,model_point).length()+10 and sum_region(picture,wall_point).length()>sum_region(dark,wall_point).length()+10,"Visible "+kind+" light reaches imported model and environment")
		if kind=="spot":
			data.lights[0].rotation_degrees=[80.,0.,0.];editor.commit(data,"Aim away")
			var away: Image=await app.renderer.capture(app.keys,[],0,true)
			check(difference(picture,away)>100,"Spot direction changes illumination")
	data.lights=[Document.create("directional",Vector3(0,1,0),3.)];data.lights[0].rotation_degrees=[-45.,-35.,0.];data.lights[0].color=[1.,.25,.1];editor.commit(data,"Warm light")
	var red: Image=await app.renderer.capture(app.keys,[],0,true);var rgb:=sum_region(red,model_point)
	check(rgb.x>rgb.z*1.2,"Light color visibly changes imported model")
	data.lights[0].energy=0.;editor.commit(data,"Zero intensity")
	var zero: Image=await app.renderer.capture(app.keys,[],0,true)
	check(sum_region(zero,model_point).length()<sum_region(red,model_point).length()*.1,"Intensity controls visible light")
	data.lights[0].energy=1.;data.lights[0].color=[1.,1.,1.];editor.commit(data,"Export lighting")
	app.change_lighting(0);var flat: Image=await app.renderer.capture(app.keys,[],0,true)
	data.lights[0].visible=false;editor.commit(data,"Hidden in flat")
	check((await app.renderer.capture(app.keys,[],0,true)).get_data()==flat.get_data(),"Unshaded retains exact pixels independently of authored lights")
	data.lights[0].visible=true;editor.commit(data,"Restore");app.change_lighting(1)
	check(app.renderer.world_runtime.instances.has(model_id) and app.renderer.world_runtime.instances.has(environment_id),"Separate imported instances remain installed")
func cold_read() -> void:
	if not graphics:
		for theme in ["neon","light"]:
			var reader=await make_app(theme)
			for storage in ["packed","linked"]:
				var directory:=folder.path_join(theme+"-"+storage+"-unpacked")
				var loaded:=Storage.load_project(directory)
				check(not loaded.has("error") and reader.install_project_data(loaded,directory),"Fresh process installs "+theme+" "+storage+" HAS")
				var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join(theme+"-expected.json")))
				check(saved_equal(Document.document(reader.video),expected.lighting) and reader.renderer.scene_lighting.nodes.size()==3,"All three light types match saved values after "+storage+" reopening")
				var editor: Node=reader.scene_lighting_editor;editor.open();editor.add_light("point")
				check(Document.document(reader.video).lights.size()==4,"Cold reopened lights remain editable")
				reader.undo();await settled();check(saved_equal(Document.document(reader.video),expected.lighting),"Cold reopened edit Undo preserves saved lights")
			reader.free();await process_frame
		finish("reader");return
	var app=await make_app("light")
	app.has_project.open_file(folder.path_join("neon.has"));await wait_job(app.has_project)
	var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
	check(saved_equal(Document.document(app.video),expected.lighting),"Fresh process loads packed authored lights")
	var image: Image=await app.renderer.capture(app.keys,[],0,true)
	check(image.get_data().hex_encode().sha256_text()==expected.sha256,"Fresh process reproduces exact lit pixels")
	app.scene_lighting_editor.open();app.scene_lighting_editor.add_light("point")
	check(Document.document(app.video).lights.size()==expected.lighting.lights.size()+1,"Reopened lights remain editable")
	app.undo();await settled();check(saved_equal(Document.document(app.video),expected.lighting),"Reopened light edit Undo preserves saved lights")
	app.free();await process_frame;finish("reader")
func finish(phase: String) -> void:
	var result:={"checks":checks,"failures":failures,"graphics":graphics,"phase":phase,"measurements":measurements}
	write_json(folder.path_join(phase+"-result.json"),result);print("SCENE_LIGHTING "+JSON.stringify(result));quit(0 if failures==0 else 1)
