shader_type canvas_item;
render_mode unshaded;
uniform vec4 ghost_color : source_color = vec4(0.2,0.8,1.0,0.25);
void fragment() {
	COLOR = vec4(ghost_color.rgb, texture(TEXTURE,UV).a * ghost_color.a);
}
