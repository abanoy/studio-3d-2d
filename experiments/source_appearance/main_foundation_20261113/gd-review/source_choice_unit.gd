extends SceneTree
## Authored headless boundary cases. No native reader, converter, or child is run.
const Choice = preload("res://src/source_choice_dialog.gd")
const Importer = preload("res://src/source_import.gd")

class MetadataDouble extends RefCounted:
	var launches: Array = []
	var closed: Array = []
	var token := -1
	var next_token := 101
	var alive := false
	var now := 1000
	var exit_code := 0

class ChoiceDouble extends Choice:
	var worker := MetadataDouble.new()
	func _launch_metadata(args: PackedStringArray) -> int:
		worker.token = worker.next_token
		worker.next_token += 1
		worker.alive = true
		worker_exit = -1
		worker.launches.append({"token": worker.token, "args": args.duplicate()})
		return worker.token
	func _metadata_running() -> bool:
		return worker.token > 0 and worker.alive
	func _stop_metadata() -> void:
		if worker.token > 0:
			worker.closed.append(worker.token)
			worker.token = -1
			worker.alive = false
			worker_exit = worker.exit_code
	func _clock_msec() -> int:
		return worker.now

class HeightDouble extends RefCounted:
	var pending := false

class PoseDouble extends RefCounted:
	var additions: Array = []
	func finish_drag() -> void: pass
	func add_model(path: String, frame: int, placement: Dictionary) -> String:
		additions.append({"path": path, "frame": frame, "placement": placement})
		return "Unexpected adoption in metadata-only test"

class BrowserDouble extends RefCounted:
	var opened: Array = []
	func open(actor: bool) -> void: opened.append(actor)

class AppDouble extends Control:
	var exporting := false
	var height_review := HeightDouble.new()
	var pose_editor := PoseDouble.new()
	var source_browser := BrowserDouble.new()
	var messages: Array = []
	var stops := 0
	var document := {"world": {"actors": [{"id": "existing", "pose": [1, 2, 3]}]},
		"history": [{"label": "existing edit"}], "redo": [{"label": "future edit"}],
		"dirty": true, "frame": 17, "selection": "existing"}
	func stop() -> void: stops += 1
	func finish_stroke() -> void: pass
	func release_mouse() -> void: pass
	func message(text: String) -> void: messages.append(text)
	func label(parent: Node, text: String) -> Label:
		var result := Label.new(); result.text = text; parent.add_child(result); return result
	func button(parent: Node, text: String, action: Callable) -> Button:
		var result := Button.new(); result.text = text; parent.add_child(result); result.pressed.connect(action); return result
	func spin(parent: Node, title: String, minimum: float, maximum: float, value: float) -> SpinBox:
		label(parent, title)
		var result := SpinBox.new(); result.min_value = minimum; result.max_value = maximum; result.value = value
		parent.add_child(result); return result

class ImportDouble extends Importer:
	var last_choice: ChoiceDouble
	var choices_created := 0
	var launches: Array = []
	var spawned: Array = []
	var forward_launch := false
	var saved_paths := 0
	func inspect_source_members(_path: String) -> Dictionary:
		return {"code": 0, "data": {"models": ["models/authored_a.mdl", "models/authored_b.mdl"], "maps": ["maps/authored.bsp"]}, "text": "authored catalogue stand-in"}
	func make_appearance_ui() -> Node:
		last_choice = ChoiceDouble.new(); last_choice.set_process(false); choices_created += 1; return last_choice
	func save_paths() -> Error:
		saved_paths += 1; return OK
	func _spawn_preparation(args: PackedStringArray) -> int:
		spawned.append(args.duplicate()); return -1
	func launch(path: String, member: String, as_model: bool, scale: float, content := "", dependency_mounts = null, asset_root := "", obj_up := "Y", at_frame := 0, placement := {}, appearance := {}) -> void:
		if forward_launch:
			super.launch(path, member, as_model, scale, content, dependency_mounts, asset_root, obj_up, at_frame, placement, appearance)
			return
		launches.append({"path": path, "member": member, "actor": as_model, "scale": scale,
			"frame": at_frame, "placement": placement.duplicate(true), "appearance": appearance.duplicate(true),
			"metadata_token_at_launch": last_choice.worker.token if is_instance_valid(last_choice) else -1})

var checks := 0
var failures := 0
var folder := ""
var app: AppDouble
var importer: ImportDouble

func _initialize() -> void: call_deferred("run")

