extends "res://tests/movement_path_smoke.gd"
const CameraEdits=preload("res://src/camera_key_edits.gd")
func _initialize() -> void:
	create_timer(150).timeout.connect(func():push_error("Camera timeline UX watchdog");quit(2));call_deferred("run")
func reveal_view(view: Control) -> void:
	var dock_scroll: ScrollContainer=app.workspace_layout.panels.timeline.get_node("TimelineContentScroll")
	dock_scroll.ensure_control_visible(view.get_parent() if view==app.timeline else view);await settled()
func double_at(view: Control,point: Vector2) -> void:
	await reveal_view(view)
	var press:=InputEventMouseButton.new();press.button_index=MOUSE_BUTTON_LEFT;press.pressed=true;press.double_click=true;event_at(view,point,press);await process_frame
	var release:=InputEventMouseButton.new();release.button_index=MOUSE_BUTTON_LEFT;event_at(view,point,release);await settled()
func wheel(view: Control,point: Vector2,index: int) -> void:
	await reveal_view(view)
	for down in [true,false]:
		var event:=InputEventMouseButton.new();event.button_index=index;event.ctrl_pressed=true;event.pressed=down;event_at(view,point,event);await process_frame
	await settled()
func press_key(view: Control,at: int) -> void:
	await reveal_view(view)
	var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.pressed=true;event_at(view,Vector2(view.x(at),38),event);await process_frame
func drag_motion(view: Control,at: int) -> void:
	var event:=InputEventMouseMotion.new();event.button_mask=MOUSE_BUTTON_MASK_LEFT;event_at(view,Vector2(view.x(at),38),event);await process_frame
