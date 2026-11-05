extends SceneTree
const Model=preload("res://src/model.gd")
func _initialize() -> void:
	var actor:=Model.new();actor.data=Model.definition("res://project.godot")
	for frame in [0,24]:
		var transform:=Model.identity();transform.position=[0 if frame==0 else 10,0,0]
		actor.data.pose_keys.append({"frame":frame,"pose":{"left":transform},"transform":{"position":[0,0,0],"rotation_xyzw":[0,0,0,1],"scale":1.},"interpolation":"ease"})
	var before:=actor.sample(6)
	var edited:=actor.sample(12);edited["right"]=Model.identity();edited.right.position=[1,0,0]
	var error:=actor.put_pose_key({"frame":12,"pose":edited,"transform":actor.sample_transform(12),"authored_channels":["right"],"interpolation":"ease"},48)
	var result:={"before":before,"after":actor.sample(6),"error":error}
	var file:=FileAccess.open("res://output/body-channel-probe.json",FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close()
	print("BODY_CHANNEL_PROBE "+JSON.stringify(result));quit()
