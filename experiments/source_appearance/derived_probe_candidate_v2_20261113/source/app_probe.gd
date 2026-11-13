extends RefCounted
# Output-only candidate. No runtime invocation is performed by loading this file.
const World=preload("res://src/world_document.gd")
const Timeline=preload("res://src/timeline.gd")
const Pixels=preload("res://src/cel_raster_reader.gd")
const CASE_KEYS=["nitori-skin-0","keiki-000"]
var _tree: SceneTree
var _app
var _result: Dictionary
var _job: Dictionary={}
var _startup: Dictionary={}
var _common: String=""

func _check(ok: bool,label: String) -> bool:
	_result.checks+=1
	if not ok:_result.failures+=1
	print(("PASS " if ok else "FAIL ")+label)
	return ok

func _normal(value: Variant) -> Variant:
	return JSON.parse_string(JSON.stringify(value,"",true,true))

func _path(value: String) -> String:
	var text:=ProjectSettings.globalize_path(value).replace("\\","/").simplify_path().trim_suffix("/")
	return text.to_lower() if OS.get_name()=="Windows" else text

func _transform(value: Transform3D) -> Array:
	return [value.basis.x.x,value.basis.x.y,value.basis.x.z,value.basis.y.x,value.basis.y.y,value.basis.y.z,value.basis.z.x,value.basis.z.y,value.basis.z.z,value.origin.x,value.origin.y,value.origin.z]

func _settled() -> void:
	for index in range(4):await _tree.process_frame
	await RenderingServer.frame_post_draw

func _startup_finished(value: Dictionary) -> void:
	_startup=value.duplicate(true)
	_startup["finished"]=true

func _operation_finished(action: String,success: bool) -> void:
	_job={"finished":true,"action":action,"success":success}

func _idle() -> bool:
	return _app.has_project.pid<=0 and not _app.has_project.project_loader.busy() and not _app.has_project.snapshot_writer.busy() and _app.source_import.pid<=0 and not _app.exporting

func _operation(action: String,invoke: Callable) -> bool:
	_job={}
	var callback:=Callable(self,"_operation_finished")
	_app.has_project.operation_finished.connect(callback)
	invoke.call()
	var until:=Time.get_ticks_msec()+150000
	while (not _job.get("finished",false) or not _idle()) and Time.get_ticks_msec()<until:await _tree.process_frame
	if _app.has_project.operation_finished.is_connected(callback):_app.has_project.operation_finished.disconnect(callback)
	await _settled()
	return _check(_job.get("finished",false) and _job.get("action")==action and _job.get("success",false) and _idle(),"normal HAS "+action+" emits successful completion and drains its workers")

func _actor(id: String) -> RefCounted:
	return _app.renderer.world_runtime.instance(id) if _app.renderer.world_runtime else null

func _binding_rows(actor: RefCounted) -> Array:
	var rows: Array=[]
	for id in actor.order:
		var value: Dictionary=actor.bones[id]
		rows.append({"id":str(id),"name":str(value.name),"index":int(value.index),"parent":actor.parent_id(id)})
	return rows

func _bone_transforms(actor: RefCounted) -> Dictionary:
	var values: Dictionary={}
	for id in actor.order:values[str(id)]=_transform(actor.bone_transform(id))
	return values

func _find_bone(actor: RefCounted,name: String) -> String:
	var matches: Array=[]
	for id in actor.order:
		if str(actor.bones[id].name)==name:matches.append(str(id))
	if not _check(matches.size()==1,"exact named posing bone is uniquely bound: "+name):return ""
	return str(matches[0])

