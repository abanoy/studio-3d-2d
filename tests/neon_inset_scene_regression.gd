# SOURCE-ONLY DRAFT, NOT EXECUTED. Run against the isolated redesign checkout after its current
# graphics lease closes. Tests actual Godot projection/ray APIs with the new nonzero frame inset.
extends SceneTree
const SceneView = preload("res://src/scene_view.gd")
const Canvas = preload("res://src/canvas_view.gd")
var checks := 0
var failures := 0
var maximum_projection_error := 0.0
var maximum_ray_error := 0.0
var configurations := 0

func _initialize() -> void: call_deferred("run")

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		print("FAIL " + label)

func run() -> void:
	var native := SubViewport.new()
	native.own_world_3d = true
	root.add_child(native)
	var source := Camera3D.new()
	native.add_child(source)
	source.current = true
	var preview := SubViewport.new()
	preview.world_3d = native.find_world_3d()
	root.add_child(preview)
	var target := Camera3D.new()
	preview.add_child(target)
	target.current = true
	var canvas := Canvas.new()
	root.add_child(canvas)
	canvas.scene_editing = true
	canvas.scene_setup = true
	await process_frame
	for dimensions in [Vector2i(1920,1080), Vector2i(1080,1920), Vector2i(1024,1024)]:
		native.size = dimensions
		canvas.resolution = Vector2(dimensions)
		for extent in [Vector2(1200,360), Vector2(480,760), Vector2(600,600), Vector2(1200.75,360.25)]:
			canvas.size = extent
			preview.size = canvas.setup_size()
			for inset in [Vector2.ZERO, Vector2(24,40), Vector2(48,63), Vector2(16,90)]:
				canvas.fit_inset = inset
				var frame: Rect2 = canvas.image_rect()
				var area: Rect2 = canvas.scene_rect()
				check(frame.size.is_equal_approx(canvas.setup_frame_size()), "setup frame helper equals displayed native frame")
				check(frame.get_center().distance_to(area.get_center()) < 0.001, "nonzero inset keeps the native film centered")
				for keep in [Camera3D.KEEP_HEIGHT, Camera3D.KEEP_WIDTH]:
					source.keep_aspect = keep
					for fov in [15.0,60.0,120.0]:
						source.fov = fov
						for roll in [0.0,0.6]:
							source.position = Vector3(3,2,4)
							source.look_at(Vector3.ZERO)
							source.rotate_object_local(Vector3.BACK, roll)
							var before: Array = [source.global_transform, source.fov, source.keep_aspect, native.size]
							SceneView.copy_camera(source,target,native.size,preview.size,true,canvas.setup_frame_size())
							configurations += 1
							for fraction in [Vector2(.01,.01),Vector2(.2,.7),Vector2(.5,.5),Vector2(.95,.1),Vector2(.99,.99)]:
								var screen: Vector2 = area.position + area.size * fraction
								var pixel: Vector2 = (screen - frame.position) / frame.size * canvas.resolution
								var ray_error := source.project_ray_normal(pixel).distance_to(target.project_ray_normal(screen-area.position))
								maximum_ray_error = maxf(maximum_ray_error,ray_error)
								check(ray_error < 0.000003, "inset native and display ray directions agree")
								var world: Vector3 = source.project_position(pixel,5.0)
								var projection_error := screen.distance_to(area.position + target.unproject_position(world))
								maximum_projection_error = maxf(maximum_projection_error,projection_error)
								check(projection_error < 0.01, "inset native and display point projection agree")
								check(canvas.scene_contains(pixel), "inset off-frame setup positions remain editable")
								check(canvas.scene_uv(pixel).distance_to(fraction)<0.00001, "inset ID-mask UV follows full display area")
							check(before == [source.global_transform,source.fov,source.keep_aspect,native.size], "inset presentation leaves the native shot unchanged")
				for screen in [area.position+Vector2(0,area.size.y/2),area.position+Vector2(area.size.x/2,0)]:
					var pixel: Vector2 = (screen-frame.position)/frame.size*canvas.resolution
					check(canvas.scene_contains(pixel), "round-tripped exact top/left setup edge is accepted")
				for screen in [area.position-Vector2(.02,.02),area.end+Vector2(.02,.02)]:
					var pixel: Vector2 = (screen-frame.position)/frame.size*canvas.resolution
					check(not canvas.scene_contains(pixel), "genuine off-scene pointer exceeds the .01 pixel tolerance")
	var report := {"status":"PASS" if failures==0 else "FAIL", "checks":checks,"failures":failures,
		"configurations":configurations,"maximum_projection_error_pixels":maximum_projection_error,
		"maximum_ray_error":maximum_ray_error,"native_assets_used":false}
	var encoded := JSON.stringify(report,"",true,true)
	var args := OS.get_cmdline_user_args()
	if not args.is_empty():
		var file := FileAccess.open(args[0],FileAccess.WRITE)
		if file: file.store_string(encoded); file.close()
		else: failures += 1; print("FAIL cannot create requested result")
	print("INSET_SCENE_REGRESSION " + encoded)
	canvas.free()
	preview.free()
	native.free()
	quit(0 if failures==0 else 1)
