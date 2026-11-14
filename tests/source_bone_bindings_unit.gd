extends SceneTree
# Authored structural controls, not a SourceIO/native conversion or solver test.
const Bindings = preload("res://src/source_bone_bindings.gd")
const Model = preload("res://src/model.gd")
const SceneIO = preload("res://src/scene3d.gd")
const NATIVE = "8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716"
const GLB_SHA = "39637fa34e53c81708329ab963659e8100a285a92e25a22a92ab5e708c0154c1"
const CATALOGUE_SHA = "782f1dfbefb1b61078468730c634a6ec696a414f0034dd2b6b3ecc6bc058474d"
const JIGGLE_SHA = "ffe01c326a8ba54a57974f8257f716cffe1ea6c6f6e36cb73da0780e1ddc30c4"
const PROOF_SHA = "3f7f4ab5c1ec58f6c987de24ebb907ae5e8e0427fa8f7e109418fcae5fd6307b"
const BAD_SLOT_PROOF = "c7e84f05cda8baba273c1364fe76153f2aac315fafe69fd1f717b4d314bda9bf"
const BAD_CHUNKS_SHA = "95e0c8785860cfce8ad34a60ff58feef6c65d22ea6a6d318d9523ddfdd0ff934"
const BAD_CHUNKS_PROOF = "5c8388cf1ec98fbf314ed4fec08766e122487a3dc504fc0c1eaa9d92bd8fa639"
# Golden bytes/digests were generated independently with Python struct/hashlib.
const GOLDEN_GLB = """Z2xURgIAAACQJAAAwBIAAEpTT057ImFjY2Vzc29ycyI6W3siYnVmZmVyVmlldyI6MCwiY29tcG9uZW50VHlwZSI6NTEyNiwiY291bnQiOjMsIm1heCI6WzEs
MSwwXSwibWluIjpbMCwwLDBdLCJ0eXBlIjoiVkVDMyJ9LHsiYnVmZmVyVmlldyI6MSwiY29tcG9uZW50VHlwZSI6NTEyMywiY291bnQiOjMsInR5cGUiOiJW
RUM0In0seyJidWZmZXJWaWV3IjoyLCJjb21wb25lbnRUeXBlIjo1MTI2LCJjb3VudCI6MywidHlwZSI6IlZFQzQifSx7ImJ1ZmZlclZpZXciOjMsImNvbXBv
bmVudFR5cGUiOjUxMjMsImNvdW50IjozLCJ0eXBlIjoiU0NBTEFSIn0seyJidWZmZXJWaWV3Ijo0LCJjb21wb25lbnRUeXBlIjo1MTI2LCJjb3VudCI6Njks
InR5cGUiOiJNQVQ0In1dLCJhc3NldCI6eyJnZW5lcmF0b3IiOiJIQVMgYXV0aG9yZWQgc3RydWN0dXJhbCBiaW5kaW5nIGNvbnRyb2xzOyBubyBuYXRpdmUg
Y29udmVyc2lvbiIsInZlcnNpb24iOiIyLjAifSwiYnVmZmVyVmlld3MiOlt7ImJ1ZmZlciI6MCwiYnl0ZUxlbmd0aCI6MzYsImJ5dGVPZmZzZXQiOjB9LHsi
YnVmZmVyIjowLCJieXRlTGVuZ3RoIjoyNCwiYnl0ZU9mZnNldCI6MzZ9LHsiYnVmZmVyIjowLCJieXRlTGVuZ3RoIjo0OCwiYnl0ZU9mZnNldCI6NjB9LHsi
YnVmZmVyIjowLCJieXRlTGVuZ3RoIjo2LCJieXRlT2Zmc2V0IjoxMDh9LHsiYnVmZmVyIjowLCJieXRlTGVuZ3RoIjo0NDE2LCJieXRlT2Zmc2V0IjoxMTZ9
XSwiYnVmZmVycyI6W3siYnl0ZUxlbmd0aCI6NDUzMn1dLCJtYXRlcmlhbHMiOlt7InBick1ldGFsbGljUm91Z2huZXNzIjp7ImJhc2VDb2xvckZhY3RvciI6
WzAuNSwwLjcsMC44LDFdLCJtZXRhbGxpY0ZhY3RvciI6MCwicm91Z2huZXNzRmFjdG9yIjoxfX1dLCJtZXNoZXMiOlt7InByaW1pdGl2ZXMiOlt7ImF0dHJp
YnV0ZXMiOnsiSk9JTlRTXzAiOjEsIlBPU0lUSU9OIjowLCJXRUlHSFRTXzAiOjJ9LCJpbmRpY2VzIjozLCJtYXRlcmlhbCI6MH1dfV0sIm5vZGVzIjpbeyJj
aGlsZHJlbiI6WzY5LDcwXSwibmFtZSI6IkF1dGhvcmVkQXJtYXR1cmUifSx7Im5hbWUiOiJmaXh0dXJlXzY4IiwidHJhbnNsYXRpb24iOlswLDAuNjgsMF19
LHsibmFtZSI6ImZpeHR1cmVfNjciLCJ0cmFuc2xhdGlvbiI6WzAsMC42NywwXX0seyJuYW1lIjoiZml4dHVyZV82NiIsInRyYW5zbGF0aW9uIjpbMCwwLjY2
LDBdfSx7Im5hbWUiOiJmaXh0dXJlXzY1IiwidHJhbnNsYXRpb24iOlswLDAuNjUsMF19LHsibmFtZSI6ImZpeHR1cmVfNjQiLCJ0cmFuc2xhdGlvbiI6WzAs
MC42NCwwXX0seyJuYW1lIjoiZml4dHVyZV82MyIsInRyYW5zbGF0aW9uIjpbMCwwLjYzLDBdfSx7Im5hbWUiOiJmaXh0dXJlXzYyIiwidHJhbnNsYXRpb24i
OlswLDAuNjIsMF19LHsibmFtZSI6ImZpeHR1cmVfNjEiLCJ0cmFuc2xhdGlvbiI6WzAsMC42MSwwXX0seyJuYW1lIjoiZml4dHVyZV82MCIsInRyYW5zbGF0
aW9uIjpbMCwwLjYsMF19LHsibmFtZSI6ImZpeHR1cmVfNTkiLCJ0cmFuc2xhdGlvbiI6WzAsMC41OSwwXX0seyJuYW1lIjoiZml4dHVyZV81OCIsInRyYW5z
bGF0aW9uIjpbMCwwLjU4LDBdfSx7Im5hbWUiOiJmaXh0dXJlXzU3IiwidHJhbnNsYXRpb24iOlswLDAuNTcsMF19LHsibmFtZSI6ImZpeHR1cmVfNTYiLCJ0
cmFuc2xhdGlvbiI6WzAsMC41NiwwXX0seyJuYW1lIjoiZml4dHVyZV81NSIsInRyYW5zbGF0aW9uIjpbMCwwLjU1LDBdfSx7Im5hbWUiOiJmaXh0dXJlXzU0
IiwidHJhbnNsYXRpb24iOlswLDAuNTQsMF19LHsibmFtZSI6ImZpeHR1cmVfNTMiLCJ0cmFuc2xhdGlvbiI6WzAsMC41MywwXX0seyJuYW1lIjoiZml4dHVy
ZV81MiIsInRyYW5zbGF0aW9uIjpbMCwwLjUyLDBdfSx7Im5hbWUiOiJmaXh0dXJlXzUxIiwidHJhbnNsYXRpb24iOlswLDAuNTEsMF19LHsibmFtZSI6ImZp
eHR1cmVfNTAiLCJ0cmFuc2xhdGlvbiI6WzAsMC41LDBdfSx7Im5hbWUiOiJmaXh0dXJlXzQ5IiwidHJhbnNsYXRpb24iOlswLDAuNDksMF19LHsibmFtZSI6
ImZpeHR1cmVfNDgiLCJ0cmFuc2xhdGlvbiI6WzAsMC40OCwwXX0seyJuYW1lIjoiZml4dHVyZV80NyIsInRyYW5zbGF0aW9uIjpbMCwwLjQ3LDBdfSx7Im5h
bWUiOiJmaXh0dXJlXzQ2IiwidHJhbnNsYXRpb24iOlswLDAuNDYsMF19LHsibmFtZSI6ImZpeHR1cmVfNDUiLCJ0cmFuc2xhdGlvbiI6WzAsMC40NSwwXX0s
eyJuYW1lIjoiZml4dHVyZV80NCIsInRyYW5zbGF0aW9uIjpbMCwwLjQ0LDBdfSx7Im5hbWUiOiJmaXh0dXJlXzQzIiwidHJhbnNsYXRpb24iOlswLDAuNDMs
MF19LHsibmFtZSI6ImZpeHR1cmVfNDIiLCJ0cmFuc2xhdGlvbiI6WzAsMC40MiwwXX0seyJuYW1lIjoiZml4dHVyZV80MSIsInRyYW5zbGF0aW9uIjpbMCww
LjQxLDBdfSx7Im5hbWUiOiJmaXh0dXJlXzQwIiwidHJhbnNsYXRpb24iOlswLDAuNCwwXX0seyJuYW1lIjoiZml4dHVyZV8zOSIsInRyYW5zbGF0aW9uIjpb
MCwwLjM5LDBdfSx7Im5hbWUiOiJmaXh0dXJlXzM4IiwidHJhbnNsYXRpb24iOlswLDAuMzgsMF19LHsibmFtZSI6ImZpeHR1cmVfMzciLCJ0cmFuc2xhdGlv
biI6WzAsMC4zNywwXX0seyJuYW1lIjoiZml4dHVyZV8zNiIsInRyYW5zbGF0aW9uIjpbMCwwLjM2LDBdfSx7Im5hbWUiOiJmaXh0dXJlXzM1IiwidHJhbnNs
YXRpb24iOlswLDAuMzUsMF19LHsibmFtZSI6ImZpeHR1cmVfMzQiLCJ0cmFuc2xhdGlvbiI6WzAsMC4zNCwwXX0seyJuYW1lIjoiZml4dHVyZV8zMyIsInRy
YW5zbGF0aW9uIjpbMCwwLjMzLDBdfSx7Im5hbWUiOiJmaXh0dXJlXzMyIiwidHJhbnNsYXRpb24iOlswLDAuMzIsMF19LHsibmFtZSI6ImZpeHR1cmVfMzEi
LCJ0cmFuc2xhdGlvbiI6WzAsMC4zMSwwXX0seyJuYW1lIjoiZml4dHVyZV8zMCIsInRyYW5zbGF0aW9uIjpbMCwwLjMsMF19LHsibmFtZSI6ImZpeHR1cmVf
MjkiLCJ0cmFuc2xhdGlvbiI6WzAsMC4yOSwwXX0seyJuYW1lIjoiZml4dHVyZV8yOCIsInRyYW5zbGF0aW9uIjpbMCwwLjI4LDBdfSx7Im5hbWUiOiJmaXh0
dXJlXzI3IiwidHJhbnNsYXRpb24iOlswLDAuMjcsMF19LHsibmFtZSI6ImZpeHR1cmVfMjYiLCJ0cmFuc2xhdGlvbiI6WzAsMC4yNiwwXX0seyJuYW1lIjoi
Zml4dHVyZV8yNSIsInRyYW5zbGF0aW9uIjpbMCwwLjI1LDBdfSx7Im5hbWUiOiJmaXh0dXJlXzI0IiwidHJhbnNsYXRpb24iOlswLDAuMjQsMF19LHsibmFt
ZSI6ImZpeHR1cmVfMjMiLCJ0cmFuc2xhdGlvbiI6WzAsMC4yMywwXX0seyJuYW1lIjoiZml4dHVyZV8yMiIsInRyYW5zbGF0aW9uIjpbMCwwLjIyLDBdfSx7
Im5hbWUiOiJmaXh0dXJlXzIxIiwidHJhbnNsYXRpb24iOlswLDAuMjEsMF19LHsibmFtZSI6ImZpeHR1cmVfMjAiLCJ0cmFuc2xhdGlvbiI6WzAsMC4yLDBd
fSx7Im5hbWUiOiJmaXh0dXJlXzE5IiwidHJhbnNsYXRpb24iOlswLDAuMTksMF19LHsibmFtZSI6ImZpeHR1cmVfMTgiLCJ0cmFuc2xhdGlvbiI6WzAsMC4x
OCwwXX0seyJuYW1lIjoiZml4dHVyZV8xNyIsInRyYW5zbGF0aW9uIjpbMCwwLjE3LDBdfSx7Im5hbWUiOiJmaXh0dXJlXzE2IiwidHJhbnNsYXRpb24iOlsw
LDAuMTYsMF19LHsibmFtZSI6ImZpeHR1cmVfMTUiLCJ0cmFuc2xhdGlvbiI6WzAsMC4xNSwwXX0seyJuYW1lIjoiZml4dHVyZV8xNCIsInRyYW5zbGF0aW9u
IjpbMCwwLjE0LDBdfSx7Im5hbWUiOiJmaXh0dXJlXzEzIiwidHJhbnNsYXRpb24iOlswLDAuMTMsMF19LHsibmFtZSI6ImZpeHR1cmVfMTIiLCJ0cmFuc2xh
dGlvbiI6WzAsMC4xMiwwXX0seyJuYW1lIjoiZml4dHVyZV8xMSIsInRyYW5zbGF0aW9uIjpbMCwwLjExLDBdfSx7Im5hbWUiOiJmaXh0dXJlXzEwIiwidHJh
bnNsYXRpb24iOlswLDAuMSwwXX0seyJuYW1lIjoiZml4dHVyZV8wOSIsInRyYW5zbGF0aW9uIjpbMCwwLjA5LDBdfSx7Im5hbWUiOiJmaXh0dXJlXzA4Iiwi
dHJhbnNsYXRpb24iOlswLDAuMDgsMF19LHsibmFtZSI6ImZpeHR1cmVfMDciLCJ0cmFuc2xhdGlvbiI6WzAsMC4wNywwXX0seyJuYW1lIjoiZml4dHVyZV8w
NiIsInRyYW5zbGF0aW9uIjpbMCwwLjA2LDBdfSx7Im5hbWUiOiJmaXh0dXJlXzA1IiwidHJhbnNsYXRpb24iOlswLDAuMDUsMF19LHsibmFtZSI6ImZpeHR1
cmVfMDQiLCJ0cmFuc2xhdGlvbiI6WzAsMC4wNCwwXX0seyJuYW1lIjoiZml4dHVyZV8wMyIsInRyYW5zbGF0aW9uIjpbMCwwLjAzLDBdfSx7Im5hbWUiOiJm
aXh0dXJlXzAyIiwidHJhbnNsYXRpb24iOlswLDAuMDIsMF19LHsibmFtZSI6ImZpeHR1cmVfMDEiLCJ0cmFuc2xhdGlvbiI6WzAsMC4wMSwwXX0seyJjaGls
ZHJlbiI6WzEsMiwzLDQsNSw2LDcsOCw5LDEwLDExLDEyLDEzLDE0LDE1LDE2LDE3LDE4LDE5LDIwLDIxLDIyLDIzLDI0LDI1LDI2LDI3LDI4LDI5LDMwLDMx
LDMyLDMzLDM0LDM1LDM2LDM3LDM4LDM5LDQwLDQxLDQyLDQzLDQ0LDQ1LDQ2LDQ3LDQ4LDQ5LDUwLDUxLDUyLDUzLDU0LDU1LDU2LDU3LDU4LDU5LDYwLDYx
LDYyLDYzLDY0LDY1LDY2LDY3LDY4XSwibmFtZSI6ImZpeHR1cmVfMDAiLCJ0cmFuc2xhdGlvbiI6WzAsMC4wLDBdfSx7Im1lc2giOjAsIm5hbWUiOiJBdXRo
b3JlZFRyaWFuZ2xlIiwic2tpbiI6MH1dLCJzY2VuZSI6MCwic2NlbmVzIjpbeyJub2RlcyI6WzBdfV0sInNraW5zIjpbeyJpbnZlcnNlQmluZE1hdHJpY2Vz
Ijo0LCJqb2ludHMiOlsxLDIsMyw0LDUsNiw3LDgsOSwxMCwxMSwxMiwxMywxNCwxNSwxNiwxNywxOCwxOSwyMCwyMSwyMiwyMywyNCwyNSwyNiwyNywyOCwy
OSwzMCwzMSwzMiwzMywzNCwzNSwzNiwzNywzOCwzOSw0MCw0MSw0Miw0Myw0NCw0NSw0Niw0Nyw0OCw0OSw1MCw1MSw1Miw1Myw1NCw1NSw1Niw1Nyw1OCw1
OSw2MCw2MSw2Miw2Myw2NCw2NSw2Niw2Nyw2OCw2OV0sInNrZWxldG9uIjo2OX1dfSC0EQAAQklOAAAAAAAAAAAAAAAAAAAAgD8AAAAAAAAAAAAAAAAAAIA/
AAAAAEQAAAAAAAAARAAAAAAAAABEAAAAAAAAAAAAgD8AAAAAAAAAAAAAAAAAAIA/AAAAAAAAAAAAAAAAAACAPwAAAAAAAAAAAAAAAAAAAQACAAAAAACAPwAA
AAAAAAAAAAAAAAAAAAAAAIA/AAAAAAAAAAAAAAAAAAAAAAAAgD8AAAAAAAAAAHsULr8AAAAAAACAPwAAgD8AAAAAAAAAAAAAAAAAAAAAAACAPwAAAAAAAAAA
AAAAAAAAAAAAAIA/AAAAAAAAAAAfhSu/AAAAAAAAgD8AAIA/AAAAAAAAAAAAAAAAAAAAAAAAgD8AAAAAAAAAAAAAAAAAAAAAAACAPwAAAAAAAAAAw/UovwAA
AAAAAIA/AACAPwAAAAAAAAAAAAAAAAAAAAAAAIA/AAAAAAAAAAAAAAAAAAAAAAAAgD8AAAAAAAAAAGZmJr8AAAAAAACAPwAAgD8AAAAAAAAAAAAAAAAAAAAA
AACAPwAAAAAAAAAAAAAAAAAAAAAAAIA/AAAAAAAAAAAK1yO/AAAAAAAAgD8AAIA/AAAAAAAAAAAAAAAAAAAAAAAAgD8AAAAAAAAAAAAAAAAAAAAAAACAPwAA
AAAAAAAArkchvwAAAAAAAIA/AACAPwAAAAAAAAAAAAAAAAAAAAAAAIA/AAAAAAAAAAAAAAAAAAAAAAAAgD8AAAAAAAAAAFK4Hr8AAAAAAACAPwAAgD8AAAAA
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"""
const PARAMETER_FIELDS = ["length", "tip_mass", "yaw_stiffness", "yaw_damping", "pitch_stiffness", "pitch_damping", "along_stiffness", "along_damping", "angle_limit", "min_yaw", "max_yaw", "yaw_friction", "yaw_bounce", "min_pitch", "max_pitch", "pitch_friction", "pitch_bounce", "base_mass", "base_stiffness", "base_damping", "base_min_left", "base_max_left", "base_left_friction", "base_min_up", "base_max_up", "base_up_friction", "base_min_forward", "base_max_forward", "base_forward_friction"]
var checks := 0
var failures := 0
var folder := ""
var fixture := ""
var bad_chunks := ""

