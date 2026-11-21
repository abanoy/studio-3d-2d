extends "res://tests/posed_bounds_app_headless.gd"
const Lights=preload("res://src/scene_lighting_document.gd")
const Lighting=preload("res://src/lighting.gd")

func fixture(path: String,second: bool) -> bool:
	var scene:=Node3D.new();var mesh:=MeshInstance3D.new();mesh.mesh=BoxMesh.new()
	mesh.position=Vector3(0,1,0);mesh.scale=Vector3(.75,1.5,.75) if second else Vector3.ONE
	scene.add_child(mesh);mesh.owner=scene
	var doc:=GLTFDocument.new();var state:=GLTFState.new()
	var okay: bool=doc.append_from_scene(scene,state)==OK and doc.write_to_filesystem(state,path)==OK
	scene.free();return okay

func choose(bridge: Node,path: String) -> bool:
	bridge.open();await settle()
	var panel: Node=bridge.window.get_meta("discovery_panel")
	panel.tabs.current_tab=0;panel.picker.dir_selected.emit(path.get_base_dir())
	while panel.local.loading:await process_frame
	await settle()
	var item: TreeItem=panel.tree.get_root().get_first_child()
	while item and str(item.get_metadata(0).path).replace("\\","/").simplify_path().to_lower()!=path.replace("\\","/").simplify_path().to_lower():item=item.get_next()
	if item==null:
		printerr("DISCOVERY_INTERACTION_DIAGNOSTIC "+JSON.stringify({"path":path,"scan":panel.local.message,"rows":panel.local.rows,"visible":panel.visible_rows}))
		return false
	item.select(0);panel.tree.item_selected.emit();await settle()
	panel.use_button.pressed.emit();await settle();await settle()
	return true

func screenshot(folder: String,leaf: String) -> bool:
	if DisplayServer.get_name()=="headless":return app.renderer.native_readbacks==0
	var image: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	return image!=null and image.save_png(folder.path_join(leaf+".png"))==OK and app.renderer.native_readbacks==0

func finish_case(reading: bool) -> void:
	var expected:=7 if reading else 16
	if checks!=expected:push_error("Unexpected interaction check count");quit(2);return
	print(("DISCOVERY_LIGHTING_READ " if reading else "DISCOVERY_LIGHTING_WRITE ")+JSON.stringify({"checks":checks,"failures":failures,"graphics":DisplayServer.get_name()!="headless","theme":"classic" if "--classic" in OS.get_cmdline_user_args() else "neon"}))
	await shutdown()

