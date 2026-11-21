extends "res://tests/scene_indirect_smoke.gd"
# Separate from the primary worker's authoritative native early-return controls.
func wait_bake(app: Node) -> void:
	await settled()
	while app.renderer.scene_lighting.indirect.voxel.baking:await process_frame
	await settled()

func run() -> void:
	var args:=OS.get_cmdline_user_args();folder=args[0];graphics=not "--cpu" in args;fixtures()
	for theme in ["neon","light"]:
		var app=await make_app(theme)
		check(app.load_scene(folder.path_join("room.glb")).is_empty(),"Import original environment in "+theme)
		var actor=app.renderer.world_runtime.instance(app.last_import_id)
		actor.data.position=[0,0,0];actor.data.rotation_xyzw=[0,0,0,1];actor.data.scale=1.;app.set_frame(0)
		app.video.duration_frames=2
		var editor: Node=app.scene_lighting_editor;editor.open();app.change_lighting(1)
		var lighting:=Document.empty();lighting.indirect=Document.indirect(lighting).duplicate(true)
		lighting.indirect.method="voxelgi";lighting.indirect.enabled=true;lighting.indirect.voxel=Document.voxel({}).duplicate(true)
		editor.commit(lighting,"Initial bounded-room bake");await wait_bake(app)
		var voxel=app.renderer.scene_lighting.indirect.voxel
		check(voxel.error.is_empty() and voxel.probe.visible and voxel.probe.data!=null,"Initial real room bake succeeds")
		var previous: VoxelGIData=voxel.probe.data;var count: int=voxel.bake_count
		var world: Dictionary=app.renderer.world_state().duplicate(true)
		lighting=Document.document(app.video).duplicate(true);lighting.indirect.voxel.position=[1000,1000,1000]
		editor.commit(lighting,"Move room away from all environment meshes");await wait_bake(app)
		# Exercise ordinary later syncs, not only bake_room's immediate hide().
		for tick in range(3):app.renderer.apply_lighting();await process_frame
		check(voxel.probe.data==null,"Empty rebake discards earlier successful data")
		check(not voxel.probe.visible,"Later syncs cannot re-show failed empty-room data")
		check(voxel.bake_count==count and voxel.error.contains("No static environment"),"Empty rebake keeps success count and actionable error")
		check(app.renderer.scene_lighting.indirect.capture_error(app.video)==voxel.error,"Failed room refuses capture admission")
		if graphics:
			var export_error: String=await app.export_movie(folder)
			check(export_error.contains("No static environment") and not FileAccess.file_exists(app.last_export_folder.path_join("movie.mp4")),"Actual movie export refuses failed room without creating a movie")
		app.undo();await wait_bake(app)
		check(voxel.error.is_empty() and voxel.probe.visible and voxel.probe.data!=null and voxel.probe.data!=previous and voxel.bake_count==count+1,"Undoing empty bounds performs a fresh successful bake")
		check(app.renderer.world_state()==world,"Bounds failure and recovery preserve original world data")
		if graphics:
			var export_error: String=await app.export_movie(folder)
			check(export_error.is_empty() and FileAccess.file_exists(app.last_export_folder.path_join("movie.mp4")),"Actual movie export recovers after successful fresh bake")
			if export_error.is_empty():measurements[theme]=app.last_export_folder.path_join("movie.mp4")
		app.free();await process_frame
	finish("writer")
