extends SceneTree
# Generated rows and controlled callbacks only: no model, worker, GPU or save.
const Core = preload("res://src/loose_part_selection.gd")
const Selector = preload("res://src/loose_part_selector.gd")
var failures := 0
var checks := 0

class Editor extends Node:
	var app := {"recovery_revision":7,"playing":false,"exporting":false,"navigating":false}
	var revision := 7
	var pid := -1
	var window: Window
	var included: Dictionary = {}
	var selected_key := ""
	var keys: Array = ["a","b","c","d"]
	var part_names: Array = ["A","B","C","D"]
	var info := Label.new()
	var fields: Array = []
	var anchors := OptionButton.new()
	var existing_toggle := CheckButton.new()
	var patch_toggle := CheckButton.new()
	var include_toggle := CheckButton.new()
	var apply_button := Button.new()
	var selected_calls: Array = []
	var include_calls := 0
	var refresh_calls := 0
	var wind_stops := 0
	var asset_apply_calls := 0
	var preview_launch_fails := false
	var review_launch_fails := false
	var wind_selected := {"wind-original":true}
	func included_key(key: String) -> String:
		for group in included:
			if included[group].source_keys.has(key): return group
		return ""
	func select_part(index: int) -> void:
		selected_calls.append(index); selected_key = keys[index]; pid = -1 if preview_launch_fails else 1
	func include_part(enabled: bool) -> void:
		if enabled:
			include_calls += 1
			included["g-"+selected_key] = {"valid":false,"source_keys":[selected_key],"request":{"reviewed":true,"identity":selected_key}}
			pid = -1 if review_launch_fails else 1
	func stop_pending_preview(_reason: String) -> void: wind_stops += 1
	func refresh_inclusions() -> void: refresh_calls += 1

func check(value: bool, label: String) -> void:
	checks += 1
	if not value: failures += 1
	print(("PASS " if value else "FAIL ")+label)

func make_case() -> Dictionary:
	var editor := Editor.new(); root.add_child(editor)
	var window := Window.new(); root.add_child(window); editor.window = window
	var item := ItemList.new(); window.add_child(item)
	for name in editor.part_names: item.add_item(name)
	var selector := Selector.new(); window.add_child(selector)
	selector.editor = editor; selector.list = item; selector.status = Label.new(); window.add_child(selector.status)
	selector.model.configure(editor.keys)
	return {"editor":editor,"window":window,"selector":selector}

func dispose(value: Dictionary) -> void:
	value.selector.shutdown(); value.window.free()
	for control in [value.editor.info,value.editor.anchors,value.editor.existing_toggle,value.editor.patch_toggle,value.editor.include_toggle,value.editor.apply_button]: control.free()
	value.editor.free()

