extends SceneTree
const SceneView=preload("res://src/scene_view.gd")
const Canvas=preload("res://src/canvas_view.gd")
var checks:=0
var failures:=0
var cases: Array=[]
func _initialize() -> void:call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1
	if not ok:failures+=1;print("FAIL "+label)
func run() -> void:
	var native:=SubViewport.new();native.own_world_3d=true;root.add_child(native)
	var camera:=Camera3D.new();native.add_child(camera);camera.current=true;camera.near=.05;camera.far=2000.;camera.cull_mask=1048575 & ~(1<<19)
	var preview:=SubViewport.new();preview.world_3d=native.find_world_3d();root.add_child(preview)
	var display:=Camera3D.new();preview.add_child(display);display.current=true
	var canvas:=Canvas.new();root.add_child(canvas);canvas.zoom=1.7;canvas.pan=Vector2(43,-29)
	await process_frame
	var samples:=0;var outside:=0;var maximum:=0.;var ray_maximum:=0.
	for dimensions in [Vector2i(1920,1080),Vector2i(1280,720),Vector2i(960,540)]:
		native.size=dimensions;canvas.resolution=Vector2(dimensions)
		for extent in [Vector2(1200,360),Vector2(480,760),Vector2(600,600),Vector2(1200.75,360.25)]:
			canvas.size=extent;canvas.scene_editing=true;canvas.scene_setup=false
			var paper: Rect2=canvas.image_rect();var zoom: float=canvas.zoom;var pan: Vector2=canvas.pan
			canvas.scene_setup=true;preview.size=canvas.setup_size()
			var frame: Rect2=canvas.image_rect();var area: Rect2=canvas.scene_rect()
			check(area.size==Vector2(preview.size) and area.size.x<=extent.x and area.size.y<=extent.y,"full scene uses the actual integer preview aspect without stretching")
			check(is_equal_approx(frame.size.x/frame.size.y,float(dimensions.x)/dimensions.y),"film frame retains native output aspect")
			for keep in [Camera3D.KEEP_HEIGHT,Camera3D.KEEP_WIDTH]:
				camera.keep_aspect=keep;camera.fov=60.
				for eye in [Vector3(3,2,4),Vector3(-4,1,-3),Vector3(.2,4,1)]:
					for roll in [0.,.6]:
						camera.position=eye;camera.look_at(Vector3.ZERO);camera.rotate_object_local(Vector3.BACK,roll)
						var before: Array=[camera.global_transform,camera.fov,camera.near,camera.far,camera.keep_aspect,camera.cull_mask,native.size]
						SceneView.copy_camera(camera,display,native.size,preview.size,true)
						var error:=0.;var rays:=0.;var extended:=0
						for depth in [1.,5.,20.]:
							for x in range(-4,5):
								for y in range(-4,5):
									var world: Vector3=camera.global_transform*Vector3(x*depth*.35,y*depth*.35,-depth)
									var pixel: Vector2=camera.unproject_position(world)
									var mapped: Vector2=frame.position+pixel/canvas.resolution*frame.size
									if area.has_point(mapped):
										error=maxf(error,mapped.distance_to(area.position+display.unproject_position(world)))
										check(canvas.scene_contains(pixel),"visible virtual native point is editable in Setup")
										if not Rect2(Vector2.ZERO,canvas.resolution).has_point(pixel):extended+=1
									samples+=1
						for x in [.05,.25,.5,.75,.95]:
							for y in [.05,.25,.5,.75,.95]:
								var screen: Vector2=area.position+area.size*Vector2(x,y)
								var pixel: Vector2=(screen-frame.position)/frame.size*canvas.resolution
								rays=maxf(rays,camera.project_ray_normal(pixel).distance_to(display.project_ray_normal(screen-area.position)))
								check(canvas.scene_uv(pixel).distance_to(Vector2(x,y))<.00001,"ID-mask UV uses the displayed scene rather than fixed half native pixels")
						check(error<.01 and rays<.000003,"actual display camera agrees with native projections and rays across view/roll/aspect")
						check(display.cull_mask==camera.cull_mask and not display.get_cull_mask_value(20),"extended scene excludes shared selection ID copies")
						check(before==[camera.global_transform,camera.fov,camera.near,camera.far,camera.keep_aspect,camera.cull_mask,native.size],"editor projection never mutates the native shot")
						maximum=maxf(maximum,error);ray_maximum=maxf(ray_maximum,rays);outside+=extended
						cases.append({"native":str(dimensions),"extent":str(extent),"roll":roll,"keep":keep,"projection_error":error,"ray_error":rays,"outside":extended})
			canvas.scene_setup=false
			check(canvas.image_rect()==paper and canvas.zoom==zoom and canvas.pan==pan,"Focus/Draw restore the exact preserved paper zoom and pan")
			check(not canvas.scene_contains(Vector2(-5000,-5000)),"Focus rejects native-exterior click targets")
	check(cases.size()==144 and outside>1000,"mapping exercises all configurations and many visible off-frame points")
	check(not canvas.scene_contains(Vector2(INF,0)),"nonfinite click coordinates cannot enter scene tools")
	var report:={"checks":checks,"failures":failures,"cases":cases.size(),"world_samples":samples,"outside_native_samples":outside,"maximum_projection_error_pixels":maximum,"maximum_ray_error":ray_maximum}
	var args:=OS.get_cmdline_user_args();var path: String=args[0].path_join("unit.json") if not args.is_empty() else "res://output/scene-view-unit.json"
	var file:=FileAccess.open(path,FileAccess.WRITE);file.store_string(JSON.stringify(report,"",true,true));file.close()
	print("SCENE_VIEW_UNIT "+JSON.stringify(report));canvas.free();preview.free();native.free();quit(0 if failures==0 else 1)
