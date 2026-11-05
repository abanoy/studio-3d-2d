extends Control
var texture: ImageTexture
func show_image(image: Image) -> void:
	texture=ImageTexture.create_from_image(image);queue_redraw()
func _draw() -> void:
	var fitted:=Rect2(Vector2.ZERO,size)
	var ratio:=minf(size.x/1920.0,size.y/1080.0)
	fitted.size=Vector2(1920,1080)*ratio;fitted.position=(size-fitted.size)*0.5
	for y in range(0,int(fitted.size.y),16):
		for x in range(0,int(fitted.size.x),16):
			var tile:=Rect2(fitted.position+Vector2(x,y),Vector2(minf(16,fitted.size.x-x),minf(16,fitted.size.y-y)))
			draw_rect(tile,Color(0.72,0.72,0.72) if (x/16+y/16)%2==0 else Color(0.9,0.9,0.9))
	if texture:draw_texture_rect(texture,fitted,false)
