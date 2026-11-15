extends SceneTree
const Helper=preload("res://src/secondary_helper_editor.gd")
class TestApp extends RefCounted:
	var navigating:=false
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:
	var editor:=Helper.new();editor.app=TestApp.new();editor.parts=ItemList.new();editor.include_toggle=CheckButton.new();editor.include_status=Label.new();editor.apply_button=Button.new()
	editor.preview={"can_apply":true};editor.preview_ready=false
	editor.refresh_inclusions()
	check(editor.apply_button.disabled and editor.include_toggle.disabled,"a stale successful preview cannot enable Apply or a new setup check")
	editor.app.navigating=true;editor.refresh_inclusions();editor.app.navigating=false;editor.refresh_inclusions()
	check(editor.apply_button.disabled and editor.include_toggle.disabled,"navigation refresh cannot resurrect rejected single-part eligibility")
	editor.preview_ready=true;editor.refresh_inclusions()
	check(not editor.apply_button.disabled and not editor.include_toggle.disabled,"a matching completed preview restores the original single-part workflow")
	editor.preview_ready=false;editor.included={"other":{"source_keys":["other"],"valid":true,"mode":"weighted"}};editor.refresh_inclusions()
	check(not editor.apply_button.disabled and editor.include_toggle.disabled,"an unqueued failed focus does not invalidate another reviewed checked part")
	editor.included.other.valid=false;editor.refresh_inclusions()
	check(editor.apply_button.disabled and editor.include_status.text.contains("needs review"),"an invalid checked item blocks the entire checked setup")
	editor.parts.free();editor.include_toggle.free();editor.include_status.free();editor.apply_button.free();editor.free()
	var result:={"checks":checks,"failures":failures};print("SECONDARY_BATCH_UNIT "+JSON.stringify(result));quit(0 if failures==0 else 1)
