extends RefCounted
# Generated geometry only; no owner assets.
const Fixture=preload("res://tests/secondary_fixture.gd")
static func json_integers(value):
	# Godot JSON parsing returns numeric floats. Restore exact integer tokens in
	# this generated-only fixture before the strict Python glTF helper reads it.
	if value is Dictionary:
		var result: Dictionary={}
		for key in value:result[key]=json_integers(value[key])
		return result
	if value is Array:
		var result: Array=[]
		for item in value:result.append(json_integers(item))
		return result
	if value is float and is_finite(value) and value==floor(value) and absf(value)<9007199254740992.:return int(value)
	return value
static func create(path: String) -> Error:
	var error: Error=Fixture.create(path)
	if error!=OK:return error
	var bytes: PackedByteArray=FileAccess.get_file_as_bytes(path)
	var length: int=bytes.decode_u32(12)
	var data: Dictionary=JSON.parse_string(bytes.slice(20,20+length).get_string_from_utf8())
	var source: Dictionary=data.extensions.VRMC_springBone
	for chain in source.springs:
		chain.erase("colliderGroups")
		for joint in chain.joints:joint.gravityPower=0.
	data.erase("extensions");data.erase("extensionsUsed")
	data["extras"]={"has_secondary_helpers_1":{"specVersion":"1.0","springs":source.springs}}
	return Fixture.write_glb(path,json_integers(data),bytes.slice(28+length))
