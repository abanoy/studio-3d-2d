extends SceneTree
# SUCCESSOR UNPARSED/UNRUN. Exact JSON-number comparison; no native assets.
const BasisDomain = preload("res://experiments/six_foot_domain_json_transport_20261116/import_basis_domain.gd")
const SCRIPT := "res://experiments/six_foot_domain_json_transport_20261116/basis_domain_unit.gd"
var named: Dictionary = {}
var failures := 0
var raw_named: Dictionary = {}
var strict_encode_differences: Dictionary = {}

func mark(name: String,ok: bool) -> void:
	if named.has(name): push_error("Duplicate assertion name"); quit(3); return
	named[name] = ok
	if not ok: failures += 1
	print(("PASS " if ok else "FAIL ")+"basis_domain."+name)

# Test-only transport comparison. Never use float tolerance or stringify/parse
# to compare the encoder: that can conceal lost integer precision or NaN/null.
const MAX_EXACT_CROSS_TYPE_INTEGER := 9007199254740992

func exact_json_number(actual, expected) -> bool:
	var a_type := typeof(actual)
	var e_type := typeof(expected)
	if not a_type in [TYPE_INT,TYPE_FLOAT] or not e_type in [TYPE_INT,TYPE_FLOAT]: return false
	if a_type == TYPE_FLOAT and not is_finite(actual): return false
	if e_type == TYPE_FLOAT and not is_finite(expected): return false
	if a_type == e_type: return actual == expected
	var integer: int = actual if a_type == TYPE_INT else expected
	if integer < -MAX_EXACT_CROSS_TYPE_INTEGER or integer > MAX_EXACT_CROSS_TYPE_INTEGER: return false
	return float(actual) == float(expected)

func json_differences(actual, expected, path: String="$", depth: int=0, allow_number_representation: bool=true) -> Array:
	var a_type := typeof(actual)
	var e_type := typeof(expected)
	var delta := {"path":path,"actual_type":type_string(a_type),"expected_type":type_string(e_type)}
	if depth > 64:
		delta["reason"] = "depth_limit"; return [delta]
	if a_type in [TYPE_INT,TYPE_FLOAT] and e_type in [TYPE_INT,TYPE_FLOAT]:
		var number_equal := exact_json_number(actual,expected)
		if number_equal and (allow_number_representation or a_type == e_type): return []
		delta["reason"] = "number_representation" if number_equal else "number_value_or_nonfinite"
		delta["exact_numeric_equal"] = number_equal
		if is_finite(float(actual)) and is_finite(float(expected)):
			delta["actual_number"] = actual; delta["expected_number"] = expected
		return [delta]
	if a_type != e_type:
		delta["reason"] = "type"; return [delta]
	if a_type == TYPE_DICTIONARY:
		var differences: Array = []
		if actual.size() != expected.size():
			delta["reason"] = "object_key_count"; differences.append(delta)
		for key in actual:
			if typeof(key) != TYPE_STRING or not expected.has(key):
				differences.append({"path":path,"reason":"unexpected_or_nonstring_key"})
		for key in expected:
			if typeof(key) != TYPE_STRING or not actual.has(key):
				differences.append({"path":path,"reason":"missing_or_nonstring_key"})
			else:
				differences.append_array(json_differences(actual[key],expected[key],path+"."+key,depth+1,allow_number_representation))
		return differences
	if a_type == TYPE_ARRAY:
		if actual.size() != expected.size():
			delta["reason"] = "array_length"; return [delta]
		var differences: Array = []
		for index in range(actual.size()):
			differences.append_array(json_differences(actual[index],expected[index],path+"["+str(index)+"]",depth+1,allow_number_representation))
		return differences
	if not a_type in [TYPE_NIL,TYPE_BOOL,TYPE_STRING]:
		delta["reason"] = "non_json_type"; return [delta]
	if actual != expected:
		delta["reason"] = "value"; return [delta]
	return []

func compare_contract(name: String, actual, expected, equal: bool) -> void:
	mark("transport.comparator."+name,json_differences(actual,expected).is_empty() == equal)