func _initialize() -> void:
	create_timer(12.0).timeout.connect(func(): push_error("Source bone binding authored controls watchdog"); quit(2))
	call_deferred("run")
func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok: failures += 1
	print(("PASS " if ok else "FAIL ") + label)
func digest(raw: PackedByteArray) -> String:
	var hash := HashingContext.new()
	hash.start(HashingContext.HASH_SHA256)
	hash.update(raw)
	return hash.finish().hex_encode()
func report() -> Dictionary:
	var bones: Array = []
	var rows: Array = []
	var rules: Array = []
	for i in 69:
		var name := "fixture_%02d" % i
		var parent := -1 if i == 0 else 0
		bones.append({"name": name, "parent": parent})
		rows.append({"native_index": i, "native_name": name, "native_parent_index": parent, "gltf_node_index": 69 - i, "skin_memberships": [{"skin_index": 0, "joint_slot": 68 - i}]})
		if i < 20: continue
		var prefix := PackedByteArray()
		prefix.resize(120)
		prefix.encode_u32(0, 49)
		var words: Array = []
		var parameters := {}
		for field in PARAMETER_FIELDS.size():
			if field == 5: prefix.encode_u32(4 + field * 4, 0x80000000)
			else: prefix.encode_float(4 + field * 4, (float(i) + float(field) / 4.0) / 8.0)
			words.append(prefix.decode_u32(4 + field * 4))
			parameters[PARAMETER_FIELDS[field]] = prefix.decode_float(4 + field * 4)
		var offset := 408 + i * 216
		rules.append({"native_bone_index": i, "native_bone_name": name, "native_parent_index": parent, "native_bone_flags": 1284, "native_procedure_type": 5, "raw_rule_flags": 49, "known_rule_flags": ["IS_FLEXIBLE", "HAS_ANGLE_CONSTRAINT", "HAS_LENGTH_CONSTRAINT"], "unknown_rule_flag_bits": 0, "parameters": parameters, "binary_provenance": {"bone_record_offset": offset, "bone_relative_rule_offset": 20000, "rule_absolute_offset": offset + 20000, "prefix_bytes": 120, "prefix_sha256": digest(prefix), "float32_words_uint32": words}, "binding_status": "unattempted", "applied": false})
	var jiggle := {"format": "studio_source_jiggle_metadata_1", "status": "retained_inert", "applied": false, "runtime_support": "not_implemented", "binding_status": "unattempted", "full_native_rule_layout_verified": false, "original_source_sha256": NATIVE, "native_mdl_sha256": NATIVE, "native_version": 49, "native_bone_count": 69, "declared_jiggle_rule_count": 49, "source_scale": 0.01905, "sourceio_revision": "fe24260b97ac03b899d9b5d4f0fd7b34772f3647", "native_bone_catalogue_sha256": CATALOGUE_SHA, "rules": rules}
	var crosswalk := {"format": "studio_source_bone_crosswalk_1", "profile": "junko_hair_mdl49_fe242_blender51_1", "status": "retained_inert", "applied": false, "runtime_binding": "unattempted", "native_solver": "not_implemented", "original_source_sha256": NATIVE, "native_mdl_sha256": NATIVE, "glb_sha256": GLB_SHA, "native_bone_catalogue_sha256": CATALOGUE_SHA, "jiggle_wire_sha256": JIGGLE_SHA, "proof_sha256": PROOF_SHA, "max_rest_matrix_error": 0.0, "source_scale": 0.01905, "native_bone_count": 69, "bones": rows}
	return {"source_sha256": NATIVE, "scale": 0.01905, "native_parameters": {"bones": bones, "source_jiggle": jiggle, "source_export_crosswalk": crosswalk}}
