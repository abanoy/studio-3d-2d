extends SceneTree
# Actual SourceImport completion/managed-world route with an already-converted GLB.
# Headless state/API qualification only; no new conversion or pixel qualification.
const Model=preload("res://src/model.gd")
const Importer=preload("res://src/source_import.gd")
const Lighting=preload("res://src/lighting.gd")
var checks: int=0
var failures: int=0
var app
var output: String=""
var case_name: String=""
var completed: bool=false

func _initialize() -> void:
	create_timer(180).timeout.connect(func():push_error("Prepared-map editor watchdog");quit(2))
	call_deferred("run")

func check(ok: bool,label: String) -> bool:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
	return ok

func settle() -> void:
	for i in range(4):await process_frame

func dictionary(path: String,limit: int) -> Dictionary:
	var file:=FileAccess.open(path,FileAccess.READ)
	if file==null or file.get_length()>limit:return {}
	var parsed=JSON.parse_string(file.get_as_text())
	return parsed if parsed is Dictionary else {}

func hashes(files: Dictionary) -> bool:
	for key in ["scene","parameters","entities"]:
		if not files.has(key) or FileAccess.get_sha256(str(files[key].path))!=str(files[key].sha256):return false
	return true

func finite_box(box: AABB) -> bool:
	return box.position.is_finite() and box.size.is_finite() and box.size.length_squared()>0

func geometry(node: Node) -> Dictionary:
	var value: Dictionary={"meshes":0,"surfaces":0,"vertices":0,"materials":true,"lights":0,"point":0,"spot":0,"directional":0,"finite_lights":true,"scripts_absent":true}
	var nodes: Array=[node];nodes.append_array(node.find_children("*","",true,false))
	for child in nodes:
		value.scripts_absent=value.scripts_absent and child.get_script()==null
		if child is MeshInstance3D and child.mesh:
			value.meshes+=1
			for surface in range(child.mesh.get_surface_count()):
				value.surfaces+=1;value.vertices+=child.mesh.surface_get_array_len(surface)
				value.materials=value.materials and child.get_active_material(surface) is BaseMaterial3D
		if child is Light3D:
			value.lights+=1
			if child is OmniLight3D:value.point+=1
			elif child is SpotLight3D:value.spot+=1
			elif child is DirectionalLight3D:value.directional+=1
			var color: Color=child.light_color
			value.finite_lights=value.finite_lights and child.transform.is_finite() and is_finite(child.light_energy) and child.light_energy>=0 and is_finite(color.r) and is_finite(color.g) and is_finite(color.b)
	return value

func finish() -> void:
	if is_instance_valid(app):app.queue_free();app=null;await settle()
	var report: Dictionary={"format":"has_prepared_map_editor_headless_1","case":case_name,"checks":checks,"failures":failures,"actual_current_app_and_SourceImport_completion":completed,"actual_Model_API_used":completed,"conversion_rerun":false,"graphics_executed":false,"artist_appearance_qualified":false,"Full_qualification_claimed":false,"application_source_modified":false}
	if not output.is_empty():
		var file:=FileAccess.open(output.path_join("result.json"),FileAccess.WRITE)
		if file:file.store_string(JSON.stringify(report));file.close()
	print("PREPARED_MAP_EDITOR "+JSON.stringify(report));quit(0 if failures==0 and checks==32 else 1)