func run_comparator_contracts() -> void:
	compare_contract("int_float_exact",9,9.0,true)
	compare_contract("float_int_exact",9.0,9,true)
	compare_contract("nested_number_exact",{"a":[{"b":9}]},{"a":[{"b":9.0}]},true)
	compare_contract("largest_safe_positive",9007199254740992,9007199254740992.0,true)
	compare_contract("largest_safe_negative",-9007199254740992,-9007199254740992.0,true)
	compare_contract("unsafe_integer_alias",9007199254740993,9007199254740992.0,false)
	compare_contract("unsafe_negative_alias",-9007199254740993,-9007199254740992.0,false)
	compare_contract("same_large_integer",9007199254740993,9007199254740993,true)
	compare_contract("true_is_not_one",true,1,false)
	compare_contract("false_is_not_zero",false,0.0,false)
	compare_contract("string_is_not_number","9",9,false)
	compare_contract("different_integer",9,10.0,false)
	compare_contract("different_fraction",9,9.000000000000002,false)
	compare_contract("nan_refused",NAN,NAN,false)
	compare_contract("infinity_refused",INF,INF,false)
	compare_contract("negative_infinity_refused",-INF,-INF,false)
	compare_contract("null_exact",null,null,true)
	compare_contract("null_is_not_false",null,false,false)
	compare_contract("case_sensitive_strings","Model","model",false)
	compare_contract("ordered_arrays",[1,2],[2.0,1.0],false)
	compare_contract("array_length",[1],[1.0,2.0],false)
	compare_contract("missing_null_key",{}, {"a":null},false)
	compare_contract("extra_key",{"a":null},{},false)
	compare_contract("object_order_irrelevant",{"a":1,"b":2},{"b":2.0,"a":1.0},true)
	compare_contract("integer_object_key_refused",{1:9},{"1":9.0},false)
	compare_contract("native_vector_refused",Vector3.ZERO,Vector3.ZERO,false)
	var nested = null
	for unused in range(66): nested = [nested]
	compare_contract("depth_limit",nested,nested,false)
	mark("transport.comparator.raw_variant_type_mismatch_is_reproduced",{"schema_version":9} != {"schema_version":9.0} and 9 == 9.0)

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
		var raw_ok: bool = actual.has("error") if row.expected.get("error",false) else not actual.has("error")
		var ok: bool = raw_ok
		if ok and not row.expected.get("error",false):
			for field in row.expected:
				var raw_equal: bool = actual.get(field) == row.expected[field]
				if not raw_equal: raw_ok = false
				if row.operation == "encode" and field == "document":
					if not json_differences(actual.get(field),row.expected[field],"$.document").is_empty(): ok = false
					if not raw_equal: strict_encode_differences[row.name] = json_differences(actual.get(field),row.expected[field],"$.document",0,false)
				elif not raw_equal: ok = false
		raw_named["corpus."+row.name] = raw_ok
		mark("corpus."+row.name,ok)
	run_comparator_contracts()
	var expected_raw_failures: Array = []
	for index in range(7):
		var case_name := "schema_encode_"+str(index)
		expected_raw_failures.append("corpus."+case_name)
		var differences: Array = strict_encode_differences.get(case_name,[])
		var proves_numeric_type_only := differences.size() == 1
		if proves_numeric_type_only:
			var delta: Dictionary = differences[0]
			proves_numeric_type_only = delta.get("path") == "$.document.schema_version" and delta.get("actual_type") == "int" and delta.get("expected_type") == "float" and delta.get("reason") == "number_representation" and delta.get("exact_numeric_equal") == true and delta.get("actual_number") == 9 and delta.get("expected_number") == 9
		mark("transport.actual_type_only_"+case_name,proves_numeric_type_only)
	var raw_failures: Array = []
	for name in raw_named:
		if not raw_named[name]: raw_failures.append(name)
	raw_failures.sort(); expected_raw_failures.sort()
	mark("transport.raw_failure_set_preserved",raw_named.size() == 434 and raw_failures == expected_raw_failures and strict_encode_differences.size() == 7)
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
	var result := {"format":"has_six_foot_gd_domain_result_1","checks":named.size(),"expected_checks":480,"failures":failures,"complete_assertion_set":named.size()==480,"named_checks":named,"raw_corpus_named_checks":raw_named,"strict_encode_differences":strict_encode_differences,"comparison_contract":"exact_json_numbers_bounded_cross_type_1","encoder_unchanged":true,"synthetic_only":true,"native_assets_read":false,"classification_run":false,"application_import_activation":false,"job_script_sha256":FileAccess.get_sha256(SCRIPT),"corpus_sha256":FileAccess.get_sha256(job.corpus)}
	DirAccess.make_dir_recursive_absolute(job.folder)
	var file := FileAccess.open(job.folder.path_join("result.json"),FileAccess.WRITE)
	if not file: push_error("Cannot write fresh result"); quit(2); return
	file.store_string(JSON.stringify(result,"",true,true)); file.close()
	print("SIX_FOOT_DOMAIN "+JSON.stringify({"checks":named.size(),"failures":failures}))
	quit(0 if failures == 0 and named.size()==480 else 1)