func fresh():
	var decoded := SceneIO.load_glb(fixture)
	if decoded.has("error"):
		check(false, "authored69-joint GLB loads: " + str(decoded.error))
		return null
	var actor = Model.new()
	actor.root = decoded.scene
	actor.data = Model.definition(fixture)
	actor.data.metadata.native_parameters = report()
	actor.inventory(actor.root)
	actor.order.reverse()
	return actor
func snapshot(actor) -> PackedByteArray:
	var values: Array = [actor.data, actor.order, actor.root.transform, actor.root.get_meta("has_source_bones", {})]
	var skeletons: Array[Skeleton3D] = []
	for id in actor.bones:
		var info: Dictionary = actor.bones[id]
		var skeleton: Skeleton3D = info.skeleton
		values.append([id, skeleton.get_instance_id(), info.index, info.name, info.path])
		if not skeleton in skeletons: skeletons.append(skeleton)
	# Snapshot actual bones independently of deliberately corrupt descriptors.
	for skeleton in skeletons:
		var catalogue: Array = []
		for index in skeleton.get_bone_count():
			catalogue.append([index, str(skeleton.get_bone_name(index)), skeleton.get_bone_parent(index), skeleton.get_bone_rest(index), skeleton.get_bone_pose(index)])
		values.append([skeleton.get_instance_id(), catalogue])
	return var_to_bytes(values)
