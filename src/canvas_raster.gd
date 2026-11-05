extends Node2D
# Share the exact floating-point draw rectangle with the front canvas; avoid
# reconstructing it through Control offsets when zooming and panning.
var texture: Texture2D
var rect:=Rect2()
func _draw() -> void:
	if texture:draw_texture_rect(texture,rect,false)