func check(ok: bool, label: String) -> void:
	checks += 1; print(("PASS " if ok else "FAIL ") + label)
	if not ok: failures += 1

func catalogue(member: String) -> Dictionary:
	# JSON round-trip deliberately reproduces Godot's floating numeric table IDs.
	return JSON.parse_string(JSON.stringify({"format": "studio_source_mdl_choices_1", "selected_member": member,
		"original_source_sha256": "a".repeat(64), "native_mdl_sha256": "b".repeat(64), "catalogue_sha256": "c".repeat(64),
		"skins": [{"index": 0}, {"index": 1}, {"index": 2}], "bodygroups": [
			{"index": 0, "name": "native_torso", "display_name": "Shared label", "choices": [
				{"index": 0, "display_name": "Body", "true_blank": false}, {"index": 1, "display_name": "Off", "true_blank": true}]},
			{"index": 1, "name": "native_hat", "display_name": "Shared label", "choices": [
				{"index": 0, "display_name": "Off", "true_blank": true}, {"index": 1, "display_name": "Hat", "true_blank": false}]},
			{"index": 2, "name": "native_ornament", "display_name": "Line\nTab\tname", "choices": [
				{"index": 0, "display_name": "Off", "true_blank": true}, {"index": 1, "display_name": "blank", "true_blank": false}]}]}))

func write_json(path: String, value: Variant) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		check(false, "authored status file can be written"); return
	file.store_string(JSON.stringify(value)); file.close()

func deliver(choice: ChoiceDouble, value: Variant) -> void:
	write_json(choice.status_path, value); choice.worker.alive = false; choice._process(0.0)

func select(option: OptionButton, index: int) -> void:
	option.select(index); option.item_selected.emit(index)

func open_source(as_model := true, extension := "gma") -> ConfirmationDialog:
	importer.start(folder.path_join("authored." + extension), as_model, 37, {"point": [1, 2, 3], "reason": "captured"})
	for child in app.get_children():
		if child is ConfirmationDialog and not child.is_queued_for_deletion(): return child
	return null

func close_dialog(dialog: ConfirmationDialog) -> void:
	dialog.queue_free(); await process_frame

