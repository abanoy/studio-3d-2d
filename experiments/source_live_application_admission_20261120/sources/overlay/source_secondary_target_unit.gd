extends SceneTree
const Candidate = preload("res://output/source-secondary-live-target-prep-20261120/source_secondary.gd")
var failures := 0

func check(value: bool, label: String) -> void:
	if not value: failures += 1
	print(("PASS " if value else "FAIL ") + label)

func _initialize() -> void:
	check(Candidate.qualified_asset_data({"sha256":Candidate.GLB_SHA}), "legacy.exact_sha_preserved")
	for value in [null, "", true, 1, "f".repeat(64)]:
		check(not Candidate.qualified_asset_data({"sha256":value}), "target.unknown_or_uncorroborated_refused")
	check(not Candidate.qualified_asset_data({}), "target.missing_refused")
	if Candidate.LIVE_GLB_SHA != "b8436dea1d13a7cb4632c37c50b4cab123616ec574720fe4e764b844c5293e71" or Candidate.LIVE_CROSSWALK_PROOF_SHA.is_empty():
		check(not Candidate.qualified_asset_data({"sha256":"b8436dea1d13a7cb4632c37c50b4cab123616ec574720fe4e764b844c5293e71"}), "correction_only.no_bone_proof_refused")
	if Candidate.LIVE_GLB_SHA.is_empty() or Candidate.LIVE_CROSSWALK_PROOF_SHA.is_empty():
		check(not Candidate.qualified_asset_data({"sha256":"e".repeat(64)}), "pending.no_new_target_admitted")
	else:
		var crosswalk := {"format":"studio_source_bone_crosswalk_1","status":"retained_inert","profile":Candidate.Bindings.PROFILE,"native_mdl_sha256":Candidate.LIVE_NATIVE_MDL_SHA,"glb_sha256":Candidate.LIVE_GLB_SHA,"proof_sha256":Candidate.LIVE_CROSSWALK_PROOF_SHA,"jiggle_wire_sha256":Candidate.WIRE_SHA}
		var data := {"sha256":Candidate.LIVE_GLB_SHA,"metadata":{"native_parameters":{"native_parameters":{"source_export_crosswalk":crosswalk}}}}
		check(Candidate.qualified_asset_data(data), "live.exact_sha_and_wire_admitted")
		for field in crosswalk:
			var altered: Dictionary = data.duplicate(true)
			altered.metadata.native_parameters.native_parameters.source_export_crosswalk[field] = "foreign"
			check(not Candidate.qualified_asset_data(altered), "live.changed_" + str(field) + "_refused")
	quit(0 if failures == 0 else 1)