func case_check(label: String, edit: Callable, expected: String) -> void:
	var actor = fresh()
	if actor == null: return
	edit.call(actor)
	var before := snapshot(actor)
	var source_before := FileAccess.get_sha256(fixture)
	var result = Bindings.resolve(actor)
	var ok: bool = result.status == "bound_inactive" and result.bindings.size() == 69 and result.by_native.size() == 69 and result.by_gltf_node.size() == 69 and result.rule_owner_ids.size() == 49 and result.rule_owner_nodes.size() == 49 if expected == "bound_inactive" else result.reason == expected and result.bindings.is_empty() and result.by_native.is_empty() and result.by_gltf_node.is_empty() and result.rule_owner_ids.is_empty() and result.rule_owner_nodes.is_empty()
	check(ok, label + " -> " + result.status + "/" + result.reason)
	check(snapshot(actor) == before and FileAccess.get_sha256(fixture) == source_before, label + " preserves data, source, mapping and actual rest/pose")
	actor.root.free()
func cw(actor) -> Dictionary: return actor.data.metadata.native_parameters.native_parameters.source_export_crosswalk
func jiggle(actor) -> Dictionary: return actor.data.metadata.native_parameters.native_parameters.source_jiggle
func change_rule_values(actor) -> void:
	var row: Dictionary = jiggle(actor).rules[0]
	var raw := PackedByteArray()
	raw.resize(120)
	raw.encode_u32(0, 49)
	for i in 29: raw.encode_u32(4 + i * 4, int(row.binary_provenance.float32_words_uint32[i]))
	raw.encode_float(4, 4.0)
	row.parameters.length = 4.0
	row.binary_provenance.float32_words_uint32[0] = raw.decode_u32(4)
	row.binary_provenance.prefix_sha256 = digest(raw)
