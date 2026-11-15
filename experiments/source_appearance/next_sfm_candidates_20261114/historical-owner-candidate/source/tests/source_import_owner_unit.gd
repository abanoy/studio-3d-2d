extends SceneTree
## Authored actual-process ownership boundaries. No native assets or converter.
const Importer = preload("res://src/source_import.gd")
var checks := 0
var failures := 0
var cases: Array = []

class PoseDouble extends RefCounted:
	var additions: Array = []
	func finish_drag() -> void: pass
	func add_model(path: String, frame: int, placement: Dictionary) -> String:
		additions.append({"path":path,"frame":frame,"placement":placement.duplicate(true)});return ""

class RendererDouble extends RefCounted:
	func active_model():return null

class AppDouble extends Control:
	var exporting := false
	var height_review = null
	var pose_editor := PoseDouble.new()
	var renderer := RendererDouble.new()
	var messages: Array = []
	var document := {"world":{"actors":[{"id":"peer","pose":[1,2,3]}]},"history":["existing"],"dirty":true}
	func stop() -> void: pass
	func finish_stroke() -> void: pass
	func release_mouse() -> void: pass
	func message(text: String) -> void:messages.append(text)
	func label(parent: Node, text: String) -> Label:
		var node:=Label.new();node.text=text;parent.add_child(node);return node
	func button(parent: Node, text: String, action: Callable) -> Button:
		var node:=Button.new();node.text=text;node.pressed.connect(action);parent.add_child(node);return node

class ImportDouble extends Importer:
	var fixture_mode := "normal"
	var bypass_creator := false
	var fail_spawn := false
	var audit := {"release_calls":0,"cached_exit_at_release":[],"release_returns":[]}
	func child_arguments() -> PackedStringArray:
		return PackedStringArray([ProjectSettings.globalize_path("res://tests/source_import_owner_worker.py"),"--status-file",result_path,"--cancel-file",cancel_path,"--gate-file",folder+"-gate","--folder",folder,"--mode",fixture_mode])
	func _spawn_preparation(_args: PackedStringArray) -> int:
		if fail_spawn:return -1
		if bypass_creator:return OS.create_process(python(),child_arguments(),false)
		return super._spawn_preparation(child_arguments())
	func _release_preparation_map_entry(owned: int) -> Error:
		audit.release_calls+=1;audit.cached_exit_at_release.append(OS.get_process_exit_code(owned))
		var result: Error=super._release_preparation_map_entry(owned)
		audit.release_returns.append(result);return result

func _initialize() -> void:
	create_timer(35).timeout.connect(func():push_error("Source import owner fixture watchdog expired");quit(2))
	call_deferred("run")

func check(ok: bool, message: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+message)
	if not ok:failures+=1

func touch(path: String) -> void:
	var file:=FileAccess.open(path,FileAccess.WRITE)
	if file:file.store_string("owned fixture gate");file.close()

func wait_child(owned: int) -> bool:
	var until:=Time.get_ticks_msec()+8000
	while OS.is_process_running(owned) and Time.get_ticks_msec()<until:await process_frame
	return not OS.is_process_running(owned)

func make_pair(mode: String) -> Array:
	var app:=AppDouble.new();root.add_child(app)
	var importer:=ImportDouble.new();importer.fixture_mode=mode;importer.app=app
	app.add_child(importer);importer.set_process(false)
	return [app,importer]

func cleanup_failed_fixture(importer: ImportDouble, owned: int) -> void:
	# This failure-only cleanup owns an authored Python process with no children.
	# Clear component reservation before cleanup, and never call generic fallback.
	importer._preparation_map_reserved=false;importer._preparation_map_pid=-1;importer.pid=-1
	if OS.is_process_running(owned) or OS.get_process_exit_code(owned)>=0:OS.kill(owned)

