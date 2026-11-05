extends Control
# Clip time-addressed artwork to the ruler area, keeping track labels fixed.
var timeline
func _draw() -> void:
	if not timeline:return
	draw_set_transform(Vector2(-timeline.LEFT,0))
	timeline.draw_content(self)
