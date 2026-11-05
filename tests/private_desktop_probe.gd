extends SceneTree
const Renderer=preload("res://src/renderer.gd")
const SceneIO=preload("res://src/scene3d.gd")
const Timeline=preload("res://src/timeline.gd")
func _initialize() -> void:
	create_timer(20).timeout.connect(func():push_error("Hidden GPU probe watchdog");quit(2));call_deferred("run")
func run() -> void:
	var folder:=ProjectSettings.globalize_path("res://output/private-desktop-probe");DirAccess.make_dir_recursive_absolute(folder)
	var renderer:=Renderer.new();root.add_child(renderer);renderer.setup(640,360)
	var path:=folder.path_join("room.glb");SceneIO.make_fixture(path);var error:=renderer.import_scene(path)
	if not error.is_empty():push_error(error);quit(2);return
	renderer.camera.position=Vector3(0,1.5,4);renderer.camera.look_at(Vector3(0,1,-3))
	var keys: Array=[Timeline.key(0,renderer.camera.position,renderer.camera.quaternion,60)]
	var image: Image=await renderer.capture(keys,[],0,true);var bytes:=image.get_data();var colors:={}
	for i in range(0,bytes.size(),4*17):colors[str(bytes[i])+","+str(bytes[i+1])+","+str(bytes[i+2])]=true
	image.save_png(folder.path_join("gpu-scene.png"))
	root.gui_embed_subwindows=false
	var popup:=Window.new();root.add_child(popup);popup.title="Owned hidden probe";popup.size=Vector2i(260,100)
	var fill:=ColorRect.new();fill.color=Color("ffd27d");popup.add_child(fill);fill.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	popup.popup_centered();await create_timer(1).timeout;await RenderingServer.frame_post_draw
	var popup_image:=popup.get_texture().get_image();popup_image.save_png(folder.path_join("native-popup.png"))
	var result:={"display":DisplayServer.get_name(),"adapter":RenderingServer.get_video_adapter_name(),"colors":colors.size(),"width":image.get_width(),"height":image.get_height(),"popup_pixel":popup_image.get_pixel(30,30).to_html()}
	var f:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);f.store_string(JSON.stringify(result));f.close()
	var valid:=DisplayServer.get_name().to_lower()=="windows" and colors.size()>10 and popup_image.get_pixel(30,30).r>0.8
	print("PRIVATE_GPU "+JSON.stringify(result));popup.free();renderer.free();quit(0 if valid else 1)