func _native_contract(actor: RefCounted,item: Dictionary,label: String) -> bool:
	var ok:=_check(actor.data.sha256==item.glb_sha256 and FileAccess.get_sha256(actor.data.source)==item.glb_sha256,label+" retains exact managed GLB bytes")
	ok=_check(actor.data.metadata.get("native_parameters",{})==item.parameters,label+" retains the entire adjacent parameter report") and ok
	var native: Dictionary=item.parameters.get("native_parameters",{})
	var bones: Array=native.get("bones",[])
	ok=_check(bones.size()==int(item.bones),label+" report retains the recorded native bone count") and ok
	var bound_names: Dictionary={}
	for id in actor.order:bound_names[str(actor.bones[id].name)]=int(bound_names.get(str(actor.bones[id].name),0))+1
	var complete:=true
	for bone in bones:complete=complete and int(bound_names.get(str(bone.name),0))==1
	ok=_check(complete,label+" binds every native bone name once; runtime helper count is recorded separately") and ok
	return ok

func _write_json(path: String,value: Dictionary) -> bool:
	if not _check(not FileAccess.file_exists(path),"fresh evidence path: "+path.get_file()):return false
	var stream:=FileAccess.open(path,FileAccess.WRITE)
	if not _check(stream!=null,"evidence file opens: "+path.get_file()):return false
	stream.store_string(JSON.stringify(value,"  ",true,true)+"\n");stream.flush()
	var ok:=stream.get_error()==OK
	stream.close()
	return _check(ok,"evidence file writes: "+path.get_file())

func _content_observation(image: Image) -> Dictionary:
	var background:=image.get_pixel(0,0)
	var changed:=0
	for y in range(0,image.get_height(),4):
		for x in range(0,image.get_width(),4):
			var sample:=image.get_pixel(x,y)
			if maxf(absf(sample.r-background.r),maxf(absf(sample.g-background.g),absf(sample.b-background.b)))>.02:changed+=1
	return {"significant_content_samples":changed,"sample_step":4,"rgb_contrast_threshold":.02,"required_samples_exclusive":100}

func _capture(key: String,folder: String,mode: String) -> Dictionary:
	var image: Image=await _app.renderer.capture(_app.keys,_app.layers,_app.frame,true)
	if not _check(image!=null and not image.is_empty(),key+" "+mode+" native capture is readable"):return {}
	image.convert(Image.FORMAT_RGBA8)
	var target:=folder.path_join(key+"-"+mode+".png")
	if not _check(not FileAccess.file_exists(target),key+" "+mode+" PNG path is fresh"):return {}
	if not _check(image.save_png(target)==OK,key+" "+mode+" native PNG saves"):return {}
	_check(_app.renderer.native_readbacks==0,key+" "+mode+" capture releases its readback")
	var content:=_content_observation(image)
	if not _check(int(content.significant_content_samples)>100,key+" "+mode+" same captured image contains significant scene content"):return {}
	return {"content":content,"pixel_sha256":Pixels.digest_bytes(image.get_data()),"width":image.get_width(),"height":image.get_height(),"format":int(image.get_format()),"png":target,"png_sha256":FileAccess.get_sha256(target)}

