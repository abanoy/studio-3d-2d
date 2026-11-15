extends SceneTree
func _initialize() -> void:
	var decoded=JSON.parse_string("{\"number\":-0.0}")
	var data:=PackedByteArray();data.resize(4);data.encode_float(0,float(decoded.number))
	print("SIGNED_ZERO_PROBE "+JSON.stringify({"json_variant_type":typeof(decoded.number),"float32_word":data.decode_u32(0),"equals_numeric_zero":float(decoded.number)==0.0}))
	var serialized:=JSON.stringify(decoded)
	var roundtrip=JSON.parse_string(serialized)
	data.encode_float(0,float(roundtrip.number))
	print("SIGNED_ZERO_ROUNDTRIP "+JSON.stringify({"serialized":serialized,"float32_word":data.decode_u32(0)}))
	serialized=JSON.stringify(decoded,"",true,true)
	roundtrip=JSON.parse_string(serialized)
	data.encode_float(0,float(roundtrip.number))
	print("SIGNED_ZERO_FULL_PRECISION "+JSON.stringify({"serialized":serialized,"float32_word":data.decode_u32(0)}))
	quit(0)
