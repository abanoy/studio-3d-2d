shader_type spatial;
render_mode unshaded, cull_disabled;
uniform vec3 object_color = vec3(1.0, 0.0, 0.0);
uniform sampler2D alpha_texture : source_color, hint_default_white;
uniform bool use_alpha = false;
uniform float opacity = 1.0;
void fragment() {
	ALBEDO = object_color;
	ALPHA = use_alpha ? texture(alpha_texture, UV).a * opacity : 1.0;
	ALPHA_SCISSOR_THRESHOLD = 0.2;
}
