extends SceneTree
var scalar_bit_differences:=0
var float32_differences:=0
var structure_differences:=0
func compare(a,b) -> void:
	if a is Dictionary and b is Dictionary:
		if a.size()!=b.size():structure_differences+=1;return
		for key in a:
			if not b.has(key):structure_differences+=1
			else:compare(a[key],b[key])
	elif a is Array and b is Array:
		if a.size()!=b.size():structure_differences+=1;return
		for index in range(a.size()):compare(a[index],b[index])
	elif (a is float or a is int) and (b is float or b is int):
		if PackedFloat64Array([float(a)]).to_byte_array()!=PackedFloat64Array([float(b)]).to_byte_array():scalar_bit_differences+=1
		if PackedFloat32Array([float(a)]).to_byte_array()!=PackedFloat32Array([float(b)]).to_byte_array():float32_differences+=1
	elif typeof(a)!=typeof(b) or a!=b:structure_differences+=1
func _initialize() -> void:
	var folder: String=OS.get_cmdline_user_args()[0]
	var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
	var actual: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("actual-stamps-diagnostic.json")))
	var canonical_differences: Array=[];var raw_differences: Array=[];var probe47:={}
	for at in range(49):
		var left: String=expected.samples[str(at)];var right: String=actual[str(at)]
		if left!=right:raw_differences.append(at)
		var a=JSON.parse_string(left);var b=JSON.parse_string(right);compare(a,b)
		var ac:=JSON.stringify(a,"",true,true);var bc:=JSON.stringify(b,"",true,true)
		if ac!=bc:canonical_differences.append(at)
		if at==47:
			var ids: Array=a.keys();ids.sort();var id: String=ids[-1]
			probe47={"id":id,"expected_parsed_scale":a[id].root.scale,"actual_parsed_scale":b[id].root.scale,"expected_float64_bits":PackedFloat64Array([a[id].root.scale]).to_byte_array().hex_encode(),"actual_float64_bits":PackedFloat64Array([b[id].root.scale]).to_byte_array().hex_encode(),"expected_canonical_tail":ac.right(70),"actual_canonical_tail":bc.right(70)}
	var result:={"frames":49,"raw_text_differences":raw_differences,"canonical_text_differences":canonical_differences,"scalar_bit_differences_after_equal_parse_count":scalar_bit_differences,"float32_differences":float32_differences,"structure_differences":structure_differences,"frame47":probe47,"original_assertion_changed":false}
	FileAccess.open(folder.path_join("wire-probe-result.json"),FileAccess.WRITE).store_string(JSON.stringify(result,"",true,true))
	print("SCENARIO_D_WIRE_PROBE ",JSON.stringify(result));quit()
