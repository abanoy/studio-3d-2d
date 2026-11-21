extends RefCounted
# Temporary editor lens only. The existing Save camera key path persists it explicitly.
const MIN_FOV:=15.
const MAX_FOV:=120.
const DEGREES_PER_NOTCH:=3.
static func plan(current,button: int,factor) -> Dictionary:
	if button not in [MOUSE_BUTTON_WHEEL_UP,MOUSE_BUTTON_WHEEL_DOWN]:return {"error":"Use the mouse wheel to change the lens."}
	if not (current is int or current is float) or not is_finite(float(current)) or current<MIN_FOV or current>MAX_FOV:return {"error":"Set the editor lens between 15° and 120° before wheel zoom."}
	if not (factor is int or factor is float) or not is_finite(float(factor)) or factor<=0 or factor>8:return {"error":"The wheel step is invalid."}
	var next: float=clampf(float(current)+(-1. if button==MOUSE_BUTTON_WHEEL_UP else 1.)*DEGREES_PER_NOTCH*float(factor),MIN_FOV,MAX_FOV)
	return {"fov":next,"changed":not is_equal_approx(next,float(current))}
static func handle(app,event: InputEvent) -> bool:
	if not event is InputEventMouseButton or not event.pressed or event.button_index not in [MOUSE_BUTTON_WHEEL_UP,MOUSE_BUTTON_WHEEL_DOWN]:return false
	if app.mode.selected not in [1,2] or app.exporting or app.playing or app.home and app.home.visible or app.has_dialog(app):return false
	if app.pose_editor.dragging or app.physics_editor.grabbing() or app.drawing or app.source_import.pid>0 or app.has_project.pid>0:return false
	if app.camera_transform_editor and app.camera_transform_editor.has_draft():return false
	# Keep the established Ctrl-wheel dolly and Ctrl-right orbit pan authoritative.
	if app.navigation_scheme=="orbit" and (event.ctrl_pressed or app.orbit_control.active):return false
	var pending: bool=app.world_selection and app.world_selection.pending_button==MOUSE_BUTTON_RIGHT and app.camera_buttons==0
	if not pending and app.camera_buttons!=MOUSE_BUTTON_MASK_RIGHT:return false
	var proposal:=plan(app.renderer.camera.fov,event.button_index,event.factor)
	if proposal.has("error"):app.message(proposal.error);return true
	if pending:
		var cursor: Vector2=app.world_selection.pending_cursor
		app.world_selection.cancel_gesture(true)
		app.camera_button(MOUSE_BUTTON_RIGHT,true,false,cursor)
	if proposal.changed:
		app.renderer.camera.fov=proposal.fov
		app.renderer.view_changed.emit();app.pose_editor.update_gizmo();app.camera_preview_hint()
	return true
