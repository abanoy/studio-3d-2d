extends SceneTree
# Authored source only: not parsed/run. Pure conversion/layout contracts, no app/assets.
const M=preload("res://src/editor_handle_metrics.gd")
const S=preload("res://src/shape_window_layout.gd")
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(10).timeout.connect(func():push_error("Editor geometry unit watchdog");quit(2))
	call_deferred("run")
func check(value: bool,label: String) -> void:
	checks+=1
	if not value:failures+=1
	print(("PASS " if value else "FAIL ")+"editor_geometry."+label)
func run() -> void:
	for percent in M.PERCENTS:check(M.checked_percent(percent)==percent,"supported_preference_"+str(percent))
	for value in [true,1.5,0,300,"150",null,NAN]:check(M.checked_percent(value)==150,"invalid_preference_is_read_only_default_"+str(typeof(value)))
	var frame:=Rect2(100,200,960,540)
	var screen:=Transform2D(Vector2(2,0),Vector2(0,2),Vector2(40,60))
	var before:=var_to_bytes([frame,screen])
	var result:=M.measure(150,Vector2(1920,1080),frame,screen)
	check(not result.is_empty(),"ordinary_fitted_frame_is_supported")
	if result.is_empty():quit(1);return
	var native_to_screen: Transform2D=result.native_to_screen
	check(absf((native_to_screen*Vector2(result.radius,0)-native_to_screen*Vector2.ZERO).length()-105.)<.0001,"default_RGB_radius_is_105_physical_pixels")
	check(absf((native_to_screen*Vector2(result.view_radius,0)-native_to_screen*Vector2.ZERO).length()-135.)<.0001,"default_view_ring_is_135_physical_pixels")
	check(result.hit_pixels==15.,"default_grabbing_band_is_larger_than_old_ten_pixels")
	check((native_to_screen*Vector2(960,540)).distance_to(Vector2(1200,1000))<.0001,"pan_and_window_origin_are_included_in_pointer_conversion")
	for ui in [1.,1.25,1.5,2.]:
		var matrix:=Transform2D(Vector2(ui,0),Vector2(0,ui),Vector2.ZERO)
		var current:=M.measure(150,Vector2(1920,1080),Rect2(Vector2.ZERO,Vector2(960,540)/ui),matrix)
		var converted: Transform2D=current.native_to_screen
		check(absf(converted.x.length()*current.radius-105.)<.0001 and current.hit_pixels==15.,"constant_physical_handles_with_interface_scale_"+str(ui))
	var full:=M.measure(150,Vector2(1920,1080),Rect2(0,0,960,540),Transform2D.IDENTITY)
	var four_k:=M.measure(150,Vector2(3840,2160),Rect2(0,0,960,540),Transform2D.IDENTITY)
	check(absf(four_k.radius/full.radius-2.)<.0001 and absf(four_k.native_to_screen.x.length()*four_k.radius-105.)<.0001,"4K_native_resolution_does_not_shrink_editor_handles")
	for width in [640.,1280.]:
		var zoomed:=M.measure(150,Vector2(1920,1080),Rect2(0,0,width,width*9./16.),Transform2D.IDENTITY)
		check(absf(zoomed.native_to_screen.x.length()*zoomed.radius-105.)<.0001,"canvas_fit_or_zoom_does_not_shrink_handles_"+str(width))
	var bad_cases: Array=[
		[300,Vector2(1920,1080),frame,screen],
		[150,Vector2.ZERO,frame,screen],
		[150,Vector2(NAN,1080),frame,screen],
		[150,Vector2(1920,1080),Rect2(),screen],
		[150,Vector2(1920,1080),frame,Transform2D(Vector2.ONE,Vector2.ONE,Vector2.ZERO)],
		[150,Vector2(1920,1080),frame,Transform2D(Vector2.RIGHT,Vector2.DOWN,Vector2(INF,0))]]
	for i in range(bad_cases.size()):
		var bad: Array=bad_cases[i]
		check(M.measure(bad[0],bad[1],bad[2],bad[3]).is_empty(),"invalid_projection_measurement_refused_"+str(i))
	for host in [Vector2i(3440,1440),Vector2i(1400,900),Vector2i(960,540),Vector2i(640,360),Vector2i(200,120)]:
		var extent:=S.opening_size(host);var low:=S.minimum(host);var room:=S.available(host);var position:=S.position(host,extent)
		check(extent.x>=low.x and extent.y>=low.y and extent.x<=room.x and extent.y<=room.y and position.x>=0 and position.y>=0 and position.x+extent.x<=host.x and position.y+extent.y<=host.y,"face_window_stays_accessible_"+str(host))
	var remembered:=Vector2i(650,800)
	var fitted:=S.opening_size(Vector2i(960,540),remembered)
	check(fitted==Vector2i(650,476) and remembered==Vector2i(650,800) and S.opening_size(Vector2i(1400,1000),remembered)==remembered,"temporary_small_host_does_not_destroy_the_remembered_window_size")
	check(var_to_bytes([frame,screen])==before,"measurement_never_changes_projection_inputs")
	print("EDITOR_GEOMETRY_UNIT "+JSON.stringify({"checks":checks,"failures":failures,"native_assets_tested":false,"gui_or_render_qualified":false,"application_adopted":false}))
	quit(0 if failures==0 else 1)