func completed_case(mode: String, bypass := false, teardown := false) -> void:
	var pair:=make_pair(mode);var app: AppDouble=pair[0];var importer: ImportDouble=pair[1]
	importer.bypass_creator=bypass
	var document: Dictionary=app.document.duplicate(true);var start_checks:=checks;var start_failures:=failures
	importer.launch("authored-owner-status.mdl","",true,1.0,"",null,"","Y",17,{"authored":true})
	var owned:=importer.pid;var output_folder:=importer.folder;var external_audit: Dictionary=importer.audit
	check(owned>0,"authored "+mode+" actual child starts")
	if owned<=0:app.free();return
	check(importer._preparation_map_reserved==(not bypass) and importer._preparation_map_pid==(-1 if bypass else owned),"only actual base creator reserves its mapped child: "+mode)
	importer._release_completed_preparation()
	check(OS.is_process_running(owned) and external_audit.release_calls==0,"completion helper leaves a live gated preparer untouched: "+mode)
	if mode=="cancel":importer.cancel()
	else:touch(importer.folder+"-gate")
	var ended: bool=await wait_child(owned)
	if not ended:
		check(false,"authored child reaches terminal state: "+mode);cleanup_failed_fixture(importer,owned);app.free();return
	var expected_exit:=0 if mode=="normal" else (2 if mode=="cancel" else 1)
	check(OS.get_process_exit_code(owned)==expected_exit and not OS.is_process_running(owned) and OS.get_process_exit_code(owned)==expected_exit,"completed exit remains cached before owner release: "+mode)
	if teardown:
		app.free()
		check(external_audit.release_calls==1 and external_audit.cached_exit_at_release==[expected_exit] and OS.get_process_exit_code(owned)==-1,"completed teardown consumes the exact map entry once")
	else:
		importer._process(0.0)
		if bypass:
			check(external_audit.release_calls==0 and OS.get_process_exit_code(owned)==expected_exit,"mock override without reservation does not consume a test-owned map entry")
		else:
			check(external_audit.release_calls==1 and external_audit.cached_exit_at_release==[expected_exit] and OS.get_process_exit_code(owned)==-1,"terminal polling releases mapped HANDLE entry before dropping PID: "+mode)
		check(importer.pid==-1 and not importer._preparation_map_reserved and importer._preparation_map_pid==-1,"terminal component has no stale reservation: "+mode)
		check(app.pose_editor.additions.size()==(1 if mode=="normal" else 0) and app.document==document,"existing completion/refusal/cancel adoption contract is unchanged: "+mode)
		importer._process(0.0);importer._release_completed_preparation();importer._release_completed_preparation()
		check(external_audit.release_calls==(0 if bypass else 1),"repeated polling/helper calls cannot retry a consumed reservation: "+mode)
		if bypass:
			# This child was authored/created by this test override, not base owner.
			# Its cached code proves it is still mapped before one test-owner release.
			if OS.get_process_exit_code(owned)>=0:OS.kill(owned)
			check(OS.get_process_exit_code(owned)==-1,"test cleans its own unreserved-child negative control")
		app.free()
		check(external_audit.release_calls==(0 if bypass else 1),"completed node teardown does not release twice: "+mode)
	cases.append({"mode":mode,"owned_pid":owned,"folder":output_folder,"expected_exit":expected_exit,"bypass_base_creator":bypass,"completed_teardown":teardown,"checks":checks-start_checks,"failures":failures-start_failures,"release_audit":external_audit.duplicate(true)})

func run() -> void:
	if OS.get_name()!="Windows" or str(Engine.get_version_info().get("hash",""))!="89cea143987d564363e15d207438530651d943ac" or OS.get_environment("HYBRID_PYTHON").is_empty():
		push_error("This unrun fixture requires pinned Windows Godot and explicit approved HYBRID_PYTHON");quit(2);return
	var source:=ProjectSettings.globalize_path("res://src/source_import.gd");var before:=FileAccess.get_sha256(source)
	for mode in ["normal","refusal","cancel"]:await completed_case(mode)
	await completed_case("normal",true)
	await completed_case("normal",false,true)
	var pair:=make_pair("normal");var app: AppDouble=pair[0];var importer: ImportDouble=pair[1]
	importer.fail_spawn=true;importer.launch("authored-owner-status.mdl","",true,1.0)
	importer._process(0.0);importer._release_completed_preparation()
	check(importer.pid==-1 and not importer._preparation_map_reserved and importer._preparation_map_pid==-1 and importer.audit.release_calls==0,"failed mock spawn never claims or releases a map entry")
	app.free();await process_frame
	check(FileAccess.get_sha256(source)==before,"ownership fixture leaves production source bytes unchanged")
	print("SOURCE_IMPORT_OWNER "+JSON.stringify({"checks":checks,"failures":failures,"cases":cases,"source_sha256":before,"authored_single_process_Python_only":true,"native_converter_or_GPU":false}))
	quit(0 if failures==0 else 1)
