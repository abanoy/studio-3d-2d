extends "res://tests/helper_preview_gpu.gd"
# SOURCE-ONLY native existing-joint case. Root must stage the retained inputs
# into a fresh owned GPU folder, protect originals/copies by hash/size/nsmtime,
# and pass source, parameters, expected_native_sha256, expected_native_bytes,
# native_case. Input byte/hash constants also bind the parameter sidecar.
# This deliberately does not reuse the synthetic Head2/morph3 preparation.
const NATIVE_CASE="backhair-existing-chain"
const SOURCE_SHA="4d62236d5c34468ea1f91c43089d6ce3c193be27b8460d53ea8d91d2238ab7b5"
const SOURCE_BYTES=7273728
const PARAMETERS_SHA="f4e1850d9f4fa9359a72d43f3c945aaf61a1bd726538b025da31c4fa5f8071ba"
const CONFIGURED=[11,10,9]
const CENTER=16
const ENDPOINT=103

func ints(value) -> Array:
	var result: Array=[]
	if not value is Array:return result
	for number in value:
		if not (number is int or number is float) or not is_finite(number) or number!=floor(number):return []
		result.append(int(number))
	return result

func file_identity(path: String) -> Dictionary:
	var file:=FileAccess.open(path,FileAccess.READ)
	if not file:return {}
	var count:=file.get_length();file.close()
	return {"bytes":count,"modified_seconds":FileAccess.get_modified_time(path),"sha256":FileAccess.get_sha256(path)}

func parts(path: String) -> Dictionary:
	var file:=FileAccess.open(path,FileAccess.READ)
	if not file:return {}
	var size:=file.get_length()
	if size<28 or size>128*1024*1024:file.close();return {}
	var head:=file.get_buffer(20)
	var json_bytes:=int(head.decode_u32(12))
	if head.decode_u32(0)!=0x46546c67 or head.decode_u32(4)!=2 or head.decode_u32(8)!=size or head.decode_u32(16)!=0x4e4f534a or json_bytes>16*1024*1024 or json_bytes>size-28:file.close();return {}
	file.seek(20+json_bytes)
	var parsed:=Adapter.document(path);var document=parsed.get("document")
	var bin_head:=file.get_buffer(8)
	var bin_bytes:=int(bin_head.decode_u32(0))
	if not document is Dictionary or bin_head.decode_u32(4)!=0x004e4942 or bin_bytes!=size-file.get_position():file.close();return {}
	var hash:=HashingContext.new();hash.start(HashingContext.HASH_SHA256);hash.update(file.get_buffer(bin_bytes));file.close()
	return {"document":document,"bin_sha256":hash.finish().hex_encode(),"bin_bytes":bin_bytes}

func wait_native_idle() -> bool:
	var until:=Time.get_ticks_msec()+30000
	while is_instance_valid(helper.window) and (helper.pid>0 or helper.assessment.is_empty()) and Time.get_ticks_msec()<until:await process_frame
	await settled()
	return is_instance_valid(helper.window) and helper.pid<=0 and not helper.assessment.is_empty()

func open_native() -> bool:
	helper=app.physics_editor.helper_editor;host=helper.pending_preview;helper.open(true)
	if not await wait_native_idle():check(false,"native ordinary helper inspection completes");return false
	var selected:=-1
	for index in helper.assessment.get("regions",[]).size():
		var row: Dictionary=helper.assessment.regions[index];var chain: Dictionary=row.get("existing_chain",{})
		if int(row.get("node",-1))==80 and int(row.get("primitive",-1))==1 and int(row.get("component",-1))==1 and int(chain.get("center_node",-1))==CENTER and ints(chain.get("joint_nodes"))==CONFIGURED:
			if selected>=0:check(false,"native review region is unambiguous");return false
			selected=index
	check(selected>=0,"actual assessment identifies retained region80/1/1 by exact original source-node chain")
	if selected<0:return false
	helper.parts.select(selected);helper.parts.item_selected.emit(selected)
	if not await wait_native_idle():check(false,"chosen native region finishes preview");return false
	# Use the ordinary existing-joint control; list focus alone does not opt in.
	helper.existing_toggle.button_pressed=true
	if not await wait_review():check(false,"ordinary Use existing joints review completes");return false
	var chain: Dictionary=helper.preview.get("existing_chain",{})
	check(helper.preview.get("mode")=="existing_joints" and int(chain.get("center_node",-1))==CENTER and ints(chain.get("joint_nodes"))==CONFIGURED,"ordinary review configures exactly original joints11/10/9 without name matching")
	if helper.preview.get("mode")!="existing_joints" or ints(chain.get("joint_nodes"))!=CONFIGURED:return false
	check(helper.preview.get("affected_vertices",0)>0 and not helper.preview.get("affected_regions",[]).is_empty(),"existing-joint review discloses actual shared weighted regions")
	helper.include_toggle.button_pressed=true
	if not await wait_review():check(false,"checked native group finishes reviewed inclusion");return false
	check(helper.included.size()==1 and helper.included.values()[0].valid,"native shared setup is one checked reviewed Apply membership")
	return helper.included.size()==1 and helper.included.values()[0].valid

