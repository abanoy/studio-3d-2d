extends "res://tests/movement_path_smoke.gd"
const Drawing=preload("res://src/drawing.gd")
var layer: Dictionary
var view
func _initialize() -> void:
	create_timer(100).timeout.connect(func():push_error("Drawing exposure edge watchdog");quit(2));call_deferred("run")
func mouse(point: Vector2,pressed: bool) -> void:
	var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.pressed=pressed;event_at(view,point,event);await settled()
func motion(point: Vector2,pressed:=true) -> void:
	var event:=InputEventMouseMotion.new();event.button_mask=MOUSE_BUTTON_MASK_LEFT if pressed else 0;event_at(view,point,event);await process_frame
func edge(index: int) -> Vector2:return view.cel_end_handle(1,layer.cels[index]).get_center()
func run() -> void:
	folder=OS.get_cmdline_user_args()[0].path_join("exposure-edge");DirAccess.make_dir_recursive_absolute(folder)
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false
	app.mode.select(0);app.change_mode(0);layer=app.layers[1];view=app.timeline
	var image:=Drawing.blank(1920,1080);image.fill_rect(Rect2i(100,100,80,40),Color(.2,.7,.8,.5));Drawing.touch(image)
	Drawing.insert(layer,4,48,image);layer.cels[0].duration=8;Drawing.insert(layer,24,48,Drawing.blank(1920,1080));layer.cels[1].duration=8;app.changed();app.set_frame(6);await settled()
	var pixels:=image.get_data();var composite:=Drawing.composite(app.layers,6,1920,1080).get_data();var history: int=app.history.size();var bytes: int=app.history_bytes;var point:=edge(0)
	await motion(point,false);check(view.mouse_default_cursor_shape==Control.CURSOR_HSIZE,"visible drawing right edge advertises hold resizing in Simple")
	await mouse(point,true);check(view.cel_resizing and view.cel_gesture_active() and app.frame==11,"right-edge press latches duration gesture and chooses last held frame")
	var target:=point+Vector2(view.x(16)-view.x(8),0);await motion(target)
	check(view.cel_length_preview==16 and view.cel_preview==4 and layer.cels[0].duration==8 and app.history.size()==history,"right-edge motion previews only length without changing source/history")
	var navigation_span: float=app.timeline_navigation.span;app.timeline_navigation.zoom(.5,8)
	check(app.timeline_navigation.span==navigation_span,"timeline navigation cannot change coordinates during edge preview")
	var checkpoint: int=app.checkpoint_revision;app.autosave_tick(true);await preload("res://tests/recovery_wait.gd").checkpoint(app);check(app.checkpoint_revision==checkpoint,"recovery defers during right-edge preview")
	await mouse(target,false)
	check(layer.cels[0].duration==16 and layer.cels[0].start==4 and layer.cels[1].start==24,"release extends hold without shifting either drawing")
	check(app.history.size()==history+1 and app.history_bytes==bytes+512 and app.history[-1].type=="cel_exposure","right-edge release creates one512byte duration command")
	check(is_same(Drawing.image(layer.cels[0]),image) and image.get_data()==pixels,"right-edge edit preserves exact original Image/RGBA")
	check(Drawing.composite(app.layers,18,1920,1080).get_data()==composite and Drawing.cel_at(layer,20).is_empty(),"extended held pixels render exactly through end-exclusive boundary")
	app.undo();check(layer.cels[0].duration==8,"right-edge Undo restores prior hold")
	app.redo();check(layer.cels[0].duration==16,"right-edge Redo reapplies hold");app.undo()
	point=edge(0);await mouse(point,true);target=Vector2(view.x(40),point.y);await motion(target);check(view.cel_length_preview==20 and view.cel_valid,"extension preview clamps at next drawing start");await mouse(target,false)
	check(layer.cels[0].duration==20 and layer.cels[1].start==24,"clamped extension cannot overwrite neighbor");app.undo()
	point=edge(0);await mouse(point,true);target=Vector2(view.x(0),point.y);await motion(target);await mouse(target,false)
	check(layer.cels[0].duration==1 and layer.cels[0].start==4,"shortening clamps to one whole frame without moving start")
	app.undo()
	point=edge(1);await mouse(point,true);target=Vector2(view.size.x+100,point.y);await motion(target);await mouse(target,false)
	check(layer.cels[1].duration==24 and layer.cels[0].duration==8,"last drawing extension clamps at scene end");app.undo()
	point=edge(0);history=app.history.size();await mouse(point,true);await motion(point+Vector2(2,0));await mouse(point+Vector2(2,0),false)
	check(layer.cels[0].duration==8 and app.history.size()==history,"small hand motion stays a click without resize history")
	for tool in [4,3]:
		app.tool.select(tool);point=edge(0);await mouse(point,true);await motion(point+Vector2(view.x(4)-view.x(0),0))
		var escape:=InputEventKey.new();escape.keycode=KEY_ESCAPE;escape.pressed=true;root.push_input(escape,true);await process_frame;await mouse(point,false)
		check(not view.cel_gesture_active() and layer.cels[0].duration==8 and app.history.size()==history,"first Escape cancels edge preview before drawing tool%d" % tool)
		check(app.tool.selected==tool and image.get_data()==pixels,"cancel retains tool%d and original pixels" % tool)
	app.tool.select(0);point=edge(0);await mouse(point,true);await motion(point+Vector2(view.x(4)-view.x(0),0));app.changed();await mouse(point,false)
	check(layer.cels[0].duration==8 and app.history.size()==history,"stale document revision refuses edge release")
	point=edge(0);await mouse(point,true);await motion(point+Vector2(view.x(4)-view.x(0),0))
	for pressed in [true,false]:
		var right:=InputEventMouseButton.new();right.button_index=MOUSE_BUTTON_RIGHT;right.pressed=pressed;event_at(view,point,right);await process_frame
	await mouse(point,false);check(layer.cels[0].duration==8 and app.history.size()==history and not view.cel_gesture_active(),"right-click cancels edge gesture without commit")
	var foreign: Dictionary=app.cel_timing.begin(layer.id,layer.cels[0].id,6);foreign.owner="other-child";app.cel_timing.resize(layer.cels[0].id,4,foreign)
	check(layer.cels[0].duration==8 and app.history.size()==history,"edge context from another owner cannot change parent hold")
	point=edge(0);await mouse(point,true);await motion(point+Vector2(view.x(4)-view.x(0),0));view.release_focus();await process_frame;await mouse(point,false)
	check(not view.cel_gesture_active() and layer.cels[0].duration==8 and app.history.size()==history,"focus loss cancels edge gesture")
	point=edge(0);await mouse(point,true);await motion(point+Vector2(view.x(4)-view.x(0),0));app.undo();await mouse(point,false)
	check(layer.cels[0].duration==8 and app.history.size()==history,"Undo cancels pending resize before unrelated history")
	var nav=app.timeline_navigation;nav.zoom(.25,6);nav.scrollbar.value=6;await settled()
	check(not view.cel_end_handle(1,layer.cels[1]).has_area(),"offscreen drawing end has no phantom resize handle")
	point=edge(0);await mouse(point,true);target=point+Vector2(view.x(4)-view.x(0),0);await motion(target);await mouse(target,false)
	check(layer.cels[0].duration==12 and layer.cels[0].start==4,"zoomed/panned edge uses shared frame mapping")
	app.undo();check(layer.cels[0].duration==8 and image.get_data()==pixels,"zoomed resize Undo retains original pixels/range")
	app.show_project_options();app.project_options.hide()
	check(app.project_timing.apply_duration(1440).is_empty(),"long parent opens for narrow drawing target check")
	nav.fit_all();app.set_frame(4);app.exposure.value=1;app.set_exposure();await settled()
	check(view.cel_rect(1,layer.cels[0]).size.x<18 and not view.cel_end_handle(1,layer.cels[0]).has_area(),"actual long-timeline narrow drawing keeps body target without competing edge handle")
	app.get_viewport().get_texture().get_image().save_png(folder.path_join("edge.png"))
	print("CEL_EXPOSURE_EDGE ",JSON.stringify({"checks":checks,"failures":failures}));await app.quit_studio();quit(0 if failures==0 else 1)
