extends SceneTree
const Model=preload("res://src/model.gd")
func _initialize() -> void:
	var before:=Model.new();before.data=Model.definition("res://project.godot")
	for frame in [0,24]:
		before.data.pose_keys.append({"frame":frame,"pose":{},"transform":{"position":[0 if frame==0 else 10,0,0],"rotation_xyzw":[0,0,0,1],"scale":1.0},"interpolation":"ease"})
	var after:=Model.new();after.data=Model.ShapeAnimation.promote(before.data);after.data.shape_base={"3":{"0":0.}};after.data.shape_pose={"3":{"0":1.}}
	after.data=Model.ShapeAnimation.put_key(after.data,{"frame":12,"pose":before.sample(12),"transform":before.sample_transform(12),"shapes":{"3":{"0":1.}},"interpolation":"ease","authored_channels":["@shape/3/0"]},48)
	var report:={"before_x_at6":before.sample_transform(6).position[0],"after_x_at6":after.sample_transform(6).position[0],"format":after.data.format,"shared_snapshot_limitation":true}
	var file:=FileAccess.open("res://output/shape-snapshot-probe.json",FileAccess.WRITE);file.store_string(JSON.stringify(report));file.close();print(JSON.stringify(report));quit(0)