func _writer(key: String,item: Dictionary,folder: String) -> Dictionary:
	var original:=str(item.input_glb)
	var parameter_path:=original.get_base_dir().path_join("parameters.json")
	if not _check(original.get_extension().to_lower()=="glb",key+" app probe adopts a prepared GLB without launching conversion"):return {}
	if not _check(FileAccess.file_exists(original) and FileAccess.get_sha256(original)==item.glb_sha256,key+" writer has its checksum-bound prepared GLB"):return {}
	if not _check(JSON.parse_string(FileAccess.get_file_as_string(parameter_path))==item.parameters,key+" writer has the matching adjacent report"):return {}
	if not _check(_app.new_project() and _app.current_world().objects.is_empty(),key+" starts an ordinary empty project"):return {}
	var before: Dictionary=World.portable(_app.current_world())
	var cameras: Array=_app.keys.duplicate(true)
	var count: int=_app.history.size()
	var error: String=_app.pose_editor.add_model(original,0,{})
	if not _check(error.is_empty(),key+" ordinary Add model succeeds: "+error):return {}
	var id: String=_app.last_import_id
	var actor: RefCounted=_actor(id)
	if not _check(actor!=null and _app.current_world().objects.size()==1,key+" adoption publishes one live instance"):return {}
	_native_contract(actor,item,key+" adopted")
	_check(actor.data.position==[0,0,0] and actor.data.rotation_xyzw==[0,0,0,1] and float(actor.data.scale)==1.,key+" ordinary adoption preserves prepared component coordinates without person sizing or placement")
	_check(_app.history.size()==count+1 and _app.history[-1].type=="world" and _app.keys==cameras,key+" import is one world Undo step and preserves shot keys")
	_check(_path(str(actor.data.metadata.get("import_source","")))==_path(original),key+" records the prepared GLB import origin")
	var adopted: Dictionary=World.portable(_app.current_world())
	var imported_root:=_transform(actor.root.global_transform)
	_app.undo();await _settled()
	_check(_actor(id)==null and World.portable(_app.current_world())==before and _app.history.size()==count,key+" one Undo removes only that adoption")
	_app.redo();await _settled()
	actor=_actor(id)
	if not _check(actor!=null,key+" Redo restores the same object identity"):return {}
	_check(World.portable(_app.current_world())==adopted and _app.history.size()==count+1,key+" Redo restores complete model data and report")
	_check(_transform(actor.root.global_transform)==imported_root,key+" import Undo/Redo preserves the root transform")
	_native_contract(actor,item,key+" redone")
	_app.world_selection.select_entity(id)
	_app.set_advanced(true);_app.set_frame(0)
	var editor=_app.pose_editor
	var binding:=_find_bone(actor,str(item.pose_bone_name))
	if binding.is_empty():return {}
	if not _check(editor.tree_items.has(binding),key+" posing tree contains the exact binding"):return {}
	editor.tree_items[binding].select(0);editor.tree.item_selected.emit()
	editor.operation.select(0);editor.snap.button_pressed=false;editor.auto_key.button_pressed=true
	for lock in editor.locks:lock.button_pressed=false
	editor.refresh_values()
	if not _check(editor.selected==binding,key+" normal bone selection targets the expected binding"):return {}
	var before_pose: Dictionary=actor.data.duplicate(true)
	var before_bone:=_transform(actor.bone_transform(binding))
	var pose_history: int=_app.history.size()
	editor.fields[0].value=20.;editor.apply_numeric();await _settled()
	actor=_actor(id)
	if not _check(actor!=null,key+" numeric pose edit retains the live actor"):return {}
	var posed: Dictionary=actor.data.duplicate(true)
	var authored: Array=actor.authored_keys()
	_check(_app.history.size()==pose_history+1 and authored.size()==1 and int(authored[0].frame)==0 and authored[0].pose.has(binding),key+" numeric20deg X edit authors one pose key and one Undo step")
	_check(_transform(actor.bone_transform(binding))!=before_bone and _transform(actor.root.global_transform)==imported_root,key+" named bone changes while the imported root stays fixed")
	_check(actor.data.metadata.native_parameters==item.parameters and FileAccess.get_sha256(actor.data.source)==item.glb_sha256,key+" posing preserves the native report and GLB")
	_app.undo();await _settled();actor=_actor(id)
	if not _check(actor!=null,key+" pose Undo retains the actor"):return {}
	_check(_normal(actor.data)==_normal(before_pose) and _transform(actor.bone_transform(binding))==before_bone,key+" pose Undo restores exact live data and bone transform")
	_app.redo();await _settled();actor=_actor(id)
	if not _check(actor!=null,key+" pose Redo retains the actor"):return {}
	_check(_normal(actor.data)==_normal(posed),key+" pose Redo restores exact authored data")
	_app.world_selection.select_entity(id);editor.frame_model()
	_app.keys=[Timeline.key(0,_app.renderer.camera.position,_app.renderer.camera.quaternion,_app.renderer.camera.fov)]
	var picture: Dictionary=await _capture(key,folder,"writer")
	if picture.is_empty():return {}
	var expected:={"format":"has_static_appearance_app_expected_1","key":key,"object_id":id,"glb_sha256":str(item.glb_sha256),"input_glb":original,"parameters":item.parameters,"portable_world":World.portable(_app.current_world()),"bindings":_binding_rows(actor),"authored_keys":actor.authored_keys(),"root_transform":_transform(actor.root.global_transform),"bone_transforms":_bone_transforms(actor),"camera_keys":_app.keys.duplicate(true),"video":_app.video.duplicate(true),"frame":_app.frame,"picture":picture,"project":_common.path_join(key+".has")}
	if not _check(not FileAccess.file_exists(expected.project),key+" packed project path is fresh"):return {}
	var saved: bool=await _operation("pack",func():_app.has_project.save_file(expected.project,"packed"))
	if not saved:return {}
	_check(_app.has_project.path==expected.project and _app.has_project.storage_mode=="packed" and not _app.dirty,key+" ordinary Save commits packed identity")
	_check(World.portable(_app.current_world())==expected.portable_world,key+" Save preserves the adopted posed world")
	expected["project_sha256"]=FileAccess.get_sha256(expected.project)
	if not _write_json(_common.path_join(key+"-expected.json"),expected):return {}
	return {"key":key,"object_id":id,"project":expected.project,"expected":_common.path_join(key+"-expected.json"),"picture":picture,"runtime_bones":actor.order.size(),"bindings":expected.bindings}

