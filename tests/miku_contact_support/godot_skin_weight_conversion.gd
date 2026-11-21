extends RefCounted
# Exact CPU ArrayMesh readback profile, not shader equivalence or model repair.
# Godot 4.6-stable 89cea143987d564363e15d207438530651d943ac:
# modules/gltf/gltf_document.cpp:1622-1643; rendering_server.cpp:834-850,1644-1662.
const COMMIT="89cea143987d564363e15d207438530651d943ac"
const PROFILE="godot_4_6_stable_float32_four_weights_unorm16_1"
static func f32(value: float) -> float:
	var bytes:=PackedByteArray();bytes.resize(4);bytes.encode_float(0,value);return bytes.decode_float(0)
static func engine_supported(info: Dictionary) -> bool:
	# Exact engine build hash, not a version-prefix or arbitrary compatibility claim.
	return info.get("major")==4 and info.get("minor")==6 and info.get("patch")==0 and info.get("status")=="stable" and info.get("hash")==COMMIT
static func four(value) -> bool:
	if not value is Array or value.size()!=4:return false
	for item in value:
		if not (item is int or item is float) or not is_finite(float(item)) or float(item)<0. or float(item)>1.:return false
	return true
static func expected(source) -> Dictionary:
	if not four(source):return {"error":"finite_four_source_weights_required"}
	var raw: Array=[];var total:=0.
	for item in source:
		var value: float=float(item)
		if f32(value)!=value:return {"error":"decoded_source_float32_weights_required"}
		raw.append(value);total=f32(total+value)
	var normalized: Array=[];var packed: Array=[];var readback: Array=[]
	for value in raw:
		# C++ float additions/divisions/multiplication each round to float32.
		var weight: float=f32(value/total) if total>0. else value
		var product: float=f32(weight*65535.)
		var integer: int=int(clampf(product,0.,65535.))
		normalized.append(weight);packed.append(integer)
		# C++ readback divides by a double literal then assigns to Vector<float>.
		readback.append(f32(float(integer)/65535.))
	return {"profile":PROFILE,"raw_source_weights":raw,"source_float32_sum":total,"normalized_float32_weights":normalized,"packed_uint16_weights":packed,"readback_float32_weights":readback}
static func assess(source,imported,source_ids,imported_ids) -> Dictionary:
	var prediction:=expected(source)
	if prediction.has("error"):return prediction
	if not four(imported):return {"error":"finite_four_imported_weights_required"}
	if not source_ids is Array or not imported_ids is Array or source_ids.size()!=4 or imported_ids.size()!=4:return {"error":"exact_four_slot_identities_required"}
	for slot in range(4):
		if not source_ids[slot] is String or source_ids[slot].is_empty() or not imported_ids[slot] is String or source_ids[slot]!=imported_ids[slot]:return {"error":"source_imported_slot_identity_differs","slot":slot}
		if float(imported[slot])!=prediction.readback_float32_weights[slot]:return {"error":"exact_engine_weight_conversion_differs","slot":slot}
	prediction["exact_engine_conversion_matched"]=true
	prediction["raw_source_bit_identity_claimed"]=false
	prediction["shader_equivalence_qualified"]=false
	return prediction