func _initialize() -> void: call_deferred("run")
func run() -> void:
	var m := Core.new()
	check(m.configure(["a","b","c","d","e"],[2]).is_empty(),"selection.valid_domain")
	m.click(1)
	check(m.snapshot() == {"selected":[1],"focus":1,"anchor":1},"selection.plain_click_is_single_focus")
	m.click(4,true)
	check(m.snapshot().selected == [1,4] and m.focus == 4,"selection.ctrl_add_is_not_batch_inclusion")
	m.click(1,true)
	check(m.snapshot().selected == [4] and m.focus == 1,"selection.ctrl_remove_keeps_distinct_focus")
	m.click(0); m.click(4,false,true)
	check(m.snapshot().selected == [0,1,3,4] and m.anchor == 0,"selection.shift_range_skips_disabled")
	m.click(4); m.click(0,true,true)
	check(m.snapshot().selected == [0,1,3,4],"selection.ctrl_shift_add_range")
	var unchanged: PackedByteArray = var_to_bytes(m.snapshot())
	check(not m.click(2) and not m.begin(-1) and var_to_bytes(m.snapshot()) == unchanged,"selection.disabled_or_outside_is_noop")
	check(not m.configure(["a","a"]).is_empty() and var_to_bytes(m.snapshot()) == unchanged,"selection.bad_domain_is_atomic")
	m.click(0); m.begin(1); m.update(4)
	check(m.snapshot().selected == [1,3,4],"drag.plain_selects_range_without_preview_callbacks")
	m.update(3)
	check(m.snapshot().selected == [1,3],"drag.backtracking_does_not_accumulate_rows")
	m.cancel()
	check(m.snapshot() == {"selected":[0],"focus":0,"anchor":0},"drag.escape_restores_full_selection")
	m.begin(1,true); m.update(4); m.finish()
	check(m.snapshot().selected == [0,1,3,4],"drag.ctrl_add_preserves_previous_rows")
	m.begin(1,true); m.update(3); m.finish()
	check(m.snapshot().selected == [0,4],"drag.ctrl_remove_does_not_touch_other_rows")
	m.click(1); m.begin(4,false,true); m.update(3); m.finish()
	check(m.snapshot().selected == [1,3],"drag.shift_uses_original_range_anchor")
	var keys: Array = m.selected_keys(); keys.clear()
	check(m.selected_keys() == ["b","d"],"selection.returned_keys_do_not_alias_state")
	m.begin(4); m.update(4); var done: Dictionary = m.finish()
	check(done.changed and not m.dragging,"drag.release_commits_selection_only")
	var c: Dictionary = make_case(); var editor: Node = c.editor; var selector: Node = c.selector
	selector.model.click(0); selector.model.click(1,false,true)
	var wind: PackedByteArray = var_to_bytes(editor.wind_selected)
	selector.include_selected()
	check(selector.queue_active and editor.selected_calls == [0] and editor.included.is_empty(),"batch.selection_enters_ordinary_preview_before_inclusion")
	editor.pid = -1; selector.after_review({"can_apply":true})
	check(editor.include_calls == 1 and not editor.included["g-a"].valid and selector.queue_active,"batch.include_keeps_existing_second_review")
	editor.pid = -1; editor.included["g-a"].valid = true; selector.after_review({"can_apply":true})
	check(editor.selected_calls == [0,1] and selector.queue_active and selector.model.focus == 1,"batch.only_then_reviews_next_focused_part")
	editor.pid = -1; selector.after_review({"can_apply":false})
	check(not selector.queue_active and editor.included.is_empty(),"batch.failed_later_part_restores_prior_groups_atomically")
	check(editor.asset_apply_calls == 0 and var_to_bytes(editor.wind_selected) == wind,"batch.no_asset_apply_or_wind_selection_change")
	dispose(c)
	c = make_case(); editor = c.editor; selector = c.selector
	editor.included = {"shared":{"valid":true,"source_keys":["a","b"],"request":{"original":true}}}
	selector.model.click(0); selector.model.click(2,false,true); selector.include_selected()
	check(editor.selected_calls == [2],"batch.already_reviewed_shared_group_not_reviewed_twice")
	editor.pid = -1; selector.after_review({"can_apply":true})
	editor.pid = -1; editor.included["g-c"].valid = true; selector.after_review({"can_apply":true})
	check(not selector.queue_active and editor.included.size() == 2 and editor.asset_apply_calls == 0,"batch.success_waits_for_separate_apply")
	selector.model.click(0); selector.exclude_selected()
	check(not editor.included.has("shared") and editor.included.has("g-c"),"batch.exclude_removes_complete_shared_group")
	check(editor.wind_selected == {"wind-original":true},"wind.selection_is_independent_of_row_exclusion")
	dispose(c)
	c = make_case(); editor = c.editor; selector = c.selector
	editor.included = {"old":{"valid":true,"source_keys":["d"],"request":{"token":31}}}
	var prior: PackedByteArray = var_to_bytes(editor.included)
	selector.model.click(0); editor.app.recovery_revision = 8; selector.include_selected()
	check(not selector.queue_active and editor.selected_calls.is_empty() and var_to_bytes(editor.included) == prior,"batch.context_drift_refuses_before_next_preview")
	editor.app.recovery_revision = 7; selector.include_selected()
	editor.included["partial"] = {"valid":false,"source_keys":["a"],"request":{}}
	selector.shutdown()
	check(var_to_bytes(editor.included) == prior and selector.editor == null,"batch.shutdown_restores_only_temporary_inclusion_then_releases_editor")
	c.window.free()
	for control in [editor.info,editor.anchors,editor.existing_toggle,editor.patch_toggle,editor.include_toggle,editor.apply_button]: control.free()
	editor.free()
	c = make_case(); editor = c.editor; selector = c.selector
	selector.model.click(0); selector.schedule_focus(); selector.model.click(3); selector.schedule_focus(); selector.focus_due = 1
	check(editor.apply_button.disabled and editor.include_toggle.disabled,"focus.pending_preview_cannot_apply_or_include_previous_part")
	selector._process(0.0)
	check(editor.selected_calls == [3] and selector.focus_due == 0,"focus.quick_selection_changes_coalesce_to_last_preview")
	editor.pid = -1; selector._process(0.0)
	check(editor.selected_calls == [3],"focus.idle_frame_does_not_repeat_worker_launch")
	dispose(c)
	c = make_case(); editor = c.editor; selector = c.selector
	editor.included = {"old":{"valid":true,"source_keys":["d"],"request":{"token":31}}}
	prior = var_to_bytes(editor.included); editor.preview_launch_fails = true
	selector.model.click(0); selector.include_selected()
	check(not selector.queue_active and var_to_bytes(editor.included) == prior and selector.list.focus_mode == Control.FOCUS_ALL,"batch.synchronous_preview_launch_failure_restores_groups_and_list")
	dispose(c)
	c = make_case(); editor = c.editor; selector = c.selector
	editor.included = {"old":{"valid":true,"source_keys":["d"],"request":{"token":31}}}
	prior = var_to_bytes(editor.included); selector.model.click(0); selector.include_selected()
	editor.pid = -1; editor.review_launch_fails = true; selector.after_review({"can_apply":true})
	check(not selector.queue_active and var_to_bytes(editor.included) == prior and editor.asset_apply_calls == 0,"batch.synchronous_second_review_failure_restores_original_groups")
	dispose(c)
	print("LOOSE_PART_SELECTION_UNIT ",JSON.stringify({"checks":checks,"failures":failures,"native_or_worker_started":false,"application_adopted":false}))
	quit(0 if failures == 0 else 1)