func native_case() -> void:
	var source_path: String=str(request.get("source",""));var parameter_path: String=str(request.get("parameters",""))
	var inputs_ok: bool=request.get("native_case")==NATIVE_CASE and source_path.is_absolute_path() and parameter_path.is_absolute_path() and request.get("expected_native_sha256")==SOURCE_SHA and request.get("expected_native_bytes")==SOURCE_BYTES and FileAccess.get_sha256(source_path)==SOURCE_SHA and FileAccess.get_sha256(parameter_path)==PARAMETERS_SHA
	check(inputs_ok,"explicit native case admits only the retained checksum-bound GLB and parameter copies")
	if not inputs_ok:return
	var source_file:=file_identity(source_path);var parameters_file:=file_identity(parameter_path)
	check(source_file.get("bytes")==SOURCE_BYTES and parameters_file.get("bytes")==28797,"native owned inputs retain exact retained byte counts")
	if source_file.get("bytes")!=SOURCE_BYTES or parameters_file.get("bytes")!=28797:return
	await fresh_app("native-backhair")
	app.helper_preview_runtime_path=request.python;app.helper_preview_work_root=folder.path_join("native-backhair-helper-work")
	check(OS.get_user_data_dir().replace("\\","/").ends_with(str(request.profile)),"native case uses the unique private preference profile")
	var source: RefCounted=await add_source(source_path)
	if source==null:return
	var bindings: Dictionary=source.root.get_meta("has_source_bones",{});var center_id: String=bindings.get(CENTER,"");var first_id: String=bindings.get(CONFIGURED[0],"")
	check(not center_id.is_empty() and not first_id.is_empty() and source.bones.has(center_id) and source.bones.has(first_id),"native center and first configured joint join actual imported source-node bindings")
	if center_id.is_empty() or first_id.is_empty() or not source.bones.has(center_id) or not source.bones.has(first_id):return
	# Place the camera on the horizontal side where the actual chain leaves its
	# center. This is a view choice, not a transform fitted to an oracle result.
	var center: Vector3=source.bone_transform(center_id).origin;var outward: Vector3=source.bone_transform(first_id).origin-center;outward.y=0.
	check(outward.length()>.00001,"native chain provides a nondegenerate source-derived viewing side")
	if outward.length()<=.00001:return
	var camera: Camera3D=app.renderer.camera;camera.global_position=center+outward.normalized()*1.35+Vector3(0,.1,0);camera.look_at(center+Vector3(0,-.12,0),Vector3.UP);camera.fov=45
	app.keys=[Timeline.key(0,camera.position,camera.quaternion,camera.fov)];app.renderer.evaluate(app.keys,app.frame);app.pose_editor.apply_frame();app.changed();await settled()
	var before:=document_state();var original_pose:=source_pose(source);var original: Image=await native_image(false);var meshes: Dictionary={}
	for mesh in owned_source_meshes(source):meshes[mesh]=mesh.visible
	if not await open_native():return
	var included: Dictionary=helper.included.duplicate(true);var reviewed: Dictionary=helper.request.duplicate(true)
	if not await start_pending():return
	var candidate: RefCounted=host.candidate;var candidate_sha: String=host.last_receipt.candidate.identity.sha256
	check(FileAccess.get_sha256(candidate.data.source)==candidate_sha and host.catalog.source_sha256==candidate_sha,"native current candidate is bound to its actual trusted completion SHA, not historical default-option output")
	check(host.last_receipt.operations.size()==1 and host.last_receipt.operations[0].mode=="existing_joints" and ints(host.last_receipt.operations[0].configured_source_nodes)==CONFIGURED and ints(host.last_receipt.operations[0].candidate_helper_nodes)==[ENDPOINT],"prepared native operation retains original joints11/10/9 and adds only endpoint103")
	var old:=parts(source.data.source);var derived:=parts(candidate.data.source)
	check(not old.is_empty() and not derived.is_empty(),"independent bounded GLB chunk reader sees source and candidate")
	if old.is_empty() or derived.is_empty():return
	check(old.document.nodes.size()==ENDPOINT and derived.document.nodes.size()==ENDPOINT+1,"native candidate contains all103 originals plus exactly one terminal node")
	var preserved: bool=old.bin_sha256==derived.bin_sha256 and old.bin_bytes==derived.bin_bytes
	for key in ["accessors","bufferViews","buffers","meshes","skins","materials","images","textures","samplers"]:preserved=preserved and old.document.get(key)==derived.document.get(key)
	check(preserved,"native existing-joint candidate independently preserves binary payload, skins, weights, morphs and material descriptors")
	if not preserved:return
	var moving: Array=[]
	for node in CONFIGURED:
		var original_id: String=bindings.get(node,"");var mapped: String=host.candidate_prepared.bone_id_map.get(original_id,"")
		check(not mapped.is_empty() and candidate.bones.has(mapped) and candidate.root.get_meta("has_source_bones",{}).get(node,"")==mapped,"configured original source node"+str(node)+" maps to an actual candidate skin bone")
		if not mapped.is_empty() and candidate.bones.has(mapped):moving.append(mapped)
	check(moving.size()==3 and candidate.order.size()==source.order.size(),"motion proof targets three original rotating skin bones rather than the unweighted endpoint")
	if moving.size()!=3 or candidate.order.size()!=source.order.size():return
	var selected:=Groups.filter(host.catalog,host.wind_ids.keys());var chain_found:=false
	for chain in selected.get("chains",[]):
		var nodes: Array=[]
		for joint in chain.joints:nodes.append(int(joint.binding.source_node))
		if nodes==CONFIGURED+[ENDPOINT]:chain_found=true
	check(chain_found and host.candidate_prepared.operation_group_ids.size()==1,"checked candidate-bound actual motion group contains the exact native chain and endpoint")
	if not chain_found or host.candidate_prepared.operation_group_ids.size()!=1:return
	check(helper.included==included and helper.request==reviewed and document_matches(before) and source_pose(source)==original_pose,"visible native try-out preserves checked Apply setup, original pose and authored document")
	var initial_image: Image=await native_image(false);var initial: Dictionary=host.player.simulation.latest.duplicate(true)
	for i in 90:await physics_frame
	var maximum:=angle(initial,host.player.simulation.latest,moving);var pixels:=changed_bytes(initial_image,await native_image(false))
	metrics["native_original_skin_bone_max_angle"]=maximum;metrics["native_same_candidate_changed_image_bytes"]=pixels;metrics["native_candidate_sha256"]=candidate_sha
	check(maximum>.001,"actual original native weighted joints move before Apply")
	check(pixels>100,"two native images of the same candidate show visible weighted deformation")
	check(helper.included==included and document_matches(before) and source_pose(source)==original_pose,"running native motion never authors changes to original joint poses or Apply membership")
	root.get_texture().get_image().save_png(folder.path_join("pending-helper-native-backhair-main.png"));helper.window.get_texture().get_image().save_png(folder.path_join("pending-helper-native-backhair-window.png"))
	helper.try_wind.button_pressed=false;await settled()
	assert_restored(before,original_pose,source,meshes,"native Backhair Off")
	check(changed_bytes(original,await native_image(false))==0,"native Backhair Off restores exact original native scene pixels")
	check(file_identity(source_path)==source_file and file_identity(parameter_path)==parameters_file,"native owned input copies keep exact bytes, SHA and available timestamp")
	check(app.renderer.native_readbacks==0,"native case drains every native readback scope")
	helper.close();app.free();app=null;helper=null;host=null;await settled(8)
	check(root.get_child_count()==0,"native case teardown releases all imported and temporary roots")

func run() -> void:
	setup_request()
	await native_case()
	await finish("PENDING_HELPER_NATIVE_GPU",{"prototype_only":false,"native_fidelity":false,"new_movies":false,"native_existing_joint_case":true})
