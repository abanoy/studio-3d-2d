"""Pure source instrumentation. Root alone writes/runs a private diagnostic copy."""
import hashlib

ORIGINAL_SHA256 = '7c2150ad2a5221bf3e81cad758cea609f46d414e8e2761c9b50cfb82598bf141'
LABEL = b'native color excludes selection helpers while preserving rig/source/view: '
HELPERS = '''
func diagnostic_sampler_pointer(event: InputEvent, point: Vector2) -> void:
	if not (event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT and event.pressed):return
	var pixel:=Vector2i(point.floor())
	_diagnostic_sampler_press={"mapped":[point.x,point.y],"mapped_floored":[pixel.x,pixel.y],"context_present":not app.color_sampler.context.is_empty(),"context_pixel":[]}
	if app.color_sampler.context.has("point"):
		var actual:=Vector2i(app.color_sampler.context.point)
		_diagnostic_sampler_press.context_pixel=[actual.x,actual.y]

func diagnostic_sampler_rgba8(value: Color) -> Array:
	return [value.r8,value.g8,value.b8,value.a8]

func diagnostic_sampler_rgba(value: Color) -> Array:
	return [value.r,value.g,value.b,value.a]

func diagnostic_sampler_digest(value) -> String:
	return JSON.stringify(JSON.parse_string(JSON.stringify(value,"",true,true)),"",true,true).sha256_text()

func diagnostic_sampler_native(name: String,picker,point: Vector2,wanted: Color,count: int,native_view: Dictionary,native_world: Dictionary,original_hash: String,reference_pixel: Image,rig) -> void:
	var current_view: Dictionary=app.renderer.view_state()
	var current_world: Dictionary=World.portable(app.current_world())
	var current_hash:=FileAccess.get_sha256(rig.data.source)
	var got: Color=app.color.color
	var last_pixel:=Vector2i(picker.last_result.get("point",Vector2i(-1,-1)))
	var intended_pixel:=Vector2i(point)
	var row:={"format":"has_color_sampler_native_conjunction_probe_1","case":name,
		"operands":{"capture_increment":picker.captures==count+1,"picked_color_exact":got==wanted,"view_unchanged":equal(native_view,current_view),"world_unchanged":equal(native_world,current_world),"source_sha_unchanged":current_hash==original_hash},
		"captures_before":count,"captures_after":picker.captures,
		"native_intended":[point.x,point.y],"native_intended_pixel":[intended_pixel.x,intended_pixel.y],
		"actual_pointer_press":_diagnostic_sampler_press.duplicate(true),"last_result_pixel":[last_pixel.x,last_pixel.y],
		"last_result_frame":picker.last_result.get("frame",-1),"last_result_source":picker.last_result.get("source",-1),
		"wanted_RGBA8":diagnostic_sampler_rgba8(wanted),"got_RGBA8":diagnostic_sampler_rgba8(got),
		"wanted_RGBA":diagnostic_sampler_rgba(wanted),"got_RGBA":diagnostic_sampler_rgba(got),
		"view_before_sha256":diagnostic_sampler_digest(native_view),"view_after_sha256":diagnostic_sampler_digest(current_view),
		"world_before_sha256":diagnostic_sampler_digest(native_world),"world_after_sha256":diagnostic_sampler_digest(current_world),
		"source_before_sha256":original_hash,"source_after_sha256":current_hash,
		"source_selected":picker.source.selected,"tool_selected":app.tool.selected,"frame":app.frame,
		"physics_running":app.physics_editor.is_running(),"picker_context_empty":picker.context.is_empty(),"status":app.status.text.left(300)}
	if Rect2i(Vector2i.ZERO,reference_pixel.get_size()).has_point(last_pixel):
		var at_last:=reference_pixel.get_pixelv(last_pixel)
		row["reference_at_last_result_RGBA8"]=diagnostic_sampler_rgba8(at_last)
		row["reference_at_last_result_RGBA"]=diagnostic_sampler_rgba(at_last)
	print("COLOR_SAMPLER_NATIVE_PROBE "+JSON.stringify(row))
'''


def instrument(raw_bytes):
    assert type(raw_bytes) is bytes and hashlib.sha256(raw_bytes).hexdigest() == ORIGINAL_SHA256
    newline = b'\r\n' if b'\r\n' in raw_bytes else b'\n'
    assert raw_bytes.endswith(newline)
    assert b'diagnostic_sampler_' not in raw_bytes
    line = lambda text: text.encode('utf-8') + newline
    original_assertions = [row for row in raw_bytes.splitlines(keepends=True) if b'check(' in row]
    target, = [row for row in original_assertions if LABEL in row]
    changes = [
        (line('var failures:=0'), line('var failures:=0') + line('var _diagnostic_sampler_press: Dictionary={}')),
        (line('\tvar picker=app.color_sampler'), line('\tvar picker=app.color_sampler') + line('\tapp.canvas.pointer.connect(diagnostic_sampler_pointer)')),
        (target, target + line('\t\tdiagnostic_sampler_native(name,picker,native_point,wanted,count,native_view,native_world,original_hash,reference_pixel,rig)')),
    ]
    result = raw_bytes
    for before, after in changes:
        assert result.count(before) == 1 and after not in result
        result = result.replace(before, after, 1)
    tail = HELPERS.encode('utf-8').replace(b'\n', newline)
    result += tail
    assert [row for row in result.splitlines(keepends=True) if b'check(' in row] == original_assertions
    inverse = result[:-len(tail)]
    for before, after in reversed(changes):
        assert inverse.count(after) == 1
        inverse = inverse.replace(after, before, 1)
    assert inverse == raw_bytes
    return result