func _reader(key: String,item: Dictionary,folder: String) -> Dictionary:
	var path:=_common.path_join(key+"-expected.json")
	if not _check(FileAccess.file_exists(path),key+" reader finds writer evidence"):return {}
	var parsed=JSON.parse_string(FileAccess.get_file_as_string(path))
	if not _check(parsed is Dictionary and parsed.get("format")=="has_static_appearance_app_expected_1" and parsed.get("key")==key,key+" writer evidence has its exact case identity"):return {}
	var expected: Dictionary=parsed
	_check(not FileAccess.file_exists(str(item.input_glb)),key+" original owned GLB alias is unavailable to the fresh reader")
	if not _check(FileAccess.get_sha256(expected.project)==expected.project_sha256,key+" packed HAS bytes match the writer"):return {}
	if not _check(_app.new_project(),key+" reader resets through ordinary New"):return {}
	var opened: bool=await _operation("unpack",func():_app.has_project.open_file(expected.project))
	if not opened:return {}
	var actor: RefCounted=_actor(str(expected.object_id))
	if not _check(actor!=null,key+" packed Open restores the saved object identity"):return {}
	_native_contract(actor,item,key+" reopened")
	_check(_normal(World.portable(_app.current_world()))==expected.portable_world,key+" packed Open restores exact portable actor data and metadata")
	_check(_normal(_binding_rows(actor))==expected.bindings and _normal(actor.authored_keys())==expected.authored_keys,key+" packed Open restores exact bindings and authored pose keys")
	_check(_normal(_transform(actor.root.global_transform))==expected.root_transform and _normal(_bone_transforms(actor))==expected.bone_transforms,key+" packed Open restores exact root and bone transforms")
	_check(_normal(_app.keys)==expected.camera_keys and _normal(_app.video)==expected.video and _app.frame==int(expected.frame),key+" packed Open restores shot/video/frame")
	_check(_app.has_project.path==expected.project and _app.has_project.storage_mode=="packed" and not _app.dirty and _app.history.is_empty() and _app.redo_history.is_empty() and _app.world_selection.selected.is_empty(),key+" fresh packed Open is clean with empty history and selection")
	var source_path:=_path(actor.data.source)
	var cache_path:=_path(_app.has_project.cache_root)
	_check(source_path.begins_with(cache_path+"/") and _app.source_import.pid<=0,key+" runtime asset comes from fresh unpack cache without conversion")
	var picture: Dictionary=await _capture(key,folder,"reader")
	if picture.is_empty():return {}
	_check(picture.pixel_sha256==expected.picture.pixel_sha256 and picture.width==expected.picture.width and picture.height==expected.picture.height,key+" fresh packed render preserves exact writer pixels")
	_check(FileAccess.get_sha256(expected.project)==expected.project_sha256,key+" reader preserves the packed file bytes")
	return {"key":key,"object_id":expected.object_id,"project":expected.project,"picture":picture,"writer_picture":expected.picture,"runtime_bones":actor.order.size()}

