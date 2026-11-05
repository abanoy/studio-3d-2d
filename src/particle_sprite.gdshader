shader_type spatial;
render_mode unshaded, cull_disabled, blend_add, depth_draw_never;
uniform sampler2D sprite : source_color, filter_linear, repeat_disable;
void vertex() {
	float a = INSTANCE_CUSTOM.x;
	vec2 p = mat2(vec2(cos(a), sin(a)), vec2(-sin(a), cos(a))) * VERTEX.xy;
	float radius = length(MODEL_MATRIX[0].xyz);
	vec3 center = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	vec3 facing = center + radius * (INV_VIEW_MATRIX[0].xyz * p.x + INV_VIEW_MATRIX[1].xyz * p.y);
	POSITION = PROJECTION_MATRIX * VIEW_MATRIX * vec4(facing, 1.0);
}
void fragment() {
	vec4 tex = texture(sprite, UV);
	ALBEDO = tex.rgb * COLOR.rgb;
	ALPHA = tex.a * COLOR.a;
}
