extends Node
var checks:=0
var failures:=0
func _ready() -> void:
	get_parent().startup_recovery_finished.connect(observe)
	get_tree().create_timer(40).timeout.connect(func():push_error("Home startup watchdog");get_tree().quit(2))
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func observe(result: Dictionary) -> void:
	var app=get_parent();var folder: String=OS.get_cmdline_user_args()[0];var recovered: bool=OS.get_cmdline_user_args()[1]=="recovered"
	for i in range(4):await get_tree().process_frame
	await RenderingServer.frame_post_draw
	check(not result.cancelled and bool(result.restored)==recovered,"normal inherited startup completes recovery before Home choice")
	check(app.home.visible!=recovered,"fresh startup shows Home while valid recovery goes straight to editing")
	check(not app.has_dialog(app),"Home is embedded, with no native splash/focus window")
	var expected=preload("res://src/recovery.gd").read_json(folder.path_join("expected.json"))
	check(FileAccess.get_sha256(app.recent_path)==expected.recents_sha256 and app.home.store.read().size()==expected.rows,"startup/recovery never rewrites recent-project preferences")
	check(FileAccess.get_sha256(expected.manual)==expected.manual_sha256 and FileAccess.get_sha256(expected.fixture)==expected.fixture_sha256,"fresh startup preserves manual HAS and original geometry")
	if recovered:check(app.dirty and app.frame==12 and app.has_project.path.is_empty(),"recovered work stays unsaved at its original frame")
	else:check(not app.dirty and app.renderer.world_runtime.instances.is_empty(),"Home covers a clean empty New world")
	var file:=FileAccess.open(folder.path_join("startup-"+str(OS.get_cmdline_user_args()[1])+".json"),FileAccess.WRITE);file.store_string(JSON.stringify({"checks":checks,"failures":failures}));file.close()
	print("HOME_STARTUP "+JSON.stringify({"checks":checks,"failures":failures}));get_tree().quit(0 if failures==0 else 1)
