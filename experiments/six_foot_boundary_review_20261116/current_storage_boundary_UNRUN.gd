extends SceneTree
# UNPARSED / UNRUN. Future root-owned metadata/file boundary diagnostic only.
# Uses actual current Storage/Model; no SceneIO, renderer, Model.apply or physics.
const Storage=preload("res://src/storage.gd")
const Model=preload("res://src/model.gd")
const World=preload("res://src/world_document.gd")
var checks: Dictionary={}
var failures:=0
var folder: String

func check(name: String,value: bool) -> void:
	checks[name]=value
	if not value:failures+=1

func put(path: String,text: String) -> bool:
	var stream:=FileAccess.open(path,FileAccess.WRITE)
	if stream==null:return false
	stream.store_string(text);stream.close();return true

func record(digest: String) -> Dictionary:
	return {"format":"studio_import_basis_1","purpose":"standard_complete_human_six_feet",
		"source_sha256":digest,"measured_from_sha256":digest,"factor":"0.9144",
		"target_metres":"1.8288","measured_converted_height":"2",
		"measurement_algorithm":"neutral_complete_human_height_1","reference_pose":"neutral_default",
		"classification":"verified_complete_human","decision":"automatic_qualified"}

func _initialize() -> void:call_deferred("run")
func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if args.size()!=1:push_error("Supply one fresh root-owned direct child of project output.");quit(2);return
	folder=ProjectSettings.globalize_path(args[0]).replace("\\","/").simplify_path()
	var boundary:=ProjectSettings.globalize_path("res://output").replace("\\","/").simplify_path()
	if folder.get_base_dir()!=boundary or not Storage.write_path_error(boundary,folder.get_file()).is_empty() or DirAccess.dir_exists_absolute(folder) or FileAccess.file_exists(folder):
		push_error("Fresh contained output folder required; existing data stays untouched.");quit(2);return
	if DirAccess.make_dir_recursive_absolute(folder)!=OK:quit(2);return
	var source:=folder.path_join("synthetic-not-a-model.glb")
	if not put(source,"Synthetic metadata fixture only; deliberately not a GLB."):quit(2);return
	var row:=World.object(source,"model","Synthetic boundary")
	row.asset_basis=record(row.sha256)
	check("current_model1_ignores_extra_basis",Model.validate(row,48).is_empty())
	var world:=World.empty();world.objects=[row]
	var portable:=World.portable(world)
	check("current_portable_preserves_extra_basis",portable.objects[0].asset_basis==row.asset_basis)
	var video:={"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":48}
	var camera:=[{"frame":0,"position":[0,0,3],"rotation_xyzw":[0,0,0,1],"fov":60,"interpolation":"linear"}]
	# decode_project requires managed bytes, not a real GLB geometry load.
	if DirAccess.make_dir_recursive_absolute(folder.path_join("assets"))!=OK:quit(2);return
	if not put(folder.path_join(portable.objects[0].path),"Synthetic metadata fixture only; deliberately not a GLB."):quit(2);return
	var plain:={"schema_version":4,"video":video,"camera_keys":camera,"layers":[],"audio":{},"editor":{"frame":0},"world":portable}
	var decoded:=Storage.decode_project(plain.duplicate(true),folder)
	check("current_storage4_accepts_extra_basis",not decoded.has("error"))
	check("current_storage4_returns_uninterpreted_basis",not decoded.has("error") and decoded.world.objects[0].asset_basis==row.asset_basis)
	var wrapped: Dictionary=plain.duplicate(true)
	wrapped.schema_version=9;wrapped.basis_content_schema_version=4;wrapped.import_basis_capability="studio_import_basis_1"
	check("current_storage_rejects_proper_schema9",Storage.decode_project(wrapped,folder).has("error"))
	# Genuine synthetic PNG only for the existing reference-sheet decoder.
	var picture:=Image.create(1,1,false,Image.FORMAT_RGBA8);picture.fill(Color.WHITE)
	var png:=folder.path_join("synthetic-reference.png")
	if picture.save_png(png)!=OK:quit(2);return
	var reference:={"format":"studio_reference_sheet_1","name":"Synthetic reference","source":png,"sha256":FileAccess.get_sha256(png)}
	var out:={};var prepared_folder:=folder.path_join("prepared-legacy7")
	# _manifest_out returns before directory_commit/Python launch; only owned
	# preparation copies occur. No renderer or model importer is called.
	var why:=Storage.save_project(prepared_folder,video,camera,[],"",0,{},{},{},true,world,{},[],{},out,reference)
	check("current_storage_prepares_legacy7",why.is_empty() and out.has("manifest"))
	if not why.is_empty() or not out.has("manifest"):finish();return
	check("current_writer_emits7_not9",out.manifest.schema_version==7 and out.manifest.content_schema_version==4)
	check("current_writer_keeps_extra_basis",out.manifest.world.objects[0].asset_basis==row.asset_basis)
	check("current_writer_does_not_add_basis_capability",not out.manifest.has("import_basis_capability") and not out.manifest.has("basis_content_schema_version"))
	var manifest_path:=prepared_folder.path_join("project.json")
	if not put(manifest_path,JSON.stringify(out.manifest)):quit(2);return
	check("current_readable_manifest_accepts_extra_basis7",Storage.readable_manifest(manifest_path))
	var legacy7:=Storage.decode_project(out.manifest.duplicate(true),prepared_folder)
	check("current_decode7_accepts_extra_basis",not legacy7.has("error"))
	check("current_decode7_preserves_uninterpreted_basis",not legacy7.has("error") and legacy7.world.objects[0].asset_basis==row.asset_basis)
	finish()

func finish() -> void:
	var result:={"format":"has_current_storage_basis_boundary_diagnostic_1","checks":checks.size(),"failures":failures,"named_checks":checks,
		"diagnostic_of_current_acceptance_not_product_feature_pass":true,"geometry_import_renderer_or_basis_activation":false,
		"directory_commit_worker_called":false,"source":"Current source52f63c9; this draft must be staged and reviewed by root before any future execution."}
	put(folder.path_join("result.json"),JSON.stringify(result,"\t"));quit(0 if failures==0 else 1)
