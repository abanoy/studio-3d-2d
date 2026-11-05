extends Node
const Model=preload("res://src/model.gd")
const World=preload("res://src/world_document.gd")
const Storage=preload("res://src/storage.gd")
const Store=preload("res://src/lesson_store.gd")
var app
var folder: String
var mode: String
var checks:=0
var failures:=0
func _ready() -> void:
	get_tree().create_timer(160).timeout.connect(func():push_error("Contact persistence reader watchdog");get_tree().quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settled() -> void:
	for i in range(4):await get_tree().process_frame
	await RenderingServer.frame_post_draw
func json_file(path: String) -> Dictionary:return JSON.parse_string(FileAccess.get_file_as_string(path))
func same(a,b) -> bool:return JSON.parse_string(JSON.stringify(a,"",true,true))==JSON.parse_string(JSON.stringify(b,"",true,true))
func run() -> void:
	var args:=OS.get_cmdline_user_args();folder=args[0];mode=args[1];var writer:=json_file(folder.path_join("writer-result.json"));var expected:=json_file(folder.path_join("expected.json"))
	app=get_parent()
	while app.startup_recovery_result.is_empty():await get_tree().process_frame
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("reader-cache-"+mode);app.home.hide()
	if mode in ["packed","linked"]:
		app.has_project.open_file(writer[mode])
		while app.has_project.pid>0:await get_tree().process_frame
		check(not app.has_project.path.is_empty(),"fresh process opens the ordinary "+mode+" HAS")
	elif mode=="recovery":check(app.startup_recovery_result.get("restored",false) and app.dirty and app.has_project.path.is_empty(),"unmodified normal startup automatically recovers Model7 as an unsaved copy")
	elif mode=="lesson":
		var store:=Store.new();store.root=writer.lesson_root;check(store.load_snapshot(app,"basic-pose","1234","step_01"),"fresh process loads the ordinary lesson checkpoint API")
		check(same(Store.ui(app),expected.lesson_ui) and store.restored_observations.get("preview_seen",false),"lesson snapshot retains exact editor context and observations")
	if not app.renderer.world_runtime or app.renderer.world_runtime.instances.size()!=7:
		check(false,"complete five-native/group/map world exists: "+app.status.text);get_tree().quit(1);return
	await settled();check(same(World.portable(app.current_world()),expected.world),"all portable native/parent/body/contact/visibility data survives "+mode)
	check(same(app.video,expected.video) and same(app.keys,expected.keys) and Storage.image_hash(app.layers[1].cels[0].image)==expected.paint,"camera/video and independent editable RGBA survive "+mode)
	check(app.audio_clip.source.sha256==expected.audio.sha256 and app.audio_clip.start_frame==expected.audio.start_frame and app.audio_clip.gain_db==expected.audio.gain_db,"actual audio bytes and synchronization settings survive "+mode)
	var exact:=true;var errors:=0
	for id in expected.ids:
		var actor: RefCounted=app.renderer.world_runtime.instance(id)
		for half in range(96,-1,-1):
			var pose: Dictionary=actor.sample(float(half)/2);exact=exact and JSON.stringify(pose,"",true,true).sha256_text()==expected.samples[id][half];errors+=0 if actor.evaluation_error.is_empty() else 1
	check(exact and errors==0,"all485 native half-frame poses are exact on reverse seek after "+mode)
	app.set_frame(41);var hidden: RefCounted=app.renderer.world_runtime.instance(expected.ids[-1]);app.world_selection.select_entity(hidden.data.id)
	check(not hidden.root.visible and app.world_selection.selected==hidden.data.id and hidden.evaluation_error.is_empty(),"hidden planted native model remains selected with a valid pose")
	app.set_frame(12);app.world_selection.select_entity(expected.ids[0]);var actor: RefCounted=app.renderer.active_model();var before: Dictionary=actor.data.duplicate(true);var shots: Array=app.keys.duplicate(true)
	app.pose_editor.frame_model();check(actor.data==before and app.keys==shots and actor.evaluation_error.is_empty(),"current-pose framing changes no contact or explicit camera key")
	var actual: Image=await app.renderer.capture(app.keys,app.layers,12,true);var reference:=Image.load_from_file(folder.path_join("reference.png"));reference.convert(Image.FORMAT_RGBA8)
	var a:=actual.get_data();var b:=reference.get_data();var changes:=0;var total:=0.
	for i in range(a.size()):
		if a[i]!=b[i]:changes+=1;total+=absf(float(a[i])-float(b[i]))
	var mean:=total/a.size();actual.save_png(folder.path_join("reader-"+mode+".png"))
	check(changes<=384 and mean<.002,"fresh native scene rebuild retains the established mesh-edge pixel bound: "+mode)
	var movie:=""
	if mode=="packed":
		var error: String=await app.export_movie(folder);movie=app.last_export_folder.path_join("movie.mp4")
		check(error.is_empty() and actual.get_data()==Image.load_from_file(app.last_export_folder.path_join("frame_000013.png")).get_data(),"fresh packed reopen exports exact own preview pixels with synchronized audio")
	var result:={"checks":checks,"failures":failures,"mode":mode,"movie":movie,"changed_channels":changes,"mean_error":mean};var file:=FileAccess.open(folder.path_join("reader-"+mode+".json"),FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close();print("CONTACT_PERSISTENCE_READ "+JSON.stringify(result));get_tree().quit(0 if failures==0 else 1)