func run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 1 or not args[0].is_absolute_path():
		push_error("Provide one fresh absolute output directory"); quit(2); return
	folder = args[0].replace("\\", "/"); DirAccess.make_dir_recursive_absolute(folder)
	app = AppDouble.new(); app.size = Vector2(1280, 720); root.add_child(app)
	importer = ImportDouble.new(); importer.app = app; importer.paths_file = folder.path_join("must-not-save-preferences.cfg")
	importer.set_process(false); app.add_child(importer)
	var original: Dictionary = app.document.duplicate(true)
	var dialog := open_source(); var ui: ChoiceDouble = importer.last_choice; var worker := ui.worker
	check(is_instance_valid(dialog) and dialog.visible and not dialog.dialog_hide_on_ok, "ordinary import constructs a visible confirmation with explicit guarded confirmation")
	check(ui.enabled.disabled and not ui.fields.visible and ui.request().is_empty() and not dialog.get_ok_button().disabled, "pending metadata leaves original default import available with no request")
	var launched: PackedStringArray = worker.launches[0].args
	check(launched.has("--appearance-catalogue") and launched.has("--member") and not launched.has("--appearance"), "inspection uses metadata-only arguments rather than conversion or appearance application")
	check(launched[launched.find("--member") + 1] == "models/authored_a.mdl" and launched[launched.find("--status-file") + 1] == ui.status_path, "worker arguments bind the exact selected native member and owned result address")
	check(app.document == original and app.pose_editor.additions.is_empty(), "constructing and starting the chooser changes no world, keys, history, redo or dirty state")
	var data := catalogue(ui.selected_member)
	check(typeof(data.bodygroups[0].index) == TYPE_FLOAT and ui.valid_catalogue(data), "actual JSON numeric table IDs validate before canonical integer control metadata")
	deliver(ui, {"ok": true, "catalogue": data})
	check(not ui.enabled.disabled and ui.skin.item_count == 3 and ui.groups.size() == 3, "real accepted status constructs skin and every native bodypart control")
	check(worker.closed == [101] and ui.pid == -1, "completed fake metadata ownership drains once before displaying its catalogue")
	check(not ui.fields.visible and ui.request().is_empty(), "successful inspection remains opt-in and still omits the default request")
	ui.enabled.button_pressed = true
	check(ui.fields.visible and ui.selection_valid() and ui.request().is_empty() and not dialog.get_ok_button().disabled, "enabling unchanged zero controls preserves exact default omission")
	check(ui.skin.get_selected_metadata() is int and ui.groups[1].option.get_selected_metadata() is int, "constructed OptionButtons retain native integer identities after JSON float parsing")
	check(ui.groups[0].option.get_item_text(1).contains("hidden") and not ui.groups[2].option.get_item_text(1).contains("hidden"), "native true_blank flag rather than a blank-looking label controls hidden disclosure")
	check(ui.groups[0].option.tooltip_text.contains("native_torso") and ui.groups[1].option.tooltip_text.contains("native_hat"), "identical display labels retain distinguishable native group tooltips")
	select(ui.skin, 2)
	var request := ui.request()
	check(request.format == "studio_source_appearance_request_1" and request.skin is int and request.skin == 2, "changed skin produces an explicit integer static request")
	check(request.bodygroups.keys() == ["0", "1", "2"] and request.bodygroups.values() == [0, 0, 0] and request.bodygroups["0"] is int, "request bodypart keys are canonical native integer strings with integer choices")
	check(request.source_sha256 == "a".repeat(64) and request.native_mdl_sha256 == "b".repeat(64), "request preserves both original-input and selected-native hashes")
	select(ui.skin, 0)
	check(ui.request().is_empty(), "resetting the changed skin to default removes the optional request again")
	select(ui.groups[2].option, 1)
	check(ui.selection_valid() and ui.request().bodygroups["2"] == 1, "a choice named blank with native geometry stays a selectable visible part")
	select(ui.groups[2].option, 0); select(ui.groups[0].option, 1)
	check(not ui.selection_valid() and dialog.get_ok_button().disabled and ui.request().is_empty(), "explicit all-blank choice disables confirmation without manufacturing a fallback request")
	var before_launches := importer.launches.size(); dialog.confirmed.emit()
	check(importer.launches.size() == before_launches and dialog.visible, "confirmed signal cannot bypass all-blank guard or silently import defaults")
	select(ui.groups[1].option, 1)
	check(ui.selection_valid() and not dialog.get_ok_button().disabled and ui.request().bodygroups["1"] == 1, "restoring one genuinely visible bodypart re-enables explicit preparation")
	ui.enabled.button_pressed = false
	check(ui.selection_valid() and ui.request().is_empty() and not ui.fields.visible, "opting out of changed controls explicitly returns to the original route")
	ui.enabled.button_pressed = true
	check(ui.request().bodygroups["1"] == 1, "opt-in visibility toggling preserves the chosen static values")
	var changed_request := ui.request().duplicate(true)
	dialog.confirmed.emit()
	check(importer.launches.size() == before_launches + 1 and importer.launches.back().appearance == changed_request, "valid confirmation transports exactly the inspected static request once")
	check(importer.launches.back().frame == 37 and importer.launches.back().placement == {"point": [1, 2, 3], "reason": "captured"}, "optional choice preserves the import's captured frame and placement context")
	check(importer.launches.back().metadata_token_at_launch == -1, "confirmation drains metadata ownership before handing off to preparation")
	await process_frame
	check(app.document == original and app.pose_editor.additions.is_empty(), "all chooser edits and confirmation leave existing scene and Undo data untouched before worker adoption")

	# Member change and same-member generation tests use the actual coordinator paths.
	dialog = open_source(); ui = importer.last_choice; worker = ui.worker
	var old_status := ui.status_path; var old_generation := ui.generation
	var old_result := {"ok": true, "catalogue": catalogue(ui.selected_member)}
	select(ui.members, 1)
	check(worker.closed == [101] and worker.launches.size() == 2 and ui.generation > old_generation, "member change closes the prior metadata owner and starts a distinct generation")
	check(ui.status_path != old_status and ui.selected_member == "models/authored_b.mdl", "member change receives a unique result address and exact new native identity")
	check(ui.catalogue.is_empty() and ui.groups.is_empty() and ui.enabled.disabled and ui.request().is_empty(), "member change clears old catalogue, controls and optional request")
	write_json(old_status, old_result); ui._process(0.0)
	check(ui.catalogue.is_empty() and ui.pid > 0, "a late old result file cannot satisfy the currently running member inspection")
	ui._accept_status(old_result)
	check(ui.catalogue.is_empty() and ui.enabled.disabled, "a result for another native member is refused at the actual status boundary")
	deliver(ui, {"ok": true, "catalogue": catalogue(ui.selected_member)})
	check(ui.groups.size() == 3 and not ui.enabled.disabled and ui.request().is_empty(), "the new member accepts only its own result and starts at default omission")
	var accepted_generation := ui.generation
	var accepted_catalogue := ui.catalogue.duplicate(true); var accepted_controls := ui.fields.get_child_count()
	ui.invalidate()
	var late_catalogue := catalogue(ui.selected_member); late_catalogue.original_source_sha256 = "d".repeat(64)
	ui._accept_status({"ok": true, "catalogue": late_catalogue})
	check(ui.generation > accepted_generation and ui.worker_generation == -1 and worker.closed == [101, 102]
		and ui.catalogue == accepted_catalogue and ui.groups.size() == 3 and ui.fields.get_child_count() == accepted_controls,
		"invalidation rejects late same-member catalogue/control replacement without releasing a completed owner twice")
	await close_dialog(dialog)

	# Schema and hash refusals are tested on authored JSON data, not native files.
	dialog = open_source(); ui = importer.last_choice; data = catalogue(ui.selected_member)
	for key in ["original_source_sha256", "native_mdl_sha256", "catalogue_sha256"]:
		var wrong := data.duplicate(true); wrong[key] = "G".repeat(64)
		check(not ui.valid_catalogue(wrong), "catalogue rejects invalid lowercase hex checksum: " + key)
	var wrong := data.duplicate(true); wrong.selected_member = "models/other.mdl"
	check(not ui.valid_catalogue(wrong), "catalogue binds exact selected member rather than merely a valid-looking MDL")
	wrong = data.duplicate(true); wrong.bodygroups[1].index = 9
	check(not ui.valid_catalogue(wrong), "noncanonical native bodypart identities refuse before control construction")
	wrong = data.duplicate(true); wrong.bodygroups[0].choices[0].erase("true_blank")
	check(not ui.valid_catalogue(wrong), "missing native blank classification cannot be guessed from display names")
	wrong = data.duplicate(true); wrong.skins = []
	check(not ui.valid_catalogue(wrong), "an empty skin table keeps the optional chooser unavailable")
	wrong = data.duplicate(true); wrong.bodygroups = []
	check(not ui.valid_catalogue(wrong), "an empty bodypart table keeps the optional chooser unavailable")
	wrong = data.duplicate(true); wrong.bodygroups[0].choices.resize(257)
	check(not ui.valid_catalogue(wrong), "oversized native choice table refuses before UI allocation")
	check(ui.display_name("A\nB\rC\t" + "x".repeat(120)).length() == 96 and not ui.display_name("A\nB\rC\t").contains("\n"), "native display text is bounded and stripped of multiline controls")
	await close_dialog(dialog)

	# Timeout boundary, cancel/close, malformed/bounded statuses and native-free defaults.
	dialog = open_source(); ui = importer.last_choice; worker = ui.worker
	worker.now = ui.inspection_started + 30000; ui._process(0.0)
	check(ui.pid > 0 and worker.closed.is_empty(), "metadata retains the exact thirty-second boundary without premature cancellation")
	worker.now += 1; ui._process(0.0)
	check(ui.pid == -1 and worker.closed == [101] and ui.enabled.disabled and not dialog.get_ok_button().disabled, "timeout closes the owned inspection once while preserving default preparation")
	write_json(ui.status_path, {"ok": true, "catalogue": catalogue(ui.selected_member)}); ui._process(0.0)
	check(ui.catalogue.is_empty() and ui.request().is_empty(), "late success after timeout cannot resurrect an optional appearance")
	await close_dialog(dialog)
	check(worker.closed == [101], "later dialog teardown does not release a timed-out owner twice")
	dialog = open_source(); ui = importer.last_choice; worker = ui.worker; dialog.canceled.emit()
	check(worker.closed == [101] and ui.pid == -1, "ordinary canceled signal immediately drains pending metadata")
	await process_frame
	check(worker.closed == [101], "queued cancellation and child exit retain exactly-once fake ownership cleanup")
	dialog = open_source(); ui = importer.last_choice; worker = ui.worker; dialog.close_requested.emit()
	check(worker.closed == [101] and ui.pid == -1, "window close signal also invalidates the pending inspection")
	await close_dialog(dialog)
	dialog = open_source(); ui = importer.last_choice; worker = ui.worker
	ui.worker_generation -= 1; deliver(ui, {"ok": true, "catalogue": catalogue(ui.selected_member)})
	check(ui.catalogue.is_empty() and worker.closed == [101], "stale generation completion drains without publishing controls")
	await close_dialog(dialog)
	dialog = open_source(); ui = importer.last_choice
	deliver(ui, {"ok": false, "error": "authored refusal"})
	check(ui.enabled.disabled and ui.note.text.contains("authored refusal") and not dialog.get_ok_button().disabled, "worker refusal stays actionable and leaves default conversion available")
	await close_dialog(dialog)
	dialog = open_source(); ui = importer.last_choice; worker = ui.worker; worker.exit_code = 7
	deliver(ui, {"ok": true, "catalogue": catalogue(ui.selected_member)})
	check(ui.catalogue.is_empty() and ui.enabled.disabled, "nonzero worker exit cannot promote a success-shaped status")
	await close_dialog(dialog)
	dialog = open_source(); ui = importer.last_choice
	var oversized := FileAccess.open(ui.status_path, FileAccess.WRITE); oversized.store_buffer(PackedByteArray(" ".repeat(300 * 1024 + 1).to_utf8_buffer())); oversized.close()
	ui.worker.alive = false; ui._process(0.0)
	check(ui.catalogue.is_empty() and ui.enabled.disabled and not dialog.get_ok_button().disabled, "oversized status refuses before parsing and retains default route")
	await close_dialog(dialog)
	dialog = open_source(); ui = importer.last_choice; worker = ui.worker; before_launches = importer.launches.size(); dialog.confirmed.emit()
	check(importer.launches.size() == before_launches + 1 and importer.launches.back().appearance.is_empty() and worker.closed == [101], "confirming while inspection is pending keeps exact default omission and drains the pending job")
	await process_frame
	var made := importer.choices_created; dialog = open_source(false)
	check(importer.choices_created == made, "BSP map dialog does not construct or launch the model-only appearance chooser")
	dialog.confirmed.emit()
	check(not importer.launches.back().actor and importer.launches.back().appearance.is_empty(), "map confirmation retains the original appearance-free import contract")
	await process_frame
	dialog = open_source(true, "bin"); ui = importer.last_choice
	check(ui.worker.launches.is_empty() and ui.enabled.disabled and ui.request().is_empty() and not dialog.get_ok_button().disabled, "unsupported legacy container skips optional inspection and keeps its normal default route")
	await close_dialog(dialog)

	# Exercise actual argument/file transport with a refused fake spawn, never Python.
	importer.forward_launch = true
	importer.launch(folder.path_join("authored.mdl"), "authored.mdl", true, 0.01905)
	var plain: PackedStringArray = importer.spawned.back()
	check(not plain.has("--appearance") and importer.pid == -1, "unchanged Source preparation omits optional appearance flag at the real argument boundary")
	importer.launch(folder.path_join("authored.gma"), "models/authored_a.mdl", true, 0.01905, "", null, "", "Y", 37, {}, changed_request)
	var explicit_args: PackedStringArray = importer.spawned.back(); var position := explicit_args.find("--appearance")
	check(position >= 0 and FileAccess.file_exists(explicit_args[position + 1]), "explicit static choice creates one request file and passes its owned address to preparation")
	var encoded := FileAccess.get_file_as_string(explicit_args[position + 1]) if position >= 0 else ""
	check(encoded == JSON.stringify(changed_request) and not encoded.contains('"0.0"') and not encoded.contains('"1.0"'), "real request file retains exact canonical integer keys and source/native hashes")
	var spawned_before := importer.spawned.size()
	importer.launch(folder.path_join("authored.bsp"), "", false, 0.01905, "", null, "", "Y", 0, {}, changed_request)
	check(importer.spawned.size() == spawned_before, "explicit model appearance is refused for a map rather than silently ignored")
	check(app.document == original and app.pose_editor.additions.is_empty(), "failed fake preparation, refusal, timeout, close and defaults preserve every existing document/history value")
	check(not FileAccess.file_exists(importer.paths_file), "test coordinator preference stand-in never writes shared Source settings")
	app.queue_free(); await process_frame
	var report := {"checks": checks, "failures": failures, "headless": true, "constructed_controls": true,
		"metadata_worker": "authored fake; no OS child", "preparation": "actual args/file seam with refused fake spawn",
		"native_conversion": false, "graphics": false, "actual_app_adoption": false,
		"scope": "Static chooser controls, native identities/default omission, generation/cancel/timeout ownership and import argument boundary; no native conversion or artist fidelity claim"}
	write_json(folder.path_join("result.json"), report)
	print("SOURCE_CHOICE_UNIT " + JSON.stringify(report)); quit(0 if failures == 0 else 1)
