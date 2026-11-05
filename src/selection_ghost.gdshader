shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, depth_test_disabled;
uniform vec3 object_color = vec3(1.0, 0.0, 0.0);
uniform sampler2D alpha_texture : source_color, hint_default_white;
uniform bool use_alpha = false;
uniform float opacity = 1.0;
void fragment() {
	if (use_alpha && texture(alpha_texture, UV).a * opacity < 0.2) { discard; }
	ALBEDO = object_color;
	ALPHA = 1.0;
}