func run() -> void:
	var args: PackedStringArray=OS.get_cmdline_user_args()
	if args.size()!=3:push_error("Expected owned config, fresh case output and isolated profile");quit(2);return
	output=ProjectSettings.globalize_path(args[1]).simplify_path()
	var owned: String=ProjectSettings.globalize_path("res://").simplify_path().trim_suffix("/")
	if not output.begins_with(owned+"/output/") or DirAccess.dir_exists_absolute(output):push_error("Fresh owned output required");quit(2);return
	if DirAccess.make_dir_recursive_absolute(output)!=OK:quit(2);return
	var config: Dictionary=dictionary(args[0],32*1024)
	case_name=str(config.get("name",""))
	if not check(DisplayServer.get_name()=="headless" and OS.get_name()=="Windows" and str(Engine.get_version_info().get("hash",""))==Importer.PREPARATION_PROCESS_ENGINE and not args[2].is_empty() and OS.get_user_data_dir().replace("\\","/").ends_with("/"+args[2]) and not config.is_empty(),"exact pinned Windows headless engine and isolated profile/config are admitted"):await finish();return
	var files: Dictionary=config.files;var expected: Dictionary=config.expected
	var path: String=str(files.scene.path)
	if not path.simplify_path().begins_with(owned+"/Assets/") or path.get_file()!="scene.glb" or str(files.parameters.path)!=path.get_base_dir().path_join("parameters.json"):push_error("Owned prepared bundle required");await finish();return
	if not check(hashes(files),"exact existing prepared GLB/report/raw-entity copies match their source pins"):await finish();return
	var parameters: Dictionary=dictionary(str(files.parameters.path),256*1024)
	var glb: PackedByteArray=FileAccess.get_file_as_bytes(path)
	var doc: Dictionary=JSON.parse_string(glb.slice(20,20+glb.decode_u32(12)).get_string_from_utf8())
	var serial_meshes: int=0;var serial_surfaces: int=0;var serial_vertices: int=0;var external: bool=false
	for node in doc.nodes:
		if node.has("mesh"):
			serial_meshes+=1
			for primitive in doc.meshes[int(node.mesh)].primitives:
				serial_surfaces+=1;serial_vertices+=int(doc.accessors[int(primitive.attributes.POSITION)].count)
	for resource in doc.get("buffers",[])+doc.get("images",[]):
		if resource.has("uri") and not str(resource.uri).begins_with("data:"):external=true
	check(serial_meshes==expected.mesh_nodes and serial_surfaces==expected.surfaces and serial_vertices==expected.vertices and not external and doc.get("extensionsRequired",[])==["KHR_lights_punctual"],"serialized geometry is bounded/self-contained and independently matches the retained conversion")
	var omissions: Dictionary=parameters.native_parameters.static_entity_light_omissions
	var sum: int=0
	for field in ["created","invalid","budget","starts_off","animated_style","unsupported_type"]:sum+=int(omissions[field])
	var entities: Array=JSON.parse_string(FileAccess.get_file_as_string(str(files.entities.path)))
	var light_declarations: int=0
	for entity in entities:
		var kind: String=str(entity.get("classname",""))
		if kind=="light" or kind.begins_with("light_") or kind=="env_projectedtexture":light_declarations+=1
	check(sum==int(omissions.light_entities) and light_declarations==sum and entities.size()==expected.raw_entities and omissions==expected.omissions and omissions.raw_entities_preserved==true,"every raw entity-light declaration reconciles to created or explicitly omitted category")
	check(parameters.warnings.size()==expected.warnings and not parameters.limits.is_empty() and parameters.source_sha256==expected.source_sha256 and parameters.native_parameters.static_entity_lights.size()==expected.lights and parameters.counts.static_lights==expected.lights,"full warning/limitation/source identity and supported-light report remain explicit")
	app=load("res://main.tscn").instantiate();app.display_prefs_path=output.path_join("prefs.cfg");app.recovery_root=output.path_join("recovery");app.recent_path=output.path_join("recents.json")
	root.size=Vector2i(1400,900);root.gui_embed_subwindows=true;root.add_child(app);await settle()
	app.autosave_enabled.set_pressed_no_signal(false);app.has_project.cache_root=output.path_join("project-cache")
	check(app.new_project(),"ordinary New creates the isolated current editor world")
	var before_world: Dictionary=app.current_world().duplicate(true);var before_keys: Array=app.keys.duplicate(true);var before_layers: Array=app.layers.duplicate(true);var before_video: Dictionary=app.video.duplicate(true)
	var definition: Dictionary=app.pose_editor.definition(path)
	check(not definition.has("error") and definition.data.metadata.native_parameters==parameters,"actual PoseEditor definition accepts and retains the adjacent full parameter report")
	var importer: Node=app.source_import;importer.set_process(false);importer.folder=path.get_base_dir();importer.result_path=output.path_join("relay-status.json");importer.actor=false;importer.generic=false;importer.native_family="";importer.import_frame=0;importer.cancelled=false
	var relay_spec: String=output.path_join("relay-spec.json")
	var spec:=FileAccess.open(relay_spec,FileAccess.WRITE)
	spec.store_string(JSON.stringify({"glb":path,"sha256":files.scene.sha256,"owned_root":owned}));spec.close()
	var child: int=importer._spawn_preparation(PackedStringArray(["-I","-S","-B",ProjectSettings.globalize_path("res://tools/prepared_map_status_relay.py"),relay_spec,FileAccess.get_sha256(relay_spec),importer.result_path]))
	importer.pid=child
	check(child>0 and importer._preparation_map_pid==child and importer._preparation_map_reserved,"actual SourceImport creator owns a bounded status-relay process, never a converter")
	if child<=0:await finish();return
	var until: int=Time.get_ticks_msec()+15000
	while OS.is_process_running(child) and Time.get_ticks_msec()<until:await process_frame
	var status: Dictionary=dictionary(importer.result_path,4096)
	if not check(not OS.is_process_running(child) and OS.get_process_exit_code(child)==0 and status.get("ok")==true and status.get("prepared_status_replay_only")==true,"owned relay completes with exact pinned prepared GLB status"):await finish();return
	importer._process(0.0);await settle()
	var runtime: RefCounted=app.renderer.world_runtime
	if not check(runtime!=null and runtime.instances.size()==1 and not app.last_import_id.is_empty(),"ordinary SourceImport completion installs exactly one actual world instance"):await finish();return
	completed=true
	check(importer.pid==-1 and not importer._preparation_map_reserved and importer._preparation_map_pid==-1 and OS.get_process_exit_code(child)==-1,"ordinary terminal import consumes its completed process-map entry exactly once")
	var actor: RefCounted=runtime.instance(app.last_import_id)
	var row: Dictionary=actor.data
	check(row.source!=path and str(row.source).begins_with(owned+"/output/imports/") and FileAccess.get_sha256(row.source)==files.scene.sha256,"ordinary app creates a byte-exact managed asset copy inside the owned runtime")
	check(row.metadata.native_parameters==parameters,"installed Model retains all supported fields, omissions, warnings and limitations exactly")
	check(row.metadata.import_source==path and row.metadata.external_bundle==path.get_base_dir() and app.has_project.origins[str(row.source).replace("\\","/")]==path,"actual model/cache provenance points to the owned prepared input without rewriting originals")
	check(actor.get_script()==Model and row.kind=="environment" and actor.root.is_inside_tree(),"actual source-independent Model owns the installed environment")
	var actual: Dictionary=geometry(actor.root)
	check(actual.meshes==expected.mesh_nodes,"actual imported scene has every serialized mesh node")
	check(actual.surfaces==expected.surfaces and actual.vertices==expected.vertices and actual.materials,"actual imported meshes preserve serialized surface/vertex inventory and supported materials")
	check(finite_box(app.renderer.scene_bounds(actor.root)),"actual editor bounds are finite and contain nonempty map geometry")
	check(actual.lights==expected.lights and actual.point==expected.point_lights and actual.spot==expected.spot_lights and actual.directional==expected.directional_lights,"actual installed light types/counts match serialized supported-light inventory")
	check(actual.finite_lights,"installed supported light transforms/colors/energies are finite and nonnegative")
	check(actual.scripts_absent,"native map data installs no entity scripts on imported Nodes")
	var view: Dictionary=parameters.suggested_view
	var target:=Vector3(view.target[0],view.target[1],view.target[2]);var position:=Vector3(view.position[0],view.position[1],view.position[2])
	check(app.renderer.camera.position.is_equal_approx(position) and (-app.renderer.camera.global_basis.z).dot((target-position).normalized())>.99999,"ordinary SourceImport applies the supplied temporary framing view")
	check(app.mode.selected==1 and app.keys==before_keys and app.layers==before_layers and app.video==before_video and Lighting.mode(app.video)=="unshaded","scene setup preserves shot keys/drawings/output settings and default Unshaded mode")
	var warnings: Array=app.find_children("*","AcceptDialog",true,false);var actionable: bool=false
	for dialog in warnings:
		if dialog.title=="Source import warnings" and dialog.dialog_text.contains("parameters.json") and dialog.dialog_text.contains(str(parameters.warnings[0])):actionable=true
	check(actionable and app.status.text.contains("resource warnings"),"ordinary completion exposes actionable supported-profile warnings and the full report path")
	check(not app.physics_editor.is_running() and actor.live_pose==null and actor.live_world_transform==null,"map installation does not start model physics or loose-parts simulation")
	var installed: Dictionary=app.current_world().duplicate(true)
	app.undo();check(app.current_world()==before_world,"one ordinary import Undo removes the installed map")
	app.redo();check(app.current_world()==installed,"ordinary Redo restores exact world and full native metadata")
	actor=app.renderer.world_runtime.instance(app.last_import_id)
	# Redo may clear the convenience selection ID; authoritative serialized ID is retained.
	if actor==null:actor=app.renderer.world_runtime.instance(str(row.id))
	actual=geometry(actor.root)
	check(actual.meshes==expected.mesh_nodes and actual.lights==expected.lights and actor.data.metadata.native_parameters==parameters,"Redo reinstalls actual geometry/lights with unchanged report ownership")
	app.change_lighting(Lighting.MODES.find("lit"));await settle()
	check(Lighting.mode(app.video)=="lit" and not actor.opacity_materials.unshaded and geometry(actor.root).lights==expected.lights,"actual Lit state restores supplied material shading and keeps supported scene lights")
	app.change_lighting(Lighting.MODES.find("unshaded"));await settle()
	check(Lighting.mode(app.video)=="unshaded" and actor.opacity_materials.unshaded and geometry(actor.root).lights==expected.lights,"actual Unshaded state uses temporary flat material copies without removing light data")
	check(app.keys==before_keys and app.layers==before_layers,"lighting and world history author no camera keys or drawing changes")
	check(hashes(files) and FileAccess.get_sha256(row.source)==files.scene.sha256,"all prepared input copies and managed GLB remain byte-exact after install/history/lighting")
	await finish()