func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if args.is_empty():push_error("Owned interaction data required");quit(2);return
	var folder: String=args[0];var reading: bool="--read" in args
	await setup_app(folder)
	app.has_project.cache_root=folder.path_join("reader-cache" if reading else "writer-cache")
	var packed: String=folder.path_join("Discovery lights.has")
	if reading:
		app.has_project.open_file(packed);await wait_project()
		check(app.has_project.path==packed and app.has_project.pid<=0,"fresh process opens ordinary packed interaction project")
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
		var objects: Array=app.current_world().objects
		check(objects.size()==1 and objects[0].sha256==expected.model_sha,"cold project retains first discovered model and no undone second model")
		check(Lights.document(app.video)==expected.lighting,"cold project retains exact authored light settings")
		var id: String=expected.light_id;var lamp: Node=app.renderer.scene_lighting.nodes.get(id)
		check(lamp is OmniLight3D and lamp.light_energy==3.5,"cold authored point light is installed with edited energy")
		check(app.keys==expected.keys,"cold project retains the original camera keys")
		check(Lighting.mode(app.video)=="lit" and not app.renderer.studio_light.visible,"cold project retains Lit mode without injecting a studio lamp")
		check(await screenshot(folder,"reader-lit"),"cold state capture or headless readback balance succeeds")
		await finish_case(true);return
	var first: String=folder.path_join("first.glb");var second: String=folder.path_join("second.glb")
	check(fixture(first,false) and fixture(second,true),"two generated GLBs export without owner assets or conversions")
	var original: Dictionary={first:FileAccess.get_sha256(first),second:FileAccess.get_sha256(second)}
	var key: Dictionary=app.Timeline.key(0,Vector3(0,1,6),Quaternion.IDENTITY,60.)
	key.near=.125;key.far=128.;app.keys=[key];app.set_frame(0)
	var keys: Array=app.keys.duplicate(true);var bridge: Node=app.get_node("AssetDiscoveryBridge")
	bridge.open();await settle()
	check(is_instance_valid(bridge.window) and not bridge.window.get_meta("discovery_panel").online.network_enabled,"real Discover opens offline in the active theme")
	var chosen: bool=await choose(bridge,first)
	check(chosen and not is_instance_valid(bridge.window) and app.current_world().objects.size()==1 and app.source_import.pid<=0,"ordinary discovered GLB import closes browser and installs one model")
	if failures>0:await shutdown();return
	var first_id: String=app.current_world().objects[0].id;var editor: Node=app.scene_lighting_editor
	editor.open();await settle();var history: int=app.history.size();editor.add_buttons[1].pressed.emit();await settle()
	var light_id: String=editor.selected
	check(Lights.document(app.video).lights.size()==1 and app.history.size()==history+1 and app.renderer.scene_lighting.nodes[light_id] is OmniLight3D,"actual Lights control creates a point light as one Undo edit")
	var original_light: Dictionary=Lights.document(app.video).lights[0].duplicate(true)
	app.change_lighting(1);await settle()
	check(Lighting.mode(app.video)=="lit" and app.renderer.scene_lighting.nodes[light_id].visible,"Lit mode uses the authored point light")
	editor.dialog.hide();bridge.open();await settle();var token: Dictionary=bridge.context()
	var before: Dictionary=app.current_world().duplicate(true);var revision: int=app.recovery_revision
	editor.open();await settle();editor.energy.get_line_edit().text="3.5";editor.apply_button.pressed.emit();await settle();editor.dialog.hide()
	var edited: Dictionary=Lights.document(app.video).duplicate(true)
	if app.recovery_revision<=revision or edited.lights[0].energy!=3.5:
		printerr("LIGHT_APPLY_DIAGNOSTIC "+JSON.stringify({"revision_before":revision,"revision_after":app.recovery_revision,"energy":edited.lights[0].energy,"status":app.status.text,"hint":editor.hint.text,"context_matches":editor.context==editor.token(),"blocked":editor.blocked(),"apply_disabled":editor.apply_button.disabled,"typed":editor.energy.get_line_edit().text,"range_text":editor.distance.get_line_edit().text,"range_value":editor.distance.value,"stored_range":edited.lights[0].range,"angle_text":editor.angle.get_line_edit().text,"stored_angle":edited.lights[0].spot_angle}))
	check(app.recovery_revision>revision and edited.lights[0].energy==3.5,"actual light Apply invalidates the earlier browser document context")
	if failures>0:await shutdown();return
	check(edited.lights[0].position==original_light.position and edited.lights[0].rotation_degrees==original_light.rotation_degrees and edited.lights[0].range==original_light.range and edited.lights[0].spot_angle==original_light.spot_angle,"intensity-only Apply preserves exact untouched collapsed geometry and beam settings")
	bridge.accept_local(second,token);await settle()
	check(app.current_world()==before and Lights.document(app.video)==edited and app.status.text.contains("changed"),"stale discovery callback refuses import while retaining the light edit")
	editor.open();editor.placement.show();await settle()
	editor.positions[0].get_line_edit().text="3.25";editor.distance.get_line_edit().text="9.5"
	editor.placement.hide();editor.apply_button.pressed.emit();await settle();editor.dialog.hide()
	edited=Lights.document(app.video).duplicate(true)
	check(edited.lights[0].position[0]==3.25 and edited.lights[0].range==9.5 and edited.lights[0].position[1]==original_light.position[1] and edited.lights[0].position[2]==original_light.position[2],"typed placement and range survive collapsing their section before Apply")
	bridge.window.close_requested.emit();await settle()
	chosen=await choose(bridge,second)
	check(chosen and app.current_world().objects.size()==2 and Lights.document(app.video)==edited,"fresh discovery imports a second model without replacing authored lights")
	if failures>0:await shutdown();return
	check(app.keys==keys,"discovery and light edits preserve authored camera keys")
	app.undo();await settle()
	var objects: Array=app.current_world().objects
	check(objects.size()==1 and objects[0].id==first_id and Lights.document(app.video)==edited,"Undo second import preserves first model and edited light")
	check(FileAccess.get_sha256(first)==original[first] and FileAccess.get_sha256(second)==original[second],"both original generated GLBs remain byte unchanged")
	app.has_project.save_file(packed,"packed");await wait_project()
	check(app.has_project.path==packed and FileAccess.file_exists(packed),"ordinary packed Save completes for discovered model and authored lighting")
	check(app.keys==keys and Lights.document(app.video)==edited and app.renderer.scene_lighting.nodes[light_id].light_energy==3.5,"Save preserves shot keys and live authored point light")
	check(await screenshot(folder,"writer-lit"),"writer state capture or headless readback balance succeeds")
	var output:=FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE)
	output.store_string(JSON.stringify({"model_sha":original[first],"lighting":edited,"keys":keys,"light_id":light_id},"",true,true));output.close()
	await finish_case(false)
