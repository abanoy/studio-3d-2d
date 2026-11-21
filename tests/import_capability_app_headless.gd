extends SceneTree
# Source-only authored actual-app controls. No native import or rendering required.
const Model=preload("res://src/model.gd")
const Summary=preload("res://src/import_capability_summary.gd")
var app
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(120).timeout.connect(func():push_error("Import info app watchdog");quit(2));call_deferred("run")
func check(value: bool,label: String) -> void:
	checks+=1;if not value:failures+=1
	print(("PASS " if value else "FAIL ")+label)
func settle() -> void:
	for i in range(4):await process_frame
func report_fixture() -> Dictionary:
	# Parse once like parameters.json, so numeric provenance is in its real JSON domain.
	return JSON.parse_string(JSON.stringify({"adapter":"studio_source_1","warnings":["Unknown fixture warning stays visible"],"limits":["Unknown fixture material feature stays unsupported"],"counts":{"bones":0},"materials":[{"name":"fixture-material","status":"fallback gray"}],"native_parameters":{"static_brush_lightmaps":{"faces":29},"static_entity_lights":[{"kind":"point"}],"static_entity_light_omissions":{"invalid":1,"budget":42,"starts_off":6,"animated_style":31,"unsupported_type":2,"raw_entities_preserved":true}}}))
func setup_app(folder: String) -> void:
	var prefs:=ConfigFile.new();prefs.set_value("display","theme","light" if "--classic" in OS.get_cmdline_user_args() else "neon");prefs.set_value("display","percent",150 if "--150" in OS.get_cmdline_user_args() else 100);prefs.save(folder.path_join("prefs.cfg"))
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json")
	root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	app.set_advanced("--advanced" in OS.get_cmdline_user_args());await settle()
func select_first() -> RefCounted:
	var id: String=app.renderer.world_runtime.order[0]
	app.world_selection.select_entity(id,false)
	return app.renderer.active_model()
func wait_job() -> void:
	while app.has_project.pid>0:await process_frame
	await settle()
func shutdown() -> void:
	await app.quit_studio();quit(0 if failures==0 else 1)