func _case(manifest: Dictionary,key: String) -> Dictionary:
	var cases=manifest.get("cases",{})
	if cases is Dictionary:return cases.get(key,{})
	if cases is Array:
		for item in cases:
			if item is Dictionary and item.get("key")==key:return item
	return {}

func _cleanup() -> void:
	if not is_instance_valid(_app):return
	if not _idle():
		_app.has_project.cancel()
		var until:=Time.get_ticks_msec()+15000
		while not _idle() and Time.get_ticks_msec()<until:await _tree.process_frame
		if _app.has_project.pid>0 and OS.is_process_running(_app.has_project.pid):OS.kill(_app.has_project.pid)
		if _app.has_project.project_loader.busy():_app.has_project.project_loader.finish()
		if _app.has_project.snapshot_writer.busy():_app.has_project.snapshot_writer.finish()
		await _settled()
	_check(_idle(),"app probe drains only its owned project workers before teardown")
	_check(_app.renderer.native_readbacks==0,"app probe has no retained native readback at teardown")
	_app.free();_app=null
	await _tree.process_frame

func run(tree: SceneTree,manifest: Dictionary,folder: String,mode: String) -> Dictionary:
	_tree=tree;_common=folder.get_base_dir();_result={"checks":0,"failures":0,"observations":[],"app_cases":[],"mode":mode,"scope":"ordinary baked-GLB adoption/history/pose/packed replay; no native variant-selection UI, native bundle packing, movie or artist acceptance"}
	if not _check(mode in ["writer","reader"],"app probe mode is writer or reader"):return _result
	DirAccess.make_dir_recursive_absolute(folder)
	_app=load("res://main.tscn").instantiate()
	_app.recovery_root=folder.path_join("recovery")
	_app.recent_path=folder.path_join("recents.json")
	_app.display_prefs_path=folder.path_join("display.cfg")
	_startup={};_app.startup_recovery_finished.connect(_startup_finished)
	_tree.root.add_child(_app)
	_app.autosave_enabled.button_pressed=false
	_app.has_project.cache_root=folder.path_join("has-cache")
	_app.reference_sheet.cache_root=folder.path_join("reference-cache")
	_app.workspace_layout.path=folder.path_join("workspace.json")
	var testing: bool="--script" in OS.get_cmdline_args()
	for argument in OS.get_cmdline_user_args():
		if argument.contains("smoke"):testing=true
	if not testing:
		var until:=Time.get_ticks_msec()+30000
		while not _startup.get("finished",false) and Time.get_ticks_msec()<until:await _tree.process_frame
		if not _check(_startup.get("finished",false) and not _startup.get("restored",true) and not _startup.get("cancelled",true),"ordinary fresh startup recovery finishes before the app probe"):
			await _cleanup();return _result
	await _settled()
	for key in CASE_KEYS:
		var item: Dictionary=_case(manifest,key)
		if not _check(not item.is_empty() and item.has_all(["input_glb","glb_sha256","parameters","pose_bone_name","bones"]),"manifest supplies exact app case "+key):continue
		if not _check(_idle(),key+" starts with no pending operation"):break
		var observation: Dictionary={}
		if mode=="writer":observation=await _writer(key,item,folder)
		else:observation=await _reader(key,item,folder)
		_result.observations.append(observation)
		if not observation.is_empty():_result.app_cases.append(key)
	await _cleanup()
	return _result
