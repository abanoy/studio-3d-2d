extends SceneTree
const World=preload("res://src/world_document.gd")
const Audio=preload("res://src/audio_track.gd")
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
var checks:=0
var failures:=0
var app
func _initialize() -> void:
	create_timer(170).timeout.connect(func():push_error("Current review watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settle() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func job() -> void:
	while app.has_project.pid>0:await process_frame
	await settle()
func same(a,b) -> bool:return JSON.parse_string(JSON.stringify(a,"",true,true))==JSON.parse_string(JSON.stringify(b,"",true,true))
func same_spatial(a,b,field: String="") -> bool:
	# JSON round trips in pinned Godot can change a final double digit. Model
	# positions/quaternions are consumed as float32 Vector3/Quaternion values.
	# Compare those exact bits; IDs, metadata, times and other fields stay exact.
	if a is Dictionary and b is Dictionary:
		if a.size()!=b.size():return false
		for key in a:
			if not b.has(key) or not same_spatial(a[key],b[key],str(key)):return false
		return true
	if a is Array and b is Array:
		if a.size()!=b.size():return false
		if field in ["position","rotation_xyzw"] and a.size() in [3,4]:return PackedFloat32Array(a).to_byte_array()==PackedFloat32Array(b).to_byte_array()
		for i in range(a.size()):
			if not same_spatial(a[i],b[i]):return false
		return true
	return a==b
func pcm_hash() -> String:return app.audio_mix.pcm.hex_encode().sha256_text() if app.audio_mix.has("pcm") else ""
func run() -> void:
	var config: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(OS.get_cmdline_user_args()[0]))
	var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(config.manifest))
	var folder:=ProjectSettings.globalize_path("res://output/current-review");DirAccess.make_dir_recursive_absolute(folder)
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settle()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	check(OS.get_user_data_dir().replace("\\","/").ends_with(config.profile),"review profile is separate from normal Studio settings")
	check(not app.advanced_mode and app.current_world().objects.is_empty(),"fresh source has an empty Simple world")
	app.home.open_home();await settle()
	check(app.home.visible and app.home.new_button.visible,"normal Home action opens over the current document")
	app.home.new_button.pressed.emit();await settle()
	check(not app.home.visible and app.current_world().objects.is_empty(),"Home New opens the real editor")
	var original:=FileAccess.get_sha256(config.project)
	app.has_project.open_file(config.project);await job()
	check(app.has_project.path==config.project and not app.dirty,"ordinary Open restores packed scene without developer imports")
	if app.has_project.path!=config.project:app.free();quit(1);return
	check(same(World.portable(app.current_world()),expected.world),"all saved native world records survive exactly")
	check(same(app.keys,expected.camera_keys) and same(app.video,expected.video),"explicit shot keys and project timing survive exactly")
	check(same(Audio.metadata(app.audio_document()),expected.get("audio",{})),"audio identities, endpoint, trim and gain survive exactly")
	var cache:=folder.path_join("cache").replace("\\","/").to_lower()+"/";var local:=true
	for row in app.current_world().objects:
		if row.kind=="group":continue
		var path: String=ProjectSettings.globalize_path(row.source).replace("\\","/")
		local=local and path.to_lower().begins_with(cache) and FileAccess.get_sha256(path)==row.sha256
	for clip in app.audio_clips:local=local and clip.source.path.replace("\\","/").to_lower().begins_with(cache)
	check(local,"all runtime mesh/audio assets come from the fresh local HAS cache")
	if config.kind in ["rate","duration"]:
		app.show_project_options();await settle()
		check(app.project_timing.duration.value==expected.video.duration_frames and app.frame_box.max_value==expected.video.duration_frames and app.renderer.world_runtime.duration==expected.video.duration_frames,"cold scene length agrees across Options, playhead and posing")
		check(app.project_timing.choices.selected==3 and "23.976 fps" in app.transport_info.text and pcm_hash()==config.mix,"cold fractional-rate scene retains exact audio mix and visible rate")
		var before: Dictionary=app.video.duplicate(true);var history: int=app.history.size();var mixed:=pcm_hash()
		check(app.project_timing.apply_duration(96).is_empty() and app.history.size()==history+1 and app.frame_box.max_value==96,"cold review extends a loaded scene with one Undo")
		app.undo();check(app.video==before and pcm_hash()==mixed,"cold scene-length Undo restores saved timing and exact mix")
		app.project_options.hide()
	if config.kind=="trim":
		check(pcm_hash()==config.mix and app.audio_clips[0].source_out_sample==26460,"new audio3 trim retains exact mixed PCM")
		var before: Dictionary=app.audio_document().duplicate(true);app.select_audio(0);app.audio_trim_editor.open();app.audio_trim_editor.restore_end();await settle()
		check(not app.audio_clips[0].has("source_out_sample"),"review copy can extend the original audio again")
		app.undo();check(app.audio_document()==before and pcm_hash()==config.mix,"end restoration has one exact Undo")
	if config.kind=="fade":
		check(app.audio_document().format==Audio.FADE_FORMAT and pcm_hash()==config.mix and app.audio_clips[0].fade_in_ms==100 and app.audio_clips[0].fade_out_ms==200,"cold audio4 retains exact fades and mixed PCM")
		var before: Dictionary=app.audio_document().duplicate(true);var history: int=app.history.size();app.select_audio(0);app.audio_fade_editor.open();app.audio_fade_editor.fade_in.value=0;app.audio_fade_editor.fade_out.value=0;app.audio_fade_editor.apply();await settle()
		check(app.audio_document().format==Audio.TRIM_FORMAT and app.history.size()==history+1,"review copy removes fades while retaining its source end trim")
		app.undo();check(app.audio_document()==before and pcm_hash()==config.mix,"cold fade removal has one exact Undo")
	if config.kind=="mmd":
		var actor: RefCounted=app.renderer.active_model()
		if not actor:
			for row in app.current_world().objects:
				var candidate: RefCounted=app.renderer.world_runtime.instance(row.id)
				if candidate and candidate.data.metadata.get("native_parameters",{}).get("kind")=="mmd_preparation":actor=candidate;break
		check(actor!=null and actor.data.metadata.native_parameters.ik_constraints.chains.size()==7,"portable MMD retains standard joint declarations")
		if actor:
			var foot:="";var target:=""
			for id in actor.order:
				if actor.bones[id].name=="左足首":foot=id
				if actor.bones[id].name=="左足ＩＫ":target=id
			app.set_frame(20);await settle()
			check(not foot.is_empty() and not target.is_empty() and actor.bone_transform(foot).origin.distance_to(actor.bone_transform(target).origin)<.001,"baked MMD foot target evaluates without a source-model conversion")
	if config.kind.begins_with("joint-"):
		app.set_frame(int(config.frame));var actor: RefCounted=app.renderer.active_model()
		# Normal Open intentionally clears selection. Locate the packed actor,
		# then select it explicitly as the owner would through the scene tree.
		if not actor:
			for row in app.current_world().objects:
				if row.kind=="model":actor=app.renderer.world_runtime.instance(row.id);break
		check(actor!=null,"packed joint actor is available without a preparation folder")
		if actor:
			var controller:="";var effector:="";var native: String="左足ＩＫ" if config.kind=="joint-miku" else "Foot target"
			for id in actor.order:
				if actor.bones[id].name==native:controller=id
				if actor.bones[id].name==("左足首" if config.kind=="joint-miku" else "Tip"):effector=id
			check(not controller.is_empty() and not effector.is_empty(),"packed controller and effector retain exact native bindings")
			var editor=app.pose_editor;app.world_selection.select_entity(actor.data.id);app.mode.select(2);app.change_mode(2);editor.selected=controller;editor.tree_items[controller].select(0);editor.operation.select(1);editor.refresh_values()
			var before: Dictionary=actor.data.duplicate(true);var history: int=app.history.size();var shots: Array=app.keys.duplicate(true)
			editor.fields[1].value+=.005;editor.apply_numeric();await settle()
			check(actor.data!=before and app.history.size()==history+1 and actor.bone_transform(effector).origin.distance_to(actor.bone_transform(controller).origin)<.001,"cold packed controller edit solves and auto-keys its joints")
			app.undo();check(actor.data==before and app.keys==shots,"cold controller Undo restores actor and preserves shot keys")
			check(not preload("res://src/joint_constraints.gd").plan(actor,controller).is_empty(),"joint solver binds directly to the fresh packed GLB cache")
	app.set_frame(int(config.frame));app.world_selection.clear()
	var image: Image=await app.renderer.capture(app.keys,app.layers,int(config.frame),true)
	var reference:=Image.load_from_file(config.reference);reference.convert(Image.FORMAT_RGBA8)
	var a:=image.get_data();var b:=reference.get_data();var changed:=0;var total:=0.
	check(a.size()==b.size(),"preview retains full output dimensions")
	if a.size()==b.size():
		for i in range(a.size()):
			if a[i]!=b[i]:changed+=1;total+=absf(float(a[i])-float(b[i]))
	check(changed<=384 and total/maxi(1,a.size())<.002,"relocated rendering keeps the established native mesh-edge bound")
	var world: Dictionary=World.portable(app.current_world());var shots: Array=app.keys.duplicate(true);var mixed:=pcm_hash()
	app.mode.select(0);app.change_mode(0);app.active_layer=1;app.layer_choice.select(1);app.refresh_layer()
	var cel:=Drawing.cel_at(app.layers[1],int(config.frame));var paint:=Storage.image_hash(cel.image)
	var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.pressed=true;app.color.color=Color.CYAN
	app.canvas_input(event,Vector2(80,140));app.canvas_input(InputEventMouseMotion.new(),Vector2(230,140));event.pressed=false;app.canvas_input(event,Vector2(230,140))
	check(Storage.image_hash(cel.image)!=paint and World.portable(app.current_world())==world and app.keys==shots and pcm_hash()==mixed,"routed drawing stays independent of native world, camera and audio")
	app.undo();check(Storage.image_hash(Drawing.cel_at(app.layers[1],int(config.frame)).image)==paint,"drawing Undo restores the exact cel")
	var saved:=folder.path_join("Review scene.has");app.has_project.save_file(saved,"packed");await job()
	check(app.has_project.path==saved and not app.dirty,"review copy saves a new packed HAS")
	app.new_project();app.has_project.open_file(saved);await job()
	check(same_spatial(World.portable(app.current_world()),world) and same_spatial(app.keys,shots) and pcm_hash()==mixed,"resaved spatial values retain exact engine precision; other data and PCM stay exact")
	app.set_frame(int(config.frame));var preview: Image=await app.renderer.capture(app.keys,app.layers,int(config.frame),true)
	app.export_dialog()
	while app.exporting:await process_frame
	var movie: String=app.last_export_folder.path_join("movie.mp4")
	check(FileAccess.file_exists(movie) and app.last_export_folder.get_base_dir()==folder,"ordinary Simple Export writes beside the review HAS")
	check(Image.load_from_file(app.last_export_folder.path_join("frame_%06d.png" % (int(config.frame)+1))).get_data()==preview.get_data(),"movie input frame exactly matches this process preview")
	check(FileAccess.get_sha256(config.project)==original,"reviewing/editing/resaving preserves the supplied HAS")
	await settle();app.get_viewport().get_texture().get_image().save_png(folder.path_join("editor.png"))
	var result:={"checks":checks,"failures":failures,"kind":config.kind,"changed_channels":changed,"movie":movie,"project":saved,"source_unchanged":true,"profile":OS.get_user_data_dir()}
	FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("CURRENT_CANDIDATE ",JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
