extends SceneTree
const Model=preload("res://src/model.gd")
const World=preload("res://src/world_document.gd")
func _initialize() -> void:
	var args:=OS.get_cmdline_user_args()
	var source:=World.object(args[0]);source.id="probe-source";source.draft_frame=-1
	var peer:=World.object(args[1]);peer.id="probe-peer";peer.position=[-.7,.5,0]
	var world:=World.empty();world.objects=[source,peer]
	var invalid_model:=Model.validate(source,48)
	var invalid_world:=World.validate(world,48)
	source.draft_frame=0
	var valid_standalone:=World.validate(world,48)
	peer.parent_id=source.id
	var valid_parented:=World.validate(world,48)
	var ok:=invalid_model=="Invalid pose draft frame." and invalid_world=="Invalid world object: Invalid pose draft frame." and valid_standalone.is_empty() and valid_parented.is_empty()
	var report:={"passed":ok,"invalid_model_error":invalid_model,"invalid_world_error":invalid_world,"valid_standalone_error":valid_standalone,"valid_parented_error":valid_parented,"source_sha256":source.sha256,"peer_sha256":peer.sha256,"peer_parent_id":peer.parent_id,"app_instantiated":false,"glb_scene_instantiated":false,"rendering":false}
	FileAccess.open(args[2],FileAccess.WRITE).store_string(JSON.stringify(report,"  ",true,true)+"\n")
	print("WIND_PEER_METADATA_PREFLIGHT "+JSON.stringify(report))
	quit(0 if ok else 1)