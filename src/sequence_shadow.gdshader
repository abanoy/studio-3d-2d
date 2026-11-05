shader_type canvas_item;
render_mode unshaded, blend_premul_alpha;
uniform vec4 shadow_color : source_color = vec4(0.0, 0.0, 0.0, 0.5);
uniform float softness_lod = 0.0;
void fragment() {
	float alpha = textureLod(TEXTURE, UV, softness_lod).a * shadow_color.a;
	COLOR = vec4(shadow_color.rgb * alpha, alpha);
}
