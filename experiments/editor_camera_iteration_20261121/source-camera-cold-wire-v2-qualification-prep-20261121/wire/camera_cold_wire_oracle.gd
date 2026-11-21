extends RefCounted
# Test-only exact wire expectation, observed in the retained camera diagnostic.
# No epsilon and no persistence/product changes.
const Timeline=preload("res://src/timeline.gd")
const Edits=preload("res://src/camera_key_edits.gd")
static func same_wire(a,b) -> bool:
	if a is Dictionary and b is Dictionary:
		if a.size()!=b.size():return false
		for key in a:
			if not b.has(key) or not same_wire(a[key],b[key]):return false
		return true
	if a is Array and b is Array:
		if a.size()!=b.size():return false
		for index in range(a.size()):
			if not same_wire(a[index],b[index]):return false
		return true
	if a is int and b is int:return a==b
	if a is float and b is float:return is_finite(a) and is_finite(b) and a==b
	if (a is int and b is float) or (a is float and b is int):
		var integer_value: int=a if a is int else b
		var float_value: float=b if b is float else a
		# Only convert a finite whole float inside the exact int64 conversion domain.
		if not is_finite(float_value) or float_value!=floor(float_value):return false
		if float_value < -9223372036854775808.0 or float_value >= 9223372036854775808.0:return false
		return int(float_value)==integer_value and float(integer_value)==float_value
	return typeof(a)==typeof(b) and a==b
static func same_engine(original: Array,actual: Array,duration: int) -> bool:
	if not Edits.error(original,duration).is_empty() or not Edits.error(actual,duration).is_empty() or original.size()!=actual.size():return false
	for index in range(original.size()):
		var a: Dictionary=original[index];var b: Dictionary=actual[index]
		# Edits.error proves finite integral numeric frames before this cast.
		if int(a.frame)!=int(b.frame):return false
		if a.interpolation!=b.interpolation:return false
		if Timeline.vector(a.position)!=Timeline.vector(b.position):return false
		if Timeline.quaternion(a.rotation_xyzw)!=Timeline.quaternion(b.rotation_xyzw):return false
		if a.fov!=b.fov:return false
		if a.get("near",Timeline.DEFAULT_NEAR)!=b.get("near",Timeline.DEFAULT_NEAR):return false
		if a.get("far",Timeline.DEFAULT_FAR)!=b.get("far",Timeline.DEFAULT_FAR):return false
	return true
static func matches(actual,expected_wire,original,duration: int) -> bool:
	if not actual is Array or not expected_wire is Array or not original is Array:return false
	if not Edits.error(expected_wire,duration).is_empty():return false
	return same_wire(expected_wire,actual) and same_engine(original,actual,duration)
