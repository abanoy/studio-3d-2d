extends RefCounted

const DEFAULT_NEAR:=0.05
const DEFAULT_FAR:=2000.0
const MAX_FAR:=1000000000000.0

static func range_error(keys: Array) -> String:
	if keys.is_empty():return "Missing camera keys."
	for value in keys:
		if not value is Dictionary:return "Invalid camera key."
		var nearest=value.get("near",DEFAULT_NEAR);var farthest=value.get("far",DEFAULT_FAR)
		for distance in [nearest,farthest]:
			if not (distance is int or distance is float) or not is_finite(float(distance)):return "Camera visibility distances must be finite numbers."
		if nearest<0.001:return "Nearest visible distance must be at least 0.001 scene units."
		if farthest<=nearest:return "Farthest visible distance must be greater than the nearest distance."
		if farthest>MAX_FAR:return "Camera visibility distance exceeds the supported limit of 1e12 scene units."
	return ""

static func from_camera(frame: int,camera: Camera3D,interpolation: String) -> Dictionary:
	var value:=key(frame,camera.position,camera.quaternion,camera.fov,interpolation)
	value["near"]=camera.near;value["far"]=camera.far
	return value

# Godot coordinates: right-handed, +Y up, camera looks down -Z. Quaternion XYZW.
static func key(frame: int, position: Vector3, rotation: Quaternion, fov: float, interpolation := "ease") -> Dictionary:
	return {"frame": frame, "position": [position.x, position.y, position.z], "rotation_xyzw": [rotation.x, rotation.y, rotation.z, rotation.w], "fov": fov, "interpolation": interpolation}

static func vector(a: Array) -> Vector3:
	return Vector3(a[0], a[1], a[2])

static func quaternion(a: Array) -> Quaternion:
	return Quaternion(a[0], a[1], a[2], a[3]).normalized()

static func sample(keys: Array, frame: int) -> Dictionary:
	var a: Dictionary = keys[0]
	var b: Dictionary = keys[-1]
	if frame <= a.frame:
		b = a
	elif frame >= b.frame:
		a = b
	else:
		for i in range(keys.size() - 1):
			if frame >= keys[i].frame and frame < keys[i + 1].frame:
				a = keys[i]
				b = keys[i + 1]
				break
	var t: float = 0.0 if a.frame == b.frame else float(frame - a.frame) / (b.frame - a.frame)
	if a.interpolation == "hold":
		t = 0.0
	elif a.interpolation == "ease":
		t = t * t * (3.0 - 2.0 * t)
	return {"position": vector(a.position).lerp(vector(b.position), t), "rotation": quaternion(a.rotation_xyzw).slerp(quaternion(b.rotation_xyzw), t), "fov": lerpf(a.fov, b.fov, t),"near":lerpf(float(a.get("near",DEFAULT_NEAR)),float(b.get("near",DEFAULT_NEAR)),t),"far":lerpf(float(a.get("far",DEFAULT_FAR)),float(b.get("far",DEFAULT_FAR)),t)}

static func put_key(keys: Array, value: Dictionary) -> void:
	for i in range(keys.size()):
		if keys[i].frame == value.frame:
			keys[i] = value
			return
	keys.append(value)
	keys.sort_custom(func(a, b): return a.frame < b.frame)

static func seconds(frame: int, video: Dictionary) -> float:
	return float(frame) * video.fps_den / video.fps_num
