extends RefCounted
# Read-only neutral import assessment. No anatomical/age/artist-intent claim.
const Feet=preload("res://src/foot_hold.gd")
const Labels=preload("res://src/bone_labels.gd")
const Bounds=preload("res://src/pose_bounds.gd")
const SkinPoint=preload("res://src/shape_comparison_bounds.gd")
const Shape=preload("res://src/source_shape.gd")
const SIX_FEET:=1.8288
static var queries:=0

static func head(rig: RefCounted) -> String:
	var found:=""
	for id in rig.order:
		if Labels.standard(rig.bones[id].name,Labels.role(rig.data,rig.bones[id].name))!="Head":continue
		if not found.is_empty():return ""
		found=id
	return found

static func regions(skeleton: Skeleton3D,skin: Skin,seeds: Array,rig: RefCounted) -> Array:
	var result:=[]
	for bind in range(skin.get_bind_count()):
		var name:=skin.get_bind_name(bind);var bone: int=skeleton.find_bone(name) if not name.is_empty() else skin.get_bind_bone(bind)
		var region:=-1
		for i in range(seeds.size()):
			var entry: Dictionary=rig.bones[seeds[i]]
			if entry.skeleton!=skeleton:continue
			var parent:=bone
			while parent>=0 and parent!=entry.index:parent=skeleton.get_bone_parent(parent)
			if parent>=0:region=i;break
		result.append(region)
	return result

static func query(rig: RefCounted) -> Dictionary:
	queries+=1
	var result:={"error":"","complete":false,"suggest_fit":false,"height":0.,"leg_ratio":0.,"upright":false,"vertices":0,"coverage":[0.,0.,0.],"reason":""}
	var legs:=Feet.chains(rig);var head_id:=head(rig)
	if legs.size()!=2 or head_id.is_empty():result.reason="No unambiguous complete humanoid rig. Keep this model's original size.";return result
	var updated:={}
	for entry in rig.bones.values():
		if not updated.has(entry.skeleton):entry.skeleton.force_update_all_bone_transforms();updated[entry.skeleton]=true
	var feet: Vector3=(rig.bone_transform(legs[0].ids[2]).origin+rig.bone_transform(legs[1].ids[2]).origin)*.5
	var axis: Vector3=rig.bone_transform(head_id).origin-feet
	if not axis.is_finite() or axis.length()<.00001:result.reason="The rig has no reliable neutral body axis.";return result
	axis=axis.normalized();result.upright=axis.dot(Vector3.UP)>.95
	var context:={"palettes":{},"updated":{},"error":""};var lower:=INF;var upper:=-INF;var mass:=0.
	var seeds: Array=[head_id,legs[0].ids[0],legs[1].ids[0]]
	var meshes: Array=rig.root.find_children("*","MeshInstance3D",true,false)
	if rig.root is MeshInstance3D:meshes.push_front(rig.root)
	for mesh: MeshInstance3D in meshes:
		if not mesh.mesh or not mesh.is_visible_in_tree():continue
		var palette:=Bounds.palette(mesh,context)
		if not context.error.is_empty():result.error=context.error;return result
		var skeleton=mesh.get_node_or_null(mesh.skeleton);var skin: Skin=mesh.skin
		if not palette.is_empty() and skin==null:skin=skeleton.create_skin_from_rest_transforms()
		var groups:=regions(skeleton,skin,seeds,rig) if not palette.is_empty() else []
		for surface in range(mesh.mesh.get_surface_count()):
			var arrays: Array=mesh.mesh.surface_get_arrays(surface);var positions: PackedVector3Array=Shape.vertices(mesh,surface,arrays[Mesh.ARRAY_VERTEX])
			result.vertices+=positions.size()
			if result.vertices>Bounds.VERTEX_BUDGET:result.error="Height review exceeds the 200,000 vertex budget. Keep original size or scale manually.";return result
			var weights=arrays[Mesh.ARRAY_WEIGHTS];var joints=arrays[Mesh.ARRAY_BONES]
			var stride: int=int(joints.size()/positions.size()) if not palette.is_empty() and not positions.is_empty() else 0
			for i in range(positions.size()):
				var point: Vector3=mesh.global_transform*SkinPoint.skinned(positions[i],i,arrays,palette,context)
				if not context.error.is_empty():result.error=context.error;return result
				if not point.is_finite():result.error="Invalid neutral height geometry.";return result
				var projected:=point.dot(axis);lower=minf(lower,projected);upper=maxf(upper,projected)
				for j in range(stride):
					var weight: float=weights[i*stride+j];mass+=weight;var group: int=groups[joints[i*stride+j]]
					if group>=0:result.coverage[group]+=weight
	if not is_finite(lower) or not is_finite(upper) or upper-lower<.00001:result.reason="No reliable visible neutral height.";return result
	result.height=upper-lower;result["axis"]=[axis.x,axis.y,axis.z]
	for i in range(result.coverage.size()):result.coverage[i]/=maxf(mass,.00001)
	if result.coverage.any(func(value):return value<.02):result.reason="Visible skin does not cover the head and both legs. This may be a separate part; keep its original size.";return result
	var length:=0.
	for leg in legs:
		length+=rig.bone_transform(leg.ids[0]).origin.distance_to(rig.bone_transform(leg.ids[1]).origin)+rig.bone_transform(leg.ids[1]).origin.distance_to(rig.bone_transform(leg.ids[2]).origin)
	result.leg_ratio=length*.5/result.height;result.complete=true
	result.suggest_fit=result.upright and result.leg_ratio>=.35 and result.leg_ratio<=.62
	result.reason="Review the visible extent; hair, hats and shoes affect this measurement."
	if not result.upright:result.reason="The body axis is not upright. Measurement follows that axis; fitting will not rotate the model."
	elif not result.suggest_fit:result.reason="Unusual or uncertain leg proportions. Original size stays selected unless you explicitly choose fitting."
	return result
