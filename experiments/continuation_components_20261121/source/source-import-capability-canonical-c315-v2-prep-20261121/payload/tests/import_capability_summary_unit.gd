extends SceneTree
# Candidate controls: generated dictionaries and owned nodes only; no native asset.
const Summary = preload("res://src/import_capability_summary.gd")
const Info = preload("res://src/import_capability_editor.gd")
const Model = preload("res://src/model.gd")
const Renderer = preload("res://src/renderer.gd")
const World = preload("res://src/world_runtime.gd")
const Pose = preload("res://src/pose_editor.gd")
const WorldSelection = preload("res://src/world_selection.gd")
var failures := 0
var checks := 0

class FakeApp extends Control:
	var playing := false
	var exporting := false
	var advanced_mode := false
	var renderer: Node
	var has_project := {"pid":-1}
	var messages: Array = []
	func button(parent: Node, text: String, action: Callable) -> Button:
		var item := Button.new(); item.text = text; item.pressed.connect(action); parent.add_child(item); return item
	func label(parent: Node, text: String) -> Label:
		var item := Label.new(); item.text = text; parent.add_child(item); return item
	func message(text: String) -> void: messages.append(text)

class FakeEditor extends Node:
	var app: FakeApp
	var actor: RefCounted
	func active_rig() -> RefCounted: return actor

func check(value: bool, label: String) -> void:
	checks += 1
	if not value: failures += 1
	print(("PASS " if value else "FAIL ") + label)

func has_text(values: Array, needle: String) -> bool:
	for value in values:
		if str(value).contains(needle): return true
	return false

func source_report() -> Dictionary:
	return {"adapter":"studio_source_1","warnings":[],"limits":["No Source physics, IK, gameplay, native sequence playback or lossless roundtrip"],"counts":{"bones":69},"native_parameters":{"source_jiggle":{"status":"retained_inert","rules":[{"native_bone_index":8}]}}}

func _initialize() -> void: call_deferred("run")

