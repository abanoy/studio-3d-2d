shader_type canvas_item;
render_mode unshaded;
uniform vec3 object_color = vec3(1.0, 0.0, 0.0);
uniform bool ghost = false;
float mask_at(sampler2D image, vec2 uv) {
	return 1.0 - smoothstep(0.04, 0.1, distance(texture(image, uv).rgb, object_color));
}
void fragment() {
	float center = mask_at(TEXTURE, UV);
	float outer = 0.0;
	for (int x = -2; x <= 2; x++) {
		for (int y = -2; y <= 2; y++) {
			outer = max(outer, mask_at(TEXTURE, UV + vec2(float(x),float(y)) * TEXTURE_PIXEL_SIZE));
		}
	}
	float alpha = max(outer - center, ghost ? center * 0.14 : 0.0);
	COLOR = vec4(0.15, 1.0, 0.32, alpha);
}
