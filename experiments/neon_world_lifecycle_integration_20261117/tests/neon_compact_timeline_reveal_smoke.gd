# UNRUN source draft. Uses generated geometry/PCM only; no owner assets.
# Keep the approved compact layout. Prove content-end is not model-end, then reveal and route
# real viewport clicks to first/middle/last model rows with drawing and audio lanes below them.
extends SceneTree
const SceneIO = preload("res://src/scene3d.gd")
const World = preload("res://src/world_document.gd")
const Drawing = preload("res://src/drawing.gd")
var checks := 0
var failures := 0
var samples: Array = []

func _initialize() -> void:
	create_timer(90).timeout.connect(func():push_error("Compact timeline reveal watchdog expired");quit(2))
	call_deferred("run")

func check(ok: bool,label: String) -> void:
	checks += 1
	print(("PASS " if ok else "FAIL ") + label)
	if not ok: failures += 1

func settled() -> void:
	for i in range(3): await process_frame
	await RenderingServer.frame_post_draw

func silent_wav(path: String) -> void:
	var pcm := PackedByteArray()
	pcm.resize(16000)
	pcm.fill(0)
	var file := FileAccess.open(path,FileAccess.WRITE)
	file.store_buffer("RIFF".to_ascii_buffer());file.store_32(36+pcm.size())
	file.store_buffer("WAVEfmt ".to_ascii_buffer());file.store_32(16)
	file.store_16(1);file.store_16(1);file.store_32(8000);file.store_32(16000)
	file.store_16(2);file.store_16(16)
	file.store_buffer("data".to_ascii_buffer());file.store_32(pcm.size());file.store_buffer(pcm);file.close()

func run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size()!=1: push_error("Pass one fresh owned output folder");quit(2);return
	var folder: String = ProjectSettings.globalize_path(args[0]).replace("\\","/").simplify_path()
	var output_root: String = ProjectSettings.globalize_path("res://output").replace("\\","/").simplify_path()+"/"
	if not folder.begins_with(output_root) or DirAccess.dir_exists_absolute(folder): push_error("Preserve earlier attempts; use fresh owned output under this checkout");quit(2);return
	DirAccess.make_dir_recursive_absolute(folder)
	var asset := folder.path_join("actor.glb")
	var wav := folder.path_join("silence.wav")
	SceneIO.make_pose_fixture(asset)
	silent_wav(wav)
	var asset_sha := FileAccess.get_sha256(asset)
	var app = load("res://main.tscn").instantiate()
	app.recovery_root = folder.path_join("recovery")
	app.recent_path = folder.path_join("recent.json")
	app.display_prefs_path = folder.path_join("display.cfg")
	root.size = Vector2i(1400,900)
	root.add_child(app)
	await settled()
	app.home.hide()
	app.autosave_enabled.button_pressed = false
	app.has_project.cache_root = folder.path_join("cache")
	var document := World.empty()
	for i in range(64): document.objects.append(World.object(asset,"model","Actor %02d" % i))
	check(app.restore_world(document).is_empty(),"64 generated model objects install")
	app.mode.select(0);app.change_mode(0);app.set_frame(0);app.create_cel(false)
	var cel: Dictionary = Drawing.cel_at(app.layers[1],0)
	Drawing.stroke(Drawing.image(cel),Vector2(20,20),Vector2(40,20),3,Color.RED,false)
	app.changed()
	check(app.import_audio(wav).is_empty(),"generated PCM clip installs an actual Audio lane")
	app.mode.select(1);app.change_mode(1)
	app.workspace_layout.vertical.split_offset = -166
	await settled()
	var timeline = app.timeline
	var scroll: ScrollContainer = timeline.get_parent()
	var dock_scroll: ScrollContainer = app.workspace_layout.panels.timeline.get_node("TimelineContentScroll")
	dock_scroll.ensure_control_visible(scroll)
	await settled()
	check(timeline.object_rows.size()==64 and app.layers.size()>=2 and timeline.audio_clips.size()==1,"object rows have drawing and actual audio lanes below them")
	check(scroll.size.y>=26 and scroll.size.y<115,"approved compact viewport is smaller than the trailing-lane distance")
	check(dock_scroll.get_global_rect().encloses(scroll.get_global_rect()),"outer Timeline scroll exposes the complete compact track viewport")
	scroll.scroll_vertical = 2000
	await settled()
	var last_point: Vector2 = timeline.get_global_transform()*Vector2(40,timeline.row_y(63)+12)
	check(not scroll.get_global_rect().has_point(last_point),"negative case: scrolling to all content end leaves last model above compact viewport")
	var before: Dictionary = app.current_world().duplicate(true)
	var audio_before: Dictionary = app.audio_document().duplicate(true)
	var paint: PackedByteArray = Drawing.image(cel).get_data()
	var history: int = app.history.size()
	for index in [0,32,63]:
		var prior: int = 63 if index==0 else 0
		app.world_selection.select_entity(timeline.object_rows[prior].id,false)
		app.mode.select(1);app.change_mode(1)
		await settled()
		dock_scroll.ensure_control_visible(scroll)
		await settled()
		# The successor input step: use the requested row's geometry, not total content height.
		scroll.scroll_vertical = int(timeline.row_y(index))
		await settled()
		var point: Vector2 = timeline.get_global_transform()*Vector2(40,timeline.row_y(index)+12)
		var visible: bool = scroll.get_global_rect().has_point(point) and dock_scroll.get_global_rect().has_point(point)
		check(visible,"requested first/middle/last row is inside both actual scroll viewports: %d" % index)
		var event := InputEventMouseButton.new()
		event.button_index = MOUSE_BUTTON_LEFT;event.pressed = true;event.position = point
		app.get_viewport().push_input(event,true)
		await settled()
		event.pressed = false
		app.get_viewport().push_input(event,true)
		await settled()
		var id: String = timeline.object_rows[index].id
		var selected: bool = app.renderer.active_instance_id==id and timeline.selected_id==id and app.pose_editor.active_rig()!=null and app.pose_editor.active_rig().data.id==id
		check(selected,"actual routed click selects model and pose target: %d" % index)
		samples.append({"row":index,"visible_before_route":visible,"selected_after_route":selected,"scroll_vertical":scroll.scroll_vertical,"viewport_height":scroll.size.y})
	check(app.current_world()==before and app.audio_document()==audio_before and Drawing.image(cel).get_data()==paint and app.history.size()==history,"row reveal and selection preserve world/audio/drawing pixels and Undo")
	check(FileAccess.get_sha256(asset)==asset_sha,"selection leaves generated source geometry unchanged")
	var result := {"checks":checks,"failures":failures,"samples":samples,"native_owner_assets_used":false,"compact_timeline_preserved":true}
	var encoded := JSON.stringify(result,"",true,true)
	var file := FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE)
	file.store_string(encoded);file.close()
	print("COMPACT_TIMELINE_REVEAL " + encoded)
	app.free()
	quit(0 if failures==0 else 1)
