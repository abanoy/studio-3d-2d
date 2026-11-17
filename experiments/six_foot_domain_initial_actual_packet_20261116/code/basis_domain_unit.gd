extends SceneTree
# UNPARSED/UNRUN. Future root-owned headless domain probe; no native assets.
const BasisDomain = preload("res://experiments/six_foot_import_basis_gd_candidate_20261116/import_basis_domain.gd")
const SCRIPT := "res://experiments/six_foot_import_basis_gd_candidate_20261116/basis_domain_unit.gd"
var named: Dictionary = {}
var failures := 0

func mark(name: String,ok: bool) -> void:
	if named.has(name): push_error("Duplicate assertion name"); quit(3); return
	named[name] = ok
	if not ok: failures += 1
	print(("PASS " if ok else "FAIL ")+"basis_domain."+name)

func checked_job() -> Dictionary:
	var args := OS.get_cmdline_user_args()
	if args.size() != 1: return {"error":"One root-approved job required"}
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	if not parsed is Dictionary or parsed.get("format") != "has_six_foot_domain_job_1" or parsed.get("phase") != "ROOT_APPROVED_SIX_FOOT_DOMAIN" or parsed.get("root_closed_all") != true or float(parsed.get("expires_unix",0)) <= Time.get_unix_time_from_system(): return {"error":"Fresh released root lease required"}
	if parsed.get("script_sha256") != FileAccess.get_sha256(SCRIPT) or parsed.get("corpus_sha256") != FileAccess.get_sha256(parsed.get("corpus","")): return {"error":"Root-pinned script/corpus required"}
	var base: String = ProjectSettings.globalize_path("res://output/").replace("\\","/").trim_suffix("/")+"/"
	var folder: String = str(parsed.get("folder","")).replace("\\","/")
	if not folder.is_absolute_path() or folder.simplify_path() != folder or not folder.begins_with(base) or folder == base or FileAccess.file_exists(folder.path_join("result.json")): return {"error":"Fresh owned output required"}
	return parsed

func _initialize() -> void: call_deferred("run")

func run() -> void:
	var job := checked_job()
	if job.has("error"): push_error(job.error); quit(2); return
	var corpus = JSON.parse_string(FileAccess.get_file_as_string(job.corpus))
	if not corpus is Dictionary or corpus.get("format") != "has_six_foot_gd_parity_corpus_1" or not corpus.get("rows") is Array or corpus.rows.size() != 434: push_error("Pinned434-case synthetic corpus required"); quit(2); return
	for row in corpus.rows:
		var actual: Dictionary
		if row.operation == "factor": actual = BasisDomain.factor_for(row.request.get("height"))
		elif row.operation == "ratio": actual = BasisDomain.rounded_ratio(row.request.numerator,row.request.denominator)
		elif row.operation == "model": actual = BasisDomain.model_admission(row.request.model,row.request.scene_capability,row.request.runtime_basis_ready)
		elif row.operation == "inspect": actual = BasisDomain.inspect_capability(row.request.document)
		elif row.operation == "encode": actual = BasisDomain.encode_capability(row.request.document)
		else: push_error("Unknown corpus operation"); quit(2); return
		var ok: bool = actual.has("error") if row.expected.get("error",false) else not actual.has("error")
		if ok and not row.expected.get("error",false):
			for field in row.expected:
				if actual.get(field) != row.expected[field]: ok = false
		mark("corpus."+row.name,ok)
	var sha := "a".repeat(64)
	var model := {"sha256":sha,"kind":"model","asset_basis":{"format":BasisDomain.FORMAT,"purpose":"standard_complete_human_six_feet","source_sha256":sha,"measured_from_sha256":sha,"factor":"0.9144","target_metres":"1.8288","measured_converted_height":"2","measurement_algorithm":"neutral_complete_human_height_1","reference_pose":"neutral_default","classification":"verified_complete_human","decision":"automatic_qualified"}}
	var raw := Transform3D(Basis(Vector3.UP,PI/2.0).scaled(Vector3.ONE*2.0),Vector3(3,4,5))
	var legacy_raw := Transform3D(Basis.IDENTITY.scaled(Vector3(2,3,4)),Vector3(1,2,3))
	mark("root.legacy_absent_identity",BasisDomain.configure_import_root(legacy_raw,{}).get("base_root") == legacy_raw)
	mark("root.active_runtime_off_refuses",BasisDomain.configure_import_root(raw,model,true,false).has("error"))
	mark("root.active_no_capability_refuses",BasisDomain.configure_import_root(raw,model,false,true).has("error"))
	var configured := BasisDomain.configure_import_root(raw,model,true,true)
	var expected := Transform3D(Basis.IDENTITY.scaled(Vector3.ONE*0.9144),Vector3.ZERO)*raw
	mark("root.intrinsic_times_raw",not configured.has("error") and configured.base_root.is_equal_approx(expected))
	mark("root.imported_offset_scales",not configured.has("error") and configured.base_root.origin.distance_to(Vector3(3,4,5)*0.9144) <= BasisDomain.EPS)
	mark("root.repeated_raw_configuration_does_not_compound",not configured.has("error") and BasisDomain.configure_import_root(raw,model,true,true).base_root == configured.base_root and configured.raw_root == raw)
	var artist := Transform3D(Basis.IDENTITY.scaled(Vector3.ONE*3.0),Vector3(10,20,30))
	mark("root.artist_position_remains_metres",not configured.has("error") and (artist*configured.base_root).origin.distance_to(Vector3(10,20,30)+raw.origin*0.9144*3.0) <= BasisDomain.EPS)
	mark("root.active_nonuniform_refuses",BasisDomain.configure_import_root(legacy_raw,model,true,true).has("error"))
	mark("root.active_reflection_refuses",BasisDomain.configure_import_root(Transform3D(Basis.IDENTITY.scaled(Vector3(-1,1,1)),Vector3.ZERO),model,true,true).has("error"))
	var sheared := Transform3D(Basis(Vector3(1,0,0),Vector3(0.1,1,0),Vector3(0,0,1)),Vector3.ZERO)
	mark("root.active_shear_refuses",BasisDomain.configure_import_root(sheared,model,true,true).has("error"))
	var result := {"format":"has_six_foot_gd_domain_result_1","checks":named.size(),"expected_checks":444,"failures":failures,"complete_assertion_set":named.size()==444,"named_checks":named,"synthetic_only":true,"native_assets_read":false,"classification_run":false,"application_import_activation":false,"job_script_sha256":FileAccess.get_sha256(SCRIPT),"corpus_sha256":FileAccess.get_sha256(job.corpus)}
	DirAccess.make_dir_recursive_absolute(job.folder)
	var file := FileAccess.open(job.folder.path_join("result.json"),FileAccess.WRITE)
	if not file: push_error("Cannot write fresh result"); quit(2); return
	file.store_string(JSON.stringify(result,"",true,true)); file.close()
	print("SIX_FOOT_DOMAIN "+JSON.stringify({"checks":named.size(),"failures":failures}))
	quit(0 if failures == 0 and named.size()==444 else 1)