func release_key(view: Control,at: int) -> void:
	var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event_at(view,Vector2(view.x(at),38),event);await settled()
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
	var prefs:=ConfigFile.new();prefs.set_value("display","theme","light" if "--classic" in OS.get_cmdline_user_args() else "neon");prefs.set_value("display","percent",150 if "--150" in OS.get_cmdline_user_args() else 100);prefs.save(folder.path_join("prefs.cfg"))
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false
	app.set_advanced("--advanced" in OS.get_cmdline_user_args());await settled()
	app.mode.select(1);app.change_mode(1);app.set_frame(48);app.insert_key();app.set_frame(12);await settled()
	var ruler=app.timeline_ruler;var tracks=app.timeline;var nav=app.timeline_navigation;var editor=app.camera_key_editor
	var original: Array=app.keys.duplicate(true);var video: Dictionary=app.video.duplicate(true);var world: Dictionary=app.current_world().duplicate(true);var layers: PackedByteArray=var_to_bytes(app.layers)
	var history: int=app.history.size();var revision: int=app.recovery_revision
	await reveal_view(ruler)
	check(video.duration_frames==48 and ruler.header_only and tracks.hide_header,"actual compact default has distinct ruler and tracks at48frames")
	await click_at(ruler,Vector2(ruler.x(0),38))
	check(editor.selected_frame==0 and not editor.active() and app.frame==0,"actual diamond selects and seeks without getting stuck")
	check(app.keys==original and app.history.size()==history and app.recovery_revision==revision,"selection creates no authored change")
	await press_key(ruler,0);await drag_motion(ruler,8)
	check(editor.active() and editor.preview_frame==8 and app.keys==original and app.history.size()==history,"actual drag previews without authored mutation")
	await wheel(ruler,Vector2(ruler.x(8),10),MOUSE_BUTTON_WHEEL_UP)
	check(nav.visible()==48,"Ctrl wheel cannot change a live key drag mapping")
	await release_key(ruler,8)
	var shifted: Array=app.keys.duplicate(true)
	check(shifted[0].frame==8 and shifted[1]==original[1] and app.history.size()==history+1,"release retimes only selected key in one real Undo")
	var restored_key: Dictionary=shifted[0].duplicate(true);restored_key.frame=0
	check(restored_key==original[0],"retime preserves position rotation lens interpolation and range")
	app.undo();check(app.keys==original,"actual Undo restores exact original keys")
	app.redo();check(app.keys==shifted,"actual Redo restores exact retime")
	history=app.history.size();revision=app.recovery_revision
	await drag(ruler,Vector2(ruler.x(8),38),Vector2(1,0))
	check(app.keys==shifted and app.history.size()==history and app.recovery_revision==revision,"subthreshold gesture remains selection")
	await drag(ruler,Vector2(ruler.x(8),38),Vector2(ruler.x(48)-ruler.x(8),0))
	check(app.keys==shifted and app.history.size()==history,"occupied target refuses without replacing either key")
	await press_key(ruler,8);await drag_motion(ruler,16)
	var escape:=InputEventKey.new();escape.keycode=KEY_ESCAPE;escape.pressed=true;ruler.get_viewport().push_input(escape,true);await release_key(ruler,16)
	check(not editor.active() and app.keys==shifted and app.history.size()==history,"actual Escape cancels the key ghost")
	app.set_frame(18);app.renderer.camera.fov=67.;app.renderer.camera.near=.004;app.renderer.camera.far=8000.
	var capture: Dictionary=preload("res://src/timeline.gd").from_camera(18,app.renderer.camera,app.interpolation.get_item_text(app.interpolation.selected))
	await double_at(ruler,Vector2(ruler.x(18),38))
	check(CameraEdits.index_at(app.keys,18)>=0 and app.history.size()==history+1 and app.keys[CameraEdits.index_at(app.keys,18)]==capture,"empty Camera lane double-click captures current view with one Undo")
	var with_added: Array=app.keys.duplicate(true);history=app.history.size()
	await double_at(ruler,Vector2(ruler.x(18),38))
	check(app.keys==shifted and app.history.size()==history+1,"existing Camera diamond double-click removes only that key")
	app.undo();check(app.keys==with_added,"Undo removal restores the exact captured view")
	app.redo();check(app.keys==shifted,"Redo removal restores remaining keys")
	await double_at(ruler,Vector2(ruler.x(48),38));history=app.history.size();revision=app.recovery_revision
	await double_at(ruler,Vector2(ruler.x(8),38))
	check(app.keys.size()==1 and app.keys[0].frame==8 and app.history.size()==history and app.recovery_revision==revision,"last camera key double-click is refused without dirty or Undo")
	check(app.video==video and app.current_world()==world and var_to_bytes(app.layers)==layers,"camera edits preserve video world and drawing content")
	history=app.history.size();revision=app.recovery_revision
	nav.fit_all();await wheel(ruler,Vector2(ruler.x(24),10),MOUSE_BUTTON_WHEEL_UP)
	check(nav.visible()==24 and ruler.window_span==tracks.window_span,"48-frame docked ruler routes real Ctrl wheel to both views")
	await wheel(tracks,Vector2(tracks.x(24),minf(20,tracks.size.y*.5)),MOUSE_BUTTON_WHEEL_UP)
	check(nav.visible()==12 and ruler.window_start==tracks.window_start,"compact tracks route real Ctrl wheel down to12frames")
	await wheel(ruler,Vector2(ruler.x(24),10),MOUSE_BUTTON_WHEEL_DOWN)
	check(nav.visible()==24,"Ctrl wheel down zooms out again")
	nav.fit_all();app.workspace_layout.float_panel("timeline");await settled()
	check(ruler.get_window()!=app.get_window() and nav.bar.get_window()==ruler.get_window(),"timeline ruler and zoom controls belong to actual floated window")
	await wheel(ruler,Vector2(ruler.x(24),10),MOUSE_BUTTON_WHEEL_UP)
	check(nav.visible()==24 and ruler.window_span==tracks.window_span,"floated48-frame ruler routes real Ctrl wheel")
	nav.fit_all()
	var press:=InputEventMouseButton.new();press.button_index=MOUSE_BUTTON_LEFT;press.pressed=true;event_at(ruler,Vector2(ruler.x(24),10),press);await process_frame
	check(ruler.dragging and nav.busy(),"actual unreleased ruler seek enters zoom guard")
	# Controlled delivery of the real focus-loss notification, not a claim of reproduced OS ordering.
	ruler.notification(Node.NOTIFICATION_WM_WINDOW_FOCUS_OUT);await process_frame
	check(not ruler.dragging and not nav.busy(),"floating view focus-loss notification clears stale generic seek")
	await wheel(ruler,Vector2(ruler.x(24),10),MOUSE_BUTTON_WHEEL_UP)
	check(nav.visible()==24,"Ctrl wheel works after interrupted seek without an invented release")
	await release_key(ruler,24)
	nav.fit_all();await press_key(ruler,8);await drag_motion(ruler,14);ruler.notification(Node.NOTIFICATION_WM_WINDOW_FOCUS_OUT);await process_frame
	check(not editor.active() and app.keys.size()==1 and app.keys[0].frame==8,"focus loss cancels a floated key retime without mutation")
	await release_key(ruler,14)
	app.workspace_layout.dock("timeline","bottom");await settled()
	app.get_window().size=Vector2i(1200,760);await settled();nav.fit_all()
	await wheel(ruler,Vector2(ruler.x(24),10),MOUSE_BUTTON_WHEEL_UP)
	check(nav.visible()==24 and ruler.size.x==tracks.size.x,"smaller redocked window retains real wheel route")
	check(app.history.size()==history and app.recovery_revision==revision,"zoom focus-loss and cancelled gestures author no history")
	check(app.current_world()==world and var_to_bytes(app.layers)==layers,"all routed camera and zoom events preserve unrelated authored content")
	app.new_project();await settled()
	check(not editor.active() and editor.selected_frame==-1,"New clears session selection and drag context")
	app.mode.select(1);app.change_mode(1);app.set_frame(0);await press_key(ruler,0);await drag_motion(ruler,8)
	app.renderer.camera.fov=66.;app.insert_key();var independently_edited: Array=app.keys.duplicate(true);history=app.history.size();await release_key(ruler,8)
	check(not editor.active() and app.keys==independently_edited and app.history.size()==history,"independent ordinary camera edit invalidates ghost without overwrite")
	await press_key(ruler,0);await drag_motion(ruler,8);app.new_project();await settled();var next_project: Array=app.keys.duplicate(true);history=app.history.size();await release_key(ruler,8)
	check(not editor.active() and editor.selected_frame==-1 and app.keys==next_project and app.history.size()==history,"release after New cannot commit a previous project camera key")
	await click_at(ruler,Vector2(ruler.x(0),38));var child: String=app.sequence_editor.new_sequence("Camera context");app.sequence_editor.enter(child);await settled()
	check(editor.selected_frame==-1 and not editor.active(),"entering another scene clears selection even if both scenes have a frame-zero key")
	app.sequence_editor.return_to_parent();await settled()
	app.get_viewport().get_texture().get_image().save_png(folder.path_join("camera-timeline.png"))
	print("CAMERA_TIMELINE_UX_SMOKE ",JSON.stringify({"checks":checks,"failures":failures,"controlled_focus_loss_notification":true}));await app.quit_studio();quit(0 if failures==0 else 1)
