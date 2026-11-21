extends SceneTree
const Binding=preload("res://src/miku_skin_binding.gd")
const Context=preload("res://src/miku_saved_context.gd")
var checks:=0
var failures:=0
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func _initialize() -> void:
	create_timer(10).timeout.connect(func():quit(2));call_deferred("run")
func run() -> void:
	var raw: Array=[1,0,0,0,0,1,0,0,0,0,1,0,2,3,4,1]
	var affine:=Binding.matrix(raw)
	check(not affine.has("error") and affine.transform*Vector3.ONE==Vector3(3,4,5),"column-major source affine matrix is read without repair")
	var invalid: Array=raw.duplicate();invalid[3]=1
	check(Binding.matrix(invalid).has("error"),"nonaffine source matrix refuses")
	invalid=raw.duplicate();invalid[0]=NAN
	check(Binding.matrix(invalid).has("error"),"nonfinite source matrix refuses")
	invalid=raw.duplicate();invalid[0]=0
	check(Binding.matrix(invalid).has("error"),"singular source matrix refuses")
	check(Binding.difference(Transform3D.IDENTITY,Transform3D(Basis.IDENTITY,Vector3(.1,0,0)))>.099,"calibration metric includes translated frame error")
	var q:=Quaternion(Vector3.FORWARD,PI/2)
	var trs:=Binding.local_frame({"translation":[2,0,0],"rotation":[q.x,q.y,q.z,q.w],"scale":[2,3,4]})
	check(not trs.has("error") and (trs.transform*Vector3.RIGHT).distance_to(Vector3(2,-2,0))<.00001,"source TRS uses local scale before rotation")
	check(Binding.local_frame({"rotation":[0,0,0,2]}).has("error"),"nonunit source quaternion is refused rather than normalized")
	var worlds:=Binding.source_worlds({"nodes":[{"translation":[1,0,0],"children":[1]},{"translation":[0,2,0]}]})
	check(not worlds.has("error") and worlds.world[1].origin==Vector3(1,2,0),"source parent graph composes exact frames")
	check(Binding.source_worlds({"nodes":[{"children":[1]},{"children":[0]}]}).has("error"),"source graph cycle refuses")
	check(Binding.source_worlds({"nodes":[{"children":[2]},{"children":[2]},{}]}).has("error"),"multiple source parents refuse")
	var binary:=PackedByteArray();binary.resize(24)
	for i in range(6):binary.encode_float(i*4,float(i+1))
	var decoded: Dictionary={"doc":{"buffers":[{"byteLength":24}],"bufferViews":[{"byteLength":24}],"accessors":[{"bufferView":0,"componentType":5126,"type":"VEC3","count":2}]},"binary":binary}
	var rows:=Binding.accessor(decoded,0,"VEC3",5126,2)
	check(not rows.has("error") and rows.rows==[[1.,2.,3.],[4.,5.,6.]],"dense aligned accessor preserves exact row order")
	var altered: Dictionary=decoded.duplicate(true);altered.doc.accessors[0]["sparse"]={}
	check(Binding.accessor(altered,0,"VEC3",5126,2).has("error"),"sparse accessor refuses instead of guessing")
	altered=decoded.duplicate(true);altered.doc.accessors[0]["normalized"]=true
	check(Binding.accessor(altered,0,"VEC3",5126,2).has("error"),"normalized accessor refuses")
	altered=decoded.duplicate(true);altered.doc.accessors[0]["byteOffset"]=4
	check(Binding.accessor(altered,0,"VEC3",5126,2).has("error"),"accessor cannot escape its source view")
	check(Binding.accessor(decoded,0,"VEC4",5126,2).has("error") and Binding.accessor(decoded,0,"VEC3",5126,1).has("error"),"accessor shape and row bounds are exact")
	check(Binding.glb(PackedByteArray([1,2,3])).has("error"),"truncated source GLB refuses")
	# Regression: a saved dense 156-channel pose has SIX changed channels, not six entries.
	var baseline: Dictionary={}
	for i in range(156):baseline["joint_"+str(i)]={"position":[0.,0.,0.],"rotation_xyzw":[0.,0.,0.,1.]}
	var draft: Dictionary=baseline.duplicate(true)
	for i in range(6):draft["joint_"+str(i)].position[0]=.1
	var data: Dictionary={"sha256":Context.MIKU_SHA,"format":"studio_model_6","draft_frame":0,"pose":draft.duplicate(true),"body_base_pose":baseline.duplicate(true)}
	var original:=var_to_bytes([data,draft,baseline]);var admitted:=Context.assess(data,draft,baseline,0,false,false)
	check(admitted.accepted and admitted.stored_pose_channels==156 and admitted.changed_draft_channels==6,"dense saved pose admits six actual changed channels")
	check(var_to_bytes([data,draft,baseline])==original,"context assessment never changes authored inputs")
	var changed: Dictionary=data.duplicate(true);changed.pose={}
	for i in range(6):changed.pose["joint_"+str(i)]=draft["joint_"+str(i)].duplicate(true)
	check(not Context.assess(changed,changed.pose,baseline,0,false,false).accepted,"six total stored entries do not match the dense saved case")
	check(not Context.assess(data,baseline,baseline,0,false,false).accepted,"no changed draft channels cannot pose as the saved edit")
	var seven: Dictionary=draft.duplicate(true);seven.joint_6.position[0]=.2;changed=data.duplicate(true);changed.pose=seven
	check(not Context.assess(changed,seven,baseline,0,false,false).accepted,"seven changed channels refuse the exact saved case")
	check(not Context.assess(data,draft,baseline,43,false,false).accepted,"unrelated frame43 cannot replace saved framezero")
	changed=data.duplicate(true);changed.draft_frame=43
	check(not Context.assess(changed,draft,baseline,0,false,false).accepted,"saved draft frame must itself match framezero")
	check(not Context.assess(data,draft,baseline,0,true,false).accepted,"running physics is refused independently")
	check(not Context.assess(data,draft,baseline,0,false,true).accepted,"active Record is refused independently")
	check(not Context.assess(data,draft,baseline,false,false,false).accepted,"boolean frame is not numeric framezero")
	changed=data.duplicate(true);changed.body_base_pose.erase("joint_155")
	check(not Context.assess(changed,draft,baseline,0,false,false).accepted,"missing baseline channel refuses")
	var alias: Dictionary=baseline.duplicate(true);alias["foreign"]=alias.joint_155;alias.erase("joint_155")
	check(not Context.assess(data,draft,alias,0,false,false).accepted,"same-size altered channel domain refuses")
	var foreign: Dictionary=draft.duplicate(true);foreign.joint_0.position[0]=.3
	check(not Context.assess(data,foreign,baseline,0,false,false).accepted,"sampled editing pose must equal the saved dense draft")
	foreign=baseline.duplicate(true);foreign.joint_100.position[0]=.4
	check(not Context.assess(data,draft,foreign,0,false,false).accepted,"sampled Timeline pose must equal saved body baseline")
	check(not Context.assess(data,draft,baseline,0,0,false).accepted,"numeric idle flag is not an explicit boolean")
	changed=data.duplicate(true);changed.sha256="other"
	check(not Context.assess(changed,draft,baseline,0,false,false).accepted,"different native asset cannot satisfy saved context")
	# Actual JSON roundtrip on ALL dense accessor structural fields, not only enum helper.
	for component in [5121,5123]:
		var bytes_per_slot:=1 if component==5121 else 2
		var data_bytes:=PackedByteArray();data_bytes.resize(8*bytes_per_slot)
		for index in range(8):
			if component==5121:data_bytes[index]=index
			else:data_bytes.encode_u16(index*2,index)
		var source_doc: Dictionary={"nodes":[{}],"buffers":[{"byteLength":data_bytes.size()}],"bufferViews":[{"buffer":0,"byteOffset":0,"byteLength":data_bytes.size(),"byteStride":4*bytes_per_slot}],"accessors":[{"bufferView":0,"byteOffset":0,"componentType":component,"type":"VEC4","count":2,"normalized":false}]}
		var parsed_doc: Dictionary=JSON.parse_string(JSON.stringify(source_doc))
		var canonical:=Binding.joint_component(parsed_doc.accessors[0].componentType)
		var parsed_dense:=Binding.accessor({"doc":parsed_doc,"binary":data_bytes},0.,"VEC4",int(canonical.get("component",-1)),2)
		check(typeof(parsed_doc.accessors[0].componentType)==TYPE_FLOAT and not canonical.has("error") and not parsed_dense.has("error") and parsed_dense.rows==[[0,1,2,3],[4,5,6,7]],"real_JSON_dense_unsigned_accessor_"+str(component)+"_preserves_exact_slots")
	check(Binding.joint_component(5121).component==5121,"native_integer_unsigned_byte_enum_remains_supported")
	check(Binding.joint_component(5123).component==5123,"native_integer_unsigned_short_enum_remains_supported")
	check(Binding.joint_component(5122).has("error"),"signed_short_joint_profile_still_refuses")
	check(Binding.joint_component(5125).has("error"),"unsigned_int_joint_profile_still_refuses")
	check(Binding.joint_component(5121.5).has("error"),"fractional_joint_enum_refuses_without_truncation")
	check(Binding.joint_component(false).has("error") and Binding.joint_component(true).has("error"),"boolean_joint_enum_is_not_numeric")
	check(Binding.joint_component("5121").has("error"),"text_joint_enum_is_not_coerced")
	check(Binding.joint_component(NAN).has("error") and Binding.joint_component(INF).has("error"),"nonfinite_joint_enum_refuses")
	var private_row: Dictionary={"primitive":2,"vertex":7,"failed_bone_id":"a","source_position":[1.,2.,3.],"imported_position":[1.,2.,3.],"source_indices":[0,1,2,3],"source_weights":[.5,.25,.125,.125],"source_joint_ids":["a","b","c","d"],"imported_indices":[0,1,2,3],"imported_weights":[.50001,.24999,.125,.125],"imported_joint_ids":["a","b","c","d"],"expected_summed_weights":{"a":.5,"b":.25,"c":.125,"d":.125},"actual_summed_weights":{"a":.50001,"b":.24999,"c":.125,"d":.125},"unlisted_full_source":[1,2,3,4,5]}
	var row_before:=var_to_bytes(private_row);var diagnostic:=Binding.influence_failure(private_row)
	check(diagnostic.error=="imported_source_influence_weight_differs" and diagnostic.private_influence_diagnostic.slot_count==4 and diagnostic.private_influence_diagnostic.source_weight_sum==1. and diagnostic.private_influence_diagnostic.same_positive_influence_domain,"private diagnostic keeps exact fixed-row weights sums and identity without changing refusal")
	check(var_to_bytes(private_row)==row_before and not diagnostic.private_influence_diagnostic.has("unlisted_full_source") and Binding.float32_hex(.5)=="0000003f","diagnostic is immutable whitelisted and records exact float32 bits")
	private_row.source_weights[0]=.75
	check(diagnostic.private_influence_diagnostic.source_weights[0]==.5 and diagnostic.private_influence_diagnostic.normalization_applied==false and diagnostic.private_influence_diagnostic.coordinate_reorder_applied==false,"diagnostic row is detached and applies no weight or coordinate repair")
	private_row.source_weights.append(.1)
	check(Binding.influence_failure(private_row).has("private_diagnostic_error"),"diagnostic refuses more than four slots instead of copying unbounded geometry")
	print("MIKU_SKIN_BINDING_UNIT ",JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
