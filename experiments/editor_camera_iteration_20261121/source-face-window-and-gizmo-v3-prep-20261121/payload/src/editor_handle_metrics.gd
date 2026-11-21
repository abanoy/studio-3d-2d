extends RefCounted
# Native projection pixels <-> physical editor pixels, never model/world scale.
const PERCENTS=[75,100,125,150,200]
const DEFAULT_PERCENT=150
const AXIS_RADIUS_PIXELS=70.0
const VIEW_RADIUS_PIXELS=90.0
static func checked_percent(value) -> int:
	return int(value) if value is int and value in PERCENTS else DEFAULT_PERCENT
static func measure(percent: int,resolution: Vector2,frame: Rect2,local_to_screen: Transform2D) -> Dictionary:
	if not percent in PERCENTS or not resolution.is_finite() or resolution.x<=0. or resolution.y<=0.:return {}
	if not frame.position.is_finite() or not frame.size.is_finite() or frame.size.x<=0. or frame.size.y<=0.:return {}
	if not local_to_screen.x.is_finite() or not local_to_screen.y.is_finite() or not local_to_screen.origin.is_finite():return {}
	var native_to_local:=Transform2D(Vector2(frame.size.x/resolution.x,0),Vector2(0,frame.size.y/resolution.y),frame.position)
	var native_to_screen:=local_to_screen*native_to_local
	var screen_x:=native_to_screen.x.length();var screen_y:=native_to_screen.y.length()
	if not is_finite(screen_x) or not is_finite(screen_y) or screen_x<=0. or screen_y<=0. or is_zero_approx(native_to_screen.determinant()):return {}
	var factor:=float(percent)/100.
	return {"native_to_screen":native_to_screen,"radius":AXIS_RADIUS_PIXELS*factor/screen_x,"view_radius":VIEW_RADIUS_PIXELS*factor/screen_x,"hit_pixels":maxf(12.,10.*factor),"axis_screen_pixels":AXIS_RADIUS_PIXELS*factor,"view_screen_pixels":VIEW_RADIUS_PIXELS*factor}
