extends SceneTree
const Weights=preload("res://src/godot_skin_weight_conversion.gd")
var checks:=0
var failures:=0
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var info: Dictionary={"major":4,"minor":6,"patch":0,"status":"stable","hash":Weights.COMMIT}
	check(Weights.engine_supported(info),"exact pinned engine hash accepted")
	var other: Dictionary=info.duplicate();other.hash="89cea1439"
	check(not Weights.engine_supported(other),"short version hash cannot authenticate full source")
	other=info.duplicate();other.patch=1
	check(not Weights.engine_supported(other),"other engine patch refused")
	check(not Weights.engine_supported({}),"unknown engine profile refused")
	var one:=Weights.expected([1.,0.,0.,0.])
	check(one.packed_uint16_weights==[65535,0,0,0] and one.readback_float32_weights==[1.,0.,0.,0.],"unit source weight preserves exact endpoints")
	var half:=Weights.expected([.5,.5,0.,0.])
	check(half.packed_uint16_weights==[32767,32767,0,0],"half weights truncate rather than round")
	check(half.readback_float32_weights[0]==Weights.f32(32767./65535.) and half.readback_float32_weights[0]<.5,"readback preserves UNORM loss without renormalization")
	var uneven:=Weights.expected([.5,.25,.125,.125])
	check(uneven.packed_uint16_weights==[32767,16383,8191,8191],"four distinct slots remain in original order")
	var doubled:=Weights.expected([1.,.5,.25,.25])
	check(doubled.normalized_float32_weights==uneven.normalized_float32_weights and doubled.readback_float32_weights==uneven.readback_float32_weights,"glTF float32 normalization precedes UNORM packing")
	var zero:=Weights.expected([0.,0.,0.,0.])
	check(zero.source_float32_sum==0. and zero.readback_float32_weights==[0.,0.,0.,0.],"zero-total importer profile remains zero without invented influence")
	check(Weights.expected([.1,.2,.3,.4]).has("error"),"nondecoded double weights refuse exact float32 input profile")
	check(Weights.expected([Weights.f32(.1),Weights.f32(.2),Weights.f32(.3),Weights.f32(.4)]).has("readback_float32_weights"),"decoded float32 decimal inputs accepted")
	check(Weights.expected([true,0.,0.,0.]).has("error") and Weights.expected([false,0.,0.,0.]).has("error"),"boolean source weights refused")
	check(Weights.expected(["1",0.,0.,0.]).has("error"),"text source weight refused")
	check(Weights.expected([NAN,0.,0.,0.]).has("error") and Weights.expected([INF,0.,0.,0.]).has("error"),"nonfinite source weights refused")
	check(Weights.expected([-.1,.5,.5,.1]).has("error") and Weights.expected([1.1,0.,0.,0.]).has("error"),"source weights outside bounded profile refused")
	check(Weights.expected([1.,0.,0.]).has("error") and Weights.expected([1.,0.,0.,0.,0.]).has("error"),"three or five source slots refused")
	var ids: Array=["a","b","c","d"];var src: Array=[.5,.5,0.,0.];var imported: Array=half.readback_float32_weights.duplicate()
	var before:=var_to_bytes([src,imported,ids]);var valid:=Weights.assess(src,imported,ids,ids)
	check(valid.get("exact_engine_conversion_matched",false) and not valid.raw_source_bit_identity_claimed and not valid.shader_equivalence_qualified,"exact conversion is separate from raw identity and shader proof")
	check(var_to_bytes([src,imported,ids])==before,"oracle never mutates source or imported weights")
	check(Weights.assess(src,src,ids,ids).get("error")=="exact_engine_weight_conversion_differs","raw source weights cannot bypass quantization gate")
	var changed: Array=imported.duplicate();changed[0]=Weights.f32(changed[0]+1./65535.)
	check(Weights.assess(src,changed,ids,ids).has("error"),"one whole UNORM step difference refuses")
	changed=imported.duplicate();changed[0]+=1.e-15
	check(Weights.assess(src,changed,ids,ids).has("error"),"no arbitrary epsilon admits nonexact imported readback")
	check(Weights.assess(src,imported,ids,["b","a","c","d"]).get("error")=="source_imported_slot_identity_differs","equal summed joint weights cannot hide reordered slots")
	check(Weights.assess(src,imported,["a","b","c"],ids).has("error") and Weights.assess(src,imported,["a","b","", "d"],ids).has("error"),"missing or blank slot identities refused")
	print("GODOT_SKIN_WEIGHT_CONVERSION_UNIT ",JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
