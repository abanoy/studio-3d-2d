extends SceneTree
const SceneIO=preload("res://src/scene3d.gd")
const Timeline=preload("res://src/timeline.gd")
const Drawing=preload("res://src/drawing.gd")
class CapturedPreview extends RefCounted:
	var image: Image
	func busy() -> bool:return false
	func poll() -> Dictionary:return {}
	func finish() -> Dictionary:return {}
	func start(_folder: String,_digest: String,background: Image,_overlays: Array) -> String:
		image=background.duplicate();return ""
var app
var folder: String
var checks:=0
var failures:=0
var cases: Array=[]
func _initialize() -> void:
	create_timer(120).timeout.connect(func():push_error("Scene view watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settled() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func local_pixel(point: Vector2) -> Vector2:
	var frame: Rect2=app.canvas.image_rect()
	return frame.position+point/app.canvas.resolution*frame.size
func pointer(point: Vector2,pressed: bool) -> void:
	var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.pressed=pressed;event.position=local_pixel(point)
	app.canvas._gui_input(event)
func motion(point: Vector2) -> void:
	var event:=InputEventMouseMotion.new();event.position=local_pixel(point);event.button_mask=MOUSE_BUTTON_MASK_LEFT
	app.canvas._gui_input(event)
func view_image() -> Image:
	return root.get_texture().get_image().get_region(Rect2i(Vector2i(app.canvas.global_position),Vector2i(app.canvas.size)))
func run() -> void:
	folder=OS.get_cmdline_user_args()[0]
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json");app.display_prefs_path=folder.path_join("prefs.cfg")
	root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false
	check(app.scene_view.setup_enabled and not app.scene_view.frame_enabled and not app.scene_view.grid_enabled,"fresh personal preferences default to one full-area scene with optional guides off")
	var fixture:=folder.path_join("original-rig.glb");check(SceneIO.make_pose_fixture(fixture)==OK,"create an original standard rig without private native assets")
	var placement: Dictionary=app.import_actions.placement();placement.physics_on_import=false
	check(app.pose_editor.add_model(fixture,0,placement).is_empty(),"ordinary import installs the standard rig")
	var rig: RefCounted=app.renderer.active_model();var id: String=rig.data.id;var source_hash:=FileAccess.get_sha256(fixture)
	# Isolate only the displayed canvas size from dock minimums. Production input,
	# renderer, selection, pose and export code remain the actual application.
	app.canvas.reparent(root);app.canvas.position=Vector2(12,12);app.canvas.z_index=100
	app.mode.select(0);app.change_mode(0);app.create_cel(false)
	var cel: Dictionary=Drawing.cel_at(app.layers[app.active_layer],0)
	Drawing.edit_image(cel).image.fill_rect(Rect2i(850,450,220,180),Color.MAGENTA);app.changed()
	var cel_before:=Drawing.image(cel).get_data();var native_size: Vector2i=app.renderer.viewport.size
	app.canvas.zoom=1.35;app.canvas.pan=Vector2(23,-17)
	var saved_zoom: float=app.canvas.zoom;var saved_pan: Vector2=app.canvas.pan
	var camera: Camera3D=app.renderer.camera;var editor=app.pose_editor;editor.auto_key.button_pressed=false
	for extent in [Vector2(1200,360),Vector2(480,760)]:
		for roll in [0.,.4]:
			app.canvas.size=extent;app.mode.select(1);app.change_mode(1);app.scene_view.set_setup(true,false)
			camera.position=Vector3(0,1,5);camera.look_at(Vector3(0,1,0));camera.rotate_object_local(Vector3.BACK,roll)
			app.keys=[Timeline.key(0,camera.position,camera.quaternion,camera.fov)]
			var point:=Vector2(-250,540) if extent.x>extent.y else Vector2(960,-500)
			var origin: Vector3=camera.project_position(point,5.)-Vector3(0,.5,0)
			rig.data.position=[origin.x,origin.y,origin.z];rig.data.rotation_xyzw=[0,0,0,1];rig.data.scale=1.
			app.renderer.evaluate(app.keys,0);app.world_selection.select_entity("",false);app.scene_view.sync();await settled()
			var scene: Rect2=app.canvas.scene_rect();var frame: Rect2=app.canvas.image_rect();var screen:=local_pixel(point)
			check(app.canvas.scene_setup and scene.size==Vector2(app.scene_view.viewport.size) and frame.size.x/frame.size.y>1.77,"Setup fills the exact wide/tall texture extent while retaining native frame aspect")
			check(app.canvas.scene_contains(point) and not Rect2(Vector2.ZERO,app.canvas.resolution).has_point(point),"the test model lies genuinely beyond native output and inside the editable scene")
			var image:=view_image();var pixel:=image.get_pixelv(Vector2i(screen))
			check(pixel.g>.45 and pixel.b>.3,"actual shared-world scene pixels show the off-frame model at its native-projected location")
			check(not app.scene_view.camera.get_cull_mask_value(20),"Setup camera excludes colored selection-ID geometry")
			pointer(point,true);pointer(point,false);await settled()
			check(app.world_selection.selected==id and app.mode.selected==2,"actual canvas click selects the visible off-frame model")
			var selected:=view_image();var green:=0
			for y in range(maxi(0,int(screen.y)-55),mini(image.get_height(),int(screen.y)+55)):
				for x in range(maxi(0,int(screen.x)-55),mini(image.get_width(),int(screen.x)+55)):
					var color:=selected.get_pixel(x,y)
					if color.g>.7 and color.r<.4 and color.b<.65:green+=1
			check(green>10 and app.world_selection.viewport.size==app.scene_view.viewport.size,"selection outline and ID mask agree with the full-area scene")
			editor.selected="@root";editor.operation.select(0);editor.space.select(1);editor.update_gizmo();await settled()
			var rings: Array=editor.handles.filter(func(h):return h.get("view",false) and h.get("enabled",false))
			check(rings.size()==1,"off-frame model retains the camera-facing rotation ring")
			if rings.size()==1:
				var before: Dictionary=rig.data.duplicate(true);var handle: Dictionary=rings[0]
				pointer(handle.points[6],true);motion(handle.points[8])
				check(editor.dragging and rig.data!=before,"off-frame ring starts an actual pose gesture in Setup")
				editor.finish_drag(true);check(rig.data==before,"cancelling the off-frame pose restores exact authored data")
				pointer(handle.points[6],true);motion(handle.points[8]);var count: int=app.history.size()
				var release:=InputEventMouseButton.new();release.button_index=MOUSE_BUTTON_LEFT;release.pressed=false;release.position=Vector2(1390,890);app._input(release)
				check(not editor.dragging and app.history.size()==count+1,"a release outside the canvas completes the active gesture safely")
				app.undo();check(rig.data==before,"Undo restores the completed off-frame edit")
			var navigation_view: Dictionary=app.renderer.view_state();var paper_pan: Vector2=app.canvas.pan
			var middle:=InputEventMouseButton.new();middle.button_index=MOUSE_BUTTON_MIDDLE;middle.pressed=true;middle.position=screen;app.canvas._gui_input(middle)
			var middle_motion:=InputEventMouseMotion.new();middle_motion.position=screen+Vector2(0,14);middle_motion.relative=Vector2(0,14);middle_motion.button_mask=MOUSE_BUTTON_MASK_MIDDLE;app.canvas._gui_input(middle_motion)
			check(app.navigating and app.camera_buttons==MOUSE_BUTTON_MASK_MIDDLE and app.canvas.pan==paper_pan,"Setup Pose middle drag navigates the 3D view without changing drawing paper pan")
			middle.pressed=false;middle.position=middle_motion.position;app.canvas._gui_input(middle)
			check(not app.navigating and app.renderer.view_state()!=navigation_view,"Setup navigation release safely restores ordinary cursor control")
			app.renderer.restore_view(navigation_view);await settled()
			app.world_selection.select_entity("",false);await settled()
			var final_before: Image=await app.renderer.capture(app.keys,app.layers,0,true)
			await settled();var before_guides:=view_image()
			var view: Dictionary=app.renderer.view_state();var keys: Array=app.keys.duplicate(true);var video: Dictionary=app.video.duplicate(true);var world: Dictionary=app.renderer.world_state();var history: int=app.history.size();var dirty: bool=app.dirty
			app.scene_view.set_guides(true,true,false);await settled();var after_guides:=view_image();var inside_changes:=0;var outside_changes:=0
			for y in range(2,int(extent.y)-2):
				for x in range(2,int(extent.x)-2):
					if before_guides.get_pixel(x,y)==after_guides.get_pixel(x,y):continue
					if frame.grow(2).has_point(Vector2(x,y)):inside_changes+=1
					else:outside_changes+=1
			check(inside_changes>200 and outside_changes==0,"white frame and 3×3 guides appear only inside the output frame")
			after_guides.save_png(folder.path_join("guides-%dx%d-roll%d.png"%[int(extent.x),int(extent.y),roundi(roll*100)]))
			var final_after: Image=await app.renderer.capture(app.keys,app.layers,0,true)
			check(final_before.get_data()==final_after.get_data() and final_after.get_size()==native_size,"guides and display aspect never change native captured output pixels or dimensions")
			check(final_after.get_pixel(960,540)==Color.MAGENTA and Drawing.image(cel).get_data()==cel_before,"the independent raster cel remains in native output coordinates")
			app.scene_view.set_setup(false,false);app.world_selection.select_entity("",false);await settled()
			check(not app.canvas.scene_contains(point),"Camera focus rejects the same off-frame scene target")
			pointer(point,true);pointer(point,false);await settled()
			check(app.world_selection.selected.is_empty() and not editor.dragging,"focused margin click cannot select or pose invisible scene geometry")
			var final_focus: Image=await app.renderer.capture(app.keys,app.layers,0,true)
			check(final_focus.get_data()==final_before.get_data(),"Focused and Setup views produce exactly the same native render")
			check(app.keys==keys and app.video==video and app.renderer.world_state()==world and app.renderer.view_state()==view and app.history.size()==history and app.dirty==dirty,"view options do not edit shot keys, world, video, Undo, dirty state or temporary camera")
			app.scene_view.set_setup(true,false);app.world_selection.choose_at(point);app.canvas.size=extent-Vector2(17,11);app.scene_view.sync();await settled()
			check(app.world_selection.selected.is_empty(),"resize invalidates a queued old-view selection readback")
			app.canvas.size=extent;app.scene_view.sync();await settled();app.world_selection.choose_at(point);app.scene_view.set_setup(false,false);await settled()
			check(app.world_selection.selected.is_empty(),"changing view mode invalidates a queued selection readback")
			app.scene_view.set_setup(true,false);app.scene_view.set_guides(false,false,false);await settled()
			image.save_png(folder.path_join("setup-%dx%d-roll%d.png"%[int(extent.x),int(extent.y),roundi(roll*100)]));selected.save_png(folder.path_join("selected-%dx%d-roll%d.png"%[int(extent.x),int(extent.y),roundi(roll*100)]))
			cases.append({"extent":str(extent),"roll":roll,"green_outline_pixels":green,"guide_pixels":inside_changes,"outside_guide_pixels":outside_changes})
	# A recovery thumbnail requests a current native frame even while Setup has
	# suspended ordinary native drawing. Capture the real caller's detached input.
	rig.data.position=[-.2,0,0];app.renderer.evaluate(app.keys,0);app.scene_view.sync();await settled()
	app.scene_view.set_setup(false,false);app.canvas.size=Vector2(1200,360);app.scene_view.sync();await settled()
	var center: Vector2=camera.unproject_position(rig.root.to_global(Vector3(0,.5,0)));var old_frame: Rect2=app.canvas.image_rect()
	app.world_selection.choose_at(center);app.canvas.size+=Vector2(21,0);app.scene_view.sync();await settled()
	check(app.canvas.image_rect().size==old_frame.size and app.canvas.image_rect().position!=old_frame.position and app.world_selection.selected==id,"queued native pick survives a pure frame translation with unchanged size and camera")
	app.world_selection.select_entity("",false);app.scene_view.set_setup(true,false);await settled()
	var cached: Image=await app.renderer.readback_native();camera.position+=Vector3(10,0,0);app.scene_view.sync();await settled()
	check(app.renderer.viewport.render_target_update_mode==SubViewport.UPDATE_DISABLED,"Setup suspends the unused native scene pass")
	var recorder:=CapturedPreview.new();var previous=app.recovery_preview;app.recovery_preview=recorder
	await app.finish_recovery_preview(app.recovery_root.path_join(app.recovery_session),"a".repeat(64),app.frame,app.recovery_revision,app.renderer.view_state())
	check(recorder.image!=null and recorder.image.get_size()==native_size and recorder.image.get_data()!=cached.get_data() and app.renderer.native_readbacks==0,"recovery receives fresh native pixels after Setup camera movement and releases its readback scope")
	app.recovery_preview=previous
	app.mode.select(0);app.change_mode(0);await settled()
	check(app.canvas.zoom==saved_zoom and app.canvas.pan==saved_pan and not app.canvas.scene_setup,"returning to Draw restores the unchanged paper zoom and pan")
	var pixels:=Drawing.image(cel).get_data();var start:=InputEventMouseButton.new();start.button_index=MOUSE_BUTTON_LEFT;start.pressed=true
	app.canvas_input(start,Vector2(-10,540));check(not app.drawing and Drawing.image(cel).get_data()==pixels,"Draw still refuses edits beyond native output bounds")
	app.tool.select(3);var captures: int=app.color_sampler.captures;app.color_sampler.start(Vector2(-10,540))
	check(app.color_sampler.context.is_empty() and app.color_sampler.captures==captures,"color sampling still refuses native-exterior pixels")
	app.tool.select(0);app.color.color=Color.CYAN;app.radius.value=4;pointer(Vector2(600,400),true);pointer(Vector2(600,400),false)
	check(Drawing.image(cel).get_pixel(600,400)==Color.CYAN,"actual Draw input still maps zoomed/panned canvas pixels to the native cel")
	app.undo();check(Drawing.image(cel).get_data()==pixels,"drawing Undo restores exact independent cel pixels")
	app.scene_view.set_setup(false);app.scene_view.set_guides(true,true)
	var prefs:=ConfigFile.new();check(prefs.load(app.display_prefs_path)==OK and prefs.get_value("scene_view","setup",true)==false and prefs.get_value("scene_view","thirds",false),"view preferences persist outside project data")
	check(FileAccess.get_sha256(fixture)==source_hash and app.renderer.viewport.size==native_size,"source geometry and native render viewport remain unchanged")
	app.canvas.free();app.free();await process_frame
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("reopen-recovery");app.recent_path=folder.path_join("reopen-recent.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settled()
	check(not app.scene_view.setup_enabled and app.scene_view.frame_enabled and app.scene_view.grid_enabled,"a fresh application restores personal focus and guide preferences")
	var report:={"checks":checks,"failures":failures,"cases":cases,"native_size":str(native_size),"source_sha256":source_hash}
	var out:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);out.store_string(JSON.stringify(report,"",true,true));out.close()
	print("SCENE_VIEW "+JSON.stringify(report));app.free();quit(0 if failures==0 else 1)