func run() -> void:
	var args := OS.get_cmdline_user_args()
	folder = args[0] if not args.is_empty() else ProjectSettings.globalize_path("res://output/source-bone-bindings-unit/" + str(Time.get_ticks_usec()))
	if DirAccess.dir_exists_absolute(folder):
		push_error("Use a fresh owned authored-control folder")
		quit(2)
		return
	DirAccess.make_dir_recursive_absolute(folder)
	fixture = folder.path_join("authored69.glb")
	bad_chunks = folder.path_join("authored-bad-chunks.glb")
	var raw := Marshalls.base64_to_raw(GOLDEN_GLB.replace("\n", ""))
	var file := FileAccess.open(fixture, FileAccess.WRITE)
	file.store_buffer(raw)
	file.close()
	check(FileAccess.get_sha256(fixture) == GLB_SHA, "independent golden authored GLB bytes")
	raw.append_array("JUNK".to_ascii_buffer())
	raw.encode_u32(8, raw.size())
	file = FileAccess.open(bad_chunks, FileAccess.WRITE)
	file.store_buffer(raw)
	file.close()
	check(FileAccess.get_sha256(bad_chunks) == BAD_CHUNKS_SHA, "independent malformed chunk golden bytes")
	case_check("complete69/49 with reversed actor order", func(_a): pass, "bound_inactive")
	case_check("integral JSON numbers normalized", func(a):
		for row in cw(a).bones:
			row.native_index = float(row.native_index)
			row.native_parent_index = float(row.native_parent_index)
			row.gltf_node_index = float(row.gltf_node_index)
			row.skin_memberships[0].skin_index = 0.0
			row.skin_memberships[0].joint_slot = float(row.skin_memberships[0].joint_slot), "bound_inactive")
	case_check("posed actor remains a read-only binding", func(a):
		var info: Dictionary = a.bones[a.order[5]]
		info.skeleton.set_bone_pose_rotation(info.index, Quaternion(Vector3.RIGHT, 0.25)), "bound_inactive")
	case_check("actual JSON negative-zero parameter keeps float32 provenance", func(a):
		var decoded = JSON.parse_string("{\"number\":-0.0}")
		jiggle(a).rules[0].parameters.pitch_damping = decoded.number, "bound_inactive")
	case_check("full-precision JSON save keeps original raw negative-zero provenance", func(a):
		a.data.metadata.native_parameters=JSON.parse_string(JSON.stringify(a.data.metadata.native_parameters,"",true,true)), "bound_inactive")
	case_check("legacy retained metadata without crosswalk", func(a): a.data.metadata.native_parameters.native_parameters.erase("source_export_crosswalk"), "no_crosswalk")
	case_check("omitted unsupported crosswalk", func(a): cw(a).status = "omitted", "unsupported_crosswalk")
	case_check("crosswalk applied requires actual false bool", func(a): cw(a).applied = 0, "crosswalk_inactive_contract")
	case_check("native simulation requires actual false bool", func(a): cw(a).native_simulation = 0, "crosswalk_inactive_contract")
	case_check("jiggle applied requires actual false bool", func(a): jiggle(a).applied = 0, "jiggle_inactive_contract")
	case_check("layout verification requires actual false bool", func(a): jiggle(a).full_native_rule_layout_verified = 0, "jiggle_inactive_contract")
	case_check("rule applied requires actual false bool", func(a): jiggle(a).rules[0].applied = 0, "jiggle_rule_contract")
	case_check("rest admission matches producer profile", func(a): cw(a).max_rest_matrix_error = 0.000021, "crosswalk_rest_metric")
	case_check("wrong actor GLB SHA", func(a): a.data.sha256 = "0".repeat(64), "actor_source_identity")
	case_check("wrong proof SHA", func(a): cw(a).proof_sha256 = "0".repeat(64), "crosswalk_proof_sha256")
	case_check("wrong native MDL SHA", func(a): cw(a).native_mdl_sha256 = "0".repeat(64), "crosswalk_domain")
	case_check("changed original-source identity", func(a): a.data.metadata.native_parameters.source_sha256 = "0".repeat(64), "native_identity")
	case_check("missing native row", func(a): cw(a).bones.pop_back(), "crosswalk_domain")
	case_check("duplicate native index", func(a): cw(a).bones[1].native_index = 0, "crosswalk_duplicate")
	case_check("duplicate glTF node", func(a): cw(a).bones[1].gltf_node_index = cw(a).bones[0].gltf_node_index, "crosswalk_duplicate")
	case_check("fractional source selector", func(a): cw(a).bones[0].gltf_node_index = 1.5, "crosswalk_row")
	case_check("bool source selector", func(a): cw(a).bones[0].gltf_node_index = true, "crosswalk_row")
	case_check("unpublished rest-array metadata rejected", func(a): cw(a).rest = [1,2,3], "crosswalk_unknown_field")
	case_check("wrong skin slot with independently valid proof hash", func(a):
		cw(a).bones[0].skin_memberships[0].joint_slot = 0
		cw(a).proof_sha256 = BAD_SLOT_PROOF, "source_skin_membership")
	case_check("selected-scene drift", func(a): cw(a).selected_scene = 1, "selected_scene")
	case_check("extra GLB chunk with coherent source and proof hashes", func(a):
		a.data.source = bad_chunks
		a.data.sha256 = BAD_CHUNKS_SHA
		cw(a).glb_sha256 = BAD_CHUNKS_SHA
		cw(a).proof_sha256 = BAD_CHUNKS_PROOF, "source_glb_chunks")
	case_check("missing importer source node", func(a): a.root.get_meta("has_source_bones").erase(69), "importer_map_count")
	case_check("importer does not guess numeric string keys", func(a):
		var map: Dictionary = a.root.get_meta("has_source_bones")
		var id = map[69]
		map.erase(69)
		map["69"] = id, "importer_map_domain")
	case_check("duplicate importer HAS ID", func(a):
		var map: Dictionary = a.root.get_meta("has_source_bones")
		map[68] = map[69], "importer_id_duplicate_or_missing")
	case_check("wrong live bone index", func(a): a.bones[a.order[0]].index = 69, "live_bone_index")
	case_check("wrong live name", func(a): a.bones[a.order[0]].name = "other", "live_bone_identity")
	case_check("wrong actual parent", func(a):
		var map: Dictionary = a.root.get_meta("has_source_bones")
		var info: Dictionary = a.bones[map[68]]
		info.skeleton.set_bone_parent(info.index, -1), "live_parent")
	case_check("duplicate jiggle owner", func(a): jiggle(a).rules[1].native_bone_index = jiggle(a).rules[0].native_bone_index, "jiggle_owner")
	case_check("jiggle float differs from exact words", func(a): jiggle(a).rules[0].parameters.length = 9.0, "jiggle_float_word")
	case_check("jiggle prefix hash drift", func(a): jiggle(a).rules[0].binary_provenance.prefix_sha256 = "0".repeat(64), "jiggle_prefix_sha256")
	case_check("coherent changed jiggle words fail outer wire binding", change_rule_values, "jiggle_wire_sha256")
	case_check("retained rule cannot claim applied", func(a): jiggle(a).rules[0].applied = true, "jiggle_rule_contract")
	var actor = fresh()
	if actor != null:
		var resolution = Bindings.resolve(actor)
		check(Bindings.current(actor, resolution), "fresh complete resolution remains current")
		var old_root: Node3D = actor.root
		actor.root = Node3D.new()
		check(not Bindings.current(actor, resolution), "replacement root refuses retained runtime bindings")
		actor.root.free()
		actor.root = old_root
		var foreign := Skeleton3D.new()
		var first: Dictionary = actor.bones[actor.order[0]]
		var original: Skeleton3D = first.skeleton
		first.skeleton = foreign
		check(Bindings.resolve(actor).reason == "foreign_skeleton", "actual foreign Skeleton ownership refuses")
		first.skeleton = original
		foreign.free()
		old_root.free()
	var result := {"format": "has_source_bone_bindings_authored_controls_1", "checks": checks, "failures": failures, "native_conversion": false, "native_simulation": false, "source_profile_claim_is_authored_fixture_only": true, "fixture_glb_sha256": GLB_SHA, "golden_proof_sha256": PROOF_SHA, "golden_jiggle_wire_sha256": JIGGLE_SHA}
	file = FileAccess.open(folder.path_join("result.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(result))
	file.close()
	print("SOURCE_BONE_BINDINGS " + JSON.stringify(result))
	quit(0 if failures == 0 else 1)
