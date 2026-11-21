extends SceneTree
const Wire=preload("res://tests/camera_cold_wire_oracle.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:
	var original: Array=[{"frame":0,"position":[.125,.00001,-.25],"rotation_xyzw":[-.21796278655529022,0.,0.,.9759570813746759],"fov":60.,"near":.05000000074505806,"far":2000.,"interpolation":"ease","unknown":{"enabled":false,"count":3,"word":"kept"}},{"frame":12,"position":[.125,.00001,-.25],"rotation_xyzw":[-.21796278655529022,0.,0.,.9759570813746759],"fov":57.,"near":.05000000074505806,"far":2000.,"interpolation":"ease"}]
	var source_bytes:=var_to_bytes(original)
	var expected: Array=JSON.parse_string(JSON.stringify(original,"",true,true))
	check(Wire.matches(expected,expected,original,48),"full_precision_expected_wire_preserves_exact_engine_inputs")
	var candidate: Array=expected.duplicate(true);candidate[0].frame=0.;candidate[1].frame=12.
	check(Wire.matches(candidate,expected,original,48),"integral_JSON_float_frames_retain_meaning")
	candidate=expected.duplicate(true);candidate.remove_at(1)
	check(not Wire.matches(candidate,expected,original,48),"missing_camera_key_refuses")
	candidate=expected.duplicate(true);candidate.append(expected[1].duplicate(true));candidate[2].frame=24.
	check(not Wire.matches(candidate,expected,original,48),"added_camera_key_refuses")
	candidate=expected.duplicate(true);candidate[1].frame=13.
	check(not Wire.matches(candidate,expected,original,48),"changed_integral_frame_refuses")
	candidate=expected.duplicate(true);candidate[1].frame=12.0000000000005
	check(not Wire.matches(candidate,expected,original,48),"fractional_frame_refuses_without_rounding")
	candidate=expected.duplicate(true);candidate[0].frame=false
	check(not Wire.matches(candidate,expected,original,48),"boolean_frame_is_not_zero")
	candidate=expected.duplicate(true);candidate[0].position[0]=true
	check(not Wire.matches(candidate,expected,original,48),"boolean_position_is_not_numeric")
	candidate=expected.duplicate(true);candidate[0].position[0]=NAN
	check(not Wire.matches(candidate,expected,original,48),"nonfinite_position_refuses")
	candidate=expected.duplicate(true);candidate[0].rotation_xyzw=[0.,0.,0.,0.]
	check(not Wire.matches(candidate,expected,original,48),"zero_quaternion_refuses")
	candidate=expected.duplicate(true);candidate[0].fov=true
	check(not Wire.matches(candidate,expected,original,48),"boolean_lens_is_not_numeric")
	candidate=expected.duplicate(true);candidate[1].fov=58.
	check(not Wire.matches(candidate,expected,original,48),"changed_lens_refuses")
	candidate=expected.duplicate(true);candidate[0].near=.004
	check(not Wire.matches(candidate,expected,original,48),"changed_near_clip_refuses")
	candidate=expected.duplicate(true);candidate[0].far=2001.
	check(not Wire.matches(candidate,expected,original,48),"changed_far_clip_refuses")
	candidate=expected.duplicate(true);candidate[0].interpolation="hold"
	check(not Wire.matches(candidate,expected,original,48),"changed_interpolation_refuses")
	candidate=expected.duplicate(true);candidate[0].erase("unknown")
	check(not Wire.matches(candidate,expected,original,48),"unknown_metadata_cannot_disappear")
	candidate=expected.duplicate(true);candidate[0].unknown.extra="foreign"
	check(not Wire.matches(candidate,expected,original,48),"unknown_metadata_cannot_be_added")
	candidate=expected.duplicate(true);candidate[0].unknown.enabled=0.
	check(not Wire.matches(candidate,expected,original,48),"metadata_boolean_is_not_numeric_zero")
	# Isolate the original-engine guard: the entire candidate and wire expectation
	# stay EXACTLY equal while one original engine input changes.
	var drift: Array=original.duplicate(true);drift[0].position[1]+=.001
	check(Wire.same_wire(expected,expected) and not Wire.matches(expected,expected,drift,48),"independent_original_translation_guard_refuses")
	drift=original.duplicate(true);drift[0].rotation_xyzw=[0.,0.,0.,1.]
	check(Wire.same_wire(expected,expected) and not Wire.matches(expected,expected,drift,48),"independent_original_rotation_guard_refuses")
	drift=original.duplicate(true);drift[0].fov=61.
	check(Wire.same_wire(expected,expected) and not Wire.matches(expected,expected,drift,48),"independent_original_lens_guard_refuses")
	drift=original.duplicate(true);drift[0].near=.004
	check(Wire.same_wire(expected,expected) and not Wire.matches(expected,expected,drift,48),"independent_original_near_guard_refuses")
	drift=original.duplicate(true);drift[0].far=2001.
	check(Wire.same_wire(expected,expected) and not Wire.matches(expected,expected,drift,48),"independent_original_far_guard_refuses")
	check(not Wire.same_wire(9007199254740992,9007199254740993),"adjacent_large_int64_values_remain_distinct")
	check(not Wire.same_wire(9007199254740993,9007199254740992.0),"rounded_large_int_float_collision_refuses")
	check(Wire.same_wire(9007199254740992,9007199254740992.0),"exact_representable_large_mixed_integer_is_accepted")
	check(not Wire.same_wire(9223372036854775807,9223372036854775808.0),"mixed_float_outside_int64_conversion_domain_refuses")
	drift=original.duplicate(true);drift[0].interpolation="hold"
	check(Wire.same_wire(expected,expected) and not Wire.matches(expected,expected,drift,48),"independent_original_interpolation_guard_refuses")
	check(var_to_bytes(original)==source_bytes,"all_plans_and_refusals_preserve_original_inputs")
	print("CAMERA_COLD_WIRE_UNIT ",JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
