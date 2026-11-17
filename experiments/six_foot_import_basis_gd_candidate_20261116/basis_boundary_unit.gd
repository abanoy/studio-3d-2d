extends SceneTree
# UNPARSED/UNRUN. Proposed adapter-boundary probe, not current app integration.
# Root stages this after its full lease ends. It uses only a new synthetic empty
# GLB and real SceneIO/Model, never any owner/native model or classification.
const Guards = preload("res://experiments/six_foot_import_basis_gd_candidate_20261116/source_boundary_guards.gd")
const SceneIO = preload("res://src/scene3d.gd")
const Model = preload("res://src/model.gd")
const SCRIPT := "res://experiments/six_foot_import_basis_gd_candidate_20261116/basis_boundary_unit.gd"
var named: Dictionary = {}
var failures := 0

func mark(name: String,ok: bool) -> void:
	if named.has(name): push_error("Duplicate assertion name"); quit(3); return
	named[name] = ok
	if not ok: failures += 1
	print(("PASS " if ok else "FAIL ")+"basis_boundary."+name)

func _initialize() -> void: call_deferred("run")

func run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size()!=1: push_error("One root-approved job required"); quit(2); return
	var job = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	if not job is Dictionary or job.get("format") != "has_six_foot_boundary_job_1" or job.get("phase") != "ROOT_APPROVED_SIX_FOOT_BOUNDARY" or job.get("root_closed_all") != true or float(job.get("expires_unix",0)) <= Time.get_unix_time_from_system() or job.get("script_sha256") != FileAccess.get_sha256(SCRIPT): push_error("Fresh released root lease and exact script required"); quit(2); return
	var base: String = ProjectSettings.globalize_path("res://output/").replace("\\","/").trim_suffix("/")+"/"
	var folder: String = str(job.get("folder","")).replace("\\","/")
	if not folder.is_absolute_path() or folder.simplify_path()!=folder or not folder.begins_with(base) or folder==base or FileAccess.file_exists(folder.path_join("result.json")) or FileAccess.file_exists(folder.path_join("synthetic.glb")): push_error("Fresh root-owned output required"); quit(2); return
	DirAccess.make_dir_recursive_absolute(folder)
	var source := folder.path_join("synthetic.glb")
	mark("sceneio.synthetic_empty_created",SceneIO.make_empty(source)==OK)
	var digest := FileAccess.get_sha256(source)
	var plain := Model.definition(source)
	plain["kind"]="model"
	var active := plain.duplicate(true); active["asset_basis"]={"format":"studio_import_basis_1","factor":"0.9144"}
	# Intentionally incomplete active record must still refuse before any consumer.
	for step in Guards.STEPS:
		var calls := [0]
		var response := Guards.before_step(step,active,func() -> Dictionary:
			calls[0]+=1
			return {"unexpected_downstream":true})
		mark("gate."+step+".refuses_before_downstream",response.has("error") and calls[0]==0)
	var loaded_calls := [0]
	var legacy := Guards.before_step("renderer_prepare_model",plain,func() -> Dictionary:
		loaded_calls[0]+=1
		return SceneIO.load_glb(source))
	mark("sceneio.legacy_raw_load_unchanged",not legacy.has("error") and loaded_calls[0]==1)
	if not legacy.has("error"):
		var actor := Model.new(); actor.root=legacy.scene; actor.base_root=actor.root.transform; actor.data=plain.duplicate(true)
		actor.data.metadata["import_height"]={"factor":"2","target_metres":"1.8288"}
		actor.inventory(actor.root)
		var before: Transform3D=actor.root.transform
		actor.apply(0,false,true,{})
		mark("model.legacy_diagnostic_not_active",actor.root.transform==before and actor.data.scale==1.0 and not actor.data.has("asset_basis"))
		actor.root.free()
	else: mark("model.legacy_diagnostic_not_active",false)
	for version in [3,4,5,6,7,8]:
		var document := {"schema_version":version,"world":{"objects":[active]}}
		mark("project.legacy"+str(version)+"_active_refuses",not Guards.project_error(document).is_empty())
	mark("project.schema9_refuses",not Guards.project_error({"schema_version":9}).is_empty())
	mark("project.stray_marker_refuses",not Guards.project_error({"schema_version":4,"basis_content_schema_version":4}).is_empty())
	mark("project.child_active_refuses",not Guards.project_error({"schema_version":6,"sequence_graph":{"assets":[{"scene":{"schema_version":4,"world":{"objects":[active]}}}]}}).is_empty())
	mark("project.legacy_absent_basis_unchanged",Guards.project_error({"schema_version":4,"world":{"objects":[plain]}}).is_empty())
	mark("sceneio.synthetic_source_sha_unchanged",FileAccess.get_sha256(source)==digest)
	var expected: int=1+Guards.STEPS.size()+2+6+5
	var result := {"format":"has_six_foot_boundary_result_1","checks":named.size(),"expected_checks":expected,"failures":failures,"complete_assertion_set":named.size()==expected,"named_checks":named,"scope":"Draft guards and real legacy Model/SceneIO only; current app entrypoints are not wired","owner_native_assets_read":false,"classification_run":false,"application_import_activation":false,"synthetic_glb_sha256":digest}
	var file := FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE)
	if not file: push_error("Cannot write fresh result"); quit(2); return
	file.store_string(JSON.stringify(result,"",true,true)); file.close()
	print("SIX_FOOT_BOUNDARY "+JSON.stringify({"checks":named.size(),"failures":failures}))
	quit(0 if failures==0 and named.size()==expected else 1)
