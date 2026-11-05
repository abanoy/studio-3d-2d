extends Node2D
# Texture-region drawing avoids allocating/cropping a second full-resolution PNG.
var texture: Texture2D
var rect:=Rect2()
var region:=Rect2i()
func _draw() -> void:
	if texture and region.has_area():draw_texture_rect_region(texture,rect,Rect2(region))
