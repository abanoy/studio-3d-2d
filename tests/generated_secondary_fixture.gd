extends RefCounted
# Generated geometry only; no owner assets.
const Fixture=preload("res://tests/secondary_fixture.gd")
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
	return Fixture.write_glb(path,data,bytes.slice(28+length))