func run() -> void:
	var report := source_report()
	var original: PackedByteArray = var_to_bytes(report)
	var result: Dictionary = Summary.summarize(report)
	check(result.profile == "source" and not result.limitations.is_empty(),"source.clean_resource_import_still_shows_limits")
	check(not result.native_motion.supported and result.native_motion.owners == 0,"source.retained_rule_is_not_runtime_support")
	check(has_text(result.retained,"1 imported motion declarations") and has_text(result.limitations,"not active"),"source.imported_and_active_are_separate")
	check(not has_text(result.limitations,"No Source physics, IK,") and has_text(result.limitations,"Native game animations"),"source.legacy_blanket_note_replaced_without_losing_limit")
	check(not result.force_modal and result.note_count > 0,"success.notes_do_not_force_dialog")
	var complete := source_report()
	complete.limits = ["PBR approximation; bounded static LDR brush lightmaps; no HDR-only/styled/displacement lighting, Source shader/proxy execution or 3D skybox","Default skin/bodygroup only in GLB; all imported variants retained in editable.blend","No Source physics, IK, gameplay, native sequence playback or lossless roundtrip"]
	var complete_summary: Dictionary = Summary.summarize(complete)
	check(has_text(complete_summary.limitations,"material programs") and has_text(complete_summary.limitations,"dynamic material effects") and has_text(complete_summary.limitations,"3D skybox") and has_text(complete_summary.limitations,"back to the original game format"),"source.full_producer_limits_do_not_lose_shader_skybox_or_roundtrip_facts")
	check(has_text(complete_summary.retained,"editable preparation file") and has_text(complete_summary.limitations,"requires another import"),"source.editable_variant_retention_is_distinct_from_runtime_switching")
	check(var_to_bytes(report) == original,"source.raw_report_unchanged")
	var forged := source_report(); forged.runtime_support = true; forged.native_parameters.source_jiggle.rules.resize(49)
	check(not Summary.summarize(forged).native_motion.supported,"source.forged_counts_and_flags_cannot_offer_five")
	var fake_actor := Model.new(); fake_actor.data = {"metadata":{"native_parameters":forged}}
	check(not Summary.summarize(forged,fake_actor).native_motion.supported,"source.model_without_qualified_root_cannot_offer_five")
	var lit := source_report(); lit.native_parameters.static_brush_lightmaps = {"faces":29}
	lit.warnings = ["Static Source entity lights use approximate intensity, baked lighting is not recreated"]
	lit.native_parameters.static_entity_lights = [{"kind":"point"}]
	var light_original: PackedByteArray = var_to_bytes(lit)
	var lighting: Dictionary = Summary.summarize(lit)
	check(has_text(lighting.supported,"29 surfaces") and has_text(lighting.supported,"brightness is approximate"),"bsp.baked_surfaces_and_approximate_lights_are_distinct")
	check(not has_text(lighting.limitations,"baked lighting is not recreated") and has_text(lighting.limitations,"animated and HDR"),"bsp.stale_no_lightmaps_wording_not_repeated")
	check(var_to_bytes(lit) == light_original,"bsp.display_correction_does_not_edit_provenance")
	var parsed: Variant = JSON.parse_string(JSON.stringify(lit))
	var parsed_summary: Dictionary = Summary.summarize(parsed)
	check(has_text(parsed_summary.supported,"rig and object hierarchy") and has_text(parsed_summary.supported,"29 surfaces"),"source.actual_json_numeric_counts_remain_visible")
	check(Summary.count(29.0) == 29 and Summary.count(29) == 29 and Summary.count(true) == 0 and Summary.count(1.5) == 0 and Summary.count(-1) == 0 and Summary.count(1000001) == 0,"counts.exact_json_integer_only_no_bool_fraction_or_overflow")
	lit.limits.append("Unrecognized material X remains unsupported")
	check(has_text(Summary.summarize(lit).limitations,"Unrecognized material X"),"source.unknown_loss_remains_visible")
	var missing := source_report(); missing.materials = [{"status":"fallback gray"}]
	check(has_text(Summary.summarize(missing).actions,"dependency folders"),"source.missing_resources_have_recovery_action")
	var mmd := {"kind":"mmd_preparation","limitations":["Native physics is not reproduced"],"warnings":["Native physics is not reproduced"],"missing_textures":["clothes.png"]}
	var mmd_before: PackedByteArray = var_to_bytes(mmd)
	var m: Dictionary = Summary.summarize(mmd)
	check(m.profile == "mmd" and has_text(m.actions,"beside the original model") and m.limitations.size() == 1,"mmd.loss_deduplicated_and_missing_texture_actionable")
	check(not m.native_motion.supported and var_to_bytes(mmd) == mmd_before,"mmd.no_native_physics_invention_or_input_write")
	var vrm := {"kind":"vrm_preparation","warnings":["Gaze settings remain data only"],"limitations":["Toon appearance is approximate"]}
	var v: Dictionary = Summary.summarize(vrm)
	check(v.profile == "vrm" and has_text(v.retained,"Compatible chains") and has_text(v.limitations,"Gaze"),"vrm.retained_springs_and_declared_losses_separate")
	check(not v.native_motion.supported,"vrm.metadata_alone_not_source_five_capability")
	var bad := {"adapter":"studio_source_1","warnings":[17,null,{"private":"value"}],"limits":"wrong","mount_warnings":["Choose the missing dependency folder"]}
	var b: Dictionary = Summary.summarize(bad)
	check(b.notes_incomplete and has_text(b.actions,"dependency folder") and has_text(b.actions,"incomplete"),"notes.malformed_notes_do_not_hide_valid_actions")
	var long_notes := []
	for i in range(150): long_notes.append("note-"+str(i)+" "+"z".repeat(900))
	var bounded: Dictionary = Summary.summarize({"warnings":long_notes})
	check(bounded.more_notes_retained and bounded.limitations.size() <= Summary.MAX_LINES,"notes.large_report_has_bounded_visible_list")
	var every_line_bounded := true
	for note in bounded.limitations: every_line_bounded = every_line_bounded and note.length() <= Summary.MAX_LINE
	check(every_line_bounded,"notes.visible_line_length_bounded")
	var generic: Dictionary = Summary.summarize(null)
	check(generic.profile == "standard" and not generic.force_modal and not generic.native_motion.supported,"standard.no_native_claim_or_forced_dialog")
	check(Summary.plain_text(Summary.summarize({"warnings":["[url=private]literal[/url]"]})).contains("[url=private]literal[/url]"),"notes.plain_text_preserves_literal_characters")
	var app := FakeApp.new(); root.add_child(app)
	var editor := FakeEditor.new(); editor.app = app; root.add_child(editor)
	var panel := VBoxContainer.new(); app.add_child(panel)
	var info := Info.new(); root.add_child(info); info.setup(editor,panel)
	var shared_button: Button = info.add_button(panel)
	var actor := Model.new(); actor.data = {"metadata":{"native_parameters":report},"position":[0,0,0],"keys":[]}
	editor.actor = actor
	var actor_before: PackedByteArray = var_to_bytes(actor.data)
	info._process(0.0)
	check(info.button.visible and not info.button.disabled and info.report_for(actor) == report,"info.persisted_report_uses_current_actor")
	check(shared_button.visible and not shared_button.disabled,"info.map_and_model_entrypoints_share_availability")
	info.notify_import(report)
	check(app.messages.size() == 1 and str(app.messages[0]).contains("Import info") and info.window == null,"info.normal_success_is_nonmodal")
	check(var_to_bytes(actor.data) == actor_before,"info.read_only_summary_preserves_pose_and_keys")
	info.notify_import(missing)
	check(app.messages.size() == 2 and str(app.messages[1]).contains("available actions") and info.window == null,"info.actionable_resource_loss_is_nonmodal_and_clear")
	app.playing = true; info._process(0.0)
	check(info.button.disabled,"info.playback_does_not_offer_inspection")
	app.playing = false; app.exporting = true; info._process(0.0)
	check(info.button.disabled,"info.export_does_not_offer_inspection")
	app.exporting = false; app.has_project.pid = 8; info._process(0.0)
	check(info.button.disabled,"info.project_save_does_not_offer_inspection")
	app.has_project.pid = -1
	var standard_actor := Model.new(); standard_actor.data = {"metadata":{}}; editor.actor = standard_actor; info._process(0.0)
	check(info.button.visible and info.report_for(standard_actor).is_empty(),"info.standard_glb_can_open_shared_representation_info")
	editor.actor = null; info._process(0.0)
	check(not info.button.visible and info.target() == null,"info.removed_actor_releases_selection")
	var map_actor := Model.new(); map_actor.data = {"kind":"environment","metadata":{"native_parameters":lit}}
	var actual_world := World.new(); actual_world.instances = {"map":map_actor,"character":actor}
	var actual_renderer := Renderer.new(); actual_renderer.world_runtime = actual_world; actual_renderer.active_instance_id = "map"
	app.renderer = actual_renderer
	var actual_pose := Pose.new(); actual_pose.app = app
	var map_info := Info.new(); root.add_child(map_info); map_info.setup(actual_pose,panel)
	check(actual_pose.active_rig() == map_actor and map_info.target() == map_actor,"info.actual_world_renderer_route_includes_environment_kind")
	check(has_text(Summary.summarize(map_info.report_for(map_info.target())).supported,"29 surfaces"),"info.actual_world_map_row_exposes_baked_lighting_notes")
	actual_renderer.active_instance_id = "character"
	check(map_info.target() == actor and map_info.report_for(map_info.target()) == report,"info.actual_world_selection_cannot_leak_previous_map_report")
	var selection := WorldSelection.new(); selection.app = app; selection.tree = Tree.new(); panel.add_child(selection.tree)
	selection.help_label = Label.new(); panel.add_child(selection.help_label)
	var previous_buttons: int = map_info.buttons.size()
	selection.add_import_info(map_info); selection.add_import_info(map_info)
	check(selection.actions.size() == 1 and map_info.buttons.size() == previous_buttons+1,"info.world_action_registers_only_once_after_info_exists")
	check(selection.actions[0].get_parent() == selection.tree.get_parent() and selection.actions[0].get_meta("rail")[1] == "help","info.world_action_retains_rail_parent_and_styling")
	var startup: String = FileAccess.get_file_as_string("res://src/app.gd")
	check(startup.find("world_selection.setup(hierarchy)") >= 0 and startup.find("world_selection.setup(hierarchy)") < startup.find("pose_editor.setup(self,"),"info.actual_boot_order_requires_deferred_world_binding")
	map_info.free(); actual_pose.free(); actual_renderer.free(); selection.free()
	info.close(); info.close()
	check(info.window == null and info.actor_ref == null,"info.close_is_idempotent")
	info.free(); editor.free(); app.free()
	if checks!=43:push_error("Expected exactly43 authored legacy controls");quit(2);return
	print("IMPORT_CAPABILITY_SUMMARY "+JSON.stringify({"checks":checks,"failures":failures,"legacy_controls":43,"native_assets_used":false,"user_profile":OS.get_user_data_dir()}))
	quit(0 if failures == 0 else 1)