func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if args.is_empty() or DisplayServer.get_name()!="headless":push_error("Use headless script with a new owned data folder");quit(2);return
	var folder: String=args[0]
	await setup_app(folder)
	var loaded: bool=app.load_demo_room()
	if loaded:loaded=app.restore_world(app.current_world()).is_empty()
	check(loaded,"actual Studio loads repository sample into ordinary World without a native worker")
	var actor: RefCounted=select_first();var info=app.pose_editor.import_capabilities
	actor.data.metadata.native_parameters=report_fixture();app.changed();info._process(0.)
	var report: Dictionary=info.report_for(actor);var raw_report: PackedByteArray=var_to_bytes(report)
	var world: Dictionary=app.current_world().duplicate(true);var keys: Array=app.keys.duplicate(true);var history: int=app.history.size()
	check(info.button.text=="Import info" and info.buttons.size()==2,"actual Pose and World actions are installed exactly once")
	check(info.button.visible and not info.button.disabled and info.buttons[1].visible,"actual selected environment offers report in Simple and Advanced")
	var summary: Dictionary=Summary.summarize(report,actor)
	check(Summary.plain_text(summary).contains("Unknown fixture material") and Summary.plain_text(summary).contains("Unknown fixture warning"),"actual report retains unknown limits and warnings")
	check(Summary.plain_text(summary).contains("budget): 42") and Summary.plain_text(summary).contains("animated style): 31") and not summary.actions.is_empty(),"actual map report exposes specific omissions and dependency actions")
	check(not summary.native_motion.supported,"fixture counts cannot manufacture native motion capability")
	info.open(false)
	check(is_instance_valid(info.window) and info.window.title=="Import info" and not info.window.unresizable and info.matches(),"actual headless widget owns resizable read-only report without a native popup")
	check(info.summary_text.text.contains("29 surfaces") and info.summary_text.text.contains("global limit"),"actual text includes retained compatible lightmaps and actionable omissions")
	info.notify_import(report)
	check(is_instance_valid(info.window) and not info.window.exclusive and app.status.text.contains("Import info"),"ordinary import notification is informational and does not create a modal")
	check(var_to_bytes(actor.data.metadata.native_parameters)==raw_report and app.current_world()==world and app.keys==keys and app.history.size()==history,"opening and notifying preserve raw provenance world keys and Undo")
	var actor_id: String=actor.data.id;var source: String=actor.data.source
	check(app.pose_editor.add_model(source).is_empty(),"second ordinary GLB object can be added without conversion")
	info._process(0.)
	check(info.window==null,"selection/replacement after adding another object closes old report")
	actor=app.renderer.active_model();actor.data.metadata.native_parameters={"kind":"vrm_preparation","warnings":["Second actor only"]}
	info.open(false)
	check(info.summary_text.text.contains("Second actor only") and not info.summary_text.text.contains("budget): 42"),"new selection cannot borrow previous model or map report")
	actor.data.metadata.native_parameters.warnings.append("Changed later");info._process(0.)
	check(info.window==null,"in-place persistent report changes invalidate the open summary")
	info.open(false);var digest: String=actor.data.sha256;actor.data.sha256="0".repeat(64);info._process(0.);actor.data.sha256=digest
	check(info.window==null,"source identity change invalidates open summary before any frame evaluation")
	info.open(false);var session: String=app.recovery_session;app.recovery_session=session+"other";info._process(0.);app.recovery_session=session
	check(info.window==null,"same objects in a new project session cannot retain an old report")
	info.open(false);var owner: String=app.sequence_editor.active_owner;app.sequence_editor.active_owner=owner+"other";info._process(0.);app.sequence_editor.active_owner=owner
	check(info.window==null,"sequence owner changes invalidate open report even with matching object IDs")
	info.open(false);app.exporting=true;info._process(0.);app.exporting=false
	check(info.window==null and info.button.disabled,"export closes and disables report inspection")
	info._process(0.);info.open(false);app.playing=true;info._process(0.);app.playing=false
	check(info.window==null and info.button.disabled,"playback closes and disables report inspection")
	info._process(0.);info.open(false);var pid: int=app.source_import.pid;app.source_import.pid=999999999;info._process(0.);app.source_import.pid=pid
	check(info.window==null and info.button.disabled,"preparation busy flag blocks inspection without starting a worker")
	info._process(0.);info.open(false);pid=app.has_project.pid;app.has_project.pid=999999999;info._process(0.);app.has_project.pid=pid
	check(info.window==null and info.button.disabled,"save/open busy flag blocks inspection without starting a process")
	info._process(0.);info.open(false);app.world_selection.select_entity("",false);info._process(0.)
	check(info.window==null and not info.button.visible,"deselection closes the report and hides both actions")
	app.world_selection.select_entity(actor.data.id,false);info._process(0.);info.notify_import(report)
	check(actor.data.metadata.native_parameters.warnings.has("Second actor only") and not actor.data.metadata.native_parameters.has("adapter"),"asynchronous notification never changes or borrows selected actor provenance")
	app.source_import.request_context=app.source_import.import_context()
	check(app.source_import.completion_matches(),"actual importer binds completion to current project session and sequence")
	app.recovery_session=session+"other"
	check(not app.source_import.completion_matches(),"completed preparation from an older session cannot be installed")
	app.recovery_session=session;app.sequence_editor.active_owner=owner+"other"
	check(not app.source_import.completion_matches(),"completed preparation from another sequence cannot be installed")
	app.sequence_editor.active_owner=owner;app.world_selection.select_entity(actor_id,false)
	check(app.source_import.completion_matches(),"selection changes inside the same owner do not redirect or cancel append intent")
	app.source_import.request_context={}
	check(not app.source_import.completion_matches(),"unbound result cannot install into the current document")
	info.open(false);app.new_project();await settle();info._process(0.)
	check(info.window==null and not info.button.visible,"actual New clears old source report with the old object graph")
	var rail_count: int=app.world_selection.actions.size();info.free();app.world_selection.refresh_actions()
	check(app.world_selection.actions.size()==rail_count-1,"controller teardown removes its World action before later rail refresh")
	print("IMPORT_CAPABILITY_APP "+JSON.stringify({"checks":checks,"failures":failures,"actual_app":true,"headless":true,"user_profile":OS.get_user_data_dir(),"native_worker_started":false,"graphics_qualified":false,"application_adopted":false}))
	await shutdown()
